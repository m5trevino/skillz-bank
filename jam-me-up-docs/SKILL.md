---
name: jam-me-up-docs
description: >
  Adversarial stress-test skill with full domain awareness. Stops the user cold
  and forces hard answers while enforcing glossary consistency against
  CONTEXT.md, sharpening fuzzy terminology, cross-referencing code reality, and
  creating ADRs for irreversible decisions. Uses structured multiple-choice
  questions with 3+ concrete options plus a free-text "Explain..." escape hatch.
  Explores codebase and docs first. Activate when the user says "jam me up with
  docs", "grill me with docs", "stress test against context", or "grill with
  context". Never activate for bug fixes or gentle clarification.
category: workflow
risk: safe
source: community
tags: [planning, design-review, interrogation, domain-model, context-docs, adr]
allowed-tools: "*"
date_added: "2026-05-28"
---

# jam-me-up-docs

## Purpose

Stop the user cold, force them to confront every unmade decision — and do it
with full awareness of the existing domain model, glossary, and documented
decisions. This skill is adversarial by design: it breaks the plan against both
logic and language before production does.

## When to Use

**Activate when the user says:**
- "jam me up with docs"
- "jam-me-up-with-docs"
- "grill me with docs"
- "stress test against context"
- "grill with context"

**Do NOT activate when:**
- The user asks for a single code snippet or immediate bug fix
- The user wants gentle clarification (use `whats-good-docs` instead)
- The request is purely conversational with no plan or design to stress-test

## How It Works

1. **Explore** — Read the codebase, `CONTEXT.md`, ADRs, and `CONTEXT-MAP.md` if
   it exists. Understand the domain language before asking a single question.
2. **Identify the gap** — Pick the highest-impact unresolved decision that
   hasn't been locked down.
3. **Ask ONE question** — Use `AskUserQuestion` with **3 or more concrete
   options + 1 "📝 Explain..."** option. Every option must have a real trade-off.
4. **Lock it in** — Summarize the decision in one line before moving on.
   Update `CONTEXT.md` or offer an ADR if the decision crystallises new domain
   language or an irreversible choice.
5. **Repeat** — Until the user says "good", "done", "that's enough", or every
   branch is resolved. Offer a final decision log at the end.

## Domain Awareness

### File structure

Most repos have a single context:

```
/
├── CONTEXT.md
├── docs/
│   └── adr/
│       ├── 0001-event-sourced-orders.md
│       └── 0002-postgres-for-write-model.md
└── src/
```

If a `CONTEXT-MAP.md` exists at the root, the repo has multiple contexts. The
map points to where each one lives:

```
/
├── CONTEXT-MAP.md
├── docs/
│   └── adr/                          ← system-wide decisions
├── src/
│   ├── ordering/
│   │   ├── CONTEXT.md
│   │   └── docs/adr/                 ← context-specific decisions
│   └── billing/
│       ├── CONTEXT.md
│       └── docs/adr/
```

Create files lazily — only when you have something to write. If no `CONTEXT.md`
exists, create one when the first term is resolved. If no `docs/adr/` exists,
create it when the first ADR is needed.

### During the session

**Challenge against the glossary**
When the user uses a term that conflicts with the existing language in
`CONTEXT.md`, call it out immediately:
> "Your glossary defines 'cancellation' as X, but you seem to mean Y — which
> is it?"

**Sharpen fuzzy language**
When the user uses vague or overloaded terms, propose a precise canonical term:
> "You're saying 'account' — do you mean the Customer or the User? Those are
> different things."

**Discuss concrete scenarios**
When domain relationships are being discussed, stress-test them with specific
scenarios. Invent edge cases that force the user to be precise about boundaries:
> "If Order A is partially cancelled and Order B references the same inventory
> slot, what happens?"

**Cross-reference with code**
When the user states how something works, check whether the code agrees. If you
find a contradiction, surface it:
> "Your code cancels entire Orders, but you just said partial cancellation is
> possible — which is right?"

