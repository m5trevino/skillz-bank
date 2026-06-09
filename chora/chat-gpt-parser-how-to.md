# ChatGPT Parser — How-To & Technical Reference

> **Location:** `~/.kimi/skills/chora/parsers/chatgpt_parser.py`  
> **Purpose:** Convert ChatGPT JSON exports into clean, readable `_chat.md` files using the strict Set format.  
> **Author:** Kimi Code CLI (Slice C16)  
> **Last updated:** 2026-06-01

---

## Table of Contents

1. [What It Does](#what-it-does)
2. [Quick Start](#quick-start)
3. [CLI Usage](#cli-usage)
4. [Python API](#python-api)
5. [Output Format Specification](#output-format-specification)
6. [How It Works (Internals)](#how-it-works-internals)
7. [File Naming Rules](#file-naming-rules)
8. [Error Handling](#error-handling)
9. [Examples](#examples)
10. [Troubleshooting](#troubleshooting)

---

## What It Does

The ChatGPT parser takes a ChatGPT data-export JSON file and produces **one markdown file per conversation**.

### Supported Inputs

| Input | Description |
|-------|-------------|
| `conversations.json` | The standard ChatGPT export — an array of conversation objects with `mapping` trees. |
| Individual `.json` | A single conversation object exported from ChatGPT. |

### What It Produces

For every conversation found in the source JSON, the parser writes a single `_chat.md` file to the output directory containing **only the raw conversation** — no thinking blocks, no metadata, no tool-call noise, no HTML.

---

## Quick Start

```bash
# Basic usage — processes all conversations in the export
python3 ~/.kimi/skills/chora/parsers/chatgpt_parser.py \
  ~/ai-chats/chatgpt/conversations.json

# Custom output directory
python3 ~/.kimi/skills/chora/parsers/chatgpt_parser.py \
  ~/ai-chats/chatgpt/conversations.json \
  --output-dir ~/my-archive/chatgpt
```

**Default output:** `~/peacock/aichats/chatgpt/`

---

## CLI Usage

```
usage: chatgpt_parser.py [-h] [--output-dir OUTPUT_DIR] source

Parse ChatGPT exports to _chat.md

positional arguments:
  source                Path to conversations.json or a single .json export

optional arguments:
  -h, --help            show this help message and exit
  --output-dir OUTPUT_DIR, -o OUTPUT_DIR
                        Output directory override
```

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success — at least one file written. |
| `1` | Error — file not found, empty source, or no parseable conversations. |

---

## Python API

Import and call `parse_chatgpt()` from any Python script or agent session.

```python
from pathlib import Path
from parsers.chatgpt_parser import parse_chatgpt

# Default output directory (~/peacock/aichats/chatgpt)
path: Path = parse_chatgpt("/home/user/ai-chats/chatgpt/conversations.json")
print(path)
# → /home/user/peacock/aichats/chatgpt/2025-01-20_runtime_mobile_security_rms_chat.md

# Custom output directory
path = parse_chatgpt(
    "/home/user/ai-chats/chatgpt/conversations.json",
    output_dir="/home/user/my-archive"
)
```

### Function Signature

```python
def parse_chatgpt(source_path: str, output_dir: Optional[str] = None) -> Path:
    """
    Parse a ChatGPT JSON export and write one _chat.md file per conversation.

    Args:
        source_path: Path to a ChatGPT conversations.json or individual .json export.
        output_dir: Override the default output directory.
                    Defaults to ~/peacock/aichats/chatgpt.

    Returns:
        Path to the first written _chat.md file.

    Raises:
        FileNotFoundError: If source_path does not exist.
        ValueError: If source file is empty or contains no parseable conversations.
    """
```

### Important Notes for Programmatic Use

- **Multiple conversations:** If `source_path` points to `conversations.json` (array of 187 chats), **all 187 are written**. The return value is the `Path` of the *first* one only. Check the output directory to access the rest.
- **Idempotency:** Running the parser twice on the same source will create disambiguated duplicates (`_001`, `_002`, etc.) unless the original files are removed first.
- **Non-destructive:** The parser never modifies or deletes the source JSON.

---

## Output Format Specification

Every output file follows this exact structure. No exceptions.

### 1. Top Header (3 lines)

```markdown
# Chat Log — [exact chat title from JSON]
> N sets · YYYY-MM-DD
============================================================
```

- `N sets` = number of user↔assistant pairs in the conversation.
- `YYYY-MM-DD` = the conversation's actual creation date (from `create_time` in the JSON), **not** today's date.

### 2. Set Blocks (repeated N times)

```markdown
=== Set 1 ===
user: exact raw user message here
(can span multiple lines)

assistant: exact final assistant message here
(can span multiple lines, includes embedded code blocks)

-=-=-==--=--=
```

Rules:
- Each set is numbered sequentially starting at `1`.
- `user:` and `assistant:` lines are literal prefixes, **not** markdown headers.
- The assistant message preserves **embedded code blocks** (triple-backtick fences) exactly as they appear in the original JSON.
- A blank line separates the `user:` block from the `assistant:` block.
- The separator `-=-=-==--=--=` appears **after every set**, including the last one.

### 3. What Is Removed

The parser intentionally strips the following so the output contains **only** the raw conversation:

- System messages (`role: "system"`)
- Tool messages (`role: "tool"`)
- Thinking / reasoning blocks
- Message IDs, timestamps, and metadata
- JSON structure artifacts

---

## How It Works (Internals)

### Step 1 — Load & Normalize JSON

The parser reads the source file and normalizes it into a list of conversation objects:

| Source Shape | Normalization |
|--------------|---------------|
| Array `[{...}, {...}]` | Each element is one conversation. |
| Single object `{...}` | Wrapped into a one-element list. |

### Step 2 — Traverse the Mapping Tree

ChatGPT stores conversations as a **directed acyclic graph** inside each conversation object's `mapping` field:

```json
{
  "mapping": {
    "uuid-1": { "parent": null, "children": ["uuid-2"], "message": {...} },
    "uuid-2": { "parent": "uuid-1", "children": ["uuid-3"], "message": {...} },
    "uuid-3": { "parent": "uuid-2", "children": [], "message": {...} }
  }
}
```

The parser:
1. Finds the **root node** (`parent: null`).
2. Walks the tree by always following `children[-1]` — the last child represents the **main conversation thread** (the path the user actually followed).
3. At each node, extracts `message.author.role` and `message.content`.
4. Keeps only nodes where `role` is `"user"` or `"assistant"` and the text is non-empty.
5. **Merges consecutive messages** from the same role into a single entry (handles multi-part assistant replies).

### Step 3 — Extract Text

ChatGPT content comes in multiple shapes:

| Shape | Handling |
|-------|----------|
| `{"content_type": "text", "parts": ["..."]}` | Extracts `parts` array. |
| `{"parts": ["...", "..."]}` | Joins all string parts. |
| Plain string | Used as-is. |
| Nested dicts | Recursively flattened. |

The `_extract_text()` helper handles all of these.

### Step 4 — Build the Set Document

The internal `_build_sets_md()` function assembles the final markdown string by iterating over the ordered `(role, text)` pairs and grouping them into Sets.

### Step 5 — Write to Disk

- **Date**: derived from `create_time` (Unix timestamp → `YYYY-MM-DD`).
- **Slug**: derived from the conversation `title` (lowercased, spaces → underscores, special chars stripped).
- **Filename**: `{date}_{slug}_chat.md`
- **Disambiguation**: if a file with the same name already exists, the slug gets a `_001`, `_002`, … suffix before `_chat.md`.

---

## File Naming Rules

| Component | Rule | Example |
|-----------|------|---------|
| Date | `YYYY-MM-DD` from `create_time` | `2025-01-20` |
| Slug | Lowercase title, spaces → `_`, special chars removed | `runtime_mobile_security_rms` |
| Suffix | Always `_chat.md` | `_chat.md` |
| Full name | `{date}_{slug}_chat.md` | `2025-01-20_runtime_mobile_security_rms_chat.md` |
| Disambiguation | Append `_001`, `_002` before `_chat.md` on collision | `2025-01-20_runtime_mobile_security_rms_001_chat.md` |

---

## Error Handling

| Scenario | Exception | Message |
|----------|-----------|---------|
| Source file missing | `FileNotFoundError` | `Source not found: {path}` |
| Source file empty | `ValueError` | `Source file is empty: {path}` |
| JSON is not object/array | `ValueError` | `Unexpected JSON type: {type}` |
| No user/assistant messages found | `ValueError` | `No parseable conversations found in {path}` |

All errors include the full path so you can debug immediately.

---

## Examples

### Example 1 — Process a full export

```bash
python3 ~/.kimi/skills/chora/parsers/chatgpt_parser.py \
  ~/Downloads/conversations.json
```

Output:
```
✅ Written: /home/user/peacock/aichats/chatgpt/2026-01-08_your_year_with_chatgpt_chat.md
```
(plus 186 other files in the same directory)

### Example 2 — Process a single exported chat

```bash
python3 ~/.kimi/skills/chora/parsers/chatgpt_parser.py \
  ~/Downloads/my-single-chat.json \
  --output-dir ~/Documents/chat-logs
```

Output:
```
✅ Written: /home/user/Documents/chat-logs/2025-03-15_flask_api_design_chat.md
```

### Example 3 — Use inside another Python script

```python
#!/usr/bin/env python3
from parsers.chatgpt_parser import parse_chatgpt
from pathlib import Path

SOURCE = Path.home() / "ai-chats" / "chatgpt" / "conversations.json"
OUT    = Path.home() / "peacock" / "aichats" / "chatgpt"

try:
    first_file = parse_chatgpt(str(SOURCE), str(OUT))
    print(f"Done. First file: {first_file.name}")
    print(f"Total files in output: {len(list(OUT.glob('*.md')))}")
except ValueError as e:
    print(f"Parse error: {e}")
```

---

## Troubleshooting

### "No parseable conversations found"

- Verify the JSON is a valid ChatGPT export (should have `mapping` or `messages` at the top level).
- If the file contains only system/tool messages and no user/assistant text, the parser correctly skips it.

### Duplicate `_001` files appearing

- The parser disambiguates by design. Remove old `.md` files before re-running if you want clean names.

### Wrong date on output files

- The parser uses `create_time` from the conversation object. If ChatGPT didn't populate this field, it falls back to `update_time` → `created_at` → `updated_at` → today.

### Output directory not created

- The parser auto-creates the output directory (and any parent directories) via `mkdir(parents=True, exist_ok=True)`.

### Very large `conversations.json` (100 MB+)

- The parser loads the entire JSON into memory. For truly massive exports, consider splitting the file or using a streaming JSON parser. (This is a known limitation.)

---

## Related Files

| File | Purpose |
|------|---------|
| `~/.kimi/skills/chora/parsers/chatgpt_parser.py` | **This parser** |
| `~/.kimi/skills/chora/scripts/chora.py` | Main Chora orchestrator (supports ChatGPT, Claude, Gemini, AI Studio, Kimi) |
| `~/.kimi/skills/chora/SKILL.md` | Chora skill documentation |

---

*End of document.*
