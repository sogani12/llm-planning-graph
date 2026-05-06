# Automated Price Tracking and Alert System

## Technology Stack

- **Runtime**: Python 3.11+ on Ubuntu 22.04 VPS
- **Browser automation**: Playwright (Python bindings) + playwright-stealth
- **Database**: SQLite with WAL mode (stdlib `sqlite3`, wrapped in a custom helper)
- **Scheduling**: APScheduler (`BackgroundScheduler` with cron trigger)
- **Alerting**: `smtplib` via Gmail SMTP, app password from `.env`
- **Auth**: Netscape-format cookie files loaded into Playwright at session start
- **Config**: YAML (`products.yaml`, `settings.yaml`) + `.env` for secrets
- **Testing**: pytest + saved HTML fixtures + `unittest.mock` for SMTP
- **Packaging**: `pyproject.toml` (hatchling), systemd unit for deployment

---

## Pipeline Data Flow

```
products.yaml
     |
     v
[comp_scheduler] -- APScheduler cron @ 2am
     |
     v
[comp_scraper] -- Playwright + stealth + cookie files
     |  (per product, in sequence, with random 1-5s delay)
     |  emits --> PriceRecord (iface_price_record)
     |
     +----> [comp_db] -- SQLite upsert (dedup by product_id + run_id)
     |
     +----> [comp_threshold_checker] -- compare price vs threshold
                 |
                 | if price < threshold
                 v
           [comp_alert] -- smtplib Gmail SMTP
                 |
                 v
           User inbox (price_drop | session_expired | run_failure | summary)
```

Each component is an independent Python module. The scheduler owns the top-level pipeline loop. All inter-component data exchange uses typed dataclasses (`PriceRecord`, `AlertContract`) that correspond to the graph's interface nodes (`iface_price_record`, `iface_alert_contract`).

---

## Project Structure

```
pricetrack/
  pyproject.toml
  .env.example
  README.md
  config/
    products.yaml            # product list with URLs, names, thresholds
    settings.yaml            # run schedule, email recipient, delay range
    cookies_amazon.txt       # Netscape cookie export (gitignored)
    cookies_walmart.txt      # Netscape cookie export (gitignored)
  src/pricetrack/
    __init__.py
    __main__.py              # CLI entry: run, start, dry-run subcommands
    pipeline.py              # top-level pipeline loop
    scheduler.py             # APScheduler wrapper (comp_scheduler)
    checker.py               # threshold comparison logic (comp_threshold_checker)
    alert.py                 # SMTP alert sender (comp_alert)
    db.py                    # SQLite wrapper (comp_db)
    models.py                # PriceRecord, AlertContract dataclasses
    scraper/
      __init__.py
      base.py                # BaseScraper ABC
      amazon.py              # AmazonScraper
      ebay.py                # EbayScraper
      walmart.py             # WalmartScraper
      stealth.py             # Playwright browser factory with stealth config
    utils/
      __init__.py
      logging.py             # structured JSON logging to file + stderr
      retry.py               # simple retry decorator with exponential backoff
  tests/
    conftest.py              # shared fixtures: in-memory DB, mock SMTP
    fixtures/
      amazon_product.html    # snapshot of a real Amazon product page
      ebay_product.html      # snapshot of a real eBay item page
      walmart_product.html   # snapshot of a real Walmart product page
      amazon_login_wall.html # snapshot of Amazon login redirect page
    test_scraper.py          # tst_scraper_fixtures: adapter parsing tests
    test_db.py               # tst_dedup: deduplication and upsert tests
    test_alert.py            # tst_alert_trigger: SMTP mock + threshold tests
  logs/                      # gitignored, created at runtime
    pricetrack.log
  data/
    prices.db                # SQLite database (gitignored)
```

---

## Architecture Decisions (with Rationale)

### dec_python_runtime — Python 3.11+ on Ubuntu 22.04

**Chosen**: Python 3.11+
**Alternatives considered**: Node.js, Go
**Rationale**: The user has strong Python familiarity and no requirement justifies introducing another language. Python 3.11 adds significant performance improvements over 3.10 and has stable Playwright bindings. The VPS runs Ubuntu 22.04; Python 3.11+ is installed via the `deadsnakes/ppa` repository or `pyenv`.

---

### dec_playwright — Playwright for browser automation

