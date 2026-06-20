"""
run_smi_mentions — Hermes tool: SMI (Mass Media) Mentions Search

Ищет упоминания клиники в СМИ:
- Business: forbes.ru, rbc.ru, kommersant.ru
- Glossy: marieclaire.ru, vogue.ru
- Medical: vademec.ru
- Regional: fontanka.ru, dp.ru, sobaka.ru
- Telegram-media: Mash, Baza, 112, SHOT
"""

import asyncio
import json
import logging
import time

import httpx

from tools.registry import registry

logger = logging.getLogger(__name__)

AIM_API_BASE = "http://aim-app:8000"
REQUEST_TIMEOUT = 120.0
POLL_INTERVAL = 2.0

_cache: dict[str, tuple[float, str]] = {}
_CACHE_TTL = 600


def _normalize_args(first_param, defaults):
    if isinstance(first_param, dict):
        return {k: first_param.get(k, defaults[k]) for k in defaults}
    return None


async def handle_run_smi_mentions(url=None, **kwargs) -> str:
    """Search SMI mentions for a clinic.

    Args:
        url: Website URL or clinic name to search mentions for.

    Returns:
        JSON with mentions: source, title, date, sentiment, reach.
    """
    unpacked = _normalize_args(url, {"url": ""})
    if unpacked:
        url = unpacked["url"]

    if url and not url.startswith(("http://", "https://")):
        url = "https://" + url

    if not url:
        return json.dumps({"error": "URL or clinic name is required"})

    cache_key = f"smi_{url}"
    cached = _cache.get(cache_key)
    if cached is not None:
        cached_ts, cached_result = cached
        if time.time() - cached_ts < _CACHE_TTL:
            return cached_result
        del _cache[cache_key]

    logger.info("Searching SMI mentions for: %s", url)

    try:
        from app.main import push_tool_progress
        push_tool_progress("smi", f"📰 Ищу упоминания в СМИ для {url}…")

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.post(
                f"{AIM_API_BASE}/api/smi/search",
                json={"url": url},
            )
            resp.raise_for_status()
            data = resp.json()

            task_id = data.get("task_id")
            if not task_id:
                push_tool_progress("smi", "✅ Поиск СМИ завершён!")
                result_json = json.dumps(data, ensure_ascii=False, indent=2)
                _cache[cache_key] = (time.time(), result_json)
                return result_json

            status_url = f"{AIM_API_BASE}/api/smi/search/{task_id}"
            poll_count = 0

            while True:
                await asyncio.sleep(POLL_INTERVAL)
                poll_count += 1
                status_resp = await client.get(status_url)
                status_resp.raise_for_status()
                status_data = status_resp.json()

                st = status_data.get("status", "unknown")
                if st == "done":
                    push_tool_progress("smi", "✅ Поиск СМИ завершён!")
                    result = status_data.get("result", {})
                    result_json = json.dumps(result, ensure_ascii=False, indent=2)
                    _cache[cache_key] = (time.time(), result_json)
                    return result_json
                if st == "error":
                    return json.dumps({"error": "SMI search failed", "detail": status_data.get("error", "Unknown")})

    except httpx.HTTPStatusError as e:
        logger.error("AIM API error for SMI: %s", e)
        return json.dumps({"error": "AIM API error", "status": e.response.status_code, "detail": str(e)})
    except Exception as e:
        logger.exception("SMI search error")
        return json.dumps({"error": "Unexpected error", "detail": str(e)})


registry.register(
    name="run_smi_mentions",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "run_smi_mentions",
            "description": "Search mass media mentions for a clinic across Business (Forbes, RBC), Glossy, Medical, Regional, and Telegram-media sources.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Website URL or clinic name to search media mentions for"},
                },
                "required": ["url"],
            },
        },
    },
    handler=handle_run_smi_mentions,
    check_fn=lambda: True,
    is_async=True,
    description="Search SMI/media mentions across business, medical, and regional sources",
    emoji="📰",
)
