# Software architecture planning and decision graph
---

**User**

You are a software architecture planner. As you help design a project, you maintain a structured decision graph that captures the planning intent — what the system aims to achieve, what was decided and why, what is being assumed, and what could go wrong.

The graph is your working memory. You build it incrementally as decisions are made, and you use it to ask targeted follow-up questions before writing the final plan.

---

## GRAPH SCHEMA

The graph has nodes and edges. Every node has: id (short snake_case, unique), type, label (concise noun phrase), description (1–2 sentences).

### Node types

**objective** — what the system is trying to achieve.
Extra fields: none
Example: { "id": "obj_overnight_run", "type": "objective", "label": "Unattended overnight execution", "description": "The pipeline must run start-to-finish without human intervention." }

**requirement** — a hard constraint or must-have. Non-negotiable.
Extra fields: is_functional (bool, default true)
Example: { "id": "req_dedup", "type": "requirement", "label": "Cross-run deduplication", "description": "The database must not store duplicate listings across pipeline runs.", "is_functional": true }

**assumption** — CRITICAL. Something the plan treats as true without explicit verification. Implicit beliefs about the environment, technology choices with hidden prerequisites, things that "should work."
Extra fields: confidence (0.0–1.0, lower = more uncertain), validated (bool, default false)
Example: { "id": "asm_cookie_longevity", "type": "assumption", "label": "Session cookies survive overnight run", "description": "Assumes saved cookies remain valid for the 2–4 hour duration of a pipeline run.", "confidence": 0.6, "validated": false }

**decision** — an explicit architectural or design choice. Must capture what was chosen and what was rejected.
Extra fields: rationale (string), alternatives_considered (list of strings)
Example: { "id": "dec_sqlite", "type": "decision", "label": "Use SQLite via SQLAlchemy", "description": "SQLite chosen as the persistent store.", "rationale": "Single-machine pipeline, no server to manage, portable.", "alternatives_considered": ["PostgreSQL", "DuckDB"] }

**component** — a concrete module, service, library, or subsystem.
Extra fields: file_refs (list of strings, optional), has_tests (bool, default false — true only when a passing test node points at it via a verifies edge)
Example: { "id": "comp_scraper", "type": "component", "label": "Scraper engine", "description": "Playwright-based scraper with per-site adapters.", "has_tests": false }

**interface** — an API, schema, data contract, or formal boundary between components.
Extra fields: contract (string, optional)
Example: { "id": "iface_job_schema", "type": "interface", "label": "Normalised job listing schema", "description": "Common contract all scraper adapters must output.", "contract": "{ title, company, url, source, scraped_at, description }" }

**risk** — CRITICAL. A concern, tradeoff, potential failure mode, or known limitation. Things that might break, external dependencies that could change, reliability gaps.
Extra fields: severity (0.0–1.0, higher = more severe)
Example: { "id": "risk_bot_detection", "type": "risk", "label": "Bot detection breaks scraping", "description": "Job boards may update bot detection at any time, silently breaking scrapers.", "severity": 0.85 }

**test** — a specific testing artifact. Extract only when the conversation explicitly mentions tests for particular components.
Extra fields: test_type ("unit" | "integration" | "conformance" | "end-to-end" | "security"), status ("planned" | "written" | "passing" | "failing")
Example: { "id": "tst_scraper_parse", "type": "test", "label": "Scraper HTML parsing tests", "description": "Unit tests that load saved HTML fixtures and assert correct field extraction.", "test_type": "unit", "status": "planned" }

### Edge types

| type | meaning | typical source → target |
|------|---------|------------------------|
| motivated_by | a decision or component exists because of an objective | Decision → Objective |
| assumes | a decision or component relies on an assumption being true | Decision → Assumption |
| implements | a component fulfils a requirement | Component → Requirement |
| depends_on | a component needs another component or interface | Component → Component or Interface |
| conflicts_with | a risk threatens a decision or requirement | Risk → Decision or Requirement |
| invalidates | if a risk materialises, it breaks an assumption | Risk → Assumption |
| exposes | a component provides an interface | Component → Interface |
| consumes | a component uses an interface | Component → Interface |
| verifies | a test directly checks a component or interface | Test → Component or Interface |
| guards_against | a test prevents a risk from reaching production | Test → Risk |
| validates | a test confirms a decision was correctly implemented | Test → Decision |

---

## PLANNING BEHAVIOR

### Three rules you must follow at all times

**1. Every choice becomes a decision node.**
Any time you choose one approach over another — a library, an architecture pattern, a data model, a processing strategy, a workflow, an organizational structure, how a team will operate — record it as a `decision` node immediately. Do not let choices stay implicit in prose. Include `rationale` and `alternatives_considered` where genuine alternatives exist; omit `alternatives_considered` only when no meaningful alternative applies, not to keep the graph tidy.

**2. Push back when a better approach exists.**
Before accepting any choice as final — including choices suggested by the user — consider whether a stronger alternative exists given the stated objectives. You are not limited to alternatives already in the graph; draw on what you know. If you believe a different approach would better serve the goal, surface it explicitly and ask the user to confirm before proceeding. Do not silently adopt an approach when you have reason to question it.

**3. Every uncertainty becomes an assumption node.**
Any time you are not certain something will work — a technology behaves as expected, an external dependency is reliable, a process or workflow will hold up in practice, an organizational assumption will be met — record it as an `assumption` node with an honest `confidence` score. Do not bury uncertainty in component descriptions. If confidence is below 0.7, you must ask the user about it before writing the final plan.

---

### Phase structure

Work through the plan in phases. After each phase, before moving to the next:

1. Output the full updated graph (all nodes and edges so far) inside a `[GRAPH UPDATE]` block.
2. Review the graph for gaps. Ask the user 2–3 targeted questions specifically about:
   - Assumptions with confidence < 0.7 that haven't been validated
   - High-severity risks (> 0.6) with no mitigation or guards_against edge
   - Decisions where you have reason to question the chosen approach
3. Incorporate the answers, update the graph if needed, then continue to the next phase.

Do not write the final implementation plan until you are satisfied the graph is complete — all major decisions have rationale and alternatives, key assumptions are acknowledged, and significant risks are captured.

- **Phase 1**: Clarifying questions → core architectural decisions (runtime, storage, major frameworks)
- **Phase 2**: Component design, interfaces, dependencies
- **Phase 3**: Testing strategy, error handling, deployment
- **Final**: Write the full implementation plan, grounded in the completed graph

---

## GRAPH OUTPUT FORMAT

When outputting a graph update, use this exact format so it can be parsed programmatically:

[GRAPH UPDATE]
{
  "nodes": [ ...all nodes so far... ],
  "edges": [ ...all edges so far... ]
}
[/GRAPH UPDATE]

Then ask your follow-up questions below the block.

Rules:
- Every edge source_id and target_id must match an id in the nodes array.
- Use consistent, readable ids (e.g. "dec_use_sqlite", "asm_rate_limits_stable").
- The graph is cumulative — always output the full graph, not just new nodes.
- Aim for 15–25 nodes in a complete graph. Completeness over brevity.


@prompt.txt (1-10) 

---

**Cursor**

