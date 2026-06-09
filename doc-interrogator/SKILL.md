---
name: doc-interrogator
description: Drop docs or give a URL. AI sections them, classifies by tier (quickstart/standard/full), then interrogates you about every config decision. Thick sections processed whole for review. Thin sections chomped one question at a time. Produces ready-to-use config output. Session memory resumes where you left off.
version: 1.0.0
---

# DOC-INTERROGATOR v1.0
# =====================
# INPUT:    User drops docs OR Agent fetches from URL
# SLICE:    Agent reads full doc, sections it, classifies each slice by tier
# THICK:    >50 lines OR >10 decision points → Agent processes whole slice, user reviews
# THIN:     <50 lines AND <10 decision points → One question at a time
# CHOMP:    Section by section, dependency tracking, one question at a time (thin only)
# OUTPUT:   Auto-detected format — .env, config file, Python code, Docker, shell script, or .md instructions
# MEMORY:   Saves after every answer. Resume anytime.

# INPUT METHODS
# =============
# 1. USER DROPS DOCS
#    Paste, upload, or drop docs into chat.
#    Agent receives raw text → SLICE phase.
#
# 2. AGENT FETCHES FROM URL
#    User says: "interrogate https://docs.example.com/setup"
#    Or: "fetch docs for graphiti"
#    Agent fetches, receives raw text → SLICE phase.
#    If fetch fails: tell user, fall back to method 1.
#
# 3. RESUME SESSION
#    User says: "resume graphiti" or "continue mobsf"
#    Agent loads session from ~/.kimi/skills/doc-interrogator/sessions/
#    Picks up where left off.

# SLICE PHASE
# ===========
# Agent reads ENTIRE document. Full pass. No shortcuts.
# Identifies sections. Tags each with tier.
#
# SECTION TYPES (scan for all present):
#   PREREQUISITES     — hard reqs, versions, deps
#   INSTALLATION      — package managers, docker, build
#   CONFIGURATION     — env vars, config files, flags
#   AUTHENTICATION    — keys, tokens, auth modes
#   DATABASE/BACKEND  — backend choices, connection details
#   LLM/AI PROVIDER   — model choices, API config
#   NETWORK           — ports, hosts, proxies
#   ADVANCED/OPTIONAL — tuning, telemetry, custom types
#   EXAMPLES          — quick start, code samples
#   TROUBLESHOOTING   — known errors, fixes
#
# TIER CLASSIFICATION (per slice):
#   QUICKSTART — "Required", "Prerequisites", "Getting Started", "Basic", install only
#   STANDARD   — "Recommended", "Configuration", "Setup", "Common", auth, basic backend
#   FULL       — "Optional", "Advanced", "Tuning", "Performance", "Custom", telemetry
#
# Heuristics:
#   "You must..." / "Required..." → QUICKSTART
#   "We recommend..." / "By default..." → STANDARD
#   "Optionally..." / "For advanced users..." → FULL
#   Code with required vars → QUICKSTART
#   Code with optional vars → STANDARD or FULL
#   Tables with defaults → STANDARD or FULL
#
# After slicing, present:
#   "Found {N} sections. Classified:
#    QUICKSTART ({X} sections, ~{Y} questions)
#    STANDARD (+{X} sections, ~{Y} questions total)
#    FULL (+{X} sections, ~{Y} questions total)
#    Pick tier: quickstart / standard / full"

# THICK VS THIN
# =============
# After user picks tier, evaluate each chosen section:
#
# THICK: >50 lines OR >10 decision points
#   Agent processes ENTIRE section at once.
#   Extracts ALL config decisions.
#   Presents as reviewable block:
#     "=== Section {N}: {Name} [THICK] ===
#      This section has {M} config decisions. Processing whole...
#
#      Extracted decisions:
#      1. {decision}: {options} → {agent suggestion based on docs}
#      2. {decision}: {options} → {agent suggestion}
#      ...
#
#      Review these choices. Say 'approve' to accept all,
#      or 'change {number}' to edit a specific decision."
#
# THIN: <50 lines AND <10 decision points
#   Agent chomps one question at a time.
#   See CHOMP PHASE below.

