"""
run_ads_report — Hermes tool: Ads Performance Report

POST http://app:8000/api/ads/report
Generates advertising performance report for a client project. Shows ROAS, CPC,
CTR, conversion rates, budget utilization across Yandex.Direct, VK Ads, Telegram Ads.

Registered in Hermes internal registry under toolset "aim-operations".
"""

import json
import logging

import httpx

from tools.registry import registry

logger = logging.getLogger(__name__)


def _normalize_args(first_param, defaults):
    """If hermes-agent passes the whole arguments object as first_param, extract all values."""
    if isinstance(first_param, dict):
        return {k: first_param.get(k, defaults[k]) for k in defaults}
    return None


AIM_API_BASE = "http://app:8000"
REQUEST_TIMEOUT = 30.0  # seconds


async def handle_run_ads_report(project_id=None, period="month", **kwargs) -> str:
    """Generate advertising performance report for a client project.

    Shows ROAS, CPC, CTR, conversion rates, and budget utilization
    across Yandex.Direct, VK Ads, and Telegram Ads platforms.

    Args:
        project_id: Project ID to generate report for
        period: Report period: "week", "month", or "quarter"

    Returns:
        JSON string with multi-platform ads performance metrics.
    """
    unpacked = _normalize_args(project_id, {"project_id": "", "period": "month"})
    if unpacked:
        project_id = unpacked["project_id"]
        period = unpacked["period"]
    logger.info("Running ads report for project: %s (period: %s)", project_id, period)
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{AIM_API_BASE}/api/ads/report",
                json={"project_id": project_id, "period": period},
            )
            response.raise_for_status()
            data = response.json()
            logger.info("Ads report completed for project: %s", project_id)
            return json.dumps(data, ensure_ascii=False, indent=2)
    except httpx.HTTPStatusError as e:
        logger.error("AIM API returned error for ads report: %s", e)
        return json.dumps({
            "error": "AIM API returned an error",
            "status": e.response.status_code,
            "detail": str(e),
        })
    except httpx.RequestError as e:
        logger.error("Cannot reach AIM API for ads report: %s", e)
        return json.dumps({
            "error": "Cannot reach AIM API",
            "detail": str(e),
        })
    except Exception as e:
        logger.exception("Unexpected error in ads report handler")
        return json.dumps({
            "error": "Unexpected error in tool handler",
            "detail": str(e),
        })


registry.register(
    name="run_ads_report",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "run_ads_report",
            "description": (
                "Generate advertising performance report for a client project. "
                "Shows ROAS, CPC, CTR, conversion rates, budget utilization "
                "across Yandex.Direct, VK Ads, Telegram Ads."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project ID to generate report for",
                    },
                    "period": {
                        "type": "string",
                        "description": "Report period: week, month, quarter",
                        "enum": ["week", "month", "quarter"],
                    },
                },
                "required": ["project_id"],
            },
        },
    },
    handler=handle_run_ads_report,
    check_fn=lambda: True,
    is_async=True,
    description="Generate advertising performance report showing ROAS, CPC, CTR across platforms",
    emoji="📊",
)
