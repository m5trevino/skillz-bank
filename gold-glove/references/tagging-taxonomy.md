# Tagging Taxonomy

## Controlled Vocabularies (Full)

### domain:*
`ai`, `ml`, `nlp`, `vision`, `audio`, `backend`, `frontend`, `infra`, `data`, `security`, `ux`, `ui`, `mobile`, `desktop`, `cli`, `web`, `web3`, `hardware`, `bi`, `devops`, `observability`, `testing`, `api`, `database`, `networking`, `storage`, `compute`

### layer:*
`concept`, `design`, `architecture`, `implementation`, `testing`, `deployment`, `governance`, `research`, `documentation`, `refactoring`, `integration`, `migration`, `optimization`, `monitoring`

### mood:*
`experimental`, `proven`, `speculative`, `urgent`, `foundational`, `polish`, `debt`, `breakthrough`, `incremental`, `disruptive`, `maintenance`, `exploratory`, `risky`, `safe`, `hacky`, `elegant`

### scope:*
`single-feature`, `system-wide`, `org-level`, `personal`, `client-facing`, `internal`, `team`, `external-api`, `open-source`, `proprietary`

### lifecycle:*
`idea`, `draft`, `reviewed`, `accepted`, `rejected`, `parked`, `superseded`, `deprecated`, `active`, `completed`, `cancelled`

## Tag Assignment Examples

| Idea | Tags |
|------|------|
| "Distributed queue with priority levels" | `domain:backend`, `layer:architecture`, `mood:foundational`, `scope:system-wide`, `lifecycle:idea` |
| "Dark mode toggle" | `domain:frontend`, `layer:implementation`, `mood:polish`, `scope:single-feature`, `lifecycle:idea` |
| "AI agent memory using ChromaDB" | `domain:ai`, `domain:data`, `layer:architecture`, `mood:experimental`, `scope:system-wide`, `lifecycle:idea` |
| "Code review security checklist" | `domain:security`, `layer:governance`, `mood:proven`, `scope:team`, `lifecycle:draft` |

## Extension Protocol

1. New tags must follow the `category:value` format
2. New categories require Feature Bible update
3. New values within existing categories can be added ad-hoc
4. Log all new tags in `index.md` under `## New Tags`
5. Prefer existing tags; create new ones only when no match exists
