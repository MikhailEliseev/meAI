"""
run_ci_analysis — Hermes tool: CI Marketing Analysis

POST http://app:8000/api/competitors/analyze/stream (SSE)
Consumes real-time progress events and pushes them to the global
progress queue so the frontend sees live updates during collection.

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
REQUEST_TIMEOUT = 300.0  # SSE streaming + parallel scraping (large competitors can take 2-3 min)


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

    Uses SSE streaming endpoint — progress events are pushed to the
    global tool_progress_queue in real-time so the frontend sees:
    "🔍 Ищу конкурентов…", "💰 Смотрю финансовую отчётность…", etc.

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
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    logger.info(
        "Running CI analysis (SSE stream) for URL: %s (%s, %s) with %d competitors",
        url, specialization, city, len(competitors),
    )

    # Import push_tool_progress for real-time progress events
    try:
        from app.main import push_tool_progress
    except ImportError:
        push_tool_progress = lambda stage, msg, comp="": logger.info("[tool-progress] %s: %s", stage, msg)

    result_data: dict = {}

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            async with client.stream(
                "POST",
                f"{AIM_API_BASE}/api/competitors/analyze/stream",
                json={
                    "url": url,
                    "specialization": specialization or "",
                    "city": city or "",
                    "services": services or [],
                    "competitors": competitors,
                    "client_revenue": client_revenue,
                    "client_rating": client_rating,
                },
            ) as response:
                response.raise_for_status()

                buffer = ""
                async for chunk in response.aiter_bytes():
                    buffer += chunk.decode("utf-8", errors="replace")
                    while "\n\n" in buffer:
                        line, buffer = buffer.split("\n\n", 1)
                        # Parse SSE frame: "data: {...}"
                        for raw_line in line.split("\n"):
                            raw_line = raw_line.strip()
                            if not raw_line.startswith("data: "):
                                continue
                            try:
                                event = json.loads(raw_line[6:])
                            except json.JSONDecodeError:
                                continue

                            event_type = event.get("type", "")

                            if event_type == "progress":
                                # Push to global queue for real-time SSE relay
                                push_tool_progress(
                                    event.get("stage", ""),
                                    event.get("message", ""),
                                    event.get("competitor", ""),
                                )

                            elif event_type == "result":
                                result_data = event.get("data", {})

                            elif event_type == "error":
                                logger.error("SSE stream error: %s", event.get("message"))
                                return json.dumps({
                                    "error": "CI analysis failed",
                                    "detail": event.get("message", "Unknown error"),
                                })

        if not result_data:
            return json.dumps({
                "error": "CI analysis failed",
                "detail": "No result received from SSE stream",
            })

        logger.info(
            "CI analysis complete: duration=%.1fs",
            result_data.get("duration_seconds", 0),
        )

        return json.dumps({
            "chat_summary": result_data.get("chat_summary", ""),
            "feature_matrix": result_data.get("feature_matrix", {}),
            "pricing_comparison": result_data.get("pricing_comparison", {}),
            "positioning_map": result_data.get("positioning_map", {}),
            "steal_worthy_tactics": result_data.get("steal_worthy_tactics", []),
            "top_recommendation": result_data.get("top_recommendation", ""),
            "duration_seconds": result_data.get("duration_seconds", 0),
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