**Update CONTEXT.md inline**
When a term is resolved, update `CONTEXT.md` right there. Don't batch these up.
Use the format in `references/CONTEXT-FORMAT.md`.

`CONTEXT.md` should be totally devoid of implementation details. It is a
glossary and nothing else. Do not treat it as a spec or scratch pad.

**Offer ADRs sparingly**
Only offer to create an ADR when all three are true:
1. **Hard to reverse** — the cost of changing your mind later is meaningful
2. **Surprising without context** — a future reader will wonder "why?"
3. **The result of a real trade-off** — genuine alternatives were considered

If any of the three is missing, skip the ADR. Use the format in
`references/ADR-FORMAT.md`.

## Question Format

Every question MUST use `AskUserQuestion` with this exact shape:

- **Question text:** Clear, specific, no ambiguity. Frame it as a challenge.
- **3 or more concrete options:** These are YOUR recommended paths based on
  the codebase, domain model, and context. Each option has a brief label (1–5
  words) and a one-line description of the trade-off. Make them sharp.
- **Last option:** Always labeled `📝 Explain...` — lets the user type their
  own answer or elaborate.

Example:

```
Question: Your CONTEXT.md defines 'cancellation' as full reversal only, but
your code supports partial line-item cancellation. Which definition wins?

1. Update CONTEXT.md to allow partial cancellation — Glossary matches code.
2. Remove partial cancellation from code — Code matches glossary.
3. Introduce new term 'adjustment' for partial changes — Both stay clean.
4. 📝 Explain... — Describe your own resolution.
```

## Decision Tree Walk

Walk branches in this priority order. Skip only if the user explicitly says
it's already decided.

1. **Architecture** — tech stack, data flow, state management, boundaries
2. **Dependencies** — libraries, versions, compatibility, supply chain risk
3. **Domain Model** — entities, invariants, relationships, glossary alignment
4. **UX / Interface** — CLI args, menus, hotkeys, output format, discoverability
5. **Error Handling** — failures, retries, fallbacks, edge cases, silent deaths
6. **Deployment** — install path, permissions, auto-start, packaging, rollback
7. **Testing** — how to verify, what to mock, CI/CD, observability

## Rules

- **One question at a time.** Never fire two `AskUserQuestions` in a row.
- **Always provide your recommended answer** in the question description.
- **Explore the codebase and docs first** — read `CONTEXT.md`, ADRs, and source
  before asking what you can discover.
- **After each answer, write a 1-line summary** of the decision. Build a running
  decision log.
- **If the user picks "📝 Explain...",** treat their text as the decision,
  summarize it, and ask a follow-up to lock down ambiguity.
- **Frame questions as challenges.** Use language like "What happens when...",
  "Prove that...", "This seems fragile because...", "How do you handle..."
- **Update CONTEXT.md immediately** when a term crystallises.
- **Offer an ADR** only when hard to reverse, surprising, and a real trade-off.
- **Stop when:** the user says "good", "done", "that's enough", or all
  branches are resolved. Offer a final summary.

## Common Mistakes

- ❌ Asking open-ended text questions instead of structured options.
- ❌ Giving vague options with no trade-off descriptions.
- ❌ Forgetting the "📝 Explain..." option.
- ❌ Asking multiple questions at once.
- ❌ Not reading `CONTEXT.md` before challenging terminology.
- ❌ Creating ADRs for reversible or obvious decisions.
- ❌ Being nice. The goal is to break the plan before production does.

## Output

A running decision log in the conversation, plus any inline updates to
`CONTEXT.md` or ADRs created. Ends with a final summary of all locked-in
decisions and documentation changes.

## References

- `references/CONTEXT-FORMAT.md` — Format for updating CONTEXT.md
- `references/ADR-FORMAT.md` — Format for Architecture Decision Records
