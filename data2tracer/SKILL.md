---
name: data2tracer
description: >
  Lean, document-driven forensic orchestrator for complex UI/frontend codebases.
  Ingests user-provided outputs from the research skills (init, devrything,
  titan-forensic-architect, standard, project-status-brief, clarity-of-intent,
  knowledge). Conducts a strict one-question-at-a-time intent discovery interview,
  performs conditional source-file audits, and produces a validated, traceable
  implementation plan with checkboxes. 

  No automatic sub-skill execution. User supplies the forensic artifacts.
  Designed for speed, respect of prior research work, and maximum alignment
  through structured decision-making.
category: meta
risk: safe
source: user
tags: [meta-skill, forensic, ui, orchestrator, planning, interview, peacock, document-driven, v2]
allowed-tools: "*"
date_added: "2026-06-06"
version: "2.0 - Document Driven"
---

# Skill: data2tracer (Document-Driven v2)

## 1. Purpose
Automate the **research-to-validated-plan** pipeline for complex UI/frontend codebases **when the user supplies the forensic research documents**. 

This skill does **not** run init, devrything, titan-forensic-architect, standard, status-brief, clarity-of-intent, or knowledge. It ingests the documents **you** provide, surfaces the open decisions and orphaned components, runs a disciplined one-question-at-a-time interview to lock scope, design authority, success criteria, and component fate, optionally audits actual source files, and synthesizes everything into a clean, phased, checkboxed implementation plan that traces every task back to your explicit decisions.

## 2. When to Use
**Activate when the user:**
- Says phrases like "run the forensic orchestrator on these docs", "turn this research into a plan", "orchestrate from these outputs", or provides paths to the 7 core forensic artifacts
- Has already generated (or curated) the research documents and wants structured interview + decision architecture on top of them
- Wants to avoid re-running heavy research while still getting the full validated plan pipeline

**Do NOT activate when:**
- The user wants the agent to discover and run the research from scratch (use the original orchestrator or run skills manually)
- Single bug fix or hot-patch with no planning phase
- Fully structured spec already exists and user just wants code ("WRITE THE CODE" flow)

## 3. Required Context
User **must** provide:
- **Project root path** (e.g. `/root/hetzner/peacock-engine` or `/home/workdir/artifacts/...`)
- **Target scope** (e.g. "Neural Link UI + orphaned chat components", "entire frontend", "dashboard + settings screens")
- **Paths to the research documents** (the 7 core outputs). Can be supplied as a list, one-by-one, or referenced from previous context. The orchestrator will flag any critical missing pieces.

Critical documents:
1. AGENTS.md / init project context
2. devrything forensic directory map
3. titan-forensic-architect pipeline / technical manual
4. standard skill output (journal entries + instruction blocks)
5. project-status-brief current state snapshot
6. clarity-of-intent structured document
7. knowledge synthesis / cross-project knowledge

Optionally: specific source file paths for early audit, prior draft plans, or already-made decisions.

If documents are not provided up front, the orchestrator asks for the paths before any ingestion or synthesis begins.

## 4. Execution Flow

### Phase 0 — Document Ingestion & Validation (NEW — replaces auto sub-skill running)

This is the mandatory entry gate. No sub-skills are executed.

1. **Collect paths** — If not already supplied, ask the user for the file paths to the research documents (batch list preferred).
2. **Ingest & validate each document**:
   - Verify file exists and is readable.
   - Load full content into working context.
   - Emit a short confirmation: "✅ [Doc Type] loaded — [key signal, e.g. 4 screens, 3 orphaned components, 2 design conflicts]."
3. **Coverage & gap check**:
   - Confirm the 7 perspectives are represented.
   - If any critical document is missing or empty, immediately surface exactly which one and why it matters, then pause for the user to supply it.
4. **Ready signal** — Once all required documents are ingested and validated: "All provided research documents ingested and validated. No critical gaps. Proceeding to findings synthesis."

Only after clean Phase 0 completion does the flow move to Phase 1.

