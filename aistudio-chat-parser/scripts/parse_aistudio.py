#!/usr/bin/env python3
import os
import sys
import json
import re
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

# --- CONFIG ---
ARCHIVE_ROOT = os.path.expanduser("~/session-archive/aistudio-sessions")
SKILL_ROOT = "/home/flintx/.agents/skills/aistudio-chat-parser"
TEMPLATE_PATH = os.path.join(SKILL_ROOT, "templates", "transcript_template.html")
REGISTRY_PATH = os.path.join(ARCHIVE_ROOT, "registry.json")

# --- SYMBOLS ---
USER_SEP = "▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰"
BOT_SEP = "▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄"
REF_SEP = "⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘"
BULLETS = ["💲", "♠️", "❇", "➡️", "▶", "📎"]

@dataclass
class CodeBlock:
    turn_number: int
    block_number: int
    lang: str
    code: str
    line_count: int

@dataclass
class Turn:
    turn: int
    user: str = ""
    bot: str = ""
    timestamp: str = ""
    codeBlocks: List[CodeBlock] = None
    images: List[str] = None

class HeuristicAnalyzer:
    def __init__(self, turns: List[Turn]):
        self.turns = turns
        self.jes = []
    def analyze(self):
        for turn in self.turns:
            text = turn.user.lower()
            if "decided" in text: self.jes.append({"category": "Decision", "title": f"Turn {turn.turn}", "summary": turn.user[:100]})

