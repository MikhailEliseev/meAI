"""
find_competitors — Hermes tool: Find Top Competitors

POST http://aim-app:8000/api/competitors/find
Extracts specialization & city from client website, searches Google Maps
via Apify for competitors, enriches with DaData + rusprofile financials,
scores by revenue/location/services/rating, returns top-5.

Pipeline: website extraction → Google Maps (RESIDENTIAL proxy) →
DaData enrichment → Playwright INN extraction → rusprofile financials → scoring

Registered in Hermes internal registry under toolset "aim-operations".
"""

import json
import logging

import httpx

from tools.registry import registry

logger = logging.getLogger(__name__)


def _normalize_args(first_param, defaults):
    if isinstance(first_param, dict):
        return {k: first_param.get(k, defaults.get(k)) for k in defaults}
    return None


AIM_API_BASE = "http://aim-app:8000"
REQUEST_TIMEOUT = 600.0  # full pipeline: Apify (90s) + 50-place Playwright INN extraction + nalog enrichment + scoring


async def _find_competitors_via_perplexity(url: str) -> list:
    """Fallback: найти топ-5 конкурентов через Perplexity (1 API call).

    Используется когда Apify/Google Maps вернули пустой результат.
    Возвращает структуру как main path, но с полями из Perplexity ответа.
    Стоимость: ~$0.005.
    """
    import json as _json
    import re as _re
    try:
        from app.tools.perplexity_tools import handle_perplexity_search
        question = (
            f'Для клиники с сайтом {url}: назови 5 её главных прямых конкурентов в той же специализации '
            f'и том же городе (только частные коммерческие клиники, НЕ государственные). '
            f'Формат ответа: строго 5 пунктов, каждый в одну строку: '
            f'"Бренд | сайт | специализация". Без ИНН и выручки — только идентификаторы. '
            f'Пример: "GMTClinic | gtmcinic.ru | пластическая хирургия".'
        )
        result_json = await handle_perplexity_search(question=question, context="")
        data = _json.loads(result_json)
        answer = data.get("answer", "") if isinstance(data, dict) else ""
        if not answer:
            return []

        # Парсим формат "Бренд | сайт | специализация"
        competitors = []
        for line in answer.split("\n"):
            line = line.strip()
            # Ищем нумерованные пункты: "1. ... | ... | ..."
            m = _re.match(r'^\d+[\.\)]\s*(.+)$', line)
            if not m:
                continue
            content = m.group(1)
            parts = [p.strip().lstrip('*') for p in content.split("|")]
            if len(parts) >= 2:
                brand = parts[0].strip().rstrip('.,;')[:80]
                website_part = parts[1].strip().rstrip('.,;')
                # Нормализуем сайт
                url_m = _re.search(r'(https?://[^\s)]+|[\w-]+\.\w{2,})', website_part)
                website = url_m.group(1) if url_m else ""
                if website and not website.startswith("http"):
                    website = "https://" + website
                spec = parts[2].strip() if len(parts) > 2 else ""
                if brand and brand.lower() not in ("бренд", "brand", "-"):
                    competitors.append({
                        "brand_name": brand,
                        "website": website,
                        "services": [spec] if spec else [],
                        "data_source": "perplexity",
                        "revenue_source": "perplexity",
                    })
            if len(competitors) >= 5:
                break

        return competitors[:5]
    except Exception as e:
        logger.warning("Perplexity competitors fallback failed: %s", e)
        return []


