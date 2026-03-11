#!/usr/bin/env python3
"""Diamond Brain HTTP bridge server — hardened for production.

Exposes DiamondBrain methods over HTTP/1.1 on a configurable port (default 7734).
All endpoints accept/return JSON. No external dependencies — stdlib only.

Hardening:
  - threading.RLock around all brain operations (thread-safe under HTTPServer)
  - Input validation on every endpoint (required fields, type checks)
  - No traceback leaks — internal errors return generic message + log to stderr
  - Base64 validation on blob_store
  - Content-Length cap (16 MiB default)

Usage:
    python brain/server.py --memory-dir brain/memory-forensic --port 7734
"""

import argparse
import base64
import binascii
import json
import socketserver
import sys
import threading
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

# Ensure diamond-brain root is importable
_script_dir = Path(__file__).resolve().parent
_project_root = _script_dir.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from brain.diamond_brain import DiamondBrain  # noqa: E402
from brain.fsd_key_vault import FSDKeyVault  # noqa: E402

MAX_BODY_BYTES = 16 * 1024 * 1024  # 16 MiB


# ── Validation helpers ─────────────────────────────────────────────

def _require(body: dict, key: str, typ: type = str) -> None:
    """Raise ValueError if key is missing or wrong type."""
    if key not in body:
        raise ValueError(f"missing required field: '{key}'")
    if not isinstance(body[key], typ):
        raise ValueError(f"'{key}' must be {typ.__name__}, got {type(body[key]).__name__}")


def _optional(body: dict, key: str, typ: type, default=None):
    """Return body[key] if present and correct type, else default."""
    val = body.get(key, default)
    if val is not None and not isinstance(val, typ):
        raise ValueError(f"'{key}' must be {typ.__name__}, got {type(val).__name__}")
    return val


# ── Handler ────────────────────────────────────────────────────────

