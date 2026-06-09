# OpenTUI Runtime Pitfalls & Survival Guide

**Scope:** Every known failure mode when running OpenTUI apps in real environments.  
**Ground truth:** Observed from actual install, build, and execution attempts against the repo.

---

## Pitfall 1: `console.log` Output Is Invisible While the TUI Runs

**Symptom:** You add `console.log("debug")` and see nothing. The screen renders but logs vanish.

**Why:** OpenTUI captures stdout for rendering. Standard log output is suppressed while the renderer owns the terminal.

**Fix:**
```typescript
const renderer = useRenderer()
renderer.console.show() // Opens the console overlay
console.log("Now visible")
```

**Workaround:** Set `OTUI_DUMP_CAPTURES=true` before running to dump captured output on exit.

---

## Pitfall 2: `bun install` Fails Behind a SOCKS5 Proxy

**Symptom:** `bun install` throws `UnsupportedProxyProtocol` even though `curl` works.

**Why:** Bun does not support SOCKS5 proxies (`socks5h://` or `socks5://`).

**Fix:** Unset proxy variables before running Bun:
```bash
unset http_proxy https_proxy ALL_PROXY all_proxy
bun install
```

**Workaround:** Use an HTTP proxy instead of SOCKS5, or run `bun install` in a clean environment.

---

## Pitfall 3: Prebuilt Native Binaries Are Stale Relative to TypeScript Source

**Symptom:** `Failed to initialize OpenTUI render library: Symbol "getRenderStats" not found in libopentui.so`

**Why:** The optional `@opentui/core-linux-x64` package on npm may lag behind the `main` branch. The TypeScript FFI bindings reference symbols that don't exist in the published `.so`.

**Fix:** Build from source:
```bash
bun run build
# from repo root, or:
cd packages/core && bun run build
```

**Workaround:** Pin to a released tag where the prebuilt binary and TS source are in sync.

---

## Pitfall 4: Native Build Requires Zig + Network Access for Dependencies

**Symptom:** `bun run build` fails inside `zig build` with `unable to connect to server: NameServerFailure` while fetching `uucode`.

**Why:** Zig's package manager downloads dependencies from the internet on first build. Air-gapped or restricted environments block this.

**Fix:** Pre-populate Zig's global cache (`~/.cache/zig/`) with the required tarballs, or build on a machine with internet and copy the resulting `.so`/`.dylib` into the project.

**Workaround:** Use the optional platform package (`@opentui/core-linux-x64` etc.) and accept the risk of stale symbols (see Pitfall 3).

---

## Pitfall 5: Ctrl+C Exits the App by Default

**Symptom:** Pressing Ctrl+C kills the process immediately; your cleanup code never runs.

**Why:** `createCliRenderer()` defaults to `exitOnCtrlC: true`.

**Fix:** Disable it if you need custom signal handling:
```typescript
const renderer = await createCliRenderer({ exitOnCtrlC: false })
```

Then handle it yourself:
```typescript
useKeyboard((key) => {
  if (key.ctrl && key.name === "c") {
    renderer.destroy()
    process.exit(0)
  }
})
```

---

## Pitfall 6: Missing `renderer.destroy()` Leaves the Terminal Broken

**Symptom:** After the app exits, the terminal is blank, cursor is hidden, or key echo is off.

**Why:** OpenTUI switches to the alternate screen buffer and modifies terminal state. Without cleanup, the shell session is corrupted.

**Fix:** Always call `renderer.destroy()` on exit:
```typescript
useKeyboard((key) => {
  if (key.name === "escape") {
    renderer.destroy()
    process.exit(0)
  }
})
```

**Workaround:** Run `reset` in the shell to restore terminal state.

---

## Pitfall 7: `import.meta.main` Guard Is Required in Example Files

**Symptom:** Importing an example file as a module unexpectedly starts a renderer and takes over the terminal.

**Why:** Example files in the repo use `if (import.meta.main) { createCliRenderer() ... }` to avoid side effects on import. Without this guard, top-level `await createCliRenderer()` executes immediately.

**Fix:** Wrap the bootstrap code:
```typescript
if (import.meta.main) {
  const renderer = await createCliRenderer()
  createRoot(renderer).render(<App />)
}
```

---

## Pitfall 8: Workspace Packages Are Not Linked Without `bun install`

**Symptom:** `error: Cannot find package "@opentui/core" from ...` even though the package exists in `packages/core/`.

**Why:** Bun's workspace symlinks are only created during `bun install`. Cloning the repo is not enough.

**Fix:** Run `bun install` from the repo root after every clone or clean.

---

## Pitfall 9: `screenMode: "split-footer"` Behaves Differently from `"alternate-screen"`

**Symptom:** The TUI doesn't take over the full terminal, or scrollback interferes with rendering.

**Why:** `"alternate-screen"` (default) uses the terminal's alternate buffer. `"main-screen"` and `"split-footer"` render inline, which means shell output above the app remains visible and can cause visual corruption.

**Fix:** Use the default `screenMode: "alternate-screen"` unless you explicitly need inline rendering.

---

## Pitfall 10: Mouse Support Fails in Some Terminals

**Symptom:** Clicks don't register, or the terminal prints escape sequences like `^[[M...` on click.

**Why:** Mouse input requires a terminal that supports the X11 or SGR mouse protocol. Some terminals (e.g., stock Windows CMD, basic Linux console) do not.

**Fix:** Test in a modern terminal (iTerm2, Kitty, WezTerm, Windows Terminal, GNOME Terminal). Disable mouse if unsupported:
```typescript
const renderer = await createCliRenderer({ useMouse: false })
```

---

## Pitfall 11: Code Highlighting Fails Silently Without Tree-sitter

**Symptom:** `<code>` or `<line-number>` renders plain text even though `filetype` and `syntaxStyle` are set.

**Why:** Syntax highlighting depends on `web-tree-sitter` and compiled language grammars. If the grammar assets are missing or the filetype string doesn't match a known grammar, highlighting falls back to unstyled text without an error.

**Fix:** Ensure `web-tree-sitter` is installed and the `filetype` string matches one of the supported grammars. Check `@opentui/core/tree-sitter/update-assets` for grammar setup.

---

## Pitfall 12: Hot Reload / Watch Mode Is Not Built In

**Symptom:** You edit a `.tsx` file and nothing changes in the running TUI.

**Why:** OpenTUI has no built-in hot reload. Changes to TS source require restarting the process. Changes to native Zig code require a full rebuild.

**Fix:** Use `bun --watch` or an external file watcher to restart the process:
```bash
bun --watch run app.tsx
```

**Workaround:** For rapid UI iteration, use `testRender` from `@opentui/solid` or write snapshot tests instead of running the full TUI.

---

## First 60 Seconds of Debugging a Broken TUI

1. **Can you install?** Run `bun install` from repo root. If it fails with proxy errors, unset `http_proxy`/`https_proxy`.
2. **Can you build?** Run `bun run build` from repo root. If Zig fails with network errors, you need internet or a prebuilt binary.
3. **Does the binary load?** If you see `Symbol ... not found`, the prebuilt `.so` is stale — build from source.
4. **Does the app start?** If it hangs or shows a blank screen, check that `renderer.destroy()` runs on exit and that you're using `exitOnCtrlC: false` if you handle signals yourself.
5. **Are logs missing?** Call `renderer.console.show()` before any `console.log`.
6. **Is the terminal broken after exit?** Run `reset` in your shell.
7. **Are clicks not working?** Try a different terminal emulator, or disable mouse with `useMouse: false`.
