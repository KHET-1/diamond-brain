# CLAUDE.md — Diamond Brain v2.0

> For Claude Code / Claude Dev / any AI instance working on this project.
> These directives are MANDATORY. Follow them exactly.

## What This Is

Diamond Brain is a **standalone knowledge cache + legal intelligence system + encrypted brain-to-brain linking** that any project can plug into. It persists facts, agent state, legal citations (ARS codes, case law, rules of evidence), generates court-ready documents, manages knowledge graphs, spaced repetition, temporal reasoning, and produces rich visual reports — all as JSON on disk with zero external dependencies.

- **Language:** Python 3.10+ (stdlib only — no pip install needed)
- **Storage:** JSON files in `brain/memory/`
- **Tests:** 112 tests across 21 tiers (`.github/workflows/diamond-ci.yml`)
- **Public methods:** 73 (all in `brain/diamond_brain.py`)
- **Owner:** Ryan Cashmoney (@Tunclon)

## Project Structure

```
diamond-brain/
  brain/
    __init__.py             <- Exports DiamondBrain
    diamond_brain.py        <- Core brain module (ALL logic lives here — ~5600 lines)
    memory/                 <- Auto-created JSON storage (gitignored)
      facts.json            <- Knowledge facts with confidence + time decay
      citations.json        <- Legal citations (ARS, case law, rules)
      agents.json           <- Sentinel agent registry
      commands.json         <- Shell command history + flag tracking
      escalations.json      <- Unresolved escalations
      graph.json            <- Knowledge graph (nodes + typed edges)
      temporal.json         <- Temporal events (Allen's Interval Algebra)
      amnesia.json          <- Forget/restore audit trail
      link/                 <- Diamond Link identity + peers + sync
        key.pem             <- RSA 2048 private key (never shared)
        cert.pem            <- Self-signed X.509 certificate
        identity.json       <- Fingerprint + display name
        peers.json          <- Authorized peers + sync stats + trust
        sync_log.json       <- Sync history
        custody.json        <- Hash-chained custody records (immutable)
      blobs/                <- Content-addressable evidence store
        manifest.json       <- Blob metadata index
        <sha256_hash>       <- Binary evidence files
  tests/
    __init__.py
    test_diamond_brain.py   <- 112 tests across 21 tiers
  .github/
    workflows/
      diamond-ci.yml        <- CI/CD: 5-tier pipeline across Py3.10-3.13 x 3 OSes
  sentinel_audit.py         <- Three-tier code audit pipeline
  seed_forensics.py         <- Seeds 119 digital forensics facts
  seed_ars_criminal.py      <- Seeds 56 Arizona criminal statutes
  LM_STUDIO_GUIDE.md        <- LM Studio setup, model recs, 10 LLM enhancements
  setup_template.sh         <- Helper to copy brain into any project
```

## Quick Start

```python
from brain import DiamondBrain   # or: from brain.diamond_brain import DiamondBrain

brain = DiamondBrain()

# Knowledge
brain.learn("topic", "important fact", confidence=90)
results = brain.recall("topic", max_results=15, fuzzy=True)
brain.search("keyword")
brain.advanced_recall("query")  # association chaining

# Knowledge Graph
brain.graph_auto_index()                  # Build from facts + citations
brain.graph_bfs("forensics", max_depth=3) # BFS traversal
brain.graph_query("disk imaging")         # Fuzzy graph search

# FSRS Spaced Repetition
brain.fsrs_due(threshold=0.9)             # What needs review?
brain.fsrs_review("topic", "fact", 4)     # Rate recall (1-4)

# Temporal Reasoning
brain.temporal_add("event1", "2026-01-01T10:00:00Z", "2026-01-01T11:00:00Z")
brain.temporal_relation("event1", "event2")  # Allen's Interval Algebra

# Legal citations
brain.cite("ARS 13-1105", "First Degree Murder", "A person commits...",
           category="statute", severity="FELONY", jurisdiction="AZ")
brain.recall_citations(query="murder", severity="FELONY")

# Court documents
doc = brain.generate_court_document(
    case_number="CR-2026-001234",
    defendant="John Doe",
    doc_type="MOTION",
    title="Motion to Suppress Evidence",
    sections=[{"heading": "Facts", "body": "...", "citations": ["ARS 13-3887"]}],
)

# Diamond Link — Encrypted Brain-to-Brain Sync
brain.link_init("My Brain")               # TLS identity
brain.link_sync("peer_fp_prefix")         # Sync knowledge

# Evidence Blob Store
brain.blob_store(b"evidence bytes", {"description": "disk hash"})

# Selective Amnesia
brain.forget("topic", "pattern", "reason")
brain.amnesia_restore("topic", "pattern")

# Contradiction Detection + Crystallization
brain.detect_contradictions()
brain.crystallize(min_cluster=5)

# Confidence Propagation
brain.propagate_confidence("node_id", delta=-20)

# Visual reports
print(brain.visual_report())
brain.export_html("report.html")

# Command memory
brain.log_command("git commit -m 'fix' --verbose")
brain.suggest_flags("git", "commit")

# Status
print(brain.digest())
print(brain.heatmap())
```

