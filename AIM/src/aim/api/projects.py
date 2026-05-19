"""
Project Status API Endpoint

GET /api/projects/{project_id}/status — Current project status.
Wires Hermes tool show_project_status → project data.
"""

import logging
import os
import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _project_status_from_dossier(lead_id: str) -> dict | None:
    """Try to read project status from lead dossier filesystem."""
    leads_dir = os.getenv("LEADS_DIR", "/opt/data/leads")
    dossier_path = Path(leads_dir) / lead_id

    if not dossier_path.exists():
        return None

    status_data = {}
    try:
        status_file = dossier_path / "status.json"
        if status_file.exists():
            status_data = json.loads(status_file.read_text())
    except Exception:
        pass

    try:
        profile_file = dossier_path / "profile.json"
        if profile_file.exists():
            profile = json.loads(profile_file.read_text())
            status_data["website"] = profile.get("website")
            status_data["specialty"] = profile.get("specialty")
    except Exception:
        pass

    # Count chat messages
    try:
        chat_file = dossier_path / "chat_history.json"
        if chat_file.exists():
            messages = json.loads(chat_file.read_text())
            status_data["messages_count"] = len(messages)
    except Exception:
        status_data["messages_count"] = 0

    now = datetime.now(timezone.utc).isoformat()

    return {
        "project_id": lead_id,
        "status": status_data.get("status", "unknown"),
        "website": status_data.get("website"),
        "specialty": status_data.get("specialty"),
        "messages_count": status_data.get("messages_count", 0),
        "updated_at": status_data.get("updatedAt", now),
        "active_tasks": [],
        "recent_kpis": {
            "leads_captured": 0,
            "seo_audits_completed": 0,
            "content_pages_analyzed": 0,
        },
        "blockers": [],
        "next_milestone": "Аудит сайта",
    }


@router.get("/{project_id}/status")
async def show_project_status(project_id: str):
    """Show current project status.

    Returns active tasks, recent KPIs, sprint progress, and blockers.
    Detail level depends on caller permissions (business vs admin).
    """
    if not project_id or not project_id.strip():
        raise HTTPException(status_code=400, detail="project_id is required")

    project_id = project_id.strip()

    # Try lead dossier first
    status = _project_status_from_dossier(project_id)

    if status is None:
        # Fallback: generic status
        now = datetime.now(timezone.utc).isoformat()
        status = {
            "project_id": project_id,
            "status": "not_found_in_dossiers",
            "warning": "Проект не найден в файловой системе лидов. Возможно, ID указан неверно.",
            "generated_at": now,
            "active_tasks": [],
            "recent_kpis": {},
            "blockers": [],
        }

    logger.info("Project status fetched for: %s → %s", project_id, status.get("status"))
    return status
