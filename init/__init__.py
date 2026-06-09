"""
Init Skill - Project Initialization for AI Agents

Analyzes codebase and generates AGENTS.md for AI coding agents.
Pattern: Temporary subagent isolation → Exploration → File generation → Context injection
"""

from .init import run_init, init_slash_command

__version__ = "1.0.0"
__all__ = ["run_init", "init_slash_command"]
