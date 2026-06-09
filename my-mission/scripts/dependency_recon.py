#!/usr/bin/env python3
"""
🌴 DEPENDENCY RECON v1 - GLOBAL HUSTLER EDITION
Universal dependency sniffer for Python and Node projects.
"""
import os
import sys
import re
from pathlib import Path

def sniff_dependencies(root_dir):
    root_path = Path(root_dir).resolve()
    python_imports = set()
    node_deps = set()
    
    # 1. Scan for Python Imports
    for path in root_path.rglob('*.py'):
        if any(part in {'.venv', 'venv', 'node_modules', '__pycache__'} for part in path.parts):
            continue
        try:
            content = path.read_text(errors='ignore')
            # Basic regex for 'import x' or 'from x import y'
            matches = re.findall(r'^(?:import|from)\s+([\w-]+)', content, re.MULTILINE)
            for m in matches:
                if m not in {'os', 'sys', 'time', 're', 'json', 'uuid', 'abc', 'pathlib', 'typing', 'datetime', 'collections', 'contextlib'}:
                    python_imports.add(m)
        except: continue

    # 2. Check for package.json
    pkg_json = root_path / 'package.json'
    if pkg_json.exists():
        try:
            import json
            data = json.loads(pkg_json.read_text())
            deps = data.get('dependencies', {}).keys()
            dev_deps = data.get('devDependencies', {}).keys()
            node_deps.update(deps)
            node_deps.update(dev_deps)
        except: pass

    # 3. Format Output
    output = []
    output.append(f"┎━─━─━─━─━─━─━─━─━─━─━─━─━─━─━┒")
    output.append(f"  DEPENDENCY RECON: {root_path.name.upper()}")
    output.append(f"┖━─━─━─━─━─━─━─━─━─━─━─━─━─━─━┚\n")

    if python_imports:
        output.append("🐍 PYTHON ECOSYSTEM")
        output.append("Suggested requirements.txt:")
        output.append("-" * 20)
        for dep in sorted(python_imports):
            output.append(dep)
        output.append("-" * 20)
        output.append(f"One-liner: pip install {' '.join(sorted(python_imports))}\n")

    if node_deps:
        output.append("📦 NODE.JS ECOSYSTEM")
        output.append(f"One-liner: npm install {' '.join(sorted(node_deps))}\n")

    if not python_imports and not node_deps:
        output.append("[!] No major dependencies detected. Just pure logic.")

    return "\n".join(output)

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    print(sniff_dependencies(target))
