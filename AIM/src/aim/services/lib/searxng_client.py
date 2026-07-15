"""SearXNG meta-search client.

Queries a self-hosted SearXNG instance for web search results
across multiple engines (Google, Bing, DuckDuckGo, etc.).

Used by the v2 competitor discovery pipeline as a free, reliable
source of clinic rankings and market overview snippets.
"""

import logging
import os
from typing import Optional
from urllib.parse import quote_plus

import httpx

logger = logging.getLogger(__name__)

SEARXNG_URL = os.getenv("SEARXNG_URL", "http://aim-searxng:8080")
SEARXNG_TIMEOUT = 25.0


async def searxng_search(
    query: str,
    categories: str = "general",
    language: str = "ru",
    limit: int = 15,
) -> list[dict]:
    """Search via SearXNG and return structured results.

    Args:
        query: Search query string.
        categories: SearXNG category (general, news, images, etc.).
        language: Result language preference.
        limit: Maximum number of results to return.

    Returns:
        List of result dicts with keys: title, content, url, engine.
        Returns empty list on failure.
    """
    params = (
        f"?q={quote_plus(query)}"
        f"&format=json"
        f"&categories={categories}"
        f"&language={language}"
    )
    url = f"{SEARXNG_URL}/search{params}"

    try:
        async with httpx.AsyncClient(timeout=SEARXNG_TIMEOUT) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        results = data.get("results", [])[:limit]
        logger.debug("searxng_search: query=%s results=%d", query, len(results))
        return [
            {
                "title": r.get("title", ""),
                "content": r.get("content", "") or "",
                "url": r.get("url", ""),
                "engine": r.get("engine", ""),
            }
            for r in results
        ]
    except Exception as e:
        logger.warning("searxng_search failed: query=%s error=%s", query, e)
        return []
