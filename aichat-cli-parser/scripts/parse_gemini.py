#!/usr/bin/env python3
"""
Gemini CLI JSONL Chat Log Parser
Parses Gemini CLI session JSONL files into structured markdown output.

Usage:
    python3 parse_gemini.py <session-*.jsonl> [--outdir <dir>]

Default output: ~/save-aichats.com-gemini/<session_name>/
"""

import json
import re
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# ──────────────────────────────────────────────────────────────
# Divider characters
# ──────────────────────────────────────────────────────────────
USER_DIV = "▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰"
BOT_DIV = "▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄"
CODE_DIV = "⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘"
IMAGE_DIV = "⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘"

# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

def load_gemini_file(path: Path) -> List[Dict]:
    """
    Load a Gemini session file. Auto-detects format:
      - JSONL: one JSON object per line (current CLI format)
      - JSON:  pretty-printed with 'messages' array (older ghost staging format)
    """
    if not path.exists():
        return []

    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []

    # Try JSONL first (most common for current CLI)
    entries = []
    for line in text.splitlines():
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    # If JSONL yielded nothing or only session headers, try wrapped JSON format
    if len(entries) <= 1:
        try:
            data = json.loads(text)
            if isinstance(data, dict) and "messages" in data:
                return data["messages"]
        except json.JSONDecodeError:
            pass

    return entries


def extract_user_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = []
        for part in content:
            if isinstance(part, dict):
                texts.append(part.get("text", ""))
            elif isinstance(part, str):
                texts.append(part)
        return "\n".join(texts)
    return ""


def extract_gemini_text(entry: Dict) -> str:
    content = entry.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(str(c) for c in content)
    return ""


def extract_thoughts(entry: Dict) -> str:
    thoughts = entry.get("thoughts", [])
    if not thoughts:
        return ""
    parts = []
    for t in thoughts:
        if isinstance(t, dict):
            subject = t.get("subject", "")
            description = t.get("description", "")
            if subject and description:
                parts.append(f"**{subject}**\n{description}")
            elif description:
                parts.append(description)
            elif subject:
                parts.append(subject)
    return "\n\n".join(parts)


def extract_tool_output(tool_call: Dict) -> str:
    result = tool_call.get("result", [])
    if isinstance(result, list) and result:
        fr = result[0].get("functionResponse", {})
        response = fr.get("response", {})
        if isinstance(response, dict):
            return response.get("output", "")
        elif isinstance(response, str):
            return response
    return ""


def extract_tool_result_display(tool_call: Dict) -> str:
    rd = tool_call.get("resultDisplay")
    if isinstance(rd, str):
        return rd
    if isinstance(rd, list):
        lines = []
        for row in rd:
            if isinstance(row, list):
                row_text = ""
                for cell in row:
                    if isinstance(cell, dict):
                        row_text += cell.get("text", "")
                    elif isinstance(cell, str):
                        row_text += cell
                lines.append(row_text)
            elif isinstance(row, dict):
                lines.append(row.get("text", ""))
            elif isinstance(row, str):
                lines.append(row)
        return "\n".join(lines)
    return ""


CODE_BLOCK_RE = re.compile(r"```(\w*)\n?(.*?)```", re.DOTALL)
CLIPBOARD_RE = re.compile(r"clipboard-[a-f0-9]+\.(?:png|jpg|jpeg|gif)", re.IGNORECASE)
IMAGE_PATH_RE = re.compile(r"(?:/[^/\s]+)+\.(?:png|jpg|jpeg|gif|webp|bmp)", re.IGNORECASE)
ATTACHMENT_RE = re.compile(r"@\s*(/[^\s]+)")


def extract_code_blocks(text: str) -> List[Dict[str, str]]:
    blocks = []
    for lang, code in CODE_BLOCK_RE.findall(text):
        blocks.append({"language": lang or "text", "code": code})
    return blocks


def find_attachments(text: str) -> List[str]:
    attachments = set()
    attachments.update(CLIPBOARD_RE.findall(text))
    attachments.update(IMAGE_PATH_RE.findall(text))
    attachments.update(ATTACHMENT_RE.findall(text))
    return sorted(attachments)


# ──────────────────────────────────────────────────────────────
# Core Parsing
# ──────────────────────────────────────────────────────────────

