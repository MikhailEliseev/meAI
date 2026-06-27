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
import re
import time

from app.key_bank import key_bank
from tools.registry import registry

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 30.0

_cache: dict[str, tuple[float, str]] = {}
_CACHE_TTL = 600

# Темы по умолчанию (медицинская косметология) — используются если нет specialization
DEFAULT_CONTENT_TOPICS = [
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


async def _get_content_topics(specialization: str = "") -> list[str]:
    """Получить список релевантных контент-тем для специализации.

    Если specialization передан — генерирует 10 тем через Perplexity (cached).
    Иначе возвращает DEFAULT_CONTENT_TOPICS.
    """
    if not specialization:
        return DEFAULT_CONTENT_TOPICS

    import hashlib
    cache_key = f"topics_{hashlib.sha256(specialization.encode()).hexdigest()[:16]}"
    try:
        from app.tools._file_cache import file_cache
        cached = await file_cache.get(cache_key)
        if cached is not None:
            topics = json.loads(cached)
            logger.info("Content topics cache HIT for: %s (%d topics)", specialization, len(topics))
            return topics
    except Exception:
        pass

    import httpx
    api_key = key_bank.get("PERPLEXITY_API_KEY")
    if not api_key:
        logger.info("No Perplexity key for topic generation, using defaults")
        return DEFAULT_CONTENT_TOPICS

    prompt = (
        f"Ты — эксперт по медицинскому маркетингу. Перечисли 10 самых востребованных "
        f"тем/услуг для контент-маркетинга в специализации «{specialization}».\n"
        "Это должны быть темы, которые реально ищут пациенты и по которым клиники "
        "создают страницы на своих сайтах.\n"
        "Верни ТОЛЬКО список из 10 строк, каждая с новой строки. "
        "Никаких пояснений, только названия тем."
    )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.perplexity.ai/chat/completions",
                json={
                    "model": "sonar",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Ты — эксперт по медицинскому маркетингу. Называй только темы, ничего больше.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 300,
                    "temperature": 0.1,
                },
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
            )

            if resp.status_code == 200:
                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                topics = [line.strip(" -•*#0123456789. ") for line in content.split("\n") if line.strip()]
                topics = [t for t in topics if len(t) > 3][:10]
                if len(topics) >= 5:
                    logger.info("Generated %d content topics for specialization '%s'", len(topics), specialization)
                    try:
                        from app.tools._file_cache import file_cache
                        await file_cache.set(cache_key, json.dumps(topics))
                    except Exception:
                        pass
                    return topics
            else:
                logger.warning("Topic generation failed: %d", resp.status_code)
    except Exception as e:
        logger.warning("Topic generation error: %s", str(e)[:100])

    return DEFAULT_CONTENT_TOPICS


def _normalize_args(first_param, defaults):
    if isinstance(first_param, dict):
        return {k: first_param.get(k, defaults[k]) for k in defaults}
    return None


