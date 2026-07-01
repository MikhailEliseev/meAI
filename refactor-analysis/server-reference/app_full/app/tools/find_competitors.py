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
        "type": "function",
        "function": {
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
    },
    handler=handle_find_competitors,
    check_fn=lambda: True,
    is_async=True,
    description="Find top-5 competitors for a clinic via Google Maps + financial enrichment (120-180s)",
    emoji="🔎",
)
