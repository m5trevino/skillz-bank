---
name: opentui-agent
description: >
  Build terminal UI applications with OpenTUI. Covers the React reconciler,
  imperative core renderables, layout, keyboard input, event handling,
  common pitfalls, and exact bootstrap patterns. Use this skill when the user
  asks for a TUI app, terminal UI, CLI dashboard, interactive terminal tool,
  or anything that runs in the terminal with boxes, forms, lists, or styled text.
version: "1.0.0"
scope: "OpenTUI @opentui/react and @opentui/core APIs"
---

# OpenTUI Agent Skill

## What is OpenTUI

OpenTUI is a native terminal UI library written in Zig with TypeScript bindings.
It provides a component-based architecture with Yoga-powered flexbox layout,
built-in keyboard/mouse input, syntax highlighting, animation timelines, and
optional React/Solid reconcilers. It targets correctness and high performance
for complex interactive terminal applications.

**Repository:** `~/.agents/skills/tui-ref/`  
**Site:** https://opentui.com

**Local skill folders in this directory:**

- ~/.agents/skills/tui-ref/create-tui

- ~/.agents/skills/tui-ref/opentui-demos

- ~/.agents/skills/tui-ref/opentui-text

- ~/.agents/skills/tui-ref/opentui-ui

- ~/.agents/skills/tui-ref/scripts


---
## New in v2.0: Sequential Auto-Slice Processing + Fresh Agent Clarity

This skill can now ingest tracer bullet slices from large OpenTUI projects and execute them **one at a time in strict sequence** (Autonomous mode by default).

**In Autonomous mode, every new slice is clearly announced like this:**

```
══════════════════════════════════════════════════════════════════
NEW SLICE STARTING — FRESH AGENT
══════════════════════════════════════════════════════════════════

Slice: TB-003 — StrikeScreen — Payload Striker Visual Port + Rate Headroom Polish

This slice is being executed by a completely fresh agent.
Zero knowledge of any previous slices or the overall project.
Only this slice’s objective, scope, acceptance_criteria, and hard_gates are visible.

[Loading sealed task for this slice only...]
```

After a slice finishes it will clearly say:

```
══════════════════════════════════════════════════════════════════
SLICE COMPLETE
══════════════════════════════════════════════════════════════════

TB-003 finished successfully.
Moving to next slice...
```

This makes it impossible to miss when one slice ends and a new fresh agent starts the next one.

---

## Decision Tree: Which Package to Use

| Situation | Package | Why |
|-----------|---------|-----|
| User wants JSX, React hooks, familiar component model | `@opentui/react` | Default choice. Full reconciler with `useState`, `useEffect`, `useKeyboard`. |
| User wants SolidJS signals, smaller bundle, or Solid ecosystem | `@opentui/solid` | Solid reconciler with `createSignal` and `createEffect`. |
| User needs maximum control, custom renderables, minimal deps | `@opentui/core` | Imperative renderables (classes) with direct `renderer.root.add()`. |
| User wants a quick scaffold | `scripts/create-opentui-app.sh` | Bash script in the repo that generates a working project skeleton. |

**Default to `@opentui/react` unless the user explicitly requests Solid or raw imperative APIs.**

---

---

## Decision Tree: Which Package to Use

| Situation | Package | Why |
|-----------|---------|-----|
| User wants JSX, React hooks, familiar component model | `@opentui/react` | Default choice. Full reconciler with `useState`, `useEffect`, `useKeyboard`. |
| User wants SolidJS signals, smaller bundle, or Solid ecosystem | `@opentui/solid` | Solid reconciler with `createSignal` and `createEffect`. |
| User needs maximum control, custom renderables, minimal deps | `@opentui/core` | Imperative renderables (classes) with direct `renderer.root.add()`. |
| User wants a quick scaffold | `scripts/create-opentui-app.sh` | Bash script in the repo that generates a working project skeleton. |

**Default to `@opentui/react` unless the user explicitly requests Solid or raw imperative APIs.**

---

## Bootstrap Pattern (React)

Every `@opentui/react` app follows this exact entry pattern:

```typescript
import { createCliRenderer } from "@opentui/core"
import { createRoot } from "@opentui/react"

function App() {
  return <text>Hello, OpenTUI!</text>
}

if (import.meta.main) {
  const renderer = await createCliRenderer()
  createRoot(renderer).render(<App />)
}
```

### Required tsconfig.json

