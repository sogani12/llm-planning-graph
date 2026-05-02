import json
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

import torch
from torch.utils.data import Dataset


@dataclass(frozen=True)
class RouteCondition:
    frameworks_any: Optional[List[str]] = None
    directive_contains: Optional[List[str]] = None
    response_mode: Optional[str] = None
    allowed_paths_any: Optional[List[str]] = None


@dataclass(frozen=True)
class AdapterSpec:
    name: str
    output_dir: str
    route_condition: RouteCondition

    num_virtual_tokens: int = 20
    prefix_projection: bool = True
    learning_rate: float = 1e-4
    num_train_epochs: float = 3.0
    per_device_train_batch_size: int = 2
    gradient_accumulation_steps: int = 8
    warmup_ratio: float = 0.03
    weight_decay: float = 0.0
    logging_steps: int = 10
    save_steps: int = 200
    max_length: int = 2048


def build_prompt(meta: Dict[str, Any], repo_context: str, user_query: str) -> str:
    return (
        "### METADATA\n"
        f"{json.dumps(meta, indent=2, sort_keys=True)}\n\n"
        "### REPOSITORY CONTEXT\n"
        f"{repo_context}\n\n"
        "### USER REQUEST\n"
        f"{user_query}\n\n"
        "### RESPONSE\n"
    )


def normalize_meta(meta: Dict[str, Any]) -> Dict[str, Any]:
    meta = dict(meta)

    frameworks = meta.get("frameworks", [])
    if isinstance(frameworks, str):
        frameworks = [x.strip() for x in frameworks.split(",") if x.strip()]
    frameworks = [str(x).lower() for x in frameworks]

    directive = str(meta.get("directive", "")).lower()

    bounds = meta.get("bounds", {})
    if not isinstance(bounds, dict):
        bounds = {}

    response_mode = bounds.get("response_mode", "")
    response_mode = str(response_mode).lower() if response_mode else ""

    allowed_paths = bounds.get("allowed_paths", [])
    if isinstance(allowed_paths, str):
        allowed_paths = [allowed_paths]
    allowed_paths = [str(x).lower() for x in allowed_paths]

    bounds["response_mode"] = response_mode
    bounds["allowed_paths"] = allowed_paths

    meta["frameworks"] = frameworks
    meta["directive"] = directive
    meta["bounds"] = bounds
    return meta


def contains_any_substring(text: str, patterns: Optional[List[str]]) -> bool:
    if not patterns:
        return True
    text = text.lower()
    return any(str(p).lower() in text for p in patterns)


def list_intersects(values: List[str], allowed: Optional[List[str]]) -> bool:
    if not allowed:
        return True
    values_set = {v.lower() for v in values}
    return any(a.lower() in values_set for a in allowed)


def paths_match_prefixes(paths: List[str], prefixes: Optional[List[str]]) -> bool:
    if not prefixes:
        return True
    prefixes = [p.lower() for p in prefixes]
    for path in paths:
        for prefix in prefixes:
            if path.startswith(prefix) or prefix in path:
                return True
    return False


def matches_condition(meta: Dict[str, Any], cond: RouteCondition) -> bool:
    meta = normalize_meta(meta)
    frameworks = meta["frameworks"]
    directive = meta["directive"]
    bounds = meta["bounds"]
    response_mode = bounds.get("response_mode", "")
    allowed_paths = bounds.get("allowed_paths", [])

    return (
        list_intersects(frameworks, cond.frameworks_any)
        and contains_any_substring(directive, cond.directive_contains)
        and (not cond.response_mode or response_mode == cond.response_mode.lower())
        and paths_match_prefixes(allowed_paths, cond.allowed_paths_any)
    )


