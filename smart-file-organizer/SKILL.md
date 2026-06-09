---
name: Smart File Organizer
description: This skill should be used when the user asks to "organize files", "sort files into folders", "clean up a directory", "organize my downloads", "file organizer", or mentions moving files into project folders. Helps organize any directory by creating project folders, analyzing files, and learning user preferences over time.
version: 0.1.0
---

# Smart File Organizer

Organize any directory by sorting files into user-defined project folders. The system learns from each choice and asks fewer questions over time.

## How It Works

1. Ask the user which directory to organize and what project folders to create.
2. Scan all files in the target directory.
3. For each file, check learned preferences from previous sessions.
4. If confident, move the file automatically.
5. If unsure, present a file excerpt and ask the user where it belongs.
6. Record the user's choice to improve future confidence.

## Workflow

### Step 1: Gather Input

Use the `AskUserQuestion` tool to ask:

1. **Target directory**: "Which directory would you like to organize?"
2. **Project folders**: "Enter your project folder names (comma separated):"

Example answer: `liquid-semiotic, peacock, waldo, chora, core-standards, other`

### Step 2: Prepare Environment

Run the setup script to create project folders inside the target directory:

```bash
python scripts/smart_organizer.py setup <target_dir> --projects <comma-separated-list>
```

### Step 3: Analyze Files

Run the analysis script to get a JSON report for every file:

```bash
python scripts/smart_organizer.py analyze <target_dir> --projects <comma-separated-list>
```

The script returns a JSON array where each entry contains:
- `file`: file path
- `excerpt`: first ~300 characters of content (for text files) or metadata
- `suggested_project`: best guess based on learned patterns, or `null`
- `confidence`: float from 0.0 to 1.0
- `keywords_matched`: list of matched keywords per project

### Step 4: Process Files

Iterate through the analysis results. For each file:

**If confidence >= 0.8:**
- Move the file automatically using:
```bash
python scripts/smart_organizer.py move <source_path> <dest_dir> --project <project_name>
```

**If confidence < 0.8:**
- Present the file name and excerpt to the user.
- Use `AskUserQuestion` to ask: "Where should this file go?"
- Include options:
  - Each project folder as a radio option
  - "Skip" option
  - "New folder" option (free text input)
- After receiving the answer, execute the move and record the choice:
```bash
python scripts/smart_organizer.py learn --file <path> --project <chosen_project>
```

### Step 5: Summary Report

After all files are processed, report:
- Total files processed
- Number auto-moved (high confidence)
- Number user-decided (low confidence)
- Number skipped
- Any errors encountered

## Learning System

The script maintains a JSON database at `~/.smart_file_organizer/memory.json`.

Each learned entry stores:
- `filename_pattern`: regex or substring match for filenames
- `content_keywords`: keywords found in file content that correlate with a project
- `project`: the chosen project folder
- `frequency`: how many times this pattern has been confirmed (strengthens confidence)

Confidence calculation:
- Exact filename match from history: 0.95
- Strong keyword overlap (>3 keywords): 0.85
- Moderate keyword overlap (1-3 keywords): 0.6
- No match: 0.0

## Additional Resources

### Reference Files

- **`references/architecture.md`** — Detailed technical documentation for the learning algorithm, confidence scoring, and memory format.
- **`references/troubleshooting.md`** — Common issues and edge cases (binary files, large directories, permission errors).

### Examples

- **`examples/example-session.md`** — Complete example of an organization session.

### Scripts

- **`scripts/smart_organizer.py`** — Main utility script. Supports `setup`, `analyze`, `move`, and `learn` subcommands.
