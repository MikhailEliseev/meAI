"""
Tests for AdoptionReportGenerator.

Tests:
- Generate markdown report from adoption result
- Include skill metadata (name, source, quality score)
- Include adoption details (files created, dependencies added)
- Include integration instructions
- Handle success and failure cases
- Format report sections properly
"""

from pathlib import Path

import pytest

from AIM.src.aim.teacher.skills.skill_selector import Skill
from AIM.src.aim.teacher.adoption.full_adopter import AdoptionResult
from AIM.src.aim.teacher.adoption_report import (
    AdoptionReportGenerator,
    AdoptionReport,
)


@pytest.fixture
def generator():
    """Create AdoptionReportGenerator instance."""
    return AdoptionReportGenerator()


@pytest.fixture
def successful_adoption():
    """Create successful adoption result fixture."""
    skill = Skill(
        name="Circuit Breaker",
        description="Production-ready circuit breaker with error handling",
        code_example="async def call_api(): ...",
        quality_score=85.0,
        source_repo="https://github.com/user/repo",
        file_path="circuit_breaker.py",
    )

    result = AdoptionResult(
        success=True,
        files_created=["AIM/src/aim/utils/circuit_breaker.py"],
        dependencies_added=["pybreaker>=1.0.0"],
        code_adapted=True,
        report="Successfully adapted circuit breaker pattern",
    )

    return skill, result


@pytest.fixture
def failed_adoption():
    """Create failed adoption result fixture."""
    skill = Skill(
        name="Broken Pattern",
        description="Pattern that fails to adopt",
        code_example="invalid code",
        quality_score=30.0,
        source_repo="https://github.com/user/broken",
        file_path="broken.py",
    )

    result = AdoptionResult(
        success=False,
        error="Failed to parse code",
    )

    return skill, result


class TestReportGeneration:
    """Test report generation."""

    def test_generate_success_report(self, generator, successful_adoption):
        """Should generate report for successful adoption."""
        skill, result = successful_adoption

        report = generator.generate(skill, result)

        assert isinstance(report, AdoptionReport)
        assert report.skill_name == "Circuit Breaker"
        assert report.success is True
        assert len(report.markdown) > 0

    def test_generate_failure_report(self, generator, failed_adoption):
        """Should generate report for failed adoption."""
        skill, result = failed_adoption

        report = generator.generate(skill, result)

        assert isinstance(report, AdoptionReport)
        assert report.skill_name == "Broken Pattern"
        assert report.success is False
        assert len(report.markdown) > 0

    def test_report_includes_skill_metadata(self, generator, successful_adoption):
        """Should include skill metadata in report."""
        skill, result = successful_adoption

        report = generator.generate(skill, result)

        assert "Circuit Breaker" in report.markdown
        assert "https://github.com/user/repo" in report.markdown
        assert "85.0" in report.markdown

    def test_report_includes_adoption_details(self, generator, successful_adoption):
        """Should include adoption details in report."""
        skill, result = successful_adoption

        report = generator.generate(skill, result)

        assert "AIM/src/aim/utils/circuit_breaker.py" in report.markdown
        assert "pybreaker>=1.0.0" in report.markdown
        assert "Successfully adapted" in report.markdown

    def test_report_includes_error_for_failure(self, generator, failed_adoption):
        """Should include error message for failed adoption."""
        skill, result = failed_adoption

        report = generator.generate(skill, result)

        assert "Failed to parse code" in report.markdown
        assert "❌" in report.markdown or "FAILED" in report.markdown


class TestReportFormatting:
    """Test report formatting."""

    def test_report_has_sections(self, generator, successful_adoption):
        """Should have proper markdown sections."""
        skill, result = successful_adoption

        report = generator.generate(skill, result)

        # Check for markdown headers
        assert "##" in report.markdown or "#" in report.markdown

    def test_report_has_metadata_section(self, generator, successful_adoption):
        """Should have metadata section."""
        skill, result = successful_adoption

        report = generator.generate(skill, result)

        # Should mention source and quality
        assert "source" in report.markdown.lower() or "repo" in report.markdown.lower()
        assert "quality" in report.markdown.lower() or "score" in report.markdown.lower()

    def test_report_has_files_section(self, generator, successful_adoption):
        """Should have files created section."""
        skill, result = successful_adoption

        report = generator.generate(skill, result)

        assert "file" in report.markdown.lower()

    def test_report_has_dependencies_section(self, generator, successful_adoption):
        """Should have dependencies section."""
        skill, result = successful_adoption

        report = generator.generate(skill, result)

        assert "depend" in report.markdown.lower() or "requirement" in report.markdown.lower()


class TestReportSaving:
    """Test report saving to file."""

    def test_save_report_to_file(self, generator, successful_adoption, tmp_path):
        """Should save report to markdown file."""
        skill, result = successful_adoption

        report = generator.generate(skill, result)
        output_path = tmp_path / "adoption_report.md"

        generator.save(report, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert content == report.markdown

    def test_save_creates_parent_directories(self, generator, successful_adoption, tmp_path):
        """Should create parent directories if needed."""
        skill, result = successful_adoption

        report = generator.generate(skill, result)
        output_path = tmp_path / "reports" / "adoption" / "report.md"

        generator.save(report, output_path)

        assert output_path.exists()
