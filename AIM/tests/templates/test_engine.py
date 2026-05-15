"""Tests for template engine."""

import pytest
from pathlib import Path
import sys

# Add AIM/src to path
aim_src = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(aim_src))

from aim.templates.engine import (
    TemplateEngine,
    TemplateData,
    ProjectTemplate,
    MilestoneTemplate,
    LabelTemplate,
    TaskTemplate,
)


class TestTemplateEngine:
    """Test TemplateEngine class."""

    def test_init_default_templates_dir(self):
        """Test initialization with default templates directory."""
        engine = TemplateEngine()

        assert engine.templates_dir.exists()
        assert engine.templates_dir.name == "schemas"

    def test_init_custom_templates_dir(self, tmp_path):
        """Test initialization with custom templates directory."""
        custom_dir = tmp_path / "custom_templates"
        custom_dir.mkdir()

        engine = TemplateEngine(templates_dir=custom_dir)

        assert engine.templates_dir == custom_dir

    def test_list_templates(self):
        """Test listing available templates."""
        engine = TemplateEngine()

        templates = engine.list_templates()

        assert "project_template.yaml" in templates

    def test_render_template_success(self):
        """Test rendering template with valid variables."""
        engine = TemplateEngine()

        variables = {
            "client_name": "Acme Corp",
            "industry": "Healthcare",
            "start_date": "2026-05-15",
            "team_id": "team-123",
        }

        data = engine.render_template("project_template.yaml", variables)

        assert isinstance(data, TemplateData)
        assert "Acme Corp" in data.project.name
        assert "Healthcare" in data.project.description
        assert data.project.team_id == "team-123"
        assert len(data.milestones) == 3
        assert len(data.labels) == 7
        assert len(data.tasks) == 15

    def test_render_template_not_found(self):
        """Test rendering non-existent template."""
        engine = TemplateEngine()

        with pytest.raises(FileNotFoundError, match="Template not found"):
            engine.render_template("nonexistent.yaml", {})

    def test_validate_variables_all_provided(self):
        """Test variable validation with all variables provided."""
        engine = TemplateEngine()

        variables = {
            "client_name": "Acme Corp",
            "industry": "Healthcare",
            "start_date": "2026-05-15",
            "team_id": "team-123",
        }

        missing = engine.validate_variables("project_template.yaml", variables)

        assert missing == []

    def test_validate_variables_missing(self):
        """Test variable validation with missing variables."""
        engine = TemplateEngine()

        variables = {
            "client_name": "Acme Corp",
        }

        missing = engine.validate_variables("project_template.yaml", variables)

        assert "industry" in missing
        assert "team_id" in missing


class TestProjectTemplate:
    """Test ProjectTemplate model."""

    def test_project_template_valid(self):
        """Test creating valid project template."""
        project = ProjectTemplate(
            name="Test Project",
            description="Test description",
            state="planned",
            teamId="team-123",
        )

        assert project.name == "Test Project"
        assert project.team_id == "team-123"


class TestMilestoneTemplate:
    """Test MilestoneTemplate model."""

    def test_milestone_template_valid(self):
        """Test creating valid milestone template."""
        milestone = MilestoneTemplate(
            name="Phase 1",
            description="First phase",
            durationWeeks=2,
        )

        assert milestone.name == "Phase 1"
        assert milestone.duration_weeks == 2


class TestLabelTemplate:
    """Test LabelTemplate model."""

    def test_label_template_valid(self):
        """Test creating valid label template."""
        label = LabelTemplate(
            name="priority:high",
            color="#FF0000",
        )

        assert label.name == "priority:high"
        assert label.color == "#FF0000"

    def test_label_template_invalid_color(self):
        """Test creating label with invalid color."""
        with pytest.raises(ValueError, match="Color must be hex format"):
            LabelTemplate(
                name="priority:high",
                color="red",
            )


class TestTaskTemplate:
    """Test TaskTemplate model."""

    def test_task_template_valid(self):
        """Test creating valid task template."""
        task = TaskTemplate(
            title="Test Task",
            description="Test description",
            milestone=0,
            priority=1,
            labels=["priority:high", "type:seo"],
        )

        assert task.title == "Test Task"
        assert task.milestone == 0
        assert len(task.labels) == 2
