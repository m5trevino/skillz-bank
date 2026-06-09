# OpenTUI Core Renderables Reference

**Scope:** `@opentui/core` imperative renderables only.  
**Source:** `packages/core/src/renderables/*.ts`

---

## How to Import

All renderables are exported from `@opentui/core`:

```typescript
import {
  createCliRenderer,
  BoxRenderable,
  TextRenderable,
  InputRenderable,
  TextareaRenderable,
  SelectRenderable,
  ScrollBoxRenderable,
  CodeRenderable,
  LineNumberRenderable,
  ASCIIFontRenderable,
  EditBufferRenderable,
  DiffRenderable,
  MarkdownRenderable,
  SyntaxStyle,
  RGBA,
} from "@opentui/core"
```

Create a renderer, instantiate renderables, add them to the root or to parent renderables:

```typescript
const renderer = await createCliRenderer()
const box = new BoxRenderable(renderer, { border: true, title: "Example" })
const text = new TextRenderable(renderer, { content: "Hello, world!" })
box.add(text)
renderer.root.add(box)
```

---

## Common Options (RenderableOptions)

All renderables inherit these base options:

| Option | Type | Description |
|--------|------|-------------|
| `id` | `string` | Unique identifier |
| `width` / `height` | `number \| "auto" \| "100%" \| `${number}%`` | Dimensions |
| `minWidth` / `maxWidth` / `minHeight` / `maxHeight` | `number \| "100%" \| `${number}%`` | Size constraints |
| `x` / `y` | `number` | Absolute position (when not in flex layout) |
| `flexDirection` | `"row" \| "column"` | Flex container direction |
| `flexGrow` / `flexShrink` / `flexBasis` | `number` | Flex behavior |
| `alignItems` / `alignSelf` / `justifyContent` | Flex alignment enums | Layout alignment |
| `padding` / `paddingX` / `paddingY` / `paddingTop` / `paddingRight` / `paddingBottom` / `paddingLeft` | `number \| "${number}%" \| null` | Inner spacing |
| `margin` / `marginX` / `marginY` / `marginTop` / `marginRight` / `marginBottom` / `marginLeft` | `number \| "${number}%" \| null` | Outer spacing |
| `overflow` | `"visible" \| "hidden" \| "scroll"` | Overflow behavior |
| `visible` | `boolean` | Whether the renderable is drawn |
| `buffered` | `boolean` | Use frame-buffered rendering |

---

## Component Reference

### 1. BoxRenderable

**File:** `packages/core/src/renderables/Box.ts`

Container with borders, background, and flex layout. The workhorse layout primitive.

**Key Props (BoxOptions):**

| Prop | Type | Description |
|------|------|-------------|
| `backgroundColor` | `string \| RGBA` | Fill color (default: `"transparent"`) |
| `border` | `boolean \| BorderSides[]` | Enable border or specific sides |
| `borderStyle` | `BorderStyle` | `"single"`, `"double"`, `"round"`, etc. |
| `borderColor` | `string \| RGBA` | Border color (default: `"#FFFFFF"`) |
| `focusedBorderColor` | `string \| RGBA` | Border color when focused (default: `"#00AAFF"`) |
| `customBorderChars` | `BorderCharacters` | Custom glyph set for borders |
| `title` | `string` | Top-center title text |
| `titleAlignment` | `"left" \| "center" \| "right"` | Title position |
| `bottomTitle` | `string` | Bottom title text |
| `bottomTitleAlignment` | `"left" \| "center" \| "right"` | Bottom title position |
| `shouldFill` | `boolean` | Fill background (default: `true`) |
| `focusable` | `boolean` | Can receive focus |
| `gap` / `rowGap` / `columnGap` | `number \| "${number}%"` | Flex gap between children |

**Minimal Example:**

```typescript
const box = new BoxRenderable(renderer, {
  border: true,
  title: "My Box",
  padding: 1,
  flexDirection: "column",
  gap: 1,
})
renderer.root.add(box)
```

