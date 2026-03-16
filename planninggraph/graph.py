"""
NetworkX wrapper for the decision graph.

Provides typed add/update/query/traverse operations over an underlying
nx.DiGraph. All public methods accept and return Pydantic models from schema.py.
"""

# TODO: implement

import networkx as nx

from planninggraph.schema import Node, Edge, DecisionGraph


class PlanningGraph:
    """Typed wrapper around a NetworkX directed graph."""

    def __init__(self) -> None:
        self._g: nx.DiGraph = nx.DiGraph()

    # -- Mutation ----------------------------------------------------------

    def add_node(self, node: Node) -> None:
        """Add a node; no-op if id already exists."""
        raise NotImplementedError

    def add_edge(self, edge: Edge) -> None:
        """Add a directed edge between two existing nodes."""
        raise NotImplementedError

    def update_node(self, node_id: str, **kwargs) -> None:
        """Update attributes of an existing node."""
        raise NotImplementedError

    # -- Query -------------------------------------------------------------

    def get_node(self, node_id: str) -> Node:
        raise NotImplementedError

    def neighbors(self, node_id: str) -> list[Node]:
        """Return direct successors of a node."""
        raise NotImplementedError

    def predecessors(self, node_id: str) -> list[Node]:
        raise NotImplementedError

    # -- Traversal ---------------------------------------------------------

    def blast_radius(self, node_id: str) -> list[Node]:
        """Return all nodes reachable from node_id via invalidates edges."""
        raise NotImplementedError

    # -- Serialization -----------------------------------------------------

    def to_schema(self) -> DecisionGraph:
        """Export graph as a Pydantic DecisionGraph snapshot."""
        raise NotImplementedError

    @classmethod
    def from_schema(cls, dg: DecisionGraph) -> "PlanningGraph":
        """Reconstruct a PlanningGraph from a DecisionGraph snapshot."""
        raise NotImplementedError
