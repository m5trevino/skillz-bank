---
name: opentui-guide
description: >
  Build terminal UI applications with OpenTUI. Covers three APIs (Renderables,
  Constructs, JSX), the React and Core packages, layout, keyboard input, all
  components, hooks, debugging, testing, and common patterns. Use when the user
  asks for a TUI app, terminal UI, CLI dashboard, interactive terminal tool,
  or anything that runs in the terminal with boxes, forms, lists, or styled text.
version: "3.0.0"
scope: "OpenTUI @opentui/react and @opentui/core"
---

# OpenTUI Agent Skill

## What is OpenTUI

Native terminal UI library (Zig + TypeScript) with Yoga-powered flexbox layout,
built-in keyboard/mouse, syntax highlighting, animation timelines, and optional
React/Solid reconcilers. Requires Bun runtime (not Node.js).

**Site:** https://opentui.com
**Repo:** https://github.com/anomalyco/opentui
**Reference Repository:** `~/.agents/skills/tui-ref/`  

**Local skill folders in this directory:**

- ~/.agents/skills/tui-ref/create-tui

- ~/.agents/skills/tui-ref/opentui-demos

- ~/.agents/skills/tui-ref/opentui-text

- ~/.agents/skills/tui-ref/opentui-ui

- ~/.agents/skills/tui-ref/scripts

---

---

## Sequential Auto-Slice Processing + Fresh Agent Clarity

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

## Critical Rules

1. **Use `create-tui` for new projects.** `bunx create-tui -t react my-app` — options before arguments.
2. **Never call `process.exit()` directly.** Use `renderer.destroy()`.
3. **Wrap bootstrap with `import.meta.main`.** Without it, importing the module seizes the terminal.
4. **Text styling requires nested tags in React/Solid.** Use `<span>`, `<strong>`, `<em>`, not props.
5. **`console.log` is invisible while the TUI runs.** Use `renderer.console.show()` or set `OTUI_DUMP_CAPTURES=true`.
6. **Always call `renderer.destroy()` on exit.** Without it the terminal may stay blank or cursor-hidden. Run `reset` if this happens.
7. **`exitOnCtrlC: true` by default.** Set `exitOnCtrlC: false` if you need custom signal handling.
8. **Key names are lowercase.** Use `"enter"`, `"escape"`, `"up"`, not `"Enter"`, `"Escape"`, `"Up"`.

---

## Decision Tree: Which API

```
Which API?
├─ Declarative UI with React hooks and JSX
│  └─ @opentui/react (default choice)
├─ Fine-grained reactivity with SolidJS signals
│  └─ @opentui/solid
├─ Maximum control, custom renderables, minimal deps
│  └─ @opentui/core (imperative Renderables or functional Constructs)
├─ Quick project scaffold
│  └─ bunx create-tui -t react my-app
└─ Building a library/framework on top of OpenTUI
   └─ @opentui/core (imperative)
```

**Default to `@opentui/react` unless the user explicitly requests Solid or imperative APIs.**

---

## Decision Tree: Which Component

```
Display content?
├─ Plain/styled text -> <text> or Text()
├─ Container with borders -> <box> or Box()
├─ Scrollable area -> <scrollbox> with stickyScroll + viewportCulling
├─ ASCII art banner -> <ascii-font> font="block|slick|shade|tiny"
├─ Syntax-highlighted code -> <code> with SyntaxStyle
├─ Diff viewer (unified/split) -> <diff> viewMode="unified|split"
├─ Line numbers + diagnostics -> <line-number> with setLineSign()
└─ Markdown (streaming) -> <markdown>

User input?
├─ Single-line text -> <input> (requires focused={true})
├─ Multi-line editor -> <textarea> with ref
├─ Vertical list select -> <select> with j/k/Enter
├─ Horizontal tab select -> <tab-select>
└─ Custom keyboard -> useKeyboard hook
```

---

## Three APIs: Renderables, Constructs, JSX

### JSX (React) — Declarative, default choice

```tsx
<box border title="Panel" style={{ padding: 1, flexDirection: "column" }}>
  <text fg="#00FF00">Hello</text>
  <input focused={true} placeholder="Type..." onInput={setValue} />
</box>
```

### Constructs — Functional composition, no React

```typescript
import { Text, Box } from "@opentui/core";
Text({ content: "Hello", fg: "#00FF00" })
Box({ border: "rounded", title: "Panel", padding: 1 }, Text({ content: "Child" }))
```

