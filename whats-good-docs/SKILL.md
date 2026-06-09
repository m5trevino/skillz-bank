---
name: whats-good-docs
description: >
  Supportive comprehension skill with full domain awareness. Seeks to
  understand every detail of the user's plan while enforcing glossary
  consistency against CONTEXT.md, sharpening fuzzy terminology,
  cross-referencing code reality, and creating ADRs for irreversible decisions.
  Uses structured multiple-choice questions with 3+ concrete options plus a
  free-text "Explain..." escape hatch. Explores codebase and docs first.
  Activate when the user says "whats good with docs", "help me understand with
  context", "walk me through with docs", or "explain with context". Never
  activate for adversarial review or bug fixes.
category: workflow
risk: safe
source: community
tags: [planning, comprehension, clarification, domain-model, context-docs, adr]
allowed-tools: "*"
date_added: "2026-05-28"
---

# whats-good-docs

## Purpose

Achieve complete, shared understanding of the user's plan — with full
awareness of the existing domain model, glossary, and documented decisions.
This skill is supportive and curious by design. It helps the user articulate
their intent clearly while keeping the domain language sharp and the docs in
sync.

## When to Use

**Activate when the user says:**
- "whats good with docs"
- "what's good with docs"
- "help me understand with context"
- "walk me through with docs"
- "explain with context"
- "make sure i understand the context"

**Do NOT activate when:**
- The user asks for a single code snippet or immediate bug fix
- The user wants to be grilled or have holes poked (use `jam-me-up-docs`
  instead)
- The request is purely conversational with no plan or design to understand

## How It Works

1. **Explore** — Read the codebase, `CONTEXT.md`, ADRs, and `CONTEXT-MAP.md` if
   it exists. Understand the domain language before asking a single question.
2. **Identify the gap** — Pick the highest-impact area where your understanding
   is incomplete or the user's intent is not yet fully surfaced.
3. **Ask ONE question** — Use `AskUserQuestion` with **3 or more concrete
   options + 1 "📝 Explain..."** option. Every option must help clarify intent.
4. **Confirm understanding** — Summarize what you heard in one line before
   moving on. Update `CONTEXT.md` or offer an ADR if new domain language or an
   irreversible choice crystallises.
5. **Repeat** — Until the user says "good", "done", "that's enough", or every
   branch is understood. Offer a final comprehension summary at the end.

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

**Clarify against the glossary**
When the user uses a term that might conflict with the existing language in
`CONTEXT.md`, gently clarify:
> "I see you used 'account' — in CONTEXT.md that's defined as Customer. Did
> you mean Customer, or is this a different concept we should add to the
> glossary?"

**Sharpen fuzzy language**
When the user uses vague or overloaded terms, propose a precise canonical term
with curiosity:
> "You keep saying 'handle it' — help me be precise. Do you mean retry,
> degrade, or fail fast?"

**Discuss concrete scenarios**
When domain relationships are being discussed, confirm understanding with
specific scenarios. Invent edge cases to make sure you and the user see the
same boundaries:
> "Let me check my understanding: if Order A is partially updated and Order B
> references the same inventory slot, the intended behavior is...?"

**Cross-reference with code**
When the user states how something works, check whether the code agrees. If you
find a difference, surface it as a clarification, not an accusation:
> "I want to make sure I'm following: the code cancels entire Orders, and you
> just mentioned partial cancellation. Is the code ahead of the docs, or should
> I update my understanding?"

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

- **Question text:** Clear, specific, no ambiguity. Frame it as curiosity.
- **3 or more concrete options:** These are YOUR best interpretations of what
  the user might mean, based on the codebase, domain model, and context. Each
  option has a brief label (1–5 words) and a one-line description. Make them
  generous, not leading.
- **Last option:** Always labeled `📝 Explain...` — lets the user type their
  own answer or elaborate.

Example:

```
Question: Help me understand how 'cancellation' should work here. CONTEXT.md
defines it as full reversal only, but I see partial refund logic in the code.
What's the intended domain model?

1. Cancellation is always full — Partial refunds are a separate 'adjustment'
   concept.
2. Cancellation can be partial — We should update CONTEXT.md to match the code.
3. Both exist as separate operations — 'cancel' and 'partially-cancel' are
   different domain events.
4. 📝 Explain... — Describe the intended behavior in your own words.
```

## Comprehension Tree Walk

Walk branches in this priority order. Skip only if the user explicitly says
it's already clear.

1. **Goals & Intent** — What problem are we solving? Who is the user? What does
   success look like?
2. **Architecture** — tech stack, data flow, state management, boundaries
3. **Dependencies** — libraries, versions, compatibility, rationale for choices
4. **Domain Model** — entities, invariants, relationships, glossary alignment
5. **UX / Interface** — CLI args, menus, hotkeys, output format, user journey
6. **Error Handling** — expected failures, recovery paths, degraded modes
7. **Deployment** — install path, permissions, auto-start, packaging
8. **Testing** — how to verify, what matters most to get right

## Rules

- **One question at a time.** Never fire two `AskUserQuestions` in a row.
- **Always provide your best interpretation** in the question description so
  the user knows you're trying to see it their way.
- **Explore the codebase and docs first** — read `CONTEXT.md`, ADRs, and source
  before asking what you can discover.
- **After each answer, write a 1-line summary** of your understanding. Build a
  running comprehension log.
- **If the user picks "📝 Explain...",** treat their text as the source of
  truth, summarize it back, and ask a gentle follow-up to fill any gaps.
- **Frame questions as curiosity.** Use language like "Help me understand...",
  "What was the thinking behind...", "Walk me through what happens when..."
- **Update CONTEXT.md immediately** when a term crystallises.
- **Offer an ADR** only when hard to reverse, surprising, and a real trade-off.
- **Stop when:** the user says "good", "done", "that's enough", or all
  branches are understood. Offer a final summary.

## Common Mistakes

- ❌ Asking open-ended text questions instead of structured options.
- ❌ Giving vague options with no descriptions.
- ❌ Forgetting the "📝 Explain..." option.
- ❌ Asking multiple questions at once.
- ❌ Not reading `CONTEXT.md` before clarifying terminology.
- ❌ Creating ADRs for reversible or obvious decisions.
- ❌ Turning adversarial. The goal is shared understanding, not interrogation.

## Output

A running comprehension log in the conversation, plus any inline updates to
`CONTEXT.md` or ADRs created. Ends with a final summary of everything
understood and documentation changes.

## References

- `references/CONTEXT-FORMAT.md` — Format for updating CONTEXT.md
- `references/ADR-FORMAT.md` — Format for Architecture Decision Records
