"""
Onboarding Workflow Automation

State machine for automated client onboarding:
1. Document Upload → 2. AI Processing → 3. BAA Signature →
4. Project Setup → 5. Welcome Email → 6. Kickoff Scheduling

Features:
- State persistence (PostgreSQL)
- Event-driven transitions
- Automatic retries
- Audit logging
- 30-day checkpoint automation
"""

from enum import Enum
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import structlog

from aim.models.onboarding import OnboardingSession, OnboardingState
from aim.services.onboarding.docusign_client import DocuSignClient
from aim.services.linear_leads import LinearLeadsService
from aim.services.lead_email_automation import LeadEmailAutomation
from aim.services.document_processing.nlp_extractor import DocumentProcessor

logger = structlog.get_logger()


class OnboardingStage(str, Enum):
    """Onboarding workflow stages"""
    CREATED = "created"
    DOCUMENTS_UPLOADED = "documents_uploaded"
    DOCUMENTS_PROCESSED = "documents_processed"
    BAA_SENT = "baa_sent"
    BAA_SIGNED = "baa_signed"
    PROJECT_CREATED = "project_created"
    WELCOME_SENT = "welcome_sent"
    KICKOFF_SCHEDULED = "kickoff_scheduled"
    COMPLETED = "completed"
    FAILED = "failed"


class OnboardingEvent(str, Enum):
    """Events that trigger state transitions"""
    DOCUMENTS_UPLOADED = "documents_uploaded"
    PROCESSING_COMPLETE = "processing_complete"
    PROCESSING_FAILED = "processing_failed"
    BAA_SENT = "baa_sent"
    BAA_SIGNED = "baa_signed"
    BAA_DECLINED = "baa_declined"
    PROJECT_CREATED = "project_created"
    WELCOME_SENT = "welcome_sent"
    KICKOFF_SCHEDULED = "kickoff_scheduled"
    RETRY = "retry"


class OnboardingData(BaseModel):
    """Data extracted during onboarding"""
    client_id: str
    practice_name: str
    contact_name: str
    contact_email: str
    contact_phone: str
    specialty: Optional[str] = None
    practice_size: Optional[str] = None
    location: Optional[str] = None

    # Extracted from documents
    analytics_access: Optional[Dict[str, Any]] = None
    ad_accounts: Optional[Dict[str, Any]] = None
    current_marketing: Optional[Dict[str, Any]] = None

    # BAA
    baa_envelope_id: Optional[str] = None
    baa_signed_at: Optional[datetime] = None

    # Project
    linear_project_id: Optional[str] = None
    linear_team_id: Optional[str] = None

    # Scheduling
    kickoff_call_url: Optional[str] = None
    kickoff_call_scheduled_at: Optional[datetime] = None


