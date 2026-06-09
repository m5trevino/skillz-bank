---
name: whats-good
description: >
  Supportive comprehension skill that seeks to understand every detail of the
  user's plan or design through structured multiple-choice questions. Uses 3+
  concrete options plus a free-text "Explain..." escape hatch. Explores the
  codebase first, then walks the comprehension tree one branch at a time —
  Goals, Architecture, Dependencies, UX, Error Handling, Deployment, Testing.
  Curious, thorough, and non-adversarial. Activate when the user says "what's
  good", "help me understand this plan", "make sure i understand", "walk me
  through this", or "explain this to me". Never activate for bug fixes,
  interrogation, or adversarial review (use jam-me-up instead).
category: workflow
risk: safe
source: community
tags: [planning, comprehension, clarification, design-walkthrough, understanding]
allowed-tools: "*"
date_added: "2026-05-28"
---

# whats-good

## Purpose

Achieve complete, shared understanding of the user's plan or design — every
intention, every constraint, every happy path and edge case. This skill is
supportive and curious by design. It does not try to sink the ship; it tries to
see the ship exactly as the captain sees it, so it can help navigate.

## When to Use

**Activate when the user says:**
- "what's good" / "whats good"
- "help me understand this plan"
- "make sure i understand"
- "walk me through this"
- "explain this to me"
- "tell me about this plan"
- "i want to understand"
- "what are we building here"

**Do NOT activate when:**
- The user asks for a single code snippet or immediate bug fix
- The user wants to be grilled, stress-tested, or have holes poked (use
  `jam-me-up` instead)
- The request is purely conversational with no plan or design to understand

## How It Works

1. **Explore** — Read the codebase, docs, or prior context to understand what
   exists before asking a single question.
2. **Identify the gap** — Pick the highest-impact area where your understanding
   is incomplete or the user's intent is not yet fully surfaced.
3. **Ask ONE question** — Use `AskUserQuestion` with **3 or more concrete
   options + 1 "📝 Explain..."** option. Every option must help clarify intent.
4. **Confirm understanding** — Summarize what you heard in one line before
   moving on. Make sure the user agrees with your summary.
5. **Repeat** — Until the user says "good", "done", "that's enough", or every
   branch is understood. Offer a final comprehension summary at the end.

## Question Format

Every question MUST use `AskUserQuestion` with this exact shape:

- **Question text:** Clear, specific, no ambiguity. Frame it as curiosity.
- **3 or more concrete options:** These are YOUR best interpretations of what
  the user might mean, based on the codebase and context. Each option has a
  brief label (1–5 words) and a one-line description. Make them generous, not
  leading.
- **Last option:** Always labeled `📝 Explain...` — lets the user type their
  own answer or elaborate.

Example:

```
Question: Help me understand how the clipboard monitor should behave when the
OS is under heavy load. What's the intended experience?

1. Graceful degradation with polling fallback — Slower but keeps working.
2. Queue and retry with user notification — User knows something's up.
3. Silent tolerance — Miss a few events, no big deal.
4. 📝 Explain... — Describe the intended experience in your own words.
```

## Comprehension Tree Walk

Walk branches in this priority order. Skip only if the user explicitly says
it's already clear.

1. **Goals & Intent** — What problem are we solving? Who is the user? What does
   success look like?
2. **Architecture** — tech stack, data flow, state management, boundaries
3. **Dependencies** — libraries, versions, compatibility, rationale for choices
4. **UX / Interface** — CLI args, menus, hotkeys, output format, user journey
5. **Error Handling** — expected failures, recovery paths, degraded modes
6. **Deployment** — install path, permissions, auto-start, packaging
7. **Testing** — how to verify, what matters most to get right

## Rules

- **One question at a time.** Never fire two `AskUserQuestions` in a row.
- **Always provide your best interpretation** in the question description so
  the user knows you're trying to see it their way.
- **Explore the codebase first** if the question can be answered by reading
  files, grepping, or checking configs. Don't ask what you can discover.
- **After each answer, write a 1-line summary** of your understanding. Build a
  running comprehension log in the conversation.
- **If the user picks "📝 Explain...",** treat their text as the source of
  truth, summarize it back to them, and ask a gentle follow-up to fill any
  remaining gaps.
- **Frame questions as curiosity.** Use language like "Help me understand...",
  "What was the thinking behind...", "Walk me through what happens when...",
  "I'd love to know more about..."
- **Stop when:** the user says "good", "done", "that's enough", or all
  branches are understood. Offer a final summary of everything you learned.

## Common Mistakes

- ❌ Asking open-ended text questions instead of structured options.
- ❌ Giving vague options like "Option A / Option B / Option C" with no
  descriptions.
- ❌ Forgetting the "📝 Explain..." option.
- ❌ Asking multiple questions at once.
- ❌ Not exploring the codebase before asking a question that could be
  answered by reading a config file or source line.
- ❌ Turning adversarial. The goal is comprehension, not interrogation.

## Output

A running comprehension log in the conversation, ending with a final summary of
everything understood about the plan. No code is generated unless the user
explicitly asks for it after the session.
