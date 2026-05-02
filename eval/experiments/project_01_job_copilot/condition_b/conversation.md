user: Build an automated overnight job application pipeline with the following capabilities:

- Scrape job listings from multiple job boards, including standard sites and
  auth-protected platforms (e.g. Wellfound, LinkedIn). Handle dynamic page
  loading and bot detection.
- Ingest scraped listings into a persistent database, deduplicating across runs.
- Filter listings for relevance against a user profile (skills, seniority, role
  preferences).
- For each relevant job, generate a tailored, formatted resume PDF.
- Run unattended as an overnight pipeline with full error recovery — no human
  intervention once started.
- Include a testing harness that validates scraping logic without live site calls.

As we plan, maintain a running decision graph in JSON format. After each major decision cluster, output the updated graph. Before making each new architectural decision, reference the current graph to stay consistent with prior choices. More details below:

You are an expert software architecture analyst. Your job is to read a developer–AI planning conversation or design document and extract a structured decision graph from it.

The graph captures the planning intent behind a software project: what it aims to achieve, what constraints apply, what was decided and why, what components exist, what interfaces they expose, what is being assumed, and what could go wrong.

---

## NODE TYPES

Extract nodes of the following 7 types. For each node provide: id (short snake_case string, unique), type, label (concise noun phrase), description (1–2 sentences).

### 1. objective
What the system is trying to achieve. The "why" behind the project.
Signal phrases: "the goal is", "we want to", "the system should", "this enables", "the purpose is"
Extra field: none
Example: { "id": "obj_overnight_run", "type": "objective", "label": "Unattended overnight execution", "description": "The pipeline must run from start to finish without human intervention, completing before the user wakes up." }

### 2. requirement
A hard constraint or must-have property. Non-negotiable functional or non-functional.
Signal phrases: "must", "shall", "required", "needs to", "has to", "cannot", "mandatory"
Extra fields: is_functional (bool, default true)
Example: { "id": "req_dedup", "type": "requirement", "label": "Cross-run deduplication", "description": "The database must not store duplicate job listings across pipeline runs.", "is_functional": true }

### 3. assumption
CRITICAL — these are the most commonly missed. An assumption is something the plan treats as true without explicit verification. Look for: things that "should work", unstated dependencies on external behaviour, implicit beliefs about the environment, technology choices that have hidden prerequisites.
Signal phrases: "assuming", "we expect", "should be fine", "probably", "I think", "as long as", "in most cases", implicit runtime/platform choices
Extra fields: confidence (0.0–1.0, lower = more uncertain), validated (bool, default false)
Example: { "id": "asm_playwright_nodejs", "type": "assumption", "label": "Playwright reliability on Node.js", "description": "Assumes that Playwright's Node.js bindings are more stable than Python bindings for dynamic site scraping. Not yet benchmarked.", "confidence": 0.7, "validated": false }

### 4. decision
An explicit architectural or design choice made during planning. Must include what was chosen AND (ideally) what was rejected.
Signal phrases: "we decided", "we went with", "we chose", "instead of", "rather than", "we'll use X not Y", "we switched to"
Extra fields: rationale (string), alternatives_considered (list of strings)
Example: { "id": "dec_nodejs_runtime", "type": "decision", "label": "Use Node.js over Python", "description": "Switched runtime from Python to Node.js for all browser automation.", "rationale": "Playwright's Node.js API is better maintained and more reliable for dynamic sites with heavy JS rendering.", "alternatives_considered": ["Python + Playwright", "Python + Selenium"] }

### 5. component
A concrete module, service, library, worker, or subsystem being built or used.
Signal phrases: "module", "service", "worker", "handler", "library", "package", "database", "queue", "the X does"
Extra fields: file_refs (list of strings, optional file paths)
Example: { "id": "comp_scraper", "type": "component", "label": "Job board scraper", "description": "Playwright-based scraper that handles both standard and auth-protected job boards." }

### 6. interface
An API, protocol, schema, data contract, or formal boundary between components.
Signal phrases: "API", "endpoint", "schema", "format", "contract", "payload", "the X accepts/returns"
Extra fields: contract (string describing the shape, optional)
Example: { "id": "iface_job_schema", "type": "interface", "label": "Normalised job listing schema", "description": "Common JSON schema all scrapers must output regardless of source site.", "contract": "{ title, company, url, source, scraped_at, description, tags }" }

### 7. risk
CRITICAL — also commonly missed. A risk is a concern, tradeoff, potential failure mode, or known limitation. Look for: things that might break, scaling concerns, external dependencies that could change, security issues, reliability gaps.
Signal phrases: "risk", "concern", "might fail", "could break", "tradeoff", "limitation", "caveat", "downside", "edge case", "we're not sure", "this is fragile"
Extra fields: severity (0.0–1.0, higher = more severe)
Example: { "id": "risk_bot_detection", "type": "risk", "label": "Bot detection countermeasures", "description": "Job boards may update bot detection at any time, breaking scraping logic silently.", "severity": 0.8 }

---

## EDGE TYPES

After extracting nodes, define edges between them. Each edge: id, type, source_id, target_id, rationale (optional).

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

---

## OUTPUT FORMAT

Return ONLY valid JSON. No markdown fences, no explanation, no preamble.

{
  "nodes": [ ...node objects... ],
  "edges": [ ...edge objects... ]
}

Rules:
- Every edge source_id and target_id must match an id in the nodes array.
- Use consistent, readable ids (e.g. "dec_use_nodejs", "asm_rate_limits_stable").
- Include AT LEAST: all major decisions with rationale, all non-obvious assumptions, all significant risks. Do not omit these even if the text only implies them.
- If something is implicit but clearly present (e.g. the plan assumes a technology works a certain way), extract it as an assumption with validated: false.
- Aim for completeness over brevity. A graph with 15–25 nodes is better than one with 5.

cursor: The workspace is empty — this is a greenfield project. Before I architect the full plan, I need to nail down a few decisions that significantly change the shape of the system.
Which language/runtime do you prefer? This affects the browser automation library, PDF generation ecosystem, and testing framework choices.

user: No preference - choose what fits best

cursor: Should the pipeline actually submit job applications automatically, or only prepare materials (tailored resume PDFs) for human review the next morning?

user: Prepare only: generate tailored resumes + a shortlist for manual review

cursor: Where will this pipeline run overnight?

user: Start local, but containerize for portability 

cursor: For tailored resume PDF generation, which approach do you prefer?

user: LLM-driven: use an LLM to rewrite/tailor content, then render to PDF

cursor: Good. Based on your answers: prepare-only pipeline (tailored resumes + shortlist), LLM-driven resume rewriting, start local then containerize, and I'll pick the best-fit runtime. Let me now design the full architecture.
Here is the first decision graph after resolving the initial high-level choices:
Decision Graph — Cluster 1: Foundation
{decision graph v1 in json}

Now let me design the component architecture and the remaining decisions.
Decision Graph — Cluster 2: Components, Interfaces, Assumptions, and Risks
{decision graph v2 in json}

Now let me formalize this into the implementation plan.