# WIRE-UI.md: Frontend-to-Backend Integration Guide

> **Version**: 1.0
> **Status**: [Ready/In-Progress]
> **Target**: Vite/React/HTML → [Backend Name]

---

## Architecture Overview

[Brief summary of the wiring strategy between frontend and backend.]

## Backend Endpoint Map

| Endpoint | Method | Payload (JSON) | Description |
|----------|--------|----------------|-------------|
| `/v1/chat` | POST | `{ "prompt": "...", "model": "..." }` | Standard Chat |
| `/v1/chat/stream` | POST | `{ "prompt": "...", "model": "..." }` | SSE Streaming |
| `/health` | GET | `None` | Health Check |

## Frontend Setup

### 1. Environment Variables
Create a `.env` file in the frontend root:
```env
VITE_API_BASE_URL=http://localhost:3099
```

### 2. Vite Proxy Configuration
In `vite.config.ts`, add a proxy to bypass CORS during development:
```typescript
export default defineConfig({
  server: {
    proxy: {
      '/v1': 'http://localhost:3099',
    },
  },
});
```

## Example Implementations

### A. Standard Fetch (REST)
```javascript
const response = await fetch('/v1/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ prompt: "Hello", model: "gemini-2.0" }),
});
const data = await response.json();
console.log(data.content);
```

### B. Real-Time Streaming (SSE)
```javascript
const response = await fetch('/v1/chat/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ prompt: "Tell a story", model: "gemini-2.0" }),
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { value, done } = await reader.read();
  if (done) break;
  const chunk = decoder.decode(value);
  console.log("Stream Chunk:", chunk);
}
```

## Wiring Logic & States

- **Loading State**: Show a spinner or "Typing..." indicator when `isFetching` is true.
- **Error Handling**: Catch 429 (Rate Limit) and 500 (Server Error) and display user-friendly alerts.
- **Success State**: Update the local conversation state (e.g., `messages` array) with the response `content`.

## Verification Commands

```bash
# Test the backend endpoint directly
curl -X POST http://localhost:3099/v1/chat -H "Content-Type: application/json" -d '{"prompt": "test"}'

# Test streaming
curl -X POST http://localhost:3099/v1/chat/stream -H "Content-Type: application/json" -d '{"prompt": "test"}'
```

---

**END OF WIRE-UI**
