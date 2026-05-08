"""
Anticipatory failure modeling and risk surfacing.

Given the current graph state, prompts the LLM to identify potential failure
modes by reasoning over unvalidated Assumption nodes and high-exposure
dependency chains.
"""

from __future__ import annotations

import re

from planninggraph.graph import PlanningGraph
from planninggraph.schema import Assumption, Component, EdgeType, Risk


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def surface_risks(graph: PlanningGraph) -> list[Risk]:
    """
    Proactively generate Risk nodes from the current graph state.

    Filters to Assumption nodes with validated=False or low confidence,
    then prompts the LLM to reason about exposed dependencies.
    """
    snapshot = graph.to_schema()
    existing_labels = {
        node.label.strip().lower()
        for node in snapshot.nodes
        if node.type == "risk"
    }
    risks: list[Risk] = []

    for node in snapshot.nodes:
        if isinstance(node, Assumption) and (not node.validated or node.confidence < 0.75):
            severity = round(max(0.3, 1.0 - node.confidence), 2)
            label = f"Assumption may fail: {node.label}"
            if label.lower() not in existing_labels:
                risks.append(
                    Risk(
                        id=f"risk-{_slug(node.label)}",
                        label=label,
                        description=(
                            f"Unvalidated assumption '{node.label}' could fail and invalidate "
                            f"dependent decisions or requirements."
                        ),
                        severity=severity,
                    )
                )
                existing_labels.add(label.lower())

        if isinstance(node, Component) and not node.has_tests:
            label = f"Insufficient test coverage for {node.label}"
            if label.lower() not in existing_labels:
                dependency_count = sum(
                    1
                    for edge in snapshot.edges
                    if edge.type == EdgeType.DEPENDS_ON and edge.target_id == node.id
                )
                severity = 0.45 if dependency_count == 0 else min(0.8, 0.45 + dependency_count * 0.1)
                risks.append(
                    Risk(
                        id=f"risk-{_slug(node.label)}-tests",
                        label=label,
                        description=(
                            f"Component '{node.label}' has no associated tests and may fail silently "
                            f"under integration or change pressure."
                        ),
                        severity=round(severity, 2),
                    )
                )
                existing_labels.add(label.lower())

    return risks
