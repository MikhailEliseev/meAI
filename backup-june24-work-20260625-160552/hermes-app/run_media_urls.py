"""
run_media_urls — Hermes tool: Targeted 5-СМИ URL Search (Phase 4 / DAT-02)

Per D-15: Multi-search по 5 конкретным СМИ через firecrawl_search:
Forbes, RBC, Vademecum, Kommersant, ТАСС.

Per D-16: Fallback на perplexity_search если firecrawl недоступен.

Per D-17: Возвращает простой список с гиперссылками (source, title, url, date).
Не карточки с лого (избыточно для MVP).

Per D-18: Если 0 упоминаний — честный блок «В СМИ не упоминалась»
(pr_needed=True flag для Strategy section).
"""

import asyncio
import json
import logging
import os
import re
import time

from tools.registry import registry

logger = logging.getLogger(__name__)

# ── Firecrawl (primary) ────────────────────────────────────────────
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "").strip()
USE_FIRECRAWL = bool(FIRECRAWL_API_KEY)

# ── Perplexity (fallback) ──────────────────────────────────────────
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "").strip()
PERPLEXITY_BASE_URL = "https://api.perplexity.ai"
PERPLEXITY_MODEL = "sonar-pro"
USE_PERPLEXITY = bool(PERPLEXITY_API_KEY)

# ── LLM fallback (last resort, no web search) ─────────────────────
LLM_BASE_URL = os.getenv("LLM_BASE_URL", os.getenv("OMNIROUTE_URL", "https://api.deepseek.com/v1"))
LLM_API_KEY = os.getenv("LLM_API_KEY", os.getenv("OMNIROUTE_AUTH", os.getenv("DEEPSEEK_API_KEY", "")))
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

REQUEST_TIMEOUT = 60.0
MAX_TOKENS = 4000

_cache: dict[str, tuple[float, str]] = {}
_CACHE_TTL = 600

# ── 5 target media per D-15 ────────────────────────────────────────
TARGET_MEDIA = [
    {"name": "Forbes", "domain": "forbes.ru"},
    {"name": "RBC", "domain": "rbc.ru"},
    {"name": "Vademecum", "domain": "vademec.ru"},
    {"name": "Kommersant", "domain": "kommersant.ru"},
    {"name": "ТАСС", "domain": "tass.ru"},
]

# URL pattern for extracting URLs from Perplexity text responses
_URL_PATTERN = re.compile(r'https?://[^\s<>"\)\]]+')


def _normalize_args(first_param, defaults):
    """Accept dict-style first arg (some LMs pass kwargs as dict)."""
    if isinstance(first_param, dict):
        return {k: first_param.get(k, defaults[k]) for k in defaults}
    return None


def _build_media_search_query(clinic_name: str, media_domain: str) -> str:
    """Build site-restricted query for one СМИ source.

    Per D-15: query like `"Clinic Name" site:forbes.ru` — restricts
    results to one specific outlet per call.
    """
    return f'"{clinic_name}" site:{media_domain}'


async def _firecrawl_search(query: str, limit: int = 5) -> list[dict]:
    """Call firecrawl via existing handle_firecrawl_search wrapper.

    Returns list of {title, url, description, date} dicts. Empty list
    on any failure — caller falls back to perplexity.
    """
    if not USE_FIRECRAWL:
        return []

    try:
        # Late import to avoid module-load circulars
        from app.tools.firecrawl_web import handle_firecrawl_search

        raw = await handle_firecrawl_search(query=query, limit=limit)
        data = json.loads(raw) if isinstance(raw, str) else raw

        if not data or data.get("results_count", 0) == 0:
            return []

        results = []
        for r in data.get("results", [])[:limit]:
            url = r.get("url", "")
            if not url:
                continue
            results.append({
                "title": r.get("title", "")[:200],
                "url": url,
                "description": (r.get("description", "") or "")[:300],
                "date": "",  # Firecrawl doesn't reliably return dates
            })
        return results
    except Exception as e:
        logger.warning("firecrawl_search failed for '%s': %s", query[:80], str(e)[:200])
        return []


