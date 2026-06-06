"""
Onboarding Workflow Automation

State machine for automated client onboarding with ФЗ-152 compliance.
"""

from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime, timedelta, timezone
import structlog

from pydantic import BaseModel, Field

logger = structlog.get_logger()


class OnboardingState(str, Enum):
    """Onboarding workflow states"""
    LEAD_CAPTURED = "lead_captured"
    DOCUMENTS_REQUESTED = "documents_requested"
    DOCUMENTS_UPLOADED = "documents_uploaded"
    DOCUMENTS_PROCESSED = "documents_processed"
    BAA_SENT = "baa_sent"
    BAA_SIGNED = "baa_signed"
    PAYMENT_PENDING = "payment_pending"
    PAYMENT_COMPLETED = "payment_completed"
    PROJECT_CREATED = "project_created"
    WELCOME_SENT = "welcome_sent"
    KICKOFF_SCHEDULED = "kickoff_scheduled"
    ONBOARDING_COMPLETE = "onboarding_complete"
    FAILED = "failed"


class OnboardingEvent(str, Enum):
    """Onboarding workflow events"""
    LEAD_SCORED = "lead_scored"
    DOCUMENTS_UPLOADED = "documents_uploaded"
    DOCUMENTS_VALIDATED = "documents_validated"
    DOCUMENTS_REJECTED = "documents_rejected"
    BAA_SENT = "baa_sent"
    BAA_SIGNED = "baa_signed"
    PAYMENT_INITIATED = "payment_initiated"
    PAYMENT_COMPLETED = "payment_completed"
    PAYMENT_FAILED = "payment_failed"
    PROJECT_CREATED = "project_created"
    WELCOME_SENT = "welcome_sent"
    KICKOFF_SCHEDULED = "kickoff_scheduled"


class OnboardingSession(BaseModel):
    """Onboarding session data"""
    session_id: str
    client_id: str
    state: OnboardingState
    lead_score: Optional[int] = None
    documents: List[Dict[str, Any]] = Field(default_factory=list)
    baa_envelope_id: Optional[str] = None
    payment_intent_id: Optional[str] = None
    linear_project_id: Optional[str] = None
    kickoff_meeting_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


# State transition rules
TRANSITIONS: Dict[OnboardingState, List[OnboardingEvent]] = {
    OnboardingState.LEAD_CAPTURED: [
        OnboardingEvent.LEAD_SCORED,
    ],
    OnboardingState.DOCUMENTS_REQUESTED: [
        OnboardingEvent.DOCUMENTS_UPLOADED,
    ],
    OnboardingState.DOCUMENTS_UPLOADED: [
        OnboardingEvent.DOCUMENTS_VALIDATED,
        OnboardingEvent.DOCUMENTS_REJECTED,
    ],
    OnboardingState.DOCUMENTS_PROCESSED: [
        OnboardingEvent.DOCUMENTS_VALIDATED,
    ],
    OnboardingState.BAA_SENT: [
        OnboardingEvent.BAA_SIGNED,
    ],
    OnboardingState.BAA_SIGNED: [
        OnboardingEvent.BAA_SIGNED,
    ],
    OnboardingState.PAYMENT_PENDING: [
        OnboardingEvent.PAYMENT_COMPLETED,
        OnboardingEvent.PAYMENT_FAILED,
    ],
    OnboardingState.PAYMENT_COMPLETED: [
        OnboardingEvent.PAYMENT_COMPLETED,
    ],
    OnboardingState.PROJECT_CREATED: [
        OnboardingEvent.PROJECT_CREATED,
    ],
    OnboardingState.WELCOME_SENT: [
        OnboardingEvent.WELCOME_SENT,
    ],
    OnboardingState.KICKOFF_SCHEDULED: [
        OnboardingEvent.KICKOFF_SCHEDULED,
    ],
    OnboardingState.ONBOARDING_COMPLETE: [],
    OnboardingState.FAILED: [],
}


