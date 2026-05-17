"""Onboarding API Endpoints

FastAPI endpoints for clinic onboarding workflow.

Part of: Phase 11 Sprint 3 - Task 3.4
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from aim.database import get_db
from aim.schemas.onboarding import (
    OnboardingStartRequest,
    OnboardingStartResponse,
    OnboardingStatusResponse,
    OnboardingDocumentUploadRequest,
    OnboardingDocumentUploadResponse,
    OnboardingPaymentRequest,
    OnboardingPaymentResponse,
    OnboardingCompleteResponse,
    OnboardingRetryRequest,
    OnboardingRetryResponse,
    OnboardingProgressResponse,
    OnboardingNextStep,
)
from aim.services.onboarding.onboarding_service import OnboardingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


def get_onboarding_service(db: AsyncSession = Depends(get_db)) -> OnboardingService:
    """Dependency to get OnboardingService instance."""
    return OnboardingService(db)


@router.post("/start", response_model=OnboardingStartResponse, status_code=status.HTTP_201_CREATED)
async def start_onboarding(
    request: OnboardingStartRequest,
    service: OnboardingService = Depends(get_onboarding_service),
) -> OnboardingStartResponse:
    """Start onboarding workflow for a lead.

    Creates an Onboarding record in DOCUMENTS_PENDING state.

    Args:
        request: Start request with lead_id
        service: OnboardingService instance

    Returns:
        OnboardingStartResponse with onboarding_id and initial state

    Raises:
        HTTPException 404: Lead not found
        HTTPException 409: Onboarding already exists for lead
        HTTPException 500: Internal server error
    """
    try:
        onboarding = await service.start_onboarding(request.lead_id)

        return OnboardingStartResponse(
            onboarding_id=onboarding.id,
            lead_id=onboarding.lead_id,
            state=onboarding.state,
            progress=onboarding.progress,
            message="Онбординг начат. Загрузите необходимые документы.",
        )
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        elif "already exists" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
    except Exception as e:
        logger.error(f"Failed to start onboarding: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start onboarding",
        )


@router.get("/{onboarding_id}/status", response_model=OnboardingStatusResponse)
async def get_onboarding_status(
    onboarding_id: str,
    service: OnboardingService = Depends(get_onboarding_service),
) -> OnboardingStatusResponse:
    """Get onboarding status with progress and next steps.

    Args:
        onboarding_id: Onboarding ID
        service: OnboardingService instance

    Returns:
        OnboardingStatusResponse with current state and next steps

    Raises:
        HTTPException 404: Onboarding not found
        HTTPException 500: Internal server error
    """
    try:
        status_data = await service.get_onboarding_status(onboarding_id)

        return OnboardingStatusResponse(**status_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to get onboarding status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get onboarding status",
        )


@router.post(
    "/{onboarding_id}/documents",
    response_model=OnboardingDocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_onboarding_document(
    onboarding_id: str,
    document_type: str,
    file: UploadFile = File(...),
    service: OnboardingService = Depends(get_onboarding_service),
) -> OnboardingDocumentUploadResponse:
    """Upload document during onboarding.

    Validates document type, uploads file, processes with OCR and AI extraction.

    Args:
        onboarding_id: Onboarding ID
        document_type: Document type (license, inn, ogrn, contract)
        file: Uploaded file
        service: OnboardingService instance

    Returns:
        OnboardingDocumentUploadResponse with document_id and updated state

    Raises:
        HTTPException 400: Invalid document type or file
        HTTPException 404: Onboarding not found
        HTTPException 409: Invalid state transition
        HTTPException 500: Internal server error
    """
    # Validate document type
    valid_types = ["license", "inn", "ogrn", "contract"]
    if document_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document type. Must be one of: {', '.join(valid_types)}",
        )

    # Validate file type
    allowed_types = ["application/pdf", "image/jpeg", "image/png", "image/tiff"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: PDF, JPEG, PNG, TIFF",
        )

    try:
        # Read file content
        file_content = await file.read()

        # Upload document
        document = await service.upload_document(
            onboarding_id=onboarding_id,
            document_type=document_type,
            file_content=file_content,
            filename=file.filename or "document",
        )

        # Get updated onboarding
        status_data = await service.get_onboarding_status(onboarding_id)

        return OnboardingDocumentUploadResponse(
            onboarding_id=onboarding_id,
            document_id=document.id,
            document_type=document_type,
            state=status_data["state"],
            progress=status_data["progress"],
            message=f"Документ '{document_type}' загружен и обрабатывается.",
        )
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        elif "transition" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
    except Exception as e:
        logger.error(f"Failed to upload document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document",
        )


@router.post("/{onboarding_id}/payment", response_model=OnboardingPaymentResponse)
async def process_onboarding_payment(
    onboarding_id: str,
    request: OnboardingPaymentRequest,
    service: OnboardingService = Depends(get_onboarding_service),
) -> OnboardingPaymentResponse:
    """Process onboarding payment.

    Validates documents are complete, processes payment via PaymentService.

    Args:
        onboarding_id: Onboarding ID
        request: Payment request with amount and payment details
        service: OnboardingService instance

    Returns:
        OnboardingPaymentResponse with payment_id and updated state

    Raises:
        HTTPException 400: Invalid payment data or documents not validated
        HTTPException 404: Onboarding not found
        HTTPException 409: Invalid state transition
        HTTPException 500: Internal server error
    """
    try:
        payment = await service.process_payment(
            onboarding_id=onboarding_id,
            payment_data=request.model_dump(),
        )

        # Get updated onboarding
        status_data = await service.get_onboarding_status(onboarding_id)

        return OnboardingPaymentResponse(
            onboarding_id=onboarding_id,
            payment_id=payment.id,
            payment_status=payment.status,
            state=status_data["state"],
            progress=status_data["progress"],
            message="Платёж обрабатывается.",
        )
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        elif "transition" in str(e).lower() or "not validated" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
    except Exception as e:
        logger.error(f"Failed to process payment: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process payment",
        )


@router.post("/{onboarding_id}/complete", response_model=OnboardingCompleteResponse)
async def complete_onboarding(
    onboarding_id: str,
    service: OnboardingService = Depends(get_onboarding_service),
) -> OnboardingCompleteResponse:
    """Complete onboarding workflow.

    Validates payment is completed, transitions to ONBOARDING_COMPLETE state.

    Args:
        onboarding_id: Onboarding ID
        service: OnboardingService instance

    Returns:
        OnboardingCompleteResponse with completion timestamp

    Raises:
        HTTPException 404: Onboarding not found
        HTTPException 409: Invalid state transition or payment not completed
        HTTPException 500: Internal server error
    """
    try:
        onboarding = await service.complete_onboarding(onboarding_id)

        return OnboardingCompleteResponse(
            onboarding_id=onboarding.id,
            lead_id=onboarding.lead_id,
            state=onboarding.state,
            progress=onboarding.progress,
            completed_at=onboarding.completed_at,
            message="Онбординг успешно завершён!",
        )
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )
    except Exception as e:
        logger.error(f"Failed to complete onboarding: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete onboarding",
        )


@router.post("/{onboarding_id}/retry", response_model=OnboardingRetryResponse)
async def retry_onboarding_step(
    onboarding_id: str,
    request: OnboardingRetryRequest,
    service: OnboardingService = Depends(get_onboarding_service),
) -> OnboardingRetryResponse:
    """Retry failed onboarding step.

    Resets onboarding to appropriate state for retry.

    Args:
        onboarding_id: Onboarding ID
        request: Retry request with step to retry
        service: OnboardingService instance

    Returns:
        OnboardingRetryResponse with updated state

    Raises:
        HTTPException 404: Onboarding not found
        HTTPException 409: Invalid state for retry
        HTTPException 500: Internal server error
    """
    try:
        onboarding = await service.retry_failed_step(
            onboarding_id=onboarding_id,
            step=request.step,
        )

        return OnboardingRetryResponse(
            onboarding_id=onboarding.id,
            step=request.step,
            state=onboarding.state,
            progress=onboarding.progress,
            message=f"Шаг '{request.step}' сброшен для повторной попытки.",
        )
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )
    except Exception as e:
        logger.error(f"Failed to retry step: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retry step",
        )


@router.get("/lead/{lead_id}", response_model=OnboardingStatusResponse)
async def get_onboarding_by_lead(
    lead_id: str,
    service: OnboardingService = Depends(get_onboarding_service),
) -> OnboardingStatusResponse:
    """Get onboarding for a lead.

    Args:
        lead_id: Lead ID
        service: OnboardingService instance

    Returns:
        OnboardingStatusResponse with current state and next steps

    Raises:
        HTTPException 404: Onboarding not found for lead
        HTTPException 500: Internal server error
    """
    try:
        onboarding = await service.get_onboarding_by_lead(lead_id)
        status_data = await service.get_onboarding_status(onboarding.id)

        return OnboardingStatusResponse(**status_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to get onboarding by lead: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get onboarding by lead",
        )
