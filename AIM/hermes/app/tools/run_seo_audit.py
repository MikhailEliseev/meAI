"""
run_seo_audit — Hermes tool: SEO Audit

POST http://app:8000/api/seo/audit
Runs a full SEO audit on a client website: technical analysis, keyword positions,
competitor comparison, backlink profile. Returns patient acquisition potential
(3 key numbers: patients/month, time-to-result, cost-per-patient).

Registered in Hermes internal registry under toolset "aim-operations".
"""

import json
import logging

import httpx

from tools.registry import registry

logger = logging.getLogger(__name__)

AIM_API_BASE = "http://app:8000"
REQUEST_TIMEOUT = 30.0  # seconds


async def handle_run_seo_audit(url: str, **kwargs) -> str:
    """Run a full SEO audit on a client website.

    Performs technical SEO analysis, keyword position tracking,
    competitor comparison, and backlink profile analysis.
    Returns patient acquisition potential metrics.

    Args:
        url: Website URL to audit (e.g., "https://clinic.ru")

    Returns:
        JSON string with audit results including:
        - patients_per_month: estimated monthly patient acquisition
        - time_to_result: estimated weeks to first results
        - cost_per_patient: estimated acquisition cost
    """
    logger.info("Running SEO audit for URL: %s", url)
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{AIM_API_BASE}/api/seo/audit",
                json={"url": url},
            )
            response.raise_for_status()
            data = response.json()
            logger.info("SEO audit completed for URL: %s", url)
            return json.dumps(data, ensure_ascii=False, indent=2)
    except httpx.HTTPStatusError as e:
        logger.error("AIM API returned error for SEO audit: %s", e)
        return json.dumps({
            "error": "AIM API returned an error",
            "status": e.response.status_code,
            "detail": str(e),
        })
    except httpx.RequestError as e:
        logger.error("Cannot reach AIM API for SEO audit: %s", e)
        return json.dumps({
            "error": "Cannot reach AIM API",
            "detail": str(e),
        })
    except Exception as e:
        logger.exception("Unexpected error in SEO audit handler")
        return json.dumps({
            "error": "Unexpected error in tool handler",
            "detail": str(e),
        })


registry.register(
    name="run_seo_audit",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "run_seo_audit",
            "description": (
                "Run a full SEO audit on a client website: technical analysis, "
                "keyword positions, competitor comparison, backlink profile. "
                "Returns patient acquisition potential (3 key numbers: "
                "patients/month, time-to-result, cost-per-patient)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Website URL to audit (e.g., 'https://clinic.ru')",
                    },
                },
                "required": ["url"],
            },
        },
    },
    handler=handle_run_seo_audit,
    check_fn=lambda: True,
    is_async=True,
    description="Run a full SEO audit on a client website and return patient acquisition potential",
    emoji="🔍",
)
