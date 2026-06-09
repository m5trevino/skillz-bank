---
name: project-forensic-explainer
description: >
  Exhaustively documents a completed project by ingesting the entire codebase,
  mapping architecture, deep-diving every module, tracing data flows, and
  archaeologizing design decisions. Produces a massive, authoritative technical
  manual explaining every function, feature, mechanism, and rationale.
  Activate when a project is done and the user wants to understand,
  explain, or hand off everything about it.
category: meta
risk: safe
source: user
tags: [meta-skill, documentation, forensic, explainer, archaeology, manual]
allowed-tools: "*"
date_added: "2026-06-06"
---

# Skill: Project Forensic Explainer

## 1. Purpose

Produce a comprehensive, encyclopedic technical manual for a completed project.
This skill does not plan or build — it **explains**. It treats the codebase as
an archaeological site: every function, every component, every data flow, and
every design decision is excavated, catalogued, and explained.

The output answers four questions for every part of the project:
- **What is it?** — Name, location, responsibility
- **What does it do?** — Behavior, inputs, outputs, side effects
- **How does it work?** — Code walkthrough, control flow, state transitions
- **Why was it made this way?** — Design decisions, constraints, rejected alternatives

## 2. When to Use

**Activate when the user:**
- Says phrases like "explain this entire project", "document everything",
  "how does this all work", "why was this built this way", "handoff document",
  "I need to understand every part of this", or "archaeologize this codebase"
- A project is marked complete and needs exhaustive documentation
- A project is being handed off to another team or agent
- The user wants to create a reference manual for future maintenance

**Do NOT activate when:**
- The user wants a quick summary or high-level overview (use `project-status-brief`)
- The user wants to plan changes or fixes (use `peacock-forensic-orchestrator`)
- The user wants a single feature explained (use `pinpoint`)

## 3. Required Context

The user must provide:
- **Project root path** (e.g., `/root/hetzner/ai-engine`)
- Optionally: specific areas of focus if the project is massive

If the user does not provide a path, ask for it before proceeding.

## 4. Execution Flow

### Phase 1 — Project Ingestion

Read every document that explains intent and context:

1. `AGENTS.md` (or any `AGENTS.md` in subdirectories) — project conventions
2. `README.md` — project overview
3. `package.json` / `pyproject.toml` / `Cargo.toml` — dependencies and scripts
4. `tsconfig.json` / `vite.config.ts` / `tailwind.config.*` — build and type config
5. Any `DESIGN.md`, `DESIGN_CHANGES.md`, `DESIGN_BRIEF.md` — design system docs
6. Any `WIRING.md`, `BINDING_SPEC*.json` — integration specs
7. Any `docs/` directory contents
8. Any `.syndicate/` or `.kimi/` configuration
9. Any journal entries, chat logs, or instruction entries in the project

**Goal:** Build a complete picture of what the project is supposed to be,
what constraints govern it, and what decisions have already been made.

### Phase 2 — Architecture Mapping

Map the entire codebase structure:

1. **Directory tree** — Full recursive listing of all source files
2. **Entry points** — Identify every entry point (main.tsx, main.py, index.html, etc.)
3. **Module graph** — Trace imports/exports to build a dependency graph
4. **API surface** — List every route, endpoint, WebSocket, and SSE stream
5. **State boundaries** — Identify where state lives (React useState, Zustand,
   Redux, SQLite, ChromaDB, files, etc.)
6. **External boundaries** — List every external dependency, API, service, and gateway

For each significant file, record:
- Path
- Line count
- Type (page, component, hook, API client, utility, config, route, test)
- What imports it
- What it imports
- Confidence level (HIGH = runtime-verified, MEDIUM = design-doc inferred, LOW = prototype/stale)

### Phase 3 — Module Deep Dives

For every significant module, produce a forensic entry:

