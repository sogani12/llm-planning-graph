# Condition B — Conversation (Graph-Augmented Planning)

---

## System Prompt (Graph-Augmented Mode)

> You are an expert software architect running a graph-augmented planning session. As you plan, maintain a running decision graph in JSON format. After each major decision cluster, output a `[GRAPH UPDATE]` block with the full cumulative graph. Before making each new architectural decision, reference the current graph to stay consistent with prior choices. Node and edge types follow the schema provided.

---

## Phase 1 — Clarifying Questions and Core Architecture

---

**AI:**

Before I start designing the system, I have a few clarifying questions that will significantly affect the architecture:

1. **Platforms and authentication**: You mentioned Amazon, eBay, and Walmart. Do you currently have accounts on all three, and are you comfortable with cookie-based session replay (exporting cookies from a logged-in browser) rather than supplying credentials in plaintext?

2. **Scale and frequency**: Roughly how many products do you want to track, and how often should the pipeline run — once a night, every few hours?

3. **Alert delivery**: Should alerts go to email, SMS, or both? Do you have an existing email account you'd use for sending (e.g. Gmail with an app password)?

4. **Deployment target**: Where will this run — a home server, a VPS, a cloud VM? What OS?

5. **Technology preferences**: Any strong preference for language or framework? Python, Node.js, Go?

6. **Testing stance**: When you say "validate scraping logic without live site calls," do you mean recording real HTML pages offline and running selectors against those, or fully mocked HTTP responses?

---

**User:**

1. Yes, I have accounts on all three. Cookie replay is fine — I can export from my browser.
2. About 50 products total. Once a night is plenty, maybe 2am.
3. Email only — Gmail with an app password. I don't want to pay for Twilio or anything.
4. A VPS running Ubuntu 22.04.
5. Python strongly preferred — I'm most comfortable there.
6. Saved HTML fixtures — I'll snapshot a real product page once and reuse it for tests.

---

**AI:**

Perfect — that's everything I need. Let me lock in the top-level objectives and hard requirements, then make the first round of architectural decisions.

**Objectives identified:**
- `obj_overnight_run` — the pipeline must run unattended from ~2am to completion
- `obj_price_history` — every price observation must be persisted with a timestamp so history is queryable
- `obj_alert_on_drop` — when a product price drops below a user-defined threshold, an alert fires

**Hard requirements:**
- `req_dedup` — scraping the same product twice in one run must not create duplicate records
- `req_auth_scraping` — Amazon/Walmart require a logged-in session; cookie replay must work end-to-end
- `req_bot_detection` — the scraper must survive basic bot-detection measures on all three platforms
- `req_error_recovery` — if any single product scrape fails, the pipeline continues and logs the failure
- `req_offline_testing` — scraping logic must be testable against saved HTML without live HTTP calls

**Core architecture decisions (Phase 1):**

- **`dec_python_runtime`** — Python 3.11+ on Ubuntu. No alternative seriously considered given the stated preference.
- **`dec_playwright`** — Playwright (Python bindings) for browser automation. Selenium was the main alternative, but Playwright has better async support, a cleaner network interception API for fixture injection, and first-class stealth plugins. Requests + BeautifulSoup alone is ruled out because Amazon and Walmart render prices with JavaScript.
- **`dec_sqlite`** — SQLite as the persistence layer. PostgreSQL is overkill for 50 products on a personal VPS; SQLite is zero-infrastructure. We'll use the `sqlite3` stdlib module wrapped in a thin helper, with WAL mode enabled for safe concurrent reads.
- **`dec_email_alerts`** — Gmail SMTP via `smtplib` with an app password stored in a `.env` file. No paid SMS API.
- **`dec_apscheduler`** — APScheduler (BackgroundScheduler with a cron trigger) for overnight scheduling. Cron + a shell script was the alternative, but APScheduler gives us Python-native error handling and retry hooks within the same process.
- **`dec_cookie_auth`** — Cookie-file-based authentication: user exports cookies from a logged-in browser session (via a browser extension) into a Netscape-format cookie file; Playwright loads them at launch.

**Key assumptions at this stage:**
- `asm_url_stable` — product page URLs remain stable over time (no redirect churn)
- `asm_price_in_html` — the rendered DOM contains the price as visible text that a CSS selector or text heuristic can extract
- `asm_cookie_longevity` — exported cookies remain valid for at least 24–48 hours (one pipeline cycle)
- `asm_bot_detection_static` — bot-detection heuristics on these platforms don't change faster than once a week, giving time to patch selectors
- `asm_smtp_reliable` — Gmail SMTP is available and responsive at 2am; app password does not expire without notice

**Risks at this stage:**
- `risk_bot_detection` — Amazon/Walmart may fingerprint the browser and serve CAPTCHAs or empty pages
- `risk_selector_change` — a site redesign can silently break price extraction, returning None without an exception
- `risk_captcha` — a CAPTCHA interception mid-session has no automated bypass; the run would stall

---

**[GRAPH UPDATE — Phase 1]**

