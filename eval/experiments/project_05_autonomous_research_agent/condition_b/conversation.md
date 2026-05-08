Ask any clarifying questions you need before planning.
Build an autonomous research agent system with the following capabilities:
* Accept a high-level research topic as input (e.g., "impact of AI on healthcare").
* Automatically search and retrieve relevant information from multiple web sources.
* Extract, summarize, and synthesize information into a structured report.
* Handle conflicting or duplicate information across sources.
* Maintain citations and references for all extracted information.
* Generate a final well-formatted research report.
System requirements:
* Operate as a multi-step pipeline (retrieval → processing → synthesis → output).
* Run autonomously with minimal human input once started.
* Handle failures such as API errors, missing data, or partial results.
* Include a testing strategy that does not rely on live API calls.
* Ensure scalability for multiple research queries.
Design the full system architecture, including components, data flow, and key technical decisions.

Show less
13:48
Claude responded: Before I build out the decision graph and architecture, I have a few targeted questions to make sure the plan reflects your actual constraints — not just reaso…

Formulated clarifying questions before architecting research agent system
Formulated clarifying questions before architecting research agent system
Before I build out the decision graph and architecture, I have a few targeted questions to make sure the plan reflects your actual constraints — not just reasonable defaults.

1. Deployment & runtime environment Where does this system run? A developer's local machine, a cloud VM/container (AWS/GCP/Azure), or a managed serverless platform? This determines how I design the pipeline orchestration, concurrency model, and failure-recovery strategy.

2. Search & retrieval source Do you have a preferred web search API (e.g., Tavily, Serper, Bing Search, Google Custom Search), or is that an open decision? And should the system retrieve only search snippets, or also scrape and read full page content? The latter changes complexity significantly.

3. LLM for summarization & synthesis Are you building on top of the Anthropic API (Claude), OpenAI, or keeping that as an open decision? This matters for how I design the synthesis pipeline and whether tool-use / structured outputs are in scope.

4. Output format & consumer Who or what consumes the final report — a human reading a Markdown/PDF file, a downstream system ingesting structured JSON, or both? This shapes the interface contract for the output stage.

5. Scalability definition When you say "scalability for multiple research queries" — do you mean concurrent queries running in parallel, or sequential queries queued over time? And what's the rough target scale (tens per day vs. hundreds per hour)?

You said: Deployment & runtime environment - Local Machine
Deployment & runtime environment - Local Machine
Search & retrieval source - No Preference
LLM for summarization & synthesis - its open
Output format & consumer - a human reading PDF/Markdown file
Scalability definition - concurrent queries running in parallel, target scale would be may be 200 per day

13:51
Claude responded: Phase 1 — Core Architecture

Architected autonomous research pipeline with Tavily, Claude, and asyncio
Architected autonomous research pipeline with Tavily, Claude, and asyncio
Phase 1 — Core Architecture
Great constraints to work with. 200 queries/day at local-machine concurrency is achievable but needs careful design around API rate limits and resource saturation. Let me work through the foundational decisions now.

Key Phase 1 decisions I'm making and why:

Search API → Tavily: Purpose-built for AI agents — returns full cleaned page content (not just snippets), has a Python SDK, and doesn't require a separate scraping layer. Alternatives like Serper/Google CSE return snippets only, requiring a second scraping pass.
LLM → Claude (Anthropic API) with tool use and structured output support. Alternatives considered: OpenAI GPT-4o, local Ollama models.
Pipeline orchestration → Custom async Python (asyncio + task queues): LangChain/LangGraph adds abstraction overhead for a well-defined pipeline like this. A custom DAG is lighter, more debuggable, and directly controllable.
Concurrency model → asyncio with a bounded semaphore: 200/day ≈ 8–9/hour average, but bursty concurrency may hit 10–20 simultaneous. A semaphore cap prevents resource exhaustion.
Storage → SQLite (job state) + local filesystem (artifacts): No server to manage. SQLite handles job tracking, dedup hashing, and run history. Artifacts (raw HTML, chunks, final reports) live on disk.
Output → Markdown primary, PDF via WeasyPrint: Markdown is the source of truth; PDF is derived. Avoids heavy dependencies like LaTeX.
[GRAPH UPDATE]

json
{
  "nodes": [
    {
      "id": "obj_autonomous_research",
      "type": "objective",
      "label": "Fully autonomous research pipeline",
      "description": "Accept a topic, retrieve sources, synthesize findings, and emit a report without human intervention."
    },
    {
      "id": "obj_structured_output",
      "type": "objective",
      "label": "Well-formatted cited reports",
      "description": "Final output must be human-readable with clear sections, citations, and references."
    },
    {
      "id": "obj_concurrent_scale",
      "type": "objective",
      "label": "Support ~200 concurrent queries/day",
      "description": "System must handle parallel research queries on a single local machine without queue starvation or resource exhaustion."
    },
    {
      "id": "req_autonomous",
      "type": "requirement",
      "label": "Minimal human input post-start",
      "description": "Once a query is submitted, the pipeline runs to completion or structured failure with no prompts.",
      "is_functional": true
    },
    {
      "id": "req_citations",
      "type": "requirement",
      "label": "All claims must carry source citations",
      "description": "Every extracted fact or summary block in the report must link back to its source URL and retrieval timestamp.",
      "is_functional": true
    },
    {
      "id": "req_failure_handling",
      "type": "requirement",
      "label": "Graceful degradation on partial failures",
      "description": "API errors, missing sources, or scraping failures must not abort the full pipeline — partial results are valid output.",
      "is_functional": true
    },
    {
      "id": "req_dedup",
      "type": "requirement",
      "label": "Deduplicate and reconcile conflicting sources",
      "description": "Duplicate content across sources must be collapsed; conflicting claims must be flagged, not silently merged.",
      "is_functional": true
    },
    {
      "id": "req_offline_tests",
      "type": "requirement",
      "label": "Test suite must not require live API calls",
      "description": "All tests must be runnable offline using fixtures, mocks, and recorded responses.",
      "is_functional": false
    },
    {
      "id": "dec_search_api",
      "type": "decision",
      "label": "Use Tavily as the search and retrieval API",
      "description": "Tavily is selected as the primary web search provider, returning full cleaned page content per result.",
      "rationale": "Tavily is purpose-built for AI agent pipelines — it returns full page text (not snippets), includes relevance scoring, and eliminates a separate scraping layer. Its Python SDK integrates cleanly with async code.",
      "alternatives_considered": ["Serper (snippets only, requires scraping layer)", "Bing Search API (snippet-based, higher per-call cost)", "Google Custom Search API (quota limits, snippet-only on free tier)", "SerpAPI (costly at scale)"]
    },
    {
      "id": "dec_llm",
      "type": "decision",
      "label": "Use Claude (Anthropic API) for summarization and synthesis",
      "description": "Claude is the LLM backbone for per-source summarization, conflict detection, and final synthesis.",
      "rationale": "Large context window (100K+) handles multi-source synthesis in a single pass. Structured output support via tool use enables reliable JSON extraction for citation tracking. Strong instruction-following for report formatting.",
      "alternatives_considered": ["OpenAI GPT-4o (comparable capability, different pricing structure)", "Ollama local models (no API cost, but slower on CPU, weaker synthesis quality at local sizes)", "Gemini 1.5 Pro (large context, less mature tooling ecosystem)"]
    },
    {
      "id": "dec_orchestration",
      "type": "decision",
      "label": "Custom async Python pipeline (asyncio)",
      "description": "The pipeline is implemented as a hand-rolled async DAG in Python rather than a framework like LangGraph or Prefect.",
      "rationale": "The pipeline has a fixed, well-defined stage sequence (retrieve → chunk → summarize → deduplicate → synthesize → render). A custom DAG gives full control over error boundaries, retry logic, and semaphore-based concurrency without framework overhead or abstraction leakage.",
      "alternatives_considered": ["LangChain/LangGraph (adds abstraction overhead, harder to debug, overkill for fixed pipeline)", "Prefect/Dagster (workflow orchestration tools suited for scheduled ETL, not interactive agent pipelines)", "Celery + Redis (requires a Redis server, adds infra complexity on local machine)"]
    },
    {
      "id": "dec_storage",
      "type": "decision",
      "label": "SQLite for job state, filesystem for artifacts",
      "description": "SQLite tracks job metadata, source hashes for deduplication, and run history. Raw content and final reports live as files on disk.",
      "rationale": "No server to manage. SQLite is sufficient for 200 jobs/day on a single machine. File-per-artifact is simple, inspectable, and avoids blob storage complexity.",
      "alternatives_considered": ["PostgreSQL (server overhead, unnecessary for local)", "DuckDB (good for analytics queries, less suited for transactional job state)", "Pure filesystem with JSON sidecar files (loses queryability for dedup lookups)"]
    },
    {
      "id": "dec_concurrency",
      "type": "decision",
      "label": "asyncio with bounded semaphore for concurrent queries",
      "description": "Concurrent queries are managed via an asyncio semaphore capping simultaneous in-flight pipelines.",
      "rationale": "200/day averages ~8/hour but bursts are expected. A semaphore cap (e.g., 5–10 concurrent) prevents memory exhaustion and API rate-limit collisions without a separate job queue server.",
      "alternatives_considered": ["multiprocessing (CPU-bound workloads; this pipeline is I/O-bound, asyncio is more efficient)", "ThreadPoolExecutor (GIL limits true parallelism; asyncio handles I/O concurrency natively)", "Ray (distributed computing framework, overkill for single-machine local target)"]
    },
    {
      "id": "dec_output",
      "type": "decision",
      "label": "Markdown primary output, PDF via WeasyPrint",
      "description": "The pipeline writes a structured Markdown report as its canonical artifact; PDF is rendered from it via WeasyPrint.",
      "rationale": "Markdown is version-controllable, diff-able, and easily inspected. WeasyPrint converts HTML/CSS to PDF without requiring LaTeX or headless Chrome.",
      "alternatives_considered": ["LaTeX (high-quality PDFs but heavy dependency, complex templating)", "ReportLab (programmatic PDF, verbose, poor for narrative text)", "Pandoc (excellent converter but adds a system binary dependency)"]
    },
    {
      "id": "asm_tavily_rate_limits",
      "type": "assumption",
      "label": "Tavily API rate limits accommodate burst concurrency",
      "description": "Assumes Tavily's plan tier allows enough requests/minute to serve 10 concurrent pipelines each making 3–5 search calls without throttling.",
      "confidence": 0.6,
      "validated": false
    },
    {
      "id": "asm_context_window",
      "type": "assumption",
      "label": "Multi-source content fits Claude's context window",
      "description": "Assumes that the combined chunked summaries from all sources for a single topic fit within Claude's context window for the synthesis step.",
      "confidence": 0.75,
      "validated": false
    },
    {
      "id": "asm_local_resources",
      "type": "assumption",
      "label": "Local machine can sustain 5–10 concurrent async pipelines",
      "description": "Assumes the host machine has enough RAM and network bandwidth for concurrent Tavily fetches and LLM calls without thrashing.",
      "confidence": 0.7,
      "validated": false
    },
    {
      "id": "asm_tavily_content_quality",
      "type": "assumption",
      "label": "Tavily returns substantive full-page content reliably",
      "description": "Assumes Tavily successfully extracts readable text from the majority of retrieved URLs (vs. returning empty or JavaScript-only shells).",
      "confidence": 0.65,
      "validated": false
    },
    {
      "id": "risk_api_cost",
      "type": "risk",
      "label": "LLM + search API costs escalate at scale",
      "description": "At 200 queries/day with 5–10 LLM calls per query, token costs could become significant. No cost cap is currently modeled.",
      "severity": 0.7
    },
    {
      "id": "risk_rate_limiting",
      "type": "risk",
      "label": "API rate limits throttle or fail concurrent pipelines",
      "description": "Bursts of concurrent queries may exhaust Tavily or Claude API rate limits, causing cascading failures across multiple pipelines.",
      "severity": 0.8
    },
    {
      "id": "risk_hallucination",
      "type": "risk",
      "label": "LLM hallucination in synthesis step",
      "description": "Claude may introduce claims not grounded in retrieved sources during the synthesis step, undermining report accuracy.",
      "severity": 0.75
    },
    {
      "id": "risk_content_quality",
      "type": "risk",
      "label": "Poor or paywalled source content degrades report quality",
      "description": "Many high-quality sources (academic papers, news archives) are paywalled or return minimal content, reducing synthesis quality.",
      "severity": 0.65
    },
    {
      "id": "risk_dedup_false_negative",
      "type": "risk",
      "label": "Semantic duplicates pass hash-based deduplication",
      "description": "Two sources reporting the same fact in different words will pass URL/hash dedup and be treated as independent corroboration.",
      "severity": 0.6
    }
  ],
  "edges": [
    { "source_id": "dec_search_api", "target_id": "obj_autonomous_research", "type": "motivated_by" },
    { "source_id": "dec_llm", "target_id": "obj_structured_output", "type": "motivated_by" },
    { "source_id": "dec_concurrency", "target_id": "obj_concurrent_scale", "type": "motivated_by" },
    { "source_id": "dec_orchestration", "target_id": "obj_autonomous_research", "type": "motivated_by" },
    { "source_id": "dec_output", "target_id": "obj_structured_output", "type": "motivated_by" },
    { "source_id": "dec_search_api", "target_id": "asm_tavily_rate_limits", "type": "assumes" },
    { "source_id": "dec_search_api", "target_id": "asm_tavily_content_quality", "type": "assumes" },
    { "source_id": "dec_llm", "target_id": "asm_context_window", "type": "assumes" },
    { "source_id": "dec_concurrency", "target_id": "asm_local_resources", "type": "assumes" },
    { "source_id": "risk_rate_limiting", "target_id": "dec_concurrency", "type": "conflicts_with" },
    { "source_id": "risk_rate_limiting", "target_id": "asm_tavily_rate_limits", "type": "invalidates" },
    { "source_id": "risk_hallucination", "target_id": "req_citations", "type": "conflicts_with" },
    { "source_id": "risk_content_quality", "target_id": "asm_tavily_content_quality", "type": "invalidates" },
    { "source_id": "risk_api_cost", "target_id": "dec_llm", "type": "conflicts_with" },
    { "source_id": "risk_dedup_false_negative", "target_id": "req_dedup", "type": "conflicts_with" }
  ]
}
[/GRAPH UPDATE]

Phase 1 Follow-up Questions
Three gaps the graph has surfaced that I need your input on before moving to component design:

Q1 — Rate limit mitigation strategy (risk_rate_limiting, severity 0.8 — no guard yet)** When Tavily or Claude returns a 429, should the pipeline: (a) retry with exponential backoff and continue, (b) park the affected query in a "retry later" queue, or (c) complete the report with whatever sources succeeded and flag it as partial? This shapes the entire error-handling design.

Q2 — Hallucination containment (risk_hallucination, severity 0.75)** The most practical mitigation is grounded synthesis — forcing Claude to only synthesize from explicitly passed source chunks and flagging any claim it can't attribute. Are you willing to accept a stricter, slightly more mechanical report style in exchange for that guarantee? Or is a more fluent narrative report (with a post-hoc citation-check pass) preferable?

Q3 — Deduplication depth (risk_dedup_false_negative, confidence gap on req_dedup)** For duplicate/conflicting content, two approaches are on the table:

Shallow (URL + content hash): Fast, zero extra cost, catches exact/near-exact duplicates.
Semantic (embedding similarity): Catches paraphrased duplicates and can cluster conflicting claims — but adds an embedding model dependency and ~20–40ms per source chunk.
Which matters more: speed/simplicity, or catching semantic duplicates?

You said: Q1) Retry for 3-4 times .
Q1) Retry for 3-4 times .. then also if error is coming, Keep it in a queue or report it back to the developers

Q2) fluent narrative report

Q3) Shallow (URL + content hash)

13:59
Claude responded: Phase 2 — Component Design, Interfaces & Dependencies

Architected Phase 2 pipeline with retry logic, synthesis strategy, and component design
Architected Phase 2 pipeline with retry logic, synthesis strategy, and component design
Phase 2 — Component Design, Interfaces & Dependencies
Locking in the three answers as explicit decisions before building out the component layer:

Retry: exponential backoff × 3–4 attempts → dead-letter queue + developer notification
Synthesis: fluent narrative + post-hoc citation verification pass
Dedup: shallow URL + SHA-256 content hash
Here's the full component breakdown and how data flows through each stage:

Pipeline data flow:

[Job Manager] → [Search Engine] → [Content Processor] → [Summarizer]
      ↓                                                        ↓
[Job Store]                                        [Conflict Detector]
      ↓                                                        ↓
[Report Renderer] ← [Citation Verifier] ← [Synthesis Engine]
      ↓
[Markdown + PDF output]
Cross-cutting concerns (touch every stage):

Retry Manager wraps all external calls (Tavily + Claude)
Rate Limiter gates concurrency via semaphore + per-API token bucket
Notifier fires on dead-letter queue entries
[GRAPH UPDATE]

