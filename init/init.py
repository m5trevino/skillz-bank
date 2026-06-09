"""
Init Skill Implementation

Analyzes codebase and generates AGENTS.md for AI coding agents.
Uses temporary subagent isolation to avoid context pollution.
"""

import os
import re
from pathlib import Path
from typing import Optional

from .prompts import build_init_prompt


async def run_init(
    work_dir: Optional[str] = None,
    output_file: str = "AGENTS.md",
    extra_instructions: Optional[str] = None,
    agent_model: str = "kimi"
) -> dict:
    """
    Run init analysis on a project directory.
    
    Creates a temporary subagent to explore the codebase in isolation,
    generates an AGENTS.md file, and returns the result.
    
    Args:
        work_dir: Project directory to analyze (default: current working directory)
        output_file: Output file name (default: AGENTS.md)
        extra_instructions: Additional prompt instructions
        agent_model: Model to use for the exploration subagent
    
    Returns:
        dict with keys:
        - success: bool - Whether AGENTS.md was created
        - output_file: str - Path to the output file
        - content: str - Content of the generated file
        - summary: str - Brief summary of findings
    
    Example:
        >>> result = await run_init()
        >>> print(result["summary"])
        "Analyzed 42 Python files, 5 config files"
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
    prompt = build_init_prompt(
        work_dir=str(work_dir),
        output_file=output_file,
        extra_instructions=extra_instructions
    )
    
    # Create and run temporary subagent for isolated exploration
    # This prevents exploration tool calls from cluttering the main conversation
    try:
        # Delegate to subagent for exploration
        # The subagent will use tools to explore and write the output file
        from kimi_cli.tools import Agent
        
        subagent_result = await Agent(
            description="init-explorer",
            prompt=prompt,
            model=agent_model
        )
        
    except Exception as e:
        # If Agent tool not available, provide manual instructions
        return {
            "success": False,
            "output_file": str(work_dir / output_file),
            "content": "",
            "summary": f"Subagent error: {e}. Manual exploration required."
        }
    
    # Load the generated file
    output_path = work_dir / output_file
    
    if output_path.exists():
        content = output_path.read_text(encoding="utf-8")
        summary = _extract_summary(content)
        
        return {
            "success": True,
            "output_file": str(output_path),
            "content": content,
            "summary": summary
        }
    else:
        return {
            "success": False,
            "output_file": str(output_path),
            "content": "",
            "summary": f"{output_file} was not created. The exploration may have failed."
        }


def _extract_summary(content: str) -> str:
    """
    Extract a brief summary from AGENTS.md content.
    
    Args:
        content: The AGENTS.md content
    
    Returns:
        Brief summary string
    """
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


async def init_slash_command(args: str = "") -> str:
    """
    Slash command handler for /init.
    
    Usage:
        /init              - Analyze current directory
        /init path/to/dir  - Analyze specific directory
        /init --help       - Show help
    
    Args:
        args: Command arguments
    
    Returns:
        Status message for the user
    """
    # Parse arguments
    args = args.strip()
    
    if args in ("--help", "-h", "help"):
        return """
/init - Initialize project analysis

Usage:
  /init              Analyze current working directory
  /init path/to/dir  Analyze specific directory
  /init --help       Show this help

Description:
  Analyzes the project structure and generates AGENTS.md file
  with documentation for AI coding agents.

Example:
  /init
  /init /home/user/myproject
"""
    
    # Determine working directory
    work_dir = args if args else None
    
    # Run init
    result = await run_init(work_dir=work_dir)
    
    if result["success"]:
        # Inject result into conversation context
        # This makes the AGENTS.md available to the main agent
        system_msg = (
            f"The user just ran `/init` command. "
            f"The system has analyzed the codebase and generated an `AGENTS.md` file. "
            f"Latest AGENTS.md file content:\n{result['content']}"
        )
        
        return f"✅ Init complete! {result['summary']}\n\nAGENTS.md saved to: {result['output_file']}"
    else:
        return f"❌ Init failed: {result['summary']}"


# Convenience aliases
init = run_init
analyze = run_init