### Phase 1 — Research Ingestion & Finding Synthesis

Parse the ingested documents and categorize:

- **Technologies** — frameworks, libraries, build tools, versions, target platforms
- **Patterns** — architectural approaches, state management, routing, streaming, component models
- **Constraints** — non-negotiable design rules, API contracts, performance targets, security posture
- **Open Decisions / Orphaned Components / Known Failure Modes / Conflicting Design Systems**

Surface a **compact, high-signal summary** to the user. Explicitly list every unmade decision and every orphaned component found in the supplied research. 

**Do NOT proceed to the interview until the user acknowledges the summary is accurate.**

### Phase 2 — Intent Discovery (The Interview)

Strict one-question-at-a-time protocol. Wait for the answer before the next question. Never dump multiple questions in one turn.

**Mandatory question sequence:**

1. **Implementation Intent**  
   "Is this for active implementation right now, or do you want a reusable skill definition for future agents?"

2. **Scope Targeting**  
   "The research covers [X screens, Y prototypes, Z components, N failure modes, M orphaned pieces]. What should the plan focus on first?"

3. **Design Direction** (if scope includes UI work)  
   "Which design system or prototype source should be authoritative?"  
   - If user says "I don't know" → educational fallback: present the three common approaches (audit & pick, working code is truth, merge best of both) and ask which resonates.

4. **Success Criteria & Orphaned Components**  
   "What does 'done' look like? For the orphaned components surfaced in the research, should we integrate them, harvest their patterns only, or delete them?"

5. **Detailed Audit Trigger**  
   If user says "go over each part in detail", "audit the files", or similar → switch to Phase 3 file-by-file audit mode.

6. **Engineering & Polish**  
   Targeted questions on known issues from the research (error handling, loading states, scroll behavior, model selector, reconnection logic, memory leaks, config controls, file splitting, etc.).

**Interview rules (non-negotiable):**
- One question per turn.
- If partial answer → one sharpening follow-up, then move forward.
- "I don't know" → educational mode (2-3 clear approaches, ask which resonates).
- "Go over each part in detail" → enter Phase 3 granular audit mode.
- Keep tone conversational but precise. Real recognizes real.

### Phase 3 — Source File Audit (Conditional)

Triggered only when user requests granular decisions.

1. Read the actual source files referenced in the ingested research documents (pages, components, lib, api, styles).
2. For each file/section produce a mini-audit:
   - What works cleanly
   - What is broken / missing / has undefined references or broken CSS classes
   - Functional value if adopted
3. Present findings and ask per-component decision using the same three options: **adopt**, **harvest patterns only**, or **delete**.

### Phase 4 — Plan Synthesis

Once the interview is complete, synthesize into a phased implementation plan.

Every single task must map directly to a decision the user made during the interview.

**Required structure:**

```markdown
# [Project/Scope] Implementation Plan — [YYYY-MM-DD]
## Phase 1: Foundation & Research Cleanup
- [ ] Task 1 (traced to Decision X)
- [ ] Task 2 (traced to Decision Y)

## Phase 2: [Functional Area from user decisions, e.g. Component Adoption & Integration]
- [ ] ...

## Phase 3: Polish, Hardening & Edge Cases
- [ ] ...

## Phase N: Validation & Sign-off
- [ ] Lint / type-check passes
- [ ] Build succeeds
- [ ] Runtime verification on target scope
- [ ] Orphaned component decisions executed

## References
- Ingested documents: [list with paths]
- Key user decisions: [summary]
```

### Phase 5 — Validation Loop (Mandatory)

Present the synthesized plan and ask:

"Here's the plan I wrote based on our conversation and the documents you provided. Does this match what you need? You can tell me to:  
**(a)** add something I missed  
**(b)** remove or defer a phase  
**(c)** change the component split or task breakdown  
**(d)** approve and proceed"

Refine until the user explicitly confirms it is correct.

## 5. Decision Logic

