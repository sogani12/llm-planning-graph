# Experiment Instructions

Comparative evaluation: Condition A (standard AI planning) vs Condition B (decision graph-augmented planning).

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

**Setup:** Open two windows side by side:
- Window 1: Claude Code / Cursor (planning session)
- Window 2: A separate Claude chat at claude.ai (for graph extraction)

**Step 1.** In Window 2, start a new chat. Paste the entire contents of
`planninggraph/prompts/extraction_system.txt` as the **system prompt** (use the
system prompt field if available, otherwise prepend it before your first message).

**Step 2.** In Window 1, paste `prompt.txt` as your opening message. Also add:
> "As we plan, I will periodically share an updated decision graph capturing our
> decisions so far. Please take it into account when continuing."

**Step 3.** Answer the agent's clarifying questions. After each substantive exchange
(2–4 turns), do the following:

- Copy the conversation so far
- In Window 2, send: "Extract a decision graph from this planning conversation:\n\n[paste conversation]"
- Copy the JSON response
- Save it as `condition_b/graph_v1.json` (increment version each time)
- Back in Window 1, send: "Here is the current decision graph from our planning so far. Continue with this in mind:\n\n[paste JSON]"

**Step 4.** Repeat Step 3 until the plan is complete.

**Step 5.** Save:
- Full conversation → `condition_b/conversation.md`
- Final plan → `condition_b/plan.md`
- Final graph JSON → `condition_b/graph_final.json`

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