async def _perplexity_search_fallback(query: str) -> list[dict]:
    """Use Perplexity sonar-pro for the same site-restricted query.

    Parses response text for URLs + surrounding context. Each result
    has {title, url, description, date}. Date extraction is best-effort.
    """
    if not USE_PERPLEXITY:
        return []

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=PERPLEXITY_API_KEY,
            base_url=PERPLEXITY_BASE_URL,
            timeout=REQUEST_TIMEOUT,
        )
        response = await client.chat.completions.create(
            model=PERPLEXITY_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты — исследователь СМИ-упоминаний. Найди конкретные "
                        "статьи где упоминается заданная клиника на заданном "
                        "СМИ-ресурсе. Возвращай только реальные статьи с "
                        "URLs, заголовками и датами публикации. Формат:\n"
                        "- {Заголовок статьи} | {URL} | {Дата}\n"
                        "Если статей нет — напиши «Не найдено»."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Запрос: {query}\n"
                        "Найди все статьи на этом ресурсе, где упоминается "
                        "указанная клиника. Верни список с URL и датами."
                    ),
                },
            ],
            temperature=0.1,
            max_tokens=MAX_TOKENS,
        )
        answer = response.choices[0].message.content or ""
        return _parse_perplexity_results(answer)
    except Exception as e:
        logger.warning("perplexity fallback failed for '%s': %s", query[:80], str(e)[:200])
        return []


def _parse_perplexity_results(answer: str) -> list[dict]:
    """Parse Perplexity text response into structured mentions.

    Looks for lines with URLs and extracts:
    - title (text before URL on same line, or first 80 chars before URL)
    - url (first http(s) URL on line)
    - date (regex DD.MM.YYYY or YYYY-MM-DD if present near URL)
    """
    if not answer or "Не найдено" in answer[:100]:
        return []

    date_re = re.compile(r'(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4}|\d{4}-\d{2}-\d{2})')
    results = []
    seen_urls = set()

    for line in answer.split("\n"):
        line = line.strip(" -*•\t")
        if not line or len(line) < 10:
            continue

        url_match = _URL_PATTERN.search(line)
        if not url_match:
            continue

        url = url_match.group(0).rstrip(".,;:)>")
        if url in seen_urls:
            continue
        seen_urls.add(url)

        # Title = text before URL on same line
        title = line[:url_match.start()].strip(" |—–-")
        if not title:
            title = "(без заголовка)"

        # Date search in full line
        date_match = date_re.search(line)
        date = date_match.group(1) if date_match else ""

        results.append({
            "title": title[:200],
            "url": url,
            "description": "",
            "date": date,
        })

    return results[:5]


async def _search_one_source(clinic_name: str, media: dict) -> tuple[dict, str]:
    """Run one СМИ search: firecrawl first, perplexity fallback.

    Returns (source_result_dict, provider_used).
    """
    query = _build_media_search_query(clinic_name, media["domain"])

    # Try firecrawl first
    if USE_FIRECRAWL:
        mentions = await _firecrawl_search(query, limit=5)
        if mentions:
            return (
                {
                    "source": media["name"],
                    "domain": media["domain"],
                    "mentions_found": len(mentions),
                    "mentions": mentions,
                },
                "firecrawl",
            )
        # Firecrawl returned nothing — fall through to perplexity

    # Fallback: perplexity
    if USE_PERPLEXITY:
        mentions = await _perplexity_search_fallback(query)
        if mentions:
            return (
                {
                    "source": media["name"],
                    "domain": media["domain"],
                    "mentions_found": len(mentions),
                    "mentions": mentions,
                },
                "perplexity",
            )

    # Both unavailable or both returned nothing
    return (
        {
            "source": media["name"],
            "domain": media["domain"],
            "mentions_found": 0,
            "mentions": [],
        },
        "none",
    )


