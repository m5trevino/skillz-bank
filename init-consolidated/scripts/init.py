#!/usr/bin/env python3
"""
Init Skill - Project Initialization for AI Agents

Analyzes codebase and generates AGENTS.md for AI coding agents.
Pattern: Temporary subagent isolation → Exploration → File generation → Context injection
"""

import os
import re
from pathlib import Path
from typing import Optional


# Load exploration prompt from references
PROMPT_PATH = Path(__file__).parent.parent / "references" / "exploration-prompt.md"
EXPLORATION_PROMPT = PROMPT_PATH.read_text(encoding="utf-8") if PROMPT_PATH.exists() else """
You are a software engineering expert. Please explore the current project directory
to understand the project's architecture and main details.

Task requirements:
1. Analyze the project structure and identify key configuration files
2. Understand the project's technology stack, build process and runtime architecture
3. Identify how the code is organized and main module divisions
4. Discover project-specific development conventions

After the exploration, write a thorough summary to `AGENTS.md` file in the project root.
"""


async def run_init(
    work_dir: Optional[str] = None,
    output_file: str = "AGENTS.md",
    extra_instructions: Optional[str] = None,
) -> dict:
    """
    Run init analysis on a project directory.
    
    Creates a temporary subagent to explore the codebase in isolation,
    generates an AGENTS.md file, and returns the result.
    
    Args:
        work_dir: Project directory to analyze (default: current working directory)
        output_file: Output file name (default: AGENTS.md)
        extra_instructions: Additional prompt instructions
    
    Returns:
        dict with keys:
        - success: bool - Whether AGENTS.md was created
        - output_file: str - Path to the output file
        - content: str - Content of the generated file
        - summary: str - Brief summary of findings
    """
    # Resolve working directory
    work_dir = Path(work_dir or os.getcwd()).resolve()
    
    if not work_dir.exists():
        return {
            "success": False,
            "output_file": str(work_dir / output_file),
            "content": "",
            "summary": f"Error: Working directory does not exist: {work_dir}"
        }
    
    # Build exploration prompt
    prompt = _build_prompt(
        work_dir=str(work_dir),
        output_file=output_file,
        extra_instructions=extra_instructions
    )
    
    # Note: This function is designed to be called from within an agent context
    # where the Agent tool is available. When called standalone, it returns
    # instructions for manual execution.
    return {
        "success": False,
        "output_file": str(work_dir / output_file),
        "content": "",
        "summary": "This script must be run via the Agent tool. Use the skill's /init command instead."
    }


def _build_prompt(
    work_dir: str,
    output_file: str = "AGENTS.md",
    extra_instructions: Optional[str] = None
) -> str:
    """Build the exploration prompt for the subagent."""
    prompt = EXPLORATION_PROMPT.replace(
        "`AGENTS.md` file in the project root",
        f"`{output_file}` file in `{work_dir}`"
    )
    
    if extra_instructions:
        prompt += f"\n\n## Additional Focus Areas\n\n{extra_instructions}\n"
    
    return prompt


def _extract_summary(content: str) -> str:
    """Extract a brief summary from AGENTS.md content."""
    lines = content.strip().split('\n')
    
    # Try to find project name from first heading
    project_name = "Unknown Project"
    for line in lines[:10]:
        if line.startswith('# '):
            project_name = line[2:].strip()
            break
    
    # Count sections
    sections = len([l for l in lines if l.startswith('## ')])
    
    # Estimate file references
    file_refs = len(re.findall(r'`[^`]+\.(py|js|ts|json|toml|yaml|yml|md)`', content))
    
    return f"{project_name}: {sections} sections, ~{file_refs} file references documented"


def load_agents_md(work_dir: Path) -> str:
    """Load the AGENTS.md file from the working directory."""
    agents_md_path = work_dir / "AGENTS.md"
    if agents_md_path.exists():
        return agents_md_path.read_text(encoding="utf-8")
    return ""


if __name__ == "__main__":
    import asyncio
    result = asyncio.run(run_init())
    print(result)
