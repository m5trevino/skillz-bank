#!/usr/bin/env python3
"""
Kimi-Code Parser — Dedicated parser for Kimi-Code CLI session transcripts.

Parses Kimi-Code wire.jsonl (at agents/main/wire.jsonl) and produces TWO
files inside a per-session directory:
  YYYY-MM-DD_slug/
    ├── YYYY-MM-DD_slug_chat.md   — clean conversation only
    └── YYYY-MM-DD_slug_think.md  — all thinking blocks only

Correlation: === Set N === in chat matches === Think Set N === in think.

Usage:
    from parsers.kimi_code_parser import parse_kimi_code
    chat_path, think_path = parse_kimi_code("/path/to/kimi-code-session/")
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

# ──────────────────────────────────────────────────────────────
# Output root
# ──────────────────────────────────────────────────────────────
DEFAULT_OUTPUT_ROOT = Path.home() / "peacock" / "aichats" / "kimi-code"


# ──────────────────────────────────────────────────────────────
# Session quality filter
# ──────────────────────────────────────────────────────────────

def is_meaningful_session(wire_jsonl_path: Path, min_lines: int = 6, require_tools: bool = False) -> bool:
    """
    Returns True if a wire.jsonl has enough substance to be worth parsing.

    Parameters
    ----------
    wire_jsonl_path : Path
        Path to agents/{id}/wire.jsonl
    min_lines : int
        Minimum number of JSONL events. Default 6 catches all the 2-5 line
        metadata-only sessions.
    require_tools : bool
        If True, requires at least one tool call or tool result message.
        This filters out pure chat sessions where the assistant only
        replied with text (e.g. "whats up" → "not much").
    """
    lines = 0
    has_tools = False

    with open(wire_jsonl_path, "r", encoding="utf-8") as f:
        for raw in f:
            lines += 1
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
                t = obj.get("type", "")

                # Newer protocol: tool calls appear as loop events
                if t == "context.append_loop_event":
                    event = obj.get("event", {})
                    if event.get("type") == "tool.call":
                        has_tools = True

                # Older protocol: tool results appear directly as messages
                elif t == "context.append_message":
                    if obj.get("message", {}).get("role") == "tool":
                        has_tools = True

            except json.JSONDecodeError:
                continue

    if lines < min_lines:
        return False
    if require_tools and not has_tools:
        return False
    return True


# ──────────────────────────────────────────────────────────────
# Data model
# ──────────────────────────────────────────────────────────────

@dataclass
class Set:
    """One conversation set = user prompt + assistant response + thoughts."""
    set_num: int
    user_text: str = ""
    assistant_text: str = ""
    think_text: str = ""


# ──────────────────────────────────────────────────────────────
# String helpers
# ──────────────────────────────────────────────────────────────

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
        if "text" in value:
            return _ensure_str(value["text"])
        if "think" in value:
            return _ensure_str(value["think"])
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _extract_text_parts(content) -> str:
    """Extract only 'text' type parts from a Kimi-Code content array."""
    parts = []
    if isinstance(content, list):
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                parts.append(part.get("text", ""))
    elif isinstance(content, str):
        parts.append(content)
    return "\n".join(parts)


def _extract_think_parts(content) -> str:
    """Extract only 'think' type parts from a Kimi-Code content array."""
    parts = []
    if isinstance(content, list):
        for part in content:
            if isinstance(part, dict) and part.get("type") == "think":
                parts.append(part.get("think", ""))
    return "\n\n".join(parts)


def _extract_turn_prompt_text(msg: dict) -> str:
    """Extract user text from a turn.prompt event."""
    inp = msg.get("input", [])
    parts = []
    if isinstance(inp, list):
        for part in inp:
            if isinstance(part, dict) and part.get("type") == "text":
                parts.append(part.get("text", ""))
    return "\n".join(parts)


# ──────────────────────────────────────────────────────────────
# State / metadata helpers
# ──────────────────────────────────────────────────────────────

def _load_state(session_dir: Path) -> dict:
    state_path = session_dir / "state.json"
    if state_path.exists():
        try:
            return json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _make_slug(title: Optional[str], session_id: str) -> str:
    title = title or ""
    slug = re.sub(r"[^\w\s-]", "", title).strip().lower()
    slug = re.sub(r"[-\s]+", "_", slug)
    if len(slug) > 60:
        slug = slug[:60].rstrip("_")
    if not slug:
        slug = session_id[:8]
    return slug


def _extract_date(state: dict) -> str:
    """Return date as YYYY-MM-DD from state.json createdAt (mandatory)."""
    val = state.get("createdAt")
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
    # Fallback to directory mtime if createdAt missing
    return datetime.now().strftime("%Y-%m-%d")


def _resolve_output_dir(output_dir: Path, date_str: str, slug: str) -> Path:
    """Return a unique output directory, appending _001, _002 if needed."""
    base = output_dir / f"{date_str}_{slug}"
    if not base.exists():
        return base

    counter = 1
    while True:
        candidate = output_dir / f"{date_str}_{slug}_{counter:03d}"
        if not candidate.exists():
            return candidate
        counter += 1


# ──────────────────────────────────────────────────────────────
# Wire.jsonl parser
# ──────────────────────────────────────────────────────────────

def parse_kimicode_wire_jsonl(wire_path: Path) -> List[Set]:
    """Parse a Kimi-Code wire.jsonl into Sets.

    Handles both wire formats:
      - Old: assistant messages in context.append_message with text/think parts
      - New: assistant content in context.append_loop_event content.part

    Ignored: metadata, config.update, tools.set_active_tools, usage.record,
             permission.record_approval_result, tool calls, tool results.
    """
    sets: List[Set] = []
    current_set: Optional[Set] = None

    # Track assistant content to avoid double-counting when it appears
    # in both context.append_message and context.append_loop_event.
    msg_level_text = ""   # text from context.append_message role=assistant
    msg_level_think = ""  # think from context.append_message role=assistant

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

            # ── User turn start ──
            if t == "turn.prompt":
                user_text = _extract_turn_prompt_text(msg)
                if current_set is not None:
                    # If we already have a set with no user text yet, populate it
                    if not current_set.user_text:
                        current_set.user_text = user_text
                    else:
                        # New turn
                        current_set = Set(
                            set_num=len(sets) + 1,
                            user_text=user_text,
                        )
                        sets.append(current_set)
                        msg_level_text = ""
                        msg_level_think = ""
                else:
                    current_set = Set(
                        set_num=len(sets) + 1,
                        user_text=user_text,
                    )
                    sets.append(current_set)
                    msg_level_text = ""
                    msg_level_think = ""

            elif t == "context.append_message":
                m = msg.get("message", {})
                role = m.get("role", "")
                content = m.get("content", [])

                if role == "user":
                    user_text = _extract_text_parts(content)
                    if current_set is not None and not current_set.user_text:
                        # Complement an earlier turn.prompt
                        current_set.user_text = user_text
                    elif current_set is not None and current_set.user_text == user_text:
                        # Duplicate of turn.prompt, ignore
                        pass
                    else:
                        current_set = Set(
                            set_num=len(sets) + 1,
                            user_text=user_text,
                        )
                        sets.append(current_set)
                        msg_level_text = ""
                        msg_level_think = ""

                elif role == "assistant" and current_set is not None:
                    text = _extract_text_parts(content)
                    think = _extract_think_parts(content)
                    if text:
                        msg_level_text += ("\n\n" if msg_level_text else "") + text
                        current_set.assistant_text += ("\n\n" if current_set.assistant_text else "") + text
                    if think:
                        msg_level_think += ("\n\n" if msg_level_think else "") + think
                        current_set.think_text += ("\n\n" if current_set.think_text else "") + think

                # role == "tool" is intentionally ignored for clean output

            # ── Loop events (new format) ──
            elif t == "context.append_loop_event":
                event = msg.get("event", {})
                event_type = event.get("type", "")

                if event_type == "content.part" and current_set is not None:
                    part = event.get("part", {})
                    pt = part.get("type", "")
                    if pt == "text":
                        text = part.get("text", "")
                        # Avoid duplicating text already captured from msg-level
                        if text and text not in msg_level_text and msg_level_text not in text:
                            current_set.assistant_text += ("\n\n" if current_set.assistant_text else "") + text
                        elif text and msg_level_text in text and not current_set.assistant_text:
                            # Loop event has the full text, msg-level was empty or partial
                            current_set.assistant_text = text
                    elif pt == "think":
                        think = part.get("think", "")
                        if think and think not in msg_level_think and msg_level_think not in think:
                            current_set.think_text += ("\n\n" if current_set.think_text else "") + think
                        elif think and msg_level_think in think and not current_set.think_text:
                            current_set.think_text = think

                # tool.call, tool.result, step.begin, step.end are ignored

            # All other types intentionally ignored

    # Final cleanup: strip leading/trailing whitespace
    for s in sets:
        s.user_text = s.user_text.strip()
        s.assistant_text = s.assistant_text.strip()
        s.think_text = s.think_text.strip()

    return sets


# ──────────────────────────────────────────────────────────────
# Markdown generators
# ──────────────────────────────────────────────────────────────

def generate_chat_md(sets: List[Set], title: str, date_str: str) -> str:
    """Generate clean _chat.md with === Set N === format."""
    lines = [
        f"# {title}",
        f"> {len(sets)} sets · {date_str}",
        "=" * 60,
        "",
    ]

    for i, s in enumerate(sets, 1):
        lines.append(f"=== Set {i} ===")
        lines.append("")
        lines.append(f"user: {s.user_text}")
        lines.append("")
        if s.assistant_text:
            lines.append(f"assistant: {s.assistant_text}")
        else:
            lines.append("assistant: ")
        lines.append("")
        if i < len(sets):
            lines.append("-=-=-==--=--=")
            lines.append("")

    return "\n".join(lines)


def generate_think_md(sets: List[Set]) -> str:
    """Generate _think.md with === Think Set N === format."""
    lines: List[str] = []

    for i, s in enumerate(sets, 1):
        lines.append(f"=== Think Set {i} ===")
        lines.append("")
        if s.think_text:
            lines.append(s.think_text)
        else:
            lines.append("(no thinking recorded)")
        lines.append("")

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────
# Main exported function
# ──────────────────────────────────────────────────────────────

def parse_kimi_code(
    source_path: Path,
    output_dir: Optional[Path] = None,
    min_assistant_chars: int = 0,
) -> Tuple[Path, Path]:
    """Parse a Kimi-Code session directory and write two markdown files.

    Args:
        source_path: Path to a Kimi-Code session directory containing
                     state.json and agents/main/wire.jsonl.
        output_dir:  Root directory for per-session folders.
                     Defaults to ~/peacock/aichats/kimi-code/
        min_assistant_chars: Minimum total assistant text characters required
                             to consider the session worth saving. 0 = no min.

    Returns:
        Tuple of (chat_path, think_path)

    Raises:
        FileNotFoundError: If no wire.jsonl found at agents/main/wire.jsonl.
    """
    session_dir = Path(source_path).expanduser().resolve()
    if not session_dir.is_dir():
        raise NotADirectoryError(f"Session directory not found: {session_dir}")

    # Load state
    state = _load_state(session_dir)

    # Title and date from state.json
    title = state.get("title", "Untitled") or "Untitled"
    session_id = session_dir.name
    slug = _make_slug(title, session_id)
    date_str = _extract_date(state)

    # Find wire.jsonl
    wire_path = session_dir / "agents" / "main" / "wire.jsonl"
    if not wire_path.exists():
        raise FileNotFoundError(
            f"No Kimi-Code wire.jsonl found at {wire_path}\n"
            f"  Expected agents/main/wire.jsonl alongside state.json."
        )

    # Skip empty/junk sessions silently
    if not is_meaningful_session(wire_path):
        raise RuntimeError("SESSION_EMPTY")

    # Parse
    sets = parse_kimicode_wire_jsonl(wire_path)

    # Filter out sessions with no real assistant responses
    total_assistant = sum(len(s.assistant_text) for s in sets)
    if total_assistant < min_assistant_chars:
        raise RuntimeError("SESSION_EMPTY")

    # Determine output directory
    root = (output_dir or DEFAULT_OUTPUT_ROOT).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    out = _resolve_output_dir(root, date_str, slug)
    out.mkdir(parents=True, exist_ok=True)

    # Build file paths
    chat_path = out / f"{date_str}_{slug}_chat.md"
    think_path = out / f"{date_str}_{slug}_think.md"

    # Generate and write
    chat_path.write_text(generate_chat_md(sets, title, date_str), encoding="utf-8")
    think_path.write_text(generate_think_md(sets), encoding="utf-8")

    return chat_path, think_path


# ──────────────────────────────────────────────────────────────
# CLI (optional, for direct testing)
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(f"Usage: python3 {sys.argv[0]} <session_dir> [output_dir]", file=sys.stderr)
        sys.exit(1)

    src = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    try:
        chat, think = parse_kimi_code(src, out)
        print(f"✅ Parsed {src.name}")
        print(f"   Chat : {chat}")
        print(f"   Think: {think}")
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
