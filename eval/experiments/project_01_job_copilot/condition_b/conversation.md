cursor: Exploring the workspace for context, then asking critical clarifying questions before we build the Phase 1 decision graph.
Workspace is empty — greenfield project. Asking a few high-impact questions that determine architecture, legal exposure, and reliability.

What should the overnight pipeline do after filtering relevant jobs? (This drives browser automation depth, CAPTCHA handling, and ToS risk.)
Above + prepare per-job application packets (cover letter text, answers file) but human submits
How should authenticated boards (LinkedIn, Wellfound, etc.) obtain sessions for unattended runs?
Dedicated browser user-data-dir / Playwright storageState refreshed periodically by a short manual login helper
Where will the overnight job run? (Affects IP reputation, scheduling, and headful vs headless tradeoffs.)
Same machine but packaged in Docker for reproducibility

Here’s Phase 1 after your answers: scope is discover → DB → filter → tailored resume PDF → application packet (cover letter + structured answers) with human submit; auth is Playwright storageState / persistent context with a periodic manual refresh helper; runtime is local Docker on your machine.
Pushback (before locking this in)
Docker on macOS + “log in once in a real browser profile” is often the brittle part: GUI login flows and persistent profiles are much smoother on the host than inside a typical Linux container on Mac (no real display, profile path quirks, anti-bot signals). A stronger pattern is usually: orchestration + DB in Docker, but Playwright uses a host-mounted profile directory (or a small host-side “login refresh” script that writes storageState.json into a volume the container consumes). If you want maximum reliability, we should treat “everything in one container including interactive login” as a non-goal unless you explicitly want that pain.
I’ve captured that tension as assumptions/risks in the graph below.
[GRAPH UPDATE]
{
  "nodes": [
    {
      "id": "obj_overnight_prep",
      "type": "objective",
      "label": "Overnight job prep pipeline",
      "description": "Unattended discovery and ranking of roles, persistent storage with deduplication, tailored resumes and application packets; human performs final submission."
    },
    {
      "id": "req_multi_source",
      "type": "requirement",
      "label": "Multi-board ingestion",
      "description": "Collect listings from multiple job boards with site-specific behavior.",
      "is_functional": true
    },
    {
      "id": "req_auth_sites",
      "type": "requirement",
      "label": "Authenticated sources",
      "description": "Ingest from boards that require login sessions (e.g., LinkedIn, Wellfound).",
      "is_functional": true
    },
    {
      "id": "req_dynamic_js",
      "type": "requirement",
      "label": "Dynamic pages and bot friction",
      "description": "Handle JS-rendered listings and practical bot-detection mitigations within ethical/legal constraints chosen by the operator.",
      "is_functional": true
    },
    {
      "id": "req_dedup_persist",
      "type": "requirement",
      "label": "Persistent deduplicated store",
      "description": "Store normalized listings in a database and dedupe across runs using stable keys.",
      "is_functional": true
    },
    {
      "id": "req_profile_match",
      "type": "requirement",
      "label": "Profile relevance filtering",
      "description": "Filter jobs against skills, seniority, and role preferences with explainable scores or reasons.",
      "is_functional": true
    },
    {
      "id": "req_tailored_resume_pdf",
      "type": "requirement",
      "label": "Tailored resume PDFs",
      "description": "For each relevant job, generate a formatted PDF resume variant aligned to that posting.",
      "is_functional": true
    },
    {
      "id": "req_app_packet",
      "type": "requirement",
      "label": "Application packet artifacts",
      "description": "Produce per-job artifacts such as cover letter text and answers/cheatsheet for forms, suitable for human submission.",
      "is_functional": true
    },
    {
      "id": "req_unattended_recovery",
      "type": "requirement",
      "label": "Unattended execution with recovery",
      "description": "Run overnight with retries, resumability, checkpointing, and summarized error reporting without manual babysitting.",
      "is_functional": true
    },
    {
      "id": "req_offline_tests",
      "type": "requirement",
      "label": "Offline scraping validation",
      "description": "Automated tests validate parsing/normalization using fixtures, not live network calls.",
      "is_functional": true
    },
    {
      "id": "dec_scope_human_submit",
      "type": "decision",
      "label": "Human submits applications",
      "description": "Automate discovery, tailoring, and packet generation; stop before autonomous submission.",
      "rationale": "Materially reduces CAPTCHA/phone-verification surfaces and keeps the automation posture closer to assistive tooling.",
      "alternatives_considered": [
        "Fully automated submission where possible",
        "Discovery + resume only (no cover letter/answers)"
      ]
    },
    {
      "id": "dec_auth_playwright_storage",
      "type": "decision",
      "label": "Playwright sessions via persistent storage",
      "description": "Use Playwright persistent context and/or saved storage state refreshed periodically by a login helper.",
      "rationale": "Matches authenticated web apps better than naive unauthenticated scraping; can be scripted and audited.",
      "alternatives_considered": [
        "Manual cookie injection only",
        "Official APIs/alerts first with scraping fallback"
      ]
    },
    {
      "id": "dec_runtime_local_docker",
      "type": "decision",
      "label": "Local Docker packaging",
      "description": "Package the pipeline for reproducible runs on a personal machine using Docker.",
      "rationale": "Locks dependencies and simplifies onboarding; pairs well with volume-mounted state and logs.",
      "alternatives_considered": [
        "Native venv on host",
        "Remote cloud runner"
      ]
    },
    {
      "id": "dec_stack_python_playwright",
      "type": "decision",
      "label": "Python orchestration + Playwright",
      "description": "Implement the pipeline in Python with Playwright for browser automation and pytest for tests.",
      "rationale": "Strong ecosystem for scraping workflows, PDF generation, and data tooling; Playwright is a pragmatic dynamic-site choice.",
      "alternatives_considered": [
        "Node.js with Playwright",
        "Rust + headless browser automation"
      ]
    },
    {
      "id": "dec_store_sqlite",
      "type": "decision",
      "label": "SQLite as primary database",
      "description": "Use SQLite (via SQLAlchemy or similar) on a mounted volume for listings and run metadata.",
      "rationale": "Single-operator local pipeline with minimal ops overhead; easy backups via file copy.",
      "alternatives_considered": [
        "PostgreSQL in Docker",
        "DuckDB"
      ]
    },
    {
      "id": "iface_normalized_job",
      "type": "interface",
      "label": "Normalized job record",
      "description": "Canonical fields and provenance for a listing after adapter parsing.",
      "contract": "{source, source_job_id?, canonical_url, title, company, location?, remote?, description_text, posted_at?, scraped_at, raw_ref?, content_hash}"
    },
    {
      "id": "iface_user_profile",
      "type": "interface",
      "label": "User profile model",
      "description": "Structured preferences used for filtering and tailoring outputs.",
      "contract": "{skills[], seniority, role_titles[], industries[], locations[], must_have[], avoid[], compensation?, narrative?}"
    },
    {
      "id": "comp_orchestrator",
      "type": "component",
      "label": "Pipeline orchestrator",
      "description": "Schedules stages, manages retries, checkpoints, and aggregates run reports.",
      "file_refs": [],
      "has_tests": false
    },
    {
      "id": "comp_scraper_adapters",
      "type": "component",
      "label": "Site scraper adapters",
      "description": "Per-board modules implementing discovery/pagination and mapping to the normalized job interface.",
      "file_refs": [],
      "has_tests": false
    },
    {
      "id": "comp_store",
      "type": "component",
      "label": "Persistence layer",
      "description": "Migrations, dedupe upserts, and querying for downstream filtering and artifact generation.",
      "file_refs": [],
      "has_tests": false
    },
    {
      "id": "comp_relevance_engine",
      "type": "component",
      "label": "Relevance scoring",
      "description": "Implements filtering and ranking against the user profile with explainability metadata.",
      "file_refs": [],
      "has_tests": false
    },
    {
      "id": "comp_pdf_factory",
      "type": "component",
      "label": "Resume PDF generator",
      "description": "Renders tailored resume PDFs from templates plus per-job emphasis rules.",
      "file_refs": [],
      "has_tests": false
    },
    {
      "id": "comp_packet_assembler",
      "type": "component",
      "label": "Application packet assembler",
      "description": "Generates cover letter drafts and structured answer snippets/files per job.",
      "file_refs": [],
      "has_tests": false
    },
    {
      "id": "risk_bot_and_tos",
      "type": "risk",
      "label": "Bot detection and platform policy",
      "description": "Sites may block automation or change markup; scraping may conflict with terms and account safety.",
      "severity": 0.9
    },
    {
      "id": "risk_docker_mac_auth",
      "type": "risk",
      "label": "Docker-on-Mac auth ergonomics",
      "description": "Interactive login and realistic browser fingerprints may be harder inside containers on macOS than on host-mounted profiles.",
      "severity": 0.72
    },
    {
      "id": "risk_session_instability",
      "type": "risk",
      "label": "Session expiry mid-run",
      "description": "Long unattended runs may hit forced re-auth, security challenges, or token rotation.",
      "severity": 0.68
    },
    {
      "id": "asm_operator_tos_acceptance",
      "type": "assumption",
      "label": "Operator accepts platform risk",
      "description": "Assumes the operator knowingly accepts account restriction risk and legal/ToS uncertainty for chosen boards.",
      "confidence": 0.45,
      "validated": false
    },
    {
      "id": "asm_profile_volume_mount",
      "type": "assumption",
      "label": "Persistent profile/state via volumes",
      "description": "Assumes a workable approach exists to share Playwright storage state between a refresh helper and batch scraper (often host-mounted volume).",
      "confidence": 0.55,
      "validated": false
    },
    {
      "id": "asm_session_duration",
      "type": "assumption",
      "label": "Sessions last through typical runs",
      "description": "Assumes refreshed storage state remains valid for an overnight run window under normal platform behavior.",
      "confidence": 0.62,
      "validated": false
    },
    {
      "id": "tst_adapter_fixture_suite",
      "type": "test",
      "label": "Adapter parsing fixture tests",
      "description": "pytest tests load saved HTML/JSON fixtures and assert normalized job outputs and dedupe keys.",
      "test_type": "unit",
      "status": "planned"
    }
  ],
  "edges": [
    { "type": "motivated_by", "source_id": "dec_scope_human_submit", "target_id": "obj_overnight_prep" },
    { "type": "motivated_by", "source_id": "dec_auth_playwright_storage", "target_id": "obj_overnight_prep" },
    { "type": "motivated_by", "source_id": "dec_runtime_local_docker", "target_id": "obj_overnight_prep" },
    { "type": "motivated_by", "source_id": "dec_stack_python_playwright", "target_id": "obj_overnight_prep" },
    { "type": "motivated_by", "source_id": "dec_store_sqlite", "target_id": "obj_overnight_prep" },
    { "type": "assumes", "source_id": "dec_auth_playwright_storage", "target_id": "asm_profile_volume_mount" },
    { "type": "assumes", "source_id": "dec_auth_playwright_storage", "target_id": "asm_session_duration" },
    { "type": "assumes", "source_id": "dec_stack_python_playwright", "target_id": "asm_operator_tos_acceptance" },
    { "type": "implements", "source_id": "comp_scraper_adapters", "target_id": "req_multi_source" },
    { "type": "implements", "source_id": "comp_scraper_adapters", "target_id": "req_auth_sites" },
    { "type": "implements", "source_id": "comp_scraper_adapters", "target_id": "req_dynamic_js" },
    { "type": "implements", "source_id": "comp_store", "target_id": "req_dedup_persist" },
    { "type": "implements", "source_id": "comp_relevance_engine", "target_id": "req_profile_match" },
    { "type": "implements", "source_id": "comp_pdf_factory", "target_id": "req_tailored_resume_pdf" },
    { "type": "implements", "source_id": "comp_packet_assembler", "target_id": "req_app_packet" },
    { "type": "implements", "source_id": "comp_orchestrator", "target_id": "req_unattended_recovery" },
    { "type": "implements", "source_id": "tst_adapter_fixture_suite", "target_id": "req_offline_tests" },
    { "type": "exposes", "source_id": "comp_scraper_adapters", "target_id": "iface_normalized_job" },
    { "type": "consumes", "source_id": "comp_store", "target_id": "iface_normalized_job" },
    { "type": "consumes", "source_id": "comp_relevance_engine", "target_id": "iface_normalized_job" },
    { "type": "consumes", "source_id": "comp_relevance_engine", "target_id": "iface_user_profile" },
    { "type": "consumes", "source_id": "comp_pdf_factory", "target_id": "iface_user_profile" },
    { "type": "consumes", "source_id": "comp_packet_assembler", "target_id": "iface_user_profile" },
    { "type": "depends_on", "source_id": "comp_orchestrator", "target_id": "comp_scraper_adapters" },
    { "type": "depends_on", "source_id": "comp_orchestrator", "target_id": "comp_store" },
    { "type": "depends_on", "source_id": "comp_orchestrator", "target_id": "comp_relevance_engine" },
    { "type": "depends_on", "source_id": "comp_orchestrator", "target_id": "comp_pdf_factory" },
    { "type": "depends_on", "source_id": "comp_orchestrator", "target_id": "comp_packet_assembler" },
    { "type": "depends_on", "source_id": "comp_pdf_factory", "target_id": "comp_store" },
    { "type": "depends_on", "source_id": "comp_packet_assembler", "target_id": "comp_store" },
    { "type": "conflicts_with", "source_id": "risk_bot_and_tos", "target_id": "req_auth_sites" },
    { "type": "conflicts_with", "source_id": "risk_bot_and_tos", "target_id": "req_dynamic_js" },
    { "type": "conflicts_with", "source_id": "risk_docker_mac_auth", "target_id": "dec_runtime_local_docker" },
    { "type": "invalidates", "source_id": "risk_session_instability", "target_id": "asm_session_duration" },
    { "type": "verifies", "source_id": "tst_adapter_fixture_suite", "target_id": "comp_scraper_adapters" },
    { "type": "verifies", "source_id": "tst_adapter_fixture_suite", "target_id": "iface_normalized_job" },
    { "type": "guards_against", "source_id": "tst_adapter_fixture_suite", "target_id": "risk_bot_and_tos" }
  ]
}
[/GRAPH UPDATE]
Graph gaps this turn
Low-confidence assumptions (asm_operator_tos_acceptance, asm_profile_volume_mount): need your explicit stance and preferred login/storage layout.
High-severity risk risk_bot_and_tos: fixture tests only guard parsing drift, not live blocks—need agreed mitigations (rate limits, backoff, circuit breakers, “degraded mode”).
Decision pressure-test: dec_stack_python_playwright is provisional until you confirm language preference and whether LLM-based tailoring is in scope (affects cost, determinism, and testing).

