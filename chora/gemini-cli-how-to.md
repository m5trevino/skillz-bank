# Gemini CLI Parser — How-To & Reference

> **Location:** `~/.kimi/skills/chora/parsers/gemini_cli_parser.py`  
> **Purpose:** Parse Gemini CLI session exports into clean, correlated `_chat.md` + `_think.md` per-session directories.  
> **Author:** Slice C13 + Empty-Session Filter  

---

## Table of Contents

1. [What It Does](#what-it-does)
2. [Input Formats](#input-formats)
3. [Output Format](#output-format)
4. [Empty / Junk Session Filter](#empty--junk-session-filter)
5. [How to Run](#how-to-run)
6. [Python API](#python-api)
7. [File Naming](#file-naming)
8. [How It Works Internally](#how-it-works-internally)
9. [Examples](#examples)
10. [Troubleshooting](#troubleshooting)

---

## What It Does

The parser reads Gemini CLI chat logs (JSONL, JSON, or logs.json) and produces **exactly two files** inside a dedicated per-session directory:

- **`_chat.md`** — Clean conversation only. User messages and assistant replies. No tool calls, no thinking, no metadata.
- **`_think.md`** — All thinking blocks, correlated 1:1 with chat Sets.

It supports **both legacy and new Gemini formats**, auto-detects the file type, skips empty/junk sessions silently, and never creates an output directory for a session that fails the quality filter.

---

## Input Formats

### 1. New JSONL (preferred)
**Location:** `~/.gemini/tmp/<project>/chats/session-YYYY-MM-DDTHH-MM-xxxxxxxx.jsonl`

Each line is a JSON object:
```json
{"type": "user", "content": [{"text": "Hello"}]}
{"type": "gemini", "content": "Hi!", "thoughts": [{"subject": "Greeting", "description": "Simple greeting"}]}
```

- First line may contain `$set` metadata with `startTime` — used for date extraction.
- Skipped types: `$set`, `info`, empty-type lines, session metadata.

### 2. Old JSON (legacy)
**Location:** `~/.gemini/tmp/<project>/chats/session-*.json`

Single JSON object with a `messages` array:
```json
{
  "messages": [
    {"type": "user", "content": "Hello"},
    {"type": "gemini", "content": "Hi!", "thoughts": [...]}
  ]
}
```

### 3. logs.json (legacy fallback)
**Location:** `~/.gemini/tmp/<project>/logs.json`

Flat array of `{type, message}` entries:
```json
[
  {"type": "user", "message": "Hello"},
  {"type": "gemini", "message": "Hi!"}
]
```

**Auto-detection:** The parser peeks at the JSON structure to distinguish flat-array logs from dict-with-messages. It does **not** rely on filename alone.

---

## Output Format

### Directory structure
```
~/peacock/aichats/gemini-cli/
├── 2026-05-15_session_2026_05_15t22_23_f4be1043/
│   ├── 2026-05-15_session_2026_05_15t22_23_f4be1043_chat.md
│   └── 2026-05-15_session_2026_05_15t22_23_f4be1043_think.md
├── 2026-05-22_session_2026_05_22t13_12_b0902001/
│   ├── 2026-05-22_session_2026_05_22t13_12_b0902001_chat.md
│   └── 2026-05-22_session_2026_05_22t13_12_b0902001_think.md
```

### `_chat.md`
```markdown
# session-2026-05-15T22-23-f4be1043
> 45 sets · 2026-05-15
============================================================

=== Set 1 ===

user: Hello Gemini, write a Python hello world.

assistant: Here's a simple hello world in Python:

```python
print('Hello, world!')
```

-=-=-==--=--=

=== Set 2 ===

user: Now make it say my name.

assistant: Here's a version that accepts a name:

```python
name = input('Enter your name: ')
print(f'Hello, {name}!')
```

-=-=-==--=--=
```

**Rules:**
- Header: `# <title>\n> N sets · YYYY-MM-DD\n====...`
- Each Set: `=== Set N ===` followed by `user:` and `assistant:` blocks
- Separator: `-=-=-==--=--=`
- NO tool calls, NO thinking, NO metadata, NO `$set`, NO `info` lines

### `_think.md`
```markdown
=== Think Set 1 ===

[Planning]
The user wants a basic Python example. I'll provide a concise hello world.

=== Think Set 2 ===

[Enhancement]
The user wants personalization. I'll add an input prompt.
```

**Rules:**
- Numbered `Think Set N` correlates 1:1 with `Set N` in `_chat.md`
- Only includes Sets that actually have thinking content
- Empty Sets (no thoughts) are omitted from the think file

---

## Empty / Junk Session Filter

**Before creating any directory or file**, the parser runs this mandatory filter:

| Check | Threshold | Purpose |
|-------|-----------|---------|
| User messages | ≥ 1 | Must have at least one real user message |
| Gemini responses | ≥ 1 | **Critical** — kills ~90% of junk (dead sessions, logs with no bot replies) |
| Total messages | ≥ 3 | Filters ultra-short sessions |
| Content characters | ≥ 50 | Filters near-empty sessions |

If **any** check fails, the session is **silently skipped**. No directory is created. No files are written.

These constants are defined at the top of the parser:
```python
MIN_USER_MSGS = 1
MIN_GEMINI_MSGS = 1
MIN_TOTAL_MSGS = 3
MIN_CONTENT_CHARS = 50
```

---

## How to Run

### Single file
```bash
python3 ~/.kimi/skills/chora/parsers/gemini_cli_parser.py \
  ~/.gemini/tmp/myproject/chats/session-2026-05-15T22-23-f4be1043.jsonl
```

Output goes to `~/peacock/aichats/gemini-cli/` by default.

### Custom output directory
```bash
python3 ~/.kimi/skills/chora/parsers/gemini_cli_parser.py \
  ~/.gemini/tmp/myproject/chats/session-xxx.jsonl \
  --output-dir ~/my-gemini-archive
```

### Batch — all discovered sources
```bash
python3 ~/.kimi/skills/chora/parsers/gemini_cli_parser.py --batch
```

This discovers all sources under `~/.gemini/tmp/` and processes each one.

### Batch with cleanup options
```bash
# Remove old flat .md files after batch
python3 ~/.kimi/skills/chora/parsers/gemini_cli_parser.py --batch --clean-old

# Remove empty/junk directories from a previous run before re-processing
python3 ~/.kimi/skills/chora/parsers/gemini_cli_parser.py --batch --purge-empty

# Do both
python3 ~/.kimi/skills/chora/parsers/gemini_cli_parser.py --batch --clean-old --purge-empty
```

### Clean rebuild (recommended after spec changes)
```bash
# Delete all existing output directories and rebuild from scratch
rm -rf ~/peacock/aichats/gemini-cli/*/
python3 ~/.kimi/skills/chora/parsers/gemini_cli_parser.py --batch
```

---

## Python API

### Parse a single source
```python
from pathlib import Path
from gemini_cli_parser import parse_gemini_cli

result = parse_gemini_cli("/path/to/session.jsonl")

if result is None:
    print("Session skipped — empty or junk")
else:
    print(f"Chat:  {result.chat}")
    print(f"Think: {result.think}")
```

### Batch process programmatically
```python
from gemini_cli_parser import batch_process

summary = batch_process(
    output_dir=Path("~/my-archive"),
    clean_old=True,      # remove old flat .md files
    purge_empty=True,    # remove empty dirs from previous runs
)
print(summary)
# → 📊 Gemini batch: 82 processed, 134 skipped, 0 failed of 216 total
```

### Discover sources only
```python
from gemini_cli_parser import discover_gemini_sources

sources = discover_gemini_sources()
for path, src_type in sources:
    print(f"{path} ({src_type})")
```

---

## File Naming

### Directory name
```
YYYY-MM-DD_slug
YYYY-MM-DD_slug_001   # if duplicate exists
```

- **Date:** Extracted from `startTime` / `timestamp` in metadata, then filename, then file mtime. Never today's date unless no other source exists.
- **Slug:** Cleaned file stem — lowercase, spaces → underscores, special chars removed.

### File names inside directory
```
YYYY-MM-DD_slug_chat.md
YYYY-MM-DD_slug_think.md
```

---

## How It Works Internally

### Pipeline

```
Source File
    ↓
[Auto-detect format]
    ├── JSONL  → _parse_jsonl()
    ├── JSON (dict+messages) → _parse_legacy_session_json()
    └── JSON (flat array)    → _parse_legacy_logs_json()
    ↓
[Build Set objects]
    Set(set_num, user_text, assistant_text, think_text)
    ↓
[Empty / Junk Filter]
    _should_keep_session(sets)
    ├── FAIL → return None (silently skip)
    └── PASS → continue
    ↓
[Extract date + slug]
    _extract_best_date() + _make_slug()
    ↓
[Create directory]
    YYYY-MM-DD_slug/
    ↓
[Write files]
    _generate_chat_md()  → _chat.md
    _generate_think_md() → _think.md
```

### Key functions

| Function | Purpose |
|----------|---------|
| `_parse_jsonl()` | New line-by-line JSONL format |
| `_parse_legacy_session_json()` | Old `session-*.json` with `messages` array |
| `_parse_legacy_logs_json()` | Flat `logs.json` array |
| `_extract_text()` | Coerce any content shape (string, array, dict) to plain text |
| `_extract_think()` | Extract `thoughts` array with `subject` + `description` |
| `_should_keep_session()` | Quality filter — returns True only if session passes all thresholds |
| `_extract_best_date()` | Date extraction from metadata → filename → mtime |
| `_make_slug()` | Filesystem-safe slug from file stem |
| `_disambiguate_dir()` | Append `_001`, `_002` if directory already exists |
| `_generate_chat_md()` | Build `_chat.md` content |
| `_generate_think_md()` | Build `_think.md` content |
| `parse_gemini_cli()` | Main public API — single source |
| `batch_process()` | Process all discovered sources |
| `discover_gemini_sources()` | Walk `~/.gemini/tmp/` and find all parseable files |

---

## Examples

### Example 1: New JSONL with thinking
**Input:** `session-2026-05-15T22-23-f4be1043.jsonl`
```jsonl
{"type":"$set","sessionId":"abc","startTime":"2026-05-15T10:30:00Z"}
{"type":"user","content":[{"text":"Hello"}]}
{"type":"gemini","content":"Hi!","thoughts":[{"subject":"Greeting","description":"Simple reply"}]}
```

**Output:**
```
2026-05-15_session_2026_05_15t22_23_f4be1043/
├── 2026-05-15_session_2026_05_15t22_23_f4be1043_chat.md
└── 2026-05-15_session_2026_05_15t22_23_f4be1043_think.md
```

### Example 2: Legacy logs.json
**Input:** `logs.json`
```json
[
  {"type": "user", "message": "Hello from logs"},
  {"type": "gemini", "message": "Hi from logs!"},
  {"type": "user", "message": "What can you do?"},
  {"type": "gemini", "message": "I can help with coding, writing, analysis, and more."}
]
```

**Output:**
```
2026-06-01_logs/
├── 2026-06-01_logs_chat.md
└── 2026-06-01_logs_think.md
```

### Example 3: Empty session (silently skipped)
**Input:** `session-empty.jsonl`
```jsonl
{"type":"$set","sessionId":"empty"}
{"type":"user","content":[{"text":"Hi"}]}
```

**Result:** `parse_gemini_cli()` returns `None`. No directory created. No output.

---

## Troubleshooting

### "No sources found"
- Check that `~/.gemini/tmp/` exists and contains project directories.
- Verify source files have `.jsonl`, `.json`, or are named `logs.json`.

### "0 sets" in output
- The file may contain only user messages with no gemini responses (common in `logs.json`).
- The session may have been abandoned before any assistant reply.
- These are **correctly skipped** by the empty-session filter.

### Duplicate `_001` directories
- Two different project folders contain the same session file (same date + slug).
- This is correct behavior — each source gets its own output directory.

### Old flat `.md` files still present
- Run with `--clean-old` flag, or manually delete them:
  ```bash
  rm ~/peacock/aichats/gemini-cli/*.md
  ```

### Empty directories from previous runs
- Run with `--purge-empty` flag, or manually clean:
  ```bash
  rm -rf ~/peacock/aichats/gemini-cli/*/
  ```

---

## Quick Reference Card

```bash
# Single file
python3 gemini_cli_parser.py <source>

# Batch all
python3 gemini_cli_parser.py --batch

# Batch + clean
python3 gemini_cli_parser.py --batch --clean-old --purge-empty

# Custom output
python3 gemini_cli_parser.py --batch --output-dir ~/archive

# Python API
from gemini_cli_parser import parse_gemini_cli, batch_process
parse_gemini_cli("session.jsonl")
batch_process(clean_old=True, purge_empty=True)
```

---

*End of document.*
