"""
Evaluation CLI entry point.

Usage:
  python eval/run_eval.py --stage 1   # intrinsic: graph quality metrics
  python eval/run_eval.py --stage 2   # extrinsic: plan quality human eval
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from planninggraph.schema import DecisionGraph

from eval.metrics import edge_precision, failure_point_recall, node_recall

EXPERIMENTS_DIR = Path(__file__).parent / "experiments"


def _load_graph(path: Path) -> DecisionGraph:
    return DecisionGraph.model_validate_json(path.read_text(encoding="utf-8"))


def _project_graphs(project_dir: Path) -> tuple[Path | None, list[Path]]:
    cond_b = project_dir / "condition_b"
    final_path = cond_b / "graph_final.json"
    if not final_path.exists():
        fallback = cond_b / "graph.json"
        final_path = fallback if fallback.exists() else None
    versions = sorted(cond_b.glob("graph_v*.json"))
    return final_path, versions


def _extract_failure_points(graph: DecisionGraph) -> list[str]:
    return [
        f"{node.label} {node.description}".strip()
        for node in graph.nodes
        if str(node.type) == "risk"
    ]


def run_stage1() -> int:
    rows: list[tuple[str, str, float, float, float]] = []
    for project_dir in sorted(p for p in EXPERIMENTS_DIR.iterdir() if p.is_dir()):
        final_path, versions = _project_graphs(project_dir)
        if final_path is None:
            continue

        ground_truth = _load_graph(final_path)
        failure_points = _extract_failure_points(ground_truth)
        if not versions:
            versions = [final_path]

        for version_path in versions:
            predicted = _load_graph(version_path)
            rows.append(
                (
                    project_dir.name,
                    version_path.name,
                    node_recall(predicted, ground_truth),
                    edge_precision(predicted, ground_truth),
                    failure_point_recall(predicted, failure_points),
                )
            )

    if not rows:
        print("No graph evaluations available.")
        return 0

    print("\nStage 1: intrinsic graph quality\n")
    print("| Project | Version | Node recall | Edge precision | Failure recall |")
    print("|---------|---------|-------------|----------------|----------------|")
    for project, version, n_recall, e_precision, f_recall in rows:
        print(
            f"| {project} | {version} | {n_recall:.2f} | "
            f"{e_precision:.2f} | {f_recall:.2f} |"
        )

    return 0


def _extract_total_score(text: str) -> tuple[str | None, str | None]:
    match = re.search(
        r"\|\s*\*\*Total Score\*\*\s*\|\s*\*\*([^|]+)\*\*\s*\|\s*\*\*([^|]+)\*\*\s*\|",
        text,
    )
    if not match:
        objective_matches = re.findall(
            r"\|\s*\d+\s*\|[^|]*\|\s*([0-9.]+)\s*\|\s*([0-9.]+)\s*\|",
            text,
        )
        if not objective_matches:
            return None, None
        cond_a_total = sum(float(a) for a, _ in objective_matches)
        cond_b_total = sum(float(b) for _, b in objective_matches)
        return f"{cond_a_total:g}", f"{cond_b_total:g}"
    return match.group(1).strip(), match.group(2).strip()


def run_stage2() -> int:
    rows: list[tuple[str, str, str]] = []
    for project_dir in sorted(p for p in EXPERIMENTS_DIR.iterdir() if p.is_dir()):
        objectives = project_dir / "objectives.md"
        if not objectives.exists():
            continue
        cond_a, cond_b = _extract_total_score(objectives.read_text(encoding="utf-8"))
        if cond_a is None or cond_b is None:
            continue
        rows.append((project_dir.name, cond_a, cond_b))

    if not rows:
        print("No stage 2 scorecards found.")
        return 0

    print("\nStage 2: human evaluation summary\n")
    print("| Project | Condition A | Condition B |")
    print("|---------|-------------|-------------|")
    for project, cond_a, cond_b in rows:
        print(f"| {project} | {cond_a} | {cond_b} |")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Run planninggraph evaluation")
    parser.add_argument("--stage", type=int, choices=[1, 2], required=True)
    args = parser.parse_args()
    if args.stage == 1:
        raise SystemExit(run_stage1())
    raise SystemExit(run_stage2())


if __name__ == "__main__":
    main()
