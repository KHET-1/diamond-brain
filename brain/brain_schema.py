"""
brain_schema.py — Brain Interoperability Schema Validator v1.0
==============================================================
Validates facts, NICs, and handshake messages against the Brain Schema Spec.
Used by both DiamondBrain and any fork (x9, ParrotMain, etc.) to ensure
two brains can negotiate a sync regardless of version or capability divergence.

Policy summary:
  Unknown fields  → strip + warn (never reject)
  Unknown caps    → ignore (sync intersection only)
  Missing optional→ fill defaults (never reject)
  Missing required→ skip fact with log (never crash)
  Missing NIC     → degraded mode (warn, allow sync)
  Major schema mismatch → compat=False, reject with reason
"""

import re
from datetime import datetime, timezone
from typing import Optional

FACT_SCHEMA_VERSION  = "1.0"
NIC_SPEC_VERSION     = "1.0"
HANDSHAKE_VERSION    = "1.0"

KNOWN_CAPABILITIES = frozenset([
    "facts", "agents", "citations", "graph", "fsrs",
    "blobs", "scrolls", "embeddings", "temporal", "commands",
])

# ── Fact Schema ────────────────────────────────────────────────────────────────

FACT_REQUIRED = {"topic", "fact", "confidence", "source", "verified", "created_at"}
FACT_OPTIONAL = {"updated_at", "times_recalled", "tags", "source_node", "effective_confidence"}
FACT_ALL      = FACT_REQUIRED | FACT_OPTIONAL


def _is_iso8601(val: str) -> bool:
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%dT%H:%M:%S"):
        try:
            datetime.strptime(val.replace("Z", "+00:00") if val.endswith("Z") else val, fmt)
            return True
        except (ValueError, AttributeError):
            continue
    return False


def validate_fact(raw: dict, warn_log: list = None) -> tuple[bool, dict, list]:
    """Validate and clean a single fact against schema v1.0.

    Returns:
        (valid, cleaned_fact, issues)
        valid=True  → cleaned_fact is safe to store/sync
        valid=False → fact should be skipped, issues explains why
    """
    issues = []
    if warn_log is None:
        warn_log = issues

    if not isinstance(raw, dict):
        return False, {}, ["fact is not a dict"]

    cleaned = {}

    # ── Strip unknown fields ──────────────────────────────────────────────────
    unknown = set(raw.keys()) - FACT_ALL
    if unknown:
        warn_log.append(f"stripped unknown fields: {sorted(unknown)}")

    # ── Required fields ───────────────────────────────────────────────────────
    missing = FACT_REQUIRED - set(raw.keys())
    if missing:
        return False, {}, [f"missing required fields: {sorted(missing)}"]

    # topic
    topic = raw["topic"]
    if not isinstance(topic, str) or not (1 <= len(topic) <= 128):
        return False, {}, [f"topic invalid: {repr(topic)[:40]}"]
    cleaned["topic"] = topic.lower().strip()

    # fact
    fact_text = raw["fact"]
    if not isinstance(fact_text, str) or not (1 <= len(fact_text) <= 4096):
        return False, {}, [f"fact text invalid length: {len(fact_text) if isinstance(fact_text,str) else type(fact_text)}"]
    cleaned["fact"] = fact_text

    # confidence
    conf = raw["confidence"]
    if not isinstance(conf, (int, float)) or not (0 <= conf <= 100):
        issues.append(f"confidence {conf} out of range, clamped to [0,100]")
        conf = max(0, min(100, int(conf)))
    cleaned["confidence"] = int(conf)

    # source
    src = raw["source"]
    if not isinstance(src, str) or len(src) < 1:
        issues.append("source empty, defaulting to 'unknown'")
        src = "unknown"
    cleaned["source"] = src[:256]

    # verified
    verified = raw["verified"]
    if not isinstance(verified, bool):
        issues.append(f"verified not bool ({type(verified).__name__}), casting")
        verified = bool(verified)
    cleaned["verified"] = verified

    # created_at
    created = raw["created_at"]
    if not isinstance(created, str) or not _is_iso8601(created):
        issues.append(f"created_at invalid ISO8601: {repr(created)[:30]}, using now")
        created = datetime.now(timezone.utc).isoformat()
    cleaned["created_at"] = created

    # ── Optional fields ───────────────────────────────────────────────────────
    cleaned["updated_at"]     = raw.get("updated_at", cleaned["created_at"])
    cleaned["times_recalled"] = max(0, int(raw.get("times_recalled", 0)))
    cleaned["tags"]           = raw.get("tags", []) if isinstance(raw.get("tags"), list) else []
    cleaned["source_node"]    = str(raw.get("source_node", ""))[:16]

    return True, cleaned, issues


