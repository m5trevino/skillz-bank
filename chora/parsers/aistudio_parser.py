#!/usr/bin/env python3
"""
AI Studio parser for Chora.

Parses AI Studio JSON exports (extensionless files with chunkedPrompt format)
and generates a dedicated folder per chat containing:
  - YYYY-MM-DD_slug_chat.md  (raw conversation in strict Set format)
  - YYYY-MM-DD_slug_think.md (numbered thinking blocks)

Exported function:
    parse_aistudio(source_path) -> Path

Output:
    ~/peacock/aichats/aistudio/YYYY-MM-DD_slug/
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# ─────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────

OUTPUT_ROOT = Path.home() / "peacock" / "aichats" / "aistudio"

SET_SEPARATOR = "-=-=-==--=--="


# ─────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────

def _make_slug(name: str) -> str:
    """Sanitize a chat name into a filesystem-safe slug."""
    slug = re.sub(r"[^\w\s-]", "", name or "untitled").strip().lower()
    slug = re.sub(r"[-\s]+", "_", slug)
    if not slug:
        slug = "untitled"
    return slug


def _extract_date(source_path: Path) -> str:
    """Extract best date as YYYY-MM-DD from filename or mtime."""
    name = source_path.name

    # 1. AI Studio standard: MM.DD.YY at start of filename
    m = re.match(r"^(\d{2})\.(\d{2})\.(\d{2})", name)
    if m:
        mm, dd, yy = m.groups()
        try:
            year = 2000 + int(yy) if int(yy) < 70 else 1900 + int(yy)
            dt = datetime(year, int(mm), int(dd))
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    # 2. Generic patterns
    patterns = [
        r"(\d{4})-(\d{2})-(\d{2})",
        r"(\d{4})_(\d{2})_(\d{2})",
        r"(\d{4})(\d{2})(\d{2})",
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

    # 3. File mtime
    try:
        mtime = source_path.stat().st_mtime
        return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
    except (OSError, ValueError):
        pass

    # 4. Today (fallback, should rarely hit)
    return datetime.now().strftime("%Y-%m-%d")


def _extract_title(source_path: Path, raw_data: dict) -> str:
    """Extract title from JSON or filename."""
    title = raw_data.get("title", "")
    if title:
        return title

    # AI Studio filenames are extensionless; Path.suffix is unreliable.
    name = source_path.name
    # Strip leading MM.DD.YY-
    name = re.sub(r"^\d{2}\.\d{2}\.\d{2}-", "", name)
    # Strip trailing -MM.DD, -DD, or _N (and combos like -MM.DD_N)
    name = re.sub(r"(?:-\d{2}(?:\.\d{2})?)?(?:_\d+)?$", "", name)
    title = name.replace(".", " ").replace("_", " ").strip()
    if title:
        return title

    return "Untitled"


def _disambiguate_slug(output_dir: Path, date_str: str, slug: str) -> str:
    """Return a unique slug, appending _001, _002 etc. if folder collides."""
    base = f"{date_str}_{slug}"
    existing = list(output_dir.glob(f"{base}*"))
    if not existing:
        return slug

    max_counter = 0
    for f in existing:
        m = re.search(rf"{re.escape(base)}_(\d+)$", f.name)
        if m:
            max_counter = max(max_counter, int(m.group(1)))

    return f"{slug}_{max_counter + 1:03d}"


# ─────────────────────────────────────────────────────────────────────────
# Core parser
# ─────────────────────────────────────────────────────────────────────────

def _parse_messages_format(raw_data: list) -> List[dict]:
    """Parse AI Studio list-shaped JSON with messages array."""
    sets: List[dict] = []
    current_user = ""

    for conv in raw_data:
        if not isinstance(conv, dict):
            continue
        messages = conv.get("messages", [])
        for msg in messages:
            if not isinstance(msg, dict):
                continue
            role = msg.get("role", "")
            text = msg.get("content", "")
            if isinstance(text, list):
                text = "".join(p.get("text", "") for p in text if isinstance(p, dict))
            elif not isinstance(text, str):
                text = str(text)

            if role in ("user", "human"):
                current_user = text
            elif role in ("model", "assistant"):
                sets.append({
                    "set_num": len(sets) + 1,
                    "user": current_user,
                    "bot": text,
                    "thinking": "",
                    "images": [],
                })
                current_user = ""

    return sets


def _parse_chunks(raw_data: dict) -> List[dict]:
    """Parse AI Studio chunkedPrompt into numbered sets.

    AI Studio separates model reasoning into "thinking" chunks
    (isThought=True) and regular response chunks (isThought=None/False).
    Both belong to the same conversational turn and are merged into one set.
    """
    sets: List[dict] = []
    current_set: Dict[str, Any] | None = None
    set_idx = 1

    chunks = raw_data.get("chunkedPrompt", {}).get("chunks", [])

    for chunk in chunks:
        role = chunk.get("role")
        is_thought = chunk.get("isThought") is True

        # Extract text and images from parts.
        # chunk.text already contains the concatenation of all part texts,
        # so we use it directly. For thinking chunks, the text is reasoning.
        text = chunk.get("text", "")
        images: List[str] = []

        if "parts" in chunk:
            for part in chunk["parts"]:
                if not isinstance(part, dict):
                    continue
                if "fileData" in part:
                    fname = os.path.basename(
                        part["fileData"].get("fileUri", "unknown.png")
                    )
                    images.append(fname)

        if role == "user":
            # Close previous set if model already responded
            if current_set and (current_set.get("bot") or current_set.get("thinking")):
                sets.append(current_set)
                set_idx += 1
                current_set = None

            if not current_set:
                current_set = {
                    "set_num": set_idx,
                    "user": text,
                    "bot": "",
                    "thinking": "",
                    "images": images,
                }
            else:
                if text and text not in current_set["user"]:
                    if current_set["user"]:
                        current_set["user"] += "\n" + text
                    else:
                        current_set["user"] = text
                for img in images:
                    if img not in current_set["images"]:
                        current_set["images"].append(img)

        elif role == "model":
            if not current_set:
                current_set = {
                    "set_num": set_idx,
                    "user": "",
                    "bot": "",
                    "thinking": "",
                    "images": [],
                }

            if is_thought:
                # Thinking chunk: accumulate into thinking field
                if text and text not in current_set["thinking"]:
                    if current_set["thinking"]:
                        current_set["thinking"] += "\n\n" + text
                    else:
                        current_set["thinking"] = text
            else:
                # Regular response chunk: accumulate into bot field
                if text and text not in current_set["bot"]:
                    if current_set["bot"]:
                        current_set["bot"] += "\n" + text
                    else:
                        current_set["bot"] = text

            for img in images:
                if img not in current_set["images"]:
                    current_set["images"].append(img)

    if current_set and (current_set.get("bot") or current_set.get("thinking")):
        sets.append(current_set)

    return sets


def _generate_chat_md(slug: str, date_str: str, sets: List[dict]) -> str:
    """Generate the strict _chat.md in numbered Set format.

    Code blocks stay embedded in assistant text (no extraction).
    """
    lines = [
        f"# {slug}",
        "",
        f"*{len(sets)} sets · {date_str}*",
        "",
        "=" * 60,
        "",
    ]

    for s in sets:
        # Build user text (append image notes if any)
        user_text = s["user"].strip()
        if s["images"]:
            if user_text:
                user_text += "\n\n"
            user_text += "\n".join(f"[Image attached: {img}]" for img in s["images"])

        # Build assistant text
        assistant_text = s["bot"].strip()

        lines.append(f"=== Set {s['set_num']} ===")
        lines.append(f"user: {user_text}")
        lines.append(f"assistant: {assistant_text}")
        lines.append(SET_SEPARATOR)
        lines.append("")

    lines.append("=" * 60)
    lines.append("")
    return "\n".join(lines)


def _generate_think_md(sets: List[dict]) -> str:
    """Generate the _think.md with numbered thinking blocks."""
    lines: List[str] = []

    for s in sets:
        thinking = s["thinking"].strip()
        if not thinking:
            continue
        lines.append(f"=== Think Set {s['set_num']} ===")
        lines.append(thinking)
        lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────

def parse_aistudio(source_path: str) -> Path:
    """Parse an AI Studio JSON source and write chat + think files.

    Handles:
      - Standard chunkedPrompt format
      - List-shaped JSON with messages array
      - Multiple concatenated JSON objects (parses first only)
      - Non-JSON files raise ValueError for caller to skip

    Args:
        source_path: Path to the AI Studio chat-log file (extensionless JSON).

    Returns:
        Path to the generated folder (YYYY-MM-DD_slug/).
    """
    source_path = Path(source_path)

    # Read raw text, handling potential encoding issues
    try:
        raw_text = source_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raw_text = source_path.read_text(encoding="utf-8", errors="ignore")

    if not raw_text.strip():
        raise ValueError("Source file is empty")

    # Try to parse JSON, handling extra data after first object
    try:
        raw_data = json.loads(raw_text)
    except json.JSONDecodeError:
        # Try parsing only the first JSON object (extra data after)
        try:
            decoder = json.JSONDecoder()
            raw_data, _ = decoder.raw_decode(raw_text)
        except json.JSONDecodeError:
            raise ValueError("Source file is not valid JSON")

    # Metadata (needed before parsing for folder name)
    title = _extract_title(source_path, raw_data if isinstance(raw_data, dict) else {})
    date_str = _extract_date(source_path)
    slug = _make_slug(title)

    # Parse according to format BEFORE creating folder (avoids empty dirs on fail)
    if isinstance(raw_data, list):
        sets = _parse_messages_format(raw_data)
    elif isinstance(raw_data, dict):
        sets = _parse_chunks(raw_data)
    else:
        raise ValueError("Unsupported JSON structure")

    if not sets:
        raise ValueError("No conversation sets found in source file")

    # Disambiguate and create folder ONLY after successful parse
    output_dir = OUTPUT_ROOT
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = _disambiguate_slug(output_dir, date_str, slug)

    folder_path = output_dir / f"{date_str}_{slug}"
    folder_path.mkdir(parents=True, exist_ok=True)

    chat_content = _generate_chat_md(slug, date_str, sets)
    think_content = _generate_think_md(sets)

    chat_path = folder_path / f"{date_str}_{slug}_chat.md"
    think_path = folder_path / f"{date_str}_{slug}_think.md"

    chat_path.write_text(chat_content, encoding="utf-8")
    think_path.write_text(think_content, encoding="utf-8")

    return folder_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python aistudio_parser.py <source_path>", file=sys.stderr)
        sys.exit(1)

    out = parse_aistudio(sys.argv[1])
    print(f"✅ Generated folder: {out}")
