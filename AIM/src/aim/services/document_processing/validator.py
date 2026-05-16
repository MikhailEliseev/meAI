"""
Document Processing Validator

Validates extracted data accuracy and flags low-confidence items for human review.
"""

from typing import Dict, Any, List, Optional
from enum import Enum
import structlog

logger = structlog.get_logger()


class ValidationStatus(str, Enum):
    """Validation status"""
    APPROVED = "approved"  # >95% confidence, auto-approved
    REVIEW = "review"  # <95% confidence, needs human review
    REJECTED = "rejected"  # Failed validation rules


class ValidationRule(str, Enum):
    """Validation rules"""
    CONFIDENCE_THRESHOLD = "confidence_threshold"
    REQUIRED_FIELDS = "required_fields"
    FORMAT_VALIDATION = "format_validation"
    CROSS_FIELD_VALIDATION = "cross_field_validation"


class DocumentValidator:
    """
    Document processing validator

    Validates extracted data accuracy and creates review queue
    for low-confidence items.
    """

    def __init__(
        self,
        confidence_threshold: float = 0.95,
        required_fields: Optional[List[str]] = None,
    ):
        """
        Initialize validator

        Args:
            confidence_threshold: Minimum confidence for auto-approval (default: 0.95)
            required_fields: List of required fields (default: None)
        """
        self.confidence_threshold = confidence_threshold
        self.required_fields = required_fields or []
        self.logger = logger.bind(service="document_validator")

    async def validate_extraction(
        self,
        extraction_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate extraction result

        Args:
            extraction_result: Result from NLPExtractor.extract_all()

        Returns:
            Validation result with status and issues
        """
        issues = []
        overall_confidence = extraction_result.get("overall_confidence", 0.0)

        # Rule 1: Confidence threshold
        if overall_confidence < self.confidence_threshold:
            issues.append({
                "rule": ValidationRule.CONFIDENCE_THRESHOLD,
                "severity": "high",
                "message": f"Overall confidence {overall_confidence:.2%} below threshold {self.confidence_threshold:.2%}",
                "field": "overall",
                "value": overall_confidence,
            })

        # Rule 2: Required fields
        practice_info = extraction_result.get("practice_info", {})
        for field in self.required_fields:
            if not practice_info.get(field):
                issues.append({
                    "rule": ValidationRule.REQUIRED_FIELDS,
                    "severity": "high",
                    "message": f"Required field '{field}' is missing",
                    "field": field,
                    "value": None,
                })

        # Rule 3: Format validation
        format_issues = await self._validate_formats(extraction_result)
        issues.extend(format_issues)

        # Rule 4: Cross-field validation
        cross_field_issues = await self._validate_cross_fields(extraction_result)
        issues.extend(cross_field_issues)

        # Determine status
        high_severity_count = sum(1 for issue in issues if issue["severity"] == "high")

        if high_severity_count > 0:
            status = ValidationStatus.REVIEW
        elif overall_confidence >= self.confidence_threshold:
            status = ValidationStatus.APPROVED
        else:
            status = ValidationStatus.REVIEW

        result = {
            "status": status,
            "overall_confidence": overall_confidence,
            "issues": issues,
            "issues_count": len(issues),
            "high_severity_count": high_severity_count,
            "requires_review": status == ValidationStatus.REVIEW,
        }

        self.logger.info(
            "extraction_validated",
            status=status,
            confidence=overall_confidence,
            issues_count=len(issues),
        )

        return result

    async def _validate_formats(
        self,
        extraction_result: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Validate field formats"""
        issues = []
        practice_info = extraction_result.get("practice_info", {})

        # Validate emails
        emails = practice_info.get("emails", [])
        for email in emails:
            if "@" not in email or "." not in email:
                issues.append({
                    "rule": ValidationRule.FORMAT_VALIDATION,
                    "severity": "medium",
                    "message": f"Invalid email format: {email}",
                    "field": "emails",
                    "value": email,
                })

        # Validate phones
        phones = practice_info.get("phones", [])
        for phone in phones:
            # Remove common separators
            digits = "".join(c for c in phone if c.isdigit())
            if len(digits) < 10:
                issues.append({
                    "rule": ValidationRule.FORMAT_VALIDATION,
                    "severity": "medium",
                    "message": f"Invalid phone format: {phone}",
                    "field": "phones",
                    "value": phone,
                })

        # Validate analytics IDs
        analytics = extraction_result.get("analytics_access", {})
        ga_ids = analytics.get("google_analytics", {}).get("property_ids", [])
        for ga_id in ga_ids:
            if not (ga_id.startswith("UA-") or ga_id.startswith("G-")):
                issues.append({
                    "rule": ValidationRule.FORMAT_VALIDATION,
                    "severity": "medium",
                    "message": f"Invalid Google Analytics ID format: {ga_id}",
                    "field": "google_analytics.property_ids",
                    "value": ga_id,
                })

        return issues

    async def _validate_cross_fields(
        self,
        extraction_result: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Validate cross-field consistency"""
        issues = []

        # Check if practice has contact info
        practice_info = extraction_result.get("practice_info", {})
        has_practice_name = bool(practice_info.get("practice_name"))
        has_contacts = bool(
            practice_info.get("emails") or
            practice_info.get("phones") or
            practice_info.get("websites")
        )

        if has_practice_name and not has_contacts:
            issues.append({
                "rule": ValidationRule.CROSS_FIELD_VALIDATION,
                "severity": "medium",
                "message": "Practice name found but no contact information",
                "field": "practice_info",
                "value": None,
            })

        # Check if analytics/ads accounts have emails
        analytics = extraction_result.get("analytics_access", {})
        ga_ids = analytics.get("google_analytics", {}).get("property_ids", [])
        ga_emails = analytics.get("google_analytics", {}).get("access_emails", [])

        if ga_ids and not ga_emails:
            issues.append({
                "rule": ValidationRule.CROSS_FIELD_VALIDATION,
                "severity": "low",
                "message": "Google Analytics IDs found but no access emails",
                "field": "analytics_access.google_analytics",
                "value": None,
            })

        ad_accounts = extraction_result.get("ad_accounts", {})
        google_ads_ids = ad_accounts.get("google_ads", {}).get("account_ids", [])
        google_ads_emails = ad_accounts.get("google_ads", {}).get("access_emails", [])

        if google_ads_ids and not google_ads_emails:
            issues.append({
                "rule": ValidationRule.CROSS_FIELD_VALIDATION,
                "severity": "low",
                "message": "Google Ads IDs found but no access emails",
                "field": "ad_accounts.google_ads",
                "value": None,
            })

        return issues

    async def create_review_item(
        self,
        document_id: str,
        extraction_result: Dict[str, Any],
        validation_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create review queue item

        Args:
            document_id: Document ID
            extraction_result: Extraction result
            validation_result: Validation result

        Returns:
            Review item for human review
        """
        review_item = {
            "document_id": document_id,
            "status": "pending_review",
            "confidence": validation_result["overall_confidence"],
            "issues": validation_result["issues"],
            "extracted_data": extraction_result,
            "review_priority": self._calculate_priority(validation_result),
        }

        self.logger.info(
            "review_item_created",
            document_id=document_id,
            priority=review_item["review_priority"],
            issues_count=len(validation_result["issues"]),
        )

        return review_item

    def _calculate_priority(self, validation_result: Dict[str, Any]) -> str:
        """Calculate review priority"""
        high_severity = validation_result["high_severity_count"]
        confidence = validation_result["overall_confidence"]

        if high_severity >= 3 or confidence < 0.5:
            return "high"
        elif high_severity >= 1 or confidence < 0.8:
            return "medium"
        else:
            return "low"
