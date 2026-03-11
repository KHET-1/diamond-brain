"""
================================================================================
  X9 ↔ ParrotMain Compatibility Test Suite
================================================================================
  Tests interoperability between DiamondBrain (ParrotMain) and a simulated
  x9 fork — which may be more advanced, older, or structurally different.

  Scenarios covered:
    1. x9 has NIC + same schema          → full sync, all caps negotiated
    2. x9 has NIC + minor schema ahead   → warn, sync safely
    3. x9 has NO NIC (old version)       → degraded mode, facts still sync
    4. x9 is way more advanced           → extra caps ignored, intersection synced
    5. x9 sends facts with extra fields  → stripped, core synced
    6. x9 has major schema mismatch      → rejected, no sync, clean error
    7. x9 sends malformed facts          → bad facts skipped, good facts pass
    8. x9 has no capabilities field      → assumed ["facts"], still works
    9. Two-instance local sync test      → real TCP, real DiamondBrain instances

  Run:
    python -m pytest tests/test_x9_compat.py -v
    python -m unittest tests.test_x9_compat -v
================================================================================
"""

import json
import os
import shutil
import socket
import tempfile
import threading
import time
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from brain.brain_schema import (
    validate_fact, validate_facts_batch, validate_nic,
    negotiate_handshake, parse_pair_ack, synthesize_nic_from_peer,
    FACT_SCHEMA_VERSION,
)
from brain.diamond_brain import DiamondBrain


# ─── Fixtures ────────────────────────────────────────────────────────────────

def make_valid_fact(**overrides) -> dict:
    """Minimal valid fact matching schema v1.0."""
    base = {
        "topic":      "test-topic",
        "fact":       "A perfectly valid test fact",
        "confidence": 85,
        "source":     "unit-test",
        "verified":   True,
        "created_at": "2026-03-08T12:00:00Z",
    }
    base.update(overrides)
    return base


def make_parrot_nic() -> dict:
    """Simulate ParrotMain's NIC."""
    return {
        "uuid":         "5ee0a7de-81df-497b-b6b4-593d716ad0d9",
        "name":         "ParrotMain",
        "host":         "parrot",
        "role":         "primary",
        "location":     "home-lab",
        "spec_version": "1.0",
        "fingerprint":  "sha256:0a11433d",
    }


def make_x9_nic() -> dict:
    """Simulate x9's NIC (Windows, Tanzia's machine — unknown version)."""
    return {
        "uuid":         "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "name":         "X9-Diamond",
        "host":         "TANZIAS-PC",
        "role":         "peer",
        "location":     "tanzia-desk",
        "spec_version": "1.0",
        "fingerprint":  "sha256:deadbeef1234abcd",
    }


def make_x9_pair_request(schema="1.0", caps=None, include_nic=True) -> dict:
    """Build a PAIR_REQUEST as x9 would send it."""
    req = {
        "type":          "PAIR_REQUEST",
        "peer_name":     "X9-Diamond",
        "fact_schema":   schema,
        "brain_version": "x9-2.1.0",      # x9 announces its own version
        "capabilities":  caps if caps is not None else [
            "facts", "agents", "citations", "graph", "fsrs",
            "blobs", "scrolls", "embeddings", "temporal",
            "neural_mesh",      # x9-only cap we don't know about
            "holonic_index",    # x9-only cap we don't know about
            "quantum_recall",   # x9-only cap we don't know about
        ],
    }
    if include_nic:
        req["node"] = make_x9_nic()
    return req


LOCAL_CAPS = ["facts", "agents", "citations", "graph", "fsrs", "blobs", "scrolls"]


# ──────────────────────────────────────────────────────────────────────────────
# TIER 1: Fact Schema Validation
# ──────────────────────────────────────────────────────────────────────────────

