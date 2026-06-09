#!/usr/bin/env python3
"""
Project Session Manager — Batch export + merge for all AI-CLI sessions.

Replaces the need for a /sessions-by-project view and /export-md per session.

Usage:
    # List all projects and their sessions
    python3 project_session_manager.py --list

    # Export all sessions for a project (separate files)
    python3 project_session_manager.py --export-project doc-dumpster

    # Export + merge into one file
    python3 project_session_manager.py --export-project doc-dumpster --merge

    # Export all projects
    python3 project_session_manager.py --export-all

    # Export all + merge each project
    python3 project_session_manager.py --export-all --merge

    # Backfill Kimi Code sessions into each project's devwater-data dir
    python3 project_session_manager.py --export-project doc-dumpster --devwater
    python3 project_session_manager.py --export-all --devwater
"""

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add parsers to path
sys.path.insert(0, str(Path(__file__).parent))

from parsers.kimi_code_parser import parse_kimi_code
from parsers.kimi_og_parser import parse_kimi_og, is_worth_parsing
from parsers.gemini_cli_parser import parse_gemini_cli, discover_gemini_sources
from parsers.claude_parser import parse_claude
from parsers.chatgpt_parser import parse_chatgpt
from parsers.aistudio_parser import parse_aistudio


# ──────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────

KIMI_CODE_ROOT = Path.home() / ".kimi-code" / "sessions"
KIMI_OG_ROOT = Path.home() / ".kimi" / "sessions"
GEMINI_ROOT = Path.home() / ".gemini" / "tmp"
CLAUDE_SOURCE = Path.home() / "ai-chats" / "claude" / "conversations.json"
CHATGPT_SOURCE = Path.home() / "ai-chats" / "chatgpt" / "conversations.json"
AISTUDIO_ROOT = Path.home() / "ai-chats" / "aistudio"

OUTPUT_ROOT = Path.home() / "peacock" / "aichats" / "by-project"

# Minimum assistant chars to consider a session "real"
MIN_ASSISTANT_CHARS = 100


# ──────────────────────────────────────────────────────────────
# Data model
# ──────────────────────────────────────────────────────────────

@dataclass
class Session:
    tool: str           # "kimi-code", "kimi-og", "gemini", "claude", "chatgpt", "aistudio"
    project: str        # project name / cwd basename
    session_id: str     # unique session identifier
    source_path: Path   # path to session dir or file
    created_at: Optional[datetime] = None
    title: str = ""
    assistant_chars: int = 0
    user_chars: int = 0
    sets_count: int = 0


@dataclass
class Project:
    name: str
    sessions: List[Session] = field(default_factory=list)


# ──────────────────────────────────────────────────────────────
# Discovery helpers
# ──────────────────────────────────────────────────────────────

def _md5_hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def _load_kimi_workdirs() -> Dict[str, str]:
    """Load kimi.json work_dirs and build hash→path mapping."""
    kimi_json = Path.home() / ".kimi" / "kimi.json"
    mapping = {}
    if kimi_json.exists():
        try:
            data = json.loads(kimi_json.read_text())
            for wd in data.get("work_dirs", []):
                path = wd.get("path", "")
                if path:
                    mapping[_md5_hash(path)] = path
        except Exception:
            pass
    return mapping


def _extract_kimi_code_timestamp(wire_path: Path) -> Optional[datetime]:
    """Get first timestamp from wire.jsonl."""
    if not wire_path.exists():
        return None
    try:
        with open(wire_path) as f:
            for line in f:
                obj = json.loads(line)
                ts = obj.get("time") or obj.get("timestamp") or obj.get("created_at")
                if ts:
                    return datetime.fromtimestamp(ts / 1000)
    except Exception:
        pass
    return None


def _extract_kimi_og_timestamp(state_path: Path) -> Optional[datetime]:
    """Get createdAt from state.json."""
    if not state_path.exists():
        return None
    try:
        data = json.loads(state_path.read_text())
        created = data.get("createdAt") or data.get("created_at")
        if created:
            if isinstance(created, (int, float)):
                return datetime.fromtimestamp(created)
            elif isinstance(created, str):
                return datetime.fromisoformat(created.replace("Z", "+00:00"))
    except Exception:
        pass
    return None


