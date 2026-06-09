---
name: chora
description: >-
  Wire-aware session transcript generator for Kimi CLI. Parses wire.jsonl
  (or falls back to context.jsonl) and produces four linked files:
  a chat log, a code/tool-actions log, a think-blocks log, and a
  human-readable transcript — all cross-referenced by T{turn}.A{action}
  IDs so a UI can link chat points to the exact code that was written
  or read at that moment.
triggers:
  - "chora"
  - "parse wire"
  - "wire transcript"
  - "session code log"
  - "chat code link"
  - "tool transcript"
  - "generate wire output"
---

# Chora — Wire-Aware Session Transcript

## What It Does

Chora reads a Kimi CLI session directory (or AI Studio, Kimi-Code, or Gemini CLI exports) and emits **four linked markdown files**:

| File | Suffix | Content |
|------|--------|---------|
| **Chat** | `_chat.md` | Full conversation. Each assistant turn ends with a line linking to the code actions that happened in that turn. |
| **Code** | `_code.md` | Every `ToolCall` + `ToolResult` from `wire.jsonl`: arguments, return values, diffs, file contents, shell output. For AI Studio and Gemini, markdown code blocks are extracted as pseudo-actions. |
| **Think** | `_think.md` | All `ContentPart` think blocks grouped by turn, with links to the turn's code actions. |
| **Human** | `_human.md` | Beautiful standalone-readable transcript with clean turn headers, think blocks, and smart code-snippet extraction. |

### Linking Format

All structured files share the same ID scheme:

- **Turn ID:** `T3` → Turn 3
- **Action ID:** `T3.A1` → Turn 3, Action 1

In the chat file:
```markdown
**🔗 Code Actions:** [T3.A1: StrReplaceFile](code.md#t3.a1) · [T3.A2: ReadFile](code.md#t3.a2)
```

In the code file:
```markdown
## <a name="t3.a1"></a>T3.A1 — Turn 3, Action 1 — `StrReplaceFile`
```

In the think file:
```markdown
## <a name="t3"></a>T3 — Turn 3

```
[think text]
```

**🔗 Code Actions:** [T3.A1: StrReplaceFile](code.md#t3.a1) · [T3.A2: ReadFile](code.md#t3.a2)
```

A UI can parse these anchors and links to jump from any chat turn to its code, or from a think block to the actions that followed it.

---

## Why Wire.jsonl?

`context.jsonl` only stores the assistant's **markdown text** (what the user sees). After compaction, even that can disappear.

`wire.jsonl` stores the **full protocol log**:
- Every `ToolCall` with exact JSON arguments
- Every `ToolResult` with full file contents, diffs, and shell output
- Every `ContentPart` think block
- Every `TurnBegin`/`TurnEnd` boundary

This means Chora can reconstruct the complete session history even when `context.jsonl` has been compacted or truncated.

---

## Usage

### Single session

```bash
# Interactive — pick from list
python3 ~/.kimi/skills/chora/scripts/chora.py

# Specific session
python3 ~/.kimi/skills/chora/scripts/chora.py --session-dir ~/.kimi/sessions/xxx/yyyy-yyyy-yyyy-yyyyyyyyyyyy

# Custom output directory
python3 ~/.kimi/skills/chora/scripts/chora.py --session-dir ~/.kimi/sessions/xxx/yyyy --output-dir ~/peacock/aichats

# Quick human-only mode (fast)
python3 ~/.kimi/skills/chora/scripts/chora.py --quick --session-dir ~/.kimi/sessions/xxx/yyyy
```

### Batch — all sessions

```bash
# Process every session once (skips up-to-date)
python3 ~/.kimi/skills/chora/scripts/chora.py --batch --output-dir ~/peacock/aichats

# Force re-process everything
python3 ~/.kimi/skills/chora/scripts/chora.py --batch --force --output-dir ~/peacock/aichats

# Quick batch — human-only for all sessions
python3 ~/.kimi/skills/chora/scripts/chora.py --batch --quick --output-dir ~/peacock/aichats
```

### AI Studio exports

Chora can parse Google AI Studio chat exports from `~/ai-chats/aistudio/`.

