"""
run_web_search — Hermes tool: web search via Firecrawl

Searches the web and returns results with page content.
Registered in toolset "aim-operations" so it's available in PRESALE mode.

Uses the same Firecrawl key bank as hermes-debug tools.
"""

import json
import logging
import os

from tools.registry import registry
from .firecrawl_key_bank import get_key_with_fallback, mark_exhausted, classify_exhaustion, active_count

logger = logging.getLogger(__name__)

_FALLBACK_KEY = os.environ.get("FIRECRAWL_API_KEY", "").strip()


async def handle_run_web_search(query=None, limit=None, source=None, **kwargs) -> str:
    """Search the web via Firecrawl.

    Use this to find information about competitors, clinics, doctors,
    market data, or any topic relevant to the presale conversation.

    Args:
        query: Search query string
        limit: Max results (default: 5, max: 10)
        source: 'web' (default), 'news', or 'images'

    Returns:
        JSON string with search results including title, URL, description, and markdown.
    """
    if isinstance(query, dict):
        d = query
        query = d.get("query", "")
        limit = d.get("limit", limit)
        source = d.get("source", source)

    if not query:
        return json.dumps({"error": "query is required — specify what to search for"})

    max_results = min(int(limit) if limit else 5, 10)
    src = source if source else "web"

    logger.info("run_web_search: %s (limit=%d, source=%s)", query[:100], max_results, src)

    for attempt in range(3):
        try:
            key = get_key_with_fallback()
        except RuntimeError:
            return json.dumps({
                "query": query, "source": "error",
                "results_count": 0, "results": [],
                "error": "search unavailable — no API keys",
            })

        try:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.firecrawl.dev/v2/search",
                    headers={"Authorization": f"Bearer {key}"},
                    json={
                        "query": query,
                        "limit": max_results,
                        "sources": [src],
                    },
                )
                if response.status_code == 402:
                    err_text = response.text
                    reason = classify_exhaustion(err_text)
                    if reason:
                        mark_exhausted(key, reason)
                        logger.warning("Firecrawl 402 on web_search, rotating key (attempt %d)", attempt + 1)
                        continue

                response.raise_for_status()
                data = response.json()

                results = []
                items = data.get("data", [])
                if not isinstance(items, list):
                    items = []
                for r in items[:max_results]:
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "description": r.get("description", ""),
                        "markdown": (r.get("markdown", "") or "")[:8000],
                    })

                return json.dumps({
                    "query": query,
                    "source": src,
                    "results_count": len(results),
                    "results": results,
                }, ensure_ascii=False)

        except Exception as e:
            err = str(e)
            reason = classify_exhaustion(err)
            if reason:
                mark_exhausted(key, reason)
                logger.warning("Firecrawl credit exhausted on web_search, rotating (attempt %d)", attempt + 1)
                continue
            logger.warning("run_web_search failed (attempt %d): %s", attempt + 1, err[:200])
            if attempt == 2:
                return json.dumps({
                    "query": query, "source": "error",
                    "results_count": 0, "results": [],
                    "error": f"search failed: {err[:300]}",
                })

    return json.dumps({
        "query": query, "source": "error",
        "results_count": 0, "results": [],
        "error": "all Firecrawl keys exhausted",
    })


def _check():
    try:
        return active_count > 0 or bool(_FALLBACK_KEY)
    except Exception:
        return bool(_FALLBACK_KEY)


registry.register(
    name="run_web_search",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "run_web_search",
            "description": (
                "Search the web for information about any topic. "
                "Returns page titles, URLs, descriptions, and extracted content. "
                "Use this to research competitors, find clinic information, "
                "check market data, look up doctors, or find any information "
                "needed during a presale conversation. "
                "ALWAYS use this instead of guessing or making up information."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "[REQUIRED] Search query — be specific and use Russian where appropriate (e.g., 'клиника профессора Юцковской отзывы', 'косметология Москва рейтинг')",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of results (default: 5, max: 10)",
                    },
                    "source": {
                        "type": "string",
                        "enum": ["web", "news"],
                        "description": "Search source: 'web' for general search, 'news' for recent news (default: 'web')",
                    },
                },
                "required": ["query"],
            },
        },
    },
    handler=handle_run_web_search,
    check_fn=_check,
    is_async=True,
    description="Search the web via Firecrawl — find competitors, clinics, market data, any info",
    emoji="🔍",
)