---

### 2. TextRenderable

**File:** `packages/core/src/renderables/Text.ts`

Displays styled text. Supports inline `StyledText` for rich formatting.

**Key Props (TextOptions extends TextBufferOptions):**

| Prop | Type | Description |
|------|------|-------------|
| `content` | `string \| StyledText` | Text to display |
| `fg` | `string \| RGBA` | Foreground color |
| `bg` | `string \| RGBA` | Background color |
| `attributes` | `number` | Text attributes (bold, italic, underline, dim) |

**Minimal Example:**

```typescript
const text = new TextRenderable(renderer, {
  content: "Hello, world!",
  fg: "#00FF00",
})
renderer.root.add(text)
```

---

### 3. InputRenderable

**File:** `packages/core/src/renderables/Input.ts`

Single-line text input. Extends `TextareaRenderable` with single-line constraints.

**Key Props (InputRenderableOptions):**

| Prop | Type | Description |
|------|------|-------------|
| `value` | `string` | Initial text value |
| `placeholder` | `string` | Placeholder text |
| `maxLength` | `number` | Max characters (default: `1000`) |
| `backgroundColor` | `ColorInput` | Unfocused background |
| `textColor` | `ColorInput` | Unfocused text color |
| `focusedBackgroundColor` | `ColorInput` | Focused background |
| `focusedTextColor` | `ColorInput` | Focused text color |
| `keyBindings` | `KeyBinding[]` | Custom key bindings |
| `keyAliasMap` | `Record<string, string>` | Key name aliases |

**Events:** `InputRenderableEvents.INPUT`, `CHANGE`, `ENTER`

**Minimal Example:**

```typescript
const input = new InputRenderable(renderer, {
  placeholder: "Type here...",
  value: "default",
  width: 40,
})
input.on(InputRenderableEvents.INPUT, (value: string) => {
  console.log("Input:", value)
})
input.on(InputRenderableEvents.ENTER, (value: string) => {
  console.log("Submitted:", value)
})
renderer.root.add(input)
```

---

### 4. TextareaRenderable

**File:** `packages/core/src/renderables/Textarea.ts`

Multi-line text editor with cursor, selection, undo/redo, and keybindings.

**Key Props (TextareaOptions extends EditBufferOptions):**

| Prop | Type | Description |
|------|------|-------------|
| `initialValue` | `string` | Starting text |
| `placeholder` | `StyledText \| string \| null` | Placeholder text |
| `placeholderColor` | `ColorInput` | Placeholder color (default: `"#666666"`) |
| `backgroundColor` | `ColorInput` | Unfocused background |
| `textColor` | `ColorInput` | Unfocused text color |
| `focusedBackgroundColor` | `ColorInput` | Focused background |
| `focusedTextColor` | `ColorInput` | Focused text color |
| `keyBindings` | `KeyBinding[]` | Custom key bindings |
| `keyAliasMap` | `Record<string, string>` | Key name aliases |
| `onSubmit` | `(event: SubmitEvent) => void` | Submit callback |

**Minimal Example:**

```typescript
const textarea = new TextareaRenderable(renderer, {
  initialValue: "Line 1\nLine 2",
  placeholder: "Enter text...",
  width: 60,
  height: 10,
})
renderer.root.add(textarea)
```

---

### 5. SelectRenderable

**File:** `packages/core/src/renderables/Select.ts`

List selection component with keyboard navigation.

**Key Props (SelectRenderableOptions):**