class TestFactSchemaValidation(unittest.TestCase):

    def test_valid_fact_passes(self):
        ok, cleaned, issues = validate_fact(make_valid_fact())
        self.assertTrue(ok)
        self.assertEqual(cleaned["topic"], "test-topic")
        self.assertEqual(cleaned["confidence"], 85)

    def test_missing_required_field_rejects(self):
        raw = make_valid_fact()
        del raw["fact"]
        ok, _, issues = validate_fact(raw)
        self.assertFalse(ok)
        self.assertTrue(any("missing required" in i for i in issues))

    def test_unknown_fields_stripped(self):
        """x9 extra fields must be stripped, fact still valid."""
        raw = make_valid_fact()
        raw["neural_weight"]    = 0.987     # x9-only field
        raw["holonic_cluster"]  = "tier-3"  # x9-only field
        raw["quantum_state"]    = [1, 0, 1] # x9-only field
        ok, cleaned, issues = validate_fact(raw)
        self.assertTrue(ok)
        self.assertNotIn("neural_weight",   cleaned)
        self.assertNotIn("holonic_cluster",  cleaned)
        self.assertNotIn("quantum_state",    cleaned)
        self.assertTrue(any("stripped" in i for i in issues))

    def test_confidence_out_of_range_clamped(self):
        ok, cleaned, issues = validate_fact(make_valid_fact(confidence=150))
        self.assertTrue(ok)
        self.assertEqual(cleaned["confidence"], 100)
        self.assertTrue(any("range" in i or "clamp" in i.lower() for i in issues))

    def test_invalid_iso8601_replaced_with_now(self):
        ok, cleaned, issues = validate_fact(make_valid_fact(created_at="not-a-date"))
        self.assertTrue(ok)
        self.assertIn("T", cleaned["created_at"])  # replaced with valid ISO

    def test_optional_fields_filled_with_defaults(self):
        ok, cleaned, _ = validate_fact(make_valid_fact())
        self.assertEqual(cleaned["times_recalled"], 0)
        self.assertEqual(cleaned["tags"], [])
        self.assertEqual(cleaned["source_node"], "")

    def test_source_node_preserved_from_x9(self):
        """x9 source_node fingerprint must be preserved for provenance."""
        ok, cleaned, _ = validate_fact(make_valid_fact(source_node="deadbeef"))
        self.assertTrue(ok)
        self.assertEqual(cleaned["source_node"], "deadbeef")

    def test_empty_fact_text_rejects(self):
        ok, _, issues = validate_fact(make_valid_fact(fact=""))
        self.assertFalse(ok)

    def test_non_dict_fact_rejects(self):
        ok, _, issues = validate_fact("just a string")
        self.assertFalse(ok)

    def test_batch_validation_skips_bad_keeps_good(self):
        """A batch with 1 bad fact and 2 good facts → 2 valid, 1 skipped."""
        raws = [
            make_valid_fact(fact="Good fact 1"),
            {"topic": "missing-fields"},        # bad — missing required
            make_valid_fact(fact="Good fact 2"),
        ]
        valid, issues = validate_facts_batch(raws, source_label="x9")
        self.assertEqual(len(valid), 2)
        self.assertTrue(any("skipped" in i for i in issues))

    def test_batch_x9_advanced_facts_stripped(self):
        """x9 batch with 3 extra fields each — all valid after strip."""
        raws = [
            {**make_valid_fact(fact=f"Fact {i}"),
             "neural_weight": i * 0.1,
             "holonic_tier": "alpha",
             "x9_internal_id": f"x9-{i:04d}"}
            for i in range(5)
        ]
        valid, issues = validate_facts_batch(raws, source_label="x9-advanced")
        self.assertEqual(len(valid), 5)
        for f in valid:
            self.assertNotIn("neural_weight", f)


# ──────────────────────────────────────────────────────────────────────────────
# TIER 2: NIC Validation
# ──────────────────────────────────────────────────────────────────────────────

