---
name: session-compact
description: Interactive skill that runs the full session preservation pipeline (transcripts + guardian extraction + context-agent save) before context compaction hits. Uses questionnaire to let the user choose what to preserve.
triggers:
  - "compact session"
  - "context is getting full"
  - "context limit"
  - "before compaction"
  - "run pipeline"
  - "save context"
  - "snapshot session"
  - "guardian"
  - "prepare for compact"
  - "context at"
  - "about to compact"
  - "preserve session"
  - "checkpoint"
---

# Session Compact

## Overview

When the user mentions context getting full, compaction, or wants to preserve session state, run this interactive pipeline. It combines three existing skills into one guided workflow:

1. **Transcript pipeline** (`session-transcript`) — HTML/MD/TXT/code outputs
2. **Guardian extraction** (`context-guardian`) — P0/P1/P2 critical data extraction + snapshot + briefing
3. **Context-agent save** (`context-agent`) — Session summary in ACTIVE_CONTEXT.md style

## Agent Instructions

When triggered, present **one batch of 3 questions** via `AskUserQuestion`, then execute.

### Questionnaire

**Question 1 — Scope:**
> "This session has {N} turns. What pipeline steps do you want to run?"
- All three (transcript + guardian + context-agent) ← Recommended
- Guardian extraction only (skip transcripts)
- Transcripts only (skip guardian)
- Context-agent summary only

**Question 2 — Guardian depth:**
> "How deep should the guardian extraction go?"
- P0 only — critical decisions, fixes, errors, code changes ← Fastest
- P0 + P1 — add patterns, insights, pivots ← Recommended
- Full P0+P1+P2 — include progress metrics, commands, attempts ← Thorough

**Question 3 — Output & briefing:**
> "Where to save and what extras?" (multi-select)
- Save to session-archive/ (central) ← Recommended
- Save to session dir (local)
- Generate transition briefing for next session ← Recommended
- Include code extraction (`_code.md`)

### After Questions

Build the command from answers and run:

```bash
python3 ~/.kimi/skills/session-compact/scripts/session_compact.py \
  --session-dir <current_session_dir> \
  [--transcript] [--guardian] [--context-agent] \
  --guardian-depth {p0|p0p1|full} \
  --output-to {archive|session|both} \
  --briefing {full|mini|none} \
  [--code-extraction]
```

If the user chose "All three" → enable `--transcript --guardian --context-agent`
If the user chose "Guardian only" → enable `--guardian` only, etc.

### Auto-Detect Current Session

The script auto-detects the most recently modified session if `--session-dir` is omitted. To be explicit, derive it from the current working context or pass the session directory directly.

## Output Structure

```
~/session-archive/{project_name}/{session_id}/
├── transcripts/
│   ├── {slug}_{id}.html
│   ├── {slug}_{id}.md
│   ├── {slug}_{id}.txt
│   └── {slug}_{id}_code.md      (if --code-extraction)
├── snapshots/
│   └── guardian-snapshot-{timestamp}.md
├── briefings/
│   └── transition-briefing-{timestamp}.md
└── context-agent/
    └── session-summary-{timestamp}.md
```

## Integration

| Existing Skill | How This Skill Uses It |
|----------------|------------------------|
| `session-transcript` | Imports `generate_transcript.py` for HTML/MD/TXT/code generation |
| `context-guardian` | Adapts the P0/P1/P2 extraction protocol + snapshot + briefing format |
| `context-agent` | Generates summary in ACTIVE_CONTEXT.md style with topics, decisions, tasks |

## Best Practices

- Run at ~65-70% context usage, before automatic compaction kicks in
- At natural phase transitions (research → build, milestone complete)
- Before delegating to sub-agents
- The transition briefing is designed to be the LAST thing in context, so it survives compaction

## Notes

- The script reuses `generate_transcript.py` from `session-transcript` — do not duplicate that logic
- Guardian extraction is heuristic-based (keyword matching) — review the snapshot for accuracy
- If context is already compacted, the briefing will reference the compaction output block