| Prop | Type | Description |
|------|------|-------------|
| `options` | `SelectOption[]` | Items to display `{ name, description, value? }` |
| `selectedIndex` | `number` | Initially selected index (default: `0`) |
| `backgroundColor` | `ColorInput` | Unfocused background |
| `textColor` | `ColorInput` | Unfocused text color |
| `focusedBackgroundColor` | `ColorInput` | Focused background |
| `focusedTextColor` | `ColorInput` | Focused text color |
| `selectedBackgroundColor` | `ColorInput` | Selected row bg (default: `"#334455"`) |
| `selectedTextColor` | `ColorInput` | Selected row fg (default: `"#FFFF00"`) |
| `showScrollIndicator` | `boolean` | Show scrollbar |
| `wrapSelection` | `boolean` | Wrap around at edges |
| `showDescription` | `boolean` | Show item descriptions |
| `font` | `ASCIIFontName` | Use ASCII font for item names |
| `keyBindings` | `SelectKeyBinding[]` | Custom key bindings |

**Events:** `SelectRenderableEvents.SELECTION_CHANGED`, `ITEM_SELECTED`

**Minimal Example:**

```typescript
const select = new SelectRenderable(renderer, {
  options: [
    { name: "Option 1", description: "First choice", value: "opt1" },
    { name: "Option 2", description: "Second choice", value: "opt2" },
  ],
  showDescription: true,
  width: 40,
  height: 10,
})
select.on(SelectRenderableEvents.ITEM_SELECTED, (index, option) => {
  console.log("Selected:", option.value)
})
renderer.root.add(select)
```

---

### 6. ScrollBoxRenderable

**File:** `packages/core/src/renderables/ScrollBox.ts`

Scrollable container with viewport, content area, and optional scrollbars.

**Key Props (ScrollBoxOptions extends BoxOptions):**

| Prop | Type | Description |
|------|------|-------------|
| `rootOptions` | `BoxOptions` | Style the outer root box |
| `wrapperOptions` | `BoxOptions` | Style the wrapper |
| `viewportOptions` | `BoxOptions` | Style the viewport |
| `contentOptions` | `BoxOptions` | Style the content container |
| `scrollbarOptions` | `Omit<ScrollBarOptions, "orientation">` | Shared scrollbar style |
| `verticalScrollbarOptions` | `Omit<ScrollBarOptions, "orientation">` | Vertical scrollbar style |
| `horizontalScrollbarOptions` | `Omit<ScrollBarOptions, "orientation">` | Horizontal scrollbar style |
| `scrollX` | `boolean` | Enable horizontal scroll (default: `false`) |
| `scrollY` | `boolean` | Enable vertical scroll (default: `true`) |
| `stickyScroll` | `boolean` | Auto-scroll to edges |
| `stickyStart` | `"bottom" \| "top" \| "left" \| "right"` | Sticky edge |
| `viewportCulling` | `boolean` | Skip off-screen children (default: `true`) |

**Minimal Example:**

```typescript
const scrollbox = new ScrollBoxRenderable(renderer, {
  width: 60,
  height: 20,
  scrollY: true,
  border: true,
})
for (let i = 0; i < 100; i++) {
  scrollbox.add(new TextRenderable(renderer, { content: `Line ${i}` }))
}
renderer.root.add(scrollbox)
```

---

### 7. CodeRenderable

**File:** `packages/core/src/renderables/Code.ts`

Syntax-highlighted code block using Tree-sitter.

**Key Props (CodeOptions extends TextBufferOptions):**

| Prop | Type | Description |
|------|------|-------------|
| `content` | `string` | Code text |
| `filetype` | `string` | Language identifier (e.g. `"typescript"`, `"javascript"`) |
| `syntaxStyle` | `SyntaxStyle` | Color theme for tokens |
| `conceal` | `boolean` | Hide syntax markers (default: `true`) |
| `drawUnstyledText` | `boolean` | Show plain text before highlight (default: `true`) |
| `streaming` | `boolean` | Incremental update mode (default: `false`) |
| `treeSitterClient` | `TreeSitterClient` | Custom parser client |
| `onHighlight` | `OnHighlightCallback` | Post-process highlights |
| `onChunks` | `OnChunksCallback` | Post-process text chunks |

**Minimal Example:**