async def handle_run_content_gaps(url=None, client_site=None, competitor_site=None, **kwargs) -> str:
    """Analyze content gaps between client and competitors using Perplexity.

    Searches for content topics on client site vs competitor site,
    identifies gaps where competitor has content and client doesn't.

    Args:
        url: Website URL to analyze content gaps for.
        client_site: Client website URL (alternative to url).
        competitor_site: Competitor website URL for comparison.
        specialization: Clinic specialization for topic generation (from kwargs).
        company_name: Clinic name (from kwargs).

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

    specialization = kwargs.get("specialization", "")
    if unpacked and not specialization:
        specialization = unpacked.get("specialization", "")

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

        push_tool_progress("gaps", f"🔍 Ищу контентные пробелы для {target}…")

        from urllib.parse import urlparse
        client_domain = urlparse(target).netloc.replace("www.", "")
        comp_domain = ""
        if competitor_site:
            if not competitor_site.startswith("http"):
                competitor_site = "https://" + competitor_site
            comp_domain = urlparse(competitor_site).netloc.replace("www.", "")

        providers_used: set[str] = set()

        async def _search_all_topics_batch(
            topics: list[str], domain: str, label: str
        ) -> dict[str, list[dict]]:
            """P4 optimization: search ALL topics on ONE domain in a SINGLE Perplexity call.

            Returns {topic: [results]} mapping.
            """
            if not topics or not domain:
                return {}

            # P5: file cache check
            import hashlib
            topics_hash = hashlib.sha256(",".join(sorted(topics)).encode()).hexdigest()[:16]
            cache_key = f"gaps_batch_{domain}_{topics_hash}"
            try:
                from app.tools._file_cache import file_cache
                cached = await file_cache.get(cache_key)
                if cached is not None:
                    results = json.loads(cached)
                    logger.info("run_content_gaps: cache HIT for %s (%d topics found)", domain, len(results))
                    return results
            except Exception:
                pass

            topic_list = "\n".join(f"- {t}" for t in topics)
            prompt = (
                f"Проверь, есть ли на сайте {domain} страницы по следующим темам:\n\n"
                f"{topic_list}\n\n"
                f"Для КАЖДОЙ темы из списка выше ответь СТРОГО в формате:\n"
                f"ТЕМА: название | ЕСТЬ: url страницы на {domain} | или ТЕМА: название | НЕТ\n"
                f"Если страниц несколько — укажи самую релевантную.\n"
                f"Проверь ВСЕ темы из списка. Не пропускай ни одну."
            )

            import httpx
            api_key = key_bank.get("PERPLEXITY_API_KEY")
            if not api_key:
                logger.info("run_content_gaps batch: no Perplexity key, falling back to individual")
                return {}

            try:
                async with httpx.AsyncClient(timeout=45.0) as client:
                    resp = await client.post(
                        "https://api.perplexity.ai/chat/completions",
                        json={
                            "model": "sonar",
                            "messages": [
                                {
                                    "role": "system",
                                    "content": (
                                        f"Ты проверяешь наличие страниц на сайте {domain}. "
                                        "Для КАЖДОЙ темы из списка проверь реальные URL на сайте. "
                                        "Отвечай строго в формате: ТЕМА: название | ЕСТЬ: url | или ТЕМА: название | НЕТ"
                                    ),
                                },
                                {"role": "user", "content": prompt},
                            ],
                            "max_tokens": 1200,
                            "temperature": 0.1,
                        },
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                        },
                    )

                    if resp.status_code != 200:
                        logger.warning("Batch site search failed: %d", resp.status_code)
                        return {}

                    data = resp.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    logger.info("Batch site search for %s: %d chars", domain, len(content))
            except Exception as e:
                logger.warning("Batch site search error for %s: %s", domain, str(e)[:120])
                return {}

            # Parse response: "ТЕМА: название | ЕСТЬ: url" or "ТЕМА: название | НЕТ"
            results: dict[str, list[dict]] = {}
            for line in content.split("\n"):
                line = line.strip()
                if not line or not line.upper().startswith("ТЕМА"):
                    continue

                # Extract topic and result
                topic_match = re.match(
                    r'ТЕМА:\s*(.+?)\s*\|\s*(ЕСТЬ|НЕТ)(?::\s*(.+))?',
                    line, re.IGNORECASE,
                )
                if topic_match:
                    topic = topic_match.group(1).strip().lower()
                    has_content = topic_match.group(2).upper() == "ЕСТЬ"
                    url = (topic_match.group(3) or "").strip() if has_content else ""

                    # Match topic to our canonical list
                    matched_topic = None
                    for ct in topics:
                        if ct.lower() in topic or topic in ct.lower():
                            matched_topic = ct
                            break
                    if not matched_topic:
                        matched_topic = topic

                    if has_content and url:
                        results[matched_topic] = [{
                            "title": matched_topic,
                            "url": url if url.startswith("http") else f"https://{domain}/{url.lstrip('/')}",
                            "description": f"Страница на {domain}",
                        }]
                    else:
                        results[matched_topic] = []

            # Fill in zeros for topics not found in response
            for topic in topics:
                if topic not in results:
                    results[topic] = []

            logger.info(
                "Batch site search %s: %d/%d topics found",
                label, sum(1 for v in results.values() if v), len(topics),
            )

            # P5: save to file cache
            try:
                from app.tools._file_cache import file_cache
                await file_cache.set(cache_key, json.dumps(results))
            except Exception:
                pass

            return results

        # Генерируем релевантные темы для специализации (или используем дефолтные)
        push_tool_progress("gaps", f"🎯 Генерирую темы для специализации «{specialization or 'косметология'}»…")
        content_topics = await _get_content_topics(specialization)

        # P4: 2 batch calls instead of 20 individual (one per domain)
        push_tool_progress("gaps", f"🔍 Batch-поиск: проверяю {len(content_topics)} тем на {client_domain}…")
        client_topic_results = await _search_all_topics_batch(
            content_topics, client_domain, "client"
        )
        providers_used.add("perplexity")

        comp_topic_results: dict[str, list[dict]] = {}
        if comp_domain:
            push_tool_progress("gaps", f"🔍 Batch-поиск: проверяю {len(content_topics)} тем на {comp_domain}…")
            comp_topic_results = await _search_all_topics_batch(
                content_topics, comp_domain, "competitor"
            )
            providers_used.add("perplexity")

        topic_results: dict[str, dict] = {}
        uncovered_topics: list[str] = []
        covered_topics: list[str] = []

        for topic in content_topics:
            client_has = len(client_topic_results.get(topic, [])) > 0
            comp_has = len(comp_topic_results.get(topic, [])) > 0 if comp_domain else False
            comp_links = [
                {"title": r.get("title", ""), "url": r.get("url", "")}
                for r in comp_topic_results.get(topic, [])
            ] if comp_domain else []

            topic_results[topic] = {
                "client_has_content": client_has,
                "competitor_has_content": comp_has,
                "competitor_links": comp_links[:3],
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
            "specialization": specialization or "косметология (default)",
            "topics_analyzed": len(content_topics),
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

        # P5: periodic cache cleanup
        try:
            from app.tools._file_cache import file_cache
            file_cache.cleanup_expired()
        except Exception:
            pass

        return result_json

    except Exception as e:
        logger.exception("Content gaps error")
        return json.dumps({"error": "Unexpected error", "detail": str(e)})


registry.register(
    name="run_content_gaps",
    toolset="aim-operations",
    schema={
            "name": "run_content_gaps",
            "description": "Analyze content gaps vs competitors: generates topics dynamically based on specialization, then checks what competitors cover that client doesn't.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Website URL to analyze content gaps for"},
                    "specialization": {"type": "string", "description": "Clinic specialization for topic generation (e.g., косметология, стоматология)"},
                },
                "required": ["url"],
            },
        },
    handler=handle_run_content_gaps,
    check_fn=lambda: True,
    is_async=True,
    description="Analyze content gaps vs competitors — gaps, advantages, steal-worthy tactics",
    emoji="🔍",
)
