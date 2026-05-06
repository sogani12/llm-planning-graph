# Condition A — Conversation (Standard Planning)

---

**User:**

Ask any clarifying questions you need before planning.

Build an automated price tracking and alert system with the following capabilities:
- Scrape product prices from multiple e-commerce platforms, including standard sites and auth-protected platforms (e.g. Amazon, eBay, Walmart). Handle dynamic page loading and bot detection.
- Ingest scraped price data into a persistent database, deduplicating entries across runs and tracking full price history per product.
- Allow users to set price-drop thresholds per product. When a tracked product drops below a user's threshold, trigger an alert (email or SMS).
- Run unattended as an overnight pipeline with full error recovery — no human intervention once started.
- Include a testing harness that validates scraping logic without live site calls.

---

**Assistant:**

Thanks — this is a well-scoped problem. Before I put together the implementation plan I want to nail down a few details so the architecture fits your actual situation rather than a generic one.

1. **Scale and deployment target.** Roughly how many products are you tracking, and across how many users? Are you running this on a home machine, a cloud VM, or something like a Raspberry Pi? The answer affects how aggressive the scraping schedule needs to be and whether a lightweight embedded database is sufficient or if you need a server-side one.

2. **Which platforms matter most, and do you have accounts on them?** Amazon, eBay, and Walmart are all mentioned — are all three required for launch, or is one a "nice to have"? For Amazon in particular, do you have an existing account you're willing to use for session cookies, or do you need fully anonymous scraping?

3. **Alert delivery.** Email and SMS are both listed. Do you have a preferred email provider (Gmail, SendGrid, Mailgun) or SMS gateway (Twilio, AWS SNS) already set up? If budget is a constraint, knowing that helps me avoid recommending paid services when a free tier would do.

4. **Language and tooling preference.** Any strong preference for Python vs. Node.js? Any existing libraries or frameworks you're already comfortable with (Scrapy, Playwright, Selenium, Puppeteer, etc.)?

5. **Testing bar.** When you say "testing harness," are you thinking unit tests with fixture HTML files, a full mock HTTP server, or contract tests that replay captured real responses? And do you need CI integration (GitHub Actions, etc.) or just something runnable locally?

---

**User:**

1. Solo developer, personal use — tracking around 50 products total, no multi-user needs. Running on a VPS with Ubuntu 22.04, 2 vCPU / 4 GB RAM.
2. All three platforms are needed. I have Amazon and eBay accounts I can use for session-based scraping. Walmart I'd prefer to do without logging in if possible.
3. Email only — Gmail SMTP with an app password is fine. No SMS needed.
4. Python all the way. I'm comfortable with Playwright and have used SQLite before.
5. Fixture HTML files are fine for the testing harness. No CI required, just locally runnable pytest tests.

---

**Assistant:**

Perfect — that gives me everything I need. Here is the full implementation plan.

---

# Price Tracker — Implementation Plan

## 1. Overview

This system scrapes product prices from Amazon, eBay, and Walmart on a nightly schedule, stores the full price history in a local SQLite database, and sends Gmail alerts when a tracked product drops below a user-defined threshold. It runs as an unattended overnight pipeline on an Ubuntu 22.04 VPS with automatic error recovery and a pytest-based offline test suite.

The entire stack is Python. Playwright handles dynamic page loading and provides a real browser fingerprint that reduces bot-detection friction. SQLite is the right fit here — 50 products with daily snapshots will stay well under a few megabytes for years, there is no network overhead, and no separate database process to manage. Gmail SMTP with an app password keeps the alert path dependency-free.

---

## 2. Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Language | Python 3.11+ | Type hints throughout |
| Browser automation | Playwright (async) | Chromium, stealth patches via `playwright-stealth` |
| HTTP fallback | `httpx` + `BeautifulSoup4` | For simpler pages that do not require JS |
| Database | SQLite 3 via `aiosqlite` | WAL mode enabled for safe concurrent writes |
| ORM / query layer | Raw SQL with `aiosqlite` | Keeps the schema transparent and easy to inspect |
| Scheduling | `APScheduler` (AsyncIOScheduler) | Cron-style trigger, runs inside the same process |
| Alerting | `smtplib` + `email.mime` (stdlib) | Gmail SMTP, TLS, app password |
| Configuration | `pydantic-settings` + `.env` file | Validated at startup, no silent misconfiguration |
| Testing | `pytest` + `pytest-asyncio` | Fixture HTML files, no live network calls |
| Logging | `structlog` | JSON lines to file + stderr |
| Dependency management | `pip` + `requirements.txt` | Pinned versions |

