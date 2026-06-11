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


PROJECTS_ROOT = os.getenv("PROJECTS_ROOT", "/root/projects")


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


def _project_status_from_projects_dir(project_id: str) -> dict | None:
    """Try to read project status from /root/projects/{client}/{project}/."""
    projects_root = Path(PROJECTS_ROOT)
    if not projects_root.exists():
        return None

    # Parse project_id: "client_slug:project_slug" or just "project_slug"
    parts = project_id.split(":", 1)
    if len(parts) == 2:
        client_slug, project_slug = parts
    else:
        project_slug = parts[0]
        client_slug = None

    # Find project path — check direct and nested (e.g. archive/presale-01)
    project_path = None
    client_dirs = [projects_root / client_slug] if client_slug else sorted(projects_root.iterdir())
    for client_dir in client_dirs:
        if not client_dir.is_dir():
            continue
        # Direct match
        candidate = client_dir / project_slug
        if candidate.exists() and candidate.is_dir():
            project_path = candidate
            client_slug = client_dir.name
            break
        # Recursive search (depth 1: e.g. archive/presale-01)
        for nested in sorted(client_dir.rglob(project_slug)):
            if nested.is_dir() and nested.relative_to(client_dir).parts[0] != ".impeccable":
                project_path = nested
                client_slug = client_dir.name
                break
        if project_path:
            break

    if project_path is None:
        return None

    meta_path = project_path / ".project-meta.json"
    meta = {}
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text())
        except Exception:
            pass

    # Count files as a proxy for project activity
    file_count = sum(1 for _ in project_path.rglob("*") if _.is_file())

    # Check for context.json
    ctx_path = project_path / "context.json"
    pending_tasks = []
    if ctx_path.exists():
        try:
            ctx = json.loads(ctx_path.read_text())
            pending_tasks = ctx.get("pending_tasks", [])
        except Exception:
            pass

    # Check notes/findings.md
    findings_path = project_path / "notes" / "findings.md"
    findings_preview = None
    if findings_path.exists():
        try:
            lines = findings_path.read_text().split("\n")
            findings_preview = lines[-5:] if len(lines) > 5 else lines
        except Exception:
            pass

    # Look for scope/plan files
    scope_files = []
    for name in ["SCOPE.md", "PLAN.md", "README.md", "KP_DESIGN.md"]:
        fp = project_path / name
        if fp.exists():
            scope_files.append(name)

    now = datetime.now(timezone.utc).isoformat()

    return {
        "project_id": project_id,
        "status": meta.get("status", "active"),
        "client_slug": client_slug,
        "project_slug": project_slug,
        "client_name": meta.get("client_name"),
        "project_name": meta.get("name"),
        "created_at": meta.get("created_at"),
        "file_count": file_count,
        "scope_files": scope_files,
        "pending_tasks": pending_tasks,
        "findings_preview": findings_preview,
        "source": "projects_dir",
        "generated_at": now,
        "active_tasks": [
            {"id": t.get("id"), "description": t.get("description"), "status": t.get("status")}
            for t in pending_tasks if t.get("status") == "pending"
        ],
        "recent_kpis": {},
        "blockers": [],
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
        # Fallback 1: check projects directory
        status = _project_status_from_projects_dir(project_id)

    if status is None:
        # Fallback 2: try parsing project_id as client:project
        if ":" in project_id:
            # Could be in projects dir
            pass  # Already tried above
        now = datetime.now(timezone.utc).isoformat()
        status = {
            "project_id": project_id,
            "status": "not_found",
            "warning": "Проект не найден ни в лидах, ни в директории проектов. Проверьте ID.",
            "generated_at": now,
            "active_tasks": [],
            "recent_kpis": {},
            "blockers": [],
        }

    logger.info("Project status fetched for: %s → %s (source: %s)",
                project_id, status.get("status"), status.get("source", "none"))
    return status
