#!/usr/bin/env python3
"""
Session Orchestrator Daemon
Watches ~/.kimi/sessions/ and auto-processes all sessions.
Generates transcripts (HTML, MD, TXT, code.md) and standard analysis reports.

Modes:
  --daemon    Run continuously, watching for new/updated sessions
  --batch     Process all sessions once, then exit
  --status    Show registry status

Usage:
  python3 session-daemon.py --daemon
  python3 session-daemon.py --batch
  python3 session-daemon.py --status
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import signal
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add parent of scripts dir to path for importing generate_transcript
SCRIPTS_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPTS_DIR))

from generate_transcript import (
    SESSIONS_ROOT,
    discover_sessions,
    load_session,
    generate_html,
    generate_md,
    generate_txt,
    generate_code_md,
    SessionData,
    Turn,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

ARCHIVE_ROOT = Path.home() / "session-archive"
REGISTRY_PATH = SESSIONS_ROOT / ".orchestrator-registry.json"
PIDFILE_PATH = SESSIONS_ROOT / ".orchestrator.pid"
POLL_INTERVAL = 60  # seconds between scans in daemon mode

# Ensure directories exist
ARCHIVE_ROOT.mkdir(parents=True, exist_ok=True)

# Build hash -> project name mapping from kimi.json
_HASH_TO_NAME: Dict[str, str] = {}

def _build_hash_map() -> Dict[str, str]:
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
# Registry
# ---------------------------------------------------------------------------

def load_registry() -> dict:
    if REGISTRY_PATH.exists():
        try:
            return json.loads(REGISTRY_PATH.read_text())
        except Exception:
            pass
    return {"version": 1, "sessions": {}}


def save_registry(registry: dict) -> None:
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2))


def get_session_mtime(session_dir: Path) -> float:
    """Get the most recent mtime of any file in the session directory."""
    latest = 0.0
    for item in session_dir.iterdir():
        if item.is_file():
            latest = max(latest, item.stat().st_mtime)
        elif item.is_dir() and item.name in ("uploads", "tasks", "subagents", "notifications"):
            for sub in item.iterdir():
                if sub.is_file():
                    latest = max(latest, sub.stat().st_mtime)
                elif sub.is_dir():
                    for ssub in sub.iterdir():
                        if ssub.is_file():
                            latest = max(latest, ssub.stat().st_mtime)
    return latest


# ---------------------------------------------------------------------------
# Standard Analysis (Heuristic)
# ---------------------------------------------------------------------------

@dataclass
class VIEntry:
    num: int
    turn: int
    title: str
    text: str


@dataclass
class JEEntry:
    num: int
    turn: int
    title: str
    category: str
    summary: str
    key_points: List[str]
    linked: str
    risks: List[str]
    success: List[str]


@dataclass
class IEEntry:
    num: int
    turn: int
    title: str
    target: str
    inst_type: str
    text: str
    constraints: List[str]
    priority: str
    linked: str


class HeuristicAnalyzer:
    """Extract VI, JE, IE entries from session turns using heuristics."""

    COMMAND_VERBS = {
        'make', 'create', 'build', 'fix', 'add', 'remove', 'change', 'update',
        'delete', 'write', 'run', 'test', 'check', 'show', 'find', 'search',
        'get', 'set', 'install', 'configure', 'implement', 'refactor',
        'optimize', 'debug', 'deploy', 'generate', 'extract', 'convert',
        'parse', 'format', 'render', 'display', 'print', 'output', 'save',
        'export', 'import', 'load', 'store', 'push', 'pull', 'send',
        'process', 'analyze', 'review', 'audit', 'scan', 'monitor',
        'start', 'stop', 'restart', 'kill', 'watch', 'listen', 'track',
        'compare', 'merge', 'split', 'combine', 'organize', 'sort',
        'filter', 'group', 'map', 'reduce', 'transform', 'clean',
        'validate', 'verify', 'ensure', 'confirm', 'approve',
        'move', 'copy', 'rename', 'link', 'unlink', 'chmod', 'chown',
        'schedule', 'trigger', 'execute', 'perform', 'apply',
        'set', 'unset', 'enable', 'disable', 'toggle', 'switch',
        'use', 'try', 'attempt', 'consider', 'look', 'see',
        'give', 'tell', 'explain', 'describe', 'document', 'note',
        'remember', 'keep', 'maintain', 'preserve', 'archive',
        'help', 'assist', 'support', 'guide', 'lead', 'direct',
        'ask', 'request', 'demand', 'require', 'need', 'want',
        'should', 'must', 'have to', 'supposed to', 'expected to',
        'let', 'lets', "let's",
    }

    DECISION_KWS = [
        'decided', 'decision', 'going with', 'choose', 'chosen', 'pick',
        'picking', 'select', 'selected', 'opt for', 'settled on',
        'going to use', 'final choice', 'settled', 'agreed on',
    ]

    PROGRESS_KWS = [
        'done', 'completed', 'finished', 'working', 'implemented',
        'accomplished', 'achieved', 'resolved', 'fixed', 'built',
        'created', 'established', 'set up', 'configured',
    ]

    EXPERIMENT_KWS = [
        'try', 'test', 'experiment', 'see if', "let's see", 'attempt',
        'prototype', 'mockup', 'draft', 'poc', 'proof of concept',
        'evaluate', 'assess', 'gauge', 'measure', 'benchmark',
    ]

    FAILURE_KWS = [
        'failed', 'doesn\'t work', 'does not work', 'broke', 'broken',
        'error', 'wrong', 'issue', 'problem', 'bug', 'crash',
        'not working', 'won\'t', 'would not', 'could not', 'unable',
        'missing', 'lost', 'corrupted', 'timeout', 'rejected',
    ]

    PIVOT_KWS = [
        'instead', 'changing', 'switching', 'pivot', 'revert',
        'going back', 'abandon', 'drop', 'scrap', 'replace with',
        'rather than', 'as opposed to', 'flip', 'reverse',
        'undo', 'redo', 'start over', 'from scratch',
    ]

    ARCHITECTURE_KWS = [
        'design', 'structure', 'pattern', 'architecture', 'model',
        'schema', 'framework', 'layout', 'organization', 'hierarchy',
        'component', 'module', 'layer', 'tier', 'pipeline',
        'flow', 'diagram', 'system', 'platform', 'infrastructure',
    ]

    INSIGHT_KWS = [
        'realized', 'figured out', 'discovered', 'turns out',
        'i see', 'understand now', 'makes sense', 'ah ha',
        'eureka', 'breakthrough', 'key insight', 'important',
        'critical', 'essential', 'fundamental', 'core',
    ]

    def __init__(self, turns: List[Turn], title: str):
        self.turns = turns
        self.title = title
        self.vis: List[VIEntry] = []
        self.jes: List[JEEntry] = []
        self.ies: List[IEEntry] = []

    def analyze(self) -> None:
        for turn in self.turns:
            self._analyze_turn(turn)

    def _analyze_turn(self, turn: Turn) -> None:
        user_text = turn.user_message.strip()
        user_lower = user_text.lower()
        if not user_text:
            return

        # VI: Verbatim Instructions
        vi = self._extract_vi(turn, user_text, user_lower)
        if vi:
            self.vis.append(vi)

        # JE: Journal Entries
        je = self._extract_je(turn, user_text, user_lower)
        if je:
            self.jes.append(je)

        # IE: Instruction Entries (from high-signal VIs)
        if vi and len(user_text) > 50:
            ie = self._extract_ie(turn, vi)
            if ie:
                self.ies.append(ie)

    def _extract_vi(self, turn: Turn, text: str, lower: str) -> Optional[VIEntry]:
        lines = text.split('\n')
        first_line = lines[0].strip()
        first_words = first_line.split()[:3]

        is_command = False
        # Check if first word is a command verb
        for word in first_words:
            clean = word.lower().rstrip('.,:;!?')
            if clean in self.COMMAND_VERBS:
                is_command = True
                break

        # Check for explicit instruction patterns
        instruction_patterns = [
            'we need to', 'i want you to', 'make sure', 'ensure that',
            'please', 'can you', 'could you', 'would you',
            'i need', 'we should', 'you should', 'need to',
            'has to', 'got to', 'wanna', 'want to',
        ]
        for pat in instruction_patterns:
            if pat in lower:
                is_command = True
                break

        # Check for numbered/bulleted instructions
        if re.search(r'^\s*(\d+[.):\-]\s+|[-*+]\s+)', text, re.MULTILINE):
            if len(text) > 30:
                is_command = True

        if not is_command:
            return None

        title = self._make_title(text)
        return VIEntry(
            num=len(self.vis) + 1,
            turn=turn.turn_number,
            title=title,
            text=text,
        )

    def _extract_je(self, turn: Turn, text: str, lower: str) -> Optional[JEEntry]:
        category = None
        kws = []

        for kw in self.DECISION_KWS:
            if kw in lower:
                category = 'Decision'
                kws.append(kw)
                break
        if not category:
            for kw in self.PROGRESS_KWS:
                if kw in lower:
                    category = 'Progress'
                    kws.append(kw)
                    break
        if not category:
            for kw in self.EXPERIMENT_KWS:
                if kw in lower:
                    category = 'Experiment'
                    kws.append(kw)
                    break
        if not category:
            for kw in self.FAILURE_KWS:
                if kw in lower:
                    category = 'Failure'
                    kws.append(kw)
                    break
        if not category:
            for kw in self.PIVOT_KWS:
                if kw in lower:
                    category = 'Pivot'
                    kws.append(kw)
                    break
        if not category:
            for kw in self.ARCHITECTURE_KWS:
                if kw in lower:
                    category = 'Architecture'
                    kws.append(kw)
                    break
        if not category:
            for kw in self.INSIGHT_KWS:
                if kw in lower:
                    category = 'Insight'
                    kws.append(kw)
                    break

        if not category:
            return None

        title = self._make_title(text)
        # Extract key points: sentences or bullet lines
        key_points = []
        for line in text.split('\n'):
            line = line.strip()
            if line and len(line) > 10 and not line.startswith('#'):
                key_points.append(line)
        if not key_points:
            key_points = [text[:200]]

        return JEEntry(
            num=len(self.jes) + 1,
            turn=turn.turn_number,
            title=title,
            category=category,
            summary=self._summarize(text),
            key_points=key_points[:5],
            linked=f"Turn {turn.turn_number}",
            risks=["N/A"],
            success=["N/A"],
        )

    def _extract_ie(self, turn: Turn, vi: VIEntry) -> Optional[IEEntry]:
        # Only create IE for substantial instructions
        if len(vi.text) < 60:
            return None

        # Determine target agent and type from context
        lower = vi.text.lower()
        target = "Operator"
        if any(w in lower for w in ['design', 'ui', 'ux', 'layout', 'color', 'font', 'css', 'style']):
            target = "Architect"
        elif any(w in lower for w in ['test', 'debug', 'fix', 'bug', 'error', 'issue']):
            target = "Head Coach"
        elif any(w in lower for w in ['data', 'metric', 'stat', 'analytic', 'performance']):
            target = "Stat Analyst"
        elif any(w in lower for w in ['search', 'find', 'scout', 'discover', 'identify']):
            target = "Scout"

        inst_type = "Behavior"
        if any(w in lower for w in ['design', 'architecture', 'structure', 'pattern', 'model']):
            inst_type = "Architecture"
        elif any(w in lower for w in ['rule', 'policy', 'standard', 'protocol', 'guideline']):
            inst_type = "Rule"
        elif any(w in lower for w in ['workflow', 'process', 'pipeline', 'flow']):
            inst_type = "Workflow"

        priority = "Medium"
        if any(w in lower for w in ['must', 'need to', 'have to', 'critical', 'urgent', 'important']):
            priority = "High"
        elif any(w in lower for w in ['maybe', 'consider', 'possibly', 'if you want', 'optional']):
            priority = "Low"

        constraints = []
        if 'no ' in lower or 'not ' in lower or 'without' in lower:
            constraints.append("Negative constraints detected in instruction")
        if 'only' in lower or 'just' in lower:
            constraints.append("Scope limiting language detected")
        if not constraints:
            constraints = ["N/A"]

        return IEEntry(
            num=len(self.ies) + 1,
            turn=turn.turn_number,
            title=vi.title,
            target=target,
            inst_type=inst_type,
            text=vi.text,
            constraints=constraints,
            priority=priority,
            linked=f"Turn {turn.turn_number} (VI-{vi.num})",
        )

    def _make_title(self, text: str) -> str:
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if not lines:
            return "Untitled"
        first = lines[0]
        # Remove markdown headers
        first = re.sub(r'^#{1,6}\s*', '', first)
        # Remove common prefixes
        first = re.sub(r'^(User|Assistant|Bot|AI):\s*', '', first, flags=re.I)
        # Truncate
        if len(first) > 60:
            first = first[:57] + '...'
        return first or "Untitled"

    def _summarize(self, text: str) -> str:
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        if sentences:
            summary = sentences[0]
            if len(summary) < 30 and len(sentences) > 1:
                summary += ' ' + sentences[1]
            if len(summary) > 200:
                summary = summary[:197] + '...'
            return summary
        return text[:200]

    def generate_report(self) -> str:
        now = datetime.now().isoformat()
        lines = []
        lines.append("Peacock Journal Architect – Processing Report")
        lines.append("Version: 1.1")
        lines.append(f"Processed: {now}")
        lines.append(f"Chat Length: {len(self.turns)} turns")
        lines.append("")

        lines.append("DIRECT VERBATIM INSTRUCTIONS")
        if self.vis:
            for vi in self.vis:
                lines.append(f"VI-{vi.num:03d}: {vi.title}")
                lines.append(f"Original User Message (verbatim):{vi.text}")
                lines.append("")
        else:
            lines.append("No direct verbatim instructions detected.")
            lines.append("")

        lines.append("JOURNAL ENTRIES")
        if self.jes:
            for je in self.jes:
                lines.append(f"JE-{je.num:03d}: {je.title}")
                lines.append(f"Category: {je.category}")
                lines.append(f"Summary: {je.summary}")
                lines.append("Key Points:")
                for kp in je.key_points:
                    lines.append(f"- {kp}")
                lines.append(f"Linked Messages: {je.linked}")
                lines.append("Risks / Constraints:")
                for r in je.risks:
                    lines.append(f"- {r}")
                lines.append("Success Criteria:")
                for s in je.success:
                    lines.append(f"- {s}")
                lines.append("")
        else:
            lines.append("No journal entries detected.")
            lines.append("")

        lines.append("INSTRUCTION ENTRIES")
        if self.ies:
            for ie in self.ies:
                lines.append(f"IE-{ie.num:03d}: {ie.title}")
                lines.append(f"Target Agent: {ie.target}")
                lines.append(f"Instruction Type: {ie.inst_type}")
                lines.append(f"Full Clear Instruction Text: {ie.text}")
                lines.append("Must-Haves / Constraints:")
                for c in ie.constraints:
                    lines.append(f"- {c}")
                lines.append(f"Priority: {ie.priority}")
                lines.append(f"Linked Messages: {ie.linked}")
                lines.append("")
        else:
            lines.append("No instruction entries detected.")
            lines.append("")

        lines.append("SUMMARY")
        lines.append(f"Total Verbatim Instructions: {len(self.vis)}")
        lines.append(f"Total Journal Entries: {len(self.jes)}")
        lines.append(f"Total Instruction Entries: {len(self.ies)}")

        # Key themes
        themes = set()
        for je in self.jes:
            themes.add(je.category)
        for vi in self.vis:
            # Extract key nouns from title
            words = vi.title.lower().split()
            for w in words:
                if len(w) > 4 and w not in {'should', 'would', 'could', 'this', 'that', 'with', 'from', 'have', 'been', 'were'}:
                    themes.add(w)
        theme_str = ', '.join(sorted(themes))[:200] or "N/A"
        lines.append(f"Key Themes Identified: {theme_str}")
        lines.append("")
        lines.append("Ready to copy into WALDO.")

        return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Processing
# ---------------------------------------------------------------------------

def safe_title(title: str) -> str:
    return re.sub(r'[^\w\-]+', '_', title.lower()).strip('_')[:40] or "session"


def generate_slug(title: str) -> str:
    """Generate a kebab-case slug from the session title."""
    words = re.findall(r'[a-zA-Z]+', title.lower())
    # Filter to meaningful words
    stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'}
    filtered = [w for w in words if w not in stopwords and len(w) > 2]
    if not filtered:
        filtered = [w for w in words if len(w) > 2]
    if not filtered:
        filtered = words
    slug = '-'.join(filtered[:4])
    return slug or "untitled"


def process_session(session_dir: Path, session: SessionData, registry: dict) -> dict:
    """Process a single session: generate transcripts and standard report."""
    session_id = session_dir.name
    project_id = session_dir.parent.name
    title = session.title
    safe = safe_title(title)
    slug = generate_slug(title)
    now = datetime.now()
    date_str = now.strftime("%m-%d.%y")

    # --- Transcripts into session dir ---
    trans_dir = session_dir / "transcripts"
    trans_dir.mkdir(exist_ok=True)

    base_name = f"{safe}_{session_id[:8]}"
    html_path = trans_dir / f"{base_name}.html"
    md_path = trans_dir / f"{base_name}.md"
    txt_path = trans_dir / f"{base_name}.txt"
    code_path = trans_dir / f"{base_name}_code.md"

    html_path.write_text(generate_html(session))
    md_path.write_text(generate_md(session))
    txt_path.write_text(generate_txt(session))
    code_path.write_text(generate_code_md(session))

    # --- Standard report into session dir ---
    std_dir = session_dir / "standard"
    std_dir.mkdir(exist_ok=True)

    # Archive existing standard report
    existing = list(std_dir.glob("standard.created.from.chat.*.md"))
    archive_dir = std_dir / "archive"
    archive_dir.mkdir(exist_ok=True)
    for old in existing:
        ts = now.strftime("%H%M%S")
        archive_name = old.stem + f"_{ts}.md"
        shutil.move(str(old), str(archive_dir / archive_name))

    # Generate new standard report
    analyzer = HeuristicAnalyzer(session.turns, title)
    analyzer.analyze()
    report = analyzer.generate_report()

    std_name = f"standard.created.from.chat.{slug}.{date_str}.md"
    std_path = std_dir / std_name
    std_path.write_text(report)

    # --- Copy to central archive ---
    project_name = get_project_name(project_id)
    arc_session = ARCHIVE_ROOT / project_name / session_id
    arc_trans = arc_session / "transcripts"
    arc_std = arc_session / "standard"
    arc_std_archive = arc_std / "archive"

    arc_trans.mkdir(parents=True, exist_ok=True)
    arc_std.mkdir(parents=True, exist_ok=True)
    arc_std_archive.mkdir(exist_ok=True)

    shutil.copy2(str(html_path), str(arc_trans / html_path.name))
    shutil.copy2(str(md_path), str(arc_trans / md_path.name))
    shutil.copy2(str(txt_path), str(arc_trans / txt_path.name))
    shutil.copy2(str(code_path), str(arc_trans / code_path.name))
    shutil.copy2(str(std_path), str(arc_std / std_path.name))

    # Copy archived standard reports too
    for archived in archive_dir.glob("*.md"):
        shutil.copy2(str(archived), str(arc_std_archive / archived.name))

    # Update registry
    registry["sessions"][session_id] = {
        "last_processed": time.time(),
        "context_mtime": get_session_mtime(session_dir),
        "title": title,
        "turn_count": len(session.turns),
        "word_count": session.total_words,
        "code_blocks": session.total_code_blocks,
        "images": session.total_images,
        "vi_count": len(analyzer.vis),
        "je_count": len(analyzer.jes),
        "ie_count": len(analyzer.ies),
        "transcript_outputs": [str(html_path.name), str(md_path.name), str(txt_path.name), str(code_path.name)],
        "standard_output": str(std_path.name),
    }

    print(f"  [OK] {title}: {len(session.turns)} turns, {len(analyzer.vis)} VI, {len(analyzer.jes)} JE, {len(analyzer.ies)} IE")
    return registry


def extract_session_description(session_id: str, project_id: str) -> str:
    """Extract a short description from the session's standard report."""
    project_name = get_project_name(project_id)
    std_dir = ARCHIVE_ROOT / project_name / session_id / "standard"
    if not std_dir.exists():
        return ""
    # Find the latest standard report (not in archive)
    reports = [f for f in std_dir.iterdir() if f.suffix == ".md" and f.name.startswith("standard.created.from.chat")]
    if not reports:
        return ""
    latest = max(reports, key=lambda f: f.stat().st_mtime)
    try:
        content = latest.read_text()
        # Try to extract first VI title
        vi_match = re.search(r'VI-\d+:\s*(.+)', content)
        if vi_match:
            desc = vi_match.group(1).strip()
            if len(desc) > 120:
                desc = desc[:117] + "..."
            return desc
        # Try first JE title
        je_match = re.search(r'JE-\d+:\s*(.+)', content)
        if je_match:
            desc = je_match.group(1).strip()
            if len(desc) > 120:
                desc = desc[:117] + "..."
            return desc
        # Fallback: first non-empty line after header
        for line in content.split('\n')[5:]:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('---'):
                if len(line) > 120:
                    line = line[:117] + "..."
                return line
    except Exception:
        pass
    return ""


