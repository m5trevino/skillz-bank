#!/usr/bin/env python3
"""
ChatGPT parser — dedicated vertical slice for ChatGPT exports.

Parses ChatGPT `conversations.json` (array of conversations with `mapping` tree)
or individual `.json` chat exports, and writes one `_chat.md` file per
conversation in the strict Set format.

File naming : YYYY-MM-DD_slug_chat.md
Output dir  : ~/peacock/aichats/chatgpt/
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional, Tuple

DEFAULT_OUTPUT_DIR = Path.home() / "peacock" / "aichats" / "chatgpt"

# Separator placed after every set (including the final one)
SET_SEPARATOR = "-=-=-==--=--="


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slugify(title: str) -> str:
    """Convert a title to a clean lowercase underscore slug."""
    slug = re.sub(r"[^\w\s-]", "", title).strip().lower()
    slug = re.sub(r"[-\s]+", "_", slug)
    if not slug:
        slug = "untitled"
    return slug


def _extract_chat_date(conv: dict) -> str:
    """Return YYYY-MM-DD from the conversation creation timestamp."""
    for key in ("create_time", "update_time", "created_at", "updated_at"):
        val = conv.get(key)
        if val is not None:
            try:
                dt = datetime.fromtimestamp(float(val), tz=timezone.utc)
                return dt.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                continue
    return datetime.now().strftime("%Y-%m-%d")


def _extract_text(content: Any) -> str:
    """Extract plain text from ChatGPT message content."""
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
                    parts.append(_extract_text(part["content"]))
            else:
                parts.append(str(part))
        return "".join(parts)
    if isinstance(content, dict):
        if "parts" in content:
            return _extract_text(content["parts"])
        if "text" in content:
            return content["text"]
        return json.dumps(content, ensure_ascii=False)
    return str(content)


def _disambiguate_slug(output_dir: Path, date_str: str, slug: str) -> str:
    """Return a unique slug, appending _001, _002 etc. if the base filename collides."""
    base = f"{date_str}_{slug}"
    existing = list(output_dir.glob(f"{base}_*.md"))
    if not existing:
        return slug

    max_counter = 0
    for f in existing:
        m = re.search(rf"{re.escape(base)}_(\d+)_[a-z]+\.md$", f.name)
        if m:
            max_counter = max(max_counter, int(m.group(1)))

    return f"{slug}_{max_counter + 1:03d}"


# ---------------------------------------------------------------------------
# ChatGPT-specific traversal
# ---------------------------------------------------------------------------

def _traverse_mapping(conv: dict) -> List[Tuple[str, str]]:
    """Traverse a ChatGPT conversation mapping and return ordered (role, text) pairs.

    The mapping is a dict of node_id -> node where each node has:
      - parent: node_id or None
      - children: list of node_ids
      - message: {author: {role: ...}, content: {parts: [...]}}

    We follow the main thread by always taking children[-1].
    """
    mapping = conv.get("mapping", {})
    if not mapping:
        return []

    root_id = next(
        (node_id for node_id, node in mapping.items() if node.get("parent") is None),
        None,
    )

    messages: List[Tuple[str, str]] = []
    current_id = root_id

    while current_id:
        node = mapping.get(current_id)
        if not node:
            break

        msg_obj = node.get("message")
        if msg_obj:
            role = msg_obj.get("author", {}).get("role", "")
            text = _extract_text(msg_obj.get("content", {}))

            if role in ("user", "assistant") and text.strip():
                # Merge consecutive messages from the same role
                if messages and messages[-1][0] == role:
                    messages[-1] = (role, messages[-1][1] + "\n\n" + text.strip())
                else:
                    messages.append((role, text.strip()))

        children = node.get("children", [])
        current_id = children[-1] if children else None

    return messages


def _build_sets_md(title: str, date_str: str, messages: List[Tuple[str, str]]) -> str:
    """Build the strict Set-format _chat.md content.

    Format:
      # Chat Log — [clean chat title]
      > N sets · YYYY-MM-DD
      ============================================================
      === Set 1 ===
      user: exact raw user message here (can be multiple lines)

      assistant: exact final assistant message here (can be multiple lines)

      -=-=-==--=--=
      === Set 2 ===
      user: next user message

      assistant: next assistant message

      -=-=-==--=--=
    """
    lines: List[str] = [
        f"# Chat Log — {title}",
        f"> {len(messages) // 2} sets · {date_str}",
        "============================================================",
    ]

    set_num = 0
    i = 0
    while i < len(messages):
        role, text = messages[i]

        if role == "user":
            set_num += 1
            lines.append(f"=== Set {set_num} ===")
            lines.append(f"user: {text}")

            # Look for the matching assistant message
            if i + 1 < len(messages) and messages[i + 1][0] == "assistant":
                i += 1
                _, assistant_text = messages[i]
                lines.append("")
                lines.append(f"assistant: {assistant_text}")
        else:
            # Assistant without preceding user (can happen at start)
            set_num += 1
            lines.append(f"=== Set {set_num} ===")
            lines.append(f"assistant: {text}")

        lines.append("")
        lines.append(SET_SEPARATOR)
        i += 1

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_chatgpt(source_path: str, output_dir: Optional[str] = None) -> Path:
    """Parse a ChatGPT JSON export and write one `_chat.md` file per conversation.

    Args:
        source_path: Path to a ChatGPT `conversations.json` or individual `.json` export.
        output_dir: Override the default output directory. Defaults to ~/peacock/aichats/chatgpt.

    Returns:
        Path to the first written `_chat.md` file.
    """
    src = Path(source_path)
    if not src.exists():
        raise FileNotFoundError(f"Source not found: {source_path}")

    out = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    raw_text = src.read_text(encoding="utf-8", errors="ignore")
    if not raw_text.strip():
        raise ValueError(f"Source file is empty: {source_path}")

    data = json.loads(raw_text)

    conversations: List[dict] = []
    if isinstance(data, list):
        conversations = data
    elif isinstance(data, dict):
        conversations = [data]
    else:
        raise ValueError(f"Unexpected JSON type: {type(data).__name__}")

    results: List[Path] = []

    for conv in conversations:
        if not isinstance(conv, dict):
            continue

        title = conv.get("title") or conv.get("name") or "Untitled"
        slug = _slugify(title)
        date_str = _extract_chat_date(conv)
        slug = _disambiguate_slug(out, date_str, slug)

        messages = _traverse_mapping(conv)
        if not messages:
            continue

        chat_md = _build_sets_md(title, date_str, messages)
        filename = f"{date_str}_{slug}_chat.md"
        chat_path = out / filename
        chat_path.write_text(chat_md, encoding="utf-8")
        results.append(chat_path)

    if not results:
        raise ValueError(f"No parseable conversations found in {source_path}")

    return results[0]


# ---------------------------------------------------------------------------
# CLI / Test entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Parse ChatGPT exports to _chat.md")
    parser.add_argument("source", help="Path to conversations.json or a single .json export")
    parser.add_argument("--output-dir", "-o", default=None, help="Output directory override")
    args = parser.parse_args()

    written = parse_chatgpt(args.source, args.output_dir)
    print(f"✅ Written: {written}")
