#!/usr/bin/env python3
"""
Session Compact — Full Preservation Pipeline
Runs transcripts + guardian extraction + context-agent save before compaction.

Usage:
  python3 session_compact.py --session-dir ~/.kimi/sessions/{hash}/{uuid}
    [--transcript] [--guardian] [--context-agent]
    [--guardian-depth {p0,p0p1,full}]
    [--output-to {archive,session,both}]
    [--briefing {full,mini,none}]
    [--code-extraction]
"""

import argparse
import json
import os
import re
import shutil
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SKILL_DIR = Path(__file__).parent.parent.resolve()
SESSION_TRANSCRIPT_SCRIPTS = Path.home() / ".kimi" / "skills" / "session-transcript" / "scripts"
SESSIONS_ROOT = Path.home() / ".kimi" / "sessions"
ARCHIVE_ROOT = Path.home() / "session-archive"

sys.path.insert(0, str(SESSION_TRANSCRIPT_SCRIPTS))

try:
    from generate_transcript import (
        discover_sessions,
        load_session,
        generate_html,
        generate_md,
        generate_txt,
        generate_code_md,
        SessionData,
        Turn,
    )
except ImportError as e:
    print(f"[ERROR] Cannot import session-transcript modules: {e}")
    print(f"        Expected at: {SESSION_TRANSCRIPT_SCRIPTS}")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Hash → project name mapping (copied from session-daemon.py)
# ---------------------------------------------------------------------------
_HASH_TO_NAME: Dict[str, str] = {}


def _build_hash_map() -> Dict[str, str]:
    import hashlib
    kimi_json = Path.home() / ".kimi" / "kimi.json"
    if not kimi_json.exists():
        return {}
    try:
        data = json.loads(kimi_json.read_text())
        result = {}
        for wd in data.get("work_dirs", []):
            path = wd.get("path", "")
            if not path:
                continue
            h = hashlib.md5(path.encode()).hexdigest()
            name = path.replace("/home/flintx/", "").replace("/", "-").strip("-")
            while name.startswith("."):
                name = name[1:]
            if not name:
                name = "root"
            result[h] = name
        return result
    except Exception:
        return {}


def get_project_name(project_hash: str) -> str:
    global _HASH_TO_NAME
    if not _HASH_TO_NAME:
        _HASH_TO_NAME = _build_hash_map()
    return _HASH_TO_NAME.get(project_hash, project_hash)


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------
def safe_title(title: str) -> str:
    return re.sub(r"[^\w\-]+", "_", title.lower()).strip("_")[:40] or "session"


def generate_slug(title: str) -> str:
    words = re.findall(r"[a-zA-Z]+", title.lower())
    stopwords = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "can", "i", "you", "he", "she", "it", "we",
        "they", "me", "him", "her", "us", "them", "my", "your", "his", "its",
        "our", "their",
    }
    filtered = [w for w in words if w not in stopwords and len(w) > 2]
    if not filtered:
        filtered = [w for w in words if len(w) > 2]
    if not filtered:
        filtered = words
    return "-".join(filtered[:4]) or "untitled"


def find_most_recent_session() -> Optional[Path]:
    """Find the most recently modified session directory."""
    latest_dir = None
    latest_mtime = 0.0
    for proj_dir in SESSIONS_ROOT.iterdir():
        if not proj_dir.is_dir():
            continue
        for sess_dir in proj_dir.iterdir():
            if not sess_dir.is_dir():
                continue
            mtime = 0.0
            for f in sess_dir.iterdir():
                if f.is_file():
                    mtime = max(mtime, f.stat().st_mtime)
            if mtime > latest_mtime:
                latest_mtime = mtime
                latest_dir = sess_dir
    return latest_dir


# ---------------------------------------------------------------------------
# Guardian Protocol — Extraction
# ---------------------------------------------------------------------------

