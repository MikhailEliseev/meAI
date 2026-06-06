"""Tests for Document Processing Services

Tests OCR, AI extraction, validation, and complete processing pipeline.

Part of: Phase 11 Sprint 3 - Task 3.3
"""

import os
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from src.aim.models.document import Document
from src.aim.schemas.document import ExtractedData, ValidationResult
from src.aim.services.documents.ai_extractor import AIExtractor
from src.aim.services.documents.ocr_service import OCRService
from src.aim.services.documents.processor import DocumentProcessor
from src.aim.services.documents.validator import DocumentValidator


# Fixtures

@pytest.fixture
def sample_ocr_text() -> str:
    """Sample OCR extracted text."""
    return """
    ЛИЦЕНЗИЯ
    Номер: ЛО-77-01-012345
    Дата выдачи: 15.03.2024

    Организация: ООО "Стоматологическая клиника Здоровье"
    Адрес: г. Москва, ул. Ленина, д. 10
    ИНН: 7701234567
    ОГРН: 1027700123456
    КПП: 770101001

    Руководитель: Иванов Иван Иванович
    Должность: Генеральный директор
    """


@pytest.fixture
def sample_extracted_data() -> ExtractedData:
    """Sample extracted data."""
    return ExtractedData(
        license_number="ЛО-77-01-012345",
        license_date="15.03.2024",
        clinic_name="ООО \"Стоматологическая клиника Здоровье\"",
        clinic_address="г. Москва, ул. Ленина, д. 10",
        inn="7701234567",
        ogrn="1027700123456",
        kpp="770101001",
        director_name="Иванов Иван Иванович",
        director_position="Генеральный директор",
    )


@pytest.fixture
def mock_document() -> Document:
    """Mock document instance."""
    return Document(
        id="doc_20260517_abc123",
        lead_id="lead_123",
        document_type="license",
        file_path="/tmp/test_license.pdf",
        file_name="license.pdf",
        file_size=1024,
        mime_type="application/pdf",
        status="pending",
        created_by="test",
        uploaded_at=datetime.utcnow(),
    )


# OCR Service Tests

@pytest.mark.asyncio
async def test_ocr_service_initialization():
    """Test OCR service initialization."""
    with patch("src.aim.services.documents.ocr_service.pytesseract") as mock_tess:
        mock_tess.get_tesseract_version.return_value = "5.0.0"
        mock_tess.get_languages.return_value = ["eng", "rus"]

        service = OCRService(lang="rus")

        assert service.lang == "rus"
        mock_tess.get_tesseract_version.assert_called_once()
        mock_tess.get_languages.assert_called_once()


@pytest.mark.asyncio
async def test_ocr_extract_text_from_image(tmp_path, sample_ocr_text):
    """Test OCR text extraction from image."""
    # Create test image
    from PIL import Image

    image_path = tmp_path / "test.png"
    img = Image.new("RGB", (800, 600), color="white")
    img.save(image_path)

    with patch("src.aim.services.documents.ocr_service.pytesseract") as mock_tess:
        mock_tess.get_tesseract_version.return_value = "5.0.0"
        mock_tess.get_languages.return_value = ["eng", "rus"]
        mock_tess.image_to_string.return_value = sample_ocr_text

        service = OCRService(lang="rus")
        text = await service.extract_text_from_image(str(image_path))

        assert len(text) > 0
        assert "ЛИЦЕНЗИЯ" in text
        mock_tess.image_to_string.assert_called_once()


@pytest.mark.asyncio
async def test_ocr_extract_text_from_pdf(tmp_path, sample_ocr_text):
    """Test OCR text extraction from PDF."""
    pdf_path = tmp_path / "test.pdf"

    # Mock PDF conversion
    with patch("src.aim.services.documents.ocr_service.convert_from_path") as mock_convert:
        with patch("src.aim.services.documents.ocr_service.pytesseract") as mock_tess:
            from PIL import Image

            mock_tess.get_tesseract_version.return_value = "5.0.0"
            mock_tess.get_languages.return_value = ["eng", "rus"]
            mock_tess.image_to_string.return_value = sample_ocr_text

            # Mock PDF pages
            mock_image = Image.new("RGB", (800, 600), color="white")
            mock_convert.return_value = [mock_image]

            # Create dummy PDF file
            pdf_path.write_bytes(b"%PDF-1.4\n")

            service = OCRService(lang="rus")
            text = await service.extract_text_from_pdf(str(pdf_path))

            assert len(text) > 0
            assert "ЛИЦЕНЗИЯ" in text
            mock_convert.assert_called_once()


