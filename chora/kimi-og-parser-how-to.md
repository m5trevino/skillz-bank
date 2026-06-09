# Kimi-OG Session Parser — How-To & Reference

> **File:** `parsers/kimi_og_parser.py`  
> **Purpose:** Parse Kimi OG (original Kimi CLI) session directories into clean, correlated chat + think markdown files.  
> **Output base:** `~/peacock/aichats/kimi-og/`

---

## Table of Contents

1. [What It Does](#what-it-does)
2. [Input: Kimi OG Session Structure](#input-kimi-og-session-structure)
3. [Output: Per-Session Directory Layout](#output-per-session-directory-layout)
4. [How to Run](#how-to-run)
5. [The Empty-Session Filter](#the-empty-session-filter)
6. [How It Works Internally](#how-it-works-internally)
7. [File Format Reference](#file-format-reference)
8. [Edge Cases & Behavior](#edge-cases--behavior)
9. [For Developers / Agent Integration](#for-developers--agent-integration)

---

## What It Does

This parser reads raw Kimi OG CLI session data and converts it into **human-readable, correlated markdown transcripts**.

**Key features:**
- Strips system prompts, checkpoints, tool calls, and meta-text
- Separates **conversation** (`_chat.md`) from **internal thinking** (`_think.md`)
- Numbers every turn so `Set N` in chat directly correlates with `Think Set N` in think
- Skips empty/junk sessions (no assistant replies, system-only, etc.)
- Names output directories by date + sanitized title
- Falls back to `wire.jsonl` for thinking blocks when `context.jsonl` lacks them

---

## Input: Kimi OG Session Structure

Kimi OG stores sessions at:

```
~/.kimi/sessions/
└── <session_hash>/              ← 32-char hex (project/workspace level)
    └── <conversation_uuid>/     ← UUID (individual chat session)
        ├── state.json           ← metadata (title, timestamps)
        ├── context.jsonl        ← PRIMARY conversation log
        ├── wire.jsonl           ← protocol events (backup)
        └── uploads/             ← attached images/documents
```

### `state.json` — Metadata

```json
{
  "custom_title": "my chat about python",
  "createdAt": 1776055800.845,
  "archived_at": 1778180286.973,
  "wire_mtime": 1773729927.87
}
```

**Fields used by parser:**
| Field | Purpose | Fallback if missing |
|-------|---------|---------------------|
| `custom_title` | Session name for slug | `title` → directory name |
| `createdAt` | Date for `YYYY-MM-DD` prefix | `wire_mtime` → `archived_at` → file mtime |

### `context.jsonl` — Primary Conversation Log

Each line is a JSON object with a `role` field:

```jsonl
{"role": "user", "content": "Hello, write hello world"}
{"role": "assistant", "content": [{"type": "think", "think": "The user wants..."}, {"type": "text", "text": "Sure!"}]}
{"role": "user", "content": "Thanks"}
{"role": "assistant", "content": [{"type": "text", "text": "You're welcome!"}]}
```

**Roles handled:**
| Role | Action |
|------|--------|
| `user` | Preserved in chat. Skipped if `<system>` tagged. |
| `assistant` | `text` parts → chat. `think` parts → think file. |
| `tool` | **Skipped entirely** — not part of conversation. |
| `_system_prompt` | **Skipped entirely** — meta role. |
| `_checkpoint` | **Skipped entirely** — meta role. |

### `wire.jsonl` — Protocol Backup

Rich protocol log with `TurnBegin`, `ContentPart`, `ToolCall`, `ToolResult`, `TurnEnd` events. Used as backup for thinking blocks when `context.jsonl` doesn't capture them.

---

## Output: Per-Session Directory Layout

Each session becomes one directory with exactly **two files**:

```
~/peacock/aichats/kimi-og/
└── 2026-05-07_why_cant_i_find_the_init_skillls_or_the/
    ├── 2026-05-07_why_cant_i_find_the_init_skillls_or_the_chat.md
    └── 2026-05-07_why_cant_i_find_the_init_skillls_or_the_think.md
```

**Naming formula:**
```
YYYY-MM-DD_<sanitized_title>/
├── YYYY-MM-DD_<sanitized_title>_chat.md
└── YYYY-MM-DD_<sanitized_title>_think.md
```

- `YYYY-MM-DD` from best available timestamp (see state.json section)
- Title sanitized: lowercase, spaces → underscores, special chars stripped
- Max slug length: 80 characters

---

## How to Run

### Single Session

```bash
cd /home/flintx/.kimi/skills/chora
python3 parsers/kimi_og_parser.py ~/.kimi/sessions/<hash>/<uuid>
```

Or via Python import:

```python
from parsers.kimi_og_parser import parse_kimi_og

result = parse_kimi_og("~/.kimi/sessions/<hash>/<uuid>")
print(result["chat"])   # Path to _chat.md
print(result["think"])  # Path to _think.md
print(result["dir"])    # Path to parent directory
```

### Batch Process All Sessions

```python
from pathlib import Path
from parsers.kimi_og_parser import parse_kimi_og, is_worth_parsing

root = Path.home() / ".kimi" / "sessions"

for hash_dir in root.iterdir():
    if not hash_dir.is_dir():
        continue
    for session_dir in hash_dir.iterdir():
        if not session_dir.is_dir():
            continue
        if not is_worth_parsing(session_dir):
            continue  # Skip empty sessions
        try:
            result = parse_kimi_og(str(session_dir))
            print(f"OK: {result['dir'].name}")
        except Exception as e:
            print(f"ERR: {session_dir.name}: {e}")
```

---

## The Empty-Session Filter

Before any output is created, the parser checks `is_worth_parsing(session_dir)`. A session is **skipped** if ANY of these are true:

| Condition | Reason |
|-----------|--------|
| No `context.jsonl` or `context_1.jsonl` | No data to parse |
| Zero `role: "assistant"` messages | AI never replied — empty or system-only |
| Zero `role: "user"` messages | No human input |

**Early exit optimization:** The filter stops reading as soon as it finds ≥1 user + ≥1 assistant message.

**Statistics from real run:**
- 206 total sessions scanned
- 137 passed filter (66.5% — real conversations)
- 69 skipped (33.5% — empty/junk)

---

## How It Works Internally

### Pipeline Flow

```
1. is_worth_parsing()          ← Fast scan of context.jsonl
   └─ SKIP if no assistant msg

2. parse_kimi_og(source_path)
   ├─ Load state.json          ← Get title + date
   ├─ Load context.jsonl       ← PRIMARY source
   ├─ Load wire.jsonl          ← BACKUP for thinking
   ├─ _parse_context_jsonl()   ← Build chat_sets + think_sets
   ├─ _parse_wire_thinking()   ← Merge missing think blocks
   ├─ _write_chat_md()         ← Write _chat.md
   └─ _write_think_md()        ← Write _think.md
```

### Step-by-Step

**Step 1 — `is_worth_parsing()`**
Opens `context.jsonl`, streams line by line, counts `assistant` and `user` roles. Returns `False` immediately if no assistant found.

**Step 2 — `_parse_context_jsonl()`**
Walks every entry in `context.jsonl`:
- `user` role → starts a new Set. Text extracted via `_extract_user_content()`.
- `assistant` role → appends `text` parts to current Set's assistant field, appends `think` parts to think buffer.
- `tool` / `_system_prompt` / `_checkpoint` → skipped.
- `<system>` tagged user messages → skipped.

**Step 3 — `_parse_wire_thinking()`**
Parses `wire.jsonl` for `ContentPart` events with `type: "think"`. Indexes thinking by turn number. If a Set has empty thinking after Step 2, the wire thinking is merged in.

**Step 4 — `_write_chat_md()`**
Writes header + one block per Set:
```
=== Set N ===
user: <raw user message>

assistant: <final assistant text (no think blocks)>

-=-=-==--=--=
```

**Step 5 — `_write_think_md()`**
Writes one block per Set:
```
=== Think Set N ===
<all thinking text for this Set>
```
If no thinking: writes `[no thinking recorded]`.

---

## File Format Reference

### `_chat.md`

```markdown
# my chat about python

> 12 sets · 2026-05-07
============================================================

=== Set 1 ===
user: Hello, can you write hello world in Python?

assistant: Sure! Here's a simple hello world:

```python
print("Hello, world!")
```

-=-=-==--=--=

=== Set 2 ===
user: Thanks!

assistant: You're welcome! Let me know if you need anything else.

-=-=-==--=--=
```

**Rules:**
- Only `user:` and `assistant:` lines
- Assistant text includes ONLY `type: "text"` parts
- `type: "think"` parts are **never** in chat
- Tool calls, tool results, system prompts are **never** in chat
- Separator `-=-=-==--=--=` after every Set

### `_think.md`

```markdown
=== Think Set 1 ===
The user wants a hello world script. I'll use WriteFile to create it.

=== Think Set 2 ===
The user said thanks. I should respond politely and offer further help.

=== Think Set 3 ===
[no thinking recorded]
```

**Rules:**
- Numbered to correlate with `Set N` in chat
- All `think` parts from assistant messages concatenated
- Wire protocol thinking merged when context has none
- Empty think Sets show `[no thinking recorded]`

---

## Edge Cases & Behavior

| Scenario | Behavior |
|----------|----------|
| No `state.json` | Uses directory name as title, file mtime as date |
| `custom_title` is `null` | Falls back to `title` → directory name |
| `context.jsonl` missing | Tries `context_1.jsonl`, then errors |
| `wire.jsonl` missing | Skips wire backup, thinks may be empty |
| Same date + same slug | Last write wins (overwrites previous) |
| Empty think blocks | Writes `[no thinking recorded]` |
| User message is array with image | Text preserved, image noted as `[Image: ...]` |
| Assistant has think but no text | `assistant:` line is empty string |
| System-tagged user msg (`<system>`) | Skipped entirely |

---

## For Developers / Agent Integration

### Exported API

```python
# Main entry point
parse_kimi_og(source_path: str) -> Dict[str, Path]
# Returns: {"dir": Path, "chat": Path, "think": Path}

# Filter check (use before parse_kimi_og to skip junk)
is_worth_parsing(session_dir: Path) -> bool
```

### Adding to Another Pipeline

```python
from parsers.kimi_og_parser import parse_kimi_og, is_worth_parsing
from pathlib import Path

def process_all_kimi_sessions(output_callback):
    root = Path.home() / ".kimi" / "sessions"
    for hash_dir in root.iterdir():
        for session_dir in hash_dir.iterdir():
            if not is_worth_parsing(session_dir):
                continue
            result = parse_kimi_og(str(session_dir))
            output_callback(result["chat"], result["think"])
```

### Return Value Structure

```python
{
    "dir":  Path("~/peacock/aichats/kimi-og/2026-05-07_my_chat"),
    "chat": Path("~/peacock/aichats/kimi-og/2026-05-07_my_chat/2026-05-07_my_chat_chat.md"),
    "think": Path("~/peacock/aichats/kimi-og/2026-05-07_my_chat/2026-05-07_my_chat_think.md"),
}
```

---

## File Location

```
/home/flintx/.kimi/skills/chora/parsers/kimi_og_parser.py
```

Requires Python 3.8+ with standard library only (`json`, `re`, `pathlib`, `datetime`, `typing`).