json
{
  "nodes": [
    {
      "id": "obj_autonomous_research",
      "type": "objective",
      "label": "Fully autonomous research pipeline",
      "description": "Accept a topic, retrieve sources, synthesize findings, and emit a report without human intervention."
    },
    {
      "id": "obj_structured_output",
      "type": "objective",
      "label": "Well-formatted cited reports",
      "description": "Final output must be human-readable with clear sections, citations, and references."
    },
    {
      "id": "obj_concurrent_scale",
      "type": "objective",
      "label": "Support ~200 concurrent queries/day",
      "description": "System must handle parallel research queries on a single local machine without queue starvation or resource exhaustion."
    },
    {
      "id": "req_autonomous",
      "type": "requirement",
      "label": "Minimal human input post-start",
      "description": "Once a query is submitted, the pipeline runs to completion or structured failure with no prompts.",
      "is_functional": true
    },
    {
      "id": "req_citations",
      "type": "requirement",
      "label": "All claims must carry source citations",
      "description": "Every extracted fact or summary block in the report must link back to its source URL and retrieval timestamp.",
      "is_functional": true
    },
    {
      "id": "req_failure_handling",
      "type": "requirement",
      "label": "Graceful degradation on partial failures",
      "description": "API errors, missing sources, or scraping failures must not abort the full pipeline — partial results are valid output.",
      "is_functional": true
    },
    {
      "id": "req_dedup",
      "type": "requirement",
      "label": "Deduplicate and reconcile conflicting sources",
      "description": "Duplicate content across sources must be collapsed; conflicting claims must be flagged, not silently merged.",
      "is_functional": true
    },
    {
      "id": "req_offline_tests",
      "type": "requirement",
      "label": "Test suite must not require live API calls",
      "description": "All tests must be runnable offline using fixtures, mocks, and recorded responses.",
      "is_functional": false
    },
    {
      "id": "dec_search_api",
      "type": "decision",
      "label": "Use Tavily as the search and retrieval API",
      "description": "Tavily is selected as the primary web search provider, returning full cleaned page content per result.",
      "rationale": "Purpose-built for AI agent pipelines — returns full page text, includes relevance scoring, eliminates a separate scraping layer. Python SDK integrates cleanly with asyncio.",
      "alternatives_considered": ["Serper (snippets only, requires scraping layer)", "Bing Search API (snippet-based, higher per-call cost)", "Google Custom Search API (quota limits, snippet-only on free tier)", "SerpAPI (costly at scale)"]
    },
    {
      "id": "dec_llm",
      "type": "decision",
      "label": "Use Claude (Anthropic API) for summarization and synthesis",
      "description": "Claude is the LLM backbone for per-source summarization, conflict detection, and final synthesis.",
      "rationale": "Large context window handles multi-source synthesis in a single pass. Structured output via tool use enables reliable JSON for citation tracking. Strong instruction-following for report formatting.",
      "alternatives_considered": ["OpenAI GPT-4o (comparable capability, different pricing)", "Ollama local models (no API cost, slower on CPU, weaker synthesis quality)", "Gemini 1.5 Pro (large context, less mature tooling ecosystem)"]
    },
    {
      "id": "dec_orchestration",
      "type": "decision",
      "label": "Custom async Python pipeline (asyncio)",
      "description": "The pipeline is implemented as a hand-rolled async DAG in Python rather than a framework like LangGraph or Prefect.",
      "rationale": "Fixed, well-defined stage sequence. Custom DAG gives full control over error boundaries, retry logic, and semaphore-based concurrency without framework overhead.",
      "alternatives_considered": ["LangChain/LangGraph (abstraction overhead, harder to debug)", "Prefect/Dagster (suited for ETL, not interactive agent pipelines)", "Celery + Redis (requires Redis server, adds infra complexity on local machine)"]
    },
    {
      "id": "dec_storage",
      "type": "decision",
      "label": "SQLite for job state, filesystem for artifacts",
      "description": "SQLite tracks job metadata, source hashes for dedup, and dead-letter entries. Raw content and final reports live as files on disk.",
      "rationale": "No server to manage. SQLite is sufficient for 200 jobs/day on a single machine. File-per-artifact is simple and inspectable.",
      "alternatives_considered": ["PostgreSQL (server overhead, unnecessary for local)", "DuckDB (good for analytics, less suited for transactional job state)", "Pure filesystem JSON sidecars (loses queryability for dedup lookups)"]
    },
    {
      "id": "dec_concurrency",
      "type": "decision",
      "label": "asyncio with bounded semaphore for concurrent queries",
      "description": "Concurrent queries are managed via an asyncio semaphore capping simultaneous in-flight pipelines, with a per-API token bucket rate limiter.",
      "rationale": "200/day averages ~8/hour but bursts are expected. Semaphore cap (5–10 concurrent) prevents memory exhaustion and API rate-limit collisions.",
      "alternatives_considered": ["multiprocessing (CPU-bound; this pipeline is I/O-bound)", "ThreadPoolExecutor (GIL limits parallelism)", "Ray (overkill for single-machine target)"]
    },
    {
      "id": "dec_output",
      "type": "decision",
      "label": "Markdown primary output, PDF via WeasyPrint",
      "description": "Markdown is the canonical report artifact; PDF is derived from it via WeasyPrint.",
      "rationale": "Markdown is version-controllable and diff-able. WeasyPrint converts HTML/CSS to PDF without requiring LaTeX or headless Chrome.",
      "alternatives_considered": ["LaTeX (high-quality PDF but heavy dependency)", "ReportLab (verbose, poor for narrative text)", "Pandoc (excellent but adds a system binary dependency)"]
    },
    {
      "id": "dec_retry_strategy",
      "type": "decision",
      "label": "Exponential backoff × 4, then dead-letter queue + developer alert",
      "description": "All external API calls are wrapped in a retry decorator: attempts at 1s, 2s, 4s, 8s backoff. On 4th failure, the job is written to a dead_letter_queue table in SQLite and a developer notification is fired.",
      "rationale": "Transient errors (429, 503) are common in API-heavy pipelines. Four attempts covers most transient spikes. Dead-letter queue ensures no silent data loss and allows manual replay. Developer notification enables fast incident response.",
      "alternatives_considered": ["Fail fast with no retry (too fragile for production use)", "Infinite retry (risks live-lock under sustained outage)", "Separate retry worker process (over-engineered for local single-machine target)"]
    },
    {
      "id": "dec_synthesis_style",
      "type": "decision",
      "label": "Fluent narrative synthesis with post-hoc citation verification",
      "description": "Claude generates a flowing narrative report, then a second LLM pass checks each paragraph for citation coverage and flags or injects missing references.",
      "rationale": "Fluent narrative is more readable for human consumers. Post-hoc verification catches most attribution gaps without forcing a mechanical citation-per-sentence constraint during generation.",
      "alternatives_considered": ["Strictly grounded synthesis (every sentence constrained to source chunks — more reliable but mechanical prose)", "No verification pass (faster but risks unchecked hallucination drift)"]
    },
    {
      "id": "dec_dedup_strategy",
      "type": "decision",
      "label": "Shallow deduplication via URL + SHA-256 content hash",
      "description": "Sources are deduplicated by normalising their URL and hashing their full text content. Matches on either key are collapsed to the first-seen copy.",
      "rationale": "Fast, zero extra API cost, no additional model dependency. Catches syndicated articles (same URL), mirror sites (same hash, different URL), and cached pages.",
      "alternatives_considered": ["Semantic embedding similarity (catches paraphrased duplicates but adds model dependency and latency per chunk)", "Title similarity only (too coarse, misses same-content different-title articles)"]
    },
    {
      "id": "comp_job_manager",
      "type": "component",
      "label": "Job Manager",
      "description": "Accepts research query input, creates a job record in SQLite, acquires a semaphore slot, and dispatches the pipeline. Tracks overall job lifecycle (queued → running → complete → failed).",
      "has_tests": false
    },
    {
      "id": "comp_search_engine",
      "type": "component",
      "label": "Search & Retrieval Engine",
      "description": "Calls Tavily API with the research topic, retrieves N results with full page content, and returns a list of raw SearchResult objects. Wrapped by Retry Manager.",
      "has_tests": false
    },
    {
      "id": "comp_content_processor",
      "type": "component",
      "label": "Content Processor",
      "description": "Deduplicates results by URL and SHA-256 hash, strips boilerplate, and chunks content into token-bounded segments for downstream LLM calls.",
      "has_tests": false
    },
    {
      "id": "comp_summarizer",
      "type": "component",
      "label": "Per-Source Summarizer",
      "description": "Calls Claude once per deduplicated source chunk to produce a structured summary with inline source attribution tags. Runs concurrently across sources.",
      "has_tests": false
    },
    {
      "id": "comp_conflict_detector",
      "type": "component",
      "label": "Conflict Detector",
      "description": "Scans the set of source summaries for contradictory claims on the same subject. Flags conflicts with a confidence score and both source references for the synthesis step.",
      "has_tests": false
    },
    {
      "id": "comp_synthesis_engine",
      "type": "component",
      "label": "Synthesis Engine",
      "description": "Calls Claude with all source summaries, conflict flags, and a structured report template to produce a fluent narrative research report draft.",
      "has_tests": false
    },
    {
      "id": "comp_citation_verifier",
      "type": "component",
      "label": "Citation Verifier",
      "description": "Runs a second LLM pass over the synthesized report. For each paragraph, checks that at least one citation is present and grounded in the source summaries. Flags or auto-injects missing references.",
      "has_tests": false
    },
    {
      "id": "comp_report_renderer",
      "type": "component",
      "label": "Report Renderer",
      "description": "Transforms the verified report into structured Markdown with a references section, then renders a PDF via WeasyPrint using a CSS template.",
      "has_tests": false
    },
    {
      "id": "comp_retry_manager",
      "type": "component",
      "label": "Retry Manager",
      "description": "Decorator/wrapper applied to all external API calls. Implements exponential backoff (1s/2s/4s/8s × 4 attempts). On exhaustion writes to dead_letter_queue and triggers the Notifier.",
      "has_tests": false
    },
    {
      "id": "comp_rate_limiter",
      "type": "component",
      "label": "Rate Limiter",
      "description": "Maintains a global asyncio semaphore for pipeline concurrency and per-API token buckets for Tavily and Claude to prevent rate-limit exhaustion.",
      "has_tests": false
    },
    {
      "id": "comp_job_store",
      "type": "component",
      "label": "Job Store (SQLite)",
      "description": "Persists job records, source content hashes for dedup, dead-letter queue entries, and run history. Accessed via SQLAlchemy async session.",
      "has_tests": false
    },
    {
      "id": "comp_notifier",
      "type": "component",
      "label": "Developer Notifier",
      "description": "Fires when a job enters the dead-letter queue. Writes a structured error log entry and optionally dispatches a webhook or email alert with job ID, stage, error type, and timestamp.",
      "has_tests": false
    },
    {
      "id": "iface_search_result",
      "type": "interface",
      "label": "SearchResult schema",
      "description": "Normalised output contract from the Search Engine.",
      "contract": "{ url: str, title: str, raw_content: str, relevance_score: float, retrieved_at: datetime }"
    },
    {
      "id": "iface_source_chunk",
      "type": "interface",
      "label": "SourceChunk schema",
      "description": "Token-bounded content unit output by the Content Processor, ready for LLM ingestion.",
      "contract": "{ chunk_id: str, url: str, content_hash: str, text: str, token_count: int, chunk_index: int }"
    },
    {
      "id": "iface_source_summary",
      "type": "interface",
      "label": "SourceSummary schema",
      "description": "Structured per-source summary with attribution, output by the Summarizer.",
      "contract": "{ summary_id: str, url: str, title: str, key_points: list[str], conflicts: list[str], retrieved_at: datetime }"
    },
    {
      "id": "iface_report_schema",
      "type": "interface",
      "label": "Final Report schema",
      "description": "Structured report contract passed from Synthesis Engine through Citation Verifier to Report Renderer.",
      "contract": "{ title: str, executive_summary: str, sections: list[{heading, body, citations}], conflicts_noted: list[str], references: list[{id, url, title, retrieved_at}] }"
    },
    {
      "id": "asm_tavily_rate_limits",
      "type": "assumption",
      "label": "Tavily API rate limits accommodate burst concurrency",
      "description": "Assumes Tavily's plan tier allows enough requests/minute to serve 10 concurrent pipelines each making 3–5 search calls without throttling.",
      "confidence": 0.6,
      "validated": false
    },
    {
      "id": "asm_context_window",
      "type": "assumption",
      "label": "Multi-source summaries fit Claude's context window for synthesis",
      "description": "Assumes combined SourceSummary objects for a single topic fit within Claude's context window (after per-source summarization reduces raw content volume).",
      "confidence": 0.8,
      "validated": false
    },
    {
      "id": "asm_local_resources",
      "type": "assumption",
      "label": "Local machine sustains 5–10 concurrent async pipelines",
      "description": "Assumes enough RAM and network bandwidth for concurrent Tavily fetches and LLM calls without thrashing.",
      "confidence": 0.7,
      "validated": false
    },
    {
      "id": "asm_tavily_content_quality",
      "type": "assumption",
      "label": "Tavily returns substantive full-page content reliably",
      "description": "Assumes Tavily successfully extracts readable text from the majority of retrieved URLs vs. returning empty or JS-only shells.",
      "confidence": 0.65,
      "validated": false
    },
    {
      "id": "asm_posthoc_citation_sufficient",
      "type": "assumption",
      "label": "Post-hoc citation pass catches most attribution gaps",
      "description": "Assumes a second LLM verification pass is sufficient to catch uncited claims in the fluent narrative, without requiring fully grounded generation.",
      "confidence": 0.65,
      "validated": false
    },
    {
      "id": "risk_api_cost",
      "type": "risk",
      "label": "LLM + search API costs escalate at scale",
      "description": "At 200 queries/day with multiple LLM calls per pipeline stage, token costs could become significant without a cost ceiling.",
      "severity": 0.7
    },
    {
      "id": "risk_rate_limiting",
      "type": "risk",
      "label": "API rate limits throttle or fail concurrent pipelines",
      "description": "Bursts of concurrent queries may exhaust Tavily or Claude API rate limits, causing cascading failures across multiple pipelines.",
      "severity": 0.8
    },
    {
      "id": "risk_hallucination",
      "type": "risk",
      "label": "LLM hallucination survives post-hoc citation check",
      "description": "Fluent narrative generation may introduce plausible-sounding but unsourced claims that the citation verifier fails to catch if they blend with cited content.",
      "severity": 0.7
    },
    {
      "id": "risk_content_quality",
      "type": "risk",
      "label": "Poor or paywalled source content degrades report quality",
      "description": "Many high-quality sources are paywalled or return minimal content, reducing synthesis quality silently.",
      "severity": 0.65
    },
    {
      "id": "risk_dedup_false_negative",
      "type": "risk",
      "label": "Semantic duplicates pass hash-based deduplication",
      "description": "Two sources reporting the same fact in different words pass URL/hash dedup and are treated as independent corroboration.",
      "severity": 0.6
    },
    {
      "id": "risk_deadletter_growth",
      "type": "risk",
      "label": "Dead-letter queue grows unbounded without manual replay",
      "description": "If a systemic API outage affects many concurrent jobs, the dead-letter table may accumulate hundreds of entries with no automated replay mechanism.",
      "severity": 0.55
    }
  ],
  "edges": [
    { "source_id": "dec_search_api", "target_id": "obj_autonomous_research", "type": "motivated_by" },
    { "source_id": "dec_llm", "target_id": "obj_structured_output", "type": "motivated_by" },
    { "source_id": "dec_concurrency", "target_id": "obj_concurrent_scale", "type": "motivated_by" },
    { "source_id": "dec_orchestration", "target_id": "obj_autonomous_research", "type": "motivated_by" },
    { "source_id": "dec_output", "target_id": "obj_structured_output", "type": "motivated_by" },
    { "source_id": "dec_retry_strategy", "target_id": "req_failure_handling", "type": "motivated_by" },
    { "source_id": "dec_dedup_strategy", "target_id": "req_dedup", "type": "motivated_by" },
    { "source_id": "dec_synthesis_style", "target_id": "obj_structured_output", "type": "motivated_by" },
    { "source_id": "dec_search_api", "target_id": "asm_tavily_rate_limits", "type": "assumes" },
    { "source_id": "dec_search_api", "target_id": "asm_tavily_content_quality", "type": "assumes" },
    { "source_id": "dec_llm", "target_id": "asm_context_window", "type": "assumes" },
    { "source_id": "dec_concurrency", "target_id": "asm_local_resources", "type": "assumes" },
    { "source_id": "dec_synthesis_style", "target_id": "asm_posthoc_citation_sufficient", "type": "assumes" },
    { "source_id": "risk_rate_limiting", "target_id": "dec_concurrency", "type": "conflicts_with" },
    { "source_id": "risk_rate_limiting", "target_id": "asm_tavily_rate_limits", "type": "invalidates" },
    { "source_id": "risk_hallucination", "target_id": "req_citations", "type": "conflicts_with" },
    { "source_id": "risk_hallucination", "target_id": "asm_posthoc_citation_sufficient", "type": "invalidates" },
    { "source_id": "risk_content_quality", "target_id": "asm_tavily_content_quality", "type": "invalidates" },
    { "source_id": "risk_api_cost", "target_id": "dec_llm", "type": "conflicts_with" },
    { "source_id": "risk_dedup_false_negative", "target_id": "req_dedup", "type": "conflicts_with" },
    { "source_id": "comp_job_manager", "target_id": "req_autonomous", "type": "implements" },
    { "source_id": "comp_content_processor", "target_id": "req_dedup", "type": "implements" },
    { "source_id": "comp_citation_verifier", "target_id": "req_citations", "type": "implements" },
    { "source_id": "comp_retry_manager", "target_id": "req_failure_handling", "type": "implements" },
    { "source_id": "comp_rate_limiter", "target_id": "obj_concurrent_scale", "type": "motivated_by" },
    { "source_id": "comp_search_engine", "target_id": "dec_search_api", "type": "motivated_by" },
    { "source_id": "comp_synthesis_engine", "target_id": "dec_synthesis_style", "type": "motivated_by" },
    { "source_id": "comp_content_processor", "target_id": "dec_dedup_strategy", "type": "motivated_by" },
    { "source_id": "comp_search_engine", "target_id": "iface_search_result", "type": "exposes" },
    { "source_id": "comp_content_processor", "target_id": "iface_search_result", "type": "consumes" },
    { "source_id": "comp_content_processor", "target_id": "iface_source_chunk", "type": "exposes" },
    { "source_id": "comp_summarizer", "target_id": "iface_source_chunk", "type": "consumes" },
    { "source_id": "comp_summarizer", "target_id": "iface_source_summary", "type": "exposes" },
    { "source_id": "comp_conflict_detector", "target_id": "iface_source_summary", "type": "consumes" },
    { "source_id": "comp_synthesis_engine", "target_id": "iface_source_summary", "type": "consumes" },
    { "source_id": "comp_synthesis_engine", "target_id": "iface_report_schema", "type": "exposes" },
    { "source_id": "comp_citation_verifier", "target_id": "iface_report_schema", "type": "consumes" },
    { "source_id": "comp_report_renderer", "target_id": "iface_report_schema", "type": "consumes" },
    { "source_id": "comp_job_manager", "target_id": "comp_search_engine", "type": "depends_on" },
    { "source_id": "comp_search_engine", "target_id": "comp_retry_manager", "type": "depends_on" },
    { "source_id": "comp_summarizer", "target_id": "comp_retry_manager", "type": "depends_on" },
    { "source_id": "comp_synthesis_engine", "target_id": "comp_retry_manager", "type": "depends_on" },
    { "source_id": "comp_citation_verifier", "target_id": "comp_retry_manager", "type": "depends_on" },
    { "source_id": "comp_search_engine", "target_id": "comp_rate_limiter", "type": "depends_on" },
    { "source_id": "comp_summarizer", "target_id": "comp_rate_limiter", "type": "depends_on" },
    { "source_id": "comp_synthesis_engine", "target_id": "comp_rate_limiter", "type": "depends_on" },
    { "source_id": "comp_job_manager", "target_id": "comp_job_store", "type": "depends_on" },
    { "source_id": "comp_retry_manager", "target_id": "comp_job_store", "type": "depends_on" },
    { "source_id": "comp_retry_manager", "target_id": "comp_notifier", "type": "depends_on" },
    { "source_id": "comp_content_processor", "target_id": "comp_job_store", "type": "depends_on" },
    { "source_id": "risk_rate_limiting", "target_id": "dec_retry_strategy", "type": "conflicts_with" },
    { "source_id": "risk_deadletter_growth", "target_id": "dec_retry_strategy", "type": "conflicts_with" }
  ]
}
[/GRAPH UPDATE]

