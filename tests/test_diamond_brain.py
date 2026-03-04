"""
================================================================================
  DIAMOND BRAIN — Full Test Suite
================================================================================
  Tests all 116 public methods across 31 feature tiers.
  Zero external dependencies. Uses only unittest (stdlib).

  Run:  python -m pytest tests/ -v
        python -m unittest tests.test_diamond_brain -v
        python tests/test_diamond_brain.py
================================================================================
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

# Import from source
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brain.diamond_brain import DiamondBrain, _decayed_confidence, _similarity, _now_iso


class TestDiamondBrainBase(unittest.TestCase):
    """Base class with temp directory setup/teardown."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="diamond_test_")
        self.brain = DiamondBrain(memory_dir=self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)


# ======================================================================
# TIER 1: Core Knowledge (learn, recall, search, advanced_recall)
# ======================================================================
class TestCoreKnowledge(TestDiamondBrainBase):

    def test_learn_creates_fact(self):
        entry = self.brain.learn("test-topic", "A test fact", confidence=85)
        self.assertEqual(entry["topic"], "test-topic")
        self.assertEqual(entry["confidence"], 85)
        self.assertIn("created_at", entry)

    def test_learn_dedup_similar(self):
        self.brain.learn("t", "The quick brown fox jumps over the lazy dog", confidence=80)
        entry = self.brain.learn("t", "The quick brown fox jumps over a lazy dog", confidence=90)
        # Should update, not duplicate
        facts = self.brain._load(self.brain._facts_path)
        same_topic = [f for f in facts if f["topic"] == "t"]
        self.assertEqual(len(same_topic), 1)
        self.assertEqual(same_topic[0]["confidence"], 90)

    def test_learn_no_dedup_different_topics(self):
        self.brain.learn("a", "Identical fact text", confidence=80)
        self.brain.learn("b", "Identical fact text", confidence=80)
        facts = self.brain._load(self.brain._facts_path)
        self.assertEqual(len(facts), 2)

    def test_recall_exact(self):
        self.brain.learn("forensics", "Autopsy is a GUI forensic tool", confidence=95)
        results = self.brain.recall("forensics")
        self.assertEqual(len(results), 1)
        self.assertIn("effective_confidence", results[0])

    def test_recall_fuzzy(self):
        self.brain.learn("sql-injection", "SQL injection is dangerous", confidence=90)
        results = self.brain.recall("sql_injection", fuzzy=True)
        self.assertTrue(len(results) >= 1)

    def test_recall_max_results(self):
        for i in range(20):
            self.brain.learn("bulk", f"Completely unique fact entry number {i} with distinct content xyz{i}abc",
                             confidence=50 + i)
        results = self.brain.recall("bulk", max_results=5)
        self.assertLessEqual(len(results), 5)

    def test_recall_default_max_15(self):
        for i in range(20):
            self.brain.learn("bulk", f"Unique fact {i} with more text", confidence=50 + i)
        results = self.brain.recall("bulk")
        self.assertLessEqual(len(results), 15)

    def test_recall_min_confidence(self):
        self.brain.learn("t", "Low confidence", confidence=30)
        self.brain.learn("t", "High confidence fact here", confidence=90)
        results = self.brain.recall("t", min_confidence=80)
        self.assertEqual(len(results), 1)

    def test_search_keyword(self):
        self.brain.learn("tools", "Autopsy is a forensic tool", confidence=90)
        self.brain.learn("methods", "Timeline analysis is important", confidence=85)
        results = self.brain.search("forensic")
        self.assertEqual(len(results), 1)

    def test_search_case_insensitive(self):
        self.brain.learn("t", "UPPERCASE fact", confidence=90)
        results = self.brain.search("uppercase")
        self.assertEqual(len(results), 1)

    def test_advanced_recall(self):
        self.brain.learn("a", "Primary fact", confidence=90, verified=True)
        self.brain.learn("b", "Related fact", confidence=85)
        # Add link
        facts = self.brain._load(self.brain._facts_path)
        facts[0]["links"] = ["b"]
        self.brain._save(self.brain._facts_path, facts)
        results = self.brain.advanced_recall("a")
        self.assertTrue(len(results) >= 1)


# ======================================================================
# TIER 2: Agents (checkin, report, escalation)
# ======================================================================
class TestAgents(TestDiamondBrainBase):

    def test_agent_checkin(self):
        entry = self.brain.agent_checkin("agent-1", "scanner", "scanning files")
        self.assertEqual(entry["agent_id"], "agent-1")
        self.assertEqual(entry["status"], "active")

    def test_agent_checkin_update(self):
        self.brain.agent_checkin("agent-1", "scanner", "task1")
        self.brain.agent_checkin("agent-1", "auditor", "task2")
        agents = self.brain._load(self.brain._agents_path)
        self.assertEqual(len(agents), 1)
        self.assertEqual(agents[0]["role"], "auditor")

    def test_agent_report_autolearn(self):
        self.brain.agent_checkin("agent-1", "scanner", "scanning")
        result = self.brain.agent_report("agent-1", [
            {"category": "security", "severity": "CRITICAL", "file": "x.py",
             "line": 10, "message": "SQL injection found"},
            {"category": "style", "severity": "LOW", "file": "y.py",
             "line": 5, "message": "Bad indent"},
        ])
        self.assertEqual(result["auto_learned"], 1)
        self.assertEqual(result["total_findings"], 2)


# ======================================================================
# TIER 3: Citations (cite, recall, stats, link_crime)
# ======================================================================
class TestCitations(TestDiamondBrainBase):

    def test_cite_creates_entry(self):
        entry = self.brain.cite("ARS 13-1105", "First Degree Murder",
                                "A person commits...", severity="FELONY")
        self.assertEqual(entry["code"], "ARS 13-1105")
        self.assertEqual(entry["severity"], "FELONY")

    def test_cite_dedup_by_code(self):
        self.brain.cite("ARS 13-1105", "Title1", "Text1")
        self.brain.cite("ars 13-1105", "Title2", "Text2")  # case insensitive
        citations = self.brain._load(self.brain._citations_path)
        self.assertEqual(len(citations), 1)
        self.assertEqual(citations[0]["title"], "Title2")

    def test_recall_citations_query(self):
        self.brain.cite("ARS 13-1105", "Murder", "murder statute")
        self.brain.cite("ARS 13-1802", "Theft", "theft statute")
        results = self.brain.recall_citations(query="murder")
        self.assertEqual(len(results), 1)

    def test_recall_citations_severity(self):
        self.brain.cite("ARS 13-1105", "Murder", "text", severity="FELONY")
        self.brain.cite("ARS 28-1381", "DUI", "text", severity="MISDEMEANOR")
        results = self.brain.recall_citations(severity="FELONY")
        self.assertEqual(len(results), 1)

    def test_citation_stats(self):
        self.brain.cite("ARS 13-1105", "Murder", "text", severity="FELONY", category="statute")
        self.brain.cite("ARS 13-1802", "Theft", "text", severity="FELONY", category="statute")
        stats = self.brain.citation_stats()
        self.assertEqual(stats["total_citations"], 2)
        self.assertEqual(stats["by_severity"]["FELONY"], 2)

    def test_link_crime_to_citations(self):
        self.brain.cite("ARS 13-1105", "First Degree Murder",
                        "murder with premeditation", severity="FELONY")
        codes = self.brain.link_crime_to_citations("crime", "premeditated murder")
        self.assertTrue(len(codes) >= 1)


# ======================================================================
# TIER 4: Commands (log, suggest, stats)
# ======================================================================
class TestCommands(TestDiamondBrainBase):

    def test_log_command(self):
        entry = self.brain.log_command("git commit -m 'fix' --verbose")
        self.assertEqual(entry["command"], "git")
        self.assertEqual(entry["subcommand"], "commit")
        self.assertIn("--verbose", entry["flags"])

    def test_suggest_flags(self):
        for _ in range(5):
            self.brain.log_command("git push --force")
        suggestions = self.brain.suggest_flags("git", "push")
        self.assertTrue(len(suggestions) >= 1)
        self.assertEqual(suggestions[0]["flag"], "--force")

    def test_command_stats_global(self):
        self.brain.log_command("git push")
        self.brain.log_command("git pull")
        stats = self.brain.command_stats()
        self.assertEqual(stats["total_commands_logged"], 2)

    def test_command_stats_specific(self):
        self.brain.log_command("git push --force")
        self.brain.log_command("git push --tags")
        stats = self.brain.command_stats("git")
        self.assertEqual(stats["total_invocations"], 2)


# ======================================================================
# TIER 5: Digest + Heatmap
# ======================================================================
class TestDigestHeatmap(TestDiamondBrainBase):

    def test_digest_structure(self):
        d = self.brain.digest()
        self.assertIn("total_facts", d)
        self.assertIn("topics", d)
        self.assertIn("total_citations", d)
        self.assertIn("diamond_link", d)
        self.assertIn("knowledge_graph", d)
        self.assertIn("temporal_events", d)
        self.assertIn("amnesia_entries", d)
        self.assertIn("blob_count", d)

    def test_digest_counts(self):
        self.brain.learn("t", "A fact", confidence=90)
        self.brain.cite("ARS 1", "Title", "Text")
        d = self.brain.digest()
        self.assertEqual(d["total_facts"], 1)
        self.assertEqual(d["total_citations"], 1)

    def test_heatmap_empty(self):
        hm = self.brain.heatmap()
        self.assertEqual(len(hm), 0)

    def test_heatmap_with_data(self):
        self.brain.learn("topic-a", "Fact 1", confidence=90)
        hm = self.brain.heatmap()
        self.assertIn("topic-a", hm)
        self.assertEqual(hm["topic-a"]["count"], 1)


