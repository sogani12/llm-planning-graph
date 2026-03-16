# llm-planning-graph

**Structured Planning Under Uncertainty: A Decision Graph Approach to AI-Assisted Software Development**

CS639 · Deep Learning for NLP · UW-Madison · Spring 2026

---

## What it does

Extracts and maintains a typed, directed **decision graph** from developer-AI conversations and project documents (READMEs, issues, PRs). The graph makes explicit the objectives, assumptions, dependencies, decisions, and risks embedded in a software project — enabling blast-radius computation, anticipatory failure surfacing, and dependency-aware plan maintenance.

## Stack

- **LLM backbone:** Anthropic Claude / OpenAI GPT-4o
- **Graph:** NetworkX (swap to Neo4j if scale demands)
- **Schema validation:** Pydantic v2
- **API:** FastAPI
- **Demo UI:** Streamlit
- **Fine-tuning (if needed):** HuggingFace Transformers + PEFT (LoRA)

## Quick start

```bash
# Install deps
pip install -e ".[dev]"

# Run API (local)
uvicorn api.main:app --reload

# Run demo UI
streamlit run demo/app.py

# Run with Docker (API + demo)
docker compose up
```

## Repo structure

```
planninggraph/        Core library
  schema.py           Pydantic models for all node/edge types
  extractor.py        LLM-based graph extraction from text
  graph.py            NetworkX wrapper: add, update, query, traverse
  maintenance.py      Incremental update + invalidation propagation
  failure.py          Anticipatory failure/risk surfacing
  prompts/            Prompt templates
api/
  main.py             FastAPI endpoints
eval/
  annotated/          Ground truth graphs (JSON)
  metrics.py          Node recall, edge precision, failure point recall
  run_eval.py         Eval CLI
scripts/
  eda.py              EDA over GitHub corpus
  finetune.py         Fine-tuning pipeline
tests/
data/                 Raw GitHub READMEs, issues, post-mortems
notebooks/            Exploratory work
demo/
  app.py              Streamlit demo
```

## Team

| Member | Responsibility |
|--------|---------------|
| Sogani & Garey | Graph schema + extraction pipeline |
| Motonishi & Konduru | Data collection + annotation |
| Sehgal | Living plan maintenance + blast radius |
| Khade | Baselines, Stage 2 eval, integration |