def parse_gemini_jsonl(entries: List[Dict]) -> List[Dict]:
    sets = []
    current_set = None
    i = 0

    while i < len(entries):
        entry = entries[i]
        entry_type = entry.get("type", "")

        if entry_type in ("", "$set") or "sessionId" in entry:
            i += 1
            continue

        if entry_type == "user":
            text = extract_user_text(entry.get("content", ""))
            if current_set is not None:
                sets.append(current_set)
            current_set = {
                "set_num": len(sets) + 1,
                "user": text,
                "gemini_text": "",
                "thinking": "",
                "tool_calls": [],
                "code_blocks": [],
                "attachments": [],
            }
            i += 1
            continue

        if entry_type == "gemini" and current_set is not None:
            text = extract_gemini_text(entry)
            thinking = extract_thoughts(entry)

            if text:
                if current_set["gemini_text"]:
                    current_set["gemini_text"] += "\n\n" + text
                else:
                    current_set["gemini_text"] = text

            if thinking:
                if current_set["thinking"]:
                    current_set["thinking"] += "\n\n" + thinking
                else:
                    current_set["thinking"] = thinking

            for tc in entry.get("toolCalls", []):
                if isinstance(tc, dict):
                    tool_info = {
                        "name": tc.get("name", "?"),
                        "args": tc.get("args", {}),
                        "description": tc.get("description", ""),
                        "display_name": tc.get("displayName", ""),
                        "status": tc.get("status", ""),
                        "output": extract_tool_output(tc),
                        "result_display": extract_tool_result_display(tc),
                    }
                    current_set["tool_calls"].append(tool_info)

            current_set["code_blocks"].extend(extract_code_blocks(text))
            current_set["attachments"].extend(find_attachments(text))

            for tc in current_set["tool_calls"]:
                current_set["code_blocks"].extend(extract_code_blocks(tc["output"]))
                current_set["attachments"].extend(find_attachments(tc["output"]))

            i += 1
            continue

        if entry_type == "info" and current_set is not None:
            i += 1
            continue

        i += 1

    if current_set is not None:
        sets.append(current_set)

    for s in sets:
        s["attachments"] = list(dict.fromkeys(s["attachments"]))

    return sets


# ──────────────────────────────────────────────────────────────
# Output Writers
# ──────────────────────────────────────────────────────────────

