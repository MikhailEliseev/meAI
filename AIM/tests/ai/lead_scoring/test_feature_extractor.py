"""Unit tests for Lead Feature Extractor

Tests:
- Demographic feature extraction (specialty, clinic size, location)
- Behavioral feature extraction (message quality, response time, UTM)
- Engagement feature extraction (form completion, message length)
- Technical feature extraction (device, browser, session duration)
- Timing feature extraction (day of week, hour, business hours)
- Source feature extraction (traffic source, referral)
- Historical feature extraction (previous submissions, email domain)
- Compliance feature extraction (ФЗ-152 consent, data completeness)

Part of: Phase 11 Sprint 2 - Task 2.2
"""

from datetime import datetime, timezone

import pytest

from AIM.src.aim.ai.lead_scoring.feature_extractor import LeadFeatureExtractor
from AIM.src.aim.models.lead import Lead as LeadModel
from AIM.src.aim.schemas.lead import MedicalSpecialty


@pytest.fixture
def feature_extractor():
    """Create feature extractor instance"""
    return LeadFeatureExtractor()


@pytest.fixture
def sample_lead():
    """Create sample lead for testing"""
    return LeadModel(
        id="lead_20260515_test123",
        created_at=datetime(2026, 5, 15, 14, 30, 0, tzinfo=timezone.utc),  # Friday 14:30
        updated_at=datetime(2026, 5, 15, 14, 30, 0, tzinfo=timezone.utc),
        name_encrypted="encrypted_name",
        phone_encrypted="encrypted_phone",
        email_encrypted="encrypted_email",
        email_hash="hash123",
        clinic_name_encrypted="encrypted_clinic",
        message_encrypted="encrypted_message_with_some_length",
        specialty=MedicalSpecialty.PLASTIC_SURGERY.value,
        fz152_consent=True,
        fz152_consent_timestamp=datetime.now(timezone.utc),
        fz152_consent_ip="192.168.1.1",
        source="organic_search",
        utm_source="google",
        utm_medium="organic",
        utm_campaign="plastic_surgery_promo",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0",
        processed=False,
    )


class TestDemographicFeatures:
    """Test demographic feature extraction"""

    def test_extract_specialty_value(self, feature_extractor, sample_lead):
        """Should extract specialty value correctly"""
        features = feature_extractor.extract(sample_lead, {})

        assert features["specialty"] == MedicalSpecialty.PLASTIC_SURGERY.value
        assert features["specialty_value"] == 5  # Plastic surgery is high-value

    def test_extract_specialty_value_medium(self, feature_extractor, sample_lead):
        """Should assign medium value to cosmetology"""
        sample_lead.specialty = MedicalSpecialty.COSMETOLOGY.value
        features = feature_extractor.extract(sample_lead, {})

        assert features["specialty_value"] == 3

    def test_extract_specialty_value_default(self, feature_extractor, sample_lead):
        """Should assign default value to unknown specialty"""
        sample_lead.specialty = "unknown_specialty"
        features = feature_extractor.extract(sample_lead, {})

        assert features["specialty_value"] == 2  # Default value

    def test_infer_clinic_size(self, feature_extractor, sample_lead):
        """Should infer clinic size (MVP: always 'single')"""
        features = feature_extractor.extract(sample_lead, {})

        assert features["clinic_size"] == "single"

    def test_infer_location(self, feature_extractor, sample_lead):
        """Should infer location (MVP: always 'regional')"""
        features = feature_extractor.extract(sample_lead, {})

        assert features["location"] == "regional"
        assert features["location_value"] == 5


