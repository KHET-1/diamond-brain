# Diamond Brain v2.0 — Starter Prompt for AI Sessions

> Copy this entire prompt into any AI session (Claude, GPT, local LLM) to give it
> full context on Diamond Brain. This is the "load brain" prompt.

---

## SYSTEM CONTEXT

You are working with **Diamond Brain v2.0**, a standalone Python knowledge cache and legal intelligence system with encrypted brain-to-brain linking. All code lives in `brain/diamond_brain.py` (73 public methods). Storage is JSON files in `brain/memory/`. Zero external dependencies — Python 3.10+ stdlib only.

**Owner:** Ryan Cashmoney (@Tunclon)

---

## WHAT DIAMOND BRAIN DOES

Diamond Brain is a persistent intelligence layer that:

1. **Stores knowledge facts** with confidence scores, time decay, fuzzy deduplication, and auto-linking between related topics
2. **Knowledge graph** — nodes + typed edges, BFS traversal, auto-indexing from facts/citations
3. **FSRS spaced repetition** — real memory science with stability, difficulty, retrievability (power-law forgetting curve)
4. **Confidence propagation** — belief networks where connected facts propagate confidence changes through graph edges
5. **Contradiction detection** — negation flip, antonym swap, and confidence conflict analysis
6. **Crystallization** — auto-summarize fact clusters into higher-level insight nodes
7. **Temporal reasoning** — Allen's Interval Algebra (13 relations), causal chains, timelines
8. **Manages legal citations** — Arizona Revised Statutes (ARS), Rules of Evidence, Rules of Criminal Procedure, Constitutional provisions
9. **Generates court-ready documents** with proper legal formatting (Superior Court of Arizona headers, case captions, citation appendices)
10. **Diamond Link** — encrypted brain-to-brain sync over TLS 1.2+ with certificate pinning, HMAC-SHA256 message integrity, and chain of custody
11. **Evidence blob store** — content-addressable SHA-256 storage for binary evidence
12. **Selective amnesia** — controlled forgetting with audit trail and restore capability
13. **Multi-brain consensus** — cross-brain fact verification (strong/majority/partial/contested)
14. **Peer reputation scoring** — trust scores based on sync history and manual adjustment
15. **Live subscriptions** — subscribe to topic updates from peers
16. **Produces visual reports** — ANSI terminal charts/tables/graphs AND interactive HTML reports
17. **Tracks shell commands** — logs command history, suggests flags by frequency+recency
18. **Coordinates AI agents** — agent check-in, findings reporting, auto-learning of high-severity findings

---

## DATA STORES (all in brain/memory/)

| File | Contents | Format |
|------|----------|--------|
| `facts.json` | Knowledge facts with topic, confidence, time decay, links | Array of dicts |
| `citations.json` | Legal citations — ARS codes, case law, evidence rules | Array of dicts |
| `agents.json` | Registered sentinel agents and their findings counts | Array of dicts |
| `commands.json` | Shell command history with parsed flags | Array of dicts |
| `escalations.json` | Unresolved findings needing human review | Array of dicts |
| `graph.json` | Knowledge graph — nodes + typed edges | Dict with nodes/edges |
| `temporal.json` | Temporal events with start/end timestamps | Array of dicts |
| `amnesia.json` | Forget/restore audit trail | Array of dicts |
| `link/identity.json` | This brain's fingerprint + display name | Dict |
| `link/peers.json` | Authorized peers + sync stats + trust scores | Array of dicts |
| `link/sync_log.json` | Sync history | Array of dicts |
| `link/custody.json` | Hash-chained custody records (immutable) | Array of dicts |
| `link/key.pem` | RSA 2048 private key (never shared) | PEM |
| `link/cert.pem` | Self-signed X.509 certificate | PEM |
| `blobs/manifest.json` | Blob metadata index | Array of dicts |
| `blobs/<sha256>` | Content-addressable binary evidence | Raw bytes |

**Currently seeded:**
- 121 facts (119 forensics + 2 system)
- 56 ARS criminal citations (Title 13, Title 28, AZ Constitution, Rules of Evidence, Rules of Criminal Procedure)

---

## CORE API

