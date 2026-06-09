# DeepDive Prompt Templates

## Conditional Questions (Max 3)

### Q1: Mission Clarification
Ask when: Confidence < 80% on project purpose
What is the core mission of this project? (One sentence)
[Confidence: 72% - detected multiple entry points with conflicting purposes]

### Q2: User Types
Ask when: No auth patterns detected but web framework present
What are the user types/permission levels? (e.g., admin, user, guest)
[Detected: Express.js, JWT imports, but no role definitions found]

### Q3: Critical Business Logic
Ask when: High-risk files detected without clear purpose
What is the most critical business logic that must never break?
[Flagged: payment_gateway.js (94/100 risk score, no tests)]

## Chat Log Prompts

### Chat Detection
Found chat logs in provided directory. Process for conversation archaeology?
This will:
- Preserve verbatim chats in /docs/chatlogs/
- Extract decisions, TODOs, blockers, completions
- Correlate with git history
- Generate implementation state matrix

Proceed? (Y/n)

### Mermaid Rendering
{count} Mermaid diagrams generated in /docs/diagrams/.

Render to PNG using local mermaid-cli?
- Requires: npx mmdc (detected/undetected)
- Output: High-quality PNGs for sharing
- Alternative: Use https://mermaid.live

Render now? (Y/n)
