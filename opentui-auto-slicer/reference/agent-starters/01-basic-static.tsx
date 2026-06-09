/**
 * 01-basic-static.tsx
 *
 * A minimal, non-interactive OpenTUI React app that demonstrates
 * layout, borders, styled text, and the basic bootstrap pattern.
 *
 * Run with:
 *   bun packages/react/examples/agent-starters/01-basic-static.tsx
 */

// AGENT NOTE: Always import createCliRenderer from @opentui/core and
// createRoot from @opentui/react. These are the two entry points.
import { createCliRenderer } from "@opentui/core"
import { createRoot } from "@opentui/react"

// AGENT NOTE: There are no DOM elements here. <box> and <text> are
// OpenTUI intrinsic elements, not HTML. They are provided by the
// jsxImportSource: "@opentui/react" setting in tsconfig.json.
function App() {
  return (
    // AGENT NOTE: <box> is the primary layout container. It supports
    // flexbox via Yoga (same properties as CSS flexbox). Use
    // flexDirection="column" to stack children vertically.
    <box style={{ flexDirection: "column", padding: 2, gap: 1 }}>
      {/* AGENT NOTE: <text> renders styled text. Use the style prop or
          direct props like fg="#00FF00" for foreground color. */}
      <text fg="#FFFF00">OpenTUI Static Layout</text>

      {/* AGENT NOTE: border={true} draws a single-line border around
          the box. title="..." places a label at the top edge. */}
      <box border title="Info Panel" style={{ padding: 1 }}>
        <text>This is a bordered box with a title.</text>
      </box>

      {/* AGENT NOTE: flexDirection="row" places children side-by-side.
          flexGrow={1} makes each child expand to fill available width. */}
      <box flexDirection="row" gap={1}>
        <box border style={{ flexGrow: 1, padding: 1, backgroundColor: "#1a1b26" }}>
          <text>Left column</text>
        </box>
        <box border style={{ flexGrow: 1, padding: 1, backgroundColor: "#1a1b26" }}>
          <text>Right column</text>
        </box>
      </box>

      {/* AGENT NOTE: Text modifiers (<strong>, <em>, <u>, <span>) must be
          children of <text>. They do not work as top-level elements. */}
      <text>
        <strong>Bold</strong>, <em>italic</em>, and <u>underlined</u> text.
      </text>
    </box>
  )
}

// AGENT NOTE: Always guard the bootstrap with import.meta.main.
// Without this guard, importing the file as a module would immediately
// start the renderer and seize the terminal.
if (import.meta.main) {
  // AGENT NOTE: createCliRenderer() is async and returns a CliRenderer.
  // It must be awaited.
  const renderer = await createCliRenderer()

  // AGENT NOTE: createRoot(renderer).render(<App />) mounts the React
  // tree into the terminal. This is the exact equivalent of ReactDOM.
  createRoot(renderer).render(<App />)
}
