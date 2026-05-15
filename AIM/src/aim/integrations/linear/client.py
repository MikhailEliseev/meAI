"""Linear GraphQL API client.

Based on research from github-project-llm-management pattern.
Implements GraphQL-based project sync for automated project creation.
"""

import asyncio
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel, ConfigDict, Field


class LinearProject(BaseModel):
    """Linear project model."""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    description: Optional[str] = None
    state: str
    progress: float = 0.0
    team_id: str = Field(alias="teamId")


class LinearIssue(BaseModel):
    """Linear issue (task) model."""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    title: str
    description: Optional[str] = None
    state: str
    priority: int = 0
    project_id: Optional[str] = Field(None, alias="projectId")
    assignee_id: Optional[str] = Field(None, alias="assigneeId")


class LinearClient:
    """Linear GraphQL API client.

    Provides CRUD operations for projects and issues.
    Implements retry logic and error handling.

    Example:
        client = LinearClient(api_key="lin_api_...")
        project = await client.create_project(
            name="Client SEO Audit",
            team_id="team-123",
            description="Automated project from template"
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
        """
        self.api_url = api_url
        self.headers = {
            "Authorization": api_key,
            "Content-Type": "application/json",
        }
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None

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

    async def _execute_query(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
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

    async def get_projects(
        self,
        team_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[LinearProject]:
        """Fetch projects.

        Args:
            team_id: Filter by team ID (optional)
            limit: Max projects to return

        Returns:
            List of projects
        """
        query = """
        query GetProjects($teamId: String, $first: Int) {
          projects(
            filter: { team: { id: { eq: $teamId } } }
            first: $first
          ) {
            nodes {
              id
              name
              description
              state
              progress
              team { id }
            }
          }
        }
        """

        variables = {"first": limit}
        if team_id:
            variables["teamId"] = team_id

        data = await self._execute_query(query, variables)
        nodes = data.get("projects", {}).get("nodes", [])

        return [
            LinearProject(
                id=node["id"],
                name=node["name"],
                description=node.get("description"),
                state=node["state"],
                progress=node.get("progress", 0.0),
                teamId=node["team"]["id"],
            )
            for node in nodes
        ]

    async def get_project(self, project_id: str) -> Optional[LinearProject]:
        """Fetch single project by ID.

        Args:
            project_id: Project ID

        Returns:
            Project or None if not found
        """
        query = """
        query GetProject($id: String!) {
          project(id: $id) {
            id
            name
            description
            state
            progress
            team { id }
          }
        }
        """

        data = await self._execute_query(query, {"id": project_id})
        node = data.get("project")

        if not node:
            return None

        return LinearProject(
            id=node["id"],
            name=node["name"],
            description=node.get("description"),
            state=node["state"],
            progress=node.get("progress", 0.0),
            teamId=node["team"]["id"],
        )
    async def create_project(
        self,
        name: str,
        team_id: str,
        description: Optional[str] = None,
        state: str = "planned",
    ) -> LinearProject:
        """Create new project.

        Args:
            name: Project name
            team_id: Team ID
            description: Project description (optional)
            state: Project state (planned, started, completed, canceled)

        Returns:
            Created project
        """
        query = """
        mutation CreateProject($input: ProjectCreateInput!) {
          projectCreate(input: $input) {
            success
            project {
              id
              name
              description
              state
              progress
              team { id }
            }
          }
        }
        """

        variables = {
            "input": {
                "name": name,
                "teamId": team_id,
                "state": state,
            }
        }
        if description:
            variables["input"]["description"] = description

        data = await self._execute_query(query, variables)
        result = data.get("projectCreate", {})

        if not result.get("success"):
            raise ValueError("Failed to create project")

        node = result.get("project")
        return LinearProject(
            id=node["id"],
            name=node["name"],
            description=node.get("description"),
            state=node["state"],
            progress=node.get("progress", 0.0),
            teamId=node["team"]["id"],
        )

    async def update_project(
        self,
        project_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        state: Optional[str] = None,
        progress: Optional[float] = None,
    ) -> LinearProject:
        """Update existing project.

        Args:
            project_id: Project ID
            name: New name (optional)
            description: New description (optional)
            state: New state (optional)
            progress: New progress 0.0-1.0 (optional)

        Returns:
            Updated project
        """
        query = """
        mutation UpdateProject($id: String!, $input: ProjectUpdateInput!) {
          projectUpdate(id: $id, input: $input) {
            success
            project {
              id
              name
              description
              state
              progress
              team { id }
            }
          }
        }
        """

        update_input = {}
        if name is not None:
            update_input["name"] = name
        if description is not None:
            update_input["description"] = description
        if state is not None:
            update_input["state"] = state
        if progress is not None:
            update_input["progress"] = progress

        variables = {"id": project_id, "input": update_input}

        data = await self._execute_query(query, variables)
        result = data.get("projectUpdate", {})

        if not result.get("success"):
            raise ValueError("Failed to update project")

        node = result.get("project")
        return LinearProject(
            id=node["id"],
            name=node["name"],
            description=node.get("description"),
            state=node["state"],
            progress=node.get("progress", 0.0),
            teamId=node["team"]["id"],
        )

    async def get_issues(
        self,
        project_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[LinearIssue]:
        """Fetch issues (tasks).

        Args:
            project_id: Filter by project ID (optional)
            limit: Max issues to return

        Returns:
            List of issues
        """
        query = """
        query GetIssues($projectId: String, $first: Int) {
          issues(
            filter: { project: { id: { eq: $projectId } } }
            first: $first
          ) {
            nodes {
              id
              title
              description
              state { name }
              priority
              project { id }
              assignee { id }
            }
          }
        }
        """

        variables = {"first": limit}
        if project_id:
            variables["projectId"] = project_id

        data = await self._execute_query(query, variables)
        nodes = data.get("issues", {}).get("nodes", [])

        return [
            LinearIssue(
                id=node["id"],
                title=node["title"],
                description=node.get("description"),
                state=node["state"]["name"],
                priority=node.get("priority", 0),
                projectId=node.get("project", {}).get("id") if node.get("project") else None,
                assigneeId=node.get("assignee", {}).get("id") if node.get("assignee") else None,
            )
            for node in nodes
        ]

    async def create_issue(
        self,
        title: str,
        team_id: str,
        description: Optional[str] = None,
        project_id: Optional[str] = None,
        priority: int = 0,
        assignee_id: Optional[str] = None,
    ) -> LinearIssue:
        """Create new issue (task).

        Args:
            title: Issue title
            team_id: Team ID
            description: Issue description (optional)
            project_id: Project ID (optional)
            priority: Priority 0-4 (0=none, 1=urgent, 2=high, 3=medium, 4=low)
            assignee_id: Assignee user ID (optional)

        Returns:
            Created issue
        """
        query = """
        mutation CreateIssue($input: IssueCreateInput!) {
          issueCreate(input: $input) {
            success
            issue {
              id
              title
              description
              state { name }
              priority
              project { id }
              assignee { id }
            }
          }
        }
        """

        variables = {
            "input": {
                "title": title,
                "teamId": team_id,
                "priority": priority,
            }
        }
        if description:
            variables["input"]["description"] = description
        if project_id:
            variables["input"]["projectId"] = project_id
        if assignee_id:
            variables["input"]["assigneeId"] = assignee_id

        data = await self._execute_query(query, variables)
        result = data.get("issueCreate", {})

        if not result.get("success"):
            raise ValueError("Failed to create issue")

        node = result.get("issue")
        return LinearIssue(
            id=node["id"],
            title=node["title"],
            description=node.get("description"),
            state=node["state"]["name"],
            priority=node.get("priority", 0),
            projectId=node.get("project", {}).get("id") if node.get("project") else None,
            assigneeId=node.get("assignee", {}).get("id") if node.get("assignee") else None,
        )
