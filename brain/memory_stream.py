"""
memory_stream.py — Diamond Brain encrypted append-log (Phase 1)

Implements:
  - AES-256-GCM encrypted segments (one per session)
  - Argon2id key derivation (passphrase → master_key → session_key via HKDF)
  - NDJSON event schema with bi-temporal fields
  - SHA-256 chain hashing across events (tamper detection)
  - Plaintext seek index (memory_stream.idx) for fast timestamp seeks
  - verify_chain() — forensic integrity check
  - MemoryStream.append() / read_events() / stream_connect()

Phase 2 (not here): StreamBroker (Unix socket pub/sub), Compactor, DiamondBrain hooks.
"""

from __future__ import annotations

import hashlib
import json
import os
import struct
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

# ── Crypto deps (both already installed) ─────────────────────────────────────
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes as crypto_hashes
from argon2.low_level import hash_secret_raw, Type as Argon2Type

# ── Constants ─────────────────────────────────────────────────────────────────
MAGIC          = b"DMBS"
VERSION        = 1
HEADER_SIZE    = 4 + 1 + 16   # magic + version + argon2_salt
ARGON2_T       = 3
ARGON2_M       = 65536
ARGON2_P       = 4
ARGON2_HASH_LEN = 32
NONCE_LEN      = 12
TAG_LEN        = 16
LEN_PREFIX     = 4            # 4-byte big-endian payload length
GENESIS_HASH   = "0" * 64    # hash_prev for first event


# ── Exceptions ────────────────────────────────────────────────────────────────
class DecryptionError(Exception):
    pass

class ChainError(Exception):
    pass

class StreamFormatError(Exception):
    pass


# ── Key derivation ─────────────────────────────────────────────────────────────

def _derive_master_key(passphrase: str, salt: bytes) -> bytes:
    """Argon2id: passphrase + random 16-byte salt → 32-byte master key."""
    return hash_secret_raw(
        secret=passphrase.encode(),
        salt=salt,
        time_cost=ARGON2_T,
        memory_cost=ARGON2_M,
        parallelism=ARGON2_P,
        hash_len=ARGON2_HASH_LEN,
        type=Argon2Type.ID,
    )

def _derive_session_key(master_key: bytes, session_id: str) -> bytes:
    """HKDF-SHA256: master_key + session_id → 32-byte session key."""
    hkdf = HKDF(
        algorithm=crypto_hashes.SHA256(),
        length=32,
        salt=None,
        info=session_id.encode(),
    )
    return hkdf.derive(master_key)


# ── Event helpers ─────────────────────────────────────────────────────────────

def _event_id() -> str:
    return "evt_" + uuid.uuid4().hex[:8]

def _now_ts() -> float:
    return time.time()

def _today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

