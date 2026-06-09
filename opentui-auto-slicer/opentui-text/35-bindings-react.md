# React bindings

Build terminal user interfaces using React with familiar patterns and components.

## Installation

Quick start with [bun](https://bun.sh) and [create-tui](https://github.com/msmps/create-tui):

``` astro-code
bun create tui --template react
```

Manual installation:

``` astro-code
bun install @opentui/react @opentui/core react
```

## Quick start

``` astro-code
import { createCliRenderer } from "@opentui/core"
import { createRoot } from "@opentui/react"

function App() {
  return <text>Hello, world!</text>
}

const renderer = await createCliRenderer()
createRoot(renderer).render(<App />)
```

## TypeScript configuration

Configure your `tsconfig.json`:

``` astro-code
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

## Runtime-loaded plugin support (if needed)

If your app loads external TS/TSX modules at runtime (for example a file-based plugin system), import this once in your app entry before dynamic imports:

``` astro-code
import "@opentui/react/runtime-plugin-support"
```

Use this for both normal Bun runs and standalone compiled executables.

## Components

OpenTUI React provides JSX intrinsic elements that map to core renderables:

### Layout & display

-   `<text>` - Text display with styling
-   `<box>` - Container with borders and layout
-   `<scrollbox>` - Scrollable container
-   `<ascii-font>` - ASCII art text

QR code support is available from `@opentui/qrcode/react` and must be registered explicitly with `registerQRCode()`.

### Input

-   `<input>` - Single-line text input
-   `<textarea>` - Multi-line text input
-   `<select>` - Selection list
-   `<tab-select>` - Tab-based selection

### Code & diff

-   `<code>` - Syntax-highlighted code
-   `<line-number>` - Line numbers with diff/diagnostic support
-   `<diff>` - Unified or split diff viewer
-   `<markdown>` - Markdown rendering

### Text modifiers

Use inside `<text>` components:

-   `<span>` - Inline styled text
-   `<strong>`, `<b>` - Bold text
-   `<em>`, `<i>` - Italic text
-   `<u>` - Underlined text
-   `<br>` - Line break
-   `<a>` - Link text

## API reference

### `createRoot(renderer)`

Creates a React root for rendering into the terminal.

``` astro-code
import { createCliRenderer } from "@opentui/core"
import { createRoot } from "@opentui/react"

const renderer = await createCliRenderer()
createRoot(renderer).render(<App />)
```

For plugin slots, see [Plugin Slots overview](/docs/plugins/slots) and [React slots](/docs/plugins/react).

## Hooks

### `useRenderer()`

Access the OpenTUI renderer instance.

``` astro-code
import { useRenderer } from "@opentui/react"
import { useEffect } from "react"

function App() {
  const renderer = useRenderer()

  useEffect(() => {
    renderer.console.show()
    console.log("Hello from console!")
  }, [])

  return <box />
}
```

### `useKeyboard(handler, options?)`

Handle keyboard events.

``` astro-code
import { useKeyboard, useRenderer } from "@opentui/react"

function App() {
  const renderer = useRenderer()

  useKeyboard((key) => {
    if (key.name === "escape") {
      renderer.destroy()
    }
  })

  return <text>Press ESC to close</text>
}
```

To handle release events:

``` astro-code
useKeyboard(
  (event) => {
    if (event.eventType === "release") {
      console.log("Key released:", event.name)
    } else {
      console.log("Key pressed:", event.name)
    }
  },
  { release: true },
)
```

### `useOnResize(callback)`

Handle terminal resize events.

``` astro-code
import { useOnResize } from "@opentui/react"

function App() {
  useOnResize((width, height) => {
    console.log(`Resized to ${width}x${height}`)
  })

  return <text>Resize-aware component</text>
}
```

### `useTerminalDimensions()`

Get reactive terminal dimensions.

``` astro-code
import { useTerminalDimensions } from "@opentui/react"

function App() {
  const { width, height } = useTerminalDimensions()

  return (
    <text>
      Terminal: {width}x{height}
    </text>
  )
}
```

### `usePaste(handler)`

Handle terminal paste events (bracketed paste).

``` astro-code
import { decodePasteBytes } from "@opentui/core"
import { usePaste } from "@opentui/react"

function App() {
  usePaste((event) => {
    const text = decodePasteBytes(event.bytes)
    console.log("Pasted text:", text)
  })

  return <text>Paste something into the terminal</text>
}
```

### `useFocus(handler)`

Subscribe to terminal window focus events.

``` astro-code
import { useFocus } from "@opentui/react"

function App() {
  useFocus(() => {
    console.log("Terminal gained focus")
  })

  return <text>Focus-aware component</text>
}
```

### `useBlur(handler)`

Subscribe to terminal window blur events.

``` astro-code
import { useBlur } from "@opentui/react"

function App() {
  useBlur(() => {
    console.log("Terminal lost focus")
  })

  return <text>Blur-aware component</text>
}
```

### `useSelectionHandler(handler)`

Handle text selection events (e.g., mouse drag selection).

``` astro-code
import { useSelectionHandler } from "@opentui/react"

function App() {
  useSelectionHandler((selection) => {
    const text = selection.getSelectedText()
    console.log("Selected:", text)
  })

  return <text selectable>Select this text with your mouse</text>
}
```

### `useTimeline(options?)`

Create and manage animations.

``` astro-code
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

  return <box style={{ width, backgroundColor: "#6a5acd" }} />
}
```

**Options:**

-   `duration` - Animation duration in ms (default: 1000)
-   `loop` - Whether to loop (default: false)
-   `autoplay` - Auto-start (default: true)
-   `onComplete` - Completion callback
-   `onPause` - Pause callback

## Styling

Style components with props or the `style` prop:

``` astro-code
// Direct props
<box backgroundColor="blue" padding={2}>
  <text>Hello</text>
