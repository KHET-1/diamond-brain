"""
FSD Key Vault v0.1.0 — FireStarDiamond API Key Checkout System
==============================================================
Manages Anthropic API keys for registered agents.
Keys are checked out for a specific task, used, then returned.
Every action is logged to a JSONL audit trail and TokenSentinel.

Flow:
  1. Admin registers a key:  POST /vault/register
  2. Agent requests key:     POST /vault/checkout  → gets key + checkout_token
  3. Agent uses key for task (TokenSentinel records usage externally)
  4. Agent returns key:      POST /vault/checkin   → logs tokens/cost used
  5. Sentinel can revoke:    POST /vault/revoke    → blocks all future checkouts

Endpoints added to server.py:
  GET  /vault/status          → all keys + active checkouts (no plaintext keys)
  GET  /vault/history         → full audit log
  POST /vault/register        → register a new key (admin only)
  POST /vault/checkout        → agent checks out a key
  POST /vault/checkin         → agent returns a key + usage data
  POST /vault/revoke          → revoke a key permanently

Security model (localhost-only system):
  - Keys stored base64-encoded in vault JSON (not plaintext in logs)
  - Fingerprint (first 16 chars) used in all logs — never full key
  - Checkout token (UUID) issued per-checkout — agent must present to return key
  - Expired checkouts auto-returned without usage data on next status poll
  - Revoked keys: all in-flight checkouts invalidated immediately
"""

import base64
import json
import os
import threading
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional


VAULT_FILE  = "fsd_key_vault.json"
AUDIT_FILE  = "fsd_key_vault_audit.jsonl"
DEFAULT_TTL = 4 * 3600   # 4 hours in seconds
MAX_CHECKOUT_BUDGET_USD = 10.0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now_dt() -> datetime:
    return datetime.now(timezone.utc)


def _fp(key: str) -> str:
    """First 16 chars of key as fingerprint — safe to log."""
    return key[:16]


def _encode(key: str) -> str:
    """Trivial reversible encoding — keeps key out of plaintext JSON."""
    return base64.b64encode(key.encode()).decode()


def _decode(encoded: str) -> str:
    return base64.b64decode(encoded.encode()).decode()


