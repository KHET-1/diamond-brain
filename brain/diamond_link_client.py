#!/usr/bin/env python3
"""
diamond_link_client.py — Three-Lattice Protocol Enforcer

A thin client wrapper that NovaPrime (or any peer brain) runs instead of
calling DiamondBrain directly. Enforces the Three-Lattice protocol at the
boundary — before facts touch the local brain.

WHY THIS EXISTS:
  Sending NovaPrime a spec and trusting them to implement it correctly is
  insufficient. If their learn() doesn't handle fact_class correctly, all
  inbound Class A evidence facts silently downgrade to Class B and get
  merged. This shim enforces the protocol regardless of the peer's internal
  implementation.

USAGE:
  from brain.diamond_link_client import DiamondLinkClient
  client = DiamondLinkClient()

  # Instead of brain.learn(...) directly:
  client.receive_fact(topic, fact, confidence, fact_class, source, verified)

  # Instead of brain.coord_claim() directly:
  client.receive_claim(claim_dict)

  # Check what's pending human resolution:
  client.pending_conflicts()
  client.pending_claims()
"""

import json
import hashlib
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Allow running from any location
sys.path.insert(0, str(Path(__file__).parent.parent))
from brain.diamond_brain import DiamondBrain


# ── Constants ─────────────────────────────────────────────────────────────────

VALID_CLASSES   = {"A", "B", "C"}
MAX_FACT_LEN    = 8000   # chars — reject absurdly large facts
MAX_TOPIC_LEN   = 200
MIN_CONFIDENCE  = 0
MAX_CONFIDENCE  = 100


# ── Validation ────────────────────────────────────────────────────────────────

class ProtocolViolation(Exception):
    """Raised when an incoming fact violates Three-Lattice protocol."""
    pass


def _validate_fact(topic: str, fact: str, confidence: int,
                   fact_class: str, source: str) -> None:
    """Strict inbound validation. Raises ProtocolViolation on any issue."""
    if not topic or not isinstance(topic, str):
        raise ProtocolViolation(f"Invalid topic: {topic!r}")
    if len(topic) > MAX_TOPIC_LEN:
        raise ProtocolViolation(f"Topic too long: {len(topic)} chars")
    if not fact or not isinstance(fact, str):
        raise ProtocolViolation(f"Invalid fact content")
    if len(fact) > MAX_FACT_LEN:
        raise ProtocolViolation(f"Fact too long: {len(fact)} chars")
    if not isinstance(confidence, (int, float)) or not (MIN_CONFIDENCE <= confidence <= MAX_CONFIDENCE):
        raise ProtocolViolation(f"Confidence out of range: {confidence}")
    fc = str(fact_class).upper() if fact_class else "B"
    if fc not in VALID_CLASSES:
        raise ProtocolViolation(f"Invalid fact_class: {fact_class!r}. Must be A, B, or C.")


def _validate_claim(claim: dict) -> None:
    """Validate an incoming coordination claim dict."""
    required = {"task_id", "node_id", "description"}
    missing = required - set(claim.keys())
    if missing:
        raise ProtocolViolation(f"Claim missing required fields: {missing}")
    ttl = claim.get("ttl_hours", 4.0)
    if not isinstance(ttl, (int, float)) or ttl <= 0 or ttl > 168:
        raise ProtocolViolation(f"Invalid TTL: {ttl}. Must be 0–168 hours.")


# ── Client ────────────────────────────────────────────────────────────────────