</box>

// Style prop
<box style={{ backgroundColor: "blue", padding: 2 }}>
  <text>Hello</text>
</box>
```

## Example: Login form

``` astro-code
import { createCliRenderer } from "@opentui/core"
import { createRoot, useKeyboard } from "@opentui/react"
import { useCallback, useState } from "react"

function App() {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [focused, setFocused] = useState<"username" | "password">("username")
  const [status, setStatus] = useState("idle")

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

      <text fg={status === "success" ? "green" : status === "error" ? "red" : "#999"}>{status.toUpperCase()}</text>
    </box>
  )
}

const renderer = await createCliRenderer()
createRoot(renderer).render(<App />)
```

## Component extension

Register custom renderables as JSX elements:

``` astro-code
import { BoxRenderable, createCliRenderer, type BoxOptions, type RenderContext } from "@opentui/core"
import { createRoot, extend } from "@opentui/react"

class ConsoleButtonRenderable extends BoxRenderable {
  private _label: string = "Button"

  constructor(ctx: RenderContext, options: BoxOptions & { label?: string }) {
    super(ctx, options)
    if (options.label) this._label = options.label
    this.borderStyle = "single"
    this.padding = 2
  }

  get label(): string {
    return this._label
  }

  set label(value: string) {
    this._label = value
    this.requestRender()
  }
}

// Add TypeScript support
declare module "@opentui/react" {
  interface OpenTUIComponents {
    consoleButton: typeof ConsoleButtonRenderable
  }
}

// Register the component
extend({ consoleButton: ConsoleButtonRenderable })

// Use in JSX
function App() {
  return <consoleButton label="Click me!" style={{ border: true, backgroundColor: "green" }} />
}

const renderer = await createCliRenderer()
createRoot(renderer).render(<App />)
```

## React DevTools

OpenTUI React supports React DevTools for debugging:

1.  Install:

``` astro-code
bun add --dev react-devtools-core@7
```

2.  Start DevTools:

``` astro-code
npx react-devtools@7
```

3.  Run with DEV flag:

``` astro-code
DEV=true bun run your-app.ts
```


---

_Source: https://opentui.com/docs/bindings/react
_Downloaded: 2026-05-21 19:05:07 UTC_