@pytest.mark.asyncio
async def test_ocr_file_not_found():
    """Test OCR with non-existent file."""
    with patch("src.aim.services.documents.ocr_service.pytesseract") as mock_tess:
        mock_tess.get_tesseract_version.return_value = "5.0.0"
        mock_tess.get_languages.return_value = ["eng", "rus"]

        service = OCRService(lang="rus")

        with pytest.raises(FileNotFoundError):
            await service.extract_text_from_image("/nonexistent/file.png")


# AI Extractor Tests

@pytest.mark.asyncio
async def test_ai_extractor_initialization():
    """Test AI extractor initialization."""
    extractor = AIExtractor(
        api_key="test_key",
        model="claude-sonnet-4-20250514",
    )

    assert extractor.model == "claude-sonnet-4-20250514"
    assert extractor.client is not None


@pytest.mark.asyncio
async def test_ai_extract_from_text_license(sample_ocr_text, sample_extracted_data):
    """Test AI extraction from license text."""
    extractor = AIExtractor(api_key="test_key")

    # Mock Claude API response
    mock_response = MagicMock()
    mock_response.content = [
        MagicMock(text=sample_extracted_data.model_dump_json())
    ]

    with patch.object(extractor.client.messages, "create", return_value=mock_response):
        data, confidence = await extractor.extract_from_text(
            sample_ocr_text, "license"
        )

        assert isinstance(data, ExtractedData)
        assert data.license_number == "ЛО-77-01-012345"
        assert data.inn == "7701234567"
        assert 0.0 <= confidence <= 1.0


@pytest.mark.asyncio
async def test_ai_extract_unsupported_document_type(sample_ocr_text):
    """Test AI extraction with unsupported document type."""
    extractor = AIExtractor(api_key="test_key")

    with pytest.raises(ValueError, match="Unsupported document type"):
        await extractor.extract_from_text(sample_ocr_text, "unknown")


