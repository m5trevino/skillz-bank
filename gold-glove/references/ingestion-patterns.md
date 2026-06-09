# Ingestion Patterns

## Handling Ambiguous Input

When the user's idea lacks clear boundaries:
1. Look for natural linguistic separators: "also", "another thing", "separately", "by the way"
2. Look for structural separators: headers, horizontal rules, numbered lists
3. If no separators exist, treat the entire input as a single idea
4. If the input covers multiple unrelated domains (e.g., backend + frontend + marketing), split at domain boundaries

## Handling Fragmented Input

When the user provides a `Half-Thought`:
- Do NOT pressure the user to complete it
- Capture exactly as provided
- Set `Confidence: Low`
- Add an Open Question: "What mechanism connects these fragments?"
- Tag with `mood:exploratory`

## Handling Multi-Idea Messages

When one message contains 3+ distinct ideas:
1. List detected ideas with proposed slugs
2. Ask: "Store as N separate ideas, or merge into one?"
3. If user does not respond within context window, default to separate storage

## File Ingestion Edge Cases

| Format | Handling |
|--------|----------|
| Plain text (.txt) | Treat as single payload or split by double newlines |
| Markdown (.md) | Split by H2/H3 headers; preserve header as idea title hint |
| JSONL (.jsonl) | Parse each line as message object; extract `content` field |
| Log file (.log) | Extract lines containing trigger keywords; ignore timestamps |
