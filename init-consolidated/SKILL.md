---
name: init
description: Initialize or refresh codebase exploration for AI agents by generating/updating AGENTS.md. Use when starting a new session, onboarding an agent to a codebase, or when AGENTS.md is missing/outdated. Triggers on phrases like "init this project", "create AGENTS.md", "analyze this codebase", or when agent needs project context.
---

# Init Skill - Project Initialization

Analyze codebase and generate `AGENTS.md` for AI coding agents.

## Workflow

1. **Delegate exploration** to subagent with the [exploration prompt](references/exploration-prompt.md)
2. **Subagent analyzes** project structure, tech stack, conventions
3. **Generate AGENTS.md** using the [agents template](references/agents-template.md)
4. **Inject results** into conversation context

## Usage

### Slash Command
```
/init                    # Analyze current directory
/init /path/to/project   # Analyze specific directory
```

### Python API
```python
from skills.init import run_init

result = await run_init(work_dir="/path/to/project")
print(result["summary"])
```

## Output

Creates `AGENTS.md` in project root with:
- Project overview
- Technology stack
- Architecture & code organization
- Development conventions
- Build/test commands
- Security considerations

## Why Temporary Subagent?

Exploration uses many tool calls (Glob, ReadFile, Shell). Running in isolated subagent prevents context pollution - only the final AGENTS.md enters your conversation.

## Customization

Pass extra instructions to focus analysis:
```python
await run_init(
    extra_instructions="Focus on API endpoints and authentication flow"
)
```

## Reference Files

- [exploration-prompt.md](references/exploration-prompt.md) - Prompt sent to exploration subagent
- [agents-template.md](references/agents-template.md) - Recommended AGENTS.md structure
