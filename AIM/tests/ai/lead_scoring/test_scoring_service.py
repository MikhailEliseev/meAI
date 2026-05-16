"""Unit tests for Lead Scoring Service

Tests:
- Rule-based scoring (MVP implementation)
- Tier assignment (Hot/Warm/Cold)
- Score explanation generation
- Feature normalization
- Edge cases and boundary conditions

Part of: Phase 11 Sprint 2 - Task 2.2
"""

from datetime import datetime, timezone

import pytest

from AIM.src.aim.ai.lead_scoring.scoring_service import LeadScoringService
from AIM.src.aim.models.lead import Lead as LeadModel
from AIM.src.aim.schemas.lead import MedicalSpecialty


@pytest.fixture
def scoring_service():
    """Create scoring service instance (rule-based)"""
    return LeadScoringService(model_path=None)


@pytest.fixture
def high_quality_lead():
    """Create high-quality lead (should score Hot)"""
    return LeadModel(
        id="lead_20260515_hot123",
        created_at=datetime(2026, 5, 15, 14, 30, 0, tzinfo=timezone.utc),  # Friday 14:30
        updated_at=datetime(2026, 5, 15, 14, 30, 0, tzinfo=timezone.utc),
        name_encrypted="encrypted_name",
        phone_encrypted="encrypted_phone",
        email_encrypted="encrypted_email",
        email_hash="hash123",
        clinic_name_encrypted="encrypted_clinic",
        message_encrypted="x" * 250,  # Long detailed message
        specialty=MedicalSpecialty.PLASTIC_SURGERY.value,  # High-value
        fz152_consent=True,
        fz152_consent_timestamp=datetime.now(timezone.utc),
        fz152_consent_ip="192.168.1.1",
        source="organic_search",  # High-intent
        utm_source="google",
        utm_medium="organic",
        utm_campaign="plastic_surgery_implants",  # High-intent
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
        processed=False,
    )


@pytest.fixture
def medium_quality_lead():
    """Create medium-quality lead (should score Warm)"""
    return LeadModel(
        id="lead_20260515_warm123",
        created_at=datetime(2026, 5, 15, 19, 30, 0, tzinfo=timezone.utc),  # Friday evening
        updated_at=datetime(2026, 5, 15, 19, 30, 0, tzinfo=timezone.utc),
        name_encrypted="encrypted_name",
        phone_encrypted="encrypted_phone",
        email_encrypted="encrypted_email",
        email_hash="hash456",
        clinic_name_encrypted="encrypted_clinic",
        message_encrypted="x" * 100,  # Medium message
        specialty=MedicalSpecialty.COSMETOLOGY.value,  # Medium-value
        fz152_consent=True,
        fz152_consent_timestamp=datetime.now(timezone.utc),
        fz152_consent_ip="192.168.1.2",
        source="paid_ads",
        utm_source="yandex",
        utm_medium="cpc",
        utm_campaign="general_promo",
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0) Mobile Safari",
        processed=False,
    )


@pytest.fixture
def low_quality_lead():
    """Create low-quality lead (should score Cold)"""
    return LeadModel(
        id="lead_20260517_cold123",
        created_at=datetime(2026, 5, 17, 23, 0, 0, tzinfo=timezone.utc),  # Saturday night
        updated_at=datetime(2026, 5, 17, 23, 0, 0, tzinfo=timezone.utc),
        name_encrypted="encrypted_name",
        phone_encrypted="encrypted_phone",
        email_encrypted="encrypted_email",
        email_hash="hash789",
        clinic_name_encrypted="encrypted_clinic",
        message_encrypted="x" * 20,  # Short message
        specialty=MedicalSpecialty.OTHER.value,  # Low-value
        fz152_consent=True,
        fz152_consent_timestamp=datetime.now(timezone.utc),
        fz152_consent_ip="192.168.1.3",
        source="social_media",
        utm_source=None,
        utm_medium=None,
        utm_campaign=None,
        user_agent="Mozilla/5.0 (iPhone) Mobile",
        processed=False,
    )


