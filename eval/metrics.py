"""
Evaluation metrics for decision graph quality.
Could change in the future

  node_recall           — fraction of ground-truth nodes recovered
  edge_precision        — fraction of extracted edges that are correct
  failure_point_recall  — fraction of post-mortem failure points mapped
                          to Risk or Assumption nodes in the extracted graph
"""

# TODO: implement

from planninggraph.schema import DecisionGraph


def node_recall(predicted: DecisionGraph, ground_truth: DecisionGraph) -> float:
    """Fraction of ground-truth nodes present in the predicted graph."""
    raise NotImplementedError


def edge_precision(predicted: DecisionGraph, ground_truth: DecisionGraph) -> float:
    """Fraction of predicted edges that appear in the ground truth."""
    raise NotImplementedError


def failure_point_recall(
    predicted: DecisionGraph, failure_points: list[str]
) -> float:
    """
    Fraction of documented failure point descriptions that correspond to
    a Risk or Assumption node in the predicted graph.
    """
    raise NotImplementedError
