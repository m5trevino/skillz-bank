# Herbert Expert Builder

Turn your humanized chats and research documents into a queryable expert using RAG (Retrieval-Augmented Generation).

## When to use

- You have a folder of humanized chat exports (from `chat-humanizer`)
- You have research papers, notes, or project docs in Markdown
- You want to ask questions across ALL of that material without re-reading
- You want an "expert LLM" on a specific topic you've already explored

## Prerequisites

```bash
export OPENAI_API_KEY="sk-..."
```

Get a key at https://platform.openai.com/api-keys. Costs are minimal:
- **Embeddings**: `text-embedding-3-small` — ~$0.02 per 1M tokens
- **Queries**: `gpt-4o-mini` — ~$0.15 per 1M input tokens

## Quick start

```bash
# 1. Humanize your chats first
python3 ~/.openclaw/skills/chat-humanizer/humanize.py ~/Downloads/claude_chats.json ~/chats/claude/ --split

# 2. Create an expert
he create ml-research --source ~/chats/claude/ --source ~/papers/

# 3. Query it
he query ml-research "What did I decide about gradient boosting vs neural nets?"

# 4. Or chat interactively
he chat ml-research
```

## Commands

### `he create <name> --source <path> [--source <path>...]`

Ingest files into a named ChromaDB collection. Supports:
- `.md`, `.txt`, `.markdown` — full text
- `.json` — attempts to extract messages/text fields
- `.py` — wrapped in code blocks
- Directories are recursively scanned

Chunking strategy (automatic):
- **Conversations**: Split by User/Assistant turns, 1500-char chunks with 200-char overlap
- **Markdown with headers**: Split by `##` sections
- **Plain text**: Paragraph-based sliding window

### `he list`

Show all experts and their chunk counts.

### `he info <name>`

Show metadata and sample chunks for an expert.

### `he query <name> "<question>" [--model <model>]`

Single-shot RAG query. Retrieves top-5 relevant chunks, sends to LLM with citation instructions.

Default model: `gpt-4o-mini` (cheap, fast). Override with `--model gpt-4o` for harder questions.

### `he chat <name> [--model <model>]`

Interactive chat with memory (last 4 exchanges). Type `quit` or `exit` to stop.

### `he delete <name>`

Remove an expert collection.

## Aliases

| Alias | Command |
|-------|---------|
| `he` | `~/.openclaw/services/herbert-expert` |
| `hex` | `~/.openclaw/services/herbert-expert` |
| `hel` | `~/.openclaw/services/herbert-expert list` |

## Architecture

```
Source files → Ingest → Chunk (semantic) → Embed (OpenAI) → ChromaDB collection
                                                    ↑
User question → Embed → Similarity search → Top-k chunks → LLM prompt → Answer
```

Data is stored locally at `~/.openclaw/experts/chromadb/`. No data leaves your machine except for OpenAI API calls.

## Tips

- **Combine sources**: A single expert can ingest chats + papers + code. The RAG retrieval finds relevant context across all of them.
- **Naming**: Use kebab-case names (`ml-research`, `startup-ideas`, `rust-patterns`).
- **Updating**: Re-run `create` with the same name to rebuild from scratch.
- **Cost**: A typical 50-conversation export (~100k tokens) costs ~$0.02 to embed and ~$0.01 per query.