# ======================================================================
# TIER 6: Visuals (table, bar_chart, connection_graph, report, html)
# ======================================================================
class TestVisuals(TestDiamondBrainBase):

    def test_visual_table(self):
        result = self.brain.visual_table(
            ["Col1", "Col2"], [["a", "b"], ["c", "d"]], title="Test"
        )
        self.assertIn("Test", result)
        self.assertIn("Col1", result)

    def test_visual_table_empty(self):
        result = self.brain.visual_table(["Col1"], [], title="Empty")
        self.assertIsInstance(result, str)

    def test_visual_bar_chart(self):
        result = self.brain.visual_bar_chart({"a": 10, "b": 5}, title="Chart")
        self.assertIn("Chart", result)

    def test_visual_bar_chart_empty(self):
        result = self.brain.visual_bar_chart({}, title="Empty")
        self.assertIsInstance(result, str)

    def test_visual_connection_graph(self):
        result = self.brain.visual_connection_graph(
            "center", [("node1", "related"), ("node2", "cited")], title="Graph"
        )
        self.assertIn("center", result)

    def test_visual_report_full(self):
        self.brain.learn("test", "A fact for report", confidence=90)
        result = self.brain.visual_report()
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_visual_report_topic(self):
        self.brain.learn("specific", "Topic-specific fact", confidence=90)
        result = self.brain.visual_report("specific")
        self.assertIn("SPECIFIC", result.upper())

    def test_export_html(self):
        self.brain.learn("t", "HTML fact", confidence=90)
        html_path = os.path.join(self.tmpdir, "test_report.html")
        result = self.brain.export_html(output_path=html_path)
        self.assertTrue(os.path.exists(html_path))
        content = open(html_path).read()
        self.assertIn("<!DOCTYPE html>", content)


# ======================================================================
# TIER 7: Knowledge Graph + BFS
# ======================================================================
class TestKnowledgeGraph(TestDiamondBrainBase):

    def test_graph_add_node(self):
        node = self.brain.graph_add_node("n1", "fact", {"text": "hello"})
        self.assertEqual(node["type"], "fact")

    def test_graph_add_edge(self):
        self.brain.graph_add_node("n1", "fact")
        self.brain.graph_add_node("n2", "fact")
        edge = self.brain.graph_add_edge("n1", "n2", "supports", weight=0.9)
        self.assertEqual(edge["type"], "supports")

    def test_graph_add_edge_dedup(self):
        self.brain.graph_add_node("n1", "fact")
        self.brain.graph_add_node("n2", "fact")
        self.brain.graph_add_edge("n1", "n2", "supports")
        self.brain.graph_add_edge("n1", "n2", "supports")
        graph = self.brain._graph_load()
        supports_edges = [e for e in graph["edges"] if e["type"] == "supports"]
        self.assertEqual(len(supports_edges), 1)

    def test_graph_remove_edge(self):
        self.brain.graph_add_node("n1", "fact")
        self.brain.graph_add_node("n2", "fact")
        self.brain.graph_add_edge("n1", "n2", "supports")
        removed = self.brain.graph_remove_edge("n1", "n2", "supports")
        self.assertEqual(removed, 1)

    def test_graph_bfs(self):
        self.brain.graph_add_node("a", "topic")
        self.brain.graph_add_node("b", "fact")
        self.brain.graph_add_node("c", "fact")
        self.brain.graph_add_edge("a", "b", "contains")
        self.brain.graph_add_edge("b", "c", "related")
        results = self.brain.graph_bfs("a", max_depth=2)
        ids = [r["node_id"] for r in results]
        self.assertIn("b", ids)
        self.assertIn("c", ids)

    def test_graph_bfs_max_depth(self):
        self.brain.graph_add_node("a", "topic")
        self.brain.graph_add_node("b", "fact")
        self.brain.graph_add_node("c", "fact")
        self.brain.graph_add_edge("a", "b", "contains")
        self.brain.graph_add_edge("b", "c", "related")
        results = self.brain.graph_bfs("a", max_depth=1)
        ids = [r["node_id"] for r in results]
        self.assertIn("b", ids)
        self.assertNotIn("c", ids)

    def test_graph_neighbors(self):
        self.brain.graph_add_node("a", "topic")
        self.brain.graph_add_node("b", "fact")
        self.brain.graph_add_edge("a", "b", "contains")
        neighbors = self.brain.graph_neighbors("a")
        self.assertEqual(len(neighbors), 1)

    def test_graph_query(self):
        self.brain.graph_add_node("n1", "fact", {"text": "forensics"})
        results = self.brain.graph_query("forensics")
        # Query finds the node itself, then BFS from it (0 neighbors)
        # The node is the starting point, not returned in BFS
        self.assertIsInstance(results, list)

    def test_graph_auto_index(self):
        self.brain.learn("test-topic", "A fact to index", confidence=90)
        self.brain.cite("ARS 1", "Title", "Text")
        result = self.brain.graph_auto_index()
        self.assertGreater(result["nodes_created"], 0)
        self.assertGreater(result["total_nodes"], 0)

    def test_graph_stats(self):
        self.brain.graph_add_node("n1", "fact")
        self.brain.graph_add_node("n2", "topic")
        self.brain.graph_add_edge("n1", "n2", "belongs_to")
        stats = self.brain.graph_stats()
        self.assertEqual(stats["total_nodes"], 2)
        self.assertEqual(stats["total_edges"], 1)


# ======================================================================
# TIER 8: FSRS Spaced Repetition
# ======================================================================
class TestFSRS(TestDiamondBrainBase):

    def test_fsrs_retrievability_fresh(self):
        entry = self.brain.learn("t", "Fresh fact", confidence=90)
        r = self.brain.fsrs_retrievability(entry)
        self.assertGreater(r, 0.5)

    def test_fsrs_review_good(self):
        self.brain.learn("t", "Reviewable fact", confidence=80)
        result = self.brain.fsrs_review("t", "Reviewable fact", 3)  # Good
        self.assertIsNotNone(result)
        self.assertIn("fsrs_stability", result)
        self.assertIn("fsrs_difficulty", result)
        self.assertEqual(result["fsrs_reps"], 1)

    def test_fsrs_review_again(self):
        self.brain.learn("t", "Hard fact to remember", confidence=80)
        result = self.brain.fsrs_review("t", "Hard fact to remember", 1)  # Again
        self.assertIsNotNone(result)
        self.assertEqual(result["fsrs_reps"], 0)  # Reset on Again
        self.assertEqual(result["fsrs_lapses"], 1)

    def test_fsrs_review_invalid_rating(self):
        self.brain.learn("t", "Fact", confidence=80)
        with self.assertRaises(ValueError):
            self.brain.fsrs_review("t", "Fact", 5)

    def test_fsrs_review_not_found(self):
        result = self.brain.fsrs_review("nonexistent", "nope", 3)
        self.assertIsNone(result)

    def test_fsrs_due(self):
        self.brain.learn("t", "Fact that might be due", confidence=50)
        due = self.brain.fsrs_due(threshold=0.99)  # Very high threshold
        self.assertTrue(len(due) >= 1)

    def test_fsrs_stats(self):
        self.brain.learn("t", "Stat fact", confidence=90)
        stats = self.brain.fsrs_stats()
        self.assertEqual(stats["total_facts"], 1)
        self.assertIn("avg_retrievability", stats)


# ======================================================================
# TIER 9: Confidence Propagation
# ======================================================================
class TestConfidencePropagation(TestDiamondBrainBase):

    def test_propagation_basic(self):
        self.brain.learn("a", "Source fact", confidence=90)
        self.brain.learn("b", "Connected fact", confidence=80)
        self.brain.graph_auto_index()
        graph = self.brain._graph_load()
        fact_nodes = [nid for nid, n in graph["nodes"].items()
                      if n["type"] == "fact"]
        if len(fact_nodes) >= 2:
            # Add supports edge
            self.brain.graph_add_edge(fact_nodes[0], fact_nodes[1], "supports")
            result = self.brain.propagate_confidence(fact_nodes[0], delta=-10)
            self.assertIn("nodes_affected", result)

    def test_propagation_no_graph(self):
        result = self.brain.propagate_confidence("nonexistent", delta=-5)
        self.assertEqual(result["nodes_affected"], 0)


# ======================================================================
# TIER 10: Contradiction Detection
# ======================================================================
class TestContradictions(TestDiamondBrainBase):

    def test_no_contradictions(self):
        self.brain.learn("t", "Apples are red", confidence=90)
        self.brain.learn("t", "Bananas are yellow", confidence=90)
        results = self.brain.detect_contradictions()
        self.assertEqual(len(results), 0)

    def test_negation_flip(self):
        # Facts must be distinct enough to avoid 80% dedup, but similar after negation strip
        # Manually insert to bypass dedup
        facts = [
            {"topic": "t", "fact": "the server configuration allows remote admin connections by default",
             "confidence": 90, "verified": False, "created_at": _now_iso(),
             "updated_at": _now_iso(), "links": [], "source": "test"},
            {"topic": "t", "fact": "the server configuration does not allow remote admin connections by default",
             "confidence": 60, "verified": False, "created_at": _now_iso(),
             "updated_at": _now_iso(), "links": [], "source": "test"},
        ]
        self.brain._save(self.brain._facts_path, facts)
        results = self.brain.detect_contradictions()
        self.assertTrue(len(results) >= 1)
        types = [r["type"] for r in results]
        self.assertTrue("negation_flip" in types or "antonym_swap" in types)

    def test_antonym_swap(self):
        # Manually insert to bypass dedup
        facts = [
            {"topic": "t", "fact": "the database wire protocol connection is encrypted using standard tls",
             "confidence": 90, "verified": False, "created_at": _now_iso(),
             "updated_at": _now_iso(), "links": [], "source": "test"},
            {"topic": "t", "fact": "the database wire protocol connection is unencrypted using standard tls",
             "confidence": 60, "verified": False, "created_at": _now_iso(),
             "updated_at": _now_iso(), "links": [], "source": "test"},
        ]
        self.brain._save(self.brain._facts_path, facts)
        results = self.brain.detect_contradictions()
        self.assertTrue(len(results) >= 1)

    def test_contradiction_topic_filter(self):
        self.brain.learn("a", "Thing is valid and confirmed", confidence=90)
        self.brain.learn("a", "Thing is not valid and confirmed", confidence=60)
        self.brain.learn("b", "Other is true and checked", confidence=90)
        self.brain.learn("b", "Other is not true and checked", confidence=60)
        results = self.brain.detect_contradictions(topic="a")
        for r in results:
            self.assertEqual(r["fact_a"]["topic"], "a")


