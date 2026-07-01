"""
run_content_gaps — Hermes tool: Content Gap Analysis

Сравнивает контент сайта клиники с конкурентами через DuckDuckGo:
- Темы, которые конкуренты покрывают, а клиент — нет
- Контентные преимущества клиента
- Steal-worthy tactics (тактики конкурентов, которые стоит перенять)
"""

import asyncio
import json
import logging
import time

from tools.registry import registry

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 30.0

_cache: dict[str, tuple[float, str]] = {}
_CACHE_TTL = 600

# Темы для контент-анализа (медицинская косметология)
CONTENT_TOPICS = [
    "лазерная эпиляция",
    "контурная пластика",
    "ботулинотерапия",
    "биоревитализация",
    "липоскульптурирование",
    "пилинг",
    "фотоомоложение",
    "SMAS-лифтинг",
    "лечение акне",
    "удаление сосудов",
]


def _normalize_args(first_param, defaults):
    if isinstance(first_param, dict):
        return {k: first_param.get(k, defaults[k]) for k in defaults}
    return None


async def handle_run_content_gaps(url=None, client_site=None, competitor_site=None, **kwargs) -> str:
    """Analyze content gaps between client and competitors using DuckDuckGo.

    Searches for content topics on client site vs competitor site,
    identifies gaps where competitor has content and client doesn't.

    Args:
        url: Website URL to analyze content gaps for.
        client_site: Client website URL (alternative to url).
        competitor_site: Competitor website URL for comparison.

    Returns:
        JSON with gaps, advantages, steal-worthy tactics.
    """
    unpacked = _normalize_args(url, {"url": ""})
    if unpacked:
        url = unpacked["url"]
        client_site = unpacked.get("client_site", client_site)
        competitor_site = unpacked.get("competitor_site", competitor_site)

    cs = kwargs.get("client_site", "")
    if cs and not client_site:
        client_site = cs
    comp = kwargs.get("competitor_site", "")
    if comp and not competitor_site:
        competitor_site = comp

    target = url or client_site or ""
    if target and not target.startswith(("http://", "https://")):
        target = "https://" + target

    if not target:
        return json.dumps({"error": "URL is required"})

    cache_key = f"gaps_{target}_{competitor_site or 'nocomp'}"
    cached = _cache.get(cache_key)
    if cached is not None:
        cached_ts, cached_result = cached
        if time.time() - cached_ts < _CACHE_TTL:
            return cached_result
        del _cache[cache_key]

    logger.info("Analyzing content gaps for: %s (competitor=%s)", target, competitor_site or "none")

    try:
        from app.main import push_tool_progress
        from app.tools._search_fallback import search as fallback_search

        push_tool_progress("gaps", f"🔍 Ищу контентные пробелы для {target}…")

        from urllib.parse import urlparse
        client_domain = urlparse(target).netloc.replace("www.", "")
        comp_domain = ""
        if competitor_site:
            if not competitor_site.startswith("http"):
                competitor_site = "https://" + competitor_site
            comp_domain = urlparse(competitor_site).netloc.replace("www.", "")

        providers_used: set[str] = set()

        def _url_matches_domain(url: str, domain: str) -> bool:
            """Проверяет, принадлежит ли URL указанному домену."""
            if not url or not domain:
                return False
            try:
                from urllib.parse import urlparse as _up
                parsed = _up(url)
                url_domain = parsed.netloc.replace("www.", "").lower()
                target = domain.replace("www.", "").lower()
                return url_domain == target or url_domain.endswith("." + target)
            except Exception:
                return False

        def _filter_by_domain(results: list[dict], domain: str) -> list[dict]:
            """Оставляет только результаты, URL которых принадлежат указанному домену."""
            return [r for r in results if _url_matches_domain(r.get("url", ""), domain)]

        async def _search_topic(topic: str) -> tuple[str, list[dict], list[dict]]:
            """Поиск темы на сайте клиента и конкурента параллельно."""
            client_query = f"{topic} site:{client_domain}"
            if comp_domain:
                comp_query = f"{topic} site:{comp_domain}"
                client_task = fallback_search(client_query, max_results=5)
                comp_task = fallback_search(comp_query, max_results=5)
                (client_results, cl_provider), (comp_results, cp_provider) = await asyncio.gather(
                    client_task, comp_task
                )
                providers_used.add(cl_provider)
                providers_used.add(cp_provider)
                # Пост-фильтр: только URL с целевого домена
                # Perplexity не понимает site:, возвращает общие результаты → фильтруем
                client_results = _filter_by_domain(client_results, client_domain)
                comp_results = _filter_by_domain(comp_results, comp_domain)
            else:
                client_results, cl_provider = await fallback_search(client_query, max_results=5)
                providers_used.add(cl_provider)
                client_results = _filter_by_domain(client_results, client_domain)
                comp_results = []
            return topic, client_results, comp_results

        # Все 10 топиков параллельно — общее время ~15s вместо 300s
        tasks = [_search_topic(topic) for topic in CONTENT_TOPICS]
        all_results = await asyncio.gather(*tasks, return_exceptions=True)

        topic_results: dict[str, dict] = {}
        uncovered_topics: list[str] = []
        covered_topics: list[str] = []

        for result in all_results:
            if isinstance(result, Exception):
                logger.warning("Topic search failed: %s", result)
                continue

            topic, client_results, comp_results = result

            client_has = len(client_results) > 0

            comp_has = False
            comp_links: list[dict] = []
            if comp_domain:
                comp_has = len(comp_results) > 0
                comp_links = [
                    {"title": r.get("title", ""), "url": r.get("url", "")}
                    for r in comp_results
                ]

            topic_results[topic] = {
                "client_has_content": client_has,
                "competitor_has_content": comp_has,
                "competitor_links": comp_links[:3] if comp_links else [],
            }

            if comp_has and not client_has:
                uncovered_topics.append(topic)
            elif client_has:
                covered_topics.append(topic)

        gaps = []
        for topic in uncovered_topics:
            info = topic_results[topic]
            gaps.append({
                "topic": topic,
                "gap_type": "competitor_covers_client_missing",
                "competitor_source": info["competitor_links"][0]["url"] if info["competitor_links"] else "",
            })

        advantages = []
        for topic in covered_topics:
            info = topic_results[topic]
            if not info["competitor_has_content"] and comp_domain:
                advantages.append({
                    "topic": topic,
                    "advantage_type": "client_only_topic",
                })

        result = {
            "target": target,
            "competitor": competitor_site or "none",
            "topics_analyzed": len(CONTENT_TOPICS),
            "topics_covered_by_client": len(covered_topics),
            "topics_uncovered": len(uncovered_topics),
            "content_gaps": gaps,
            "content_advantages": advantages,
            "topic_details": topic_results,
            "source": ", ".join(sorted(providers_used)) if providers_used else "none",
        }

        push_tool_progress("gaps", f"✅ Пробелов: {len(gaps)}, преимуществ: {len(advantages)}")
        result_json = json.dumps(result, ensure_ascii=False, indent=2)
        _cache[cache_key] = (time.time(), result_json)
        return result_json

    except Exception as e:
        logger.exception("Content gaps error")
        return json.dumps({"error": "Unexpected error", "detail": str(e)})


registry.register(
    name="run_content_gaps",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "run_content_gaps",
            "description": "Analyze content gaps vs competitors: what topics competitors cover but client doesn't. Returns gaps, advantages, and steal-worthy tactics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Website URL to analyze content gaps for"},
                },
                "required": ["url"],
            },
        },
    },
    handler=handle_run_content_gaps,
    check_fn=lambda: True,
    is_async=True,
    description="Analyze content gaps vs competitors — gaps, advantages, steal-worthy tactics",
    emoji="🔍",
)