def validate_facts_batch(raws: list, source_label: str = "peer") -> tuple[list, list]:
    """Validate a list of raw facts. Returns (valid_facts, all_issues)."""
    valid, all_issues = [], []
    for i, raw in enumerate(raws):
        ok, cleaned, issues = validate_fact(raw)
        if ok:
            valid.append(cleaned)
        else:
            all_issues.append(f"[{source_label}] fact[{i}] skipped: {issues}")
        if issues:
            all_issues.extend([f"[{source_label}] fact[{i}] warn: {w}" for w in issues])
    return valid, all_issues


# ── NIC Schema ─────────────────────────────────────────────────────────────────

NIC_REQUIRED = {"uuid", "name", "host", "role", "fingerprint", "spec_version"}
NIC_OPTIONAL = {"location", "created"}
VALID_ROLES  = {"primary", "peer", "satellite", "ghost"}


def validate_nic(raw: dict) -> tuple[bool, dict, list]:
    """Validate a Node Identity Card. Returns (valid, cleaned_nic, issues)."""
    issues = []
    if not isinstance(raw, dict):
        return False, {}, ["NIC is not a dict"]

    missing = NIC_REQUIRED - set(raw.keys())
    if missing:
        # Degraded mode — synthesize what we can
        issues.append(f"NIC missing required fields: {sorted(missing)} — degraded mode")
        if "uuid" not in raw:
            return False, {}, ["NIC missing uuid — cannot establish identity"]

    cleaned = {k: raw.get(k, "") for k in NIC_REQUIRED}
    cleaned["location"] = raw.get("location", "unset")
    cleaned["created"]  = raw.get("created", "")

    if cleaned.get("role") not in VALID_ROLES:
        issues.append(f"unknown role '{cleaned['role']}' — defaulting to 'peer'")
        cleaned["role"] = "peer"

    return True, cleaned, issues


def synthesize_nic_from_peer(peer_name: str, peer_ip: str) -> dict:
    """Create a synthetic NIC for a peer that has no NIC. Degraded mode."""
    import uuid as _uuid, hashlib as _hl, socket as _sock
    synthetic_uuid = str(_uuid.uuid5(_uuid.NAMESPACE_DNS, f"{peer_name}:{peer_ip}"))
    fp = _hl.sha256(f"{synthetic_uuid}{peer_name}{peer_ip}".encode()).hexdigest()
    return {
        "uuid":         synthetic_uuid,
        "name":         peer_name or f"unknown@{peer_ip}",
        "host":         peer_ip,
        "role":         "peer",
        "location":     "unset",
        "spec_version": "0.0",       # signals synthetic / unverified
        "fingerprint":  f"sha256:{fp[:16]}",
        "_synthetic":   True,        # flag: not a real NIC from the peer
    }


# ── Handshake Negotiation ───────────────────────────────────────────────────────

def _schema_major(version: str) -> int:
    try:
        return int(str(version).split(".")[0])
    except (ValueError, IndexError):
        return 1