```typescript
const syntaxStyle = SyntaxStyle.fromStyles({
  keyword: { fg: RGBA.fromHex("#ff6b6b"), bold: true },
  string: { fg: RGBA.fromHex("#51cf66") },
  default: { fg: RGBA.fromHex("#ffffff") },
})

const code = new CodeRenderable(renderer, {
  content: `const x = 42`,
  filetype: "javascript",
  syntaxStyle,
  width: 60,
  height: 10,
})
renderer.root.add(code)
```

---

### 8. LineNumberRenderable

**File:** `packages/core/src/renderables/LineNumberRenderable.ts`

Gutter with line numbers, diff highlights, and diagnostic signs. Wraps a target `Renderable & LineInfoProvider` (e.g., `CodeRenderable`).

**Key Props (LineNumberOptions):**

| Prop | Type | Description |
|------|------|-------------|
| `target` | `Renderable & LineInfoProvider` | The content renderable to number |
| `fg` | `string \| RGBA` | Gutter text color (default: `"#888888"`) |
| `bg` | `string \| RGBA` | Gutter background (default: `"transparent"`) |
| `minWidth` | `number` | Minimum gutter width (default: `3`) |
| `paddingRight` | `number` | Right padding (default: `1`) |
| `showLineNumbers` | `boolean` | Toggle visibility |
| `lineNumberOffset` | `number` | Offset added to displayed numbers |
| `lineColors` | `Map<number, string \| RGBA \| LineColorConfig>` | Per-line bg colors |
| `lineSigns` | `Map<number, LineSign>` | Per-line signs `{ before?, beforeColor?, after?, afterColor? }` |
| `hideLineNumbers` | `Set<number>` | Logical lines to hide numbers for |
| `lineNumbers` | `Map<number, number>` | Override displayed number per logical line |

**Minimal Example:**

```typescript
const code = new CodeRenderable(renderer, {
  content: "function hello() {\n  return 42\n}",
  filetype: "javascript",
  syntaxStyle,
  width: "100%",
  height: 10,
})

const lineNumbers = new LineNumberRenderable(renderer, {
  showLineNumbers: true,
  minWidth: 3,
  paddingRight: 1,
})
lineNumbers.add(code)

const container = new BoxRenderable(renderer, { flexDirection: "row", border: true })
container.add(lineNumbers)
renderer.root.add(container)
```

---

### 9. ASCIIFontRenderable

**File:** `packages/core/src/renderables/ASCIIFont.ts`

Renders text using block ASCII art fonts.

**Key Props (ASCIIFontOptions):**

| Prop | Type | Description |
|------|------|-------------|
| `text` | `string` | Text to render |
| `font` | `ASCIIFontName` | Font key: `"tiny"`, `"block"`, `"slick"`, `"shade"`, etc. |
| `color` | `ColorInput \| ColorInput[]` | Text color(s) |
| `backgroundColor` | `ColorInput` | Background color (default: `"transparent"`) |
| `selectionBg` | `ColorInput` | Selection background |
| `selectionFg` | `ColorInput` | Selection foreground |
| `selectable` | `boolean` | Allow text selection (default: `true`) |

**Minimal Example:**

```typescript
const ascii = new ASCIIFontRenderable(renderer, {
  text: "HELLO",
  font: "block",
  color: "#FF00FF",
})
renderer.root.add(ascii)
```

---

### 10. EditBufferRenderable

**File:** `packages/core/src/renderables/EditBufferRenderable.ts`

Abstract base for text-editing components. Used directly or extended for custom editors.

**Key Props (EditBufferOptions):**