class BrainHandler(BaseHTTPRequestHandler):
    """Thread-safe HTTP handler that dispatches to DiamondBrain methods."""

    server_version = "DiamondBrain/3.0"

    # Suppress per-request log lines (too noisy for forensic use)
    def log_message(self, format, *args):
        pass

    # ── Routing ────────────────────────────────────────────────────

    def do_GET(self):
        if self.path == "/status":
            self._safe_call(self._handle_status, None)
        elif self.path == "/vault/status":
            self._safe_vault_call(self._handle_vault_status, None)
        elif self.path == "/vault/history":
            self._safe_vault_call(self._handle_vault_history, None)
        else:
            self._send_error(404, f"Unknown endpoint: {self.path}")

    def do_POST(self):
        routes = {
            # ── Original 7 (must-fix hardened) ─────────────
            "/learn":           self._handle_learn,
            "/recall":          self._handle_recall,
            "/cortex_ask":      self._handle_cortex_ask,
            "/blob_store":      self._handle_blob_store,
            "/agent_checkin":   self._handle_agent_checkin,
            "/agent_report":    self._handle_agent_report,
            "/temporal_add":    self._handle_temporal_add,
            # ── Must-add for Diamond Drill integration ─────
            "/search":             self._handle_search,
            "/hybrid_search":      self._handle_hybrid_search,
            "/batch_learn":        self._handle_batch_learn,
            "/graph_auto_index":   self._handle_graph_auto_index,
            "/third_eye_scan":     self._handle_third_eye_scan,
            "/quarantine_list":    self._handle_quarantine_list,
            "/cite":               self._handle_cite,
            "/recall_citations":   self._handle_recall_citations,
            # ── Should-add for full integration ────────────
            "/cortex_summarize":      self._handle_cortex_summarize,
            "/cortex_hypothesize":    self._handle_cortex_hypothesize,
            "/detect_contradictions": self._handle_detect_contradictions,
            "/forget":                self._handle_forget,
            "/amnesia_restore":       self._handle_amnesia_restore,
            "/amnesia_log":           self._handle_amnesia_log,
        }
        vault_routes = {
            "/vault/register": self._handle_vault_register,
            "/vault/checkout":  self._handle_vault_checkout,
            "/vault/checkin":   self._handle_vault_checkin,
            "/vault/revoke":    self._handle_vault_revoke,
        }
        handler = routes.get(self.path)
        vault_handler = vault_routes.get(self.path)
        if handler:
            try:
                body = self._read_json()
            except ValueError as e:
                self._send_error(400, str(e))
                return
            self._safe_call(handler, body)
        elif vault_handler:
            try:
                body = self._read_json()
            except ValueError as e:
                self._send_error(400, str(e))
                return
            self._safe_vault_call(vault_handler, body)
        else:
            self._send_error(404, f"Unknown endpoint: {self.path}")

    def _safe_call(self, handler, body):
        """Call handler under lock, catch all errors without leaking internals."""
        lock: threading.RLock = self.server.brain_lock  # type: ignore[attr-defined]
        try:
            with lock:
                if body is None:
                    handler()
                else:
                    handler(body)
        except ValueError as e:
            # Validation errors → 400 with message (safe, we control the text)
            self._send_error(400, str(e))
        except Exception:
            # Internal errors → generic 500, log full traceback to stderr
            traceback.print_exc(file=sys.stderr)
            self._send_error(500, "Internal server error")

    def _safe_vault_call(self, handler, body):
        """Call vault handler — vault uses its own internal RLock."""
        try:
            if body is None:
                handler()
            else:
                handler(body)
        except ValueError as e:
            self._send_error(400, str(e))
        except Exception:
            traceback.print_exc(file=sys.stderr)
            self._send_error(500, "Internal server error")

    # ── Vault endpoints ────────────────────────────────────────────

    def _handle_vault_status(self):
        vault: FSDKeyVault = self.server.vault  # type: ignore[attr-defined]
        self._send_json(vault.status())

    def _handle_vault_history(self):
        vault: FSDKeyVault = self.server.vault  # type: ignore[attr-defined]
        last_n = 50
        self._send_json({"entries": vault.history(last_n=last_n), "count": last_n})

    def _handle_vault_register(self, body: dict):
        _require(body, "key")
        _require(body, "label")
        _require(body, "registered_by")
        vault: FSDKeyVault = self.server.vault  # type: ignore[attr-defined]
        result = vault.register_key(
            key=body["key"],
            label=body["label"],
            registered_by=body["registered_by"],
            daily_budget_usd=float(body.get("daily_budget_usd", 5.0)),
            monthly_budget_usd=float(body.get("monthly_budget_usd", 50.0)),
        )
        self._send_json(result)

    def _handle_vault_checkout(self, body: dict):
        _require(body, "agent_id")
        _require(body, "task")
        vault: FSDKeyVault = self.server.vault  # type: ignore[attr-defined]
        result = vault.checkout(
            agent_id=body["agent_id"],
            task=body["task"],
            fingerprint=body.get("fingerprint"),
            ttl_seconds=int(body.get("ttl_seconds", 14400)),
            max_budget_usd=float(body.get("max_budget_usd", 1.0)),
        )
        self._send_json(result)

    def _handle_vault_checkin(self, body: dict):
        _require(body, "checkout_token")
        vault: FSDKeyVault = self.server.vault  # type: ignore[attr-defined]
        result = vault.checkin(
            checkout_token=body["checkout_token"],
            tokens_used=int(body.get("tokens_used", 0)),
            cost_usd=float(body.get("cost_usd", 0.0)),
            notes=str(body.get("notes", "")),
        )
        self._send_json(result)

    def _handle_vault_revoke(self, body: dict):
        _require(body, "fingerprint")
        _require(body, "reason")
        _require(body, "revoked_by")
        vault: FSDKeyVault = self.server.vault  # type: ignore[attr-defined]
        result = vault.revoke(
            fingerprint=body["fingerprint"],
            reason=body["reason"],
            revoked_by=body["revoked_by"],
        )
        self._send_json(result)

    # ── Original endpoints (hardened) ──────────────────────────────

    def _handle_status(self):
        brain: DiamondBrain = self.server.brain  # type: ignore[attr-defined]
        digest = brain.digest()
        self._send_json({
            "status": "online",
            "facts": digest.get("total_facts", 0),
            "agents": digest.get("total_agents", 0),
            "temporal_events": digest.get("temporal_events", 0),
            "blob_count": digest.get("blob_count", 0),
            "quarantine_count": digest.get("quarantine_count", 0),
            "memory_dir": str(brain.memory_dir),
        })

    def _handle_learn(self, body: dict):
        _require(body, "topic")
        _require(body, "fact")
        brain: DiamondBrain = self.server.brain  # type: ignore[attr-defined]
        result = brain.learn(
            topic=body["topic"],
            fact=body["fact"],
            confidence=int(body.get("confidence", 90)),
            source=str(body.get("source", "auto")),
            verified=bool(body.get("verified", False)),
        )
        self._send_json(result)

    def _handle_recall(self, body: dict):
        _require(body, "topic")
        brain: DiamondBrain = self.server.brain  # type: ignore[attr-defined]
        max_results = int(body.get("max_results", 15))
        min_confidence = int(body.get("min_confidence", 0))
        fuzzy = bool(body.get("fuzzy", False))
        facts = brain.recall(
            topic=body["topic"],
            max_results=max_results,
            min_confidence=min_confidence,
            fuzzy=fuzzy,
        )
        self._send_json({
            "facts": [f.get("fact", "") for f in facts],
            "details": facts,
        })

    def _handle_cortex_ask(self, body: dict):
        _require(body, "question")
        brain: DiamondBrain = self.server.brain  # type: ignore[attr-defined]
        topics = _optional(body, "topics", list)
        max_context = int(body.get("max_context", 15))
        result = brain.cortex_ask(
            question=body["question"],
            topics=topics,
            max_context=max_context,
        )
        if isinstance(result, dict):
            # Preserve full structured response (answer, sources, confidence, etc.)
            # but guarantee "answer" key exists for simple callers
            if "answer" not in result:
                result["answer"] = str(result)
            self._send_json(result)
        else:
            self._send_json({"answer": str(result)})

    def _handle_blob_store(self, body: dict):
        _require(body, "content_b64")
        brain: DiamondBrain = self.server.brain  # type: ignore[attr-defined]
        content_b64 = body["content_b64"]
        if not isinstance(content_b64, str):
            raise ValueError("'content_b64' must be a base64-encoded string")
        try:
            content = base64.b64decode(content_b64, validate=True)
        except (binascii.Error, ValueError):
            raise ValueError("'content_b64' is not valid base64")
        metadata = body.get("metadata", {})
        if not isinstance(metadata, dict):
            raise ValueError("'metadata' must be a JSON object")
        result = brain.blob_store(content=content, metadata=metadata)
        self._send_json(result)

    def _handle_agent_checkin(self, body: dict):
        _require(body, "id")
        brain: DiamondBrain = self.server.brain  # type: ignore[attr-defined]
        result = brain.agent_checkin(
            agent_id=body["id"],
            role=str(body.get("role", "generic")),
            task=str(body.get("task", "")),
        )
        self._send_json(result)

    def _handle_agent_report(self, body: dict):
        _require(body, "id")
        brain: DiamondBrain = self.server.brain  # type: ignore[attr-defined]
        findings = body.get("findings", body.get("findings_text", ""))
        if isinstance(findings, str):
            findings = [{"text": findings}]
        if not isinstance(findings, list):
            raise ValueError("'findings' must be a list or string")
        result = brain.agent_report(
            agent_id=body["id"],
            findings=findings,
        )
        self._send_json(result)

    def _handle_temporal_add(self, body: dict):
        _require(body, "event")
        _require(body, "start")
        brain: DiamondBrain = self.server.brain  # type: ignore[attr-defined]
        result = brain.temporal_add(
            event_id=body["event"],
            start=body["start"],
            end=body.get("end", ""),
            data=_optional(body, "data", dict),
        )
        self._send_json(result)

    # ── Must-add: Diamond Drill integration ────────────────────────

    def _handle_search(self, body: dict):
        _require(body, "keyword")
        brain: DiamondBrain = self.server.brain  # type: ignore[attr-defined]
        results = brain.search(keyword=body["keyword"])
        self._send_json({"results": results})

    def _handle_hybrid_search(self, body: dict):
        _require(body, "query")
        brain: DiamondBrain = self.server.brain  # type: ignore[attr-defined]
        top_k = int(body.get("top_k", 10))
        results = brain.hybrid_search(query=body["query"], top_k=top_k)
        self._send_json({"results": results})

    def _handle_batch_learn(self, body: dict):
        _require(body, "items", list)
        brain: DiamondBrain = self.server.brain  # type: ignore[attr-defined]
        items = body["items"]
        results = []
        succeeded = 0
        failed = 0
        for item in items:
            if not isinstance(item, dict):
                results.append({"error": "item must be a JSON object"})
                failed += 1
                continue
            if "topic" not in item or "fact" not in item:
                results.append({"error": "item missing 'topic' or 'fact'"})
                failed += 1
                continue
            r = brain.learn(
                topic=item["topic"],
                fact=item["fact"],
                confidence=int(item.get("confidence", 90)),
                source=str(item.get("source", "auto")),
            )
            results.append(r)
            succeeded += 1
        self._send_json({"learned": succeeded, "failed": failed, "total": len(items), "results": results})

    def _handle_graph_auto_index(self, body: dict):
        brain: DiamondBrain = self.server.brain  # type: ignore[attr-defined]
        result = brain.graph_auto_index()
        self._send_json(result)

    def _handle_third_eye_scan(self, body: dict):
        brain: DiamondBrain = self.server.brain  # type: ignore[attr-defined]
        include_types = _optional(body, "include_types", list)
        alerts = brain.third_eye_scan(include_types=include_types)
        self._send_json({"alerts": alerts, "count": len(alerts)})

    def _handle_quarantine_list(self, body: dict):
        brain: DiamondBrain = self.server.brain  # type: ignore[attr-defined]
        status = _optional(body, "status", str)
        batch_id = _optional(body, "batch_id", str)
        entries = brain.quarantine_list(status=status, batch_id=batch_id)
        self._send_json({"entries": entries, "count": len(entries)})

    def _handle_cite(self, body: dict):
        _require(body, "code")
        _require(body, "title")
        _require(body, "text")
        brain: DiamondBrain = self.server.brain  # type: ignore[attr-defined]
        result = brain.cite(
            code=body["code"],
            title=body["title"],
            text=body["text"],
            category=str(body.get("category", "statute")),
            jurisdiction=str(body.get("jurisdiction", "AZ")),
            source=str(body.get("source", "research")),
            severity=str(body.get("severity", "REFERENCE")),
            linked_facts=_optional(body, "linked_facts", list),
        )
        self._send_json(result)

    def _handle_recall_citations(self, body: dict):
        brain: DiamondBrain = self.server.brain  # type: ignore[attr-defined]
        results = brain.recall_citations(
            query=_optional(body, "query", str),
            category=_optional(body, "category", str),
            severity=_optional(body, "severity", str),
            max_results=int(body.get("max_results", 15)),
        )
        self._send_json({"citations": results, "count": len(results)})

    # ── Should-add: full cortex + amnesia ──────────────────────────

    def _handle_cortex_summarize(self, body: dict):
        _require(body, "topic")
        brain: DiamondBrain = self.server.brain  # type: ignore[attr-defined]
        result = brain.cortex_summarize(topic=body["topic"])
        self._send_json(result)

    def _handle_cortex_hypothesize(self, body: dict):
        _require(body, "evidence_facts", list)
        _require(body, "question")
        brain: DiamondBrain = self.server.brain  # type: ignore[attr-defined]
        result = brain.cortex_hypothesize(
            evidence_facts=body["evidence_facts"],
            question=body["question"],
        )
        self._send_json(result)

    def _handle_detect_contradictions(self, body: dict):
        brain: DiamondBrain = self.server.brain  # type: ignore[attr-defined]
        topic = _optional(body, "topic", str)
        threshold = float(body.get("threshold", 0.65))
        results = brain.detect_contradictions(topic=topic, threshold=threshold)
        self._send_json({"contradictions": results, "count": len(results)})

    def _handle_forget(self, body: dict):
        _require(body, "topic")
        _require(body, "fact_pattern")
        _require(body, "reason")
        brain: DiamondBrain = self.server.brain  # type: ignore[attr-defined]
        result = brain.forget(
            topic=body["topic"],
            fact_pattern=body["fact_pattern"],
            reason=body["reason"],
        )
        self._send_json(result)

    def _handle_amnesia_restore(self, body: dict):
        _require(body, "topic")
        _require(body, "fact_pattern")
        brain: DiamondBrain = self.server.brain  # type: ignore[attr-defined]
        result = brain.amnesia_restore(
            topic=body["topic"],
            fact_pattern=body["fact_pattern"],
        )
        self._send_json(result)

    def _handle_amnesia_log(self, body: dict):
        brain: DiamondBrain = self.server.brain  # type: ignore[attr-defined]
        last_n = int(body.get("last_n", 15))
        entries = brain.amnesia_log(last_n=last_n)
        self._send_json({"entries": entries, "count": len(entries)})

    # ── JSON helpers ───────────────────────────────────────────────

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length < 0:
            raise ValueError("Invalid Content-Length (negative)")
        if length > MAX_BODY_BYTES:
            raise ValueError(f"Request body too large ({length} bytes, max {MAX_BODY_BYTES})")
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
        if not isinstance(data, dict):
            raise ValueError("Request body must be a JSON object")
        return data

    def _send_json(self, data, status: int = 200):
        payload = json.dumps(data, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_error(self, status: int, message: str):
        self._send_json({"error": message}, status=status)


# ── Threaded server ────────────────────────────────────────────────

class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    """Concurrent HTTPServer — each request runs in its own thread.

    ThreadingMixIn spawns a thread per request. The RLock on `self.brain_lock`
    serializes actual brain mutations, but I/O (read body, write response) is
    fully concurrent.  `daemon_threads = True` ensures threads don't block
    shutdown.
    """
    allow_reuse_address = True
    daemon_threads = True


def main():
    parser = argparse.ArgumentParser(description="Diamond Brain HTTP server")
    parser.add_argument(
        "--memory-dir",
        default="brain/memory-forensic",
        help="Memory directory for forensic data (default: brain/memory-forensic)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7734,
        help="HTTP port (default: 7734)",
    )
    parser.add_argument(
        "--bind",
        default="127.0.0.1",
        help="Bind address (default: 127.0.0.1, use 0.0.0.0 for network access)",
    )
    args = parser.parse_args()

    memory_dir = Path(args.memory_dir)
    memory_dir.mkdir(parents=True, exist_ok=True)

    brain = DiamondBrain(memory_dir=memory_dir)
    vault = FSDKeyVault(memory_dir=memory_dir)

    server = ThreadedHTTPServer((args.bind, args.port), BrainHandler)
    server.brain = brain           # type: ignore[attr-defined]
    server.brain_lock = threading.RLock()  # type: ignore[attr-defined]
    server.vault = vault           # type: ignore[attr-defined]

    print(f"Diamond Brain server v3.0 on {args.bind}:{args.port}  memory: {memory_dir}")
    print(f"  Endpoints: {8 + 8 + 6} = 22 brain + 6 vault (GET /vault/status|/vault/history, POST /vault/register|checkout|checkin|revoke)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