# ======================================================================
# TIER 11: Crystallization
# ======================================================================
class TestCrystallization(TestDiamondBrainBase):

    def test_crystallize_min_cluster(self):
        # Each fact must be <80% similar to avoid dedup
        distinct_facts = [
            "Binary search trees provide O(log n) lookup for sorted data structures",
            "Hash tables use chaining or open addressing to resolve key collisions",
            "Red-black trees maintain balance through rotation and color properties",
            "B-trees optimize disk access with high branching factor and sorted keys",
            "Skip lists use probabilistic layering for expected O(log n) operations",
            "Bloom filters test set membership with false positives but zero false negatives",
            "Trie structures enable prefix-based string matching in O(m) time complexity",
        ]
        for fact in distinct_facts:
            self.brain.learn("cluster-topic", fact, confidence=85)
        facts = self.brain._load(self.brain._facts_path)
        # Verify we actually have enough facts
        cluster_facts = [f for f in facts if f["topic"] == "cluster-topic"]
        self.assertGreaterEqual(len(cluster_facts), 5)
        crystals = self.brain.crystallize(min_cluster=5)
        self.assertTrue(len(crystals) >= 1)

    def test_crystallize_below_threshold(self):
        self.brain.learn("small", "Only one fact", confidence=90)
        crystals = self.brain.crystallize(min_cluster=5)
        self.assertEqual(len(crystals), 0)

    def test_crystallize_key_terms(self):
        distinct_python = [
            "Python list comprehensions provide concise syntax for creating filtered lists",
            "Python decorators wrap functions to add behavior without modifying source code",
            "Python generators yield values lazily using the yield keyword for memory efficiency",
            "Python context managers handle resource cleanup via with statements automatically",
            "Python metaclasses control class creation and allow framework-level customization",
            "Python asyncio enables concurrent IO operations without threading overhead",
        ]
        for fact in distinct_python:
            self.brain.learn("tech", fact, confidence=85)
        crystals = self.brain.crystallize(min_cluster=5)
        self.assertTrue(len(crystals) >= 1)
        if crystals:
            self.assertIn("python", crystals[0]["key_terms"])

    def test_crystallize_stores_graph_node(self):
        distinct_db = [
            "Database indexing uses B-trees and hash indexes to accelerate query lookups",
            "Database sharding distributes rows across multiple servers by partition key",
            "Database replication copies data to replicas for high availability failover",
            "Database caching stores hot query results in memory via Redis or Memcached",
            "Database ACID transactions ensure atomicity consistency isolation durability",
            "Database vacuum reclaims dead tuple storage in PostgreSQL table files",
        ]
        for fact in distinct_db:
            self.brain.learn("graphed", fact, confidence=85)
        self.brain.crystallize(min_cluster=5)
        stats = self.brain.graph_stats()
        self.assertGreater(stats["total_nodes"], 0)


# ======================================================================
# TIER 12: Temporal Reasoning
# ======================================================================
class TestTemporal(TestDiamondBrainBase):

    def test_temporal_add(self):
        entry = self.brain.temporal_add("evt1", "2026-01-01T00:00:00+00:00",
                                        "2026-01-01T01:00:00+00:00")
        self.assertEqual(entry["event_id"], "evt1")

    def test_temporal_add_dedup(self):
        self.brain.temporal_add("evt1", "2026-01-01T00:00:00+00:00")
        self.brain.temporal_add("evt1", "2026-01-02T00:00:00+00:00")
        events = self.brain._load(self.brain._temporal_path)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["start"], "2026-01-02T00:00:00+00:00")

    def test_temporal_relation_before(self):
        self.brain.temporal_add("a", "2026-01-01T00:00:00Z", "2026-01-01T01:00:00Z")
        self.brain.temporal_add("b", "2026-01-01T02:00:00Z", "2026-01-01T03:00:00Z")
        self.assertEqual(self.brain.temporal_relation("a", "b"), "before")

    def test_temporal_relation_after(self):
        self.brain.temporal_add("a", "2026-01-01T02:00:00Z", "2026-01-01T03:00:00Z")
        self.brain.temporal_add("b", "2026-01-01T00:00:00Z", "2026-01-01T01:00:00Z")
        self.assertEqual(self.brain.temporal_relation("a", "b"), "after")

    def test_temporal_relation_overlaps(self):
        self.brain.temporal_add("a", "2026-01-01T00:00:00Z", "2026-01-01T02:00:00Z")
        self.brain.temporal_add("b", "2026-01-01T01:00:00Z", "2026-01-01T03:00:00Z")
        self.assertEqual(self.brain.temporal_relation("a", "b"), "overlaps")

    def test_temporal_relation_during(self):
        self.brain.temporal_add("a", "2026-01-01T01:00:00Z", "2026-01-01T02:00:00Z")
        self.brain.temporal_add("b", "2026-01-01T00:00:00Z", "2026-01-01T03:00:00Z")
        self.assertEqual(self.brain.temporal_relation("a", "b"), "during")

    def test_temporal_relation_equals(self):
        self.brain.temporal_add("a", "2026-01-01T00:00:00Z", "2026-01-01T01:00:00Z")
        self.brain.temporal_add("b", "2026-01-01T00:00:00Z", "2026-01-01T01:00:00Z")
        self.assertEqual(self.brain.temporal_relation("a", "b"), "equals")

    def test_temporal_relation_meets(self):
        self.brain.temporal_add("a", "2026-01-01T00:00:00Z", "2026-01-01T01:00:00Z")
        self.brain.temporal_add("b", "2026-01-01T01:00:00Z", "2026-01-01T02:00:00Z")
        self.assertEqual(self.brain.temporal_relation("a", "b"), "meets")

    def test_temporal_relation_contains(self):
        self.brain.temporal_add("a", "2026-01-01T00:00:00Z", "2026-01-01T03:00:00Z")
        self.brain.temporal_add("b", "2026-01-01T01:00:00Z", "2026-01-01T02:00:00Z")
        self.assertEqual(self.brain.temporal_relation("a", "b"), "contains")

    def test_temporal_chain(self):
        self.brain.temporal_add("x", "2026-01-01T00:00:00Z", "2026-01-01T01:00:00Z")
        self.brain.temporal_add("y", "2026-01-01T02:00:00Z", "2026-01-01T03:00:00Z")
        chain = self.brain.temporal_chain()
        self.assertEqual(len(chain), 2)
        self.assertIn("_relation_to_prev", chain[1])

    def test_temporal_timeline(self):
        self.brain.temporal_add("a", "2026-01-01T00:00:00Z")
        self.brain.temporal_add("b", "2026-06-01T00:00:00Z")
        results = self.brain.temporal_timeline(
            start="2026-01-01T00:00:00Z",
            end="2026-03-01T00:00:00Z"
        )
        self.assertEqual(len(results), 1)

    def test_temporal_unknown_event(self):
        self.assertEqual(self.brain.temporal_relation("nope", "nada"), "unknown")


# ======================================================================
# TIER 13: Selective Amnesia
# ======================================================================
class TestAmnesia(TestDiamondBrainBase):

    def test_forget(self):
        self.brain.learn("secret", "Classified information here", confidence=90)
        result = self.brain.forget("secret", "Classified", "Redacted for safety")
        self.assertEqual(result["forgotten_count"], 1)
        # Fact should be gone from active store
        facts = self.brain._load(self.brain._facts_path)
        secret_facts = [f for f in facts if f["topic"] == "secret"]
        self.assertEqual(len(secret_facts), 0)

    def test_forget_preserves_others(self):
        self.brain.learn("keep", "Keep this fact", confidence=90)
        self.brain.learn("delete", "Delete this fact", confidence=90)
        self.brain.forget("delete", "Delete", "Testing")
        facts = self.brain._load(self.brain._facts_path)
        self.assertEqual(len(facts), 1)
        self.assertEqual(facts[0]["topic"], "keep")

    def test_amnesia_log(self):
        self.brain.learn("t", "Forgotten fact", confidence=80)
        self.brain.forget("t", "Forgotten", "Test reason")
        log = self.brain.amnesia_log()
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0]["reason"], "Test reason")

    def test_amnesia_restore(self):
        self.brain.learn("t", "Restorable fact here", confidence=85)
        self.brain.forget("t", "Restorable", "Temporary delete")
        result = self.brain.amnesia_restore("t", "Restorable")
        self.assertEqual(result["restored_count"], 1)
        facts = self.brain._load(self.brain._facts_path)
        self.assertEqual(len(facts), 1)

    def test_forget_no_match(self):
        result = self.brain.forget("nonexistent", "nothing", "no reason")
        self.assertEqual(result["forgotten_count"], 0)


# ======================================================================
# TIER 14: Consensus
# ======================================================================
class TestConsensus(TestDiamondBrainBase):

    def test_consensus_standalone(self):
        self.brain.learn("t", "A fact to check", confidence=90)
        result = self.brain.consensus_check("t", "A fact to check")
        self.assertEqual(result["consensus_level"], "standalone")
        self.assertEqual(result["total_peers"], 0)

    def test_consensus_with_local_match(self):
        self.brain.learn("t", "Matching fact content", confidence=90)
        result = self.brain.consensus_check("t", "Matching fact content")
        self.assertEqual(result["local_matches"], 1)


# ======================================================================
# TIER 15: Blob Store
# ======================================================================
class TestBlobStore(TestDiamondBrainBase):

    def test_blob_store_bytes(self):
        result = self.brain.blob_store(b"binary data", {"description": "test"})
        self.assertIn("hash", result)
        self.assertEqual(result["size"], 11)

    def test_blob_store_string(self):
        result = self.brain.blob_store("text data", {"description": "text"})
        self.assertEqual(result["size"], 9)

    def test_blob_store_idempotent(self):
        r1 = self.brain.blob_store(b"same content")
        r2 = self.brain.blob_store(b"same content")
        self.assertEqual(r1["hash"], r2["hash"])

    def test_blob_retrieve(self):
        stored = self.brain.blob_store(b"retrieve me")
        retrieved = self.brain.blob_retrieve(stored["hash"])
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["content"], b"retrieve me")

    def test_blob_retrieve_missing(self):
        result = self.brain.blob_retrieve("0" * 64)
        self.assertIsNone(result)

    def test_blob_verify_intact(self):
        stored = self.brain.blob_store(b"verify this")
        result = self.brain.blob_verify(stored["hash"])
        self.assertTrue(result["valid"])

    def test_blob_verify_tampered(self):
        stored = self.brain.blob_store(b"original")
        # Tamper with the blob
        blob_path = self.brain._blobs_dir / f"{stored['hash']}.blob"
        blob_path.write_bytes(b"tampered")
        result = self.brain.blob_verify(stored["hash"])
        self.assertFalse(result["valid"])

    def test_blob_list(self):
        self.brain.blob_store(b"blob1", {"description": "first"})
        self.brain.blob_store(b"blob2", {"description": "second"})
        blobs = self.brain.blob_list()
        self.assertEqual(len(blobs), 2)

    def test_blob_link(self):
        stored = self.brain.blob_store(b"evidence")
        result = self.brain.blob_link(stored["hash"], "forensics")
        self.assertIsNotNone(result)


