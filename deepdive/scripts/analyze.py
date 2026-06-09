#!/usr/bin/env python3
import os, sys, json, re, subprocess
from pathlib import Path
from collections import defaultdict
import ast

class ProjectAnalyzer:
    def __init__(self, root_path):
        self.root = Path(root_path).resolve()
        self.files = []
        self.git_history = []
        self.functions = defaultdict(list)
        self.churn_scores = {}
        self.confidence = {}
        
    def scan_structure(self):
        gitignore_patterns = self._load_gitignore()
        for path in self.root.rglob('*'):
            if path.is_file():
                rel_path = path.relative_to(self.root)
                if self._should_ignore(rel_path, gitignore_patterns):
                    continue
                if self._is_source_file(path):
                    self.files.append({
                        'path': str(rel_path),
                        'size': path.stat().st_size,
                        'lines': len(path.read_text().splitlines()),
                        'ext': path.suffix
                    })
        self.confidence['file_scan'] = 95
        
    def _load_gitignore(self):
        gitignore = self.root / '.gitignore'
        if not gitignore.exists():
            return ['node_modules', '.git', '__pycache__', '.env', 'dist', 'build']
        patterns = []
        with open(gitignore) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    patterns.append(line)
        return patterns
    
    def _should_ignore(self, path, patterns):
        path_str = str(path)
        for p in patterns:
            if p in path_str or path_str.startswith(p):
                return True
        return False
    
    def _is_source_file(self, path):
        source_exts = {'.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.rs', '.java', '.rb', '.php', '.c', '.cpp', '.h', '.swift', '.kt', '.scala'}
        return path.suffix in source_exts and path.stat().st_size < 500000
    
    def analyze_git(self):
        try:
            result = subprocess.run(
                ['git', 'log', '--all', '--format=%H|%an|%ae|%ad|%s', '--date=short', '--name-only'],
                cwd=self.root, capture_output=True, text=True
            )
            if result.returncode != 0:
                self.confidence['git_history'] = 0
                return
            commits = result.stdout.split('\n\n')
            file_churn = defaultdict(int)
            for commit in commits:
                lines = commit.strip().split('\n')
                if not lines or not lines[0]:
                    continue
                parts = lines[0].split('|')
                if len(parts) >= 5:
                    self.git_history.append({
                        'hash': parts[0],
                        'author': parts[1],
                        'date': parts[3],
                        'message': parts[4],
                        'files': lines[1:] if len(lines) > 1 else []
                    })
                    for f in lines[1:]:
                        if f.strip():
                            file_churn[f.strip()] += 1
            self.churn_scores = dict(file_churn)
            self.confidence['git_history'] = 90
        except Exception:
            self.confidence['git_history'] = 0
            
    def parse_python_ast(self, file_path):
        try:
            with open(file_path) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    complexity = 1
                    for child in ast.walk(node):
                        if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler, ast.With, ast.Assert, ast.comprehension)):
                            complexity += 1
                        elif isinstance(child, ast.BoolOp):
                            complexity += len(child.values) - 1
                    self.functions[str(file_path)].append({
                        'name': node.name,
                        'line': node.lineno,
                        'complexity': complexity,
                        'calls': [n.func.id for n in ast.walk(node) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
                    })
        except Exception:
            pass
    
    def detect_entry_points(self):
        entry_patterns = [
            r'if __name__ == ["\']__main__["\']',
            r'require\(["\']express["\']\)',
            r'func\s+main\s*\(\s*\)',
            r'public\s+static\s+void\s+main',
            r'ReactDOM\.render',
        ]
        entries = []
        for f in self.files:
            path = self.root / f['path']
            try:
                content = path.read_text()
                for pattern in entry_patterns:
                    if re.search(pattern, content):
                        entries.append(f['path'])
                        break
            except:
                pass
        return entries
    
    def calculate_risk_scores(self):
        risks = {}
        for f in self.files:
            path = f['path']
            complexity = sum(fn['complexity'] for fn in self.functions.get(str(self.root / path), []))
            churn = self.churn_scores.get(path, 0)
            has_test = any(t['path'].startswith('test') or 'test_' in t['path'] or '.test.' in t['path'] or '_test.' in t['path']
                          for t in self.files if path.replace('.py', '') in t['path'] or path.replace('.js', '') in t['path'])
            coverage_factor = 0.5 if has_test else 2.0
            risk = (complexity + 1) * (churn + 1) * coverage_factor
            risks[path] = {'score': min(risk, 100), 'complexity': complexity, 'churn': churn, 'has_tests': has_test}
        return risks
    
    def generate_mermaid_architecture(self):
        entries = self.detect_entry_points()
        core_files = [f for f in self.files if f['path'] in entries or any(x in f['path'] for x in ['main', 'app', 'index', 'server'])]
        mermaid = ["graph TD"]
        for f in core_files[:10]:
            clean_name = f['path'].replace('/', '_').replace('.', '_')
            mermaid.append(f"    {clean_name}[{f['path']}]")
        for i, f1 in enumerate(core_files[:5]):
            for f2 in core_files[i+1:6]:
                if any(dep in f2['path'] for dep in ['util', 'helper', 'lib']):
                    c1 = f1['path'].replace('/', '_').replace('.', '_')
                    c2 = f2['path'].replace('/', '_').replace('.', '_')
                    mermaid.append(f"    {c1} --> {c2}")
        return '\n'.join(mermaid)
    
    def generate_function_map(self):
        mermaid = ["graph LR"]
        all_funcs = []
        for file_path, funcs in self.functions.items():
            for fn in funcs:
                node_id = f"{Path(file_path).stem}_{fn['name']}"
                all_funcs.append((node_id, fn['name'], fn['calls']))
                mermaid.append(f'    {node_id}["{fn["name"]}()"]')
        for node_id, name, calls in all_funcs:
            for call in calls:
                for target_id, target_name, _ in all_funcs:
                    if call == target_name and target_id != node_id:
                        mermaid.append(f"    {node_id} --> {target_id}")
        return '\n'.join(mermaid)
    
    def run_full_analysis(self):
        print("Scanning project structure...")
        self.scan_structure()
        print(f"Found {len(self.files)} source files")
        print("Analyzing git history...")
        self.analyze_git()
        print("Parsing Python files...")
        for f in self.files:
            if f['ext'] == '.py':
                self.parse_python_ast(self.root / f['path'])
        print(f"Found {sum(len(v) for v in self.functions.values())} functions")
        print("Detecting entry points...")
        entries = self.detect_entry_points()
        print(f"Entry points: {entries[:5]}")
        print("Calculating risk scores...")
        risks = self.calculate_risk_scores()
        print("Generating visualizations...")
        arch_mmd = self.generate_mermaid_architecture()
        func_mmd = self.generate_function_map()
        return {
            'files': self.files,
            'functions': dict(self.functions),
            'git_history': self.git_history[:50],
            'entry_points': entries,
            'risk_scores': risks,
            'confidence': self.confidence,
            'diagrams': {'architecture': arch_mmd, 'function_map': func_mmd}
        }

if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    analyzer = ProjectAnalyzer(root)
    results = analyzer.run_full_analysis()
    docs_dir = Path(root) / 'docs'
    docs_dir.mkdir(exist_ok=True)
    with open(docs_dir / '.deepdive_analysis.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Analysis complete. Results in {docs_dir / '.deepdive_analysis.json'}")