Phase 2 Follow-up Questions
Three gaps surfaced by the graph before I move to testing strategy and error handling:

Q1 — Conflict Detector output behaviour When the Conflict Detector flags a contradiction between two sources (e.g., Source A says "X increased by 30%", Source B says "X decreased by 12%"), what should the synthesis engine do with that? Options:

(a) Present both claims side-by-side with attribution and let the reader judge
(b) Favour the higher-relevance-scored source and footnote the dissenting one
(c) Always flag a "conflicting evidence" callout box in the report section where it appears
Q2 — Token cost ceiling (risk_api_cost, severity 0.7 — no mitigation yet) Currently each pipeline makes roughly 5–8 LLM calls (N summarizations + 1 conflict pass + 1 synthesis + 1 citation check). At 200 queries/day that's up to 1,600 Claude API calls/day with no cap. Should I design in a per-query token budget that truncates lower-relevance sources if the budget would be exceeded? Or is cost tracking/alerting sufficient without hard limits?

Q3 — Developer notification channel (comp_notifier has no channel specified) For dead-letter queue alerts, what's practical for your local setup — structured log file only, or also a lightweight push channel like a local webhook, email (SMTP), or a Slack/Discord webhook?

You said: Q1) Use option (c): always flag a "conflicting evidence" callout box in the relevant report section.
Q1) Use option (c): always flag a "conflicting evidence" callout box in the relevant report section. Also present both claims side-by-side with citations so the reader can judge.
Q2) Add a per-query token budget. If the budget is exceeded, truncate or skip lower-relevance sources first. Also include cost tracking and alerts, but do not let cost grow without limits.
Q3) For now, use structured log file only for developer notifications. Since this is a local-machine setup, logs are enough. Later, it can be extended to email or Slack webhook.

14:11
Claude responded: Phase 3 — Testing Strategy, Error Handling & Deployment

Architected Phase 3 testing, error handling, and deployment strategy framework
Architected Phase 3 testing, error handling, and deployment strategy framework
Phase 3 — Testing Strategy, Error Handling & Deployment
Locking in the three decisions:

Conflict presentation: side-by-side callout box with both citations, always
Token budget: hard per-query limit, relevance-ordered truncation, cost tracker with alert threshold
Notifications: structured log file only (extensible later)
Now adding the full testing layer, remaining error handling components, and deployment wiring.

Testing philosophy for this system:

Every external boundary (Tavily, Claude) gets a recorded fixture layer. The pipeline is designed so mocks slot in at the interface level — meaning you can run the entire pipeline end-to-end in CI with zero live calls. Test types per component:

Component	Test Type	Strategy
Content Processor	Unit	Fixture HTML inputs → assert dedup/chunk output
Retry Manager	Unit	Inject failing callables → assert backoff timing + DLQ write
Schema interfaces	Conformance	Pydantic validation against recorded API responses
Summarizer / Verifier	Unit	Frozen LLM response fixtures → assert output shape
Full pipeline	Integration	All externals mocked → assert report structure
Report Renderer	Unit	Fixed ReportSchema input → assert Markdown/PDF output
Cost Tracker	Unit	Inject token counts → assert budget enforcement
[GRAPH UPDATE]

