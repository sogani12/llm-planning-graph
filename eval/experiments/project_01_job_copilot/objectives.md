# Evaluation Rubric — Job Copilot Pipeline

Each objective is scored independently for Condition A and Condition B.
Score: 0 = not addressed | 0.5 = partially addressed | 1 = fully addressed

---

## Functional Objectives (expected from both conditions)

| # | Objective | A score | B score | Notes |
|---|-----------|---------|---------|-------|
| 1 | Correct runtime chosen for browser automation (Node.js, not Python, for Playwright) | 0 | 0.5 | A chose Python — implicit, no rationale. B chose Python but recorded `dec_stack_python_playwright` with `alternatives_considered: ["Node+Playwright", "Polyglot"]` — wrong choice, but visible and challengeable. |
| 2 | Auth-protected scraping (Wellfound, LinkedIn) addressed with explicit strategy | 1 | 1 | Both: session-based auth. B adds two decision nodes — `dec_auth_playwright_storage` and `dec_auth_host_volume_canonical` — each with rationale and rejected alternatives. |
| 3 | Rate limiting handled (per-domain throttling, backoff, retry logic) | 1 | 1 | Both: exponential backoff, jitter, per-board caps. B captures `dec_conservative_automation` as an explicit decision with `throughput-first` as the rejected alternative. |
| 4 | Resume is genuinely tailored per job (not just template fill-in) | 0 | 1 | A: Jinja2 template — injects job title + company only; LLM deferred to "optional later phase." B: ChatGPT UI driven by Playwright; structured JSON output validated against schema; defer-on-failure path explicit. |
| 5 | Scraping adapts to layout heterogeneity across job boards | 0 | 1 | A: hand-written selectors per site; no strategy for boards with varying layouts. B: `dec_scrape_llm_planner` — LLM generates scrape plans from DOM/accessibility snapshots, validated against a schema before execution. Neither A nor old graph-augmented runs surfaced this. |
| 6 | PDF generation produces consistently formatted output | 0.5 | 0.5 | A: WeasyPrint + Jinja2. B: DOCX filled via docxtpl, exported via LibreOffice headless. B surfaces `risk_docx_pdf_fidelity` (severity 0.6). Neither fully addresses formatting variance across job descriptions. |
| 7 | Pipeline recovers from partial failures without full restart | 1 | 1 | Both: stage-based checkpointing. B adds `req_defer_tailoring_on_failure` as an explicit requirement — failed tailoring jobs are recorded with reason codes and skipped rather than aborting the run. |
| 8 | Database schema handles deduplication across runs | 1 | 1 | Both: composite unique key. B uses a three-tier fallback: stable `(source, source_job_id)` → canonical URL hash → description hash. |
| 9 | Testing strategy decoupled from live sites (mocks, fixtures, or recorded sessions) | 1 | 1 | Both: saved HTML fixtures. B adds scrape plan replay tests — fixture page captures + expected plan outputs exercised without a live LLM or browser. |

## Structural Objectives (graph-specific — condition B only)

| # | Objective | A score | B score | Notes |
|---|-----------|---------|---------|-------|
| 10 | Key architectural decisions recorded with explicit rationale | 0.5 | 1 | A: 5-bullet prose section, no alternatives. B: 14 decision nodes, each with `rationale` + `alternatives_considered` where meaningful alternatives exist. |
| 11 | Implicit assumptions surfaced with confidence scores | 0 | 1 | A: zero explicit assumptions. B: 6 assumption nodes — `asm_chatgpt_ui_available` (0.58), `asm_session_duration` (0.66), `asm_libreoffice_ok` (0.72) — correctly calibrated as uncertain. |
| 12 | Risks identified, severity-rated, and linked to decisions | 0.5 | 1 | A: informal prose list. B: 6 risk nodes with severity scores linked via `conflicts_with` and `invalidates` edges. Notably, B surfaced `risk_chatgpt_ui_fragility` (severity 0.88) against its own chosen tailoring approach. |

---

## Summary Counts

| Metric | Condition A | Condition B |
|--------|-------------|-------------|
| Functional objectives hit (out of 9) | 5.5 / 9 | 8 / 9 |
| Structural objectives hit (out of 3) | 1 / 3 | 3 / 3 |
| Total decision nodes in plan | 0 (no graph) | 14 |
| Total assumption nodes surfaced | 0 (no graph) | 6 |
| Total risk nodes surfaced | 0 (no graph) | 6 |
| Graph nodes total | — | 55 |
| Graph edges total | — | 85 |

---

## Key Qualitative Catches

Specific things condition B surfaced that condition A missed or glossed over:

1. **LLM-assisted scrape planning**: B introduced `dec_scrape_llm_planner` — using an LLM to generate scrape execution plans from DOM/accessibility snapshots rather than hand-writing per-site selectors. A had no strategy for layout heterogeneity across boards. This emerged from the graph forcing the agent to think explicitly about how each component would handle its inputs.

2. **Self-critical risk surfacing**: B recorded `risk_chatgpt_ui_fragility` at severity 0.88 — one of its highest-severity risks — against its own chosen tailoring approach. A surfaced no risks about its own architectural choices. The graph's `conflicts_with` edge structure pushed the agent to evaluate whether the approach it selected was actually reliable.

3. **Wrong choice made auditable**: Both conditions chose Python for Playwright. A's choice is invisible — buried in implementation prose. B's `dec_stack_python_playwright` node lists `Node+Playwright` as a considered alternative with explicit rationale for rejection. The mistake is traceable and challengeable in a way A's is not.

4. **Defer-on-failure as a first-class requirement**: B captured `req_defer_tailoring_on_failure` as an explicit requirement node — failed LLM tailoring jobs are written to the DB with reason codes and the pipeline continues. A's error handling was described in prose without distinguishing recoverable from fatal failures at the tailoring stage.
