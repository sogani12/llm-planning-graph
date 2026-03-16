"""
Evaluation CLI entry point.

Usage:
  python eval/run_eval.py --stage 1   # intrinsic: graph quality metrics
  python eval/run_eval.py --stage 2   # extrinsic: plan quality human eval
"""

# TODO: implement

import argparse


def main():
    parser = argparse.ArgumentParser(description="Run planninggraph evaluation")
    parser.add_argument("--stage", type=int, choices=[1, 2], required=True)
    args = parser.parse_args()
    raise NotImplementedError(f"Stage {args.stage} evaluation not yet implemented")


if __name__ == "__main__":
    main()
