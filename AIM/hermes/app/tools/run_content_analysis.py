"""
run_content_analysis — Hermes tool: Content Analysis

POST http://app:8000/api/content/analyze
Analyzes content quality on a medical clinic website. Evaluates medical accuracy,
SEO optimization, readability, and conversion effectiveness per page type.

Registered in Hermes internal registry under toolset "aim-operations".
"""

import json
import logging

import httpx

from tools.registry import registry

logger = logging.getLogger(__name__)

AIM_API_BASE = "http://app:8000"
REQUEST_TIMEOUT = 30.0  # seconds


async def handle_run_content_analysis(url: str, content_type: str = "all") -> str:
    """Analyze content quality on a medical clinic website.

    Evaluates medical accuracy, SEO optimization, readability scores,
    and conversion effectiveness. Analysis can be filtered by page type.

    Args:
        url: Website URL to analyze (e.g., "https://clinic.ru")
        content_type: Type of content to analyze: "all", "blog", "services", or "landing"

    Returns:
        JSON string with content analysis results per page type.
    """
    logger.info("Running content analysis for URL: %s (type: %s)", url, content_type)
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{AIM_API_BASE}/api/content/analyze",
                json={"url": url, "content_type": content_type},
            )
            response.raise_for_status()
            data = response.json()
            logger.info("Content analysis completed for URL: %s", url)
            return json.dumps(data, ensure_ascii=False, indent=2)
    except httpx.HTTPStatusError as e:
        logger.error("AIM API returned error for content analysis: %s", e)
        return json.dumps({
            "error": "AIM API returned an error",
            "status": e.response.status_code,
            "detail": str(e),
        })
    except httpx.RequestError as e:
        logger.error("Cannot reach AIM API for content analysis: %s", e)
        return json.dumps({
            "error": "Cannot reach AIM API",
            "detail": str(e),
        })
    except Exception as e:
        logger.exception("Unexpected error in content analysis handler")
        return json.dumps({
            "error": "Unexpected error in tool handler",
            "detail": str(e),
        })


registry.register(
    name="run_content_analysis",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "run_content_analysis",
            "description": (
                "Analyze content quality on a medical clinic website. "
                "Evaluates medical accuracy, SEO optimization, readability, "
                "and conversion effectiveness per page type."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Website URL to analyze (e.g., 'https://clinic.ru')",
                    },
                    "content_type": {
                        "type": "string",
                        "description": "Type of content to analyze: all, blog, services, landing",
                        "enum": ["all", "blog", "services", "landing"],
                    },
                },
                "required": ["url"],
            },
        },
    },
    handler=handle_run_content_analysis,
    check_fn=lambda: True,
    is_async=True,
    description="Analyze content quality on a medical clinic website per page type",
    emoji="📝",
)
