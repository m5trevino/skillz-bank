#!/home/flintx/ai-chats/.venv/bin/python3
"""
PEACOCK MEMORY: Query Engine v2.0
Hybrid RRF search using existing ~/ai-chats/.venv/ and chroma-db/
"""

import sys
import os
sys.path.insert(0, '/home/flintx/ai-chats/.venv/lib/python3.11/site-packages')

import json
import sqlite3
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import chromadb
from chromadb.config import Settings
import aiohttp
import asyncio
import requests
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

PEACOCK_URL = "http://localhost:3099"
CHROMA_PATH = "/home/flintx/ai-chats/chroma-db/peacock-memory"
K_RRF = 60

console = Console()

@dataclass
class SearchResult:
    chunk_id: str
    content: str
    vault: str
    metadata: Dict
    rrf_score: float
    semantic_rank: int
    keyword_rank: int
    metadata_rank: int

class HybridQueryEngine:
    def __init__(self):
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_PATH, settings=Settings(anonymized_telemetry=False))
        self.sqlite_path = f"{CHROMA_PATH}/keyword_index.db"
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _get_embedding_sync(self, query: str) -> List[float]:
        try:
            resp = requests.post(f"{PEACOCK_URL}/v1/strike",
                json={"modelId": "gemini-embedding-exp-03-07", "input": [query], "task_type": "RETRIEVAL_QUERY"},
                timeout=30)
            if resp.status_code == 200:
                return resp.json()["embeddings"][0]
        except Exception as e:
            console.print(f"[red]Embedding error: {e}[/red]")
        return [0.0] * 768
    
    def _semantic_search(self, query_embedding: List[float], vaults: List[str], top_k: int = 50):
        results = []
        for vault in vaults:
            try:
                collection = self.chroma_client.get_collection(vault)
                vault_results = collection.query(query_embeddings=[query_embedding], n_results=min(top_k, 30), include=["distances"])
                if vault_results["ids"][0]:
                    for idx, chunk_id in enumerate(vault_results["ids"][0]):
                        score = 1.0 - min(vault_results["distances"][0][idx], 1.0)
                        results.append((chunk_id, score, vault))
            except Exception as e:
                console.print(f"[dim]Semantic error for {vault}: {e}[/dim]")
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def _keyword_search(self, query: str, top_k: int = 50):
        try:
            conn = sqlite3.connect(self.sqlite_path)
            c = conn.cursor()
            c.execute("SELECT chunk_id, rank FROM chunks_fts WHERE chunks_fts MATCH ? ORDER BY rank LIMIT ?", (query, top_k))
            results = [row[0] for row in c.fetchall()]
            conn.close()
            return results
        except Exception as e:
            console.print(f"[dim]Keyword error: {e}[/dim]")
            return []
    
    def _metadata_search(self, project=None, maturity=None, platform=None, vault=None, date_after=None, has_code=None, top_k=50):
        try:
            conn = sqlite3.connect(self.sqlite_path)
            c = conn.cursor()
            conditions, params = [], []
            if vault: conditions.append("vault = ?"); params.append(vault)
            if project: conditions.append("project = ?"); params.append(project)
            if maturity: conditions.append("maturity = ?"); params.append(maturity)
            if platform: conditions.append("platform = ?"); params.append(platform)
            if date_after: conditions.append("timestamp > ?"); params.append(date_after)
            if has_code is not None: conditions.append("has_code = ?"); params.append(1 if has_code else 0)
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            c.execute(f"SELECT chunk_id FROM chunks WHERE {where_clause} ORDER BY timestamp DESC LIMIT ?", params + [top_k])
            results = [row[0] for row in c.fetchall()]
            conn.close()
            return results
        except Exception as e:
            console.print(f"[dim]Metadata error: {e}[/dim]")
            return []
    
    def _reciprocal_rank_fusion(self, semantic, keyword, metadata, top_k=20):
        rrf_scores, vault_map = {}, {}
        for rank, (doc_id, score, vault) in enumerate(semantic, 1):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1.0 / (K_RRF + rank)
            vault_map[doc_id] = vault
        for rank, doc_id in enumerate(keyword, 1):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1.0 / (K_RRF + rank)
        for rank, doc_id in enumerate(metadata, 1):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1.0 / (K_RRF + rank)
        fused = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        return [(doc_id, score, vault_map.get(doc_id, "unknown")) for doc_id, score in fused[:top_k]]
    
    def _fetch_chunk_details(self, chunk_ids: List[str]):
        results = {}
        for vault in ["tech_vault", "case_files_vault", "personal_vault", "seed_vault"]:
            try:
                collection = self.chroma_client.get_collection(vault)
                vault_chunk_ids = [cid for cid in chunk_ids if cid not in results]
                if not vault_chunk_ids: continue
                vault_results = collection.get(ids=vault_chunk_ids, include=["documents", "metadatas"])
                for i, chunk_id in enumerate(vault_results["ids"]):
                    results[chunk_id] = {"content": vault_results["documents"][i], "metadata": vault_results["metadatas"][i], "vault": vault}
            except: continue
        return results
    
    def search(self, query: str, vaults=None, project=None, maturity=None, platform=None, date_after=None, has_code=None, top_k=20):
        vaults = vaults or ["tech_vault", "case_files_vault", "personal_vault", "seed_vault"]
        query_embedding = self._get_embedding_sync(query)
        semantic_results = self._semantic_search(query_embedding, vaults, top_k=50)
        keyword_results = self._keyword_search(query, top_k=50)
        metadata_results = self._metadata_search(project, maturity, platform, vaults[0] if len(vaults)==1 else None, date_after, has_code, top_k=50)
        fused = self._reciprocal_rank_fusion(semantic_results, keyword_results, metadata_results, top_k)
        chunk_ids = [f[0] for f in fused]
        details = self._fetch_chunk_details(chunk_ids)
        semantic_rank_map = {id: i+1 for i, (id, _, _) in enumerate(semantic_results)}
        keyword_rank_map = {id: i+1 for i, id in enumerate(keyword_results)}
        metadata_rank_map = {id: i+1 for i, id in enumerate(metadata_results)}
        results = []
        for chunk_id, rrf_score, vault in fused:
            if chunk_id in details:
                d = details[chunk_id]
                results.append(SearchResult(chunk_id=chunk_id, content=d["content"], vault=d["vault"], metadata=d["metadata"],
                    rrf_score=rrf_score, semantic_rank=semantic_rank_map.get(chunk_id, 999),
                    keyword_rank=keyword_rank_map.get(chunk_id, 999), metadata_rank=metadata_rank_map.get(chunk_id, 999)))
        return results
    
    async def synthesize(self, query: str, results: List[SearchResult], model: str = "llama3-3-70b-versatile"):
        if not results:
            return "No relevant context found."
        context_parts = []
        for i, r in enumerate(results[:8], 1):
            meta = r.metadata
            source = f"{meta.get('file_source', 'unknown')}, Entry #{meta.get('entry_num', '?')}"
            context_parts.append(f"""--- Context {i} [{source}] ---
Platform: {meta.get('platform', 'UNK')} | Project: {meta.get('project', 'unknown')} | Maturity: {meta.get('maturity', '?')}
{r.content[:600]}""")
        context = "\n".join(context_parts)
        prompt = f"""You are FlintX's memory assistant with access to his complete AI conversation history. Answer based ONLY on the provided context.

USER QUESTION: {query}

RETRIEVED CONTEXT:
{context}

INSTRUCTIONS:
1. Answer comprehensively using only the context provided
2. Cite specific sources: [filename.md, Entry #XXX]
3. Note idea maturity: embryonic vs. implemented vs. abandoned
4. Surface contradictions or pivots if found
5. If context insufficient, say so — don't hallucinate

FORMAT:
**Answer**: [synthesized response with inline citations]

**Key Sources**:
- [file, entry] - relevance note

**Unresolved/Embryonic**: [list any ideas mentioned but not completed]"""
        try:
            async with self.session.post(f"{PEACOCK_URL}/v1/strike",
                json={"modelId": model, "prompt": prompt, "temp": 0.3}, timeout=60) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("content", "Error: empty response")
                else:
                    return f"Error: Peacock returned {resp.status}"
        except Exception as e:
            return f"Error calling Peacock: {e}"

