"""
run_web_search — Hermes tool: web search via Firecrawl + Brave Search fallback

Searches the web and returns results with page content.
Registered in toolset "aim-operations" so it's available in PRESALE mode.

Primary: Firecrawl /v2/search (with key rotation)
Fallback: Brave Search API (when all Firecrawl keys exhausted)
"""

import json
import logging
import os

from tools.registry import registry
from .firecrawl_key_bank import get_key_with_fallback, mark_exhausted, classify_exhaustion, active_count

logger = logging.getLogger(__name__)

_FALLBACK_KEY = os.environ.get("FIRECRAWL_API_KEY", "").strip()
_BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY", "").strip()


async def _search_via_brave(query: str, max_results: int, src: str) -> str:
    """Search via Brave Search API.

    https://api.search.brave.com/res/v1/web/search

    Returns results in the same JSON format as Firecrawl for compatibility.
    """
    import httpx

    brave_url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": _BRAVE_API_KEY,
    }
    params = {
        "q": query,
        "count": min(max_results, 20),
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(brave_url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()

    web_results = data.get("web", {}).get("results", [])
    results = []
    for r in web_results[:max_results]:
        results.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "description": r.get("description", ""),
            "markdown": "",  # Brave doesn't provide markdown
        })

    return json.dumps({
        "query": query,
        "source": f"brave_{src}",
        "results_count": len(results),
        "results": results,
    }, ensure_ascii=False)


async def handle_run_web_search(query=None, limit=None, source=None, **kwargs) -> str:
    """Search the web via Firecrawl (primary) or Brave Search (fallback).

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

    # ── Try Firecrawl keys first ──────────────────────────────────
    for attempt in range(3):
        try:
            key = get_key_with_fallback()
        except RuntimeError:
            # No keys at all — skip to Brave
            break

        if key is None:
            break

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
            logger.warning("run_web_search Firecrawl failed (attempt %d): %s", attempt + 1, err[:200])

    # ── Brave Search fallback ─────────────────────────────────────
    if _BRAVE_API_KEY:
        logger.info("Falling back to Brave Search for: %s", query[:100])
        try:
            return await _search_via_brave(query, max_results, src)
        except Exception as e:
            logger.warning("Brave Search also failed: %s", str(e)[:200])
            return json.dumps({
                "query": query, "source": "error",
                "results_count": 0, "results": [],
                "error": f"search failed — Firecrawl + Brave both unavailable: {str(e)[:300]}",
            })

    return json.dumps({
        "query": query, "source": "error",
        "results_count": 0, "results": [],
        "error": "all Firecrawl keys exhausted (no Brave API key)",
    })


def _check():
    try:
        return active_count() > 0 or bool(_BRAVE_API_KEY) or bool(_FALLBACK_KEY)
    except Exception:
        return bool(_BRAVE_API_KEY) or bool(_FALLBACK_KEY)


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
