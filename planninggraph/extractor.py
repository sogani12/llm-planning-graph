"""
LLM-based decision graph extraction from unstructured text.

Given a developer-AI conversation or project document, prompts Claude to extract
nodes and edges according to the schema in schema.py.

Usage (automated, requires ANTHROPIC_API_KEY):
    from planninggraph.extractor import extract_graph
    graph = extract_graph(text)

Usage (manual, no API key needed):
    Print the system prompt with print_extraction_prompt(), paste it into a Claude
    chat session as the system prompt, then paste your text as the user message.
    Copy the JSON response and load it with DecisionGraph.model_validate_json(json_str).
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from planninggraph.schema import DecisionGraph

_PROMPTS_DIR = Path(__file__).parent / "prompts"
_SYSTEM_PROMPT_PATH = _PROMPTS_DIR / "extraction_system.txt"


def _load_system_prompt() -> str:
    return _SYSTEM_PROMPT_PATH.read_text()


def print_extraction_prompt() -> None:
    """Print the system prompt for manual use in a Claude chat session."""
    print("=" * 70)
    print("EXTRACTION SYSTEM PROMPT")
    print("Copy everything below this line into the System Prompt field:")
    print("=" * 70)
    print(_load_system_prompt())


def _parse_graph(raw: str) -> DecisionGraph:
    """Parse raw LLM response into a DecisionGraph, stripping markdown if present."""
    # Strip markdown code fences if the model wrapped the JSON
    clean = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    clean = re.sub(r"\s*```$", "", clean.strip())
    return DecisionGraph.model_validate(json.loads(clean))


def extract_graph(text: str, model: str = "claude-sonnet-4-6") -> DecisionGraph:
    """
    Extract a DecisionGraph from unstructured text via the Anthropic API.

    Requires ANTHROPIC_API_KEY to be set in the environment.
    If the key is not set, raises EnvironmentError with instructions for manual use.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY is not set.\n"
            "To extract manually, run:\n"
            "  from planninggraph.extractor import print_extraction_prompt\n"
            "  print_extraction_prompt()\n"
            "Then paste the printed prompt as the system prompt in a Claude chat,\n"
            "paste your text as the user message, and copy the JSON response."
        )

    try:
        import anthropic
    except ImportError:
        raise ImportError("anthropic package not installed. Run: pip install anthropic")

    client = anthropic.Anthropic(api_key=api_key)
    system_prompt = _load_system_prompt()

    def _call(user_content: str) -> str:
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )
        return response.content[0].text

    raw = _call(text)

    # Retry once with a repair prompt if the JSON is invalid
    try:
        return _parse_graph(raw)
    except (json.JSONDecodeError, Exception) as first_err:
        repair_prompt = (
            f"Your previous response was not valid JSON. Error: {first_err}\n\n"
            f"Here is what you returned:\n{raw}\n\n"
            "Please return ONLY valid JSON matching the required schema. "
            "No markdown, no explanation."
        )
        raw2 = _call(repair_prompt)
        return _parse_graph(raw2)