```markdown
### Module: `[relative/path/to/File.tsx]`

**What it is:** One-sentence identity.

**What it does:** Bullet list of responsibilities.

**How it works:**
- Step-by-step walkthrough of the primary function or render flow
- Key state variables and their lifecycles
- Event handlers and their side effects
- API calls and their payloads/responses
- Conditional branches and what triggers them

**Props / Interface:**
```typescript
interface Props { ... }
```

**Dependencies:** What it imports and why.

**Dependents:** What imports this file.

**Why it was made this way:**
- Design decision rationale (from AGENTS.md, DESIGN.md, or inferred from code)
- Constraints that shaped it
- Rejected alternatives (if documented)
- Known trade-offs

**Failure modes:** What can go wrong and how (or if) it's handled.
```

**Priority order for deep dives:**
1. Entry points (main.tsx, App.tsx, main.py)
2. Page components (top-level screens)
3. API client layer (api.ts, gateway files)
4. Reusable components (used by multiple pages)
5. Core utilities and hooks
6. Backend routes and services
7. Configuration and build files

### Phase 4 — Data Flow Traces

Trace complete end-to-end journeys through the system:

1. **User clicks a button → data appears** — Full request/response cycle
2. **User types a message → streaming response** — WebSocket or SSE flow
3. **File upload → processing → result** — Multi-step pipeline
4. **Background job → state update → UI refresh** — Async flow
5. **External API call → error → retry** — Failure and recovery flow

For each trace:
```markdown
### Flow: [Name]
**Trigger:** User action or system event
**Path:**
1. `FileA.tsx:42` — handler invoked
2. `api.ts:123` — POST request sent
3. `routes/foo.py:89` — backend handler
4. `core/bar.py:156` — business logic
5. `api.ts:145` — response received
6. `FileB.tsx:67` — state updated
7. `FileC.tsx:12` — UI re-renders

**State mutations:** What changes and when
**Side effects:** What else happens (logs, files, external calls)
**Error paths:** What happens if any step fails
```

### Phase 5 — Decision Archaeology

Extract and document WHY the project is the way it is:

1. **Read version control** (if available) — `git log`, commit messages,
   merge history to trace evolution
2. **Read journal entries** — Any `JE-` or `IE-` entries from the `standard` skill
3. **Read design docs** — `DESIGN.md`, `DESIGN_CHANGES.md`, `AVIARY_DESIGN_BRIEF.md`
4. **Read AGENTS.md decisions** — Pivots, rejections, adopted patterns
5. **Infer from code** — When no document explains a choice, infer from structure

For each major decision:
```markdown
### Decision: [Name]
**What was decided:** One sentence
**When:** Date or phase (if known)
**Why:** Rationale from documents or inference
**Rejected alternatives:** What was considered and why it was passed over
**Consequences:** How this decision shaped the codebase
**Confidence:** HIGH (documented) / MEDIUM (inferred) / LOW (speculative)
```

### Phase 6 — Design System Documentation

If the project has a UI, exhaustively document the design system:

1. **Color tokens** — Every color variable, hex value, and semantic usage
2. **Typography** — Every font, size, weight, tracking, and when to use it
3. **Spacing** — Grid, gaps, padding, margins, layout constants
4. **Components** — Every reusable component, its props, and its variants
5. **Animations** — Every transition, keyframe, and motion pattern
6. **Icons** — Icon system, sizes, and usage rules
7. **Breakpoints** — Responsive behavior at every breakpoint

### Phase 7 — Synthesis

Combine everything into a single massive document or a structured directory:

```
project-manual/
├── 00-EXECUTIVE-SUMMARY.md
├── 01-ARCHITECTURE-MAP.md
├── 02-MODULE-DEEP-DIVES/
│   ├── 02.01-Entry-Points.md
│   ├── 02.02-Pages.md
│   ├── 02.03-Components.md
│   ├── 02.04-API-Client.md
│   ├── 02.05-Backend-Routes.md
│   └── ...
├── 03-DATA-FLOW-TRACES.md
├── 04-DECISION-ARCHAEOLOGY.md
├── 05-DESIGN-SYSTEM.md
├── 06-API-REFERENCE.md
├── 07-KNOWN-ISSUES.md
└── 08-HANDOFF-NOTES.md
```

**Each section must be exhaustive.** Do not summarize for brevity.
The user asked for "large detailed output" — deliver it.

### Phase 8 — Validation

Present the document structure and ask:

