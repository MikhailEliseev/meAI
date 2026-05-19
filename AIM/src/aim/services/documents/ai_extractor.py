"""AI Extraction Service

Extracts structured data from OCR text using Claude AI.

Part of: Phase 11 Sprint 3 - Task 3.3
"""

import json
import logging
from typing import Optional, Tuple

from openai import AsyncOpenAI

from aim.schemas.document import ExtractedData

logger = logging.getLogger(__name__)


class AIExtractor:
    """Service for extracting structured data from documents using AI.

    Uses OmniRoute (OpenAI-compatible API) to parse OCR text and extract:
    - License information
    - Clinic details
    - Legal entity data (INN, OGRN, KPP)
    - Director information
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "http://138.16.224.188:20128/v1",
        model: str = "claude-sonnet-4-20250514",
    ):
        """Initialize AI extractor.

        Args:
            api_key: OmniRoute API key
            base_url: OmniRoute endpoint URL
            model: Model to use
        """
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    async def extract_from_text(
        self, text: str, document_type: str
    ) -> Tuple[ExtractedData, float]:
        """Extract structured data from OCR text.

        Args:
            text: OCR extracted text
            document_type: Type of document (license, inn, ogrn, contract)

        Returns:
            Tuple of (extracted_data, confidence_score)

        Raises:
            ValueError: If document type not supported
            RuntimeError: If AI extraction fails
        """
        logger.info(f"Extracting data from {document_type} document")

        # Build prompt
        prompt = self._build_extraction_prompt(text, document_type)

        try:
            # Call OmniRoute API (OpenAI-compatible)
            response = await self.client.chat.completions.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )

            # Parse response
            content = response.choices[0].message.content
            data_dict = json.loads(content)

            # Create ExtractedData object
            extracted_data = ExtractedData(**data_dict)

            # Calculate confidence
            confidence = self._calculate_confidence(extracted_data, document_type)

            logger.info(
                f"Extracted data with confidence {confidence:.2f}: "
                f"{len(data_dict)} fields"
            )

            return extracted_data, confidence

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            raise RuntimeError(f"AI response parsing failed: {e}")

        except Exception as e:
            logger.error(f"AI extraction failed: {e}")
            raise RuntimeError(f"AI extraction failed: {e}")

    def _build_extraction_prompt(self, text: str, document_type: str) -> str:
        """Build Claude prompt for data extraction.

        Args:
            text: OCR text
            document_type: Document type

        Returns:
            Extraction prompt

        Raises:
            ValueError: If document type not supported
        """
        if document_type == "license":
            return self._build_license_prompt(text)
        elif document_type == "inn":
            return self._build_inn_prompt(text)
        elif document_type == "ogrn":
            return self._build_ogrn_prompt(text)
        elif document_type == "contract":
            return self._build_contract_prompt(text)
        else:
            raise ValueError(f"Unsupported document type: {document_type}")

    def _build_license_prompt(self, text: str) -> str:
        """Build prompt for medical license extraction."""
        return f"""Извлеки из текста медицинской лицензии следующие данные:

Текст документа:
{text}

Извлеки следующие поля (если найдены):
- license_number: Номер лицензии (формат: ЛО-XX-XX-XXXXXX)
- license_date: Дата выдачи лицензии
- license_issuer: Орган, выдавший лицензию
- clinic_name: Название клиники/организации
- clinic_address: Адрес клиники
- clinic_phone: Телефон клиники
- clinic_email: Email клиники
- inn: ИНН организации
- ogrn: ОГРН организации
- director_name: ФИО руководителя
- director_position: Должность руководителя

Верни результат ТОЛЬКО в JSON формате без дополнительного текста:
{{
  "license_number": "значение или null",
  "license_date": "значение или null",
  ...
}}

Если поле не найдено, используй null."""

    def _build_inn_prompt(self, text: str) -> str:
        """Build prompt for INN document extraction."""
        return f"""Извлеки из текста свидетельства ИНН следующие данные:

Текст документа:
{text}

Извлеки следующие поля (если найдены):
- inn: ИНН (10 или 12 цифр)
- clinic_name: Название организации
- clinic_address: Адрес организации
- kpp: КПП (9 цифр)
- ogrn: ОГРН (13 или 15 цифр)
- director_name: ФИО руководителя

Верни результат ТОЛЬКО в JSON формате без дополнительного текста:
{{
  "inn": "значение или null",
  "clinic_name": "значение или null",
  ...
}}

Если поле не найдено, используй null."""

    def _build_ogrn_prompt(self, text: str) -> str:
        """Build prompt for OGRN document extraction."""
        return f"""Извлеки из текста свидетельства ОГРН следующие данные:

Текст документа:
{text}

Извлеки следующие поля (если найдены):
- ogrn: ОГРН (13 или 15 цифр)
- clinic_name: Название организации
- clinic_address: Адрес организации
- inn: ИНН организации
- kpp: КПП организации
- director_name: ФИО руководителя

Верни результат ТОЛЬКО в JSON формате без дополнительного текста:
{{
  "ogrn": "значение или null",
  "clinic_name": "значение или null",
  ...
}}

Если поле не найдено, используй null."""

    def _build_contract_prompt(self, text: str) -> str:
        """Build prompt for contract extraction."""
        return f"""Извлеки из текста договора следующие данные:

Текст документа:
{text}

Извлеки следующие поля (если найдены):
- clinic_name: Название клиники (сторона договора)
- clinic_address: Адрес клиники
- inn: ИНН клиники
- ogrn: ОГРН клиники
- director_name: ФИО руководителя клиники
- director_position: Должность руководителя

Верни результат ТОЛЬКО в JSON формате без дополнительного текста:
{{
  "clinic_name": "значение или null",
  "clinic_address": "значение или null",
  ...
}}

Если поле не найдено, используй null."""

    def _calculate_confidence(
        self, data: ExtractedData, document_type: str
    ) -> float:
        """Calculate confidence score for extracted data.

        Based on:
        - Number of fields extracted
        - Required fields present
        - Field format validation

        Args:
            data: Extracted data
            document_type: Document type

        Returns:
            Confidence score (0.0-1.0)
        """
        # Define required fields per document type
        required_fields = {
            "license": ["license_number", "clinic_name"],
            "inn": ["inn", "clinic_name"],
            "ogrn": ["ogrn", "clinic_name"],
            "contract": ["clinic_name"],
        }

        # Get required fields for this document type
        required = required_fields.get(document_type, [])

        # Count extracted fields
        extracted_count = 0
        required_count = 0

        for field_name, field_value in data.model_dump().items():
            if field_value is not None:
                extracted_count += 1
                if field_name in required:
                    required_count += 1

        # Calculate base confidence
        total_fields = len(data.model_dump())
        base_confidence = extracted_count / total_fields if total_fields > 0 else 0.0

        # Boost if all required fields present
        required_boost = 0.2 if required_count == len(required) else 0.0

        # Final confidence (capped at 1.0)
        confidence = min(base_confidence + required_boost, 1.0)

        return confidence
