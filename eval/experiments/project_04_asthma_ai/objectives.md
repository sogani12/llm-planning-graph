# Evaluation Rubric — Asthma Advisor Planning

Each objective is scored independently for Condition A and Condition B.
Score: 0 = not addressed | 0.5 = partially addressed | 1 = fully addressed

These scores are based on the planning conversations, with source code only used as supporting evidence where the discussion was ambiguous. For both conditions Gemini 2.5 Pro was used.

---

## Functional Objectives (expected from both conditions)

| # | Objective | A score | B score | Notes |
|---|-----------|---------|---------|-------|
| 1 | Stack matches the user's explicit preference and objective constraints | 1 | 1 | A followed the requested React + Flask + Postgres stack exactly. B proposed Next.js + FastAPI initially, then corrected to React (as requested). |
| 2 | Calendar sync scope is explicit and privacy-aware | 0.5 | 1 | A mentions Apple Calendar and exports events, but the sync model stays vague. B explicitly challenged two-way sync, explained the privacy tradeoff, and got confirmation for a narrower first version. |
| 3 | Medical safety framing is built into the advisor behavior | 0 | 1 | A never clearly surfaced a concise medical disclaimer or escalation guidance. B explicitly required language like “not formal medical advice” and “see a doctor if needed,” which directly addresses liability and user safety. |
| 4 | Prediction model uses the right inputs and training data | 1 | 1 | Both conversations tied risk prediction to symptom history, weather, air quality, and mock training data rather than using an unrelated generic model. |
| 5 | Persistent storage and seeded test data are planned concretely | 1 | 1 | Both planned a persistent database plus mock/test users and historical symptom data. A stayed closer to the user’s Flask/Postgres request; B also planned database schema and seeded data. |
| 6 | Unattended operation has a concrete recovery strategy | 0.5 | 1 | A mentions error recovery and background work but does not clearly commit to a resilient unattended execution design. B explicitly chose Celery + Redis, plus circuit-breaker behavior and monitoring, which is much more operationally grounded. |
| 7 | Objective-specific tradeoffs are surfaced instead of hidden | 0 | 1 | A mostly implements the requested features without surfacing many tradeoffs. B repeatedly framed choices as tradeoffs, especially around privacy, sync scope, and commercial deployment. |
| 8 | Clarifying questions target ambiguous objectives before implementation | 0.5 | 1 | A asked basic stack/API/UI questions. B asked sharper questions about liability, privacy/commercial use, sync direction, and API preferences, which better reflects objective awareness. |

## Structural Objectives (graph-specific — condition B only)

| # | Objective | A score | B score | Notes |
|---|-----------|---------|---------|-------|
| 9 | Key architectural decisions recorded with explicit rationale and alternatives | 0.5 | 1 | A has prose summaries, but decisions are mostly implicit. B records the major choices as explicit graph decisions with rationale and alternatives considered. |
| 10 | Implicit assumptions surfaced with confidence levels | 0 | 1 | A does not surface assumptions as first-class items. B adds assumptions such as external API reliability, cookie longevity, and deployment stability with confidence scores. |
| 11 | Risks identified beyond code failures, including domain and compliance risks | 0.5 | 1 | A mentions some technical risks, but not much around medical or privacy implications. B explicitly captures risks around medical advice, PHI/commercial deployment, and calendar data exposure. |

---

## Summary Counts (based on the scores above)

| Metric | Condition A | Condition B |
|--------|-------------|-------------|
| Functional objectives hit (out of 8) | 4.5 / 8 | 8 / 8 |
| Structural objectives hit (out of 3) | 1 / 3 | 3 / 3 |
| Total decision nodes in plan | 0 (no graph) | 10 |
| Total assumption nodes surfaced | 0 (no graph) | 1 |
| Total risk nodes surfaced | 0 (no graph) | 3 |
| Graph nodes total | — | 35 |
| Graph edges total | — | 38 |

---

## Key Qualitative Catches

Specific things condition B surfaced that condition A missed or glossed over:

1. **Graph-based decision capture**: B made architectural choices explicit with rationale and alternatives. The graph contains 10 decision nodes (React, FastAPI, PostgreSQL, free-tier APIs, OAuth 2.0/JWT, Celery+Redis, OpenAI, Docker, Sentry, external API selection) — each with documented rationale and alternatives considered. A's choices were implicit in prose.

2. **Risk and assumption identification**: B surfaced domain-specific risks (medical liability severity 1.0, PHI/privacy compliance 0.9, free API rate limits 0.6) and made assumptions explicit (external API availability, confidence 0.7). A mentioned HIPAA-like obligations but didn't enumerate risks or confidence levels.

3. **Requirement clarity from graph structure**: B's graph captured 6 concrete requirements with explicit edges connecting them to objectives and mitigations (e.g., medical disclaimer "guards against" medical liability risk). This forced B to ask clarifying questions about liability framing, PHI scope, and sync direction *before* committing to implementation.

4. **Stack choice responsiveness**: B proposed alternatives (Next.js + FastAPI) upfront, then corrected to React when the user clarified. While FastAPI remained (not Flask), the decision was documented with rationale—making it visible and potentially revisable. A never questioned the Flask choice; it was simply implemented.
