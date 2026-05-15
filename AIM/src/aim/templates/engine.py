"""Template engine for project creation with Jinja2 and YAML."""

from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from jinja2 import Environment, FileSystemLoader, Template
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectTemplate(BaseModel):
    """Project template model."""
    model_config = ConfigDict(populate_by_name=True)

    name: str
    description: str
    state: str = "planned"
    team_id: str = Field(alias="teamId")


class MilestoneTemplate(BaseModel):
    """Milestone template model."""
    model_config = ConfigDict(populate_by_name=True)

    name: str
    description: str
    duration_weeks: int = Field(alias="durationWeeks")


class LabelTemplate(BaseModel):
    """Label template model."""
    model_config = ConfigDict(populate_by_name=True)

    name: str
    color: str

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str) -> str:
        """Validate hex color format."""
        if not v.startswith("#") or len(v) != 7:
            raise ValueError("Color must be hex format (#RRGGBB)")
        return v


class TaskTemplate(BaseModel):
    """Task template model."""
    model_config = ConfigDict(populate_by_name=True)

    title: str
    description: str
    milestone: int
    priority: int = 0
    labels: List[str] = []


class TemplateData(BaseModel):
    """Complete template data model."""
    model_config = ConfigDict(populate_by_name=True)

    project: ProjectTemplate
    milestones: List[MilestoneTemplate]
    labels: List[LabelTemplate]
    tasks: List[TaskTemplate]


class TemplateEngine:
    """Template engine for rendering project templates.

    Uses Jinja2 for variable substitution and YAML for template storage.

    Example:
        engine = TemplateEngine()
        data = engine.render_template(
            template_name="project_template.yaml",
            variables={
                "client_name": "Acme Corp",
                "industry": "Healthcare",
                "start_date": "2026-05-15",
                "team_id": "team-123",
            }
        )
    """

    def __init__(
        self,
        templates_dir: Optional[Path] = None,
    ):
        """Initialize template engine.

        Args:
            templates_dir: Path to templates directory (default: schemas/)
        """
        if templates_dir is None:
            templates_dir = Path(__file__).parent / "schemas"

        self.templates_dir = templates_dir
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=False,
        )

    def render_template(
        self,
        template_name: str,
        variables: Dict[str, Any],
    ) -> TemplateData:
        """Render template with variables.

        Args:
            template_name: Template file name (e.g., "project_template.yaml")
            variables: Template variables (client_name, industry, etc.)

        Returns:
            Rendered template data

        Raises:
            FileNotFoundError: Template not found
            ValueError: Invalid template format or missing variables
        """
        # Load template
        template_path = self.templates_dir / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_name}")

        # Render with Jinja2
        template = self.jinja_env.get_template(template_name)
        rendered_yaml = template.render(**variables)

        # Parse YAML
        try:
            data = yaml.safe_load(rendered_yaml)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in template: {e}")

        # Validate with Pydantic
        try:
            return TemplateData(**data)
        except Exception as e:
            raise ValueError(f"Invalid template data: {e}")

    def validate_variables(
        self,
        template_name: str,
        variables: Dict[str, Any],
    ) -> List[str]:
        """Validate that all required variables are provided.

        Args:
            template_name: Template file name
            variables: Provided variables

        Returns:
            List of missing variable names (empty if all provided)
        """
        # Load template
        template_path = self.templates_dir / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_name}")

        # Get template source
        with open(template_path, "r") as f:
            template_source = f.read()

        # Parse template to find variables
        template = Template(template_source)
        required_vars = set(template.module.__dict__.get("__jinja2_template_vars__", []))

        # Find undefined variables (simple regex approach)
        import re
        var_pattern = r"\{\{\s*(\w+)\s*\}\}"
        found_vars = set(re.findall(var_pattern, template_source))

        # Check which are missing
        provided_vars = set(variables.keys())
        missing_vars = found_vars - provided_vars

        return sorted(missing_vars)

    def list_templates(self) -> List[str]:
        """List available templates.

        Returns:
            List of template file names
        """
        if not self.templates_dir.exists():
            return []

        return [
            f.name
            for f in self.templates_dir.iterdir()
            if f.is_file() and f.suffix in [".yaml", ".yml"]
        ]
