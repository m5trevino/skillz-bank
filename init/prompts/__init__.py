"""
Prompt templates for the init skill.
"""

from pathlib import Path

# Load the default init prompt
INIT = (Path(__file__).parent / "init.md").read_text(encoding="utf-8")


def build_init_prompt(
    work_dir: str = None,
    output_file: str = "AGENTS.md",
    extra_instructions: str = None
) -> str:
    """
    Build the init exploration prompt with optional customizations.
    
    Args:
        work_dir: The working directory to analyze
        output_file: Output file name (default: AGENTS.md)
        extra_instructions: Additional instructions to append
    
    Returns:
        Complete prompt string
    """
    prompt = INIT
    
    # Add working directory context if provided
    if work_dir:
        prompt += f"\n\nWorking directory: {work_dir}"
    
    # Override output file if different from default
    if output_file != "AGENTS.md":
        prompt = prompt.replace("`AGENTS.md`", f"`{output_file}`")
        prompt = prompt.replace("AGENTS.md file", f"{output_file} file")
    
    # Add extra instructions
    if extra_instructions:
        prompt += f"\n\nAdditional instructions:\n{extra_instructions}"
    
    return prompt
