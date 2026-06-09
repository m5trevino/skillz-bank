#!/usr/bin/env python3
"""Devwater hook wrapper for kimi_code_parser.

Called by pre-compact-export.sh instead of the obsolete chora.py skill.
Imports the real kimi_code_parser from /home/flintx/chora/parsers/ and
adapts its output for the devwater-data directory structure.

Usage:
    python3 devwater_kimi_wrapper.py <session_dir> <output_dir> <basename>

Output:
    Renames parser output from YYYY-MM-DD_slug/{slug}_chat.md → {basename}-chat.md
    and YYYY-MM-DD_slug/{slug}_think.md → {basename}-think.md,
    both placed directly in <output_dir>.
"""

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parsers.kimi_code_parser import parse_kimi_code


def main() -> int:
    if len(sys.argv) < 4:
        print("Usage: python3 devwater_kimi_wrapper.py <session_dir> <output_dir> <basename>", file=sys.stderr)
        return 1

    session_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    basename = sys.argv[3]

    try:
        chat_path, think_path = parse_kimi_code(
            session_dir, output_dir=output_dir, min_assistant_chars=100
        )
    except RuntimeError as e:
        if "SESSION_EMPTY" in str(e):
            print("EMPTY", flush=True)
            return 0
        raise

    # Rename files to devwater convention
    new_chat = output_dir / f"{basename}-chat.md"
    new_think = output_dir / f"{basename}-think.md"

    chat_path.rename(new_chat)
    think_path.rename(new_think)

    # Remove the now-empty dated subdirectory if possible
    dated_dir = chat_path.parent
    if dated_dir != output_dir:
        try:
            dated_dir.rmdir()
        except OSError:
            pass

    print(f"CHAT:{new_chat}")
    print(f"THINK:{new_think}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