[GRAPH UPDATE]
{
  "nodes": [
    {
      "id": "obj_personalized_digest",
      "type": "objective",
      "label": "Personalized daily content digest",
      "description": "Deliver a concise daily digest of relevant content tailored to a user profile."
    },
    {
      "id": "obj_unattended_overnight",
      "type": "objective",
      "label": "Unattended overnight execution",
      "description": "Run the full pipeline on a schedule without manual intervention and recover from failures."
    },
    {
      "id": "req_multi_source_ingest",
      "type": "requirement",
      "label": "Multi-source public content ingestion",
      "description": "Collect content from blogs, news, RSS feeds, and forums, including pagination and basic dynamic loading.",
      "is_functional": true
    },
    {
      "id": "req_persistent_dedup",
      "type": "requirement",
      "label": "Persistent cross-run deduplication",
      "description": "Store content in a persistent database and prevent duplicate records across runs.",
      "is_functional": true
    },
    {
      "id": "req_relevance_filtering",
      "type": "requirement",
      "label": "Profile-based filtering and ranking",
      "description": "Score and rank items by topics, keywords, and preferred sources from a user profile.",
      "is_functional": true
    },
    {
      "id": "req_summary_and_digest",
      "type": "requirement",
      "label": "Summaries and formatted digest output",
      "description": "Generate concise summaries for relevant items and produce a clean daily digest in email or PDF form.",
      "is_functional": true
    },
    {
      "id": "req_observability_recovery",
      "type": "requirement",
      "label": "Robust logging and error recovery",
      "description": "Provide structured logging, fault handling, and retry/recovery behavior for unattended runs.",
      "is_functional": true
    },
    {
      "id": "req_snapshot_test_harness",
      "type": "requirement",
      "label": "Snapshot-based parser validation",
      "description": "Validate parsing and extraction logic using saved snapshots instead of live source calls.",
      "is_functional": true
    },
    {
      "id": "dec_python_orchestration",
      "type": "decision",
      "label": "Use Python as orchestration runtime",
      "description": "Implement ingestion, ranking, summarization orchestration, and scheduling in Python.",
      "rationale": "Strong ecosystem for scraping, NLP, data processing, and testing with low operational overhead for a single-project pipeline.",
      "alternatives_considered": ["Node.js/TypeScript", "Go"]
    },
    {
      "id": "dec_postgresql_storage",
      "type": "decision",
      "label": "Use PostgreSQL for persistent content store",
      "description": "Store normalized content, fingerprints, user profiles, runs, and digest artifacts in PostgreSQL.",
      "rationale": "Better concurrency, indexing, and reliability for long-running growth than SQLite, while keeping schema flexibility.",
      "alternatives_considered": ["SQLite", "DuckDB"]
    },
    {
      "id": "dec_hybrid_collection",
      "type": "decision",
      "label": "Hybrid feed-first collection strategy",
      "description": "Use RSS/API ingestion first and only use headless browser scraping for sources that require dynamic rendering.",
      "rationale": "Reduces fragility, runtime, and bot-detection risk compared with full browser scraping everywhere.",
      "alternatives_considered": ["Browser-only scraping", "RSS/API-only ingestion"]
    },
    {
      "id": "asm_sources_allow_collection",
      "type": "assumption",
      "label": "Target sources permit automated collection",
      "description": "Assumes robots policies and terms permit the planned level of ingestion and scraping.",
      "confidence": 0.55,
      "validated": false
    },
    {
      "id": "asm_profile_signal_quality",
      "type": "assumption",
      "label": "User profile provides enough relevance signal",
      "description": "Assumes topics, keywords, and source preferences are sufficient to rank content accurately.",
      "confidence": 0.62,
      "validated": false
    },
    {
      "id": "asm_llm_summary_budget",
      "type": "assumption",
      "label": "LLM summarization cost and latency are acceptable",
      "description": "Assumes nightly volume can be summarized within budget and overnight runtime constraints.",
      "confidence": 0.58,
      "validated": false
    },
    {
      "id": "risk_source_layout_drift",
      "type": "risk",
      "label": "Source layout or markup drift",
      "description": "Site template changes can silently break extraction logic and reduce digest quality.",
      "severity": 0.78
    },
    {
      "id": "risk_bot_mitigation_failure",
      "type": "risk",
      "label": "Bot mitigation blocks collection",
      "description": "Anti-bot controls may block dynamic scraping paths and reduce source coverage.",
      "severity": 0.74
    },
    {
      "id": "risk_digest_quality_mismatch",
      "type": "risk",
      "label": "Digest quality misses user intent",
      "description": "Filtering and summarization may over-compress or miss relevant items, reducing trust.",
      "severity": 0.67
    }
  ],
  "edges": [
    {
      "type": "motivated_by",
      "source_id": "dec_python_orchestration",
      "target_id": "obj_unattended_overnight"
    },
    {
      "type": "motivated_by",
      "source_id": "dec_postgresql_storage",
      "target_id": "obj_unattended_overnight"
    },
    {
      "type": "motivated_by",
      "source_id": "dec_hybrid_collection",
      "target_id": "obj_personalized_digest"
    },
    {
      "type": "assumes",
      "source_id": "dec_hybrid_collection",
      "target_id": "asm_sources_allow_collection"
    },
    {
      "type": "assumes",
      "source_id": "dec_python_orchestration",
      "target_id": "asm_llm_summary_budget"
    },
    {
      "type": "assumes",
      "source_id": "dec_python_orchestration",
      "target_id": "asm_profile_signal_quality"
    },
    {
      "type": "conflicts_with",
      "source_id": "risk_source_layout_drift",
      "target_id": "req_multi_source_ingest"
    },
    {
      "type": "conflicts_with",
      "source_id": "risk_bot_mitigation_failure",
      "target_id": "req_multi_source_ingest"
    },
    {
      "type": "conflicts_with",
      "source_id": "risk_digest_quality_mismatch",
      "target_id": "req_relevance_filtering"
    },
    {
      "type": "invalidates",
      "source_id": "risk_bot_mitigation_failure",
      "target_id": "asm_sources_allow_collection"
    },
    {
      "type": "conflicts_with",
      "source_id": "risk_source_layout_drift",
      "target_id": "req_snapshot_test_harness"
    }
  ]
}
[/GRAPH UPDATE]

1. **Compliance/collection scope (assumption 0.55):** Are all target sources strictly those that permit crawling via terms/robots, or do you want the system to include sources that may require manual allowlisting and legal review before enabling?  
2. **Storage pushback (questioning decision):** I proposed PostgreSQL for growth/reliability, but if this is truly single-user/single-machine, SQLite could cut complexity. Do you prefer operational simplicity (`SQLite`) or future scale/concurrency (`PostgreSQL`)?  
3. **High-risk quality/cost controls (assumptions 0.62/0.58 + risks):** Do you want a two-stage relevance flow (cheap keyword/BM25 prefilter + LLM rerank/summarize) to control cost and improve precision, or an LLM-heavy approach from the start?

---

**User**

Look at graph_v1.json and update that.
Yes, keep legal contraints in mind, use SQLite, no preference on the LLM approach

---

**Cursor**

Understood — I’ll load `graph_v1.json`, incorporate your decisions (legal constraints, SQLite), and update the graph accordingly for the next phase.

I found the current graph and am now applying your answers directly into it: switching storage to SQLite, adding explicit legal-compliance constraints, and selecting a default LLM strategy so the plan can move forward.

Updated `condition_b/graph_v1.json` with your decisions:
- legal/compliance constraints are now explicit requirements
- storage is switched to SQLite
- no strict LLM preference is resolved with a two-stage approach (prefilter then LLM rerank/summarize)

[GRAPH UPDATE]
{
  "nodes": [
    {
      "id": "obj_personalized_digest",
      "type": "objective",
      "label": "Personalized daily content digest",
      "description": "Deliver a concise daily digest of relevant content tailored to a user profile."
    },
    {
      "id": "obj_unattended_overnight",
      "type": "objective",
      "label": "Unattended overnight execution",
      "description": "Run the full pipeline on a schedule without manual intervention and recover from failures."
    },
    {
      "id": "req_multi_source_ingest",
      "type": "requirement",
      "label": "Multi-source public content ingestion",
      "description": "Collect content from blogs, news, RSS feeds, and forums, including pagination and basic dynamic loading.",
      "is_functional": true
    },
    {
      "id": "req_persistent_dedup",
      "type": "requirement",
      "label": "Persistent cross-run deduplication",
      "description": "Store content in a persistent database and prevent duplicate records across runs.",
      "is_functional": true
    },
    {
      "id": "req_relevance_filtering",
      "type": "requirement",
      "label": "Profile-based filtering and ranking",
      "description": "Score and rank items by topics, keywords, and preferred sources from a user profile.",
      "is_functional": true
    },
    {
      "id": "req_summary_and_digest",
      "type": "requirement",
      "label": "Summaries and formatted digest output",
      "description": "Generate concise summaries for relevant items and produce a clean daily digest in email or PDF form.",
      "is_functional": true
    },
    {
      "id": "req_observability_recovery",
      "type": "requirement",
      "label": "Robust logging and error recovery",
      "description": "Provide structured logging, fault handling, and retry/recovery behavior for unattended runs.",
      "is_functional": true
    },
    {
      "id": "req_snapshot_test_harness",
      "type": "requirement",
      "label": "Snapshot-based parser validation",
      "description": "Validate parsing and extraction logic using saved snapshots instead of live source calls.",
      "is_functional": true
    },
    {
      "id": "req_compliant_collection",
      "type": "requirement",
      "label": "Legally compliant source collection",
      "description": "Only ingest from sources permitted by robots policies and terms, with an explicit allowlist gate.",
      "is_functional": true
    },
    {
      "id": "dec_python_orchestration",
      "type": "decision",
      "label": "Use Python as orchestration runtime",
      "description": "Implement ingestion, ranking, summarization orchestration, and scheduling in Python.",
      "rationale": "Strong ecosystem for scraping, NLP, data processing, and testing with low operational overhead for a single-project pipeline.",
      "alternatives_considered": [
        "Node.js/TypeScript",
        "Go"
      ]
    },
    {
      "id": "dec_sqlite_storage",
      "type": "decision",
      "label": "Use SQLite for persistent content store",
      "description": "Store normalized content, fingerprints, user profiles, runs, and digest artifacts in SQLite.",
      "rationale": "Single-machine unattended pipeline favors minimal operations and simple deployment over multi-writer scalability.",
      "alternatives_considered": [
        "PostgreSQL",
        "DuckDB"
      ]
    },
    {
      "id": "dec_hybrid_collection",
      "type": "decision",
      "label": "Hybrid feed-first collection strategy",
      "description": "Use RSS/API ingestion first and only use headless browser scraping for sources that require dynamic rendering.",
      "rationale": "Reduces fragility, runtime, and bot-detection risk compared with full browser scraping everywhere.",
      "alternatives_considered": [
        "Browser-only scraping",
        "RSS/API-only ingestion"
      ]
    },
    {
      "id": "dec_two_stage_relevance",
      "type": "decision",
      "label": "Two-stage relevance and summarization",
      "description": "Apply cheap keyword/BM25 prefiltering before LLM reranking and summarization on a reduced candidate set.",
      "rationale": "Balances quality, cost, and latency when there is no strict preference for LLM-heavy or heuristic-only ranking.",
      "alternatives_considered": [
        "LLM-only ranking and summarization",
        "Heuristic-only ranking"
      ]
    },
    {
      "id": "asm_sources_allow_collection",
      "type": "assumption",
      "label": "Allowlisted sources remain compliant",
      "description": "Assumes selected source terms and robots policies remain stable between periodic compliance reviews.",
      "confidence": 0.74,
      "validated": false
    },
    {
      "id": "asm_profile_signal_quality",
      "type": "assumption",
      "label": "User profile provides enough relevance signal",
      "description": "Assumes topics, keywords, and source preferences are sufficient to rank content accurately.",
      "confidence": 0.62,
      "validated": false
    },
    {
      "id": "asm_llm_summary_budget",
      "type": "assumption",
      "label": "LLM summarization cost and latency are acceptable",
      "description": "Assumes nightly volume can be summarized within budget and overnight runtime constraints.",
      "confidence": 0.71,
      "validated": false
    },
    {
      "id": "risk_source_layout_drift",
      "type": "risk",
      "label": "Source layout or markup drift",
      "description": "Site template changes can silently break extraction logic and reduce digest quality.",
      "severity": 0.78
    },
    {
      "id": "risk_bot_mitigation_failure",
      "type": "risk",
      "label": "Bot mitigation blocks collection",
      "description": "Anti-bot controls may block dynamic scraping paths and reduce source coverage.",
      "severity": 0.74
    },
    {
      "id": "risk_digest_quality_mismatch",
      "type": "risk",
      "label": "Digest quality misses user intent",
      "description": "Filtering and summarization may over-compress or miss relevant items, reducing trust.",
      "severity": 0.67
    },
    {
      "id": "risk_terms_change_breaks_compliance",
      "type": "risk",
      "label": "Terms changes break compliance",
      "description": "Source policy updates may invalidate prior allowlisting and force rapid source shutdowns.",
      "severity": 0.72
    }
  ],
  "edges": [
    {
      "type": "motivated_by",
      "source_id": "dec_python_orchestration",
      "target_id": "obj_unattended_overnight"
    },
    {
      "type": "motivated_by",
      "source_id": "dec_sqlite_storage",
      "target_id": "obj_unattended_overnight"
    },
    {
      "type": "motivated_by",
      "source_id": "dec_hybrid_collection",
      "target_id": "obj_personalized_digest"
    },
    {
      "type": "motivated_by",
      "source_id": "dec_two_stage_relevance",
      "target_id": "obj_personalized_digest"
    },
    {
      "type": "assumes",
      "source_id": "dec_hybrid_collection",
      "target_id": "asm_sources_allow_collection"
    },
    {
      "type": "assumes",
      "source_id": "dec_two_stage_relevance",
      "target_id": "asm_profile_signal_quality"
    },
    {
      "type": "assumes",
      "source_id": "dec_two_stage_relevance",
      "target_id": "asm_llm_summary_budget"
    },
    {
      "type": "conflicts_with",
      "source_id": "risk_source_layout_drift",
      "target_id": "req_multi_source_ingest"
    },
    {
      "type": "conflicts_with",
      "source_id": "risk_bot_mitigation_failure",
      "target_id": "req_multi_source_ingest"
    },
    {
      "type": "conflicts_with",
      "source_id": "risk_digest_quality_mismatch",
      "target_id": "req_relevance_filtering"
    },
    {
      "type": "invalidates",
      "source_id": "risk_bot_mitigation_failure",
      "target_id": "asm_sources_allow_collection"
    },
    {
      "type": "conflicts_with",
      "source_id": "risk_source_layout_drift",
      "target_id": "req_snapshot_test_harness"
    },
    {
      "type": "conflicts_with",
      "source_id": "risk_terms_change_breaks_compliance",
      "target_id": "req_compliant_collection"
    },
    {
      "type": "invalidates",
      "source_id": "risk_terms_change_breaks_compliance",
      "target_id": "asm_sources_allow_collection"
    }
  ]
}
[/GRAPH UPDATE]

