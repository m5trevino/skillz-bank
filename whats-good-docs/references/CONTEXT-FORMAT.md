# CONTEXT.md Format

`CONTEXT.md` is a glossary. Nothing else. No implementation details, no specs,
no scratch pads.

## Structure

```markdown
# [Domain Name] Context

## Glossary

### [Term]

**Definition:** One clear sentence.
**Also known as:** [synonyms or legacy names]
**Not to be confused with:** [nearby terms]
**Used in:** [bounded contexts or modules]
```

## Rules

- One term per section.
- Definition must be implementation-free.
- If a term has state (e.g., "Order"), list the states as sub-bullets, not as
  workflow or logic.
- When a term is renamed, keep the old name in "Also known as" for searchability.
- Do not put code, API signatures, or file paths in CONTEXT.md.
