"""Document Processing Service

Orchestrates the complete document processing pipeline:
OCR → AI Extraction → Validation → Storage

Part of: Phase 11 Sprint 3 - Task 3.3
"""

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from aim.models.document import Document
from aim.schemas.document import ExtractedData, ValidationResult
from aim.services.documents.ai_extractor import AIExtractor
from aim.services.documents.ocr_service import OCRService
from aim.services.documents.validator import DocumentValidator

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Service for processing uploaded documents.

    Pipeline:
    1. OCR: Extract text from image/PDF
    2. AI Extraction: Parse structured data from text
    3. Validation: Verify data integrity and checksums
    4. Storage: Save to database with status
    """

    def __init__(
        self,
        ocr_service: OCRService,
        ai_extractor: AIExtractor,
        validator: DocumentValidator,
    ):
        """Initialize document processor.

        Args:
            ocr_service: OCR service instance
            ai_extractor: AI extraction service instance
            validator: Validation service instance
        """
        self.ocr_service = ocr_service
        self.ai_extractor = ai_extractor
        self.validator = validator

    async def process_document(
        self,
        document: Document,
        file_path: str,
        db: AsyncSession,
    ) -> Document:
        """Process document through complete pipeline.

        Args:
            document: Document model instance
            file_path: Path to uploaded file
            db: Database session

        Returns:
            Updated document with processing results

        Raises:
            FileNotFoundError: If file not found
            RuntimeError: If processing fails
        """
        logger.info(f"Processing document {document.id} ({document.document_type})")

        try:
            # Update status to processing
            document.status = "processing"
            await db.commit()

            # Step 1: OCR - Extract text
            ocr_text = await self._extract_text(file_path)
            document.ocr_text = ocr_text
            await db.commit()

            logger.info(f"OCR extracted {len(ocr_text)} characters")

            # Step 2: AI Extraction - Parse structured data
            extracted_data, confidence = await self._extract_data(
                ocr_text, document.document_type
            )
            document.extracted_data = extracted_data.model_dump()
            document.confidence_score = confidence
            await db.commit()

            logger.info(
                f"AI extracted data with confidence {confidence:.2f}"
            )

            # Step 3: Validation - Verify data
            validation_result = self._validate_data(
                extracted_data, document.document_type, confidence
            )
            document.validation_errors = validation_result.errors
            await db.commit()

            logger.info(
                f"Validation: valid={validation_result.is_valid}, "
                f"errors={len(validation_result.errors)}, "
                f"warnings={len(validation_result.warnings)}"
            )

            # Step 4: Determine final status
            document.status = "completed"
            document.processed_at = datetime.now(timezone.utc)

            if validation_result.is_valid:
                document.validation_status = "valid"
            elif validation_result.errors:
                document.validation_status = "invalid"
            else:
                document.validation_status = "needs_review"

            await db.commit()

            logger.info(
                f"Document {document.id} processed successfully: "
                f"status={document.validation_status}"
            )

            return document

        except Exception as e:
            logger.error(f"Document processing failed: {e}")

            # Update status to failed
            document.status = "failed"
            document.validation_errors = [str(e)]
            await db.commit()

            raise RuntimeError(f"Document processing failed: {e}")

    async def _extract_text(self, file_path: str) -> str:
        """Extract text from file using OCR.

        Args:
            file_path: Path to file

        Returns:
            Extracted text

        Raises:
            FileNotFoundError: If file not found
            RuntimeError: If OCR fails
        """
        # Check file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Determine file type
        file_ext = Path(file_path).suffix.lower()

        # Extract text based on file type
        if file_ext == ".pdf":
            return await self.ocr_service.extract_text_from_pdf(file_path)
        elif file_ext in (".jpg", ".jpeg", ".png", ".tiff", ".tif"):
            return await self.ocr_service.extract_text_from_image(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")

    async def _extract_data(
        self, text: str, document_type: str
    ) -> Tuple[ExtractedData, float]:
        """Extract structured data from text using AI.

        Args:
            text: OCR extracted text
            document_type: Document type

        Returns:
            Tuple of (extracted_data, confidence_score)

        Raises:
            RuntimeError: If AI extraction fails
        """
        return await self.ai_extractor.extract_from_text(text, document_type)

    def _validate_data(
        self,
        data: ExtractedData,
        document_type: str,
        confidence_score: float,
    ) -> ValidationResult:
        """Validate extracted data.

        Args:
            data: Extracted data
            document_type: Document type
            confidence_score: AI extraction confidence

        Returns:
            Validation result
        """
        return self.validator.validate_extracted_data(
            data, document_type, confidence_score
        )

    async def reprocess_document(
        self,
        document: Document,
        db: AsyncSession,
    ) -> Document:
        """Reprocess existing document.

        Useful for:
        - Retrying failed processing
        - Reprocessing with updated AI models
        - Manual review corrections

        Args:
            document: Document to reprocess
            db: Database session

        Returns:
            Updated document

        Raises:
            FileNotFoundError: If original file not found
            RuntimeError: If reprocessing fails
        """
        logger.info(f"Reprocessing document {document.id}")

        # Reset status
        document.status = "pending"
        document.ocr_text = None
        document.extracted_data = None
        document.confidence_score = None
        document.validation_status = None
        document.validation_errors = None
        document.processed_at = None
        await db.commit()

        # Process again
        return await self.process_document(
            document, document.file_path, db
        )

    def get_processing_stats(self, document: Document) -> dict:
        """Get processing statistics for document.

        Args:
            document: Processed document

        Returns:
            Statistics dictionary
        """
        stats = {
            "document_id": document.id,
            "document_type": document.document_type,
            "status": document.status,
            "validation_status": document.validation_status,
            "confidence_score": document.confidence_score,
            "ocr_text_length": len(document.ocr_text) if document.ocr_text else 0,
            "fields_extracted": 0,
            "errors_count": len(document.validation_errors or []),
            "processing_time": None,
        }

        # Count extracted fields
        if document.extracted_data:
            stats["fields_extracted"] = sum(
                1 for v in document.extracted_data.values() if v is not None
            )

        # Calculate processing time
        if document.processed_at and document.uploaded_at:
            delta = document.processed_at - document.uploaded_at
            stats["processing_time"] = delta.total_seconds()

        return stats