---

## 3. Repository Layout

```
price-tracker/
├── price_tracker/
│   ├── __init__.py
│   ├── config.py              # Pydantic settings, loaded from .env
│   ├── database.py            # Schema creation, connection pool, all SQL helpers
│   ├── models.py              # Plain dataclasses: Product, PriceRecord, Alert
│   ├── scheduler.py           # APScheduler setup, job registration, main entry point
│   ├── pipeline.py            # Orchestrates a full scrape-ingest-alert cycle
│   ├── alerting.py            # Gmail SMTP alert dispatch
│   │
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base.py            # Abstract BaseScraper, shared Playwright helpers
│   │   ├── amazon.py          # Amazon scraper (session-based, Playwright)
│   │   ├── ebay.py            # eBay scraper (session-based, Playwright)
│   │   └── walmart.py         # Walmart scraper (anonymous, Playwright + httpx fallback)
│   │
│   └── utils/
│       ├── __init__.py
│       ├── stealth.py         # Browser fingerprint helpers, user-agent rotation
│       └── retry.py           # Exponential backoff decorator, circuit-breaker state
│
├── tests/
│   ├── conftest.py            # Shared fixtures: in-memory DB, fake config, HTML loader
│   ├── fixtures/
│   │   ├── amazon_product.html
│   │   ├── ebay_product.html
│   │   └── walmart_product.html
│   ├── test_scrapers.py       # Parser logic tests against fixture HTML
│   ├── test_database.py       # Dedup logic, price history insertion, schema tests
│   ├── test_pipeline.py       # End-to-end pipeline with mocked scrapers
│   └── test_alerting.py       # Alert threshold logic, SMTP mock
│
├── data/
│   └── prices.db              # SQLite database (git-ignored)
│
├── logs/
│   └── tracker.log            # Rotating log file (git-ignored)
│
├── products.yaml              # User-maintained product list with thresholds
├── .env                       # Secrets: Gmail credentials, session cookies (git-ignored)
├── .env.example               # Safe template committed to repo
├── requirements.txt
├── requirements-dev.txt       # pytest, pytest-asyncio, pytest-mock extras
└── run.py                     # Thin entry point: `python run.py` starts the scheduler
```

---

## 4. Configuration

`price_tracker/config.py` uses `pydantic-settings` to read from environment variables (populated from `.env`). All values are validated at import time so the process fails loudly before doing any work if something is missing.

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    db_path: str = "data/prices.db"

    # Gmail
    gmail_sender: str
    gmail_app_password: str
    alert_recipient: str

    # Playwright
    headless: bool = True
    browser_timeout_ms: int = 30_000
    playwright_slow_mo_ms: int = 150

    # Scheduler
    scrape_hour: int = 2       # 2 AM local time
    scrape_minute: int = 0

    # Retry
    max_retries: int = 3
    retry_base_delay_s: float = 5.0

    # Cookies / sessions (JSON strings or file paths)
    amazon_cookies_path: str = ""
    ebay_cookies_path: str = ""
```

`.env.example`:
```
GMAIL_SENDER=you@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
ALERT_RECIPIENT=you@gmail.com
AMAZON_COOKIES_PATH=data/amazon_cookies.json
EBAY_COOKIES_PATH=data/ebay_cookies.json
```

---

## 5. Product List Format

`products.yaml` is the single place the user edits to add, remove, or reprice products. No database UI needed.

```yaml
products:
  - id: amzn-B09G9HD5F7
    name: "Sony WH-1000XM5 Headphones"
    platform: amazon
    url: "https://www.amazon.com/dp/B09G9HD5F7"
    threshold: 279.00

  - id: ebay-387234981234
    name: "Kindle Paperwhite 11th Gen"
    platform: ebay
    url: "https://www.ebay.com/itm/387234981234"
    threshold: 89.99

  - id: wmt-987654321
    name: "Instant Pot Duo 7-in-1"
    platform: walmart
    url: "https://www.walmart.com/ip/987654321"
    threshold: 59.00
