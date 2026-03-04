#!/usr/bin/env python3
"""
Diamond NetBlade -- Sentinel Auditor v1.0
Three-tier automated code audit pipeline:
  Tier 1: Pattern scan (free, instant)
  Tier 2: Local LLM via LM Studio (cheap, per-file)
  Tier 3: Claude escalation (expensive, cross-file)

Brain: Diamond Brain caches findings between runs.

Usage:
  python sentinel_audit.py [options]
    --tier 1|2|3|all    Run specific tier (default: all)
    --target PATH       Target directory (default: project root)
    --verbose           Show detailed output
    --brain-status      Show Diamond Brain digest and exit
    --skip-cache        Ignore brain cache, re-audit everything
    --output FILE       Save report to file (default: stdout)

Windows-native. No bash dependency. Uses pathlib for all paths.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO

# ---------------------------------------------------------------------------
# Resolve project root and wire up brain import
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
BRAIN_DIR = SCRIPT_DIR / "brain"

sys.path.insert(0, str(SCRIPT_DIR))

try:
    from brain.diamond_brain import DiamondBrain
except ImportError:
    # Fallback: if the import path differs, try direct import
    try:
        sys.path.insert(0, str(BRAIN_DIR))
        from diamond_brain import DiamondBrain
    except ImportError:
        DiamondBrain = None  # type: ignore[misc,assignment]

# ---------------------------------------------------------------------------
# HTTP client -- prefer requests, fall back to urllib
# ---------------------------------------------------------------------------
try:
    import requests as _requests

    def _http_post(url: str, payload: dict, timeout: float = 120.0) -> dict:
        resp = _requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        return resp.json()

except ImportError:
    import urllib.request
    import urllib.error

    def _http_post(url: str, payload: dict, timeout: float = 120.0) -> dict:  # type: ignore[misc]
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))


# ---------------------------------------------------------------------------
# ANSI colour helpers -- degrade on dumb terminals
# ---------------------------------------------------------------------------
_COLOR_ENABLED = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None

class _C:
    """ANSI escape sequences. All resolve to empty strings when colour is off."""
    RESET   = "\033[0m"   if _COLOR_ENABLED else ""
    BOLD    = "\033[1m"   if _COLOR_ENABLED else ""
    DIM     = "\033[2m"   if _COLOR_ENABLED else ""
    RED     = "\033[91m"  if _COLOR_ENABLED else ""
    YELLOW  = "\033[93m"  if _COLOR_ENABLED else ""
    GREEN   = "\033[92m"  if _COLOR_ENABLED else ""
    CYAN    = "\033[96m"  if _COLOR_ENABLED else ""
    MAGENTA = "\033[95m"  if _COLOR_ENABLED else ""
    WHITE   = "\033[97m"  if _COLOR_ENABLED else ""
    BLUE    = "\033[94m"  if _COLOR_ENABLED else ""

# Severity -> colour mapping
_SEV_COLOR = {
    "CRITICAL": _C.RED,
    "HIGH":     _C.YELLOW,
    "MEDIUM":   _C.CYAN,
    "LOW":      _C.GREEN,
    "PASS":     _C.GREEN,
}

BANNER = f"""{_C.CYAN}{_C.BOLD}
    ___  _                                _   _   _      _   ____  _           _
   / _ \\(_) __ _ _ __ ___   ___  _ __   __| | | \\ | | ___| |_| __ )| | __ _  __| | ___
  / /_\\// |/ _` | '_ ` _ \\ / _ \\| '_ \\ / _` | |  \\| |/ _ \\ __|  _ \\| |/ _` |/ _` |/ _ \\
 / /_\\\\ | | (_| | | | | | | (_) | | | | (_| | | |\\  |  __/ |_| |_) | | (_| | (_| |  __/
 \\____/_|_|\\__,_|_| |_| |_|\\___/|_| |_|\\__,_| |_| \\_|\\___|\\__|____/|_|\\__,_|\\__,_|\\___|
{_C.RESET}
{_C.MAGENTA}{_C.BOLD}  SENTINEL AUDITOR v1.0{_C.RESET}{_C.DIM}  //  Three-Tier Code Audit Pipeline{_C.RESET}
{_C.BLUE}  ======================================================================{_C.RESET}
"""


# ===========================================================================
#  UTILITY FUNCTIONS
# ===========================================================================

def _sev_label(severity: str) -> str:
    """Coloured severity badge."""
    c = _SEV_COLOR.get(severity.upper(), _C.WHITE)
    return f"{c}[{severity.upper()}]{_C.RESET}"


def _relative(path: Path) -> str:
    """Show path relative to project root for readability."""
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _file_hash(filepath: Path) -> str:
    """Quick SHA-256 prefix for change detection."""
    try:
        return hashlib.sha256(filepath.read_bytes()).hexdigest()[:16]
    except OSError:
        return "unknown"


def _collect_rs_files(target: Path) -> List[Path]:
    """Walk *target* and return all .rs files, sorted by path."""
    rs_files: List[Path] = []
    for dirpath, _dirnames, filenames in os.walk(target):
        for fn in filenames:
            if fn.endswith(".rs"):
                rs_files.append(Path(dirpath) / fn)
    rs_files.sort()
    return rs_files


def _is_test_file(filepath: Path) -> bool:
    """Heuristic: file lives under a test/ directory or has 'test' in name."""
    parts_lower = [p.lower() for p in filepath.parts]
    if any(p in ("test", "tests", "test_utils") for p in parts_lower):
        return True
    if filepath.stem.startswith("test_") or filepath.stem.endswith("_test"):
        return True
    return False


def _read_lines(filepath: Path) -> List[str]:
    """Read a file into a list of lines. Returns empty list on failure."""
    try:
        return filepath.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []


# ===========================================================================
#  TIER 1 -- PATTERN SCANNER (Python, no bash dependency)
# ===========================================================================

# Each rule: (pattern_regex, category, severity, message_template, skip_tests)
# pattern_regex operates on a single line of source code.
_TIER1_RULES: List[tuple] = [
    # --- Dangerous panics ---
    (
        re.compile(r"\.unwrap\(\)"),
        "unwrap",
        "HIGH",
        ".unwrap() call -- will panic on None/Err",
        True,  # skip test files
    ),
    (
        re.compile(r"\.expect\("),
        "expect",
        "MEDIUM",
        ".expect() call -- will panic with message on None/Err",
        True,
    ),
    (
        re.compile(r"\bpanic!\s*\("),
        "panic",
        "HIGH",
        "panic! macro -- hard crash",
        True,
    ),
    # --- Performance ---
    (
        re.compile(r"\.remove\(\s*0\s*\)"),
        "vec_remove_zero",
        "MEDIUM",
        ".remove(0) is O(n) on Vec -- consider VecDeque::pop_front()",
        False,
    ),
    # --- Memory safety ---
    # HashMap/HashSet inside struct fields without capacity mention
    # (matched contextually below, not as a simple line regex)

    # --- String allocations in loops ---
    (
        re.compile(r"String::from\s*\(|format!\s*\("),
        "loop_allocation",
        "MEDIUM",
        "String allocation (String::from / format!) potentially inside loop",
        False,
    ),
]


def _check_unsafe_indexing(line: str, prev_line: str) -> bool:
    """Heuristic: [variable_name] that is not a numeric literal and not
    preceded by .get / len() / bounds checks on the prior line."""
    # Match something[variable] but not something[0], something[1], etc.
    if not re.search(r"\[\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\]", line):
        return False
    # Exclude numeric-only indices
    if re.search(r"\[\s*\d+\s*\]", line):
        return False
    # Exclude known safe patterns on current or previous line
    safe = re.compile(r"\.get\(|\.get_mut\(|len\(\)|\.contains|assert|bounds|checked|\.iter\(\)|impl\s+Index|type\s|use\s|mod\s|//|///")
    if safe.search(line) or safe.search(prev_line):
        return False
    # Exclude attribute macros, derive, etc.
    if line.strip().startswith("#[") or line.strip().startswith("//"):
        return False
    return True


def _check_hashmap_in_struct(lines: List[str]) -> List[Dict[str, Any]]:
    """Find HashMap/HashSet fields inside struct definitions without capacity bounds."""
    findings: List[Dict[str, Any]] = []
    in_struct = False
    struct_name = ""
    brace_depth = 0

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Detect struct opening
        struct_match = re.match(r"(?:pub\s+)?struct\s+(\w+)", stripped)
        if struct_match and "{" in line:
            in_struct = True
            struct_name = struct_match.group(1)
            brace_depth = line.count("{") - line.count("}")
            continue
        elif struct_match and i + 1 < len(lines) and "{" in lines[i + 1]:
            in_struct = True
            struct_name = struct_match.group(1)
            brace_depth = 0
            continue

        if in_struct:
            brace_depth += line.count("{") - line.count("}")
            if brace_depth <= 0:
                in_struct = False
                continue

            if re.search(r"HashMap\s*<|HashSet\s*<", line):
                # Check surrounding context for capacity docs
                context = " ".join(lines[max(0, i - 2) : i + 2])
                if not re.search(r"with_capacity|bounded|max_size|capacity|limit|// bounded", context, re.IGNORECASE):
                    findings.append({
                        "line": i + 1,
                        "message": f"HashMap/HashSet field without capacity bounds in struct {struct_name}",
                        "code_snippet": stripped,
                    })
    return findings


def _check_u16_arithmetic(line: str) -> bool:
    """Heuristic: u16 value in arithmetic without saturating_ prefix."""
    # Look for patterns like: variable + 1, variable - 1, cast as u16 then add
    if "u16" not in line:
        return False
    # Must have arithmetic operator
    if not re.search(r"[+\-\*]", line):
        return False
    # Already using saturating?
    if "saturating_" in line or "checked_" in line or "wrapping_" in line:
        return False
    # Skip type declarations, use statements, comments
    stripped = line.strip()
    if stripped.startswith("//") or stripped.startswith("///") or stripped.startswith("use "):
        return False
    if re.search(r":\s*u16", stripped) and not re.search(r"[+\-\*]", stripped.split(":")[-1]):
        return False
    return True


def _check_missing_keypress(filepath: Path, lines: List[str]) -> Optional[Dict[str, Any]]:
    """Check if a file handles keyboard events but misses KeyEventKind::Press."""
    # Only check files that look like input/event handlers
    name_lower = filepath.stem.lower()
    content_joined = "\n".join(lines[:200])  # scan first 200 lines for patterns

    has_key_handling = bool(
        re.search(r"KeyCode::|KeyEvent|fn\s+\w*(?:input|event|key|handle)\w*", content_joined)
    )
    if not has_key_handling:
        return None

    has_press_filter = "KeyEventKind::Press" in "\n".join(lines)
    if has_press_filter:
        return None

    return {
        "line": 1,
        "message": "File handles key events but does not filter on KeyEventKind::Press (Windows double-fire bug)",
        "code_snippet": "(whole-file check)",
    }


def _is_inside_loop(lines: List[str], line_idx: int, lookback: int = 15) -> bool:
    """Rough heuristic: is line_idx inside a for/while/loop block?"""
    brace_depth = 0
    start = max(0, line_idx - lookback)
    for i in range(line_idx - 1, start - 1, -1):
        stripped = lines[i].strip()
        brace_depth += stripped.count("}") - stripped.count("{")
        if brace_depth < 0:
            # We entered a block -- check if it is a loop
            if re.match(r"(for|while|loop)\b", stripped):
                return True
            brace_depth = 0
    return False


def tier1_scan(
    target: Path,
    verbose: bool = False,
    out: TextIO = sys.stdout,
) -> List[Dict[str, Any]]:
    """Tier 1: Pattern scanner. Returns list of finding dicts."""
    findings: List[Dict[str, Any]] = []
    scan_dirs = []

    # Collect directories to scan
    crates_dir = target / "crates"
    src_dir = target / "src"
    if crates_dir.is_dir():
        scan_dirs.append(crates_dir)
    if src_dir.is_dir():
        scan_dirs.append(src_dir)
    if not scan_dirs:
        scan_dirs.append(target)

    rs_files: List[Path] = []
    for d in scan_dirs:
        rs_files.extend(_collect_rs_files(d))

    if verbose:
        out.write(f"  {_C.DIM}Tier 1: scanning {len(rs_files)} .rs files...{_C.RESET}\n")

    for filepath in rs_files:
        lines = _read_lines(filepath)
        if not lines:
            continue

        is_test = _is_test_file(filepath)
        rel = _relative(filepath)

        # --- Regex-based rules ---
        for rule_re, category, severity, msg_template, skip_tests in _TIER1_RULES:
            if skip_tests and is_test:
                continue

            for i, line in enumerate(lines):
                stripped = line.strip()
                # Skip comments
                if stripped.startswith("//") or stripped.startswith("///"):
                    continue

                if rule_re.search(line):
                    # Special handling: loop_allocation only counts inside loops
                    if category == "loop_allocation":
                        if not _is_inside_loop(lines, i):
                            continue

                    findings.append({
                        "category": category,
                        "severity": severity,
                        "file": rel,
                        "line": i + 1,
                        "message": msg_template,
                        "code_snippet": stripped[:120],
                    })

        # --- Unsafe array indexing ---
        if not is_test:
            prev_line = ""
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith("//"):
                    prev_line = stripped
                    continue
                if _check_unsafe_indexing(stripped, prev_line):
                    findings.append({
                        "category": "unsafe_indexing",
                        "severity": "CRITICAL",
                        "file": rel,
                        "line": i + 1,
                        "message": "Potential unsafe array indexing without bounds check",
                        "code_snippet": stripped[:120],
                    })
                prev_line = stripped

        # --- HashMap/HashSet in structs ---
        for hit in _check_hashmap_in_struct(lines):
            findings.append({
                "category": "unbounded_hashmap",
                "severity": "HIGH",
                "file": rel,
                "line": hit["line"],
                "message": hit["message"],
                "code_snippet": hit["code_snippet"],
            })

        # --- u16 arithmetic without saturating ---
        if not is_test:
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith("//"):
                    continue
                if _check_u16_arithmetic(stripped):
                    findings.append({
                        "category": "u16_arithmetic",
                        "severity": "HIGH",
                        "file": rel,
                        "line": i + 1,
                        "message": "u16 arithmetic without saturating_add/saturating_sub",
                        "code_snippet": stripped[:120],
                    })

        # --- Missing KeyEventKind::Press ---
        kp_hit = _check_missing_keypress(filepath, lines)
        if kp_hit:
            findings.append({
                "category": "missing_keypress_filter",
                "severity": "MEDIUM",
                "file": rel,
                "line": kp_hit["line"],
                "message": kp_hit["message"],
                "code_snippet": kp_hit["code_snippet"],
            })

    return findings


# ===========================================================================
#  TIER 1.5 -- BINARY TRUTH FILTER (fast local LLM triage)
# ===========================================================================
#
#  Instead of sending whole files to the LLM (slow, context-heavy), we ask
#  binary yes/no questions about each Tier 1 finding.  The LLM replies with
#  just "1" (real issue) or "0" (false positive).
#
#  ~2 seconds per question vs ~80 seconds per file.
#  Reduces 120 findings → ~30 real ones before the expensive Tier 2 pass.
#

TRUTH_ENGINE_URL = "http://localhost:1234/v1/chat/completions"

# ---------------------------------------------------------------------------
# Model identifiers -- loaded via `lms load --identifier <name>`
#   sentinel-fast  = Ministral-3-3B  (speed demon, 0.1s/question, Tier 1.5)
#   reasoner     = DeepSeek-R1-8B  (thinking model, ~55s/file, Tier 2)
# ---------------------------------------------------------------------------
TRUTH_MODEL = "sentinel-fast"      # Fast non-thinking model for binary triage
TIER2_MODEL = "reasoner"         # Reasoning model for deep file analysis

TRUTH_SYSTEM = (
    "You are a Rust code safety auditor. Reply ONLY 0 or 1.\n"
    "0 = false positive. 1 = real issue.\n\n"
    "RULES:\n"
    "- .unwrap() after .is_some()/.is_ok() → 0\n"
    "- .expect() in main() or init → 0\n"
    "- panic! in wildcard _ arm when all enum variants are already matched → 0\n"
    "- .unwrap() without any guard → 1\n"
    "- Unbounded collection in infinite loop → 1\n"
    "- O(n) operation in render/tick → 1\n\n"
    "Examples:\n"
    "Code: if x.is_some() { x.unwrap(); }\n"
    "Q: dangerous? A: 0\n\n"
    "Code: list.first().unwrap();\n"
    "Q: dangerous? A: 1\n\n"
    "Code: match d { Variant1 => .., Variant2 => .., _ => panic!(\"impossible\") }\n"
    "Q: reachable panic? A: 0\n\n"
    "Code: fn main() { f().expect(\"err\"); }\n"
    "Q: dangerous expect? A: 0\n\n"
    "Reply ONLY 0 or 1. No other text."
)

# Map finding categories to focused yes/no questions
_TRUTH_QUESTIONS: Dict[str, str] = {
    "unwrap": "Is this .unwrap() call reachable with a None/Err value at runtime (not in a test, not after a guaranteed-Some check)?",
    "unsafe_indexing": "Is this array/slice indexing actually unsafe? Could the index be out of bounds at runtime? (Ignore if the index is a constant, or if bounds are checked within 3 lines above.)",
    "unbounded_hashmap": "Is this HashMap/HashSet truly unbounded — could it grow without limit in production? (Ignore if the struct is short-lived, test-only, or has documented capacity limits nearby.)",
    "u16_arithmetic": "Is this u16 arithmetic actually at risk of overflow? (Ignore if it is just a type annotation, a from_le_bytes call, or inside a function signature.)",
    "expect": "Is this .expect() call in production code that could panic under normal conditions? (Ignore if it is in a test, CLI setup, or one-time initialization.)",
    "panic": "Is this panic! macro reachable in normal program flow? (Ignore if it is in a test, unreachable branch, or debug assertion.)",
    "loop_allocations": "Is this String allocation actually inside a hot loop? (Ignore if the loop runs fewer than ~100 iterations or is not in a render/tick path.)",
    "vec_remove_zero": "Is this .remove(0) actually called in a hot path where O(n) matters?",
    "missing_keypress_filter": "Does this input handler actually process key events without filtering for KeyEventKind::Press?",
    "missing_saturating": "Is this arithmetic on a u16 variable that could realistically overflow at runtime?",
}


def _ask_truth(question: str, code_snippet: str, timeout: float = 30.0) -> Optional[bool]:
    """Ask the local LLM a binary yes/no question. Returns True (real), False (FP), or None (error)."""
    payload = {
        "model": TRUTH_MODEL,
        "messages": [
            {"role": "system", "content": TRUTH_SYSTEM},
            {"role": "user", "content": f"Code: {code_snippet}\nQ: {question}\nA:"},
        ],
        "temperature": 0.0,
        # Ministral-3-3B replies with a single digit — 4 tokens is plenty.
        "max_tokens": 4,
    }
    try:
        resp = _http_post(TRUTH_ENGINE_URL, payload, timeout=timeout)
        msg = resp.get("choices", [{}])[0].get("message", {})
        raw = msg.get("content", "").strip()
        # Extract just the digit from visible content
        for ch in raw:
            if ch in ("0", "1"):
                return ch == "1"
        # Fallback: check reasoning_content (DeepSeek R1 sometimes puts answer there)
        reasoning = msg.get("reasoning_content", "")
        if reasoning:
            # Look for final verdict in reasoning — last digit mentioned
            last_digit = None
            for ch in reasoning:
                if ch in ("0", "1"):
                    last_digit = ch
            if last_digit is not None:
                return last_digit == "1"
        return None  # Could not parse
    except Exception:
        return None  # LLM unreachable, keep the finding


def _get_code_context(filepath: Path, line_num: int, context_lines: int = 5) -> str:
    """Extract a few lines of code around a finding for the truth engine."""
    try:
        abs_path = PROJECT_ROOT / filepath if not filepath.is_absolute() else filepath
        lines = abs_path.read_text(encoding="utf-8", errors="replace").splitlines()
        start = max(0, line_num - context_lines - 1)
        end = min(len(lines), line_num + context_lines)
        snippet_lines = []
        for i in range(start, end):
            marker = ">>>" if i == line_num - 1 else "   "
            snippet_lines.append(f"{marker} {i + 1:4d} | {lines[i]}")
        return "\n".join(snippet_lines)
    except Exception:
        return "(code not available)"


def tier1_5_truth_filter(
    tier1_findings: List[Dict[str, Any]],
    verbose: bool = False,
    out: TextIO = sys.stdout,
) -> List[Dict[str, Any]]:
    """Filter Tier 1 findings using binary yes/no questions to local LLM.

    Returns only the findings the LLM confirms as real issues.
    """
    if not tier1_findings:
        return []

    # Quick connectivity check
    try:
        _http_post(
            TRUTH_ENGINE_URL,
            {"model": TRUTH_MODEL, "messages": [{"role": "user", "content": "1"}], "max_tokens": 1},
            timeout=5.0,
        )
    except Exception:
        out.write(f"  {_C.YELLOW}[SKIP]{_C.RESET} LM Studio not reachable — keeping all Tier 1 findings\n")
        return tier1_findings

    confirmed: List[Dict[str, Any]] = []
    filtered_out = 0
    errors = 0

    out.write(f"  {_C.DIM}Filtering {len(tier1_findings)} findings via binary truth engine...{_C.RESET}\n")

    for i, finding in enumerate(tier1_findings):
        category = finding.get("category", "")
        question = _TRUTH_QUESTIONS.get(category)
        if question is None:
            # No truth question for this category — keep it
            confirmed.append(finding)
            continue

        line_num = finding.get("line", 0)
        filepath = Path(finding.get("file", ""))
        snippet = _get_code_context(filepath, line_num)

        verdict = _ask_truth(question, snippet)

        if verdict is None:
            errors += 1
            confirmed.append(finding)  # On error, keep the finding
        elif verdict:
            confirmed.append(finding)
            if verbose:
                out.write(f"    {_C.RED}[REAL]{_C.RESET} {filepath}:{line_num} {category}\n")
        else:
            filtered_out += 1
            if verbose:
                out.write(f"    {_C.GREEN}[FP]{_C.RESET}   {filepath}:{line_num} {category}\n")

        # Progress indicator every 20 findings
        if (i + 1) % 20 == 0:
            out.write(f"  {_C.DIM}  ...{i + 1}/{len(tier1_findings)} checked{_C.RESET}\n")
            out.flush()

    out.write(
        f"  {_C.BOLD}Truth filter:{_C.RESET} "
        f"{_C.GREEN}{filtered_out} false positives removed{_C.RESET}, "
        f"{_C.YELLOW}{len(confirmed)} confirmed{_C.RESET}"
    )
    if errors:
        out.write(f", {_C.RED}{errors} errors{_C.RESET}")
    out.write("\n")

    return confirmed


# ===========================================================================
#  TIER 2 -- LOCAL LLM AUDIT (LM Studio / OpenAI-compatible)
# ===========================================================================

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"

TIER2_SYSTEM_PROMPT = (
    "You are a Rust code auditor. Analyze this file for:\n"
    "1. Potential panics (unwrap, expect, indexing without bounds check)\n"
    "2. Memory safety (unbounded collections, leaks)\n"
    "3. Performance (unnecessary allocations in hot paths, O(n) where O(1) possible)\n"
    "4. Windows compatibility (u16 overflow, terminal handling)\n"
    "5. Error handling (unhandled Results, silent failures)\n\n"
    "Respond ONLY with a JSON array of finding objects. Each object must have:\n"
    '  {"category": "...", "severity": "CRITICAL|HIGH|MEDIUM|LOW", '
    '"line": <number or null>, "message": "..."}\n'
    "If no issues are found, respond with an empty array: []\n"
    "Do NOT include any text outside the JSON array."
)


def _call_lm_studio(filepath: Path, content: str, timeout: float = 120.0) -> List[Dict[str, Any]]:
    """Send a single file to LM Studio for analysis. Returns parsed findings."""
    # Truncate content to ~2500 tokens (~10000 chars) to stay within context window
    max_chars = 10000
    if len(content) > max_chars:
        content = content[:max_chars] + "\n// ... (truncated for analysis)\n"
    user_msg = f"File: {filepath.name}\n\n```rust\n{content}\n```"

    payload = {
        "model": TIER2_MODEL,
        "messages": [
            {"role": "system", "content": TIER2_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        "temperature": 0.1,
        "max_tokens": 2048,
    }

    resp = _http_post(LM_STUDIO_URL, payload, timeout=timeout)
    raw = resp.get("choices", [{}])[0].get("message", {}).get("content", "")

    # Try to extract JSON array from the response
    # The LLM might wrap it in markdown code fences
    raw = raw.strip()
    if raw.startswith("```"):
        # Strip code fences
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        raw = raw.strip()

    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [
                {
                    "category": f.get("category", "llm_finding"),
                    "severity": f.get("severity", "MEDIUM").upper(),
                    "line": f.get("line"),
                    "message": f.get("message", "(no message)"),
                }
                for f in parsed
                if isinstance(f, dict)
            ]
    except (json.JSONDecodeError, TypeError):
        pass

    return []


def tier2_llm_audit(
    target: Path,
    tier1_findings: List[Dict[str, Any]],
    brain: Optional[Any],
    verbose: bool = False,
    skip_cache: bool = False,
    out: TextIO = sys.stdout,
) -> List[Dict[str, Any]]:
    """Tier 2: Send files with Tier 1 findings to local LLM for deeper analysis."""
    findings: List[Dict[str, Any]] = []

    # Determine which files had Tier 1 hits
    files_with_issues = sorted(set(f["file"] for f in tier1_findings))
    if not files_with_issues:
        out.write(f"  {_C.GREEN}No Tier 1 findings -- Tier 2 has nothing to escalate.{_C.RESET}\n")
        return findings

    if verbose:
        out.write(f"  {_C.DIM}Tier 2: {len(files_with_issues)} files to analyze via LM Studio...{_C.RESET}\n")

    # Check LM Studio connectivity first
    try:
        _http_post(
            LM_STUDIO_URL,
            {
                "model": TIER2_MODEL,
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 1,
            },
            timeout=5.0,
        )
    except Exception:
        out.write(
            f"  {_C.YELLOW}[SKIP]{_C.RESET} LM Studio not reachable at {LM_STUDIO_URL}\n"
            f"  {_C.DIM}Start LM Studio and load a model to enable Tier 2 analysis.{_C.RESET}\n"
        )
        return findings

    for rel_path in files_with_issues:
        abs_path = PROJECT_ROOT / rel_path

        # Brain cache check
        if brain and not skip_cache:
            try:
                if brain._audit_cache and hasattr(brain, "is_cached"):
                    # Brain has a file-level cache -- use it
                    if brain.is_cached(abs_path):
                        if verbose:
                            out.write(f"    {_C.DIM}[cached] {rel_path}{_C.RESET}\n")
                        continue
                else:
                    # Fallback: check facts for a recent audit entry
                    cache_key = f"tier2:{rel_path}"
                    existing = brain.recall(cache_key)
                    if existing:
                        # Check if we have recall-based entries (list-style brain)
                        if isinstance(existing, list) and existing:
                            entry = existing[0]
                            # If updated_at < 24h, skip
                            ts = entry.get("updated_at") or entry.get("created_at")
                            if ts:
                                from datetime import datetime as _dt
                                try:
                                    cached_dt = _dt.fromisoformat(ts)
                                    if cached_dt.tzinfo is None:
                                        cached_dt = cached_dt.replace(tzinfo=timezone.utc)
                                    age_h = (datetime.now(timezone.utc) - cached_dt).total_seconds() / 3600
                                    current_hash = _file_hash(abs_path)
                                    old_hash = entry.get("fact", "")
                                    if age_h < 24 and current_hash in old_hash:
                                        if verbose:
                                            out.write(f"    {_C.DIM}[cached] {rel_path}{_C.RESET}\n")
                                        continue
                                except (ValueError, TypeError):
                                    pass
            except Exception:
                pass  # Brain errors should never block audit

        if not abs_path.is_file():
            continue

        content = abs_path.read_text(encoding="utf-8", errors="replace")

        out.write(f"    {_C.CYAN}Analyzing:{_C.RESET} {rel_path} ... ")
        out.flush()

        try:
            t0 = time.time()
            llm_findings = _call_lm_studio(abs_path, content)
            elapsed = time.time() - t0

            for f in llm_findings:
                f["file"] = rel_path
                f["code_snippet"] = "(LLM analysis)"
                f["source"] = "tier2_llm"
                findings.append(f)

            count = len(llm_findings)
            if count > 0:
                out.write(f"{_C.YELLOW}{count} issue(s){_C.RESET} ({elapsed:.1f}s)\n")
            else:
                out.write(f"{_C.GREEN}clean{_C.RESET} ({elapsed:.1f}s)\n")

            # Cache to brain
            if brain:
                try:
                    if hasattr(brain, "cache_audit"):
                        brain.cache_audit(abs_path, llm_findings)
                    else:
                        cache_key = f"tier2:{rel_path}"
                        brain.learn(
                            topic=cache_key,
                            fact=f"hash={_file_hash(abs_path)} findings={count}",
                            confidence=90,
                            source="sentinel-auditor-tier2",
                        )
                except Exception:
                    pass

        except Exception as exc:
            out.write(f"{_C.RED}ERROR: {exc}{_C.RESET}\n")

    return findings


# ===========================================================================
#  TIER 3 -- CLAUDE ESCALATION (report generation, no API call)
# ===========================================================================

def tier3_escalation(
    all_findings: List[Dict[str, Any]],
    brain: Optional[Any],
    verbose: bool = False,
    out: TextIO = sys.stdout,
) -> List[Dict[str, Any]]:
    """Tier 3: Generate escalation report for issues that need Claude review.

    Criteria: severity >= HIGH AND brain has no existing knowledge on the topic.
    Does NOT call Claude API -- generates a report for human/Claude Code review.
    """
    escalations: List[Dict[str, Any]] = []

    for finding in all_findings:
        severity = finding.get("severity", "").upper()
        if severity not in ("HIGH", "CRITICAL"):
            continue

        category = finding.get("category", "unknown")

        # Check if brain already knows about this category
        if brain:
            try:
                existing = brain.recall(category)
                if existing:
                    # List-style brain: non-empty list means we have knowledge
                    if isinstance(existing, list) and len(existing) > 0:
                        continue
                    # Dict-style brain: truthy means we have knowledge
                    elif existing:
                        continue
            except Exception:
                pass

        escalations.append({
            "category": category,
            "severity": severity,
            "file": finding.get("file", "?"),
            "line": finding.get("line", "?"),
            "message": finding.get("message", ""),
            "code_snippet": finding.get("code_snippet", ""),
            "reason": f"No brain knowledge on '{category}' and severity is {severity}",
            "needs_cross_file_analysis": severity == "CRITICAL",
        })

    # Deduplicate by (category, file) -- keep first occurrence
    seen = set()
    unique: List[Dict[str, Any]] = []
    for esc in escalations:
        key = (esc["category"], esc["file"])
        if key not in seen:
            seen.add(key)
            unique.append(esc)
    escalations = unique

    # Save escalations to brain memory
    if escalations:
        esc_path = BRAIN_DIR / "memory" / "escalations.json"
        esc_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing escalations
        existing_esc: List[Dict[str, Any]] = []
        if esc_path.exists():
            try:
                existing_esc = json.loads(esc_path.read_text(encoding="utf-8"))
                if not isinstance(existing_esc, list):
                    existing_esc = []
            except (json.JSONDecodeError, OSError):
                existing_esc = []

        # Append new escalations with timestamp
        now = datetime.now(timezone.utc).isoformat()
        for esc in escalations:
            esc["escalated_at"] = now
            esc["resolved"] = False

        existing_esc.extend(escalations)
        esc_path.write_text(
            json.dumps(existing_esc, indent=2, default=str),
            encoding="utf-8",
        )

        # Also record via brain API if available
        if brain and hasattr(brain, "add_escalation"):
            for esc in escalations:
                try:
                    brain.add_escalation(esc)
                except Exception:
                    pass

    return escalations


# ===========================================================================
#  OUTPUT FORMATTING
# ===========================================================================

def _print_findings(
    findings: List[Dict[str, Any]],
    tier_label: str,
    verbose: bool,
    out: TextIO,
) -> None:
    """Print findings for a single tier."""
    if not findings:
        out.write(f"  {_C.GREEN}[PASS]{_C.RESET} {tier_label}: No issues found.\n")
        return

    out.write(f"\n  {_C.BOLD}{tier_label}: {len(findings)} issue(s){_C.RESET}\n")
    out.write(f"  {_C.BLUE}{'=' * 60}{_C.RESET}\n")

    # Group by file
    by_file: Dict[str, List[Dict[str, Any]]] = {}
    for f in findings:
        by_file.setdefault(f["file"], []).append(f)

    for filepath in sorted(by_file.keys()):
        file_findings = by_file[filepath]
        out.write(f"\n  {_C.WHITE}{_C.BOLD}{filepath}{_C.RESET}\n")

        for f in sorted(file_findings, key=lambda x: x.get("line", 0)):
            sev = _sev_label(f["severity"])
            line = f.get("line", "?")
            msg = f["message"]
            out.write(f"    {sev} L{line}: {msg}\n")

            if verbose and f.get("code_snippet") and f["code_snippet"] != "(whole-file check)":
                out.write(f"      {_C.DIM}{f['code_snippet']}{_C.RESET}\n")


def _print_escalations(
    escalations: List[Dict[str, Any]],
    out: TextIO,
) -> None:
    """Print Tier 3 escalation report."""
    if not escalations:
        out.write(f"\n  {_C.GREEN}[PASS]{_C.RESET} Tier 3: No escalations needed.\n")
        return

    out.write(f"\n  {_C.RED}{_C.BOLD}TIER 3 ESCALATIONS -- Needs Claude / Human Review{_C.RESET}\n")
    out.write(f"  {_C.RED}{'=' * 60}{_C.RESET}\n")

    for esc in escalations:
        sev = _sev_label(esc["severity"])
        out.write(
            f"    {sev} {esc['file']}:L{esc['line']} -- {esc['message']}\n"
            f"      {_C.DIM}Reason: {esc['reason']}{_C.RESET}\n"
        )

    esc_path = BRAIN_DIR / "memory" / "escalations.json"
    out.write(f"\n  {_C.DIM}Escalations saved to: {esc_path}{_C.RESET}\n")


def _print_summary(
    tier_results: Dict[str, Dict[str, Any]],
    brain: Optional[Any],
    out: TextIO,
) -> None:
    """Print final summary table."""
    out.write(f"\n{_C.BOLD}{_C.BLUE}  AUDIT SUMMARY{_C.RESET}\n")
    out.write(f"  {_C.BLUE}{'=' * 60}{_C.RESET}\n\n")

    # Table header
    out.write(f"  {_C.BOLD}{'Tier':<12} {'Issues Found':<18} {'Time':>10}{_C.RESET}\n")
    out.write(f"  {_C.DIM}{'-' * 42}{_C.RESET}\n")

    total_issues = 0
    for tier_name in ("Tier 1", "Tier 1.5", "Tier 2", "Tier 3"):
        info = tier_results.get(tier_name, {"count": 0, "time": 0.0, "skipped": False})
        count = info["count"]
        elapsed = info["time"]

        if info.get("skipped"):
            count_str = f"{_C.DIM}(skipped){_C.RESET}"
        elif tier_name == "Tier 1.5":
            # Tier 1.5 shows removed count, not added
            note = info.get("note", "")
            count_str = f"{_C.GREEN}{note or f'{count} FPs removed'}{_C.RESET}"
        elif count == 0:
            count_str = f"{_C.GREEN}0{_C.RESET}"
        else:
            count_str = f"{_C.YELLOW}{count}{_C.RESET}"
            total_issues += count

        out.write(f"  {tier_name:<12} {count_str:<28} {elapsed:>8.2f}s\n")

    out.write(f"  {_C.DIM}{'-' * 42}{_C.RESET}\n")
    total_color = _C.GREEN if total_issues == 0 else _C.YELLOW
    total_time = sum(r.get("time", 0) for r in tier_results.values())
    out.write(f"  {'TOTAL':<12} {total_color}{total_issues:<18}{_C.RESET} {total_time:>8.2f}s\n")

    # Severity breakdown
    all_findings = []
    for info in tier_results.values():
        all_findings.extend(info.get("findings", []))

    if all_findings:
        sev_counts: Dict[str, int] = {}
        for f in all_findings:
            s = f.get("severity", "MEDIUM").upper()
            sev_counts[s] = sev_counts.get(s, 0) + 1

        out.write(f"\n  {_C.BOLD}Severity Breakdown:{_C.RESET}\n")
        for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
            c = sev_counts.get(sev, 0)
            if c > 0:
                color = _SEV_COLOR.get(sev, _C.WHITE)
                out.write(f"    {color}{sev:<12} {c}{_C.RESET}\n")

    # Brain status
    if brain:
        out.write(f"\n  {_C.MAGENTA}{_C.BOLD}Brain Status:{_C.RESET}\n")
        try:
            d = brain.digest()
            facts = d.get("total_facts", d.get("facts_cached", 0))
            agents = d.get("total_agents", d.get("agents_registered", 0))
            out.write(f"    Facts cached:      {_C.CYAN}{facts}{_C.RESET}\n")
            out.write(f"    Agents registered: {_C.CYAN}{agents}{_C.RESET}\n")
        except Exception:
            out.write(f"    {_C.DIM}(brain digest unavailable){_C.RESET}\n")

    out.write("\n")

    if total_issues == 0:
        out.write(f"  {_C.GREEN}{_C.BOLD}All clear. No issues detected.{_C.RESET}\n\n")
    else:
        out.write(
            f"  {_C.YELLOW}{_C.BOLD}Audit complete. "
            f"{total_issues} issue(s) require attention.{_C.RESET}\n\n"
        )


def _print_brain_status(brain: Any, out: TextIO) -> None:
    """Print detailed brain status and exit."""
    out.write(BANNER)
    out.write(f"  {_C.MAGENTA}{_C.BOLD}Diamond Brain -- Status Report{_C.RESET}\n")
    out.write(f"  {_C.BLUE}{'=' * 50}{_C.RESET}\n\n")

    try:
        d = brain.digest()
    except Exception as exc:
        out.write(f"  {_C.RED}Error reading brain: {exc}{_C.RESET}\n")
        return

    # Adapt to both brain API styles
    facts = d.get("total_facts", d.get("facts_cached", 0))
    agents_count = d.get("total_agents", d.get("agents_registered", 0))
    topics = d.get("topics", [])
    last_updated = d.get("last_updated")
    agents_detail = d.get("agent_history", d.get("agents", {}))

    out.write(f"  {_C.WHITE}Facts Cached:{_C.RESET}       {_C.CYAN}{facts}{_C.RESET}\n")
    out.write(f"  {_C.WHITE}Agents Registered:{_C.RESET}  {_C.CYAN}{agents_count}{_C.RESET}\n")
    if topics:
        out.write(f"  {_C.WHITE}Topics:{_C.RESET}            {_C.DIM}{', '.join(topics[:20])}{_C.RESET}\n")
    if last_updated:
        out.write(f"  {_C.WHITE}Last Updated:{_C.RESET}      {_C.DIM}{last_updated}{_C.RESET}\n")

    # Agent detail
    if agents_detail:
        out.write(f"\n  {_C.MAGENTA}{_C.BOLD}Agent Roster:{_C.RESET}\n")
        if isinstance(agents_detail, list):
            for a in agents_detail:
                aid = a.get("agent_id", "?")
                role = a.get("role", "?")
                status = a.get("status", "?")
                fc = a.get("findings_count", 0)
                sc = _C.GREEN if status == "active" else _C.RED
                out.write(
                    f"    {_C.WHITE}{aid:<22}{_C.RESET}"
                    f"  role={_C.CYAN}{role}{_C.RESET}"
                    f"  status={sc}{status}{_C.RESET}"
                    f"  findings={_C.YELLOW}{fc}{_C.RESET}\n"
                )
        elif isinstance(agents_detail, dict):
            for aid, info in agents_detail.items():
                role = info.get("role", "?") if isinstance(info, dict) else "?"
                status = info.get("status", "?") if isinstance(info, dict) else "?"
                sc = _C.GREEN if status == "active" else _C.RED
                out.write(
                    f"    {_C.WHITE}{aid:<22}{_C.RESET}"
                    f"  role={_C.CYAN}{role}{_C.RESET}"
                    f"  status={sc}{status}{_C.RESET}\n"
                )

    # Escalations
    esc_path = BRAIN_DIR / "memory" / "escalations.json"
    if esc_path.exists():
        try:
            esc = json.loads(esc_path.read_text(encoding="utf-8"))
            if isinstance(esc, list) and esc:
                unresolved = [e for e in esc if not e.get("resolved", False)]
                out.write(
                    f"\n  {_C.WHITE}Pending Escalations:{_C.RESET} "
                    f"{_C.YELLOW}{len(unresolved)}{_C.RESET} of {len(esc)} total\n"
                )
        except Exception:
            pass

    # Heatmap if available
    if hasattr(brain, "heatmap"):
        try:
            hm = brain.heatmap()
            if hm:
                out.write(f"\n  {_C.MAGENTA}{_C.BOLD}Knowledge Heatmap:{_C.RESET}\n")
                for topic, info in sorted(hm.items(), key=lambda x: x[1]["freshness_score"], reverse=True):
                    score = info["freshness_score"]
                    if score >= 80:
                        bar_c = _C.GREEN
                    elif score >= 40:
                        bar_c = _C.YELLOW
                    else:
                        bar_c = _C.RED
                    filled = score // 5
                    bar = f"{bar_c}{'|' * filled}{_C.DIM}{'.' * (20 - filled)}{_C.RESET}"
                    out.write(
                        f"    {_C.WHITE}{topic:<25}{_C.RESET}"
                        f" [{bar}] {bar_c}{score:>3}%{_C.RESET}"
                        f" {_C.DIM}({info['count']} facts){_C.RESET}\n"
                    )
        except Exception:
            pass

    out.write("\n")


# ===========================================================================
#  MAIN
# ===========================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="sentinel_audit",
        description="Diamond NetBlade -- Sentinel Auditor v1.0: Three-tier code audit pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python sentinel_audit.py                    # Run all tiers\n"
            "  python sentinel_audit.py --tier 1           # Pattern scan only\n"
            "  python sentinel_audit.py --tier 2 --verbose # LLM audit with detail\n"
            "  python sentinel_audit.py --brain-status     # Show brain state\n"
            "  python sentinel_audit.py --output report.txt\n"
        ),
    )
    parser.add_argument(
        "--tier",
        choices=["1", "2", "3", "all"],
        default="all",
        help="Run specific tier: 1 (pattern), 2 (local LLM), 3 (escalation), all (default: all)",
    )
    parser.add_argument(
        "--target",
        type=str,
        default=None,
        help=f"Target directory (default: {PROJECT_ROOT})",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output including code snippets",
    )
    parser.add_argument(
        "--brain-status",
        action="store_true",
        help="Show Diamond Brain digest and exit",
    )
    parser.add_argument(
        "--skip-cache",
        action="store_true",
        help="Ignore brain cache, re-audit everything",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Save report to file (default: stdout)",
    )
    parser.add_argument(
        "--no-filter",
        action="store_true",
        help="Skip Tier 1.5 binary truth filter (send all findings to Tier 2)",
    )
    args = parser.parse_args()

    # Output stream
    out: TextIO = sys.stdout
    output_file = None
    if args.output:
        output_file = open(args.output, "w", encoding="utf-8")
        out = output_file

    target = Path(args.target) if args.target else PROJECT_ROOT

    # Initialize brain
    brain = None
    if DiamondBrain is not None:
        try:
            brain = DiamondBrain()
        except Exception as exc:
            out.write(f"  {_C.YELLOW}[WARN]{_C.RESET} Failed to initialize Diamond Brain: {exc}\n")

    # Brain status mode
    if args.brain_status:
        if brain is None:
            out.write(f"  {_C.RED}Diamond Brain not available.{_C.RESET}\n")
            return 1
        _print_brain_status(brain, out)
        if output_file:
            output_file.close()
        return 0

    # Print banner
    out.write(BANNER)
    out.write(f"  {_C.DIM}Target:  {target}{_C.RESET}\n")
    out.write(f"  {_C.DIM}Time:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{_C.RESET}\n")
    if brain:
        out.write(f"  {_C.DIM}Brain:   ONLINE{_C.RESET}\n")
    else:
        out.write(f"  {_C.DIM}Brain:   OFFLINE (brain module not found){_C.RESET}\n")
    out.write(f"  {_C.DIM}Tier:    {args.tier}{_C.RESET}\n")
    out.write("\n")

    # Register agent with brain
    if brain:
        try:
            brain.agent_checkin("sentinel-auditor", "code-auditor", "rust-audit")
        except Exception:
            pass

    run_tier1 = args.tier in ("1", "all")
    run_tier2 = args.tier in ("2", "all")
    run_tier3 = args.tier in ("3", "all")

    run_filter = run_tier1 and run_tier2 and not args.no_filter

    tier_results: Dict[str, Dict[str, Any]] = {
        "Tier 1": {"count": 0, "time": 0.0, "findings": [], "skipped": not run_tier1},
        "Tier 1.5": {"count": 0, "time": 0.0, "findings": [], "skipped": not run_filter},
        "Tier 2": {"count": 0, "time": 0.0, "findings": [], "skipped": not run_tier2},
        "Tier 3": {"count": 0, "time": 0.0, "findings": [], "skipped": not run_tier3},
    }

    all_findings: List[Dict[str, Any]] = []

    # ---------------------------------------------------------------
    # TIER 1
    # ---------------------------------------------------------------
    if run_tier1:
        out.write(f"  {_C.BOLD}{_C.CYAN}--- TIER 1: Pattern Scanner ---{_C.RESET}\n")
        t0 = time.time()
        tier1_findings = tier1_scan(target, verbose=args.verbose, out=out)
        t1_elapsed = time.time() - t0

        _print_findings(tier1_findings, "Tier 1: Pattern Scan", args.verbose, out)

        tier_results["Tier 1"] = {
            "count": len(tier1_findings),
            "time": t1_elapsed,
            "findings": tier1_findings,
            "skipped": False,
        }
        all_findings.extend(tier1_findings)

        # Report to brain
        if brain:
            try:
                brain.agent_report("sentinel-auditor", tier1_findings)
            except Exception:
                pass
    else:
        tier1_findings = []

    # ---------------------------------------------------------------
    # TIER 1.5 — Binary Truth Filter
    # ---------------------------------------------------------------
    if run_filter and tier1_findings:
        out.write(f"\n  {_C.BOLD}{_C.CYAN}--- TIER 1.5: Binary Truth Filter ---{_C.RESET}\n")
        t0 = time.time()
        original_count = len(tier1_findings)
        tier1_findings = tier1_5_truth_filter(
            tier1_findings, verbose=args.verbose, out=out,
        )
        t15_elapsed = time.time() - t0

        tier_results["Tier 1.5"] = {
            "count": original_count - len(tier1_findings),
            "time": t15_elapsed,
            "findings": [],
            "skipped": False,
            "note": f"Filtered {original_count} → {len(tier1_findings)}",
        }

        # Replace all_findings with the filtered set
        all_findings = [f for f in all_findings if f in tier1_findings]

    # ---------------------------------------------------------------
    # TIER 2
    # ---------------------------------------------------------------
    if run_tier2:
        out.write(f"\n  {_C.BOLD}{_C.CYAN}--- TIER 2: Local LLM Audit ---{_C.RESET}\n")
        t0 = time.time()

        # If we did not run Tier 1 but want Tier 2, do a quick Tier 1 to know which files
        if not run_tier1:
            tier1_findings = tier1_scan(target, verbose=False, out=out)

        tier2_findings = tier2_llm_audit(
            target,
            tier1_findings,
            brain,
            verbose=args.verbose,
            skip_cache=args.skip_cache,
            out=out,
        )
        t2_elapsed = time.time() - t0

        _print_findings(tier2_findings, "Tier 2: LLM Analysis", args.verbose, out)

        tier_results["Tier 2"] = {
            "count": len(tier2_findings),
            "time": t2_elapsed,
            "findings": tier2_findings,
            "skipped": False,
        }
        all_findings.extend(tier2_findings)

        # Learn findings into brain
        if brain and tier2_findings:
            for f in tier2_findings:
                try:
                    brain.learn(
                        topic=f.get("category", "tier2_finding"),
                        fact=f"{f.get('severity', 'MEDIUM')}: {f.get('message', '')} in {f.get('file', '?')}",
                        confidence=80,
                        source="sentinel-auditor-tier2",
                    )
                except Exception:
                    pass

    # ---------------------------------------------------------------
    # TIER 3
    # ---------------------------------------------------------------
    if run_tier3:
        out.write(f"\n  {_C.BOLD}{_C.CYAN}--- TIER 3: Claude Escalation ---{_C.RESET}\n")
        t0 = time.time()

        # If neither Tier 1 nor 2 ran, gather findings first
        if not run_tier1 and not run_tier2:
            all_findings = tier1_scan(target, verbose=False, out=out)

        escalations = tier3_escalation(
            all_findings,
            brain,
            verbose=args.verbose,
            out=out,
        )
        t3_elapsed = time.time() - t0

        _print_escalations(escalations, out)

        tier_results["Tier 3"] = {
            "count": len(escalations),
            "time": t3_elapsed,
            "findings": escalations,
            "skipped": False,
        }

    # ---------------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------------
    _print_summary(tier_results, brain, out)

    if output_file:
        output_file.close()
        # Also print to real stdout that we wrote a file
        print(f"Report saved to: {args.output}")

    # Exit code: 0 if no CRITICAL, 1 if any CRITICAL
    has_critical = any(
        f.get("severity", "").upper() == "CRITICAL"
        for f in all_findings
    )
    return 1 if has_critical else 0


if __name__ == "__main__":
    sys.exit(main())
