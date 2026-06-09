---
name: ingest-n-plan
description: >
  Meta-skill that transforms unstructured research notes into production-ready
  agent skill definitions. Activate when the user pastes articles, exploration
  notes, technology comparisons, or raw links and asks to "turn this into a skill",
  "build a skill from my research", "create an implementation guide", or
  "package this into a skill". Parses technologies, patterns, constraints, and
  open questions; conducts a one-question-at-a-time intent discovery interview;
  outputs a complete SKILL.md with execution flow, decision logic, guardrails,
  and example interactions. Never activate for single-file code requests or
  bug fixes.
category: meta
risk: safe
source: community
tags: [meta-skill, skill-authoring, research, interview, generator, workflow]
allowed-tools: "*"
date_added: "2026-05-28"
---

# skill-architect

## Purpose

Interview users about their research and development intent, then synthesize a
complete, production-ready agent skill definition (SKILL.md) that any coding
agent can execute cold.

## When to Use

**Activate when the user:**
- Pastes research notes, article snippets, links, or summaries about technologies
  or patterns
- Says phrases like "turn this into a skill", "build a skill from my research",
  "create an implementation guide", "package this", or "I want a skill that..."
- Provides exploratory content with uncertainty ("considering GraphRAG",
  "might use Redis", "unsure about auth")

**Do NOT activate when:**
- The user asks for a single code snippet or immediate bug fix
- The user provides a fully structured spec and only wants coding
- The request is purely conversational with no research content or skill intent

## Required Context

The user must provide at least one of:
- Unstructured research notes, article summaries, or pasted content
- A rough idea of what they want the skill to do
- Target domain or technology names

## Execution Flow

### Phase 1: Research Intake

1. Parse the user's input and categorize into:
   - **Technologies** — libraries, frameworks, platforms mentioned
   - **Patterns** — architectural approaches, design patterns, workflows
   - **Constraints** — limitations, requirements, non-negotiables
   - **Open Questions** — decisions not yet made ("considering X", "unsure about Y")
2. Surface the categorized findings to the user in a compact summary.
3. Highlight any items that sound like unmade decisions — these become interview
   targets.

### Phase 2: Intent Discovery (The Interview)

Ask **one question at a time**. Wait for the answer before proceeding.

**Question categories to cycle through:**
1. **Implementation Intent** — Is this for active implementation or exploration?
2. **Approach Clarity** — Do they know how to integrate it, or need guidance?
3. **Scope & Constraints** — Prototype, MVP, or production? Timeline?
4. **Integration Context** — Current stack, language, framework, existing DB?
5. **Success Criteria** — What does "done" look like? Output format? Thresholds?
6. **Edge Cases & Failure Modes** — What should happen when things go wrong?

**Interview rules:**
- If user says **"I don't know"** → Switch to educational mode: explain 2–3
  common approaches, ask which resonates.
- If user says **"No / Not yet"** → Ask if they want a *research tracker*
  instead of an *implementation guide*.
- If user gives a **partial answer** → Ask one sharpening follow-up, then move on.
- Keep tone conversational. One question per turn.

See `references/interview-questions.md` for the full question bank and branching
logic.

### Phase 3: Skill Generation

Once the interview is complete, synthesize everything into a skill definition
with these exact sections:

```markdown
# Skill: [Descriptive Name]

## 1. Purpose
One-sentence what this skill does.

## 2. When to Use
Trigger conditions (user mentions X, asks for Y, pastes Z).

## 3. Required Context
What the user must provide (API keys, file paths, schema, etc.).

## 4. Execution Flow
Step-by-step logic the skill follows.

## 5. Decision Logic
Branching rules (if A then B, if user says C then D).

## 6. Output Format
Exactly what the skill produces (code, markdown, JSON, questions, etc.).

## 7. Constraints & Guardrails
What the skill must NEVER do.

## 8. Example Interaction
A sample back-and-forth showing the skill in action.
```

### Phase 4: Validation Loop

Present the generated skill and ask:

> "Here's the skill I wrote based on our conversation. Does this match what you
> need? You can tell me to: **(a)** make it more detailed, **(b)** simplify it,
> **(c)** change the output format, or **(d)** add a section I missed."

Refine until the user confirms it is correct.

## Core Patterns

### Pattern 1: Research-to-Decision Mapping

When the user pastes raw research, extract decision signals and present them
as a checklist before interviewing:

```markdown
I see these technologies: [list]
These patterns: [list]
These open decisions: [list]

Let's resolve the decisions first. [Ask first question]
```

### Pattern 2: Educational Fallback

When the user lacks clarity, provide structured options instead of forcing
a choice:

```markdown
There are three common approaches:
1. [Approach A] — best when [condition]
2. [Approach B] — best when [condition]
3. [Approach C] — best when [condition]

Which sounds closest to your situation? Or should the skill walk you through
choosing?
```

### Pattern 3: Stack-Agnostic to Stack-Specific Transition

Start with generic questions. Only ask stack-specific questions after
confirming implementation intent:

```markdown
- Generic: "Is this for a prototype, MVP, or production system?"
- Specific: "What language and framework are you using?"
- Deep: "Do you have an existing database or vector store?"
```

## Common Mistakes

### CRITICAL: Hallucinating Implementation Details

Wrong:
> "I'll assume you're using React with TypeScript and Node.js on the backend."

Correct:
> "What does your current stack look like? I need to know language, framework,
> and any existing database before I can design the skill."

Reason: Assumed stack produces a skill that fails in the user's actual
environment.

### HIGH: Generating the Skill Before Completing the Interview

Wrong:
> "Based on your first answer, here's the full skill..."

Correct:
> "Got it. One more question: [next interview question]. I need to understand
> [topic] before I can write an accurate skill."

Reason: Incomplete context produces incomplete or misaligned skills.

### HIGH: Skipping the Validation Loop

Wrong:
> "Skill complete. Here it is."

Correct:
> "Here's the skill I wrote. Does this match what you need? Tell me to make it
> more detailed, simplify it, change the format, or add a missing section."

Reason: Without user confirmation, subtle misalignments propagate.

### MEDIUM: Asking Multiple Questions at Once

Wrong:
> "What's your stack, timeline, and what does done look like?"

Correct:
> "What does your current stack look like? (Language, framework, existing DB)"

Reason: Multiple questions reduce answer quality and break conversational flow.

## Constraints & Guardrails

- **NEVER** hallucinate implementation details the user did not confirm.
- **ALWAYS** ask before assuming stack, scale, or security posture.
- **ALWAYS** include a mandatory confirmation step in generated skills that take
  actions (run code, call APIs, modify files).
- **NEVER** skip the validation loop at the end.
- **ALWAYS** keep SKILL.md output under 500 lines; move detailed examples and
  checklists to `references/`.
- **NEVER** ask more than one question per turn during the interview.

## Output Format

The final deliverable is a complete, copy-paste-ready skill definition formatted
as Markdown with YAML frontmatter, following the Agent Skills specification.

## References

- `references/interview-questions.md` — Full question bank with branching logic
- `references/example-interaction.md` — Complete sample back-and-forth
