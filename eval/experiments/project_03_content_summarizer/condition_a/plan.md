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