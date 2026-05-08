# Condition A Plan

## Final System Proposed

The agent produced a full-stack Autonomous Research Agent with:

- React UI for entering a research topic and viewing pipeline progress
- Python backend for research orchestration
- Multi-stage pipeline: retrieval, processing, synthesis, reporting
- Mock mode for running without live API calls
- Multi-format report generation: Markdown, HTML, DOCX
- Testing harness using mock fixtures

## Architecture

### Frontend
- React UI with topic input
- Example research topics
- Live pipeline visualization
- Sources tab
- Conflicts tab
- Report tab
- Download buttons for Markdown and HTML

### Backend
- FastAPI API server
- CLI entry point
- Pipeline orchestrator
- Retriever
- Processor
- Synthesizer
- Reporter
- Retry utility
- Cache utility
- Structured logger
- Mock fixtures
- Tests

## Pipeline Stages

1. Retrieval  
   Searches and fetches sources in parallel using SerpAPI, Brave, or mock data.

2. Processing  
   Deduplicates sources using URL, content hash, and similarity checks. Extracts facts and detects conflicts.

3. Synthesis  
   Uses Claude to generate a structured research report from processed sources.

4. Reporting  
   Produces Markdown, HTML, and DOCX outputs.

## Key Architectural Decisions

- Uses parallel retrieval for faster source collection.
- Uses mock mode so tests do not depend on live APIs.
- Uses three-level deduplication to catch exact and near-duplicate sources.
- Uses SSE streaming to show pipeline progress in the UI.
- Uses structured models/contracts between pipeline stages.
- Uses retry and cache utilities for reliability.

## Testing Strategy

The system includes mock fixtures and tests that validate the pipeline without making live API calls.

## Notes for Evaluation

Condition A produced a strong implementation-heavy plan and even generated full UI/backend code. However, it focused more on implementation than explicitly documenting assumptions, risks, tradeoffs, and rationale.