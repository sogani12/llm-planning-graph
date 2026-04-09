# Multi-Prefix Routing with PEFT Prefix Tuning

This repository implements a **training + deployment pipeline** for using **multiple prefix-tuning adapters** (via PEFT) with a **JSON-driven routing system** for repository-aware LLMs.

This version uses a **modular file structure**:

```
common.py   → shared logic (schema, routing, dataset)
train.py    → training adapters + generating routing rules
runtime.py  → inference + adapter routing + generation
```

---

# Overview

## Core Idea

Instead of training one monolithic model, this system:

1. Trains **multiple prefix adapters**
2. Uses **JSON metadata** to select the correct adapter
3. Injects **repository context dynamically**
4. Routes and generates output at runtime

---

# Architecture

```
Training Phase:
  dataset → filter per adapter → train prefix → save adapter

Deployment Phase:
  load adapters → route via JSON → set_adapter → generate
```

---

# Project Structure

```
project/
├── common.py                # shared logic
├── train.py                 # training pipeline
├── runtime.py               # inference pipeline
├── data/
│   ├── train_examples.json
│   ├── request_meta.json
│   └── repo_context.txt
├── adapters/               # saved prefix adapters
└── deploy/
    └── routing_rules.json
```

---

# File Responsibilities

## `common.py`

Shared utilities used by both training and inference.

Includes:

* `RouteCondition` → routing schema
* `AdapterSpec` → adapter configuration
* `build_prompt()` → input formatting
* `matches_condition()` → routing logic
* `PrefixDataset` → training dataset
* `CausalCollator` → batching
* `filter_examples_for_adapter()` → dataset filtering
* `synthesize_routing_rules()` → rule generation

👉 Ensures **training and inference use identical logic**

---

## `train.py`

Handles **adapter training and rule generation**

### Responsibilities

* Load dataset
* Filter data per adapter
* Train prefix-tuned models (PEFT)
* Save adapters
* Generate routing rules

### Run Training

```bash
python train.py \
  --base-model gpt2 \
  --examples ./data/train_examples.json \
  --adapters-root ./adapters \
  --routing-rules ./deploy/routing_rules.json
```

---

## `runtime.py`

Handles **inference and routing**

### Responsibilities

* Load base model
* Load all adapters
* Select adapter via JSON metadata
* Generate output

### Run Inference

```bash
python runtime.py \
  --base-model gpt2 \
  --routing-rules ./deploy/routing_rules.json \
  --meta-json ./data/request_meta.json \
  --repo-context-file ./data/repo_context.txt \
  --user-query "Add savings projection feature"
```

---

# Data Format

## Training Example

```json
{
  "meta": {
    "frameworks": ["python"],
    "directive": "financial planning app",
    "bounds": {
      "response_mode": "python_only",
      "allowed_paths": ["backend/services"]
    }
  },
  "repo_context": "...code...",
  "user_query": "Add feature",
  "target": "def function(...): ..."
}
```

---

## Inference Metadata

```json
{
  "frameworks": ["python"],
  "directive": "financial planning app",
  "bounds": {
    "response_mode": "python_only",
    "allowed_paths": ["backend/services"]
  }
}
```

---

# Prompt Format

All inputs are structured:

```
### METADATA
{JSON}

### REPOSITORY CONTEXT
<code>

### USER REQUEST
<task>

### RESPONSE
```

---

# Training Details

Each adapter:

1. Filters dataset via `route_condition`
2. Trains prefix-tuning parameters:

   ```python
   PrefixTuningConfig(
       task_type=TaskType.CAUSAL_LM,
       num_virtual_tokens=20,
       prefix_projection=True
   )
   ```
3. Saves adapter:

   ```
   ./adapters/<adapter_name>/
   ```

---

# Routing Rules

Automatically generated after training.

Example:

```json
{
  "rules": [
    {
      "adapter_name": "finance_python",
      "condition": {
        "frameworks_any": ["python"],
        "directive_contains": ["financial planning app"],
        "response_mode": "python_only",
        "allowed_paths_any": ["backend/"]
      }
    }
  ]
}
```

---

# Routing Logic

At runtime:

```
JSON metadata → match rules → select adapter → generate
```

Example:

```
frameworks = python
directive = financial
→ finance_python adapter
```

---

# Multi-Prefix Routing

The system supports:

* multiple specialized adapters
* dynamic switching via:

  ```python
  model.set_adapter(adapter_name)
  ```

---

# Design Principles

## 1. Separation of Concerns

| Component       | Role                    |
| --------------- | ----------------------- |
| Prefix adapters | behavior specialization |
| JSON metadata   | explicit control        |
| Retrieval       | repo knowledge          |
| Router          | adapter selection       |

---

## 2. Prefix ≠ Memory

Prefix tuning:

* does NOT store repository data
* only biases behavior

Use retrieval for repo context.

---

## 3. Train = Route Alignment

Routing rules are derived from:

```
filter_examples_for_adapter()
```

This prevents mismatch between:

* training behavior
* runtime routing

---

## 4. Soft vs Hard Constraints

Prefix tuning provides:

* soft adherence

For strict rules:

* validate outputs
* reject + regenerate

---

# Extending the System

## Add Adapter

1. Add new `AdapterSpec` in `common.py`
2. Define `route_condition`
3. Run training again

---

## Improve Routing

Future improvements:

* learned router (classifier)
* confidence-based routing
* multi-adapter blending

---

## Add Validation Layer

````python
def validate(output):
    return "def " in output and "```" not in output
````

---

# Common Pitfalls

## Inconsistent Metadata

Bad:

```
framework = python
frameworks = ["python"]
```

Good:

```
frameworks = ["python"]
```

---

## Weak Training Signals

If:

```
response_mode = python_only
```

But outputs include text → model won't learn constraint

---

## Routing Mismatch

Ensure:

```
training filters == routing rules
```

---

# Summary

This system enables:

* modular prefix-tuned adapters
* structured control via JSON
* automatic routing
* scalable multi-domain LLM behavior

---

# Next Steps

* add retrieval pipeline
* implement learned router
* add reinforcement learning
* improve constraint validation

---
