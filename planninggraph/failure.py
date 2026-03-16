"""
Anticipatory failure modeling and risk surfacing.

Given the current graph state, prompts the LLM to identify potential failure
modes by reasoning over unvalidated Assumption nodes and high-exposure
dependency chains.
"""

# TODO: implement

from planninggraph.graph import PlanningGraph
from planninggraph.schema import Risk


def surface_risks(graph: PlanningGraph) -> list[Risk]:
    """
    Proactively generate Risk nodes from the current graph state.

    Filters to Assumption nodes with validated=False or low confidence,
    then prompts the LLM to reason about exposed dependencies.
    """
    raise NotImplementedError
