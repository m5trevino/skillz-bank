---
name: pinpoint
description: Deep-dive analysis and documentation of a specific feature, component, or system in a codebase. Use when user asks to "pinpoint", "deep dive", "analyze", or "document" a specific feature like "pinpoint the auth system", "analyze the payment flow", or "document the WebSocket handler". Complements the init skill by focusing on single features rather than whole codebase.
---

# Pinpoint Skill - Feature Deep Dive

Analyze and document a specific feature, component, or system in detail.

## Workflow

1. **Identify target** - User specifies what feature to analyze
2. **Delegate analysis** - Subagent explores using [pinpoint prompt](references/pinpoint-prompt.md)
3. **Generate documentation** - Create detailed feature doc using [feature template](references/feature-template.md)
4. **Output to file** - Save as `docs/pinpoints/<feature-name>.md`

## Usage

### Natural Language Triggers
```
"Pinpoint the authentication system"
"Deep dive the payment flow"
"Analyze the WebSocket handler"
"Document the caching layer"
```

### Python API
```python
from skills.pinpoint import pinpoint_feature

result = await pinpoint_feature(
    feature_name="authentication system",
    focus_areas=["JWT flow", "session management"]
)
```

## Output

Creates `docs/pinpoints/<feature-name>.md` with:
- Feature overview and purpose
- Architecture diagram (ASCII)
- Implementation details
- Key files and functions
- Data flow / step-by-step flow
- Dependencies and integrations
- Configuration options

## Comparison with Init

| Init | Pinpoint |
|------|----------|
| Whole codebase | Single feature |
| AGENTS.md | docs/pinpoints/*.md |
| General overview | Deep technical detail |
| "Initialize this project" | "Analyze this feature" |

## When to Use

- After building a complex feature, document it
- Onboarding someone to a specific component
- Before refactoring - understand current implementation
- Capturing tribal knowledge about critical systems
