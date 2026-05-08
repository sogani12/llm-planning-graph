from planninggraph.failure import surface_risks
from planninggraph.maintenance import apply_update
from planninggraph.prompts import load_prompt
from planninggraph.schema import (
    Assumption,
    Component,
    DecisionGraph,
    Edge,
    EdgeType,
    Objective,
    Requirement,
)
from eval.metrics import edge_precision, failure_point_recall, node_recall


def test_graph_round_trip_and_blast_radius(sample_graph):
    snapshot = sample_graph.to_schema()
    restored = sample_graph.from_schema(snapshot)

    assert restored.get_node("obj-1").label == "Ship feature"
    assert {node.id for node in restored.blast_radius("asm-1")} == {"comp-1", "obj-1"}


def test_apply_update_accepts_graph_json(empty_graph):
    update_payload = DecisionGraph(
        nodes=[
            Requirement(id="req-1", label="Nightly runs", description="System runs overnight"),
            Component(id="comp-2", label="Scheduler", description="Triggers nightly runs", has_tests=True),
        ],
        edges=[
            Edge(
                id="edge-3",
                type=EdgeType.IMPLEMENTS,
                source_id="comp-2",
                target_id="req-1",
                rationale="Scheduler implements nightly execution.",
            )
        ],
    ).model_dump_json()

    result = apply_update(empty_graph, update_payload)
    snapshot = empty_graph.to_schema()

    assert len(result["added_nodes"]) == 2
    assert len(result["added_edges"]) == 1
    assert len(snapshot.nodes) == 2
    assert len(snapshot.edges) == 1


def test_surface_risks_uses_assumptions_and_untested_components(sample_graph):
    risks = surface_risks(sample_graph)
    labels = {risk.label for risk in risks}

    assert "Assumption may fail: API remains stable" in labels
    assert "Insufficient test coverage for Sync worker" in labels


def test_metrics_match_by_type_and_label():
    ground_truth = DecisionGraph(
        nodes=[
            Objective(id="obj-1", label="Ship feature", description=""),
            Assumption(id="asm-1", label="API stable", description=""),
        ],
        edges=[
            Edge(
                id="edge-1",
                type=EdgeType.ASSUMES,
                source_id="obj-1",
                target_id="asm-1",
            )
        ],
    )
    predicted = DecisionGraph(
        nodes=[
            Objective(id="another-id", label="Ship feature", description=""),
            Assumption(id="different-id", label="API stable", description=""),
        ],
        edges=[
            Edge(
                id="edge-2",
                type=EdgeType.ASSUMES,
                source_id="another-id",
                target_id="different-id",
            )
        ],
    )

    assert node_recall(predicted, ground_truth) == 1.0
    assert edge_precision(predicted, ground_truth) == 1.0
    assert failure_point_recall(predicted, ["API stable"]) == 1.0


def test_load_prompt_reads_template():
    prompt = load_prompt("extraction_system")
    assert "decision graph" in prompt.lower()
