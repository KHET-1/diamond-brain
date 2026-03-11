# Diamond Brain — Sync Guide
## ParrotMain ↔ Tanzia-Brain ↔ Future Nodes

**Last updated:** 2026-03-09
**Protocol:** DiamondLink Plain TCP (newline-delimited JSON)
**Schema:** brain_schema.py v1.0 (X9 adapter included)

---

## Network Map

| Node | Machine | IP | REST API | DiamondLink TCP |
|------|---------|-----|----------|-----------------|
| ParrotMain | parrot (rathin) | 192.168.1.x | — | port 7778 |
| DiamondParrot | parrot (rathin, alt brain) | 192.168.1.x | — | port 7778 |
| Tanzia-Brain | Windows (Tanzia) | 192.168.1.151 | port 7734 | port 7778 |
| Lenny-FSD (X9) | Windows (Tanzia alt) | 192.168.1.151 | port 8080 | port 7778 |

**Tanzia fingerprint (short):** `e290aaf23ca213c6`
**ParrotMain NIC:** `ParrotMain | parrot | primary`
**X9 cert fingerprint:** `c30c2d52adcbbf11e5824002b59bb5d6d3e9a2e34ea4af82266d73627cea68ca`

---

## Part 1: Push Facts to Tanzia via REST API

Use Tanzia's HTTP REST bridge (`brain/server.py` running on port 7734).

### Quick push — single fact

```bash
curl -s -X POST http://192.168.1.151:7734/learn \
  -H "Content-Type: application/json" \
  -d '{"topic": "test", "fact": "hello from parrot", "confidence": 90, "source": "parrot", "verified": true}'
```

### Batch push — multiple facts at once

```python
import sys, os, json, urllib.request
sys.path.insert(0, os.path.expanduser('~/projects/lib'))
from rathin_utils.brain import Brain
brain = Brain()

# Pull all facts from local brain
all_facts = []
for topic in brain.digest()["topics"]:
    facts = brain.recall(topic, max_results=500)
    for f in facts:
        all_facts.append({
            "topic": f["topic"],
            "fact": f["fact"],
            "confidence": int(f.get("confidence", 80)),
            "source": f.get("source", "parrot"),
            "verified": bool(f.get("verified", False)),
            "created_at": f.get("created_at", ""),
        })

# Batch push — Tanzia's endpoint uses "items" (NOT "facts")
payload = json.dumps({"items": all_facts}).encode()
req = urllib.request.Request(
    "http://192.168.1.151:7734/batch_learn",
    data=payload,
    headers={"Content-Type": "application/json"}
)
resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
print(f"Pushed {len(all_facts)} facts → stored: {resp.get('stored', '?')}, skipped: {resp.get('skipped', '?')}")
```

**Key gotcha:** Tanzia's `/batch_learn` uses `"items"` not `"facts"`. Don't mix them up.

### Pull facts FROM Tanzia

```python
import urllib.request, json

resp = json.loads(urllib.request.urlopen("http://192.168.1.151:7734/facts", timeout=10).read())
tanzia_facts = resp.get("facts", [])
print(f"Tanzia has {len(tanzia_facts)} facts")

# Ingest into local brain
sys.path.insert(0, os.path.expanduser('~/projects/lib'))
from rathin_utils.brain import Brain
brain = Brain()
for f in tanzia_facts:
    brain.learn(f["topic"], f["fact"], f.get("confidence", 80), "tanzia_sync", True)
print("Done")
```

---

## Part 2: DiamondLink Plain TCP Sync (Bidirectional)

Plain TCP protocol on port 7778. Messages are newline-delimited JSON (`\n` after each message).

### Message flow

```
ParrotMain                         Tanzia-Brain
    │                                   │
    │──── PAIR_REQUEST ────────────────>│
    │<─── PAIR_ACK / PAIR_ACCEPT ───────│
    │                                   │
    │──── SYNC_REQUEST ────────────────>│  (push our snapshot)
    │<─── SYNC_RESPONSE ────────────────│  (receive their snapshot)
    │<─── SYNC_DONE ────────────────────│
```

