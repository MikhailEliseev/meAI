"""Tests for Linear GraphQL API client - only implemented methods."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

import sys
from pathlib import Path

# Add AIM/src to path
aim_src = Path(__file__).parent.parent.parent.parent / "src"
sys.path.insert(0, str(aim_src))

from src.aim.integrations.linear.client import LinearClient
from src.aim.integrations.linear.schemas import LinearIssue, LinearTeam, LinearWorkflowState, LinearUser, LinearLabel


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
        async with LinearClient(api_key="test_key") as client:
            yield client


class TestLinearClientInit:
    """Test LinearClient initialization."""

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        client = LinearClient(api_key="test_key")
        assert client.api_key == "test_key"
        assert client.base_url == "https://api.linear.app/graphql"

    def test_init_without_api_key(self):
        """Test initialization without API key raises error."""
        with pytest.raises(ValueError, match="LINEAR_API_KEY"):
            LinearClient(api_key="")


class TestLinearClientContextManager:
    """Test LinearClient context manager."""

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_httpx_client):
        """Test using LinearClient as context manager."""
        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            async with LinearClient(api_key="test_key") as client:
                assert client is not None

            mock_httpx_client.aclose.assert_called_once()


class TestListTeams:
    """Test list_teams method."""

    @pytest.mark.asyncio
    async def test_list_teams_success(self, linear_client, mock_httpx_client):
        """Test fetching teams successfully."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "teams": {
                    "nodes": [
                        {
                            "id": "team1",
                            "name": "Engineering",
                            "key": "ENG",
                        }
                    ]
                }
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_response

        teams = await linear_client.list_teams()

        assert len(teams) == 1
        assert teams[0].id == "team1"
        assert teams[0].name == "Engineering"
        assert teams[0].key == "ENG"


class TestListWorkflowStates:
    """Test list_workflow_states method."""

    @pytest.mark.asyncio
    async def test_list_workflow_states_success(self, linear_client, mock_httpx_client):
        """Test fetching workflow states successfully."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "team": {
                    "states": {
                        "nodes": [
                            {
                                "id": "state1",
                                "name": "Todo",
                                "type": "unstarted",
                                "color": "#e2e2e2",
                                "position": 0,
                            }
                        ]
                    }
                }
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_response

        states = await linear_client.list_workflow_states("team1")

        assert len(states) == 1
        assert states[0].id == "state1"
        assert states[0].name == "Todo"
        assert states[0].type == "unstarted"


class TestListUsers:
    """Test list_users method."""

    @pytest.mark.asyncio
    async def test_list_users_success(self, linear_client, mock_httpx_client):
        """Test fetching users successfully."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "users": {
                    "nodes": [
                        {
                            "id": "user1",
                            "name": "John Doe",
                            "email": "john@example.com",
                            "avatarUrl": "https://example.com/avatar.jpg",
                            "active": True,
                        }
                    ]
                }
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_response

        users = await linear_client.list_users()

        assert len(users) == 1
        assert users[0].id == "user1"
        assert users[0].name == "John Doe"
        assert users[0].email == "john@example.com"


