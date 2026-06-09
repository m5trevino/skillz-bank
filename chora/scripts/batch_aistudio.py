#!/usr/bin/env python3
"""Batch re-process all AI Studio chat logs with the fixed parser."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers.aistudio_parser import parse_aistudio

ROOT = Path.home() / "ai-chats" / "aistudio" / "accounts"

total = 0
success = 0
failed = 0
errors = []

for account_dir in ROOT.iterdir():
    if not account_dir.is_dir():
        continue
    chat_logs = account_dir / "chat-logs"
    if not chat_logs.exists():
        continue
    for entry in chat_logs.iterdir():
        if not entry.is_file() or entry.name.startswith("."):
            continue
        total += 1
        try:
            parse_aistudio(str(entry))
            success += 1
        except Exception as e:
            failed += 1
            errors.append(f"{entry.name}: {e}")
        if total % 100 == 0:
            print(f"  ... processed {total} files ({success} OK, {failed} failed)")

print(f"\n✅ Done: {success}/{total} succeeded, {failed} failed")
if errors:
    print("\nErrors:")
    for e in errors[:30]:
        print(f"  {e}")
    if len(errors) > 30:
        print(f"  ... and {len(errors) - 30} more")
