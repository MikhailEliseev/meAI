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

    # P5: file cache check
    import hashlib
    cache_key = f"search_{hashlib.sha256((query + str(max_results)).encode()).hexdigest()[:24]}"
    try:
        from app.tools._file_cache import file_cache
        import json as _json
        cached = await file_cache.get(cache_key)
        if cached is not None:
            results = _json.loads(cached)
            logger.info("_search_fallback: Perplexity cache HIT %d results for '%s'", len(results), query[:60])
            return results
    except Exception:
        pass

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

            # Parse content using citation markers [N] (Perplexity's standard format)
            # Format: "- **Title** — description.[N]" where N is 1-based index into citations[]
            parsed_from_content = _parse_perplexity_content(content, citations)

            for item in parsed_from_content:
                if item["url"] not in seen_urls:
                    seen_urls.add(item["url"])
                    results.append(item)

            # If not enough from citation markers, try legacy parsing
            if len(results) < max_results:
                parsed = _parse_numbered_results(content)
                for item in parsed:
                    if item["url"] not in seen_urls and len(results) < max_results:
                        seen_urls.add(item["url"])
                        results.append(item)

            # Fallback 3: narrative format — Perplexity returned prose with
            # inline citation markers [N] instead of bullet list.
            # Extract sentences around each unique citation.
            if not results and citations:
                parsed = _parse_narrative_citations(content, citations)
                for item in parsed:
                    if item["url"] not in seen_urls and len(results) < max_results:
                        seen_urls.add(item["url"])
                        results.append(item)

            # Fallback 4: last resort — use citations directly with URL-derived titles
            if not results and citations:
                from urllib.parse import urlparse
                for url in citations[:max_results]:
                    if url not in seen_urls:
                        seen_urls.add(url)
                        parsed_url = urlparse(url)
                        domain = parsed_url.netloc.replace("www.", "")
                        path = parsed_url.path.strip("/")
                        # Try to extract meaningful title from content
                        title = _extract_title_for_url(content, url)
                        if not title:
                            title = f"{domain}/{path.split('/')[-1]}" if path else domain
                        results.append({
                            "title": title[:200],
                            "url": url,
                            "description": _extract_snippet_for_url(content, url),
                        })

            if results:
                logger.info("_search_fallback: Perplexity returned %d results for '%s'",
                           len(results), query[:60])
                # P5: save to file cache
                try:
                    import json as _json
                    from app.tools._file_cache import file_cache
                    await file_cache.set(cache_key, _json.dumps(results[:max_results]))
                except Exception:
                    pass
                return results[:max_results]

            logger.info("_search_fallback: Perplexity 0 results for '%s'", query[:60])
            # P5: cache empty results too (prevent repeat calls for sites with no content)
            try:
                import json as _json
                from app.tools._file_cache import file_cache
                await file_cache.set(cache_key, _json.dumps([]))
            except Exception:
                pass
            return []

    except Exception as e:
        logger.warning("_search_fallback: Perplexity error: %s", str(e)[:120])
        return []
    finally:
        # P5: cleanup expired cache entries to prevent directory growth
        try:
            from app.tools._file_cache import file_cache
            file_cache.cleanup_expired()
        except Exception:
            pass


def _parse_perplexity_content(content: str, citations: list[str]) -> list[dict]:
    """Parse Perplexity response using citation markers [N].

    Perplexity format:
      "- **Title** — description.[N]"
    where [N] is a 1-based index into the citations array.

    Returns list[dict] with {title, url, description}.
    """
    results = []
    if not citations:
        return results

    # Split content into lines and process each one
    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue

        # Find citation markers like [7], [3], [12] at end of line or within text
        cite_matches = list(re.finditer(r'\[(\d+)\]', line))
        if not cite_matches:
            continue

        # Use the last citation number in the line
        last_cite = cite_matches[-1]
        cite_num = int(last_cite.group(1))

        # Convert 1-based to 0-based index
        if cite_num < 1 or cite_num > len(citations):
            continue
        url = citations[cite_num - 1]

        # Remove the citation marker(s) from the line for clean text
        clean_line = re.sub(r'\s*\[\d+\]', '', line).strip()

        # Remove leading list markers: "- ", "• ", "* ", "1. ", "2. "
        clean_line = re.sub(r'^[-•*]\s*', '', clean_line)
        clean_line = re.sub(r'^\d+[\.\)]\s*', '', clean_line)

        # Extract title from **bold** markers
        title = ""
        bold_match = re.search(r'\*\*(.+?)\*\*', clean_line)
        if bold_match:
            title = bold_match.group(1).strip()
            # Description is everything after the bold part
            after_bold = clean_line[bold_match.end():].strip()
            # Remove leading " — " or " - " separator
            description = re.sub(r'^[—\-]\s*', '', after_bold).strip()
        else:
            # No bold — use the whole line as title (up to first separator)
            sep_match = re.search(r'\s*[—\-]\s*', clean_line)
            if sep_match:
                title = clean_line[:sep_match.start()].strip()
                description = clean_line[sep_match.end():].strip()
            else:
                title = clean_line
                description = ""

        # Clean up title: remove common artifacts
        title = title.strip(" -*•#0123456789. ")
        title = re.sub(r'\*+', '', title).strip()

        if title and len(title) > 3:
            results.append({
                "title": title[:200],
                "url": url,
                "description": description[:300] if description else "",
            })

    return results