**Chosen**: Playwright (Python) + playwright-stealth
**Alternatives considered**: Selenium + undetected-chromedriver, requests + BeautifulSoup
**Rationale**: Playwright's Python API has first-class support for `page.route()`, which enables intercepting network requests and returning saved fixture content — essential for satisfying `req_offline_testing`. playwright-stealth patches the standard browser fingerprinting vectors (navigator.webdriver, canvas fingerprint, WebGL renderer string) with a single import. Requests + BS4 cannot execute JavaScript, ruling it out for Amazon and Walmart, which both render prices dynamically. Selenium's route-interception equivalent requires more boilerplate and undetected-chromedriver has a slower patch cadence against evolving bot detection.

---

### dec_sqlite — SQLite for persistence

**Chosen**: SQLite with WAL mode
**Alternatives considered**: PostgreSQL, TinyDB, flat CSV files
**Rationale**: 50 products tracked nightly produces approximately 18,250 rows per year — well within SQLite's practical limits. WAL mode allows concurrent reads from external tools (e.g. DB Browser for SQLite) without blocking the pipeline's writes. Zero infrastructure cost: no daemon, no network port, no connection string to manage. The schema is simple enough (4 tables) that an ORM adds unnecessary complexity.

**Schema**:
```sql
CREATE TABLE products (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    platform TEXT NOT NULL
);

CREATE TABLE runs (
    run_id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL DEFAULT 'running'
);

CREATE TABLE price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    price REAL,
    currency TEXT NOT NULL DEFAULT 'USD',
    scraped_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('ok', 'error', 'session_expired')),
    UNIQUE(product_id, run_id),
    FOREIGN KEY(product_id) REFERENCES products(id),
    FOREIGN KEY(run_id) REFERENCES runs(run_id)
);

CREATE TABLE thresholds (
    product_id TEXT PRIMARY KEY,
    threshold_price REAL NOT NULL,
    alert_sent_at TEXT,
    FOREIGN KEY(product_id) REFERENCES products(id)
);
```

The `UNIQUE(product_id, run_id)` constraint, combined with `INSERT OR REPLACE` semantics, implements `req_dedup`: a second scrape of the same product within the same run overwrites rather than duplicates the record.

---

### dec_email_alerts — Gmail SMTP for alerts

**Chosen**: smtplib + Gmail app password
**Alternatives considered**: Twilio SMS, SendGrid, Mailgun
**Rationale**: The user explicitly rejected paid APIs. Gmail SMTP with an app password is free, requires no additional account, and is reliable enough for overnight personal use (`asm_smtp_reliable` confidence: 0.90). The app password is stored in `.env` and never committed to source control. Per the user's request in Phase 3, the system always sends a run-summary email even on success, providing nightly confirmation that the pipeline ran.

---

### dec_apscheduler — APScheduler for overnight scheduling

**Chosen**: APScheduler `BackgroundScheduler` with a cron trigger at 02:00
**Alternatives considered**: system cron + shell script, Celery beat, rq-scheduler
**Rationale**: APScheduler runs in-process, so Python exceptions from the pipeline are caught within the same process context and can trigger a failure email before the process exits. A shell-script cron job would require a separate Python invocation, losing the in-process exception context. Celery beat and rq-scheduler require a Redis or RabbitMQ broker — unnecessary complexity for a single-machine, single-user system.

`misfire_grace_time=3600` is set: if the VPS is briefly offline at 2am, APScheduler fires the job as soon as the machine comes back online within the next hour.

---

### dec_cookie_auth — Cookie-file authentication

**Chosen**: Netscape-format cookie files loaded into Playwright browser context
**Alternatives considered**: Plaintext username/password login flow, OAuth tokens, no auth (public pages only)
**Rationale**: Storing credentials in `.env` and automating a login form is fragile — Amazon's login page frequently adds CAPTCHA, 2FA prompts, and changes form selectors. Cookie replay avoids re-authentication entirely: the user exports cookies once per week using the Cookie-Editor browser extension and the pipeline treats the exported session as pre-authenticated. Cookie expiry is detected by checking for login-wall DOM indicators before price extraction; a warning email is sent rather than silently recording wrong data.

---

### dec_fixture_testing — HTML fixture-based offline tests

**Chosen**: Saved `.html` fixture files + Playwright `page.route()` interception
**Alternatives considered**: `responses` library HTTP mocking, VCR.py cassette recording
**Rationale**: Playwright's `page.route()` can intercept any URL pattern and return a static response with a local HTML body. This exercises the complete scraper code path (browser launch, navigation, DOM query) without any live network call, satisfying `req_offline_testing`. VCR.py records and replays full HTTP sessions — useful for REST APIs but adds overhead for browser-rendered pages. The `responses` library patches `urllib3`, which Playwright does not use (it communicates via the Chrome DevTools Protocol), making it ineffective here.