Rich text with template literals:
```typescript
import { t, bold, fg, italic } from "@opentui/core";
Text({ content: t`${bold(fg("#FFFF00")("bold yellow"))} and ${italic("italic")}` })
```

### Renderables — Imperative classes, full control

```typescript
const box = new BoxRenderable(renderer, { border: true, title: "Panel" });
const text = new TextRenderable(renderer, { content: "Hello" });
box.add(text);
renderer.root.add(box);
```

**Prefer Renderables for stateful components needing direct control. Prefer Constructs for simple composition without React overhead.**

Text attributes (bitwise OR): `BOLD | DIM | ITALIC | UNDERLINE | BLINK | INVERSE | HIDDEN | STRIKETHROUGH`

---

## Bootstrap (React)

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

Required tsconfig.json:
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

Required dependencies: `@opentui/core ^0.2.15`, `@opentui/react ^0.2.15`, `react ^19.2.0`

---

## Renderer Options

```typescript
const renderer = await createCliRenderer({
  exitOnCtrlC: true,
  targetFps: 30,
  maxFps: 60,
  useAlternateScreen: true,
  useMouse: true,
  backgroundColor: "#000000",
  useConsole: true,
})
```

- **Live mode**: call `renderer.start()` for continuous rendering at target FPS
- **On-demand**: without `start()`, renders only on changes

---

## Hooks

| Hook | Purpose | Example |
|------|---------|---------|
| `useRenderer()` | Access CliRenderer for console, destroy | `renderer.console.toggle()` |
| `useKeyboard(handler, opts?)` | Global keyboard input | `handler` receives `KeyEvent` |
| `usePaste(handler)` | Terminal paste events | Decode with `decodePasteBytes` |
| `useFocus(handler)` / `useBlur(handler)` | Window focus/blur events | — |
| `useOnResize(cb)` | Terminal resize | `cb(width, height)` |
| `useTerminalDimensions()` | Reactive `{ width, height }` | Re-renders on resize |
| `useTimeline(opts?)` | Animation timeline | `duration`, `easing`, `loop`, `onUpdate` |

KeyEvent properties: `name`, `ctrl`, `shift`, `meta` (Alt on Linux), `option` (macOS), `sequence`.
Set `{ release: true }` to get key release events instead of press.

Console overlay: `renderer.console.show()` / `.hide()` / `.toggle()`. Backtick key toggles visibility.

---

## JSX Components

| Component | Key Props |
|-----------|-----------|
| `<box>` | border, borderStyle (single/double/rounded/bold/classic), title, titleAlign, focused |
| `<text>` | content, fg, bg, attributes. Children: `<span>`, `<strong>`, `<b>`, `<em>`, `<i>`, `<u>`, `<br>`, `<a href="">` |
| `<input>` | placeholder, value, focused, onInput, onSubmit, backgroundColor, focusedBackgroundColor |
| `<textarea>` | ref, placeholder, focused, initialValue, style. Access: `ref.current.getText()` |
| `<select>` | options, focused, onChange(index, option), showScrollIndicator, selectedIndex, showDescription |
| `<tab-select>` | options, focused, onChange, tabWidth |
| `<scrollbox>` | focused, scrollY, stickyScroll, viewportCulling, rootOptions/wrapperOptions/viewportOptions/contentOptions/scrollbarOptions |
| `<code>` | content, filetype, syntaxStyle, streaming, selectable |
| `<line-number>` | ref, fg, bg, minWidth, showLineNumbers. Methods: `setLineColor(i, color)`, `setLineSign(i, {after, afterColor})` |
| `<diff>` | oldContent, newContent, filetype, syntaxStyle, viewMode="unified\|split" |
| `<ascii-font>` | text, font (tiny/block/slick/shade), color |
| `<markdown>` | Streaming markdown renderer |

Style props: `width`, `height`, `padding`, `margin`, `backgroundColor`, `flexDirection`, `flexGrow`, `flexShrink`, `flexWrap`, `justifyContent`, `alignItems`, `gap`, `visible`, `position` (relative/absolute), `top`, `left`, `zIndex`.

Size: `width={40}`, `height={10}`, `width="50%"`, `width="auto"`, `minWidth={20}`, `maxWidth={80}`.

Colors: hex `"#RRGGBB"` or `RGBA.fromHex()`, `RGBA.fromInts(r,g,b,a)`, `RGBA.fromValues(r,g,b,a)`.

### Core Renderables (imperative, no React)

