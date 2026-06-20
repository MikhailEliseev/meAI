"""
run_pagespeed — Hermes tool: PageSpeed Insights

POST http://aim-app:8000/api/pagespeed/analyze → starts async analysis
GET  http://aim-app:8000/api/pagespeed/analyze/{task_id} → polls until done

Returns Core Web Vitals: LCP, FCP, TBT, CLS + Performance score.
"""

import asyncio
import json
import logging
import time

import httpx

from tools.registry import registry

logger = logging.getLogger(__name__)

AIM_API_BASE = "http://aim-app:8000"
REQUEST_TIMEOUT = 300.0
POLL_INTERVAL = 2.0

# In-memory cache
_cache: dict[str, tuple[float, str]] = {}
_CACHE_TTL = 600


def _normalize_args(first_param, defaults):
    if isinstance(first_param, dict):
        return {k: first_param.get(k, defaults[k]) for k in defaults}
    return None


async def handle_run_pagespeed(url=None, **kwargs) -> str:
    """Run PageSpeed Insights analysis on a website.

    Args:
        url: Website URL to analyze.

    Returns:
        JSON with performance metrics and Core Web Vitals.
    """
    unpacked = _normalize_args(url, {"url": ""})
    if unpacked:
        url = unpacked["url"]

    if url and not url.startswith(("http://", "https://")):
        url = "https://" + url

    if not url:
        return json.dumps({"error": "URL is required"})

    cached = _cache.get(url)
    if cached is not None:
        cached_ts, cached_result = cached
        if time.time() - cached_ts < _CACHE_TTL:
            logger.info("PageSpeed cache HIT for: %s", url)
            return cached_result
        else:
            del _cache[url]

    logger.info("Running PageSpeed for: %s", url)

    try:
        from app.main import push_tool_progress
        push_tool_progress("pagespeed", f"🚀 Замеряю скорость {url}…")

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.post(
                f"{AIM_API_BASE}/api/pagespeed/analyze",
                json={"url": url},
            )
            resp.raise_for_status()
            data = resp.json()

            task_id = data.get("task_id")
            if not task_id:
                # Synchronous response
                push_tool_progress("pagespeed", "✅ PageSpeed готов!")
                result_json = json.dumps(data, ensure_ascii=False, indent=2)
                _cache[url] = (time.time(), result_json)
                return result_json

            # Poll async
            status_url = f"{AIM_API_BASE}/api/pagespeed/analyze/{task_id}"
            poll_count = 0

            while True:
                await asyncio.sleep(POLL_INTERVAL)
                poll_count += 1

                status_resp = await client.get(status_url)
                status_resp.raise_for_status()
                status_data = status_resp.json()

                st = status_data.get("status", "unknown")
                if st == "done":
                    push_tool_progress("pagespeed", "✅ PageSpeed готов!")
                    result = status_data.get("result", {})
                    result_json = json.dumps(result, ensure_ascii=False, indent=2)
                    _cache[url] = (time.time(), result_json)
                    return result_json

                if st == "error":
                    return json.dumps({
                        "error": "PageSpeed analysis failed",
                        "detail": status_data.get("error", "Unknown"),
                    })

                if poll_count % 3 == 0:
                    push_tool_progress("pagespeed", f"⏳ PageSpeed: опрос #{poll_count}…")

    except httpx.HTTPStatusError as e:
        logger.error("AIM API error for PageSpeed: %s", e)
        return json.dumps({"error": "AIM API error", "status": e.response.status_code, "detail": str(e)})
    except Exception as e:
        logger.exception("PageSpeed error")
        return json.dumps({"error": "Unexpected error", "detail": str(e)})


registry.register(
    name="run_pagespeed",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "run_pagespeed",
            "description": "Run Google PageSpeed Insights analysis: Performance, Accessibility, Best Practices, SEO scores + Core Web Vitals (LCP, FCP, TBT, CLS).",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Website URL to analyze"},
                },
                "required": ["url"],
            },
        },
    },
    handler=handle_run_pagespeed,
    check_fn=lambda: True,
    is_async=True,
    description="Run Google PageSpeed Insights: performance scores and Core Web Vitals",
    emoji="🚀",
)
