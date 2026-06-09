# AI Studio Chat Parser — How-To & Reference

> **File:** `parsers/aistudio_parser.py`  
> **Purpose:** Convert Google AI Studio JSON chat exports into clean, cross-referenced Markdown transcripts  
> **Output root:** `~/peacock/aichats/aistudio/`

---

## 1. What This Parser Does

AI Studio (Google's Gemini playground) exports chats as **extensionless JSON files**. Each file contains the full conversation history in a proprietary chunked format. This parser reads those raw exports and produces **two linked Markdown files per chat**:

| File | Purpose |
|------|---------|
| `_chat.md` | The full conversation — user messages + assistant responses only (no reasoning noise) |
| `_think.md` | The model's internal reasoning/thinking blocks, numbered by Set |

**Key feature:** AI Studio separates model reasoning ("thinking") from the final response into distinct JSON chunks. The parser correctly splits these so that `_chat.md` contains only what the user actually sees, while `_think.md` preserves the model's chain-of-thought for analysis.

---

## 2. Running the Parser

### 2.1 Single File

```bash
cd /home/flintx/.kimi/skills/chora
python3 parsers/aistudio_parser.py "/path/to/your/ai-studio-chat-file"
```

**Example:**
```bash
python3 parsers/aistudio_parser.py \
  "/home/flintx/ai-chats/aistudio/accounts/you@gmail.com/chat-logs/01.19.26-diving.deep.into.data.architecture-01.19"
```

**Output:**
```
✅ Generated folder: /home/flintx/peacock/aichats/aistudio/2026-01-19_diving_deep_into_data_architecture
```

### 2.2 Batch Process All Accounts

```bash
cd /home/flintx/.kimi/skills/chora
python3 scripts/batch_aistudio.py
```

This walks every `accounts/<email>/chat-logs/` directory and processes every file. Progress prints every 100 files.

### 2.3 From Python Code

```python
from parsers.aistudio_parser import parse_aistudio
from pathlib import Path

folder = parse_aistudio("/path/to/chat-file")
print(f"Output: {folder}")
# -> ~/peacock/aichats/aistudio/2026-01-19_slug_name
```

**Returns:** `pathlib.Path` pointing to the generated folder.

---

## 3. Output Format

### 3.1 Folder Structure

```
~/peacock/aichats/aistudio/
└── 2026-01-19_diving_deep_into_data_architecture/
    ├── 2026-01-19_diving_deep_into_data_architecture_chat.md
    └── 2026-01-19_diving_deep_into_data_architecture_think.md
```

**Naming rules:**
- Folder + files: `YYYY-MM-DD_slug`
- Slug comes from the chat title (JSON `title` field) or falls back to the filename
- If a folder already exists, disambiguation appends `_001`, `_002`, etc.

### 3.2 `_chat.md` Format

```markdown
# slug_name

*57 sets · 2026-01-19*

============================================================

=== Set 1 ===
user: whats good. ?

look at this chat.

[Image attached: photo.png]
assistant: Yo, what's real, Architect? I hear you loud and clear...
-=-=-==--=--=

=== Set 2 ===
user: i need to fix my ezenv...
assistant: Bet, Architect. If **ezenv** is actin' "bootise," we gotta strip the system down...
-=-=-==--=--=

...

============================================================
```

**Format rules:**
- `=== Set N ===` — turn delimiter
- `user:` — user message (may include `[Image attached: filename]` lines)
- `assistant:` — model's final response ONLY (thinking removed)
- `-=-=-==--=--=` — set separator
- Code blocks stay embedded in assistant text (not extracted)

### 3.3 `_think.md` Format

```markdown
=== Think Set 1 ===
**Reviewing The Chat Log**

Okay, so I'm diving into this chat log about building "ezenv"...

**Adopting A Hustler Mindset**

Alright, Architect, I'm digging deeper, channeling that streetwise hustler vibe...

=== Think Set 2 ===
**Assessing The Situation**

I'm deep in thought, focusing on the persona: Matthew Trevino...
```

**Format rules:**
- Only sets that actually contain thinking are written
- Numbered by Set to cross-reference with `_chat.md`
- Thinking blocks appear in the order they were generated

---

## 4. How It Works (Internal Architecture)

### 4.1 Input: AI Studio JSON Structure

AI Studio exports use a `chunkedPrompt` format. A conversation is an array of **chunks**, each with:

```json
{
  "chunkedPrompt": {
    "chunks": [
      {
        "role": "user",
        "text": "whats good. ?"
      },
      {
        "role": "model",
        "isThought": true,
        "thinkingBudget": -1,
        "parts": [
          {"text": "**Reviewing The Chat Log**\n\nOkay, so I'm diving...", "thought": true}
        ],
        "text": "**Reviewing The Chat Log**\n\nOkay, so I'm diving..."
      },
      {
        "role": "model",
        "parts": [
          {"text": "Yo, what's real, Architect? I hear you loud..."}
        ],
        "text": "Yo, what's real, Architect? I hear you loud..."
      }
    ]
  }
}
```

**Critical insight:** AI Studio splits every model turn into **two chunks**:
1. `isThought: true` — the model's internal reasoning (not shown to user)
2. `isThought: null/false` — the final response (shown to user)

The parser merges both chunks into a single "Set" but routes the text to different fields.

### 4.2 Parsing Pipeline

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Read JSON file │────▶│  Detect format  │────▶│  Parse chunks   │
│                 │     │  (dict or list) │     │  into Sets      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                         │
                              ┌──────────────────────────┘
                              ▼
                    ┌─────────────────┐
                    │  For each chunk │
                    │  - user → store │
                    │  - model think  │
                    │  - model reply  │
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Write _chat.md │
                    │  Write _think.md│
                    └─────────────────┘
```

### 4.3 Supported Input Formats

The parser handles **three shapes** of AI Studio exports:

| Shape | Structure | When it appears |
|-------|-----------|-----------------|
| **Standard** | `{"chunkedPrompt": {"chunks": [...]}}` | Most AI Studio exports |
| **List** | `[{"messages": [{"role": "...", "content": "..."}]}]` | Some test/legacy exports |
| **Extra data** | Multiple JSON objects concatenated in one file | Rare export edge case |

### 4.4 Date Extraction

Dates are extracted in this priority order:

1. **Filename prefix** — `MM.DD.YY-...` (AI Studio standard)
   - Year pivot: `yy < 70` → `2000+yy`, else `1900+yy`
2. **Generic patterns** — `YYYY-MM-DD`, `YYYY_MM_DD`, `YYYYMMDD` anywhere in filename
3. **File mtime** — filesystem modification time
4. **Today** — fallback (rarely hits)

### 4.5 Title Extraction

1. JSON `title` field (if present)
2. Filename with date prefix/suffix stripped:
   - Strip leading `MM.DD.YY-`
   - Strip trailing `-MM.DD`, `-DD`, `_N`
   - Convert `.` and `_` to spaces
3. Fallback: `"Untitled"`

---

## 5. File Reference

### 5.1 `parsers/aistudio_parser.py`

| Function | Purpose |
|----------|---------|
| `parse_aistudio(source_path)` | **Main entry point.** Reads JSON, parses, writes folder + 2 files. Returns `Path` to folder. |
| `_parse_chunks(raw_data)` | Parses standard `chunkedPrompt` format. Handles `isThought` splitting. |
| `_parse_messages_format(raw_data)` | Parses list-shaped JSON with `messages` array. |
| `_generate_chat_md(slug, date_str, sets)` | Renders `_chat.md` with strict Set format. |
| `_generate_think_md(sets)` | Renders `_think.md` with numbered thinking blocks. |
| `_extract_date(source_path)` | Extracts best date from filename or mtime. |
| `_extract_title(source_path, raw_data)` | Extracts chat title from JSON or filename. |
| `_make_slug(name)` | Sanitizes title into filesystem-safe slug. |
| `_disambiguate_slug(...)` | Appends `_001`, `_002` if folder already exists. |

### 5.2 `scripts/batch_aistudio.py`

Simple batch driver that:
1. Scans `~/ai-chats/aistudio/accounts/*/chat-logs/`
2. Calls `parse_aistudio()` on every file
3. Prints progress every 100 files
4. Reports success/failure count with error samples

---

## 6. Error Handling

The parser raises `ValueError` for these conditions (callers should catch and skip):

| Error | Cause |
|-------|-------|
| `"Source file is empty"` | File has zero bytes |
| `"Source file is not valid JSON"` | File is not parseable JSON (e.g., image, PDF, text) |
| `"Unsupported JSON structure"` | JSON is neither a dict nor a list |
| `"No conversation sets found in source file"` | Valid JSON but no user/model chunks |

**Important:** The parser creates the output folder **only after** successful JSON parsing. Failed files do NOT leave empty folders behind.

---

## 7. Typical Failure Types

When batch-processing, expect some failures. These are **normal** and should be skipped:

| File type | Why it fails |
|-----------|--------------|
| `.png`, `.jpg` | Images exported alongside chats — not JSON |
| `.pdf` | PDF attachments — not JSON |
| `.mp4` | Video attachments — not JSON |
| `.txt`, `.md` | Plain text notes — not JSON |
| Git refs | Files like `HEAD`, `master` from git repos — not JSON |
| Empty prompts | Files with no conversation data — no sets found |

---

## 8. Customizing Output Location

Edit `OUTPUT_ROOT` in `parsers/aistudio_parser.py`:

```python
# Default:
OUTPUT_ROOT = Path.home() / "peacock" / "aichats" / "aistudio"

# Custom:
OUTPUT_ROOT = Path("/your/custom/path")
```

---

## 9. Cross-Referencing Chat ↔ Think

Both files use the same **Set numbering**:

- `_chat.md`: `=== Set 7 ===`
- `_think.md`: `=== Think Set 7 ===`

If a Set has no thinking, it simply doesn't appear in `_think.md`. The numbers are always in sync.

---

## 10. Requirements

- Python 3.10+
- Standard library only (`json`, `os`, `re`, `datetime`, `pathlib`, `typing`)
- No external dependencies

---

## 11. Quick Start Checklist

```bash
# 1. Navigate to project
cd /home/flintx/.kimi/skills/chora

# 2. Process a single chat
python3 parsers/aistudio_parser.py \
  "/home/flintx/ai-chats/aistudio/accounts/you@gmail.com/chat-logs/01.19.26-your-chat-name-01.19"

# 3. Or batch-process everything
python3 scripts/batch_aistudio.py

# 4. Check output
ls ~/peacock/aichats/aistudio/
```
