"""
Pydantic models for all node and edge types in the decision graph.

Node types:  Objective, Requirement, Assumption, Decision, Component, Interface, Risk, Test
Edge types:  motivated_by, assumes, implements, depends_on,
             conflicts_with, invalidates, exposes, consumes,
             verifies, guards_against, validates
"""

from __future__ import annotations

import uuid
from enum import Enum
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Discriminator, Field, Tag


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class NodeType(str, Enum):
    OBJECTIVE = "objective"
    REQUIREMENT = "requirement"
    ASSUMPTION = "assumption"
    DECISION = "decision"
    COMPONENT = "component"
    INTERFACE = "interface"
    RISK = "risk"
    TEST = "test"


class EdgeType(str, Enum):
    MOTIVATED_BY   = "motivated_by"
    ASSUMES        = "assumes"
    IMPLEMENTS     = "implements"
    DEPENDS_ON     = "depends_on"
    CONFLICTS_WITH = "conflicts_with"
    INVALIDATES    = "invalidates"
    EXPOSES        = "exposes"
    CONSUMES       = "consumes"
    VERIFIES       = "verifies"
    GUARDS_AGAINST = "guards_against"
    VALIDATES      = "validates"


# ---------------------------------------------------------------------------
# Base models
# ---------------------------------------------------------------------------

class Node(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: NodeType
    label: str
    description: str = ""


class Edge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: EdgeType
    source_id: str
    target_id: str
    rationale: str = ""


# ---------------------------------------------------------------------------
# Concrete node types
# ---------------------------------------------------------------------------

class Objective(Node):
    type: Literal["objective"] = "objective"


class Requirement(Node):
    type: Literal["requirement"] = "requirement"
    is_functional: bool = True


class Assumption(Node):
    type: Literal["assumption"] = "assumption"
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    validated: bool = False


class Decision(Node):
    type: Literal["decision"] = "decision"
    rationale: str = ""
    alternatives_considered: list[str] = Field(default_factory=list)


class Component(Node):
    type: Literal["component"] = "component"
    file_refs: list[str] = Field(default_factory=list)
    has_tests: bool = False


class Interface(Node):
    type: Literal["interface"] = "interface"
    contract: str = ""


class Risk(Node):
    type: Literal["risk"] = "risk"
    severity: float = Field(default=0.5, ge=0.0, le=1.0)


class Test(Node):
    type: Literal["test"] = "test"
    test_type: Literal["unit", "integration", "conformance", "end-to-end", "security"] = "unit"
    status: Literal["planned", "written", "passing", "failing"] = "planned"


AnyNode = Annotated[
    Union[
        Annotated[Objective, Tag("objective")],
        Annotated[Requirement, Tag("requirement")],
        Annotated[Assumption, Tag("assumption")],
        Annotated[Decision, Tag("decision")],
        Annotated[Component, Tag("component")],
        Annotated[Interface, Tag("interface")],
        Annotated[Risk, Tag("risk")],
        Annotated[Test, Tag("test")],
    ],
    Discriminator("type"),
]


# ---------------------------------------------------------------------------
# Graph snapshot (for serialization)
# ---------------------------------------------------------------------------

class DecisionGraph(BaseModel):
    nodes: list[AnyNode] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
