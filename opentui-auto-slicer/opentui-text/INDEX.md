# OpenTUI Documentation — Full Text Archive

Downloaded on 2026-05-21 from the pages listed at https://opentui.com/docs

This bundle contains clean Markdown text extracted from every page the user requested.

## Files (46 pages + raw README)

- [00-home.md](00-home.md) — OpenTUI Home (Landing Page)
- [01-github-README-raw.md](01-github-README-raw.md) — GitHub README (raw, best version)
- [01-github-repo.md](01-github-repo.md) — GitHub Repo (rendered view)
- [02-getting-started.md](02-getting-started.md) — Getting Started
- [03-renderer.md](03-renderer.md) — Core Concepts: Renderer
- [04-renderables.md](04-renderables.md) — Core Concepts: Renderables
- [05-constructs.md](05-constructs.md) — Core Concepts: Constructs
- [06-renderables-vs-constructs.md](06-renderables.md) — Core Concepts: Renderables vs Constructs
- [07-layout.md](07-layout.md) — Core Concepts: Layout System
- [08-keyboard.md](08-keyboard.md) — Core Concepts: Keyboard Input
- [09-console.md](09-console.md) — Core Concepts: Console Overlay
- [10-notifications.md](10-notifications.md) — Core Concepts: Notifications
- [11-colors.md](11-colors.md) — Core Concepts: Colors
- [12-lifecycle.md](12-lifecycle.md) — Core Concepts: Lifecycle
- [13-audio.md](13-audio.md) — Core Concepts: Native Audio
- [14-plugins-slots.md](14-plugins-slots.md) — Plugins: Slots
- [15-plugins-core.md](15-plugins-core.md) — Plugins: Core
- [16-plugins-react.md](16-plugins-react.md) — Plugins: React
- [17-plugins-solid.md](17-plugins-solid.md) — Plugins: Solid
- [18-component-text.md](18-component-text.md) — Component: Text
- [19-component-box.md](19-component-box.md) — Component: Box
- [20-component-input.md](20-component-input.md) — Component: Input
- [21-component-textarea.md](21-component-textarea.md) — Component: Textarea
- [22-component-select.md](22-component-select.md) — Component: Select
- [23-component-tab-select.md](23-component-tab-select.md) — Component: TabSelect
- [24-component-scrollbox.md](24-component-scrollbox.md) — Component: ScrollBox
- [25-component-scrollbar.md](25-component-scrollbar.md) — Component: ScrollBar
- [26-component-slider.md](26-component-slider.md) — Component: Slider
- [27-component-code.md](27-component-code.md) — Component: Code
- [28-component-markdown.md](28-component-markdown.md) — Component: Markdown
- [29-component-line-number.md](29-component-line-number.md) — Component: Line Numbers
- [30-component-frame-buffer.md](30-component-frame-buffer.md) — Component: FrameBuffer
- [31-component-ascii-font.md](31-component-ascii-font.md) — Component: ASCIIFont
- [32-component-diff.md](32-component-diff.md) — Component: Diff
- [33-component-qr-code.md](33-component-qr-code.md) — Component: QR Code
- [34-bindings-solid.md](34-bindings-solid.md) — Bindings: Solid.js
- [35-bindings-react.md](35-bindings-react.md) — Bindings: React
- [36-keymap-overview.md](36-keymap-overview.md) — Keymap: Overview
- [37-keymap-hosts.md](37-keymap-hosts.md) — Keymap: Hosts
- [38-keymap-core.md](38-keymap-core.md) — Keymap: Core
- [39-keymap-react.md](39-keymap-react.md) — Keymap: React
- [40-keymap-solid.md](40-keymap-solid.md) — Keymap: Solid
- [41-keymap-addons.md](41-keymap-addons.md) — Keymap: Built-in Addons
- [42-keymap-custom-addons.md](42-keymap-custom-addons.md) — Keymap: Custom Addons
- [43-reference-env-vars.md](43-reference-env-vars.md) — Reference: Environment Variables
- [44-reference-tree-sitter.md](44-reference-tree-sitter.md) — Reference: Tree-sitter
- [45-reference-color-matrix.md](45-reference-color-matrix.md) — Reference: Color Matrix

## How these were created

- Docs pages: HTML → pandoc GFM (targeting the main `<article class="content">`)
- GitHub raw: direct `raw.githubusercontent.com` README.md (cleanest)
- GitHub rendered: best-effort from the webpage

All files include the original source URL at the bottom.

## Usage

```bash
# Search everything
grep -r "CliRenderer" --include="*.md" .

# Read a specific topic
cat 03-renderer.md | less
```

