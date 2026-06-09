---
name: json-chat-analyzer
description: >-
  Parse JSON/JSONL chat exports (Kimi CLI sessions, Claude, OpenAI, etc.) and
  generate an HTML stats dashboard plus a compact Markdown tree breakdown.
  Use when the user wants to analyze chat logs, inspect role/type/think/text
  distributions, or visualize message structure from a JSON/JSONL export.
  Triggers: "json filter", "chat analyzer", "breakdown chat", "analyze session",
  "role stats", "think/text count", "jsonl viewer".
---

# JSON Chat Analyzer

Parse chat exports and emit two files into an output directory:

- `index.html`   — dark, compact dashboard listing every role with counts, type
  tags, and a think/text/other mini-bar. Each role links to its Markdown
  section.
- `breakdown.md` — high-and-tight ASCII tree per role:

```
── role:assistant
│   ├── type:think — 16
│   │   ├── think:16
│   │   └── text:2
│   └── type:text — 0
│       └── text:0
```

## Supported formats

- **JSON**  — single array of messages or `{"messages": [...]}`
- **JSONL** — one JSON object per line (Kimi CLI session exports)
- **Messages** are dicts with `role` and `content` fields

## Content type detection

| `content` shape      | Detected type |
|----------------------|---------------|
| `[{"type":"think"}]` | `think`       |
| `[{"type":"text"}]`  | `text`        |
| `"string"`           | `text`        |
| `null` (meta roles)  | role name     |

No message ever shows as `unknown`.

## Procedure

1. Ask the user for the input `.json` or `.jsonl` file path.
2. Optionally ask for an output directory (defaults to `./chat_analysis`).
3. Run the bundled script:
   ```bash
   python3 ~/.kimi/skills/json-chat-analyzer/scripts/json_chat_analyzer.py \
     <input.jsonl> [output_dir]
   ```
4. Confirm the two output files and print the console summary.
5. Offer to open `index.html` in a browser or show `breakdown.md`.

## Rules

- **ALWAYS**: run the bundled script rather than re-implementing the logic.
- **ALWAYS**: handle both `.json` and `.jsonl` without asking the user to convert.
- **NEVER**: write long sample-message sections or collapsible blocks in the
  Markdown output — keep it high and tight.
- **NEVER**: label a message type as `unknown`; fall back to `text`, the role
  name, or `other`.
