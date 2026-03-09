# LM Studio Integration — Diamond Brain
_Technical Reference | 2026-03-09_

## Overview

Diamond Brain's Neural Cortex is wired to a local LM Studio inference stack running on `localhost:1234`. The integration provides three AI capabilities: **semantic vector search**, **LLM reasoning via RAG**, and **agentic MCP tool use**. All features degrade gracefully when LM Studio is offline — fallbacks return keyword-search results or structured error states.

---

## Model Stack

| Role | Model | Size | API Identifier |
|------|-------|------|----------------|
| Embedder | nomic-embed-text-v1.5 | 84 MB | `text-embedding-nomic-embed-text-v1.5` |
| Fast LLM | Mistral-7B-Instruct-v0.3 | 4.1 GB | `mistralai/mistral-7b-instruct-v0.3` |
| Reasoner / Tools | Qwen2.5-Coder-7B-Instruct | 4.4 GB | `lmstudio-community/qwen2.5-coder-7b-instruct-gguf` |

### Why These Models

- **nomic-embed-text-v1.5** — 768-dim vectors optimised for retrieval. At 84 MB it loads in milliseconds and stays resident with no TTL.
- **Mistral-7B** — Fast generalist (69 tok/s on this hardware). Used for all cortex chat operations. Limitation: jinja template only supports user/assistant roles — system prompts are merged into the first user message.
- **Qwen2.5-Coder-7B** — Proper tool-use jinja template. Required for MCP ephemeral integrations where tool results are injected as structured messages.

---

## Architecture

```
DiamondBrain.cortex_ask(question)
    │
    ├─ _cortex_build_context()        # RAG: hybrid_search + citations + temporal
    │       │
    │       └─ hybrid_search()
    │               ├─ search()       # keyword (weight 0.4)
    │               ├─ _graph_load()  # graph centrality (weight 0.3)
    │               └─ semantic_search()  # cosine similarity (weight 0.3)
    │                       │
    │                       └─ _embed() ──► LM Studio /v1/embeddings
    │                                       nomic-embed-text-v1.5
    │
    └─ _cortex_chat(messages)
            ├─ SDK path: lmstudio.Client().llm.model().respond(Chat())
            └─ REST fallback: POST /v1/chat/completions

DiamondBrain.cortex_act(task, mcp_servers=[...])
    │
    ├─ _cortex_build_context()        # inject RAG context into prompt
    └─ POST /api/v1/chat              # LM Studio native endpoint
            └─ integrations: ephemeral_mcp or plugin
                    └─ MCP server executes tools, injects results
```

---

## SDK Client

```python
# Singleton pattern — module-level cached client
client = DiamondBrain._lms_client()   # returns lmstudio.Client or None

# Manual close (only needed on process shutdown)
DiamondBrain._lms_close()
```

The client is lazy-initialised on first call. `_lms_available = False` after any import failure short-circuits all future attempts. `lms.set_sync_api_timeout(30)` is set on init.

### Install
```bash
pip install lmstudio   # v1.5.0+
```

---

## Embeddings

### Generating Vectors
```python
brain = DiamondBrain()
vec = brain._embed("text to embed")   # → list[float] | None, 768 dims
```
Uses SDK path first (`client.embedding.model(model_id).embed(text)`), falls back to REST.

### Backfilling All Facts
```bash
python3 diamond_brain.py --embed-facts          # skip already-embedded
python3 diamond_brain.py --embed-facts --force  # re-embed everything
```
```python
result = brain.embed_facts(max_facts=500, force=False)
# → {"embedded": N, "skipped": N, "failed": N}
```
New facts are auto-embedded when `learn()` is called.

### Semantic Search
```bash
python3 diamond_brain.py --semantic-search "fraudulent check deposits"
```
```python
results = brain.semantic_search("query", top_k=10)
# → [{"topic": "...", "fact": "...", "_semantic_score": 0.646, ...}]
```

### Hybrid Search (keyword + graph + semantic)
```python
results = brain.hybrid_search("query", top_k=10, use_semantic=True)
# Weights: keyword=0.4, graph=0.3, semantic=0.3
# Falls back to 0.6/0.4 when semantic unavailable
```

### Storage
Vectors stored in `memory/embeddings.json` as `{fact_key: [float, ...]}`. Atomic writes via `.tmp` + `os.replace`. Key format: `"{topic}::{fact[:80]}"`.

---

## Chat / Cortex

### Model Constants
```python
DiamondBrain._LM_FAST_MODEL    = "mistralai/mistral-7b-instruct-v0.3"
DiamondBrain._LM_REASON_MODEL  = "lmstudio-community/qwen2.5-coder-7b-instruct-gguf"
DiamondBrain._LM_EMBED_MODEL   = "text-embedding-nomic-embed-text-v1.5"
DiamondBrain._LM_CHAT_URL      = "http://localhost:1234/v1/chat/completions"
DiamondBrain._LM_NATIVE_CHAT_URL = "http://localhost:1234/api/v1/chat"
```

