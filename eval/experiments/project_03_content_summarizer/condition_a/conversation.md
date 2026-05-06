# Prompt text discussion
---

**User**

Ask any clarifying questions you need before planning

Build an automated personalized content monitoring and summarization pipeline with the following capabilities:

- Scrape or ingest content from multiple public sources (e.g., blogs, news sites, RSS feeds, forums). Handle pagination and basic dynamic loading where necessary.
- Ingest collected content into a persistent database, deduplicating across runs.
- Filter and rank content for relevance against a user profile (topics of interest, keywords, preferred sources).
- Generate concise summaries for each relevant item and compile a clean, formatted daily digest (email or PDF).
- Run unattended as an overnight scheduled job with robust logging and error recovery.
- Include a testing harness that validates parsing and extraction logic using saved content snapshots instead of live site calls.

---

**Cursor**

Before I plan the implementation, I need a few details to avoid building the wrong thing:

1. **Scope & sources**
- Which sources should we target first (specific RSS feeds/sites/forums)?
- Are there any sources we should explicitly exclude?
- Do you want only English content, or multilingual support?

2. **Scraping constraints**
- Is basic HTTP + HTML parsing enough for v1, or do you expect JS-rendered pages (Playwright/Selenium) from day one?
- Any legal/compliance constraints (robots.txt respect, rate limits, user agent policy)?

3. **User profile model**
- Will there be a **single user profile** or multiple users/profiles?
- How should relevance be scored: keyword matching only, embeddings/semantic similarity, or hybrid?
- Do preferred sources boost rank even if topic match is weaker?

4. **Database & persistence**
- Preferred DB: SQLite (simple), Postgres (production), or something else?
- Should we store full raw HTML/content snapshots, or only extracted fields + metadata?
- What dedup key should be authoritative (canonical URL, normalized title+date hash, content hash)?

5. **Summaries & digest output**
- Which LLM/provider should generate summaries (OpenAI/local/etc.)?
- Target summary length per item (e.g., 3 bullets, 100 words)?
- Daily digest format preference: email, PDF, or both?
- If email: any SMTP/provider requirements?

6. **Scheduling & operations**
- Preferred scheduler: cron, APScheduler, GitHub Actions, or another runner?
- What time zone and delivery time defines “daily”?
- Retry policy expectations (e.g., per-source retries, backoff, max failures)?

7. **Testing harness**
- Do you already have saved HTML/content snapshots, or should I define a fixture format and generate starter snapshots?
- Should tests cover only parsing/extraction, or also dedup + ranking + digest assembly integration?

8. **Environment & non-functional**
- Preferred language/framework (Python seems likely—okay to proceed with that)?
- Any deployment target constraints (local machine, Docker, cloud VM)?
- Expected scale (items/day) and latency budget for overnight run?

Once you answer these, I’ll provide a concrete architecture + phased build plan with component boundaries and test strategy.

---

**User**

All the popular sites, English content. JS-rendered would be better, try to not cross any legal limits. Single user profile, and boost rank preferred sources. SQLite should be good, store only extracted fields and metadata, use canonical URL as dedup key. A local LLM should be fine, summarize in 3 bullets, PDF is fine. No preferred scheduler and time zone should be CST(or CDT), use any retry policy.Define a fixture format and generate starter snapshots, tests should cover everything. Python is fine, and I will only run it on my local amchine. No latency budget for overnight run

---

**Cursor**

Perfect—this gives enough to move forward. I’ll scaffold a Python end-to-end pipeline in this project with JS-capable ingestion, SQLite persistence, relevance ranking, local-LLM summarization, PDF digest generation, scheduling hooks, retries/logging, and a full snapshot-based test harness. I’m starting by inspecting the repo layout, then I’ll implement the core modules and tests.

Great constraints set. Here’s a concrete implementation plan for your **Python local content-monitoring + summarization pipeline**.