json
{
  "nodes": [
    {
      "id": "obj_autonomous_research",
      "type": "objective",
      "label": "Fully autonomous research pipeline",
      "description": "Accept a topic, retrieve sources, synthesize findings, and emit a report without human intervention."
    },
    {
      "id": "obj_structured_output",
      "type": "objective",
      "label": "Well-formatted cited reports",
      "description": "Final output must be human-readable with clear sections, citations, and references."
    },
    {
      "id": "obj_concurrent_scale",
      "type": "objective",
      "label": "Support ~200 concurrent queries/day",
      "description": "System must handle parallel research queries on a single local machine without queue starvation or resource exhaustion."
    },
    {
      "id": "req_autonomous",
      "type": "requirement",
      "label": "Minimal human input post-start",
      "description": "Once a query is submitted, the pipeline runs to completion or structured failure with no prompts.",
      "is_functional": true
    },
    {
      "id": "req_citations",
      "type": "requirement",
      "label": "All claims must carry source citations",
      "description": "Every extracted fact or summary block in the report must link back to its source URL and retrieval timestamp.",
      "is_functional": true
    },
    {
      "id": "req_failure_handling",
      "type": "requirement",
      "label": "Graceful degradation on partial failures",
      "description": "API errors, missing sources, or scraping failures must not abort the full pipeline — partial results are valid output.",
      "is_functional": true
    },
    {
      "id": "req_dedup",
      "type": "requirement",
      "label": "Deduplicate and reconcile conflicting sources",
      "description": "Duplicate content across sources must be collapsed; conflicting claims must be flagged, not silently merged.",
      "is_functional": true
    },
    {
      "id": "req_offline_tests",
      "type": "requirement",
      "label": "Test suite must not require live API calls",
      "description": "All tests must be runnable offline using fixtures, mocks, and recorded responses.",
      "is_functional": false
    },
    {
      "id": "dec_search_api",
      "type": "decision",
      "label": "Use Tavily as the search and retrieval API",
      "description": "Tavily is selected as the primary web search provider, returning full cleaned page content per result.",
      "rationale": "Purpose-built for AI agent pipelines — returns full page text, includes relevance scoring, eliminates a separate scraping layer. Python SDK integrates cleanly with asyncio.",
      "alternatives_considered": ["Serper (snippets only, requires scraping layer)", "Bing Search API (snippet-based, higher per-call cost)", "Google Custom Search API (quota limits, snippet-only on free tier)", "SerpAPI (costly at scale)"]
    },
    {
      "id": "dec_llm",
      "type": "decision",
      "label": "Use Claude (Anthropic API) for summarization and synthesis",
      "description": "Claude is the LLM backbone for per-source summarization, conflict detection, and final synthesis.",
      "rationale": "Large context window handles multi-source synthesis in a single pass. Structured output via tool use enables reliable JSON for citation tracking. Strong instruction-following for report formatting.",
      "alternatives_considered": ["OpenAI GPT-4o (comparable capability, different pricing)", "Ollama local models (no API cost, slower on CPU, weaker synthesis quality)", "Gemini 1.5 Pro (large context, less mature tooling ecosystem)"]
    },
    {
      "id": "dec_orchestration",
      "type": "decision",
      "label": "Custom async Python pipeline (asyncio)",
      "description": "The pipeline is a hand-rolled async DAG in Python rather than a framework like LangGraph or Prefect.",
      "rationale": "Fixed, well-defined stage sequence. Custom DAG gives full control over error boundaries, retry logic, and semaphore-based concurrency without framework overhead.",
      "alternatives_considered": ["LangChain/LangGraph (abstraction overhead, harder to debug)", "Prefect/Dagster (suited for ETL, not interactive agent pipelines)", "Celery + Redis (requires Redis server, adds infra complexity on local machine)"]
    },
    {
      "id": "dec_storage",
      "type": "decision",
      "label": "SQLite for job state, filesystem for artifacts",
      "description": "SQLite tracks job metadata, source hashes for dedup, dead-letter entries, and cost records. Raw content and final reports live as files on disk.",
      "rationale": "No server to manage. SQLite is sufficient for 200 jobs/day on a single machine. File-per-artifact is simple and inspectable.",
      "alternatives_considered": ["PostgreSQL (server overhead, unnecessary for local)", "DuckDB (good for analytics, less suited for transactional job state)", "Pure filesystem JSON sidecars (loses queryability for dedup lookups)"]
    },
    {
      "id": "dec_concurrency",
      "type": "decision",
      "label": "asyncio with bounded semaphore and per-API token buckets",
      "description": "Concurrent queries managed via an asyncio semaphore (pipeline-level cap) plus per-API token bucket rate limiters for Tavily and Claude independently.",
      "rationale": "200/day with burst concurrency. Semaphore cap (5–10 concurrent) prevents memory exhaustion. Separate token buckets per API prevent one API's rate limit from starving the other.",
      "alternatives_considered": ["multiprocessing (CPU-bound; this pipeline is I/O-bound)", "ThreadPoolExecutor (GIL limits parallelism)", "Ray (overkill for single-machine target)"]
    },
    {
      "id": "dec_output",
      "type": "decision",
      "label": "Markdown primary output, PDF via WeasyPrint",
      "description": "Markdown is the canonical report artifact; PDF is derived from it via WeasyPrint.",
      "rationale": "Markdown is version-controllable and diff-able. WeasyPrint converts HTML/CSS to PDF without requiring LaTeX or headless Chrome.",
      "alternatives_considered": ["LaTeX (high-quality PDF but heavy dependency)", "ReportLab (verbose, poor for narrative text)", "Pandoc (excellent but adds a system binary dependency)"]
    },
    {
      "id": "dec_retry_strategy",
      "type": "decision",
      "label": "Exponential backoff × 4, then dead-letter queue + structured log alert",
      "description": "All external API calls retry with 1s/2s/4s/8s backoff. On 4th failure the job enters dead_letter_queue in SQLite and a structured log entry is written at ERROR level.",
      "rationale": "Transient errors (429, 503) are common in API-heavy pipelines. Four attempts covers most transient spikes. Dead-letter queue ensures no silent data loss and allows manual replay. Structured log is sufficient for local-machine developer response.",
      "alternatives_considered": ["Fail fast with no retry (too fragile)", "Infinite retry (risks live-lock under sustained outage)", "Push notification channel (over-engineered for local setup; extensible later)"]
    },
    {
      "id": "dec_synthesis_style",
      "type": "decision",
      "label": "Fluent narrative synthesis with post-hoc citation verification",
      "description": "Claude generates a flowing narrative report, then a second LLM pass checks each paragraph for citation coverage and flags or injects missing references.",
      "rationale": "Fluent narrative is more readable for human consumers. Post-hoc verification catches most attribution gaps without forcing a mechanical citation-per-sentence constraint during generation.",
      "alternatives_considered": ["Strictly grounded synthesis (more reliable but mechanical prose)", "No verification pass (faster but risks unchecked hallucination drift)"]
    },
    {
      "id": "dec_dedup_strategy",
      "type": "decision",
      "label": "Shallow deduplication via URL normalisation + SHA-256 content hash",
      "description": "Sources deduplicated by normalised URL and SHA-256 hash of full text. Matches on either key collapse to the first-seen copy.",
      "rationale": "Fast, zero extra API cost, no additional model dependency. Catches syndicated articles (same URL), mirror sites (same hash, different URL), and cached pages.",
      "alternatives_considered": ["Semantic embedding similarity (catches paraphrased duplicates but adds model dependency and latency)", "Title similarity only (too coarse)"]
    },
    {
      "id": "dec_conflict_presentation",
      "type": "decision",
      "label": "Conflicting claims get a side-by-side callout box in the report",
      "description": "When the Conflict Detector flags a contradiction, the Synthesis Engine always renders a visually distinct callout block presenting both claims with their citations, letting the reader judge.",
      "rationale": "Presenting both claims preserves epistemic honesty. A callout box makes conflicts visually salient rather than burying them in prose. Neither source is silently discarded.",
      "alternatives_considered": ["Favour higher-relevance source and footnote dissent (suppresses information)", "Merge claims silently (misleading and unreliable)"]
    },
    {
      "id": "dec_token_budget",
      "type": "decision",
      "label": "Per-query token budget with relevance-ordered truncation and cost alerts",
      "description": "Each query has a configurable max token budget. Before summarization, sources are sorted by Tavily relevance score; lower-relevance sources are truncated or skipped if the budget would be exceeded. Cumulative daily cost is tracked in SQLite and an alert threshold triggers a log WARNING.",
      "rationale": "Prevents unbounded cost growth at 200 queries/day. Relevance-ordered truncation maximises information quality per token spent. Soft alert (not hard kill) at a daily threshold allows the operator to tune limits without breaking running jobs.",
      "alternatives_considered": ["Cost tracking only without hard limits (risk of runaway spend)", "Uniform truncation of all sources equally (wastes budget on low-relevance content)", "No token management (acceptable for low volume, not for 200/day)"]
    },
    {
      "id": "dec_notification_channel",
      "type": "decision",
      "label": "Structured log file as sole developer notification channel",
      "description": "Dead-letter events, cost threshold alerts, and pipeline errors are written as structured JSON log entries (via Python structlog) to a rotating log file.",
      "rationale": "Sufficient for a local-machine setup where the developer can tail the log. Structlog's JSON output is machine-parseable for future integration with log shippers or alerting tools.",
      "alternatives_considered": ["Email via SMTP (extensible future option, not needed now)", "Slack/Discord webhook (extensible future option, not needed now)", "Plain print/stderr (not machine-parseable, harder to query)"]
    },
    {
      "id": "dec_config_management",
      "type": "decision",
      "label": "YAML config file with environment variable overrides",
      "description": "All pipeline parameters (semaphore size, token budgets, cost alert threshold, log path, API keys) live in a config.yaml. Environment variables override individual keys for CI and secrets management.",
      "rationale": "YAML config is human-readable and version-controllable (with secrets excluded via .gitignore). Env var override is the standard pattern for CI and containerised execution without modifying config files.",
      "alternatives_considered": ["Env vars only (no single source of truth for non-secret config)", "Hardcoded defaults (not operator-tunable without code changes)", "Pydantic Settings only (good but requires understanding Python to configure)"]
    },
    {
      "id": "comp_job_manager",
      "type": "component",
      "label": "Job Manager",
      "description": "Accepts research query input via CLI or programmatic API, creates a job record in SQLite, acquires a semaphore slot, and dispatches the pipeline DAG. Tracks job lifecycle: queued → running → complete → failed.",
      "has_tests": false
    },
    {
      "id": "comp_search_engine",
      "type": "component",
      "label": "Search & Retrieval Engine",
      "description": "Calls Tavily API with the research topic, retrieves N results with full page content, and returns a list of raw SearchResult objects. Wrapped by Retry Manager and Rate Limiter.",
      "has_tests": false
    },
    {
      "id": "comp_content_processor",
      "type": "component",
      "label": "Content Processor",
      "description": "Deduplicates results by URL normalisation and SHA-256 hash, strips boilerplate, and chunks content into token-bounded segments. Applies token budget ordering (highest relevance first).",
      "has_tests": false
    },
    {
      "id": "comp_summarizer",
      "type": "component",
      "label": "Per-Source Summarizer",
      "description": "Calls Claude once per deduplicated source chunk to produce a structured SourceSummary with inline attribution tags. Runs concurrently across sources within the token budget.",
      "has_tests": false
    },
    {
      "id": "comp_conflict_detector",
      "type": "component",
      "label": "Conflict Detector",
      "description": "Scans the set of SourceSummary objects for contradictory claims on the same subject. Emits ConflictFlag records with both source references, confidence score, and the verbatim conflicting claims.",
      "has_tests": false
    },
    {
      "id": "comp_synthesis_engine",
      "type": "component",
      "label": "Synthesis Engine",
      "description": "Calls Claude with all source summaries, conflict flags, and a structured report template. Renders a fluent narrative draft with conflict callout boxes wherever ConflictFlags exist.",
      "has_tests": false
    },
    {
      "id": "comp_citation_verifier",
      "type": "component",
      "label": "Citation Verifier",
      "description": "Runs a second LLM pass over the synthesized report. For each paragraph, checks citation presence and groundedness against source summaries. Flags or auto-injects missing references.",
      "has_tests": false
    },
    {
      "id": "comp_report_renderer",
      "type": "component",
      "label": "Report Renderer",
      "description": "Transforms the verified ReportSchema into structured Markdown with a full references section, then renders a PDF via WeasyPrint using a CSS template.",
      "has_tests": false
    },
    {
      "id": "comp_retry_manager",
      "type": "component",
      "label": "Retry Manager",
      "description": "Decorator/wrapper applied to all external API calls. Implements exponential backoff (1s/2s/4s/8s × 4 attempts). On exhaustion, writes to dead_letter_queue in SQLite and triggers the Notifier.",
      "has_tests": false
    },
    {
      "id": "comp_rate_limiter",
      "type": "component",
      "label": "Rate Limiter",
      "description": "Maintains a global asyncio semaphore for pipeline-level concurrency and independent per-API token buckets for Tavily and Claude.",
      "has_tests": false
    },
    {
      "id": "comp_token_budget_manager",
      "type": "component",
      "label": "Token Budget Manager",
      "description": "Enforces per-query token budgets by ordering sources by relevance score and truncating or skipping lower-relevance sources when the budget would be exceeded. Tracks per-call token usage.",
      "has_tests": false
    },
    {
      "id": "comp_cost_tracker",
      "type": "component",
      "label": "Cost Tracker",
      "description": "Accumulates token usage and estimated API cost per job in SQLite. Compares running daily total against a configurable alert threshold and logs a structured WARNING when exceeded.",
      "has_tests": false
    },
    {
      "id": "comp_job_store",
      "type": "component",
      "label": "Job Store (SQLite via SQLAlchemy async)",
      "description": "Persists job records, source content hashes for dedup, dead-letter queue entries, cost records, and run history. Accessed via SQLAlchemy async session.",
      "has_tests": false
    },
    {
      "id": "comp_notifier",
      "type": "component",
      "label": "Developer Notifier",
      "description": "Writes structured JSON log entries via structlog for dead-letter events, cost threshold breaches, and pipeline errors. Outputs to a rotating log file. Designed for future extension to email/webhook.",
      "has_tests": false
    },
    {
      "id": "comp_config_manager",
      "type": "component",
      "label": "Config Manager",
      "description": "Loads config.yaml at startup and merges environment variable overrides. Exposes a typed Settings object (via Pydantic) consumed by all components.",
      "has_tests": false
    },
    {
      "id": "iface_search_result",
      "type": "interface",
      "label": "SearchResult schema",
      "description": "Normalised output contract from the Search Engine.",
      "contract": "{ url: str, title: str, raw_content: str, relevance_score: float, retrieved_at: datetime }"
    },
    {
      "id": "iface_source_chunk",
      "type": "interface",
      "label": "SourceChunk schema",
      "description": "Token-bounded content unit output by the Content Processor, ready for LLM ingestion.",
      "contract": "{ chunk_id: str, url: str, content_hash: str, text: str, token_count: int, chunk_index: int, relevance_score: float }"
    },
    {
      "id": "iface_source_summary",
      "type": "interface",
      "label": "SourceSummary schema",
      "description": "Structured per-source summary with attribution, output by the Summarizer.",
      "contract": "{ summary_id: str, url: str, title: str, key_points: list[str], conflicts: list[str], token_cost: int, retrieved_at: datetime }"
    },
    {
      "id": "iface_conflict_flag",
      "type": "interface",
      "label": "ConflictFlag schema",
      "description": "Conflict record emitted by Conflict Detector and consumed by the Synthesis Engine.",
      "contract": "{ conflict_id: str, claim_a: str, source_a_url: str, claim_b: str, source_b_url: str, confidence: float, subject: str }"
    },
    {
      "id": "iface_report_schema",
      "type": "interface",
      "label": "Final Report schema",
      "description": "Structured report contract passed from Synthesis Engine through Citation Verifier to Report Renderer.",
      "contract": "{ title: str, executive_summary: str, sections: list[{heading, body, citations, conflict_callouts}], references: list[{id, url, title, retrieved_at}], quality_flags: list[str] }"
    },
    {
      "id": "tst_content_processor",
      "type": "test",
      "label": "Content Processor dedup and chunking unit tests",
      "description": "Loads fixture HTML and raw text inputs. Asserts correct URL normalisation, SHA-256 deduplication, boilerplate stripping, and token-bounded chunk output.",
      "test_type": "unit",
      "status": "planned"
    },
    {
      "id": "tst_retry_manager",
      "type": "test",
      "label": "Retry Manager backoff and DLQ unit tests",
      "description": "Injects callables that fail N times then succeed (or always fail). Asserts correct backoff timing, attempt count, dead-letter queue write, and notifier trigger on exhaustion.",
      "test_type": "unit",
      "status": "planned"
    },
    {
      "id": "tst_schema_conformance",
      "type": "test",
      "label": "Interface schema conformance tests",
      "description": "Validates recorded Tavily and Claude API responses against Pydantic models for all four interface schemas. Ensures schema contracts hold against real API response shapes.",
      "test_type": "conformance",
      "status": "planned"
    },
    {
      "id": "tst_summarizer",
      "type": "test",
      "label": "Summarizer unit tests with frozen LLM fixtures",
      "description": "Feeds frozen Claude response fixtures into the Summarizer. Asserts correct SourceSummary shape, attribution presence, and token cost recording.",
      "test_type": "unit",
      "status": "planned"
    },
    {
      "id": "tst_citation_verifier",
      "type": "test",
      "label": "Citation Verifier unit tests",
      "description": "Provides a ReportSchema with known uncited paragraphs and frozen LLM verification responses. Asserts correct flag injection and reference resolution.",
      "test_type": "unit",
      "status": "planned"
    },
    {
      "id": "tst_pipeline_integration",
      "type": "test",
      "label": "Full pipeline integration test (all externals mocked)",
      "description": "Runs the complete pipeline from Job Manager to Report Renderer with all Tavily and Claude calls replaced by recorded fixture responses. Asserts final report structure, citation presence, and conflict callout rendering.",
      "test_type": "integration",
      "status": "planned"
    },
    {
      "id": "tst_token_budget",
      "type": "test",
      "label": "Token Budget Manager enforcement unit tests",
      "description": "Injects a set of sources exceeding the budget limit. Asserts that lower-relevance sources are truncated first, budget is never exceeded, and cost tracker receives correct token counts.",
      "test_type": "unit",
      "status": "planned"
    },
    {
      "id": "tst_report_renderer",
      "type": "test",
      "label": "Report Renderer output tests",
      "description": "Feeds a fixed ReportSchema with known sections, citations, and conflict callouts. Asserts Markdown structure (headings, callout blocks, references section) and that PDF generation completes without error.",
      "test_type": "unit",
      "status": "planned"
    },
    {
      "id": "asm_tavily_rate_limits",
      "type": "assumption",
      "label": "Tavily API rate limits accommodate burst concurrency",
      "description": "Assumes Tavily's plan tier allows enough requests/minute to serve 10 concurrent pipelines each making 3–5 search calls without throttling.",
      "confidence": 0.6,
      "validated": false
    },
    {
      "id": "asm_context_window",
      "type": "assumption",
      "label": "Multi-source summaries fit Claude's context window for synthesis",
      "description": "Assumes combined SourceSummary objects for a single topic fit within Claude's context window after per-source summarization reduces raw content volume.",
      "confidence": 0.8,
      "validated": false
    },
    {
      "id": "asm_local_resources",
      "type": "assumption",
      "label": "Local machine sustains 5–10 concurrent async pipelines",
      "description": "Assumes enough RAM and network bandwidth for concurrent Tavily fetches and LLM calls without thrashing.",
      "confidence": 0.7,
      "validated": false
    },
    {
      "id": "asm_tavily_content_quality",
      "type": "assumption",
      "label": "Tavily returns substantive full-page content reliably",
      "description": "Assumes Tavily successfully extracts readable text from the majority of retrieved URLs vs. returning empty or JS-only shells.",
      "confidence": 0.65,
      "validated": false
    },
    {
      "id": "asm_posthoc_citation_sufficient",
      "type": "assumption",
      "label": "Post-hoc citation pass catches most attribution gaps",
      "description": "Assumes a second LLM verification pass is sufficient to catch uncited claims in the fluent narrative.",
      "confidence": 0.65,
      "validated": false
    },
    {
      "id": "asm_structlog_sufficient",
      "type": "assumption",
      "label": "Structured log file is sufficient for developer incident response",
      "description": "Assumes the developer monitors log output during pipeline operation and can respond to dead-letter or cost-alert entries without push notifications.",
      "confidence": 0.8,
      "validated": false
    },
    {
      "id": "risk_api_cost",
      "type": "risk",
      "label": "LLM + search API costs escalate at scale",
      "description": "At 200 queries/day with multiple LLM calls per pipeline stage, token costs could become significant without a cost ceiling.",
      "severity": 0.7
    },
    {
      "id": "risk_rate_limiting",
      "type": "risk",
      "label": "API rate limits throttle or fail concurrent pipelines",
      "description": "Bursts of concurrent queries may exhaust Tavily or Claude API rate limits, causing cascading failures across multiple pipelines.",
      "severity": 0.8
    },
    {
      "id": "risk_hallucination",
      "type": "risk",
      "label": "LLM hallucination survives post-hoc citation check",
      "description": "Fluent narrative generation may introduce plausible-sounding but unsourced claims that the citation verifier fails to catch.",
      "severity": 0.7
    },
    {
      "id": "risk_content_quality",
      "type": "risk",
      "label": "Poor or paywalled source content degrades report quality",
      "description": "Many high-quality sources are paywalled or return minimal content, reducing synthesis quality silently.",
      "severity": 0.65
    },
    {
      "id": "risk_dedup_false_negative",
      "type": "risk",
      "label": "Semantic duplicates pass hash-based deduplication",
      "description": "Two sources reporting the same fact in different words pass URL/hash dedup and are treated as independent corroboration.",
      "severity": 0.6
    },
    {
      "id": "risk_deadletter_growth",
      "type": "risk",
      "label": "Dead-letter queue grows unbounded without manual replay",
      "description": "A systemic API outage may accumulate hundreds of DLQ entries with no automated replay mechanism.",
      "severity": 0.55
    },
    {
      "id": "risk_low_source_coverage",
      "type": "risk",
      "label": "Too few usable sources yield a low-confidence report",
      "description": "If paywalls or Tavily extraction failures reduce usable sources below a meaningful threshold, the synthesized report may be thin but not visibly flagged as low-confidence.",
      "severity": 0.65
    }
  ],
  "edges": [
    { "source_id": "dec_search_api", "target_id": "obj_autonomous_research", "type": "motivated_by" },
    { "source_id": "dec_llm", "target_id": "obj_structured_output", "type": "motivated_by" },
    { "source_id": "dec_concurrency", "target_id": "obj_concurrent_scale", "type": "motivated_by" },
    { "source_id": "dec_orchestration", "target_id": "obj_autonomous_research", "type": "motivated_by" },
    { "source_id": "dec_output", "target_id": "obj_structured_output", "type": "motivated_by" },
    { "source_id": "dec_retry_strategy", "target_id": "req_failure_handling", "type": "motivated_by" },
    { "source_id": "dec_dedup_strategy", "target_id": "req_dedup", "type": "motivated_by" },
    { "source_id": "dec_synthesis_style", "target_id": "obj_structured_output", "type": "motivated_by" },
    { "source_id": "dec_conflict_presentation", "target_id": "req_dedup", "type": "motivated_by" },
    { "source_id": "dec_token_budget", "target_id": "obj_concurrent_scale", "type": "motivated_by" },
    { "source_id": "dec_search_api", "target_id": "asm_tavily_rate_limits", "type": "assumes" },
    { "source_id": "dec_search_api", "target_id": "asm_tavily_content_quality", "type": "assumes" },
    { "source_id": "dec_llm", "target_id": "asm_context_window", "type": "assumes" },
    { "source_id": "dec_concurrency", "target_id": "asm_local_resources", "type": "assumes" },
    { "source_id": "dec_synthesis_style", "target_id": "asm_posthoc_citation_sufficient", "type": "assumes" },
    { "source_id": "dec_notification_channel", "target_id": "asm_structlog_sufficient", "type": "assumes" },
    { "source_id": "risk_rate_limiting", "target_id": "dec_concurrency", "type": "conflicts_with" },
    { "source_id": "risk_rate_limiting", "target_id": "asm_tavily_rate_limits", "type": "invalidates" },
    { "source_id": "risk_hallucination", "target_id": "req_citations", "type": "conflicts_with" },
    { "source_id": "risk_hallucination", "target_id": "asm_posthoc_citation_sufficient", "type": "invalidates" },
    { "source_id": "risk_content_quality", "target_id": "asm_tavily_content_quality", "type": "invalidates" },
    { "source_id": "risk_api_cost", "target_id": "dec_llm", "type": "conflicts_with" },
    { "source_id": "risk_dedup_false_negative", "target_id": "req_dedup", "type": "conflicts_with" },
    { "source_id": "risk_low_source_coverage", "target_id": "asm_tavily_content_quality", "type": "invalidates" },
    { "source_id": "risk_deadletter_growth", "target_id": "dec_retry_strategy", "type": "conflicts_with" },
    { "source_id": "comp_job_manager", "target_id": "req_autonomous", "type": "implements" },
    { "source_id": "comp_content_processor", "target_id": "req_dedup", "type": "implements" },
    { "source_id": "comp_citation_verifier", "target_id": "req_citations", "type": "implements" },
    { "source_id": "comp_retry_manager", "target_id": "req_failure_handling", "type": "implements" },
    { "source_id": "comp_token_budget_manager", "target_id": "dec_token_budget", "type": "motivated_by" },
    { "source_id": "comp_cost_tracker", "target_id": "dec_token_budget", "type": "motivated_by" },
    { "source_id": "comp_notifier", "target_id": "dec_notification_channel", "type": "motivated_by" },
    { "source_id": "comp_config_manager", "target_id": "dec_config_management", "type": "motivated_by" },
    { "source_id": "comp_conflict_detector", "target_id": "dec_conflict_presentation", "type": "motivated_by" },
    { "source_id": "comp_rate_limiter", "target_id": "obj_concurrent_scale", "type": "motivated_by" },
    { "source_id": "comp_search_engine", "target_id": "dec_search_api", "type": "motivated_by" },
    { "source_id": "comp_synthesis_engine", "target_id": "dec_synthesis_style", "type": "motivated_by" },
    { "source_id": "comp_content_processor", "target_id": "dec_dedup_strategy", "type": "motivated_by" },
    { "source_id": "comp_search_engine", "target_id": "iface_search_result", "type": "exposes" },
    { "source_id": "comp_content_processor", "target_id": "iface_search_result", "type": "consumes" },
    { "source_id": "comp_content_processor", "target_id": "iface_source_chunk", "type": "exposes" },
    { "source_id": "comp_summarizer", "target_id": "iface_source_chunk", "type": "consumes" },
    { "source_id": "comp_summarizer", "target_id": "iface_source_summary", "type": "exposes" },
    { "source_id": "comp_conflict_detector", "target_id": "iface_source_summary", "type": "consumes" },
    { "source_id": "comp_conflict_detector", "target_id": "iface_conflict_flag", "type": "exposes" },
    { "source_id": "comp_synthesis_engine", "target_id": "iface_source_summary", "type": "consumes" },
    { "source_id": "comp_synthesis_engine", "target_id": "iface_conflict_flag", "type": "consumes" },
    { "source_id": "comp_synthesis_engine", "target_id": "iface_report_schema", "type": "exposes" },
    { "source_id": "comp_citation_verifier", "target_id": "iface_report_schema", "type": "consumes" },
    { "source_id": "comp_report_renderer", "target_id": "iface_report_schema", "type": "consumes" },
    { "source_id": "comp_job_manager", "target_id": "comp_search_engine", "type": "depends_on" },
    { "source_id": "comp_search_engine", "target_id": "comp_retry_manager", "type": "depends_on" },
    { "source_id": "comp_summarizer", "target_id": "comp_retry_manager", "type": "depends_on" },
    { "source_id": "comp_synthesis_engine", "target_id": "comp_retry_manager", "type": "depends_on" },
    { "source_id": "comp_citation_verifier", "target_id": "comp_retry_manager", "type": "depends_on" },
    { "source_id": "comp_search_engine", "target_id": "comp_rate_limiter", "type": "depends_on" },
    { "source_id": "comp_summarizer", "target_id": "comp_rate_limiter", "type": "depends_on" },
    { "source_id": "comp_synthesis_engine", "target_id": "comp_rate_limiter", "type": "depends_on" },
    { "source_id": "comp_summarizer", "target_id": "comp_token_budget_manager", "type": "depends_on" },
    { "source_id": "comp_content_processor", "target_id": "comp_token_budget_manager", "type": "depends_on" },
    { "source_id": "comp_token_budget_manager", "target_id": "comp_cost_tracker", "type": "depends_on" },
    { "source_id": "comp_cost_tracker", "target_id": "comp_job_store", "type": "depends_on" },
    { "source_id": "comp_cost_tracker", "target_id": "comp_notifier", "type": "depends_on" },
    { "source_id": "comp_job_manager", "target_id": "comp_job_store", "type": "depends_on" },
    { "source_id": "comp_retry_manager", "target_id": "comp_job_store", "type": "depends_on" },
    { "source_id": "comp_retry_manager", "target_id": "comp_notifier", "type": "depends_on" },
    { "source_id": "comp_content_processor", "target_id": "comp_job_store", "type": "depends_on" },
    { "source_id": "comp_job_manager", "target_id": "comp_config_manager", "type": "depends_on" },
    { "source_id": "comp_rate_limiter", "target_id": "comp_config_manager", "type": "depends_on" },
    { "source_id": "comp_token_budget_manager", "target_id": "comp_config_manager", "type": "depends_on" },
    { "source_id": "tst_content_processor", "target_id": "comp_content_processor", "type": "verifies" },
    { "source_id": "tst_retry_manager", "target_id": "comp_retry_manager", "type": "verifies" },
    { "source_id": "tst_retry_manager", "target_id": "risk_rate_limiting", "type": "guards_against" },
    { "source_id": "tst_retry_manager", "target_id": "risk_deadletter_growth", "type": "guards_against" },
    { "source_id": "tst_schema_conformance", "target_id": "iface_search_result", "type": "verifies" },
    { "source_id": "tst_schema_conformance", "target_id": "iface_source_summary", "type": "verifies" },
    { "source_id": "tst_schema_conformance", "target_id": "iface_conflict_flag", "type": "verifies" },
    { "source_id": "tst_schema_conformance", "target_id": "iface_report_schema", "type": "verifies" },
    { "source_id": "tst_summarizer", "target_id": "comp_summarizer", "type": "verifies" },
    { "source_id": "tst_citation_verifier", "target_id": "comp_citation_verifier", "type": "verifies" },
    { "source_id": "tst_citation_verifier", "target_id": "risk_hallucination", "type": "guards_against" },
    { "source_id": "tst_pipeline_integration", "target_id": "comp_job_manager", "type": "verifies" },
    { "source_id": "tst_pipeline_integration", "target_id": "dec_orchestration", "type": "validates" },
    { "source_id": "tst_token_budget", "target_id": "comp_token_budget_manager", "type": "verifies" },
    { "source_id": "tst_token_budget", "target_id": "risk_api_cost", "type": "guards_against" },
    { "source_id": "tst_report_renderer", "target_id": "comp_report_renderer", "type": "verifies" },
    { "source_id": "tst_report_renderer", "target_id": "dec_output", "type": "validates" }
  ]
}
[/GRAPH UPDATE]

