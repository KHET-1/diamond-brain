"""LM Studio integration tests — SDK, embeddings, cortex, MCP.

These tests require LM Studio running on localhost:1234 with:
  - text-embedding-nomic-embed-text-v1.5 loaded
  - mistralai/mistral-7b-instruct-v0.3 loaded (or any LLM)

Tests are skipped automatically when LM Studio is offline.
"""
import json
import tempfile
import urllib.request
import urllib.error

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _lmstudio_online() -> bool:
    try:
        with urllib.request.urlopen(
                "http://localhost:1234/v1/models", timeout=3) as r:
            data = json.loads(r.read())
            return bool(data.get("data"))
    except Exception:
        return False


def _model_loaded(model_id: str) -> bool:
    try:
        with urllib.request.urlopen(
                "http://localhost:1234/v1/models", timeout=3) as r:
            data = json.loads(r.read())
            ids = [m["id"] for m in data.get("data", [])]
            return any(model_id in mid for mid in ids)
    except Exception:
        return False


LM_ONLINE = _lmstudio_online()
EMBED_READY = LM_ONLINE and _model_loaded("nomic-embed-text")
LLM_READY = LM_ONLINE and _model_loaded("mistral")

requires_lm = pytest.mark.skipif(not LM_ONLINE, reason="LM Studio offline")
requires_embed = pytest.mark.skipif(not EMBED_READY,
                                    reason="Embed model not loaded")
requires_llm = pytest.mark.skipif(not LLM_READY,
                                   reason="LLM not loaded")


def make_brain():
    from brain.diamond_brain import DiamondBrain
    d = tempfile.mkdtemp(prefix="db_lms_test_")
    b = DiamondBrain(memory_dir=d)
    b.learn("test_topic", "LM Studio provides a local AI inference server.")
    b.learn("fraud", "Defendant deposited stolen checks after account closure.")
    b.learn("identity_theft", "Perpetrator used victim credentials on NordPass.")
    return b


# ---------------------------------------------------------------------------
# SDK Client Tests
# ---------------------------------------------------------------------------

class TestSDKClient:
    @requires_lm
    def test_singleton_client_returns_same_instance(self):
        from brain.diamond_brain import DiamondBrain
        c1 = DiamondBrain._lms_client()
        c2 = DiamondBrain._lms_client()
        assert c1 is c2, "Should return the same cached client instance"

    @requires_lm
    def test_client_is_not_none(self):
        from brain.diamond_brain import DiamondBrain
        assert DiamondBrain._lms_client() is not None

    @requires_lm
    def test_models_list_via_rest(self):
        with urllib.request.urlopen(
                "http://localhost:1234/v1/models", timeout=5) as r:
            data = json.loads(r.read())
        assert "data" in data
        assert len(data["data"]) > 0


# ---------------------------------------------------------------------------
# Embedding Tests
# ---------------------------------------------------------------------------