def negotiate_handshake(local_nic: dict, local_caps: list,
                         peer_msg: dict, peer_ip: str = "") -> dict:
    """Process a PAIR_REQUEST from a peer and compute the PAIR_ACK payload.

    Handles all compatibility cases including:
    - x9 being more advanced (extra caps, extra fields)
    - x9 being older (missing NIC, missing caps field)
    - Major schema mismatch (reject)
    - Minor schema mismatch (warn, allow)

    Returns dict ready to be sent as PAIR_ACK.
    """
    issues = []
    degraded = False

    # ── NIC exchange ────────────────────────────────────────────────────────
    # X9 compat: accept display_name (Lenny-FSD) or peer_name (local brains)
    _peer_display = peer_msg.get("display_name") or peer_msg.get("peer_name", "unknown")
    peer_nic_raw = peer_msg.get("node", {})
    if peer_nic_raw:
        nic_ok, peer_nic, nic_issues = validate_nic(peer_nic_raw)
        issues.extend(nic_issues)
        if not nic_ok:
            peer_nic = synthesize_nic_from_peer(_peer_display, peer_ip)
            degraded = True
            issues.append("peer NIC invalid — using synthetic NIC (degraded mode)")
    else:
        # No NIC at all — old brain, X9 (cert-based), or pre-spec fork
        peer_nic = synthesize_nic_from_peer(_peer_display, peer_ip)
        # X9 compat: annotate with peer's raw fingerprint if present (cert SHA-256)
        if peer_msg.get("fingerprint"):
            peer_nic["_peer_raw_fp"] = peer_msg["fingerprint"]
        degraded = True
        issues.append("peer has no NIC — synthetic identity assigned (degraded mode)")

    # ── Schema version check ────────────────────────────────────────────────
    peer_schema  = peer_msg.get("fact_schema", "1.0")
    local_schema = FACT_SCHEMA_VERSION
    local_major  = _schema_major(local_schema)
    peer_major   = _schema_major(peer_schema)

    if peer_major != local_major:
        return {
            "type":          "PAIR_ACK",
            "node":          local_nic,
            "negotiated":    [],
            "compat":        False,
            "reject_reason": f"fact_schema major mismatch: local={local_schema} peer={peer_schema}",
            "peer_nic":      peer_nic,
            "issues":        issues,
        }

    if peer_schema != local_schema:
        issues.append(f"minor schema mismatch local={local_schema} peer={peer_schema} — syncing safely")

    # ── Capability negotiation ──────────────────────────────────────────────
    peer_caps_raw = peer_msg.get("capabilities", [])
    if not peer_caps_raw:
        # Old brain — assume facts only
        peer_caps_raw = ["facts"]
        issues.append("peer sent no capabilities — assuming ['facts'] only")

    local_set = set(local_caps)
    peer_set  = set(peer_caps_raw)
    unknown_peer_caps = peer_set - KNOWN_CAPABILITIES - local_set
    if unknown_peer_caps:
        issues.append(f"peer has unknown capabilities (ignored): {sorted(unknown_peer_caps)}")

    negotiated = sorted(local_set & peer_set)
    if not negotiated:
        negotiated = ["facts"]   # floor — always sync facts if schema matches
        issues.append("no capability intersection — falling back to facts-only sync")

    return {
        "type":           "PAIR_ACK",
        "node":           local_nic,
        "fact_schema":    local_schema,
        "negotiated":     negotiated,
        "compat":         True,
        "degraded":       degraded,
        "reject_reason":  None,
        "peer_nic":       peer_nic,
        "peer_caps":      sorted(peer_set),
        "issues":         issues,
    }


def parse_pair_ack(ack: dict, peer_ip: str = "") -> tuple[bool, dict, list]:
    """Parse a PAIR_ACK we received. Returns (compat, negotiation_result, issues).

    X9 compat: also accepts PAIR_ACCEPT (Lenny-FSD flat format with no compat flag).
    """
    # X9 compat: PAIR_ACCEPT is X9's spelling — flat format, no compat/negotiated keys
    if ack.get("type") == "PAIR_ACCEPT":
        peer_nic = synthesize_nic_from_peer(
            ack.get("display_name", "unknown"), peer_ip)
        if ack.get("fingerprint"):
            peer_nic["_peer_raw_fp"] = ack["fingerprint"]
        return True, {
            "peer_nic":   peer_nic,
            "negotiated": ["facts"],   # X9 minimum capability floor
            "degraded":   True,        # synthetic NIC, no capability negotiation
        }, ["X9 PAIR_ACCEPT — degraded mode (synthetic NIC, facts-only)"]

    issues = list(ack.get("issues", []))
    if not ack.get("compat", False):
        reason = ack.get("reject_reason", "unknown")
        return False, {}, [f"peer rejected sync: {reason}"] + issues

    peer_nic_raw = ack.get("peer_nic") or ack.get("node", {})
    nic_ok, peer_nic, nic_issues = validate_nic(peer_nic_raw)
    issues.extend(nic_issues)
    if not nic_ok:
        peer_nic = synthesize_nic_from_peer(ack.get("peer_name", "unknown"), peer_ip)
        issues.append("ACK NIC invalid — synthetic fallback")

    return True, {
        "peer_nic":   peer_nic,
        "negotiated": ack.get("negotiated", ["facts"]),
        "degraded":   ack.get("degraded", False),
    }, issues
