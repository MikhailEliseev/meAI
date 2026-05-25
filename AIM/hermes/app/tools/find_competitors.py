"""
find_competitors — Hermes tool: Find Top-3 Competitors

POST http://app:8000/api/competitors/find
Extracts services from client website, searches DaData for similar
medical companies, scores by revenue/location/services, returns top-3.

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


AIM_API_BASE = "http://app:8000"
REQUEST_TIMEOUT = 60.0  # longer — service extractor fetches website


async def handle_find_competitors(url=None, named_competitors=None, **kwargs) -> str:
    """Find top-3 competitors for a clinic website.

    Extracts client services, specialization, and city from the website,
    searches DaData for similar medical companies, scores them by
    revenue match, location, and service overlap, and returns top-3.

    Args:
        url: Client clinic website URL (e.g., "https://clinic.ru")
        named_competitors: Optional list of competitor names or URLs

    Returns:
        JSON string with 3 competitors: inn, legal_name, revenue, services,
        match scores (revenue_match, location_score, service_overlap),
        and human-readable match_reason for each.
    """
    defaults = {"url": "", "named_competitors": None}
    unpacked = _normalize_args(url, defaults)
    if unpacked:
        url = unpacked["url"]
        named_competitors = unpacked.get("named_competitors")

    if not url:
        return json.dumps({"error": "url is required"})
    # Auto-prepend https:// if URL has no protocol
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    logger.info("Finding competitors for URL: %s, named: %s", url, named_competitors)
    try:
        payload: dict = {"url": url, "count": 3}
        if named_competitors:
            payload["named_competitors"] = named_competitors

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{AIM_API_BASE}/api/competitors/find",
                json=payload,
            )
            response.raise_for_status()
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

            # Compact for LLM consumption — strip noisy fields
            compact = []
            for i, c in enumerate(competitors, 1):
                profile = c.get("profile", {})
                compact.append({
                    "rank": i,
                    "inn": profile.get("inn", c.get("inn", "")),
                    "legal_name": c.get("legal_name", profile.get("legal_name", "")),
                    "brand_name": c.get("brand_name") or profile.get("brand_name"),
                    "revenue_year": c.get("revenue_year") or profile.get("revenue_year"),
                    "profit_year": c.get("profit_year") or profile.get("profit_year"),
                    "financial_year": c.get("financial_year") or profile.get("financial_year"),
                    "data_source": c.get("data_source", profile.get("data_source", "estimate")),
                    "services": c.get("services", []),
                    "total_score": c.get("total_score"),
                    "revenue_match": c.get("revenue_match"),
                    "match_reason": c.get("match_reason", ""),
                    "website": c.get("website"),
                    "social_links": c.get("social_links", {}),
                })

            result: dict = {"competitors": compact}
            if is_megalopolis:
                result["is_megalopolis"] = True
                result["suggestion"] = (
                    "Это крупный город (Москва/СПб). Автоматический поиск конкурентов "
                    "по открытым данным даёт ограниченные результаты. Попроси пользователя "
                    "назвать его конкурентов — он точно знает своих главных соперников. "
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
                "Find top-3 competitors for a client clinic website. "
                "Extracts services, city, and specialization from the site, "
                "searches DaData for similar medical companies, scores them "
                "by revenue match, location, and service overlap. "
                "Optionally accepts named_competitors — a list of competitor "
                "names or URLs to look up directly via DaData. "
                "Returns 3 competitors with match reasons for the client to review."
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
                        "description": "Optional list of competitor names or URLs to look up via DaData",
                    },
                },
                "required": ["url"],
            },
        },
    },
    handler=handle_find_competitors,
    check_fn=lambda: True,
    is_async=True,
    description="Find top-3 competitors for a clinic website by revenue, services, and location",
    emoji="🔎",
)