1. For the low-confidence assumption (`asm_profile_signal_quality`, 0.62): should we include a lightweight feedback loop (thumbs up/down per digest item) to tune ranking over time?  
2. For high-severity risks with no test mitigations yet (`risk_source_layout_drift`, `risk_bot_mitigation_failure`, `risk_terms_change_breaks_compliance`): do you want automatic source quarantine (disable failing/non-compliant source until reviewed), or continue best-effort ingest with warnings?  
3. For compliance operations: how frequently should policy re-checks run (daily before crawl, weekly, or manual only)?

---

**User**

Look at graph_v2.json and update that.
Yes include a lghtweight feedback loop, add automatic source quarantine, run the policy daily

---

**Cursor**

I’ll open `graph_v2.json` and apply these new decisions directly: lightweight feedback loop, automatic source quarantine, and daily policy checks.

I’m updating the graph now with those three explicit decisions and linking them to the existing risks/assumptions so Phase 2 is consistent.

Updated `condition_b/graph_v2.json` with your three instructions:
- added a **lightweight feedback-loop decision**
- added **automatic source quarantine decision**
- added **daily policy-check decision**

[GRAPH UPDATE]
{
  "nodes": [
    {
      "id": "obj_personalized_digest",
      "type": "objective",
      "label": "Personalized daily content digest",
      "description": "Deliver a concise daily digest of relevant content tailored to a user profile."
    },
    {
      "id": "obj_unattended_overnight",
      "type": "objective",
      "label": "Unattended overnight execution",
      "description": "Run the full pipeline on a schedule without manual intervention and recover from failures."
    },
    {
      "id": "req_multi_source_ingest",
      "type": "requirement",
      "label": "Multi-source public content ingestion",
      "description": "Collect content from blogs, news, RSS feeds, and forums, including pagination and basic dynamic loading.",
      "is_functional": true
    },
    {
      "id": "req_persistent_dedup",
      "type": "requirement",
      "label": "Persistent cross-run deduplication",
      "description": "Store content in a persistent database and prevent duplicate records across runs.",
      "is_functional": true
    },
    {
      "id": "req_relevance_filtering",
      "type": "requirement",
      "label": "Profile-based filtering and ranking",
      "description": "Score and rank items by topics, keywords, and preferred sources from a user profile.",
      "is_functional": true
    },
    {
      "id": "req_summary_and_digest",
      "type": "requirement",
      "label": "Summaries and formatted digest output",
      "description": "Generate concise summaries for relevant items and produce a clean daily digest in email or PDF form.",
      "is_functional": true
    },
    {
      "id": "req_observability_recovery",
      "type": "requirement",
      "label": "Robust logging and error recovery",
      "description": "Provide structured logging, fault handling, and retry/recovery behavior for unattended runs.",
      "is_functional": true
    },
    {
      "id": "req_snapshot_test_harness",
      "type": "requirement",
      "label": "Snapshot-based parser validation",
      "description": "Validate parsing and extraction logic using saved snapshots instead of live source calls.",
      "is_functional": true
    },
    {
      "id": "req_compliant_collection",
      "type": "requirement",
      "label": "Legally compliant source collection",
      "description": "Only ingest from sources permitted by robots policies and terms, with an explicit allowlist gate.",
      "is_functional": true
    },
    {
      "id": "req_feedback_capture",
      "type": "requirement",
      "label": "Lightweight relevance feedback capture",
      "description": "Collect simple per-item user feedback to improve ranking quality over time.",
      "is_functional": true
    },
    {
      "id": "req_daily_policy_check",
      "type": "requirement",
      "label": "Daily source policy verification",
      "description": "Verify robots and terms constraints daily before collection starts.",
      "is_functional": true
    },
    {
      "id": "dec_python_orchestration",
      "type": "decision",
      "label": "Use Python as orchestration runtime",
      "description": "Implement ingestion, ranking, summarization orchestration, and scheduling in Python.",
      "rationale": "Strong ecosystem for scraping, NLP, data processing, and testing with low operational overhead for a single-project pipeline.",
      "alternatives_considered": [
        "Node.js/TypeScript",
        "Go"
      ]
    },
    {
      "id": "dec_sqlite_storage",
      "type": "decision",
      "label": "Use SQLite for persistent content store",
      "description": "Store normalized content, fingerprints, user profiles, runs, and digest artifacts in SQLite.",
      "rationale": "Single-machine unattended pipeline favors minimal operations and simple deployment over multi-writer scalability.",
      "alternatives_considered": [
        "PostgreSQL",
        "DuckDB"
      ]
    },
    {
      "id": "dec_hybrid_collection",
      "type": "decision",
      "label": "Hybrid feed-first collection strategy",
      "description": "Use RSS/API ingestion first and only use headless browser scraping for sources that require dynamic rendering.",
      "rationale": "Reduces fragility, runtime, and bot-detection risk compared with full browser scraping everywhere.",
      "alternatives_considered": [
        "Browser-only scraping",
        "RSS/API-only ingestion"
      ]
    },
    {
      "id": "dec_two_stage_relevance",
      "type": "decision",
      "label": "Two-stage relevance and summarization",
      "description": "Apply cheap keyword/BM25 prefiltering before LLM reranking and summarization on a reduced candidate set.",
      "rationale": "Balances quality, cost, and latency when there is no strict preference for LLM-heavy or heuristic-only ranking.",
      "alternatives_considered": [
        "LLM-only ranking and summarization",
        "Heuristic-only ranking"
      ]
    },
    {
      "id": "dec_feedback_loop_lightweight",
      "type": "decision",
      "label": "Add lightweight explicit feedback loop",
      "description": "Capture simple positive/negative feedback on digest items and feed it into ranking weight updates.",
      "rationale": "Low-friction feedback improves personalization while avoiding heavy UX and labeling overhead.",
      "alternatives_considered": [
        "No feedback loop",
        "Implicit behavior-only feedback",
        "Detailed multi-label annotation"
      ]
    },
    {
      "id": "dec_auto_source_quarantine",
      "type": "decision",
      "label": "Enable automatic source quarantine",
      "description": "Automatically disable sources that fail extraction, trigger anti-bot blocks, or fail compliance checks until reviewed.",
      "rationale": "Protects pipeline reliability and compliance by failing safely at source level instead of degrading entire runs.",
      "alternatives_considered": [
        "Best-effort continue with warnings",
        "Abort entire run on source failure"
      ]
    },
    {
      "id": "dec_daily_policy_schedule",
      "type": "decision",
      "label": "Run policy checks daily pre-collection",
      "description": "Execute source robots/terms verification as a daily gate before ingestion begins.",
      "rationale": "Daily cadence catches policy drift early while remaining operationally simple.",
      "alternatives_considered": [
        "Weekly checks",
        "Manual checks only",
        "Per-request checks during scraping"
      ]
    },
    {
      "id": "asm_sources_allow_collection",
      "type": "assumption",
      "label": "Allowlisted sources remain compliant",
      "description": "Assumes selected source terms and robots policies remain stable between daily compliance checks.",
      "confidence": 0.83,
      "validated": false
    },
    {
      "id": "asm_profile_signal_quality",
      "type": "assumption",
      "label": "User profile provides enough relevance signal",
      "description": "Assumes topics, keywords, and source preferences are sufficient to rank content accurately.",
      "confidence": 0.68,
      "validated": false
    },
    {
      "id": "asm_llm_summary_budget",
      "type": "assumption",
      "label": "LLM summarization cost and latency are acceptable",
      "description": "Assumes nightly volume can be summarized within budget and overnight runtime constraints.",
      "confidence": 0.71,
      "validated": false
    },
    {
      "id": "asm_feedback_participation",
      "type": "assumption",
      "label": "User provides enough feedback signals",
      "description": "Assumes users will submit sufficient thumbs up/down signals to improve ranking quality.",
      "confidence": 0.63,
      "validated": false
    },
    {
      "id": "risk_source_layout_drift",
      "type": "risk",
      "label": "Source layout or markup drift",
      "description": "Site template changes can silently break extraction logic and reduce digest quality.",
      "severity": 0.78
    },
    {
      "id": "risk_bot_mitigation_failure",
      "type": "risk",
      "label": "Bot mitigation blocks collection",
      "description": "Anti-bot controls may block dynamic scraping paths and reduce source coverage.",
      "severity": 0.74
    },
    {
      "id": "risk_digest_quality_mismatch",
      "type": "risk",
      "label": "Digest quality misses user intent",
      "description": "Filtering and summarization may over-compress or miss relevant items, reducing trust.",
      "severity": 0.67
    },
    {
      "id": "risk_terms_change_breaks_compliance",
      "type": "risk",
      "label": "Terms changes break compliance",
      "description": "Source policy updates may invalidate prior allowlisting and force rapid source shutdowns.",
      "severity": 0.72
    }
  ],
  "edges": [
    {
      "type": "motivated_by",
      "source_id": "dec_python_orchestration",
      "target_id": "obj_unattended_overnight"
    },
    {
      "type": "motivated_by",
      "source_id": "dec_sqlite_storage",
      "target_id": "obj_unattended_overnight"
    },
    {
      "type": "motivated_by",
      "source_id": "dec_hybrid_collection",
      "target_id": "obj_personalized_digest"
    },
    {
      "type": "motivated_by",
      "source_id": "dec_two_stage_relevance",
      "target_id": "obj_personalized_digest"
    },
    {
      "type": "motivated_by",
      "source_id": "dec_feedback_loop_lightweight",
      "target_id": "obj_personalized_digest"
    },
    {
      "type": "motivated_by",
      "source_id": "dec_auto_source_quarantine",
      "target_id": "obj_unattended_overnight"
    },
    {
      "type": "motivated_by",
      "source_id": "dec_daily_policy_schedule",
      "target_id": "obj_unattended_overnight"
    },
    {
      "type": "assumes",
      "source_id": "dec_hybrid_collection",
      "target_id": "asm_sources_allow_collection"
    },
    {
      "type": "assumes",
      "source_id": "dec_two_stage_relevance",
      "target_id": "asm_profile_signal_quality"
    },
    {
      "type": "assumes",
      "source_id": "dec_two_stage_relevance",
      "target_id": "asm_llm_summary_budget"
    },
    {
      "type": "assumes",
      "source_id": "dec_feedback_loop_lightweight",
      "target_id": "asm_feedback_participation"
    },
    {
      "type": "assumes",
      "source_id": "dec_daily_policy_schedule",
      "target_id": "asm_sources_allow_collection"
    },
    {
      "type": "conflicts_with",
      "source_id": "risk_source_layout_drift",
      "target_id": "req_multi_source_ingest"
    },
    {
      "type": "conflicts_with",
      "source_id": "risk_bot_mitigation_failure",
      "target_id": "req_multi_source_ingest"
    },
    {
      "type": "conflicts_with",
      "source_id": "risk_digest_quality_mismatch",
      "target_id": "req_relevance_filtering"
    },
    {
      "type": "invalidates",
      "source_id": "risk_bot_mitigation_failure",
      "target_id": "asm_sources_allow_collection"
    },
    {
      "type": "conflicts_with",
      "source_id": "risk_source_layout_drift",
      "target_id": "req_snapshot_test_harness"
    },
    {
      "type": "conflicts_with",
      "source_id": "risk_terms_change_breaks_compliance",
      "target_id": "req_compliant_collection"
    },
    {
      "type": "invalidates",
      "source_id": "risk_terms_change_breaks_compliance",
      "target_id": "asm_sources_allow_collection"
    },
    {
      "type": "conflicts_with",
      "source_id": "risk_source_layout_drift",
      "target_id": "dec_hybrid_collection"
    },
    {
      "type": "conflicts_with",
      "source_id": "risk_bot_mitigation_failure",
      "target_id": "dec_hybrid_collection"
    },
    {
      "type": "conflicts_with",
      "source_id": "risk_terms_change_breaks_compliance",
      "target_id": "dec_hybrid_collection"
    },
    {
      "type": "implements",
      "source_id": "dec_feedback_loop_lightweight",
      "target_id": "req_feedback_capture"
    },
    {
      "type": "implements",
      "source_id": "dec_daily_policy_schedule",
      "target_id": "req_daily_policy_check"
    },
    {
      "type": "implements",
      "source_id": "dec_auto_source_quarantine",
      "target_id": "req_observability_recovery"
    }
  ]
}
[/GRAPH UPDATE]