## CLI Commands

```bash
# Status
python -m brain.diamond_brain                     # Full digest + heatmap

# Knowledge
python -m brain.diamond_brain --recall <topic>
python -m brain.diamond_brain --search <keyword>
python -m brain.diamond_brain --learn <topic> <fact> [confidence] [source]
python -m brain.diamond_brain --prune [max_age_days] [min_confidence]

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

# Contradiction Detection + Crystallization
python -m brain.diamond_brain --contradictions
python -m brain.diamond_brain --crystallize

# Citations
python -m brain.diamond_brain --cite <code> <title> <text> [--severity X]
python -m brain.diamond_brain --citations [query] [--severity FELONY]
python -m brain.diamond_brain --citation-stats

# Court Documents
python -m brain.diamond_brain --court-doc [--case X] [--defendant X] [--type MOTION]

# Visuals & Reports
python -m brain.diamond_brain --visual [topic]
python -m brain.diamond_brain --html [output_path]

# Diamond Link (Encrypted Sync)
python -m brain.diamond_brain --link-init [name]
python -m brain.diamond_brain --link-identity
python -m brain.diamond_brain --link-pair-start [--port 7777]
python -m brain.diamond_brain --link-pair-connect <host:port> <token>
python -m brain.diamond_brain --link-peers
python -m brain.diamond_brain --link-unpair <fp>
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

# Consensus + Reputation
python -m brain.diamond_brain --consensus <topic> <fact_text>
python -m brain.diamond_brain --peer-reputation <fp>

# Subscriptions
python -m brain.diamond_brain --subscribe <fp> <topic1,topic2>
python -m brain.diamond_brain --unsubscribe <fp> <topic1,topic2>

# Command Memory
python -m brain.diamond_brain --log-command "git push --force"
python -m brain.diamond_brain --suggest "git" [--smart] [--top N]
python -m brain.diamond_brain --command-stats [command]
python -m brain.diamond_brain --shell-hook
```

## Seeding Knowledge

```bash
python seed_forensics.py         # 119 digital forensics facts
python seed_ars_criminal.py      # 56 Arizona criminal statutes
```

## Running Tests

```bash
python -m unittest tests.test_diamond_brain -v   # 112 tests
```

## CI/CD Pipeline

GitHub Actions (`.github/workflows/diamond-ci.yml`) — 5 tiers:

| Tier | Job | What |
|:-----|:----|:-----|
| 0 | Gates | Syntax + import + digest smoke |
| 1 | Test Matrix | 112 tests x Python 3.10-3.13 x Ubuntu/macOS/Windows |
| 2 | Integration | Seed + graph + FSRS + temporal + blob + link + HTML |
| 3 | CLI Smoke | Every CLI command exercised |
| 4 | Security | No eval/exec, stdlib-only imports, atomic writes, no secrets |

## Sentinel Auditor

Three-tier code audit pipeline using Diamond Brain + LM Studio:

