# Patterns

Open when you need a concrete code example for a common OpenTUI UI pattern.

## Contents

1. Static Layout
2. Stateful Input Form
3. Select List
4. Code Block with Syntax Highlighting
5. Multi-View Application
6. Modal Dialog
7. Focus Management (Tab Switching)
8. List with Keyboard Selection
9. Responsive Layout
10. Loading Spinner
11. Syntax Style Configuration
12. Scrollbox with Scrollbar Styling
13. Timeline Animation

---

## 1. Static Layout

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

## 2. Stateful Input Form

```tsx
import { useKeyboard, useRenderer } from "@opentui/react"
import { useCallback, useEffect, useState } from "react"

function App() {
  const [value, setValue] = useState("")
  const [submitted, setSubmitted] = useState<string | null>(null)
  const renderer = useRenderer()

  useEffect(() => { renderer.console.show() }, [renderer])

  useKeyboard((key) => {
    if (key.name === "escape") {
      renderer.destroy()
      process.exit(0)
    }
  })

  return (
    <box style={{ flexDirection: "column", padding: 2, gap: 1 }}>
      <box border title="Input" style={{ width: 50, height: 3 }}>
        <input focused={true} placeholder="Type here..." onInput={setValue}
          onSubmit={() => setSubmitted(value)} />
      </box>
      {submitted && <text fg="#00FF00">Submitted: {submitted}</text>}
    </box>
  )
}
```

---

## 3. Select List

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
        onItemSelected={(index, option) => console.log("Selected:", option.value)}
      />
    </box>
  )
}
```

---

## 4. Code Block with Syntax Highlighting

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
      <code content={`const x = 42`} filetype="javascript"
        syntaxStyle={syntaxStyle} width={60} height={10} />
    </box>
  )
}
```

---

## 5. Multi-View Application

```tsx
import { useState } from "react"
import { useKeyboard } from "@opentui/react"

type View = "home" | "settings" | "help"

function App() {
  const [view, setView] = useState<View>("home")

  useKeyboard((key) => {
    if (key.name === "1") setView("home")
    if (key.name === "2") setView("settings")
    if (key.name === "3") setView("help")
    if (key.name === "escape") process.exit(0)
  })

  return (
    <box style={{ flexDirection: "column", width: "100%", height: "100%" }}>
      {view === "home" && <text>Home View</text>}
      {view === "settings" && <text>Settings View</text>}
      {view === "help" && <text>Help View</text>}
    </box>
  )
}
```

---

## 6. Modal Dialog

```tsx
import { useState } from "react"
import { useKeyboard } from "@opentui/react"

function App() {
  const [showModal, setShowModal] = useState(false)

  useKeyboard((key) => {
    if (showModal) return
    if (key.name === "m") setShowModal(true)
  })

  return (
    <>
      <text>Press m to open modal</text>
      {showModal && <Modal onClose={() => setShowModal(false)} />}
    </>
  )
}

function Modal({ onClose }: { onClose: () => void }) {
  const [input, setInput] = useState("")
  useKeyboard((key) => { if (key.name === "escape") onClose() })

  return (
    <box style={{
      position: "absolute", top: "50%", left: "50%",
      width: 60, height: 10, backgroundColor: "#1a1a1a",
      border: true, borderColor: "#FFFFFF",
    }}>
      <input placeholder="Enter value..." value={input} focused={true}
        onInput={setInput}
        onSubmit={(val) => { console.log("Submitted:", val); onClose() }} />
    </box>
  )
}
```

---

## 7. Focus Management (Tab Switching)

```tsx
import { useState } from "react"
import { useKeyboard } from "@opentui/react"

type FocusPanel = "left" | "right"

function App() {
  const [focused, setFocused] = useState<FocusPanel>("left")

  useKeyboard((key) => {
    if (key.name === "tab") setFocused(focused === "left" ? "right" : "left")
  })

  return (
    <box style={{ flexDirection: "row", width: "100%", height: "100%" }}>
      <box title="Left" style={{ flexGrow: 1, border: true }} focused={focused === "left"}>
        <text>Content</text>
      </box>
      <box title="Right" style={{ flexGrow: 1, border: true }} focused={focused === "right"}>
        <text>Content</text>
      </box>
    </box>
  )
}
```

