<p align="center">
  <img src="https://img.shields.io/badge/◆_Diamond_Brain-v3.0-00d4ff?style=for-the-badge&labelColor=0a0a0a" alt="Diamond Brain v3.0" />
</p>

<p align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+" /></a>
  <a href="#zero-dependencies"><img src="https://img.shields.io/badge/Dependencies-Zero-00c853?style=flat-square" alt="Zero Dependencies" /></a>
  <a href="#everything-is-tested"><img src="https://img.shields.io/badge/Tests-213_passing-00c853?style=flat-square" alt="213 Tests" /></a>
  <a href="#the-full-api"><img src="https://img.shields.io/badge/Public_Methods-116-7c4dff?style=flat-square" alt="116 Methods" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-ffd600?style=flat-square" alt="MIT License" /></a>
  <a href="#the-http-server"><img src="https://img.shields.io/badge/Server-Port_7734-ff6d00?style=flat-square" alt="HTTP Server" /></a>
</p>

<h1 align="center">◆ Diamond Brain v3.0</h1>

<p align="center">
  <strong>Your AI's permanent memory. Your team's shared knowledge. Your case's chain of custody.</strong>
</p>

<p align="center">
  <em>
    Built by <a href="https://github.com/Tunclon">Ryan Cashmoney</a> and <a href="https://claude.ai">Claude</a> (Anthropic) —<br/>
    a human-AI collaboration that produced 9,600 lines of zero-dependency Python,<br/>
    31 feature systems, and 213 tests. Every line reviewed by both minds.
  </em>
</p>

---

<br/>

## What Is Diamond Brain?

**Diamond Brain is a memory system for AI agents and humans.**

Imagine giving Claude, GPT, or any AI a brain that doesn't forget when the conversation ends. A brain that can share what it knows with other brains — encrypted. A brain that tracks legal citations, builds knowledge graphs, detects contradictions in what it's been told, and refuses to permanently delete anything without a 14-day cooling-off period and a passphrase.

That's Diamond Brain.

It's a single Python file. No pip install. No database. No cloud service. Just drop it into your project, and your AI has persistent, shareable, auditable memory.

<br/>

---

<br/>

## Who Is This For?

<table>
<tr>
<td width="50%" valign="top">

### 👤 Non-Technical Users

You don't need to understand code. You need to understand what this does for you:

- **Your AI remembers everything** — facts, evidence, legal citations, timelines
- **Nothing gets silently deleted** — the Quarantine system holds everything for 14 days minimum
- **Share knowledge securely** — encrypted brain-to-brain sync between trusted peers
- **Court-ready documents** — generates properly formatted legal motions with real statute citations
- **Your AI gets smarter over time** — spaced repetition surfaces what needs review

</td>
<td width="50%" valign="top">

### 🔧 Technical Users

You care about architecture. Here's why this is interesting:

- **9,600 lines, zero imports outside stdlib** — json, pathlib, ssl, hashlib, that's it
- **Atomic writes everywhere** — `.tmp` + `os.replace()`, safe even on power loss
- **Allen's Interval Algebra** — 13 temporal relations, not just "before/after"
- **FSRS-4 spaced repetition** — power-law forgetting curves, not exponential decay
- **CRDT-ready** — conflict-free replicated data types for multi-brain merge
- **Merkle DAG chain of custody** — blockchain-style hash chains for evidence integrity

</td>
</tr>
</table>

<br/>

---

<br/>

## The 31 Systems Inside Diamond Brain

Every one of these is built, tested, and working. Not a roadmap — this is what ships in v3.0.

<br/>

### 🧠 Core Intelligence

<table>
<tr><td width="30%"><strong>Knowledge Store</strong></td><td>Learn facts with confidence scores (0-100%). The brain automatically detects duplicates, links related topics together, and decays confidence over time — unverified facts fade faster than verified ones. Think of it as memory that honestly knows how sure it is.</td></tr>
<tr><td><strong>Knowledge Graph</strong></td><td>Every fact, citation, and topic becomes a node in a connected graph. The brain can traverse these connections — "show me everything within 3 hops of forensics" — and auto-builds the graph from your data. No manual wiring needed.</td></tr>
<tr><td><strong>Hybrid Search</strong></td><td>Combines keyword matching with graph connectivity scoring. Facts that are well-connected to your search term rank higher than isolated matches. Finds what you actually meant, not just what you typed.</td></tr>
<tr><td><strong>Spaced Repetition (FSRS)</strong></td><td>Based on real memory science. The brain tracks how well you remember each fact and schedules reviews right before you'd forget. Uses power-law forgetting curves — more accurate than the exponential decay most apps use.</td></tr>
</table>

<br/>

### 🔍 Analysis & Reasoning

