"""FastAPI-приложение Гермес v2.

Маршруты:
  GET  /health                 — healthcheck (Phase 1).
  POST /tools/find-competitors — прозрачный прокси к aim-app:8000 (Phase 1).
  POST /api/chat/stream        — SSE-диалог через deepseek-chat (Phase 2).
"""
import json
import logging
import uuid

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import StreamingResponse

from app.llm import stream_chat
from app.session import (
    async_init_db,
    async_load_history,
    async_save_message,
    get_session_lock,
)
from app.tools.competitors import find_competitors

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Гермес v2", version="0.2.0")


# --- Phase 1: health + find_competitors ------------------------------------

class FindCompetitorsRequest(BaseModel):
    url: str
    count: int = 3


@app.get("/health")
async def health():
    return {"status": "ok", "service": "hermes-v2"}


@app.post("/tools/find-competitors")
async def tools_find_competitors(req: FindCompetitorsRequest):
    return await find_competitors(req.url, req.count)


# --- Phase 2: диалоговый SSE -----------------------------------------------

class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str


@app.on_event("startup")
async def startup():
    """Создаёт таблицу messages при старте (идемпотентно)."""
    await async_init_db()
    logger.info("startup: SQLite init done")


@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    """SSE-диалог: стримит токены deepseek-chat, сохраняет историю per-session.

    SSE-события (совместимы с Theme-чатом useStreamChat.js):
      text-delta — токен ответа.
      finish     — конец ответа, содержит session_id.
      error      — ошибка.
    """
    session_id = req.session_id or str(uuid.uuid4())
    lock = get_session_lock(session_id)

    async def event_generator():
        async with lock:
            # Загрузить историю + добавить новое сообщение пользователя
            history = await async_load_history(session_id)
            await async_save_message(session_id, "user", req.message)
            history.append({"role": "user", "content": req.message})

            full_response = []
            try:
                async for token in stream_chat(history):
                    full_response.append(token)
                    yield f"data: {json.dumps({'type': 'text-delta', 'textDelta': token}, ensure_ascii=False)}\n\n"
            except Exception as e:
                logger.error("chat_stream LLM error: %s", e)
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
                return

            # Сохранить ответ ассистента в историю
            assistant_text = "".join(full_response)
            if assistant_text:
                await async_save_message(session_id, "assistant", assistant_text)

            yield f"data: {json.dumps({'type': 'finish', 'session_id': session_id}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
