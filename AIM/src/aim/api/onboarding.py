"""Onboarding API Endpoints

FastAPI endpoints for clinic onboarding workflow.

Part of: Phase 11 Sprint 3 - Task 3.4
"""

import logging
import os
import tempfile
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.aim.database import get_db
from src.aim.schemas.onboarding import (
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
from src.aim.services.documents.ai_extractor import AIExtractor
from src.aim.services.documents.ocr_service import OCRService
from src.aim.services.documents.processor import DocumentProcessor
from src.aim.services.documents.validator import DocumentValidator
from src.aim.services.onboarding.onboarding_service import OnboardingService
from src.aim.services.payment.yookassa_client import YooKassaClient
from src.aim.services.payment.payment_service import PaymentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


def get_onboarding_service(db: AsyncSession = Depends(get_db)) -> OnboardingService:
    """Dependency to get OnboardingService instance with full dependency chain."""
    ocr = OCRService()
    extractor = AIExtractor(
        api_key=os.getenv("DEEPSEEK_API_KEY", ""),
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
    )
    validator = DocumentValidator()
    doc_processor = DocumentProcessor(ocr, extractor, validator)

    yookassa = YooKassaClient(
        account_id=os.getenv("YOOKASSA_SHOP_ID", ""),
        secret_key=os.getenv("YOOKASSA_SECRET_KEY", ""),
        test_mode=os.getenv("ENVIRONMENT", "development") != "production",
    )
    payment = PaymentService(db_session=db, yookassa_client=yookassa)

    return OnboardingService(document_processor=doc_processor, payment_service=payment)


@router.post("/start", response_model=OnboardingStartResponse, status_code=status.HTTP_201_CREATED)
async def start_onboarding(
    request: OnboardingStartRequest,
    db: AsyncSession = Depends(get_db),
    service: OnboardingService = Depends(get_onboarding_service),
) -> OnboardingStartResponse:
    """Start onboarding workflow for a lead.

    Creates an Onboarding record in DOCUMENTS_PENDING state.
    """
    try:
        onboarding = await service.start_onboarding(request.lead_id, db)

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
    db: AsyncSession = Depends(get_db),
    service: OnboardingService = Depends(get_onboarding_service),
) -> OnboardingStatusResponse:
    """Get onboarding status with progress and next steps."""
    try:
        status_data = await service.get_onboarding_status(onboarding_id, db)

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
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(...),
    service: OnboardingService = Depends(get_onboarding_service),
) -> OnboardingDocumentUploadResponse:
    """Upload document during onboarding.

    Validates document type, uploads file, processes with OCR and AI extraction.
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
        # Save uploaded file to temp location
        suffix = os.path.splitext(file.filename or "document")[1] or ".pdf"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            file_path = tmp.name

        # Upload document
        onboarding, document = await service.upload_document(
            onboarding_id=onboarding_id,
            document_type=document_type,
            file_path=file_path,
            db=db,
        )

        return OnboardingDocumentUploadResponse(
            onboarding_id=onboarding_id,
            document_id=document.id,
            document_type=document_type,
            state=onboarding.state,
            progress=onboarding.progress,
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
    db: AsyncSession = Depends(get_db),
    service: OnboardingService = Depends(get_onboarding_service),
) -> OnboardingPaymentResponse:
    """Process onboarding payment.

    Validates documents are complete, processes payment via PaymentService.
    """
    try:
        onboarding, payment = await service.process_payment(
            onboarding_id=onboarding_id,
            payment_data=request.model_dump(),
            db=db,
        )

        return OnboardingPaymentResponse(
            onboarding_id=onboarding_id,
            payment_id=payment.id,
            payment_status=payment.status,
            state=onboarding.state,
            progress=onboarding.progress,
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
    db: AsyncSession = Depends(get_db),
    service: OnboardingService = Depends(get_onboarding_service),
) -> OnboardingCompleteResponse:
    """Complete onboarding workflow.

    Validates payment is completed, transitions to ONBOARDING_COMPLETE state.
    """
    try:
        onboarding = await service.complete_onboarding(onboarding_id, db)

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
    db: AsyncSession = Depends(get_db),
    service: OnboardingService = Depends(get_onboarding_service),
) -> OnboardingRetryResponse:
    """Retry failed onboarding step.

    Resets onboarding to appropriate state for retry.
    """
    try:
        onboarding = await service.retry_failed_step(
            onboarding_id=onboarding_id,
            step=request.step,
            db=db,
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
    db: AsyncSession = Depends(get_db),
    service: OnboardingService = Depends(get_onboarding_service),
) -> OnboardingStatusResponse:
    """Get onboarding for a lead."""
    try:
        onboarding = await service.get_onboarding_by_lead(lead_id, db)
        if not onboarding:
            raise ValueError(f"Onboarding not found for lead: {lead_id}")
        status_data = await service.get_onboarding_status(onboarding.id, db)

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
