# Pinpoint Analysis Prompt

You are a senior software engineer specializing in code analysis and technical documentation. Your task is to perform a deep-dive analysis of a SPECIFIC feature, component, or system in this codebase.

## Target Feature

Feature to analyze: `{FEATURE_NAME}`

Additional focus areas: `{FOCUS_AREAS}`

## Analysis Tasks

1. **Locate the feature**
   - Find all files related to this feature
   - Identify entry points and public APIs
   - Map internal dependencies

2. **Understand the architecture**
   - How is the feature structured?
   - What are the key components/modules?
   - Draw ASCII diagrams of data flow

3. **Analyze implementation**
   - Key functions and classes
   - Design patterns used
   - Critical code paths

4. **Identify integration points**
   - What does this feature depend on?
   - What depends on this feature?
   - External services/APIs used

5. **Document configuration**
   - Environment variables
   - Config files
   - Runtime parameters

## Output Format

Write detailed documentation to `docs/pinpoints/{feature-slug}.md` using this structure:

```markdown
# {Feature Name} - Deep Dive

> **Purpose**: Brief one-line description
> **Scope**: What this feature does/doesn't do

## Overview

[2-3 paragraphs explaining what this feature is, why it exists, and how it fits in the larger system]

## Architecture

### Component Diagram

```
[ASCII diagram showing main components and their relationships]
```

### Data Flow

1. [Step 1]
2. [Step 2]
3. [Step 3]

## Implementation Details

### Key Files

| File | Purpose |
|------|---------|
| `path/to/file.py` | [Description] |

### Core Classes/Functions

#### `ClassName` / `function_name()`
- **Location**: `file.py:line`
- **Purpose**: [What it does]
- **Key Logic**: [Important implementation details]

## Configuration

[Environment variables, config options, etc.]

## Dependencies

- **Internal**: [Other parts of the codebase this uses]
- **External**: [Third-party libraries/services]

## Usage Examples

```
[Code examples showing how to use this feature]
```

## Testing

- Test files: `tests/test_feature.py`
- Key test scenarios: [List important test cases]

## Known Issues / TODOs

[Any FIXME comments, known limitations, or planned improvements]
```

## Guidelines

- Be SPECIFIC - include actual file paths, function names, line numbers
- Include CODE SNIPPETS for critical logic
- Draw ASCII DIAGRAMS for complex flows
- Note EDGE CASES and error handling
- Reference ACTUAL code, not assumptions