def write_chat_sets(sets: List[Dict], path: Path, source_name: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Gemini Chat Sets\n\n")
        f.write(f"**Source:** `{source_name}`\n")
        f.write(f"**Generated:** {datetime.now().isoformat()}\n")
        f.write(f"**Total Sets:** {len(sets)}\n\n")
        f.write("---\n\n")

        for s in sets:
            f.write(f"{USER_DIV}\n")
            f.write(f"### Set {s['set_num']}\n")
            f.write("### User\n")
            f.write(f"{USER_DIV}\n")
            f.write(f"{s['user']}\n")

            f.write(f"\n{BOT_DIV}\n")
            f.write(f"### Set {s['set_num']}\n")
            f.write("### Gemini\n")
            f.write(f"{BOT_DIV}\n")

            if s["thinking"]:
                f.write("**[Thinking]**\n")
                f.write(f"{s['thinking']}\n")
                f.write("**[/Thinking]**\n\n")

            f.write(f"{s['gemini_text']}\n")

            if s["tool_calls"]:
                f.write("\n**Tools Called:**\n")
                for tc in s["tool_calls"]:
                    f.write(f"- `{tc['name']}` — {tc['display_name'] or tc['description']}\n")
                    if tc["output"]:
                        output = tc["output"]
                        if len(output) > 300:
                            output = output[:300] + "\n... [truncated]\n"
                        f.write(f"  ```\n{output}\n  ```\n")

            f.write(f"{BOT_DIV}\n\n")


def write_code_blocks(sets: List[Dict], path: Path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Code Blocks\n\n")
        f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
        f.write("---\n\n")
        total_blocks = 0
        for s in sets:
            for cb in s["code_blocks"]:
                total_blocks += 1
                lines = cb["code"].strip().splitlines()
                line_count = len(lines)
                lang = cb["language"]
                f.write(f"{CODE_DIV}\n")
                f.write(f"### Code: Set {s['set_num']}\n")
                f.write(f"**Language:** `{lang}`\n")
                f.write(f"**Lines:** {line_count}\n")
                f.write(f"{CODE_DIV}\n\n")
                f.write(f"```{lang}\n")
                f.write(cb["code"])
                if not cb["code"].endswith("\n"):
                    f.write("\n")
                f.write(f"```\n\n")
        f.write(f"\n**Total code blocks extracted:** {total_blocks}\n")


def write_attachments(sets: List[Dict], path: Path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Attachments\n\n")
        f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
        f.write("---\n\n")
        total_attachments = 0
        for s in sets:
            if s["attachments"]:
                f.write(f"{IMAGE_DIV}\n")
                f.write(f"### Set {s['set_num']}\n")
                f.write(f"{IMAGE_DIV}\n\n")
                for att in s["attachments"]:
                    total_attachments += 1
                    f.write(f"- `{att}`\n")
                f.write("\n")
        f.write(f"\n**Total attachments found:** {total_attachments}\n")


def write_thinking(sets: List[Dict], path: Path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Model Thinking\n\n")
        f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
        f.write("---\n\n")
        for s in sets:
            if s["thinking"]:
                f.write(f"{BOT_DIV}\n")
                f.write(f"### Set {s['set_num']}\n")
                f.write(f"{BOT_DIV}\n\n")
                f.write(f"{s['thinking']}\n\n")


def write_tools(sets: List[Dict], path: Path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Tool Calls\n\n")
        f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
        f.write("---\n\n")
        all_tools = []
        for s in sets:
            for tc in s["tool_calls"]:
                all_tools.append({"set": s["set_num"], **tc})
        if not all_tools:
            f.write("*No tool calls recorded.*\n")
            return
        by_name = {}
        for t in all_tools:
            by_name.setdefault(t["name"], []).append(t)
        f.write(f"**Total tool calls:** {len(all_tools)}\n\n")
        for name, calls in sorted(by_name.items()):
            f.write(f"## `{name}`\n")
            f.write(f"**Called {len(calls)} time(s)**\n\n")
            for c in calls:
                f.write(f"- Set {c['set']}\n")
                args = json.dumps(c["args"], indent=2) if c["args"] else "{}"
                if len(args) > 200:
                    args = args[:200] + "..."
                f.write(f"  ```json\n  {args}\n  ```\n")
                if c["output"]:
                    output = c["output"]
                    if len(output) > 200:
                        output = output[:200] + "..."
                    f.write(f"  **Output:**\n  ```\n  {output}\n  ```\n")
            f.write("\n")


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Parse Gemini CLI session JSONL into markdown")
    parser.add_argument("input", help="Path to session-*.jsonl file")
    parser.add_argument("--outdir", "-o", help="Output directory (default: ~/save-aichats.com-gemini/<session_name>)")
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        print(f"❌ File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Determine output directory
    if args.outdir:
        output_dir = Path(args.outdir).expanduser().resolve()
    else:
        default_base = Path.home() / "save-aichats.com-gemini"
        session_name = input_path.stem
        output_dir = default_base / session_name

    output_dir.mkdir(parents=True, exist_ok=True)

    # Load and parse
    entries = load_gemini_file(input_path)
    print(f"📥 Loaded {len(entries)} entries from {input_path.name}")

    sets = parse_gemini_jsonl(entries)
    print(f"🧩 Parsed {len(sets)} conversation sets")

    # Write outputs
    write_chat_sets(sets, output_dir / "CHAT_SETS.md", input_path.name)
    write_code_blocks(sets, output_dir / "CODE_BLOCKS.md")
    write_attachments(sets, output_dir / "ATTACHMENTS.md")
    write_thinking(sets, output_dir / "THINKING.md")
    write_tools(sets, output_dir / "TOOLS.md")

    total_code = sum(len(s["code_blocks"]) for s in sets)
    total_attachments = sum(len(s["attachments"]) for s in sets)
    total_tools = sum(len(s["tool_calls"]) for s in sets)

    print(f"\n✅ Output written to: {output_dir}")
    print(f"   CHAT_SETS.md    — {len(sets)} conversation sets")
    print(f"   CODE_BLOCKS.md  — {total_code} code blocks")
    print(f"   ATTACHMENTS.md  — {total_attachments} attachments")
    print(f"   THINKING.md     — model reasoning blocks")
    print(f"   TOOLS.md        — {total_tools} tool calls")


if __name__ == "__main__":
    main()
