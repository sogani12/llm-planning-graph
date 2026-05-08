"""
Fine-tuning pipeline for Llama-3-8B on annotated planning dialogues.

Could change in the future:
Uses LoRA (via PEFT) for parameter-efficient fine-tuning.
Only needed if prompt engineering alone fails to reliably elicit implicit
assumptions or produce well-formed graph updates.

Target hardware: single GPU on instgpu-{01..05}.cs.wisc.edu
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from prefix_tuning.common import default_adapter_specs, synthesize_routing_rules
from prefix_tuning.train_graph_models import (
    load_examples,
    train_one_adapter_with_metrics,
)

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train planninggraph adapters with optional validation metrics"
    )
    parser.add_argument("--base-model", required=True, help="Base model identifier")
    parser.add_argument("--examples", required=True, help="Training examples JSON")
    parser.add_argument("--val-examples", default=None, help="Validation examples JSON")
    parser.add_argument("--adapters-root", default="./adapters", help="Adapter output directory")
    parser.add_argument(
        "--routing-rules",
        default="./deploy/routing_rules.json",
        help="Where to write synthesized routing rules",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    try:
        from transformers import AutoTokenizer
    except ImportError as exc:
        raise SystemExit(
            "transformers is required for fine-tuning. Install project dependencies first."
        ) from exc

    examples_path = Path(args.examples)
    if not examples_path.exists():
        raise SystemExit(f"Training examples file not found: {examples_path}")
    if args.val_examples and not Path(args.val_examples).exists():
        raise SystemExit(f"Validation examples file not found: {args.val_examples}")

    tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    examples = load_examples(args.examples)
    val_examples = load_examples(args.val_examples) if args.val_examples else None
    specs = default_adapter_specs(args.adapters_root)

    results = []
    for spec in specs:
        results.append(
            train_one_adapter_with_metrics(
                args.base_model,
                tokenizer,
                examples,
                spec,
                val_examples,
            )
        )

    routing_rules = synthesize_routing_rules(specs)
    routing_rules_path = Path(args.routing_rules)
    routing_rules_path.parent.mkdir(parents=True, exist_ok=True)
    routing_rules_path.write_text(json.dumps(routing_rules, indent=2), encoding="utf-8")

    logger.info("Fine-tuning complete.")
    logger.info("Adapter results: %s", results)
    logger.info("Routing rules written to %s", routing_rules_path)


if __name__ == "__main__":
    main()