class TestListLabels:
    """Test list_labels method."""

    @pytest.mark.asyncio
    async def test_list_labels_success(self, linear_client, mock_httpx_client):
        """Test fetching labels successfully."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "team": {
                    "labels": {
                        "nodes": [
                            {
                                "id": "label1",
                                "name": "Bug",
                                "color": "#ff0000",
                            }
                        ]
                    }
                }
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_response

        labels = await linear_client.list_labels("team1")

        assert len(labels) == 1
        assert labels[0].id == "label1"
        assert labels[0].name == "Bug"
        assert labels[0].color == "#ff0000"


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
                        "identifier": "ENG-123",
                        "title": "New Task",
                        "description": "Test task",
                        "url": "https://linear.app/team/issue/ENG-123",
                        "state": {
                            "id": "state1",
                            "name": "Todo",
                            "type": "unstarted",
                            "color": "#e2e2e2",
                            "position": 0,
                        },
                        "priority": 2,
                        "assignee": {
                            "id": "user1",
                            "name": "John Doe",
                            "email": "john@example.com",
                            "avatarUrl": "https://example.com/avatar.jpg",
                            "active": True,
                        },
                        "labels": {"nodes": []},
                        "createdAt": "2024-01-01T00:00:00Z",
                        "updatedAt": "2024-01-01T00:00:00Z",
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
        assert issue.identifier == "ENG-123"
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
                        "identifier": "ENG-124",
                        "title": "New Task",
                        "description": None,
                        "url": "https://linear.app/team/issue/ENG-124",
                        "state": {
                            "id": "state1",
                            "name": "Todo",
                            "type": "unstarted",
                            "color": "#e2e2e2",
                            "position": 0,
                        },
                        "priority": 0,
                        "assignee": None,
                        "labels": {"nodes": []},
                        "createdAt": "2024-01-01T00:00:00Z",
                        "updatedAt": "2024-01-01T00:00:00Z",
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
        assert issue.assignee is None

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


class TestUpdateIssue:
    """Test update_issue method."""

    @pytest.mark.asyncio
    async def test_update_issue_success(self, linear_client, mock_httpx_client):
        """Test updating issue successfully."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "issueUpdate": {
                    "success": True,
                    "issue": {
                        "id": "issue1",
                        "identifier": "ENG-123",
                        "title": "Updated Task",
                        "description": "Updated description",
                        "url": "https://linear.app/team/issue/ENG-123",
                        "state": {
                            "id": "state2",
                            "name": "In Progress",
                            "type": "started",
                            "color": "#f2c94c",
                            "position": 1,
                        },
                        "priority": 1,
                        "assignee": {
                            "id": "user2",
                            "name": "Jane Doe",
                            "email": "jane@example.com",
                            "avatarUrl": "https://example.com/avatar2.jpg",
                            "active": True,
                        },
                        "labels": {"nodes": []},
                        "createdAt": "2024-01-01T00:00:00Z",
                        "updatedAt": "2024-01-02T00:00:00Z",
                    },
                }
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_response

        issue = await linear_client.update_issue(
            issue_id="issue1",
            title="Updated Task",
            description="Updated description",
            state_id="state2",
            priority=1,
            assignee_id="user2",
        )

        assert issue.title == "Updated Task"
        assert issue.state.name == "In Progress"
        assert issue.priority == 1

    @pytest.mark.asyncio
    async def test_update_issue_partial(self, linear_client, mock_httpx_client):
        """Test updating issue with partial data."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "issueUpdate": {
                    "success": True,
                    "issue": {
                        "id": "issue1",
                        "identifier": "ENG-123",
                        "title": "Task",
                        "description": "Description",
                        "url": "https://linear.app/team/issue/ENG-123",
                        "state": {
                            "id": "state3",
                            "name": "Done",
                            "type": "completed",
                            "color": "#5e6ad2",
                            "position": 2,
                        },
                        "priority": 0,
                        "assignee": None,
                        "labels": {"nodes": []},
                        "createdAt": "2024-01-01T00:00:00Z",
                        "updatedAt": "2024-01-03T00:00:00Z",
                    },
                }
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_response

        issue = await linear_client.update_issue(
            issue_id="issue1",
            state_id="state3",
        )

        assert issue.state.name == "Done"

    @pytest.mark.asyncio
    async def test_update_issue_failure(self, linear_client, mock_httpx_client):
        """Test updating issue failure."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {"issueUpdate": {"success": False}}
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_response

        with pytest.raises(ValueError, match="Failed to update issue"):
            await linear_client.update_issue(
                issue_id="issue1",
                title="Updated Task",
            )


class TestGetIssue:
    """Test get_issue method."""

    @pytest.mark.asyncio
    async def test_get_issue_success(self, linear_client, mock_httpx_client):
        """Test fetching single issue successfully."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "issue": {
                    "id": "issue1",
                    "identifier": "ENG-123",
                    "title": "Task 1",
                    "description": "Test task",
                    "url": "https://linear.app/team/issue/ENG-123",
                    "state": {
                        "id": "state1",
                        "name": "Todo",
                        "type": "unstarted",
                        "color": "#e2e2e2",
                        "position": 0,
                    },
                    "priority": 2,
                    "assignee": {
                        "id": "user1",
                        "name": "John Doe",
                        "email": "john@example.com",
                        "avatarUrl": "https://example.com/avatar.jpg",
                        "active": True,
                    },
                    "labels": {"nodes": []},
                    "createdAt": "2024-01-01T00:00:00Z",
                    "updatedAt": "2024-01-01T00:00:00Z",
                }
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_response

        issue = await linear_client.get_issue("issue1")

        assert issue is not None
        assert issue.id == "issue1"
        assert issue.identifier == "ENG-123"
        assert issue.title == "Task 1"

    @pytest.mark.asyncio
    async def test_get_issue_not_found(self, linear_client, mock_httpx_client):
        """Test fetching non-existent issue."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"issue": None}}
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_response

        issue = await linear_client.get_issue("nonexistent")

        assert issue is None