---

## Key Assumptions

| ID | Label | Confidence | Status | Notes |
|----|-------|-----------|--------|-------|
| `asm_url_stable` | Product URLs remain stable | 0.85 | unvalidated | Amazon ASIN and Walmart item URLs are stable; eBay item IDs can change on relisted items |
| `asm_price_in_html` | Price is present in rendered DOM | 0.80 | unvalidated | May fail on out-of-stock, third-party-only, or region-locked listings |
| `asm_cookie_longevity` | Exported cookies stay valid 24-48h | 0.70 | unvalidated | Amazon sessions are particularly short-lived; weekly re-export recommended |
| `asm_bot_detection_static` | Bot-detection rules change slowly | 0.65 | unvalidated | Lowest-confidence assumption; Amazon's fingerprinting is actively maintained |
| `asm_smtp_reliable` | Gmail SMTP available at 2am | 0.90 | unvalidated | High uptime in practice; VPS outbound port 587 must be unblocked by the hosting provider |

**Action on assumption failure**:

- `asm_price_in_html` fails → `status="error"` recorded; logged at WARNING level; listed in run summary
- `asm_cookie_longevity` fails → `status="session_expired"` recorded; warning email sent immediately
- `asm_smtp_reliable` fails → logged at ERROR level; retry once after 60 seconds; run continues

---

## Risk Register

| ID | Label | Severity | Mitigation |
|----|-------|---------|-----------|
| `risk_bot_detection` | Bot detection breaks scraping | 0.85 | playwright-stealth plugin; random 1-5s delays; realistic user-agent; no proxy |
| `risk_captcha` | CAPTCHA blocks unattended session | 0.80 | Detect CAPTCHA DOM indicators; treat as session expiry; send warning email; skip product |
| `risk_selector_change` | CSS selector breakage on site redesign | 0.75 | Per-product try/except; `status="error"` recorded; run-summary lists failures |
| `risk_cookie_expiry` | Cookie expiry mid-run | 0.70 | Login-wall detection before price extraction; warning email sent; user re-exports cookies |
| `risk_alert_failure` | SMTP alert silently dropped | 0.65 | Single retry after 60s; error logged; run-summary attempted as final SMTP call |
| `risk_run_duration` | Pipeline run exceeds overnight window | 0.40 | Run-summary email confirms finish time; delays bounded at 5s max; browser reused per platform |

---

## Implementation Plan

### Phase 1 — Foundation (Days 1-2)

**1.1 Project scaffolding**

```bash
mkdir pricetrack && cd pricetrack
python3.11 -m venv .venv && source .venv/bin/activate
pip install playwright playwright-stealth apscheduler pydantic python-dotenv pyyaml pytest pytest-asyncio
playwright install chromium
playwright install-deps chromium
```

`pyproject.toml`:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "pricetrack"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "playwright>=1.44",
    "playwright-stealth>=1.0",
    "apscheduler>=3.10",
    "pydantic>=2.0",
    "python-dotenv>=1.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-asyncio>=0.23"]

[project.scripts]
pricetrack = "pricetrack.__main__:main"
```

**1.2 Data models (`models.py`)**

```python
from dataclasses import dataclass
from typing import Literal

@dataclass
class PriceRecord:
    product_id: str
    url: str
    platform: str
    price: float | None
    currency: str
    scraped_at: str          # ISO 8601
    status: Literal["ok", "error", "session_expired"]
    run_id: str

@dataclass
class AlertContract:
    product_id: str
    product_name: str
    current_price: float
    threshold_price: float
    platform: str
    product_url: str
    alert_type: Literal["price_drop", "session_expired", "run_failure"]