Phase 3 Follow-up Questions
Three final gaps before writing the implementation plan:

Q1 — Minimum viable source threshold (risk_low_source_coverage, severity 0.65 — no guard yet)** If after deduplication and paywall filtering fewer than N usable sources remain, the report will be thin. Should the pipeline: (a) proceed and embed a quality_flags warning in the report header (e.g., "Low confidence — only 2 sources available"), or (b) abort the job with a structured error so the caller knows the query produced insufficient coverage?

Q2 — Artifact retention policy Completed reports, source chunk files, and raw Tavily content accumulate on disk. For 200 queries/day that's non-trivial volume. Should I design in (a) a configurable TTL (e.g., auto-delete artifacts older than 7 days, keep SQLite records), (b) keep everything indefinitely and document manual cleanup, or (c) keep only the final Markdown/PDF and discard intermediate artifacts after job completion?

Q3 — CLI interface shape The Job Manager needs an entry point. Which fits your workflow best:

(a) Single-query CLI: python -m researcher "impact of AI on healthcare"
(b) Batch file CLI: python -m researcher --batch queries.txt (one query per line, runs all concurrently up to semaphore limit)
(c) Both — single and batch modes
You said: Q1) Use option (a): proceed with the report, but include quality_flags in the report header.
Q1) Use option (a): proceed with the report, but include quality_flags in the report header. If fewer than 3 usable sources remain, mark the report as low confidence and clearly mention the source coverage limitation.
Q2) Use option (a): configurable TTL. Keep final Markdown/PDF reports longer, but auto-delete raw Tavily content and intermediate chunks after 7 days. Keep SQLite metadata for run history and debugging.
Q3) Use option (c): support both single-query CLI and batch file CLI. Single-query mode is useful for quick testing, while batch mode supports the 200-queries/day scalability requirement.

15:24
Claude responded: The graph is complete.

Finalized implementation strategy incorporating user decisions and quality parameters
Finalized implementation strategy incorporating user decisions and quality parameters
The graph is complete. All decisions have rationale and alternatives, every high-severity risk has at least one guard, and all major components have planned tests. Let me lock in the final three answers, do one last graph update, then write the full implementation plan.

Locked in:

Source threshold: Proceed with report, embed quality_flags warning if < 3 usable sources
Artifact TTL: Configurable TTL — raw/intermediate files purged after 7 days, final reports kept longer, SQLite metadata kept indefinitely
CLI: Both single-query and batch modes
[GRAPH UPDATE]

