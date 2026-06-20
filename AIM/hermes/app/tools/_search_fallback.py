"""_search_fallback — Unified search with automatic provider fallback.

Providers (tried in order):
  1. Perplexity (sonar model, web search via LLM)
  2. Firecrawl (if keys are active)

All providers return the same format: list[dict] with {title, url, description}.

Usage:
    from app.tools._search_fallback import search
    results = await search("лазерная эпиляция Москва", max_results=5)
    # Returns list[dict], falls back through providers automatically
"""

from __future__ import annotations

import logging
import re
import time

from app.key_bank import key_bank

logger = logging.getLogger(__name__)

# Standard result format
# Each provider returns list[dict] with keys: title, url, description


async def _perplexity_search(query: str, max_results: int) -> list[dict]:
    """Perplexity web search — primary provider (uses PERPLEXITY_API_KEY).

    Для site-specific запросов (query содержит "site:") использует
    специальный промпт — явно просит Perplexity проверить конкретный сайт.
    """
    api_key = key_bank.get("PERPLEXITY_API_KEY")
    if not api_key:
        logger.info("_search_fallback: Perplexity — no API key, skipping")
        return []

    # ── Определяем, site-specific ли это запрос ─────────────────
    site_domain = ""
    search_topic = query
    site_match = re.search(r'\bsite:(\S+)', query)
    if site_match:
        site_domain = site_match.group(1).rstrip(".,;:!?)")
        search_topic = query[:site_match.start()].strip()
        if not search_topic:
            search_topic = query  # fallback

    import httpx
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if site_domain:
                system_prompt = (
                    f"You are checking whether the website {site_domain} has pages about "
                    f"a specific topic. Search ONLY {site_domain} — do NOT return results "
                    f"from other websites. For each relevant page on {site_domain} provide: "
                    f"1. Title 2. Full URL on {site_domain} 3. Brief description. "
                    f"If {site_domain} has NO relevant pages on this topic, "
                    f"say exactly: NO_PAGES_FOUND. Be thorough — check blog, services, "
                    f"articles, and news sections of {site_domain}."
                )
                user_message = (
                    f"Search {site_domain} for: {search_topic}. "
                    f"Return ONLY pages from {site_domain}. "
                    f"If nothing relevant found, say NO_PAGES_FOUND."
                )
            else:
                system_prompt = (
                    "You are a web search assistant. Search the web and return "
                    "results as a numbered list. For each result provide: "
                    "1. Title of the page 2. URL 3. One-sentence description. "
                    "Be concise. Return ONLY the list, no preamble."
                )
                user_message = f"Search: {query}"

            resp = await client.post(
                "https://api.perplexity.ai/chat/completions",
                json={
                    "model": "sonar",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    "max_tokens": 500,
                    "temperature": 0.1,
                },
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
            )

            if resp.status_code != 200:
                logger.warning("_search_fallback: Perplexity returned %d", resp.status_code)
                return []

            data = resp.json()
            # Extract citations (Perplexity's direct web references)
            citations = data.get("citations", [])
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

            # Perplexity может вернуть "NO_PAGES_FOUND" для site-specific запросов
            if "NO_PAGES_FOUND" in content.upper():
                logger.info(
                    "_search_fallback: Perplexity site-search — no pages found on %s for '%s'",
                    site_domain, search_topic[:40],
                )
                return []

            # Фильтруем citations по домену для site-specific запросов
            if site_domain:
                citations = [
                    url for url in citations
                    if site_domain.replace("www.", "") in url.replace("www.", "")
                ]

            results = []
            seen_urls = set()

            # First, use citations (most reliable — actual URLs Perplexity searched)
            for url in citations:
                if url not in seen_urls:
                    seen_urls.add(url)
                    # Try to find a matching title in the content
                    title = _extract_title_for_url(content, url)
                    description = _extract_snippet_for_url(content, url)
                    results.append({
                        "title": title or url.split("//")[-1].split("/")[0],
                        "url": url,
                        "description": description or "",
                    })

            # If not enough from citations, parse the numbered list from content
            if len(results) < max_results:
                parsed = _parse_numbered_results(content)
                for item in parsed:
                    if item["url"] not in seen_urls and len(results) < max_results:
                        seen_urls.add(item["url"])
                        results.append(item)

            if results:
                logger.info("_search_fallback: Perplexity returned %d results for '%s'",
                           len(results), query[:60])
                return results[:max_results]

            logger.info("_search_fallback: Perplexity 0 results for '%s'", query[:60])
            return []

    except Exception as e:
        logger.warning("_search_fallback: Perplexity error: %s", str(e)[:120])
        return []


def _extract_title_for_url(content: str, url: str) -> str:
    """Try to find a page title associated with a URL in Perplexity's response."""
    domain = url.split("//")[-1].split("/")[0].replace("www.", "")
    # Look for patterns like "Title (domain.com)" or "[Title](url)"
    for line in content.split("\n"):
        if domain in line or url.split("/")[-1] in line:
            # Extract text before the URL/domain
            cleaned = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', line)
            cleaned = re.sub(r'\([^)]*\)', '', cleaned)
            cleaned = cleaned.strip(" -•*#0123456789. ")
            if cleaned and len(cleaned) > 5:
                return cleaned[:200]
    return ""


