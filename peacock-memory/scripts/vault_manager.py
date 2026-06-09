#!/home/flintx/ai-chats/.venv/bin/python3
"""
PEACOCK MEMORY: Vault Manager v2.0
CORRECTED PATHS: Uses ~/ai-chats/aistudio/, chatgpt/, claude/ directly
"""

import sys
import os
import re
import json
import asyncio
import hashlib
import aiohttp
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import chromadb
from chromadb.config import Settings
import sqlite3
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.panel import Panel

# CORRECTED CONFIGURATION
PEACOCK_URL = "http://localhost:3099"
CHROMA_PATH = "/home/flintx/ai-chats/chroma-db/peacock-memory"  # Uses your existing chroma-db dir
LOGS_DIRS = [
    "/home/flintx/ai-chats/aistudio",      # CORRECTED: no all-logs-clean/
    "/home/flintx/ai-chats/chatgpt",       # CORRECTED: no all-logs-clean/
    "/home/flintx/ai-chats/claude"         # CORRECTED: no all-logs-clean/
]
BATCH_SIZE = 50
CHECKPOINT_FILE = "/home/flintx/ai-chats/chroma-db/peacock-memory_checkpoint.json"

console = Console()

@dataclass
class ExchangePair:
    user_entry: str
    ai_response: str
    entry_num: str
    platform: str
    file_source: str
    timestamp: Optional[str] = None
    branch_info: Optional[Dict] = None

@dataclass
class EnrichedChunk:
    exchange: ExchangePair
    chunk_id: str
    vault: str
    topics: List[str]
    project_context: Optional[str]
    idea_maturity: str
    code_languages: List[str]
    has_code_blocks: bool
    requires_follow_up: bool
    confidence: float
    entities: List[str]

