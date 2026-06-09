# ADR Format

Architecture Decision Records capture decisions that are hard to reverse,
surprising without context, and the result of real trade-offs.

## Filename

```
docs/adr/0001-[short-kebab-title].md
```

Use zero-padded sequential numbers.

## Structure

```markdown
# [Number]. [Title]

## Status

Proposed / Accepted / Deprecated / Superseded by [link]

## Context

What is the forcing function? What problem are we solving?

## Decision

What are we doing? Be specific.

## Consequences

### Positive
- ...

### Negative
- ...

### Risks
- ...

## Alternatives Considered

- **[Alternative A]** — Why it was rejected.
- **[Alternative B]** — Why it was rejected.
```

## Rules

- Keep it under 2 pages. Brevity forces clarity.
- Status starts as "Proposed". Move to "Accepted" only after implementation
  begins.
- If a decision is reversed, mark the old ADR as "Superseded" and link forward.
- Do not use ADRs for reversible or obvious choices.