```

These dataclasses directly implement `iface_price_record` and `iface_alert_contract` from the planning graph.

**1.3 Database layer (`db.py`)**

Key public functions:
- `init_db(path: str) -> sqlite3.Connection` — create tables if not exist; enable WAL with `PRAGMA journal_mode=WAL`
- `upsert_price(conn, record: PriceRecord) -> None` — `INSERT OR REPLACE INTO price_history`
- `get_latest_price(conn, product_id: str) -> float | None`
- `get_threshold(conn, product_id: str) -> float | None`
- `create_run(conn, run_id: str) -> None`
- `finish_run(conn, run_id: str, status: str) -> None`

The `UNIQUE(product_id, run_id)` constraint and `INSERT OR REPLACE` together enforce `req_dedup` at the database level, independent of application logic.

---

### Phase 2 — Scraper (Days 3-5)

**2.1 Stealth browser factory (`scraper/stealth.py`)**

Creates a Playwright browser context with:
- `headless=True`
- Realistic `user_agent` string (current Chrome on Windows)
- `viewport` set to `1280x800`
- `locale="en-US"`, `timezone_id="America/New_York"`
- playwright-stealth applied via `await stealth_async(page)`
- Cookies loaded from Netscape file if `cookies_path` is provided

**2.2 Base scraper (`scraper/base.py`)**

```python
import abc, asyncio, random
from ..models import PriceRecord

class BaseScraper(abc.ABC):
    PLATFORM: str = ""
    LOGIN_WALL_SELECTORS: list[str] = []
    PRICE_SELECTORS: list[str] = []

    async def scrape(self, product_id: str, url: str, run_id: str) -> PriceRecord:
        await asyncio.sleep(random.uniform(1.0, 5.0))
        await self._page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        if await self._is_login_wall():
            return PriceRecord(
                product_id=product_id, url=url, platform=self.PLATFORM,
                price=None, currency="USD",
                scraped_at=datetime.utcnow().isoformat() + "Z",
                status="session_expired", run_id=run_id
            )
        price = await self._extract_price()
        status = "ok" if price is not None else "error"
        return PriceRecord(
            product_id=product_id, url=url, platform=self.PLATFORM,
            price=price, currency="USD",
            scraped_at=datetime.utcnow().isoformat() + "Z",
            status=status, run_id=run_id
        )

    async def _is_login_wall(self) -> bool:
        for selector in self.LOGIN_WALL_SELECTORS:
            if await self._page.query_selector(selector):
                return True
        return False

    async def _extract_price(self) -> float | None:
        for selector in self.PRICE_SELECTORS:
            el = await self._page.query_selector(selector)
            if el:
                text = await el.inner_text()
                return _parse_price(text)
        return None
```

**2.3 Platform adapters**

**Amazon** (`scraper/amazon.py`):
- `LOGIN_WALL_SELECTORS`: `["#ap_email", "#captchacharacters", "[data-cel-widget='CAPTCHA']"]`
- `PRICE_SELECTORS`: `[".a-price .a-offscreen", "#priceblock_ourprice", "#priceblock_dealprice", ".reinventPricePriceToPayMargin .a-price"]`
- Cookies loaded from `cookies_amazon.txt`

**eBay** (`scraper/ebay.py`):
- No cookie auth (eBay prices are publicly accessible)
- `PRICE_SELECTORS`: `[".x-price-primary .ux-textspans", "#prcIsum", ".x-bin-price__content .ux-textspans"]`

**Walmart** (`scraper/walmart.py`):
- `LOGIN_WALL_SELECTORS`: `["#sign-in-modal", "[data-testid='signin-modal']", "[data-automation='login-modal']"]`
- `PRICE_SELECTORS`: `["[itemprop='price']", "[data-automation='buybox-price']", ".price-characteristic"]`
- Cookies loaded from `cookies_walmart.txt`

---

### Phase 3 — Alert System (Day 6)

**3.1 Threshold checker (`checker.py`)**

```python
def check_threshold(
    conn: sqlite3.Connection,
    record: PriceRecord,
    products_config: dict
) -> AlertContract | None:
    if record.status != "ok" or record.price is None:
        return None
    threshold = get_threshold(conn, record.product_id)
    if threshold is None:
        return None
    if record.price < threshold:
        return AlertContract(
            product_id=record.product_id,
            product_name=products_config[record.product_id]["name"],
            current_price=record.price,
            threshold_price=threshold,
            platform=record.platform,
            product_url=record.url,
            alert_type="price_drop",
        )
    return None