<table>
<tr><td width="30%"><strong>Contradiction Detection</strong></td><td>Finds facts that disagree with each other — negation flips ("X is safe" vs "X is not safe"), antonym swaps ("fast" vs "slow"), and confidence conflicts (one source says 95% sure, another says 20%). Surfaces problems before they become legal issues.</td></tr>
<tr><td><strong>Crystallization</strong></td><td>When you have 50 facts about the same topic, the brain can compress them into a higher-level insight — a "crystal." These crystals become nodes in the knowledge graph, so you get automatic summarization that preserves connections.</td></tr>
<tr><td><strong>Confidence Propagation</strong></td><td>When a source is discredited, every fact from that source should be questioned. Confidence propagation cascades changes through the knowledge graph — if Fact A drops, connected Facts B and C drop too, with decreasing intensity per hop.</td></tr>
<tr><td><strong>Temporal Reasoning</strong></td><td>Not just "this happened before that." Full Allen's Interval Algebra — 13 possible relationships between events (overlaps, during, meets, contains, etc.). Can detect impossible timelines, suspicious gaps, and speed violations in event sequences.</td></tr>
<tr><td><strong>Timeline Anomaly Detection</strong></td><td>Feed it a sequence of events and it flags what doesn't make sense — a suspect at two locations simultaneously, evidence logged before the crime occurred, or suspiciously fast travel between scenes.</td></tr>
</table>

<br/>

### ⚖️ Legal Intelligence

<table>
<tr><td width="30%"><strong>Legal Citations</strong></td><td>Store and search Arizona Revised Statutes, Rules of Evidence, Constitutional provisions, and case law. Pre-seeded with 56 ARS criminal statutes covering homicide, assault, DUI, search & seizure, Miranda rights, and sentencing ranges.</td></tr>
<tr><td><strong>Court Document Generator</strong></td><td>Produces properly formatted motions, briefs, and legal documents with case captions, citation appendices, and the correct disclaimer. References real statutes from the citation store — never fabricates law.</td></tr>
<tr><td><strong>Crime-to-Citation Linking</strong></td><td>When a fact mentions a crime, the brain automatically finds and links the relevant statutes. Describe a scenario, and it surfaces the applicable ARS codes.</td></tr>
<tr><td><strong>Witness Credibility Scoring</strong></td><td>Track information sources — witnesses, tools, publications — with credibility scores that adjust based on consistency, corroboration, recency, and track record. Facts from credible sources carry more weight.</td></tr>
</table>

<br/>

### 🔒 Security & Integrity

<table>
<tr><td width="30%"><strong>Diamond Link</strong></td><td>Encrypted brain-to-brain sync. TLS 1.2+ with ECDHE+AESGCM ciphers, certificate pinning, HMAC-SHA256 message integrity, and replay protection via nonces. Pair brains with a one-time token, then sync knowledge across machines. Built for NextCloud and peer-to-peer deployment.</td></tr>
<tr><td><strong>Chain of Custody</strong></td><td>Every significant action — fact learned, sync completed, evidence stored — gets a SHA-256 hash-chained record. Like a blockchain for your knowledge. Tamper with one record and the chain breaks. Verifiable with a single command.</td></tr>
<tr><td><strong>Evidence Blob Store</strong></td><td>Content-addressable storage for binary evidence — screenshots, disk images, tool output. Each blob is SHA-256 hashed, linked to fact topics, and integrity-verified on retrieval. The hash IS the filename — content can't be swapped.</td></tr>
<tr><td><strong>Merkle DAG</strong></td><td>Merkle tree proofs for any fact in the store. Generate a cryptographic proof that a specific fact existed at a specific time, verifiable by anyone with the proof file — without revealing the rest of your knowledge.</td></tr>
<tr><td><strong>Homomorphic Confidence</strong></td><td>Multiple brains can vote on a fact's confidence without revealing their individual scores. Commitment-reveal protocol — commit your score, wait for others, then reveal simultaneously. No one can change their vote after seeing others'.</td></tr>
<tr><td><strong>CRDT Sync</strong></td><td>Conflict-free replicated data types with hybrid logical clocks. When two brains edit the same fact offline, CRDT merge gives a deterministic result — no conflicts, no manual resolution, no data loss.</td></tr>
</table>

<br/>

### 🛡️ Safety Systems

<table>
<tr><td width="30%"><strong>Diamond Quarantine</strong></td><td>Nothing leaves the brain permanently without a fight. Every deletion — prune, forget, tombstone — goes to quarantine first. 14-day mandatory hold. To permanently delete, you need the passphrase <code>PERMANENTLY DELETE</code>, a reason, and the brain will push back up to 2 times with concerns before accepting. Tagged items (verified facts, crime-related, cited) get extra warnings.</td></tr>
<tr><td><strong>The Third Eye</strong></td><td>13 automated detectors that continuously monitor brain health — orphaned evidence, graph isolation, stale crystals, crime facts without citations, facts never reviewed, silent agents, quarantine pressure, and more. Severity-graded alerts from MEDIUM to CRITICAL. Your brain's immune system.</td></tr>
<tr><td><strong>Selective Amnesia</strong></td><td>Controlled forgetting with a complete audit trail. Every forget operation is logged with who, what, when, and why. Every forget is reversible. The amnesia log is immutable — you can always see what was forgotten and restore it.</td></tr>
<tr><td><strong>Multi-Brain Consensus</strong></td><td>Ask multiple brains if they agree on a fact. Returns consensus level — strong (80%+), majority (60%+), partial (40%+), contested, or standalone. Trust but verify, across brains.</td></tr>
</table>