1. For low-confidence assumptions (`asm_profile_signal_quality` 0.68, `asm_feedback_participation` 0.63): do you want fallback behavior if feedback volume is low (e.g., keep baseline BM25 weights and only apply feedback after a minimum threshold)?  
2. For high-severity risk mitigation completeness: should quarantined sources auto-retry after N days, or stay quarantined until explicit manual re-approval?  
3. Since we’re entering testing/error-handling detail next, should the daily run fail hard when policy-check service is unavailable, or default to “no ingest” (safe mode) and still send an operational alert digest?

---

**User**

Yes fallback if feedback volume is low, auto-retry after N approvals, default to no ingest

---

**Cursor**

Perfect — I’ll apply these answers into `graph_v3.json` now: low-feedback fallback behavior, quarantine auto-retry policy, and safe-mode no-ingest default on policy-check failure.

I’m now adding three explicit decision nodes for those answers and wiring them to assumptions/risks so the graph stays machine-usable for final planning.

Applied your answers to `condition_b/graph_v3.json` and encoded each as explicit decisions/requirements.

[GRAPH UPDATE]
{
  "nodes": [
    {
      "id": "obj_personalized_digest",
      "type": "objective",
      "label": "Personalized daily content digest",
      "description": "Deliver a concise daily digest of relevant content tailored to a user profile."
    },
    {
      "id": "obj_unattended_overnight",
      "type": "objective",
      "label": "Unattended overnight execution",
      "description": "Run the full pipeline on a schedule without manual intervention and recover from failures."
    },
    {
      "id": "req_multi_source_ingest",
      "type": "requirement",
      "label": "Multi-source public content ingestion",
      "description": "Collect content from blogs, news, RSS feeds, and forums, including pagination and basic dynamic loading.",
      "is_functional": true
    },
    {
      "id": "req_persistent_dedup",
      "type": "requirement",
      "label": "Persistent cross-run deduplication",
      "description": "Store content in a persistent database and prevent duplicate records across runs.",
      "is_functional": true
    },
    {
      "id": "req_relevance_filtering",
      "type": "requirement",
      "label": "Profile-based filtering and ranking",
      "description": "Score and rank items by topics, keywords, and preferred sources from a user profile.",
      "is_functional": true
    },
    {
      "id": "req_summary_and_digest",
      "type": "requirement",
      "label": "Summaries and formatted digest output",
      "description": "Generate concise summaries for relevant items and produce a clean daily digest in email or PDF form.",
      "is_functional": true
    },
    {
      "id": "req_observability_recovery",
      "type": "requirement",
      "label": "Robust logging and error recovery",
      "description": "Provide structured logging, fault handling, and retry/recovery behavior for unattended runs.",
      "is_functional": true
    },
    {
      "id": "req_snapshot_test_harness",
      "type": "requirement",
      "label": "Snapshot-based parser validation",
      "description": "Validate parsing and extraction logic using saved snapshots instead of live source calls.",
      "is_functional": true
    },
    {
      "id": "req_compliant_collection",
      "type": "requirement",
      "label": "Legally compliant source collection",
      "description": "Only ingest from sources permitted by robots policies and terms, with an explicit allowlist gate.",
      "is_functional": true
    },
    {
      "id": "req_feedback_capture",
      "type": "requirement",
      "label": "Lightweight relevance feedback capture",
      "description": "Collect simple per-item user feedback to improve ranking quality over time.",
      "is_functional": true
    },
    {
      "id": "req_daily_policy_check",
      "type": "requirement",
      "label": "Daily source policy verification",
      "description": "Verify robots and terms constraints daily before collection starts.",
      "is_functional": true
    },
    {
      "id": "req_policy_failure_safe_mode",
      "type": "requirement",
      "label": "No-ingest safe mode on policy-check failure",
      "description": "If policy verification fails, skip ingestion for that run and emit operational alerts.",
      "is_functional": true
    },
    {
      "id": "dec_python_orchestration",
      "type": "decision",
      "label": "Use Python as orchestration runtime",
      "description": "Implement ingestion, ranking, summarization orchestration, and scheduling in Python.",
      "rationale": "Strong ecosystem for scraping, NLP, data processing, and testing with low operational overhead for a single-project pipeline.",
      "alternatives_considered": [
        "Node.js/TypeScript",
        "Go"
      ]
    },
    {
      "id": "dec_sqlite_storage",
      "type": "decision",
      "label": "Use SQLite for persistent content store",
      "description": "Store normalized content, fingerprints, user profiles, runs, and digest artifacts in SQLite.",
      "rationale": "Single-machine unattended pipeline favors minimal operations and simple deployment over multi-writer scalability.",
      "alternatives_considered": [
        "PostgreSQL",
        "DuckDB"
      ]
    },
    {
      "id": "dec_hybrid_collection",
      "type": "decision",
      "label": "Hybrid feed-first collection strategy",
      "description": "Use RSS/API ingestion first and only use headless browser scraping for sources that require dynamic rendering.",
      "rationale": "Reduces fragility, runtime, and bot-detection risk compared with full browser scraping everywhere.",
      "alternatives_considered": [
        "Browser-only scraping",
        "RSS/API-only ingestion"
      ]
    },
    {
      "id": "dec_two_stage_relevance",
      "type": "decision",
      "label": "Two-stage relevance and summarization",
      "description": "Apply cheap keyword/BM25 prefiltering before LLM reranking and summarization on a reduced candidate set.",
      "rationale": "Balances quality, cost, and latency when there is no strict preference for LLM-heavy or heuristic-only ranking.",
      "alternatives_considered": [
        "LLM-only ranking and summarization",
        "Heuristic-only ranking"
      ]
    },
    {
      "id": "dec_feedback_loop_lightweight",
      "type": "decision",
      "label": "Add lightweight explicit feedback loop",
      "description": "Capture simple positive/negative feedback on digest items and feed it into ranking weight updates.",
      "rationale": "Low-friction feedback improves personalization while avoiding heavy UX and labeling overhead.",
      "alternatives_considered": [
        "No feedback loop",
        "Implicit behavior-only feedback",
        "Detailed multi-label annotation"
      ]
    },
    {
      "id": "dec_auto_source_quarantine",
      "type": "decision",
      "label": "Enable automatic source quarantine",
      "description": "Automatically disable sources that fail extraction, trigger anti-bot blocks, or fail compliance checks until reviewed.",
      "rationale": "Protects pipeline reliability and compliance by failing safely at source level instead of degrading entire runs.",
      "alternatives_considered": [
        "Best-effort continue with warnings",
        "Abort entire run on source failure"
      ]
    },
    {
      "id": "dec_daily_policy_schedule",
      "type": "decision",
      "label": "Run policy checks daily pre-collection",
      "description": "Execute source robots/terms verification as a daily gate before ingestion begins.",
      "rationale": "Daily cadence catches policy drift early while remaining operationally simple.",
      "alternatives_considered": [
        "Weekly checks",
        "Manual checks only",
        "Per-request checks during scraping"
      ]
    },
    {
      "id": "dec_feedback_min_volume_fallback",
      "type": "decision",
      "label": "Fallback to baseline ranking on low feedback volume",
      "description": "Keep baseline BM25/keyword weights until a minimum feedback threshold is met, then apply feedback-driven tuning.",
      "rationale": "Prevents unstable personalization when explicit feedback volume is sparse.",
      "alternatives_considered": [
        "Always apply feedback updates",
        "Disable feedback-driven tuning entirely"
      ]
    },
    {
      "id": "dec_quarantine_reenable_after_n_approvals",
      "type": "decision",
      "label": "Re-enable quarantined sources after N approvals",
      "description": "Keep sources quarantined until they receive N explicit approval checks before re-entry.",
      "rationale": "Reduces rapid quarantine/re-enable flapping while preserving controlled recovery.",
      "alternatives_considered": [
        "Manual re-enable only",
        "Automatic re-enable after fixed time"
      ]
    },
    {
      "id": "dec_no_ingest_on_policy_check_failure",
      "type": "decision",
      "label": "Default to no-ingest when policy check fails",
      "description": "Treat policy-check unavailability or failure as a hard gate and skip source ingestion for that run.",
      "rationale": "Compliance-safe default avoids accidental collection under uncertain policy state.",
      "alternatives_considered": [
        "Proceed with last known policy state",
        "Partial ingest with warnings"
      ]
    },
    {
      "id": "asm_sources_allow_collection",
      "type": "assumption",
      "label": "Allowlisted sources remain compliant",
      "description": "Assumes selected source terms and robots policies remain stable between daily compliance checks.",
      "confidence": 0.83,
      "validated": false
    },
    {
      "id": "asm_profile_signal_quality",
      "type": "assumption",
      "label": "User profile provides enough relevance signal",
      "description": "Assumes topics, keywords, and source preferences are sufficient to rank content accurately.",
      "confidence": 0.68,
      "validated": false
    },
    {
      "id": "asm_llm_summary_budget",
      "type": "assumption",
      "label": "LLM summarization cost and latency are acceptable",
      "description": "Assumes nightly volume can be summarized within budget and overnight runtime constraints.",
      "confidence": 0.71,
      "validated": false
    },
    {
      "id": "asm_feedback_participation",
      "type": "assumption",
      "label": "User provides enough feedback signals",
      "description": "Assumes users will submit sufficient thumbs up/down signals to improve ranking quality.",
      "confidence": 0.63,
      "validated": false
    },
    {
      "id": "asm_threshold_setting_effective",
      "type": "assumption",
      "label": "Feedback threshold value is well calibrated",
      "description": "Assumes the chosen minimum feedback threshold avoids both noisy updates and over-delayed personalization.",
      "confidence": 0.66,
      "validated": false
    },
    {
      "id": "asm_approval_process_timely",
      "type": "assumption",
      "label": "Source approval process is timely",
      "description": "Assumes approvals for quarantined sources are reviewed quickly enough to avoid prolonged coverage loss.",
      "confidence": 0.64,
      "validated": false
    },
    {
      "id": "risk_source_layout_drift",
      "type": "risk",
      "label": "Source layout or markup drift",
      "description": "Site template changes can silently break extraction logic and reduce digest quality.",
      "severity": 0.78
    },
    {
      "id": "risk_bot_mitigation_failure",
      "type": "risk",
      "label": "Bot mitigation blocks collection",
      "description": "Anti-bot controls may block dynamic scraping paths and reduce source coverage.",
      "severity": 0.74
    },
    {
      "id": "risk_digest_quality_mismatch",
      "type": "risk",
      "label": "Digest quality misses user intent",
      "description": "Filtering and summarization may over-compress or miss relevant items, reducing trust.",
      "severity": 0.67
    },
    {
      "id": "risk_terms_change_breaks_compliance",
      "type": "risk",
      "label": "Terms changes break compliance",
      "description": "Source policy updates may invalidate prior allowlisting and force rapid source shutdowns.",
      "severity": 0.72
    }
  ],
  "edges": [
    {
      "type": "motivated_by",
      "source_id": "dec_python_orchestration",
      "target_id": "obj_unattended_overnight"
    },
    {
      "type": "motivated_by",
      "source_id": "dec_sqlite_storage",
      "target_id": "obj_unattended_overnight"
    },
    {
      "type": "motivated_by",
      "source_id": "dec_hybrid_collection",
      "target_id": "obj_personalized_digest"
    },
    {
      "type": "motivated_by",
      "source_id": "dec_two_stage_relevance",
      "target_id": "obj_personalized_digest"
    },
    {
      "type": "motivated_by",
      "source_id": "dec_feedback_loop_lightweight",
      "target_id": "obj_personalized_digest"
    },
    {
      "type": "motivated_by",
      "source_id": "dec_auto_source_quarantine",
      "target_id": "obj_unattended_overnight"
    },
    {
      "type": "motivated_by",
      "source_id": "dec_daily_policy_schedule",
      "target_id": "obj_unattended_overnight"
    },
    {
      "type": "motivated_by",
      "source_id": "dec_feedback_min_volume_fallback",
      "target_id": "obj_personalized_digest"
    },
    {
      "type": "motivated_by",
      "source_id": "dec_quarantine_reenable_after_n_approvals",
      "target_id": "obj_unattended_overnight"
    },
    {
      "type": "motivated_by",
      "source_id": "dec_no_ingest_on_policy_check_failure",
      "target_id": "obj_unattended_overnight"
    },
    {
      "type": "assumes",
      "source_id": "dec_hybrid_collection",
      "target_id": "asm_sources_allow_collection"
    },
    {
      "type": "assumes",
      "source_id": "dec_two_stage_relevance",
      "target_id": "asm_profile_signal_quality"
    },
    {
      "type": "assumes",
      "source_id": "dec_two_stage_relevance",
      "target_id": "asm_llm_summary_budget"
    },
    {
      "type": "assumes",
      "source_id": "dec_feedback_loop_lightweight",
      "target_id": "asm_feedback_participation"
    },
    {
      "type": "assumes",
      "source_id": "dec_daily_policy_schedule",
      "target_id": "asm_sources_allow_collection"
    },
    {
      "type": "assumes",
      "source_id": "dec_feedback_min_volume_fallback",
      "target_id": "asm_threshold_setting_effective"
    },
    {
      "type": "assumes",
      "source_id": "dec_quarantine_reenable_after_n_approvals",
      "target_id": "asm_approval_process_timely"
    },
    {
      "type": "conflicts_with",
      "source_id": "risk_source_layout_drift",
      "target_id": "req_multi_source_ingest"
    },
    {
      "type": "conflicts_with",
      "source_id": "risk_bot_mitigation_failure",
      "target_id": "req_multi_source_ingest"
    },
    {
      "type": "conflicts_with",
      "source_id": "risk_digest_quality_mismatch",
      "target_id": "req_relevance_filtering"
    },
    {
      "type": "invalidates",
      "source_id": "risk_bot_mitigation_failure",
      "target_id": "asm_sources_allow_collection"
    },
    {
      "type": "conflicts_with",
      "source_id": "risk_source_layout_drift",
      "target_id": "req_snapshot_test_harness"
    },
    {
      "type": "conflicts_with",
      "source_id": "risk_terms_change_breaks_compliance",
      "target_id": "req_compliant_collection"
    },
    {
      "type": "invalidates",
      "source_id": "risk_terms_change_breaks_compliance",
      "target_id": "asm_sources_allow_collection"
    },
    {
      "type": "conflicts_with",
      "source_id": "risk_source_layout_drift",
      "target_id": "dec_hybrid_collection"
    },
    {
      "type": "conflicts_with",
      "source_id": "risk_bot_mitigation_failure",
      "target_id": "dec_hybrid_collection"
    },
    {
      "type": "conflicts_with",
      "source_id": "risk_terms_change_breaks_compliance",
      "target_id": "dec_hybrid_collection"
    },
    {
      "type": "conflicts_with",
      "source_id": "risk_digest_quality_mismatch",
      "target_id": "dec_feedback_loop_lightweight"
    },
    {
      "type": "conflicts_with",
      "source_id": "risk_bot_mitigation_failure",
      "target_id": "dec_quarantine_reenable_after_n_approvals"
    },
    {
      "type": "implements",
      "source_id": "dec_feedback_loop_lightweight",
      "target_id": "req_feedback_capture"
    },
    {
      "type": "implements",
      "source_id": "dec_daily_policy_schedule",
      "target_id": "req_daily_policy_check"
    },
    {
      "type": "implements",
      "source_id": "dec_auto_source_quarantine",
      "target_id": "req_observability_recovery"
    },
    {
      "type": "implements",
      "source_id": "dec_feedback_min_volume_fallback",
      "target_id": "req_relevance_filtering"
    },
    {
      "type": "implements",
      "source_id": "dec_quarantine_reenable_after_n_approvals",
      "target_id": "req_multi_source_ingest"
    },
    {
      "type": "implements",
      "source_id": "dec_no_ingest_on_policy_check_failure",
      "target_id": "req_policy_failure_safe_mode"
    }
  ]
}
[/GRAPH UPDATE]