```

`comp_threshold_checker` depends on `comp_db` (graph edge `e23: depends_on`) and exposes `iface_alert_contract` (edge `e21: exposes`).

**3.2 Email alert sender (`alert.py`)**

Four email templates, all sent via `smtplib.SMTP` over port 587 with STARTTLS:

1. **price_drop** — Subject: `[PriceTrack] Price drop: {name} now ${price:.2f}`. Body: product name, current price, threshold, platform, direct URL.
2. **session_expired** — Subject: `[PriceTrack] Warning: {platform} session expired`. Body: instructions to re-export cookies, file path.
3. **run_failure** — Subject: `[PriceTrack] Pipeline run FAILED`. Body: exception message and traceback.
4. **run_summary** — Always sent at end of run. Lists: run duration, product count, successes, errors, session-expiry events, and any price drops triggered.

Retry logic: if the SMTP call raises `smtplib.SMTPException`, wait 60 seconds and retry once. If the retry also fails, log at ERROR level and continue. The run-summary is the last SMTP call made; if it fails, only the log file records the outcome.

---

### Phase 4 — Scheduler and Pipeline Loop (Day 7)

**4.1 Pipeline loop (`pipeline.py`)**

The pipeline:
1. Generates a UUID `run_id` and records it in `runs` table
2. Iterates over `config["products"]` in order
3. For each product, catches all exceptions per-product (satisfying `req_error_recovery`)
4. Calls the appropriate scraper adapter
5. Upserts the `PriceRecord` into `price_history`
6. If `status == "session_expired"`, fires a warning alert immediately
7. If `status == "ok"`, calls `check_threshold()` and fires a price-drop alert if triggered
8. After all products, marks the run as complete and sends the run-summary email

**4.2 Scheduler (`scheduler.py`)**

```python
from apscheduler.schedulers.blocking import BlockingScheduler
import asyncio, logging

logger = logging.getLogger(__name__)

def start_scheduler(config: dict) -> None:
    scheduler = BlockingScheduler()
    scheduler.add_job(
        _run_job,
        trigger="cron",
        hour=config.get("schedule_hour", 2),
        minute=config.get("schedule_minute", 0),
        args=[config],
        misfire_grace_time=3600,
        max_instances=1,
    )
    logger.info("Scheduler started. Pipeline fires daily at %02d:%02d.",
                config.get("schedule_hour", 2), config.get("schedule_minute", 0))
    scheduler.start()

def _run_job(config: dict) -> None:
    try:
        summary = asyncio.run(run_pipeline(config, config["db_path"]))
        send_run_summary(summary, config["smtp"])
    except Exception as exc:
        logger.critical("Pipeline top-level crash: %s", exc, exc_info=True)
        send_failure_alert(str(exc), config["smtp"])
```

`max_instances=1` prevents a second run from starting if the first is still running (guards against `risk_run_duration` overlap).

---

### Phase 5 — Configuration (Day 8)

**`config/products.yaml`** (example):
```yaml
products:
  - id: "amz_headphones_001"
    name: "Sony WH-1000XM5 Headphones"
    url: "https://www.amazon.com/dp/B09XS7JWHH"
    platform: "amazon"
    threshold: 279.99

  - id: "ebay_watch_042"
    name: "Casio G-Shock GA-2100"
    url: "https://www.ebay.com/itm/123456789012"
    platform: "ebay"
    threshold: 85.00

  - id: "wmt_coffee_007"
    name: "Keurig K-Mini Coffee Maker"
    url: "https://www.walmart.com/ip/Keurig-K-Mini/123456789"
    platform: "walmart"
    threshold: 59.99
```

**`config/settings.yaml`**:
```yaml
schedule_hour: 2
schedule_minute: 0
delay_min_seconds: 1.0
delay_max_seconds: 5.0
db_path: "data/prices.db"
log_path: "logs/pricetrack.log"
```

**`.env.example`**:
```
GMAIL_USER=youraddress@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
GMAIL_RECIPIENT=youraddress@gmail.com
DB_PATH=/opt/pricetrack/data/prices.db
COOKIES_AMAZON=/opt/pricetrack/config/cookies_amazon.txt
COOKIES_WALMART=/opt/pricetrack/config/cookies_walmart.txt
```

---

### Phase 6 — Deployment (Day 9)

**6.1 VPS setup**

```bash
# Install Python 3.11
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update && sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Clone and install
git clone https://github.com/yourname/pricetrack.git /opt/pricetrack
cd /opt/pricetrack
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
playwright install chromium
playwright install-deps chromium

