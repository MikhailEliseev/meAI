"""FastAPI-приложение Гермес v2 — Phase 7.

Маршруты:
  GET  /health                 — healthcheck
  POST /tools/find-competitors — прозрачный прокси к aim-app:8000
  POST /api/chat/stream        — SSE-диалог через LLM с tool-calling
"""
import json
import logging
import re
import uuid

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import StreamingResponse

from app.llm import chat_with_tools
from app.session import (
    async_init_db,
    async_load_history,
    async_save_message,
    get_session_lock,
)
from app.tools import register_all
from app.tools.competitors import find_competitors

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Гермес v2", version="0.3.0")


# --- Health + find_competitors -----------------------------------------------

class FindCompetitorsRequest(BaseModel):
    url: str
    count: int = 3


@app.get("/health")
async def health():
    return {"status": "ok", "service": "hermes-v2", "version": "0.3.0"}


@app.post("/tools/find-competitors")
async def tools_find_competitors(req: FindCompetitorsRequest):
    return await find_competitors(req.url, req.count)


# --- SSE диалог ---------------------------------------------------------------

class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str


@app.on_event("startup")
async def startup():
    """Создаёт таблицу messages + регистрирует тулы."""
    await async_init_db()
    register_all()
    logger.info("startup: SQLite + tools registered")


# Fallback кнопки — наши самые сильные инструменты для следующих фаз.
# Базовый анализ (конкуренты + отзывы) уже сделан → ведём к соцсетям и SEO.
_FALLBACK_SUGGESTIONS = [
    {"label": "📸 Анализ соцсетей конкурентов", "tool": "run_instagram_content"},
    {"label": "🔍 Глубокий SEO-аудит сайта", "tool": "seo_audit"},
]

# Regex tolerant of markdown bold wrappers (LLM sometimes emits **[SUGGESTIONS]**)
_SUGGESTIONS_RE = re.compile(
    r"\*{0,2}\[SUGGESTIONS\]\*{0,2}\s*\n(.*?)\*{0,2}\[/SUGGESTIONS\]\*{0,2}",
    re.DOTALL,
)


def extract_suggestions(text: str) -> tuple[str, list[dict]]:
    """Парсит [SUGGESTIONS]...[/SUGGESTIONS] из текста.

    Returns: (clean_text_without_marker, buttons_list)
    Если маркера нет — (text, fallback_suggestions).
    """
    m = _SUGGESTIONS_RE.search(text)
    if not m:
        return text, _FALLBACK_SUGGESTIONS
    block = m.group(1)
    buttons = []
    for line in block.strip().split("\n"):
        line = line.strip()
        if "|" in line:
            label, tool = line.rsplit("|", 1)
            buttons.append({"label": label.strip(), "tool": tool.strip()})
    clean = _SUGGESTIONS_RE.sub("", text).rstrip()
    # Also strip leftover markdown (--- separators, empty lines before marker)
    clean = re.sub(r"\n---\s*$", "", clean)
    return clean, (buttons if buttons else _FALLBACK_SUGGESTIONS)