---

## 8. List with Keyboard Selection

```tsx
import { useState } from "react"
import { useKeyboard } from "@opentui/react"

function FileList({ files }: { files: string[] }) {
  const [selected, setSelected] = useState(0)

  useKeyboard((key) => {
    if (key.name === "up") setSelected(Math.max(0, selected - 1))
    if (key.name === "down") setSelected(Math.min(files.length - 1, selected + 1))
    if (key.name === "enter") console.log("Selected:", files[selected])
  })

  return (
    <box style={{ flexDirection: "column" }}>
      {files.map((file, idx) => (
        <text key={file}
          fg={idx === selected ? "#00FF00" : "#FFFFFF"}
          bg={idx === selected ? "#333333" : undefined}>
          {idx === selected ? "> " : "  "}{file}
        </text>
      ))}
    </box>
  )
}
```

---

## 9. Responsive Layout

```tsx
import { useTerminalDimensions } from "@opentui/react"

function App() {
  const { width, height } = useTerminalDimensions()
  const isSmall = width < 80

  return (
    <box style={{ flexDirection: isSmall ? "column" : "row", width, height }}>
      <box style={{ width: isSmall ? width : 30 }}><text>Sidebar</text></box>
      <box style={{ width: isSmall ? width : width - 30 }}><text>Main</text></box>
    </box>
  )
}
```

---

## 10. Loading Spinner

```tsx
import { useState, useEffect } from "react"

function Spinner() {
  const [frame, setFrame] = useState(0)
  const frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

  useEffect(() => {
    const id = setInterval(() => setFrame((f) => (f + 1) % frames.length), 80)
    return () => clearInterval(id)
  }, [])

  return <text fg="#00FFFF">{frames[frame]} Loading...</text>
}
```

---

## 11. Syntax Style Configuration

Full theme with all token types:

```tsx
import { SyntaxStyle, RGBA } from "@opentui/core"

const syntaxStyle = SyntaxStyle.fromStyles({
  keyword: { fg: RGBA.fromHex("#ff6b6b"), bold: true },
  string: { fg: RGBA.fromHex("#51cf66") },
  comment: { fg: RGBA.fromHex("#868e96"), italic: true },
  function: { fg: RGBA.fromHex("#4dabf7") },
  number: { fg: RGBA.fromHex("#ffd43b") },
})
```

---

## 12. Scrollbox with Scrollbar Styling

```tsx
<scrollbox focused={true} style={{
  height: 20,
  rootOptions: { backgroundColor: "#24283b" },
  wrapperOptions: { backgroundColor: "#1f2335" },
  viewportOptions: { backgroundColor: "#1a1b26" },
  contentOptions: { backgroundColor: "#16161e" },
  scrollbarOptions: {
    showArrows: true,
    trackOptions: { foregroundColor: "#7aa2f7", backgroundColor: "#414868" },
  },
}}>
  {/* scrollable children */}
</scrollbox>
```

Imperative scroll control:
```typescript
scrollbox.scrollBy({ y: 10, unit: "line" })
scrollbox.scrollTo({ x: 0, y: 100 })
```

---

## 13. Timeline Animation

```tsx
import { useTimeline } from "@opentui/react"
import { useEffect, useState } from "react"

function AnimatedBox() {
  const [width, setWidth] = useState(0)
  const timeline = useTimeline({ duration: 2000, loop: false, autoplay: true })

  useEffect(() => {
    timeline.add({ width }, {
      width: 50, duration: 2000, ease: "linear",
      onUpdate: (anim) => setWidth(anim.targets[0].width),
    })
  }, [])

  return <box style={{ width }}><text>Animating...</text></box>
}
```
