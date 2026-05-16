"""Tests for Linear GraphQL API client."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

import sys
from pathlib import Path

# Add AIM/src to path
aim_src = Path(__file__).parent.parent.parent.parent / "src"
sys.path.insert(0, str(aim_src))

from aim.integrations.linear.client import LinearClient, LinearProject, LinearIssue


@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient."""
    client = AsyncMock(spec=httpx.AsyncClient)
    client.post = AsyncMock()
    client.aclose = AsyncMock()
    return client


@pytest_asyncio.fixture
async def linear_client(mock_httpx_client):
    """Create LinearClient with mocked httpx."""
    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        client = LinearClient(api_key="test_key")
        async with client:
            yield client


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

        # Client should be closed after exit
        assert client._client is not None  # Reference remains

    @pytest.mark.asyncio
    async def test_context_manager_closes_client(self, mock_httpx_client):
        """Test that context manager closes httpx client."""
        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            client = LinearClient(api_key="test_key")

            async with client:
                pass

            mock_httpx_client.aclose.assert_called_once()


class TestExecuteQuery:
    """Test _execute_query method."""

    @pytest.mark.asyncio
    async def test_execute_query_success(self, linear_client, mock_httpx_client):
        """Test successful query execution."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"test": "value"}}
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_response

        result = await linear_client._execute_query("query { test }")

        assert result == {"test": "value"}
        mock_httpx_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_query_with_variables(self, linear_client, mock_httpx_client):
        """Test query execution with variables."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"test": "value"}}
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_response

        variables = {"id": "123"}
        result = await linear_client._execute_query("query { test }", variables)

        assert result == {"test": "value"}
        call_args = mock_httpx_client.post.call_args
        assert call_args[1]["json"]["variables"] == variables

    @pytest.mark.asyncio
    async def test_execute_query_graphql_error(self, linear_client, mock_httpx_client):
        """Test query execution with GraphQL errors."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "errors": [{"message": "Field not found"}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_response

        with pytest.raises(ValueError, match="GraphQL errors"):
            await linear_client._execute_query("query { test }")

    @pytest.mark.asyncio
    async def test_execute_query_http_error_with_retry(self, linear_client, mock_httpx_client):
        """Test query execution with HTTP error and retry."""
        mock_httpx_client.post.side_effect = [
            httpx.HTTPError("Connection failed"),
            httpx.HTTPError("Connection failed"),
            MagicMock(json=lambda: {"data": {"test": "value"}}, raise_for_status=lambda: None),
        ]

        result = await linear_client._execute_query("query { test }")

        assert result == {"test": "value"}
        assert mock_httpx_client.post.call_count == 3

    @pytest.mark.asyncio
    async def test_execute_query_max_retries_exceeded(self, linear_client, mock_httpx_client):
        """Test query execution fails after max retries."""
        mock_httpx_client.post.side_effect = httpx.HTTPError("Connection failed")

        with pytest.raises(httpx.HTTPError):
            await linear_client._execute_query("query { test }")

        assert mock_httpx_client.post.call_count == 3  # max_retries

    @pytest.mark.asyncio
    async def test_execute_query_without_context_manager(self):
        """Test query execution without context manager raises error."""
        client = LinearClient(api_key="test_key")

        with pytest.raises(RuntimeError, match="Client not initialized"):
            await client._execute_query("query { test }")


class TestGetProjects:
    """Test get_projects method."""

    @pytest.mark.asyncio
    async def test_get_projects_success(self, linear_client, mock_httpx_client):
        """Test fetching projects successfully."""
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
        mock_httpx_client.post.return_value = mock_response

        projects = await linear_client.get_projects()

        assert len(projects) == 1
        assert projects[0].id == "proj1"
        assert projects[0].name == "Project 1"
        assert projects[0].progress == 0.5

    @pytest.mark.asyncio
    async def test_get_projects_with_team_filter(self, linear_client, mock_httpx_client):
        """Test fetching projects with team filter."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"projects": {"nodes": []}}}
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_response

        await linear_client.get_projects(team_id="team1")

        call_args = mock_httpx_client.post.call_args
        assert call_args[1]["json"]["variables"]["teamId"] == "team1"

    @pytest.mark.asyncio
    async def test_get_projects_empty_result(self, linear_client, mock_httpx_client):
        """Test fetching projects with empty result."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"projects": {"nodes": []}}}
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_response

        projects = await linear_client.get_projects()

        assert projects == []


class TestGetProject:
    """Test get_project method."""

    @pytest.mark.asyncio
    async def test_get_project_success(self, linear_client, mock_httpx_client):
        """Test fetching single project successfully."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "project": {
                    "id": "proj1",
                    "name": "Project 1",
                    "description": "Test project",
                    "state": "started",
                    "progress": 0.5,
                    "team": {"id": "team1"},
                }
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_response

        project = await linear_client.get_project("proj1")

        assert project is not None
        assert project.id == "proj1"
        assert project.name == "Project 1"

    @pytest.mark.asyncio
    async def test_get_project_not_found(self, linear_client, mock_httpx_client):
        """Test fetching non-existent project."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"project": None}}
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_response

        project = await linear_client.get_project("nonexistent")

        assert project is None


class TestCreateProject:
    """Test create_project method."""

    @pytest.mark.asyncio
    async def test_create_project_success(self, linear_client, mock_httpx_client):
        """Test creating project successfully."""
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
        mock_httpx_client.post.return_value = mock_response

        project = await linear_client.create_project(
            name="New Project",
            team_id="team1",
            description="Test project",
        )

        assert project.id == "proj1"
        assert project.name == "New Project"
        assert project.state == "planned"

    @pytest.mark.asyncio
    async def test_create_project_without_description(self, linear_client, mock_httpx_client):
        """Test creating project without description."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "projectCreate": {
                    "success": True,
                    "project": {
                        "id": "proj1",
                        "name": "New Project",
                        "description": None,
                        "state": "planned",
                        "progress": 0.0,
                        "team": {"id": "team1"},
                    },
                }
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_response

        project = await linear_client.create_project(
            name="New Project",
            team_id="team1",
        )

        assert project.description is None

    @pytest.mark.asyncio
    async def test_create_project_failure(self, linear_client, mock_httpx_client):
        """Test creating project failure."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {"projectCreate": {"success": False}}
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_response

        with pytest.raises(ValueError, match="Failed to create project"):
            await linear_client.create_project(
                name="New Project",
                team_id="team1",
            )


class TestUpdateProject:
    """Test update_project method."""

    @pytest.mark.asyncio
    async def test_update_project_success(self, linear_client, mock_httpx_client):
        """Test updating project successfully."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "projectUpdate": {
                    "success": True,
                    "project": {
                        "id": "proj1",
                        "name": "Updated Project",
                        "description": "Updated description",
                        "state": "started",
                        "progress": 0.5,
                        "team": {"id": "team1"},
                    },
                }
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_response

        project = await linear_client.update_project(
            project_id="proj1",
            name="Updated Project",
            description="Updated description",
            state="started",
            progress=0.5,
        )

        assert project.name == "Updated Project"
        assert project.state == "started"
        assert project.progress == 0.5

    @pytest.mark.asyncio
    async def test_update_project_partial(self, linear_client, mock_httpx_client):
        """Test updating project with partial data."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "projectUpdate": {
                    "success": True,
                    "project": {
                        "id": "proj1",
                        "name": "Project 1",
                        "description": "Test project",
                        "state": "completed",
                        "progress": 1.0,
                        "team": {"id": "team1"},
                    },
                }
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_response

        project = await linear_client.update_project(
            project_id="proj1",
            state="completed",
            progress=1.0,
        )

        assert project.state == "completed"
        assert project.progress == 1.0

    @pytest.mark.asyncio
    async def test_update_project_failure(self, linear_client, mock_httpx_client):
        """Test updating project failure."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {"projectUpdate": {"success": False}}
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_response

        with pytest.raises(ValueError, match="Failed to update project"):
            await linear_client.update_project(
                project_id="proj1",
                name="Updated Project",
            )