def _extract_snippet_for_url(content: str, url: str) -> str:
    """Try to find a description snippet for a URL."""
    domain = url.split("//")[-1].split("/")[0].replace("www.", "")
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if domain in line or url.split("/")[-1] in line:
            # Look at the next line for a description
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip(" -•*#0123456789. ")
                if next_line and len(next_line) > 10:
                    return next_line[:300]
            # Or the current line after the URL
            after_url = line.split(url)[-1] if url in line else line.split(domain)[-1]
            after_url = after_url.strip(" -•:*#()[]")
            if after_url and len(after_url) > 10:
                return after_url[:300]
    return ""


def _parse_numbered_results(content: str) -> list[dict]:
    """Parse a numbered list of search results from Perplexity's response."""
    results = []
    # Pattern: "1. Title (url)" or "1. [Title](url)"
    lines = content.split("\n")
    current_title = None
    current_url = None

    for line in lines:
        # Try markdown link format: [Title](url)
        md_match = re.findall(r'\[([^\]]+)\]\((https?://[^)]+)\)', line)
        if md_match:
            for title, url in md_match:
                results.append({"title": title[:200], "url": url, "description": ""})
                continue

        # Try "Title - url" or "Title (url)" format
        url_match = re.search(r'(https?://[^\s\)]+)', line)
        if url_match:
            url = url_match.group(0).rstrip(".)")
            # Title is everything before the URL
            title_part = line[:url_match.start()].strip(" -•*#0123456789. ")
            if title_part and len(title_part) > 3:
                current_title = title_part[:200]
                current_url = url
                results.append({"title": current_title, "url": current_url, "description": ""})

    return results


async def _firecrawl_search(query: str, max_results: int) -> list[dict]:
    """Firecrawl search — tertiary provider (requires active keys)."""
    from app.tools.firecrawl_key_bank import classify_exhaustion

    api_key = key_bank.get_firecrawl_key()
    if not api_key:
        logger.info("_search_fallback: Firecrawl — no active keys, skipping")
        return []

    import httpx
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.firecrawl.dev/v1/search",
                json={"query": query, "limit": max_results},
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
            )

            if resp.status_code == 200:
                data = resp.json()
                items = data.get("data", data.get("results", []))
                results = []
                for item in items:
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "description": item.get("description", item.get("snippet", "")),
                    })
                logger.info("_search_fallback: Firecrawl returned %d results for '%s'", len(results), query[:60])
                return results

            if resp.status_code in (401, 402, 429):
                reason = classify_exhaustion(str(resp.status_code))
                key_bank.mark_firecrawl_exhausted(api_key)
                logger.warning("_search_fallback: Firecrawl key exhausted (%s)", reason)
                return []

            logger.warning("_search_fallback: Firecrawl returned %d", resp.status_code)
            return []
    except Exception as e:
        logger.warning("_search_fallback: Firecrawl error: %s", str(e)[:120])
        return []


# Provider chain — tried in order
# NOTE: DDG removed — blocked on server IP + _ddg module not implemented.
# Perplexity is primary (sonar model, web search via LLM).
# Firecrawl is backup (all 15 keys currently exhausted as of 2026-06-20).
_PROVIDERS = [
    ("perplexity", _perplexity_search),
    ("firecrawl", _firecrawl_search),
]


async def search(
    query: str,
    max_results: int = 5,
    providers: list[str] | None = None,
) -> tuple[list[dict], str]:
    """Search the web with automatic provider fallback.

    Tries each provider in order. Falls back to next if:
    - Provider returns 0 results
    - Provider raises an exception

    Args:
        query: Search query string.
        max_results: Max results (default 5, capped at 10).
        providers: Override provider list (e.g. ["ddg", "crawlee"]).

    Returns:
        (results: list[dict], provider_used: str)
        results format: [{title, url, description}]
        provider_used: name of the provider that returned results (or "none")
    """
    max_results = min(max_results, 10)

    chain = _PROVIDERS
    if providers:
        chain = [(p, fn) for p, fn in _PROVIDERS if p in providers]

    is_site_specific = bool(re.search(r'\bsite:\S+', query))

    for provider_name, provider_fn in chain:
        start = time.time()
        try:
            results = await provider_fn(query, max_results)
            elapsed = time.time() - start
            if results:
                logger.info(
                    "_search_fallback: [%s] ✓ %d results in %.1fs for '%s'",
                    provider_name, len(results), elapsed, query[:60],
                )
                return results, provider_name
            else:
                # Для site-specific запросов: пустой результат от Perplexity = валидный ответ
                # (NO_PAGES_FOUND — сайт не покрывает тему). НЕ фоллбэчимся на Firecrawl.
                if is_site_specific and provider_name == "perplexity":
                    logger.info(
                        "_search_fallback: [%s] site-search — 0 results for '%s' (valid: no pages on target site)",
                        provider_name, query[:60],
                    )
                    return [], provider_name
                logger.info(
                    "_search_fallback: [%s] ✗ 0 results in %.1fs, falling back…",
                    provider_name, elapsed,
                )
        except Exception as e:
            elapsed = time.time() - start
            logger.warning(
                "_search_fallback: [%s] ✗ error in %.1fs: %s",
                provider_name, elapsed, str(e)[:120],
            )
            continue

    logger.error("_search_fallback: ALL providers failed for '%s'", query[:60])
    return [], "none"


def active_providers() -> list[str]:
    """List providers that are likely available right now."""
    available = []

    # Perplexity — primary, always available if key is set
    if key_bank.get("PERPLEXITY_API_KEY"):
        available.append("perplexity")

    try:
        if key_bank.get_firecrawl_key() is not None:
            available.append("firecrawl")
    except Exception:
        pass

    return available
