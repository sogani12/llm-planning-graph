from __future__ import annotations
import json
import os
import re
from planninggraph.schema import DecisionGraph
_EXTRACTION_PROMPT = """\
You are an expert software architecture analyst. Read the developer–AI planning \
conversation or design document below and extract a structured decision graph from it.

Return ONLY valid JSON in this exact shape — no markdown fences, no explanation:

{
  "nodes": [ ...node objects... ],
  "edges": [ ...edge objects... ]
}

Node types (8): objective, requirement, assumption, decision, component, interface, risk, test
- objective: { id, type, label, description }
- requirement: { id, type, label, description, is_functional }
- assumption: { id, type, label, description, confidence (0-1), validated (bool) }
- decision: { id, type, label, description, rationale, alternatives_considered (list) }
- component: { id, type, label, description, file_refs (list), has_tests (bool) }
- interface: { id, type, label, description, contract }
- risk: { id, type, label, description, severity (0-1) }
- test: { id, type, label, description, test_type, status }

Edge types (11): motivated_by, assumes, implements, depends_on, conflicts_with,
  invalidates, exposes, consumes, verifies, guards_against, validates
Each edge: { id, type, source_id, target_id, rationale (optional) }

Rules:
- Every edge source_id and target_id must match a node id.
- Extract implicit assumptions even when not stated directly.
- Include all significant decisions with rationale and alternatives.
- Include all notable risks with severity.
- Aim for 15–25 nodes. Completeness over brevity.
"""

def print_extraction_prompt():
    """Print the extraction prompt for manual use in a Claude chat session."""
    print("=" * 70)
    print("EXTRACTION PROMPT — paste as system prompt in a Claude chat session")
    print("=" * 70)
    print(_EXTRACTION_PROMPT)


def _parse_graph(raw):
    clean = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    clean = re.sub(r"\s*```$", "", clean.strip())
    return DecisionGraph.model_validate(json.loads(clean))

def extract_graph(text, model = "claude-sonnet-4-6"):
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
    system_prompt = _EXTRACTION_PROMPT
    def _call(user_content):
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )
        return response.content[0].text
    raw = _call(text)
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
