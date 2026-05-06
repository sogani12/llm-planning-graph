## Final Implementation Plan

Build a Python-based, unattended nightly pipeline that ingests compliant public content, deduplicates in SQLite, ranks against a user profile, summarizes relevant items, and delivers a daily digest. The plan below is grounded in your finalized graph decisions (SQLite, daily policy gate, no-ingest safe mode, quarantine with 2 approvals, feedback threshold at 50 votes).

### 1) System Architecture

- **Runtime**: Python CLI app with modular pipeline stages.
- **Storage**: SQLite (single-machine, low-ops), with WAL mode and indexes for dedup + ranking reads.
- **Collection strategy**: Feed/API first, browser scraping only where needed.
- **Safety gates**:
  - Daily policy check before ingestion.
  - If policy check fails/unavailable => **no ingest** for that run + alert.
  - Automatic source quarantine on repeated extraction/compliance/bot failures.
  - Re-enable quarantined source only after **2 explicit approvals**.
- **Relevance strategy**:
  - Stage 1: heuristic prefilter (keywords + BM25).
  - Stage 2: LLM rerank + summary on reduced candidate set.
  - Feedback-aware tuning only after **>=50 explicit votes**.

### 2) Repository/Module Layout

- `src/orchestrator/`: run coordination, stage transitions, run state machine.
- `src/ingest/`
  - `source_registry.py` (allowlisted source config + capabilities)
  - `fetch_rss.py`, `fetch_http.py`, `fetch_browser.py`
  - `parsers/` per-source adapters (normalized output)
- `src/policy/`
  - `checker.py` (robots/terms checks)
  - `contracts.py` (`iface_policy_check_result`)
- `src/quarantine/`
  - `manager.py` (state transitions + approval flow)
- `src/relevance/`
  - `prefilter.py` (keywords/BM25)
  - `rerank_llm.py`
  - `feedback_model.py` (enabled only after threshold)
- `src/summarize/` LLM summarization + guardrails (length/style constraints)
- `src/digest/` email/PDF rendering and dispatch
- `src/storage/`
  - schema migrations
  - DAO/repositories
- `src/observability/` structured logs, metrics emitters, alerts
- `tests/`
  - `fixtures/snapshots/` saved HTML/feed payloads
  - conformance/integration suites matching graph tests

### 3) Data Model (SQLite)

Core tables:

- `sources` (`source_id`, type, base_url, allowlisted, quarantine_state, last_policy_status, last_approved_at, approval_count)
- `policy_checks` (`id`, `source_id`, `check_time`, `robots_allowed`, `terms_allowed`, `status`, `reason`)
- `content_items` (`item_id`, canonical_url, source_id, title, body, published_at, fetched_at, raw_hash, canonical_hash, metadata_json)
- `ingestion_runs` (`run_id`, start_ts, end_ts, status, policy_gate_status, error_summary)
- `relevance_scores` (`run_id`, `item_id`, prefilter_score, llm_score, final_score, rank_reason_json)
- `summaries` (`item_id`, model, summary_text, token_count, cost_estimate, created_at)
- `digests` (`digest_id`, date, format, recipient, artifact_path, status)
- `feedback_votes` (`vote_id`, `item_id`, vote(+/-), user_id(optional), voted_at)

Indexes/constraints:

- Unique on `canonical_hash` and/or canonical URL normalization for cross-run dedup.
- Composite indexes on (`source_id`, `published_at`), (`run_id`, `final_score`), (`check_time`, `status`).
- Foreign keys on all run/source/item relationships.

### 4) End-to-End Nightly Workflow

1. **Start run**; create `ingestion_runs` record.
2. **Policy gate** (daily):
   - Run checker for each allowlisted source.
   - Persist `policy_checks`.
   - If checker unavailable/invalid => mark run safe mode, **skip ingest**, send ops alert digest, end run gracefully.
3. **Source selection**:
   - Exclude quarantined sources.
   - For each source: use RSS/API first, browser fallback if required.
4. **Parse + normalize** with source adapters.
5. **Dedup** by canonical URL/hash and content fingerprint.
6. **Relevance stage 1** (keywords + BM25).
7. **Relevance stage 2** (LLM rerank on top candidates).
8. **Feedback tuning**:
   - If total votes < 50: keep baseline weights.
   - If >= 50: apply feedback-adjusted weighting in final score composition.
9. **Summarization** for selected items.
10. **Digest generation** (email/PDF), persist artifact + status.
11. **Quarantine management**:
    - Update failure counters.
    - Auto-quarantine failing sources.
    - Re-enable only after 2 explicit approvals.
12. **Finalize run** and emit metrics/log summary.

### 5) Error Handling & Recovery

- Per-source isolation: one source failure does not fail entire run.
- Retry policy:
  - network/transient errors: exponential backoff with capped retries.
  - parsing failures: no blind retry; snapshot capture + quarantine scoring.
- Idempotency:
  - dedup constraints prevent duplicate writes on reruns.
  - run stage checkpoints allow safe rerun from failed stage.
- Safe defaults:
  - compliance uncertainty => no ingest.
  - LLM outage => still ship reduced digest (prefiltered + extractive fallback summary) with degraded-mode flag.

### 6) Testing Plan (directly mapped to graph)

- **Conformance**: `tst_parser_snapshot_conformance`
  - Saved fixture snapshots for each parser adapter.
  - Fail on schema drift or missing required fields.
  - Guards against source layout drift.
- **Conformance**: `tst_policy_contract_conformance`
  - Validate policy check result contract and gate behavior.
  - Explicitly assert no-ingest on invalid/unavailable policy checks.
  - Guards against terms/compliance breakage.
- **Integration**: `tst_quarantine_workflow_integration`
  - Quarantine transitions, approval count tracking, re-enable only at 2 approvals.
  - Guards against bot-block operational regressions.
- Additional recommended:
  - dedup correctness tests (cross-run repeats)
  - ranking pipeline determinism tests (seeded fixtures)
  - digest rendering snapshot tests (email + PDF)

### 7) Observability & Ops

- Structured logs with `run_id`, `source_id`, stage, severity, decision path.
- Metrics:
  - items fetched/parsed/deduped
  - policy pass/fail counts
  - quarantine count + re-enable latency
  - LLM token/cost/latency
  - digest send success rate
- Alerts:
  - policy gate failure (safe mode run)
  - sharp drop in parsed items for a source
  - repeated quarantine flapping
  - digest delivery failure

### 8) Delivery Phases

- **Phase A (foundation)**: schema, run orchestrator, policy gate, source registry.
- **Phase B (ingestion core)**: hybrid collectors + parser adapters + dedup.
- **Phase C (relevance/summarization)**: two-stage ranking, summaries, digest rendering.
- **Phase D (reliability controls)**: quarantine manager, approvals workflow, alerts.
- **Phase E (feedback loop)**: vote capture, 50-threshold fallback, adaptive weighting.
- **Phase F (hardening)**: full conformance/integration suite, runbooks, retry tuning.

### 9) Acceptance Criteria

- Nightly run completes unattended for 7 consecutive days.
- Policy gate executes daily; policy-check failure triggers no-ingest safe mode and alert.
- Duplicate insertion rate effectively zero under repeated reruns.
- Quarantined sources require 2 approvals before re-enable.
- Feedback weighting remains disabled until 50 votes; activates thereafter.
- High-severity risks covered by automated conformance/integration tests in CI.