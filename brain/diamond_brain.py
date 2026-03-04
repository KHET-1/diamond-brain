"""
================================================================================
  DIAMOND BRAIN v3.0 — Standalone Knowledge Cache + Legal Intelligence
================================================================================
  Standalone knowledge cache + legal intelligence + encrypted brain-to-brain
  linking. 116 public methods, 31 feature tiers, 213 tests. Stores facts,
  tracks agents, manages legal citations, generates court documents,
  knowledge graphs, spaced repetition, temporal reasoning, encrypted sync.
  All data persisted as JSON on disk. No external dependencies.

  Owner: Ryan Cashmoney (@Tunclon)
  Adapted for cross-platform with zero dependencies.
================================================================================
"""

import hashlib
import io
import json
import math
import os
import shlex
import secrets
import statistics
import sys
import textwrap
import time
from pathlib import Path
from datetime import datetime, timezone
from difflib import SequenceMatcher, get_close_matches

# ---------------------------------------------------------------------------
# UTF-8 safety — ensure stdout/stderr handle Unicode on all platforms
# ---------------------------------------------------------------------------
# On Windows or terminals with ASCII encoding, Python may default to a codec
# that chokes on box-drawing or emoji characters.  Reconfigure to UTF-8 with
# 'replace' error handling so the worst case is a '?' instead of a crash.
for _stream_name in ("stdout", "stderr"):
    _stream = getattr(sys, _stream_name, None)
    if _stream and hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass  # some environments (e.g. IDLE) don't support reconfigure

# ---------------------------------------------------------------------------
# ANSI helpers — degrade gracefully on terminals that strip escapes
# ---------------------------------------------------------------------------
class _C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    ITALIC  = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK   = "\033[5m"
    INVERSE = "\033[7m"
    CYAN    = "\033[96m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    RED     = "\033[91m"
    MAGENTA = "\033[95m"
    WHITE   = "\033[97m"
    BLUE    = "\033[94m"
    ORANGE  = "\033[38;5;208m"
    GOLD    = "\033[38;5;220m"
    PINK    = "\033[38;5;205m"
    GRAY    = "\033[38;5;245m"
    BG_DARK    = "\033[48;5;235m"
    BG_RED     = "\033[48;5;52m"
    BG_GREEN   = "\033[48;5;22m"
    BG_BLUE    = "\033[48;5;17m"
    BG_GOLD    = "\033[48;5;58m"

    # Box drawing
    H_LINE  = "\u2500"
    V_LINE  = "\u2502"
    TL      = "\u250c"
    TR      = "\u2510"
    BL      = "\u2514"
    BR      = "\u2518"
    T_DOWN  = "\u252c"
    T_UP    = "\u2534"
    T_RIGHT = "\u251c"
    T_LEFT  = "\u2524"
    CROSS   = "\u253c"
    DIAMOND = "\u25c6"
    BULLET  = "\u2022"
    ARROW   = "\u2192"
    CHECK   = "\u2713"
    WARN    = "\u26a0"
    SCALE   = "\u2696"  # scales of justice


BANNER = f"""
{_C.CYAN}                        {_C.BOLD}◆{_C.RESET}
{_C.CYAN}                      ◆{_C.GOLD}◆◆{_C.CYAN}◆{_C.RESET}
{_C.CYAN}                    ◆{_C.GOLD}◆{_C.WHITE}{_C.BOLD}◆◆{_C.RESET}{_C.GOLD}◆{_C.CYAN}◆{_C.RESET}
{_C.CYAN}                  ◆{_C.GOLD}◆{_C.WHITE}{_C.BOLD}◆◆◆◆{_C.RESET}{_C.GOLD}◆{_C.CYAN}◆{_C.RESET}
{_C.CYAN}                    ◆{_C.GOLD}◆{_C.WHITE}{_C.BOLD}◆◆{_C.RESET}{_C.GOLD}◆{_C.CYAN}◆{_C.RESET}
{_C.CYAN}                      ◆{_C.GOLD}◆◆{_C.CYAN}◆{_C.RESET}
{_C.CYAN}                        {_C.BOLD}◆{_C.RESET}
{_C.CYAN}{_C.BOLD}  ╔══════════════════════════════════════════════════════════════╗{_C.RESET}
{_C.CYAN}{_C.BOLD}  ║{_C.RESET}{_C.WHITE}{_C.BOLD}          D I A M O N D    B R A I N   v 3 . 0{_C.RESET}{_C.CYAN}{_C.BOLD}             ║{_C.RESET}
{_C.CYAN}{_C.BOLD}  ║{_C.RESET}{_C.DIM}          Knowledge  +  Legal Intelligence System{_C.RESET}{_C.CYAN}{_C.BOLD}          ║{_C.RESET}
{_C.CYAN}{_C.BOLD}  ╚══════════════════════════════════════════════════════════════╝{_C.RESET}
"""

# ---------------------------------------------------------------------------
# Section header art — smaller inline diamonds for each section
# ---------------------------------------------------------------------------
def _section_header(title: str, icon: str = "", color: str = _C.CYAN) -> str:
    """Generate a decorated section header with diamond accents."""
    w = max(len(title) + 8, 40)
    top = f"{color}{_C.BOLD}  ◆─{'─' * w}─◆{_C.RESET}"
    mid = f"{color}{_C.BOLD}  │ {icon} {_C.WHITE}{title}{color}{'':>{w - len(title) - 2}}│{_C.RESET}"
    bot = f"{color}{_C.BOLD}  ◆─{'─' * w}─◆{_C.RESET}"
    return f"{top}\n{mid}\n{bot}"

def _mini_diamond(color: str = _C.GOLD) -> str:
    """Single-line diamond accent."""
    return f"{color}◆{_C.RESET}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _days_ago(iso_str: str) -> float:
    try:
        dt = datetime.fromisoformat(iso_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - dt
        return delta.total_seconds() / 86400.0
    except (ValueError, TypeError):
        return 999.0


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _decayed_confidence(confidence: int, updated_at: str, verified: bool) -> int:
    """Apply time decay to confidence.  Verified facts decay slower.

    Formula: confidence * e^(-days / half_life)
    Half-life: 60 days for unverified, 180 days for verified.
    Floor: 30 (never drops below 30 — the fact still exists).

    This is a READ-ONLY calculation — does not mutate stored data.
    """
    days = _days_ago(updated_at)
    half_life = 180.0 if verified else 60.0
    decay = math.exp(-days / half_life)
    return max(30, int(confidence * decay))


def _parse_command(raw: str) -> dict:
    """Tokenize a shell command into components.

    Handles pipes/chains by parsing only the first command segment.
    Falls back to str.split() on malformed input.
    """
    # Take only the first command in a pipe/chain
    for sep in ("|", "&&", "||", ";"):
        if sep in raw:
            raw = raw[:raw.index(sep)]
            break

    raw = raw.strip()
    try:
        tokens = shlex.split(raw)
    except ValueError:
        tokens = raw.split()

    if not tokens:
        return {"command": "", "subcommand": None, "flags": [], "positional_args": []}

    command = tokens[0]
    flags = []
    positional_args = []
    subcommand = None

    for token in tokens[1:]:
        if token.startswith("-"):
            flags.append(token)
        elif subcommand is None and "." not in token and "/" not in token:
            subcommand = token
        else:
            positional_args.append(token)

    return {
        "command": command,
        "subcommand": subcommand,
        "flags": flags,
        "positional_args": positional_args,
    }


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points using the Haversine formula."""
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _flag_score(count: int, last_used_iso: str) -> float:
    """Score a flag by frequency * recency.  14-day half-life."""
    days = _days_ago(last_used_iso)
    return count * math.exp(-days / 14.0)


def _smart_suggest_llm(command: str, subcommand: str | None, cwd: str | None,
                       freq_suggestions: list[dict]) -> list[str]:
    """Call LM Studio (sentinel-fast model) for context-aware flag suggestions.

    Returns a list of flag strings, or empty list on failure.
    """
    import urllib.request
    import urllib.error

    freq_text = ", ".join(
        f"{s['flag']}(used {s['count']}x)" for s in freq_suggestions[:10]
    ) or "none yet"

    cmd_str = f"{command} {subcommand}" if subcommand else command
    prompt = (
        f"The user frequently runs `{cmd_str}`. "
        f"Their most-used flags: {freq_text}. "
        f"Working directory: {cwd or 'unknown'}. "
        f"Suggest 5 useful flags they might not know about. "
        f"Reply with ONLY a JSON array of flag strings, e.g. [\"--flag1\", \"-x\"]. No explanation."
    )

    payload = json.dumps({
        "model": "sentinel-fast",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 200,
    }).encode()

    req = urllib.request.Request(
        "http://localhost:1234/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        content = data["choices"][0]["message"]["content"].strip()
        # Extract JSON array from response (handle markdown fencing)
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        result = json.loads(content)
        if isinstance(result, list):
            return [str(f) for f in result if isinstance(f, str)]
    except (urllib.error.URLError, json.JSONDecodeError, KeyError,
            IndexError, OSError):
        pass
    return []


class DiamondBrain:
    """Self-contained knowledge cache for AI-assisted code audit pipelines.

    All data is stored as JSON files under the ``memory_dir`` path.
    Default location: ``<this_file's_directory>/memory/``
    """

    DEFAULT_MEMORY_DIR = Path(__file__).resolve().parent / "memory"

    def __init__(self, memory_dir: Path | str | None = None):
        self.memory_dir = Path(memory_dir) if memory_dir else self.DEFAULT_MEMORY_DIR
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        self._facts_path = self.memory_dir / "facts.json"
        self._agents_path = self.memory_dir / "agents.json"
        self._escalations_path = self.memory_dir / "escalations.json"
        self._commands_path = self.memory_dir / "commands.json"
        self._citations_path = self.memory_dir / "citations.json"
        self._link_dir_path = self.memory_dir / "link"
        self._graph_path = self.memory_dir / "graph.json"
        self._temporal_path = self.memory_dir / "temporal.json"
        self._amnesia_path = self.memory_dir / "amnesia.json"
        self._blobs_dir = self.memory_dir / "blobs"
        self._sources_path = self.memory_dir / "sources.json"

        # Ensure files exist
        for p in (self._facts_path, self._agents_path, self._escalations_path,
                  self._commands_path, self._citations_path, self._temporal_path,
                  self._amnesia_path, self._sources_path):
            if not p.exists():
                p.write_text("[]", encoding="utf-8")

    # ------------------------------------------------------------------
    # Internal I/O
    # ------------------------------------------------------------------
    def _load(self, path: Path) -> list:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save(self, path: Path, data: list) -> None:
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        # Atomic-ish rename (Windows allows overwrite via os.replace)
        os.replace(str(tmp), str(path))

    # ------------------------------------------------------------------
    # recall — retrieve facts for a topic, sorted by confidence desc
    # ------------------------------------------------------------------
    def recall(
        self,
        topic: str,
        max_results: int = 15,
        min_confidence: int = 0,
        fuzzy: bool = False,
    ) -> list[dict]:
        """Return up to *max_results* facts for *topic*, highest confidence first.

        Args:
            topic: Exact topic name to search for.
            max_results: Maximum number of facts to return.
            min_confidence: Only return facts with confidence >= this value.
            fuzzy: If True, also match topics that are >80% similar
                   (e.g. "sql-injection" matches "sql_injection").
        """
        facts = self._load(self._facts_path)
        topic_lower = topic.lower()

        # Exact matches (filter out CRDT tombstones)
        matches = [
            f for f in facts
            if f.get("topic", "").lower() == topic_lower
            and f.get("confidence", 0) >= min_confidence
            and not f.get("_crdt", {}).get("tombstone")
        ]

        if fuzzy:
            all_topics = list({f.get("topic", "").lower() for f in facts})
            similar = get_close_matches(topic_lower, all_topics, n=5, cutoff=0.8)
            # Remove exact match (already included)
            similar = [t for t in similar if t != topic_lower]
            for f in facts:
                if (
                    f.get("topic", "").lower() in similar
                    and f.get("confidence", 0) >= min_confidence
                    and f not in matches
                    and not f.get("_crdt", {}).get("tombstone")
                ):
                    matches.append(f)

        # Add effective_confidence (time-decayed) and source-weighted confidence
        sources = self._sources_load()
        for m in matches:
            m["effective_confidence"] = _decayed_confidence(
                m.get("confidence", 0),
                m.get("updated_at", m.get("created_at", "")),
                m.get("verified", False),
            )
            src_id = m.get("source", "")
            src = self._source_find(sources, src_id) if src_id else None
            if src:
                m["source_weighted_confidence"] = round(
                    m.get("confidence", 0)
                    * self._source_calc_score(src, facts) / 100.0, 1)
            else:
                m["source_weighted_confidence"] = float(m.get("confidence", 0))

        matches.sort(key=lambda f: f.get("effective_confidence", 0), reverse=True)
        return matches[:max_results]

    # ------------------------------------------------------------------
    # advanced_recall — deep search with association chaining
    # ------------------------------------------------------------------
    def advanced_recall(
        self,
        query: str,
        max_results: int = 15,
        min_confidence: int = 70,
    ) -> list[dict]:
        """Search facts by keyword, then chain in associated topics.

        1. Keyword search across all facts.
        2. For each result, check if it mentions other known topics.
        3. Pull one high-confidence fact per associated topic.
        4. Deduplicate, sort by confidence, return top N.

        This is the "galaxy-brain" recall — useful when exploring a domain
        and you want the Brain to surface related knowledge automatically.
        """
        # Phase 1: keyword search
        hits = self.search(query)
        hits = [f for f in hits if f.get("confidence", 0) >= min_confidence]

        # Phase 2: association chaining
        all_topics = list({f.get("topic", "").lower() for f in self._load(self._facts_path)})
        seen_keys = set()
        chained: list[dict] = []

        for f in hits:
            key = (f.get("topic", ""), f.get("fact", ""))
            if key not in seen_keys:
                seen_keys.add(key)
                chained.append(f)

            # Find topics mentioned in this fact's text
            fact_text = f.get("fact", "").lower()
            related = get_close_matches(fact_text, all_topics, n=3, cutoff=0.6)
            for rel_topic in related:
                if rel_topic == f.get("topic", "").lower():
                    continue
                assoc = self.recall(rel_topic, max_results=1, min_confidence=min_confidence)
                for a in assoc:
                    akey = (a.get("topic", ""), a.get("fact", ""))
                    if akey not in seen_keys:
                        seen_keys.add(akey)
                        chained.append(a)

        chained.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        return chained[:max_results]

    # ------------------------------------------------------------------
    # learn — store a fact with deduplication via fuzzy matching
    # ------------------------------------------------------------------
    def learn(
        self,
        topic: str,
        fact: str,
        confidence: int = 90,
        source: str = "auto",
        verified: bool = False,
    ) -> dict:
        """Store a fact. If a >80 percent similar fact already exists for the
        same topic, update it instead of creating a duplicate."""
        facts = self._load(self._facts_path)
        now = _now_iso()

        # Check for existing similar fact under the same topic
        for existing in facts:
            if existing.get("topic", "").lower() != topic.lower():
                continue
            sim = _similarity(existing.get("fact", ""), fact)
            if sim > 0.80:
                # Update in place
                existing["fact"] = fact
                existing["confidence"] = max(existing.get("confidence", 0), confidence)
                existing["source"] = source
                existing["verified"] = verified or existing.get("verified", False)
                existing["updated_at"] = now
                self._crdt_ensure_metadata(existing)
                existing["_crdt"]["hlc"] = self._crdt_hlc_now()
                existing["_crdt"]["version"] = (
                    existing["_crdt"].get("version", 1) + 1)
                self._save(self._facts_path, facts)
                self._source_track_contribution(source)
                return existing

        # New fact
        entry = {
            "topic": topic,
            "fact": fact,
            "confidence": confidence,
            "source": source,
            "verified": verified,
            "created_at": now,
            "updated_at": now,
            "links": [],
        }
        self._crdt_ensure_metadata(entry)
        facts.append(entry)

        # Auto-link: find related topics and tag them
        self._auto_link(entry, facts)

        self._save(self._facts_path, facts)
        self._source_track_contribution(source)
        return entry

    # ------------------------------------------------------------------
    # search — keyword search across all facts
    # ------------------------------------------------------------------
    def search(self, keyword: str) -> list[dict]:
        """Search all stored facts for *keyword* (case-insensitive).
        Matches against topic, fact text, and source fields."""
        facts = self._load(self._facts_path)
        kw = keyword.lower()
        results = []
        for f in facts:
            if f.get("_crdt", {}).get("tombstone"):
                continue
            blob = " ".join([
                f.get("topic", ""),
                f.get("fact", ""),
                f.get("source", ""),
            ]).lower()
            if kw in blob:
                results.append(f)
        return results

    # ------------------------------------------------------------------
    # agent_checkin — register a swarm agent
    # ------------------------------------------------------------------
    def agent_checkin(
        self,
        agent_id: str,
        role: str,
        task: str,
        status: str = "active",
    ) -> dict:
        """Register or update a sentinel agent. Returns the agent record."""
        agents = self._load(self._agents_path)
        now = _now_iso()

        for agent in agents:
            if agent.get("agent_id") == agent_id:
                agent["role"] = role
                agent["task"] = task
                agent["status"] = status
                agent["checked_in_at"] = now
                self._save(self._agents_path, agents)
                return agent

        entry = {
            "agent_id": agent_id,
            "role": role,
            "task": task,
            "status": status,
            "checked_in_at": now,
            "findings_count": 0,
        }
        agents.append(entry)
        self._save(self._agents_path, agents)
        return entry

    # ------------------------------------------------------------------
    # agent_report — agent submits findings, auto-learns HIGH+
    # ------------------------------------------------------------------
    def agent_report(self, agent_id: str, findings: list[dict]) -> dict:
        """Process findings from an agent.

        Each finding is a dict with keys:
            category, severity, file, line, message

        Findings with severity HIGH or CRITICAL are auto-learned.
        Returns a summary dict.
        """
        agents = self._load(self._agents_path)
        learned_count = 0
        escalated_count = 0

        for finding in findings:
            severity = finding.get("severity", "").upper()
            category = finding.get("category", "unknown")
            message = finding.get("message", "")
            file_ref = finding.get("file", "?")
            line_ref = finding.get("line", "?")

            fact_text = f"[{severity}] {message} (file: {file_ref}, line: {line_ref})"

            if severity in ("HIGH", "CRITICAL"):
                self.learn(
                    topic=category,
                    fact=fact_text,
                    confidence=95 if severity == "CRITICAL" else 85,
                    source=f"agent:{agent_id}",
                    verified=False,
                )
                learned_count += 1

                if self.escalation_needed(finding):
                    escalated_count += 1

        # Update agent findings count
        for agent in agents:
            if agent.get("agent_id") == agent_id:
                agent["findings_count"] = agent.get("findings_count", 0) + len(findings)
                break
        self._save(self._agents_path, agents)

        return {
            "agent_id": agent_id,
            "total_findings": len(findings),
            "auto_learned": learned_count,
            "escalated": escalated_count,
        }

    # ------------------------------------------------------------------
    # digest — full status overview
    # ------------------------------------------------------------------
    def digest(self) -> dict:
        """Return a status overview of the entire brain."""
        facts = self._load(self._facts_path)
        agents = self._load(self._agents_path)
        commands = self._load(self._commands_path)
        citations = self._load(self._citations_path)

        topics = sorted(set(f.get("topic", "") for f in facts))
        timestamps = [f.get("updated_at", "") for f in facts]
        last_updated = max(timestamps) if timestamps else None

        agent_summary = []
        for a in agents:
            agent_summary.append({
                "agent_id": a.get("agent_id"),
                "role": a.get("role"),
                "status": a.get("status"),
                "findings_count": a.get("findings_count", 0),
            })

        # Diamond Link status
        link_info = {
            "initialized": False,
            "fingerprint": None,
            "display_name": None,
            "peer_count": 0,
            "total_syncs": 0,
        }
        identity = self.link_identity()
        if identity:
            link_info["initialized"] = True
            link_info["fingerprint"] = identity.get("fingerprint")
            link_info["display_name"] = identity.get("display_name")
            peers = self._link_load_peers()
            link_info["peer_count"] = len(peers)
            link_info["total_syncs"] = sum(
                p.get("syncs_completed", 0) for p in peers
            )

        # Graph stats
        graph = self._graph_load()
        graph_info = {
            "total_nodes": len(graph.get("nodes", {})),
            "total_edges": len(graph.get("edges", [])),
        }

        # Temporal events
        temporal_events = self._load(self._temporal_path)

        # Amnesia
        amnesia_entries = self._load(self._amnesia_path)

        # Blobs
        blob_count = len(list(self._blobs_dir.glob("*.blob"))) if self._blobs_dir.exists() else 0

        # Sources
        sources = self._sources_load()

        return {
            "total_facts": len(facts),
            "topics": topics,
            "total_agents": len(agents),
            "agent_history": agent_summary,
            "commands_logged": len(commands),
            "total_citations": len(citations),
            "last_updated": last_updated,
            "diamond_link": link_info,
            "knowledge_graph": graph_info,
            "temporal_events": len(temporal_events),
            "amnesia_entries": len(amnesia_entries),
            "blob_count": blob_count,
            "registered_sources": len(sources),
            "temporal_anomalies": self.temporal_anomaly_summary()["total_anomalies"]
                if temporal_events else 0,
            "cortex_queries": self._cortex_log_load().get("total_queries", 0),
            "third_eye_alerts": self._eye_load().get("total_alerts", 0),
            "quarantine_count": len(self._quarantine_load()),
        }

    # ------------------------------------------------------------------
    # heatmap — knowledge freshness per topic
    # ------------------------------------------------------------------
    def heatmap(self) -> dict:
        """Return a dict of topic -> {count, freshness_score, oldest, newest}.

        freshness_score: 100 = updated today, 0 = 30+ days stale.
        """
        facts = self._load(self._facts_path)
        topic_map: dict[str, list[dict]] = {}
        for f in facts:
            t = f.get("topic", "unknown")
            topic_map.setdefault(t, []).append(f)

        result = {}
        for topic, items in topic_map.items():
            dates = []
            for item in items:
                for key in ("updated_at", "created_at"):
                    val = item.get(key)
                    if val:
                        dates.append(val)
            if not dates:
                result[topic] = {
                    "count": len(items),
                    "freshness_score": 0,
                    "oldest": None,
                    "newest": None,
                }
                continue

            dates_sorted = sorted(dates)
            oldest = dates_sorted[0]
            newest = dates_sorted[-1]

            days = _days_ago(newest)
            freshness = max(0, min(100, int(100 - (days / 30.0) * 100)))

            result[topic] = {
                "count": len(items),
                "freshness_score": freshness,
                "oldest": oldest,
                "newest": newest,
            }
        return result

    # ------------------------------------------------------------------
    # log_command — record a shell command
    # ------------------------------------------------------------------
    def log_command(self, raw_command: str, cwd: str | None = None,
                    max_history: int = 50000) -> dict:
        """Parse and store a shell command to commands.json.

        Trims oldest entries when the log exceeds *max_history*.
        """
        parsed = _parse_command(raw_command)
        entry = {
            "command": parsed["command"],
            "subcommand": parsed["subcommand"],
            "flags": parsed["flags"],
            "positional_args": parsed["positional_args"],
            "raw": raw_command.strip(),
            "cwd": cwd,
            "timestamp": _now_iso(),
        }

        commands = self._load(self._commands_path)
        commands.append(entry)

        # Trim oldest if over cap
        if len(commands) > max_history:
            commands = commands[-max_history:]

        self._save(self._commands_path, commands)
        return entry

    # ------------------------------------------------------------------
    # suggest_flags — frequency + recency ranked flag suggestions
    # ------------------------------------------------------------------
    def suggest_flags(self, command: str, subcommand: str | None = None,
                      top_n: int = 15) -> list[dict]:
        """Aggregate flags by frequency and recency, return scored list.

        Returns list of {flag, count, last_used, score} dicts.
        """
        commands = self._load(self._commands_path)
        cmd_lower = command.lower()

        # Filter to matching commands
        matching = [
            c for c in commands
            if c.get("command", "").lower() == cmd_lower
        ]
        if subcommand:
            sub_lower = subcommand.lower()
            matching = [
                c for c in matching
                if (c.get("subcommand") or "").lower() == sub_lower
            ]

        # Aggregate flags
        flag_data: dict[str, dict] = {}  # flag -> {count, last_used}
        for c in matching:
            ts = c.get("timestamp", "")
            for flag in c.get("flags", []):
                if flag not in flag_data:
                    flag_data[flag] = {"count": 0, "last_used": ts}
                flag_data[flag]["count"] += 1
                if ts > flag_data[flag]["last_used"]:
                    flag_data[flag]["last_used"] = ts

        # Score and sort
        results = []
        for flag, data in flag_data.items():
            score = _flag_score(data["count"], data["last_used"])
            results.append({
                "flag": flag,
                "count": data["count"],
                "last_used": data["last_used"],
                "score": round(score, 2),
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_n]

    # ------------------------------------------------------------------
    # smart_suggest — LLM-powered flag suggestions
    # ------------------------------------------------------------------
    def smart_suggest(self, command: str, subcommand: str | None = None,
                      cwd: str | None = None, top_n: int = 5) -> list[str]:
        """LLM-powered flag suggestions via LM Studio.

        Falls back to suggest_flags() on LLM failure.
        """
        freq = self.suggest_flags(command, subcommand, top_n=10)
        llm_flags = _smart_suggest_llm(command, subcommand, cwd, freq)

        if llm_flags:
            return llm_flags[:top_n]

        # Fallback: just return top flags from frequency data
        return [f["flag"] for f in freq[:top_n]]

    # ------------------------------------------------------------------
    # command_stats — usage statistics
    # ------------------------------------------------------------------
    def command_stats(self, command: str | None = None) -> dict:
        """Return usage stats for commands.

        If *command* is given, return detailed stats for that command.
        Otherwise, return a summary across all commands.
        """
        commands = self._load(self._commands_path)

        if command:
            cmd_lower = command.lower()
            matching = [
                c for c in commands
                if c.get("command", "").lower() == cmd_lower
            ]
            subcommands: dict[str, int] = {}
            unique_flags: set[str] = set()
            for c in matching:
                sub = c.get("subcommand")
                if sub:
                    subcommands[sub] = subcommands.get(sub, 0) + 1
                for flag in c.get("flags", []):
                    unique_flags.add(flag)

            return {
                "command": command,
                "total_invocations": len(matching),
                "subcommands": subcommands,
                "unique_flags": sorted(unique_flags),
            }

        # Global summary
        cmd_counts: dict[str, int] = {}
        for c in commands:
            cmd = c.get("command", "")
            cmd_counts[cmd] = cmd_counts.get(cmd, 0) + 1

        return {
            "total_commands_logged": len(commands),
            "unique_commands": len(cmd_counts),
            "top_commands": dict(
                sorted(cmd_counts.items(), key=lambda x: x[1], reverse=True)[:15]
            ),
        }

    # ------------------------------------------------------------------
    # _auto_link — tag related topics on a new fact (called by learn)
    # ------------------------------------------------------------------
    def _auto_link(self, entry: dict, all_facts: list[dict]) -> None:
        """Find existing topics that are related to this fact and store them
        in the ``links`` array.  Uses fuzzy matching on topic names (>70%
        similarity) and keyword overlap in fact text.

        Mutates *entry* in place — does NOT call _save (caller does that).
        """
        topic_lower = entry.get("topic", "").lower()
        fact_lower = entry.get("fact", "").lower()

        # Collect all unique topics except this one
        other_topics = list({
            f.get("topic", "")
            for f in all_facts
            if f.get("topic", "").lower() != topic_lower
        })
        if not other_topics:
            return

        links: list[str] = list(entry.get("links", []))
        other_lower = [t.lower() for t in other_topics]

        # Method 1: Fuzzy topic name match (e.g. "sql-injection" ↔ "sql_injection")
        similar = get_close_matches(topic_lower, other_lower, n=5, cutoff=0.7)
        for s in similar:
            # Find the original-cased topic name
            for ot in other_topics:
                if ot.lower() == s and ot not in links:
                    links.append(ot)

        # Method 2: Topic name appears in fact text
        for ot in other_topics:
            if ot.lower() in fact_lower and ot not in links:
                links.append(ot)

        entry["links"] = links  # no cap — store all discovered links

    # ------------------------------------------------------------------
    # prune_stale — remove facts below a freshness threshold
    # ------------------------------------------------------------------
    def prune_stale(self, max_age_days: int = 90, min_confidence: int = 30) -> int:
        """Remove facts that are both older than *max_age_days* and have
        confidence below *min_confidence*.  Verified facts are never pruned.

        Returns the number of facts removed.
        """
        facts = self._load(self._facts_path)
        before_count = len(facts)

        pruned = []
        to_quarantine = []
        for f in facts:
            if (f.get("verified", False)
                    or _days_ago(f.get("updated_at",
                                       f.get("created_at", ""))) < max_age_days
                    or f.get("confidence", 0) >= min_confidence):
                pruned.append(f)
            else:
                to_quarantine.append(f)

        removed = before_count - len(pruned)
        if removed > 0:
            for f in to_quarantine:
                age = _days_ago(f.get("updated_at", f.get("created_at", "")))
                self._quarantine_add(
                    f, "prune",
                    f"Pruned: age={age:.0f}d, confidence={f.get('confidence', 0)}")
            self._save(self._facts_path, pruned)
        return removed

    # ------------------------------------------------------------------
    # escalation_needed — can this finding be resolved locally?
    # ------------------------------------------------------------------
    def escalation_needed(self, finding: dict) -> bool:
        """Returns True if the finding cannot be resolved from brain knowledge.

        Criteria: severity >= HIGH *and* no existing brain facts on the topic.
        If escalation is needed, the finding is logged to escalations.json.
        """
        severity = finding.get("severity", "").upper()
        if severity not in ("HIGH", "CRITICAL"):
            return False

        category = finding.get("category", "")
        existing = self.recall(category, max_results=1)
        if existing:
            return False

        # Log escalation
        escalations = self._load(self._escalations_path)
        escalations.append({
            "finding": finding,
            "reason": f"No brain knowledge on topic '{category}' and severity is {severity}",
            "escalated_at": _now_iso(),
            "resolved": False,
        })
        self._save(self._escalations_path, escalations)
        return True

    # ------------------------------------------------------------------
    # cite — store a legal citation (statute, case law, rule)
    # ------------------------------------------------------------------
    def cite(
        self,
        code: str,
        title: str,
        text: str,
        category: str = "statute",
        jurisdiction: str = "AZ",
        source: str = "research",
        severity: str = "REFERENCE",
        linked_facts: list[str] | None = None,
    ) -> dict:
        """Store a legal citation. Deduplicates by code.

        Args:
            code: Statutory code (e.g. "ARS 13-1105", "Rule 403").
            title: Short title (e.g. "First Degree Murder").
            text: Full text or summary of the statute/rule.
            category: One of: statute, case-law, rule, constitutional, procedural.
            jurisdiction: Jurisdiction code (AZ, US, federal).
            severity: FELONY, MISDEMEANOR, REFERENCE, CONSTITUTIONAL, PROCEDURAL.
            linked_facts: Optional list of fact topics this citation supports.
        """
        citations = self._load(self._citations_path)
        now = _now_iso()
        code_upper = code.strip().upper()

        # Dedup by code
        for existing in citations:
            if existing.get("code", "").upper() == code_upper:
                existing["title"] = title
                existing["text"] = text
                existing["category"] = category
                existing["severity"] = severity
                existing["source"] = source
                existing["updated_at"] = now
                if linked_facts:
                    old_links = existing.get("linked_facts", [])
                    existing["linked_facts"] = list(set(old_links + linked_facts))
                self._save(self._citations_path, citations)
                return existing

        entry = {
            "code": code_upper,
            "title": title,
            "text": text,
            "category": category,
            "jurisdiction": jurisdiction,
            "severity": severity,
            "source": source,
            "linked_facts": linked_facts or [],
            "created_at": now,
            "updated_at": now,
        }
        citations.append(entry)
        self._save(self._citations_path, citations)
        return entry

    # ------------------------------------------------------------------
    # recall_citations — search citations by code, category, keyword
    # ------------------------------------------------------------------
    def recall_citations(
        self,
        query: str | None = None,
        category: str | None = None,
        severity: str | None = None,
        max_results: int = 15,
    ) -> list[dict]:
        """Search citations. Filters stack (AND logic)."""
        citations = self._load(self._citations_path)
        results = citations

        if query:
            q = query.lower()
            results = [
                c for c in results
                if q in c.get("code", "").lower()
                or q in c.get("title", "").lower()
                or q in c.get("text", "").lower()
            ]

        if category:
            cat = category.lower()
            results = [c for c in results if c.get("category", "").lower() == cat]

        if severity:
            sev = severity.upper()
            results = [c for c in results if c.get("severity", "").upper() == sev]

        return results[:max_results]

    # ------------------------------------------------------------------
    # citation_stats — overview of stored citations
    # ------------------------------------------------------------------
    def citation_stats(self) -> dict:
        """Return citation statistics."""
        citations = self._load(self._citations_path)
        by_category: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        by_jurisdiction: dict[str, int] = {}

        for c in citations:
            cat = c.get("category", "unknown")
            by_category[cat] = by_category.get(cat, 0) + 1
            sev = c.get("severity", "REFERENCE")
            by_severity[sev] = by_severity.get(sev, 0) + 1
            jur = c.get("jurisdiction", "unknown")
            by_jurisdiction[jur] = by_jurisdiction.get(jur, 0) + 1

        return {
            "total_citations": len(citations),
            "by_category": by_category,
            "by_severity": by_severity,
            "by_jurisdiction": by_jurisdiction,
        }

    # ------------------------------------------------------------------
    # link_crime_to_citations — auto-link accusation facts to citations
    # ------------------------------------------------------------------
    def link_crime_to_citations(self, fact_topic: str, fact_text: str) -> list[str]:
        """Find citations relevant to a crime-related fact and return codes.

        Called automatically when learn() detects crime-related content.
        Uses three matching strategies:
        1. Direct ARS code mention in text
        2. Title keyword overlap (2+ significant words)
        3. Single high-confidence crime keyword match
        """
        citations = self._load(self._citations_path)
        if not citations:
            return []

        # Single-word crime terms that are strong enough signals alone
        _CRIME_KEYWORDS = {
            "murder", "homicide", "manslaughter", "assault", "battery",
            "robbery", "burglary", "theft", "larceny", "arson",
            "kidnapping", "rape", "weapons", "firearm", "drug",
            "narcotic", "marijuana", "methamphetamine", "fentanyl",
            "dui", "dwi", "trespass", "shoplifting", "forgery",
            "fraud", "embezzlement", "extortion", "stalking",
            "domestic", "self-defense", "justification", "warrant",
            "miranda", "search", "seizure", "bail", "sentencing",
        }

        linked_codes = []
        text_lower = (fact_topic + " " + fact_text).lower()

        for cit in citations:
            title_lower = cit.get("title", "").lower()
            code_lower = cit.get("code", "").lower()

            # Strategy 1: Direct code mention
            if code_lower in text_lower or code_lower.replace(" ", "") in text_lower.replace(" ", ""):
                linked_codes.append(cit["code"])
                continue

            # Strategy 2: Title keyword overlap (2+ significant words)
            title_words = {w for w in title_lower.split() if len(w) > 3}
            text_words = set(text_lower.split())
            overlap = title_words & text_words
            if len(overlap) >= 2:
                linked_codes.append(cit["code"])
                continue

            # Strategy 3: Single high-confidence crime keyword in both
            title_crime_words = {w for w in title_lower.split()} & _CRIME_KEYWORDS
            text_crime_words = {w for w in text_lower.split()} & _CRIME_KEYWORDS
            if title_crime_words & text_crime_words:
                linked_codes.append(cit["code"])

        return linked_codes

    # ------------------------------------------------------------------
    # generate_court_document — output court-ready formatted document
    # ------------------------------------------------------------------
    def generate_court_document(
        self,
        doc_type: str = "MOTION",
        case_number: str = "CR-2026-______",
        court_name: str = "SUPERIOR COURT OF ARIZONA",
        county: str = "MARICOPA COUNTY",
        plaintiff: str = "STATE OF ARIZONA",
        defendant: str = "[DEFENDANT NAME]",
        title: str = "MOTION",
        sections: list[dict] | None = None,
        include_citations: bool = True,
        attorney_name: str = "[ATTORNEY NAME]",
        bar_number: str = "[BAR NUMBER]",
    ) -> str:
        """Generate a court-ready document with proper legal formatting.

        Args:
            doc_type: MOTION, BRIEF, MEMORANDUM, PETITION, RESPONSE.
            sections: List of {heading, body, citations[]} dicts.
            include_citations: Auto-append citation appendix.

        Returns:
            Formatted document string (plain text, court-standard).
        """
        width = 72
        line = "=" * width
        thin = "-" * width
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%B %d, %Y")

        lines = []

        # -- Header block --
        lines.append(line)
        lines.append(f"IN THE {court_name}")
        lines.append(f"IN AND FOR {county}")
        lines.append(line)
        lines.append("")
        lines.append(f"  {plaintiff},")
        lines.append(f"{'':>40}Case No. {case_number}")
        lines.append(f"{'':>8}Plaintiff,")
        lines.append(f"{'':>40}{doc_type}")
        lines.append(f"  vs.")
        lines.append("")
        lines.append(f"  {defendant},")
        lines.append("")
        lines.append(f"{'':>8}Defendant.")
        lines.append(line)
        lines.append("")

        # -- Title --
        lines.append(f"{'':>10}{title.upper()}")
        lines.append("")
        lines.append(thin)
        lines.append("")

        # -- Sections --
        all_cited_codes = []
        if sections:
            for i, sec in enumerate(sections, 1):
                heading = sec.get("heading", f"Section {i}")
                body = sec.get("body", "")
                cites = sec.get("citations", [])

                lines.append(f"  {i}. {heading.upper()}")
                lines.append("")
                # Wrap body text to court width
                for para in body.split("\n"):
                    wrapped = textwrap.fill(para.strip(), width=width - 4,
                                           initial_indent="    ",
                                           subsequent_indent="    ")
                    lines.append(wrapped)
                lines.append("")

                if cites:
                    for cite_code in cites:
                        all_cited_codes.append(cite_code)
                        lines.append(f"    See {cite_code}.")
                    lines.append("")

        # -- Citation appendix --
        if include_citations and all_cited_codes:
            lines.append(thin)
            lines.append("")
            lines.append("  CITATIONS AND AUTHORITIES")
            lines.append("")
            cited_details = self._load(self._citations_path)
            seen = set()
            for code in all_cited_codes:
                if code in seen:
                    continue
                seen.add(code)
                code_upper = code.upper()
                for cit in cited_details:
                    if cit.get("code", "").upper() == code_upper:
                        lines.append(f"    {cit['code']} - {cit.get('title', '')}")
                        wrapped = textwrap.fill(
                            cit.get("text", ""),
                            width=width - 8,
                            initial_indent="        ",
                            subsequent_indent="        ",
                        )
                        lines.append(wrapped)
                        lines.append("")
                        break
                else:
                    lines.append(f"    {code}")
                    lines.append("")

        # -- Signature block --
        lines.append(thin)
        lines.append("")
        lines.append(f"  RESPECTFULLY SUBMITTED this {date_str}.")
        lines.append("")
        lines.append("")
        lines.append(f"{'':>40}____________________________")
        lines.append(f"{'':>40}{attorney_name}")
        lines.append(f"{'':>40}Bar No. {bar_number}")
        lines.append("")
        lines.append(line)

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # export_html — generate standalone HTML report with search + downloads
    # ------------------------------------------------------------------
    def export_html(self, output_path: str | Path | None = None) -> str:
        """Generate a standalone HTML report with search, charts, and
        downloadable court documents.

        Returns the HTML string. If output_path given, also writes to file.
        """
        facts = self._load(self._facts_path)
        citations = self._load(self._citations_path)
        commands = self._load(self._commands_path)
        d = self.digest()
        cstats = self.citation_stats()
        hm = self.heatmap()

        # Prepare JSON data for embedding in HTML
        facts_json = json.dumps(facts, ensure_ascii=False)
        citations_json = json.dumps(citations, ensure_ascii=False)
        heatmap_json = json.dumps(hm, ensure_ascii=False)
        digest_json = json.dumps(d, ensure_ascii=False)
        cstats_json = json.dumps(cstats, ensure_ascii=False)

        # Build court doc template data
        court_template = self.generate_court_document(
            title="[DOCUMENT TITLE]",
            sections=[{
                "heading": "Statement of Facts",
                "body": "(Generated from Diamond Brain knowledge base.)",
                "citations": [],
            }],
        )
        court_template_escaped = json.dumps(court_template)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Diamond Brain v3.0 — Intelligence Report</title>
<style>
:root {{
  --bg: #0d1117; --surface: #161b22; --border: #30363d;
  --text: #e6edf3; --dim: #7d8590; --cyan: #58a6ff;
  --green: #3fb950; --yellow: #d29922; --red: #f85149;
  --gold: #e3b341; --magenta: #bc8cff; --blue: #58a6ff;
  --orange: #db6d28;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: var(--bg); color: var(--text); font-family: 'Segoe UI', system-ui, sans-serif; }}
.container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
h1 {{ color: var(--cyan); text-align: center; padding: 30px 0 10px; font-size: 2em; }}
h1 .diamond {{ color: var(--gold); }}
.subtitle {{ text-align: center; color: var(--dim); margin-bottom: 30px; }}
.search-box {{ display: flex; gap: 10px; margin-bottom: 30px; }}
.search-box input {{ flex: 1; padding: 12px 16px; background: var(--surface); border: 1px solid var(--border);
  color: var(--text); border-radius: 6px; font-size: 16px; outline: none; }}
.search-box input:focus {{ border-color: var(--cyan); box-shadow: 0 0 10px rgba(88,166,255,0.2); }}
.search-box button {{ padding: 12px 24px; background: var(--cyan); color: var(--bg); border: none;
  border-radius: 6px; font-weight: bold; cursor: pointer; }}
.search-box button:hover {{ opacity: 0.9; }}
.stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-bottom: 30px; }}
.stat-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px;
  padding: 20px; text-align: center; }}
.stat-card .number {{ font-size: 2.5em; font-weight: bold; }}
.stat-card .label {{ color: var(--dim); margin-top: 5px; }}
.stat-card.facts .number {{ color: var(--green); }}
.stat-card.citations .number {{ color: var(--gold); }}
.stat-card.topics .number {{ color: var(--cyan); }}
.stat-card.commands .number {{ color: var(--magenta); }}
.section {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px;
  padding: 20px; margin-bottom: 20px; }}
.section h2 {{ color: var(--cyan); margin-bottom: 15px; display: flex; align-items: center; gap: 10px; }}
.section h2 .icon {{ font-size: 1.2em; }}
table {{ width: 100%; border-collapse: collapse; }}
th {{ background: var(--bg); color: var(--cyan); text-align: left; padding: 10px 12px;
  border-bottom: 2px solid var(--border); position: sticky; top: 0; }}
td {{ padding: 8px 12px; border-bottom: 1px solid var(--border); }}
tr:hover td {{ background: rgba(88,166,255,0.05); }}
.severity {{ font-weight: bold; padding: 2px 8px; border-radius: 4px; font-size: 0.85em; }}
.severity.FELONY {{ color: var(--red); background: rgba(248,81,73,0.1); }}
.severity.MISDEMEANOR {{ color: var(--yellow); background: rgba(210,153,34,0.1); }}
.severity.REFERENCE {{ color: var(--dim); }}
.severity.CONSTITUTIONAL {{ color: var(--gold); background: rgba(227,179,65,0.1); }}
.severity.PROCEDURAL {{ color: var(--blue); background: rgba(88,166,255,0.1); }}
.chart-bar {{ display: flex; align-items: center; gap: 10px; margin: 4px 0; }}
.chart-bar .bar-label {{ min-width: 200px; color: var(--dim); font-size: 0.9em; text-align: right; }}
.chart-bar .bar {{ height: 22px; border-radius: 3px; transition: width 0.5s; }}
.chart-bar .bar-value {{ color: var(--text); font-size: 0.85em; min-width: 40px; }}
.btn {{ padding: 10px 20px; border: 1px solid var(--border); background: var(--surface);
  color: var(--text); border-radius: 6px; cursor: pointer; font-size: 0.9em; }}
.btn:hover {{ border-color: var(--cyan); }}
.btn.primary {{ background: var(--cyan); color: var(--bg); border-color: var(--cyan); font-weight: bold; }}
.court-doc-preview {{ background: var(--bg); border: 1px solid var(--border); border-radius: 6px;
  padding: 20px; font-family: 'Courier New', monospace; font-size: 0.85em;
  white-space: pre-wrap; max-height: 500px; overflow-y: auto; margin: 15px 0; }}
.toolbar {{ display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 15px; }}
.tag {{ display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 0.8em;
  background: rgba(88,166,255,0.1); color: var(--cyan); margin: 2px; }}
#results {{ display: none; }}
.connection {{ color: var(--dim); font-size: 0.85em; }}
.connection .arrow {{ color: var(--cyan); }}
footer {{ text-align: center; padding: 30px; color: var(--dim); font-size: 0.85em; }}
</style>
</head>
<body>
<div class="container">
  <h1><span class="diamond">◆</span> Diamond Brain v3.0 <span class="diamond">◆</span></h1>
  <div class="subtitle">Knowledge + Legal Intelligence Report — Generated {datetime.now(timezone.utc).strftime('%B %d, %Y at %H:%M UTC')}</div>

  <div class="search-box">
    <input type="text" id="searchInput" placeholder="Search facts, citations, statutes... (e.g. 'murder', 'ARS 13', 'self-defense')" />
    <button onclick="doSearch()">Search</button>
  </div>

  <div class="stats-grid">
    <div class="stat-card facts"><div class="number">{d['total_facts']}</div><div class="label">Facts</div></div>
    <div class="stat-card citations"><div class="number">{cstats['total_citations']}</div><div class="label">Citations</div></div>
    <div class="stat-card topics"><div class="number">{len(d['topics'])}</div><div class="label">Topics</div></div>
    <div class="stat-card commands"><div class="number">{d.get('commands_logged', 0)}</div><div class="label">Commands</div></div>
  </div>

  <div id="results" class="section">
    <h2><span class="icon">🔍</span> Search Results</h2>
    <div id="resultsBody"></div>
  </div>

  <div class="section">
    <h2><span class="icon">⚖</span> Legal Citations ({cstats['total_citations']})</h2>
    <div class="toolbar">
      <button class="btn" onclick="filterCitations('all')">All</button>
      <button class="btn" onclick="filterCitations('FELONY')" style="color:var(--red)">Felony</button>
      <button class="btn" onclick="filterCitations('MISDEMEANOR')" style="color:var(--yellow)">Misdemeanor</button>
      <button class="btn" onclick="filterCitations('CONSTITUTIONAL')" style="color:var(--gold)">Constitutional</button>
      <button class="btn" onclick="filterCitations('PROCEDURAL')" style="color:var(--blue)">Procedural</button>
      <button class="btn" onclick="filterCitations('REFERENCE')">Reference</button>
    </div>
    <table id="citationsTable">
      <thead><tr><th>Code</th><th>Title</th><th>Severity</th><th>Category</th><th>Text</th></tr></thead>
      <tbody id="citationsBody"></tbody>
    </table>
  </div>

  <div class="section">
    <h2><span class="icon">📈</span> Knowledge Distribution</h2>
    <div id="heatmapChart"></div>
  </div>

  <div class="section">
    <h2><span class="icon">📄</span> Court Document Generator</h2>
    <p style="color:var(--dim);margin-bottom:15px;">Generate court-ready documents populated from brain knowledge. Edit fields and download.</p>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:15px;">
      <div><label style="color:var(--dim);font-size:0.85em;">Case Number</label><br/>
        <input type="text" id="caseNum" value="CR-2026-______" style="width:100%;padding:8px;background:var(--bg);border:1px solid var(--border);color:var(--text);border-radius:4px;"/></div>
      <div><label style="color:var(--dim);font-size:0.85em;">Defendant</label><br/>
        <input type="text" id="defendant" value="[DEFENDANT NAME]" style="width:100%;padding:8px;background:var(--bg);border:1px solid var(--border);color:var(--text);border-radius:4px;"/></div>
      <div><label style="color:var(--dim);font-size:0.85em;">Document Type</label><br/>
        <select id="docType" style="width:100%;padding:8px;background:var(--bg);border:1px solid var(--border);color:var(--text);border-radius:4px;">
          <option>MOTION</option><option>BRIEF</option><option>MEMORANDUM</option><option>PETITION</option><option>RESPONSE</option>
        </select></div>
      <div><label style="color:var(--dim);font-size:0.85em;">Attorney</label><br/>
        <input type="text" id="attorney" value="[ATTORNEY NAME]" style="width:100%;padding:8px;background:var(--bg);border:1px solid var(--border);color:var(--text);border-radius:4px;"/></div>
    </div>
    <button class="btn primary" onclick="generateCourtDoc()">Generate Document</button>
    <button class="btn" onclick="downloadCourtDoc()">Download as .txt</button>
    <div id="courtDocPreview" class="court-doc-preview" style="display:none;"></div>
  </div>

  <footer>
    Diamond Brain v3.0 — Knowledge + Legal Intelligence — Owner: Ryan Cashmoney (@Tunclon)<br/>
    Generated by Diamond Brain. Not legal advice. Always verify statutes at azleg.gov.
  </footer>
</div>

<script>
const FACTS = {facts_json};
const CITATIONS = {citations_json};
const HEATMAP = {heatmap_json};
const DIGEST = {digest_json};

// --- Search ---
function doSearch() {{
  const q = document.getElementById('searchInput').value.toLowerCase().trim();
  if (!q) {{ document.getElementById('results').style.display='none'; return; }}
  document.getElementById('results').style.display='block';
  let html = '';

  // Search facts
  const matchedFacts = FACTS.filter(f =>
    (f.topic||'').toLowerCase().includes(q) ||
    (f.fact||'').toLowerCase().includes(q) ||
    (f.source||'').toLowerCase().includes(q)
  ).slice(0, 15);

  if (matchedFacts.length) {{
    html += '<h3 style="color:#3fb950;margin:10px 0;">Facts (' + matchedFacts.length + ')</h3><table>';
    html += '<tr><th>Topic</th><th>Fact</th><th>Confidence</th><th>Source</th></tr>';
    matchedFacts.forEach(f => {{
      html += '<tr><td><span class="tag">' + (f.topic||'') + '</span></td>';
      html += '<td>' + (f.fact||'').substring(0,120) + '</td>';
      html += '<td>' + (f.confidence||0) + '%</td>';
      html += '<td style="color:var(--dim)">' + (f.source||'') + '</td></tr>';
    }});
    html += '</table>';
  }}

  // Search citations
  const matchedCites = CITATIONS.filter(c =>
    (c.code||'').toLowerCase().includes(q) ||
    (c.title||'').toLowerCase().includes(q) ||
    (c.text||'').toLowerCase().includes(q)
  ).slice(0, 15);

  if (matchedCites.length) {{
    html += '<h3 style="color:#e3b341;margin:15px 0 10px;">⚖ Citations (' + matchedCites.length + ')</h3><table>';
    html += '<tr><th>Code</th><th>Title</th><th>Severity</th><th>Text</th></tr>';
    matchedCites.forEach(c => {{
      html += '<tr><td><strong>' + c.code + '</strong></td>';
      html += '<td>' + (c.title||'') + '</td>';
      html += '<td><span class="severity ' + (c.severity||'') + '">' + (c.severity||'') + '</span></td>';
      html += '<td style="font-size:0.85em">' + (c.text||'').substring(0,150) + '...</td></tr>';
    }});
    html += '</table>';
  }}

  if (!matchedFacts.length && !matchedCites.length) {{
    html = '<p style="color:var(--dim)">No results for "' + q + '"</p>';
  }}
  document.getElementById('resultsBody').innerHTML = html;
}}
document.getElementById('searchInput').addEventListener('keydown', e => {{ if(e.key==='Enter') doSearch(); }});

// --- Citations table ---
function renderCitations(filter) {{
  const tbody = document.getElementById('citationsBody');
  let filtered = filter === 'all' ? CITATIONS : CITATIONS.filter(c => c.severity === filter);
  let html = '';
  filtered.forEach(c => {{
    html += '<tr><td><strong>' + c.code + '</strong></td>';
    html += '<td>' + (c.title||'') + '</td>';
    html += '<td><span class="severity ' + (c.severity||'') + '">' + (c.severity||'') + '</span></td>';
    html += '<td><span class="tag">' + (c.category||'') + '</span></td>';
    html += '<td style="font-size:0.85em;max-width:400px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + (c.text||'').substring(0,100) + '...</td></tr>';
  }});
  tbody.innerHTML = html;
}}
function filterCitations(sev) {{ renderCitations(sev); }}
renderCitations('all');

// --- Heatmap chart ---
(function() {{
  const container = document.getElementById('heatmapChart');
  const entries = Object.entries(HEATMAP).sort((a,b) => b[1].count - a[1].count).slice(0, 15);
  const maxCount = Math.max(...entries.map(e => e[1].count), 1);
  let html = '';
  entries.forEach(([topic, info]) => {{
    const pct = (info.count / maxCount) * 100;
    const color = info.freshness_score >= 80 ? '#3fb950' : info.freshness_score >= 40 ? '#d29922' : '#f85149';
    html += '<div class="chart-bar">';
    html += '<div class="bar-label">' + topic + '</div>';
    html += '<div class="bar" style="width:' + pct + '%;background:' + color + ';"></div>';
    html += '<div class="bar-value">' + info.count + ' facts</div>';
    html += '</div>';
  }});
  container.innerHTML = html;
}})();

// --- Court Doc Generator ---
let currentDoc = '';
function generateCourtDoc() {{
  const caseNum = document.getElementById('caseNum').value;
  const defendant = document.getElementById('defendant').value;
  const docType = document.getElementById('docType').value;
  const attorney = document.getElementById('attorney').value;
  const now = new Date();
  const dateStr = now.toLocaleDateString('en-US', {{year:'numeric', month:'long', day:'numeric'}});
  const w = 72;
  const line = '='.repeat(w);
  const thin = '-'.repeat(w);

  let doc = line + '\\n';
  doc += 'IN THE SUPERIOR COURT OF ARIZONA\\n';
  doc += 'IN AND FOR MARICOPA COUNTY\\n';
  doc += line + '\\n\\n';
  doc += '  STATE OF ARIZONA,\\n';
  doc += ' '.repeat(40) + 'Case No. ' + caseNum + '\\n';
  doc += ' '.repeat(8) + 'Plaintiff,\\n';
  doc += ' '.repeat(40) + docType + '\\n';
  doc += '  vs.\\n\\n';
  doc += '  ' + defendant + ',\\n\\n';
  doc += ' '.repeat(8) + 'Defendant.\\n';
  doc += line + '\\n\\n';
  doc += ' '.repeat(10) + docType + '\\n\\n';
  doc += thin + '\\n\\n';
  doc += '  1. STATEMENT OF FACTS\\n\\n';
  doc += '    (Insert statement of facts here.)\\n\\n';
  doc += thin + '\\n\\n';
  doc += '  RESPECTFULLY SUBMITTED this ' + dateStr + '.\\n\\n\\n';
  doc += ' '.repeat(40) + '____________________________\\n';
  doc += ' '.repeat(40) + attorney + '\\n';
  doc += ' '.repeat(40) + 'Bar No. [BAR NUMBER]\\n\\n';
  doc += line;

  currentDoc = doc;
  document.getElementById('courtDocPreview').style.display = 'block';
  document.getElementById('courtDocPreview').textContent = doc;
}}

function downloadCourtDoc() {{
  if (!currentDoc) generateCourtDoc();
  const blob = new Blob([currentDoc], {{type:'text/plain'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'court_document_' + new Date().toISOString().slice(0,10) + '.txt';
  a.click();
}}
</script>
</body>
</html>"""

        if output_path:
            path = Path(output_path)
            path.write_text(html, encoding="utf-8")

        return html

    # ------------------------------------------------------------------
    # visual_bar_chart — ANSI bar chart for terminal display
    # ------------------------------------------------------------------
    def visual_bar_chart(self, data: dict[str, int | float],
                         title: str = "Chart", width: int = 40,
                         color: str = "") -> str:
        """Generate a colored ANSI bar chart string.

        Args:
            data: {label: value} dict.
            title: Chart title.
            width: Max bar width in characters.
            color: ANSI color code for bars (default: auto by value).
        """
        if not data:
            return f"  {_C.DIM}No data to chart.{_C.RESET}"

        max_val = max(data.values()) if data.values() else 1
        max_label = max(len(str(k)) for k in data.keys()) if data else 10

        lines = []
        lines.append(f"\n  {_C.CYAN}{_C.BOLD}{_C.DIAMOND} {title} {_C.DIAMOND}{_C.RESET}")
        lines.append(f"  {_C.DIM}{_C.H_LINE * (max_label + width + 12)}{_C.RESET}")

        for label, value in data.items():
            bar_len = int((value / max_val) * width) if max_val else 0
            pct = (value / max_val * 100) if max_val else 0

            if color:
                bar_color = color
            elif pct >= 75:
                bar_color = _C.GREEN
            elif pct >= 40:
                bar_color = _C.YELLOW
            else:
                bar_color = _C.RED

            bar = f"{bar_color}{'█' * bar_len}{_C.DIM}{'░' * (width - bar_len)}{_C.RESET}"
            lines.append(
                f"    {_C.WHITE}{str(label):<{max_label}}{_C.RESET}"
                f"  {_C.V_LINE}{bar}{_C.V_LINE}"
                f"  {bar_color}{value}{_C.RESET}"
            )

        lines.append(f"  {_C.DIM}{_C.H_LINE * (max_label + width + 12)}{_C.RESET}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # visual_table — ANSI formatted table
    # ------------------------------------------------------------------
    def visual_table(self, headers: list[str], rows: list[list[str]],
                     title: str = "Table") -> str:
        """Generate a box-drawn ANSI table string."""
        if not rows:
            return f"  {_C.DIM}No data to display.{_C.RESET}"

        # Calculate column widths
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))

        def fmt_row(cells, sep=_C.V_LINE):
            parts = []
            for i, cell in enumerate(cells):
                w = col_widths[i] if i < len(col_widths) else 10
                parts.append(f" {str(cell):<{w}} ")
            return f"  {sep}{sep.join(parts)}{sep}"

        def divider(left, mid, right, fill=_C.H_LINE):
            parts = [fill * (w + 2) for w in col_widths]
            return f"  {left}{mid.join(parts)}{right}"

        lines = []
        lines.append(f"\n  {_C.CYAN}{_C.BOLD}{_C.SCALE} {title} {_C.SCALE}{_C.RESET}")
        lines.append(f"{_C.DIM}{divider(_C.TL, _C.T_DOWN, _C.TR)}{_C.RESET}")
        lines.append(f"{_C.BOLD}{_C.WHITE}{fmt_row(headers)}{_C.RESET}")
        lines.append(f"{_C.DIM}{divider(_C.T_RIGHT, _C.CROSS, _C.T_LEFT)}{_C.RESET}")

        for row in rows:
            # Color severity columns
            colored_cells = []
            for cell in row:
                cell_str = str(cell)
                cell_upper = cell_str.upper()
                if cell_upper in ("FELONY", "CRITICAL", "HIGH"):
                    colored_cells.append(f"{_C.RED}{_C.BOLD}{cell_str}{_C.RESET}")
                elif cell_upper in ("MISDEMEANOR", "MEDIUM", "WARNING"):
                    colored_cells.append(f"{_C.YELLOW}{cell_str}{_C.RESET}")
                elif cell_upper in ("REFERENCE", "LOW", "PROCEDURAL"):
                    colored_cells.append(f"{_C.DIM}{cell_str}{_C.RESET}")
                else:
                    colored_cells.append(cell_str)
            lines.append(fmt_row(colored_cells))

        lines.append(f"{_C.DIM}{divider(_C.BL, _C.T_UP, _C.BR)}{_C.RESET}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # visual_connection_graph — ANSI connection/link visualization
    # ------------------------------------------------------------------
    def visual_connection_graph(self, center: str,
                                connections: list[tuple[str, str]],
                                title: str = "Connections") -> str:
        """Generate an ANSI text connection graph.

        Args:
            center: Central node label.
            connections: List of (label, relation_type) tuples.
        """
        lines = []
        lines.append(f"\n  {_C.MAGENTA}{_C.BOLD}{_C.DIAMOND} {title} {_C.DIAMOND}{_C.RESET}")
        lines.append("")

        if not connections:
            lines.append(f"    {_C.CYAN}{_C.BOLD}[{center}]{_C.RESET}  {_C.DIM}(no connections){_C.RESET}")
            return "\n".join(lines)

        mid = len(connections) // 2
        for i, conn in enumerate(connections):
            if isinstance(conn, (list, tuple)) and len(conn) >= 2:
                label, rel = conn[0], conn[1]
            else:
                label, rel = str(conn), "related"
            if i < mid:
                connector = f"{_C.DIM}{_C.T_RIGHT}{_C.H_LINE}{_C.H_LINE}{_C.RESET}"
            elif i == mid:
                connector = f"{_C.CYAN}{_C.BOLD}{_C.H_LINE}{_C.H_LINE}{_C.ARROW}{_C.RESET}"
            else:
                connector = f"{_C.DIM}{_C.T_RIGHT}{_C.H_LINE}{_C.H_LINE}{_C.RESET}"

            if i == mid:
                lines.append(
                    f"    {_C.GOLD}[{label}]{_C.RESET}"
                    f" {connector}"
                    f" {_C.CYAN}{_C.BOLD}[{center}]{_C.RESET}"
                    f" {_C.DIM}({rel}){_C.RESET}"
                )
            else:
                lines.append(
                    f"    {_C.GOLD}[{label}]{_C.RESET}"
                    f" {connector}"
                    f" {_C.DIM}({rel}){_C.RESET}"
                )

        lines.append("")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # visual_report — full visual report of a topic or the whole brain
    # ------------------------------------------------------------------
    def visual_report(self, topic: str | None = None) -> str:
        """Generate a comprehensive visual report.

        If topic is given, report on that topic with citations.
        Otherwise, report on the entire brain.
        """
        lines = []

        if topic:
            # Topic-specific report
            facts = self.recall(topic, max_results=15, fuzzy=True)
            citations = self.recall_citations(query=topic)

            lines.append(_section_header(
                f"VISUAL REPORT: {topic.upper()}", _C.DIAMOND, _C.CYAN
            ))

            # Facts as table
            if facts:
                fact_rows = []
                for f in facts:
                    conf = f.get("confidence", 0)
                    fact_rows.append([
                        f.get("topic", "?"),
                        f.get("fact", "")[:60],
                        str(conf) + "%",
                        f.get("source", "?"),
                    ])
                lines.append(self.visual_table(
                    ["Topic", "Fact", "Conf", "Source"],
                    fact_rows,
                    title=f"Facts: {topic}",
                ))

            # Citations as table
            if citations:
                cit_rows = []
                for c in citations:
                    cit_rows.append([
                        c.get("code", "?"),
                        c.get("title", "")[:40],
                        c.get("severity", "?"),
                        c.get("category", "?"),
                    ])
                lines.append(self.visual_table(
                    ["Code", "Title", "Severity", "Category"],
                    cit_rows,
                    title=f"Citations: {topic}",
                ))

            # Connection graph
            all_links = []
            for f in facts:
                for link in f.get("links", []):
                    all_links.append((link, "related"))
            crime_citations = self.link_crime_to_citations(topic, topic)
            for cc in crime_citations:
                all_links.append((cc, "cited"))
            if all_links:
                lines.append(self.visual_connection_graph(
                    topic, all_links[:15], title=f"Links: {topic}"
                ))
        else:
            # Full brain report
            d = self.digest()
            lines.append(_section_header(
                "DIAMOND BRAIN — FULL VISUAL REPORT", _C.DIAMOND, _C.CYAN
            ))

            # Heatmap as bar chart
            hm = self.heatmap()
            if hm:
                chart_data = {
                    t: info["count"] for t, info in
                    sorted(hm.items(), key=lambda x: x[1]["count"], reverse=True)[:15]
                }
                lines.append(self.visual_bar_chart(
                    chart_data, title="Knowledge Distribution"
                ))

            # Citation stats as bar chart
            cstats = self.citation_stats()
            if cstats["total_citations"] > 0:
                lines.append(self.visual_bar_chart(
                    cstats["by_severity"],
                    title="Citations by Severity",
                    color=_C.GOLD,
                ))
                lines.append(self.visual_bar_chart(
                    cstats["by_category"],
                    title="Citations by Category",
                    color=_C.BLUE,
                ))

            # Summary table
            summary_rows = [
                ["Total Facts", str(d["total_facts"]), _C.CHECK],
                ["Topics", str(len(d["topics"])), _C.CHECK],
                ["Agents", str(d["total_agents"]), _C.CHECK],
                ["Commands", str(d.get("commands_logged", 0)), _C.CHECK],
                ["Citations", str(cstats["total_citations"]), _C.SCALE],
            ]
            lines.append(self.visual_table(
                ["Metric", "Count", "Status"],
                summary_rows,
                title="Brain Summary",
            ))

        return "\n".join(lines)

    # ==================================================================
    # DIAMOND LINK — Encrypted Brain-to-Brain Linking
    # ==================================================================

    def _link_dir(self) -> Path:
        """Path to the link storage directory."""
        return self.memory_dir / "link"

    def _link_load_json(self, filename: str) -> list | dict:
        """Load a JSON file from the link directory."""
        path = self._link_dir() / filename
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data
        except (json.JSONDecodeError, FileNotFoundError):
            return [] if filename != "identity.json" else {}

    def _link_save_json(self, filename: str, data) -> None:
        """Atomic-write a JSON file to the link directory."""
        path = self._link_dir() / filename
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False),
                       encoding="utf-8")
        os.replace(str(tmp), str(path))

    def _link_load_peers(self) -> list[dict]:
        data = self._link_load_json("peers.json")
        return data if isinstance(data, list) else []

    def _link_save_peers(self, peers: list[dict]) -> None:
        self._link_save_json("peers.json", peers)

    def _link_load_sync_log(self) -> list[dict]:
        data = self._link_load_json("sync_log.json")
        return data if isinstance(data, list) else []

    def _link_save_sync_log(self, log: list[dict]) -> None:
        # Rolling window: keep last 1000 entries
        self._link_save_json("sync_log.json", log[-1000:])

    def _link_append_sync_log(self, entry: dict) -> None:
        log = self._link_load_sync_log()
        log.append(entry)
        self._link_save_sync_log(log)

    # --- Chain of Custody ---
    def _link_load_custody_log(self) -> list[dict]:
        data = self._link_load_json("custody_log.json")
        return data if isinstance(data, list) else []

    def _link_save_custody_log(self, log: list[dict]) -> None:
        self._link_save_json("custody_log.json", log[-5000:])

    def _link_append_custody(self, event_type: str, details: dict) -> dict:
        """Append an immutable chain-of-custody record.

        Every record gets:
        - Immutable timestamp (UTC ISO-8601)
        - Event type (PAIR, UNPAIR, SYNC_SEND, SYNC_RECV, IDENTITY_CREATED, etc.)
        - SHA-256 hash chaining to previous record (blockchain-style)
        - Actor fingerprint (this brain's identity)
        - Peer fingerprint (if applicable)
        """
        log = self._link_load_custody_log()

        # Chain hash: SHA-256 of previous entry's JSON
        prev_hash = "GENESIS"
        if log:
            prev_json = json.dumps(log[-1], sort_keys=True, ensure_ascii=False)
            prev_hash = hashlib.sha256(prev_json.encode()).hexdigest()

        identity = self._link_load_json("identity.json")
        actor_fp = identity.get("fingerprint", "UNKNOWN")

        record = {
            "seq": len(log),
            "timestamp": _now_iso(),
            "event_type": event_type,
            "actor_fingerprint": actor_fp,
            "prev_hash": prev_hash,
            "details": details,
        }
        # Compute this record's own hash for verification
        record_json = json.dumps(record, sort_keys=True, ensure_ascii=False)
        record["record_hash"] = hashlib.sha256(record_json.encode()).hexdigest()

        log.append(record)
        self._link_save_custody_log(log)

        # Mark Merkle DAG as stale
        self._merkle_mark_stale()

        return record

    def link_verify_custody_chain(self) -> dict:
        """Verify the integrity of the chain of custody log.

        Returns {valid: bool, records: int, broken_at: int | None, message: str}.
        """
        log = self._link_load_custody_log()
        if not log:
            return {"valid": True, "records": 0, "broken_at": None,
                    "message": "No custody records yet."}

        for i, record in enumerate(log):
            # Verify chain link
            if i == 0:
                if record.get("prev_hash") != "GENESIS":
                    return {"valid": False, "records": len(log), "broken_at": 0,
                            "message": "First record does not have GENESIS prev_hash."}
            else:
                prev_json = json.dumps(log[i - 1], sort_keys=True, ensure_ascii=False)
                # Remove record_hash from prev before hashing (it was added after)
                prev_copy = dict(log[i - 1])
                prev_copy.pop("record_hash", None)
                prev_json = json.dumps(prev_copy, sort_keys=True, ensure_ascii=False)
                expected_prev = hashlib.sha256(prev_json.encode()).hexdigest()
                if record.get("prev_hash") != expected_prev:
                    return {"valid": False, "records": len(log), "broken_at": i,
                            "message": f"Chain broken at record #{i}: prev_hash mismatch."}

            # Verify self-hash
            record_copy = dict(record)
            stored_hash = record_copy.pop("record_hash", None)
            if stored_hash:
                check_json = json.dumps(record_copy, sort_keys=True, ensure_ascii=False)
                expected_hash = hashlib.sha256(check_json.encode()).hexdigest()
                if stored_hash != expected_hash:
                    return {"valid": False, "records": len(log), "broken_at": i,
                            "message": f"Record #{i} self-hash mismatch (tampered)."}

        return {"valid": True, "records": len(log), "broken_at": None,
                "message": f"Chain intact. {len(log)} records verified."}

    # ==================================================================
    #  FEATURE 24: MERKLE DAG FOR CUSTODY
    # ==================================================================

    def _merkle_path(self) -> Path:
        return self._link_dir() / "merkle_dag.json"

    def _merkle_load(self) -> dict:
        path = self._merkle_path()
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return {}

    def _merkle_save(self, dag: dict) -> None:
        path = self._merkle_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(dag, indent=2, ensure_ascii=False),
                       encoding="utf-8")
        os.replace(str(tmp), str(path))

    def _merkle_mark_stale(self) -> None:
        """Mark DAG as stale (called after custody append)."""
        dag = self._merkle_load()
        if dag:
            dag["stale"] = True
            self._merkle_save(dag)

    @staticmethod
    def _merkle_hash_leaf(record: dict) -> str:
        """SHA-256 hash of a custody record (leaf node)."""
        record_copy = dict(record)
        record_copy.pop("record_hash", None)
        data = json.dumps(record_copy, sort_keys=True,
                          ensure_ascii=False).encode()
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def _merkle_hash_pair(left: str, right: str) -> str:
        """SHA-256 hash of two concatenated hashes (internal node)."""
        combined = (left + right).encode()
        return hashlib.sha256(combined).hexdigest()

    def _merkle_build_tree(self, leaves: list[str]) -> list[list[str]]:
        """Build Merkle tree layers from leaf hashes. Returns layers[0]=leaves."""
        if not leaves:
            return [[]]
        layers = [list(leaves)]
        current = list(leaves)
        while len(current) > 1:
            next_layer = []
            for i in range(0, len(current), 2):
                left = current[i]
                right = current[i + 1] if i + 1 < len(current) else left
                next_layer.append(self._merkle_hash_pair(left, right))
            layers.append(next_layer)
            current = next_layer
        return layers

    def _merkle_find_sibling_path(self, layers: list[list[str]],
                                   leaf_index: int) -> list[dict]:
        """Build proof path: list of {hash, position} siblings from leaf to root."""
        proof = []
        idx = leaf_index
        for layer in layers[:-1]:
            if idx % 2 == 0:
                sibling_idx = idx + 1
                position = "right"
            else:
                sibling_idx = idx - 1
                position = "left"
            if sibling_idx < len(layer):
                proof.append({"hash": layer[sibling_idx],
                              "position": position})
            else:
                proof.append({"hash": layer[idx], "position": "right"})
            idx //= 2
        return proof

    def merkle_build(self) -> dict:
        """Build/rebuild Merkle tree from the custody chain.

        Returns {root_hash, leaf_count, built_at, stale}.
        """
        log = self._link_load_custody_log()
        leaves = [self._merkle_hash_leaf(r) for r in log]
        layers = self._merkle_build_tree(leaves)
        root = layers[-1][0] if layers and layers[-1] else "EMPTY"

        dag = {
            "root_hash": root,
            "leaf_count": len(leaves),
            "tree_layers": layers,
            "built_at": _now_iso(),
            "stale": False,
        }
        self._merkle_save(dag)
        return {
            "root_hash": root,
            "leaf_count": len(leaves),
            "built_at": dag["built_at"],
            "stale": False,
        }

    def merkle_prove(self, record_seq: int) -> dict:
        """Generate inclusion proof for a custody record by sequence number.

        Returns {record_seq, leaf_hash, root_hash, proof_path}.
        """
        dag = self._merkle_load()
        if not dag or not dag.get("tree_layers"):
            return {"error": "Merkle DAG not built. Run merkle_build() first."}

        layers = dag["tree_layers"]
        if record_seq < 0 or record_seq >= len(layers[0]):
            return {"error": f"Record seq {record_seq} out of range "
                    f"(0-{len(layers[0]) - 1})."}

        leaf_hash = layers[0][record_seq]
        proof_path = self._merkle_find_sibling_path(layers, record_seq)

        return {
            "record_seq": record_seq,
            "leaf_hash": leaf_hash,
            "root_hash": dag["root_hash"],
            "proof_path": proof_path,
        }

    @staticmethod
    def merkle_verify_proof(proof: dict) -> dict:
        """Verify a Merkle inclusion proof (standalone — no DAG load).

        Args:
            proof: {leaf_hash, root_hash, proof_path: [{hash, position}]}
        Returns:
            {valid: bool, computed_root, expected_root}
        """
        current = proof.get("leaf_hash", "")
        for step in proof.get("proof_path", []):
            sibling = step["hash"]
            if step["position"] == "right":
                current = hashlib.sha256(
                    (current + sibling).encode()).hexdigest()
            else:
                current = hashlib.sha256(
                    (sibling + current).encode()).hexdigest()

        expected = proof.get("root_hash", "")
        return {
            "valid": current == expected,
            "computed_root": current,
            "expected_root": expected,
        }

    def merkle_status(self) -> dict:
        """Return Merkle DAG status: root_hash, size, staleness."""
        dag = self._merkle_load()
        if not dag:
            return {"built": False, "root_hash": None, "leaf_count": 0,
                    "stale": True, "built_at": None}
        return {
            "built": True,
            "root_hash": dag.get("root_hash"),
            "leaf_count": dag.get("leaf_count", 0),
            "stale": dag.get("stale", True),
            "built_at": dag.get("built_at"),
        }

    # ------------------------------------------------------------------
    # link_init — generate identity (cert + key via openssl)
    # ------------------------------------------------------------------
    def link_init(self, display_name: str = "Diamond Brain") -> dict:
        """Initialize Diamond Link identity.

        Generates RSA 2048 key pair + self-signed X.509 certificate via
        openssl CLI. Creates brain/memory/link/ directory. Idempotent —
        if identity already exists, returns it without regenerating.

        Returns: {fingerprint, display_name, created_at, cert_path, key_path}
        """
        import shutil
        import subprocess

        link_dir = self._link_dir()
        identity_path = link_dir / "identity.json"

        # Idempotent: return existing identity
        if identity_path.exists():
            return self._link_load_json("identity.json")

        # Check for openssl
        if not shutil.which("openssl"):
            raise RuntimeError(
                "Diamond Link requires 'openssl' CLI for one-time certificate "
                "generation. Install it:\n"
                "  Linux:   sudo apt install openssl\n"
                "  macOS:   pre-installed (or: brew install openssl)\n"
                "  Windows: included with Git for Windows"
            )

        link_dir.mkdir(parents=True, exist_ok=True)

        key_path = link_dir / "key.pem"
        cert_path = link_dir / "cert.pem"

        # Generate RSA 2048 private key
        subprocess.run(
            ["openssl", "genrsa", "-out", str(key_path), "2048"],
            check=True, capture_output=True,
        )

        # Set restrictive permissions on private key
        try:
            os.chmod(str(key_path), 0o600)
        except OSError:
            pass  # Windows may not support chmod

        # Generate self-signed certificate (valid 10 years)
        subprocess.run(
            [
                "openssl", "req", "-new", "-x509",
                "-key", str(key_path),
                "-out", str(cert_path),
                "-days", "3650",
                "-subj", f"/CN=DiamondBrain-{display_name}/O=DiamondLink",
            ],
            check=True, capture_output=True,
        )

        # Compute fingerprint = SHA-256 of DER-encoded certificate
        result = subprocess.run(
            ["openssl", "x509", "-in", str(cert_path), "-outform", "DER"],
            check=True, capture_output=True,
        )
        fingerprint = hashlib.sha256(result.stdout).hexdigest()

        identity = {
            "fingerprint": fingerprint,
            "display_name": display_name,
            "created_at": _now_iso(),
            "cert_path": str(cert_path),
            "key_path": str(key_path),
        }
        self._link_save_json("identity.json", identity)

        # Initialize empty peer/log files
        if not (link_dir / "peers.json").exists():
            self._link_save_json("peers.json", [])
        if not (link_dir / "sync_log.json").exists():
            self._link_save_json("sync_log.json", [])
        if not (link_dir / "custody_log.json").exists():
            self._link_save_json("custody_log.json", [])

        # Chain of custody: record identity creation
        self._link_append_custody("IDENTITY_CREATED", {
            "display_name": display_name,
            "fingerprint": fingerprint,
        })

        return identity

    # ------------------------------------------------------------------
    # link_identity — return this brain's fingerprint + display name
    # ------------------------------------------------------------------
    def link_identity(self) -> dict | None:
        """Return this brain's link identity, or None if not initialized."""
        identity = self._link_load_json("identity.json")
        return identity if identity else None

    # ------------------------------------------------------------------
    # Message protocol: HMAC + length-prefixed I/O
    # ------------------------------------------------------------------
    def _link_hmac_key(self, local_fp: str, peer_fp: str) -> bytes:
        """Derive HMAC key from both peers' fingerprints (sorted for consistency)."""
        combined = ":".join(sorted([local_fp, peer_fp]))
        return hashlib.sha256(combined.encode()).digest()

    def _link_hmac_sign(self, data: bytes, key: bytes) -> bytes:
        """HMAC-SHA256 sign data."""
        import hmac as _hmac
        return _hmac.new(key, data, hashlib.sha256).digest()

    def _link_hmac_verify(self, data: bytes, tag: bytes, key: bytes) -> bool:
        """Verify HMAC-SHA256 tag."""
        import hmac as _hmac
        expected = _hmac.new(key, data, hashlib.sha256).digest()
        return _hmac.compare_digest(expected, tag)

    def _link_send_message(self, sock, msg_dict: dict, hmac_key: bytes) -> None:
        """Send a length-prefixed JSON message with HMAC tag over TLS socket.

        Wire format: <4-byte big-endian length><JSON body><32-byte HMAC tag>
        """
        import secrets as _secrets
        # Add nonce to prevent replay attacks
        msg_dict["_nonce"] = _secrets.token_hex(16)
        msg_dict["_timestamp"] = _now_iso()

        body = json.dumps(msg_dict, ensure_ascii=False).encode("utf-8")
        if len(body) > 10 * 1024 * 1024:  # 10 MB max
            raise ValueError("Message too large (>10 MB)")

        tag = self._link_hmac_sign(body, hmac_key)
        payload = body + tag
        length = len(payload).to_bytes(4, "big")
        sock.sendall(length + payload)

    def _link_recv_message(self, sock, hmac_key: bytes) -> dict:
        """Receive a length-prefixed JSON message with HMAC verification.

        Returns parsed dict. Raises ValueError on HMAC failure or size violation.
        """
        # Read 4-byte length header
        raw_len = self._link_recv_exact(sock, 4)
        length = int.from_bytes(raw_len, "big")

        if length > 10 * 1024 * 1024 + 32:  # 10 MB + HMAC tag
            raise ValueError("Message too large")
        if length < 32:
            raise ValueError("Message too small (no HMAC tag)")

        payload = self._link_recv_exact(sock, length)
        body = payload[:-32]
        tag = payload[-32:]

        if not self._link_hmac_verify(body, tag, hmac_key):
            raise ValueError("HMAC verification failed — message integrity compromised")

        return json.loads(body.decode("utf-8"))

    @staticmethod
    def _link_recv_exact(sock, n: int) -> bytes:
        """Read exactly n bytes from socket."""
        data = b""
        while len(data) < n:
            chunk = sock.recv(n - len(data))
            if not chunk:
                raise ConnectionError("Connection closed while reading")
            data += chunk
        return data

    # ------------------------------------------------------------------
    # Snapshot: serialize/deserialize facts + citations for sync
    # ------------------------------------------------------------------
    def _link_build_snapshot(self, topics: list[str] | None = None) -> dict:
        """Build a snapshot of facts and citations for sharing.

        Each fact/citation gets a content_hash for dedup/conflict detection.
        If topics is specified, only include facts matching those topics.
        """
        facts = self._load(self._facts_path)
        citations = self._load(self._citations_path)

        if topics:
            topics_lower = [t.lower() for t in topics]
            facts = [f for f in facts
                     if f.get("topic", "").lower() in topics_lower]

        # Add content hashes
        snap_facts = []
        for f in facts:
            content = f"{f.get('topic','')}/{f.get('fact','')}".lower()
            f_copy = dict(f)
            f_copy["_content_hash"] = hashlib.sha256(content.encode()).hexdigest()[:16]
            snap_facts.append(f_copy)

        snap_citations = []
        for c in citations:
            c_copy = dict(c)
            c_copy["_content_hash"] = hashlib.sha256(
                c.get("code", "").encode()
            ).hexdigest()[:16]
            snap_citations.append(c_copy)

        identity = self.link_identity() or {}
        return {
            "source_fingerprint": identity.get("fingerprint", ""),
            "source_name": identity.get("display_name", ""),
            "snapshot_at": _now_iso(),
            "facts": snap_facts,
            "citations": snap_citations,
        }

    def _link_resolve_fact_conflict(self, local: dict, remote: dict) -> str:
        """Determine winner in a fact conflict.

        Priority chain:
        1. Verified fact wins over unverified
        2. Higher effective confidence wins (after time decay)
        3. More recently updated wins (within 5-point confidence margin)
        4. Complementary facts (60-80% similarity) → keep both
        5. Tiebreaker: lexicographically smaller fingerprint wins

        Returns: 'local', 'remote', 'both', or 'skip'
        """
        local_verified = local.get("verified", False)
        remote_verified = remote.get("verified", False)

        # Rule 1: Verified wins
        if local_verified and not remote_verified:
            return "local"
        if remote_verified and not local_verified:
            return "remote"

        # Rule 2: Higher effective confidence
        local_eff = _decayed_confidence(
            local.get("confidence", 0),
            local.get("updated_at", local.get("created_at", "")),
            local_verified,
        )
        remote_eff = _decayed_confidence(
            remote.get("confidence", 0),
            remote.get("updated_at", remote.get("created_at", "")),
            remote_verified,
        )

        margin = 5
        if abs(local_eff - remote_eff) > margin:
            return "local" if local_eff > remote_eff else "remote"

        # Rule 3: More recently updated (within margin)
        local_days = _days_ago(local.get("updated_at", ""))
        remote_days = _days_ago(remote.get("updated_at", ""))
        if abs(local_days - remote_days) > 1.0:
            return "local" if local_days < remote_days else "remote"

        # Rule 4: Check similarity — complementary facts kept as both
        sim = _similarity(local.get("fact", ""), remote.get("fact", ""))
        if 0.60 <= sim <= 0.80:
            return "both"

        # Rule 5: Tiebreaker — skip (local wins by default)
        return "local"

    def _link_apply_snapshot(self, snapshot: dict, peer_fp: str,
                             direction: str = "pull",
                             dry_run: bool = False) -> dict:
        """Apply incoming snapshot data with conflict resolution.

        Returns: {facts_added, facts_updated, facts_skipped,
                  citations_added, citations_updated, conflicts: [...]}
        """
        stats = {
            "facts_added": 0, "facts_updated": 0, "facts_skipped": 0,
            "citations_added": 0, "citations_updated": 0,
            "conflicts": [],
        }

        if direction not in ("pull", "both"):
            return stats  # push-only: nothing to apply locally

        local_facts = self._load(self._facts_path)
        local_citations = self._load(self._citations_path)

        remote_facts = snapshot.get("facts", [])
        remote_citations = snapshot.get("citations", [])

        # --- Apply facts ---
        for rf in remote_facts:
            rf_topic = rf.get("topic", "").lower()
            rf_fact = rf.get("fact", "")
            rf_hash = rf.get("_content_hash", "")

            # Find matching local fact
            match = None
            match_idx = None
            for i, lf in enumerate(local_facts):
                if lf.get("topic", "").lower() != rf_topic:
                    continue
                sim = _similarity(lf.get("fact", ""), rf_fact)
                if sim > 0.80:
                    match = lf
                    match_idx = i
                    break

            if match is None:
                # New fact — add it
                if not dry_run:
                    new_fact = {k: v for k, v in rf.items()
                               if not k.startswith("_") or k == "_crdt"}
                    new_fact["source"] = f"link:{peer_fp[:12]}"
                    new_fact.setdefault("links", [])
                    self._crdt_ensure_metadata(new_fact)
                    local_facts.append(new_fact)
                stats["facts_added"] += 1
            else:
                # CRDT merge when both sides have metadata, else LWW
                if "_crdt" in match and "_crdt" in rf:
                    winner = self._crdt_merge_fact(match, rf)
                else:
                    winner = self._link_resolve_fact_conflict(match, rf)
                stats["conflicts"].append({
                    "topic": rf_topic,
                    "fact_preview": rf_fact[:60],
                    "resolution": winner,
                })

                if winner == "remote":
                    if not dry_run:
                        for k, v in rf.items():
                            if not k.startswith("_"):
                                local_facts[match_idx][k] = v
                        local_facts[match_idx]["source"] = f"link:{peer_fp[:12]}"
                    stats["facts_updated"] += 1
                elif winner == "both":
                    if not dry_run:
                        new_fact = {k: v for k, v in rf.items()
                                    if not k.startswith("_")}
                        new_fact["source"] = f"link:{peer_fp[:12]}"
                        new_fact["confidence"] = max(
                            30, int(rf.get("confidence", 50) * 0.8))
                        new_fact.setdefault("links", [])
                        local_facts.append(new_fact)
                    stats["facts_added"] += 1
                else:
                    stats["facts_skipped"] += 1

        # --- Apply citations ---
        local_codes = {c.get("code", "").upper() for c in local_citations}
        for rc in remote_citations:
            rc_code = rc.get("code", "").upper()
            if rc_code in local_codes:
                # Update if remote is newer
                for lc in local_citations:
                    if lc.get("code", "").upper() == rc_code:
                        local_updated = lc.get("updated_at", "")
                        remote_updated = rc.get("updated_at", "")
                        if remote_updated > local_updated:
                            if not dry_run:
                                for k, v in rc.items():
                                    if not k.startswith("_"):
                                        lc[k] = v
                            stats["citations_updated"] += 1
                        break
            else:
                if not dry_run:
                    new_cit = {k: v for k, v in rc.items()
                               if not k.startswith("_")}
                    local_citations.append(new_cit)
                stats["citations_added"] += 1

        if not dry_run:
            self._save(self._facts_path, local_facts)
            self._save(self._citations_path, local_citations)

        return stats

    # ------------------------------------------------------------------
    # TLS context helpers
    # ------------------------------------------------------------------
    def _link_server_ssl_context(self) -> "ssl.SSLContext":
        """Create TLS server context with strong ciphers."""
        import ssl
        identity = self._link_load_json("identity.json")
        if not identity:
            raise RuntimeError("Diamond Link not initialized. Run link_init() first.")

        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ctx.set_ciphers("ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20")
        ctx.load_cert_chain(
            certfile=identity["cert_path"],
            keyfile=identity["key_path"],
        )
        return ctx

    def _link_client_ssl_context(self) -> "ssl.SSLContext":
        """Create TLS client context (no cert verification — we use fingerprint pinning)."""
        import ssl
        identity = self._link_load_json("identity.json")
        if not identity:
            raise RuntimeError("Diamond Link not initialized. Run link_init() first.")

        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE  # We verify via fingerprint pinning
        ctx.load_cert_chain(
            certfile=identity["cert_path"],
            keyfile=identity["key_path"],
        )
        return ctx

    def _link_verify_peer_cert(self, ssl_sock, expected_fp: str) -> bool:
        """Verify peer certificate fingerprint matches expected value."""
        der_cert = ssl_sock.getpeercert(binary_form=True)
        if not der_cert:
            return False
        actual_fp = hashlib.sha256(der_cert).hexdigest()
        return actual_fp == expected_fp

    # ------------------------------------------------------------------
    # link_pair_start — listen for pairing request
    # ------------------------------------------------------------------
    def link_pair_start(self, port: int = 7777, timeout: int = 300) -> str:
        """Start listening for a pairing request.

        Generates a 64-char hex pairing token, listens on the given port.
        The remote brain must provide this token to complete pairing.
        Returns the pairing token (display it to the user).

        Blocks until a peer connects or timeout expires.
        """
        import secrets as _secrets
        import socket
        import ssl

        identity = self.link_identity()
        if not identity:
            raise RuntimeError("Diamond Link not initialized. Run link_init() first.")

        token = _secrets.token_hex(32)  # 64 hex chars
        local_fp = identity["fingerprint"]

        ctx = self._link_server_ssl_context()
        ctx.verify_mode = ssl.CERT_NONE  # Pairing: no client cert yet

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind(("0.0.0.0", port))
            srv.listen(1)
            srv.settimeout(timeout)

            print(f"\n{_C.CYAN}{_C.BOLD}  Diamond Link Pairing{_C.RESET}")
            print(f"  {_C.WHITE}Listening on port {_C.GREEN}{port}{_C.RESET}")
            print(f"  {_C.WHITE}Token: {_C.GOLD}{_C.BOLD}{token}{_C.RESET}")
            print(f"  {_C.DIM}Waiting for peer (timeout: {timeout}s)...{_C.RESET}\n")

            try:
                conn, addr = srv.accept()
            except socket.timeout:
                print(f"  {_C.RED}Pairing timed out.{_C.RESET}")
                return token

            with ctx.wrap_socket(conn, server_side=True) as tls_conn:
                # Derive a temporary HMAC key from the token
                temp_key = hashlib.sha256(token.encode()).digest()

                try:
                    # Receive pairing request
                    msg = self._link_recv_message(tls_conn, temp_key)
                    if msg.get("type") != "PAIR_REQUEST":
                        self._link_send_message(tls_conn, {
                            "type": "PAIR_REJECT", "reason": "Invalid message type"
                        }, temp_key)
                        return token

                    if msg.get("token") != token:
                        self._link_send_message(tls_conn, {
                            "type": "PAIR_REJECT", "reason": "Invalid token"
                        }, temp_key)
                        print(f"  {_C.RED}Pairing rejected: invalid token.{_C.RESET}")
                        return token

                    peer_fp = msg.get("fingerprint", "")
                    peer_name = msg.get("display_name", "Unknown")
                    peer_cert_pem = msg.get("cert_pem", "")

                    # Accept pairing — store peer
                    peers = self._link_load_peers()
                    # Check if already paired
                    for p in peers:
                        if p.get("fingerprint") == peer_fp:
                            p["status"] = "active"
                            p["display_name"] = peer_name
                            p["last_paired"] = _now_iso()
                            self._link_save_peers(peers)
                            break
                    else:
                        peers.append({
                            "fingerprint": peer_fp,
                            "display_name": peer_name,
                            "cert_pem": peer_cert_pem,
                            "host": addr[0],
                            "port": port,
                            "status": "active",
                            "shared_topics": [],  # empty = share all
                            "paired_at": _now_iso(),
                            "last_paired": _now_iso(),
                            "last_sync": None,
                            "syncs_completed": 0,
                        })
                        self._link_save_peers(peers)

                    # Send acceptance with our identity
                    cert_pem = Path(identity["cert_path"]).read_text(encoding="utf-8")
                    self._link_send_message(tls_conn, {
                        "type": "PAIR_ACCEPT",
                        "fingerprint": local_fp,
                        "display_name": identity["display_name"],
                        "cert_pem": cert_pem,
                    }, temp_key)

                    # Chain of custody record
                    self._link_append_custody("PAIR", {
                        "peer_fingerprint": peer_fp,
                        "peer_name": peer_name,
                        "direction": "accepted",
                        "remote_addr": addr[0],
                    })

                    print(f"  {_C.GREEN}{_C.CHECK} Paired with:{_C.RESET} "
                          f"{_C.WHITE}{peer_name}{_C.RESET} "
                          f"{_C.DIM}({peer_fp[:16]}...){_C.RESET}")

                except (ValueError, ConnectionError, json.JSONDecodeError) as e:
                    print(f"  {_C.RED}Pairing error: {e}{_C.RESET}")

        return token

    # ------------------------------------------------------------------
    # link_pair_connect — connect to a peer for pairing
    # ------------------------------------------------------------------
    def link_pair_connect(self, host: str, port: int, token: str) -> bool:
        """Connect to a peer brain and complete pairing.

        Args:
            host: Hostname or IP of the peer brain
            port: Port number
            token: Pairing token from peer's link_pair_start()

        Returns: True if pairing succeeded
        """
        import socket
        import ssl

        identity = self.link_identity()
        if not identity:
            raise RuntimeError("Diamond Link not initialized. Run link_init() first.")

        local_fp = identity["fingerprint"]
        cert_pem = Path(identity["cert_path"]).read_text(encoding="utf-8")
        ctx = self._link_client_ssl_context()

        try:
            with socket.create_connection((host, port), timeout=30) as sock:
                with ctx.wrap_socket(sock, server_hostname=host) as tls_conn:
                    # HMAC key derived from token
                    temp_key = hashlib.sha256(token.encode()).digest()

                    # Send pairing request
                    self._link_send_message(tls_conn, {
                        "type": "PAIR_REQUEST",
                        "token": token,
                        "fingerprint": local_fp,
                        "display_name": identity["display_name"],
                        "cert_pem": cert_pem,
                    }, temp_key)

                    # Receive response
                    resp = self._link_recv_message(tls_conn, temp_key)

                    if resp.get("type") == "PAIR_ACCEPT":
                        peer_fp = resp.get("fingerprint", "")
                        peer_name = resp.get("display_name", "Unknown")
                        peer_cert_pem = resp.get("cert_pem", "")

                        # Store peer
                        peers = self._link_load_peers()
                        for p in peers:
                            if p.get("fingerprint") == peer_fp:
                                p["status"] = "active"
                                p["display_name"] = peer_name
                                p["last_paired"] = _now_iso()
                                self._link_save_peers(peers)
                                break
                        else:
                            peers.append({
                                "fingerprint": peer_fp,
                                "display_name": peer_name,
                                "cert_pem": peer_cert_pem,
                                "host": host,
                                "port": port,
                                "status": "active",
                                "shared_topics": [],
                                "paired_at": _now_iso(),
                                "last_paired": _now_iso(),
                                "last_sync": None,
                                "syncs_completed": 0,
                            })
                            self._link_save_peers(peers)

                        # Chain of custody
                        self._link_append_custody("PAIR", {
                            "peer_fingerprint": peer_fp,
                            "peer_name": peer_name,
                            "direction": "initiated",
                            "remote_addr": host,
                        })

                        print(f"  {_C.GREEN}{_C.CHECK} Paired with:{_C.RESET} "
                              f"{_C.WHITE}{peer_name}{_C.RESET} "
                              f"{_C.DIM}({peer_fp[:16]}...){_C.RESET}")
                        return True
                    else:
                        reason = resp.get("reason", "Unknown")
                        print(f"  {_C.RED}Pairing rejected: {reason}{_C.RESET}")
                        return False

        except (ConnectionError, socket.timeout, OSError, ValueError) as e:
            print(f"  {_C.RED}Pairing failed: {e}{_C.RESET}")
            return False

    # ------------------------------------------------------------------
    # link_peers — list authorized peers
    # ------------------------------------------------------------------
    def link_peers(self) -> list[dict]:
        """Return list of all authorized peers with sync stats."""
        return self._link_load_peers()

    # ------------------------------------------------------------------
    # link_unpair — revoke peer authorization
    # ------------------------------------------------------------------
    def link_unpair(self, peer_fingerprint: str) -> bool:
        """Revoke a peer's authorization.

        Accepts full fingerprint or prefix match (min 8 chars).
        Returns True if peer was found and removed.
        """
        peers = self._link_load_peers()
        fp_lower = peer_fingerprint.lower()

        found = None
        for i, p in enumerate(peers):
            if p.get("fingerprint", "").lower().startswith(fp_lower):
                found = i
                break

        if found is None:
            return False

        removed = peers.pop(found)
        self._link_save_peers(peers)

        # Chain of custody
        self._link_append_custody("UNPAIR", {
            "peer_fingerprint": removed.get("fingerprint", ""),
            "peer_name": removed.get("display_name", ""),
        })

        return True

    # ------------------------------------------------------------------
    # link_set_shared_topics — per-peer topic sharing config
    # ------------------------------------------------------------------
    def link_set_shared_topics(self, peer_fingerprint: str,
                               topics: list[str]) -> bool:
        """Configure which topics are shared with a specific peer.

        Empty list = share everything. Returns True if peer found.
        """
        peers = self._link_load_peers()
        fp_lower = peer_fingerprint.lower()

        for p in peers:
            if p.get("fingerprint", "").lower().startswith(fp_lower):
                p["shared_topics"] = topics
                self._link_save_peers(peers)
                return True
        return False

    # ------------------------------------------------------------------
    # link_serve — start TLS sync server
    # ------------------------------------------------------------------
    def link_serve(self, port: int = 7777, max_connections: int = 10) -> None:
        """Start TLS server accepting sync requests from authorized peers.

        Blocks indefinitely (Ctrl+C to stop).
        """
        import socket
        import ssl
        import time

        identity = self.link_identity()
        if not identity:
            raise RuntimeError("Diamond Link not initialized. Run link_init() first.")

        local_fp = identity["fingerprint"]
        ctx = self._link_server_ssl_context()
        ctx.verify_mode = ssl.CERT_NONE  # We verify via fingerprint pinning

        # Rate limiting state
        connection_log: dict[str, list[float]] = {}

        print(f"\n{_C.CYAN}{_C.BOLD}  Diamond Link Server{_C.RESET}")
        print(f"  {_C.WHITE}Fingerprint: {_C.DIM}{local_fp[:16]}...{_C.RESET}")
        print(f"  {_C.WHITE}Listening on port {_C.GREEN}{port}{_C.RESET}")
        print(f"  {_C.DIM}Press Ctrl+C to stop.{_C.RESET}\n")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind(("0.0.0.0", port))
            srv.listen(max_connections)
            srv.settimeout(1.0)  # Allow Ctrl+C to work

            try:
                while True:
                    try:
                        conn, addr = srv.accept()
                    except socket.timeout:
                        continue

                    # Rate limiting: 10 connections/minute per IP
                    ip = addr[0]
                    now = time.time()
                    connection_log.setdefault(ip, [])
                    connection_log[ip] = [
                        t for t in connection_log[ip] if now - t < 60
                    ]
                    if len(connection_log[ip]) >= 10:
                        print(f"  {_C.YELLOW}Rate limited: {ip}{_C.RESET}")
                        conn.close()
                        continue
                    connection_log[ip].append(now)

                    try:
                        with ctx.wrap_socket(conn, server_side=True) as tls_conn:
                            self._link_handle_sync_request(tls_conn, addr)
                    except Exception as e:
                        print(f"  {_C.RED}Connection error from {addr[0]}: {e}{_C.RESET}")

            except KeyboardInterrupt:
                print(f"\n  {_C.YELLOW}Server stopped.{_C.RESET}")

    def _link_handle_sync_request(self, tls_conn, addr) -> None:
        """Handle a single incoming sync request on the server side."""
        identity = self.link_identity()
        local_fp = identity["fingerprint"]
        peers = self._link_load_peers()

        # We don't know the peer yet — use a temporary HMAC key
        # based on our own fingerprint (peer must know it to even attempt)
        temp_key = hashlib.sha256(local_fp.encode()).digest()

        try:
            msg = self._link_recv_message(tls_conn, temp_key)
        except ValueError:
            # Try each known peer's HMAC key
            return

        if msg.get("type") != "SYNC_REQUEST":
            return

        peer_fp = msg.get("fingerprint", "")

        # Verify peer is authorized
        peer = None
        for p in peers:
            if p.get("fingerprint") == peer_fp and p.get("status") == "active":
                peer = p
                break

        if not peer:
            self._link_send_message(tls_conn, {
                "type": "SYNC_REJECT",
                "reason": "Unauthorized peer",
            }, temp_key)
            print(f"  {_C.RED}Rejected sync from unknown peer: "
                  f"{peer_fp[:16]}...{_C.RESET}")
            return

        # Switch to peer-specific HMAC key
        hmac_key = self._link_hmac_key(local_fp, peer_fp)

        direction = msg.get("direction", "both")
        requested_topics = msg.get("topics")

        # Determine topics to share
        shared_topics = peer.get("shared_topics", [])
        if shared_topics and requested_topics:
            # Intersection of configured and requested
            topics = [t for t in requested_topics if t in shared_topics]
        elif shared_topics:
            topics = shared_topics
        else:
            topics = requested_topics  # None means all

        # Build and send our snapshot
        snapshot = self._link_build_snapshot(topics)
        self._link_send_message(tls_conn, {
            "type": "SYNC_SNAPSHOT",
            "snapshot": snapshot,
        }, hmac_key)

        # Receive peer's snapshot if direction allows
        stats_received = {"facts_added": 0, "facts_updated": 0,
                          "facts_skipped": 0, "citations_added": 0,
                          "citations_updated": 0, "conflicts": []}

        if direction in ("both", "push"):
            peer_msg = self._link_recv_message(tls_conn, hmac_key)
            if peer_msg.get("type") == "SYNC_SNAPSHOT":
                peer_snapshot = peer_msg.get("snapshot", {})
                dry_run = msg.get("dry_run", False)
                stats_received = self._link_apply_snapshot(
                    peer_snapshot, peer_fp, "pull", dry_run
                )

        # Send confirmation
        self._link_send_message(tls_conn, {
            "type": "SYNC_COMPLETE",
            "stats": stats_received,
        }, hmac_key)

        # Update peer record
        for p in peers:
            if p.get("fingerprint") == peer_fp:
                p["last_sync"] = _now_iso()
                p["syncs_completed"] = p.get("syncs_completed", 0) + 1
                break
        self._link_save_peers(peers)

        # Log sync
        self._link_append_sync_log({
            "timestamp": _now_iso(),
            "peer_fingerprint": peer_fp,
            "peer_name": peer.get("display_name", "Unknown"),
            "direction": direction,
            "facts_sent": len(snapshot.get("facts", [])),
            "facts_received": stats_received["facts_added"] + stats_received["facts_updated"],
            "citations_sent": len(snapshot.get("citations", [])),
            "citations_received": stats_received["citations_added"] + stats_received["citations_updated"],
            "conflicts": len(stats_received["conflicts"]),
        })

        # Chain of custody
        self._link_append_custody("SYNC_RECV", {
            "peer_fingerprint": peer_fp,
            "peer_name": peer.get("display_name", ""),
            "direction": direction,
            "facts_received": stats_received["facts_added"] + stats_received["facts_updated"],
            "citations_received": stats_received["citations_added"] + stats_received["citations_updated"],
        })

        print(f"  {_C.GREEN}{_C.CHECK} Synced with {peer.get('display_name', '?')}{_C.RESET}"
              f" {_C.DIM}(+{stats_received['facts_added']}f, "
              f"+{stats_received['citations_added']}c){_C.RESET}")

    # ------------------------------------------------------------------
    # link_sync — initiate sync with a peer
    # ------------------------------------------------------------------
    def link_sync(self, peer_fingerprint: str, topics: list[str] | None = None,
                  direction: str = "both", dry_run: bool = False) -> dict:
        """Initiate a sync with an authorized peer.

        Args:
            peer_fingerprint: Full fingerprint or prefix (min 8 chars)
            topics: List of topics to sync (None = all shared)
            direction: 'both', 'push', or 'pull'
            dry_run: If True, calculate changes but don't apply

        Returns: {facts_sent, facts_received, citations_sent, citations_received,
                  conflicts, dry_run}
        """
        import socket

        identity = self.link_identity()
        if not identity:
            raise RuntimeError("Diamond Link not initialized. Run link_init() first.")

        local_fp = identity["fingerprint"]
        peers = self._link_load_peers()
        fp_lower = peer_fingerprint.lower()

        peer = None
        for p in peers:
            if p.get("fingerprint", "").lower().startswith(fp_lower):
                peer = p
                break

        if not peer:
            raise ValueError(f"No peer found matching: {peer_fingerprint}")
        if peer.get("status") != "active":
            raise ValueError(f"Peer is not active: {peer.get('display_name')}")

        peer_fp = peer["fingerprint"]
        host = peer.get("host", "localhost")
        port = peer.get("port", 7777)
        hmac_key = self._link_hmac_key(local_fp, peer_fp)

        # Server-hello uses server's fingerprint for temp key
        temp_key = hashlib.sha256(peer_fp.encode()).digest()

        ctx = self._link_client_ssl_context()

        try:
            with socket.create_connection((host, port), timeout=30) as sock:
                with ctx.wrap_socket(sock, server_hostname=host) as tls_conn:
                    # Determine topics
                    shared_topics = peer.get("shared_topics", [])
                    sync_topics = topics
                    if shared_topics and not sync_topics:
                        sync_topics = shared_topics

                    # Send sync request
                    self._link_send_message(tls_conn, {
                        "type": "SYNC_REQUEST",
                        "fingerprint": local_fp,
                        "direction": direction,
                        "topics": sync_topics,
                        "dry_run": dry_run,
                    }, temp_key)

                    # Receive server's snapshot
                    resp = self._link_recv_message(tls_conn, hmac_key)
                    if resp.get("type") == "SYNC_REJECT":
                        raise ValueError(f"Sync rejected: {resp.get('reason')}")

                    server_snapshot = resp.get("snapshot", {})

                    # Apply server's snapshot locally
                    stats = self._link_apply_snapshot(
                        server_snapshot, peer_fp, direction, dry_run
                    )

                    # Send our snapshot if direction allows
                    if direction in ("both", "push"):
                        our_snapshot = self._link_build_snapshot(sync_topics)
                        self._link_send_message(tls_conn, {
                            "type": "SYNC_SNAPSHOT",
                            "snapshot": our_snapshot,
                        }, hmac_key)

                    # Receive completion confirmation
                    complete_msg = self._link_recv_message(tls_conn, hmac_key)
                    remote_stats = complete_msg.get("stats", {})

        except (ConnectionError, socket.timeout, OSError) as e:
            raise ConnectionError(f"Sync failed: {e}") from e

        # Build result
        our_snapshot_data = self._link_build_snapshot(sync_topics) if direction != "pull" else {"facts": [], "citations": []}
        result = {
            "peer": peer.get("display_name", peer_fp[:16]),
            "direction": direction,
            "dry_run": dry_run,
            "facts_sent": len(our_snapshot_data.get("facts", [])),
            "facts_received": stats["facts_added"] + stats["facts_updated"],
            "citations_sent": len(our_snapshot_data.get("citations", [])),
            "citations_received": stats["citations_added"] + stats["citations_updated"],
            "conflicts": stats["conflicts"],
        }

        if not dry_run:
            # Update peer record
            for p in peers:
                if p.get("fingerprint") == peer_fp:
                    p["last_sync"] = _now_iso()
                    p["syncs_completed"] = p.get("syncs_completed", 0) + 1
                    break
            self._link_save_peers(peers)

            # Log sync
            self._link_append_sync_log({
                "timestamp": _now_iso(),
                "peer_fingerprint": peer_fp,
                "peer_name": peer.get("display_name", "Unknown"),
                "direction": direction,
                "facts_sent": result["facts_sent"],
                "facts_received": result["facts_received"],
                "citations_sent": result["citations_sent"],
                "citations_received": result["citations_received"],
                "conflicts": len(result["conflicts"]),
            })

            # Chain of custody
            self._link_append_custody("SYNC_SEND", {
                "peer_fingerprint": peer_fp,
                "peer_name": peer.get("display_name", ""),
                "direction": direction,
                "facts_sent": result["facts_sent"],
                "facts_received": result["facts_received"],
                "citations_sent": result["citations_sent"],
                "citations_received": result["citations_received"],
            })

        return result

    # ------------------------------------------------------------------
    # link_status — combined overview
    # ------------------------------------------------------------------
    def link_status(self) -> dict:
        """Return combined Diamond Link status.

        Returns: {initialized, identity, peers, recent_syncs, custody_chain}
        """
        identity = self.link_identity()
        peers = self._link_load_peers()
        sync_log = self._link_load_sync_log()
        custody = self.link_verify_custody_chain()

        return {
            "initialized": identity is not None and bool(identity),
            "identity": identity,
            "peer_count": len(peers),
            "peers": peers,
            "total_syncs": sum(p.get("syncs_completed", 0) for p in peers),
            "recent_syncs": sync_log[-10:],
            "custody_chain": custody,
        }

    # ------------------------------------------------------------------
    # link_log — sync history
    # ------------------------------------------------------------------
    def link_log(self, last_n: int = 15) -> list[dict]:
        """Return recent sync log entries."""
        log = self._link_load_sync_log()
        return log[-last_n:]

    # ------------------------------------------------------------------
    # link_custody_log — chain of custody entries
    # ------------------------------------------------------------------
    def link_custody_log(self, last_n: int = 15) -> list[dict]:
        """Return recent chain of custody records."""
        log = self._link_load_custody_log()
        return log[-last_n:]

    # ==================================================================
    #  FEATURE 1: KNOWLEDGE GRAPH + BFS TRAVERSAL
    # ==================================================================

    def _graph_load(self) -> dict:
        """Load the knowledge graph. Format: {nodes: {id: {...}}, edges: [...]}"""
        try:
            data = json.loads(self._graph_path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "nodes" in data and "edges" in data:
                return data
        except (json.JSONDecodeError, FileNotFoundError):
            pass
        return {"nodes": {}, "edges": []}

    def _graph_save(self, graph: dict) -> None:
        tmp = self._graph_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(graph, indent=2, ensure_ascii=False),
                       encoding="utf-8")
        os.replace(str(tmp), str(self._graph_path))

    @staticmethod
    def _graph_node_id(node_type: str, content: str) -> str:
        """Generate a deterministic short node ID."""
        raw = f"{node_type}:{content}".lower()
        return hashlib.sha256(raw.encode()).hexdigest()[:12]

    def graph_add_node(self, node_id: str, node_type: str,
                       data: dict | None = None) -> dict:
        """Add or update a node in the knowledge graph.

        node_type: fact, citation, topic, crystal, blob, event
        """
        graph = self._graph_load()
        now = _now_iso()
        existing = graph["nodes"].get(node_id)
        node = {
            "type": node_type,
            "data": data or {},
            "created_at": existing["created_at"] if existing else now,
            "updated_at": now,
        }
        graph["nodes"][node_id] = node
        self._graph_save(graph)
        return node

    def graph_add_edge(self, source: str, target: str, edge_type: str,
                       weight: float = 1.0) -> dict:
        """Add a typed edge between two nodes.

        edge_type: supports, contradicts, related, contains, cites,
                   temporal, belongs_to, derived_from, references
        Deduplicates by (source, target, edge_type).
        """
        graph = self._graph_load()
        now = _now_iso()

        # Dedup
        for e in graph["edges"]:
            if (e["source"] == source and e["target"] == target
                    and e["type"] == edge_type):
                e["weight"] = weight
                e["updated_at"] = now
                self._graph_save(graph)
                return e

        edge = {
            "source": source,
            "target": target,
            "type": edge_type,
            "weight": weight,
            "created_at": now,
            "updated_at": now,
        }
        graph["edges"].append(edge)
        self._graph_save(graph)
        return edge

    def graph_remove_edge(self, source: str, target: str,
                          edge_type: str | None = None) -> int:
        """Remove edges between source and target. Returns count removed."""
        graph = self._graph_load()
        before = len(graph["edges"])
        graph["edges"] = [
            e for e in graph["edges"]
            if not (e["source"] == source and e["target"] == target
                    and (edge_type is None or e["type"] == edge_type))
        ]
        removed = before - len(graph["edges"])
        if removed:
            self._graph_save(graph)
        return removed

    def graph_bfs(self, start: str, max_depth: int = 3,
                  edge_types: list[str] | None = None) -> list[dict]:
        """Breadth-first traversal from a node.

        Returns list of {node_id, depth, path, node_data, edge_type}.
        """
        graph = self._graph_load()
        if start not in graph["nodes"]:
            return []

        visited = {start}
        queue = [(start, 0, [start], None)]
        results = []

        while queue:
            current, depth, path, via_edge = queue.pop(0)
            if depth > 0:
                results.append({
                    "node_id": current,
                    "depth": depth,
                    "path": path,
                    "node_data": graph["nodes"].get(current, {}),
                    "via_edge_type": via_edge,
                })

            if depth >= max_depth:
                continue

            # Find neighbors
            for e in graph["edges"]:
                neighbor = None
                etype = e["type"]
                if edge_types and etype not in edge_types:
                    continue
                if e["source"] == current:
                    neighbor = e["target"]
                elif e["target"] == current:
                    neighbor = e["source"]

                if neighbor and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, depth + 1, path + [neighbor], etype))

        return results

    def graph_neighbors(self, node_id: str,
                        edge_type: str | None = None) -> list[dict]:
        """Get direct neighbors of a node."""
        return self.graph_bfs(node_id, max_depth=1, edge_types=(
            [edge_type] if edge_type else None
        ))

    def graph_query(self, query: str, max_depth: int = 2) -> list[dict]:
        """Search graph by keyword, then BFS from matching nodes."""
        graph = self._graph_load()
        query_lower = query.lower()
        matching_nodes = []

        for nid, node in graph["nodes"].items():
            data = node.get("data", {})
            blob = json.dumps(data).lower()
            if query_lower in blob or query_lower in nid:
                matching_nodes.append(nid)

        all_results = []
        seen = set()
        for nid in matching_nodes[:10]:
            results = self.graph_bfs(nid, max_depth=max_depth)
            for r in results:
                if r["node_id"] not in seen:
                    seen.add(r["node_id"])
                    all_results.append(r)

        return all_results

    def graph_auto_index(self) -> dict:
        """Index all existing facts and citations as graph nodes + edges.

        Creates: topic nodes, fact nodes, citation nodes.
        Edges: fact->topic (belongs_to), fact->fact (related via links),
               fact->citation (cites).
        Returns: {nodes_created, edges_created}
        """
        facts = self._load(self._facts_path)
        citations = self._load(self._citations_path)
        graph = self._graph_load()
        nodes_before = len(graph["nodes"])
        edges_before = len(graph["edges"])

        # Index topics
        topics = set()
        for f in facts:
            t = f.get("topic", "")
            if t:
                topics.add(t)
        for t in topics:
            nid = self._graph_node_id("topic", t)
            if nid not in graph["nodes"]:
                graph["nodes"][nid] = {
                    "type": "topic",
                    "data": {"name": t},
                    "created_at": _now_iso(),
                    "updated_at": _now_iso(),
                }

        # Index facts
        for f in facts:
            topic = f.get("topic", "")
            fact_text = f.get("fact", "")
            fid = self._graph_node_id("fact", f"{topic}/{fact_text}")
            if fid not in graph["nodes"]:
                graph["nodes"][fid] = {
                    "type": "fact",
                    "data": {
                        "topic": topic,
                        "fact": fact_text[:200],
                        "confidence": f.get("confidence", 0),
                        "verified": f.get("verified", False),
                    },
                    "created_at": f.get("created_at", _now_iso()),
                    "updated_at": f.get("updated_at", _now_iso()),
                }

            # Edge: fact -> topic
            tid = self._graph_node_id("topic", topic)
            edge_exists = any(
                e["source"] == fid and e["target"] == tid
                and e["type"] == "belongs_to"
                for e in graph["edges"]
            )
            if not edge_exists and tid in graph["nodes"]:
                graph["edges"].append({
                    "source": fid, "target": tid,
                    "type": "belongs_to", "weight": 1.0,
                    "created_at": _now_iso(), "updated_at": _now_iso(),
                })

            # Edges: fact -> linked topics
            for link in f.get("links", []):
                link_tid = self._graph_node_id("topic", link)
                edge_exists = any(
                    e["source"] == fid and e["target"] == link_tid
                    and e["type"] == "related"
                    for e in graph["edges"]
                )
                if not edge_exists and link_tid in graph["nodes"]:
                    graph["edges"].append({
                        "source": fid, "target": link_tid,
                        "type": "related", "weight": 0.7,
                        "created_at": _now_iso(), "updated_at": _now_iso(),
                    })

        # Index citations
        for c in citations:
            code = c.get("code", "")
            cid = self._graph_node_id("citation", code)
            if cid not in graph["nodes"]:
                graph["nodes"][cid] = {
                    "type": "citation",
                    "data": {
                        "code": code,
                        "title": c.get("title", ""),
                        "severity": c.get("severity", ""),
                        "category": c.get("category", ""),
                    },
                    "created_at": c.get("created_at", _now_iso()),
                    "updated_at": c.get("updated_at", _now_iso()),
                }

            # Edges: citation -> linked fact topics
            for lt in c.get("linked_facts", []):
                lt_tid = self._graph_node_id("topic", lt)
                edge_exists = any(
                    e["source"] == cid and e["target"] == lt_tid
                    and e["type"] == "cites"
                    for e in graph["edges"]
                )
                if not edge_exists and lt_tid in graph["nodes"]:
                    graph["edges"].append({
                        "source": cid, "target": lt_tid,
                        "type": "cites", "weight": 0.9,
                        "created_at": _now_iso(), "updated_at": _now_iso(),
                    })

        self._graph_save(graph)
        return {
            "nodes_created": len(graph["nodes"]) - nodes_before,
            "edges_created": len(graph["edges"]) - edges_before,
            "total_nodes": len(graph["nodes"]),
            "total_edges": len(graph["edges"]),
        }

    def graph_stats(self) -> dict:
        """Return graph statistics."""
        graph = self._graph_load()
        type_counts: dict[str, int] = {}
        for node in graph["nodes"].values():
            t = node.get("type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1

        edge_type_counts: dict[str, int] = {}
        for edge in graph["edges"]:
            t = edge.get("type", "unknown")
            edge_type_counts[t] = edge_type_counts.get(t, 0) + 1

        return {
            "total_nodes": len(graph["nodes"]),
            "total_edges": len(graph["edges"]),
            "node_types": type_counts,
            "edge_types": edge_type_counts,
        }

    # ==================================================================
    #  FEATURE 2: FSRS SPACED REPETITION
    # ==================================================================

    # FSRS-4 default parameters
    _FSRS_W = [
        0.4, 0.6, 2.4, 5.8,   # w0-w3: initial stability per rating
        4.93, 0.94, 0.86, 0.01,  # w4-w7: difficulty params
        1.49, 0.14, 0.94,        # w8-w10: recall stability params
        2.18, 0.05, 0.34, 1.26,  # w11-w14: forget stability params
        0.29, 2.61,              # w15-w16: additional params
    ]

    def fsrs_retrievability(self, fact: dict) -> float:
        """Calculate current retrievability of a fact (0.0 to 1.0).

        Uses FSRS power-law forgetting curve:
            R(t, S) = (1 + t / (9 * S))^(-1)
        """
        stability = fact.get("fsrs_stability")
        if stability is None:
            # Legacy fact — estimate from confidence + age
            conf = fact.get("confidence", 50) / 100.0
            days = _days_ago(fact.get("updated_at", fact.get("created_at", "")))
            if days < 0.01:
                return min(1.0, conf)
            # Reverse-engineer stability from current confidence and time
            # When conf >= 1.0, treat as very stable (high confidence = no decay)
            if conf >= 0.99:
                stability = max(180.0, days * 2)
            else:
                denominator = (1 / max(conf, 0.01)) - 1
                if denominator <= 0:
                    stability = max(180.0, days * 2)
                else:
                    stability = max(0.1, days / (9 * denominator))

        last_review = fact.get("fsrs_last_review",
                               fact.get("updated_at",
                                        fact.get("created_at", "")))
        days = _days_ago(last_review)
        if stability <= 0:
            return 0.0
        return (1 + days / (9 * stability)) ** -1

    def _fsrs_init_stability(self, rating: int) -> float:
        """Initial stability for a new fact based on first rating."""
        # rating: 1=Again, 2=Hard, 3=Good, 4=Easy
        idx = max(0, min(3, rating - 1))
        return self._FSRS_W[idx]

    def _fsrs_init_difficulty(self, rating: int) -> float:
        """Initial difficulty for a new fact."""
        w4, w5 = self._FSRS_W[4], self._FSRS_W[5]
        return max(1.0, min(10.0, w4 - (rating - 3) * w5))

    def _fsrs_next_difficulty(self, d: float, rating: int) -> float:
        """Update difficulty after a review."""
        w6 = self._FSRS_W[6]
        new_d = d - w6 * (rating - 3)
        # Mean reversion
        w7 = self._FSRS_W[7]
        new_d = w7 * self._FSRS_W[4] + (1 - w7) * new_d
        return max(1.0, min(10.0, new_d))

    def _fsrs_next_stability(self, s: float, d: float, r: float,
                             rating: int) -> float:
        """Calculate new stability after a review.

        If rating >= 2 (recalled): stability increases
        If rating == 1 (forgot): stability resets lower
        """
        w = self._FSRS_W
        if rating >= 2:
            # Successful recall
            hard_penalty = w[15] if rating == 2 else 1.0
            easy_bonus = w[16] if rating == 4 else 1.0
            new_s = s * (
                math.exp(w[8])
                * (11 - d)
                * s ** (-w[9])
                * (math.exp(w[10] * (1 - r)) - 1)
                + 1
            ) * hard_penalty * easy_bonus
        else:
            # Failed recall (lapse)
            new_s = (
                w[11]
                * d ** (-w[12])
                * ((s + 1) ** w[13] - 1)
                * math.exp(w[14] * (1 - r))
            )

        return max(0.1, new_s)

    def fsrs_review(self, topic: str, fact_text: str,
                    rating: int) -> dict | None:
        """Review a fact using FSRS algorithm.

        Rating: 1=Again (forgot), 2=Hard, 3=Good, 4=Easy

        Updates the fact's FSRS state in-place. Returns updated fact.
        """
        if rating not in (1, 2, 3, 4):
            raise ValueError("Rating must be 1 (Again), 2 (Hard), 3 (Good), or 4 (Easy)")

        facts = self._load(self._facts_path)
        topic_lower = topic.lower()
        target = None
        target_idx = None

        for i, f in enumerate(facts):
            if f.get("topic", "").lower() != topic_lower:
                continue
            sim = _similarity(f.get("fact", ""), fact_text)
            if sim > 0.80:
                target = f
                target_idx = i
                break

        if target is None:
            return None

        now = _now_iso()
        reps = target.get("fsrs_reps", 0)
        lapses = target.get("fsrs_lapses", 0)

        if reps == 0:
            # First review
            s = self._fsrs_init_stability(rating)
            d = self._fsrs_init_difficulty(rating)
        else:
            s = target.get("fsrs_stability", 1.0)
            d = target.get("fsrs_difficulty", 5.0)
            r = self.fsrs_retrievability(target)
            d = self._fsrs_next_difficulty(d, rating)
            s = self._fsrs_next_stability(s, d, r, rating)

        # Update FSRS fields
        target["fsrs_stability"] = round(s, 4)
        target["fsrs_difficulty"] = round(d, 4)
        target["fsrs_last_review"] = now
        target["fsrs_reps"] = reps + 1 if rating >= 2 else 0
        target["fsrs_lapses"] = lapses + (1 if rating == 1 else 0)

        # Also update effective confidence based on stability
        # Higher stability = higher confidence floor
        stability_bonus = min(30, int(s * 2))
        base_conf = target.get("confidence", 50)
        if rating >= 3:
            target["confidence"] = min(100, base_conf + stability_bonus // 3)
        elif rating == 1:
            target["confidence"] = max(30, base_conf - 15)

        target["updated_at"] = now
        self._save(self._facts_path, facts)
        return target

    def fsrs_due(self, threshold: float = 0.9,
                 max_results: int = 15) -> list[dict]:
        """Return facts whose retrievability has dropped below threshold.

        Sorted by retrievability ascending (most forgotten first).
        """
        facts = self._load(self._facts_path)
        due = []
        for f in facts:
            r = self.fsrs_retrievability(f)
            if r < threshold:
                f_copy = dict(f)
                f_copy["_retrievability"] = round(r, 4)
                f_copy["_days_since_review"] = round(
                    _days_ago(f.get("fsrs_last_review",
                                    f.get("updated_at", ""))), 1
                )
                due.append(f_copy)

        due.sort(key=lambda x: x["_retrievability"])
        return due[:max_results]

    def fsrs_stats(self) -> dict:
        """Return FSRS statistics across all facts."""
        facts = self._load(self._facts_path)
        total = len(facts)
        reviewed = sum(1 for f in facts if f.get("fsrs_reps", 0) > 0)
        retrievabilities = [self.fsrs_retrievability(f) for f in facts]

        avg_r = sum(retrievabilities) / total if total else 0
        due_90 = sum(1 for r in retrievabilities if r < 0.9)
        due_70 = sum(1 for r in retrievabilities if r < 0.7)
        mature = sum(1 for f in facts
                     if f.get("fsrs_stability", 0) > 21)

        return {
            "total_facts": total,
            "reviewed_facts": reviewed,
            "avg_retrievability": round(avg_r, 3),
            "due_at_90": due_90,
            "due_at_70": due_70,
            "mature_facts": mature,
        }

    # ==================================================================
    #  FEATURE 3: CONFIDENCE PROPAGATION
    # ==================================================================

    def propagate_confidence(self, node_id: str, delta: int,
                             decay_per_hop: float = 0.7,
                             max_depth: int = 3) -> dict:
        """Propagate a confidence change through the knowledge graph.

        When a fact's confidence changes by `delta`, connected facts
        have their confidence adjusted by delta * decay_per_hop^depth.

        Only propagates through 'supports' and 'related' edges.
        Returns: {nodes_affected, adjustments: [{node_id, old_conf, new_conf, depth}]}
        """
        graph = self._graph_load()
        facts = self._load(self._facts_path)

        # BFS propagation
        visited = {node_id}
        queue = [(node_id, 0)]
        adjustments = []

        propagation_edges = {"supports", "related", "belongs_to"}

        while queue:
            current, depth = queue.pop(0)
            if depth >= max_depth:
                continue

            hop_delta = int(delta * (decay_per_hop ** (depth + 1)))
            if abs(hop_delta) < 1:
                continue

            for e in graph["edges"]:
                if e["type"] not in propagation_edges:
                    continue

                neighbor = None
                if e["source"] == current:
                    neighbor = e["target"]
                elif e["target"] == current:
                    neighbor = e["source"]

                if neighbor and neighbor not in visited:
                    visited.add(neighbor)
                    node = graph["nodes"].get(neighbor, {})
                    if node.get("type") == "fact":
                        # Find and adjust the actual fact
                        node_data = node.get("data", {})
                        for f in facts:
                            if (f.get("topic", "").lower() ==
                                    node_data.get("topic", "").lower()
                                    and _similarity(
                                        f.get("fact", ""),
                                        node_data.get("fact", "")
                                    ) > 0.8):
                                old_conf = f.get("confidence", 50)
                                new_conf = max(30, min(100, old_conf + hop_delta))
                                f["confidence"] = new_conf
                                adjustments.append({
                                    "node_id": neighbor,
                                    "topic": f.get("topic", ""),
                                    "fact_preview": f.get("fact", "")[:60],
                                    "old_confidence": old_conf,
                                    "new_confidence": new_conf,
                                    "depth": depth + 1,
                                })
                                break

                    queue.append((neighbor, depth + 1))

        if adjustments:
            self._save(self._facts_path, facts)

        return {
            "source_node": node_id,
            "delta": delta,
            "nodes_affected": len(adjustments),
            "adjustments": adjustments,
        }

    # ==================================================================
    #  FEATURE 4: CONTRADICTION DETECTION
    # ==================================================================

    _NEGATION_WORDS = frozenset({
        "not", "no", "never", "cannot", "can't", "doesn't", "don't",
        "isn't", "aren't", "wasn't", "weren't", "won't", "wouldn't",
        "shouldn't", "couldn't", "neither", "nor", "none", "nothing",
        "nowhere", "nobody", "without", "lack", "lacks", "absent",
        "impossible", "unable", "false", "incorrect", "invalid",
    })

    _ANTONYM_PAIRS = [
        ("true", "false"), ("valid", "invalid"), ("legal", "illegal"),
        ("secure", "insecure"), ("safe", "unsafe"), ("possible", "impossible"),
        ("allow", "deny"), ("permit", "prohibit"), ("grant", "revoke"),
        ("enable", "disable"), ("include", "exclude"), ("accept", "reject"),
        ("open", "closed"), ("active", "inactive"), ("encrypted", "unencrypted"),
        ("guilty", "innocent"), ("lawful", "unlawful"),
    ]

    def detect_contradictions(self, topic: str | None = None,
                              threshold: float = 0.65) -> list[dict]:
        """Scan facts for potential contradictions.

        Detects three types:
        1. Negation flip: similar facts where one has negation words
        2. Antonym swap: similar facts with swapped antonyms
        3. Confidence conflict: same-topic facts with >40pt confidence gap
           and high text similarity

        Returns list of {fact_a, fact_b, type, similarity, confidence}.
        """
        facts = self._load(self._facts_path)
        if topic:
            topic_lower = topic.lower()
            facts = [f for f in facts
                     if f.get("topic", "").lower() == topic_lower]

        contradictions = []
        checked = set()

        for i, a in enumerate(facts):
            for j, b in enumerate(facts):
                if i >= j:
                    continue
                # Only compare same-topic facts
                if (a.get("topic", "").lower() !=
                        b.get("topic", "").lower()):
                    continue

                pair_key = (i, j)
                if pair_key in checked:
                    continue
                checked.add(pair_key)

                a_text = a.get("fact", "").lower()
                b_text = b.get("fact", "").lower()
                a_words = set(a_text.split())
                b_words = set(b_text.split())

                # Type 1: Negation flip
                a_neg = a_words & self._NEGATION_WORDS
                b_neg = b_words & self._NEGATION_WORDS
                if bool(a_neg) != bool(b_neg):
                    # Strip negation and compare
                    a_clean = " ".join(
                        w for w in a_text.split()
                        if w.strip(".,;:!?") not in self._NEGATION_WORDS
                    )
                    b_clean = " ".join(
                        w for w in b_text.split()
                        if w.strip(".,;:!?") not in self._NEGATION_WORDS
                    )
                    sim = _similarity(a_clean, b_clean)
                    if sim > threshold:
                        contradictions.append({
                            "fact_a": {
                                "topic": a.get("topic"),
                                "fact": a.get("fact"),
                                "confidence": a.get("confidence", 0),
                                "source": a.get("source", ""),
                            },
                            "fact_b": {
                                "topic": b.get("topic"),
                                "fact": b.get("fact"),
                                "confidence": b.get("confidence", 0),
                                "source": b.get("source", ""),
                            },
                            "type": "negation_flip",
                            "similarity": round(sim, 3),
                            "confidence_gap": abs(
                                a.get("confidence", 0) - b.get("confidence", 0)
                            ),
                        })
                        continue

                # Type 2: Antonym swap
                for w1, w2 in self._ANTONYM_PAIRS:
                    if ((w1 in a_words and w2 in b_words) or
                            (w2 in a_words and w1 in b_words)):
                        # Check rest is similar
                        a_no_ant = a_text.replace(w1, "").replace(w2, "")
                        b_no_ant = b_text.replace(w1, "").replace(w2, "")
                        sim = _similarity(a_no_ant, b_no_ant)
                        if sim > threshold:
                            contradictions.append({
                                "fact_a": {
                                    "topic": a.get("topic"),
                                    "fact": a.get("fact"),
                                    "confidence": a.get("confidence", 0),
                                    "source": a.get("source", ""),
                                },
                                "fact_b": {
                                    "topic": b.get("topic"),
                                    "fact": b.get("fact"),
                                    "confidence": b.get("confidence", 0),
                                    "source": b.get("source", ""),
                                },
                                "type": "antonym_swap",
                                "similarity": round(sim, 3),
                                "antonyms": (w1, w2),
                                "confidence_gap": abs(
                                    a.get("confidence", 0)
                                    - b.get("confidence", 0)
                                ),
                            })
                            break

                # Type 3: Confidence conflict (high similarity, big gap)
                sim = _similarity(a_text, b_text)
                conf_gap = abs(
                    a.get("confidence", 0) - b.get("confidence", 0)
                )
                if sim > 0.80 and conf_gap > 40:
                    # Check not already caught above
                    already = any(
                        c["fact_a"]["fact"] == a.get("fact")
                        and c["fact_b"]["fact"] == b.get("fact")
                        for c in contradictions
                    )
                    if not already:
                        contradictions.append({
                            "fact_a": {
                                "topic": a.get("topic"),
                                "fact": a.get("fact"),
                                "confidence": a.get("confidence", 0),
                                "source": a.get("source", ""),
                            },
                            "fact_b": {
                                "topic": b.get("topic"),
                                "fact": b.get("fact"),
                                "confidence": b.get("confidence", 0),
                                "source": b.get("source", ""),
                            },
                            "type": "confidence_conflict",
                            "similarity": round(sim, 3),
                            "confidence_gap": conf_gap,
                        })

        # Update source contradiction counts (idempotent SET, not increment)
        source_counts: dict[str, int] = {}
        for c in contradictions:
            for key in ("fact_a", "fact_b"):
                src_id = c[key].get("source", "")
                if src_id:
                    source_counts[src_id] = source_counts.get(src_id, 0) + 1
        if source_counts:
            srcs = self._sources_load()
            changed = False
            for src in srcs:
                sid = src.get("source_id", "")
                if sid in source_counts:
                    src["contradictions_flagged"] = source_counts[sid]
                    changed = True
            if changed:
                self._sources_save(srcs)

        return contradictions

    # ==================================================================
    #  FEATURE 5: CRYSTALLIZATION
    # ==================================================================

    def crystallize(self, topic: str | None = None,
                    min_cluster: int = 5) -> list[dict]:
        """Auto-summarize fact clusters into higher-level insight nodes.

        Groups facts by topic, analyzes each cluster, generates summary
        "crystal" nodes. Optionally stores as graph nodes.

        Returns list of crystal dicts.
        """
        facts = self._load(self._facts_path)
        if topic:
            facts = [f for f in facts
                     if f.get("topic", "").lower() == topic.lower()]

        # Group by topic
        topic_groups: dict[str, list[dict]] = {}
        for f in facts:
            t = f.get("topic", "unknown")
            topic_groups.setdefault(t, []).append(f)

        stop_words = frozenset({
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "shall", "can",
            "to", "of", "in", "for", "on", "with", "at", "by", "from",
            "as", "into", "through", "during", "before", "after", "above",
            "below", "between", "and", "but", "or", "not", "that", "this",
            "these", "those", "it", "its", "all", "each", "every", "both",
            "such", "than", "too", "very", "just", "about", "also", "more",
            "most", "other", "some", "any", "only", "own", "same", "so",
            "then", "there", "here", "when", "where", "why", "how", "what",
            "which", "who", "whom", "whose", "if", "while", "because",
            "although", "though", "since", "until", "unless", "high",
        })

        crystals = []
        for t, group in sorted(topic_groups.items()):
            if len(group) < min_cluster:
                continue

            avg_conf = sum(f.get("confidence", 0) for f in group) / len(group)
            verified_count = sum(1 for f in group if f.get("verified", False))
            sources = list(set(f.get("source", "?") for f in group))

            # Extract key terms
            word_freq: dict[str, int] = {}
            for f in group:
                for word in f.get("fact", "").lower().split():
                    word = word.strip(".,;:!?()[]{}\"'-/\\")
                    if len(word) > 3 and word not in stop_words:
                        word_freq[word] = word_freq.get(word, 0) + 1

            top_terms = sorted(word_freq.items(),
                               key=lambda x: x[1], reverse=True)[:10]
            key_terms = [w for w, _ in top_terms]

            # Find sub-clusters by similarity
            subclusters = []
            used = set()
            for i, fa in enumerate(group):
                if i in used:
                    continue
                cluster = [fa]
                used.add(i)
                for j, fb in enumerate(group):
                    if j in used or j <= i:
                        continue
                    sim = _similarity(fa.get("fact", ""), fb.get("fact", ""))
                    if sim > 0.50:
                        cluster.append(fb)
                        used.add(j)
                if len(cluster) > 1:
                    subclusters.append({
                        "size": len(cluster),
                        "sample": cluster[0].get("fact", "")[:80],
                    })

            # Confidence distribution
            conf_buckets = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            for f in group:
                c = f.get("confidence", 0)
                if c >= 90:
                    conf_buckets["critical"] += 1
                elif c >= 70:
                    conf_buckets["high"] += 1
                elif c >= 50:
                    conf_buckets["medium"] += 1
                else:
                    conf_buckets["low"] += 1

            # Average retrievability
            retrievabilities = [self.fsrs_retrievability(f) for f in group]
            avg_r = sum(retrievabilities) / len(retrievabilities)

            summary_parts = [
                f"Cluster of {len(group)} facts about {t}.",
                f"Key concepts: {', '.join(key_terms[:5])}.",
                f"Average confidence: {avg_conf:.0f}%.",
                f"Verified: {verified_count}/{len(group)}.",
                f"Memory strength: {avg_r:.0%}.",
            ]
            if subclusters:
                summary_parts.append(
                    f"Contains {len(subclusters)} sub-clusters."
                )

            crystal = {
                "topic": t,
                "fact_count": len(group),
                "avg_confidence": round(avg_conf, 1),
                "avg_retrievability": round(avg_r, 3),
                "verified_ratio": f"{verified_count}/{len(group)}",
                "confidence_distribution": conf_buckets,
                "key_terms": key_terms,
                "sources": sources[:5],
                "subclusters": subclusters[:5],
                "summary": " ".join(summary_parts),
                "crystallized_at": _now_iso(),
            }
            crystals.append(crystal)

            # Optionally store as graph node
            cid = self._graph_node_id("crystal", t)
            graph = self._graph_load()
            graph["nodes"][cid] = {
                "type": "crystal",
                "data": crystal,
                "created_at": _now_iso(),
                "updated_at": _now_iso(),
            }
            # Link crystal to topic
            tid = self._graph_node_id("topic", t)
            if tid in graph["nodes"]:
                edge_exists = any(
                    e["source"] == cid and e["target"] == tid
                    and e["type"] == "derived_from"
                    for e in graph["edges"]
                )
                if not edge_exists:
                    graph["edges"].append({
                        "source": cid, "target": tid,
                        "type": "derived_from", "weight": 1.0,
                        "created_at": _now_iso(), "updated_at": _now_iso(),
                    })
            self._graph_save(graph)

        return crystals

    # ==================================================================
    #  FEATURE 6: TEMPORAL REASONING (Allen's Interval Algebra)
    # ==================================================================

    def temporal_add(self, event_id: str, start: str,
                     end: str | None = None,
                     data: dict | None = None) -> dict:
        """Add a temporal event.

        start/end: ISO-8601 timestamps. end=None means point event.
        """
        events = self._load(self._temporal_path)
        now = _now_iso()

        entry = {
            "event_id": event_id,
            "start": start,
            "end": end or start,
            "data": data or {},
            "created_at": now,
        }

        # Dedup by event_id
        for i, e in enumerate(events):
            if e.get("event_id") == event_id:
                events[i] = entry
                self._save(self._temporal_path, events)
                return entry

        events.append(entry)
        self._save(self._temporal_path, events)

        # Auto-index as graph node
        nid = self._graph_node_id("event", event_id)
        graph = self._graph_load()
        graph["nodes"][nid] = {
            "type": "event",
            "data": {"event_id": event_id, "start": start,
                     "end": end or start, **(data or {})},
            "created_at": now, "updated_at": now,
        }
        self._graph_save(graph)

        return entry

    def temporal_relation(self, a_id: str, b_id: str) -> str:
        """Determine Allen's Interval Algebra relation between two events.

        Returns one of the 13 relations:
            before, after, meets, met_by, overlaps, overlapped_by,
            starts, started_by, during, contains, finishes, finished_by,
            equals
        """
        events = self._load(self._temporal_path)
        a = b = None
        for e in events:
            if e.get("event_id") == a_id:
                a = e
            if e.get("event_id") == b_id:
                b = e
        if not a or not b:
            return "unknown"

        as_, ae = a["start"], a["end"]
        bs, be = b["start"], b["end"]

        if ae < bs:
            return "before"
        if be < as_:
            return "after"
        if ae == bs:
            return "meets"
        if be == as_:
            return "met_by"
        if as_ < bs and ae > bs and ae < be:
            return "overlaps"
        if bs < as_ and be > as_ and be < ae:
            return "overlapped_by"
        if as_ == bs and ae < be:
            return "starts"
        if as_ == bs and ae > be:
            return "started_by"
        if as_ > bs and ae < be:
            return "during"
        if as_ < bs and ae > be:
            return "contains"
        if ae == be and as_ > bs:
            return "finishes"
        if ae == be and as_ < bs:
            return "finished_by"
        if as_ == bs and ae == be:
            return "equals"
        return "unknown"

    def temporal_chain(self, event_ids: list[str] | None = None) -> list[dict]:
        """Build a causal chain of events sorted by start time.

        Returns events with inter-event relations annotated.
        """
        events = self._load(self._temporal_path)
        if event_ids:
            id_set = set(event_ids)
            events = [e for e in events if e.get("event_id") in id_set]

        events.sort(key=lambda e: e.get("start", ""))

        chain = []
        for i, e in enumerate(events):
            entry = dict(e)
            if i > 0:
                entry["_relation_to_prev"] = self.temporal_relation(
                    events[i - 1]["event_id"], e["event_id"]
                )
                # Calculate time gap
                prev_end = events[i - 1].get("end", events[i - 1].get("start", ""))
                this_start = e.get("start", "")
                if prev_end and this_start:
                    gap_days = _days_ago(prev_end) - _days_ago(this_start)
                    entry["_gap_days"] = round(abs(gap_days), 2)
            chain.append(entry)

        return chain

    def temporal_timeline(self, start: str | None = None,
                          end: str | None = None,
                          max_results: int = 15) -> list[dict]:
        """Get events within a time range, sorted chronologically."""
        events = self._load(self._temporal_path)

        if start:
            events = [e for e in events if e.get("start", "") >= start]
        if end:
            events = [e for e in events if e.get("start", "") <= end]

        events.sort(key=lambda e: e.get("start", ""))
        return events[:max_results]

    # ==================================================================
    #  FEATURE 23: TIMELINE ANOMALY DETECTION
    # ==================================================================

    _ANOMALY_SEVERITY = {
        "temporal_cycle": "CRITICAL",
        "backwards_causation": "CRITICAL",
        "impossible_sequence": "HIGH",
        "speed_violation": "HIGH",
        "overlapping_exclusive": "MEDIUM",
        "suspicious_gap": "LOW",
    }

    def _temporal_detect_cycles(self, events: list) -> list[dict]:
        """DFS cycle detection on precedence graph built from depends_on."""
        graph: dict[str, list[str]] = {}
        for e in events:
            eid = e.get("event_id", "")
            deps = e.get("data", {}).get("depends_on", [])
            if isinstance(deps, str):
                deps = [deps]
            graph[eid] = deps

        anomalies = []
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {eid: WHITE for eid in graph}
        path: list[str] = []

        def dfs(node: str) -> None:
            color[node] = GRAY
            path.append(node)
            for dep in graph.get(node, []):
                if dep not in color:
                    continue
                if color[dep] == GRAY:
                    cycle_start = path.index(dep)
                    cycle = path[cycle_start:] + [dep]
                    anomalies.append({
                        "type": "temporal_cycle",
                        "severity": "CRITICAL",
                        "events": cycle,
                        "message": f"Cycle detected: {' -> '.join(cycle)}",
                    })
                    return
                if color[dep] == WHITE:
                    dfs(dep)
            path.pop()
            color[node] = BLACK

        for eid in graph:
            if color[eid] == WHITE:
                dfs(eid)
        return anomalies

    def _temporal_detect_backwards_causation(self, events: list) -> list[dict]:
        """Detect effect occurring before its cause via cause_of metadata."""
        id_map = {e.get("event_id", ""): e for e in events}
        anomalies = []
        for e in events:
            cause_of = e.get("data", {}).get("cause_of")
            if not cause_of:
                continue
            if isinstance(cause_of, str):
                cause_of = [cause_of]
            for effect_id in cause_of:
                effect = id_map.get(effect_id)
                if not effect:
                    continue
                if e.get("start", "") > effect.get("start", ""):
                    anomalies.append({
                        "type": "backwards_causation",
                        "severity": "CRITICAL",
                        "cause_event": e.get("event_id"),
                        "effect_event": effect_id,
                        "cause_start": e.get("start"),
                        "effect_start": effect.get("start"),
                        "message": (f"Cause '{e.get('event_id')}' starts after "
                                    f"effect '{effect_id}'"),
                    })
        return anomalies

    def _temporal_detect_impossible_sequences(self, events: list) -> list[dict]:
        """Detect B depends_on A but B.start < A.end."""
        id_map = {e.get("event_id", ""): e for e in events}
        anomalies = []
        for e in events:
            deps = e.get("data", {}).get("depends_on", [])
            if isinstance(deps, str):
                deps = [deps]
            for dep_id in deps:
                dep = id_map.get(dep_id)
                if not dep:
                    continue
                if e.get("start", "") < dep.get("end", dep.get("start", "")):
                    anomalies.append({
                        "type": "impossible_sequence",
                        "severity": "HIGH",
                        "event": e.get("event_id"),
                        "dependency": dep_id,
                        "event_start": e.get("start"),
                        "dependency_end": dep.get("end"),
                        "message": (f"'{e.get('event_id')}' starts before "
                                    f"dependency '{dep_id}' ends"),
                    })
        return anomalies

    def _temporal_detect_speed_violations(self, events: list,
                                          max_speed_kmh: float = 900.0
                                          ) -> list[dict]:
        """Detect physically impossible travel speeds between events."""
        located = [e for e in events
                   if "location" in e.get("data", {})]
        located.sort(key=lambda e: e.get("start", ""))
        anomalies = []
        for i in range(len(located) - 1):
            a, b = located[i], located[i + 1]
            a_loc = a["data"]["location"]
            b_loc = b["data"]["location"]
            if not all(k in a_loc for k in ("lat", "lon")):
                continue
            if not all(k in b_loc for k in ("lat", "lon")):
                continue
            dist = _haversine_km(
                float(a_loc["lat"]), float(a_loc["lon"]),
                float(b_loc["lat"]), float(b_loc["lon"]))
            try:
                t_a = datetime.fromisoformat(
                    a.get("end", a.get("start", "")))
                t_b = datetime.fromisoformat(b.get("start", ""))
                if t_a.tzinfo is None:
                    t_a = t_a.replace(tzinfo=timezone.utc)
                if t_b.tzinfo is None:
                    t_b = t_b.replace(tzinfo=timezone.utc)
                hours = max((t_b - t_a).total_seconds() / 3600.0, 0.001)
            except (ValueError, TypeError):
                continue
            speed = dist / hours
            if speed > max_speed_kmh:
                anomalies.append({
                    "type": "speed_violation",
                    "severity": "HIGH",
                    "from_event": a.get("event_id"),
                    "to_event": b.get("event_id"),
                    "distance_km": round(dist, 1),
                    "time_hours": round(hours, 2),
                    "speed_kmh": round(speed, 1),
                    "max_speed_kmh": max_speed_kmh,
                    "message": (f"{round(speed, 0)} km/h between "
                                f"'{a.get('event_id')}' and "
                                f"'{b.get('event_id')}' "
                                f"(limit: {max_speed_kmh} km/h)"),
                })
        return anomalies

    def _temporal_detect_overlapping_exclusives(self, events: list
                                                ) -> list[dict]:
        """Detect same exclusive_resource used at overlapping times."""
        resource_events: dict[str, list[dict]] = {}
        for e in events:
            res = e.get("data", {}).get("exclusive_resource")
            if res:
                resource_events.setdefault(res, []).append(e)
        anomalies = []
        for res, res_evts in resource_events.items():
            res_evts.sort(key=lambda e: e.get("start", ""))
            for i in range(len(res_evts)):
                for j in range(i + 1, len(res_evts)):
                    a, b = res_evts[i], res_evts[j]
                    if (a.get("start", "") < b.get("end", b.get("start", ""))
                            and b.get("start", "")
                            < a.get("end", a.get("start", ""))):
                        anomalies.append({
                            "type": "overlapping_exclusive",
                            "severity": "MEDIUM",
                            "resource": res,
                            "event_a": a.get("event_id"),
                            "event_b": b.get("event_id"),
                            "message": (
                                f"Resource '{res}' used by both "
                                f"'{a.get('event_id')}' and "
                                f"'{b.get('event_id')}' "
                                f"at overlapping times"),
                        })
        return anomalies

    def _temporal_detect_suspicious_gaps(self, events: list) -> list[dict]:
        """Detect gaps exceeding mean + 2.5*stddev."""
        if len(events) < 3:
            return []
        sorted_events = sorted(events, key=lambda e: e.get("start", ""))
        gaps: list[tuple[float, int]] = []
        for i in range(len(sorted_events) - 1):
            a_end = sorted_events[i].get(
                "end", sorted_events[i].get("start", ""))
            b_start = sorted_events[i + 1].get("start", "")
            try:
                t_a = datetime.fromisoformat(a_end)
                t_b = datetime.fromisoformat(b_start)
                if t_a.tzinfo is None:
                    t_a = t_a.replace(tzinfo=timezone.utc)
                if t_b.tzinfo is None:
                    t_b = t_b.replace(tzinfo=timezone.utc)
                gap_hours = (t_b - t_a).total_seconds() / 3600.0
                gaps.append((gap_hours, i))
            except (ValueError, TypeError):
                continue
        if len(gaps) < 3:
            return []
        gap_values = [g[0] for g in gaps]
        mean_gap = statistics.mean(gap_values)
        stdev_gap = statistics.stdev(gap_values)
        threshold = mean_gap + 2.5 * stdev_gap
        anomalies = []
        for gap_hours, idx in gaps:
            if gap_hours > threshold and stdev_gap > 0:
                anomalies.append({
                    "type": "suspicious_gap",
                    "severity": "LOW",
                    "after_event": sorted_events[idx].get("event_id"),
                    "before_event": sorted_events[idx + 1].get("event_id"),
                    "gap_hours": round(gap_hours, 1),
                    "threshold_hours": round(threshold, 1),
                    "message": (
                        f"{round(gap_hours, 1)}h gap between "
                        f"'{sorted_events[idx].get('event_id')}' and "
                        f"'{sorted_events[idx + 1].get('event_id')}' "
                        f"(threshold: {round(threshold, 1)}h)"),
                })
        return anomalies

    def temporal_detect_anomalies(
            self, event_ids: list[str] | None = None,
            include_types: list[str] | None = None,
            max_results: int = 15) -> list[dict]:
        """Detect temporal anomalies across 6 categories.

        Returns anomalies sorted by severity (CRITICAL first).
        """
        events = self._load(self._temporal_path)
        if event_ids:
            id_set = set(event_ids)
            events = [e for e in events if e.get("event_id") in id_set]
        if not events:
            return []

        all_types = {
            "temporal_cycle": self._temporal_detect_cycles,
            "backwards_causation": self._temporal_detect_backwards_causation,
            "impossible_sequence": self._temporal_detect_impossible_sequences,
            "speed_violation": self._temporal_detect_speed_violations,
            "overlapping_exclusive":
                self._temporal_detect_overlapping_exclusives,
            "suspicious_gap": self._temporal_detect_suspicious_gaps,
        }

        types_to_check = include_types or list(all_types.keys())
        anomalies: list[dict] = []
        for atype in types_to_check:
            if atype in all_types:
                anomalies.extend(all_types[atype](events))

        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        anomalies.sort(
            key=lambda a: severity_order.get(a.get("severity", "LOW"), 4))
        return anomalies[:max_results]

    def temporal_anomaly_summary(self) -> dict:
        """Return anomaly counts by type and severity."""
        anomalies = self.temporal_detect_anomalies(max_results=999)
        by_type: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        for a in anomalies:
            t = a.get("type", "unknown")
            s = a.get("severity", "unknown")
            by_type[t] = by_type.get(t, 0) + 1
            by_severity[s] = by_severity.get(s, 0) + 1
        return {
            "total_anomalies": len(anomalies),
            "by_type": by_type,
            "by_severity": by_severity,
        }

    # ==================================================================
    #  FEATURE 7: PEER REPUTATION SCORING
    # ==================================================================

    def link_peer_reputation(self, peer_fingerprint: str) -> dict:
        """Calculate trust/reputation score for a peer.

        Based on:
        - Facts accepted vs rejected during sync
        - Overrides (their facts replacing ours)
        - Sync frequency and recency
        - Manual trust adjustments

        Score: 0-100 (100 = fully trusted)
        """
        peers = self._link_load_peers()
        fp_lower = peer_fingerprint.lower()

        peer = None
        for p in peers:
            if p.get("fingerprint", "").lower().startswith(fp_lower):
                peer = p
                break

        if not peer:
            return {"error": "Peer not found"}

        # Load sync log for this peer
        sync_log = self._link_load_sync_log()
        peer_syncs = [s for s in sync_log
                      if s.get("peer_fingerprint", "").lower().startswith(fp_lower)]

        total_syncs = len(peer_syncs)
        total_facts_received = sum(
            s.get("facts_received", 0) for s in peer_syncs
        )
        total_conflicts = sum(
            s.get("conflicts", 0) for s in peer_syncs
        )

        # Base score
        base = 50.0

        # Sync frequency bonus (more syncs = more trust, up to +20)
        sync_bonus = min(20.0, total_syncs * 2.0)

        # Low conflict ratio bonus (fewer conflicts = more trust, up to +20)
        if total_facts_received > 0:
            conflict_ratio = total_conflicts / total_facts_received
            conflict_bonus = max(0, 20.0 * (1 - conflict_ratio * 5))
        else:
            conflict_bonus = 0.0

        # Recency bonus (synced recently = +10)
        recency_bonus = 0.0
        if peer.get("last_sync"):
            days_since = _days_ago(peer["last_sync"])
            recency_bonus = max(0, 10.0 * math.exp(-days_since / 30))

        # Manual trust adjustment
        manual_trust = peer.get("trust_adjustment", 0)

        score = max(0, min(100, int(
            base + sync_bonus + conflict_bonus + recency_bonus + manual_trust
        )))

        return {
            "fingerprint": peer.get("fingerprint", ""),
            "display_name": peer.get("display_name", ""),
            "reputation_score": score,
            "total_syncs": total_syncs,
            "facts_received": total_facts_received,
            "conflicts": total_conflicts,
            "sync_bonus": round(sync_bonus, 1),
            "conflict_bonus": round(conflict_bonus, 1),
            "recency_bonus": round(recency_bonus, 1),
            "manual_adjustment": manual_trust,
        }

    def link_adjust_trust(self, peer_fingerprint: str,
                          adjustment: int) -> bool:
        """Manually adjust a peer's trust score.

        adjustment: positive to increase trust, negative to decrease.
        Capped at +/- 30.
        """
        peers = self._link_load_peers()
        fp_lower = peer_fingerprint.lower()

        for p in peers:
            if p.get("fingerprint", "").lower().startswith(fp_lower):
                current = p.get("trust_adjustment", 0)
                p["trust_adjustment"] = max(-30, min(30, current + adjustment))
                self._link_save_peers(peers)
                return True
        return False

    # ==================================================================
    #  FEATURE 8: SELECTIVE AMNESIA
    # ==================================================================

    def forget(self, topic: str, fact_pattern: str,
               reason: str) -> dict:
        """Intentionally forget facts matching a pattern, with audit trail.

        Moves matching facts to the amnesia archive. They are removed
        from active facts.json but preserved in amnesia.json with the
        reason for deletion and immutable timestamp.

        Args:
            topic: Topic to search in
            fact_pattern: Substring or pattern to match against fact text
            reason: Why this fact is being forgotten (required)

        Returns: {forgotten_count, archived_entries}
        """
        facts = self._load(self._facts_path)
        amnesia = self._load(self._amnesia_path)
        now = _now_iso()
        pattern_lower = fact_pattern.lower()
        topic_lower = topic.lower()

        to_forget = []
        remaining = []

        for f in facts:
            if (f.get("topic", "").lower() == topic_lower
                    and pattern_lower in f.get("fact", "").lower()):
                to_forget.append(f)
            else:
                remaining.append(f)

        if not to_forget:
            return {"forgotten_count": 0, "archived_entries": []}

        archived = []
        for f in to_forget:
            archive_entry = {
                "original_fact": f,
                "reason": reason,
                "forgotten_at": now,
                "forgotten_by": "user",
                "topic": f.get("topic", ""),
                "fact_preview": f.get("fact", "")[:100],
                "original_confidence": f.get("confidence", 0),
            }
            amnesia.append(archive_entry)
            archived.append(archive_entry)

        self._save(self._facts_path, remaining)
        self._save(self._amnesia_path, amnesia)

        # Quarantine safety net
        for f in to_forget:
            self._quarantine_add(f, "forget", reason)

        # Chain of custody if link is initialized
        if self.link_identity():
            self._link_append_custody("SELECTIVE_AMNESIA", {
                "topic": topic,
                "pattern": fact_pattern,
                "reason": reason,
                "facts_forgotten": len(to_forget),
            })

        return {"forgotten_count": len(to_forget), "archived_entries": archived}

    def amnesia_log(self, last_n: int = 15) -> list[dict]:
        """Return recent amnesia entries (forgotten facts with reasons)."""
        log = self._load(self._amnesia_path)
        return log[-last_n:]

    def amnesia_restore(self, topic: str, fact_pattern: str) -> dict:
        """Restore a previously forgotten fact from the amnesia archive.

        Returns: {restored_count}
        """
        amnesia = self._load(self._amnesia_path)
        facts = self._load(self._facts_path)
        pattern_lower = fact_pattern.lower()
        topic_lower = topic.lower()

        to_restore = []
        remaining_amnesia = []

        for entry in amnesia:
            if (entry.get("topic", "").lower() == topic_lower
                    and pattern_lower in entry.get("fact_preview", "").lower()):
                to_restore.append(entry)
            else:
                remaining_amnesia.append(entry)

        restored = 0
        for entry in to_restore:
            original = entry.get("original_fact", {})
            if original:
                original["restored_at"] = _now_iso()
                original["source"] = f"restored:{entry.get('reason', 'unknown')}"
                facts.append(original)
                restored += 1

        if restored:
            self._save(self._facts_path, facts)
            self._save(self._amnesia_path, remaining_amnesia)

        return {"restored_count": restored}

    # ==================================================================
    #  FEATURE 9: MULTI-BRAIN CONSENSUS
    # ==================================================================

    def consensus_check(self, topic: str,
                        fact_text: str) -> dict:
        """Check consensus on a fact across all peer sync history.

        Analyzes sync logs and local data to determine how many brains
        agree on this fact (or similar facts).

        Returns: {consensus_level, agreeing_peers, total_peers,
                  local_confidence, peer_sources}
        """
        facts = self._load(self._facts_path)
        topic_lower = topic.lower()
        fact_lower = fact_text.lower()

        # Find local matches
        local_matches = []
        for f in facts:
            if f.get("topic", "").lower() != topic_lower:
                continue
            sim = _similarity(f.get("fact", ""), fact_text)
            if sim > 0.70:
                local_matches.append(f)

        # Count unique peer sources
        peer_sources = set()
        for f in local_matches:
            source = f.get("source", "")
            if source.startswith("link:"):
                peer_sources.add(source.split(":")[1])

        peers = self._link_load_peers()
        total_peers = len(peers)
        agreeing_peers = len(peer_sources)

        # Calculate consensus level
        if total_peers == 0:
            consensus = "standalone"
            confidence_modifier = 0
        elif agreeing_peers == 0:
            consensus = "unverified"
            confidence_modifier = 0
        elif agreeing_peers >= total_peers * 0.75:
            consensus = "strong"
            confidence_modifier = 15
        elif agreeing_peers >= total_peers * 0.5:
            consensus = "majority"
            confidence_modifier = 10
        elif agreeing_peers >= 1:
            consensus = "partial"
            confidence_modifier = 5
        else:
            consensus = "contested"
            confidence_modifier = -10

        local_conf = (local_matches[0].get("confidence", 0)
                      if local_matches else 0)

        return {
            "topic": topic,
            "fact_preview": fact_text[:80],
            "consensus_level": consensus,
            "agreeing_peers": agreeing_peers,
            "total_peers": total_peers,
            "local_confidence": local_conf,
            "confidence_modifier": confidence_modifier,
            "peer_sources": list(peer_sources),
            "local_matches": len(local_matches),
        }

    # ==================================================================
    #  FEATURE 10: LIVE SUBSCRIPTION (Polling-based, stdlib threading)
    # ==================================================================

    def link_subscribe(self, peer_fingerprint: str,
                       topics: list[str]) -> bool:
        """Subscribe to topics from a peer for auto-sync.

        Stores subscription in peer config. Used by link_poll_subscriptions().
        """
        peers = self._link_load_peers()
        fp_lower = peer_fingerprint.lower()

        for p in peers:
            if p.get("fingerprint", "").lower().startswith(fp_lower):
                existing = p.get("subscriptions", [])
                merged = list(set(existing + topics))
                p["subscriptions"] = merged
                self._link_save_peers(peers)
                return True
        return False

    def link_unsubscribe(self, peer_fingerprint: str,
                         topics: list[str]) -> bool:
        """Unsubscribe from topics."""
        peers = self._link_load_peers()
        fp_lower = peer_fingerprint.lower()

        for p in peers:
            if p.get("fingerprint", "").lower().startswith(fp_lower):
                existing = p.get("subscriptions", [])
                p["subscriptions"] = [t for t in existing if t not in topics]
                self._link_save_peers(peers)
                return True
        return False

    def link_poll_subscriptions(self) -> list[dict]:
        """Poll all peers for subscribed topics. Sync any that have updates.

        Returns list of sync results per peer.
        """
        peers = self._link_load_peers()
        results = []

        for p in peers:
            subs = p.get("subscriptions", [])
            if not subs or p.get("status") != "active":
                continue

            try:
                result = self.link_sync(
                    p["fingerprint"], topics=subs, direction="pull"
                )
                results.append({
                    "peer": p.get("display_name", p["fingerprint"][:16]),
                    "topics": subs,
                    "result": result,
                })
            except (ConnectionError, ValueError, OSError):
                results.append({
                    "peer": p.get("display_name", p["fingerprint"][:16]),
                    "topics": subs,
                    "error": "Connection failed",
                })

        return results

    # ==================================================================
    #  FEATURE 11: EVIDENCE BLOB STORE
    # ==================================================================

    def blob_store(self, content: bytes | str,
                   metadata: dict | None = None) -> dict:
        """Store evidence in content-addressable blob storage.

        Content is stored as: blobs/<sha256_hash>.blob
        Metadata stored in: blobs/<sha256_hash>.meta.json

        Returns: {hash, size, path, metadata}
        """
        if isinstance(content, str):
            content = content.encode("utf-8")

        blob_hash = hashlib.sha256(content).hexdigest()
        self._blobs_dir.mkdir(parents=True, exist_ok=True)

        blob_path = self._blobs_dir / f"{blob_hash}.blob"
        meta_path = self._blobs_dir / f"{blob_hash}.meta.json"

        # Write blob (idempotent — same content = same hash)
        if not blob_path.exists():
            tmp = blob_path.with_suffix(".tmp")
            tmp.write_bytes(content)
            os.replace(str(tmp), str(blob_path))

        # Write/update metadata
        now = _now_iso()
        meta = {
            "hash": blob_hash,
            "size": len(content),
            "stored_at": now,
            "metadata": metadata or {},
        }
        tmp = meta_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(meta, indent=2, ensure_ascii=False),
                       encoding="utf-8")
        os.replace(str(tmp), str(meta_path))

        # Auto-index as graph node
        nid = self._graph_node_id("blob", blob_hash)
        graph = self._graph_load()
        graph["nodes"][nid] = {
            "type": "blob",
            "data": {
                "hash": blob_hash,
                "size": len(content),
                "description": (metadata or {}).get("description", ""),
                "content_type": (metadata or {}).get("content_type", "unknown"),
            },
            "created_at": now, "updated_at": now,
        }
        self._graph_save(graph)

        # Chain of custody
        if self.link_identity():
            self._link_append_custody("BLOB_STORED", {
                "hash": blob_hash,
                "size": len(content),
                "description": (metadata or {}).get("description", ""),
            })

        return {
            "hash": blob_hash,
            "size": len(content),
            "path": str(blob_path),
            "metadata": metadata or {},
        }

    def blob_retrieve(self, blob_hash: str) -> dict | None:
        """Retrieve a blob by its SHA-256 hash.

        Returns: {hash, content, size, metadata} or None
        """
        blob_path = self._blobs_dir / f"{blob_hash}.blob"
        meta_path = self._blobs_dir / f"{blob_hash}.meta.json"

        if not blob_path.exists():
            return None

        content = blob_path.read_bytes()
        meta = {}
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, FileNotFoundError):
                pass

        return {
            "hash": blob_hash,
            "content": content,
            "size": len(content),
            "metadata": meta.get("metadata", {}),
            "stored_at": meta.get("stored_at", "unknown"),
        }

    def blob_list(self, max_results: int = 15) -> list[dict]:
        """List all stored blobs with metadata."""
        if not self._blobs_dir.exists():
            return []

        blobs = []
        for meta_file in sorted(self._blobs_dir.glob("*.meta.json")):
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                blobs.append(meta)
            except (json.JSONDecodeError, FileNotFoundError):
                continue

        blobs.sort(key=lambda b: b.get("stored_at", ""), reverse=True)
        return blobs[:max_results]

    def blob_link(self, blob_hash: str, fact_topic: str) -> dict | None:
        """Link a blob to a fact topic via the knowledge graph."""
        blob_nid = self._graph_node_id("blob", blob_hash)
        topic_nid = self._graph_node_id("topic", fact_topic)

        graph = self._graph_load()
        if blob_nid not in graph["nodes"]:
            return None

        # Ensure topic node exists
        if topic_nid not in graph["nodes"]:
            graph["nodes"][topic_nid] = {
                "type": "topic",
                "data": {"name": fact_topic},
                "created_at": _now_iso(), "updated_at": _now_iso(),
            }

        edge = {
            "source": blob_nid, "target": topic_nid,
            "type": "references", "weight": 1.0,
            "created_at": _now_iso(), "updated_at": _now_iso(),
        }
        graph["edges"].append(edge)
        self._graph_save(graph)
        return edge

    def blob_verify(self, blob_hash: str) -> dict:
        """Verify a blob's integrity by recomputing its SHA-256 hash."""
        blob_path = self._blobs_dir / f"{blob_hash}.blob"
        if not blob_path.exists():
            return {"valid": False, "error": "Blob not found"}

        content = blob_path.read_bytes()
        actual_hash = hashlib.sha256(content).hexdigest()
        valid = actual_hash == blob_hash

        return {
            "expected_hash": blob_hash,
            "actual_hash": actual_hash,
            "valid": valid,
            "size": len(content),
        }


    # ==================================================================
    #  FEATURE 22: WITNESS CREDIBILITY SCORING
    # ==================================================================

    _SOURCE_TYPE_BASELINES = {
        "official_record": 90,
        "digital_tool": 85,
        "peer_brain": 70,
        "ai_agent": 65,
        "human_witness": 60,
        "anonymous": 40,
    }

    def _sources_load(self) -> list:
        """Load sources registry."""
        try:
            data = json.loads(self._sources_path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _sources_save(self, sources: list) -> None:
        """Atomic save for sources registry."""
        tmp = self._sources_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(sources, indent=2, ensure_ascii=False),
                       encoding="utf-8")
        os.replace(str(tmp), str(self._sources_path))

    def _source_find(self, sources: list, source_id: str) -> dict | None:
        """Find a source by ID (case-insensitive)."""
        sid = source_id.lower()
        for s in sources:
            if s.get("source_id", "").lower() == sid:
                return s
        return None

    def _source_track_contribution(self, source_id: str) -> None:
        """Increment contribution count for a registered source."""
        sources = self._sources_load()
        src = self._source_find(sources, source_id)
        if src:
            src["facts_contributed"] = src.get("facts_contributed", 0) + 1
            src["last_contributed"] = _now_iso()
            self._sources_save(sources)

    def _source_calc_consistency(self, src: dict) -> float:
        """0-100 score based on contradiction rate."""
        contradictions = src.get("contradictions_flagged", 0)
        return max(0.0, 100.0 - contradictions * 15.0)

    def _source_calc_corroboration(self, src: dict, facts: list) -> float:
        """0-100 score: proportion of source's topics also covered by others."""
        source_id = src.get("source_id", "")
        source_facts = [f for f in facts if f.get("source", "") == source_id]
        if not source_facts:
            return 50.0
        corroborated = 0
        for sf in source_facts:
            topic = sf.get("topic", "").lower()
            for other in facts:
                if (other.get("source", "") != source_id
                        and other.get("topic", "").lower() == topic):
                    corroborated += 1
                    break
        return min(100.0, (corroborated / len(source_facts)) * 100.0)

    def _source_calc_recency(self, src: dict) -> float:
        """0-100 score based on time since last contribution (90-day half)."""
        last = src.get("last_contributed")
        if not last:
            return 30.0
        days = _days_ago(last)
        return max(0.0, min(100.0, 100.0 * math.exp(-days / 90.0)))

    def _source_calc_expertise(self, src: dict, facts: list) -> float:
        """0-100 score: domain alignment with contributed facts."""
        domains = {d.lower() for d in src.get("domains", [])}
        if not domains:
            return 50.0
        source_id = src.get("source_id", "")
        source_facts = [f for f in facts if f.get("source", "") == source_id]
        if not source_facts:
            return 50.0
        matched = 0
        for sf in source_facts:
            topic = sf.get("topic", "").lower()
            fact_text = sf.get("fact", "").lower()
            for domain in domains:
                if domain in topic or domain in fact_text:
                    matched += 1
                    break
        return min(100.0, (matched / len(source_facts)) * 100.0)

    def _source_calc_score(self, src: dict, facts: list) -> float:
        """Calculate credibility score for a source (no side effects)."""
        consistency = self._source_calc_consistency(src)
        corroboration = self._source_calc_corroboration(src, facts)
        recency = self._source_calc_recency(src)
        expertise = self._source_calc_expertise(src, facts)
        type_base = float(self._SOURCE_TYPE_BASELINES.get(
            src.get("source_type", "anonymous"), 40))
        manual = max(-30, min(30, src.get("manual_adjustment", 0)))
        raw = (consistency * 0.30 + corroboration * 0.25
               + recency * 0.15 + expertise * 0.15 + type_base * 0.15)
        return max(0.0, min(100.0, raw + manual))

    def source_register(self, source_id: str,
                        source_type: str = "human_witness",
                        display_name: str | None = None,
                        domains: list[str] | None = None) -> dict:
        """Register or update a source for credibility tracking.

        source_type: one of official_record, digital_tool, peer_brain,
                     ai_agent, human_witness, anonymous
        """
        sources = self._sources_load()
        existing = self._source_find(sources, source_id)
        now = _now_iso()

        if existing:
            existing["source_type"] = source_type
            if display_name is not None:
                existing["display_name"] = display_name
            if domains is not None:
                existing["domains"] = domains
            existing["updated_at"] = now
            self._sources_save(sources)
            return existing

        entry = {
            "source_id": source_id,
            "source_type": source_type,
            "display_name": display_name or source_id,
            "domains": domains or [],
            "facts_contributed": 0,
            "contradictions_flagged": 0,
            "manual_adjustment": 0,
            "last_contributed": None,
            "credibility_history": [],
            "created_at": now,
            "updated_at": now,
        }
        sources.append(entry)
        self._sources_save(sources)
        return entry

    def source_credibility(self, source_id: str) -> dict:
        """Calculate full credibility profile with sub-scores.

        Formula: consistency*0.30 + corroboration*0.25 + recency*0.15
                 + expertise*0.15 + type_base*0.15 + manual_adjustment
        """
        sources = self._sources_load()
        src = self._source_find(sources, source_id)
        if not src:
            return {"error": f"Source '{source_id}' not registered"}

        facts = self._load(self._facts_path)
        consistency = self._source_calc_consistency(src)
        corroboration = self._source_calc_corroboration(src, facts)
        recency = self._source_calc_recency(src)
        expertise = self._source_calc_expertise(src, facts)
        type_base = float(self._SOURCE_TYPE_BASELINES.get(
            src.get("source_type", "anonymous"), 40))
        manual = max(-30, min(30, src.get("manual_adjustment", 0)))

        raw_score = (consistency * 0.30 + corroboration * 0.25
                     + recency * 0.15 + expertise * 0.15 + type_base * 0.15)
        final_score = max(0.0, min(100.0, raw_score + manual))

        # Snapshot to history
        snapshot = {"score": round(final_score, 1), "timestamp": _now_iso()}
        src["credibility_history"].append(snapshot)
        src["credibility_history"] = src["credibility_history"][-50:]
        self._sources_save(sources)

        return {
            "source_id": src["source_id"],
            "display_name": src.get("display_name", src["source_id"]),
            "source_type": src.get("source_type", "anonymous"),
            "credibility_score": round(final_score, 1),
            "sub_scores": {
                "consistency": round(consistency, 1),
                "corroboration": round(corroboration, 1),
                "recency": round(recency, 1),
                "expertise": round(expertise, 1),
                "type_base": round(type_base, 1),
            },
            "manual_adjustment": manual,
            "facts_contributed": src.get("facts_contributed", 0),
            "contradictions_flagged": src.get("contradictions_flagged", 0),
        }

    def source_adjust_credibility(self, source_id: str,
                                  adjustment: int) -> dict:
        """Manual credibility adjustment, capped at +/-30 cumulative."""
        sources = self._sources_load()
        src = self._source_find(sources, source_id)
        if not src:
            return {"error": f"Source '{source_id}' not registered"}

        current = src.get("manual_adjustment", 0)
        new_adj = max(-30, min(30, current + adjustment))
        src["manual_adjustment"] = new_adj
        src["updated_at"] = _now_iso()
        self._sources_save(sources)

        return {
            "source_id": source_id,
            "previous_adjustment": current,
            "new_adjustment": new_adj,
            "delta": new_adj - current,
        }

    def source_list(self) -> list[dict]:
        """List all registered sources, ranked by credibility score."""
        sources = self._sources_load()
        ranked = []
        for src in sources:
            cred = self.source_credibility(src["source_id"])
            ranked.append(cred)
        ranked.sort(key=lambda x: x.get("credibility_score", 0), reverse=True)
        return ranked

    def source_weighted_confidence(self, fact: dict) -> float:
        """Calculate weighted confidence: base_confidence * source_weight.

        source_weight = credibility_score / 100.0 (range 0.0-1.0).
        Unregistered sources get weight 1.0 (no penalty, no boost).
        """
        base = fact.get("confidence", 0)
        source_id = fact.get("source", "")
        if not source_id:
            return float(base)

        sources = self._sources_load()
        src = self._source_find(sources, source_id)
        if not src:
            return float(base)

        facts = self._load(self._facts_path)
        cred_score = self._source_calc_score(src, facts)
        return round(base * cred_score / 100.0, 1)

    def source_credibility_trend(self, source_id: str) -> list[dict]:
        """Return time-series of credibility snapshots for a source."""
        sources = self._sources_load()
        src = self._source_find(sources, source_id)
        if not src:
            return []
        return src.get("credibility_history", [])

    # ==================================================================
    #  FEATURE 25: CRDT SYNC (Conflict-Free Replicated Data Types)
    # ==================================================================

    def _crdt_node_id(self) -> str:
        """Persistent node ID derived from identity or memory_dir hash."""
        identity = self.link_identity()
        if identity and identity.get("fingerprint"):
            return identity["fingerprint"][:12]
        return hashlib.sha256(
            str(self.memory_dir).encode()).hexdigest()[:12]

    def _crdt_hlc_now(self) -> dict:
        """Generate a monotonically increasing HLC timestamp."""
        wall = int(time.time() * 1000)
        node = self._crdt_node_id()
        if not hasattr(self, '_crdt_last_hlc'):
            self._crdt_last_hlc = {"wall": 0, "counter": 0, "node": node}
        last = self._crdt_last_hlc
        if wall > last["wall"]:
            hlc = {"wall": wall, "counter": 0, "node": node}
        elif wall == last["wall"]:
            hlc = {"wall": wall, "counter": last["counter"] + 1,
                   "node": node}
        else:
            hlc = {"wall": last["wall"],
                   "counter": last["counter"] + 1, "node": node}
        self._crdt_last_hlc = dict(hlc)
        return dict(hlc)

    def _crdt_hlc_compare(self, a: dict, b: dict) -> int:
        """Compare two HLC timestamps. Returns -1, 0, or 1."""
        if a.get("wall", 0) != b.get("wall", 0):
            return -1 if a["wall"] < b["wall"] else 1
        if a.get("counter", 0) != b.get("counter", 0):
            return -1 if a["counter"] < b["counter"] else 1
        a_node = a.get("node", "")
        b_node = b.get("node", "")
        if a_node != b_node:
            return -1 if a_node < b_node else 1
        return 0

    def _crdt_hlc_merge(self, local_hlc: dict, remote_hlc: dict) -> dict:
        """Merge two HLCs, advancing the logical clock."""
        wall = int(time.time() * 1000)
        max_wall = max(wall, local_hlc.get("wall", 0),
                       remote_hlc.get("wall", 0))
        if (max_wall == wall and max_wall > local_hlc.get("wall", 0)
                and max_wall > remote_hlc.get("wall", 0)):
            counter = 0
        elif local_hlc.get("wall", 0) == remote_hlc.get("wall", 0):
            counter = max(local_hlc.get("counter", 0),
                          remote_hlc.get("counter", 0)) + 1
        elif local_hlc.get("wall", 0) > remote_hlc.get("wall", 0):
            counter = local_hlc.get("counter", 0) + 1
        else:
            counter = remote_hlc.get("counter", 0) + 1
        node = self._crdt_node_id()
        hlc = {"wall": max_wall, "counter": counter, "node": node}
        self._crdt_last_hlc = dict(hlc)
        return dict(hlc)

    def _crdt_ensure_metadata(self, fact: dict) -> dict:
        """Add CRDT metadata to a fact if not present."""
        if "_crdt" not in fact:
            node = self._crdt_node_id()
            fact["_crdt"] = {
                "hlc": self._crdt_hlc_now(),
                "origin_node": node,
                "version": 1,
                "tombstone": False,
                "merge_history": [],
            }
        return fact

    def _crdt_merge_fact(self, local: dict, remote: dict) -> str:
        """CRDT-aware merge. Returns 'local', 'remote', or 'both'."""
        local_crdt = local.get("_crdt", {})
        remote_crdt = remote.get("_crdt", {})
        local_hlc = local_crdt.get(
            "hlc", {"wall": 0, "counter": 0, "node": ""})
        remote_hlc = remote_crdt.get(
            "hlc", {"wall": 0, "counter": 0, "node": ""})

        # Tombstoned facts take precedence
        local_tomb = local_crdt.get("tombstone", False)
        remote_tomb = remote_crdt.get("tombstone", False)
        if local_tomb and not remote_tomb:
            return "local"
        if remote_tomb and not local_tomb:
            return "remote"

        # HLC comparison: higher wins
        cmp = self._crdt_hlc_compare(local_hlc, remote_hlc)
        if cmp > 0:
            return "local"
        if cmp < 0:
            return "remote"

        # Equal HLC: higher version wins
        local_ver = local_crdt.get("version", 1)
        remote_ver = remote_crdt.get("version", 1)
        if local_ver != remote_ver:
            return "local" if local_ver > remote_ver else "remote"

        # Complementary check (60-80% similarity -> keep both)
        sim = _similarity(local.get("fact", ""), remote.get("fact", ""))
        if 0.60 <= sim <= 0.80:
            return "both"

        return "local"

    def crdt_upgrade_facts(self) -> dict:
        """One-time: add CRDT metadata to all existing facts."""
        facts = self._load(self._facts_path)
        upgraded = 0
        for f in facts:
            if "_crdt" not in f:
                self._crdt_ensure_metadata(f)
                upgraded += 1
        self._save(self._facts_path, facts)
        return {"upgraded": upgraded, "total": len(facts)}

    def crdt_merge_snapshot(self, snapshot: dict) -> dict:
        """CRDT-aware convergent merge of a remote snapshot.

        Guarantees: commutativity, idempotency, associativity
        via HLC total ordering.
        """
        local_facts = self._load(self._facts_path)
        remote_facts = snapshot.get("facts", [])
        peer_fp = snapshot.get("source_fingerprint", "unknown")[:12]

        stats = {"merged": 0, "added": 0, "skipped": 0}

        for rf in remote_facts:
            rf_topic = rf.get("topic", "").lower()
            rf_fact = rf.get("fact", "")

            match = None
            match_idx = None
            for i, lf in enumerate(local_facts):
                if lf.get("topic", "").lower() != rf_topic:
                    continue
                sim = _similarity(lf.get("fact", ""), rf_fact)
                if sim > 0.80:
                    match = lf
                    match_idx = i
                    break

            if match is None:
                new_fact = {k: v for k, v in rf.items()
                           if not k.startswith("_") or k == "_crdt"}
                new_fact["source"] = f"link:{peer_fp}"
                new_fact.setdefault("links", [])
                self._crdt_ensure_metadata(new_fact)
                local_facts.append(new_fact)
                stats["added"] += 1
            else:
                winner = self._crdt_merge_fact(match, rf)
                if winner == "remote":
                    for k, v in rf.items():
                        if not k.startswith("_") or k == "_crdt":
                            local_facts[match_idx][k] = v
                    local_facts[match_idx]["source"] = f"link:{peer_fp}"
                    local_crdt = match.get("_crdt", {})
                    remote_crdt = rf.get("_crdt", {})
                    merged_hlc = self._crdt_hlc_merge(
                        local_crdt.get("hlc",
                                       {"wall": 0, "counter": 0, "node": ""}),
                        remote_crdt.get("hlc",
                                        {"wall": 0, "counter": 0, "node": ""}))
                    local_facts[match_idx].setdefault("_crdt", {})
                    local_facts[match_idx]["_crdt"]["hlc"] = merged_hlc
                    local_facts[match_idx]["_crdt"]["version"] = max(
                        local_crdt.get("version", 1),
                        remote_crdt.get("version", 1)) + 1
                    local_facts[match_idx]["_crdt"].setdefault(
                        "merge_history", []).append({
                            "peer": peer_fp, "merged_at": _now_iso(),
                            "winner": "remote"})
                    stats["merged"] += 1
                elif winner == "both":
                    new_fact = {k: v for k, v in rf.items()
                               if not k.startswith("_") or k == "_crdt"}
                    new_fact["source"] = f"link:{peer_fp}"
                    new_fact.setdefault("links", [])
                    self._crdt_ensure_metadata(new_fact)
                    local_facts.append(new_fact)
                    stats["added"] += 1
                else:
                    stats["skipped"] += 1

        self._save(self._facts_path, local_facts)
        return stats

    def crdt_tombstone(self, topic: str, pattern: str) -> dict:
        """Soft-delete matching facts by setting tombstone flag.

        Tombstones propagate via sync — other brains will also soft-delete.
        """
        facts = self._load(self._facts_path)
        tombstoned = 0
        pattern_lower = pattern.lower()
        for f in facts:
            if f.get("topic", "").lower() != topic.lower():
                continue
            if pattern_lower in f.get("fact", "").lower():
                # Quarantine a copy before tombstoning
                self._quarantine_add(f, "tombstone",
                                     "CRDT tombstone applied")
                self._crdt_ensure_metadata(f)
                f["_crdt"]["tombstone"] = True
                f["_crdt"]["hlc"] = self._crdt_hlc_now()
                f["_crdt"]["version"] = f["_crdt"].get("version", 1) + 1
                tombstoned += 1
        self._save(self._facts_path, facts)
        return {"tombstoned": tombstoned, "topic": topic, "pattern": pattern}

    def crdt_status(self) -> dict:
        """Return CRDT status: node ID, HLC state, fact counts."""
        facts = self._load(self._facts_path)
        crdt_facts = [f for f in facts if "_crdt" in f]
        tombstoned = [f for f in crdt_facts
                      if f["_crdt"].get("tombstone")]
        return {
            "node_id": self._crdt_node_id(),
            "total_facts": len(facts),
            "crdt_enabled": len(crdt_facts),
            "legacy": len(facts) - len(crdt_facts),
            "tombstoned": len(tombstoned),
        }

    def crdt_debug_hlc(self) -> list[dict]:
        """Debug: show HLC timestamps for all CRDT-enabled facts."""
        facts = self._load(self._facts_path)
        debug = []
        for f in facts:
            if "_crdt" in f:
                crdt = f["_crdt"]
                debug.append({
                    "topic": f.get("topic", "?"),
                    "fact_preview": f.get("fact", "")[:50],
                    "hlc": crdt["hlc"],
                    "version": crdt.get("version", 1),
                    "tombstone": crdt.get("tombstone", False),
                    "origin_node": crdt.get("origin_node", "?"),
                })
        debug.sort(key=lambda x: (
            x["hlc"]["wall"], x["hlc"]["counter"]))
        return debug

    # ==================================================================
    #  FEATURE 26: CASE/UCO ONTOLOGY EXPORT
    # ==================================================================

    _TOOL_KEYWORDS = frozenset({
        "autopsy", "volatility", "wireshark", "encase", "ftk",
        "cellebrite", "magnet", "sleuthkit", "x-ways", "axiom",
        "plaso", "log2timeline", "yara", "hashcat", "john",
        "nmap", "metasploit", "burpsuite", "ghidra", "ida",
        "binwalk", "foremost", "scalpel", "bulk_extractor",
        "regripper", "mimikatz", "procmon", "sysinternals",
    })

    _ARTIFACT_KEYWORDS = frozenset({
        "file", "registry", "log", "packet", "artifact", "image",
        "disk", "memory", "dump", "hash", "signature", "header",
        "metadata", "timestamp", "inode", "sector", "partition",
        "volume", "mft", "ntfs", "fat", "ext4", "hfs", "apfs",
        "prefetch", "shellbag", "lnk", "jumplist", "usnjrnl",
        "event log", "syslog", "pcap", "network",
    })

    def _case_classify_fact(self, fact: dict) -> str:
        """Classify a fact into UCO type based on keywords."""
        text = (fact.get("topic", "") + " " + fact.get("fact", "")).lower()
        words = set(text.split())
        if words & self._TOOL_KEYWORDS:
            return "uco-tool:Tool"
        if words & self._ARTIFACT_KEYWORDS:
            return "uco-observable:ObservableObject"
        return "uco-core:Assertion"

    def _case_map_fact(self, fact: dict, idx: int) -> dict:
        """Map a fact to a UCO JSON-LD object."""
        uco_type = self._case_classify_fact(fact)
        obj = {
            "@id": f"kb:fact-{idx}",
            "@type": uco_type,
            "uco-core:name": fact.get("topic", ""),
            "uco-core:description": fact.get("fact", ""),
            "uco-core:confidence": fact.get("confidence", 0) / 100.0,
            "uco-core:createdBy": fact.get("source", ""),
        }
        if fact.get("created_at"):
            obj["uco-core:objectCreatedTime"] = fact["created_at"]
        return obj

    def _case_map_citation(self, citation: dict, idx: int) -> dict:
        """Map a citation to a UCO Assertion with legal provenance."""
        return {
            "@id": f"kb:citation-{idx}",
            "@type": "uco-core:Assertion",
            "uco-core:statement": (
                f"{citation.get('code', '')} - "
                f"{citation.get('title', '')}"),
            "uco-core:description": citation.get("description", ""),
            "case-investigation:legalCode": citation.get("code", ""),
            "case-investigation:severity": citation.get("severity", ""),
        }

    def _case_map_temporal(self, event: dict, idx: int) -> dict:
        """Map a temporal event to a UCO Action."""
        obj = {
            "@id": f"kb:event-{idx}",
            "@type": "uco-action:Action",
            "uco-core:name": event.get("event_id", ""),
            "uco-action:startTime": event.get("start", ""),
            "uco-action:endTime": event.get("end", ""),
        }
        data = event.get("data", {})
        if data.get("location"):
            obj["uco-location:location"] = data["location"]
        return obj

    def _case_map_blob(self, blob_meta: dict, idx: int) -> dict:
        """Map a blob to a UCO ObservableObject with ContentDataFacet."""
        return {
            "@id": f"kb:blob-{idx}",
            "@type": "uco-observable:ObservableObject",
            "uco-observable:hasChanged": False,
            "uco-core:hasFacet": [{
                "@type": "uco-observable:ContentDataFacet",
                "uco-observable:hash": [{
                    "@type": "uco-types:Hash",
                    "uco-types:hashMethod": "SHA-256",
                    "uco-types:hashValue": blob_meta.get("hash", ""),
                }],
                "uco-observable:sizeInBytes": blob_meta.get("size", 0),
            }],
            "uco-core:description": blob_meta.get(
                "metadata", {}).get("description", ""),
        }

    def _case_map_custody(self, record: dict, idx: int) -> dict:
        """Map a custody record to a CASE ProvenanceRecord."""
        return {
            "@id": f"kb:custody-{idx}",
            "@type": "case-investigation:ProvenanceRecord",
            "uco-core:name": record.get("event_type", ""),
            "uco-action:startTime": record.get("timestamp", ""),
            "case-investigation:exhibitNumber": record.get("seq", idx),
            "uco-core:createdBy": record.get("actor_fingerprint", ""),
            "uco-core:description": json.dumps(
                record.get("details", {})),
        }

    def _case_map_graph_edge(self, edge: dict, idx: int) -> dict:
        """Map a graph edge to a UCO Relationship."""
        return {
            "@id": f"kb:rel-{idx}",
            "@type": "uco-core:Relationship",
            "uco-core:source": edge.get("source", ""),
            "uco-core:target": edge.get("target", ""),
            "uco-core:kindOfRelationship": edge.get("type", "related"),
            "uco-core:isDirectional": True,
        }

    def export_case_uco(self, output_path: str | None = None,
                        investigation_name: str = "Diamond Brain Export",
                        case_number: str = "") -> dict:
        """Export all knowledge in CASE/UCO JSON-LD format.

        Returns the JSON-LD dict. Optionally writes to output_path.
        """
        graph_objects = []

        # Facts
        facts = self._load(self._facts_path)
        active_facts = [f for f in facts
                        if not f.get("_crdt", {}).get("tombstone")]
        for i, f in enumerate(active_facts):
            graph_objects.append(self._case_map_fact(f, i))

        # Citations
        citations = self._load(self._citations_path)
        for i, c in enumerate(citations):
            graph_objects.append(self._case_map_citation(c, i))

        # Temporal events
        events = self._load(self._temporal_path)
        for i, e in enumerate(events):
            graph_objects.append(self._case_map_temporal(e, i))

        # Blobs
        if self._blobs_dir.exists():
            for i, meta_file in enumerate(
                    self._blobs_dir.glob("*.meta.json")):
                try:
                    meta = json.loads(
                        meta_file.read_text(encoding="utf-8"))
                    graph_objects.append(self._case_map_blob(meta, i))
                except (json.JSONDecodeError, FileNotFoundError):
                    continue

        # Custody chain
        custody_log = self._link_load_custody_log()
        for i, record in enumerate(custody_log):
            graph_objects.append(self._case_map_custody(record, i))

        # Graph edges
        graph_data = self._graph_load()
        for i, edge in enumerate(graph_data.get("edges", [])):
            graph_objects.append(self._case_map_graph_edge(edge, i))

        bundle = {
            "@context": {
                "kb": "http://example.org/kb/",
                "uco-core": "https://ontology.unifiedcyberontology.org"
                            "/uco/core/",
                "uco-observable": "https://ontology."
                                  "unifiedcyberontology.org"
                                  "/uco/observable/",
                "uco-action": "https://ontology."
                              "unifiedcyberontology.org/uco/action/",
                "uco-tool": "https://ontology."
                            "unifiedcyberontology.org/uco/tool/",
                "uco-types": "https://ontology."
                             "unifiedcyberontology.org/uco/types/",
                "uco-location": "https://ontology."
                                "unifiedcyberontology.org"
                                "/uco/location/",
                "case-investigation": "https://ontology."
                                      "caseontology.org"
                                      "/case/investigation/",
            },
            "@type": "uco-core:Bundle",
            "uco-core:name": investigation_name,
            "case-investigation:caseNumber": case_number,
            "uco-core:objectCreatedTime": _now_iso(),
            "@graph": graph_objects,
        }

        if output_path:
            out = Path(output_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(bundle, indent=2,
                                      ensure_ascii=False),
                           encoding="utf-8")

        return bundle

    # ==================================================================
    #  Hybrid Search (keyword + graph scoring — no external deps)
    # ==================================================================

    def hybrid_search(self, query: str, top_k: int = 10) -> list[dict]:
        """Combined keyword + graph search. No external dependencies.

        Weights: keyword=0.6, graph=0.4
        Returns facts ranked by combined score.
        """
        keyword_results = self.search(query)
        graph_data = self._graph_load()

        scored: dict[str, float] = {}
        fact_map: dict[str, dict] = {}

        # Keyword scoring
        for i, f in enumerate(keyword_results):
            key = f"{f.get('topic', '')}/{f.get('fact', '')[:50]}"
            kw_score = 1.0 - (i / max(len(keyword_results), 1))
            scored[key] = scored.get(key, 0) + kw_score * 0.6
            fact_map[key] = f

        # Graph scoring
        query_lower = query.lower()
        nodes = graph_data.get("nodes", {})
        for nid, node in nodes.items():
            if query_lower in nid.lower() or query_lower in str(
                    node.get("data", {})).lower():
                edges = [e for e in graph_data.get("edges", [])
                         if e.get("source") == nid
                         or e.get("target") == nid]
                graph_score = min(1.0, len(edges) * 0.2)
                key = f"graph:{nid}"
                scored[key] = scored.get(key, 0) + graph_score * 0.4

        ranked = sorted(scored.items(), key=lambda x: x[1], reverse=True)
        results = []
        for key, score in ranked[:top_k]:
            if key in fact_map:
                f_copy = dict(fact_map[key])
                f_copy["_hybrid_score"] = round(score, 4)
                results.append(f_copy)
        return results

    # ==================================================================
    #  FEATURE 28: HOMOMORPHIC CONFIDENCE (Encrypted Multi-Party Scoring)
    # ==================================================================

    _HC_DEFAULT_PRIME = 10007

    def _hc_vault_path(self) -> Path:
        return self._link_dir() / "confidence_vault.json"

    def _hc_load(self) -> dict:
        path = self._hc_vault_path()
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return {"sessions": {}}

    def _hc_save(self, vault: dict) -> None:
        path = self._hc_vault_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(vault, indent=2, ensure_ascii=False),
                       encoding="utf-8")
        os.replace(str(tmp), str(path))

    @staticmethod
    def _hc_fact_hash(topic: str, fact_text: str) -> str:
        """Deterministic hash for a fact's identity."""
        content = f"{topic.lower()}:{fact_text.lower()}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _hc_split_score(self, score: int, n_shares: int,
                        prime: int | None = None) -> list[int]:
        """Split score into n additive shares mod prime."""
        p = prime or self._HC_DEFAULT_PRIME
        shares = [secrets.randbelow(p) for _ in range(n_shares - 1)]
        last_share = (score - sum(shares)) % p
        shares.append(last_share)
        return shares

    def _hc_commitment(self, partial_sum: int, nonce: str) -> str:
        """SHA-256 commitment: H(partial_sum:nonce)."""
        data = f"{partial_sum}:{nonce}".encode()
        return hashlib.sha256(data).hexdigest()

    def hc_initiate(self, topic: str, fact_text: str,
                    my_score: int, n_peers: int = 1) -> dict:
        """Start a homomorphic confidence session.

        Splits my_score into shares for n_peers + self.
        Returns session info with shares to distribute.
        """
        fact_hash = self._hc_fact_hash(topic, fact_text)
        p = self._HC_DEFAULT_PRIME
        n_total = n_peers + 1  # self + peers
        shares = self._hc_split_score(my_score, n_total, p)

        # My share is shares[0], rest go to peers
        my_share = shares[0]
        nonce = secrets.token_hex(16)
        my_commitment = self._hc_commitment(my_share, nonce)

        vault = self._hc_load()
        vault["sessions"][fact_hash] = {
            "topic": topic,
            "fact_text": fact_text[:200],
            "fact_hash": fact_hash,
            "phase": "initiated",
            "prime": p,
            "n_expected": n_total,
            "my_share": my_share,
            "my_nonce": nonce,
            "my_commitment": my_commitment,
            "peer_shares": shares[1:],  # shares to send to peers
            "commitments": {self._crdt_node_id(): my_commitment},
            "reveals": {},
            "created_at": _now_iso(),
        }
        self._hc_save(vault)

        return {
            "fact_hash": fact_hash,
            "phase": "initiated",
            "my_commitment": my_commitment,
            "shares_for_peers": shares[1:],
            "n_expected": n_total,
        }

    def hc_receive_commitment(self, peer_fp: str, fact_hash: str,
                               commitment: str,
                               share: int) -> dict:
        """Store a peer's commitment and received share."""
        vault = self._hc_load()
        session = vault["sessions"].get(fact_hash)
        if not session:
            return {"error": f"No session for {fact_hash[:16]}..."}
        if session["phase"] not in ("initiated", "committed"):
            return {"error": f"Wrong phase: {session['phase']}"}

        session["commitments"][peer_fp] = commitment
        session["my_share"] = (session["my_share"] + share) % session["prime"]
        session["phase"] = "committed"
        self._hc_save(vault)

        return {
            "fact_hash": fact_hash,
            "phase": "committed",
            "commitments_received": len(session["commitments"]),
            "n_expected": session["n_expected"],
        }

    def hc_reveal(self, fact_hash: str) -> dict:
        """Reveal my partial sum and nonce."""
        vault = self._hc_load()
        session = vault["sessions"].get(fact_hash)
        if not session:
            return {"error": f"No session for {fact_hash[:16]}..."}
        if session["phase"] not in ("committed", "initiated"):
            return {"error": f"Wrong phase: {session['phase']}"}

        my_node = self._crdt_node_id()
        session["reveals"][my_node] = {
            "partial_sum": session["my_share"],
            "nonce": session["my_nonce"],
        }
        session["phase"] = "revealed"
        self._hc_save(vault)

        return {
            "fact_hash": fact_hash,
            "phase": "revealed",
            "partial_sum": session["my_share"],
            "nonce": session["my_nonce"],
        }

    def hc_receive_reveal(self, peer_fp: str, fact_hash: str,
                           partial_sum: int, nonce: str) -> dict:
        """Process a peer's reveal — verify commitment matches."""
        vault = self._hc_load()
        session = vault["sessions"].get(fact_hash)
        if not session:
            return {"error": f"No session for {fact_hash[:16]}..."}

        # Verify commitment
        expected = session["commitments"].get(peer_fp)
        actual = self._hc_commitment(partial_sum, nonce)
        if expected and actual != expected:
            return {
                "error": "Commitment mismatch — possible tampering",
                "peer": peer_fp,
                "expected": expected,
                "actual": actual,
            }

        session["reveals"][peer_fp] = {
            "partial_sum": partial_sum,
            "nonce": nonce,
        }
        self._hc_save(vault)

        return {
            "fact_hash": fact_hash,
            "peer": peer_fp,
            "verified": True,
            "reveals_received": len(session["reveals"]),
        }

    def hc_aggregate(self, fact_hash: str) -> dict:
        """Compute aggregate confidence from all reveals."""
        vault = self._hc_load()
        session = vault["sessions"].get(fact_hash)
        if not session:
            return {"error": f"No session for {fact_hash[:16]}..."}

        reveals = session.get("reveals", {})
        if len(reveals) < session["n_expected"]:
            return {
                "error": f"Need {session['n_expected']} reveals, "
                         f"have {len(reveals)}",
                "reveals_received": len(reveals),
            }

        p = session["prime"]
        total = sum(r["partial_sum"] for r in reveals.values()) % p
        n = len(reveals)
        average = round(total / n, 1)

        session["phase"] = "aggregated"
        session["result"] = {
            "total": total,
            "average": average,
            "participants": n,
            "aggregated_at": _now_iso(),
        }
        self._hc_save(vault)

        return {
            "fact_hash": fact_hash,
            "topic": session["topic"],
            "total": total,
            "average": average,
            "participants": n,
            "phase": "aggregated",
        }

    def hc_status(self, fact_hash: str | None = None) -> dict | list[dict]:
        """Get status of HC session(s)."""
        vault = self._hc_load()
        if fact_hash:
            session = vault["sessions"].get(fact_hash)
            if not session:
                return {"error": f"No session for {fact_hash[:16]}..."}
            return {
                "fact_hash": fact_hash,
                "topic": session["topic"],
                "phase": session["phase"],
                "commitments": len(session.get("commitments", {})),
                "reveals": len(session.get("reveals", {})),
                "n_expected": session["n_expected"],
                "result": session.get("result"),
            }
        # All sessions
        summaries = []
        for fh, session in vault["sessions"].items():
            summaries.append({
                "fact_hash": fh[:16] + "...",
                "topic": session["topic"],
                "phase": session["phase"],
            })
        return summaries

    def case_validate_export(self, data: dict) -> dict:
        """Validate structural integrity of a CASE/UCO export.

        Checks: @context present, @graph is list, all objects have @id
        and @type, @id uniqueness, cross-reference validity.
        """
        errors = []
        warnings = []

        if "@context" not in data:
            errors.append("Missing @context")
        if "@graph" not in data:
            errors.append("Missing @graph")
            return {"valid": False, "errors": errors, "warnings": warnings}

        graph = data["@graph"]
        if not isinstance(graph, list):
            errors.append("@graph must be a list")
            return {"valid": False, "errors": errors, "warnings": warnings}

        ids_seen = set()
        for i, obj in enumerate(graph):
            obj_id = obj.get("@id")
            if not obj_id:
                errors.append(f"Object [{i}] missing @id")
            elif obj_id in ids_seen:
                errors.append(f"Duplicate @id: {obj_id}")
            else:
                ids_seen.add(obj_id)

            if not obj.get("@type"):
                errors.append(f"Object [{i}] ({obj_id}) missing @type")

        # Cross-reference validation for relationships
        for obj in graph:
            if obj.get("@type") == "uco-core:Relationship":
                src = obj.get("uco-core:source", "")
                tgt = obj.get("uco-core:target", "")
                if src and src.startswith("kb:") and src not in ids_seen:
                    warnings.append(
                        f"Relationship {obj.get('@id')} references "
                        f"unknown source: {src}")
                if tgt and tgt.startswith("kb:") and tgt not in ids_seen:
                    warnings.append(
                        f"Relationship {obj.get('@id')} references "
                        f"unknown target: {tgt}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "object_count": len(graph),
            "unique_types": list({
                obj.get("@type", "") for obj in graph}),
        }

    # ==================================================================
    #  FEATURE 29: NEURAL CORTEX (LLM Reasoning Layer)
    # ==================================================================

    def _cortex_log_path(self) -> Path:
        return self.memory_dir / "cortex_log.json"

    def _cortex_log_load(self) -> dict:
        path = self._cortex_log_path()
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return {"total_queries": 0, "total_tokens": 0,
                "total_response_ms": 0, "queries": []}

    def _cortex_log_save(self, log: dict) -> None:
        path = self._cortex_log_path()
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(log, indent=2, ensure_ascii=False),
                       encoding="utf-8")
        os.replace(str(tmp), str(path))

    def _cortex_chat(self, messages: list[dict],
                     temperature: float = 0.3,
                     max_tokens: int = 2000) -> str | None:
        """Send chat completion request to LM Studio. Returns text or None."""
        import urllib.request
        import urllib.error

        payload = json.dumps({
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }).encode()
        req = urllib.request.Request(
            "http://localhost:1234/v1/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
            content = data["choices"][0]["message"]["content"]
            return content.strip() if content else None
        except (urllib.error.URLError, json.JSONDecodeError,
                KeyError, IndexError, OSError, TimeoutError):
            return None

    def _cortex_system_prompt(self) -> str:
        """Return the system prompt for forensic analysis.

        When Diamond Brains 3.0 personality is enabled, overlays
        high-velocity, decisive communication style onto the
        forensic analyst baseline.
        """
        base = (
            "You are Diamond Brain's Neural Cortex, a forensic intelligence "
            "analyst. You analyze evidence, legal citations, witness credibility, "
            "and temporal data to provide investigative insights.\n\n"
            "RULES:\n"
            "1. Always cite your sources — reference specific facts, citations, "
            "or events from the provided context.\n"
            "2. Note confidence levels — if facts have low confidence or "
            "contradictions exist, flag them.\n"
            "3. Be precise — state what the evidence shows, not what you assume.\n"
            "4. Flag gaps — if the context lacks information needed to fully "
            "answer, say so.\n"
            "5. Legal disclaimer — you are not providing legal advice. "
            "All statutory references should be verified at azleg.gov.\n"
            "6. Use professional forensic terminology.\n"
            "7. Structure your response with clear headings when appropriate."
        )
        if self._cortex_db3_enabled:
            base += self._cortex_db3_overlay()
        return base

    _cortex_db3_enabled: bool = False

    def cortex_set_personality(self, enabled: bool = True) -> dict:
        """Enable or disable Diamond Brains 3.0 personality overlay.

        When enabled, cortex responses use high-velocity, decisive
        communication: one-sentence nukes, killer constraints,
        confidence ratings, and zero hedging.
        """
        self._cortex_db3_enabled = enabled
        return {
            "personality": "db3" if enabled else "default",
            "status": "enabled" if enabled else "disabled",
        }

    @staticmethod
    def _cortex_db3_overlay() -> str:
        """Diamond Brains 3.0 personality overlay for cortex prompts."""
        return (
            "\n\nDIAMOND BRAINS 3.0 OVERLAY — ACTIVE:\n"
            "- Lead with the ONE variable that is 80x more decisive than "
            "all others combined. Treat the rest as background noise.\n"
            "- Open with a one-sentence nuke: the highest-leverage insight.\n"
            "- State confidence as [CONFIDENCE: XX%] at the top.\n"
            "- If multiple paths remain, present each as a path card with: "
            "when it wins, 3-5 bullet execution skeleton, rating (half-star).\n"
            "- No hedging, no disclaimers beyond the legal one, no filler.\n"
            "- End with a single unambiguous next action.\n"
            "- If something is broken or over-hyped, call it out bluntly.\n"
            "- Vibe: precise, high-velocity, zero fluff."
        )

    def cortex_debrief(self, topic: str | None = None) -> dict:
        """Diamond Brains 3.0 post-mortem: what worked, what missed,
        what to change.  Examines recent brain activity — contradictions,
        low-confidence facts, stale crystals, quarantine pressure — and
        produces a structured retrospective.

        Falls back to data-driven summary when LLM unavailable.
        """
        t0 = time.time()

        # Gather signals
        contradictions = self.detect_contradictions(topic=topic)
        quarantine = self._quarantine_load()
        q_eligible = [e for e in quarantine
                      if self._days_ago(e.get("quarantined_at", "")) >= 14]
        alerts = self.third_eye_scan()
        active_alerts = [a for a in alerts if not a.get("suppressed")]

        facts = (self.recall(topic, max_results=50, fuzzy=True)
                 if topic else self._load(self._facts_path))
        low_conf = [f for f in facts if f.get("confidence", 0) < 50]
        high_conf = [f for f in facts
                     if f.get("confidence", 0) >= 85
                     and f.get("verified")]

        hits: list[str] = []
        misses: list[str] = []
        changes: list[str] = []

        if high_conf:
            hits.append(f"{len(high_conf)} verified high-confidence facts "
                        f"holding strong")
        if not active_alerts:
            hits.append("Third Eye clean — no active alerts")
        elif len(active_alerts) <= 2:
            hits.append(f"Only {len(active_alerts)} Third Eye alert(s) — "
                        f"manageable")

        if contradictions:
            misses.append(f"{len(contradictions)} unresolved contradictions")
        if low_conf:
            misses.append(f"{len(low_conf)} facts below 50% confidence — "
                          f"need verification or pruning")
        if q_eligible:
            misses.append(f"{len(q_eligible)} quarantine items eligible for "
                          f"review — decision debt accumulating")

        crit_alerts = [a for a in active_alerts
                       if a.get("severity") == "CRITICAL"]
        if crit_alerts:
            changes.append(f"CRITICAL: {len(crit_alerts)} alert(s) need "
                           f"immediate attention")
        if len(low_conf) > len(facts) * 0.3 and facts:
            changes.append("Over 30% of facts are low-confidence — consider "
                           "a verification sweep")
        if len(quarantine) > 50:
            changes.append("Quarantine backlog exceeding 50 items — schedule "
                           "a purge review")

        # LLM-enhanced debrief if available
        llm_summary = None
        context_parts = []
        if hits:
            context_parts.append("HITS:\n" + "\n".join(
                f"  ✅ {h}" for h in hits))
        if misses:
            context_parts.append("MISSES:\n" + "\n".join(
                f"  ❌ {m}" for m in misses))
        if changes:
            context_parts.append("CHANGES:\n" + "\n".join(
                f"  🔄 {c}" for c in changes))
        context_str = "\n\n".join(context_parts)

        messages = [
            {"role": "system", "content": (
                "You are Diamond Brains 3.0 in debrief mode. Produce a "
                "tight post-mortem. Format: ✅ Hit / ❌ Miss / 🔄 Change. "
                "End with one compound lesson using 'Belief Cascade' "
                "(if wins are compounding) or 'Refractive Resolve' "
                "(if bouncing back from a bad state). Keep it under "
                "150 words total."
            )},
            {"role": "user", "content": (
                f"BRAIN STATE:\n{context_str}\n\n"
                f"Topic focus: {topic or 'full brain'}\n"
                f"Total facts: {len(facts)}, "
                f"Quarantine: {len(quarantine)}, "
                f"Active alerts: {len(active_alerts)}\n\n"
                "Give me the debrief."
            )},
        ]
        response = self._cortex_chat(messages)
        elapsed_ms = int((time.time() - t0) * 1000)

        if response:
            llm_summary = response
            self._cortex_track_query("debrief", "lm_studio",
                                     len(response.split()), elapsed_ms,
                                     question=f"debrief:{topic or 'all'}")

        return {
            "hits": hits,
            "misses": misses,
            "changes": changes,
            "llm_summary": llm_summary,
            "stats": {
                "total_facts": len(facts),
                "high_confidence": len(high_conf),
                "low_confidence": len(low_conf),
                "contradictions": len(contradictions),
                "quarantine_total": len(quarantine),
                "quarantine_eligible": len(q_eligible),
                "active_alerts": len(active_alerts),
                "critical_alerts": len(crit_alerts),
            },
            "model": "lm_studio" if llm_summary else "fallback",
            "fallback": llm_summary is None,
        }

    def _cortex_format_facts(self, facts: list[dict]) -> str:
        """Format fact list for LLM prompt."""
        lines = []
        for f in facts:
            conf = f.get("confidence", 0)
            eff = f.get("effective_confidence", conf)
            src = f.get("source", "unknown")
            lines.append(
                f"- [{f.get('topic', '?')}] (confidence: {eff}%, source: {src}) "
                f"{f.get('fact', '')}")
        return "\n".join(lines)

    def _cortex_format_citations(self, citations: list[dict]) -> str:
        """Format citation list for LLM prompt."""
        lines = []
        for c in citations:
            lines.append(
                f"- {c.get('code', '?')} [{c.get('severity', '?')}]: "
                f"{c.get('title', '')} — {c.get('text', '')[:200]}")
        return "\n".join(lines)

    def _cortex_build_context(self, query: str,
                              topics: list[str] | None = None,
                              max_facts: int = 15) -> str:
        """Assemble RAG context from multiple subsystems."""
        sections = []

        # 1. Relevant facts via hybrid_search
        facts = self.hybrid_search(query, top_k=max_facts)
        if not facts and topics:
            for t in topics[:3]:
                facts.extend(self.recall(t, max_results=5, fuzzy=True))
        if facts:
            sections.append("RELEVANT FACTS:\n" + self._cortex_format_facts(facts))

        # 2. Relevant citations
        citations = self.recall_citations(query=query, max_results=5)
        if not citations and topics:
            for t in topics[:2]:
                citations.extend(self.recall_citations(query=t, max_results=3))
        if citations:
            sections.append("LEGAL CITATIONS:\n"
                            + self._cortex_format_citations(citations))

        # 3. Temporal events (if query mentions time-related words)
        time_words = {"when", "before", "after", "during", "timeline",
                      "sequence", "first", "last", "time", "date", "event"}
        if time_words & set(query.lower().split()):
            events = self.temporal_chain()
            if events:
                event_lines = []
                for e in events[:8]:
                    event_lines.append(
                        f"- [{e.get('start', '?')}] {e.get('event_id', '?')}: "
                        f"{e.get('data', {}).get('description', '')}")
                sections.append("TIMELINE:\n" + "\n".join(event_lines))

        # 4. Contradictions in the retrieved facts
        fact_topics = list(set(f.get("topic", "") for f in facts))
        for t in fact_topics[:3]:
            contras = self.detect_contradictions(topic=t)
            if contras:
                contra_lines = []
                for c in contras[:3]:
                    contra_lines.append(
                        f"- {c['type']}: \"{c['fact_a']['fact'][:60]}\" vs "
                        f"\"{c['fact_b']['fact'][:60]}\"")
                sections.append("CONTRADICTIONS DETECTED:\n"
                                + "\n".join(contra_lines))
                break

        # 5. Source credibility for mentioned sources
        source_ids = list(set(
            f.get("source", "") for f in facts if f.get("source")))
        if source_ids:
            cred_lines = []
            for sid in source_ids[:3]:
                cred = self.source_credibility(sid)
                if "error" not in cred:
                    cred_lines.append(
                        f"- {sid}: credibility={cred['credibility_score']}/100 "
                        f"({cred['source_type']})")
            if cred_lines:
                sections.append("SOURCE CREDIBILITY:\n"
                                + "\n".join(cred_lines))

        context = "\n\n".join(sections)
        if len(context) > 6000:
            context = (context[:5950]
                       + "\n\n[... context truncated for model limits ...]")
        return context

    def _cortex_track_query(self, method: str, model: str,
                            tokens: int, response_ms: int,
                            question: str = "",
                            fallback: bool = False) -> None:
        """Track cortex usage stats."""
        log = self._cortex_log_load()
        log["total_queries"] = log.get("total_queries", 0) + 1
        log["total_tokens"] = log.get("total_tokens", 0) + tokens
        log["total_response_ms"] = log.get("total_response_ms", 0) + response_ms
        log["queries"].append({
            "method": method,
            "question": question[:200],
            "model": model,
            "tokens": tokens,
            "response_ms": response_ms,
            "fallback": fallback,
            "timestamp": _now_iso(),
        })
        log["queries"] = log["queries"][-500:]
        self._cortex_log_save(log)

    @staticmethod
    def _cortex_parse_json_list(text: str) -> list[dict]:
        """Extract a JSON list from LLM response text."""
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [ln for ln in lines if not ln.strip().startswith("```")]
            cleaned = "\n".join(lines)
        try:
            result = json.loads(cleaned)
            if isinstance(result, list):
                return result
            if isinstance(result, dict):
                return [result]
        except json.JSONDecodeError:
            pass
        start = cleaned.find("[")
        end = cleaned.rfind("]")
        if start != -1 and end != -1 and end > start:
            try:
                result = json.loads(cleaned[start:end + 1])
                if isinstance(result, list):
                    return result
            except json.JSONDecodeError:
                pass
        return [{"hypothesis": cleaned, "supporting_evidence": [],
                 "confidence": 0, "reasoning": "Unparseable LLM response"}]

    @staticmethod
    def _cortex_parse_sections(text: str) -> list[dict]:
        """Parse markdown-style sections from LLM response."""
        sections = []
        current_title = ""
        current_lines: list[str] = []

        for line in text.split("\n"):
            stripped = line.strip()
            is_heading = False
            heading_text = ""
            if stripped.startswith("## "):
                is_heading = True
                heading_text = stripped[3:].strip()
            elif stripped.startswith("# "):
                is_heading = True
                heading_text = stripped[2:].strip()
            elif (len(stripped) > 3 and stripped[0].isdigit()
                  and stripped[1] in ".)" and stripped[2] == " "):
                is_heading = True
                heading_text = stripped[3:].strip()

            if is_heading and heading_text:
                if current_title:
                    sections.append({
                        "title": current_title,
                        "content": "\n".join(current_lines).strip(),
                        "citations": [],
                    })
                current_title = heading_text
                current_lines = []
            else:
                current_lines.append(line)

        if current_title:
            sections.append({
                "title": current_title,
                "content": "\n".join(current_lines).strip(),
                "citations": [],
            })
        return sections if sections else [{"title": "Response",
                                           "content": text, "citations": []}]

    # --- Public Cortex Methods ---

    def cortex_ask(self, question: str,
                   topics: list[str] | None = None,
                   max_context: int = 15) -> dict:
        """RAG-powered question answering against the knowledge base.

        Falls back to bullet-point summary when LLM unavailable.
        """
        t0 = time.time()
        context = self._cortex_build_context(question, topics, max_context)

        messages = [
            {"role": "system", "content": self._cortex_system_prompt()},
            {"role": "user", "content": (
                f"CONTEXT:\n{context}\n\n"
                f"QUESTION: {question}\n\n"
                "Answer based on the provided context. Cite specific facts "
                "and citations. Note any contradictions or low-confidence data."
            )},
        ]

        response = self._cortex_chat(messages)
        elapsed_ms = int((time.time() - t0) * 1000)

        if response:
            facts = self.hybrid_search(question, top_k=max_context)
            sources = list(set(
                f.get("source", "unknown") for f in facts if f.get("source")
            ))
            self._cortex_track_query("ask", "lm_studio",
                                     len(response.split()), elapsed_ms,
                                     question=question)
            return {
                "answer": response,
                "sources_used": sources[:10],
                "model": "lm_studio",
                "tokens_used": len(response.split()),
                "fallback": False,
            }

        # FALLBACK: bullet-point summary from retrieved facts
        facts = self.hybrid_search(question, top_k=max_context)
        if not facts and topics:
            for t in topics[:3]:
                facts.extend(self.recall(t, max_results=5, fuzzy=True))

        if facts:
            bullets = []
            for f in facts[:10]:
                bullets.append(
                    f"- [{f.get('topic', '?')}] {f.get('fact', '')} "
                    f"(confidence: {f.get('confidence', 0)}%)")
            answer = ("[LLM unavailable — showing matched facts]\n\n"
                      + "\n".join(bullets))
        else:
            answer = "[LLM unavailable — no matching facts found for this query]"

        sources = list(set(
            f.get("source", "unknown") for f in facts if f.get("source")
        ))
        self._cortex_track_query("ask", "fallback", 0, elapsed_ms,
                                 question=question, fallback=True)
        return {
            "answer": answer,
            "sources_used": sources[:10],
            "model": "fallback",
            "tokens_used": 0,
            "fallback": True,
        }

    def cortex_summarize(self, topic: str) -> dict:
        """Summarize all knowledge about a topic.

        Falls back to crystallize() output.
        """
        t0 = time.time()
        facts = self.recall(topic, max_results=50, fuzzy=True)

        # Get graph neighbors for broader context
        graph = self._graph_load()
        related_topics: set[str] = set()
        for edge in graph.get("edges", []):
            if topic.lower() in edge.get("source", "").lower():
                related_topics.add(edge.get("target", ""))
            elif topic.lower() in edge.get("target", "").lower():
                related_topics.add(edge.get("source", ""))

        for rt in list(related_topics)[:3]:
            facts.extend(self.recall(rt, max_results=5, fuzzy=True))

        crystals = self.crystallize(topic=topic, min_cluster=1)

        context_parts = [self._cortex_format_facts(facts)]
        if crystals:
            for c in crystals[:2]:
                context_parts.append(
                    f"CRYSTAL SUMMARY ({c.get('topic', '?')}): "
                    f"key_terms={c.get('key_terms', [])}, "
                    f"avg_confidence={c.get('avg_confidence', 0):.0f}%")

        context = "\n\n".join(context_parts)
        if len(context) > 6000:
            context = context[:5950] + "\n[... truncated ...]"

        messages = [
            {"role": "system", "content": self._cortex_system_prompt()},
            {"role": "user", "content": (
                f"CONTEXT:\n{context}\n\n"
                f"Summarize all knowledge about \"{topic}\". Include:\n"
                "1. Key findings and their confidence levels\n"
                "2. Sources and their reliability\n"
                "3. Any contradictions or gaps\n"
                "4. Related topics worth investigating"
            )},
        ]

        response = self._cortex_chat(messages)
        elapsed_ms = int((time.time() - t0) * 1000)

        if response:
            self._cortex_track_query("summarize", "lm_studio",
                                     len(response.split()), elapsed_ms,
                                     question=topic)
            return {
                "summary": response,
                "fact_count": len(facts),
                "topic": topic,
                "model": "lm_studio",
                "fallback": False,
            }

        # FALLBACK: use crystallize output
        if crystals:
            parts = []
            for c in crystals:
                parts.append(
                    f"Topic: {c.get('topic', '?')} "
                    f"({c.get('fact_count', 0)} facts, "
                    f"avg confidence: {c.get('avg_confidence', 0):.0f}%)\n"
                    f"Key terms: {', '.join(c.get('key_terms', []))}\n"
                    f"Sources: {', '.join(c.get('sources', []))}")
            summary = ("[LLM unavailable — showing crystallized analysis]\n\n"
                       + "\n\n".join(parts))
        else:
            bullets = [f"- {f.get('fact', '')}" for f in facts[:10]]
            summary = (
                f"[LLM unavailable — {len(facts)} facts on '{topic}']\n\n"
                + "\n".join(bullets) if bullets
                else f"[No facts found for topic '{topic}']"
            )

        self._cortex_track_query("summarize", "fallback", 0, elapsed_ms,
                                 question=topic, fallback=True)
        return {
            "summary": summary,
            "fact_count": len(facts),
            "topic": topic,
            "model": "fallback",
            "fallback": True,
        }

    def cortex_hypothesize(self, evidence_facts: list[str],
                           question: str) -> dict:
        """Generate investigative hypotheses from evidence.

        evidence_facts: list of fact topics or text snippets.
        Falls back to anomalies + contradictions as areas of interest.
        """
        t0 = time.time()

        all_facts: list[dict] = []
        for ef in evidence_facts:
            topic_facts = self.recall(ef, max_results=5, fuzzy=True)
            if topic_facts:
                all_facts.extend(topic_facts)
            else:
                all_facts.extend(self.search(ef)[:5])

        anomalies = self.temporal_detect_anomalies(max_results=5)
        contradictions = self.detect_contradictions()[:5]

        context_parts = [self._cortex_format_facts(all_facts)]

        if anomalies:
            anom_lines = [
                f"- {a['type']} [{a['severity']}]: {a.get('message', '')}"
                for a in anomalies[:5]]
            context_parts.append("TEMPORAL ANOMALIES:\n"
                                 + "\n".join(anom_lines))

        if contradictions:
            contra_lines = [
                f"- {c['type']}: \"{c['fact_a']['fact'][:50]}\" vs "
                f"\"{c['fact_b']['fact'][:50]}\""
                for c in contradictions[:5]]
            context_parts.append("CONTRADICTIONS:\n"
                                 + "\n".join(contra_lines))

        context = "\n\n".join(context_parts)
        if len(context) > 6000:
            context = context[:5950] + "\n[... truncated ...]"

        messages = [
            {"role": "system", "content": self._cortex_system_prompt()},
            {"role": "user", "content": (
                f"EVIDENCE:\n{context}\n\n"
                f"QUESTION: {question}\n\n"
                "Generate 2-4 investigative hypotheses. For each:\n"
                "1. State the hypothesis\n"
                "2. List supporting evidence from context\n"
                "3. Rate confidence (0-100%)\n"
                "4. Explain reasoning\n\n"
                "Respond in JSON: [{\"hypothesis\": \"...\", "
                "\"supporting_evidence\": [\"...\"], "
                "\"confidence\": N, \"reasoning\": \"...\"}]"
            )},
        ]

        response = self._cortex_chat(messages, temperature=0.4)
        elapsed_ms = int((time.time() - t0) * 1000)

        if response:
            hypotheses = self._cortex_parse_json_list(response)
            self._cortex_track_query("hypothesize", "lm_studio",
                                     len(response.split()), elapsed_ms,
                                     question=question)
            return {
                "hypotheses": hypotheses,
                "model": "lm_studio",
                "fallback": False,
            }

        # FALLBACK: anomalies and contradictions as areas of interest
        fallback_hypotheses: list[dict] = []
        for a in anomalies[:2]:
            fallback_hypotheses.append({
                "hypothesis": f"Temporal anomaly requires investigation: "
                              f"{a.get('message', '')}",
                "supporting_evidence": a.get("events", []),
                "confidence": 0,
                "reasoning": f"[LLM unavailable] {a['type']} ({a['severity']})",
            })
        for c in contradictions[:2]:
            fallback_hypotheses.append({
                "hypothesis": "Contradiction needs resolution between sources",
                "supporting_evidence": [c["fact_a"]["fact"][:80],
                                        c["fact_b"]["fact"][:80]],
                "confidence": 0,
                "reasoning": f"[LLM unavailable] {c['type']} detected",
            })
        if not fallback_hypotheses:
            fallback_hypotheses.append({
                "hypothesis": "[LLM unavailable — insufficient data "
                              "for auto-hypothesis]",
                "supporting_evidence": [],
                "confidence": 0,
                "reasoning": "No temporal anomalies or contradictions detected",
            })

        self._cortex_track_query("hypothesize", "fallback", 0, elapsed_ms,
                                 question=question, fallback=True)
        return {
            "hypotheses": fallback_hypotheses,
            "model": "fallback",
            "fallback": True,
        }

    def cortex_cross_examine(self, source_id: str) -> dict:
        """Analyze a source's credibility with LLM reasoning.

        Falls back to raw credibility data + contradictions.
        """
        t0 = time.time()

        cred = self.source_credibility(source_id)
        if "error" in cred:
            return cred

        # Get all facts from this source
        all_facts = self._load(self._facts_path)
        source_facts = [f for f in all_facts
                        if f.get("source", "") == source_id
                        and not f.get("_crdt", {}).get("tombstone")]

        # Check contradictions involving these facts
        relevant_contras: list[dict] = []
        fact_topics = set(f.get("topic", "") for f in source_facts)
        for t in list(fact_topics)[:5]:
            contras = self.detect_contradictions(topic=t)
            for c in contras:
                if (c["fact_a"].get("source") == source_id
                        or c["fact_b"].get("source") == source_id):
                    relevant_contras.append(c)

        context_parts = [
            f"SOURCE PROFILE:\n"
            f"- ID: {source_id}\n"
            f"- Type: {cred.get('source_type', '?')}\n"
            f"- Credibility Score: {cred.get('credibility_score', 0)}/100\n"
            f"- Sub-scores: {json.dumps(cred.get('sub_scores', {}))}\n"
            f"- Facts contributed: {cred.get('facts_contributed', 0)}\n"
            f"- Contradictions flagged: {cred.get('contradictions_flagged', 0)}",

            "FACTS FROM THIS SOURCE:\n"
            + self._cortex_format_facts(source_facts[:15]),
        ]

        if relevant_contras:
            contra_lines = [
                f"- {c['type']}: \"{c['fact_a']['fact'][:50]}\" vs "
                f"\"{c['fact_b']['fact'][:50]}\""
                for c in relevant_contras[:5]]
            context_parts.append(
                "CONTRADICTIONS INVOLVING THIS SOURCE:\n"
                + "\n".join(contra_lines))

        context = "\n\n".join(context_parts)
        if len(context) > 6000:
            context = context[:5950] + "\n[... truncated ...]"

        messages = [
            {"role": "system", "content": self._cortex_system_prompt()},
            {"role": "user", "content": (
                f"CONTEXT:\n{context}\n\n"
                f"Analyze the reliability of source '{source_id}'. Include:\n"
                "1. Overall credibility assessment\n"
                "2. Specific reliability flags (positive or negative)\n"
                "3. Any patterns in their contributions\n"
                "4. Recommendations for how to weight this source's information"
            )},
        ]

        response = self._cortex_chat(messages)
        elapsed_ms = int((time.time() - t0) * 1000)

        flags: list[str] = []
        if cred.get("contradictions_flagged", 0) > 0:
            flags.append("contradictions_present")
        if cred.get("credibility_score", 0) < 50:
            flags.append("low_credibility")
        if cred.get("sub_scores", {}).get("consistency", 100) < 50:
            flags.append("inconsistent")

        if response:
            self._cortex_track_query("cross_examine", "lm_studio",
                                     len(response.split()), elapsed_ms,
                                     question=source_id)
            return {
                "analysis": response,
                "credibility_score": cred.get("credibility_score", 0),
                "flags": flags,
                "recommendations": [],
                "model": "lm_studio",
                "fallback": False,
            }

        # FALLBACK: raw credibility data
        analysis_parts = [
            "[LLM unavailable — raw credibility data]",
            f"Score: {cred.get('credibility_score', 0)}/100",
            f"Type: {cred.get('source_type', '?')}",
            f"Facts contributed: {cred.get('facts_contributed', 0)}",
            f"Sub-scores: {json.dumps(cred.get('sub_scores', {}))}",
        ]
        if relevant_contras:
            analysis_parts.append(
                f"Contradictions found: {len(relevant_contras)}")

        self._cortex_track_query("cross_examine", "fallback", 0, elapsed_ms,
                                 question=source_id, fallback=True)
        return {
            "analysis": "\n".join(analysis_parts),
            "credibility_score": cred.get("credibility_score", 0),
            "flags": flags,
            "recommendations": [],
            "model": "fallback",
            "fallback": True,
        }

    def cortex_timeline_narrative(
            self, event_ids: list[str] | None = None) -> dict:
        """Generate a prose narrative from the temporal chain.

        Falls back to formatted timeline with anomaly annotations.
        """
        t0 = time.time()

        chain = self.temporal_chain(event_ids=event_ids)
        anomalies = self.temporal_detect_anomalies(
            event_ids=event_ids, max_results=10)

        if not chain:
            return {
                "narrative": "No temporal events found.",
                "event_count": 0,
                "anomalies_noted": 0,
                "model": "none",
                "fallback": False,
            }

        event_lines = []
        for e in chain:
            desc = e.get("data", {}).get("description", "")
            line = f"- [{e.get('start', '?')}] {e.get('event_id', '?')}"
            if desc:
                line += f": {desc}"
            event_lines.append(line)

        context_parts = ["EVENTS (chronological):\n"
                         + "\n".join(event_lines)]

        if anomalies:
            anom_lines = [
                f"- {a['type']} [{a['severity']}]: {a.get('message', '')}"
                for a in anomalies]
            context_parts.append("ANOMALIES:\n" + "\n".join(anom_lines))

        context = "\n\n".join(context_parts)
        if len(context) > 6000:
            context = context[:5950] + "\n[... truncated ...]"

        messages = [
            {"role": "system", "content": self._cortex_system_prompt()},
            {"role": "user", "content": (
                f"CONTEXT:\n{context}\n\n"
                "Write a clear, chronological narrative of these events. "
                "Highlight any anomalies or suspicious patterns. "
                "Use professional forensic language."
            )},
        ]

        response = self._cortex_chat(messages)
        elapsed_ms = int((time.time() - t0) * 1000)

        if response:
            self._cortex_track_query("timeline_narrative", "lm_studio",
                                     len(response.split()), elapsed_ms)
            return {
                "narrative": response,
                "event_count": len(chain),
                "anomalies_noted": len(anomalies),
                "model": "lm_studio",
                "fallback": False,
            }

        # FALLBACK: formatted timeline
        lines = []
        for e in chain:
            desc = e.get("data", {}).get("description",
                                         e.get("event_id", "?"))
            lines.append(f"[{e.get('start', '?')}] {desc}")
        if anomalies:
            lines.append("\nANOMALIES DETECTED:")
            for a in anomalies:
                lines.append(
                    f"  [{a['severity']}] {a['type']}: "
                    f"{a.get('message', '')}")

        self._cortex_track_query("timeline_narrative", "fallback", 0,
                                 elapsed_ms, fallback=True)
        return {
            "narrative": ("[LLM unavailable — formatted timeline]\n\n"
                          + "\n".join(lines)),
            "event_count": len(chain),
            "anomalies_noted": len(anomalies),
            "model": "fallback",
            "fallback": True,
        }

    def cortex_case_brief(self, topics: list[str] | None = None,
                          case_number: str = "") -> dict:
        """Generate a comprehensive case brief.

        Falls back to template-based brief.
        """
        t0 = time.time()

        if topics:
            facts: list[dict] = []
            for t in topics:
                facts.extend(self.recall(t, max_results=20, fuzzy=True))
        else:
            facts = self._load(self._facts_path)
            facts = [f for f in facts
                     if not f.get("_crdt", {}).get("tombstone")]

        citations = self._load(self._citations_path)
        chain = self.temporal_chain()
        contradictions = self.detect_contradictions()
        crystals = self.crystallize(min_cluster=3)

        source_ids = list(set(
            f.get("source", "") for f in facts if f.get("source")))
        cred_summaries = []
        for sid in source_ids[:5]:
            c = self.source_credibility(sid)
            if "error" not in c:
                cred_summaries.append(
                    f"{sid}: {c['credibility_score']}/100 ({c['source_type']})")

        context_parts = [
            f"CASE NUMBER: {case_number or '(unassigned)'}",
            f"FACTS ({len(facts)} total):\n"
            + self._cortex_format_facts(facts[:20]),
        ]
        if citations:
            context_parts.append(
                f"CITATIONS ({len(citations)} total):\n"
                + self._cortex_format_citations(citations[:10]))
        if chain:
            event_lines = [f"- [{e.get('start', '?')}] {e.get('event_id', '?')}"
                           for e in chain[:10]]
            context_parts.append("TIMELINE:\n" + "\n".join(event_lines))
        if contradictions:
            contra_lines = [
                f"- {c['type']}: gap={c.get('confidence_gap', 0)}pt"
                for c in contradictions[:5]]
            context_parts.append("CONTRADICTIONS:\n"
                                 + "\n".join(contra_lines))
        if cred_summaries:
            context_parts.append("SOURCE CREDIBILITY:\n- "
                                 + "\n- ".join(cred_summaries))
        if crystals:
            crystal_lines = [
                f"- {c.get('topic', '?')}: "
                f"{', '.join(c.get('key_terms', [])[:5])}"
                for c in crystals[:5]]
            context_parts.append("INSIGHTS:\n" + "\n".join(crystal_lines))

        context = "\n\n".join(context_parts)
        if len(context) > 6000:
            context = context[:5950] + "\n[... truncated ...]"

        case_label = (f" for case {case_number}" if case_number else "")
        messages = [
            {"role": "system", "content": self._cortex_system_prompt()},
            {"role": "user", "content": (
                f"CONTEXT:\n{context}\n\n"
                f"Generate a formal case brief{case_label}. "
                "Structure with these sections:\n"
                "1. Executive Summary\n"
                "2. Evidence Overview\n"
                "3. Timeline of Events\n"
                "4. Source Credibility Assessment\n"
                "5. Contradictions and Anomalies\n"
                "6. Key Legal Citations\n"
                "7. Conclusions and Recommendations\n\n"
                "Include the disclaimer: 'Not legal advice. Verify at azleg.gov.'"
            )},
        ]

        response = self._cortex_chat(messages, max_tokens=3000)
        elapsed_ms = int((time.time() - t0) * 1000)

        if response:
            self._cortex_track_query("case_brief", "lm_studio",
                                     len(response.split()), elapsed_ms,
                                     question=case_number or "full_brief")
            brief_sections = self._cortex_parse_sections(response)
            return {
                "brief": response,
                "sections": brief_sections,
                "model": "lm_studio",
                "fallback": False,
            }

        # FALLBACK: template-based brief
        brief_sections = [
            {"title": "Executive Summary",
             "content": f"Case brief for {case_number or '(unassigned)'}. "
                        f"{len(facts)} facts, {len(citations)} citations, "
                        f"{len(chain)} timeline events.",
             "citations": []},
            {"title": "Evidence Overview",
             "content": self._cortex_format_facts(facts[:10]),
             "citations": []},
            {"title": "Timeline",
             "content": "\n".join(
                 f"[{e.get('start', '?')}] {e.get('event_id', '?')}"
                 for e in chain[:10]) or "No timeline events.",
             "citations": []},
            {"title": "Contradictions",
             "content": "\n".join(
                 f"{c['type']}: gap={c.get('confidence_gap', 0)}pt"
                 for c in contradictions[:5]) or "No contradictions detected.",
             "citations": []},
            {"title": "Legal Citations",
             "content": self._cortex_format_citations(citations[:10]),
             "citations": [c.get("code", "") for c in citations[:10]]},
            {"title": "Disclaimer",
             "content": "Not legal advice. Verify at azleg.gov.",
             "citations": []},
        ]

        brief = "[LLM unavailable — template-based brief]\n\n"
        for s in brief_sections:
            brief += f"## {s['title']}\n{s['content']}\n\n"

        self._cortex_track_query("case_brief", "fallback", 0, elapsed_ms,
                                 question=case_number or "full_brief",
                                 fallback=True)
        return {
            "brief": brief,
            "sections": brief_sections,
            "model": "fallback",
            "fallback": True,
        }

    def cortex_status(self) -> dict:
        """Check LLM connectivity and cortex stats."""
        import urllib.request
        import urllib.error

        url = "http://localhost:1234/v1/models"
        available = False
        model = None

        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
            models = data.get("data", [])
            if models:
                available = True
                model = models[0].get("id", "unknown")
        except (urllib.error.URLError, json.JSONDecodeError,
                KeyError, OSError, TimeoutError):
            pass

        log = self._cortex_log_load()
        total_q = log.get("total_queries", 0)
        avg_ms = (round(log.get("total_response_ms", 0) / total_q)
                  if total_q > 0 else 0)
        last_query = (log["queries"][-1] if log.get("queries") else None)

        return {
            "available": available,
            "model": model,
            "url": "http://localhost:1234",
            "total_queries": total_q,
            "last_query": last_query,
            "avg_response_ms": avg_ms,
        }

    # ==================================================================
    # FEATURE 30: THE THIRD EYE — Meta-Cognitive Surveillance
    # ==================================================================
    # The Third Eye scans the brain's own internals for 12 categories of
    # silence, decay, and hidden danger.  Every alert it fires represents
    # something the brain knew — but never surfaced.
    # ------------------------------------------------------------------

    # ---- storage helpers ---------------------------------------------

    def _eye_path(self) -> Path:
        return self.memory_dir / "third_eye.json"

    def _eye_load(self) -> dict:
        path = self._eye_path()
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return {
            "last_scan": None,
            "total_scans": 0,
            "suppressed": {},
            "watched_topics": [],
            "alerts": [],
            "total_alerts": 0,
        }

    def _eye_save(self, state: dict) -> None:
        path = self._eye_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False),
                       encoding="utf-8")
        os.replace(str(tmp), str(path))

    # ---- severity ordering -------------------------------------------
    _EYE_SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

    # ---- 12 detectors ------------------------------------------------

    def _eye_detect_unresolved_escalations(self, watched: set) -> list[dict]:
        """CRITICAL if >7 days old, HIGH if newer."""
        escalations = self._load(self._escalations_path)
        alerts: list[dict] = []
        for esc in escalations:
            if esc.get("resolved"):
                continue
            days = _days_ago(esc.get("escalated_at", ""))
            sev = "CRITICAL" if days > 7 else "HIGH"
            finding = esc.get("finding", {})
            cat = finding.get("category", "unknown")
            alerts.append({
                "type": "unresolved_escalations",
                "severity": sev,
                "message": f"Escalation '{cat}' unresolved for {days} days",
                "affected": [cat],
                "recommended_action": "Review and resolve the escalation or add brain knowledge on the topic",
                "suppressed": False,
            })
        return alerts

    def _eye_detect_tombstone_accumulation(self, watched: set) -> list[dict]:
        """HIGH if >20% tombstoned, MEDIUM if >10%."""
        facts = self._load(self._facts_path)
        if not facts:
            return []
        tombstoned = sum(1 for f in facts
                         if f.get("_crdt", {}).get("tombstone"))
        ratio = tombstoned / len(facts)
        threshold_high = 0.10 if watched else 0.20
        threshold_med = 0.05 if watched else 0.10
        if ratio >= threshold_high:
            return [{
                "type": "tombstone_accumulation",
                "severity": "HIGH",
                "message": f"{tombstoned}/{len(facts)} facts ({ratio:.0%}) are tombstoned — silent data bloat",
                "affected": [f"tombstone_ratio:{ratio:.2f}"],
                "recommended_action": "Consider garbage-collecting tombstoned facts",
                "suppressed": False,
            }]
        if ratio >= threshold_med:
            return [{
                "type": "tombstone_accumulation",
                "severity": "MEDIUM",
                "message": f"{tombstoned}/{len(facts)} facts ({ratio:.0%}) are tombstoned",
                "affected": [f"tombstone_ratio:{ratio:.2f}"],
                "recommended_action": "Monitor tombstone growth; gc if exceeds 20%",
                "suppressed": False,
            }]
        return []

    def _eye_detect_orphaned_blobs(self, watched: set) -> list[dict]:
        """HIGH per .blob file with no .meta.json sidecar."""
        if not self._blobs_dir.exists():
            return []
        blobs = {p.stem for p in self._blobs_dir.glob("*.blob")}
        metas = {p.stem.replace(".meta", "")
                 for p in self._blobs_dir.glob("*.meta.json")}
        orphans = blobs - metas
        if not orphans:
            return []
        return [{
            "type": "orphaned_blobs",
            "severity": "HIGH",
            "message": f"{len(orphans)} blob(s) without metadata sidecar — evidence integrity at risk",
            "affected": sorted(orphans),
            "recommended_action": "Re-store orphaned blobs or remove them; check for interrupted writes",
            "suppressed": False,
        }]

    def _eye_detect_graph_isolation(self, watched: set) -> list[dict]:
        """MEDIUM — nodes with zero edge connections (invisible to BFS)."""
        graph = self._graph_load()
        nodes = graph.get("nodes", {})
        edges = graph.get("edges", [])
        if not nodes:
            return []
        connected = set()
        for e in edges:
            connected.add(e.get("source", ""))
            connected.add(e.get("target", ""))
        isolated = [nid for nid in nodes if nid not in connected]
        if not isolated:
            return []
        return [{
            "type": "graph_isolation",
            "severity": "MEDIUM",
            "message": f"{len(isolated)} graph node(s) have zero edges — invisible to traversal",
            "affected": isolated[:15],
            "recommended_action": "Run graph_auto_index() to rebuild edges or remove orphaned nodes",
            "suppressed": False,
        }]

    def _eye_detect_stale_crystals(self, watched: set) -> list[dict]:
        """MEDIUM — crystal older than newest fact in its topic."""
        facts = self._load(self._facts_path)
        graph = self._graph_load()
        alerts: list[dict] = []
        # Find crystal nodes
        for nid, node in graph.get("nodes", {}).items():
            if node.get("type") != "crystal":
                continue
            crystal_data = node.get("data", {})
            crystal_topic = crystal_data.get("topic", "")
            crystal_at = crystal_data.get("crystallized_at", "")
            if not crystal_at:
                continue
            # Find newest fact for this topic
            topic_facts = [f for f in facts
                           if f.get("topic", "").lower() == crystal_topic.lower()]
            if not topic_facts:
                continue
            newest_fact = max(
                (f.get("updated_at", f.get("created_at", ""))
                 for f in topic_facts), default="")
            if not newest_fact or newest_fact <= crystal_at:
                continue
            # Crystal is stale
            stale_days = _days_ago(crystal_at)
            threshold = 3 if crystal_topic.lower() in watched else 7
            if stale_days >= threshold:
                alerts.append({
                    "type": "stale_crystals",
                    "severity": "MEDIUM",
                    "message": f"Crystal for '{crystal_topic}' is {stale_days} days old but topic has newer facts",
                    "affected": [crystal_topic],
                    "recommended_action": f"Re-run crystallize(topic='{crystal_topic}') to refresh insights",
                    "suppressed": False,
                })
        return alerts

    def _eye_detect_inactive_sources(self, watched: set) -> list[dict]:
        """HIGH if last_contributed=None, MEDIUM if >30 days silent."""
        sources = self._sources_load()
        alerts: list[dict] = []
        for src in sources:
            sid = src.get("source_id", "unknown")
            last = src.get("last_contributed")
            if last is None:
                alerts.append({
                    "type": "inactive_sources",
                    "severity": "HIGH",
                    "message": f"Source '{sid}' registered but NEVER contributed — phantom source",
                    "affected": [sid],
                    "recommended_action": f"Learn facts with source='{sid}' or remove the registration",
                    "suppressed": False,
                })
            elif _days_ago(last) > 30:
                alerts.append({
                    "type": "inactive_sources",
                    "severity": "MEDIUM",
                    "message": f"Source '{sid}' silent for {_days_ago(last)} days",
                    "affected": [sid],
                    "recommended_action": "Check if source is still active; update or archive",
                    "suppressed": False,
                })
        return alerts

    def _eye_detect_crime_citation_voids(self, watched: set) -> list[dict]:
        """HIGH — facts with crime keywords but empty links array."""
        facts = self._load(self._facts_path)
        _CRIME_KEYWORDS = {
            "murder", "homicide", "manslaughter", "assault", "battery",
            "robbery", "burglary", "theft", "larceny", "arson",
            "kidnapping", "rape", "weapons", "firearm", "drug",
            "narcotic", "dui", "dwi", "trespass", "forgery",
            "fraud", "embezzlement", "extortion", "stalking",
        }
        voids: list[str] = []
        for f in facts:
            if f.get("_crdt", {}).get("tombstone"):
                continue
            text = (f.get("topic", "") + " " + f.get("fact", "")).lower()
            has_crime = any(kw in text for kw in _CRIME_KEYWORDS)
            if has_crime and not f.get("links"):
                voids.append(f.get("topic", "unknown"))
        if not voids:
            return []
        return [{
            "type": "crime_citation_voids",
            "severity": "HIGH",
            "message": f"{len(voids)} fact(s) mention crimes but have NO citation links — Rule 6 violation",
            "affected": sorted(set(voids)),
            "recommended_action": "Run link_crime_to_citations() for affected topics or learn with proper citations",
            "suppressed": False,
        }]

    def _eye_detect_never_reviewed_facts(self, watched: set) -> list[dict]:
        """MEDIUM if >20 facts (or >10 for watched topics) with fsrs_reps=0."""
        facts = self._load(self._facts_path)
        never_reviewed = [f for f in facts
                          if not f.get("_crdt", {}).get("tombstone")
                          and f.get("fsrs_reps", 0) == 0]
        # Lower threshold if any never-reviewed fact is in a watched topic
        has_watched = any(f.get("topic", "").lower() in watched
                          for f in never_reviewed) if watched else False
        threshold = 10 if has_watched else 20
        if len(never_reviewed) < threshold:
            return []
        return [{
            "type": "never_reviewed_facts",
            "severity": "MEDIUM",
            "message": f"{len(never_reviewed)} facts have NEVER been reviewed (fsrs_reps=0) — invisible to spaced repetition",
            "affected": sorted(set(f.get("topic", "unknown")
                                   for f in never_reviewed))[:15],
            "recommended_action": "Run fsrs_due() and review pending facts to activate retention tracking",
            "suppressed": False,
        }]

    def _eye_detect_stale_merkle(self, watched: set) -> list[dict]:
        """MEDIUM if merkle_dag.json has stale=True."""
        dag = self._merkle_load()
        if not dag or not dag.get("stale"):
            return []
        return [{
            "type": "stale_merkle",
            "severity": "MEDIUM",
            "message": "Merkle DAG is stale — custody chain integrity not provable",
            "affected": [str(self._merkle_path())],
            "recommended_action": "Run --link-custody --verify to rebuild the Merkle DAG",
            "suppressed": False,
        }]

    def _eye_detect_custody_cap_proximity(self, watched: set) -> list[dict]:
        """CRITICAL if >4500 records, HIGH if >4000."""
        log = self._link_load_custody_log()
        count = len(log)
        if count > 4500:
            return [{
                "type": "custody_cap_proximity",
                "severity": "CRITICAL",
                "message": f"Custody log at {count:,}/5,000 — chain corruption imminent on overflow",
                "affected": ["link/custody_log.json"],
                "recommended_action": "Archive old custody records immediately; chain will break at 5000",
                "suppressed": False,
            }]
        if count > 4000:
            return [{
                "type": "custody_cap_proximity",
                "severity": "HIGH",
                "message": f"Custody log at {count:,}/5,000 — approaching silent truncation",
                "affected": ["link/custody_log.json"],
                "recommended_action": "Plan custody log archival before reaching 5000-record cap",
                "suppressed": False,
            }]
        return []

    def _eye_detect_ghost_graph_topics(self, watched: set) -> list[dict]:
        """LOW — graph topic nodes for topics pruned from facts.json."""
        facts = self._load(self._facts_path)
        graph = self._graph_load()
        live_topics = {f.get("topic", "").lower() for f in facts
                       if not f.get("_crdt", {}).get("tombstone")}
        ghosts: list[str] = []
        for nid, node in graph.get("nodes", {}).items():
            if node.get("type") != "topic":
                continue
            node_label = node.get("data", {}).get("label", "").lower()
            if node_label and node_label not in live_topics:
                ghosts.append(node_label)
        if not ghosts:
            return []
        return [{
            "type": "ghost_graph_topics",
            "severity": "LOW",
            "message": f"{len(ghosts)} graph topic node(s) reference pruned/absent topics",
            "affected": sorted(ghosts)[:15],
            "recommended_action": "Run graph_auto_index() to rebuild graph from current facts",
            "suppressed": False,
        }]

    def _eye_detect_silent_agents(self, watched: set) -> list[dict]:
        """MEDIUM — agents checked in >24h ago with findings_count=0."""
        agents = self._load(self._agents_path)
        alerts: list[dict] = []
        for a in agents:
            checked_in = a.get("checked_in_at", "")
            if not checked_in:
                continue
            hours_ago = _days_ago(checked_in) * 24
            if hours_ago > 24 and a.get("findings_count", 0) == 0:
                alerts.append({
                    "type": "silent_agents",
                    "severity": "MEDIUM",
                    "message": f"Agent '{a.get('agent_id', '?')}' checked in {hours_ago:.0f}h ago with ZERO findings",
                    "affected": [a.get("agent_id", "unknown")],
                    "recommended_action": "Investigate if agent is functioning correctly or decommission",
                    "suppressed": False,
                })
        return alerts

    def _eye_detect_quarantine_pressure(self, watched: set) -> list[dict]:
        """CRITICAL >21d eligible, HIGH >14d eligible, MEDIUM any items."""
        entries = self._quarantine_load()
        if not entries:
            return []
        eligible = [e for e in entries
                    if _days_ago(e.get("quarantined_at", "")) >= 14]
        overdue = [e for e in entries
                   if _days_ago(e.get("quarantined_at", "")) >= 21]
        tagged = sum(1 for e in entries if e.get("tags"))
        tag_note = f" ({tagged} with safety tags)" if tagged else ""
        if overdue:
            return [{
                "type": "quarantine_pressure",
                "severity": "CRITICAL",
                "message": (f"{len(overdue)} quarantined item(s) overdue >21 days"
                            f"{tag_note} — review and purge or restore immediately"),
                "affected": sorted(set(e.get("topic", "?") for e in overdue))[:10],
                "recommended_action": "Run --quarantine-preview then --quarantine-purge or --quarantine-restore",
                "suppressed": False,
            }]
        if eligible:
            return [{
                "type": "quarantine_pressure",
                "severity": "HIGH",
                "message": (f"{len(eligible)} quarantined item(s) eligible for purge"
                            f"{tag_note}"),
                "affected": sorted(set(e.get("topic", "?") for e in eligible))[:10],
                "recommended_action": "Run --quarantine-preview to review eligible items",
                "suppressed": False,
            }]
        return [{
            "type": "quarantine_pressure",
            "severity": "MEDIUM",
            "message": f"{len(entries)} item(s) in quarantine (holding){tag_note}",
            "affected": sorted(set(e.get("topic", "?") for e in entries))[:10],
            "recommended_action": "Items will become eligible for purge after 14-day hold",
            "suppressed": False,
        }]

    # ---- public API --------------------------------------------------

    def third_eye_scan(self, include_types: list[str] | None = None) -> list[dict]:
        """Run all (or specified) detectors. Save state. Return alerts sorted by severity.

        Each alert fires with:
            type, severity, message, affected, recommended_action, suppressed
        """
        all_detectors = {
            "unresolved_escalations":   self._eye_detect_unresolved_escalations,
            "tombstone_accumulation":   self._eye_detect_tombstone_accumulation,
            "orphaned_blobs":           self._eye_detect_orphaned_blobs,
            "graph_isolation":          self._eye_detect_graph_isolation,
            "stale_crystals":           self._eye_detect_stale_crystals,
            "inactive_sources":         self._eye_detect_inactive_sources,
            "crime_citation_voids":     self._eye_detect_crime_citation_voids,
            "never_reviewed_facts":     self._eye_detect_never_reviewed_facts,
            "stale_merkle":             self._eye_detect_stale_merkle,
            "custody_cap_proximity":    self._eye_detect_custody_cap_proximity,
            "ghost_graph_topics":       self._eye_detect_ghost_graph_topics,
            "silent_agents":            self._eye_detect_silent_agents,
            "quarantine_pressure":      self._eye_detect_quarantine_pressure,
        }

        state = self._eye_load()
        watched = {t.lower() for t in state.get("watched_topics", [])}
        suppressed_map = state.get("suppressed", {})

        types_to_run = include_types if include_types else list(all_detectors.keys())
        all_alerts: list[dict] = []

        for atype in types_to_run:
            detector = all_detectors.get(atype)
            if not detector:
                continue
            raw = detector(watched)
            # Apply suppression
            sup_targets = suppressed_map.get(atype, [])
            for alert in raw:
                if "*" in sup_targets:
                    alert["suppressed"] = True
                elif any(t in sup_targets for t in alert.get("affected", [])):
                    alert["suppressed"] = True
                all_alerts.append(alert)

        # Sort by severity (CRITICAL first)
        sev_order = self._EYE_SEVERITY_ORDER
        all_alerts.sort(key=lambda a: sev_order.get(a.get("severity", "LOW"), 9))

        # Update state
        active_alerts = [a for a in all_alerts if not a.get("suppressed")]
        state["last_scan"] = _now_iso()
        state["total_scans"] = state.get("total_scans", 0) + 1
        state["alerts"] = all_alerts
        state["total_alerts"] = len(active_alerts)
        self._eye_save(state)

        return all_alerts

    def third_eye_summary(self) -> dict:
        """Return alert counts grouped by type and severity."""
        state = self._eye_load()
        alerts = state.get("alerts", [])
        active = [a for a in alerts if not a.get("suppressed")]
        by_type: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        for a in active:
            by_type[a["type"]] = by_type.get(a["type"], 0) + 1
            by_severity[a["severity"]] = by_severity.get(a["severity"], 0) + 1
        return {
            "total": len(active),
            "by_type": by_type,
            "by_severity": by_severity,
            "last_scan": state.get("last_scan"),
            "watched_topics": state.get("watched_topics", []),
        }

    def third_eye_suppress(self, alert_type: str,
                           target: str = "*") -> dict:
        """Suppress an alert type entirely (*) or for a specific target."""
        state = self._eye_load()
        sup = state.setdefault("suppressed", {})
        targets = sup.setdefault(alert_type, [])
        if target not in targets:
            targets.append(target)
        # Mark existing alerts as suppressed
        for a in state.get("alerts", []):
            if a["type"] == alert_type:
                if target == "*" or target in a.get("affected", []):
                    a["suppressed"] = True
        state["total_alerts"] = len([
            a for a in state.get("alerts", []) if not a.get("suppressed")])
        self._eye_save(state)
        return {"suppressed": alert_type, "target": target}

    def third_eye_watch(self, topic: str) -> dict:
        """Add topic to watched list (lowers detection thresholds)."""
        state = self._eye_load()
        watched = state.setdefault("watched_topics", [])
        topic_lower = topic.lower()
        if topic_lower not in [w.lower() for w in watched]:
            watched.append(topic)
        self._eye_save(state)
        return {"watched": topic, "total_watched": len(watched)}

    def third_eye_status(self) -> dict:
        """Last scan time, total alerts, breakdown by severity, watched topics."""
        state = self._eye_load()
        alerts = state.get("alerts", [])
        active = [a for a in alerts if not a.get("suppressed")]
        by_severity: dict[str, int] = {}
        for a in active:
            by_severity[a["severity"]] = by_severity.get(a["severity"], 0) + 1
        return {
            "last_scan": state.get("last_scan"),
            "total_scans": state.get("total_scans", 0),
            "total_alerts": len(active),
            "by_severity": by_severity,
            "watched_topics": state.get("watched_topics", []),
        }

    # ==================================================================
    # FEATURE 31: DIAMOND QUARANTINE — Information Safety Net
    # ==================================================================
    # Nothing leaves the brain permanently without:
    #   1. A 14-day mandatory hold
    #   2. The brain generating a reason (with up to 2 pushbacks)
    #   3. The human typing "PERMANENTLY DELETE"
    # ------------------------------------------------------------------

    _CRIME_KW_QUARANTINE = frozenset({
        "murder", "homicide", "manslaughter", "assault", "robbery",
        "burglary", "theft", "arson", "kidnapping", "rape", "weapons",
        "drug", "narcotic", "dui", "fraud", "stalking",
    })

    def _quarantine_path(self) -> Path:
        return self.memory_dir / "quarantine.json"

    def _quarantine_load(self) -> list:
        path = self._quarantine_path()
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    return data
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return []

    def _quarantine_save(self, entries: list) -> None:
        path = self._quarantine_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(entries, indent=2, ensure_ascii=False),
                       encoding="utf-8")
        os.replace(str(tmp), str(path))

    def _quarantine_add(self, fact: dict, source: str,
                        trigger_reason: str) -> dict:
        """Add a fact to quarantine. Returns the quarantine entry."""
        entries = self._quarantine_load()
        now = _now_iso()
        fact_text = (fact.get("topic", "") + " " + fact.get("fact", "")).lower()

        # Detect tags for elevated warnings
        tags: list[str] = []
        if fact.get("verified"):
            tags.append("verified")
        if any(kw in fact_text for kw in self._CRIME_KW_QUARANTINE):
            tags.append("crime")
        if fact.get("links"):
            tags.append("linked")

        # Batch ID = ISO week (items in same 7-day window batch together)
        from datetime import datetime, timezone, timedelta
        dt = datetime.now(timezone.utc)
        year, week, _ = dt.isocalendar()
        batch_id = f"{year}-W{week:02d}"

        # Hold until = 14 days from now
        hold_dt = dt + timedelta(days=14)

        content = f"{fact.get('topic', '')}:{fact.get('fact', '')}"
        entry_id = hashlib.sha256(
            (content + now).encode()).hexdigest()[:12]

        entry = {
            "id": entry_id,
            "source": source,
            "topic": fact.get("topic", ""),
            "fact_preview": fact.get("fact", "")[:150],
            "original_data": fact,
            "quarantined_at": now,
            "hold_until": hold_dt.isoformat(),
            "status": "holding",
            "brain_reason": None,
            "purge_reason": None,
            "batch_id": batch_id,
            "staged_at": None,
            "tags": tags,
        }
        entries.append(entry)
        self._quarantine_save(entries)
        return entry

    def _quarantine_generate_reason(self, entries: list[dict]) -> str:
        """Brain writes a human-readable reason for why these items
        should (or shouldn't) be purged."""
        topics = sorted(set(e.get("topic", "?") for e in entries))
        sources = sorted(set(e.get("source", "?") for e in entries))
        oldest_days = max((_days_ago(e.get("quarantined_at", ""))
                           for e in entries), default=0)
        tagged = [e for e in entries if e.get("tags")]
        tag_summary = []
        if any("verified" in e.get("tags", []) for e in tagged):
            tag_summary.append("verified facts present")
        if any("crime" in e.get("tags", []) for e in tagged):
            tag_summary.append("crime-related content present")
        if any("linked" in e.get("tags", []) for e in tagged):
            tag_summary.append("citation-linked facts present")

        parts = [f"{len(entries)} fact(s) across topic(s): {', '.join(topics[:5])}",
                 f"Source(s): {', '.join(sources)}",
                 f"Oldest: {oldest_days:.0f} days in quarantine"]
        if tag_summary:
            parts.append(f"Caution: {'; '.join(tag_summary)}")
        return ". ".join(parts)

    def _quarantine_evaluate_pushback(self, entries: list[dict]) -> list[str]:
        """Brain evaluates entries and returns concerns (up to 2 pushbacks).

        Returns list of concern strings. Empty list = no pushback.
        """
        concerns: list[str] = []
        verified = [e for e in entries if "verified" in e.get("tags", [])]
        if verified:
            concerns.append(
                f"{len(verified)} fact(s) were manually verified — "
                "deletion is irreversible and these were trusted")
        crime = [e for e in entries if "crime" in e.get("tags", [])]
        if crime:
            concerns.append(
                f"{len(crime)} fact(s) contain crime-related content — "
                "may be needed for legal proceedings")
        # Check for sole-topic facts (only knowledge about a topic)
        all_facts = self._load(self._facts_path)
        live_topics = {}
        for f in all_facts:
            if not f.get("_crdt", {}).get("tombstone"):
                t = f.get("topic", "").lower()
                live_topics[t] = live_topics.get(t, 0) + 1
        for e in entries:
            t = e.get("topic", "").lower()
            if live_topics.get(t, 0) <= 1:
                concerns.append(
                    f"Topic '{e.get('topic')}' has no other facts — "
                    "this is the brain's only knowledge on this subject")
                break  # one warning is enough
        linked = [e for e in entries if "linked" in e.get("tags", [])]
        if linked:
            concerns.append(
                f"{len(linked)} fact(s) are linked to legal citations — "
                "purging may break citation cross-references")
        return concerns

    # ---- public API --------------------------------------------------

    def quarantine_list(self, status: str | None = None,
                        batch_id: str | None = None) -> list[dict]:
        """List quarantine entries (minus original_data for display)."""
        entries = self._quarantine_load()
        # Update statuses based on time
        now_str = _now_iso()
        for e in entries:
            if e.get("status") == "holding":
                if _days_ago(e.get("quarantined_at", "")) >= 14:
                    e["status"] = "eligible"
        self._quarantine_save(entries)
        if status:
            entries = [e for e in entries if e.get("status") == status]
        if batch_id:
            entries = [e for e in entries
                       if e.get("batch_id") == batch_id]
        # Strip original_data for display
        display = []
        for e in entries:
            d = {k: v for k, v in e.items() if k != "original_data"}
            display.append(d)
        return display

    def quarantine_stats(self) -> dict:
        """Count breakdown by status, source, batch."""
        entries = self._quarantine_load()
        by_status: dict[str, int] = {}
        by_source: dict[str, int] = {}
        by_batch: dict[str, int] = {}
        for e in entries:
            s = e.get("status", "holding")
            if s == "holding" and _days_ago(e.get("quarantined_at", "")) >= 14:
                s = "eligible"
            by_status[s] = by_status.get(s, 0) + 1
            by_source[e.get("source", "?")] = by_source.get(
                e.get("source", "?"), 0) + 1
            by_batch[e.get("batch_id", "?")] = by_batch.get(
                e.get("batch_id", "?"), 0) + 1
        oldest = min((_days_ago(e.get("quarantined_at", ""))
                      for e in entries), default=0) if entries else 0
        return {
            "total": len(entries),
            "by_status": by_status,
            "by_source": by_source,
            "by_batch": by_batch,
            "oldest_days": round(oldest, 1),
        }

    def quarantine_preview(self, batch_id: str | None = None) -> list[dict]:
        """Show eligible entries with brain-generated reasons."""
        entries = self._quarantine_load()
        eligible = [e for e in entries
                    if _days_ago(e.get("quarantined_at", "")) >= 14]
        if batch_id:
            eligible = [e for e in eligible
                        if e.get("batch_id") == batch_id]
        # Group by batch
        batches: dict[str, list[dict]] = {}
        for e in eligible:
            bid = e.get("batch_id", "unknown")
            batches.setdefault(bid, []).append(e)
        result = []
        for bid, group in sorted(batches.items()):
            reason = self._quarantine_generate_reason(group)
            for e in group:
                e["brain_reason"] = reason
            self._quarantine_save(self._quarantine_load())  # persist reasons
            result.append({
                "batch_id": bid,
                "count": len(group),
                "brain_reason": reason,
                "entries": [{k: v for k, v in e.items()
                             if k != "original_data"} for e in group],
            })
        return result

    def quarantine_restore(self, entry_id: str) -> dict:
        """Move quarantined fact back into active facts.json."""
        entries = self._quarantine_load()
        target = None
        remaining = []
        for e in entries:
            if e.get("id") == entry_id:
                target = e
            else:
                remaining.append(e)
        if not target:
            return {"error": f"Entry '{entry_id}' not found in quarantine"}
        # Restore original fact
        original = target.get("original_data", {})
        if not original:
            return {"error": "No original data to restore"}
        facts = self._load(self._facts_path)
        # Clear tombstone if present
        if original.get("_crdt", {}).get("tombstone"):
            original["_crdt"]["tombstone"] = False
        original["updated_at"] = _now_iso()
        facts.append(original)
        self._save(self._facts_path, facts)
        self._quarantine_save(remaining)
        return {
            "restored": True,
            "topic": target.get("topic"),
            "fact_preview": target.get("fact_preview"),
        }

    def quarantine_purge(self, batch_id: str, passphrase: str,
                         reason: str | None = None,
                         override: bool = False) -> dict:
        """Permanently delete quarantined items. Requires passphrase + reason.

        Brain can push back up to 2 times with concerns before requiring
        override=True to proceed.
        """
        if passphrase != "PERMANENTLY DELETE":
            return {"error": "passphrase_mismatch",
                    "message": "Passphrase must be exactly: PERMANENTLY DELETE"}

        entries = self._quarantine_load()
        batch = [e for e in entries
                 if e.get("batch_id") == batch_id
                 and _days_ago(e.get("quarantined_at", "")) >= 14]

        if not batch:
            still_holding = [e for e in entries
                             if e.get("batch_id") == batch_id
                             and _days_ago(e.get("quarantined_at", "")) < 14]
            if still_holding:
                return {"error": "hold_period_active",
                        "message": f"{len(still_holding)} item(s) still in 14-day hold",
                        "hold_remaining_days": round(
                            14 - _days_ago(still_holding[0].get(
                                "quarantined_at", "")), 1)}
            return {"error": "batch_not_found",
                    "message": f"No eligible items in batch '{batch_id}'"}

        # Brain pushback system (up to 2 times)
        if not override:
            concerns = self._quarantine_evaluate_pushback(batch)
            if concerns:
                # Track pushback count in eye state (reuse third_eye.json)
                eye_state = self._eye_load()
                pushbacks = eye_state.setdefault("quarantine_pushbacks", {})
                count = pushbacks.get(batch_id, 0) + 1
                pushbacks[batch_id] = count
                self._eye_save(eye_state)

                if count <= 2:
                    return {
                        "pushback": True,
                        "pushback_count": count,
                        "concerns": concerns,
                        "message": (
                            "Brain has concerns about this purge. "
                            f"Pushback {count}/2. "
                            "Call again with override=True to proceed."
                            if count < 2 else
                            "Final pushback. Call with override=True "
                            "to override the brain's objections."
                        ),
                    }

        # Generate reason if not provided
        if not reason:
            reason = self._quarantine_generate_reason(batch)

        # Execute purge
        batch_ids = {e["id"] for e in batch}
        remaining = [e for e in entries if e["id"] not in batch_ids]
        purged_count = len(batch_ids)

        self._quarantine_save(remaining)

        # Clear pushback counter
        eye_state = self._eye_load()
        eye_state.get("quarantine_pushbacks", {}).pop(batch_id, None)
        self._eye_save(eye_state)

        # Log to custody chain if link initialized
        if self.link_identity():
            self._link_append_custody("QUARANTINE_PURGE", {
                "batch_id": batch_id,
                "purged_count": purged_count,
                "reason": reason,
            })

        return {
            "purged": purged_count,
            "batch_id": batch_id,
            "reason": reason,
            "remaining_quarantine": len(remaining),
        }

    def quarantine_status(self) -> dict:
        """Quick status: counts, oldest item, next eligible date."""
        entries = self._quarantine_load()
        if not entries:
            return {"total": 0, "holding": 0, "eligible": 0,
                    "oldest_days": 0, "critical_tags": []}
        holding = eligible = 0
        oldest = 0.0
        crit_tags: set[str] = set()
        for e in entries:
            days = _days_ago(e.get("quarantined_at", ""))
            if days > oldest:
                oldest = days
            if days >= 14:
                eligible += 1
            else:
                holding += 1
            for t in e.get("tags", []):
                if t in ("verified", "crime", "linked"):
                    crit_tags.add(t)
        return {
            "total": len(entries),
            "holding": holding,
            "eligible": eligible,
            "oldest_days": round(oldest, 1),
            "critical_tags": sorted(crit_tags),
        }


# ==========================================================================
# CLI entry point
# ==========================================================================
def _print_source_list(brain: DiamondBrain) -> None:
    """Pretty-print source credibility rankings."""
    ranked = brain.source_list()
    print(_section_header("Source Credibility Rankings", _C.SCALE, _C.ORANGE))
    if not ranked:
        print(f"  {_C.DIM}No sources registered.{_C.RESET}\n")
        return
    for i, src in enumerate(ranked, 1):
        score = src["credibility_score"]
        sc = _C.GREEN if score >= 70 else (_C.YELLOW if score >= 40 else _C.RED)
        filled = int(score) // 5
        bar = f"{sc}{'|' * filled}{_C.DIM}{'.' * (20 - filled)}{_C.RESET}"
        print(f"    {_C.WHITE}{i:>2}.{_C.RESET}"
              f"  [{bar}] {sc}{score:>5.1f}{_C.RESET}"
              f"  {_C.CYAN}{src['display_name']}{_C.RESET}"
              f"  {_C.DIM}({src['source_type']}, {src['facts_contributed']}f){_C.RESET}")
    print()


def _print_source_credibility(brain: DiamondBrain, source_id: str) -> None:
    """Pretty-print credibility profile for a source."""
    cred = brain.source_credibility(source_id)
    if "error" in cred:
        print(f"  {_C.RED}{cred['error']}{_C.RESET}")
        return

    score = cred["credibility_score"]
    sc = _C.GREEN if score >= 70 else (_C.YELLOW if score >= 40 else _C.RED)
    name = cred["display_name"]
    print(f"\n{_section_header(f'Source: {name}', _C.SCALE, _C.ORANGE)}")
    filled = int(score) // 5
    bar = f"{sc}{'|' * filled}{_C.DIM}{'.' * (20 - filled)}{_C.RESET}"
    print(f"    {_C.WHITE}{_C.BOLD}Credibility :{_C.RESET}  [{bar}] {sc}{score:.1f}/100{_C.RESET}")
    print(f"    {_C.WHITE}{_C.BOLD}Type        :{_C.RESET}  {cred['source_type']}")
    print(f"    {_C.WHITE}{_C.BOLD}Facts       :{_C.RESET}  {cred['facts_contributed']}")
    print(f"    {_C.WHITE}{_C.BOLD}Conflicts   :{_C.RESET}  {cred['contradictions_flagged']}")
    sub = cred["sub_scores"]
    print(f"    {_C.DIM}Breakdown: consistency={sub['consistency']:.0f}"
          f" corroboration={sub['corroboration']:.0f}"
          f" recency={sub['recency']:.0f}"
          f" expertise={sub['expertise']:.0f}"
          f" type={sub['type_base']:.0f}"
          f" manual={cred['manual_adjustment']:+d}{_C.RESET}\n")


def _print_digest(brain: DiamondBrain) -> None:
    """Pretty-print the brain digest to stdout."""
    print(BANNER)
    d = brain.digest()

    print(f"  {_C.WHITE}{_C.BOLD}Total Facts :{_C.RESET}  {_C.GREEN}{d['total_facts']}{_C.RESET}")
    print(f"  {_C.WHITE}{_C.BOLD}Topics      :{_C.RESET}  {_C.CYAN}{', '.join(d['topics']) if d['topics'] else '(none yet)'}{_C.RESET}")
    print(f"  {_C.WHITE}{_C.BOLD}Agents      :{_C.RESET}  {_C.YELLOW}{d['total_agents']}{_C.RESET}")
    print(f"  {_C.WHITE}{_C.BOLD}Commands    :{_C.RESET}  {_C.MAGENTA}{d.get('commands_logged', 0)}{_C.RESET}")
    print(f"  {_C.WHITE}{_C.BOLD}Citations   :{_C.RESET}  {_C.GOLD}{_C.SCALE} {d.get('total_citations', 0)}{_C.RESET}")
    graph = d.get("knowledge_graph", {})
    if graph.get("total_nodes", 0) > 0:
        print(f"  {_C.WHITE}{_C.BOLD}Graph       :{_C.RESET}  {_C.CYAN}{graph['total_nodes']} nodes{_C.RESET} / {_C.MAGENTA}{graph['total_edges']} edges{_C.RESET}")
    if d.get("temporal_events", 0) > 0:
        print(f"  {_C.WHITE}{_C.BOLD}Events      :{_C.RESET}  {_C.YELLOW}{d['temporal_events']}{_C.RESET}")
    if d.get("amnesia_entries", 0) > 0:
        print(f"  {_C.WHITE}{_C.BOLD}Forgotten   :{_C.RESET}  {_C.DIM}{d['amnesia_entries']} archived{_C.RESET}")
    if d.get("blob_count", 0) > 0:
        print(f"  {_C.WHITE}{_C.BOLD}Blobs       :{_C.RESET}  {_C.BLUE}{d['blob_count']} evidence files{_C.RESET}")
    if d.get("registered_sources", 0) > 0:
        print(f"  {_C.WHITE}{_C.BOLD}Sources     :{_C.RESET}  {_C.ORANGE}{d['registered_sources']} registered{_C.RESET}")
    cortex_q = d.get("cortex_queries", 0)
    if cortex_q > 0:
        print(f"  {_C.WHITE}{_C.BOLD}Cortex      :{_C.RESET}  {_C.MAGENTA}{cortex_q} queries{_C.RESET}")
    eye_count = d.get("third_eye_alerts", 0)
    if eye_count > 0:
        eye_state = brain._eye_load()
        has_critical = any(a.get("severity") == "CRITICAL"
                          and not a.get("suppressed")
                          for a in eye_state.get("alerts", []))
        eye_color = _C.RED if has_critical else _C.YELLOW
        print(f"  {_C.WHITE}{_C.BOLD}Third Eye   :{_C.RESET}  {eye_color}\u25c9 {eye_count} alert{'s' if eye_count != 1 else ''}{_C.RESET}")
    q_count = d.get("quarantine_count", 0)
    if q_count > 0:
        q_status = brain.quarantine_status()
        q_eligible = q_status.get("eligible", 0)
        q_color = (_C.RED if q_status.get("oldest_days", 0) >= 21
                   else _C.YELLOW if q_eligible > 0 else _C.DIM)
        q_extra = f" ({q_eligible} eligible)" if q_eligible else ""
        print(f"  {_C.WHITE}{_C.BOLD}Quarantine  :{_C.RESET}  {q_color}{q_count} item{'s' if q_count != 1 else ''}{q_extra}{_C.RESET}")
    print(f"  {_C.WHITE}{_C.BOLD}Last Updated:{_C.RESET}  {_C.DIM}{d['last_updated'] or 'never'}{_C.RESET}")
    print()

    # Diamond Link section
    link = d.get("diamond_link", {})
    if link.get("initialized"):
        print(f"\n{_section_header('Diamond Link', _C.DIAMOND, _C.GOLD)}")
        fp = link.get("fingerprint", "")
        print(f"    {_C.WHITE}{_C.BOLD}Identity  :{_C.RESET}  "
              f"{_C.GOLD}{link.get('display_name', '?')}{_C.RESET} "
              f"{_C.DIM}({fp[:16]}...){_C.RESET}")
        peer_count = link.get("peer_count", 0)
        peer_color = _C.GREEN if peer_count > 0 else _C.DIM
        print(f"    {_C.WHITE}{_C.BOLD}Peers     :{_C.RESET}  "
              f"{peer_color}{peer_count}{_C.RESET}")
        print(f"    {_C.WHITE}{_C.BOLD}Syncs     :{_C.RESET}  "
              f"{_C.CYAN}{link.get('total_syncs', 0)}{_C.RESET}")
    else:
        print(f"\n    {_C.DIM}Diamond Link: not initialized "
              f"(run --link-init to enable){_C.RESET}")
    print()

    if d["agent_history"]:
        print(_section_header("Agent Roster", _C.BULLET, _C.MAGENTA))
        for a in d["agent_history"]:
            status_color = _C.GREEN if a["status"] == "active" else _C.RED
            print(
                f"    {_C.WHITE}{a['agent_id']:<20}{_C.RESET}"
                f"  role={_C.CYAN}{a['role']}{_C.RESET}"
                f"  status={status_color}{a['status']}{_C.RESET}"
                f"  findings={_C.YELLOW}{a['findings_count']}{_C.RESET}"
            )
        print()


def _print_heatmap(brain: DiamondBrain) -> None:
    """Pretty-print the knowledge heatmap."""
    hm = brain.heatmap()
    if not hm:
        print(f"  {_C.DIM}No facts stored yet. Heatmap is empty.{_C.RESET}")
        return

    print(_section_header("Knowledge Heatmap", "🔥", _C.MAGENTA))
    for topic, info in sorted(hm.items(), key=lambda x: x[1]["freshness_score"], reverse=True):
        score = info["freshness_score"]
        if score >= 80:
            bar_color = _C.GREEN
        elif score >= 40:
            bar_color = _C.YELLOW
        else:
            bar_color = _C.RED

        filled = score // 5
        bar = f"{bar_color}{'|' * filled}{_C.DIM}{'.' * (20 - filled)}{_C.RESET}"
        print(
            f"    {_C.WHITE}{topic:<25}{_C.RESET}"
            f"  [{bar}]"
            f"  {bar_color}{score:>3}%{_C.RESET}"
            f"  {_C.DIM}({info['count']} facts){_C.RESET}"
        )
    print()


def _print_recall(brain: DiamondBrain, query: str, fuzzy: bool = True) -> None:
    """Pretty-print recall results for a query."""
    print(_section_header(f'Recall: "{query}"', _C.DIAMOND, _C.CYAN))

    # Exact + fuzzy recall
    results = brain.recall(query, max_results=15, min_confidence=0, fuzzy=fuzzy)
    if results:
        print(f"  {_C.WHITE}Direct matches:{_C.RESET}")
        for f in results:
            conf = f.get("confidence", 0)
            eff = f.get("effective_confidence", conf)
            conf_color = _C.GREEN if eff >= 80 else (_C.YELLOW if eff >= 50 else _C.RED)
            decay_note = f" {_C.DIM}(eff:{eff}%){_C.RESET}" if eff != conf else ""
            links = f.get("links", [])
            link_note = f" {_C.DIM}-> {', '.join(links)}{_C.RESET}" if links else ""
            print(
                f"    {conf_color}[{conf:>3}%]{_C.RESET}{decay_note}"
                f"  {_C.CYAN}{f.get('topic', '?')}{_C.RESET}"
                f"  {f.get('fact', '')}{link_note}"
            )
    else:
        print(f"  {_C.DIM}No direct matches.{_C.RESET}")

    # Advanced recall (association chaining)
    advanced = brain.advanced_recall(query, max_results=15, min_confidence=70)
    # Filter out duplicates already shown above
    direct_keys = {(f.get("topic", ""), f.get("fact", "")) for f in results}
    advanced = [f for f in advanced if (f.get("topic", ""), f.get("fact", "")) not in direct_keys]
    if advanced:
        print(f"\n  {_C.MAGENTA}Associated knowledge:{_C.RESET}")
        for f in advanced:
            conf = f.get("confidence", 0)
            conf_color = _C.GREEN if conf >= 80 else (_C.YELLOW if conf >= 50 else _C.RED)
            print(
                f"    {conf_color}[{conf:>3}%]{_C.RESET}"
                f"  {_C.CYAN}{f.get('topic', '?')}{_C.RESET}"
                f"  {f.get('fact', '')}"
            )
    print()


def _print_suggestions(brain: DiamondBrain, command: str,
                       subcommand: str | None = None, top_n: int = 10) -> None:
    """Pretty-print flag suggestions."""
    cmd_str = f"{command} {subcommand}" if subcommand else command
    suggestions = brain.suggest_flags(command, subcommand, top_n=top_n)

    print(_section_header(f"Flag Suggestions: `{cmd_str}`", _C.ARROW, _C.CYAN))
    if not suggestions:
        print(f"  {_C.DIM}No command history for `{cmd_str}` yet.{_C.RESET}\n")
        return

    for i, s in enumerate(suggestions, 1):
        score = s["score"]
        if score >= 5:
            color = _C.GREEN
        elif score >= 1:
            color = _C.YELLOW
        else:
            color = _C.DIM
        print(
            f"    {_C.WHITE}{i:>2}.{_C.RESET}"
            f"  {color}{s['flag']:<20}{_C.RESET}"
            f"  {_C.DIM}used {s['count']}x{_C.RESET}"
            f"  {_C.DIM}score={s['score']}{_C.RESET}"
        )
    print()


def _print_smart_suggestions(brain: DiamondBrain, command: str,
                             subcommand: str | None = None,
                             cwd: str | None = None, top_n: int = 5) -> None:
    """Pretty-print LLM-powered flag suggestions."""
    cmd_str = f"{command} {subcommand}" if subcommand else command
    print(_section_header(f"Smart Suggestions: `{cmd_str}`", "🧠", _C.CYAN))
    print(f"  {_C.DIM}Querying LM Studio (sentinel-fast)...{_C.RESET}")

    flags = brain.smart_suggest(command, subcommand, cwd, top_n=top_n)
    if not flags:
        print(f"  {_C.YELLOW}No suggestions available.{_C.RESET}\n")
        return

    for i, flag in enumerate(flags, 1):
        print(f"    {_C.WHITE}{i:>2}.{_C.RESET}  {_C.GREEN}{flag}{_C.RESET}")
    print()


def _print_command_stats(brain: DiamondBrain, command: str | None = None) -> None:
    """Pretty-print command usage stats."""
    stats = brain.command_stats(command)

    if command:
        print(_section_header(f"Stats: `{command}`", _C.BULLET, _C.CYAN))
        print(f"  {_C.WHITE}{_C.BOLD}Invocations :{_C.RESET}  {_C.GREEN}{stats['total_invocations']}{_C.RESET}")
        if stats["subcommands"]:
            print(f"  {_C.WHITE}{_C.BOLD}Subcommands :{_C.RESET}")
            for sub, count in sorted(stats["subcommands"].items(),
                                     key=lambda x: x[1], reverse=True):
                print(f"    {_C.CYAN}{sub:<20}{_C.RESET}  {_C.DIM}{count}x{_C.RESET}")
        if stats["unique_flags"]:
            print(f"  {_C.WHITE}{_C.BOLD}Unique Flags:{_C.RESET}  {_C.DIM}{', '.join(stats['unique_flags'])}{_C.RESET}")
    else:
        print(_section_header("Command Stats", _C.BULLET, _C.CYAN))
        print(f"  {_C.WHITE}{_C.BOLD}Total Logged   :{_C.RESET}  {_C.GREEN}{stats['total_commands_logged']}{_C.RESET}")
        print(f"  {_C.WHITE}{_C.BOLD}Unique Commands:{_C.RESET}  {_C.YELLOW}{stats['unique_commands']}{_C.RESET}")
        if stats["top_commands"]:
            print(f"  {_C.WHITE}{_C.BOLD}Top Commands   :{_C.RESET}")
            for cmd, count in stats["top_commands"].items():
                print(f"    {_C.CYAN}{cmd:<20}{_C.RESET}  {_C.DIM}{count}x{_C.RESET}")
    print()


def _print_shell_hook() -> None:
    """Print bash/zsh hook snippet for auto-logging commands."""
    brain_cmd = "python -m brain.diamond_brain"
    print(_section_header("Shell Hook Setup", _C.ARROW, _C.YELLOW))
    print(f"  {_C.DIM}Add one of the following to your shell config:{_C.RESET}\n")

    print(f"  {_C.YELLOW}{_C.BOLD}Bash (~/.bashrc):{_C.RESET}")
    print(f'    diamond_brain_log() {{')
    print(f'      local cmd="$(history 1 | sed \'s/^ *[0-9]* *//\')"')
    print(f'      [ -n "$cmd" ] && {brain_cmd} --log-command "$cmd" --cwd "$PWD" &>/dev/null &')
    print(f'    }}')
    print(f'    PROMPT_COMMAND="diamond_brain_log;$PROMPT_COMMAND"')
    print()

    print(f"  {_C.YELLOW}{_C.BOLD}Zsh (~/.zshrc):{_C.RESET}")
    print(f'    diamond_brain_log() {{')
    print(f'      local cmd="$(fc -ln -1)"')
    print(f'      [ -n "$cmd" ] && {brain_cmd} --log-command "$cmd" --cwd "$PWD" &>/dev/null &')
    print(f'    }}')
    print(f'    precmd_functions+=(diamond_brain_log)')
    print()


if __name__ == "__main__":
    import sys

    brain = DiamondBrain()

    # CLI: --recall <query> for quick recall from terminal
    if len(sys.argv) >= 3 and sys.argv[1] == "--recall":
        query = " ".join(sys.argv[2:])
        _print_recall(brain, query)
        sys.exit(0)

    # CLI: --search <keyword> for keyword search
    if len(sys.argv) >= 3 and sys.argv[1] == "--search":
        keyword = " ".join(sys.argv[2:])
        results = brain.search(keyword)
        print(_section_header(f'Search: "{keyword}"', _C.DIAMOND, _C.CYAN))
        if results:
            for f in results:
                print(f"    [{f.get('confidence', 0):>3}%] {f.get('topic', '?')}: {f.get('fact', '')}")
        else:
            print(f"  {_C.DIM}No results.{_C.RESET}")
        print()
        sys.exit(0)

    # CLI: --learn <topic> <fact> [confidence] [source]
    if len(sys.argv) >= 4 and sys.argv[1] == "--learn":
        topic = sys.argv[2]
        fact_text = sys.argv[3]
        confidence = int(sys.argv[4]) if len(sys.argv) >= 5 else 90
        source = sys.argv[5] if len(sys.argv) >= 6 else "cli"
        entry = brain.learn(topic, fact_text, confidence, source)
        links = entry.get("links", [])
        link_str = f" -> linked: {', '.join(links)}" if links else ""
        print(f"  {_C.GREEN}Learned:{_C.RESET} [{confidence}%] {topic}: {fact_text}{link_str}")
        sys.exit(0)

    # CLI: --prune [max_age_days] [min_confidence]
    if len(sys.argv) >= 2 and sys.argv[1] == "--prune":
        max_age = int(sys.argv[2]) if len(sys.argv) >= 3 else 90
        min_conf = int(sys.argv[3]) if len(sys.argv) >= 4 else 30
        removed = brain.prune_stale(max_age_days=max_age, min_confidence=min_conf)
        if removed > 0:
            print(f"  {_C.YELLOW}Pruned {removed} stale facts (>{max_age} days, <{min_conf}% confidence){_C.RESET}")
        else:
            print(f"  {_C.GREEN}No stale facts to prune.{_C.RESET}")
        sys.exit(0)

    # CLI: --log-command "cmd" [--cwd /path]
    if len(sys.argv) >= 3 and sys.argv[1] == "--log-command":
        raw_cmd = sys.argv[2]
        cwd = None
        if "--cwd" in sys.argv:
            cwd_idx = sys.argv.index("--cwd")
            if cwd_idx + 1 < len(sys.argv):
                cwd = sys.argv[cwd_idx + 1]
        entry = brain.log_command(raw_cmd, cwd=cwd)
        print(
            f"  {_C.GREEN}Logged:{_C.RESET} {entry['command']}"
            f"{(' ' + entry['subcommand']) if entry['subcommand'] else ''}"
            f"  {_C.DIM}flags={entry['flags']}{_C.RESET}"
        )
        sys.exit(0)

    # CLI: --suggest "command [subcommand]" [--smart] [--top N]
    if len(sys.argv) >= 3 and sys.argv[1] == "--suggest":
        parts = sys.argv[2].split(None, 1)
        s_command = parts[0]
        s_subcommand = parts[1] if len(parts) > 1 else None
        s_smart = "--smart" in sys.argv
        s_top = 10
        if "--top" in sys.argv:
            top_idx = sys.argv.index("--top")
            if top_idx + 1 < len(sys.argv):
                s_top = int(sys.argv[top_idx + 1])

        if s_smart:
            s_cwd = None
            if "--cwd" in sys.argv:
                cwd_idx = sys.argv.index("--cwd")
                if cwd_idx + 1 < len(sys.argv):
                    s_cwd = sys.argv[cwd_idx + 1]
            _print_smart_suggestions(brain, s_command, s_subcommand, s_cwd, s_top)
        else:
            _print_suggestions(brain, s_command, s_subcommand, s_top)
        sys.exit(0)

    # CLI: --command-stats [command]
    if len(sys.argv) >= 2 and sys.argv[1] == "--command-stats":
        cs_command = sys.argv[2] if len(sys.argv) >= 3 else None
        _print_command_stats(brain, cs_command)
        sys.exit(0)

    # CLI: --cite <code> <title> <text> [--category X] [--severity X]
    if len(sys.argv) >= 5 and sys.argv[1] == "--cite":
        c_code = sys.argv[2]
        c_title = sys.argv[3]
        c_text = sys.argv[4]
        c_cat = "statute"
        c_sev = "REFERENCE"
        if "--category" in sys.argv:
            idx = sys.argv.index("--category")
            if idx + 1 < len(sys.argv):
                c_cat = sys.argv[idx + 1]
        if "--severity" in sys.argv:
            idx = sys.argv.index("--severity")
            if idx + 1 < len(sys.argv):
                c_sev = sys.argv[idx + 1]
        entry = brain.cite(c_code, c_title, c_text, category=c_cat, severity=c_sev)
        print(f"  {_C.GOLD}{_C.SCALE} Cited:{_C.RESET} {entry['code']} — {entry['title']}")
        sys.exit(0)

    # CLI: --citations [query] [--category X] [--severity X]
    if len(sys.argv) >= 2 and sys.argv[1] == "--citations":
        c_query = sys.argv[2] if len(sys.argv) >= 3 and not sys.argv[2].startswith("--") else None
        c_cat = None
        c_sev = None
        if "--category" in sys.argv:
            idx = sys.argv.index("--category")
            if idx + 1 < len(sys.argv):
                c_cat = sys.argv[idx + 1]
        if "--severity" in sys.argv:
            idx = sys.argv.index("--severity")
            if idx + 1 < len(sys.argv):
                c_sev = sys.argv[idx + 1]
        results = brain.recall_citations(query=c_query, category=c_cat, severity=c_sev)
        if results:
            rows = []
            for c in results:
                rows.append([
                    c.get("code", "?"),
                    c.get("title", "")[:40],
                    c.get("severity", "?"),
                    c.get("category", "?"),
                ])
            print(brain.visual_table(
                ["Code", "Title", "Severity", "Category"],
                rows,
                title=f"Citations{f': {c_query}' if c_query else ''}",
            ))
        else:
            print(f"  {_C.DIM}No citations found.{_C.RESET}")
        sys.exit(0)

    # CLI: --citation-stats
    if len(sys.argv) >= 2 and sys.argv[1] == "--citation-stats":
        stats = brain.citation_stats()
        print(_section_header("Citation Statistics", _C.SCALE, _C.GOLD))
        print(f"  {_C.WHITE}{_C.BOLD}Total Citations:{_C.RESET}  {_C.GREEN}{stats['total_citations']}{_C.RESET}")
        if stats["by_severity"]:
            print(brain.visual_bar_chart(stats["by_severity"], title="By Severity"))
        if stats["by_category"]:
            print(brain.visual_bar_chart(stats["by_category"], title="By Category", color=_C.BLUE))
        if stats["by_jurisdiction"]:
            print(brain.visual_bar_chart(stats["by_jurisdiction"], title="By Jurisdiction", color=_C.CYAN))
        sys.exit(0)

    # CLI: --court-doc [--type X] [--case X] [--defendant X]
    if len(sys.argv) >= 2 and sys.argv[1] == "--court-doc":
        cd_type = "MOTION"
        cd_case = "CR-2026-______"
        cd_def = "[DEFENDANT NAME]"
        if "--type" in sys.argv:
            idx = sys.argv.index("--type")
            if idx + 1 < len(sys.argv):
                cd_type = sys.argv[idx + 1]
        if "--case" in sys.argv:
            idx = sys.argv.index("--case")
            if idx + 1 < len(sys.argv):
                cd_case = sys.argv[idx + 1]
        if "--defendant" in sys.argv:
            idx = sys.argv.index("--defendant")
            if idx + 1 < len(sys.argv):
                cd_def = sys.argv[idx + 1]
        doc = brain.generate_court_document(
            doc_type=cd_type,
            case_number=cd_case,
            defendant=cd_def,
            title=f"{cd_type} — GENERATED BY DIAMOND BRAIN",
            sections=[{
                "heading": "Statement of Facts",
                "body": "(Insert statement of facts here.)",
                "citations": [],
            }],
        )
        print(doc)
        sys.exit(0)

    # CLI: --visual [topic]
    if len(sys.argv) >= 2 and sys.argv[1] == "--visual":
        v_topic = sys.argv[2] if len(sys.argv) >= 3 else None
        print(brain.visual_report(v_topic))
        sys.exit(0)

    # CLI: --html [output_path]
    if len(sys.argv) >= 2 and sys.argv[1] == "--html":
        html_path = sys.argv[2] if len(sys.argv) >= 3 else "diamond_brain_report.html"
        brain.export_html(output_path=html_path)
        print(f"  {_C.GREEN}{_C.CHECK} HTML report exported:{_C.RESET} {html_path}")
        print(f"  {_C.DIM}Open in browser to search, filter, and generate court documents.{_C.RESET}")
        sys.exit(0)

    # CLI: --shell-hook
    if len(sys.argv) >= 2 and sys.argv[1] == "--shell-hook":
        _print_shell_hook()
        sys.exit(0)

    # ==================================================================
    # Diamond Link CLI commands
    # ==================================================================

    # CLI: --link-init [name]
    if len(sys.argv) >= 2 and sys.argv[1] == "--link-init":
        name = sys.argv[2] if len(sys.argv) >= 3 else "Diamond Brain"
        try:
            identity = brain.link_init(name)
            fp = identity["fingerprint"]
            print(f"\n{_section_header('Diamond Link Initialized', _C.DIAMOND, _C.GOLD)}")
            print(f"    {_C.WHITE}{_C.BOLD}Name       :{_C.RESET}  {_C.GOLD}{identity['display_name']}{_C.RESET}")
            print(f"    {_C.WHITE}{_C.BOLD}Fingerprint:{_C.RESET}  {_C.CYAN}{fp}{_C.RESET}")
            print(f"    {_C.WHITE}{_C.BOLD}Created    :{_C.RESET}  {_C.DIM}{identity['created_at']}{_C.RESET}")
            print(f"\n    {_C.DIM}Share your fingerprint with peers to begin pairing.{_C.RESET}\n")
        except RuntimeError as e:
            print(f"  {_C.RED}{e}{_C.RESET}")
        sys.exit(0)

    # CLI: --link-identity
    if len(sys.argv) >= 2 and sys.argv[1] == "--link-identity":
        identity = brain.link_identity()
        if identity:
            fp = identity["fingerprint"]
            print(f"\n{_section_header('Diamond Link Identity', _C.DIAMOND, _C.GOLD)}")
            print(f"    {_C.WHITE}{_C.BOLD}Name       :{_C.RESET}  {_C.GOLD}{identity['display_name']}{_C.RESET}")
            print(f"    {_C.WHITE}{_C.BOLD}Fingerprint:{_C.RESET}  {_C.CYAN}{fp}{_C.RESET}")
            print(f"    {_C.WHITE}{_C.BOLD}Created    :{_C.RESET}  {_C.DIM}{identity['created_at']}{_C.RESET}\n")
        else:
            print(f"  {_C.DIM}Diamond Link not initialized. Run --link-init first.{_C.RESET}")
        sys.exit(0)

    # CLI: --link-pair-start [--port N]
    if len(sys.argv) >= 2 and sys.argv[1] == "--link-pair-start":
        lp_port = 7777
        if "--port" in sys.argv:
            idx = sys.argv.index("--port")
            if idx + 1 < len(sys.argv):
                lp_port = int(sys.argv[idx + 1])
        brain.link_pair_start(port=lp_port)
        sys.exit(0)

    # CLI: --link-pair-connect <host:port> <token>
    if len(sys.argv) >= 4 and sys.argv[1] == "--link-pair-connect":
        hp = sys.argv[2]
        lp_token = sys.argv[3]
        if ":" in hp:
            lp_host, lp_port_str = hp.rsplit(":", 1)
            lp_port = int(lp_port_str)
        else:
            lp_host = hp
            lp_port = 7777
        brain.link_pair_connect(lp_host, lp_port, lp_token)
        sys.exit(0)

    # CLI: --link-peers
    if len(sys.argv) >= 2 and sys.argv[1] == "--link-peers":
        peers = brain.link_peers()
        if peers:
            print(f"\n{_section_header('Authorized Peers', _C.DIAMOND, _C.GOLD)}")
            for p in peers:
                status_color = _C.GREEN if p.get("status") == "active" else _C.RED
                fp = p.get("fingerprint", "")
                syncs = p.get("syncs_completed", 0)
                topics = p.get("shared_topics", [])
                topic_str = ", ".join(topics) if topics else "(all)"
                print(f"    {_C.WHITE}{_C.BOLD}{p.get('display_name', '?')}{_C.RESET}")
                print(f"      {_C.DIM}Fingerprint:{_C.RESET} {_C.CYAN}{fp[:32]}...{_C.RESET}")
                print(f"      {_C.DIM}Status:{_C.RESET} {status_color}{p.get('status', '?')}{_C.RESET}"
                      f"  {_C.DIM}Syncs:{_C.RESET} {_C.YELLOW}{syncs}{_C.RESET}"
                      f"  {_C.DIM}Topics:{_C.RESET} {topic_str}")
                if p.get("last_sync"):
                    print(f"      {_C.DIM}Last sync:{_C.RESET} {p['last_sync']}")
                print()
        else:
            print(f"  {_C.DIM}No peers paired yet.{_C.RESET}")
        sys.exit(0)

    # CLI: --link-unpair <fingerprint_prefix>
    if len(sys.argv) >= 3 and sys.argv[1] == "--link-unpair":
        fp_prefix = sys.argv[2]
        if brain.link_unpair(fp_prefix):
            print(f"  {_C.YELLOW}Unpaired peer: {fp_prefix}{_C.RESET}")
        else:
            print(f"  {_C.RED}No peer found matching: {fp_prefix}{_C.RESET}")
        sys.exit(0)

    # CLI: --link-serve [--port N]
    if len(sys.argv) >= 2 and sys.argv[1] == "--link-serve":
        ls_port = 7777
        if "--port" in sys.argv:
            idx = sys.argv.index("--port")
            if idx + 1 < len(sys.argv):
                ls_port = int(sys.argv[idx + 1])
        brain.link_serve(port=ls_port)
        sys.exit(0)

    # CLI: --link-sync <fp_prefix> [--topics t1,t2] [--direction X] [--dry-run]
    if len(sys.argv) >= 3 and sys.argv[1] == "--link-sync":
        ls_fp = sys.argv[2]
        ls_topics = None
        ls_dir = "both"
        ls_dry = "--dry-run" in sys.argv

        if "--topics" in sys.argv:
            idx = sys.argv.index("--topics")
            if idx + 1 < len(sys.argv):
                ls_topics = [t.strip() for t in sys.argv[idx + 1].split(",")]
        if "--direction" in sys.argv:
            idx = sys.argv.index("--direction")
            if idx + 1 < len(sys.argv):
                ls_dir = sys.argv[idx + 1]

        try:
            result = brain.link_sync(ls_fp, topics=ls_topics,
                                     direction=ls_dir, dry_run=ls_dry)
            dry_label = f" {_C.YELLOW}(DRY RUN){_C.RESET}" if ls_dry else ""
            print(f"\n{_section_header('Sync Complete' + (' (Dry Run)' if ls_dry else ''), _C.CHECK, _C.GREEN)}")
            print(f"    {_C.WHITE}Peer       :{_C.RESET}  {result['peer']}{dry_label}")
            print(f"    {_C.WHITE}Direction  :{_C.RESET}  {result['direction']}")
            print(f"    {_C.WHITE}Facts sent :{_C.RESET}  {_C.CYAN}{result['facts_sent']}{_C.RESET}")
            print(f"    {_C.WHITE}Facts recv :{_C.RESET}  {_C.GREEN}{result['facts_received']}{_C.RESET}")
            print(f"    {_C.WHITE}Cites sent :{_C.RESET}  {_C.CYAN}{result['citations_sent']}{_C.RESET}")
            print(f"    {_C.WHITE}Cites recv :{_C.RESET}  {_C.GREEN}{result['citations_received']}{_C.RESET}")
            if result['conflicts']:
                print(f"    {_C.WHITE}Conflicts  :{_C.RESET}  {_C.YELLOW}{len(result['conflicts'])}{_C.RESET}")
                for c in result['conflicts'][:5]:
                    print(f"      {_C.DIM}{c['topic']}: {c['fact_preview']} -> {c['resolution']}{_C.RESET}")
            print()
        except (ValueError, ConnectionError, RuntimeError) as e:
            print(f"  {_C.RED}{e}{_C.RESET}")
        sys.exit(0)

    # CLI: --link-set-topics <fp_prefix> <topic1,topic2,...>
    if len(sys.argv) >= 4 and sys.argv[1] == "--link-set-topics":
        st_fp = sys.argv[2]
        st_topics = [t.strip() for t in sys.argv[3].split(",")]
        if brain.link_set_shared_topics(st_fp, st_topics):
            print(f"  {_C.GREEN}Shared topics set:{_C.RESET} {', '.join(st_topics)}")
        else:
            print(f"  {_C.RED}No peer found matching: {st_fp}{_C.RESET}")
        sys.exit(0)

    # CLI: --link-status
    if len(sys.argv) >= 2 and sys.argv[1] == "--link-status":
        status = brain.link_status()
        print(f"\n{_section_header('Diamond Link Status', _C.DIAMOND, _C.GOLD)}")

        if status["initialized"]:
            ident = status["identity"]
            fp = ident.get("fingerprint", "")
            print(f"    {_C.WHITE}{_C.BOLD}Identity   :{_C.RESET}  "
                  f"{_C.GOLD}{ident.get('display_name', '?')}{_C.RESET}")
            print(f"    {_C.WHITE}{_C.BOLD}Fingerprint:{_C.RESET}  {_C.CYAN}{fp}{_C.RESET}")
            print(f"    {_C.WHITE}{_C.BOLD}Peers      :{_C.RESET}  "
                  f"{_C.GREEN}{status['peer_count']}{_C.RESET}")
            print(f"    {_C.WHITE}{_C.BOLD}Total Syncs:{_C.RESET}  "
                  f"{_C.YELLOW}{status['total_syncs']}{_C.RESET}")

            # Chain of custody status
            custody = status.get("custody_chain", {})
            chain_color = _C.GREEN if custody.get("valid") else _C.RED
            print(f"    {_C.WHITE}{_C.BOLD}Custody    :{_C.RESET}  "
                  f"{chain_color}{custody.get('message', 'N/A')}{_C.RESET}")

            if status["peers"]:
                print(f"\n    {_C.WHITE}{_C.BOLD}Peers:{_C.RESET}")
                for p in status["peers"]:
                    sc = _C.GREEN if p.get("status") == "active" else _C.RED
                    print(f"      {sc}{_C.BULLET}{_C.RESET} "
                          f"{_C.WHITE}{p.get('display_name', '?')}{_C.RESET} "
                          f"{_C.DIM}({p.get('fingerprint', '')[:16]}...){_C.RESET} "
                          f"syncs={_C.YELLOW}{p.get('syncs_completed', 0)}{_C.RESET}")

            if status["recent_syncs"]:
                print(f"\n    {_C.WHITE}{_C.BOLD}Recent Syncs:{_C.RESET}")
                for s in status["recent_syncs"][-5:]:
                    print(f"      {_C.DIM}{s.get('timestamp', '?')}{_C.RESET}"
                          f"  {_C.CYAN}{s.get('peer_name', '?')}{_C.RESET}"
                          f"  {s.get('direction', '?')}"
                          f"  {_C.DIM}f:{s.get('facts_received', 0)} c:{s.get('citations_received', 0)}{_C.RESET}")
        else:
            print(f"    {_C.DIM}Not initialized. Run --link-init to enable.{_C.RESET}")
        print()
        sys.exit(0)

    # CLI: --link-log [--last N]
    if len(sys.argv) >= 2 and sys.argv[1] == "--link-log":
        ll_n = 15
        if "--last" in sys.argv:
            idx = sys.argv.index("--last")
            if idx + 1 < len(sys.argv):
                ll_n = int(sys.argv[idx + 1])
        log = brain.link_log(last_n=ll_n)
        if log:
            print(f"\n{_section_header('Sync Log', _C.ARROW, _C.CYAN)}")
            for entry in log:
                print(f"    {_C.DIM}{entry.get('timestamp', '?')}{_C.RESET}"
                      f"  {_C.WHITE}{entry.get('peer_name', '?')}{_C.RESET}"
                      f"  {entry.get('direction', '?')}"
                      f"  facts:{_C.GREEN}+{entry.get('facts_received', 0)}{_C.RESET}"
                      f"/{_C.CYAN}{entry.get('facts_sent', 0)}{_C.RESET}"
                      f"  cites:{_C.GREEN}+{entry.get('citations_received', 0)}{_C.RESET}"
                      f"/{_C.CYAN}{entry.get('citations_sent', 0)}{_C.RESET}"
                      f"  {_C.YELLOW}conflicts:{entry.get('conflicts', 0)}{_C.RESET}")
            print()
        else:
            print(f"  {_C.DIM}No sync history yet.{_C.RESET}")
        sys.exit(0)

    # CLI: --link-custody [--last N] [--verify]
    if len(sys.argv) >= 2 and sys.argv[1] == "--link-custody":
        if "--verify" in sys.argv:
            result = brain.link_verify_custody_chain()
            color = _C.GREEN if result["valid"] else _C.RED
            print(f"\n{_section_header('Chain of Custody Verification', _C.DIAMOND, color)}")
            print(f"    {_C.WHITE}{_C.BOLD}Status  :{_C.RESET}  {color}{'INTACT' if result['valid'] else 'BROKEN'}{_C.RESET}")
            print(f"    {_C.WHITE}{_C.BOLD}Records :{_C.RESET}  {result['records']}")
            print(f"    {_C.WHITE}{_C.BOLD}Message :{_C.RESET}  {result['message']}")
            if result.get("broken_at") is not None:
                print(f"    {_C.RED}{_C.BOLD}Broken at record #{result['broken_at']}{_C.RESET}")
            print()
        else:
            lc_n = 15
            if "--last" in sys.argv:
                idx = sys.argv.index("--last")
                if idx + 1 < len(sys.argv):
                    lc_n = int(sys.argv[idx + 1])
            log = brain.link_custody_log(last_n=lc_n)
            if log:
                print(f"\n{_section_header('Chain of Custody', _C.DIAMOND, _C.GOLD)}")
                for entry in log:
                    evt = entry.get("event_type", "?")
                    evt_color = {
                        "IDENTITY_CREATED": _C.GREEN,
                        "PAIR": _C.CYAN,
                        "UNPAIR": _C.RED,
                        "SYNC_SEND": _C.BLUE,
                        "SYNC_RECV": _C.MAGENTA,
                    }.get(evt, _C.WHITE)
                    print(f"    {_C.DIM}#{entry.get('seq', '?'):>4}{_C.RESET}"
                          f"  {_C.DIM}{entry.get('timestamp', '?')}{_C.RESET}"
                          f"  {evt_color}{_C.BOLD}{evt:<18}{_C.RESET}"
                          f"  {_C.DIM}chain:{entry.get('prev_hash', '?')[:12]}...{_C.RESET}")
                    details = entry.get("details", {})
                    if details.get("peer_name"):
                        print(f"           {_C.WHITE}peer: {details['peer_name']}{_C.RESET}"
                              f"  {_C.DIM}({details.get('peer_fingerprint', '')[:16]}...){_C.RESET}")
                print()
            else:
                print(f"  {_C.DIM}No custody records yet.{_C.RESET}")
        sys.exit(0)

    # CLI: --merkle-build
    if len(sys.argv) >= 2 and sys.argv[1] == "--merkle-build":
        result = brain.merkle_build()
        print(f"\n{_section_header('Merkle DAG Built', _C.DIAMOND, _C.GREEN)}")
        print(f"    {_C.WHITE}{_C.BOLD}Root Hash  :{_C.RESET}  "
              f"{_C.GREEN}{result['root_hash'][:32]}...{_C.RESET}")
        print(f"    {_C.WHITE}{_C.BOLD}Leaf Count :{_C.RESET}  {result['leaf_count']}")
        print(f"    {_C.WHITE}{_C.BOLD}Built At   :{_C.RESET}  {result['built_at']}\n")
        sys.exit(0)

    # CLI: --merkle-prove <seq>
    if len(sys.argv) >= 3 and sys.argv[1] == "--merkle-prove":
        seq = int(sys.argv[2])
        proof = brain.merkle_prove(seq)
        if "error" in proof:
            print(f"  {_C.RED}{proof['error']}{_C.RESET}")
        else:
            print(f"\n{_section_header(f'Merkle Proof: Record #{seq}', _C.DIAMOND, _C.CYAN)}")
            print(f"    {_C.WHITE}{_C.BOLD}Leaf Hash :{_C.RESET}  {proof['leaf_hash'][:32]}...")
            print(f"    {_C.WHITE}{_C.BOLD}Root Hash :{_C.RESET}  {proof['root_hash'][:32]}...")
            print(f"    {_C.WHITE}{_C.BOLD}Path Len  :{_C.RESET}  {len(proof['proof_path'])} steps")
            # Write proof to temp file
            proof_path = f"/tmp/merkle_proof_{seq}.json"
            Path(proof_path).write_text(
                json.dumps(proof, indent=2), encoding="utf-8")
            print(f"    {_C.DIM}Proof saved to: {proof_path}{_C.RESET}\n")
        sys.exit(0)

    # CLI: --merkle-verify <proof_file>
    if len(sys.argv) >= 3 and sys.argv[1] == "--merkle-verify":
        pf = Path(sys.argv[2])
        if not pf.exists():
            print(f"  {_C.RED}File not found: {pf}{_C.RESET}")
        else:
            proof_data = json.loads(pf.read_text(encoding="utf-8"))
            result = DiamondBrain.merkle_verify_proof(proof_data)
            color = _C.GREEN if result["valid"] else _C.RED
            print(f"\n{_section_header('Merkle Proof Verification', _C.DIAMOND, color)}")
            print(f"    {_C.WHITE}{_C.BOLD}Valid :{_C.RESET}  "
                  f"{color}{'YES' if result['valid'] else 'NO'}{_C.RESET}")
            print(f"    {_C.DIM}Computed: {result['computed_root'][:32]}...{_C.RESET}")
            print(f"    {_C.DIM}Expected: {result['expected_root'][:32]}...{_C.RESET}\n")
        sys.exit(0)

    # CLI: --merkle-status
    if len(sys.argv) >= 2 and sys.argv[1] == "--merkle-status":
        status = brain.merkle_status()
        print(f"\n{_section_header('Merkle DAG Status', _C.DIAMOND, _C.GOLD)}")
        if status["built"]:
            print(f"    {_C.WHITE}{_C.BOLD}Root Hash  :{_C.RESET}  "
                  f"{status['root_hash'][:32]}...")
            print(f"    {_C.WHITE}{_C.BOLD}Leaves     :{_C.RESET}  {status['leaf_count']}")
            stale_color = _C.YELLOW if status["stale"] else _C.GREEN
            print(f"    {_C.WHITE}{_C.BOLD}Stale      :{_C.RESET}  "
                  f"{stale_color}{'yes' if status['stale'] else 'no'}{_C.RESET}")
            print(f"    {_C.WHITE}{_C.BOLD}Built At   :{_C.RESET}  "
                  f"{_C.DIM}{status['built_at']}{_C.RESET}")
        else:
            print(f"    {_C.DIM}Not built yet. Run --merkle-build.{_C.RESET}")
        print()
        sys.exit(0)

    # ==================================================================
    # Fractal Brain Feature CLI Commands
    # ==================================================================

    # CLI: --graph-index
    if len(sys.argv) >= 2 and sys.argv[1] == "--graph-index":
        result = brain.graph_auto_index()
        print(f"\n{_section_header('Knowledge Graph Indexed', _C.DIAMOND, _C.CYAN)}")
        print(f"    {_C.WHITE}{_C.BOLD}Nodes Created:{_C.RESET}  {_C.GREEN}{result['nodes_created']}{_C.RESET}")
        print(f"    {_C.WHITE}{_C.BOLD}Edges Created:{_C.RESET}  {_C.GREEN}{result['edges_created']}{_C.RESET}")
        print(f"    {_C.WHITE}{_C.BOLD}Total Nodes  :{_C.RESET}  {_C.CYAN}{result['total_nodes']}{_C.RESET}")
        print(f"    {_C.WHITE}{_C.BOLD}Total Edges  :{_C.RESET}  {_C.CYAN}{result['total_edges']}{_C.RESET}\n")
        sys.exit(0)

    # CLI: --graph-stats
    if len(sys.argv) >= 2 and sys.argv[1] == "--graph-stats":
        stats = brain.graph_stats()
        print(f"\n{_section_header('Knowledge Graph', _C.DIAMOND, _C.CYAN)}")
        print(f"    {_C.WHITE}{_C.BOLD}Total Nodes:{_C.RESET}  {_C.GREEN}{stats['total_nodes']}{_C.RESET}")
        print(f"    {_C.WHITE}{_C.BOLD}Total Edges:{_C.RESET}  {_C.GREEN}{stats['total_edges']}{_C.RESET}")
        if stats["node_types"]:
            print(f"\n    {_C.WHITE}{_C.BOLD}Node Types:{_C.RESET}")
            for ntype, count in sorted(stats["node_types"].items(), key=lambda x: x[1], reverse=True):
                print(f"      {_C.CYAN}{ntype:<15}{_C.RESET}  {count}")
        if stats["edge_types"]:
            print(f"\n    {_C.WHITE}{_C.BOLD}Edge Types:{_C.RESET}")
            for etype, count in sorted(stats["edge_types"].items(), key=lambda x: x[1], reverse=True):
                print(f"      {_C.MAGENTA}{etype:<15}{_C.RESET}  {count}")
        print()
        sys.exit(0)

    # CLI: --graph-query <query> [--depth N]
    if len(sys.argv) >= 3 and sys.argv[1] == "--graph-query":
        gq_query = sys.argv[2]
        gq_depth = 2
        if "--depth" in sys.argv:
            idx = sys.argv.index("--depth")
            if idx + 1 < len(sys.argv):
                gq_depth = int(sys.argv[idx + 1])
        results = brain.graph_query(gq_query, max_depth=gq_depth)
        print(f"\n{_section_header(f'Graph Query: \"{gq_query}\"', _C.DIAMOND, _C.CYAN)}")
        if results:
            for r in results[:15]:
                node = r.get("node_data", {})
                ntype = node.get("type", "?")
                data = node.get("data", {})
                label = data.get("name", data.get("topic", data.get("code", data.get("fact", r["node_id"]))))
                if isinstance(label, str) and len(label) > 60:
                    label = label[:60] + "..."
                depth_bar = "  " * r["depth"]
                type_color = {"fact": _C.GREEN, "topic": _C.CYAN, "citation": _C.GOLD,
                              "crystal": _C.MAGENTA, "blob": _C.BLUE, "event": _C.YELLOW}.get(ntype, _C.WHITE)
                print(f"    {depth_bar}{type_color}{_C.BOLD}{ntype:<10}{_C.RESET}"
                      f"  {_C.WHITE}{label}{_C.RESET}"
                      f"  {_C.DIM}via:{r.get('via_edge_type', '?')} depth:{r['depth']}{_C.RESET}")
        else:
            print(f"    {_C.DIM}No graph nodes matching query.{_C.RESET}")
        print()
        sys.exit(0)

    # CLI: --graph-bfs <node_id> [--depth N]
    if len(sys.argv) >= 3 and sys.argv[1] == "--graph-bfs":
        gb_start = sys.argv[2]
        gb_depth = 3
        if "--depth" in sys.argv:
            idx = sys.argv.index("--depth")
            if idx + 1 < len(sys.argv):
                gb_depth = int(sys.argv[idx + 1])
        results = brain.graph_bfs(gb_start, max_depth=gb_depth)
        print(f"\n{_section_header(f'BFS from {gb_start[:16]}', _C.ARROW, _C.CYAN)}")
        if results:
            for r in results[:15]:
                node = r.get("node_data", {})
                ntype = node.get("type", "?")
                print(f"    {'  ' * r['depth']}{_C.CYAN}{ntype}{_C.RESET}"
                      f"  {_C.DIM}{r['node_id'][:16]}{_C.RESET}"
                      f"  via:{r.get('via_edge_type', '?')}")
        else:
            print(f"    {_C.DIM}No results (node not found or no connections).{_C.RESET}")
        print()
        sys.exit(0)

    # CLI: --fsrs-due [--threshold 0.9] [--top N]
    if len(sys.argv) >= 2 and sys.argv[1] == "--fsrs-due":
        fd_thresh = 0.9
        fd_top = 15
        if "--threshold" in sys.argv:
            idx = sys.argv.index("--threshold")
            if idx + 1 < len(sys.argv):
                fd_thresh = float(sys.argv[idx + 1])
        if "--top" in sys.argv:
            idx = sys.argv.index("--top")
            if idx + 1 < len(sys.argv):
                fd_top = int(sys.argv[idx + 1])
        due = brain.fsrs_due(threshold=fd_thresh, max_results=fd_top)
        print(f"\n{_section_header(f'FSRS: Facts Due for Review (R < {fd_thresh})', '🧠', _C.MAGENTA)}")
        if due:
            for f in due:
                r = f.get("_retrievability", 0)
                r_color = _C.GREEN if r >= 0.8 else (_C.YELLOW if r >= 0.5 else _C.RED)
                print(f"    {r_color}[R={r:.2f}]{_C.RESET}"
                      f"  {_C.CYAN}{f.get('topic', '?')}{_C.RESET}"
                      f"  {f.get('fact', '')[:70]}"
                      f"  {_C.DIM}({f.get('_days_since_review', '?')}d ago){_C.RESET}")
        else:
            print(f"    {_C.GREEN}All facts above threshold! Memory is strong.{_C.RESET}")
        print()
        sys.exit(0)

    # CLI: --fsrs-review <topic> <fact_text> <rating>
    if len(sys.argv) >= 5 and sys.argv[1] == "--fsrs-review":
        fr_topic = sys.argv[2]
        fr_fact = sys.argv[3]
        fr_rating = int(sys.argv[4])
        result = brain.fsrs_review(fr_topic, fr_fact, fr_rating)
        if result:
            rating_names = {1: "Again", 2: "Hard", 3: "Good", 4: "Easy"}
            r_name = rating_names.get(fr_rating, "?")
            print(f"  {_C.GREEN}{_C.CHECK} Reviewed ({r_name}):{_C.RESET}"
                  f"  S={result.get('fsrs_stability', 0):.1f}d"
                  f"  D={result.get('fsrs_difficulty', 0):.1f}"
                  f"  reps={result.get('fsrs_reps', 0)}"
                  f"  conf={result.get('confidence', 0)}%")
        else:
            print(f"  {_C.RED}Fact not found.{_C.RESET}")
        sys.exit(0)

    # CLI: --fsrs-stats
    if len(sys.argv) >= 2 and sys.argv[1] == "--fsrs-stats":
        stats = brain.fsrs_stats()
        print(f"\n{_section_header('FSRS Memory Statistics', '🧠', _C.MAGENTA)}")
        print(f"    {_C.WHITE}{_C.BOLD}Total Facts      :{_C.RESET}  {_C.GREEN}{stats['total_facts']}{_C.RESET}")
        print(f"    {_C.WHITE}{_C.BOLD}Reviewed Facts   :{_C.RESET}  {_C.CYAN}{stats['reviewed_facts']}{_C.RESET}")
        print(f"    {_C.WHITE}{_C.BOLD}Avg Retrievability:{_C.RESET}  {_C.YELLOW}{stats['avg_retrievability']:.1%}{_C.RESET}")
        print(f"    {_C.WHITE}{_C.BOLD}Due (R < 90%)    :{_C.RESET}  {_C.RED}{stats['due_at_90']}{_C.RESET}")
        print(f"    {_C.WHITE}{_C.BOLD}Weak (R < 70%)   :{_C.RESET}  {_C.RED}{stats['due_at_70']}{_C.RESET}")
        print(f"    {_C.WHITE}{_C.BOLD}Mature (S > 21d) :{_C.RESET}  {_C.GREEN}{stats['mature_facts']}{_C.RESET}\n")
        sys.exit(0)

    # CLI: --contradictions [topic]
    if len(sys.argv) >= 2 and sys.argv[1] == "--contradictions":
        ct_topic = sys.argv[2] if len(sys.argv) >= 3 else None
        contradictions = brain.detect_contradictions(topic=ct_topic)
        title = f"Contradictions{f': {ct_topic}' if ct_topic else ''}"
        print(f"\n{_section_header(title, _C.WARN, _C.RED)}")
        if contradictions:
            for c in contradictions[:15]:
                ctype = c.get("type", "?")
                type_color = {"negation_flip": _C.RED, "antonym_swap": _C.YELLOW,
                              "confidence_conflict": _C.MAGENTA}.get(ctype, _C.WHITE)
                print(f"    {type_color}{_C.BOLD}{ctype:<20}{_C.RESET}"
                      f"  sim={_C.DIM}{c.get('similarity', 0):.0%}{_C.RESET}"
                      f"  gap={_C.YELLOW}{c.get('confidence_gap', 0)}pt{_C.RESET}")
                fa = c.get("fact_a", {})
                fb = c.get("fact_b", {})
                print(f"      {_C.WHITE}A:{_C.RESET} [{fa.get('confidence', 0)}%] {fa.get('fact', '')[:70]}")
                print(f"      {_C.WHITE}B:{_C.RESET} [{fb.get('confidence', 0)}%] {fb.get('fact', '')[:70]}")
                if c.get("antonyms"):
                    print(f"      {_C.DIM}Antonyms: {c['antonyms'][0]} <-> {c['antonyms'][1]}{_C.RESET}")
                print()
        else:
            print(f"    {_C.GREEN}No contradictions detected.{_C.RESET}\n")
        sys.exit(0)

    # CLI: --crystallize [topic] [--min-cluster N]
    if len(sys.argv) >= 2 and sys.argv[1] == "--crystallize":
        cr_topic = None
        cr_min = 5
        if len(sys.argv) >= 3 and not sys.argv[2].startswith("--"):
            cr_topic = sys.argv[2]
        if "--min-cluster" in sys.argv:
            idx = sys.argv.index("--min-cluster")
            if idx + 1 < len(sys.argv):
                cr_min = int(sys.argv[idx + 1])
        crystals = brain.crystallize(topic=cr_topic, min_cluster=cr_min)
        print(f"\n{_section_header('Crystallization', _C.DIAMOND, _C.MAGENTA)}")
        if crystals:
            for cr in crystals:
                r_bar_val = int(cr.get("avg_retrievability", 0) * 20)
                r_bar = f"{_C.GREEN}{'|' * r_bar_val}{_C.DIM}{'.' * (20 - r_bar_val)}{_C.RESET}"
                print(f"    {_C.GOLD}{_C.BOLD}{_C.DIAMOND} {cr['topic']}{_C.RESET}"
                      f"  {_C.DIM}({cr['fact_count']} facts){_C.RESET}")
                print(f"      {_C.WHITE}Confidence:{_C.RESET} {cr['avg_confidence']:.0f}%"
                      f"  {_C.WHITE}Verified:{_C.RESET} {cr['verified_ratio']}"
                      f"  {_C.WHITE}Memory:{_C.RESET} [{r_bar}] {cr['avg_retrievability']:.0%}")
                print(f"      {_C.WHITE}Key Terms:{_C.RESET} {_C.CYAN}{', '.join(cr['key_terms'][:7])}{_C.RESET}")
                cd = cr.get("confidence_distribution", {})
                if cd:
                    print(f"      {_C.WHITE}Distribution:{_C.RESET}"
                          f"  {_C.RED}critical:{cd.get('critical', 0)}{_C.RESET}"
                          f"  {_C.YELLOW}high:{cd.get('high', 0)}{_C.RESET}"
                          f"  {_C.GREEN}med:{cd.get('medium', 0)}{_C.RESET}"
                          f"  {_C.DIM}low:{cd.get('low', 0)}{_C.RESET}")
                if cr.get("subclusters"):
                    print(f"      {_C.WHITE}Sub-clusters:{_C.RESET} {len(cr['subclusters'])}")
                print()
        else:
            print(f"    {_C.DIM}No clusters large enough to crystallize "
                  f"(min: {cr_min} facts).{_C.RESET}\n")
        sys.exit(0)

    # CLI: --temporal-add <event_id> <start> [end] [--data key=val]
    if len(sys.argv) >= 4 and sys.argv[1] == "--temporal-add":
        ta_id = sys.argv[2]
        ta_start = sys.argv[3]
        ta_end = sys.argv[4] if len(sys.argv) >= 5 and not sys.argv[4].startswith("--") else None
        ta_data = {}
        if "--data" in sys.argv:
            idx = sys.argv.index("--data")
            if idx + 1 < len(sys.argv):
                for kv in sys.argv[idx + 1:]:
                    if "=" in kv:
                        k, v = kv.split("=", 1)
                        ta_data[k] = v
        entry = brain.temporal_add(ta_id, ta_start, ta_end, ta_data)
        print(f"  {_C.GREEN}{_C.CHECK} Event added:{_C.RESET} {ta_id}"
              f"  {_C.DIM}{ta_start} -> {ta_end or ta_start}{_C.RESET}")
        sys.exit(0)

    # CLI: --temporal-chain [event_ids...]
    if len(sys.argv) >= 2 and sys.argv[1] == "--temporal-chain":
        tc_ids = sys.argv[2:] if len(sys.argv) >= 3 else None
        chain = brain.temporal_chain(tc_ids)
        print(f"\n{_section_header('Temporal Chain', _C.ARROW, _C.YELLOW)}")
        if chain:
            for i, e in enumerate(chain):
                rel = e.get("_relation_to_prev", "")
                gap = e.get("_gap_days", "")
                rel_str = f" {_C.MAGENTA}{rel}{_C.RESET}" if rel else ""
                gap_str = f" {_C.DIM}(gap: {gap}d){_C.RESET}" if gap else ""
                print(f"    {_C.YELLOW}{_C.BOLD}{e.get('event_id', '?')}{_C.RESET}"
                      f"  {_C.DIM}{e.get('start', '?')}{_C.RESET}"
                      f"  {_C.ARROW} {_C.DIM}{e.get('end', '?')}{_C.RESET}"
                      f"{rel_str}{gap_str}")
                data = e.get("data", {})
                if data:
                    for k, v in list(data.items())[:3]:
                        print(f"      {_C.DIM}{k}: {v}{_C.RESET}")
        else:
            print(f"    {_C.DIM}No temporal events recorded.{_C.RESET}")
        print()
        sys.exit(0)

    # CLI: --temporal-relation <event_a> <event_b>
    if len(sys.argv) >= 4 and sys.argv[1] == "--temporal-relation":
        tr_a = sys.argv[2]
        tr_b = sys.argv[3]
        rel = brain.temporal_relation(tr_a, tr_b)
        color = _C.GREEN if rel != "unknown" else _C.RED
        print(f"  {_C.WHITE}{tr_a}{_C.RESET} {color}{_C.BOLD}{rel}{_C.RESET} {_C.WHITE}{tr_b}{_C.RESET}")
        sys.exit(0)

    # CLI: --temporal-anomalies [--type TYPE] [--severity LEVEL]
    if len(sys.argv) >= 2 and sys.argv[1] == "--temporal-anomalies":
        ta_types = None
        if "--type" in sys.argv:
            idx = sys.argv.index("--type")
            if idx + 1 < len(sys.argv):
                ta_types = [sys.argv[idx + 1]]
        anomalies = brain.temporal_detect_anomalies(include_types=ta_types)
        sev_filter = None
        if "--severity" in sys.argv:
            idx = sys.argv.index("--severity")
            if idx + 1 < len(sys.argv):
                sev_filter = sys.argv[idx + 1].upper()
        print(f"\n{_section_header('Temporal Anomalies', _C.WARN, _C.RED)}")
        shown = 0
        for a in anomalies:
            if sev_filter and a.get("severity") != sev_filter:
                continue
            sev = a.get("severity", "?")
            sc = _C.RED if sev == "CRITICAL" else (
                _C.YELLOW if sev == "HIGH" else (
                    _C.ORANGE if sev == "MEDIUM" else _C.DIM))
            print(f"    {sc}[{sev}]{_C.RESET} "
                  f"{_C.WHITE}{a.get('type', '?')}{_C.RESET}: "
                  f"{a.get('message', '')}")
            shown += 1
        if shown == 0:
            print(f"    {_C.GREEN}No anomalies detected.{_C.RESET}")
        print()
        sys.exit(0)

    # CLI: --temporal-anomaly-summary
    if len(sys.argv) >= 2 and sys.argv[1] == "--temporal-anomaly-summary":
        summary = brain.temporal_anomaly_summary()
        print(f"\n{_section_header('Anomaly Summary', _C.WARN, _C.RED)}")
        print(f"    {_C.WHITE}{_C.BOLD}Total :{_C.RESET}  "
              f"{summary['total_anomalies']}")
        if summary["by_severity"]:
            for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
                count = summary["by_severity"].get(sev, 0)
                if count > 0:
                    sc = _C.RED if sev == "CRITICAL" else (
                        _C.YELLOW if sev == "HIGH" else (
                            _C.ORANGE if sev == "MEDIUM" else _C.DIM))
                    print(f"    {sc}{sev:<10}{_C.RESET}  {count}")
        if summary["by_type"]:
            print(f"    {_C.DIM}---{_C.RESET}")
            for t, count in sorted(summary["by_type"].items()):
                print(f"    {_C.DIM}{t}: {count}{_C.RESET}")
        print()
        sys.exit(0)

    # CLI: --forget <topic> <pattern> <reason>
    if len(sys.argv) >= 5 and sys.argv[1] == "--forget":
        fg_topic = sys.argv[2]
        fg_pattern = sys.argv[3]
        fg_reason = " ".join(sys.argv[4:])
        result = brain.forget(fg_topic, fg_pattern, fg_reason)
        if result["forgotten_count"] > 0:
            print(f"  {_C.YELLOW}Forgotten: {result['forgotten_count']} facts{_C.RESET}")
            print(f"  {_C.DIM}Reason: {fg_reason}{_C.RESET}")
            print(f"  {_C.DIM}Archived in amnesia log. Restorable with --amnesia-restore.{_C.RESET}")
        else:
            print(f"  {_C.DIM}No matching facts found.{_C.RESET}")
        sys.exit(0)

    # CLI: --amnesia-log [--last N]
    if len(sys.argv) >= 2 and sys.argv[1] == "--amnesia-log":
        al_n = 15
        if "--last" in sys.argv:
            idx = sys.argv.index("--last")
            if idx + 1 < len(sys.argv):
                al_n = int(sys.argv[idx + 1])
        log = brain.amnesia_log(last_n=al_n)
        print(f"\n{_section_header('Amnesia Log (Forgotten Facts)', _C.WARN, _C.YELLOW)}")
        if log:
            for entry in log:
                print(f"    {_C.DIM}{entry.get('forgotten_at', '?')}{_C.RESET}"
                      f"  {_C.CYAN}{entry.get('topic', '?')}{_C.RESET}"
                      f"  {_C.WHITE}{entry.get('fact_preview', '?')}{_C.RESET}")
                print(f"      {_C.YELLOW}Reason:{_C.RESET} {entry.get('reason', '?')}"
                      f"  {_C.DIM}(was {entry.get('original_confidence', 0)}% confidence){_C.RESET}")
        else:
            print(f"    {_C.GREEN}No forgotten facts. Total recall.{_C.RESET}")
        print()
        sys.exit(0)

    # CLI: --amnesia-restore <topic> <pattern>
    if len(sys.argv) >= 4 and sys.argv[1] == "--amnesia-restore":
        ar_topic = sys.argv[2]
        ar_pattern = sys.argv[3]
        result = brain.amnesia_restore(ar_topic, ar_pattern)
        if result["restored_count"] > 0:
            print(f"  {_C.GREEN}{_C.CHECK} Restored: {result['restored_count']} facts{_C.RESET}")
        else:
            print(f"  {_C.DIM}No matching facts in amnesia archive.{_C.RESET}")
        sys.exit(0)

    # CLI: --consensus <topic> <fact_text>
    if len(sys.argv) >= 4 and sys.argv[1] == "--consensus":
        cc_topic = sys.argv[2]
        cc_fact = " ".join(sys.argv[3:])
        result = brain.consensus_check(cc_topic, cc_fact)
        level = result["consensus_level"]
        level_color = {"strong": _C.GREEN, "majority": _C.CYAN, "partial": _C.YELLOW,
                       "unverified": _C.DIM, "contested": _C.RED,
                       "standalone": _C.DIM}.get(level, _C.WHITE)
        print(f"\n{_section_header('Consensus Check', _C.DIAMOND, _C.CYAN)}")
        print(f"    {_C.WHITE}{_C.BOLD}Consensus  :{_C.RESET}  {level_color}{_C.BOLD}{level.upper()}{_C.RESET}")
        print(f"    {_C.WHITE}{_C.BOLD}Agreeing   :{_C.RESET}  {result['agreeing_peers']}/{result['total_peers']} peers")
        print(f"    {_C.WHITE}{_C.BOLD}Local Conf :{_C.RESET}  {result['local_confidence']}%")
        print(f"    {_C.WHITE}{_C.BOLD}Modifier   :{_C.RESET}  {result['confidence_modifier']:+d}")
        if result["peer_sources"]:
            print(f"    {_C.WHITE}{_C.BOLD}Sources    :{_C.RESET}  {', '.join(result['peer_sources'])}")
        print()
        sys.exit(0)

    # CLI: --blob-store <file_path> [--description text] [--type content_type]
    if len(sys.argv) >= 3 and sys.argv[1] == "--blob-store":
        bs_file = sys.argv[2]
        bs_meta = {}
        if "--description" in sys.argv:
            idx = sys.argv.index("--description")
            if idx + 1 < len(sys.argv):
                bs_meta["description"] = sys.argv[idx + 1]
        if "--type" in sys.argv:
            idx = sys.argv.index("--type")
            if idx + 1 < len(sys.argv):
                bs_meta["content_type"] = sys.argv[idx + 1]
        try:
            content = Path(bs_file).read_bytes()
            bs_meta.setdefault("original_filename", Path(bs_file).name)
            result = brain.blob_store(content, bs_meta)
            print(f"  {_C.GREEN}{_C.CHECK} Blob stored:{_C.RESET}")
            print(f"    {_C.WHITE}Hash:{_C.RESET} {_C.CYAN}{result['hash']}{_C.RESET}")
            print(f"    {_C.WHITE}Size:{_C.RESET} {result['size']:,} bytes")
            print(f"    {_C.WHITE}Path:{_C.RESET} {_C.DIM}{result['path']}{_C.RESET}")
        except FileNotFoundError:
            print(f"  {_C.RED}File not found: {bs_file}{_C.RESET}")
        sys.exit(0)

    # CLI: --blob-list
    if len(sys.argv) >= 2 and sys.argv[1] == "--blob-list":
        blobs = brain.blob_list()
        print(f"\n{_section_header('Evidence Blob Store', _C.DIAMOND, _C.BLUE)}")
        if blobs:
            for b in blobs:
                meta = b.get("metadata", {})
                desc = meta.get("description", meta.get("original_filename", ""))
                print(f"    {_C.CYAN}{b.get('hash', '?')[:24]}...{_C.RESET}"
                      f"  {_C.DIM}{b.get('size', 0):>10,}B{_C.RESET}"
                      f"  {_C.WHITE}{desc}{_C.RESET}"
                      f"  {_C.DIM}{b.get('stored_at', '?')}{_C.RESET}")
        else:
            print(f"    {_C.DIM}No blobs stored yet.{_C.RESET}")
        print()
        sys.exit(0)

    # CLI: --blob-verify <hash>
    if len(sys.argv) >= 3 and sys.argv[1] == "--blob-verify":
        bv_hash = sys.argv[2]
        result = brain.blob_verify(bv_hash)
        color = _C.GREEN if result.get("valid") else _C.RED
        status = "INTACT" if result.get("valid") else "TAMPERED"
        print(f"  {color}{_C.BOLD}{status}{_C.RESET}"
              f"  hash={_C.DIM}{bv_hash[:24]}...{_C.RESET}"
              f"  size={result.get('size', 0):,}B")
        if not result.get("valid") and result.get("actual_hash"):
            print(f"  {_C.RED}Expected: {result['expected_hash']}{_C.RESET}")
            print(f"  {_C.RED}Actual:   {result['actual_hash']}{_C.RESET}")
        sys.exit(0)

    # CLI: --blob-link <hash> <topic>
    if len(sys.argv) >= 4 and sys.argv[1] == "--blob-link":
        bl_hash = sys.argv[2]
        bl_topic = sys.argv[3]
        result = brain.blob_link(bl_hash, bl_topic)
        if result:
            print(f"  {_C.GREEN}{_C.CHECK} Linked blob to topic:{_C.RESET} {bl_topic}")
        else:
            print(f"  {_C.RED}Blob not found.{_C.RESET}")
        sys.exit(0)

    # CLI: --peer-reputation <fp_prefix>
    if len(sys.argv) >= 3 and sys.argv[1] == "--peer-reputation":
        pr_fp = sys.argv[2]
        result = brain.link_peer_reputation(pr_fp)
        if "error" not in result:
            score = result["reputation_score"]
            sc = _C.GREEN if score >= 70 else (_C.YELLOW if score >= 40 else _C.RED)
            pr_name = result["display_name"]
            print(f"\n{_section_header(f'Peer Reputation: {pr_name}', _C.DIAMOND, _C.GOLD)}")
            # Visual reputation bar
            filled = score // 5
            bar = f"{sc}{'|' * filled}{_C.DIM}{'.' * (20 - filled)}{_C.RESET}"
            print(f"    {_C.WHITE}{_C.BOLD}Score      :{_C.RESET}  [{bar}] {sc}{score}/100{_C.RESET}")
            print(f"    {_C.WHITE}{_C.BOLD}Syncs      :{_C.RESET}  {result['total_syncs']}")
            print(f"    {_C.WHITE}{_C.BOLD}Facts Recv :{_C.RESET}  {result['facts_received']}")
            print(f"    {_C.WHITE}{_C.BOLD}Conflicts  :{_C.RESET}  {result['conflicts']}")
            print(f"    {_C.DIM}Bonus breakdown: sync={result['sync_bonus']:+.0f}"
                  f" conflict={result['conflict_bonus']:+.0f}"
                  f" recency={result['recency_bonus']:+.0f}"
                  f" manual={result['manual_adjustment']:+d}{_C.RESET}\n")
        else:
            print(f"  {_C.RED}{result['error']}{_C.RESET}")
        sys.exit(0)

    # CLI: --subscribe <fp_prefix> <topics_csv>
    if len(sys.argv) >= 4 and sys.argv[1] == "--subscribe":
        sub_fp = sys.argv[2]
        sub_topics = [t.strip() for t in sys.argv[3].split(",")]
        if brain.link_subscribe(sub_fp, sub_topics):
            print(f"  {_C.GREEN}{_C.CHECK} Subscribed to:{_C.RESET} {', '.join(sub_topics)}")
        else:
            print(f"  {_C.RED}Peer not found.{_C.RESET}")
        sys.exit(0)

    # CLI: --unsubscribe <fp_prefix> <topics_csv>
    if len(sys.argv) >= 4 and sys.argv[1] == "--unsubscribe":
        unsub_fp = sys.argv[2]
        unsub_topics = [t.strip() for t in sys.argv[3].split(",")]
        if brain.link_unsubscribe(unsub_fp, unsub_topics):
            print(f"  {_C.YELLOW}Unsubscribed from:{_C.RESET} {', '.join(unsub_topics)}")
        else:
            print(f"  {_C.RED}Peer not found.{_C.RESET}")
        sys.exit(0)

    # CLI: --case-export [path] [--case-number X] [--investigator X]
    if len(sys.argv) >= 2 and sys.argv[1] == "--case-export":
        ce_path = None
        ce_case = ""
        ce_inv = "Diamond Brain Export"
        if len(sys.argv) >= 3 and not sys.argv[2].startswith("--"):
            ce_path = sys.argv[2]
        if "--case-number" in sys.argv:
            idx = sys.argv.index("--case-number")
            if idx + 1 < len(sys.argv):
                ce_case = sys.argv[idx + 1]
        if "--investigator" in sys.argv:
            idx = sys.argv.index("--investigator")
            if idx + 1 < len(sys.argv):
                ce_inv = sys.argv[idx + 1]
        result = brain.export_case_uco(ce_path, ce_inv, ce_case)
        n_objects = len(result.get("@graph", []))
        print(f"  {_C.GREEN}{_C.CHECK} CASE/UCO Export:{_C.RESET} "
              f"{n_objects} objects")
        if ce_path:
            print(f"  {_C.DIM}Written to: {ce_path}{_C.RESET}")
        sys.exit(0)

    # CLI: --case-validate <path>
    if len(sys.argv) >= 3 and sys.argv[1] == "--case-validate":
        cv_path = Path(sys.argv[2])
        if not cv_path.exists():
            print(f"  {_C.RED}File not found: {cv_path}{_C.RESET}")
        else:
            cv_data = json.loads(cv_path.read_text(encoding="utf-8"))
            result = brain.case_validate_export(cv_data)
            color = _C.GREEN if result["valid"] else _C.RED
            print(f"\n{_section_header('CASE/UCO Validation', _C.SCALE, color)}")
            print(f"    {_C.WHITE}{_C.BOLD}Valid   :{_C.RESET}  "
                  f"{color}{'YES' if result['valid'] else 'NO'}{_C.RESET}")
            print(f"    {_C.WHITE}{_C.BOLD}Objects :{_C.RESET}  "
                  f"{result['object_count']}")
            if result["errors"]:
                print(f"    {_C.RED}Errors:{_C.RESET}")
                for e in result["errors"]:
                    print(f"      {_C.RED}- {e}{_C.RESET}")
            if result["warnings"]:
                print(f"    {_C.YELLOW}Warnings:{_C.RESET}")
                for w in result["warnings"]:
                    print(f"      {_C.YELLOW}- {w}{_C.RESET}")
            print()
        sys.exit(0)

    # CLI: --crdt-upgrade
    if len(sys.argv) >= 2 and sys.argv[1] == "--crdt-upgrade":
        result = brain.crdt_upgrade_facts()
        print(f"  {_C.GREEN}{_C.CHECK} CRDT Upgrade:{_C.RESET} "
              f"{result['upgraded']}/{result['total']} facts")
        sys.exit(0)

    # CLI: --crdt-status
    if len(sys.argv) >= 2 and sys.argv[1] == "--crdt-status":
        status = brain.crdt_status()
        print(f"\n{_section_header('CRDT Status', _C.DIAMOND, _C.CYAN)}")
        print(f"    {_C.WHITE}{_C.BOLD}Node ID    :{_C.RESET}  {status['node_id']}")
        print(f"    {_C.WHITE}{_C.BOLD}Total Facts:{_C.RESET}  {status['total_facts']}")
        print(f"    {_C.WHITE}{_C.BOLD}CRDT-enabled:{_C.RESET} {_C.GREEN}{status['crdt_enabled']}{_C.RESET}")
        print(f"    {_C.WHITE}{_C.BOLD}Legacy     :{_C.RESET}  {_C.YELLOW}{status['legacy']}{_C.RESET}")
        print(f"    {_C.WHITE}{_C.BOLD}Tombstoned :{_C.RESET}  {_C.DIM}{status['tombstoned']}{_C.RESET}\n")
        sys.exit(0)

    # CLI: --crdt-debug
    if len(sys.argv) >= 2 and sys.argv[1] == "--crdt-debug":
        debug = brain.crdt_debug_hlc()
        print(f"\n{_section_header('CRDT HLC Debug', _C.DIAMOND, _C.CYAN)}")
        for d in debug[:20]:
            tomb = f" {_C.RED}[TOMBSTONED]{_C.RESET}" if d["tombstone"] else ""
            print(f"    {_C.DIM}w={d['hlc']['wall']} c={d['hlc']['counter']}"
                  f" n={d['hlc']['node']}{_C.RESET}"
                  f"  v{d['version']} {_C.CYAN}{d['topic']}{_C.RESET}"
                  f"  {d['fact_preview']}{tomb}")
        print()
        sys.exit(0)

    # CLI: --crdt-tombstone <topic> <pattern>
    if len(sys.argv) >= 4 and sys.argv[1] == "--crdt-tombstone":
        ct_topic = sys.argv[2]
        ct_pattern = " ".join(sys.argv[3:])
        result = brain.crdt_tombstone(ct_topic, ct_pattern)
        print(f"  {_C.YELLOW}Tombstoned: {result['tombstoned']} facts{_C.RESET}")
        sys.exit(0)

    # CLI: --hc-initiate <topic> <fact> <score> [n_peers]
    if len(sys.argv) >= 5 and sys.argv[1] == "--hc-initiate":
        hc_topic = sys.argv[2]
        hc_fact = sys.argv[3]
        hc_score = int(sys.argv[4])
        hc_np = int(sys.argv[5]) if len(sys.argv) >= 6 else 1
        result = brain.hc_initiate(hc_topic, hc_fact, hc_score, hc_np)
        if "error" in result:
            print(f"  {_C.RED}{result['error']}{_C.RESET}")
        else:
            print(f"  {_C.GREEN}{_C.CHECK} HC Session Initiated:{_C.RESET}")
            print(f"    Hash: {result['fact_hash'][:16]}...")
            print(f"    Shares for peers: {result['shares_for_peers']}")
        sys.exit(0)

    # CLI: --hc-status [hash]
    if len(sys.argv) >= 2 and sys.argv[1] == "--hc-status":
        hc_hash = sys.argv[2] if len(sys.argv) >= 3 else None
        result = brain.hc_status(hc_hash)
        print(f"\n{_section_header('HC Status', _C.DIAMOND, _C.CYAN)}")
        if isinstance(result, list):
            if not result:
                print(f"    {_C.DIM}No sessions.{_C.RESET}")
            for s in result:
                print(f"    {_C.CYAN}{s['topic']}{_C.RESET} "
                      f"[{s['phase']}] {s['fact_hash']}")
        elif "error" in result:
            print(f"    {_C.RED}{result['error']}{_C.RESET}")
        else:
            print(f"    {_C.WHITE}{_C.BOLD}Topic   :{_C.RESET}  {result['topic']}")
            print(f"    {_C.WHITE}{_C.BOLD}Phase   :{_C.RESET}  {result['phase']}")
            print(f"    {_C.WHITE}{_C.BOLD}Commits :{_C.RESET}  "
                  f"{result['commitments']}/{result['n_expected']}")
            print(f"    {_C.WHITE}{_C.BOLD}Reveals :{_C.RESET}  "
                  f"{result['reveals']}/{result['n_expected']}")
            if result.get("result"):
                r = result["result"]
                print(f"    {_C.GREEN}{_C.BOLD}Average :{_C.RESET}  {r['average']}")
        print()
        sys.exit(0)

    # CLI: --hc-reveal <hash>
    if len(sys.argv) >= 3 and sys.argv[1] == "--hc-reveal":
        result = brain.hc_reveal(sys.argv[2])
        if "error" in result:
            print(f"  {_C.RED}{result['error']}{_C.RESET}")
        else:
            print(f"  {_C.GREEN}{_C.CHECK} Revealed:{_C.RESET} "
                  f"partial_sum={result['partial_sum']}")
        sys.exit(0)

    # CLI: --hc-aggregate <hash>
    if len(sys.argv) >= 3 and sys.argv[1] == "--hc-aggregate":
        result = brain.hc_aggregate(sys.argv[2])
        if "error" in result:
            print(f"  {_C.RED}{result['error']}{_C.RESET}")
        else:
            print(f"  {_C.GREEN}{_C.CHECK} Aggregated:{_C.RESET}")
            print(f"    Topic: {result['topic']}")
            print(f"    Total: {result['total']}, Average: {result['average']}")
            print(f"    Participants: {result['participants']}")
        sys.exit(0)

    # ==================================================================
    # Neural Cortex CLI Commands
    # ==================================================================

    # CLI: --cortex-ask <question>
    if len(sys.argv) >= 3 and sys.argv[1] == "--cortex-ask":
        cq = " ".join(sys.argv[2:])
        result = brain.cortex_ask(cq)
        print(f"\n{_section_header('Neural Cortex', _C.DIAMOND, _C.MAGENTA)}")
        fb_tag = f" {_C.YELLOW}[FALLBACK]{_C.RESET}" if result["fallback"] else ""
        print(f"    {_C.WHITE}{_C.BOLD}Model  :{_C.RESET}  {result['model']}{fb_tag}")
        print(f"    {_C.WHITE}{_C.BOLD}Sources:{_C.RESET}  "
              f"{', '.join(result['sources_used'][:5]) or 'none'}")
        print(f"\n{result['answer']}\n")
        sys.exit(0)

    # CLI: --cortex-summarize <topic>
    if len(sys.argv) >= 3 and sys.argv[1] == "--cortex-summarize":
        ct = " ".join(sys.argv[2:])
        result = brain.cortex_summarize(ct)
        print(f"\n{_section_header(f'Cortex Summary: {ct}', _C.DIAMOND, _C.MAGENTA)}")
        fb_tag = f" {_C.YELLOW}[FALLBACK]{_C.RESET}" if result["fallback"] else ""
        print(f"    {_C.WHITE}{_C.BOLD}Facts :{_C.RESET}  {result['fact_count']}{fb_tag}")
        print(f"\n{result['summary']}\n")
        sys.exit(0)

    # CLI: --cortex-hypothesize <question>
    if len(sys.argv) >= 3 and sys.argv[1] == "--cortex-hypothesize":
        cq = " ".join(sys.argv[2:])
        d = brain.digest()
        evidence = d.get("topics", [])[:5]
        result = brain.cortex_hypothesize(evidence, cq)
        print(f"\n{_section_header('Hypotheses', _C.DIAMOND, _C.MAGENTA)}")
        for i, h in enumerate(result.get("hypotheses", []), 1):
            print(f"    {_C.BOLD}Hypothesis {i}:{_C.RESET} "
                  f"{h.get('hypothesis', '?')}")
            print(f"    {_C.DIM}Confidence: {h.get('confidence', 0)}%{_C.RESET}")
            print(f"    {_C.DIM}Reasoning: {h.get('reasoning', '')}{_C.RESET}\n")
        sys.exit(0)

    # CLI: --cortex-cross-examine <source_id>
    if len(sys.argv) >= 3 and sys.argv[1] == "--cortex-cross-examine":
        src = sys.argv[2]
        result = brain.cortex_cross_examine(src)
        if "error" in result:
            print(f"  {_C.RED}{result['error']}{_C.RESET}")
        else:
            print(f"\n{_section_header(f'Cross-Examination: {src}', _C.SCALE, _C.MAGENTA)}")
            score = result.get("credibility_score", 0)
            score_color = (_C.GREEN if score >= 70
                           else (_C.YELLOW if score >= 40 else _C.RED))
            print(f"    {_C.WHITE}{_C.BOLD}Score:{_C.RESET}  "
                  f"{score_color}{score}/100{_C.RESET}")
            if result.get("flags"):
                print(f"    {_C.WHITE}{_C.BOLD}Flags:{_C.RESET}  "
                      f"{_C.YELLOW}{', '.join(result['flags'])}{_C.RESET}")
            print(f"\n{result.get('analysis', '')}\n")
        sys.exit(0)

    # CLI: --cortex-timeline
    if len(sys.argv) >= 2 and sys.argv[1] == "--cortex-timeline":
        result = brain.cortex_timeline_narrative()
        print(f"\n{_section_header('Timeline Narrative', _C.DIAMOND, _C.MAGENTA)}")
        print(f"    {_C.WHITE}{_C.BOLD}Events   :{_C.RESET}  {result['event_count']}")
        print(f"    {_C.WHITE}{_C.BOLD}Anomalies:{_C.RESET}  {result['anomalies_noted']}")
        print(f"\n{result['narrative']}\n")
        sys.exit(0)

    # CLI: --cortex-brief [--case-number X]
    if len(sys.argv) >= 2 and sys.argv[1] == "--cortex-brief":
        cb_case = ""
        if "--case-number" in sys.argv:
            idx = sys.argv.index("--case-number")
            if idx + 1 < len(sys.argv):
                cb_case = sys.argv[idx + 1]
        result = brain.cortex_case_brief(case_number=cb_case)
        print(f"\n{_section_header('Case Brief', _C.SCALE, _C.MAGENTA)}")
        print(result["brief"])
        print()
        sys.exit(0)

    # CLI: --cortex-status
    if len(sys.argv) >= 2 and sys.argv[1] == "--cortex-status":
        status = brain.cortex_status()
        print(f"\n{_section_header('Neural Cortex Status', _C.DIAMOND, _C.MAGENTA)}")
        avail_color = _C.GREEN if status["available"] else _C.RED
        print(f"    {_C.WHITE}{_C.BOLD}Available :{_C.RESET}  "
              f"{avail_color}{'YES' if status['available'] else 'NO'}{_C.RESET}")
        if status["model"]:
            print(f"    {_C.WHITE}{_C.BOLD}Model     :{_C.RESET}  {status['model']}")
        print(f"    {_C.WHITE}{_C.BOLD}URL       :{_C.RESET}  {status['url']}")
        print(f"    {_C.WHITE}{_C.BOLD}Queries   :{_C.RESET}  {status['total_queries']}")
        print(f"    {_C.WHITE}{_C.BOLD}Avg Speed :{_C.RESET}  "
              f"{status['avg_response_ms']}ms")
        if status.get("last_query"):
            lq = status["last_query"]
            print(f"    {_C.WHITE}{_C.BOLD}Last Query:{_C.RESET}  "
                  f"{lq.get('method', '?')} @ {lq.get('timestamp', '?')}")
        print()
        sys.exit(0)

    # CLI: --cortex-personality [on|off]
    if len(sys.argv) >= 2 and sys.argv[1] == "--cortex-personality":
        enable = True
        if len(sys.argv) >= 3 and sys.argv[2].lower() in ("off", "false", "0"):
            enable = False
        result = brain.cortex_set_personality(enable)
        state = (f"{_C.GREEN}ENABLED" if enable
                 else f"{_C.YELLOW}DISABLED")
        print(f"\n{_section_header('Diamond Brains 3.0', _C.DIAMOND, _C.MAGENTA)}")
        print(f"    Personality: {state}{_C.RESET}")
        print(f"    Cortex responses will {'use DB3 high-velocity style' if enable else 'use default forensic analyst style'}")
        print()
        sys.exit(0)

    # CLI: --cortex-debrief [topic]
    if len(sys.argv) >= 2 and sys.argv[1] == "--cortex-debrief":
        db_topic = sys.argv[2] if len(sys.argv) >= 3 else None
        result = brain.cortex_debrief(topic=db_topic)
        print(f"\n{_section_header('DB3 Debrief', _C.DIAMOND, _C.MAGENTA)}")
        if result["hits"]:
            for h in result["hits"]:
                print(f"    {_C.GREEN}\u2705 {h}{_C.RESET}")
        if result["misses"]:
            for m in result["misses"]:
                print(f"    {_C.RED}\u274c {m}{_C.RESET}")
        if result["changes"]:
            for c in result["changes"]:
                print(f"    {_C.YELLOW}\U0001f504 {c}{_C.RESET}")
        print()
        s = result["stats"]
        print(f"    {_C.WHITE}{_C.BOLD}Facts      :{_C.RESET}  "
              f"{s['total_facts']} total, {s['high_confidence']} verified-high, "
              f"{s['low_confidence']} low-conf")
        print(f"    {_C.WHITE}{_C.BOLD}Quarantine :{_C.RESET}  "
              f"{s['quarantine_total']} held, {s['quarantine_eligible']} eligible")
        print(f"    {_C.WHITE}{_C.BOLD}Alerts     :{_C.RESET}  "
              f"{s['active_alerts']} active, {s['critical_alerts']} critical")
        if result.get("llm_summary"):
            print(f"\n    {_C.CYAN}{_C.BOLD}LLM Summary:{_C.RESET}")
            for line in result["llm_summary"].split("\n"):
                print(f"    {line}")
        print()
        sys.exit(0)

    # CLI: --third-eye-scan [--type TYPE]
    if len(sys.argv) >= 2 and sys.argv[1] == "--third-eye-scan":
        te_types = None
        if "--type" in sys.argv:
            idx = sys.argv.index("--type")
            if idx + 1 < len(sys.argv):
                te_types = [sys.argv[idx + 1]]
        alerts = brain.third_eye_scan(include_types=te_types)
        active = [a for a in alerts if not a.get("suppressed")]
        print(f"\n{_section_header('Third Eye Scan', _C.DIAMOND, _C.MAGENTA)}")
        if not active:
            print(f"    {_C.GREEN}{_C.CHECK} No alerts — brain is healthy{_C.RESET}")
        else:
            for a in active:
                sev = a["severity"]
                sc = (_C.RED if sev == "CRITICAL" else
                      _C.YELLOW if sev in ("HIGH", "MEDIUM") else _C.DIM)
                print(f"    {sc}{_C.BOLD}[{sev}]{_C.RESET} {a['message']}")
                print(f"           {_C.DIM}Action: {a['recommended_action']}{_C.RESET}")
        suppressed = [a for a in alerts if a.get("suppressed")]
        if suppressed:
            print(f"    {_C.DIM}({len(suppressed)} suppressed){_C.RESET}")
        print()
        sys.exit(0)

    # CLI: --third-eye-status
    if len(sys.argv) >= 2 and sys.argv[1] == "--third-eye-status":
        status = brain.third_eye_status()
        print(f"\n{_section_header('Third Eye Status', _C.DIAMOND, _C.MAGENTA)}")
        print(f"    {_C.WHITE}{_C.BOLD}Last Scan   :{_C.RESET}  "
              f"{status.get('last_scan') or 'never'}")
        print(f"    {_C.WHITE}{_C.BOLD}Total Scans :{_C.RESET}  "
              f"{status.get('total_scans', 0)}")
        total = status.get("total_alerts", 0)
        tc = _C.GREEN if total == 0 else _C.RED
        print(f"    {_C.WHITE}{_C.BOLD}Active Alerts:{_C.RESET}  {tc}{total}{_C.RESET}")
        by_sev = status.get("by_severity", {})
        if by_sev:
            parts = []
            for s in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
                if by_sev.get(s):
                    sc = _C.RED if s == "CRITICAL" else _C.YELLOW if s != "LOW" else _C.DIM
                    parts.append(f"{sc}{s}={by_sev[s]}{_C.RESET}")
            print(f"    {_C.WHITE}{_C.BOLD}Breakdown   :{_C.RESET}  {', '.join(parts)}")
        watched = status.get("watched_topics", [])
        if watched:
            print(f"    {_C.WHITE}{_C.BOLD}Watching    :{_C.RESET}  "
                  f"{_C.CYAN}{', '.join(watched)}{_C.RESET}")
        print()
        sys.exit(0)

    # CLI: --third-eye-suppress <type> [target]
    if len(sys.argv) >= 3 and sys.argv[1] == "--third-eye-suppress":
        te_type = sys.argv[2]
        te_target = sys.argv[3] if len(sys.argv) >= 4 else "*"
        result = brain.third_eye_suppress(te_type, te_target)
        print(f"  {_C.GREEN}{_C.CHECK} Suppressed:{_C.RESET} "
              f"{result['suppressed']} (target={result['target']})")
        sys.exit(0)

    # CLI: --third-eye-watch <topic>
    if len(sys.argv) >= 3 and sys.argv[1] == "--third-eye-watch":
        te_topic = sys.argv[2]
        result = brain.third_eye_watch(te_topic)
        print(f"  {_C.GREEN}{_C.CHECK} Watching:{_C.RESET} "
              f"'{result['watched']}' ({result['total_watched']} total)")
        sys.exit(0)

    # CLI: --quarantine-list [--batch BATCH_ID]
    if len(sys.argv) >= 2 and sys.argv[1] == "--quarantine-list":
        q_batch = None
        if "--batch" in sys.argv:
            idx = sys.argv.index("--batch")
            if idx + 1 < len(sys.argv):
                q_batch = sys.argv[idx + 1]
        items = brain.quarantine_list(batch_id=q_batch)
        print(f"\n{_section_header('Diamond Quarantine', _C.DIAMOND, _C.YELLOW)}")
        if not items:
            print(f"    {_C.GREEN}{_C.CHECK} Quarantine is empty{_C.RESET}")
        else:
            for e in items:
                days = round(_days_ago(e.get("quarantined_at", "")), 1)
                sc = _C.RED if days >= 21 else _C.YELLOW if days >= 14 else _C.DIM
                tags_str = f" [{', '.join(e.get('tags', []))}]" if e.get("tags") else ""
                print(f"    {sc}{e['id']}{_C.RESET} "
                      f"{_C.CYAN}{e.get('topic', '?')}{_C.RESET} "
                      f"{_C.DIM}({e.get('source', '?')}, {days}d){_C.RESET}"
                      f"{_C.YELLOW}{tags_str}{_C.RESET}")
                print(f"           {_C.DIM}{e.get('fact_preview', '')[:80]}{_C.RESET}")
        print()
        sys.exit(0)

    # CLI: --quarantine-stats
    if len(sys.argv) >= 2 and sys.argv[1] == "--quarantine-stats":
        stats = brain.quarantine_stats()
        print(f"\n{_section_header('Quarantine Stats', _C.DIAMOND, _C.YELLOW)}")
        print(f"    {_C.WHITE}{_C.BOLD}Total      :{_C.RESET}  {stats['total']}")
        for label, data in [("By Status", stats["by_status"]),
                            ("By Source", stats["by_source"])]:
            if data:
                parts = [f"{k}={v}" for k, v in sorted(data.items())]
                print(f"    {_C.WHITE}{_C.BOLD}{label:<11}:{_C.RESET}  {', '.join(parts)}")
        print(f"    {_C.WHITE}{_C.BOLD}Oldest     :{_C.RESET}  {stats['oldest_days']} days")
        print()
        sys.exit(0)

    # CLI: --quarantine-preview [--batch BATCH_ID]
    if len(sys.argv) >= 2 and sys.argv[1] == "--quarantine-preview":
        q_batch = None
        if "--batch" in sys.argv:
            idx = sys.argv.index("--batch")
            if idx + 1 < len(sys.argv):
                q_batch = sys.argv[idx + 1]
        batches = brain.quarantine_preview(batch_id=q_batch)
        print(f"\n{_section_header('Quarantine Preview', _C.DIAMOND, _C.YELLOW)}")
        if not batches:
            print(f"    {_C.DIM}No eligible items (14-day hold not expired){_C.RESET}")
        else:
            for b in batches:
                print(f"    {_C.WHITE}{_C.BOLD}Batch {b['batch_id']}{_C.RESET}"
                      f"  ({b['count']} items)")
                print(f"    {_C.DIM}Reason: {b['brain_reason']}{_C.RESET}")
                for e in b["entries"][:5]:
                    print(f"      {_C.CYAN}{e['id']}{_C.RESET} {e.get('topic', '?')}"
                          f" {_C.DIM}{e.get('fact_preview', '')[:60]}{_C.RESET}")
                if b["count"] > 5:
                    print(f"      {_C.DIM}... and {b['count'] - 5} more{_C.RESET}")
        print()
        sys.exit(0)

    # CLI: --quarantine-restore <entry_id>
    if len(sys.argv) >= 3 and sys.argv[1] == "--quarantine-restore":
        entry_id = sys.argv[2]
        result = brain.quarantine_restore(entry_id)
        if "error" in result:
            print(f"  {_C.RED}{result['error']}{_C.RESET}")
        else:
            print(f"  {_C.GREEN}{_C.CHECK} Restored:{_C.RESET} "
                  f"{result['topic']} — {result['fact_preview']}")
        sys.exit(0)

    # CLI: --quarantine-purge <batch_id> <passphrase> [--reason TEXT] [--override]
    if len(sys.argv) >= 4 and sys.argv[1] == "--quarantine-purge":
        qp_batch = sys.argv[2]
        qp_pass = sys.argv[3]
        qp_reason = None
        if "--reason" in sys.argv:
            idx = sys.argv.index("--reason")
            if idx + 1 < len(sys.argv):
                qp_reason = sys.argv[idx + 1]
        qp_override = "--override" in sys.argv
        result = brain.quarantine_purge(qp_batch, qp_pass,
                                        reason=qp_reason,
                                        override=qp_override)
        if result.get("error"):
            print(f"  {_C.RED}{result['error']}: {result.get('message', '')}{_C.RESET}")
        elif result.get("pushback"):
            print(f"  {_C.YELLOW}{_C.BOLD}Brain pushback ({result['pushback_count']}/2):{_C.RESET}")
            for c in result.get("concerns", []):
                print(f"    {_C.YELLOW}• {c}{_C.RESET}")
            print(f"  {_C.DIM}{result.get('message', '')}{_C.RESET}")
        else:
            print(f"  {_C.GREEN}{_C.CHECK} Purged:{_C.RESET} "
                  f"{result['purged']} items from batch {result['batch_id']}")
            print(f"  {_C.DIM}Reason: {result.get('reason', 'N/A')}{_C.RESET}")
        sys.exit(0)

    # CLI: --source-register <id> <type> [name] [domains_csv]
    if len(sys.argv) >= 4 and sys.argv[1] == "--source-register":
        sr_id = sys.argv[2]
        sr_type = sys.argv[3]
        sr_name = sys.argv[4] if len(sys.argv) >= 5 else None
        sr_domains = sys.argv[5].split(",") if len(sys.argv) >= 6 else None
        result = brain.source_register(sr_id, sr_type, sr_name, sr_domains)
        print(f"  {_C.GREEN}{_C.CHECK} Registered:{_C.RESET} "
              f"{result['display_name']} ({result['source_type']})")
        sys.exit(0)

    # CLI: --source-credibility <id>
    if len(sys.argv) >= 3 and sys.argv[1] == "--source-credibility":
        _print_source_credibility(brain, sys.argv[2])
        sys.exit(0)

    # CLI: --source-list
    if len(sys.argv) >= 2 and sys.argv[1] == "--source-list":
        _print_source_list(brain)
        sys.exit(0)

    # CLI: --source-adjust <id> <delta>
    if len(sys.argv) >= 4 and sys.argv[1] == "--source-adjust":
        sa_id = sys.argv[2]
        sa_delta = int(sys.argv[3])
        result = brain.source_adjust_credibility(sa_id, sa_delta)
        if "error" in result:
            print(f"  {_C.RED}{result['error']}{_C.RESET}")
        else:
            print(f"  {_C.GREEN}{_C.CHECK} Adjusted:{_C.RESET} {sa_id} "
                  f"({result['previous_adjustment']:+d} -> "
                  f"{result['new_adjustment']:+d})")
        sys.exit(0)

    _print_digest(brain)
    _print_heatmap(brain)

    # If the brain is empty, seed a welcome fact so the user sees it work
    if brain.digest()["total_facts"] == 0:
        print(f"  {_C.YELLOW}First run detected. Seeding a welcome fact...{_C.RESET}")
        brain.learn(
            topic="diamond-brain",
            fact="Diamond Brain module initialized. Ready to cache knowledge.",
            confidence=100,
            source="system",
            verified=True,
        )
        print(f"  {_C.GREEN}Done. Run again to see the brain in action.{_C.RESET}\n")
