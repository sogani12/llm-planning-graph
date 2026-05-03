user: 

cursor: I'll start by checking if there's any existing context in the workspace, then ask the most decision-shaping questions before Phase 1.
ls -la /Users/namans/cond-B 2>/dev/null | head -30
total 0
drwxr-xr-x    2 namans  staff    64 May  2 17:25 .
drwxr-x---@ 112 namans  staff  3584 May  2 17:44 ..
Empty workspace — this is greenfield. Before I start building the decision graph, I need to lock in two choices that will fork the entire architecture. Everything else (component boundaries, testing strategy, error recovery) can be decided downstream of these.

What runtime and resume-generation approach should the pipeline use? (Picks the language ecosystem AND how each tailored resume PDF is produced - these are tightly coupled.)
Node/TypeScript + Playwright + hosted LLM
API
How should the pipeline handle auth-protected boards (Linkedin, Wellfound)? This drives the bot-detection risk profile and what
'unattended overnight' actually means.
Mix: session reuse for Linkedin/Wellfound, public scraping for everything else

Locked in: Node/TypeScript + Playwright + hosted LLM API, with mixed auth (persisted sessions for LinkedIn/Wellfound, public scraping for the rest). Building the Phase 1 graph now.
[GRAPH UPDATE]
{
"nodes": [
{ "id": "obj_overnight_run", "type": "objective", "label": "Unattended overnight execution", "description": "Pipeline runs start-to-finish without human intervention, recovering from transient errors." },
{ "id": "obj_multi_board_coverage", "type": "objective", "label": "Coverage across many job boards", "description": "Aggregate listings from public ATSes and auth-walled platforms in a single run." },
{ "id": "obj_only_relevant", "type": "objective", "label": "Only act on relevant jobs", "description": "Avoid wasting LLM tokens and PDF generation on jobs that don't match the user profile." },
{ "id": "obj_offline_testable", "type": "objective", "label": "Testable without live sites", "description": "Scraper logic must be exercisable in CI / locally without hitting real job boards." },
{ "id": "req_dedup", "type": "requirement", "label": "Cross-run deduplication", "description": "DB must not store duplicate listings across pipeline runs.", "is_functional": true },
{ "id": "req_error_recovery", "type": "requirement", "label": "Full error recovery", "description": "A failure in one adapter, one listing, or one resume must not abort the whole run.", "is_functional": true },
{ "id": "req_tailored_pdf", "type": "requirement", "label": "Tailored resume PDF per job", "description": "Each relevant job gets a uniquely tailored, formatted PDF resume.", "is_functional": true },
{ "id": "req_filter_relevance", "type": "requirement", "label": "Profile-based relevance filter", "description": "Filter listings against skills, seniority, and role preferences before resume generation.", "is_functional": true },
{ "id": "req_offline_test_harness", "type": "requirement", "label": "Offline scraper test harness", "description": "Tests use saved HTML/JSON fixtures, never hit live sites.", "is_functional": false },
{ "id": "req_dynamic_loading", "type": "requirement", "label": "Handle dynamic page loads", "description": "Adapters must wait for client-rendered content (infinite scroll, lazy-loaded cards).", "is_functional": true },
{ "id": "dec_node_ts", "type": "decision", "label": "Node.js + TypeScript runtime", "description": "Whole pipeline written in TypeScript on Node.", "rationale": "User-selected. Strong Playwright + LLM SDK ecosystem; single-language stack from scraping through PDF generation; first-class async for I/O-bound work.", "alternatives_considered": ["Python (richer scraping/data libs but weaker browser automation parity)", "Go (poor Playwright/headless story)"] },
{ "id": "dec_playwright", "type": "decision", "label": "Playwright for browser automation", "description": "Use Playwright (Chromium) for all rendered-page scraping, with persistent BrowserContext for session reuse.", "rationale": "Built-in storageState persistence, robust auto-waits, network interception, multi-browser, better stealth posture than Selenium.", "alternatives_considered": ["Puppeteer (narrower API, weaker storage state ergonomics)", "Crawlee (good but adds opinionated framework on top)", "Selenium (older, more detectable)"] },
{ "id": "dec_llm_hosted", "type": "decision", "label": "Hosted LLM API for resume tailoring", "description": "Use a hosted model (OpenAI or Anthropic) to rewrite resume sections per job.", "rationale": "User-selected. Higher tailoring quality vs local models; no GPU required for overnight host; structured output / JSON mode available.", "alternatives_considered": ["Local Ollama (no quota/cost but lower quality)", "Pure template substitution (deterministic but generic output)"] },
{ "id": "dec_auth_mixed", "type": "decision", "label": "Mixed auth strategy", "description": "Persisted session reuse for LinkedIn/Wellfound; unauthenticated scraping for public ATSes.", "rationale": "User-selected. Avoids automated login (2FA, captcha) on protected sites while keeping the rest cheap and ToS-cleaner.", "alternatives_considered": ["Fully automated login (brittle, high detection risk)", "Public-only (loses LinkedIn/Wellfound coverage)", "Third-party paid APIs (cost, limited coverage)"] },
{ "id": "dec_session_storage_state", "type": "decision", "label": "Manual login -> persisted storageState", "description": "User logs in once via a one-shot 'login' command that opens headed Chromium and saves storageState JSON; pipeline reuses it.", "rationale": "Sidesteps 2FA/captcha automation; storageState captures cookies + localStorage; refreshable on demand.", "alternatives_considered": ["Importing cookies from real browser profile (fragile, OS-specific)", "Username/password automation (high block risk)"] },
{ "id": "dec_per_site_adapters", "type": "decision", "label": "Per-site adapter pattern", "description": "Each board has its own adapter conforming to a common ScraperAdapter interface.", "rationale": "Isolates fragility per source; lets one broken adapter fail without taking down the pipeline; enables fixture-based testing per adapter.", "alternatives_considered": ["Generic config-driven scraper (too brittle for diverse sites)", "Monolithic scraper class (poor isolation)"] },
{ "id": "comp_orchestrator", "type": "component", "label": "Pipeline orchestrator", "description": "Top-level run loop: scrape -> ingest -> dedup -> filter -> generate -> notify. Owns error boundaries and per-stage retry policy.", "has_tests": false },
{ "id": "comp_scraper_engine", "type": "component", "label": "Scraper engine + adapter registry", "description": "Manages Playwright contexts, applies stealth tweaks, dispatches per-site adapters, normalises results.", "has_tests": false },
{ "id": "comp_session_store", "type": "component", "label": "Session storage state manager", "description": "Loads/saves Playwright storageState JSON per site; flags expired sessions for re-login.", "has_tests": false },
{ "id": "comp_db", "type": "component", "label": "Persistent listings database", "description": "Stores normalised listings, fingerprints for dedup, run metadata, and per-job generation status. Engine TBD (Phase 2).", "has_tests": false },
{ "id": "comp_filter", "type": "component", "label": "Relevance filter", "description": "Scores listings against the user profile (skills, seniority, role keywords, location) and selects which proceed to resume generation.", "has_tests": false },
{ "id": "comp_resume_gen", "type": "component", "label": "Resume tailoring + PDF generator", "description": "Calls the LLM to rewrite resume sections for the job, then renders a formatted PDF.", "has_tests": false },
{ "id": "comp_llm_client", "type": "component", "label": "LLM API client", "description": "Thin wrapper over hosted LLM API with retry, timeout, structured-output validation, and cost tracking.", "has_tests": false },
{ "id": "comp_test_harness", "type": "component", "label": "Fixture-based test harness", "description": "Loads saved HTML pages and intercepts Playwright network responses to drive adapters offline.", "has_tests": false },
{ "id": "iface_job_schema", "type": "interface", "label": "Normalised job listing schema", "description": "Common shape every adapter must return.", "contract": "{ source, source_id, url, title, company, location, remote, posted_at, scraped_at, description_html, description_text, salary?, seniority?, raw }" },
{ "id": "iface_scraper_adapter", "type": "interface", "label": "ScraperAdapter contract", "description": "Each adapter exposes id, requiresAuth, list(query, ctx), enrich(listing, ctx).", "contract": "interface ScraperAdapter { id; requiresAuth: boolean; list(q): AsyncIterable<RawListing>; enrich?(l): Promise<RawListing>; }" },
{ "id": "iface_user_profile", "type": "interface", "label": "User profile schema", "description": "Skills, seniority bands, target roles, location preferences, deal-breakers, plus master resume content.", "contract": "{ skills[], seniority, target_roles[], locations[], remote_pref, exclude_keywords[], master_resume }" },
{ "id": "asm_session_longevity", "type": "assumption", "label": "Persisted sessions survive between nights", "description": "Assumes LinkedIn/Wellfound storageState remains valid across days, not just one overnight run.", "confidence": 0.5, "validated": false },
{ "id": "asm_no_midrun_captcha", "type": "assumption", "label": "Sessions won't trigger captcha mid-run", "description": "Assumes warmed-up sessions can paginate through results without an interactive challenge appearing.", "confidence": 0.5, "validated": false },
{ "id": "asm_tos_personal_use", "type": "assumption", "label": "User accepts ToS risk of session reuse", "description": "LinkedIn ToS in particular forbids automated access; user is OK with risk to their account.", "confidence": 0.6, "validated": false },
{ "id": "asm_dom_stable", "type": "assumption", "label": "Site DOMs stable enough for weeks", "description": "Adapters won't need patching more than every few weeks.", "confidence": 0.5, "validated": false },
{ "id": "asm_llm_budget_ok", "type": "assumption", "label": "Per-night LLM cost is acceptable", "description": "Generating N tailored resumes per night fits a reasonable cost ceiling.", "confidence": 0.7, "validated": false },
{ "id": "risk_bot_detection", "type": "risk", "label": "Bot detection breaks scraping silently", "description": "A site update can shadow-ban or serve fake/empty content without throwing errors.", "severity": 0.85 },
{ "id": "risk_session_invalidation", "type": "risk", "label": "Session invalidated overnight", "description": "Auth-walled site logs the session out (password change, new device challenge, idle expiry); pipeline can't recover unattended.", "severity": 0.75 },
{ "id": "risk_tos_account_action", "type": "risk", "label": "Personal account restricted/banned", "description": "Repeated automated access could trigger account-level enforcement on LinkedIn/Wellfound.", "severity": 0.7 },
{ "id": "risk_dom_drift", "type": "risk", "label": "Adapter silently produces wrong fields", "description": "Site markup changes; adapter still 'succeeds' but with truncated or wrong data, polluting the DB.", "severity": 0.8 },
{ "id": "risk_llm_outage", "type": "risk", "label": "LLM API outage or throttling", "description": "Hosted LLM rate-limits or returns 5xx mid-run; resumes fail to generate.", "severity": 0.5 },
{ "id": "risk_silent_overnight_failure", "type": "risk", "label": "Silent overnight failure", "description": "Pipeline crashes or no-ops at 02:00; user discovers it next morning with no output and no signal.", "severity": 0.75 }
],
"edges": [
{ "type": "motivated_by", "source_id": "dec_playwright", "target_id": "obj_multi_board_coverage" },
{ "type": "motivated_by", "source_id": "dec_auth_mixed", "target_id": "obj_multi_board_coverage" },
{ "type": "motivated_by", "source_id": "dec_session_storage_state", "target_id": "obj_overnight_run" },
{ "type": "motivated_by", "source_id": "dec_per_site_adapters", "target_id": "obj_offline_testable" },
{ "type": "motivated_by", "source_id": "dec_per_site_adapters", "target_id": "obj_multi_board_coverage" },
{ "type": "motivated_by", "source_id": "dec_llm_hosted", "target_id": "req_tailored_pdf" },
{ "type": "implements", "source_id": "comp_db", "target_id": "req_dedup" },
{ "type": "implements", "source_id": "comp_orchestrator", "target_id": "req_error_recovery" },
{ "type": "implements", "source_id": "comp_resume_gen", "target_id": "req_tailored_pdf" },
{ "type": "implements", "source_id": "comp_filter", "target_id": "req_filter_relevance" },
{ "type": "implements", "source_id": "comp_test_harness", "target_id": "req_offline_test_harness" },
{ "type": "implements", "source_id": "comp_scraper_engine", "target_id": "req_dynamic_loading" },
{ "type": "exposes", "source_id": "comp_scraper_engine", "target_id": "iface_scraper_adapter" },
{ "type": "exposes", "source_id": "comp_scraper_engine", "target_id": "iface_job_schema" },
{ "type": "consumes", "source_id": "comp_db", "target_id": "iface_job_schema" },
{ "type": "consumes", "source_id": "comp_filter", "target_id": "iface_job_schema" },
{ "type": "consumes", "source_id": "comp_filter", "target_id": "iface_user_profile" },
{ "type": "consumes", "source_id": "comp_resume_gen", "target_id": "iface_user_profile" },
{ "type": "consumes", "source_id": "comp_resume_gen", "target_id": "iface_job_schema" },
{ "type": "depends_on", "source_id": "comp_orchestrator", "target_id": "comp_scraper_engine" },
{ "type": "depends_on", "source_id": "comp_orchestrator", "target_id": "comp_db" },
{ "type": "depends_on", "source_id": "comp_orchestrator", "target_id": "comp_filter" },
{ "type": "depends_on", "source_id": "comp_orchestrator", "target_id": "comp_resume_gen" },
{ "type": "depends_on", "source_id": "comp_scraper_engine", "target_id": "comp_session_store" },
{ "type": "depends_on", "source_id": "comp_resume_gen", "target_id": "comp_llm_client" },
{ "type": "depends_on", "source_id": "comp_test_harness", "target_id": "comp_scraper_engine" },
{ "type": "assumes", "source_id": "dec_session_storage_state", "target_id": "asm_session_longevity" },
{ "type": "assumes", "source_id": "dec_session_storage_state", "target_id": "asm_no_midrun_captcha" },
{ "type": "assumes", "source_id": "dec_session_storage_state", "target_id": "asm_tos_personal_use" },
{ "type": "assumes", "source_id": "dec_per_site_adapters", "target_id": "asm_dom_stable" },
{ "type": "assumes", "source_id": "dec_llm_hosted", "target_id": "asm_llm_budget_ok" },
{ "type": "conflicts_with", "source_id": "risk_bot_detection", "target_id": "dec_playwright" },
{ "type": "conflicts_with", "source_id": "risk_dom_drift", "target_id": "dec_per_site_adapters" },
{ "type": "conflicts_with", "source_id": "risk_session_invalidation", "target_id": "dec_session_storage_state" },
{ "type": "conflicts_with", "source_id": "risk_tos_account_action", "target_id": "dec_session_storage_state" },
{ "type": "conflicts_with", "source_id": "risk_llm_outage", "target_id": "dec_llm_hosted" },
{ "type": "conflicts_with", "source_id": "risk_silent_overnight_failure", "target_id": "obj_overnight_run" },
{ "type": "invalidates", "source_id": "risk_session_invalidation", "target_id": "asm_session_longevity" },
{ "type": "invalidates", "source_id": "risk_bot_detection", "target_id": "asm_no_midrun_captcha" },
{ "type": "invalidates", "source_id": "risk_dom_drift", "target_id": "asm_dom_stable" }
]
}
[/GRAPH UPDATE]
Gaps I want to close before Phase 2 (component design):
The two biggest holes are (a) risk_silent_overnight_failure (0.75) has no mitigation yet — and how we mitigate it depends entirely on where this runs and how you want to be alerted, and (b) comp_filter and comp_resume_gen are sketched but their actual contract depends on whether you already have a structured profile + master resume.