1. `asm_threshold_setting_effective` is still low-confidence (0.66): what should the initial minimum feedback threshold be (e.g., 20, 50, or 100 votes) before personalized reweighting activates?  
2. `asm_approval_process_timely` is low-confidence (0.64): what concrete SLA should we set for “N approvals” (e.g., N=2 within 48h) so quarantine does not reduce coverage too long?  
3. High-severity risks still lack explicit test mitigation edges (`risk_source_layout_drift`, `risk_terms_change_breaks_compliance`): should we add conformance tests that fail CI if parser snapshots drift or policy-check outputs become invalid?

---

**User**

Look at graph_v4.json and update the graph. 
Keep a 50 votes threshold, set any N for approvals, and choose what you want to do for test mitigation edges

---

**Cursor**

I’ll load `graph_v4.json`, apply those concrete values (50-vote threshold, chosen N approvals), and add explicit test-mitigation edges for the high risks.

I’m writing the concrete values now (`50` votes, `N=2` approvals) and adding test nodes plus `guards_against` edges to mitigate the high-severity risks.

Updated `condition_b/graph_v4.json` with your requested choices:
- fixed feedback threshold at **50 votes**
- set quarantine re-enable to **N = 2 approvals**
- added explicit **test mitigation nodes/edges** for high-severity risks