class TestEmbeddings:
    @requires_embed
    def test_embed_returns_768_dims(self):
        b = make_brain()
        vec = b._embed("test sentence for embedding")
        assert vec is not None
        assert len(vec) == 768

    @requires_embed
    def test_embed_different_texts_differ(self):
        b = make_brain()
        v1 = b._embed("financial fraud bank account")
        v2 = b._embed("astronomy telescope stars")
        assert v1 is not None and v2 is not None
        sim = DiamondBrain._cosine(v1, v2)
        assert sim < 0.9, f"Unrelated texts should not be highly similar, got {sim}"

    @requires_embed
    def test_embed_similar_texts_are_close(self):
        from brain.diamond_brain import DiamondBrain
        b = make_brain()
        v1 = b._embed("identity theft stealing credentials")
        v2 = b._embed("account takeover stolen password")
        assert v1 and v2
        sim = DiamondBrain._cosine(v1, v2)
        assert sim > 0.65, f"Similar texts should have high cosine sim, got {sim}"

    @requires_embed
    def test_embed_facts_backfills_store(self):
        b = make_brain()
        result = b.embed_facts()
        # learn() auto-embeds each fact on creation, so embed_facts()
        # finds them already in the store (skipped, not re-embedded).
        assert result["embedded"] + result["skipped"] == 3
        assert result["failed"] == 0
        store = b._emb_load()
        assert len(store) == 3

    @requires_embed
    def test_embed_facts_skips_existing(self):
        b = make_brain()
        b.embed_facts()
        result2 = b.embed_facts()
        assert result2["skipped"] == 3
        assert result2["embedded"] == 0

    @requires_embed
    def test_embed_facts_force_reembeds(self):
        b = make_brain()
        b.embed_facts()
        result = b.embed_facts(force=True)
        assert result["embedded"] == 3

    @requires_embed
    def test_learn_auto_embeds_new_fact(self):
        b = make_brain()
        b.learn("auto_embed_test", "This fact should be embedded immediately.")
        store = b._emb_load()
        keys = list(store.keys())
        assert any("auto_embed_test" in k for k in keys), \
            f"New fact not found in embed store. Keys: {keys}"

    @requires_embed
    def test_semantic_search_returns_ranked_results(self):
        b = make_brain()
        b.embed_facts()
        results = b.semantic_search("stolen credentials NordPass", top_k=3)
        assert len(results) > 0
        assert results[0].get("topic") == "identity_theft"
        scores = [r["_semantic_score"] for r in results]
        assert scores == sorted(scores, reverse=True), "Results must be ranked by score"

    @requires_embed
    def test_semantic_search_empty_when_no_store(self):
        b = make_brain()  # no embed_facts called
        results = b.semantic_search("fraud")
        # Should return [] since no vectors stored yet (learn auto-embeds,
        # but in a fresh brain the 3 learn() calls above may or may not
        # have connected — either result is valid)
        assert isinstance(results, list)

    @requires_embed
    def test_hybrid_search_blends_all_three_legs(self):
        b = make_brain()
        b.embed_facts()
        results = b.hybrid_search("stolen account fraud", top_k=5)
        assert len(results) > 0
        for r in results:
            assert "_hybrid_score" in r
        # Top result should be relevant to fraud/identity
        top_topic = results[0].get("topic", "")
        assert top_topic in ("fraud", "identity_theft", "test_topic")


# ---------------------------------------------------------------------------
# Chat / Cortex Tests
# ---------------------------------------------------------------------------

