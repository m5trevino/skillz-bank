# Example Organization Session

## User Request

> "Organize my ~/database-docs/keep folder"

## Step 1 — Ask for Target Directory

The agent already knows the directory from the user's message: `~/database-docs/keep`

## Step 2 — Ask for Project Folders

**Agent (via AskUserQuestion):**
> Enter your project folder names (comma separated):

**User:**
> liquid-semiotic, peacock, waldo, chora, core-standards, other

## Step 3 — Setup

The agent runs:
```bash
python scripts/smart_organizer.py setup ~/database-docs/keep \
  --projects "liquid-semiotic,peacock,waldo,chora,core-standards,other"
```

Folders created inside `~/database-docs/keep`.

## Step 4 — Analysis

The agent runs:
```bash
python scripts/smart_organizer.py analyze ~/database-docs/keep \
  --projects "liquid-semiotic,peacock,waldo,chora,core-standards,other"
```

Returns JSON like:
```json
[
  {
    "file": "/home/user/database-docs/keep/00-EXECUTIVE_OVERVIEW.md",
    "excerpt": "Project: liquid-semiotic ... invariant laws from agent frameworks...",
    "suggested_project": "liquid-semiotic",
    "confidence": 0.85,
    "keywords_matched": ["liquid-semiotic", "invariant", "agent"]
  },
  {
    "file": "/home/user/database-docs/keep/notes-2024-01.txt",
    "excerpt": "Random meeting notes about various topics...",
    "suggested_project": null,
    "confidence": 0.0,
    "keywords_matched": []
  }
]
```

## Step 5 — Process Files

**High confidence (≥ 0.80):**
- `00-EXECUTIVE_OVERVIEW.md` → auto-moved to `liquid-semiotic/`

**Low confidence (< 0.80):**

**Agent (via AskUserQuestion):**
> **File:** `notes-2024-01.txt`
> **Excerpt:** "Random meeting notes about various topics..."
>
> Where should this file go?

Options:
- liquid-semiotic
- peacock
- waldo
- chora
- core-standards
- other
- Skip
- New folder (type name)

**User selects:** `other`

The agent runs:
```bash
python scripts/smart_organizer.py move \
  /home/user/database-docs/keep/notes-2024-01.txt \
  /home/user/database-docs/keep \
  --project other

python scripts/smart_organizer.py learn \
  --file /home/user/database-docs/keep/notes-2024-01.txt \
  --project other
```

## Step 6 — Summary

**Agent reports:**
> ✅ Done!
> - 12 files processed
> - 8 auto-moved (high confidence)
> - 3 user-decided
> - 1 skipped
> - 0 errors
>
> Learned 3 new preferences. Next time I'll ask fewer questions.
