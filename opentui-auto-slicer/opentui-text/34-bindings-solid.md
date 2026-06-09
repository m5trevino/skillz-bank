# Solid.js bindings

Build terminal user interfaces with Solid.js’s fine-grained reactivity and OpenTUI.

## Installation

``` astro-code
bun install solid-js @opentui/solid
```

## Setup

### 1. Configure TypeScript

Add JSX config to `tsconfig.json`:

``` astro-code
{
  "compilerOptions": {
    "jsx": "preserve",
    "jsxImportSource": "@opentui/solid"
  }
}
```

### 2. Configure Bun

Add preload script to `bunfig.toml`:

``` astro-code
preload = ["@opentui/solid/preload"]
```

### 3. Enable runtime-loaded plugin support (if needed)

If your app loads external TS/TSX modules at runtime (for example a file-based plugin system), import this once in your entry file before dynamic imports:

``` astro-code
import "@opentui/solid/runtime-plugin-support"
```

### 4. Create your app

``` astro-code
import { render } from "@opentui/solid"

const App = () => <text>Hello, World!</text>

render(App)
```

Run with `bun index.tsx`.

## Components

OpenTUI Solid provides JSX intrinsic elements that map to core renderables.

**Note:** Solid uses snake_case for multi-word component names (e.g., `ascii_font`, `tab_select`).

### Layout & display

-   `<text>` - Styled text container
-   `<box>` - Layout container with borders
-   `<scrollbox>` - Scrollable container
-   `<ascii_font>` - ASCII art text
-   `<markdown>` - Render Markdown content

QR code support is available from `@opentui/qrcode/solid` and must be registered explicitly with `registerQRCode()`.

### Input

-   `<input>` - Single-line text input
-   `<textarea>` - Multi-line text input
-   `<select>` - List selection
-   `<tab_select>` - Tab-based selection

### Code & diff

-   `<code>` - Syntax-highlighted code
-   `<line_number>` - Line numbers with diff/diagnostic support
-   `<diff>` - Unified or split diff viewer

### Text modifiers

Use inside `<text>` components:

-   `<span>` - Inline styled text
-   `<strong>`, `<b>` - Bold text
-   `<em>`, `<i>` - Italic text
-   `<u>` - Underlined text
-   `<br>` - Line break
-   `<a>` - Link text with href

## API reference

### `render(node, rendererOrConfig?)`

Render a Solid component tree into a CLI renderer.

``` astro-code
import { render } from "@opentui/solid"

// Simple usage
render(() => <App />)

// With renderer config
render(() => <App />, {
  targetFps: 30,
  exitOnCtrlC: false,
})
```

**Parameters:**

-   `node` - Function returning a JSX element
-   `rendererOrConfig` - Optional `CliRenderer` instance or `CliRendererConfig`

### `testRender(node, options?)`

Create a test renderer for snapshots and interaction tests.

``` astro-code
import { testRender } from "@opentui/solid"

const testSetup = await testRender(() => <App />, { width: 40, height: 10 })
```

### `extend(components)`

Register custom renderables as JSX intrinsic elements.

``` astro-code
import { extend } from "@opentui/solid"

extend({ custom_box: CustomBoxRenderable })
```

### `getComponentCatalogue()`

Returns the current component catalogue that powers JSX tag lookup.

For plugin slots, see [Plugin Slots overview](/docs/plugins/slots) and [Solid slots](/docs/plugins/solid).

## Scrollback writers

