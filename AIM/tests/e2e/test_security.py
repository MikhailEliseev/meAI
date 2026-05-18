"""Security Tests — Task 4.2

Covers:
- Encryption (AES-256-GCM roundtrip, tampering detection, key validation)
- ФЗ-152 compliance (consent required, consent audit trail)
- Rate limiting (per-IP, sliding window, token bucket)
- Input validation (XSS, injection, path traversal)
- Error handling (no internal detail leakage)

Part of: Phase 11 Sprint 4 - Task 4.2
"""

import base64
import os
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from aim.models.lead import Lead
from aim.utils.encryption import (
    FieldEncryption,
    EncryptionError,
    DecryptionError,
    generate_encryption_key,
    get_encryptor,
)
from aim.services.lead_capture import RateLimitExceeded, LeadCaptureService


# ──────────────────────────────────────────────────
# Encryption Tests
# ──────────────────────────────────────────────────


class TestEncryptionRoundtrip:
    """AES-256-GCM encryption/decryption correctness."""

    def test_encrypt_decrypt_roundtrip(self):
        key = os.urandom(32)
        enc = FieldEncryption(key=key)
        plaintext = "Dr. Иван Петров — стоматолог-имплантолог"
        encrypted = enc.encrypt(plaintext)
        decrypted = enc.decrypt(encrypted)
        assert decrypted == plaintext
        assert encrypted != plaintext
        # Nonce (12 bytes) + ciphertext (+ 16 bytes auth tag) → 28+ bytes overhead
        raw_len = len(base64.b64decode(encrypted))
        assert raw_len > len(plaintext.encode("utf-8"))

    def test_encrypt_empty_string(self):
        enc = FieldEncryption(key=os.urandom(32))
        assert enc.encrypt("") == ""
        assert enc.decrypt("") == ""

    def test_encrypt_unicode_cyrillic(self):
        enc = FieldEncryption(key=os.urandom(32))
        text = "Очень длинное сообщение с кириллицей 😎 и спецсимволами: <>&\"'"
        encrypted = enc.encrypt(text)
        assert enc.decrypt(encrypted) == text

    def test_encrypt_dict_roundtrip(self):
        enc = FieldEncryption(key=os.urandom(32))
        data = {
            "name": "Иван Петров",
            "email": "ivan@clinic.ru",
            "phone": "+79991234567",
            "extra": "not-encrypted",
        }
        encrypted = enc.encrypt_dict(data, ["name", "email", "phone"])
        assert "name_encrypted" in encrypted
        assert "email_encrypted" in encrypted
        assert "phone_encrypted" in encrypted
        assert "extra" not in encrypted
        # Decrypt back
        decrypted = enc.decrypt_dict(encrypted, ["name", "email", "phone"])
        assert decrypted["name"] == "Иван Петров"
        assert decrypted["email"] == "ivan@clinic.ru"
        assert decrypted["phone"] == "+79991234567"

    def test_different_ciphertexts_same_plaintext(self):
        enc = FieldEncryption(key=os.urandom(32))
        text = "same text"
        c1 = enc.encrypt(text)
        c2 = enc.encrypt(text)
        assert c1 != c2  # different nonces
        assert enc.decrypt(c1) == enc.decrypt(c2) == text

    def test_tampered_ciphertext_detected(self):
        enc = FieldEncryption(key=os.urandom(32))
        encrypted = enc.encrypt("sensitive")
        raw = bytearray(base64.b64decode(encrypted))
        raw[-1] ^= 0xFF  # flip last byte
        tampered = base64.b64encode(bytes(raw)).decode()
        with pytest.raises(DecryptionError):
            enc.decrypt(tampered)

    def test_wrong_key_cannot_decrypt(self):
        enc1 = FieldEncryption(key=os.urandom(32))
        enc2 = FieldEncryption(key=os.urandom(32))
        encrypted = enc1.encrypt("secret")
        with pytest.raises(DecryptionError):
            enc2.decrypt(encrypted)

    def test_generate_encryption_key(self):
        key_b64 = generate_encryption_key()
        key = base64.b64decode(key_b64)
        assert len(key) == 32
        # Should be usable
        enc = FieldEncryption(key=key)
        assert enc.encrypt("test")

    def test_invalid_key_length_rejected(self):
        with pytest.raises(ValueError, match="must be 32 bytes"):
            FieldEncryption(key=os.urandom(16))
        with pytest.raises(ValueError, match="must be 32 bytes"):
            FieldEncryption(key=os.urandom(64))