@dataclass
class GuardianEntry:
    priority: str  # P0, P1, P2
    category: str
    turn: int
    title: str
    text: str
    details: Dict = field(default_factory=dict)


class GuardianExtractor:
    """Extract P0/P1/P2 entries from session turns using heuristics."""

    # Command verbs for detecting instructions/decisions
    COMMAND_VERBS = {
        "make", "create", "build", "fix", "add", "remove", "change", "update",
        "delete", "write", "run", "test", "check", "show", "find", "search",
        "get", "set", "install", "configure", "implement", "refactor",
        "optimize", "debug", "deploy", "generate", "extract", "convert",
        "parse", "format", "render", "display", "print", "output", "save",
        "export", "import", "load", "store", "push", "pull", "send",
        "process", "analyze", "review", "audit", "scan", "monitor",
        "start", "stop", "restart", "kill", "watch", "listen", "track",
        "compare", "merge", "split", "combine", "organize", "sort",
        "filter", "group", "map", "reduce", "transform", "clean",
        "validate", "verify", "ensure", "confirm", "approve",
        "move", "copy", "rename", "link", "unlink", "chmod", "chown",
        "schedule", "trigger", "execute", "perform", "apply",
        "enable", "disable", "toggle", "switch",
        "use", "try", "attempt", "consider", "look", "see",
        "give", "tell", "explain", "describe", "document", "note",
        "remember", "keep", "maintain", "preserve", "archive",
        "help", "assist", "support", "guide", "lead", "direct",
        "ask", "request", "demand", "require", "need", "want",
        "should", "must", "have to", "supposed to", "expected to",
        "let", "lets", "let's",
    }

    # Keywords for categorization
    DECISION_KWS = [
        "decided", "decision", "going with", "choose", "chosen", "pick",
        "picking", "select", "selected", "opt for", "settled on",
        "going to use", "final choice", "settled", "agreed on",
    ]
    PROGRESS_KWS = [
        "done", "completed", "finished", "working", "implemented",
        "accomplished", "achieved", "resolved", "fixed", "built",
        "created", "established", "set up", "configured",
    ]
    FAILURE_KWS = [
        "failed", "doesn't work", "does not work", "broke", "broken",
        "error", "wrong", "issue", "problem", "bug", "crash",
        "not working", "won't", "would not", "could not", "unable",
        "missing", "lost", "corrupted", "timeout", "rejected",
    ]
    FIX_KWS = [
        "fixed", "corrected", "resolved", "patched", "workaround",
        "solution", "solved", "addressed", "mitigated",
    ]
    PIVOT_KWS = [
        "instead", "changing", "switching", "pivot", "revert",
        "going back", "abandon", "drop", "scrap", "replace with",
        "rather than", "as opposed to", "flip", "reverse",
        "undo", "redo", "start over", "from scratch",
    ]
    ARCHITECTURE_KWS = [
        "design", "structure", "pattern", "architecture", "model",
        "schema", "framework", "layout", "organization", "hierarchy",
        "component", "module", "layer", "tier", "pipeline",
        "flow", "diagram", "system", "platform", "infrastructure",
    ]
    INSIGHT_KWS = [
        "realized", "figured out", "discovered", "turns out",
        "i see", "understand now", "makes sense", "ah ha",
        "eureka", "breakthrough", "key insight", "important",
        "critical", "essential", "fundamental", "core",
    ]

    def __init__(self, turns: List[Turn], depth: str = "p0p1"):
        self.turns = turns
        self.depth = depth  # p0, p0p1, full
        self.entries: List[GuardianEntry] = []

    def extract(self) -> List[GuardianEntry]:
        for turn in self.turns:
            self._extract_from_turn(turn)
        # Sort by priority then turn
        priority_order = {"P0": 0, "P1": 1, "P2": 2}
        self.entries.sort(key=lambda e: (priority_order.get(e.priority, 99), e.turn))
        return self.entries

    def _extract_from_turn(self, turn: Turn) -> None:
        user_text = turn.user_message.strip()
        user_lower = user_text.lower()
        if not user_text:
            return

        # P0: Critical items
        p0 = self._extract_p0(turn, user_text, user_lower)
        self.entries.extend(p0)

        # P1: Important items (if depth allows)
        if self.depth in ("p0p1", "full"):
            p1 = self._extract_p1(turn, user_text, user_lower)
            self.entries.extend(p1)

        # P2: Tolerable items (if depth is full)
        if self.depth == "full":
            p2 = self._extract_p2(turn, user_text, user_lower)
            self.entries.extend(p2)

    def _extract_p0(self, turn: Turn, text: str, lower: str) -> List[GuardianEntry]:
        entries = []

        # Check for explicit decisions
        for kw in self.DECISION_KWS:
            if kw in lower:
                entries.append(GuardianEntry(
                    priority="P0",
                    category="Decision",
                    turn=turn.turn_number,
                    title=self._make_title(text, "Decision"),
                    text=text,
                    details={"keyword": kw},
                ))
                break

        # Check for fixes/corrections
        for kw in self.FIX_KWS:
            if kw in lower:
                entries.append(GuardianEntry(
                    priority="P0",
                    category="Fix Applied",
                    turn=turn.turn_number,
                    title=self._make_title(text, "Fix"),
                    text=text,
                    details={"keyword": kw},
                ))
                break

        # Check for errors found
        for kw in self.FAILURE_KWS:
            if kw in lower:
                entries.append(GuardianEntry(
                    priority="P0",
                    category="Error Found",
                    turn=turn.turn_number,
                    title=self._make_title(text, "Error"),
                    text=text,
                    details={"keyword": kw},
                ))
                break

        # Check for code/file modifications in assistant response
        if turn.code_blocks:
            for cb in turn.code_blocks:
                entries.append(GuardianEntry(
                    priority="P0",
                    category="Code Change",
                    turn=turn.turn_number,
                    title=f"Code: {cb.language or 'unknown'}",
                    text=cb.code[:500] + ("..." if len(cb.code) > 500 else ""),
                    details={"language": cb.language, "full_length": len(cb.code)},
                ))

        return entries

    def _extract_p1(self, turn: Turn, text: str, lower: str) -> List[GuardianEntry]:
        entries = []

        # Patterns discovered
        for kw in self.ARCHITECTURE_KWS:
            if kw in lower:
                entries.append(GuardianEntry(
                    priority="P1",
                    category="Pattern/Architecture",
                    turn=turn.turn_number,
                    title=self._make_title(text, "Pattern"),
                    text=text,
                ))
                break

        # Insights
        for kw in self.INSIGHT_KWS:
            if kw in lower:
                entries.append(GuardianEntry(
                    priority="P1",
                    category="Insight",
                    turn=turn.turn_number,
                    title=self._make_title(text, "Insight"),
                    text=text,
                ))
                break

        # Pivots
        for kw in self.PIVOT_KWS:
            if kw in lower:
                entries.append(GuardianEntry(
                    priority="P1",
                    category="Pivot",
                    turn=turn.turn_number,
                    title=self._make_title(text, "Pivot"),
                    text=text,
                ))
                break

        return entries

    def _extract_p2(self, turn: Turn, text: str, lower: str) -> List[GuardianEntry]:
        entries = []

        # Progress metrics
        for kw in self.PROGRESS_KWS:
            if kw in lower:
                entries.append(GuardianEntry(
                    priority="P2",
                    category="Progress",
                    turn=turn.turn_number,
                    title=self._make_title(text, "Progress"),
                    text=text,
                ))
                break

        # Commands that worked
        if re.search(r"^\s*[`$>](?:\s*\w+)", text, re.MULTILINE):
            entries.append(GuardianEntry(
                priority="P2",
                category="Command",
                turn=turn.turn_number,
                title=self._make_title(text, "Command"),
                text=text,
            ))

        return entries

    def _make_title(self, text: str, prefix: str) -> str:
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if not lines:
            return f"{prefix}: Untitled"
        first = lines[0]
        first = re.sub(r"^#{1,6}\s*", "", first)
        first = re.sub(r"^(User|Assistant|Bot|AI):\s*", "", first, flags=re.I)
        if len(first) > 60:
            first = first[:57] + "..."
        return f"{prefix}: {first}" or f"{prefix}: Untitled"

    def verify_integrity(self) -> List[str]:
        """Return a list of verification warnings."""
        warnings = []

        # Check for code changes without file paths
        code_entries = [e for e in self.entries if e.category == "Code Change"]
        if code_entries:
            # Check if any mention file paths
            has_paths = any(re.search(r"[\w\-]+\.(py|js|ts|jsx|tsx|go|rs|java|cpp|c|h|md|json|yaml|yml|sh|bash)", e.text) for e in code_entries)
            if not has_paths:
                warnings.append("Code changes detected but no file paths found in P0 entries")

        # Check for decisions without rationale
        decision_entries = [e for e in self.entries if e.category == "Decision"]
        for de in decision_entries:
            if len(de.text) < 30:
                warnings.append(f"Decision at turn {de.turn} is very short — may lack rationale")

        # Check for errors without fixes
        errors = [e for e in self.entries if e.category == "Error Found"]
        fixes = [e for e in self.entries if e.category == "Fix Applied"]
        if errors and not fixes:
            warnings.append("Errors found but no fixes recorded — session may have unresolved issues")

        return warnings


