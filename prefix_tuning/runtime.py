import argparse
import json
from typing import Any, Dict, Optional
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from common import build_prompt, matches_condition, RouteCondition

class MultiPrefixRuntime:
    def __init__(self, base_model_name, routing_rules_path, device = None, torch_dtype = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        with open(routing_rules_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        self.rules = payload["rules"]
        self.tokenizer = AutoTokenizer.from_pretrained(base_model_name)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            torch_dtype=torch_dtype,
        )
        base_model.config.pad_token_id = self.tokenizer.pad_token_id
        if not self.rules:
            raise ValueError("No routing rules found.")
        first = self.rules[0]
        first_adapter_name = first["adapter_name"]
        first_adapter_path = first["adapter_path"]
        self.model = PeftModel.from_pretrained(
            base_model,
            first_adapter_path,
            adapter_name=first_adapter_name,
            is_trainable=False,
        )
        loaded = {first_adapter_name}
        for rule in self.rules[1:]:
            name = rule["adapter_name"]
            path = rule["adapter_path"]
            if name not in loaded:
                self.model.load_adapter(path, adapter_name=name, is_trainable=False)
                loaded.add(name)
        self.model.to(self.device)
        self.model.eval()
        self.available_adapters = loaded

    @staticmethod
    def _condition_from_dict(d):
        return RouteCondition(
            frameworks_any=d.get("frameworks_any"),
            directive_contains=d.get("directive_contains"),
            response_mode=d.get("response_mode"),
            allowed_paths_any=d.get("allowed_paths_any"),
        )

    def choose_adapter(self, meta):
        for rule in self.rules:
            cond = self._condition_from_dict(rule["condition"])
            if matches_condition(meta, cond):
                return rule["adapter_name"]
        if "default" in self.available_adapters:
            return "default"
        raise ValueError("No route matched and no default adapter is available.")

    @torch.inference_mode()
    def generate(self, meta,repo_context, user_query, max_new_tokens = 256, temperature = 0.0, do_sample = False):
        adapter_name = self.choose_adapter(meta)
        self.model.set_adapter(adapter_name)
        prompt = build_prompt(meta, repo_context, user_query)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=do_sample,
            temperature=temperature,
            pad_token_id=self.tokenizer.pad_token_id,
            eos_token_id=self.tokenizer.eos_token_id,
        )
        decoded = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        response = decoded[len(prompt):] if decoded.startswith(prompt) else decoded
        return {
            "adapter_name": adapter_name,
            "prompt": prompt,
            "response": response.strip(),
        }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model", required=True)
    parser.add_argument("--routing-rules", required=True)
    parser.add_argument("--meta-json", required=True)
    parser.add_argument("--repo-context-file", required=True)
    parser.add_argument("--user-query", required=True)
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--do-sample", action="store_true")
    args = parser.parse_args()
    with open(args.meta_json, "r", encoding="utf-8") as f:
        meta = json.load(f)
    with open(args.repo_context_file, "r", encoding="utf-8") as f:
        repo_context = f.read()
    runtime = MultiPrefixRuntime(
        base_model_name=args.base_model,
        routing_rules_path=args.routing_rules,
        torch_dtype=torch.float16 if torch.cuda.is_available() else None,
    )
    result = runtime.generate(
        meta=meta,
        repo_context=repo_context,
        user_query=args.user_query,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        do_sample=args.do_sample,
    )
    print(f"SELECTED ADAPTER: {result["adapter_name"]}\n")
    print(result["response"])

if __name__ == "__main__":
    main()