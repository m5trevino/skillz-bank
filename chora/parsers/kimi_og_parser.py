#!/usr/bin/env python3
"""
kimi_og_parser.py — Kimi OG (original Kimi CLI) session parser.

Reads a Kimi OG session directory:
    ~/.kimi/sessions/<session_hash>/<conversation_uuid>/

Key files:
    context.jsonl  → PRIMARY conversation log (user / assistant / tool messages)
    wire.jsonl     → protocol events (backup for think blocks + timestamps)
    state.json     → session metadata (title, timestamps)

Produces ONE directory with exactly TWO files:
    YYYY-MM-DD_slug/YYYY-MM-DD_slug_chat.md   ← clean conversation only
    YYYY-MM-DD_slug/YYYY-MM-DD_slug_think.md  ← all thinking blocks only

Output base: ~/peacock/aichats/kimi-og/
"""

import json
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple, Optional

# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────


def _load_jsonl(path: Path) -> List[Dict]:
    """Load a JSONL file, skipping malformed lines."""
    if not path.exists():
        return []
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries


def _extract_text_parts(content: Any) -> str:
    """Extract only 'text' type parts from an array content block."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                texts.append(part.get("text", ""))
            elif isinstance(part, str):
                texts.append(part)
        return "\n".join(texts)
    return ""


def _extract_think_parts(content: Any) -> str:
    """Extract only 'think' type parts from an array content block."""
    if isinstance(content, list):
        thoughts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "think":
                thoughts.append(part.get("think", ""))
        return "\n\n".join(thoughts)
    return ""


def _extract_user_content(content: Any) -> str:
    """Extract raw user message content, preserving text and noting attachments."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = []
        for part in content:
            if isinstance(part, dict):
                ptype = part.get("type", "")
                if ptype == "text":
                    texts.append(part.get("text", ""))
                elif ptype == "image_url":
                    url = part.get("image_url", {}).get("url", "")
                    if url.startswith("data:"):
                        texts.append("[Image: base64 data]")
                    else:
                        texts.append(f"[Image: {url}]")
            elif isinstance(part, str):
                texts.append(part)
        return "\n".join(texts)
    return str(content)


def _is_system_message(text: str) -> bool:
    return text.strip().startswith("<system>")


def _is_meta_role(role: str) -> bool:
    """Roles that are not part of the conversation."""
    return role in ("_system_prompt", "_checkpoint")


