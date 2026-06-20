"""
run_review_platforms — Hermes tool: Review Platforms Scanner

Собирает рейтинги и отзывы клиники со всех доступных платформ:
ProDoctorov, Яндекс.Карты, 2ГИС, Google Maps, otzovik.com, irecommend.ru, zoon.ru.
"""

import asyncio
import json
import logging
import time

import httpx

from tools.registry import registry

logger = logging.getLogger(__name__)

AIM_API_BASE = "http://aim-app:8000"
REQUEST_TIMEOUT = 180.0
POLL_INTERVAL = 2.0

_cache: dict[str, tuple[float, str]] = {}
_CACHE_TTL = 600


def _normalize_args(first_param, defaults):
    if isinstance(first_param, dict):
        return {k: first_param.get(k, defaults[k]) for k in defaults}
    return None


async def handle_run_review_platforms(url=None, **kwargs) -> str:
    """Scan review platforms for a clinic.

    Args:
        url: Website URL or clinic name to search.

    Returns:
        JSON with ratings, reviews count, positive/negative themes per platform.
    """
    unpacked = _normalize_args(url, {"url": ""})
    if unpacked:
        url = unpacked["url"]

    if url and not url.startswith(("http://", "https://")):
        url = "https://" + url

    if not url:
        return json.dumps({"error": "URL or clinic name is required"})

    cache_key = f"reviews_{url}"
    cached = _cache.get(cache_key)
    if cached is not None:
        cached_ts, cached_result = cached
        if time.time() - cached_ts < _CACHE_TTL:
            return cached_result
        del _cache[cache_key]

    logger.info("Scanning review platforms for: %s", url)

    try:
        from app.main import push_tool_progress
        push_tool_progress("reviews", f"⭐ Собираю отзывы для {url}…")

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.post(
                f"{AIM_API_BASE}/api/reviews/scan",
                json={"url": url},
            )
            resp.raise_for_status()
            data = resp.json()

            task_id = data.get("task_id")
            if not task_id:
                push_tool_progress("reviews", "✅ Отзывы собраны!")
                result_json = json.dumps(data, ensure_ascii=False, indent=2)
                _cache[cache_key] = (time.time(), result_json)
                return result_json

            status_url = f"{AIM_API_BASE}/api/reviews/scan/{task_id}"
            poll_count = 0

            while True:
                await asyncio.sleep(POLL_INTERVAL)
                poll_count += 1
                status_resp = await client.get(status_url)
                status_resp.raise_for_status()
                status_data = status_resp.json()

                st = status_data.get("status", "unknown")
                if st == "done":
                    push_tool_progress("reviews", "✅ Отзывы собраны!")
                    result = status_data.get("result", {})
                    result_json = json.dumps(result, ensure_ascii=False, indent=2)
                    _cache[cache_key] = (time.time(), result_json)
                    return result_json
                if st == "error":
                    return json.dumps({"error": "Review scan failed", "detail": status_data.get("error", "Unknown")})

    except httpx.HTTPStatusError as e:
        logger.error("AIM API error for reviews: %s", e)
        return json.dumps({"error": "AIM API error", "status": e.response.status_code, "detail": str(e)})
    except Exception as e:
        logger.exception("Review scan error")
        return json.dumps({"error": "Unexpected error", "detail": str(e)})


registry.register(
    name="run_review_platforms",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "run_review_platforms",
            "description": "Scan all review platforms (ProDoctorov, Yandex Maps, 2GIS, Google Maps, otzovik, irecommend, zoon.ru) for clinic ratings and patient reviews.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Website URL or clinic name to search reviews for"},
                },
                "required": ["url"],
            },
        },
    },
    handler=handle_run_review_platforms,
    check_fn=lambda: True,
    is_async=True,
    description="Scan review platforms for clinic ratings and patient reviews",
    emoji="⭐",
)
