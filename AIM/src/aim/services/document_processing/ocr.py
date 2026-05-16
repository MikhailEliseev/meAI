"""
OCR Service

Extracts text from documents using Tesseract OCR.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import structlog
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import io

logger = structlog.get_logger()


class OCRService:
    """
    OCR service for document text extraction

    Uses Tesseract OCR for text extraction from images and PDFs.
    Supports multiple languages and confidence scoring.
    """

    def __init__(
        self,
        languages: List[str] = None,
        dpi: int = 300,
        min_confidence: float = 0.7,
    ):
        """
        Initialize OCR service

        Args:
            languages: List of language codes (default: ["eng", "rus"])
            dpi: DPI for PDF conversion (default: 300)
            min_confidence: Minimum confidence threshold (default: 0.7)
        """
        self.languages = languages or ["eng", "rus"]
        self.dpi = dpi
        self.min_confidence = min_confidence
        self.logger = logger.bind(service="ocr")

    async def extract_text_from_image(
        self,
        image_path: str,
    ) -> Dict[str, Any]:
        """
        Extract text from image file

        Args:
            image_path: Path to image file

        Returns:
            Extracted text with confidence scores
        """
        try:
            # Open image
            image = Image.open(image_path)

            # Extract text with confidence
            data = pytesseract.image_to_data(
                image,
                lang="+".join(self.languages),
                output_type=pytesseract.Output.DICT,
            )

            # Filter by confidence
            text_blocks = []
            for i in range(len(data["text"])):
                if int(data["conf"][i]) > self.min_confidence * 100:
                    text_blocks.append({
                        "text": data["text"][i],
                        "confidence": int(data["conf"][i]) / 100,
                        "bbox": {
                            "x": data["left"][i],
                            "y": data["top"][i],
                            "width": data["width"][i],
                            "height": data["height"][i],
                        },
                    })

            # Combine text
            full_text = " ".join([block["text"] for block in text_blocks if block["text"].strip()])

            # Calculate average confidence
            avg_confidence = sum([block["confidence"] for block in text_blocks]) / len(text_blocks) if text_blocks else 0

            self.logger.info(
                "text_extracted_from_image",
                image_path=image_path,
                text_length=len(full_text),
                blocks_count=len(text_blocks),
                avg_confidence=avg_confidence,
            )

            return {
                "text": full_text,
                "blocks": text_blocks,
                "confidence": avg_confidence,
                "language": self.languages,
            }

        except Exception as e:
            self.logger.error(
                "image_ocr_failed",
                image_path=image_path,
                error=str(e),
            )
            raise

    async def extract_text_from_pdf(
        self,
        pdf_path: str,
    ) -> Dict[str, Any]:
        """
        Extract text from PDF file

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text with confidence scores per page
        """
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=self.dpi)

            # Extract text from each page
            pages = []
            all_text = []

            for page_num, image in enumerate(images, start=1):
                # Extract text from page
                data = pytesseract.image_to_data(
                    image,
                    lang="+".join(self.languages),
                    output_type=pytesseract.Output.DICT,
                )

                # Filter by confidence
                text_blocks = []
                for i in range(len(data["text"])):
                    if int(data["conf"][i]) > self.min_confidence * 100:
                        text_blocks.append({
                            "text": data["text"][i],
                            "confidence": int(data["conf"][i]) / 100,
                        })

                # Combine text for page
                page_text = " ".join([block["text"] for block in text_blocks if block["text"].strip()])
                all_text.append(page_text)

                # Calculate page confidence
                page_confidence = sum([block["confidence"] for block in text_blocks]) / len(text_blocks) if text_blocks else 0

                pages.append({
                    "page_number": page_num,
                    "text": page_text,
                    "confidence": page_confidence,
                    "blocks_count": len(text_blocks),
                })

            # Combine all pages
            full_text = "\n\n".join(all_text)

            # Calculate average confidence
            avg_confidence = sum([page["confidence"] for page in pages]) / len(pages) if pages else 0

            self.logger.info(
                "text_extracted_from_pdf",
                pdf_path=pdf_path,
                pages_count=len(pages),
                text_length=len(full_text),
                avg_confidence=avg_confidence,
            )

            return {
                "text": full_text,
                "pages": pages,
                "confidence": avg_confidence,
                "language": self.languages,
            }

        except Exception as e:
            self.logger.error(
                "pdf_ocr_failed",
                pdf_path=pdf_path,
                error=str(e),
            )
            raise

    async def extract_text(
        self,
        file_path: str,
    ) -> Dict[str, Any]:
        """
        Extract text from file (auto-detect type)

        Args:
            file_path: Path to file

        Returns:
            Extracted text with metadata
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        if extension == ".pdf":
            return await self.extract_text_from_pdf(file_path)
        elif extension in [".jpg", ".jpeg", ".png", ".tiff", ".bmp"]:
            return await self.extract_text_from_image(file_path)
        else:
            raise ValueError(f"Unsupported file type: {extension}")
