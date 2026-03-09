# AI Memory Stream — Design Document
_2026-03-09 | diamond-brain | Status: Draft_

---

## Vision

Replace diamond-brain's flat JSON snapshot files (`facts.json`, `embeddings.json`, `graph.json`) with a **unified encrypted append log** that is both a write-ahead log (durable replay buffer for the AI) and a live pub/sub event bus (real-time fanout to other processes). Every memory operation — learn, recall, forget, link, compact — becomes an immutable timestamped event. The stream is the source of truth. All other stores are materialized views derived from it.

The "dream token" concept from the design brief is realized here: each event carries an inline **768-dim concept vector** (its embedding). One float array encodes the full semantic meaning of the event without any text — allowing the AI to reconstruct context at session start using vector arithmetic instead of LLM inference.

### Goals
- Full memory provenance: know exactly when, why, and by whom every fact was learned
- Minimal token cost at session start via LLMLingua-2 compression (target: 20x reduction)
- Encrypted at rest — unreadable without the session key
- Live pub/sub fanout to void_cathedral HTML client and future subscribers
- Time-travel debugging: replay to any timestamp to see what the AI knew then
- Tamper detection: chain-hashed events, like a blockchain for memory

### Non-Goals
- Cloud sync (local-only by design)
- Fully Homomorphic Encryption (FHE) — AES-256-GCM is sufficient for local threat model; FHE path documented as future upgrade
- Changing the `brain.py` / `DiamondBrain` public API surface

---

## Research Grounding

