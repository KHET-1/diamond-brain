"""
================================================================================
  DIAMOND BRAIN v1.0 — Standalone Knowledge Cache
================================================================================
  Lightweight intelligence module. Stores facts, tracks agents, handles
  escalations. All data persisted as JSON on disk. No external dependencies.

  Origin: Modeled after rathin_utils.brain.Brain from the Parrot Linux rig.
  Adapted for Windows / cross-platform with zero dependencies.
================================================================================
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone
from difflib import SequenceMatcher


# ---------------------------------------------------------------------------
# ANSI helpers — degrade gracefully on terminals that strip escapes
# ---------------------------------------------------------------------------
class _C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    CYAN   = "\033[96m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"
    MAGENTA = "\033[95m"
    WHITE  = "\033[97m"
    BG_DARK = "\033[48;5;235m"


BANNER = f"""
{_C.CYAN}{_C.BOLD}  ============================================================{_C.RESET}
{_C.CYAN}{_C.BOLD}     DIAMOND BRAIN{_C.RESET}{_C.DIM}  //  Knowledge Cache  //  Standalone{_C.RESET}
{_C.CYAN}{_C.BOLD}  ============================================================{_C.RESET}
"""


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

        # Ensure files exist
        for p in (self._facts_path, self._agents_path, self._escalations_path):
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
    def recall(self, topic: str, max_results: int = 8) -> list[dict]:
        """Return up to *max_results* facts for *topic*, highest confidence first."""
        facts = self._load(self._facts_path)
        matches = [f for f in facts if f.get("topic", "").lower() == topic.lower()]
        matches.sort(key=lambda f: f.get("confidence", 0), reverse=True)
        return matches[:max_results]

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
                self._save(self._facts_path, facts)
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
        }
        facts.append(entry)
        self._save(self._facts_path, facts)
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
        """Register or update a zombie agent. Returns the agent record."""
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

        return {
            "total_facts": len(facts),
            "topics": topics,
            "total_agents": len(agents),
            "agent_history": agent_summary,
            "last_updated": last_updated,
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


# ==========================================================================
# CLI entry point
# ==========================================================================
def _print_digest(brain: DiamondBrain) -> None:
    """Pretty-print the brain digest to stdout."""
    print(BANNER)
    d = brain.digest()

    print(f"  {_C.WHITE}{_C.BOLD}Total Facts :{_C.RESET}  {_C.GREEN}{d['total_facts']}{_C.RESET}")
    print(f"  {_C.WHITE}{_C.BOLD}Topics      :{_C.RESET}  {_C.CYAN}{', '.join(d['topics']) if d['topics'] else '(none yet)'}{_C.RESET}")
    print(f"  {_C.WHITE}{_C.BOLD}Agents      :{_C.RESET}  {_C.YELLOW}{d['total_agents']}{_C.RESET}")
    print(f"  {_C.WHITE}{_C.BOLD}Last Updated:{_C.RESET}  {_C.DIM}{d['last_updated'] or 'never'}{_C.RESET}")
    print()

    if d["agent_history"]:
        print(f"  {_C.MAGENTA}{_C.BOLD}--- Agent Roster ---{_C.RESET}")
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

    print(f"  {_C.MAGENTA}{_C.BOLD}--- Knowledge Heatmap ---{_C.RESET}")
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


if __name__ == "__main__":
    brain = DiamondBrain()

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
