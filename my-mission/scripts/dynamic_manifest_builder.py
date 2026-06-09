#!/usr/bin/env python3
"""
🌴 MY MISSION: DYNAMIC MANIFEST BUILDER
Generates a live-state technical blueprint for app onboarding.
"""

import os
import datetime
import sys
from pathlib import Path

def get_env_status():
    # Look for common AI keys
    keys = {
        "GROQ_KEYS": [k for k in os.environ if "GROQ" in k],
        "GEMINI_KEYS": [k for k in os.environ if "GEMINI" in k],
        "OPENAI_KEYS": [k for k in os.environ if "OPENAI" in k],
        "ANTHROPIC_KEYS": [k for k in os.environ if "ANTHROPIC" in k]
    }
    status = []
    for platform, found in keys.items():
        status.append(f"| **{platform}** | {'✅ ACTIVE' if found else '❌ MISSING'} | {len(found)} keys detected |")
    return "\n".join(status)

def get_dir_stats():
    # Basic directory inventory
    dirs = [d for d in os.listdir('.') if os.path.isdir(d) and not d.startswith('.')]
    stats = []
    for d in dirs:
        count = len(list(Path(d).rglob('*')))
        stats.append(f"| **{d.upper()}** | {count} items found |")
    return "\n".join(stats)

def build_manifest(target_dir="."):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    os.chdir(target_dir)
    
    manifest = f"""# ┎━─━─━─━─━─━─━─━─━─━─━─━─━─━─━┒
# 🌴 SYNDICATE LIVE MANIFEST
# ┖━─━─━─━─━─━─━─━─━─━─━─━─━─━─━┚
**GENERATED:** {timestamp}
**NODE:** {os.uname().nodename}
**STATUS:** MISSION_READY

---

## ⬛ I. OPERATIONAL API STATUS
| Platform | Status | Intelligence |
| :--- | :--- | :--- |
{get_env_status()}

## ⬛ II. REPOSITORY INVENTORY
| Directory | Volume |
| :--- | :--- |
{get_dir_stats()}

## ⬛ III. TECHNICAL COMMANDS (LOCAL)
*   `analyze`: High-context code review pass.
*   `vacuum`: Universal code merging protocol.
*   `recon`: Dependency and environment sniffing.
*   `strike`: Execute specific mission objective.

## ⬛ IV. ACTIVE ENVIRONMENT
*   **Python:** {sys.version.split()[0]}
*   **Root:** {os.getcwd()}
*   **User:** {os.getlogin() if hasattr(os, 'getlogin') else 'unknown'}

---
**IF FOUND, INITIATE RM -RF IMMEDIATELY // PROPERTY OF THE SYNDICATE**
**4SHO.**
"""
    
    output_path = "SYNDICATE_MANIFEST.md"
    with open(output_path, "w") as f:
        f.write(manifest)
    return output_path

if __name__ == "__main__":
    path = build_manifest()
    print(f"✅ {path} has been manifested.")