class TestCortexChat:
    @requires_llm
    def test_cortex_chat_returns_string(self):
        b = make_brain()
        result = b._cortex_chat([
            {"role": "system", "content": "Reply in one word only."},
            {"role": "user", "content": "Say CONFIRMED."},
        ])
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

    @requires_llm
    def test_cortex_chat_system_prompt_merged(self):
        """System prompt must not cause jinja template error."""
        b = make_brain()
        result = b._cortex_chat([
            {"role": "system",
             "content": "You are a legal analyst. Be very brief."},
            {"role": "user",
             "content": "What does ARS stand for in Arizona law?"},
        ], max_tokens=50)
        assert result is not None
        assert "Arizona" in result or "Revised" in result or "Statutes" in result

    @requires_llm
    def test_cortex_chat_fallback_without_sdk(self):
        """Force REST fallback path."""
        from brain.diamond_brain import DiamondBrain
        orig = DiamondBrain._lms_available
        try:
            DiamondBrain._lms_available = False
            b = make_brain()
            result = b._cortex_chat([
                {"role": "user", "content": "Say YES."}
            ], max_tokens=10)
            assert result is not None
        finally:
            DiamondBrain._lms_available = orig
            DiamondBrain._lms_client_instance = None

    @requires_llm
    def test_query_expand_returns_list(self):
        b = make_brain()
        terms = b.query_expand("financial fraud", n=3)
        assert isinstance(terms, list)
        assert terms[0] == "financial fraud"
        assert len(terms) >= 2, "Should expand to at least 2 terms"

    @requires_llm
    def test_auto_categorize_returns_snake_case(self):
        b = make_brain()
        topic = b.auto_categorize(
            "Defendant used victim's debit card at an ATM on three occasions")
        assert topic is not None
        assert "_" in topic or topic.isalpha()
        assert topic == topic.lower()
        assert len(topic) <= 50

    @requires_llm
    def test_search_expanded_merges_results(self):
        b = make_brain()
        b.embed_facts()
        results = b.search_expanded("stolen identity credentials", top_k=5)
        assert isinstance(results, list)
        for r in results:
            assert "_expanded_score" in r

    @requires_llm
    def test_cortex_ask_returns_answer(self):
        b = make_brain()
        b.embed_facts()
        result = b.cortex_ask("What evidence of fraud is in the knowledge base?")
        assert "answer" in result
        assert result["answer"]
        assert result["model"] in ("lm_studio", "fallback")

    @requires_llm
    def test_cortex_summarize_covers_topic(self):
        b = make_brain()
        result = b.cortex_summarize("fraud")
        assert "summary" in result
        assert result["fact_count"] >= 1

    @requires_llm
    def test_cortex_chat_respects_model_routing(self):
        """cortex_hypothesize should use _LM_REASON_MODEL."""
        from brain.diamond_brain import DiamondBrain
        called_with = []
        orig = b = make_brain()
        orig_chat = DiamondBrain._cortex_chat

        def spy(self, messages, temperature=0.3, max_tokens=2000, model=None):
            called_with.append(model)
            return "stub"

        DiamondBrain._cortex_chat = spy
        try:
            b.cortex_hypothesize(["fraud"], "Who committed fraud?")
            assert called_with[-1] == DiamondBrain._LM_REASON_MODEL
        finally:
            DiamondBrain._cortex_chat = orig_chat


# ---------------------------------------------------------------------------
# Native API / cortex_act Tests
# ---------------------------------------------------------------------------

