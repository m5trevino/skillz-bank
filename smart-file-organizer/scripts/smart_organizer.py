#!/usr/bin/env python3
"""
Smart File Organizer — Backend utility for the smart-file-organizer skill.

Handles directory setup, file analysis, learned-pattern matching, file moves,
and memory persistence. All user interaction is handled by the agent; this
script only returns structured data and executes filesystem operations.

Subcommands:
    setup   Create project folders inside a target directory.
    analyze Scan files and return confidence-ranked suggestions as JSON.
    move    Move a file into a project folder.
    learn   Record a user choice to improve future suggestions.
"""

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MEMORY_PATH = Path.home() / ".smart_file_organizer" / "memory.json"
MAX_EXCERPT_CHARS = 300
BINARY_CHECK_BYTES = 1024

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def ensure_memory() -> dict[str, Any]:
    """Load the memory JSON, or return a fresh structure."""
    if MEMORY_PATH.exists():
        try:
            with open(MEMORY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"entries": []}


def save_memory(memory: dict[str, Any]) -> None:
    """Persist memory to disk."""
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MEMORY_PATH, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2)


def is_binary(file_path: Path) -> bool:
    """Heuristic: check if a file is binary."""
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(BINARY_CHECK_BYTES)
        if b"\x00" in chunk:
            return True
        return False
    except OSError:
        return True


def get_excerpt(file_path: Path) -> str:
    """Return a short text excerpt for display, or metadata for binaries."""
    if is_binary(file_path):
        size = file_path.stat().st_size
        return f"[Binary file, {size} bytes]"
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read(MAX_EXCERPT_CHARS * 2)
        # Collapse whitespace and truncate
        text = re.sub(r"\s+", " ", text).strip()
        return text[:MAX_EXCERPT_CHARS]
    except OSError as e:
        return f"[Unable to read: {e}]"


def extract_keywords(text: str) -> list[str]:
    """Extract meaningful lowercase keywords from text."""
    # Remove non-alphanumeric, split, filter short tokens and common stop words
    stop_words = {
        "the", "and", "for", "are", "but", "not", "you", "all", "can",
        "had", "her", "was", "one", "our", "out", "day", "get", "has",
        "him", "his", "how", "man", "new", "now", "old", "see", "two",
        "way", "who", "boy", "did", "its", "let", "put", "say", "she",
        "too", "use", "with", "have", "this", "will", "your", "from",
        "they", "know", "want", "been", "good", "much", "some", "time",
        "very", "when", "come", "here", "just", "like", "long", "make",
        "many", "over", "such", "take", "than", "them", "well", "were",
    }
    words = re.findall(r"[a-zA-Z0-9_\-]+", text.lower())
    keywords = [w for w in words if len(w) >= 3 and w not in stop_words]
    return keywords


def learn(memory: dict[str, Any], file_path: Path, project: str) -> None:
    """Record a user choice in memory."""
    filename = file_path.name
    excerpt = get_excerpt(file_path)
    keywords = extract_keywords(filename + " " + excerpt)

    # Check for existing entry to update frequency
    for entry in memory["entries"]:
        if entry["project"] == project and filename in entry.get("filename_patterns", []):
            entry["frequency"] = entry.get("frequency", 1) + 1
            # Merge new keywords
            existing = set(entry.get("content_keywords", []))
            existing.update(keywords)
            entry["content_keywords"] = list(existing)
            save_memory(memory)
            return

    # New entry
    memory["entries"].append({
        "filename_patterns": [filename],
        "content_keywords": keywords,
        "project": project,
        "frequency": 1,
    })
    save_memory(memory)


