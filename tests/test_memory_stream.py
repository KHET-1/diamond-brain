"""
test_memory_stream.py — Phase 2 test suite for diamond-brain memory stream.

Covers all 10 tests from the design doc:
  1. Event write/read roundtrip
  2. Wrong passphrase → DecryptionError
  3. Chain hash detects tampering
  4. Compaction Gen0→Gen1
  5. Checkpoint save/load roundtrip
  6. Seek index fast seek (skips old segments)
  7. Pub/sub fanout to two subscribers
  8. Pub/sub reconnect replay
  9. stream_connect applies Gen1 + Gen0 deltas on top of checkpoint
 10. Compactor dedup by vector similarity
"""

from __future__ import annotations

import json
import socket
import tempfile
import threading
import time
from pathlib import Path

import pytest

# Allow running from repo root
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "brain"))

from memory_stream import (
    Compactor,
    DecryptionError,
    MemoryStream,
    StreamBroker,
    _cosine_sim,
    _dedup_by_vector,
    stream_connect,
    verify_chain,
)

PASSPHRASE = "test-passphrase-phase2"


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def stream(tmp_dir: Path) -> MemoryStream:
    s = MemoryStream(tmp_dir, PASSPHRASE)
    s.open_session("test-sess-001")
    yield s
    try:
        s.close_session()
    except Exception:
        pass


# ── 1. Event write/read roundtrip ─────────────────────────────────────────────

def test_event_write_read_roundtrip(tmp_dir: Path) -> None:
    s = MemoryStream(tmp_dir, PASSPHRASE)
    s.open_session("sess-rtt")
    s.append(op="LEARN", topic="fraud", content="Defendant forged checks.",
             confidence=0.95, source="test")
    s.close_session()

    events = list(s.read_events(op="LEARN", topic="fraud"))
    assert len(events) == 1
    evt = events[0]
    assert evt["op"]      == "LEARN"
    assert evt["topic"]   == "fraud"
    assert evt["content"] == "Defendant forged checks."
    assert abs(evt["confidence"] - 0.95) < 0.01
    assert evt["source"]  == "test"
    assert "id" in evt
    assert "ts_sys_created" in evt
    assert "hash_prev" in evt


# ── 2. Wrong passphrase → DecryptionError ─────────────────────────────────────

def test_wrong_passphrase_raises(tmp_dir: Path) -> None:
    s = MemoryStream(tmp_dir, PASSPHRASE)
    s.open_session()
    s.append(op="LEARN", topic="test", content="secret fact", confidence=0.9)
    s.close_session()

    wrong = MemoryStream(tmp_dir, "wrong-passphrase-xyz")
    with pytest.raises(DecryptionError):
        list(wrong.read_events())


# ── 3. Chain hash detects tampering ───────────────────────────────────────────

def test_chain_hash_detects_tampering(tmp_dir: Path) -> None:
    s = MemoryStream(tmp_dir, PASSPHRASE)
    s.open_session()
    s.append(op="LEARN", topic="a", content="fact one", confidence=0.8)
    s.append(op="LEARN", topic="b", content="fact two", confidence=0.9)
    s.close_session()

    events = list(s.read_events())
    assert len(events) >= 2

    ok, msg = verify_chain(events)
    assert ok, f"Chain should be valid: {msg}"

    # Tamper with event 1's content
    tampered = [dict(e) for e in events]
    tampered[1]["content"] = "TAMPERED"

    ok2, msg2 = verify_chain(tampered)
    assert not ok2, "Tampered chain should fail"
    assert "broken" in msg2.lower()


# ── 4. Compaction Gen0 → Gen1 ────────────────────────────────────────────────