class PrefixDataset(Dataset):
    def __init__(self, examples: List[Dict[str, Any]], tokenizer, max_length: int = 2048) -> None:
        self.examples = examples
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        ex = self.examples[idx]
        prompt = build_prompt(ex["meta"], ex["repo_context"], ex["user_query"])
        target = ex["target"]

        prompt_ids = self.tokenizer(
            prompt,
            add_special_tokens=False,
            truncation=True,
            max_length=self.max_length,
        )["input_ids"]

        target_ids = self.tokenizer(
            target,
            add_special_tokens=False,
            truncation=True,
            max_length=self.max_length,
        )["input_ids"]

        available_target_len = max(0, self.max_length - len(prompt_ids) - 1)
        target_ids = target_ids[:available_target_len]

        input_ids = prompt_ids + target_ids + [self.tokenizer.eos_token_id]
        attention_mask = [1] * len(input_ids)
        labels = [-100] * len(prompt_ids) + target_ids + [self.tokenizer.eos_token_id]

        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
            "labels": torch.tensor(labels, dtype=torch.long),
        }


class CausalCollator:
    def __init__(self, tokenizer) -> None:
        self.pad_token_id = tokenizer.pad_token_id

    def __call__(self, features: List[Dict[str, torch.Tensor]]) -> Dict[str, torch.Tensor]:
        max_len = max(len(x["input_ids"]) for x in features)

        batch = {"input_ids": [], "attention_mask": [], "labels": []}
        for x in features:
            pad_len = max_len - len(x["input_ids"])

            batch["input_ids"].append(
                torch.cat([x["input_ids"], torch.full((pad_len,), self.pad_token_id, dtype=torch.long)])
            )
            batch["attention_mask"].append(
                torch.cat([x["attention_mask"], torch.zeros(pad_len, dtype=torch.long)])
            )
            batch["labels"].append(
                torch.cat([x["labels"], torch.full((pad_len,), -100, dtype=torch.long)])
            )

        return {k: torch.stack(v) for k, v in batch.items()}


def filter_examples_for_adapter(examples: List[Dict[str, Any]], spec: AdapterSpec) -> List[Dict[str, Any]]:
    return [ex for ex in examples if matches_condition(ex["meta"], spec.route_condition)]


def synthesize_routing_rules(adapter_specs: List[AdapterSpec]) -> Dict[str, Any]:
    rules = []
    for spec in adapter_specs:
        rules.append(
            {
                "adapter_name": spec.name,
                "priority": 0 if spec.name != "default" else 9999,
                "condition": asdict(spec.route_condition),
                "adapter_path": spec.output_dir,
            }
        )

    def specificity(rule: Dict[str, Any]):
        cond = rule["condition"]
        score = 0
        for key in ("frameworks_any", "directive_contains", "allowed_paths_any"):
            if cond.get(key):
                score += len(cond[key])
        if cond.get("response_mode"):
            score += 2
        return (-score, rule["priority"])

    rules.sort(key=specificity)
    return {"rules": rules}


def default_adapter_specs(root: str = "./adapters") -> List[AdapterSpec]:
    return [
        AdapterSpec(
            name="finance_python",
            output_dir=f"{root}/finance_python",
            route_condition=RouteCondition(
                frameworks_any=["python"],
                directive_contains=["financial planning app", "budget", "forecast", "cashflow"],
                response_mode="python_only",
                allowed_paths_any=["backend/", "services/", "app/"],
            ),
        ),
        AdapterSpec(
            name="finance_sql",
            output_dir=f"{root}/finance_sql",
            route_condition=RouteCondition(
                frameworks_any=["sql"],
                directive_contains=["financial planning app", "budget", "forecast", "cashflow"],
                allowed_paths_any=["db/", "migrations/", "sql/"],
            ),
        ),
        AdapterSpec(
            name="backend_python",
            output_dir=f"{root}/backend_python",
            route_condition=RouteCondition(
                frameworks_any=["python"],
                response_mode="python_only",
                allowed_paths_any=["backend/", "services/", "app/"],
            ),
        ),
        AdapterSpec(
            name="db_sql",
            output_dir=f"{root}/db_sql",
            route_condition=RouteCondition(
                frameworks_any=["sql"],
                allowed_paths_any=["db/", "migrations/", "sql/"],
            ),
        ),
        AdapterSpec(
            name="default",
            output_dir=f"{root}/default",
            route_condition=RouteCondition(),
        ),
    ]