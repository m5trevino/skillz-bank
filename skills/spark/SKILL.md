---
name: spark
description: >
  Three-phase project inception skill that guides you from raw idea to
  execution-ready plan. Phase 1 diverges — brainstorms the opportunity space,
  user needs, and creative approaches (Jobs-to-be-Done, Opportunity Solution
  Trees). Phase 2 converges — stress-tests every assumption with pre-mortems,
  trade-off analysis, and Shape Up appetite sizing. Phase 3 locks — produces
  a phased delivery plan with risk register, tech decisions, and success
  criteria. One question at a time. 3+ concrete options + "Explain..." per
  question. Activates when the user says "spark this", "incept this project",
  "greenfield this", or "start from scratch".
category: planning
risk: safe
source: community
tags:
  - inception
  - brainstorming
  - planning
  - interrogation
  - shape-up
  - project-start
  - mvp
  - jtbd
  - pre-mortem
allowed-tools: "*"
date_added: "2026-06-10"
---

# spark — Project Inception Engine

## Purpose

Turn a raw, unformed idea into a validated, sequenced, execution-ready project
plan. Three distinct phases, one question at a time:

- **Phase 1: Brainstorm** — Diverge. Map the opportunity space, understand the
  user, explore approaches. Uses JTBD, Opportunity Solution Trees, and north
  star thinking.
- **Phase 2: Interrogate** — Converge and stress-test. Pre-mortem the plan,
  appetite-size the scope, challenge trade-offs. Uses Shape Up, risk-first
  analysis, and lean MVP definition.
- **Phase 3: Plan** — Lock and structure. Produce a phased delivery plan with
  tech decisions, risk register, milestones, and clear success criteria.

## When to Use

**Activate when the user says:**
- "spark this" / "spark a project"
- "incept this project" / "project inception"
- "greenfield this idea"
- "start from scratch"
- "turn this idea into a plan"
- "I have an idea for a project"
- "where do I start with this idea"
- "brainstorm and plan this"

**Do NOT activate when:**
- The user already has a complete, validated plan and just wants execution
- The user wants a single code snippet or immediate bug fix
- The user wants a pure creative brainstorm with no execution intent
- The request is purely conversational with no project or idea to develop

## How It Works

### Phase 1: Brainstorm (Divergent)

Explore the opportunity space before converging on any one path. Each question
broadens understanding.

**Question sequence (one per turn):**

1. **Core problem** — "What's the problem or opportunity you're trying to
   address? Who feels the pain, and how do they experience it today?"
   *(JTBD framing: what job are they hiring your solution to do?)*

2. **User & context** — "Who's the primary user? What's their context,
   capabilities, and constraints? Is this for yourself, a team, or
   customers?"

3. **Approach landscape** — "What are 2-3 fundamentally different ways this
   could be solved? Don't judge yet — just map the possibility space."
   *(Opportunity Solution Tree: multiple paths to the outcome)*

4. **North star** — "If this succeeds wildly in 12 months, what does that
   look like? What's the one thing that must be true for you to call it a
   win?"

5. **Riskiest assumption** — "Of everything we've discussed, what single
   assumption would hurt most if it's wrong? What do we need to validate
   first?"

**Transition gate:** After Phase 1, summarise the opportunity space and ask:
"Does this capture the landscape accurately? Ready to stress-test and
converge?"

### Phase 2: Interrogate (Convergent + Stress-Test)

Challenge every assumption. Try to break the idea before it costs real time.

**Question sequence (one per turn):**

1. **Why this approach?** — "Of the approaches we mapped, you seem to lean
   toward [X]. Why this one over the others? What's the specific bet you're
   making?"

2. **Pre-mortem** — "Imagine it's 12 months from now and this project failed
   completely. What went wrong? Be specific — technical, market, team,
   timing."

3. **Appetite & scope** — "How much time/energy/resources is this worth
   before you'd reconsider? What's the appetite? If we had to ship something
   useful in half that time, what would we cut?"
   *(Shape Up: fixed appetite, variable scope)*

4. **Trade-off tension** — "What's the hardest trade-off in this project?
   Speed vs quality? Features vs simplicity? Custom vs off-the-shelf?"

5. **Edge cases & unknowns** — "What do we not know yet that could change
   everything? What would force a pivot or a kill?"

**Transition gate:** After Phase 2, summarise the locked-in bets and surviving
assumptions. Ask: "Ready to structure this into a plan?"

### Phase 3: Plan (Structured Output)

Lock decisions into a concrete, phased delivery plan.

**Question sequence (one per turn):**

1. **Phasing** — "How should we slice the work? What's the first thing a user
   needs to be able to do? What comes after?"
   *(Thinnest vertical slice first, then expand)*

2. **Tech foundation** — "Any strong opinions on tech stack, platform, or
   infrastructure? Constraints from the ecosystem or team skills?"

3. **Milestones & signals** — "What are 3-4 concrete milestones that show
   real progress? What does 'done' look like at each?"

4. **Risks to track** — "From the pre-mortem, which 2-3 risks deserve
   explicit mitigations in the plan? How will we know if they're
   materialising?"