class TestNICValidation(unittest.TestCase):

    def test_valid_nic_passes(self):
        ok, cleaned, issues = validate_nic(make_x9_nic())
        self.assertTrue(ok)
        self.assertEqual(cleaned["name"], "X9-Diamond")

    def test_parrot_nic_passes(self):
        ok, cleaned, _ = validate_nic(make_parrot_nic())
        self.assertTrue(ok)
        self.assertEqual(cleaned["name"], "ParrotMain")

    def test_missing_uuid_hard_rejects(self):
        nic = make_x9_nic()
        del nic["uuid"]
        ok, _, issues = validate_nic(nic)
        self.assertFalse(ok)
        self.assertTrue(any("uuid" in i for i in issues))

    def test_unknown_role_defaults_to_peer(self):
        nic = make_x9_nic()
        nic["role"] = "overlord"   # x9 invented a new role
        ok, cleaned, issues = validate_nic(nic)
        self.assertTrue(ok)
        self.assertEqual(cleaned["role"], "peer")

    def test_synthetic_nic_created_for_no_nic_peer(self):
        """If x9 (old version) sends no NIC, we synthesize one."""
        synthetic = synthesize_nic_from_peer("X9-Diamond", "192.168.1.100")
        self.assertIn("uuid", synthetic)
        self.assertTrue(synthetic.get("_synthetic"))
        self.assertEqual(synthetic["role"], "peer")


# ──────────────────────────────────────────────────────────────────────────────
# TIER 3: Handshake Negotiation
# ──────────────────────────────────────────────────────────────────────────────

class TestHandshakeNegotiation(unittest.TestCase):

    def test_x9_full_compat(self):
        """x9 has NIC + same schema → compat=True, full negotiation."""
        ack = negotiate_handshake(
            make_parrot_nic(), LOCAL_CAPS,
            make_x9_pair_request(), peer_ip="192.168.1.100"
        )
        self.assertTrue(ack["compat"])
        self.assertIn("facts", ack["negotiated"])
        self.assertEqual(ack["reject_reason"], None)

    def test_x9_extra_caps_ignored(self):
        """x9 has neural_mesh, holonic_index, quantum_recall — we ignore them."""
        ack = negotiate_handshake(
            make_parrot_nic(), LOCAL_CAPS,
            make_x9_pair_request(), peer_ip="192.168.1.100"
        )
        self.assertTrue(ack["compat"])
        for exotic_cap in ("neural_mesh", "holonic_index", "quantum_recall"):
            self.assertNotIn(exotic_cap, ack["negotiated"])
        # But our shared caps ARE in negotiated
        for shared_cap in ("facts", "agents", "graph"):
            self.assertIn(shared_cap, ack["negotiated"])
        # Issues should mention unknown caps
        self.assertTrue(any("unknown capabilities" in i for i in ack["issues"]))

    def test_x9_minor_schema_ahead(self):
        """x9 is on schema 1.3, we're on 1.0 → warn but compat=True."""
        ack = negotiate_handshake(
            make_parrot_nic(), LOCAL_CAPS,
            make_x9_pair_request(schema="1.3"), peer_ip="192.168.1.100"
        )
        self.assertTrue(ack["compat"])
        self.assertTrue(any("minor schema" in i or "mismatch" in i for i in ack["issues"]))

    def test_x9_major_schema_mismatch_rejected(self):
        """x9 is on schema 2.0 → reject, no sync."""
        ack = negotiate_handshake(
            make_parrot_nic(), LOCAL_CAPS,
            make_x9_pair_request(schema="2.0"), peer_ip="192.168.1.100"
        )
        self.assertFalse(ack["compat"])
        self.assertIn("major mismatch", ack["reject_reason"])
        self.assertEqual(ack["negotiated"], [])

    def test_x9_no_nic_degraded_mode(self):
        """x9 sends no NIC (old version) → degraded=True, still compat."""
        ack = negotiate_handshake(
            make_parrot_nic(), LOCAL_CAPS,
            make_x9_pair_request(include_nic=False), peer_ip="192.168.1.100"
        )
        self.assertTrue(ack["compat"])
        self.assertTrue(ack["degraded"])
        self.assertTrue(ack["peer_nic"].get("_synthetic"))
        self.assertTrue(any("no NIC" in i or "degraded" in i for i in ack["issues"]))

    def test_x9_no_capabilities_field(self):
        """x9 (very old) sends no capabilities → assume facts only, still works."""
        req = make_x9_pair_request()
        del req["capabilities"]
        ack = negotiate_handshake(
            make_parrot_nic(), LOCAL_CAPS, req, peer_ip="192.168.1.100"
        )
        self.assertTrue(ack["compat"])
        self.assertIn("facts", ack["negotiated"])
        self.assertTrue(any("no capabilities" in i for i in ack["issues"]))

    def test_x9_only_unknown_caps(self):
        """x9 only has exotic caps we don't know — floor to facts."""
        req = make_x9_pair_request(caps=["neural_mesh", "quantum_recall"])
        ack = negotiate_handshake(
            make_parrot_nic(), LOCAL_CAPS, req, peer_ip="192.168.1.100"
        )
        self.assertTrue(ack["compat"])
        # Falls back to floor
        self.assertIn("facts", ack["negotiated"])

    def test_parse_pair_ack_success(self):
        """We send PAIR_REQ, x9 sends back PAIR_ACK — we parse it correctly."""
        ack_from_x9 = {
            "type":       "PAIR_ACK",
            "node":       make_x9_nic(),
            "fact_schema":"1.0",
            "negotiated": ["facts", "agents", "graph"],
            "compat":     True,
            "degraded":   False,
            "reject_reason": None,
            "issues":     [],
        }
        ok, result, issues = parse_pair_ack(ack_from_x9, peer_ip="192.168.1.100")
        self.assertTrue(ok)
        self.assertIn("facts", result["negotiated"])
        self.assertEqual(result["peer_nic"]["name"], "X9-Diamond")

    def test_parse_pair_ack_rejected(self):
        """x9 sends PAIR_ACK with compat=False — we handle it cleanly."""
        ack_from_x9 = {
            "type":         "PAIR_ACK",
            "compat":       False,
            "negotiated":   [],
            "reject_reason": "fact_schema major mismatch: local=2.0 peer=1.0",
        }
        ok, result, issues = parse_pair_ack(ack_from_x9)
        self.assertFalse(ok)
        self.assertTrue(any("rejected" in i for i in issues))


