# Evaluation Rubric — Job Copilot Pipeline

Each objective is scored independently for Condition A and Condition B.
Score: 0 = not addressed | 0.5 = partially addressed | 1 = fully addressed

---

## Functional Objectives (expected from both conditions)

| # | Objective | A score | B score | Notes |
|---|-----------|---------|---------|-------|
| 1 | Correct runtime chosen for browser automation (Node.js, not Python, for Playwright) | 0 | 0.5 | Both chose Python (wrong). A: implicit, no rationale. B: explicit `dec_python_runtime` node with `alternatives_considered: [Node.js, Go]` — auditable even if wrong. |
| 2 | Auth-protected scraping (Wellfound, LinkedIn) addressed with explicit strategy | 1 | 1 | Both: cookie-based auth strategy, explicitly designed. B adds `dec_cookie_auth` with alternatives considered. |
| 3 | Rate limiting handled (per-domain throttling, backoff, retry logic) | 1 | 1 | Both: exponential backoff, randomized jitter, 429 handling. B also captures `risk_rate_limiting` as a severity-0.7 node. |
| 4 | PDF generation produces consistently formatted output across varying job descriptions | 0.5 | 0.5 | Both use WeasyPrint + Jinja2 template. Neither fully addresses cross-job formatting variance. B adds `risk_pdf_formatting` (severity 0.4) and `asm_weasyprint_quality` (confidence 0.7). |
| 5 | Pipeline recovers from partial failures without full restart (checkpointing or job queue) | 1 | 1 | Both: stage-based checkpointing. B adds circuit breaker (>50% item failure halts stage gracefully). |
| 6 | Database schema handles deduplication across runs | 1 | 1 | Both: composite unique constraint (url + source). A: SHA-256 + fuzzy title match. B: `req_dedup` requirement node, `comp_db` implements it. |
| 7 | Testing strategy decoupled from live sites (mocks, fixtures, or recorded sessions) | 1 | 1 | Both: recorded HTML fixture pattern. B captures `dec_fixture_testing` as explicit decision node. |

## Structural Objectives (graph-specific — condition B only)

| # | Objective | A score | B score | Notes |
|---|-----------|---------|---------|-------|
| 8  | Key architectural decisions recorded with explicit rationale (e.g. Node.js vs Python, which job boards, PDF library choice) | 0.5 | 1 | A: 5-bullet prose section, no alternatives listed. B: 10 decision nodes, each with `rationale` + `alternatives_considered`. |
| 9  | Implicit assumptions surfaced (e.g. "Playwright behaves the same across runtimes", "job board structure is stable", "LLM filtering accuracy is sufficient") | 0 | 1 | A: zero explicit assumptions. B: 8 assumption nodes with confidence scores — `asm_playwright_stealth` (0.5), `asm_cookie_longevity` (0.6), `asm_site_stability` (0.6), `asm_weasyprint_quality` (0.7), etc. |
| 10 | Risks identified (e.g. bot detection changes, rate limit policy changes, auth flow changes on Wellfound, PDF formatting edge cases, overnight run duration estimates) | 0.5 | 1 | A: 6-item informal prose table. B: 9 risk nodes with severity scores, linked to decisions/assumptions via `conflicts_with` and `invalidates` edges. |

---

## Summary Counts (fill in after both sessions)

| Metric | Condition A | Condition B |
|--------|-------------|-------------|
| Functional objectives hit (out of 7) | 5.5 / 7 | 6 / 7 |
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

3. **Auditable wrong decision**: Both conditions chose Python for Playwright (the less reliable runtime for this use case). A recorded this implicitly. B's `dec_python_runtime` node documents the choice with `alternatives_considered: ["Node.js + TypeScript", "Go"]` — meaning the mistake is visible, traceable, and challengeable in a way A's is not.
