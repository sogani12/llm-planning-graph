from fastapi import FastAPI
from pydantic import BaseModel

from planninggraph.failure import surface_risks
from planninggraph.graph import PlanningGraph
from planninggraph.maintenance import apply_update

app = FastAPI(
    title="planninggraph",
    description="Decision graph extraction and maintenance for AI-assisted software development",
    version="0.1.0",
)

CURRENT_GRAPH = PlanningGraph()


class ExtractRequest(BaseModel):
    text: str


@app.get("/health")
def health():
    return {
        "status": "ok",
        "nodes": len(CURRENT_GRAPH.to_schema().nodes),
        "edges": len(CURRENT_GRAPH.to_schema().edges),
    }


@app.post("/extract")
def extract(req: ExtractRequest):
    """Extract a decision graph from unstructured text."""
    from planninggraph.extractor import extract_graph
    graph = extract_graph(req.text)
    return graph.model_dump()


@app.post("/update")
def update(req: ExtractRequest):
    """Apply an incremental update to the current graph."""
    result = apply_update(CURRENT_GRAPH, req.text)
    result["graph"] = CURRENT_GRAPH.to_schema().model_dump()
    return result


@app.get("/risks")
def risks():
    """Surface anticipated failure modes from the current graph."""
    return [risk.model_dump() for risk in surface_risks(CURRENT_GRAPH)]
