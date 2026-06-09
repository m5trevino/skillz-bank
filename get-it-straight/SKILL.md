---
name: get-it-straight
description: Takes structured questions and prepares them for the user to answer one at a time in their local CLI bot. Each question gets 3 pre-filled options plus one open input option. Minimal instructions. Use when you have decision-forcing questions that need to be answered cleanly.
---

# get-it-straight

Take the list of questions and turn them into a simple, ready-to-use format for answering one question at a time.

## Core Rules

- Output questions **one at a time**.
- Preserve the original options from the input as much as possible.
- If the input has pre-filled options + an open input option, keep that structure.
- Do **not** artificially limit or force a specific number of options (could be 3, 4, 5, or 6 depending on the source).
- Do **not** add extra explanation, context, or instructions unless the user asks for it.
- Preserve the original question text exactly.
- Keep the output clean and mechanical.

## Output Format

For each question, output in this exact shape:

```markdown
Q-00X: [Short title of the question]

[Full question text here]

1. [Pre-filled answer 1]
2. [Pre-filled answer 2]
3. [Pre-filled answer 3]
4. [Open input — user types their own answer]

---
```

After the user answers all questions, they will bring back the locked decisions.

## What This Skill Does NOT Do

- Does not assume any specific bot name or function name.
- Does not add long "handoff instructions" or "use this function" text.
- Does not summarize or rewrite the questions.
- Does not add "Why this matters" sections unless they were already in the input.

This skill exists to make raw structured questions easy to consume one by one while preserving the original options structure (including open input options). Nothing more.