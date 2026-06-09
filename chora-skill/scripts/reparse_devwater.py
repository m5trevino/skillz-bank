#!/usr/bin/env python3
"""Re-parse June 5-6 sessions into devwater-data directories."""
import json
import sys
sys.path.insert(0, "/home/flintx/chora")
from parsers.kimi_code_parser import parse_kimi_code
from pathlib import Path

sessions_dir = Path.home() / ".kimi-code/sessions"

project_map = {
    "doc-dumpster": Path("/home/flintx/doc-dumpster/devwater-data"),
    "waldo": Path("/home/flintx/waldo/devwater-data"),
    "auto-ats": Path("/home/flintx/auto-ats/devwater-data"),
}

JUN5_START = 1780642800000
JUN6_END = 1780815599000

created = []
skipped = []
errors = []

for pattern, devwater_dir in project_map.items():
    proj_dirs = [d for d in sessions_dir.glob("wd_*") if pattern in d.name]
    
    for proj_dir in proj_dirs:
        for sess_dir in proj_dir.iterdir():
            if not sess_dir.is_dir():
                continue
            if not (sess_dir.name.startswith("session_") or sess_dir.name.startswith("ses_")):
                continue
            
            wire = sess_dir / "agents" / "main" / "wire.jsonl"
            if not wire.exists():
                continue
            
            # Get timestamp
            ts = None
            with open(wire) as f:
                for line in f:
                    try:
                        obj = json.loads(line)
                        ts = obj.get("time") or obj.get("timestamp") or obj.get("created_at")
                        if ts:
                            break
                    except:
                        pass
            
            if not ts or not (JUN5_START <= ts <= JUN6_END):
                continue
            
            basename = sess_dir.name
            
            try:
                chat_path, think_path = parse_kimi_code(
                    sess_dir, output_dir=devwater_dir, min_assistant_chars=100
                )
                # Rename to devwater convention
                new_chat = devwater_dir / f"{basename}-chat.md"
                new_think = devwater_dir / f"{basename}-think.md"
                chat_path.rename(new_chat)
                think_path.rename(new_think)
                
                # Remove empty dated subdirectory
                dated_dir = chat_path.parent
                if dated_dir != devwater_dir:
                    try:
                        dated_dir.rmdir()
                    except OSError:
                        pass
                
                created.append((pattern, basename))
            except RuntimeError as e:
                if "SESSION_EMPTY" in str(e):
                    skipped.append((pattern, basename))
                else:
                    errors.append((pattern, basename, str(e)))
            except Exception as e:
                errors.append((pattern, basename, str(e)))

print(f"CREATED ({len(created)}):")
for proj, sess in created:
    print(f"  {proj}/{sess}")

print(f"\nSKIPPED ({len(skipped)}):")
for proj, sess in skipped:
    print(f"  {proj}/{sess}")

if errors:
    print(f"\nERRORS ({len(errors)}):")
    for proj, sess, err in errors:
        print(f"  {proj}/{sess}: {err}")
