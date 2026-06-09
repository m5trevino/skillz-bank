#!/usr/bin/env python3
"""
Chora — Wire-aware session transcript generator for Kimi CLI.

Parses wire.jsonl (or falls back to context.jsonl) and generates four
linked files:
  - {slug}_chat.md    — conversation with code-action links
  - {slug}_code.md    — all tool arguments, results, diffs, file contents
  - {slug}_think.md   — all think blocks with action links
  - {slug}_human.md   — beautiful human-readable transcript

IDs are T{turn}.A{action} (e.g. T3.A1) so a UI can cross-reference.
"""

import argparse
import json
import os
import re
import sys
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple

SESSIONS_ROOT = Path.home() / ".kimi" / "sessions"

# AI Studio root path (fixed location)
AISTUDIO_ROOT = Path.home() / "ai-chats" / "aistudio"

# Kimi-Code new CLI root paths
KIMICODE_ROOT = Path.home() / ".kimi-code" / "sessions"

# Gemini CLI root path
GEMINI_ROOT = Path.home() / ".gemini" / "tmp"

# ChatGPT export root path (common location)
CHATGPT_ROOT = Path.home() / "ai-chats" / "chatgpt"

# Claude export root path (common location)
CLAUDE_ROOT = Path.home() / "ai-chats" / "claude"


# Default output root and source subfolder mapping
DEFAULT_OUTPUT_ROOT = Path.home() / "peacock" / "aichats"

SOURCE_FOLDERS = {
    "kimi": "kimi-og",
    "aistudio": "aistudio",
    "kimicode": "kimi-code",
    "gemini": "gemini-cli",
    "chatgpt": "chatgpt",
    "claude": "claude",
}

# Maximum lines for a code snippet in human.md before truncation
HUMAN_MAX_CODE_LINES = 120
# Maximum characters for a shell output in human.md
HUMAN_MAX_SHELL_OUTPUT = 4000

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class ToolAction:
    step: int
    tool: str
    args: str
    result: Optional[dict]

@dataclass
class Turn:
    turn_num: int
    user_input: str
    assistant_text: str
    think: str
    actions: List[ToolAction] = field(default_factory=list)

@dataclass
class SessionData:
    session_id: str
    title: str
    turns: List[Turn]
    total_actions: int = 0


class ValidationResult(NamedTuple):
    ok: bool
    chat_ok: bool
    code_ok: bool
    think_ok: bool
    human_ok: bool
    errors: List[str]


# ---------------------------------------------------------------------------
# String helpers
# ---------------------------------------------------------------------------

