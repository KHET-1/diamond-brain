"""
================================================================================
  DIAMOND BRAIN — Full Test Suite
================================================================================
  Tests all 70 public methods across all feature domains.
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