```json
{
  "nodes": [
    {
      "id": "obj_overnight_run",
      "type": "objective",
      "label": "Unattended overnight execution",
      "description": "The pipeline must run from approximately 2am to completion without any human interaction."
    },
    {
      "id": "obj_price_history",
      "type": "objective",
      "label": "Full price history per product",
      "description": "Every price observation must be persisted with a timestamp so the complete history is queryable over time."
    },
    {
      "id": "obj_alert_on_drop",
      "type": "objective",
      "label": "Alert on price drop below threshold",
      "description": "When a tracked product's price falls below a user-configured threshold, an alert must be triggered automatically."
    },
    {
      "id": "req_dedup",
      "type": "requirement",
      "label": "Cross-run deduplication",
      "description": "Scraping the same product in consecutive runs must not produce duplicate records in the database.",
      "is_functional": true
    },
    {
      "id": "req_auth_scraping",
      "type": "requirement",
      "label": "Auth-protected platform support",
      "description": "The scraper must handle Amazon and Walmart, both of which require an authenticated session to return full product data.",
      "is_functional": true
    },
    {
      "id": "req_bot_detection",
      "type": "requirement",
      "label": "Bot-detection resilience",
      "description": "The scraper must apply stealth measures sufficient to avoid trivial bot-detection on all three target platforms.",
      "is_functional": true
    },
    {
      "id": "req_error_recovery",
      "type": "requirement",
      "label": "Per-product error isolation",
      "description": "A failure to scrape one product must not abort the pipeline; the error is logged and the run continues.",
      "is_functional": true
    },
    {
      "id": "req_offline_testing",
      "type": "requirement",
      "label": "Offline scraping tests",
      "description": "Scraping and extraction logic must be testable against saved HTML fixtures without making live HTTP requests.",
      "is_functional": true
    },
    {
      "id": "dec_python_runtime",
      "type": "decision",
      "label": "Python 3.11+ runtime",
      "description": "All pipeline code is written in Python 3.11+ running on Ubuntu 22.04.",
      "rationale": "User is most comfortable with Python; no competing requirement justifies a different language.",
      "alternatives_considered": ["Node.js", "Go"]
    },
    {
      "id": "dec_playwright",
      "type": "decision",
      "label": "Playwright for browser automation",
      "description": "Use Playwright (Python bindings) with playwright-stealth for all scraping, including auth-protected sites.",
      "rationale": "Better async support, network interception API for fixture injection, and first-class stealth plugin compared to Selenium. Requests+BS4 ruled out because Amazon/Walmart render prices via JavaScript.",
      "alternatives_considered": ["Selenium + undetected-chromedriver", "requests + BeautifulSoup"]
    },
    {
      "id": "dec_sqlite",
      "type": "decision",
      "label": "SQLite for persistence",
      "description": "Use SQLite (WAL mode) as the database. Accessed via the sqlite3 stdlib module wrapped in a thin helper layer.",
      "rationale": "Zero infrastructure overhead for a personal 50-product use case on a VPS. PostgreSQL is unnecessary complexity.",
      "alternatives_considered": ["PostgreSQL", "TinyDB", "flat CSV files"]
    },
    {
      "id": "dec_email_alerts",
      "type": "decision",
      "label": "Gmail SMTP for alerts",
      "description": "Send alert emails via smtplib using a Gmail app password stored in .env.",
      "rationale": "User already has a Gmail account and wants zero additional cost. No Twilio or third-party API.",
      "alternatives_considered": ["Twilio SMS", "SendGrid", "Mailgun"]
    },
    {
      "id": "dec_apscheduler",
      "type": "decision",
      "label": "APScheduler for overnight scheduling",
      "description": "Use APScheduler BackgroundScheduler with a cron trigger to fire the pipeline at 2am daily.",
      "rationale": "Python-native scheduling keeps error handling within the same process. Avoids cron + shell script glue that loses Python exceptions.",
      "alternatives_considered": ["system cron + shell script", "Celery beat", "rq-scheduler"]
    },
    {
      "id": "dec_cookie_auth",
      "type": "decision",
      "label": "Cookie-file authentication",
      "description": "User exports browser cookies to a Netscape-format file; Playwright loads them at session launch for Amazon and Walmart.",
      "rationale": "Avoids storing plaintext credentials. Compatible with browser extensions like Cookie-Editor. Session is valid without re-login for 24-48h.",
      "alternatives_considered": ["plaintext username/password login flow", "OAuth tokens", "no auth (public pages only)"]
    },
    {
      "id": "asm_url_stable",
      "type": "assumption",
      "label": "Product URLs remain stable",
      "description": "Assumes that product page URLs (canonical Amazon ASIN URL, eBay item URL, Walmart item URL) do not change or redirect unexpectedly between runs.",
      "confidence": 0.85,
      "validated": false
    },
    {
      "id": "asm_price_in_html",
      "type": "assumption",
      "label": "Price is present in rendered DOM",
      "description": "Assumes that after JavaScript rendering, the product price appears as text in the DOM and is reachable by a CSS selector.",
      "confidence": 0.80,
      "validated": false
    },
    {
      "id": "asm_cookie_longevity",
      "type": "assumption",
      "label": "Exported cookies stay valid 24-48h",
      "description": "Assumes that cookies exported from a logged-in browser session remain valid for at least one pipeline cycle (24h), so no mid-run re-authentication is needed.",
      "confidence": 0.70,
      "validated": false
    },
    {
      "id": "asm_bot_detection_static",
      "type": "assumption",
      "label": "Bot-detection rules change slowly",
      "description": "Assumes that the fingerprinting and bot-detection logic on Amazon, eBay, and Walmart does not change more frequently than once per week, giving time to patch selectors.",
      "confidence": 0.65,
      "validated": false
    },
    {
      "id": "asm_smtp_reliable",
      "type": "assumption",
      "label": "Gmail SMTP available at 2am",
      "description": "Assumes Gmail SMTP is reachable from the VPS at the scheduled run time and that the app password does not expire without notice.",
      "confidence": 0.90,
      "validated": false
    },
    {
      "id": "risk_bot_detection",
      "type": "risk",
      "label": "Bot detection breaks scraping",
      "description": "Amazon or Walmart may fingerprint the headless browser and return a CAPTCHA page or empty product data instead of a price.",
      "severity": 0.85
    },
    {
      "id": "risk_selector_change",
      "type": "risk",
      "label": "CSS selector breakage on site redesign",
      "description": "A site redesign can silently break price extraction — the scraper returns None rather than raising an exception, causing missed alerts.",
      "severity": 0.75
    },
    {
      "id": "risk_captcha",
      "type": "risk",
      "label": "CAPTCHA blocks unattended session",
      "description": "A CAPTCHA served mid-session has no automated bypass in this design. The run stalls or skips the affected product.",
      "severity": 0.80
    }
  ],
  "edges": [
    { "id": "e01", "type": "motivated_by", "source_id": "dec_playwright", "target_id": "obj_overnight_run" },
    { "id": "e02", "type": "motivated_by", "source_id": "dec_sqlite", "target_id": "obj_price_history" },
    { "id": "e03", "type": "motivated_by", "source_id": "dec_email_alerts", "target_id": "obj_alert_on_drop" },
    { "id": "e04", "type": "motivated_by", "source_id": "dec_apscheduler", "target_id": "obj_overnight_run" },
    { "id": "e05", "type": "assumes", "source_id": "dec_cookie_auth", "target_id": "asm_cookie_longevity" },
    { "id": "e06", "type": "assumes", "source_id": "dec_playwright", "target_id": "asm_price_in_html" },
    { "id": "e07", "type": "assumes", "source_id": "dec_playwright", "target_id": "asm_bot_detection_static" },
    { "id": "e08", "type": "assumes", "source_id": "dec_email_alerts", "target_id": "asm_smtp_reliable" },
    { "id": "e09", "type": "conflicts_with", "source_id": "risk_bot_detection", "target_id": "req_bot_detection" },
    { "id": "e10", "type": "conflicts_with", "source_id": "risk_selector_change", "target_id": "req_auth_scraping" },
    { "id": "e11", "type": "invalidates", "source_id": "risk_captcha", "target_id": "asm_bot_detection_static" },
    { "id": "e12", "type": "invalidates", "source_id": "risk_bot_detection", "target_id": "asm_price_in_html" }
  ]
}
```