| Prop | Type | Description |
|------|------|-------------|
| `textColor` | `string \| RGBA` | Text color |
| `backgroundColor` | `string \| RGBA` | Background color |
| `selectionBg` | `string \| RGBA` | Selection background |
| `selectionFg` | `string \| RGBA` | Selection foreground |
| `selectable` | `boolean` | Allow selection |
| `attributes` | `number` | Text attributes |
| `wrapMode` | `"none" \| "char" \| "word"` | Wrapping mode (default: `"word"`) |
| `showCursor` | `boolean` | Show cursor (default: `true`) |
| `cursorColor` | `string \| RGBA` | Cursor color |
| `cursorStyle` | `CursorStyleOptions` | `{ style: "block" \| "line" \| "underline", blinking: boolean }` |
| `syntaxStyle` | `SyntaxStyle` | Syntax highlighting theme |
| `tabIndicator` | `string \| number` | Visual tab indicator |
| `onCursorChange` | `(event: CursorChangeEvent) => void` | Cursor moved callback |
| `onContentChange` | `(event: ContentChangeEvent) => void` | Content changed callback |

**Minimal Example:**

```typescript
const editor = new EditBufferRenderable(renderer, {
  textColor: "#FFFFFF",
  backgroundColor: "#1a1b26",
  cursorStyle: { style: "block", blinking: true },
  width: 80,
  height: 24,
})
renderer.root.add(editor)
```

---

### 11. DiffRenderable

**File:** `packages/core/src/renderables/Diff.ts`

Unified or split diff viewer with syntax highlighting and line numbers.

**Key Props (DiffRenderableOptions):**

| Prop | Type | Description |
|------|------|-------------|
| `diff` | `string` | Unified diff text |
| `view` | `"unified" \| "split"` | Layout mode (default: `"unified"`) |
| `syncScroll` | `boolean` | Sync scroll in split mode |
| `fg` | `string \| RGBA` | Text color |
| `filetype` | `string` | Language for syntax highlighting |
| `syntaxStyle` | `SyntaxStyle` | Syntax theme |
| `wrapMode` | `"word" \| "char" \| "none"` | Text wrapping |
| `conceal` | `boolean` | Conceal syntax markers |
| `showLineNumbers` | `boolean` | Show line numbers (default: `true`) |
| `addedBg` / `removedBg` / `contextBg` | `string \| RGBA` | Line background colors |
| `addedSignColor` / `removedSignColor` | `string \| RGBA` | Sign colors |

**Minimal Example:**

```typescript
const diff = new DiffRenderable(renderer, {
  diff: `--- a/file.ts\n+++ b/file.ts\n@@ -1,3 +1,3 @@\n- old\n+ new\n  context`,
  view: "unified",
  showLineNumbers: true,
  width: 80,
  height: 20,
})
renderer.root.add(diff)
```

---

### 12. MarkdownRenderable

**File:** `packages/core/src/renderables/Markdown.ts`

Renders Markdown to styled text, lists, code blocks, blockquotes, and tables.

**Key Props (MarkdownOptions):**

| Prop | Type | Description |
|------|------|-------------|
| `content` | `string` | Markdown source |
| `syntaxStyle` | `SyntaxStyle` | Color theme |
| `fg` | `ColorInput` | Default text color |
| `bg` | `ColorInput` | Default background |
| `conceal` | `boolean` | Hide syntax markers in text (default: `true`) |
| `concealCode` | `boolean` | Hide syntax markers in code blocks (default: `false`) |
| `streaming` | `boolean` | Incremental render mode (default: `false`) |
| `tableOptions` | `MarkdownTableOptions` | Table styling |
| `renderNode` | `(token, context) => Renderable \| undefined \| null` | Custom node renderer |

**Minimal Example:**

```typescript
const md = new MarkdownRenderable(renderer, {
  content: "# Heading\n\nSome **bold** text and `code`.",
  syntaxStyle,
  width: 80,
  height: 20,
})
renderer.root.add(md)
```

---

## Quick Type Reference

```typescript
type ColorInput = string | RGBA

interface SelectOption {
  name: string
  description: string
  value?: any
}

interface LineSign {
  before?: string
  beforeColor?: string | RGBA
  after?: string
  afterColor?: string | RGBA
}

interface LineColorConfig {
  gutter?: string | RGBA
  content?: string | RGBA
}

interface CursorStyleOptions {
  style: "block" | "line" | "underline"
  blinking: boolean
}
```
