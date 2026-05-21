"""Onboarding Service

Orchestrates complete clinic onboarding workflow.

Part of: Phase 11 Sprint 3 - Task 3.4
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from aim.models.document import Document
from aim.models.lead import Lead
from aim.models.onboarding import Onboarding
from aim.models.payment import Payment
from aim.schemas.payment import PaymentRequest, PaymentStatus
from aim.services.documents.processor import DocumentProcessor
from aim.services.onboarding.state_machine import (
    OnboardingEvent,
    OnboardingState,
    OnboardingStateMachine,
)
from aim.services.payment.payment_service import PaymentService

logger = logging.getLogger(__name__)


class OnboardingService:
    """Service for managing clinic onboarding workflow.

    Orchestrates:
    - Document upload and validation
    - Payment processing
    - State transitions
    - Progress tracking
    """

    REQUIRED_DOCUMENTS = {"license", "inn", "ogrn", "contract"}
    DEFAULT_ONBOARDING_FEE = 50000.0  # RUB

    def __init__(
        self,
        document_processor: DocumentProcessor,
        payment_service: PaymentService,
    ):
        """Initialize onboarding service.

        Args:
            document_processor: Document processing service
            payment_service: Payment processing service
        """
        self.document_processor = document_processor
        self.payment_service = payment_service

    async def start_onboarding(
        self, lead_id: str, db: AsyncSession
    ) -> Onboarding:
        """Start onboarding for lead.

        Args:
            lead_id: Lead ID
            db: Database session

        Returns:
            Created onboarding instance

        Raises:
            ValueError: If lead not found or onboarding already exists
        """
        logger.info(f"Starting onboarding for lead {lead_id}")

        # Check lead exists
        result = await db.execute(select(Lead).where(Lead.id == lead_id))
        lead = result.scalar_one_or_none()
        if not lead:
            raise ValueError(f"Lead not found: {lead_id}")

        # Check if onboarding already exists
        result = await db.execute(
            select(Onboarding).where(Onboarding.lead_id == lead_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise ValueError(
                f"Onboarding already exists for lead {lead_id}: {existing.id}"
            )

        # Create onboarding
        onboarding = Onboarding(
            id=Onboarding.generate_id(),
            lead_id=lead_id,
            state=OnboardingState.DOCUMENTS_PENDING.value,
            progress=10,
            documents_uploaded=[],
            documents_validated=False,
            onboarding_fee=self.DEFAULT_ONBOARDING_FEE,
            started_at=datetime.now(timezone.utc),
            metadata={"document_types": []},
        )

        db.add(onboarding)
        await db.commit()
        await db.refresh(onboarding)

        logger.info(f"Onboarding started: {onboarding.id}")

        return onboarding

    async def upload_document(
        self,
        onboarding_id: str,
        document_type: str,
        file_path: str,
        db: AsyncSession,
    ) -> tuple[Onboarding, Document]:
        """Upload and process document.

        Args:
            onboarding_id: Onboarding ID
            document_type: Document type
            file_path: Path to uploaded file
            db: Database session

        Returns:
            Tuple of (updated onboarding, created document)

        Raises:
            ValueError: If onboarding not found or invalid state
        """
        logger.info(
            f"Uploading document for onboarding {onboarding_id}: {document_type}"
        )

        # Get onboarding
        result = await db.execute(
            select(Onboarding).where(Onboarding.id == onboarding_id)
        )
        onboarding = result.scalar_one_or_none()
        if not onboarding:
            raise ValueError(f"Onboarding not found: {onboarding_id}")

        # Check state allows document upload
        state_machine = OnboardingStateMachine(onboarding.state)
        if not state_machine.can_transition(OnboardingEvent.UPLOAD_DOCUMENT):
            raise ValueError(
                f"Cannot upload document in state: {onboarding.state}"
            )

        # Create document record
        document = Document(
            id=Document.generate_id(),
            lead_id=onboarding.lead_id,
            document_type=document_type,
            file_path=file_path,
            file_name=file_path.split("/")[-1],
            file_size=0,  # Will be updated by processor
            mime_type="application/octet-stream",
            status="pending",
            created_by="onboarding_service",
            uploaded_at=datetime.now(timezone.utc),
        )

        db.add(document)
        await db.commit()
        await db.refresh(document)

        # Process document
        try:
            document = await self.document_processor.process_document(
                document, file_path, db
            )
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            # Continue - document marked as failed

        # Update onboarding
        onboarding.add_document(document.id)
        flag_modified(onboarding, "documents_uploaded")

        # Update document types in extra_data
        if not onboarding.extra_data:
            onboarding.extra_data = {}
        doc_types = list(onboarding.extra_data.get("document_types", []))
        if document_type not in doc_types:
            doc_types.append(document_type)
        onboarding.extra_data["document_types"] = doc_types
        flag_modified(onboarding, "extra_data")

        # Update progress
        onboarding.progress = onboarding.calculate_progress()

        await db.commit()
        await db.refresh(onboarding)

        logger.info(
            f"Document uploaded: {document.id}, progress: {onboarding.progress}%"
        )

        return onboarding, document

    async def check_documents_complete(
        self, onboarding_id: str, db: AsyncSession
    ) -> bool:
        """Check if all required documents uploaded.

        Args:
            onboarding_id: Onboarding ID
            db: Database session

        Returns:
            True if all required documents uploaded

        Raises:
            ValueError: If onboarding not found
        """
        result = await db.execute(
            select(Onboarding).where(Onboarding.id == onboarding_id)
        )
        onboarding = result.scalar_one_or_none()
        if not onboarding:
            raise ValueError(f"Onboarding not found: {onboarding_id}")

        return onboarding.is_documents_complete()

    async def validate_documents(
        self, onboarding_id: str, db: AsyncSession
    ) -> Onboarding:
        """Validate all uploaded documents.

        Args:
            onboarding_id: Onboarding ID
            db: Database session

        Returns:
            Updated onboarding

        Raises:
            ValueError: If onboarding not found or documents incomplete
        """
        logger.info(f"Validating documents for onboarding {onboarding_id}")

        # Get onboarding
        result = await db.execute(
            select(Onboarding).where(Onboarding.id == onboarding_id)
        )
        onboarding = result.scalar_one_or_none()
        if not onboarding:
            raise ValueError(f"Onboarding not found: {onboarding_id}")

        # Check all documents uploaded
        if not onboarding.is_documents_complete():
            raise ValueError(
                f"Not all required documents uploaded. "
                f"Required: {self.REQUIRED_DOCUMENTS}, "
                f"Uploaded: {set(onboarding.get_uploaded_document_types())}"
            )

        # Get all documents
        result = await db.execute(
            select(Document).where(
                Document.id.in_(onboarding.documents_uploaded)
            )
        )
        documents = result.scalars().all()

        # Check all documents processed and valid
        all_valid = True
        for doc in documents:
            if doc.status != "completed":
                all_valid = False
                logger.warning(
                    f"Document {doc.id} not processed: {doc.status}"
                )
            elif doc.validation_status != "valid":
                all_valid = False
                logger.warning(
                    f"Document {doc.id} not valid: {doc.validation_status}"
                )

        # Update onboarding state
        state_machine = OnboardingStateMachine(onboarding.state)

        if all_valid:
            # Transition to validated
            if onboarding.state == OnboardingState.DOCUMENTS_PENDING.value:
                state_machine.transition(OnboardingEvent.VALIDATE_DOCUMENTS)
                onboarding.state = OnboardingState.DOCUMENTS_UPLOADED.value

            state_machine = OnboardingStateMachine(onboarding.state)
            state_machine.transition(OnboardingEvent.VALIDATE_DOCUMENTS)
            onboarding.state = OnboardingState.DOCUMENTS_VALIDATED.value
            onboarding.documents_validated = True
            onboarding.progress = 60

            logger.info(f"Documents validated successfully")
        else:
            # Transition to failed
            state_machine.transition(OnboardingEvent.FAIL)
            onboarding.state = OnboardingState.ONBOARDING_FAILED.value
            onboarding.failed_at = datetime.now(timezone.utc)
            onboarding.failure_reason = "Document validation failed"

            logger.error(f"Document validation failed")

        await db.commit()
        await db.refresh(onboarding)

        return onboarding

    async def calculate_onboarding_fee(
        self, onboarding_id: str, db: AsyncSession
    ) -> float:
        """Calculate onboarding fee.

        Args:
            onboarding_id: Onboarding ID
            db: Database session

        Returns:
            Fee amount in RUB

        Raises:
            ValueError: If onboarding not found
        """
        result = await db.execute(
            select(Onboarding).where(Onboarding.id == onboarding_id)
        )
        onboarding = result.scalar_one_or_none()
        if not onboarding:
            raise ValueError(f"Onboarding not found: {onboarding_id}")

        # For now, fixed fee
        # In future: can be dynamic based on clinic size, services, etc.
        return onboarding.onboarding_fee

    async def process_payment(
        self,
        onboarding_id: str,
        payment_data: dict,
        db: AsyncSession,
    ) -> tuple[Onboarding, Payment]:
        """Process onboarding payment.

        Args:
            onboarding_id: Onboarding ID
            payment_data: Payment data (amount, method, card details, etc.)
            db: Database session

        Returns:
            Tuple of (updated onboarding, created payment)

        Raises:
            ValueError: If onboarding not found or invalid state
        """
        logger.info(f"Processing payment for onboarding {onboarding_id}")

        # Get onboarding
        result = await db.execute(
            select(Onboarding).where(Onboarding.id == onboarding_id)
        )
        onboarding = result.scalar_one_or_none()
        if not onboarding:
            raise ValueError(f"Onboarding not found: {onboarding_id}")

        # Auto-validate documents if still in DOCUMENTS_PENDING
        if onboarding.state == OnboardingState.DOCUMENTS_PENDING.value:
            if not onboarding.is_documents_complete():
                raise ValueError("Not all required documents uploaded")
            onboarding = await self.validate_documents(onboarding_id, db)
            if onboarding.state == OnboardingState.ONBOARDING_FAILED.value:
                raise ValueError("Document validation failed")

        # Check state allows payment
        state_machine = OnboardingStateMachine(onboarding.state)
        if not state_machine.can_transition(OnboardingEvent.REQUEST_PAYMENT):
            raise ValueError(
                f"Cannot process payment in state: {onboarding.state}"
            )

        # Transition to payment pending
        state_machine.transition(OnboardingEvent.REQUEST_PAYMENT)
        onboarding.state = OnboardingState.PAYMENT_PENDING.value
        onboarding.progress = 70
        await db.commit()

        # Process payment via payment service
        try:
            # Transition to payment processing
            state_machine = OnboardingStateMachine(onboarding.state)
            state_machine.transition(OnboardingEvent.PROCESS_PAYMENT)
            onboarding.state = OnboardingState.PAYMENT_PROCESSING.value
            onboarding.progress = 80
            await db.commit()

            # Create payment
            payment_request = PaymentRequest(
                amount=onboarding.onboarding_fee,
                currency=payment_data.get("currency", "RUB"),
                payment_method=payment_data["payment_method"].lower(),
                customer_name=payment_data["customer_name"],
                customer_email=payment_data["customer_email"],
                customer_phone=payment_data.get("customer_phone"),
                card_number=payment_data.get("card_number"),
                card_expiry=payment_data.get("card_expiry"),
                card_cvv=payment_data.get("card_cvv"),
                lead_id=onboarding.lead_id,
                metadata=payment_data.get("metadata"),
            )
            payment_response = await self.payment_service.create_payment(
                request=payment_request,
            )
            payment = await db.get(Payment, payment_response.payment_id)

            # Check payment status
            if payment.status == PaymentStatus.COMPLETED.value:
                # Transition to payment completed
                state_machine = OnboardingStateMachine(onboarding.state)
                state_machine.transition(OnboardingEvent.COMPLETE_PAYMENT)
                onboarding.state = OnboardingState.PAYMENT_COMPLETED.value
                onboarding.payment_id = payment.id
                onboarding.progress = 90

                logger.info(f"Payment completed: {payment.id}")
            else:
                # Payment failed
                state_machine = OnboardingStateMachine(onboarding.state)
                state_machine.transition(OnboardingEvent.FAIL)
                onboarding.state = OnboardingState.ONBOARDING_FAILED.value
                onboarding.failed_at = datetime.now(timezone.utc)
                onboarding.failure_reason = f"Payment failed: {payment.status}"

                logger.error(f"Payment failed: {payment.status}")

            await db.commit()
            await db.refresh(onboarding)

            return onboarding, payment

        except Exception as e:
            logger.error(f"Payment processing failed: {e}")

            # Transition to failed
            state_machine = OnboardingStateMachine(onboarding.state)
            state_machine.transition(OnboardingEvent.FAIL)
            onboarding.state = OnboardingState.ONBOARDING_FAILED.value
            onboarding.failed_at = datetime.now(timezone.utc)
            onboarding.failure_reason = f"Payment error: {str(e)}"

            await db.commit()
            await db.refresh(onboarding)

            raise

    async def complete_onboarding(
        self, onboarding_id: str, db: AsyncSession
    ) -> Onboarding:
        """Complete onboarding workflow.

        Args:
            onboarding_id: Onboarding ID
            db: Database session

        Returns:
            Updated onboarding

        Raises:
            ValueError: If onboarding not found or invalid state
        """
        logger.info(f"Completing onboarding {onboarding_id}")

        # Get onboarding
        result = await db.execute(
            select(Onboarding).where(Onboarding.id == onboarding_id)
        )
        onboarding = result.scalar_one_or_none()
        if not onboarding:
            raise ValueError(f"Onboarding not found: {onboarding_id}")

        # Check state allows completion
        state_machine = OnboardingStateMachine(onboarding.state)
        if not state_machine.can_transition(OnboardingEvent.COMPLETE_ONBOARDING):
            raise ValueError(
                f"Cannot complete onboarding in state: {onboarding.state}"
            )

        # Transition to complete
        state_machine.transition(OnboardingEvent.COMPLETE_ONBOARDING)
        onboarding.state = OnboardingState.ONBOARDING_COMPLETE.value
        onboarding.progress = 100
        onboarding.completed_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(onboarding)

        logger.info(f"Onboarding completed: {onboarding.id}")

        return onboarding

    async def get_onboarding_status(
        self, onboarding_id: str, db: AsyncSession
    ) -> dict:
        """Get onboarding status and progress.

        Args:
            onboarding_id: Onboarding ID
            db: Database session

        Returns:
            Status dictionary with state, progress, next_steps

        Raises:
            ValueError: If onboarding not found
        """
        result = await db.execute(
            select(Onboarding).where(Onboarding.id == onboarding_id)
        )
        onboarding = result.scalar_one_or_none()
        if not onboarding:
            raise ValueError(f"Onboarding not found: {onboarding_id}")

        # Get next steps
        state_machine = OnboardingStateMachine(onboarding.state)
        next_steps = state_machine.get_next_steps()

        return {
            "onboarding_id": onboarding.id,
            "lead_id": onboarding.lead_id,
            "state": onboarding.state,
            "progress": onboarding.progress,
            "documents_uploaded": onboarding.documents_uploaded,
            "documents_validated": onboarding.documents_validated,
            "payment_id": onboarding.payment_id,
            "onboarding_fee": onboarding.onboarding_fee,
            "started_at": onboarding.started_at,
            "completed_at": onboarding.completed_at,
            "failed_at": onboarding.failed_at,
            "failure_reason": onboarding.failure_reason,
            "next_steps": [step["description"] for step in next_steps],
        }

    async def retry_failed_step(
        self, onboarding_id: str, step: str, db: AsyncSession
    ) -> Onboarding:
        """Retry failed onboarding step.

        Args:
            onboarding_id: Onboarding ID
            step: Step to retry (documents_validation, payment_processing, etc.)
            db: Database session

        Returns:
            Updated onboarding

        Raises:
            ValueError: If onboarding not found or not in failed state
        """
        logger.info(f"Retrying step {step} for onboarding {onboarding_id}")

        # Get onboarding
        result = await db.execute(
            select(Onboarding).where(Onboarding.id == onboarding_id)
        )
        onboarding = result.scalar_one_or_none()
        if not onboarding:
            raise ValueError(f"Onboarding not found: {onboarding_id}")

        # Check in failed state
        if onboarding.state != OnboardingState.ONBOARDING_FAILED.value:
            raise ValueError(
                f"Cannot retry - onboarding not in failed state: {onboarding.state}"
            )

        # Reset to appropriate state based on step
        state_machine = OnboardingStateMachine(onboarding.state)
        state_machine.transition(OnboardingEvent.RETRY)

        if step == "documents_validation":
            onboarding.state = OnboardingState.DOCUMENTS_PENDING.value
            onboarding.progress = 20
        elif step == "payment_processing":
            onboarding.state = OnboardingState.DOCUMENTS_VALIDATED.value
            onboarding.progress = 60
        elif step == "onboarding_completion":
            onboarding.state = OnboardingState.PAYMENT_COMPLETED.value
            onboarding.progress = 90
        else:
            raise ValueError(f"Unknown step: {step}")

        # Clear failure info
        onboarding.failed_at = None
        onboarding.failure_reason = None

        await db.commit()
        await db.refresh(onboarding)

        logger.info(f"Retry initiated: new state {onboarding.state}")

        return onboarding

    async def get_onboarding_by_lead(
        self, lead_id: str, db: AsyncSession
    ) -> Optional[Onboarding]:
        """Get onboarding for lead.

        Args:
            lead_id: Lead ID
            db: Database session

        Returns:
            Onboarding instance or None
        """
        result = await db.execute(
            select(Onboarding).where(Onboarding.lead_id == lead_id)
        )
        return result.scalar_one_or_none()
