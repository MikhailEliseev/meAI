"""Named competitor search — find competitors by fuzzy/misspelled names.

Two-stage approach:
  1. Apify category search → rapidfuzz match against results (fast, free)
  2. Web search fallback for low-confidence matches (reliable but slower)

Solves: client types "клиника Делете" → finds Delete clinic
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Optional

from rapidfuzz import fuzz

logger = logging.getLogger(__name__)

# Thresholds
_FUZZY_CONFIDENT = 90   # Score above this → confident match, no fallback needed
_FUZZY_MINIMUM = 65     # Score below this → not a match
_WEB_FALLBACK_NEEDED = 85  # Score below this → trigger web search

# Common words in clinic names that inflate fuzzy scores without adding signal
_COMMON_WORDS = {
    "клиника", "клиники", "клиник",
    "центр", "медицинский", "медицинской", "медицинская",
    "косметология", "косметологии", "косметологический", "косметологическая",
    "стоматология", "стоматологии", "стоматологическая",
    "санкт", "петербург", "спб", "москва",
    "лазерный", "лазерная", "лазерной",
    "эстетический", "эстетическая", "эстетической",
    "школа", "кабинет", "студия", "салон",
}

# Cyrillic → Latin transliteration map (common Russian keyboard swaps)
_CYR_TO_LAT = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
    'е': 'e', 'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i',
    'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
    'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
    'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch',
    'ш': 'sh', 'щ': 'sch', 'ъ': '', 'ы': 'y', 'ь': '',
    'э': 'e', 'ю': 'yu', 'я': 'ya',
}


def _transliterate(text: str) -> str:
    """Convert Cyrillic to Latin for cross-alphabet matching.

    "инскин" → "inskin", "делете" → "delete"
    """
    result = []
    for ch in text:
        result.append(_CYR_TO_LAT.get(ch, ch))
    return "".join(result)


@dataclass
class NamedCompetitorMatch:
    """Result of finding a named competitor."""
    query: str
    brand_name: str = ""
    legal_name: str = ""
    website: str = ""
    rating: float = 0.0
    reviews_count: int = 0
    address: str = ""
    fuzzy_score: float = 0.0
    found_via: str = "none"  # "fuzzy", "web_search", "none"


def find_by_fuzzy(
    query: str,
    profiles: list,
    threshold: int = _FUZZY_MINIMUM,
) -> Optional[NamedCompetitorMatch]:
    """Try to match a named competitor against Apify category search results.

    Uses multiple rapidfuzz scoring strategies with penalties for common words
    and requires at least 2 strategies to agree for high-confidence matches.
    """
    query_lower = query.lower().strip()

    # Build query variants: original + transliterated (инскин → inskin)
    query_variants = {query_lower}
    query_trans = _transliterate(query_lower)
    if query_trans != query_lower:
        query_variants.add(query_trans)

    best_score = 0.0
    best_idx = -1

    # Calculate common-words penalty (on original query only)
    query_words = [w for w in query_lower.split() if len(w) >= 2]
    unique_words = [w for w in query_words if w not in _COMMON_WORDS]
    common_count = sum(1 for w in query_words if w in _COMMON_WORDS)

    if unique_words:
        common_penalty = (common_count / len(query_words)) * 10
    else:
        common_penalty = (common_count / max(len(query_words), 1)) * 15

    for i, profile in enumerate(profiles):
        brand = (profile.brand_name or "").lower()
        legal = (profile.legal_name or "").lower()

        # Build candidate variants: original + transliterated (inskin → инскин)
        candidate_variants = set()
        if brand:
            candidate_variants.add(brand)
            brand_trans = _transliterate(brand)
            if brand_trans != brand:
                candidate_variants.add(brand_trans)
        if legal and legal != brand:
            candidate_variants.add(legal)
            legal_trans = _transliterate(legal)
            if legal_trans != legal:
                candidate_variants.add(legal_trans)

        if not candidate_variants:
            continue

        # Try all combinations of query × candidate variants, take best
        best_pair_score = 0.0
        for qv in query_variants:
            for cv in candidate_variants:
                scores = {
                    "ratio": fuzz.ratio(qv, cv),
                    "partial": fuzz.partial_ratio(qv, cv),
                    "token_sort": fuzz.token_sort_ratio(qv, cv),
                    "WRatio": fuzz.WRatio(qv, cv),
                }
                adjusted = {k: max(0, v - common_penalty) for k, v in scores.items()}
                best_strategy = max(adjusted.values())

                strategies_above = sum(1 for v in adjusted.values() if v >= threshold)
                consensus_bonus = 5 if strategies_above >= 3 else (0 if strategies_above >= 2 else -10)

                pair_score = best_strategy + consensus_bonus
                pair_score = max(0, min(100, pair_score))

                if pair_score > best_pair_score:
                    best_pair_score = pair_score

        if best_pair_score > best_score:
            best_score = best_pair_score
            best_idx = i

    if best_idx >= 0 and best_score >= threshold:
        p = profiles[best_idx]
        return NamedCompetitorMatch(
            query=query,
            brand_name=p.brand_name or "",
            legal_name=p.legal_name or "",
            website=p.website or "",
            rating=p.rating or 0,
            reviews_count=p.reviews_count or 0,
            address=p.legal_address or "",
            fuzzy_score=round(best_score, 1),
            found_via="fuzzy",
        )

    return None


def build_web_search_query(query: str, city: str = "", specialization: str = "") -> str:
    """Build a web search query to find a named competitor's website."""
    parts = [query]
    if city:
        parts.append(city)
    if specialization:
        parts.append(specialization)
    parts.append("сайт клиника")
    return " ".join(parts)