def test_compaction_gen0_to_gen1(tmp_dir: Path) -> None:
    s = MemoryStream(tmp_dir, PASSPHRASE)
    s.open_session()
    # Write 3 facts in same topic with old timestamps
    for i in range(3):
        s.append(op="LEARN", topic="fraud", content=f"Fact {i}", confidence=0.9)
    s.close_session()

    # Compact with cutoff far in the future (captures all events)
    comp = Compactor(s)
    s.open_session("compact-sess")
    result = comp.compact_gen0_to_gen1(cutoff_ts=time.time() + 10)
    s.close_session()

    assert result["compacted"] == 3
    assert "fraud" in result["topics"]

    # Gen1 COMPACT event should exist
    gen1 = list(s.read_events(gen=1, op="COMPACT", topic="fraud"))
    assert len(gen1) == 1
    assert "fraud" in gen1[0]["content"].lower() or gen1[0]["topic"] == "fraud"


# ── 5. Checkpoint save/load roundtrip ────────────────────────────────────────

def test_checkpoint_roundtrip(tmp_dir: Path) -> None:
    s = MemoryStream(tmp_dir, PASSPHRASE)
    s.open_session()
    # Write a Gen2 COMPACT event directly
    s._append_raw(
        op="COMPACT",
        topic="finance",
        content="Victim lost $500k to wire fraud.",
        extra={"gen": 2, "gen_from": 1, "gen_to": 2,
               "confidence": 0.98, "source": "compactor",
               "ts_valid_from": "2026-03-11",
               "vector": [0.1, 0.2, 0.3]},
    )
    s.close_session()

    path = s.save_checkpoint()
    assert path.exists()
    assert path.stat().st_size > 0

    ck = s.load_checkpoint()
    assert "finance" in ck["topics"]
    assert any("500k" in c for c in ck["contents"])
    assert ck["as_of_ts"] > 0


# ── 6. Seek index enables fast segment skip ───────────────────────────────────

def test_seek_index_skips_old_segments(tmp_dir: Path) -> None:
    # Write two separate sessions (two segments)
    s = MemoryStream(tmp_dir, PASSPHRASE)

    s.open_session("sess-old")
    s.append(op="LEARN", topic="old", content="old fact", confidence=0.7)
    old_ts = time.time()
    s.close_session()

    time.sleep(0.05)
    new_ts = time.time()

    s.open_session("sess-new")
    s.append(op="LEARN", topic="new", content="new fact", confidence=0.8)
    s.close_session()

    # Read only events since new_ts — should skip old segment
    recent = list(s.read_events(since_ts=new_ts))
    topics = [e["topic"] for e in recent if e["op"] == "LEARN"]
    assert "new" in topics
    assert "old" not in topics


# ── 7. Pub/sub fanout to two subscribers ─────────────────────────────────────

def test_pubsub_fanout_two_subscribers(tmp_dir: Path) -> None:
    s = MemoryStream(tmp_dir, PASSPHRASE)
    broker = s.start_broker()
    time.sleep(0.1)  # let broker start

    received: list[list[dict]] = [[], []]
    stop_flags = [threading.Event(), threading.Event()]

    def subscriber(idx: int) -> None:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(str(broker.sock_path))
        sock.sendall(json.dumps({"op": "SUBSCRIBE", "from_offset": 0,
                                  "topics": ["*"]}).encode() + b"\n")
        sock.settimeout(2.0)
        buf = b""
        while not stop_flags[idx].is_set():
            try:
                data = sock.recv(4096)
                if not data:
                    break
                buf += data
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    msg = json.loads(line)
                    if msg.get("op") == "EVENT":
                        received[idx].append(msg["event"])
            except socket.timeout:
                break
        sock.close()

    threads = [threading.Thread(target=subscriber, args=(i,), daemon=True) for i in range(2)]
    for t in threads:
        t.start()

    time.sleep(0.1)
    s.open_session()
    s.append(op="LEARN", topic="test", content="broadcast fact", confidence=0.9)
    s.close_session()
    time.sleep(0.3)

    for flag in stop_flags:
        flag.set()
    for t in threads:
        t.join(timeout=2)
    s.stop_broker()

    # Both subscribers should have received the event
    for i in range(2):
        learn_events = [e for e in received[i] if e.get("op") == "LEARN"]
        assert len(learn_events) >= 1, f"Subscriber {i} got no LEARN events"


