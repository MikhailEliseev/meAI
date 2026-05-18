"""Lead Capture Service with ФЗ-152 Compliance

Handles lead form submissions with:
- Field-level encryption (AES-256-GCM)
- ФЗ-152 consent validation
- Rate limiting (10 req/min per IP)
- Audit logging
- reCAPTCHA verification

Russian Market Adaptation:
- ФЗ-152 consent required (not HIPAA)
- Russian phone format validation
- Cyrillic name support
- IP-based geolocation for compliance

Part of: Phase 11 - Client Acquisition (Task 2.1)
"""

import asyncio
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aim.models.lead import Lead as LeadModel
from aim.middleware.cache import cache
from aim.metrics import leads_captured_total, leads_scored_total, rate_limit_hits_total
from aim.schemas.lead import (
    LeadCaptureRequest,
    LeadCaptureResponse,
    LeadRecord,
    LeadSource,
)
from aim.utils.encryption import get_encryptor


class RateLimitExceeded(Exception):
    """Rate limit exceeded for IP address"""

    pass


class RecaptchaVerificationFailed(Exception):
    """reCAPTCHA verification failed"""

    pass


class LeadCaptureService:
    """Lead capture service with ФЗ-152 compliance

    Features:
    - AES-256 field encryption
    - ФЗ-152 consent tracking
    - Rate limiting (10 req/min per IP)
    - reCAPTCHA v3 verification
    - Audit logging
    - Duplicate detection
    """

    # Class-level rate limit cache (shared across all instances)
    _rate_limit_cache: dict[str, list[float]] = {}

    def __init__(
        self,
        db_session: AsyncSession,
        recaptcha_secret: str,
        rate_limit_per_minute: int = 10,
        recaptcha_min_score: float = 0.5,
    ):
        """Initialize lead capture service

        Args:
            db_session: Database session
            recaptcha_secret: reCAPTCHA v3 secret key
            rate_limit_per_minute: Max requests per IP per minute
            recaptcha_min_score: Minimum reCAPTCHA score (0.0-1.0)
        """
        self.db = db_session
        self.recaptcha_secret = recaptcha_secret
        self.rate_limit = rate_limit_per_minute
        self.recaptcha_min_score = recaptcha_min_score
        self.encryptor = get_encryptor()

    async def capture_lead(
        self,
        request: LeadCaptureRequest,
        client_ip: str,
        user_agent: Optional[str] = None,
    ) -> LeadCaptureResponse:
        """Capture lead from form submission

        Args:
            request: Lead capture form data
            client_ip: Client IP address
            user_agent: Client user agent

        Returns:
            LeadCaptureResponse with lead ID

        Raises:
            RateLimitExceeded: If rate limit exceeded
            RecaptchaVerificationFailed: If reCAPTCHA fails
            HTTPException: If validation or storage fails
        """
        # 1. Rate limiting
        await self._check_rate_limit(client_ip)

        # 2. reCAPTCHA verification
        await self._verify_recaptcha(request.recaptcha_token, client_ip)

        # 3. Check for duplicates (email)
        existing_lead = await self._find_duplicate(request.email)
        if existing_lead:
            # Return existing lead ID (don't create duplicate)
            return LeadCaptureResponse(
                success=True,
                lead_id=existing_lead.id,
                message="Мы уже получили вашу заявку. Свяжемся с вами в ближайшее время.",
                estimated_response_time="15 минут",
            )

        # 4. Generate lead ID
        lead_id = self._generate_lead_id()

        # 5. Encrypt sensitive fields
        encrypted_data = self._encrypt_lead_data(request)

        # 6. Create lead record
        lead_record = LeadModel(
            id=lead_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            # Encrypted fields
            name_encrypted=encrypted_data["name_encrypted"],
            phone_encrypted=encrypted_data["phone_encrypted"],
            email_encrypted=encrypted_data["email_encrypted"],
            email_hash=LeadModel.hash_email(request.email),
            clinic_name_encrypted=encrypted_data["clinic_name_encrypted"],
            message_encrypted=encrypted_data.get("message_encrypted"),
            # Specialty (not encrypted - used for filtering)
            specialty=request.specialty.value,
            # ФЗ-152 compliance
            fz152_consent=request.fz152_consent,
            fz152_consent_timestamp=datetime.now(timezone.utc),
            fz152_consent_ip=client_ip,
            # Metadata
            source=request.source.value,
            utm_source=request.utm_source,
            utm_medium=request.utm_medium,
            utm_campaign=request.utm_campaign,
            utm_content=request.utm_content,
            utm_term=request.utm_term,
            user_agent=user_agent,
            # Processing status
            processed=False,
        )

        # 7. Save to database
        self.db.add(lead_record)
        await self.db.commit()
        await self.db.refresh(lead_record)

        # Emit business metrics
        leads_captured_total.labels(
            source=request.source.value, specialty=request.specialty.value
        ).inc()

        # Invalidate analytics cache (new data available)
        cache.invalidate("analytics:")

        # 8. Audit log
        await self._audit_log(
            lead_id=lead_id,
            action="lead_captured",
            ip=client_ip,
            details={
                "source": request.source.value,
                "specialty": request.specialty.value,
                "fz152_consent": request.fz152_consent,
            },
        )

        # 9. Process lead synchronously to get score/tier for immediate response
        scoring_result = await self._process_lead_async(lead_id)

        return LeadCaptureResponse(
            success=True,
            lead_id=lead_id,
            message="Спасибо за обращение! Мы свяжемся с вами в течение 15 минут.",
            estimated_response_time="15 минут",
            tier=scoring_result.get("tier"),
            score=scoring_result.get("score"),
        )

    async def _check_rate_limit(self, ip: str) -> None:
        """Check rate limit for IP address

        Args:
            ip: Client IP address

        Raises:
            RateLimitExceeded: If rate limit exceeded
        """
        cache = self.__class__._rate_limit_cache
        now = datetime.now(timezone.utc).timestamp()
        minute_ago = now - 60

        # Get recent requests for this IP
        if ip not in cache:
            cache[ip] = []

        # Remove old requests (older than 1 minute)
        cache[ip] = [ts for ts in cache[ip] if ts > minute_ago]

        # Check limit
        if len(cache[ip]) >= self.rate_limit:
            rate_limit_hits_total.labels(endpoint="lead_capture").inc()
            raise RateLimitExceeded(
                f"Rate limit exceeded: {self.rate_limit} requests per minute"
            )

        # Add current request
        cache[ip].append(now)

    async def _verify_recaptcha(self, token: str, ip: str) -> None:
        """Verify reCAPTCHA v3 token

        Args:
            token: reCAPTCHA token from client
            ip: Client IP address

        Raises:
            RecaptchaVerificationFailed: If verification fails
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://www.google.com/recaptcha/api/siteverify",
                    data={
                        "secret": self.recaptcha_secret,
                        "response": token,
                        "remoteip": ip,
                    },
                    timeout=5.0,
                )
                result = response.json()

                if not result.get("success"):
                    raise RecaptchaVerificationFailed(
                        f"reCAPTCHA verification failed: {result.get('error-codes')}"
                    )

                score = result.get("score", 0.0)
                if score < self.recaptcha_min_score:
                    raise RecaptchaVerificationFailed(
                        f"reCAPTCHA score too low: {score} < {self.recaptcha_min_score}"
                    )

            except httpx.TimeoutException:
                # Allow submission if reCAPTCHA service is down
                # (log warning in production)
                pass
            except httpx.HTTPError as e:
                # Allow submission if reCAPTCHA service is down
                # (log warning in production)
                pass

    async def _find_duplicate(self, email: str) -> Optional[LeadModel]:
        """Find duplicate lead by email

        Args:
            email: Email address to check

        Returns:
            Existing lead or None
        """
        # Hash email for comparison (encrypted emails can't be queried directly)
        email_hash = LeadModel.hash_email(email)

        stmt = select(LeadModel).where(LeadModel.email_hash == email_hash)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    def _generate_lead_id(self) -> str:
        """Generate unique lead ID

        Returns:
            Lead ID in format: lead_YYYYMMDDHHMMSS_UUID
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"lead_{timestamp}_{unique_id}"

    def _encrypt_lead_data(self, request: LeadCaptureRequest) -> dict:
        """Encrypt sensitive lead fields

        Args:
            request: Lead capture request

        Returns:
            Dictionary with encrypted fields
        """
        encrypted = self.encryptor.encrypt_dict(
            {
                "name": request.name,
                "phone": request.phone,
                "email": request.email,
                "clinic_name": request.clinic_name,
                "message": request.message,
            },
            ["name", "phone", "email", "clinic_name", "message"],
        )

        return encrypted

    async def _audit_log(
        self, lead_id: str, action: str, ip: str, details: dict
    ) -> None:
        """Log audit event for ФЗ-152 compliance.

        Writes immutable audit record to database for regulatory defense.
        Also logs via structlog for operational visibility.
        """
        import logging
        logger = logging.getLogger("aim.fz152")

        try:
            from aim.models.fz152_audit import FZ152AuditLog

            audit_entry = FZ152AuditLog(
                lead_id=lead_id,
                action=action,
                ip_address=ip,
                details=details,
                agent="lead_capture",
            )
            self.db.add(audit_entry)
            await self.db.commit()

            logger.info(
                "fz152_audit",
                extra={
                    "lead_id": lead_id,
                    "action": action,
                    "ip": ip,
                    "details": details,
                },
            )
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}", exc_info=True)

    async def _process_lead_async(self, lead_id: str) -> None:
        """Process lead asynchronously (scoring, Linear, email)

        Args:
            lead_id: Lead ID to process

        Note:
            This runs in background. Errors are logged but don't fail capture.
        """
        try:
            # 1. Load lead from database
            stmt = select(LeadModel).where(LeadModel.id == lead_id)
            result = await self.db.execute(stmt)
            lead = result.scalar_one_or_none()

            if not lead:
                print(f"[ERROR] Lead {lead_id} not found for processing")
                return

            # 2. Score lead (Task 2.2)
            from aim.ai.lead_scoring.scoring_service import LeadScoringService

            scoring_service = LeadScoringService(model_path=None)  # Rule-based for MVP
            score_result = await scoring_service.score_lead(
                lead=lead,
                metadata={
                    "user_agent": lead.user_agent,
                    "utm_campaign": lead.utm_campaign,
                    "session_duration": 0,  # TODO: Track from frontend
                },
            )

            # 3. Update lead with score
            lead.score = score_result.score
            lead.tier = score_result.tier.lower()
            lead.processed = True
            await self.db.commit()

            # Emit scoring metric
            leads_scored_total.labels(tier=score_result.tier.lower()).inc()

            print(
                f"[INFO] Lead {lead_id} scored: {score_result.score} ({score_result.tier})"
            )

            # 4. Create email workflow and schedule emails
            from aim.services.email.workflow_engine import WorkflowEngine

            workflow_engine = WorkflowEngine(self.db)
            await workflow_engine.trigger_workflow(
                lead_id=lead.id,
                tier=score_result.tier.lower(),
                start_immediately=True,
            )

            # 5. Create Linear task (Task 2.3 - TODO)

            # Return score and tier for immediate response
            return {
                "score": score_result.score,
                "tier": score_result.tier.lower(),
            }

        except Exception as e:
            # Log error but don't fail (capture already succeeded)
            print(f"[ERROR] Lead processing failed for {lead_id}: {e}")
            return {"score": None, "tier": None}