<br/>

### 🤖 AI & Integration

<table>
<tr><td width="30%"><strong>Neural Cortex</strong></td><td>RAG (Retrieval-Augmented Generation) pipeline that feeds relevant facts to an LLM for reasoning. Ask questions, generate hypotheses, cross-examine sources, build case timelines, and produce legal briefs — all grounded in your knowledge store. Works with LM Studio locally or any OpenAI-compatible API.</td></tr>
<tr><td><strong>HTTP Server</strong></td><td>Production-hardened HTTP bridge on port 7734. Thread-safe with RLock, input validation on every endpoint, base64 validation, 16MB request cap, no traceback leaks. 22 endpoints covering learn, recall, search, cortex, citations, graph, third eye, quarantine, and more. Designed for Diamond Drill integration.</td></tr>
<tr><td><strong>Agent Coordination</strong></td><td>Multiple AI agents can check in, report findings, and trigger escalations. HIGH and CRITICAL findings are automatically learned as facts. Built for swarm architectures where multiple agents analyze different aspects of a case.</td></tr>
<tr><td><strong>Command Memory</strong></td><td>Logs shell commands with flag parsing, tracks which flags you use most, and suggests flags based on frequency + recency (14-day half-life scoring). Optionally uses LLM for smart suggestions. Designed for Claude to remember its own commands across sessions.</td></tr>
<tr><td><strong>UCO/CASE Export</strong></td><td>Export your knowledge in Unified Cyber Ontology format — the international standard for digital forensic evidence exchange. Classifies facts as Tools, Observables, Actions, or Assertions automatically.</td></tr>
</table>

<br/>

### 📊 Visualization

<table>
<tr><td width="30%"><strong>Terminal Reports</strong></td><td>Rich ANSI-colored output — bar charts, box-drawn tables, connection graphs, heatmaps. Designed for WezTerm, Kitty, and Windows Terminal. Looks professional in any modern terminal.</td></tr>
<tr><td><strong>HTML Reports</strong></td><td>Standalone interactive HTML with dark theme, search, charts, and a built-in court document generator. One file, no dependencies, opens in any browser. Share reports with anyone.</td></tr>
</table>

<br/>

---

<br/>

## Quick Start

### Install

```bash
git clone https://github.com/Tunclon/diamond-brain.git
cd diamond-brain
```