def parse_web_search_result(search_text: str, original_query: str = "") -> Optional[NamedCompetitorMatch]:
    """Parse web search result text to extract competitor info.

    Extracts: website URL, brand name, legal name, INN, address.
    """
    website = extract_website_from_search_results(search_text)

    if not website:
        return None

    # Try to extract INN
    inn_match = re.search(r'ИНН[:\s]*(\d{10,12})', search_text)
    inn = inn_match.group(1) if inn_match else ""

    # Try to extract brand name (usually in bold or header-like text)
    brand_name = ""
    # Look for patterns like "**Brand Name**" or "## Brand Name"
    brand_patterns = [
        r'\*\*(.+?)\*\*',           # **Brand Name**
        r'##\s+(.+?)(?:\n|$)',      # ## Brand Name
        r'«(.+?)»',                  # «Brand Name»
    ]
    for pattern in brand_patterns:
        m = re.search(pattern, search_text)
        if m:
            candidate = m.group(1).strip()
            # Filter out non-brand matches
            if len(candidate) >= 3 and not any(skip in candidate.lower()
                for skip in ('результаты', 'поиск', 'примечание', 'поиска')):
                brand_name = candidate
                break

    return NamedCompetitorMatch(
        query=original_query,
        brand_name=brand_name,
        website=website,
        found_via="web_search",
    )


async def search_web_for_competitor(
    query: str,
    city: str = "",
    specialization: str = "",
) -> Optional[NamedCompetitorMatch]:
    """Search the web for a competitor's website using DuckDuckGo.

    Uses the duckduckgo_search library which handles anti-bot protection.
    Free, no API key required.
    """
    search_query = build_web_search_query(query, city, specialization)
    logger.info("Web search: %s", search_query)

    try:
        # Run synchronous DDGS in a thread — it's an I/O-bound HTTP call
        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(None, _ddg_text_search, search_query)

        if not results:
            logger.info("Web search: no results for '%s'", query)
            return None

        # Build search text from results: URLs + titles + bodies
        parts: list[str] = []
        for r in results[:10]:
            href = r.get("href", "")
            if href:
                parts.append(href)
            title = r.get("title", "")
            if title:
                parts.append(title)
            body = r.get("body", "")
            if body:
                parts.append(body)

        search_text = "\n".join(parts)
        return parse_web_search_result(search_text, original_query=query)

    except Exception as e:
        logger.warning("Web search failed for '%s': %s", query, e)
        return None


