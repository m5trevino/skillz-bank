#!/usr/bin/env python3
"""
JSON/JSONL Chat Analyzer
Parses chat exports (Kimi CLI sessions, Claude, OpenAI, etc.) and generates:
  - index.html  : role stats dashboard
  - breakdown.md: high-and-tight tree breakdown

Usage:
  python3 json_chat_analyzer.py <input.json|jsonl> [output_dir]
"""

import json
import sys
import os
from collections import defaultdict
from datetime import datetime
import html


def load_messages(path):
    """Load JSON or JSONL file into a list of message dicts."""
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read().strip()

    # Try standard JSON first
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("messages", [data])
        return []
    except json.JSONDecodeError:
        pass

    # Fallback: JSONL (one JSON object per line)
    messages = []
    for n, line in enumerate(raw.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            messages.append(json.loads(line))
        except json.JSONDecodeError:
            print(f"  ⚠️  skipped invalid JSON on line {n}")
    return messages


def msg_type(msg):
    """Return the primary type of a message."""
    content = msg.get("content")

    if isinstance(content, list) and content:
        first = content[0]
        if isinstance(first, dict):
            return first.get("type") or "block"
        return "mixed"

    if isinstance(content, str):
        return "text"

    if content is None:
        role = msg.get("role", "unknown")
        # Meta roles (_checkpoint, _usage, etc.) → use role name without prefix
        return role.lstrip("_") if role.startswith("_") else "empty"

    return msg.get("type", "other")


def msg_has_think(msg):
    """True if the message contains think content anywhere."""
    content = msg.get("content", [])
    if isinstance(content, list):
        return any(isinstance(b, dict) and b.get("type") == "think" for b in content)
    if isinstance(content, dict):
        return "think" in content
    return bool(msg.get("think"))


def msg_has_text(msg):
    """True if the message contains text content anywhere."""
    content = msg.get("content", [])
    if isinstance(content, list):
        return any(isinstance(b, dict) and b.get("type") == "text" for b in content)
    if isinstance(content, str):
        return bool(content.strip())
    if isinstance(content, dict):
        return "text" in content
    return bool(msg.get("text"))


def analyze(messages):
    """Analyze messages and return stats dict."""
    stats = {
        "total": 0,
        "roles": defaultdict(lambda: {
            "count": 0,
            "types": defaultdict(int),
            "think": 0,
            "text": 0,
        }),
        "global_think": 0,
        "global_text": 0,
        "all_types": set(),
    }

    for msg in messages:
        if not isinstance(msg, dict):
            continue

        role = msg.get("role", "unknown")
        typ = msg_type(msg)

        stats["total"] += 1
        stats["roles"][role]["count"] += 1
        stats["roles"][role]["types"][typ] += 1
        stats["all_types"].add(typ)

        if msg_has_think(msg):
            stats["roles"][role]["think"] += 1
            stats["global_think"] += 1
        if msg_has_text(msg):
            stats["roles"][role]["text"] += 1
            stats["global_text"] += 1

    return stats


def generate_html(stats, filename):
    """Generate compact HTML dashboard."""
    roles = dict(stats["roles"])
    total = stats["total"]
    types_str = ", ".join(sorted(stats["all_types"]))

    lines = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '  <meta charset="UTF-8">',
        f'  <title>{html.escape(os.path.basename(filename))}</title>',
        "  <style>",
        "    *{margin:0;padding:0;box-sizing:border-box}",
        "    body{font-family:'SF Mono',Monaco,monospace;background:#0d0d0d;color:#bbb;line-height:1.5;padding:1.5rem}",
        "    .wrap{max-width:800px;margin:0 auto}",
        "    h1{color:#00d4aa;font-size:1.1rem;margin-bottom:.2rem}",
        "    .meta{color:#555;font-size:.75rem;margin-bottom:1.5rem;border-bottom:1px solid #222;padding-bottom:.5rem}",
        "    .pills{display:flex;gap:.6rem;margin-bottom:1.5rem;font-size:.8rem;flex-wrap:wrap}",
        "    .pill{background:#111;border:1px solid #222;padding:.25rem .7rem;border-radius:4px}",
        "    .pill b{color:#00d4aa}",
        "    .card{background:#111;border:1px solid #1a1a1a;border-left:3px solid #00d4aa;padding:.7rem 1rem;margin-bottom:.5rem}",
        "    .head{display:flex;justify-content:space-between;align-items:center;margin-bottom:.3rem}",
        "    .role{color:#fff;font-size:.9rem;font-weight:600}",
        "    .count{color:#00d4aa;font-size:.85rem}",
        "    .tags{display:flex;gap:.4rem;flex-wrap:wrap;font-size:.72rem}",
        "    .tag{background:#151515;border:1px solid #262626;padding:.1rem .4rem;border-radius:3px;color:#888}",
        "    .tag i{color:#ff6b35;font-style:normal}",
        "    .bar{display:flex;height:3px;margin-top:.4rem;gap:1px}",
        "    .b-think{background:#ff6b35}",
        "    .b-text{background:#00d4aa}",
        "    .b-other{background:#333}",
        "    a.link{display:inline-block;margin-top:.4rem;color:#555;text-decoration:none;font-size:.7rem}",
        "    a.link:hover{color:#00d4aa}",
        "  </style>",
        "</head>",
        "<body>",
        '  <div class="wrap">',
        f'    <h1>📊 {html.escape(os.path.basename(filename))}</h1>',
        f'    <p class="meta">{total} messages · {len(roles)} roles · {types_str}</p>',
        '    <div class="pills">',
        f'      <div class="pill"><b>{total}</b> total</div>',
        f'      <div class="pill"><b>{stats["global_think"]}</b> think</div>',
        f'      <div class="pill"><b>{stats["global_text"]}</b> text</div>',
        "    </div>",
    ]

    for role, d in sorted(roles.items(), key=lambda x: x[1]["count"], reverse=True):
        c = d["count"]
        th = d["think"]
        tx = d["text"]
        ot = max(0, c - th - tx)

        tags = "".join(
            f'<span class="tag">{html.escape(str(t))}:<i>{n}</i></span>'
            for t, n in sorted(d["types"].items(), key=lambda x: x[1], reverse=True)
        )

        tw = (th / c * 100) if c else 0
        txw = (tx / c * 100) if c else 0
        ow = max(0, 100 - tw - txw)

        lines += [
            f'    <div class="card" id="role-{html.escape(str(role))}">',
            '      <div class="head">',
            f'        <span class="role">role:{html.escape(str(role))}</span>',
            f'        <span class="count">{c}</span>',
            "      </div>",
            f'      <div class="tags">{tags}</div>',
            '      <div class="bar">',
            f'        <div class="b-think" style="width:{tw}%" title="think:{th}"></div>',
            f'        <div class="b-text" style="width:{txw}%" title="text:{tx}"></div>',
            f'        <div class="b-other" style="width:{ow}%" title="other:{ot}"></div>',
            "      </div>",
            f'      <a class="link" href="breakdown.md#{html.escape(str(role))}">view md →</a>',
            "    </div>",
        ]

    lines += [
        "  </div>",
        "</body>",
        "</html>",
    ]

    return "\n".join(lines)


