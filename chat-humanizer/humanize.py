#!/usr/bin/env python3
"""
Chat Humanizer — Convert AI platform JSON exports to clean Markdown.
Supports: ChatGPT, Claude, Google AI Studio / Gemini
Handles .json files and extensionless JSON text files.
Supports single combined output OR split per-conversation files.
"""

import json
import sys
import re
import os
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, List


def detect_format(data) -> str:
    """Auto-detect the export format."""
    if isinstance(data, list) and len(data) > 0:
        first = data[0]
        if isinstance(first, dict):
            if "chat_messages" in first:
                return "claude"
            if "mapping" in first:
                return "chatgpt"
            if "contents" in first:
                return "aistudio"
    if isinstance(data, dict):
        if "chunkedPrompt" in data:
            return "aistudio"
        if "contents" in data:
            return "aistudio"
        if "chat_messages" in data:
            return "claude"
        if "mapping" in data:
            return "chatgpt"
    return "unknown"


def fmt_time(ts) -> str:
    """Format various timestamp formats."""
    if ts is None:
        return ""
    if isinstance(ts, (int, float)):
        try:
            return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
        except (ValueError, OSError):
            return str(ts)
    if isinstance(ts, str):
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return ts
    return str(ts)


def clean_filename(name: str) -> str:
    """Clean a string for use as a filename."""
    if not name:
        return "untitled"
    # Remove or replace invalid chars
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    # Limit length
    if len(name) > 60:
        name = name[:60]
    return name or "untitled"


def clean_text(text) -> str:
    """Clean up text content."""
    if text is None:
        return ""
    if isinstance(text, list):
        text = "\n".join(str(t) for t in text if t)
    text = str(text)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    return text.strip()


def extract_chatgpt_messages(mapping: dict) -> List[tuple]:
    """Extract (role, text) pairs from ChatGPT mapping tree."""
    messages = []
    root_id = None
    for node_id, node in mapping.items():
        if node.get("parent") is None:
            root_id = node_id
            break

    def walk(node_id):
        node = mapping.get(node_id)
        if not node:
            return
        msg = node.get("message")
        if msg:
            role = msg.get("author", {}).get("role", "unknown")
            if role == "system":
                pass
            elif msg.get("metadata", {}).get("is_visually_hidden_from_conversation"):
                pass
            else:
                content = msg.get("content", {})
                parts = content.get("parts", [])
                text = clean_text(parts)
                if text:
                    display_role = "User" if role == "user" else "ChatGPT"
                    messages.append((display_role, text))
        for child_id in node.get("children", []):
            walk(child_id)

    if root_id:
        walk(root_id)
    return messages


def extract_claude_messages(chat_messages: list) -> List[tuple]:
    """Extract (role, text) pairs from Claude chat_messages."""
    messages = []
    for msg in chat_messages:
        sender = msg.get("sender", "unknown")
        text = clean_text(msg.get("text", ""))
        if not text:
            continue
        display_role = "User" if sender == "human" else "Claude"
        messages.append((display_role, text))
    return messages


def extract_aistudio_chunks(chunks: list) -> List[tuple]:
    """Extract (role, text) pairs from AI Studio chunkedPrompt chunks."""
    messages = []
    for chunk in chunks:
        role = chunk.get("role", "unknown")
        if chunk.get("isThought"):
            continue

        text = ""
        if "text" in chunk:
            text = clean_text(chunk["text"])
        elif "driveDocument" in chunk:
            doc_id = chunk["driveDocument"].get("id", "unknown")
            text = f"*[Attached Google Drive document: {doc_id}]*"
        elif "inlineFile" in chunk:
            inline = chunk["inlineFile"]
            mime = inline.get("mimeType", "unknown")
            name = inline.get("name", "unnamed")
            text = f"*[Attached file: {name} ({mime})]*"
        elif "executableCode" in chunk:
            code = chunk["executableCode"]
            text = f"```\n{code}\n```"
        elif "codeExecutionResult" in chunk:
            result = chunk["codeExecutionResult"]
            text = f"**[Execution Result]:**\n```\n{result}\n```"
        elif "parts" in chunk:
            parts_texts = []
            for part in chunk["parts"]:
                if "text" in part:
                    parts_texts.append(part["text"])
                elif "executableCode" in part:
                    parts_texts.append(f"```\n{part['executableCode']}\n```")
                elif "codeExecutionResult" in part:
                    parts_texts.append(f"```\n{part['codeExecutionResult']}\n```")
            text = clean_text("\n".join(parts_texts))

        if not text:
            continue

        display_role = "User" if role == "user" else "Gemini"
        messages.append((display_role, text))
    return messages