## End-to-End Design

- **Ingestion layer**: source adapters for RSS, standard HTML pages, and JS-rendered sites (Playwright when needed).
- **Storage layer**: SQLite for persistent items, source-run metadata, dedup keys, scoring, summaries, and digest history.
- **Ranking layer**: profile-aware relevance scoring (keywords/topics + preferred-source boost).
- **Summarization layer**: local LLM summaries (3 bullets per relevant item).
- **Output layer**: daily PDF digest.
- **Scheduler/runtime**: unattended nightly run in local timezone (`America/Chicago`) with retries, structured logging, and partial-failure recovery.
- **Testing harness**: fixture-driven parser/extractor tests + integration pipeline tests, no live-site dependency.

## Proposed Project Structure

- `src/config/` – YAML/JSON config + user profile
- `src/sources/` – adapters (`rss.py`, `news_site.py`, `forum.py`, `playwright_site.py`)
- `src/ingest/` – fetch orchestration, normalization, canonical URL handling
- `src/db/` – SQLite schema + repository layer
- `src/ranking/` – relevance scorer with preferred-source boost
- `src/summarize/` – local LLM client abstraction + bullet formatter
- `src/digest/` – PDF renderer + daily digest builder
- `src/pipeline/` – orchestration, retries, checkpointing
- `src/scheduler/` – APScheduler/cron entrypoint
- `src/logging/` – structured logs + run summaries
- `tests/fixtures/` – saved HTML/RSS snapshots + expected extraction outputs
- `tests/` – unit + adapter + integration + end-to-end tests

## Core Data Model (SQLite)

- `sources` – source config and state
- `items` – canonical URL (unique), title, author, publish date, content text, source id, extracted metadata
- `item_runs` – when item was seen, extraction status/errors
- `scores` – per-item relevance score + score breakdown
- `summaries` – 3-bullet summary + model metadata
- `digests` – per-day digest outputs and generation metadata
- `runs` – pipeline run lifecycle + failure/success stats

Dedup is via **canonical URL unique index** (your requirement), with normalization before insert.

## Relevance Scoring (No LLM required)

- Base score from:
  - topic/keyword matches (title > body weighting)
  - source quality confidence
  - recency decay (optional)
- Preferred-source boost:
  - additive or multiplier boost when source in `preferred_sources`
- Hard filters:
  - language == English
  - optional blocked keywords/sources

## Summarization

- Local model adapter (Ollama/llama.cpp-compatible abstraction).
- Prompt enforces exactly 3 concise bullets per item.
- Store raw response + parsed bullet list + validation status.
- Retry on malformed output; fallback bullet extraction from raw output.

## Overnight Scheduling + Reliability

- Run nightly at configurable local time in CST/CDT (`America/Chicago`).
- Retry policy:
  - source fetch retries with exponential backoff
  - per-item summarization retries
- Error recovery:
  - failures in one source/item do not fail entire run
  - run summary records partial failures
- Logging:
  - JSON logs + human-readable run summary file

## Testing Harness (Snapshot-First)

- Fixture format (starter):
  - `tests/fixtures/<source>/<case_name>/raw.(html|xml|json)`
  - `tests/fixtures/<source>/<case_name>/expected.json`
- Tests:
  - parser unit tests for each adapter
  - canonical URL normalization + dedup tests
  - ranking tests (including preferred source boosts)
  - summarizer contract tests (3 bullets, fallback paths)
  - digest generation tests (PDF file created + expected contents)
  - full integration run over fixtures only

## Legal/Compliance Guardrails

- Respect `robots.txt` where applicable
- Rate limiting + polite delays
- Clear user-agent string
- No authentication bypass or restricted-content scraping
- Maintain source allowlist

If you want, I’ll now move from plan to implementation and scaffold **v1 in this repo** (configs, DB schema, adapters, pipeline, PDF digest, and full fixture-based tests) in one pass.

---