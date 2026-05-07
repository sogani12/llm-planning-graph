import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging
from dataclasses import asdict

logger = logging.getLogger(__name__)

def create_training_example(corpus_file, chunk_idx, chunk_text, graph, metadata, repo_context_prefix = "Repository planning document"):    
    query_templates = {
        "high_risk": "Design a robust system that handles error recovery and failure scenarios.",
        "medium_risk": "Design a system with appropriate error handling and resilience.",
        "low_risk": "Design a straightforward system with basic error handling.",
        "high_complexity": "Create a comprehensive planning document that captures all objectives, requirements, decisions, and risks.",
        "medium_complexity": "Create a planning document that outlines the main objectives, decisions, and key requirements.",
        "low_complexity": "Create a simple planning document with the core objectives and decisions.",
    }
    risk_profile = metadata.get("risk_profile", "medium")
    complexity = metadata.get("complexity_estimate", "medium")
    domains = metadata.get("domains", ["general"])
    frameworks = metadata.get("frameworks", [])
    query = query_templates.get(f"{risk_profile}_risk", query_templates["medium_risk"])
    if "data" in domains:
        query += " Include data pipeline stages and integration points."
    if "backend" in domains:
        query += " Include API design, database schema, and service boundaries."
    if "frontend" in domains:
        query += " Include UI components, state management, and user flows."
    if "infrastructure" in domains:
        query += " Include deployment architecture, scalability, and operational concerns."
    if frameworks:
        framework_str = ", ".join(frameworks[:3])
        query += f" Use {framework_str} for implementation context."
    example = {
        "meta": metadata,
        "repo_context": f"{repo_context_prefix}:\n\n{chunk_text}",
        "user_query": query,
        "target": json.dumps(graph),  # Target is the extracted graph as JSON string
        "source": {
            "corpus_file": corpus_file,
            "chunk_idx": chunk_idx,
        }
    }
    return example


def format_training_examples(extracted_results, output_file = "data/training_examples.json"):
    examples = []
    for result in extracted_results:
        try:
            example = create_training_example(
                corpus_file=result["corpus_file"],
                chunk_idx=result["chunk_idx"],
                chunk_text=result["chunk_text"],
                graph=result["graph"],
                metadata=result["metadata"],
            )
            examples.append(example)
        except Exception as e:
            logger.error(f"Failed to format example from {result['corpus_file']}: {e}")
            continue
    logger.info(f"Formatted {len(examples)} training examples")
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(examples, f, indent=2)
    logger.info(f"Saved training examples to {output_file}")
    return examples

def create_train_val_test_splits(examples, train_ratio = 0.7, val_ratio = 0.15, test_ratio = 0.15, output_dir = "data/"):
    profile_groups = {}
    for ex in examples:
        profile = ex["meta"].get("routing_profile", "default")
        if profile not in profile_groups:
            profile_groups[profile] = []
        profile_groups[profile].append(ex)
    logger.info(f"Distribution of examples by routing profile:")
    for profile, group in profile_groups.items():
        logger.info(f"  {profile}: {len(group)} examples")
    train_examples = []
    val_examples = []
    test_examples = []
    for profile, group in profile_groups.items():
        def get_sort_key(x):
            source = x.get("source", {})
            return source.get("corpus_file") or source.get("graph_file") or ""
        group_sorted = sorted(group, key=get_sort_key)
        n = len(group)
        train_n = int(n * train_ratio)
        val_n = int(n * val_ratio)
        train_examples.extend(group_sorted[:train_n])
        val_examples.extend(group_sorted[train_n:train_n + val_n])
        test_examples.extend(group_sorted[train_n + val_n:])
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    splits = {
        "train": train_examples,
        "val": val_examples,
        "test": test_examples,
    }
    for split_name, split_examples in splits.items():
        output_file = Path(output_dir) / f"training_examples_{split_name}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(split_examples, f, indent=2)
        logger.info(f"Saved {split_name} split ({len(split_examples)} examples) to {output_file}")
    return splits

def add_example_from_existing_graphs(output_file = "data/training_examples.json", graph_files = None):
    if graph_files is None:
        graph_files = list(Path("eval/experiments/").glob("**/graph_*.json"))
    examples = []
    if Path(output_file).exists():
        with open(output_file, "r", encoding="utf-8") as f:
            examples = json.load(f)
        logger.info(f"Loaded {len(examples)} existing examples from {output_file}")
    for graph_file in graph_files:
        try:
            with open(graph_file, "r", encoding="utf-8") as f:
                graph = json.load(f)
            from graph_classifier import classify_graph, build_metadata_from_characteristics
            characteristics = classify_graph(graph)
            metadata = build_metadata_from_characteristics(characteristics)
            example = {
                "meta": metadata,
                "repo_context": f"Extracted planning graph from {graph_file.parent.name}",
                "user_query": "Extract and structure the planning decisions.",
                "target": json.dumps(graph),
                "source": {
                    "graph_file": str(graph_file),
                    "chunk_idx": 0,
                }
            }
            examples.append(example)
            logger.info(f"Added example from {graph_file}")
        except Exception as e:
            logger.error(f"Failed to add example from {graph_file}: {e}")
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(examples, f, indent=2)
    logger.info(f"Saved {len(examples)} total examples to {output_file}")
    return examples

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    examples = add_example_from_existing_graphs()
    print(f"\nCreated {len(examples)} training examples")