def generate_manager_html(registry: dict) -> None:
    """Generate the session manager HTML in the archive root."""
    sessions_data = []
    for sid, data in registry.get("sessions", {}).items():
        # Find project ID from archive structure
        project_id = data.get("project_id", "default")
        
        desc = extract_session_description(sid, project_id)
        sessions_data.append({
            "id": sid,
            "project": project_id,
            "title": data.get("title", "Untitled"),
            "custom_title": data.get("custom_title", ""),
            "turns": data.get("turn_count", 0),
            "words": data.get("word_count", 0),
            "vi": data.get("vi_count", 0),
            "je": data.get("je_count", 0),
            "ie": data.get("ie_count", 0),
            "code": data.get("code_blocks", 0),
            "images": data.get("images", 0),
            "desc": desc,
            "ts": data.get("last_processed", 0),
        })

    # Sort by most recently processed first
    sessions_data.sort(key=lambda x: x["ts"], reverse=True)

    sessions_json = json.dumps(sessions_data, ensure_ascii=False)
    sessions_json_safe = sessions_json.replace('</script>', '<\\/script>').replace('</SCRIPT>', '<\\/SCRIPT>')

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Session Manager — {len(sessions_data)} Sessions</title>
<style>
:root {{
  --bg: #0d0d0d;
  --bg-left: rgba(20, 35, 60, 0.35);
  --bg-right: rgba(40, 40, 40, 0.35);
  --border: #444;
  --border-light: #333;
  --text: #e0e0e0;
  --text-dim: #888;
  --accent: #4a9eff;
  --accent-hover: #6bb3ff;
  --btn-bg: #2a2a2a;
  --btn-hover: #3a3a3a;
  --success: #4caf50;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-size: 14px;
  line-height: 1.6;
  padding: 0;
  margin: 0;
}}
header {{
  background: #111;
  padding: 20px 40px;
  border-bottom: 2px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 100;
}}
.controls {{ display: flex; gap: 15px; align-items: center; }}
input[type="text"] {{
  background: #1a1a1a;
  border: 1px solid var(--border);
  color: #fff;
  padding: 8px 12px;
  border-radius: 4px;
  outline: none;
}}
input[type="text"]:focus {{ border-color: var(--accent); }}
button {{
  background: var(--btn-bg);
  border: 1px solid var(--border);
  color: #ccc;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
}}
button:hover {{ background: var(--btn-hover); color: #fff; }}
button.primary {{ background: var(--accent); border-color: var(--accent); color: #fff; }}

#sessions-container {{
  max-width: 1400px;
  margin: 0 auto;
  border-left: 2px solid var(--border);
  border-right: 2px solid var(--border);
}}
.session-row {{
  display: grid;
  grid-template-columns: 1fr 60px 1fr;
  border-bottom: 2px solid var(--border);
  min-height: 120px;
}}
.session-left {{
  background: var(--bg-left);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}}
.session-id {{ font-family: monospace; color: var(--text-dim); font-size: 12px; }}
.session-title {{ font-size: 18px; font-weight: bold; color: var(--accent); }}
.rename-field {{ margin-top: 5px; width: 100%; }}

.session-divider {{
  border-left: 2px solid var(--border);
  border-right: 2px solid var(--border);
  background: #151515;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  color: #555;
}}
.session-right {{
  background: var(--bg-right);
  padding: 20px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}}
.session-desc {{ color: #ccc; font-style: italic; }}
.session-stats {{ font-size: 11px; color: var(--text-dim); margin-top: 10px; display: flex; gap: 15px; }}

.saved-badge {{
  display: none;
  font-size: 10px;
  color: var(--success);
  margin-top: 5px;
}}
.saved-badge.show {{ display: block; }}

.actions {{ margin-top: 15px; display: flex; gap: 10px; }}
.actions a {{ color: var(--accent); text-decoration: none; font-size: 12px; }}
.actions a:hover {{ text-decoration: underline; }}

@media (max-width: 1000px) {{
  .session-row {{ grid-template-columns: 1fr; }}
  .session-divider {{ display: none; }}
  #sessions-container {{ border: none; }}
}}
</style>
</head>
<body>

<header>
  <div>
    <h1>Peacock Session Manager</h1>
    <p style="color: var(--text-dim);">Archive: {ARCHIVE_ROOT}</p>
  </div>
  <div class="controls">
    <input type="text" id="search-input" placeholder="Search sessions..." oninput="doSearch()">
    <button onclick="exportRenames()" title="Download JSON to apply with --apply-renames">Export for Daemon</button>
  </div>
</header>

<div id="sessions-container"></div>

<div id="no-results" style="padding: 100px; text-align: center; color: var(--text-dim); display: none;">
  No sessions matching your search.
</div>

<script>
const sessions = {sessions_json_safe};
const RENAME_KEY = 'peacock_session_renames';

function loadRenames() {{
  return JSON.parse(localStorage.getItem(RENAME_KEY) || '{{}}');
}}

function saveRenames(renames) {{
  localStorage.setItem(RENAME_KEY, JSON.stringify(renames));
}}

function formatDate(ts) {{
  if (!ts) return '';
  const d = new Date(ts * 1000);
  return d.toLocaleDateString();
}}

function renderSessions(filtered) {{
  const container = document.getElementById('sessions-container');
  container.innerHTML = '';
  const renames = loadRenames();

  filtered.forEach(s => {{
    const customName = renames[s.id] || s.custom_title || '';
    const displayTitle = customName || s.title;
    
    const row = document.createElement('div');
    row.className = 'session-row';
    row.innerHTML = `
      <div class="session-left">
        <div class="session-id">${{s.id}}</div>
        <div class="session-title">${{displayTitle}}</div>
        <input type="text" class="rename-field" placeholder="Custom name..." value="${{customName}}" 
               onchange="handleRename('${{s.id}}', this.value)">
        <div class="saved-badge" id="badge-${{s.id}}">Saved to Browser</div>
        <div class="actions">
          <a href="./${{s.project}}/${{s.id}}/transcripts/" target="_blank">View Transcripts</a>
          <a href="./${{s.project}}/${{s.id}}/standard/" target="_blank">View Standard Reports</a>
        </div>
      </div>
      <div class="session-divider">
        <div style="font-size: 20px;">#</div>
        <div style="font-size: 10px; margin-top: 5px;">${{formatDate(s.ts)}}</div>
      </div>
      <div class="session-right">
        <div class="session-desc">${{s.desc || 'No summary available.'}}</div>
        <div class="session-stats">
          <span>${{s.turns}} turns</span>
          <span>VI: ${{s.vi}}</span>
          <span>JE: ${{s.je}}</span>
          <span>IE: ${{s.ie}}</span>
        </div>
      </div>
    `;
    container.appendChild(row);
  }});
  
  document.getElementById('no-results').style.display = filtered.length ? 'none' : 'block';
}}

function handleRename(id, value) {{
  const renames = loadRenames();
  if (value.trim()) renames[id] = value.trim();
  else delete renames[id];
  saveRenames(renames);
  
  const badge = document.getElementById('badge-' + id);
  badge.classList.add('show');
  setTimeout(() => badge.classList.remove('show'), 2000);
}}

function doSearch() {{
  const q = document.getElementById('search-input').value.toLowerCase();
  const filtered = sessions.filter(s => 
    s.id.toLowerCase().includes(q) || 
    s.title.toLowerCase().includes(q) || 
    s.desc.toLowerCase().includes(q)
  );
  renderSessions(filtered);
}}

function exportRenames() {{
  const renames = loadRenames();
  const blob = new Blob([JSON.stringify(renames, null, 2)], {{type: 'application/json'}});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'session_renames.json';
  a.click();
}}

renderSessions(sessions);
</script>
</body>
</html>
'''
    manager_path = ARCHIVE_ROOT / "session-manager.html"
    manager_path.write_text(html)
    print(f"  Session manager updated: {manager_path}")


def scan_and_process(registry: dict, force: bool = False) -> dict:
    """Scan all sessions and process new/updated ones."""
    sessions = discover_sessions()
    processed = 0
    skipped = 0
    failed = 0

    for session_dir, state in sessions:
        session_id = session_dir.name
        entry = registry.get("sessions", {}).get(session_id, {})
        current_mtime = get_session_mtime(session_dir)

        if not force and entry.get("context_mtime", 0) >= current_mtime:
            skipped += 1
            continue

        print(f"Processing {session_id}...")
        try:
            session = load_session(session_dir)
            if not session:
                failed += 1
                continue
            registry = process_session(session_dir, session, registry)
            processed += 1
        except Exception as e:
            print(f"  [FAIL] {session_id}: {e}")
            failed += 1

    # Generate session manager after processing
    try:
        generate_manager_html(registry)
    except Exception as e:
        print(f"  [WARN] Failed to generate manager HTML: {e}")

    print(f"\nScan complete: {processed} processed, {skipped} up-to-date, {failed} failed")
    return registry


# ---------------------------------------------------------------------------
# Daemon mode
# ---------------------------------------------------------------------------

running = True


def signal_handler(signum, frame):
    global running
    print(f"\nReceived signal {signum}, shutting down...")
    running = False


def run_daemon() -> None:
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Write pidfile
    PIDFILE_PATH.write_text(str(os.getpid()))

    print(f"Session Orchestrator Daemon started")
    print(f"  Watching: {SESSIONS_ROOT}")
    print(f"  Archive:  {ARCHIVE_ROOT}")
    print(f"  Registry: {REGISTRY_PATH}")
    print(f"  Poll interval: {POLL_INTERVAL}s")
    print(f"  PID: {os.getpid()}")
    print("Press Ctrl+C to stop.\n")

    # Initial full scan
    registry = load_registry()
    print("Initial scan...")
    registry = scan_and_process(registry)
    save_registry(registry)

    while running:
        time.sleep(POLL_INTERVAL)
        if not running:
            break
        print(f"\n[{datetime.now().isoformat()}] Scanning...")
        registry = load_registry()
        registry = scan_and_process(registry)
        save_registry(registry)

    # Cleanup
    PIDFILE_PATH.unlink(missing_ok=True)
    print("Daemon stopped.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
 

def apply_renames(json_path: str):
    """Read a JSON file and rename session directories in the archive."""
    path = Path(json_path)
    if not path.exists():
        print(f"Error: {json_path} not found.")
        return
        return

    try:
        new_names = json.loads(path.read_text())
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return

    registry = load_registry()
    sessions = registry.get("sessions", {})
    renamed_count = 0

    for sid, new_name in new_names.items():
        if sid not in sessions:
            print(f"  [SKIP] Session {sid} not in registry.")
            continue
        
        data = sessions[sid]
        project_id = data.get("project_id")
        project_name = get_project_name(project_id)
        
        old_path = ARCHIVE_ROOT / project_name / sid
        if not old_path.exists():
            print(f"  [WARN] Path not found: {old_path}")
            continue

        # For now, we just update the title in the registry
        # Renaming the directory is tricky because it might break links
        # Better: keep the directory ID as unique, but store the custom name
        # If user REALLY wants the dir renamed, we can do it, but let's stick to title update first
        # Wait, user said "only change the mirriors dir" - implying the dir name itself.
        
        # Clean the new name for filesystem
        clean_name = re.sub(r'[^\w\s-]', '', new_name).strip().replace(' ', '_')
        if not clean_name:
            continue
            
        new_dir_name = f"{clean_name}_{sid[:8]}"
        new_path = old_path.parent / new_dir_name
        
        if old_path == new_path:
            continue

        try:
            shutil.move(str(old_path), str(new_path))
            # Update registry
            data["custom_title"] = new_name
            data["archive_path"] = str(new_path)
            renamed_count += 1
            print(f"  [OK] Renamed {sid} -> {new_dir_name}")
        except Exception as e:
            print(f"  [FAIL] Failed to rename {sid}: {e}")

    if renamed_count > 0:
        save_registry(registry)
        print(f"\nSuccessfully renamed {renamed_count} sessions.")
    else:
        print("\nNo sessions were renamed.")

def apply_renames(json_path: str):
    """Read a JSON file and rename session directories in the archive."""
    path = Path(json_path)
    if not path.exists():
        print(f"Error: {json_path} not found.")
        return

    try:
        new_names = json.loads(path.read_text())
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return

    registry = load_registry()
    sessions = registry.get("sessions", {})
    renamed_count = 0

    for sid, new_name in new_names.items():
        if sid not in sessions:
            continue
        
        data = sessions[sid]
        project_id = data.get("project_id", "default")
        project_name = get_project_name(project_id)
        
        # Look for the current path (it might have been renamed already)
        old_path_found = None
        for p in (ARCHIVE_ROOT / project_name).iterdir():
            if p.is_dir() and p.name.endswith(sid[:8]):
                old_path_found = p
                break
        
        if not old_path_found:
            # Try original ID path
            old_path_found = ARCHIVE_ROOT / project_name / sid
            
        if not old_path_found or not old_path_found.exists():
            continue
        
        # Clean the new name for filesystem
        clean_name = re.sub(r'[^\w\s-]', '', new_name).strip().replace(' ', '_')
        if not clean_name:
            continue
            
        new_dir_name = f"{clean_name}_{sid[:8]}"
        new_path = old_path_found.parent / new_dir_name
        
        if old_path_found == new_path:
            continue

        try:
            shutil.move(str(old_path_found), str(new_path))
            data["custom_title"] = new_name
            renamed_count += 1
            print(f"  [OK] Renamed {sid[:8]} -> {new_dir_name}")
        except Exception as e:
            print(f"  [FAIL] Failed to rename {sid}: {e}")

    if renamed_count > 0:
        save_registry(registry)
        print(f"\nSuccessfully renamed {renamed_count} sessions.")
    else:
        print("\nNo sessions were renamed.")


def main():
    parser = argparse.ArgumentParser(description="Session Orchestrator Daemon")
    parser.add_argument("--daemon", action="store_true", help="Run as a background watcher daemon")
    parser.add_argument("--batch", action="store_true", help="Process all sessions once and exit")
    parser.add_argument("--status", action="store_true", help="Show registry status")
    parser.add_argument("--force", action="store_true", help="Re-process all sessions even if up-to-date")
    parser.add_argument("--apply-renames", type=str, help="Apply renames from a JSON file")
    args = parser.parse_args()

    if args.apply_renames:
        apply_renames(args.apply_renames)
        return

    if args.status:
        registry = load_registry()
        sessions = registry.get("sessions", {})
        print(f"Registry: {REGISTRY_PATH}")
        print(f"Archive:  {ARCHIVE_ROOT}")
        print(f"Tracked sessions: {len(sessions)}\n")
        if not sessions:
            print("No sessions processed yet.")
            return

        print(f"{'Session ID':<36} {'Turns':>6} {'VI':>4} {'JE':>4} {'IE':>4} {'Last Processed':>20}")
        print("-" * 80)
        for sid, data in sorted(sessions.items(), key=lambda x: x[1].get("last_processed", 0), reverse=True):
            ts = datetime.fromtimestamp(data.get("last_processed", 0)).strftime("%Y-%m-%d %H:%M:%S")
            print(f"{sid:<36} {data.get('turn_count', 0):>6} {data.get('vi_count', 0):>4} {data.get('je_count', 0):>4} {data.get('ie_count', 0):>4} {ts:>20}")
        return

    if args.batch:
        registry = load_registry()
        registry = scan_and_process(registry, force=args.force)
        save_registry(registry)
        return

    if args.daemon:
        # Check if already running
        if PIDFILE_PATH.exists():
            try:
                old_pid = int(PIDFILE_PATH.read_text().strip())
                os.kill(old_pid, 0)
                print(f"Daemon already running (PID {old_pid}).")
                print(f"Stop it first, or delete {PIDFILE_PATH}")
                sys.exit(1)
            except (OSError, ValueError):
                PIDFILE_PATH.unlink(missing_ok=True)
        run_daemon()
        return

    # Default: run batch mode
    registry = load_registry()
    registry = scan_and_process(registry, force=args.force)
    save_registry(registry)


if __name__ == "__main__":
    main()