class TestBehavioralFeatures:
    """Test behavioral feature extraction"""

    def test_score_message_quality_high(self, feature_extractor, sample_lead):
        """Should score long message as high quality"""
        sample_lead.message_encrypted = "x" * 250  # Long message
        features = feature_extractor.extract(sample_lead, {})

        assert features["message_quality"] == 10

    def test_score_message_quality_medium(self, feature_extractor, sample_lead):
        """Should score medium message appropriately"""
        sample_lead.message_encrypted = "x" * 150
        features = feature_extractor.extract(sample_lead, {})

        assert features["message_quality"] == 7

    def test_score_message_quality_low(self, feature_extractor, sample_lead):
        """Should score short message as low quality"""
        sample_lead.message_encrypted = "x" * 30
        features = feature_extractor.extract(sample_lead, {})

        assert features["message_quality"] == 3

    def test_score_message_quality_none(self, feature_extractor, sample_lead):
        """Should handle missing message"""
        sample_lead.message_encrypted = None
        features = feature_extractor.extract(sample_lead, {})

        assert features["message_quality"] == 0

    def test_response_time_business_hours(self, feature_extractor, sample_lead):
        """Should detect business hours submission"""
        # Friday 14:30 UTC
        sample_lead.created_at = datetime(2026, 5, 15, 14, 30, 0, tzinfo=timezone.utc)
        features = feature_extractor.extract(sample_lead, {})

        assert features["response_time"] == "business_hours"

    def test_response_time_evening(self, feature_extractor, sample_lead):
        """Should detect evening submission"""
        # Friday 19:00 UTC
        sample_lead.created_at = datetime(2026, 5, 15, 19, 0, 0, tzinfo=timezone.utc)
        features = feature_extractor.extract(sample_lead, {})

        assert features["response_time"] == "evening"

    def test_response_time_night(self, feature_extractor, sample_lead):
        """Should detect night submission"""
        # Friday 23:00 UTC
        sample_lead.created_at = datetime(2026, 5, 15, 23, 0, 0, tzinfo=timezone.utc)
        features = feature_extractor.extract(sample_lead, {})

        assert features["response_time"] == "night"

    def test_response_time_weekend(self, feature_extractor, sample_lead):
        """Should detect weekend submission"""
        sample_lead.created_at = datetime(2026, 5, 17, 14, 0, 0, tzinfo=timezone.utc)  # Saturday
        features = feature_extractor.extract(sample_lead, {})

        assert features["response_time"] == "weekend"

    def test_utm_campaign_high_intent(self, feature_extractor, sample_lead):
        """Should score high-intent UTM campaign"""
        metadata = {"utm_campaign": "dental_implants_promo"}
        features = feature_extractor.extract(sample_lead, metadata)

        assert features["utm_campaign"] == "dental_implants_promo"
        assert features["utm_campaign_value"] == 5

    def test_utm_campaign_medium_intent(self, feature_extractor, sample_lead):
        """Should score medium-intent UTM campaign"""
        metadata = {"utm_campaign": "consultation_booking"}
        features = feature_extractor.extract(sample_lead, metadata)

        assert features["utm_campaign_value"] == 3

    def test_utm_campaign_low_intent(self, feature_extractor, sample_lead):
        """Should score low-intent UTM campaign"""
        metadata = {"utm_campaign": "general_promo"}
        features = feature_extractor.extract(sample_lead, metadata)

        assert features["utm_campaign_value"] == 1

    def test_utm_campaign_none(self, feature_extractor, sample_lead):
        """Should handle missing UTM campaign"""
        features = feature_extractor.extract(sample_lead, {})

        assert features["utm_campaign"] is None
        assert features["utm_campaign_value"] == 0


class TestEngagementFeatures:
    """Test engagement feature extraction"""

    def test_form_completion_full(self, feature_extractor, sample_lead):
        """Should calculate 100% completion when all fields filled"""
        features = feature_extractor.extract(sample_lead, {})

        assert features["form_completion"] == 1.0

    def test_form_completion_partial(self, feature_extractor, sample_lead):
        """Should calculate 80% completion when message missing"""
        sample_lead.message_encrypted = None
        features = feature_extractor.extract(sample_lead, {})

        assert features["form_completion"] == 0.8

    def test_message_length(self, feature_extractor, sample_lead):
        """Should extract message length"""
        sample_lead.message_encrypted = "x" * 150
        features = feature_extractor.extract(sample_lead, {})

        assert features["message_length"] == 150

    def test_has_phone_and_email(self, feature_extractor, sample_lead):
        """Should always be True (both required)"""
        features = feature_extractor.extract(sample_lead, {})

        assert features["has_phone_and_email"] is True


class TestTechnicalFeatures:
    """Test technical feature extraction"""

    def test_parse_device_desktop(self, feature_extractor, sample_lead):
        """Should detect desktop device"""
        metadata = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
        }
        features = feature_extractor.extract(sample_lead, metadata)

        assert features["device_type"] == "desktop"

    def test_parse_device_mobile(self, feature_extractor, sample_lead):
        """Should detect mobile device"""
        metadata = {"user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0) Mobile Safari"}
        features = feature_extractor.extract(sample_lead, metadata)

        assert features["device_type"] == "mobile"

    def test_parse_device_tablet(self, feature_extractor, sample_lead):
        """Should detect tablet device"""
        metadata = {"user_agent": "Mozilla/5.0 (iPad; CPU OS 16_0) Safari"}
        features = feature_extractor.extract(sample_lead, metadata)

        assert features["device_type"] == "tablet"

    def test_parse_browser_chrome(self, feature_extractor, sample_lead):
        """Should detect Chrome browser"""
        metadata = {"user_agent": "Mozilla/5.0 Chrome/120.0.0.0"}
        features = feature_extractor.extract(sample_lead, metadata)

        assert features["browser"] == "chrome"

    def test_parse_browser_safari(self, feature_extractor, sample_lead):
        """Should detect Safari browser"""
        metadata = {"user_agent": "Mozilla/5.0 Safari/605.1.15"}
        features = feature_extractor.extract(sample_lead, metadata)

        assert features["browser"] == "safari"

    def test_parse_browser_firefox(self, feature_extractor, sample_lead):
        """Should detect Firefox browser"""
        metadata = {"user_agent": "Mozilla/5.0 Firefox/120.0"}
        features = feature_extractor.extract(sample_lead, metadata)

        assert features["browser"] == "firefox"

    def test_session_duration(self, feature_extractor, sample_lead):
        """Should extract session duration"""
        metadata = {"session_duration": 180}
        features = feature_extractor.extract(sample_lead, metadata)

        assert features["session_duration"] == 180