# CHOMP PHASE (thin sections only)
# =================================
# ONE SECTION AT A TIME. ONE QUESTION AT A TIME.
#
# Per section:
#   1. STATE: "=== Section {N}: {Name} [{tier}] ==="
#   2. SUMMARIZE: "This section covers: {brief}"
#   3. COUNT: "{M} questions"
#   4. ASK ONE:
#      "[{section}] {question}
#       Context: {what this controls}
#       Default: {documented default or 'none'}
#       Options: {discrete options or 'free text'}
#       Your answer:"
#   5. WAIT FOR ANSWER
#   6. RECORD: save to session
#   7. CHECK DEPENDENCIES
#   8. NEXT
#
# VALID ANSWERS:
#   specific value → use exactly
#   "default"      → use documented default
#   "skip"         → mark skipped
#   "explain more" → deeper context, re-ask
#   "back"         → previous question
#   "quit"         → save, exit
#
# DEPENDENCY TRACKING:
#   After each answer, gate downstream questions.
#   "Since you picked {X}, skipping {Y}"
#   Examples:
#     - "Neo4j" → skip FalkorDB/Kuzu/Neptune
#     - "Docker" → ask --add-host, skip host-install
#     - "disabled auth" → skip API key questions
#     - "no dynamic analysis" → skip ADB/emulator

# OUTPUT ADAPTER
# ==============
# Detect config method from docs:
#
# SETTINGS/CONFIG FILE
#   Signals: "Edit config.py", "settings.json", ".ini", ".toml", ".yaml"
#   Output: Ready-to-edit config file with user choices filled in
#
# ENVIRONMENT VARIABLES
#   Signals: export VAR=, .env, "Set environment variable", os.environ
#   Output: .env file or shell export block
#
# COMMAND-LINE FLAGS
#   Signals: --flag, -f, CLI examples
#   Output: Shell script or command template
#
# INTERACTIVE/GUI
#   Signals: "Open web UI", "Click Settings", "Admin panel"
#   Output: .md or .txt step-by-step instructions
#
# CODE/API
#   Signals: Python class instantiation, constructor args, client = Class(...)
#   Output: Python code block
#
# DOCKER/CONTAINER
#   Signals: docker run -e, docker-compose.yml, ENV in Dockerfile
#   Output: Docker command or compose snippet
#
# MIXED
#   Signals: Multiple methods shown
#   Output: Ask user which method, or generate all with labels
#
# Before generating, ask ONE question if mixed:
#   "Docs show configuration via:
#    [1] Environment variables
#    [2] Settings file (config.json)
#    [3] Python code
#    Which format do you want? (number)"
#
# Or if clear: "Generating .env file based on docs..."
#
# OUTPUT CONTENT:
#   Header: tool name, date, tier, sections covered, config method
#   Body: all answers, defaults used, skips noted, dependency resolutions
#   Footer: prerequisites checklist, next steps, verify commands

# MEMORY / RESUME
# ===============
# Save after EVERY answer. Session file:
#   ~/.kimi/skills/doc-interrogator/sessions/{tool-name}.json
#
# Contains:
#   tool_name, input_method, source_url,
#   tier, sections_chosen, thick_sections[], thin_sections[],
#   current_section, current_question,
#   answers{}, skipped{}, defaults_used{}, dependencies{},
#   output_format_detected, timestamp
#
# On resume: load, say where left off, continue.

# BEHAVIOR RULES
# ==============
# DO:
#   - Read full docs before slicing
#   - Classify slices by tier from content
#   - Thick sections: process whole, present for review
#   - Thin sections: one question at a time
#   - Reference specific doc passages
#   - Track dependencies
#   - Save after every answer
#   - Let user control pace
#
# DO NOT:
#   - Validate installs
#   - Check ports
#   - Verify API keys
#   - Suggest alternatives not in docs
#   - Add "best practices"
#   - Run commands
#   - Make assumptions beyond docs
#   - Rush or batch questions (thin sections)
#   - Skip review on thick sections
#
# The job: GET DOCS → SLICE → TIER → THICK/THIN → CHOMP/REVIEW → OUTPUT. Period.
