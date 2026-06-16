"""
run_ci_analysis — Hermes tool: CI Marketing Analysis

POST http://app:8000/api/competitors/analyze
Uses non-streaming endpoint because hermes-agent runs tools in a
ThreadPoolExecutor where SSE aiter_bytes() does not work reliably.

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


def _normalize_competitor(comp) -> dict:
    """Normalize a competitor to {'name': str, 'url': str} dict.

    LLM may pass bare strings, objects with 'website' instead of 'url',
    or clinic names without URLs. This handles all cases gracefully.
    """
    if isinstance(comp, str):
        if comp.startswith(("http://", "https://")):
            name = comp.split("//")[-1].split("/")[0].replace("www.", "")[:40]
            return {"name": name, "url": comp}
        # Clinic name without URL — pass as name, API needs a url too
        return {"name": comp, "url": ""}
    if isinstance(comp, dict):
        url = comp.get("url", comp.get("website", ""))
        name = comp.get("name", comp.get("brand_name", ""))
        if not name and url:
            name = url.split("//")[-1].split("/")[0].replace("www.", "")[:40]
        return {"name": name or "unknown", "url": url}
    return {"name": "unknown", "url": ""}


AIM_API_BASE = "http://app:8000"
REQUEST_TIMEOUT = 600.0  # deep tier runs 9 phases, can take 5-8 min


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

    Scrapes competitor websites in parallel, then produces:
    - SWOT analysis (per-competitor + aggregate)
    - Feature comparison matrix (21 dimensions)
    - Pricing tier comparison
    - Positioning map (price × specialization)
    - Steal-worthy tactics (what to copy from competitors)
    - Top strategic recommendation

    Use after find_competitors confirmed the competitor list.

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
        positioning_map, best_practices, top_recommendation.
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
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    # Normalize competitors: LLM may pass bare strings or {website} objects
    competitors = [_normalize_competitor(c) for c in competitors]
    # Filter out competitors without URLs — warn but don't fail
    no_url = [c["name"] for c in competitors if not c["url"]]
    competitors = [c for c in competitors if c["url"]]
    if not competitors:
        return json.dumps({
            "error": "No competitors with valid URLs",
            "detail": f"Could not resolve URLs for: {', '.join(no_url)}. Ask the client for website links.",
        })

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
                    "tier": "deep",
                    "client_revenue": client_revenue,
                    "client_rating": client_rating,
                },
            )
            response.raise_for_status()
            result = response.json()

        logger.info(
            "CI analysis complete: duration=%.1fs tactics=%d",
            result.get("duration_seconds", 0),
            len(result.get("steal_worthy_tactics", [])),
        )

        return json.dumps({
            "chat_summary": result.get("chat_summary", ""),
            "feature_matrix": result.get("feature_matrix", {}),
            "pricing_comparison": result.get("pricing_comparison", {}),
            "positioning_map": result.get("positioning_map", {}),
            "best_practices": result.get("steal_worthy_tactics", []),
            "top_recommendation": result.get("top_recommendation", ""),
            "duration_seconds": result.get("duration_seconds", 0),
        }, ensure_ascii=False, indent=2)

    except httpx.HTTPStatusError as e:
        logger.error("AIM API returned error for run_ci_analysis: %s", e)
        return json.dumps({
            "error": "AIM API returned an error",
            "status": e.response.status_code,
            "detail": str(e) or type(e).__name__,
        })
    except httpx.RequestError as e:
        logger.error("Cannot reach AIM API for run_ci_analysis: %s (type=%s)", e, type(e).__name__)
        return json.dumps({
            "error": "Cannot reach AIM API",
            "detail": str(e) or type(e).__name__,
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
                "Run full competitive intelligence analysis on selected competitors. "
                "Analyzes SEO (basic audit, no paid APIs), social media presence "
                "(Instagram, Telegram, VK, TikTok), tax-filed financials from "
                "bo.nalog.gov.ru, and website features. Compares everything against "
                "the client's own website. Returns detailed per-competitor breakdown "
                "with scores, specific issues, and strategic recommendations."
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
                        "description": (
                            "List of competitors. Each object MUST have 'website' field. "
                            "If from find_competitors, include all fields. "
                            "If named manually by user (when find_competitors failed), "
                            "pass: {\"website\": \"https://competitor.ru\"} — "
                            "brand_name and other fields are optional."
                        ),
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
    description="Full CI analysis: SEO + social + financials + website comparison",
    emoji="📊",
)