json
{
  "nodes": [
    { "id": "obj_autonomous_research", "type": "objective", "label": "Fully autonomous research pipeline", "description": "Accept a topic, retrieve sources, synthesize findings, and emit a report without human intervention." },
    { "id": "obj_structured_output", "type": "objective", "label": "Well-formatted cited reports", "description": "Final output must be human-readable with clear sections, citations, and references." },
    { "id": "obj_concurrent_scale", "type": "objective", "label": "Support ~200 concurrent queries/day", "description": "System must handle parallel research queries on a single local machine without queue starvation or resource exhaustion." },
    { "id": "req_autonomous", "type": "requirement", "label": "Minimal human input post-start", "description": "Once a query is submitted, the pipeline runs to completion or structured failure with no prompts.", "is_functional": true },
    { "id": "req_citations", "type": "requirement", "label": "All claims must carry source citations", "description": "Every extracted fact or summary block in the report must link back to its source URL and retrieval timestamp.", "is_functional": true },
    { "id": "req_failure_handling", "type": "requirement", "label": "Graceful degradation on partial failures", "description": "API errors, missing sources, or scraping failures must not abort the full pipeline — partial results are valid output.", "is_functional": true },
    { "id": "req_dedup", "type": "requirement", "label": "Deduplicate and reconcile conflicting sources", "description": "Duplicate content across sources must be collapsed; conflicting claims must be flagged, not silently merged.", "is_functional": true },
    { "id": "req_offline_tests", "type": "requirement", "label": "Test suite must not require live API calls", "description": "All tests must be runnable offline using fixtures, mocks, and recorded responses.", "is_functional": false },
    { "id": "dec_search_api", "type": "decision", "label": "Use Tavily as the search and retrieval API", "description": "Tavily selected as the primary web search provider, returning full cleaned page content per result.", "rationale": "Purpose-built for AI agent pipelines — returns full page text, includes relevance scoring, eliminates a separate scraping layer. Python SDK integrates cleanly with asyncio.", "alternatives_considered": ["Serper (snippets only, requires scraping layer)", "Bing Search API (snippet-based, higher per-call cost)", "Google Custom Search API (quota limits, snippet-only on free tier)", "SerpAPI (costly at scale)"] },
    { "id": "dec_llm", "type": "decision", "label": "Use Claude (Anthropic API) for summarization and synthesis", "description": "Claude is the LLM backbone for per-source summarization, conflict detection, and final synthesis.", "rationale": "Large context window handles multi-source synthesis in a single pass. Structured output via tool use enables reliable JSON for citation tracking. Strong instruction-following for report formatting.", "alternatives_considered": ["OpenAI GPT-4o (comparable capability, different pricing)", "Ollama local models (no API cost, slower on CPU, weaker synthesis quality)", "Gemini 1.5 Pro (large context, less mature tooling ecosystem)"] },
    { "id": "dec_orchestration", "type": "decision", "label": "Custom async Python pipeline (asyncio)", "description": "The pipeline is a hand-rolled async DAG in Python rather than a framework like LangGraph or Prefect.", "rationale": "Fixed, well-defined stage sequence. Custom DAG gives full control over error boundaries, retry logic, and semaphore-based concurrency without framework overhead.", "alternatives_considered": ["LangChain/LangGraph (abstraction overhead, harder to debug)", "Prefect/Dagster (suited for ETL, not interactive agent pipelines)", "Celery + Redis (requires Redis server, adds infra complexity on local machine)"] },
    { "id": "dec_storage", "type": "decision", "label": "SQLite for job state, filesystem for artifacts", "description": "SQLite tracks job metadata, source hashes for dedup, dead-letter entries, and cost records. Raw content and final reports live as files on disk.", "rationale": "No server to manage. SQLite is sufficient for 200 jobs/day on a single machine. File-per-artifact is simple and inspectable.", "alternatives_considered": ["PostgreSQL (server overhead, unnecessary for local)", "DuckDB (good for analytics, less suited for transactional job state)", "Pure filesystem JSON sidecars (loses queryability for dedup lookups)"] },
    { "id": "dec_concurrency", "type": "decision", "label": "asyncio with bounded semaphore and per-API token buckets", "description": "Concurrent queries managed via asyncio semaphore (pipeline-level cap) plus per-API token bucket rate limiters for Tavily and Claude independently.", "rationale": "200/day with burst concurrency. Semaphore cap prevents memory exhaustion. Separate token buckets per API prevent one API's rate limit from starving the other.", "alternatives_considered": ["multiprocessing (CPU-bound; this pipeline is I/O-bound)", "ThreadPoolExecutor (GIL limits parallelism)", "Ray (overkill for single-machine target)"] },
    { "id": "dec_output", "type": "decision", "label": "Markdown primary output, PDF via WeasyPrint", "description": "Markdown is the canonical report artifact; PDF is derived via WeasyPrint.", "rationale": "Markdown is version-controllable and diff-able. WeasyPrint converts HTML/CSS to PDF without requiring LaTeX or headless Chrome.", "alternatives_considered": ["LaTeX (high-quality PDF but heavy dependency)", "ReportLab (verbose, poor for narrative text)", "Pandoc (excellent but adds a system binary dependency)"] },
    { "id": "dec_retry_strategy", "type": "decision", "label": "Exponential backoff × 4, then dead-letter queue + structured log alert", "description": "All external API calls retry with 1s/2s/4s/8s backoff. On 4th failure the job enters dead_letter_queue in SQLite and a structured log entry is written at ERROR level.", "rationale": "Transient errors (429, 503) are common in API-heavy pipelines. Four attempts covers most transient spikes. Dead-letter queue ensures no silent data loss. Structured log is sufficient for local-machine developer response.", "alternatives_considered": ["Fail fast with no retry (too fragile)", "Infinite retry (risks live-lock under sustained outage)", "Push notification channel (over-engineered for local setup; extensible later)"] },
    { "id": "dec_synthesis_style", "type": "decision", "label": "Fluent narrative synthesis with post-hoc citation verification", "description": "Claude generates a flowing narrative report, then a second LLM pass checks each paragraph for citation coverage and flags or injects missing references.", "rationale": "Fluent narrative is more readable for human consumers. Post-hoc verification catches most attribution gaps without forcing a mechanical citation-per-sentence constraint during generation.", "alternatives_considered": ["Strictly grounded synthesis (more reliable but mechanical prose)", "No verification pass (faster but risks unchecked hallucination drift)"] },
    { "id": "dec_dedup_strategy", "type": "decision", "label": "Shallow deduplication via URL normalisation + SHA-256 content hash", "description": "Sources deduplicated by normalised URL and SHA-256 hash of full text. Matches on either key collapse to the first-seen copy.", "rationale": "Fast, zero extra API cost, no additional model dependency. Catches syndicated articles, mirror sites, and cached pages.", "alternatives_considered": ["Semantic embedding similarity (catches paraphrased duplicates but adds model dependency and latency)", "Title similarity only (too coarse)"] },
    { "id": "dec_conflict_presentation", "type": "decision", "label": "Conflicting claims get a side-by-side callout box in the report", "description": "When the Conflict Detector flags a contradiction, the Synthesis Engine renders a visually distinct callout block presenting both claims with citations, letting the reader judge.", "rationale": "Presenting both claims preserves epistemic honesty. A callout box makes conflicts visually salient rather than burying them in prose.", "alternatives_considered": ["Favour higher-relevance source and footnote dissent (suppresses information)", "Merge claims silently (misleading and unreliable)"] },
    { "id": "dec_token_budget", "type": "decision", "label": "Per-query token budget with relevance-ordered truncation and cost alerts", "description": "Each query has a configurable max token budget. Sources sorted by Tavily relevance score; lower-relevance sources truncated/skipped if budget exceeded. Daily cost tracked in SQLite with log WARNING at threshold.", "rationale": "Prevents unbounded cost growth at 200 queries/day. Relevance-ordered truncation maximises information quality per token spent. Soft alert without hard kill allows operator tuning.", "alternatives_considered": ["Cost tracking only without hard limits (risk of runaway spend)", "Uniform truncation of all sources equally (wastes budget on low-relevance content)", "No token management (not viable for 200/day)"] },
    { "id": "dec_notification_channel", "type": "decision", "label": "Structured log file as sole developer notification channel", "description": "Dead-letter events, cost threshold alerts, and pipeline errors written as structured JSON log entries via structlog to a rotating log file.", "rationale": "Sufficient for a local-machine setup. Structlog JSON output is machine-parseable for future integration with log shippers or alerting tools.", "alternatives_considered": ["Email via SMTP (extensible future option)", "Slack/Discord webhook (extensible future option)", "Plain print/stderr (not machine-parseable)"] },
    { "id": "dec_config_management", "type": "decision", "label": "YAML config file with environment variable overrides", "description": "All pipeline parameters live in config.yaml. Environment variables override individual keys for CI and secrets management.", "rationale": "YAML is human-readable and version-controllable. Env var override is the standard pattern for CI execution without modifying config files.", "alternatives_considered": ["Env vars only (no single source of truth)", "Hardcoded defaults (not operator-tunable)", "Pydantic Settings only (requires Python knowledge to configure)"] },
    { "id": "dec_source_threshold", "type": "decision", "label": "Proceed with report but embed quality_flags warning below 3 sources", "description": "If fewer than 3 usable sources remain after dedup and paywall filtering, the pipeline proceeds to synthesis but marks the report as low-confidence with a prominent header flag describing the source coverage limitation.", "rationale": "Aborting the job loses all partial value; a flagged report lets the human reader make an informed judgment about trustworthiness. Three sources is the minimum for meaningful triangulation.", "alternatives_considered": ["Abort job and return structured error (loses all partial work)", "Proceed silently without flagging (misleads reader about coverage)"] },
    { "id": "dec_artifact_ttl", "type": "decision", "label": "Configurable TTL: 7-day purge for intermediates, longer retention for final reports", "description": "A nightly cleanup job deletes raw Tavily content and source chunk files older than TTL_INTERMEDIATE_DAYS (default 7). Final Markdown/PDF reports are retained for TTL_REPORT_DAYS (default 90). SQLite metadata is kept indefinitely.", "rationale": "Intermediate artifacts are large and only needed for debugging active jobs. Final reports are the primary deliverable and should persist. SQLite records are small and valuable for run history and dedup lookups.", "alternatives_considered": ["Keep everything indefinitely (disk exhaustion at 200/day)", "Delete all intermediates immediately on completion (loses debuggability for failed jobs)", "No TTL policy (undocumented and inconsistent)"] },
    { "id": "dec_cli_interface", "type": "decision", "label": "CLI supports both single-query and batch file modes", "description": "python -m researcher \"<topic>\" for single-query. python -m researcher --batch queries.txt for batch mode. Batch mode submits all queries concurrently up to the semaphore limit.", "rationale": "Single-query mode enables quick testing and one-off research tasks. Batch mode is the primary interface for the 200-queries/day scalability target.", "alternatives_considered": ["Single-query only (cannot drive 200/day workload efficiently)", "Batch only (poor developer experience for testing and one-off use)"] },
    { "id": "comp_job_manager", "type": "component", "label": "Job Manager", "description": "Accepts research query input via CLI (single or batch), creates job records in SQLite, acquires semaphore slots, and dispatches the pipeline DAG. Tracks job lifecycle: queued → running → complete → failed.", "has_tests": false },
    { "id": "comp_search_engine", "type": "component", "label": "Search & Retrieval Engine", "description": "Calls Tavily API with the research topic, retrieves N results with full page content, and returns a list of raw SearchResult objects. Wrapped by Retry Manager and Rate Limiter.", "has_tests": false },
    { "id": "comp_content_processor", "type": "component", "label": "Content Processor", "description": "Deduplicates results by URL normalisation and SHA-256 hash, strips boilerplate, chunks content into token-bounded segments, applies relevance-ordered token budget, and enforces the 3-source minimum threshold.", "has_tests": false },
    { "id": "comp_summarizer", "type": "component", "label": "Per-Source Summarizer", "description": "Calls Claude once per deduplicated source chunk to produce a structured SourceSummary with inline attribution tags. Runs concurrently across sources within the token budget.", "has_tests": false },
    { "id": "comp_conflict_detector", "type": "component", "label": "Conflict Detector", "description": "Scans the set of SourceSummary objects for contradictory claims. Emits ConflictFlag records with both source references, confidence score, and the verbatim conflicting claims.", "has_tests": false },
    { "id": "comp_synthesis_engine", "type": "component", "label": "Synthesis Engine", "description": "Calls Claude with all source summaries, conflict flags, quality flags, and a structured report template. Renders a fluent narrative with conflict callout boxes wherever ConflictFlags exist.", "has_tests": false },
    { "id": "comp_citation_verifier", "type": "component", "label": "Citation Verifier", "description": "Runs a second LLM pass over the synthesized report. Checks citation presence and groundedness per paragraph against source summaries. Flags or auto-injects missing references.", "has_tests": false },
    { "id": "comp_report_renderer", "type": "component", "label": "Report Renderer", "description": "Transforms the verified ReportSchema into structured Markdown with a references section, then renders a PDF via WeasyPrint using a CSS template.", "has_tests": false },
    { "id": "comp_retry_manager", "type": "component", "label": "Retry Manager", "description": "Decorator/wrapper applied to all external API calls. Implements exponential backoff (1s/2s/4s/8s × 4 attempts). On exhaustion, writes to dead_letter_queue in SQLite and triggers the Notifier.", "has_tests": false },
    { "id": "comp_rate_limiter", "type": "component", "label": "Rate Limiter", "description": "Maintains a global asyncio semaphore for pipeline-level concurrency and independent per-API token buckets for Tavily and Claude.", "has_tests": false },
    { "id": "comp_token_budget_manager", "type": "component", "label": "Token Budget Manager", "description": "Enforces per-query token budgets by ordering sources by relevance score and truncating or skipping lower-relevance sources when budget would be exceeded. Tracks per-call token usage.", "has_tests": false },
    { "id": "comp_cost_tracker", "type": "component", "label": "Cost Tracker", "description": "Accumulates token usage and estimated API cost per job in SQLite. Compares running daily total against configurable alert threshold and logs a structured WARNING when exceeded.", "has_tests": false },
    { "id": "comp_job_store", "type": "component", "label": "Job Store (SQLite via SQLAlchemy async)", "description": "Persists job records, source content hashes, dead-letter entries, cost records, and run history. Accessed via SQLAlchemy async session.", "has_tests": false },
    { "id": "comp_notifier", "type": "component", "label": "Developer Notifier", "description": "Writes structured JSON log entries via structlog for dead-letter events, cost threshold breaches, and pipeline errors. Outputs to a rotating log file. Designed for future extension to email/webhook.", "has_tests": false },
    { "id": "comp_config_manager", "type": "component", "label": "Config Manager", "description": "Loads config.yaml at startup, merges environment variable overrides, and exposes a typed Settings object (via Pydantic) consumed by all components.", "has_tests": false },
    { "id": "comp_cleanup_job", "type": "component", "label": "Artifact Cleanup Job", "description": "Nightly scheduled coroutine that deletes raw Tavily content and source chunk files older than TTL_INTERMEDIATE_DAYS (default 7). Final reports deleted after TTL_REPORT_DAYS (default 90). SQLite metadata retained indefinitely.", "has_tests": false },
    { "id": "comp_cli", "type": "component", "label": "CLI Entry Point", "description": "Typer-based CLI providing two modes: single-query (researcher \"<topic>\") and batch file (researcher --batch queries.txt). Batch mode reads one query per line and submits all to Job Manager concurrently up to the semaphore cap.", "has_tests": false },
    { "id": "iface_search_result", "type": "interface", "label": "SearchResult schema", "description": "Normalised output contract from the Search Engine.", "contract": "{ url: str, title: str, raw_content: str, relevance_score: float, retrieved_at: datetime }" },
    { "id": "iface_source_chunk", "type": "interface", "label": "SourceChunk schema", "description": "Token-bounded content unit output by the Content Processor, ready for LLM ingestion.", "contract": "{ chunk_id: str, url: str, content_hash: str, text: str, token_count: int, chunk_index: int, relevance_score: float }" },
    { "id": "iface_source_summary", "type": "interface", "label": "SourceSummary schema", "description": "Structured per-source summary with attribution, output by the Summarizer.", "contract": "{ summary_id: str, url: str, title: str, key_points: list[str], conflicts: list[str], token_cost: int, retrieved_at: datetime }" },
    { "id": "iface_conflict_flag", "type": "interface", "label": "ConflictFlag schema", "description": "Conflict record emitted by Conflict Detector and consumed by the Synthesis Engine.", "contract": "{ conflict_id: str, claim_a: str, source_a_url: str, claim_b: str, source_b_url: str, confidence: float, subject: str }" },
    { "id": "iface_report_schema", "type": "interface", "label": "Final Report schema", "description": "Structured report contract passed from Synthesis Engine through Citation Verifier to Report Renderer.", "contract": "{ title: str, executive_summary: str, quality_flags: list[str], sections: list[{heading, body, citations, conflict_callouts}], references: list[{id, url, title, retrieved_at}] }" },
    { "id": "tst_content_processor", "type": "test", "label": "Content Processor dedup and chunking unit tests", "description": "Loads fixture HTML and raw text inputs. Asserts correct URL normalisation, SHA-256 deduplication, boilerplate stripping, token-bounded chunk output, and quality_flag injection when source count < 3.", "test_type": "unit", "status": "planned" },
    { "id": "tst_retry_manager", "type": "test", "label": "Retry Manager backoff and DLQ unit tests", "description": "Injects callables that fail N times then succeed (or always fail). Asserts correct backoff timing, attempt count, dead-letter queue write, and notifier trigger on exhaustion.", "test_type": "unit", "status": "planned" },
    { "id": "tst_schema_conformance", "type": "test", "label": "Interface schema conformance tests", "description": "Validates recorded Tavily and Claude API responses against Pydantic models for all four interface schemas. Ensures schema contracts hold against real API response shapes.", "test_type": "conformance", "status": "planned" },
    { "id": "tst_summarizer", "type": "test", "label": "Summarizer unit tests with frozen LLM fixtures", "description": "Feeds frozen Claude response fixtures into the Summarizer. Asserts correct SourceSummary shape, attribution presence, and token cost recording.", "test_type": "unit", "status": "planned" },
    { "id": "tst_citation_verifier", "type": "test", "label": "Citation Verifier unit tests", "description": "Provides a ReportSchema with known uncited paragraphs and frozen LLM verification responses. Asserts correct flag injection and reference resolution.", "test_type": "unit", "status": "planned" },
    { "id": "tst_pipeline_integration", "type": "test", "label": "Full pipeline integration test (all externals mocked)", "description": "Runs the complete pipeline from CLI entry through Job Manager to Report Renderer with all Tavily and Claude calls replaced by recorded fixture responses. Asserts final report structure, citation presence, conflict callout rendering, and quality_flags.", "test_type": "integration", "status": "planned" },
    { "id": "tst_token_budget", "type": "test", "label": "Token Budget Manager enforcement unit tests", "description": "Injects a set of sources exceeding the budget limit. Asserts that lower-relevance sources are truncated first, budget is never exceeded, and cost tracker receives correct token counts.", "test_type": "unit", "status": "planned" },
    { "id": "tst_report_renderer", "type": "test", "label": "Report Renderer output tests", "description": "Feeds a fixed ReportSchema with known sections, citations, and conflict callouts. Asserts Markdown structure (headings, callout blocks, references section) and that PDF generation completes without error.", "test_type": "unit", "status": "planned" },
    { "id": "tst_cleanup_job", "type": "test", "label": "Artifact cleanup TTL unit tests", "description": "Creates fixture artifact files with manipulated mtimes. Asserts that files older than TTL_INTERMEDIATE_DAYS are deleted and final reports within TTL_REPORT_DAYS are retained.", "test_type": "unit", "status": "planned" },
    { "id": "asm_tavily_rate_limits", "type": "assumption", "label": "Tavily API rate limits accommodate burst concurrency", "description": "Assumes Tavily's plan tier allows enough requests/minute for 10 concurrent pipelines each making 3–5 search calls without throttling.", "confidence": 0.6, "validated": false },
    { "id": "asm_context_window", "type": "assumption", "label": "Multi-source summaries fit Claude's context window for synthesis", "description": "Assumes combined SourceSummary objects for a single topic fit within Claude's context window after per-source summarization reduces raw content volume.", "confidence": 0.8, "validated": false },
    { "id": "asm_local_resources", "type": "assumption", "label": "Local machine sustains 5–10 concurrent async pipelines", "description": "Assumes enough RAM and network bandwidth for concurrent Tavily fetches and LLM calls without thrashing.", "confidence": 0.7, "validated": false },
    { "id": "asm_tavily_content_quality", "type": "assumption", "label": "Tavily returns substantive full-page content reliably", "description": "Assumes Tavily successfully extracts readable text from the majority of retrieved URLs vs. returning empty or JS-only shells.", "confidence": 0.65, "validated": false },
    { "id": "asm_posthoc_citation_sufficient", "type": "assumption", "label": "Post-hoc citation pass catches most attribution gaps", "description": "Assumes a second LLM verification pass is sufficient to catch uncited claims in the fluent narrative.", "confidence": 0.65, "validated": false },
    { "id": "asm_structlog_sufficient", "type": "assumption", "label": "Structured log file is sufficient for developer incident response", "description": "Assumes the developer monitors log output during pipeline operation and can respond to dead-letter or cost-alert entries without push notifications.", "confidence": 0.8, "validated": false },
    { "id": "risk_api_cost", "type": "risk", "label": "LLM + search API costs escalate at scale", "description": "At 200 queries/day with multiple LLM calls per pipeline stage, token costs could become significant without a cost ceiling.", "severity": 0.7 },
    { "id": "risk_rate_limiting", "type": "risk", "label": "API rate limits throttle or fail concurrent pipelines", "description": "Bursts of concurrent queries may exhaust Tavily or Claude API rate limits, causing cascading failures across multiple pipelines.", "severity": 0.8 },
    { "id": "risk_hallucination", "type": "risk", "label": "LLM hallucination survives post-hoc citation check", "description": "Fluent narrative generation may introduce plausible-sounding but unsourced claims that the citation verifier fails to catch.", "severity": 0.7 },
    { "id": "risk_content_quality", "type": "risk", "label": "Poor or paywalled source content degrades report quality", "description": "Many high-quality sources are paywalled or return minimal content, reducing synthesis quality silently.", "severity": 0.65 },
    { "id": "risk_dedup_false_negative", "type": "risk", "label": "Semantic duplicates pass hash-based deduplication", "description": "Two sources reporting the same fact in different words pass URL/hash dedup and are treated as independent corroboration.", "severity": 0.6 },
    { "id": "risk_deadletter_growth", "type": "risk", "label": "Dead-letter queue grows unbounded without manual replay", "description": "A systemic API outage may accumulate hundreds of DLQ entries with no automated replay mechanism.", "severity": 0.55 },
    { "id": "risk_low_source_coverage", "type": "risk", "label": "Too few usable sources yield a low-confidence report", "description": "If paywalls or Tavily extraction failures reduce usable sources below 3, the synthesized report may be thin but not visibly flagged as low-confidence.", "severity": 0.65 }
  ],
  "edges": [
    { "source_id": "dec_search_api", "target_id": "obj_autonomous_research", "type": "motivated_by" },
    { "source_id": "dec_llm", "target_id": "obj_structured_output", "type": "motivated_by" },
    { "source_id": "dec_concurrency", "target_id": "obj_concurrent_scale", "type": "motivated_by" },
    { "source_id": "dec_orchestration", "target_id": "obj_autonomous_research", "type": "motivated_by" },
    { "source_id": "dec_output", "target_id": "obj_structured_output", "type": "motivated_by" },
    { "source_id": "dec_retry_strategy", "target_id": "req_failure_handling", "type": "motivated_by" },
    { "source_id": "dec_dedup_strategy", "target_id": "req_dedup", "type": "motivated_by" },
    { "source_id": "dec_synthesis_style", "target_id": "obj_structured_output", "type": "motivated_by" },
    { "source_id": "dec_conflict_presentation", "target_id": "req_dedup", "type": "motivated_by" },
    { "source_id": "dec_token_budget", "target_id": "obj_concurrent_scale", "type": "motivated_by" },
    { "source_id": "dec_source_threshold", "target_id": "req_failure_handling", "type": "motivated_by" },
    { "source_id": "dec_artifact_ttl", "target_id": "obj_concurrent_scale", "type": "motivated_by" },
    { "source_id": "dec_cli_interface", "target_id": "obj_concurrent_scale", "type": "motivated_by" },
    { "source_id": "dec_search_api", "target_id": "asm_tavily_rate_limits", "type": "assumes" },
    { "source_id": "dec_search_api", "target_id": "asm_tavily_content_quality", "type": "assumes" },
    { "source_id": "dec_llm", "target_id": "asm_context_window", "type": "assumes" },
    { "source_id": "dec_concurrency", "target_id": "asm_local_resources", "type": "assumes" },
    { "source_id": "dec_synthesis_style", "target_id": "asm_posthoc_citation_sufficient", "type": "assumes" },
    { "source_id": "dec_notification_channel", "target_id": "asm_structlog_sufficient", "type": "assumes" },
    { "source_id": "risk_rate_limiting", "target_id": "dec_concurrency", "type": "conflicts_with" },
    { "source_id": "risk_rate_limiting", "target_id": "asm_tavily_rate_limits", "type": "invalidates" },
    { "source_id": "risk_hallucination", "target_id": "req_citations", "type": "conflicts_with" },
    { "source_id": "risk_hallucination", "target_id": "asm_posthoc_citation_sufficient", "type": "invalidates" },
    { "source_id": "risk_content_quality", "target_id": "asm_tavily_content_quality", "type": "invalidates" },
    { "source_id": "risk_api_cost", "target_id": "dec_llm", "type": "conflicts_with" },
    { "source_id": "risk_dedup_false_negative", "target_id": "req_dedup", "type": "conflicts_with" },
    { "source_id": "risk_low_source_coverage", "target_id": "asm_tavily_content_quality", "type": "invalidates" },
    { "source_id": "risk_deadletter_growth", "target_id": "dec_retry_strategy", "type": "conflicts_with" },
    { "source_id": "comp_job_manager", "target_id": "req_autonomous", "type": "implements" },
    { "source_id": "comp_content_processor", "target_id": "req_dedup", "type": "implements" },
    { "source_id": "comp_citation_verifier", "target_id": "req_citations", "type": "implements" },
    { "source_id": "comp_retry_manager", "target_id": "req_failure_handling", "type": "implements" },
    { "source_id": "comp_token_budget_manager", "target_id": "dec_token_budget", "type": "motivated_by" },
    { "source_id": "comp_cost_tracker", "target_id": "dec_token_budget", "type": "motivated_by" },
    { "source_id": "comp_notifier", "target_id": "dec_notification_channel", "type": "motivated_by" },
    { "source_id": "comp_config_manager", "target_id": "dec_config_management", "type": "motivated_by" },
    { "source_id": "comp_conflict_detector", "target_id": "dec_conflict_presentation", "type": "motivated_by" },
    { "source_id": "comp_rate_limiter", "target_id": "obj_concurrent_scale", "type": "motivated_by" },
    { "source_id": "comp_search_engine", "target_id": "dec_search_api", "type": "motivated_by" },
    { "source_id": "comp_synthesis_engine", "target_id": "dec_synthesis_style", "type": "motivated_by" },
    { "source_id": "comp_content_processor", "target_id": "dec_dedup_strategy", "type": "motivated_by" },
    { "source_id": "comp_cleanup_job", "target_id": "dec_artifact_ttl", "type": "motivated_by" },
    { "source_id": "comp_cli", "target_id": "dec_cli_interface", "type": "motivated_by" },
    { "source_id": "comp_search_engine", "target_id": "iface_search_result", "type": "exposes" },
    { "source_id": "comp_content_processor", "target_id": "iface_search_result", "type": "consumes" },
    { "source_id": "comp_content_processor", "target_id": "iface_source_chunk", "type": "exposes" },
    { "source_id": "comp_summarizer", "target_id": "iface_source_chunk", "type": "consumes" },
    { "source_id": "comp_summarizer", "target_id": "iface_source_summary", "type": "exposes" },
    { "source_id": "comp_conflict_detector", "target_id": "iface_source_summary", "type": "consumes" },
    { "source_id": "comp_conflict_detector", "target_id": "iface_conflict_flag", "type": "exposes" },
    { "source_id": "comp_synthesis_engine", "target_id": "iface_source_summary", "type": "consumes" },
    { "source_id": "comp_synthesis_engine", "target_id": "iface_conflict_flag", "type": "consumes" },
    { "source_id": "comp_synthesis_engine", "target_id": "iface_report_schema", "type": "exposes" },
    { "source_id": "comp_citation_verifier", "target_id": "iface_report_schema", "type": "consumes" },
    { "source_id": "comp_report_renderer", "target_id": "iface_report_schema", "type": "consumes" },
    { "source_id": "comp_cli", "target_id": "comp_job_manager", "type": "depends_on" },
    { "source_id": "comp_job_manager", "target_id": "comp_search_engine", "type": "depends_on" },
    { "source_id": "comp_search_engine", "target_id": "comp_retry_manager", "type": "depends_on" },
    { "source_id": "comp_summarizer", "target_id": "comp_retry_manager", "type": "depends_on" },
    { "source_id": "comp_synthesis_engine", "target_id": "comp_retry_manager", "type": "depends_on" },
    { "source_id": "comp_citation_verifier", "target_id": "comp_retry_manager", "type": "depends_on" },
    { "source_id": "comp_search_engine", "target_id": "comp_rate_limiter", "type": "depends_on" },
    { "source_id": "comp_summarizer", "target_id": "comp_rate_limiter", "type": "depends_on" },
    { "source_id": "comp_synthesis_engine", "target_id": "comp_rate_limiter", "type": "depends_on" },
    { "source_id": "comp_summarizer", "target_id": "comp_token_budget_manager", "type": "depends_on" },
    { "source_id": "comp_content_processor", "target_id": "comp_token_budget_manager", "type": "depends_on" },
    { "source_id": "comp_token_budget_manager", "target_id": "comp_cost_tracker", "type": "depends_on" },
    { "source_id": "comp_cost_tracker", "target_id": "comp_job_store", "type": "depends_on" },
    { "source_id": "comp_cost_tracker", "target_id": "comp_notifier", "type": "depends_on" },
    { "source_id": "comp_job_manager", "target_id": "comp_job_store", "type": "depends_on" },
    { "source_id": "comp_retry_manager", "target_id": "comp_job_store", "type": "depends_on" },
    { "source_id": "comp_retry_manager", "target_id": "comp_notifier", "type": "depends_on" },
    { "source_id": "comp_content_processor", "target_id": "comp_job_store", "type": "depends_on" },
    { "source_id": "comp_cleanup_job", "target_id": "comp_job_store", "type": "depends_on" },
    { "source_id": "comp_job_manager", "target_id": "comp_config_manager", "type": "depends_on" },
    { "source_id": "comp_rate_limiter", "target_id": "comp_config_manager", "type": "depends_on" },
    { "source_id": "comp_token_budget_manager", "target_id": "comp_config_manager", "type": "depends_on" },
    { "source_id": "comp_cleanup_job", "target_id": "comp_config_manager", "type": "depends_on" },
    { "source_id": "tst_content_processor", "target_id": "comp_content_processor", "type": "verifies" },
    { "source_id": "tst_content_processor", "target_id": "risk_low_source_coverage", "type": "guards_against" },
    { "source_id": "tst_retry_manager", "target_id": "comp_retry_manager", "type": "verifies" },
    { "source_id": "tst_retry_manager", "target_id": "risk_rate_limiting", "type": "guards_against" },
    { "source_id": "tst_retry_manager", "target_id": "risk_deadletter_growth", "type": "guards_against" },
    { "source_id": "tst_schema_conformance", "target_id": "iface_search_result", "type": "verifies" },
    { "source_id": "tst_schema_conformance", "target_id": "iface_source_summary", "type": "verifies" },
    { "source_id": "tst_schema_conformance", "target_id": "iface_conflict_flag", "type": "verifies" },
    { "source_id": "tst_schema_conformance", "target_id": "iface_report_schema", "type": "verifies" },
    { "source_id": "tst_summarizer", "target_id": "comp_summarizer", "type": "verifies" },
    { "source_id": "tst_citation_verifier", "target_id": "comp_citation_verifier", "type": "verifies" },
    { "source_id": "tst_citation_verifier", "target_id": "risk_hallucination", "type": "guards_against" },
    { "source_id": "tst_pipeline_integration", "target_id": "comp_job_manager", "type": "verifies" },
    { "source_id": "tst_pipeline_integration", "target_id": "dec_orchestration", "type": "validates" },
    { "source_id": "tst_token_budget", "target_id": "comp_token_budget_manager", "type": "verifies" },
    { "source_id": "tst_token_budget", "target_id": "risk_api_cost", "type": "guards_against" },
    { "source_id": "tst_report_renderer", "target_id": "comp_report_renderer", "type": "verifies" },
    { "source_id": "tst_report_renderer", "target_id": "dec_output", "type": "validates" },
    { "source_id": "tst_cleanup_job", "target_id": "comp_cleanup_job", "type": "verifies" }
  ]
}
[/GRAPH UPDATE]