def is_worth_parsing(session_dir: Path) -> bool:
    """Return True only if session has real back-and-forth conversation."""
    ctx_path = session_dir / "context.jsonl"
    if not ctx_path.exists():
        ctx_path = session_dir / "context_1.jsonl"
    if not ctx_path.exists():
        return False

    assistant_count = 0
    user_count = 0

    try:
        with open(ctx_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                    role = obj.get("role")
                    if role == "assistant":
                        assistant_count += 1
                    elif role == "user":
                        user_count += 1

                    # Early exit if we already have what we need
                    if assistant_count >= 1 and user_count >= 1:
                        return True
                except json.JSONDecodeError:
                    continue
    except (OSError, IOError):
        return False

    return False  # No assistant response = junk session


def _slugify(text: str) -> str:
    """Sanitize title: lowercase, spaces → underscores, strip specials."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s_]", "", text)
    text = re.sub(r"[\s-]+", "_", text)
    text = re.sub(r"_+", "_", text)
    text = text.strip("_")
    return text[:80]


def _get_best_date(session_dir: Path, state: Dict) -> str:
    """Determine date from state.json, falling back to file mtimes."""
    # Priority 1: createdAt
    created_at = state.get("createdAt")
    if created_at:
        try:
            dt = datetime.fromtimestamp(float(created_at), tz=timezone.utc)
            return dt.strftime("%Y-%m-%d")
        except (ValueError, TypeError, OSError):
            pass

    # Priority 2: wire_mtime
    wire_mtime = state.get("wire_mtime")
    if wire_mtime:
        try:
            dt = datetime.fromtimestamp(float(wire_mtime), tz=timezone.utc)
            return dt.strftime("%Y-%m-%d")
        except (ValueError, TypeError, OSError):
            pass

    # Priority 3: archived_at
    archived_at = state.get("archived_at")
    if archived_at:
        try:
            dt = datetime.fromtimestamp(float(archived_at), tz=timezone.utc)
            return dt.strftime("%Y-%m-%d")
        except (ValueError, TypeError, OSError):
            pass

    # Priority 4: wire.jsonl mtime
    wire_path = session_dir / "wire.jsonl"
    if wire_path.exists():
        try:
            mtime = wire_path.stat().st_mtime
            dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
            return dt.strftime("%Y-%m-%d")
        except (OSError, ValueError):
            pass

    # Priority 5: context.jsonl mtime
    ctx_path = session_dir / "context.jsonl"
    if not ctx_path.exists():
        ctx_path = session_dir / "context_1.jsonl"
    if ctx_path.exists():
        try:
            mtime = ctx_path.stat().st_mtime
            dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
            return dt.strftime("%Y-%m-%d")
        except (OSError, ValueError):
            pass

    # Fallback: today
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")


def _get_chat_name(state: Dict, session_dir: Path) -> str:
    """Best available title from state.json or directory name."""
    custom_title = state.get("custom_title")
    if custom_title and str(custom_title).strip():
        return str(custom_title).strip()
    title = state.get("title")
    if title and str(title).strip():
        return str(title).strip()
    return session_dir.name


# ──────────────────────────────────────────────────────────────
# Core Parsing
# ──────────────────────────────────────────────────────────────


def _parse_context_jsonl(entries: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    Parse context.jsonl into conversation sets and think sets.

    Returns:
        (chat_sets, think_sets) where both are lists of dicts with 'set_num' and content.
    """
    chat_sets = []
    think_sets = []
    current_chat = None
    current_think = None

    for entry in entries:
        role = entry.get("role", "")

        # Skip meta roles entirely
        if _is_meta_role(role):
            continue

        if role == "user":
            content = entry.get("content", "")
            text = _extract_user_content(content)

            # Skip system-tagged user messages
            if isinstance(text, str) and _is_system_message(text):
                continue

            # Finalize previous set
            if current_chat is not None:
                chat_sets.append(current_chat)
                think_sets.append(current_think if current_think else {"set_num": current_chat["set_num"], "thinking": ""})

            set_num = len(chat_sets) + 1
            current_chat = {
                "set_num": set_num,
                "user": text,
                "assistant": "",
            }
            current_think = {
                "set_num": set_num,
                "thinking": "",
            }
            continue

        if role == "assistant" and current_chat is not None:
            content = entry.get("content", [])
            text = _extract_text_parts(content)
            thinking = _extract_think_parts(content)

            if text:
                if current_chat["assistant"]:
                    current_chat["assistant"] += "\n\n" + text
                else:
                    current_chat["assistant"] = text

            if thinking:
                if current_think["thinking"]:
                    current_think["thinking"] += "\n\n" + thinking
                else:
                    current_think["thinking"] = thinking

            continue

        # Tool results: skip entirely for chat, do not create new sets
        if role == "tool" and current_chat is not None:
            continue

    # Finalize last set
    if current_chat is not None:
        chat_sets.append(current_chat)
        think_sets.append(current_think if current_think else {"set_num": current_chat["set_num"], "thinking": ""})

    return chat_sets, think_sets


def _parse_wire_thinking(entries: List[Dict]) -> Dict[int, str]:
    """
    Parse wire.jsonl to extract thinking blocks indexed by turn number.
    Used as backup when context.jsonl has no think content.
    """
    turns = []
    current_turn_thinking = []
    in_turn = False

    for entry in entries:
        msg = entry.get("message", {})
        msg_type = msg.get("type", "")
        payload = msg.get("payload", {})

        if msg_type == "TurnBegin":
            if in_turn:
                turns.append("\n\n".join(current_turn_thinking))
            current_turn_thinking = []
            in_turn = True

        elif msg_type == "ContentPart":
            if payload.get("type") == "think":
                current_turn_thinking.append(payload.get("think", ""))

        elif msg_type == "TurnEnd":
            if in_turn:
                turns.append("\n\n".join(current_turn_thinking))
            in_turn = False

    wire_think = {}
    for idx, thinking in enumerate(turns):
        if thinking.strip():
            wire_think[idx] = thinking
    return wire_think


# ──────────────────────────────────────────────────────────────
# Output Writers
# ──────────────────────────────────────────────────────────────


def _write_chat_md(chat_sets: List[Dict], path: Path, chat_name: str, date_str: str):
    """Write _chat.md — strict clean format, user + assistant only."""
    with open(path, "w", encoding="utf-8") as f:
        # Header
        f.write(f"# {chat_name}\n\n")
        f.write(f"> {len(chat_sets)} sets · {date_str}\n")
        f.write("=" * 60 + "\n\n")

        for s in chat_sets:
            f.write(f"=== Set {s['set_num']} ===\n")
            f.write(f"user: {s['user']}\n\n")
            f.write(f"assistant: {s['assistant']}\n\n")
            f.write("-=-=-==--=--=\n\n")


def _write_think_md(think_sets: List[Dict], path: Path):
    """Write _think.md — numbered think sets correlating with chat sets."""
    with open(path, "w", encoding="utf-8") as f:
        for s in think_sets:
            thinking = s.get("thinking", "").strip()
            if thinking:
                f.write(f"=== Think Set {s['set_num']} ===\n")
                f.write(f"{thinking}\n\n")
            else:
                f.write(f"=== Think Set {s['set_num']} ===\n")
                f.write("[no thinking recorded]\n\n")


# ──────────────────────────────────────────────────────────────
# Main Entry Point
# ──────────────────────────────────────────────────────────────


def parse_kimi_og(source_path: str) -> Dict[str, Path]:
    """
    Parse a Kimi OG session directory and write 2 markdown files.

    Args:
        source_path: Path to the Kimi OG session directory.

    Returns:
        Dict with keys: 'dir', 'chat', 'think' → Path objects.
    """
    session_dir = Path(source_path).expanduser().resolve()
    if not session_dir.is_dir():
        raise ValueError(f"Not a directory: {session_dir}")

    # ── Skip junk sessions ──
    if not is_worth_parsing(session_dir):
        raise ValueError(f"Junk session (no assistant response): {session_dir}")

    # ── Locate input files ──
    state_path = session_dir / "state.json"
    wire_path = session_dir / "wire.jsonl"
    context_path = session_dir / "context.jsonl"
    if not context_path.exists():
        context_path = session_dir / "context_1.jsonl"

    if not context_path.exists():
        raise FileNotFoundError(f"No context.jsonl or context_1.jsonl found in {session_dir}")

    # ── Load state.json ──
    state = {}
    if state_path.exists():
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                state = json.load(f)
        except (json.JSONDecodeError, OSError):
            state = {}

    # ── Determine output directory ──
    chat_name = _get_chat_name(state, session_dir)
    date_str = _get_best_date(session_dir, state)
    slug = _slugify(chat_name)
    base_name = f"{date_str}_{slug}"

    outdir = Path.home() / "peacock" / "aichats" / "kimi-og" / base_name
    outdir.mkdir(parents=True, exist_ok=True)

    # ── Load & parse data ──
    context_entries = _load_jsonl(context_path)
    wire_entries = _load_jsonl(wire_path)

    chat_sets, think_sets = _parse_context_jsonl(context_entries)

    # Merge wire thinking as backup when context has no think content
    if wire_entries:
        wire_think = _parse_wire_thinking(wire_entries)
        for idx, think_set in enumerate(think_sets):
            if not think_set["thinking"].strip() and idx in wire_think:
                think_set["thinking"] = wire_think[idx]

    # ── Write outputs ──
    chat_path = outdir / f"{base_name}_chat.md"
    _write_chat_md(chat_sets, chat_path, chat_name, date_str)

    think_path = outdir / f"{base_name}_think.md"
    _write_think_md(think_sets, think_path)

    return {
        "dir": outdir,
        "chat": chat_path,
        "think": think_path,
    }


# ── CLI convenience ──
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 kimi_og_parser.py <session_dir>")
        sys.exit(1)

    result = parse_kimi_og(sys.argv[1])
    print("✅ Kimi-OG locked.")
    print(f"   Dir:  {result['dir']}")
    print(f"   Chat: {result['chat']}")
    print(f"   Think: {result['think']}")