async def handle_run_media_urls(url=None, company_name="", **kwargs) -> str:
    """Search 5 specific Russian media outlets for clinic mentions.

    Per D-15..18: runs 5 parallel site-restricted searches via firecrawl
    (perplexity fallback). Returns concrete URLs + titles + dates — not
    category counters. Honest «В СМИ не упоминалась» block when 0 hits
    (pr_needed=True flag for Strategy section).

    Args:
        url: Clinic website URL (used as fallback identifier).
        company_name: Clinic name (preferred).

    Returns:
        JSON: clinic, total_mentions, media_with_mentions, media_total=5,
        mentions_by_source (5 entries), all_mentions (flat list),
        source, searched_at, pr_needed.
    """
    unpacked = _normalize_args(url, {"url": ""})
    if unpacked:
        url = unpacked["url"]
        company_name = unpacked.get("company_name", company_name)

    cn = kwargs.get("company_name", "")
    if cn and not company_name:
        company_name = cn

    search_target = url or company_name or ""
    if not search_target:
        return json.dumps({"error": "URL or clinic name is required"}, ensure_ascii=False)

    # Derive clinic name from URL domain if needed
    if search_target.startswith("http") and not company_name:
        from urllib.parse import urlparse
        parsed = urlparse(search_target)
        company_name = parsed.netloc.replace("www.", "")

    clinic_name = company_name or search_target

    cache_key = f"media_urls_{clinic_name}"
    cached = _cache.get(cache_key)
    if cached is not None:
        cached_ts, cached_result = cached
        if time.time() - cached_ts < _CACHE_TTL:
            logger.info("Media URLs cache HIT for: %s", clinic_name)
            return cached_result
        del _cache[cache_key]

    logger.info(
        "Searching 5 СМИ (firecrawl=%s, perplexity=%s) for: %s",
        "available" if USE_FIRECRAWL else "unavailable",
        "available" if USE_PERPLEXITY else "unavailable",
        clinic_name,
    )

    try:
        from app.main import push_tool_progress

        push_tool_progress(
            "media_urls",
            f"📰 Ищу упоминания в 5 СМИ (Forbes, RBC, Vademecum, Kommersant, ТАСС) для {clinic_name}…",
        )

        # Run all 5 searches in parallel
        coros = [_search_one_source(clinic_name, media) for media in TARGET_MEDIA]
        results = await asyncio.gather(*coros, return_exceptions=True)

        mentions_by_source = []
        all_mentions = []
        providers_used: set[str] = set()

        for media, result in zip(TARGET_MEDIA, results):
            if isinstance(result, Exception):
                logger.warning("Media search failed for %s: %s", media["name"], result)
                mentions_by_source.append({
                    "source": media["name"],
                    "domain": media["domain"],
                    "mentions_found": 0,
                    "mentions": [],
                    "error": str(result)[:200],
                })
                continue

            source_dict, provider = result
            mentions_by_source.append(source_dict)
            providers_used.add(provider)
            for mention in source_dict["mentions"]:
                all_mentions.append({
                    "source": media["name"],
                    "domain": media["domain"],
                    **mention,
                })

        total_mentions = len(all_mentions)
        media_with_mentions = sum(1 for s in mentions_by_source if s["mentions_found"] > 0)

        # Determine composite source label
        non_none = providers_used - {"none"}
        if len(non_none) == 0:
            source = "none"
        elif non_none == {"firecrawl"}:
            source = "firecrawl"
        elif non_none == {"perplexity"}:
            source = "perplexity (fallback)"
        else:
            source = "mixed"

        push_tool_progress(
            "media_urls",
            f"✅ Найдено {total_mentions} упоминаний в {media_with_mentions}/5 СМИ",
        )

        result_json_obj = {
            "clinic": clinic_name,
            "total_mentions": total_mentions,
            "media_with_mentions": media_with_mentions,
            "media_total": len(TARGET_MEDIA),
            "mentions_by_source": mentions_by_source,
            "all_mentions": all_mentions,  # flat list for HTML rendering per D-17
            "source": source,
            "searched_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            # D-18: honest block flag — strategy section should set PR recommendation
            "pr_needed": total_mentions == 0,
        }

        result_json = json.dumps(result_json_obj, ensure_ascii=False, indent=2)
        _cache[cache_key] = (time.time(), result_json)
        return result_json

    except Exception as e:
        logger.exception("Media URLs search error for %s", clinic_name)
        return json.dumps({
            "error": "Media URLs search failed",
            "detail": str(e)[:500],
        }, ensure_ascii=False)


registry.register(
    name="run_media_urls",
    toolset="aim-operations",
    schema={
            "name": "run_media_urls",
            "description": (
                "Search 5 target media outlets (Forbes, RBC, Vademecum, Kommersant, "
                "ТАСС) for clinic mentions with concrete URLs and dates. Uses "
                "firecrawl_search with perplexity fallback. Returns simple list "
                "with hyperlinks per mention. Sets pr_needed=True when 0 mentions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Website URL or clinic name to search media mentions for",
                    },
                    "company_name": {
                        "type": "string",
                        "description": "Clinic name (preferred over URL)",
                    },
                },
                "required": ["url"],
            },
        },
    handler=handle_run_media_urls,
    check_fn=lambda: True,
    is_async=True,
    description="Targeted 5-СМИ search (Forbes, RBC, Vademecum, Kommersant, ТАСС) with URLs and dates",
    emoji="📰",
)