Final Implementation Plan: Autonomous Research Agent System
1. Project Structure
researcher/
├── config.yaml                  # Operator-tunable parameters
├── pyproject.toml               # Dependencies and entry points
├── .env.example                 # API key template (never committed)
│
├── researcher/
│   ├── __main__.py              # CLI entry point (Typer)
│   ├── settings.py              # Config Manager — Pydantic Settings + YAML loader
│   ├── models.py                # All Pydantic schemas (interfaces)
│   ├── database.py              # SQLAlchemy async engine + table definitions
│   │
│   ├── pipeline/
│   │   ├── job_manager.py       # Job lifecycle, semaphore dispatch
│   │   ├── search_engine.py     # Tavily API wrapper
│   │   ├── content_processor.py # Dedup, chunk, threshold check
│   │   ├── summarizer.py        # Per-source Claude summarization
│   │   ├── conflict_detector.py # Contradictory claim detection
│   │   ├── synthesis_engine.py  # Claude narrative synthesis
│   │   ├── citation_verifier.py # Post-hoc citation pass
│   │   └── report_renderer.py   # Markdown + PDF output
│   │
│   ├── infra/
│   │   ├── retry.py             # Exponential backoff decorator
│   │   ├── rate_limiter.py      # Semaphore + per-API token buckets
│   │   ├── token_budget.py      # Per-query budget enforcement
│   │   ├── cost_tracker.py      # Token cost accumulation + alerts
│   │   ├── notifier.py          # structlog writer
│   │   └── cleanup.py           # TTL-based artifact purge
│   │
│   └── prompts/
│       ├── summarize.txt        # Per-source summarization prompt template
│       ├── synthesize.txt       # Synthesis prompt template
│       └── verify_citations.txt # Citation verification prompt template
│
├── tests/
│   ├── conftest.py              # Shared fixtures, mock factories
│   ├── fixtures/                # Recorded API responses (JSON), HTML samples
│   ├── unit/
│   │   ├── test_content_processor.py
│   │   ├── test_retry.py
│   │   ├── test_token_budget.py
│   │   ├── test_summarizer.py
│   │   ├── test_citation_verifier.py
│   │   ├── test_report_renderer.py
│   │   └── test_cleanup.py
│   ├── conformance/
│   │   └── test_schemas.py
│   └── integration/
│       └── test_pipeline.py
│
└── outputs/                     # Runtime artifact root (gitignored)
    ├── reports/                 # Final .md and .pdf files
    ├── intermediates/           # Raw Tavily content, chunks (TTL 7d)
    └── logs/                    # Rotating structlog output
2. Configuration (config.yaml)
yaml
# Pipeline concurrency
concurrency:
  max_pipeline_slots: 8          # Global asyncio semaphore cap
  tavily_requests_per_minute: 60 # Token bucket for Tavily API
  claude_requests_per_minute: 40 # Token bucket for Claude API

# Search & retrieval
search:
  results_per_query: 10          # Tavily results to fetch per topic
  min_usable_sources: 3          # Below this: quality_flag = LOW_CONFIDENCE

# Token budgets (approximate; 1 token ≈ 0.75 words)
token_budget:
  per_query_max_tokens: 80000    # Hard cap across all LLM calls for one query
  summarization_max_tokens: 2000 # Per-source summary output cap
  synthesis_max_tokens: 4000     # Synthesis output cap
  verification_max_tokens: 2000  # Citation check output cap

# Cost tracking (USD estimates based on Claude Sonnet pricing)
cost:
  daily_alert_threshold_usd: 20.00
  cost_per_1k_input_tokens: 0.003
  cost_per_1k_output_tokens: 0.015

# Retry
retry:
  max_attempts: 4
  base_backoff_seconds: 1.0      # Doubles each attempt: 1, 2, 4, 8

# Artifact TTL
storage:
  output_root: "./outputs"
  intermediate_ttl_days: 7
  report_ttl_days: 90

# Logging
logging:
  log_dir: "./outputs/logs"
  max_bytes: 10485760            # 10 MB per log file
  backup_count: 5
3. Data Models (models.py)
All pipeline interfaces are Pydantic v2 models. They serve as both runtime validation and the schema conformance test contract.

python
from pydantic import BaseModel, HttpUrl, field_validator
from datetime import datetime
from enum import Enum
from typing import Optional
import hashlib

# ── SearchResult ────────────────────────────────────────────────
class SearchResult(BaseModel):
    url: str
    title: str
    raw_content: str
    relevance_score: float        # 0.0–1.0 from Tavily
    retrieved_at: datetime

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(self.raw_content.encode()).hexdigest()

# ── SourceChunk ─────────────────────────────────────────────────
class SourceChunk(BaseModel):
    chunk_id: str                 # "{url_hash}_{chunk_index}"
    url: str
    content_hash: str
    text: str
    token_count: int
    chunk_index: int
    relevance_score: float

# ── SourceSummary ───────────────────────────────────────────────
class SourceSummary(BaseModel):
    summary_id: str
    url: str
    title: str
    key_points: list[str]
    raw_conflicts: list[str]      # Potential contradictions noted by Claude
    token_cost: int               # Actual tokens consumed by this call
    retrieved_at: datetime

# ── ConflictFlag ────────────────────────────────────────────────
class ConflictFlag(BaseModel):
    conflict_id: str
    subject: str                  # e.g., "AI diagnostic accuracy rate"
    claim_a: str
    source_a_url: str
    claim_b: str
    source_b_url: str
    confidence: float             # 0.0–1.0; how certain the detector is

# ── ReportSection ───────────────────────────────────────────────
class ConflictCallout(BaseModel):
    subject: str
    claim_a: str
    source_a_url: str
    claim_b: str
    source_b_url: str

class ReportSection(BaseModel):
    heading: str
    body: str
    citations: list[str]          # Reference IDs, e.g. ["ref_1", "ref_3"]
    conflict_callouts: list[ConflictCallout] = []

class Reference(BaseModel):
    ref_id: str
    url: str
    title: str
    retrieved_at: datetime

class QualityFlag(str, Enum):
    LOW_CONFIDENCE = "LOW_CONFIDENCE"   # < min_usable_sources
    PARTIAL_RESULTS = "PARTIAL_RESULTS" # Some sources failed retrieval
    CITATION_GAPS   = "CITATION_GAPS"   # Verifier found unfixable gaps

# ── FinalReport ─────────────────────────────────────────────────
class FinalReport(BaseModel):
    title: str
    topic: str
    generated_at: datetime
    quality_flags: list[QualityFlag] = []
    source_count: int
    executive_summary: str
    sections: list[ReportSection]
    references: list[Reference]
4. Database Schema (database.py)
python
# SQLAlchemy async tables — four concerns kept cleanly separated

# jobs: lifecycle tracking
# columns: id, topic, status, created_at, completed_at,
#          source_count, quality_flags (JSON), artifact_path

# content_hashes: deduplication store
# columns: url_normalized, content_hash, first_seen_at, job_id

# dead_letter_queue: failed jobs awaiting manual replay
# columns: id, job_id, stage, error_type, error_message,
#          attempt_count, failed_at, resolved (bool)

# cost_records: per-job token and USD tracking
# columns: id, job_id, stage, input_tokens, output_tokens,
#          estimated_cost_usd, recorded_at
5. Component Implementations
5.1 Retry Manager (infra/retry.py)
python
import asyncio, functools
from researcher.infra.notifier import log_dead_letter

def with_retry(max_attempts: int = 4, base_backoff: float = 1.0):
    """
    Decorator for any async function making external API calls.
    Retries with exponential backoff on any Exception.
    On exhaustion: writes to dead_letter_queue and re-raises.
    """
    def decorator(fn):
        @functools.wraps(fn)
        async def wrapper(*args, job_id: str, stage: str, **kwargs):
            last_exc = None
            for attempt in range(max_attempts):
                try:
                    return await fn(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    if attempt < max_attempts - 1:
                        wait = base_backoff * (2 ** attempt)
                        await asyncio.sleep(wait)
            # Exhausted — write to DLQ and alert
            await log_dead_letter(job_id=job_id, stage=stage, exc=last_exc)
            raise last_exc
        return wrapper
    return decorator
5.2 Rate Limiter (infra/rate_limiter.py)
python
import asyncio, time

class TokenBucketLimiter:
    """
    Async token bucket. Each API gets its own instance.
    Callers await .acquire() before making an API call.
    """
    def __init__(self, rate_per_minute: int):
        self._rate = rate_per_minute / 60.0   # tokens per second
        self._tokens = float(rate_per_minute)
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_refill
            self._tokens = min(
                self._rate * 60,              # cap at burst size
                self._tokens + elapsed * self._rate
            )
            self._last_refill = now
            if self._tokens < 1:
                wait = (1 - self._tokens) / self._rate
                await asyncio.sleep(wait)
                self._tokens = 0
            else:
                self._tokens -= 1

# Singletons shared across all concurrent pipelines
class RateLimiters:
    tavily: TokenBucketLimiter
    claude: TokenBucketLimiter

    @classmethod
    def init(cls, settings):
        cls.tavily = TokenBucketLimiter(settings.concurrency.tavily_requests_per_minute)
        cls.claude = TokenBucketLimiter(settings.concurrency.claude_requests_per_minute)
5.3 Search Engine (pipeline/search_engine.py)
python
from tavily import AsyncTavilyClient
from researcher.infra.retry import with_retry
from researcher.infra.rate_limiter import RateLimiters
from researcher.models import SearchResult
from datetime import datetime, timezone

class SearchEngine:
    def __init__(self, api_key: str):
        self._client = AsyncTavilyClient(api_key=api_key)

    @with_retry(max_attempts=4, base_backoff=1.0)
    async def search(self, topic: str, n: int, job_id: str, stage: str) -> list[SearchResult]:
        await RateLimiters.tavily.acquire()
        response = await self._client.search(
            query=topic,
            search_depth="advanced",   # returns full page content
            max_results=n,
            include_raw_content=True,
        )
        return [
            SearchResult(
                url=r["url"],
                title=r.get("title", ""),
                raw_content=r.get("raw_content") or r.get("content", ""),
                relevance_score=r.get("score", 0.5),
                retrieved_at=datetime.now(timezone.utc),
            )
            for r in response.get("results", [])
        ]
5.4 Content Processor (pipeline/content_processor.py)
python
import hashlib, re
from urllib.parse import urlparse, urlunparse
from researcher.models import SearchResult, SourceChunk, QualityFlag
from researcher.infra.token_budget import TokenBudgetManager

def _normalize_url(url: str) -> str:
    p = urlparse(url.lower().rstrip("/"))
    return urlunparse((p.scheme, p.netloc, p.path, "", "", ""))

def _strip_boilerplate(text: str) -> str:
    # Remove nav/footer patterns, excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def _chunk_text(text: str, max_tokens: int) -> list[str]:
    # Approximate: 1 token ≈ 4 chars. Split on paragraph boundaries.
    max_chars = max_tokens * 4
    paragraphs = text.split("\n\n")
    chunks, current = [], []
    current_len = 0
    for p in paragraphs:
        if current_len + len(p) > max_chars and current:
            chunks.append("\n\n".join(current))
            current, current_len = [], 0
        current.append(p)
        current_len += len(p)
    if current:
        chunks.append("\n\n".join(current))
    return chunks

class ContentProcessor:
    def __init__(self, budget: TokenBudgetManager, min_sources: int = 3):
        self._budget = budget
        self._min_sources = min_sources
        self._seen_urls: set[str] = set()
        self._seen_hashes: set[str] = set()

    def process(
        self, results: list[SearchResult]
    ) -> tuple[list[SourceChunk], list[QualityFlag]]:
        quality_flags = []
        deduped = self._deduplicate(results)

        if len(deduped) < self._min_sources:
            quality_flags.append(QualityFlag.LOW_CONFIDENCE)

        # Sort by relevance descending — budget truncation drops from the tail
        deduped.sort(key=lambda r: r.relevance_score, reverse=True)

        chunks = []
        for result in deduped:
            if not self._budget.can_afford(result.raw_content):
                # Budget exhausted; remaining sources silently skipped
                break
            clean = _strip_boilerplate(result.raw_content)
            url_hash = hashlib.md5(result.url.encode()).hexdigest()[:8]
            for i, text in enumerate(_chunk_text(clean, max_tokens=4000)):
                chunks.append(SourceChunk(
                    chunk_id=f"{url_hash}_{i}",
                    url=result.url,
                    content_hash=result.content_hash,
                    text=text,
                    token_count=len(text) // 4,
                    chunk_index=i,
                    relevance_score=result.relevance_score,
                ))
            self._budget.consume(result.raw_content)

        return chunks, quality_flags

    def _deduplicate(self, results: list[SearchResult]) -> list[SearchResult]:
        deduped = []
        for r in results:
            norm = _normalize_url(r.url)
            h = r.content_hash
            if norm not in self._seen_urls and h not in self._seen_hashes:
                self._seen_urls.add(norm)
                self._seen_hashes.add(h)
                deduped.append(r)
        return deduped
5.5 Per-Source Summarizer (pipeline/summarizer.py)
python
import asyncio, anthropic
from researcher.models import SourceChunk, SourceSummary
from researcher.infra.retry import with_retry
from researcher.infra.rate_limiter import RateLimiters
from researcher.infra.cost_tracker import CostTracker

SUMMARIZE_PROMPT = open("researcher/prompts/summarize.txt").read()

class Summarizer:
    def __init__(self, client: anthropic.AsyncAnthropic, tracker: CostTracker):
        self._client = client
        self._tracker = tracker

    async def summarize_all(
        self, chunks: list[SourceChunk], job_id: str
    ) -> list[SourceSummary]:
        """Run summarization concurrently across all chunks."""
        tasks = [self._summarize_chunk(c, job_id) for c in chunks]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # Filter out failed summaries — partial results are valid
        return [r for r in results if isinstance(r, SourceSummary)]

    @with_retry(max_attempts=4, base_backoff=1.0)
    async def _summarize_chunk(
        self, chunk: SourceChunk, job_id: str, stage: str = "summarize"
    ) -> SourceSummary:
        await RateLimiters.claude.acquire()
        prompt = SUMMARIZE_PROMPT.format(
            url=chunk.url,
            content=chunk.text,
        )
        response = await self._client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        # Claude returns structured JSON (enforced via prompt instructions)
        import json
        data = json.loads(response.content[0].text)
        tokens_used = response.usage.input_tokens + response.usage.output_tokens
        await self._tracker.record(job_id=job_id, stage="summarize",
                                   input_tokens=response.usage.input_tokens,
                                   output_tokens=response.usage.output_tokens)
        return SourceSummary(
            summary_id=chunk.chunk_id,
            url=chunk.url,
            title=data["title"],
            key_points=data["key_points"],
            raw_conflicts=data.get("potential_conflicts", []),
            token_cost=tokens_used,
            retrieved_at=chunk.__dict__.get("retrieved_at") or __import__("datetime").datetime.utcnow(),
        )
prompts/summarize.txt:

You are a research assistant. Summarize the following web page content.

URL: {url}
CONTENT:
{content}

Respond with ONLY a JSON object (no markdown fences) with this structure:
{{
  "title": "page title or inferred topic",
  "key_points": ["concise factual claim with any statistics", ...],
  "potential_conflicts": ["claim that may contradict common knowledge or other sources", ...]
}}

Rules:
- key_points must be direct factual claims grounded in the content above
- Do not introduce information not present in CONTENT
- Each key_point must be attributable to this source URL
5.6 Conflict Detector (pipeline/conflict_detector.py)
python
from researcher.models import SourceSummary, ConflictFlag
import uuid

class ConflictDetector:
    """
    Lightweight heuristic conflict detection.
    For each pair of summaries sharing a topic keyword,
    asks Claude to identify contradictory claim pairs.
    Returns ConflictFlag objects consumed by the Synthesis Engine.
    """
    def __init__(self, client, tracker):
        self._client = client
        self._tracker = tracker

    async def detect(
        self, summaries: list[SourceSummary], job_id: str
    ) -> list[ConflictFlag]:
        if len(summaries) < 2:
            return []

        # Flatten all key_points with their source URLs into a single prompt
        # Claude identifies pairs that contradict each other
        all_claims = []
        for s in summaries:
            for point in s.key_points:
                all_claims.append({"url": s.url, "claim": point})

        prompt = self._build_prompt(all_claims)
        response = await self._client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        import json
        raw = json.loads(response.content[0].text)
        await self._tracker.record(job_id=job_id, stage="conflict_detect",
                                   input_tokens=response.usage.input_tokens,
                                   output_tokens=response.usage.output_tokens)
        return [
            ConflictFlag(
                conflict_id=str(uuid.uuid4())[:8],
                subject=c["subject"],
                claim_a=c["claim_a"], source_a_url=c["source_a_url"],
                claim_b=c["claim_b"], source_b_url=c["source_b_url"],
                confidence=c["confidence"],
            )
            for c in raw.get("conflicts", [])
        ]

    def _build_prompt(self, claims: list[dict]) -> str:
        claims_text = "\n".join(
            f"[{i+1}] ({c['url']}) {c['claim']}"
            for i, c in enumerate(claims)
        )
        return f"""
You are a fact-checking assistant. Below is a numbered list of claims from different web sources.
Identify pairs of claims that directly contradict each other on the same subject.

CLAIMS:
{claims_text}

Respond with ONLY a JSON object (no markdown fences):
{{
  "conflicts": [
    {{
      "subject": "the topic both claims address",
      "claim_a": "first claim verbatim",
      "source_a_url": "url of first claim",
      "claim_b": "second contradicting claim verbatim",
      "source_b_url": "url of second claim",
      "confidence": 0.0-1.0
    }}
  ]
}}

If no genuine contradictions exist, return {{"conflicts": []}}.
Only flag direct factual contradictions, not differences in emphasis or scope.
"""
5.7 Synthesis Engine (pipeline/synthesis_engine.py)
python
from researcher.models import SourceSummary, ConflictFlag, QualityFlag, FinalReport

SYNTHESIZE_PROMPT = open("researcher/prompts/synthesize.txt").read()

class SynthesisEngine:
    def __init__(self, client, tracker):
        self._client = client
        self._tracker = tracker

    async def synthesize(
        self,
        topic: str,
        summaries: list[SourceSummary],
        conflicts: list[ConflictFlag],
        quality_flags: list[QualityFlag],
        job_id: str,
    ) -> FinalReport:
        summaries_text = self._format_summaries(summaries)
        conflicts_text = self._format_conflicts(conflicts)
        flags_text = ", ".join(f.value for f in quality_flags) or "NONE"

        prompt = SYNTHESIZE_PROMPT.format(
            topic=topic,
            summaries=summaries_text,
            conflicts=conflicts_text,
            quality_flags=flags_text,
        )
        response = await self._client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        )
        import json
        data = json.loads(response.content[0].text)
        await self._tracker.record(...)

        return FinalReport(**data)  # Pydantic validates the response shape
