"""Lead Capture API Endpoints

FastAPI endpoints for lead capture with AI scoring and Linear integration.

Part of: Phase 11 Sprint 2 - Task 2.1
"""

import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from aim.database import get_db
from aim.schemas.lead import (
    LeadCaptureRequest,
    LeadCaptureResponse,
)
from aim.services.lead_capture import LeadCaptureService, RateLimitExceeded

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/leads", tags=["leads"])


def get_lead_service(db: AsyncSession = Depends(get_db)) -> LeadCaptureService:
    """Dependency to get LeadCaptureService instance."""
    recaptcha_secret = os.getenv("RECAPTCHA_SECRET_KEY", "test_secret_key")
    return LeadCaptureService(db, recaptcha_secret=recaptcha_secret)


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

        # Capture lead
        result = await service.capture_lead(
            request=request,
            client_ip=client_ip,
        )

        return LeadCaptureResponse(
            lead_id=result["lead_id"],
            tier=result["tier"],
            score=result["score"],
            message="Лид успешно создан",
        )
    except RateLimitExceeded as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to capture lead: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to capture lead",
        )
