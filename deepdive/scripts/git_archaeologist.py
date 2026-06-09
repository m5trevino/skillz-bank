#!/usr/bin/env python3
import subprocess, json
from datetime import datetime
from collections import defaultdict
import re

class GitArchaeologist:
    def __init__(self, repo_path):
        self.repo_path = repo_path
        self.commits = []
        self.epochs = []
        
    def excavate(self):
        result = subprocess.run(
            ['git', 'log', '--all', '--reverse', '--format=%H|%an|%ad|%s', '--date=short'],
            cwd=self.repo_path, capture_output=True, text=True
        )
        if result.returncode != 0:
            return None
        lines = result.stdout.strip().split('\n')
        for line in lines:
            parts = line.split('|')
            if len(parts) >= 4:
                self.commits.append({
                    'hash': parts[0][:8],
                    'author': parts[1],
                    'date': parts[2],
                    'message': parts[3],
                    'category': self._categorize(parts[3])
                })
        return self._detect_epochs()
    
    def _categorize(self, message):
        msg = message.lower()
        if any(x in msg for x in ['fix', 'bug', 'hotfix', 'patch']):
            return 'fix'
        elif any(x in msg for x in ['add', 'feature', 'implement', 'new']):
            return 'feature'
        elif any(x in msg for x in ['refactor', 'rewrite', 'restructure']):
            return 'refactor'
        elif any(x in msg for x in ['test', 'testing', 'spec']):
            return 'test'
        elif any(x in msg for x in ['doc', 'readme', 'comment']):
            return 'docs'
        elif any(x in msg for x in ['merge', 'pull request', 'pr']):
            return 'merge'
        else:
            return 'other'
    
    def _detect_epochs(self):
        if not self.commits:
            return []
        epochs = []
        current_epoch = {
            'start': self.commits[0]['date'],
            'end': self.commits[0]['date'],
            'commits': [self.commits[0]],
            'authors': {self.commits[0]['author']},
            'categories': defaultdict(int)
        }
        current_epoch['categories'][self.commits[0]['category']] += 1
        
        for commit in self.commits[1:]:
            last_date = datetime.strptime(current_epoch['end'], '%Y-%m-%d')
            this_date = datetime.strptime(commit['date'], '%Y-%m-%d')
            gap = (this_date - last_date).days
            major_shift = (current_epoch['categories']['feature'] > 5 and commit['category'] == 'refactor')
            
            if gap > 30 or major_shift:
                epochs.append(self._finalize_epoch(current_epoch))
                current_epoch = {
                    'start': commit['date'],
                    'end': commit['date'],
                    'commits': [],
                    'authors': set(),
                    'categories': defaultdict(int)
                }
            
            current_epoch['commits'].append(commit)
            current_epoch['end'] = commit['date']
            current_epoch['authors'].add(commit['author'])
            current_epoch['categories'][commit['category']] += 1
        
        epochs.append(self._finalize_epoch(current_epoch))
        return epochs
    
    def _finalize_epoch(self, epoch):
        total = len(epoch['commits'])
        categories = dict(epoch['categories'])
        dominant = max(categories, key=categories.get)
        first_msg = epoch['commits'][0]['message'][:50] if epoch['commits'] and total > 0 else "Unknown"
        mood = {
            'feature': 'Building',
            'fix': 'Stabilizing', 
            'refactor': 'Restructuring',
            'test': 'Hardening',
            'docs': 'Documenting'
        }.get(dominant, 'Maintaining')
        
        return {
            'start': epoch['start'],
            'end': epoch['end'],
            'duration_days': (datetime.strptime(epoch['end'], '%Y-%m-%d') - datetime.strptime(epoch['start'], '%Y-%m-%d')).days,
            'commit_count': total,
            'authors': list(epoch['authors']),
            'dominant_activity': dominant,
            'mood': mood,
            'first_commit': first_msg,
            'activity_breakdown': categories
        }
    
    def generate_timeline_mermaid(self):
        if not self.epochs:
            return "No git history available"
        mermaid = ["gantt", "    title Project Evolution Timeline", "    dateFormat YYYY-MM-DD"]
        for i, epoch in enumerate(self.epochs):
            section = f"Epoch {i+1}: {epoch['mood']}"
            task = f"{epoch['dominant_activity']} :{epoch['start']}, {epoch['end']}"
            mermaid.append(f"    {section}")
            mermaid.append(f"    {task}")
        return '\n'.join(mermaid)
    
    def generate_narrative(self):
        if not self.epochs:
            return "No git history available for narrative generation."
        narrative = ["# Project Legacy Timeline\n"]
        for i, epoch in enumerate(self.epochs):
            narrative.append(f"## Epoch {i+1}: {epoch['mood']} ({epoch['start']} → {epoch['end']})")
            narrative.append(f"**Duration:** {epoch['duration_days']} days | **Commits:** {epoch['commit_count']} | **Authors:** {', '.join(epoch['authors'][:3])}")
            narrative.append(f"**Vibe:** {epoch['mood']} | **Focus:** {epoch['dominant_activity']}")
            narrative.append(f"**Started with:** {epoch['first_commit']}")
            narrative.append(f"**Activity mix:** {dict(epoch['activity_breakdown'])}")
            narrative.append("")
            if epoch['duration_days'] > 60:
                narrative.append("_Long epoch suggests sustained effort or blockage._")
            if len(epoch['authors']) == 1:
                narrative.append("_Solo work - knowledge silo risk._")
            if epoch['activity_breakdown'].get('fix', 0) > epoch['commit_count'] * 0.5:
                narrative.append("_High fix rate suggests instability or bug debt._")
            narrative.append("---\n")
        
        if len(self.epochs) > 1:
            recent = self.epochs[-1]
            if recent['mood'] == 'Stabilizing':
                narrative.append("## Current Trajectory: Stabilization Mode")
                narrative.append("Recent focus on fixes suggests feature-complete or maintenance phase.")
            elif recent['mood'] == 'Building':
                narrative.append("## Current Trajectory: Active Development")
                narrative.append("Continued feature work indicates growth phase.")
        
        return '\n'.join(narrative)

if __name__ == '__main__':
    import sys
    from pathlib import Path
    repo = sys.argv[1] if len(sys.argv) > 1 else '.'
    archaeologist = GitArchaeologist(repo)
    epochs = archaeologist.excavate()
    if epochs:
        print(f"Detected {len(epochs)} epochs")
        narrative = archaeologist.generate_narrative()
        print(narrative)
        docs = Path(repo) / 'docs' / 'diagrams'
        docs.mkdir(parents=True, exist_ok=True)
        with open(docs / 'git_timeline.mmd', 'w') as f:
            f.write(archaeologist.generate_timeline_mermaid())
        with open(Path(repo) / 'docs' / '05-LEGACY_TIMELINE.md', 'w') as f:
            f.write(narrative)
        print(f"\nTimeline saved to {docs / 'git_timeline.mmd'}")
    else:
        print("No git history found")
