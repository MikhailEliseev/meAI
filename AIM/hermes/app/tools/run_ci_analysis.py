"""
run_ci_analysis — Hermes tool: CI Marketing Analysis

POST http://app:8000/api/competitors/analyze
Scrapes competitor websites and runs rule-based marketing analysis:
SWOT, feature matrix, pricing comparison, positioning map, steal-worthy tactics.

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
REQUEST_TIMEOUT = 30.0  # parallel scraping of 3 websites + analysis


async def handle_run_ci_analysis(
    url=None,
    specialization=None,
    city=None,
    services=None,
    competitors=None,
    client_revenue=None,
    client_rating=None,
    **kwargs,
) -> str:
    """Run CI marketing analysis on confirmed competitors.

    Scrapes 3 competitor websites in parallel, then produces:
    - SWOT analysis (per-competitor + aggregate)
    - Feature comparison matrix (21 dimensions)
    - Pricing tier comparison
    - Positioning map (price × specialization)
    - Steal-worthy tactics (what to copy from competitors)
    - Top strategic recommendation

    Args:
        url: Client clinic website URL
        specialization: Client specialization (e.g., "стоматология")
        city: Client city
        services: List of client services
        competitors: List of 3 confirmed competitor objects
        client_revenue: Estimated client annual revenue (optional)
        client_rating: Client rating (optional)

    Returns:
        JSON with chat_summary, feature_matrix, pricing_comparison,
        positioning_map, steal_worthy_tactics, top_recommendation.
    """
    unpacked = _normalize_args(url, {
        "url": "",
        "specialization": "",
        "city": "",
        "services": [],
        "competitors": [],
        "client_revenue": None,
        "client_rating": None,
    })
    if unpacked:
        url = unpacked["url"]
        specialization = unpacked["specialization"]
        city = unpacked["city"]
        services = unpacked["services"]
        competitors = unpacked["competitors"]
        client_revenue = unpacked["client_revenue"]
        client_rating = unpacked["client_rating"]

    if not url:
        return json.dumps({"error": "url is required"})
    if not competitors or len(competitors) == 0:
        return json.dumps({"error": "at least one competitor is required"})

    logger.info(
        "Running CI analysis for URL: %s (%s, %s) with %d competitors",
        url, specialization, city, len(competitors),
    )

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{AIM_API_BASE}/api/competitors/analyze",
                json={
                    "url": url,
                    "specialization": specialization or "",
                    "city": city or "",
                    "services": services or [],
                    "competitors": competitors,
                    "client_revenue": client_revenue,
                    "client_rating": client_rating,
                },
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                logger.warning("run_ci_analysis returned error: %s", data.get("error"))
                return json.dumps({
                    "error": "CI analysis failed",
                    "detail": data.get("error", "Unknown error"),
                })

            logger.info(
                "CI analysis complete: duration=%.1fs tactics=%d features=%d",
                data.get("duration_seconds", 0),
                len(data.get("steal_worthy_tactics", [])),
                len(data.get("feature_matrix", {})),
            )

            return json.dumps({
                "chat_summary": data.get("chat_summary", ""),
                "feature_matrix": data.get("feature_matrix", {}),
                "pricing_comparison": data.get("pricing_comparison", {}),
                "positioning_map": data.get("positioning_map", {}),
                "steal_worthy_tactics": data.get("steal_worthy_tactics", []),
                "top_recommendation": data.get("top_recommendation", ""),
                "duration_seconds": data.get("duration_seconds", 0),
            }, ensure_ascii=False, indent=2)

    except httpx.HTTPStatusError as e:
        logger.error("AIM API returned error for run_ci_analysis: %s", e)
        return json.dumps({
            "error": "AIM API returned an error",
            "status": e.response.status_code,
            "detail": str(e),
        })
    except httpx.RequestError as e:
        logger.error("Cannot reach AIM API for run_ci_analysis: %s", e)
        return json.dumps({
            "error": "Cannot reach AIM API",
            "detail": str(e),
        })
    except Exception as e:
        logger.exception("Unexpected error in run_ci_analysis handler")
        return json.dumps({
            "error": "Unexpected error in tool handler",
            "detail": str(e),
        })


registry.register(
    name="run_ci_analysis",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "run_ci_analysis",
            "description": (
                "Run competitive intelligence marketing analysis on 3 confirmed competitors. "
                "Scrapes competitor websites, then produces SWOT analysis, feature comparison "
                "matrix (21 dimensions), pricing tier comparison, positioning map, and "
                "steal-worthy tactics. Fast (<12s), deterministic, no LLM calls. "
                "Shows the client exactly where they stand vs competitors and what to improve."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Client clinic website URL (e.g., 'https://clinic.ru')",
                    },
                    "specialization": {
                        "type": "string",
                        "description": "Client specialization (e.g., 'стоматология', 'косметология')",
                    },
                    "city": {
                        "type": "string",
                        "description": "Client city (e.g., 'Казань')",
                    },
                    "services": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of client services",
                    },
                    "competitors": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "List of 3 confirmed competitors from find_competitors result",
                    },
                    "client_revenue": {
                        "type": "integer",
                        "description": "Estimated client annual revenue in RUB (optional)",
                    },
                    "client_rating": {
                        "type": "number",
                        "description": "Client rating from Yandex Maps (optional, 0-5)",
                    },
                },
                "required": ["url", "competitors"],
            },
        },
    },
    handler=handle_run_ci_analysis,
    check_fn=lambda: True,
    is_async=True,
    description="CI marketing analysis: SWOT, features, pricing, tactics for 3 competitors",
    emoji="📊",
)
