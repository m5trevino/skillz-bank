#!/usr/bin/env python3
"""
Claude Parser — Vertical Slice C15

Parses Claude JSON exports (conversations.json or individual chat objects)
and produces a single rich _chat.md per conversation in standard numbered Set format.

Stripped from:
  - /home/flintx/save-aichats-personal-edition/backend/main.py
  - /home/flintx/.kimi/skills/chora/claude-logic-chatlog-path-info.txt

MANDATORY OUTPUT:
  - ~/peacock/aichats/claude/YYYY-MM-DD_real-chat-name_slug_chat.md
  - Standard numbered Set format with embedded code blocks
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# ──────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────

OUTPUT_ROOT = Path.home() / "peacock" / "aichats" / "claude"

SET_SEPARATOR = "-=-=-==--=--="


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

def _extract_text(content: Any) -> str:
    """Extract plain text from Claude message content.

    Handles:
      - plain string
      - list of content blocks (Claude native format)
      - dict with 'text' key
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                if block.get("type") == "text" and "text" in block:
                    parts.append(block["text"] or "")
                elif "text" in block:
                    parts.append(block["text"] or "")
        return "".join(parts)
    if isinstance(content, dict):
        return content.get("text", "")
    return str(content)


def _make_slug(name: str) -> str:
    """Sanitize a chat name into a filesystem-safe slug."""
    slug = re.sub(r"[^\w\s-]", "", name or "untitled").strip().lower()
    slug = re.sub(r"[-\s]+", "_", slug)
    if not slug:
        slug = "untitled"
    return slug


def _extract_date(chat: dict) -> str:
    """Return YYYY-MM-DD from the best available timestamp."""
    for key in ("created_at", "updated_at", "create_time", "timestamp"):
        val = chat.get(key)
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
    return datetime.now().strftime("%Y-%m-%d")


def _disambiguate_slug(output_dir: Path, date_str: str, slug: str) -> str:
    """Return a unique slug, appending _001, _002 etc. if the base filename collides."""
    base = f"{date_str}_{slug}"
    pattern = f"{base}_*.md"
    existing = list(output_dir.glob(pattern))
    if not existing:
        return slug

    max_counter = 0
    for f in existing:
        m = re.search(rf"{re.escape(base)}_(\d+)_[a-z]+\.md$", f.name)
        if m:
            max_counter = max(max_counter, int(m.group(1)))

    return f"{slug}_{max_counter + 1:03d}"


# ──────────────────────────────────────────────────────────────
# Core parser
# ──────────────────────────────────────────────────────────────

def _parse_conversation(chat: dict) -> List[dict]:
    """Parse a single Claude conversation dict into numbered sets."""
    sets: List[dict] = []
    current_user = ""

    messages = chat.get("chat_messages", chat.get("messages", []))
    for msg in messages:
        if not isinstance(msg, dict):
            continue

        role = msg.get("sender", msg.get("role", ""))
        text = _extract_text(msg.get("content", msg.get("text", "")))

        if role in ("human", "user"):
            current_user = text
        elif role in ("assistant", "bot"):
            sets.append({
                "set_num": len(sets) + 1,
                "user": current_user,
                "assistant": text,
            })
            current_user = ""

    return sets


def _generate_chat_md(chat_name: str, sets: List[dict], date_str: str) -> str:
    """Generate the rich _chat.md in standard numbered Set format.

    Code blocks stay embedded in assistant text (no extraction).
    Non-text content blocks (tool_use, tool_result, thinking, etc.) are skipped.
    """
    lines = [
        f"# Chat Log — {chat_name}",
        "",
        f"> {len(sets)} sets · {date_str}",
        "",
        "=" * 60,
        "",
    ]

    for s in sets:
        lines.append(f"=== Set {s['set_num']} ===")
        lines.append(f"user: {s['user']}")
        lines.append("")
        lines.append(f"assistant: {s['assistant']}")
        lines.append("")
        lines.append(SET_SEPARATOR)
        lines.append("")

    lines.append("=" * 60)
    lines.append("")
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────

def parse_claude(source_path: str) -> Dict[str, str]:
    """Parse a Claude JSON export and write _chat.md file(s).

    Args:
        source_path: Path to a Claude JSON file. Supports:
          - conversations.json (array of conversation objects)
          - Individual conversation export (single dict with chat_messages)

    Returns:
        Dict mapping generated filename -> markdown content string.
        Files are written to ~/peacock/aichats/claude/.
    """
    source_path = Path(source_path)
    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    raw_text = source_path.read_text(encoding="utf-8", errors="ignore")
    if not raw_text.strip():
        raise ValueError("Source file is empty")

    data = json.loads(raw_text)

    conversations = []
    if isinstance(data, list):
        conversations = data
    elif isinstance(data, dict):
        conversations = [data]
    else:
        raise ValueError("Unsupported JSON structure")

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    results: Dict[str, str] = {}

    for chat in conversations:
        if not isinstance(chat, dict):
            continue

        messages = chat.get("chat_messages", chat.get("messages", []))
        if not messages:
            continue

        chat_name = chat.get("name", chat.get("title", "Untitled")).strip()
        date_str = _extract_date(chat)
        slug = _make_slug(chat_name)
        slug = _disambiguate_slug(OUTPUT_ROOT, date_str, slug)

        sets = _parse_conversation(chat)
        if not sets:
            continue

        content = _generate_chat_md(chat_name or "Untitled", sets, date_str)
        filename = f"{date_str}_{slug}_chat.md"
        out_path = OUTPUT_ROOT / filename

        out_path.write_text(content, encoding="utf-8")
        results[filename] = content

    return results


# ──────────────────────────────────────────────────────────────
# CLI / Direct test
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    test_path = sys.argv[1] if len(sys.argv) > 1 else "/home/flintx/ai-chats/claude/conversations.json"
    print(f"Testing parse_claude({test_path!r})...")
    outputs = parse_claude(test_path)
    print(f"Generated {len(outputs)} file(s):")
    for fname, content in outputs.items():
        print(f"  → {OUTPUT_ROOT / fname}  ({len(content)} chars)")
        # Show first 20 lines as preview
        preview_lines = content.splitlines()[:20]
        for line in preview_lines:
            print(f"      {line}")
        print("      ...")
        print()
