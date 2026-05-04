"""
Expand planning docs training dataset with diverse document types.
Generates more comprehensive training examples for the universal graph extractor.
"""

import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def create_adr_example():
    """Architecture Decision Record example."""
    graph = {
        "nodes": [
            {
                "id": "obj_scalable_api",
                "type": "objective",
                "label": "Build scalable API",
                "description": "Design an API that can handle 10k requests/second."
            },
            {
                "id": "req_low_latency",
                "type": "requirement",
                "label": "Sub-100ms latency",
                "description": "All API responses must complete within 100ms at p99.",
                "is_functional": True
            },
            {
                "id": "dec_microservices",
                "type": "decision",
                "label": "Use microservices architecture",
                "description": "Decompose monolith into independent services.",
                "rationale": "Enables independent scaling and deployment.",
                "alternatives_considered": ["Monolithic architecture", "Serverless functions"]
            },
            {
                "id": "dec_cache_layer",
                "type": "decision",
                "label": "Add Redis cache layer",
                "description": "Cache frequently accessed data.",
                "rationale": "Reduces database load, improves latency.",
                "alternatives_considered": ["Memcached", "Application-level caching"]
            },
            {
                "id": "comp_api_gateway",
                "type": "component",
                "label": "API Gateway",
                "description": "Central entry point for all API requests."
            },
            {
                "id": "comp_user_service",
                "type": "component",
                "label": "User Service",
                "description": "Handles user management and authentication."
            },
            {
                "id": "asm_db_scaling",
                "type": "assumption",
                "label": "Database can scale horizontally",
                "description": "Assumes database sharding is feasible.",
                "confidence": 0.75,
                "validated": False
            },
            {
                "id": "risk_cache_invalidation",
                "type": "risk",
                "label": "Cache invalidation complexity",
                "description": "Keeping cache consistent with database is complex.",
                "severity": 0.6
            }
        ],
        "edges": [
            {"source_id": "comp_api_gateway", "target_id": "obj_scalable_api", "type": "motivated_by"},
            {"source_id": "dec_microservices", "target_id": "obj_scalable_api", "type": "motivated_by"},
            {"source_id": "dec_cache_layer", "target_id": "req_low_latency", "type": "implements"},
            {"source_id": "risk_cache_invalidation", "target_id": "dec_cache_layer", "type": "conflicts_with"},
            {"source_id": "comp_user_service", "target_id": "comp_api_gateway", "type": "depends_on"}
        ]
    }
    
    return {
        "meta": {
            "frameworks": ["microservices", "api", "caching"],
            "directive": "extract architecture decisions for scalable API",
            "risk_profile": "medium",
            "complexity_estimate": "high",
            "bounds": {"response_mode": "structured_json"}
        },
        "repo_context": "System needs to handle high-scale API requests. Current monolith has latency issues. Team exploring microservices + caching to improve performance.",
        "user_query": "Document all decisions, requirements, risks, and assumptions for the API redesign. Include services and their dependencies.",
        "target": json.dumps(graph),
        "source": {"type": "adr", "document_type": "architecture_decision_record"}
    }