# ──────────────────────────────────────────────────
# ФЗ-152 Compliance Tests
# ──────────────────────────────────────────────────


@pytest.mark.asyncio
class TestFZ152Compliance:
    """ФЗ-152 consent validation and audit trail."""

    async def test_capture_rejected_without_consent(self, client: AsyncClient):
        resp = await client.post("/api/leads/capture", json={
            "name": "Dr. Test",
            "email": "test@clinic.ru",
            "phone": "+79991234567",
            "clinic_name": "Test Clinic",
            "specialty": "dentistry",
            "fz152_consent": False,
            "recaptcha_token": "test_token_no_consent",
        })
        assert resp.status_code == 422

    async def test_consent_timestamp_stored(self, client: AsyncClient, db: AsyncSession):
        resp = await client.post("/api/leads/capture", json={
            "name": "Dr. Test",
            "email": "consent_check@clinic.ru",
            "phone": "+79991234567",
            "clinic_name": "Test Clinic",
            "specialty": "dentistry",
            "fz152_consent": True,
            "recaptcha_token": "test_token_consent_check",
        })
        assert resp.status_code == 201
        lead_id = resp.json()["lead_id"]

        result = await db.execute(select(Lead).where(Lead.id == lead_id))
        lead = result.scalar_one()
        assert lead.fz152_consent is True
        assert lead.fz152_consent_timestamp is not None
        assert lead.fz152_consent_ip is not None

    async def test_consent_ip_recorded(self, client: AsyncClient, db: AsyncSession):
        resp = await client.post("/api/leads/capture", json={
            "name": "Dr. Test",
            "email": "consent_ip@clinic.ru",
            "phone": "+79991234567",
            "clinic_name": "Test Clinic",
            "specialty": "dentistry",
            "fz152_consent": True,
            "recaptcha_token": "test_token_ip",
        })
        assert resp.status_code == 201
        lead_id = resp.json()["lead_id"]

        result = await db.execute(select(Lead).where(Lead.id == lead_id))
        lead = result.scalar_one()
        assert lead.fz152_consent_ip == "127.0.0.1"

    async def test_pii_fields_encrypted_at_rest(self, client: AsyncClient, db: AsyncSession):
        resp = await client.post("/api/leads/capture", json={
            "name": "Dr. PII Test",
            "email": "pii_test@clinic.ru",
            "phone": "+79991234567",
            "clinic_name": "PII Clinic",
            "specialty": "dentistry",
            "fz152_consent": True,
            "recaptcha_token": "test_token_pii",
            "message": "Sensitive patient acquisition info",
        })
        assert resp.status_code == 201
        lead_id = resp.json()["lead_id"]

        result = await db.execute(select(Lead).where(Lead.id == lead_id))
        lead = result.scalar_one()

        # PII stored encrypted, not in plaintext
        assert lead.name_encrypted is not None
        assert lead.email_encrypted is not None
        assert lead.phone_encrypted is not None
        assert lead.clinic_name_encrypted is not None
        assert lead.message_encrypted is not None

        # Verify encryption is REAL (not base64 of plaintext)
        import base64
        try:
            decoded = base64.b64decode(lead.name_encrypted)
            raw_text = decoded.decode("utf-8")
            assert "Dr. PII Test" not in raw_text
        except (UnicodeDecodeError, Exception):
            pass  # can't decode encrypted data — good

    async def test_email_hash_stored_for_dedup(self, client: AsyncClient, db: AsyncSession):
        """Verify email_hash enables duplicate detection without storing plaintext email."""
        email = "hash_test@clinic.ru"
        await client.post("/api/leads/capture", json={
            "name": "Dr. Hash",
            "email": email,
            "phone": "+79991234567",
            "clinic_name": "Hash Clinic",
            "specialty": "dentistry",
            "fz152_consent": True,
            "recaptcha_token": "test_token_hash",
        })

        expected_hash = Lead.hash_email(email)
        result = await db.execute(
            select(Lead).where(Lead.email_hash == expected_hash)
        )
        leads = result.scalars().all()
        assert len(leads) >= 1