def _ddg_text_search(query: str) -> list[dict]:
    """Synchronous DuckDuckGo text search (runs in thread pool)."""
    try:
        from ddgs import DDGS

        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=10))
    except ImportError:
        logger.warning("ddgs not installed — web search unavailable")
        return []
    except Exception:
        logger.debug("DDG search error", exc_info=True)
        return []


# Backward-compatible alias
find_by_web_search = search_web_for_competitor


async def find_named_competitors(
    queries: list[str],
    category_profiles: list,
    city: str = "",
    specialization: str = "",
    web_search_callback=None,
) -> list[NamedCompetitorMatch]:
    """Find named competitors with fuzzy match + optional web search fallback.

    Args:
        queries: what the client typed (e.g. ["клиника Делете", "инскин"])
        category_profiles: CompanyProfile list from Apify category search
        city: city name for web search context
        specialization: e.g. "косметология"
        web_search_callback: async callable(query, city, spec) -> Optional[NamedCompetitorMatch]
    """
    results: list[NamedCompetitorMatch] = []

    for query in queries:
        # Stage 1: fuzzy match against category results
        match = find_by_fuzzy(query, category_profiles)

        if match and match.fuzzy_score >= _FUZZY_CONFIDENT:
            # Confident match — no fallback needed
            results.append(match)
            continue

        # Stage 2: web search fallback for low-confidence matches
        if web_search_callback and (not match or match.fuzzy_score < _WEB_FALLBACK_NEEDED):
            try:
                web_result = await web_search_callback(query, city, specialization)
                if web_result and web_result.website:
                    if match:
                        # Merge: prefer web result's website if fuzzy found wrong one
                        match.website = web_result.website
                        match.brand_name = web_result.brand_name or match.brand_name
                        match.found_via = "fuzzy+web"
                    else:
                        web_result.found_via = "web_search"
                        match = web_result
            except Exception as e:
                logger.warning("Web fallback failed for '%s': %s", query, e)

        if match:
            results.append(match)
        else:
            results.append(NamedCompetitorMatch(query=query, found_via="none"))

    return results


def rank_matches(matches: list[NamedCompetitorMatch]) -> list[NamedCompetitorMatch]:
    """Sort matches: found (best first) → not found (at bottom)."""
    found = [m for m in matches if m.found_via != "none"]
    not_found = [m for m in matches if m.found_via == "none"]
    found.sort(key=lambda m: m.fuzzy_score, reverse=True)
    return found + not_found


# ── Utils ──────────────────────────────────────────────────────────

def extract_website_from_search_results(search_text: str) -> Optional[str]:
    """Extract the most likely clinic website from web search results text.

    Favors early results that aren't aggregators/directories.
    Uses result order as the primary signal — the first non-aggregator URL wins.
    """
    url_pattern = re.compile(r'https?://[^\s<>"]+')
    urls = url_pattern.findall(search_text)

    # Known aggregator/directory domains — never the clinic's own website
    _aggregator_domains = [
        'google.com', 'yandex.ru', 'yandex.com',
        '2gis.ru', '2gis.com',
        'zoon.ru', 'zoon.com',
        'prodoctorov.ru', 'prodoctorov.com',
        'napopravku.ru',
        'otzovik.ru', 'otzovik.com',
        'irecommend.ru',
        'vk.com', 'vk.ru',
        'yell.ru',
        'docdoc.ru', 'docdoc.com',
        'beautynailhairsalons.com',
        'kleos.ru',
        'cynoclub.ru',
        'вполиклинике.рф',
        'spb.napopravku.ru',
    ]

    for url in urls:
        url_lower = url.lower()
        # Skip aggregators
        if any(domain in url_lower for domain in _aggregator_domains):
            continue
        # Skip deep pages (more than 3 path segments)
        if url.count('/') > 3:
            continue
        # First non-aggregator, short URL wins
        return url

    return None