def create_rfc_example():
    """Request for Comments style document."""
    graph = {
        "nodes": [
            {
                "id": "obj_real_time_collab",
                "type": "objective",
                "label": "Real-time collaboration",
                "description": "Enable multiple users to edit documents simultaneously."
            },
            {
                "id": "req_conflict_resolution",
                "type": "requirement",
                "label": "Automatic conflict resolution",
                "description": "System must resolve concurrent edits automatically.",
                "is_functional": True
            },
            {
                "id": "dec_crdt_algorithm",
                "type": "decision",
                "label": "Use CRDT algorithm",
                "description": "Implement Conflict-free Replicated Data Type.",
                "rationale": "CRDTs guarantee eventual consistency without centralized coordination.",
                "alternatives_considered": ["Operational Transformation", "Lock-based coordination"]
            },
            {
                "id": "comp_sync_engine",
                "type": "component",
                "label": "Sync Engine",
                "description": "Synchronizes document state across clients."
            },
            {
                "id": "asm_network_reliability",
                "type": "assumption",
                "label": "Network is eventually reliable",
                "description": "Assumes network doesn't partition indefinitely.",
                "confidence": 0.85,
                "validated": False
            },
            {
                "id": "risk_large_documents",
                "type": "risk",
                "label": "Performance with large documents",
                "description": "CRDT overhead may degrade with document size.",
                "severity": 0.7
            },
            {
                "id": "tst_conflict_resolution",
                "type": "test",
                "label": "Conflict resolution tests",
                "description": "Unit tests for concurrent edit scenarios.",
                "test_type": "unit",
                "status": "planned"
            }
        ],
        "edges": [
            {"source_id": "comp_sync_engine", "target_id": "obj_real_time_collab", "type": "motivated_by"},
            {"source_id": "dec_crdt_algorithm", "target_id": "req_conflict_resolution", "type": "implements"},
            {"source_id": "risk_large_documents", "target_id": "dec_crdt_algorithm", "type": "conflicts_with"},
            {"source_id": "tst_conflict_resolution", "target_id": "comp_sync_engine", "type": "verifies"}
        ]
    }
    
    return {
        "meta": {
            "frameworks": ["crdt", "realtime", "collaboration"],
            "directive": "extract design decisions for real-time collaboration",
            "risk_profile": "medium",
            "complexity_estimate": "high",
            "bounds": {"response_mode": "structured_json"}
        },
        "repo_context": "Building collaborative document editing platform. Need to support simultaneous edits without conflicts. Considering CRDT-based approach.",
        "user_query": "Extract all design objectives, requirements, decisions, components, and risks. Include testing strategy.",
        "target": json.dumps(graph),
        "source": {"type": "rfc", "document_type": "design_proposal"}
    }


def create_database_schema_example():
    """Database design and schema planning."""
    graph = {
        "nodes": [
            {
                "id": "obj_efficient_queries",
                "type": "objective",
                "label": "Efficient analytical queries",
                "description": "Support complex analytical queries on billion-row tables."
            },
            {
                "id": "req_query_performance",
                "type": "requirement",
                "label": "Sub-second query latency",
                "description": "Analytical queries must complete in < 1 second.",
                "is_functional": True
            },
            {
                "id": "dec_columnar_storage",
                "type": "decision",
                "label": "Use columnar storage format",
                "description": "Store data in columnar format (Parquet/ORC).",
                "rationale": "Columnar format optimizes for analytical queries over row format.",
                "alternatives_considered": ["Row-based storage", "Hybrid storage"]
            },
            {
                "id": "dec_partitioning_strategy",
                "type": "decision",
                "label": "Partition by date",
                "description": "Partition tables by date for efficient pruning.",
                "rationale": "Date-based partitioning enables partition pruning and improves query performance.",
                "alternatives_considered": ["No partitioning", "Hash-based partitioning"]
            },
            {
                "id": "comp_etl_pipeline",
                "type": "component",
                "label": "ETL Pipeline",
                "description": "Transforms raw data to columnar format."
            },
            {
                "id": "iface_schema_contract",
                "type": "interface",
                "label": "Table schema contract",
                "description": "Defines column names, types, and constraints.",
                "contract": "{columns: [{name, type, nullable}]}"
            },
            {
                "id": "risk_storage_cost",
                "type": "risk",
                "label": "Storage cost explosion",
                "description": "Columnar storage may increase storage requirements.",
                "severity": 0.5
            }
        ],
        "edges": [
            {"source_id": "dec_columnar_storage", "target_id": "req_query_performance", "type": "implements"},
            {"source_id": "dec_partitioning_strategy", "target_id": "obj_efficient_queries", "type": "motivated_by"},
            {"source_id": "comp_etl_pipeline", "target_id": "iface_schema_contract", "type": "exposes"},
            {"source_id": "risk_storage_cost", "target_id": "dec_columnar_storage", "type": "conflicts_with"}
        ]
    }
    
    return {
        "meta": {
            "frameworks": ["sql", "analytics", "data-warehouse"],
            "directive": "extract database schema and design decisions",
            "risk_profile": "low",
            "complexity_estimate": "medium",
            "bounds": {"response_mode": "structured_json"}
        },
        "repo_context": "Designing data warehouse for analytics. Current row-based queries are slow. Exploring columnar storage with date-based partitioning.",
        "user_query": "Document objectives, requirements, schema decisions, ETL components, and risks. Include interfaces and contracts.",
        "target": json.dumps(graph),
        "source": {"type": "design_spec", "document_type": "database_schema"}
    }


