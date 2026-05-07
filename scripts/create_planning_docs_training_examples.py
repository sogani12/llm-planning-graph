import json
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def create_extraction_system_example():
    ground_truth_graph = {
        "nodes": [
            {
                "id": "obj_structured_planning",
                "type": "objective",
                "label": "Structured decision capture",
                "description": "Capture planning intent in a machine-readable graph format."
            },
            {
                "id": "obj_incremental_refinement",
                "type": "objective",
                "label": "Incremental graph refinement",
                "description": "Build the planning graph incrementally as decisions are made."
            },
            {
                "id": "req_graph_schema",
                "type": "requirement",
                "label": "Formal graph schema",
                "description": "Every node and edge must follow a defined schema with consistent types.",
                "is_functional": True
            },
            {
                "id": "req_node_metadata",
                "type": "requirement",
                "label": "Rich node metadata",
                "description": "Nodes must include id, type, label, description, and type-specific fields.",
                "is_functional": True
            },
            {
                "id": "req_edge_semantics",
                "type": "requirement",
                "label": "Semantic edge relationships",
                "description": "Edges must express clear relationships: motivated_by, assumes, implements, etc.",
                "is_functional": True
            },
            {
                "id": "dec_node_types",
                "type": "decision",
                "label": "Node type taxonomy",
                "description": "Defined 8 node types: objective, requirement, assumption, decision, component, interface, risk, test.",
                "rationale": "Covers all aspects of architecture planning from goals to implementation.",
                "alternatives_considered": ["Flatter taxonomy", "More specialized types"]
            },
            {
                "id": "dec_edge_semantics",
                "type": "decision",
                "label": "11 edge relationship types",
                "description": "Defined edges: motivated_by, assumes, implements, depends_on, conflicts_with, invalidates, exposes, consumes, verifies, guards_against, validates.",
                "rationale": "Enables rich semantic relationships between planning elements.",
                "alternatives_considered": ["Generic edges only", "Fewer edge types"]
            },
            {
                "id": "comp_schema_validator",
                "type": "component",
                "label": "Schema validation system",
                "description": "Validates that all nodes/edges conform to the graph schema.",
                "file_refs": ["planninggraph/schema.py"]
            },
            {
                "id": "comp_graph_extractor",
                "type": "component",
                "label": "Planning graph extractor",
                "description": "Extracts DecisionGraphs from planning documents and conversations.",
                "file_refs": ["planninggraph/extractor.py"]
            },
            {
                "id": "iface_node_schema",
                "type": "interface",
                "label": "Node schema contract",
                "description": "Every node has: id (snake_case), type (enum), label, description, plus type-specific fields.",
                "contract": "{ id, type, label, description, ...type_specific }"
            },
            {
                "id": "iface_edge_schema",
                "type": "interface",
                "label": "Edge schema contract",
                "description": "Every edge has: source_id, target_id, type (relationship semantic).",
                "contract": "{ source_id, target_id, type }"
            },
            {
                "id": "asm_semantic_clarity",
                "type": "assumption",
                "label": "Semantic relationships capture intent",
                "description": "Assumes that edge types (motivated_by, assumes, etc.) sufficiently capture decision rationale.",
                "confidence": 0.85,
                "validated": False
            },
            {
                "id": "asm_extractability",
                "type": "assumption",
                "label": "Graphs extractable from text",
                "description": "Assumes that planning documents contain enough structure to reliably extract nodes and edges.",
                "confidence": 0.7,
                "validated": False
            },
            {
                "id": "risk_ambiguous_relationships",
                "type": "risk",
                "label": "Ambiguous edge relationships",
                "description": "Multiple edge types may apply between the same nodes; ambiguity can lead to inconsistent graphs.",
                "severity": 0.6
            },
            {
                "id": "risk_incomplete_extraction",
                "type": "risk",
                "label": "Incomplete graph extraction",
                "description": "Not all decisions/assumptions may be explicitly stated in planning documents.",
                "severity": 0.7
            },
            {
                "id": "tst_schema_compliance",
                "type": "test",
                "label": "Schema compliance tests",
                "description": "Unit tests that validate extracted graphs conform to the schema.",
                "test_type": "conformance",
                "status": "planned"
            }
        ],
        "edges": [
            {
                "source_id": "comp_graph_extractor",
                "target_id": "obj_structured_planning",
                "type": "motivated_by"
            },
            {
                "source_id": "comp_schema_validator",
                "target_id": "req_graph_schema",
                "type": "implements"
            },
            {
                "source_id": "comp_graph_extractor",
                "target_id": "iface_node_schema",
                "type": "consumes"
            },
            {
                "source_id": "comp_graph_extractor",
                "target_id": "iface_edge_schema",
                "type": "consumes"
            },
            {
                "source_id": "comp_schema_validator",
                "target_id": "comp_graph_extractor",
                "type": "depends_on"
            },
            {
                "source_id": "dec_node_types",
                "target_id": "req_node_metadata",
                "type": "implements"
            },
            {
                "source_id": "dec_edge_semantics",
                "target_id": "req_edge_semantics",
                "type": "implements"
            },
            {
                "source_id": "dec_node_types",
                "target_id": "obj_structured_planning",
                "type": "motivated_by"
            },
            {
                "source_id": "dec_edge_semantics",
                "target_id": "obj_structured_planning",
                "type": "motivated_by"
            },
            {
                "source_id": "risk_ambiguous_relationships",
                "target_id": "dec_edge_semantics",
                "type": "conflicts_with"
            },
            {
                "source_id": "risk_incomplete_extraction",
                "target_id": "asm_extractability",
                "type": "invalidates"
            },
            {
                "source_id": "tst_schema_compliance",
                "target_id": "comp_schema_validator",
                "type": "verifies"
            }
        ]
    }
    repo_context = Path(project_root / "planninggraph" / "prompts" / "extraction_system.txt").read_text()[:2000]
    example = {
        "meta": {
            "frameworks": ["planning", "architecture", "documentation"],
            "directive": "extract planning graph from schema and behavioral rules",
            "risk_profile": "low",
            "complexity_estimate": "medium",
            "bounds": {
                "response_mode": "structured_json",
                "allowed_paths": ["planning/", "schema/", "architecture/"]
            }
        },
        "repo_context": repo_context,
        "user_query": (
            "This document defines a planning graph schema and extraction system. "
            "Extract all objectives, requirements, decisions, components, interfaces, assumptions, and risks. "
            "Include all relationships between them. Represent as a DecisionGraph JSON."
        ),
        "target": json.dumps(ground_truth_graph),
        "source": {
            "type": "planning_documentation",
            "file": "planninggraph/prompts/extraction_system.txt",
            "document_type": "schema_definition"
        }
    }
    return example