prompts/synthesize.txt (key instructions):

You are a professional research writer. Using ONLY the source summaries below,
write a comprehensive research report on: "{topic}"

SOURCE SUMMARIES:
{summaries}

DETECTED CONFLICTS:
{conflicts}

QUALITY FLAGS: {quality_flags}

Output ONLY a JSON object matching the FinalReport schema:
{{
  "title": "...",
  "topic": "{topic}",
  "quality_flags": [...],   // include any passed-in flags unchanged
  "source_count": N,
  "executive_summary": "3-4 sentence overview...",
  "sections": [
    {{
      "heading": "...",
      "body": "Fluent narrative paragraph(s)...",
      "citations": ["ref_1", "ref_3"],
      "conflict_callouts": []   // populate from DETECTED CONFLICTS where relevant
    }}
  ],
  "references": [
    {{"ref_id": "ref_1", "url": "...", "title": "...", "retrieved_at": "ISO datetime"}}
  ]
}}

RULES:
- Every factual claim in body text must have a citation ref_id in that section's citations list
- Do not introduce facts not present in SOURCE SUMMARIES
- For each item in DETECTED CONFLICTS, include a conflict_callout in the most relevant section
- If QUALITY FLAGS includes LOW_CONFIDENCE, begin executive_summary with a clear warning
5.8 Citation Verifier (pipeline/citation_verifier.py)
python
VERIFY_PROMPT = open("researcher/prompts/verify_citations.txt").read()

class CitationVerifier:
    def __init__(self, client, tracker):
        self._client = client
        self._tracker = tracker

    async def verify(self, report: FinalReport, summaries: list[SourceSummary], job_id: str) -> FinalReport:
        prompt = VERIFY_PROMPT.format(
            report_json=report.model_dump_json(indent=2),
            summaries=self._format_summaries(summaries),
        )
        response = await self._client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        import json
        verified_data = json.loads(response.content[0].text)
        await self._tracker.record(...)
        # Return validated report; may have CITATION_GAPS flag added
        return FinalReport(**verified_data)
5.9 Report Renderer (pipeline/report_renderer.py)
python
from pathlib import Path
from datetime import datetime
from weasyprint import HTML
from researcher.models import FinalReport, QualityFlag

class ReportRenderer:
    def __init__(self, output_root: Path):
        self._output_root = output_root

    def render(self, report: FinalReport, job_id: str) -> dict[str, Path]:
        md = self._to_markdown(report)
        html = self._md_to_html(md)

        slug = job_id[:8]
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        base = self._output_root / "reports" / f"{slug}_{ts}"
        base.parent.mkdir(parents=True, exist_ok=True)

        md_path = base.with_suffix(".md")
        pdf_path = base.with_suffix(".pdf")
        md_path.write_text(md, encoding="utf-8")
        HTML(string=html).write_pdf(str(pdf_path))

        return {"markdown": md_path, "pdf": pdf_path}

    def _to_markdown(self, report: FinalReport) -> str:
        lines = []

        # Quality flag banner
        if report.quality_flags:
            flags = ", ".join(f.value for f in report.quality_flags)
            lines += [f"> ⚠️ **Quality Flags**: {flags}", "",
                      f"> This report has {report.source_count} usable sources. "
                      f"Treat findings with appropriate caution.", ""]

        lines += [f"# {report.title}", "",
                  f"*Generated: {report.generated_at.isoformat()}*", "",
                  "## Executive Summary", "", report.executive_summary, ""]

        for section in report.sections:
            lines += [f"## {section.heading}", "", section.body, ""]

            # Conflict callout boxes
            for cc in section.conflict_callouts:
                lines += [
                    "---",
                    f"**⚡ Conflicting Evidence: {cc.subject}**",
                    "",
                    f"| Source A | Source B |",
                    f"|----------|----------|",
                    f"| {cc.claim_a} ([source]({cc.source_a_url})) "
                    f"| {cc.claim_b} ([source]({cc.source_b_url})) |",
                    "",
                    "---", "",
                ]

        # References section
        lines += ["## References", ""]
        for ref in report.references:
            lines.append(
                f"- **[{ref.ref_id}]** {ref.title}. "
                f"<{ref.url}> *(retrieved {ref.retrieved_at.date()})*"
            )

        return "\n".join(lines)

    def _md_to_html(self, md: str) -> str:
        import markdown
        css = """
        body { font-family: Georgia, serif; max-width: 820px; margin: 40px auto;
               color: #222; line-height: 1.7; }
        h1, h2, h3 { font-family: system-ui, sans-serif; }
        blockquote { background: #fff8dc; border-left: 4px solid #e6ac00;
                     padding: 12px 16px; margin: 16px 0; }
        table { border-collapse: collapse; width: 100%; margin: 16px 0; }
        td, th { border: 1px solid #ccc; padding: 8px 12px; }
        hr { border: none; border-top: 1px solid #ddd; }
        """
        body = markdown.markdown(md, extensions=["tables", "fenced_code"])
        return f"<html><head><style>{css}</style></head><body>{body}</body></html>"
5.10 Job Manager (pipeline/job_manager.py)
python
import asyncio, uuid
from datetime import datetime, timezone
from researcher.models import QualityFlag
from researcher.database import JobStore

class JobManager:
    def __init__(self, settings, store: JobStore, semaphore: asyncio.Semaphore,
                 search_engine, content_processor_factory,
                 summarizer, conflict_detector,
                 synthesis_engine, citation_verifier, report_renderer):
        self._settings = settings
        self._store = store
        self._sem = semaphore
        # ... store all components

    async def submit(self, topic: str) -> str:
        job_id = str(uuid.uuid4())
        await self._store.create_job(job_id, topic)
        asyncio.create_task(self._run(job_id, topic))
        return job_id

    async def submit_batch(self, topics: list[str]) -> list[str]:
        return [await self.submit(t) for t in topics]

    async def _run(self, job_id: str, topic: str):
        async with self._sem:
            await self._store.set_status(job_id, "running")
            try:
                # Stage 1: Search
                results = await self._search_engine.search(
                    topic, n=self._settings.search.results_per_query,
                    job_id=job_id, stage="search"
                )
                # Stage 2: Process
                processor = self._content_processor_factory(job_id)
                chunks, quality_flags = processor.process(results)

                # Stage 3: Summarize
                summaries = await self._summarizer.summarize_all(chunks, job_id)

                if not summaries:
                    quality_flags.append(QualityFlag.PARTIAL_RESULTS)

                # Stage 4: Detect conflicts
                conflicts = await self._conflict_detector.detect(summaries, job_id)

                # Stage 5: Synthesize
                report = await self._synthesis_engine.synthesize(
                    topic, summaries, conflicts, quality_flags, job_id
                )
                # Stage 6: Verify citations
                report = await self._citation_verifier.verify(report, summaries, job_id)

                # Stage 7: Render
                paths = self._report_renderer.render(report, job_id)

                await self._store.set_complete(job_id, paths["markdown"], report.quality_flags)

            except Exception as exc:
                await self._store.set_failed(job_id, str(exc))
                raise
5.11 CLI Entry Point (__main__.py)
python
import typer, asyncio
from pathlib import Path
from researcher.settings import load_settings
from researcher.bootstrap import build_job_manager  # wires all components

app = typer.Typer()

@app.command()
def research(
    topic: str = typer.Argument(None, help="Research topic"),
    batch: Path = typer.Option(None, "--batch", help="Path to file with one topic per line"),
    config: Path = typer.Option("config.yaml", "--config"),
):
    settings = load_settings(config)
    manager = build_job_manager(settings)

    if batch:
        topics = [line.strip() for line in batch.read_text().splitlines() if line.strip()]
        typer.echo(f"Submitting {len(topics)} queries...")
        asyncio.run(_run_batch(manager, topics))
    elif topic:
        asyncio.run(_run_single(manager, topic))
    else:
        typer.echo("Provide a topic or --batch file.", err=True)
        raise typer.Exit(1)

async def _run_single(manager, topic: str):
    job_id = await manager.submit(topic)
    typer.echo(f"Job {job_id} submitted. Waiting for completion...")
    # Poll job store until done
    await manager.wait_for(job_id)

async def _run_batch(manager, topics: list[str]):
    job_ids = await manager.submit_batch(topics)
    typer.echo(f"Submitted {len(job_ids)} jobs. Waiting...")
    await manager.wait_for_all(job_ids)

if __name__ == "__main__":
    app()
6. Testing Strategy
Golden rule: zero live API calls in CI. Every external boundary has a fixture layer.

Fixture strategy (tests/conftest.py)
python
import pytest, json
from pathlib import Path
from unittest.mock import AsyncMock

FIXTURES = Path(__file__).parent / "fixtures"

@pytest.fixture
def tavily_response():
    return json.loads((FIXTURES / "tavily_search_response.json").read_text())

@pytest.fixture
def mock_search_engine(tavily_response):
    engine = AsyncMock()
    engine.search.return_value = [SearchResult(**r) for r in tavily_response["results"]]
    return engine

@pytest.fixture
def mock_claude_client():
    """Returns an AsyncMock whose messages.create returns recorded responses."""
    client = AsyncMock()
    responses = {
        "summarize":  (FIXTURES / "claude_summarize_response.json").read_text(),
        "synthesize": (FIXTURES / "claude_synthesize_response.json").read_text(),
        "verify":     (FIXTURES / "claude_verify_response.json").read_text(),
    }
    # Route by prompt content
    async def create(**kwargs):
        prompt = kwargs["messages"][0]["content"]
        key = "summarize" if "Summarize" in prompt else \
              "verify" if "verify" in prompt.lower() else "synthesize"
        mock_resp = AsyncMock()
        mock_resp.content = [AsyncMock(text=responses[key])]
        mock_resp.usage = AsyncMock(input_tokens=500, output_tokens=200)
        return mock_resp
    client.messages.create.side_effect = create
    return client
Key test files
tests/unit/test_content_processor.py

python
def test_deduplicates_same_url():
    results = [make_result(url="https://example.com/a", content="foo")] * 3
    chunks, flags = ContentProcessor(...).process(results)
    assert len([c for c in chunks if c.url == "https://example.com/a"]) == 1

def test_deduplicates_same_hash_different_url():
    r1 = make_result(url="https://a.com", content="same content")
    r2 = make_result(url="https://b.com", content="same content")
    chunks, _ = ContentProcessor(...).process([r1, r2])
    assert len(chunks) == 1

def test_low_confidence_flag_below_threshold():
    results = [make_result() for _ in range(2)]  # below min=3
    _, flags = ContentProcessor(min_sources=3, ...).process(results)
    assert QualityFlag.LOW_CONFIDENCE in flags

def test_relevance_ordered_truncation():
    # Budget allows only 1 source. Low-relevance source should be dropped.
    low = make_result(relevance_score=0.2, content="x" * 1000)
    high = make_result(relevance_score=0.9, content="y" * 1000)
    chunks, _ = ContentProcessor(tight_budget, ...).process([low, high])
    assert all(c.relevance_score == 0.9 for c in chunks)
tests/unit/test_retry.py

python
async def test_succeeds_on_third_attempt():
    call_count = 0
    @with_retry(max_attempts=4, base_backoff=0.01)
    async def flaky(job_id, stage):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("transient")
        return "ok"
    result = await flaky(job_id="test", stage="test")
    assert result == "ok"
    assert call_count == 3

async def test_writes_dlq_on_exhaustion(mock_store):
    @with_retry(max_attempts=4, base_backoff=0.01)
    async def always_fails(job_id, stage):
        raise Exception("permanent error")
    with pytest.raises(Exception):
        await always_fails(job_id="j1", stage="search")
    mock_store.write_dead_letter.assert_called_once()
tests/conformance/test_schemas.py

python
def test_search_result_schema(tavily_response):
    for r in tavily_response["results"]:
        sr = SearchResult(**r)  # Pydantic raises if schema mismatch
        assert sr.relevance_score >= 0.0

def test_report_schema_roundtrip(claude_synthesize_fixture):
    report = FinalReport(**json.loads(claude_synthesize_fixture))
    assert len(report.sections) > 0
    assert all(len(s.citations) > 0 for s in report.sections)
tests/integration/test_pipeline.py

python
async def test_full_pipeline_produces_report(
    mock_search_engine, mock_claude_client, tmp_path
):
    settings = make_test_settings(output_root=tmp_path)
    manager = build_job_manager(
        settings,
        search_engine=mock_search_engine,
        claude_client=mock_claude_client,
    )
    job_id = await manager.submit("impact of AI on healthcare")
    await manager.wait_for(job_id, timeout=10)

    job = await manager._store.get_job(job_id)
    assert job.status == "complete"
    assert Path(job.artifact_path).with_suffix(".md").exists()
    assert Path(job.artifact_path).with_suffix(".pdf").exists()

async def test_pipeline_flags_low_confidence_with_few_sources(
    mock_search_engine_few_results, mock_claude_client, tmp_path
):
    # Fixture returns only 2 results
    ...
    md_content = Path(job.artifact_path).read_text()
    assert "LOW_CONFIDENCE" in md_content
    assert "⚠️" in md_content
7. Artifact Cleanup Job (infra/cleanup.py)
python
import asyncio
from pathlib import Path
from datetime import datetime, timezone, timedelta
from researcher.infra.notifier import get_logger

log = get_logger()

async def run_cleanup(settings):
    """Scheduled nightly. Call from a long-running supervisor loop."""
    now = datetime.now(timezone.utc)
    root = Path(settings.storage.output_root)

    intermediate_cutoff = now - timedelta(days=settings.storage.intermediate_ttl_days)
    report_cutoff = now - timedelta(days=settings.storage.report_ttl_days)

    deleted_count = 0
    for path in (root / "intermediates").rglob("*"):
        if path.is_file():
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            if mtime < intermediate_cutoff:
                path.unlink()
                deleted_count += 1

    for path in (root / "reports").rglob("*"):
        if path.is_file() and path.suffix in {".md", ".pdf"}:
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            if mtime < report_cutoff:
                path.unlink()
                deleted_count += 1

    log.info("cleanup_complete", deleted_files=deleted_count,
             intermediate_ttl_days=settings.storage.intermediate_ttl_days,
             report_ttl_days=settings.storage.report_ttl_days)
8. Dependency Manifest (pyproject.toml)
toml
[project]
name = "researcher"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
  "anthropic>=0.28",          # Claude API client
  "tavily-python>=0.3",       # Search & retrieval
  "pydantic>=2.0",            # Schema validation
  "pydantic-settings>=2.0",   # Config management
  "sqlalchemy[asyncio]>=2.0", # Async ORM
  "aiosqlite>=0.19",          # SQLite async driver
  "typer>=0.12",              # CLI
  "structlog>=24.0",          # Structured JSON logging
  "markdown>=3.6",            # MD → HTML for PDF rendering
  "weasyprint>=61.0",         # HTML → PDF
  "pyyaml>=6.0",              # config.yaml loading
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0",
  "pytest-asyncio>=0.23",
  "pytest-cov>=5.0",
]

[project.scripts]
researcher = "researcher.__main__:app"
9. Known Risks & Mitigations Summary
Risk	Severity	Mitigation in this design
API rate limits cascade	0.8	Per-API token buckets + exponential backoff + DLQ
LLM hallucination	0.7	Post-hoc citation verifier pass; prompt rules enforcing grounded generation
API cost runaway	0.7	Per-query token budget; relevance-ordered truncation; daily cost alert threshold
Paywalled/poor sources	0.65	Quality flag on low source count; partial-results flag if summaries fail
Low source coverage	0.65	Minimum source threshold (3); LOW_CONFIDENCE flag + report header warning
Semantic dedup misses	0.6	Accepted tradeoff for speed; flagged in architecture documentation
DLQ growth unbounded	0.55	DLQ table queryable via SQLite; structured log alerts; manual replay path documented
10. Operational Notes
First-run setup:

bash
cp .env.example .env          # Add TAVILY_API_KEY and ANTHROPIC_API_KEY
pip install -e ".[dev]"
python -m researcher --help
Running tests:

bash
pytest tests/ -v --cov=researcher  # All tests run offline via fixtures
Single query:

bash
python -m researcher "impact of AI on healthcare"
Batch mode (200 queries):

bash
python -m researcher --batch queries.txt
# Outputs progress to stdout; reports written to ./outputs/reports/
Monitoring:

bash
tail -f outputs/logs/researcher.log | python -m json.tool
# Watch for "level": "error" (DLQ entries) and "level": "warning" (cost threshold)
Tuning concurrency and cost for your machine: Edit config.yaml — start with max_pipeline_slots: 4 and daily_alert_threshold_usd: 10.00, observe log output for the first 50 queries, then increase slots if neither API nor machine resources are saturated.