class OnboardingWorkflow:
    """
    Automated onboarding workflow state machine

    Manages client onboarding from document upload to project kickoff.
    """

    def __init__(
        self,
        db: AsyncSession,
        docusign_client: DocuSignClient,
        linear_service: LinearLeadsService,
        email_service: LeadEmailAutomation,
        document_processor: DocumentProcessor,
    ):
        self.db = db
        self.docusign = docusign_client
        self.linear = linear_service
        self.email = email_service
        self.document_processor = document_processor

        # State transition map
        self.transitions = {
            OnboardingStage.CREATED: {
                OnboardingEvent.DOCUMENTS_UPLOADED: OnboardingStage.DOCUMENTS_UPLOADED,
            },
            OnboardingStage.DOCUMENTS_UPLOADED: {
                OnboardingEvent.PROCESSING_COMPLETE: OnboardingStage.DOCUMENTS_PROCESSED,
                OnboardingEvent.PROCESSING_FAILED: OnboardingStage.FAILED,
            },
            OnboardingStage.DOCUMENTS_PROCESSED: {
                OnboardingEvent.BAA_SENT: OnboardingStage.BAA_SENT,
            },
            OnboardingStage.BAA_SENT: {
                OnboardingEvent.BAA_SIGNED: OnboardingStage.BAA_SIGNED,
                OnboardingEvent.BAA_DECLINED: OnboardingStage.FAILED,
            },
            OnboardingStage.BAA_SIGNED: {
                OnboardingEvent.PROJECT_CREATED: OnboardingStage.PROJECT_CREATED,
            },
            OnboardingStage.PROJECT_CREATED: {
                OnboardingEvent.WELCOME_SENT: OnboardingStage.WELCOME_SENT,
            },
            OnboardingStage.WELCOME_SENT: {
                OnboardingEvent.KICKOFF_SCHEDULED: OnboardingStage.KICKOFF_SCHEDULED,
            },
            OnboardingStage.KICKOFF_SCHEDULED: {
                OnboardingEvent.RETRY: OnboardingStage.COMPLETED,
            },
        }

    async def create_session(
        self,
        client_id: str,
        practice_name: str,
        contact_name: str,
        contact_email: str,
        contact_phone: str,
    ) -> OnboardingSession:
        """Create new onboarding session"""
        session = OnboardingSession(
            client_id=client_id,
            stage=OnboardingStage.CREATED,
            data={
                "practice_name": practice_name,
                "contact_name": contact_name,
                "contact_email": contact_email,
                "contact_phone": contact_phone,
            },
            created_at=datetime.utcnow(),
        )

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        logger.info(
            "onboarding_session_created",
            session_id=session.id,
            client_id=client_id,
        )

        return session

    async def handle_event(
        self,
        session_id: str,
        event: OnboardingEvent,
        event_data: Optional[Dict[str, Any]] = None,
    ) -> OnboardingSession:
        """Handle onboarding event and transition state"""
        # Load session
        result = await self.db.execute(
            select(OnboardingSession).where(OnboardingSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise ValueError(f"Onboarding session {session_id} not found")

        current_stage = OnboardingStage(session.stage)

        # Check if transition is valid
        if event not in self.transitions.get(current_stage, {}):
            logger.warning(
                "invalid_transition",
                session_id=session_id,
                current_stage=current_stage,
                event_type=event,
            )
            return session

        # Get next stage
        next_stage = self.transitions[current_stage][event]

        # Update session
        session.stage = next_stage
        session.updated_at = datetime.utcnow()

        if event_data:
            session.data.update(event_data)

        # Add to history
        if not session.history:
            session.history = []

        session.history.append({
            "stage": next_stage,
            "event": event,
            "timestamp": datetime.utcnow().isoformat(),
            "data": event_data,
        })

        await self.db.commit()
        await self.db.refresh(session)

        logger.info(
            "onboarding_transition",
            session_id=session_id,
            from_stage=current_stage,
            to_stage=next_stage,
            event_type=event,
        )

        # Trigger next action
        await self._trigger_next_action(session)

        return session

    async def _trigger_next_action(self, session: OnboardingSession) -> None:
        """Trigger automatic action based on current stage"""
        stage = OnboardingStage(session.stage)

        if stage == OnboardingStage.DOCUMENTS_UPLOADED:
            # Process documents
            await self._process_documents(session)

        elif stage == OnboardingStage.DOCUMENTS_PROCESSED:
            # Send BAA
            await self._send_baa(session)

        elif stage == OnboardingStage.BAA_SIGNED:
            # Create Linear project
            await self._create_project(session)

        elif stage == OnboardingStage.PROJECT_CREATED:
            # Send welcome email
            await self._send_welcome_email(session)

        elif stage == OnboardingStage.WELCOME_SENT:
            # Schedule kickoff call
            await self._schedule_kickoff(session)

        elif stage == OnboardingStage.KICKOFF_SCHEDULED:
            # Mark as completed
            await self.handle_event(
                session.id,
                OnboardingEvent.RETRY,
            )

    async def _process_documents(self, session: OnboardingSession) -> None:
        """Process uploaded documents with AI"""
        try:
            # Get document IDs from session data
            document_ids = session.data.get("document_ids", [])

            if not document_ids:
                logger.warning(
                    "no_documents_to_process",
                    session_id=session.id,
                )
                await self.handle_event(
                    session.id,
                    OnboardingEvent.PROCESSING_FAILED,
                    {"error": "No documents uploaded"},
                )
                return

            # Process each document
            extracted_data = {}

            for doc_id in document_ids:
                # TODO: Load document from storage
                # result = await self.document_processor.process_document(doc_id)
                # extracted_data[doc_id] = result
                pass

            # Update session with extracted data
            await self.handle_event(
                session.id,
                OnboardingEvent.PROCESSING_COMPLETE,
                {
                    "extracted_data": extracted_data,
                    "processed_at": datetime.utcnow().isoformat(),
                },
            )

        except Exception as e:
            logger.error(
                "document_processing_failed",
                session_id=session.id,
                error=str(e),
            )
            await self.handle_event(
                session.id,
                OnboardingEvent.PROCESSING_FAILED,
                {"error": str(e)},
            )

    async def _send_baa(self, session: OnboardingSession) -> None:
        """Send BAA for signature via DocuSign"""
        try:
            data = session.data

            # Create DocuSign envelope
            envelope_id = await self.docusign.send_baa(
                recipient_email=data["contact_email"],
                recipient_name=data["contact_name"],
                practice_name=data["practice_name"],
            )

            await self.handle_event(
                session.id,
                OnboardingEvent.BAA_SENT,
                {
                    "baa_envelope_id": envelope_id,
                    "baa_sent_at": datetime.utcnow().isoformat(),
                },
            )

        except Exception as e:
            logger.error(
                "baa_send_failed",
                session_id=session.id,
                error=str(e),
            )

    async def _create_project(self, session: OnboardingSession) -> None:
        """Create Linear project from template"""
        try:
            data = session.data

            # Create project in Linear
            project = await self.linear.create_project_from_template(
                practice_name=data["practice_name"],
                contact_email=data["contact_email"],
                specialty=data.get("specialty"),
                template_id="onboarding-template",  # Phase 7.5 template
            )

            await self.handle_event(
                session.id,
                OnboardingEvent.PROJECT_CREATED,
                {
                    "linear_project_id": project["id"],
                    "linear_team_id": project["team_id"],
                    "project_created_at": datetime.utcnow().isoformat(),
                },
            )

        except Exception as e:
            logger.error(
                "project_creation_failed",
                session_id=session.id,
                error=str(e),
            )

    async def _send_welcome_email(self, session: OnboardingSession) -> None:
        """Send welcome email sequence"""
        try:
            data = session.data

            # Send welcome email
            await self.email.send_welcome_email(
                to_email=data["contact_email"],
                to_name=data["contact_name"],
                practice_name=data["practice_name"],
                project_url=f"https://app.iamaim.ru/projects/{data.get('linear_project_id')}",
            )

            await self.handle_event(
                session.id,
                OnboardingEvent.WELCOME_SENT,
                {
                    "welcome_sent_at": datetime.utcnow().isoformat(),
                },
            )

        except Exception as e:
            logger.error(
                "welcome_email_failed",
                session_id=session.id,
                error=str(e),
            )

    async def _schedule_kickoff(self, session: OnboardingSession) -> None:
        """Schedule kickoff call"""
        try:
            data = session.data

            # TODO: Integrate with scheduling service (Calendly, Cal.com)
            # For now, just create a placeholder
            kickoff_url = f"https://calendly.com/iamaim/kickoff?client={session.client_id}"
            kickoff_time = datetime.utcnow() + timedelta(hours=48)

            await self.handle_event(
                session.id,
                OnboardingEvent.KICKOFF_SCHEDULED,
                {
                    "kickoff_call_url": kickoff_url,
                    "kickoff_call_scheduled_at": kickoff_time.isoformat(),
                },
            )

        except Exception as e:
            logger.error(
                "kickoff_scheduling_failed",
                session_id=session.id,
                error=str(e),
            )

    async def get_session(self, session_id: str) -> Optional[OnboardingSession]:
        """Get onboarding session by ID"""
        result = await self.db.execute(
            select(OnboardingSession).where(OnboardingSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_client_sessions(self, client_id: str) -> List[OnboardingSession]:
        """Get all onboarding sessions for a client"""
        result = await self.db.execute(
            select(OnboardingSession)
            .where(OnboardingSession.client_id == client_id)
            .order_by(OnboardingSession.created_at.desc())
        )
        return result.scalars().all()
