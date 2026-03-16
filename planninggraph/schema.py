"""
Pydantic models for all node and edge types in the decision graph.

Node types:  Objective, Requirement, Assumption, Decision, Component, Interface, Risk
Edge types:  motivated_by, assumes, implements, depends_on,
             conflicts_with, invalidates, exposes, consumes
"""

from __future__ import annotations

import uuid
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


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


class EdgeType(str, Enum):
    MOTIVATED_BY = "motivated_by"
    ASSUMES = "assumes"
    IMPLEMENTS = "implements"
    DEPENDS_ON = "depends_on"
    CONFLICTS_WITH = "conflicts_with"
    INVALIDATES = "invalidates"
    EXPOSES = "exposes"
    CONSUMES = "consumes"


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
    type: NodeType = NodeType.OBJECTIVE


class Requirement(Node):
    type: NodeType = NodeType.REQUIREMENT
    is_functional: bool = True


class Assumption(Node):
    type: NodeType = NodeType.ASSUMPTION
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    validated: bool = False


class Decision(Node):
    type: NodeType = NodeType.DECISION
    rationale: str = ""
    alternatives_considered: list[str] = Field(default_factory=list) # not sure what elements of the list should look like


class Component(Node):
    type: NodeType = NodeType.COMPONENT
    file_refs: list[str] = Field(default_factory=list)


class Interface(Node):
    type: NodeType = NodeType.INTERFACE
    contract: str = ""


class Risk(Node):
    type: NodeType = NodeType.RISK
    severity: float = Field(default=0.5, ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Graph snapshot (for serialization)
# ---------------------------------------------------------------------------

class DecisionGraph(BaseModel):
    nodes: list[Node] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
