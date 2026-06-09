---
name: slice-n-dice
description: General-purpose sequential auto-slicer for tracer bullet execution. Ingests a list of slices and runs them one at a time with completely fresh agents. Uses loud, unmistakable handoff messaging so you always know when one slice ends and the next begins. Designed for any project — not tied to any specific framework or UI library. Use when you want clean, compartmentalized execution of many narrow slices without context bleed.
---

# slice-n-dice — General Sequential Auto-Slicer

This skill turns a list of tracer bullet slices into a strict, sequential execution pipeline where **each slice runs in a brand new agent with zero knowledge of anything before it**.

## Core Behavior

- Accepts a list of tracer bullet slices (in the standard format with objective, scope, acceptance_criteria, hard_gates, etc.).
- Executes them **one at a time** in strict order.
- Every new slice is announced with clear, loud messaging so there is zero ambiguity about when one slice ends and the next begins.
- Each slice is treated as a completely isolated task. The agent running it has **only** that slice’s objective, scope, acceptance criteria, and hard gates.
- After a slice finishes, it clearly signals completion before moving to the next one.
- Resume-safe and stateful via manifest + progress tracking.

## Messaging Format (Strict)

When a new slice starts:

```
══════════════════════════════════════════════════════════════════
NEW SLICE STARTING — FRESH AGENT
══════════════════════════════════════════════════════════════════
Slice: [slice_id] — [slice_name]
This slice is being executed by a completely fresh agent.
Zero knowledge of any previous slices or the overall project.
Only this slice’s objective, scope, acceptance_criteria, and hard_gates are visible.
[Loading sealed task for this slice only...]
```

When a slice finishes:

```
══════════════════════════════════════════════════════════════════
SLICE COMPLETE
══════════════════════════════════════════════════════════════════
[slice_id] finished successfully.
Moving to next slice...
```

These messages must appear exactly like this. They are non-negotiable.

## When to Use

Use this skill when:
- You have a large list of tracer bullet slices and want them executed cleanly one by one.
- You want to guarantee fresh agent context for every slice (no context degradation or assumption carry-over).
- You are working on any project (not just OpenTUI) and need reliable, auditable slice execution.
- You want loud, unmistakable signaling between slices.

## Rules

- Never run more than one slice at a time.
- Never give the agent running a slice any information about previous or future slices.
- Never skip the loud messaging.
- If a slice fails or is blocked by its hard gates, stop and surface it clearly before continuing.
- Keep the focus narrow: this skill exists to execute slices sequentially with fresh agents. It does not generate slices, it does not design architecture, it executes.

## Output After All Slices Complete

When the full list is finished, produce a clean summary:
- Total slices attempted
- Slices completed successfully
- Any slices that were blocked or failed + short reason
- Final state of the project after the run

This skill is the general-purpose execution engine for tracer bullet methodology. It is framework-agnostic and project-agnostic.