```bash
# Auto-detect AI Studio when inside ~/ai-chats/aistudio (or any subdir)
cd ~/ai-chats/aistudio
python3 ~/.kimi/skills/chora/scripts/chora.py --batch --output-dir ~/peacock/aichats

# Explicit AI Studio source mode
python3 ~/.kimi/skills/chora/scripts/chora.py --source aistudio --batch --output-dir ~/peacock/aichats

# Single AI Studio conversation file
python3 ~/.kimi/skills/chora/scripts/chora.py \
  --source aistudio \
  --session-dir ~/ai-chats/aistudio/accounts/my@gmail.com/chat-logs/my-chat \
  --output-dir ~/peacock/aichats
```

**AI Studio source discovery:**
1. `accounts/<gmail>/chat-logs/*` — extensionless JSON files (one conversation per file)

AI Studio mode extracts markdown code blocks from assistant responses and surfaces them as `CodeBlock` pseudo-actions in `_code.md`, so WALDO and other UIs can browse code snippets with the same T{turn}.A{action} linking.

### Kimi-Code new CLI sessions

Chora can parse Kimi-Code (new CLI) sessions from `~/.kimi-code/sessions/`.

```bash
# Auto-detect Kimi-Code when inside ~/.kimi-code/sessions (or any subdir)
cd ~/.kimi-code/sessions
python3 ~/.kimi/skills/chora/scripts/chora.py --batch --output-dir ~/peacock/aichats

# Explicit Kimi-Code source mode
python3 ~/.kimi/skills/chora/scripts/chora.py --source kimicode --batch --output-dir ~/peacock/aichats

# Single Kimi-Code session
python3 ~/.kimi/skills/chora/scripts/chora.py \
  --source kimicode \
  --session-dir ~/.kimi-code/sessions/ses_xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx \
  --output-dir ~/peacock/aichats
```

**Kimi-Code source discovery:**
1. `sessions/ses_{uuid}/` — flat sessions with `agents/main/wire.jsonl` + `state.json`
2. `sessions/wd_{project}_*/ses_{uuid}/` — project-grouped sessions

### Gemini CLI chats

Chora can parse Gemini CLI chat exports from `~/.gemini/tmp/`.

```bash
# Auto-detect Gemini when inside ~/.gemini/tmp (or any subdir)
cd ~/.gemini/tmp
python3 ~/.kimi/skills/chora/scripts/chora.py --batch --output-dir ~/peacock/aichats

# Explicit Gemini source mode
python3 ~/.kimi/skills/chora/scripts/chora.py --source gemini --batch --output-dir ~/peacock/aichats

# Single Gemini chat file
python3 ~/.kimi/skills/chora/scripts/chora.py \
  --source gemini \
  --session-dir ~/.gemini/tmp/myproject/chats/session-2026-01-01T00-00-xxxxxxxx.jsonl \
  --output-dir ~/peacock/aichats
```

**Gemini source discovery:**
1. `<project>/chats/session-*.jsonl` — new line-by-line JSONL format
2. `<project>/chats/session-*.json` — old single JSON format
3. `<project>/logs.json` — fallback simple log array
4. `<project>/chats/*.jsonl` — subagent jsonl files

### ChatGPT exports

Chora can parse ChatGPT exported `conversations.json` files.

```bash
# Auto-detect ChatGPT when conversations.json with role="assistant" is found
python3 ~/.kimi/skills/chora/scripts/chora.py \
  --session-dir ~/ai-chats/chatgpt/conversations.json \
  --output-dir ~/peacock/aichats

# Explicit ChatGPT source mode
python3 ~/.kimi/skills/chora/scripts/chora.py --source chatgpt --batch --output-dir ~/peacock/aichats

# Single ChatGPT conversation file
python3 ~/.kimi/skills/chora/scripts/chora.py \
  --source chatgpt \
  --session-dir ~/ai-chats/chatgpt/my-chat.json \
  --output-dir ~/peacock/aichats
```