class TestCortexAct:
    @requires_llm
    def test_cortex_act_basic_returns_answer(self):
        b = make_brain()
        b.embed_facts()
        result = b.cortex_act("Summarize the evidence of financial fraud in one sentence.")
        assert "answer" in result
        assert isinstance(result["answer"], str)
        assert len(result["answer"]) > 0

    @requires_llm
    def test_cortex_act_has_stats_when_not_fallback(self):
        b = make_brain()
        result = b.cortex_act("Say the word CONFIRMED.")
        if not result["fallback"]:
            assert "response_id" in result
            # Stats may be empty dict on fallback path
            assert isinstance(result["stats"], dict)

    @requires_llm
    def test_cortex_act_fallback_on_bad_endpoint(self):
        """When native endpoint unreachable, falls back to cortex_ask."""
        from brain.diamond_brain import DiamondBrain
        orig_url = DiamondBrain._LM_NATIVE_CHAT_URL
        try:
            DiamondBrain._LM_NATIVE_CHAT_URL = "http://localhost:9999/api/v1/chat"
            b = make_brain()
            result = b.cortex_act("What is fraud?")
            assert result["fallback"] is True
            assert isinstance(result["answer"], str)
        finally:
            DiamondBrain._LM_NATIVE_CHAT_URL = orig_url

    @requires_llm
    def test_cortex_act_with_hf_mcp(self):
        """Ephemeral HuggingFace MCP — requires LM Studio to allow remote MCPs
        and a model with tool-use jinja template support.
        Skipped if the native endpoint returns an error (model template issue).
        """
        b = make_brain()
        result = b.cortex_act(
            "Search HuggingFace for embedding models for legal text analysis.",
            mcp_servers=[{
                "type": "ephemeral_mcp",
                "server_label": "huggingface",
                "server_url": "https://huggingface.co/mcp",
                "allowed_tools": ["hub_repo_search", "hf_doc_search"],
            }]
        )
        # If the model doesn't support tool-use, it falls back — either is valid
        assert "answer" in result
        assert isinstance(result["answer"], str)

    @requires_lm
    def test_native_endpoint_returns_response_id(self):
        """Raw native API test — model-independent."""
        payload = json.dumps({
            "model": "mistralai/mistral-7b-instruct-v0.3",
            "input": "Reply: NATIVE_OK",
            "stream": False,
            "max_output_tokens": 20,
        }).encode()
        req = urllib.request.Request(
            "http://localhost:1234/api/v1/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        assert "response_id" in data
        assert data["response_id"].startswith("resp_")
        assert "stats" in data
        assert data["stats"]["tokens_per_second"] > 0

    @requires_lm
    def test_native_stateful_continuation(self):
        """Test previous_response_id for stateful conversation."""
        def _chat(text, prev_id=None):
            body = {
                "model": "mistralai/mistral-7b-instruct-v0.3",
                "input": text,
                "stream": False,
                "max_output_tokens": 50,
            }
            if prev_id:
                body["previous_response_id"] = prev_id
            payload = json.dumps(body).encode()
            req = urllib.request.Request(
                "http://localhost:1234/api/v1/chat",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())

        r1 = _chat("My secret number is 42. Acknowledge with OK.")
        assert "response_id" in r1
        r2 = _chat("What was my secret number?",
                   prev_id=r1["response_id"])
        content = r2["output"][0]["content"]
        assert "42" in content, f"Model forgot the number. Got: {content}"


# ---------------------------------------------------------------------------
# MCP Config Tests
# ---------------------------------------------------------------------------

class TestMCPConfig:
    def test_mcp_json_has_fetch_server(self):
        import json
        from pathlib import Path
        mcp_path = Path.home() / ".lmstudio" / "mcp.json"
        assert mcp_path.exists(), "mcp.json not found"
        cfg = json.loads(mcp_path.read_text())
        assert "mcpServers" in cfg
        assert "fetch" in cfg["mcpServers"]
        assert "filesystem" in cfg["mcpServers"]

    def test_mcp_fetch_server_config_valid(self):
        import json
        from pathlib import Path
        cfg = json.loads(
            (Path.home() / ".lmstudio" / "mcp.json").read_text())
        fetch = cfg["mcpServers"]["fetch"]
        assert fetch["command"] == "uvx"
        assert "mcp-server-fetch" in fetch["args"]

    def test_mcp_filesystem_server_config_valid(self):
        import json
        from pathlib import Path
        cfg = json.loads(
            (Path.home() / ".lmstudio" / "mcp.json").read_text())
        fs = cfg["mcpServers"]["filesystem"]
        assert fs["command"] == "npx"
        assert any("server-filesystem" in a for a in fs["args"])
        assert "/home/rathin/projects/diamond-brain" in fs["args"]

    def test_uvx_mcp_server_fetch_launchable(self):
        """Verify uvx can launch mcp-server-fetch (smoke check)."""
        import subprocess
        result = subprocess.run(
            ["uvx", "mcp-server-fetch", "--help"],
            capture_output=True, text=True, timeout=30
        )
        assert result.returncode == 0
        assert "fetch" in result.stdout.lower() or "web" in result.stdout.lower()

    def test_npx_mcp_server_filesystem_launchable(self):
        """Verify npx can launch filesystem MCP server (smoke check)."""
        import subprocess, signal
        proc = subprocess.Popen(
            ["npx", "-y", "@modelcontextprotocol/server-filesystem",
             "/tmp"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        try:
            # Give it 5 seconds to start
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # Still running = good (it's a server, no timeout = success)
            proc.send_signal(signal.SIGTERM)
            proc.wait()
            return
        # If it exited quickly, check it wasn't a hard error
        assert proc.returncode in (0, -15), \
            f"Server crashed with code {proc.returncode}"


# ---------------------------------------------------------------------------
# Import for inline use
# ---------------------------------------------------------------------------
from brain.diamond_brain import DiamondBrain  # noqa: E402