def create_planning_doc_training_set():
    examples = []
    ex1 = create_extraction_system_example()
    examples.append(ex1)
    ex2_base = create_extraction_system_example()
    ex2_base["user_query"] = (
        "Design a graph data model that captures: "
        "what a system aims to achieve (objectives), "
        "hard constraints (requirements), "
        "what we assume to be true (assumptions), "
        "explicit design choices (decisions), "
        "concrete modules and services (components), "
        "APIs and boundaries (interfaces), "
        "concerns and failure modes (risks), "
        "and testing artifacts. "
        "Include all relationships between these elements."
    )
    examples.append(ex2_base)
    ex3_base = create_extraction_system_example()
    ex3_base["user_query"] = (
        "From this planning framework, extract: "
        "1) Core architectural decisions "
        "2) Assumed constraints "
        "3) Potential risks and how they relate to decisions "
        "4) Components and their dependencies "
        "5) All explicit requirements"
    )
    examples.append(ex3_base)
    train_count = max(1, len(examples) * 60 // 100)
    val_count = max(1, len(examples) * 20 // 100)
    train_split = examples[:train_count]
    val_split = examples[train_count:train_count + val_count]
    test_split = examples[train_count + val_count:]
    return {
        "all": examples,
        "train": train_split,
        "val": val_split,
        "test": test_split
    }

def main():
    splits = create_planning_doc_training_set()
    data_dir = project_root / "data"
    data_dir.mkdir(exist_ok=True)
    for split_name, examples in splits.items():
        output_file = data_dir / f"planning_docs_training_{split_name}.json"
        with open(output_file, "w") as f:
            json.dump(examples, f, indent=2)
        print(f"✓ Created {output_file} ({len(examples)} examples)")
    print(f"\nGenerated {len(splits['all'])} planning doc training examples")
    print("Files created:")
    print(f"  - data/planning_docs_training_all.json")
    print(f"  - data/planning_docs_training_train.json")
    print(f"  - data/planning_docs_training_val.json")
    print(f"  - data/planning_docs_training_test.json")

if __name__ == "__main__":
    main()