In [`split-footer`](/docs/core-concepts/renderer#split-footer) mode with `externalOutputMode: "capture-stdout"`, the Solid binding provides helpers that append JSX-rendered output above the footer. They wrap [`renderer.writeToScrollback`](/docs/core-concepts/renderer#writing-to-scrollback) so you can write scrollback content with signals and components.

### `writeSolidToScrollback(renderer, node, options?)`

Render a JSX node once and append it as a scrollback commit.

``` astro-code
import { writeSolidToScrollback } from "@opentui/solid"

writeSolidToScrollback(renderer, () => <text fg="#8BD5CA">api responded in 12ms</text>)
```

### `createScrollbackWriter(node, options?)`

If you need to pass the same JSX rendering to multiple `writeToScrollback` calls (or hold onto the writer inside your own code), use the lower-level factory:

``` astro-code
import { createScrollbackWriter } from "@opentui/solid"

const writer = createScrollbackWriter(() => <text>logged at {new Date().toISOString()}</text>, { startOnNewLine: true })

renderer.writeToScrollback(writer)
```

### Options

| Option            | Type      | Default        | Description                                                              |
|-------------------|-----------|----------------|--------------------------------------------------------------------------|
| `width`           | `number`  | renderer width | Override the snapshot width in columns                                   |
| `height`          | `number`  | measured auto  | Override the snapshot height in rows (otherwise measured from layout)    |
| `rowColumns`      | `number`  | snapshot width | Explicit last-row column count for tail tracking                         |
| `startOnNewLine`  | `boolean` | `true`         | Insert a newline before this commit if the previous commit ended mid-row |
| `trailingNewline` | `boolean` | \-             | Append a newline after the final row                                     |

The writer returns a `ScrollbackSnapshot` whose teardown disposes the inner Solid subtree after the snapshot renders. Use the core [`ScrollbackSurface`](/docs/core-concepts/renderer#writing-to-scrollback) APIs directly if you need streaming commits that re-render the same tree over time.

## Hooks

### `useRenderer()`

Access the OpenTUI renderer instance.

``` astro-code
import { useRenderer } from "@opentui/solid"
import { onMount } from "solid-js"

const App = () => {
  const renderer = useRenderer()

  onMount(() => {
    renderer.console.show()
    console.log("Hello from console!")
  })

  return <box />
}
```

### `useKeyboard(handler, options?)`

Subscribe to keyboard events.

``` astro-code
import { useKeyboard, useRenderer } from "@opentui/solid"

const App = () => {
  const renderer = useRenderer()

  useKeyboard((key) => {
    if (key.name === "escape") {
      renderer.destroy()
    }
  })

  return <text>Press ESC to close</text>
}
```

With release events:

``` astro-code
import { createSignal } from "solid-js"

const App = () => {
  const [pressedKeys, setPressedKeys] = createSignal(new Set<string>())

  useKeyboard(
    (event) => {
      setPressedKeys((keys) => {
        const newKeys = new Set(keys)
        if (event.eventType === "release") {
          newKeys.delete(event.name)
        } else {
          newKeys.add(event.name)
        }
        return newKeys
      })
    },
    { release: true },
  )

  return <text>Pressed: {Array.from(pressedKeys()).join(", ") || "none"}</text>
}
```

### `onResize(callback)`

Handle terminal resize events.

``` astro-code
import { onResize } from "@opentui/solid"

const App = () => {
  onResize((width, height) => {
    console.log(`Resized to ${width}x${height}`)
  })

  return <text>Resize-aware component</text>
}
```

### `onFocus(callback)`

Run side effects when the terminal window gains focus.

``` astro-code
import { onFocus } from "@opentui/solid"

const App = () => {
  onFocus(() => {
    console.log("Terminal focused")
  })

  return <text>Switch away and back to trigger focus events</text>
}
```

### `onBlur(callback)`

Run side effects when the terminal window loses focus.

``` astro-code
import { onBlur } from "@opentui/solid"

const App = () => {
  onBlur(() => {
    console.log("Terminal blurred")
  })

  return <text>Switch away and back to trigger blur events</text>
}
```

These hooks listen for terminal focus-in/focus-out events when the terminal emulator supports them.

### `useTerminalDimensions()`

Get reactive terminal dimensions (returns a Solid signal).

``` astro-code
import { useTerminalDimensions } from "@opentui/solid"

const App = () => {
  const dimensions = useTerminalDimensions()

  return (
    <text>
      Terminal: {dimensions().width}x{dimensions().height}
    </text>
  )
}
```

### `usePaste(handler)`

Subscribe to paste events.

``` astro-code
import { usePaste } from "@opentui/solid"

const textDecoder = new TextDecoder()

const App = () => {
  usePaste((event) => {
    console.log("Pasted:", textDecoder.decode(event.bytes))
  })

  return <text>Paste something!</text>
}
```

### `useSelectionHandler(callback)`

Handle text selection events.

``` astro-code
import { useSelectionHandler } from "@opentui/solid"

const App = () => {
  useSelectionHandler((selection) => {
    console.log("Selected:", selection)
  })

  return <text selectable>Select me!</text>
}
```

### `useTimeline(options?)`

Create and manage animations.

``` astro-code
import { useTimeline } from "@opentui/solid"
import { createSignal, onMount } from "solid-js"

const App = () => {
  const [width, setWidth] = createSignal(0)

  const timeline = useTimeline({
    duration: 2000,
    loop: false,
  })

  onMount(() => {
    timeline.add(
      { width: width() },
      {
        width: 50,
        duration: 2000,
        ease: "linear",
        onUpdate: (animation) => {
          setWidth(animation.targets[0].width)
        },
      },
    )
  })

  return <box style={{ width: width(), backgroundColor: "#6a5acd" }} />
}
```

## Special components

### `Portal`

Render children into a different mount point (useful for modals and overlays).

``` astro-code
import { Portal, useRenderer } from "@opentui/solid"

const App = () => {
  const renderer = useRenderer()

  return (
    <box>
      <text>Main content</text>
      <Portal mount={renderer.root}>
        <box border>Overlay</box>
      </Portal>
    </box>
  )
}
```

### `Dynamic`

Render arbitrary intrinsic elements or components dynamically.

``` astro-code
import { Dynamic } from "@opentui/solid"
import { createSignal } from "solid-js"

const App = () => {
  const [isMultiline, setIsMultiline] = createSignal(false)

  return <Dynamic component={isMultiline() ? "textarea" : "input"} />
}
```

## Building for production

Use [Bun.build](https://bun.sh/docs/bundler) with the Solid plugin:

``` astro-code
import solidPlugin from "@opentui/solid/bun-plugin"

await Bun.build({
  entrypoints: ["./index.tsx"],
  target: "bun",
  outdir: "./build",
  plugins: [solidPlugin],
})
```

To compile to a standalone executable:

``` astro-code
await Bun.build({
  entrypoints: ["./index.tsx"],
  plugins: [solidPlugin],
  compile: {
    target: "bun-darwin-arm64",
    outfile: "./app-macos",
  },
})
```

If that executable loads external plugins/modules at runtime, keep `import "@opentui/solid/runtime-plugin-support"` in your app entry.

## Example: counter

``` astro-code
import { render, useKeyboard, useRenderer } from "@opentui/solid"
import { createSignal } from "solid-js"

const App = () => {
  const [count, setCount] = createSignal(0)
  const renderer = useRenderer()

  useKeyboard((key) => {
    if (key.name === "up") setCount((c) => c + 1)
    if (key.name === "down") setCount((c) => c - 1)
    if (key.name === "escape") renderer.destroy()
  })

  return (
    <box border padding={2}>
      <text>Count: {count()}</text>
      <text fg="#888">Up/Down to change, ESC to close</text>
    </box>
  )
}

render(App)
```

## Differences from React bindings

| Aspect             | Solid                                                  | React                                  |
|--------------------|--------------------------------------------------------|----------------------------------------|
| Render function    | `render(() => <App />)`                                | `createRoot(renderer).render(<App />)` |
| Component naming   | snake_case (`ascii_font`)                              | kebab-case (`ascii-font`)              |
| State              | `createSignal`                                         | `useState`                             |
| Effects            | `onMount`, `onCleanup`                                 | `useEffect`                            |
| Resize hook        | `onResize(callback)`                                   | `useOnResize(callback)`                |
| Dimensions         | Returns signal: `dimensions().width`                   | Returns object: `dimensions.width`     |
| Extra hooks        | `onFocus`, `onBlur`, `usePaste`, `useSelectionHandler` | \-                                     |
| Special components | `Portal`, `Dynamic`                                    | \-                                     |


---

_Source: https://opentui.com/docs/bindings/solid
_Downloaded: 2026-05-21 19:05:06 UTC_
