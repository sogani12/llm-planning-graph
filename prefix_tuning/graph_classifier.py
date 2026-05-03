"""
Classify decision graphs by characteristics (risk profile, complexity, domains, frameworks).

Enables routing of graphs to specialized prefix-tuned adapters based on graph structure.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import re


@dataclass
class GraphCharacteristics:
    """Characteristics of a decision graph for adapter routing."""
    
    # Risk classification
    risk_profile: str  # "low", "medium", "high"
    risk_score: float  # 0.0-1.0, based on risk node count and severity
    
    # Complexity estimation
    complexity_score: float  # 0.0-1.0, based on node count, edge density, decision diversity
    complexity_level: str  # "low", "medium", "high"
    
    # Domain/framework inference
    frameworks: List[str] = field(default_factory=list)  # ["python", "react", "sql", "docker", ...]
    domains: List[str] = field(default_factory=list)  # ["backend", "frontend", "data", "infrastructure", ...]
    
    # Structural features
    node_count: int = 0
    edge_count: int = 0
    decision_count: int = 0
    assumption_count: int = 0
    risk_count: int = 0
    requirement_count: int = 0
    
    # Routing profile (derived)
    routing_profile: str = ""  # "high_risk_backend", "low_complexity_frontend", etc.
    
    # Confidence in classification
    confidence: float = 1.0


def extract_frameworks_from_text(text: str) -> List[str]:
    """Extract framework/technology mentions from text content."""
    frameworks = set()
    
    # Technology keywords
    tech_patterns = {
        "python": r"\bpython\b",
        "typescript": r"\btypescript\b|\bts\b",
        "javascript": r"\bjavascript\b|\bjs\b",
        "react": r"\breact\b",
        "nodejs": r"\bnode\.?js\b|node",
        "sql": r"\bsql\b",
        "postgresql": r"\bpostgres\b|\bpg\b",
        "sqlite": r"\bsqlite\b",
        "mongodb": r"\bmongo\b",
        "docker": r"\bdocker\b",
        "kubernetes": r"\bk8s\b|kubernetes",
        "go": r"\bgo\b(?!ing|od|al)",
        "rust": r"\brust\b",
        "java": r"\bjava\b",
        "csharp": r"\bc#\b|\.net",
        "aws": r"\baws\b|lambda|s3\b",
        "gcp": r"\bgcp\b|bigquery",
        "azure": r"\bazure\b",
        "graphql": r"\bgraphql\b",
        "rest": r"\brest(?:ful)?\b",
        "grpc": r"\bgrpc\b",
    }
    
    text_lower = text.lower()
    for tech, pattern in tech_patterns.items():
        if re.search(pattern, text_lower, re.IGNORECASE):
            frameworks.add(tech)
    
    return sorted(list(frameworks))


def infer_domain_from_nodes(nodes: List[Dict[str, Any]]) -> List[str]:
    """Infer domain/tier from node labels and descriptions."""
    domains = set()
    all_text = " ".join([
        node.get("label", "") + " " + node.get("description", "")
        for node in nodes
    ]).lower()
    
    # Domain keywords
    domain_patterns = {
        "backend": r"\b(?:backend|server|api|service|microservice|database|persistence)\b",
        "frontend": r"\b(?:frontend|ui|ux|react|vue|angular|client|web|browser)\b",
        "data": r"\b(?:data|pipeline|etl|analytics|ml|machine learning|bigquery|warehouse)\b",
        "infrastructure": r"\b(?:infrastructure|devops|deploy|kubernetes|docker|cloud|terraform)\b",
        "auth": r"\b(?:auth|security|encryption|ssl|tls|oauth|jwt)\b",
        "integration": r"\b(?:integration|sync|replicate|webhook|event)\b",
    }
    
    for domain, pattern in domain_patterns.items():
        if re.search(pattern, all_text):
            domains.add(domain)
    
    # If no domains found, return generic
    if not domains:
        domains.add("general")
    
    return sorted(list(domains))


def classify_graph(graph: Dict[str, Any]) -> GraphCharacteristics:
    """
    Classify a decision graph by its structure and content.
    
    Args:
        graph: Dict with 'nodes' and 'edges' keys (standard DecisionGraph format)
    
    Returns:
        GraphCharacteristics with routing profile and scores
    """
    
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    
    # Count node types
    node_type_counts = {}
    for node in nodes:
        ntype = node.get("type", "unknown")
        node_type_counts[ntype] = node_type_counts.get(ntype, 0) + 1
    
    decision_count = node_type_counts.get("decision", 0)
    assumption_count = node_type_counts.get("assumption", 0)
    risk_count = node_type_counts.get("risk", 0)
    requirement_count = node_type_counts.get("requirement", 0)
    objective_count = node_type_counts.get("objective", 0)
    
    node_count = len(nodes)
    edge_count = len(edges)
    
    # Complexity scoring
    # Factors: node count, edge density, decision diversity
    complexity_score = min(
        1.0,
        (node_count / 50) * 0.5 +  # normalized node count
        (edge_count / 60 if node_count > 0 else 0) * 0.3 +  # edge density
        (decision_count / 10) * 0.2  # decision diversity
    )
    
    if complexity_score < 0.33:
        complexity_level = "low"
    elif complexity_score < 0.67:
        complexity_level = "medium"
    else:
        complexity_level = "high"
    
    # Risk profiling
    # Factors: number of risk nodes, mention of risk keywords in assumptions
    risk_score = min(1.0, risk_count / 5)  # normalize: 5+ risks = 1.0
    
    # Check for risk keywords in assumptions and decisions
    risk_keywords = ["error", "failure", "recovery", "resilience", "fault", "crash", "timeout", "retry"]
    for node in nodes:
        if node.get("type") in ["assumption", "decision", "requirement"]:
            text = (node.get("label", "") + " " + node.get("description", "")).lower()
            if any(kw in text for kw in risk_keywords):
                risk_score = min(1.0, risk_score + 0.15)
    
    if risk_score < 0.33:
        risk_profile = "low"
    elif risk_score < 0.67:
        risk_profile = "medium"
    else:
        risk_profile = "high"
    
    # Extract text for framework/domain inference
    all_text = " ".join([
        node.get("label", "") + " " + node.get("description", "") + " " + 
        node.get("rationale", "")
        for node in nodes
    ])
    
    frameworks = extract_frameworks_from_text(all_text)
    domains = infer_domain_from_nodes(nodes)
    
    # Derive routing profile
    # e.g., "high_risk_backend", "low_complexity_frontend"
    profile_parts = [risk_profile, complexity_level]
    if domains:
        profile_parts.append(domains[0])  # primary domain
    routing_profile = "_".join(profile_parts)
    
    characteristics = GraphCharacteristics(
        risk_profile=risk_profile,
        risk_score=risk_score,
        complexity_score=complexity_score,
        complexity_level=complexity_level,
        frameworks=frameworks,
        domains=domains,
        node_count=node_count,
        edge_count=edge_count,
        decision_count=decision_count,
        assumption_count=assumption_count,
        risk_count=risk_count,
        requirement_count=requirement_count,
        routing_profile=routing_profile,
        confidence=0.8 if node_count > 10 else 0.5,  # higher confidence for larger graphs
    )
    
    return characteristics


def build_metadata_from_characteristics(chars: GraphCharacteristics) -> Dict[str, Any]:
    """
    Convert GraphCharacteristics into router metadata format.
    
    Returns dict suitable for use in training examples.
    """
    return {
        "frameworks": chars.frameworks if chars.frameworks else ["general"],
        "directive": "extract planning graph",
        "domain": chars.domains[0] if chars.domains else "general",
        "risk_profile": chars.risk_profile,
        "complexity_estimate": chars.complexity_level,
        "bounds": {
            "response_mode": "structured_json",
            "allowed_paths": ["planning/", "architecture/", "design/"],
        }
    }
