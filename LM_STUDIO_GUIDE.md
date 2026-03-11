# LM Studio Integration Guide

## Setup

### Install LM Studio
Download from [lmstudio.ai/download](https://lmstudio.ai/download). Current version: 0.4.4-1 (Feb 2026).

### CLI Tool (`lms`)
Ships with LM Studio, auto-added to PATH on first run.

```bash
lms --version          # Check CLI version
lms server start       # Start API server (port 1234)
lms server stop        # Stop server
lms ls                 # List local models
lms ps                 # Show loaded models
lms load <model>       # Load a model
lms unload <model>     # Unload a model
```

## Model Recommendations for Code Audit

Tested on RTX 4080 Laptop GPU (12 GB VRAM):

| Role | Model | Size | Speed | Quality | Verdict |
|------|-------|------|-------|---------|---------|
| **Tier 1.5 Triage** | Ministral-3-3B | 2.99 GB | 0.1s/q | 100% on binary FP detection | **Best sentinel worker** |
| **Tier 2 Deep Analysis** | DeepSeek-R1-0528-Qwen3-8B-Q6_K | 6.73 GB | ~55s/file | Best reasoning at 8B | **Best reasoner** |
| Not recommended | Qwen3-4B-Instruct | 2.50 GB | 0.4s/q | 50% — too trigger-happy | Says "1" for everything |

**Multi-model stack** (both loaded simultaneously, ~9.7 GB VRAM):
- `sentinel-fast` = Ministral-3-3B → binary yes/no triage (Tier 1.5)
- `reasoner` = DeepSeek-R1-8B → deep file analysis (Tier 2)

## DeepSeek R1 Quirks (Things We Learned)

### 1. Thinking Tokens Eat Your Context
DeepSeek R1 uses "thinking" tokens (internal chain-of-thought) that consume context window space. A 4096 context window is NOT enough for code audit — the thinking tokens alone can use 2000+ tokens before the model even starts responding.

**Fix:** Load with `--context-length 16384` minimum:
```bash
lms load <model> --gpu max --context-length 16384 --identifier sentinel-auditor --yes
```

### 2. Context Size Exceeded = 400 Error
When the input + thinking tokens exceed the context, LM Studio returns:
```json
{"error": "Context size has been exceeded."}
```
This is an HTTP 400, not a timeout. Your code should catch this and truncate the input.

**Fix:** Truncate source files to ~10,000 characters before sending:
```python
max_chars = 10000
if len(content) > max_chars:
    content = content[:max_chars] + "\n// ... (truncated for analysis)\n"
```

### 3. Model Identifier Matters
The model name in API calls must match the identifier you set when loading:
```python
# WRONG — "local-model" is not a valid identifier
payload = {"model": "local-model", ...}

# RIGHT — use the identifier from lms load --identifier
payload = {"model": "sentinel-auditor", ...}
```

### 4. Empty Responses (Thinking Only)
Sometimes DeepSeek R1 spends all output tokens on thinking and returns an empty response. This is normal for complex prompts. Increase `max_tokens` or simplify the prompt.

### 5. LM Studio Directory Structure
Models must be in `publisher/model-name-GGUF/file.gguf` format:
```
S:\AI_Models\
  lmstudio-community\
    DeepSeek-R1-0528-Qwen3-8B-GGUF\
      DeepSeek-R1-0528-Qwen3-8B-Q6_K.gguf    <- Recognized
  DeepSeek-R1-0528-Qwen3-8B-Q6_K.gguf        <- NOT recognized (loose file)
```

Loose `.gguf` files at the root won't show up in `lms ls`. Move them into the proper directory structure.

### 6. PowerShell Required for CLI
The `lms` CLI needs PowerShell to start the llmster daemon. In Git Bash/WSL:
```bash
export PATH="$PATH:/c/Windows/System32/WindowsPowerShell/v1.0"
lms server start
```

### 7. Parallel Requests (Yes, It Works!)
LM Studio 0.4.0+ supports parallel requests via continuous batching:
- **Same model, multiple requests**: Set "Max Concurrent Predictions" slider (default: 4 slots)
- **Multiple instances**: Load the same model twice with different identifiers
- **MLX parallel**: Added Feb 2026 for Apple Silicon

```bash
# Load two instances of the same model
lms load <model> --identifier auditor-1 --yes
lms load <model> --identifier auditor-2 --yes

# Now auditor-1 and auditor-2 can process requests simultaneously
```

For continuous batching (single instance, multiple requests), this is enabled by default in 0.4.0+. No extra config needed.

## API Endpoint

```
POST http://localhost:1234/v1/chat/completions
Content-Type: application/json

{
    "model": "sentinel-auditor",
    "messages": [
        {"role": "system", "content": "You are a Rust code auditor..."},
        {"role": "user", "content": "File: main.rs\n```rust\n...\n```"}
    ],
    "temperature": 0.1,
    "max_tokens": 2048
}
```

## Binary Truth Engine Pattern (Tier 1.5)

Instead of sending whole files to the LLM (slow, ~80-100s/file), ask binary yes/no questions about each finding. The LLM replies with just `1` (real) or `0` (false positive).

```python
# Traditional: "Analyze this 500-line file for issues"
# → 10,000 input tokens + 2,000 output tokens = ~80 seconds

# Truth engine: "Is this .unwrap() on line 42 unguarded? 1 or 0"
# → 50 input tokens + 1 output token = ~0.1 seconds (Ministral-3-3B)
```

### Model Selection for Truth Engine

**Use a fast, non-thinking model** — NOT a reasoning model. Reasoning models waste time
on chain-of-thought for a binary answer.

| Model | Accuracy | Speed | Verdict |
|-------|----------|-------|---------|
| **Ministral-3-3B** | **100% (6/6)** | **0.1s/q** | **Best for truth engine** |
| Qwen3-4B (thinking) | 50% (3/6) | 0.5s/q | Too trigger-happy, says "1" for everything |
| Qwen3-4B (no-think) | 50% (3/6) | 0.4s/q | Same bias even without thinking |
| DeepSeek R1 8B | 17% (1/6) | 41s/q | Terrible — thinking tokens make binary answers unreliable |

### Prompt Engineering (Critical!)

A simple "reply 0 or 1" prompt gets ~67% accuracy. Adding **rules + few-shot examples** gets 100%.

**The winning prompt:**
```python
TRUTH_SYSTEM = """You are a Rust code safety auditor. Reply ONLY 0 or 1.
0 = false positive. 1 = real issue.

RULES:
- .unwrap() after .is_some()/.is_ok() → 0
- .expect() in main() or init → 0
- panic! in wildcard _ arm when all enum variants are already matched → 0
- .unwrap() without any guard → 1
- Unbounded collection in infinite loop → 1
- O(n) operation in render/tick → 1

Examples:
Code: if x.is_some() { x.unwrap(); }
Q: dangerous? A: 0

Code: list.first().unwrap();
Q: dangerous? A: 1

Code: match d { Variant1 => .., Variant2 => .., _ => panic!("impossible") }
Q: reachable panic? A: 0

Code: fn main() { f().expect("err"); }
Q: dangerous expect? A: 0

Reply ONLY 0 or 1. No other text."""
```

**Key findings about prompting:**
- Few-shot examples are essential — they teach the model what "false positive" means
- Rules alone aren't enough; the model needs concrete examples
- JSON Schema (`response_format`) actually **hurts** accuracy — biases models toward `{"real": true}`
- Keep user messages minimal: `Code: {snippet}\nQ: {question}\nA:` (the trailing `A:` primes the answer)
- `max_tokens: 4` is plenty for non-thinking models (they output a single digit)

### DeepSeek R1: Why NOT to Use for Truth Engine

DeepSeek R1 uses "thinking" tokens (internal chain-of-thought) that are invisible but consume context and time. For binary questions:
- ~200 thinking tokens consumed before the answer
- Often returns empty content or `?` instead of `0`/`1`
- 300x slower than Ministral for the same task
- `reasoning_content` field has the thinking, but the final digit is unreliable

**Use DeepSeek R1 for Tier 2 deep analysis (where reasoning helps), not Tier 1.5 triage.**

### Multi-Model Strategy

```bash
# Tier 1.5 — Fast binary triage (0.1s/question)
lms load mistralai/ministral-3-3b --identifier sentinel-fast --gpu max --context-length 8192 --yes

# Tier 2 — Deep reasoning analysis (~55s/file)
lms load deepseek-r1-0528-qwen3-8b --identifier reasoner --gpu max --context-length 16384 --yes
```

Both models can be loaded simultaneously on a 12GB VRAM GPU (~9.7GB total).

### Results

On Diamond NetBlade (120 Tier 1 findings):
- **Without truth filter**: 120 findings → Tier 2 analyzes 25 files @ ~55s each = ~23 min
- **With truth filter**: 120 findings filtered to ~30 real in ~3s, then Tier 2 only hits ~8 files (~7 min)

---

## Diamond Brain + LM Studio Integration

### Why Connect LM Studio to Diamond Brain?

Diamond Brain out of the box uses keyword matching and fuzzy string similarity (`difflib`). It works, but it's dumb — it can't understand meaning, only character overlap. Connecting a local LLM through LM Studio turns the brain from a glorified grep into something that actually *thinks*.

Here's every way LM Studio makes Diamond Brain better:

### 1. Smart Flag Suggestions (Already Built)

**What it does:** When you run `--suggest "git" --smart`, the brain sends your flag usage history to the LLM and gets back context-aware suggestions you might not know about.

**Without LM Studio:** Just shows your most-used flags ranked by frequency/recency.
**With LM Studio:** Suggests flags you've *never used* but probably should based on your patterns.

```bash
# Frequency-only (no LM Studio needed)
python -m brain.diamond_brain --suggest "git commit"

# LLM-powered (needs sentinel-fast model loaded)
python -m brain.diamond_brain --suggest "git commit" --smart
```

**Model:** `sentinel-fast` (Ministral-3-3B) — fast enough that suggestions feel instant.

### 2. Semantic Search (Upgrade Path)

**The problem:** `brain.search("network intrusion")` won't find a fact stored under topic `forensics-tools-network` that says "Zeek performs deep packet inspection for threat hunting" — there's no keyword overlap.

**The fix:** Use LM Studio's embedding endpoint to convert facts and queries into vectors, then match by meaning.

**How to use embeddings with LM Studio:**
```bash
# Load an embedding model
lms load nomic-ai/nomic-embed-text-v1.5-GGUF --identifier embedder --gpu max --yes
```

```python
# Generate embeddings via LM Studio API
import urllib.request, json

def get_embedding(text: str) -> list[float]:
    payload = json.dumps({
        "model": "embedder",
        "input": text
    }).encode()
    req = urllib.request.Request(
        "http://localhost:1234/v1/embeddings",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return data["data"][0]["embedding"]

# Compare similarity
import math
def cosine_sim(a, b):
    dot = sum(x*y for x,y in zip(a,b))
    mag_a = math.sqrt(sum(x*x for x in a))
    mag_b = math.sqrt(sum(x*x for x in b))
    return dot / (mag_a * mag_b) if mag_a and mag_b else 0.0

query_vec = get_embedding("network intrusion detection")
fact_vec = get_embedding("Zeek performs deep packet inspection for threat hunting")
print(cosine_sim(query_vec, fact_vec))  # ~0.82 — high match!
```

**Recommended embedding models:**

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| **nomic-embed-text-v1.5** | 274 MB | ~2ms/query | Excellent for retrieval | **Best default** |
| mxbai-embed-large | 670 MB | ~5ms/query | Slightly better accuracy | Large knowledge bases |
| all-MiniLM-L6-v2 | 91 MB | <1ms/query | Good enough | Low VRAM / CPU-only |

### 3. Auto-Categorization

**The problem:** When you `brain.learn("stuff", "YARA rules detect malware patterns")`, you chose a garbage topic name. The brain stores it but it's unfindable later.

**The fix:** Before storing, ask the LLM to suggest a proper category.

```python
prompt = f"""Given this fact: "{fact_text}"
Suggest the best category name from this list: {existing_topics}
Or suggest a new descriptive category name.
Reply with ONLY the category name, nothing else."""
```

**Model:** `sentinel-fast` — categorization is a simple classification task.

### 4. Fact Summarization & Deduplication

**The problem:** After months of use, the brain accumulates verbose, overlapping facts. The 80% fuzzy dedup catches near-duplicates but misses semantic duplicates like:
- "Volatility 3 is a memory forensics framework"
- "vol3 is the go-to tool for RAM analysis"

**The fix:** Periodically ask the LLM to review a topic's facts and merge/condense.

```python
prompt = f"""These facts are stored under topic "{topic}":
{json.dumps(facts, indent=2)}

Identify any that are semantically duplicate or could be merged.
Return a JSON array of merged facts, each with "fact" and "confidence" keys.
Remove redundancy. Keep the most specific details from each."""
```

**Model:** `reasoner` (DeepSeek-R1-8B) — needs reasoning to judge semantic overlap.

### 5. Knowledge Gap Detection

**The problem:** You've seeded 119 forensics facts but how do you know what's *missing*?

**The fix:** Send the brain's topic list + fact summaries to the LLM and ask what's absent.

```python
prompt = f"""Here are the topics and fact counts in a digital forensics knowledge base:
{json.dumps(topic_summary)}

What critical forensics knowledge areas are MISSING?
Consider: incident response, cloud forensics, IoT forensics,
cryptocurrency tracing, container forensics, AI-generated content detection.
Reply as a JSON array of {{"topic": "...", "why": "..."}} objects."""
```

**Model:** `reasoner` — needs broad knowledge and reasoning about coverage gaps.

### 6. Smarter Auto-Linking

**The problem:** `_auto_link()` uses fuzzy string matching on topic names. "memory-forensics" links to "forensics-tools-memory" (good) but won't link "volatility" to "forensics-tools-memory" (no string overlap).

**The fix:** Use the LLM to identify conceptual relationships.

```python
prompt = f"""Topic: "{new_topic}" — Fact: "{new_fact}"
Existing topics: {existing_topics}
Which existing topics are conceptually related? Reply as a JSON array of topic names."""
```

**Model:** `sentinel-fast` — classification task, fast enough to run on every `learn()` call.

### 7. Query Expansion

**The problem:** `brain.search("RAM analysis")` misses facts containing "memory forensics" or "volatile data acquisition".

**The fix:** Expand the query with synonyms before searching.

```python
prompt = f"""Expand this search query with synonyms and related terms: "{query}"
Domain: digital forensics and security.
Reply as a JSON array of search strings. Max 5."""

# "RAM analysis" → ["RAM analysis", "memory forensics", "volatile data",
#                    "memory acquisition", "physical memory dump"]
```

**Model:** `sentinel-fast` — simple synonym generation.

### 8. Fact Validation & Contradiction Detection

**The problem:** Two facts might contradict each other and you'd never know:
- "MD5 is acceptable for evidence integrity verification"
- "MD5 is cryptographically broken and should never be used for evidence"

**The fix:** When learning a new fact, ask the LLM to check against existing facts on the same topic.

```python
prompt = f"""New fact: "{new_fact}"
Existing facts on this topic:
{json.dumps(existing_facts)}

Does the new fact CONTRADICT any existing fact?
Reply: {{"contradicts": true/false, "conflicting_fact": "..." or null, "resolution": "..."}}"""
```

**Model:** `reasoner` — needs careful comparison and judgment.

### 9. Natural Language Digest

**The problem:** `brain.digest()` returns raw JSON stats. Useful for code, not for humans.

**The fix:** Feed the digest to the LLM for a narrative summary.

```python
prompt = f"""Summarize this knowledge base status for a security analyst:
{json.dumps(brain.digest(), indent=2)}

Include: what's well-covered, what's stale, what needs attention.
Keep it under 5 sentences. Be direct."""
```

**Model:** `sentinel-fast` — straightforward text generation.

### 10. Command Prediction

**The problem:** You logged 500 commands. The brain can suggest flags, but can't predict what you'll run next.

**The fix:** Feed recent command history to the LLM with working directory context.

```python
prompt = f"""Recent commands (newest first):
{recent_commands}
Current directory: {cwd}

What command is the user most likely to run next?
Reply with ONLY the command string, nothing else."""
```

**Model:** `sentinel-fast` — pattern matching on short context.

---

### Model Recommendations for Diamond Brain

| Role | Model | Identifier | VRAM | Why |
|------|-------|------------|------|-----|
| **Fast tasks** (suggestions, categorization, query expansion, linking, digest) | Ministral-3-3B | `sentinel-fast` | ~3 GB | Sub-second responses, good enough for classification |
| **Reasoning tasks** (gap detection, dedup, validation, deep analysis) | DeepSeek-R1-0528-Qwen3-8B | `reasoner` | ~7 GB | Best reasoning at 8B, worth the wait |
| **Embeddings** (semantic search) | nomic-embed-text-v1.5 | `embedder` | ~0.3 GB | Tiny, fast, excellent retrieval quality |

**Full stack (all three loaded):** ~10.3 GB VRAM — fits on a 12 GB GPU.

```bash
# Load the full Diamond Brain stack
lms load mistralai/ministral-3-3b --identifier sentinel-fast --gpu max --context-length 8192 --yes
lms load deepseek-r1-0528-qwen3-8b --identifier reasoner --gpu max --context-length 16384 --yes
lms load nomic-ai/nomic-embed-text-v1.5-GGUF --identifier embedder --gpu max --yes
```

### Quick Test

```bash
# Verify all models are loaded
lms ps

# Test fast model
curl -s http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"sentinel-fast","messages":[{"role":"user","content":"Reply OK"}],"max_tokens":4}' \
  | python -m json.tool

# Test embeddings
curl -s http://localhost:1234/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{"model":"embedder","input":"test query"}' \
  | python -c "import sys,json; d=json.load(sys.stdin); print(f'Embedding dim: {len(d[\"data\"][0][\"embedding\"])}')"

# Test smart suggestions (needs commands logged first)
python -m brain.diamond_brain --suggest "git" --smart
```

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `lms: command not found` | Not on PATH | `export PATH="$PATH:/c/Users/YOU/.lmstudio/bin"` |
| `powershell.exe not found` | Missing from PATH in bash | `export PATH="$PATH:/c/Windows/System32/WindowsPowerShell/v1.0"` |
| 400 Context exceeded | File too large for context window | Truncate to 10K chars, use 16K+ context |
| Empty response | Thinking tokens consumed output budget | Increase max_tokens or simplify prompt |
| Model not in `lms ls` | Loose GGUF file | Move to `publisher/model-GGUF/` directory structure |
