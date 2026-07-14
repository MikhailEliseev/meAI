"""FastAPI-приложение Гермес v2 — Walking Skeleton (Phase 1).

Два маршрута:
  GET  /health                 — healthcheck.
  POST /tools/find-competitors — прозрачный прокси к aim-app:8000.

LLM/чат/SSE добавляются в Phase 2. Остальные тулы — в Phase 3.
"""
import logging

from fastapi import FastAPI
from pydantic import BaseModel

from app.tools.competitors import find_competitors

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Гермес v2", version="0.1.0")


class FindCompetitorsRequest(BaseModel):
    url: str
    count: int = 3


@app.get("/health")
async def health():
    return {"status": "ok", "service": "hermes-v2"}


@app.post("/tools/find-competitors")
async def tools_find_competitors(req: FindCompetitorsRequest):
    return await find_competitors(req.url, req.count)
