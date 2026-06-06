"""Integration tests for project creation flow.

Tests real interaction between LinearClient, TemplateEngine, and ProjectCreator
without mocks (except for HTTP calls to Linear API).
"""

import pytest
from unittest.mock import patch, AsyncMock
from pathlib import Path
import sys

# Add AIM/src to path
aim_src = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(aim_src))

from src.aim.services.project_creator import ProjectCreator, CreationResult
from src.aim.integrations.linear.client import LinearClient
from src.aim.templates.engine import TemplateEngine


class TestProjectCreationFlow:
    """Integration tests for end-to-end project creation."""

    @pytest.mark.asyncio
    async def test_full_project_creation_flow(self):
        """Test complete flow: template → Linear API → project created."""
        # Mock HTTP responses
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "projectCreate": {
                    "success": True,
                    "project": {
                        "id": "proj-123",
                        "name": "Acme Corp - Marketing Campaign",
                        "description": "Marketing campaign for Acme Corp in Healthcare industry",
                        "state": "planned",
                        "progress": 0.0,
                        "team": {"id": "team-123"},
                    },
                }
            }
        }
        mock_response.raise_for_status = lambda: None

        mock_issue_response = MagicMock()
        mock_issue_response.json.return_value = {
            "data": {
                "issueCreate": {
                    "success": True,
                    "issue": {
                        "id": "issue-1",
                        "title": "Task 1",
                        "description": None,
                        "state": {"name": "Todo"},
                        "priority": 0,
                        "project": {"id": "proj-123"},
                        "assignee": None,
                    },
                }
            }
        }
        mock_issue_response.raise_for_status = lambda: None

        # Create mock HTTP client
        mock_http_client = AsyncMock()
        mock_http_client.post.side_effect = [
            mock_response,  # Project creation
            *[mock_issue_response] * 15,  # 15 tasks
        ]
        mock_http_client.aclose = AsyncMock()

        # Create real components
        linear_client = LinearClient(api_key="test-key")
        template_engine = TemplateEngine()
        creator = ProjectCreator(
            client=linear_client,
            template_engine=template_engine,
        )

        # Inject mock client
        linear_client._client = mock_http_client

        # Execute full flow
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
        assert result.tasks_created == 15

        # Verify API calls
        assert mock_http_client.post.call_count == 16  # 1 project + 15 tasks

    @pytest.mark.asyncio
    async def test_template_rendering_with_real_engine(self):
        """Test that TemplateEngine correctly renders project template."""
        # Create real TemplateEngine
        engine = TemplateEngine()

        # Render template
        template_data = engine.render_template(
            template_name="project_template.yaml",
            variables={
                "client_name": "Test Client",
                "industry": "Technology",
                "start_date": "2026-06-01",
                "team_id": "team-456",
            },
        )

        # Verify rendered data
        assert template_data.project.name == "Test Client - Marketing Campaign"
        assert "Technology" in template_data.project.description
        assert template_data.project.team_id == "team-456"
        assert len(template_data.tasks) == 15
        assert len(template_data.milestones) == 3
        assert len(template_data.labels) == 7

        # Verify task structure
        first_task = template_data.tasks[0]
        assert first_task.title == "Competitor Analysis"
        assert first_task.priority == 1
        assert "Technology" in first_task.description

    @pytest.mark.asyncio
    async def test_validation_with_real_components(self):
        """Test validation using real TemplateEngine."""
        # Mock LinearClient
        mock_client = AsyncMock(spec=LinearClient)

        # Create real TemplateEngine
        engine = TemplateEngine()

        # Create ProjectCreator with real engine
        creator = ProjectCreator(
            client=mock_client,
            template_engine=engine,
        )

        # Test validation with complete variables
        is_valid, errors = await creator.validate_before_create(
            template_name="project_template.yaml",
            variables={
                "client_name": "Test",
                "industry": "Tech",
                "start_date": "2026-05-15",
                "team_id": "team-123",
            },
        )

        assert is_valid is True
        assert errors == []

        # Test validation with missing variables
        is_valid, errors = await creator.validate_before_create(
            template_name="project_template.yaml",
            variables={
                "client_name": "Test",
            },
        )

        assert is_valid is False
        assert len(errors) > 0
        assert any("Missing variables" in err for err in errors)

    @pytest.mark.asyncio
    async def test_error_handling_across_components(self):
        """Test error propagation through all components."""
        # Create mock HTTP client that fails
        mock_http_client = AsyncMock()
        mock_http_client.post.side_effect = Exception("Network error")
        mock_http_client.aclose = AsyncMock()

        # Create real components
        linear_client = LinearClient(api_key="test-key")
        template_engine = TemplateEngine()
        creator = ProjectCreator(
            client=linear_client,
            template_engine=template_engine,
        )

        # Inject mock client
        linear_client._client = mock_http_client

        # Execute flow (should handle error gracefully)
        result = await creator.create_project(
            template_name="project_template.yaml",
            variables={
                "client_name": "Test",
                "industry": "Tech",
                "start_date": "2026-05-15",
                "team_id": "team-123",
            },
        )

        # Verify error handling
        assert result.success is False
        assert "Network error" in result.error

    @pytest.mark.asyncio
    async def test_rollback_with_real_components(self):
        """Test rollback mechanism with real component interaction."""
        from unittest.mock import MagicMock

        # Mock HTTP responses
        mock_project_response = MagicMock()
        mock_project_response.json.return_value = {
            "data": {
                "projectCreate": {
                    "success": True,
                    "project": {
                        "id": "proj-rollback",
                        "name": "Test Project",
                        "description": "Test",
                        "state": "planned",
                        "progress": 0.0,
                        "team": {"id": "team-123"},
                    },
                }
            }
        }
        mock_project_response.raise_for_status = lambda: None

        mock_update_response = MagicMock()
        mock_update_response.json.return_value = {
            "data": {
                "projectUpdate": {
                    "success": True,
                    "project": {
                        "id": "proj-rollback",
                        "name": "Test Project",
                        "description": "Test",
                        "state": "canceled",
                        "progress": 0.0,
                        "team": {"id": "team-123"},
                    },
                }
            }
        }
        mock_update_response.raise_for_status = lambda: None

        # Create mock HTTP client
        mock_http_client = AsyncMock()
        # Project creation succeeds, all tasks fail
        mock_http_client.post.side_effect = [
            mock_project_response,  # Project creation
            *[Exception("Task failed")] * 15,  # All tasks fail
            mock_update_response,  # Rollback (update to canceled)
        ]
        mock_http_client.aclose = AsyncMock()

        # Create real components
        linear_client = LinearClient(api_key="test-key")
        template_engine = TemplateEngine()
        creator = ProjectCreator(
            client=linear_client,
            template_engine=template_engine,
        )

        # Inject mock client
        linear_client._client = mock_http_client

        # Execute flow with rollback
        result = await creator.create_project_with_rollback(
            template_name="project_template.yaml",
            variables={
                "client_name": "Test",
                "industry": "Tech",
                "start_date": "2026-05-15",
                "team_id": "team-123",
            },
        )

        # Verify rollback occurred
        assert result.success is False
        assert "Too many tasks failed" in result.error

        # Verify rollback call (last call should be update to canceled)
        last_call = mock_http_client.post.call_args_list[-1]
        assert "projectUpdate" in str(last_call)

    @pytest.mark.asyncio
    async def test_multiple_projects_creation(self):
        """Test creating multiple projects in sequence."""
        from unittest.mock import MagicMock

        # Mock HTTP responses
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "projectCreate": {
                    "success": True,
                    "project": {
                        "id": "proj-multi",
                        "name": "Multi Project",
                        "description": "Test",
                        "state": "planned",
                        "progress": 0.0,
                        "team": {"id": "team-123"},
                    },
                }
            }
        }
        mock_response.raise_for_status = lambda: None

        mock_issue_response = MagicMock()
        mock_issue_response.json.return_value = {
            "data": {
                "issueCreate": {
                    "success": True,
                    "issue": {
                        "id": "issue-multi",
                        "title": "Task",
                        "description": None,
                        "state": {"name": "Todo"},
                        "priority": 0,
                        "project": {"id": "proj-multi"},
                        "assignee": None,
                    },
                }
            }
        }
        mock_issue_response.raise_for_status = lambda: None

        # Create mock HTTP client
        mock_http_client = AsyncMock()
        # Each project: 1 project + 15 tasks = 16 calls
        # 3 projects = 48 calls
        mock_http_client.post.side_effect = [
            mock_response,
            *[mock_issue_response] * 15,
            mock_response,
            *[mock_issue_response] * 15,
            mock_response,
            *[mock_issue_response] * 15,
        ]
        mock_http_client.aclose = AsyncMock()

        # Create real components
        linear_client = LinearClient(api_key="test-key")
        template_engine = TemplateEngine()
        creator = ProjectCreator(
            client=linear_client,
            template_engine=template_engine,
        )

        # Inject mock client
        linear_client._client = mock_http_client

        # Create 3 projects
        results = []
        for i in range(3):
            result = await creator.create_project(
                template_name="project_template.yaml",
                variables={
                    "client_name": f"Client {i+1}",
                    "industry": "Tech",
                    "start_date": "2026-05-15",
                    "team_id": "team-123",
                },
            )
            results.append(result)

        # Verify all succeeded
        assert all(r.success for r in results)
        assert all(r.tasks_created == 15 for r in results)
        assert mock_http_client.post.call_count == 48