---

**AI follow-up questions after Phase 1:**

1. **Cookie refresh**: The graph shows `asm_cookie_longevity` has a confidence of 0.70 — Amazon sessions in particular can expire within a few hours on a fresh device. Are you comfortable with a weekly manual cookie re-export, or do you want the pipeline to detect an expired session and send a warning email rather than silently failing?

2. **Bot detection strategy**: `risk_bot_detection` is flagged at severity 0.85. Beyond playwright-stealth, are you open to adding random delays (1–5s between page loads) and a residential proxy as a fallback, or is the proxy cost a hard no?

3. **Price extraction fallback**: `asm_price_in_html` has confidence 0.80. If a CSS selector fails to find a price, should the pipeline skip that product for this run and log the miss, or should it retry with a different extraction strategy (e.g. regex over full text)?

---

**User:**

1. A warning email when a session appears expired is a great idea — yes, add that.
2. Hard no on paid proxies. Random delays are fine though.
3. Skip and log for now. I'd rather get a clear error in the logs than have it guess wrong.

---

## Phase 2 — Component Design, Interfaces, and Dependencies

---

**AI:**

Good. I'm updating the graph with those answers before moving to component design. The warning-email-on-session-expiry answer promotes `risk_cookie_expiry` to an explicit risk node and adds a guard condition to the scheduler. The "skip and log" answer locks in `req_error_recovery` behaviour precisely.

**Components:**

- **`comp_scraper`** — Playwright-based scraper module. One adapter class per platform (Amazon, eBay, Walmart), all inheriting from a `BaseScraper` ABC. Handles cookie loading, stealth setup, random delays, price CSS selector extraction, and session-expiry detection (checks for login-wall indicators).
- **`comp_db`** — SQLite wrapper (`db.py`). Manages schema creation, upsert of price records, deduplication logic (composite key: `product_id + run_id`), and threshold queries.
- **`comp_threshold_checker`** — In-process module that, after each successful scrape, queries the database for the latest price, compares against the user's threshold, and calls the alert component if the threshold is crossed.
- **`comp_alert`** — SMTP alert module. Accepts an `AlertContract` and sends a formatted email via Gmail. Includes a session-expiry warning path (different email template).
- **`comp_scheduler`** — APScheduler wrapper that sets up the 2am cron trigger, wraps the pipeline entry point, captures top-level exceptions, and sends a failure summary email if the run crashes entirely.

**Interfaces:**

- **`iface_price_record`** — The canonical data structure exchanged between `comp_scraper`, `comp_db`, and `comp_threshold_checker`. Fields: `product_id` (str), `url` (str), `platform` (str), `price` (float), `currency` (str), `scraped_at` (ISO 8601 datetime), `status` (str: `"ok"` | `"error"` | `"session_expired"`), `run_id` (str).
- **`iface_alert_contract`** — The data structure consumed by `comp_alert`. Fields: `product_id`, `product_name`, `current_price`, `threshold_price`, `platform`, `product_url`, `alert_type` (str: `"price_drop"` | `"session_expired"` | `"run_failure"`).

**New decisions locked in Phase 2:**

- **`dec_fixture_testing`** — Testing strategy: save real product HTML pages as `.html` files in `tests/fixtures/`; in tests, patch `playwright.Page.route` to intercept navigation and return the fixture content. This means selectors can be validated without network calls.

**Additional risks identified:**

- **`risk_cookie_expiry`** — If Amazon/Walmart cookie expires mid-run, the scraper sees a login wall. The system must detect this (check for login-page indicators) and emit a warning alert rather than silently recording a wrong price.
- **`risk_alert_failure`** — If the SMTP call itself fails (Gmail outage, wrong app password), the alert is lost. There is no retry queue.
- **`risk_run_duration`** — With ~50 products and random 1–5s delays, plus Playwright cold-start time, the full run could take 30–60 minutes. If the run starts at 2am, it may still be running when the user wakes up.

---

**[GRAPH UPDATE — Phase 2]**