def suggest(memory: dict[str, Any], file_path: Path, projects: list[str]) -> dict[str, Any]:
    """Return suggestion info for a single file."""
    filename = file_path.name
    excerpt = get_excerpt(file_path)
    keywords = extract_keywords(filename + " " + excerpt)

    best_project = None
    best_confidence = 0.0
    matched_keywords: dict[str, list[str]] = {}

    for entry in memory.get("entries", []):
        # Filename pattern match
        filename_match = any(
            pat in filename.lower() or re.search(pat, filename, re.IGNORECASE)
            for pat in entry.get("filename_patterns", [])
        )

        # Keyword overlap
        entry_keywords = set(entry.get("content_keywords", []))
        overlap = entry_keywords.intersection(keywords)

        # Calculate raw score
        score = 0.0
        if filename_match:
            score += 0.5
        score += min(len(overlap) * 0.15, 0.5)
        # Boost by frequency
        freq = entry.get("frequency", 1)
        score *= (1 + 0.1 * (freq - 1))
        score = min(score, 1.0)

        if score > best_confidence:
            best_confidence = score
            best_project = entry["project"]
            matched_keywords[best_project] = list(overlap)

    # Also do naive keyword matching against project names themselves
    for proj in projects:
        proj_kw = extract_keywords(proj)
        overlap = set(proj_kw).intersection(keywords)
        if overlap:
            score = min(len(overlap) * 0.2, 0.6)
            if score > best_confidence:
                best_confidence = score
                best_project = proj
                matched_keywords[best_project] = list(overlap)

    return {
        "file": str(file_path),
        "excerpt": excerpt,
        "suggested_project": best_project,
        "confidence": round(best_confidence, 3),
        "keywords_matched": matched_keywords.get(best_project, []),
    }


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------


def cmd_setup(args: argparse.Namespace) -> None:
    target = Path(args.target_dir).expanduser().resolve()
    projects = [p.strip() for p in args.projects.split(",") if p.strip()]
    if not projects:
        print("Error: no project folders specified.", file=sys.stderr)
        sys.exit(1)
    for proj in projects:
        proj_dir = target / proj
        proj_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created: {proj_dir}")
    print(json.dumps({"status": "ok", "created": projects}))


def cmd_analyze(args: argparse.Namespace) -> None:
    target = Path(args.target_dir).expanduser().resolve()
    projects = [p.strip() for p in args.projects.split(",") if p.strip()]
    memory = ensure_memory()
    results = []

    if not target.is_dir():
        print(f"Error: {target} is not a directory.", file=sys.stderr)
        sys.exit(1)

    # Gather files (non-recursive, top-level only)
    entries = sorted(
        [e for e in target.iterdir() if e.is_file()],
        key=lambda e: e.name.lower(),
    )

    for entry in entries:
        info = suggest(memory, entry, projects)
        results.append(info)

    print(json.dumps(results, indent=2))


def cmd_move(args: argparse.Namespace) -> None:
    source = Path(args.source).expanduser().resolve()
    dest_dir = Path(args.dest_dir).expanduser().resolve()
    project = args.project

    if not source.exists():
        print(f"Error: source file not found: {source}", file=sys.stderr)
        sys.exit(1)

    dest = dest_dir / project / source.name
    # Handle name collisions
    counter = 1
    original_dest = dest
    while dest.exists():
        stem = original_dest.stem
        suffix = original_dest.suffix
        dest = original_dest.with_name(f"{stem}_{counter}{suffix}")
        counter += 1

    shutil.move(str(source), str(dest))
    print(json.dumps({"status": "moved", "from": str(source), "to": str(dest)}))


def cmd_learn(args: argparse.Namespace) -> None:
    file_path = Path(args.file).expanduser().resolve()
    project = args.project
    memory = ensure_memory()
    learn(memory, file_path, project)
    print(json.dumps({"status": "learned", "file": str(file_path), "project": project}))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Smart File Organizer backend")
    sub = parser.add_subparsers(dest="command", required=True)

    p_setup = sub.add_parser("setup", help="Create project folders")
    p_setup.add_argument("target_dir")
    p_setup.add_argument("--projects", required=True)

    p_analyze = sub.add_parser("analyze", help="Analyze files and suggest folders")
    p_analyze.add_argument("target_dir")
    p_analyze.add_argument("--projects", required=True)

    p_move = sub.add_parser("move", help="Move a file into a project folder")
    p_move.add_argument("source")
    p_move.add_argument("dest_dir")
    p_move.add_argument("--project", required=True)

    p_learn = sub.add_parser("learn", help="Record a user choice")
    p_learn.add_argument("--file", required=True)
    p_learn.add_argument("--project", required=True)

    args = parser.parse_args()

    if args.command == "setup":
        cmd_setup(args)
    elif args.command == "analyze":
        cmd_analyze(args)
    elif args.command == "move":
        cmd_move(args)
    elif args.command == "learn":
        cmd_learn(args)


if __name__ == "__main__":
    main()
