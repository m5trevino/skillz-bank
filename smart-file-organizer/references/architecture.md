# Smart File Organizer — Architecture & Learning System

## Memory Format

The learning database lives at `~/.smart_file_organizer/memory.json`.

```json
{
  "entries": [
    {
      "filename_patterns": ["00-EXECUTIVE_OVERVIEW.md"],
      "content_keywords": ["liquid-semiotic", "invariant", "laws", "agent"],
      "project": "liquid-semiotic",
      "frequency": 3
    }
  ]
}
```

- `filename_patterns`: Substrings or regexes that match filenames.
- `content_keywords`: Keywords extracted from file names and text excerpts.
- `project`: The folder the user chose.
- `frequency`: How many times this exact mapping has been confirmed.

## Confidence Scoring

| Signal | Base Score | Cap |
|--------|-----------|-----|
| Filename pattern match | +0.50 | — |
| Keyword overlap (each) | +0.15 | +0.50 |
| Frequency bonus | ×(1 + 0.1×(freq−1)) | 1.0 |
| Project-name keyword match | +0.20 each | 0.60 |

Thresholds:
- `≥ 0.80` → Auto-move without asking.
- `< 0.80` → Ask the user.

## Keyword Extraction

The script tokenizes file names and text excerpts, lowercases everything, drops tokens shorter than 3 characters, and filters a small stop-word list. The remaining tokens become the keyword set for matching.

## Binary File Handling

Binary files are detected by checking for null bytes in the first 1 KB. For binaries, the excerpt shows file size instead of content, and keyword extraction falls back to the filename only.

## Name Collision Resolution

When moving a file, if the destination already exists, the script appends `_1`, `_2`, etc., before the extension.

## Scope

Analysis is **top-level only** (non-recursive). The skill organizes the immediate children of the target directory. Nested subdirectories are ignored during analysis.
