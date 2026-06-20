"""
run_content_gaps — Hermes tool: Content Gap Analysis

Сравнивает контент сайта клиники с конкурентами, выявляет пробелы:
- Темы, которые конкуренты покрывают, а клиент — нет
- Контентные преимущества клиента
- Steal-worthy tactics (тактики конкурентов, которые стоит перенять)
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


async def handle_run_content_gaps(url=None, client_site=None, competitor_site=None, **kwargs) -> str:
    """Analyze content gaps between client and competitors.

    Args:
        url: Website URL to analyze content gaps for.
        client_site: Client website URL (alternative to url).
        competitor_site: Competitor website URL for comparison.

    Returns:
        JSON with gaps, advantages, steal-worthy tactics, and messaging strategy.
    """
    unpacked = _normalize_args(url, {"url": ""})
    if unpacked:
        url = unpacked["url"]
        client_site = unpacked.get("client_site", client_site)
        competitor_site = unpacked.get("competitor_site", competitor_site)

    # Also extract from kwargs
    cs = kwargs.get("client_site", "")
    if cs and not client_site:
        client_site = cs
    comp = kwargs.get("competitor_site", "")
    if comp and not competitor_site:
        competitor_site = comp

    # Target: URL > client_site
    target = url or client_site or ""
    if target and not target.startswith(("http://", "https://")):
        target = "https://" + target

    if not target:
        return json.dumps({"error": "URL is required"})

    cache_key = f"gaps_{target}"
    cached = _cache.get(cache_key)
    if cached is not None:
        cached_ts, cached_result = cached
        if time.time() - cached_ts < _CACHE_TTL:
            return cached_result
        del _cache[cache_key]

    logger.info("Analyzing content gaps for: %s (competitor=%s)", target, competitor_site or "none")

    try:
        from app.main import push_tool_progress
        push_tool_progress("gaps", f"🔍 Ищу контентные пробелы для {target}…")

        payload = {"url": target}
        if competitor_site:
            payload["competitor_site"] = competitor_site

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.post(
                f"{AIM_API_BASE}/api/content/gaps",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

            task_id = data.get("task_id")
            if not task_id:
                push_tool_progress("gaps", "✅ Анализ контента готов!")
                result_json = json.dumps(data, ensure_ascii=False, indent=2)
                _cache[cache_key] = (time.time(), result_json)
                return result_json

            status_url = f"{AIM_API_BASE}/api/content/gaps/{task_id}"
            poll_count = 0

            while True:
                await asyncio.sleep(POLL_INTERVAL)
                poll_count += 1
                status_resp = await client.get(status_url)
                status_resp.raise_for_status()
                status_data = status_resp.json()

                st = status_data.get("status", "unknown")
                if st == "done":
                    push_tool_progress("gaps", "✅ Анализ контента готов!")
                    result = status_data.get("result", {})
                    result_json = json.dumps(result, ensure_ascii=False, indent=2)
                    _cache[cache_key] = (time.time(), result_json)
                    return result_json
                if st == "error":
                    return json.dumps({"error": "Content gap analysis failed", "detail": status_data.get("error", "Unknown")})

    except httpx.HTTPStatusError as e:
        logger.error("AIM API error for content gaps: %s", e)
        return json.dumps({"error": "AIM API error", "status": e.response.status_code, "detail": str(e)})
    except Exception as e:
        logger.exception("Content gaps error")
        return json.dumps({"error": "Unexpected error", "detail": str(e)})


registry.register(
    name="run_content_gaps",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "run_content_gaps",
            "description": "Analyze content gaps vs competitors: what topics competitors cover but client doesn't. Returns gaps, advantages, and steal-worthy tactics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Website URL to analyze content gaps for"},
                },
                "required": ["url"],
            },
        },
    },
    handler=handle_run_content_gaps,
    check_fn=lambda: True,
    is_async=True,
    description="Analyze content gaps vs competitors — gaps, advantages, steal-worthy tactics",
    emoji="🔍",
)
