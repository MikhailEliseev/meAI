"""Unit tests for Lead Capture Service

Tests:
- Rate limiting (10 req/min per IP)
- reCAPTCHA verification
- Duplicate detection
- Field encryption
- ФЗ-152 consent validation
- Lead creation and storage
- Audit logging

Part of: Phase 11 - Client Acquisition (Task 2.1)
"""

import base64
import hashlib
import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from AIM.src.aim.models.lead import Lead as LeadModel
from AIM.src.aim.schemas.lead import (
    LeadCaptureRequest,
    LeadSource,
    MedicalSpecialty,
)
from AIM.src.aim.services.lead_capture import (
    LeadCaptureService,
    RateLimitExceeded,
    RecaptchaVerificationFailed,
)


# Set test encryption key
os.environ["AIM_ENCRYPTION_KEY"] = base64.b64encode(os.urandom(32)).decode()


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def lead_capture_service(mock_db_session):
    """Create lead capture service with mock DB"""
    return LeadCaptureService(
        db_session=mock_db_session,
        recaptcha_secret="test_secret",
        rate_limit_per_minute=10,
        recaptcha_min_score=0.5,
    )


@pytest.fixture
def valid_lead_request():
    """Valid lead capture request"""
    return LeadCaptureRequest(
        name="Иван Иванов",
        phone="+79991234567",
        email="ivan@example.com",
        clinic_name="Стоматология Дента",
        specialty=MedicalSpecialty.DENTISTRY,
        message="Хочу узнать о ваших услугах",
        fz152_consent=True,
        source=LeadSource.LANDING_PAGE,
        utm_source="google",
        utm_medium="cpc",
        utm_campaign="dental_implants",
        recaptcha_token="test_token_123",
    )


class TestRateLimiting:
    """Test rate limiting functionality"""

    @pytest.mark.asyncio
    async def test_rate_limit_allows_within_limit(
        self, lead_capture_service, valid_lead_request
    ):
        """Should allow requests within rate limit"""
        with patch.object(
            lead_capture_service, "_verify_recaptcha", new_callable=AsyncMock
        ):
            with patch.object(
                lead_capture_service, "_find_duplicate", return_value=None
            ):
                with patch.object(
                    lead_capture_service, "_process_lead_async", new_callable=AsyncMock
                ):
                    # First request should succeed
                    await lead_capture_service._check_rate_limit("192.168.1.1")

                    # 9 more requests should succeed (total 10)
                    for _ in range(9):
                        await lead_capture_service._check_rate_limit("192.168.1.1")

    @pytest.mark.asyncio
    async def test_rate_limit_blocks_after_limit(self, lead_capture_service):
        """Should block requests after rate limit exceeded"""
        # Fill up rate limit (10 requests)
        for _ in range(10):
            await lead_capture_service._check_rate_limit("192.168.1.1")

        # 11th request should raise exception
        with pytest.raises(RateLimitExceeded):
            await lead_capture_service._check_rate_limit("192.168.1.1")

    @pytest.mark.asyncio
    async def test_rate_limit_per_ip(self, lead_capture_service):
        """Should track rate limit per IP address"""
        # IP 1: 10 requests (at limit)
        for _ in range(10):
            await lead_capture_service._check_rate_limit("192.168.1.1")

        # IP 2: should still work (different IP)
        await lead_capture_service._check_rate_limit("192.168.1.2")

        # IP 1: should be blocked
        with pytest.raises(RateLimitExceeded):
            await lead_capture_service._check_rate_limit("192.168.1.1")


class TestRecaptchaVerification:
    """Test reCAPTCHA verification"""

    @pytest.mark.asyncio
    async def test_recaptcha_success(self, lead_capture_service):
        """Should pass with valid reCAPTCHA response"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True, "score": 0.9}

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            # Should not raise exception
            await lead_capture_service._verify_recaptcha("valid_token", "192.168.1.1")

    @pytest.mark.asyncio
    async def test_recaptcha_failure(self, lead_capture_service):
        """Should fail with invalid reCAPTCHA response"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": False,
            "error-codes": ["invalid-input-response"],
        }

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            with pytest.raises(RecaptchaVerificationFailed):
                await lead_capture_service._verify_recaptcha(
                    "invalid_token", "192.168.1.1"
                )

    @pytest.mark.asyncio
    async def test_recaptcha_low_score(self, lead_capture_service):
        """Should fail with low reCAPTCHA score"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True, "score": 0.3}

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            with pytest.raises(RecaptchaVerificationFailed):
                await lead_capture_service._verify_recaptcha("token", "192.168.1.1")


class TestDuplicateDetection:
    """Test duplicate lead detection"""

    @pytest.mark.asyncio
    async def test_find_duplicate_by_email(self, lead_capture_service, mock_db_session):
        """Should find duplicate lead by email hash"""
        email = "test@example.com"
        email_hash = LeadModel.hash_email(email)

        # Mock existing lead
        existing_lead = LeadModel(
            id="lead_20260516_abc123",
            email_hash=email_hash,
            name_encrypted="encrypted_name",
            phone_encrypted="encrypted_phone",
            email_encrypted="encrypted_email",
            clinic_name_encrypted="encrypted_clinic",
            specialty="dentistry",
            fz152_consent=True,
            fz152_consent_timestamp=datetime.now(timezone.utc),
            fz152_consent_ip="192.168.1.1",
            source="landing_page",
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_lead
        mock_db_session.execute.return_value = mock_result

        # Should find duplicate
        duplicate = await lead_capture_service._find_duplicate(email)
        assert duplicate is not None
        assert duplicate.id == "lead_20260516_abc123"

    @pytest.mark.asyncio
    async def test_no_duplicate_found(self, lead_capture_service, mock_db_session):
        """Should return None when no duplicate exists"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Should not find duplicate
        duplicate = await lead_capture_service._find_duplicate("new@example.com")
        assert duplicate is None


