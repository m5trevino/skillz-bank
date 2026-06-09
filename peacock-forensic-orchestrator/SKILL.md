---
name: peacock-forensic-orchestrator
description: >
  Orchestrates a complete forensic analysis of a UI codebase by running multiple
  research skills (init, devrything, titan, standard, status-brief, clarity-of-intent,
  knowledge), ingests their outputs, conducts a one-question-at-a-time intent
  discovery interview, audits source files, and produces a validated implementation
  plan. Activates when the user wants to turn a codebase into actionable plans
  through automated research + structured decision-making.
category: meta
risk: safe
source: user
tags: [meta-skill, forensic, ui, orchestrator, planning, interview, peacock]
allowed-tools: "*"
date_added: "2026-06-06"
---

# Skill: Peacock Forensic Orchestrator

## 1. Purpose

Automate the full research-to-plan pipeline for a complex UI/frontend codebase.
This skill does not just read documents — it **runs the forensic skills** that
produce the documents, ingests their outputs, interviews the user one question
at a time, audits source files, and synthesizes a validated implementation plan.

## 2. When to Use

**Activate when the user:**
- Says phrases like "run the forensic orchestrator", "analyze and plan this UI",
  "do the full workflow", "turn this codebase into a plan", or references
  multiple forensic skills at once
- Wants the agent to both research the codebase AND produce an actionable plan
- Has a complex project (like Peacock Engine) with multiple screens, design
  systems, and orphaned components

**Do NOT activate when:**
- The user wants a single bug fix with no research phase
- The user provides a fully structured spec and only wants coding
- The user explicitly says to skip research and go straight to implementation

## 3. Required Context

The user must provide:
- **Project root path** (e.g., `/root/hetzner/ai-engine`)
- **Target scope** (e.g., "UI layer", "Neural Link", "entire frontend")
- Optionally: existing research documents to skip re-generation

If the user does not provide a project path, ask for it before proceeding.

## 4. Execution Flow

### Phase 0 — Sub-Skill Orchestration (Run the Skills)

The orchestrator MUST run the following skills in order. Each skill produces
an output document. The orchestrator reads each output before proceeding to the
next skill.

**Skill execution order:**

| # | Skill | Trigger Phrase | Output Document |
|---|-------|---------------|-----------------|
| 1 | `init` | "Init this project" | `AGENTS.md` + project context |
| 2 | `devrything` | "Map this directory" | Forensic directory map |
| 3 | `titan-forensic-architect` | "Generate technical manual" | Pipeline architecture docs |
| 4 | `standard` | "Process this chat" | Structured journal + instructions |
| 5 | `project-status-brief` | "Project status brief" | Current state snapshot |
| 6 | `clarity-of-intent` | "Clarify intent" | Structured intent document |
| 7 | `knowledge` | "Promote knowledge" | Cross-project knowledge synthesis |

**Execution rules:**
1. Check if skill outputs already exist in the project directory.
2. If outputs exist AND are recent (modified within last 7 days), read them.
3. If outputs do not exist or are stale, **run the skill** by loading its
   `SKILL.md` and following its execution flow.
4. After each skill completes, read its output document into context.
5. Only proceed to the next skill after the current skill's output is ingested.

**How to run a sub-skill:**
- Read the sub-skill's `SKILL.md` from `/root/.kimi/skills/[skill-name]/SKILL.md`
- Follow its instructions exactly as if the user had triggered it
- Capture its output (usually a `.md` file or terminal output) and save it to
  the project's working directory for reference

### Phase 1 — Research Ingestion

After all 7 skills have run and their outputs are read:

1. **Parse all outputs** and categorize findings:
   - **Technologies** — frameworks, libraries, build tools, versions
   - **Patterns** — architectural approaches, state management, routing, streaming
   - **Constraints** — non-negotiable design rules, API contracts, build targets
   - **Open Decisions** — unmade choices, conflicting design systems, orphaned code,
     missing features, known failure modes
2. **Surface a compact summary** to the user. Highlight every unmade decision
   and every orphaned component.
3. **Do NOT proceed** to Phase 2 until the user acknowledges the summary.

### Phase 2 — Intent Discovery (The Interview)

Use `AskUserQuestion` **one question at a time**. Wait for the answer before
proceeding. Never ask more than one question per turn.

**Question sequence (mandatory order):**

1. **Implementation Intent**
   > "Is this for active implementation right now, or do you want a reusable
   > skill definition for future agents?"

2. **Scope Targeting**
   > "What is the immediate scope? The research covers [X screens, Y prototypes,
   > Z components, N failure modes]. What should the plan focus on?"

3. **Design Direction** (if scope includes UI work)
   > "Which design system or prototype source should be authoritative?"
   - If user says **"I don't know"** → Educational fallback:
     > "There are three common approaches:
     > 1. [Audit prototypes and present a curated pick]
     > 2. [Working code is truth — polish first, reskin later]
     > 3. [Merge best of prototypes + working code]
     > Which resonates?"

4. **Success Criteria**
   > "What does 'done' look like? Should we integrate orphaned components,
   > delete them, or harvest their patterns?"

5. **Detailed Audit** (if user requests detail)
   > "I will now inspect the actual source files and present a per-component
   > audit. We will decide on each part individually."
   - Read the relevant source files (pages, components, lib, api)
   - For each file/section, ask: adopt, harvest patterns, or delete?

6. **Engineering & Polish**
   > Ask about specific fixes: error handling, loading states, scroll behavior,
   > config controls, file splitting, reconnection logic, memory leaks.