def _quick_assistant_chars_kimi_code(wire_path: Path) -> int:
    """Fast scan: count assistant text chars without full parse."""
    chars = 0
    try:
        with open(wire_path) as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    t = obj.get("type", "")
                    if t == "context.append_message":
                        if obj.get("message", {}).get("role") == "assistant":
                            for part in obj.get("message", {}).get("content", []):
                                if isinstance(part, dict) and part.get("type") == "text":
                                    chars += len(part.get("text", ""))
                    elif t == "context.append_loop_event":
                        event = obj.get("event", {})
                        if event.get("type") == "content.part":
                            part = event.get("part", {})
                            if part.get("type") == "text":
                                chars += len(part.get("text", ""))
                except Exception:
                    pass
    except Exception:
        pass
    return chars


def _quick_assistant_chars_kimi_og(context_path: Path) -> int:
    """Fast scan of context.jsonl for assistant text."""
    chars = 0
    try:
        with open(context_path) as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    if obj.get("role") == "assistant":
                        content = obj.get("content", [])
                        if isinstance(content, list):
                            for part in content:
                                if isinstance(part, dict) and part.get("type") == "text":
                                    chars += len(part.get("text", ""))
                        elif isinstance(content, str):
                            chars += len(content)
                except Exception:
                    pass
    except Exception:
        pass
    return chars


# ──────────────────────────────────────────────────────────────
# Discovery per tool
# ──────────────────────────────────────────────────────────────

def discover_kimi_code_sessions() -> List[Session]:
    """Discover all Kimi-Code sessions grouped by project."""
    sessions = []
    if not KIMI_CODE_ROOT.exists():
        return sessions

    for proj_dir in KIMI_CODE_ROOT.iterdir():
        if not proj_dir.is_dir() or not proj_dir.name.startswith("wd_"):
            continue

        # Extract project name from wd_<name>_<hash>
        parts = proj_dir.name.split("_")
        if len(parts) >= 3:
            project = "_".join(parts[1:-1])  # everything between wd_ and hash
        else:
            project = proj_dir.name

        for sess_dir in proj_dir.iterdir():
            if not sess_dir.is_dir():
                continue
            if not (sess_dir.name.startswith("session_") or sess_dir.name.startswith("ses_")):
                continue

            wire = sess_dir / "agents" / "main" / "wire.jsonl"
            if not wire.exists():
                continue

            ts = _extract_kimi_code_timestamp(wire)
            assistant_chars = _quick_assistant_chars_kimi_code(wire)

            # Load title from state.json
            title = ""
            state_path = sess_dir / "state.json"
            if state_path.exists():
                try:
                    state = json.loads(state_path.read_text())
                    title = state.get("title", "") or ""
                except Exception:
                    pass

            sessions.append(Session(
                tool="kimi-code",
                project=project,
                session_id=sess_dir.name,
                source_path=sess_dir,
                created_at=ts,
                title=title,
                assistant_chars=assistant_chars,
            ))

    return sessions


def discover_kimi_og_sessions() -> List[Session]:
    """Discover all Kimi-OG sessions grouped by project hash."""
    sessions = []
    if not KIMI_OG_ROOT.exists():
        return sessions

    hash_to_path = _load_kimi_workdirs()

    for hash_dir in KIMI_OG_ROOT.iterdir():
        if not hash_dir.is_dir():
            continue

        # Map hash to actual path
        project_path = hash_to_path.get(hash_dir.name, hash_dir.name)
        project = Path(project_path).name or hash_dir.name

        for sess_dir in hash_dir.iterdir():
            if not sess_dir.is_dir():
                continue

            context = sess_dir / "context.jsonl"
            if not context.exists():
                context = sess_dir / "context_1.jsonl"

            if not context.exists():
                continue

            ts = _extract_kimi_og_timestamp(sess_dir / "state.json")
            assistant_chars = _quick_assistant_chars_kimi_og(context)

            # Load title
            title = ""
            state_path = sess_dir / "state.json"
            if state_path.exists():
                try:
                    state = json.loads(state_path.read_text())
                    title = state.get("custom_title", "") or state.get("title", "") or ""
                except Exception:
                    pass

            sessions.append(Session(
                tool="kimi-og",
                project=project,
                session_id=sess_dir.name,
                source_path=sess_dir,
                created_at=ts,
                title=title,
                assistant_chars=assistant_chars,
            ))

    return sessions


