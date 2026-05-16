"""Linear GraphQL API client for lead management

Implements GraphQL API for:
- Creating issues (tasks) for Hot/Warm leads
- Managing workflow states
- Assigning tasks to sales team
- Syncing task status

Part of: Phase 11 Sprint 2 - Task 2.3
"""

import asyncio
from typing import Any

import httpx

from AIM.src.aim.integrations.linear.schemas import (
    LinearCreateIssueInput,
    LinearIssue,
    LinearLabel,
    LinearProject,
    LinearTeam,
    LinearUpdateIssueInput,
    LinearUser,
    LinearWorkflowState,
)


class LinearClient:
    """Linear GraphQL API client for lead management

    Provides operations for:
    - Creating issues (tasks) for leads
    - Managing workflow states
    - Assigning tasks to team members
    - Fetching teams, users, labels

    Example:
        async with LinearClient(api_key="lin_api_...") as client:
            issue = await client.create_issue(
                team_id="team_abc123",
                title="[Hot] Plastic Surgery Lead - Score 87",
                description="Lead details...",
                priority=1,
                label_ids=["label_hot123"],
                assignee_id="user_abc123",
            )
    """

    def __init__(
        self,
        api_key: str,
        api_url: str = "https://api.linear.app/graphql",
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """Initialize Linear client.

        Args:
            api_key: Linear API key (starts with lin_api_)
            api_url: Linear GraphQL endpoint
            timeout: Request timeout in seconds
            max_retries: Max retry attempts on failure

        Raises:
            ValueError: If api_key is empty
        """
        if not api_key:
            raise ValueError("LINEAR_API_KEY is required")

        self.api_key = api_key
        self.base_url = api_url
        self.api_url = api_url
        self.headers = {
            "Authorization": api_key,
            "Content-Type": "application/json",
        }
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            headers=self.headers,
            timeout=self.timeout,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _execute_query(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute GraphQL query with retry logic.

        Args:
            query: GraphQL query string
            variables: Query variables

        Returns:
            Query result data

        Raises:
            httpx.HTTPError: On request failure after retries
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = await self._client.post(
                    self.api_url,
                    json=payload,
                )
                response.raise_for_status()

                result = response.json()

                # Check for GraphQL errors
                if "errors" in result:
                    error_msg = "; ".join(e.get("message", "") for e in result["errors"])
                    raise ValueError(f"GraphQL errors: {error_msg}")

                return result.get("data", {})

            except (httpx.HTTPError, ValueError) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    await asyncio.sleep(2 ** attempt)
                continue

        raise last_error or RuntimeError("Query failed after retries")

    async def list_teams(self) -> list[LinearTeam]:
        """Fetch all teams

        Returns:
            List of teams
        """
        query = """
        query ListTeams {
          teams {
            nodes {
              id
              name
              key
              description
            }
          }
        }
        """

        data = await self._execute_query(query)
        nodes = data.get("teams", {}).get("nodes", [])

        return [
            LinearTeam(
                id=node["id"],
                name=node["name"],
                key=node["key"],
                description=node.get("description"),
            )
            for node in nodes
        ]

    async def list_workflow_states(self, team_id: str) -> list[LinearWorkflowState]:
        """Fetch workflow states for team

        Args:
            team_id: Team ID

        Returns:
            List of workflow states
        """
        query = """
        query ListWorkflowStates($teamId: String!) {
          team(id: $teamId) {
            states {
              nodes {
                id
                name
                type
                color
                position
              }
            }
          }
        }
        """

        data = await self._execute_query(query, {"teamId": team_id})
        nodes = data.get("team", {}).get("states", {}).get("nodes", [])

        return [
            LinearWorkflowState(
                id=node["id"],
                name=node["name"],
                type=node["type"],
                color=node.get("color"),
                position=node.get("position"),
            )
            for node in nodes
        ]

    async def list_users(self) -> list[LinearUser]:
        """Fetch all active users

        Returns:
            List of users
        """
        query = """
        query ListUsers {
          users {
            nodes {
              id
              name
              email
              avatarUrl
              active
            }
          }
        }
        """

        data = await self._execute_query(query)
        nodes = data.get("users", {}).get("nodes", [])

        return [
            LinearUser(
                id=node["id"],
                name=node["name"],
                email=node["email"],
                avatar_url=node.get("avatarUrl"),
                active=node.get("active", True),
            )
            for node in nodes
            if node.get("active", True)
        ]

    async def list_labels(self, team_id: str) -> list[LinearLabel]:
        """Fetch labels for team

        Args:
            team_id: Team ID

        Returns:
            List of labels
        """
        query = """
        query ListLabels($teamId: String!) {
          team(id: $teamId) {
            labels {
              nodes {
                id
                name
                color
                description
              }
            }
          }
        }
        """

        data = await self._execute_query(query, {"teamId": team_id})
        nodes = data.get("team", {}).get("labels", {}).get("nodes", [])

        return [
            LinearLabel(
                id=node["id"],
                name=node["name"],
                color=node["color"],
                description=node.get("description"),
            )
            for node in nodes
        ]

    async def create_issue(
        self,
        team_id: str,
        title: str,
        description: str | None = None,
        priority: int = 0,
        label_ids: list[str] | None = None,
        assignee_id: str | None = None,
        state_id: str | None = None,
    ) -> LinearIssue:
        """Create new issue (task)

        Args:
            team_id: Team ID
            title: Issue title
            description: Issue description (markdown)
            priority: Priority (0=none, 1=urgent, 2=high, 3=medium, 4=low)
            label_ids: List of label IDs
            assignee_id: Assignee user ID
            state_id: Initial workflow state ID

        Returns:
            Created issue
        """
        query = """
        mutation CreateIssue($input: IssueCreateInput!) {
          issueCreate(input: $input) {
            success
            issue {
              id
              identifier
              title
              description
              priority
              url
              createdAt
              updatedAt
              state {
                id
                name
                type
                color
                position
              }
              assignee {
                id
                name
                email
                avatarUrl
                active
              }
              labels {
                nodes {
                  id
                  name
                  color
                  description
                }
              }
            }
          }
        }
        """

        input_data: dict[str, Any] = {
            "teamId": team_id,
            "title": title,
            "priority": priority,
        }

        if description:
            input_data["description"] = description
        if label_ids:
            input_data["labelIds"] = label_ids
        if assignee_id:
            input_data["assigneeId"] = assignee_id
        if state_id:
            input_data["stateId"] = state_id

        data = await self._execute_query(query, {"input": input_data})
        result = data.get("issueCreate", {})

        if not result.get("success"):
            raise ValueError("Failed to create issue")

        node = result["issue"]
        return LinearIssue(
            id=node["id"],
            identifier=node["identifier"],
            title=node["title"],
            description=node.get("description"),
            priority=node["priority"],
            state=LinearWorkflowState(
                id=node["state"]["id"],
                name=node["state"]["name"],
                type=node["state"]["type"],
                color=node["state"].get("color"),
                position=node["state"].get("position"),
            ),
            assignee=LinearUser(
                id=node["assignee"]["id"],
                name=node["assignee"]["name"],
                email=node["assignee"]["email"],
                avatar_url=node["assignee"].get("avatarUrl"),
                active=node["assignee"].get("active", True),
            )
            if node.get("assignee")
            else None,
            labels=[
                LinearLabel(
                    id=label["id"],
                    name=label["name"],
                    color=label["color"],
                    description=label.get("description"),
                )
                for label in node.get("labels", {}).get("nodes", [])
            ],
            url=node["url"],
            created_at=node["createdAt"],
            updated_at=node["updatedAt"],
        )

    async def update_issue(
        self,
        issue_id: str,
        state_id: str | None = None,
        assignee_id: str | None = None,
        priority: int | None = None,
        title: str | None = None,
        description: str | None = None,
    ) -> LinearIssue:
        """Update existing issue

        Args:
            issue_id: Issue ID
            state_id: New workflow state ID
            assignee_id: New assignee user ID
            priority: New priority
            title: New title
            description: New description

        Returns:
            Updated issue
        """
        query = """
        mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
          issueUpdate(id: $id, input: $input) {
            success
            issue {
              id
              identifier
              title
              description
              priority
              url
              createdAt
              updatedAt
              state {
                id
                name
                type
                color
                position
              }
              assignee {
                id
                name
                email
                avatarUrl
                active
              }
              labels {
                nodes {
                  id
                  name
                  color
                  description
                }
              }
            }
          }
        }
        """

        input_data: dict[str, Any] = {}
        if state_id is not None:
            input_data["stateId"] = state_id
        if assignee_id is not None:
            input_data["assigneeId"] = assignee_id
        if priority is not None:
            input_data["priority"] = priority
        if title is not None:
            input_data["title"] = title
        if description is not None:
            input_data["description"] = description

        data = await self._execute_query(query, {"id": issue_id, "input": input_data})
        result = data.get("issueUpdate", {})

        if not result.get("success"):
            raise ValueError("Failed to update issue")

        node = result["issue"]
        return LinearIssue(
            id=node["id"],
            identifier=node["identifier"],
            title=node["title"],
            description=node.get("description"),
            priority=node["priority"],
            state=LinearWorkflowState(
                id=node["state"]["id"],
                name=node["state"]["name"],
                type=node["state"]["type"],
                color=node["state"].get("color"),
                position=node["state"].get("position"),
            ),
            assignee=LinearUser(
                id=node["assignee"]["id"],
                name=node["assignee"]["name"],
                email=node["assignee"]["email"],
                avatar_url=node["assignee"].get("avatarUrl"),
                active=node["assignee"].get("active", True),
            )
            if node.get("assignee")
            else None,
            labels=[
                LinearLabel(
                    id=label["id"],
                    name=label["name"],
                    color=label["color"],
                    description=label.get("description"),
                )
                for label in node.get("labels", {}).get("nodes", [])
            ],
            url=node["url"],
            created_at=node["createdAt"],
            updated_at=node["updatedAt"],
        )

    async def get_issue(self, issue_id: str) -> LinearIssue | None:
        """Fetch single issue by ID

        Args:
            issue_id: Issue ID

        Returns:
            Issue or None if not found
        """
        query = """
        query GetIssue($id: String!) {
          issue(id: $id) {
            id
            identifier
            title
            description
            priority
            url
            createdAt
            updatedAt
            state {
              id
              name
              type
              color
              position
            }
            assignee {
              id
              name
              email
              avatarUrl
              active
            }
            labels {
              nodes {
                id
                name
                color
                description
              }
            }
          }
        }
        """

        data = await self._execute_query(query, {"id": issue_id})
        node = data.get("issue")

        if not node:
            return None

        return LinearIssue(
            id=node["id"],
            identifier=node["identifier"],
            title=node["title"],
            description=node.get("description"),
            priority=node["priority"],
            state=LinearWorkflowState(
                id=node["state"]["id"],
                name=node["state"]["name"],
                type=node["state"]["type"],
                color=node["state"].get("color"),
                position=node["state"].get("position"),
            ),
            assignee=LinearUser(
                id=node["assignee"]["id"],
                name=node["assignee"]["name"],
                email=node["assignee"]["email"],
                avatar_url=node["assignee"].get("avatarUrl"),
                active=node["assignee"].get("active", True),
            )
            if node.get("assignee")
            else None,
            labels=[
                LinearLabel(
                    id=label["id"],
                    name=label["name"],
                    color=label["color"],
                    description=label.get("description"),
                )
                for label in node.get("labels", {}).get("nodes", [])
            ],
            url=node["url"],
            created_at=node["createdAt"],
            updated_at=node["updatedAt"],
        )