class TestTierAssignment:
    """Test tier assignment logic"""

    @pytest.mark.asyncio
    async def test_assign_hot_tier(self, scoring_service, high_quality_lead):
        """Should assign Hot tier for score >= 80"""
        metadata = {
            "user_agent": high_quality_lead.user_agent,
            "utm_campaign": high_quality_lead.utm_campaign,
            "session_duration": 200,
        }

        result = await scoring_service.score_lead(high_quality_lead, metadata)

        assert result.tier == "Hot"
        assert result.score >= 80

    @pytest.mark.asyncio
    async def test_assign_warm_tier(self, scoring_service, medium_quality_lead):
        """Should assign Warm tier for score 50-79"""
        metadata = {
            "user_agent": medium_quality_lead.user_agent,
            "utm_campaign": medium_quality_lead.utm_campaign,
            "session_duration": 100,
        }

        result = await scoring_service.score_lead(medium_quality_lead, metadata)

        assert result.tier == "Warm"
        assert 50 <= result.score < 80

    @pytest.mark.asyncio
    async def test_assign_cold_tier(self, scoring_service, low_quality_lead):
        """Should assign Cold tier for score < 50"""
        metadata = {
            "user_agent": low_quality_lead.user_agent,
            "utm_campaign": low_quality_lead.utm_campaign,
            "session_duration": 30,
        }

        result = await scoring_service.score_lead(low_quality_lead, metadata)

        assert result.tier == "Cold"
        assert result.score < 50


class TestScoreCalculation:
    """Test score calculation logic"""

    @pytest.mark.asyncio
    async def test_score_range(self, scoring_service, high_quality_lead):
        """Should return score in range 0-100"""
        metadata = {"session_duration": 150}

        result = await scoring_service.score_lead(high_quality_lead, metadata)

        assert 0 <= result.score <= 100

    @pytest.mark.asyncio
    async def test_high_value_specialty_bonus(self, scoring_service, high_quality_lead):
        """Should give bonus for high-value specialty"""
        metadata = {"session_duration": 150}

        result = await scoring_service.score_lead(high_quality_lead, metadata)

        # Plastic surgery should contribute to high score
        assert result.score >= 70

    @pytest.mark.asyncio
    async def test_business_hours_bonus(self, scoring_service, high_quality_lead):
        """Should give bonus for business hours submission"""
        # Friday 14:30 = business hours
        metadata = {"session_duration": 150}

        result = await scoring_service.score_lead(high_quality_lead, metadata)

        # Business hours should contribute to score
        assert "business" in str(result.factors.get("is_business_hours", "")).lower() or result.factors.get("is_business_hours") is True

    @pytest.mark.asyncio
    async def test_organic_traffic_bonus(self, scoring_service, high_quality_lead):
        """Should give bonus for organic search traffic"""
        metadata = {"session_duration": 150}

        result = await scoring_service.score_lead(high_quality_lead, metadata)

        # Organic search should contribute to high score
        assert result.factors["is_organic"] is True

    @pytest.mark.asyncio
    async def test_long_message_bonus(self, scoring_service, high_quality_lead):
        """Should give bonus for detailed message"""
        metadata = {"session_duration": 150}

        result = await scoring_service.score_lead(high_quality_lead, metadata)

        # Long message should contribute to high score
        assert result.factors["message_quality"] >= 7


class TestExplanation:
    """Test score explanation generation"""

    @pytest.mark.asyncio
    async def test_explanation_exists(self, scoring_service, high_quality_lead):
        """Should provide explanation for score"""
        metadata = {"session_duration": 150}

        result = await scoring_service.score_lead(high_quality_lead, metadata)

        assert len(result.explanation) > 0
        assert len(result.explanation) <= 5  # Top 5 factors

    @pytest.mark.asyncio
    async def test_explanation_format(self, scoring_service, high_quality_lead):
        """Should provide human-readable explanations"""
        metadata = {"session_duration": 150}

        result = await scoring_service.score_lead(high_quality_lead, metadata)

        # Each explanation should be a string
        for explanation in result.explanation:
            assert isinstance(explanation, str)
            assert len(explanation) > 0

    @pytest.mark.asyncio
    async def test_explanation_includes_specialty(self, scoring_service, high_quality_lead):
        """Should mention high-value specialty in explanation"""
        metadata = {"session_duration": 150}

        result = await scoring_service.score_lead(high_quality_lead, metadata)

        # Should mention plastic surgery
        explanations_text = " ".join(result.explanation).lower()
        assert "plastic" in explanations_text or "surgery" in explanations_text or "specialty" in explanations_text


