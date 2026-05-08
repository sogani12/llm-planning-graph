# Evaluation Rubric — Asthma Advisor Planning (Revised)

Each objective is scored independently for Condition A and Condition B.
Score: 0 = not addressed | 0.5 = partially addressed | 1 = fully addressed

These scores are based on prompt fidelity and concrete planning, not documentation format. Source code used as supporting evidence where needed. For both conditions Gemini 2.5 Pro was used.

---

## Functional Objectives (expected from both conditions — all address the prompt requirements directly)

| # | Objective | Criterion | A score | B score | Notes |
|---|-----------|-----------|---------|---------|-------|
| 1 | **Prediction model inputs are concrete and sourced** | Plan specifies which features feed the model (symptom history ✓, weather data ✓, air quality ✓) and shows *how* each is obtained/processed. Generic "based on..." without data source or processing = 0.5. | 1 | 1 | Both tied prediction to symptom history, weather, air quality, and mock training data. Both showed how inputs would flow into the model. |
| 2 | **Calendar sync direction and scope are explicit** | Plan specifies: (a) read-only? bidirectional? (b) which calendar systems (Apple, Google, Outlook)? (c) what data is synced (events only, reminders, all-day blocks)? Vague "sync" without direction/scope = 0.5 or less. | 0.5 | 1 | A mentions Apple Calendar + exports but doesn't clarify read vs. write. B explicitly challenged two-way sync, chose narrower (read-only/forward) scope, and documented the privacy tradeoff. |
| 3 | **Proactive advisor trigger is defined operationally** | Plan shows *when* advisor notifies: e.g., "if (air_quality > 150 AND flare_risk > 0.6) then send alert." Thresholds, conditions, or logic shown. Vague "when risks are high" without specifics = 0.5. | 0.5 | 0.5 | Both mentioned triggering on high flare-up risk + environmental factors, but neither specified numeric thresholds or exact conditions. Both punted specifics to implementation. |
| 4 | **Error recovery and unattended operation are concrete** | Plan names specific tactics: retry logic (exponential backoff?), circuit breaker, timeout behavior, task queue persistence, rollback, alerts. Prose like "full error recovery" without mechanisms = 0.5 or less. | 0.5 | 1 | A mentions "error recovery and background work" but stays vague on mechanism. B explicitly chose Celery + Redis with circuit-breaker behavior, monitoring, and defined retry/fallback paths. |
| 5 | **Mock training and test data scope is specified** | How many test users? How much historical symptom data per user (e.g., 90 days, 1000 events)? What format? Enough to validate model predictions *and* UI flows? Vague "mock data included" = 0.5. | 1 | 1 | Both planned mock/test users with historical symptom data and structured records. Both tied data to model validation and UI testing. |
| 6 | **Medical liability and safety are explicitly framed** | Plan shows: (a) exact disclaimer language or placeholder, (b) when system escalates to "see a doctor," (c) what the system does *not* do (e.g., doesn't diagnose). Generic "medical advice" language = 0.5. | 0 | 1 | A never surfaced liability framing or escalation rules. B explicitly required language ("not formal medical advice," "consult physician"), defined escalation triggers, and scoped what advisor cannot claim. |
| 7 | **Unattended operation boundaries are clearly defined** | Specifies: (a) what runs without intervention (scheduled jobs, webhooks, background workers), (b) what requires human action if it fails (e.g., "API key rotation → manual restart"; "DB crash → alert + auto-recover"), (c) monitoring/alerting for critical paths. Fuzzy "runs unattended" = 0.5. | 0.5 | 1 | A says "unattended with error recovery" but doesn't separate automated vs. manual recovery paths. B defined Celery/Redis task persistence, circuit breakers, and explicit monitoring/alert hierarchy. |
| 8 | **Clarifying questions target actual ambiguities in the prompt** | Agent asks about: stack choices, sync direction/scope, liability/PHI scope, data volume, deployment constraints. Questions about UI color or naming = 0 or 0.5. | 0.5 | 1 | A asked about stack/API design—reasonable but generic. B asked specifically about liability framing, commercial use, sync direction, and API cost constraints—directly resolving prompt ambiguities. |
| 9 | **Testing strategy is concrete and covers key risks** | Plan specifies: (a) unit tests for prediction model (threshold logic, data pipeline), (b) integration tests for calendar sync, (c) UI/E2E tests for advisor flow, (d) failure scenarios (API downtime, bad data). Vague "we'll test" or no mention = 0 or 0.5. | 0 | 0 | A does not mention testing strategy. B does not mention testing strategy. This is a critical gap in both conversations. |

## Quality Objectives (expected from both conditions — show rigor beyond addressing requirements)

| # | Objective | Criterion | A score | B score | Notes |
|---|-----------|-----------|---------|---------|-------|
| 9 | **Alternatives are considered and trade-offs are named** | Plan shows ≥2 meaningful alternatives per major decision (e.g., "rule-based vs. ML model," "read-only vs. bidirectional sync") with stated consequences. Stating one approach without acknowledging tradeoffs = 0 or 0.5. | 0 | 1 | A mostly implements requested features without surfacing alternatives or tradeoffs. B repeatedly surfaced choices as tradeoffs: privacy cost of bidirectional sync, operational cost of Celery vs. simple cron, commercial deployment constraints. |
| 10 | **Risks and constraints are explicitly identified and scoped** | Plan surfaces ≥3 categories: (a) operational (API downtime, rate limits), (b) domain (medical liability, PHI compliance), (c) scope/phase (what's deferred?). Unscoped risks or vague "there may be risks" = 0.5. | 0.5 | 1 | A mentions HIPAA-like obligations but doesn't enumerate specific risks or mitigation. B identified medical liability risk, PHI/commercial scope risk, external API reliability risk—with severity/mitigation for each. |
| 11 | **Deferred work and assumptions are explicit, not buried** | If medical validation, precise calendar integration, or compliance audit are planned for phase 2, plan *names them* as deferred. Doesn't pretend full scope is covered. Hiding deferrals in implementation prose = 0 or 0.5. | 0.5 | 1 | A doesn't clearly separate MVP scope from future work (e.g., when does medical validation happen?). B explicitly defers commercial PHI compliance and two-way calendar sync to phase 2, with stated MVP scope. |

---

## Summary Counts

| Metric | Condition A | Condition B |
|--------|-------------|-------------|
| Functional objectives hit (out of 9) | 4.5 / 9 | 7.5 / 9 |
| Quality objectives hit (out of 3) | 1.0 / 3 | 3.0 / 3 |
| **Total score (out of 12)** | **5.0 / 12** | **10.0 / 12** |

---

## Key Qualitative Catches

1. **Both missed operational trigger specificity**: Objective #3 is the biggest gap — neither plan nailed "if X > threshold AND Y > threshold then notify." This should have been a hard clarifying question.

2. **Both completely omitted testing strategy**: Objective #9 reveals a critical shared gap. Neither A nor B discussed unit tests for the prediction model, integration tests for calendar sync, E2E tests for the advisor flow, or failure scenario testing. This is especially risky for a medical application.

3. **A conflates features with planning rigor**: A may have mentioned all 7 capabilities (logging, sync, model, advisor, unattended, mock data, test data) but didn't *plan* them with concrete tactics. B did (except for testing).

4. **B's liability framing is material, not just documentation**: B didn't just say "add a disclaimer." B specified language ("not formal medical advice"), escalation rules ("if risk > X, say 'see a doctor'"), and scope boundaries ("doesn't diagnose"). This is the difference between addressing a requirement and planning safely.

5. **A's error recovery prose hides vagueness**: Phrases like "full error recovery with no human intervention" actually obscure that A didn't specify *how*. The rubric now catches this by requiring mechanism names (Celery, circuit-breaker, etc.).

6. **Deferred work visibility**: B's graph structure forced it to be explicit about MVP vs. phase 2. A's prose doesn't clearly separate them, making it unclear what's actually scoped for the initial build.