# ---------------------------------------------------------------------------
# Guardian Protocol — Snapshot & Briefing Generation
# ---------------------------------------------------------------------------

def generate_guardian_snapshot(entries: List[GuardianEntry], session: SessionData, warnings: List[str]) -> str:
    now = datetime.now().isoformat()
    lines = []
    lines.append("# Guardian Snapshot")
    lines.append(f"**Session:** {session.title}")
    lines.append(f"**Turns:** {len(session.turns)}")
    lines.append(f"**Generated:** {now}")
    lines.append("")

    if warnings:
        lines.append("## ⚠️ Verification Warnings")
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")

    # Group by priority
    p0s = [e for e in entries if e.priority == "P0"]
    p1s = [e for e in entries if e.priority == "P1"]
    p2s = [e for e in entries if e.priority == "P2"]

    lines.append(f"## P0 — Critical ({len(p0s)} items)")
    lines.append("")
    for e in p0s:
        lines.append(f"### {e.title} (Turn {e.turn})")
        lines.append(f"- **Category:** {e.category}")
        lines.append(f"- **Text:** {e.text[:300]}{'...' if len(e.text) > 300 else ''}")
        if e.details:
            for k, v in e.details.items():
                lines.append(f"- **{k}:** {v}")
        lines.append("")

    if p1s:
        lines.append(f"## P1 — Important ({len(p1s)} items)")
        lines.append("")
        for e in p1s:
            lines.append(f"### {e.title} (Turn {e.turn})")
            lines.append(f"- **Category:** {e.category}")
            lines.append(f"- **Text:** {e.text[:200]}{'...' if len(e.text) > 200 else ''}")
            lines.append("")

    if p2s:
        lines.append(f"## P2 — Reference ({len(p2s)} items)")
        lines.append("")
        for e in p2s:
            lines.append(f"- **{e.title}** (Turn {e.turn}) — {e.category}")
        lines.append("")

    return "\n".join(lines)


