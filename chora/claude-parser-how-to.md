# Claude Parser — How-To & Reference

**Location:** `parsers/claude_parser.py`  
**Purpose:** Parse Claude JSON chat exports into clean, numbered-Set markdown files.  
**Output directory:** `~/peacock/aichats/claude/`

---

## Table of Contents

1. [What It Does](#what-it-does)
2. [Quick Start](#quick-start)
3. [Input Format](#input-format)
4. [Output Format](#output-format)
5. [File Naming Rules](#file-naming-rules)
6. [API Reference](#api-reference)
7. [How It Works Internally](#how-it-works-internally)
8. [Edge Cases & Behaviour](#edge-cases--behaviour)
9. [Troubleshooting](#troubleshooting)

---

## What It Does

`claude_parser.py` reads Claude JSON exports and writes one `_chat.md` file per conversation.

**Stripped logic from:**
- `/home/flintx/save-aichats-personal-edition/backend/main.py`
- `/home/flintx/.kimi/skills/chora/claude-logic-chatlog-path-info.txt`

**It keeps:**
- Final user messages
- Final assistant responses
- Markdown code blocks **embedded** inside assistant text

**It discards:**
- `tool_use` blocks (Claude's internal tool calls)
- `tool_result` blocks (raw tool output)
- `thinking` / reasoning blocks
- `token_budget` metadata
- `voice_note` attachments
- System events or meta-text

---

## Quick Start

### Run from command line

```bash
# Default: parse the system-wide conversations.json
python3 /home/flintx/.kimi/skills/chora/parsers/claude_parser.py

# Parse a specific file
python3 /home/flintx/.kimi/skills/chora/parsers/claude_parser.py /path/to/your/conversations.json
```

### Use as a module

```python
from parsers.claude_parser import parse_claude

results = parse_claude("/home/flintx/ai-chats/claude/conversations.json")

# results is a dict: {filename: markdown_content}
for fname, content in results.items():
    print(f"Written: {fname} ({len(content)} chars)")
```

### One-liner in Python

```python
from parsers.claude_parser import parse_claude, OUTPUT_ROOT

parse_claude("/home/flintx/ai-chats/claude/conversations.json")
print(f"Files in {OUTPUT_ROOT}:", list(OUTPUT_ROOT.glob("*_chat.md")))
```

---

## Input Format

The parser accepts any of these JSON shapes:

### 1. `conversations.json` — array of conversations

```json
[
  {
    "uuid": "7e40514b-fc55-429c-9bd4-a3cfbea7c9bc",
    "name": "Sublime Text Column Selection",
    "created_at": "2025-06-11T01:52:20.971202Z",
    "chat_messages": [
      {
        "sender": "human",
        "content": [{"type": "text", "text": "IN SUBLIME HOW DO I..."}]
      },
      {
        "sender": "assistant",
        "content": [
          {"type": "text", "text": "Aight, what up G!..."},
          {"type": "tool_use", "name": "read_file", "input": {...}},
          {"type": "tool_result", "content": "..."},
          {"type": "text", "text": "So basically..."}
        ]
      }
    ]
  }
]
```

### 2. Single conversation object

```json
{
  "name": "My Chat",
  "created_at": "2025-06-01T12:00:00Z",
  "chat_messages": [...]
}
```

### Field mapping

| JSON Field | Used For |
|------------|----------|
| `name` / `title` | Chat title → slug → filename |
| `created_at` / `updated_at` / `create_time` / `timestamp` | Date extraction (YYYY-MM-DD) |
| `chat_messages` / `messages` | Message list to parse |
| `sender` / `role` | Determines user vs assistant |
| `content` / `text` | Message text extraction |

---

## Output Format

Each generated `_chat.md` follows this exact template:

```markdown
# Chat Log — {chat title}

> {N} sets · {YYYY-MM-DD}

============================================================

=== Set 1 ===
user: {exact raw user message}

assistant: {exact final assistant message with embedded code blocks}

-=-=-==--=--=

=== Set 2 ===
user: {next user message}

assistant: {next assistant message}

-=-=-==--=--=

...

============================================================
```

### Rules of the format

1. **Header** — `# Chat Log — {clean title}`
2. **Meta line** — `> N sets · YYYY-MM-DD` (chat creation date, not today's date)
3. **Top divider** — 60 `=` characters
4. **Per Set:**
   - `=== Set N ===`
   - `user: ` + full raw message (may span multiple lines)
   - blank line
   - `assistant: ` + full final response (may span multiple lines, code blocks stay inline)
   - blank line
   - `-=-=-==--=--=`
   - blank line before next set
5. **Bottom divider** — 60 `=` characters

---

## File Naming Rules

**Pattern:** `YYYY-MM-DD_{slug}_chat.md`

| Component | Source | Example |
|-----------|--------|---------|
| `YYYY-MM-DD` | `created_at` → ISO parse → `%Y-%m-%d` | `2025-06-11` |
| `{slug}` | `name` field → lowercased → spaces→underscores → stripped special chars | `sublime_text_column_selection` |
| `_chat.md` | Fixed suffix | always `_chat.md` |

**Collision handling:** If two chats share the same date and title slug, the second one gets `_001`, `_002`, etc. appended to the slug:

```
2025-06-15_document_processing_instructions_chat.md
2025-06-15_document_processing_instructions_001_chat.md
```

**Output location:** Always flat in `~/peacock/aichats/claude/` — no sub-folders.

---

## API Reference

### `parse_claude(source_path: str) -> Dict[str, str]`

**Args:**
- `source_path` — Path to a Claude JSON file (string or Path-like).

**Returns:**
- `Dict[str, str]` mapping `filename → markdown_content` for every conversation that had at least one message pair.

**Side effects:**
- Creates `~/peacock/aichats/claude/` if it doesn't exist.
- Writes one `.md` file per non-empty conversation.

**Raises:**
- `FileNotFoundError` — source file does not exist.
- `ValueError` — source file is empty or has unsupported JSON structure.

### `OUTPUT_ROOT`

Class-level constant pointing to `~/peacock/aichats/claude/`.

---

## How It Works Internally

### Step 1 — Load JSON

```
conversations.json → json.loads() → List[dict] or dict
```

If top-level is a list, each element is treated as one conversation.  
If top-level is a dict, it's treated as a single conversation.

### Step 2 — Extract metadata per conversation

```python
date_str  = _extract_date(chat)      # from created_at / updated_at / create_time / timestamp
slug      = _make_slug(chat_name)    # sanitize title
slug      = _disambiguate_slug(...)  # append _001 if collision
```

### Step 3 — Parse messages into Sets

```python
for msg in chat_messages:
    if sender == "human":
        current_user = extract_text(msg)
    elif sender == "assistant":
        sets.append({
            "set_num": N,
            "user": current_user,
            "assistant": extract_text(msg)   # ONLY type="text" blocks kept
        })
```

**Important:** `_extract_text()` intentionally filters the `content` array:

| Block type | Kept? | Reason |
|------------|-------|--------|
| `text` | ✅ Yes | Final delivered message |
| `tool_use` | ❌ No | Internal tool call — not part of conversation |
| `tool_result` | ❌ No | Raw tool output — not part of conversation |
| `thinking` | ❌ No | Internal reasoning — stripped per spec |
| `token_budget` | ❌ No | Metadata |
| `voice_note` | ❌ No | Attachment |

If a message has multiple `text` blocks interleaved with tools, only the `text` blocks are concatenated.

### Step 4 — Render markdown

```python
_generate_chat_md(chat_name, sets, date_str)
```

Builds the exact template described in [Output Format](#output-format).

### Step 5 — Write to disk

```python
out_path = OUTPUT_ROOT / f"{date_str}_{slug}_chat.md"
out_path.write_text(content, encoding="utf-8")
```

---

## Edge Cases & Behaviour

| Scenario | Behaviour |
|----------|-----------|
| Empty conversation (0 messages) | Skipped entirely — no file written. |
| Conversation with only user messages (no assistant reply) | Skipped — requires at least one user→assistant pair to form a Set. |
| Multiple `text` blocks in one assistant message | Concatenated in order. Tool blocks between them are dropped, so only the final delivered text remains. |
| Missing `created_at` | Falls back to `updated_at` → `create_time` → `timestamp` → today's date. |
| Missing `name` / `title` | Defaults to `"Untitled"`. |
| Chat title has special characters | Stripped; only letters, numbers, underscores, and hyphens survive. Spaces become underscores. |
| Same title, same date | Second file gets `_001` suffix in slug. Third gets `_002`, etc. |
| Very large `conversations.json` | Parsed streaming-style via `json.loads()`; memory usage equals file size. 512-conversation test file (~140 MB) processes in ~2 seconds. |

---

## Troubleshooting

### "Source file not found"

Check the path. The default test path is `/home/flintx/ai-chats/claude/conversations.json`.

### "Unsupported JSON structure"

The parser expects either:
- A JSON array of conversation objects, or
- A single JSON object with `chat_messages` or `messages`

If your export has a different top-level shape, inspect it with:

```bash
python3 -c "import json; d=json.load(open('file.json')); print(type(d))"
```

### Output files have `_001` when they shouldn't

This means a file with the same date+slug already exists in `~/peacock/aichats/claude/`. Delete old files and re-run:

```bash
rm ~/peacock/aichats/claude/*.md
python3 /home/flintx/.kimi/skills/chora/parsers/claude_parser.py
```

### Assistant text seems cut off

The parser only keeps `type: "text"` blocks. If Claude's response included tool calls without trailing text, the final tool result is not included (it's a `tool_result` block, not text). This is by design — the output is the **conversation**, not the **tool execution log**.

---

## Integration with Other Parsers

This parser follows the same conventions as the other Chora parsers:

| Parser | Output dir | Suffix | Sets style |
|--------|-----------|--------|------------|
| `kimi_og_parser.py` | `~/peacock/aichats/kimi-og/` | `_chat.md` | `### Set N` with tool details |
| `kimi_code_parser.py` | `~/peacock/aichats/kimi-code/` | `_chat.md` | `## Turn N` with action links |
| `claude_parser.py` | `~/peacock/aichats/claude/` | `_chat.md` | `=== Set N ===` raw conversation |

All write flat (no sub-folders) and use `YYYY-MM-DD_slug_chat.md` naming.

---

*Last updated: 2026-06-01*