class OnboardingWorkflow:
    """
    Automated onboarding workflow with state machine
    
    Handles:
    - Document collection and validation
    - BAA signature via Контур.Диадок
    - Payment processing via ЮKassa
    - Linear project creation
    - Welcome email sequence
    - Kickoff call scheduling
    """

    def __init__(
        self,
        document_processor,
        kontour_client,
        payment_service,
        linear_client,
        email_service,
        calendar_service,
    ):
        """
        Initialize workflow

        Args:
            document_processor: Document processing service
            kontour_client: Контур.Диадок API client
            payment_service: ЮKassa payment service
            linear_client: Linear API client
            email_service: SendGrid email service
            calendar_service: Calendar scheduling service
        """
        self.document_processor = document_processor
        self.kontour = kontour_client
        self.payment = payment_service
        self.linear = linear_client
        self.email = email_service
        self.calendar = calendar_service
        self.logger = logger.bind(service="onboarding_workflow")

    async def start_onboarding(
        self,
        client_id: str,
        lead_score: int,
    ) -> OnboardingSession:
        """
        Start onboarding workflow
        
        Args:
            client_id: Client ID
            lead_score: Lead qualification score (0-100)
        
        Returns:
            Onboarding session
        """
        session = OnboardingSession(
            session_id=f"onb_{client_id}_{int(datetime.now(timezone.utc).timestamp())}",
            client_id=client_id,
            state=OnboardingState.LEAD_CAPTURED,
            lead_score=lead_score,
        )

        self.logger.info(
            "onboarding_started",
            session_id=session.session_id,
            client_id=client_id,
            lead_score=lead_score,
        )

        # Auto-trigger for hot leads (score >= 80)
        if lead_score >= 80:
            await self.handle_event(session, OnboardingEvent.LEAD_SCORED)

        return session

    async def handle_event(
        self,
        session: OnboardingSession,
        event: OnboardingEvent,
    ) -> OnboardingSession:
        """
        Handle workflow event
        
        Args:
            session: Current session
            event: Event to handle
        
        Returns:
            Updated session
        
        Raises:
            ValueError: If transition is not allowed
        """
        # Validate transition
        allowed_events = TRANSITIONS.get(session.state, [])
        if event not in allowed_events:
            raise ValueError(
                f"Event {event} not allowed in state {session.state}"
            )

        self.logger.info(
            "handling_event",
            session_id=session.session_id,
            state=session.state,
            workflow_event=event,
        )

        # Execute state transition
        if event == OnboardingEvent.LEAD_SCORED:
            session = await self._request_documents(session)
        elif event == OnboardingEvent.DOCUMENTS_UPLOADED:
            session = await self._process_documents(session)
        elif event == OnboardingEvent.DOCUMENTS_VALIDATED:
            session = await self._send_baa(session)
        elif event == OnboardingEvent.DOCUMENTS_REJECTED:
            session = await self._reject_documents(session)
        elif event == OnboardingEvent.BAA_SIGNED:
            session = await self._initiate_payment(session)
        elif event == OnboardingEvent.PAYMENT_COMPLETED:
            session = await self._create_project(session)
        elif event == OnboardingEvent.PAYMENT_FAILED:
            session = await self._handle_payment_failure(session)
        elif event == OnboardingEvent.PROJECT_CREATED:
            session = await self._send_welcome_email(session)
        elif event == OnboardingEvent.WELCOME_SENT:
            session = await self._schedule_kickoff(session)
        elif event == OnboardingEvent.KICKOFF_SCHEDULED:
            session.state = OnboardingState.ONBOARDING_COMPLETE
            session.updated_at = datetime.now(timezone.utc)
            return session  # Don't update timestamp twice

        session.updated_at = datetime.now(timezone.utc)
        return session

    async def _request_documents(
        self,
        session: OnboardingSession,
    ) -> OnboardingSession:
        """Request documents from client"""
        # Send email with secure upload link
        await self.email.send_template(
            to=session.metadata.get("email"),
            template="document_request",
            data={
                "client_name": session.metadata.get("name"),
                "upload_link": f"https://iamaim.ru/onboarding/{session.session_id}/upload",
                "required_documents": [
                    "Practice information",
                    "Analytics access",
                    "Advertising accounts",
                ],
            },
        )

        session.state = OnboardingState.DOCUMENTS_REQUESTED
        self.logger.info(
            "documents_requested",
            session_id=session.session_id,
        )
        return session

    async def _process_documents(
        self,
        session: OnboardingSession,
    ) -> OnboardingSession:
        """Process uploaded documents"""
        # Extract and validate data
        results = []
        for doc in session.documents:
            result = await self.document_processor.process_document(
                document_id=doc["id"],
                file_path=doc["path"],
            )
            results.append(result)

        # Check if validation passed
        all_approved = all(
            r["validation"]["status"] == "approved"
            for r in results
        )

        if all_approved:
            session.state = OnboardingState.DOCUMENTS_PROCESSED
            session.metadata["extraction_results"] = results
            self.logger.info(
                "documents_validated",
                session_id=session.session_id,
            )
            # Auto-trigger BAA
            return await self.handle_event(session, OnboardingEvent.DOCUMENTS_VALIDATED)
        else:
            # Create review queue items
            for result in results:
                if result["validation"]["requires_review"]:
                    await self.document_processor.create_review_item(
                        document_id=result["document_id"],
                        extraction_result=result["extraction"],
                        validation_result=result["validation"],
                    )
            
            session.state = OnboardingState.DOCUMENTS_UPLOADED
            self.logger.warning(
                "documents_need_review",
                session_id=session.session_id,
            )

        return session

    async def _reject_documents(
        self,
        session: OnboardingSession,
    ) -> OnboardingSession:
        """Handle document rejection"""
        await self.email.send_template(
            to=session.metadata.get("email"),
            template="document_rejection",
            data={
                "client_name": session.metadata.get("name"),
                "issues": session.metadata.get("validation_issues", []),
                "reupload_link": f"https://iamaim.ru/onboarding/{session.session_id}/upload",
            },
        )

        session.state = OnboardingState.DOCUMENTS_REQUESTED
        return session

    async def _send_baa(
        self,
        session: OnboardingSession,
    ) -> OnboardingSession:
        """Send BAA for signature via Контур.Диадок"""
        from src.aim.services.contracts.kontour_client import (
            SignatureType,
            get_signature_type_for_amount,
        )

        doc_path = session.metadata.get("baa_document_path", "")
        recipient_inn = session.metadata.get("inn", "")
        amount = session.metadata.get("package_price", 5000)

        document_id = await self.kontour.send_for_signature(
            document_path=doc_path,
            recipient_email=session.metadata.get("email", ""),
            recipient_name=session.metadata.get("name", ""),
            recipient_inn=recipient_inn,
            signature_type=get_signature_type_for_amount(amount),
            message=f"Договор для {session.metadata.get('practice_name', '')}",
        )

        session.baa_envelope_id = document_id
        session.state = OnboardingState.BAA_SENT

        self.logger.info(
            "baa_sent",
            session_id=session.session_id,
            document_id=document_id,
        )
        return session

    async def _initiate_payment(
        self,
        session: OnboardingSession,
    ) -> OnboardingSession:
        """Initiate payment via ЮKassa"""
        payment_intent = await self.payment.create_payment_intent(
            amount=session.metadata.get("package_price", 5000),
            currency="RUB",
            customer_email=session.metadata.get("email"),
            description=f"AIM Agency - {session.metadata.get('package_name')}",
        )

        session.payment_intent_id = payment_intent["id"]
        session.state = OnboardingState.PAYMENT_PENDING

        # Send payment link
        await self.email.send_template(
            to=session.metadata.get("email"),
            template="payment_request",
            data={
                "client_name": session.metadata.get("name"),
                "amount": session.metadata.get("package_price"),
                "payment_link": payment_intent["payment_url"],
            },
        )

        self.logger.info(
            "payment_initiated",
            session_id=session.session_id,
            payment_intent_id=payment_intent["id"],
        )
        return session

    async def _handle_payment_failure(
        self,
        session: OnboardingSession,
    ) -> OnboardingSession:
        """Handle payment failure"""
        await self.email.send_template(
            to=session.metadata.get("email"),
            template="payment_failed",
            data={
                "client_name": session.metadata.get("name"),
                "retry_link": f"https://iamaim.ru/onboarding/{session.session_id}/payment",
            },
        )

        session.state = OnboardingState.PAYMENT_PENDING
        return session

    async def _create_project(
        self,
        session: OnboardingSession,
    ) -> OnboardingSession:
        """Create Linear project from Phase 7.5 template"""
        project = await self.linear.create_project_from_template(
            template_id="phase_7_5_template",
            project_name=f"{session.metadata.get('practice_name')} - Launch",
            client_id=session.client_id,
            metadata=session.metadata.get("extraction_results"),
        )

        session.linear_project_id = project["id"]
        session.state = OnboardingState.PROJECT_CREATED

        self.logger.info(
            "project_created",
            session_id=session.session_id,
            project_id=project["id"],
        )
        
        # Auto-trigger welcome email
        return await self.handle_event(session, OnboardingEvent.PROJECT_CREATED)

    async def _send_welcome_email(
        self,
        session: OnboardingSession,
    ) -> OnboardingSession:
        """Send welcome email sequence"""
        await self.email.send_template(
            to=session.metadata.get("email"),
            template="welcome_sequence",
            data={
                "client_name": session.metadata.get("name"),
                "project_link": f"https://linear.app/aim/project/{session.linear_project_id}",
                "team_intro": "Your dedicated team: SEO Specialist, Content Writer, Ads Manager",
                "next_steps": [
                    "Review project timeline",
                    "Schedule kickoff call",
                    "Complete onboarding checklist",
                ],
            },
        )

        session.state = OnboardingState.WELCOME_SENT
        
        self.logger.info(
            "welcome_sent",
            session_id=session.session_id,
        )
        
        # Auto-trigger kickoff scheduling
        return await self.handle_event(session, OnboardingEvent.WELCOME_SENT)

    async def _schedule_kickoff(
        self,
        session: OnboardingSession,
    ) -> OnboardingSession:
        """Schedule kickoff call"""
        # Find available slot (next 7 days, business hours)
        available_slots = await self.calendar.find_available_slots(
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=7),
            duration_minutes=60,
        )

        if available_slots:
            # Book first available slot
            meeting = await self.calendar.create_meeting(
                title=f"Kickoff Call - {session.metadata.get('practice_name')}",
                attendees=[
                    session.metadata.get("email"),
                    "team@iamaim.ru",
                ],
                start_time=available_slots[0],
                duration_minutes=60,
                description="Project kickoff and strategy alignment",
            )

            session.kickoff_meeting_id = meeting["id"]
            session.state = OnboardingState.KICKOFF_SCHEDULED

            # Send calendar invite
            await self.email.send_calendar_invite(
                to=session.metadata.get("email"),
                meeting=meeting,
            )

            self.logger.info(
                "kickoff_scheduled",
                session_id=session.session_id,
                meeting_id=meeting["id"],
                meeting_time=available_slots[0],
            )
            
            # Complete onboarding
            return await self.handle_event(session, OnboardingEvent.KICKOFF_SCHEDULED)
        else:
            self.logger.warning(
                "no_available_slots",
                session_id=session.session_id,
            )

        return session
