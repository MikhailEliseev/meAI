"""Thin-wrapper find_competitors — прозрачный HTTP-прокси к aim-app:8000.

Паттерн скопирован из бэкапа app/tools/find_competitors.py:283-298:
  async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
      response = await client.post(f"{AIM_API_BASE}/api/competitors/find", json=payload)
      response.raise_for_status()
      data = response.json()

Per CLAUDE.md convention: handler НИКОГДА не бросает исключение наружу —
при ошибке возвращает {"error": ...}.
"""
import logging

import httpx

from app.config import AIM_API_BASE, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)


async def find_competitors(url: str, count: int = 3) -> dict:
    """Прозрачный прокси к aim-app POST /api/competitors/find.

    Args:
        url: сайт клиники (схема добавляется если нет).
        count: сколько конкурентов вернуть.

    Returns:
        JSON-ответ aim-app как есть, либо {"error": ...} при сбое.
    """
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    logger.info("find_competitors proxy: url=%s count=%d", url, count)
    payload = {"url": url, "count": count}

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{AIM_API_BASE}/api/competitors/find",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error("find_competitors upstream error: %s status=%s", url, e.response.status_code)
        return {
            "error": "upstream aim-app error",
            "status": e.response.status_code,
            "detail": str(e),
        }
    except httpx.RequestError as e:
        logger.error("find_competitors cannot reach aim-app: %s — %s", url, e)
        return {
            "error": "cannot reach aim-app",
            "detail": str(e),
        }