**ChatGPT format supported:**
- `conversations.json` — array of conversation objects with `title` + `messages`
- Individual `.json` chat exports (single conversation object)
- Messages with `role: "user"` / `role: "assistant"`
- Content as string, `{"parts": [...]}`, or `{"content_type": "text", "parts": [...]}`

### Claude exports

Chora can parse Claude exported `conversations.json` or individual chat exports.

```bash
# Auto-detect Claude when conversations.json with role="assistant" is found
python3 ~/.kimi/skills/chora/scripts/chora.py \
  --session-dir ~/ai-chats/claude/conversations.json \
  --output-dir ~/peacock/aichats

# Explicit Claude source mode
python3 ~/.kimi/skills/chora/scripts/chora.py --source claude --batch --output-dir ~/peacock/aichats

# Single Claude conversation file
python3 ~/.kimi/skills/chora/scripts/chora.py \
  --source claude \
  --session-dir ~/ai-chats/claude/my-chat.json \
  --output-dir ~/peacock/aichats
```

**Claude format supported:**
- `conversations.json` — array of conversation objects with `title` + `messages`
- Original Claude format with `chat_messages` and `sender: "human"` / `sender: "assistant"`
- Individual `.json` chat exports
- Content as string or text object

### DevWater Hook Mode

Chora can run as a **post-session hook** for DevWater (or any orchestrator) to automatically archive sessions on `SessionEnd` or `PreCompact`.

```bash
# Hook mode — silent, auto-detects session from env vars
python3 ~/.kimi/skills/chora/scripts/chora.py --hook

# Hook mode with explicit session directory
python3 ~/.kimi/skills/chora/scripts/chora.py --hook --session-dir /path/to/session

# Hook mode with custom output directory
python3 ~/.kimi/skills/chora/scripts/chora.py --hook --session-dir /path/to/session --output-dir ~/archive/chora
```

**Environment variables read in hook mode:**
- `CHORA_SESSION_DIR` — session directory path
- `DEVWATER_SESSION_DIR` — fallback session directory path

**Hook output directory resolution:**
1. `--output-dir` if explicitly provided
2. `~/peacock/aichats/` created on first run

Hook mode always produces **all four files** (ignores `--quick`), runs silently except for the one-line summary, and outputs into `{output_dir}/{source}/YYYY-MM-DD_{title}_*.md`.

### Helper script for DevWater

A small shell wrapper is included for DevWater integration:

```bash
# Call from DevWater hooks configuration
~/.kimi/skills/chora/scripts/chora-hook.sh [SESSION_DIR]
```

The script accepts an optional session directory argument, falls back to `DEVWATER_SESSION_DIR`, and forwards to `chora.py --hook`. Set it as a `SessionEnd` or `PreCompact` hook in your DevWater config:

```yaml
hooks:
  SessionEnd: ~/.kimi/skills/chora/scripts/chora-hook.sh
```

### List sessions without processing

```bash
python3 ~/.kimi/skills/chora/scripts/chora.py --list
```

---

## CLI Reference

| Flag | Description |
|------|-------------|
| `--session-dir DIR` | Path to a specific session directory or file. For Kimi: `state.json` + `wire.jsonl` dir. For AI Studio: extensionless chat-log file. For Kimi-Code: session dir with `agents/main/wire.jsonl`. For Gemini: `session-*.jsonl` or `session-*.json` file. For ChatGPT/Claude: `conversations.json` or individual `.json` exports. |
| `--output-dir DIR` | Output directory for generated files (default: `~/peacock/aichats`) |
| `--source SOURCE` | Input source: `kimi` (default), `aistudio`, `kimicode`, `gemini`, `chatgpt`, or `claude`. Auto-detected from CWD or file structure. |
| `--batch` | Process all discovered sessions (skips up-to-date by default) |
| `--force` | Re-process sessions even if output is already up-to-date |
| `--quick` | Fast human-only mode: generate only `_human.md` |
| `--hook` | DevWater hook mode: silent, auto-detect session, always 4 files |
| `--list` | List all discovered sessions and exit without processing |

---

## Output Example

### Kimi sessions (kimi-og)

