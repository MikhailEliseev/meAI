"""
Tests for Onboarding Workflow Automation

Tests state machine transitions, automatic actions, and error handling.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from aim.services.onboarding.workflow import (
    OnboardingWorkflow,
    OnboardingStage,
    OnboardingEvent,
    OnboardingData,
)
from aim.models.onboarding import OnboardingSession


@pytest.fixture
def mock_db():
    """Mock database session"""
    db = AsyncMock(spec=AsyncSession)
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def mock_docusign():
    """Mock DocuSign client"""
    client = AsyncMock()
    client.send_baa = AsyncMock(return_value="envelope-123")
    client.get_envelope_status = AsyncMock()
    return client


@pytest.fixture
def mock_linear():
    """Mock Linear service"""
    service = AsyncMock()
    service.create_project_from_template = AsyncMock(
        return_value={
            "id": "project-123",
            "team_id": "team-123",
        }
    )
    return service


@pytest.fixture
def mock_email():
    """Mock email service"""
    service = AsyncMock()
    service.send_welcome_email = AsyncMock()
    return service


@pytest.fixture
def mock_document_processor():
    """Mock document processor"""
    processor = AsyncMock()
    processor.process_document = AsyncMock(
        return_value={
            "practice_name": "Test Clinic",
            "inn": "1234567890",
        }
    )
    return processor


@pytest.fixture
def workflow(mock_db, mock_docusign, mock_linear, mock_email, mock_document_processor):
    """Create workflow instance with mocked dependencies"""
    return OnboardingWorkflow(
        db=mock_db,
        docusign_client=mock_docusign,
        linear_service=mock_linear,
        email_service=mock_email,
        document_processor=mock_document_processor,
    )


@pytest.mark.asyncio
async def test_create_session(workflow, mock_db):
    """Test creating new onboarding session"""
    # Arrange
    client_id = "client-123"
    practice_name = "Test Clinic"
    contact_name = "Dr. Smith"
    contact_email = "smith@test.com"
    contact_phone = "+1234567890"

    # Act
    session = await workflow.create_session(
        client_id=client_id,
        practice_name=practice_name,
        contact_name=contact_name,
        contact_email=contact_email,
        contact_phone=contact_phone,
    )

    # Assert
    assert session.client_id == client_id
    assert session.stage == OnboardingStage.CREATED
    assert session.data["practice_name"] == practice_name
    assert session.data["contact_name"] == contact_name
    assert session.data["contact_email"] == contact_email
    assert session.data["contact_phone"] == contact_phone
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_documents_uploaded_transition(workflow, mock_db):
    """Test transition from CREATED to DOCUMENTS_UPLOADED"""
    # Arrange
    session = OnboardingSession(
        id="session-123",
        client_id="client-123",
        stage=OnboardingStage.CREATED,
        data={
            "practice_name": "Test Clinic",
            "contact_name": "Dr. Smith",
            "contact_email": "smith@test.com",
        },
        history=[],
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = session
    mock_db.execute.return_value = mock_result

    # Mock _trigger_next_action to prevent automatic transitions
    with patch.object(workflow, '_trigger_next_action', new_callable=AsyncMock):
        # Act
        result = await workflow.handle_event(
            session_id="session-123",
            event=OnboardingEvent.DOCUMENTS_UPLOADED,
            event_data={"document_ids": ["doc-1", "doc-2"]},
        )

        # Assert
        assert result.stage == OnboardingStage.DOCUMENTS_UPLOADED
        assert "document_ids" in result.data
        assert len(result.history) == 1
        assert result.history[0]["event"] == OnboardingEvent.DOCUMENTS_UPLOADED
        mock_db.commit.assert_called()


@pytest.mark.asyncio
async def test_invalid_transition(workflow, mock_db):
    """Test that invalid transitions are rejected"""
    # Arrange
    session = OnboardingSession(
        id="session-123",
        client_id="client-123",
        stage=OnboardingStage.CREATED,
        data={},
        history=[],
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = session
    mock_db.execute.return_value = mock_result

    # Act
    result = await workflow.handle_event(
        session_id="session-123",
        event=OnboardingEvent.BAA_SIGNED,  # Invalid from CREATED
    )

    # Assert
    assert result.stage == OnboardingStage.CREATED  # Stage unchanged
    assert len(result.history) == 0  # No history entry


@pytest.mark.asyncio
async def test_process_documents_success(workflow, mock_db, mock_document_processor):
    """Test successful document processing"""
    # Arrange
    session = OnboardingSession(
        id="session-123",
        client_id="client-123",
        stage=OnboardingStage.DOCUMENTS_UPLOADED,
        data={"document_ids": ["doc-1", "doc-2"]},
        history=[],
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = session
    mock_db.execute.return_value = mock_result

    # Act
    await workflow._process_documents(session)

    # Assert
    # Should trigger PROCESSING_COMPLETE event
    assert mock_db.commit.called


@pytest.mark.asyncio
async def test_process_documents_no_documents(workflow, mock_db):
    """Test document processing with no documents"""
    # Arrange
    session = OnboardingSession(
        id="session-123",
        client_id="client-123",
        stage=OnboardingStage.DOCUMENTS_UPLOADED,
        data={},  # No document_ids
        history=[],
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = session
    mock_db.execute.return_value = mock_result

    # Act
    await workflow._process_documents(session)

    # Assert
    # Should trigger PROCESSING_FAILED event
    assert mock_db.commit.called


@pytest.mark.asyncio
async def test_send_baa(workflow, mock_db, mock_docusign):
    """Test sending BAA via DocuSign"""
    # Arrange
    session = OnboardingSession(
        id="session-123",
        client_id="client-123",
        stage=OnboardingStage.DOCUMENTS_PROCESSED,
        data={
            "practice_name": "Test Clinic",
            "contact_name": "Dr. Smith",
            "contact_email": "smith@test.com",
        },
        history=[],
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = session
    mock_db.execute.return_value = mock_result

    # Act
    await workflow._send_baa(session)

    # Assert
    mock_docusign.send_baa.assert_called_once_with(
        recipient_email="smith@test.com",
        recipient_name="Dr. Smith",
        practice_name="Test Clinic",
    )
    assert mock_db.commit.called


@pytest.mark.asyncio
async def test_create_project(workflow, mock_db, mock_linear):
    """Test creating Linear project"""
    # Arrange
    session = OnboardingSession(
        id="session-123",
        client_id="client-123",
        stage=OnboardingStage.BAA_SIGNED,
        data={
            "practice_name": "Test Clinic",
            "contact_email": "smith@test.com",
            "specialty": "Dentistry",
        },
        history=[],
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = session
    mock_db.execute.return_value = mock_result

    # Act
    await workflow._create_project(session)

    # Assert
    mock_linear.create_project_from_template.assert_called_once()
    call_kwargs = mock_linear.create_project_from_template.call_args.kwargs
    assert call_kwargs["practice_name"] == "Test Clinic"
    assert call_kwargs["contact_email"] == "smith@test.com"
    assert call_kwargs["specialty"] == "Dentistry"
    assert mock_db.commit.called


@pytest.mark.asyncio
async def test_send_welcome_email(workflow, mock_db, mock_email):
    """Test sending welcome email"""
    # Arrange
    session = OnboardingSession(
        id="session-123",
        client_id="client-123",
        stage=OnboardingStage.PROJECT_CREATED,
        data={
            "practice_name": "Test Clinic",
            "contact_name": "Dr. Smith",
            "contact_email": "smith@test.com",
            "linear_project_id": "project-123",
        },
        history=[],
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = session
    mock_db.execute.return_value = mock_result

    # Act
    await workflow._send_welcome_email(session)

    # Assert
    mock_email.send_welcome_email.assert_called_once()
    call_kwargs = mock_email.send_welcome_email.call_args.kwargs
    assert call_kwargs["to_email"] == "smith@test.com"
    assert call_kwargs["to_name"] == "Dr. Smith"
    assert call_kwargs["practice_name"] == "Test Clinic"
    assert "project-123" in call_kwargs["project_url"]
    assert mock_db.commit.called


@pytest.mark.asyncio
async def test_schedule_kickoff(workflow, mock_db):
    """Test scheduling kickoff call"""
    # Arrange
    session = OnboardingSession(
        id="session-123",
        client_id="client-123",
        stage=OnboardingStage.WELCOME_SENT,
        data={},
        history=[],
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = session
    mock_db.execute.return_value = mock_result

    # Act
    await workflow._schedule_kickoff(session)

    # Assert
    assert mock_db.commit.called
    # Should have kickoff_call_url and kickoff_call_scheduled_at in data


@pytest.mark.asyncio
async def test_full_workflow_happy_path(workflow, mock_db, mock_docusign, mock_linear, mock_email):
    """Test complete workflow from start to finish"""
    # Arrange
    session = OnboardingSession(
        id="session-123",
        client_id="client-123",
        stage=OnboardingStage.CREATED,
        data={
            "practice_name": "Test Clinic",
            "contact_name": "Dr. Smith",
            "contact_email": "smith@test.com",
        },
        history=[],
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = session
    mock_db.execute.return_value = mock_result

    # Mock _trigger_next_action to prevent automatic transitions
    with patch.object(workflow, '_trigger_next_action', new_callable=AsyncMock):
        # Act & Assert - Step 1: Documents uploaded
        await workflow.handle_event(
            session_id="session-123",
            event=OnboardingEvent.DOCUMENTS_UPLOADED,
            event_data={"document_ids": ["doc-1"]},
        )
        assert session.stage == OnboardingStage.DOCUMENTS_UPLOADED

        # Step 2: Processing complete
        await workflow.handle_event(
            session_id="session-123",
            event=OnboardingEvent.PROCESSING_COMPLETE,
        )
        assert session.stage == OnboardingStage.DOCUMENTS_PROCESSED

        # Step 3: BAA sent
        await workflow.handle_event(
            session_id="session-123",
            event=OnboardingEvent.BAA_SENT,
        )
        assert session.stage == OnboardingStage.BAA_SENT

        # Step 4: BAA signed
        await workflow.handle_event(
            session_id="session-123",
            event=OnboardingEvent.BAA_SIGNED,
        )
        assert session.stage == OnboardingStage.BAA_SIGNED

        # Step 5: Project created
        await workflow.handle_event(
            session_id="session-123",
            event=OnboardingEvent.PROJECT_CREATED,
        )
        assert session.stage == OnboardingStage.PROJECT_CREATED

        # Step 6: Welcome sent
        await workflow.handle_event(
            session_id="session-123",
            event=OnboardingEvent.WELCOME_SENT,
        )
        assert session.stage == OnboardingStage.WELCOME_SENT

        # Step 7: Kickoff scheduled
        await workflow.handle_event(
            session_id="session-123",
            event=OnboardingEvent.KICKOFF_SCHEDULED,
        )
        assert session.stage == OnboardingStage.KICKOFF_SCHEDULED


@pytest.mark.asyncio
async def test_workflow_failure_path(workflow, mock_db):
    """Test workflow failure scenarios"""
    # Arrange
    session = OnboardingSession(
        id="session-123",
        client_id="client-123",
        stage=OnboardingStage.DOCUMENTS_UPLOADED,
        data={},
        history=[],
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = session
    mock_db.execute.return_value = mock_result

    # Act - Processing failed
    await workflow.handle_event(
        session_id="session-123",
        event=OnboardingEvent.PROCESSING_FAILED,
        event_data={"error": "Invalid document format"},
    )

    # Assert
    assert session.stage == OnboardingStage.FAILED
    assert "error" in session.data


@pytest.mark.asyncio
async def test_get_session(workflow, mock_db):
    """Test retrieving session by ID"""
    # Arrange
    expected_session = OnboardingSession(
        id="session-123",
        client_id="client-123",
        stage=OnboardingStage.CREATED,
        data={},
        history=[],
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = expected_session
    mock_db.execute.return_value = mock_result

    # Act
    session = await workflow.get_session("session-123")

    # Assert
    assert session == expected_session
    mock_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_client_sessions(workflow, mock_db):
    """Test retrieving all sessions for a client"""
    # Arrange
    expected_sessions = [
        OnboardingSession(
            id="session-1",
            client_id="client-123",
            stage=OnboardingStage.COMPLETED,
            data={},
            history=[],
        ),
        OnboardingSession(
            id="session-2",
            client_id="client-123",
            stage=OnboardingStage.CREATED,
            data={},
            history=[],
        ),
    ]

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = expected_sessions
    mock_db.execute.return_value = mock_result

    # Act
    sessions = await workflow.get_client_sessions("client-123")

    # Assert
    assert len(sessions) == 2
    assert sessions == expected_sessions
    mock_db.execute.assert_called_once()
