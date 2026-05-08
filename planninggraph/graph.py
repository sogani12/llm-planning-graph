"""
NetworkX wrapper for the decision graph.

Provides typed add/update/query/traverse operations over an underlying
nx.DiGraph. All public methods accept and return Pydantic models from schema.py.
"""

import networkx as nx

from planninggraph.schema import DecisionGraph, Edge, EdgeType, Node


class PlanningGraph:
    """Typed wrapper around a NetworkX directed graph."""

    def __init__(self) -> None:
        self._g: nx.DiGraph = nx.DiGraph()

    # -- Mutation ----------------------------------------------------------

    def add_node(self, node: Node) -> None:
        """Add a node; no-op if id already exists."""
        if node.id in self._g:
            return
        self._g.add_node(node.id, data=node)

    def add_edge(self, edge: Edge) -> None:
        """Add a directed edge between two existing nodes."""
        if edge.source_id not in self._g or edge.target_id not in self._g:
            raise KeyError(
                f"Cannot add edge {edge.id}: missing node(s) "
                f"{edge.source_id!r} -> {edge.target_id!r}"
            )

        existing = self._g.get_edge_data(edge.source_id, edge.target_id)
        if existing and existing.get("data").id == edge.id:
            return
        self._g.add_edge(edge.source_id, edge.target_id, data=edge)

    def update_node(self, node_id: str, **kwargs) -> None:
        """Update attributes of an existing node."""
        node = self.get_node(node_id)
        updated = node.__class__.model_validate({**node.model_dump(), **kwargs})
        self._g.nodes[node_id]["data"] = updated

    # -- Query -------------------------------------------------------------

    def get_node(self, node_id: str) -> Node:
        if node_id not in self._g:
            raise KeyError(f"Unknown node id: {node_id}")
        return self._g.nodes[node_id]["data"]

    def neighbors(self, node_id: str) -> list[Node]:
        """Return direct successors of a node."""
        if node_id not in self._g:
            raise KeyError(f"Unknown node id: {node_id}")
        return [self.get_node(neighbor_id) for neighbor_id in self._g.successors(node_id)]

    def predecessors(self, node_id: str) -> list[Node]:
        if node_id not in self._g:
            raise KeyError(f"Unknown node id: {node_id}")
        return [self.get_node(pred_id) for pred_id in self._g.predecessors(node_id)]

    # -- Traversal ---------------------------------------------------------

    def blast_radius(self, node_id: str) -> list[Node]:
        """Return all nodes reachable from node_id via invalidates edges."""
        if node_id not in self._g:
            raise KeyError(f"Unknown node id: {node_id}")

        invalidation_graph = nx.DiGraph()
        invalidation_graph.add_nodes_from(self._g.nodes())
        invalidation_graph.add_edges_from(
            (
                source_id,
                target_id,
            )
            for source_id, target_id, payload in self._g.edges(data=True)
            if payload["data"].type == EdgeType.INVALIDATES
        )
        descendants = nx.descendants(invalidation_graph, node_id)
        return [self.get_node(descendant_id) for descendant_id in descendants]

    # -- Serialization -----------------------------------------------------

    def to_schema(self) -> DecisionGraph:
        """Export graph as a Pydantic DecisionGraph snapshot."""
        nodes = [self._g.nodes[node_id]["data"] for node_id in self._g.nodes]
        edges = [
            payload["data"]
            for _, _, payload in self._g.edges(data=True)
        ]
        return DecisionGraph(nodes=nodes, edges=edges)

    @classmethod
    def from_schema(cls, dg: DecisionGraph) -> "PlanningGraph":
        """Reconstruct a PlanningGraph from a DecisionGraph snapshot."""
        graph = cls()
        for node in dg.nodes:
            graph.add_node(node)
        for edge in dg.edges:
            graph.add_edge(edge)
        return graph