What is your acceptable posture toward authenticated scraping/automation on
LinkedIn/Wellfound-like sites? (This does not change whether risks exist; it changes how aggressively we design mitigations and logging.)
Conservative: minimize automation signals, strict rate limits, prefer manual refresh and smaller batches
Which auth refresh shape do you want as the default? (We can still support both, but one should be canonical.)
Not sure - pick the most reliable for macOS
Docker
How should resume/cover-letter tailoring be produced?
LLM-assisted rewriting with strict schemas and offline tests for formatting constraints

Locking in conservative automation, canonical macOS-Docker auth via host helper + shared volume (most reliable default), and optional LLM tailoring with strict structured outputs. Updating the cumulative graph for end of Phase 1 / start of Phase 2, then asking focused Phase 2 questions.
[GRAPH UPDATE]
[/GRAPH UPDATE]
Graph review (this phase)
guards_against from decision nodes: The schema shows guards_against from test → risk. I used dec_conservative_automation and dec_auth_host_volume_canonical as guards—conceptually they’re mitigations, not tests. In the next graph revision I’ll either add explicit mitigation components (rate limiter, session health check) with implements-style links, or represent mitigation as risk → decision edges if you want strict edge typing. For the final plan prose, mitigations will be explicit.
Low-confidence assumptions still open: asm_host_volume_auth (0.74), asm_session_duration (0.66), asm_llm_available_when_enabled (0.63)—worth validating via your environment and provider choice.