def discover_gemini_sessions() -> List[Session]:
    """Discover all Gemini CLI sessions grouped by project."""
    sessions = []
    if not GEMINI_ROOT.exists():
        return sessions

    sources = discover_gemini_sources(GEMINI_ROOT)
    for source_path, src_type in sources:
        # Project is the parent of chats/ or the direct parent
        if source_path.parent.name == "chats":
            project = source_path.parent.parent.name
        else:
            project = source_path.parent.name

        # Extract date from filename if possible
        ts = None
        stem = source_path.stem
        if stem.startswith("session-"):
            date_part = stem.replace("session-", "").split("T")[0]
            try:
                ts = datetime.strptime(date_part, "%Y-%m-%d")
            except ValueError:
                pass

        sessions.append(Session(
            tool="gemini",
            project=project,
            session_id=source_path.name,
            source_path=source_path,
            created_at=ts,
        ))

    return sessions


def discover_claude_sessions() -> List[Session]:
    """Claude has a single JSON export — treat as one 'claude' project."""
    if not CLAUDE_SOURCE.exists():
        return []
    return [Session(
        tool="claude",
        project="claude",
        session_id="conversations",
        source_path=CLAUDE_SOURCE,
    )]


def discover_chatgpt_sessions() -> List[Session]:
    """ChatGPT has a single JSON export — treat as one 'chatgpt' project."""
    if not CHATGPT_SOURCE.exists():
        return []
    return [Session(
        tool="chatgpt",
        project="chatgpt",
        session_id="conversations",
        source_path=CHATGPT_SOURCE,
    )]


def discover_aistudio_sessions() -> List[Session]:
    """Discover AI Studio sessions grouped by account."""
    sessions = []
    if not AISTUDIO_ROOT.exists():
        return sessions

    accounts_dir = AISTUDIO_ROOT / "accounts"
    if not accounts_dir.exists():
        return sessions

    for account_dir in accounts_dir.iterdir():
        if not account_dir.is_dir():
            continue
        chat_logs = account_dir / "chat-logs"
        if not chat_logs.exists():
            continue

        for chat_file in chat_logs.iterdir():
            if chat_file.is_file():
                sessions.append(Session(
                    tool="aistudio",
                    project=account_dir.name,
                    session_id=chat_file.name,
                    source_path=chat_file,
                ))

    return sessions


# ──────────────────────────────────────────────────────────────
# Group by project
# ──────────────────────────────────────────────────────────────

def group_by_project(sessions: List[Session]) -> Dict[str, Project]:
    """Group sessions by project name."""
    projects: Dict[str, Project] = {}
    for sess in sessions:
        if sess.project not in projects:
            projects[sess.project] = Project(name=sess.project)
        projects[sess.project].sessions.append(sess)

    # Sort sessions within each project by created_at
    for proj in projects.values():
        proj.sessions.sort(key=lambda s: s.created_at or datetime.min)

    return projects


# ──────────────────────────────────────────────────────────────
# Export logic
# ──────────────────────────────────────────────────────────────

