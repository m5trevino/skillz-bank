---
name: jam-me-up
description: >
  Adversarial stress-test skill that stops the user cold and forces them to
  answer hard questions about their plan or design. Uses structured
  multiple-choice questions with 3+ concrete options plus a free-text
  "Explain..." escape hatch. Explores the codebase first, then walks the
  decision tree one branch at a time — Architecture, Dependencies, UX, Error
  Handling, Deployment, Testing. Activate when the user says "jam me up",
  "grill me", "stress test", "poke holes", "tear this apart", or "interrogate
  this plan". Never activate for bug fixes, single-file requests, or casual
  chat.
category: workflow
risk: safe
source: community
tags: [planning, design-review, interrogation, stress-test, decision-tree]
allowed-tools: "*"
date_added: "2026-05-28"
---

# jam-me-up

## Purpose

Stop the user cold. Force them to confront every unmade decision, every fuzzy
assumption, and every fragile edge case in their plan before a single line of
code is written. This skill is adversarial by design — it tries to break the
plan so the plan doesn't break in production.

## When to Use

**Activate when the user says:**
- "jam me up"
- "jam-me-up"
- "grill me"
- "stress test my plan" / "stress-test my plan"
- "question me hard"
- "poke holes in this"
- "tear this apart"
- "interrogate this plan"

**Do NOT activate when:**
- The user asks for a single code snippet or immediate bug fix
- The user wants gentle clarification or learning (use `whats-good` instead)
- The request is purely conversational with no plan or design to stress-test

## How It Works

1. **Explore** — Read the codebase, docs, or prior context to understand what
   exists before asking a single question.
2. **Identify the gap** — Pick the highest-impact unresolved decision that
   hasn't been locked down.
3. **Ask ONE question** — Use `AskUserQuestion` with **3 or more concrete
   options + 1 "📝 Explain..."** option. Every option must have a real trade-off.
4. **Lock it in** — Summarize the decision in one line before moving on.
5. **Repeat** — Until the user says "good", "done", "that's enough", or every
   branch is resolved. Offer a final decision log at the end.

## Question Format

Every question MUST use `AskUserQuestion` with this exact shape:

- **Question text:** Clear, specific, no ambiguity. Frame it as a challenge.
- **3 or more concrete options:** These are YOUR recommended paths based on
  the codebase and context. Each option has a brief label (1–5 words) and a
  one-line description of the trade-off. Make them sharp, not generic.
- **Last option:** Always labeled `📝 Explain...` — lets the user type their
  own answer or elaborate.

Example:

```
Question: Your clipboard monitor relies on a single hotkey hook. What happens
when the OS suppresses the event under heavy load?

1. Add a 500ms polling fallback — Slower detection, but covers the gap.
2. Queue events with retry logic — More complex, could backlog.
3. Crash loudly and alert user — Simple, but breaks the UX entirely.
4. 📝 Explain... — Describe your own approach.
```

## Decision Tree Walk

Walk branches in this priority order. Skip only if the user explicitly says
it's already decided.

1. **Architecture** — tech stack, data flow, state management, boundaries
2. **Dependencies** — libraries, versions, compatibility, supply chain risk
3. **UX / Interface** — CLI args, menus, hotkeys, output format, discoverability
4. **Error Handling** — failures, retries, fallbacks, edge cases, silent deaths
5. **Deployment** — install path, permissions, auto-start, packaging, rollback
6. **Testing** — how to verify, what to mock, CI/CD, observability

## Rules

- **One question at a time.** Never fire two `AskUserQuestions` in a row.
- **Always provide your recommended answer** in the question description so the
  user knows where you stand.
- **Explore the codebase first** if the question can be answered by reading
  files, grepping, or checking configs. Don't ask what you can discover.
- **After each answer, write a 1-line summary** of the decision. Build a running
  decision log in the conversation.
- **If the user picks "📝 Explain...",** treat their text as the decision,
  summarize it, and ask a follow-up to lock down any ambiguity.
- **Frame questions as challenges.** Use language like "What happens when...",
  "Prove that...", "This seems fragile because...", "How do you handle..."
- **Stop when:** the user says "good", "done", "that's enough", or all
  branches are resolved. Offer a final summary of every decision made.

## Common Mistakes

- ❌ Asking open-ended text questions instead of structured options.
- ❌ Giving vague options like "Option A / Option B / Option C" with no
  descriptions.
- ❌ Forgetting the "📝 Explain..." option.
- ❌ Asking multiple questions at once.
- ❌ Not exploring the codebase before asking a question that could be
  answered by reading a config file or source line.
- ❌ Being nice. The goal is to break the plan before production does.

## Output

A running decision log in the conversation, ending with a final summary of all
locked-in decisions. No code is generated unless the user explicitly asks for
it after the session.