### System Prompt Merging
Mistral's jinja template rejects system role. All `_cortex_chat()` calls automatically flatten the system prompt into the first user message:
```
[INSTRUCTIONS]
<system_content>

[MESSAGE]
<user_content>
```

### cortex_chat() — Internal Method
```python
response = brain._cortex_chat(
    messages=[
        {"role": "system", "content": "You are a forensic analyst."},
        {"role": "user", "content": "Summarise the fraud evidence."},
    ],
    temperature=0.3,
    max_tokens=2000,
    model=None,   # None = _LM_FAST_MODEL; pass _LM_REASON_MODEL for deep tasks
)
# → str | None
```

### Public Cortex Methods

| Method | Purpose | Model Used |
|--------|---------|-----------|
| `cortex_ask(question)` | RAG Q&A against knowledge base | fast |
| `cortex_summarize(topic)` | Summarise all facts on a topic | fast |
| `cortex_hypothesize(evidence, question)` | Generate investigative hypotheses | **reasoner** |
| `cortex_cross_examine(source_id)` | Credibility analysis of a source | fast |
| `cortex_timeline_narrative()` | Narrative from temporal events | fast |
| `cortex_case_brief(case_number)` | Full legal case brief | **reasoner** |
| `cortex_debrief(topic)` | Post-mortem brain state analysis | fast |
| `cortex_status()` | LM Studio connectivity + stats | — |

### Query Expansion
```bash
python3 diamond_brain.py --query-expand "identity theft"
```
```python
terms = brain.query_expand("identity theft", n=4)
# → ["identity theft", "stolen_identity", "account_takeover", ...]
```

### Auto-Categorize
```bash
python3 diamond_brain.py --auto-categorize "Defendant transferred funds via CashApp"
```
```python
topic = brain.auto_categorize(text, existing_topics=["fraud", "evidence_financial"])
# → "cash_app_transfers" (snake_case, max 50 chars)
```

### Expanded Search
```bash
python3 diamond_brain.py --search-expanded "stolen identity credentials"
```
```python
results = brain.search_expanded("query", top_k=10)
# Runs query_expand() then hybrid_search() per term, merges and re-ranks
```

---

## MCP Integration

### mcp.json (pre-configured servers)
Location: `~/.lmstudio/mcp.json`

```json
{
  "mcpServers": {
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch", "--ignore-robots-txt"],
      "description": "Fetch web pages and URLs"
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem",
               "/home/rathin/projects/diamond-brain",
               "/home/rathin/projects/void_cathedral",
               "/home/rathin/projects"],
      "description": "Read files from the projects directory"
    }
  }
}
```

Use in API requests: `"integrations": [{"type": "plugin", "id": "mcp/fetch"}]`

### cortex_act() — Agentic MCP Execution
```python
result = brain.cortex_act(
    task="Find current ARS 13-2310 statute text",
    mcp_servers=[{
        "type": "ephemeral_mcp",
        "server_label": "fetch",
        "server_url": "http://localhost:PORT/mcp",  # or remote URL
        "allowed_tools": ["fetch"],
    }],
    model=None,   # defaults to _LM_FAST_MODEL
    max_tokens=2000,
)
# Returns:
# {
#   "answer": "...",           # extracted text from output[].type==message
#   "output": [...],           # full native API output array
#   "response_id": "resp_...", # for stateful continuation
#   "stats": {"tokens_per_second": 69.5, ...},
#   "model": "...",
#   "mcp_servers": ["fetch"],
#   "fallback": False,
# }
```

### Stateful Continuation
```python
r1 = brain.cortex_act("Analyse the NordPass evidence")
r2 = brain.cortex_act(
    "What criminal charges does that support?",
    # Pass previous_response_id manually via native API
)
```
The native `/api/v1/chat` endpoint maintains context server-side via `previous_response_id`. `cortex_act()` returns the `response_id` — pass it back in the payload for multi-turn without resending history.

### Remote MCP (HuggingFace)
```python
result = brain.cortex_act(
    "Search for legal document embedding models",
    mcp_servers=[{
        "type": "ephemeral_mcp",
        "server_label": "huggingface",
        "server_url": "https://huggingface.co/mcp",
        "allowed_tools": ["hub_repo_search", "hf_doc_search"],
    }]
)
```
Available HF tools: `hf_whoami`, `space_search`, `hub_repo_search`, `paper_search`, `hub_repo_details`, `hf_doc_search`, `hf_doc_fetch`

**Note:** Requires Qwen or another model with tool-use jinja template. Mistral will fall back to `cortex_ask()`.

---

## LM Studio REST API — Quick Reference

