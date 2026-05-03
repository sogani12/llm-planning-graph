#!/usr/bin/env python
"""
Bootstrap training examples from existing graphs in eval/experiments/.

This is the quick-start approach to get training examples without waiting for
full corpus extraction.
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from prefix_tuning.graph_classifier import classify_graph, build_metadata_from_characteristics
from prefix_tuning.format_training_examples import (
    create_training_example,
    format_training_examples,
    create_train_val_test_splits,
    add_example_from_existing_graphs,
)

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def bootstrap_from_job_copilot():
    """Generate training examples from job_copilot experiment."""
    
    logger.info("="*60)
    logger.info("Bootstrapping training examples from job_copilot")
    logger.info("="*60)
    
    # Load job_copilot graphs
    graph_files = [
        Path("eval/experiments/project_01_job_copilot/condition_b/graph_v1.json"),
        Path("eval/experiments/project_01_job_copilot/condition_b/graph_v2.json"),
    ]
    
    examples = []
    
    for graph_file in graph_files:
        if not graph_file.exists():
            logger.warning(f"Graph file not found: {graph_file}")
            continue
        
        logger.info(f"\nProcessing: {graph_file}")
        
        with open(graph_file, "r") as f:
            graph = json.load(f)
        
        # Classify graph
        characteristics = classify_graph(graph)
        metadata = build_metadata_from_characteristics(characteristics)
        
        logger.info(f"  Graph characteristics:")
        logger.info(f"    - Routing profile: {characteristics.routing_profile}")
        logger.info(f"    - Nodes: {characteristics.node_count}")
        logger.info(f"    - Edges: {characteristics.edge_count}")
        logger.info(f"    - Frameworks: {characteristics.frameworks}")
        logger.info(f"    - Domains: {characteristics.domains}")
        
        # Create training example
        example = {
            "meta": metadata,
            "repo_context": (
                "Job Copilot: An automated job application system.\n"
                "Scrapes job boards (LinkedIn, Wellfound, etc.), filters listings by user profile,\n"
                "generates tailored resumes, and prepares materials for morning review.\n"
                "Runs unattended overnight with full error recovery and bot evasion."
            ),
            "user_query": (
                "Design a comprehensive planning graph for a job application copilot that:\n"
                "1. Scrapes multiple job boards (LinkedIn, Wellfound, etc.)\n"
                "2. Filters listings by user preferences and skills\n"
                "3. Generates tailored PDF resumes for each matching job\n"
                "4. Handles authentication, dynamic pages, bot detection\n"
                "5. Runs unattended overnight with full error recovery\n\n"
                "Capture all objectives, requirements, decisions, and risks."
            ),
            "target": json.dumps(graph),
            "source": {
                "graph_file": str(graph_file),
                "condition": "condition_b" if "condition_b" in str(graph_file) else "unknown",
            }
        }
        
        examples.append(example)
    
    # Create duplicates with slight variations to expand dataset
    # (This is data augmentation: same graph, different queries/contexts)
    augmented_examples = []
    for ex in examples:
        augmented_examples.append(ex)
        
        # Variation 1: More technical query
        ex_var1 = ex.copy()
        ex_var1["user_query"] = (
            "Create a detailed architecture decision graph for a job scraping and resume generation system.\n"
            "Include decisions about: runtime (Python), database (SQLite), automation (Playwright), PDF generation (WeasyPrint).\n"
            "Capture assumptions about scraping legality, error recovery strategies, and bot evasion techniques.\n"
            "Document all risks including rate limiting, authentication failures, and job market changes."
        )
        augmented_examples.append(ex_var1)
        
        # Variation 2: Business-focused query
        ex_var2 = ex.copy()
        ex_var2["user_query"] = (
            "Define the planning graph for a job copilot product.\n"
            "What are the core objectives and requirements?\n"
            "What architectural decisions need to be made?\n"
            "What are the key risks and assumptions?\n"
            "What testing and validation strategies are needed?"
        )
        augmented_examples.append(ex_var2)
    
    examples = augmented_examples
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Created {len(examples)} training examples (with augmentation)")
    logger.info(f"{'='*60}")
    
    # Save training examples
    output_file = Path("data/training_examples.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w") as f:
        json.dump(examples, f, indent=2)
    
    logger.info(f"Saved training examples to: {output_file}")
    
    # Create train/val/test splits
    splits = create_train_val_test_splits(
        examples,
        train_ratio=0.6,  # Smaller train set for small dataset
        val_ratio=0.2,
        test_ratio=0.2,
    )
    
    logger.info(f"\nSplit summary:")
    logger.info(f"  Train: {len(splits['train'])} examples")
    logger.info(f"  Val:   {len(splits['val'])} examples")
    logger.info(f"  Test:  {len(splits['test'])} examples")
    
    return examples, splits


if __name__ == "__main__":
    examples, splits = bootstrap_from_job_copilot()
    
    print("\n" + "="*60)
    print("Bootstrap complete!")
    print("="*60)
    print(f"\nTraining data ready in:")
    print(f"  - data/training_examples.json (all examples)")
    print(f"  - data/training_examples_train.json (60%)")
    print(f"  - data/training_examples_val.json (20%)")
    print(f"  - data/training_examples_test.json (20%)")
    print(f"\nNext steps:")
    print(f"  1. Validate data:    python scripts/validate_training_data.py")
    print(f"  2. Update adapters:  Edit prefix_tuning/common.py")
    print(f"  3. Start training:   python prefix_tuning/train_graph_models.py")