### Run sync from Python (client mode — Tanzia serves)

```python
import sys, os, json, socket, time
sys.path.insert(0, os.path.expanduser('~/projects/diamond-brain'))
from brain.diamond_brain import DiamondBrain

b = DiamondBrain()
TANZIA_IP = "192.168.1.151"
TANZIA_PORT = 7778

def send_msg(sock, msg):
    sock.sendall((json.dumps(msg) + "\n").encode())

def recv_msg(sock):
    buf = b""
    while b"\n" not in buf:
        chunk = sock.recv(4096)
        if not chunk:
            break
        buf += chunk
    return json.loads(buf.split(b"\n")[0])

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((TANZIA_IP, TANZIA_PORT))
    print(f"Connected to Tanzia at {TANZIA_IP}:{TANZIA_PORT}")

    # 1. PAIR_REQUEST
    pair_req = {
        "type": "PAIR_REQUEST",
        "peer_name": "ParrotMain",
        "fact_schema": "1.0",
        "capabilities": ["facts"],
    }
    send_msg(s, pair_req)

    # 2. Receive PAIR_ACK or PAIR_ACCEPT
    ack = recv_msg(s)
    print(f"ACK: {ack.get('type')} | compat: {ack.get('compat', '?')}")
    if ack.get("type") not in ("PAIR_ACK", "PAIR_ACCEPT") or ack.get("compat") is False:
        print(f"Pairing rejected: {ack.get('reject_reason')}")
        exit(1)

    # 3. Build and send snapshot
    snapshot = b._link_build_snapshot()
    send_msg(s, {"type": "SYNC_REQUEST", "facts": snapshot})
    print(f"Pushed {len(snapshot)} facts")

    # 4. Receive their snapshot
    resp = recv_msg(s)
    if resp.get("type") == "SYNC_RESPONSE":
        their_facts = resp.get("facts", [])
        print(f"Received {len(their_facts)} facts from Tanzia")
        b._link_merge_snapshot(their_facts, source_label="tanzia")
        print("Merge complete")

    # Done
    done = recv_msg(s)
    print(f"Sync status: {done}")
```

### Serve so Tanzia can connect to us (server mode)

```bash
cd ~/projects/diamond-brain
python3 -m brain.diamond_brain --link-serve --port 7778
```

Then have Tanzia connect from their side.

---

## Part 3: CLI Quick Commands

```bash
# Check link status
cd ~/projects/diamond-brain
python3 -m brain.diamond_brain --link-status

# List known peers
python3 -m brain.diamond_brain --link-peers

# Full sync (when peer is already paired)
python3 -m brain.diamond_brain --link-sync e290aaf2 --direction both

# Push only to Tanzia
python3 -m brain.diamond_brain --link-sync e290aaf2 --direction push

# Pull only from Tanzia
python3 -m brain.diamond_brain --link-sync e290aaf2 --direction pull

# Dry run — see what would sync without merging
python3 -m brain.diamond_brain --link-sync e290aaf2 --dry-run
```

**Note:** `e290aaf2` is the short prefix of Tanzia's fingerprint. Full: `e290aaf23ca213c68833deb00537e40dd9122f348bca63d6eaba663fc2257d59`

---

## Part 4: REST Endpoints Reference (Tanzia at 192.168.1.151:7734)

| Endpoint | Method | Body | Description |
|----------|--------|------|-------------|
| `/learn` | POST | `{topic, fact, confidence, source, verified}` | Store single fact |
| `/batch_learn` | POST | `{"items": [...facts...]}` | Store many facts (**items** not facts) |
| `/facts` | GET | — | Get all facts |
| `/recall` | GET | `?topic=X` | Recall by topic |
| `/search` | GET | `?q=keyword` | Search all facts |
| `/digest` | GET | — | Brain status summary |
| `/status` | GET | — | Server health check |

---

## Part 5: Adding a New Node to the Network

1. **On the new node**, make sure `diamond_brain.py` + `brain_schema.py` are present
2. **Init TLS identity** (only needed for TLS mode):
   ```bash
   python3 -m brain.diamond_brain --link-init "NewNodeName"
   ```