```
~/peacock/aichats/kimi-og/
├── 2026-06-01_what_up_what_did_we_all_get_done_chat.md
├── 2026-06-01_what_up_what_did_we_all_get_done_code.md
├── 2026-06-01_what_up_what_did_we_all_get_done_think.md
├── 2026-06-01_what_up_what_did_we_all_get_done_human.md
├── 2026-05-31_i_dont_ike_how_your_doing_it_chat.md
├── 2026-05-31_i_dont_ike_how_your_doing_it_code.md
├── 2026-05-31_i_dont_ike_how_your_doing_it_think.md
└── 2026-05-31_i_dont_ike_how_your_doing_it_human.md
```

### AI Studio exports (aistudio)

```
~/peacock/aichats/aistudio/
├── 2026-06-01_root_conversation_a_chat.md
├── 2026-06-01_root_conversation_a_code.md
├── 2026-06-01_root_conversation_a_think.md
├── 2026-06-01_root_conversation_a_human.md
├── 2026-05-30_my_first_chat_chat.md
├── 2026-05-30_my_first_chat_code.md
├── 2026-05-30_my_first_chat_think.md
└── 2026-05-30_my_first_chat_human.md
```

### Kimi-Code sessions (kimi-code)

```
~/peacock/aichats/kimi-code/
├── 2026-06-01_whats_up_chat.md
├── 2026-06-01_whats_up_code.md
├── 2026-06-01_whats_up_think.md
├── 2026-06-01_whats_up_human.md
├── 2026-05-31_fix_the_bug_chat.md
├── 2026-05-31_fix_the_bug_code.md
├── 2026-05-31_fix_the_bug_think.md
└── 2026-05-31_fix_the_bug_human.md
```

### Gemini CLI chats (gemini-cli)

```
~/peacock/aichats/gemini-cli/
├── 2026-01-01_session_xxxxxxxx_chat.md
├── 2026-01-01_session_xxxxxxxx_code.md
├── 2026-01-01_session_xxxxxxxx_think.md
├── 2026-01-01_session_xxxxxxxx_human.md
├── 2026-01-02_session_yyyyyyyy_chat.md
├── 2026-01-02_session_yyyyyyyy_code.md
├── 2026-01-02_session_yyyyyyyy_think.md
└── 2026-01-02_session_yyyyyyyy_human.md
```

### ChatGPT exports (chatgpt)

```
~/peacock/aichats/chatgpt/
├── 2026-06-01_chatgpt_python_help_chat.md
├── 2026-06-01_chatgpt_python_help_code.md
├── 2026-06-01_chatgpt_python_help_think.md
└── 2026-06-01_chatgpt_python_help_human.md
```

### Claude exports (claude)

```
~/peacock/aichats/claude/
├── 2026-06-01_claude_api_design_chat_chat.md
├── 2026-06-01_claude_api_design_chat_code.md
├── 2026-06-01_claude_api_design_chat_think.md
└── 2026-06-01_claude_api_design_chat_human.md
```

Every successful run ends with a one-line summary:

```
✅ Chora complete: 42 turns, 127 actions, 4 files → /home/user/peacock/aichats/kimi-og
```

---

## Fallback

If a session directory has **no** `wire.jsonl`, Chora falls back to `context.jsonl`. In this mode:
- Chat, think, and human files are generated normally
- Code file will be **empty** (no tool actions are captured in context.jsonl)

---

## Skipped Wire Events

These events are intentionally ignored:
- `StatusUpdate` — token counts, context usage
- `CompactionBegin` / `CompactionEnd`
- `MCPLoadingBegin` / `MCPLoadingEnd`

---

## Integration Notes

Chora is designed to be the **first step** in a UI pipeline:

1. **Chora** → Parse wire.jsonl → `_chat.md` + `_code.md` + `_think.md` + `_human.md`
2. **UI** → Render chat, link T{turn}.A{action} IDs to code sections
3. **Search / embedding** → Index `_chat.md` for semantic search, index `_code.md` for code search

Chora does **not** replace `session-transcript` — it complements it. `session-transcript` generates rich HTML split-view transcripts. Chora generates the structured, linkable raw material that a UI or downstream parser can consume.