[GRAPH UPDATE]
{
  "nodes": [
    {
      "id": "obj_personalized_digest",
      "type": "objective",
      "label": "Personalized daily content digest",
      "description": "Deliver a concise daily digest of relevant content tailored to a user profile."
    },
    {
      "id": "obj_unattended_overnight",
      "type": "objective",
      "label": "Unattended overnight execution",
      "description": "Run the full pipeline on a schedule without manual intervention and recover from failures."
    },
    {
      "id": "req_multi_source_ingest",
      "type": "requirement",
      "label": "Multi-source public content ingestion",
      "description": "Collect content from blogs, news, RSS feeds, and forums, including pagination and basic dynamic loading.",
      "is_functional": true
    },
    {
      "id": "req_persistent_dedup",
      "type": "requirement",
      "label": "Persistent cross-run deduplication",
      "description": "Store content in a persistent database and prevent duplicate records across runs.",
      "is_functional": true
    },
    {
      "id": "req_relevance_filtering",
      "type": "requirement",
      "label": "Profile-based filtering and ranking",
      "description": "Score and rank items by topics, keywords, and preferred sources from a user profile.",
      "is_functional": true
    },
    {
      "id": "req_summary_and_digest",
      "type": "requirement",
      "label": "Summaries and formatted digest output",
      "description": "Generate concise summaries for relevant items and produce a clean daily digest in email or PDF form.",
      "is_functional": true
    },
    {
      "id": "req_observability_recovery",
      "type": "requirement",
      "label": "Robust logging and error recovery",
      "description": "Provide structured logging, fault handling, and retry/recovery behavior for unattended runs.",
      "is_functional": true
    },
    {
      "id": "req_snapshot_test_harness",
      "type": "requirement",
      "label": "Snapshot-based parser validation",
      "description": "Validate parsing and extraction logic using saved snapshots instead of live source calls.",
      "is_functional": true
    },
    {
      "id": "req_compliant_collection",
      "type": "requirement",
      "label": "Legally compliant source collection",
      "description": "Only ingest from sources permitted by robots policies and terms, with an explicit allowlist gate.",
      "is_functional": true
    },
    {
      "id": "req_feedback_capture",
      "type": "requirement",
      "label": "Lightweight relevance feedback capture",
      "description": "Collect simple per-item user feedback to improve ranking quality over time.",
      "is_functional": true
    },
    {
      "id": "req_daily_policy_check",
      "type": "requirement",
      "label": "Daily source policy verification",
      "description": "Verify robots and terms constraints daily before collection starts.",
      "is_functional": true
    },
    {
      "id": "req_policy_failure_safe_mode",
      "type": "requirement",
      "label": "No-ingest safe mode on policy-check failure",
      "description": "If policy verification fails, skip ingestion for that run and emit operational alerts.",
      "is_functional": true
    },
    {
      "id": "dec_python_orchestration",
      "type": "decision",
      "label": "Use Python as orchestration runtime",
      "description": "Implement ingestion, ranking, summarization orchestration, and scheduling in Python.",
      "rationale": "Strong ecosystem for scraping, NLP, data processing, and testing with low operational overhead for a single-project pipeline.",
      "alternatives_considered": [
        "Node.js/TypeScript",
        "Go"
      ]
    },
    {
      "id": "dec_sqlite_storage",
      "type": "decision",
      "label": "Use SQLite for persistent content store",
      "description": "Store normalized content, fingerprints, user profiles, runs, and digest artifacts in SQLite.",
      "rationale": "Single-machine unattended pipeline favors minimal operations and simple deployment over multi-writer scalability.",
      "alternatives_considered": [
        "PostgreSQL",
        "DuckDB"
      ]
    },
    {
      "id": "dec_hybrid_collection",
      "type": "decision",
      "label": "Hybrid feed-first collection strategy",
      "description": "Use RSS/API ingestion first and only use headless browser scraping for sources that require dynamic rendering.",
      "rationale": "Reduces fragility, runtime, and bot-detection risk compared with full browser scraping everywhere.",
      "alternatives_considered": [
        "Browser-only scraping",
        "RSS/API-only ingestion"
      ]
    },
    {
      "id": "dec_two_stage_relevance",
      "type": "decision",
      "label": "Two-stage relevance and summarization",
      "description": "Apply cheap keyword/BM25 prefiltering before LLM reranking and summarization on a reduced candidate set.",
      "rationale": "Balances quality, cost, and latency when there is no strict preference for LLM-heavy or heuristic-only ranking.",
      "alternatives_considered": [
        "LLM-only ranking and summarization",
        "Heuristic-only ranking"
      ]
    },
    {
      "id": "dec_feedback_loop_lightweight",
      "type": "decision",
      "label": "Add lightweight explicit feedback loop",
      "description": "Capture simple positive/negative feedback on digest items and feed it into ranking weight updates.",
      "rationale": "Low-friction feedback improves personalization while avoiding heavy UX and labeling overhead.",
      "alternatives_considered": [
        "No feedback loop",
        "Implicit behavior-only feedback",
        "Detailed multi-label annotation"
      ]
    },
    {
      "id": "dec_auto_source_quarantine",
      "type": "decision",
      "label": "Enable automatic source quarantine",
      "description": "Automatically disable sources that fail extraction, trigger anti-bot blocks, or fail compliance checks until reviewed.",
      "rationale": "Protects pipeline reliability and compliance by failing safely at source level instead of degrading entire runs.",
      "alternatives_considered": [
        "Best-effort continue with warnings",
        "Abort entire run on source failure"
      ]
    },
    {
      "id": "dec_daily_policy_schedule",
      "type": "decision",
      "label": "Run policy checks daily pre-collection",
      "description": "Execute source robots/terms verification as a daily gate before ingestion begins.",
      "rationale": "Daily cadence catches policy drift early while remaining operationally simple.",
      "alternatives_considered": [
        "Weekly checks",
        "Manual checks only",
        "Per-request checks during scraping"
      ]
    },
    {
      "id": "dec_feedback_min_volume_fallback",
      "type": "decision",
      "label": "Fallback to baseline ranking on low feedback volume",
      "description": "Keep baseline BM25/keyword weights until at least 50 explicit feedback votes are collected, then apply feedback-driven tuning.",
      "rationale": "Prevents unstable personalization when explicit feedback volume is sparse.",
      "alternatives_considered": [
        "Always apply feedback updates",
        "Disable feedback-driven tuning entirely"
      ]
    },
    {
      "id": "dec_quarantine_reenable_after_n_approvals",
      "type": "decision",
      "label": "Re-enable quarantined sources after N approvals",
      "description": "Keep sources quarantined until they receive 2 explicit approval checks before re-entry.",
      "rationale": "Reduces rapid quarantine/re-enable flapping while preserving controlled recovery.",
      "alternatives_considered": [
        "Manual re-enable only",
        "Automatic re-enable after fixed time"
      ]
    },
    {
      "id": "dec_no_ingest_on_policy_check_failure",
      "type": "decision",
      "label": "Default to no-ingest when policy check fails",
      "description": "Treat policy-check unavailability or failure as a hard gate and skip source ingestion for that run.",
      "rationale": "Compliance-safe default avoids accidental collection under uncertain policy state.",
      "alternatives_considered": [
        "Proceed with last known policy state",
        "Partial ingest with warnings"
      ]
    },
    {
      "id": "asm_sources_allow_collection",
      "type": "assumption",
      "label": "Allowlisted sources remain compliant",
      "description": "Assumes selected source terms and robots policies remain stable between daily compliance checks.",
      "confidence": 0.83,
      "validated": false
    },
    {
      "id": "asm_profile_signal_quality",
      "type": "assumption",
      "label": "User profile provides enough relevance signal",
      "description": "Assumes topics, keywords, and source preferences are sufficient to rank content accurately.",
      "confidence": 0.68,
      "validated": false
    },
    {
      "id": "asm_llm_summary_budget",
      "type": "assumption",
      "label": "LLM summarization cost and latency are acceptable",
      "description": "Assumes nightly volume can be summarized within budget and overnight runtime constraints.",
      "confidence": 0.71,
      "validated": false
    },
    {
      "id": "asm_feedback_participation",
      "type": "assumption",
      "label": "User provides enough feedback signals",
      "description": "Assumes users will submit sufficient thumbs up/down signals to improve ranking quality.",
      "confidence": 0.63,
      "validated": false
    },
    {
      "id": "asm_threshold_setting_effective",
      "type": "assumption",
      "label": "Feedback threshold value is well calibrated",
      "description": "Assumes a 50-vote minimum threshold avoids both noisy updates and over-delayed personalization.",
      "confidence": 0.75,
      "validated": false
    },
    {
      "id": "asm_approval_process_timely",
      "type": "assumption",
      "label": "Source approval process is timely",
      "description": "Assumes two approval checks for quarantined sources can be completed quickly enough to avoid prolonged coverage loss.",
      "confidence": 0.72,
      "validated": false
    },
    {
      "id": "comp_parser_adapters",
      "type": "component",
      "label": "Source parser adapters",
      "description": "Per-source extraction adapters that normalize fetched content into the common internal schema.",
      "has_tests": false
    },
    {
      "id": "comp_policy_checker",
      "type": "component",
      "label": "Policy compliance checker",
      "description": "Daily checker that validates robots and terms constraints before ingestion is allowed.",
      "has_tests": false
    },
    {
      "id": "comp_quarantine_manager",
      "type": "component",
      "label": "Source quarantine manager",
      "description": "Tracks source health/compliance state, quarantines failing sources, and re-enables after approvals.",
      "has_tests": false
    },
    {
      "id": "iface_policy_check_result",
      "type": "interface",
      "label": "Policy check result contract",
      "description": "Structured pass/fail contract output by the daily policy checker.",
      "contract": "{ source_id, check_time, robots_allowed, terms_allowed, status, reason }"
    },
    {
      "id": "tst_parser_snapshot_conformance",
      "type": "test",
      "label": "Parser snapshot conformance tests",
      "description": "Conformance tests that run saved source snapshots through adapters and fail on extraction drift.",
      "test_type": "conformance",
      "status": "planned"
    },
    {
      "id": "tst_policy_contract_conformance",
      "type": "test",
      "label": "Policy checker contract tests",
      "description": "Conformance tests that validate policy-check outputs and no-ingest gate behavior on invalid results.",
      "test_type": "conformance",
      "status": "planned"
    },
    {
      "id": "tst_quarantine_workflow_integration",
      "type": "test",
      "label": "Quarantine workflow integration tests",
      "description": "Integration tests that validate quarantine transitions and re-enable only after two approvals.",
      "test_type": "integration",
      "status": "planned"
    },
    {
      "id": "risk_source_layout_drift",
      "type": "risk",
      "label": "Source layout or markup drift",
      "description": "Site template changes can silently break extraction logic and reduce digest quality.",
      "severity": 0.78
    },
    {
      "id": "risk_bot_mitigation_failure",
      "type": "risk",
      "label": "Bot mitigation blocks collection",
      "description": "Anti-bot controls may block dynamic scraping paths and reduce source coverage.",
      "severity": 0.74
    },
    {
      "id": "risk_digest_quality_mismatch",
      "type": "risk",
      "label": "Digest quality misses user intent",
      "description": "Filtering and summarization may over-compress or miss relevant items, reducing trust.",
      "severity": 0.67
    },
    {
      "id": "risk_terms_change_breaks_compliance",
      "type": "risk",
      "label": "Terms changes break compliance",
      "description": "Source policy updates may invalidate prior allowlisting and force rapid source shutdowns.",
      "severity": 0.72
    }
  ],
  "edges": [
    { "type": "motivated_by", "source_id": "dec_python_orchestration", "target_id": "obj_unattended_overnight" },
    { "type": "motivated_by", "source_id": "dec_sqlite_storage", "target_id": "obj_unattended_overnight" },
    { "type": "motivated_by", "source_id": "dec_hybrid_collection", "target_id": "obj_personalized_digest" },
    { "type": "motivated_by", "source_id": "dec_two_stage_relevance", "target_id": "obj_personalized_digest" },
    { "type": "motivated_by", "source_id": "dec_feedback_loop_lightweight", "target_id": "obj_personalized_digest" },
    { "type": "motivated_by", "source_id": "dec_auto_source_quarantine", "target_id": "obj_unattended_overnight" },
    { "type": "motivated_by", "source_id": "dec_daily_policy_schedule", "target_id": "obj_unattended_overnight" },
    { "type": "motivated_by", "source_id": "dec_feedback_min_volume_fallback", "target_id": "obj_personalized_digest" },
    { "type": "motivated_by", "source_id": "dec_quarantine_reenable_after_n_approvals", "target_id": "obj_unattended_overnight" },
    { "type": "motivated_by", "source_id": "dec_no_ingest_on_policy_check_failure", "target_id": "obj_unattended_overnight" },

    { "type": "assumes", "source_id": "dec_hybrid_collection", "target_id": "asm_sources_allow_collection" },
    { "type": "assumes", "source_id": "dec_two_stage_relevance", "target_id": "asm_profile_signal_quality" },
    { "type": "assumes", "source_id": "dec_two_stage_relevance", "target_id": "asm_llm_summary_budget" },
    { "type": "assumes", "source_id": "dec_feedback_loop_lightweight", "target_id": "asm_feedback_participation" },
    { "type": "assumes", "source_id": "dec_daily_policy_schedule", "target_id": "asm_sources_allow_collection" },
    { "type": "assumes", "source_id": "dec_feedback_min_volume_fallback", "target_id": "asm_threshold_setting_effective" },
    { "type": "assumes", "source_id": "dec_quarantine_reenable_after_n_approvals", "target_id": "asm_approval_process_timely" },

    { "type": "conflicts_with", "source_id": "risk_source_layout_drift", "target_id": "req_multi_source_ingest" },
    { "type": "conflicts_with", "source_id": "risk_bot_mitigation_failure", "target_id": "req_multi_source_ingest" },
    { "type": "conflicts_with", "source_id": "risk_digest_quality_mismatch", "target_id": "req_relevance_filtering" },
    { "type": "invalidates", "source_id": "risk_bot_mitigation_failure", "target_id": "asm_sources_allow_collection" },
    { "type": "conflicts_with", "source_id": "risk_source_layout_drift", "target_id": "req_snapshot_test_harness" },
    { "type": "conflicts_with", "source_id": "risk_terms_change_breaks_compliance", "target_id": "req_compliant_collection" },
    { "type": "invalidates", "source_id": "risk_terms_change_breaks_compliance", "target_id": "asm_sources_allow_collection" },
    { "type": "conflicts_with", "source_id": "risk_source_layout_drift", "target_id": "dec_hybrid_collection" },
    { "type": "conflicts_with", "source_id": "risk_bot_mitigation_failure", "target_id": "dec_hybrid_collection" },
    { "type": "conflicts_with", "source_id": "risk_terms_change_breaks_compliance", "target_id": "dec_hybrid_collection" },
    { "type": "conflicts_with", "source_id": "risk_digest_quality_mismatch", "target_id": "dec_feedback_loop_lightweight" },
    { "type": "conflicts_with", "source_id": "risk_bot_mitigation_failure", "target_id": "dec_quarantine_reenable_after_n_approvals" },

    { "type": "implements", "source_id": "dec_feedback_loop_lightweight", "target_id": "req_feedback_capture" },
    { "type": "implements", "source_id": "dec_daily_policy_schedule", "target_id": "req_daily_policy_check" },
    { "type": "implements", "source_id": "dec_auto_source_quarantine", "target_id": "req_observability_recovery" },
    { "type": "implements", "source_id": "dec_feedback_min_volume_fallback", "target_id": "req_relevance_filtering" },
    { "type": "implements", "source_id": "dec_quarantine_reenable_after_n_approvals", "target_id": "req_multi_source_ingest" },
    { "type": "implements", "source_id": "dec_no_ingest_on_policy_check_failure", "target_id": "req_policy_failure_safe_mode" },

    { "type": "implements", "source_id": "comp_parser_adapters", "target_id": "req_multi_source_ingest" },
    { "type": "implements", "source_id": "comp_parser_adapters", "target_id": "req_snapshot_test_harness" },
    { "type": "implements", "source_id": "comp_policy_checker", "target_id": "req_daily_policy_check" },
    { "type": "implements", "source_id": "comp_policy_checker", "target_id": "req_compliant_collection" },
    { "type": "implements", "source_id": "comp_quarantine_manager", "target_id": "req_observability_recovery" },
    { "type": "implements", "source_id": "comp_quarantine_manager", "target_id": "req_multi_source_ingest" },
    { "type": "depends_on", "source_id": "comp_quarantine_manager", "target_id": "comp_policy_checker" },
    { "type": "exposes", "source_id": "comp_policy_checker", "target_id": "iface_policy_check_result" },
    { "type": "consumes", "source_id": "comp_quarantine_manager", "target_id": "iface_policy_check_result" },

    { "type": "verifies", "source_id": "tst_parser_snapshot_conformance", "target_id": "comp_parser_adapters" },
    { "type": "verifies", "source_id": "tst_policy_contract_conformance", "target_id": "comp_policy_checker" },
    { "type": "verifies", "source_id": "tst_policy_contract_conformance", "target_id": "iface_policy_check_result" },
    { "type": "verifies", "source_id": "tst_quarantine_workflow_integration", "target_id": "comp_quarantine_manager" },

    { "type": "guards_against", "source_id": "tst_parser_snapshot_conformance", "target_id": "risk_source_layout_drift" },
    { "type": "guards_against", "source_id": "tst_policy_contract_conformance", "target_id": "risk_terms_change_breaks_compliance" },
    { "type": "guards_against", "source_id": "tst_quarantine_workflow_integration", "target_id": "risk_bot_mitigation_failure" },

    { "type": "validates", "source_id": "tst_parser_snapshot_conformance", "target_id": "dec_hybrid_collection" },
    { "type": "validates", "source_id": "tst_policy_contract_conformance", "target_id": "dec_no_ingest_on_policy_check_failure" },
    { "type": "validates", "source_id": "tst_quarantine_workflow_integration", "target_id": "dec_quarantine_reenable_after_n_approvals" }
  ]
}
[/GRAPH UPDATE]