class AIStudioParser:
    def __init__(self, input_path: str):
        self.input_path = input_path
        with open(input_path, 'r', encoding='utf-8') as f:
            self.raw_data = json.load(f)
        base = os.path.basename(input_path)
        self.session_id = re.sub(r'[^a-zA-Z0-9]', '-', re.sub(r'\.(json|txt|md)$', '', base, flags=re.I)).lower()
        self.title = self.raw_data.get("title")
        self.turns: List[Turn] = []
        self.all_images = []

    def _format_bullets(self, text: str, turn_idx: int) -> str:
        if not text: return ""
        lines = text.split('\n')
        bullet_idx = turn_idx % len(BULLETS)
        new_lines = []
        for line in lines:
            if re.match(r'^[ \t]*[*•-][ \t]+', line):
                symbol = BULLETS[bullet_idx]
                line = re.sub(r'^[ \t]*[*•-][ \t]+', f"{symbol} ", line)
                bullet_idx = (bullet_idx + 1) % len(BULLETS)
            new_lines.append(line)
        return '\n'.join(new_lines)

    def parse(self):
        chunks = self.raw_data.get("chunkedPrompt", {}).get("chunks", [])
        turn_idx = 1
        current_turn = None
        for chunk in chunks:
            role = chunk.get("role")
            text = chunk.get("text", "")
            if "parts" in chunk:
                text += "".join([p.get("text", "") for p in chunk["parts"] if isinstance(p, dict) and "text" in p])
            img_list = []
            if "parts" in chunk:
                for p in chunk["parts"]:
                    if isinstance(p, dict) and "fileData" in p:
                        fname = os.path.basename(p["fileData"].get("fileUri", "unknown.png"))
                        img_list.append(fname)
                        if fname not in self.all_images: self.all_images.append(fname)
            if role == "user":
                if current_turn and current_turn.bot:
                    self.turns.append(current_turn)
                    turn_idx += 1
                    current_turn = None
                if not current_turn:
                    current_turn = Turn(turn=turn_idx, user=text, bot="", codeBlocks=[], images=img_list)
                else:
                    if text not in current_turn.user: current_turn.user += "\n" + text
                    for img in img_list:
                        if img not in current_turn.images: current_turn.images.append(img)
                if not self.title: self.title = text[:50].strip() + "..."
            elif role == "model":
                if current_turn:
                    if text not in current_turn.bot: current_turn.bot += "\n" + text
                else:
                    current_turn = Turn(turn=turn_idx, user="", bot=text, codeBlocks=[], images=[])
        if current_turn: self.turns.append(current_turn)
        for turn in self.turns:
            code_matches = re.findall(r'```(.*?)\n?(.*?)```', turn.bot, re.DOTALL)
            seen_code = set()
            block_idx = 1
            for lang, code in code_matches:
                trimmed = code.strip()
                if trimmed and trimmed not in seen_code:
                    turn.codeBlocks.append(CodeBlock(turn_number=turn.turn, block_number=block_idx, lang=lang.strip() or "text", code=trimmed, line_count=len(trimmed.split('\n'))))
                    seen_code.add(trimmed)
                    block_idx += 1

    def generate_outputs(self):
        safe_title = re.sub(r'[^a-zA-Z0-9]', '-', self.title).lower().strip('-')[:60]
        session_dir = os.path.join(ARCHIVE_ROOT, f"{self.session_id}_{safe_title}")
        os.makedirs(session_dir, exist_ok=True)

        self.generate_md(os.path.join(session_dir, "transcript.md"), session_dir)
        self.generate_html(os.path.join(session_dir, "transcript.html"))
        self.generate_txt(os.path.join(session_dir, "transcript.txt"))
        self.generate_code_file(os.path.join(session_dir, "_code.md"))
        self.generate_image_summary(os.path.join(session_dir, "_images.md"))
        
        self._update_registry(session_dir)
        return session_dir

    def generate_md(self, path: str, session_dir: str):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"# {self.title}\n\nSession ID: {self.session_id}\n\n")
            for turn in self.turns:
                f.write(f"{USER_SEP}\n### Turn {turn.turn}\n### User\n{USER_SEP}\n\n{self._format_bullets(turn.user, turn.turn)}\n\n")
                for img in turn.images: f.write(f"⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘\n     IMAGE ATTACHED: \n   {img}\n⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘⫘\n\n")
                f.write(f"{BOT_SEP}\n### Turn {turn.turn}\n### Gemini\n{BOT_SEP}\n\n")
                bot_clean = re.sub(r'```[\s\S]*?```', '', turn.bot, flags=re.DOTALL)
                if bot_clean.strip(): f.write(f"{self._format_bullets(bot_clean.strip(), turn.turn)}\n\n")
                for cb in turn.codeBlocks:
                    f.write(f"{REF_SEP}\n                            Code: Turn {turn.turn} // Block {cb.block_number}\n")
                    f.write(f"                          {cb.line_count} lines of code. \n")
                    f.write(f"       {session_dir}/_code.md\n{REF_SEP}\n\n")
                f.write("---\n\n")

    def generate_txt(self, path: str):
        with open(path, 'w', encoding='utf-8') as f:
            for turn in self.turns:
                f.write(f"--- TURN {turn.turn} ---\nUSER: {turn.user}\n\nGEMINI: {turn.bot}\n\n")

    def generate_code_file(self, path: str):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"# Code Extractions: {self.title}\n\n")
            for turn in self.turns:
                if turn.codeBlocks:
                    f.write(f"## TURN {turn.turn}\n\n")
                    for cb in turn.codeBlocks:
                        f.write(f"### Block {cb.block_number} ({cb.lang})\n```{cb.lang}\n{cb.code}\n```\n\n")

    def generate_image_summary(self, path: str):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"# Image inventory: {self.title}\n\n")
            if not self.all_images: f.write("No images.\n")
            else:
                for i, img in enumerate(self.all_images, 1): f.write(f"{i}. {img}\n")

    def generate_html(self, path: str):
        if not os.path.exists(TEMPLATE_PATH): return
        with open(TEMPLATE_PATH, 'r') as f: template = f.read()
        turns_json = json.dumps([asdict(t) for t in self.turns], ensure_ascii=False)
        html = template.replace('{{title}}', self.title).replace('{{session_id}}', self.session_id).replace('{{turns_json}}', turns_json.replace('</script>', '<\\/script>'))
        with open(path, 'w', encoding='utf-8') as f: f.write(html)

    def _update_registry(self, session_dir: str):
        registry = {"sessions": []}
        os.makedirs(ARCHIVE_ROOT, exist_ok=True)
        if os.path.exists(REGISTRY_PATH):
            with open(REGISTRY_PATH, 'r') as f:
                try: registry = json.load(f)
                except: pass
        exists = False
        for s in registry["sessions"]:
            if s["id"] == self.session_id:
                s.update({"title": self.title, "path": session_dir, "last_processed": datetime.now().isoformat()})
                exists = True; break
        if not exists: registry["sessions"].append({"id": self.session_id, "title": self.title, "path": session_dir, "last_processed": datetime.now().isoformat()})
        with open(REGISTRY_PATH, 'w') as f: json.dump(registry, f, indent=2)

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(1)
    p = AIStudioParser(sys.argv[1])
    p.parse()
    out = p.generate_outputs()
    print(f"Extraction complete: {out}")
