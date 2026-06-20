"""
run_web_search — Hermes tool: web search via DuckDuckGo (free, no keys).

Searches the web and returns results with titles, URLs, and descriptions.
Registered in toolset "aim-operations" so it's available in PRESALE mode.

Primary: DuckDuckGo HTML search (бесплатный, без API-ключа).
"""
from __future__ import annotations

import json
import logging

from tools.registry import registry

logger = logging.getLogger(__name__)


async def handle_run_web_search(query=None, limit=None, source=None, **kwargs) -> str:
    """Search the web via DuckDuckGo.

    Args:
        query: Search query string
        limit: Max results (default: 5, max: 10)
        source: 'web' (default) only — DDG doesn't separate news/images

    Returns:
        JSON string with search results including title, URL, description.
    """
    if isinstance(query, dict):
        d = query
        query = d.get("query", "")
        limit = d.get("limit", limit)
        source = d.get("source", source)

    if not query:
        return json.dumps({"error": "query is required — specify what to search for"})

    max_results = min(int(limit) if limit else 5, 10)

    logger.info("run_web_search: %s (limit=%d)", query[:100], max_results)

    from app.tools._search_fallback import search

    results, provider = await search(query, max_results=max_results)

    return json.dumps({
        "query": query,
        "source": provider,
        "results_count": len(results),
        "results": results,
    }, ensure_ascii=False)


def _check():
    return True  # DDG always available — no API key required


registry.register(
    name="run_web_search",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "run_web_search",
            "description": (
                "Search the web for information about any topic. "
                "Returns page titles, URLs, and descriptions. "
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
                        "description": "[REQUIRED] Search query — be specific and use Russian where appropriate",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of results (default: 5, max: 10)",
                    },
                    "source": {
                        "type": "string",
                        "enum": ["web"],
                        "description": "Search source (default: 'web')",
                    },
                },
                "required": ["query"],
            },
        },
    },
    handler=handle_run_web_search,
    check_fn=_check,
    is_async=True,
    description="Search the web via DuckDuckGo — find competitors, clinics, market data, any info",
    emoji="🔍",
)
