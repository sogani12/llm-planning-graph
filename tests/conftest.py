"""Shared pytest fixtures."""

import pytest

from planninggraph.schema import (
    Objective, Requirement, Assumption, Decision,
    Component, Interface, Risk, Edge, EdgeType, DecisionGraph,
)
from planninggraph.graph import PlanningGraph


# TODO: add fixtures as modules are implemented


@pytest.fixture
def empty_graph() -> PlanningGraph:
    return PlanningGraph()
