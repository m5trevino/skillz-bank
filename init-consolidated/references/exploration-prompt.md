# Exploration Prompt

You are a software engineering expert with many years of programming experience. Please explore the current project directory to understand the project's architecture and main details.

## Task Requirements

1. **Analyze project structure**
   - Identify key configuration files (pyproject.toml, package.json, Cargo.toml, etc.)
   - Map directory structure and main modules

2. **Understand tech stack**
   - Primary languages and frameworks
   - Build tools and package managers
   - Runtime architecture

3. **Identify conventions**
   - Code style guidelines (linters, formatters config)
   - Testing strategies
   - Git workflow
   - Deployment processes

4. **Document findings**
   - Write comprehensive summary to `AGENTS.md`
   - Reference existing AGENTS.md content if present
   - Use the project's natural language (from comments/docs)

## AGENTS.md Structure

Use this structure for the output file:

```markdown
# AGENTS.md

> **Notice for AI Agents**: This file provides a high-level overview of the project architecture, development conventions, and operational instructions. Read this before attempting any significant changes.

## 🚀 Project Overview
[Brief summary of purpose and functionality]

## 🛠️ Technology Stack
- **Primary Language**: [e.g., Python, TypeScript]
- **Framework**: [e.g., FastAPI, React]
- **Build Tooling**: [e.g., npm, poetry]
- **Database**: [if applicable]

## 🏗️ Architecture & Code Organization
[High-level folder structure and module responsibilities]

## 💻 Development Conventions
- **Code Style**: [linter/formatter configs]
- **Naming Conventions**: [patterns used]
- **Git Workflow**: [branching, commits]

## 🧪 Testing & Validation
```bash
# Example commands
npm test
pytest
```

## 🔐 Security Considerations
[Key protocols, sensitive areas]

## 📦 Deployment & CI/CD
[Deployment process summary]
```

## Guidelines

- Be specific - use actual file names, commands, and paths found in the project
- Do not make assumptions - document what you see
- Ensure accuracy - verify information by reading files
- Use natural language from the project's own documentation
- If AGENTS.md exists, read it first and update/improve it
