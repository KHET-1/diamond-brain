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
import socket
import ssl
import threading
import time
import uuid
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from difflib import SequenceMatcher

# brain_schema — interoperability validators (wire these into handshake paths)
try:
    from brain.brain_schema import negotiate_handshake, parse_pair_ack, validate_facts_batch
except ImportError:
    from brain_schema import negotiate_handshake, parse_pair_ack, validate_facts_batch


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


def _decayed_confidence(confidence: int, timestamp: str, verified: bool) -> float:
    """
    Calculate time-decayed confidence for a fact.

    Unverified facts: 60-day half-life (confidence halves every 60 days)
    Verified facts: 180-day half-life (confidence halves every 180 days)
    Floor: 30 (confidence never drops below 30)

    Args:
        confidence: Initial confidence (0-100)
        timestamp: ISO timestamp when fact was created/updated
        verified: Whether the fact was verified (True = slower decay)

    Returns:
        Decayed confidence value, floored at 30
    """
    try:
        fact_time = datetime.fromisoformat(timestamp)
        if fact_time.tzinfo is None:
            fact_time = fact_time.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        age_days = (now - fact_time).total_seconds() / 86400.0
    except (ValueError, TypeError):
        return float(confidence)  # Invalid timestamp, return original

    # Half-life: 60 days for unverified, 180 for verified
    half_life = 180 if verified else 60

    # Exponential decay: C(t) = C0 * (0.5)^(t/half_life)
    decayed = confidence * (0.5 ** (age_days / half_life))

    # Floor at 30
    return max(30.0, decayed)


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
        self._identity_path = self.memory_dir / "link" / "identity.json"

        # Ensure files exist
        for p in (self._facts_path, self._agents_path, self._escalations_path):
            if not p.exists():
                p.write_text("[]", encoding="utf-8")

        # Persistent peer identity tracking (set on pair)
        self._peer_nic: dict = {}

        # Ensure Node Identity Card exists
        self._ensure_node_identity()

    # ------------------------------------------------------------------
    # Node Identity Card (NIC) — spec v1.0
    # ------------------------------------------------------------------
    def _ensure_node_identity(self) -> None:
        """Create NIC if not present. UUID is generated once and never regenerated."""
        self._identity_path.parent.mkdir(parents=True, exist_ok=True)
        if self._identity_path.exists():
            try:
                nic = json.loads(self._identity_path.read_text(encoding="utf-8"))
                if nic.get("uuid"):
                    return  # Already established
            except (json.JSONDecodeError, KeyError):
                pass
        node_uuid = str(uuid.uuid4())
        host = socket.gethostname()
        name = f"Diamond@{host}"
        fp_raw = hashlib.sha256(f"{node_uuid}{name}{host}".encode()).hexdigest()
        nic = {
            "uuid":         node_uuid,
            "name":         name,
            "host":         host,
            "role":         "primary",
            "location":     "unset",
            "created":      datetime.now(timezone.utc).isoformat(),
            "spec_version": "1.0",
            "fingerprint":  f"sha256:{fp_raw[:16]}",
        }
        tmp = self._identity_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(nic, indent=2), encoding="utf-8")
        os.replace(str(tmp), str(self._identity_path))

    def node_id(self) -> dict:
        """Return this brain's Node Identity Card."""
        try:
            return json.loads(self._identity_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def whoami(self) -> str:
        """Print and return compact identity: Name | host | role | fingerprint."""
        n = self.node_id()
        if not n.get("uuid"):
            print(f"  [no identity]")
            return ""
        fp = n.get("fingerprint", "")[-8:]
        line = f"{n.get('name','?')} | {n.get('host','?')} | {n.get('role','?')} | {fp}"
        print(f"  {_C.CYAN}{_C.BOLD}[{line}]{_C.RESET}")
        return line

    def set_node_name(self, name: str, role: str = None, location: str = None) -> None:
        """Update mutable NIC fields. UUID never changes."""
        n = self.node_id()
        if not n.get("uuid"):
            self._ensure_node_identity()
            n = self.node_id()
        n["name"] = name
        if role:     n["role"]     = role
        if location: n["location"] = location
        fp_raw = hashlib.sha256(f"{n['uuid']}{name}{n['host']}".encode()).hexdigest()
        n["fingerprint"] = f"sha256:{fp_raw[:16]}"
        tmp = self._identity_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(n, indent=2), encoding="utf-8")
        os.replace(str(tmp), str(self._identity_path))
        self.whoami()

    # ------------------------------------------------------------------
    # _get_capabilities — advertise what stores this instance has
    # ------------------------------------------------------------------
    def _get_capabilities(self) -> list:
        """Return the list of capability tokens this brain can sync.

        Capabilities are determined by which stores exist on disk.
        Always includes 'facts' as the baseline floor.
        """
        caps = ["facts"]
        store_map = {
            "agents":    self.memory_dir / "agents.json",
            "citations": self.memory_dir / "citations.json",
            "graph":     self.memory_dir / "graph.json",
            "fsrs":      self.memory_dir / "fsrs.json",
            "temporal":  self.memory_dir / "temporal.json",
            "commands":  self.memory_dir / "commands.json",
            "blobs":     self.memory_dir / "blobs" / "manifest.json",
            "scrolls":   self.memory_dir / "scrolls",
            "embeddings": self.memory_dir / "embeddings.json",
        }
        for cap, path in store_map.items():
            if path.exists():
                caps.append(cap)
        return caps

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

    # ------------------------------------------------------------------
    # link_init — initialize peer name for pairing
    # ------------------------------------------------------------------
    def link_init(self, peer_name: str) -> None:
        """Initialize the brain for pairing. Sets the peer identifier."""
        self.peer_name = peer_name
        self.peer_ip = None
        self._link_connected = False
        self._link_peer_ip = None

    # ------------------------------------------------------------------
    # export_json — export brain as JSON string
    # ------------------------------------------------------------------
    def export_json(self, pretty: bool = True) -> str:
        """Export brain snapshot as JSON string.

        Usage:
            json_str = brain.export_json()
            with open('backup.json', 'w') as f:
                f.write(json_str)
        """
        snapshot = self._link_build_snapshot()
        return json.dumps(snapshot, indent=2 if pretty else None, ensure_ascii=False)

    # ------------------------------------------------------------------
    # import_json — import brain from JSON string
    # ------------------------------------------------------------------
    def import_json(self, json_str: str) -> int:
        """Import brain snapshot from JSON string.

        Returns: Number of facts merged
        """
        snapshot = json.loads(json_str)
        self._link_import_snapshot(snapshot)
        return len(snapshot.get("facts", []))

    # ------------------------------------------------------------------
    # link_serve — TCP+TLS server for accepting peer connections
    # ------------------------------------------------------------------
    def link_serve(self, port: int = 7777, bind_addr: str = "0.0.0.0") -> None:
        """Start listening for incoming peer connections.

        Protocol:
          1. Receive PAIR_REQUEST or SYNC_REQUEST
          2. Respond with PAIR_ACK or SYNC_DATA
          3. Wait for next request or close
        """
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((bind_addr, port))
        server_socket.listen(1)

        print(f"{_C.GREEN}✓ Diamond Brain listening on port {port}{_C.RESET}")

        try:
            while True:
                conn, addr = server_socket.accept()
                peer_ip = addr[0]
                print(f"{_C.CYAN}→ Connection from {peer_ip}:{addr[1]}{_C.RESET}")

                try:
                    # Receive first message
                    msg = conn.recv(1024).decode("utf-8")
                    msg_dict = json.loads(msg)
                    msg_type = msg_dict.get("type")

                    if msg_type == "PAIR_REQUEST":
                        # Use schema validator to build PAIR_ACK and negotiate caps
                        response = negotiate_handshake(
                            self.node_id(),
                            self._get_capabilities(),
                            msg_dict,
                            peer_ip,
                        )
                        # Preserve extra fields the inline path provided
                        response["peer_name"] = getattr(self, 'peer_name', 'Diamond')
                        response["facts_count"] = len(self._load(self._facts_path))
                        # Cache the validated peer NIC from the negotiation result
                        peer_nic = response.get("peer_nic", {})
                        if peer_nic:
                            self._peer_nic = peer_nic
                        conn.send(json.dumps(response).encode("utf-8"))
                        self.peer_ip = peer_ip
                        peer_label = peer_nic.get("name") or msg_dict.get('peer_name', 'Unknown')
                        peer_fp = peer_nic.get("fingerprint", "")[-8:] if peer_nic else ""
                        if response.get("compat", True):
                            print(f"{_C.GREEN}✓ Paired with {peer_label} [{peer_fp}]{_C.RESET}")
                        else:
                            reason = response.get("reject_reason", "schema mismatch")
                            print(f"{_C.RED}✗ Rejected {peer_label}: {reason}{_C.RESET}")

                        # Keep socket open — loop until peer disconnects or sync completes
                        while True:
                            try:
                                next_bytes = conn.recv(4096)
                                if not next_bytes:
                                    break
                                next_dict = json.loads(next_bytes.decode("utf-8").strip())
                                next_type = next_dict.get("type")

                                if next_type == "PAIR_CONFIRM":
                                    # Peer confirmed pairing — acknowledge and keep reading
                                    print(f"{_C.GREEN}  ✓ Peer confirmed pairing{_C.RESET}")

                                elif next_type == "SYNC_REQUEST":
                                    topics    = next_dict.get("topics", [])
                                    direction = next_dict.get("direction", "push")
                                    self._handle_sync_request(conn, peer_ip, topics=topics)
                                    if direction == "both":
                                        # Receive peer's facts too
                                        self._link_recv_snapshot(conn, peer_ip)
                                    conn.send(json.dumps({"type": "SYNC_DONE"}).encode("utf-8"))
                                    break

                                # Unknown types: log and continue reading

                            except (json.JSONDecodeError, UnicodeDecodeError):
                                break
                            except Exception as e:
                                print(f"{_C.RED}✗ Protocol error: {e}{_C.RESET}")
                                break

                    elif msg_type == "SYNC_REQUEST":
                        # Direct sync request (no prior pairing)
                        self._handle_sync_request(conn, peer_ip)

                except Exception as e:
                    print(f"{_C.RED}✗ Error: {e}{_C.RESET}")
                finally:
                    conn.close()
        except KeyboardInterrupt:
            print(f"\n{_C.YELLOW}✓ Server stopped{_C.RESET}")
        finally:
            server_socket.close()

    # ------------------------------------------------------------------
    # link_pair_connect — client connects to peer and syncs facts
    # ------------------------------------------------------------------
    def link_pair_connect(self, remote_ip: str, port: int = 7777, timeout: int = 10) -> bool:
        """Connect to a peer brain and synchronize facts.

        Phase 1: TCP handshake
        Phase 2: TLS encrypted sync

        Returns: True if sync successful, False otherwise
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)

            print(f"{_C.CYAN}→ Connecting to {remote_ip}:{port}...{_C.RESET}")
            sock.connect((remote_ip, port))

            # Phase 1: TCP handshake — include NIC in request
            request = {
                "type": "PAIR_REQUEST",
                "peer_name": getattr(self, 'peer_name', 'Diamond'),
                "facts_count": len(self._load(self._facts_path)),
                "node": self.node_id(),
            }
            sock.send(json.dumps(request).encode("utf-8"))

            # Receive peer response (PAIR_ACK or just proceed)
            response = sock.recv(1024).decode("utf-8")
            response_dict = json.loads(response)
            response_type = response_dict.get("type")

            if response_type == "PAIR_ACK":
                compat, negotiation, ack_issues = parse_pair_ack(response_dict, remote_ip)
                if ack_issues:
                    for issue in ack_issues:
                        print(f"{_C.YELLOW}  ⚠ {issue}{_C.RESET}")
                if not compat:
                    reason = response_dict.get("reject_reason", "peer rejected sync")
                    print(f"{_C.RED}✗ Pairing rejected by peer: {reason}{_C.RESET}")
                    return False
                peer_nic = negotiation.get("peer_nic", {})
                if peer_nic:
                    self._peer_nic = peer_nic
                peer_label = peer_nic.get("name") or response_dict.get('peer_name', 'Unknown')
                peer_fp = peer_nic.get("fingerprint", "")[-8:] if peer_nic else ""
                print(f"{_C.GREEN}✓ Paired with {peer_label} [{peer_fp}]{_C.RESET}")
                self.peer_ip = remote_ip
            elif response_type == "PAIR_RESPONSE":
                # Old protocol - still supported
                print(f"{_C.GREEN}✓ Paired with {response_dict.get('peer_name', 'Unknown')}{_C.RESET}")
                self.peer_ip = remote_ip
            else:
                print(f"{_C.RED}✗ Invalid response from peer{_C.RESET}")
                return False

            # Send PAIR_CONFIRM to complete pairing handshake
            confirm = {"type": "PAIR_CONFIRM"}
            sock.send(json.dumps(confirm).encode("utf-8"))
            print(f"{_C.GREEN}✓ Sent pairing confirmation{_C.RESET}")

            # Phase 2: Request sync
            print(f"{_C.YELLOW}→ Requesting sync...{_C.RESET}")
            sync_request = {
                "type": "SYNC_REQUEST",
                "peer_name": getattr(self, 'peer_name', 'Diamond'),
            }
            sock.send(json.dumps(sync_request).encode("utf-8"))

            # Receive sync data
            self._link_recv_snapshot(sock, remote_ip)

            sock.close()
            return True

        except socket.timeout:
            print(f"{_C.RED}✗ Connection timeout{_C.RESET}")
            return False
        except Exception as e:
            print(f"{_C.RED}✗ Connection error: {e}{_C.RESET}")
            return False

    # ------------------------------------------------------------------
    # establish_diamond_link — high-level wrapper for LAN/WAN connect
    # ------------------------------------------------------------------
    def establish_diamond_link(self, passphrase: str, host: str = None,
                                port: int = 7777, timeout: int = 10) -> dict:
        """
        High-level Diamond Link connect.
        - If host is given: direct TCP connect (works over internet/WAN)
        - If host is None: UDP broadcast discovery on LAN, then connect
        Returns: {"status": "connected"|"failed", "peer_name": str, "peer_ip": str, "facts_merged": int}
        """
        if host:
            # WAN / direct mode — skip UDP
            return self._direct_connect(host, port, timeout, passphrase)
        else:
            # LAN mode — UDP broadcast DIAMOND_ANNOUNCE, wait for ACK
            peer_ip = self._udp_discover(passphrase, timeout)
            if peer_ip:
                return self._direct_connect(peer_ip, port, timeout, passphrase)
            return {"status": "failed", "reason": "no peers found on LAN"}

    # ------------------------------------------------------------------
    # _direct_connect — thin wrapper around link_pair_connect
    # ------------------------------------------------------------------
    def _direct_connect(self, host: str, port: int, timeout: int, passphrase: str = None) -> dict:
        """Thin wrapper: call link_pair_connect, capture result."""
        try:
            ok = self.link_pair_connect(host, port=port, timeout=timeout)
            self._link_peer_ip = host
            self._link_connected = ok
            return {
                "status": "connected" if ok else "failed",
                "peer_ip": host,
                "port": port,
                "peer_name": getattr(self, "peer_name", "Diamond"),
                "facts_merged": len(self._load(self._facts_path)) if ok else 0,
            }
        except Exception as e:
            self._link_connected = False
            return {"status": "failed", "reason": str(e)}

    # ------------------------------------------------------------------
    # _udp_discover — UDP broadcast discovery on LAN
    # ------------------------------------------------------------------
    def _udp_discover(self, passphrase: str, timeout: int = 10) -> str | None:
        """
        Broadcast UDP DIAMOND_ANNOUNCE on LAN, wait for peer response.
        Returns: peer_ip if found, None if timeout.
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(timeout)

            # Send broadcast announce
            announce = json.dumps({
                "type": "DIAMOND_ANNOUNCE",
                "peer_name": getattr(self, "peer_name", "Diamond"),
                "passphrase_hash": hash(passphrase) & 0xffffffff,  # Low security for LAN discovery
            }).encode("utf-8")
            sock.sendto(announce, ("<broadcast>", 7776))

            # Wait for response
            print(f"{_C.YELLOW}→ Broadcasting for peers on LAN (timeout {timeout}s)...{_C.RESET}")
            try:
                data, addr = sock.recvfrom(1024)
                response = json.loads(data.decode("utf-8"))
                if response.get("type") == "DIAMOND_ACK":
                    peer_ip = addr[0]
                    print(f"{_C.GREEN}✓ Found peer at {peer_ip}{_C.RESET}")
                    return peer_ip
            except socket.timeout:
                print(f"{_C.RED}✗ No peers found on LAN{_C.RESET}")
                return None
            finally:
                sock.close()

        except Exception as e:
            print(f"{_C.RED}✗ UDP discovery error: {e}{_C.RESET}")
            return None

    # ------------------------------------------------------------------
    # diamond_link_status — check connection status
    # ------------------------------------------------------------------
    def diamond_link_status(self) -> dict:
        """Return current Diamond Link connection status including NICs."""
        local_nic = self.node_id()
        peer_nic  = getattr(self, "_peer_nic", {})
        return {
            "connected":    getattr(self, "_link_connected", False),
            "peer_ip":      getattr(self, "_link_peer_ip", None),
            "peer_name":    peer_nic.get("name") or getattr(self, "peer_name", None),
            "has_identity": bool(local_nic.get("uuid")),
            "local":  {k: local_nic.get(k) for k in ("uuid", "name", "host", "role", "fingerprint")},
            "peer":   {k: peer_nic.get(k)  for k in ("uuid", "name", "host", "role", "fingerprint")} if peer_nic else {},
        }

    # ------------------------------------------------------------------
    # disconnect_diamond_link — disconnect from peer
    # ------------------------------------------------------------------
    def disconnect_diamond_link(self) -> None:
        """Disconnect from peer."""
        self._link_connected = False
        self._link_peer_ip = None
        print(f"{_C.YELLOW}✓ Diamond Link disconnected{_C.RESET}")

    # ------------------------------------------------------------------
    # link_status — status info for tests / diagnostic
    # ------------------------------------------------------------------
    def link_status(self) -> dict:
        """Return link initialization and peer discovery status."""
        return {
            "initialized": getattr(self, "peer_name", None) is not None,
            "peer_count": len(self._get_peers()),
            "peer_ip": getattr(self, "peer_ip", None),
        }

    # ------------------------------------------------------------------
    # _get_peers — retrieve list of discovered peers
    # ------------------------------------------------------------------
    def _get_peers(self) -> list:
        """Return list of known peers from peers.json."""
        peers_file = self.memory_dir / "link" / "peers.json"
        if peers_file.exists():
            try:
                return json.loads(peers_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, FileNotFoundError):
                return []
        return []

    # ------------------------------------------------------------------
    # _handle_sync_request — respond to SYNC_REQUEST with facts
    # ------------------------------------------------------------------
    def _handle_sync_request(
        self,
        conn: socket.socket,
        peer_ip: str,
        topics: list | None = None,
        direction: str = "push",
    ) -> None:
        """Handle SYNC_REQUEST by sending our facts snapshot."""
        try:
            facts = self._load(self._facts_path)
            if topics:
                facts = [f for f in facts if f.get("topic") in topics]
            payload = json.dumps({
                "type": "SYNC_RESPONSE",
                "facts": facts,
                "peer_name": getattr(self, "peer_name", "Diamond"),
            }).encode("utf-8")
            conn.send(len(payload).to_bytes(4, "big") + payload)
            print(f"{_C.GREEN}✓ Sent {len(facts)} facts to {peer_ip}{_C.RESET}")
        except Exception as e:
            print(f"{_C.RED}✗ Sync send error: {e}{_C.RESET}")

    # ------------------------------------------------------------------
    # _link_build_snapshot — export brain as JSON snapshot
    # ------------------------------------------------------------------
    def _link_build_snapshot(self) -> dict:
        """Build a snapshot of the brain's knowledge for export/import."""
        return {
            "peer_name": getattr(self, 'peer_name', 'Diamond'),
            "facts": self._load(self._facts_path),
            "agents": self._load(self._agents_path),
            "escalations": self._load(self._escalations_path),
            "exported_at": _now_iso(),
        }

    # ------------------------------------------------------------------
    # _tls_send_facts — send our facts via socket with length prefix
    # ------------------------------------------------------------------
    def _tls_send_facts(self, sock: socket.socket, peer_ip: str) -> None:
        """Send all facts to peer using length-prefixed framing."""
        facts = self._load(self._facts_path)
        payload = json.dumps({
            "type": "FACTS_SEND",
            "facts": facts,
            "peer_name": getattr(self, 'peer_name', 'Diamond'),
        }).encode("utf-8")

        # Send length prefix (4 bytes, big-endian)
        length = len(payload)
        sock.send(length.to_bytes(4, 'big') + payload)

    # ------------------------------------------------------------------
    # _tls_recv_facts — receive and merge facts from peer via socket
    # ------------------------------------------------------------------
    def _tls_recv_facts(self, sock: socket.socket, peer_ip: str) -> None:
        """Receive facts from peer and merge them (length-prefixed)."""
        try:
            # Read 4-byte length prefix
            length_bytes = sock.recv(4)
            if len(length_bytes) < 4:
                return

            length = int.from_bytes(length_bytes, 'big')

            # Read exact number of bytes
            data = b""
            while len(data) < length:
                chunk = sock.recv(min(4096, length - len(data)))
                if not chunk:
                    break
                data += chunk

            if data:
                msg = json.loads(data.decode("utf-8"))
                if msg.get("type") == "FACTS_SEND":
                    peer_facts = msg.get("facts", [])
                    self._merge_facts(peer_facts)
        except Exception as e:
            print(f"{_C.RED}✗ Error receiving facts: {e}{_C.RESET}")

    # ------------------------------------------------------------------
    # _link_recv_snapshot — receive and import snapshot from peer
    # ------------------------------------------------------------------
    def _link_recv_snapshot(self, sock: socket.socket, peer_ip: str) -> None:
        """Receive SYNC_DATA snapshot from peer and merge it."""
        try:
            # Read 4-byte length prefix
            length_bytes = sock.recv(4)
            if len(length_bytes) < 4:
                print(f"{_C.RED}✗ No data from peer{_C.RESET}")
                return

            length = int.from_bytes(length_bytes, 'big')

            # Read exact number of bytes
            data = b""
            while len(data) < length:
                chunk = sock.recv(min(4096, length - len(data)))
                if not chunk:
                    break
                data += chunk

            if data:
                msg = json.loads(data.decode("utf-8"))
                if msg.get("type") in ("SYNC_DATA", "SYNC_RESPONSE"):
                    raw_facts = msg.get("facts") or msg.get("snapshot", {}).get("facts", [])
                    # Derive a source label from the peer NIC fingerprint if available
                    peer_fp = getattr(self, '_peer_nic', {}).get("fingerprint", peer_ip)
                    valid_facts, issues = validate_facts_batch(raw_facts, source_label=peer_fp)
                    if issues:
                        for issue in issues:
                            print(f"{_C.YELLOW}  schema: {issue}{_C.RESET}")
                    self._merge_facts(valid_facts)
                    print(f"{_C.GREEN}✓ Sync complete{_C.RESET}")
        except Exception as e:
            print(f"{_C.RED}✗ Error receiving sync: {e}{_C.RESET}")

    # ------------------------------------------------------------------
    # _link_import_snapshot — import facts from a snapshot
    # ------------------------------------------------------------------
    def _link_import_snapshot(self, snapshot: dict) -> None:
        """Import facts from a snapshot (local or from peer)."""
        peer_facts = snapshot.get("facts", [])
        self._merge_facts(peer_facts)

    # ------------------------------------------------------------------
    # _merge_facts — merge peer facts into our database
    # ------------------------------------------------------------------
    def _merge_facts(self, peer_facts: list) -> None:
        """Merge peer facts, keeping highest confidence version."""
        facts = self._load(self._facts_path)
        merged = 0

        for peer_fact in peer_facts:
            existing = None
            for local_fact in facts:
                if (local_fact.get("topic", "").lower() ==
                    peer_fact.get("topic", "").lower() and
                    local_fact.get("fact", "") == peer_fact.get("fact", "")):
                    existing = local_fact
                    break

            if existing:
                # Keep higher confidence
                if peer_fact.get("confidence", 0) > existing.get("confidence", 0):
                    existing.update(peer_fact)
                    merged += 1
            else:
                # New fact
                facts.append(peer_fact)
                merged += 1

        self._save(self._facts_path, facts)
        print(f"{_C.GREEN}  Merged {merged} facts{_C.RESET}")


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