Which LLM integration should be the default for optional tailoring? (You can add more later; this choice drives SDK deps and secrets layout.)
playwright to simulate Ul on chatgpt. have option for logging in once if auth json not present
What is the canonical source resume format the PDF generator should treat as ground truth?
DOCX template uploaded into a mounted volume
Pick an MVP board set for v1 adapters (others stubbed behind interfaces).
option B but for job boards, have LLM assisted dynamic web scraping as different job boards will have different layouts. use playwright for this too

Recording a major architecture shift: tailoring via Playwright-driven ChatGPT web UI (with one-time login when auth state is missing), canonical resume as a mounted DOCX template, MVP boards: LinkedIn + Wellfound + one public ATS-style board, and LLM-assisted adaptive scraping for heterogeneous layouts—still using Playwright for execution.
Pushback: Automating the ChatGPT website is typically more brittle and policy-sensitive than calling an API with the same structured-output discipline. The graph encodes that as a high-severity risk; we should still design a deterministic fallback path (templates/rules) so overnight runs don’t hard-fail when the UI changes.
[GRAPH UPDATE]
{
  "nodes": [
    {
      "id": "obj_overnight_prep",
      "type": "objective",
      "label": "Overnight job prep pipeline",
      "description": "Unattended discovery and ranking of roles, persistent storage with deduplication, tailored resumes and application packets; human performs final submission."
    },
    {
      "id": "req_multi_source",
      "type": "requirement",
      "label": "Multi-board ingestion",
      "description": "Collect listings from multiple job boards with site-specific behavior.",
      "is_functional": true
    },
    {
      "id": "req_auth_sites",
      "type": "requirement",
      "label": "Authenticated sources",
      "description": "Ingest from boards that require login sessions (e.g., LinkedIn, Wellfound).",
      "is_functional": true
    },
    {
      "id": "req_dynamic_js",
      "type": "requirement",
      "label": "Dynamic pages and bot friction",
      "description": "Handle JS-rendered listings and practical bot-detection mitigations within operator-chosen constraints.",
      "is_functional": true
    },
    {
      "id": "req_dedup_persist",
      "type": "requirement",
      "label": "Persistent deduplicated store",
      "description": "Store normalized listings in a database and dedupe across runs using stable keys.",
      "is_functional": true
    },
    {
      "id": "req_profile_match",
      "type": "requirement",
      "label": "Profile relevance filtering",
      "description": "Filter jobs against skills, seniority, and role preferences with explainable scores or reasons.",
      "is_functional": true
    },
    {
      "id": "req_tailored_resume_pdf",
      "type": "requirement",
      "label": "Tailored resume PDFs",
      "description": "For each relevant job, generate a formatted PDF resume variant aligned to that posting.",
      "is_functional": true
    },
    {
      "id": "req_app_packet",
      "type": "requirement",
      "label": "Application packet artifacts",
      "description": "Produce per-job artifacts such as cover letter text and answers/cheatsheet for forms, suitable for human submission.",
      "is_functional": true
    },
    {
      "id": "req_unattended_recovery",
      "type": "requirement",
      "label": "Unattended execution with recovery",
      "description": "Run overnight with retries, resumability, checkpointing, and summarized error reporting without manual babysitting.",
      "is_functional": true
    },
    {
      "id": "req_offline_tests",
      "type": "requirement",
      "label": "Offline scraping validation",
      "description": "Automated tests validate parsing/normalization using fixtures, not live network calls.",
      "is_functional": true
    },
    {
      "id": "dec_scope_human_submit",
      "type": "decision",
      "label": "Human submits applications",
      "description": "Automate discovery, tailoring, and packet generation; stop before autonomous submission.",
      "rationale": "Reduces CAPTCHA surfaces and keeps automation closer to assistive tooling.",
      "alternatives_considered": [
        "Fully automated submission where possible",
        "Discovery + resume only"
      ]
    },
    {
      "id": "dec_conservative_automation",
      "type": "decision",
      "label": "Conservative automation defaults",
      "description": "Prefer smaller batches, strict rate limits, backoff/jitter, and periodic manual session refresh.",
      "rationale": "Operator preference to reduce aggressive automation signals on authenticated sources.",
      "alternatives_considered": [
        "Throughput-first scraping",
        "Audit-only logging without behavioral throttles"
      ]
    },
    {
      "id": "dec_auth_playwright_storage",
      "type": "decision",
      "label": "Playwright session state on disk",
      "description": "Persist authentication using Playwright storageState JSON and/or profile directories, refreshed by a login helper when invalid.",
      "rationale": "Standard Playwright approach for authenticated sites; supports 'login once if missing' flows.",
      "alternatives_considered": [
        "Manual cookie paste only",
        "Third-party session brokers"
      ]
    },
    {
      "id": "dec_auth_host_volume_canonical",
      "type": "decision",
      "label": "Host refresh + shared volume canonical path",
      "description": "Default: host-side refresh writes storageState into a directory mounted into Docker batch jobs.",
      "rationale": "Most reliable on macOS Docker versus in-container interactive browser setup.",
      "alternatives_considered": [
        "All-in-container VNC/X11 login",
        "Separate Linux runner"
      ]
    },
    {
      "id": "dec_runtime_local_docker",
      "type": "decision",
      "label": "Local Docker packaging",
      "description": "Run the batch pipeline in Docker on a personal machine with mounted volumes for state, DB, artifacts, and templates.",
      "rationale": "Reproducible dependencies; pairs with volume-mounted secrets and outputs.",
      "alternatives_considered": [
        "Native venv only",
        "Cloud VM runner"
      ]
    },
    {
      "id": "dec_stack_python_playwright",
      "type": "decision",
      "label": "Python orchestration + Playwright",
      "description": "Python service architecture with Playwright automation and pytest-based tests.",
      "rationale": "Good fit for data/sqlite/pdf/docx tooling and a single-language codebase.",
      "alternatives_considered": [
        "Node.js + Playwright",
        "Polyglot split services"
      ]
    },
    {
      "id": "dec_store_sqlite",
      "type": "decision",
      "label": "SQLite primary database",
      "description": "SQLite on a mounted volume with migrations for listings, runs, checkpoints, and artifact pointers.",
      "rationale": "Low ops overhead for a single-user local pipeline; easy backup via file copy.",
      "alternatives_considered": [
        "Postgres container",
        "DuckDB"
      ]
    },
    {
      "id": "dec_tailoring_chatgpt_ui",
      "type": "decision",
      "label": "Tailoring via ChatGPT web UI automation",
      "description": "Use Playwright to drive the ChatGPT web UI to produce structured tailoring fields validated against schemas.",
      "rationale": "Matches user preference to use ChatGPT without mandating a particular vendor API SDK as the primary path.",
      "alternatives_considered": [
        "OpenAI/Anthropic HTTP API as primary",
        "Deterministic-only tailoring"
      ]
    },
    {
      "id": "dec_resume_docx_canonical",
      "type": "decision",
      "label": "Canonical resume is a DOCX template",
      "description": "Authoritative resume content starts as a DOCX on a mounted volume; PDFs are rendered from programmatic fills.",
      "rationale": "Matches user workflow preference; DOCX is a practical interchange format for edits.",
      "alternatives_considered": [
        "YAML/Markdown source",
        "JSON Resume",
        "LaTeX source"
      ]
    },
    {
      "id": "dec_mvp_li_wf_ats",
      "type": "decision",
      "label": "MVP boards: LinkedIn + Wellfound + one ATS-like public board",
      "description": "Initial adapters target three categories while keeping a shared normalized contract.",
      "rationale": "Covers authenticated and semi-standard listing pages while staying bounded for v1.",
      "alternatives_considered": [
        "Two authenticated boards only",
        "RSS-first MVP"
      ]
    },
    {
      "id": "dec_scrape_llm_planner",
      "type": "decision",
      "label": "LLM-assisted scrape planning with Playwright execution",
      "description": "For heterogeneous layouts, an LLM proposes an extraction plan from captured DOM/context; Playwright executes and results are validated before persistence.",
      "rationale": "Addresses 'different layouts per board' without hand-writing infinite one-off selectors for every variant.",
      "alternatives_considered": [
        "Hand-written adapters only",
        "Pure CV/vision scraping without structured plans"
      ]
    },
    {
      "id": "iface_normalized_job",
      "type": "interface",
      "label": "Normalized job record",
      "description": "Canonical fields and provenance for a listing after adapter parsing.",
      "contract": "{source, source_job_id?, canonical_url, title, company, location?, remote?, description_text, posted_at?, scraped_at, raw_ref?, content_hash}"
    },
    {
      "id": "iface_user_profile",
      "type": "interface",
      "label": "User profile model",
      "description": "Structured preferences used for filtering and tailoring outputs.",
      "contract": "{skills[], seniority, role_titles[], industries[], locations[], must_have[], avoid[], compensation?, narrative?}"
    },
    {
      "id": "iface_tailored_artifact",
      "type": "interface",
      "label": "Tailoring payload contract",
      "description": "Validated structured output that drives DOCX fill and packet text assembly.",
      "contract": "{highlights[], role_title_override?, summary_bullets[], cover_letter_paragraphs[], form_answers[{q_key,q_text,answer}], claims_used[]}"
    },
    {
      "id": "iface_scrape_plan",
      "type": "interface",
      "label": "Scrape execution plan",
      "description": "Machine-checkable steps/selectors/heuristics the Playwright runner executes, produced or revised by the planner.",
      "contract": "{version, site_key, steps:[{action,selector?,wait_for?,extract:{fields[]}}], validation:{min_items,required_fields[]}}"
    },
    {
      "id": "iface_resume_docx",
      "type": "interface",
      "label": "Resume DOCX template contract",
      "description": "Defines placeholder fields mapping from profile + tailoring payload to DOCX template regions.",
      "contract": "{template_path, placeholders:{summary,experience_bullets,skills,title?}}"
    },
    {
      "id": "comp_orchestrator",
      "type": "component",
      "label": "Pipeline orchestrator",
      "description": "Stage scheduling, retries, checkpoints, run reports, and per-site circuit breaking.",
      "file_refs": [],
      "has_tests": false
    },
    {
      "id": "comp_rate_limiter",
      "type": "component",
      "label": "Rate limit and jitter policy",
      "description": "Centralized throttles, concurrency caps, and cooldowns per domain for conservative operation.",
      "file_refs": [],
      "has_tests": false
    },
    {
      "id": "comp_scraper_adapters",
      "type": "component",
      "label": "Playwright scrape executor",
      "description": "Executes scrape plans, collects listings, normalizes to iface_normalized_job, and emits artifacts for debugging.",
      "file_refs": [],
      "has_tests": false
    },
    {
      "id": "comp_scrape_planner",
      "type": "component",
      "label": "LLM scrape planner",
      "description": "Produces and updates iface_scrape_plan from page captures; never persists unvalidated extractions.",
      "file_refs": [],
      "has_tests": false
    },
    {
      "id": "comp_store",
      "type": "component",
      "label": "Persistence layer",
      "description": "Migrations, dedupe upserts, run metadata, and artifact storage pointers.",
      "file_refs": [],
      "has_tests": false
    },
    {
      "id": "comp_relevance_engine",
      "type": "component",
      "label": "Relevance scoring",
      "description": "Filters and ranks jobs against iface_user_profile with explainability metadata.",
      "file_refs": [],
      "has_tests": false
    },
    {
      "id": "comp_docx_renderer",
      "type": "component",
      "label": "DOCX render and PDF export",
      "description": "Fills the mounted DOCX template using python-docx/docxtpl patterns and exports PDF via a stable headless conversion path.",
      "file_refs": [],
      "has_tests": false
    },
    {
      "id": "comp_packet_assembler",
      "type": "component",
      "label": "Application packet assembler",
      "description": "Writes cover letter and form-answer files per job from validated tailoring payloads.",
      "file_refs": [],
      "has_tests": false
    },
    {
      "id": "comp_chatgpt_ui_tailor",
      "type": "component",
      "label": "ChatGPT UI tailoring driver",
      "description": "Playwright automation of ChatGPT web UI with storageState login; parses model output into iface_tailored_artifact with schema validation and retries.",
      "file_refs": [],
      "has_tests": false
    },
    {
      "id": "risk_bot_and_tos",
      "type": "risk",
      "label": "Bot detection and platform policy",
      "description": "Boards and auxiliary web UIs may block automation; behavior may conflict with terms and threaten accounts.",
      "severity": 0.9
    },
    {
      "id": "risk_chatgpt_ui_fragility",
      "type": "risk",
      "label": "ChatGPT UI breakage and account friction",
      "description": "UI changes, A/B tests, CAPTCHAs, or policy enforcement can break tailoring automation independent of job boards.",
      "severity": 0.88
    },
    {
      "id": "risk_scrape_plan_unsafe",
      "type": "risk",
      "label": "Unsafe or hallucinated scrape plans",
      "description": "LLM-proposed selectors may misfire, silently scrape wrong regions, or over-collect data without strict validation gates.",
      "severity": 0.78
    },
    {
      "id": "risk_docker_mac_auth",
      "type": "risk",
      "label": "Docker-on-Mac auth ergonomics",
      "description": "Session refresh and browser realism may still be awkward if misconfigured mounts or permissions block state files.",
      "severity": 0.72
    },
    {
      "id": "risk_session_instability",
      "type": "risk",
      "label": "Session expiry mid-run",
      "description": "Authenticated sources may force re-auth during long runs.",
      "severity": 0.68
    },
    {
      "id": "risk_docx_pdf_fidelity",
      "type": "risk",
      "label": "DOCX/PDF fidelity loss",
      "description": "Template complexity or conversion tooling may alter layout versus manually crafted documents.",
      "severity": 0.6
    },
    {
      "id": "asm_operator_posture_conservative",
      "type": "assumption",
      "label": "Conservative throughput posture",
      "description": "Assumes operator accepts slower runs for fewer aggressive automation signals.",
      "confidence": 0.82,
      "validated": true
    },
    {
      "id": "asm_host_volume_auth",
      "type": "assumption",
      "label": "Host refresh + volume works here",
      "description": "Assumes storageState files written on the host are visible and usable inside Docker with stable paths.",
      "confidence": 0.74,
      "validated": false
    },
    {
      "id": "asm_session_duration",
      "type": "assumption",
      "label": "Sessions survive conservative batch windows",
      "description": "Assumes refreshed sessions remain valid for typical overnight slices given throttling and smaller batches.",
      "confidence": 0.66,
      "validated": false
    },
    {
      "id": "asm_chatgpt_ui_available",
      "type": "assumption",
      "label": "ChatGPT web session can be established non-interactively after first setup",
      "description": "Assumes initial headed login can create durable storageState suitable for unattended steps until expiry.",
      "confidence": 0.58,
      "validated": false
    },
    {
      "id": "asm_docx_template_maintained",
      "type": "assumption",
      "label": "DOCX template uses supported placeholder conventions",
      "description": "Assumes the user maintains a template compatible with the renderer’s placeholder and paragraph rules.",
      "confidence": 0.7,
      "validated": false
    },
    {
      "id": "tst_adapter_fixture_suite",
      "type": "test",
      "label": "Adapter and normalization fixture tests",
      "description": "pytest loads saved HTML/JSON fixtures and asserts iface_normalized_job outputs and dedupe keys without network I/O.",
      "test_type": "unit",
      "status": "planned"
    },
    {
      "id": "tst_tailoring_schema_contract",
      "type": "test",
      "label": "Tailoring schema conformance tests",
      "description": "Validates tailoring payloads against JSON Schema using stubbed ChatGPT outputs and golden cases.",
      "test_type": "conformance",
      "status": "planned"
    },
    {
      "id": "tst_scrape_plan_replay",
      "type": "test",
      "label": "Scrape plan replay tests",
      "description": "Offline replay of iface_scrape_plan against captured DOM fixtures to ensure extraction stability without live sites.",
      "test_type": "integration",
      "status": "planned"
    }
  ],
  "edges": [
    { "type": "motivated_by", "source_id": "dec_scope_human_submit", "target_id": "obj_overnight_prep" },
    { "type": "motivated_by", "source_id": "dec_conservative_automation", "target_id": "obj_overnight_prep" },
    { "type": "motivated_by", "source_id": "dec_auth_playwright_storage", "target_id": "obj_overnight_prep" },
    { "type": "motivated_by", "source_id": "dec_auth_host_volume_canonical", "target_id": "obj_overnight_prep" },
    { "type": "motivated_by", "source_id": "dec_runtime_local_docker", "target_id": "obj_overnight_prep" },
    { "type": "motivated_by", "source_id": "dec_stack_python_playwright", "target_id": "obj_overnight_prep" },
    { "type": "motivated_by", "source_id": "dec_store_sqlite", "target_id": "obj_overnight_prep" },
    { "type": "motivated_by", "source_id": "dec_tailoring_chatgpt_ui", "target_id": "obj_overnight_prep" },
    { "type": "motivated_by", "source_id": "dec_resume_docx_canonical", "target_id": "obj_overnight_prep" },
    { "type": "motivated_by", "source_id": "dec_mvp_li_wf_ats", "target_id": "obj_overnight_prep" },
    { "type": "motivated_by", "source_id": "dec_scrape_llm_planner", "target_id": "obj_overnight_prep" },
    { "type": "assumes", "source_id": "dec_conservative_automation", "target_id": "asm_operator_posture_conservative" },
    { "type": "assumes", "source_id": "dec_auth_host_volume_canonical", "target_id": "asm_host_volume_auth" },
    { "type": "assumes", "source_id": "dec_auth_playwright_storage", "target_id": "asm_session_duration" },
    { "type": "assumes", "source_id": "dec_tailoring_chatgpt_ui", "target_id": "asm_chatgpt_ui_available" },
    { "type": "assumes", "source_id": "dec_resume_docx_canonical", "target_id": "asm_docx_template_maintained" },
    { "type": "implements", "source_id": "comp_rate_limiter", "target_id": "req_dynamic_js" },
    { "type": "implements", "source_id": "comp_scraper_adapters", "target_id": "req_multi_source" },
    { "type": "implements", "source_id": "comp_scraper_adapters", "target_id": "req_auth_sites" },
    { "type": "implements", "source_id": "comp_scrape_planner", "target_id": "req_dynamic_js" },
    { "type": "implements", "source_id": "comp_store", "target_id": "req_dedup_persist" },
    { "type": "implements", "source_id": "comp_relevance_engine", "target_id": "req_profile_match" },
    { "type": "implements", "source_id": "comp_docx_renderer", "target_id": "req_tailored_resume_pdf" },
    { "type": "implements", "source_id": "comp_packet_assembler", "target_id": "req_app_packet" },
    { "type": "implements", "source_id": "comp_chatgpt_ui_tailor", "target_id": "req_tailored_resume_pdf" },
    { "type": "implements", "source_id": "comp_chatgpt_ui_tailor", "target_id": "req_app_packet" },
    { "type": "implements", "source_id": "comp_orchestrator", "target_id": "req_unattended_recovery" },
    { "type": "implements", "source_id": "tst_adapter_fixture_suite", "target_id": "req_offline_tests" },
    { "type": "implements", "source_id": "tst_scrape_plan_replay", "target_id": "req_offline_tests" },
    { "type": "implements", "source_id": "tst_tailoring_schema_contract", "target_id": "req_offline_tests" },
    { "type": "exposes", "source_id": "comp_scraper_adapters", "target_id": "iface_normalized_job" },
    { "type": "exposes", "source_id": "comp_scrape_planner", "target_id": "iface_scrape_plan" },
    { "type": "exposes", "source_id": "comp_chatgpt_ui_tailor", "target_id": "iface_tailored_artifact" },
    { "type": "exposes", "source_id": "comp_docx_renderer", "target_id": "iface_resume_docx" },
    { "type": "consumes", "source_id": "comp_scraper_adapters", "target_id": "iface_scrape_plan" },
    { "type": "consumes", "source_id": "comp_store", "target_id": "iface_normalized_job" },
    { "type": "consumes", "source_id": "comp_relevance_engine", "target_id": "iface_normalized_job" },
    { "type": "consumes", "source_id": "comp_relevance_engine", "target_id": "iface_user_profile" },
    { "type": "consumes", "source_id": "comp_chatgpt_ui_tailor", "target_id": "iface_user_profile" },
    { "type": "consumes", "source_id": "comp_chatgpt_ui_tailor", "target_id": "iface_normalized_job" },
    { "type": "consumes", "source_id": "comp_docx_renderer", "target_id": "iface_user_profile" },
    { "type": "consumes", "source_id": "comp_docx_renderer", "target_id": "iface_tailored_artifact" },
    { "type": "consumes", "source_id": "comp_docx_renderer", "target_id": "iface_resume_docx" },
    { "type": "consumes", "source_id": "comp_packet_assembler", "target_id": "iface_tailored_artifact" },
    { "type": "consumes", "source_id": "comp_scrape_planner", "target_id": "iface_normalized_job" },
    { "type": "depends_on", "source_id": "comp_orchestrator", "target_id": "comp_rate_limiter" },
    { "type": "depends_on", "source_id": "comp_orchestrator", "target_id": "comp_scraper_adapters" },
    { "type": "depends_on", "source_id": "comp_orchestrator", "target_id": "comp_scrape_planner" },
    { "type": "depends_on", "source_id": "comp_orchestrator", "target_id": "comp_store" },
    { "type": "depends_on", "source_id": "comp_orchestrator", "target_id": "comp_relevance_engine" },
    { "type": "depends_on", "source_id": "comp_orchestrator", "target_id": "comp_chatgpt_ui_tailor" },
    { "type": "depends_on", "source_id": "comp_orchestrator", "target_id": "comp_docx_renderer" },
    { "type": "depends_on", "source_id": "comp_orchestrator", "target_id": "comp_packet_assembler" },
    { "type": "depends_on", "source_id": "comp_scraper_adapters", "target_id": "comp_rate_limiter" },
    { "type": "depends_on", "source_id": "comp_chatgpt_ui_tailor", "target_id": "comp_rate_limiter" },
    { "type": "depends_on", "source_id": "comp_scrape_planner", "target_id": "comp_rate_limiter" },
    { "type": "depends_on", "source_id": "comp_pdf_factory_deprec", "target_id": "comp_store" },
    { "type": "depends_on", "source_id": "comp_docx_renderer", "target_id": "comp_store" },
    { "type": "depends_on", "source_id": "comp_packet_assembler", "target_id": "comp_store" },
    { "type": "depends_on", "source_id": "comp_chatgpt_ui_tailor", "target_id": "comp_store" },
    { "type": "depends_on", "source_id": "comp_scrape_planner", "target_id": "comp_chatgpt_ui_tailor" },
    { "type": "depends_on", "source_id": "comp_scrape_planner", "target_id": "comp_scraper_adapters" },
    { "type": "conflicts_with", "source_id": "risk_bot_and_tos", "target_id": "req_auth_sites" },
    { "type": "conflicts_with", "source_id": "risk_chatgpt_ui_fragility", "target_id": "dec_tailoring_chatgpt_ui" },
    { "type": "conflicts_with", "source_id": "risk_scrape_plan_unsafe", "target_id": "dec_scrape_llm_planner" },
    { "type": "conflicts_with", "source_id": "risk_docker_mac_auth", "target_id": "dec_runtime_local_docker" },
    { "type": "invalidates", "source_id": "risk_session_instability", "target_id": "asm_session_duration" },
    { "type": "invalidates", "source_id": "risk_chatgpt_ui_fragility", "target_id": "asm_chatgpt_ui_available" },
    { "type": "verifies", "source_id": "tst_adapter_fixture_suite", "target_id": "comp_scraper_adapters" },
    { "type": "verifies", "source_id": "tst_adapter_fixture_suite", "target_id": "iface_normalized_job" },
    { "type": "verifies", "source_id": "tst_scrape_plan_replay", "target_id": "comp_scraper_adapters" },
    { "type": "verifies", "source_id": "tst_scrape_plan_replay", "target_id": "iface_scrape_plan" },
    { "type": "verifies", "source_id": "tst_tailoring_schema_contract", "target_id": "comp_chatgpt_ui_tailor" },
    { "type": "verifies", "source_id": "tst_tailoring_schema_contract", "target_id": "iface_tailored_artifact" },
    { "type": "guards_against", "source_id": "tst_scrape_plan_replay", "target_id": "risk_scrape_plan_unsafe" },
    { "type": "guards_against", "source_id": "tst_tailoring_schema_contract", "target_id": "risk_chatgpt_ui_fragility" },
    { "type": "guards_against", "source_id": "tst_adapter_fixture_suite", "target_id": "risk_bot_and_tos" },
    { "type": "validates", "source_id": "tst_tailoring_schema_contract", "target_id": "dec_tailoring_chatgpt_ui" },
    { "type": "validates", "source_id": "tst_scrape_plan_replay", "target_id": "dec_scrape_llm_planner" }
  ]
}
[/GRAPH UPDATE]
Fix required before the graph is valid
I introduced a bad edge by mistake: comp_pdf_factory_deprec does not exist in the nodes list (leftover from renaming comp_pdf_factory → comp_docx_renderer). Remove that edge and point artifact dependencies at comp_docx_renderer only. I’ll treat that as a correction in the next revision; mentally replace that edge with:
depends_on: comp_docx_renderer → comp_store
Also remove the erroneous consumes comp_scrape_planner → iface_normalized_job if the planner consumes page capture not normalized job—planner input is better modeled as a separate capture interface next round.