```bash
python sentinel_audit.py --tier all --verbose
python sentinel_audit.py --brain-status
```

## LM Studio Integration

See `LM_STUDIO_GUIDE.md` for:
- Model recommendations (sentinel-fast, reasoner, embedder)
- 10 ways LM Studio supercharges the brain
- Binary Truth Engine pattern
- DeepSeek R1 quirks

**Model identifiers:** `sentinel-fast` (Ministral-3-3B), `reasoner` (DeepSeek-R1-8B), `embedder` (nomic-embed-text-v1.5)

## Key Architecture Notes

- **Atomic writes:** `.tmp` + `os.replace()` — never corrupt JSON
- **Fuzzy dedup:** 80% similarity threshold on learn() (difflib.SequenceMatcher)
- **Time decay:** Facts lose confidence over time (60-day half-life unverified, 180-day verified)
- **FSRS forgetting:** Power-law curve R(t,S) = (1 + t/(9*S))^(-1) — more realistic than exponential
- **Knowledge Graph:** Nodes + typed edges, BFS traversal, auto-index from facts/citations
- **Confidence Propagation:** 0.7x decay per hop through graph edges
- **Allen's Interval Algebra:** 13 temporal relations (before, after, meets, overlaps, during, starts, finishes, equals, and inverses)
- **Auto-linking:** Facts auto-discover related topics via fuzzy match + keyword overlap
- **Crime-citation linking:** Single crime keywords AND multi-word overlap both trigger ARS linkage
- **TLS encryption:** ECDHE+AESGCM ciphers via Python ssl module (stdlib)
- **Chain of custody:** SHA-256 hash-chained immutable records (blockchain-style)
- **Content-addressable blobs:** SHA-256 hash as blob filename
- **Display defaults:** 15 results shown, unlimited storage
- **Flag scoring:** 14-day half-life for command flag recency
- **No external deps:** Everything is Python stdlib (json, pathlib, difflib, math, hashlib, ssl, hmac, secrets, socket, subprocess, shutil, threading)

---

## AI AGENT DIRECTIVES — MANDATORY

These rules govern ALL AI agents working on Diamond Brain. Follow every rule.

### Rule 1: No External Dependencies
Everything must be Python stdlib. numpy/sentence-transformers are optional enhancement layers only. If you import something outside stdlib, you broke the project.

### Rule 2: Atomic Writes Always
Write to `.tmp`, then `os.replace()`. Never write directly to production JSON files. This is non-negotiable.

### Rule 3: Fuzzy Dedup on learn()
Check for >80% similar facts before creating duplicates. Use `difflib.SequenceMatcher`.

### Rule 4: Display 15, Store Unlimited
All `max_results` defaults = 15. Storage arrays have no cap (except commands: 50K rolling window).

### Rule 5: Professional Terminology Only
No "zombie", "kill", or other potentially misinterpretable terms in legal contexts. Use "sentinel", "audit", "scan", "prune", "archive".

### Rule 6: Crime Accusations MUST Link to Citations
Any fact mentioning a crime must be linked to relevant ARS codes via `link_crime_to_citations()`. If a user describes a crime scenario, find and cite the relevant statutes.

### Rule 7: Offer Visual Output
When presenting data that benefits from visual representation — charts, tables, graphs, comparisons — offer to show it visually. Use `visual_report()`, `visual_bar_chart()`, `visual_table()`, or `export_html()`.

### Rule 8: Court Documents Must Be Accurate
Never fabricate statutory text. Always reference actual ARS codes from the citations store. Include the disclaimer: "Not legal advice. Verify at azleg.gov."

### Rule 9: Confidence Scoring
Rate your own confidence 1-100%. Research if below 85%. All facts stored in the brain should have honest confidence scores. Never inflate confidence.

### Rule 10: Test After Every Change
Run this after ANY code change:
```bash
python -c "from brain.diamond_brain import DiamondBrain; b = DiamondBrain(); print(b.digest())"
python -m unittest tests.test_diamond_brain  # 112 tests
```
If it errors, you broke something. Fix it before moving on.