# ======================================================================
# TIER 16: Diamond Link (identity + custody, no network needed)
# ======================================================================
class TestDiamondLink(TestDiamondBrainBase):

    def test_link_identity_before_init(self):
        identity = self.brain.link_identity()
        self.assertTrue(identity is None or identity == {})

    def test_link_init(self):
        if not shutil.which("openssl"):
            self.skipTest("openssl not available")
        identity = self.brain.link_init("TestBrain")
        self.assertIn("fingerprint", identity)
        self.assertEqual(identity["display_name"], "TestBrain")
        self.assertEqual(len(identity["fingerprint"]), 64)

    def test_link_init_idempotent(self):
        if not shutil.which("openssl"):
            self.skipTest("openssl not available")
        id1 = self.brain.link_init("TestBrain")
        id2 = self.brain.link_init("DifferentName")
        self.assertEqual(id1["fingerprint"], id2["fingerprint"])

    def test_link_peers_empty(self):
        peers = self.brain.link_peers()
        self.assertEqual(len(peers), 0)

    def test_link_custody_chain_empty(self):
        result = self.brain.link_verify_custody_chain()
        self.assertTrue(result["valid"])

    def test_link_custody_chain_with_init(self):
        if not shutil.which("openssl"):
            self.skipTest("openssl not available")
        self.brain.link_init("CustodyTest")
        result = self.brain.link_verify_custody_chain()
        self.assertTrue(result["valid"])
        self.assertEqual(result["records"], 1)

    def test_link_custody_log(self):
        if not shutil.which("openssl"):
            self.skipTest("openssl not available")
        self.brain.link_init("LogTest")
        log = self.brain.link_custody_log()
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0]["event_type"], "IDENTITY_CREATED")

    def test_link_status(self):
        status = self.brain.link_status()
        self.assertIn("initialized", status)
        self.assertIn("peer_count", status)

    def test_link_log_empty(self):
        log = self.brain.link_log()
        self.assertEqual(len(log), 0)


# ======================================================================
# TIER 17: Peer Reputation
# ======================================================================
class TestPeerReputation(TestDiamondBrainBase):

    def test_reputation_no_peer(self):
        result = self.brain.link_peer_reputation("nonexistent")
        self.assertIn("error", result)

    def test_adjust_trust_no_peer(self):
        result = self.brain.link_adjust_trust("nonexistent", 10)
        self.assertFalse(result)


# ======================================================================
# TIER 18: Subscriptions
# ======================================================================
class TestSubscriptions(TestDiamondBrainBase):

    def test_subscribe_no_peer(self):
        result = self.brain.link_subscribe("nonexistent", ["topic1"])
        self.assertFalse(result)

    def test_unsubscribe_no_peer(self):
        result = self.brain.link_unsubscribe("nonexistent", ["topic1"])
        self.assertFalse(result)


# ======================================================================
# TIER 19: Prune
# ======================================================================
class TestPrune(TestDiamondBrainBase):

    def test_prune_stale(self):
        # Create an old fact manually
        facts = [{
            "topic": "old",
            "fact": "Ancient fact",
            "confidence": 20,
            "created_at": "2020-01-01T00:00:00+00:00",
            "updated_at": "2020-01-01T00:00:00+00:00",
            "verified": False,
            "links": [],
        }]
        self.brain._save(self.brain._facts_path, facts)
        removed = self.brain.prune_stale(max_age_days=30, min_confidence=30)
        self.assertEqual(removed, 1)

    def test_prune_keeps_recent(self):
        self.brain.learn("fresh", "New fact", confidence=90)
        removed = self.brain.prune_stale(max_age_days=30)
        self.assertEqual(removed, 0)


# ======================================================================
# TIER 20: Utility Functions
# ======================================================================
class TestUtils(unittest.TestCase):

    def test_decayed_confidence(self):
        result = _decayed_confidence(100, _now_iso(), False)
        self.assertGreaterEqual(result, 99)  # Tiny decay in milliseconds

    def test_decayed_confidence_old(self):
        result = _decayed_confidence(100, "2020-01-01T00:00:00+00:00", False)
        self.assertLess(result, 100)
        self.assertGreaterEqual(result, 30)  # Floor is 30

    def test_decayed_verified_slower(self):
        old_date = "2024-01-01T00:00:00+00:00"
        unverified = _decayed_confidence(100, old_date, False)
        verified = _decayed_confidence(100, old_date, True)
        self.assertGreaterEqual(verified, unverified)

    def test_similarity(self):
        self.assertGreater(_similarity("hello world", "hello world"), 0.99)
        self.assertGreater(_similarity("sql-injection", "sql_injection"), 0.8)
        self.assertLess(_similarity("apple", "zebra"), 0.5)


# ======================================================================
# TIER 21: Atomic Writes
# ======================================================================
class TestAtomicWrites(TestDiamondBrainBase):

    def test_save_load_roundtrip(self):
        data = [{"key": "value", "num": 42}]
        self.brain._save(self.brain._facts_path, data)
        loaded = self.brain._load(self.brain._facts_path)
        self.assertEqual(loaded, data)

    def test_no_tmp_files_left(self):
        self.brain.learn("t", "Fact", confidence=90)
        tmp_files = list(Path(self.tmpdir).glob("*.tmp"))
        self.assertEqual(len(tmp_files), 0)


# ======================================================================
# TIER 22: Witness Credibility Scoring
# ======================================================================
class TestWitnessCredibility(TestDiamondBrainBase):

    def test_source_register(self):
        result = self.brain.source_register(
            "witness-1", "human_witness", "Jane Doe", ["forensics"])
        self.assertEqual(result["source_id"], "witness-1")
        self.assertEqual(result["source_type"], "human_witness")
        self.assertEqual(result["display_name"], "Jane Doe")
        self.assertEqual(result["domains"], ["forensics"])

    def test_source_register_default_type(self):
        result = self.brain.source_register("src-1")
        self.assertEqual(result["source_type"], "human_witness")
        self.assertEqual(result["facts_contributed"], 0)

    def test_source_credibility_default(self):
        self.brain.source_register("src-1", "human_witness")
        cred = self.brain.source_credibility("src-1")
        self.assertIn("credibility_score", cred)
        self.assertGreater(cred["credibility_score"], 0)
        self.assertIn("sub_scores", cred)
        self.assertEqual(cred["sub_scores"]["type_base"], 60.0)

    def test_source_credibility_after_contributions(self):
        self.brain.source_register("src-1", "digital_tool",
                                   domains=["forensics"])
        self.brain.learn("forensics-test", "Autopsy is a forensics tool",
                         source="src-1")
        self.brain.learn("forensics-tools", "Volatility analyzes memory",
                         source="src-1")
        cred = self.brain.source_credibility("src-1")
        self.assertEqual(cred["facts_contributed"], 2)

    def test_source_credibility_unregistered(self):
        cred = self.brain.source_credibility("nonexistent")
        self.assertIn("error", cred)

    def test_source_adjust_credibility(self):
        self.brain.source_register("src-1")
        result = self.brain.source_adjust_credibility("src-1", 10)
        self.assertEqual(result["new_adjustment"], 10)
        # Verify capped at 30
        result2 = self.brain.source_adjust_credibility("src-1", 25)
        self.assertEqual(result2["new_adjustment"], 30)

    def test_source_adjust_negative_capped(self):
        self.brain.source_register("src-1")
        result = self.brain.source_adjust_credibility("src-1", -50)
        self.assertEqual(result["new_adjustment"], -30)

    def test_source_weighted_confidence(self):
        self.brain.source_register("src-1", "official_record")
        fact = {"confidence": 80, "source": "src-1"}
        weighted = self.brain.source_weighted_confidence(fact)
        self.assertIsInstance(weighted, float)
        self.assertGreater(weighted, 0)

    def test_source_weighted_unregistered(self):
        fact = {"confidence": 80, "source": "unknown-source"}
        weighted = self.brain.source_weighted_confidence(fact)
        self.assertEqual(weighted, 80.0)

    def test_source_list_ranked(self):
        self.brain.source_register("low", "anonymous")
        self.brain.source_register("high", "official_record")
        ranked = self.brain.source_list()
        self.assertEqual(len(ranked), 2)
        self.assertGreaterEqual(
            ranked[0]["credibility_score"],
            ranked[1]["credibility_score"])

    def test_source_credibility_trend(self):
        self.brain.source_register("src-1")
        self.brain.source_credibility("src-1")
        self.brain.source_credibility("src-1")
        trend = self.brain.source_credibility_trend("src-1")
        self.assertGreaterEqual(len(trend), 2)
        self.assertIn("score", trend[0])
        self.assertIn("timestamp", trend[0])

    def test_digest_includes_sources(self):
        self.brain.source_register("src-1")
        d = self.brain.digest()
        self.assertEqual(d["registered_sources"], 1)


