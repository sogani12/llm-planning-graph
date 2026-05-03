"""
Validate training examples and generate statistics report.

Checks:
- Metadata consistency and required fields
- Graph validity (can parse as DecisionGraph)
- Example completeness (all fields present)
- Length distributions
- Balance across routing profiles
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


def validate_example(example: Dict[str, Any], idx: int) -> List[str]:
    """
    Validate a single training example.
    
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Check required fields
    required_fields = ["meta", "repo_context", "user_query", "target"]
    for field in required_fields:
        if field not in example:
            errors.append(f"Example {idx}: missing required field '{field}'")
    
    # Check metadata structure
    if "meta" in example:
        meta = example["meta"]
        meta_required = ["frameworks", "directive", "bounds"]
        for field in meta_required:
            if field not in meta:
                errors.append(f"Example {idx}: meta missing '{field}'")
        
        # Check frameworks is a list
        if "frameworks" in meta and not isinstance(meta["frameworks"], list):
            errors.append(f"Example {idx}: meta.frameworks should be a list")
        
        # Check bounds structure
        if "bounds" in meta and isinstance(meta["bounds"], dict):
            bounds_required = ["response_mode", "allowed_paths"]
            for field in bounds_required:
                if field not in meta["bounds"]:
                    errors.append(f"Example {idx}: meta.bounds missing '{field}'")
    
    # Check target is valid JSON
    if "target" in example:
        try:
            if isinstance(example["target"], str):
                graph = json.loads(example["target"])
            else:
                graph = example["target"]
            
            # Check graph structure
            if "nodes" not in graph:
                errors.append(f"Example {idx}: target graph missing 'nodes'")
            elif not isinstance(graph["nodes"], list):
                errors.append(f"Example {idx}: target graph nodes should be a list")
            
            if "edges" not in graph:
                errors.append(f"Example {idx}: target graph missing 'edges'")
            elif not isinstance(graph["edges"], list):
                errors.append(f"Example {idx}: target graph edges should be a list")
        
        except json.JSONDecodeError as e:
            errors.append(f"Example {idx}: target is not valid JSON: {e}")
    
    # Check field lengths
    if "repo_context" in example:
        if len(example["repo_context"]) < 50:
            errors.append(f"Example {idx}: repo_context too short (< 50 chars)")
        if len(example["repo_context"]) > 10000:
            errors.append(f"Example {idx}: repo_context too long (> 10k chars)")
    
    if "user_query" in example:
        if len(example["user_query"]) < 10:
            errors.append(f"Example {idx}: user_query too short (< 10 chars)")
        if len(example["user_query"]) > 1000:
            errors.append(f"Example {idx}: user_query too long (> 1k chars)")
    
    return errors