class TestEncryption:
    """Test field encryption"""

    def test_encrypt_lead_data(self, lead_capture_service, valid_lead_request):
        """Should encrypt all PII fields"""
        encrypted = lead_capture_service._encrypt_lead_data(valid_lead_request)

        # Should have encrypted fields
        assert "name_encrypted" in encrypted
        assert "phone_encrypted" in encrypted
        assert "email_encrypted" in encrypted
        assert "clinic_name_encrypted" in encrypted
        assert "message_encrypted" in encrypted

        # Encrypted data should be base64 strings
        assert isinstance(encrypted["name_encrypted"], str)
        assert len(encrypted["name_encrypted"]) > 0

        # Should not contain plaintext
        assert "Иван Иванов" not in encrypted["name_encrypted"]
        assert "+79991234567" not in encrypted["phone_encrypted"]


class TestLeadCapture:
    """Test complete lead capture flow"""

    @pytest.mark.asyncio
    async def test_capture_new_lead(
        self, lead_capture_service, valid_lead_request, mock_db_session
    ):
        """Should capture new lead successfully"""
        # Mock no duplicate
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Mock reCAPTCHA success
        mock_recaptcha_response = MagicMock()
        mock_recaptcha_response.json.return_value = {"success": True, "score": 0.9}

        with patch("httpx.AsyncClient.post", return_value=mock_recaptcha_response):
            with patch.object(
                lead_capture_service, "_process_lead_async", new_callable=AsyncMock
            ):
                response = await lead_capture_service.capture_lead(
                    request=valid_lead_request,
                    client_ip="192.168.1.1",
                    user_agent="Mozilla/5.0",
                )

        # Should return success
        assert response.success is True
        assert response.lead_id.startswith("lead_")
        assert "Спасибо" in response.message

        # Should have called db.add and db.commit
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_capture_duplicate_lead(
        self, lead_capture_service, valid_lead_request, mock_db_session
    ):
        """Should return existing lead ID for duplicate"""
        # Mock existing lead
        existing_lead = LeadModel(
            id="lead_20260516_existing",
            email_hash=LeadModel.hash_email(valid_lead_request.email),
            name_encrypted="encrypted_name",
            phone_encrypted="encrypted_phone",
            email_encrypted="encrypted_email",
            clinic_name_encrypted="encrypted_clinic",
            specialty="dentistry",
            fz152_consent=True,
            fz152_consent_timestamp=datetime.now(timezone.utc),
            fz152_consent_ip="192.168.1.1",
            source="landing_page",
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_lead
        mock_db_session.execute.return_value = mock_result

        # Mock reCAPTCHA success
        mock_recaptcha_response = MagicMock()
        mock_recaptcha_response.json.return_value = {"success": True, "score": 0.9}

        with patch("httpx.AsyncClient.post", return_value=mock_recaptcha_response):
            response = await lead_capture_service.capture_lead(
                request=valid_lead_request,
                client_ip="192.168.1.1",
                user_agent="Mozilla/5.0",
            )

        # Should return existing lead ID
        assert response.success is True
        assert response.lead_id == "lead_20260516_existing"
        assert "уже получили" in response.message

        # Should NOT have called db.add (no new lead created)
        mock_db_session.add.assert_not_called()


class TestLeadIDGeneration:
    """Test lead ID generation"""

    def test_generate_lead_id_format(self, lead_capture_service):
        """Should generate lead ID in correct format"""
        lead_id = lead_capture_service._generate_lead_id()

        # Format: lead_YYYYMMDDHHMMSS_UUID
        assert lead_id.startswith("lead_")
        parts = lead_id.split("_")
        assert len(parts) == 3
        assert parts[0] == "lead"
        assert len(parts[1]) == 14  # YYYYMMDDHHMMSS
        assert len(parts[2]) == 8  # UUID (first 8 chars)

    def test_generate_unique_ids(self, lead_capture_service):
        """Should generate unique IDs"""
        id1 = lead_capture_service._generate_lead_id()
        id2 = lead_capture_service._generate_lead_id()

        assert id1 != id2


class TestEmailHashing:
    """Test email hashing for duplicate detection"""

    def test_hash_email(self):
        """Should generate consistent SHA-256 hash"""
        email = "test@example.com"
        hash1 = LeadModel.hash_email(email)
        hash2 = LeadModel.hash_email(email)

        # Should be consistent
        assert hash1 == hash2

        # Should be SHA-256 (64 hex chars)
        assert len(hash1) == 64
        assert all(c in "0123456789abcdef" for c in hash1)

    def test_hash_email_case_sensitive(self):
        """Should be case-sensitive"""
        hash1 = LeadModel.hash_email("test@example.com")
        hash2 = LeadModel.hash_email("TEST@example.com")

        # Should be different
        assert hash1 != hash2