```json
{
  "compilerOptions": {
    "lib": ["ESNext", "DOM"],
    "target": "ESNext",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "jsxImportSource": "@opentui/react",
    "strict": true,
    "skipLibCheck": true
  }
}
```

### Required package.json dependencies

```json
{
  "dependencies": {
    "@opentui/core": "^0.2.15",
    "@opentui/react": "^0.2.15",
    "react": "^19.2.0"
  }
}
```

---

## Common Hooks (React)

Import all hooks from `@opentui/react`:

| Hook | Purpose |
|------|---------|
| `useRenderer()` | Access the `CliRenderer` instance (for `console.show()`, `destroy()`, etc.) |
| `useKeyboard(handler, options?)` | Global keyboard input. `handler` receives `KeyEvent` with `.name`, `.ctrl`, `.meta`. |
| `usePaste(handler)` | Terminal paste events. Decode bytes with `decodePasteBytes` from `@opentui/core`. |
| `useFocus(handler)` / `useBlur(handler)` | Terminal window focus/blur events. |
| `useOnResize(callback)` | Terminal dimensions changed. Receives `(width, height)`. |
| `useTerminalDimensions()` | Reactive `{ width, height }` hook. |
| `useTimeline(options?)` | Animation timeline (duration, easing, loop, onUpdate). |

---

## JSX Components (React)

**Layout & Display:** `<box>`, `<scrollbox>`, `<ascii-font>`, `<text>`  
**Input:** `<input>`, `<textarea>`, `<select>`, `<tab-select>`  
**Code:** `<code>`, `<line-number>`, `<diff>`  
**Text Modifiers (inside `<text>` only):** `<span>`, `<strong>`, `<b>`, `<em>`, `<i>`, `<u>`, `<br>`, `<a>`  
**Other:** `<markdown>`

---

## Styling

Components accept style props directly or via a `style` prop object:

```tsx
<box border title="Panel" style={{ padding: 1, backgroundColor: "#1a1b26" }}>
  <text fg="#00FF00">Styled text</text>
</box>
```

Common properties: `width`, `height`, `border`, `borderStyle`, `borderColor`, `padding`, `margin`, `backgroundColor`, `flexDirection`, `flexGrow`, `flexShrink`, `alignItems`, `justifyContent`, `gap`, `visible`.

---

## Pattern 1: Static Layout

```tsx
function App() {
  return (
    <box style={{ flexDirection: "column", padding: 2, gap: 1 }}>
      <text fg="#FFFF00">Static Layout</text>

      <box border title="Panel" style={{ padding: 1 }}>
        <text>Content inside a bordered box</text>
      </box>

      <box flexDirection="row" gap={1}>
        <box border style={{ flexGrow: 1, padding: 1 }}>
          <text>Left</text>
        </box>
        <box border style={{ flexGrow: 1, padding: 1 }}>
          <text>Right</text>
        </box>
      </box>
    </box>
  )
}
```

---

## Pattern 2: Stateful Input Form

```tsx
import { useKeyboard, useRenderer } from "@opentui/react"
import { useCallback, useEffect, useState } from "react"

function App() {
  const [value, setValue] = useState("")
  const [submitted, setSubmitted] = useState<string | null>(null)
  const renderer = useRenderer()

  useEffect(() => {
    renderer.console.show()
  }, [renderer])

  useKeyboard((key) => {
    if (key.name === "escape") {
      renderer.destroy()
      process.exit(0)
    }
  })

  return (
    <box style={{ flexDirection: "column", padding: 2, gap: 1 }}>
      <box border title="Input" style={{ width: 50, height: 3 }}>
        <input
          focused={true}
          placeholder="Type here..."
          onInput={setValue}
          onSubmit={() => setSubmitted(value)}
        />
      </box>
      {submitted && <text fg="#00FF00">Submitted: {submitted}</text>}
    </box>
  )
}
```

---

## Pattern 3: Select List with Keyboard Navigation

```tsx
import { useState } from "react"

function App() {
  const [selected, setSelected] = useState(0)

  return (
    <box style={{ padding: 2 }}>
      <select
        options={[
          { name: "Option 1", description: "First choice", value: "opt1" },
          { name: "Option 2", description: "Second choice", value: "opt2" },
        ]}
        selectedIndex={selected}
        showDescription={true}
        width={50}
        height={10}
        onItemSelected={(index, option) => {
          console.log("Selected:", option.value)
        }}
      />
    </box>
  )
}
```

---

## Pattern 4: Code Block with Syntax Highlighting

