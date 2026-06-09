---
name: handoff
description: >
  Compacts the current conversation into a dense, cold-start handoff document
  saved to the OS temp directory — never the workspace. Captures decisions,
  current state, modified files, next steps, and suggested skills. References
  existing artifacts (PRDs, plans, ADRs, commits, diffs) by path instead of
  duplicating them. Redacts secrets and PII. Activate when the user says
  "handoff", "create handoff", "session handoff", "pass this to another agent",
  "cold start doc", or "summarise for next session". Never activate for code
  generation, bug fixes, or casual chat without an explicit handoff request.
argument-hint: "What will the next session be used for?"
category: workflow
risk: safe
source: community
tags: [context-management, session-handoff, continuity, cold-start, summary]
allowed-tools: "*"
date_added: "2026-05-28"
---

# handoff

## Purpose

Distil the entire session into a single document that a fresh agent can read
cold and immediately know: what the goal is, where things stand, what got
decided, what changed, and what to do next — without reading the full
conversation history.

## When to Use

**Activate when the user says:**
- "handoff"
- "create handoff"
- "session handoff"
- "pass this to another agent"
- "cold start doc"
- "summarise for next session"
- "save state for later"

**Do NOT activate when:**
- The user wants to continue working in the current session
- The request is a bug fix, code generation, or casual chat without an
  explicit handoff trigger
- The user says "save this file" or "write this to disk" — that is normal
  file I/O, not a session handoff

## How It Works

1. **Analyse the session** — Review the conversation, decisions, file changes,
   and any invoked skills.
2. **Gather artifacts** — Identify PRDs, plans, ADRs, issues, commits, and diffs
   that exist in the workspace. Note their paths.
3. **Determine next focus** — If the user passed an `argument-hint`, treat it
   as the description of what the next session will focus on. Tailor the
   handoff accordingly.
4. **Draft the document** — Write the handoff using the template below.
5. **Redact** — Scan for API keys, passwords, tokens, PII, and other secrets.
   Replace with `[REDACTED]`.
6. **Save** — Write the file to the OS temp directory. Do NOT save it into the
   current workspace.

## Information Architecture

| Capture (inline) | Reference (by path only) |
|------------------|--------------------------|
| Original goal / request | PRDs, specs, design docs |
| Decisions made with rationale | ADRs |
| Current state (in-progress / blocked / done) | Commits, diffs |
| Files modified in this session | Full implementation plans |
| Blockers or open questions | Test logs, build outputs |
| Next steps (prioritised) | Conversation history |
| Suggested skills for next agent | — |

**Rule:** If the content exists in another artifact, reference it. Never copy
it into the handoff.

## Redaction Rules

- **ALWAYS redact:** API keys, access tokens, passwords, connection strings,
  private keys, certificates, email addresses, phone numbers, names of
  individuals, internal hostnames or IPs if sensitive.
- **Replace with:** `[REDACTED]` or `[REDACTED: description]` if the type
  matters for context.
- **When in doubt:** Redact. A fresh agent can ask for non-sensitive values.

## Suggested Skills Logic

Analyse the session to recommend skills the next agent should invoke:

1. **Skills already used** — List any skills that were loaded during this
   session. The next agent should know what context was already applied.
2. **Domain match** — Based on the tech stack and task domain, suggest
   relevant skills from the ecosystem (e.g., `fastapi`, `rag-implementation`,
   `pydantic-models-py`).
3. **Next-session focus** — If the `argument-hint` implies a specific phase
   (planning → `plan-author`, implementation → `code-implementer`, review →
   `code-reviewer`), suggest the matching skill.

Format as a simple list with one-line rationale per skill.

## Output Format

Save as Markdown to the OS temp directory (`/tmp/` on Unix, `%TEMP%` on
Windows). Filename: `handoff-YYYYMMDD-HHMMSS.md`.

```markdown
# Handoff: [Short Goal Description]

## Original Goal

One sentence. What was the user trying to achieve?

## Decisions Made

- **[Decision]** — [Rationale in one line].
- **[Decision]** — [Rationale in one line].

## Current State

- **Status:** [in-progress | blocked | complete | needs-review]
- **Last action:** [What was just done]
- **Blockers:** [None | List them]

## Files Modified

- `path/to/file` — [Why it was touched]
- `path/to/file` — [Why it was touched]

## Referenced Artifacts

- `path/to/prd.md` — PRD
- `path/to/adr-0001.md` — ADR: [title]
- `path/to/plan.md` — Implementation plan
- `abc1234` — Commit hash (if committed)

## Next Steps (Prioritised)

1. [Step 1]
2. [Step 2]
3. [Step 3]

## Suggested Skills for Next Agent

- `skill-name` — [Why it should be invoked]
- `skill-name` — [Why it should be invoked]

## Notes

[Anything else the next agent needs to know that doesn't fit above.]
```

## Common Mistakes

- ❌ Saving the handoff into the workspace. It belongs in the OS temp directory.
- ❌ Copying full PRD or ADR text into the handoff. Reference by path.
- ❌ Including raw secrets because "the next agent will need them". Redact
  always; the next agent can request non-sensitive values.
- ❌ Writing a chronological narrative of the conversation. Use the structured
  template — decisions, state, files, next steps.
- ❌ Forgetting the `argument-hint`. If the user provided focus for the next
  session, the handoff must be tailored to it.
- ❌ Suggesting generic skills with no rationale. Every suggestion must explain
  why it matches the next session's work.

## Example

**User:** "handoff: next session will finish the FastAPI auth routes"

**Output:**
```markdown
# Handoff: FastAPI Auth Routes

## Original Goal

Implement JWT-based authentication for the FastAPI user service.

## Decisions Made

- **Use python-jose** — Chosen over PyJWT for built-in JWK support.
- **Access + refresh token pair** — Access 15min, refresh 7d.
- **Argon2 for password hashing** — Future-proof over bcrypt.

## Current State

- **Status:** in-progress
- **Last action:** Login and register routes scaffolded; models defined.
- **Blockers:** None

## Files Modified

- `src/auth/router.py` — Login/register endpoints stubbed
- `src/auth/models.py` — User and Token models
- `src/auth/security.py` — Password hashing utilities

## Referenced Artifacts

- `docs/prd-auth.md` — Full auth PRD
- `docs/adr-0003-jwt-library.md` — Why python-jose

## Next Steps (Prioritised)

1. Implement `/auth/refresh` endpoint
2. Add dependency injection for current_user
3. Write unit tests for all auth flows

## Suggested Skills for Next Agent

- `fastapi` — For idiomatic route patterns and dependency injection
- `code-implementer` — For executing the remaining implementation plan
- `requesting-code-review` — Before merging auth code

## Notes

Refresh token rotation is planned but out of scope for this PR. See PRD
section 4.2.
```
