"""
Evaluation metrics for decision graph quality.
Could change in the future

  node_recall           — fraction of ground-truth nodes recovered
  edge_precision        — fraction of extracted edges that are correct
  failure_point_recall  — fraction of post-mortem failure points mapped
                          to Risk or Assumption nodes in the extracted graph
"""

from __future__ import annotations

import re

from planninggraph.schema import DecisionGraph


def _normalize(text: str) -> str:
    return re.sub(r"\W+", " ", text or "").strip().lower()


def _node_signature(node) -> tuple[str, str]:
    return (str(node.type), _normalize(node.label))


def node_recall(predicted: DecisionGraph, ground_truth: DecisionGraph) -> float:
    """Fraction of ground-truth nodes present in the predicted graph."""
    if not ground_truth.nodes:
        return 1.0

    predicted_signatures = {_node_signature(node) for node in predicted.nodes}
    ground_truth_signatures = {_node_signature(node) for node in ground_truth.nodes}
    return len(predicted_signatures & ground_truth_signatures) / len(ground_truth_signatures)


def edge_precision(predicted: DecisionGraph, ground_truth: DecisionGraph) -> float:
    """Fraction of predicted edges that appear in the ground truth."""
    if not predicted.edges:
        return 1.0

    predicted_nodes = {node.id: node for node in predicted.nodes}
    truth_nodes = {node.id: node for node in ground_truth.nodes}

    def edge_signature(edge, node_lookup) -> tuple[str, tuple[str, str], tuple[str, str]]:
        return (
            str(edge.type),
            _node_signature(node_lookup[edge.source_id]),
            _node_signature(node_lookup[edge.target_id]),
        )

    predicted_signatures = {
        edge_signature(edge, predicted_nodes)
        for edge in predicted.edges
        if edge.source_id in predicted_nodes and edge.target_id in predicted_nodes
    }
    ground_truth_signatures = {
        edge_signature(edge, truth_nodes)
        for edge in ground_truth.edges
        if edge.source_id in truth_nodes and edge.target_id in truth_nodes
    }
    if not predicted_signatures:
        return 1.0
    return len(predicted_signatures & ground_truth_signatures) / len(predicted_signatures)


def failure_point_recall(
    predicted: DecisionGraph, failure_points: list[str]
) -> float:
    """
    Fraction of documented failure point descriptions that correspond to
    a Risk or Assumption node in the predicted graph.
    """
    if not failure_points:
        return 1.0

    candidate_text = [
        _normalize(f"{node.label} {node.description}")
        for node in predicted.nodes
        if str(node.type) in {"risk", "assumption"}
    ]
    if not candidate_text:
        return 0.0

    matches = 0
    for failure_point in failure_points:
        normalized = _normalize(failure_point)
        if not normalized:
            continue
        tokens = {token for token in normalized.split() if len(token) > 3}
        if any(
            normalized in candidate
            or (tokens and len(tokens & set(candidate.split())) / len(tokens) >= 0.5)
            for candidate in candidate_text
        ):
            matches += 1
    return matches / len(failure_points)
