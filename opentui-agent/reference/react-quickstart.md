# OpenTUI React Quickstart

**Package:** `@opentui/react`  
**Source patterns:** `packages/react/README.md`, `packages/react/examples/*.tsx`

---

## Dependencies

```bash
bun install @opentui/react @opentui/core react
```

`@opentui/react` requires `@opentui/core` and `react` as peer dependencies.

---

## TypeScript Configuration

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

The key fields are `"jsx": "react-jsx"` and `"jsxImportSource": "@opentui/react"` so JSX elements resolve to OpenTUI components instead of DOM elements.

---

## Entry Boilerplate

Every `@opentui/react` app follows this exact pattern:

```tsx
import { createCliRenderer } from "@opentui/core"
import { createRoot } from "@opentui/react"
import { App } from "./App"

if (import.meta.main) {
  const renderer = await createCliRenderer()
  createRoot(renderer).render(<App />)
}
```

`createCliRenderer()` is async and must be awaited. `createRoot(renderer).render(<App />)` mounts the React tree into the terminal.

---

## Available Hooks

Import from `@opentui/react`:

| Hook | Signature | Purpose |
|------|-----------|---------|
| `useRenderer()` | `() => CliRenderer` | Access the renderer instance |
| `useKeyboard(handler, options?)` | `(key: KeyEvent) => void` | Handle keyboard input |
| `usePaste(handler)` | `(event: PasteEvent) => void` | Handle terminal paste |
| `useFocus(handler)` | `() => void` | Terminal window gains focus |
| `useBlur(handler)` | `() => void` | Terminal window loses focus |
| `useOnResize(callback)` | `(width, height) => void` | Terminal resized |
| `useTerminalDimensions()` | `() => { width, height }` | Current terminal size (reactive) |
| `useSelectionHandler(handler)` | `(selection: Selection) => void` | Mouse text selection |
| `useTimeline(options?)` | `(options: TimelineOptions) => Timeline` | Animation timeline |

---

## Available JSX Components

**Layout & Display:**

- `<text>` — styled text container
- `<box>` — layout container with borders, padding, flex settings
- `<scrollbox>` — scrollable container with optional scrollbars
- `<ascii-font>` — ASCII art text renderer

**Input:**

- `<input>` — single-line text input
- `<textarea>` — multi-line text input
- `<select>` — list selection dropdown
- `<tab-select>` — tab-based selection

**Code & Diff:**

- `<code>` — syntax-highlighted code block
- `<line-number>` — line-numbered code with diff/diagnostic helpers
- `<diff>` — unified or split diff viewer

**Text Modifiers (must be inside `<text>`):**

- `<span>`, `<strong>`, `<b>`, `<em>`, `<i>`, `<u>`, `<br>`, `<a>`

**Other:**

- `<markdown>` — Markdown renderer

---

## Styling

Components accept style props directly or through a `style` prop:

```tsx
{/* Direct props */}
<box backgroundColor="blue" padding={2}>
  <text>Hello</text>
</box>

{/* Style prop */}
<box style={{ backgroundColor: "blue", padding: 2 }}>
  <text>Hello</text>
</box>
```

Common style properties: `width`, `height`, `border`, `borderStyle`, `borderColor`, `padding`, `margin`, `backgroundColor`, `flexDirection`, `flexGrow`, `flexShrink`, `alignItems`, `justifyContent`, `gap`.

---

## App Skeleton 1: Static Layout

A non-interactive layout with boxes, borders, and styled text.

```tsx
import { createCliRenderer } from "@opentui/core"
import { createRoot } from "@opentui/react"

function App() {
  return (
    <box style={{ flexDirection: "column", padding: 2, gap: 1 }}>
      <text fg="#FFFF00">Static Layout Demo</text>

      <box border title="Panel A" style={{ padding: 1 }}>
        <text>Content inside a bordered box</text>
      </box>

      <box flexDirection="row" gap={1}>
        <box border style={{ flexGrow: 1, padding: 1, backgroundColor: "#1a1b26" }}>
          <text>Left column</text>
        </box>
        <box border style={{ flexGrow: 1, padding: 1, backgroundColor: "#1a1b26" }}>
          <text>Right column</text>
        </box>
      </box>
    </box>
  )
}

if (import.meta.main) {
  const renderer = await createCliRenderer()
  createRoot(renderer).render(<App />)
}
```

---

## App Skeleton 2: Stateful Counter

A component that uses React state and `useEffect` for a live-updating counter.