async def _enrich_competitor_with_financials(comp: dict, client_city: str = "") -> dict:
    """Для одного конкурента: найти INN через Perplexity + выручку через nalog.ru.

    Стоимость: ~1 Perplexity call + 1 nalog call (~$0.002).
    Возвращает comp с добавленными полями inn, revenue_year, profit_year, revenue_trend.
    """
    import json as _json
    import re as _re
    try:
        from app.tools.perplexity_tools import handle_perplexity_search

        brand = comp.get("brand_name", "")
        website = comp.get("website", "")
        if not brand and not website:
            return comp

        # 1. Получаем INN через Perplexity
        q = (
            f'Найди ИНН клиники "{brand}" (сайт {website}) — основное юрлицо, '
            f'медицинская деятельность (ОКВЭД 86.x). Верни только 10-значный ИНН и название юрлица.'
        )
        r = await handle_perplexity_search(question=q, context="")
        d = _json.loads(r)
        answer = d.get("answer", "") if isinstance(d, dict) else ""
        inn_match = _re.search(r'\b(\d{10})\b', answer)
        if not inn_match:
            return comp
        inn = inn_match.group(1)
        comp["inn"] = inn
        comp["inns"] = [inn]

        # 2. Получаем финансы через aim-app (nalog.ru)
        import httpx as _httpx
        async with _httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "http://aim-app:8000/api/companies/financials",
                params={"inn": inn},
            )
            if resp.status_code != 200:
                return comp
            data = resp.json()
            if not data.get("success"):
                return comp
            company = data.get("company", {})
            revenue = company.get("revenue", {})
            profit = company.get("profit", {})
            if revenue:
                latest_year = sorted(revenue.keys(), reverse=True)[0]
                comp["revenue_year"] = revenue[latest_year]
                comp["financial_year"] = int(latest_year)
                comp["revenue_source"] = "tax_filed"
                comp["data_source"] = "nalog"
                comp["legal_name"] = company.get("full_name") or company.get("short_name") or brand
                comp["revenue_trend"] = company.get("revenue_trend")
                comp["profit_year"] = profit.get(latest_year)
                logger.info(
                    "find_competitors: enriched %s (inn=%s) revenue=%s",
                    brand, inn, comp["revenue_year"]
                )
        return comp
    except Exception as e:
        logger.debug("enrich competitor %s failed: %s", comp.get("brand_name", "?"), e)
        return comp


async def handle_find_competitors(url=None, named_competitors=None, client_revenue=None, **kwargs) -> str:
    """Find top competitors for a clinic website.

    Extracts specialization and city from the client website, searches
    Google Maps via Apify for medical companies in the same city/specialization,
    enriches with DaData + rusprofile financial data, scores by revenue match,
    location proximity, service overlap, rating, and reviews.

    Args:
        url: Client clinic website URL (e.g., "https://clinic.ru")
        named_competitors: Optional list of competitor names or URLs
        client_revenue: Optional client annual revenue (RUB) for gap-scoring
                       — boosts competitors with +20-50% higher revenue

    Returns:
        JSON string with up to 5 competitors: inn, inns (multi-entity), licenses, revenue, services,
        rating, reviews_count, website, social_links, match scores
        (revenue_match, location_score, service_overlap, total_score),
        and human-readable match_reason for each.
    """
    defaults = {"url": "", "named_competitors": None, "client_revenue": None}
    unpacked = _normalize_args(url, defaults)
    if unpacked:
        url = unpacked["url"]
        named_competitors = unpacked.get("named_competitors")
        client_revenue = unpacked.get("client_revenue")

    if not url:
        return json.dumps({"error": "url is required"})
    # Auto-prepend https:// if URL has no protocol
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    logger.info("Finding competitors for URL: %s, named: %s", url, named_competitors)

    from app.main import push_tool_progress

    try:
        payload: dict = {"url": url, "count": 5}
        if named_competitors:
            payload["named_competitors"] = named_competitors
        if client_revenue:
            payload["client_revenue"] = client_revenue

        push_tool_progress("competitors", f"🔎 Извлекаю специализацию и город из {url}…")
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            push_tool_progress("competitors", "🗺️ Ищу конкурентов через Google Maps (Apify)…")
            response = await client.post(
                f"{AIM_API_BASE}/api/competitors/find",
                json=payload,
            )
            response.raise_for_status()
            push_tool_progress("competitors", "💰 Обогащаю финансовыми данными (rusprofile)…")
            data = response.json()

            if not data.get("success"):
                logger.warning("find_competitors returned error: %s", data.get("error"))
                return json.dumps({
                    "error": "Failed to find competitors",
                    "detail": data.get("error", "Unknown error"),
                })

            competitors = data.get("competitors", [])
            is_megalopolis = data.get("is_megalopolis", False)
            logger.info("Found %d competitors for URL: %s (megalopolis=%s)", len(competitors), url, is_megalopolis)

            # Fallback: если Google Maps не дал результатов — спросить Perplexity
            # (1 API call, ~$0.005). Возвращает 5 топ-конкурентов.
            if not competitors:
                push_tool_progress("competitors", "🔄 Google Maps пустой — спрашиваю Perplexity о топ-конкурентах…")
                perplexity_comps = await _find_competitors_via_perplexity(url)
                if perplexity_comps:
                    # Enrich каждого конкурента: INN + финансы через nalog.ru (~$0.01 за конкурента)
                    push_tool_progress("competitors", f"💰 Тяну финансы для {len(perplexity_comps)} конкурентов…")
                    import asyncio as _aio
                    enriched = await _aio.gather(
                        *[_enrich_competitor_with_financials(c) for c in perplexity_comps],
                        return_exceptions=False,
                    )
                    competitors = [c for c in enriched if c]
                    is_megalopolis = False  # сбрасываем suggestion
                    logger.info("Perplexity fallback found %d competitors (enriched)", len(competitors))
                    push_tool_progress("competitors", f"✅ {len(competitors)} конкурентов с финансами")

            push_tool_progress("competitors", f"✅ Найдено конкурентов: {len(competitors)}")

            # Compact for LLM consumption — keep key fields
            compact = []
            for i, c in enumerate(competitors, 1):
                compact.append({
                    "rank": i,
                    "inn": c.get("inn", ""),
                    "inns": c.get("inns", []),
                    "licenses": c.get("licenses", []),
                    "is_multi_entity": c.get("is_multi_entity", False),
                    "legal_name": c.get("legal_name", ""),
                    "brand_name": c.get("brand_name"),
                    "revenue_year": c.get("revenue_year"),
                    "profit_year": c.get("profit_year"),
                    "financial_year": c.get("financial_year"),
                    "revenue_trend": c.get("revenue_trend"),
                    "employee_count": c.get("employee_count"),
                    "revenue_source": c.get("revenue_source", "none"),
                    "data_source": c.get("data_source", "apify_google_maps"),
                    "services": c.get("services", []),
                    "total_score": c.get("total_score"),
                    "revenue_match": c.get("revenue_match"),
                    "location_score": c.get("location_score"),
                    "service_overlap": c.get("service_overlap"),
                    "match_reason": c.get("match_reason", ""),
                    "website": c.get("website"),
                    "rating": c.get("rating"),
                    "reviews_count": c.get("reviews_count"),
                    "legal_address": c.get("legal_address"),
                    "social_links": c.get("social_links", {}),
                })

            result: dict = {"competitors": compact}
            if is_megalopolis:
                result["is_megalopolis"] = True
                result["suggestion"] = (
                    "Это крупный город (Москва/СПб). Google Maps показывает много "
                    "конкурентов, но для точного позиционирования стоит уточнить "
                    "у клиента его прямых конкурентов. "
                    "Передай их имена в параметр named_competitors при следующем вызове."
                )

            # Example wow-comment integration (COMMENTED OUT - LLM generates via prompt)
            # To enable manual triggers if LLM needs help, uncomment and customize:
            # from app.main import push_wow_comment  # Lazy import avoids circular dependency
            # if len(compact) > 0:
            #     top_revenue = compact[0].get("revenue_year", 0)
            #     if top_revenue and top_revenue > 50_000_000:
            #         push_wow_comment(f"Найдено {len(compact)} сильных конкурентов, лидер с выручкой {top_revenue:,} ₽", "warning")

            return json.dumps(result, ensure_ascii=False, indent=2)

    except httpx.HTTPStatusError as e:
        logger.error("AIM API returned error for find_competitors: %s", e)
        return json.dumps({
            "error": "AIM API returned an error",
            "status": e.response.status_code,
            "detail": str(e),
        })
    except httpx.RequestError as e:
        logger.error("Cannot reach AIM API for find_competitors: %s", e)
        return json.dumps({
            "error": "Cannot reach AIM API",
            "detail": str(e),
        })
    except Exception as e:
        logger.exception("Unexpected error in find_competitors handler")
        return json.dumps({
            "error": "Unexpected error in tool handler",
            "detail": str(e),
        })


