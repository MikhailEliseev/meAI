"""Project creator service - orchestrates template rendering and Linear API calls."""

from typing import Any, Dict, List, Optional
import asyncio
from dataclasses import dataclass

from src.aim.integrations.linear.client import LinearClient, LinearProject, LinearIssue
from src.aim.templates.engine import TemplateEngine, TemplateData


@dataclass
class CreationResult:
    """Result of project creation."""
    success: bool
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    tasks_created: int = 0
    error: Optional[str] = None


class ProjectCreator:
    """Orchestrates automated project creation in Linear.

    Combines TemplateEngine (for rendering templates) and LinearClient
    (for API calls) to create complete projects with milestones, labels, and tasks.

    Example:
        async with LinearClient(api_key="...") as client:
            creator = ProjectCreator(client=client)
            result = await creator.create_project(
                template_name="project_template.yaml",
                variables={
                    "client_name": "Acme Corp",
                    "industry": "Healthcare",
                    "team_id": "team-123",
                }
            )
    """

    def __init__(
        self,
        client: LinearClient,
        template_engine: Optional[TemplateEngine] = None,
    ):
        """Initialize project creator.

        Args:
            client: Linear API client (must be in context manager)
            template_engine: Template engine (default: new instance)
        """
        self.client = client
        self.template_engine = template_engine or TemplateEngine()

    async def create_project(
        self,
        template_name: str,
        variables: Dict[str, Any],
    ) -> CreationResult:
        """Create project from template.

        Args:
            template_name: Template file name
            variables: Template variables

        Returns:
            Creation result with project ID and stats
        """
        try:
            # Step 1: Render template
            template_data = self.template_engine.render_template(
                template_name=template_name,
                variables=variables,
            )

            # Step 2: Create project in Linear
            project = await self.client.create_project(
                name=template_data.project.name,
                team_id=template_data.project.team_id,
                description=template_data.project.description,
                state=template_data.project.state,
            )

            # Step 3: Create tasks
            tasks_created = 0
            for task_template in template_data.tasks:
                try:
                    await self.client.create_issue(
                        title=task_template.title,
                        team_id=template_data.project.team_id,
                        description=task_template.description,
                        project_id=project.id,
                        priority=task_template.priority,
                    )
                    tasks_created += 1
                except Exception as e:
                    # Log error but continue with other tasks
                    print(f"Warning: Failed to create task '{task_template.title}': {e}")

            return CreationResult(
                success=True,
                project_id=project.id,
                project_name=project.name,
                tasks_created=tasks_created,
            )

        except Exception as e:
            return CreationResult(
                success=False,
                error=str(e),
            )

    async def create_project_with_rollback(
        self,
        template_name: str,
        variables: Dict[str, Any],
    ) -> CreationResult:
        """Create project with automatic rollback on failure.

        If any step fails after project creation, attempts to delete the project.

        Args:
            template_name: Template file name
            variables: Template variables

        Returns:
            Creation result
        """
        project_id = None

        try:
            # Step 1: Render template
            template_data = self.template_engine.render_template(
                template_name=template_name,
                variables=variables,
            )

            # Step 2: Create project
            project = await self.client.create_project(
                name=template_data.project.name,
                team_id=template_data.project.team_id,
                description=template_data.project.description,
                state=template_data.project.state,
            )
            project_id = project.id

            # Step 3: Create tasks
            tasks_created = 0
            failed_tasks = []

            for task_template in template_data.tasks:
                try:
                    await self.client.create_issue(
                        title=task_template.title,
                        team_id=template_data.project.team_id,
                        description=task_template.description,
                        project_id=project.id,
                        priority=task_template.priority,
                    )
                    tasks_created += 1
                except Exception as e:
                    failed_tasks.append((task_template.title, str(e)))

            # If too many tasks failed, consider it a failure
            if len(failed_tasks) > len(template_data.tasks) * 0.5:
                raise ValueError(
                    f"Too many tasks failed ({len(failed_tasks)}/{len(template_data.tasks)})"
                )

            return CreationResult(
                success=True,
                project_id=project.id,
                project_name=project.name,
                tasks_created=tasks_created,
            )

        except Exception as e:
            # Rollback: try to delete project if it was created
            if project_id:
                try:
                    # Note: Linear API doesn't have delete project mutation
                    # In production, would mark as "canceled" instead
                    await self.client.update_project(
                        project_id=project_id,
                        state="canceled",
                    )
                except Exception as rollback_error:
                    print(f"Rollback failed: {rollback_error}")

            return CreationResult(
                success=False,
                error=str(e),
            )

    async def validate_before_create(
        self,
        template_name: str,
        variables: Dict[str, Any],
    ) -> tuple[bool, List[str]]:
        """Validate template and variables before creation.

        Args:
            template_name: Template file name
            variables: Template variables

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check template exists
        templates = self.template_engine.list_templates()
        if template_name not in templates:
            errors.append(f"Template not found: {template_name}")
            return False, errors

        # Check required variables
        missing_vars = self.template_engine.validate_variables(
            template_name=template_name,
            variables=variables,
        )
        if missing_vars:
            errors.append(f"Missing variables: {', '.join(missing_vars)}")

        # Try to render template
        try:
            self.template_engine.render_template(
                template_name=template_name,
                variables=variables,
            )
        except Exception as e:
            errors.append(f"Template rendering failed: {e}")

        return len(errors) == 0, errors