def generate_markdown(messages, stats, filename):
    """Generate high-and-tight Markdown tree breakdown."""
    # Group messages by role
    by_role = defaultdict(list)
    for msg in messages:
        if isinstance(msg, dict):
            by_role[msg.get("role", "unknown")].append(msg)

    lines = [
        f"# `{os.path.basename(filename)}`",
        "",
        f"> {stats['total']} messages · {len(stats['roles'])} roles",
        "",
    ]

    # Top summary line
    for role, d in sorted(stats["roles"].items(), key=lambda x: x[1]["count"], reverse=True):
        types_part = " ".join(f"{t}:{n}" for t, n in sorted(d["types"].items()))
        lines.append(f"- `role:{role}` — {d['count']} ({types_part})")

    lines += ["", "---", ""]

    # Tree view per role
    for role, msgs in sorted(by_role.items(), key=lambda x: len(x[1]), reverse=True):
        total_role = len(msgs)
        lines.append(f'### <a name="{role}"></a>`{role}` — {total_role}')
        lines.append("")
        lines.append("```")
        lines.append(f"── role:{role}")

        # Count types
        type_counts = defaultdict(int)
        for msg in msgs:
            type_counts[msg_type(msg)] += 1

        type_items = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
        for ti, (t, tc) in enumerate(type_items):
            is_last_type = ti == len(type_items) - 1
            branch = "└──" if is_last_type else "├──"
            indent = "│   "
            lines.append(f"{indent}{branch} type:{t} — {tc}")

            # Count think/text for messages of this type
            think_c = sum(1 for m in msgs if msg_type(m) == t and msg_has_think(m))
            text_c = sum(1 for m in msgs if msg_type(m) == t and msg_has_text(m))

            sub_indent = indent + ("    " if is_last_type else "│   ")
            subs = []
            if think_c:
                subs.append(("think", think_c))
            if text_c:
                subs.append(("text", text_c))

            for si, (name, sc) in enumerate(subs):
                sub_branch = "└──" if si == len(subs) - 1 else "├──"
                lines.append(f"{sub_indent}{sub_branch} {name}:{sc}")

        lines.append("```")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 json_chat_analyzer.py <input.json|jsonl> [output_dir]")
        sys.exit(1)

    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "./chat_analysis"

    print(f"🔍 Loading {src}...")
    messages = load_messages(src)
    print(f"📊 Analyzing {len(messages)} messages...")

    stats = analyze(messages)
    os.makedirs(out, exist_ok=True)

    # HTML
    html_path = os.path.join(out, "index.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(generate_html(stats, src))
    print(f"✅ HTML:  {html_path}")

    # Markdown
    md_path = os.path.join(out, "breakdown.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(generate_markdown(messages, stats, src))
    print(f"✅ Markdown: {md_path}")

    # Console summary
    print(f"\n📊 {stats['total']} messages · {len(stats['roles'])} roles")
    for role, d in sorted(stats["roles"].items(), key=lambda x: x[1]["count"], reverse=True):
        types = " ".join(f"{t}:{n}" for t, n in sorted(d["types"].items()))
        print(f"   role:{role:20s} {d['count']:4d}  ({types})")


if __name__ == "__main__":
    main()