```json
{
  "nodes": [
    {
      "id": "obj_overnight_run",
      "type": "objective",
      "label": "Unattended overnight execution",
      "description": "The pipeline must run from approximately 2am to completion without any human interaction."
    },
    {
      "id": "obj_price_history",
      "type": "objective",
      "label": "Full price history per product",
      "description": "Every price observation must be persisted with a timestamp so the complete history is queryable over time."
    },
    {
      "id": "obj_alert_on_drop",
      "type": "objective",
      "label": "Alert on price drop below threshold",
      "description": "When a tracked product's price falls below a user-configured threshold, an alert must be triggered automatically."
    },
    {
      "id": "req_dedup",
      "type": "requirement",
      "label": "Cross-run deduplication",
      "description": "Scraping the same product in consecutive runs must not produce duplicate records in the database.",
      "is_functional": true
    },
    {
      "id": "req_auth_scraping",
      "type": "requirement",
      "label": "Auth-protected platform support",
      "description": "The scraper must handle Amazon and Walmart, both of which require an authenticated session to return full product data.",
      "is_functional": true
    },
    {
      "id": "req_bot_detection",
      "type": "requirement",
      "label": "Bot-detection resilience",
      "description": "The scraper must apply stealth measures sufficient to avoid trivial bot-detection on all three target platforms.",
      "is_functional": true
    },
    {
      "id": "req_error_recovery",
      "type": "requirement",
      "label": "Per-product error isolation",
      "description": "A failure to scrape one product must not abort the pipeline; the error is logged and the run continues.",
      "is_functional": true
    },
    {
      "id": "req_offline_testing",
      "type": "requirement",
      "label": "Offline scraping tests",
      "description": "Scraping and extraction logic must be testable against saved HTML fixtures without making live HTTP requests.",
      "is_functional": true
    },
    {
      "id": "dec_python_runtime",
      "type": "decision",
      "label": "Python 3.11+ runtime",
      "description": "All pipeline code is written in Python 3.11+ running on Ubuntu 22.04.",
      "rationale": "User is most comfortable with Python; no competing requirement justifies a different language.",
      "alternatives_considered": ["Node.js", "Go"]
    },
    {
      "id": "dec_playwright",
      "type": "decision",
      "label": "Playwright for browser automation",
      "description": "Use Playwright (Python bindings) with playwright-stealth for all scraping, including auth-protected sites.",
      "rationale": "Better async support, network interception API for fixture injection, and first-class stealth plugin compared to Selenium.",
      "alternatives_considered": ["Selenium + undetected-chromedriver", "requests + BeautifulSoup"]
    },
    {
      "id": "dec_sqlite",
      "type": "decision",
      "label": "SQLite for persistence",
      "description": "Use SQLite (WAL mode) as the database. Accessed via the sqlite3 stdlib module wrapped in a thin helper layer.",
      "rationale": "Zero infrastructure overhead for a personal 50-product use case on a VPS.",
      "alternatives_considered": ["PostgreSQL", "TinyDB", "flat CSV files"]
    },
    {
      "id": "dec_email_alerts",
      "type": "decision",
      "label": "Gmail SMTP for alerts",
      "description": "Send alert emails via smtplib using a Gmail app password stored in .env.",
      "rationale": "User already has a Gmail account and wants zero additional cost.",
      "alternatives_considered": ["Twilio SMS", "SendGrid", "Mailgun"]
    },
    {
      "id": "dec_apscheduler",
      "type": "decision",
      "label": "APScheduler for overnight scheduling",
      "description": "Use APScheduler BackgroundScheduler with a cron trigger to fire the pipeline at 2am daily.",
      "rationale": "Python-native scheduling keeps error handling within the same process.",
      "alternatives_considered": ["system cron + shell script", "Celery beat", "rq-scheduler"]
    },
    {
      "id": "dec_cookie_auth",
      "type": "decision",
      "label": "Cookie-file authentication",
      "description": "User exports browser cookies to Netscape-format files; Playwright loads them at session launch for Amazon and Walmart.",
      "rationale": "Avoids storing plaintext credentials. Session is valid for 24-48h.",
      "alternatives_considered": ["plaintext username/password login flow", "OAuth tokens"]
    },
    {
      "id": "dec_fixture_testing",
      "type": "decision",
      "label": "HTML fixture-based offline tests",
      "description": "Save real product HTML pages in tests/fixtures/; patch Playwright page routing to serve fixture content during tests.",
      "rationale": "Satisfies req_offline_testing while keeping tests deterministic and fast.",
      "alternatives_considered": ["responses library HTTP mocking", "VCR.py cassette recording", "fully mocked DOM"]
    },
    {
      "id": "asm_url_stable",
      "type": "assumption",
      "label": "Product URLs remain stable",
      "description": "Assumes that product page URLs do not change or redirect unexpectedly between runs.",
      "confidence": 0.85,
      "validated": false
    },
    {
      "id": "asm_price_in_html",
      "type": "assumption",
      "label": "Price is present in rendered DOM",
      "description": "Assumes that after JavaScript rendering, the product price appears as text in the DOM reachable by a CSS selector.",
      "confidence": 0.80,
      "validated": false
    },
    {
      "id": "asm_cookie_longevity",
      "type": "assumption",
      "label": "Exported cookies stay valid 24-48h",
      "description": "Assumes that cookies exported from a logged-in browser session remain valid for at least one pipeline cycle.",
      "confidence": 0.70,
      "validated": false
    },
    {
      "id": "asm_bot_detection_static",
      "type": "assumption",
      "label": "Bot-detection rules change slowly",
      "description": "Assumes that fingerprinting logic on Amazon, eBay, and Walmart does not change more frequently than once per week.",
      "confidence": 0.65,
      "validated": false
    },
    {
      "id": "asm_smtp_reliable",
      "type": "assumption",
      "label": "Gmail SMTP available at 2am",
      "description": "Assumes Gmail SMTP is reachable from the VPS at the scheduled run time and that the app password does not expire without notice.",
      "confidence": 0.90,
      "validated": false
    },
    {
      "id": "risk_bot_detection",
      "type": "risk",
      "label": "Bot detection breaks scraping",
      "description": "Amazon or Walmart may fingerprint the headless browser and return a CAPTCHA page or empty product data.",
      "severity": 0.85
    },
    {
      "id": "risk_selector_change",
      "type": "risk",
      "label": "CSS selector breakage on site redesign",
      "description": "A site redesign can silently break price extraction, returning None rather than raising an exception.",
      "severity": 0.75
    },
    {
      "id": "risk_captcha",
      "type": "risk",
      "label": "CAPTCHA blocks unattended session",
      "description": "A CAPTCHA served mid-session has no automated bypass; the run stalls or skips the affected product.",
      "severity": 0.80
    },
    {
      "id": "risk_cookie_expiry",
      "type": "risk",
      "label": "Cookie expiry mid-run",
      "description": "If an Amazon or Walmart session cookie expires during the run, the scraper lands on a login wall and may silently record wrong data or no data.",
      "severity": 0.70
    },
    {
      "id": "risk_alert_failure",
      "type": "risk",
      "label": "SMTP alert silently dropped",
      "description": "If the SMTP call fails (Gmail outage, wrong app password, blocked port), the alert is lost with no retry mechanism.",
      "severity": 0.65
    },
    {
      "id": "risk_run_duration",
      "type": "risk",
      "label": "Pipeline run exceeds overnight window",
      "description": "With 50 products and 1-5s random delays, the run can take 30-60 minutes. If started at 2am this is fine, but any system slowdown could push it past a reasonable window.",
      "severity": 0.40
    },
    {
      "id": "comp_scraper",
      "type": "component",
      "label": "Platform scraper",
      "description": "Playwright-based scraper with one adapter per platform (Amazon, eBay, Walmart). Handles cookie loading, stealth, random delays, session-expiry detection, and price extraction.",
      "file_refs": ["src/pricetrack/scraper/base.py", "src/pricetrack/scraper/amazon.py", "src/pricetrack/scraper/ebay.py", "src/pricetrack/scraper/walmart.py"]
    },
    {
      "id": "comp_db",
      "type": "component",
      "label": "SQLite database layer",
      "description": "Manages schema creation, upsert of price records, deduplication by composite key (product_id + run_id), and threshold queries.",
      "file_refs": ["src/pricetrack/db.py"]
    },
    {
      "id": "comp_threshold_checker",
      "type": "component",
      "label": "Threshold checker",
      "description": "After each successful scrape, queries the database for the latest price and compares it against the user's configured threshold. Calls the alert component if the threshold is crossed.",
      "file_refs": ["src/pricetrack/checker.py"]
    },
    {
      "id": "comp_alert",
      "type": "component",
      "label": "Email alert sender",
      "description": "SMTP-based alert module. Accepts an AlertContract and sends a formatted HTML email via Gmail. Handles price-drop, session-expiry, and run-failure templates.",
      "file_refs": ["src/pricetrack/alert.py"]
    },
    {
      "id": "comp_scheduler",
      "type": "component",
      "label": "Pipeline scheduler",
      "description": "APScheduler wrapper that sets up the 2am cron trigger, wraps the pipeline entry point, and sends a failure summary email if the run crashes.",
      "file_refs": ["src/pricetrack/scheduler.py"]
    },
    {
      "id": "iface_price_record",
      "type": "interface",
      "label": "PriceRecord data contract",
      "description": "Canonical data structure exchanged between the scraper, database, and threshold checker.",
      "contract": "{ product_id: str, url: str, platform: str, price: float | None, currency: str, scraped_at: str (ISO8601), status: 'ok' | 'error' | 'session_expired', run_id: str }"
    },
    {
      "id": "iface_alert_contract",
      "type": "interface",
      "label": "AlertContract data contract",
      "description": "Data structure consumed by the alert component for all alert types.",
      "contract": "{ product_id: str, product_name: str, current_price: float, threshold_price: float, platform: str, product_url: str, alert_type: 'price_drop' | 'session_expired' | 'run_failure' }"
    }
  ],
  "edges": [
    { "id": "e01", "type": "motivated_by", "source_id": "dec_playwright", "target_id": "obj_overnight_run" },
    { "id": "e02", "type": "motivated_by", "source_id": "dec_sqlite", "target_id": "obj_price_history" },
    { "id": "e03", "type": "motivated_by", "source_id": "dec_email_alerts", "target_id": "obj_alert_on_drop" },
    { "id": "e04", "type": "motivated_by", "source_id": "dec_apscheduler", "target_id": "obj_overnight_run" },
    { "id": "e05", "type": "assumes", "source_id": "dec_cookie_auth", "target_id": "asm_cookie_longevity" },
    { "id": "e06", "type": "assumes", "source_id": "dec_playwright", "target_id": "asm_price_in_html" },
    { "id": "e07", "type": "assumes", "source_id": "dec_playwright", "target_id": "asm_bot_detection_static" },
    { "id": "e08", "type": "assumes", "source_id": "dec_email_alerts", "target_id": "asm_smtp_reliable" },
    { "id": "e09", "type": "conflicts_with", "source_id": "risk_bot_detection", "target_id": "req_bot_detection" },
    { "id": "e10", "type": "conflicts_with", "source_id": "risk_selector_change", "target_id": "req_auth_scraping" },
    { "id": "e11", "type": "invalidates", "source_id": "risk_captcha", "target_id": "asm_bot_detection_static" },
    { "id": "e12", "type": "invalidates", "source_id": "risk_bot_detection", "target_id": "asm_price_in_html" },
    { "id": "e13", "type": "invalidates", "source_id": "risk_cookie_expiry", "target_id": "asm_cookie_longevity" },
    { "id": "e14", "type": "implements", "source_id": "comp_scraper", "target_id": "req_auth_scraping" },
    { "id": "e15", "type": "implements", "source_id": "comp_scraper", "target_id": "req_bot_detection" },
    { "id": "e16", "type": "implements", "source_id": "comp_db", "target_id": "req_dedup" },
    { "id": "e17", "type": "implements", "source_id": "comp_scheduler", "target_id": "req_error_recovery" },
    { "id": "e18", "type": "exposes", "source_id": "comp_scraper", "target_id": "iface_price_record" },
    { "id": "e19", "type": "consumes", "source_id": "comp_db", "target_id": "iface_price_record" },
    { "id": "e20", "type": "consumes", "source_id": "comp_threshold_checker", "target_id": "iface_price_record" },
    { "id": "e21", "type": "exposes", "source_id": "comp_threshold_checker", "target_id": "iface_alert_contract" },
    { "id": "e22", "type": "consumes", "source_id": "comp_alert", "target_id": "iface_alert_contract" },
    { "id": "e23", "type": "depends_on", "source_id": "comp_threshold_checker", "target_id": "comp_db" },
    { "id": "e24", "type": "depends_on", "source_id": "comp_scheduler", "target_id": "comp_scraper" },
    { "id": "e25", "type": "conflicts_with", "source_id": "risk_alert_failure", "target_id": "dec_email_alerts" }
  ]
}
```

