# Diamond Brain

Lightweight, standalone knowledge cache for AI-assisted code audit pipelines. Store facts, register zombie agents, track escalations, and visualize knowledge freshness — all with zero external dependencies.

## What It Does

Diamond Brain is a JSON-backed knowledge store designed for multi-agent workflows:

- **Learn & Recall** — Store facts with confidence scores, fuzzy dedup prevents duplicates
- **Agent Registration** — Zombie agents check in, report findings, auto-learn from results
- **Escalation Engine** — Flags findings that need human/expensive-AI review
- **Knowledge Heatmap** — Visualize which topics are fresh vs stale
- **Brain Cache** — Skip re-auditing unchanged files within 24 hours

## Quick Start

### 1. Copy into your project
```bash
cp -r diamond-brain/brain/ your-project/scripts/brain/
```

### 2. Use it
```python
from brain.diamond_brain import DiamondBrain

brain = DiamondBrain()  # Uses default memory/ directory

# Store knowledge
brain.learn("sql-injection", "Always use parameterized queries", 95, "OWASP", True)

# Recall knowledge
facts = brain.recall("sql-injection")

# Register a zombie agent
brain.agent_checkin("audit-bot-01", "code-auditor", "rust-safety-scan")

# Report findings (HIGH+ auto-learned)
brain.agent_report("audit-bot-01", [
    {"category": "unwrap", "severity": "HIGH", "file": "main.rs", "line": 42, "message": ".unwrap() call"}
])

# Check brain status
print(brain.digest())

# Knowledge freshness
print(brain.heatmap())
```

### 3. Customize for your project
- Set custom memory directory: `DiamondBrain(memory_dir="path/to/memory")`
- Facts stored in `memory/facts.json`
- Agent registry in `memory/agents.json`
- Escalations in `memory/escalations.json`

## API Reference

| Method | Description |
|--------|-------------|
| `recall(topic, max_results=8)` | Get facts for a topic, sorted by confidence |
| `learn(topic, fact, confidence, source, verified)` | Store a fact (fuzzy dedup at 80%) |
| `search(keyword)` | Cross-topic keyword search |
| `agent_checkin(agent_id, role, task, status)` | Register/update an agent |
| `agent_report(agent_id, findings)` | Submit findings, auto-learn HIGH+ |
| `digest()` | Full brain status overview |
| `heatmap()` | Per-topic freshness scores (0-100) |
| `escalation_needed(finding)` | Check if finding needs external review |

## Integration with LM Studio

Diamond Brain pairs with LM Studio for three-tier auditing:

1. **Tier 1** (free): Pattern scanner finds code smells
2. **Tier 2** (cheap): Local LLM via LM Studio analyzes flagged files
3. **Tier 3** (expensive): Escalated to Claude/GPT for cross-file reasoning

The Zombie Auditor script (`zombie_audit.py`) orchestrates all three tiers.

## LM Studio Setup & DeepSeek R1 Quirks

See [LM_STUDIO_GUIDE.md](LM_STUDIO_GUIDE.md) for detailed setup instructions and model recommendations.

## Origin

Inspired by `rathin_utils.brain.Brain` from the Parrot Linux rig. Rebuilt for Windows/cross-platform with zero dependencies.

## Requirements

- Python 3.10+
- No external packages (stdlib only: json, os, pathlib, datetime, difflib)

## License

MIT