def _parse_narrative_citations(content: str, citations: list[str]) -> list[dict]:
    """Parse narrative-format Perplexity response with inline citation markers.

    Format: "text...[N]...text...[M]..." where [N] are inline citation markers
    embedded in prose paragraphs (not bullet lists).

    Extracts the sentence or text segment around each unique citation marker
    and pairs it with the corresponding URL from the citations array.
    """
    results = []
    if not citations:
        return results

    seen_cites = set()
    for m in re.finditer(r'\[(\d+)\]', content):
        cite_num = int(m.group(1))
        if cite_num < 1 or cite_num > len(citations):
            continue
        if cite_num in seen_cites:
            continue
        seen_cites.add(cite_num)

        # Extract context around citation: look backwards and forwards
        # for sentence boundaries to get a meaningful snippet
        pos = m.start()
        sentence_start = max(0, pos - 250)
        text_before = content[sentence_start:pos]

        # Find last sentence boundary before citation
        for sep in ['. ', '! ', '? ', '.\n', '!\n', '?\n', ': ']:
            last_sep = text_before.rfind(sep)
            if last_sep > 30:
                sentence_start = sentence_start + last_sep + len(sep)
                break

        sentence_end = min(len(content), pos + 250)
        text_after = content[pos:sentence_end]
        for sep in ['. ', '! ', '? ', '\n']:
            next_sep = text_after.find(sep, 5)
            if next_sep > 30:
                sentence_end = pos + next_sep + 1
                break

        snippet = content[sentence_start:sentence_end].strip()
        # Remove citation markers and extra whitespace
        snippet = re.sub(r'\s*\[\d+\]', '', snippet)
        snippet = re.sub(r'\s+', ' ', snippet).strip()

        if snippet and len(snippet) > 10:
            results.append({
                "title": snippet[:200],
                "url": citations[cite_num - 1],
                "description": "",
            })

    return results


def _extract_title_for_url(content: str, url: str) -> str:
    """Try to find a page title associated with a URL in Perplexity's response."""
    domain = url.split("//")[-1].split("/")[0].replace("www.", "")

    # Strategy 1: Find the specific URL in the text and extract the preceding title.
    # Perplexity often returns: **Title** — https://url.com/... — Description
    # Or: **Title** (https://url.com/...) — Description
    url_escaped = re.escape(url)
    # Look for "**Title** — URL" or "Title — URL" pattern
    title_url_pattern = re.compile(
        r'\*{0,2}([^*\n]{5,200}?)\*{0,2}\s*[—\-]\s*' + url_escaped,
        re.IGNORECASE,
    )
    match = title_url_pattern.search(content)
    if match:
        title = match.group(1).strip(" -*•#0123456789. ")
        if len(title) > 5:
            return title[:200]

    # Strategy 2: Find a shorter segment around the URL (max 2 URLs in same line)
    for line in content.split("\n"):
        if url not in line and domain not in line:
            continue
        # If line is very long (>500 chars), it contains many results. Extract segment around URL.
        if len(line) > 500:
            url_pos = line.find(url)
            if url_pos < 0:
                url_pos = line.find(domain)
            if url_pos >= 0:
                # Look backwards for a title separator (—, **, •)
                segment_start = max(0, url_pos - 300)
                prefix = line[segment_start:url_pos]
                # Find the last title-like marker before URL
                for sep in [" — ", " - ", " • ", "  "]:
                    last_sep = prefix.rfind(sep)
                    if last_sep > 20:
                        candidate = prefix[last_sep + len(sep):].strip(" -*•#0123456789. ")
                        if 5 < len(candidate) < 200:
                            return candidate
                # Fallback: last **text** before URL
                bold_matches = list(re.finditer(r'\*\*(.+?)\*\*', prefix))
                if bold_matches:
                    candidate = bold_matches[-1].group(1).strip()
                    if len(candidate) > 3:
                        return candidate[:200]
        # Shorter line — use the whole thing
        cleaned = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', line)
        cleaned = re.sub(r'\([^)]*\)', '', cleaned)
        cleaned = cleaned.strip(" -•*#0123456789. ")
        if cleaned and len(cleaned) > 5 and len(cleaned) < 300:
            return cleaned[:200]
        # Strip markdown bold
        cleaned = re.sub(r'\*+', '', cleaned).strip()
        if cleaned and 5 < len(cleaned) < 300:
            return cleaned[:200]

    return ""


def _extract_snippet_for_url(content: str, url: str) -> str:
    """Try to find a description snippet for a URL."""
    domain = url.split("//")[-1].split("/")[0].replace("www.", "")
    url_escaped = re.escape(url)

    # Strategy 1: "URL — Description" or "URL — **Description**" pattern
    snippet_pattern = re.compile(
        url_escaped + r'\s*[—\-]\s*\*{0,2}([^*\n]{20,300}?)\*{0,2}(?:\s*[—\-]|\s*$)',
        re.IGNORECASE,
    )
    match = snippet_pattern.search(content)
    if match:
        desc = match.group(1).strip(" -*•#0123456789. ")
        if len(desc) > 10:
            return desc[:300]

    # Strategy 2: Look for text after URL in the same line
    for line in content.split("\n"):
        if url not in line and domain not in line:
            continue
        after_url = line.split(url)[-1] if url in line else ""
        if after_url:
            # Take text up to next URL or line end
            next_url = re.search(r'https?://', after_url)
            if next_url:
                after_url = after_url[:next_url.start()]
            after_url = after_url.strip(" -•:*#()[]↔→\n")
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