## Question Format

Every question MUST use `AskUserQuestion` with this exact shape:

- **Question text:** Clear, specific, framed for the current phase.
  Brainstorm = curious and open. Interrogate = sharp and challenging.
  Plan = structured and concrete.
- **3 or more concrete options:** Your best interpretations based on
  everything the user has said so far. Each option has a brief label (1-5
  words) and a one-line description.
- **Last option:** Always labeled `📝 Explain...` — lets the user type their
  own answer or elaborate.

### Example (Phase 1 — Brainstorm):

```
Question: What's the core problem you're trying to solve? Who feels it
today, and what do they do instead?

1. Personal pain I'm solving for myself — I've hit this wall repeatedly.
2. Observed market gap — I've seen others struggle with it.
3. Technical challenge I want to explore — The problem is the fun part.
4. 📝 Explain... — Describe the problem in your own words.
```

### Example (Phase 2 — Interrogate):

```
Question: Imagine it's 12 months from now and this project failed. What
was the cause?

1. We built something nobody actually needed — Misread the real problem.
2. Scope ballooned and we never shipped — Too many features, no focus.
3. Technical approach hit a dead end — Wrong stack or missing capability.
4. 📝 Explain... — Describe your own failure scenario.
```

### Example (Phase 3 — Plan):

```
Question: What's the thinnest vertical slice a user could interact with
and get value?

1. A CLI tool that does one thing well — Fastest to ship, proves the core.
2. A minimal web UI with the key action — More visible, more investment.
3. An API endpoint + integration test — If this is a library/platform play.
4. 📝 Explain... — Describe the first slice in your own words.
```

## Industry Practices Incorporated

| Practice | Where it appears |
|----------|-----------------|
| Jobs-to-be-Done | Phase 1, Q1 — framing the problem as a job |
| Opportunity Solution Tree | Phase 1, Q3 — multiple solution paths |
| Shape Up (appetite) | Phase 2, Q3 — fixed appetite, variable scope |
| Pre-mortem | Phase 2, Q2 — fail before you build |
| Lean MVP / RAT | Phase 1, Q5 — riskiest assumption test |
| Wardley Mapping | Phase 2, Q5 — unknown unknowns |
| RFC / ADR | Phase 3 output — tech decisions documented |
| User Story Mapping | Phase 3, Q1 — slicing by user value |
| DACI / RACI | Phase 1, Q2 — who decides |
| Dunning-Kruger check | Phase 2, Q1 — why THIS approach |

## Rules

- **One question at a time.** Never fire two questions in a row. Wait for the
  answer.
- **Always provide 3+ concrete options** plus the "📝 Explain..." escape hatch.
- **Explore first.** If the question can be answered by grepping the codebase,
  reading a file, or checking configs, do that instead of asking.
- **Phase-appropriate tone:**
  - Phase 1: Curious, expansive, non-judgmental.
  - Phase 2: Sharp, challenging, adversarial.
  - Phase 3: Structured, pragmatic, forward-looking.
- **After each answer, write a 1-line summary** to confirm understanding.
  Build a running inception log.
- **If the user picks "📝 Explain...",** treat their text as the source of
  truth, summarise it, and ask a gentle follow-up to lock down ambiguity.
- **At each phase transition**, summarise what was learned and confirm before
  proceeding.
- **Stop when:** the user says "good", "done", "that's enough", or all three
  phases are complete. Deliver the final inception document.
- **If the idea is clearly bad** (pre-mortem hits a fatal flaw early), say so
  directly. "Spark" is not a cheerleader — it kills bad ideas fast.

## Common Mistakes

- ❌ Skipping Phase 1 and jumping straight to interrogation. Let the idea
  breathe first.
- ❌ Asking open-ended text questions instead of structured options.
- ❌ Giving vague options with no real trade-offs in Phase 2.
- ❌ Forgetting the "📝 Explain..." option.
- ❌ Asking multiple questions at once.
- ❌ Being too nice in Phase 2 — the user wants you to try to break it.
- ❌ Being too adversarial in Phase 1 — kills creativity before it starts.
- ❌ Skipping the phase transition confirmations — the user might want to
  loop back.
- ❌ Not exploring the codebase before asking discoverable questions.
- ❌ Outputting a generic plan template instead of one tailored to the
  specific answers.

## Output

A **Project Inception Document** synthesised from all three phases, saved as
`INCEPTION.md` in the project root (or a path the user specifies):

```markdown
# [Project Name] — Inception

## Phase 1: Opportunity Space
- Core problem / JTBD
- Primary user & context
- Approaches considered
- North star vision
- Riskiest assumption

## Phase 2: Stress-Test Results
- Why this approach
- Pre-mortem findings
- Appetite & scope boundary
- Trade-offs accepted
- Known unknowns

## Phase 3: Delivery Plan
- Phased breakdown (vertical slices)
- Tech foundation decisions
- Milestones & success signals
- Risk register with mitigations

## Decision Log
All locked-in decisions from the session, one per line.
```

The document traces every decision back to the question that produced it.
No plan template is ever dumped generically — every section is written from
the actual answers given.