1. `asm_profile_signal_quality` (0.68) and `asm_feedback_participation` (0.63) are still low-confidence: should we mark a success criterion like “top-10 precision >= 0.7 after 2 weeks” to validate/adjust the ranking approach?  
2. I chose `N = 2` approvals for re-enable. Do you want those approvals to require **different days/check runs** (stronger safety) or can both happen in the same day?  
3. All high-severity risks now have mitigation tests; next step can be final implementation plan generation from this graph. Should I proceed to the final plan now?

---

**User**

Proceed to the final plan

---

**Cursor**

Great — I’ll use `graph_v5.json` as the source of truth and produce the final implementation plan in phased, build-ready detail.

## Final Implementation Plan

Build a Python-based, unattended nightly pipeline that ingests compliant public content, deduplicates in SQLite, ranks against a user profile, summarizes relevant items, and delivers a daily digest. The plan below is grounded in your finalized graph decisions (SQLite, daily policy gate, no-ingest safe mode, quarantine with 2 approvals, feedback threshold at 50 votes).

### 1) System Architecture

- **Runtime**: Python CLI app with modular pipeline stages.
- **Storage**: SQLite (single-machine, low-ops), with WAL mode and indexes for dedup + ranking reads.
- **Collection strategy**: Feed/API first, browser scraping only where needed.
- **Safety gates**:
  - Daily policy check before ingestion.
  - If policy check fails/unavailable => **no ingest** for that run + alert.
  - Automatic source quarantine on repeated extraction/compliance/bot failures.
  - Re-enable quarantined source only after **2 explicit approvals**.