```

---

## 6. Database Schema

```sql
CREATE TABLE IF NOT EXISTS products (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    platform    TEXT NOT NULL,
    url         TEXT NOT NULL,
    threshold   REAL NOT NULL,
    active      INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS price_history (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id   TEXT NOT NULL REFERENCES products(id),
    price        REAL NOT NULL,
    currency     TEXT NOT NULL DEFAULT 'USD',
    in_stock     INTEGER NOT NULL DEFAULT 1,
    scraped_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    run_id       TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_price_per_day
    ON price_history (product_id, date(scraped_at));

CREATE TABLE IF NOT EXISTS sent_alerts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id  TEXT NOT NULL REFERENCES products(id),
    price       REAL NOT NULL,
    sent_at     TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    run_id      TEXT NOT NULL
);
```

Deduplication is enforced by `UNIQUE INDEX uq_price_per_day` on `(product_id, date(scraped_at))`. A pipeline restart on the same day will skip already-inserted rows.

---

## 7. Scraper Design

### Base Class

`price_tracker/scrapers/base.py` defines the contract all scrapers implement. The key design decision is separating Playwright navigation from HTML parsing — `_parse_html(html: str)` is a pure function that can be called from tests without a browser.

### Amazon

Session cookies loaded from a JSON file exported by a browser extension. `playwright-stealth` patches are applied on every new page. Price is extracted from `#corePriceDisplay_desktop_feature_div` with fallbacks to `#price_inside_buybox` and `#priceblock_ourprice`.

### eBay

Less aggressive bot detection. Cookie-based session for consistency. Price from `.x-price-primary span[itemprop="price"]` with meta tag fallback. Auction listings (no Buy It Now price) are detected and returned with `price=None, in_stock=False`.

### Walmart

Scraped anonymously. Price data lives in a `<script id="__NEXT_DATA__">` JSON blob embedded in the page — extracting from JSON is more stable than CSS selectors because Walmart's class names are auto-generated.

### Stealth Helpers

`price_tracker/utils/stealth.py` rotates user-agents, randomises viewport dimensions, applies `playwright-stealth`, and injects realistic request headers per navigation.

---

## 8. Pipeline Orchestration

Products are scraped sequentially with a randomised 10–30 second delay between each, keeping the request rate low. A UUID4 `run_id` is assigned at the start of each run and stored with every price record and alert for auditability.

```
run_pipeline()
├── Load products.yaml
├── Sync products table
├── Launch Chromium, load cookies
├── For each product:
│   ├── scrape() with retry (3x, exponential backoff)
│   ├── insert price_history (skip if today's row exists)
│   └── check_and_alert()
├── Close browser
└── If >20% failed: send health warning email
```

---

## 9. Alert Logic

Alerts fire when `current_price <= threshold` AND the price is a new low (lower than the last recorded alert for that product). This prevents nightly re-alerts when a product stays below threshold.

---

## 10. Error Recovery

- **Per-scrape**: retry decorator with exponential backoff (5s → 10s → 20s), 3 attempts
- **Bot detected**: 90s fixed delay before one final retry
- **Pipeline crash**: broad `try/except` at the top level, sends a crash email to alert recipient
- **Process crash**: systemd `Restart=on-failure` brings it back within 60 seconds

---

## 11. Scheduler

APScheduler `AsyncIOScheduler` with a cron trigger at 02:00 UTC. `max_instances=1` prevents overlapping runs. `misfire_grace_time=3600` handles brief VPS downtime.

---

## 12. Testing Harness

All tests use pytest with no live network calls:

- `test_scrapers.py` — loads fixture HTML and calls `_parse_html()` directly
- `test_database.py` — uses an in-memory SQLite DB; tests dedup, insertion, retrieval
- `test_alerting.py` — mocks `smtplib.SMTP_SSL`; tests threshold logic, re-fire prevention, new-low re-alert
- `test_pipeline.py` — mocks the scraper factory; tests full pipeline flow end-to-end

---

## 13. Risks and Limitations

The biggest practical risk is anti-bot evolution — Amazon updates its detection frequently and stealth patches that work today may break in weeks. The session-cookie approach reduces exposure but does not eliminate it.

Cookie expiry is a silent failure mode: expired sessions return login-page HTML, which the parser treats as a `ParseFailureError`. After three consecutive days of failure the pipeline health warning fires, but users should refresh cookies proactively every few months.

Walmart's `__NEXT_DATA__` extraction could silently break if Walmart changes its rendering pipeline. Because parsers are isolated and tested against fixtures, a fix is contained to updating the parser and re-snapshotting the fixture.

At current scale (50 products, daily) SQLite is entirely sufficient. Multi-user or sub-hourly scraping would require a rethink.
