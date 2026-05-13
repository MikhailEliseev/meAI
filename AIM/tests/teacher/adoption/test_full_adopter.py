"""
Tests for FullAdopter.

Tests:
- Orchestrate full adoption workflow
- Copy files from GitHub repo
- Install dependencies
- Adapt imports to project structure
- Adapt tests to project conventions
- Generate adoption report
"""

from pathlib import Path

import pytest

from AIM.src.aim.teacher.skills.skill_selector import Skill
from AIM.src.aim.teacher.adoption.full_adopter import (
    FullAdopter,
    AdoptionResult,
)


@pytest.fixture
def adopter():
    """Create FullAdopter instance."""
    return FullAdopter()


@pytest.fixture
def circuit_breaker_skill():
    """Create circuit breaker skill for adoption."""
    return Skill(
        name="Circuit Breaker",
        description="Production-ready circuit breaker",
        code_example="""
from pybreaker import CircuitBreaker

class APIClient:
    def __init__(self):
        self.breaker = CircuitBreaker(fail_max=5, reset_timeout=60)

    async def call_api(self):
        return await self.breaker.call(self._do_call)
""",
        quality_score=85.0,
        source_repo="https://github.com/user/circuit-breaker-repo",
        file_path="circuit_breaker.py",
    )


class TestFullAdoption:
    """Test full adoption workflow."""

    @pytest.mark.asyncio
    async def test_adopt_skill(self, adopter, circuit_breaker_skill, tmp_path):
        """Should adopt skill completely."""
        target_path = tmp_path / "adopted"
        target_path.mkdir()

        result = await adopter.adopt(
            skill=circuit_breaker_skill,
            target_dir=target_path,
        )

        assert isinstance(result, AdoptionResult)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_copy_files(self, adopter, circuit_breaker_skill, tmp_path):
        """Should copy files to target directory."""
        target_path = tmp_path / "adopted"
        target_path.mkdir()

        result = await adopter.adopt(
            skill=circuit_breaker_skill,
            target_dir=target_path,
        )

        # Should create file
        assert len(result.files_created) > 0

    @pytest.mark.asyncio
    async def test_install_dependencies(self, adopter, circuit_breaker_skill, tmp_path):
        """Should identify dependencies for installation."""
        target_path = tmp_path / "adopted"
        target_path.mkdir()

        result = await adopter.adopt(
            skill=circuit_breaker_skill,
            target_dir=target_path,
        )

        # Should identify pybreaker dependency
        assert "pybreaker" in result.dependencies_added

    @pytest.mark.asyncio
    async def test_adapt_imports(self, adopter, circuit_breaker_skill, tmp_path):
        """Should adapt imports to project structure."""
        target_path = tmp_path / "adopted"
        target_path.mkdir()

        result = await adopter.adopt(
            skill=circuit_breaker_skill,
            target_dir=target_path,
        )

        # Should have adapted code
        assert result.code_adapted is True


class TestAdoptionReport:
    """Test adoption report generation."""

    @pytest.mark.asyncio
    async def test_generate_report(self, adopter, circuit_breaker_skill, tmp_path):
        """Should generate adoption report."""
        target_path = tmp_path / "adopted"
        target_path.mkdir()

        result = await adopter.adopt(
            skill=circuit_breaker_skill,
            target_dir=target_path,
        )

        assert result.report is not None
        assert len(result.report) > 0

    @pytest.mark.asyncio
    async def test_report_includes_summary(self, adopter, circuit_breaker_skill, tmp_path):
        """Should include summary in report."""
        target_path = tmp_path / "adopted"
        target_path.mkdir()

        result = await adopter.adopt(
            skill=circuit_breaker_skill,
            target_dir=target_path,
        )

        # Report should mention skill name
        assert circuit_breaker_skill.name in result.report


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handle_empty_skill(self, adopter, tmp_path):
        """Should handle skill without code."""
        skill = Skill(
            name="Empty",
            description="No code",
            code_example="",
            quality_score=0.0,
            source_repo="https://github.com/user/empty",
            file_path="empty.py",
        )

        target_path = tmp_path / "adopted"
        target_path.mkdir()

        result = await adopter.adopt(skill=skill, target_dir=target_path)

        # Should fail gracefully
        assert result.success is False

    @pytest.mark.asyncio
    async def test_handle_invalid_target_dir(self, adopter, circuit_breaker_skill):
        """Should handle invalid target directory."""
        invalid_path = Path("/nonexistent/path")

        result = await adopter.adopt(
            skill=circuit_breaker_skill,
            target_dir=invalid_path,
        )

        # Should fail gracefully
        assert result.success is False
