# Agent Guidelines for opentui

Default to using Bun instead of Node.js.

- Use `bun <file>` instead of `node <file>` or `ts-node <file>`
- Use `bun test` instead of `jest` or `vitest`
- Use `bun install` instead of `npm install` or `yarn install` or `pnpm install`
- Use `bun run <script>` instead of `npm run <script>` or `yarn run <script>` or `pnpm run <script>`
- Bun automatically loads .env, so don't use dotenv.

NOTE: When only changing typescript, you do NOT need to run the build script.
The build is only needed when changing native code.

## APIs

Don't use bun-specific APIs. Generated code should work in Bun, Node.js and Deno runtimes.

## Portable FFI Types

- In portable FFI code, stay within the `node:ffi`/`bun:ffi` type intersection.
- Avoid backend-specific ABI names in shared definitions: no `usize`, `napi_env`, or `napi_value`. Use explicit widths like `u32`/`u64`.
- Treat `i64`/`u64` as `bigint`, and native booleans as `0`/`1`.
- For pointer params, pass `ptr(view)` explicitly and keep shared `Pointer` values as `number | bigint`.
- For C strings, encode to bytes and pass pointers; do not assume raw JS strings or portable native string return normalization.
- Create callbacks through the loaded library/platform facade, not `new JSCallback(...)`, and only assume same-thread callback behavior.

## Testing

Use `bun test` to run tests from the packages directories for a specific package.

```ts#index.test.ts
import { test, expect } from "bun:test";

test("hello world", () => {
  expect(1).toBe(1);
});
```

For more information, read the Bun API docs in `node_modules/bun-types/docs/**.md`.

## Build/Test Commands

To build the project (before running typescript tests), run
`bun run build`
FROM THE REPO ROOT to make sure all packages are built correctly.

To run native tests for `packages/core`, run
`bun run test:native`
FROM THE `packages/core` DIRECTORY.

To filter native tests, use:
`bun run test:native -Dtest-filter="test name"`
FROM THE `packages/core` DIRECTORY.

## Typescript Code Style

- **Runtime**: Bun with TypeScript
- **Formatting**: oxfmt (semi: false, printWidth: 120)
- **Imports**: Use explicit imports, group by: built-ins, external deps, internal modules
- **Types**: Strict TypeScript, use interfaces for options/configs, explicit return types for public APIs
- **Naming**: camelCase for variables/functions, PascalCase for classes/interfaces, UPPER_CASE for constants
- **Error Handling**: Use proper Error objects, avoid silent failures
- **Async**: Prefer async/await over Promises, handle errors explicitly
- **Comments**: Minimal comments, NO JSDoc
- **File Structure**: Index files for clean exports, group related functionality
- **Testing**: Bun test framework, descriptive test names, use beforeEach/afterEach for setup

## Debugging

- NOTE this is a terminal UI lib and when running examples or apps built with it,
  you cannot currently see log output like console.log. Ask the user to run the example/app and provide the output.
- Reproduce the issue in a test case. Do NOT start fixing without a reproducible test case.
  Use debug logs to see what is actually happening. DO NOT GUESS.

---

## AI Coding Agent Quickstart

### Why OpenTUI for terminal apps

OpenTUI is a native terminal UI core written in Zig with TypeScript bindings. It provides a component-based architecture with flexible layout (Yoga-powered flexbox), built-in input handling, syntax highlighting, animation timelines, and optional React/Solid reconcilers. It targets correctness, stability, and high performance, making it suitable for complex interactive terminal applications that need more than simple CLI output.

### Decision tree: which package to use

| Situation | Use this |
|-----------|----------|
| You need maximum control, custom renderables, or minimal dependencies | `@opentui/core` imperative renderables |
| You want JSX, familiar React patterns, hooks, and component composition | `@opentui/react` |
| You prefer SolidJS signals, smaller bundle, or the Solid ecosystem | `@opentui/solid` |

Default to `@opentui/react` unless the user explicitly requests SolidJS or raw imperative APIs.

### Reference artifacts in this repo

- **`renderables-reference.md`** — Inventory of every core renderable with key props and minimal usage snippets. Use this when working with `@opentui/core` directly.
- **`react-quickstart.md`** — Exact boilerplate, imports, available hooks/components, and 3 app skeletons for `@opentui/react`.
- **`tui-survival-guide.md`** — Runtime pitfalls, common crash patterns, and a 60-second debugging checklist.

### Recommended first app structure (React)

```
project/
  tsconfig.json   # jsx: "react-jsx", jsxImportSource: "@opentui/react"
  index.tsx       # Entry point with import.meta.main guard
  App.tsx         # Root component
```

Entry pattern:

```typescript
import { createCliRenderer } from "@opentui/core"
import { createRoot } from "@opentui/react"
import { App } from "./App"

if (import.meta.main) {
  const renderer = await createCliRenderer()
  createRoot(renderer).render(<App />)
}
```

For imperative core, skip `createRoot` and instantiate renderables directly, adding them to `renderer.root`.

### Top 5 survival rules

1. **`console.log` is invisible while the TUI runs.** Call `renderer.console.show()` before logging, or set `OTUI_DUMP_CAPTURES=true`.
2. **`bun install` can fail behind SOCKS5 proxies.** Bun does not support `socks5://` or `socks5h://`. Unset `http_proxy`/`https_proxy`/`ALL_PROXY` before installing.
3. **Prebuilt native binaries may be stale.** If you see `Symbol ... not found in libopentui.so`, the optional platform package lags behind the source. Build from source with `bun run build` from the repo root.
4. **Always call `renderer.destroy()` on exit.** Without it, the terminal may remain blank, cursor hidden, or key echo disabled. Run `reset` in the shell if this happens.
5. **`exitOnCtrlC: true` by default.** The app exits immediately on Ctrl+C. Set `exitOnCtrlC: false` in `createCliRenderer()` if you need custom signal handling.