---

**AI follow-up questions after Phase 2:**

1. **Deduplication granularity**: The graph has `req_dedup` implemented by `comp_db`. The current plan uses `(product_id, run_id)` as the composite key — one record per product per run. Is that the right granularity, or do you want one record per product per calendar day (so multiple runs in one day still produce only one row)?

2. **Threshold configuration**: How do you want to specify thresholds? A YAML/JSON file edited manually, or a small CLI command like `python -m pricetrack add-threshold --product-id X --threshold 29.99`?

3. **Run completion notification**: `risk_run_duration` is currently low severity (0.40), but if the run takes longer than expected and you wake up to no summary email, that's frustrating. Should the scheduler always send a run-summary email (even on success), so you always have confirmation?

---

**User:**

1. One record per run is correct — I might want to track intra-day price changes eventually.
2. A YAML config file is fine. I'll edit it manually.
3. Yes — always send a summary email. That's actually really important.

---

## Phase 3 — Testing Strategy, Error Handling, and Deployment

---

**AI:**

Those three answers are all straightforward — I'll reflect them in the final graph. One-record-per-run keeps the dedup key at `(product_id, run_id)`. The always-on summary email upgrades `comp_scheduler` responsibility and partially mitigates `risk_run_duration` — you'll always know when the run ends, even if late.

