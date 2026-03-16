"""
Prompt template loader.

Prompt templates live as .txt files alongside this package.
Use load_prompt(name) to retrieve a template by filename stem.
"""

# TODO: implement

from pathlib import Path

PROMPTS_DIR = Path(__file__).parent


def load_prompt(name: str) -> str:
    """Load a prompt template by stem name (without .txt extension)."""
    raise NotImplementedError