class TestTimingFeatures:
    """Test timing feature extraction"""

    def test_day_of_week(self, feature_extractor, sample_lead):
        """Should extract day of week (0=Monday)"""
        # Friday 2026-05-15 = weekday 4
        sample_lead.created_at = datetime(2026, 5, 15, 14, 30, 0, tzinfo=timezone.utc)
        features = feature_extractor.extract(sample_lead, {})

        # May 15, 2026 is Friday (weekday 4)
        assert features["day_of_week"] == 4

    def test_hour_of_day(self, feature_extractor, sample_lead):
        """Should extract hour of day"""
        features = feature_extractor.extract(sample_lead, {})

        assert features["hour_of_day"] == 14

    def test_is_business_hours_true(self, feature_extractor, sample_lead):
        """Should detect business hours (weekday 9-18)"""
        # Friday 14:30 UTC
        sample_lead.created_at = datetime(2026, 5, 15, 14, 30, 0, tzinfo=timezone.utc)
        features = feature_extractor.extract(sample_lead, {})

        assert features["is_business_hours"] is True

    def test_is_business_hours_false_weekend(self, feature_extractor, sample_lead):
        """Should detect non-business hours (weekend)"""
        sample_lead.created_at = datetime(2026, 5, 17, 14, 0, 0, tzinfo=timezone.utc)  # Saturday
        features = feature_extractor.extract(sample_lead, {})

        assert features["is_business_hours"] is False

    def test_is_business_hours_false_night(self, feature_extractor, sample_lead):
        """Should detect non-business hours (night)"""
        sample_lead.created_at = datetime(2026, 5, 15, 22, 0, 0, tzinfo=timezone.utc)
        features = feature_extractor.extract(sample_lead, {})

        assert features["is_business_hours"] is False


class TestSourceFeatures:
    """Test source feature extraction"""

    def test_traffic_source(self, feature_extractor, sample_lead):
        """Should extract traffic source"""
        features = feature_extractor.extract(sample_lead, {})

        assert features["traffic_source"] == "organic_search"

    def test_is_referral_true(self, feature_extractor, sample_lead):
        """Should detect referral traffic"""
        sample_lead.source = "referral"
        features = feature_extractor.extract(sample_lead, {})

        assert features["is_referral"] is True

    def test_is_referral_false(self, feature_extractor, sample_lead):
        """Should detect non-referral traffic"""
        features = feature_extractor.extract(sample_lead, {})

        assert features["is_referral"] is False

    def test_is_organic_true(self, feature_extractor, sample_lead):
        """Should detect organic search traffic"""
        features = feature_extractor.extract(sample_lead, {})

        assert features["is_organic"] is True

    def test_is_organic_false(self, feature_extractor, sample_lead):
        """Should detect non-organic traffic"""
        sample_lead.source = "paid_ads"
        features = feature_extractor.extract(sample_lead, {})

        assert features["is_organic"] is False


class TestHistoricalFeatures:
    """Test historical feature extraction"""

    def test_previous_submissions(self, feature_extractor, sample_lead):
        """Should extract previous submissions count (MVP: always 0)"""
        features = feature_extractor.extract(sample_lead, {})

        assert features["previous_submissions"] == 0

    def test_email_domain_type(self, feature_extractor, sample_lead):
        """Should classify email domain (MVP: always 'free')"""
        features = feature_extractor.extract(sample_lead, {})

        assert features["email_domain_type"] == "free"


class TestComplianceFeatures:
    """Test compliance feature extraction"""

    def test_fz152_consent_true(self, feature_extractor, sample_lead):
        """Should extract ФЗ-152 consent"""
        features = feature_extractor.extract(sample_lead, {})

        assert features["fz152_consent"] is True

    def test_fz152_consent_false(self, feature_extractor, sample_lead):
        """Should handle missing consent"""
        sample_lead.fz152_consent = False
        features = feature_extractor.extract(sample_lead, {})

        assert features["fz152_consent"] is False

    def test_data_completeness_full(self, feature_extractor, sample_lead):
        """Should calculate 100% completeness"""
        features = feature_extractor.extract(sample_lead, {})

        assert features["data_completeness"] == 1.0

    def test_data_completeness_partial(self, feature_extractor, sample_lead):
        """Should calculate partial completeness"""
        sample_lead.message_encrypted = None
        sample_lead.utm_source = None
        sample_lead.utm_campaign = None
        features = feature_extractor.extract(sample_lead, {})

        assert features["data_completeness"] == 0.7  # 7/10 points