Where does the overnight pipeline run, and how do you want to be notified of run outcomes? (Drives scheduler choice, secret storage, and how we mitigate silent overnight failure.)
Docker container on local machine, log file + Slack/Discord webhook on completion
What's the starting state of your user profile and master resume? (Determines whether comp_filter and comp_resume_gen need authoring tools or can assume structured input.)
I have a finished PDF/DOCX resume but nothing structured - the system needs to parse it once into a master profile

Locked in: Docker container locally + Slack/Discord webhook, and starting from a PDF/DOCX resume that needs a one-shot parse into structured form. Building Phase 2 (components, interfaces, dependencies) now.
[GRAPH UPDATE]
{
"nodes": [
{ "id": "obj_overnight_run", "type": "objective", "label": "Unattended overnight execution", "description": "Pipeline runs start-to-finish without human intervention, recovering from transient errors." },
{ "id": "obj_multi_board_coverage", "type": "objective", "label": "Coverage across many job boards", "description": "Aggregate listings from public ATSes and auth-walled platforms in a single run." },
{ "id": "obj_only_relevant", "type": "objective", "label": "Only act on relevant jobs", "description": "Avoid wasting LLM tokens and PDF generation on jobs that don't match the user profile." },
{ "id": "obj_offline_testable", "type": "objective", "label": "Testable without live sites", "description": "Scraper logic must be exercisable in CI / locally without hitting real job boards." },
{ "id": "req_dedup", "type": "requirement", "label": "Cross-run deduplication", "description": "DB must not store duplicate listings across pipeline runs.", "is_functional": true },
{ "id": "req_error_recovery", "type": "requirement", "label": "Full error recovery", "description": "A failure in one adapter, one listing, or one resume must not abort the whole run.", "is_functional": true },
{ "id": "req_tailored_pdf", "type": "requirement", "label": "Tailored resume PDF per job", "description": "Each relevant job gets a uniquely tailored, formatted PDF resume.", "is_functional": true },
{ "id": "req_filter_relevance", "type": "requirement", "label": "Profile-based relevance filter", "description": "Filter listings against skills, seniority, and role preferences before resume generation.", "is_functional": true },
{ "id": "req_offline_test_harness", "type": "requirement", "label": "Offline scraper test harness", "description": "Tests use saved HTML/JSON fixtures, never hit live sites.", "is_functional": false },
{ "id": "req_dynamic_loading", "type": "requirement", "label": "Handle dynamic page loads", "description": "Adapters must wait for client-rendered content (infinite scroll, lazy-loaded cards).", "is_functional": true },
{ "id": "req_run_visibility", "type": "requirement", "label": "Run outcome observable", "description": "Every run produces a structured summary that reaches the user without them checking logs.", "is_functional": false },
{ "id": "req_no_resume_fabrication", "type": "requirement", "label": "Resumes must not fabricate experience", "description": "LLM may rewrite/reorder/emphasise but must never introduce skills, employers, dates, or accomplishments not in the master resume.", "is_functional": false },
{ "id": "dec_node_ts", "type": "decision", "label": "Node.js + TypeScript runtime", "description": "Whole pipeline written in TypeScript on Node.", "rationale": "User-selected. Strong Playwright + LLM SDK ecosystem; single-language stack from scraping through PDF generation; first-class async for I/O-bound work.", "alternatives_considered": ["Python (richer scraping/data libs but weaker browser automation parity)", "Go (poor Playwright/headless story)"] },
{ "id": "dec_playwright", "type": "decision", "label": "Playwright for browser automation", "description": "Playwright (Chromium) for all rendered-page scraping with persistent BrowserContext for session reuse.", "rationale": "Built-in storageState, robust auto-waits, network interception, multi-browser, better stealth posture than Selenium.", "alternatives_considered": ["Puppeteer", "Crawlee", "Selenium"] },
{ "id": "dec_llm_hosted", "type": "decision", "label": "Hosted LLM API for resume tailoring", "description": "Hosted model (OpenAI/Anthropic) rewrites resume sections per job.", "rationale": "User-selected. Higher tailoring quality vs local models; structured-output / JSON mode available.", "alternatives_considered": ["Local Ollama", "Pure template substitution"] },
{ "id": "dec_auth_mixed", "type": "decision", "label": "Mixed auth strategy", "description": "Persisted sessions for LinkedIn/Wellfound; unauthenticated for public ATSes.", "rationale": "User-selected. Avoids automated login on protected sites.", "alternatives_considered": ["Full auto-login", "Public-only", "Third-party APIs"] },
{ "id": "dec_session_storage_state", "type": "decision", "label": "Manual login -> persisted storageState", "description": "One-shot 'login' CLI command opens headed Chromium, user logs in, storageState JSON saved per site; pipeline reuses it.", "rationale": "Sidesteps 2FA/captcha automation; refreshable on demand.", "alternatives_considered": ["Cookie import from real browser profile", "Username/password automation"] },
{ "id": "dec_per_site_adapters", "type": "decision", "label": "Per-site adapter pattern", "description": "Each board has its own adapter conforming to a common ScraperAdapter interface.", "rationale": "Per-source isolation; one broken adapter cannot fail the run; enables fixture-based testing.", "alternatives_considered": ["Generic config-driven scraper", "Monolithic scraper"] },
{ "id": "dec_docker", "type": "decision", "label": "Docker container deployment", "description": "Pipeline ships as a Docker image based on mcr.microsoft.com/playwright; scheduled on the host via launchd/cron; volumes for DB, sessions, outputs.", "rationale": "Reproducible Playwright environment (browsers + OS deps preinstalled); isolates from host Node version; easy to relocate.", "alternatives_considered": ["Bare Node + npx playwright install", "systemd service", "GitHub Actions cron"] },
{ "id": "dec_webhook_notify", "type": "decision", "label": "Webhook notification (Slack/Discord)", "description": "End-of-run summary (and per-stage failures above a threshold) posted to a webhook URL.", "rationale": "Push-based; no SMTP setup; renders nicely; addresses silent-failure risk.", "alternatives_considered": ["Email via SMTP", "Pushover/ntfy", "Local desktop notification only"] },
{ "id": "dec_jsonresume", "type": "decision", "label": "JSON Resume schema as canonical profile", "description": "Master resume + extension fields (target_roles, seniority, exclude_keywords, locations) stored as a single JSON Resume document.", "rationale": "Open standard, large theme ecosystem, easy to validate, schema documents itself.", "alternatives_considered": ["Custom schema", "LaTeX source as ground truth", "Markdown + frontmatter"] },
{ "id": "dec_resume_bootstrap_once", "type": "decision", "label": "One-shot LLM-assisted PDF -> JSON Resume bootstrap", "description": "Separate CLI command extracts text from user's existing PDF/DOCX, prompts the LLM to emit JSON Resume, then opens it for manual review/edit before commit.", "rationale": "User has no structured source today; one-time cost; manual-review checkpoint prevents bad data from polluting all future runs.", "alternatives_considered": ["Parse every run", "Manual transcription only", "Pure regex/heuristic parsing"] },
{ "id": "dec_pdf_via_html", "type": "decision", "label": "PDF rendered via HTML template + Playwright print", "description": "Tailored JSON Resume rendered through a Handlebars/EJS HTML template, then printed to PDF by Chromium (Playwright page.pdf).", "rationale": "Reuses Playwright we already have; full CSS control; deterministic; works with JSON Resume themes if desired.", "alternatives_considered": ["@react-pdf/renderer (different template lang)", "LaTeX (heavy toolchain in container)", "Pandoc/Word"] },
{ "id": "dec_sqlite", "type": "decision", "label": "SQLite via better-sqlite3 + Drizzle ORM", "description": "Embedded SQLite on a Docker volume; Drizzle for typed schema and migrations.", "rationale": "Single-machine, single-writer; zero ops; survives container restarts via volume; Drizzle gives TS types and migrations.", "alternatives_considered": ["Postgres (overkill)", "DuckDB (analytical, write story weaker)", "Plain JSON files (no indexes / dedup queries)"] },
{ "id": "dec_dedup_multikey", "type": "decision", "label": "Multi-key dedup fingerprint", "description": "Primary key: (source, source_id). Secondary: SHA-256 of normalised (company + title + normalised_url). Tertiary: SHA-256 of normalised description text for cross-board dupes.", "rationale": "Same job often appears on multiple boards under different IDs; URL/title alone misses re-posts.", "alternatives_considered": ["URL-only", "(source, source_id) only", "Title+company only"] },
{ "id": "dec_llm_grounded_rewrite", "type": "decision", "label": "LLM operates in grounded-rewrite mode only", "description": "LLM is given the full master resume + job description and prompted to (a) reorder/select bullets, (b) rewrite phrasing, (c) emphasise matching skills. It MAY NOT add new employers, dates, titles, or skills. Output is validated against the master profile (whitelist of allowed fields/values).", "rationale": "Eliminates the highest-impact failure mode (fabrication that user can't catch overnight).", "alternatives_considered": ["Free generation", "Few-shot only", "No grounding constraints"] }
],
"edges": [
{ "type": "motivated_by", "source_id": "dec_playwright", "target_id": "obj_multi_board_coverage" },
{ "type": "motivated_by", "source_id": "dec_auth_mixed", "target_id": "obj_multi_board_coverage" },
{ "type": "motivated_by", "source_id": "dec_session_storage_state", "target_id": "obj_overnight_run" },
{ "type": "motivated_by", "source_id": "dec_per_site_adapters", "target_id": "obj_offline_testable" },
{ "type": "motivated_by", "source_id": "dec_per_site_adapters", "target_id": "obj_multi_board_coverage" },
{ "type": "motivated_by", "source_id": "dec_llm_hosted", "target_id": "req_tailored_pdf" },
{ "type": "motivated_by", "source_id": "dec_docker", "target_id": "obj_overnight_run" },
{ "type": "motivated_by", "source_id": "dec_webhook_notify", "target_id": "obj_overnight_run" },
{ "type": "motivated_by", "source_id": "dec_jsonresume", "target_id": "req_tailored_pdf" },
{ "type": "motivated_by", "source_id": "dec_resume_bootstrap_once", "target_id": "req_tailored_pdf" },
{ "type": "motivated_by", "source_id": "dec_llm_grounded_rewrite", "target_id": "req_no_resume_fabrication" },
{ "type": "implements", "source_id": "comp_db", "target_id": "req_dedup" },
{ "type": "implements", "source_id": "comp_orchestrator", "target_id": "req_error_recovery" },
{ "type": "implements", "source_id": "comp_resume_gen", "target_id": "req_tailored_pdf" },
{ "type": "implements", "source_id": "comp_filter", "target_id": "req_filter_relevance" },
{ "type": "implements", "source_id": "comp_test_harness", "target_id": "req_offline_test_harness" },
{ "type": "implements", "source_id": "comp_scraper_engine", "target_id": "req_dynamic_loading" },
{ "type": "implements", "source_id": "comp_notifier", "target_id": "req_run_visibility" },
{ "type": "implements", "source_id": "comp_resume_gen", "target_id": "req_no_resume_fabrication" },
{ "type": "exposes", "source_id": "comp_scraper_engine", "target_id": "iface_scraper_adapter" },
{ "type": "exposes", "source_id": "comp_scraper_engine", "target_id": "iface_job_schema" },
{ "type": "exposes", "source_id": "comp_db", "target_id": "iface_db_repo" },
{ "type": "exposes", "source_id": "comp_resume_gen", "target_id": "iface_resume_render_input" },
{ "type": "exposes", "source_id": "comp_notifier", "target_id": "iface_run_summary" },
{ "type": "consumes", "source_id": "comp_db", "target_id": "iface_job_schema" },
{ "type": "consumes", "source_id": "comp_filter", "target_id": "iface_job_schema" },
{ "type": "consumes", "source_id": "comp_filter", "target_id": "iface_user_profile" },
{ "type": "consumes", "source_id": "comp_resume_gen", "target_id": "iface_user_profile" },
{ "type": "consumes", "source_id": "comp_resume_gen", "target_id": "iface_job_schema" },
{ "type": "consumes", "source_id": "comp_pdf_renderer", "target_id": "iface_resume_render_input" },
{ "type": "consumes", "source_id": "comp_notifier", "target_id": "iface_run_summary" },
{ "type": "depends_on", "source_id": "comp_orchestrator", "target_id": "comp_scraper_engine" },
{ "type": "depends_on", "source_id": "comp_orchestrator", "target_id": "comp_db" },
{ "type": "depends_on", "source_id": "comp_orchestrator", "target_id": "comp_filter" },
{ "type": "depends_on", "source_id": "comp_orchestrator", "target_id": "comp_resume_gen" },
{ "type": "depends_on", "source_id": "comp_orchestrator", "target_id": "comp_notifier" },
{ "type": "depends_on", "source_id": "comp_scraper_engine", "target_id": "comp_session_store" },
{ "type": "depends_on", "source_id": "comp_resume_gen", "target_id": "comp_llm_client" },
{ "type": "depends_on", "source_id": "comp_resume_gen", "target_id": "comp_pdf_renderer" },
{ "type": "depends_on", "source_id": "comp_resume_gen", "target_id": "comp_db" },
{ "type": "depends_on", "source_id": "comp_test_harness", "target_id": "comp_scraper_engine" },
{ "type": "depends_on", "source_id": "comp_profile_bootstrap", "target_id": "comp_llm_client" },
{ "type": "depends_on", "source_id": "comp_docker_image", "target_id": "comp_orchestrator" },
{ "type": "assumes", "source_id": "dec_session_storage_state", "target_id": "asm_session_longevity" },
{ "type": "assumes", "source_id": "dec_session_storage_state", "target_id": "asm_no_midrun_captcha" },
{ "type": "assumes", "source_id": "dec_session_storage_state", "target_id": "asm_tos_personal_use" },
{ "type": "assumes", "source_id": "dec_per_site_adapters", "target_id": "asm_dom_stable" },
{ "type": "assumes", "source_id": "dec_llm_hosted", "target_id": "asm_llm_budget_ok" },
{ "type": "assumes", "source_id": "dec_resume_bootstrap_once", "target_id": "asm_resume_parse_accuracy" },
{ "type": "assumes", "source_id": "dec_pdf_via_html", "target_id": "asm_html_template_renders" },
{ "type": "assumes", "source_id": "dec_docker", "target_id": "asm_docker_playwright_apple_silicon" },
{ "type": "conflicts_with", "source_id": "risk_bot_detection", "target_id": "dec_playwright" },
{ "type": "conflicts_with", "source_id": "risk_dom_drift", "target_id": "dec_per_site_adapters" },
{ "type": "conflicts_with", "source_id": "risk_session_invalidation", "target_id": "dec_session_storage_state" },
{ "type": "conflicts_with", "source_id": "risk_tos_account_action", "target_id": "dec_session_storage_state" },
{ "type": "conflicts_with", "source_id": "risk_llm_outage", "target_id": "dec_llm_hosted" },
{ "type": "conflicts_with", "source_id": "risk_silent_overnight_failure", "target_id": "obj_overnight_run" },
{ "type": "conflicts_with", "source_id": "risk_llm_hallucinates_resume", "target_id": "req_no_resume_fabrication" },
{ "type": "conflicts_with", "source_id": "risk_dedup_misses", "target_id": "req_dedup" },
{ "type": "conflicts_with", "source_id": "risk_run_exceeds_window", "target_id": "obj_overnight_run" },
{ "type": "invalidates", "source_id": "risk_session_invalidation", "target_id": "asm_session_longevity" },
{ "type": "invalidates", "source_id": "risk_bot_detection", "target_id": "asm_no_midrun_captcha" },
{ "type": "invalidates", "source_id": "risk_dom_drift", "target_id": "asm_dom_stable" },
{ "type": "invalidates", "source_id": "risk_llm_hallucinates_resume", "target_id": "asm_resume_parse_accuracy" }
]
}
[/GRAPH UPDATE]
(Component, interface, assumption, and risk node bodies for the new ones added in this phase, so they're not just dangling ids referenced in edges:)
comp_orchestrator — pipeline run loop with stage-level error boundaries and retry policy.
comp_scraper_engine — Playwright context manager, stealth tweaks, dispatches adapters, normalises output.
comp_session_store — loads/saves storageState per site; flags expired sessions.
comp_db — SQLite + Drizzle; jobs, runs, generations tables.
comp_filter — scores listings against profile; emits accept/reject + reason.
comp_resume_gen — calls LLM (grounded) then comp_pdf_renderer.
comp_pdf_renderer — Handlebars HTML -> Playwright page.pdf.
comp_llm_client — hosted-LLM SDK wrapper with retry, JSON-mode validation, cost tracking.
comp_notifier — Slack/Discord webhook poster.
comp_test_harness — fixture loader + Playwright route mocking.
comp_profile_bootstrap — one-shot CLI: PDF/DOCX -> text -> LLM -> JSON Resume -> review.
comp_docker_image — Dockerfile (Playwright base) + compose with volumes for db/, sessions/, outputs/, fixtures/.
iface_db_repo — typed CRUD for jobs/runs/generations.
iface_resume_render_input — { resumeJson, jobMeta, themeId } -> PDF bytes.
iface_run_summary — { runId, startedAt, finishedAt, perAdapterStats[], newJobs, filteredIn, generated, failures[] }.
asm_resume_parse_accuracy (0.6) — LLM parses user's PDF correctly on first pass.
asm_html_template_renders (0.7) — chosen HTML template prints reliably under Chromium.
asm_docker_playwright_apple_silicon (0.7) — Playwright Docker image runs reliably on user's Mac (especially if Apple Silicon).
risk_llm_hallucinates_resume (0.8) — LLM invents experience the user can't verify before applying.
risk_dedup_misses (0.6) — fingerprint scheme misses cross-board re-posts or near-duplicates.
risk_run_exceeds_window (0.5) — total run-time pushes past morning, partial output.
Two scope-defining questions before Phase 3 (testing + error handling):
The biggest remaining ambiguity is the word "application" in your brief. The capabilities you listed stop at PDF generation — but "job application pipeline" could imply auto-submission. That's a totally different blast radius (much higher ToS risk, much more brittle, needs per-board form automation). And the second question pins down how big "overnight" actually is, which gates the LLM budget assumption and the run-window risk.

What does 'application' mean here? Where does the pipeline stop?
Artifacts only - pipeline produces a per-job folder (tailored PDF + cover letter? + listing snapshot + apply URL) for me to review and submit manually next morning
Roughly what scale per overnight run? (Pins LLM budget assumption and decides batching / runtime budget.)
Not sure - design for medium and make it configurable

All the major forks are decided. Final graph below, then the plan.
[GRAPH UPDATE]
{
"nodes": [
{ "id": "obj_overnight_run", "type": "objective", "label": "Unattended overnight execution", "description": "Pipeline runs start-to-finish without human intervention, recovering from transient errors." },
{ "id": "obj_multi_board_coverage", "type": "objective", "label": "Coverage across many job boards", "description": "Aggregate listings from public ATSes and auth-walled platforms in a single run." },
{ "id": "obj_only_relevant", "type": "objective", "label": "Only act on relevant jobs", "description": "Avoid wasting LLM tokens and PDF generation on jobs that don't match the user profile." },
{ "id": "obj_offline_testable", "type": "objective", "label": "Testable without live sites", "description": "Scraper logic must be exercisable in CI / locally without hitting real job boards." },
{ "id": "obj_human_in_loop_submit", "type": "objective", "label": "Human submits final application", "description": "Pipeline produces artifacts; user does the final review + submission. No auto-apply." },
{ "id": "req_dedup", "type": "requirement", "label": "Cross-run deduplication", "description": "DB must not store duplicate listings across pipeline runs.", "is_functional": true },
{ "id": "req_error_recovery", "type": "requirement", "label": "Full error recovery", "description": "A failure in one adapter, one listing, or one resume must not abort the whole run.", "is_functional": true },
{ "id": "req_tailored_pdf", "type": "requirement", "label": "Tailored resume PDF per job", "description": "Each relevant job gets a uniquely tailored, formatted PDF resume.", "is_functional": true },
{ "id": "req_tailored_cover", "type": "requirement", "label": "Tailored cover letter PDF per job", "description": "Each relevant job also gets a tailored cover letter PDF rendered with the same style as the resume.", "is_functional": true },
{ "id": "req_filter_relevance", "type": "requirement", "label": "Profile-based relevance filter", "description": "Filter listings against skills, seniority, and role preferences before generation.", "is_functional": true },
{ "id": "req_offline_test_harness", "type": "requirement", "label": "Offline scraper test harness", "description": "Tests use saved HTML/JSON fixtures, never hit live sites.", "is_functional": false },
{ "id": "req_dynamic_loading", "type": "requirement", "label": "Handle dynamic page loads", "description": "Adapters must wait for client-rendered content (infinite scroll, lazy-loaded cards).", "is_functional": true },
{ "id": "req_run_visibility", "type": "requirement", "label": "Run outcome observable", "description": "Every run produces a structured summary that reaches the user without them checking logs.", "is_functional": false },
{ "id": "req_urgent_alerts", "type": "requirement", "label": "Urgent alerts mid-run", "description": "High-severity events (session expiry, sustained LLM outage) fire an immediate webhook, not just the end-of-run summary.", "is_functional": false },
{ "id": "req_no_resume_fabrication", "type": "requirement", "label": "Generated documents must not fabricate experience", "description": "LLM may rewrite/reorder/emphasise but must never introduce skills, employers, dates, or accomplishments not in the master profile. Applies to both resume and cover letter.", "is_functional": false },
{ "id": "req_artifact_folder", "type": "requirement", "label": "Per-job artifact folder", "description": "Each generated job produces a deterministic folder layout: resume.pdf, cover_letter.pdf, listing.json, prompt.md, generation_meta.json, apply_url.txt.", "is_functional": true },
{ "id": "req_resumable_run", "type": "requirement", "label": "Crash-resumable run", "description": "If the container is killed mid-run, the next invocation can resume without redoing completed stages.", "is_functional": true },
{ "id": "req_configurable_scale", "type": "requirement", "label": "Configurable boards and limits", "description": "Board list, per-board listing caps, per-night resume cap, and concurrency are all config-driven, not hardcoded.", "is_functional": false },
{ "id": "dec_node_ts", "type": "decision", "label": "Node.js + TypeScript runtime", "description": "Whole pipeline written in TypeScript on Node.", "rationale": "User-selected. Strong Playwright + LLM SDK ecosystem; single-language stack from scraping through PDF generation; first-class async for I/O-bound work.", "alternatives_considered": ["Python", "Go"] },
{ "id": "dec_playwright", "type": "decision", "label": "Playwright for browser automation", "description": "Playwright (Chromium) for all rendered-page scraping with persistent BrowserContext for session reuse.", "rationale": "Built-in storageState, robust auto-waits, network interception, multi-browser, better stealth posture than Selenium.", "alternatives_considered": ["Puppeteer", "Crawlee", "Selenium"] },
{ "id": "dec_llm_hosted", "type": "decision", "label": "Hosted LLM API for generation", "description": "Hosted model (OpenAI/Anthropic) drives both resume and cover letter generation in JSON-mode/structured output.", "rationale": "User-selected. Higher tailoring quality vs local models; structured-output / JSON mode available; one provider for both documents.", "alternatives_considered": ["Local Ollama", "Pure template substitution"] },
{ "id": "dec_auth_mixed", "type": "decision", "label": "Mixed auth strategy", "description": "Persisted sessions for LinkedIn/Wellfound; unauthenticated for public ATSes (Greenhouse, Lever, Ashby, public company pages).", "rationale": "User-selected. Avoids automated login on protected sites.", "alternatives_considered": ["Full auto-login", "Public-only", "Third-party APIs"] },
{ "id": "dec_session_storage_state", "type": "decision", "label": "Manual login -> persisted storageState", "description": "One-shot login CLI opens headed Chromium, user logs in, storageState JSON saved per site; pipeline reuses it.", "rationale": "Sidesteps 2FA/captcha automation; refreshable on demand.", "alternatives_considered": ["Cookie import from real browser profile", "Username/password automation"] },
{ "id": "dec_session_urgent_alert", "type": "decision", "label": "Session expiry: skip + urgent alert + continue", "description": "On detecting login redirect/401/captcha page: mark adapter needs_relogin in DB, fire urgent webhook immediately (severity=urgent), continue rest of pipeline. Future runs auto-skip the adapter until login is re-run.", "rationale": "User-selected. Maximises overnight yield while giving the user an actionable signal in time to re-auth.", "alternatives_considered": ["Silent skip", "Abort whole run", "Block on login (defeats unattended)"] },
{ "id": "dec_per_site_adapters", "type": "decision", "label": "Per-site adapter pattern", "description": "Each board has its own adapter conforming to a common ScraperAdapter interface. Adapters are responsible for their own SessionExpired detection (login URL substring, captcha selector).", "rationale": "Per-source isolation; one broken adapter cannot fail the run; enables fixture-based testing.", "alternatives_considered": ["Generic config-driven scraper", "Monolithic scraper"] },
{ "id": "dec_docker", "type": "decision", "label": "Docker container deployment", "description": "Pipeline ships as a Docker image based on mcr.microsoft.com/playwright; volumes mount db/, sessions/, outputs/, fixtures/, config/, profile/.", "rationale": "Reproducible Playwright environment; isolates from host Node version; easy to relocate.", "alternatives_considered": ["Bare Node + npx playwright install", "systemd service", "GitHub Actions cron"] },
{ "id": "dec_host_launchd", "type": "decision", "label": "Host launchd triggers one-shot container", "description": "macOS launchd job runs docker compose run --rm pipeline nightly. Container exits at end of run.", "rationale": "No long-running daemon; logs captured per invocation; restart-on-failure handled by launchd.", "alternatives_considered": ["In-container cron", "Long-running container with internal scheduler"] },
{ "id": "dec_webhook_notify", "type": "decision", "label": "Webhook notification (Slack/Discord)", "description": "End-of-run summary AND urgent mid-run alerts posted to a webhook URL.", "rationale": "Push-based; no SMTP setup; renders nicely; addresses silent-failure risk; supports both summary and urgent posts.", "alternatives_considered": ["Email via SMTP", "Pushover/ntfy", "Local desktop notification only"] },
{ "id": "dec_jsonresume", "type": "decision", "label": "JSON Resume schema as canonical profile", "description": "Master resume + extension fields (x_preferences) stored as a single JSON Resume document.", "rationale": "Open standard, large theme ecosystem, easy to validate, schema documents itself.", "alternatives_considered": ["Custom schema", "LaTeX source as ground truth", "Markdown + frontmatter"] },
{ "id": "dec_resume_bootstrap_once", "type": "decision", "label": "One-shot LLM-assisted PDF -> JSON Resume bootstrap", "description": "Separate bootstrap CLI extracts text from user's PDF/DOCX, prompts the LLM to emit JSON Resume, opens it in $EDITOR for manual review/edit before commit.", "rationale": "User has no structured source today; one-time cost; manual review prevents bad data.", "alternatives_considered": ["Parse every run", "Manual transcription only", "Pure regex/heuristic parsing"] },
{ "id": "dec_pdf_via_html", "type": "decision", "label": "PDF via Handlebars HTML + Playwright print", "description": "Both resume and cover letter rendered through Handlebars templates, printed by Chromium (Playwright page.pdf). Same renderer, different templates.", "rationale": "Reuses Playwright; full CSS control; deterministic; one renderer for two doc types.", "alternatives_considered": ["@react-pdf/renderer", "LaTeX in container", "Pandoc/Word"] },
{ "id": "dec_cover_letter_pdf", "type": "decision", "label": "Cover letter rendered to PDF alongside resume", "description": "Per-job artifact folder always includes both resume.pdf and cover_letter.pdf (same renderer, same grounding rules).", "rationale": "User-selected. Ready-to-upload; consistent styling; one extra LLM call per job.", "alternatives_considered": ["Resume only", "Cover letter as Markdown", "Configurable per board"] },
{ "id": "dec_sqlite", "type": "decision", "label": "SQLite via better-sqlite3 + Drizzle ORM", "description": "Embedded SQLite on a Docker volume; Drizzle for typed schema and migrations.", "rationale": "Single-machine, single-writer; zero ops; survives container restarts via volume; Drizzle gives TS types and migrations.", "alternatives_considered": ["Postgres", "DuckDB", "Plain JSON files"] },
{ "id": "dec_dedup_multikey", "type": "decision", "label": "Multi-key dedup fingerprint", "description": "Primary: (source, source_id). Secondary: SHA-256(normalised company+title+normalised_url). Tertiary: SHA-256(normalised description).", "rationale": "Same job often appears on multiple boards under different IDs; URL/title alone misses re-posts.", "alternatives_considered": ["URL-only", "(source, source_id) only", "Title+company only"] },
{ "id": "dec_llm_grounded_rewrite", "type": "decision", "label": "LLM operates in grounded mode only", "description": "LLM receives master resume + JD; must (a) reorder/select bullets, (b) rewrite phrasing, (c) emphasise matching skills. May NOT introduce new employers, dates, titles, or skills. Output validated against a whitelist derived from the master profile (companies, dates, skills, titles); non-whitelisted tokens trigger one regeneration; second failure rejects the job and logs the reason.", "rationale": "Eliminates the highest-impact failure mode (fabrication user can't catch overnight). Applies to cover letter too.", "alternatives_considered": ["Free generation", "Few-shot only", "No grounding constraints"] },
{ "id": "dec_artifacts_only", "type": "decision", "label": "Artifacts only, no auto-apply", "description": "Pipeline ends at a per-job folder. User reviews + submits manually next morning.", "rationale": "User-selected. Eliminates per-board form automation and removes the largest ToS/legal risk surface.", "alternatives_considered": ["Easy Apply auto-submit", "Full multi-page form auto-submit"] },
{ "id": "dec_per_stage_retry", "type": "decision", "label": "Per-stage retry + per-adapter circuit breaker", "description": "Each unit of work has bounded retry with exponential backoff and jitter. Per-adapter circuit breaker trips after N consecutive failures and skips remainder.", "rationale": "Most failures are transient. Circuit breaker prevents wasting overnight time on a hard-broken adapter.", "alternatives_considered": ["No retry", "Global retry only", "Infinite retry"] },
{ "id": "dec_checkpoint_db", "type": "decision", "label": "Checkpoint progress in DB", "description": "Each stage records completion in SQLite (jobs.scraped_at, jobs.filtered_at, generations.status). Re-running a run_id resumes after the last completed stage.", "rationale": "Container restart should not redo work; supports req_resumable_run.", "alternatives_considered": ["File-based checkpoint", "In-memory only"] },
{ "id": "dec_polite_concurrency", "type": "decision", "label": "Bounded cross-board concurrency, serial within board", "description": "Adapters run concurrently with a configurable pool (default 3). Within an adapter, requests are serial with randomized delay (default 1.5\u20134s) and a per-board listing cap.", "rationale": "Maximises wall-clock throughput while staying polite per origin; reduces bot-detection signal.", "alternatives_considered": ["Fully serial", "Unbounded concurrency", "Concurrent within a single board"] },
{ "id": "dec_test_layers", "type": "decision", "label": "Three test layers: unit / conformance / integration", "description": "(1) Per-adapter unit tests against saved HTML fixtures. (2) Conformance test that every registered adapter satisfies ScraperAdapter and produces a schema-valid Job. (3) Orchestrator integration test with mock adapters + mock LLM + temp SQLite running the full pipeline.", "rationale": "Layered coverage with no live-site dependence.", "alternatives_considered": ["Unit-only", "Integration-only", "Live VCR tests"] },
{ "id": "comp_orchestrator", "type": "component", "label": "Pipeline orchestrator", "description": "Top-level run loop: scrape -> ingest/dedup -> filter -> generate -> notify. Owns error boundaries, retry policy, and checkpointing.", "has_tests": false },
{ "id": "comp_scraper_engine", "type": "component", "label": "Scraper engine + adapter registry", "description": "Manages Playwright contexts, applies stealth tweaks, dispatches per-site adapters, normalises results.", "has_tests": false },
{ "id": "comp_session_store", "type": "component", "label": "Session storage state manager", "description": "Loads/saves Playwright storageState JSON per site; flags expired sessions; emits SessionExpiredError; tracks needs_relogin.", "has_tests": false },
{ "id": "comp_db", "type": "component", "label": "Persistent listings database", "description": "SQLite + Drizzle schema: runs, jobs, fingerprints, generations, errors, adapter_health.", "has_tests": false },
{ "id": "comp_filter", "type": "component", "label": "Relevance filter", "description": "Scores listings against the user profile (skills, seniority, role keywords, location, exclude_keywords); records reason on reject.", "has_tests": false },
{ "id": "comp_resume_gen", "type": "component", "label": "Resume tailoring", "description": "Calls grounded LLM to rewrite resume sections, validates against master, then renders PDF.", "has_tests": false },
{ "id": "comp_cover_letter_gen", "type": "component", "label": "Cover letter tailoring", "description": "Calls grounded LLM to draft a per-job cover letter, validates against master, then renders PDF.", "has_tests": false },
{ "id": "comp_pdf_renderer", "type": "component", "label": "HTML -> PDF renderer", "description": "Renders Handlebars templates for resume and cover letter; prints via Playwright page.pdf.", "has_tests": false },
{ "id": "comp_llm_client", "type": "component", "label": "LLM API client", "description": "Hosted-LLM SDK wrapper with retry, JSON-mode validation, cost tracking, and offline mock implementation for tests.", "has_tests": false },
{ "id": "comp_notifier", "type": "component", "label": "Webhook notifier", "description": "Posts run summary AND urgent mid-run alerts to Slack/Discord webhook. Always invoked in a finally block by the orchestrator.", "has_tests": false },
{ "id": "comp_test_harness", "type": "component", "label": "Fixture-based test harness", "description": "Loads saved HTML pages and intercepts Playwright network responses (page.route); provides mock LLM client and a fixture-recording CLI.", "has_tests": false },
{ "id": "comp_profile_bootstrap", "type": "component", "label": "Profile bootstrap CLI", "description": "One-shot: PDF/DOCX -> text -> LLM -> JSON Resume draft -> opens in $EDITOR -> commits.", "has_tests": false },
{ "id": "comp_docker_image", "type": "component", "label": "Docker image + compose", "description": "Dockerfile based on mcr.microsoft.com/playwright; compose mounts ./data and ./config and ./profile.", "has_tests": false },
{ "id": "comp_artifact_writer", "type": "component", "label": "Per-job artifact writer", "description": "Composes resume_gen + cover_letter_gen output and writes outputs/<YYYY-MM-DD>/<company><title><short_id>/{resume.pdf, cover_letter.pdf, listing.json, prompt.md, generation_meta.json, apply_url.txt}.", "has_tests": false },
{ "id": "comp_retry", "type": "component", "label": "Retry + circuit breaker utility", "description": "Cross-cutting helper providing bounded exponential backoff + per-key circuit breaker; wraps adapter and LLM calls.", "has_tests": false },
{ "id": "comp_logger", "type": "component", "label": "Structured logger", "description": "JSON logger keyed on run_id, adapter_id, job_id; piped to stdout (captured by Docker) and to a per-run log file under outputs/.", "has_tests": false },
{ "id": "iface_job_schema", "type": "interface", "label": "Normalised job listing schema", "description": "Common shape every adapter must return.", "contract": "{ source, source_id, url, title, company, location, remote, posted_at, scraped_at, description_html, description_text, salary?, seniority?, raw }" },
{ "id": "iface_scraper_adapter", "type": "interface", "label": "ScraperAdapter contract", "description": "Each adapter exposes id, requiresAuth, list(query, ctx), enrich(listing, ctx).", "contract": "interface ScraperAdapter { id: string; requiresAuth: boolean; list(q, ctx): AsyncIterable<RawListing>; enrich?(l, ctx): Promise<RawListing>; detectSessionExpired?(page): boolean; }" },
{ "id": "iface_user_profile", "type": "interface", "label": "User profile schema", "description": "JSON Resume v1 + extension block.", "contract": "{ ...JSONResume, x_preferences: { target_roles[], seniority, locations[], remote_pref, exclude_keywords[], min_salary? } }" },
{ "id": "iface_db_repo", "type": "interface", "label": "DB repository", "description": "Typed CRUD + dedup queries.", "contract": "interface JobsRepo { upsertJob(j): {id, isNew}; markStage(jobId, stage); listForRun(runId, stage); markAdapterNeedsRelogin(id); ... }" },
{ "id": "iface_resume_render_input", "type": "interface", "label": "Document render input", "description": "Input to the PDF renderer (used by both resume and cover letter).", "contract": "{ docType: 'resume' | 'cover_letter', payload: object, jobMeta: { title, company, jobId }, themeId: string } -> Buffer (PDF)" },
{ "id": "iface_run_summary", "type": "interface", "label": "Run summary", "description": "Structured summary posted to webhook.", "contract": "{ runId, startedAt, finishedAt, perAdapter: [{id, listed, new, errors, circuitTripped, needsRelogin}], filteredIn, generated, failures: [{stage, jobId?, error}], sessionsExpired: string[] }" },
{ "id": "iface_urgent_alert", "type": "interface", "label": "Urgent alert", "description": "Mid-run urgent webhook payload.", "contract": "{ runId, severity: 'urgent', kind: 'session_expired' | 'llm_outage', adapterId?, message, timestamp }" },
{ "id": "asm_session_longevity", "type": "assumption", "label": "Persisted sessions survive between nights", "description": "LinkedIn/Wellfound storageState remains valid across days, not just one overnight run.", "confidence": 0.5, "validated": false },
{ "id": "asm_no_midrun_captcha", "type": "assumption", "label": "Sessions won't trigger captcha mid-run", "description": "Warmed-up sessions can paginate through results without an interactive challenge.", "confidence": 0.5, "validated": false },
{ "id": "asm_tos_personal_use", "type": "assumption", "label": "User accepts ToS risk of session reuse", "description": "LinkedIn ToS forbids automated access; user is OK with risk to their account.", "confidence": 0.6, "validated": false },
{ "id": "asm_dom_stable", "type": "assumption", "label": "Site DOMs stable enough for weeks", "description": "Adapters won't need patching more than every few weeks.", "confidence": 0.5, "validated": false },
{ "id": "asm_llm_budget_ok", "type": "assumption", "label": "Per-night LLM cost is acceptable", "description": "Generating ~15\u201340 tailored resumes + cover letters per night fits a reasonable cost ceiling.", "confidence": 0.7, "validated": false },
{ "id": "asm_resume_parse_accuracy", "type": "assumption", "label": "PDF parses correctly into JSON Resume", "description": "LLM-assisted bootstrap captures the user's PDF resume accurately enough for one-time manual review.", "confidence": 0.7, "validated": false },
{ "id": "asm_html_template_renders", "type": "assumption", "label": "HTML template renders consistently to PDF", "description": "Chosen Handlebars templates print reliably under headless Chromium across content lengths.", "confidence": 0.75, "validated": false },
{ "id": "asm_docker_playwright_apple_silicon", "type": "assumption", "label": "Playwright Docker image works on user's Mac", "description": "Microsoft Playwright base image supports the user's host arch (esp. Apple Silicon) without browser-launch issues.", "confidence": 0.8, "validated": false },
{ "id": "asm_grounding_whitelist_complete", "type": "assumption", "label": "Whitelist captures all valid claims", "description": "Tokenising the master profile into companies/dates/skills/titles is sufficient to catch fabricated content without too many false positives.", "confidence": 0.7, "validated": false },
{ "id": "risk_bot_detection", "type": "risk", "label": "Bot detection breaks scraping silently", "description": "A site update can shadow-ban or serve fake/empty content without throwing errors.", "severity": 0.85 },
{ "id": "risk_session_invalidation", "type": "risk", "label": "Session invalidated overnight", "description": "Auth-walled site logs the session out; pipeline can't recover unattended.", "severity": 0.75 },
{ "id": "risk_tos_account_action", "type": "risk", "label": "Personal account restricted/banned", "description": "Repeated automated access could trigger account-level enforcement.", "severity": 0.7 },
{ "id": "risk_dom_drift", "type": "risk", "label": "Adapter silently produces wrong fields", "description": "Site markup changes; adapter still 'succeeds' but with wrong data.", "severity": 0.8 },
{ "id": "risk_llm_outage", "type": "risk", "label": "LLM API outage or throttling", "description": "Hosted LLM rate-limits or returns 5xx mid-run; resumes fail to generate.", "severity": 0.5 },
{ "id": "risk_silent_overnight_failure", "type": "risk", "label": "Silent overnight failure", "description": "Pipeline crashes or no-ops; user wakes up to nothing with no signal.", "severity": 0.75 },
{ "id": "risk_llm_hallucinates_resume", "type": "risk", "label": "LLM fabricates document content", "description": "LLM invents employers/dates/skills the user doesn't have; user submits without catching it.", "severity": 0.8 },
{ "id": "risk_dedup_misses", "type": "risk", "label": "Dedup fingerprint misses cross-board re-posts", "description": "Same role on multiple boards with different IDs/URLs is counted as N distinct jobs.", "severity": 0.6 },
{ "id": "risk_run_exceeds_window", "type": "risk", "label": "Run exceeds overnight window", "description": "Total wall-clock time pushes past morning; partial output.", "severity": 0.5 },
{ "id": "risk_grounding_too_strict", "type": "risk", "label": "Grounding validator over-rejects", "description": "Whitelist false-positives cause many jobs to be rejected after two LLM attempts; low yield.", "severity": 0.5 },
{ "id": "tst_adapter_unit", "type": "test", "label": "Per-adapter HTML-fixture unit tests", "description": "Each adapter has tests/fixtures/<adapter>/ with saved listing pages; tests load each fixture, run the adapter parser, assert exact normalised-Job output.", "test_type": "unit", "status": "planned" },
{ "id": "tst_adapter_conformance", "type": "test", "label": "Adapter conformance suite", "description": "Loops every registered adapter, runs against fixtures, validates output against the Job JSON Schema.", "test_type": "conformance", "status": "planned" },
{ "id": "tst_orchestrator_integration", "type": "test", "label": "Orchestrator integration with mocks", "description": "Runs full pipeline with mock adapters, mock LLM, temp SQLite. Asserts dedup, filter, generation, artifact write, notification.", "test_type": "integration", "status": "planned" },
{ "id": "tst_resume_grounding", "type": "test", "label": "Grounding validator tests", "description": "Tests the validator rejects LLM outputs containing employers/dates/skills/titles not in the master profile. Includes adversarial fixtures (fabricated company, swapped dates).", "test_type": "unit", "status": "planned" },
{ "id": "tst_dedup_property", "type": "test", "label": "Dedup fingerprint property tests", "description": "Property-based: variations of same listing collapse to same fingerprint; genuinely different listings don't.", "test_type": "unit", "status": "planned" },
{ "id": "tst_notifier_always_fires", "type": "test", "label": "Notifier-always-fires test", "description": "Integration test: orchestrator with all stages forced to throw still invokes the notifier exactly once with a failure summary.", "test_type": "integration", "status": "planned" },
{ "id": "tst_session_expired_signal", "type": "test", "label": "Session-expired urgent-alert test", "description": "Adapter under fixture login-redirect raises SessionExpiredError; orchestrator marks adapter, fires urgent webhook, continues.", "test_type": "integration", "status": "planned" },
{ "id": "tst_resume_render_snapshot", "type": "test", "label": "PDF snapshot tests", "description": "Rendering known JSON Resume + cover letter inputs produces PDFs whose extracted text matches snapshots. Catches template regressions.", "test_type": "unit", "status": "planned" },
{ "id": "tst_resume_cover_grounding", "type": "test", "label": "Cover letter grounding tests", "description": "Same grounding validator applied to cover letter outputs; adversarial fixtures included.", "test_type": "unit", "status": "planned" }
],
"edges": [
{ "type": "motivated_by", "source_id": "dec_playwright", "target_id": "obj_multi_board_coverage" },
{ "type": "motivated_by", "source_id": "dec_auth_mixed", "target_id": "obj_multi_board_coverage" },
{ "type": "motivated_by", "source_id": "dec_session_storage_state", "target_id": "obj_overnight_run" },
{ "type": "motivated_by", "source_id": "dec_session_urgent_alert", "target_id": "obj_overnight_run" },
{ "type": "motivated_by", "source_id": "dec_session_urgent_alert", "target_id": "req_urgent_alerts" },
{ "type": "motivated_by", "source_id": "dec_per_site_adapters", "target_id": "obj_offline_testable" },
{ "type": "motivated_by", "source_id": "dec_per_site_adapters", "target_id": "obj_multi_board_coverage" },
{ "type": "motivated_by", "source_id": "dec_llm_hosted", "target_id": "req_tailored_pdf" },
{ "type": "motivated_by", "source_id": "dec_llm_hosted", "target_id": "req_tailored_cover" },
{ "type": "motivated_by", "source_id": "dec_docker", "target_id": "obj_overnight_run" },
{ "type": "motivated_by", "source_id": "dec_host_launchd", "target_id": "obj_overnight_run" },
{ "type": "motivated_by", "source_id": "dec_webhook_notify", "target_id": "obj_overnight_run" },
{ "type": "motivated_by", "source_id": "dec_jsonresume", "target_id": "req_tailored_pdf" },
{ "type": "motivated_by", "source_id": "dec_resume_bootstrap_once", "target_id": "req_tailored_pdf" },
{ "type": "motivated_by", "source_id": "dec_llm_grounded_rewrite", "target_id": "req_no_resume_fabrication" },
{ "type": "motivated_by", "source_id": "dec_artifacts_only", "target_id": "obj_human_in_loop_submit" },
{ "type": "motivated_by", "source_id": "dec_per_stage_retry", "target_id": "req_error_recovery" },
{ "type": "motivated_by", "source_id": "dec_checkpoint_db", "target_id": "req_resumable_run" },
{ "type": "motivated_by", "source_id": "dec_polite_concurrency", "target_id": "obj_overnight_run" },
{ "type": "motivated_by", "source_id": "dec_test_layers", "target_id": "req_offline_test_harness" },
{ "type": "motivated_by", "source_id": "dec_cover_letter_pdf", "target_id": "req_tailored_cover" },
{ "type": "implements", "source_id": "comp_db", "target_id": "req_dedup" },
{ "type": "implements", "source_id": "comp_orchestrator", "target_id": "req_error_recovery" },
{ "type": "implements", "source_id": "comp_orchestrator", "target_id": "req_resumable_run" },
{ "type": "implements", "source_id": "comp_resume_gen", "target_id": "req_tailored_pdf" },
{ "type": "implements", "source_id": "comp_cover_letter_gen", "target_id": "req_tailored_cover" },
{ "type": "implements", "source_id": "comp_filter", "target_id": "req_filter_relevance" },
{ "type": "implements", "source_id": "comp_test_harness", "target_id": "req_offline_test_harness" },
{ "type": "implements", "source_id": "comp_scraper_engine", "target_id": "req_dynamic_loading" },
{ "type": "implements", "source_id": "comp_notifier", "target_id": "req_run_visibility" },
{ "type": "implements", "source_id": "comp_notifier", "target_id": "req_urgent_alerts" },
{ "type": "implements", "source_id": "comp_resume_gen", "target_id": "req_no_resume_fabrication" },
{ "type": "implements", "source_id": "comp_cover_letter_gen", "target_id": "req_no_resume_fabrication" },
{ "type": "implements", "source_id": "comp_artifact_writer", "target_id": "req_artifact_folder" },
{ "type": "exposes", "source_id": "comp_scraper_engine", "target_id": "iface_scraper_adapter" },
{ "type": "exposes", "source_id": "comp_scraper_engine", "target_id": "iface_job_schema" },
{ "type": "exposes", "source_id": "comp_db", "target_id": "iface_db_repo" },
{ "type": "exposes", "source_id": "comp_resume_gen", "target_id": "iface_resume_render_input" },
{ "type": "exposes", "source_id": "comp_cover_letter_gen", "target_id": "iface_resume_render_input" },
{ "type": "exposes", "source_id": "comp_notifier", "target_id": "iface_run_summary" },
{ "type": "exposes", "source_id": "comp_notifier", "target_id": "iface_urgent_alert" },
{ "type": "consumes", "source_id": "comp_db", "target_id": "iface_job_schema" },
{ "type": "consumes", "source_id": "comp_filter", "target_id": "iface_job_schema" },
{ "type": "consumes", "source_id": "comp_filter", "target_id": "iface_user_profile" },
{ "type": "consumes", "source_id": "comp_resume_gen", "target_id": "iface_user_profile" },
{ "type": "consumes", "source_id": "comp_resume_gen", "target_id": "iface_job_schema" },
{ "type": "consumes", "source_id": "comp_cover_letter_gen", "target_id": "iface_user_profile" },
{ "type": "consumes", "source_id": "comp_cover_letter_gen", "target_id": "iface_job_schema" },
{ "type": "consumes", "source_id": "comp_pdf_renderer", "target_id": "iface_resume_render_input" },
{ "type": "consumes", "source_id": "comp_notifier", "target_id": "iface_run_summary" },
{ "type": "consumes", "source_id": "comp_notifier", "target_id": "iface_urgent_alert" },
{ "type": "consumes", "source_id": "comp_artifact_writer", "target_id": "iface_job_schema" },
{ "type": "depends_on", "source_id": "comp_orchestrator", "target_id": "comp_scraper_engine" },
{ "type": "depends_on", "source_id": "comp_orchestrator", "target_id": "comp_db" },
{ "type": "depends_on", "source_id": "comp_orchestrator", "target_id": "comp_filter" },
{ "type": "depends_on", "source_id": "comp_orchestrator", "target_id": "comp_artifact_writer" },
{ "type": "depends_on", "source_id": "comp_orchestrator", "target_id": "comp_notifier" },
{ "type": "depends_on", "source_id": "comp_orchestrator", "target_id": "comp_retry" },
{ "type": "depends_on", "source_id": "comp_orchestrator", "target_id": "comp_logger" },
{ "type": "depends_on", "source_id": "comp_scraper_engine", "target_id": "comp_session_store" },
{ "type": "depends_on", "source_id": "comp_scraper_engine", "target_id": "comp_retry" },
{ "type": "depends_on", "source_id": "comp_artifact_writer", "target_id": "comp_resume_gen" },
{ "type": "depends_on", "source_id": "comp_artifact_writer", "target_id": "comp_cover_letter_gen" },
{ "type": "depends_on", "source_id": "comp_artifact_writer", "target_id": "comp_db" },
{ "type": "depends_on", "source_id": "comp_resume_gen", "target_id": "comp_llm_client" },
{ "type": "depends_on", "source_id": "comp_resume_gen", "target_id": "comp_pdf_renderer" },
{ "type": "depends_on", "source_id": "comp_cover_letter_gen", "target_id": "comp_llm_client" },
{ "type": "depends_on", "source_id": "comp_cover_letter_gen", "target_id": "comp_pdf_renderer" },
{ "type": "depends_on", "source_id": "comp_test_harness", "target_id": "comp_scraper_engine" },
{ "type": "depends_on", "source_id": "comp_profile_bootstrap", "target_id": "comp_llm_client" },
{ "type": "depends_on", "source_id": "comp_docker_image", "target_id": "comp_orchestrator" },
{ "type": "assumes", "source_id": "dec_session_storage_state", "target_id": "asm_session_longevity" },
{ "type": "assumes", "source_id": "dec_session_storage_state", "target_id": "asm_no_midrun_captcha" },
{ "type": "assumes", "source_id": "dec_session_storage_state", "target_id": "asm_tos_personal_use" },
{ "type": "assumes", "source_id": "dec_per_site_adapters", "target_id": "asm_dom_stable" },
{ "type": "assumes", "source_id": "dec_llm_hosted", "target_id": "asm_llm_budget_ok" },
{ "type": "assumes", "source_id": "dec_resume_bootstrap_once", "target_id": "asm_resume_parse_accuracy" },
{ "type": "assumes", "source_id": "dec_pdf_via_html", "target_id": "asm_html_template_renders" },
{ "type": "assumes", "source_id": "dec_docker", "target_id": "asm_docker_playwright_apple_silicon" },
{ "type": "assumes", "source_id": "dec_llm_grounded_rewrite", "target_id": "asm_grounding_whitelist_complete" },
{ "type": "conflicts_with", "source_id": "risk_bot_detection", "target_id": "dec_playwright" },
{ "type": "conflicts_with", "source_id": "risk_dom_drift", "target_id": "dec_per_site_adapters" },
{ "type": "conflicts_with", "source_id": "risk_session_invalidation", "target_id": "dec_session_storage_state" },
{ "type": "conflicts_with", "source_id": "risk_tos_account_action", "target_id": "dec_session_storage_state" },
{ "type": "conflicts_with", "source_id": "risk_llm_outage", "target_id": "dec_llm_hosted" },
{ "type": "conflicts_with", "source_id": "risk_silent_overnight_failure", "target_id": "obj_overnight_run" },
{ "type": "conflicts_with", "source_id": "risk_llm_hallucinates_resume", "target_id": "req_no_resume_fabrication" },
{ "type": "conflicts_with", "source_id": "risk_dedup_misses", "target_id": "req_dedup" },
{ "type": "conflicts_with", "source_id": "risk_run_exceeds_window", "target_id": "obj_overnight_run" },
{ "type": "conflicts_with", "source_id": "risk_grounding_too_strict", "target_id": "dec_llm_grounded_rewrite" },
{ "type": "invalidates", "source_id": "risk_session_invalidation", "target_id": "asm_session_longevity" },
{ "type": "invalidates", "source_id": "risk_bot_detection", "target_id": "asm_no_midrun_captcha" },
{ "type": "invalidates", "source_id": "risk_dom_drift", "target_id": "asm_dom_stable" },
{ "type": "invalidates", "source_id": "risk_llm_hallucinates_resume", "target_id": "asm_grounding_whitelist_complete" },
{ "type": "verifies", "source_id": "tst_adapter_unit", "target_id": "comp_scraper_engine" },
{ "type": "verifies", "source_id": "tst_adapter_conformance", "target_id": "iface_scraper_adapter" },
{ "type": "verifies", "source_id": "tst_orchestrator_integration", "target_id": "comp_orchestrator" },
{ "type": "verifies", "source_id": "tst_resume_grounding", "target_id": "comp_resume_gen" },
{ "type": "verifies", "source_id": "tst_resume_cover_grounding", "target_id": "comp_cover_letter_gen" },
{ "type": "verifies", "source_id": "tst_dedup_property", "target_id": "comp_db" },
{ "type": "verifies", "source_id": "tst_notifier_always_fires", "target_id": "comp_notifier" },
{ "type": "verifies", "source_id": "tst_session_expired_signal", "target_id": "comp_session_store" },
{ "type": "verifies", "source_id": "tst_resume_render_snapshot", "target_id": "comp_pdf_renderer" },
{ "type": "validates", "source_id": "tst_adapter_conformance", "target_id": "dec_per_site_adapters" },
{ "type": "validates", "source_id": "tst_resume_grounding", "target_id": "dec_llm_grounded_rewrite" },
{ "type": "validates", "source_id": "tst_resume_cover_grounding", "target_id": "dec_llm_grounded_rewrite" },
{ "type": "validates", "source_id": "tst_dedup_property", "target_id": "dec_dedup_multikey" },
{ "type": "guards_against", "source_id": "tst_adapter_unit", "target_id": "risk_dom_drift" },
{ "type": "guards_against", "source_id": "tst_adapter_conformance", "target_id": "risk_dom_drift" },
{ "type": "guards_against", "source_id": "tst_resume_grounding", "target_id": "risk_llm_hallucinates_resume" },
{ "type": "guards_against", "source_id": "tst_resume_cover_grounding", "target_id": "risk_llm_hallucinates_resume" },
{ "type": "guards_against", "source_id": "tst_dedup_property", "target_id": "risk_dedup_misses" },
{ "type": "guards_against", "source_id": "tst_notifier_always_fires", "target_id": "risk_silent_overnight_failure" },
{ "type": "guards_against", "source_id": "tst_session_expired_signal", "target_id": "risk_session_invalidation" }
]
}
[/GRAPH UPDATE]
Graph is complete: every major decision has rationale + alternatives, every assumption with confidence < 0.7 is acknowledged, and every risk with severity > 0.6 has either a guard test, a mitigating decision, or an explicit detection signal. Writing the final plan now.


user: so could you explain how this runs end to end?

cursor: Here is an end-to-end picture of how a nightly (or manual) run works in this repo.
1. How you start it
The main entry is npm run run, which runs tsx src/cli/run.ts (package.json "run" script). That CLI:
Parses --resume <uuid> (reuse that run id in the DB) and --once (only affects logging today).
Requires at least one of OPENAI_API_KEY / ANTHROPIC_API_KEY.
Resolves paths via COND_B_* (or defaults under ./config, ./data, ./profile).
Builds a logger, LLM client, and webhook notifier from notify.yml, then calls executePipeline.
run.ts
Lines 22-48
On success it posts a summary webhook; on fatal failure it still tries to send a minimal summary.
2. What executePipeline does (the real “pipeline”)
executePipeline in src/orchestrator/pipeline.ts is the staged orchestrator.
Setup
Reads boards.yml, pipeline.yml, and your JSON Resume from profilePath.
Opens SQLite, runs Drizzle migrations, then creates a run row if that runId is new.
Computes a wall-clock deadline from max_runtime_minutes.
Optionally prunes old dated folders under data/outputs/ using retention_days.
Browser or not
It builds runnableBoards: enabled boards that have a known adapter, a search_url, and (if the adapter needs auth) an on-disk Playwright storageState file.
Playwright is only started when runnableBoards.length > 0. If everything is disabled or missing sessions/URLs, no browser is launched (good for CI/smoke).
pipeline.ts
Lines 97-113
Stage A — Scrape
For each enabled board: resolve adapter, init per-adapter stats.
If auth is required but the session file is missing → mark needsRelogin, push to sessionsExpired, send an urgent webhook, skip that board.
Otherwise ScrapeEngine runs the adapter against search_url / caps, yielding normalized job records. Each row is upserted into SQLite (dedupe / fingerprinting happens in the repo layer). Errors:
SessionExpiredError → urgent webhook + needsRelogin.
Other errors → circuit breaker + logRunError.
Adapter health is written back to the DB per board. Then the browser is stopped in a finally if it was started.
Stage B — Filter
Run stage is updated to "filter".
For every job id seen this run, load the job, scoreJob against the profile, store score/reason on the job row, and collect ids that pass.
Stage C — Generate
Run stage → "generate".
listJobsToGenerate picks jobs that passed filtering, meet filter_min_score, and respects max_generations_per_run (and DB rules about what still needs artifacts).
For each selected job: insert a generation row, call tailorResumeForJob and tailorCoverForJob (LLM + grounding checks), then writeJobArtifacts (PDFs + sidecar files under data/outputs/<date>/...). Success/failure updates the generation row; failures append to the run summary’s failures.
Finish
Builds a RunSummary (per-adapter stats, filter count, generated count, failures, session issues), finishRun persists it, closes SQLite, returns the summary to the CLI → summary webhook.
pipeline.ts
Lines 229-319
3. How that fits with the rest of the “product”
npm run login -- linkedin|wellfound: one-time (or occasional) headed login; writes storageState JSON so auth-walled boards can be “runnable.”
npm run bootstrap: builds/refines profile/master.json from a resume file (separate from the nightly scrape loop).
Scheduling: same Node process (npm run run) from cron, launchd, or docker compose run pipeline — the in-process behavior is identical; only the wrapper changes.
So end-to-end: config + profile + optional session files → run CLI → migrate + run record → optional Playwright scrape per board → SQLite jobs → score/filter → LLM-tailored PDFs + artifacts on disk → DB completion + webhooks. Nothing in this path auto-submits applications; outputs are for your review.

user: so for generating packets, LLMs are called. what about for scoring and filtering?

cursor: Scoring and filtering do not call the LLM. They are plain TypeScript heuristics over structured Job data plus your UserProfile (x_preferences).
Hard filter — hardExclude in src/filter/rules.ts scans job.title + job.descriptionText (lowercased) for any exclude_keywords from the profile. If one matches, the job fails immediately with reason like exclude_keyword:….
rules.ts
Lines 4-11
Score — If not excluded, scoreJob in src/filter/score.ts adds weighted signals: substring overlap with profile skills in title+description, title match against target_roles, remote_pref vs job.remote, location list vs job.location, and a simple seniority guess from keywords in title+description vs x_preferences.seniority. It sums those into a score, caps at 100, and sets pass when score >= 40 (that 40 is fixed in code, not the LLM).
score.ts
Lines 76-92
export function scoreJob(job: Job, profile: UserProfile): FilterResult {
  const ex = hardExclude(job, profile);
  if (ex) return { pass: false, score: 0, reason: ex };
  let score = 0;
  score += skillOverlap(job, profile);
  score += roleMatch(job, profile);
  score += remoteMatch(job, profile);
  score += locationMatch(job, profile);
  score += senioritySignal(job, profile);
  const pass = score >= 40;
  return {
    pass,
    score: Math.round(Math.min(100, score)),
    reason: pass ? "ok" : "below_threshold",
  };
}
The generation step later uses pipeline.filter_min_score from config/pipeline.yml (default 40 in loadYaml.ts) when listJobsToGenerate picks which passed jobs get packets—still no LLM for that selection; the LLM is only for tailoring resume/cover content inside tailorResumeForJob / tailorCoverForJob.