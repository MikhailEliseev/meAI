"""
Tests for Document Validator
"""

import pytest
from src.aim.services.document_processing.validator import (
    DocumentValidator,
    ValidationStatus,
    ValidationRule,
)


@pytest.fixture
def validator():
    """Create validator instance"""
    return DocumentValidator(
        confidence_threshold=0.95,
        required_fields=["practice_name", "location"],
    )


@pytest.fixture
def high_confidence_extraction():
    """High confidence extraction result"""
    return {
        "practice_info": {
            "practice_name": "Dental Clinic",
            "location": "Moscow",
            "specialty": "Dentistry",
            "emails": ["info@dental.com"],
            "phones": ["+7 (495) 123-45-67"],
            "websites": ["https://dental.com"],
            "confidence": 0.98,
        },
        "analytics_access": {
            "google_analytics": {
                "property_ids": ["UA-123456-1"],
                "access_emails": ["analytics@dental.com"],
            },
            "yandex_metrica": {
                "counter_ids": ["12345678"],
                "access_emails": ["metrica@dental.com"],
            },
            "confidence": 0.96,
        },
        "ad_accounts": {
            "google_ads": {
                "account_ids": ["123-456-7890"],
                "access_emails": ["ads@dental.com"],
            },
            "yandex_direct": {
                "client_ids": ["9876543210"],
                "access_emails": ["direct@dental.com"],
            },
            "confidence": 0.97,
        },
        "overall_confidence": 0.97,
    }


@pytest.fixture
def low_confidence_extraction():
    """Low confidence extraction result"""
    return {
        "practice_info": {
            "practice_name": None,
            "location": "Moscow",
            "specialty": None,
            "emails": [],
            "phones": [],
            "websites": [],
            "confidence": 0.2,
        },
        "analytics_access": {
            "google_analytics": {
                "property_ids": [],
                "access_emails": [],
            },
            "yandex_metrica": {
                "counter_ids": [],
                "access_emails": [],
            },
            "confidence": 0.0,
        },
        "ad_accounts": {
            "google_ads": {
                "account_ids": [],
                "access_emails": [],
            },
            "yandex_direct": {
                "client_ids": [],
                "access_emails": [],
            },
            "confidence": 0.0,
        },
        "overall_confidence": 0.08,
    }


