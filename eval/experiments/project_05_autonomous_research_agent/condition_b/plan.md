# Condition B Plan — Autonomous Research Agent (Graph-Based Planning)

## Final System Overview

The system is an **autonomous research agent pipeline** that accepts a topic, retrieves relevant web sources, processes and synthesizes them, and generates a structured research report with citations.

The system is designed to:
- Run fully autonomously
- Handle failures gracefully
- Scale to ~200 queries/day on a local machine
- Produce high-quality, cited reports

---

## Architecture Overview

### Pipeline Flow

Job Manager → Search Engine → Content Processor → Summarizer  
→ Conflict Detector → Synthesis Engine → Citation Verifier  
→ Report Renderer → Output (Markdown + PDF)

---

## Core Components

### 1. Job Manager
- Accepts input query
- Tracks job lifecycle (queued → running → complete → failed)
- Manages concurrency using semaphore

---

### 2. Search & Retrieval Engine
- Uses Tavily API
- Retrieves full page content (not just snippets)
- Wrapped with retry + rate limiter

---

### 3. Content Processor
- Deduplicates using:
  - URL normalization
  - SHA-256 content hash
- Cleans and chunks content
- Applies token budget ordering

---

### 4. Summarizer
- Uses Claude (Anthropic API)
- Generates structured summaries per source
- Runs concurrently across sources

---

### 5. Conflict Detector
- Detects contradictory claims across sources
- Outputs structured conflict records

---

### 6. Synthesis Engine
- Generates fluent narrative report
- Includes conflict callout boxes
- Combines all summaries into structured output

---

### 7. Citation Verifier
- Runs second LLM pass
- Ensures all claims are properly cited
- Flags or injects missing citations

---

### 8. Report Renderer
- Outputs:
  - Markdown (primary)
  - PDF via WeasyPrint
- Includes references and structured sections

---

## Cross-Cutting Components

### Retry Manager
- Exponential backoff (1s, 2s, 4s, 8s)
- Max 4 retries
- On failure → dead-letter queue + log

---

### Rate Limiter
- Global semaphore (5–10 concurrent pipelines)
- Per-API token bucket (Tavily + Claude)

---

### Token Budget Manager
- Enforces per-query token limit
- Keeps high-relevance sources
- Drops low-relevance sources when needed

---

### Cost Tracker
- Tracks API token usage
- Logs warnings when threshold exceeded

---

### Job Store (SQLite)
- Stores:
  - Job metadata
  - Dedup hashes
  - Dead-letter queue
  - Cost tracking

---

### Notifier
- Structured log file (JSON)
- Logs:
  - Failures
  - Dead-letter entries
  - Cost alerts

---

## Key Architectural Decisions

### 1. Search API → Tavily
- Returns full page content
- Eliminates need for scraping layer

---

### 2. LLM → Claude
- Large context window
- Strong structured output support

---

### 3. Orchestration → asyncio (custom DAG)
- Lightweight
- Full control over retries and concurrency

---

### 4. Storage → SQLite + Filesystem
- No server required
- Easy local debugging

---

### 5. Output → Markdown + PDF
- Markdown as source of truth
- PDF generated via WeasyPrint

---

### 6. Retry Strategy
- 4 attempts with exponential backoff
- Failures stored in dead-letter queue

---

### 7. Deduplication Strategy
- URL + content hash (shallow dedup)
- No embedding-based similarity

---

### 8. Synthesis Strategy
- Fluent narrative report
- Post-hoc citation verification

---

### 9. Conflict Handling
- Always show:
  - Side-by-side claims
  - "Conflicting Evidence" callout box
- Never hide contradictions

---

### 10. Token Budgeting
- Per-query token limit
- Prioritize high-relevance sources

---

### 11. Notification Strategy
- Structured logs only (local setup)
- Extensible to Slack/email later

---

## Testing Strategy

### Unit Tests
- Content Processor (dedup + chunking)
- Retry Manager (backoff + failure handling)
- Token Budget enforcement
- Report Renderer

---

### Conformance Tests
- Validate API responses against schemas

---

### Integration Tests
- Full pipeline with mocked APIs
- No live API calls required

---

### Mocking Strategy
- Recorded fixtures for:
  - Tavily responses
  - Claude outputs
- Enables offline testing

---

## Error Handling Strategy

- Retry external calls (max 4 attempts)
- Dead-letter queue for persistent failures
- Partial results allowed (no full pipeline failure)
- Structured logging for debugging

---

## Assumptions

- Tavily provides reliable full-page content
- Claude context window is sufficient
- Local machine can handle 5–10 concurrent jobs
- Post-hoc citation check catches most issues
- Developer monitors logs manually

---

## Risks

- API rate limits may throttle pipeline
- LLM hallucination may pass verification
- Poor-quality sources reduce report quality
- Cost may grow without proper limits
- Dedup may miss semantic duplicates
- Dead-letter queue may grow without cleanup
- Low number of sources may produce weak reports

---

## Summary

Compared to Condition A, this plan:
- Clearly separates architecture from implementation
- Explicitly defines assumptions and risks
- Documents all key decisions with rationale
- Provides structured pipeline design instead of code-first output

This results in a more **robust, explainable, and evaluatable system design**.