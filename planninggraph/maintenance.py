"""
Incremental graph update and invalidation propagation.

When a developer introduces a new requirement or a code change invalidates a
prior assumption, this module:
  (a) identifies new nodes/edges to add
  (b) updates attributes of existing nodes
  (c) marks edges as invalidated and traverses the blast radius
"""

# TODO: implement

from planninggraph.graph import PlanningGraph
from planninggraph.schema import DecisionGraph


def apply_update(graph: PlanningGraph, new_text: str) -> dict:
    """
    Process a new dialogue turn or commit message against the current graph.

    Returns a dict with keys:
      added_nodes, added_edges, updated_nodes, invalidated_nodes (blast radius)
    """
    raise NotImplementedError
