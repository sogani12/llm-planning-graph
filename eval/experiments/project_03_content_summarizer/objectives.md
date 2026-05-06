# Evaluation Rubric — Content Summarizer Pipeline

Each objective is scored independently for Condition A and Condition B.
Score: 0 = not addressed | 0.5 = partially addressed | 1 = fully addressed

---

## Functional Objectives (expected from both conditions)

| # | Objective | A score | B score | Notes |
|---|-----------|---------|---------|-------|
| 1 | Multi-source public content ingestion includes standard feeds/pages and JS-rendered fallback when needed | 1 | 1 | Both plans cover RSS/HTML ingestion and browser-assisted fallback for harder sources. B makes the feed-first/browser-fallback strategy explicit via `dec_hybrid_collection`. |
| 2 | Database/storage design supports persistent cross-run deduplication | 1 | 1 | Both use SQLite with canonical URL or canonical hash dedup across runs. B makes this a first-class requirement node `req_persistent_dedup`. |
| 3 | Relevance filtering is personalized to a user profile rather than simple global ranking | 1 | 1 | A includes profile-aware keyword/topic scoring with preferred-source boost. B includes a two-stage profile-aware relevance path with heuristic prefilter plus LLM rerank. |
| 4 | Summaries are constrained and digest-ready rather than unconstrained free-form generation | 0.5 | 1 | A specifies local LLM summaries with exactly 3 bullets, but leaves validation lighter. B adds summarization guardrails and ties output more directly to digest generation and ranking stages. |
| 5 | Pipeline is designed for unattended nightly execution with retries and partial-failure recovery | 1 | 1 | Both describe nightly unattended runs, retries, structured logging, and partial-failure handling without restarting the whole pipeline. |
| 6 | Testing strategy is decoupled from live sources using saved fixtures/snapshots | 1 | 1 | Both use fixture-driven tests and snapshot-first validation. B also maps this to explicit graph test nodes like `tst_parser_snapshot_conformance`. |
| 7 | Content collection is gated by an explicit compliance/safety strategy when source policy is uncertain | 0.5 | 1 | A has legal/compliance guardrails and allowlists, but no explicit pre-ingest policy gate. B adds daily policy verification, a contract for policy results, and `dec_no_ingest_on_policy_check_failure`. |
| 8 | Feedback or adaptive relevance logic is included with a safe fallback when signal volume is too low | 0 | 1 | A has no explicit feedback loop. B includes lightweight explicit feedback plus `dec_feedback_min_volume_fallback`, keeping baseline ranking until `>=50` votes. |

## Structural Objectives (graph-specific — condition B only)

| # | Objective | A score | B score | Notes |
|---|-----------|---------|---------|-------|
| 9  | Key architectural decisions recorded with explicit rationale (e.g. runtime, storage, collection strategy, policy gate behavior) | 0.5 | 1 | A has a concise prose architecture section but no explicit alternatives. B records 10 decision nodes with rationale and traceable design choices. |
| 10 | Implicit assumptions surfaced (e.g. allowlisted sources remain compliant, summaries stay within budget, feedback volume is sufficient) | 0 | 1 | A leaves assumptions implicit. B surfaces 6 assumption nodes such as `asm_sources_allow_collection`, `asm_llm_summary_budget`, and `asm_feedback_participation`. |
| 11 | Risks identified (e.g. source layout drift, bot mitigation failure, digest mismatch, terms changes) | 0.5 | 1 | A has general reliability/compliance notes but no explicit risk register. B records 4 risk nodes and ties them to concrete safeguards like quarantine and policy checks. |

---

## Summary Counts (fill in after both sessions)

| Metric | Condition A | Condition B |
|--------|-------------|-------------|
| Functional objectives hit (out of 8) | 6 / 8 | 8 / 8 |
| Structural objectives hit (out of 3) | 1 / 3 | 3 / 3 |
| Total decision nodes in plan | 0 (no graph) | 10 |
| Total assumption nodes surfaced | 0 (no graph) | 6 |
| Total risk nodes surfaced | 0 (no graph) | 4 |
| Graph nodes total | — | 39 |
| Graph edges total | — | 54 |

---

## Key Qualitative Catches

Specific things condition B surfaced that condition A missed or glossed over:

1. **Compliance becomes an explicit gate instead of a soft guideline**: A includes reasonable guardrails like allowlists and `robots.txt` respect, but B turns compliance into an enforceable daily policy check with a no-ingest safe mode on failure.

2. **Operational quarantine logic is made concrete**: A discusses retries and partial-failure recovery, but B adds automatic source quarantine and a strict re-enable rule of 2 approvals, which makes operational handling of unstable or non-compliant sources auditable.

3. **Feedback is treated as a controlled system, not an eventual idea**: A has no explicit feedback loop. B includes lightweight explicit feedback capture and a thresholded fallback so adaptive ranking is disabled until there are at least 50 votes.

4. **The graph forces explicit assumptions and risk accounting**: B surfaces 6 assumptions and 4 risks, including budget, source compliance, and feedback sufficiency. A covers some of the same ideas informally, but they are not enumerated as challengeable artifacts.