class DiamondLinkClient:
    """
    Three-Lattice protocol enforcer.

    Wraps DiamondBrain and validates all inbound facts before they touch
    the local knowledge store. Designed to be the only write path for
    facts received from peer brains via Diamond Link sync.
    """

    def __init__(self, memory_dir: str | None = None, strict: bool = True):
        """
        Args:
            memory_dir: Path to brain memory dir. Defaults to DiamondBrain default.
            strict:     If True (default), raise ProtocolViolation on bad input.
                        If False, log and skip bad facts instead of raising.
        """
        self.brain  = DiamondBrain(memory_dir=memory_dir)
        self.strict = strict
        self._log: list[dict] = []   # in-memory audit log for this session

    # ── Fact ingestion ────────────────────────────────────────────────────────

    def receive_fact(self,
                     topic: str,
                     fact: str,
                     confidence: int = 90,
                     fact_class: str = "B",
                     source: str = "link",
                     verified: bool = False) -> dict | None:
        """
        Validate and store an incoming fact from a peer brain.

        Class A facts are NEVER silently overwritten — conflicts are logged
        and returned to the caller for human resolution.

        Returns the stored fact dict, or None if validation failed (non-strict).
        Raises ProtocolViolation in strict mode.
        """
        fact_class = str(fact_class).upper() if fact_class else "B"

        # Validate
        try:
            _validate_fact(topic, fact, confidence, fact_class, source)
        except ProtocolViolation as e:
            self._audit("REJECT", topic, fact_class, str(e))
            if self.strict:
                raise
            return None

        # Store via brain — protocol-aware learn()
        result = self.brain.learn(
            topic=topic,
            fact=fact,
            confidence=int(confidence),
            source=source,
            verified=verified,
            fact_class=fact_class,
        )
        self._audit("ACCEPT", topic, fact_class,
                    f"confidence={confidence} verified={verified}")

        # Surface any new conflicts immediately
        new_conflicts = self.brain.coord_conflicts(resolved=False)
        if new_conflicts:
            self._audit("CONFLICT", topic, fact_class,
                        f"{len(new_conflicts)} open conflict(s)")

        return result

    def receive_snapshot(self, snapshot: dict) -> dict:
        """
        Apply a full Diamond Link sync snapshot.

        Delegates to brain.crdt_merge_snapshot() which now enforces
        Three-Lattice class rules internally. Returns merge stats.
        """
        if not isinstance(snapshot, dict):
            raise ProtocolViolation("Snapshot must be a dict")

        facts = snapshot.get("facts", [])
        # Pre-validate all facts before any are applied
        if self.strict:
            for i, f in enumerate(facts):
                try:
                    _validate_fact(
                        f.get("topic", ""),
                        f.get("fact", ""),
                        f.get("confidence", 0),
                        f.get("fact_class", "B"),
                        f.get("source", "link"),
                    )
                except ProtocolViolation as e:
                    raise ProtocolViolation(
                        f"Snapshot fact[{i}] invalid: {e}"
                    ) from e

        stats = self.brain.crdt_merge_snapshot(snapshot)
        self._audit("SNAPSHOT", "multi", "mixed",
                    f"added={stats['added']} merged={stats['merged']} "
                    f"conflicts={stats.get('conflicts', 0)}")
        return stats

    # ── Coordination ──────────────────────────────────────────────────────────

    def receive_claim(self, claim: dict) -> dict | None:
        """
        Accept and validate an incoming coordination claim from a peer.

        Returns the merged result or None on validation failure.
        """
        try:
            _validate_claim(claim)
        except ProtocolViolation as e:
            self._audit("REJECT-CLAIM", claim.get("task_id", "?"), "C", str(e))
            if self.strict:
                raise
            return None

        result = self.brain.coord_merge_remote([claim], claim.get("node_id", "unknown"))
        self._audit("CLAIM", claim["task_id"], "C",
                    f"node={claim['node_id']} ttl={claim.get('ttl_hours')}h")
        return result

    # ── Status & audit ────────────────────────────────────────────────────────

    def pending_conflicts(self) -> list[dict]:
        """Return all open Class A conflicts requiring human resolution."""
        return self.brain.coord_conflicts(resolved=False)

    def pending_claims(self, status: str = "ACTIVE") -> list[dict]:
        """Return active coordination claims."""
        return self.brain.coord_list_claims(status=status)

    def resolve_conflict(self, conflict_id: str, winner_fact_id: str,
                         resolved_by: str) -> bool:
        """Mark a Class A conflict resolved. Both facts remain stored."""
        ok = self.brain.coord_resolve(conflict_id, winner_fact_id, resolved_by)
        if ok:
            self._audit("RESOLVE", conflict_id, "A",
                        f"winner={winner_fact_id} by={resolved_by}")
        return ok

    def session_audit(self) -> list[dict]:
        """Return in-memory audit log for this session."""
        return list(self._log)

    def status(self) -> dict:
        """Return combined brain + coordination status."""
        coord = self.brain.coord_status()
        conflicts = self.pending_conflicts()
        return {
            "brain_facts": len(self.brain._load(self.brain._facts_path)),
            "coord": coord,
            "open_conflicts": len(conflicts),
            "conflicts": conflicts,
            "session_provisional": self.brain._session_provisional,
            "session_audit_entries": len(self._log),
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _audit(self, action: str, topic: str, fact_class: str, detail: str) -> None:
        self._log.append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "topic": topic,
            "fact_class": fact_class,
            "detail": detail,
        })


# ── CLI smoke test ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import tempfile, shutil
    DiamondBrain._embed = lambda self, t: None  # skip LM Studio in test

    print("DiamondLinkClient — Three-Lattice Protocol Enforcer")
    print("=" * 55)

    with tempfile.TemporaryDirectory() as tmpdir:
        client = DiamondLinkClient(memory_dir=tmpdir, strict=True)

        # Accept a valid Class B fact
        f = client.receive_fact("analysis", "400-402GB zone carve complete — 7 artifacts", 88, "B")
        print(f"[B] accepted: {f['topic']} conf={f['confidence']}")

        # Accept a Class A evidence fact
        f = client.receive_fact("ipad-signin", "iPad signed into tanzia2.0@gmail.com Nov 23 2025", 95, "A", verified=True)
        print(f"[A] accepted: {f['topic']} class={f['fact_class']}")

        # Try to inject a conflicting Class A — should accept + log conflict
        f2 = client.receive_fact("ipad-signin", "iPad signed into livesanuk@gmail.com Nov 23 2025", 85, "A")
        print(f"[A] conflict accepted: {f2['topic']} — conflict logged")

        # Try to inject garbage fact_class — should raise
        try:
            client.receive_fact("test", "bad class", 80, "X")
            print("ERROR: should have raised")
        except Exception as e:
            print(f"[REJECT] bad fact_class caught: {e}")

        # Try to inject oversized fact
        try:
            client.receive_fact("test", "x" * 9000, 80, "B")
            print("ERROR: should have raised")
        except Exception as e:
            print(f"[REJECT] oversized fact caught: {e}")

        # Status
        s = client.status()
        print(f"\nStatus: facts={s['brain_facts']} open_conflicts={s['open_conflicts']}")
        print(f"Audit log: {s['session_audit_entries']} entries")
        print(f"Conflicts: {[c['conflict_id'] for c in s['conflicts']]}")

    print("\nOK — client shim operational")
