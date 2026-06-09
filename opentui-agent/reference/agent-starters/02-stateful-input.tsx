/**
 * 02-stateful-input.tsx
 *
 * A minimal interactive OpenTUI React app with state, keyboard input,
 * a focused text input, and form submission handling.
 *
 * Run with:
 *   bun packages/react/examples/agent-starters/02-stateful-input.tsx
 */

// AGENT NOTE: createCliRenderer is the imperative entry point.
// useKeyboard and useRenderer are React hooks from @opentui/react.
import { createCliRenderer } from "@opentui/core"
import { createRoot, useKeyboard, useRenderer } from "@opentui/react"
import { useCallback, useEffect, useState } from "react"

function App() {
  // AGENT NOTE: Standard React hooks work exactly as expected.
  // useState drives re-renders which update the terminal output.
  const [value, setValue] = useState("")
  const [submitted, setSubmitted] = useState<string | null>(null)

  // AGENT NOTE: useRenderer() gives access to the CliRenderer instance.
  // You need this to call renderer.console.show() or renderer.destroy().
  const renderer = useRenderer()

  // AGENT NOTE: console.log is INVISIBLE while the TUI runs.
  // Call renderer.console.show() inside useEffect so logs are visible
  // in the built-in console overlay.
  useEffect(() => {
    renderer.console.show()
    console.log("App started. Type something and press Enter.")
  }, [renderer])

  // AGENT NOTE: useKeyboard registers a global key handler.
  // It receives KeyEvent objects with .name, .ctrl, .meta, etc.
  useKeyboard((key) => {
    // AGENT NOTE: Always check key.name, not key.code.
    // "escape" is the standard way to exit a TUI app.
    if (key.name === "escape") {
      console.log("Exiting...")
      // AGENT NOTE: renderer.destroy() restores terminal state.
      // Without it, the shell may be left blank or cursor-hidden.
      renderer.destroy()
      process.exit(0)
    }
  })

  // AGENT NOTE: <input> is a single-line text field.
  // onInput fires on every keystroke. onSubmit fires when the user
  // presses Enter (Return).
  const handleSubmit = useCallback(() => {
    console.log("Submitted:", value)
    setSubmitted(value)
  }, [value])

  return (
    <box style={{ flexDirection: "column", padding: 2, gap: 1 }}>
      <text fg="#FFFF00">Stateful Input Demo</text>

      {/* AGENT NOTE: A box with border and padding creates a visual
          frame for the input field. height={3} reserves space for
          the border (top + bottom = 2 cells) plus one line of text. */}
      <box border title="Enter text" style={{ width: 50, height: 3 }}>
        <input
          // AGENT NOTE: focused={true} gives this input initial focus.
          // Only one focusable component should be focused at a time.
          focused={true}
          placeholder="Type here..."
          // AGENT NOTE: onInput receives the current string value.
          // It is called on every character change.
          onInput={setValue}
          // AGENT NOTE: onSubmit fires when the user presses Enter.
          // It does NOT fire onInput again.
          onSubmit={handleSubmit}
        />
      </box>

      {/* AGENT NOTE: Conditional rendering works exactly like React DOM.
          Use standard ternary or && expressions. */}
      {submitted ? (
        <text fg="#00FF00">Submitted: {submitted}</text>
      ) : (
        <text fg="#888888">Press Enter to submit. Press ESC to exit.</text>
      )}
    </box>
  )
}

// AGENT NOTE: This guard prevents the renderer from starting when the
// file is imported by another module (e.g. for testing or composition).
if (import.meta.main) {
  const renderer = await createCliRenderer()
  createRoot(renderer).render(<App />)
}