# ======================================================================
# TIER 23: Timeline Anomaly Detection
# ======================================================================
class TestTimelineAnomalies(TestDiamondBrainBase):

    def test_no_anomalies_clean_data(self):
        self.brain.temporal_add("e1", "2026-01-01T00:00:00Z",
                                "2026-01-01T01:00:00Z")
        self.brain.temporal_add("e2", "2026-01-01T02:00:00Z",
                                "2026-01-01T03:00:00Z")
        anomalies = self.brain.temporal_detect_anomalies()
        self.assertEqual(len(anomalies), 0)

    def test_cycle_detection(self):
        self.brain.temporal_add("a", "2026-01-01T00:00:00Z",
                                "2026-01-01T01:00:00Z",
                                data={"depends_on": ["b"]})
        self.brain.temporal_add("b", "2026-01-01T01:00:00Z",
                                "2026-01-01T02:00:00Z",
                                data={"depends_on": ["a"]})
        anomalies = self.brain.temporal_detect_anomalies(
            include_types=["temporal_cycle"])
        self.assertGreater(len(anomalies), 0)
        self.assertEqual(anomalies[0]["severity"], "CRITICAL")

    def test_backwards_causation(self):
        self.brain.temporal_add("cause", "2026-01-01T05:00:00Z",
                                "2026-01-01T06:00:00Z",
                                data={"cause_of": "effect"})
        self.brain.temporal_add("effect", "2026-01-01T01:00:00Z",
                                "2026-01-01T02:00:00Z")
        anomalies = self.brain.temporal_detect_anomalies(
            include_types=["backwards_causation"])
        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0]["type"], "backwards_causation")

    def test_impossible_sequence(self):
        self.brain.temporal_add("dep", "2026-01-01T02:00:00Z",
                                "2026-01-01T05:00:00Z")
        self.brain.temporal_add("task", "2026-01-01T01:00:00Z",
                                "2026-01-01T03:00:00Z",
                                data={"depends_on": ["dep"]})
        anomalies = self.brain.temporal_detect_anomalies(
            include_types=["impossible_sequence"])
        self.assertGreater(len(anomalies), 0)

    def test_speed_violation(self):
        # Phoenix AZ to New York in 10 minutes = ~21,000 km/h
        self.brain.temporal_add(
            "phoenix", "2026-01-01T00:00:00Z", "2026-01-01T00:05:00Z",
            data={"location": {"lat": 33.45, "lon": -112.07}})
        self.brain.temporal_add(
            "nyc", "2026-01-01T00:10:00Z", "2026-01-01T00:15:00Z",
            data={"location": {"lat": 40.71, "lon": -74.01}})
        anomalies = self.brain.temporal_detect_anomalies(
            include_types=["speed_violation"])
        self.assertEqual(len(anomalies), 1)
        self.assertGreater(anomalies[0]["speed_kmh"], 900)

    def test_overlapping_exclusives(self):
        self.brain.temporal_add(
            "use1", "2026-01-01T00:00:00Z", "2026-01-01T02:00:00Z",
            data={"exclusive_resource": "vehicle-AZ123"})
        self.brain.temporal_add(
            "use2", "2026-01-01T01:00:00Z", "2026-01-01T03:00:00Z",
            data={"exclusive_resource": "vehicle-AZ123"})
        anomalies = self.brain.temporal_detect_anomalies(
            include_types=["overlapping_exclusive"])
        self.assertEqual(len(anomalies), 1)

    def test_suspicious_gap(self):
        # 10 events 1h apart, then one massive 500h gap
        for i in range(10):
            self.brain.temporal_add(
                f"evt{i}",
                f"2026-01-01T{i:02d}:00:00Z",
                f"2026-01-01T{i:02d}:30:00Z")
        self.brain.temporal_add(
            "evt_late", "2026-01-22T12:00:00Z", "2026-01-22T13:00:00Z")
        anomalies = self.brain.temporal_detect_anomalies(
            include_types=["suspicious_gap"])
        self.assertGreater(len(anomalies), 0)

    def test_anomaly_summary(self):
        self.brain.temporal_add("a", "2026-01-01T00:00:00Z",
                                "2026-01-01T01:00:00Z",
                                data={"depends_on": ["b"]})
        self.brain.temporal_add("b", "2026-01-01T01:00:00Z",
                                "2026-01-01T02:00:00Z",
                                data={"depends_on": ["a"]})
        summary = self.brain.temporal_anomaly_summary()
        self.assertGreater(summary["total_anomalies"], 0)
        self.assertIn("by_type", summary)
        self.assertIn("by_severity", summary)

    def test_filter_by_type(self):
        self.brain.temporal_add("e1", "2026-01-01T00:00:00Z",
                                "2026-01-01T01:00:00Z")
        anomalies = self.brain.temporal_detect_anomalies(
            include_types=["speed_violation"])
        self.assertEqual(len(anomalies), 0)

    def test_empty_events(self):
        anomalies = self.brain.temporal_detect_anomalies()
        self.assertEqual(len(anomalies), 0)


# ======================================================================
# TIER 24: Merkle DAG for Custody
# ======================================================================
class TestMerkleDAG(TestDiamondBrainBase):

    def _setup_custody(self, n=5):
        """Seed N custody records via link_init + manual appends."""
        import shutil
        if not shutil.which("openssl"):
            self.skipTest("openssl not available")
        self.brain.link_init("MerkleTest")
        for i in range(n):
            self.brain._link_append_custody(
                "TEST_EVENT", {"index": i, "note": f"record {i}"})

    def test_merkle_build_empty(self):
        result = self.brain.merkle_build()
        self.assertEqual(result["leaf_count"], 0)
        self.assertEqual(result["root_hash"], "EMPTY")
        self.assertFalse(result["stale"])

    def test_merkle_build_with_records(self):
        self._setup_custody(5)
        result = self.brain.merkle_build()
        self.assertGreater(result["leaf_count"], 0)
        self.assertNotEqual(result["root_hash"], "EMPTY")
        self.assertEqual(len(result["root_hash"]), 64)

    def test_merkle_prove_and_verify(self):
        self._setup_custody(5)
        self.brain.merkle_build()
        for seq in range(self.brain.merkle_status()["leaf_count"]):
            proof = self.brain.merkle_prove(seq)
            self.assertNotIn("error", proof)
            v = DiamondBrain.merkle_verify_proof(proof)
            self.assertTrue(v["valid"],
                            f"Proof failed for seq {seq}")

    def test_merkle_tampered_proof(self):
        self._setup_custody(5)
        self.brain.merkle_build()
        proof = self.brain.merkle_prove(0)
        proof["leaf_hash"] = "0" * 64  # tamper
        v = DiamondBrain.merkle_verify_proof(proof)
        self.assertFalse(v["valid"])

    def test_merkle_stale_detection(self):
        self._setup_custody(3)
        self.brain.merkle_build()
        status = self.brain.merkle_status()
        self.assertFalse(status["stale"])
        # Append new record -> should mark stale
        self.brain._link_append_custody("NEW_EVENT", {"x": 1})
        status = self.brain.merkle_status()
        self.assertTrue(status["stale"])

    def test_merkle_status_not_built(self):
        status = self.brain.merkle_status()
        self.assertFalse(status["built"])

    def test_merkle_prove_out_of_range(self):
        self._setup_custody(3)
        self.brain.merkle_build()
        proof = self.brain.merkle_prove(999)
        self.assertIn("error", proof)

    def test_merkle_single_record(self):
        self._setup_custody(0)
        self.brain.merkle_build()
        # link_init creates 1 custody record (IDENTITY_CREATED)
        status = self.brain.merkle_status()
        if status["leaf_count"] > 0:
            proof = self.brain.merkle_prove(0)
            v = DiamondBrain.merkle_verify_proof(proof)
            self.assertTrue(v["valid"])


# ======================================================================
# TIER 25: CRDT Sync
# ======================================================================
class TestCRDTSync(TestDiamondBrainBase):

    def test_hlc_monotonic(self):
        hlc1 = self.brain._crdt_hlc_now()
        hlc2 = self.brain._crdt_hlc_now()
        cmp = self.brain._crdt_hlc_compare(hlc1, hlc2)
        self.assertLessEqual(cmp, 0)  # hlc1 <= hlc2

    def test_crdt_metadata_on_learn(self):
        entry = self.brain.learn("t", "A CRDT fact", confidence=80)
        self.assertIn("_crdt", entry)
        self.assertIn("hlc", entry["_crdt"])
        self.assertFalse(entry["_crdt"]["tombstone"])

    def test_crdt_upgrade_facts(self):
        # Insert legacy fact without CRDT
        facts = self.brain._load(self.brain._facts_path)
        facts.append({"topic": "legacy", "fact": "Old fact",
                       "confidence": 70, "source": "auto",
                       "created_at": "2025-01-01T00:00:00Z",
                       "updated_at": "2025-01-01T00:00:00Z",
                       "links": []})
        self.brain._save(self.brain._facts_path, facts)
        result = self.brain.crdt_upgrade_facts()
        self.assertEqual(result["upgraded"], 1)

    def test_crdt_merge_higher_hlc_wins(self):
        local = {"fact": "Local fact", "_crdt": {
            "hlc": {"wall": 100, "counter": 0, "node": "aaa"},
            "version": 1, "tombstone": False}}
        remote = {"fact": "Remote fact", "_crdt": {
            "hlc": {"wall": 200, "counter": 0, "node": "bbb"},
            "version": 1, "tombstone": False}}
        winner = self.brain._crdt_merge_fact(local, remote)
        self.assertEqual(winner, "remote")

    def test_crdt_merge_idempotent(self):
        local = {"fact": "Same fact", "_crdt": {
            "hlc": {"wall": 100, "counter": 0, "node": "aaa"},
            "version": 1, "tombstone": False}}
        winner = self.brain._crdt_merge_fact(local, dict(local))
        self.assertEqual(winner, "local")  # equal -> local wins

    def test_crdt_tombstone_filters(self):
        self.brain.learn("t", "Visible fact")
        self.brain.learn("t", "Hidden fact for removal")
        self.brain.crdt_tombstone("t", "Hidden")
        results = self.brain.recall("t")
        facts_text = [f["fact"] for f in results]
        self.assertNotIn("Hidden fact for removal", facts_text)

    def test_crdt_tombstone_search_filters(self):
        self.brain.learn("t", "Searchable fact about cats")
        self.brain.learn("t", "Doomed fact about cats")
        self.brain.crdt_tombstone("t", "Doomed")
        results = self.brain.search("cats")
        facts_text = [f["fact"] for f in results]
        self.assertNotIn("Doomed fact about cats", facts_text)

    def test_crdt_merge_snapshot(self):
        self.brain.learn("t", "Local fact A", confidence=80)
        snapshot = {
            "source_fingerprint": "remote123456",
            "facts": [{
                "topic": "t",
                "fact": "Remote fact B",
                "confidence": 85,
                "source": "remote",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
                "_crdt": {
                    "hlc": {"wall": 999999999999, "counter": 0,
                            "node": "remote123456"},
                    "origin_node": "remote123456",
                    "version": 1, "tombstone": False, "merge_history": []},
            }],
        }
        result = self.brain.crdt_merge_snapshot(snapshot)
        self.assertEqual(result["added"], 1)

    def test_crdt_status(self):
        self.brain.learn("t", "A fact")
        status = self.brain.crdt_status()
        self.assertIn("node_id", status)
        self.assertGreater(status["crdt_enabled"], 0)
        self.assertEqual(status["tombstoned"], 0)

    def test_crdt_debug_hlc(self):
        self.brain.learn("t", "Debug me")
        debug = self.brain.crdt_debug_hlc()
        self.assertGreater(len(debug), 0)
        self.assertIn("hlc", debug[0])


