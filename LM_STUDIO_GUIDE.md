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

| Model | Size | VRAM | Quality | Speed | Verdict |
|-------|------|------|---------|-------|---------|
| DeepSeek-R1-0528-Qwen3-8B-Q6_K | 6.3 GB | ~7 GB | Best reasoning at 8B | ~55s/file | **Recommended** |
| Ministral-3-14B-Reasoning Q4_K_M | 7.7 GB | ~9 GB | Stronger but more quantized | Slower | Good if VRAM allows |
| DeepSeek-R1-0528-Qwen3-8B-Q4_K_M | 4.7 GB | ~5 GB | Good reasoning, smaller | ~40s/file | Budget option |
| Qwen3-4B-Instruct Q4_K_M | 2.4 GB | ~3 GB | Weak for code audit | Fast | Not recommended |

## DeepSeek R1 Quirks (Things We Learned)

### 1. Thinking Tokens Eat Your Context
DeepSeek R1 uses "thinking" tokens (internal chain-of-thought) that consume context window space. A 4096 context window is NOT enough for code audit — the thinking tokens alone can use 2000+ tokens before the model even starts responding.

**Fix:** Load with `--context-length 16384` minimum:
```bash
lms load <model> --gpu max --context-length 16384 --identifier zombie-auditor --yes
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
payload = {"model": "zombie-auditor", ...}
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
    "model": "zombie-auditor",
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
# → 50 input tokens + 1 output token = ~3-10 seconds
```

### DeepSeek R1 Thinking Budget

DeepSeek R1 uses ~200 thinking tokens even for binary questions. Set `max_tokens: 256` (not 8) to leave room for thinking + the 1-digit answer.

The response separates thinking from output:
```json
{
  "content": "\n1",
  "reasoning_content": "Let me analyze this code..."
}
```

### Structured Outputs

LM Studio supports structured outputs via JSON Schema. For the truth engine:
```json
{
  "model": "zombie-auditor",
  "messages": [...],
  "max_tokens": 256,
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "name": "verdict",
      "schema": {
        "type": "object",
        "properties": {
          "real": {"type": "boolean"}
        },
        "required": ["real"]
      }
    }
  }
}
```

This forces the model to output `{"real": true}` or `{"real": false}` — no parsing needed.

### Results

On Diamond NetBlade (120 Tier 1 findings):
- **Without truth filter**: 120 findings → Tier 2 analyzes 25 files @ ~80s each = ~33 min
- **With truth filter**: 120 findings filtered to ~30 real ones in ~2-5 min, then Tier 2 only hits ~8 files

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `lms: command not found` | Not on PATH | `export PATH="$PATH:/c/Users/YOU/.lmstudio/bin"` |
| `powershell.exe not found` | Missing from PATH in bash | `export PATH="$PATH:/c/Windows/System32/WindowsPowerShell/v1.0"` |
| 400 Context exceeded | File too large for context window | Truncate to 10K chars, use 16K+ context |
| Empty response | Thinking tokens consumed output budget | Increase max_tokens or simplify prompt |
| Model not in `lms ls` | Loose GGUF file | Move to `publisher/model-GGUF/` directory structure |
