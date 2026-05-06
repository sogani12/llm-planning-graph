# Price Tracker — Implementation Plan (Condition A)

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
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── scheduler.py
│   ├── pipeline.py
│   ├── alerting.py
│   ├── scrapers/
│   │   ├── base.py
│   │   ├── amazon.py
│   │   ├── ebay.py
│   │   └── walmart.py
│   └── utils/
│       ├── stealth.py
│       └── retry.py
├── tests/
│   ├── conftest.py
│   ├── fixtures/
│   │   ├── amazon_product.html
│   │   ├── ebay_product.html
│   │   └── walmart_product.html
│   ├── test_scrapers.py
│   ├── test_database.py
│   ├── test_pipeline.py
│   └── test_alerting.py
├── data/prices.db
├── logs/tracker.log
├── products.yaml
├── .env / .env.example
├── requirements.txt
└── run.py
```

---

## 4. Configuration

`pydantic-settings` reads from `.env`. All fields are validated at startup — the process fails immediately if secrets are missing.

```python
class Settings(BaseSettings):
    db_path: str = "data/prices.db"
    gmail_sender: str
    gmail_app_password: str
    alert_recipient: str
    headless: bool = True
    browser_timeout_ms: int = 30_000
    scrape_hour: int = 2
    scrape_minute: int = 0
    max_retries: int = 3
    retry_base_delay_s: float = 5.0
    amazon_cookies_path: str = ""
    ebay_cookies_path: str = ""
```

---

## 5. Product List Format

`products.yaml` is the single place to add/remove/update products:

```yaml
products:
  - id: amzn-B09G9HD5F7
    name: "Sony WH-1000XM5 Headphones"
    platform: amazon
    url: "https://www.amazon.com/dp/B09G9HD5F7"
    threshold: 279.00
```

---

## 6. Database Schema

```sql
CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, platform TEXT NOT NULL,
    url TEXT NOT NULL, threshold REAL NOT NULL, active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT NOT NULL REFERENCES products(id),
    price REAL NOT NULL, currency TEXT DEFAULT 'USD',
    in_stock INTEGER DEFAULT 1,
    scraped_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    run_id TEXT NOT NULL
);

-- Deduplication: one price row per product per calendar day
CREATE UNIQUE INDEX IF NOT EXISTS uq_price_per_day
    ON price_history (product_id, date(scraped_at));

CREATE TABLE IF NOT EXISTS sent_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT NOT NULL REFERENCES products(id),
    price REAL NOT NULL,
    sent_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    run_id TEXT NOT NULL
);
```

---

## 7. Scraper Design

All scrapers extend `BaseScraper`. The critical design constraint is separating Playwright navigation from HTML parsing so that `parse_html(html: str)` can be called directly in tests without a live browser.

**Amazon**: Cookie-based session (JSON file from browser extension). CSS selectors for `#corePriceDisplay_desktop_feature_div` with fallbacks. `playwright-stealth` + randomised delays + UA rotation.

**eBay**: Cookie session for consistency. `.x-price-primary span[itemprop="price"]` selector. Auction listings (no Buy It Now) returned as `price=None`.

**Walmart**: Anonymous. Extracts price from `<script id="__NEXT_DATA__">` JSON blob — more stable than CSS class selectors which are auto-generated.

---

## 8. Pipeline

Sequential scraping with 10–30s delays between products. UUID4 `run_id` stored with every record.

```
run_pipeline()
├── Load products.yaml → sync DB
├── Launch Chromium, load cookies
├── For each product: scrape → insert (skip if today exists) → check_and_alert
├── Close browser
└── If >20% failed: send health warning email
```

---

## 9. Alert Logic

Alert fires when `current_price <= threshold` AND it is a new all-time low for that product (lower than the last alert). Prevents nightly re-alerts when the price stays below threshold.

---

## 10. Error Recovery

- **Per-scrape**: 3 retries, exponential backoff (5s → 10s → 20s)
- **Bot detected**: 90s wait before one final retry
- **Pipeline crash**: top-level `try/except` sends crash email
- **Process crash**: systemd `Restart=on-failure`, `RestartSec=60`

---

## 11. Scheduler

APScheduler `AsyncIOScheduler`, cron at 02:00 UTC. `max_instances=1` prevents overlapping runs.

---

## 12. Testing Harness

No live network calls in any test.

- `test_scrapers.py` — loads fixture HTML, calls `parse_html()` directly, asserts price/in_stock
- `test_database.py` — in-memory SQLite, tests dedup (`uq_price_per_day` constraint), insertion
- `test_alerting.py` — mocks `smtplib.SMTP_SSL`, tests threshold logic and re-fire prevention
- `test_pipeline.py` — mocks scraper factory, runs full pipeline end-to-end

```bash
pytest tests/ -v --asyncio-mode=auto
```

---

## 13. Deployment (Ubuntu 22.04)

```bash
sudo useradd -m tracker
sudo -u tracker git clone <repo> /home/tracker/price-tracker
cd /home/tracker/price-tracker && sudo -u tracker python3.11 -m venv .venv
sudo -u tracker .venv/bin/pip install -r requirements.txt
sudo -u tracker .venv/bin/playwright install chromium
# Populate .env and export cookies to data/amazon_cookies.json, data/ebay_cookies.json
sudo cp deploy/price-tracker.service /etc/systemd/system/
sudo systemctl enable --now price-tracker
```

---

## 14. Risks and Limitations

The biggest practical risk is anti-bot evolution — Amazon updates its detection frequently and stealth patches that work today may break in weeks. Cookie expiry is a silent failure mode: expired sessions return login-page HTML, which appears as `ParseFailureError`. After three consecutive daily failures the pipeline health warning fires. Users should refresh cookies proactively every few months.

Walmart's `__NEXT_DATA__` parsing could silently break if Walmart changes its rendering pipeline. Because parsers are isolated and tested against fixtures, a fix is contained to updating `parse_html()` and re-snapshotting the fixture file.

At current scale (50 products, daily) SQLite is sufficient. Multi-user or sub-hourly scraping would require a rethink of the storage and concurrency model.