class TestDocumentValidator:
    """Test document validator"""

    @pytest.mark.asyncio
    async def test_init_with_defaults(self):
        """Test initialization with default parameters"""
        validator = DocumentValidator()

        assert validator.confidence_threshold == 0.95
        assert validator.required_fields == []

    @pytest.mark.asyncio
    async def test_init_with_custom_params(self):
        """Test initialization with custom parameters"""
        validator = DocumentValidator(
            confidence_threshold=0.9,
            required_fields=["practice_name"],
        )

        assert validator.confidence_threshold == 0.9
        assert validator.required_fields == ["practice_name"]

    @pytest.mark.asyncio
    async def test_validate_high_confidence_approved(
        self,
        validator,
        high_confidence_extraction,
    ):
        """Test validation of high confidence extraction"""
        result = await validator.validate_extraction(high_confidence_extraction)

        assert result["status"] == ValidationStatus.APPROVED
        assert result["overall_confidence"] == 0.97
        assert result["issues_count"] == 0
        assert result["high_severity_count"] == 0
        assert result["requires_review"] is False

    @pytest.mark.asyncio
    async def test_validate_low_confidence_review(
        self,
        validator,
        low_confidence_extraction,
    ):
        """Test validation of low confidence extraction"""
        result = await validator.validate_extraction(low_confidence_extraction)

        assert result["status"] == ValidationStatus.REVIEW
        assert result["overall_confidence"] == 0.08
        assert result["issues_count"] > 0
        assert result["high_severity_count"] > 0
        assert result["requires_review"] is True

    @pytest.mark.asyncio
    async def test_confidence_threshold_rule(self, validator):
        """Test confidence threshold validation rule"""
        extraction = {
            "practice_info": {
                "practice_name": "Clinic",
                "location": "Moscow",
                "confidence": 0.9,
            },
            "analytics_access": {"confidence": 0.9},
            "ad_accounts": {"confidence": 0.9},
            "overall_confidence": 0.9,  # Below 0.95 threshold
        }

        result = await validator.validate_extraction(extraction)

        # Should have confidence threshold issue
        confidence_issues = [
            issue for issue in result["issues"]
            if issue["rule"] == ValidationRule.CONFIDENCE_THRESHOLD
        ]

        assert len(confidence_issues) == 1
        assert confidence_issues[0]["severity"] == "high"
        assert "below threshold" in confidence_issues[0]["message"]

    @pytest.mark.asyncio
    async def test_required_fields_rule(self, validator):
        """Test required fields validation rule"""
        extraction = {
            "practice_info": {
                "practice_name": None,  # Missing required field
                "location": "Moscow",
                "confidence": 0.98,
            },
            "analytics_access": {"confidence": 0.98},
            "ad_accounts": {"confidence": 0.98},
            "overall_confidence": 0.98,
        }

        result = await validator.validate_extraction(extraction)

        # Should have required field issue
        required_issues = [
            issue for issue in result["issues"]
            if issue["rule"] == ValidationRule.REQUIRED_FIELDS
        ]

        assert len(required_issues) == 1
        assert required_issues[0]["field"] == "practice_name"
        assert required_issues[0]["severity"] == "high"

    @pytest.mark.asyncio
    async def test_email_format_validation(self, validator):
        """Test email format validation"""
        extraction = {
            "practice_info": {
                "practice_name": "Clinic",
                "location": "Moscow",
                "emails": ["invalid-email", "valid@email.com"],
                "confidence": 0.98,
            },
            "analytics_access": {"confidence": 0.98},
            "ad_accounts": {"confidence": 0.98},
            "overall_confidence": 0.98,
        }

        result = await validator.validate_extraction(extraction)

        # Should have email format issue
        format_issues = [
            issue for issue in result["issues"]
            if issue["rule"] == ValidationRule.FORMAT_VALIDATION
            and issue["field"] == "emails"
        ]

        assert len(format_issues) == 1
        assert "invalid-email" in format_issues[0]["message"]
        assert format_issues[0]["severity"] == "medium"

    @pytest.mark.asyncio
    async def test_phone_format_validation(self, validator):
        """Test phone format validation"""
        extraction = {
            "practice_info": {
                "practice_name": "Clinic",
                "location": "Moscow",
                "phones": ["123", "+7 (495) 123-45-67"],  # First is too short
                "confidence": 0.98,
            },
            "analytics_access": {"confidence": 0.98},
            "ad_accounts": {"confidence": 0.98},
            "overall_confidence": 0.98,
        }

        result = await validator.validate_extraction(extraction)

        # Should have phone format issue
        format_issues = [
            issue for issue in result["issues"]
            if issue["rule"] == ValidationRule.FORMAT_VALIDATION
            and issue["field"] == "phones"
        ]

        assert len(format_issues) == 1
        assert "123" in format_issues[0]["message"]

    @pytest.mark.asyncio
    async def test_analytics_id_format_validation(self, validator):
        """Test analytics ID format validation"""
        extraction = {
            "practice_info": {
                "practice_name": "Clinic",
                "location": "Moscow",
                "confidence": 0.98,
            },
            "analytics_access": {
                "google_analytics": {
                    "property_ids": ["INVALID-ID", "UA-123456-1"],
                    "access_emails": [],
                },
                "yandex_metrica": {
                    "counter_ids": [],
                    "access_emails": [],
                },
                "confidence": 0.98,
            },
            "ad_accounts": {"confidence": 0.98},
            "overall_confidence": 0.98,
        }

        result = await validator.validate_extraction(extraction)

        # Should have GA ID format issue
        format_issues = [
            issue for issue in result["issues"]
            if issue["rule"] == ValidationRule.FORMAT_VALIDATION
            and "google_analytics" in issue["field"]
        ]

        assert len(format_issues) == 1
        assert "INVALID-ID" in format_issues[0]["message"]

    @pytest.mark.asyncio
    async def test_cross_field_practice_without_contacts(self, validator):
        """Test cross-field validation: practice without contacts"""
        extraction = {
            "practice_info": {
                "practice_name": "Clinic",
                "location": "Moscow",
                "emails": [],
                "phones": [],
                "websites": [],
                "confidence": 0.98,
            },
            "analytics_access": {"confidence": 0.98},
            "ad_accounts": {"confidence": 0.98},
            "overall_confidence": 0.98,
        }

        result = await validator.validate_extraction(extraction)

        # Should have cross-field issue
        cross_issues = [
            issue for issue in result["issues"]
            if issue["rule"] == ValidationRule.CROSS_FIELD_VALIDATION
            and "contact information" in issue["message"]
        ]

        assert len(cross_issues) == 1
        assert cross_issues[0]["severity"] == "medium"

    @pytest.mark.asyncio
    async def test_cross_field_analytics_without_emails(self, validator):
        """Test cross-field validation: analytics IDs without emails"""
        extraction = {
            "practice_info": {
                "practice_name": "Clinic",
                "location": "Moscow",
                "confidence": 0.98,
            },
            "analytics_access": {
                "google_analytics": {
                    "property_ids": ["UA-123456-1"],
                    "access_emails": [],  # Missing emails
                },
                "yandex_metrica": {
                    "counter_ids": [],
                    "access_emails": [],
                },
                "confidence": 0.98,
            },
            "ad_accounts": {"confidence": 0.98},
            "overall_confidence": 0.98,
        }

        result = await validator.validate_extraction(extraction)

        # Should have cross-field issue
        cross_issues = [
            issue for issue in result["issues"]
            if issue["rule"] == ValidationRule.CROSS_FIELD_VALIDATION
            and "access emails" in issue["message"]
        ]

        assert len(cross_issues) >= 1
        assert any("Google Analytics" in issue["message"] for issue in cross_issues)

    @pytest.mark.asyncio
    async def test_create_review_item(self, validator, low_confidence_extraction):
        """Test review item creation"""
        validation_result = await validator.validate_extraction(
            low_confidence_extraction
        )

        review_item = await validator.create_review_item(
            document_id="doc-123",
            extraction_result=low_confidence_extraction,
            validation_result=validation_result,
        )

        assert review_item["document_id"] == "doc-123"
        assert review_item["status"] == "pending_review"
        assert review_item["confidence"] == 0.08
        assert len(review_item["issues"]) > 0
        assert "review_priority" in review_item
        assert review_item["extracted_data"] == low_confidence_extraction

    @pytest.mark.asyncio
    async def test_priority_calculation_high(self, validator):
        """Test high priority calculation"""
        validation_result = {
            "overall_confidence": 0.3,
            "high_severity_count": 3,
            "issues": [],
        }

        priority = validator._calculate_priority(validation_result)

        assert priority == "high"

    @pytest.mark.asyncio
    async def test_priority_calculation_medium(self, validator):
        """Test medium priority calculation"""
        validation_result = {
            "overall_confidence": 0.7,
            "high_severity_count": 1,
            "issues": [],
        }

        priority = validator._calculate_priority(validation_result)

        assert priority == "medium"

    @pytest.mark.asyncio
    async def test_priority_calculation_low(self, validator):
        """Test low priority calculation"""
        validation_result = {
            "overall_confidence": 0.85,
            "high_severity_count": 0,
            "issues": [],
        }

        priority = validator._calculate_priority(validation_result)

        assert priority == "low"

    @pytest.mark.asyncio
    async def test_multiple_validation_rules(self, validator):
        """Test multiple validation rules triggered"""
        extraction = {
            "practice_info": {
                "practice_name": None,  # Missing required
                "location": "Moscow",
                "emails": ["invalid"],  # Invalid format
                "phones": [],
                "websites": [],
                "confidence": 0.5,
            },
            "analytics_access": {"confidence": 0.5},
            "ad_accounts": {"confidence": 0.5},
            "overall_confidence": 0.5,  # Below threshold
        }

        result = await validator.validate_extraction(extraction)

        # Should have multiple issues
        assert result["issues_count"] >= 3

        # Check different rule types present
        rule_types = {issue["rule"] for issue in result["issues"]}
        assert ValidationRule.CONFIDENCE_THRESHOLD in rule_types
        assert ValidationRule.REQUIRED_FIELDS in rule_types
        assert ValidationRule.FORMAT_VALIDATION in rule_types

    @pytest.mark.asyncio
    async def test_no_issues_approved(self, validator, high_confidence_extraction):
        """Test that extraction with no issues is approved"""
        result = await validator.validate_extraction(high_confidence_extraction)

        assert result["status"] == ValidationStatus.APPROVED
        assert result["issues_count"] == 0
        assert result["requires_review"] is False
