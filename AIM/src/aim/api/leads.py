"""Lead Capture API Endpoints

FastAPI endpoints for lead capture with AI scoring and Linear integration.

Part of: Phase 11 Sprint 2 - Task 2.1
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.aim.database import get_db
from src.aim.schemas.lead import (
    ChatLeadRequest,
    LeadCaptureRequest,
    LeadCaptureResponse,
)
from src.aim.services.lead_capture import LeadCaptureService, RateLimitExceeded, RecaptchaVerificationFailed

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/leads", tags=["leads"])

LEADS_DIR = os.getenv("LEADS_DIR", "/opt/data/leads")


def _list_leads_from_filesystem(period: str = "all", status_filter: str = "all") -> list[dict]:
    """Read lead dossiers from filesystem."""
    leads_path = Path(LEADS_DIR)
    if not leads_path.exists():
        return []

    leads = []
    for lead_dir in sorted(leads_path.iterdir(), reverse=True):
        if not lead_dir.is_dir():
            continue

        lead_id = lead_dir.name
        dossier = {"lead_id": lead_id}

        # Read status.json
        status_file = lead_dir / "status.json"
        if status_file.exists():
            try:
                status_data = json.loads(status_file.read_text())
                dossier["status"] = status_data.get("status", "unknown")
                dossier["updated_at"] = status_data.get("updatedAt", "")
            except (json.JSONDecodeError, OSError):
                dossier["status"] = "unknown"

        # Read profile.json
        profile_file = lead_dir / "profile.json"
        if profile_file.exists():
            try:
                profile = json.loads(profile_file.read_text())
                dossier["website"] = profile.get("website")
                dossier["name"] = profile.get("name")
                dossier["phone"] = profile.get("phone")
                dossier["email"] = profile.get("email")
            except (json.JSONDecodeError, OSError):
                pass

        # Count chat messages
        chat_file = lead_dir / "chat_history.json"
        if chat_file.exists():
            try:
                messages = json.loads(chat_file.read_text())
                dossier["messages_count"] = len(messages)
            except (json.JSONDecodeError, OSError):
                dossier["messages_count"] = 0
        else:
            dossier["messages_count"] = 0

        # Filter by status
        if status_filter != "all" and dossier.get("status") != status_filter:
            continue

        # Filter by period
        if period == "today":
            try:
                updated = datetime.fromisoformat(dossier.get("updated_at", "").replace("Z", "+00:00"))
                if updated.date() != datetime.now(timezone.utc).date():
                    continue
            except (ValueError, AttributeError):
                pass
        elif period == "week":
            try:
                updated = datetime.fromisoformat(dossier.get("updated_at", "").replace("Z", "+00:00"))
                days_ago = (datetime.now(timezone.utc) - updated).days
                if days_ago > 7:
                    continue
            except (ValueError, AttributeError):
                pass
        elif period == "month":
            try:
                updated = datetime.fromisoformat(dossier.get("updated_at", "").replace("Z", "+00:00"))
                days_ago = (datetime.now(timezone.utc) - updated).days
                if days_ago > 30:
                    continue
            except (ValueError, AttributeError):
                pass

        leads.append(dossier)

    return leads


@router.get("")
async def list_leads(
    period: str = Query("all", pattern=r"^(today|week|month|all)$"),
    status: str = Query("all", pattern=r"^(new|qualified|audited|contacted|active|completed|closed|all)$"),
):
    """List all leads from filesystem dossiers."""
    return _list_leads_from_filesystem(period=period, status_filter=status)


def get_lead_service(db: AsyncSession = Depends(get_db)) -> LeadCaptureService:
    """Dependency to get LeadCaptureService instance."""
    recaptcha_secret = os.getenv("RECAPTCHA_SECRET_KEY", "test_secret_key")
    return LeadCaptureService(db, recaptcha_secret=recaptcha_secret)


@router.post("", response_model=LeadCaptureResponse, status_code=status.HTTP_201_CREATED)
async def capture_chat_lead(
    request: ChatLeadRequest,
    service: LeadCaptureService = Depends(get_lead_service),
) -> LeadCaptureResponse:
    """Capture lead from Hermes chat — lightweight, no form validation.

    Hermes collects contact via two-step conversation flow and calls
    this endpoint via the collect_contact tool. No reCAPTCHA (internal
    service call), no rate limiting (Hermes throttles itself).

    Returns LeadCaptureResponse with lead_id for Hermes to report back.
    """
    try:
        result = await service.capture_chat_lead(request=request)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to capture chat lead: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to capture chat lead",
        )


@router.post("/capture", response_model=LeadCaptureResponse, status_code=status.HTTP_201_CREATED)
async def capture_lead(
    request: LeadCaptureRequest,
    http_request: Request,
    service: LeadCaptureService = Depends(get_lead_service),
) -> LeadCaptureResponse:
    """Capture lead from contact form.

    Creates lead with AI scoring and triggers Linear task creation.

    Args:
        request: Lead capture request with form data
        http_request: FastAPI request for IP extraction
        service: LeadCaptureService instance

    Returns:
        LeadCaptureResponse with lead_id, tier, score

    Raises:
        HTTPException 429: Rate limit exceeded
        HTTPException 400: Invalid data or reCAPTCHA failed
        HTTPException 500: Internal server error
    """
    try:
        # Get client IP
        client_ip = http_request.client.host if http_request.client else "unknown"

        # Capture lead (returns LeadCaptureResponse with tier/score)
        result = await service.capture_lead(
            request=request,
            client_ip=client_ip,
        )

        return result
    except RateLimitExceeded as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
        )
    except RecaptchaVerificationFailed as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        print(f"[ERROR] Failed to capture lead: {e}", flush=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to capture lead",
        )
