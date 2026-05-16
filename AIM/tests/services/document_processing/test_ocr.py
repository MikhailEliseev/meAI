"""
Tests for OCR Service
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from PIL import Image
import io

from aim.services.document_processing.ocr import OCRService


@pytest.fixture
def ocr_service():
    """Create OCR service instance"""
    return OCRService(
        languages=["eng", "rus"],
        dpi=300,
        min_confidence=0.7,
    )


@pytest.fixture
def mock_image():
    """Create mock image"""
    img = Image.new("RGB", (800, 600), color="white")
    return img


@pytest.fixture
def mock_ocr_data():
    """Mock Tesseract OCR data"""
    return {
        "text": ["Practice", "Name:", "Dental", "Clinic", "Email:", "info@dental.com"],
        "conf": [95, 90, 92, 88, 93, 85],
        "left": [100, 200, 100, 200, 100, 200],
        "top": [100, 100, 150, 150, 200, 200],
        "width": [80, 60, 70, 65, 60, 120],
        "height": [20, 20, 20, 20, 20, 20],
    }


class TestOCRService:
    """Test OCR service"""

    @pytest.mark.asyncio
    async def test_init_with_defaults(self):
        """Test initialization with default parameters"""
        service = OCRService()

        assert service.languages == ["eng", "rus"]
        assert service.dpi == 300
        assert service.min_confidence == 0.7

    @pytest.mark.asyncio
    async def test_init_with_custom_params(self):
        """Test initialization with custom parameters"""
        service = OCRService(
            languages=["eng"],
            dpi=150,
            min_confidence=0.8,
        )

        assert service.languages == ["eng"]
        assert service.dpi == 150
        assert service.min_confidence == 0.8

    @pytest.mark.asyncio
    @patch("aim.services.document_processing.ocr.Image.open")
    @patch("aim.services.document_processing.ocr.pytesseract.image_to_data")
    async def test_extract_text_from_image_success(
        self,
        mock_image_to_data,
        mock_image_open,
        ocr_service,
        mock_image,
        mock_ocr_data,
    ):
        """Test successful text extraction from image"""
        mock_image_open.return_value = mock_image
        mock_image_to_data.return_value = mock_ocr_data

        result = await ocr_service.extract_text_from_image("test.jpg")

        assert "text" in result
        assert "blocks" in result
        assert "confidence" in result
        assert "language" in result

        # Check text is combined
        assert len(result["text"]) > 0

        # Check blocks are filtered by confidence
        assert all(block["confidence"] >= 0.7 for block in result["blocks"])

        # Check average confidence
        assert 0 <= result["confidence"] <= 1

    @pytest.mark.asyncio
    @patch("aim.services.document_processing.ocr.Image.open")
    @patch("aim.services.document_processing.ocr.pytesseract.image_to_data")
    async def test_extract_text_from_image_low_confidence(
        self,
        mock_image_to_data,
        mock_image_open,
        ocr_service,
        mock_image,
    ):
        """Test extraction with low confidence text"""
        low_conf_data = {
            "text": ["Text1", "Text2", "Text3"],
            "conf": [50, 60, 65],  # All below 70% threshold
            "left": [100, 200, 300],
            "top": [100, 100, 100],
            "width": [80, 80, 80],
            "height": [20, 20, 20],
        }

        mock_image_open.return_value = mock_image
        mock_image_to_data.return_value = low_conf_data

        result = await ocr_service.extract_text_from_image("test.jpg")

        # No blocks should pass confidence threshold
        assert len(result["blocks"]) == 0
        assert result["text"] == ""
        assert result["confidence"] == 0

    @pytest.mark.asyncio
    @patch("aim.services.document_processing.ocr.Image.open")
    async def test_extract_text_from_image_file_not_found(
        self,
        mock_image_open,
        ocr_service,
    ):
        """Test extraction with non-existent file"""
        mock_image_open.side_effect = FileNotFoundError("File not found")

        with pytest.raises(FileNotFoundError):
            await ocr_service.extract_text_from_image("nonexistent.jpg")

    @pytest.mark.asyncio
    @patch("aim.services.document_processing.ocr.convert_from_path")
    @patch("aim.services.document_processing.ocr.pytesseract.image_to_data")
    async def test_extract_text_from_pdf_success(
        self,
        mock_image_to_data,
        mock_convert_from_path,
        ocr_service,
        mock_image,
        mock_ocr_data,
    ):
        """Test successful text extraction from PDF"""
        # Mock PDF conversion to 2 pages
        mock_convert_from_path.return_value = [mock_image, mock_image]
        mock_image_to_data.return_value = mock_ocr_data

        result = await ocr_service.extract_text_from_pdf("test.pdf")

        assert "text" in result
        assert "pages" in result
        assert "confidence" in result

        # Check 2 pages processed
        assert len(result["pages"]) == 2

        # Check each page has required fields
        for page in result["pages"]:
            assert "page_number" in page
            assert "text" in page
            assert "confidence" in page
            assert "blocks_count" in page

        # Check text is combined from all pages
        assert "\n\n" in result["text"]

    @pytest.mark.asyncio
    @patch("aim.services.document_processing.ocr.convert_from_path")
    async def test_extract_text_from_pdf_conversion_error(
        self,
        mock_convert_from_path,
        ocr_service,
    ):
        """Test PDF conversion error"""
        mock_convert_from_path.side_effect = Exception("PDF conversion failed")

        with pytest.raises(Exception):
            await ocr_service.extract_text_from_pdf("test.pdf")

    @pytest.mark.asyncio
    @patch("aim.services.document_processing.ocr.OCRService.extract_text_from_pdf")
    async def test_extract_text_pdf_file(
        self,
        mock_extract_pdf,
        ocr_service,
    ):
        """Test extract_text with PDF file"""
        mock_extract_pdf.return_value = {"text": "PDF content"}

        result = await ocr_service.extract_text("document.pdf")

        assert result == {"text": "PDF content"}
        mock_extract_pdf.assert_called_once_with("document.pdf")

    @pytest.mark.asyncio
    @patch("aim.services.document_processing.ocr.OCRService.extract_text_from_image")
    async def test_extract_text_image_file(
        self,
        mock_extract_image,
        ocr_service,
    ):
        """Test extract_text with image file"""
        mock_extract_image.return_value = {"text": "Image content"}

        result = await ocr_service.extract_text("document.jpg")

        assert result == {"text": "Image content"}
        mock_extract_image.assert_called_once_with("document.jpg")

    @pytest.mark.asyncio
    async def test_extract_text_unsupported_format(self, ocr_service):
        """Test extract_text with unsupported file format"""
        with pytest.raises(ValueError, match="Unsupported file type"):
            await ocr_service.extract_text("document.txt")

    @pytest.mark.asyncio
    @patch("aim.services.document_processing.ocr.Image.open")
    @patch("aim.services.document_processing.ocr.pytesseract.image_to_data")
    async def test_bbox_coordinates(
        self,
        mock_image_to_data,
        mock_image_open,
        ocr_service,
        mock_image,
        mock_ocr_data,
    ):
        """Test bounding box coordinates are correctly extracted"""
        mock_image_open.return_value = mock_image
        mock_image_to_data.return_value = mock_ocr_data

        result = await ocr_service.extract_text_from_image("test.jpg")

        # Check first block has correct bbox
        first_block = result["blocks"][0]
        assert first_block["bbox"]["x"] == 100
        assert first_block["bbox"]["y"] == 100
        assert first_block["bbox"]["width"] == 80
        assert first_block["bbox"]["height"] == 20

    @pytest.mark.asyncio
    @patch("aim.services.document_processing.ocr.Image.open")
    @patch("aim.services.document_processing.ocr.pytesseract.image_to_data")
    async def test_language_parameter(
        self,
        mock_image_to_data,
        mock_image_open,
        ocr_service,
        mock_image,
        mock_ocr_data,
    ):
        """Test language parameter is passed to Tesseract"""
        mock_image_open.return_value = mock_image
        mock_image_to_data.return_value = mock_ocr_data

        await ocr_service.extract_text_from_image("test.jpg")

        # Check Tesseract was called with correct language
        call_args = mock_image_to_data.call_args
        assert call_args[1]["lang"] == "eng+rus"

    @pytest.mark.asyncio
    @patch("aim.services.document_processing.ocr.convert_from_path")
    @patch("aim.services.document_processing.ocr.pytesseract.image_to_data")
    async def test_pdf_dpi_parameter(
        self,
        mock_image_to_data,
        mock_convert_from_path,
        ocr_service,
        mock_image,
        mock_ocr_data,
    ):
        """Test DPI parameter is used for PDF conversion"""
        mock_convert_from_path.return_value = [mock_image]
        mock_image_to_data.return_value = mock_ocr_data

        await ocr_service.extract_text_from_pdf("test.pdf")

        # Check PDF conversion was called with correct DPI
        call_args = mock_convert_from_path.call_args
        assert call_args[1]["dpi"] == 300
