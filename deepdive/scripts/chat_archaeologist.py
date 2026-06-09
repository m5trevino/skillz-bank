#!/usr/bin/env python3
import json, re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

class ChatArchaeologist:
    def __init__(self, chatlogs_path):
        self.path = Path(chatlogs_path)
        self.sessions = []
        self.decisions = []
        self.todos = []
        self.completions = []
        self.blockers = []
        self.verbatim_archive = []
        
    def ingest(self):
        chat_files = list(self.path.glob('*.json')) + list(self.path.glob('*.md')) + list(self.path.glob('*.txt'))
        for file in chat_files:
            self._parse_file(file)
        return {
            'sessions': self.sessions,
            'decisions': self.decisions,
            'todos': self.todos,
            'completions': self.completions,
            'blockers': self.blockers,
            'verbatim': self.verbatim_archive
        }
    
    def _extract_timestamp(self, filename):
        patterns = [r'(\d{4}-\d{2}-\d{2})', r'(\d{8})', r'(\d{4}_\d{2}_\d{2})']
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                return match.group(1)
        return datetime.now().strftime('%Y-%m-%d')
    
    def _parse_file(self, file):
        timestamp = self._extract_timestamp(file.name)
        with open(file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        self.verbatim_archive.append({
            'file': file.name,
            'timestamp': timestamp,
            'content': content
        })
        
        lines = content.split('\n')
        current_topic = "general"
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(x in line_lower for x in ['app', 'project', 'feature', 'module']):
                current_topic = self._extract_topic(line)
            
            decision_patterns = [
                r'(?:we should|let\'s|decided to|going with|fuck it[,\s]+use|fuckin[\'g]\s+use|gonna use)\s+(.{10,100})',
                r'(?:switch|change|migrate|refactor|move)\s+(?:to|from)?\s+(.{10,100})',
                r'(?:i want|need|gotta)\s+(.{10,100})(?:because|since|as)',
            ]
            for pattern in decision_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    self.decisions.append({
                        'text': line.strip(),
                        'extract': match.group(1) if match.groups() else line.strip(),
                        'topic': current_topic,
                        'timestamp': timestamp,
                        'source_file': file.name,
                        'line_number': i,
                        'context': '\n'.join(lines[max(0,i-2):i+3])
                    })
            
            todo_patterns = [
                r'(?:todo|need to|still have to|next step|haven\'t|yet to|gotta)\s+(.{10,100})',
                r'(?:fix|build|add|implement|refactor|create)\s+(?:the|this|a)?\s+(.{10,100})(?:later|soon|next|eventually)',
            ]
            for pattern in todo_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    self.todos.append({
                        'text': line.strip(),
                        'extract': match.group(1) if match.groups() else line.strip(),
                        'topic': current_topic,
                        'timestamp': timestamp,
                        'source_file': file.name,
                        'status': 'pending'
                    })
            
            if re.search(r'(?:done|finished|completed|works now|fucking finally|it\'s live|shipped|deployed)', line, re.IGNORECASE):
                self.completions.append({
                    'text': line.strip(),
                    'topic': current_topic,
                    'timestamp': timestamp,
                    'source_file': file.name
                })
            
            if re.search(r'(?:stuck on|can\'t figure out|broken|pissing me off|fucking bug|doesn\'t work|failed)', line, re.IGNORECASE):
                self.blockers.append({
                    'text': line.strip(),
                    'topic': current_topic,
                    'timestamp': timestamp,
                    'source_file': file.name
                })
        
        self.sessions.append({
            'file': file.name,
            'timestamp': timestamp,
            'topics': list(set([d['topic'] for d in self.decisions if d['source_file'] == file.name]))
        })
    
    def _extract_topic(self, line):
        topics = ['auth', 'database', 'api', 'frontend', 'backend', 'ui', 'cache', 'deploy', 'test']
        for t in topics:
            if t in line.lower():
                return t
        return "general"
    
    def correlate_with_code(self, code_analysis, git_history):
        for todo in self.todos:
            todo_text = todo['text'].lower()
            implemented = False
            evidence = []
            for commit in git_history:
                if commit.get('date', '') > todo['timestamp']:
                    if any(keyword in commit.get('message', '').lower() for keyword in todo_text.split()[:3]):
                        implemented = True
                        evidence.append(f"commit:{commit['hash']}")
            for file_info in code_analysis.get('files', []):
                if any(keyword in file_info['path'].lower() for keyword in todo_text.split()[:3]):
                    implemented = True
                    evidence.append(f"file:{file_info['path']}")
            todo['status'] = 'implemented' if implemented else 'pending'
            todo['evidence'] = evidence
        return self.todos
    
    def generate_verbatim_doc(self):
        lines = ["# Conversation Archive\n", "**Preserved verbatim from chat logs**\n"]
        for v in self.verbatim_archive:
            lines.append(f"## {v['file']} ({v['timestamp']})")
            lines.append("```")
            lines.append(v['content'])
            lines.append("```\n")
        return '\n'.join(lines)
    
    def generate_synthesis(self):
        lines = ["# Discussion Synthesis\n", "## Major Decisions\n"]
        for d in self.decisions[:20]:
            lines.append(f"### [{d['timestamp']}] {d['topic'].upper()}")
            lines.append(f"**Decision:** {d['text'][:100]}")
            lines.append(f"**Extract:** {d.get('extract', 'N/A')[:100]}")
            lines.append(f"**Source:** `{d['source_file']}:{d['line_number']}`")
            lines.append(f"**Context:**")
            lines.append("```")
            lines.append(d['context'][:300])
            lines.append("```\n")
        
        if self.blockers:
            lines.append("## Blockers Encountered\n")
            for b in self.blockers[:10]:
                lines.append(f"- [{b['timestamp']}] {b['topic']}: {b['text'][:80]}...")
        
        if self.completions:
            lines.append("\n## Completions Celebrated\n")
            for c in self.completions[:10]:
                lines.append(f"- [{c['timestamp']}] {c['topic']}: {c['text'][:80]}...")
        
        return '\n'.join(lines)
    
    def generate_state_matrix(self, correlated_todos):
        lines = ["# Implementation State Matrix\n"]
        lines.append("| Discussed | Date | Status | Evidence | Topic |")
        lines.append("|-----------|------|--------|----------|-------|")
        
        for todo in correlated_todos[:30]:
            status_icon = "✅" if todo['status'] == 'implemented' else "❌"
            evidence = ', '.join(todo.get('evidence', []))[:40]
            lines.append(f"| {todo['text'][:40]}... | {todo['timestamp']} | {status_icon} {todo['status']} | {evidence} | {todo['topic']} |")
        
        lines.append("\n## Pending Actions (Auto-Extracted)\n")
        pending = [t for t in correlated_todos if t['status'] == 'pending']
        for p in pending[:15]:
            lines.append(f"- [ ] {p['timestamp']}: {p['text'][:80]}... ({p['topic']})")
        
        return '\n'.join(lines)
    
    def generate_narrative(self, git_epochs):
        lines = ["# Complete Project Narrative\n"]
        lines.append("## Code Epochs + Conversation Epochs\n")
        
        for i, epoch in enumerate(git_epochs or []):
            lines.append(f"### Epoch {i+1}: {epoch.get('mood', 'Unknown')} ({epoch.get('start')} → {epoch.get('end')})")
            lines.append(f"**Code:** {epoch.get('dominant_activity', 'unknown')} phase, {epoch.get('commit_count', 0)} commits")
            
            epoch_chats = [d for d in self.decisions if epoch.get('start') <= d['timestamp'] <= epoch.get('end', '9999-99-99')]
            if epoch_chats:
                lines.append(f"**Chats:** {len(epoch_chats)} decisions discussed")
                for c in epoch_chats[:3]:
                    lines.append(f"- {c['timestamp']}: {c['text'][:60]}...")
            else:
                lines.append("**Chats:** No recorded discussions")
            lines.append("")
        
        recent_pending = [t for t in self.todos if t['status'] == 'pending'][-5:]
        if recent_pending:
            lines.append("## Current Tensions (Discussed but Not Done)\n")
            for p in recent_pending:
                lines.append(f"- [{p['timestamp']}] {p['topic']}: {p['text'][:80]}...")
        
        return '\n'.join(lines)

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: chat_archaeologist.py <chatlogs_dir> [analysis.json]")
        sys.exit(1)
    
    chat_dir = sys.argv[1]
    analysis_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    archaeologist = ChatArchaeologist(chat_dir)
    data = archaeologist.ingest()
    
    print(f"Processed {len(data['sessions'])} chat sessions")
    print(f"Extracted: {len(data['decisions'])} decisions, {len(data['todos'])} todos, {len(data['completions'])} completions, {len(data['blockers'])} blockers")
    
    code_analysis = {}
    git_history = []
    if analysis_file:
        with open(analysis_file) as f:
            full_analysis = json.load(f)
            code_analysis = full_analysis
            git_history = full_analysis.get('git_history', [])
    
    correlated = archaeologist.correlate_with_code(code_analysis, git_history)
    
    docs = Path('.') / 'docs'
    docs.mkdir(exist_ok=True)
    
    with open(docs / '11-CONVERSATION_LOG.md', 'w') as f:
        f.write(archaeologist.generate_verbatim_doc())
    
    with open(docs / '12-DISCUSSION_SYNTHESIS.md', 'w') as f:
        f.write(archaeologist.generate_synthesis())
    
    with open(docs / '13-IMPLEMENTATION_STATE.md', 'w') as f:
        f.write(archaeologist.generate_state_matrix(correlated))
    
    print(f"\nChat archaeology complete. Outputs in {docs}/")
