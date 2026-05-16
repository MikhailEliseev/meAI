"""OCR Service

Extracts text from images and PDFs using Tesseract OCR.

Part of: Phase 11 Sprint 3 - Task 3.3
"""

import logging
import os
from pathlib import Path
from typing import Optional

import pytesseract
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)


class OCRService:
    """Service for extracting text from documents using OCR.

    Supports:
    - Images (JPEG, PNG, TIFF)
    - PDFs (converted to images first)
    - Russian language text
    - Image preprocessing for better accuracy
    """

    def __init__(self, lang: str = "rus"):
        """Initialize OCR service.

        Args:
            lang: Tesseract language code (default: rus for Russian)
        """
        self.lang = lang
        self._verify_tesseract()

    def _verify_tesseract(self) -> None:
        """Verify Tesseract is installed and language is available."""
        try:
            # Check if Tesseract is installed
            pytesseract.get_tesseract_version()

            # Check if language is available
            available_langs = pytesseract.get_languages()
            if self.lang not in available_langs:
                raise RuntimeError(
                    f"Tesseract language '{self.lang}' not installed. "
                    f"Available: {available_langs}"
                )

            logger.info(f"Tesseract OCR initialized with language: {self.lang}")

        except Exception as e:
            logger.error(f"Tesseract verification failed: {e}")
            raise RuntimeError(f"Tesseract OCR not available: {e}")

    async def extract_text_from_image(
        self, image_path: str, preprocess: bool = True
    ) -> str:
        """Extract text from image using OCR.

        Args:
            image_path: Path to image file
            preprocess: Whether to preprocess image for better accuracy

        Returns:
            Extracted text

        Raises:
            FileNotFoundError: If image file not found
            ValueError: If image format not supported
            RuntimeError: If OCR fails
        """
        logger.info(f"Extracting text from image: {image_path}")

        # Verify file exists
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        try:
            # Load image
            image = Image.open(image_path)

            # Preprocess if requested
            if preprocess:
                image = self._preprocess_image(image)

            # Extract text
            text = pytesseract.image_to_string(image, lang=self.lang)

            # Clean text
            text = self._clean_text(text)

            logger.info(
                f"Extracted {len(text)} characters from {image_path}"
            )

            return text

        except Exception as e:
            logger.error(f"OCR failed for {image_path}: {e}")
            raise RuntimeError(f"OCR extraction failed: {e}")

    async def extract_text_from_pdf(
        self, pdf_path: str, preprocess: bool = True
    ) -> str:
        """Extract text from PDF using OCR.

        Converts PDF pages to images and runs OCR on each page.

        Args:
            pdf_path: Path to PDF file
            preprocess: Whether to preprocess images for better accuracy

        Returns:
            Extracted text from all pages

        Raises:
            FileNotFoundError: If PDF file not found
            RuntimeError: If PDF conversion or OCR fails
        """
        logger.info(f"Extracting text from PDF: {pdf_path}")

        # Verify file exists
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path)
            logger.info(f"Converted PDF to {len(images)} images")

            # Extract text from each page
            texts = []
            for i, image in enumerate(images, 1):
                logger.debug(f"Processing page {i}/{len(images)}")

                # Preprocess if requested
                if preprocess:
                    image = self._preprocess_image(image)

                # Extract text
                text = pytesseract.image_to_string(image, lang=self.lang)
                texts.append(text)

            # Combine all pages
            combined_text = "\n\n".join(texts)

            # Clean text
            combined_text = self._clean_text(combined_text)

            logger.info(
                f"Extracted {len(combined_text)} characters from {len(images)} pages"
            )

            return combined_text

        except Exception as e:
            logger.error(f"PDF OCR failed for {pdf_path}: {e}")
            raise RuntimeError(f"PDF OCR extraction failed: {e}")

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR accuracy.

        Steps:
        - Convert to grayscale
        - Increase contrast
        - Sharpen
        - Remove noise

        Args:
            image: PIL Image

        Returns:
            Preprocessed image
        """
        # Convert to grayscale
        image = image.convert("L")

        # Increase contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)

        # Sharpen
        image = image.filter(ImageFilter.SHARPEN)

        # Remove noise (median filter)
        image = image.filter(ImageFilter.MedianFilter(size=3))

        return image

    def _clean_text(self, text: str) -> str:
        """Clean extracted text.

        - Remove extra whitespace
        - Remove empty lines
        - Normalize line breaks

        Args:
            text: Raw OCR text

        Returns:
            Cleaned text
        """
        # Split into lines
        lines = text.split("\n")

        # Remove empty lines and strip whitespace
        lines = [line.strip() for line in lines if line.strip()]

        # Join with single newline
        cleaned = "\n".join(lines)

        return cleaned

    def get_confidence(self, image_path: str) -> dict[str, float]:
        """Get OCR confidence scores for image.

        Args:
            image_path: Path to image file

        Returns:
            Dictionary with confidence scores per word
        """
        try:
            image = Image.open(image_path)
            data = pytesseract.image_to_data(
                image, lang=self.lang, output_type=pytesseract.Output.DICT
            )

            # Calculate average confidence
            confidences = [
                float(conf) for conf in data["conf"] if conf != "-1"
            ]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            return {
                "average": avg_confidence,
                "min": min(confidences) if confidences else 0.0,
                "max": max(confidences) if confidences else 0.0,
            }

        except Exception as e:
            logger.error(f"Failed to get confidence for {image_path}: {e}")
            return {"average": 0.0, "min": 0.0, "max": 0.0}