> "I have produced a comprehensive manual for [Project X]. It contains [N] sections
> and [M] module deep dives. Would you like me to:
> **(a)** expand a specific section,
> **(b)** add a section I missed,
> **(c)** reformat the output (single file vs. directory),
> or **(d)** approve and save it?"

## 5. Decision Logic

| Condition | Action |
|-----------|--------|
| User provides no project path | Ask for project root path before proceeding |
| Project has no `AGENTS.md` | Run the `init` skill first to generate project context |
| Project has design docs (`DESIGN.md`, etc.) | Extract and preserve verbatim design rules and decisions |
| Project has journal entries (`standard` skill outputs) | Use them as primary source for "why" explanations |
| Code has no comments or docs | Infer purpose from function names, prop types, and usage patterns |
| A module is imported by many files | Prioritize it in the deep-dive queue |
| A module imports many files | Deep-dive it early to understand integration patterns |
| User asks for a specific area only | Skip Phase 2 broad mapping and focus only on the requested modules |

## 6. Output Format

The default output is a **directory of markdown files** named `project-manual/`
in the project root. Each file is a standalone document.

If the user prefers a **single massive file**, concatenate all sections with
clear headers and a table of contents.

**Minimum viable sections:**
- Executive Summary
- Architecture Map
- Module Deep Dives (all significant files)
- Data Flow Traces (all major user journeys)
- Decision Archaeology (all documented pivots and choices)
- API Reference (all endpoints, methods, types)
- Known Issues and Workarounds
- Handoff Notes for future maintainers

## 7. Constraints & Guardrails

- **NEVER** skip a significant module because it seems "boring." Every file
  that is imported by the app gets a deep dive.
- **NEVER** hallucinate design decisions. If no document explains why something
  was built a certain way, mark the explanation as INFERRED and state the
  confidence level.
- **ALWAYS** include function signatures, prop interfaces, and type definitions
  verbatim from the source code.
- **ALWAYS** trace imports backward (who uses this?) and forward (what does this use?).
- **NEVER** produce a high-level summary when the user asked for exhaustive detail.
- **ALWAYS** save the output to disk. Do not keep it only in the conversation context.
- **ALWAYS** include a "Known Issues" section documenting bugs, tech debt, and
  orphaned code found during the audit.

## 8. Example Interaction

**User:** "Explain the entire Peacock Engine UI — every function, every feature,
how it works, and why it was made that way. Large output."

**Agent:** *(Phase 1 — ingests AGENTS.md, README, package.json, DESIGN.md, etc.)*

**Agent:** *(Phase 2 — maps directory tree, entry points, module graph)*
> "Mapping 28 source files, 18 React components, 47 API methods, 14 backend
> routers, 2 streaming endpoints, and 1 WebSocket..."

**Agent:** *(Phase 3 — deep dives every module)*
> "Documenting `App.tsx`: tab router, 6 screens, no React Router..."
> "Documenting `api.ts`: 375 lines, 6 domain APIs, WebSocket factory..."
> "Documenting `NeuralLink.tsx`: dual streaming, 3-panel layout..."

**Agent:** *(Phase 4 — traces data flows)*
> "Tracing: User sends chat message → REST SSE path..."
> "Tracing: User sends chat message → WebSocket path..."
> "Tracing: Dashboard telemetry loading..."

**Agent:** *(Phase 5 — decision archaeology)*
> "Decision: Framework pivot from Alpine.js to React+Vite (JE-003)..."
> "Decision: Rejection of dark glassmorphism (JE-002)..."
> "Decision: Tab-based routing instead of React Router (Clarity-of-Intent)..."

**Agent:** *(Phase 6 — design system docs)*
> "Color tokens: 33 custom Tailwind variables..."
> "Typography: Space Grotesk / Inter / JetBrains Mono..."

**Agent:** *(Phase 7 — synthesizes and saves)*
> "Manual complete. Saved to `ai-engine/project-manual/` with 8 sections
> and 28 module deep dives."

**Agent:** *(Phase 8 — validation)*
> "Would you like me to (a) expand a section, (b) add a missing topic,
> (c) reformat, or (d) approve?"

**User:** "Expand the Neural Link data flow traces."

**Agent:** *(Expands Section 3 with additional sequence diagrams, state
machine descriptions, and edge case handling.)*