def validate_training_examples(
    input_file: str = "data/training_examples.json",
) -> Dict[str, Any]:
    """
    Validate all training examples.
    
    Returns:
        Report dict with validation results, statistics, errors
    """
    
    logger.info(f"Loading training examples from {input_file}")
    
    if not Path(input_file).exists():
        logger.error(f"File not found: {input_file}")
        return {"valid": False, "error": f"File not found: {input_file}"}
    
    with open(input_file, "r", encoding="utf-8") as f:
        examples = json.load(f)
    
    logger.info(f"Loaded {len(examples)} examples")
    
    # Validate each example
    all_errors = []
    for idx, example in enumerate(examples):
        errors = validate_example(example, idx)
        all_errors.extend(errors)
    
    # Compute statistics
    stats = {
        "total_examples": len(examples),
        "valid_examples": len(examples) - len(all_errors),
        "errors": all_errors,
        "error_count": len(all_errors),
    }
    
    # Profile distribution
    profile_counts: Dict[str, int] = {}
    for example in examples:
        profile = example.get("meta", {}).get("routing_profile", "unknown")
        profile_counts[profile] = profile_counts.get(profile, 0) + 1
    
    stats["profile_distribution"] = profile_counts
    
    # Length statistics
    repo_context_lengths = []
    user_query_lengths = []
    target_node_counts = []
    target_edge_counts = []
    
    for example in examples:
        if "repo_context" in example:
            repo_context_lengths.append(len(example["repo_context"]))
        
        if "user_query" in example:
            user_query_lengths.append(len(example["user_query"]))
        
        if "target" in example:
            try:
                if isinstance(example["target"], str):
                    graph = json.loads(example["target"])
                else:
                    graph = example["target"]
                target_node_counts.append(len(graph.get("nodes", [])))
                target_edge_counts.append(len(graph.get("edges", [])))
            except:
                pass
    
    def compute_stats(values: List[int]) -> Dict[str, float]:
        if not values:
            return {}
        values_sorted = sorted(values)
        return {
            "min": values_sorted[0],
            "max": values_sorted[-1],
            "mean": sum(values) / len(values),
            "median": values_sorted[len(values) // 2],
        }
    
    stats["repo_context_length_stats"] = compute_stats(repo_context_lengths)
    stats["user_query_length_stats"] = compute_stats(user_query_lengths)
    stats["target_node_count_stats"] = compute_stats(target_node_counts)
    stats["target_edge_count_stats"] = compute_stats(target_edge_counts)
    
    # Framework distribution
    framework_counts: Dict[str, int] = {}
    for example in examples:
        frameworks = example.get("meta", {}).get("frameworks", [])
        for fw in frameworks:
            framework_counts[fw] = framework_counts.get(fw, 0) + 1
    
    stats["framework_distribution"] = framework_counts
    
    # Risk profile distribution
    risk_counts: Dict[str, int] = {}
    for example in examples:
        risk = example.get("meta", {}).get("risk_profile", "unknown")
        risk_counts[risk] = risk_counts.get(risk, 0) + 1
    
    stats["risk_profile_distribution"] = risk_counts
    
    # Complexity distribution
    complexity_counts: Dict[str, int] = {}
    for example in examples:
        complexity = example.get("meta", {}).get("complexity_estimate", "unknown")
        complexity_counts[complexity] = complexity_counts.get(complexity, 0) + 1
    
    stats["complexity_distribution"] = complexity_counts
    
    # Validation result
    stats["valid"] = len(all_errors) == 0
    stats["validation_status"] = "VALID" if stats["valid"] else "INVALID"
    
    return stats


def print_validation_report(stats: Dict[str, Any]) -> None:
    """Pretty-print validation report."""
    
    print("\n" + "="*60)
    print("TRAINING DATA VALIDATION REPORT")
    print("="*60)
    
    print(f"\nValidation Status: {stats.get('validation_status', 'UNKNOWN')}")
    print(f"Total Examples: {stats.get('total_examples', 0)}")
    print(f"Valid Examples: {stats.get('valid_examples', 0)}")
    print(f"Errors: {stats.get('error_count', 0)}")
    
    if stats.get("error_count", 0) > 0:
        print(f"\nFirst 10 Errors:")
        for error in stats.get("errors", [])[:10]:
            print(f"  - {error}")
    
    print(f"\n--- Profile Distribution ---")
    for profile, count in sorted(stats.get("profile_distribution", {}).items()):
        pct = 100.0 * count / stats.get("total_examples", 1)
        print(f"  {profile}: {count} ({pct:.1f}%)")
    
    print(f"\n--- Framework Distribution (Top 10) ---")
    fw_sorted = sorted(stats.get("framework_distribution", {}).items(), 
                       key=lambda x: x[1], reverse=True)[:10]
    for fw, count in fw_sorted:
        pct = 100.0 * count / stats.get("total_examples", 1)
        print(f"  {fw}: {count} ({pct:.1f}%)")
    
    print(f"\n--- Risk Profile Distribution ---")
    for risk, count in sorted(stats.get("risk_profile_distribution", {}).items()):
        pct = 100.0 * count / stats.get("total_examples", 1)
        print(f"  {risk}: {count} ({pct:.1f}%)")
    
    print(f"\n--- Complexity Distribution ---")
    for complexity, count in sorted(stats.get("complexity_distribution", {}).items()):
        pct = 100.0 * count / stats.get("total_examples", 1)
        print(f"  {complexity}: {count} ({pct:.1f}%)")
    
    print(f"\n--- Length Statistics ---")
    print(f"  repo_context: {stats.get('repo_context_length_stats', {})}")
    print(f"  user_query: {stats.get('user_query_length_stats', {})}")
    print(f"  target nodes: {stats.get('target_node_count_stats', {})}")
    print(f"  target edges: {stats.get('target_edge_count_stats', {})}")
    
    print("\n" + "="*60 + "\n")


def save_validation_report(
    stats: Dict[str, Any],
    output_file: str = "data/training_data_stats.json"
) -> None:
    """Save validation report to JSON file."""
    
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Saved validation report to {output_file}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    stats = validate_training_examples()
    print_validation_report(stats)
    save_validation_report(stats)