class FSDKeyVault:
    """
    Thread-safe API key checkout vault.
    Persists to two files in memory_dir:
      fsd_key_vault.json        — registry of keys + active checkouts
      fsd_key_vault_audit.jsonl — append-only audit log of every event
    """

    def __init__(self, memory_dir: Path, token_sentinel=None):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self._vault_path = self.memory_dir / VAULT_FILE
        self._audit_path = self.memory_dir / AUDIT_FILE
        self._lock = threading.RLock()
        self._sentinel = token_sentinel  # optional TokenSentinel reference
        self._data = self._load()
        self._expire_stale()

    # ── Persistence ──────────────────────────────────────────────────────────

    def _load(self) -> dict:
        if self._vault_path.exists():
            try:
                with open(self._vault_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"keys": {}, "checkouts": {}}

    def _save(self):
        """Atomic write. Caller must hold _lock."""
        tmp = self._vault_path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)
        os.replace(str(tmp), str(self._vault_path))

    def _audit(self, event: str, **fields):
        """Append one event to the JSONL audit log."""
        record = {"ts": _now(), "event": event, **fields}
        line = json.dumps(record, default=str) + "\n"
        with open(self._audit_path, "a", encoding="utf-8") as f:
            f.write(line)

    # ── Admin: register key ───────────────────────────────────────────────────

    def register_key(
        self,
        key: str,
        label: str,
        registered_by: str,
        daily_budget_usd: float = 5.0,
        monthly_budget_usd: float = 50.0,
    ) -> dict:
        """
        Register an Anthropic API key with the vault.

        Args:
            key:                 Full sk-ant-... key
            label:               Human name, e.g. "Ryan primary key"
            registered_by:       Who registered it (agent/user name)
            daily_budget_usd:    Max daily spend before sentinel flags
            monthly_budget_usd:  Max monthly spend before sentinel flags

        Returns:
            {"ok": True, "fingerprint": str, "label": str}
        """
        if not key or len(key) < 16:
            raise ValueError("Key too short to be valid")
        fp = _fp(key)
        with self._lock:
            if fp in self._data["keys"]:
                raise ValueError(f"Key fp={fp}... already registered")
            self._data["keys"][fp] = {
                "encoded":            _encode(key),
                "label":              label,
                "fingerprint":        fp,
                "registered_by":      registered_by,
                "registered_at":      _now(),
                "status":             "active",    # active | revoked
                "daily_budget_usd":   daily_budget_usd,
                "monthly_budget_usd": monthly_budget_usd,
                "total_checkouts":    0,
                "total_tokens_used":  0,
                "total_cost_usd":     0.0,
                "last_checkout":      None,
                "revoked_at":         None,
                "revoked_reason":     None,
            }
            self._save()
        self._audit("register", fingerprint=fp, label=label, registered_by=registered_by)
        return {"ok": True, "fingerprint": fp, "label": label}

    # ── Agent: checkout key ───────────────────────────────────────────────────

    def checkout(
        self,
        agent_id: str,
        task: str,
        fingerprint: Optional[str] = None,
        ttl_seconds: int = DEFAULT_TTL,
        max_budget_usd: float = 1.0,
    ) -> dict:
        """
        Check out an API key for a task.

        Args:
            agent_id:       Agent identifier, e.g. "Sage-v2", "lm-studio-local"
            task:           Short task description, e.g. "fsd_legal_doc generation"
            fingerprint:    Request a specific key by fp (optional; uses first active if None)
            ttl_seconds:    How long before checkout auto-expires (default 4h)
            max_budget_usd: Agent's self-declared max spend for this task

        Returns:
            {
                "ok": True,
                "checkout_token": str,   # present to checkin
                "key": str,              # actual API key — ONLY returned here, never logged
                "fingerprint": str,
                "expires_at": str,
                "max_budget_usd": float,
            }
        """
        with self._lock:
            self._expire_stale()

            # Find key to issue
            key_rec = self._find_key(fingerprint)
            if key_rec is None:
                raise ValueError("No active key available in vault")

            fp = key_rec["fingerprint"]

            # Check if already checked out by this agent
            for token, co in self._data["checkouts"].items():
                if co["fingerprint"] == fp and co["agent_id"] == agent_id and co["status"] == "active":
                    raise ValueError(
                        f"Agent '{agent_id}' already has key fp={fp}... checked out "
                        f"(token: {token[:8]}...). Check in first."
                    )

            expires_at = (_now_dt() + timedelta(seconds=ttl_seconds)).isoformat()
            token = str(uuid.uuid4())

            self._data["checkouts"][token] = {
                "checkout_token":  token,
                "fingerprint":     fp,
                "agent_id":        agent_id,
                "task":            task[:200],
                "checked_out_at":  _now(),
                "expires_at":      expires_at,
                "ttl_seconds":     ttl_seconds,
                "max_budget_usd":  min(max_budget_usd, MAX_CHECKOUT_BUDGET_USD),
                "status":          "active",    # active | returned | expired | revoked
                "tokens_used":     0,
                "cost_usd":        0.0,
                "checked_in_at":   None,
            }
            key_rec["total_checkouts"] += 1
            key_rec["last_checkout"] = _now()
            self._save()

        self._audit(
            "checkout",
            fingerprint=fp,
            agent_id=agent_id,
            task=task[:80],
            checkout_token=token[:8] + "...",
            expires_at=expires_at,
            max_budget_usd=max_budget_usd,
        )

        return {
            "ok":             True,
            "checkout_token": token,
            "key":            _decode(key_rec["encoded"]),  # full key returned to agent
            "fingerprint":    fp,
            "expires_at":     expires_at,
            "max_budget_usd": min(max_budget_usd, MAX_CHECKOUT_BUDGET_USD),
        }

    # ── Agent: checkin key ────────────────────────────────────────────────────

    def checkin(
        self,
        checkout_token: str,
        tokens_used: int = 0,
        cost_usd: float = 0.0,
        notes: str = "",
    ) -> dict:
        """
        Return a checked-out key and record usage.

        Args:
            checkout_token:  Token returned by checkout()
            tokens_used:     Total tokens consumed during task
            cost_usd:        Total cost of task (from TokenSentinel or caller)
            notes:           Optional summary of what was done

        Returns:
            {"ok": True, "fingerprint": str, "tokens_used": int, "cost_usd": float}
        """
        with self._lock:
            co = self._data["checkouts"].get(checkout_token)
            if co is None:
                raise ValueError(f"Unknown checkout token: {checkout_token[:8]}...")
            if co["status"] != "active":
                raise ValueError(
                    f"Checkout token already {co['status']} — cannot check in again"
                )

            fp = co["fingerprint"]
            co["status"]        = "returned"
            co["tokens_used"]   = tokens_used
            co["cost_usd"]      = cost_usd
            co["checked_in_at"] = _now()
            co["notes"]         = notes[:500]

            # Update key totals
            key_rec = self._data["keys"].get(fp)
            if key_rec:
                key_rec["total_tokens_used"] += tokens_used
                key_rec["total_cost_usd"]    = round(
                    key_rec.get("total_cost_usd", 0.0) + cost_usd, 8
                )

            self._save()

        self._audit(
            "checkin",
            fingerprint=fp,
            agent_id=co["agent_id"],
            task=co["task"][:80],
            checkout_token=checkout_token[:8] + "...",
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            notes=notes[:200],
        )

        # Record to TokenSentinel if available
        if self._sentinel and tokens_used > 0:
            try:
                self._sentinel.record_call(
                    caller=f"vault/{co['agent_id']}",
                    model="claude-sonnet-4-6",
                    input_tokens=tokens_used,
                    output_tokens=0,
                    tags=["vault-checkout"],
                )
            except Exception:
                pass

        return {
            "ok":          True,
            "fingerprint": fp,
            "tokens_used": tokens_used,
            "cost_usd":    cost_usd,
        }

    def checkin_by_agent(self, agent_id: str, notes: str = "force_release") -> dict:
        """
        Force-release any active checkout held by a given agent_id.
        Used to clean up stale checkouts from crashed runs before re-reserving.
        Returns {"ok": True, "released": int}.
        """
        released = 0
        with self._lock:
            for token, co in list(self._data["checkouts"].items()):
                if co.get("agent_id") == agent_id and co.get("status") == "active":
                    fp = co["fingerprint"]
                    co["status"]        = "returned"
                    co["checked_in_at"] = _now()
                    co["tokens_used"]   = 0
                    co["cost_usd"]      = 0.0
                    co["notes"]         = notes
                    released += 1
            if released:
                self._save()
        self._audit("checkin_by_agent", agent_id=agent_id, released=released)
        return {"ok": True, "agent_id": agent_id, "released": released}

    # ── Admin: revoke key ─────────────────────────────────────────────────────

    def revoke(self, fingerprint: str, reason: str, revoked_by: str) -> dict:
        """
        Permanently revoke a key. All active checkouts are immediately invalidated.

        Args:
            fingerprint:  Key fp to revoke (first 16 chars)
            reason:       Why it's being revoked
            revoked_by:   Who ordered the revocation

        Returns:
            {"ok": True, "fingerprint": str, "invalidated_checkouts": int}
        """
        with self._lock:
            key_rec = self._data["keys"].get(fingerprint)
            if key_rec is None:
                raise ValueError(f"No key with fingerprint: {fingerprint}")
            if key_rec["status"] == "revoked":
                raise ValueError(f"Key fp={fingerprint}... is already revoked")

            key_rec["status"]        = "revoked"
            key_rec["revoked_at"]    = _now()
            key_rec["revoked_reason"] = reason

            # Invalidate all active checkouts for this key
            invalidated = 0
            for co in self._data["checkouts"].values():
                if co["fingerprint"] == fingerprint and co["status"] == "active":
                    co["status"] = "revoked"
                    invalidated += 1

            self._save()

        self._audit(
            "revoke",
            fingerprint=fingerprint,
            reason=reason,
            revoked_by=revoked_by,
            invalidated_checkouts=invalidated,
        )

        return {
            "ok":                    True,
            "fingerprint":           fingerprint,
            "invalidated_checkouts": invalidated,
        }

    # ── Status / history ──────────────────────────────────────────────────────

    def status(self) -> dict:
        """
        Return full vault status — safe to expose over HTTP (no plaintext keys).
        """
        with self._lock:
            self._expire_stale()
            keys = []
            for fp, rec in self._data["keys"].items():
                keys.append({
                    "fingerprint":       fp,
                    "label":             rec["label"],
                    "status":            rec["status"],
                    "registered_by":     rec["registered_by"],
                    "registered_at":     rec["registered_at"],
                    "total_checkouts":   rec["total_checkouts"],
                    "total_tokens_used": rec["total_tokens_used"],
                    "total_cost_usd":    rec["total_cost_usd"],
                    "last_checkout":     rec["last_checkout"],
                    "daily_budget_usd":  rec["daily_budget_usd"],
                    "revoked_at":        rec.get("revoked_at"),
                    "revoked_reason":    rec.get("revoked_reason"),
                })

            active_cos = [
                {k: v for k, v in co.items() if k != "checkout_token"}
                for co in self._data["checkouts"].values()
                if co["status"] == "active"
            ]

        return {
            "keys":             keys,
            "active_checkouts": active_cos,
            "total_keys":       len(keys),
            "active_key_count": sum(1 for k in keys if k["status"] == "active"),
        }

    def history(self, last_n: int = 50) -> list:
        """Return last N audit log entries, newest first."""
        if not self._audit_path.exists():
            return []
        lines = self._audit_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        records = []
        for line in lines:
            try:
                records.append(json.loads(line))
            except Exception:
                pass
        return list(reversed(records))[:last_n]

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _find_key(self, fingerprint: Optional[str]) -> Optional[dict]:
        """Return the key record to use, or None if unavailable."""
        if fingerprint:
            rec = self._data["keys"].get(fingerprint)
            if rec and rec["status"] == "active":
                return rec
            return None
        # First active key
        for rec in self._data["keys"].values():
            if rec["status"] == "active":
                return rec
        return None

    def _expire_stale(self):
        """Mark expired active checkouts as 'expired'. Caller may hold lock."""
        now = _now_dt()
        changed = False
        for co in self._data["checkouts"].values():
            if co["status"] != "active":
                continue
            try:
                exp = datetime.fromisoformat(co["expires_at"])
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=timezone.utc)
                if now > exp:
                    co["status"] = "expired"
                    co["checked_in_at"] = _now()
                    changed = True
                    self._audit(
                        "expired",
                        fingerprint=co["fingerprint"],
                        agent_id=co["agent_id"],
                        task=co["task"][:80],
                    )
            except Exception:
                pass
        if changed:
            self._save()
