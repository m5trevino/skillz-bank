# Sources

Consolidation of 11 OpenTUI-related skills into a single reference-backed skill.

## Source Skills

| Skill | Score | Primary Contribution |
|-------|-------|---------------------|
| opentui-agent (393 lines) | 88/100 | Bootstrap, hooks table, 4 patterns, survival rules, renderables table, build commands |
| opentui-dev (999 lines) | 85/100 | All component prop tables, 6 additional patterns, code style, layout details, RGBA API, useTimeline example, usePaste/useFocus examples |
| opentui-auto-slicer (374 lines) | 82/100 | Auto-slice banners (excluded — generic workflow, not OpenTUI-specific) |
| opentui-8 (215 lines) | 78/100 | Decision tree branching format, REFERENCE.md convention, critical rules, troubleshooting index |
| opentui-debug (93 lines) | 75/100 | logDebug file-based debugging (excluded — same as jcha0713 with path bloat) |
| brianlovin-hn-cli-opentui (271 lines) | 70/100 | Constructs API, template literal styling, testing with createTestRenderer, imperative component examples |
| jcha0713-igl-opentui-debug (78 lines) | 72/100 | logDebug API, troubleshooting table, useEffect/useKeyboard debug patterns |
| opentui-5 (212 lines) | 75/100 | Decision trees (superseded by opentui-8) |
| opentui-skill (200 lines) | 76/100 | Decision trees (superseded by opentui-8) |
| opentuiii (216 lines) | 73/100 | Oldest iteration, path bloat (superseded by opentui-8) |
| cli-opentui (286 lines) | 68/100 | Duplicate of brianlovin with stale paths (excluded) |

## Decisions

1. **Execution shape**: reference-backed-expert. SKILL.md as router (~230 lines), references for deep content. Inline-guidance rejected — consolidated content would exceed 1000 lines.

2. **File split**: Lean — only patterns and testing extracted to references. Debugging kept inline (small enough). Code style kept inline (compact table).

3. **Decision tree format**: Adopted branching tree from opentui-8. Flat table from opentui-agent replaced.

4. **Three APIs**: Added Constructs API from brianlovin. opentui-agent and opentui-dev only documented Renderables and JSX.

5. **Testing**: Extracted from brianlovin. Was completely absent from opentui-agent.

6. **Debugging/logDebug**: Kept inline from jcha0713 (clean version). opentui-debug excluded (duplicate with path bloat).

7. **Auto-slice banners**: Excluded from consolidated skill. Feature is generic workflow, not OpenTUI-specific. Already exists in slice-n-dice skill.

8. **Patterns**: 4 original (agent) + 6 from dev + spinner + timeline = 13 patterns total in reference file.

9. **Duplicate Decision Tree removed**: opentui-agent had the "Which Package" table duplicated (lines 77-99 and 88-99). Consolidated to single decision tree.

10. **Stale paths removed**: All `~/.agents/skills/tui-ref/` references removed. Only live URLs retained.

## Gaps

- No Markdown component code example (referenced in decision trees but no source had code)
- No QR Code component code example (referenced in opentui-auto-slicer node_modules but no source had code)
- No Slider component code example (referenced in demos but no source had code)
- Solid reconciler examples limited — all sources defaulted to React