When ChatGPT Ul tailoring fails (schema invalid, Ul changed, session dead), what should the overnight run do for the affected jobs?
Skip tailoring for that job, mark deferred for morning review; continue pipeline
What should the LLM scrape planner primarily consume to propose iface_scrape_plan? (This determines fixtures and testability.)
Accessibility tree + trimmed HTML snapshot per page (text-first, cheaper)
Preferred DOCX→PDF path on macOS/Docker (fidelity vs simplicity tradeoff)?
LibreOffice headless in container (common default)

Incorporating Phase 3: tailoring failures defer the job (pipeline continues), scrape planner consumes DOM/a11y snapshots, PDF via LibreOffice headless in Docker. Fixing the invalid graph edge and emitting the final cumulative graph, then the implementation plan via CreatePlan.

user: can you explain how this runs end to end

cursor: Here is an end-to-end picture of how a run works in this repo.
1. How you start it
jobpipe run (or jobpipe run --offline) loads settings from env / .env via get_settings(), optionally forces offline=True, then calls run_pipeline(s)
( lines 14–24).
jobpipe refresh-auth is separate: headed Playwright saves storageState JSON under JOBPIPE_SECRETS_DIR for ChatGPT / LinkedIn / Wellfound so later runs can reuse sessions ( refresh-auth).
jobpipe doctor only checks paths, profile file, template, LibreOffice, DB — it does not run the pipeline.
2. One DB transaction for the whole run
run_pipeline opens a single SQLAlchemy session with session_scope(settings): create engine → create_all tables → yield session → commit on success or rollback on error 1. So the whole pipeline is one committed unit unless something raises.
Inside that scope it:
Inserts a pipeline_runs row (running, then completed at the end).
Builds shared objects: ChatGPTUIClient, ScrapePlanner, loads UserProfile from config/profile.yaml, and ScrapeContext (settings + session + run id + profile + planner) ( 52–67).
3. Stage A — Ingest (scrape → normalize → upsert)
For each site in fixed order linkedin → wellfound → ats_greenhouse 2:
If the circuit breaker is open for that site, ingest is skipped and a scrape event is logged ( 69–73).
Otherwise it calls that site module’s discover(ctx) inside with_backoff (retries with exponential backoff) ( 74–80, ).
Each site’s discover (see e.g. LinkedIn/Wellfound/ATS modules) typically: get HTML (fixtures + bundled plan when offline; Playwright + optional storageState when not), build a page capture, ask ScrapePlanner for a JSON scrape plan (ChatGPT UI if chatgpt.json exists, else bundled plan JSON), run the offline executor on the HTML to get rows, map rows to NormalizedJob, return a list.
Each normalized job is upsert_job into SQLite by dedupe key (updates in place if the listing already exists) 3.
Success/failure updates circuit state and scrape_events; each site ends with a checkpoints row for ingest ( 81–94).
4. Stage B — Relevance
Selects jobs where relevance_score is still NULL (up to 2000), runs apply_relevance_to_session (score + explanation JSON + relevant flag vs profile and threshold), records job_processing for stage relevance, flushes, checkpoint ( 98–105).
5. Stage C — Tailor
Eligible jobs: relevance_score is not null and ≥ relevance_threshold ( 110–114).
If a job already has tailored_artifact_json and tailored_for_content_hash == content_hash, it is skipped (idempotent re-run).
Otherwise:
If offline OR no ChatGPT storage file → offline_stub_tailored (deterministic JSON that passes the tailored-artifact schema).
Else → build_tailoring_prompt + chatgpt.request_tailored_artifact (Playwright on chatgpt.com, parse JSON, validate schema).
On success: JSON stored on the job row, defer fields cleared, job_processing tailor/done.
On failure: defer_reason / defer_detail, tailor/deferred — pipeline continues ( 114–139).
6. Stage D — Render (DOCX + PDF)
Ensures templates/resume.docx exists (creates a minimal template if missing).
Same eligible jobs; skips if defer_reason set or no tailored JSON; skips if this run already has a resume_pdf artifact (duplicate guard).
render_resume_docx_pdf: docxtpl render → save DOCX under artifacts/run_<id>/ → soffice --headless to PDF; artifacts rows for resume_docx and resume_pdf ( 143–189).
7. Stage E — Packet
Again eligible jobs with tailored JSON and no defer; write_packet writes job_<id>_packet.md under the same run folder and records an artifacts row packet_md ( 192–205).
8. Finish
Updates pipeline_runs: finished_at, status=completed, summary_json.
Writes artifacts/run_<id>_report.md from the in-memory summary dict.
Returns that summary dict to the CLI, which prints JSON to stdout ( 208–215, 24–25).
Mental model: one command → one DB transaction → ordered stages (ingest all boards → score unscored jobs → tailor high scorers → PDF + markdown packets) → SQLite is the source of truth for jobs/runs/artifacts; the filesystem holds DOCX/PDF/MD under JOBPIPE_ARTIFACTS_DIR.
Docker: same entrypoint: container default CMD is run, so docker compose run … jobpipe run is the same run_pipeline path with paths coming from env/volume mounts described in .

user: and to clarify, is the scoring and packet generation LLM assisted?

cursor: No for scoring. Relevance is fully rule-based: substring checks for profile skills, role titles, must_have / avoid, a small seniority heuristic, and a numeric score — no ChatGPT or other LLM in .
Packet generation itself is not LLM-assisted. only formats the already-produced tailored dict into Markdown (headers, cover_letter_paragraphs, form_answers). It does not call any model.
Where the LLM can appear: the tailoring step can be LLM-assisted: if you are not in --offline mode and secrets/chatgpt.json exists, the pipeline uses the ChatGPT web UI to produce the JSON artifact that later drives both resume rendering and the packet ( tailor branch). Otherwise it uses the offline stub JSON, so the packet text is stub copy, not from an LLM.
Related: Scrape planning can also use the same ChatGPT client when storage exists; otherwise it falls back to bundled JSON plans 1. That is separate from relevance scoring.