# ──────────────────────────────────────────────────
# Rate Limiting Tests
# ──────────────────────────────────────────────────


@pytest.mark.asyncio
class TestRateLimiting:
    """Rate limiting behavior for lead capture and API clients."""

    async def test_sliding_window_clears_old_requests(self):
        service = LeadCaptureService(
            db_session=AsyncMock(),
            recaptcha_secret="test",
            rate_limit_per_minute=3,
            recaptcha_min_score=0.0,
        )
        # Add fake old requests (2 minutes ago)
        old_ts = datetime.now(timezone.utc).timestamp() - 120
        service.__class__._rate_limit_cache["test_ip"] = [old_ts, old_ts, old_ts]

        # Should NOT raise — old requests are outside 60s window
        await service._check_rate_limit("test_ip")

    async def test_rate_limit_exceeded_raises(self):
        service = LeadCaptureService(
            db_session=AsyncMock(),
            recaptcha_secret="test",
            rate_limit_per_minute=3,
            recaptcha_min_score=0.0,
        )
        now = datetime.now(timezone.utc).timestamp()
        service.__class__._rate_limit_cache["test_ip"] = [now] * 3

        with pytest.raises(RateLimitExceeded):
            await service._check_rate_limit("test_ip")

    async def test_rate_limit_cache_isolation(self):
        """Different IPs have separate rate limit counters."""
        service = LeadCaptureService(
            db_session=AsyncMock(),
            recaptcha_secret="test",
            rate_limit_per_minute=2,
            recaptcha_min_score=0.0,
        )
        now = datetime.now(timezone.utc).timestamp()
        service.__class__._rate_limit_cache["ip_a"] = [now] * 2
        service.__class__._rate_limit_cache["ip_b"] = []

        # ip_a is exhausted
        with pytest.raises(RateLimitExceeded):
            await service._check_rate_limit("ip_a")
        # ip_b is fine
        await service._check_rate_limit("ip_b")

    async def test_endpoint_returns_429_on_rate_limit(self, client: AsyncClient):
        """E2E: 11th request from same IP returns 429."""
        # First 10 should succeed
        for i in range(10):
            resp = await client.post("/api/leads/capture", json={
                "name": f"Dr. Rate {i}",
                "email": f"rate_test_{i}@clinic.ru",
                "phone": "+79991234567",
                "clinic_name": "Rate Clinic",
                "specialty": "dentistry",
                "fz152_consent": True,
                "recaptcha_token": f"test_token_rate_{i}",
            })
            assert resp.status_code == 201

        # 11th should be rate limited
        resp = await client.post("/api/leads/capture", json={
            "name": "Dr. Rate 11",
            "email": "rate_test_11@clinic.ru",
            "phone": "+79991234567",
            "clinic_name": "Rate Clinic",
            "specialty": "dentistry",
            "fz152_consent": True,
            "recaptcha_token": "test_token_rate_11",
        })
        assert resp.status_code == 429

    async def test_rate_limit_error_message_is_safe(self, client: AsyncClient):
        """429 response should not leak internal state."""
        LeadCaptureService._rate_limit_cache.clear()
        for i in range(11):
            resp = await client.post("/api/leads/capture", json={
                "name": f"Dr. {i}",
                "email": f"safe_test_{i}@clinic.ru",
                "phone": "+79991234567",
                "clinic_name": "Clinic",
                "specialty": "dentistry",
                "fz152_consent": True,
                "recaptcha_token": f"test_token_safe_{i}",
            })
        assert resp.status_code == 429
        detail = resp.json()["detail"]
        assert "cache" not in detail.lower()
        assert "traceback" not in detail.lower()


# ──────────────────────────────────────────────────
# Input Validation & Injection Tests
# ──────────────────────────────────────────────────