registry.register(
    name="find_competitors",
    toolset="aim-operations",
    schema={
            "name": "find_competitors",
            "description": (
                "Find top competitors for a client clinic website. "
                "Extracts specialization and city from the site, searches Google Maps "
                "via Apify for medical companies in the same area, enriches with "
                "DaData + rusprofile financial data, scores by revenue match, "
                "location proximity, service overlap, rating, and reviews. "
                "Optionally accepts named_competitors — competitor names or URLs "
                "to look up directly. "
                "Returns up to 5 competitors with match reasons for the client to review. "
                "⚠️ Takes ~120-180 seconds (full pipeline: Google Maps → INN extraction → nalog → scoring)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Client clinic website URL (e.g., 'https://clinic.ru')",
                    },
                    "named_competitors": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of competitor names or URLs to look up",
                    },
                    "client_revenue": {
                        "type": "integer",
                        "description": "Optional client annual revenue (RUB) for gap-scoring. "
                                       "Boosts competitors with +20-50% higher revenue — "
                                       "the sweet spot for growth potential. "
                                       "Get this from run_prescan → revenue_year.",
                    },
                },
                "required": ["url"],
            },
        },
    handler=handle_find_competitors,
    check_fn=lambda: True,
    is_async=True,
    description="Find top-5 competitors for a clinic via Google Maps + financial enrichment (120-180s)",
    emoji="🔎",
)