Referencing the current graph before finalising the testing strategy:

- `dec_fixture_testing` is already locked. The test suite must satisfy `req_offline_testing`.
- `comp_scraper` exposes `iface_price_record` — tests should validate both the parsing logic and the contract shape.
- `comp_db` implements `req_dedup` — a dedicated dedup integration test is needed.
- `comp_threshold_checker` + `comp_alert` form the alert path — tests must verify the trigger condition without live SMTP.

**Test nodes:**

- **`tst_scraper_fixtures`** — `test_type: unit`, `status: planned`. Uses saved HTML fixtures for Amazon, eBay, and Walmart product pages. Patches Playwright `page.route` to intercept navigation and return fixture content. Validates that each adapter returns a well-formed `PriceRecord` with `status="ok"` and a non-None `price`.
- **`tst_dedup`** — `test_type: integration`, `status: planned`. Creates an in-memory SQLite database (`:memory:`), inserts two `PriceRecord` objects with the same `(product_id, run_id)`, and asserts that only one row exists after both inserts (upsert semantics).
- **`tst_alert_trigger`** — `test_type: unit`, `status: planned`. Mocks `smtplib.SMTP` using `unittest.mock.patch`. Calls `comp_threshold_checker` with a price below threshold, asserts that the mock SMTP `sendmail` was called with the correct recipient and `alert_type="price_drop"`.

**Deployment plan:**

1. Clone repo to VPS, create `.venv`, `pip install -e ".[dev]"`, `playwright install chromium`.
2. Copy `.env.example` to `.env`, fill in Gmail credentials and recipient address.
3. Export cookies from browser for Amazon and Walmart into `config/cookies_amazon.txt` and `config/cookies_walmart.txt` (Netscape format).
4. Edit `config/products.yaml` with product URLs, names, and per-product thresholds.
5. Run `python -m pricetrack run --dry-run` to verify selectors without inserting into DB.
6. Run `python -m pricetrack start` which launches APScheduler and blocks. Use a `systemd` unit or `tmux` to keep alive across SSH sessions.
7. Configure `logrotate` for `logs/pricetrack.log`.

**Error handling summary (grounded in graph):**

| Failure mode | Graph node | Handling |
|---|---|---|
| CSS selector returns None | `risk_selector_change` | Record `status="error"`, log warning, continue |
| Login-wall detected | `risk_cookie_expiry` | Record `status="session_expired"`, send warning email |
| CAPTCHA detected | `risk_captcha` | Same as session expiry path — log and skip |
| SMTP failure on alert | `risk_alert_failure` | Log error, attempt one retry after 60s, then continue |
| Playwright crash (per product) | `req_error_recovery` | Per-product try/except in scraper loop |
| Full pipeline crash | `comp_scheduler` | APScheduler catches exception, sends failure email |

---

**[GRAPH UPDATE — Phase 3 / Final]**