# ──────────────────────────────────────────────────────────────────────────────
# TIER 4: Full DiamondBrain Integration — Two Local Instances
# ──────────────────────────────────────────────────────────────────────────────

class TestTwoInstanceLocalSync(unittest.TestCase):
    """
    Spins up two real DiamondBrain instances on different ports.
    ParrotMain (server) ↔ X9 simulation (client).
    """

    def setUp(self):
        self.dir_a = tempfile.mkdtemp(prefix="brain_parrot_")
        self.dir_b = tempfile.mkdtemp(prefix="brain_x9_")
        self.brain_a = DiamondBrain(memory_dir=self.dir_a)  # ParrotMain
        self.brain_b = DiamondBrain(memory_dir=self.dir_b)  # X9 simulation
        self.brain_a.set_node_name("ParrotMain-Test", role="primary", location="test")
        self.brain_b.set_node_name("X9-Test", role="peer", location="test")

    def tearDown(self):
        shutil.rmtree(self.dir_a, ignore_errors=True)
        shutil.rmtree(self.dir_b, ignore_errors=True)

    def _find_free_port(self) -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

    def test_nics_are_unique(self):
        """Two instances must have different UUIDs."""
        nic_a = self.brain_a.node_id()
        nic_b = self.brain_b.node_id()
        self.assertNotEqual(nic_a["uuid"], nic_b["uuid"])
        self.assertEqual(nic_a["name"], "ParrotMain-Test")
        self.assertEqual(nic_b["name"], "X9-Test")

    def test_whoami_returns_string(self):
        result_a = self.brain_a.whoami()
        result_b = self.brain_b.whoami()
        self.assertIn("ParrotMain-Test", result_a)
        self.assertIn("X9-Test", result_b)

    def test_diamond_link_status_has_local_nic(self):
        """diamond_link_status must always return local NIC."""
        status = self.brain_a.diamond_link_status()
        self.assertIn("local", status)
        self.assertEqual(status["local"]["name"], "ParrotMain-Test")
        self.assertFalse(status["connected"])

    def test_two_instances_learn_different_facts(self):
        self.brain_a.learn("parrot-topic", "Fact only ParrotMain knows", confidence=90)
        self.brain_b.learn("x9-topic",    "Fact only X9 knows",         confidence=95)

        parrot_facts = self.brain_a.recall("parrot-topic")
        x9_facts     = self.brain_b.recall("x9-topic")
        self.assertEqual(len(parrot_facts), 1)
        self.assertEqual(len(x9_facts),     1)

        # Facts don't cross-contaminate before sync
        self.assertEqual(self.brain_a.recall("x9-topic"),    [])
        self.assertEqual(self.brain_b.recall("parrot-topic"), [])

    def test_local_tcp_sync(self):
        """Real TCP sync: ParrotMain serves, X9 connects and syncs facts."""
        port = self._find_free_port()

        # Seed facts on both sides
        self.brain_a.learn("shared-topic", "ParrotMain fact about AI",   confidence=88)
        self.brain_b.learn("shared-topic", "X9 fact about neural mesh",  confidence=92)

        # Server thread (ParrotMain)
        server_errors = []
        def serve():
            try:
                self.brain_a.link_serve(port=port, bind_addr="127.0.0.1")
            except Exception as e:
                server_errors.append(str(e))

        server_t = threading.Thread(target=serve, daemon=True)
        server_t.start()
        time.sleep(0.3)

        # Client (X9) connects and syncs
        self.brain_b.link_init("X9-Test")
        synced = self.brain_b.link_pair_connect(
            remote_ip="127.0.0.1",
            port=port,
            timeout=5
        )

        # Give sync time to complete
        time.sleep(0.5)
        self.assertTrue(synced, f"Sync failed. Server errors: {server_errors}")