### Server Management
```bash
~/.lmstudio/bin/lms server start [--port 1234]
~/.lmstudio/bin/lms server status
~/.lmstudio/bin/lms server stop
~/.lmstudio/bin/lms ps --json          # loaded models
~/.lmstudio/bin/lms ls                 # all downloaded models
~/.lmstudio/bin/lms load <model> --gpu max --context-length 8192 --ttl 600
~/.lmstudio/bin/lms unload --all
~/.lmstudio/bin/lms get <model>@q4_k_m -y   # download
~/.lmstudio/bin/lms log stream --source model --filter input,output
```

### Endpoints

| Endpoint | Use |
|----------|-----|
| `GET /v1/models` | List loaded models (OpenAI-compat) |
| `POST /v1/chat/completions` | Chat — stateless, OpenAI-compat |
| `POST /v1/embeddings` | Embeddings — OpenAI-compat |
| `POST /v1/responses` | Stateful chat + reasoning + MCP tools |
| `POST /v1/messages` | Anthropic-compat (0.4.1+) |
| `GET /api/v1/models` | Full model list with capabilities |
| `POST /api/v1/chat` | Native stateful chat + MCP integrations |
| `POST /api/v1/models/load` | Load model with config |
| `POST /api/v1/models/unload` | Unload model |
| `POST /api/v1/models/download` | Download from HF/catalog |

### Native Chat Request (full)
```bash
curl http://localhost:1234/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "lmstudio-community/qwen2.5-coder-7b-instruct-gguf",
    "input": "Summarise the fraud evidence",
    "stream": false,
    "max_output_tokens": 2000,
    "temperature": 0.3,
    "store": true,
    "integrations": [
      {
        "type": "ephemeral_mcp",
        "server_label": "huggingface",
        "server_url": "https://huggingface.co/mcp",
        "allowed_tools": ["hub_repo_search"]
      }
    ]
  }'
```

---

## CLI Reference (diamond_brain.py)

```bash
# Embeddings
python3 diamond_brain.py --embed-facts [--force]
python3 diamond_brain.py --semantic-search "<query>"

# Search
python3 diamond_brain.py --query-expand "<query>"
python3 diamond_brain.py --search-expanded "<query>"
python3 diamond_brain.py --auto-categorize "<text>"

# Cortex
python3 diamond_brain.py --cortex-status
python3 diamond_brain.py --cortex-ask "<question>"
python3 diamond_brain.py --cortex-summarize "<topic>"
python3 diamond_brain.py --cortex-hypothesize "<question>"
python3 diamond_brain.py --cortex-cross-examine "<source_id>"
python3 diamond_brain.py --cortex-timeline
python3 diamond_brain.py --cortex-brief [--case-number X]
python3 diamond_brain.py --cortex-debrief [topic]
python3 diamond_brain.py --cortex-act "<task>" [--mcp <url> <label>]
python3 diamond_brain.py --cortex-personality [on|off]

# Cortex status
python3 diamond_brain.py --cortex-status
```

---

## Testing

```bash
# Run LM Studio integration tests (requires LM Studio running)
cd ~/projects/diamond-brain
python3 -m pytest tests/test_lm_studio.py -v

# Run all tests (LM Studio tests skip if offline)
python3 -m pytest tests/ -q
```

### Test Coverage (33 tests)
- `TestSDKClient` — singleton lifecycle, REST models list
- `TestEmbeddings` — dims, cosine sim, backfill, auto-embed, semantic search, hybrid search
- `TestCortexChat` — system merge, SDK/REST fallback, model routing, all cortex methods
- `TestCortexAct` — native endpoint, stats, fallback, HF MCP, stateful continuation
- `TestMCPConfig` — mcp.json structure, uvx/npx server launchability

---

## Known Limitations

| Issue | Workaround |
|-------|-----------|
| Mistral jinja rejects system role | Auto-merged into first user message in `_cortex_chat()` |
| Mistral can't use MCP tool injection | Use Qwen as `_LM_REASON_MODEL` for `cortex_act()` |
| SDK `Chat` no system role | Same merge — handled transparently |
| Qwen model ID is coder variant | Works for all tasks; swap for `qwen2.5-7b-instruct` when available |
| embeddings.json can grow large | 314 facts ≈ 1.8 MB; trim via `embed_facts(max_facts=N)` |

---

## Upgrade Path

When a better model is downloaded, update two class constants:
```python
# In diamond_brain.py (~line 7100)
_LM_FAST_MODEL = "mistralai/mistral-7b-instruct-v0.3"
_LM_REASON_MODEL = "lmstudio-community/qwen2.5-coder-7b-instruct-gguf"
```

Recommended upgrades:
- **Reasoner**: DeepSeek-R1-8B or Qwen2.5-14B when disk allows
- **Embedder**: mxbai-embed-large-v1 (already on disk, 335M, 1024-dim) — higher quality but slower

To switch embedder: change `_LM_EMBED_MODEL` and run `--embed-facts --force` to reindex.