class TestFeatureExtraction:
    """Test feature extraction integration"""

    @pytest.mark.asyncio
    async def test_all_features_extracted(self, scoring_service, high_quality_lead):
        """Should extract all 30+ features"""
        metadata = {
            "user_agent": high_quality_lead.user_agent,
            "utm_campaign": high_quality_lead.utm_campaign,
            "session_duration": 150,
        }

        result = await scoring_service.score_lead(high_quality_lead, metadata)

        # Should have all major feature categories
        assert "specialty" in result.factors
        assert "message_quality" in result.factors
        assert "form_completion" in result.factors
        assert "device_type" in result.factors
        assert "day_of_week" in result.factors
        assert "traffic_source" in result.factors
        assert "previous_submissions" in result.factors
        assert "fz152_consent" in result.factors

    @pytest.mark.asyncio
    async def test_factors_stored(self, scoring_service, high_quality_lead):
        """Should store all extracted factors in result"""
        metadata = {"session_duration": 150}

        result = await scoring_service.score_lead(high_quality_lead, metadata)

        # Factors should be a dictionary
        assert isinstance(result.factors, dict)
        assert len(result.factors) >= 20  # At least 20 features


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    @pytest.mark.asyncio
    async def test_minimal_lead(self, scoring_service):
        """Should handle lead with minimal data"""
        minimal_lead = LeadModel(
            id="lead_minimal",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            name_encrypted="name",
            phone_encrypted="phone",
            email_encrypted="email",
            email_hash="hash",
            clinic_name_encrypted="clinic",
            message_encrypted=None,  # No message
            specialty=MedicalSpecialty.OTHER.value,
            fz152_consent=True,
            fz152_consent_timestamp=datetime.now(timezone.utc),
            fz152_consent_ip="127.0.0.1",
            source="unknown",
            processed=False,
        )

        metadata = {}

        result = await scoring_service.score_lead(minimal_lead, metadata)

        # Should still return valid score
        assert 0 <= result.score <= 100
        assert result.tier in ["Hot", "Warm", "Cold"]

    @pytest.mark.asyncio
    async def test_missing_metadata(self, scoring_service, high_quality_lead):
        """Should handle missing metadata gracefully"""
        metadata = {}  # Empty metadata

        result = await scoring_service.score_lead(high_quality_lead, metadata)

        # Should still return valid score
        assert 0 <= result.score <= 100
        assert result.tier in ["Hot", "Warm", "Cold"]

    @pytest.mark.asyncio
    async def test_scored_at_timestamp(self, scoring_service, high_quality_lead):
        """Should include scoring timestamp"""
        metadata = {"session_duration": 150}

        result = await scoring_service.score_lead(high_quality_lead, metadata)

        # Should have recent timestamp
        assert result.scored_at is not None
        assert isinstance(result.scored_at, datetime)
        assert result.scored_at.tzinfo is not None  # Should be timezone-aware


class TestRuleBased:
    """Test rule-based scoring (MVP implementation)"""

    @pytest.mark.asyncio
    async def test_uses_rule_based_when_no_model(self, high_quality_lead):
        """Should use rule-based scoring when model not available"""
        service = LeadScoringService(model_path=None)
        metadata = {"session_duration": 150}

        result = await service.score_lead(high_quality_lead, metadata)

        # Should return valid result
        assert result.score > 0
        assert result.tier in ["Hot", "Warm", "Cold"]

    @pytest.mark.asyncio
    async def test_consistent_scoring(self, scoring_service, high_quality_lead):
        """Should return consistent scores for same lead"""
        metadata = {"session_duration": 150}

        result1 = await scoring_service.score_lead(high_quality_lead, metadata)
        result2 = await scoring_service.score_lead(high_quality_lead, metadata)

        # Scores should be identical (deterministic)
        assert result1.score == result2.score
        assert result1.tier == result2.tier