```python
from brain import DiamondBrain   # or: from brain.diamond_brain import DiamondBrain
brain = DiamondBrain()

# --- Knowledge ---
brain.learn(topic, fact, confidence=90, source="auto", verified=False)
brain.recall(topic, max_results=15, min_confidence=0, fuzzy=False)
brain.search(keyword)                    # keyword search across all facts
brain.advanced_recall(query)             # association chaining across topics
brain.heatmap()                          # freshness scores per topic
brain.prune_stale(max_age_days=90)       # remove old low-confidence facts

# --- Knowledge Graph ---
brain.graph_add_node(node_id, node_type, data=None)
brain.graph_add_edge(source, target, edge_type, weight=1.0)
brain.graph_remove_edge(source, target, edge_type=None)
brain.graph_bfs(start, max_depth=3, edge_types=None)
brain.graph_neighbors(node_id, edge_type=None)
brain.graph_query(query, max_depth=2)
brain.graph_auto_index()                 # build graph from facts + citations
brain.graph_stats()

# --- FSRS Spaced Repetition ---
brain.fsrs_retrievability(fact)          # current retrievability (0-1)
brain.fsrs_review(topic, fact_text, rating)  # 1=forgot, 2=hard, 3=good, 4=easy
brain.fsrs_due(threshold=0.9, max_results=15)
brain.fsrs_stats()

# --- Confidence Propagation ---
brain.propagate_confidence(node_id, delta, decay_per_hop=0.7, max_depth=3)

# --- Contradiction Detection ---
brain.detect_contradictions(topic=None, threshold=0.65)

# --- Crystallization ---
brain.crystallize(topic=None, min_cluster=5)

# --- Temporal Reasoning ---
brain.temporal_add(event_id, start, end=None, data=None)
brain.temporal_relation(a_id, b_id)      # Allen's Interval Algebra (13 relations)
brain.temporal_chain(event_ids=None)     # chronological ordering
brain.temporal_timeline(start=None, end=None, max_results=15)

# --- Legal Citations ---
brain.cite(code, title, text, category="statute", jurisdiction="AZ",
           severity="REFERENCE", linked_facts=[])
brain.recall_citations(query=None, category=None, severity=None, max_results=15)
brain.citation_stats()
brain.link_crime_to_citations(topic, text)

# --- Court Documents ---
brain.generate_court_document(
    doc_type="MOTION",
    case_number="CR-2026-______",
    court_name="SUPERIOR COURT OF ARIZONA",
    county="MARICOPA COUNTY",
    plaintiff="STATE OF ARIZONA",
    defendant="[DEFENDANT NAME]",
    title="MOTION",
    sections=[{"heading": "...", "body": "...", "citations": ["ARS 13-..."]}],
    include_citations=True,
    attorney_name="[ATTORNEY NAME]",
    bar_number="[BAR NUMBER]",
)

# --- Diamond Link (Encrypted Brain-to-Brain Sync) ---
brain.link_init(display_name="Diamond Brain")
brain.link_identity()
brain.link_pair_start(port=7777, timeout=300)
brain.link_pair_connect(host, port, token)
brain.link_peers()
brain.link_unpair(peer_fingerprint)
brain.link_serve(port=7777, max_connections=10)
brain.link_sync(peer_fingerprint, topics=None, direction="both", dry_run=False)
brain.link_set_shared_topics(peer_fingerprint, topics)
brain.link_status()
brain.link_log(last_n=15)
brain.link_custody_log(last_n=15)
brain.link_verify_custody_chain()

# --- Peer Reputation ---
brain.link_peer_reputation(peer_fingerprint)
brain.link_adjust_trust(peer_fingerprint, adjustment)

# --- Selective Amnesia ---
brain.forget(topic, fact_pattern, reason)
brain.amnesia_log(last_n=15)
brain.amnesia_restore(topic, fact_pattern)

# --- Multi-Brain Consensus ---
brain.consensus_check(topic, fact_text)

# --- Live Subscriptions ---
brain.link_subscribe(peer_fingerprint, topics)
brain.link_unsubscribe(peer_fingerprint, topics)
brain.link_poll_subscriptions()

# --- Evidence Blob Store ---
brain.blob_store(content, metadata=None)       # bytes or str
brain.blob_retrieve(blob_hash)
brain.blob_list(max_results=15)
brain.blob_link(blob_hash, fact_topic)
brain.blob_verify(blob_hash)

# --- Visual Reports ---
brain.visual_bar_chart(data_dict, title)
brain.visual_table(headers, rows, title)
brain.visual_connection_graph(center, connections)
brain.visual_report(topic=None)
brain.export_html(output_path)

# --- Command Memory ---
brain.log_command(raw_command, cwd=None)
brain.suggest_flags(command, subcommand=None, top_n=15)
brain.smart_suggest(command, subcommand=None, cwd=None, top_n=5)  # needs LM Studio
brain.command_stats(command=None)

# --- Agents ---
brain.agent_checkin(agent_id, role, task, status="active")
brain.agent_report(agent_id, findings_list)
brain.escalation_needed(finding)

# --- Status ---
brain.digest()                           # full brain overview dict
```