- **Relevance strategy**:
  - Stage 1: heuristic prefilter (keywords + BM25).
  - Stage 2: LLM rerank + summary on reduced candidate set.
  - Feedback-aware tuning only after **>=50 explicit votes**.

### 2) Repository/Module Layout

- `src/orchestrator/`: run coordination, stage transitions, run state machine.
- `src/ingest/`
  - `source_registry.py` (allowlisted source config + capabilities)
  - `fetch_rss.py`, `fetch_http.py`, `fetch_browser.py`
  - `parsers/` per-source adapters (normalized output)
- `src/policy/`
  - `checker.py` (robots/terms checks)
  - `contracts.py` (`iface_policy_check_result`)
- `src/quarantine/`
  - `manager.py` (state transitions + approval flow)
- `src/relevance/`
  - `prefilter.py` (keywords/BM25)
  - `rerank_llm.py`
  - `feedback_model.py` (enabled only after threshold)
- `src/summarize/` LLM summarization + guardrails (length/style constraints)
- `src/digest/` email/PDF rendering and dispatch
- `src/storage/`
  - schema migrations
  - DAO/repositories
- `src/observability/` structured logs, metrics emitters, alerts
- `tests/`
  - `fixtures/snapshots/` saved HTML/feed payloads
  - conformance/integration suites matching graph tests

### 3) Data Model (SQLite)

Core tables:

- `sources` (`source_id`, type, base_url, allowlisted, quarantine_state, last_policy_status, last_approved_at, approval_count)
- `policy_checks` (`id`, `source_id`, `check_time`, `robots_allowed`, `terms_allowed`, `status`, `reason`)
- `content_items` (`item_id`, canonical_url, source_id, title, body, published_at, fetched_at, raw_hash, canonical_hash, metadata_json)
- `ingestion_runs` (`run_id`, start_ts, end_ts, status, policy_gate_status, error_summary)
- `relevance_scores` (`run_id`, `item_id`, prefilter_score, llm_score, final_score, rank_reason_json)
- `summaries` (`item_id`, model, summary_text, token_count, cost_estimate, created_at)
- `digests` (`digest_id`, date, format, recipient, artifact_path, status)
- `feedback_votes` (`vote_id`, `item_id`, vote(+/-), user_id(optional), voted_at)

Indexes/constraints:

- Unique on `canonical_hash` and/or canonical URL normalization for cross-run dedup.
- Composite indexes on (`source_id`, `published_at`), (`run_id`, `final_score`), (`check_time`, `status`).
- Foreign keys on all run/source/item relationships.

### 4) End-to-End Nightly Workflow

1. **Start run**; create `ingestion_runs` record.
2. **Policy gate** (daily):
   - Run checker for each allowlisted source.
   - Persist `policy_checks`.
   - If checker unavailable/invalid => mark run safe mode, **skip ingest**, send ops alert digest, end run gracefully.
3. **Source selection**:
   - Exclude quarantined sources.
   - For each source: use RSS/API first, browser fallback if required.
4. **Parse + normalize** with source adapters.
5. **Dedup** by canonical URL/hash and content fingerprint.
6. **Relevance stage 1** (keywords + BM25).
7. **Relevance stage 2** (LLM rerank on top candidates).
8. **Feedback tuning**:
   - If total votes < 50: keep baseline weights.
   - If >= 50: apply feedback-adjusted weighting in final score composition.
9. **Summarization** for selected items.
10. **Digest generation** (email/PDF), persist artifact + status.
11. **Quarantine management**:
    - Update failure counters.
    - Auto-quarantine failing sources.
    - Re-enable only after 2 explicit approvals.
12. **Finalize run** and emit metrics/log summary.

### 5) Error Handling & Recovery

- Per-source isolation: one source failure does not fail entire run.
- Retry policy:
  - network/transient errors: exponential backoff with capped retries.
  - parsing failures: no blind retry; snapshot capture + quarantine scoring.
- Idempotency:
  - dedup constraints prevent duplicate writes on reruns.
  - run stage checkpoints allow safe rerun from failed stage.
- Safe defaults:
  - compliance uncertainty => no ingest.
  - LLM outage => still ship reduced digest (prefiltered + extractive fallback summary) with degraded-mode flag.

### 6) Testing Plan (directly mapped to graph)

- **Conformance**: `tst_parser_snapshot_conformance`
  - Saved fixture snapshots for each parser adapter.
  - Fail on schema drift or missing required fields.
  - Guards against source layout drift.
- **Conformance**: `tst_policy_contract_conformance`
  - Validate policy check result contract and gate behavior.
  - Explicitly assert no-ingest on invalid/unavailable policy checks.
  - Guards against terms/compliance breakage.
- **Integration**: `tst_quarantine_workflow_integration`
  - Quarantine transitions, approval count tracking, re-enable only at 2 approvals.
  - Guards against bot-block operational regressions.
- Additional recommended:
  - dedup correctness tests (cross-run repeats)
  - ranking pipeline determinism tests (seeded fixtures)
  - digest rendering snapshot tests (email + PDF)

### 7) Observability & Ops

- Structured logs with `run_id`, `source_id`, stage, severity, decision path.
- Metrics:
  - items fetched/parsed/deduped
  - policy pass/fail counts
  - quarantine count + re-enable latency
  - LLM token/cost/latency
  - digest send success rate
- Alerts:
  - policy gate failure (safe mode run)
  - sharp drop in parsed items for a source
  - repeated quarantine flapping
  - digest delivery failure

### 8) Delivery Phases

- **Phase A (foundation)**: schema, run orchestrator, policy gate, source registry.
- **Phase B (ingestion core)**: hybrid collectors + parser adapters + dedup.
- **Phase C (relevance/summarization)**: two-stage ranking, summaries, digest rendering.
- **Phase D (reliability controls)**: quarantine manager, approvals workflow, alerts.
- **Phase E (feedback loop)**: vote capture, 50-threshold fallback, adaptive weighting.
- **Phase F (hardening)**: full conformance/integration suite, runbooks, retry tuning.

### 9) Acceptance Criteria

- Nightly run completes unattended for 7 consecutive days.
- Policy gate executes daily; policy-check failure triggers no-ingest safe mode and alert.
- Duplicate insertion rate effectively zero under repeated reruns.
- Quarantined sources require 2 approvals before re-enable.
- Feedback weighting remains disabled until 50 votes; activates thereafter.
- High-severity risks covered by automated conformance/integration tests in CI.

If you want, I can turn this into a concrete task breakdown (`tickets.md`) with estimated effort and dependency order next.