def create_security_planning_example():
    """Security and compliance planning document."""
    graph = {
        "nodes": [
            {
                "id": "obj_data_protection",
                "type": "objective",
                "label": "Protect user data",
                "description": "Ensure user data is encrypted and access controlled."
            },
            {
                "id": "req_encryption_at_rest",
                "type": "requirement",
                "label": "Encryption at rest",
                "description": "All data must be encrypted when stored.",
                "is_functional": True
            },
            {
                "id": "req_encryption_in_transit",
                "type": "requirement",
                "label": "Encryption in transit",
                "description": "All data in transit must use TLS 1.3.",
                "is_functional": True
            },
            {
                "id": "dec_kms_integration",
                "type": "decision",
                "label": "Use AWS KMS",
                "description": "Leverage AWS Key Management Service for key management.",
                "rationale": "KMS provides managed key rotation, audit logging, and compliance.",
                "alternatives_considered": ["Self-managed keys", "Hardware security modules"]
            },
            {
                "id": "dec_tls_enforcement",
                "type": "decision",
                "label": "Enforce TLS 1.3",
                "description": "Require minimum TLS 1.3 for all connections.",
                "rationale": "TLS 1.3 provides strongest security against known vulnerabilities.",
                "alternatives_considered": ["TLS 1.2", "Auto-upgrade strategy"]
            },
            {
                "id": "comp_auth_service",
                "type": "component",
                "label": "Authentication Service",
                "description": "Validates user identity and issues tokens."
            },
            {
                "id": "asm_aws_trustworthy",
                "type": "assumption",
                "label": "AWS KMS is trustworthy",
                "description": "Assumes AWS doesn't have backdoors in KMS.",
                "confidence": 0.95,
                "validated": True
            },
            {
                "id": "risk_key_compromise",
                "type": "risk",
                "label": "Master key compromise",
                "description": "If master key is compromised, all data is at risk.",
                "severity": 0.95
            },
            {
                "id": "tst_encryption_validation",
                "type": "test",
                "label": "Encryption validation tests",
                "description": "Verify all data is encrypted before storage.",
                "test_type": "security",
                "status": "passing"
            }
        ],
        "edges": [
            {"source_id": "comp_auth_service", "target_id": "obj_data_protection", "type": "motivated_by"},
            {"source_id": "dec_kms_integration", "target_id": "req_encryption_at_rest", "type": "implements"},
            {"source_id": "dec_tls_enforcement", "target_id": "req_encryption_in_transit", "type": "implements"},
            {"source_id": "risk_key_compromise", "target_id": "asm_aws_trustworthy", "type": "invalidates"},
            {"source_id": "tst_encryption_validation", "target_id": "comp_auth_service", "type": "verifies"}
        ]
    }
    
    return {
        "meta": {
            "frameworks": ["security", "compliance", "cryptography"],
            "directive": "extract security planning and compliance requirements",
            "risk_profile": "high",
            "complexity_estimate": "high",
            "bounds": {"response_mode": "structured_json"}
        },
        "repo_context": "Building financial platform with strict security requirements. Need to ensure GDPR and SOC2 compliance. Planning encryption strategy.",
        "user_query": "Extract all security objectives, encryption requirements, key management decisions, and risks. Include authentication components and tests.",
        "target": json.dumps(graph),
        "source": {"type": "security_planning", "document_type": "compliance_doc"}
    }


