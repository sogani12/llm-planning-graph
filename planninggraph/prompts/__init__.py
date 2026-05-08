"""
Prompt template loader.

Prompt templates live as .txt files alongside this package.
Use load_prompt(name) to retrieve a template by filename stem.
"""

from pathlib import Path

PROMPTS_DIR = Path(__file__).parent


def load_prompt(name: str) -> str:
    """Load a prompt template by stem name (without .txt extension)."""
    prompt_path = PROMPTS_DIR / f"{name}.txt"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")