def build_markdown(title: str, created: str, messages: List[tuple], platform: str) -> str:
    """Build a single conversation markdown document."""
    out = []
    out.append(f"# {title}")
    if created:
        out.append(f"*{created}*")
    out.append("")
    if platform:
        out.append(f"*Platform: {platform}*")
        out.append("")

    for role, text in messages:
        out.append(f"**{role}:** {text}")
        out.append("")

    return "\n".join(out)


def humanize_claude(data, out_dir: Optional[Path] = None, single_file: bool = True) -> List[str]:
    """Convert Claude conversations to Markdown."""
    conversations = data if isinstance(data, list) else [data]
    outputs = []

    if single_file:
        out = ["# Claude Conversations\n"]
        for conv in conversations:
            title = conv.get("name") or conv.get("uuid", "Untitled")[:8]
            created = fmt_time(conv.get("created_at"))
            messages = extract_claude_messages(conv.get("chat_messages", []))
            if not messages:
                continue
            out.append(f"## {title}")
            if created:
                out.append(f"*{created}*")
            out.append("")
            for role, text in messages:
                out.append(f"**{role}:** {text}")
                out.append("")
        return ["\n".join(out)]
    else:
        for i, conv in enumerate(conversations, 1):
            title = conv.get("name") or "Untitled"
            created = fmt_time(conv.get("created_at"))
            messages = extract_claude_messages(conv.get("chat_messages", []))
            if not messages:
                continue

            safe_title = clean_filename(title)
            filename = f"{i:03d}-{safe_title}.md"
            filepath = out_dir / filename

            md = build_markdown(title, created, messages, "Claude")
            filepath.write_text(md, encoding="utf-8")
            outputs.append(str(filepath))

        return outputs


def humanize_chatgpt(data, out_dir: Optional[Path] = None, single_file: bool = True) -> List[str]:
    """Convert ChatGPT conversations to Markdown."""
    conversations = data if isinstance(data, list) else [data]
    outputs = []

    if single_file:
        out = ["# ChatGPT Conversations\n"]
        for conv in conversations:
            title = conv.get("title") or "Untitled"
            created = fmt_time(conv.get("create_time"))
            messages = extract_chatgpt_messages(conv.get("mapping", {}))
            if not messages:
                continue
            out.append(f"## {title}")
            if created:
                out.append(f"*{created}*")
            out.append("")
            for role, text in messages:
                out.append(f"**{role}:** {text}")
                out.append("")
        return ["\n".join(out)]
    else:
        for i, conv in enumerate(conversations, 1):
            title = conv.get("title") or "Untitled"
            created = fmt_time(conv.get("create_time"))
            messages = extract_chatgpt_messages(conv.get("mapping", {}))
            if not messages:
                continue

            safe_title = clean_filename(title)
            filename = f"{i:03d}-{safe_title}.md"
            filepath = out_dir / filename

            md = build_markdown(title, created, messages, "ChatGPT")
            filepath.write_text(md, encoding="utf-8")
            outputs.append(str(filepath))

        return outputs


