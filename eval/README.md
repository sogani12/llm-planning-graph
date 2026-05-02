# Experiment Instructions

Comparative evaluation: Condition A (standard AI planning) vs Condition B (decision graph-augmented planning).

The project prompt (`experiments/<project>/prompt.txt`) is **identical** for both conditions.
The only difference is that Condition B uses a system prompt that instructs the agent to maintain a decision graph as it plans.

---

## Running an Experiment

### Condition A — Standard Planning

1. Open Claude Code or Cursor in a fresh project directory
2. Paste the contents of `experiments/<project>/prompt.txt` as your opening message
3. Answer any clarifying questions the agent asks naturally
4. Let the agent produce a full plan (usually a markdown document or file tree)
5. Save the full conversation to `experiments/<project>/condition_a/conversation.md`
6. Save the final plan document to `experiments/<project>/condition_a/plan.md`

---

### Condition B — Graph-Augmented Planning

**Setup:** In Claude Code, Cursor, or any Claude interface that supports a system prompt field, set the system prompt to the full contents of `planninggraph/prompts/extraction_system.txt` before starting.

**Step 1.** With the system prompt set, paste `prompt.txt` as your opening message — the same message used in Condition A.

**Step 2.** Answer the agent's clarifying questions naturally, the same way you would in Condition A.

**Step 3.** The agent will plan in phases. After each phase it will:
- Output a `[GRAPH UPDATE]` block containing the full graph JSON so far
- Ask you 2–3 targeted follow-up questions about assumptions or risks it flagged

Answer those questions naturally. The agent will update the graph and continue.

**Step 4.** Repeat until the agent writes the final implementation plan.

**Step 5.** Save:
- Full conversation → `condition_b/conversation.md`
- Final plan → `condition_b/plan.md`
- Each graph version → `condition_b/graph_v1.json`, `graph_v2.json`, … (copy from `[GRAPH UPDATE]` blocks in the conversation)
- Final graph → `condition_b/graph_final.json`

---

### After Both Conditions

1. Fill in `experiments/<project>/objectives.md`:
   - Score each objective 0 / 0.5 / 1 for each condition
   - Fill in summary counts from `graph_final.json`
   - Document 2–3 specific qualitative catches from condition B

2. Run the comparison table:
   ```
   python eval/compare.py
   ```

---

## Visualising a Graph

With the Streamlit demo running (`docker compose up demo`):

1. Open `http://localhost:8501`
2. Paste the contents of `graph_final.json` into the JSON editor
3. Click "Render Graph"

---

## Automated Extraction (once ANTHROPIC_API_KEY is set)

For post-hoc extraction from a completed conversation (not needed during Condition B — the agent maintains the graph live):

```python
from planninggraph.extractor import extract_graph
graph = extract_graph(open("condition_b/conversation.md").read())
print(graph.model_dump_json(indent=2))
```

Or via the API:
```bash
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"text": "..."}'
```