# ======================================================================
# TIER 26: CASE/UCO Ontology Export
# ======================================================================
class TestCASEExport(TestDiamondBrainBase):

    def test_export_empty(self):
        bundle = self.brain.export_case_uco()
        self.assertIn("@context", bundle)
        self.assertIn("@graph", bundle)
        self.assertEqual(len(bundle["@graph"]), 0)

    def test_export_with_facts(self):
        self.brain.learn("forensics", "Autopsy is a disk forensics tool",
                         confidence=90)
        self.brain.learn("network", "Wireshark captures packets",
                         confidence=85)
        bundle = self.brain.export_case_uco()
        self.assertGreater(len(bundle["@graph"]), 0)

    def test_export_classifies_tool(self):
        self.brain.learn("tools", "Autopsy analyzes disk images")
        bundle = self.brain.export_case_uco()
        types = [o["@type"] for o in bundle["@graph"]]
        self.assertIn("uco-tool:Tool", types)

    def test_export_classifies_artifact(self):
        self.brain.learn("evidence", "The registry file contains keys")
        bundle = self.brain.export_case_uco()
        types = [o["@type"] for o in bundle["@graph"]]
        self.assertIn("uco-observable:ObservableObject", types)

    def test_export_classifies_general(self):
        self.brain.learn("legal", "Miranda rights must be read")
        bundle = self.brain.export_case_uco()
        types = [o["@type"] for o in bundle["@graph"]]
        self.assertIn("uco-core:Assertion", types)

    def test_export_with_temporal(self):
        self.brain.temporal_add("evt1", "2026-01-01T00:00:00Z",
                                "2026-01-01T01:00:00Z")
        bundle = self.brain.export_case_uco()
        types = [o["@type"] for o in bundle["@graph"]]
        self.assertIn("uco-action:Action", types)

    def test_export_to_file(self):
        self.brain.learn("t", "Test fact")
        out_path = os.path.join(self.tmpdir, "export.jsonld")
        self.brain.export_case_uco(output_path=out_path)
        self.assertTrue(os.path.exists(out_path))
        data = json.loads(Path(out_path).read_text(encoding="utf-8"))
        self.assertIn("@context", data)

    def test_validate_valid_export(self):
        self.brain.learn("t", "Fact")
        bundle = self.brain.export_case_uco()
        result = self.brain.case_validate_export(bundle)
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)

    def test_validate_invalid_missing_context(self):
        result = self.brain.case_validate_export({"@graph": []})
        self.assertFalse(result["valid"])

    def test_validate_duplicate_ids(self):
        data = {
            "@context": {},
            "@graph": [
                {"@id": "kb:1", "@type": "test"},
                {"@id": "kb:1", "@type": "test"},
            ],
        }
        result = self.brain.case_validate_export(data)
        self.assertFalse(result["valid"])

    def test_export_with_case_number(self):
        bundle = self.brain.export_case_uco(
            investigation_name="Test Case",
            case_number="AZ-2026-001")
        self.assertEqual(
            bundle["case-investigation:caseNumber"], "AZ-2026-001")

    def test_export_filters_tombstoned(self):
        self.brain.learn("t", "Keep this fact")
        self.brain.learn("t", "Remove this doomed fact")
        self.brain.crdt_tombstone("t", "doomed")
        bundle = self.brain.export_case_uco()
        descriptions = [o.get("uco-core:description", "")
                        for o in bundle["@graph"]]
        self.assertNotIn("Remove this doomed fact", descriptions)


# ===================================================================
# TIER 28: Homomorphic Confidence
# ===================================================================

class TestHomomorphicConfidence(TestDiamondBrainBase):

    def test_shares_sum_to_score(self):
        """Additive shares mod prime reconstruct the original score."""
        score = 75
        shares = self.brain._hc_split_score(score, 3)
        p = self.brain._HC_DEFAULT_PRIME
        self.assertEqual(sum(shares) % p, score)

    def test_shares_sum_to_score_large(self):
        """Works for scores near prime boundary."""
        score = 99
        shares = self.brain._hc_split_score(score, 5)
        p = self.brain._HC_DEFAULT_PRIME
        self.assertEqual(sum(shares) % p, score)

    def test_commitment_verify(self):
        """Commitment matches when partial_sum and nonce are correct."""
        partial = 42
        nonce = "abc123"
        c = self.brain._hc_commitment(partial, nonce)
        self.assertEqual(len(c), 64)  # SHA-256 hex
        # Same inputs = same commitment
        c2 = self.brain._hc_commitment(partial, nonce)
        self.assertEqual(c, c2)
        # Different nonce = different commitment
        c3 = self.brain._hc_commitment(partial, "xyz789")
        self.assertNotEqual(c, c3)

    def test_initiate_session(self):
        """hc_initiate creates a session with shares."""
        result = self.brain.hc_initiate("test-topic", "test fact", 80)
        self.assertEqual(result["phase"], "initiated")
        self.assertIn("fact_hash", result)
        self.assertEqual(result["n_expected"], 2)  # 1 peer + self
        self.assertEqual(len(result["shares_for_peers"]), 1)

    def test_full_2brain_protocol(self):
        """Full protocol: 2 brains, initiate -> commit -> reveal -> aggregate."""
        # Brain A initiates
        r1 = self.brain.hc_initiate("topic", "fact text", 80, n_peers=1)
        fh = r1["fact_hash"]
        peer_share = r1["shares_for_peers"][0]

        # Simulate peer B: compute their partial sum and commitment
        peer_fp = "peer-B-fingerprint"
        peer_nonce = "peer-nonce-123"
        peer_partial = peer_share  # peer's partial sum = their received share
        peer_commitment = self.brain._hc_commitment(peer_partial, peer_nonce)

        # Brain A receives peer B's commitment + share (share=0, B keeps theirs)
        r2 = self.brain.hc_receive_commitment(peer_fp, fh, peer_commitment, 0)
        self.assertEqual(r2["phase"], "committed")

        # Brain A reveals
        r3 = self.brain.hc_reveal(fh)
        self.assertEqual(r3["phase"], "revealed")

        # Brain A receives peer B's reveal
        r4 = self.brain.hc_receive_reveal(peer_fp, fh, peer_partial, peer_nonce)
        self.assertTrue(r4["verified"])

        # Aggregate
        r5 = self.brain.hc_aggregate(fh)
        self.assertEqual(r5["phase"], "aggregated")
        self.assertEqual(r5["participants"], 2)
        # The aggregate total should reconstruct correctly
        self.assertIn("average", r5)

    def test_3brain_protocol(self):
        """Full protocol with 3 participants."""
        r1 = self.brain.hc_initiate("topic3", "fact3", 90, n_peers=2)
        fh = r1["fact_hash"]
        self.assertEqual(len(r1["shares_for_peers"]), 2)
        self.assertEqual(r1["n_expected"], 3)

    def test_tampered_reveal_detection(self):
        """Detect commitment mismatch on reveal."""
        r1 = self.brain.hc_initiate("topic-tamper", "tamper test", 70)
        fh = r1["fact_hash"]
        peer_fp = "bad-peer"
        # Commit with one value
        legit_commitment = self.brain._hc_commitment(42, "nonce1")
        self.brain.hc_receive_commitment(peer_fp, fh, legit_commitment, 0)
        self.brain.hc_reveal(fh)
        # Reveal with different value (tampering)
        r = self.brain.hc_receive_reveal(peer_fp, fh, 99, "nonce1")
        self.assertIn("error", r)
        self.assertIn("tampering", r["error"])

    def test_phase_ordering(self):
        """Cannot aggregate before enough reveals."""
        r1 = self.brain.hc_initiate("topic-phase", "phase test", 60)
        fh = r1["fact_hash"]
        # Try to aggregate with only self (no peer reveal)
        r = self.brain.hc_aggregate(fh)
        self.assertIn("error", r)

    def test_status_single(self):
        """hc_status with specific hash returns session details."""
        r1 = self.brain.hc_initiate("status-topic", "status fact", 55)
        fh = r1["fact_hash"]
        s = self.brain.hc_status(fh)
        self.assertEqual(s["topic"], "status-topic")
        self.assertEqual(s["phase"], "initiated")
        self.assertEqual(s["n_expected"], 2)

    def test_status_all(self):
        """hc_status without hash returns all sessions."""
        self.brain.hc_initiate("all1", "fact1", 50)
        self.brain.hc_initiate("all2", "fact2", 60)
        result = self.brain.hc_status()
        self.assertIsInstance(result, list)
        self.assertGreaterEqual(len(result), 2)

    def test_no_session_error(self):
        """Operations on non-existent session return error."""
        r = self.brain.hc_reveal("nonexistent_hash")
        self.assertIn("error", r)
        r = self.brain.hc_aggregate("nonexistent_hash")
        self.assertIn("error", r)


# ===================================================================
# TIER 29: Neural Cortex (LLM Reasoning Layer)
# ===================================================================

