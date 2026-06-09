---
name: standard
description: "Reads any chat (live session or file on disk) and turns it into clean, structured Journal Entries, Instruction Entries, and a verbatim section of the user's direct instructions. High-precision signal extractor built for the Peacock organization pipeline. Version: 1.4. MUST output ONLY the exact report inside one markdown code block. Saves via Loaded Toke cat block. Anti Vibe Coder compliant — zero deviation allowed."
---

# Standard v1.4 - Peacock Journal Architect
## Activation Protocol
The skill activates in **two modes**:
**Mode A — Live Chat:** Any trigger phrase ("process this chat", "make journal", "journal this", "make instruction", "create instruction entry", "upgrade this chat", "peacock architect", "architect this") → process entire current conversation history.
**Mode B — File Input:** File path detected in message → read file and process identically.

## Input Source Detection (Strict Priority)
1. Recognizable file path (`/`, `./`, `../`, `~/`, or ends with .txt/.md/.log/.json/.jsonl) → Mode B.
2. Trigger phrase only → Mode A.
3. Ambiguous → ask once: "Process current chat session or provide a file path?"

## Core Rules (Non-Negotiable - ZERO DEVIATION)
- Process the **entire** input source (full history OR full file contents).
- Be extremely precise, detailed, and objective.
- Respect Anti Vibe Coder principles — maximum signal, **zero bullshit, zero fluff, zero narrative**.
- Output **ONLY** the exact report format below. **NO additional commentary, NO intros, NO explanations, NO vibe, NO Loaded Toke inside the report**.
- The entire report MUST live inside a single ```markdown code block.
- Number entries sequentially. Titles pulled directly from context. Never invent or embellish.
- No high-signal content → output exactly: "NO HIGH-SIGNAL CONTENT DETECTED. Nothing to journal or instruct."

## Exact Output Format (MUST be inside ```markdown ... ``` - nothing else before or after)
```markdown
Peacock Journal Architect – Processing Report
Version: 1.4
Processed: [current ISO 8601 timestamp]
Source: [Live Chat Session / File: <path>]
Chat Length: X messages

DIRECT VERBATIM INSTRUCTIONS
VI-001: [Short Descriptive Title]
Original User Message (verbatim):[exact text the user typed]

JOURNAL ENTRIES
JE-001: [Title]
Category: [Decision / Progress / Experiment / Failure / Pivot / Architecture / Insight / Other]
Summary: [1-2 sentence summary]
Key Points:
- [bullet 1]
- [bullet 2]
Linked Messages: [message IDs or ranges, e.g. User:3-5]
Risks / Constraints: [bullet list or N/A]
Success Criteria: [bullet list or N/A]

INSTRUCTION ENTRIES
IE-001: [Title]
Target Agent: [Head Coach, Stat Analyst, Offensive Coordinator, Trainer, Scout, Architect, Operator, etc.]
Instruction Type: [Behavior / Architecture / Rule / Workflow / Standard / Protocol / Decision Framework / Other]
Full Clear Instruction Text: [full precise instruction — rephrase only for clarity while preserving original intent]
Must-Haves / Constraints: [bullet list]
Priority: [High / Medium / Low]
Linked Messages: [references]

SUMMARY
Total Verbatim Instructions: X
Total Journal Entries: X
Total Instruction Entries: X
Key Themes Identified: [short comma-separated list of core themes]
Ready to copy into WALDO.
```

## File Processing Protocol (Mode B)
1. Read the file using the ReadFile tool with the provided path.
2. Treat entire file as conversation transcript.
3. Infer: Chat Length, Source File, Subject slug from filename or topic.

## Persistence & Delivery Protocol (Loaded Toke)
After emitting the markdown code block:
1. Infer short kebab-case subject slug (2–4 words).
2. Save the **exact report content** (without extra text) to `./standard-skill/standard.created.from.chat.{subject-slug}.{MM-DD}.{YY}.md` using cat << 'EOF' block.
3. Echo full telemetry.
4. Present the termbin URL if possible.

## Processing Discipline
- Pre-fill every field faithfully from source only.
- Prioritize architecture points, explicit instructions, decisions, pivots, failures, completions.
- Ambiguous fields = note clearly, never guess.
- Include history up to and including the trigger message.
- Every token must increase clarity or actionability for the Peacock pipeline.

## Anti Vibe Coder Compliance
This skill exists for pure signal extraction only. The structure **is** the product. Zero deviation allowed under any circumstances.
