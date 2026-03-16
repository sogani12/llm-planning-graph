"""
LLM-based graph extraction from unstructured text.

Given a developer-AI conversation or project document (README, issue thread),
prompts an LLM to extract nodes and edges according to the schema defined in
schema.py. Uses structured JSON output with Pydantic validation.

Pipeline stages:
  1. Entity identification + node type classification
  2. Coreference resolution across dialogue turns
  3. Relation extraction + edge type classification
  4. Confidence scoring for Assumption nodes (linguistic hedge detection)
"""

# TODO: implement


def extract_graph(text: str) -> "planninggraph.schema.DecisionGraph":  # noqa: F821
    """Extract a DecisionGraph from unstructured text via LLM."""
    raise NotImplementedError
