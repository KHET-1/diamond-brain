<p align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+" /></a>
  <a href="#requirements"><img src="https://img.shields.io/badge/Dependencies-Zero-brightgreen?style=flat-square" alt="Zero Dependencies" /></a>
  <a href="#storage"><img src="https://img.shields.io/badge/Storage-JSON-orange?style=flat-square" alt="JSON Storage" /></a>
  <a href="#cicd-pipeline"><img src="https://img.shields.io/badge/Tests-112-green?style=flat-square" alt="112 Tests" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="MIT License" /></a>
</p>

<h1 align="center">Diamond Brain v2.0</h1>

<p align="center">
  <strong>Standalone Knowledge Cache + Legal Intelligence + Encrypted Brain-to-Brain Linking</strong><br/>
  <em>Facts. Citations. Knowledge Graphs. Spaced Repetition. Temporal Reasoning. Encrypted Sync. Zero Dependencies.</em>
</p>

---

## Table of Contents

- [What It Does](#what-it-does)
- [Quick Start](#quick-start)
- [CLI Reference](#cli-reference)
- [API Reference](#api-reference)
  - [Knowledge](#knowledge)
  - [Knowledge Graph](#knowledge-graph)
  - [FSRS Spaced Repetition](#fsrs-spaced-repetition)
  - [Confidence Propagation](#confidence-propagation)
  - [Contradiction Detection](#contradiction-detection)
  - [Crystallization](#crystallization)
  - [Temporal Reasoning](#temporal-reasoning)
  - [Legal Citations](#legal-citations)
  - [Court Documents](#court-documents)
  - [Diamond Link (Encrypted Sync)](#diamond-link-encrypted-sync)
  - [Peer Reputation](#peer-reputation)
  - [Selective Amnesia](#selective-amnesia)
  - [Multi-Brain Consensus](#multi-brain-consensus)
  - [Live Subscriptions](#live-subscriptions)
  - [Evidence Blob Store](#evidence-blob-store)
  - [Visual Reports](#visual-reports)
  - [Command Memory](#command-memory)
  - [Agents](#agents)
- [Storage](#storage)
- [Security Architecture](#security-architecture-diamond-link)
- [CI/CD Pipeline](#cicd-pipeline)
- [Pre-Seeded Knowledge](#pre-seeded-knowledge)
- [LM Studio Integration](#lm-studio-integration)
- [Integration](#integration)
- [Architecture](#architecture)
- [Requirements](#requirements)
- [License](#license)

---

## What It Does

Diamond Brain is a JSON-backed intelligence layer that persists across AI sessions. Drop it into any [Python](https://www.python.org/) project and get:

| Capability | Description |
|:---|:---|
| **Knowledge Store** | Facts with confidence scores, time decay, fuzzy dedup ([difflib](https://docs.python.org/3/library/difflib.html)), auto-linking between topics |
| **[Knowledge Graph](#knowledge-graph)** | Nodes + typed edges, [BFS](https://en.wikipedia.org/wiki/Breadth-first_search) traversal, auto-indexing from facts/citations |
| **[FSRS Spaced Repetition](#fsrs-spaced-repetition)** | Real memory science — stability, difficulty, retrievability ([FSRS algorithm](https://github.com/open-spaced-repetition/fsrs4anki)) |
| **[Confidence Propagation](#confidence-propagation)** | Belief networks — when fact A drops, connected facts propagate the change |
| **[Contradiction Detection](#contradiction-detection)** | Negation flip, antonym swap, and confidence conflict detection |
| **[Crystallization](#crystallization)** | Auto-summarize fact clusters into higher-level insight nodes |
| **[Temporal Reasoning](#temporal-reasoning)** | [Allen's Interval Algebra](https://en.wikipedia.org/wiki/Allen%27s_interval_algebra) — 13 temporal relations, causal chains, timelines |
| **[Legal Citations](#legal-citations)** | [Arizona Revised Statutes](https://www.azleg.gov/arstitle/), Rules of Evidence, Criminal Procedure, Constitutional provisions |
| **[Court Documents](#court-documents)** | Court-ready document generator with proper formatting, case captions, citation appendices |
| **[Diamond Link](#diamond-link-encrypted-sync)** | Encrypted brain-to-brain sync over [TLS 1.2+](https://docs.python.org/3/library/ssl.html) with certificate pinning and chain of custody |
| **[Evidence Blob Store](#evidence-blob-store)** | Content-addressable [SHA-256](https://en.wikipedia.org/wiki/SHA-2) storage for binary evidence (code, screenshots, tool output) |
| **[Selective Amnesia](#selective-amnesia)** | Controlled forgetting with audit trail and restore capability |
| **[Multi-Brain Consensus](#multi-brain-consensus)** | Cross-brain fact verification (strong/majority/partial/contested) |
| **[Visual Reports](#visual-reports)** | ANSI terminal charts, tables, connection graphs + interactive HTML reports |
| **[Command Memory](#command-memory)** | Shell command logging, flag frequency tracking, LLM-powered suggestions |
| **[Agent Coordination](#agents)** | Multi-agent check-in, findings reporting, auto-escalation |

**Zero external dependencies.** [Python 3.10+](https://www.python.org/downloads/) stdlib only.

---

## Quick Start

### Install

```bash
git clone https://github.com/Tunclon/diamond-brain.git
cd diamond-brain
```

No `pip install`. No `requirements.txt`. Just [Python](https://www.python.org/downloads/).

### First Run

```bash
python -m brain.diamond_brain
```

### Seed Knowledge

```bash
python seed_forensics.py          # 119 digital forensics facts
python seed_ars_criminal.py       # 56 Arizona criminal statutes
```

### Use in Python

```python
from brain.diamond_brain import DiamondBrain

brain = DiamondBrain()

# Learn facts
brain.learn("authentication", "JWT refresh tokens should rotate on use",
            confidence=95, source="OWASP", verified=True)

# Recall with fuzzy matching
facts = brain.recall("auth", fuzzy=True)

# Knowledge Graph
brain.graph_auto_index()                  # Build graph from facts + citations
brain.graph_bfs("forensics", max_depth=3) # Traverse connections
brain.graph_query("disk imaging")         # Fuzzy graph search

# FSRS Spaced Repetition
due = brain.fsrs_due(threshold=0.9)       # What needs review?
brain.fsrs_review("topic", "fact", 4)     # Rate recall (1=forgot, 4=easy)

# Temporal Reasoning
brain.temporal_add("arrest", "2026-01-15T10:00:00Z", "2026-01-15T10:30:00Z")
brain.temporal_add("search", "2026-01-15T10:15:00Z", "2026-01-15T11:00:00Z")
brain.temporal_relation("arrest", "search")  # -> "overlaps"
brain.temporal_chain()                        # Chronological ordering

# Legal citations
brain.cite("ARS 13-1105", "First Degree Murder",
           "A person commits first degree murder if...",
           category="statute", severity="FELONY", jurisdiction="AZ")
brain.recall_citations(query="murder", severity="FELONY")

# Court documents
doc = brain.generate_court_document(
    case_number="CR-2026-001234",
    defendant="John Doe",
    doc_type="MOTION",
    title="Motion to Suppress Evidence",
    sections=[{
        "heading": "Unlawful Search",
        "body": "Officers conducted a warrantless search...",
        "citations": ["ARS 13-3887", "AZ CONST ART 2 SEC 8"],
    }],
)

# Diamond Link -- Encrypted Brain-to-Brain Sync
brain.link_init("My Brain")                     # Generate TLS identity
brain.link_pair_start(port=7777)                # Listen for peer (Terminal 1)
brain.link_pair_connect("host", 7777, "token")  # Connect to peer (Terminal 2)
brain.link_sync("peer_fp_prefix")               # Sync knowledge

# Evidence Blob Store
stored = brain.blob_store(b"forensic evidence bytes", {"description": "disk image hash"})
brain.blob_verify(stored["hash"])               # Integrity check
brain.blob_link(stored["hash"], "forensics")    # Link blob to fact topic

# Selective Amnesia
brain.forget("topic", "pattern", "reason for forgetting")
brain.amnesia_log()                             # Audit trail
brain.amnesia_restore("topic", "pattern")       # Undo forget

# Contradiction Detection
contradictions = brain.detect_contradictions()

# Crystallization
crystals = brain.crystallize(min_cluster=5)     # Auto-summarize clusters

# Export interactive HTML report
brain.export_html("report.html")
```

---

## CLI Reference

```bash
# --- Status -----------------------------------------------
python -m brain.diamond_brain                          # Digest + heatmap

# --- Knowledge --------------------------------------------
python -m brain.diamond_brain --recall <topic>
python -m brain.diamond_brain --search <keyword>
python -m brain.diamond_brain --learn <topic> <fact> [confidence] [source]
python -m brain.diamond_brain --prune [max_age_days] [min_confidence]

# --- Knowledge Graph --------------------------------------
python -m brain.diamond_brain --graph-index            # Auto-build from facts/citations
python -m brain.diamond_brain --graph-stats            # Node/edge counts by type
python -m brain.diamond_brain --graph-query <query> [--depth N]
python -m brain.diamond_brain --graph-bfs <start> [--depth N]

# --- FSRS Spaced Repetition ------------------------------
python -m brain.diamond_brain --fsrs-stats             # Retrievability overview
python -m brain.diamond_brain --fsrs-due               # Facts due for review
python -m brain.diamond_brain --fsrs-review <topic> <fact_prefix> <rating>

# --- Temporal Reasoning -----------------------------------
python -m brain.diamond_brain --temporal-add <id> <start> [end]
python -m brain.diamond_brain --temporal-relation <id_a> <id_b>
python -m brain.diamond_brain --temporal-chain

# --- Contradiction Detection ------------------------------
python -m brain.diamond_brain --contradictions

# --- Crystallization --------------------------------------
python -m brain.diamond_brain --crystallize

# --- Legal Citations --------------------------------------
python -m brain.diamond_brain --cite <code> <title> <text> [--severity FELONY]
python -m brain.diamond_brain --citations [query] [--severity FELONY]
python -m brain.diamond_brain --citation-stats

# --- Court Documents --------------------------------------
python -m brain.diamond_brain --court-doc [--case X] [--defendant X] [--type MOTION]

# --- Visual Reports ---------------------------------------
python -m brain.diamond_brain --visual [topic]         # ANSI terminal report
python -m brain.diamond_brain --html [output.html]     # Interactive HTML report

# --- Diamond Link (Encrypted Sync) -----------------------
python -m brain.diamond_brain --link-init [name]       # Generate TLS identity
python -m brain.diamond_brain --link-identity          # Show fingerprint
python -m brain.diamond_brain --link-pair-start [--port 7777]
python -m brain.diamond_brain --link-pair-connect <host:port> <token>
python -m brain.diamond_brain --link-peers             # List authorized peers
python -m brain.diamond_brain --link-unpair <fp>       # Remove peer
python -m brain.diamond_brain --link-serve [--port 7777]
python -m brain.diamond_brain --link-sync <fp> [--topics t1,t2] [--direction both|push|pull] [--dry-run]
python -m brain.diamond_brain --link-set-topics <fp> <topic1,topic2>
python -m brain.diamond_brain --link-status            # Identity + peers + syncs
python -m brain.diamond_brain --link-log [--last N]    # Sync history
python -m brain.diamond_brain --link-custody           # Chain of custody log
python -m brain.diamond_brain --link-custody --verify  # Verify chain integrity

# --- Evidence Blob Store ----------------------------------
python -m brain.diamond_brain --blob-store <file> [--description X]
python -m brain.diamond_brain --blob-list
python -m brain.diamond_brain --blob-verify <hash>
python -m brain.diamond_brain --blob-link <hash> <topic>

# --- Selective Amnesia ------------------------------------
python -m brain.diamond_brain --forget <topic> <pattern> <reason>
python -m brain.diamond_brain --amnesia-log
python -m brain.diamond_brain --amnesia-restore <topic> <pattern>

# --- Consensus --------------------------------------------
python -m brain.diamond_brain --consensus <topic> <fact_text>

# --- Peer Reputation --------------------------------------
python -m brain.diamond_brain --peer-reputation <fp>

# --- Subscriptions ----------------------------------------
python -m brain.diamond_brain --subscribe <fp> <topic1,topic2>
python -m brain.diamond_brain --unsubscribe <fp> <topic1,topic2>

# --- Command Memory ---------------------------------------
python -m brain.diamond_brain --log-command "git push --force"
python -m brain.diamond_brain --suggest "git" [--smart] [--top N]
python -m brain.diamond_brain --command-stats [command]
python -m brain.diamond_brain --shell-hook              # Auto-log setup
```

---

## API Reference

### Knowledge

| Method | Description |
|:-------|:------------|
| `learn(topic, fact, confidence, source, verified)` | Store a fact. Fuzzy dedup at 80% similarity via [`difflib.SequenceMatcher`](https://docs.python.org/3/library/difflib.html#difflib.SequenceMatcher). |
| `recall(topic, max_results=15, fuzzy=False)` | Retrieve facts sorted by confidence with time decay. |
| `search(keyword)` | Case-insensitive keyword search across all facts. |
| `advanced_recall(query, max_results=15)` | Association chaining — follows topic links automatically. |
| `heatmap()` | Per-topic freshness scores (0-100). |
| `prune_stale(max_age_days=90)` | Remove old, low-confidence, unverified facts. |

### Knowledge Graph

| Method | Description |
|:-------|:------------|
| `graph_add_node(node_id, node_type, data)` | Add a node to the knowledge graph. |
| `graph_add_edge(source, target, edge_type, weight=1.0)` | Create a typed edge between nodes. |
| `graph_remove_edge(source, target, edge_type)` | Remove edges between nodes. |
| `graph_bfs(start, max_depth=3, edge_types)` | [Breadth-first](https://en.wikipedia.org/wiki/Breadth-first_search) traversal from a starting node. |
| `graph_neighbors(node_id, edge_type)` | Get immediate neighbors of a node. |
| `graph_query(query, max_depth=2)` | Fuzzy search the graph by keyword. |
| `graph_auto_index()` | Build graph from all facts and citations automatically. |
| `graph_stats()` | Node/edge counts by type. |

### FSRS Spaced Repetition

Based on the [FSRS-4 algorithm](https://github.com/open-spaced-repetition/fsrs4anki) — power-law forgetting curve `R(t,S) = (1 + t/(9*S))^(-1)`.

| Method | Description |
|:-------|:------------|
| `fsrs_retrievability(fact)` | Calculate current retrievability (0-1) using power-law forgetting. |
| `fsrs_review(topic, fact_text, rating)` | Record a review (1=forgot, 2=hard, 3=good, 4=easy). Updates stability + difficulty. |
| `fsrs_due(threshold=0.9, max_results=15)` | Facts whose retrievability has dropped below threshold. |
| `fsrs_stats()` | Overview: average retrievability, due counts, review totals. |

### Confidence Propagation

| Method | Description |
|:-------|:------------|
| `propagate_confidence(node_id, delta, decay=0.7, max_depth=3)` | Propagate confidence change through [graph edges](#knowledge-graph) with 0.7x decay per hop. |

### Contradiction Detection

| Method | Description |
|:-------|:------------|
| `detect_contradictions(topic, threshold=0.65)` | Find contradicting facts via negation flip, antonym swap, and confidence conflict analysis. |

### Crystallization

| Method | Description |
|:-------|:------------|
| `crystallize(topic, min_cluster=5)` | Auto-summarize fact clusters into higher-level insight nodes stored in the [knowledge graph](#knowledge-graph). |

### Temporal Reasoning

Full implementation of [Allen's Interval Algebra](https://en.wikipedia.org/wiki/Allen%27s_interval_algebra) — 13 temporal relations: before, after, meets, met-by, overlaps, overlapped-by, during, contains, starts, started-by, finishes, finished-by, equals.

| Method | Description |
|:-------|:------------|
| `temporal_add(event_id, start, end, data)` | Register a temporal event ([ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) timestamps). |
| `temporal_relation(a_id, b_id)` | Returns one of 13 [Allen's relations](https://en.wikipedia.org/wiki/Allen%27s_interval_algebra). |
| `temporal_chain(event_ids)` | Chronologically ordered event chain. |
| `temporal_timeline(start, end, max_results=15)` | Events within a time range. |

### Legal Citations

| Method | Description |
|:-------|:------------|
| `cite(code, title, text, category, severity, jurisdiction)` | Store a legal citation. Deduplicates by code. |
| `recall_citations(query, category, severity)` | Search citations with stackable filters. |
| `citation_stats()` | Counts by category, severity, jurisdiction. |
| `link_crime_to_citations(topic, text)` | Auto-find relevant [ARS codes](https://www.azleg.gov/arstitle/) for a crime fact. |

### Court Documents

| Method | Description |
|:-------|:------------|
| `generate_court_document(doc_type, case_number, defendant, sections, ...)` | Generate formatted [Superior Court of Arizona](https://www.superiorcourt.maricopa.gov/) document with citation appendix. |

### Diamond Link (Encrypted Sync)

Encrypted brain-to-brain knowledge sync over [TLS 1.2+](https://docs.python.org/3/library/ssl.html) with [HMAC-SHA256](https://docs.python.org/3/library/hmac.html) message integrity and [SHA-256](https://docs.python.org/3/library/hashlib.html) certificate fingerprint pinning. See [Security Architecture](#security-architecture-diamond-link) for full details.

| Method | Description |
|:-------|:------------|
| `link_init(display_name)` | Generate TLS identity (cert + key via [OpenSSL](https://www.openssl.org/)). Idempotent. |
| `link_identity()` | This brain's fingerprint + display name. |
| `link_pair_start(port=7777, timeout=300)` | Listen for peer pairing. Returns 64-char hex token. |
| `link_pair_connect(host, port, token)` | Connect to peer and complete pairing. |
| `link_peers()` | List all authorized peers with sync stats. |
| `link_unpair(peer_fingerprint)` | Revoke peer authorization. |
| `link_serve(port=7777)` | Start TLS sync server. |
| `link_sync(peer_fp, topics, direction, dry_run)` | Sync knowledge with authorized peer. |
| `link_set_shared_topics(peer_fp, topics)` | Configure per-peer topic sharing. |
| `link_status()` | Combined identity + peers + recent syncs. |
| `link_log(last_n=15)` | Sync history. |
| `link_custody_log(last_n=15)` | [Chain of custody](https://en.wikipedia.org/wiki/Chain_of_custody) audit trail. |
| `link_verify_custody_chain()` | Verify [SHA-256 hash-chain](https://en.wikipedia.org/wiki/Hash_chain) integrity. |

### Peer Reputation

| Method | Description |
|:-------|:------------|
| `link_peer_reputation(peer_fingerprint)` | Reputation score based on sync history + trust. |
| `link_adjust_trust(peer_fingerprint, adjustment)` | Manually adjust trust score for a peer. |

### Selective Amnesia

| Method | Description |
|:-------|:------------|
| `forget(topic, fact_pattern, reason)` | Controlled forgetting with audit trail. |
| `amnesia_log(last_n=15)` | View forget/restore history. |
| `amnesia_restore(topic, fact_pattern)` | Restore previously forgotten facts. |

### Multi-Brain Consensus

| Method | Description |
|:-------|:------------|
| `consensus_check(topic, fact_text)` | Check how many peers agree — strong / majority / partial / contested / standalone. |

### Live Subscriptions

| Method | Description |
|:-------|:------------|
| `link_subscribe(peer_fp, topics)` | Subscribe to topic updates from a peer. |
| `link_unsubscribe(peer_fp, topics)` | Unsubscribe from topic updates. |
| `link_poll_subscriptions()` | Check for and apply subscription updates. |

### Evidence Blob Store

[Content-addressable](https://en.wikipedia.org/wiki/Content-addressable_storage) binary evidence storage using [SHA-256](https://en.wikipedia.org/wiki/SHA-2) hashes.

| Method | Description |
|:-------|:------------|
| `blob_store(content, metadata)` | Store binary evidence. Returns [SHA-256](https://docs.python.org/3/library/hashlib.html) hash. |
| `blob_retrieve(blob_hash)` | Retrieve stored evidence by hash. |
| `blob_list(max_results=15)` | List stored blobs with metadata. |
| `blob_link(blob_hash, fact_topic)` | Link a blob to a fact topic. |
| `blob_verify(blob_hash)` | Verify blob integrity (content matches hash). |

### Visual Reports

| Method | Description |
|:-------|:------------|
| `visual_bar_chart(data, title)` | ANSI colored bar chart. |
| `visual_table(headers, rows, title)` | [Box-drawing](https://en.wikipedia.org/wiki/Box-drawing_character) table with severity coloring. |
| `visual_connection_graph(center, connections)` | Text-based connection visualization. |
| `visual_report(topic=None)` | Comprehensive visual report (topic or full brain). |
| `export_html(output_path)` | Standalone HTML with search, charts, court doc generator. |

### Command Memory

| Method | Description |
|:-------|:------------|
| `log_command(raw_command, cwd)` | Parse and store a shell command via [`shlex`](https://docs.python.org/3/library/shlex.html). |
| `suggest_flags(command, subcommand, top_n=15)` | Frequency + recency ranked flag suggestions. |
| `smart_suggest(command, subcommand, cwd)` | LLM-powered suggestions via [LM Studio](https://lmstudio.ai). |
| `command_stats(command=None)` | Usage statistics. |

### Agents

| Method | Description |
|:-------|:------------|
| `agent_checkin(agent_id, role, task)` | Register or update a sentinel agent. |
| `agent_report(agent_id, findings)` | Submit findings. HIGH+ auto-learned. |
| `escalation_needed(finding)` | Check if finding needs human review. |
| `digest()` | Full brain status overview. |

---

## Storage

All data lives in `brain/memory/` as human-readable JSON:

```
brain/memory/
  facts.json          # Knowledge facts
  citations.json      # Legal citations (ARS, rules, constitutional)
  agents.json         # Sentinel agent registry
  commands.json       # Shell command history
  escalations.json    # Unresolved escalations
  graph.json          # Knowledge graph (nodes + edges)
  temporal.json       # Temporal events
  amnesia.json        # Forget/restore audit trail
  link/               # Diamond Link identity + peers + sync logs
    key.pem           # RSA 2048 private key (never shared)
    cert.pem          # Self-signed X.509 certificate
    identity.json     # Fingerprint + display name
    peers.json        # Authorized peers + sync stats
    sync_log.json     # Sync history
    custody.json      # Hash-chained custody records
  blobs/              # Content-addressable evidence store
    <sha256_hash>     # Binary evidence files
    manifest.json     # Blob metadata index
```

Writes are atomic (`.tmp` + [`os.replace()`](https://docs.python.org/3/library/os.html#os.replace)) — safe even on crash.

---

## Security Architecture (Diamond Link)

| Layer | Mechanism |
|:------|:----------|
| **Transport** | [TLS 1.2+](https://docs.python.org/3/library/ssl.html) via Python `ssl`, [ECDHE+AESGCM](https://en.wikipedia.org/wiki/Authenticated_encryption) ciphers only |
| **Identity** | Self-signed [X.509](https://en.wikipedia.org/wiki/X.509) cert, fingerprint = [SHA-256](https://en.wikipedia.org/wiki/SHA-2) of DER-encoded cert |
| **Authentication** | [Certificate pinning](https://en.wikipedia.org/wiki/Transport_Layer_Security#Certificate_pinning) after out-of-band pairing |
| **Pairing** | 64-char hex token ([`secrets.token_hex`](https://docs.python.org/3/library/secrets.html#secrets.token_hex)), 5-minute expiry |
| **Message integrity** | [HMAC-SHA256](https://docs.python.org/3/library/hmac.html) on every message |
| **Wire format** | `<4-byte length><JSON body><32-byte HMAC tag>` over TLS |
| **Replay protection** | [Nonce](https://en.wikipedia.org/wiki/Cryptographic_nonce) in every message |
| **Chain of custody** | [SHA-256 hash chain](https://en.wikipedia.org/wiki/Hash_chain) — immutable records |
| **Private key** | `0o600` permissions, never transmitted |
| **No plaintext fallback** | TLS is mandatory, no `--insecure` option |

---

## CI/CD Pipeline

The [GitHub Actions](https://docs.github.com/en/actions) pipeline ([`.github/workflows/diamond-ci.yml`](.github/workflows/diamond-ci.yml)) runs 5 tiers:

| Tier | Job | Description |
|:-----|:----|:------------|
| 0 | Gates | Syntax + import + digest smoke test |
| 1 | Test Matrix | 112 tests across [Python 3.10-3.13](https://www.python.org/downloads/) x Ubuntu/macOS/Windows |
| 2 | Integration | Seed data + graph + FSRS + crystallize + temporal + blob + link |
| 3 | CLI Smoke | Every CLI command exercised |
| 4 | Security | No `eval`/`exec`, no secrets, stdlib-only imports ([AST](https://docs.python.org/3/library/ast.html) verified), atomic writes verified |

All 5 tiers must pass for `Diamond Complete`.

---

## Pre-Seeded Knowledge

### Digital Forensics (119 facts)

```bash
python seed_forensics.py
```

Covers: [Autopsy](https://www.autopsy.com/), [Volatility 3](https://github.com/volatilityfoundation/volatility3), [Wireshark](https://www.wireshark.org/), [Zeek](https://zeek.org/), [YARA](https://virustotal.github.io/yara/), [Ghidra](https://ghidra-sre.org/), [Plaso](https://github.com/log2timeline/plaso), [Chainsaw](https://github.com/WithSecureLabs/chainsaw), [Hayabusa](https://github.com/Yamato-Security/hayabusa). Windows/Linux/macOS artifacts. [NIST SP 800-86](https://csrc.nist.gov/pubs/sp/800/86/final), [SANS DFIR](https://www.sans.org/digital-forensics-incident-response/), [MITRE ATT&CK](https://attack.mitre.org/), [RFC 3227](https://datatracker.ietf.org/doc/html/rfc3227) methodologies.

### Arizona Criminal Law (56 citations)

```bash
python seed_ars_criminal.py
```

Covers: Homicide ([ARS 13-1102](https://www.azleg.gov/ars/13/01102.htm)-[1105](https://www.azleg.gov/ars/13/01105.htm)), Assault, Self-Defense/Justification ([Castle Doctrine](https://www.azleg.gov/ars/13/00411.htm)), Drug Offenses, DUI ([ARS 28-1381](https://www.azleg.gov/ars/28/01381.htm)), Weapons, Domestic Violence, Criminal Procedure (arrest, [Miranda](https://www.azleg.gov/ars/13/03884.htm), search/seizure, warrants), [AZ Constitutional Rights](https://www.azleg.gov/constitution/), Sentencing Ranges, [Rules of Evidence](https://govt.westlaw.com/azrules/Browse/Home/Arizona/ArizonaRulesofEvidence) (401-803), Rules of Criminal Procedure.

---

## LM Studio Integration

Diamond Brain optionally connects to [LM Studio](https://lmstudio.ai) for 10 AI-powered enhancements:

1. Smart flag suggestions
2. Semantic search (embeddings)
3. Auto-categorization
4. Fact summarization & dedup
5. Knowledge gap detection
6. Smarter auto-linking
7. Query expansion
8. Contradiction detection
9. Natural language digests
10. Command prediction

**Model stack:** [`sentinel-fast`](https://huggingface.co/mistralai/Ministral-8B-Instruct-2410) (Ministral-3-3B, 3GB) + [`reasoner`](https://huggingface.co/deepseek-ai/DeepSeek-R1) (DeepSeek-R1-8B, 7GB) + [`embedder`](https://huggingface.co/nomic-ai/nomic-embed-text-v1.5) (nomic-embed-text-v1.5, 0.3GB). All three fit on a 12GB GPU.

See [`LM_STUDIO_GUIDE.md`](LM_STUDIO_GUIDE.md) for full setup instructions.

---

## Integration

### Drop into any project

```bash
cp -r brain/ /path/to/your/project/brain/
# or
bash setup_template.sh /path/to/your/project
```

Then: `from brain.diamond_brain import DiamondBrain`

### Custom memory directory

```python
brain = DiamondBrain(memory_dir="/path/to/your/memory")
```

---

## Architecture

```
                         ┌──────────────────────────────┐
                         │       Diamond Brain v2.0     │
                         │    73 Methods / 0 Dependencies│
                         └──────────────┬───────────────┘
          ┌──────────┬──────────┬───────┴───────┬──────────┬──────────┐
          │          │          │               │          │          │
     ┌────┴────┐ ┌───┴───┐ ┌───┴────┐   ┌─────┴─────┐ ┌──┴───┐ ┌───┴────┐
     │  Facts  │ │ Graph │ │  FSRS  │   │ Temporal  │ │ Cite │ │ Agents │
     │  Store  │ │ Index │ │ Review │   │ Reasoner  │ │ Store│ │ Store  │
     └────┬────┘ └───┬───┘ └───┬────┘   └─────┬─────┘ └──┬───┘ └───┬────┘
          │          │         │               │          │          │
          └──────────┴────┬────┴───────────────┴──────────┘          │
                          │                                          │
          ┌───────────────┼───────────────┐                          │
          │               │               │                          │
     ┌────┴────┐   ┌──────┴──────┐  ┌─────┴─────┐           ┌──────┴──────┐
     │ Terminal │   │    HTML     │  │   Court    │           │  Diamond    │
     │ Visuals  │   │   Report   │  │   Docs     │           │    Link     │
     └──────────┘   └────────────┘  └───────────┘           └──────┬──────┘
                                                                    │
                                                    ┌───────┬───────┼───────┐
                                                    │       │       │       │
                                               ┌────┴──┐ ┌──┴──┐ ┌─┴──┐ ┌──┴──┐
                                               │ Sync  │ │Pair │ │Blob│ │Chain│
                                               │Engine │ │ TLS │ │ DB │ │ of  │
                                               └───────┘ └─────┘ └────┘ │Cust.│
                                                                         └─────┘
```

---

## Requirements

- [**Python 3.10+**](https://www.python.org/downloads/) (uses `str | None` union syntax)
- **No external packages** — stdlib only ([`json`](https://docs.python.org/3/library/json.html), [`pathlib`](https://docs.python.org/3/library/pathlib.html), [`difflib`](https://docs.python.org/3/library/difflib.html), [`math`](https://docs.python.org/3/library/math.html), [`hashlib`](https://docs.python.org/3/library/hashlib.html), [`ssl`](https://docs.python.org/3/library/ssl.html), [`hmac`](https://docs.python.org/3/library/hmac.html), [`secrets`](https://docs.python.org/3/library/secrets.html), [`socket`](https://docs.python.org/3/library/socket.html), [`subprocess`](https://docs.python.org/3/library/subprocess.html), [`shutil`](https://docs.python.org/3/library/shutil.html), [`threading`](https://docs.python.org/3/library/threading.html))
- [**OpenSSL**](https://www.openssl.org/) CLI (for Diamond Link cert generation — pre-installed on Linux/macOS, via [Git for Windows](https://gitforwindows.org/) on Windows)
- [**LM Studio**](https://lmstudio.ai) (optional) — for AI-powered features

---

## License

[MIT](LICENSE)

---

<p align="center">
  <strong>Built by Ryan Cashmoney (<a href="https://github.com/Tunclon">@Tunclon</a>)</strong><br/>
  <em>Diamond Brain — Because knowledge should persist.</em>
</p>
