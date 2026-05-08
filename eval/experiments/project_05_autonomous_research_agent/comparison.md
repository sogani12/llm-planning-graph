# Comparison — Condition A vs Condition B

## Summary

Condition A (standard LLM planning) produced a highly detailed implementation with full-stack code (Python backend + React UI). However, it focused primarily on building the system rather than explicitly structuring the reasoning behind architectural decisions.

Condition B (graph-based planning) produced a more structured, modular, and well-reasoned system design. It explicitly captured assumptions, risks, decision rationale, and component relationships, leading to a more complete and evaluatable architecture.

Overall, Condition B demonstrates significantly better **planning clarity, reasoning transparency, and robustness** compared to Condition A.

---

## Objective Scores

| Objective | Condition A | Condition B |
|----------|-------------|-------------|
| 1. Clear pipeline stages defined | 1 | 1 |
| 2. Multi-source retrieval + deduplication | 1 | 1 |
| 3. Conflict resolution strategy | 0.5 | 1 |
| 4. Citation tracking | 1 | 1 |
| 5. Error handling & retries | 0.5 | 1 |
| 6. Autonomous execution | 1 | 1 |
| 7. Testing without live APIs | 1 | 1 |
| 8. Architectural decisions with rationale | 0 | 1 |
| 9. Assumptions explicitly stated | 0 | 1 |
| 10. Risks identified | 0 | 1 |

---

## Strengths of Condition A

- Generated a **complete working system** including:
  - React UI
  - Python backend
  - Pipeline implementation
- Included practical engineering features:
  - Parallel retrieval
  - Deduplication
  - Multi-format report generation
- Demonstrated strong **implementation capability**

---

## Weaknesses of Condition A

- Lacked explicit **architectural reasoning**
- Did not clearly separate:
  - assumptions
  - risks
  - design tradeoffs
- Error handling and retry strategies were **implicit**
- No structured explanation of:
  - why decisions were made
  - alternatives considered
- Difficult to evaluate systematically due to **code-first approach**

---

## Strengths of Condition B

- Clear **pipeline decomposition**:
  - retrieval → processing → synthesis → output
- Explicit **decision tracking** with rationale
- Clearly defined:
  - assumptions
  - risks
  - constraints
- Strong handling of edge cases:
  - rate limiting
  - hallucination
  - low source coverage
- Introduced important system components:
  - token budget manager
  - cost tracker
  - retry manager
- Designed for **scalability and robustness**
- Testing strategy is **fully decoupled from live APIs**

---

## Improvements in Condition B

- Explicit **conflict handling strategy** (callout boxes + citations)
- Defined **retry mechanism with dead-letter queue**
- Introduced **cost control via token budgeting**
- Added **structured logging for observability**
- Included **component-level interfaces and contracts**
- Clearly mapped **data flow across pipeline stages**

---

## Weaknesses of Condition B

- Does not produce full implementation code
- Slightly more complex design due to additional components
- Some assumptions (e.g., API limits, content quality) remain unvalidated

---

## Key Insights

- Condition A is **implementation-heavy but reasoning-light**
- Condition B is **reasoning-heavy and architecture-focused**
- Graph-based planning forces:
  - explicit thinking
  - better decomposition
  - clearer tradeoffs

---

## Conclusion

Condition B (graph-based planning) significantly improves the quality of system design by:

- Making assumptions and risks explicit
- Structuring decisions with rationale
- Improving modularity and clarity
- Enabling easier evaluation against objectives

While Condition A demonstrates strong coding ability, Condition B provides a **more complete and reliable engineering plan**, making it better suited for complex system design tasks.