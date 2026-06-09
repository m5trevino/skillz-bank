#!/usr/bin/env python3
"""
Kimi CLI Chat Log Parser
Parses Kimi CLI session files into structured markdown output.

Usage:
    python3 parse_kimi.py <session_dir> [--outdir <dir>]

A Kimi session directory contains:
    context_1.jsonl   : Primary chat history (user/assistant/tool messages)
    wire.jsonl        : Protocol-level details (thinking blocks, tool calls)

Optional global dirs (auto-detected):
    ~/.kimi/user-history/*.jsonl  : User message history
    ~/.kimi/logs/kimi.*.log       : Application logs

Default output: ~/save-aichats.com-kimi/<session_name>/
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

def load_jsonl(path: Path) -> List[Dict]:
    if not path.exists():
        return []
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries


def extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                texts.append(part.get("text", ""))
            elif isinstance(part, dict) and part.get("type") == "think":
                pass
            elif isinstance(part, str):
                texts.append(part)
        return "\n".join(texts)
    return ""


def extract_thinking(content: Any) -> str:
    if isinstance(content, list):
        thoughts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "think":
                thoughts.append(part.get("think", ""))
        return "\n\n".join(thoughts)
    return ""


def is_system_message(text: str) -> bool:
    return text.strip().startswith("<system>")


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

def parse_context_jsonl(entries: List[Dict]) -> List[Dict]:
    sets = []
    current_set = None
    i = 0

    while i < len(entries):
        entry = entries[i]
        role = entry.get("role", "")

        if role == "user":
            text = entry.get("content", "")
            if isinstance(text, str):
                if is_system_message(text):
                    if current_set is not None:
                        current_set["system_events"].append(text)
                    i += 1
                    continue
                else:
                    if current_set is not None:
                        sets.append(current_set)
                    current_set = {
                        "set_num": len(sets) + 1,
                        "user": text,
                        "assistant": "",
                        "thinking": "",
                        "tool_results": [],
                        "system_events": [],
                        "code_blocks": [],
                        "attachments": [],
                        "tool_calls": [],
                    }
            i += 1
            continue

        if role == "assistant" and current_set is not None:
            content = entry.get("content", [])
            text = extract_text(content)
            thinking = extract_thinking(content)

            if text:
                if current_set["assistant"]:
                    current_set["assistant"] += "\n\n" + text
                else:
                    current_set["assistant"] = text
            if thinking:
                if current_set["thinking"]:
                    current_set["thinking"] += "\n\n" + thinking
                else:
                    current_set["thinking"] = thinking

            for tc in entry.get("tool_calls", []):
                if isinstance(tc, dict):
                    func = tc.get("function", {})
                    current_set["tool_calls"].append({
                        "name": func.get("name", "?"),
                        "arguments": func.get("arguments", ""),
                    })

            current_set["code_blocks"].extend(extract_code_blocks(text))
            current_set["attachments"].extend(find_attachments(text))
            i += 1
            continue

        if role == "tool" and current_set is not None:
            content = entry.get("content", "")
            text = extract_text(content)
            tool_call_id = entry.get("tool_call_id", "")
            if text:
                current_set["tool_results"].append({
                    "tool_call_id": tool_call_id,
                    "text": text,
                })
                current_set["code_blocks"].extend(extract_code_blocks(text))
                current_set["attachments"].extend(find_attachments(text))
            i += 1
            continue

        i += 1

    if current_set is not None:
        sets.append(current_set)

    for s in sets:
        s["attachments"] = list(dict.fromkeys(s["attachments"]))

    return sets


def parse_wire_jsonl(entries: List[Dict]) -> Dict[int, Dict]:
    turns = []
    current_turn = {"thinking": [], "tool_calls": [], "text_parts": []}
    in_turn = False

    for entry in entries:
        msg = entry.get("message", {})
        msg_type = msg.get("type", "")
        payload = msg.get("payload", {})

        if msg_type == "TurnBegin":
            if in_turn:
                turns.append(current_turn)
            current_turn = {"thinking": [], "tool_calls": [], "text_parts": []}
            in_turn = True

        elif msg_type == "ContentPart":
            part_type = payload.get("type", "")
            if part_type == "think":
                current_turn["thinking"].append(payload.get("think", ""))
            elif part_type == "text":
                current_turn["text_parts"].append(payload.get("text", ""))

        elif msg_type == "ToolCall":
            func = payload.get("function", {})
            current_turn["tool_calls"].append({
                "name": func.get("name", "?"),
                "arguments": func.get("arguments", ""),
            })

        elif msg_type == "TurnEnd":
            if in_turn:
                turns.append(current_turn)
            in_turn = False

    wire_data = {}
    for idx, turn in enumerate(turns):
        wire_data[idx] = turn
    return wire_data


# ──────────────────────────────────────────────────────────────
# Output Writers
# ──────────────────────────────────────────────────────────────

def write_chat_sets(sets: List[Dict], path: Path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Kimi Chat Sets\n\n")
        f.write(f"**Generated:** {datetime.now().isoformat()}\n")
        f.write(f"**Total Sets:** {len(sets)}\n\n")
        f.write("---\n\n")

        for s in sets:
            f.write(f"{USER_DIV}\n")
            f.write(f"### Set {s['set_num']}\n")
            f.write("### User\n")
            f.write(f"{USER_DIV}\n")
            f.write(f"{s['user']}\n")

            if s["system_events"]:
                f.write("\n**System Events:**\n")
                for ev in s["system_events"]:
                    ev_clean = ev.replace("<system>", "").replace("</system>", "").strip()
                    f.write(f"- {ev_clean}\n")

            f.write(f"\n{BOT_DIV}\n")
            f.write(f"### Set {s['set_num']}\n")
            f.write("### Kimi\n")
            f.write(f"{BOT_DIV}\n")

            if s["thinking"]:
                f.write("**[Thinking]**\n")
                f.write(f"{s['thinking']}\n")
                f.write("**[/Thinking]**\n\n")

            f.write(f"{s['assistant']}\n")

            if s["tool_results"]:
                f.write("\n**Tool Results:**\n")
                for tr in s["tool_results"]:
                    f.write(f"- Tool `{tr['tool_call_id']}`:\n")
                    text = tr["text"]
                    if len(text) > 500:
                        text = text[:500] + "\n... [truncated]\n"
                    f.write(f"  ```\n{text}\n  ```\n")

            if s["tool_calls"]:
                f.write("\n**Tools Called:**\n")
                for tc in s["tool_calls"]:
                    f.write(f"- `{tc['name']}`\n")

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


def write_thinking(sets: List[Dict], wire_data: Dict[int, Dict], path: Path):
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
        if wire_data:
            f.write("\n---\n\n")
            f.write("# Wire Protocol Thinking (Extended)\n\n")
            for turn_num, turn in wire_data.items():
                if turn["thinking"]:
                    f.write(f"{BOT_DIV}\n")
                    f.write(f"### Turn {turn_num}\n")
                    f.write(f"{BOT_DIV}\n\n")
                    for thought in turn["thinking"]:
                        f.write(f"{thought}\n\n")


def write_tools(sets: List[Dict], path: Path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Tool Calls\n\n")
        f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
        f.write("---\n\n")
        all_tools = []
        for s in sets:
            for tc in s["tool_calls"]:
                all_tools.append({
                    "set": s["set_num"],
                    "name": tc["name"],
                    "arguments": tc["arguments"],
                })
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
                args = c["arguments"]
                if len(args) > 200:
                    args = args[:200] + "..."
                f.write(f"  ```json\n  {args}\n  ```\n")
            f.write("\n")


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────

def main():
    argparser = argparse.ArgumentParser(description="Parse Kimi CLI session into markdown")
    argparser.add_argument("input", help="Path to Kimi session directory containing context_1.jsonl")
    argparser.add_argument("--outdir", "-o", help="Output directory (default: ~/save-aichats.com-kimi/<session_name>)")
    args = argparser.parse_args()

    session_dir = Path(args.input).expanduser().resolve()
    if not session_dir.is_dir():
        print(f"❌ Directory not found: {session_dir}", file=sys.stderr)
        sys.exit(1)

    # Kimi uses either context.jsonl or context_1.jsonl
    context_file = session_dir / "context_1.jsonl"
    if not context_file.exists():
        context_file = session_dir / "context.jsonl"

    wire_file = session_dir / "wire.jsonl"

    if not context_file.exists():
        print(f"❌ Missing context_1.jsonl or context.jsonl in {session_dir}", file=sys.stderr)
        sys.exit(1)

    # Determine output directory
    if args.outdir:
        output_dir = Path(args.outdir).expanduser().resolve()
    else:
        default_base = Path.home() / "save-aichats.com-kimi"
        session_name = session_dir.name
        output_dir = default_base / session_name

    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    context_entries = load_jsonl(context_file)
    wire_entries = load_jsonl(wire_file) if wire_file.exists() else []

    # Optional global dirs
    user_history_dir = Path.home() / ".kimi" / "user-history"
    logs_dir = Path.home() / ".kimi" / "logs"

    user_history_entries = []
    if user_history_dir.exists():
        for uh_file in user_history_dir.glob("*.jsonl"):
            user_history_entries.extend(load_jsonl(uh_file))

    log_files = list(logs_dir.glob("kimi.*.log")) if logs_dir.exists() else []

    print(f"📥 Loaded {len(context_entries)} context entries")
    print(f"📡 Loaded {len(wire_entries)} wire entries")
    print(f"📚 Loaded {len(user_history_entries)} user-history entries")
    print(f"📋 Found {len(log_files)} log files")

    # Parse
    sets = parse_context_jsonl(context_entries)
    wire_data = parse_wire_jsonl(wire_entries)

    print(f"🧩 Parsed {len(sets)} conversation sets")

    # Write outputs
    write_chat_sets(sets, output_dir / "CHAT_SETS.md")
    write_code_blocks(sets, output_dir / "CODE_BLOCKS.md")
    write_attachments(sets, output_dir / "ATTACHMENTS.md")
    write_thinking(sets, wire_data, output_dir / "THINKING.md")
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
