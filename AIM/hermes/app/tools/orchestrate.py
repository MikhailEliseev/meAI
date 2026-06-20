"""
orchestrate — unified Hermes tool replacing 16 AIM operation tools.

Calls POST http://app:8000/api/hermes/orchestrate — the single orchestration endpoint.
All operations (prescan, seo_audit, content_analysis, ads_report,
competitor_analysis, lead_management, knowledge_query) go through this one tool.

Registered in Hermes internal registry under toolset "aim-operations".
"""

import json
import logging

import httpx

from tools.registry import registry

logger = logging.getLogger(__name__)

AIM_API_BASE = "http://aim-app:8000"
REQUEST_TIMEOUT = 300.0


async def handle_orchestrate(operation=None, params=None, **kwargs) -> str:
    """Route any AIM operation through the unified orchestrator.

    Args:
        operation: Operation name — one of:
            prescan, seo_audit, content_analysis, ads_report,
            competitor_analysis, lead_management, knowledge_query
        params: Operation-specific parameters:
            - prescan: {url, force_refresh?}
            - seo_audit: {url, timeout?}
            - competitor_analysis: {url, competitors?, niche?, tier?}
            - lead_management: {action, lead_data?, period?, status?}
            - knowledge_query: {query, domain?}
            - ads_report: {client_id?, period?}
            - content_analysis: {url}

    Returns:
        JSON string with {"status": "success"|"error", "operation": ..., "result": {...}}
    """
    if isinstance(operation, dict):
        d = operation
        operation = d.get("operation", "")
        if not params:
            params = d.get("params", {})

    if isinstance(params, dict) and "url" in params:
        url = params["url"]
        if isinstance(url, str) and not url.startswith(("http://", "https://")):
            params = {**params, "url": "https://" + url}

    if not operation:
        return json.dumps({
            "error": "operation is required",
            "available": [
                "prescan", "seo_audit", "content_analysis",
                "ads_report", "competitor_analysis",
                "lead_management", "knowledge_query",
            ],
        })

    logger.info("Orchestrating operation: %s", operation)

    from app.main import push_tool_progress

    push_tool_progress(
        operation,
        f"Выполняю операцию: {operation}…",
    )

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{AIM_API_BASE}/api/hermes/orchestrate",
                json={"operation": operation, "params": params or {}},
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "success":
                result = data.get("result", {})
                push_tool_progress(
                    operation,
                    f"Операция {operation} завершена успешно",
                )
                return json.dumps(result, ensure_ascii=False, indent=2)
            else:
                logger.warning("Operation %s returned error: %s", operation, data.get("error"))
                return json.dumps({
                    "error": f"Operation '{operation}' failed",
                    "detail": data.get("error", "Unknown error"),
                }, ensure_ascii=False)

    except httpx.HTTPStatusError as e:
        logger.error("AIM API error for operation %s: %s", operation, e)
        return json.dumps({
            "error": f"AIM API error ({e.response.status_code})",
            "detail": str(e),
        })
    except httpx.RequestError as e:
        logger.error("Cannot reach AIM API for operation %s: %s", operation, e)
        return json.dumps({
            "error": "Cannot reach AIM API",
            "detail": str(e),
        })
    except Exception as e:
        logger.exception("Unexpected error in orchestrate handler")
        return json.dumps({
            "error": "Unexpected error in tool handler",
            "detail": str(e),
        })


# ── Registry ───────────────────────────────────────────────────────────────

registry.register(
    name="orchestrate",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "orchestrate",
            "description": (
                "Unified orchestrator for ALL AIM operations. "
                "Use this ONE tool instead of run_prescan, run_seo_audit, find_competitors, etc. "
                "Operations: "
                "prescan (3-stage intelligence: financials → deep analysis → market), "
                "seo_audit (SEO analysis with weighted scoring), "
                "content_analysis (content quality and structure), "
                "ads_report (ad campaign performance), "
                "competitor_analysis (CI pipeline: quick/deep/full tiers), "
                "lead_management (collect/list/qualify leads), "
                "knowledge_query (search AIM knowledge base)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": (
                            "[REQUIRED] Operation to execute: prescan, seo_audit, content_analysis, "
                            "ads_report, competitor_analysis, lead_management, knowledge_query"
                        ),
                        "enum": [
                            "prescan",
                            "seo_audit",
                            "content_analysis",
                            "ads_report",
                            "competitor_analysis",
                            "lead_management",
                            "knowledge_query",
                        ],
                    },
                    "params": {
                        "type": "object",
                        "description": (
                            "[REQUIRED] Operation-specific parameters. "
                            "prescan: {url, force_refresh?}. "
                            "seo_audit: {url, timeout?}. "
                            "competitor_analysis: {url, competitors?, niche?, tier?}. "
                            "lead_management: {action: collect|list|qualify, lead_data?, period?, status?}. "
                            "knowledge_query: {query, domain?}."
                        ),
                    },
                },
                "required": ["operation", "params"],
            },
        },
    },
    handler=handle_orchestrate,
    check_fn=lambda: True,
    is_async=True,
    description="Unified orchestrator for ALL AIM operations — one tool to rule them all",
    emoji="🎯",
)