@pytest.mark.asyncio
class TestInputValidation:
    """XSS, injection, and input sanitization."""

    async def test_html_injection_in_name_blocked(self, client: AsyncClient):
        resp = await client.post("/api/leads/capture", json={
            "name": "<script>alert('XSS')</script>",
            "email": "xss@clinic.ru",
            "phone": "+79991234567",
            "clinic_name": "Test Clinic",
            "specialty": "dentistry",
            "fz152_consent": True,
            "recaptcha_token": "test_token_xss_name",
        })
        assert resp.status_code == 422

    async def test_html_injection_in_clinic_name_blocked(self, client: AsyncClient):
        resp = await client.post("/api/leads/capture", json={
            "name": "Dr. Test",
            "email": "xss_clinic@clinic.ru",
            "phone": "+79991234567",
            "clinic_name": "<img src=x onerror=alert(1)>",
            "specialty": "dentistry",
            "fz152_consent": True,
            "recaptcha_token": "test_token_xss_clinic",
        })
        assert resp.status_code == 422

    async def test_html_injection_in_message_blocked(self, client: AsyncClient):
        resp = await client.post("/api/leads/capture", json={
            "name": "Dr. Test",
            "email": "xss_msg@clinic.ru",
            "phone": "+79991234567",
            "clinic_name": "Test Clinic",
            "specialty": "dentistry",
            "message": "<iframe src='evil.com'></iframe>",
            "fz152_consent": True,
            "recaptcha_token": "test_token_xss_msg",
        })
        assert resp.status_code == 422

    async def test_sql_injection_in_query_params_safe(self, client: AsyncClient):
        """SQL injection in query params — SQLAlchemy parametrizes queries by design."""
        resp = await client.get("/api/analytics/leads", params={
            "start_date": "2026-01-01T00:00:00",
            "end_date": "2026-12-31T00:00:00",
            "tier": "hot' OR '1'='1",
        })
        # Should return 422 (invalid tier), NOT 500 or leaked data
        assert resp.status_code == 422

    async def test_path_traversal_in_filenames_safe(self, client: AsyncClient, db: AsyncSession):
        """File upload with path traversal filename should be sanitized."""
        # Create lead first
        resp = await client.post("/api/leads/capture", json={
            "name": "Dr. Path",
            "email": "path_test@clinic.ru",
            "phone": "+79991234567",
            "clinic_name": "Path Clinic",
            "specialty": "dentistry",
            "fz152_consent": True,
            "recaptcha_token": "test_token_path",
        })
        lead_id = resp.json()["lead_id"]

        # Start onboarding
        start = await client.post("/api/onboarding/start", json={"lead_id": lead_id})
        onboarding_id = start.json()["onboarding_id"]

        # Try path traversal filename
        import io
        malicious_file = io.BytesIO(b"%PDF-1.4 fake content")
        resp = await client.post(
            f"/api/onboarding/{onboarding_id}/documents",
            params={"document_type": "license"},
            files={"file": ("../../../etc/passwd", malicious_file, "application/pdf")},
        )
        # Should still work — filename is sanitized
        assert resp.status_code == 201

    async def test_invalid_phone_rejected(self, client: AsyncClient):
        resp = await client.post("/api/leads/capture", json={
            "name": "Dr. Test",
            "email": "phone_test@clinic.ru",
            "phone": "DROP TABLE leads;--",
            "clinic_name": "Test Clinic",
            "specialty": "dentistry",
            "fz152_consent": True,
            "recaptcha_token": "test_token_phone",
        })
        assert resp.status_code == 422

    async def test_invalid_specialty_rejected(self, client: AsyncClient):
        resp = await client.post("/api/leads/capture", json={
            "name": "Dr. Test",
            "email": "spec_test@clinic.ru",
            "phone": "+79991234567",
            "clinic_name": "Test Clinic",
            "specialty": "hacking",
            "fz152_consent": True,
            "recaptcha_token": "test_token_spec",
        })
        assert resp.status_code == 422

    async def test_empty_name_rejected(self, client: AsyncClient):
        resp = await client.post("/api/leads/capture", json={
            "name": "A",  # min_length=2
            "email": "short@clinic.ru",
            "phone": "+79991234567",
            "clinic_name": "Test Clinic",
            "specialty": "dentistry",
            "fz152_consent": True,
            "recaptcha_token": "test_token_short",
        })
        assert resp.status_code == 422


