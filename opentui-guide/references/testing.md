# Testing

Open when you need to write headless tests for OpenTUI components or interactions.

Uses `@opentui/core/testing` with `bun:test`. No terminal required — fully headless.

## Contents

1. Test Renderer Setup
2. Keyboard Input Testing
3. Mouse Click Testing
4. Modifier Key Testing
5. Capture & Assert Output
6. Best Practices

---

## 1. Test Renderer Setup

```typescript
import { describe, it, expect, beforeEach, afterEach } from "bun:test"
import { createTestRenderer } from "@opentui/core/testing"

describe("MyApp", () => {
  let renderer, mockInput, mockMouse, renderOnce, captureCharFrame

  beforeEach(async () => {
    const ctx = await createTestRenderer({
      width: 80,
      height: 24,
      kittyKeyboard: true,
    })
    renderer = ctx.renderer
    mockInput = ctx.mockInput
    mockMouse = ctx.mockMouse
    renderOnce = ctx.renderOnce
    captureCharFrame = ctx.captureCharFrame
  })

  afterEach(async () => {
    await renderer.idle()
    renderer.destroy()
  })
})
```

### API Reference

| API | Purpose |
|-----|---------|
| `createTestRenderer({ width, height, kittyKeyboard })` | Create headless renderer context |
| `ctx.renderer` | The CliRenderer instance |
| `ctx.mockInput` | Simulated keyboard input |
| `ctx.mockMouse` | Simulated mouse input |
| `ctx.renderOnce` | Trigger a single render cycle (returns Promise) |
| `ctx.captureCharFrame` | Capture current rendered output as string |
| `renderer.idle()` | Wait for pending async operations |
| `renderer.destroy()` | Cleanup, release terminal resources |

---

## 2. Keyboard Input Testing

```typescript
it("should handle keyboard input", async () => {
  await renderOnce()

  mockInput.pressKey("j")
  await renderOnce()

  const frame = captureCharFrame()
  expect(frame).toContain("expected text")
})
```

### Mock Input API

| Method | Purpose |
|--------|---------|
| `mockInput.pressKey(name)` | Simulate key press ("j", "enter", "escape", "up", "down") |
| `mockInput.pressEnter()` | Simulate Enter key |
| `mockInput.pressKey(name, modifiers)` | With modifiers: `{ ctrl: true }`, `{ shift: true }`, `{ super: true }`, `{ meta: true }` |

---

## 3. Mouse Click Testing

```typescript
it("should handle mouse clicks", async () => {
  await mockMouse.click(10, 5)
  await renderOnce()

  const frame = captureCharFrame()
  expect(frame).toContain("clicked")
})
```

### Mock Mouse API

| Method | Purpose |
|--------|---------|
| `mockMouse.click(x, y)` | Simulate mouse click at position |

---

## 4. Modifier Key Testing

```typescript
it("should handle modifier keys", async () => {
  mockInput.pressKey("j", { super: true })   // Cmd+J
  mockInput.pressKey("k", { ctrl: true })    // Ctrl+K
  mockInput.pressEnter()
  await renderOnce()

  const frame = captureCharFrame()
  expect(frame).toContain("modifier result")
})
```

---

## 5. Capture & Assert Output

```typescript
it("should render initial state", async () => {
  await renderOnce()
  const frame = captureCharFrame()
  expect(frame).toContain("Hello")
  expect(frame).not.toContain("Goodbye")
})
```

`captureCharFrame()` returns the rendered terminal output as a string. Use `toContain`, `toMatch`, or `not.toContain` to assert.

---

## 6. Best Practices

1. **`await renderOnce()` after every state change** before asserting — rendering is async
2. **`renderer.idle()` in afterEach** — waits for pending async operations before cleanup
3. **`renderer.destroy()` in afterEach** — releases resources, prevents test leaks
4. **Test one interaction per `it` block** — keeps failures isolated
5. **Capture frame after render, not before** — `captureCharFrame()` reads current state, does not trigger render
6. **Use `kittyKeyboard: true`** when testing key sequences that depend on kitty protocol