@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    """SSE-диалог: стримит токены LLM, сохраняет историю per-session.

    SSE-события (совместимы с Theme-чатом useStreamChat.js и chat-inline.php):
      text-delta   — токен ответа.
      tool-progress — начало/конец вызова тулза.
      suggestions  — кнопки действий.
      finish       — конец ответа, содержит session_id.
      error        — ошибка.
    """
    session_id = req.session_id or str(uuid.uuid4())
    logger.info("=== DEBUG chat_stream START: session=%s msg=%r ===", session_id[:8], req.message[:100])
    lock = get_session_lock(session_id)

    async def event_generator():
        async with lock:
            # Загрузить историю + добавить новое сообщение пользователя
            history = await async_load_history(session_id)
            await async_save_message(session_id, "user", req.message)
            history.append({"role": "user", "content": req.message})

            full_response = []
            formatted_parts = []  # таблицы/факты из кода (анти-галлюцинация)
            # Буфер для перехвата [SUGGESTIONS] маркера (стримится токенами).
            # Держим хвост буфера незакрытым, пока не убедимся что это не маркер.
            # LLM иногда оборачивает маркер в markdown bold: **[SUGGESTIONS]**
            MARKER_CORE = "[SUGGESTIONS]"
            MARKER_PREFIXES = ("**[SUGGESTIONS]", "[SUGGESTIONS]")
            sent_idx = 0  # сколько символов уже отправлено

            try:
                async for event in chat_with_tools(history):
                    kind = event[0]
                    if kind == "formatted":
                        # Точные данные из кода (таблицы ФНС, профиль).
                        # Стримим пользователю как text-delta, но храним отдельно
                        # чтобы prepend к clean_text перед сохранением в историю.
                        formatted_parts.append(event[1])
                        yield f"data: {json.dumps({'type': 'text-delta', 'textDelta': event[1]}, ensure_ascii=False)}\n\n"
                    elif kind == "text":
                        full_response.append(event[1])
                        accumulated = "".join(full_response)
                        # Найдём позицию начала маркера (с учётом ** префикса)
                        marker_pos = -1
                        for prefix in MARKER_PREFIXES:
                            pos = accumulated.find(prefix)
                            if pos != -1 and (marker_pos == -1 or pos < marker_pos):
                                marker_pos = pos
                        if marker_pos != -1:
                            safe_end = marker_pos
                        else:
                            # Не стримим последние символы — могут быть началом маркера.
                            # Учитываем самый длинный префикс (**[SUGGESTIONS])
                            hold_back = len(MARKER_PREFIXES[0])
                            safe_end = max(sent_idx, len(accumulated) - hold_back + 1)
                        if safe_end > sent_idx:
                            chunk = accumulated[sent_idx:safe_end]
                            yield f"data: {json.dumps({'type': 'text-delta', 'textDelta': chunk}, ensure_ascii=False)}\n\n"
                            sent_idx = safe_end
                    elif kind == "tool_start":
                        tool_name, tool_args, human_msg = event[1], event[2], event[3] if len(event) > 3 else ""
                        yield f"data: {json.dumps({'type': 'tool-progress', 'tool': tool_name, 'status': 'start', 'args': tool_args, 'message': human_msg}, ensure_ascii=False)}\n\n"
                    elif kind == "tool_result":
                        tool_name, result, human_msg = event[1], event[2], event[3] if len(event) > 3 else ""
                        yield f"data: {json.dumps({'type': 'tool-progress', 'tool': tool_name, 'status': 'done', 'result': result, 'message': human_msg}, ensure_ascii=False)}\n\n"
                    elif kind == "report_ready":
                        # ("report_ready", url, title) — Phase 11: авто-публикация отчёта
                        report_url = event[1] if len(event) > 1 else ""
                        report_title = event[2] if len(event) > 2 else ""
                        report_summary = (
                            f"Полный разбор: {report_title}"
                            if report_title else
                            "Полный разбор сайта, конкурентов и рынка"
                        )
                        logger.info("SSE: emitting report-ready url=%s", report_url)
                        yield f"data: {json.dumps({'type': 'report-ready', 'url': report_url, 'title': report_title, 'summary': report_summary}, ensure_ascii=False)}\n\n"
                    elif kind == "finish":
                        break
            except Exception as e:
                logger.error("chat_stream LLM error: %s", e)
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
                return

            # Финальная обработка: дослать остаток текста (без маркера) + suggestions
            accumulated = "".join(full_response)
            clean_text, buttons = extract_suggestions(accumulated)
            # Дослать текст, который не стримился (между sent_idx и концом чистого текста)
            clean_len = len(clean_text)
            if clean_len > sent_idx:
                yield f"data: {json.dumps({'type': 'text-delta', 'textDelta': clean_text[sent_idx:]}, ensure_ascii=False)}\n\n"

            # Сохранить ЧИСТЫЙ ответ (без маркера) в историю.
            # ВАЖНО: prepend formatted_parts (таблицы из кода) — иначе при
            # перезагрузке сессии таблицы исчезнут, останутся только выводы LLM.
            formatted_text = "".join(formatted_parts)
            full_clean = formatted_text + clean_text if clean_text else formatted_text
            if full_clean:
                await async_save_message(session_id, "assistant", full_clean)

            # Эмитить suggestions (CHAT-01, CHAT-05)
            if buttons:
                yield f"data: {json.dumps({'type': 'suggestions', 'buttons': buttons}, ensure_ascii=False)}\n\n"

            yield f"data: {json.dumps({'type': 'finish', 'session_id': session_id}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
