"""Tests for ProjectCreator service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import sys

# Add AIM/src to path
aim_src = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(aim_src))

from aim.services.project_creator import ProjectCreator, CreationResult
from aim.integrations.linear.client import LinearClient, LinearProject, LinearIssue
from aim.templates.engine import TemplateEngine


class TestProjectCreator:
    """Test ProjectCreator class."""

    @pytest.mark.asyncio
    async def test_create_project_success(self):
        """Test successful project creation."""
        # Mock LinearClient
        mock_client = AsyncMock(spec=LinearClient)
        mock_project = LinearProject(
            id="proj-123",
            name="Acme Corp - Marketing Campaign",
            description="Test",
            state="planned",
            teamId="team-123",
        )
        mock_client.create_project.return_value = mock_project
        mock_client.create_issue.return_value = LinearIssue(
            id="issue-1",
            title="Task 1",
            state="Todo",
            teamId="team-123",
        )

        # Create ProjectCreator
        creator = ProjectCreator(client=mock_client)

        # Create project
        result = await creator.create_project(
            template_name="project_template.yaml",
            variables={
                "client_name": "Acme Corp",
                "industry": "Healthcare",
                "start_date": "2026-05-15",
                "team_id": "team-123",
            },
        )

        # Verify result
        assert result.success is True
        assert result.project_id == "proj-123"
        assert result.project_name == "Acme Corp - Marketing Campaign"
        assert result.tasks_created == 15  # From template

        # Verify API calls
        mock_client.create_project.assert_called_once()
        assert mock_client.create_issue.call_count == 15

    @pytest.mark.asyncio
    async def test_create_project_template_not_found(self):
        """Test project creation with non-existent template."""
        mock_client = AsyncMock(spec=LinearClient)
        creator = ProjectCreator(client=mock_client)

        # Non-existent template
        result = await creator.create_project(
            template_name="nonexistent.yaml",
            variables={
                "client_name": "Acme Corp",
                "industry": "Healthcare",
                "team_id": "team-123",
            },
        )

        # Verify failure
        assert result.success is False
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_create_project_api_error(self):
        """Test project creation with API error."""
        mock_client = AsyncMock(spec=LinearClient)
        mock_client.create_project.side_effect = Exception("API Error")

        creator = ProjectCreator(client=mock_client)

        result = await creator.create_project(
            template_name="project_template.yaml",
            variables={
                "client_name": "Acme Corp",
                "industry": "Healthcare",
                "start_date": "2026-05-15",
                "team_id": "team-123",
            },
        )

        # Verify failure
        assert result.success is False
        assert "API Error" in result.error

    @pytest.mark.asyncio
    async def test_create_project_with_rollback_success(self):
        """Test project creation with rollback on success."""
        mock_client = AsyncMock(spec=LinearClient)
        mock_project = LinearProject(
            id="proj-123",
            name="Test Project",
            description="Test",
            state="planned",
            teamId="team-123",
        )
        mock_client.create_project.return_value = mock_project
        mock_client.create_issue.return_value = LinearIssue(
            id="issue-1",
            title="Task 1",
            state="Todo",
            teamId="team-123",
        )

        creator = ProjectCreator(client=mock_client)

        result = await creator.create_project_with_rollback(
            template_name="project_template.yaml",
            variables={
                "client_name": "Acme Corp",
                "industry": "Healthcare",
                "start_date": "2026-05-15",
                "team_id": "team-123",
            },
        )

        assert result.success is True
        assert result.project_id == "proj-123"

    @pytest.mark.asyncio
    async def test_create_project_with_rollback_failure(self):
        """Test project creation with rollback on failure."""
        mock_client = AsyncMock(spec=LinearClient)
        mock_project = LinearProject(
            id="proj-123",
            name="Test Project",
            description="Test",
            state="planned",
            teamId="team-123",
        )
        mock_client.create_project.return_value = mock_project
        # All tasks fail
        mock_client.create_issue.side_effect = Exception("Task creation failed")

        creator = ProjectCreator(client=mock_client)

        result = await creator.create_project_with_rollback(
            template_name="project_template.yaml",
            variables={
                "client_name": "Acme Corp",
                "industry": "Healthcare",
                "start_date": "2026-05-15",
                "team_id": "team-123",
            },
        )

        # Verify failure and rollback
        assert result.success is False
        mock_client.update_project.assert_called_once_with(
            project_id="proj-123",
            state="canceled",
        )

    @pytest.mark.asyncio
    async def test_validate_before_create_success(self):
        """Test validation before creation - success."""
        mock_client = AsyncMock(spec=LinearClient)
        creator = ProjectCreator(client=mock_client)

        is_valid, errors = await creator.validate_before_create(
            template_name="project_template.yaml",
            variables={
                "client_name": "Acme Corp",
                "industry": "Healthcare",
                "start_date": "2026-05-15",
                "team_id": "team-123",
            },
        )

        assert is_valid is True
        assert errors == []

    @pytest.mark.asyncio
    async def test_validate_before_create_missing_variables(self):
        """Test validation before creation - missing variables."""
        mock_client = AsyncMock(spec=LinearClient)
        creator = ProjectCreator(client=mock_client)

        is_valid, errors = await creator.validate_before_create(
            template_name="project_template.yaml",
            variables={
                "client_name": "Acme Corp",
            },
        )

        assert is_valid is False
        assert len(errors) > 0
        assert any("Missing variables" in err for err in errors)

    @pytest.mark.asyncio
    async def test_validate_before_create_template_not_found(self):
        """Test validation before creation - template not found."""
        mock_client = AsyncMock(spec=LinearClient)
        creator = ProjectCreator(client=mock_client)

        is_valid, errors = await creator.validate_before_create(
            template_name="nonexistent.yaml",
            variables={},
        )

        assert is_valid is False
        assert any("Template not found" in err for err in errors)
