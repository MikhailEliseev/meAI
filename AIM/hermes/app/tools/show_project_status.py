"""
show_project_status — Hermes tool: Project Status

GET http://app:8000/api/projects/{project_id}/status
Shows current project status including active tasks, recent KPIs, current
sprint progress, and any blockers. For active clients, shows business-level
summary. For admin, shows full technical details.

Registered in Hermes internal registry under toolset "aim-operations".
"""

import json
import logging

import httpx

from tools.registry import registry

logger = logging.getLogger(__name__)

AIM_API_BASE = "http://app:8000"
REQUEST_TIMEOUT = 30.0  # seconds


async def handle_show_project_status(project_id: str) -> str:
    """Show current project status for a client project.

    Returns active tasks, recent KPIs, current sprint progress,
    and any blockers. Level of detail depends on caller permissions.

    Args:
        project_id: Project ID to check status for

    Returns:
        JSON string with project status including tasks, KPIs, and blockers.
    """
    logger.info("Fetching project status for: %s", project_id)
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(
                f"{AIM_API_BASE}/api/projects/{project_id}/status",
            )
            response.raise_for_status()
            data = response.json()
            logger.info("Project status fetched for: %s", project_id)
            return json.dumps(data, ensure_ascii=False, indent=2)
    except httpx.HTTPStatusError as e:
        logger.error("AIM API returned error for project status: %s", e)
        return json.dumps({
            "error": "AIM API returned an error",
            "status": e.response.status_code,
            "detail": str(e),
        })
    except httpx.RequestError as e:
        logger.error("Cannot reach AIM API for project status: %s", e)
        return json.dumps({
            "error": "Cannot reach AIM API",
            "detail": str(e),
        })
    except Exception as e:
        logger.exception("Unexpected error in project status handler")
        return json.dumps({
            "error": "Unexpected error in tool handler",
            "detail": str(e),
        })


registry.register(
    name="show_project_status",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "show_project_status",
            "description": (
                "Show current project status including active tasks, recent KPIs, "
                "current sprint progress, and any blockers. For active clients, "
                "shows business-level summary. For admin, shows full technical details."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project ID to check status for",
                    },
                },
                "required": ["project_id"],
            },
        },
    },
    handler=handle_show_project_status,
    check_fn=lambda: True,
    is_async=True,
    description="Show current project status including KPIs, tasks, and blockers",
    emoji="📋",
)
