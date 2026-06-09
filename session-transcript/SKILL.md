---
name: session-transcript
description: Parse kimi-cli session directories and generate human-readable transcripts in multiple formats — interactive HTML (split-view, searchable, with buckets and modals), Markdown, plain text, and extracted code. Includes an auto-running daemon that watches ~/.kimi/sessions/ and continuously processes new and updated sessions, generating both transcripts and Peacock Standard analysis reports (VI, JE, IE entries). Use when the user wants to export, review, search, share, archive, or auto-process chat sessions. Triggers include: export session, save chat log, transcript, review conversation, share chat, extract code, generate session report, process all sessions, auto-archive sessions, session daemon.
---

# Session Transcript + Orchestrator

Export kimi-cli sessions into human-readable, shareable, and searchable formats. Includes a background daemon that auto-processes all sessions continuously.

## Components

| Component | Script | Purpose |
|-----------|--------|---------|
| **Transcript Generator** | `scripts/generate_transcript.py` | One-shot session export (HTML, MD, TXT, code.md) |
| **Orchestrator Daemon** | `scripts/session-daemon.py` | Background watcher that auto-processes all sessions |

---

## When to Use This Skill

Use the **transcript generator** when the user wants to:
- Export or save a single chat session conversation
- Review a past session's messages, code, or images
- Share a session transcript with another AI bot or human
- Extract all code blocks from a session into a separate file
- Archive session data in a readable format
- Search through past conversations

Use the **orchestrator daemon** when the user wants to:
- Automatically process ALL sessions in the background
- Keep transcripts and standard reports up-to-date without manual work
- Auto-detect new sessions and process them immediately
- Maintain a centralized archive of all session data
- Generate Peacock Standard analysis reports (VI, JE, IE) for every session

---

## Transcript Generator

### Output Formats

| Format | Extension | Description |
|--------|-----------|-------------|
| **HTML** | `.html` | Interactive split-view transcript. Self-contained, no server needed. |
| **Markdown** | `.md` | Formatted transcript with headers, code blocks, and stats. |
| **Text** | `.txt` | Clean raw transcript for sharing with other bots. |
| **Code** | `_code.md` | All code blocks extracted and numbered by turn. |

### HTML Features

- **Split-view layout**: User messages on the left, bot messages on the right
- **Different background shades** per side for easy scanning
- **Boxed design**: Lines on edges and center divider, horizontal separators between turns
- **Turn numbers** displayed in the center gutter
- **Timestamps** in each turn divider
- **Per-message checkboxes** for granular selection
- **Pagination**: 10/25/50/100 turns per page (or all)
- **Search**: Filter by user msg, bot msg, code blocks, images; regex support; highlight matches
- **Filter toggles**: Show user only, bot only, or both
- **Jump to turn**: Input box + dropdown navigation
- **Code modal**: Click "Code" tag on any message to view code in a modal with syntax highlighting toggle, copy, save, or add-to-bucket
- **Image modal**: Click "Image" tag to view uploads with save-to-bucket or save-to-disk
- **Bucket system**: Collect messages, code blocks, and images into buckets (including custom-named buckets). Export all buckets to clipboard or file.
- **View history**: localStorage tracks every time the HTML is opened
- **Scroll position memory**: Returns to where you left off
- **Mobile swipe**: Swipe left/right to switch between user and bot sides on small screens

### Usage

```bash
# Interactive — pick from list or auto-detects current session
python3 scripts/generate_transcript.py

# Specific session
python3 scripts/generate_transcript.py --session-dir ~/.kimi/sessions/xxx/yyyy-yyyy-yyyy-yyyyyyyyyyyy

# Output directory
python3 scripts/generate_transcript.py --output-dir ~/Documents/transcripts

# Specific format
python3 scripts/generate_transcript.py --format html     # HTML only
python3 scripts/generate_transcript.py --format md       # Markdown only
python3 scripts/generate_transcript.py --format txt      # Text only
python3 scripts/generate_transcript.py --format code     # Code extraction only
python3 scripts/generate_transcript.py --format all      # All formats (default)
```