```tsx
import { CodeRenderable, SyntaxStyle, RGBA } from "@opentui/core"

const syntaxStyle = SyntaxStyle.fromStyles({
  keyword: { fg: RGBA.fromHex("#ff6b6b"), bold: true },
  string: { fg: RGBA.fromHex("#51cf66") },
  default: { fg: RGBA.fromHex("#ffffff") },
})

function App() {
  return (
    <box style={{ padding: 1 }}>
      <code
        content={`const x = 42`}
        filetype="javascript"
        syntaxStyle={syntaxStyle}
        width={60}
        height={10}
      />
    </box>
  )
}
```

---

## Core Renderables Quick Reference

When using `@opentui/core` directly (no React), instantiate these classes:

| Renderable | Import | Primary Use |
|------------|--------|-------------|
| `BoxRenderable` | `@opentui/core` | Layout container with borders, padding, flexbox |
| `TextRenderable` | `@opentui/core` | Styled text display |
| `InputRenderable` | `@opentui/core` | Single-line text input |
| `TextareaRenderable` | `@opentui/core` | Multi-line text editor |
| `SelectRenderable` | `@opentui/core` | List selection with keyboard nav |
| `ScrollBoxRenderable` | `@opentui/core` | Scrollable container with scrollbars |
| `CodeRenderable` | `@opentui/core` | Syntax-highlighted code block |
| `LineNumberRenderable` | `@opentui/core` | Line-numbered gutter (wraps CodeRenderable) |
| `DiffRenderable` | `@opentui/core` | Unified/split diff viewer |
| `MarkdownRenderable` | `@opentui/core` | Markdown renderer |
| `ASCIIFontRenderable` | `@opentui/core` | ASCII art text |

All accept `width`, `height`, `padding`, `margin`, `backgroundColor`, `visible`, `flexDirection`, `flexGrow`, etc.

**Entry pattern (imperative):**

```typescript
const renderer = await createCliRenderer()
const box = new BoxRenderable(renderer, { border: true, title: "Panel" })
const text = new TextRenderable(renderer, { content: "Hello" })
box.add(text)
renderer.root.add(box)
```

---

## Survival Rules

1. **`console.log` is invisible while the TUI runs.** Call `renderer.console.show()` before logging, or set `OTUI_DUMP_CAPTURES=true`.
2. **Always call `renderer.destroy()` on exit.** Without it, the terminal may remain blank, cursor hidden, or key echo disabled. Run `reset` in the shell if this happens.
3. **`exitOnCtrlC: true` by default.** The app exits immediately on Ctrl+C. Set `exitOnCtrlC: false` in `createCliRenderer()` if you need custom signal handling.
4. **`bun install` can fail behind SOCKS5 proxies.** Bun does not support `socks5://` or `socks5h://`. Unset `http_proxy`/`https_proxy`/`ALL_PROXY` before installing.
5. **Prebuilt native binaries may be stale.** If you see `Symbol ... not found in libopentui.so`, build from source with `bun run build` from the repo root.
6. **Wrap bootstrap with `import.meta.main`.** Without this guard, importing the file as a module starts the renderer and seizes the terminal.
7. **No built-in hot reload.** Use `bun --watch` or an external watcher to restart the process on file changes.

---

## Build & Run Commands

```bash
# Install dependencies
bun install

# Build native libraries (only needed for native code changes or if prebuilt binary is stale)
bun run build

# Run an app
bun index.tsx

# Run with auto-restart on change
bun --watch index.tsx

# Run tests for a package
cd packages/core && bun run test:native
```

---

## Deep Dive References

For extended prop tables, additional patterns, and full diagnostic details, see the artifacts in the repo:

- **`/reference/renderables-reference.md`** — Complete inventory of all core renderables with key props and minimal usage snippets.
- **`/reference/react-quickstart.md`** — Extended React guide with all hooks, components, styling reference, and 3 detailed app skeletons.
- **`/reference/tui-survival-guide.md`** — Full runtime pitfalls guide with exact error messages, symptoms, fixes, and a 60-second debugging checklist.
- **`/reference/agent-starters/`** — Heavily-commented starter templates (`01-basic-static.tsx`, `02-stateful-input.tsx`).
- **`/reference/create-opentui-app.sh`** — Bash scaffold generator that produces a fresh, runnable OpenTUI project in one command.
- **`/reference/AGENTS.md`** — Root agent guidelines with the quickstart appendix.