---

## AI SWARM PROTOCOL — VERIFICATION & FACT-CHECKING

When multiple AI agents work on Diamond Brain, or when a single agent needs to verify its own work, follow this protocol.

### Phase 1: RECON (Read Everything)
Before writing any code:
1. Read `brain/diamond_brain.py` — understand every method
2. Read `CLAUDE.md` (this file) — understand all rules
3. Read `STARTER_PROMPT.md` — understand the full system context
4. Run `python -m brain.diamond_brain` — see current brain state
5. Run `python -m brain.diamond_brain --citation-stats` — verify citations are loaded

### Phase 2: TRACE (Follow Every Connection)
Before modifying any feature:
1. Trace all callers of the method you're changing (grep for method name)
2. Trace all methods the target method calls
3. Check if CLI commands reference the method
4. Check if `export_html()` references the method (HTML has inline JS)
5. Check if `visual_report()` references the method

### Phase 3: IMPLEMENT (Write Code)
1. Make changes in `brain/diamond_brain.py` only (single source of truth)
2. Follow existing patterns — look at how similar methods are structured
3. Use `_C` class for all ANSI colors (never hardcode escape sequences)
4. Use `_section_header()` for all new section headers
5. Use `_load()` and `_save()` for all JSON operations
6. Add CLI command to `__main__` block if user-facing

### Phase 4: VERIFY (Test Everything)
After every change, run the full verification chain:
```bash
# 1. Syntax check
python -c "import py_compile; py_compile.compile('brain/diamond_brain.py', doraise=True)"

# 2. Import check
python -c "from brain import DiamondBrain; print('OK')"

# 3. Digest check (exercises init + load + all stores)
python -c "from brain.diamond_brain import DiamondBrain; b = DiamondBrain(); d = b.digest(); print(f'Facts: {d[\"total_facts\"]}, Citations: {d[\"total_citations\"]}, Commands: {d[\"commands_logged\"]}')"

# 4. Visual check (exercises formatting + ANSI)
python -m brain.diamond_brain 2>&1 | head -20

# 5. Full test suite
python -m unittest tests.test_diamond_brain -v

# 6. Method-specific tests for whatever you changed
```

### Phase 5: FACT-CHECK (Validate Knowledge)
When adding facts or citations:
1. Verify ARS codes exist at azleg.gov (never invent statute numbers)
2. Verify tool names and version numbers against official sources
3. Cross-reference forensic methodologies against NIST/SANS/MITRE
4. Confidence scores must reflect actual certainty, not optimism
5. Sources must be real and citable

### Phase 6: DOCUMENT
After features are verified:
1. Update `CLAUDE.md` if new rules or methods were added
2. Update `STARTER_PROMPT.md` if the API surface changed
3. Update `README.md` if user-facing features changed
4. Update `LM_STUDIO_GUIDE.md` if LLM integration changed

---

## AI TOOL RAMPAGE CHECKLIST

When asked to "rampage" or "full audit" the project, execute this checklist:

```
[ ] Import check passes
[ ] All 73 public methods callable without crash
[ ] 112 tests pass (python -m unittest tests.test_diamond_brain)
[ ] digest() returns correct counts
[ ] recall() returns facts sorted by effective confidence
[ ] search() finds facts across all topics
[ ] advanced_recall() follows topic links
[ ] cite() deduplicates by code
[ ] recall_citations() filters by query/category/severity
[ ] citation_stats() counts match actual data
[ ] link_crime_to_citations() finds relevant statutes
[ ] generate_court_document() produces valid formatting
[ ] log_command() parses flags correctly
[ ] suggest_flags() scores by frequency + recency
[ ] command_stats() reports accurate counts
[ ] visual_report() renders without errors
[ ] visual_bar_chart() handles empty data
[ ] visual_table() handles empty rows
[ ] visual_connection_graph() accepts both tuples and strings
[ ] export_html() produces valid standalone HTML
[ ] heatmap() shows freshness scores
[ ] prune_stale() removes old facts correctly
[ ] agent_checkin() registers agents
[ ] agent_report() auto-learns HIGH+ findings
[ ] graph_auto_index() builds graph from facts + citations
[ ] graph_bfs() traverses correctly
[ ] graph_query() finds nodes by keyword
[ ] fsrs_retrievability() computes power-law forgetting
[ ] fsrs_review() updates stability + difficulty
[ ] fsrs_due() finds facts below threshold
[ ] propagate_confidence() cascades through edges
[ ] detect_contradictions() finds negation/antonym/confidence conflicts
[ ] crystallize() groups facts into insight clusters
[ ] temporal_add()/temporal_relation()/temporal_chain() work with Allen's Algebra
[ ] forget()/amnesia_restore() work with audit trail
[ ] consensus_check() returns correct agreement levels
[ ] blob_store()/blob_retrieve()/blob_verify() maintain integrity
[ ] link_init() generates TLS identity
[ ] link_verify_custody_chain() validates hash chain
[ ] All CLI commands work
[ ] No "zombie" references in code (only in historical notes)
[ ] .gitignore covers all generated files
[ ] All JSON files use atomic writes
```

---

## QUALITY GATES

No change ships unless:
1. `python -c "from brain import DiamondBrain"` succeeds
2. `python -m unittest tests.test_diamond_brain` — all 112 tests pass
3. All existing CLI commands still work
4. No new external dependencies introduced
5. JSON stores remain backward-compatible
6. ANSI output renders correctly (test in terminal)

---

## IMPLEMENTED FEATURES (formerly Roadmap)

All features from the original roadmap have been implemented:

| Feature | Status | Methods |
|:--------|:-------|:--------|
| Knowledge Graph | Done | `graph_add_node`, `graph_add_edge`, `graph_bfs`, `graph_query`, `graph_auto_index`, `graph_stats` |
| FSRS Spaced Repetition | Done | `fsrs_retrievability`, `fsrs_review`, `fsrs_due`, `fsrs_stats` |
| Confidence Propagation | Done | `propagate_confidence` |
| Temporal Reasoning | Done | `temporal_add`, `temporal_relation`, `temporal_chain`, `temporal_timeline` |
| Crystallization | Done | `crystallize` |
| Contradiction Detection | Done | `detect_contradictions` |
| Evidence Blob Store | Done | `blob_store`, `blob_retrieve`, `blob_list`, `blob_link`, `blob_verify` |
| Diamond Link (Encrypted Sync) | Done | `link_init`, `link_pair_start`, `link_pair_connect`, `link_sync`, `link_serve` + 8 more |
| Selective Amnesia | Done | `forget`, `amnesia_log`, `amnesia_restore` |
| Multi-Brain Consensus | Done | `consensus_check` |
| Peer Reputation | Done | `link_peer_reputation`, `link_adjust_trust` |
| Live Subscriptions | Done | `link_subscribe`, `link_unsubscribe`, `link_poll_subscriptions` |
| Chain of Custody | Done | `link_custody_log`, `link_verify_custody_chain` |

### Future Possibilities

| Priority | Feature | Description |
|:---------|:--------|:------------|
| P1 | Fractal Hierarchy | Holons: fact -> cluster -> domain -> worldview. Same interface at every scale. |
| P1 | Self-Organizing Clusters | Hebbian "fire together wire together" + label propagation. |
| P2 | Embedding Search | Vector similarity via numpy + sentence-transformers or LM Studio embeddings. |
| P2 | Multi-Brain Orchestrator | Automated multi-brain workflows with task distribution. |

---

## TERMINAL RECOMMENDATIONS

For best visual experience with Diamond Brain:
- **Best terminal:** WezTerm, Kitty, or Windows Terminal (full Unicode + 256-color + box drawing support)
- **Font:** JetBrains Mono, FiraCode, or Cascadia Code (ligatures + powerline glyphs)
- **CLI enhancers:** bat (better cat), fd (better find), fzf (fuzzy finder for piping brain output)
- **Shell:** zsh with starship prompt (shows git status + directory context)
