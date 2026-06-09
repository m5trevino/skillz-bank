#!/bin/bash
# Validation script for project-mapper skill
# Ensures directory structure and templates are in place.

echo "🔍 Validating project-mapper skill..."

SKILL_DIR=".gemini/skills/project-mapper"

if [ -d "$SKILL_DIR" ]; then
    echo "✅ Skill directory found."
else
    echo "❌ Skill directory missing!"
    exit 1
fi

REQUIRED_FILES=(
    "SKILL.md"
    "references/agents-template.md"
    "references/deep-dive-template.md"
    "prompts/exploration.md"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$SKILL_DIR/$file" ]; then
        echo "✅ $file found."
    else
        echo "❌ $file missing!"
        exit 1
    fi
done

echo "🚀 project-mapper skill is ready for action."
