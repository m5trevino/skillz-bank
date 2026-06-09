#!/usr/bin/env python3
"""
Session Transcript Generator
Generates human-readable transcripts from kimi-cli session data.

Outputs:
  - HTML: Interactive split-view transcript with search, buckets, modals
  - MD:  Formatted markdown transcript
  - TXT: Clean raw transcript (for sharing with other bots)
  - code.md: All code blocks extracted and numbered by turn
"""

import argparse
import json
import os
import re
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SESSIONS_ROOT = Path.home() / ".kimi" / "sessions"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class CodeBlock:
    turn_number: int
    block_number: int
    language: str
    code: str


@dataclass
class Turn:
    turn_number: int
    user_message: str
    bot_message: str
    timestamp: Optional[str] = None
    code_blocks: List[CodeBlock] = field(default_factory=list)
    images: List[str] = field(default_factory=list)
    has_code: bool = False
    has_images: bool = False


@dataclass
class SessionData:
    session_id: str
    title: str
    state: dict
    turns: List[Turn]
    uploads: List[str]
    total_words: int = 0
    total_code_blocks: int = 0
    total_images: int = 0


# ---------------------------------------------------------------------------
# Session discovery
# ---------------------------------------------------------------------------

def discover_sessions() -> List[Tuple[Path, dict]]:
    """Scan ~/.kimi/sessions and return list of (session_dir, state) tuples."""
    sessions = []
    if not SESSIONS_ROOT.exists():
        return sessions
    for project_dir in SESSIONS_ROOT.iterdir():
        if not project_dir.is_dir():
            continue
        for session_dir in project_dir.iterdir():
            if not session_dir.is_dir():
                continue
            state_path = session_dir / "state.json"
            if state_path.exists():
                try:
                    state = json.loads(state_path.read_text())
                    sessions.append((session_dir, state))
                except Exception:
                    pass
    # Sort by archived_at desc, then mtime
    def sort_key(item):
        s = item[1]
        return s.get("archived_at", 0) or s.get("wire_mtime", 0) or item[0].stat().st_mtime
    sessions.sort(key=sort_key, reverse=True)
    return sessions


