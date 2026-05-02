from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="planninggraph",
    description="Decision graph extraction and maintenance for AI-assisted software development",
    version="0.1.0",
)


class ExtractRequest(BaseModel):
    text: str


# TODO: wire up real handlers once planninggraph modules are implemented


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/extract")
def extract(req: ExtractRequest):
    """Extract a decision graph from unstructured text."""
    from planninggraph.extractor import extract_graph
    graph = extract_graph(req.text)
    return graph.model_dump()


@app.post("/update")
def update(req: ExtractRequest):
    """Apply an incremental update to the current graph."""
    raise NotImplementedError


@app.get("/risks")
def risks():
    """Surface anticipated failure modes from the current graph."""
    raise NotImplementedError