def _ensure_str(value) -> str:
    """Recursively coerce lists/dicts/None to a plain string."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            parts.append(_ensure_str(item))
        return "\n".join(parts)
    if isinstance(value, dict):
        # If it has a text/think key, extract that; otherwise json dump
        if "text" in value:
            return _ensure_str(value["text"])
        if "think" in value:
            return _ensure_str(value["think"])
        return json.dumps(value, ensure_ascii=False)
    return str(value)


# ---------------------------------------------------------------------------
# Session discovery
# ---------------------------------------------------------------------------

def _has_session_data(session_dir: Path) -> bool:
    """Return True if the directory contains parseable session data."""
    return (session_dir / "wire.jsonl").exists() or (session_dir / "context.jsonl").exists()


def _scan_for_sessions(root: Path) -> List[Tuple[Path, dict]]:
    """Recursively scan a directory tree for valid session folders."""
    found: List[Tuple[Path, dict]] = []
    if not root.exists():
        return found

    # A session directory has state.json AND at least one data file.
    # We scan two levels deep (project/session) and also check immediate children.
    for path in root.rglob("state.json"):
        session_dir = path.parent
        if not _has_session_data(session_dir):
            continue
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            state = {}
        found.append((session_dir, state))

    return found


def discover_sessions() -> List[Tuple[Path, dict]]:
    """Discover all sessions under the standard Kimi sessions root.

    Also scans the current working directory for local session_* folders.
    Includes archived sessions. Returns list sorted by mtime (newest first).
    """
    sessions: List[Tuple[Path, dict]] = []
    seen: set = set()

    # 1. Standard Kimi sessions tree
    if SESSIONS_ROOT.exists():
        for project_dir in SESSIONS_ROOT.iterdir():
            if not project_dir.is_dir():
                continue
            for session_dir in project_dir.iterdir():
                if not session_dir.is_dir():
                    continue
                if session_dir in seen:
                    continue
                if not _has_session_data(session_dir):
                    continue
                state_path = session_dir / "state.json"
                state: dict = {}
                if state_path.exists():
                    try:
                        state = json.loads(state_path.read_text(encoding="utf-8"))
                    except Exception:
                        pass
                sessions.append((session_dir, state))
                seen.add(session_dir)

    # 2. Local session_* directories in cwd (for dev / testing)
    cwd = Path.cwd()
    for local_dir in cwd.iterdir():
        if not local_dir.is_dir():
            continue
        if local_dir.name.startswith("session_") or local_dir.name.startswith("sess_"):
            if local_dir in seen:
                continue
            if not _has_session_data(local_dir):
                continue
            state_path = local_dir / "state.json"
            state = {}
            if state_path.exists():
                try:
                    state = json.loads(state_path.read_text(encoding="utf-8"))
                except Exception:
                    pass
            sessions.append((local_dir, state))
            seen.add(local_dir)

    sessions.sort(key=lambda item: item[0].stat().st_mtime, reverse=True)
    return sessions


def list_sessions() -> None:
    """Print a formatted list of all discovered sessions and exit."""
    sessions = discover_sessions()
    if not sessions:
        print("No sessions found.", file=sys.stderr)
        print(f"  Searched: {SESSIONS_ROOT}", file=sys.stderr)
        print("  (Sessions need state.json + wire.jsonl or context.jsonl)", file=sys.stderr)
        return

    print(f"\n📁 Found {len(sessions)} session(s):\n")
    for i, (sdir, state) in enumerate(sessions, 1):
        title = state.get("custom_title", "Untitled")
        archived = " 🗃️  archived" if state.get("archived") else ""
        mtime = datetime.fromtimestamp(sdir.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        has_wire = "📡 wire" if (sdir / "wire.jsonl").exists() else "📄 context"
        project = sdir.parent.name if sdir.parent != SESSIONS_ROOT else "local"
        print(f"  {i:3}. {title}{archived}")
        print(f"       {has_wire}  ·  {mtime}  ·  {project}/{sdir.name}")
    print()


def pick_session(interactive: bool = True) -> Optional[Path]:
    """Pick a session interactively or return the most recent one."""
    # If already inside a session directory, use it
    cwd = Path.cwd()
    try:
        rel = cwd.relative_to(SESSIONS_ROOT)
        parts = rel.parts
        if len(parts) >= 2:
            candidate = SESSIONS_ROOT / parts[0] / parts[1]
            if (candidate / "state.json").exists() and _has_session_data(candidate):
                return candidate
    except ValueError:
        pass

    sessions = discover_sessions()
    if not sessions:
        print("No sessions found.", file=sys.stderr)
        print(f"  Searched: {SESSIONS_ROOT}", file=sys.stderr)
        print("  Ensure the directory contains state.json and wire.jsonl or context.jsonl.", file=sys.stderr)
        return None

    if not interactive:
        return sessions[0][0]

    print("\nAvailable sessions:\n")
    for i, (sdir, state) in enumerate(sessions, 1):
        title = state.get("custom_title", "Untitled")
        archived = " [archived]" if state.get("archived") else ""
        mtime = datetime.fromtimestamp(sdir.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        has_wire = " 📡" if (sdir / "wire.jsonl").exists() else ""
        print(f"  {i}. {title}{archived}{has_wire}  ({mtime})")
    print("\n  0. Cancel")
    try:
        choice = input("\nPick a session: ").strip()
        if not choice.isdigit():
            print("Invalid selection — please enter a number.", file=sys.stderr)
            return None
        choice_num = int(choice)
        if choice_num == 0:
            return None
        if choice_num < 1 or choice_num > len(sessions):
            print(f"Invalid selection — choose 0–{len(sessions)}.", file=sys.stderr)
            return None
        return sessions[choice_num - 1][0]
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Invalid selection: {e}", file=sys.stderr)
        return None


def load_state(session_dir: Path) -> dict:
    state_path = session_dir / "state.json"
    if state_path.exists():
        try:
            return json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def make_slug(title: Optional[str], session_id: str) -> str:
    title = title or ""
    slug = re.sub(r"[^\w\s-]", "", title).strip().lower()
    slug = re.sub(r"[-\s]+", "_", slug)
    if not slug:
        slug = session_id[:8]
    return slug


def _extract_best_date(source_path: Path, state: dict) -> str:
    """Return the best available date as YYYY-MM-DD.

    Priority:
      1. State fields: createdAt, startTime, created_at, start_time, timestamp
      2. Filename patterns: YYYY-MM-DD, YYYY_MM_DD, YYYYMMDD
      3. File/directory mtime
      4. Today's date
    """
    # 1. State fields
    for key in ("createdAt", "startTime", "created_at", "start_time", "timestamp", "date"):
        val = state.get(key)
        if val and isinstance(val, str):
            try:
                val_clean = val.replace("Z", "+00:00")
                dt = datetime.fromisoformat(val_clean)
                return dt.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                for fmt in (
                    "%Y-%m-%dT%H:%M:%S.%f%z",
                    "%Y-%m-%dT%H:%M:%S%z",
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%d",
                ):
                    try:
                        dt = datetime.strptime(val, fmt)
                        return dt.strftime("%Y-%m-%d")
                    except ValueError:
                        continue

    # 2. Filename patterns
    name = source_path.name
    patterns = [
        r'(\d{4})-(\d{2})-(\d{2})',
        r'(\d{4})_(\d{2})_(\d{2})',
        r'(\d{4})(\d{2})(\d{2})',
    ]
    for pattern in patterns:
        m = re.search(pattern, name)
        if m:
            y, mo, d = m.groups()
            try:
                dt = datetime(int(y), int(mo), int(d))
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

    # 3. File/directory mtime
    try:
        mtime = source_path.stat().st_mtime
        return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
    except (OSError, ValueError):
        pass

    # 4. Today
    return datetime.now().strftime("%Y-%m-%d")


def _disambiguate_slug(output_dir: Path, date_str: str, slug: str) -> str:
    """Return a unique slug, appending _001, _002 etc. if the base filename collides.

    Checks for any existing file matching {date_str}_{slug}_*.md in output_dir.
    If one exists, finds the next unused counter suffix.
    """
    base = f"{date_str}_{slug}"
    pattern = f"{base}_*.md"
    existing = list(output_dir.glob(pattern))
    if not existing:
        return slug

    # Find the highest existing counter
    max_counter = 0
    for f in existing:
        # Match patterns like 2026-05-17_untitled_001_chat.md
        m = re.search(rf"{re.escape(base)}_(\d+)_[a-z]+\.md$", f.name)
        if m:
            max_counter = max(max_counter, int(m.group(1)))

    return f"{slug}_{max_counter + 1:03d}"


# ---------------------------------------------------------------------------
# Wire.jsonl parser
# ---------------------------------------------------------------------------

def parse_wire_jsonl(wire_path: Path) -> List[Turn]:
    turns: List[Turn] = []
    current_turn: Optional[Turn] = None
    current_step = 1
    pending_tool: Optional[ToolAction] = None

    with open(wire_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue

            m = msg.get("message", {})
            t = m.get("type", "unknown")
            payload = m.get("payload", {})

            if t == "TurnBegin":
                user_text = ""
                user_input = payload.get("user_input", [])
                if user_input and isinstance(user_input, list):
                    first = user_input[0]
                    if isinstance(first, dict):
                        user_text = _ensure_str(first.get("text", ""))
                    elif isinstance(first, str):
                        user_text = first
                current_turn = Turn(
                    turn_num=len(turns) + 1,
                    user_input=user_text,
                    assistant_text="",
                    think="",
                    actions=[],
                )
                turns.append(current_turn)
                current_step = 1

            elif t == "TurnEnd":
                current_turn = None
                pending_tool = None

            elif t == "StepBegin":
                current_step = payload.get("n", current_step)

            elif t == "ContentPart" and current_turn is not None:
                pt = payload.get("type", "")
                if pt == "text":
                    current_turn.assistant_text += _ensure_str(payload.get("text", ""))
                elif pt == "think":
                    think_text = _ensure_str(payload.get("think", ""))
                    if current_turn.think:
                        current_turn.think += "\n\n"
                    current_turn.think += think_text

            elif t == "ToolCall":
                fn = payload.get("function", {}).get("name", "unknown")
                args = payload.get("function", {}).get("arguments", "")
                pending_tool = ToolAction(
                    step=current_step,
                    tool=fn,
                    args=args,
                    result=None,
                )

            elif t == "ToolResult" and pending_tool is not None and current_turn is not None:
                rv = payload.get("return_value", {})
                pending_tool.result = rv
                current_turn.actions.append(pending_tool)
                pending_tool = None

    return turns


# ---------------------------------------------------------------------------
# Context.jsonl fallback parser (no tool actions, just chat)
# ---------------------------------------------------------------------------

def parse_context_jsonl(ctx_path: Path) -> List[Turn]:
    """Parse context.jsonl as a fallback when wire.jsonl is missing."""
    turns: List[Turn] = []
    pending_user_text = ""

    def _extract_text(content) -> str:
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, str):
                    parts.append(part)
                elif isinstance(part, dict):
                    t = part.get("type", "")
                    if t == "text":
                        parts.append(part.get("text", ""))
                    elif t == "think":
                        parts.append(part.get("think", ""))
                elif isinstance(part, list):
                    parts.append(_extract_text(part))
            return "\n".join(parts)
        return str(content)

    with open(ctx_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue

            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "user":
                pending_user_text = _extract_text(content)
            elif role == "assistant":
                text = _extract_text(content)
                # Separate think from text heuristically
                think = ""
                assistant_text = text
                # If content is a list, extract think parts separately
                if isinstance(content, list):
                    think_parts = []
                    text_parts = []
                    for part in content:
                        if isinstance(part, dict):
                            if part.get("type") == "think":
                                think_parts.append(part.get("think", ""))
                            elif part.get("type") == "text":
                                text_parts.append(part.get("text", ""))
                    think = "\n".join(think_parts)
                    assistant_text = "\n".join(text_parts)

                turn = Turn(
                    turn_num=len(turns) + 1,
                    user_input=pending_user_text,
                    assistant_text=assistant_text,
                    think=think,
                    actions=[],
                )
                turns.append(turn)
                pending_user_text = ""

    return turns


# ---------------------------------------------------------------------------
# AI Studio parser
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# Kimi-Code parser
# ---------------------------------------------------------------------------

def _is_kimicode_dir(path: Path) -> bool:
    """Return True if path is inside the Kimi-Code sessions root."""
    try:
        path.relative_to(KIMICODE_ROOT)
        return True
    except ValueError:
        return False


def _has_kimicode_data(session_dir: Path) -> bool:
    """Return True if the directory contains parseable Kimi-Code session data."""
    return (session_dir / "agents" / "main" / "wire.jsonl").exists()


def discover_kimicode_sources(kimicode_dir: Optional[Path] = None) -> List[Tuple[Path, dict]]:
    """Discover all Kimi-Code session sources.

    Returns a list of (session_dir, state) tuples sorted by mtime.
    Sources are:
      - sessions/ses_{uuid}/  (flat sessions)
      - sessions/wd_{project}_*/ses_{uuid}/  (project-grouped sessions)
    """
    root = kimicode_dir or KIMICODE_ROOT
    sources: List[Tuple[Path, dict]] = []
    if not root.exists():
        return sources

    # 1. Flat sessions: ses_{uuid}/
    for entry in root.iterdir():
        if not entry.is_dir():
            continue
        if entry.name.startswith("ses_"):
            if _has_kimicode_data(entry):
                state_path = entry / "state.json"
                state: dict = {}
                if state_path.exists():
                    try:
                        state = json.loads(state_path.read_text(encoding="utf-8"))
                    except Exception:
                        pass
                sources.append((entry, state))

    # 2. Project-grouped sessions: wd_{project}_*/ses_{uuid}/
    for proj_dir in root.iterdir():
        if not proj_dir.is_dir():
            continue
        if not proj_dir.name.startswith("wd_"):
            continue
        for sess_dir in proj_dir.iterdir():
            if not sess_dir.is_dir():
                continue
            if sess_dir.name.startswith("ses_"):
                if _has_kimicode_data(sess_dir):
                    state_path = sess_dir / "state.json"
                    state = {}
                    if state_path.exists():
                        try:
                            state = json.loads(state_path.read_text(encoding="utf-8"))
                        except Exception:
                            pass
                    sources.append((sess_dir, state))

    sources.sort(key=lambda item: item[0].stat().st_mtime, reverse=True)
    return sources


# ---------------------------------------------------------------------------
# Gemini CLI parser
# ---------------------------------------------------------------------------

def _is_gemini_dir(path: Path) -> bool:
    """Return True if path is inside the Gemini tmp root."""
    try:
        path.relative_to(GEMINI_ROOT)
        return True
    except ValueError:
        return False


def discover_gemini_sources(gemini_dir: Optional[Path] = None) -> List[Tuple[Path, dict]]:
    """Discover all Gemini CLI conversation sources.

    Returns a list of (source_path, metadata) tuples sorted by mtime.
    Sources are:
      - <project>/chats/session-*.jsonl  (new line-by-line JSONL)
      - <project>/chats/session-*.json   (old single JSON)
      - <project>/logs.json              (fallback simple log)
      - <project>/chats/*.jsonl          (subagent jsonl files)
    """
    root = gemini_dir or GEMINI_ROOT
    sources: List[Tuple[Path, dict]] = []
    if not root.exists():
        return sources

    for project_dir in root.iterdir():
        if not project_dir.is_dir():
            continue
        chats_dir = project_dir / "chats"
        if chats_dir.exists():
            for entry in chats_dir.iterdir():
                if not entry.is_file():
                    continue
                if entry.name.startswith("."):
                    continue
                # New format: session-*.jsonl
                if entry.suffix == ".jsonl" and entry.stem.startswith("session-"):
                    sources.append((entry, {"project": project_dir.name, "type": "jsonl"}))
                # Old format: session-*.json
                elif entry.suffix == ".json" and entry.stem.startswith("session-"):
                    sources.append((entry, {"project": project_dir.name, "type": "json"}))
                # Subagent files: *.jsonl (not session-*)
                elif entry.suffix == ".jsonl":
                    sources.append((entry, {"project": project_dir.name, "type": "subagent"}))
        # Fallback logs.json
        logs_json = project_dir / "logs.json"
        if logs_json.exists():
            sources.append((logs_json, {"project": project_dir.name, "type": "logs"}))

    sources.sort(key=lambda item: item[0].stat().st_mtime, reverse=True)
    return sources


def _is_aistudio_dir(path: Path) -> bool:
    """Return True if path is inside the AI Studio root."""
    try:
        path.relative_to(AISTUDIO_ROOT)
        return True
    except ValueError:
        return False


def discover_aistudio_sources(aistudio_dir: Optional[Path] = None) -> List[Tuple[Path, dict]]:
    """Discover all AI Studio conversation sources.

    Returns a list of (source_path, metadata) tuples sorted by mtime.
    Sources are extensionless JSON files in accounts/<gmail>/chat-logs/*.
    """
    root = aistudio_dir or AISTUDIO_ROOT
    sources: List[Tuple[Path, dict]] = []
    if not root.exists():
        return sources

    # accounts/<gmail>/chat-logs/* (extensionless JSON files)
    accounts_dir = root / "accounts"
    if accounts_dir.exists():
        for gmail_dir in accounts_dir.iterdir():
            if not gmail_dir.is_dir():
                continue
            chat_logs_dir = gmail_dir / "chat-logs"
            if not chat_logs_dir.exists():
                continue
            for entry in chat_logs_dir.iterdir():
                if entry.is_file() and not entry.name.startswith("."):
                    # Extensionless JSON files only
                    if entry.suffix == "":
                        sources.append((entry, {"account": gmail_dir.name, "type": "chat-log"}))

    sources.sort(key=lambda item: item[0].stat().st_mtime, reverse=True)
    return sources


def _extract_aistudio_text(content) -> str:
    """Extract plain text from AI Studio message content (handles string or parts array)."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict):
                if "text" in part:
                    parts.append(part["text"])
                elif "content" in part:
                    parts.append(_extract_aistudio_text(part["content"]))
            else:
                parts.append(str(part))
        return "\n".join(parts)
    return str(content)


def _extract_code_blocks(text: str) -> List[Tuple[str, str]]:
    """Extract markdown fenced code blocks from text.

    Returns list of (language, code) tuples.
    """
    pattern = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)
    results = []
    for match in pattern.finditer(text):
        lang = match.group(1).strip()
        code = match.group(2)
        results.append((lang, code))
    return results


def _extract_chatgpt_claude_text(content) -> str:
    """Extract plain text from ChatGPT/Claude message content.

    Handles string, dict with 'parts'/'text', list of parts, and
    ChatGPT-style content_type objects.
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict):
                if "text" in part:
                    parts.append(part["text"])
                elif "content" in part:
                    parts.append(_extract_chatgpt_claude_text(part["content"]))
                elif part.get("type") == "text":
                    parts.append(part.get("text", ""))
            else:
                parts.append(str(part))
        return "\n".join(parts)
    if isinstance(content, dict):
        # ChatGPT: {"content_type": "text", "parts": ["..."]}
        if "parts" in content:
            return _extract_chatgpt_claude_text(content["parts"])
        if "text" in content:
            return content["text"]
        return json.dumps(content, ensure_ascii=False)
    return str(content)


def _detect_chatgpt_claude_json(source_path: Path) -> Optional[str]:
    """Auto-detect if a JSON file is ChatGPT or Claude export format.

    Returns 'chatgpt', 'claude', or None.

    Detection rules:
      - File must be .json and parseable.
      - Top level is an array of conversation objects or a single object.
      - Each conversation has 'title' (or 'name') and a 'messages' array.
      - Messages have role: 'user' / 'assistant' (NOT 'model' which is AI Studio).
      - Distinguishes from AI Studio by checking for role='assistant'.
    """
    if not source_path.exists() or source_path.suffix != ".json":
        return None

    try:
        raw_text = source_path.read_text(encoding="utf-8", errors="ignore")
        if not raw_text.strip():
            return None
        data = json.loads(raw_text)
    except Exception:
        return None

    conversations = []
    if isinstance(data, list):
        conversations = data
    elif isinstance(data, dict):
        conversations = [data]
    else:
        return None

    if not conversations:
        return None

    conv = conversations[0]
    if not isinstance(conv, dict):
        return None

    # Accept 'messages' or 'chat_messages' (original Claude format)
    messages = conv.get("messages", conv.get("chat_messages", []))
    if not isinstance(messages, list) or not messages:
        return None

    # Must have at least one assistant role to be ChatGPT/Claude
    # (AI Studio uses "model", not "assistant")
    sample = messages[:20]
    has_assistant = any(
        isinstance(m, dict) and m.get("role") == "assistant"
        for m in sample
    )
    has_model = any(
        isinstance(m, dict) and m.get("role") == "model"
        for m in sample
    )

    if has_model and not has_assistant:
        return None  # AI Studio

    if not has_assistant:
        # Also accept original Claude format with sender="assistant"
        has_sender_assistant = any(
            isinstance(m, dict) and m.get("sender") == "assistant"
            for m in sample
        )
        if not has_sender_assistant:
            return None

    # Distinguish ChatGPT vs Claude heuristics
    # ChatGPT often has: mapping, model, model_slug, moderation_results
    if "mapping" in conv or "model" in conv or "model_slug" in conv:
        return "chatgpt"

    # Claude original format: chat_messages with sender
    if "chat_messages" in conv and any(isinstance(m, dict) and "sender" in m for m in messages):
        return "claude"

    # Filename hints
    name = source_path.name.lower()
    if "chatgpt" in name or "openai" in name:
        return "chatgpt"
    if "claude" in name or "anthropic" in name:
        return "claude"

    # Default to chatgpt since parser is identical for the simplified format
    return "chatgpt"


def parse_aistudio_json(source_path: Path) -> List[Turn]:
    """Parse an AI Studio JSON source into Turns.

    Handles two shapes:
      - A single conversation object with 'messages' key
      - A top-level array of conversation objects
    """
    raw_text = source_path.read_text(encoding="utf-8", errors="ignore")
    if not raw_text.strip():
        return []

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        return []

    conversations = []
    if isinstance(data, list):
        conversations = data
    elif isinstance(data, dict):
        if "messages" in data:
            conversations = [data]
        elif "history" in data:
            conversations = [data]
        else:
            # Maybe a single conversation wrapped differently
            conversations = [data]

    all_turns: List[Turn] = []
    turn_offset = 0

    for conv in conversations:
        if not isinstance(conv, dict):
            continue

        messages = conv.get("messages", conv.get("history", []))
        if not messages:
            continue

        pending_user = ""
        for msg in messages:
            if not isinstance(msg, dict):
                continue

            role = msg.get("role", "")
            content = msg.get("content", "")
            text = _extract_aistudio_text(content)

            if role in ("user", "human"):
                pending_user = text
            elif role in ("model", "assistant", "bot"):
                # Extract code blocks as pseudo-actions so code.md has content
                code_blocks = _extract_code_blocks(text)
                actions: List[ToolAction] = []
                for idx, (lang, code) in enumerate(code_blocks, 1):
                    # Build a pseudo ToolAction that renders nicely in code.md
                    pseudo_args = json.dumps({"language": lang, "extracted": True}, ensure_ascii=False)
                    pseudo_result = {
                        "output": code,
                        "message": f"Extracted code block ({lang or 'unknown'})",
                    }
                    actions.append(ToolAction(
                        step=idx,
                        tool="CodeBlock",
                        args=pseudo_args,
                        result=pseudo_result,
                    ))

                turn = Turn(
                    turn_num=turn_offset + 1,
                    user_input=pending_user,
                    assistant_text=text,
                    think="",
                    actions=actions,
                )
                all_turns.append(turn)
                turn_offset += 1
                pending_user = ""

    return all_turns


# ---------------------------------------------------------------------------
# ChatGPT + Claude parser
# ---------------------------------------------------------------------------

def parse_chatgpt_claude_json(source_path: Path) -> List[Turn]:
    """Parse ChatGPT or Claude JSON exports into Turns.

    Handles two shapes:
      - A top-level array of conversation objects (conversations.json)
      - A single conversation object (individual chat export)

    Each conversation object is expected to have:
      - 'title' or 'name'
      - 'messages': array of {role, content} dicts

    Also supports original Claude format with 'chat_messages' and 'sender'.

    Code blocks in assistant messages are extracted as pseudo-actions
    so _code.md has content and WALDO can browse them.
    """
    raw_text = source_path.read_text(encoding="utf-8", errors="ignore")
    if not raw_text.strip():
        return []

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        return []

    conversations = []
    if isinstance(data, list):
        conversations = data
    elif isinstance(data, dict):
        if "messages" in data or "chat_messages" in data:
            conversations = [data]
        else:
            conversations = [data]

    all_turns: List[Turn] = []
    turn_offset = 0

    for conv in conversations:
        if not isinstance(conv, dict):
            continue

        # Support both simplified format (messages) and original Claude (chat_messages)
        messages = conv.get("messages", conv.get("chat_messages", []))
        if not messages:
            continue

        pending_user = ""
        for msg in messages:
            if not isinstance(msg, dict):
                continue

            # Normalized role (handle both 'role' and 'sender' keys)
            role = msg.get("role", msg.get("sender", ""))
            content = msg.get("content", msg.get("text", ""))
            text = _extract_chatgpt_claude_text(content)

            # System messages: prepend to pending user input
            if role in ("system", "system_instruction"):
                if pending_user:
                    pending_user = f"[System]\n{text}\n\n{pending_user}"
                else:
                    pending_user = f"[System]\n{text}"
                continue

            if role in ("user", "human"):
                if pending_user.startswith("[System]"):
                    pending_user = f"{pending_user}\n\n{text}"
                else:
                    pending_user = text

            elif role in ("assistant", "bot"):
                # Extract code blocks as pseudo-actions
                code_blocks = _extract_code_blocks(text)
                actions: List[ToolAction] = []
                for idx, (lang, code) in enumerate(code_blocks, 1):
                    pseudo_args = json.dumps(
                        {"language": lang, "extracted": True}, ensure_ascii=False
                    )
                    pseudo_result = {
                        "output": code,
                        "message": f"Extracted code block ({lang or 'unknown'})",
                    }
                    actions.append(
                        ToolAction(
                            step=idx,
                            tool="CodeBlock",
                            args=pseudo_args,
                            result=pseudo_result,
                        )
                    )

                turn = Turn(
                    turn_num=turn_offset + 1,
                    user_input=pending_user,
                    assistant_text=text,
                    think="",
                    actions=actions,
                )
                all_turns.append(turn)
                turn_offset += 1
                pending_user = ""

    return all_turns


def discover_chatgpt_claude_sources(
    root_dir: Optional[Path] = None,
) -> List[Tuple[Path, str]]:
    """Discover ChatGPT/Claude JSON sources in a directory.

    Returns a list of (source_path, detected_source) tuples sorted by mtime.
    Scans for .json files and uses _detect_chatgpt_claude_json.
    """
    sources: List[Tuple[Path, str]] = []
    if not root_dir or not root_dir.exists():
        return sources

    if root_dir.is_file() and root_dir.suffix == ".json":
        detected = _detect_chatgpt_claude_json(root_dir)
        if detected:
            sources.append((root_dir, detected))
        return sources

    for entry in root_dir.rglob("*.json"):
        if entry.name.startswith("."):
            continue
        detected = _detect_chatgpt_claude_json(entry)
        if detected:
            sources.append((entry, detected))

    # Also explicit conversations.json at root
    conv_json = root_dir / "conversations.json"
    if conv_json.exists():
        detected = _detect_chatgpt_claude_json(conv_json)
        if detected:
            tup = (conv_json, detected)
            if tup not in sources:
                sources.append(tup)

    sources.sort(key=lambda item: item[0].stat().st_mtime, reverse=True)
    return sources


# ---------------------------------------------------------------------------
# Kimi-Code parser
# ---------------------------------------------------------------------------

def parse_kimicode_wire_jsonl(wire_path: Path) -> List[Turn]:
    """Parse a Kimi-Code wire.jsonl into Turns.

    The Kimi-Code format uses line-by-line JSON with types:
      - context.append_message (role=user/assistant/tool)
      - metadata, config.update, tools.set_active_tools (ignored)

    Code blocks in assistant text are extracted as pseudo-actions so _code.md
    is populated even when no explicit tool calls were made.
    """
    turns: List[Turn] = []
    current_turn: Optional[Turn] = None
    pending_tools: Dict[str, ToolAction] = {}
    current_step = 1

    def _extract_content_parts(content) -> Tuple[str, str]:
        """Extract (text, think) from Kimi-Code content array."""
        text_parts = []
        think_parts = []
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict):
                    pt = part.get("type", "")
                    if pt == "text":
                        text_parts.append(part.get("text", ""))
                    elif pt == "think":
                        think_parts.append(part.get("think", ""))
        elif isinstance(content, str):
            text_parts.append(content)
        return "\n".join(text_parts), "\n".join(think_parts)

    with open(wire_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue

            t = msg.get("type", "unknown")

            if t == "context.append_message":
                m = msg.get("message", {})
                role = m.get("role", "")
                content = m.get("content", [])

                if role == "user":
                    user_text, _ = _extract_content_parts(content)
                    current_turn = Turn(
                        turn_num=len(turns) + 1,
                        user_input=user_text,
                        assistant_text="",
                        think="",
                        actions=[],
                    )
                    turns.append(current_turn)
                    current_step = 1
                    pending_tools = {}

                elif role == "assistant" and current_turn is not None:
                    text, think = _extract_content_parts(content)
                    if text:
                        current_turn.assistant_text += text
                    if think:
                        if current_turn.think:
                            current_turn.think += "\n\n"
                        current_turn.think += think

                    # Capture tool calls from this assistant message
                    tool_calls = m.get("toolCalls", [])
                    for tc in tool_calls:
                        if isinstance(tc, dict):
                            tc_id = tc.get("id", "")
                            fn = tc.get("name", "unknown")
                            args = tc.get("arguments", "")
                            if isinstance(args, dict):
                                args = json.dumps(args, ensure_ascii=False)
                            pending_tools[tc_id] = ToolAction(
                                step=current_step,
                                tool=fn,
                                args=args,
                                result=None,
                            )
                            current_step += 1

                elif role == "tool" and current_turn is not None:
                    tc_id = m.get("toolCallId", "")
                    result_text, _ = _extract_content_parts(content)

                    if tc_id and tc_id in pending_tools:
                        pending_tools[tc_id].result = {
                            "output": result_text,
                            "message": f"Result for {pending_tools[tc_id].tool}",
                        }
                        current_turn.actions.append(pending_tools[tc_id])
                        del pending_tools[tc_id]
                    else:
                        # orphaned tool result: create generic action
                        current_turn.actions.append(ToolAction(
                            step=current_step,
                            tool="ToolResult",
                            args="{}",
                            result={"output": result_text, "message": "Orphaned tool result"},
                        ))
                        current_step += 1

            # Other types (metadata, config.update, etc.) are intentionally ignored

    # Post-process: extract markdown code blocks from assistant text as pseudo-actions
    for turn in turns:
        code_blocks = _extract_code_blocks(turn.assistant_text)
        if code_blocks:
            offset = len(turn.actions)
            for idx, (lang, code) in enumerate(code_blocks, 1):
                pseudo_args = json.dumps(
                    {"language": lang, "extracted": True}, ensure_ascii=False
                )
                pseudo_result = {
                    "output": code,
                    "message": f"Extracted code block ({lang or 'unknown'})",
                }
                turn.actions.append(
                    ToolAction(
                        step=offset + idx,
                        tool="CodeBlock",
                        args=pseudo_args,
                        result=pseudo_result,
                    )
                )

    return turns


def _extract_gemini_text(content) -> str:
    """Extract plain text from Gemini message content."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict):
                if "text" in part:
                    parts.append(part["text"])
                elif "content" in part:
                    parts.append(_extract_gemini_text(part["content"]))
        return "\n".join(parts)
    return str(content)


def _extract_gemini_thinks(msg: dict) -> str:
    """Extract think blocks from a Gemini message."""
    thoughts = msg.get("thoughts", [])
    if not thoughts:
        return ""
    parts = []
    for t in thoughts:
        if isinstance(t, dict):
            subject = t.get("subject", "")
            description = t.get("description", "")
            if subject and description:
                parts.append(f"[{subject}]\n{description}")
            elif description:
                parts.append(description)
            elif subject:
                parts.append(subject)
    return "\n\n".join(parts)


def _extract_gemini_tool_results(tool_call: dict) -> dict:
    """Extract result dict from a Gemini tool call."""
    # Prefer human-readable resultDisplay if present
    result_display = tool_call.get("resultDisplay", "")
    status = tool_call.get("status", "")
    is_error = status == "error"
    name = tool_call.get("name", "unknown")

    if result_display:
        return {
            "output": result_display,
            "message": f"Result for {name}",
            "is_error": is_error,
        }

    result = tool_call.get("result", [])
    if not result:
        return {}

    # result is usually [{"functionResponse": {"response": {...}}}]
    for item in result:
        if isinstance(item, dict) and "functionResponse" in item:
            resp = item["functionResponse"].get("response", {})
            out = resp.get("output", "")
            if out:
                return {"output": out, "message": f"Result for {name}", "is_error": is_error}
            err = resp.get("error", "")
            if err:
                return {"output": err, "message": f"Error in {name}", "is_error": True}

    # Fallback: stringify the whole result
    return {"output": json.dumps(result, ensure_ascii=False), "message": "Raw tool result", "is_error": is_error}


def parse_gemini_jsonl(source_path: Path) -> List[Turn]:
    """Parse a Gemini CLI JSONL source into Turns.

    Each line is a JSON object. Relevant types: user, gemini, assistant.
    Ignores: info, $set, metadata lines.
    """
    turns: List[Turn] = []
    pending_user = ""

    with open(source_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue

            t = msg.get("type", "unknown")
            if t == "user":
                pending_user = _extract_gemini_text(msg.get("content"))
            elif t in ("gemini", "assistant"):
                content = _extract_gemini_text(msg.get("content", ""))
                think = _extract_gemini_thinks(msg)

                actions: List[ToolAction] = []
                tool_calls = msg.get("toolCalls", [])
                for idx, tc in enumerate(tool_calls, 1):
                    if not isinstance(tc, dict):
                        continue
                    fn = tc.get("name", "unknown")
                    args = tc.get("args", "")
                    if isinstance(args, dict):
                        args = json.dumps(args, ensure_ascii=False)
                    result = _extract_gemini_tool_results(tc)
                    actions.append(ToolAction(
                        step=idx,
                        tool=fn,
                        args=args,
                        result=result,
                    ))

                # Also extract code blocks as pseudo-actions for code.md
                code_blocks = _extract_code_blocks(content)
                code_offset = len(actions)
                for idx, (lang, code) in enumerate(code_blocks, 1):
                    pseudo_args = json.dumps({"language": lang, "extracted": True}, ensure_ascii=False)
                    pseudo_result = {
                        "output": code,
                        "message": f"Extracted code block ({lang or 'unknown'})",
                    }
                    actions.append(ToolAction(
                        step=code_offset + idx,
                        tool="CodeBlock",
                        args=pseudo_args,
                        result=pseudo_result,
                    ))

                turn = Turn(
                    turn_num=len(turns) + 1,
                    user_input=pending_user,
                    assistant_text=content,
                    think=think,
                    actions=actions,
                )
                turns.append(turn)
                pending_user = ""

    return turns


def parse_gemini_json(source_path: Path) -> List[Turn]:
    """Parse an old Gemini JSON source (single file with messages array)."""
    raw_text = source_path.read_text(encoding="utf-8", errors="ignore")
    if not raw_text.strip():
        return []
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        return []

    if not isinstance(data, dict):
        return []

    messages = data.get("messages", [])
    turns: List[Turn] = []
    pending_user = ""

    for msg in messages:
        if not isinstance(msg, dict):
            continue
        t = msg.get("type", "unknown")
        if t == "user":
            pending_user = _extract_gemini_text(msg.get("content"))
        elif t in ("gemini", "assistant"):
            content = _extract_gemini_text(msg.get("content", ""))
            think = _extract_gemini_thinks(msg)

            actions: List[ToolAction] = []
            tool_calls = msg.get("toolCalls", [])
            for idx, tc in enumerate(tool_calls, 1):
                if not isinstance(tc, dict):
                    continue
                fn = tc.get("name", "unknown")
                args = tc.get("args", "")
                if isinstance(args, dict):
                    args = json.dumps(args, ensure_ascii=False)
                result = _extract_gemini_tool_results(tc)
                actions.append(ToolAction(
                    step=idx,
                    tool=fn,
                    args=args,
                    result=result,
                ))

            code_blocks = _extract_code_blocks(content)
            code_offset = len(actions)
            for idx, (lang, code) in enumerate(code_blocks, 1):
                pseudo_args = json.dumps({"language": lang, "extracted": True}, ensure_ascii=False)
                pseudo_result = {
                    "output": code,
                    "message": f"Extracted code block ({lang or 'unknown'})",
                }
                actions.append(ToolAction(
                    step=code_offset + idx,
                    tool="CodeBlock",
                    args=pseudo_args,
                    result=pseudo_result,
                ))

            turn = Turn(
                turn_num=len(turns) + 1,
                user_input=pending_user,
                assistant_text=content,
                think=think,
                actions=actions,
            )
            turns.append(turn)
            pending_user = ""

    return turns


def parse_gemini_logs_json(source_path: Path) -> List[Turn]:
    """Parse a Gemini logs.json fallback (simple array of entries)."""
    raw_text = source_path.read_text(encoding="utf-8", errors="ignore")
    if not raw_text.strip():
        return []
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        return []

    if not isinstance(data, list):
        return []

    turns: List[Turn] = []
    pending_user = ""

    for entry in data:
        if not isinstance(entry, dict):
            continue
        t = entry.get("type", "unknown")
        msg_text = entry.get("message", "")
        if t == "user":
            pending_user = _ensure_str(msg_text)
        elif t in ("gemini", "assistant"):
            turn = Turn(
                turn_num=len(turns) + 1,
                user_input=pending_user,
                assistant_text=_ensure_str(msg_text),
                think="",
                actions=[],
            )
            turns.append(turn)
            pending_user = ""

    return turns

# ---------------------------------------------------------------------------
# Markdown generators
# ---------------------------------------------------------------------------

def _detect_lang(tool_name: str, args: str) -> str:
    if tool_name == "Shell":
        return "bash"
    if tool_name == "CodeBlock":
        try:
            parsed = json.loads(args) if isinstance(args, str) else args
            return parsed.get("language", "")
        except Exception:
            return ""
    if tool_name in ("ReadFile", "WriteFile", "StrReplaceFile"):
        try:
            parsed = json.loads(args) if isinstance(args, str) else args
            fp = parsed.get("path", "")
            if fp.endswith(".py"):
                return "python"
            if fp.endswith(".js") or fp.endswith(".mjs"):
                return "javascript"
            if fp.endswith(".ts") or fp.endswith(".tsx"):
                return "typescript"
            if fp.endswith(".json"):
                return "json"
            if fp.endswith(".md"):
                return "markdown"
            if fp.endswith(".sh"):
                return "bash"
            if fp.endswith(".css"):
                return "css"
            if fp.endswith(".html"):
                return "html"
            if fp.endswith(".rs"):
                return "rust"
            if fp.endswith(".go"):
                return "go"
            if fp.endswith(".java"):
                return "java"
            if fp.endswith(".c") or fp.endswith(".cpp") or fp.endswith(".h"):
                return "cpp"
            if fp.endswith(".yaml") or fp.endswith(".yml"):
                return "yaml"
            if fp.endswith(".toml"):
                return "toml"
        except Exception:
            pass
    return ""


def generate_chat_md(turns: List[Turn], title: str) -> str:
    lines = [f"# Chat Log — {title}", "", f"> {len(turns)} turns · Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}"]
    for turn in turns:
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(f"## Turn {turn.turn_num} — User")
        lines.append("")
        lines.append(_ensure_str(turn.user_input))
        lines.append("")
        lines.append(f"## Turn {turn.turn_num} — Assistant")
        lines.append("")
        lines.append(_ensure_str(turn.assistant_text))
        if turn.actions:
            links = []
            for i, a in enumerate(turn.actions, 1):
                aid = f"T{turn.turn_num}.A{i}"
                links.append(f"[{aid}: {a.tool}](code.md#{aid.lower()})")
            lines.append("")
            lines.append(f"**🔗 Code Actions:** {' · '.join(links)}")
    lines.append("")
    return "\n".join(lines)


def generate_code_md(turns: List[Turn], title: str) -> str:
    total_actions = sum(len(t.actions) for t in turns)
    lines = [f"# Code & Tool Actions — {title}", "", f"> {total_actions} actions · Linked to chat log"]

    for turn in turns:
        for i, a in enumerate(turn.actions, 1):
            aid = f"T{turn.turn_num}.A{i}"
            lines.append("")
            lines.append("---")
            lines.append("")
            lines.append(f"## <a name=\"{aid.lower()}\"></a>{aid} — Turn {turn.turn_num}, Action {i} — `{a.tool}`")

            # Arguments
            if a.args:
                lines.append("")
                lines.append("### Arguments")
                lines.append("")
                try:
                    parsed = json.loads(a.args) if isinstance(a.args, str) else a.args
                    lines.append(f"```json")
                    lines.append(json.dumps(parsed, indent=2, ensure_ascii=False))
                    lines.append("```")
                except Exception:
                    lines.append(f"```")
                    lines.append(str(a.args))
                    lines.append("```")

            # Result
            rv = a.result or {}
            if rv:
                lines.append("")
                lines.append("### Result")
                lines.append("")
                if rv.get("is_error"):
                    lines.append("**❌ Error**")
                else:
                    lines.append("**✅ Success**")

                msg = _ensure_str(rv.get("message", ""))
                if msg:
                    lines.append("")
                    lines.append(f"> {msg}")

                # Output
                out = _ensure_str(rv.get("output", ""))
                if out:
                    lang = _detect_lang(a.tool, a.args)
                    lines.append("")
                    lines.append(f"```{lang}")
                    lines.append(out)
                    lines.append("```")

                # Display diffs (StrReplaceFile)
                displays = rv.get("display", [])
                for disp in displays:
                    if disp.get("type") == "diff":
                        lines.append("")
                        lines.append(f"### Diff — `{disp.get('path', 'unknown')}`")
                        old_start = disp.get("old_start", "?")
                        new_start = disp.get("new_start", "?")
                        lines.append(f"")
                        lines.append(f"> Lines {old_start} → {new_start}")
                        old_text = _ensure_str(disp.get("old_text", ""))
                        new_text = _ensure_str(disp.get("new_text", ""))
                        if old_text or new_text:
                            lines.append("")
                            lines.append("```diff")
                            for ln in old_text.splitlines():
                                lines.append(f"- {ln}")
                            for ln in new_text.splitlines():
                                lines.append(f"+ {ln}")
                            lines.append("```")

    lines.append("")
    return "\n".join(lines)


def generate_think_md(turns: List[Turn], title: str) -> str:
    lines = [f"# Think Blocks — {title}", "", f"> {len(turns)} turns · Linked to chat log"]
    for turn in turns:
        if not turn.think and not turn.actions:
            continue
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(f"## <a name=\"t{turn.turn_num}\"></a>T{turn.turn_num} — Turn {turn.turn_num}")
        lines.append("")
        if turn.think:
            lines.append("```")
            lines.append(_ensure_str(turn.think))
            lines.append("```")
        else:
            lines.append("*(no think block in this turn)*")

        if turn.actions:
            links = []
            for i, a in enumerate(turn.actions, 1):
                aid = f"T{turn.turn_num}.A{i}"
                links.append(f"[{aid}: {a.tool}](code.md#{aid.lower()})")
            lines.append("")
            lines.append(f"**🔗 Code Actions:** {' · '.join(links)}")

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Human-readable markdown generator (polished)
# ---------------------------------------------------------------------------

def _action_summary_human(action: ToolAction) -> Tuple[str, str, str]:
    """Return (label, subtitle, body) for a tool action in human-readable form."""
    tool = action.tool
    args = action.args
    result = action.result or {}

    def _parse_args():
        try:
            return json.loads(args) if isinstance(args, str) else args
        except Exception:
            return {}

    parsed = _parse_args()
    path = parsed.get("path", "")
    lang = _detect_lang(tool, args)

    # CodeBlock (AI Studio pseudo-action)
    if tool == "CodeBlock":
        out = _ensure_str(result.get("output", ""))
        lines = out.splitlines()
        if len(lines) > HUMAN_MAX_CODE_LINES:
            out = "\n".join(lines[:HUMAN_MAX_CODE_LINES]) + f"\n\n... ({len(lines) - HUMAN_MAX_CODE_LINES} lines truncated)"
        label = f"📦 Code Block ({lang or 'unknown'})"
        return label, "", out

    # Shell
    if tool == "Shell":
        cmd = _ensure_str(parsed.get("command", ""))
        out = _ensure_str(result.get("output", ""))
        if len(out) > HUMAN_MAX_SHELL_OUTPUT:
            out = out[:HUMAN_MAX_SHELL_OUTPUT] + f"\n\n... ({len(out) - HUMAN_MAX_SHELL_OUTPUT} chars truncated)"
        return "🖥️  Shell", f"`{cmd}`", out

    # WriteFile
    if tool == "WriteFile":
        content = _ensure_str(parsed.get("content", ""))
        lines = content.splitlines()
        if len(lines) > HUMAN_MAX_CODE_LINES:
            content = "\n".join(lines[:HUMAN_MAX_CODE_LINES]) + f"\n\n... ({len(lines) - HUMAN_MAX_CODE_LINES} lines truncated)"
        return "✍️  WriteFile", f"`{path}`", content

    # ReadFile
    if tool == "ReadFile":
        out = _ensure_str(result.get("output", ""))
        lines = out.splitlines()
        if len(lines) > HUMAN_MAX_CODE_LINES:
            out = "\n".join(lines[:HUMAN_MAX_CODE_LINES]) + f"\n\n... ({len(lines) - HUMAN_MAX_CODE_LINES} lines truncated)"
        return "📖 ReadFile", f"`{path}`", out

    # StrReplaceFile
    if tool == "StrReplaceFile":
        diffs = []
        displays = result.get("display", [])
        for disp in displays:
            if disp.get("type") == "diff":
                old_text = _ensure_str(disp.get("old_text", ""))
                new_text = _ensure_str(disp.get("new_text", ""))
                diffs.append(f"--- old")
                diffs.extend(old_text.splitlines())
                diffs.append(f"+++ new")
                diffs.extend(new_text.splitlines())
        body = "\n".join(diffs) if diffs else "*(no diff data)*"
        lines = body.splitlines()
        if len(lines) > HUMAN_MAX_CODE_LINES:
            body = "\n".join(lines[:HUMAN_MAX_CODE_LINES]) + f"\n\n... ({len(lines) - HUMAN_MAX_CODE_LINES} lines truncated)"
        return "🔧 StrReplaceFile", f"`{path}`", body

    # Edit (generic fallback for file-editing tools)
    if tool in ("Edit", "StrReplace"):
        old_text = _ensure_str(parsed.get("old_string", ""))
        new_text = _ensure_str(parsed.get("new_string", ""))
        lines = []
        lines.append("--- old")
        lines.extend(old_text.splitlines())
        lines.append("+++ new")
        lines.extend(new_text.splitlines())
        body = "\n".join(lines) if (old_text or new_text) else "*(no edit data)*"
        line_list = body.splitlines()
        if len(line_list) > HUMAN_MAX_CODE_LINES:
            body = "\n".join(line_list[:HUMAN_MAX_CODE_LINES]) + f"\n\n... ({len(line_list) - HUMAN_MAX_CODE_LINES} lines truncated)"
        return tool, f"`{path}`", body

    # Generic fallback
    out = _ensure_str(result.get("output", ""))
    msg = _ensure_str(result.get("message", ""))
    body = out or msg or "*(no output)*"
    if len(body) > HUMAN_MAX_SHELL_OUTPUT:
        body = body[:HUMAN_MAX_SHELL_OUTPUT] + f"\n\n... ({len(body) - HUMAN_MAX_SHELL_OUTPUT} chars truncated)"
    return tool, "", body


def generate_human_md(turns: List[Turn], title: str) -> str:
    """Generate a beautifully formatted standalone-readable transcript.

    Interleaves chat turns, think blocks, and key code snippets in natural
    reading order. Designed for ``cat``, ``less``, or any plain editor.
    """
    total_actions = sum(len(t.actions) for t in turns)
    think_count = sum(1 for t in turns if t.think.strip())

    lines = [
        f"# {title}",
        "",
        f"*{len(turns)} turns · {total_actions} actions · {think_count} think blocks · {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        "=" * 60,
        "",
    ]

    for turn in turns:
        # Turn header with visual separator
        lines.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("")
        lines.append(f"### Turn {turn.turn_num}")
        lines.append("")

        # User
        user_text = _ensure_str(turn.user_input).strip()
        if user_text:
            lines.append("👤 **User**")
            lines.append("")
            lines.append(user_text)
            lines.append("")

        # Think block — clearly separated, quoted style
        think_text = _ensure_str(turn.think).strip()
        if think_text:
            lines.append("💭 **Think**")
            lines.append("")
            lines.append("```")
            lines.append(think_text)
            lines.append("```")
            lines.append("")

        # Assistant
        assistant_text = _ensure_str(turn.assistant_text).strip()
        if assistant_text:
            lines.append("🤖 **Assistant**")
            lines.append("")
            lines.append(assistant_text)
            lines.append("")

        # Actions (code snippets) — smart extraction, truncated if too long
        if turn.actions:
            for action in turn.actions:
                label, subtitle, body = _action_summary_human(action)
                header = label
                if subtitle:
                    header += f"  {subtitle}"
                lines.append(header)
                lines.append("")
                if body.strip():
                    lang = _detect_lang(action.tool, action.args)
                    lines.append(f"```{lang}")
                    lines.append(body.rstrip("\n"))
                    lines.append("```")
                else:
                    lines.append("*(no output)*")
                lines.append("")

    lines.append("=" * 60)
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_outputs(
    chat_path: Path,
    code_path: Path,
    think_path: Path,
    human_path: Path,
    turns: List[Turn],
) -> ValidationResult:
    """Validate that all four output files were generated correctly."""
    errors: List[str] = []

    chat_ok = chat_path.exists() and chat_path.stat().st_size > 0 and chat_path.read_text(encoding="utf-8").startswith("# ")
    code_ok = code_path.exists() and code_path.stat().st_size > 0 and code_path.read_text(encoding="utf-8").startswith("# ")
    think_ok = think_path.exists() and think_path.stat().st_size > 0 and think_path.read_text(encoding="utf-8").startswith("# ")
    human_ok = human_path.exists() and human_path.stat().st_size > 0 and human_path.read_text(encoding="utf-8").startswith("# ")

    if not chat_ok:
        errors.append(f"chat file missing or invalid: {chat_path}")
    if not code_ok:
        errors.append(f"code file missing or invalid: {code_path}")
    if not think_ok:
        errors.append(f"think file missing or invalid: {think_path}")
    if not human_ok:
        errors.append(f"human file missing or invalid: {human_path}")

    # Extra: ensure human.md contains all turns
    if human_ok:
        human_text = human_path.read_text(encoding="utf-8")
        for turn in turns:
            if f"### Turn {turn.turn_num}" not in human_text:
                errors.append(f"human.md missing Turn {turn.turn_num}")
                human_ok = False
                break

    ok = chat_ok and code_ok and think_ok and human_ok
    return ValidationResult(ok, chat_ok, code_ok, think_ok, human_ok, errors)


# ---------------------------------------------------------------------------
# Main processing
# ---------------------------------------------------------------------------

def process_session(
    session_dir: Path,
    output_dir: Path,
    *,
    quick: bool = False,
    silent: bool = False,
) -> Tuple[Tuple[Path, ...], str]:
    """Parse a session and write output files.

    Args:
        session_dir: Path to the Kimi session directory.
        output_dir: Directory to write markdown files into.
        quick: If True, only generate the human-readable file.
        silent: If True, suppress progress prints.

    Returns:
        Tuple of (generated file paths, one-line summary string).
    """
    state = load_state(session_dir)
    title = state.get("custom_title", "Untitled")
    session_id = session_dir.name
    slug = make_slug(title, session_id)
    date_str = _extract_best_date(session_dir, state)
    slug = _disambiguate_slug(output_dir, date_str, slug)

    wire_path = session_dir / "wire.jsonl"
    ctx_path = session_dir / "context.jsonl"

    if wire_path.exists():
        turns = parse_wire_jsonl(wire_path)
        source = "wire"
    elif ctx_path.exists():
        turns = parse_context_jsonl(ctx_path)
        source = "context"
    else:
        raise FileNotFoundError(
            f"No wire.jsonl or context.jsonl found in {session_dir}\n"
            f"  This directory does not appear to contain a valid Kimi session."
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    chat_path = output_dir / f"{date_str}_{slug}_chat.md"
    code_path = output_dir / f"{date_str}_{slug}_code.md"
    think_path = output_dir / f"{date_str}_{slug}_think.md"
    human_path = output_dir / f"{date_str}_{slug}_human.md"

    total_actions = sum(len(t.actions) for t in turns)

    if quick:
        human_path.write_text(generate_human_md(turns, title), encoding="utf-8")
        if not silent:
            print(f"  ✅ {human_path.name}  (quick mode — human only)")
        summary = f"✅ Chora complete: {len(turns)} turns, {total_actions} actions, 1 file → {output_dir}"
        return (human_path,), summary

    chat_path.write_text(generate_chat_md(turns, title), encoding="utf-8")
    code_path.write_text(generate_code_md(turns, title), encoding="utf-8")
    think_path.write_text(generate_think_md(turns, title), encoding="utf-8")
    human_path.write_text(generate_human_md(turns, title), encoding="utf-8")

    # Validate
    validation = validate_outputs(chat_path, code_path, think_path, human_path, turns)
    if not validation.ok:
        for err in validation.errors:
            print(f"  ⚠️  Validation error: {err}", file=sys.stderr)
        raise RuntimeError(f"Output validation failed for {session_dir.name}")

    if not silent:
        print(f"  ✅ {chat_path.name}  ({len(turns)} turns, source={source})")
        print(f"  ✅ {code_path.name}  ({total_actions} actions)")
        print(f"  ✅ {think_path.name}  ({sum(1 for t in turns if t.think)} think blocks)")
        print(f"  ✅ {human_path.name}  (human-readable)")

    summary = f"✅ Chora complete: {len(turns)} turns, {total_actions} actions, 4 files → {output_dir}"
    return (chat_path, code_path, think_path, human_path), summary


def process_aistudio_source(
    source_path: Path,
    output_dir: Path,
    *,
    quick: bool = False,
    silent: bool = False,
) -> Tuple[Tuple[Path, ...], str]:
    """Parse an AI Studio JSON source and write output files.

    Args:
        source_path: Path to an AI Studio chat-log file (extensionless JSON).
        output_dir: Directory to write markdown files into.
        quick: If True, only generate the human-readable file.
        silent: If True, suppress progress prints.

    Returns:
        Tuple of (generated file paths, one-line summary string).
    """
    turns = parse_aistudio_json(source_path)
    # Derive title from first conversation or filename
    title = source_path.stem or "Untitled"
    try:
        raw = json.loads(source_path.read_text(encoding="utf-8", errors="ignore"))
        if isinstance(raw, list) and raw and isinstance(raw[0], dict):
            title = raw[0].get("title", title)
        elif isinstance(raw, dict):
            title = raw.get("title", title)
    except Exception:
        pass

    slug = make_slug(title, source_path.stem)
    date_str = _extract_best_date(source_path, {})
    slug = _disambiguate_slug(output_dir, date_str, slug)
    output_dir.mkdir(parents=True, exist_ok=True)

    chat_path = output_dir / f"{date_str}_{slug}_chat.md"
    code_path = output_dir / f"{date_str}_{slug}_code.md"
    think_path = output_dir / f"{date_str}_{slug}_think.md"
    human_path = output_dir / f"{date_str}_{slug}_human.md"

    total_actions = sum(len(t.actions) for t in turns)

    if quick:
        human_path.write_text(generate_human_md(turns, title), encoding="utf-8")
        if not silent:
            print(f"  ✅ {human_path.name}  (quick mode — human only)")
        summary = f"✅ Chora complete: {len(turns)} turns, {total_actions} actions, 1 file → {output_dir}"
        return (human_path,), summary

    chat_path.write_text(generate_chat_md(turns, title), encoding="utf-8")
    code_path.write_text(generate_code_md(turns, title), encoding="utf-8")
    think_path.write_text(generate_think_md(turns, title), encoding="utf-8")
    human_path.write_text(generate_human_md(turns, title), encoding="utf-8")

    # Validate
    validation = validate_outputs(chat_path, code_path, think_path, human_path, turns)
    if not validation.ok:
        for err in validation.errors:
            print(f"  ⚠️  Validation error: {err}", file=sys.stderr)
        raise RuntimeError(f"Output validation failed for {source_path.name}")

    if not silent:
        print(f"  ✅ {chat_path.name}  ({len(turns)} turns, source=aistudio)")
        print(f"  ✅ {code_path.name}  ({total_actions} code blocks)")
        print(f"  ✅ {think_path.name}  ({sum(1 for t in turns if t.think)} think blocks)")
        print(f"  ✅ {human_path.name}  (human-readable)")

    summary = f"✅ Chora complete: {len(turns)} turns, {total_actions} actions, 4 files → {output_dir}"
    return (chat_path, code_path, think_path, human_path), summary


def process_kimicode_source(
    session_dir: Path,
    output_dir: Path,
    *,
    quick: bool = False,
    silent: bool = False,
) -> Tuple[Tuple[Path, ...], str]:
    """Parse a Kimi-Code session and write output files.

    Args:
        session_dir: Path to a Kimi-Code session directory (contains state.json + agents/main/wire.jsonl).
        output_dir: Directory to write markdown files into.
        quick: If True, only generate the human-readable file.
        silent: If True, suppress progress prints.

    Returns:
        Tuple of (generated file paths, one-line summary string).
    """
    state_path = session_dir / "state.json"
    state: dict = {}
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    # Title from state.json (Kimi-Code uses "title" and "isCustomTitle")
    title = state.get("title", "Untitled")
    session_id = session_dir.name
    slug = make_slug(title, session_id)
    date_str = _extract_best_date(session_dir, state)
    slug = _disambiguate_slug(output_dir, date_str, slug)

    wire_path = session_dir / "agents" / "main" / "wire.jsonl"
    if not wire_path.exists():
        raise FileNotFoundError(f"No Kimi-Code wire.jsonl found at {wire_path}")

    turns = parse_kimicode_wire_jsonl(wire_path)

    output_dir.mkdir(parents=True, exist_ok=True)

    chat_path = output_dir / f"{date_str}_{slug}_chat.md"
    code_path = output_dir / f"{date_str}_{slug}_code.md"
    think_path = output_dir / f"{date_str}_{slug}_think.md"
    human_path = output_dir / f"{date_str}_{slug}_human.md"

    total_actions = sum(len(t.actions) for t in turns)

    if quick:
        human_path.write_text(generate_human_md(turns, title), encoding="utf-8")
        if not silent:
            print(f"  ✅ {human_path.name}  (quick mode — human only)")
        summary = f"✅ Chora complete: {len(turns)} turns, {total_actions} actions, 1 file → {output_dir}"
        return (human_path,), summary

    chat_path.write_text(generate_chat_md(turns, title), encoding="utf-8")
    code_path.write_text(generate_code_md(turns, title), encoding="utf-8")
    think_path.write_text(generate_think_md(turns, title), encoding="utf-8")
    human_path.write_text(generate_human_md(turns, title), encoding="utf-8")

    validation = validate_outputs(chat_path, code_path, think_path, human_path, turns)
    if not validation.ok:
        for err in validation.errors:
            print(f"  ⚠️  Validation error: {err}", file=sys.stderr)
        raise RuntimeError(f"Output validation failed for {session_dir.name}")

    if not silent:
        print(f"  ✅ {chat_path.name}  ({len(turns)} turns, source=kimicode)")
        print(f"  ✅ {code_path.name}  ({total_actions} actions)")
        print(f"  ✅ {think_path.name}  ({sum(1 for t in turns if t.think)} think blocks)")
        print(f"  ✅ {human_path.name}  (human-readable)")

    summary = f"✅ Chora complete: {len(turns)} turns, {total_actions} actions, 4 files → {output_dir}"
    return (chat_path, code_path, think_path, human_path), summary


def process_gemini_source(
    source_path: Path,
    output_dir: Path,
    *,
    quick: bool = False,
    silent: bool = False,
) -> Tuple[Tuple[Path, ...], str]:
    """Parse a Gemini CLI source and write output files.

    Args:
        source_path: Path to a Gemini chat file (jsonl, json, or logs.json).
        output_dir: Directory to write markdown files into.
        quick: If True, only generate the human-readable file.
        silent: If True, suppress progress prints.

    Returns:
        Tuple of (generated file paths, one-line summary string).
    """
    if source_path.suffix == ".jsonl":
        turns = parse_gemini_jsonl(source_path)
        src_type = "jsonl"
    elif source_path.name == "logs.json":
        turns = parse_gemini_logs_json(source_path)
        src_type = "logs"
    else:
        turns = parse_gemini_json(source_path)
        src_type = "json"

    title = source_path.stem or "Untitled"
    slug = make_slug(title, source_path.stem)
    date_str = _extract_best_date(source_path, {})
    slug = _disambiguate_slug(output_dir, date_str, slug)
    output_dir.mkdir(parents=True, exist_ok=True)

    chat_path = output_dir / f"{date_str}_{slug}_chat.md"
    code_path = output_dir / f"{date_str}_{slug}_code.md"
    think_path = output_dir / f"{date_str}_{slug}_think.md"
    human_path = output_dir / f"{date_str}_{slug}_human.md"

    total_actions = sum(len(t.actions) for t in turns)

    if quick:
        human_path.write_text(generate_human_md(turns, title), encoding="utf-8")
        if not silent:
            print(f"  ✅ {human_path.name}  (quick mode — human only)")
        summary = f"✅ Chora complete: {len(turns)} turns, {total_actions} actions, 1 file → {output_dir}"
        return (human_path,), summary

    chat_path.write_text(generate_chat_md(turns, title), encoding="utf-8")
    code_path.write_text(generate_code_md(turns, title), encoding="utf-8")
    think_path.write_text(generate_think_md(turns, title), encoding="utf-8")
    human_path.write_text(generate_human_md(turns, title), encoding="utf-8")

    validation = validate_outputs(chat_path, code_path, think_path, human_path, turns)
    if not validation.ok:
        for err in validation.errors:
            print(f"  ⚠️  Validation error: {err}", file=sys.stderr)
        raise RuntimeError(f"Output validation failed for {source_path.name}")

    if not silent:
        print(f"  ✅ {chat_path.name}  ({len(turns)} turns, source=gemini/{src_type})")
        print(f"  ✅ {code_path.name}  ({total_actions} actions)")
        print(f"  ✅ {think_path.name}  ({sum(1 for t in turns if t.think)} think blocks)")
        print(f"  ✅ {human_path.name}  (human-readable)")

    summary = f"✅ Chora complete: {len(turns)} turns, {total_actions} actions, 4 files → {output_dir}"
    return (chat_path, code_path, think_path, human_path), summary


def process_chatgpt_claude_source(
    source_path: Path,
    output_dir: Path,
    *,
    source_label: str = "chatgpt",
    quick: bool = False,
    silent: bool = False,
) -> Tuple[Tuple[Path, ...], str]:
    """Parse a ChatGPT or Claude JSON source and write output files.

    Args:
        source_path: Path to a conversations.json or individual chat export.
        output_dir: Directory to write markdown files into.
        source_label: 'chatgpt' or 'claude' (used in progress messages).
        quick: If True, only generate the human-readable file.
        silent: If True, suppress progress prints.

    Returns:
        Tuple of (generated file paths, one-line summary string).
    """
    turns = parse_chatgpt_claude_json(source_path)

    # Derive title from first conversation or filename
    title = source_path.stem or "Untitled"
    try:
        raw = json.loads(source_path.read_text(encoding="utf-8", errors="ignore"))
        if isinstance(raw, list) and raw and isinstance(raw[0], dict):
            title = raw[0].get("title", raw[0].get("name", title))
        elif isinstance(raw, dict):
            title = raw.get("title", raw.get("name", title))
    except Exception:
        pass

    slug = make_slug(title, source_path.stem)
    date_str = _extract_best_date(source_path, {})
    slug = _disambiguate_slug(output_dir, date_str, slug)
    output_dir.mkdir(parents=True, exist_ok=True)

    chat_path = output_dir / f"{date_str}_{slug}_chat.md"
    code_path = output_dir / f"{date_str}_{slug}_code.md"
    think_path = output_dir / f"{date_str}_{slug}_think.md"
    human_path = output_dir / f"{date_str}_{slug}_human.md"

    total_actions = sum(len(t.actions) for t in turns)

    if quick:
        human_path.write_text(generate_human_md(turns, title), encoding="utf-8")
        if not silent:
            print(f"  ✅ {human_path.name}  (quick mode — human only)")
        summary = f"✅ Chora complete: {len(turns)} turns, {total_actions} actions, 1 file → {output_dir}"
        return (human_path,), summary

    chat_path.write_text(generate_chat_md(turns, title), encoding="utf-8")
    code_path.write_text(generate_code_md(turns, title), encoding="utf-8")
    think_path.write_text(generate_think_md(turns, title), encoding="utf-8")
    human_path.write_text(generate_human_md(turns, title), encoding="utf-8")

    validation = validate_outputs(chat_path, code_path, think_path, human_path, turns)
    if not validation.ok:
        for err in validation.errors:
            print(f"  ⚠️  Validation error: {err}", file=sys.stderr)
        raise RuntimeError(f"Output validation failed for {source_path.name}")

    if not silent:
        print(f"  ✅ {chat_path.name}  ({len(turns)} turns, source={source_label})")
        print(f"  ✅ {code_path.name}  ({total_actions} code blocks)")
        print(f"  ✅ {think_path.name}  ({sum(1 for t in turns if t.think)} think blocks)")
        print(f"  ✅ {human_path.name}  (human-readable)")

    summary = f"✅ Chora complete: {len(turns)} turns, {total_actions} actions, 4 files → {output_dir}"
    return (chat_path, code_path, think_path, human_path), summary


def batch_process(
    output_dir: Path,
    *,
    force: bool = False,
    quick: bool = False,
    silent: bool = False,
) -> str:
    """Process all discovered sessions with progress reporting and error resilience.

    Returns a one-line summary string.
    """
    sessions = discover_sessions()
    if not sessions:
        msg = "No sessions found."
        if not silent:
            print(msg, file=sys.stderr)
            print(f"  Searched: {SESSIONS_ROOT}", file=sys.stderr)
        return f"📊 Batch complete: 0 processed, 0 skipped, 0 failed of 0 total"

    processed = 0
    skipped = 0
    failed = 0
    errors: List[Tuple[str, str]] = []
    total = len(sessions)

    for idx, (session_dir, state) in enumerate(sessions, 1):
        title = state.get("custom_title", "Untitled") or "Untitled"
        slug = make_slug(title, session_dir.name)
        out = output_dir

        # Skip if already processed and not forced
        if not force:
            date_str = _extract_best_date(session_dir, state)
            slug = _disambiguate_slug(out, date_str, slug)
            marker = out / f"{date_str}_{slug}_chat.md"
            if quick:
                marker = out / f"{date_str}_{slug}_human.md"
            if marker.exists():
                session_mtime = session_dir.stat().st_mtime
                out_mtime = marker.stat().st_mtime
                if out_mtime >= session_mtime:
                    skipped += 1
                    continue

        if not silent:
            prefix = f"[{idx}/{total}]"
            print(f"\n{prefix} 📂 {title}")
        try:
            _, _ = process_session(session_dir, out, quick=quick, silent=silent)
            processed += 1
        except Exception as exc:
            failed += 1
            err_msg = str(exc)
            errors.append((title, err_msg))
            if not silent:
                print(f"  ❌ Failed: {err_msg}", file=sys.stderr)
            if os.environ.get("CHORA_DEBUG"):
                traceback.print_exc()

    summary = f"📊 Batch complete: {processed} processed, {skipped} skipped, {failed} failed of {total} total → {output_dir}"
    if not silent:
        print(f"\n{'=' * 50}")
        print(summary)
        if errors:
            print(f"\nFailures:")
            for title, err in errors:
                print(f"  • {title}: {err}")
        print("=" * 50)
    return summary


def batch_process_aistudio(
    output_dir: Path,
    aistudio_dir: Optional[Path] = None,
    *,
    force: bool = False,
    quick: bool = False,
    silent: bool = False,
) -> str:
    """Process all discovered AI Studio sources.

    Returns a one-line summary string.
    """
    sources = discover_aistudio_sources(aistudio_dir)
    if not sources:
        msg = "No AI Studio sources found."
        if not silent:
            print(msg, file=sys.stderr)
            print(f"  Searched: {aistudio_dir or AISTUDIO_ROOT}", file=sys.stderr)
        return f"📊 AI Studio batch complete: 0 processed, 0 skipped, 0 failed of 0 total"

    processed = 0
    skipped = 0
    failed = 0
    errors: List[Tuple[str, str]] = []
    total = len(sources)

    for idx, (source_path, meta) in enumerate(sources, 1):
        title = source_path.stem or "Untitled"
        slug = make_slug(title, source_path.stem)
        out = output_dir

        # Skip if already processed and not forced
        if not force:
            date_str = _extract_best_date(source_path, {})
            slug = _disambiguate_slug(out, date_str, slug)
            marker = out / f"{date_str}_{slug}_chat.md"
            if quick:
                marker = out / f"{date_str}_{slug}_human.md"
            if marker.exists():
                src_mtime = source_path.stat().st_mtime
                out_mtime = marker.stat().st_mtime
                if out_mtime >= src_mtime:
                    skipped += 1
                    continue

        if not silent:
            prefix = f"[{idx}/{total}]"
            print(f"\n{prefix} 📂 {title}  ({meta.get('type', 'unknown')})")
        try:
            _, _ = process_aistudio_source(source_path, out, quick=quick, silent=silent)
            processed += 1
        except Exception as exc:
            failed += 1
            err_msg = str(exc)
            errors.append((title, err_msg))
            if not silent:
                print(f"  ❌ Failed: {err_msg}", file=sys.stderr)
            if os.environ.get("CHORA_DEBUG"):
                traceback.print_exc()

    summary = f"📊 AI Studio batch complete: {processed} processed, {skipped} skipped, {failed} failed of {total} total → {output_dir}"
    if not silent:
        print(f"\n{'=' * 50}")
        print(summary)
        if errors:
            print(f"\nFailures:")
            for title, err in errors:
                print(f"  • {title}: {err}")
        print("=" * 50)
    return summary


def batch_process_kimicode(
    output_dir: Path,
    kimicode_dir: Optional[Path] = None,
    *,
    force: bool = False,
    quick: bool = False,
    silent: bool = False,
) -> str:
    """Process all discovered Kimi-Code sessions.

    Returns a one-line summary string.
    """
    sources = discover_kimicode_sources(kimicode_dir)
    if not sources:
        msg = "No Kimi-Code sources found."
        if not silent:
            print(msg, file=sys.stderr)
            print(f"  Searched: {kimicode_dir or KIMICODE_ROOT}", file=sys.stderr)
        return f"📊 Kimi-Code batch complete: 0 processed, 0 skipped, 0 failed of 0 total"

    processed = 0
    skipped = 0
    failed = 0
    errors: List[Tuple[str, str]] = []
    total = len(sources)

    for idx, (session_dir, state) in enumerate(sources, 1):
        title = state.get("title", "Untitled") or "Untitled"
        slug = make_slug(title, session_dir.name)
        out = output_dir

        if not force:
            date_str = _extract_best_date(session_dir, state)
            slug = _disambiguate_slug(out, date_str, slug)
            marker = out / f"{date_str}_{slug}_chat.md"
            if quick:
                marker = out / f"{date_str}_{slug}_human.md"
            if marker.exists():
                src_mtime = session_dir.stat().st_mtime
                out_mtime = marker.stat().st_mtime
                if out_mtime >= src_mtime:
                    skipped += 1
                    continue

        if not silent:
            prefix = f"[{idx}/{total}]"
            print(f"\n{prefix} 📂 {title}")
        try:
            _, _ = process_kimicode_source(session_dir, out, quick=quick, silent=silent)
            processed += 1
        except Exception as exc:
            failed += 1
            err_msg = str(exc)
            errors.append((title, err_msg))
            if not silent:
                print(f"  ❌ Failed: {err_msg}", file=sys.stderr)
            if os.environ.get("CHORA_DEBUG"):
                traceback.print_exc()

    summary = f"📊 Kimi-Code batch complete: {processed} processed, {skipped} skipped, {failed} failed of {total} total → {output_dir}"
    if not silent:
        print(f"\n{'=' * 50}")
        print(summary)
        if errors:
            print(f"\nFailures:")
            for title, err in errors:
                print(f"  • {title}: {err}")
        print("=" * 50)
    return summary


def batch_process_gemini(
    output_dir: Path,
    gemini_dir: Optional[Path] = None,
    *,
    force: bool = False,
    quick: bool = False,
    silent: bool = False,
) -> str:
    """Process all discovered Gemini CLI sources.

    Returns a one-line summary string.
    """
    sources = discover_gemini_sources(gemini_dir)
    if not sources:
        msg = "No Gemini sources found."
        if not silent:
            print(msg, file=sys.stderr)
            print(f"  Searched: {gemini_dir or GEMINI_ROOT}", file=sys.stderr)
        return f"📊 Gemini batch complete: 0 processed, 0 skipped, 0 failed of 0 total"

    processed = 0
    skipped = 0
    failed = 0
    errors: List[Tuple[str, str]] = []
    total = len(sources)

    for idx, (source_path, meta) in enumerate(sources, 1):
        title = source_path.stem or "Untitled"
        slug = make_slug(title, source_path.stem)
        out = output_dir

        if not force:
            date_str = _extract_best_date(source_path, {})
            slug = _disambiguate_slug(out, date_str, slug)
            marker = out / f"{date_str}_{slug}_chat.md"
            if quick:
                marker = out / f"{date_str}_{slug}_human.md"
            if marker.exists():
                src_mtime = source_path.stat().st_mtime
                out_mtime = marker.stat().st_mtime
                if out_mtime >= src_mtime:
                    skipped += 1
                    continue

        if not silent:
            prefix = f"[{idx}/{total}]"
            print(f"\n{prefix} 📂 {title}  ({meta.get('type', 'unknown')})")
        try:
            _, _ = process_gemini_source(source_path, out, quick=quick, silent=silent)
            processed += 1
        except Exception as exc:
            failed += 1
            err_msg = str(exc)
            errors.append((title, err_msg))
            if not silent:
                print(f"  ❌ Failed: {err_msg}", file=sys.stderr)
            if os.environ.get("CHORA_DEBUG"):
                traceback.print_exc()

    summary = f"📊 Gemini batch complete: {processed} processed, {skipped} skipped, {failed} failed of {total} total → {output_dir}"
    if not silent:
        print(f"\n{'=' * 50}")
        print(summary)
        if errors:
            print(f"\nFailures:")
            for title, err in errors:
                print(f"  • {title}: {err}")
        print("=" * 50)
    return summary


def batch_process_chatgpt(
    output_dir: Path,
    chatgpt_dir: Optional[Path] = None,
    *,
    force: bool = False,
    quick: bool = False,
    silent: bool = False,
) -> str:
    """Process all discovered ChatGPT JSON sources.

    Returns a one-line summary string.
    """
    sources = discover_chatgpt_claude_sources(chatgpt_dir)

    if not sources:
        msg = "No ChatGPT sources found."
        if not silent:
            print(msg, file=sys.stderr)
            print(f"  Searched: {chatgpt_dir or CHATGPT_ROOT}", file=sys.stderr)
        return f"📊 ChatGPT batch complete: 0 processed, 0 skipped, 0 failed of 0 total"

    processed = 0
    skipped = 0
    failed = 0
    errors: List[Tuple[str, str]] = []
    total = len(sources)

    for idx, (source_path, detected) in enumerate(sources, 1):
        title = source_path.stem or "Untitled"
        slug = make_slug(title, source_path.stem)
        out = output_dir

        if not force:
            date_str = _extract_best_date(source_path, {})
            slug = _disambiguate_slug(out, date_str, slug)
            marker = out / f"{date_str}_{slug}_chat.md"
            if quick:
                marker = out / f"{date_str}_{slug}_human.md"
            if marker.exists():
                src_mtime = source_path.stat().st_mtime
                out_mtime = marker.stat().st_mtime
                if out_mtime >= src_mtime:
                    skipped += 1
                    continue

        if not silent:
            prefix = f"[{idx}/{total}]"
            print(f"\n{prefix} 📂 {title}")
        try:
            _, _ = process_chatgpt_claude_source(
                source_path, out, source_label="chatgpt", quick=quick, silent=silent
            )
            processed += 1
        except Exception as exc:
            failed += 1
            err_msg = str(exc)
            errors.append((title, err_msg))
            if not silent:
                print(f"  ❌ Failed: {err_msg}", file=sys.stderr)
            if os.environ.get("CHORA_DEBUG"):
                traceback.print_exc()

    summary = f"📊 ChatGPT batch complete: {processed} processed, {skipped} skipped, {failed} failed of {total} total → {output_dir}"
    if not silent:
        print(f"\n{'=' * 50}")
        print(summary)
        if errors:
            print(f"\nFailures:")
            for title, err in errors:
                print(f"  • {title}: {err}")
        print("=" * 50)
    return summary


def batch_process_claude(
    output_dir: Path,
    claude_dir: Optional[Path] = None,
    *,
    force: bool = False,
    quick: bool = False,
    silent: bool = False,
) -> str:
    """Process all discovered Claude JSON sources.

    Returns a one-line summary string.
    """
    sources = discover_chatgpt_claude_sources(claude_dir)

    if not sources:
        msg = "No Claude sources found."
        if not silent:
            print(msg, file=sys.stderr)
            print(f"  Searched: {claude_dir or CLAUDE_ROOT}", file=sys.stderr)
        return f"📊 Claude batch complete: 0 processed, 0 skipped, 0 failed of 0 total"

    processed = 0
    skipped = 0
    failed = 0
    errors: List[Tuple[str, str]] = []
    total = len(sources)

    for idx, (source_path, detected) in enumerate(sources, 1):
        title = source_path.stem or "Untitled"
        slug = make_slug(title, source_path.stem)
        out = output_dir

        if not force:
            date_str = _extract_best_date(source_path, {})
            slug = _disambiguate_slug(out, date_str, slug)
            marker = out / f"{date_str}_{slug}_chat.md"
            if quick:
                marker = out / f"{date_str}_{slug}_human.md"
            if marker.exists():
                src_mtime = source_path.stat().st_mtime
                out_mtime = marker.stat().st_mtime
                if out_mtime >= src_mtime:
                    skipped += 1
                    continue

        if not silent:
            prefix = f"[{idx}/{total}]"
            print(f"\n{prefix} 📂 {title}")
        try:
            _, _ = process_chatgpt_claude_source(
                source_path, out, source_label="claude", quick=quick, silent=silent
            )
            processed += 1
        except Exception as exc:
            failed += 1
            err_msg = str(exc)
            errors.append((title, err_msg))
            if not silent:
                print(f"  ❌ Failed: {err_msg}", file=sys.stderr)
            if os.environ.get("CHORA_DEBUG"):
                traceback.print_exc()

    summary = f"📊 Claude batch complete: {processed} processed, {skipped} skipped, {failed} failed of {total} total → {output_dir}"
    if not silent:
        print(f"\n{'=' * 50}")
        print(summary)
        if errors:
            print(f"\nFailures:")
            for title, err in errors:
                print(f"  • {title}: {err}")
        print("=" * 50)
    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="chora",
        description=(
            "Chora — Wire-aware session transcript generator for Kimi CLI.\n"
            "Parses wire.jsonl (or falls back to context.jsonl) and produces "
            "four linked markdown files: chat, code, think, and human-readable.\n"
            "Also supports AI Studio, Kimi-Code, Gemini CLI, ChatGPT, and Claude exports."
        ),
        epilog=(
            "Examples:\n"
            "  chora                              # Interactive session picker\n"
            "  chora --list                       # List all sessions\n"
            "  chora --session-dir ~/.kimi/sessions/PROJECT/SESSION-ID\n"
            "  chora --batch --output-dir ~/archive/chora\n"
            "  chora --batch --force --output-dir ~/archive/chora\n"
            "  chora --quick --session-dir ~/.kimi/sessions/.../session-id\n"
            "  chora --hook                       # DevWater hook mode (silent, auto-detect session)\n"
            "  chora --hook --session-dir /path/to/session\n"
            "  chora --source aistudio            # Process AI Studio exports\n"
            "  chora --source aistudio --batch --output-dir ~/archive/aistudio\n"
            "  chora --source kimicode            # Process Kimi-Code sessions\n"
            "  chora --source kimicode --batch --output-dir ~/archive/kimicode\n"
            "  chora --source gemini              # Process Gemini CLI chats\n"
            "  chora --source gemini --batch --output-dir ~/archive/gemini\n"
            "  chora --source chatgpt             # Process ChatGPT exports\n"
            "  chora --source chatgpt --batch --output-dir ~/archive/chatgpt\n"
            "  chora --source claude              # Process Claude exports\n"
            "  chora --source claude --batch --output-dir ~/archive/claude"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--session-dir",
        type=Path,
        metavar="DIR",
        help="Path to a specific session directory or file (source-dependent)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help="Output directory for generated files (default: ~/peacock/aichats)",
    )
    parser.add_argument(
        "--source",
        type=str,
        choices=["kimi", "aistudio", "kimicode", "gemini", "chatgpt", "claude"],
        default=None,
        metavar="SOURCE",
        help="Input source type: 'kimi' (default), 'aistudio', 'kimicode', 'gemini', 'chatgpt', or 'claude'",
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Process all discovered sessions (skips up-to-date by default)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-process sessions even if output is already up-to-date",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_sessions",
        help="List all discovered sessions and exit without processing",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Fast human-only mode: generate only _human.md",
    )
    parser.add_argument(
        "--hook",
        action="store_true",
        help=(
            "DevWater hook mode: read session dir from CHORA_SESSION_DIR or "
            "DEVWATER_SESSION_DIR env vars (or --session-dir), run silently, "
            "and output to ~/peacock/aichats/{source}/. "
            "Always produces all four files."
        ),
    )
    return parser


def main():
    parser = _build_parser()
    args = parser.parse_args()

    if args.list_sessions:
        list_sessions()
        return

    # Auto-detect source from session-dir or CWD
    source = args.source
    if source is None:
        # 1. Check explicit session-dir for a JSON file
        if args.session_dir and args.session_dir.exists():
            if args.session_dir.is_file() and args.session_dir.suffix == ".json":
                detected = _detect_chatgpt_claude_json(args.session_dir)
                if detected:
                    source = detected
            elif args.session_dir.is_dir():
                conv_json = args.session_dir / "conversations.json"
                if conv_json.exists():
                    detected = _detect_chatgpt_claude_json(conv_json)
                    if detected:
                        source = detected
        # 2. Fall back to CWD detection
        if source is None:
            cwd = Path.cwd()
            conv_json = cwd / "conversations.json"
            if conv_json.exists():
                detected = _detect_chatgpt_claude_json(conv_json)
                if detected:
                    source = detected
            elif _is_aistudio_dir(cwd):
                source = "aistudio"
            elif _is_kimicode_dir(cwd):
                source = "kimicode"
            elif _is_gemini_dir(cwd):
                source = "gemini"
            else:
                source = "kimi"

    # Compute output directory with source subfolder
    base_output_dir = args.output_dir or DEFAULT_OUTPUT_ROOT
    output_dir = base_output_dir / SOURCE_FOLDERS[source]
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.hook:
        # Hook mode supports Kimi and Kimi-Code sessions only
        if source in ("aistudio", "gemini", "chatgpt", "claude"):
            print(f"Hook mode is not supported for {source} sources.", file=sys.stderr)
            sys.exit(1)

        # Determine session directory (precedence: arg → CHORA_SESSION_DIR → DEVWATER_SESSION_DIR → CWD)
        session_dir = args.session_dir
        if not session_dir:
            env_dir = os.environ.get("CHORA_SESSION_DIR") or os.environ.get("DEVWATER_SESSION_DIR")
            if env_dir:
                session_dir = Path(env_dir)
        if not session_dir:
            cwd = Path.cwd()
            if _has_session_data(cwd):
                session_dir = cwd
            elif _has_kimicode_data(cwd):
                session_dir = cwd

        if not session_dir:
            print("Hook mode: no session directory found.", file=sys.stderr)
            print("  Set CHORA_SESSION_DIR or DEVWATER_SESSION_DIR, or use --session-dir.", file=sys.stderr)
            sys.exit(1)

        if not session_dir.exists():
            print(f"Session directory not found: {session_dir}", file=sys.stderr)
            sys.exit(1)

        if not (_has_session_data(session_dir) or _has_kimicode_data(session_dir)):
            print(f"No session data found in {session_dir}", file=sys.stderr)
            sys.exit(1)

        try:
            if _has_kimicode_data(session_dir):
                _, summary = process_kimicode_source(session_dir, output_dir, quick=False, silent=True)
            else:
                _, summary = process_session(session_dir, output_dir, quick=False, silent=True)
        except Exception as exc:
            print(f"Hook mode error: {exc}", file=sys.stderr)
            if os.environ.get("CHORA_DEBUG"):
                traceback.print_exc()
            sys.exit(1)
        print(summary)
        return

    if args.batch:
        if source == "aistudio":
            batch_process_aistudio(output_dir, force=args.force, quick=args.quick)
        elif source == "kimicode":
            batch_process_kimicode(output_dir, force=args.force, quick=args.quick)
        elif source == "gemini":
            batch_process_gemini(output_dir, force=args.force, quick=args.quick)
        elif source == "chatgpt":
            batch_process_chatgpt(output_dir, chatgpt_dir=args.session_dir, force=args.force, quick=args.quick)
        elif source == "claude":
            batch_process_claude(output_dir, claude_dir=args.session_dir, force=args.force, quick=args.quick)
        else:
            batch_process(output_dir, force=args.force, quick=args.quick)
        return


    # Single-source mode
    if source == "kimicode":
        session_dir = args.session_dir
        if not session_dir:
            sources = discover_kimicode_sources()
            if not sources:
                print("No Kimi-Code sources found.", file=sys.stderr)
                print(f"  Searched: {KIMICODE_ROOT}", file=sys.stderr)
                sys.exit(1)
            print("\nAvailable Kimi-Code sessions:\n")
            for i, (sp, state) in enumerate(sources, 1):
                title = state.get("title", "Untitled")
                mtime = datetime.fromtimestamp(sp.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                print(f"  {i}. {title}  ({mtime})")
            print("\n  0. Cancel")
            try:
                choice = input("\nPick a session: ").strip()
                if not choice.isdigit():
                    print("Invalid selection — please enter a number.", file=sys.stderr)
                    sys.exit(1)
                choice_num = int(choice)
                if choice_num == 0:
                    sys.exit(0)
                if choice_num < 1 or choice_num > len(sources):
                    print(f"Invalid selection — choose 0–{len(sources)}.", file=sys.stderr)
                    sys.exit(1)
                session_dir = sources[choice_num - 1][0]
            except (EOFError, KeyboardInterrupt):
                print("\nCancelled.", file=sys.stderr)
                sys.exit(1)

        if not session_dir.exists():
            print(f"Session directory not found: {session_dir}", file=sys.stderr)
            sys.exit(1)

        if not _has_kimicode_data(session_dir):
            print(f"No Kimi-Code data found in {session_dir}", file=sys.stderr)
            print("  Expected agents/main/wire.jsonl alongside state.json.", file=sys.stderr)
            sys.exit(1)

        print(f"\n🔍 Processing Kimi-Code session: {session_dir.name}...")
        try:
            paths, summary = process_kimicode_source(session_dir, output_dir, quick=args.quick)
        except Exception as exc:
            print(f"\n❌ Error: {exc}", file=sys.stderr)
            if os.environ.get("CHORA_DEBUG"):
                traceback.print_exc()
            sys.exit(1)

        print(f"\n📁 Output: {output_dir}")
        if args.quick:
            print(f"   Human: {paths[0]}")
        else:
            print(f"   Chat : {paths[0]}")
            print(f"   Code : {paths[1]}")
            print(f"   Think: {paths[2]}")
            print(f"   Human: {paths[3]}")
        print(summary)
        return

    if source == "gemini":
        source_path = args.session_dir
        if not source_path:
            sources = discover_gemini_sources()
            if not sources:
                print("No Gemini sources found.", file=sys.stderr)
                print(f"  Searched: {GEMINI_ROOT}", file=sys.stderr)
                sys.exit(1)
            print("\nAvailable Gemini sources:\n")
            for i, (sp, meta) in enumerate(sources, 1):
                mtime = datetime.fromtimestamp(sp.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                stype = meta.get("type", "unknown")
                print(f"  {i}. {sp.name}  ({stype}, {mtime})")
            print("\n  0. Cancel")
            try:
                choice = input("\nPick a source: ").strip()
                if not choice.isdigit():
                    print("Invalid selection — please enter a number.", file=sys.stderr)
                    sys.exit(1)
                choice_num = int(choice)
                if choice_num == 0:
                    sys.exit(0)
                if choice_num < 1 or choice_num > len(sources):
                    print(f"Invalid selection — choose 0–{len(sources)}.", file=sys.stderr)
                    sys.exit(1)
                source_path = sources[choice_num - 1][0]
            except (EOFError, KeyboardInterrupt):
                print("\nCancelled.", file=sys.stderr)
                sys.exit(1)

        if not source_path.exists():
            print(f"Source not found: {source_path}", file=sys.stderr)
            sys.exit(1)

        print(f"\n🔍 Processing Gemini source: {source_path.name}...")
        try:
            paths, summary = process_gemini_source(source_path, output_dir, quick=args.quick)
        except Exception as exc:
            print(f"\n❌ Error: {exc}", file=sys.stderr)
            if os.environ.get("CHORA_DEBUG"):
                traceback.print_exc()
            sys.exit(1)

        print(f"\n📁 Output: {output_dir}")
        if args.quick:
            print(f"   Human: {paths[0]}")
        else:
            print(f"   Chat : {paths[0]}")
            print(f"   Code : {paths[1]}")
            print(f"   Think: {paths[2]}")
            print(f"   Human: {paths[3]}")
        print(summary)
        return

    # Single-source mode
    if source == "aistudio":
        # Single AI Studio source: pick interactively or use explicit path
        source_path = args.session_dir  # Re-use --session-dir as explicit source path
        if not source_path:
            sources = discover_aistudio_sources()
            if not sources:
                print("No AI Studio sources found.", file=sys.stderr)
                print(f"  Searched: {AISTUDIO_ROOT}", file=sys.stderr)
                print("  Expected accounts/<gmail>/chat-logs/*", file=sys.stderr)
                sys.exit(1)
            # Interactive pick
            print("\nAvailable AI Studio sources:\n")
            for i, (sp, meta) in enumerate(sources, 1):
                mtime = datetime.fromtimestamp(sp.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                stype = meta.get("type", "unknown")
                print(f"  {i}. {sp.name}  ({stype}, {mtime})")
            print("\n  0. Cancel")
            try:
                choice = input("\nPick a source: ").strip()
                if not choice.isdigit():
                    print("Invalid selection — please enter a number.", file=sys.stderr)
                    sys.exit(1)
                choice_num = int(choice)
                if choice_num == 0:
                    sys.exit(0)
                if choice_num < 1 or choice_num > len(sources):
                    print(f"Invalid selection — choose 0–{len(sources)}.", file=sys.stderr)
                    sys.exit(1)
                source_path = sources[choice_num - 1][0]
            except (EOFError, KeyboardInterrupt):
                print("\nCancelled.", file=sys.stderr)
                sys.exit(1)

        if not source_path.exists():
            print(f"Source not found: {source_path}", file=sys.stderr)
            sys.exit(1)

        print(f"\n🔍 Processing AI Studio source: {source_path.name}...")
        try:
            paths, summary = process_aistudio_source(source_path, output_dir, quick=args.quick)
        except Exception as exc:
            print(f"\n❌ Error: {exc}", file=sys.stderr)
            if os.environ.get("CHORA_DEBUG"):
                traceback.print_exc()
            sys.exit(1)

        print(f"\n📁 Output: {output_dir}")
        if args.quick:
            print(f"   Human: {paths[0]}")
        else:
            print(f"   Chat : {paths[0]}")
            print(f"   Code : {paths[1]}")
            print(f"   Think: {paths[2]}")
            print(f"   Human: {paths[3]}")
        print(summary)
        return

    # Single-source mode — ChatGPT
    if source == "chatgpt":
        source_path = args.session_dir
        if not source_path:
            root = CHATGPT_ROOT
            sources = discover_chatgpt_claude_sources(root)
            # Also check CWD
            cwd_sources = discover_chatgpt_claude_sources(Path.cwd())
            for s in cwd_sources:
                if s not in sources:
                    sources.append(s)
            sources = [(p, s) for p, s in sources if s == "chatgpt"]
            sources.sort(key=lambda item: item[0].stat().st_mtime, reverse=True)

            if not sources:
                print("No ChatGPT sources found.", file=sys.stderr)
                print(f"  Searched: {root}", file=sys.stderr)
                print("  Use --session-dir to specify a file or directory.", file=sys.stderr)
                sys.exit(1)
            print("\nAvailable ChatGPT sources:\n")
            for i, (sp, detected) in enumerate(sources, 1):
                mtime = datetime.fromtimestamp(sp.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                print(f"  {i}. {sp.name}  ({detected}, {mtime})")
            print("\n  0. Cancel")
            try:
                choice = input("\nPick a source: ").strip()
                if not choice.isdigit():
                    print("Invalid selection — please enter a number.", file=sys.stderr)
                    sys.exit(1)
                choice_num = int(choice)
                if choice_num == 0:
                    sys.exit(0)
                if choice_num < 1 or choice_num > len(sources):
                    print(f"Invalid selection — choose 0–{len(sources)}.", file=sys.stderr)
                    sys.exit(1)
                source_path = sources[choice_num - 1][0]
            except (EOFError, KeyboardInterrupt):
                print("\nCancelled.", file=sys.stderr)
                sys.exit(1)

        if not source_path.exists():
            print(f"Source not found: {source_path}", file=sys.stderr)
            sys.exit(1)

        print(f"\n🔍 Processing ChatGPT source: {source_path.name}...")
        try:
            paths, summary = process_chatgpt_claude_source(
                source_path, output_dir, source_label="chatgpt", quick=args.quick
            )
        except Exception as exc:
            print(f"\n❌ Error: {exc}", file=sys.stderr)
            if os.environ.get("CHORA_DEBUG"):
                traceback.print_exc()
            sys.exit(1)

        print(f"\n📁 Output: {output_dir}")
        if args.quick:
            print(f"   Human: {paths[0]}")
        else:
            print(f"   Chat : {paths[0]}")
            print(f"   Code : {paths[1]}")
            print(f"   Think: {paths[2]}")
            print(f"   Human: {paths[3]}")
        print(summary)
        return

    # Single-source mode — Claude
    if source == "claude":
        source_path = args.session_dir
        if not source_path:
            root = CLAUDE_ROOT
            sources = discover_chatgpt_claude_sources(root)
            # Also check CWD
            cwd_sources = discover_chatgpt_claude_sources(Path.cwd())
            for s in cwd_sources:
                if s not in sources:
                    sources.append(s)
            sources = [(p, s) for p, s in sources if s == "claude"]
            sources.sort(key=lambda item: item[0].stat().st_mtime, reverse=True)

            if not sources:
                print("No Claude sources found.", file=sys.stderr)
                print(f"  Searched: {root}", file=sys.stderr)
                print("  Use --session-dir to specify a file or directory.", file=sys.stderr)
                sys.exit(1)
            print("\nAvailable Claude sources:\n")
            for i, (sp, detected) in enumerate(sources, 1):
                mtime = datetime.fromtimestamp(sp.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                print(f"  {i}. {sp.name}  ({detected}, {mtime})")
            print("\n  0. Cancel")
            try:
                choice = input("\nPick a source: ").strip()
                if not choice.isdigit():
                    print("Invalid selection — please enter a number.", file=sys.stderr)
                    sys.exit(1)
                choice_num = int(choice)
                if choice_num == 0:
                    sys.exit(0)
                if choice_num < 1 or choice_num > len(sources):
                    print(f"Invalid selection — choose 0–{len(sources)}.", file=sys.stderr)
                    sys.exit(1)
                source_path = sources[choice_num - 1][0]
            except (EOFError, KeyboardInterrupt):
                print("\nCancelled.", file=sys.stderr)
                sys.exit(1)

        if not source_path.exists():
            print(f"Source not found: {source_path}", file=sys.stderr)
            sys.exit(1)

        print(f"\n🔍 Processing Claude source: {source_path.name}...")
        try:
            paths, summary = process_chatgpt_claude_source(
                source_path, output_dir, source_label="claude", quick=args.quick
            )
        except Exception as exc:
            print(f"\n❌ Error: {exc}", file=sys.stderr)
            if os.environ.get("CHORA_DEBUG"):
                traceback.print_exc()
            sys.exit(1)

        print(f"\n📁 Output: {output_dir}")
        if args.quick:
            print(f"   Human: {paths[0]}")
        else:
            print(f"   Chat : {paths[0]}")
            print(f"   Code : {paths[1]}")
            print(f"   Think: {paths[2]}")
            print(f"   Human: {paths[3]}")
        print(summary)
        return

    # Default Kimi single-session mode
    session_dir = args.session_dir
    if not session_dir:
        session_dir = pick_session(interactive=True)

    if not session_dir:
        print("No session selected.", file=sys.stderr)
        print("  Tip: use --list to see available sessions, or --session-dir to specify one.", file=sys.stderr)
        sys.exit(1)

    if not session_dir.exists():
        print(f"Session directory not found: {session_dir}", file=sys.stderr)
        sys.exit(1)

    if not _has_session_data(session_dir):
        print(
            f"No session data found in {session_dir}", file=sys.stderr
        )
        print(
            "  Expected wire.jsonl or context.jsonl alongside state.json.", file=sys.stderr
        )
        sys.exit(1)

    print(f"\n🔍 Processing {session_dir.name}...")
    try:
        paths, summary = process_session(session_dir, output_dir, quick=args.quick)
    except Exception as exc:
        print(f"\n❌ Error: {exc}", file=sys.stderr)
        if os.environ.get("CHORA_DEBUG"):
            traceback.print_exc()
        sys.exit(1)

    print(f"\n📁 Output: {output_dir}")
    if args.quick:
        print(f"   Human: {paths[0]}")
    else:
        print(f"   Chat : {paths[0]}")
        print(f"   Code : {paths[1]}")
        print(f"   Think: {paths[2]}")
        print(f"   Human: {paths[3]}")
    print(summary)


if __name__ == "__main__":
    main()