def generate_transition_briefing(entries: List[GuardianEntry], session: SessionData, mini: bool = False) -> str:
    now = datetime.now().isoformat()
    p0s = [e for e in entries if e.priority == "P0"]

    decisions = [e for e in p0s if e.category == "Decision"]
    fixes = [e for e in p0s if e.category == "Fix Applied"]
    errors = [e for e in p0s if e.category == "Error Found"]
    code_changes = [e for e in p0s if e.category == "Code Change"]

    lines = []
    lines.append("# Transition Briefing")
    lines.append(f"**Session:** {session.title} | **Turns:** {len(session.turns)} | **Generated:** {now}")
    lines.append("")

    if mini:
        lines.append("## Quick State")
        lines.append(f"- Decisions: {len(decisions)} | Fixes: {len(fixes)} | Errors: {len(errors)} | Code changes: {len(code_changes)}")
        if decisions:
            lines.append(f"- Last decision: {decisions[-1].title}")
        lines.append("")
        lines.append("## Next Session Should Know")
        for e in decisions[-3:] + fixes[-3:]:
            lines.append(f"- **{e.category}:** {e.title}")
        lines.append("")
        return "\n".join(lines)

    # Full briefing
    lines.append("## Current State")
    lines.append(f"- Project: {session.title}")
    lines.append(f"- Phase: In progress")
    lines.append(f"- Progress: {len(session.turns)} turns processed")
    lines.append("")

    lines.append("## What Was Done This Session")
    for e in decisions[:5] + fixes[:5]:
        lines.append(f"1. **{e.category}:** {e.title}")
    lines.append("")

    if errors:
        lines.append("## Errors Found")
        for e in errors[:5]:
            lines.append(f"- {e.title}: {e.text[:150]}")
        lines.append("")

    lines.append("## Critical Decisions (Do Not Change Without Reason)")
    for e in decisions:
        lines.append(f"- **{e.title}:** {e.text[:200]}")
    lines.append("")

    lines.append("## Fixes Applied (Do Not Revert)")
    for e in fixes:
        lines.append(f"- {e.title}: {e.text[:200]}")
    lines.append("")

    if code_changes:
        lines.append("## Code Changes")
        for e in code_changes[:5]:
            lines.append(f"- {e.title} ({e.details.get('language', 'unknown')}, {e.details.get('full_length', 0)} chars)")
        lines.append("")

    lines.append("## Where To Recover More Information")
    lines.append("- Guardian snapshot: see snapshots/ directory")
    lines.append("- Full transcript: see transcripts/ directory")
    lines.append("- Standard report: see standard/ directory")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Context-Agent Style Save