def _serialize(event: dict) -> bytes:
    """Canonical JSON bytes for hashing — sorted keys, no extra whitespace."""
    return json.dumps(event, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()

def _sha256_hex(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


# ── Seek index ────────────────────────────────────────────────────────────────
# One line per segment: "<session_id>\t<ts_sys_created>\t<file_offset>\n"
# Enables O(log n) seek to a timestamp without decrypting all segments.

@dataclass
class IndexEntry:
    session_id:   str
    ts_created:   float
    file_offset:  int   # byte offset of segment start in .log


def _idx_append(idx_path: Path, entry: IndexEntry) -> None:
    with open(idx_path, "a", encoding="utf-8") as f:
        f.write(f"{entry.session_id}\t{entry.ts_created:.6f}\t{entry.file_offset}\n")

def _idx_load(idx_path: Path) -> list[IndexEntry]:
    if not idx_path.exists():
        return []
    entries = []
    for line in idx_path.read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        if len(parts) == 3:
            entries.append(IndexEntry(
                session_id=parts[0],
                ts_created=float(parts[1]),
                file_offset=int(parts[2]),
            ))
    return entries


# ── Low-level segment read/write ──────────────────────────────────────────────

def _write_segment(fh, session_key: bytes, plaintext_lines: list[bytes]) -> int:
    """Encrypt and write one segment. Returns byte offset of this segment."""
    offset = fh.tell()
    nonce      = os.urandom(NONCE_LEN)
    payload    = b"\n".join(plaintext_lines)
    aesgcm     = AESGCM(session_key)
    ciphertext = aesgcm.encrypt(nonce, payload, None)   # auth_tag appended by lib
    length     = struct.pack(">I", len(ciphertext))
    fh.write(nonce + length + ciphertext)
    fh.flush()
    os.fsync(fh.fileno())
    return offset

def _read_segment(fh, session_key: bytes) -> Optional[list[bytes]]:
    """Decrypt one segment from current file position. Returns None on EOF, list of lines otherwise."""
    nonce_bytes = fh.read(NONCE_LEN)
    if not nonce_bytes:
        return None   # EOF
    if len(nonce_bytes) < NONCE_LEN:
        raise StreamFormatError("Truncated nonce in segment")
    len_bytes = fh.read(LEN_PREFIX)
    if len(len_bytes) < LEN_PREFIX:
        raise StreamFormatError("Truncated length prefix")
    payload_len  = struct.unpack(">I", len_bytes)[0]
    ciphertext   = fh.read(payload_len)
    if len(ciphertext) < payload_len:
        raise StreamFormatError("Truncated ciphertext")
    try:
        aesgcm    = AESGCM(session_key)
        plaintext = aesgcm.decrypt(nonce_bytes, ciphertext, None)
    except Exception as exc:
        raise DecryptionError(f"AES-GCM auth failed: {exc}") from exc
    return [line for line in plaintext.split(b"\n") if line.strip()]


# ── MemoryStream ──────────────────────────────────────────────────────────────

class MemoryStream:
    """
    Encrypted append-only event log for Diamond Brain.

    Usage:
        stream = MemoryStream(memory_dir, passphrase="my secret")
        stream.open_session("sess_abc123")
        stream.append(op="LEARN", topic="fraud", content="...", confidence=0.95)
        stream.close_session()
    """

    def __init__(self, memory_dir: Path | str, passphrase: str):
        self.memory_dir   = Path(memory_dir)
        self.log_path     = self.memory_dir / "memory_stream.log"
        self.idx_path     = self.memory_dir / "memory_stream.idx"
        self._passphrase  = passphrase
        self._master_key: Optional[bytes]  = None
        self._session_key: Optional[bytes] = None
        self._session_id: Optional[str]    = None
        self._session_events: list[bytes]  = []  # buffered NDJSON lines for current session
        self._prev_hash: str = GENESIS_HASH
        self._segment_offset: int = 0
        self._ensure_log_header()

    # ── Header ────────────────────────────────────────────────────────────

    def _ensure_log_header(self) -> None:
        if self.log_path.exists() and self.log_path.stat().st_size >= HEADER_SIZE:
            # Read existing salt
            with open(self.log_path, "rb") as f:
                magic   = f.read(4)
                version = f.read(1)[0]
                salt    = f.read(16)
            if magic != MAGIC:
                raise StreamFormatError(f"Bad magic: {magic!r}")
            if version != VERSION:
                raise StreamFormatError(f"Unsupported version: {version}")
            self._argon2_salt = salt
        else:
            # New log — write header atomically
            self._argon2_salt = os.urandom(16)
            tmp = self.log_path.with_suffix(".tmp")
            with open(tmp, "wb") as f:
                f.write(MAGIC + bytes([VERSION]) + self._argon2_salt)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, self.log_path)

        # Derive master key now that we have the salt
        self._master_key = _derive_master_key(self._passphrase, self._argon2_salt)

    # ── Session lifecycle ─────────────────────────────────────────────────

    def open_session(self, session_id: Optional[str] = None) -> str:
        """Begin a new session. Returns the session_id."""
        if self._session_id:
            raise RuntimeError("Session already open — call close_session() first")
        self._session_id    = session_id or ("sess_" + uuid.uuid4().hex[:8])
        self._session_key   = _derive_session_key(self._master_key, self._session_id)
        self._session_events = []
        self._prev_hash     = self._tail_hash()  # chain from last committed event

        # Write SESSION_START event
        self._append_raw(op="SESSION_START", topic="__meta__", content="", extra={
            "session_id": self._session_id,
            "key_hint":   hashlib.sha256(self._session_key).hexdigest()[:16],
        })
        return self._session_id

    def close_session(self, tokens_used: int = 0) -> None:
        """Flush current session as one encrypted segment."""
        if not self._session_id:
            return
        self._append_raw(op="SESSION_END", topic="__meta__", content="", extra={
            "session_id":  self._session_id,
            "event_count": len(self._session_events),
            "tokens_used": tokens_used,
        })
        self._flush_segment()
        self._session_id    = None
        self._session_key   = None
        self._session_events = []

    def _flush_segment(self) -> None:
        if not self._session_events or not self._session_key:
            return
        with open(self.log_path, "ab") as fh:
            offset = _write_segment(fh, self._session_key, self._session_events)
        self._segment_offset = offset
        _idx_append(self.idx_path, IndexEntry(
            session_id=self._session_id or "unknown",
            ts_created=_now_ts(),
            file_offset=offset,
        ))

    # ── Append ────────────────────────────────────────────────────────────

    def append(
        self,
        op: str,
        topic: str,
        content: str = "",
        confidence: float = 0.9,
        source: str = "auto",
        gen: int = 0,
        links: Optional[list[str]] = None,
        vector: Optional[list[float]] = None,
        ts_valid_from: Optional[str] = None,
        ts_valid_until: Optional[str] = None,
        **extra,
    ) -> dict:
        """Append one event to the in-memory session buffer."""
        if not self._session_id:
            raise RuntimeError("No open session — call open_session() first")
        return self._append_raw(
            op=op, topic=topic, content=content,
            extra=dict(
                confidence=confidence,
                source=source,
                gen=gen,
                links=links or [],
                vector=vector,
                ts_valid_from=ts_valid_from or _today_str(),
                ts_valid_until=ts_valid_until,
                **extra,
            ),
        )

    def _append_raw(self, op: str, topic: str, content: str, extra: dict) -> dict:
        """Build event dict, compute chain hash, buffer as NDJSON."""
        event: dict = {
            "id":                 _event_id(),
            "op":                 op,
            "gen":                extra.pop("gen", 0),
            "ts_sys_created":     _now_ts(),
            "ts_sys_invalidated": None,
            "ts_valid_from":      extra.pop("ts_valid_from", _today_str()),
            "ts_valid_until":     extra.pop("ts_valid_until", None),
            "topic":              topic,
            "content":            content,
            "session_id":         self._session_id or "",
            "hash_prev":          self._prev_hash,
        }
        event.update(extra)

        raw         = _serialize(event)
        self._prev_hash = _sha256_hex(raw)
        self._session_events.append(raw)
        return event

    # ── Read ──────────────────────────────────────────────────────────────

    def read_events(
        self,
        passphrase: Optional[str] = None,
        since_ts: float = 0.0,
        gen: Optional[int] = None,
        op: Optional[str] = None,
        topic: Optional[str] = None,
    ) -> Iterator[dict]:
        """
        Decrypt and yield events from the log.

        Args:
            passphrase: If different from the one used at init (e.g. for reading old logs).
            since_ts:   Only yield events with ts_sys_created >= this value.
            gen:        Filter by generation (0, 1, or 2).
            op:         Filter by op type ("LEARN", "RECALL", etc.).
            topic:      Filter by topic (exact match).
        """
        master_key = self._master_key
        if passphrase and passphrase != self._passphrase:
            master_key = _derive_master_key(passphrase, self._argon2_salt)

        # Use index to skip segments before since_ts if possible
        index   = _idx_load(self.idx_path)
        skip_to = 0
        if since_ts > 0 and index:
            # Last segment with ts_created <= since_ts
            before = [e for e in index if e.ts_created <= since_ts]
            if before:
                skip_to = before[-1].file_offset

        with open(self.log_path, "rb") as fh:
            fh.read(HEADER_SIZE)  # skip header
            if skip_to > HEADER_SIZE:
                fh.seek(skip_to)

            while True:
                pos = fh.tell()

                # Determine session_key for this segment via index
                seg_entry = next(
                    (e for e in reversed(index) if e.file_offset <= pos),
                    None,
                )
                if seg_entry is None:
                    # No index entry — attempt with current session key (new unflipped segment)
                    if not self._session_key:
                        break
                    session_key = self._session_key
                else:
                    session_key = _derive_session_key(master_key, seg_entry.session_id)

                try:
                    lines = _read_segment(fh, session_key)
                except StreamFormatError:
                    break  # truncated — stop cleanly
                if lines is None:
                    break  # EOF

                for line in lines:
                    try:
                        evt = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    ts = evt.get("ts_sys_created", 0.0)
                    if ts < since_ts:
                        continue
                    if gen is not None and evt.get("gen") != gen:
                        continue
                    if op and evt.get("op") != op:
                        continue
                    if topic and evt.get("topic") != topic:
                        continue
                    yield evt

    # ── Tail hash (for chain continuity across sessions) ──────────────────

    def _tail_hash(self) -> str:
        """Return hash_prev value of the last committed event, or GENESIS_HASH."""
        # Read last event from log to continue the chain
        last_event = None
        try:
            for evt in self.read_events():
                last_event = evt
        except Exception:
            pass
        if last_event is None:
            return GENESIS_HASH
        # Reconstruct the canonical bytes and re-hash
        raw = _serialize(last_event)
        return _sha256_hex(raw)

    # ── Context manager ───────────────────────────────────────────────────

    def __enter__(self) -> "MemoryStream":
        self.open_session()
        return self

    def __exit__(self, *_) -> None:
        self.close_session()


# ── verify_chain ──────────────────────────────────────────────────────────────

def verify_chain(events: list[dict]) -> tuple[bool, str]:
    """
    Verify the SHA-256 chain across a list of events.

    Args:
        events: Ordered list of event dicts as returned by read_events().

    Returns:
        (True, "OK") or (False, "Chain broken at event N: evt_xxxxxxxx — expected ... got ...")
    """
    if not events:
        return True, "OK (empty)"

    prev_raw  = _serialize(events[0])
    prev_hash = GENESIS_HASH

    # First event must have hash_prev == GENESIS_HASH or a valid prior hash
    for i, evt in enumerate(events):
        declared_prev = evt.get("hash_prev", "")
        raw           = _serialize(evt)

        if i > 0:
            expected = _sha256_hex(prev_raw)
            if declared_prev != expected:
                return False, (
                    f"Chain broken at event {i}: {evt.get('id', '?')} — "
                    f"expected {expected[:30]}... got {declared_prev[:30]}..."
                )
        prev_raw = raw

    return True, "OK"


# ── stream_connect — on-session-start protocol ────────────────────────────────

@dataclass
class MemoryContext:
    """Assembled memory state ready for LLM injection."""
    facts:       list[dict] = field(default_factory=list)
    session_id:  str        = ""
    as_of_ts:    float      = 0.0

    def to_text(self, max_facts: int = 200) -> str:
        """Format facts as a compact bullet list for LLM context injection."""
        lines = []
        for f in self.facts[:max_facts]:
            topic   = f.get("topic", "?")
            content = f.get("content", "")
            conf    = f.get("confidence", 0)
            if content and topic not in ("__meta__",):
                lines.append(f"[{topic}|{conf:.0%}] {content}")
        return "\n".join(lines)


def stream_connect(
    memory_dir: Path | str,
    passphrase: str,
    session_id: Optional[str] = None,
    since_ts: float = 0.0,
) -> tuple[MemoryStream, MemoryContext]:
    """
    Open the memory stream for a new session and assemble a MemoryContext.

    Returns (stream, ctx) where stream is open and ctx has today's facts loaded.
    Call stream.close_session() when done.
    """
    stream     = MemoryStream(memory_dir, passphrase)
    session_id = stream.open_session(session_id)

    ctx        = MemoryContext(session_id=session_id, as_of_ts=_now_ts())

    # Load LEARN events since since_ts (today's Gen0 + Gen1 if since_ts=0 means all)
    for evt in stream.read_events(since_ts=since_ts, op="LEARN"):
        if evt.get("ts_sys_invalidated") is None:  # skip invalidated facts
            ctx.facts.append(evt)

    return stream, ctx


# ── CLI smoke interface ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse, sys, getpass

    parser = argparse.ArgumentParser(description="Diamond Brain — Memory Stream CLI")
    sub    = parser.add_subparsers(dest="cmd")

    p_verify = sub.add_parser("verify", help="Verify chain integrity")
    p_verify.add_argument("--dir", default=None)

    p_replay = sub.add_parser("replay", help="Print all events since timestamp")
    p_replay.add_argument("--dir", default=None)
    p_replay.add_argument("--since", type=float, default=0.0)

    p_write = sub.add_parser("write-test", help="Write a test event")
    p_write.add_argument("--dir", default=None)

    args   = parser.parse_args()
    phrase = getpass.getpass("Passphrase: ")

    from pathlib import Path as _P
    default_dir = _P.home() / "projects" / "diamond-brain" / "brain" / "memory"

    mem_dir = _P(args.dir) if getattr(args, "dir", None) else default_dir

    if args.cmd == "write-test":
        s = MemoryStream(mem_dir, phrase)
        sid = s.open_session()
        s.append(op="LEARN", topic="test", content="memory_stream Phase 1 smoke test", confidence=0.99, source="cli")
        s.close_session()
        print(f"Wrote test event in session {sid}")

    elif args.cmd == "replay":
        s = MemoryStream(mem_dir, phrase)
        count = 0
        for evt in s.read_events(since_ts=args.since):
            print(json.dumps(evt, indent=2))
            count += 1
        print(f"\n{count} events replayed.")

    elif args.cmd == "verify":
        s = MemoryStream(mem_dir, phrase)
        events = list(s.read_events())
        ok, msg = verify_chain(events)
        sym = "✓" if ok else "✗"
        print(f"{sym} Chain verify: {msg}  ({len(events)} events)")
        sys.exit(0 if ok else 1)

    else:
        parser.print_help()