---

## Orchestrator Daemon

The daemon watches `~/.kimi/sessions/` continuously and automatically:
1. Generates transcripts (HTML, MD, TXT, code.md) into each session's `transcripts/` folder
2. Generates Peacock Standard analysis reports into each session's `standard/` folder
3. Archives old standard reports before creating new ones
4. Copies everything to `~/session-archive/` (central archive)
5. Maintains a registry to track what's been processed and when

### Directory Structure

Each session directory gets:
```
{session_uuid}/
├── state.json
├── context.jsonl
├── wire.jsonl
├── transcripts/              <-- NEW
│   ├── {title}_{id}.html
│   ├── {title}_{id}.md
│   ├── {title}_{id}.txt
│   └── {title}_{id}_code.md
└── standard/                 <-- NEW
    ├── standard.created.from.chat.{slug}.{MM-DD}.{YY}.md
    └── archive/
        └── standard.created.from.chat.{slug}.{MM-DD}.{YY}_{timestamp}.md
```

Central archive at `~/session-archive/` mirrors this structure:
```
~/session-archive/
├── .registry.json
├── {project_hash}/
│   └── {session_uuid}/
│       ├── transcripts/
│       └── standard/
│           └── archive/
```

### Standard Analysis (Heuristic)

The daemon generates standard reports using a heuristic analyzer that extracts:

| Entry Type | Detected By |
|------------|-------------|
| **VI (Verbatim Instructions)** | Imperative verbs, explicit command patterns, numbered lists |
| **JE (Journal Entries)** | Decision, progress, experiment, failure, pivot, architecture, insight keywords |
| **IE (Instruction Entries)** | High-signal instructions with inferred target agent and priority |

**Note:** This is an automated baseline. For deeper AI-powered analysis, manually run the Peacock Standard skill on important sessions.

### Daemon Commands

```bash
# Run as background daemon (polls every 60s)
python3 scripts/session-daemon.py --daemon

# Process all sessions once, then exit
python3 scripts/session-daemon.py --batch

# Force re-process all sessions even if up-to-date
python3 scripts/session-daemon.py --batch --force

# Show registry status
python3 scripts/session-daemon.py --status
```

### Systemd Auto-Start (Optional)

Create `~/.config/systemd/user/session-orchestrator.service`:

```ini
[Unit]
Description=Session Orchestrator Daemon
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 %h/.kimi/skills/session-transcript/scripts/session-daemon.py --daemon
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
```

Then enable and start:
```bash
systemctl --user daemon-reload
systemctl --user enable session-orchestrator
systemctl --user start session-orchestrator
systemctl --user status session-orchestrator
```

### Registry

The registry is stored at `~/.kimi/sessions/.orchestrator-registry.json` and tracks:
- Last processed timestamp per session
- Context file mtime (for change detection)
- Turn count, word count, code blocks, images
- VI/JE/IE counts per session
- Generated output filenames

---

## What Gets Parsed

| Source | Parsed? | Notes |
|--------|---------|-------|
| `state.json` | Yes | Title, archived status |
| `context.jsonl` | Yes | Main conversation |
| `context_N.jsonl` | Yes | Archived context segments (in order) |
| `uploads/` | References | Image filenames tagged in messages |
| `tasks/` | No | Not included in transcript |
| `subagents/` | No | Not included in transcript |
| `wire.jsonl` | No | Protocol log, not conversation |

---

## Important Notes

- **HTML images**: The HTML references `./uploads/` via relative path. Moving the HTML file away from the session directory breaks image links. Keep them together or copy both.
- **localStorage**: View history and scroll position are stored per-browser. Different browsers don't share this data.
- **Turn numbering**: Only complete turns (user message + assistant response) are included. Orphaned user messages without a response are skipped.
- **Code blocks**: Fenced code blocks (` ```lang\ncode\n``` `) are extracted. Inline code (` `code` `) is not extracted to the code file.
- **Daemon safety**: The daemon uses a PID file to prevent multiple instances. It handles SIGTERM and SIGINT gracefully.