def export_session(
    sess: Session,
    output_dir: Path,
    min_chars: int = MIN_ASSISTANT_CHARS,
    devwater: bool = False,
) -> Optional[Tuple[Path, Path]]:
    """Export a single session using the appropriate parser.

    Returns (chat_path, think_path) or None if skipped/empty.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        if sess.tool == "kimi-code":
            chat, think = parse_kimi_code(
                sess.source_path,
                output_dir=output_dir,
                min_assistant_chars=min_chars,
            )
            if devwater:
                basename = sess.session_id
                new_chat = output_dir / f"{basename}-chat.md"
                new_think = output_dir / f"{basename}-think.md"
                chat.rename(new_chat)
                think.rename(new_think)
                # remove dated subdir if empty
                dated_dir = chat.parent
                if dated_dir != output_dir:
                    try:
                        dated_dir.rmdir()
                    except OSError:
                        pass
                return new_chat, new_think
            return chat, think

        elif sess.tool == "kimi-og":
            if not is_worth_parsing(sess.source_path):
                return None
            result = parse_kimi_og(str(sess.source_path))
            # kimi_og writes to its own output dir, not our custom one
            # so we need to copy/rename or modify behavior
            # For now, return the paths it created
            chat = result.get("chat")
            think = result.get("think")
            if chat and think:
                return chat, think
            return None

        elif sess.tool == "gemini":
            result = parse_gemini_cli(sess.source_path, output_dir=output_dir)
            if result:
                return result.chat, result.think
            return None

        elif sess.tool == "claude":
            # claude writes flat files to its own output dir
            parse_claude(str(sess.source_path))
            return None  # flat files, no per-session pairing

        elif sess.tool == "chatgpt":
            parse_chatgpt(str(sess.source_path), str(output_dir))
            return None  # flat files

        elif sess.tool == "aistudio":
            result_dir = parse_aistudio(str(sess.source_path))
            if result_dir:
                chat = result_dir / f"{result_dir.name}_chat.md"
                think = result_dir / f"{result_dir.name}_think.md"
                if chat.exists() and think.exists():
                    return chat, think
            return None

    except RuntimeError as e:
        if "SESSION_EMPTY" in str(e):
            return None
        raise
    except Exception as e:
        print(f"  ❌ {sess.tool}/{sess.session_id}: {e}", file=sys.stderr)
        return None

    return None


# ──────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────

def cmd_list(projects: Dict[str, Project], min_chars: int = MIN_ASSISTANT_CHARS) -> None:
    """Print sessions grouped by project."""
    print(f"\n{'='*70}")
    print("PROJECT SESSION LIST")
    print(f"{'='*70}")

    for proj_name in sorted(projects.keys()):
        proj = projects[proj_name]
        real_sessions = [s for s in proj.sessions if s.assistant_chars >= min_chars]
        empty_sessions = [s for s in proj.sessions if s.assistant_chars < min_chars]

        print(f"\n📁 {proj_name}")
        print(f"   Sessions: {len(real_sessions)} real, {len(empty_sessions)} empty")

        for sess in real_sessions:
            date_str = sess.created_at.strftime("%Y-%m-%d %H:%M") if sess.created_at else "unknown"
            title = sess.title[:40] + "..." if len(sess.title) > 40 else sess.title
            print(f"   ├─ [{sess.tool}] {sess.session_id[:20]}... | {date_str} | {sess.assistant_chars:>6} chars | {title}")

        if empty_sessions:
            print(f"   └─ (+{len(empty_sessions)} empty/minimal sessions hidden)")
        else:
            print(f"   └─")


def cmd_export_project(
    project: Project,
    merge: bool = False,
    min_chars: int = MIN_ASSISTANT_CHARS,
    output_root: Path = OUTPUT_ROOT,
    devwater: bool = False,
) -> None:
    """Export all sessions for a single project."""
    if devwater:
        proj_out = Path(f"/home/flintx/{project.name}/devwater-data")
    else:
        proj_out = output_root / project.name
    proj_out.mkdir(parents=True, exist_ok=True)

    print(f"\n📁 Exporting project: {project.name}")
    print(f"   Output: {proj_out}")
    print(f"   Sessions: {len(project.sessions)}")

    chat_files: List[Path] = []
    skipped = 0
    exported = 0

    for sess in project.sessions:
        if devwater and sess.tool != "kimi-code":
            skipped += 1
            continue

        result = export_session(sess, proj_out, min_chars=min_chars, devwater=devwater)
        if result:
            chat, think = result
            chat_files.append(chat)
            exported += 1
            print(f"   ✅ {sess.session_id[:30]}... → {chat.name}")
        else:
            skipped += 1

    print(f"   Exported: {exported}, Skipped: {skipped}")

    if merge and chat_files:
        merged_path = proj_out / f"{project.name}_MERGED.md"
        merge_chat_files(chat_files, merged_path, project)
        print(f"   📝 Merged → {merged_path}")


def merge_chat_files(chat_files: List[Path], merged_path: Path, project: Project) -> None:
    """Concatenate multiple chat files into one merged file."""
    lines = [
        f"# {project.name} — Merged Session Transcripts",
        f"> {len(chat_files)} sessions · merged {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "=" * 60,
        "",
    ]

    for i, chat_file in enumerate(chat_files, 1):
        content = chat_file.read_text(encoding="utf-8")
        lines.append(f"\n{'#'*60}")
        lines.append(f"# SESSION {i}: {chat_file.parent.name}")
        lines.append(f"{'#'*60}\n")
        lines.append(content)
        lines.append("")

    merged_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Project Session Manager — batch export AI chat sessions by project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list                          # Show all projects and sessions
  %(prog)s --export-project doc-dumpster   # Export one project (separate files)
  %(prog)s --export-project doc-dumpster --merge   # Export + merge
  %(prog)s --export-all                    # Export every project
  %(prog)s --export-all --merge            # Export + merge all projects
  %(prog)s --export-project doc-dumpster --devwater   # Backfill to devwater-data
  %(prog)s --export-all --devwater         # Backfill every project to devwater-data
  %(prog)s --export-project doc-dumpster --devwater --since 2026-06-05 --until 2026-06-06
        """,
    )
    parser.add_argument("--list", action="store_true", help="List all projects and sessions")
    parser.add_argument("--export-project", metavar="NAME", help="Export sessions for a specific project")
    parser.add_argument("--export-all", action="store_true", help="Export all projects")
    parser.add_argument("--merge", action="store_true", help="Merge all session chats into one file per project")
    parser.add_argument("--min-chars", type=int, default=MIN_ASSISTANT_CHARS,
                        help=f"Minimum assistant chars to export (default: {MIN_ASSISTANT_CHARS})")
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT,
                        help=f"Output directory for exports (default: {OUTPUT_ROOT})")
    parser.add_argument("--devwater", action="store_true",
                        help="Write Kimi Code sessions directly to each project's devwater-data dir")
    parser.add_argument("--since", metavar="YYYY-MM-DD",
                        help="Only include sessions on or after this date")
    parser.add_argument("--until", metavar="YYYY-MM-DD",
                        help="Only include sessions on or before this date")

    args = parser.parse_args()

    min_chars = args.min_chars

    # Discover all sessions
    print("🔍 Discovering sessions...")
    all_sessions: List[Session] = []
    all_sessions.extend(discover_kimi_code_sessions())
    all_sessions.extend(discover_kimi_og_sessions())
    all_sessions.extend(discover_gemini_sessions())
    all_sessions.extend(discover_claude_sessions())
    all_sessions.extend(discover_chatgpt_sessions())
    all_sessions.extend(discover_aistudio_sessions())

    # Apply date filters
    def _parse_date(s: str):
        return datetime.strptime(s, "%Y-%m-%d")

    if args.since:
        since_dt = _parse_date(args.since)
        all_sessions = [s for s in all_sessions if s.created_at and s.created_at >= since_dt]
    if args.until:
        until_dt = _parse_date(args.until)
        until_dt = until_dt.replace(hour=23, minute=59, second=59)
        all_sessions = [s for s in all_sessions if s.created_at and s.created_at <= until_dt]

    projects = group_by_project(all_sessions)
    print(f"   Found {len(all_sessions)} sessions across {len(projects)} projects")

    if args.list:
        cmd_list(projects, min_chars=min_chars)
        return 0

    if args.export_project:
        if args.export_project not in projects:
            print(f"❌ Project '{args.export_project}' not found.")
            print(f"   Available: {', '.join(sorted(projects.keys()))}")
            return 1
        cmd_export_project(projects[args.export_project], merge=args.merge, min_chars=min_chars, output_root=args.output_root, devwater=args.devwater)
        return 0

    if args.export_all:
        for proj_name in sorted(projects.keys()):
            cmd_export_project(projects[proj_name], merge=args.merge, min_chars=min_chars, output_root=args.output_root, devwater=args.devwater)
        print(f"\n✅ All exports done. Output: {args.output_root}")
        return 0

    # Default: list
    cmd_list(projects, min_chars=min_chars)
    return 0


if __name__ == "__main__":
    sys.exit(main())