class TestGetIssues:
    """Test get_issues method."""

    @pytest.mark.asyncio
    async def test_get_issues_success(self, linear_client, mock_httpx_client):
        """Test fetching issues successfully."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "issues": {
                    "nodes": [
                        {
                            "id": "issue1",
                            "title": "Task 1",
                            "description": "Test task",
                            "state": {"name": "Todo"},
                            "priority": 2,
                            "project": {"id": "proj1"},
                            "assignee": {"id": "user1"},
                        }
                    ]
                }
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_response

        issues = await linear_client.get_issues()

        assert len(issues) == 1
        assert issues[0].id == "issue1"
        assert issues[0].title == "Task 1"
        assert issues[0].state == "Todo"

    @pytest.mark.asyncio
    async def test_get_issues_with_project_filter(self, linear_client, mock_httpx_client):
        """Test fetching issues with project filter."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"issues": {"nodes": []}}}
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_response

        await linear_client.get_issues(project_id="proj1")

        call_args = mock_httpx_client.post.call_args
        assert call_args[1]["json"]["variables"]["projectId"] == "proj1"

    @pytest.mark.asyncio
    async def test_get_issues_without_project_assignee(self, linear_client, mock_httpx_client):
        """Test fetching issues without project and assignee."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "issues": {
                    "nodes": [
                        {
                            "id": "issue1",
                            "title": "Task 1",
                            "description": None,
                            "state": {"name": "Todo"},
                            "priority": 0,
                            "project": None,
                            "assignee": None,
                        }
                    ]
                }
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_response

        issues = await linear_client.get_issues()

        assert issues[0].project_id is None
        assert issues[0].assignee_id is None


class TestCreateIssue:
    """Test create_issue method."""

    @pytest.mark.asyncio
    async def test_create_issue_success(self, linear_client, mock_httpx_client):
        """Test creating issue successfully."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "issueCreate": {
                    "success": True,
                    "issue": {
                        "id": "issue1",
                        "title": "New Task",
                        "description": "Test task",
                        "state": {"name": "Todo"},
                        "priority": 2,
                        "project": {"id": "proj1"},
                        "assignee": {"id": "user1"},
                    },
                }
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_response

        issue = await linear_client.create_issue(
            title="New Task",
            team_id="team1",
            description="Test task",
            priority=2,
            assignee_id="user1",
        )

        assert issue.id == "issue1"
        assert issue.title == "New Task"
        assert issue.priority == 2

    @pytest.mark.asyncio
    async def test_create_issue_minimal(self, linear_client, mock_httpx_client):
        """Test creating issue with minimal data."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "issueCreate": {
                    "success": True,
                    "issue": {
                        "id": "issue1",
                        "title": "New Task",
                        "description": None,
                        "state": {"name": "Todo"},
                        "priority": 0,
                        "project": None,
                        "assignee": None,
                    },
                }
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_response

        issue = await linear_client.create_issue(
            title="New Task",
            team_id="team1",
        )

        assert issue.description is None
        assert issue.project_id is None
        assert issue.assignee_id is None

    @pytest.mark.asyncio
    async def test_create_issue_failure(self, linear_client, mock_httpx_client):
        """Test creating issue failure."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {"issueCreate": {"success": False}}
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_response

        with pytest.raises(ValueError, match="Failed to create issue"):
            await linear_client.create_issue(
                title="New Task",
                team_id="team1",
            )