class PeacockClient:
    def __init__(self, base_url: str = PEACOCK_URL):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.available = False
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        self.available = await self.health_check()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def health_check(self) -> bool:
        try:
            async with self.session.get(f"{self.base_url}/health", timeout=5) as resp:
                return resp.status == 200
        except:
            return False
    
    async def triage(self, content: str) -> Dict:
        if not self.available:
            return self._fallback_triage(content)
        
        prompt = f"""ACT AS: THE TRIAGE OFFICER + IDEA MINER.
Analyze this chat log exchange. Classify into exactly one vault:
- tech_vault: Code, Peacock, Social Lube, APIs, Linux, scripts, development
- case_files_vault: True crime, investigations, legal, court, transcripts
- personal_vault: Spiritual, family, goals, personal history, relationships
- seed_vault: Unassigned ideas, embryonic concepts, random thoughts, pivots

EXTRACT:
- project: Specific name if tech_vault (peacock, social-lube, dark-room, etc.)
- maturity: embryonic|exploring|committed|abandoned|completed|uncertain
- topics: Technical concepts mentioned
- has_code: true if contains code blocks
- entities: Named tools, people, projects
- requires_follow_up: true if embryonic/exploring without resolution

Return ONLY JSON:
{{"vault": "...", "project": "...", "maturity": "...", "topics": [...], "has_code": bool, "entities": [...], "requires_follow_up": bool, "confidence": 0.0-1.0}}

CONTENT:
{content[:2500]}"""
        
        try:
            async with self.session.post(
                f"{self.base_url}/v1/strike", 
                json={"modelId": "llama3-8b-8192", "prompt": prompt, "temp": 0.1},
                timeout=30
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return self._parse_response(data.get("content", "{}"))
                else:
                    return self._fallback_triage(content)
        except Exception as e:
            return self._fallback_triage(content)
    
    def _parse_response(self, content: str) -> Dict:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            for pattern in [r'```json\s*(.*?)\s*```', r'```\s*(.*?)\s*```', r'\{.*?\}']:
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    try:
                        return json.loads(match.group(1) if '```' in pattern else match.group())
                    except:
                        continue
            return self._fallback_triage(content)
    
    def _fallback_triage(self, content: str) -> Dict:
        content_lower = content.lower()
        tech_signals = ["peacock", "social-lube", "code", "api", "python", "react", "chroma", "function", "class", "def ", "import "]
        case_signals = ["kohberger", "crime", "court", "legal", "transcript", "investigation", "murder", "case"]
        personal_signals = ["spiritual", "family", "goal", "personal", "wife", "girlfriend", "mother", "father", "meditation"]
        
        vault = "seed_vault"
        project = None
        confidence = 0.4
        
        if any(s in content_lower for s in case_signals):
            vault = "case_files_vault"
            confidence = 0.6
        elif any(s in content_lower for s in personal_signals):
            vault = "personal_vault"
            confidence = 0.5
        elif any(s in content_lower for s in tech_signals):
            vault = "tech_vault"
            confidence = 0.6
            if "peacock" in content_lower:
                project = "peacock"
            elif "social-lube" in content_lower or "social lube" in content_lower:
                project = "social-lube"
            elif "dark-room" in content_lower or "dark room" in content_lower:
                project = "dark-room"
        
        return {
            "vault": vault, "project": project, "maturity": "uncertain",
            "topics": [], "has_code": "```" in content or "def " in content,
            "entities": [], "requires_follow_up": False, "confidence": confidence
        }
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        async with self.session.post(
            f"{self.base_url}/v1/strike",
            json={"modelId": "gemini-embedding-exp-03-07", "input": texts, "task_type": "RETRIEVAL_DOCUMENT"},
            timeout=60
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("embeddings", [])
            else:
                raise Exception(f"Embedding failed: {resp.status}")

class ASCIIParser:
    BORDER_PATTERNS = [
        r'[┎━─━┒┍──━┑╔═══╗]\s*[\n\r]+.*?�\s*(.*?)\s*�.*?[\n\r]+.*?░█░█░█▀▀░.*?[\n\r]+\[(USER ENTRY|GEMINI RESPONSE|CLAUDE RESPONSE|CHATGPT RESPONSE)\s*#(\d+)\].*?[\n\r]+[┖━─━┚┕──━┙╚═══╝](.*?)(?=[┎━─━┒┍──━┑╔═══╗]|$)',
        r'[┎━─━┒┍──━┑╔═══╗].*?\[(USER ENTRY|GEMINI RESPONSE|CLAUDE RESPONSE|CHATGPT RESPONSE)\s*#(\d+)\].*?[┖━─━┚┕──━┙╚═══╝](.*?)(?=[┎━─━┒┍──━┑╔═══╗]|$)',
    ]
    
    PLATFORM_MAP = {
        "USER ENTRY": "USER", "GEMINI RESPONSE": "GEMINI",
        "CLAUDE RESPONSE": "CLAUDE", "CHATGPT RESPONSE": "CHATGPT"
    }
    
    def parse_file(self, filepath: Path) -> List[ExchangePair]:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            console.print(f"[red]Failed to read {filepath}: {e}[/red]")
            return []
        
        if len(content) < 50:
            return []
        
        for pattern in self.BORDER_PATTERNS:
            matches = list(re.finditer(pattern, content, re.DOTALL | re.IGNORECASE))
            if len(matches) >= 2:
                return self._process_matches(matches, filepath, content)
        
        return self._fallback_parse(content, filepath)
    
    def _process_matches(self, matches, filepath: Path, raw_content: str) -> List[ExchangePair]:
        exchanges = []
        i = 0
        while i < len(matches) - 1:
            current = matches[i]
            next_match = matches[i + 1]
            current_type = current.group(2).upper() if len(current.groups()) >= 2 else "UNKNOWN"
            next_type = next_match.group(2).upper() if len(next_match.groups()) >= 2 else "UNKNOWN"
            
            if "USER" in current_type and "USER" not in next_type:
                platform = self.PLATFORM_MAP.get(next_type, "UNKNOWN")
                exchanges.append(ExchangePair(
                    user_entry=current.group(3).strip() if len(current.groups()) >= 3 else current.group(0),
                    ai_response=next_match.group(3).strip() if len(next_match.groups()) >= 3 else next_match.group(0),
                    entry_num=current.group(3) if len(current.groups()) >= 3 and current.group(3).isdigit() else str(i),
                    platform=platform, file_source=str(filepath),
                    timestamp=self._extract_date(filepath.name),
                    branch_info=self._detect_branch(filepath.name)
                ))
                i += 2
            else:
                i += 1
        return exchanges
    
    def _fallback_parse(self, content: str, filepath: Path) -> List[ExchangePair]:
        exchanges = []
        lines = content.split('\n')
        current_user = None
        entry_num = 0
        for line in lines:
            if '[USER ENTRY' in line.upper():
                current_user = line
                entry_num += 1
            elif current_user and any(x in line.upper() for x in ['GEMINI', 'CLAUDE', 'CHATGPT']):
                exchanges.append(ExchangePair(
                    user_entry=current_user, ai_response=line, entry_num=str(entry_num),
                    platform=self._detect_platform(line), file_source=str(filepath),
                    timestamp=self._extract_date(filepath.name),
                    branch_info=self._detect_branch(filepath.name)
                ))
                current_user = None
        return exchanges
    
    def _detect_platform(self, line: str) -> str:
        line_upper = line.upper()
        if 'GEMINI' in line_upper: return 'GEMINI'
        elif 'CLAUDE' in line_upper: return 'CLAUDE'
        elif 'CHATGPT' in line_upper or 'GPT' in line_upper: return 'CHATGPT'
        return 'UNKNOWN'
    
    def _extract_date(self, filename: str) -> Optional[str]:
        patterns = [(r'(\d{2})\.(\d{2})\.(\d{2})', True), (r'(\d{4})-(\d{2})-(\d{2})', False)]
        for pattern, is_yy in patterns:
            match = re.search(pattern, filename)
            if match:
                if is_yy:
                    mm, dd, yy = match.groups()
                    return f"20{yy}-{mm}-{dd}"
                else:
                    yyyy, mm, dd = match.groups()
                    return f"{yyyy}-{mm}-{dd}"
        return None
    
    def _detect_branch(self, filename: str) -> Dict:
        fname_lower = filename.lower()
        if 'branch' in fname_lower:
            match = re.search(r'branch[-_]?(\d+)', fname_lower)
            if match:
                return {"is_branch": True, "branch_num": int(match.group(1))}
        return {"is_branch": False}

class ChromaVault:
    VAULTS = ["tech_vault", "case_files_vault", "personal_vault", "seed_vault"]
    
    def __init__(self, path: str = CHROMA_PATH):
        os.makedirs(path, exist_ok=True)
        self.client = chromadb.PersistentClient(path=path, settings=Settings(anonymized_telemetry=False))
        self.collections = {}
        self._init_collections()
        self.sqlite_path = os.path.join(path, "keyword_index.db")
        self._init_sqlite()
    
    def _init_collections(self):
        for vault in self.VAULTS:
            self.collections[vault] = self.client.get_or_create_collection(
                name=vault, metadata={"hnsw:space": "cosine"}
            )
    
    def _init_sqlite(self):
        conn = sqlite3.connect(self.sqlite_path)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id TEXT PRIMARY KEY, content TEXT, vault TEXT, project TEXT,
                platform TEXT, timestamp TEXT, maturity TEXT, file_source TEXT,
                entry_num TEXT, has_code BOOLEAN, requires_follow_up BOOLEAN
            )
        """)
        c.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                content, vault, project, maturity, content='chunks', content_rowid='rowid'
            )
        """)
        conn.commit()
        conn.close()
    
    def upsert_chunk(self, chunk: EnrichedChunk, embedding: List[float]):
        collection = self.collections[chunk.vault]
        metadata = {
            "file_source": chunk.exchange.file_source, "entry_num": chunk.exchange.entry_num,
            "platform": chunk.exchange.platform, "project": chunk.project_context or "unknown",
            "maturity": chunk.idea_maturity, "topics": ",".join(chunk.topics),
            "entities": ",".join(chunk.entities), "has_code": chunk.has_code_blocks,
            "requires_follow_up": chunk.requires_follow_up, "confidence": chunk.confidence,
            "timestamp": chunk.exchange.timestamp or "unknown",
            "is_branch": chunk.exchange.branch_info.get("is_branch", False)
        }
        content = f"USER: {chunk.exchange.user_entry}\n\nAI ({chunk.exchange.platform}): {chunk.exchange.ai_response}"
        
        collection.upsert(
            ids=[chunk.chunk_id], documents=[content], embeddings=[embedding], metadatas=[metadata]
        )
        
        conn = sqlite3.connect(self.sqlite_path)
        c = conn.cursor()
        c.execute("""
            INSERT OR REPLACE INTO chunks 
            (chunk_id, content, vault, project, platform, timestamp, maturity, file_source, entry_num, has_code, requires_follow_up)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (chunk.chunk_id, content, chunk.vault, chunk.project_context, chunk.exchange.platform,
              chunk.exchange.timestamp, chunk.idea_maturity, chunk.exchange.file_source,
              chunk.exchange.entry_num, chunk.has_code_blocks, chunk.requires_follow_up))
        conn.commit()
        conn.close()

class CheckpointManager:
    def __init__(self, path: str = CHECKPOINT_FILE):
        self.path = path
        self.state = self._load()
    
    def _load(self) -> Dict:
        if os.path.exists(self.path):
            try:
                with open(self.path, 'r') as f:
                    return json.load(f)
            except:
                return self._empty_state()
        return self._empty_state()
    
    def _empty_state(self) -> Dict:
        return {"processed_files": {}, "last_run": None, "total_chunks": 0, "vault_counts": {v: 0 for v in ChromaVault.VAULTS}}
    
    def save(self):
        with open(self.path, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def is_processed(self, file_hash: str) -> bool:
        return file_hash in self.state["processed_files"]
    
    def mark_processed(self, file_hash: str, file_path: str, chunks: int, vault: str):
        self.state["processed_files"][file_hash] = {
            "path": file_path, "chunks": chunks, "vault": vault,
            "timestamp": datetime.now().isoformat()
        }
        self.state["total_chunks"] += chunks
        self.state["vault_counts"][vault] = self.state["vault_counts"].get(vault, 0) + chunks
        self.state["last_run"] = datetime.now().isoformat()
        self.save()
    
    def get_stats(self) -> Dict:
        return self.state

class VaultManager:
    def __init__(self):
        self.parser = ASCIIParser()
        self.vault = ChromaVault()
        self.checkpoint = CheckpointManager()
        self.peacock: Optional[PeacockClient] = None
        
    async def initialize(self):
        self.peacock = PeacockClient()
        await self.peacock.__aenter__()
        if self.peacock.available:
            console.print("[green]✓ Peacock Engine V2 connected[/green]")
        else:
            console.print("[yellow]⚠ Peacock unavailable — using fallback triage[/yellow]")
    
    async def shutdown(self):
        if self.peacock:
            await self.peacock.__aexit__(None, None, None)
    
    async def ingest_file(self, filepath: Path, progress: Progress, task: TaskID) -> Tuple[int, str]:
        file_hash = hashlib.md5(filepath.read_bytes()).hexdigest()
        if self.checkpoint.is_processed(file_hash):
            progress.advance(task)
            return 0, "skipped"
        
        exchanges = self.parser.parse_file(filepath)
        if not exchanges:
            progress.advance(task)
            return 0, "empty"
        
        chunks = []
        for exchange in exchanges:
            content = f"{exchange.user_entry}\n\n{exchange.ai_response}"
            triage_result = await self.peacock.triage(content)
            
            chunks.append(EnrichedChunk(
                exchange=exchange,
                chunk_id=f"{file_hash[:16]}_{exchange.entry_num}_{exchange.platform}",
                vault=triage_result.get("vault", "seed_vault"),
                topics=triage_result.get("topics", []),
                project_context=triage_result.get("project"),
                idea_maturity=triage_result.get("maturity", "uncertain"),
                code_languages=[],
                has_code_blocks=triage_result.get("has_code", False),
                requires_follow_up=triage_result.get("requires_follow_up", False),
                confidence=triage_result.get("confidence", 0.5),
                entities=triage_result.get("entities", [])
            ))
        
        vault_chunks = {}
        for c in chunks:
            vault_chunks.setdefault(c.vault, []).append(c)
        
        total_stored = 0
        for vault, vault_chunk_list in vault_chunks.items():
            texts = [f"USER: {c.exchange.user_entry}\n\nAI: {c.exchange.ai_response}" for c in vault_chunk_list]
            try:
                if self.peacock.available:
                    embeddings = await self.peacock.embed(texts)
                    for chunk, embedding in zip(vault_chunk_list, embeddings):
                        self.vault.upsert_chunk(chunk, embedding)
                        total_stored += 1
                else:
                    console.print(f"[red]Cannot embed {filepath.name} — Peacock down[/red]")
                    return 0, "error"
            except Exception as e:
                console.print(f"[red]Embedding failed for {filepath.name}: {e}[/red]")
                return 0, "error"
        
        primary_vault = max(vault_chunks.keys(), key=lambda k: len(vault_chunks[k])) if vault_chunks else "seed_vault"
        self.checkpoint.mark_processed(file_hash, str(filepath), total_stored, primary_vault)
        progress.advance(task)
        return total_stored, "success"
    
    async def run_ingestion(self, max_files: Optional[int] = None, specific_dirs: Optional[List[str]] = None):
        await self.initialize()
        try:
            dirs_to_scan = specific_dirs or LOGS_DIRS
            all_files = []
            
            for log_dir in dirs_to_scan:
                path = Path(log_dir)
                if path.exists():
                    files = list(path.rglob("*.md"))
                    console.print(f"[dim]Found {len(files)} .md files in {log_dir}[/dim]")
                    all_files.extend(files)
                else:
                    console.print(f"[yellow]Directory not found: {log_dir}[/yellow]")
            
            files_to_process = [f for f in all_files if not self.checkpoint.is_processed(hashlib.md5(f.read_bytes()).hexdigest())]
            if max_files:
                files_to_process = files_to_process[:max_files]
            
            if not files_to_process:
                console.print("[green]All files already processed![/green]")
                self._print_stats()
                return
            
            console.print(f"[bold cyan]Processing {len(files_to_process)} files ({len(all_files) - len(files_to_process)} already done)[/bold cyan]")
            
            with Progress(TextColumn("[bold blue]{task.description}"), BarColumn(), TextColumn("[progress.percentage]{task.percentage:>3.0f}%"), TimeElapsedColumn(), console=console) as progress:
                task = progress.add_task("[cyan]Ingesting...", total=len(files_to_process))
                semaphore = asyncio.Semaphore(3)
                
                async def process_with_limit(f: Path):
                    async with semaphore:
                        return await self.ingest_file(f, progress, task)
                
                results = await asyncio.gather(*[process_with_limit(f) for f in files_to_process])
            
            success_count = sum(1 for r in results if r[1] == "success")
            total_chunks = sum(r[0] for r in results)
            console.print(f"[bold green]✓ Ingested {total_chunks} chunks from {success_count} files[/bold green]")
            self._print_stats()
        finally:
            await self.shutdown()
    
    def _print_stats(self):
        stats = self.checkpoint.get_stats()
        table = Table(title="Vault Statistics")
        table.add_column("Vault", style="cyan")
        table.add_column("Chunks", style="green")
        table.add_column("% of Total", style="yellow")
        total = stats["total_chunks"]
        for vault, count in stats["vault_counts"].items():
            pct = (count / total * 100) if total > 0 else 0
            table.add_row(vault, str(count), f"{pct:.1f}%")
        table.add_row("TOTAL", str(total), "100%", style="bold")
        console.print(table)
        console.print(f"[dim]Checkpoint: {CHECKPOINT_FILE}[/dim]")

def main():
    if len(sys.argv) < 2:
        console.print(Panel.fit(
            "[bold]Peacock Memory Vault Manager v2.0[/bold]\n\n"
            "Commands:\n"
            "  [cyan]init[/cyan] [max_files] [dir1,dir2,...]  - Start/resume ingestion\n"
            "  [cyan]status[/cyan]                            - Show checkpoint status\n"
            "  [cyan]test[/cyan] <file>                         - Test parse single file\n"
            "  [cyan]reset[/cyan]                               - Clear checkpoint\n\n"
            "Examples:\n"
            "  ~/ai-chats/.venv/bin/python vault_manager.py init\n"
            "  ~/ai-chats/.venv/bin/python vault_manager.py init 100 aistudio\n"
            "  ~/ai-chats/.venv/bin/python vault_manager.py init 0 aistudio,chatgpt",
            title="Usage", border_style="blue"
        ))
        return
    
    command = sys.argv[1]
    manager = VaultManager()
    
    if command == "init":
        max_files = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else None
        specific_dirs = None
        if len(sys.argv) > 3:
            dir_names = sys.argv[3].split(',')
            specific_dirs = [f"/home/flintx/ai-chats/{name.strip()}" for name in dir_names]
        
        asyncio.run(manager.run_ingestion(max_files, specific_dirs))
    
    elif command == "status":
        stats = manager.checkpoint.get_stats()
        console.print(f"[bold]Checkpoint Status[/bold]")
        console.print(f"Files processed: {len(stats['processed_files'])}")
        console.print(f"Total chunks: {stats['total_chunks']}")
        console.print(f"Last run: {stats['last_run'] or 'Never'}")
        for vault, count in stats["vault_counts"].items():
            console.print(f"  {vault}: {count}")
    
    elif command == "test":
        test_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(LOGS_DIRS[0]) / "01.07.26-your-year.with.chatgpt.md"
        if test_path.exists():
            console.print(f"[bold]Testing: {test_path}[/bold]")
            exchanges = manager.parser.parse_file(test_path)
            console.print(f"Found {len(exchanges)} exchanges")
            for i, ex in enumerate(exchanges[:3], 1):
                console.print(f"\n[cyan]Exchange {i}:[/cyan] Platform={ex.platform}, Entry={ex.entry_num}")
                console.print(f"  User: {ex.user_entry[:80]}...")
                console.print(f"  AI: {ex.ai_response[:80]}...")
            
            async def test_triage():
                await manager.initialize()
                if manager.peacock.available and exchanges:
                    result = await manager.peacock.triage(f"{exchanges[0].user_entry}\n\n{exchanges[0].ai_response}")
                    console.print(f"\n[green]Triage:[/green] {json.dumps(result, indent=2)}")
                await manager.shutdown()
            
            asyncio.run(test_triage())
        else:
            console.print(f"[red]File not found: {test_path}[/red]")
    
    elif command == "reset":
        confirm = input("Type 'DESTROY' to clear all checkpoints: ")
        if confirm == "DESTROY":
            if os.path.exists(CHECKPOINT_FILE):
                os.remove(CHECKPOINT_FILE)
                console.print("[red]Checkpoint destroyed[/red]")
            clear_db = input("Clear ChromaDB too? (yes/no): ")
            if clear_db == "yes":
                for name, coll in manager.vault.collections.items():
                    coll.delete(where={})
                console.print("[red]ChromaDB cleared[/red]")

if __name__ == "__main__":
    main()
