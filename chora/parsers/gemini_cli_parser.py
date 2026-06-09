#!/usr/bin/env python3
"""
Gemini CLI Parser — strict 2-file Set format.

Parses Gemini CLI session exports (legacy JSON/logs + new JSONL) and produces
exactly two files inside a per-session directory:

  YYYY-MM-DD_slug/
    YYYY-MM-DD_slug_chat.md   ← clean conversation only
    YYYY-MM-DD_slug_think.md  ← all thinking blocks only

Set numbers in _chat.md correlate 1:1 with Think Set numbers in _think.md.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, NamedTuple, Optional, Tuple

# ---------------------------------------------------------------------------
# Output configuration
# ---------------------------------------------------------------------------
DEFAULT_OUTPUT_ROOT = Path.home() / "peacock" / "aichats" / "gemini-cli"

# ---------------------------------------------------------------------------
# Empty / junk session filter thresholds
# ---------------------------------------------------------------------------
MIN_USER_MSGS = 1
MIN_GEMINI_MSGS = 1
MIN_TOTAL_MSGS = 3
MIN_CONTENT_CHARS = 50


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Set:
    set_num: int
    user_text: str
    assistant_text: str
    think_text: str  # may be empty


class FileSet(NamedTuple):
    chat: Path
    think: Path


# ---------------------------------------------------------------------------
# Date / slug helpers
# ---------------------------------------------------------------------------

def _extract_date_from_jsonl_first_line(source_path: Path) -> Optional[str]:
    """Peek at first line of JSONL for startTime / timestamp."""
    try:
        with open(source_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(entry, dict):
                    for key in ("startTime", "timestamp", "createdAt", "date"):
                        val = entry.get(key)
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
                break  # only first non-empty line
    except Exception:
        pass
    return None


def _extract_date_from_json(source_path: Path) -> Optional[str]:
    """Peek at JSON file for top-level timestamp or first-entry timestamp."""
    try:
        raw = source_path.read_text(encoding="utf-8", errors="ignore")
        if not raw.strip():
            return None
        data = json.loads(raw)
        if isinstance(data, dict):
            for key in ("startTime", "timestamp", "createdAt", "date"):
                val = data.get(key)
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
        if isinstance(data, list) and data and isinstance(data[0], dict):
            for key in ("startTime", "timestamp", "createdAt", "date"):
                val = data[0].get(key)
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
    except Exception:
        pass
    return None


def _extract_best_date(source_path: Path) -> str:
    """Return YYYY-MM-DD from metadata, filename, or file mtime."""
    # 1. Format-specific metadata peek
    if source_path.suffix == ".jsonl":
        date = _extract_date_from_jsonl_first_line(source_path)
        if date:
            return date
    else:
        date = _extract_date_from_json(source_path)
        if date:
            return date

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

    # 3. File mtime
    try:
        mtime = source_path.stat().st_mtime
        return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
    except (OSError, ValueError):
        pass

    # 4. Today (should not reach here often)
    return datetime.now().strftime("%Y-%m-%d")


def _make_slug(name: str) -> str:
    """Create a filesystem-safe slug from a file stem or title."""
    slug = re.sub(r"[^\w\s-]", "", name).strip().lower()
    slug = re.sub(r"[-\s]+", "_", slug)
    if not slug:
        slug = "untitled"
    return slug


def _disambiguate_dir(output_dir: Path, date_str: str, slug: str) -> str:
    """Append _001, _002 etc. if directory already exists."""
    base = f"{date_str}_{slug}"
    candidate = output_dir / base
    if not candidate.exists():
        return base

    counter = 1
    while True:
        candidate = output_dir / f"{base}_{counter:03d}"
        if not candidate.exists():
            return f"{base}_{counter:03d}"
        counter += 1


# ---------------------------------------------------------------------------
# Text extraction helpers
# ---------------------------------------------------------------------------

def _extract_text(content) -> str:
    """Coerce any Gemini content shape to plain string."""
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
        return "\n".join(parts)
    return str(content)


def _extract_think(entry: dict) -> str:
    """Extract think text from a gemini entry."""
    thoughts = entry.get("thoughts", [])
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


# ---------------------------------------------------------------------------
# Legacy parsers (logs.json + old session-*.json)
# ---------------------------------------------------------------------------

def _parse_legacy_logs_json(source_path: Path) -> List[Set]:
    """Parse logs.json — flat array of {type, message} entries."""
    raw = source_path.read_text(encoding="utf-8", errors="ignore")
    if not raw.strip():
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []

    if not isinstance(data, list):
        return []

    sets: List[Set] = []
    pending_user = ""

    for entry in data:
        if not isinstance(entry, dict):
            continue
        t = entry.get("type", "")
        if t == "user":
            pending_user = _extract_text(entry.get("message", entry.get("content", "")))
        elif t == "gemini":
            sets.append(Set(
                set_num=len(sets) + 1,
                user_text=pending_user,
                assistant_text=_extract_text(entry.get("message", entry.get("content", ""))),
                think_text="",
            ))
            pending_user = ""

    return sets


def _parse_legacy_session_json(source_path: Path) -> List[Set]:
    """Parse old session-*.json — single object with 'messages' array."""
    raw = source_path.read_text(encoding="utf-8", errors="ignore")
    if not raw.strip():
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []

    if not isinstance(data, dict):
        return []

    messages = data.get("messages", [])
    if not isinstance(messages, list):
        return []

    sets: List[Set] = []
    pending_user = ""

    for msg in messages:
        if not isinstance(msg, dict):
            continue
        t = msg.get("type", "")
        if t == "user":
            pending_user = _extract_text(msg.get("content", ""))
        elif t == "gemini":
            sets.append(Set(
                set_num=len(sets) + 1,
                user_text=pending_user,
                assistant_text=_extract_text(msg.get("content", "")),
                think_text=_extract_think(msg),
            ))
            pending_user = ""

    return sets


# ---------------------------------------------------------------------------
# New JSONL parser (session-*.jsonl)
# ---------------------------------------------------------------------------

def _parse_jsonl(source_path: Path) -> List[Set]:
    """Parse new line-by-line JSONL format."""
    sets: List[Set] = []
    pending_user = ""

    with open(source_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            if not isinstance(entry, dict):
                continue

            t = entry.get("type", "")

            # Skip noise entirely
            if t in ("$set", "info", "") or "sessionId" in entry:
                continue

            if t == "user":
                pending_user = _extract_text(entry.get("content", ""))
            elif t == "gemini":
                sets.append(Set(
                    set_num=len(sets) + 1,
                    user_text=pending_user,
                    assistant_text=_extract_text(entry.get("content", "")),
                    think_text=_extract_think(entry),
                ))
                pending_user = ""

    return sets


# ---------------------------------------------------------------------------
# Auto-dispatch
# ---------------------------------------------------------------------------

def _parse_source(source_path: Path) -> List[Set]:
    """Auto-detect format and parse."""
    name = source_path.name

    if source_path.suffix == ".jsonl":
        return _parse_jsonl(source_path)

    if source_path.suffix == ".json":
        # Peek to distinguish flat array (logs.json style) from dict with messages
        try:
            raw = source_path.read_text(encoding="utf-8", errors="ignore")
            if raw.strip():
                data = json.loads(raw)
                if isinstance(data, list):
                    return _parse_legacy_logs_json(source_path)
                if isinstance(data, dict) and "messages" in data:
                    return _parse_legacy_session_json(source_path)
        except Exception:
            pass
        # Fallback by name
        if name == "logs.json":
            return _parse_legacy_logs_json(source_path)
        return _parse_legacy_session_json(source_path)

    # Unknown extension — try JSONL first, then fallback
    try:
        return _parse_jsonl(source_path)
    except Exception:
        pass
    try:
        return _parse_legacy_session_json(source_path)
    except Exception:
        pass
    return _parse_legacy_logs_json(source_path)


# ---------------------------------------------------------------------------
# Markdown generators
# ---------------------------------------------------------------------------

def _generate_chat_md(sets: List[Set], title: str, date_str: str) -> str:
    lines = [
        f"# {title}",
        f"> {len(sets)} sets · {date_str}",
        "=" * 60,
        "",
    ]

    for s in sets:
        lines.append(f"=== Set {s.set_num} ===")
        lines.append("")
        lines.append(f"user: {s.user_text}")
        lines.append("")
        lines.append(f"assistant: {s.assistant_text}")
        lines.append("")
        lines.append("-=-=-==--=--=")
        lines.append("")

    return "\n".join(lines)


def _generate_think_md(sets: List[Set]) -> str:
    lines = []
    for s in sets:
        if not s.think_text:
            continue
        lines.append(f"=== Think Set {s.set_num} ===")
        lines.append("")
        lines.append(s.think_text)
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Empty / junk session filter
# ---------------------------------------------------------------------------

def _should_keep_session(sets: List[Set]) -> bool:
    """Return True if the session passes all quality filters.

    Filters:
      - At least 1 real user message
      - At least 1 real Gemini/assistant response
      - At least 3 total messages
      - At least 50 characters of real text content
    """
    if not sets:
        return False

    user_count = sum(1 for s in sets if s.user_text.strip())
    gemini_count = sum(1 for s in sets if s.assistant_text.strip())
    total_msgs = len(sets)
    content_chars = sum(
        len(s.user_text.strip()) + len(s.assistant_text.strip())
        for s in sets
    )

    if user_count < MIN_USER_MSGS:
        return False
    if gemini_count < MIN_GEMINI_MSGS:
        return False
    if total_msgs < MIN_TOTAL_MSGS:
        return False
    if content_chars < MIN_CONTENT_CHARS:
        return False
    return True


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_gemini_cli(source_path: Path | str, output_dir: Optional[Path] = None) -> Optional[FileSet]:
    """Parse a Gemini CLI source and write the two canonical files.

    Args:
        source_path: Path to the Gemini session file (.jsonl, .json, or logs.json).
        output_dir: Directory to write into. Defaults to ~/peacock/aichats/gemini-cli.

    Returns:
        FileSet with paths to chat and think markdown files.
    """
    source_path = Path(source_path).expanduser().resolve()
    if not source_path.exists():
        raise FileNotFoundError(f"Source not found: {source_path}")

    sets = _parse_source(source_path)

    # Empty / junk session filter — check BEFORE creating any directory or files
    if not _should_keep_session(sets):
        return None

    title = source_path.stem or "Untitled"
    slug = _make_slug(title)
    date_str = _extract_best_date(source_path)

    out = (output_dir or DEFAULT_OUTPUT_ROOT).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    dir_name = _disambiguate_dir(out, date_str, slug)
    session_dir = out / dir_name
    session_dir.mkdir(parents=True, exist_ok=True)

    chat_path = session_dir / f"{dir_name}_chat.md"
    think_path = session_dir / f"{dir_name}_think.md"

    chat_path.write_text(_generate_chat_md(sets, title, date_str), encoding="utf-8")
    think_path.write_text(_generate_think_md(sets), encoding="utf-8")

    return FileSet(chat=chat_path, think=think_path)


# ---------------------------------------------------------------------------
# Batch processing
# ---------------------------------------------------------------------------

GEMINI_ROOT = Path.home() / ".gemini" / "tmp"


def discover_gemini_sources(gemini_dir: Optional[Path] = None) -> List[Tuple[Path, str]]:
    """Discover all Gemini CLI conversation sources.

    Returns a list of (source_path, source_type) tuples sorted by mtime.
    """
    root = gemini_dir or GEMINI_ROOT
    sources: List[Tuple[Path, str]] = []
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
                if entry.suffix == ".jsonl" and entry.stem.startswith("session-"):
                    sources.append((entry, "jsonl"))
                elif entry.suffix == ".json" and entry.stem.startswith("session-"):
                    sources.append((entry, "json"))
                elif entry.suffix == ".jsonl":
                    sources.append((entry, "subagent"))
        logs_json = project_dir / "logs.json"
        if logs_json.exists():
            sources.append((logs_json, "logs"))

    sources.sort(key=lambda item: item[0].stat().st_mtime, reverse=True)
    return sources


def batch_process(
    output_dir: Optional[Path] = None,
    gemini_dir: Optional[Path] = None,
    clean_old: bool = False,
    purge_empty: bool = False,
) -> str:
    """Process all discovered Gemini CLI sources into the new directory format.

    Args:
        output_dir: Directory to write into. Defaults to ~/peacock/aichats/gemini-cli.
        gemini_dir: Root directory to scan for sources. Defaults to ~/.gemini/tmp.
        clean_old: If True, remove old flat .md files after successful batch.
        purge_empty: If True, remove empty/junk output directories before batch.

    Returns:
        One-line summary string.
    """
    out = (output_dir or DEFAULT_OUTPUT_ROOT).expanduser().resolve()

    # Purge empty directories from previous runs
    if purge_empty and out.exists():
        for item in out.iterdir():
            if item.is_dir():
                chat_file = item / f"{item.name}_chat.md"
                if chat_file.exists():
                    chat_text = chat_file.read_text(encoding="utf-8")
                    # Check if it's an empty session (0 sets or just header)
                    if "> 0 sets ·" in chat_text or "=== Set 1 ===" not in chat_text:
                        try:
                            import shutil
                            shutil.rmtree(item)
                        except Exception:
                            pass

    sources = discover_gemini_sources(gemini_dir)
    if not sources:
        return "📊 Gemini batch: 0 sources found"

    processed = 0
    skipped = 0
    failed = 0
    errors: List[Tuple[str, str]] = []

    for idx, (source_path, src_type) in enumerate(sources, 1):
        try:
            result = parse_gemini_cli(source_path, out)
            if result is None:
                skipped += 1
            else:
                processed += 1
        except Exception as exc:
            failed += 1
            errors.append((source_path.name, str(exc)))

    # Clean old flat files if requested
    if clean_old and out.exists():
        for flat in out.glob("*.md"):
            try:
                flat.unlink()
            except Exception:
                pass

    summary = f"📊 Gemini batch: {processed} processed, {skipped} skipped, {failed} failed of {len(sources)} total → {out}"
    if clean_old:
        summary += " (old flat files removed)"
    if purge_empty:
        summary += " (empty dirs purged)"
    if errors and failed <= 5:
        for name, err in errors:
            print(f"  ⚠️  {name}: {err}", file=sys.stderr)
    return summary


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def _main() -> None:
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        prog="gemini_cli_parser",
        description="Parse Gemini CLI sessions into strict 2-file Set format.",
    )
    parser.add_argument("source", nargs="?", type=Path, default=None,
                        help="Path to Gemini session file (omit for batch mode)")
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=None,
        help=f"Output directory (default: {DEFAULT_OUTPUT_ROOT})",
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Process all discovered Gemini sources",
    )
    parser.add_argument(
        "--clean-old",
        action="store_true",
        help="Remove old flat .md files after batch processing",
    )
    parser.add_argument(
        "--purge-empty",
        action="store_true",
        help="Remove empty/junk output directories before batch",
    )
    args = parser.parse_args()

    if args.batch or args.source is None:
        summary = batch_process(
            args.output_dir,
            clean_old=args.clean_old,
            purge_empty=args.purge_empty,
        )
        print(summary)
        return

    try:
        files = parse_gemini_cli(args.source, args.output_dir)
    except Exception as exc:
        print(f"❌ Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if files is None:
        print("⏭️  Session skipped: empty or junk (0 gemini responses or < 50 chars)")
        return

    sets = _parse_source(args.source)
    print(f'"Gemini-CLI locked. Per-session directory with _chat.md + _think.md, '
          f'full legacy + new format support, numbered Sets + Think Sets with correlation, '
          f'date-first naming, ready."')
    print(f"   Sets : {len(sets)}")
    print(f"   Chat : {files.chat}")
    print(f"   Think: {files.think}")


if __name__ == "__main__":
    _main()