# ── 8. Pub/sub reconnect replay ───────────────────────────────────────────────

def test_pubsub_reconnect_replay(tmp_dir: Path) -> None:
    s = MemoryStream(tmp_dir, PASSPHRASE)
    broker = s.start_broker()
    time.sleep(0.1)

    # Push an event before subscribing
    s.open_session()
    s.append(op="LEARN", topic="pre-connect", content="missed event", confidence=0.9)
    s.close_session()
    time.sleep(0.1)

    # Connect with from_offset=0 — should get the missed event replayed
    received: list[dict] = []
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(str(broker.sock_path))
    sock.sendall(json.dumps({"op": "SUBSCRIBE", "from_offset": 0,
                              "topics": ["*"]}).encode() + b"\n")
    sock.settimeout(2.0)
    buf = b""
    deadline = time.time() + 2.0
    while time.time() < deadline:
        try:
            data = sock.recv(4096)
            if not data:
                break
            buf += data
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                msg = json.loads(line)
                if msg.get("op") == "EVENT":
                    received.append(msg["event"])
        except socket.timeout:
            break
    sock.close()
    s.stop_broker()

    learn_events = [e for e in received if e.get("op") == "LEARN"
                    and e.get("topic") == "pre-connect"]
    assert len(learn_events) >= 1, "Replay on reconnect failed"


# ── 9. stream_connect applies Gen1 + Gen0 deltas ────────────────────────────

def test_stream_connect_applies_deltas(tmp_dir: Path) -> None:
    # Write a Gen1 COMPACT event (simulates compacted memory)
    s = MemoryStream(tmp_dir, PASSPHRASE)
    s.open_session("setup-sess")
    s._append_raw(op="COMPACT", topic="case", content="Defendant is Jayce Gregg.",
                  extra={"gen": 1, "gen_from": 0, "gen_to": 1,
                         "confidence": 0.99, "source": "compactor",
                         "ts_valid_from": "2026-03-10"})
    # Write a Gen0 LEARN event (today)
    s.append(op="LEARN", topic="case", content="Victim is Robert Cashman.",
             confidence=0.95, source="test")
    s.close_session()

    # stream_connect should assemble both
    stream2, ctx = stream_connect(tmp_dir, PASSPHRASE)
    stream2.close_session()

    topics = [f.get("topic") for f in ctx.facts]
    assert "case" in topics

    text = ctx.to_text()
    assert "Jayce" in text or "Robert" in text


# ── 10. Compactor dedup by vector similarity ─────────────────────────────────

def test_compactor_dedup_by_vector() -> None:
    vec_a = [1.0, 0.0, 0.0]
    vec_b = [0.999, 0.001, 0.0]   # near-identical to vec_a (sim ~1.0)
    vec_c = [0.0, 1.0, 0.0]       # orthogonal to vec_a (sim = 0.0)

    events = [
        {"id": "e1", "content": "fact A", "vector": vec_a},
        {"id": "e2", "content": "fact B (dup)", "vector": vec_b},
        {"id": "e3", "content": "fact C (unique)", "vector": vec_c},
    ]

    unique = _dedup_by_vector(events, threshold=0.95)
    assert len(unique) == 2, f"Expected 2 unique, got {len(unique)}"
    ids = {e["id"] for e in unique}
    assert "e1" in ids
    assert "e3" in ids
    assert "e2" not in ids  # e2 is too similar to e1


# ── Bonus: cosine_sim correctness ─────────────────────────────────────────────

def test_cosine_sim_values() -> None:
    a = [1.0, 0.0]
    b = [0.0, 1.0]
    c = [1.0, 0.0]
    assert abs(_cosine_sim(a, b)) < 0.01   # orthogonal → 0
    assert abs(_cosine_sim(a, c) - 1.0) < 0.01  # identical → 1
