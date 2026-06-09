# Herbert Service Connection Registry

## Description

Manage third-party service connections (Stripe, Gmail, Slack, GitHub, etc.) for Herbert/OpenClaw. Provides a unified `claw services` experience: list available services, check connection status, run interactive setup wizards, and sync credentials to `openclaw.json` automatically.

## When to use

- The user wants to connect a third-party service (API, OAuth, MCP)
- A skill requires a service that isn't connected yet
- The user asks about service status, credentials, or setup
- Before running a skill that depends on external APIs (Stripe, GitHub, etc.)
- The user says "set up X", "connect to X", "configure X", "add X API key"

## Commands

```bash
# List all known services with connection status
herbert-services list

# Show only connected services (with credential validation)
herbert-services status

# Interactive setup guide for a service
herbert-services connect <service-id>

# Remove a service connection
herbert-services disconnect <service-id>

# Sync connected services to openclaw.json (MCP servers + env vars)
herbert-services sync

# Show which services a skill needs
herbert-services skill <skill-name>

# Check if all services required by a skill are connected
herbert-services check <skill-name>

# Machine-readable JSON output of all status
herbert-services json
```

## Available Services

| ID | Name | Category | Key Credentials |
|---|---|---|---|
| `stripe` | Stripe | payments | `STRIPE_SECRET_KEY` |
| `github` | GitHub | dev | `GITHUB_TOKEN` |
| `gmail` | Gmail | communication | `GMAIL_ACCESS_TOKEN` |
| `slack` | Slack | communication | `SLACK_BOT_TOKEN` |
| `openai` | OpenAI | ai | `OPENAI_API_KEY` |
| `anthropic` | Anthropic | ai | `ANTHROPIC_API_KEY` |
| `notion` | Notion | productivity | `NOTION_API_KEY` |
| `hubspot` | HubSpot | crm | `HUBSPOT_API_KEY` |
| `resend` | Resend | communication | `RESEND_API_KEY` |
| `twilio` | Twilio | communication | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` |
| `supabase` | Supabase | database | `SUPABASE_URL`, `SUPABASE_ANON_KEY` |
| `neon` | Neon | database | `NEON_API_KEY`, `DATABASE_URL` |
| `vercel` | Vercel | hosting | `VERCEL_TOKEN` |
| `netlify` | Netlify | hosting | `NETLIFY_AUTH_TOKEN` |
| `cloudflare` | Cloudflare | hosting | `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` |
| `composio` | Composio | platform | `COMPOSIO_API_KEY` |

## Workflow

### 1. Check before using a skill

Always verify service dependencies before running a skill that needs external APIs:

```bash
herbert-services check <skill-name>
```

If missing services are reported, guide the user to connect them first.

### 2. Connect a service

```bash
herbert-services connect <service-id>
```

This prints:
- What the service does
- Setup URL
- Required credentials with validation patterns
- Which skills use this service

The user must export credentials to their environment, then run `connect` again to register.

### 3. Sync to OpenClaw

```bash
herbert-services sync
```

Writes to `~/.openclaw/openclaw.json`:
- **MCP servers** (e.g., GitHub MCP server with resolved token)
- **Env vars** (all connected service credentials)

Only touches entries managed by the registry. Manually-added MCP servers and env vars are preserved.

### 4. Disconnect when done

```bash
herbert-services disconnect <service-id>
herbert-services sync
```

Removes the service from the registry and cleans up `openclaw.json`.

## Integration with Skills

Skills declare their service dependencies in the catalog. When a user asks to use a skill:

1. Run `herbert-services check <skill>` to verify readiness
2. If not ready, show `herbert-services skill <skill>` to list missing services
3. Guide the user through `herbert-services connect <svc>` for each missing service
4. Run `herbert-services sync` to apply changes
5. Proceed with the skill

## Files

- `~/.openclaw/services/catalog.json` — User overrides for the service catalog
- `~/.openclaw/services/services.json` — Connected services registry
- `~/.openclaw/services/herbert_services.py` — Core implementation
- `~/.openclaw/openclaw.json` — Sync target (MCP servers + env vars)

## Security

- Credentials are validated against regex patterns before sync
- Only env vars present in the shell environment are synced (never hardcoded)
- Disconnected services are fully cleaned from `openclaw.json`
- The registry never stores credential values — only references to env vars
- OpenClaw's existing secret resolution (`env`, `file`, `exec`) can be used for production
