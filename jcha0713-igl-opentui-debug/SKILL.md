---
name: opentui-debug
description: Debug OpenTUI applications using file-based logging when console.log is captured by the TUI overlay.
---

# OpenTUI Debug

File-based debugging for OpenTUI apps since `console.log` output is captured by the TUI's debug overlay.

## Quick Start

**Log from components:**
```typescript
import { logDebug } from "./utils/debug.ts";

logDebug("render", { width, height, scrollOffset });
```

**Agent reads the log:**
```
read /path/to/project/debug.log
```

## When to Use

Use when:
- `console.log` doesn't appear in terminal (captured by OpenTUI)
- Need to trace state changes across renders
- Debugging scroll behavior, layout calculations
- Analyzing key input handling

## Setup (Already in Project)

- `src/utils/debug.ts` - Logger utility
- `debug.log` - Output file (project root, gitignored)
- Auto-clears on app start

## API

```typescript
logDebug(label: string, data: unknown): void
```

Logs are appended with timestamps:
```
[2026-02-06T04:35:04.309Z] label:
{
  "key": "value"
}
```

## Best Practices

1. **Log state changes** in `useEffect`
2. **Log key presses** in `useKeyboard` handlers
3. **Log calculated values** (visible rows, scroll offsets)
4. **Restart app** after adding debug points (logger initializes on import)

## Example

```typescript
useKeyboard((key) => {
  logDebug("key", { name: key.name, mode: currentMode });
  // ... handle
});

useEffect(() => {
  logDebug("scroll", { offset, maxScroll, visible: rows.length });
}, [offset]);
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| No log file | Restart app after adding `logDebug()` |
| Log not updating | Check `logDebug()` is actually called |
| Too verbose | Remove logs from frequently-rendered components |
