"""Document Processing API Endpoints

FastAPI routes for document upload, processing, and status tracking.

Part of: Phase 11 Sprint 3 - Task 3.3
"""

import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aim.config.settings import get_api_settings
from aim.database import get_db
from aim.models.document import Document
from aim.models.lead import Lead
from aim.schemas.document import (
    DocumentListResponse,
    DocumentStatusResponse,
    DocumentUploadResponse,
)
from aim.services.documents.ai_extractor import AIExtractor
from aim.services.documents.ocr_service import OCRService
from aim.services.documents.processor import DocumentProcessor
from aim.services.documents.validator import DocumentValidator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])

# Allowed file types
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".tif"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def get_document_processor() -> DocumentProcessor:
    """Get document processor instance.

    Returns:
        DocumentProcessor instance
    """
    settings = get_api_settings(skip_validation=True)

    ocr_service = OCRService(lang="rus")
    ai_extractor = AIExtractor(
        api_key=settings.omni_route_key,
        base_url=settings.omni_route_url,
        model="claude-sonnet-4-20250514",
    )
    validator = DocumentValidator()

    return DocumentProcessor(ocr_service, ai_extractor, validator)


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    lead_id: str = Form(...),
    document_type: str = Form(...),
    db: AsyncSession = Depends(get_db),
    processor: DocumentProcessor = Depends(get_document_processor),
) -> DocumentUploadResponse:
    """Upload and process document.

    Args:
        file: Uploaded file
        lead_id: Lead ID
        document_type: Document type (license, inn, ogrn, contract)
        db: Database session
        processor: Document processor

    Returns:
        Upload response with document ID and status

    Raises:
        HTTPException: If validation fails or processing errors
    """
    logger.info(
        f"Document upload: lead_id={lead_id}, "
        f"type={document_type}, file={file.filename}"
    )

    # Validate document type
    if document_type not in ("license", "inn", "ogrn", "contract"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document type: {document_type}",
        )

    # Validate lead exists
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead not found: {lead_id}",
        )

    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed: {file_ext}. "
            f"Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Read file content
    content = await file.read()

    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large: {len(content)} bytes. "
            f"Max: {MAX_FILE_SIZE} bytes",
        )

    # Create upload directory
    settings = get_api_settings(skip_validation=True)
    upload_dir = Path(settings.upload_dir) / lead_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    file_id = uuid.uuid4().hex[:8]
    safe_filename = f"{document_type}_{file_id}{file_ext}"
    file_path = upload_dir / safe_filename

    # Save file
    with open(file_path, "wb") as f:
        f.write(content)

    logger.info(f"File saved: {file_path}")

    # Create document record
    document = Document(
        id=Document.generate_id(),
        lead_id=lead_id,
        document_type=document_type,
        file_path=str(file_path),
        file_name=file.filename,
        file_size=len(content),
        mime_type=file.content_type or "application/octet-stream",
        status="pending",
        created_by="api",
        uploaded_at=datetime.now(timezone.utc),
    )

    db.add(document)
    await db.commit()
    await db.refresh(document)

    logger.info(f"Document created: {document.id}")

    # Process document asynchronously
    try:
        document = await processor.process_document(document, str(file_path), db)

        return DocumentUploadResponse(
            document_id=document.id,
            status=document.status,
            message="Document uploaded and processed successfully",
        )

    except Exception as e:
        logger.error(f"Document processing failed: {e}")

        return DocumentUploadResponse(
            document_id=document.id,
            status="failed",
            message="Document uploaded but processing failed",
        )


@router.get("/{document_id}", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: str,
    db: AsyncSession = Depends(get_db),
) -> DocumentStatusResponse:
    """Get document processing status.

    Args:
        document_id: Document ID
        db: Database session

    Returns:
        Document status with extracted data and validation

    Raises:
        HTTPException: If document not found
    """
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )

    # Build response
    response = DocumentStatusResponse(
        document_id=document.id,
        status=document.status,
        document_type=document.document_type,
        file_name=document.file_name,
        file_size=document.file_size,
        uploaded_at=document.uploaded_at,
        processed_at=document.processed_at,
    )

    # Add extracted data if available
    if document.extracted_data:
        from aim.schemas.document import ExtractedData

        response.extracted_data = ExtractedData(**document.extracted_data)

    # Add validation result if available
    if document.validation_status:
        from aim.schemas.document import ValidationResult

        response.validation_result = ValidationResult(
            is_valid=document.validation_status == "valid",
            confidence_score=document.confidence_score or 0.0,
            errors=document.validation_errors or [],
            warnings=[],
        )

    return response


@router.get("/lead/{lead_id}", response_model=DocumentListResponse)
async def list_lead_documents(
    lead_id: str,
    document_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    """List all documents for a lead.

    Args:
        lead_id: Lead ID
        document_type: Optional filter by document type
        db: Database session

    Returns:
        List of documents

    Raises:
        HTTPException: If lead not found
    """
    # Validate lead exists
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead not found: {lead_id}",
        )

    # Build query
    query = select(Document).where(Document.lead_id == lead_id)

    if document_type:
        query = query.where(Document.document_type == document_type)

    query = query.order_by(Document.uploaded_at.desc())

    # Execute query
    result = await db.execute(query)
    documents = result.scalars().all()

    # Build response
    document_responses = []
    for doc in documents:
        doc_response = DocumentStatusResponse(
            document_id=doc.id,
            status=doc.status,
            document_type=doc.document_type,
            file_name=doc.file_name,
            file_size=doc.file_size,
            uploaded_at=doc.uploaded_at,
            processed_at=doc.processed_at,
        )

        # Add extracted data if available
        if doc.extracted_data:
            from aim.schemas.document import ExtractedData

            doc_response.extracted_data = ExtractedData(**doc.extracted_data)

        # Add validation result if available
        if doc.validation_status:
            from aim.schemas.document import ValidationResult

            doc_response.validation_result = ValidationResult(
                is_valid=doc.validation_status == "valid",
                confidence_score=doc.confidence_score or 0.0,
                errors=doc.validation_errors or [],
                warnings=[],
            )

        document_responses.append(doc_response)

    return DocumentListResponse(
        documents=document_responses,
        total=len(document_responses),
    )


@router.post("/{document_id}/reprocess", response_model=DocumentUploadResponse)
async def reprocess_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    processor: DocumentProcessor = Depends(get_document_processor),
) -> DocumentUploadResponse:
    """Reprocess existing document.

    Args:
        document_id: Document ID
        db: Database session
        processor: Document processor

    Returns:
        Reprocessing response

    Raises:
        HTTPException: If document not found or reprocessing fails
    """
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )

    try:
        document = await processor.reprocess_document(document, db)

        return DocumentUploadResponse(
            document_id=document.id,
            status=document.status,
            message="Document reprocessed successfully",
        )

    except Exception as e:
        logger.error(f"Document reprocessing failed: {e}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document reprocessing failed",
        )
