# Interview Question Bank

## Decision Tree

```
Start
├── User says "just exploring" or "not yet"
│   └── Offer: research-tracker skill vs. implementation-guide skill
├── User says "active project" or "implementing"
│   └── Ask: "Do you already know how you want to integrate it?"
│       ├── "Yes"
│       │   └── Ask stack-specific questions
│       ├── "No" / "I don't know"
│       │   └── Educational mode: present 2-3 approaches
│       └── "Partially"
│           └── One sharpening follow-up, then proceed
└── User gives vague or mixed signals
    └── Ask: "Is this for a prototype, MVP, or production system?"
```

## Question Categories

### 1. Implementation Intent

- "You researched [topic]. Do you plan to implement this in the current project,
  or were you just exploring?"
- "Is this something you need to build now, or are you gathering context for
  a future decision?"

**If exploring:**
- "Would you like me to build a *research tracker* skill that helps you compare
  and evaluate options over time, or an *implementation guide* you can use later
  when you're ready?"

### 2. Approach Clarity

**If implementing:**
- "Do you already know how you want to integrate it, or do you need help
  figuring that out?"

**If "I don't know":**
Present 2-3 common approaches with one-line tradeoffs each, then ask:
- "Which of these sounds closest to your data/situation? Or should the skill
  walk you through choosing?"

### 3. Scope & Constraints

- "Is this for a prototype, MVP, or production system?"
- "What's your timeline?"
- "Are there any hard constraints? (budget, compliance, latency, offline-only)"

### 4. Integration Context

- "What does your current stack look like? Language, framework, existing DB?"
- "Are you adding this to an existing codebase or starting fresh?"
- "Do you have any existing infrastructure this needs to plug into?"

### 5. Success Criteria

- "What would 'done' look like for this piece?"
- "What output format do you need? (code, markdown docs, JSON config)"
- "Any performance thresholds or quality bars?"

### 6. Edge Cases & Failure Modes

- "What should happen if [primary technology] fails or returns low-confidence
  results?"
- "Are there any error cases or edge cases you already know about?"
- "Should the skill handle retries, fallbacks, or graceful degradation?"

## Follow-up Rules

| User Response | Action |
|--------------|--------|
| "I don't know" | Switch to educational mode; present 2-3 options |
| "No / Not yet" | Offer research-tracker alternative |
| Partial answer | Ask one sharpening question, then advance |
| Definitive answer | Log decision, check category coverage, ask next category |
| Off-topic | Gently redirect: "Got it. To make the skill accurate, I still need to know [specific question]." |