```tsx
import { createCliRenderer } from "@opentui/core"
import { createRoot } from "@opentui/react"
import { useEffect, useState } from "react"

function App() {
  const [count, setCount] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setCount((prev) => prev + 1)
    }, 1000)

    return () => clearInterval(interval)
  }, [])

  return (
    <box title="Counter" style={{ padding: 2, border: true }}>
      <text fg="#00FF00">Count: {count}</text>
    </box>
  )
}

if (import.meta.main) {
  const renderer = await createCliRenderer()
  createRoot(renderer).render(<App />)
}
```

---

## App Skeleton 3: Form with Input and Submit

A form with two input fields, tab navigation, and a submit handler.

```tsx
import { createCliRenderer } from "@opentui/core"
import { createRoot, useKeyboard } from "@opentui/react"
import { useCallback, useState } from "react"

function App() {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [focused, setFocused] = useState<"username" | "password">("username")
  const [status, setStatus] = useState<"idle" | "success" | "error">("idle")

  useKeyboard((key) => {
    if (key.name === "tab") {
      setFocused((prev) => (prev === "username" ? "password" : "username"))
    }
  })

  const handleSubmit = useCallback(() => {
    if (username === "admin" && password === "secret") {
      setStatus("success")
    } else {
      setStatus("error")
    }
  }, [username, password])

  return (
    <box style={{ border: true, padding: 2, flexDirection: "column", gap: 1 }}>
      <text fg="#FFFF00">Login Form</text>

      <box title="Username" style={{ border: true, width: 40, height: 3 }}>
        <input
          placeholder="Enter username..."
          onInput={setUsername}
          onSubmit={handleSubmit}
          focused={focused === "username"}
        />
      </box>

      <box title="Password" style={{ border: true, width: 40, height: 3 }}>
        <input
          placeholder="Enter password..."
          onInput={setPassword}
          onSubmit={handleSubmit}
          focused={focused === "password"}
        />
      </box>

      <text
        style={{
          fg: status === "success" ? "green" : status === "error" ? "red" : "#999",
        }}
      >
        {status.toUpperCase()}
      </text>
    </box>
  )
}

if (import.meta.main) {
  const renderer = await createCliRenderer()
  createRoot(renderer).render(<App />)
}
```

---

## Renderer Lifecycle and Console Handling

### Creating the renderer with options

```tsx
const renderer = await createCliRenderer({
  exitOnCtrlC: false,      // Handle Ctrl+C yourself
  screenMode: "alternate-screen", // "alternate-screen" | "main-screen" | "split-footer"
  targetFps: 30,
  useMouse: true,
})
```

### Common renderer methods

```tsx
const renderer = useRenderer()

// Show the built-in console overlay so console.log is visible
renderer.console.show()

// Toggle debug stats overlay
renderer.toggleDebugOverlay()

// Graceful shutdown
renderer.destroy()
```

### Important: console.log is hidden by default

While an OpenTUI app is running, standard `console.log` output is suppressed. To see logs:

```tsx
import { useRenderer } from "@opentui/react"
import { useEffect } from "react"

function App() {
  const renderer = useRenderer()

  useEffect(() => {
    renderer.console.show()
    console.log("Now visible in the console overlay!")
  }, [renderer])

  return <text>App running</text>
}
```

### Keyboard exit pattern

```tsx
import { useKeyboard } from "@opentui/react"

function App() {
  useKeyboard((key) => {
    if (key.name === "escape") {
      process.exit(0)
    }
  })

  return <text>Press ESC to exit</text>
}
```

### Terminal dimensions

```tsx
import { useTerminalDimensions } from "@opentui/react"

function App() {
  const { width, height } = useTerminalDimensions()

  return (
    <box>
      <text>Terminal: {width}x{height}</text>
    </box>
  )
}
```

---

## Paste Handling

```tsx
import { decodePasteBytes } from "@opentui/core"
import { usePaste } from "@opentui/react"

function App() {
  usePaste((event) => {
    const text = decodePasteBytes(event.bytes)
    console.log("Pasted:", text)
  })

  return <text>Paste something</text>
}
```

---

## Animation with useTimeline

```tsx
import { useTimeline } from "@opentui/react"
import { useEffect, useState } from "react"

function App() {
  const [width, setWidth] = useState(0)

  const timeline = useTimeline({
    duration: 2000,
    loop: false,
  })

  useEffect(() => {
    timeline.add(
      { width },
      {
        width: 50,
        duration: 2000,
        ease: "linear",
        onUpdate: (animation) => {
          setWidth(animation.targets[0].width)
        },
      },
    )
  }, [])

  return <box style={{ width, height: 1, backgroundColor: "#6a5acd" }} />
}
```
