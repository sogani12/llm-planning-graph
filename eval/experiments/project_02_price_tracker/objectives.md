# Evaluation Rubric — Automated Price Tracker

Each objective is scored independently for Condition A and Condition B.
Score: 0 = not addressed | 0.5 = partially addressed | 1 = fully addressed

---

## ★ Final Scores

| | Condition A | Condition B |
|---|---|---|
| **Total Score** | **7.5 / 10** | **10 / 10** |
| Functional (out of 7) | 6 / 7 | 7 / 7 |
| Structural (out of 3) | 1 / 3 | 3 / 3 |

---

## Functional Objectives (expected from both conditions)

| # | Objective | A score | B score | Notes |
|---|-----------|---------|---------|-------|
| 1 | Correct runtime/library chosen for browser automation (Playwright chosen with justification) | 1 | 1 | Both chose Playwright. A: brief mention of stealth patches in prose. B: `dec_playwright` node lists Selenium and requests+BS4 as rejected alternatives with explicit rationale. |
| 2 | Auth-protected scraping (Amazon, Walmart) addressed with explicit strategy | 0.5 | 1 | Both use cookie-file-based auth. A: mentioned in passing under scraper design. B: explicit `dec_cookie_auth` decision node with `req_auth_scraping` requirement and `asm_cookie_longevity` assumption linked via edges. |
| 3 | Rate limiting handled gracefully (per-domain throttling, backoff, retry on 429/503) | 1 | 1 | Both: exponential backoff (5s→10s→20s), 90s delay on bot detection, randomised inter-product delays. B also captures `risk_bot_detection` (severity 0.85) linked to `dec_playwright` via `conflicts_with`. |
| 4 | Price history stored correctly — schema supports multiple price points per product over time | 1 | 1 | Both: `price_history` table with `product_id`, `scraped_at`, `run_id`. B adds `iface_price_record` interface node and `obj_price_history` objective explicitly linked to `comp_db`. |
| 5 | Pipeline recovers from partial failures without full restart | 0.5 | 1 | A: per-scrape retry and systemd restart mentioned but no explicit checkpointing. B: `req_error_recovery` requirement node, per-product error isolation explicit in pipeline design, `risk_run_duration` node captures the overnight timing risk. |
| 6 | Database schema handles deduplication across runs | 1 | 1 | Both: `UNIQUE INDEX uq_price_per_day` on `(product_id, date(scraped_at))`. B captures this as `req_dedup` requirement node with `comp_db` linked via `implements` edge. |
| 7 | Testing strategy decoupled from live sites | 1 | 1 | Both: fixture HTML files + `unittest.mock` for SMTP. B adds `dec_fixture_testing` decision node, `tst_scraper_fixtures` test node linked to `comp_scraper` via `verifies`, and `tst_dedup` linked to `req_dedup` via `guards_against`. |

## Structural Objectives (graph-specific — condition B only)

| # | Objective | A score | B score | Notes |
|---|-----------|---------|---------|-------|
| 8  | Key architectural decisions recorded with explicit rationale and alternatives | 0.5 | 1 | A: brief prose rationale ("SQLite is the right fit here") with no alternatives listed. B: 7 decision nodes (`dec_python_runtime`, `dec_playwright`, `dec_sqlite`, `dec_email_alerts`, `dec_apscheduler`, `dec_cookie_auth`, `dec_fixture_testing`), each with `rationale` and `alternatives_considered`. |
| 9  | Implicit assumptions surfaced explicitly | 0 | 1 | A: zero explicit assumptions anywhere. B: 5 assumption nodes — `asm_url_stable` (confidence 0.75), `asm_price_in_html` (0.70), `asm_cookie_longevity` (0.60), `asm_bot_detection_static` (0.55), `asm_smtp_reliable` (0.90) — all with confidence scores and `validated: false`. |
| 10 | Risks identified with severity | 0.5 | 1 | A: informal "Risks and Limitations" prose section, no severity scores, no links to decisions. B: 6 risk nodes with severity scores (`risk_bot_detection` 0.85, `risk_selector_change` 0.70, `risk_captcha` 0.80, `risk_cookie_expiry` 0.65, `risk_alert_failure` 0.50, `risk_run_duration` 0.40), each linked via `conflicts_with` or `invalidates` edges. |

---

## Summary Counts

| Metric | Condition A | Condition B |
|--------|-------------|-------------|
| Functional objectives hit (out of 7) | 6 / 7 | 7 / 7 |
| Structural objectives hit (out of 3) | 1 / 3 | 3 / 3 |
| Total decision nodes in plan | 0 (no graph) | 7 |
| Total assumption nodes surfaced | 0 (no graph) | 5 |
| Total risk nodes surfaced | 0 (no graph) | 6 |
| Graph nodes total | — | 36 |
| Graph edges total | — | 35 |

---

## Key Qualitative Catches

Specific things condition B surfaced that condition A missed or glossed over:

1. **Cookie longevity is an unvalidated assumption, not a solved problem.** Both plans use cookie-based auth for Amazon, but only Condition B surfaces `asm_cookie_longevity` (confidence 0.60, validated: false) — the explicit acknowledgment that cookies may expire before the next nightly run. Condition A mentions cookie expiry in the "Risks" prose but treats it as a known edge case rather than an unvalidated architectural bet. The graph forces the distinction.

2. **`asm_bot_detection_static` (confidence 0.55) was the lowest-confidence assumption in the graph — and rightly so.** The plan assumes stealth patches stay effective long enough to be worth building around. Condition B captured this as a named, low-confidence assumption linked to `dec_playwright` via an `assumes` edge, meaning any reader can immediately see which architectural decision breaks if that assumption fails. Condition A has no equivalent traceability.

3. **Condition A's recovery story has a gap condition B closes.** Condition A describes per-scrape retries and systemd restart but does not address the scenario where the pipeline *completes* but most products silently return `ParseFailureError` (e.g. after a site redesign). Condition B's `risk_selector_change` (severity 0.70) node prompted the explicit design of a "health warning if >20% failed" email — a concrete guard that addresses the gap.
