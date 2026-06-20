"""_ddg — Async DuckDuckGo search utility.

Free, no API key required. Uses DDG's HTML endpoint (non-JS version)
which is designed for accessibility and less aggressively rate-limited.

Usage:
    from app.tools._ddg import ddg_search
    results = await ddg_search("клиника отзывы site:prodoctorov.ru", max_results=5)
    # Returns list[dict] with keys: title, url, description
"""

from __future__ import annotations

import logging
import re

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DDG_HTML_URL = "https://html.duckduckgo.com/html/"
REQUEST_TIMEOUT = 15.0

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
}


async def ddg_search(query: str, max_results: int = 5) -> list[dict]:
    """Search DuckDuckGo and return structured results.

    Args:
        query: Search query (supports site:, quotes, etc.)
        max_results: Max number of results (default 5, capped at 20)

    Returns:
        List of dicts: {title, url, description}
    """
    max_results = min(max_results, 20)

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.get(
                DDG_HTML_URL,
                params={"q": query},
                headers=_HEADERS,
            )

            if resp.status_code != 200:
                logger.warning("DDG search returned %d for query: %s", resp.status_code, query[:80])
                return []

            results = _parse_ddg_html(resp.text, max_results)
            return results

    except Exception as e:
        logger.warning("DDG search failed for query '%s': %s", query[:80], str(e)[:120])
        return []


def _parse_ddg_html(html: str, max_results: int) -> list[dict]:
    """Parse DuckDuckGo HTML results page."""
    soup = BeautifulSoup(html, "lxml")
    results = []

    for link in soup.select(".result"):
        if len(results) >= max_results:
            break

        title_el = link.select_one(".result__title a")
        snippet_el = link.select_one(".result__snippet")
        url_el = link.select_one(".result__url")

        if not title_el:
            continue

        title = title_el.get_text(strip=True)
        url = _extract_ddg_url(title_el.get("href", ""))
        description = snippet_el.get_text(strip=True) if snippet_el else ""

        if url and title:
            results.append({
                "title": title,
                "url": url,
                "description": description[:300],
            })

    return results


def _extract_ddg_url(href: str) -> str:
    """Extract real URL from DDG redirect URL."""
    # DDG uses //duckduckgo.com/l/?uddg=<encoded_url>&...
    if "uddg=" in href:
        import urllib.parse
        parsed = urllib.parse.urlparse(href)
        qs = urllib.parse.parse_qs(parsed.query)
        encoded = qs.get("uddg", [""])[0]
        if encoded:
            return urllib.parse.unquote(encoded)
    return href
