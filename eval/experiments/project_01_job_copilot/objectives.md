# Evaluation Rubric — Job Copilot Pipeline

Each objective is scored independently for Condition A and Condition B.
Score: 0 = not addressed | 0.5 = partially addressed | 1 = fully addressed

---

## Functional Objectives (expected from both conditions)

| # | Objective | A score | B score | Notes |
|---|-----------|---------|---------|-------|
| 1 | Correct runtime chosen for browser automation (Node.js, not Python, for Playwright) | 0 | 1 | A chose Python (wrong, implicit, no rationale). B chose Node.js + TypeScript — correct choice, explicit `dec_python_runtime` node with `alternatives_considered`. |
| 2 | Auth-protected scraping (Wellfound, LinkedIn) addressed with explicit strategy | 1 | 1 | Both: cookie-based auth strategy, explicitly designed. B adds `dec_cookie_auth` with alternatives considered. |
| 3 | Rate limiting handled (per-domain throttling, backoff, retry logic) | 1 | 1 | Both: exponential backoff, randomized jitter, 429 handling. B also captures `risk_rate_limiting` as a severity-0.7 node. |
| 4 | Resume is genuinely tailored per job (not just template fill-in) | 0 | 1 | A: pure template — injects job title + company into a fixed Jinja2 template; explicitly defers LLM tailoring to "optional later phase." B: full LLM grounded-rewrite pipeline — rewrites bullets, reorders skills, validates against a whitelist to prevent hallucination, regenerates on rejection. |
| 5 | PDF generation produces consistently formatted output across varying job descriptions | 0.5 | 0.5 | A: WeasyPrint + Jinja2. B: Playwright PDF render of Handlebars template. Neither fully addresses cross-job formatting variance. B adds `risk_pdf_formatting` (severity 0.4) and `asm_weasyprint_quality` (confidence 0.7). |
| 6 | Pipeline recovers from partial failures without full restart (checkpointing or job queue) | 1 | 1 | Both: stage-based checkpointing. B adds circuit breaker (>50% item failure halts stage gracefully). |
| 7 | Database schema handles deduplication across runs | 1 | 1 | Both: composite unique constraint (url + source). A: SHA-256 + fuzzy title match. B: `req_dedup` requirement node, `comp_db` implements it. |
| 8 | Testing strategy decoupled from live sites (mocks, fixtures, or recorded sessions) | 1 | 1 | Both: recorded HTML fixture pattern. B captures `dec_fixture_testing` as explicit decision node. |

## Structural Objectives (graph-specific — condition B only)

| # | Objective | A score | B score | Notes |
|---|-----------|---------|---------|-------|
| 9  | Key architectural decisions recorded with explicit rationale (e.g. Node.js vs Python, which job boards, PDF library choice) | 0.5 | 1 | A: 5-bullet prose section, no alternatives listed. B: 10 decision nodes, each with `rationale` + `alternatives_considered`. |
| 10 | Implicit assumptions surfaced (e.g. "Playwright behaves the same across runtimes", "job board structure is stable", "LLM filtering accuracy is sufficient") | 0 | 1 | A: zero explicit assumptions. B: 8 assumption nodes with confidence scores — `asm_playwright_stealth` (0.5), `asm_cookie_longevity` (0.6), `asm_site_stability` (0.6), `asm_weasyprint_quality` (0.7), etc. |
| 11 | Risks identified (e.g. bot detection changes, rate limit policy changes, auth flow changes on Wellfound, PDF formatting edge cases, overnight run duration estimates) | 0.5 | 1 | A: 6-item informal prose table. B: 9 risk nodes with severity scores, linked to decisions/assumptions via `conflicts_with` and `invalidates` edges. |

---

## Summary Counts (fill in after both sessions)

| Metric | Condition A | Condition B |
|--------|-------------|-------------|
| Functional objectives hit (out of 8) | 5.5 / 8 | 7.5 / 8 |
| Structural objectives hit (out of 3) | 1 / 3 | 3 / 3 |
| Total decision nodes in plan | 0 (no graph) | 10 |
| Total assumption nodes surfaced | 0 (no graph) | 8 |
| Total risk nodes surfaced | 0 (no graph) | 9 |
| Graph nodes total | — | 57 |
| Graph edges total | — | 64 |

---

## Key Qualitative Catches

Specific things condition B surfaced that condition A missed or glossed over:

1. **Implicit assumptions made explicit**: B surfaced `asm_playwright_stealth` (confidence 0.5) — the plan assumes playwright-stealth is sufficient for LinkedIn/Wellfound bot evasion. A made the same assumption silently. B also captured `asm_cookie_longevity` (0.6) — that session cookies survive a 2–4 hour overnight run — which is a real and non-obvious failure mode.

2. **Broken feedback loop still produced better structure**: B generated both graph versions in a single final message (not iteratively). Despite no true feedback loop, the graph format forced explicit enumeration: 9 risk nodes (vs 6 informal prose items in A), 8 assumption nodes (vs 0 in A), and all decisions linked to their motivating objectives via edges.

3. **Correct runtime and LLM tailoring**: B chose Node.js + TypeScript (correct for Playwright). A chose Python (wrong, implicit). More significantly, B included a full LLM grounded-rewrite pipeline for resume tailoring — rewrites bullets per job description, validates output against a whitelist, regenerates on hallucination. A explicitly deferred LLMs: "optional local LLM hook later — omit from v1." This is the largest functional gap between conditions.

4. **Risk A missed entirely**: B surfaced `risk_legal_tos` (severity 0.5) — scraping LinkedIn and Wellfound may violate their Terms of Service. A's risk table covers technical failure modes but never raises the legal/ToS dimension at all.