def pick_session(interactive: bool = True) -> Optional[Path]:
    """Let user pick a session, or auto-detect current session."""
    # Try to detect current session from cwd
    cwd = Path.cwd()
    try:
        rel = cwd.relative_to(SESSIONS_ROOT)
        parts = rel.parts
        if len(parts) >= 2:
            candidate = SESSIONS_ROOT / parts[0] / parts[1]
            if (candidate / "state.json").exists():
                return candidate
    except ValueError:
        pass

    sessions = discover_sessions()
    if not sessions:
        print("No sessions found in ~/.kimi/sessions/", file=sys.stderr)
        return None

    if not interactive:
        return sessions[0][0]

    print("\nAvailable sessions:\n")
    for i, (sdir, state) in enumerate(sessions, 1):
        title = state.get("custom_title", "Untitled")
        archived = " [archived]" if state.get("archived") else ""
        mtime = datetime.fromtimestamp(sdir.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        print(f"  {i}. {title}{archived}  ({mtime})")
    print("\n  0. Cancel")
    try:
        choice = int(input("\nPick a session: ").strip())
        if choice == 0:
            return None
        return sessions[choice - 1][0]
    except (ValueError, IndexError):
        print("Invalid selection.", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Context parsing
# ---------------------------------------------------------------------------

def extract_text_from_content(content) -> str:
    """Extract plain text from various content formats."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict):
                t = part.get("type", "")
                if t == "text":
                    parts.append(part.get("text", ""))
                elif t == "think":
                    parts.append(f"[think]\n{part.get('think', '')}\n[/think]")
                elif t in ("tool_calls", "tool_call"):
                    # Skip tool calls in transcript
                    pass
        return "\n".join(parts)
    return str(content)


def extract_code_blocks(text: str, turn_number: int) -> Tuple[str, List[CodeBlock]]:
    """Extract fenced code blocks from text. Returns (text_with_placeholders, blocks)."""
    pattern = r"```(\w*)\n(.*?)\n```"
    blocks = []
    counter = [0]

    def replacer(match):
        lang = match.group(1).strip() or "text"
        code = match.group(2)
        counter[0] += 1
        blocks.append(CodeBlock(
            turn_number=turn_number,
            block_number=counter[0],
            language=lang,
            code=code
        ))
        return f"[CODE_BLOCK_{counter[0]}]"

    cleaned = re.sub(pattern, replacer, text, flags=re.DOTALL)
    return cleaned, blocks


def find_image_references(text: str, uploads: List[str]) -> List[str]:
    """Find references to uploaded images in text."""
    found = []
    for upload in uploads:
        name = Path(upload).name
        if name in text:
            found.append(name)
    return found


def parse_context_files(session_dir: Path) -> List[Turn]:
    """Parse all context.jsonl files in a session directory."""
    # Find all context files
    context_files = []
    for f in session_dir.iterdir():
        if f.name == "context.jsonl":
            context_files.append((float('inf'), f))  # Current context last
        elif re.match(r"context_\d+\.jsonl", f.name):
            num = int(re.search(r"\d+", f.name).group())
            context_files.append((num, f))
    context_files.sort(key=lambda x: x[0])

    # Collect uploads
    uploads_dir = session_dir / "uploads"
    uploads = []
    if uploads_dir.exists():
        uploads = [str(f) for f in uploads_dir.iterdir() if f.is_file()]

    turns = []
    current_user = ""
    current_bot = ""
    turn_number = 0
    current_timestamp = None

    for _, ctx_file in context_files:
        for line in ctx_file.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue

            role = msg.get("role", "")
            content = extract_text_from_content(msg.get("content", ""))
            if role == "user":
                if current_bot:
                    turns.append(finalize_turn(turn_number, current_user, current_bot, current_timestamp, uploads))
                    current_user = ""
                    current_bot = ""
                if not current_user:
                    turn_number += 1
                current_user += ("\n\n" if current_user else "") + content
            elif role == "assistant":
                current_bot += ("\n\n" if current_bot else "") + content
                if not current_timestamp:
                    current_timestamp = msg.get("timestamp")
            elif role == "tool":
                current_bot += f"\n\n[Tool Result]\n{content}"

    # Finalize last turn
    if current_user or current_bot:
        turns.append(finalize_turn(turn_number, current_user, current_bot, current_timestamp, uploads))

    return turns


def finalize_turn(num: int, user: str, bot: str, timestamp, uploads: List[str]) -> Turn:
    bot_cleaned, code_blocks = extract_code_blocks(bot, num)
    images = find_image_references(bot_cleaned, uploads)
    images.extend(find_image_references(user, uploads))
    images = list(set(images))
    return Turn(
        turn_number=num,
        user_message=user.strip(),
        bot_message=bot_cleaned.strip(),
        timestamp=timestamp,
        code_blocks=code_blocks,
        images=images,
        has_code=len(code_blocks) > 0,
        has_images=len(images) > 0
    )


# ---------------------------------------------------------------------------
# Output generators
# ---------------------------------------------------------------------------

def generate_txt(session: SessionData) -> str:
    """Clean raw transcript for sharing with bots."""
    lines = []
    lines.append(f"Session: {session.title}")
    lines.append(f"Generated: {datetime.now().isoformat()}")
    lines.append("=" * 60)
    lines.append("")
    for turn in session.turns:
        lines.append(f"--- Turn {turn.turn_number} ---")
        if turn.timestamp:
            lines.append(f"Time: {turn.timestamp}")
        lines.append("")
        lines.append("USER:")
        lines.append(turn.user_message)
        lines.append("")
        lines.append("ASSISTANT:")
        lines.append(turn.bot_message)
        lines.append("")
    return "\n".join(lines)


def generate_md(session: SessionData) -> str:
    """Formatted markdown transcript."""
    lines = []
    lines.append(f"# Session Transcript: {session.title}")
    lines.append(f"\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
    lines.append(f"\n*Turns: {len(session.turns)} | Words: {session.total_words} | Code blocks: {session.total_code_blocks}*")
    lines.append("\n---\n")
    for turn in session.turns:
        lines.append(f"## Turn {turn.turn_number}")
        if turn.timestamp:
            lines.append(f"*{turn.timestamp}*")
        lines.append("\n### User")
        lines.append(turn.user_message)
        lines.append("\n### Assistant")
        # Restore code blocks in markdown
        bot_text = turn.bot_message
        for cb in turn.code_blocks:
            placeholder = f"[CODE_BLOCK_{cb.block_number}]"
            code_md = f"\n```{cb.language}\n{cb.code}\n```\n"
            bot_text = bot_text.replace(placeholder, code_md, 1)
        lines.append(bot_text)
        lines.append("\n---\n")
    return "\n".join(lines)


def generate_code_md(session: SessionData) -> str:
    """Extract all code blocks into a single file."""
    lines = []
    lines.append(f"# Code Extraction: {session.title}")
    lines.append(f"\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
    lines.append(f"\n*Total code blocks: {session.total_code_blocks}*")
    lines.append("\n---\n")
    for turn in session.turns:
        for cb in turn.code_blocks:
            lines.append(f"## Turn {cb.turn_number} — Block {cb.block_number} ({cb.language})")
            lines.append(f"\n```{cb.language}")
            lines.append(cb.code)
            lines.append("```\n")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# HTML generator
# ---------------------------------------------------------------------------

def escape_js_string(s: str) -> str:
    """Escape a string for embedding in JavaScript."""
    s = s.replace("\\", "\\\\")
    s = s.replace("'", "\\'")
    s = s.replace('"', '\\"')
    s = s.replace("\n", "\\n")
    s = s.replace("\r", "\\r")
    s = s.replace("\t", "\\t")
    return s


def generate_html(session: SessionData) -> str:
    """Generate interactive HTML transcript."""
    # Serialize turn data as JSON for embedding
    turns_json = []
    for turn in session.turns:
        turns_json.append({
            "turn": turn.turn_number,
            "user": turn.user_message,
            "bot": turn.bot_message,
            "timestamp": turn.timestamp or "",
            "hasCode": turn.has_code,
            "hasImages": turn.has_images,
            "codeBlocks": [
                {"blockNum": cb.block_number, "lang": cb.language, "code": cb.code}
                for cb in turn.code_blocks
            ],
            "images": turn.images
        })

    turns_json_str = json.dumps(turns_json, ensure_ascii=False)
    session_id = session.session_id
    title = escape_js_string(session.title)

    # Escape for safe embedding in HTML script tag
    # Replace </script> with <\/script> to prevent breaking out of the script tag
    turns_json_safe = turns_json_str.replace('</script>', '<\\/script>').replace('</SCRIPT>', '<\\/SCRIPT>')

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Session Transcript — {session.title}</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
:root {{
  --bg: #0d0d0d;
  --bg-user: rgba(20, 35, 60, 0.35);
  --bg-bot: rgba(40, 40, 40, 0.35);
  --border: #444;
  --border-light: #333;
  --text: #e0e0e0;
  --text-dim: #888;
  --accent: #4a9eff;
  --accent-hover: #6bb3ff;
  --modal-bg: #1a1a1a;
  --btn-bg: #2a2a2a;
  --btn-hover: #3a3a3a;
  --success: #4caf50;
  --warning: #ff9800;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-size: 14px;
  line-height: 1.6;
  overflow-x: hidden;
}}

/* Header */
#header {{
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(13,13,13,0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border);
}}
#stats-bar {{
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 10px 20px;
  font-size: 13px;
  color: var(--text-dim);
}}
#stats-bar .stat {{ font-weight: 600; color: var(--text); }}
#view-history {{ margin-left: auto; font-size: 12px; color: var(--text-dim); cursor: pointer; }}
#view-history:hover {{ color: var(--accent); }}

/* Controls */
#controls {{
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  padding: 10px 20px;
  border-bottom: 1px solid var(--border-light);
}}
#controls button, #controls select, #controls input {{
  background: var(--btn-bg);
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 6px 12px;
  font-size: 13px;
  cursor: pointer;
}}
#controls button:hover, #controls select:hover {{
  background: var(--btn-hover);
}}
#controls button.active {{
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}}
#search-box {{
  flex: 1;
  min-width: 200px;
  max-width: 400px;
}}
#search-box input {{
  width: 100%;
  padding: 6px 12px;
}}
#search-filters {{
  display: flex;
  gap: 8px;
}}
#search-filters label {{
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-dim);
  cursor: pointer;
}}
#search-filters input[type="checkbox"] {{ accent-color: var(--accent); }}

/* Pagination */
#pagination {{
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}}
#page-info {{ color: var(--text-dim); font-size: 12px; min-width: 80px; text-align: center; }}

/* Turns container */
#turns-container {{
  border-left: 2px solid var(--border);
  border-right: 2px solid var(--border);
  margin: 0 20px;
  min-height: 200px;
}}
.turn {{
  display: grid;
  grid-template-columns: 1fr 70px 1fr;
  border-bottom: 2px solid var(--border);
  position: relative;
}}
.turn.hidden {{ display: none; }}

.user-side, .bot-side {{
  padding: 16px;
  position: relative;
  min-height: 60px;
  word-break: break-word;
  white-space: pre-wrap;
}}
.user-side {{
  background: var(--bg-user);
}}
.bot-side {{
  background: var(--bg-bot);
}}
.turn-divider {{
  border-left: 2px solid var(--border);
  border-right: 2px solid var(--border);
  background: #151515;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 8px 4px;
  gap: 4px;
}}
.turn-number {{
  font-size: 14px;
  font-weight: 700;
  color: var(--accent);
}}
.turn-timestamp {{
  font-size: 10px;
  color: #555;
  text-align: center;
  line-height: 1.2;
}}

.msg-checkbox {{
  position: absolute;
  top: 8px;
  right: 8px;
  width: 16px;
  height: 16px;
  accent-color: var(--accent);
  cursor: pointer;
  z-index: 5;
}}

/* Tag buttons */
.tag-buttons {{
  display: flex;
  gap: 6px;
  margin-top: 10px;
  flex-wrap: wrap;
}}
.tag-btn {{
  background: var(--btn-bg);
  border: 1px solid var(--border);
  color: var(--text-dim);
  padding: 3px 10px;
  border-radius: 4px;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.15s;
}}
.tag-btn:hover {{
  background: var(--btn-hover);
  color: var(--text);
  border-color: var(--accent);
}}
.tag-btn.code {{ border-left: 3px solid var(--accent); }}
.tag-btn.image {{ border-left: 3px solid var(--warning); }}

/* Placeholders */
.code-placeholder {{
  background: rgba(74, 158, 255, 0.1);
  border: 1px dashed var(--accent);
  color: var(--accent);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  display: inline-block;
  margin: 4px 0;
}}

/* Modal */
.modal-overlay {{
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.8);
  z-index: 1000;
  display: none;
  align-items: center;
  justify-content: center;
  padding: 20px;
}}
.modal-overlay.active {{ display: flex; }}
.modal {{
  background: var(--modal-bg);
  border: 1px solid var(--border);
  border-radius: 12px;
  width: 90%;
  max-width: 900px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}}
.modal-header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}}
.modal-title {{ font-size: 16px; font-weight: 600; }}
.modal-close {{
  background: none;
  border: none;
  color: var(--text-dim);
  font-size: 24px;
  cursor: pointer;
}}
.modal-close:hover {{ color: var(--text); }}
.modal-body {{
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}}
.modal-footer {{
  display: flex;
  gap: 10px;
  padding: 12px 20px;
  border-top: 1px solid var(--border);
}}
.modal-footer button {{
  background: var(--btn-bg);
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 8px 16px;
  cursor: pointer;
  font-size: 13px;
}}
.modal-footer button:hover {{ background: var(--btn-hover); }}
.modal-footer button.primary {{ background: var(--accent); border-color: var(--accent); color: #fff; }}
.modal-footer button.primary:hover {{ background: var(--accent-hover); }}

/* Code viewer */
.code-viewer {{
  background: #0d0d0d;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
  font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
  font-size: 13px;
  line-height: 1.5;
  overflow-x: auto;
  white-space: pre;
}}
.code-viewer .kw {{ color: #c678dd; }}
.code-viewer .str {{ color: #98c379; }}
.code-viewer .num {{ color: #d19a66; }}
.code-viewer .comment {{ color: #5c6370; font-style: italic; }}
.code-viewer .fn {{ color: #61afef; }}

/* Bucket sidebar */
#bucket-panel {{
  position: fixed;
  right: -350px;
  top: 0;
  bottom: 0;
  width: 320px;
  background: var(--modal-bg);
  border-left: 1px solid var(--border);
  z-index: 200;
  transition: right 0.3s ease;
  display: flex;
  flex-direction: column;
}}
#bucket-panel.open {{ right: 0; }}
#bucket-panel-header {{
  padding: 16px;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}}
#bucket-panel-body {{
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}}
.bucket-section {{
  margin-bottom: 16px;
}}
.bucket-section-title {{
  font-size: 12px;
  text-transform: uppercase;
  color: var(--text-dim);
  margin-bottom: 8px;
  letter-spacing: 0.5px;
}}
.bucket-item {{
  background: var(--btn-bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 8px 10px;
  font-size: 12px;
  margin-bottom: 6px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}}
.bucket-item button {{
  background: none;
  border: none;
  color: var(--text-dim);
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
}}
.bucket-item button:hover {{ color: #ff4444; }}

/* Floating buttons */
#float-actions {{
  position: fixed;
  bottom: 20px;
  right: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  z-index: 150;
}}
.float-btn {{
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--btn-bg);
  border: 1px solid var(--border);
  color: var(--text);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 20px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.4);
  transition: all 0.2s;
}}
.float-btn:hover {{ background: var(--accent); color: #fff; border-color: var(--accent); transform: scale(1.05); }}

/* Selected state */
.user-side.selected, .bot-side.selected {{
  outline: 2px solid var(--accent);
  outline-offset: -2px;
}}

/* History panel */
#history-panel {{
  position: fixed;
  top: 60px;
  right: 20px;
  background: var(--modal-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px;
  font-size: 12px;
  color: var(--text-dim);
  z-index: 90;
  display: none;
  max-width: 280px;
}}
#history-panel.open {{ display: block; }}
#history-panel h4 {{ color: var(--text); margin-bottom: 8px; font-size: 13px; }}
#history-panel ul {{ list-style: none; }}
#history-panel li {{ padding: 2px 0; }}

/* No results */
#no-results {{
  text-align: center;
  padding: 60px 20px;
  color: var(--text-dim);
  display: none;
}}
#no-results.active {{ display: block; }}

/* Scrollbar */
::-webkit-scrollbar {{ width: 8px; }}
::-webkit-scrollbar-track {{ background: var(--bg); }}
::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 4px; }}
::-webkit-scrollbar-thumb:hover {{ background: #555; }}

/* Mobile */
@media (max-width: 768px) {{
  #turns-container {{ margin: 0 8px; }}
  .turn {{ grid-template-columns: 1fr; }}
  .turn-divider {{
    order: -1;
    flex-direction: row;
    border-left: none;
    border-right: none;
    border-bottom: 2px solid var(--border);
    padding: 6px 12px;
    justify-content: flex-start;
    gap: 12px;
  }}
  .user-side {{ border-right: none; border-bottom: 1px solid var(--border-light); }}
}}

/* Bubble View */
#bubble-container {{ display: none; padding: 20px; max-width: 900px; margin: 0 auto; }}
#bubble-container.active {{ display: block; }}
#turns-container.hidden {{ display: none; }}

.bubble-msg {{ max-width: 80%; margin-bottom: 16px; padding: 14px 18px; border-radius: 20px; position: relative; word-break: break-word; white-space: pre-wrap; font-size: 14px; line-height: 1.6; }}
.bubble-msg.user {{ margin-right: auto; margin-left: 0; background: var(--bg-user); border-bottom-left-radius: 4px; color: var(--text); }}
.bubble-msg.bot {{ margin-left: auto; margin-right: 0; background: var(--bg-bot); border-bottom-right-radius: 4px; color: var(--text); }}

.bubble-msg.user::before {{ content: '{{'; position: absolute; left: -18px; top: 50%; transform: translateY(-50%); font-size: 28px; color: var(--accent); opacity: 0.25; font-weight: 300; font-family: Georgia, serif; }}
.bubble-msg.bot::after {{ content: '}}'; position: absolute; right: -18px; top: 50%; transform: translateY(-50%); font-size: 28px; color: var(--accent); opacity: 0.25; font-weight: 300; font-family: Georgia, serif; }}

.bubble-meta {{ font-size: 11px; color: var(--text-dim); margin-bottom: 4px; display: flex; justify-content: space-between; align-items: center; }}
.bubble-meta .turn-num {{ font-weight: 700; color: var(--accent); }}
.bubble-content {{ position: relative; }}
.bubble-checkbox {{ margin-left: 8px; accent-color: var(--accent); cursor: pointer; }}

.bubble-tag-buttons {{ display: flex; gap: 6px; margin-top: 10px; flex-wrap: wrap; }}

@media (max-width: 768px) {{
  .bubble-msg {{ max-width: 92%; }}
  .bubble-msg.user::before {{ display: none; }}
  .bubble-msg.bot::after {{ display: none; }}
}}
</style>
</head>
<body>

<div id="header">
  <div id="stats-bar">
    <span><span class="stat" id="stat-title">{session.title}</span></span>
    <span>Turns: <span class="stat" id="stat-turns">{len(session.turns)}</span></span>
    <span>Words: <span class="stat" id="stat-words">{session.total_words}</span></span>
    <span>Code: <span class="stat" id="stat-code">{session.total_code_blocks}</span></span>
    <span>Images: <span class="stat" id="stat-images">{session.total_images}</span></span>
    <span id="view-history" onclick="toggleHistory()">View History</span>
  </div>
  <div id="controls">
    <div id="search-box">
      <input type="text" id="search-input" placeholder="Search... (regex supported)" onkeyup="handleSearch(event)">
    </div>
    <div id="search-filters">
      <label><input type="checkbox" id="filter-user" checked onchange="doSearch()"> User</label>
      <label><input type="checkbox" id="filter-bot" checked onchange="doSearch()"> Bot</label>
      <label><input type="checkbox" id="filter-code" onchange="doSearch()"> Code</label>
      <label><input type="checkbox" id="filter-regex" onchange="doSearch()"> Regex</label>
    </div>
    <button id="btn-user" onclick="setFilter('user')">User Only</button>
    <button id="btn-bot" onclick="setFilter('bot')">Bot Only</button>
    <button id="btn-both" class="active" onclick="setFilter('both')">Both</button>
    <button id="btn-view-split" class="active" onclick="setViewMode('split')">Split</button>
    <button id="btn-view-bubble" onclick="setViewMode('bubble')">Bubble</button>
    <select id="page-size" onchange="setPageSize()">
      <option value="10">10 / page</option>
      <option value="25" selected>25 / page</option>
      <option value="50">50 / page</option>
      <option value="100">100 / page</option>
      <option value="999999">All</option>
    </select>
    <div id="pagination">
      <button onclick="prevPage()">&larr;</button>
      <span id="page-info">1 / 1</span>
      <button onclick="nextPage()">&rarr;</button>
    </div>
    <input type="text" id="jump-input" placeholder="Go to #" style="width:70px" onkeyup="handleJump(event)">
    <button onclick="openBuckets()">Buckets</button>
  </div>
</div>

<div id="no-results">
  <h2>No results</h2>
  <p>Try adjusting your search or filters.</p>
</div>

<div id="turns-container"></div>
<div id="bubble-container"></div>

<div id="history-panel">
  <h4>View History</h4>
  <ul id="history-list"></ul>
</div>

<div id="bucket-panel">
  <div id="bucket-panel-header">
    <span style="font-weight:600;">Buckets</span>
    <button class="modal-close" onclick="closeBuckets()">&times;</button>
  </div>
  <div id="bucket-panel-body">
    <div class="bucket-section">
      <div class="bucket-section-title">Messages</div>
      <div id="bucket-messages"></div>
    </div>
    <div class="bucket-section">
      <div class="bucket-section-title">Code</div>
      <div id="bucket-code"></div>
    </div>
    <div class="bucket-section">
      <div class="bucket-section-title">Images</div>
      <div id="bucket-images"></div>
    </div>
    <div class="bucket-section">
      <div class="bucket-section-title">Custom Buckets</div>
      <div id="bucket-custom"></div>
      <button onclick="createCustomBucket()" style="margin-top:8px;width:100%;">+ New Bucket</button>
    </div>
  </div>
  <div class="modal-footer">
    <button onclick="exportAllBuckets('clipboard')">Copy All</button>
    <button onclick="exportAllBuckets('file')" class="primary">Save All</button>
  </div>
</div>

<div id="float-actions">
  <button class="float-btn" onclick="scrollToBottom()" title="Jump to bottom">&darr;</button>
  <button class="float-btn" onclick="exportSelected('clipboard')" title="Copy selected">&#128203;</button>
  <button class="float-btn" onclick="exportSelected('file')" title="Save selected">&#128190;</button>
</div>

<!-- Code Modal -->
<div id="code-modal" class="modal-overlay" onclick="if(event.target===this)closeCodeModal()">
  <div class="modal">
    <div class="modal-header">
      <span class="modal-title" id="code-modal-title">Code</span>
      <button class="modal-close" onclick="closeCodeModal()">&times;</button>
    </div>
    <div class="modal-body">
      <div style="margin-bottom:12px;">
        <label><input type="checkbox" id="syntax-toggle" onchange="toggleSyntax()"> Syntax Highlight</label>
      </div>
      <div id="code-modal-content" class="code-viewer"></div>
    </div>
    <div class="modal-footer">
      <button onclick="copyModalCode()">Copy</button>
      <button onclick="saveModalCode()">Save</button>
      <button onclick="addCodeToBucket()">Add to Bucket</button>
      <button onclick="closeCodeModal()">Close</button>
    </div>
  </div>
</div>

<!-- Image Modal -->
<div id="image-modal" class="modal-overlay" onclick="if(event.target===this)closeImageModal()">
  <div class="modal">
    <div class="modal-header">
      <span class="modal-title" id="image-modal-title">Image</span>
      <button class="modal-close" onclick="closeImageModal()">&times;</button>
    </div>
    <div class="modal-body" style="text-align:center;">
      <img id="image-modal-img" style="max-width:100%;max-height:70vh;border-radius:8px;" src="" alt="">
    </div>
    <div class="modal-footer">
      <button onclick="addImageToBucket()">Add to Bucket</button>
      <button onclick="saveModalImage()">Save</button>
      <button onclick="closeImageModal()">Close</button>
    </div>
  </div>
</div>

<script type="application/json" id="turns-data">
{turns_json_safe}
</script>
<script>
// ---------------------------------------------------------------------------
// Embedded data
// ---------------------------------------------------------------------------
const SESSION_ID = '{session_id}';
const SESSION_TITLE = '{title}';
const turns = JSON.parse(document.getElementById('turns-data').textContent);

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
let currentPage = 0;
let pageSize = 25;
let filterMode = 'both';
let searchQuery = '';
let searchRegex = null;
let selectedTurns = new Set();
let currentCodeBlock = null;
let currentImage = null;

const buckets = {{
  messages: [],
  code: [],
  images: [],
  custom: {{}}
}};

// Load from localStorage
function loadState() {{
  try {{
    const s = localStorage.getItem('st_selected_' + SESSION_ID);
    if (s) selectedTurns = new Set(JSON.parse(s));
    const b = localStorage.getItem('st_buckets_' + SESSION_ID);
    if (b) {{
      const parsed = JSON.parse(b);
      buckets.messages = parsed.messages || [];
      buckets.code = parsed.code || [];
      buckets.images = parsed.images || [];
      buckets.custom = parsed.custom || {{}};
    }}
  }} catch(e) {{}}
}}
function saveState() {{
  localStorage.setItem('st_selected_' + SESSION_ID, JSON.stringify([...selectedTurns]));
  localStorage.setItem('st_buckets_' + SESSION_ID, JSON.stringify(buckets));
}}

// ---------------------------------------------------------------------------
// View history
// ---------------------------------------------------------------------------
function logView() {{
  const key = 'st_views';
  let views = JSON.parse(localStorage.getItem(key) || '{{}}');
  views[SESSION_ID] = views[SESSION_ID] || [];
  views[SESSION_ID].push(new Date().toISOString());
  localStorage.setItem(key, JSON.stringify(views));
  updateHistoryPanel();
}}
function updateHistoryPanel() {{
  const views = JSON.parse(localStorage.getItem('st_views') || '{{}}');
  const list = views[SESSION_ID] || [];
  const ul = document.getElementById('history-list');
  ul.innerHTML = list.slice(-20).reverse().map(t => {{
    const d = new Date(t);
    return `<li>${{d.toLocaleDateString()}} ${{d.toLocaleTimeString()}}</li>`;
  }}).join('') || '<li>Never viewed before</li>';
  const last = list[list.length - 2];
  const hist = document.getElementById('view-history');
  if (last) {{
    const d = new Date(last);
    hist.textContent = `Last viewed: ${{d.toLocaleDateString()}} ${{d.toLocaleTimeString()}}`;
  }} else {{
    hist.textContent = 'Never viewed';
  }}
}}
function toggleHistory() {{
  document.getElementById('history-panel').classList.toggle('open');
}}

// ---------------------------------------------------------------------------
// Scroll position
// ---------------------------------------------------------------------------
function saveScroll() {{
  const pos = JSON.parse(localStorage.getItem('st_scroll') || '{{}}');
  pos[SESSION_ID] = window.scrollY;
  localStorage.setItem('st_scroll', JSON.stringify(pos));
}}
function restoreScroll() {{
  try {{
    const pos = JSON.parse(localStorage.getItem('st_scroll') || '{{}}');
    if (pos[SESSION_ID] !== undefined) {{
      window.scrollTo(0, pos[SESSION_ID]);
    }}
  }} catch(e) {{}}
}}
window.addEventListener('scroll', saveScroll, {{passive: true}});

// ---------------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------------
function escapeHtml(s) {{
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}}

function syntaxHighlight(code, lang) {{
  code = escapeHtml(code);
  const keywords = '\\b(def|class|return|if|else|elif|for|while|try|except|finally|with|import|from|as|lambda|yield|async|await|function|var|let|const|new|this|typeof|instanceof|undefined|null|true|false)\\b';
  const strings = '("(?:[^"\\\\]|\\\\.)*"|\x27(?:[^\x27\\\\]|\\\\.)*\x27|`(?:[^`\\\\]|\\\\.)*`)';
  const comments = '(#.*$|//.*$|/\\*[\\s\\S]*?\\*/)';
  const numbers = '\\b\\d+(?:\\.\\d+)?\\b';
  const functions = '\\b([a-zA-Z_]\\w*)(?=\\()';
  code = code.replace(new RegExp(comments, 'gm'), '<span class="comment">$&</span>');
  code = code.replace(new RegExp(strings, 'g'), '<span class="str">$&</span>');
  code = code.replace(new RegExp(keywords, 'g'), '<span class="kw">$&</span>');
  code = code.replace(new RegExp(numbers, 'g'), '<span class="num">$&</span>');
  code = code.replace(new RegExp(functions, 'g'), '<span class="fn">$&</span>');
  return code;
}}

function renderTurns() {{
  const container = document.getElementById('turns-container');
  container.innerHTML = '';

  let filtered = turns;
  if (searchQuery) {{
    filtered = turns.filter(t => {{
      const userMatch = document.getElementById('filter-user').checked && searchRegex.test(t.user);
      const botMatch = document.getElementById('filter-bot').checked && searchRegex.test(t.bot);
      const codeMatch = document.getElementById('filter-code').checked && t.codeBlocks.some(cb => searchRegex.test(cb.code));
      return userMatch || botMatch || codeMatch;
    }});
  }}

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  currentPage = Math.min(currentPage, totalPages - 1);
  const start = currentPage * pageSize;
  const end = start + pageSize;
  const pageTurns = filtered.slice(start, end);

  document.getElementById('page-info').textContent = `${{currentPage + 1}} / ${{totalPages}}`;
  document.getElementById('no-results').classList.toggle('active', filtered.length === 0);

  for (const turn of pageTurns) {{
    const el = document.createElement('div');
    el.className = 'turn';
    el.dataset.turn = turn.turn;

    const botHtml = marked.parse(botHtml);
    // Replace code placeholders with tag buttons
    botHtml = botHtml.replace(/\[CODE_BLOCK_(\d+)\]/g, (m, num) => {{
      return `<span class="tag-btn code" onclick="openCodeModal(${{turn.turn}}, ${{num}})">Code #${{num}}</span>`;
    }});

    const userChecked = selectedTurns.has('u-' + turn.turn) ? 'checked' : '';
    const botChecked = selectedTurns.has('b-' + turn.turn) ? 'checked' : '';

    const userDisplay = filterMode === 'bot' ? 'none' : 'block';
    const botDisplay = filterMode === 'user' ? 'none' : 'block';

    const ts = turn.timestamp ? new Date(turn.timestamp).toLocaleString() : '';

    const userMd = marked.parse(turn.user);
    const botMd = marked.parse(botHtml);
    el.innerHTML = `
      <div class="user-side" style="display:${{userDisplay}}" data-turn="${{turn.turn}}" data-side="user">
        <input type="checkbox" class="msg-checkbox" ${{userChecked}} onchange="toggleCheckbox(${{turn.turn}}, 'user', this)">
        ${{userMd}}
        ${{turn.images.length ? '<div class="tag-buttons">' + turn.images.map(img => `<span class="tag-btn image" onclick="openImageModal('${{img}}')">${{img.substring(0, 30)}}</span>`).join('') + '</div>' : ''}}
      </div>
      <div class="turn-divider">
        <span class="turn-number">${{turn.turn}}</span>
        <span class="turn-timestamp">${{ts}}</span>
      </div>
      <div class="bot-side" style="display:${{botDisplay}}" data-turn="${{turn.turn}}" data-side="bot">
        <input type="checkbox" class="msg-checkbox" ${{botChecked}} onchange="toggleCheckbox(${{turn.turn}}, 'bot', this)">
        ${{botMd}}
        ${{turn.codeBlocks.length && !botHtml.includes('Code #') ? '<div class="tag-buttons">' + turn.codeBlocks.map(cb => `<span class="tag-btn code" onclick="openCodeModal(${{turn.turn}}, ${{cb.blockNum}})">Code #${{cb.blockNum}}</span>`).join('') + '</div>' : ''}}
      </div>
    `;
    container.appendChild(el);
  }}
}}

function toggleCheckbox(turn, side, cb) {{
  const key = side + '-' + turn;
  if (cb.checked) selectedTurns.add(key);
  else selectedTurns.delete(key);
  saveState();
}}

// ---------------------------------------------------------------------------
// View Mode Switching
// ---------------------------------------------------------------------------
let viewMode = 'split';

function setViewMode(mode) {{
  viewMode = mode;
  document.getElementById('btn-view-split').classList.toggle('active', mode === 'split');
  document.getElementById('btn-view-bubble').classList.toggle('active', mode === 'bubble');
  document.getElementById('turns-container').classList.toggle('hidden', mode === 'bubble');
  document.getElementById('bubble-container').classList.toggle('active', mode === 'bubble');
  if (mode === 'bubble') renderBubbleTurns();
  else renderTurns();
}}

// ---------------------------------------------------------------------------
// Bubble View Rendering
// ---------------------------------------------------------------------------
function renderBubbleTurns() {{
  const container = document.getElementById('bubble-container');
  container.innerHTML = '';

  let filtered = turns;
  if (searchQuery) {{
    filtered = turns.filter(t => {{
      const userMatch = document.getElementById('filter-user').checked && searchRegex.test(t.user);
      const botMatch = document.getElementById('filter-bot').checked && searchRegex.test(t.bot);
      const codeMatch = document.getElementById('filter-code').checked && t.codeBlocks.some(cb => searchRegex.test(cb.code));
      return userMatch || botMatch || codeMatch;
    }});
  }}

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  currentPage = Math.min(currentPage, totalPages - 1);
  const start = currentPage * pageSize;
  const end = start + pageSize;
  const pageTurns = filtered.slice(start, end);

  document.getElementById('page-info').textContent = `${{currentPage + 1}} / ${{totalPages}}`;
  document.getElementById('no-results').classList.toggle('active', filtered.length === 0);

  for (const turn of pageTurns) {{
    const ts = turn.timestamp ? new Date(turn.timestamp).toLocaleString() : '';

    // User message bubble
    if (filterMode !== 'bot') {{
      const userEl = document.createElement('div');
      userEl.className = 'bubble-msg user';
      userEl.dataset.turn = turn.turn;
      userEl.dataset.side = 'user';

      const userHtml = marked.parse(turn.user);
      if (turn.images.length) {{
        userHtml += '<div class="bubble-tag-buttons">' + turn.images.map(img => `<span class="tag-btn image" onclick="openImageModal('${{img}}')">${{img.substring(0, 30)}}</span>`).join('') + '</div>';
      }}

      const userChecked = selectedTurns.has('u-' + turn.turn) ? 'checked' : '';

      userEl.innerHTML = `
        <div class="bubble-meta">
          <span class="turn-num">Turn ${{turn.turn}} — You</span>
          <span>${{ts}} <input type="checkbox" class="bubble-checkbox" ${{userChecked}} onchange="toggleCheckbox(${{turn.turn}}, 'user', this)"></span>
        </div>
        <div class="bubble-content">${{userHtml}}</div>
      `;
      container.appendChild(userEl);
    }}

    // Bot message bubble
    if (filterMode !== 'user') {{
      const botEl = document.createElement('div');
      botEl.className = 'bubble-msg bot';
      botEl.dataset.turn = turn.turn;
      botEl.dataset.side = 'bot';

      const botHtml = marked.parse(botHtml);
      botHtml = botHtml.replace(/\[CODE_BLOCK_(\d+)\]/g, (m, num) => {{
        return `<span class="tag-btn code" onclick="openCodeModal(${{turn.turn}}, ${{num}})">Code #${{num}}</span>`;
      }});

      if (turn.codeBlocks.length && !botHtml.includes('Code #')) {{
        botHtml += '<div class="bubble-tag-buttons">' + turn.codeBlocks.map(cb => `<span class="tag-btn code" onclick="openCodeModal(${{turn.turn}}, ${{cb.blockNum}})">Code #${{cb.blockNum}}</span>`).join('') + '</div>';
      }}

      const botChecked = selectedTurns.has('b-' + turn.turn) ? 'checked' : '';

      botEl.innerHTML = `
        <div class="bubble-meta">
          <span class="turn-num">Turn ${{turn.turn}} — Kimi</span>
          <span>${{ts}} <input type="checkbox" class="bubble-checkbox" ${{botChecked}} onchange="toggleCheckbox(${{turn.turn}}, 'bot', this)"></span>
        </div>
        <div class="bubble-content">${{botMd}}</div>
      `;
      container.appendChild(botEl);
    }}
  }}
}}

// ---------------------------------------------------------------------------
// Pagination & Filters
// ---------------------------------------------------------------------------
function setPageSize() {{
  pageSize = parseInt(document.getElementById('page-size').value);
  currentPage = 0;
  if (viewMode === 'bubble') renderBubbleTurns();
  else renderTurns();
}}
function prevPage() {{
  if (currentPage > 0) {{ currentPage--; if (viewMode === 'bubble') renderBubbleTurns(); else renderTurns(); }}
}}
function nextPage() {{
  const total = Math.ceil(turns.length / pageSize);
  if (currentPage < total - 1) {{ currentPage++; if (viewMode === 'bubble') renderBubbleTurns(); else renderTurns(); }}
}}
function setFilter(mode) {{
  filterMode = mode;
  document.getElementById('btn-user').classList.toggle('active', mode === 'user');
  document.getElementById('btn-bot').classList.toggle('active', mode === 'bot');
  document.getElementById('btn-both').classList.toggle('active', mode === 'both');
  if (viewMode === 'bubble') renderBubbleTurns();
  else renderTurns();
}}
function handleJump(e) {{
  if (e.key === 'Enter') {{
    const num = parseInt(e.target.value);
    if (num && num > 0 && num <= turns.length) {{
      const idx = turns.findIndex(t => t.turn === num);
      if (idx >= 0) {{
        currentPage = Math.floor(idx / pageSize);
        renderTurns();
        setTimeout(() => {{
          const el = document.querySelector(`.turn[data-turn="${{num}}"]`);
          if (el) el.scrollIntoView({{behavior: 'smooth', block: 'center'}});
        }}, 50);
      }}
    }}
  }}
}}
function scrollToBottom() {{
  window.scrollTo({{top: document.body.scrollHeight, behavior: 'smooth'}});
}}

// ---------------------------------------------------------------------------
// Search
// ---------------------------------------------------------------------------
function handleSearch(e) {{
  if (e.key === 'Enter') doSearch();
}}
function doSearch() {{
  const q = document.getElementById('search-input').value.trim();
  searchQuery = q;
  if (!q) {{
    searchRegex = null;
    currentPage = 0;
    if (viewMode === 'bubble') renderBubbleTurns();
    else renderTurns();
    return;
  }}
  try {{
    const flags = document.getElementById('filter-regex').checked ? 'i' : 'gi';
    const pattern = document.getElementById('filter-regex').checked ? q : q.replace(/[.*+?^${{}}()|[\]\\]/g, '\\$&');
    searchRegex = new RegExp(pattern, flags);
  }} catch(e) {{
    searchRegex = new RegExp(q.replace(/[.*+?^${{}}()|[\]\\]/g, '\\$&'), 'gi');
  }}
  currentPage = 0;
  if (viewMode === 'bubble') renderBubbleTurns();
  else renderTurns();
}}

// ---------------------------------------------------------------------------
// Code Modal
// ---------------------------------------------------------------------------
function openCodeModal(turnNum, blockNum) {{
  const turn = turns.find(t => t.turn === turnNum);
  if (!turn) return;
  const cb = turn.codeBlocks.find(c => c.blockNum === blockNum);
  if (!cb) return;
  currentCodeBlock = {{turn: turnNum, block: blockNum, lang: cb.lang, code: cb.code}};
  document.getElementById('code-modal-title').textContent = `Turn ${{turnNum}} — Code #${{blockNum}} (${{cb.lang}})`;
  const highlighted = document.getElementById('syntax-toggle').checked ? syntaxHighlight(cb.code, cb.lang) : escapeHtml(cb.code);
  document.getElementById('code-modal-content').innerHTML = highlighted;
  document.getElementById('code-modal').classList.add('active');
}}
function closeCodeModal() {{
  document.getElementById('code-modal').classList.remove('active');
  currentCodeBlock = null;
}}
function toggleSyntax() {{
  if (currentCodeBlock) {{
    const cb = currentCodeBlock;
    const el = document.getElementById('code-modal-content');
    el.innerHTML = document.getElementById('syntax-toggle').checked ? syntaxHighlight(cb.code, cb.lang) : escapeHtml(cb.code);
  }}
}}
function copyModalCode() {{
  if (!currentCodeBlock) return;
  navigator.clipboard.writeText(currentCodeBlock.code).then(() => alert('Copied!'));
}}
function saveModalCode() {{
  if (!currentCodeBlock) return;
  const blob = new Blob([currentCodeBlock.code], {{type: 'text/plain'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `turn_${{currentCodeBlock.turn}}_code_${{currentCodeBlock.block}}.${{currentCodeBlock.lang || 'txt'}}`;
  a.click();
}}
function addCodeToBucket() {{
  if (!currentCodeBlock) return;
  buckets.code.push(currentCodeBlock);
  saveState();
  renderBuckets();
  alert('Added to code bucket!');
}}

// ---------------------------------------------------------------------------
// Image Modal
// ---------------------------------------------------------------------------
function openImageModal(filename) {{
  currentImage = filename;
  document.getElementById('image-modal-title').textContent = filename;
  document.getElementById('image-modal-img').src = './uploads/' + filename;
  document.getElementById('image-modal').classList.add('active');
}}
function closeImageModal() {{
  document.getElementById('image-modal').classList.remove('active');
  currentImage = null;
}}
function saveModalImage() {{
  if (!currentImage) return;
  const a = document.createElement('a');
  a.href = './uploads/' + currentImage;
  a.download = currentImage;
  a.click();
}}
function addImageToBucket() {{
  if (!currentImage) return;
  buckets.images.push(currentImage);
  saveState();
  renderBuckets();
  alert('Added to image bucket!');
}}

// ---------------------------------------------------------------------------
// Buckets
// ---------------------------------------------------------------------------
function openBuckets() {{
  renderBuckets();
  document.getElementById('bucket-panel').classList.add('open');
}}
function closeBuckets() {{
  document.getElementById('bucket-panel').classList.remove('open');
}}
function renderBuckets() {{
  const msgEl = document.getElementById('bucket-messages');
  msgEl.innerHTML = buckets.messages.map((m, i) => `<div class="bucket-item"><span>Turn ${{m.turn}} (${{m.side}})</span><button onclick="removeFromBucket('messages', ${{i}})">&times;</button></div>`).join('') || '<div style="color:#555;font-size:12px;">Empty</div>';

  const codeEl = document.getElementById('bucket-code');
  codeEl.innerHTML = buckets.code.map((c, i) => `<div class="bucket-item"><span>Turn ${{c.turn}} #${{c.block}} (${{c.lang}})</span><button onclick="removeFromBucket('code', ${{i}})">&times;</button></div>`).join('') || '<div style="color:#555;font-size:12px;">Empty</div>';

  const imgEl = document.getElementById('bucket-images');
  imgEl.innerHTML = buckets.images.map((img, i) => `<div class="bucket-item"><span>${{img}}</span><button onclick="removeFromBucket('images', ${{i}})">&times;</button></div>`).join('') || '<div style="color:#555;font-size:12px;">Empty</div>';

  const customEl = document.getElementById('bucket-custom');
  let customHtml = '';
  for (const [name, items] of Object.entries(buckets.custom)) {{
    customHtml += `<div style="margin-bottom:8px;"><div style="font-size:11px;color:#888;margin-bottom:4px;">${{name}}</div>${{items.map((it, i) => `<div class="bucket-item"><span>${{typeof it === 'string' ? it : 'Turn ' + it.turn}}</span><button onclick="removeFromCustom('${{name}}', ${{i}})">&times;</button></div>`).join('')}}</div>`;
  }}
  customEl.innerHTML = customHtml || '<div style="color:#555;font-size:12px;">No custom buckets</div>';
}}
function removeFromBucket(type, idx) {{
  buckets[type].splice(idx, 1);
  saveState();
  renderBuckets();
}}
function removeFromCustom(name, idx) {{
  buckets.custom[name].splice(idx, 1);
  if (buckets.custom[name].length === 0) delete buckets.custom[name];
  saveState();
  renderBuckets();
}}
function createCustomBucket() {{
  const name = prompt('Bucket name:');
  if (name && !buckets.custom[name]) {{
    buckets.custom[name] = [];
    saveState();
    renderBuckets();
  }}
}}
function exportAllBuckets(mode) {{
  const lines = [];
  lines.push('# Bucket Export — ' + SESSION_TITLE);
  lines.push('');
  if (buckets.messages.length) {{
    lines.push('## Messages');
    for (const m of buckets.messages) {{
      const turn = turns.find(t => t.turn === m.turn);
      const text = m.side === 'user' ? (turn?.user || '') : (turn?.bot || '');
      lines.push(`### Turn ${{m.turn}} (${{m.side}})`);
      lines.push(text);
      lines.push('');
    }}
  }}
  if (buckets.code.length) {{
    lines.push('## Code');
    for (const c of buckets.code) {{
      lines.push(`### Turn ${{c.turn}} — Block ${{c.block}} (${{c.lang}})`);
      lines.push('```' + c.lang);
      lines.push(c.code);
      lines.push('```');
      lines.push('');
    }}
  }}
  if (buckets.images.length) {{
    lines.push('## Images');
    for (const img of buckets.images) lines.push('- ' + img);
    lines.push('');
  }}
  for (const [name, items] of Object.entries(buckets.custom)) {{
    lines.push('## ' + name);
    for (const it of items) {{
      if (typeof it === 'string') lines.push('- ' + it);
      else lines.push(`- Turn ${{it.turn}} #${{it.block || ''}}`);
    }}
    lines.push('');
  }}
  const text = lines.join('\\n');
  if (mode === 'clipboard') {{
    navigator.clipboard.writeText(text).then(() => alert('Copied to clipboard!'));
  }} else {{
    const blob = new Blob([text], {{type: 'text/markdown'}});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'buckets_' + SESSION_ID.slice(0,8) + '.md';
    a.click();
  }}
}}

// ---------------------------------------------------------------------------
// Export selected
// ---------------------------------------------------------------------------
function exportSelected(mode) {{
  if (selectedTurns.size === 0) {{ alert('No messages selected. Use checkboxes.'); return; }}
  const lines = [];
  lines.push('# Selected Messages — ' + SESSION_TITLE);
  lines.push('');
  const sorted = [...selectedTurns].sort();
  for (const key of sorted) {{
    const [side, turnStr] = key.split('-');
    const turn = turns.find(t => t.turn === parseInt(turnStr));
    if (!turn) continue;
    lines.push(`## Turn ${{turn.turn}} (${{side}})`);
    const text = side === 'user' ? turn.user : turn.bot;
    lines.push(text);
    lines.push('');
  }}
  const text = lines.join('\\n');
  if (mode === 'clipboard') {{
    navigator.clipboard.writeText(text).then(() => alert('Copied ' + selectedTurns.size + ' messages!'));
  }} else {{
    const blob = new Blob([text], {{type: 'text/markdown'}});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'selected_' + SESSION_ID.slice(0,8) + '.md';
    a.click();
  }}
}}

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------
loadState();
logView();
if (viewMode === 'bubble') renderBubbleTurns();
else renderTurns();
restoreScroll();
</script>

</body>
</html>
'''
    return html


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def load_session(session_dir: Path) -> Optional[SessionData]:
    """Load all session data from a session directory."""
    state_path = session_dir / "state.json"
    if not state_path.exists():
        print(f"No state.json in {session_dir}", file=sys.stderr)
        return None

    state = json.loads(state_path.read_text())
    title = state.get("custom_title") or state.get("title", "Untitled Session")
    session_id = session_dir.name

    turns = parse_context_files(session_dir)

    uploads_dir = session_dir / "uploads"
    uploads = [f.name for f in uploads_dir.iterdir()] if uploads_dir.exists() else []

    total_words = sum(len(t.user_message.split()) + len(t.bot_message.split()) for t in turns)
    total_code = sum(len(t.code_blocks) for t in turns)
    total_images = sum(len(t.images) for t in turns)

    return SessionData(
        session_id=session_id,
        title=title,
        state=state,
        turns=turns,
        uploads=uploads,
        total_words=total_words,
        total_code_blocks=total_code,
        total_images=total_images
    )


def main():
    parser = argparse.ArgumentParser(description="Generate human-readable transcripts from kimi sessions")
    parser.add_argument("--session-dir", help="Path to specific session directory")
    parser.add_argument("--output-dir", "-o", default=".", help="Output directory")
    parser.add_argument("--format", choices=["html", "md", "txt", "code", "all"], default="all",
                        help="Output format (default: all)")
    parser.add_argument("--no-interactive", action="store_true", help="Use most recent session without prompting")
    args = parser.parse_args()

    # Resolve session directory
    if args.session_dir:
        session_dir = Path(args.session_dir).resolve()
    else:
        session_dir = pick_session(interactive=not args.no_interactive)
        if not session_dir:
            sys.exit(1)

    # Load session
    print(f"Loading session from {session_dir}...")
    session = load_session(session_dir)
    if not session:
        sys.exit(1)

    print(f"Loaded: {session.title}")
    print(f"  Turns: {len(session.turns)}")
    print(f"  Words: {session.total_words}")
    print(f"  Code blocks: {session.total_code_blocks}")
    print(f"  Images: {session.total_images}")

    # Create output dir
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Use session title for filename base
    safe_title = re.sub(r'[^\w\-]+', '_', session.title.lower()).strip('_')[:40] or "session"
    base_name = f"{safe_title}_{session.session_id[:8]}"

    formats_to_generate = ["html", "md", "txt", "code"] if args.format == "all" else [args.format]

    generated = []
    if "html" in formats_to_generate:
        html_path = output_dir / f"{base_name}.html"
        html_path.write_text(generate_html(session))
        generated.append(html_path)
        print(f"  HTML: {html_path}")

    if "md" in formats_to_generate:
        md_path = output_dir / f"{base_name}.md"
        md_path.write_text(generate_md(session))
        generated.append(md_path)
        print(f"  MD:   {md_path}")

    if "txt" in formats_to_generate:
        txt_path = output_dir / f"{base_name}.txt"
        txt_path.write_text(generate_txt(session))
        generated.append(txt_path)
        print(f"  TXT:  {txt_path}")

    if "code" in formats_to_generate:
        code_path = output_dir / f"{base_name}_code.md"
        code_path.write_text(generate_code_md(session))
        generated.append(code_path)
        print(f"  CODE: {code_path}")

    print(f"\nDone. {len(generated)} file(s) generated in {output_dir}")


if __name__ == "__main__":
    main()