# ──────────────────────────────────────────────────────────────────────────────
# TIER 5: Schema Spec Compliance
# ──────────────────────────────────────────────────────────────────────────────

class TestSchemaSpecCompliance(unittest.TestCase):
    """Verifies that DiamondBrain's actual output complies with the spec."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="brain_spec_")
        self.brain  = DiamondBrain(memory_dir=self.tmpdir)
        self.brain.set_node_name("SpecTest", role="primary", location="test")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_learned_fact_passes_schema_validator(self):
        """Facts written by DiamondBrain must pass our own validator."""
        entry = self.brain.learn("spec-topic", "A compliant fact", confidence=80,
                                 source="spec-test", verified=True)
        ok, cleaned, issues = validate_fact(entry)
        # Filter out "stripped" warnings — those are fine
        hard_issues = [i for i in issues if "stripped" not in i and "warn" not in i.lower()]
        self.assertTrue(ok, f"DiamondBrain fact failed schema: {issues}")

    def test_node_id_passes_nic_validator(self):
        """NIC written by DiamondBrain must pass our validator."""
        nic = self.brain.node_id()
        ok, cleaned, issues = validate_nic(nic)
        self.assertTrue(ok, f"DiamondBrain NIC failed schema: {issues}")

    def test_node_id_has_all_required_fields(self):
        nic = self.brain.node_id()
        required = {"uuid", "name", "host", "role", "fingerprint", "spec_version"}
        for field in required:
            self.assertIn(field, nic, f"NIC missing required field: {field}")

    def test_node_id_uuid_is_stable(self):
        """UUID must never change between loads."""
        uuid1 = self.brain.node_id()["uuid"]
        brain2 = DiamondBrain(memory_dir=self.tmpdir)
        uuid2  = brain2.node_id()["uuid"]
        self.assertEqual(uuid1, uuid2, "UUID changed on reload — spec violation")

    def test_negotiate_own_handshake(self):
        """Brain can negotiate a handshake with itself — useful for self-test."""
        local_nic  = self.brain.node_id()
        local_caps = ["facts", "agents", "citations"]
        fake_peer_req = {
            "type":         "PAIR_REQUEST",
            "node":         local_nic,   # same NIC (self-sync test)
            "fact_schema":  FACT_SCHEMA_VERSION,
            "capabilities": local_caps,
        }
        ack = negotiate_handshake(local_nic, local_caps, fake_peer_req)
        self.assertTrue(ack["compat"])
        self.assertIn("facts", ack["negotiated"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
