"""Tests for Document API Endpoints

Tests document upload, status retrieval, and listing endpoints.

Part of: Phase 11 Sprint 3 - Task 3.3
"""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from io import BytesIO

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from aim.models.document import Document
from aim.models.lead import Lead
from aim.schemas.document import (
    DocumentUploadResponse,
    DocumentStatusResponse,
    ExtractedData,
)


# Fixtures

@pytest.fixture
def mock_lead():
    """Mock lead instance."""
    return Lead(
        id="lead_123",
        email="test@example.com",
        clinic_name="Test Clinic",
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def mock_document():
    """Mock document instance."""
    return Document(
        id="doc_20260517_abc123",
        lead_id="lead_123",
        document_type="license",
        file_path="/tmp/uploads/lead_123/license_abc123.pdf",
        file_name="license.pdf",
        file_size=1024,
        mime_type="application/pdf",
        status="completed",
        validation_status="valid",
        confidence_score=0.85,
        created_by="api",
        uploaded_at=datetime.utcnow(),
        processed_at=datetime.utcnow(),
        extracted_data={
            "license_number": "ЛО-77-01-012345",
            "clinic_name": "Test Clinic",
            "inn": "7707083893",
        },
        validation_errors=[],
    )


@pytest.fixture
def sample_pdf_file():
    """Sample PDF file for upload."""
    content = b"%PDF-1.4\n%Test PDF content\n"
    return UploadFile(
        filename="test_license.pdf",
        file=BytesIO(content),
        content_type="application/pdf",
    )


# Upload Endpoint Tests

@pytest.mark.asyncio
async def test_upload_document_success(mock_lead, sample_pdf_file, tmp_path):
    """Test successful document upload."""
    from aim.api.documents import upload_document

    # Mock database
    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_lead

    # Mock processor
    mock_processor = AsyncMock()
    processed_doc = Document(
        id="doc_20260517_abc123",
        lead_id="lead_123",
        document_type="license",
        file_path=str(tmp_path / "license.pdf"),
        file_name="test_license.pdf",
        file_size=len(await sample_pdf_file.read()),
        mime_type="application/pdf",
        status="completed",
        created_by="api",
        uploaded_at=datetime.utcnow(),
    )
    await sample_pdf_file.seek(0)  # Reset file pointer
    mock_processor.process_document.return_value = processed_doc

    # Mock settings
    with patch("aim.api.documents.get_settings") as mock_settings:
        mock_settings.return_value.upload_dir = str(tmp_path)

        # Upload document
        response = await upload_document(
            file=sample_pdf_file,
            lead_id="lead_123",
            document_type="license",
            db=mock_db,
            processor=mock_processor,
        )

        assert isinstance(response, DocumentUploadResponse)
        assert response.document_id == "doc_20260517_abc123"
        assert response.status == "completed"
        mock_processor.process_document.assert_called_once()


@pytest.mark.asyncio
async def test_upload_document_invalid_type(mock_lead, sample_pdf_file):
    """Test upload with invalid document type."""
    from aim.api.documents import upload_document
    from fastapi import HTTPException

    mock_db = AsyncMock(spec=AsyncSession)
    mock_processor = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await upload_document(
            file=sample_pdf_file,
            lead_id="lead_123",
            document_type="invalid_type",
            db=mock_db,
            processor=mock_processor,
        )

    assert exc_info.value.status_code == 400
    assert "Invalid document type" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_upload_document_lead_not_found(sample_pdf_file):
    """Test upload with non-existent lead."""
    from aim.api.documents import upload_document
    from fastapi import HTTPException

    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.execute.return_value.scalar_one_or_none.return_value = None
    mock_processor = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await upload_document(
            file=sample_pdf_file,
            lead_id="nonexistent_lead",
            document_type="license",
            db=mock_db,
            processor=mock_processor,
        )

    assert exc_info.value.status_code == 404
    assert "Lead not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_upload_document_invalid_file_type(mock_lead):
    """Test upload with invalid file extension."""
    from aim.api.documents import upload_document
    from fastapi import HTTPException

    # Create file with invalid extension
    invalid_file = UploadFile(
        filename="test.exe",
        file=BytesIO(b"invalid content"),
        content_type="application/x-msdownload",
    )

    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_lead
    mock_processor = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await upload_document(
            file=invalid_file,
            lead_id="lead_123",
            document_type="license",
            db=mock_db,
            processor=mock_processor,
        )

    assert exc_info.value.status_code == 400
    assert "File type not allowed" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_upload_document_file_too_large(mock_lead):
    """Test upload with file exceeding size limit."""
    from aim.api.documents import upload_document
    from fastapi import HTTPException

    # Create large file (> 10 MB)
    large_content = b"x" * (11 * 1024 * 1024)
    large_file = UploadFile(
        filename="large.pdf",
        file=BytesIO(large_content),
        content_type="application/pdf",
    )

    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_lead
    mock_processor = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await upload_document(
            file=large_file,
            lead_id="lead_123",
            document_type="license",
            db=mock_db,
            processor=mock_processor,
        )

    assert exc_info.value.status_code == 413
    assert "File too large" in str(exc_info.value.detail)


# Status Endpoint Tests

@pytest.mark.asyncio
async def test_get_document_status_success(mock_document):
    """Test successful document status retrieval."""
    from aim.api.documents import get_document_status

    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_document

    response = await get_document_status(
        document_id="doc_20260517_abc123",
        db=mock_db,
    )

    assert isinstance(response, DocumentStatusResponse)
    assert response.document_id == "doc_20260517_abc123"
    assert response.status == "completed"
    assert response.extracted_data is not None
    assert response.validation_result is not None


@pytest.mark.asyncio
async def test_get_document_status_not_found():
    """Test status retrieval for non-existent document."""
    from aim.api.documents import get_document_status
    from fastapi import HTTPException

    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await get_document_status(
            document_id="nonexistent_doc",
            db=mock_db,
        )

    assert exc_info.value.status_code == 404
    assert "Document not found" in str(exc_info.value.detail)


# List Endpoint Tests

@pytest.mark.asyncio
async def test_list_lead_documents_success(mock_lead, mock_document):
    """Test successful document listing."""
    from aim.api.documents import list_lead_documents
    from aim.schemas.document import DocumentListResponse

    mock_db = AsyncMock(spec=AsyncSession)

    # Mock lead query
    lead_result = AsyncMock()
    lead_result.scalar_one_or_none.return_value = mock_lead

    # Mock documents query
    docs_result = AsyncMock()
    docs_result.scalars.return_value.all.return_value = [mock_document]

    mock_db.execute.side_effect = [lead_result, docs_result]

    response = await list_lead_documents(
        lead_id="lead_123",
        db=mock_db,
    )

    assert isinstance(response, DocumentListResponse)
    assert response.total == 1
    assert len(response.documents) == 1
    assert response.documents[0].document_id == "doc_20260517_abc123"


@pytest.mark.asyncio
async def test_list_lead_documents_with_filter(mock_lead, mock_document):
    """Test document listing with type filter."""
    from aim.api.documents import list_lead_documents

    mock_db = AsyncMock(spec=AsyncSession)

    lead_result = AsyncMock()
    lead_result.scalar_one_or_none.return_value = mock_lead

    docs_result = AsyncMock()
    docs_result.scalars.return_value.all.return_value = [mock_document]

    mock_db.execute.side_effect = [lead_result, docs_result]

    response = await list_lead_documents(
        lead_id="lead_123",
        document_type="license",
        db=mock_db,
    )

    assert response.total == 1


@pytest.mark.asyncio
async def test_list_lead_documents_lead_not_found():
    """Test listing for non-existent lead."""
    from aim.api.documents import list_lead_documents
    from fastapi import HTTPException

    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await list_lead_documents(
            lead_id="nonexistent_lead",
            db=mock_db,
        )

    assert exc_info.value.status_code == 404
    assert "Lead not found" in str(exc_info.value.detail)


# Reprocess Endpoint Tests

@pytest.mark.asyncio
async def test_reprocess_document_success(mock_document):
    """Test successful document reprocessing."""
    from aim.api.documents import reprocess_document

    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_document

    mock_processor = AsyncMock()
    reprocessed_doc = mock_document
    reprocessed_doc.status = "completed"
    mock_processor.reprocess_document.return_value = reprocessed_doc

    response = await reprocess_document(
        document_id="doc_20260517_abc123",
        db=mock_db,
        processor=mock_processor,
    )

    assert isinstance(response, DocumentUploadResponse)
    assert response.document_id == "doc_20260517_abc123"
    assert response.status == "completed"
    mock_processor.reprocess_document.assert_called_once()


@pytest.mark.asyncio
async def test_reprocess_document_not_found():
    """Test reprocessing non-existent document."""
    from aim.api.documents import reprocess_document
    from fastapi import HTTPException

    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.execute.return_value.scalar_one_or_none.return_value = None
    mock_processor = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await reprocess_document(
            document_id="nonexistent_doc",
            db=mock_db,
            processor=mock_processor,
        )

    assert exc_info.value.status_code == 404
    assert "Document not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_reprocess_document_failure(mock_document):
    """Test reprocessing failure."""
    from aim.api.documents import reprocess_document
    from fastapi import HTTPException

    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_document

    mock_processor = AsyncMock()
    mock_processor.reprocess_document.side_effect = RuntimeError("Processing failed")

    with pytest.raises(HTTPException) as exc_info:
        await reprocess_document(
            document_id="doc_20260517_abc123",
            db=mock_db,
            processor=mock_processor,
        )

    assert exc_info.value.status_code == 500
    assert "Reprocessing failed" in str(exc_info.value.detail)
