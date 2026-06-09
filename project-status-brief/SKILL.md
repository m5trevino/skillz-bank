---
name: project-status-brief
description: >
  Forces the coder bot to output a clean, high-signal, compartmentalized snapshot
  of the CURRENT project state. No full vision, no implementation plan, no future
  speculation. Only what exists right now. This brief is formatted so Grok (or any
  slicer) can create accurate tracer bullet slices without leaking scope.
category: planning
risk: low
tags:
  - project-status
  - current-state
  - handoff
  - compartmentalization
  - tracer-prep
triggers:
  - "give grok the current project status"
  - "create project status brief"
  - "snapshot current codebase state"
  - "prepare for tracer bullet slicing"
---

# Project Status Brief

## What It Does

Outputs a clean, high-signal, compartmentalized snapshot of the **CURRENT** project state. No full vision. No implementation plan. No future speculation. Only what exists right now.

## Execution Flow

1. **Scan** the current codebase/files only.
2. **Extract** key components, modules, and state.
3. **List** completed, in-progress, and missing pieces narrowly.
4. **Output** in strict format only. No extra commentary.

## Decision Logic

- Stay strictly in "what exists right now" — never speculate on future work.
- If something is unclear, mark it as `UNKNOWN` and move on.
- Keep output small and dense.

## Guardrails

- **Maximum compartmentalization**: Do not mention overall goals, big picture, or future plans.
- **No implementation plan leakage**.
- Output must be copy-paste ready for Grok.

## Output Format

```yaml
project_status_brief:
  project_name: "Short name"
  current_date: "YYYY-MM-DD"
  core_modules:
    - name: "..."
      status: "complete | in-progress | missing"
      description: "One sentence max"
      key_files: ["file1", "file2"]
  data_flow: "Short description of main data paths (if relevant)"
  tech_stack: ["list", "of", "tech"]
  known_issues:
    - "Only current blockers"
  handoff_notes: "Anything Grok needs to know for slicing"
```