---

## CLI COMMANDS

```bash
# Status
python -m brain.diamond_brain                           # Digest + heatmap

# Knowledge
python -m brain.diamond_brain --recall <topic>
python -m brain.diamond_brain --search <keyword>
python -m brain.diamond_brain --learn <topic> <fact> [confidence] [source]
python -m brain.diamond_brain --prune [max_age] [min_conf]

# Knowledge Graph
python -m brain.diamond_brain --graph-index
python -m brain.diamond_brain --graph-stats
python -m brain.diamond_brain --graph-query <query> [--depth N]
python -m brain.diamond_brain --graph-bfs <start> [--depth N]

# FSRS Spaced Repetition
python -m brain.diamond_brain --fsrs-stats
python -m brain.diamond_brain --fsrs-due
python -m brain.diamond_brain --fsrs-review <topic> <fact_prefix> <rating>

# Temporal Reasoning
python -m brain.diamond_brain --temporal-add <id> <start> [end]
python -m brain.diamond_brain --temporal-relation <id_a> <id_b>
python -m brain.diamond_brain --temporal-chain

# Contradiction Detection
python -m brain.diamond_brain --contradictions

# Crystallization
python -m brain.diamond_brain --crystallize

# Legal Citations
python -m brain.diamond_brain --cite <code> <title> <text> [--severity X]
python -m brain.diamond_brain --citations [query] [--severity FELONY]
python -m brain.diamond_brain --citation-stats

# Court Documents
python -m brain.diamond_brain --court-doc [--case X] [--defendant X] [--type MOTION]

# Visual Reports
python -m brain.diamond_brain --visual [topic]
python -m brain.diamond_brain --html [output_path]

# Diamond Link
python -m brain.diamond_brain --link-init [name]
python -m brain.diamond_brain --link-identity
python -m brain.diamond_brain --link-pair-start [--port 7777]
python -m brain.diamond_brain --link-pair-connect <host:port> <token>
python -m brain.diamond_brain --link-peers
python -m brain.diamond_brain --link-unpair <fingerprint>
python -m brain.diamond_brain --link-serve [--port 7777]
python -m brain.diamond_brain --link-sync <fp> [--topics t1,t2] [--direction both|push|pull] [--dry-run]
python -m brain.diamond_brain --link-set-topics <fp> <topic1,topic2>
python -m brain.diamond_brain --link-status
python -m brain.diamond_brain --link-log [--last N]
python -m brain.diamond_brain --link-custody [--verify]

# Evidence Blob Store
python -m brain.diamond_brain --blob-store <file> [--description X]
python -m brain.diamond_brain --blob-list
python -m brain.diamond_brain --blob-verify <hash>
python -m brain.diamond_brain --blob-link <hash> <topic>

# Selective Amnesia
python -m brain.diamond_brain --forget <topic> <pattern> <reason>
python -m brain.diamond_brain --amnesia-log
python -m brain.diamond_brain --amnesia-restore <topic> <pattern>

# Consensus
python -m brain.diamond_brain --consensus <topic> <fact_text>

# Peer Reputation
python -m brain.diamond_brain --peer-reputation <fp>

# Subscriptions
python -m brain.diamond_brain --subscribe <fp> <topic1,topic2>
python -m brain.diamond_brain --unsubscribe <fp> <topic1,topic2>

# Command Memory
python -m brain.diamond_brain --log-command "command here" [--cwd /path]
python -m brain.diamond_brain --suggest "command" [--smart] [--top N]
python -m brain.diamond_brain --command-stats [command]
python -m brain.diamond_brain --shell-hook
```

---

## KEY DESIGN DECISIONS

