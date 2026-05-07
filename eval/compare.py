from __future__ import annotations
import json
from pathlib import Path

EXPERIMENTS_DIR = Path(__file__).parent / "experiments"

def count_nodes(graph_path):
    data = json.loads(graph_path.read_text())
    counts = {}
    for node in data.get("nodes", []):
        t = node.get("type", "unknown")
        counts[t] = counts.get(t, 0) + 1
    return counts


def main():
    projects = sorted(p for p in EXPERIMENTS_DIR.iterdir() if p.is_dir())
    if not projects:
        print("No experiments found in", EXPERIMENTS_DIR)
        return

    rows = []
    for project in projects:
        name = project.name
        graph_path = project / "condition_b" / "graph_final.json"
        if not graph_path.exists():
            rows.append({
                "project": name,
                "status": "condition_b/graph_final.json missing",
                "nodes": {},
                "total_nodes": 0,
                "total_edges": 0,
            })
            continue
        data = json.loads(graph_path.read_text())
        node_counts = count_nodes(graph_path)
        total_edges = len(data.get("edges", []))
        rows.append({
            "project": name,
            "status": "complete",
            "nodes": node_counts,
            "total_nodes": sum(node_counts.values()),
            "total_edges": total_edges,
        })
    node_types = ["objective", "requirement", "assumption", "decision",
                  "component", "interface", "risk", "test"]
    header = "| Project | " + " | ".join(t[:5] for t in node_types) + " | Total nodes | Edges |"
    sep    = "|---------|" + "|".join(["-------"] * len(node_types)) + "|-------------|-------|"
    print("\n## Graph Node Counts by Experiment\n")
    print(header)
    print(sep)
    for row in rows:
        if row["status"] != "complete":
            print(f"| {row['project']} | *{row['status']}* |")
            continue
        counts = [str(row["nodes"].get(t, 0)) for t in node_types]
        print(f"| {row['project']} | " + " | ".join(counts) + f" | {row['total_nodes']} | {row['total_edges']} |\n")

if __name__ == "__main__":
    main()