def create_ml_pipeline_example():
    """Machine learning pipeline design."""
    graph = {
        "nodes": [
            {
                "id": "obj_accurate_predictions",
                "type": "objective",
                "label": "Accurate ML predictions",
                "description": "Build ML pipeline with > 95% accuracy on validation set."
            },
            {
                "id": "req_low_latency_inference",
                "type": "requirement",
                "label": "Low inference latency",
                "description": "Model inference must complete in < 100ms.",
                "is_functional": True
            },
            {
                "id": "dec_model_format",
                "type": "decision",
                "label": "Use ONNX for model export",
                "description": "Export models to ONNX format for portability.",
                "rationale": "ONNX enables inference on multiple platforms.",
                "alternatives_considered": ["SavedModel", "CoreML", "PMML"]
            },
            {
                "id": "dec_feature_store",
                "type": "decision",
                "label": "Implement feature store",
                "description": "Centralized feature management and versioning.",
                "rationale": "Feature store ensures consistency between training and serving.",
                "alternatives_considered": ["Inline features", "CSV-based features"]
            },
            {
                "id": "comp_training_pipeline",
                "type": "component",
                "label": "Training Pipeline",
                "description": "Runs periodic model retraining."
            },
            {
                "id": "comp_inference_service",
                "type": "component",
                "label": "Inference Service",
                "description": "Serves trained models for predictions."
            },
            {
                "id": "asm_data_quality",
                "type": "assumption",
                "label": "Training data is high quality",
                "description": "Assumes input data has minimal errors and biases.",
                "confidence": 0.7,
                "validated": False
            },
            {
                "id": "risk_model_drift",
                "type": "risk",
                "label": "Model drift over time",
                "description": "Model performance may degrade as data distribution changes.",
                "severity": 0.8
            }
        ],
        "edges": [
            {"source_id": "comp_training_pipeline", "target_id": "obj_accurate_predictions", "type": "motivated_by"},
            {"source_id": "comp_inference_service", "target_id": "req_low_latency_inference", "type": "implements"},
            {"source_id": "dec_model_format", "target_id": "comp_inference_service", "type": "depends_on"},
            {"source_id": "dec_feature_store", "target_id": "asm_data_quality", "type": "assumes"},
            {"source_id": "risk_model_drift", "target_id": "asm_data_quality", "type": "invalidates"}
        ]
    }
    
    return {
        "meta": {
            "frameworks": ["ml", "python", "tensorflow"],
            "directive": "extract ML pipeline design and decisions",
            "risk_profile": "medium",
            "complexity_estimate": "high",
            "bounds": {"response_mode": "structured_json"}
        },
        "repo_context": "Building recommendation system with ML. Need to balance model accuracy with serving latency. Planning feature store and ONNX export.",
        "user_query": "Document objectives, inference requirements, model export decisions, components, and risks. Include feature management strategy.",
        "target": json.dumps(graph),
        "source": {"type": "ml_design", "document_type": "ml_pipeline_spec"}
    }


def main():
    """Generate expanded planning docs dataset."""
    examples = [
        # Original extraction_system.txt example
        # (would be loaded from create_planning_docs_training_examples if available)
        
        # New diverse examples
        create_adr_example(),
        create_rfc_example(),
        create_database_schema_example(),
        create_security_planning_example(),
        create_ml_pipeline_example(),
    ]
    
    data_dir = project_root / "data"
    data_dir.mkdir(exist_ok=True)
    
    # Save all examples
    output_file = data_dir / "planning_docs_expanded_all.json"
    with open(output_file, "w") as f:
        json.dump(examples, f, indent=2)
    print(f"✓ Created {output_file} ({len(examples)} examples)")
    
    # Split: 70% train, 15% val, 15% test
    import math
    train_count = math.ceil(len(examples) * 0.7)
    val_count = math.ceil(len(examples) * 0.15)
    
    train_split = examples[:train_count]
    val_split = examples[train_count:train_count + val_count]
    test_split = examples[train_count + val_count:]
    
    splits = {
        "train": train_split,
        "val": val_split,
        "test": test_split,
    }
    
    for split_name, split_examples in splits.items():
        output_file = data_dir / f"planning_docs_expanded_{split_name}.json"
        with open(output_file, "w") as f:
            json.dump(split_examples, f, indent=2)
        print(f"✓ Created {output_file} ({len(split_examples)} examples)")
    
    print(f"\nGenerated {len(examples)} diverse planning doc training examples")
    print(f"Train/Val/Test split: {train_count}/{val_count}/{len(test_split)}")
    print("\nFiles created:")
    print(f"  - data/planning_docs_expanded_all.json")
    print(f"  - data/planning_docs_expanded_train.json ({len(train_split)} examples)")
    print(f"  - data/planning_docs_expanded_val.json ({len(val_split)} examples)")
    print(f"  - data/planning_docs_expanded_test.json ({len(test_split)} examples)")


if __name__ == "__main__":
    main()
