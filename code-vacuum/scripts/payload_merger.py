#!/usr/bin/env python3
"""
🌴 CODE VACUUM v2 - GLOBAL HUSTLER EDITION
Universal codebase merger with aggressive junk filtering.
"""
import os
import sys
from pathlib import Path

# The "Playa" Blacklist - stuff we don't touch
EXCLUDE_DIRS = {
    '.git', '.venv', 'venv', 'node_modules', '__pycache__', 
    '.next', 'dist', 'build', '.cache', 'nanobanana-output',
    '.pytest_cache', '.vscode', '.idea', 'vault' # Vault is forensic, not code
}

EXCLUDE_FILES = {
    'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 
    '.DS_Store', 'peacock.db', 'server.log', 'success_strikes.log', 
    'failed_strikes.log', 'manual_strikes.log'
}

ALLOWED_EXTENSIONS = {
    '.py', '.js', '.ts', '.tsx', '.sh', '.md', '.css', 
    '.html', '.env', '.json', '.yaml', '.yml', '.txt',
    '.sql', '.dockerfile', 'Dockerfile'
}

def vacuum_code(root_dir):
    output = []
    root_path = Path(root_dir).resolve()
    
    # Header for the whole strike
    output.append(f"┎━─━─━─━─━─━─━─━─━─━─━─━─━─━─━┒")
    output.append(f"  VACUUM STRIKE: {root_path.name.upper()}")
    output.append(f"┖━─━─━─━─━─━─━─━─━─━─━─━─━─━─━┚\n")

    for root, dirs, files in os.walk(root_path):
        # Filter directories in-place
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            if file in EXCLUDE_FILES:
                continue
                
            path = Path(root) / file
            
            # Check extension or if it's a known config file
            if path.suffix.lower() in ALLOWED_EXTENSIONS or file in ALLOWED_EXTENSIONS:
                try:
                    content = path.read_text(encoding='utf-8', errors='ignore')
                    rel_path = path.relative_to(root_path)
                    
                    header_line = "━" * (len(str(rel_path)) + 4)
                    if len(header_line) < 40:
                        header_line = "━" * 40
                        
                    output.append(f"┎{header_line}┒")
                    output.append(f"  FILE: {rel_path}")
                    output.append(f"┖{header_line}┚")
                    output.append(content)
                    output.append("\n" + "="*50 + "\n")
                except Exception:
                    continue
                    
    return "\n".join(output)

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    print(vacuum_code(target))