# Configure secrets
cp .env.example .env
nano .env   # fill in Gmail credentials and DB path
```

**6.2 Cookie export workflow**

1. Install Cookie-Editor extension (Chrome Web Store or Firefox Add-ons)
2. Log in to Amazon and Walmart in your browser
3. Open Cookie-Editor → Export → Netscape HTTP Cookie File format
4. Save the output as `cookies_amazon.txt` and `cookies_walmart.txt`
5. Copy to the VPS: `scp cookies_amazon.txt user@vps:/opt/pricetrack/config/`
6. Repeat weekly (calendar reminder recommended; `asm_cookie_longevity` confidence 0.70)

**6.3 Validation before enabling the scheduler**

```bash
# Verify one product extracts correctly (no DB write)
python -m pricetrack run --dry-run --product-id amz_headphones_001

# Run full pipeline once, inspect logs
python -m pricetrack run
tail -50 logs/pricetrack.log

# Send a test email to verify SMTP config
python -m pricetrack test-email
```

**6.4 systemd unit**

`/etc/systemd/system/pricetrack.service`:
```ini
[Unit]
Description=Price Tracking Pipeline (APScheduler)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/pricetrack
ExecStart=/opt/pricetrack/.venv/bin/python -m pricetrack start
Restart=on-failure
RestartSec=60
EnvironmentFile=/opt/pricetrack/.env
StandardOutput=append:/opt/pricetrack/logs/pricetrack.log
StandardError=append:/opt/pricetrack/logs/pricetrack.log

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable pricetrack
sudo systemctl start pricetrack
sudo systemctl status pricetrack
```

**6.5 Log rotation** (`/etc/logrotate.d/pricetrack`):
```
/opt/pricetrack/logs/*.log {
    daily
    rotate 30
    compress
    missingok
    notifempty
    postrotate
        systemctl kill -s USR1 pricetrack.service 2>/dev/null || true
    endscript
}
```

---

## Testing Strategy

The testing strategy is grounded in three graph test nodes (`tst_scraper_fixtures`, `tst_dedup`, `tst_alert_trigger`) and one decision node (`dec_fixture_testing`). All tests run without network access.

### tst_scraper_fixtures — Scraper fixture unit tests

**File**: `tests/test_scraper.py`
**Type**: unit
**Satisfies**: `req_offline_testing`
**Guards against**: `risk_selector_change`
**Validates**: `asm_price_in_html`

**Approach**: Use Playwright's `page.route("**/*", ...)` to intercept every navigation request and return the content of a saved HTML fixture file. The scraper adapter runs its full code path (page navigation, DOM query, price parsing) without any live network call.

**`tests/conftest.py`** (shared fixtures):
```python
import pytest
from pathlib import Path

FIXTURE_DIR = Path(__file__).parent / "fixtures"

@pytest.fixture
def amazon_html():
    return (FIXTURE_DIR / "amazon_product.html").read_text()

@pytest.fixture
def amazon_login_wall_html():
    return (FIXTURE_DIR / "amazon_login_wall.html").read_text()

@pytest.fixture
def ebay_html():
    return (FIXTURE_DIR / "ebay_product.html").read_text()

@pytest.fixture
def walmart_html():
    return (FIXTURE_DIR / "walmart_product.html").read_text()
```

**`tests/test_scraper.py`**:
```python
import pytest
from playwright.async_api import async_playwright
from pricetrack.scraper.amazon import AmazonScraper
from pricetrack.scraper.ebay import EbayScraper
from pricetrack.scraper.walmart import WalmartScraper

@pytest.mark.asyncio
async def test_amazon_extracts_price(amazon_html):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.route("**/*", lambda r: r.fulfill(
            body=amazon_html, content_type="text/html"
        ))
        scraper = AmazonScraper(page=page, cookies_path=None)
        record = await scraper.scrape("test_001", "https://www.amazon.com/dp/B09XS7JWHH", "run_001")
    assert record.status == "ok"
    assert record.price is not None and record.price > 0
    assert record.currency == "USD"
    assert record.product_id == "test_001"

@pytest.mark.asyncio
async def test_amazon_detects_login_wall(amazon_login_wall_html):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.route("**/*", lambda r: r.fulfill(
            body=amazon_login_wall_html, content_type="text/html"
        ))
        scraper = AmazonScraper(page=page, cookies_path=None)
        record = await scraper.scrape("test_001", "https://www.amazon.com/dp/B09XS7JWHH", "run_001")
    assert record.status == "session_expired"
    assert record.price is None

@pytest.mark.asyncio
async def test_ebay_extracts_price(ebay_html):
    # ... analogous to Amazon test
    assert record.status == "ok"
    assert record.price is not None

@pytest.mark.asyncio
async def test_walmart_extracts_price(walmart_html):
    # ... analogous to Amazon test
    assert record.status == "ok"
    assert record.price is not None
```