3. **Get their fingerprint:**
   ```bash
   python3 -m brain.diamond_brain --link-identity
   ```
4. **Exchange fingerprints** with existing nodes (add to each other's `peers.json`)
5. **peers.json** location: `brain/memory/link/peers.json`
   ```json
   {
     "fingerprint": "THEIR_FULL_64_CHAR_HEX",
     "display_name": "TheirNodeName",
     "host": "their_ip",
     "port": 7778,
     "authorized": true,
     "protocol": "plain",
     "rest_api": "http://their_ip:7734"
   }
   ```
6. **Run initial sync** (push our facts, pull theirs)

---

## Part 6: brain_schema.py — X9 / Lenny-FSD Compatibility

`brain_schema.py` handles the protocol differences between ParrotMain and X9 (Lenny-FSD):

| Field | ParrotMain format | X9/Lenny format | Handled by |
|-------|------------------|-----------------|------------|
| Request type | `PAIR_REQUEST` | `PAIR_REQUEST` | both |
| Response type | `PAIR_ACK` | `PAIR_ACCEPT` | `parse_pair_ack()` |
| Peer name field | `peer_name` | `display_name` | `negotiate_handshake()` |
| Identity | NIC (UUID4) | cert fingerprint (SHA-256 64-char) | `synthesize_nic_from_peer()` |
| Capabilities | `["facts", ...]` | not sent | defaults to `["facts"]` |
| Schema version | `"1.0"` | not sent | defaults to `"1.0"` |

**Result:** X9 ↔ ParrotMain works in "degraded mode" — facts-only sync, synthetic NIC, no capability negotiation. This is by design until X9 adopts the NIC spec.

---

## Part 7: Token Auth (implemented 2026-03-09)

`link_pair_connect` now accepts both formats + token param:

```python
# Start a token-authenticated server (Tanzia side):
b.link_pair_start(port=7778)
# → prints: "ab12cd34ef56... give this to peer"

# Connect with token (ParrotMain side):
b.link_pair_connect("192.168.1.151:7778", token="ab12cd34ef56...")
# or:
b.link_pair_connect("192.168.1.151", port=7778, token="ab12cd34ef56...")
```

Token validation uses `secrets.compare_digest()` (timing-safe). Requests with wrong/missing token receive a `PAIR_ACK` with `compat=False` and `reject_reason: "invalid or missing pairing token"`.

**No-token mode still works** — calling `link_serve()` without `require_token` accepts any peer (backward compatible).

---

## Quick Start Checklist

```bash
# 1. Verify Tanzia is reachable
curl -s http://192.168.1.151:7734/status | python3 -m json.tool

# 2. Check peer registration
cat ~/projects/diamond-brain/brain/memory/link/peers.json

# 3. Push local facts via REST
python3 ~/projects/diamond-brain/sync_push.py   # (create from Part 1 code above)

# 4. Run bidirectional TCP sync
python3 ~/projects/diamond-brain/sync_tcp.py    # (create from Part 2 code above)

# 5. Verify sync worked
curl -s http://192.168.1.151:7734/digest | python3 -m json.tool
```

---

## Troubleshooting

| Problem | Likely cause | Fix |
|---------|-------------|-----|
| Connection refused on 7778 | Tanzia's DiamondLink server not running | Have Tanzia run `--link-serve` |
| Connection refused on 7734 | Tanzia's brain server not running | Have Tanzia start `brain/server.py` |
| Windows Firewall blocking | Ports not allowed | Allow TCP 7734+7778 inbound on Tanzia |
| `/batch_learn` 400 error | Using `"facts"` key instead of `"items"` | Change key to `"items"` |
| PAIR_ACK compat=False | Schema major version mismatch | Both nodes need brain_schema.py v1.0 |
| `_link_build_snapshot` AttributeError | Calling with argument | Call with no args: `b._link_build_snapshot()` |
| Merge gets 0 new facts | Facts already present (fuzzy dedup 80%) | Normal — not an error |
