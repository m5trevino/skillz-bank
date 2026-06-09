# Retrieval Patterns

## Advanced Search

### Composite Queries
Combine multiple filters in natural language:
- "Show me high-confidence AI ideas from last month" → `domain:ai AND confidence:high AND date:>30days`
- "Any experimental frontend features?" → `domain:frontend AND mood:experimental AND layer:implementation`
- "What did I archive?" → `status:archived`

### Fuzzy Matching
- Slug search is case-insensitive
- Partial matches rank lower than exact matches
- Typo tolerance: if no exact match, try Levenshtein distance <= 2 on slugs

### Cross-Linking Surfaces
When displaying a single idea, automatically query for:
- Ideas that link TO this idea (backlinks)
- Ideas this idea links FROM (forward links)
- Ideas with overlapping tags (related)
- Ideas captured within 24 hours (temporal cluster)

## Ranking Heuristics

When multiple results match, rank by:
1. Exact slug match (highest)
2. Tag match count (more matching tags = higher)
3. Recency (newer = higher)
4. Confidence (higher = higher)
5. Urgency (Now > Soon > Later > Someday)