**Interview rules:**
- If user gives a **partial answer** → Ask one sharpening follow-up, then move on.
- If user says **"go over each part in detail"** → Switch to file-by-file audit
  mode. Read sources, present findings, ask per-component decisions.
- If user says **"I don't know"** → Switch to educational mode: explain 2–3
  common approaches, ask which resonates.
- Keep tone conversational. One question per turn.

### Phase 3 — Source File Audit (Conditional)

If the interview reveals the need for granular decisions:

1. Read the actual source files referenced in the research documents.
2. For each file, produce a mini-audit:
   - What works
   - What is broken / missing
   - Functional value if adopted
   - Broken CSS classes or undefined references
3. Present findings and ask per-file decisions using `AskUserQuestion`.

### Phase 4 — Plan Synthesis

Once the interview is complete, synthesize everything into a phased
implementation plan:

```markdown
## [Project Name] Implementation Plan

### Phase 1: [Name]
- [ ] Task 1
- [ ] Task 2

### Phase 2: [Name]
- [ ] Task 3
- [ ] Task 4

### Phase N: Validation
- [ ] Lint passes
- [ ] Build succeeds
- [ ] Runtime verification
```

Every phase must map directly to a user decision from the interview.

### Phase 5 — Validation Loop

Present the plan and ask:

> "Here's the plan I wrote based on our conversation. Does this match what you
> need? You can tell me to: **(a)** add something I missed, **(b)** remove or
> defer a phase, **(c)** change the component split, or **(d)** approve and start
> implementation."

Refine until the user confirms it is correct.

## 5. Decision Logic

| Condition | Action |
|-----------|--------|
| User provides no project path | Ask for project root path before running any skills |
| Sub-skill outputs already exist and are fresh | Read existing outputs; do not re-run the skill |
| Sub-skill outputs are stale or missing | Run the skill by loading its SKILL.md and executing its flow |
| User says "I don't know" | Switch to educational mode: explain 2–3 common approaches, ask which resonates |
| User says "go over each part in detail" | Enter file-by-file audit mode. Read sources, present per-component decisions |
| User says "plan right now" | Treat as active implementation planning, not skill generation |
| Orphaned components found | Always ask: adopt, harvest patterns, or delete. Never assume |
| Conflicting design systems found | Present the conflict, ask which is authoritative, document the rejection |
| User approves the plan | Begin implementation immediately (if intent was active) or save plan to disk |

## 6. Output Format

The final deliverable is a **validated implementation plan** formatted as
Markdown with checkboxes. If the user requested a reusable skill definition
instead of immediate implementation, output a `SKILL.md` following the Agent
Skills specification.

**Plan structure:**
```markdown
# [Project] Implementation Plan

## Phase 1: Foundation & Cleanup
## Phase 2: [Functional Area]
## Phase 3: [Functional Area]
## Phase N: Validation
```

## 7. Constraints & Guardrails

- **NEVER** hallucinate implementation details the user did not confirm.
- **ALWAYS** run the sub-skills if outputs are missing or stale. Do not skip research.
- **ALWAYS** ask before assuming stack, scale, or security posture.
- **ALWAYS** read actual source files before asking users to decide on them.
- **NEVER** ask more than one question per turn during the interview.
- **NEVER** skip the validation loop at the end.
- **ALWAYS** include a mandatory confirmation step before destructive actions
  (deleting files, running builds, modifying API contracts).
- **ALWAYS** keep output under 500 lines; move detailed examples to
  `references/`.

## 8. Example Interaction

**User:** "Run the forensic orchestrator on the ai-engine project."

**Agent:** *(Phase 0 — runs sub-skills)*
> "Running init... done. AGENTS.md generated.
> Running devrything... done. Forensic map generated.
> Running titan-forensic-architect... done. Pipeline docs generated.
> Running standard... done. Journal entries extracted.
> Running project-status-brief... done. Status snapshot generated.
> Running clarity-of-intent... done. Intent document generated.
> Running knowledge... done. Knowledge synthesis complete."

**Agent:** *(Phase 1 — ingests all outputs, presents summary)*
> "Research complete. I found 6 screens, 4 orphaned components, 3 conflicting
> design systems, and 9 known failure modes. Unmade decisions: [list]."

**Agent:** *(Phase 2 — Question 1)*
> "Is this for active implementation right now, or do you want a reusable skill?"

**User:** "Plan right now."

**Agent:** *(Question 2)*
> "What is the immediate scope?"

**User:** "Neural Link and best designs."

**Agent:** *(Question 3)*
> "Which design prototypes should be authoritative?"

**User:** "I'm not sure yet."

**Agent:** *(Educational fallback — Question 4)*
> "Three approaches: [audit prototypes], [working code is truth], [merge best].
> Which resonates?"

**User:** "Working code is truth — polish first, reskin later."

**Agent:** *(Question 5)*
> "What does 'done' look like for the orphaned components?"

**User:** "Go over each part in detail."

**Agent:** *(Phase 3 — reads source files, presents per-file audit)*
> "Working code has 9 issues: no scroll, no model selector, WS hack..."
> "Orphaned ChatKernel has scroll-to-bottom and empty state..."

**Agent:** *(Per-file questions)*
> "ChatKernel — adopt, harvest, or delete?"

**User:** "Harvest the pattern only."

**Agent:** *(Continues per-file until all decisions are collected)*

**Agent:** *(Phase 4 — synthesizes plan)*
> "## Neural Link Polish Plan — 6 Phases..."

**Agent:** *(Phase 5 — validation)*
> "Does this match what you need? (a) add, (b) remove, (c) change, (d) approve."

**User:** "Approve."

**Agent:** *(Begins implementation.)*