class TestNeuralCortex(TestDiamondBrainBase):

    @staticmethod
    def _fake_chat(messages, temperature=0.3, max_tokens=2000):
        """Deterministic fake LLM response based on message content."""
        user_msg = messages[-1]["content"] if messages else ""
        if "summarize" in user_msg.lower():
            return "This is a summary of the forensic evidence."
        if "hypothes" in user_msg.lower():
            return json.dumps([{
                "hypothesis": "Test hypothesis",
                "supporting_evidence": ["fact1"],
                "confidence": 75,
                "reasoning": "Based on evidence"
            }])
        if "reliability" in user_msg.lower() or "credibility" in user_msg.lower():
            return "Source shows moderate reliability with some inconsistencies."
        if "narrative" in user_msg.lower() or "chronological" in user_msg.lower():
            return "On day one, the initial event occurred."
        if "case brief" in user_msg.lower() or "formal" in user_msg.lower():
            return ("## Executive Summary\nBrief content.\n"
                    "## Evidence\nEvidence content.")
        return "This is a test response from the Neural Cortex."

    def setUp(self):
        super().setUp()
        self.brain._cortex_chat = self._fake_chat
        self.brain.learn("forensics", "Autopsy is a digital forensics tool",
                         confidence=90, source="expert-1")
        self.brain.learn("forensics", "Volatility analyzes memory dumps",
                         confidence=85, source="expert-1")
        self.brain.learn("evidence", "MD5 hashes verify file integrity",
                         confidence=80, source="textbook")

    def test_cortex_ask_with_llm(self):
        result = self.brain.cortex_ask("What forensic tools are available?")
        self.assertFalse(result["fallback"])
        self.assertIn("answer", result)
        self.assertIsInstance(result["sources_used"], list)
        self.assertEqual(result["model"], "lm_studio")

    def test_cortex_ask_fallback(self):
        self.brain._cortex_chat = lambda *a, **kw: None
        result = self.brain.cortex_ask("What forensic tools are available?")
        self.assertTrue(result["fallback"])
        self.assertEqual(result["model"], "fallback")
        self.assertIn("LLM unavailable", result["answer"])

    def test_cortex_summarize_with_llm(self):
        result = self.brain.cortex_summarize("forensics")
        self.assertFalse(result["fallback"])
        self.assertIn("summary", result)
        self.assertGreater(result["fact_count"], 0)

    def test_cortex_summarize_fallback(self):
        self.brain._cortex_chat = lambda *a, **kw: None
        result = self.brain.cortex_summarize("forensics")
        self.assertTrue(result["fallback"])
        self.assertIn("summary", result)

    def test_cortex_hypothesize_with_llm(self):
        result = self.brain.cortex_hypothesize(
            ["forensics", "evidence"], "Who accessed the system?")
        self.assertFalse(result["fallback"])
        self.assertIsInstance(result["hypotheses"], list)
        self.assertGreater(len(result["hypotheses"]), 0)

    def test_cortex_hypothesize_fallback(self):
        self.brain._cortex_chat = lambda *a, **kw: None
        result = self.brain.cortex_hypothesize(
            ["forensics"], "Who accessed the system?")
        self.assertTrue(result["fallback"])

    def test_cortex_cross_examine_with_llm(self):
        self.brain.source_register("expert-1", "human_witness", "Dr. Expert")
        result = self.brain.cortex_cross_examine("expert-1")
        self.assertFalse(result["fallback"])
        self.assertIn("analysis", result)
        self.assertIn("credibility_score", result)

    def test_cortex_cross_examine_fallback(self):
        self.brain._cortex_chat = lambda *a, **kw: None
        self.brain.source_register("expert-1", "human_witness")
        result = self.brain.cortex_cross_examine("expert-1")
        self.assertTrue(result["fallback"])
        self.assertIn("credibility_score", result)

    def test_cortex_cross_examine_unregistered(self):
        result = self.brain.cortex_cross_examine("nobody")
        self.assertIn("error", result)

    def test_cortex_timeline_narrative(self):
        self.brain.temporal_add("evt1", "2026-01-01T10:00:00Z",
                                "2026-01-01T11:00:00Z")
        self.brain.temporal_add("evt2", "2026-01-01T12:00:00Z",
                                "2026-01-01T13:00:00Z")
        result = self.brain.cortex_timeline_narrative()
        self.assertFalse(result["fallback"])
        self.assertEqual(result["event_count"], 2)

    def test_cortex_timeline_empty(self):
        result = self.brain.cortex_timeline_narrative()
        self.assertEqual(result["event_count"], 0)

    def test_cortex_case_brief(self):
        result = self.brain.cortex_case_brief(case_number="CR-2026-001")
        self.assertFalse(result["fallback"])
        self.assertIn("brief", result)
        self.assertIsInstance(result["sections"], list)

    def test_cortex_status(self):
        result = self.brain.cortex_status()
        self.assertIn("available", result)
        self.assertIn("total_queries", result)
        self.assertIsInstance(result["avg_response_ms"], int)

    def test_cortex_query_tracking(self):
        self.brain.cortex_ask("test question")
        log = self.brain._cortex_log_load()
        self.assertEqual(log["total_queries"], 1)
        self.assertEqual(log["queries"][0]["method"], "ask")


# ── Tier 30: Third Eye — Meta-Cognitive Surveillance ────────────────
class TestThirdEye(TestDiamondBrainBase):

    def test_scan_empty_brain(self):
        """Clean brain returns no alerts."""
        alerts = self.brain.third_eye_scan()
        active = [a for a in alerts if not a.get("suppressed")]
        self.assertEqual(active, [])

    def test_detect_unresolved_escalation(self):
        """Unresolved escalation in escalations.json -> alert fires."""
        import json
        from datetime import datetime, timezone
        escalations = [{
            "finding": {"category": "rare-topic", "severity": "HIGH"},
            "reason": "No brain knowledge",
            "escalated_at": datetime.now(timezone.utc).isoformat(),
            "resolved": False,
        }]
        self.brain._save(self.brain._escalations_path, escalations)
        alerts = self.brain.third_eye_scan(include_types=["unresolved_escalations"])
        active = [a for a in alerts if not a.get("suppressed")]
        self.assertTrue(len(active) >= 1)
        self.assertEqual(active[0]["type"], "unresolved_escalations")
        self.assertIn("severity", active[0])

    def test_detect_tombstone_accumulation(self):
        """Tombstone >20% facts -> HIGH alert."""
        # Learn 5 facts, tombstone 2 (40%)
        for i in range(5):
            self.brain.learn(f"topic-ts-{i}", f"fact {i}", confidence=80)
        facts = self.brain._load(self.brain._facts_path)
        for f in facts[:2]:
            f.setdefault("_crdt", {})["tombstone"] = True
        self.brain._save(self.brain._facts_path, facts)
        alerts = self.brain.third_eye_scan(include_types=["tombstone_accumulation"])
        active = [a for a in alerts if not a.get("suppressed")]
        self.assertTrue(len(active) >= 1)
        self.assertEqual(active[0]["severity"], "HIGH")

    def test_detect_orphaned_blob(self):
        """Manually create .blob without .meta.json -> HIGH alert."""
        self.brain._blobs_dir.mkdir(parents=True, exist_ok=True)
        orphan = self.brain._blobs_dir / "deadbeef1234.blob"
        orphan.write_bytes(b"orphaned evidence")
        alerts = self.brain.third_eye_scan(include_types=["orphaned_blobs"])
        active = [a for a in alerts if not a.get("suppressed")]
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["severity"], "HIGH")
        self.assertIn("deadbeef1234", active[0]["affected"])

    def test_detect_graph_isolation(self):
        """Add graph node with no edges -> MEDIUM alert."""
        self.brain.graph_add_node("isolated-node-1", "topic",
                                  {"label": "lonely"})
        alerts = self.brain.third_eye_scan(include_types=["graph_isolation"])
        active = [a for a in alerts if not a.get("suppressed")]
        self.assertTrue(len(active) >= 1)
        self.assertEqual(active[0]["severity"], "MEDIUM")

    def test_detect_stale_crystal(self):
        """Learn facts, crystallize, then learn more -> crystal becomes stale."""
        distinct_facts = [
            "Autopsy is a digital forensics platform for disk analysis",
            "Volatility extracts memory artifacts from RAM dumps",
            "EnCase produces court-admissible forensic images",
            "FTK Imager creates bit-for-bit copies of storage media",
            "Wireshark captures and analyzes network packet traffic",
            "Sleuth Kit provides command-line forensic analysis tools",
        ]
        for fact in distinct_facts:
            self.brain.learn("crystal-topic", fact, confidence=85)
        self.brain.crystallize(topic="crystal-topic", min_cluster=5)
        # Backdate the crystal
        graph = self.brain._graph_load()
        for nid, node in graph["nodes"].items():
            if node.get("type") == "crystal":
                node["data"]["crystallized_at"] = "2025-01-01T00:00:00Z"
        self.brain._graph_save(graph)
        # Learn a new fact (updated_at is now)
        self.brain.learn("crystal-topic", "brand new finding", confidence=90)
        alerts = self.brain.third_eye_scan(include_types=["stale_crystals"])
        active = [a for a in alerts if not a.get("suppressed")]
        self.assertTrue(len(active) >= 1)
        self.assertIn("crystal-topic", active[0]["affected"])

    def test_detect_inactive_source(self):
        """Register source, never learn with it -> HIGH alert."""
        self.brain.source_register("ghost-src", "witness", "Ghost Witness")
        alerts = self.brain.third_eye_scan(include_types=["inactive_sources"])
        active = [a for a in alerts if not a.get("suppressed")]
        self.assertTrue(len(active) >= 1)
        self.assertEqual(active[0]["severity"], "HIGH")
        self.assertIn("ghost-src", active[0]["affected"])

    def test_detect_crime_citation_void(self):
        """Learn fact with 'murder' keyword, links=[] -> HIGH alert."""
        self.brain.learn("crime-case", "The suspect committed murder in Phoenix")
        # Clear any auto-links
        facts = self.brain._load(self.brain._facts_path)
        for f in facts:
            if "murder" in f.get("fact", "").lower():
                f["links"] = []
        self.brain._save(self.brain._facts_path, facts)
        alerts = self.brain.third_eye_scan(include_types=["crime_citation_voids"])
        active = [a for a in alerts if not a.get("suppressed")]
        self.assertTrue(len(active) >= 1)
        self.assertEqual(active[0]["severity"], "HIGH")

    def test_detect_never_reviewed(self):
        """Learn 25 facts, no fsrs_review -> MEDIUM alert."""
        # Each fact needs a unique topic to avoid within-topic dedup
        facts = [
            ("disk-imaging", "dd creates bit-for-bit copies of storage media"),
            ("memory-forensics", "Volatility extracts process lists from RAM dumps"),
            ("network-capture", "Wireshark decodes packet protocols in real-time"),
            ("mobile-forensics", "Cellebrite UFED bypasses device lock screens"),
            ("malware-analysis", "Ghidra decompiles x86 and ARM binaries"),
            ("log-analysis", "Plaso creates super timelines from multiple log sources"),
            ("registry-forensics", "RegRipper parses Windows registry hives automatically"),
            ("email-forensics", "MIME header analysis reveals original sender routing"),
            ("browser-forensics", "SQLite databases store Chrome browsing history"),
            ("steganography", "LSB analysis detects hidden data in image pixels"),
            ("crypto-analysis", "Hashcat performs GPU-accelerated password recovery"),
            ("file-carving", "Scalpel recovers deleted files from raw disk images"),
            ("timeline-analysis", "MFT timestamps reveal file access patterns"),
            ("incident-response", "KAPE automates triage artifact collection"),
            ("cloud-forensics", "AWS CloudTrail logs all API calls with timestamps"),
            ("iot-forensics", "JTAG extraction dumps firmware from embedded devices"),
            ("anti-forensics", "Timestomping modifies NTFS file timestamps"),
            ("chain-custody", "Evidence bags require tamper-evident seals"),
            ("court-prep", "Expert witnesses explain technical findings to juries"),
            ("hash-verification", "SHA-256 confirms evidence integrity post-acquisition"),
            ("encryption", "BitLocker recovery keys bypass full-disk encryption"),
            ("virtual-machines", "VMDK snapshots preserve volatile system state"),
            ("container-forensics", "Docker layer analysis reveals build history"),
            ("database-forensics", "Transaction logs reconstruct deleted SQL records"),
            ("firmware-analysis", "Binwalk extracts embedded filesystems from firmware"),
        ]
        for topic, fact in facts:
            self.brain.learn(topic, fact, confidence=70)
        alerts = self.brain.third_eye_scan(include_types=["never_reviewed_facts"])
        active = [a for a in alerts if not a.get("suppressed")]
        self.assertTrue(len(active) >= 1)
        self.assertEqual(active[0]["severity"], "MEDIUM")

    def test_detect_stale_merkle(self):
        """Stale merkle DAG -> MEDIUM alert."""
        self.brain.link_init("test-brain")
        # Force stale merkle
        dag = self.brain._merkle_load()
        if not dag:
            dag = {"root": "test", "leaves": []}
        dag["stale"] = True
        self.brain._merkle_save(dag)
        alerts = self.brain.third_eye_scan(include_types=["stale_merkle"])
        active = [a for a in alerts if not a.get("suppressed")]
        self.assertTrue(len(active) >= 1)
        self.assertEqual(active[0]["severity"], "MEDIUM")

    def test_suppress_alert(self):
        """Suppress type, rescan -> alert marked suppressed."""
        self.brain.source_register("suppress-src", "witness")
        self.brain.third_eye_scan()
        self.brain.third_eye_suppress("inactive_sources")
        alerts = self.brain.third_eye_scan(include_types=["inactive_sources"])
        for a in alerts:
            if a["type"] == "inactive_sources":
                self.assertTrue(a["suppressed"])

    def test_watch_lowers_threshold(self):
        """Watch topic -> never_reviewed threshold drops to 10."""
        self.brain.third_eye_watch("watched-topic")
        items = [
            "Chain of custody documentation procedures",
            "Evidence bag labeling and sealing protocol",
            "Digital hash verification using SHA-256",
            "Write blocker deployment for disk imaging",
            "Mobile device Faraday cage isolation",
            "RAM capture using live forensics toolkit",
            "Network traffic baseline comparison method",
            "Registry hive extraction from Windows image",
            "Browser artifact timeline reconstruction",
            "Email header analysis for source tracing",
            "Steganography detection in image files",
            "Log correlation across multiple timestamps",
        ]
        for item in items:
            self.brain.learn("watched-topic", item, confidence=75)
        alerts = self.brain.third_eye_scan(include_types=["never_reviewed_facts"])
        active = [a for a in alerts if not a.get("suppressed")]
        self.assertTrue(len(active) >= 1)

    def test_summary_counts(self):
        """Run scan with multiple alert types -> summary counts correct."""
        self.brain.source_register("summary-src", "informant")
        self.brain._blobs_dir.mkdir(parents=True, exist_ok=True)
        (self.brain._blobs_dir / "abc123.blob").write_bytes(b"data")
        self.brain.third_eye_scan()
        summary = self.brain.third_eye_summary()
        self.assertGreaterEqual(summary["total"], 2)
        self.assertIn("inactive_sources", summary["by_type"])
        self.assertIn("orphaned_blobs", summary["by_type"])

    def test_status_returns_scan_time(self):
        """After scan, status shows last_scan."""
        self.brain.third_eye_scan()
        status = self.brain.third_eye_status()
        self.assertIsNotNone(status["last_scan"])
        self.assertEqual(status["total_scans"], 1)