| Condition                              | Action |
|----------------------------------------|--------|
| No project root or document paths      | Ask for them before ingesting anything |
| Document path invalid / file unreadable| Notify immediately with exact failure; ask for correction |
| Critical research document missing     | List exactly which one + why it matters; do not proceed until supplied |
| All required documents ingested & validated | Generate compact findings summary → wait for user ack → start Phase 2 interview |
| User says "I don't know" on design/authority | Educational mode: 2-3 clear approaches → ask which resonates |
| User says "go over each part in detail" or "audit the files" | Enter Phase 3 file-by-file audit mode |
| User approves final plan               | If intent = active implementation → ready for "WRITE THE CODE". If reusable skill → output full SKILL.md. Always save plan to disk with references. |
| Orphaned component or conflicting design system found | ALWAYS surface in summary and ask explicitly: adopt / harvest / delete? Never auto-decide. |
| User wants to skip interview           | Not allowed. The interview is the core value of this orchestrator. |

## 6. Output Format

Final deliverable is **always** the validated implementation plan in the checkbox markdown format above (unless user explicitly chose reusable skill output, in which case output a proper SKILL.md following the Agent Skills spec).

Include traceability section and references to the exact documents ingested.

## 7. Constraints & Guardrails

- **NEVER** hallucinate research findings or assume document contents. Always read the actual files the user provided.
- **ALWAYS** complete Phase 0 ingestion + validation before any synthesis or interview questions.
- **ALWAYS** ask exactly one question per turn in Phase 2.
- **ALWAYS** run the full validation loop (Phase 5) before considering any plan final.
- **ALWAYS** get explicit confirmation before recommending destructive actions (delete files, major refactors, breaking API changes).
- **NEVER** re-run the original forensic sub-skills (init, devrything, titan, standard, etc.) unless the user explicitly instructs it. This variant trusts the documents you are given.
- Keep final plan output focused and scannable. Move long file audits or examples to a `/references/` subdirectory when needed.
- Only begin implementation after user says "WRITE THE CODE" (or equivalent explicit green light) following plan approval.

## 8. Example Interaction (Document-Driven Flow)

**User:** "Run the forensic orchestrator on the Neural Link scope. Docs: AGENTS.md at /path/AGENTS.md, map at /path/devrything-map.md, titan at /path/titan-pipeline.md, standard at /path/standard-output.md, status at /path/status-brief.md, clarity at /path/clarity-intent.md, knowledge at /path/knowledge.md."

**Agent:**  
"Copy that locc. Ingesting your 7 documents now...

✅ AGENTS.md loaded — context, personas, core stack locked.  
✅ Forensic map loaded — 12 directories, 47 files, component locations mapped.  
✅ Titan pipeline docs loaded — full architecture flows + data contracts documented.  
✅ Standard journal loaded — 23 entries, 8 instruction blocks extracted.  
✅ Status brief loaded — current state + known failure modes captured.  
✅ Clarity-of-intent loaded — goals and success criteria structured.  
✅ Knowledge synthesis loaded — cross-project patterns + invariants integrated.

All documents validated. No critical gaps.

**Compact Research Summary (from your docs):**  
4 screens in scope, 3 orphaned components (ChatKernel, ModelSelectorV2, ScrollController), 2 conflicting design systems (legacy Tailwind vs shadcn/ui), 5 known failure modes (no reliable auto-scroll, flaky WS reconnection, inconsistent loading states, missing model selector in some flows, memory leak on rapid re-renders).

Unmade decisions surfaced: [list the 3-4 biggest ones with file references].

Does this summary match what you see in the research? Anything you want to correct or add before we lock intent?"

**User:** "Looks accurate. Proceed."

**Agent:** (Phase 2 begins — one question at a time)

"Is this for active implementation right now, or do you want a reusable skill definition for future agents?"

[Conversation continues exactly one question per turn until all decisions are collected, then Phase 4 plan synthesis, then Phase 5 validation loop.]

---

**End of Skill Definition**