def humanize_aistudio(data, out_dir: Optional[Path] = None, single_file: bool = True) -> List[str]:
    """Convert Google AI Studio / Gemini JSON to Markdown."""
    outputs = []

    # Handle chunkedPrompt format (exported .txt files) — single conversation
    if "chunkedPrompt" in data:
        chunks = data.get("chunkedPrompt", {}).get("chunks", [])
        run_settings = data.get("runSettings", {})
        model = run_settings.get("model", "unknown")
        messages = extract_aistudio_chunks(chunks)

        if not messages:
            return []

        title = "AI Studio Conversation"
        md = build_markdown(title, "", messages, f"AI Studio / {model}")

        if single_file:
            return [md]
        else:
            filename = "001-conversation.md"
            filepath = out_dir / filename
            filepath.write_text(md, encoding="utf-8")
            return [str(filepath)]

    # Handle standard contents format
    contents = data.get("contents", []) if isinstance(data, dict) else []
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) and "contents" in data[0]:
        # Array of sessions
        if single_file:
            out = ["# AI Studio / Gemini Conversations\n"]
            for session in data:
                title = session.get("title", "Untitled")
                messages = []
                for msg in session.get("contents", []):
                    role = msg.get("role", "unknown")
                    parts = msg.get("parts", [])
                    text = extract_aistudio_parts(parts)
                    if text:
                        display_role = "User" if role == "user" else "Gemini"
                        messages.append((display_role, text))
                if not messages:
                    continue
                out.append(f"## {title}\n")
                for role, text in messages:
                    out.append(f"**{role}:** {text}")
                    out.append("")
            return ["\n".join(out)]
        else:
            for i, session in enumerate(data, 1):
                title = session.get("title", "Untitled")
                messages = []
                for msg in session.get("contents", []):
                    role = msg.get("role", "unknown")
                    parts = msg.get("parts", [])
                    text = extract_aistudio_parts(parts)
                    if text:
                        display_role = "User" if role == "user" else "Gemini"
                        messages.append((display_role, text))
                if not messages:
                    continue

                safe_title = clean_filename(title)
                filename = f"{i:03d}-{safe_title}.md"
                filepath = out_dir / filename

                md = build_markdown(title, "", messages, "AI Studio / Gemini")
                filepath.write_text(md, encoding="utf-8")
                outputs.append(str(filepath))
            return outputs
    else:
        # Single session
        messages = []
        for msg in contents:
            role = msg.get("role", "unknown")
            parts = msg.get("parts", [])
            text = extract_aistudio_parts(parts)
            if text:
                display_role = "User" if role == "user" else "Gemini"
                messages.append((display_role, text))

        if not messages:
            return []

        md = build_markdown("AI Studio Conversation", "", messages, "AI Studio / Gemini")
        if single_file:
            return [md]
        else:
            filename = "001-conversation.md"
            filepath = out_dir / filename
            filepath.write_text(md, encoding="utf-8")
            return [str(filepath)]


def extract_aistudio_parts(parts) -> str:
    """Extract text from AI Studio parts array."""
    if not parts:
        return ""
    texts = []
    for part in parts:
        if isinstance(part, str):
            texts.append(part)
        elif isinstance(part, dict):
            if "text" in part:
                texts.append(part["text"])
            elif "executableCode" in part:
                texts.append(f"```\n{part['executableCode']}\n```")
            elif "codeExecutionResult" in part:
                texts.append(f"```\n{part['codeExecutionResult']}\n```")
    return clean_text("\n".join(texts))


def humanize(input_path: str, output_path: Optional[str] = None, split: bool = False) -> List[str]:
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {input_path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    fmt = detect_format(data)

    # Determine output directory
    if split:
        if output_path:
            out_dir = Path(output_path)
        else:
            # Create a directory named after the input file
            base = path.stem if path.suffix else path.name
            out_dir = path.parent / f"{base}-humanized"
        out_dir.mkdir(parents=True, exist_ok=True)
    else:
        out_dir = None

    if fmt == "claude":
        results = humanize_claude(data, out_dir, single_file=not split)
    elif fmt == "chatgpt":
        results = humanize_chatgpt(data, out_dir, single_file=not split)
    elif fmt == "aistudio":
        results = humanize_aistudio(data, out_dir, single_file=not split)
    else:
        name = path.name.lower()
        if "claude" in name:
            results = humanize_claude(data, out_dir, single_file=not split)
        elif "chatgpt" in name or "openai" in name:
            results = humanize_chatgpt(data, out_dir, single_file=not split)
        else:
            raise ValueError(f"Unknown format. Could not detect platform from JSON structure.")

    if split:
        return results
    else:
        # Single file output
        if output_path:
            out = Path(output_path)
        else:
            if path.suffix == "":
                out = Path(str(path) + ".md")
            else:
                out = path.with_suffix(".md")
        out.write_text(results[0], encoding="utf-8")
        return [str(out)]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Humanize AI chat exports")
    parser.add_argument("input", help="Input JSON file")
    parser.add_argument("output", nargs="?", help="Output file or directory")
    parser.add_argument("--split", "-s", action="store_true", help="One file per conversation")
    args = parser.parse_args()

    try:
        results = humanize(args.input, args.output, split=args.split)
        for r in results[:5]:
            print(f"✅ {r}")
        if len(results) > 5:
            print(f"... and {len(results) - 5} more files")
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
