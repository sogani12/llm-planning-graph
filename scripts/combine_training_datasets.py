"""
Combine all training datasets for universal adapter training.
Merges job_copilot examples with planning docs examples.
"""

import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def load_json_file(filepath):
    """Safely load JSON file."""
    if not filepath.exists():
        return []
    with open(filepath) as f:
        return json.load(f)


def main():
    """Combine all training datasets."""
    data_dir = project_root / "data"
    
    # Load all datasets
    job_copilot_train = load_json_file(data_dir / "training_examples_train.json")
    job_copilot_val = load_json_file(data_dir / "training_examples_val.json")
    job_copilot_test = load_json_file(data_dir / "training_examples_test.json")
    
    planning_expanded_train = load_json_file(data_dir / "planning_docs_expanded_train.json")
    planning_expanded_val = load_json_file(data_dir / "planning_docs_expanded_val.json")
    planning_expanded_test = load_json_file(data_dir / "planning_docs_expanded_test.json")
    
    # Combine splits
    combined_train = job_copilot_train + planning_expanded_train
    combined_val = job_copilot_val + planning_expanded_val
    combined_test = job_copilot_test + planning_expanded_test
    combined_all = combined_train + combined_val + combined_test
    
    # Save combined datasets
    splits = {
        "all": combined_all,
        "train": combined_train,
        "val": combined_val,
        "test": combined_test,
    }
    
    print("=== Combined Training Datasets ===\n")
    
    for split_name, examples in splits.items():
        if not examples:
            print(f"⚠️  {split_name:6} split is empty")
            continue
            
        output_file = data_dir / f"training_data_combined_{split_name}.json"
        with open(output_file, "w") as f:
            json.dump(examples, f, indent=2)
        
        # Count examples by source
        job_count = sum(1 for ex in examples if "job_copilot" in ex.get("source", {}).get("file", ""))
        planning_count = len(examples) - job_count
        
        print(f"✓ {split_name:6}: {len(examples):2} examples "
              f"(job_copilot: {job_count}, planning_docs: {planning_count})")
        print(f"           → {output_file.name}")
    
    print(f"\n=== Ready for Training ===")
    print(f"\nUse for Phase 2 training:")
    print(f"  uv run python prefix_tuning/train_graph_models.py \\")
    print(f"    --base-model distilgpt2 \\")
    print(f"    --examples data/training_data_combined_train.json \\")
    print(f"    --val-examples data/training_data_combined_val.json")


if __name__ == "__main__":
    main()
