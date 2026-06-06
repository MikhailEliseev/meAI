"""Document Validation Service

Validates extracted data from documents using Russian legal entity checksums.

Part of: Phase 11 Sprint 3 - Task 3.3
"""

import logging
import re
from typing import Optional

from src.aim.schemas.document import ExtractedData, ValidationResult

logger = logging.getLogger(__name__)


class DocumentValidator:
    """Service for validating extracted document data.

    Validates:
    - INN checksum (10 or 12 digits)
    - OGRN checksum (13 or 15 digits)
    - KPP format (9 digits)
    - Medical license format (ЛО-XX-XX-XXXXXX)
    - Required fields per document type
    - Cross-field consistency
    """

    # Required fields per document type
    REQUIRED_FIELDS = {
        "license": ["license_number", "clinic_name"],
        "inn": ["inn", "clinic_name"],
        "ogrn": ["ogrn", "clinic_name"],
        "contract": ["clinic_name"],
    }

    def validate_extracted_data(
        self, data: ExtractedData, document_type: str, confidence_score: float
    ) -> ValidationResult:
        """Validate extracted data.

        Args:
            data: Extracted data
            document_type: Document type
            confidence_score: AI extraction confidence

        Returns:
            Validation result with errors and warnings
        """
        logger.info(f"Validating {document_type} document data")

        errors = []
        warnings = []

        # Check required fields
        required = self.REQUIRED_FIELDS.get(document_type, [])
        for field_name in required:
            field_value = getattr(data, field_name, None)
            if not field_value:
                errors.append(f"Обязательное поле отсутствует: {field_name}")

        # Validate INN
        if data.inn:
            inn_error = self.validate_inn(data.inn)
            if inn_error:
                errors.append(inn_error)

        # Validate OGRN
        if data.ogrn:
            ogrn_error = self.validate_ogrn(data.ogrn)
            if ogrn_error:
                errors.append(ogrn_error)

        # Validate KPP
        if data.kpp:
            kpp_error = self.validate_kpp(data.kpp)
            if kpp_error:
                errors.append(kpp_error)

        # Validate license number
        if data.license_number:
            license_error = self.validate_license_number(data.license_number)
            if license_error:
                errors.append(license_error)

        # Check confidence score
        if confidence_score < 0.5:
            warnings.append(
                f"Низкая уверенность извлечения: {confidence_score:.2f}"
            )
        elif confidence_score < 0.7:
            warnings.append(
                f"Средняя уверенность извлечения: {confidence_score:.2f}"
            )

        # Cross-field consistency
        consistency_warnings = self._check_consistency(data)
        warnings.extend(consistency_warnings)

        # Determine validity
        is_valid = len(errors) == 0

        logger.info(
            f"Validation complete: valid={is_valid}, "
            f"errors={len(errors)}, warnings={len(warnings)}"
        )

        return ValidationResult(
            is_valid=is_valid,
            confidence_score=confidence_score,
            errors=errors,
            warnings=warnings,
        )

    def validate_inn(self, inn: str) -> Optional[str]:
        """Validate INN checksum.

        INN format:
        - 10 digits for legal entities
        - 12 digits for individuals

        Checksum algorithm:
        - 10 digits: last digit is checksum
        - 12 digits: last 2 digits are checksums

        Args:
            inn: INN string

        Returns:
            Error message or None if valid
        """
        # Check format
        if not inn.isdigit():
            return "ИНН должен содержать только цифры"

        if len(inn) not in (10, 12):
            return "ИНН должен быть 10 или 12 цифр"

        # Validate checksum
        if len(inn) == 10:
            # Legal entity INN
            coefficients = [2, 4, 10, 3, 5, 9, 4, 6, 8]
            checksum = sum(
                int(inn[i]) * coefficients[i] for i in range(9)
            ) % 11 % 10

            if int(inn[9]) != checksum:
                return "Неверная контрольная сумма ИНН"

        elif len(inn) == 12:
            # Individual INN
            # First checksum (11th digit)
            coefficients_1 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
            checksum_1 = sum(
                int(inn[i]) * coefficients_1[i] for i in range(10)
            ) % 11 % 10

            if int(inn[10]) != checksum_1:
                return "Неверная первая контрольная сумма ИНН"

            # Second checksum (12th digit)
            coefficients_2 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
            checksum_2 = sum(
                int(inn[i]) * coefficients_2[i] for i in range(11)
            ) % 11 % 10

            if int(inn[11]) != checksum_2:
                return "Неверная вторая контрольная сумма ИНН"

        return None

    def validate_ogrn(self, ogrn: str) -> Optional[str]:
        """Validate OGRN checksum.

        OGRN format:
        - 13 digits for legal entities (ОГРН)
        - 15 digits for individual entrepreneurs (ОГРНИП)

        Checksum algorithm:
        - Last digit is checksum
        - Checksum = (first N-1 digits mod divisor) mod 10
        - Divisor: 11 for ОГРН, 13 for ОГРНИП

        Args:
            ogrn: OGRN string

        Returns:
            Error message or None if valid
        """
        # Check format
        if not ogrn.isdigit():
            return "ОГРН должен содержать только цифры"

        if len(ogrn) not in (13, 15):
            return "ОГРН должен быть 13 или 15 цифр"

        # Validate checksum
        if len(ogrn) == 13:
            # Legal entity OGRN
            divisor = 11
            number = int(ogrn[:12])
            checksum = (number % divisor) % 10

            if int(ogrn[12]) != checksum:
                return "Неверная контрольная сумма ОГРН"

        elif len(ogrn) == 15:
            # Individual entrepreneur OGRNIP
            divisor = 13
            number = int(ogrn[:14])
            checksum = (number % divisor) % 10

            if int(ogrn[14]) != checksum:
                return "Неверная контрольная сумма ОГРНИП"

        return None

    def validate_kpp(self, kpp: str) -> Optional[str]:
        """Validate KPP format.

        KPP format: 9 digits
        - First 4 digits: tax authority code
        - Next 2 digits: reason code
        - Last 3 digits: sequential number

        Args:
            kpp: KPP string

        Returns:
            Error message or None if valid
        """
        # Check format
        if not kpp.isdigit():
            return "КПП должен содержать только цифры"

        if len(kpp) != 9:
            return "КПП должен быть 9 цифр"

        # Basic format validation
        tax_authority = kpp[:4]
        reason_code = kpp[4:6]

        # Tax authority code should not be 0000
        if tax_authority == "0000":
            return "Неверный код налогового органа в КПП"

        # Reason code should be valid (01-50)
        try:
            reason = int(reason_code)
            if reason < 1 or reason > 50:
                return "Неверный код причины постановки на учёт в КПП"
        except ValueError:
            return "Неверный формат кода причины в КПП"

        return None

    def validate_license_number(self, license_number: str) -> Optional[str]:
        """Validate medical license number format.

        Format: ЛО-XX-XX-XXXXXX
        - ЛО: License type (medical)
        - XX: Region code (2 digits)
        - XX: License type code (2 digits)
        - XXXXXX: Sequential number (6 digits)

        Args:
            license_number: License number string

        Returns:
            Error message or None if valid
        """
        # Pattern: ЛО-XX-XX-XXXXXX
        pattern = r"^ЛО-\d{2}-\d{2}-\d{6}$"

        if not re.match(pattern, license_number):
            return (
                "Неверный формат номера лицензии. "
                "Ожидается: ЛО-XX-XX-XXXXXX"
            )

        return None

    def _check_consistency(self, data: ExtractedData) -> list[str]:
        """Check cross-field consistency.

        Args:
            data: Extracted data

        Returns:
            List of consistency warnings
        """
        warnings = []

        # If INN is 10 digits (legal entity), OGRN should be 13 digits
        if data.inn and len(data.inn) == 10:
            if data.ogrn and len(data.ogrn) != 13:
                warnings.append(
                    "ИНН юридического лица (10 цифр) должен "
                    "соответствовать ОГРН (13 цифр)"
                )

        # If INN is 12 digits (individual), OGRN should be 15 digits
        if data.inn and len(data.inn) == 12:
            if data.ogrn and len(data.ogrn) != 15:
                warnings.append(
                    "ИНН физического лица (12 цифр) должен "
                    "соответствовать ОГРНИП (15 цифр)"
                )

        # KPP should only exist for legal entities (10-digit INN)
        if data.kpp:
            if not data.inn:
                warnings.append("КПП указан, но ИНН отсутствует")
            elif len(data.inn) == 12:
                warnings.append(
                    "КПП не применяется для физических лиц "
                    "(ИНН 12 цифр)"
                )

        return warnings
