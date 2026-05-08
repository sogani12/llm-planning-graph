"""Shared pytest fixtures."""

import pytest

from planninggraph.schema import (
    Objective, Requirement, Assumption, Decision,
    Component, Interface, Risk, Test, Edge, EdgeType, DecisionGraph,
)
from planninggraph.graph import PlanningGraph


@pytest.fixture
def empty_graph() -> PlanningGraph:
    return PlanningGraph()


@pytest.fixture
def sample_graph() -> PlanningGraph:
    graph = PlanningGraph()
    objective = Objective(id="obj-1", label="Ship feature", description="Deliver the MVP")
    assumption = Assumption(
        id="asm-1",
        label="API remains stable",
        description="Partner API schema does not change",
        confidence=0.6,
        validated=False,
    )
    component = Component(
        id="comp-1",
        label="Sync worker",
        description="Processes remote updates",
        has_tests=False,
    )
    risk = Risk(id="risk-1", label="API drift", description="Schema changes break parsing", severity=0.8)
    for node in (objective, assumption, component, risk):
        graph.add_node(node)
    graph.add_edge(
        Edge(
            id="edge-1",
            type=EdgeType.INVALIDATES,
            source_id="asm-1",
            target_id="comp-1",
            rationale="API drift invalidates sync worker assumptions.",
        )
    )
    graph.add_edge(
        Edge(
            id="edge-2",
            type=EdgeType.INVALIDATES,
            source_id="comp-1",
            target_id="obj-1",
            rationale="Broken sync worker blocks shipment objective.",
        )
    )
    return graph