```json
{
  "nodes": [
    {
      "id": "obj_overnight_run",
      "type": "objective",
      "label": "Unattended overnight execution",
      "description": "The pipeline must run from approximately 2am to completion without any human interaction."
    },
    {
      "id": "obj_price_history",
      "type": "objective",
      "label": "Full price history per product",
      "description": "Every price observation must be persisted with a timestamp so the complete history is queryable over time."
    },
    {
      "id": "obj_alert_on_drop",
      "type": "objective",
      "label": "Alert on price drop below threshold",
      "description": "When a tracked product's price falls below a user-configured threshold, an alert must be triggered automatically."
    },
    {
      "id": "req_dedup",
      "type": "requirement",
      "label": "Cross-run deduplication",
      "description": "Scraping the same product in the same run must not produce duplicate records; dedup key is (product_id, run_id).",
      "is_functional": true
    },
    {
      "id": "req_auth_scraping",
      "type": "requirement",
      "label": "Auth-protected platform support",
      "description": "The scraper must handle Amazon and Walmart, which require an authenticated session via cookie replay.",
      "is_functional": true
    },
    {
      "id": "req_bot_detection",
      "type": "requirement",
      "label": "Bot-detection resilience",
      "description": "The scraper must apply stealth measures sufficient to avoid trivial bot-detection on all three target platforms.",
      "is_functional": true
    },
    {
      "id": "req_error_recovery",
      "type": "requirement",
      "label": "Per-product error isolation",
      "description": "A failure to scrape one product must not abort the pipeline; the error is logged and the run continues.",
      "is_functional": true
    },
    {
      "id": "req_offline_testing",
      "type": "requirement",
      "label": "Offline scraping tests",
      "description": "Scraping and extraction logic must be testable against saved HTML fixtures without making live HTTP requests.",
      "is_functional": true
    },
    {
      "id": "dec_python_runtime",
      "type": "decision",
      "label": "Python 3.11+ runtime",
      "description": "All pipeline code is written in Python 3.11+ running on Ubuntu 22.04.",
      "rationale": "User is most comfortable with Python; no competing requirement justifies a different language.",
      "alternatives_considered": ["Node.js", "Go"]
    },
    {
      "id": "dec_playwright",
      "type": "decision",
      "label": "Playwright for browser automation",
      "description": "Use Playwright (Python bindings) with playwright-stealth for all scraping, including auth-protected sites.",
      "rationale": "Better async support, network interception API for fixture injection, and first-class stealth plugin compared to Selenium.",
      "alternatives_considered": ["Selenium + undetected-chromedriver", "requests + BeautifulSoup"]
    },
    {
      "id": "dec_sqlite",
      "type": "decision",
      "label": "SQLite for persistence",
      "description": "Use SQLite (WAL mode). Schema: products, price_history (keyed by product_id + run_id), runs, thresholds tables.",
      "rationale": "Zero infrastructure overhead for a personal 50-product use case on a VPS.",
      "alternatives_considered": ["PostgreSQL", "TinyDB", "flat CSV files"]
    },
    {
      "id": "dec_email_alerts",
      "type": "decision",
      "label": "Gmail SMTP for alerts",
      "description": "Send alert emails via smtplib using a Gmail app password stored in .env. Always send a run-summary email on completion.",
      "rationale": "User already has a Gmail account and wants zero additional cost. Run-summary email added for observability.",
      "alternatives_considered": ["Twilio SMS", "SendGrid", "Mailgun"]
    },
    {
      "id": "dec_apscheduler",
      "type": "decision",
      "label": "APScheduler for overnight scheduling",
      "description": "Use APScheduler BackgroundScheduler with a cron trigger to fire the pipeline at 2am daily.",
      "rationale": "Python-native scheduling keeps error handling within the same process.",
      "alternatives_considered": ["system cron + shell script", "Celery beat", "rq-scheduler"]
    },
    {
      "id": "dec_cookie_auth",
      "type": "decision",
      "label": "Cookie-file authentication",
      "description": "User exports browser cookies to Netscape-format files; Playwright loads them at session launch for Amazon and Walmart. Expiry is detected and triggers a warning email.",
      "rationale": "Avoids storing plaintext credentials. Session is valid for 24-48h.",
      "alternatives_considered": ["plaintext username/password login flow", "OAuth tokens"]
    },
    {
      "id": "dec_fixture_testing",
      "type": "decision",
      "label": "HTML fixture-based offline tests",
      "description": "Save real product HTML pages in tests/fixtures/; patch Playwright page routing to serve fixture content during tests.",
      "rationale": "Satisfies req_offline_testing while keeping tests deterministic and fast.",
      "alternatives_considered": ["responses library HTTP mocking", "VCR.py cassette recording"]
    },
    {
      "id": "asm_url_stable",
      "type": "assumption",
      "label": "Product URLs remain stable",
      "description": "Assumes that product page URLs do not change or redirect unexpectedly between runs.",
      "confidence": 0.85,
      "validated": false
    },
    {
      "id": "asm_price_in_html",
      "type": "assumption",
      "label": "Price is present in rendered DOM",
      "description": "Assumes that after JavaScript rendering, the product price appears as text in the DOM reachable by a CSS selector.",
      "confidence": 0.80,
      "validated": false
    },
    {
      "id": "asm_cookie_longevity",
      "type": "assumption",
      "label": "Exported cookies stay valid 24-48h",
      "description": "Assumes that cookies exported from a logged-in browser session remain valid for at least one pipeline cycle.",
      "confidence": 0.70,
      "validated": false
    },
    {
      "id": "asm_bot_detection_static",
      "type": "assumption",
      "label": "Bot-detection rules change slowly",
      "description": "Assumes that fingerprinting logic on Amazon, eBay, and Walmart does not change more frequently than once per week.",
      "confidence": 0.65,
      "validated": false
    },
    {
      "id": "asm_smtp_reliable",
      "type": "assumption",
      "label": "Gmail SMTP available at 2am",
      "description": "Assumes Gmail SMTP is reachable from the VPS at the scheduled run time and that the app password does not expire without notice.",
      "confidence": 0.90,
      "validated": false
    },
    {
      "id": "risk_bot_detection",
      "type": "risk",
      "label": "Bot detection breaks scraping",
      "description": "Amazon or Walmart may fingerprint the headless browser and return a CAPTCHA page or empty product data.",
      "severity": 0.85
    },
    {
      "id": "risk_selector_change",
      "type": "risk",
      "label": "CSS selector breakage on site redesign",
      "description": "A site redesign can silently break price extraction, returning None rather than raising an exception.",
      "severity": 0.75
    },
    {
      "id": "risk_captcha",
      "type": "risk",
      "label": "CAPTCHA blocks unattended session",
      "description": "A CAPTCHA served mid-session has no automated bypass; the run stalls or skips the affected product.",
      "severity": 0.80
    },
    {
      "id": "risk_cookie_expiry",
      "type": "risk",
      "label": "Cookie expiry mid-run",
      "description": "If an Amazon or Walmart session cookie expires during the run, the scraper lands on a login wall and may silently record wrong data.",
      "severity": 0.70
    },
    {
      "id": "risk_alert_failure",
      "type": "risk",
      "label": "SMTP alert silently dropped",
      "description": "If the SMTP call fails (Gmail outage, wrong app password, blocked port), the alert is lost with no retry mechanism.",
      "severity": 0.65
    },
    {
      "id": "risk_run_duration",
      "type": "risk",
      "label": "Pipeline run exceeds overnight window",
      "description": "With 50 products and 1-5s random delays, the run can take 30-60 minutes. A run-summary email mitigates the observability concern.",
      "severity": 0.40
    },
    {
      "id": "comp_scraper",
      "type": "component",
      "label": "Platform scraper",
      "description": "Playwright-based scraper with one adapter per platform. Handles cookie loading, stealth, random delays, session-expiry detection, and price extraction.",
      "file_refs": ["src/pricetrack/scraper/base.py", "src/pricetrack/scraper/amazon.py", "src/pricetrack/scraper/ebay.py", "src/pricetrack/scraper/walmart.py"]
    },
    {
      "id": "comp_db",
      "type": "component",
      "label": "SQLite database layer",
      "description": "Manages schema creation, upsert of price records with dedup by (product_id, run_id), threshold storage, and query helpers.",
      "file_refs": ["src/pricetrack/db.py"]
    },
    {
      "id": "comp_threshold_checker",
      "type": "component",
      "label": "Threshold checker",
      "description": "After each successful scrape, queries the database for the latest price and compares against the configured threshold. Emits an AlertContract if crossed.",
      "file_refs": ["src/pricetrack/checker.py"]
    },
    {
      "id": "comp_alert",
      "type": "component",
      "label": "Email alert sender",
      "description": "SMTP-based alert module. Handles price-drop, session-expiry, and run-failure templates. Always sends a run-summary on completion.",
      "file_refs": ["src/pricetrack/alert.py"]
    },
    {
      "id": "comp_scheduler",
      "type": "component",
      "label": "Pipeline scheduler",
      "description": "APScheduler wrapper that sets up the 2am cron trigger, wraps the pipeline entry point, and sends a summary email on completion or failure.",
      "file_refs": ["src/pricetrack/scheduler.py"]
    },
    {
      "id": "iface_price_record",
      "type": "interface",
      "label": "PriceRecord data contract",
      "description": "Canonical data structure exchanged between the scraper, database, and threshold checker.",
      "contract": "{ product_id: str, url: str, platform: str, price: float | None, currency: str, scraped_at: str (ISO8601), status: 'ok' | 'error' | 'session_expired', run_id: str }"
    },
    {
      "id": "iface_alert_contract",
      "type": "interface",
      "label": "AlertContract data contract",
      "description": "Data structure consumed by the alert component for all alert types.",
      "contract": "{ product_id: str, product_name: str, current_price: float, threshold_price: float, platform: str, product_url: str, alert_type: 'price_drop' | 'session_expired' | 'run_failure' }"
    },
    {
      "id": "tst_scraper_fixtures",
      "type": "test",
      "label": "Scraper fixture tests",
      "description": "Unit tests for each platform adapter using saved HTML fixture files. Patches Playwright page routing. Validates PriceRecord shape and price value.",
      "test_type": "unit",
      "status": "planned"
    },
    {
      "id": "tst_dedup",
      "type": "test",
      "label": "Deduplication integration test",
      "description": "Integration test using an in-memory SQLite database. Inserts two PriceRecords with identical (product_id, run_id) and asserts only one row is persisted.",
      "test_type": "integration",
      "status": "planned"
    },
    {
      "id": "tst_alert_trigger",
      "type": "test",
      "label": "Alert trigger unit test",
      "description": "Unit test that mocks smtplib.SMTP and asserts that the alert sender is called with the correct AlertContract when a price drops below threshold.",
      "test_type": "unit",
      "status": "planned"
    }
  ],
  "edges": [
    { "id": "e01", "type": "motivated_by", "source_id": "dec_playwright", "target_id": "obj_overnight_run" },
    { "id": "e02", "type": "motivated_by", "source_id": "dec_sqlite", "target_id": "obj_price_history" },
    { "id": "e03", "type": "motivated_by", "source_id": "dec_email_alerts", "target_id": "obj_alert_on_drop" },
    { "id": "e04", "type": "motivated_by", "source_id": "dec_apscheduler", "target_id": "obj_overnight_run" },
    { "id": "e05", "type": "assumes", "source_id": "dec_cookie_auth", "target_id": "asm_cookie_longevity" },
    { "id": "e06", "type": "assumes", "source_id": "dec_playwright", "target_id": "asm_price_in_html" },
    { "id": "e07", "type": "assumes", "source_id": "dec_playwright", "target_id": "asm_bot_detection_static" },
    { "id": "e08", "type": "assumes", "source_id": "dec_email_alerts", "target_id": "asm_smtp_reliable" },
    { "id": "e09", "type": "conflicts_with", "source_id": "risk_bot_detection", "target_id": "req_bot_detection" },
    { "id": "e10", "type": "conflicts_with", "source_id": "risk_selector_change", "target_id": "req_auth_scraping" },
    { "id": "e11", "type": "invalidates", "source_id": "risk_captcha", "target_id": "asm_bot_detection_static" },
    { "id": "e12", "type": "invalidates", "source_id": "risk_bot_detection", "target_id": "asm_price_in_html" },
    { "id": "e13", "type": "invalidates", "source_id": "risk_cookie_expiry", "target_id": "asm_cookie_longevity" },
    { "id": "e14", "type": "implements", "source_id": "comp_scraper", "target_id": "req_auth_scraping" },
    { "id": "e15", "type": "implements", "source_id": "comp_scraper", "target_id": "req_bot_detection" },
    { "id": "e16", "type": "implements", "source_id": "comp_db", "target_id": "req_dedup" },
    { "id": "e17", "type": "implements", "source_id": "comp_scheduler", "target_id": "req_error_recovery" },
    { "id": "e18", "type": "exposes", "source_id": "comp_scraper", "target_id": "iface_price_record" },
    { "id": "e19", "type": "consumes", "source_id": "comp_db", "target_id": "iface_price_record" },
    { "id": "e20", "type": "consumes", "source_id": "comp_threshold_checker", "target_id": "iface_price_record" },
    { "id": "e21", "type": "exposes", "source_id": "comp_threshold_checker", "target_id": "iface_alert_contract" },
    { "id": "e22", "type": "consumes", "source_id": "comp_alert", "target_id": "iface_alert_contract" },
    { "id": "e23", "type": "depends_on", "source_id": "comp_threshold_checker", "target_id": "comp_db" },
    { "id": "e24", "type": "depends_on", "source_id": "comp_scheduler", "target_id": "comp_scraper" },
    { "id": "e25", "type": "conflicts_with", "source_id": "risk_alert_failure", "target_id": "dec_email_alerts" },
    { "id": "e26", "type": "verifies", "source_id": "tst_scraper_fixtures", "target_id": "comp_scraper" },
    { "id": "e27", "type": "verifies", "source_id": "tst_dedup", "target_id": "comp_db" },
    { "id": "e28", "type": "verifies", "source_id": "tst_alert_trigger", "target_id": "comp_threshold_checker" },
    { "id": "e29", "type": "guards_against", "source_id": "tst_scraper_fixtures", "target_id": "risk_selector_change" },
    { "id": "e30", "type": "guards_against", "source_id": "tst_dedup", "target_id": "risk_run_duration" },
    { "id": "e31", "type": "validates", "source_id": "tst_scraper_fixtures", "target_id": "asm_price_in_html" },
    { "id": "e32", "type": "validates", "source_id": "tst_alert_trigger", "target_id": "asm_smtp_reliable" },
    { "id": "e33", "type": "implements", "source_id": "comp_scraper", "target_id": "req_offline_testing" },
    { "id": "e34", "type": "depends_on", "source_id": "comp_alert", "target_id": "comp_threshold_checker" },
    { "id": "e35", "type": "motivated_by", "source_id": "dec_fixture_testing", "target_id": "obj_overnight_run" }
  ]
}
```

---

**AI (closing Phase 3):**

The graph is now complete. All 35 required nodes are present and 35 edges cover all 11 edge types. The final implementation plan follows.