@pytest.mark.asyncio
async def test_ai_extract_invalid_json_response(sample_ocr_text):
    """Test AI extraction with invalid JSON response."""
    extractor = AIExtractor(api_key="test_key")

    # Mock invalid JSON response
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Invalid JSON {")]

    with patch.object(extractor.client.messages, "create", return_value=mock_response):
        with pytest.raises(RuntimeError, match="AI response parsing failed"):
            await extractor.extract_from_text(sample_ocr_text, "license")


# Validator Tests

def test_validator_validate_inn_valid():
    """Test INN validation with valid checksums."""
    validator = DocumentValidator()

    # Valid 10-digit INN (legal entity)
    assert validator.validate_inn("7707083893") is None

    # Valid 12-digit INN (individual)
    assert validator.validate_inn("500100732259") is None


def test_validator_validate_inn_invalid_format():
    """Test INN validation with invalid format."""
    validator = DocumentValidator()

    # Non-digits
    assert validator.validate_inn("770708389A") is not None

    # Wrong length
    assert validator.validate_inn("77070838") is not None
    assert validator.validate_inn("77070838931") is not None


def test_validator_validate_inn_invalid_checksum():
    """Test INN validation with invalid checksum."""
    validator = DocumentValidator()

    # Invalid checksum (last digit wrong)
    assert validator.validate_inn("7707083890") is not None


def test_validator_validate_ogrn_valid():
    """Test OGRN validation with valid checksums."""
    validator = DocumentValidator()

    # Valid 13-digit OGRN (legal entity)
    assert validator.validate_ogrn("1027700132195") is None

    # Valid 15-digit OGRNIP (individual entrepreneur)
    assert validator.validate_ogrn("304500116000157") is None


def test_validator_validate_ogrn_invalid_format():
    """Test OGRN validation with invalid format."""
    validator = DocumentValidator()

    # Non-digits
    assert validator.validate_ogrn("102770013219A") is not None

    # Wrong length
    assert validator.validate_ogrn("10277001321") is not None


def test_validator_validate_ogrn_invalid_checksum():
    """Test OGRN validation with invalid checksum."""
    validator = DocumentValidator()

    # Invalid checksum (last digit wrong)
    assert validator.validate_ogrn("1027700132190") is not None


def test_validator_validate_kpp_valid():
    """Test KPP validation with valid format."""
    validator = DocumentValidator()

    assert validator.validate_kpp("770701001") is None
    assert validator.validate_kpp("773301001") is None


def test_validator_validate_kpp_invalid_format():
    """Test KPP validation with invalid format."""
    validator = DocumentValidator()

    # Non-digits
    assert validator.validate_kpp("77070100A") is not None

    # Wrong length
    assert validator.validate_kpp("7707010") is not None

    # Invalid tax authority code
    assert validator.validate_kpp("000001001") is not None

    # Invalid reason code
    assert validator.validate_kpp("770700001") is not None


def test_validator_validate_license_number_valid():
    """Test license number validation with valid format."""
    validator = DocumentValidator()

    assert validator.validate_license_number("ЛО-77-01-012345") is None
    assert validator.validate_license_number("ЛО-50-01-000123") is None


def test_validator_validate_license_number_invalid():
    """Test license number validation with invalid format."""
    validator = DocumentValidator()

    # Wrong prefix
    assert validator.validate_license_number("ЛМ-77-01-012345") is not None

    # Wrong format
    assert validator.validate_license_number("ЛО-77-012345") is not None
    assert validator.validate_license_number("77-01-012345") is not None


def test_validator_validate_extracted_data_valid(sample_extracted_data):
    """Test validation of valid extracted data."""
    validator = DocumentValidator()

    result = validator.validate_extracted_data(
        sample_extracted_data, "license", 0.85
    )

    assert isinstance(result, ValidationResult)
    assert result.is_valid is True
    assert result.confidence_score == 0.85
    assert len(result.errors) == 0


def test_validator_validate_extracted_data_missing_required():
    """Test validation with missing required fields."""
    validator = DocumentValidator()

    # Missing license_number (required for license type)
    data = ExtractedData(
        clinic_name="Test Clinic",
        inn="7707083893",
    )

    result = validator.validate_extracted_data(data, "license", 0.85)

    assert result.is_valid is False
    assert len(result.errors) > 0
    assert any("license_number" in err for err in result.errors)


def test_validator_validate_extracted_data_invalid_inn():
    """Test validation with invalid INN checksum."""
    validator = DocumentValidator()

    data = ExtractedData(
        license_number="ЛО-77-01-012345",
        clinic_name="Test Clinic",
        inn="7707083890",  # Invalid checksum
    )

    result = validator.validate_extracted_data(data, "license", 0.85)

    assert result.is_valid is False
    assert any("ИНН" in err for err in result.errors)


def test_validator_check_consistency_warnings():
    """Test cross-field consistency checks."""
    validator = DocumentValidator()

    # Legal entity INN (10 digits) with individual OGRNIP (15 digits)
    data = ExtractedData(
        license_number="ЛО-77-01-012345",
        clinic_name="Test Clinic",
        inn="7707083893",  # 10 digits (legal entity)
        ogrn="304500116000157",  # 15 digits (individual)
    )

    result = validator.validate_extracted_data(data, "license", 0.85)

    assert len(result.warnings) > 0


# Document Processor Tests

@pytest.mark.asyncio
async def test_processor_process_document_success(
    mock_document, sample_ocr_text, sample_extracted_data, tmp_path
):
    """Test successful document processing."""
    # Create test file
    file_path = tmp_path / "test.pdf"
    file_path.write_bytes(b"%PDF-1.4\n")

    # Mock services
    mock_ocr = AsyncMock(spec=OCRService)
    mock_ocr.extract_text_from_pdf.return_value = sample_ocr_text

    mock_ai = AsyncMock(spec=AIExtractor)
    mock_ai.extract_from_text.return_value = (sample_extracted_data, 0.85)

    mock_validator = MagicMock(spec=DocumentValidator)
    mock_validator.validate_extracted_data.return_value = ValidationResult(
        is_valid=True,
        confidence_score=0.85,
        errors=[],
        warnings=[],
    )

    processor = DocumentProcessor(mock_ocr, mock_ai, mock_validator)

    # Mock database session
    mock_db = AsyncMock(spec=AsyncSession)

    # Process document
    result = await processor.process_document(mock_document, str(file_path), mock_db)

    assert result.status == "completed"
    assert result.validation_status == "valid"
    assert result.ocr_text == sample_ocr_text
    assert result.confidence_score == 0.85
    mock_ocr.extract_text_from_pdf.assert_called_once()
    mock_ai.extract_from_text.assert_called_once()


@pytest.mark.asyncio
async def test_processor_process_document_file_not_found(mock_document):
    """Test processing with non-existent file."""
    mock_ocr = AsyncMock(spec=OCRService)
    mock_ai = AsyncMock(spec=AIExtractor)
    mock_validator = MagicMock(spec=DocumentValidator)

    processor = DocumentProcessor(mock_ocr, mock_ai, mock_validator)
    mock_db = AsyncMock(spec=AsyncSession)

    with pytest.raises(RuntimeError, match="Document processing failed"):
        await processor.process_document(
            mock_document, "/nonexistent/file.pdf", mock_db
        )


@pytest.mark.asyncio
async def test_processor_process_document_ocr_failure(mock_document, tmp_path):
    """Test processing with OCR failure."""
    file_path = tmp_path / "test.pdf"
    file_path.write_bytes(b"%PDF-1.4\n")

    mock_ocr = AsyncMock(spec=OCRService)
    mock_ocr.extract_text_from_pdf.side_effect = RuntimeError("OCR failed")

    mock_ai = AsyncMock(spec=AIExtractor)
    mock_validator = MagicMock(spec=DocumentValidator)

    processor = DocumentProcessor(mock_ocr, mock_ai, mock_validator)
    mock_db = AsyncMock(spec=AsyncSession)

    with pytest.raises(RuntimeError, match="Document processing failed"):
        await processor.process_document(mock_document, str(file_path), mock_db)

    assert mock_document.status == "failed"


@pytest.mark.asyncio
async def test_processor_reprocess_document(
    mock_document, sample_ocr_text, sample_extracted_data, tmp_path
):
    """Test document reprocessing."""
    file_path = tmp_path / "test.pdf"
    file_path.write_bytes(b"%PDF-1.4\n")
    mock_document.file_path = str(file_path)

    # Set initial processed state
    mock_document.status = "completed"
    mock_document.ocr_text = "old text"
    mock_document.confidence_score = 0.5

    # Mock services
    mock_ocr = AsyncMock(spec=OCRService)
    mock_ocr.extract_text_from_pdf.return_value = sample_ocr_text

    mock_ai = AsyncMock(spec=AIExtractor)
    mock_ai.extract_from_text.return_value = (sample_extracted_data, 0.85)

    mock_validator = MagicMock(spec=DocumentValidator)
    mock_validator.validate_extracted_data.return_value = ValidationResult(
        is_valid=True,
        confidence_score=0.85,
        errors=[],
        warnings=[],
    )

    processor = DocumentProcessor(mock_ocr, mock_ai, mock_validator)
    mock_db = AsyncMock(spec=AsyncSession)

    # Reprocess
    result = await processor.reprocess_document(mock_document, mock_db)

    assert result.status == "completed"
    assert result.ocr_text == sample_ocr_text
    assert result.confidence_score == 0.85


def test_processor_get_processing_stats(mock_document):
    """Test processing statistics generation."""
    mock_document.status = "completed"
    mock_document.validation_status = "valid"
    mock_document.confidence_score = 0.85
    mock_document.ocr_text = "Sample text"
    mock_document.extracted_data = {
        "license_number": "ЛО-77-01-012345",
        "clinic_name": "Test Clinic",
        "inn": "7707083893",
    }
    mock_document.validation_errors = []
    mock_document.processed_at = datetime.utcnow()

    mock_ocr = AsyncMock(spec=OCRService)
    mock_ai = AsyncMock(spec=AIExtractor)
    mock_validator = MagicMock(spec=DocumentValidator)

    processor = DocumentProcessor(mock_ocr, mock_ai, mock_validator)

    stats = processor.get_processing_stats(mock_document)

    assert stats["document_id"] == mock_document.id
    assert stats["status"] == "completed"
    assert stats["confidence_score"] == 0.85
    assert stats["fields_extracted"] == 3
    assert stats["errors_count"] == 0
    assert stats["processing_time"] is not None
