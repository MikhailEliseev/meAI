"""
run_pagespeed — Hermes tool: PageSpeed Insights

Вызывает Google PageSpeed Insights API v5 напрямую (бесплатно, без ключа).
Возвращает Core Web Vitals: Performance score, LCP, FCP, TBT, CLS.
"""

import asyncio
import json
import logging
import time

import httpx

from tools.registry import registry

logger = logging.getLogger(__name__)

PAGESPEED_API = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
REQUEST_TIMEOUT = 60.0

_cache: dict[str, tuple[float, str]] = {}
_CACHE_TTL = 600


def _normalize_args(first_param, defaults):
    if isinstance(first_param, dict):
        return {k: first_param.get(k, defaults[k]) for k in defaults}
    return None


async def _run_pagespeed_for_strategy(client: httpx.AsyncClient, url: str, strategy: str) -> dict:
    """Run PageSpeed for one strategy (mobile/desktop) with retry on 429."""
    from app.key_bank import key_bank
    google_key = key_bank.get("GOOGLE_API_KEY")
    params: dict = {"url": url, "strategy": strategy, "category": "performance"}
    if google_key:
        params["key"] = google_key

    last_error = None
    for attempt in range(3):
        try:
            resp = await client.get(
                PAGESPEED_API,
                params=params,
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            break
        except httpx.HTTPStatusError as e:
            last_error = e
            if e.response.status_code == 429 and attempt < 2:
                await asyncio.sleep(2.0 * (attempt + 1))
                continue
            raise
    else:
        raise last_error  # type: ignore[misc]

    data = resp.json()

    lighthouse = data.get("lighthouseResult", {})
    categories = lighthouse.get("categories", {})
    audits = lighthouse.get("audits", {})

    performance = categories.get("performance", {})
    score = int((performance.get("score", 0) or 0) * 100)

    # Core Web Vitals из audits
    def _audit_value(audit_id: str, metric: str = "displayValue") -> str:
        a = audits.get(audit_id, {})
        return a.get(metric, a.get("numericValue", "N/A"))

    return {
        "strategy": strategy,
        "performance_score": score,
        "lcp": _audit_value("largest-contentful-paint"),
        "fcp": _audit_value("first-contentful-paint"),
        "tbt": _audit_value("total-blocking-time"),
        "cls": _audit_value("cumulative-layout-shift"),
        "si": _audit_value("speed-index"),
        "tti": _audit_value("interactive"),
    }


async def handle_run_pagespeed(url=None, **kwargs) -> str:
    """Run Google PageSpeed Insights analysis on a website.

    Args:
        url: Website URL to analyze.

    Returns:
        JSON with performance metrics and Core Web Vitals for mobile + desktop.
    """
    unpacked = _normalize_args(url, {"url": ""})
    if unpacked:
        url = unpacked["url"]

    if not url:
        return json.dumps({"error": "URL is required"})

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    cached = _cache.get(url)
    if cached is not None:
        cached_ts, cached_result = cached
        if time.time() - cached_ts < _CACHE_TTL:
            logger.info("PageSpeed cache HIT for: %s", url)
            return cached_result
        del _cache[url]

    logger.info("Running PageSpeed for: %s", url)

    try:
        from app.main import push_tool_progress

        push_tool_progress("pagespeed", f"🚀 Замеряю скорость {url}…")

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            # Запускаем mobile + desktop последовательно (Google rate-limits parallel)
            mobile = await _run_pagespeed_for_strategy(client, url, "mobile")
            await asyncio.sleep(1.5)
            desktop = await _run_pagespeed_for_strategy(client, url, "desktop")

        result = {
            "url": url,
            "mobile": mobile,
            "desktop": desktop,
            "analyzed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        push_tool_progress("pagespeed", "✅ PageSpeed готов!")
        result_json = json.dumps(result, ensure_ascii=False, indent=2)
        _cache[url] = (time.time(), result_json)
        return result_json

    except httpx.HTTPStatusError as e:
        logger.error("Google PageSpeed API error: %s", e)
        detail = str(e)
        if e.response.status_code == 429:
            detail = "Rate limited by Google. Set GOOGLE_API_KEY env var for higher quota (free from Google Cloud Console)."
        elif e.response.status_code == 403:
            detail = "Access denied. May need valid GOOGLE_API_KEY."
        return json.dumps({"error": "PageSpeed API error", "status": e.response.status_code, "detail": detail})
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
