# Feature Documentation Template

Template for generated pinpoint documentation.

---

```markdown
# {Feature Name} - Deep Dive

> **Purpose**: Brief one-line description
> **Scope**: What this feature does and doesn't do

## Overview

[2-3 paragraphs explaining:
- What this feature is
- Why it exists (problem it solves)
- How it fits in the larger system
- High-level approach]

## Architecture

### Component Diagram

```
┌─────────────────┐
│   Entry Point   │
│   (API/CLI/UI)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Core Handler   │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌───────┐
│Service│ │Service│
│   A   │ │   B   │
└───────┘ └───────┘
```

### Data Flow

1. [Input received at entry point]
2. [Validation/transformation]
3. [Core processing]
4. [Output generation]

## Implementation Details

### Key Files

| File | Purpose | Key Elements |
|------|---------|--------------|
| `src/auth/handler.py` | Main entry point | `AuthHandler` class |
| `src/auth/jwt.py` | JWT operations | `encode_token()`, `decode_token()` |

### Core Classes/Functions

#### `ClassName` (`src/module/file.py:45`)

```python
class ClassName:
    """Brief docstring"""
    
    def key_method(self, param: str) -> Result:
        # Critical logic here
        pass
```

- **Purpose**: [What it does]
- **Key Logic**: [Important implementation details, algorithms used]
- **Edge Cases**: [Error handling, special conditions]

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTH_SECRET` | required | JWT signing secret |
| `AUTH_EXPIRY` | 3600 | Token expiry in seconds |

## Dependencies

### Internal
- `src/utils/crypto.py` - Encryption utilities
- `src/db/models.py` - User model

### External
- `pyjwt` - JWT encoding/decoding
- `bcrypt` - Password hashing

## Usage Examples

```python
# Basic usage
from src.auth import AuthHandler

handler = AuthHandler()
token = handler.authenticate(username, password)
```

## Testing

- **Test file**: `tests/test_auth.py`
- **Key scenarios**:
  - Valid credentials
  - Invalid password
  - Expired token
  - Rate limiting

## Known Issues / TODOs

- [ ] Add refresh token rotation (TODO in `jwt.py:89`)
- [ ] Rate limiting needs improvement for burst traffic
```

---

## Section Guidelines

### Architecture Diagram
- Use ASCII art for component relationships
- Show data flow direction with arrows
- Group related components

### Implementation Details
- Include actual file paths with line numbers
- Show code snippets for critical logic
- Explain WHY, not just WHAT

### Data Flow
- Numbered steps from trigger to completion
- Include error paths
- Note async/sync boundaries

### Configuration
- Table format for easy scanning
- Note required vs optional
- Include validation rules
