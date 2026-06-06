"""Simplified tests for Linear GraphQL API client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

import sys
from pathlib import Path

# Add AIM/src to path
aim_src = Path(__file__).parent.parent.parent.parent / "src"
sys.path.insert(0, str(aim_src))

from src.aim.integrations.linear.client import LinearClient, LinearProject, LinearIssue


class TestLinearClientInit:
    """Test LinearClient initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        client = LinearClient(api_key="test_key")

        assert client.api_url == "https://api.linear.app/graphql"
        assert client.headers["Authorization"] == "test_key"
        assert client.headers["Content-Type"] == "application/json"
        assert client.timeout == 30.0
        assert client.max_retries == 3

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        client = LinearClient(
            api_key="custom_key",
            api_url="https://custom.api/graphql",
            timeout=60.0,
            max_retries=5,
        )

        assert client.api_url == "https://custom.api/graphql"
        assert client.headers["Authorization"] == "custom_key"
        assert client.timeout == 60.0
        assert client.max_retries == 5


class TestLinearClientContextManager:
    """Test async context manager."""

    @pytest.mark.asyncio
    async def test_context_manager_creates_client(self):
        """Test that context manager creates httpx client."""
        client = LinearClient(api_key="test_key")

        assert client._client is None

        async with client:
            assert client._client is not None


class TestExecuteQuery:
    """Test _execute_query method."""

    @pytest.mark.asyncio
    async def test_execute_query_success(self):
        """Test successful query execution."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"test": "value"}}
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response

        with patch("httpx.AsyncClient", return_value=mock_client):
            client = LinearClient(api_key="test_key")
            async with client:
                result = await client._execute_query("query { test }")

        assert result == {"test": "value"}

    @pytest.mark.asyncio
    async def test_execute_query_graphql_error(self):
        """Test query execution with GraphQL errors."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "errors": [{"message": "Field not found"}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response

        with patch("httpx.AsyncClient", return_value=mock_client):
            client = LinearClient(api_key="test_key")
            async with client:
                with pytest.raises(ValueError, match="GraphQL errors"):
                    await client._execute_query("query { test }")

    @pytest.mark.asyncio
    async def test_execute_query_without_context_manager(self):
        """Test query execution without context manager raises error."""
        client = LinearClient(api_key="test_key")

        with pytest.raises(RuntimeError, match="Client not initialized"):
            await client._execute_query("query { test }")


class TestGetProjects:
    """Test get_projects method."""

    @pytest.mark.asyncio
    async def test_get_projects_success(self):
        """Test fetching projects successfully."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "projects": {
                    "nodes": [
                        {
                            "id": "proj1",
                            "name": "Project 1",
                            "description": "Test project",
                            "state": "started",
                            "progress": 0.5,
                            "team": {"id": "team1"},
                        }
                    ]
                }
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response

        with patch("httpx.AsyncClient", return_value=mock_client):
            client = LinearClient(api_key="test_key")
            async with client:
                projects = await client.get_projects()

        assert len(projects) == 1
        assert projects[0].id == "proj1"
        assert projects[0].name == "Project 1"


class TestCreateProject:
    """Test create_project method."""

    @pytest.mark.asyncio
    async def test_create_project_success(self):
        """Test creating project successfully."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "projectCreate": {
                    "success": True,
                    "project": {
                        "id": "proj1",
                        "name": "New Project",
                        "description": "Test project",
                        "state": "planned",
                        "progress": 0.0,
                        "team": {"id": "team1"},
                    },
                }
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response

        with patch("httpx.AsyncClient", return_value=mock_client):
            client = LinearClient(api_key="test_key")
            async with client:
                project = await client.create_project(
                    name="New Project",
                    team_id="team1",
                    description="Test project",
                )

        assert project.id == "proj1"
        assert project.name == "New Project"