| Concept | Source | Applied As |
|---------|--------|-----------|
| Append log as source of truth | [Zep/Graphiti arxiv:2501.13956](https://arxiv.org/abs/2501.13956) | `memory_stream.log` as WAL |
| Bi-temporal fact timestamps | Zep/Graphiti bi-temporal model | 4 timestamps per event |
| Concept vectors as compressed meaning | [Meta LCM arxiv:2412.08821](https://arxiv.org/abs/2412.08821) | Inline `vector` field per event |
| 3-stage generational compaction | [LightMem arxiv:2510.18866](https://arxiv.org/abs/2510.18866) | Gen0→Gen1→Gen2 pipeline |
| LLM-based session compression | [LLMLingua-2 arxiv:2403.12968](https://arxiv.org/abs/2403.12968) | On-connect context compression |
| Zettelkasten event linking | [A-Mem arxiv:2502.12110](https://arxiv.org/abs/2502.12110) | `LINK` event type, `links[]` field |
| JIT memory retrieval | [GAM arxiv:2511.18423](https://arxiv.org/abs/2511.18423) | Semantic-gated decompression |
| Event-centric propositions | [Long-Term Conv. Memory arxiv:2511.17208](https://arxiv.org/abs/2511.17208) | Event schema shape |
| RL-optimized memory | [MemPO arxiv:2603.00680](https://arxiv.org/abs/2603.00680) | Future: recall scoring feedback loop |

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                    diamond-brain process                     │
│                                                              │
│  learn() / recall() / forget() / embed() / link()           │
│           │                                                  │
│           ▼                                                  │
│  ┌────────────────┐    encrypt(AES-256-GCM)                  │
│  │  StreamWriter  │──────────────────────► memory_stream.log │
│  └────────────────┘                        (append-only)     │
│           │                                                  │
│           │  fan-out (Unix socket)                           │
│           ▼                                                  │
│  ┌────────────────┐                                          │
│  │  StreamBroker  │──► void_cathedral HTML client            │
│  │  (local only)  │──► dashboard / future subscribers        │
│  └────────────────┘                                          │
│                                                              │
│  On session start:                                           │
│  StreamReader ──► decrypt ──► load Gen2 checkpoint           │
│                          ──► apply Gen1 deltas               │
│                          ──► apply Gen0 (today)              │
│                          ──► LLMLingua-2 compress            │
│                          ──► inject into LLM context         │
│                                                              │
│  Compaction (background, nightly):                           │
│  Gen0 (raw events) ──► Gen1 (daily summaries)                │
│  Gen1 (summaries)  ──► Gen2 (long-term distilled facts)      │
└──────────────────────────────────────────────────────────────┘
                              │
                  memory_stream.log (disk)
                  memory_stream.idx (seek index)
                  memory_stream.checkpoint (Gen2 snapshot)
```

---

## Event Schema

Every operation appended to the stream as a single NDJSON line, then encrypted.

```python
{
    # Identity
    "id":      "evt_a3f7b2c1",         # uuid4, first 8 chars
    "op":      "LEARN",                # see Op Types below
    "gen":     0,                      # 0=raw, 1=daily summary, 2=long-term

    # Bi-temporal model (Zep/Graphiti style)
    "ts_sys_created":    1741234567.123,  # when the system wrote this event
    "ts_sys_invalidated": None,           # when superseded (None = still live)
    "ts_valid_from":     "2026-03-09",    # when the fact became true in the world
    "ts_valid_until":    None,            # when the fact stopped being true

    # Payload
    "topic":   "fraud",
    "content": "Defendant deposited stolen checks after account closure.",

    # Compression fields
    "content_compressed": "def_dep_stln_chk_cls",   # LLMLingua-2 compressed form
    "vector":  [0.123, 0.456, ...],                  # 768-dim concept vector (dream token)

    # Provenance
    "confidence": 0.95,
    "source":     "session_2026-03-09_obs",
    "session_id": "sess_abc123",

    # Graph (A-Mem style Zettelkasten linking)
    "links":   ["evt_xy9z1a2b"],        # IDs of related events

    # Integrity
    "hash_prev": "sha256:4a7f...",      # SHA-256 of previous event's raw bytes
}
```

### Op Types

| Op | Trigger | Key Fields |
|----|---------|-----------|
| `SESSION_START` | AI connects | `session_id`, `key_hint` (HKDF salt, not key) |
| `SESSION_END`   | AI disconnects | `session_id`, `event_count`, `tokens_used` |
| `LEARN`         | `brain.learn()` | `topic`, `content`, `vector`, `confidence`, `source` |
| `RECALL`        | `brain.recall()` | `topic`, `query`, `result_ids[]` |
| `FORGET`        | `brain.forget()` | `topic`, `target_id`, invalidates that event |
| `EMBED`         | `brain._embed()` | `target_id`, `vector` (updates vector for existing event) |
| `LINK`          | `brain.link()` or auto | `source_id`, `target_id`, `relation` |
| `QUERY`         | search operations | `query_text`, `query_vector`, `result_ids[]`, `strategy` |
| `COMPACT`       | nightly compaction | `gen_from`, `gen_to`, `event_count`, `summary` |

---

## Encryption

### Key Derivation

```
passphrase
    │
    ▼
Argon2id(passphrase, salt=random_16_bytes, t=3, m=65536, p=4)
    │
    ▼  32-byte master_key
    │
HKDF-SHA256(master_key, info=session_id)
    │
    ▼  32-byte session_key  (one per session, never reused)
```

Master key is never stored. Derived fresh from passphrase each session.
Session key encrypts one segment of the log (all events in that session).

### File Format

```
memory_stream.log:
┌─────────────────────────────────────┐
│  magic: b"DMBS"  (4 bytes)          │
│  version: 1       (1 byte)          │
│  argon2_salt: random (16 bytes)     │
├─────────────────────────────────────┤
│  SEGMENT (one per session):         │
│  ┌─────────────────────────────┐    │
│  │  nonce: random (12 bytes)   │    │
│  │  payload_len (4 bytes, BE)  │    │
│  │  ciphertext: AES-256-GCM    │    │
│  │  auth_tag: (16 bytes)       │    │
│  └─────────────────────────────┘    │
│  ... more segments ...              │
└─────────────────────────────────────┘
```

Segment boundary = session boundary. Reading past sessions requires decrypting each segment separately. An attacker who gets the file without the passphrase sees only opaque binary blobs.

### Seek Index

`memory_stream.idx` — plaintext lightweight index mapping `(session_id, ts)` → `(segment_offset, byte_offset_within_segment)`. Enables fast seeking without full decrypt. Contains no content.

---

## Generational Compaction (LightMem-inspired)

### Three Generations

```
Gen0: raw events (today's session, uncompressed content, full fidelity)
 │  nightly compaction (LLM summarizes day's events into propositions)
 ▼
Gen1: daily summary events (condensed, still timestamped, still vectorized)
 │  weekly compaction (distill weekly summaries into permanent facts)
 ▼
Gen2: long-term distilled facts (replaces facts.json; the materialized view)
```

Gen0 events are kept indefinitely (append-only). Compaction creates new Gen1/Gen2
events in the log — it never deletes old ones. This preserves full time-travel capability.

### Compaction Algorithm

**Gen0 → Gen1 (nightly, uses LLM):**
1. Load all Gen0 events from yesterday
2. Group by topic
3. Feed each group to `cortex_summarize()` → one neo-Davidsonian proposition per topic
4. Write a `COMPACT(gen_from=0, gen_to=1)` event per topic with the summary
5. Invalidate (set `ts_sys_invalidated`) on the source Gen0 events

**Gen1 → Gen2 (weekly, uses LLM):**
1. Load all Gen1 events from the past week
2. Deduplicate by vector similarity (cosine > 0.95 = same fact, keep most confident)
3. Feed to `cortex_case_brief()` or `cortex_summarize()` → distilled facts
4. Write `COMPACT(gen_from=1, gen_to=2)` events
5. Update `memory_stream.checkpoint` with full Gen2 vector matrix

### Checkpoint File

`memory_stream.checkpoint` — an encrypted NumPy `.npz` archive:
```python
{
    "event_ids":    np.array([...], dtype='U32'),  # evt IDs
    "topics":       np.array([...], dtype='U64'),
    "contents":     np.array([...], dtype=object),
    "vectors":      np.array([...], dtype=np.float32),  # shape: (N, 768)
    "timestamps":   np.array([...], dtype=np.float64),
    "as_of_ts":     float,   # log timestamp up to which this checkpoint is valid
}
```

On session start: load checkpoint (fast, single decrypt) → apply Gen1 delta → apply Gen0 delta → no full replay needed.

---

## On-Connect Protocol (AI Session Start)

```python
def stream_connect(passphrase: str) -> MemoryContext:
    # 1. Derive key
    master_key = argon2id(passphrase, log.argon2_salt)

    # 2. Load Gen2 checkpoint (pre-computed long-term facts)
    ctx = load_checkpoint(master_key)  # fast, binary

    # 3. Apply Gen1 deltas since last checkpoint
    gen1_events = read_events(since=ctx.as_of_ts, gen=1, key=master_key)
    ctx.apply(gen1_events)

    # 4. Apply today's Gen0 raw events
    gen0_events = read_events(since=today_start(), gen=0, key=master_key)
    ctx.apply(gen0_events)

    # 5. Compress context for LLM injection
    context_text = ctx.to_text()          # assemble fact strings
    compressed   = llmlingua2(context_text)  # 5-20x compression

    # 6. Inject into session
    session.prime(compressed)
    return ctx
```

Estimated timings (358 facts, today's hardware):
- Checkpoint decrypt + load: ~5ms
- Gen1/Gen0 delta apply: ~2ms
- LLMLingua-2 compression: ~50-200ms (one-time, cached per session)
- Total cold-start overhead: **< 300ms**

---

## Live Pub/Sub (Unix Socket Broker)

A small broker thread runs inside the diamond-brain process. Consumers connect via Unix domain socket at `~/.local/share/diamond-brain/stream.sock`.

### Protocol (line-oriented JSON)

**Subscribe:**
```json
{"op": "SUBSCRIBE", "from_offset": 0, "topics": ["fraud", "*"]}
```

**Server pushes events as they are appended:**
```json
{"op": "EVENT", "offset": 1247, "event": {...}}
```

**Consumer acknowledges (optional, for durable delivery):**
```json
{"op": "ACK", "offset": 1247}
```

Each consumer maintains its own cursor. If the consumer (e.g. void_cathedral HTML client) disconnects and reconnects, it resumes from its last ACK'd offset. Missed events are replayed.

### void_cathedral Integration

The bridge (`bridge/main.py`) already has a WebSocket server. A new `MemoryStreamRelay` class in the bridge connects to the Unix socket and forwards memory events to the HTML client:

```python
# In void_cathedral HTML client — new memory feed panel
ws.on('memory_event', (evt) => {
    if (evt.op === 'LEARN')  showBrainActivity(evt.topic, evt.content);
    if (evt.op === 'RECALL') highlightFact(evt.topic);
    if (evt.op === 'COMPACT') showCompaction(evt.gen_from, evt.gen_to);
});
```

---

## Integrity & Tamper Detection

Each event contains `hash_prev` = SHA-256 of the raw bytes of the previous event (before encryption). This creates a cryptographic chain:

```
event_1.hash_prev = "0000...0000"  (genesis)
event_2.hash_prev = sha256(event_1_bytes)
event_3.hash_prev = sha256(event_2_bytes)
...
```

Verification function:
```python
def verify_chain(events: list[dict]) -> bool:
    for i, evt in enumerate(events[1:], 1):
        expected = sha256(serialize(events[i-1]))
        if evt["hash_prev"] != expected:
            return False, f"Chain broken at event {i}: {evt['id']}"
    return True, "OK"
```

Any deletion or modification of a past event breaks all subsequent hashes. Useful for forensic use cases — diamond-brain is already used for legal case analysis.

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Wrong passphrase | AES-GCM auth tag check fails → `DecryptionError`, no partial data exposed |
| Truncated log (crash mid-write) | Last incomplete segment ignored; log valid up to last complete segment |
| Corrupt chain hash | `verify_chain()` returns position of break; warn user, continue from last good event |
| LLMLingua-2 unavailable | Fall back to raw text injection (no compression); session still starts |
| Broker socket in use | New process connects as subscriber; old process as writer |
| NumPy unavailable | Checkpoint uses pure-Python cosine (already implemented) |
| Compaction fails mid-run | No Gen0 events invalidated until compaction writes all Gen1 events; idempotent retry |

---

## Integration Points (What Changes in diamond-brain)

| Location | Change |
|----------|--------|
| `DiamondBrain.learn()` | After writing to `facts.json` (unchanged), also append `LEARN` event to stream |
| `DiamondBrain.recall()` | After query, append `RECALL` event |
| `DiamondBrain.forget()` | Append `FORGET` event; invalidate prior event's `ts_sys_invalidated` |
| `DiamondBrain._embed()` | After generating vector, append `EMBED` event inline |
| `DiamondBrain.semantic_search()` | Append `QUERY` event |
| `DiamondBrain.__init__()` | Accept optional `stream_passphrase` param; if set, call `stream_connect()` |
| New: `MemoryStream` class | `brain/memory_stream.py` — all stream logic isolated here |
| New: `StreamBroker` class | Thread inside `MemoryStream`, Unix socket pub/sub |
| New: `Compactor` class | Nightly scheduled compaction, can be run manually via CLI |
| CLI: `--stream-verify` | Run `verify_chain()` across full log, report any breaks |
| CLI: `--stream-compact` | Manually trigger Gen0→Gen1 or Gen1→Gen2 compaction |
| CLI: `--stream-replay <ts>` | Show brain state as of a past timestamp |

The existing `facts.json` / `embeddings.json` / `graph.json` are **kept** as materialized views during transition. They continue to work unchanged. The stream is additive. Full migration to stream-as-source-of-truth is Phase 2.

---

## File Layout

```
brain/
  diamond_brain.py        (unchanged API, new stream hooks)
  memory_stream.py        (NEW: MemoryStream, StreamBroker, Compactor)
  memory/
    facts.json            (kept, materialized view for now)
    embeddings.json       (kept, materialized view for now)
    graph.json            (kept, materialized view for now)
    memory_stream.log     (NEW: encrypted append log)
    memory_stream.idx     (NEW: plaintext seek index)
    memory_stream.checkpoint  (NEW: encrypted Gen2 snapshot)
```

---

## Testing Plan

### Unit Tests (`tests/test_memory_stream.py`)

- `test_event_write_read_roundtrip` — write event, read back, assert fields match
- `test_encryption_wrong_passphrase_fails` — wrong key → `DecryptionError`
- `test_chain_hash_detects_tampering` — mutate one byte of event, verify chain breaks
- `test_compaction_gen0_to_gen1` — N events → compact → 1 summary event per topic
- `test_checkpoint_roundtrip` — write checkpoint, load, assert vectors match
- `test_seek_index_fast_seek` — seek by timestamp uses index, not full scan
- `test_pubsub_fanout` — two mock subscribers both receive appended event
- `test_pubsub_reconnect_replay` — subscriber disconnects, reconnects, gets missed events
- `test_session_connect_applies_deltas` — checkpoint + Gen1 delta + Gen0 delta = correct state
- `test_llmlingua_compression_reduces_tokens` — context tokens after compress < before

### Integration Tests (require LM Studio)

- `test_full_session_cycle` — learn 10 facts, connect new session, verify all recalled
- `test_void_cathedral_relay` — bridge receives memory events via WebSocket

### CLI Smoke Tests

```bash
python3 diamond_brain.py --stream-verify
python3 diamond_brain.py --stream-compact --gen 0
python3 diamond_brain.py --stream-replay "2026-03-01T00:00:00"
```

---

## Implementation Sequence

1. **`MemoryStream` core** — file format, AES-256-GCM encrypt/decrypt, NDJSON append, seek index
2. **Chain hashing** — `hash_prev` on every event, `verify_chain()`
3. **`StreamBroker`** — Unix socket, cursor tracking, fanout
4. **Hook `learn()` / `recall()` / `forget()`** — append events (non-breaking, additive)
5. **On-connect protocol** — `stream_connect()`, checkpoint load, delta apply
6. **LLMLingua-2 integration** — `pip install llmlingua`, compress on connect
7. **`Compactor`** — Gen0→Gen1 nightly, Gen1→Gen2 weekly
8. **CLI flags** — `--stream-verify`, `--stream-compact`, `--stream-replay`
9. **void_cathedral relay** — `MemoryStreamRelay` in `bridge/main.py`
10. **Tests** — unit + integration

---

## Dependencies

```
# New pip installs
cryptography>=42.0.0    # AES-256-GCM, HKDF
argon2-cffi>=23.1.0     # Argon2id key derivation
llmlingua>=0.2.0        # LLMLingua-2 compression (optional, graceful fallback)

# Already available
numpy                   # vector math (already in use)
```

---

## Open Questions

1. **Passphrase UX** — where does the user provide the passphrase? CLI flag (insecure in shell history), env var (`DIAMOND_BRAIN_KEY`), or keyring (`keyring` library, OS secure store)?
2. **Inline vectors vs separate** — storing 768 floats per event makes Gen0 large fast (one LEARN event ≈ 6.1 KB). Alternative: events reference `embeddings.json` by key. Decision depends on whether we want the log to be fully self-contained.
3. **LLMLingua-2 model size** — requires downloading a small transformer (~125MB XLM-RoBERTa). Acceptable for this machine (480GB NVMe), but worth flagging.
4. **Compaction LLM call cost** — Gen0→Gen1 requires one LLM call per topic per day. At 40+ topics, this could be 40 LLM calls. Batch into one call or use a very small model (Mistral 3B).
5. **FHE upgrade path** — when Cachemir (arxiv:2602.11470) matures and GPU FHE becomes < 5% overhead, the encryption layer can be swapped in without changing the event schema or pub/sub protocol.

---

_Design by: Claude Sonnet 4.6 + rathin | Research: HuggingFace papers, web search 2026-03-09_
_Next step: invoke writing-plans to create implementation plan_