# ── Tier 31: Diamond Quarantine — Information Safety Net ────────────
class TestDiamondQuarantine(TestDiamondBrainBase):

    def test_prune_quarantines_instead_of_deletes(self):
        """Low-conf old fact -> prune_stale -> fact in quarantine."""
        self.brain.learn("old-topic", "ancient low-conf fact", confidence=10)
        # Backdate the fact
        facts = self.brain._load(self.brain._facts_path)
        for f in facts:
            if "ancient" in f.get("fact", ""):
                f["updated_at"] = "2024-01-01T00:00:00Z"
                f["created_at"] = "2024-01-01T00:00:00Z"
        self.brain._save(self.brain._facts_path, facts)
        removed = self.brain.prune_stale(max_age_days=90, min_confidence=30)
        self.assertGreaterEqual(removed, 1)
        q = self.brain._quarantine_load()
        self.assertTrue(any(e.get("source") == "prune" for e in q))

    def test_forget_sends_to_quarantine(self):
        """forget() -> fact in quarantine AND amnesia log."""
        self.brain.learn("secret-topic", "classified information alpha", confidence=80)
        self.brain.forget("secret-topic", "classified", "no longer needed")
        q = self.brain._quarantine_load()
        self.assertTrue(any(e.get("source") == "forget" for e in q))
        amnesia = self.brain._load(self.brain._amnesia_path)
        self.assertTrue(len(amnesia) >= 1)

    def test_tombstone_sends_to_quarantine(self):
        """crdt_tombstone() -> copy in quarantine."""
        self.brain.learn("ts-topic", "tombstone target fact", confidence=75)
        self.brain.crdt_tombstone("ts-topic", "tombstone target")
        q = self.brain._quarantine_load()
        self.assertTrue(any(e.get("source") == "tombstone" for e in q))

    def test_quarantine_list_and_filter(self):
        """List by batch and status."""
        self.brain.learn("ql-topic", "quarantine list test fact", confidence=80)
        self.brain.forget("ql-topic", "quarantine list", "testing")
        items = self.brain.quarantine_list()
        self.assertTrue(len(items) >= 1)
        self.assertNotIn("original_data", items[0])
        # Filter by status
        holding = self.brain.quarantine_list(status="holding")
        self.assertTrue(all(e.get("status") == "holding" for e in holding))

    def test_quarantine_restore(self):
        """quarantine_restore(id) -> fact back in active facts."""
        self.brain.learn("restore-topic", "restore me please unique fact", confidence=85)
        facts_before = len(self.brain._load(self.brain._facts_path))
        self.brain.forget("restore-topic", "restore me", "testing restore")
        facts_after = len(self.brain._load(self.brain._facts_path))
        self.assertLess(facts_after, facts_before)
        q = self.brain._quarantine_load()
        entry_id = q[-1]["id"]
        result = self.brain.quarantine_restore(entry_id)
        self.assertTrue(result["restored"])
        facts_restored = len(self.brain._load(self.brain._facts_path))
        self.assertEqual(facts_restored, facts_before)

    def test_purge_requires_passphrase(self):
        """Wrong passphrase -> error."""
        result = self.brain.quarantine_purge("2026-W10", "wrong password")
        self.assertEqual(result["error"], "passphrase_mismatch")

    def test_purge_respects_14day_hold(self):
        """Item quarantined today -> purge with correct passphrase -> NOT deleted."""
        self.brain.learn("hold-topic", "hold me tight unique text", confidence=80)
        self.brain.forget("hold-topic", "hold me", "test hold")
        q = self.brain._quarantine_load()
        batch_id = q[-1]["batch_id"]
        result = self.brain.quarantine_purge(batch_id, "PERMANENTLY DELETE")
        self.assertIn("error", result)
        self.assertIn("hold", result["error"])

    def test_purge_eligible_item(self):
        """Backdate quarantined_at to 15 days ago -> purge succeeds."""
        self.brain.learn("eligible-topic", "eligible for deletion unique data", confidence=80)
        self.brain.forget("eligible-topic", "eligible for", "test eligible")
        # Backdate quarantine entry
        q = self.brain._quarantine_load()
        for e in q:
            if "eligible" in e.get("fact_preview", ""):
                e["quarantined_at"] = "2025-01-01T00:00:00Z"
                batch_id = e["batch_id"]
        self.brain._quarantine_save(q)
        result = self.brain.quarantine_purge(batch_id, "PERMANENTLY DELETE",
                                             override=True)
        self.assertGreaterEqual(result.get("purged", 0), 1)

    def test_quarantine_stats(self):
        """Add items from two sources -> stats counts correct."""
        self.brain.learn("stat-topic-1", "stat fact alpha unique one", confidence=80)
        self.brain.learn("stat-topic-2", "stat fact beta unique two", confidence=10)
        self.brain.forget("stat-topic-1", "stat fact alpha", "testing stats")
        # Backdate for prune
        facts = self.brain._load(self.brain._facts_path)
        for f in facts:
            if "stat fact beta" in f.get("fact", ""):
                f["updated_at"] = "2024-01-01T00:00:00Z"
                f["created_at"] = "2024-01-01T00:00:00Z"
        self.brain._save(self.brain._facts_path, facts)
        self.brain.prune_stale(max_age_days=90, min_confidence=30)
        stats = self.brain.quarantine_stats()
        self.assertGreaterEqual(stats["total"], 2)
        self.assertIn("forget", stats["by_source"])
        self.assertIn("prune", stats["by_source"])

    def test_third_eye_quarantine_alert(self):
        """Add item -> third_eye_scan() -> quarantine_pressure alert fires."""
        self.brain.learn("eye-q-topic", "eye quarantine alert fact unique", confidence=80)
        self.brain.forget("eye-q-topic", "eye quarantine", "test alert")
        alerts = self.brain.third_eye_scan(include_types=["quarantine_pressure"])
        active = [a for a in alerts if not a.get("suppressed")]
        self.assertTrue(len(active) >= 1)
        self.assertEqual(active[0]["type"], "quarantine_pressure")


if __name__ == "__main__":
    unittest.main(verbosity=2)