**Fixture capture**: Run `python -m pricetrack capture-fixture --product-id amz_headphones_001` to save the current rendered DOM to `tests/fixtures/amazon_product.html`. This command navigates with the real browser, saves `page.content()`, and exits without scraping.

---

### tst_dedup — Deduplication integration test

**File**: `tests/test_db.py`
**Type**: integration
**Implements**: `req_dedup`

**Approach**: Use SQLite in-memory mode (`:memory:`) to create the real schema and run real upsert operations without touching the filesystem.

```python
import pytest
from pricetrack.db import init_db, upsert_price
from pricetrack.models import PriceRecord

@pytest.fixture
def mem_db():
    conn = init_db(":memory:")
    conn.execute("INSERT INTO products VALUES ('p1', 'Test Product', 'http://example.com', 'amazon')")
    conn.execute("INSERT INTO runs VALUES ('run_001', '2025-05-03T02:00:00Z', NULL, 'running')")
    conn.commit()
    return conn

def _make_record(run_id="run_001", price=99.99):
    return PriceRecord(
        product_id="p1", url="http://example.com", platform="amazon",
        price=price, currency="USD",
        scraped_at="2025-05-03T02:05:00Z",
        status="ok", run_id=run_id
    )

def test_duplicate_in_same_run_produces_one_row(mem_db):
    upsert_price(mem_db, _make_record())
    upsert_price(mem_db, _make_record())  # same (product_id, run_id)
    cur = mem_db.execute("SELECT COUNT(*) FROM price_history WHERE product_id='p1'")
    assert cur.fetchone()[0] == 1

def test_different_runs_produce_separate_rows(mem_db):
    mem_db.execute("INSERT INTO runs VALUES ('run_002', '2025-05-04T02:00:00Z', NULL, 'running')")
    mem_db.commit()
    upsert_price(mem_db, _make_record(run_id="run_001", price=99.99))
    upsert_price(mem_db, _make_record(run_id="run_002", price=95.00))
    cur = mem_db.execute("SELECT COUNT(*) FROM price_history WHERE product_id='p1'")
    assert cur.fetchone()[0] == 2

def test_upsert_overwrites_price_in_same_run(mem_db):
    upsert_price(mem_db, _make_record(price=99.99))
    upsert_price(mem_db, _make_record(price=89.99))  # same run, different price
    cur = mem_db.execute("SELECT price FROM price_history WHERE product_id='p1'")
    assert cur.fetchone()[0] == 89.99
```

---

### tst_alert_trigger — Alert trigger unit test

**File**: `tests/test_alert.py`
**Type**: unit
**Validates**: `asm_smtp_reliable`

**Approach**: Mock `smtplib.SMTP` using `unittest.mock.patch`. Verify that `check_threshold()` returns the correct `AlertContract` and that `send_alert()` invokes `sendmail` with the correct recipient.

```python
import pytest
from unittest.mock import patch, MagicMock
from pricetrack.db import init_db, upsert_price
from pricetrack.checker import check_threshold
from pricetrack.alert import send_alert
from pricetrack.models import PriceRecord

TEST_SMTP_CONFIG = {
    "user": "test@gmail.com",
    "app_password": "test-password",
    "from": "test@gmail.com",
    "to": "user@example.com",
}

@pytest.fixture
def mem_db_with_threshold():
    conn = init_db(":memory:")
    conn.execute("INSERT INTO products VALUES ('p1', 'Test Product', 'http://x.com', 'amazon')")
    conn.execute("INSERT INTO thresholds VALUES ('p1', 100.00, NULL)")
    conn.commit()
    return conn

def _price_record(price: float) -> PriceRecord:
    return PriceRecord(
        product_id="p1", url="http://x.com", platform="amazon",
        price=price, currency="USD",
        scraped_at="2025-05-03T02:05:00Z", status="ok", run_id="run_001"
    )

def test_price_below_threshold_returns_contract(mem_db_with_threshold):
    record = _price_record(89.99)
    contract = check_threshold(mem_db_with_threshold, record, {"p1": {"name": "Test Product"}})
    assert contract is not None
    assert contract.alert_type == "price_drop"
    assert contract.current_price == 89.99
    assert contract.threshold_price == 100.00

def test_price_above_threshold_returns_none(mem_db_with_threshold):
    record = _price_record(120.00)
    contract = check_threshold(mem_db_with_threshold, record, {"p1": {"name": "Test Product"}})
    assert contract is None

def test_send_alert_calls_smtp(mem_db_with_threshold):
    record = _price_record(89.99)
    contract = check_threshold(mem_db_with_threshold, record, {"p1": {"name": "Test Product"}})
    with patch("pricetrack.alert.smtplib.SMTP") as mock_smtp_cls:
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_server
        send_alert(contract, TEST_SMTP_CONFIG)
    assert mock_server.sendmail.called
    call_args = mock_server.sendmail.call_args
    assert call_args[0][1] == "user@example.com"  # recipient

def test_error_record_does_not_trigger_alert(mem_db_with_threshold):
    record = PriceRecord(
        product_id="p1", url="http://x.com", platform="amazon",
        price=None, currency="USD", scraped_at="2025-05-03T02:05:00Z",
        status="error", run_id="run_001"
    )
    contract = check_threshold(mem_db_with_threshold, record, {"p1": {"name": "Test Product"}})
    assert contract is None
```

