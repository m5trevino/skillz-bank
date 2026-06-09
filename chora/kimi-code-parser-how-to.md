# Kimi-Code Parser — How-To & Reference

> **Location:** `~/.kimi/skills/chora/parsers/kimi_code_parser.py`
> **Purpose:** Parse Kimi-Code (new Kimi CLI) session transcripts into clean, human-readable markdown.
> **Output:** Per-session directories containing `_chat.md` + `_think.md`

---

## Table of Contents

1. [What It Does](#what-it-does)
2. [Input: Kimi-Code Sessions](#input-kimi-code-sessions)
3. [Output Format](#output-format)
4. [How to Run It](#how-to-run-it)
5. [How It Works Internally](#how-it-works-internally)
6. [The Empty-Session Filter](#the-empty-session-filter)
7. [Batch Processing All Sessions](#batch-processing-all-sessions)
8. [Troubleshooting](#troubleshooting)

---

## What It Does

This parser reads Kimi-Code CLI session data and produces **two clean markdown files** per session:

| File | Content | What's Removed |
|------|---------|----------------|
| `_chat.md` | Raw conversation (user + assistant) | Think blocks, tool calls, system meta, JSON noise |
| `_think.md` | All assistant thinking blocks | Everything else |

**Key features:**
- Handles **both old and new** Kimi-Code wire protocols
- **Correlates** chat Sets with Think Sets by number (`Set 1` ↔ `Think Set 1`)
- **Filters out junk** — skips empty sessions with no real tool activity
- **Auto-names** output directories using the session date + cleaned title from `state.json`
- **Zero external dependencies** — pure Python 3 standard library

---

## Input: Kimi-Code Sessions

### Where Sessions Live

```
~/.kimi-code/sessions/
├── wd_<project-name>_<hash>/        ← workdir-scoped sessions (most common)
│   └── ses_<uuid>/
│       ├── state.json
│       └── agents/
│           └── main/
│               └── wire.jsonl        ← THE PRIMARY EVENT LOG
│
└── ses_<uuid>/                       ← direct sessions (no workdir prefix)
    ├── state.json
    └── agents/
        └── main/
            └── wire.jsonl
```

### What the Parser Reads

| File | Purpose | Required? |
|------|---------|-----------|
| `state.json` | Session metadata: `title`, `createdAt`, `updatedAt` | Yes |
| `agents/main/wire.jsonl` | Line-by-line JSON event log (the actual conversation) | Yes |

#### `state.json` fields used

```json
{
  "createdAt": "2026-06-01T03:16:08.573Z",
  "updatedAt": "2026-06-01T04:01:12.875Z",
  "title": "Slice C1: Direct CLI Executable + Shebang ...",
  "isCustomTitle": false
}
```

- **`createdAt`** → used for the `YYYY-MM-DD` date in the output directory name
- **`title`** → used for the `slug` (cleaned, lowercased, spaces→underscores)

#### `wire.jsonl` event types handled

The parser recognizes these event types and ignores everything else:

| Event Type | Role | What It Contains |
|------------|------|------------------|
| `turn.prompt` | User | Raw user input in `input[].text` |
| `context.append_message` + `role: user` | User | Stored user message in `message.content[].text` |
| `context.append_message` + `role: assistant` | Assistant | Final response text + think blocks in `message.content[]` |
| `context.append_loop_event` + `content.part` | Assistant | Streaming text/think parts (newer protocol) |

**Ignored events:** `metadata`, `config.update`, `tools.set_active_tools`, `usage.record`, `permission.record_approval_result`, `tool.call`, `tool.result`, `step.begin`, `step.end`.

---

## Output Format

### Directory Structure

```
~/peacock/aichats/kimi-code/
├── 2026-06-01_slice_c1_direct_cli_executable/
│   ├── 2026-06-01_slice_c1_direct_cli_executable_chat.md
│   └── 2026-06-01_slice_c1_direct_cli_executable_think.md
│
├── 2026-05-27_what_up_what_did_we_all_get_done/
│   ├── 2026-05-27_what_up_what_did_we_all_get_done_chat.md
│   └── 2026-05-27_what_up_what_did_we_all_get_done_think.md
│
└── 2026-03-21_whats_good_001/          ← _001, _002 etc. for collisions
    ├── 2026-03-21_whats_good_001_chat.md
    └── 2026-03-21_whats_good_001_think.md
```

- **One directory per session**
- **Exactly 2 files per directory**
- Directory name: `YYYY-MM-DD_slug` (auto-disambiguated with `_001`, `_002` if same title+date)

### `_chat.md` Format

```markdown
# Slice C1: Direct CLI Executable + Shebang
> 3 sets · 2026-06-01
============================================================

=== Set 1 ===

user: Slice C1: Direct CLI Executable + Shebang
"Implement Slice C1 for Chora. Make chora.py directly runnable..."

assistant: Slice C1 implemented and verified. Here's what changed:

**1. Shebang + Direct Execution**
- `#!/usr/bin/env python3` was already present...

-=-=-==--=--=

=== Set 2 ===

user: Slice C2: Human Readable Output
"Slice C2 — Generate clean _human.md..."

assistant: Slice C2 implemented and verified. Here's what changed:
...
```

**Rules:**
- Header: `# [title from state.json]`
- Meta line: `> N sets · YYYY-MM-DD`
- Separator: `=` × 60
- Each set: `=== Set N ===`, `user:`, `assistant:`
- Between sets: `-=-=-==--=--=`
- **No think blocks, no tool calls, no system messages, no JSON**

### `_think.md` Format

```markdown
=== Think Set 1 ===

The user wants me to implement Slice C1 for the Chora skill. Let me first understand the current state of the project by reading the existing files.

I need to:
1. Read the existing SKILL.md...

=== Think Set 2 ===

The user wants Slice C2: improve the `_human.md` output to be a single beautifully formatted markdown file...
```

**Rules:**
- Each block: `=== Think Set N ===`
- Contains **only** the assistant's internal reasoning
- `(no thinking recorded)` if a set had no think blocks
- **Correlates by number** with `_chat.md` (`Think Set 1` ↔ `Set 1`)

---

## How to Run It

### Method 1: Python Import (Recommended)

```python
from pathlib import Path
from parsers.kimi_code_parser import parse_kimi_code

# Parse a single session
session_dir = Path.home() / ".kimi-code" / "sessions" / "wd_chora_0ab6de30ad45" / "session_2b1fd6d7-..."

chat_path, think_path = parse_kimi_code(session_dir)

print(f"Chat:  {chat_path}")
print(f"Think: {think_path}")
```

**Optional: Custom output directory**

```python
output_root = Path.home() / "my-archive" / "kimi-code"
chat_path, think_path = parse_kimi_code(session_dir, output_dir=output_root)
```

**Handling the empty-session filter**

```python
try:
    chat_path, think_path = parse_kimi_code(session_dir)
except RuntimeError as e:
    if "SESSION_EMPTY" in str(e):
        print("Session has no real work — skipped silently.")
    else:
        raise
```

### Method 2: CLI

```bash
cd ~/.kimi/skills/chora

# Parse one session
python3 parsers/kimi_code_parser.py ~/.kimi-code/sessions/wd_chora_0ab6de30ad45/session_2b1fd6d7-...

# Parse with custom output root
python3 parsers/kimi_code_parser.py ~/.kimi-code/sessions/ses_466cb7d4-... ~/my-archive/kimi-code
```

### Method 3: Batch Script (Process ALL Sessions)

```python
#!/usr/bin/env python3
"""Batch-process every Kimi-Code session."""
import sys
from pathlib import Path

# Add the project to path
sys.path.insert(0, str(Path.home() / ".kimi" / "skills" / "chora"))

from parsers.kimi_code_parser import parse_kimi_code, is_meaningful_session

root = Path.home() / ".kimi-code" / "sessions"
wire_paths = list(root.rglob("agents/*/wire.jsonl"))

total = len(wire_paths)
skipped = 0
kept = 0
failed = 0

for wire_path in wire_paths:
    session_dir = wire_path.parents[2]  # wire.jsonl → main → agents → session_dir

    # Filter: skip empty/junk sessions
    if not is_meaningful_session(wire_path):
        skipped += 1
        continue

    try:
        chat, think = parse_kimi_code(session_dir)
        kept += 1
    except Exception as e:
        failed += 1
        print(f"  ❌ {session_dir.name}: {e}")

print(f"📊 Done: {total} total | {skipped} skipped | {kept} processed | {failed} failed")
```

Run it:
```bash
python3 batch_kimicode.py
```

---

## How It Works Internally

### 1. Discovery

```
session_dir/
├── state.json              ← read for title + date
└── agents/
    └── main/
        └── wire.jsonl      ← read line-by-line (JSONL)
```

### 2. The Wire Parser (`parse_kimicode_wire_jsonl`)

Reads every line of `wire.jsonl` as JSON and categorizes events:

```
turn.prompt              → user message (start new Set)
context.append_message   →
  role=user              → user message (start new Set)
  role=assistant         → assistant text + think blocks
  role=tool              → IGNORED (clean output)
context.append_loop_event→
  content.part type=text → assistant text (streaming)
  content.part type=think→ think blocks (streaming)
  tool.call              → IGNORED
  tool.result            → IGNORED
  step.begin/end         → IGNORED
```

**Deduplication logic:** Some sessions emit assistant content in **both** `context.append_message` (old protocol) and `context.append_loop_event` (new protocol). The parser tracks `msg_level_text` / `msg_level_think` and skips loop-event content that is already contained in the message-level content.

### 3. State Extraction

| Source | Field | Fallback |
|--------|-------|----------|
| Date | `state.json` → `createdAt` | Directory mtime |
| Title | `state.json` → `title` | `"Untitled"` |
| Slug | Cleaned title (lower, `[^\w\s-]` stripped, spaces→`_`) | Session UUID first 8 chars |

### 4. File Naming

```
YYYY-MM-DD = from state.json createdAt (ISO 8601 parsed)
slug       = cleaned title, max 60 chars, trailing _ stripped

directory:  ~/peacock/aichats/kimi-code/YYYY-MM-DD_slug/
chat file:  YYYY-MM-DD_slug_chat.md
think file: YYYY-MM-DD_slug_think.md
```

If `YYYY-MM-DD_slug` already exists, auto-increment: `YYYY-MM-DD_slug_001`, `_002`, etc.

### 5. Markdown Generation

Two generators produce the final files:

- `generate_chat_md(sets, title, date_str)` → `_chat.md`
- `generate_think_md(sets)` → `_think.md`

Both iterate over the same `List[Set]` so the numbering is guaranteed to match.

---

## The Empty-Session Filter

### Why It Exists

About **25% of Kimi-Code sessions** are empty or near-empty:
- `"whats up"` → `"not much"` (no files touched)
- Single paste with no assistant response
- Pure metadata lines (≤5 lines total)

Creating dated directories for these wastes space and pollutes the archive.

### The Filter Function

```python
is_meaningful_session(wire_jsonl_path, min_lines=6, require_tools=True)
```

**Skip conditions (ANY true → skip):**

| Condition | Default | What It Catches |
|-----------|---------|-----------------|
| `lines < min_lines` | `lines < 6` | Metadata-only sessions (2–5 lines) |
| `require_tools and not has_tools` | no tool calls | Pure chat sessions |

**Tool detection checks BOTH protocols:**
- New: `context.append_loop_event` with `event.type == "tool.call"`
- Old: `context.append_message` with `message.role == "tool"`

### Three Strictness Presets

```python
# 1. LENIENT — skips only the 60 truly dead sessions
is_meaningful_session(wire_path, min_lines=6, require_tools=False)

# 2. RECOMMENDED — skips 61 sessions (60 dead + 1 chat-only)
#    Keeps 184 sessions where assistant actually DID something
is_meaningful_session(wire_path, min_lines=6, require_tools=True)

# 3. STRICT — only substantial multi-turn work
#    Skips 69 sessions, keeps 176
is_meaningful_session(wire_path, min_lines=10, require_tools=True)
```

The parser uses **RECOMMENDED** (`min_lines=6, require_tools=True`) by default.

---

## Batch Processing All Sessions

### Quick One-Liner

```bash
cd ~/.kimi/skills/chora && python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from parsers.kimi_code_parser import parse_kimi_code, is_meaningful_session

root = Path.home() / '.kimi-code' / 'sessions'
wire_paths = list(root.rglob('agents/*/wire.jsonl'))

skipped = kept = 0
for wp in wire_paths:
    sd = wp.parents[2]
    if not is_meaningful_session(wp):
        skipped += 1
        continue
    parse_kimi_code(sd)
    kept += 1

print(f'Done: {len(wire_paths)} total | {skipped} skipped | {kept} processed')
"
```

### Expected Output

```
Done: 245 total | 62 skipped | 183 processed
```

Resulting structure:
```
~/peacock/aichats/kimi-code/
├── 2026-03-19_social_lube/
├── 2026-03-21_trevino_war_room/
├── 2026-04-10_deep_dive_documentation_skill_version_1/
├── 2026-04-10_deep_dive_documentation_skill_version_1_001/
├── 2026-04-10_deep_dive_documentation_skill_version_1_002/
...
```

---

## Troubleshooting

### `FileNotFoundError: No Kimi-Code wire.jsonl found`

The session directory doesn't contain `agents/main/wire.jsonl`. Check:
```bash
ls ~/.kimi-code/sessions/<session-id>/agents/main/
```

### `RuntimeError: SESSION_EMPTY`

The session passed the wire.jsonl existence check but failed the meaningful-session filter. It has ≤5 lines or zero tool calls. This is normal — about 25% of sessions are junk.

### Duplicate directories (`_001`, `_002`)

Two sessions on the same date have the same title (or the title slug collides). The parser auto-increments the directory suffix. This is expected and harmless.

### Missing `state.json`

If `state.json` is missing, the parser falls back to:
- Date: directory mtime
- Title: `"Untitled"`
- Slug: first 8 chars of the session UUID

### Assistant text is empty

Some sessions use only the **new protocol** where assistant text lives exclusively in `context.append_loop_event` `content.part` events. The parser handles this. If text is still missing, the wire file may be truncated or the session was aborted mid-turn.

---

## File Reference

| File | Purpose |
|------|---------|
| `parsers/kimi_code_parser.py` | The parser module (this doc) |
| `parsers/__init__.py` | Package init (empty, required for imports) |
| `~/peacock/aichats/kimi-code/` | Default output root |
| `~/.kimi-code/sessions/` | Default Kimi-Code sessions root |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-06-01 | Initial parser — 4-file chora format (`_chat.md`, `_code.md`, `_think.md`, `_human.md`) |
| 2026-06-01 | Rewritten to 2-file clean format (`_chat.md` + `_think.md`) with `=== Set N ===` correlation |
| 2026-06-01 | Added `is_meaningful_session` filter — skips ~25% empty/junk sessions |

---

*Last updated: 2026-06-01*