| Class | Primary Use |
|-------|-------------|
| `BoxRenderable` | Layout container with borders, padding, flexbox |
| `TextRenderable` | Styled text display |
| `InputRenderable` | Single-line text input. Events: `InputEvent.INPUT`, `InputEvent.ENTER` |
| `TextareaRenderable` | Multi-line text editor |
| `SelectRenderable` | List selection with keyboard nav. Events: `SelectEvent.ITEM_SELECTED` |
| `ScrollBoxRenderable` | Scrollable container. Methods: `.scrollBy()`, `.scrollTo()` |
| `CodeRenderable` | Syntax-highlighted code. Props: `streaming`, `selectable` |
| `LineNumberRenderable` | Line-numbered gutter. Methods: `setLineColor()`, `setLineSign()` |
| `DiffRenderable` | Unified/split diff viewer |
| `MarkdownRenderable` | Markdown renderer |
| `ASCIIFontRenderable` | ASCII art text |

All accept `width`, `height`, `padding`, `margin`, `backgroundColor`, `visible`, `flexDirection`, `flexGrow`, etc.

---

## Patterns

See `references/patterns.md` for: Static Layout, Input Form, Select List, Code Block,
Multi-View App, Modal Dialog, Focus Management, List Selection, Responsive Layout,
Loading Spinner, Syntax Style, Scrollbox Styling, Timeline Animation.

---

## Testing

See `references/testing.md` for headless testing with `createTestRenderer`, `mockInput`,
`mockMouse`, `renderOnce`, `captureCharFrame`.

---

## Debugging

When `console.log` is captured by the TUI overlay, use file-based logging:

```typescript
import { logDebug } from "./utils/debug.ts";
logDebug("render", { width, height, scrollOffset });
```

Logs append to `debug.log` with timestamps. Agent reads: `read /path/to/project/debug.log`.

Best practices: log state changes in `useEffect`, log key presses in `useKeyboard`,
log calculated values (visible rows, scroll offsets). Restart app after adding debug points.

| Issue | Fix |
|-------|-----|
| No log file | Restart app after adding `logDebug()` |
| Log not updating | Check `logDebug()` is actually called |
| Too verbose | Remove logs from frequently-rendered components |

Environment variables: `OTUI_DEBUG=true`, `OTUI_SHOW_STATS=true`, `OTUI_DUMP_CAPTURES=true`

---

## Survival Rules

1. **Bun only** — not Node.js. Zig only needed for native code changes.
2. **`bun install` fails behind SOCKS5.** Unset `http_proxy`/`https_proxy`/`ALL_PROXY` first.
3. **Prebuilt binaries may be stale.** `Symbol ... not found in libopentui.so` — build from source: `bun run build`.
4. **No built-in hot reload.** Use `bun --watch index.tsx`.
5. **Focus required.** Inputs/selects need `focused={true}` to receive events.
6. **Alternate screen is default.** Set `useAlternateScreen: false` to disable full-screen mode.
7. **Sticky scroll for chat UIs.** `stickyScroll: "bottom"` keeps view anchored.
8. **Viewport culling for large lists.** `viewportCulling: true` on ScrollBox.

---

## Troubleshooting

| Symptom | Cause | Fix |
|--------|-------|-----|
| Blank terminal after exit | `renderer.destroy()` not called | Add cleanup. Run `reset`. |
| Keyboard not working | Component not focused | Set `focused={true}` on input/select |
| Layout broken | Parent has no dimensions | Add explicit `width`/`height` or use `flexGrow` |
| Colors not showing | Terminal doesn't support 24-bit | Use hex `"#RRGGBB"`. Check terminal. |
| Console.log invisible | TUI captures stdout | `renderer.console.show()` or `OTUI_DUMP_CAPTURES=true` |
| Styling not applying | Using props instead of children | Use nested tags: `<text><span fg="red">text</span></text>` |

---

## Build & Run

```bash
bun install
bun run build          # Only for native changes or stale prebuilt binaries
bun index.tsx           # Run
bun --watch index.tsx   # Auto-restart on change
cd packages/core && bun run test:native
```

---

## Code Style

Import order: external deps → OpenTUI → internal utils → components → `type` imports.
Naming: camelCase (vars/funcs), PascalCase (components/types), UPPER_CASE (constants).
Component structure: hooks → event handlers → effects → helpers → JSX return.

---

## Resources

- Getting Started: https://opentui.com/docs/getting-started/
- Components: https://opentui.com/docs/components/box/ (box, text, input, select, scrollbox, code)
- React Bindings: https://opentui.com/docs/bindings/react/
- Awesome List: https://github.com/msmps/awesome-opentui
