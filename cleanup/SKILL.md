---
name: cleanup
description: >-
  Deep forensic mapping of a directory full of files, docs, code, and databases.
  Produces a comprehensive directory map with architecture brief, pipeline flow,
  duplicate detection, gaps, and decision recommendations. Use when the user
  says "map this directory", "organize these files", "what is in this folder",
  "clean up this dir", or needs to understand a complex project archive.
---

# Cleanup — Directory Forensic Mapper

Maps any directory into a structured intelligence report. Treats the directory
as a **living system**: files are not just listed, they are categorized by
function, traced through pipeline relationships, and evaluated for gaps.

## Trigger phrases

- "map this directory" / "organize these files"
- "what is in this folder" / "clean up this dir"
- "review the whole dir" / "directory structure"
- "make sense of this archive" / "document this project"

## 4-Phase Workflow

### Phase 1: Reconnaissance

1. `ls -la` or `tree` to get directory layout
2. Count files by extension (`find . -type f | sed 's/.*\.//' | sort | uniq -c | sort -rn`)
3. Identify **manifest files** — anything named `START_HERE`, `README`, `OVERVIEW`, `MANIFEST`, `BLUEPRINT`, `SPEC`, `ARCHITECTURE`, or containing pipeline/layer/system terminology
4. Flag **database files** (`.db`, `.sqlite`, `.sqlite3`) for schema extraction
5. Note **config files** (`.toml`, `.json`, `.yaml`) that define bindings or wiring

### Phase 2: Deep Read of Critical Files

Read in this priority order:

1. **Session resumption files** (`START_HERE.md`, `README.md`, `00-*`)
2. **Architecture overviews** (`*-OVERVIEW*`, `*-BLUEPRINT*`, `*-ARCHITECTURE*`)
3. **Pipeline manifests** (`*pipeline*manifest*`, `*-pipeline-*.md`)
4. **Spec files** (`*-spec.md`, `*_SPEC.md`)
5. **Writeups** (`*_WRITEUP*`, `*_MASTER_*`)
6. **Config/schemas** (`BINDING_SPEC*`, `WIRING*`, `*.json` manifests)

For each critical file, extract:
- **Purpose** — one-line summary
- **Pipeline position** — where does this fit in the data flow?
- **Inputs** — what does it read/consume?
- **Outputs** — what does it produce?
- **Relationships** — what other files/systems does it reference?

### Phase 3: Database & Code Inspection

If a database is found:
1. `sqlite3 <file> ".schema"` to extract table definitions
2. `sqlite3 <file> ".tables"` to list tables
3. For each table, document: purpose, key columns, foreign key relationships
4. Identify which tables are **operational** (logs, jobs) vs **reference** (config, registry)

If Python/TypeScript/Shell scripts are found:
1. Read entry-point scripts (top-level `.py`, `main*`, `cli*`)
2. Extract function names that suggest pipeline stages
3. Note any script that writes to ChromaDB, databases, or external APIs

### Phase 4: Synthesis Report

Write a single comprehensive Markdown report with these sections:

#### 1. TL;DR
One paragraph: what this directory is, its primary function, and the pipeline flow.

#### 2. Directory Topology (Layer Map)
Group directories into functional layers. Assign each layer a name and purpose.
Use a tree or table format.

#### 3. Layer-by-Layer Breakdown
For each layer, list key files with:
- File name
- One-line purpose
- Pipeline position (if applicable)

#### 4. The Pipeline Flow (End-to-End)
Describe the data flow: what consumes what, what produces what, and in what order.
Use Mermaid `flowchart` if appropriate.

#### 5. Database Schema (if applicable)
Table-by-table breakdown with purpose and key columns.

#### 6. Critical Distinctions
Clarify any ambiguous or easily confused components (e.g., "X is the sensor, Y is the dashboard").
Use a comparison table.

#### 7. Cold Start Read Order
If a fresh agent needs to understand this system, what 5-8 files should they read first?

#### 8. Duplicate & Variant Analysis
Identify:
- Draft iterations (`(1)`, `(2)`, `(3)` suffixes)
- Cross-cutting concerns duplicated across domains
- Files with `_refined`, `_v2`, `_v3` variants

#### 9. Gaps & Anomalies Detected
List 5-10 specific gaps, placeholders, or inconsistencies found.

#### 10. Decision Points
Present 3-5 choices the user faces, with Option A, Option B, and a recommendation.

#### 11. Adjacent Opportunities
Suggest 3-5 next actions or automations that would improve the system.

## Rules

- **Always write the report to a file**, do not just display it in chat.
- **File naming convention**: `<directory-name>-directory-map.md`
- **Save location**: current working directory or user's specified path
- **Be explicit about pipeline relationships** — do not just list files, explain how they connect
- **Flag no-op/placeholder code** explicitly (e.g., "Remote sync is a no-op")
- **Distinguish human-facing vs machine-facing components** clearly
- **Identify the single source of truth** for each major concept
- **If >50 files**, use a summarization approach: aggregate by directory, then deep-dive only critical files
- **If databases found**, always extract schema before synthesis

## Skill Stack

This skill composes with:
- `deep-research` — for synthesizing findings into coherent narrative
- `project-analyzer` — for tech stack and feature identification
- `devrything` — for forensic pipeline architecture mapping
- `code-researcher` — for tracing data flows through scripts
- `data-analyzer` — for database schema interpretation and statistics
- `knowledge` / `knowledge-synthesizer` — for cross-project pattern recognition

## Output Example

See [reference.md](reference.md) for a full example of the synthesis report format.
