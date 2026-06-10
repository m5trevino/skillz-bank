---
name: tracer-bullet-slicer
description: >-
  Takes ANY input (PRD, implementation plan, current situation, messy notes,
  or whatever you throw at it) and slices it into clean, thin vertical tracer
  bullet slices. Each slice is a narrow, independent, full-stack execution
  unit. Zero knowledge of the overall mission allowed. This skill is the
  gatekeeper that keeps every agent blind and focused.
category: planning
risk: low
tags:
  - tracer-bullet
  - vertical-slice
  - compartmentalization
  - dark-factory
  - high-signal
  - ruthless-decomposition
  - incremental-delivery
triggers:
  - "slice this into tracer bullets"
  - "make tracer bullet plan"
  - "break down vertically"
  - "create sliced plan"
  - "bad ass tracer slices"
  - "decompose into vertical slices"
  - "tracer bullet decomposition"
  - "split this into independent units"
---

# Tracer Bullet Slicer

## What It Does

Takes ANY input and slices it into **clean, thin vertical tracer bullet slices**. Each slice is a narrow, independent, full-stack execution unit. **Zero knowledge of the overall mission allowed.** This skill keeps every agent blind and focused and is the gatekeeper that prevents scope bleed.

## When to Use

- Starting a new feature or project that needs incremental delivery
- Breaking down a large PRD or spec into independently shippable units
- Whenever a plan feels too abstract or horizontally layered
- When stakeholders ask for "everything at once" and you need to reframe as vertical slices
- Any time you need a sequenced execution plan with clear handoffs between agents

## Do Not Use

- For trivial single-file changes (just do it directly)
- When the full scope is already small and well-understood (< 1 day of work)
- For pure research or investigation that has no clear output artifact
- When the input is already sliced vertically and just needs validation

## Execution Flow

1. **Ingest & Strip** — Read input, extract only core objectives and high-risk areas. Kill all fluff.
2. **Risk-First Analysis** — Identify highest risk / unknown / critical path items first.
3. **Vertical Slice** — Break into thin, full-stack tracer bullets. Each slice must stand alone.
4. **Harden & Compartmentalize** — Aggressively split anything that risks leaking big picture.
5. **Output Locked Slices** — Numbered, ready for Head Coach sequencing and Defensive Coordinator gates.

## Decision Logic

- Input vague or messy → Immediately trigger `jam-me-up` or `whats-good` to clarify before slicing.
- Any slice risks exposing full scope → Split it harder, no mercy. If you can imagine the full system from one slice, it's too big.
- Prioritize: Highest risk → Highest value → Quick feedback loops.
- If something smells like horizontal layer (shared model, global config, "all of X") → Destroy it and re-slice vertically.
- Two slices that share the same hard gate → Merge them or find the real boundary.
- A slice with > 8 hours estimated effort → Split it.
- A slice with zero hard gates → You missed a constraint, find it.
- If a slice's handoff is "everything" → Wrong. A slice hands off exactly one interface or data shape.
- When a dependency between slices appears → Document it explicitly. If more than 2 dependencies chain, re-architect.

## Guardrails (Non-Negotiable)

- **Maximum Compartmentalization** — No slice gets even a hint of the full project vision. Ever.
- **No horizontal bullshit** — No "do all models", "build entire UI", "set up database schema", etc.
- Every slice must be independently buildable, testable, and verifiable.
- **Max 4–8 hours effort per slice** — Force it small. If unsure, pick the lower bound.
- Every slice requires: narrow objective, strict scope, acceptance criteria, test strategy, handoff format.
- If in doubt, **make the slice smaller**.
- Never output a slice that depends on another unbuilt slice without flagging it.

## Output Format

Each slice follows this strict template:

```yaml
tracer_bullets:
  - slice_id: TB-NNN
    name: "One-line present-tense description"
    objective: "Narrow — what exactly does this slice achieve?"
    scope: "What's included + what's explicitly excluded"
    acceptance_criteria:
      - List of concrete, testable conditions
    test_strategy: "Unit, integration, e2e — one line per approach"
    handoff_format: "The exact interface, data shape, or artifact this slice produces"
    estimated_effort: "X hours (always 4-8)"
    hard_gates:
      - Things this slice MUST NOT do or reference
      - Slices it explicitly depends on (if any)
```

## Edge Cases

- **Dependency chain > 2 deep**: Flag it in the plan annotation, not in any single slice. The orchestrator needs visibility.
- **Slice with no test strategy**: It's not a real slice. Go back to step 3.
- **Single slice taking the whole feature**: You failed at step 4. The feature is too big for one slice.
- **Two identical handoff formats from different slices**: They overlap. Merge or re-slice.
- **Input is already slices**: Skip straight to validation. Check: independence, size, gate coverage, test strategy.

## References

See `references/example-slice-output.yaml` for a concrete example of a 3-slice decomposition of a "User Payment System" PRD.