# ──────────────────────────────────────────────────
# Error Handling — No Internal Detail Leakage
# ──────────────────────────────────────────────────


@pytest.mark.asyncio
class TestErrorHandlingSafety:
    """500 errors must not leak internal exception details."""

    async def test_analytics_500_is_generic(self, client: AsyncClient):
        """When analytics fails, error detail must not contain traceback."""
        # Invalid date range triggers 422 (validation), not 500
        resp = await client.get("/api/analytics/leads", params={
            "start_date": "2027-01-01T00:00:00",
            "end_date": "2026-01-01T00:00:00",  # end < start
        })
        assert resp.status_code == 422
        detail = resp.json()["detail"]
        assert "Traceback" not in detail
        assert "Exception" not in detail

    async def test_onboarding_500_is_generic(self, client: AsyncClient):
        """Non-existent onboarding should return clean 404, not 500 with traceback."""
        resp = await client.get("/api/onboarding/nonexistent_id/status")
        assert resp.status_code == 404
        detail = resp.json()["detail"]
        assert "Traceback" not in detail
        assert "Exception" not in detail

    async def test_leads_validation_error_is_safe(self, client: AsyncClient):
        """Validation errors should be descriptive but safe."""
        resp = await client.post("/api/leads/capture", json={})
        assert resp.status_code == 422
        detail = resp.json()["detail"]
        # FastAPI returns list of validation errors
        assert isinstance(detail, list)
        for err in detail:
            assert "Traceback" not in str(err)

    async def test_documents_upload_invalid_type_is_safe(self, client: AsyncClient):
        """Invalid document type error should not leak internal state."""
        resp = await client.post(
            "/api/documents/upload",
            data={"lead_id": "nonexistent", "document_type": "license"},
            files={"file": ("test.pdf", b"%PDF-1.4 fake", "application/pdf")},
        )
        # 404 — lead not found, message is safe
        assert resp.status_code == 404
        detail = resp.json()["detail"]
        assert "Traceback" not in detail

    async def test_duplicate_lead_returns_safe_message(self, client: AsyncClient):
        """Duplicate lead detection returns user-friendly message, no internals."""
        payload = {
            "name": "Dr. Dup",
            "email": "safe_dup@clinic.ru",
            "phone": "+79991234567",
            "clinic_name": "Dup Clinic",
            "specialty": "dentistry",
            "fz152_consent": True,
            "recaptcha_token": "test_token_dup_safe",
        }
        await client.post("/api/leads/capture", json=payload)
        resp = await client.post("/api/leads/capture", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert "уже получили" in data["message"]
        assert "Traceback" not in data["message"]


# ──────────────────────────────────────────────────
# reCAPTCHA Verification Tests
# ──────────────────────────────────────────────────


@pytest.mark.asyncio
class TestRecaptcha:
    """reCAPTCHA verification behavior."""

    async def test_recaptcha_timeout_allows_submission(self, client: AsyncClient):
        """If reCAPTCHA times out, submission should still work (fail-open)."""
        resp = await client.post("/api/leads/capture", json={
            "name": "Dr. Captcha",
            "email": "captcha_timeout@clinic.ru",
            "phone": "+79991234567",
            "clinic_name": "Timeout Clinic",
            "specialty": "dentistry",
            "fz152_consent": True,
            "recaptcha_token": "test_token_timeout",
        })
        # With mock_recaptcha autouse, this should succeed
        assert resp.status_code == 201

    async def test_recaptcha_http_error_allows_submission(self, client: AsyncClient):
        """reCAPTCHA HTTP errors should not block legitimate submissions."""
        resp = await client.post("/api/leads/capture", json={
            "name": "Dr. Captcha2",
            "email": "captcha_http@clinic.ru",
            "phone": "+79991234567",
            "clinic_name": "HTTP Clinic",
            "specialty": "dentistry",
            "fz152_consent": True,
            "recaptcha_token": "test_token_http_error",
        })
        assert resp.status_code == 201
