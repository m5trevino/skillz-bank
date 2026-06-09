# Wiring Patterns

Tactical payloads for framework-specific handshake execution.

## FastAPI

### CORS Middleware
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Static Mounting
```python
from fastapi.staticfiles import StaticFiles
import os

if os.path.exists("app/static"):
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    app.mount("/", StaticFiles(directory="app/static", html=True), name="root_ui")
```

### SPA Catch-All
```python
from fastapi.responses import FileResponse

@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    if full_path.startswith("v1/") or full_path.startswith("static/"):
        return {"detail": "Not Found"}
    
    index_path = os.path.join("app/static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"detail": "Not Found"}
```

## Express (Node.js)

### CORS & Static
```javascript
const cors = require('cors');
const express = require('express');
const path = require('path');

app.use(cors());
app.use(express.static(path.join(__dirname, 'static')));

app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'static', 'index.html'));
});
```

## Vite (Frontend)

### Configuration
```typescript
// vite.config.ts
export default defineConfig({
  build: {
    outDir: '../app/static',
    emptyOutDir: true,
  },
  server: {
    port: 3000,
    proxy: {
      '/v1': 'http://localhost:3099',
    },
  },
});
```

### API Base Logic
```typescript
// api.ts
const isProd = typeof window !== 'undefined' && window.location.hostname !== 'localhost';
const API_BASE = isProd ? "" : "http://localhost:3099";
```
