# Chat Humanizer

Convert AI platform JSON exports into clean, readable Markdown.

**Platforms:** ChatGPT, Claude, Google AI Studio / Gemini  
**Modes:** Single combined file (default) OR one file per conversation (`--split`)

---

## Usage

### Default — Single combined file
```bash
humanize-chat ~/ai-chats/chatgpt/conversations.json
# → creates conversations.md

humanize-chat ~/ai-chats/claude/conversations.json
# → creates conversations.md

humanize-chat ~/ai-chats/aistudio/my-chat.txt
# → creates my-chat.txt.md
```

### Split — One file per conversation
```bash
# ChatGPT
humanize-chat ~/ai-chats/chatgpt/conversations.json --split
# → creates conversations-humanized/001-Title-Here.md

# Claude
humanize-chat ~/ai-chats/claude/conversations.json --split
# → creates conversations-humanized/001-Title-Here.md

# AI Studio (single file)
humanize-chat ~/ai-chats/aistudio/my-chat.txt --split
# → creates my-chat.txt-humanized/001-conversation.md

# Custom output directory
humanize-chat ~/ai-chats/claude/conversations.json ~/my-output --split
```

---

## Installation

```bash
# Already added to ~/.bashrc as:
alias humanize-chat='python3 ~/.openclaw/skills/chat-humanizer/humanize.py'
```

---

## Supported Formats

| Platform | File | Structure |
|----------|------|-----------|
| **ChatGPT** | `conversations.json` | Array of objects with `mapping` tree |
| **Claude** | `conversations.json` | Array of objects with `chat_messages` |
| **AI Studio** | extensionless `.txt` or `.json` | `chunkedPrompt.chunks` or `contents` |

---

## Filename Convention (Split Mode)

Each conversation gets a numbered, sanitized filename:

```
001-Project-Setup-Help.md
002-Debug-API-Error.md
003-Refactor-Plan.md
```

Titles are cleaned of invalid filesystem characters and truncated to 60 characters.
