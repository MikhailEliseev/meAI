"""Hermes Knowledge API — ingest, context, search, learn, status."""

import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from knowledge.vault import HermesKnowledgeVault

logger = logging.getLogger(__name__)

router = APIRouter(tags=["knowledge"])

_VAULT_BASE = Path(__file__).resolve().parent.parent / "knowledge"
vault = HermesKnowledgeVault(base_path=str(_VAULT_BASE))


# ── Models ────────────────────────────────────────────────────────────────

class IngestRequest(BaseModel):
    event_type: str
    payload: dict = {}


class IngestResponse(BaseModel):
    event_id: str
    status: str = "ingested"


class ContextQuery(BaseModel):
    domain: Optional[str] = None
    action: Optional[str] = None


class ContextResponse(BaseModel):
    patterns: list = []
    learnings: list = []
    rules: list = []
    query: str


class LearnRequest(BaseModel):
    execution_id: str


class LearnResponse(BaseModel):
    execution_id: str
    pattern: str
    extracted_at: str


class SearchResult(BaseModel):
    results: list = []
    query: str
    total: int = 0


class StatusResponse(BaseModel):
    executions_count: int
    patterns_count: int
    learnings_count: int
    rules_count: int
    last_ingest: Optional[str] = None
    loop_health: str


# ── Routes ─────────────────────────────────────────────────────────────────

@router.post("/ingest", response_model=IngestResponse, status_code=202)
async def ingest(body: IngestRequest):
    """Store an execution event in raw/executions/.

    Called by EventBus subscribers or directly via HTTP for manual ingestion.
    """
    from types import SimpleNamespace

    event_id = body.payload.get("correlation_id",
                                 body.payload.get("event_id",
                                                   f"evt-{hash(str(body.payload)) % 10**8:08d}"))

    wrapper = SimpleNamespace(
        event_type=body.event_type,
        payload=body.payload,
        event_id=event_id,
    )
    stored_id = await vault.ingest_execution(wrapper)
    logger.info(f"[Knowledge API] Ingested via HTTP: {body.event_type} → {stored_id}")
    return IngestResponse(event_id=stored_id)


@router.get("/context", response_model=ContextResponse)
async def context(domain: str = "", action: str = ""):
    """Search knowledge vault for patterns relevant to domain+action."""
    if not domain and not action:
        raise HTTPException(status_code=400, detail="domain or action required")

    result = await vault.query_context(domain, action)
    return ContextResponse(**result)


@router.get("/status", response_model=StatusResponse)
async def status():
    """Return vault health status."""
    stats = await vault.get_status()
    return StatusResponse(**stats)


@router.post("/learn", response_model=LearnResponse)
async def learn(body: LearnRequest):
    """Trigger LLM pattern extraction from a raw execution.

    Reads raw/executions/{id}.json, sends to LLM via OmniRoute,
    saves extracted patterns in wiki/patterns/.
    """
    from datetime import datetime, timezone
    from knowledge.ingest import LLMIngest

    execution_id = body.execution_id
    ingest = LLMIngest(vault)

    patterns = await ingest.extract_patterns(execution_id)

    if not patterns:
        raise HTTPException(
            status_code=404,
            detail=f"no patterns extracted for execution {execution_id}",
        )

    return LearnResponse(
        execution_id=execution_id,
        pattern=patterns[0],
        extracted_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/search", response_model=SearchResult)
async def search(q: str = "", domain: str = ""):
    """Full-text search across all knowledge layers."""
    if not q:
        raise HTTPException(status_code=400, detail="query parameter 'q' required")

    results = []
    search_dirs = [
        ("raw", vault.raw.glob("*.json")),
        ("patterns", vault.wiki_patterns.glob("*.md")),
        ("rules", vault.decisions.glob("*.md")),
    ]

    if domain:
        learnings_dir = vault.wiki_learnings / domain
        if learnings_dir.exists():
            search_dirs.append(("learnings", learnings_dir.rglob("*.md")))
    else:
        search_dirs.append(("learnings", vault.wiki_learnings.rglob("*.md")))

    for layer, files in search_dirs:
        for f in files:
            try:
                text = f.read_text(encoding="utf-8")
            except Exception:
                continue
            if q.lower() in text.lower():
                results.append({
                    "layer": layer,
                    "name": f.stem,
                    "snippet": text[:300],
                    "path": str(f.relative_to(vault.base)),
                })

    return SearchResult(results=results, query=q, total=len(results))