# ---------------------------------------------------------------------------

def generate_context_agent_summary(session: SessionData, entries: List[GuardianEntry]) -> str:
    now = datetime.now().isoformat()
    turns = session.turns

    # Extract topics from user messages
    topics: Set[str] = set()
    for turn in turns:
        words = re.findall(r"\b[A-Za-z]{5,}\b", turn.user_message)
        for w in words:
            w = w.lower()
            if w not in {"should", "would", "could", "this", "that", "with", "from", "have", "been", "were", "there", "their", "about", "which", "when", "where", "while", "because", "before", "after", "during", "through", "between", "under", "over", "into", "onto", "upon", "within", "without", "against", "among", "around", "above", "below", "behind", "beyond", "across", "along", "beside", "inside", "outside", "toward", "towards", "until", "unless", "although", "though", "whether", "either", "neither", "both", "each", "every", "some", "many", "much", "more", "most", "other", "another", "such", "only", "even", "also", "just", "still", "already", "yet", "ever", "never", "always", "often", "sometimes", "usually", "really", "very", "quite", "rather", "pretty", "enough", "almost", "nearly", "mostly", "mainly", "partly", "fully", "completely", "totally", "entirely", "exactly", "precisely", "specifically", "particularly", "especially", "generally", "typically", "normally", "usually", "frequently", "regularly", "constantly", "continuously", "repeatedly", "occasionally", "rarely", "seldom", "hardly", "barely", "scarcely", "merely", "simply", "basically", "fundamentally", "essentially", "primarily", "principally", "chiefly", "mainly", "mostly", "largely", "partly", "partially", "slightly", "somewhat", "somehow", "anyway", "anyhow", "instead", "otherwise", "elsewhere", "anywhere", "everywhere", "somewhere", "nowhere", "here", "there", "then", "now", "today", "tomorrow", "yesterday", "soon", "later", "earlier", "before", "after", "ago", "hence", "thus", "therefore", "however", "nevertheless", "nonetheless", "otherwise", "instead", "meanwhile", "besides", "furthermore", "moreover", "additionally", "also", "too", "either", "neither", "both", "indeed", "actually", "certainly", "definitely", "absolutely", "obviously", "clearly", "apparently", "seemingly", "presumably", "supposedly", "probably", "possibly", "perhaps", "maybe", "likely", "unlikely", "surely", "certainly", "definitely", "absolutely", "obviously", "clearly", "apparently", "seemingly", "presumably", "supposedly", "probably", "possibly", "perhaps", "maybe", "likely", "unlikely", "surely"}:
                topics.add(w)

    # Categorize entries
    decisions = [e for e in entries if e.category == "Decision"]
    fixes = [e for e in entries if e.category == "Fix Applied"]
    errors = [e for e in entries if e.category == "Error Found"]
    code_changes = [e for e in entries if e.category == "Code Change"]
    insights = [e for e in entries if e.category == "Insight"]
    pivots = [e for e in entries if e.category == "Pivot"]

    # Files modified (from code blocks)
    files_modified: Set[str] = set()
    for turn in turns:
        for cb in turn.code_blocks:
            # Try to infer file from context or code
            pass  # We'll skip this for now as it requires deeper analysis

    lines = []
    lines.append("# Session Summary — Context Agent Style")
    lines.append(f"**Session:** {session.title}")
    lines.append(f"**Turns:** {len(turns)}")
    lines.append(f"**Words:** {session.total_words}")
    lines.append(f"**Code blocks:** {session.total_code_blocks}")
    lines.append(f"**Images:** {session.total_images}")
    lines.append(f"**Generated:** {now}")
    lines.append("")

    lines.append("## Topics")
    topic_list = sorted(topics)[:20]
    lines.append(", ".join(topic_list) if topic_list else "N/A")
    lines.append("")

    lines.append("## Decisions")
    if decisions:
        for e in decisions[:10]:
            lines.append(f"- {e.title}")
    else:
        lines.append("No decisions recorded.")
    lines.append("")

    lines.append("## Tasks Completed")
    if fixes:
        for e in fixes[:10]:
            lines.append(f"- [x] {e.title}")
    else:
        lines.append("No completed tasks recorded.")
    lines.append("")

    lines.append("## Tasks Pending")
    # Heuristic: look for open-ended instructions or questions
    pending = []
    for turn in turns[-5:]:
        if "?" in turn.user_message and len(turn.user_message) > 20:
            pending.append(turn.user_message[:100])
    if pending:
        for p in pending[:5]:
            lines.append(f"- [ ] {p}")
    else:
        lines.append("No pending tasks detected.")
    lines.append("")

    lines.append("## Errors Resolved")
    if errors:
        for e in errors[:5]:
            lines.append(f"- {e.title}: {e.text[:150]}")
    else:
        lines.append("No errors recorded.")
    lines.append("")

    lines.append("## Insights")
    if insights:
        for e in insights[:5]:
            lines.append(f"- {e.title}")
    else:
        lines.append("No insights recorded.")
    lines.append("")

    lines.append("## Pivots")
    if pivots:
        for e in pivots[:5]:
            lines.append(f"- {e.title}")
    else:
        lines.append("No pivots recorded.")
    lines.append("")

    lines.append("## Code Changes")
    if code_changes:
        for e in code_changes[:10]:
            lang = e.details.get("language", "unknown")
            size = e.details.get("full_length", 0)
            lines.append(f"- {e.title} ({lang}, {size} chars)")
    else:
        lines.append("No code changes recorded.")
    lines.append("")

    lines.append("## Metrics")
    lines.append(f"- Total turns: {len(turns)}")
    lines.append(f"- Total words: {session.total_words}")
    lines.append(f"- Code blocks: {session.total_code_blocks}")
    lines.append(f"- Images: {session.total_images}")
    lines.append(f"- Guardian entries: {len(entries)} (P0: {len([e for e in entries if e.priority=='P0'])}, P1: {len([e for e in entries if e.priority=='P1'])}, P2: {len([e for e in entries if e.priority=='P2'])})")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main Orchestration