---

## Error Handling Summary

| Failure mode | Graph node | Handling |
|---|---|---|
| CSS selector returns None | `risk_selector_change` | `status="error"` recorded; logged at WARNING; listed in run summary |
| Login-wall detected | `risk_cookie_expiry` | `status="session_expired"` recorded; warning email sent immediately |
| CAPTCHA detected | `risk_captcha` | Same path as session expiry |
| SMTP call fails | `risk_alert_failure` | Retry once after 60s; log ERROR; continue pipeline |
| Playwright exception per product | `req_error_recovery` | Per-product try/except; `status="error"` recorded |
| Full pipeline crash | `comp_scheduler` | APScheduler catches exception; failure email attempted |
| Cookie file missing | `dec_cookie_auth` | Startup check raises `FileNotFoundError` with clear message before run begins |

---

## Operational Runbook

### Weekly maintenance

1. Re-export Amazon and Walmart cookies (given `asm_cookie_longevity` confidence 0.70)
2. Review run-summary email from the previous night for any product errors
3. Check `logs/pricetrack.log` for WARNING or ERROR lines

### Responding to a selector failure

When the run-summary reports a product with `status="error"`:
1. Open the product URL in a logged-in browser
2. Use DevTools Inspector to identify the current price element
3. Update `PRICE_SELECTORS` in the relevant adapter (`amazon.py`, `ebay.py`, or `walmart.py`)
4. Capture a fresh HTML fixture: `python -m pricetrack capture-fixture --product-id <id>`
5. Run `pytest tests/test_scraper.py` to verify the updated selector
6. Restart the service: `sudo systemctl restart pricetrack`

### Responding to a session-expiry warning

1. Note which platform is named in the warning email
2. Log in to that platform in your browser
3. Open Cookie-Editor → Export → Netscape format
4. SCP the file to the VPS: `scp cookies_amazon.txt user@vps:/opt/pricetrack/config/`
5. No service restart needed — cookies are loaded fresh on each pipeline run

### Adding a new product

1. Find the canonical product URL (ensure it is a standard item page)
2. Add an entry to `config/products.yaml`
3. Run `python -m pricetrack run --dry-run --product-id <new_id>` to confirm extraction
4. The product is picked up on the next scheduled run

---

## Known Limitations and Non-Goals

- **No web UI**: Price history is stored in SQLite and must be queried directly or via a tool like DB Browser for SQLite. A web dashboard is a future extension.
- **No proxy support**: Paid residential proxies were explicitly excluded. If bot detection becomes persistent, rotating the VPS IP or sourcing a residential IP is the only mitigation.
- **No SMS alerts**: Twilio and other paid SMS providers are excluded. Gmail is the only delivery channel.
- **Single user**: Thresholds and cookies are for one user. Multi-account support would require a schema change to namespace products and thresholds by user.
- **Once-per-run price capture**: The pipeline runs once nightly. Intra-day price volatility is not captured unless `schedule_hour` in `settings.yaml` is changed and the run is triggered multiple times per day.
- **No CAPTCHA solving**: CAPTCHAs cause the affected product to be skipped for the run. There is no automated solver integration.
- **No historical price chart**: The database stores the full history, but there is no built-in visualization. Use `sqlite3` CLI or pandas to query `price_history` for trend analysis.