| Decision | Value | Why |
|----------|-------|-----|
| Fuzzy dedup threshold | 80% | Prevents near-duplicate facts |
| Time decay (unverified) | 60-day half-life | Old unverified facts lose relevance |
| Time decay (verified) | 180-day half-life | Verified knowledge persists longer |
| Confidence floor | 30 | Facts never fully disappear |
| Display limit | 15 results | Show enough context without overwhelming |
| Storage cap | Unlimited (50K commands) | Hold everything; only commands have a rolling cap |
| Flag recency | 14-day half-life | Commands are more volatile than facts |
| Atomic writes | .tmp + os.replace() | Never corrupt JSON even on crash |
| No external deps | stdlib only | Drop into any Python project instantly |
| Auto-linking | Fuzzy topic match + keyword overlap | Related facts discoverable without manual tagging |
| Crime auto-linking | Keyword + title + code refs | Crime terms auto-connect to ARS codes via 3 strategies |
| FSRS forgetting curve | R(t,S) = (1 + t/(9*S))^(-1) | Power-law — more realistic than exponential decay |
| Confidence propagation | 0.7x decay per hop | Graph-based belief networks |
| TLS encryption | ECDHE+AESGCM via ssl module | Strong transport security, stdlib only |
| Chain of custody | SHA-256 hash-chained records | Immutable, blockchain-style audit trail |
| Blob addressing | SHA-256 content hash | Content-addressable, dedup by default |
| Allen's Interval Algebra | 13 temporal relations | Complete temporal reasoning framework |

---

## SECURITY (DIAMOND LINK)

| Layer | Mechanism |
|:------|:----------|
| Transport | TLS 1.2+ (ECDHE+AESGCM ciphers only) |
| Identity | Self-signed X.509 cert, SHA-256 fingerprint |
| Authentication | Certificate fingerprint pinning after pairing |
| Pairing | 64-char hex token, 5-minute expiry |
| Message integrity | HMAC-SHA256 on every message |
| Wire format | `<4B length><JSON><32B HMAC>` over TLS |
| Replay protection | Nonce in every message |
| Chain of custody | SHA-256 hash chain, immutable records |
| Private key | `0o600` permissions, never transmitted |
| Plaintext | Not supported — TLS mandatory |

---

## ARIZONA CRIMINAL LAW CITATIONS (SEEDED)

56 citations covering:
- **Homicide:** ARS 13-1102 through 13-1105 (negligent homicide to first degree murder)
- **Assault:** ARS 13-1203, 13-1204
- **Self-defense / Justification:** ARS 13-404 through 13-411 (including Castle Doctrine)
- **Drugs:** ARS 13-3401 through 13-3408
- **DUI:** ARS 28-1381 through 28-1383
- **Weapons:** ARS 13-3101, 13-3102
- **Domestic Violence:** ARS 13-3601, 13-3602
- **Property:** ARS 13-1802 (theft), 13-1805 (shoplifting)
- **Criminal Procedure:** ARS 13-3883 (arrest), 13-3884 (Miranda), 13-3887 (search/seizure), 13-3903 (warrants), 13-3925 (surveillance)
- **Constitutional:** AZ Const Art 2, Secs 4, 8, 10, 15, 24
- **Sentencing:** ARS 13-701 through 13-705
- **Rules of Evidence:** Rules 401-404, 702, 801-803
- **Rules of Criminal Procedure:** Rules 6, 7, 15, 15.1, 17, 20

---

## FORENSICS KNOWLEDGE (SEEDED)

119 facts across 26 categories covering:
- Tools: disk, memory, network, mobile, logs, malware, endpoint
- OS artifacts: Windows (Registry, Event Logs, MFT, Prefetch, Amcache, SRUM), Linux (/var/log, bash_history, wtmp), macOS (FSEvents, Unified Logs, KnowledgeC)
- Methodologies: NIST SP 800-86, RFC 3227, SANS DFIR, MITRE ATT&CK
- Commands: imaging (dd, dcfldd), analysis (strings, file, exiftool), Volatility 3, Plaso/log2timeline, YARA

---

## LM STUDIO INTEGRATION

Diamond Brain optionally connects to LM Studio (localhost:1234) for:
1. Smart flag suggestions (--suggest --smart)
2. Semantic search (embedding endpoint)
3. Auto-categorization of facts
4. Fact summarization & dedup
5. Knowledge gap detection
6. Smarter auto-linking
7. Query expansion
8. Contradiction detection
9. Natural language digests
10. Command prediction

**Model stack:**
- `sentinel-fast` = Ministral-3-3B (fast tasks, ~3 GB VRAM)
- `reasoner` = DeepSeek-R1-8B (deep analysis, ~7 GB VRAM)
- `embedder` = nomic-embed-text-v1.5 (semantic search, ~0.3 GB VRAM)

---

## MANDATORY RULES FOR AI AGENTS

### The 10 Commandments

