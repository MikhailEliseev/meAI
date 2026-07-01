"""
geo_optimizer_tools — Hermes tool: GEO audit via geo-optimizer-skill package.

Wraps the geo_optimizer Python API (v4.13.0) for LLM-driven GEO analysis.
Covers: GEO score, robots.txt, llms.txt, schema markup, meta tags, content,
trust signals, AI discovery readiness, citations, competitor comparison.
"""

import json
import logging
import os
import sys

from tools.registry import registry

logger = logging.getLogger(__name__)

# geo-optimizer-skill installed to custom prefix
_GEOPATH = "/opt/data/pip-packages"
if _GEOPATH not in sys.path:
    sys.path.insert(0, _GEOPATH)

# Cache: URL → (timestamp, result_json), TTL = 15 minutes
_cache: dict[str, tuple[float, str]] = {}
_CACHE_TTL = 900


async def handle_run_geo_audit(
    url: str = None,
    refresh: bool = False,
    **kwargs,
) -> str:
    """Run a full GEO audit on a target website using geo-optimizer-skill.

    Returns GEO score (0-100), band (A-F), detailed breakdown across
    15+ dimensions, prioritized recommendations, and AI discovery readiness.

    Args:
        url: Target website URL (with https://)
        refresh: Skip cache and run fresh audit
    """
    if isinstance(url, dict):
        d = url
        url = d.get("url", "")
        refresh = d.get("refresh", False)

    if not url or not isinstance(url, str):
        return json.dumps({"error": "url is required (string)"})

    url = url.strip()
    if not url.startswith("http"):
        url = f"https://{url}"

    import time

    # Check cache
    cache_key = url.lower().rstrip("/")
    if not refresh and cache_key in _cache:
        ts, cached = _cache[cache_key]
        if time.time() - ts < _CACHE_TTL:
            logger.info("geo_audit: cache hit for %s", url)
            return cached

    logger.info("geo_audit: starting audit for %s", url)

    try:
        import asyncio
        from dataclasses import asdict

        from geo_optimizer import audit_async

        result = await audit_async(url, use_cache=not refresh)
        data = _serialize_audit_result(result)

        output = json.dumps(data, ensure_ascii=False, indent=2)
        _cache[cache_key] = (time.time(), output)
        return output

    except Exception as e:
        logger.error("geo_audit failed for %s: %s", url, e, exc_info=True)
        return json.dumps({"error": "GEO audit failed", "detail": str(e)})


def _serialize_audit_result(result) -> dict:
    """Convert AuditResult to JSON-safe dict with only meaningful fields."""
    from dataclasses import asdict

    raw = asdict(result)

    # Flatten nested dataclass results for LLM readability
    out = {
        "url": raw.get("url"),
        "timestamp": raw.get("timestamp"),
        "score": raw.get("score"),
        "band": raw.get("band"),
        "http_status": raw.get("http_status"),
        "page_size_bytes": raw.get("page_size"),
        "audit_duration_ms": raw.get("audit_duration_ms"),
        "recommendations": raw.get("recommendations", []),
        "score_breakdown": raw.get("score_breakdown", {}),
    }

    # Include non-empty sub-results
    for key in (
        "robots", "llms", "schema", "meta", "content", "citability",
        "signals", "ai_discovery", "trust_stack", "negative_signals",
        "prompt_injection", "brand_entity", "webmcp", "cdn_check",
        "js_rendering", "rag_chunk", "embedding_proximity",
        "content_decay", "platform_citation", "brand_sentiment",
        "context_window", "instruction_readiness", "intent_mapping",
        "hallucination_bait",
    ):
        val = raw.get(key)
        if val:
            out[key] = val

    if raw.get("error"):
        out["error"] = raw["error"]

    return out


registry.register(
    name="run_geo_audit",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "run_geo_audit",
            "description": (
                "Run a full GEO (Generative Engine Optimization) audit on a website. "
                "Checks: GEO score (0-100), robots.txt, llms.txt, schema markup, "
                "meta tags, content quality, trust signals, AI discovery readiness, "
                "citations, brand sentiment, and more. "
                "Returns score, band, prioritized recommendations, and detailed breakdown. "
                "Use this for any 'GEO audit' or 'AI search optimization' request."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "[REQUIRED] Target website URL (e.g., https://arclinic.ru)",
                    },
                    "refresh": {
                        "type": "boolean",
                        "description": "Skip cache and run fresh audit (default: false)",
                    },
                },
                "required": ["url"],
            },
        },
    },
    handler=handle_run_geo_audit,
    is_async=True,
    description="Run a full GEO (Generative Engine Optimization) audit on a website",
)