No `pip install`. No `requirements.txt`. No Docker. Just [Python 3.10+](https://www.python.org/downloads/).

### First Run

```bash
python -m brain.diamond_brain
```

### Seed With Knowledge

```bash
python seed_forensics.py          # 119 digital forensics facts
python seed_ars_criminal.py       # 56 Arizona criminal statutes
```

### Use in Your Code

```python
from brain import DiamondBrain

brain = DiamondBrain()

# Learn something
brain.learn("security", "Always rotate JWT refresh tokens on use",
            confidence=95, source="OWASP", verified=True)

# Recall it later — even across sessions
facts = brain.recall("security", fuzzy=True)

# Search across everything
results = brain.search("token")

# Ask the cortex (needs LM Studio or compatible LLM)
answer = brain.cortex_ask("What do we know about authentication?")

# See your brain's health
print(brain.digest())
```

### Start the HTTP Server

```bash
python brain/server.py --port 7734 --bind 127.0.0.1
```

Now any application — including [Diamond Drill](https://github.com/Tunclon/diamond-drill) — can talk to the brain over HTTP.

<br/>

---

<br/>

## Zero Dependencies

Diamond Brain uses **only Python's standard library**. Nothing else. No numpy. No requests. No database drivers. No cloud SDKs.

The complete import list:

```
json · pathlib · difflib · math · hashlib · ssl · hmac · secrets
socket · subprocess · shutil · threading · textwrap · statistics
time · shlex · datetime · os · re · base64 · collections
```

Every one of these ships with Python. If you have Python, you have Diamond Brain.

<br/>

---

<br/>

## Everything Is Tested

**213 tests across 31 tiers.** Zero failures. Runs in under 1 second.

```bash
python -m unittest tests.test_diamond_brain -v
```

The [CI/CD pipeline](.github/workflows/diamond-ci.yml) runs 5 tiers on every push:

| Tier | What It Does |
|:-----|:-------------|
| **0 — Gates** | Syntax check, import check, digest smoke test |
| **1 — Test Matrix** | 213 tests across Python 3.10, 3.11, 3.12, 3.13 on Ubuntu, macOS, and Windows |
| **2 — Integration** | Seeds 175 facts + citations, exercises every feature end-to-end |
| **3 — CLI Smoke** | Runs every one of the 85 CLI commands |
| **4 — Security** | AST-verified: no `eval`/`exec`, no external imports, atomic writes confirmed, no secrets in code |

<br/>

---

<br/>

## The 85 CLI Commands

Every feature is accessible from the command line. Here are the highlights:

```bash
# ─── Your Knowledge ─────────────────────────────────────────
python -m brain.diamond_brain                                    # Full status dashboard
python -m brain.diamond_brain --learn "topic" "fact" 95          # Learn with 95% confidence
python -m brain.diamond_brain --recall "topic"                   # What do we know?
python -m brain.diamond_brain --search "keyword"                 # Search everything

# ─── Knowledge Graph ────────────────────────────────────────
python -m brain.diamond_brain --graph-index                      # Auto-build from all data
python -m brain.diamond_brain --graph-query "forensics"          # Fuzzy graph search
python -m brain.diamond_brain --graph-bfs "node" --depth 3       # Traverse connections

# ─── Legal ──────────────────────────────────────────────────
python -m brain.diamond_brain --cite "ARS 13-1105" "Murder" "..."
python -m brain.diamond_brain --citations --severity FELONY      # All felony statutes
python -m brain.diamond_brain --court-doc --type MOTION --case CR-2026-001

# ─── Brain Health ───────────────────────────────────────────
python -m brain.diamond_brain --third-eye-scan                   # 13-detector health check
python -m brain.diamond_brain --quarantine-stats                 # What's in quarantine?
python -m brain.diamond_brain --contradictions                   # Find disagreements
python -m brain.diamond_brain --fsrs-due                         # What needs review?

# ─── Diamond Link ───────────────────────────────────────────
python -m brain.diamond_brain --link-init "My Brain"             # Create TLS identity
python -m brain.diamond_brain --link-pair-start --port 7777      # Wait for peer
python -m brain.diamond_brain --link-sync <peer_fingerprint>     # Encrypted sync
python -m brain.diamond_brain --link-custody --verify            # Verify chain integrity

# ─── Safety ─────────────────────────────────────────────────
python -m brain.diamond_brain --forget "topic" "pattern" "reason"
python -m brain.diamond_brain --amnesia-restore "topic" "pattern"
python -m brain.diamond_brain --quarantine-purge <batch> "PERMANENTLY DELETE"

# ─── AI Integration ─────────────────────────────────────────
python -m brain.diamond_brain --cortex-ask "What happened on Jan 15?"
python -m brain.diamond_brain --cortex-brief --case-number CR-2026-001
python -m brain.diamond_brain --cortex-hypothesize "Who had motive?"

# ─── Reports ────────────────────────────────────────────────
python -m brain.diamond_brain --visual                           # Terminal report
python -m brain.diamond_brain --html report.html                 # Interactive HTML
python -m brain.diamond_brain --case-export evidence.json        # UCO/CASE format
```

<br/>

---

<br/>

## The HTTP Server

`brain/server.py` — a production-hardened HTTP bridge for Diamond Brain.

```bash
python brain/server.py --port 7734 --bind 127.0.0.1
```

**22 endpoints**, thread-safe with `threading.RLock`, input validation on every route, no traceback leaks.

| Endpoint | What It Does |
|:---------|:-------------|
| `GET /status` | Brain health dashboard |
| `POST /learn` | Learn a fact |
| `POST /recall` | Recall facts by topic (returns full metadata) |
| `POST /search` | Keyword search |
| `POST /hybrid_search` | Keyword + graph combined search |
| `POST /batch_learn` | Learn many facts in one call |
| `POST /cortex_ask` | Ask the AI cortex a question |
| `POST /cite` | Store a legal citation |
| `POST /recall_citations` | Search citations |
| `POST /blob_store` | Store binary evidence (base64) |
| `POST /agent_checkin` | Register an AI agent |
| `POST /agent_report` | Submit agent findings |
| `POST /temporal_add` | Add a temporal event |
| `POST /graph_auto_index` | Rebuild knowledge graph |
| `POST /third_eye_scan` | Run health detectors |
| `POST /quarantine_list` | View quarantined items |
| `POST /cortex_summarize` | Summarize a topic |
| `POST /cortex_hypothesize` | Generate hypotheses |
| `POST /detect_contradictions` | Find contradictions |
| `POST /forget` | Controlled forgetting |
| `POST /amnesia_restore` | Restore forgotten facts |
| `POST /amnesia_log` | View forget/restore history |

<br/>

---

<br/>

## Storage

Everything lives in `brain/memory/` as human-readable JSON. You can open any file in a text editor.

```
brain/memory/
├── facts.json            Knowledge facts with confidence, sources, timestamps
├── citations.json        Legal citations (ARS, rules, constitutional)
├── agents.json           AI agent registry
├── commands.json         Shell command history (50K rolling window)
├── escalations.json      Items needing human review
├── graph.json            Knowledge graph (nodes + typed edges)
├── temporal.json         Temporal events
├── amnesia.json          Forget/restore audit trail (immutable)
├── sources.json          Witness & source credibility tracking
├── quarantine.json       Deleted items in 14-day holding
├── link/
│   ├── key.pem           RSA 2048 private key (never leaves this machine)
│   ├── cert.pem          Self-signed X.509 certificate
│   ├── identity.json     Your brain's fingerprint
│   ├── peers.json        Authorized peers + trust scores
│   ├── sync_log.json     Sync history
│   └── custody.json      Hash-chained custody records
└── blobs/
    ├── manifest.json     Evidence metadata index
    └── <sha256_hash>     Binary evidence files
```

**Every write is atomic** — data is written to a `.tmp` file first, then renamed with `os.replace()`. Even if power cuts mid-write, your data is safe.

<br/>

---

<br/>

## Pre-Seeded Knowledge

### Digital Forensics — 119 Facts

```bash
python seed_forensics.py
```

Covers [Autopsy](https://www.autopsy.com/), [Volatility 3](https://github.com/volatilityfoundation/volatility3), [Wireshark](https://www.wireshark.org/), [Zeek](https://zeek.org/), [YARA](https://virustotal.github.io/yara/), [Ghidra](https://ghidra-sre.org/), [Plaso](https://github.com/log2timeline/plaso), [Chainsaw](https://github.com/WithSecureLabs/chainsaw), [Hayabusa](https://github.com/Yamato-Security/hayabusa). Windows, Linux, and macOS artifact analysis. Methodologies from [NIST SP 800-86](https://csrc.nist.gov/pubs/sp/800/86/final), [SANS DFIR](https://www.sans.org/digital-forensics-incident-response/), [MITRE ATT&CK](https://attack.mitre.org/), and [RFC 3227](https://datatracker.ietf.org/doc/html/rfc3227).

### Arizona Criminal Law — 56 Citations

```bash
python seed_ars_criminal.py
```

Covers: Homicide ([ARS 13-1102](https://www.azleg.gov/ars/13/01102.htm)–[1105](https://www.azleg.gov/ars/13/01105.htm)), Assault, Self-Defense ([Castle Doctrine](https://www.azleg.gov/ars/13/00411.htm)), Drug Offenses, DUI ([ARS 28-1381](https://www.azleg.gov/ars/28/01381.htm)), Weapons, Domestic Violence, Criminal Procedure, [Miranda Rights](https://www.azleg.gov/ars/13/03884.htm), Search & Seizure, [AZ Constitutional Rights](https://www.azleg.gov/constitution/), Sentencing Ranges, [Rules of Evidence](https://govt.westlaw.com/azrules/Browse/Home/Arizona/ArizonaRulesofEvidence) (401–803).

<br/>

---

<br/>

## Integration

### Drop Into Any Project

```bash
bash setup_template.sh /path/to/your/project
# or just:
cp -r brain/ /your/project/brain/
```

Then:

```python
from brain import DiamondBrain
brain = DiamondBrain(memory_dir="/your/custom/path")
```

### With Diamond Drill (Rust Forensics TUI)

Diamond Brain is the intelligence backend for [Diamond Drill](https://github.com/Tunclon/diamond-drill) — a Rust-based forensic analysis TUI. Drill auto-detects the brain server, sends findings via HTTP, and the brain persists everything with full chain of custody.

```bash
# Terminal 1: Start the brain
python brain/server.py --port 7734

# Terminal 2: Drill auto-connects
diamond-drill --brain http://localhost:7734
```

### With LM Studio

The Neural Cortex connects to [LM Studio](https://lmstudio.ai) on `localhost:1234` for AI-powered features. See [`LM_STUDIO_GUIDE.md`](LM_STUDIO_GUIDE.md) for model recommendations and setup.

<br/>

---

<br/>

---

<br/>

# Technical Reference

*Everything below is for developers, AI agents, and the technically curious.*

<br/>

## The Full API

### Knowledge Management

| Method | Returns | Description |
|:-------|:--------|:------------|
| `learn(topic, fact, confidence, source, verified)` | `dict` | Store fact with 80% fuzzy dedup via [`difflib.SequenceMatcher`](https://docs.python.org/3/library/difflib.html) |
| `recall(topic, max_results=15, fuzzy=False)` | `list[dict]` | Retrieve by topic, sorted by effective confidence with time decay |
| `search(keyword)` | `list[dict]` | Case-insensitive cross-field keyword search |
| `advanced_recall(query, max_results=15)` | `list[dict]` | Association chaining — follows `links` array across topics |
| `hybrid_search(query, top_k=10)` | `list[dict]` | Keyword (60%) + graph connectivity (40%) combined scoring |
| `prune_stale(max_age_days=90, min_confidence=30)` | `int` | Remove old/low-confidence facts → quarantine |
| `digest()` | `dict` | Full brain status: counts, ages, health, Third Eye alerts |
| `heatmap()` | `dict` | Per-topic freshness scores (0–100) |

### Knowledge Graph

| Method | Returns | Description |
|:-------|:--------|:------------|
| `graph_add_node(node_id, node_type, data)` | `dict` | Add node (types: fact, citation, topic, crystal, blob, event) |
| `graph_add_edge(source, target, edge_type, weight)` | `dict` | Add typed edge (supports, contradicts, related, cites, etc.) |
| `graph_remove_edge(source, target, edge_type)` | `dict` | Remove edge |
| `graph_bfs(start, max_depth=3, edge_types)` | `list[dict]` | Breadth-first traversal |
| `graph_neighbors(node_id, edge_type)` | `list[dict]` | Immediate neighbors |
| `graph_query(query, max_depth=2)` | `list[dict]` | Fuzzy node search |
| `graph_auto_index()` | `dict` | Build graph from all facts + citations automatically |
| `graph_stats()` | `dict` | Node/edge counts by type |

### FSRS Spaced Repetition

Power-law forgetting: `R(t,S) = (1 + t/(9*S))^(-1)` — based on [FSRS-4](https://github.com/open-spaced-repetition/fsrs4anki).

| Method | Returns | Description |
|:-------|:--------|:------------|
| `fsrs_retrievability(fact)` | `float` | Current retrievability (0.0–1.0) |
| `fsrs_review(topic, fact_text, rating)` | `dict` | Record review: 1=forgot, 2=hard, 3=good, 4=easy |
| `fsrs_due(threshold=0.9, max_results=15)` | `list[dict]` | Facts below retrievability threshold |
| `fsrs_stats()` | `dict` | Review totals, avg retrievability, due counts |

### Temporal Reasoning

Full [Allen's Interval Algebra](https://en.wikipedia.org/wiki/Allen%27s_interval_algebra) — 13 relations.

| Method | Returns | Description |
|:-------|:--------|:------------|
| `temporal_add(event_id, start, end, data)` | `dict` | Register event with ISO 8601 timestamps |
| `temporal_relation(a_id, b_id)` | `str` | One of 13 Allen relations |
| `temporal_chain(event_ids)` | `list[dict]` | Chronologically ordered chain |
| `temporal_timeline(start, end)` | `list[dict]` | Events within time range |
| `temporal_detect_anomalies()` | `list[dict]` | Impossible sequences, suspicious gaps, speed violations |
| `temporal_anomaly_summary()` | `dict` | Anomaly type counts |

### Legal Intelligence

| Method | Returns | Description |
|:-------|:--------|:------------|
| `cite(code, title, text, category, severity, jurisdiction)` | `dict` | Store citation, dedup by code |
| `recall_citations(query, category, severity)` | `list[dict]` | Search with stackable filters |
| `citation_stats()` | `dict` | Counts by category/severity/jurisdiction |
| `link_crime_to_citations(topic, text)` | `list` | Auto-find relevant ARS codes |
| `generate_court_document(doc_type, case_number, defendant, sections)` | `str` | Formatted legal document |

### Witness Credibility

| Method | Returns | Description |
|:-------|:--------|:------------|
| `source_register(source_id, source_type, name)` | `dict` | Register an information source |
| `source_credibility(source_id)` | `dict` | Computed credibility score |
| `source_adjust_credibility(source_id, delta)` | `dict` | Manual trust adjustment |
| `source_list()` | `list[dict]` | All sources ranked by credibility |
| `source_weighted_confidence(fact)` | `float` | Fact confidence weighted by source credibility |
| `source_credibility_trend(source_id)` | `dict` | Credibility over time |

### Diamond Link (Encrypted Sync)

| Method | Returns | Description |
|:-------|:--------|:------------|
| `link_init(display_name)` | `dict` | Generate TLS identity (RSA 2048 + X.509) |
| `link_identity()` | `dict` | This brain's fingerprint + name |
| `link_pair_start(port=7777, timeout=300)` | `dict` | Listen for peer (returns 64-char token) |
| `link_pair_connect(host, port, token)` | `dict` | Connect and complete pairing |
| `link_peers()` | `list[dict]` | Authorized peers with sync stats |
| `link_unpair(peer_fingerprint)` | `dict` | Revoke peer |
| `link_serve(port=7777)` | — | Start TLS sync server |
| `link_sync(peer_fp, topics, direction, dry_run)` | `dict` | Sync knowledge with peer |
| `link_set_shared_topics(peer_fp, topics)` | `dict` | Configure per-peer topic sharing |
| `link_status()` | `dict` | Identity + peers + recent syncs |
| `link_log(last_n=15)` | `list[dict]` | Sync history |
| `link_custody_log(last_n=15)` | `list[dict]` | Chain of custody records |
| `link_verify_custody_chain()` | `dict` | Verify SHA-256 hash chain integrity |
| `link_peer_reputation(peer_fp)` | `dict` | Trust score based on sync history |
| `link_adjust_trust(peer_fp, delta)` | `dict` | Manual trust adjustment |
| `link_subscribe(peer_fp, topics)` | `dict` | Subscribe to peer topic updates |
| `link_unsubscribe(peer_fp, topics)` | `dict` | Unsubscribe |
| `link_poll_subscriptions()` | `dict` | Check for subscription updates |

### Safety Systems

| Method | Returns | Description |
|:-------|:--------|:------------|
| `forget(topic, fact_pattern, reason)` | `dict` | Controlled forgetting with audit trail → quarantine |
| `amnesia_log(last_n=15)` | `list[dict]` | Forget/restore history (immutable) |
| `amnesia_restore(topic, fact_pattern)` | `dict` | Restore forgotten facts |
| `quarantine_list(status, batch_id)` | `list[dict]` | View quarantined items |
| `quarantine_stats()` | `dict` | Counts by status/source/batch |
| `quarantine_preview(batch_id)` | `list[dict]` | Preview with brain-generated reasons |
| `quarantine_restore(entry_id)` | `dict` | Restore to active facts |
| `quarantine_purge(batch_id, passphrase, reason, override)` | `dict` | Permanent delete (requires "PERMANENTLY DELETE") |
| `quarantine_status()` | `dict` | Summary with critical tag counts |
| `third_eye_scan(include_types)` | `list[dict]` | Run 13 health detectors |
| `third_eye_summary()` | `dict` | Alert summary by severity |
| `third_eye_suppress(alert_type, duration_days)` | `dict` | Suppress false positives |
| `third_eye_watch(topic)` | `dict` | Add topic to watchlist |
| `third_eye_status()` | `dict` | Detector status + suppression list |

### Cryptographic Integrity

| Method | Returns | Description |
|:-------|:--------|:------------|
| `merkle_build()` | `dict` | Build Merkle tree from all facts |
| `merkle_prove(fact_index)` | `dict` | Generate inclusion proof |
| `merkle_verify_proof(proof)` | `bool` | Verify proof (static method) |
| `merkle_status()` | `dict` | Tree root, depth, leaf count |
| `crdt_upgrade_facts()` | `dict` | Migrate facts to CRDT format |
| `crdt_merge_snapshot(snapshot)` | `dict` | Merge remote CRDT snapshot |
| `crdt_tombstone(topic, fact_text)` | `dict` | CRDT soft-delete → quarantine |
| `crdt_status()` | `dict` | CRDT statistics |
| `hc_initiate(topic, fact, score, n_peers)` | `dict` | Start homomorphic confidence vote |
| `hc_receive_commitment(session_hash, peer_fp, commitment)` | `dict` | Receive peer commitment |
| `hc_reveal(session_hash)` | `dict` | Reveal this brain's score |
| `hc_receive_reveal(session_hash, peer_fp, score, nonce)` | `dict` | Receive peer reveal |
| `hc_aggregate(session_hash)` | `dict` | Compute final aggregated confidence |
| `hc_status(session_hash)` | `dict` | Session status |

### Neural Cortex (AI Integration)

| Method | Returns | Description |
|:-------|:--------|:------------|
| `cortex_ask(question, topics, max_context)` | `dict` | RAG — retrieves facts, sends to LLM |
| `cortex_summarize(topic)` | `dict` | Bullet-point summary of topic |
| `cortex_hypothesize(evidence_facts, question)` | `dict` | Generate hypotheses from evidence |
| `cortex_cross_examine(source_id)` | `dict` | Challenge source credibility |
| `cortex_case_brief(topics)` | `dict` | Generate legal case brief |
| `cortex_timeline_narrative(events)` | `dict` | Chronological narrative from events |
| `cortex_status()` | `dict` | LLM connection status |

### Visualization & Export

| Method | Returns | Description |
|:-------|:--------|:------------|
| `visual_report(topic=None)` | `str` | ANSI terminal report |
| `visual_bar_chart(data, title)` | `str` | Colored bar chart |
| `visual_table(headers, rows, title)` | `str` | Box-drawn table |
| `visual_connection_graph(center, connections)` | `str` | Text connection graph |
| `export_html(output_path)` | `str` | Standalone interactive HTML report |
| `export_case_uco(output_path)` | `dict` | UCO/CASE ontology JSON-LD |
| `case_validate_export(path)` | `dict` | Validate UCO export structure |

### Agents & Commands

| Method | Returns | Description |
|:-------|:--------|:------------|
| `agent_checkin(agent_id, role, task)` | `dict` | Register/update agent |
| `agent_report(agent_id, findings)` | `dict` | Submit findings (HIGH+ auto-learned) |
| `escalation_needed(finding)` | `bool` | Check if finding needs human review |
| `consensus_check(topic, fact_text)` | `dict` | Multi-brain fact agreement |
| `log_command(raw_command, cwd)` | `dict` | Parse and store shell command |
| `suggest_flags(command, subcommand)` | `list[dict]` | Frequency + recency ranked suggestions |
| `smart_suggest(command, subcommand, cwd)` | `list[dict]` | LLM-powered suggestions |
| `command_stats(command=None)` | `dict` | Usage statistics |

<br/>

---

<br/>

## Security Architecture

| Layer | Implementation |
|:------|:---------------|
| **Transport** | TLS 1.2+ via Python [`ssl`](https://docs.python.org/3/library/ssl.html), ECDHE+AESGCM ciphers only |
| **Identity** | RSA 2048 keypair, self-signed X.509 cert, SHA-256 fingerprint |
| **Authentication** | Certificate pinning after out-of-band pairing |
| **Pairing** | 64-char hex token via [`secrets.token_hex`](https://docs.python.org/3/library/secrets.html), 5-minute expiry |
| **Message Integrity** | HMAC-SHA256 on every message |
| **Wire Format** | `<4-byte length><JSON body><32-byte HMAC tag>` over TLS |
| **Replay Protection** | Cryptographic nonce in every message |
| **Chain of Custody** | SHA-256 hash chain — immutable, verifiable |
| **Key Protection** | `0o600` permissions, never transmitted, never logged |
| **No Plaintext** | TLS is mandatory. No `--insecure` flag exists. |

<br/>

---

<br/>

## Architecture

```
                              ┌─────────────────────────────────┐
                              │     ◆  Diamond Brain v3.0  ◆    │
                              │    116 Methods · 0 Dependencies  │
                              └───────────────┬─────────────────┘
             ┌──────────┬──────────┬──────────┼──────────┬──────────┬──────────┐
             │          │          │          │          │          │          │
        ┌────┴────┐ ┌───┴───┐ ┌───┴────┐ ┌───┴───┐ ┌───┴────┐ ┌──┴───┐ ┌───┴────┐
        │  Facts  │ │ Graph │ │  FSRS  │ │Temporal│ │  Cite  │ │Agents│ │ Cortex │
        │  Store  │ │ Index │ │ Review │ │Reasoner│ │ Store  │ │ Store│ │  (LLM) │
        └────┬────┘ └───┬───┘ └───┬────┘ └───┬───┘ └───┬────┘ └──┬───┘ └───┬────┘
             │          │         │           │         │          │         │
             └──────────┴────┬────┴───────────┴─────────┘          │         │
                             │                                     │         │
        ┌────────────────────┼────────────────────┐                │         │
        │                    │                    │                │         │
   ┌────┴─────┐  ┌──────────┴──────────┐  ┌──────┴──────┐  ┌─────┴─────┐   │
   │ Terminal  │  │    Interactive      │  │   Court     │  │  Diamond  │   │
   │ Visuals   │  │   HTML Report      │  │   Docs      │  │   Link    │   │
   └──────────┘  └─────────────────────┘  └─────────────┘  └─────┬─────┘   │
                                                                  │         │
                                                  ┌───────┬───────┼─────┐   │
                                                  │       │       │     │   │
                                             ┌────┴──┐ ┌──┴──┐ ┌─┴──┐ ┌┴───┴──┐
                                             │ Sync  │ │Pair │ │Blob│ │ HTTP  │
                                             │Engine │ │ TLS │ │ DB │ │Server │
                                             └───────┘ └─────┘ └────┘ │ :7734 │
                                                                       └───────┘
```

<br/>

---

<br/>

## Requirements

| Requirement | Details |
|:------------|:--------|
| **Python** | [3.10+](https://www.python.org/downloads/) (uses `str \| None` union syntax) |
| **Packages** | None. Zero. Stdlib only. |
| **OpenSSL** | For Diamond Link cert generation (pre-installed on Linux/macOS, via [Git for Windows](https://gitforwindows.org/) on Windows) |
| **LM Studio** | Optional — for Neural Cortex AI features ([download](https://lmstudio.ai)) |
| **Disk Space** | ~50KB for code, storage grows with your knowledge |

<br/>

---

<br/>

## License

[MIT](LICENSE) — use it, fork it, build on it.

<br/>

---

<br/>

<p align="center">
  <img src="https://img.shields.io/badge/◆-00d4ff?style=for-the-badge&labelColor=0a0a0a&label=%20" alt="Diamond" />
</p>

<h3 align="center">Built With Pride</h3>

<p align="center">
  <strong>Diamond Brain is a collaboration between<br/>
  <a href="https://github.com/Tunclon">Ryan Cashmoney</a> (human architect) and <a href="https://claude.ai">Claude</a> (AI engineer, Anthropic).</strong>
</p>

<p align="center">
  Ryan designed the vision — a persistent intelligence layer for AI agents,<br/>
  built for legal professionals and forensic investigators who need<br/>
  knowledge that survives reboots, crashes, and context window limits.<br/><br/>
  Claude wrote the implementation — 9,600 lines of zero-dependency Python,<br/>
  31 feature systems, 213 tests, and a security architecture<br/>
  built on nothing but the standard library.<br/><br/>
  Every line was reviewed by both minds.<br/>
  Every feature was debated, refined, and hardened together.<br/><br/>
  This is what human-AI collaboration looks like when both sides bring their best.
</p>

<p align="center">
  <em>Diamond Brain — Because knowledge should persist.</em>
</p>
</content>
</invoke>