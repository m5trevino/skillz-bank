---
name: session-handoff
description: Generates a cold-start handoff document that tells a NEW bot exactly where work left off. Compact, task-focused, zero-fluff. Designed to be read at the start of a fresh session with zero prior context.
triggers:
  - "hand off"
  - "handoff"
  - "where did we leave off"
  - "next session"
  - "cold start"
  - "continue work"
  - "pick up where"
  - "new session"
  - "resume task"
  - "bot handoff"
  - "session handoff"
---

# Session Handoff

## Purpose

The standard report is a complete overview. The guardian snapshot preserves critical decisions. The **handoff report** is the third piece: it tells a brand-new bot **exactly what to do first**.

When a new session starts with zero context, the bot reads:
1. Standard report → understands the big picture
2. Guardian snapshot → sees critical decisions and fixes
3. **Handoff report** → knows the current task, file state, and next action

Result: zero context degradation, zero "what were we doing?", immediate productivity.

## Agent Instructions

When triggered, run the questionnaire, then execute the script.

### Questionnaire (1 batch, 3 questions)

**Question 1 — Task focus:**
> "What task were we in the middle of when this session ends?"
- Auto-detect from recent turns ← Default
- I'll specify the task name
- Multiple parallel tasks

**Question 2 — State when stopped:**
> "What was happening when we stopped?"
- Writing / editing code
- Debugging a bug
- Running tests
- Researching / exploring
- Planning / designing
- Waiting on me (user)

**Question 3 — Blockers & next step:**
> "Any blockers, and what should the next bot do FIRST?"
- No blockers — continue current task
- Bug blocking — fix this first
- Decision needed — ask user first
- Environment issue — fix setup first
- I'll type the exact next step

### Script Execution

```bash
python3 ~/.kimi/skills/session-handoff/scripts/session_handoff.py \
  --session-dir <path> \
  --guardian-snapshot <path> \
  --task "<task description>" \
  --state {coding|debugging|testing|researching|planning|waiting} \
  --next-step "<description>" \
  --output-to {archive|session|both}
```

### How the Script Works

1. Reads the last N turns (default: last 10) to understand current context
2. Reads the guardian snapshot (if available) for P0 decisions/fixes relevant to current task
3. Extracts files mentioned in recent turns and code blocks
4. Detects test commands, errors, and fix attempts
5. Generates a compact handoff report (target: under 1500 tokens)

### Handoff Report Structure

```markdown
# Hand-Off Report — {project}
**Task:** {current task}
**Status:** {in progress / blocked / waiting}
**Left off:** {what was happening}

## Boot Sequence (READ THESE FIRST)
1. {file to read first}
2. {file to read second}
3. {run this command}

## Files In Play
| File | Status | Notes |
|------|--------|-------|
| path/to/file.py | modified | last edited in turn 47 |

## Current Code State
```
{key code snippet showing current state}
```

## What Works / What Doesn't
- ✓ Working: ...
- ✗ Broken: ...
- ? Unknown: ...

## Exact Next Action
1. {first thing to do}
2. {second thing}
3. {third thing}

## Decisions Needed
- {any pending decision}

## Guardian Context
- {relevant P0 decisions from guardian snapshot}
```

## Best Practices

- Keep the handoff under 1500 tokens — it's meant to be READ, not stored
- The "Boot Sequence" section is the most important — tell the new bot exactly what files to read first
- Include actual code snippets, not descriptions — saves the bot from having to search
- If tests are failing, include the exact failure message
- If there's a bug, include the exact error and what you've tried

## Integration

This skill runs AFTER `session-compact` (which runs guardian + transcripts + context-agent). The handoff reads the guardian snapshot that was just generated and focuses it into a task-level cold-start document.
