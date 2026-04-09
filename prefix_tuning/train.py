import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, Trainer, TrainingArguments
from peft import PrefixTuningConfig, TaskType, get_peft_model

from common import (
    PrefixDataset,
    CausalCollator,
    filter_examples_for_adapter,
    synthesize_routing_rules,
    default_adapter_specs,
    AdapterSpec,
)


def load_examples(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def train_one_adapter(
    base_model_name: str,
    tokenizer,
    examples: List[Dict[str, Any]],
    spec: AdapterSpec,
) -> None:
    train_examples = filter_examples_for_adapter(examples, spec)
    if not train_examples:
        print(f"[skip] {spec.name}: no matching examples")
        return

    print(f"[train] {spec.name}: {len(train_examples)} examples")

    base_model = AutoModelForCausalLM.from_pretrained(base_model_name)
    base_model.config.pad_token_id = tokenizer.pad_token_id

    peft_config = PrefixTuningConfig(
        task_type=TaskType.CAUSAL_LM,
        num_virtual_tokens=spec.num_virtual_tokens,
        prefix_projection=spec.prefix_projection,
        encoder_hidden_size=base_model.config.hidden_size,
    )

    model = get_peft_model(base_model, peft_config)
    model.print_trainable_parameters()

    dataset = PrefixDataset(train_examples, tokenizer, max_length=spec.max_length)
    collator = CausalCollator(tokenizer)

    args = TrainingArguments(
        output_dir=spec.output_dir,
        overwrite_output_dir=True,
        learning_rate=spec.learning_rate,
        num_train_epochs=spec.num_train_epochs,
        per_device_train_batch_size=spec.per_device_train_batch_size,
        gradient_accumulation_steps=spec.gradient_accumulation_steps,
        warmup_ratio=spec.warmup_ratio,
        weight_decay=spec.weight_decay,
        logging_steps=spec.logging_steps,
        save_steps=spec.save_steps,
        save_total_limit=2,
        report_to="none",
        fp16=torch.cuda.is_available(),
        bf16=False,
        remove_unused_columns=False,
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=dataset,
        data_collator=collator,
    )
    trainer.train()

    Path(spec.output_dir).mkdir(parents=True, exist_ok=True)
    model.save_pretrained(spec.output_dir)
    tokenizer.save_pretrained(spec.output_dir)

    print(f"[saved] {spec.name} -> {spec.output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model", required=True)
    parser.add_argument("--examples", required=True)
    parser.add_argument("--adapters-root", default="./adapters")
    parser.add_argument("--routing-rules", default="./deploy/routing_rules.json")
    args = parser.parse_args()

    tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    examples = load_examples(args.examples)
    specs = default_adapter_specs(args.adapters_root)

    for spec in specs:
        train_one_adapter(args.base_model, tokenizer, examples, spec)

    routing_rules = synthesize_routing_rules(specs)
    Path(args.routing_rules).parent.mkdir(parents=True, exist_ok=True)
    with open(args.routing_rules, "w", encoding="utf-8") as f:
        json.dump(routing_rules, f, indent=2)

    print(f"[rules] wrote routing rules -> {args.routing_rules}")


if __name__ == "__main__":
    main()