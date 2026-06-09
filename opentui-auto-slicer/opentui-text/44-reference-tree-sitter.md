# Tree-sitter

OpenTUI integrates Tree-sitter for fast, accurate syntax highlighting. You can register parsers globally or per client.

## Add parsers globally

Use `addDefaultParsers()` before creating clients:

``` astro-code
import { addDefaultParsers, getTreeSitterClient } from "@opentui/core"

addDefaultParsers([
  {
    filetype: "python",
    wasm: "https://github.com/tree-sitter/tree-sitter-python/releases/download/v0.23.6/tree-sitter-python.wasm",
    queries: {
      highlights: ["https://raw.githubusercontent.com/tree-sitter/tree-sitter-python/master/queries/highlights.scm"],
    },
  },
])

const client = getTreeSitterClient()
await client.initialize()
```

## Add parsers per client

``` astro-code
import { TreeSitterClient } from "@opentui/core"

const client = new TreeSitterClient({ dataPath: "./cache" })
await client.initialize()

client.addFiletypeParser({
  filetype: "rust",
  wasm: "https://github.com/tree-sitter/tree-sitter-rust/releases/download/v0.23.2/tree-sitter-rust.wasm",
  queries: {
    highlights: ["https://raw.githubusercontent.com/tree-sitter/tree-sitter-rust/master/queries/highlights.scm"],
  },
})
```

## Parser configuration

``` astro-code
interface FiletypeParserOptions {
  filetype: string
  aliases?: string[]
  wasm: string
  queries: {
    highlights: string[]
    injections?: string[]
  }
  injectionMapping?: {
    nodeTypes?: Record<string, string>
    infoStringMap?: Record<string, string>
  }
}
```

`aliases` maps additional filetype ids to the same parser assets.

## Language injections

Use `queries.injections` to highlight embedded languages.

-   `injectionMapping.nodeTypes` maps injected node types to filetype ids.
-   `injectionMapping.infoStringMap` maps code fence language labels to filetype ids.

``` astro-code
client.addFiletypeParser({
  filetype: "markdown",
  wasm: "https://github.com/tree-sitter-grammars/tree-sitter-markdown/releases/download/v0.5.1/tree-sitter-markdown.wasm",
  queries: {
    highlights: ["./assets/markdown/highlights.scm"],
    injections: [
      "https://raw.githubusercontent.com/nvim-treesitter/nvim-treesitter/refs/heads/master/queries/markdown/injections.scm",
    ],
  },
  injectionMapping: {
    nodeTypes: {
      inline: "markdown_inline",
      pipe_table_cell: "markdown_inline",
    },
    infoStringMap: {
      js: "javascript",
      jsx: "javascriptreact",
      ts: "typescript",
      tsx: "typescriptreact",
    },
  },
})
```

If `infoStringMap` has no match, the fence language label is used as the filetype id.

## Use local files

``` astro-code
import pythonWasm from "./parsers/tree-sitter-python.wasm" with { type: "file" }
import pythonHighlights from "./queries/python/highlights.scm" with { type: "file" }

addDefaultParsers([
  {
    filetype: "python",
    wasm: pythonWasm,
    queries: {
      highlights: [pythonHighlights],
    },
  },
])
```

## Automated asset management

Use the `updateAssets` utility to download parsers and generate imports.

### CLI usage

``` astro-code
{
  "scripts": {
    "prebuild": "bun node_modules/@opentui/core/lib/tree-sitter/update-assets.js --config ./parsers-config.json --assets ./src/parsers --output ./src/parsers.ts"
  }
}
```

### Programmatic usage

``` astro-code
import { updateAssets } from "@opentui/core/tree-sitter/update-assets"

await updateAssets({
  configPath: "./parsers-config.json",
  assetsDir: "./src/parsers",
  outputPath: "./src/parsers.ts",
})
```

## Using with CodeRenderable

``` astro-code
import { CodeRenderable, RGBA, SyntaxStyle, getTreeSitterClient } from "@opentui/core"

const client = getTreeSitterClient()
await client.initialize()

const syntaxStyle = SyntaxStyle.fromStyles({
  default: { fg: RGBA.fromHex("#E6EDF3") },
})

const code = new CodeRenderable(renderer, {
  id: "code",
  content: "const x = 1",
  filetype: "typescript",
  syntaxStyle,
  treeSitterClient: client,
})
```

## Caching

Parser and query files are cached in the client `dataPath`. Set a custom cache directory:

``` astro-code
const client = new TreeSitterClient({
  dataPath: "./my-cache",
})
```

## File type resolution

``` astro-code
import { pathToFiletype, extToFiletype, infoStringToFiletype } from "@opentui/core"

const ft1 = pathToFiletype("src/main.rs")
const ft2 = extToFiletype("ts")
const ft3 = infoStringToFiletype("TSX title=Button.tsx")
```

`infoStringToFiletype()` is used for fenced markdown code blocks.

You can extend or override mappings at runtime:

``` astro-code
import { extensionToFiletype, basenameToFiletype } from "@opentui/core"

extensionToFiletype.set("templ", "html")
basenameToFiletype.set("mytoolrc", "yaml")
```


---

_Source: https://opentui.com/docs/reference/tree-sitter
_Downloaded: 2026-05-21 19:05:16 UTC_
