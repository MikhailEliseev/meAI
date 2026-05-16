"""
Tests for Onboarding Workflow
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from aim.services.onboarding.workflow import (
    OnboardingWorkflow,
    OnboardingState,
    OnboardingEvent,
    OnboardingSession,
    TRANSITIONS,
)


@pytest.fixture
def mock_services():
    """Create mock services"""
    return {
        "document_processor": AsyncMock(),
        "docusign_client": AsyncMock(),
        "payment_service": AsyncMock(),
        "linear_client": AsyncMock(),
        "email_service": AsyncMock(),
        "calendar_service": AsyncMock(),
    }


@pytest.fixture
def workflow(mock_services):
    """Create workflow instance"""
    return OnboardingWorkflow(**mock_services)


@pytest.fixture
def sample_session():
    """Sample onboarding session"""
    return OnboardingSession(
        session_id="onb_client123_1234567890",
        client_id="client123",
        state=OnboardingState.LEAD_CAPTURED,
        lead_score=85,
        metadata={
            "email": "doctor@dental.com",
            "name": "Dr. Smith",
            "practice_name": "Smile Dental",
            "package_name": "Growth Package",
            "package_price": 5000,
        },
    )


class TestOnboardingWorkflow:
    """Test onboarding workflow"""

    @pytest.mark.asyncio
    async def test_start_onboarding_hot_lead(self, workflow, mock_services):
        """Test starting onboarding for hot lead (score >= 80)"""
        session = await workflow.start_onboarding(
            client_id="client123",
            lead_score=85,
        )

        assert session.client_id == "client123"
        assert session.lead_score == 85
        # Hot lead should auto-trigger document request
        assert session.state == OnboardingState.DOCUMENTS_REQUESTED
        mock_services["email_service"].send_template.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_onboarding_cold_lead(self, workflow):
        """Test starting onboarding for cold lead (score < 80)"""
        session = await workflow.start_onboarding(
            client_id="client456",
            lead_score=50,
        )

        assert session.client_id == "client456"
        assert session.lead_score == 50
        # Cold lead stays in LEAD_CAPTURED
        assert session.state == OnboardingState.LEAD_CAPTURED

    @pytest.mark.asyncio
    async def test_state_transitions_validation(self, workflow, sample_session):
        """Test state transition validation"""
        # Valid transition
        sample_session.state = OnboardingState.DOCUMENTS_REQUESTED
        await workflow.handle_event(sample_session, OnboardingEvent.DOCUMENTS_UPLOADED)
        # Should not raise

        # Invalid transition
        sample_session.state = OnboardingState.LEAD_CAPTURED
        with pytest.raises(ValueError, match="not allowed"):
            await workflow.handle_event(sample_session, OnboardingEvent.BAA_SIGNED)

    @pytest.mark.asyncio
    async def test_request_documents(self, workflow, sample_session, mock_services):
        """Test document request"""
        sample_session.state = OnboardingState.LEAD_CAPTURED
        session = await workflow.handle_event(
            sample_session,
            OnboardingEvent.LEAD_SCORED,
        )

        assert session.state == OnboardingState.DOCUMENTS_REQUESTED
        mock_services["email_service"].send_template.assert_called_once_with(
            to="doctor@dental.com",
            template="document_request",
            data={
                "client_name": "Dr. Smith",
                "upload_link": f"https://iamaim.ru/onboarding/{session.session_id}/upload",
                "required_documents": [
                    "Practice information",
                    "Analytics access",
                    "Advertising accounts",
                ],
            },
        )

    @pytest.mark.asyncio
    async def test_process_documents_approved(self, workflow, sample_session, mock_services):
        """Test document processing with approved validation"""
        sample_session.state = OnboardingState.DOCUMENTS_REQUESTED
        sample_session.documents = [
            {"id": "doc1", "path": "/tmp/doc1.pdf"},
            {"id": "doc2", "path": "/tmp/doc2.pdf"},
        ]

        # Mock approved validation
        mock_services["document_processor"].process_document.return_value = {
            "document_id": "doc1",
            "extraction": {"practice_name": "Smile Dental"},
            "validation": {
                "status": "approved",
                "requires_review": False,
            },
        }

        session = await workflow.handle_event(
            sample_session,
            OnboardingEvent.DOCUMENTS_UPLOADED,
        )

        # Should auto-progress to BAA_SENT
        assert session.state == OnboardingState.BAA_SENT
        assert mock_services["document_processor"].process_document.call_count == 2
        mock_services["docusign_client"].send_baa.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_documents_needs_review(self, workflow, sample_session, mock_services):
        """Test document processing with review needed"""
        sample_session.state = OnboardingState.DOCUMENTS_REQUESTED
        sample_session.documents = [
            {"id": "doc1", "path": "/tmp/doc1.pdf"},
        ]

        # Mock review needed
        mock_services["document_processor"].process_document.return_value = {
            "document_id": "doc1",
            "extraction": {"practice_name": None},
            "validation": {
                "status": "review",
                "requires_review": True,
            },
        }

        session = await workflow.handle_event(
            sample_session,
            OnboardingEvent.DOCUMENTS_UPLOADED,
        )

        # Should stay in DOCUMENTS_UPLOADED
        assert session.state == OnboardingState.DOCUMENTS_UPLOADED
        mock_services["document_processor"].create_review_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_baa(self, workflow, sample_session, mock_services):
        """Test BAA sending via DocuSign"""
        sample_session.state = OnboardingState.DOCUMENTS_PROCESSED

        mock_services["docusign_client"].send_baa.return_value = {
            "envelope_id": "env123",
            "status": "sent",
        }

        session = await workflow.handle_event(
            sample_session,
            OnboardingEvent.DOCUMENTS_VALIDATED,
        )

        assert session.state == OnboardingState.BAA_SENT
        assert session.baa_envelope_id == "env123"
        mock_services["docusign_client"].send_baa.assert_called_once_with(
            client_email="doctor@dental.com",
            client_name="Dr. Smith",
            practice_name="Smile Dental",
        )

    @pytest.mark.asyncio
    async def test_initiate_payment(self, workflow, sample_session, mock_services):
        """Test payment initiation via Helcim"""
        sample_session.state = OnboardingState.BAA_SIGNED

        mock_services["payment_service"].create_payment_intent.return_value = {
            "id": "pi_123",
            "payment_url": "https://helcim.com/pay/pi_123",
        }

        session = await workflow.handle_event(
            sample_session,
            OnboardingEvent.BAA_SIGNED,
        )

        assert session.state == OnboardingState.PAYMENT_PENDING
        assert session.payment_intent_id == "pi_123"
        mock_services["payment_service"].create_payment_intent.assert_called_once_with(
            amount=5000,
            currency="USD",
            customer_email="doctor@dental.com",
            description="AIM Agency - Growth Package",
        )
        mock_services["email_service"].send_template.assert_called_once()

    @pytest.mark.asyncio
    async def test_payment_failure(self, workflow, sample_session, mock_services):
        """Test payment failure handling"""
        sample_session.state = OnboardingState.PAYMENT_PENDING

        session = await workflow.handle_event(
            sample_session,
            OnboardingEvent.PAYMENT_FAILED,
        )

        # Should stay in PAYMENT_PENDING
        assert session.state == OnboardingState.PAYMENT_PENDING
        mock_services["email_service"].send_template.assert_called_once_with(
            to="doctor@dental.com",
            template="payment_failed",
            data={
                "client_name": "Dr. Smith",
                "retry_link": f"https://iamaim.ru/onboarding/{session.session_id}/payment",
            },
        )

    @pytest.mark.asyncio
    async def test_create_project(self, workflow, sample_session, mock_services):
        """Test Linear project creation"""
        sample_session.state = OnboardingState.PAYMENT_COMPLETED

        mock_services["linear_client"].create_project_from_template.return_value = {
            "id": "proj_123",
            "name": "Smile Dental - Launch",
        }
        
        # Mock calendar for auto-trigger chain
        mock_services["calendar_service"].find_available_slots.return_value = [
            datetime.utcnow() + timedelta(days=2),
        ]
        mock_services["calendar_service"].create_meeting.return_value = {
            "id": "meeting_123",
        }

        session = await workflow.handle_event(
            sample_session,
            OnboardingEvent.PAYMENT_COMPLETED,
        )

        # Should auto-progress to ONBOARDING_COMPLETE (via PROJECT_CREATED -> WELCOME_SENT -> KICKOFF_SCHEDULED)
        assert session.state == OnboardingState.ONBOARDING_COMPLETE
        assert session.linear_project_id == "proj_123"
        mock_services["linear_client"].create_project_from_template.assert_called_once_with(
            template_id="phase_7_5_template",
            project_name="Smile Dental - Launch",
            client_id="client123",
            metadata=None,
        )

    @pytest.mark.asyncio
    async def test_send_welcome_email(self, workflow, sample_session, mock_services):
        """Test welcome email sending"""
        sample_session.state = OnboardingState.PROJECT_CREATED
        sample_session.linear_project_id = "proj_123"

        # Mock calendar for auto-trigger
        mock_services["calendar_service"].find_available_slots.return_value = [
            datetime.utcnow() + timedelta(days=2),
        ]
        mock_services["calendar_service"].create_meeting.return_value = {
            "id": "meeting_123",
        }

        session = await workflow.handle_event(
            sample_session,
            OnboardingEvent.PROJECT_CREATED,
        )

        # Should auto-progress to ONBOARDING_COMPLETE (via WELCOME_SENT -> KICKOFF_SCHEDULED)
        assert session.state == OnboardingState.ONBOARDING_COMPLETE
        # Welcome email should be sent
        assert any(
            call[1].get("template") == "welcome_sequence"
            for call in mock_services["email_service"].send_template.call_args_list
        )

    @pytest.mark.asyncio
    async def test_schedule_kickoff(self, workflow, sample_session, mock_services):
        """Test kickoff call scheduling"""
        sample_session.state = OnboardingState.WELCOME_SENT

        mock_services["calendar_service"].find_available_slots.return_value = [
            datetime.utcnow() + timedelta(days=2),
        ]
        mock_services["calendar_service"].create_meeting.return_value = {
            "id": "meeting_123",
            "start_time": datetime.utcnow() + timedelta(days=2),
        }

        # Trigger via WELCOME_SENT event (auto-triggers kickoff scheduling)
        session = await workflow.handle_event(
            sample_session,
            OnboardingEvent.WELCOME_SENT,
        )

        # Should complete onboarding
        assert session.state == OnboardingState.ONBOARDING_COMPLETE
        assert session.kickoff_meeting_id == "meeting_123"
        mock_services["calendar_service"].find_available_slots.assert_called_once()
        mock_services["calendar_service"].create_meeting.assert_called_once()
        mock_services["email_service"].send_calendar_invite.assert_called_once()

    @pytest.mark.asyncio
    async def test_schedule_kickoff_no_slots(self, workflow, sample_session, mock_services):
        """Test kickoff scheduling with no available slots"""
        sample_session.state = OnboardingState.WELCOME_SENT

        mock_services["calendar_service"].find_available_slots.return_value = []

        # Trigger via WELCOME_SENT event
        session = await workflow.handle_event(
            sample_session,
            OnboardingEvent.WELCOME_SENT,
        )

        # Should stay in WELCOME_SENT (no slots available)
        assert session.state == OnboardingState.WELCOME_SENT
        assert session.kickoff_meeting_id is None

    @pytest.mark.asyncio
    async def test_full_workflow_happy_path(self, workflow, mock_services):
        """Test complete workflow from start to finish"""
        # Mock all services
        mock_services["document_processor"].process_document.return_value = {
            "document_id": "doc1",
            "extraction": {"practice_name": "Smile Dental"},
            "validation": {"status": "approved", "requires_review": False},
        }
        mock_services["docusign_client"].send_baa.return_value = {
            "envelope_id": "env123",
            "status": "sent",
        }
        mock_services["payment_service"].create_payment_intent.return_value = {
            "id": "pi_123",
            "payment_url": "https://helcim.com/pay/pi_123",
        }
        mock_services["linear_client"].create_project_from_template.return_value = {
            "id": "proj_123",
        }
        mock_services["calendar_service"].find_available_slots.return_value = [
            datetime.utcnow() + timedelta(days=2),
        ]
        mock_services["calendar_service"].create_meeting.return_value = {
            "id": "meeting_123",
        }

        # Start onboarding
        session = await workflow.start_onboarding(
            client_id="client123",
            lead_score=85,
        )
        session.metadata = {
            "email": "doctor@dental.com",
            "name": "Dr. Smith",
            "practice_name": "Smile Dental",
            "package_price": 5000,
        }

        # Upload documents
        session.documents = [{"id": "doc1", "path": "/tmp/doc1.pdf"}]
        session = await workflow.handle_event(session, OnboardingEvent.DOCUMENTS_UPLOADED)

        # BAA signed (auto-progressed to BAA_SENT after documents)
        session = await workflow.handle_event(session, OnboardingEvent.BAA_SIGNED)

        # Payment completed (now in PAYMENT_PENDING)
        session = await workflow.handle_event(session, OnboardingEvent.PAYMENT_COMPLETED)

        # Should reach ONBOARDING_COMPLETE
        assert session.state == OnboardingState.ONBOARDING_COMPLETE
        assert session.baa_envelope_id == "env123"
        assert session.payment_intent_id == "pi_123"
        assert session.linear_project_id == "proj_123"
        assert session.kickoff_meeting_id == "meeting_123"

    def test_transitions_completeness(self):
        """Test that all states have transition rules"""
        for state in OnboardingState:
            assert state in TRANSITIONS, f"Missing transition rules for {state}"