1. **No external dependencies.** Everything must be Python stdlib. numpy/sentence-transformers are optional enhancement layers only.
2. **Atomic writes always.** Write to .tmp, then os.replace(). Never write directly to production JSON.
3. **Fuzzy dedup on learn().** Check for >80% similar facts before creating duplicates.
4. **All display defaults = 15.** When showing lists, show 15 items by default. Storage is unlimited.
5. **Professional terminology.** No "zombie", "kill", or other potentially misinterpretable terms in legal contexts. Use "sentinel", "audit", "scan".
6. **Crime accusations must link to citations.** Any fact mentioning a crime must be linked to relevant ARS codes.
7. **Offer visuals.** When presenting data that would benefit from visual representation (charts, tables, graphs), offer to show it visually.
8. **Court documents must be accurate.** Never fabricate statutory text. Always reference actual ARS codes from the citations store. Include disclaimer: "Not legal advice. Verify at azleg.gov."
9. **Confidence scoring.** Rate your own confidence 1-100%. Research if below 85%. All facts stored in the brain should have honest confidence scores.
10. **Test after changes.** Run `python -c "from brain import DiamondBrain; b = DiamondBrain(); print(b.digest())"` to verify no import errors.

### Verification Swarm Protocol

When an AI agent needs to verify Diamond Brain's integrity:

**RECON** — Read `diamond_brain.py`, `CLAUDE.md`, `STARTER_PROMPT.md`. Run `python -m brain.diamond_brain` to see brain state.

**TRACE** — For any method you're changing: grep all callers, trace all dependencies, check CLI commands, check HTML export, check visual_report.

**IMPLEMENT** — Make changes in `brain/diamond_brain.py` only. Follow existing patterns. Use `_C` for ANSI colors, `_section_header()` for headers, `_load()`/`_save()` for JSON.

**VERIFY** — After every change:
```bash
python -c "import py_compile; py_compile.compile('brain/diamond_brain.py', doraise=True)"
python -c "from brain import DiamondBrain; b = DiamondBrain(); print(b.digest())"
python -m brain.diamond_brain 2>&1 | head -20
python -m unittest tests.test_diamond_brain -v  # 112 tests
```

**FACT-CHECK** — Verify ARS codes exist at azleg.gov. Cross-reference forensic tools against official sources. Never inflate confidence scores.

**DOCUMENT** — Update CLAUDE.md, STARTER_PROMPT.md, README.md as needed.

### Full Audit Checklist

When asked to "rampage", "full audit", or "verify everything":
- Import check passes
- All 73 public methods callable without crash
- digest() returns correct counts
- recall/search/advanced_recall work correctly
- cite/recall_citations/citation_stats work correctly
- link_crime_to_citations finds relevant statutes
- generate_court_document produces valid formatting
- log_command/suggest_flags/command_stats work correctly
- visual_report/visual_bar_chart/visual_table/visual_connection_graph render without errors
- export_html produces valid standalone HTML
- graph_auto_index builds graph, graph_bfs traverses correctly
- fsrs_review updates stability/difficulty, fsrs_due finds due facts
- propagate_confidence cascades through graph edges
- detect_contradictions finds negation/antonym/confidence conflicts
- crystallize groups facts into insight clusters
- temporal_add/temporal_relation/temporal_chain work with Allen's Algebra
- forget/amnesia_restore work with audit trail
- consensus_check returns correct agreement levels
- blob_store/blob_retrieve/blob_verify maintain integrity
- link_init generates TLS identity, link_verify_custody_chain passes
- All CLI commands work
- No "zombie" references in code
- All JSON files use atomic writes
- 112 tests pass

---

## CI/CD PIPELINE

GitHub Actions (`.github/workflows/diamond-ci.yml`) — 5 tiers:

| Tier | Job | What it tests |
|:-----|:----|:--------------|
| 0 | Gates | Syntax + import + digest smoke |
| 1 | Test Matrix | 112 tests x Python 3.10-3.13 x Ubuntu/macOS/Windows |
| 2 | Integration | Seed + graph + FSRS + temporal + blob + link + HTML |
| 3 | CLI Smoke | Every CLI command exercised |
| 4 | Security | No eval/exec, stdlib-only imports, atomic writes, no secrets |

---

## TERMINAL RECOMMENDATIONS

For best visual experience with Diamond Brain:
- **Best terminal:** WezTerm, Kitty, or Windows Terminal (full Unicode + 256-color + box drawing support)
- **Font:** JetBrains Mono, FiraCode, or Cascadia Code (ligatures + powerline glyphs)
- **CLI enhancers:** bat (better cat), fd (better find), fzf (fuzzy finder for piping brain output)
- **Shell:** zsh with starship prompt (shows git status + directory context)

---

*This prompt covers the complete Diamond Brain v2.0 system. Load it at the start of any AI session to give full project context.*
