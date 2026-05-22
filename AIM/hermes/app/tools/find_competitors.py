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
        return {k: first_param.get(k, defaults[k]) for k in defaults}
    return None


AIM_API_BASE = "http://app:8000"
REQUEST_TIMEOUT = 60.0  # longer — service extractor fetches website


async def handle_find_competitors(url=None, **kwargs) -> str:
    """Find top-3 competitors for a clinic website.

    Extracts client services, specialization, and city from the website,
    searches DaData for similar medical companies, scores them by
    revenue match, location, and service overlap, and returns top-3.

    Args:
        url: Client clinic website URL (e.g., "https://clinic.ru")

    Returns:
        JSON string with 3 competitors: inn, legal_name, revenue, services,
        match scores (revenue_match, location_score, service_overlap),
        and human-readable match_reason for each.
    """
    unpacked = _normalize_args(url, {"url": ""})
    if unpacked:
        url = unpacked["url"]

    if not url:
        return json.dumps({"error": "url is required"})

    logger.info("Finding competitors for URL: %s", url)
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{AIM_API_BASE}/api/competitors/find",
                json={"url": url, "count": 3},
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
            logger.info("Found %d competitors for URL: %s", len(competitors), url)

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
                })
            return json.dumps({"competitors": compact}, ensure_ascii=False, indent=2)

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
                "Returns 3 competitors with match reasons for the client to review."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Client clinic website URL (e.g., 'https://clinic.ru')",
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
