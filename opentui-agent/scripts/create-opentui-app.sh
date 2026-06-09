#!/bin/bash
#
# create-opentui-app.sh
#
# Scaffold a minimal @opentui/react + TypeScript project.
# Usage: ./scripts/create-opentui-app.sh <project-name>
#
# Requirements: bash, mkdir, cat
# Runtime: bun (tested on MX Linux / Bun 1.3+)

set -euo pipefail

PROJECT_NAME="${1:-}"

# ── Validation ───────────────────────────────────────────────────────────────

if [ -z "$PROJECT_NAME" ]; then
  echo "Error: project name is required."
  echo "Usage: $0 <project-name>"
  exit 1
fi

# Reject names that look like paths or contain dangerous characters
if [[ "$PROJECT_NAME" == *"/"* || "$PROJECT_NAME" == *"\\"* ]]; then
  echo "Error: project name cannot contain path separators."
  exit 1
fi

if [ -e "$PROJECT_NAME" ]; then
  echo "Error: '$PROJECT_NAME' already exists in the current directory."
  exit 1
fi

# ── Create project skeleton ──────────────────────────────────────────────────

mkdir -p "$PROJECT_NAME"
cd "$PROJECT_NAME"

# package.json
cat > package.json << 'EOF'
{
  "name": "PROJECT_NAME_PLACEHOLDER",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "bun index.tsx"
  },
  "dependencies": {
    "@opentui/core": "^0.2.15",
    "@opentui/react": "^0.2.15",
    "react": "^19.2.0"
  },
  "devDependencies": {
    "@types/react": "^19.2.0",
    "typescript": "^5"
  }
}
EOF

# tsconfig.json
cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "lib": ["ESNext", "DOM"],
    "target": "ESNext",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "jsxImportSource": "@opentui/react",
    "strict": true,
    "skipLibCheck": true
  }
}
EOF

# index.tsx — minimal static layout starter
cat > index.tsx << 'EOF'
import { createCliRenderer } from "@opentui/core"
import { createRoot } from "@opentui/react"

function App() {
  return (
    <box style={{ flexDirection: "column", padding: 2, gap: 1 }}>
      <text fg="#FFFF00">Hello from OpenTUI!</text>

      <box border title="Panel" style={{ padding: 1 }}>
        <text>This is a bordered box.</text>
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

if (import.meta.main) {
  const renderer = await createCliRenderer()
  createRoot(renderer).render(<App />)
}
EOF

# README.md
cat > README.md << 'EOF'
# PROJECT_NAME_PLACEHOLDER

A minimal [OpenTUI](https://opentui.com) React terminal application.

## Install

```bash
bun install
```

## Run

```bash
bun run dev
```

## Exit

Press `Escape` or `Ctrl+C` to exit the application.
EOF

# Replace placeholders with the actual project name
sed -i "s/PROJECT_NAME_PLACEHOLDER/$PROJECT_NAME/g" package.json README.md

echo ""
echo "✅ Created '$PROJECT_NAME'"
echo ""
echo "Next steps:"
echo "  cd $PROJECT_NAME"
echo "  bun install"
echo "  bun run dev"
echo ""
