"""
Incremental graph update and invalidation propagation.

When a developer introduces a new requirement or a code change invalidates a
prior assumption, this module:
  (a) identifies new nodes/edges to add
  (b) updates attributes of existing nodes
  (c) marks edges as invalidated and traverses the blast radius
"""

from __future__ import annotations

import json
import re

from planninggraph.graph import PlanningGraph
from planninggraph.schema import (
    Assumption,
    Component,
    Decision,
    DecisionGraph,
    Edge,
    EdgeType,
    Objective,
    Requirement,
    Risk,
    Test,
)

INVALIDATION_HINTS = (
    "invalid",
    "no longer",
    "deprecated",
    "replaced",
    "superseded",
    "obsolete",
)


def _normalize(text: str) -> str:
    return re.sub(r"\W+", " ", text).strip().lower()


def _build_index(graph: PlanningGraph) -> dict[tuple[str, str], str]:
    snapshot = graph.to_schema()
    return {
        (node.type, _normalize(node.label)): node.id
        for node in snapshot.nodes
    }


def _merge_node(
    graph: PlanningGraph,
    node,
    node_index: dict[tuple[str, str], str],
    updated_nodes: list[str],
) -> tuple[str, bool]:
    key = (node.type, _normalize(node.label))
    existing_id = node_index.get(key)
    if existing_id is None:
        graph.add_node(node)
        node_index[key] = node.id
        return node.id, True

    current = graph.get_node(existing_id)
    merged = current.model_dump()
    incoming = node.model_dump(exclude={"id"})
    for field, value in incoming.items():
        if isinstance(value, str) and len(value) > len(str(merged.get(field, ""))):
            merged[field] = value
        elif isinstance(value, bool) and value:
            merged[field] = value
        elif isinstance(value, (int, float)) and value != merged.get(field):
            merged[field] = value
        elif isinstance(value, list) and value:
            merged[field] = sorted(set(merged.get(field, [])) | set(value))
    graph.update_node(existing_id, **merged)
    updated_nodes.append(existing_id)
    return existing_id, False


def _candidate_graph_from_text(new_text: str) -> DecisionGraph:
    stripped = new_text.strip()
    candidates = [stripped]
    fenced_blocks = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, flags=re.DOTALL)
    candidates.extend(fenced_blocks)

    for candidate in candidates:
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and "nodes" in data and "edges" in data:
            return DecisionGraph.model_validate(data)

    try:
        from planninggraph.extractor import extract_graph

        return extract_graph(new_text)
    except Exception:
        return _heuristic_graph_from_text(new_text)


def _heuristic_graph_from_text(new_text: str) -> DecisionGraph:
    node_builders = [
        ("objective", ("objective", "goal", "target"), Objective),
        ("requirement", ("must", "should", "need", "require"), Requirement),
        ("assumption", ("assume", "assuming", "likely"), Assumption),
        ("decision", ("decide", "decision", "choose", "selected", "use "), Decision),
        ("risk", ("risk", "failure", "break", "timeout", "error"), Risk),
        ("test", ("test", "validate", "verify"), Test),
        ("component", ("module", "service", "component", "api", "worker"), Component),
    ]
    sentences = [
        part.strip(" -\t")
        for part in re.split(r"[\n.!?]+", new_text)
        if part.strip()
    ]

    nodes = []
    for sentence in sentences[:12]:
        lowered = sentence.lower()
        for _, keywords, builder in node_builders:
            if any(keyword in lowered for keyword in keywords):
                label = sentence[:80]
                kwargs = {"label": label, "description": sentence}
                if builder is Assumption:
                    kwargs.update({"confidence": 0.6, "validated": False})
                if builder is Decision:
                    kwargs.update({"rationale": "Inferred from update text."})
                if builder is Risk:
                    kwargs.update({"severity": 0.5})
                nodes.append(builder(**kwargs))
                break

    if not nodes and new_text.strip():
        nodes.append(Requirement(label="Incremental update", description=new_text.strip()))

    return DecisionGraph(nodes=nodes, edges=[])


def apply_update(graph: PlanningGraph, new_text: str) -> dict:
    """
    Process a new dialogue turn or commit message against the current graph.

    Returns a dict with keys:
      added_nodes, added_edges, updated_nodes, invalidated_nodes (blast radius)
    """
    extracted = _candidate_graph_from_text(new_text)
    node_index = _build_index(graph)
    added_nodes: list[str] = []
    updated_nodes: list[str] = []
    added_edges: list[str] = []
    invalidated_ids: set[str] = set()
    extracted_id_map: dict[str, str] = {}

    for node in extracted.nodes:
        node_id_before = node.id
        resolved_id, was_added = _merge_node(graph, node, node_index, updated_nodes)
        extracted_id_map[node_id_before] = resolved_id
        if was_added:
            added_nodes.append(resolved_id)

    existing_edges = {
        (
            edge.type,
            edge.source_id,
            edge.target_id,
        ): edge.id
        for edge in graph.to_schema().edges
    }

    for edge in extracted.edges:
        mapped_source = extracted_id_map.get(edge.source_id, edge.source_id)
        mapped_target = extracted_id_map.get(edge.target_id, edge.target_id)
        signature = (edge.type, mapped_source, mapped_target)
        if signature in existing_edges:
            continue
        new_edge = Edge(
            type=edge.type,
            source_id=mapped_source,
            target_id=mapped_target,
            rationale=edge.rationale,
        )
        graph.add_edge(new_edge)
        added_edges.append(new_edge.id)
        existing_edges[signature] = new_edge.id
        if edge.type == EdgeType.INVALIDATES:
            invalidated_ids.add(mapped_target)

    if any(hint in new_text.lower() for hint in INVALIDATION_HINTS):
        invalidated_ids.update(updated_nodes)

    blast_radius_ids: set[str] = set()
    for node_id in invalidated_ids:
        if not node_id:
            continue
        blast_radius_ids.add(node_id)
        for impacted in graph.blast_radius(node_id):
            blast_radius_ids.add(impacted.id)

    return {
        "added_nodes": added_nodes,
        "added_edges": added_edges,
        "updated_nodes": sorted(set(updated_nodes)),
        "invalidated_nodes": sorted(blast_radius_ids),
    }