def format_result(result: SearchResult, idx: int):
    meta = result.metadata
    title = f"{idx}. {meta.get('file_source', 'unknown')} #{meta.get('entry_num', '?')}"
    subtitle = f"{meta.get('platform', 'UNK')} | {result.vault} | {meta.get('maturity', '?')}"
    content = result.content[:700] + "..." if len(result.content) > 700 else result.content
    info = f"""[dim]RRF:[/dim] {result.rrf_score:.4f} | [dim]Ranks:[/dim] s#{result.semantic_rank} k#{result.keyword_rank} m#{result.metadata_rank}
[dim]Project:[/dim] {meta.get('project', 'unknown')} | [dim]Follow-up:[/dim] {meta.get('requires_follow_up', False)}"""
    return Panel(f"{content}\n\n{info}", title=f"[bold cyan]{title}[/bold cyan]", subtitle=f"[dim]{subtitle}[/dim]", border_style="blue")

def main():
    if len(sys.argv) < 2:
        console.print(Panel.fit(
            "[bold]Peacock Memory Query Engine v2.0[/bold]\n\n"
            "Usage: query_engine.py [cyan]\"your query\"[/cyan] [options]\n\n"
            "Options:\n"
            "  [cyan]--vault[/cyan] tech|case|personal|seed\n"
            "  [cyan]--project[/cyan] name\n"
            "  [cyan]--maturity[/cyan] embryonic|committed|completed\n"
            "  [cyan]--platform[/cyan] GEMINI|CLAUDE|CHATGPT\n"
            "  [cyan]--code[/cyan]\n"
            "  [cyan]--after[/cyan] YYYY-MM-DD\n"
            "  [cyan]--synthesize[/cyan]\n"
            "  [cyan]--limit[/cyan] N\n\n"
            "Examples:\n"
            '  ~/ai-chats/.venv/bin/python query_engine.py "invariant law" --project peacock --synthesize\n'
            '  ~/ai-chats/.venv/bin/python query_engine.py "abandoned ideas" --vault seed --maturity embryonic',
            title="Hybrid RRF Search", border_style="green"
        ))
        return
    
    query = sys.argv[1]
    args = sys.argv[2:]
    vaults, project, maturity, platform, date_after, has_code, do_synthesize, limit = None, None, None, None, None, None, False, 10
    
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--vault" and i + 1 < len(args):
            vault_map = {"tech": "tech_vault", "case": "case_files_vault", "personal": "personal_vault", "seed": "seed_vault"}
            vaults = [vault_map.get(args[i+1], args[i+1])]
            i += 2
        elif arg == "--project" and i + 1 < len(args):
            project = args[i+1]
            i += 2
        elif arg == "--maturity" and i + 1 < len(args):
            maturity = args[i+1]
            i += 2
        elif arg == "--platform" and i + 1 < len(args):
            platform = args[i+1]
            i += 2
        elif arg == "--after" and i + 1 < len(args):
            date_after = args[i+1]
            i += 2
        elif arg == "--code":
            has_code = True
            i += 1
        elif arg == "--synthesize":
            do_synthesize = True
            i += 1
        elif arg == "--limit" and i + 1 < len(args):
            limit = int(args[i+1])
            i += 2
        else:
            i += 1
    
    engine = HybridQueryEngine()
    console.print(f"[bold cyan]Searching:[/bold cyan] {query}")
    if vaults:
        console.print(f"[dim]Vaults: {', '.join(vaults)}[/dim]")
    if project:
        console.print(f"[dim]Project: {project}[/dim]")
    
    results = engine.search(query, vaults, project, maturity, platform, date_after, has_code, limit)
    console.print(f"[green]Found {len(results)} results (RRF fused)[/green]\n")
    
    for i, r in enumerate(results, 1):
        console.print(format_result(r, i))
    
    if do_synthesize and results:
        console.print("\n[bold yellow]Synthesizing via Peacock...[/bold yellow]")
        async def run_synthesis():
            async with engine:
                return await engine.synthesize(query, results)
        try:
            answer = asyncio.run(run_synthesis())
            console.print(Panel(Markdown(answer), title="[bold green]Synthesized Answer[/bold green]", border_style="green"))
        except Exception as e:
            console.print(f"[red]Synthesis failed: {e}[/red]")

if __name__ == "__main__":
    main()
