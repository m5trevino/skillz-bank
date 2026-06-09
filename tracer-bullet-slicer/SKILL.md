---
name: tracer-bullet-slicer
description: >-
  Takes ANY input (PRD, implementation plan, current situation, messy notes,
  schema migration doc, whatever the fuck you throw at it) and slices it into
  clean, thin vertical tracer bullet slices. Each slice is a narrow, independent,
  full-stack execution unit. Zero knowledge of the overall mission allowed.
  This skill is the gatekeeper that keeps every agent blind and focused.
category: planning
risk: low
tags:
  - tracer-bullet
  - vertical-slice
  - compartmentalization
  - dark-factory
  - high-signal
  - ruthless-decomposition
triggers:
  - "slice this into tracer bullets"
  - "make tracer bullet plan"
  - "break down vertically"
  - "create sliced plan"
  - "bad ass tracer slices"
---

# Tracer Bullet Slicer — v2

## What It Does

Takes ANY input and slices it into **clean, thin vertical tracer bullet slices**. Each slice is a narrow, independent, full-stack execution unit. **Zero knowledge of the overall mission allowed.** This skill keeps every agent blind and focused.

## Execution Flow

1. **Ingest & Strip** — Read input, extract only core objectives and high-risk areas. Kill all fluff.
2. **Risk-First Analysis** — Identify highest risk / unknown / critical path items first.
3. **Vertical Slice** — Break into thin, full-stack tracer bullets. Each slice must stand alone.
4. **Harden & Compartmentalize** — Aggressively split anything that risks leaking big picture.
5. **Output Locked Slices** — Numbered, ready for Head Coach sequencing and Defensive Coordinator gates.

## Decision Logic

- Input vague or messy → Immediately trigger `jam-me-up` or `whats-good`.
- Any slice risks exposing full scope → Split it harder, no mercy.
- Prioritize: Highest risk → Highest value → Quick feedback loops.
- If something smells like horizontal layer → Destroy it and re-slice vertically.

## Guardrails (Non-Negotiable)

- **Maximum Compartmentalization** — No slice gets even a hint of the full project vision. Ever.
- **No horizontal bullshit** — No "do all models", "build entire UI", etc.
- Every slice must be independently buildable, testable, and verifiable.
- **Max 4–8 hours effort per slice** — Force it small.
- Every slice requires: narrow objective, strict scope, acceptance criteria, test strategy, handoff format.
- If in doubt, **make the slice smaller**.

## Output Format

```yaml
tracer_bullets:
  - slice_id: TB-001
    name: "User Login Flow"
    objective: "Narrow — only login, no profile or permissions"
    scope: "UI form + POST /auth + token storage + error handling"
    acceptance_criteria:
      - User can login with email/password
      - JWT token is returned and stored securely
      - Invalid credentials returns 401 with clear message
    test_strategy: "Unit + integration for auth flow"
    handoff_format: "Auth service interface + token shape"
    estimated_effort: "4 hours"
    hard_gates:
      - Must not reference user profile, roles, or permissions
      - Must not depend on any unbuilt slice
```