# ---------------------------------------------------------------------------

def run_pipeline(args: argparse.Namespace) -> None:
    # Resolve session directory
    session_dir = Path(args.session_dir) if args.session_dir else None
    if not session_dir:
        session_dir = find_most_recent_session()
        if not session_dir:
            print("[ERROR] No session found. Specify --session-dir.")
            sys.exit(1)
        print(f"[INFO] Auto-detected session: {session_dir}")

    if not session_dir.exists():
        print(f"[ERROR] Session directory not found: {session_dir}")
        sys.exit(1)

    session_id = session_dir.name
    project_id = session_dir.parent.name
    project_name = get_project_name(project_id)

    print(f"=" * 60)
    print(f"Session Compact Pipeline")
    print(f"Session: {session_id}")
    print(f"Project: {project_name}")
    print(f"=" * 60)
    print()

    # Load session
    print("[1/4] Loading session data...")
    session = load_session(session_dir)
    if not session:
        print("[ERROR] Failed to load session.")
        sys.exit(1)
    print(f"      Turns: {len(session.turns)}")
    print(f"      Words: {session.total_words}")
    print(f"      Code blocks: {session.total_code_blocks}")
    print()

    # Determine output roots
    if args.output_to in ("session", "both"):
        out_session = session_dir
    else:
        out_session = None

    if args.output_to in ("archive", "both"):
        arc_session = ARCHIVE_ROOT / project_name / session_id
        arc_session.mkdir(parents=True, exist_ok=True)
        out_archive = arc_session
    else:
        out_archive = None

    # -----------------------------------------------------------------------
    # Step 1: Transcript pipeline
    # -----------------------------------------------------------------------
    if args.transcript:
        print("[2/4] Running transcript pipeline...")
        safe = safe_title(session.title)
        slug = generate_slug(session.title)
        base_name = f"{safe}_{session_id[:8]}"

        # Generate outputs
        html = generate_html(session)
        md = generate_md(session)
        txt = generate_txt(session)
        code_md = generate_code_md(session)

        # Write to session dir
        if out_session:
            trans_dir = out_session / "transcripts"
            trans_dir.mkdir(exist_ok=True)
            (trans_dir / f"{base_name}.html").write_text(html)
            (trans_dir / f"{base_name}.md").write_text(md)
            (trans_dir / f"{base_name}.txt").write_text(txt)
            if args.code_extraction:
                (trans_dir / f"{base_name}_code.md").write_text(code_md)
            print(f"      Written to session dir: {trans_dir}")

        # Write to archive
        if out_archive:
            trans_dir = out_archive / "transcripts"
            trans_dir.mkdir(exist_ok=True)
            (trans_dir / f"{base_name}.html").write_text(html)
            (trans_dir / f"{base_name}.md").write_text(md)
            (trans_dir / f"{base_name}.txt").write_text(txt)
            if args.code_extraction:
                (trans_dir / f"{base_name}_code.md").write_text(code_md)
            print(f"      Written to archive: {trans_dir}")
        print()

    # -----------------------------------------------------------------------
    # Step 2: Guardian protocol
    # -----------------------------------------------------------------------
    if args.guardian:
        print("[3/4] Running guardian extraction...")
        extractor = GuardianExtractor(session.turns, depth=args.guardian_depth)
        entries = extractor.extract()
        warnings = extractor.verify_integrity()

        print(f"      Extracted: {len(entries)} entries")
        print(f"        P0: {len([e for e in entries if e.priority == 'P0'])}")
        print(f"        P1: {len([e for e in entries if e.priority == 'P1'])}")
        print(f"        P2: {len([e for e in entries if e.priority == 'P2'])}")
        if warnings:
            print(f"      Warnings: {len(warnings)}")
            for w in warnings:
                print(f"        ! {w}")

        # Snapshot
        snapshot = generate_guardian_snapshot(entries, session, warnings)
        if out_session:
            snap_dir = out_session / "snapshots"
            snap_dir.mkdir(exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            (snap_dir / f"guardian-snapshot-{ts}.md").write_text(snapshot)

        if out_archive:
            snap_dir = out_archive / "snapshots"
            snap_dir.mkdir(exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            (snap_dir / f"guardian-snapshot-{ts}.md").write_text(snapshot)

        # Briefing
        if args.briefing != "none":
            briefing = generate_transition_briefing(entries, session, mini=(args.briefing == "mini"))
            if out_session:
                brief_dir = out_session / "briefings"
                brief_dir.mkdir(exist_ok=True)
                ts = datetime.now().strftime("%Y%m%d-%H%M%S")
                (brief_dir / f"transition-briefing-{ts}.md").write_text(briefing)

            if out_archive:
                brief_dir = out_archive / "briefings"
                brief_dir.mkdir(exist_ok=True)
                ts = datetime.now().strftime("%Y%m%d-%H%M%S")
                (brief_dir / f"transition-briefing-{ts}.md").write_text(briefing)

            print(f"      Briefing: {args.briefing}")
        print()

    # -----------------------------------------------------------------------
    # Step 3: Context-agent save
    # -----------------------------------------------------------------------
    if args.context_agent:
        print("[4/4] Running context-agent save...")
        # Reuse entries if guardian ran, otherwise extract minimal
        if args.guardian:
            extractor = GuardianExtractor(session.turns, depth="p0")
            entries = extractor.extract()
        else:
            entries = []

        summary = generate_context_agent_summary(session, entries)

        if out_session:
            ca_dir = out_session / "context-agent"
            ca_dir.mkdir(exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            (ca_dir / f"session-summary-{ts}.md").write_text(summary)

        if out_archive:
            ca_dir = out_archive / "context-agent"
            ca_dir.mkdir(exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            (ca_dir / f"session-summary-{ts}.md").write_text(summary)

        print(f"      Summary written")
        print()

    # -----------------------------------------------------------------------
    # Done
    # -----------------------------------------------------------------------
    print("=" * 60)
    print("Pipeline complete.")
    if out_archive:
        print(f"Archive: {out_archive}")
    if out_session:
        print(f"Session: {out_session}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Session Compact — Full Preservation Pipeline")
    parser.add_argument("--session-dir", help="Path to session directory")
    parser.add_argument("--transcript", action="store_true", help="Run transcript pipeline")
    parser.add_argument("--guardian", action="store_true", help="Run guardian extraction")
    parser.add_argument("--context-agent", action="store_true", help="Run context-agent save")
    parser.add_argument("--guardian-depth", choices=["p0", "p0p1", "full"], default="p0p1",
                        help="Guardian extraction depth")
    parser.add_argument("--output-to", choices=["archive", "session", "both"], default="both",
                        help="Where to write outputs")
    parser.add_argument("--briefing", choices=["full", "mini", "none"], default="full",
                        help="Transition briefing type")
    parser.add_argument("--code-extraction", action="store_true", help="Include _code.md output")
    parser.add_argument("--daemon-hint", action="store_true", help="Enable daemon hint mode")

    args = parser.parse_args()

    # If no pipeline steps specified, enable all
    if not any([args.transcript, args.guardian, args.context_agent]):
        args.transcript = True
        args.guardian = True
        args.context_agent = True

    run_pipeline(args)


if __name__ == "__main__":
    main()
