# Agent Starter Templates

Minimal, production-ready starting points for `@opentui/react` apps.

## Files

| File | Purpose |
|------|---------|
| `01-basic-static.tsx` | Non-interactive layout demo. Boxes, borders, text styling, flex row/column. |
| `02-stateful-input.tsx` | Interactive form with `useState`, `useKeyboard`, `<input>`, and submit handling. |

## How to run

From the repo root:

```bash
bun packages/react/examples/agent-starters/01-basic-static.tsx
bun packages/react/examples/agent-starters/02-stateful-input.tsx
```

## Requirements

- `bun install` must have been run from the repo root so workspace links resolve.
- Native libraries must be built (`bun run build` from repo root) or the optional platform package must match the TypeScript source version.

## tsconfig.json

Both starters assume this configuration:

```json
{
  "compilerOptions": {
    "jsx": "react-jsx",
    "jsxImportSource": "@opentui/react",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "target": "ESNext"
  }
}
```
