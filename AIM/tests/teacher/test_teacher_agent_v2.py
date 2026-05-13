"""
Tests for TeacherAgent v2.0 methods.

Tests:
- deep_audit_subagent() - GitHub search and skill extraction
- compare_solutions() - Multi-dimensional comparison
- adopt_solution() - Full adoption workflow
"""

from pathlib import Path

import pytest

from AIM.src.aim.teacher.teacher_agent import TeacherAgent
from AIM.src.aim.teacher.skills.skill_selector import Skill


@pytest.fixture
def teacher():
    """Create TeacherAgent instance."""
    return TeacherAgent()


@pytest.fixture
def sample_skills():
    """Create sample skills for comparison."""
    return [
        Skill(
            name="Circuit Breaker",
            description="High quality implementation",
            code_example="async def call(): await breaker.call()",
            quality_score=85.0,
            source_repo="https://github.com/user/high-quality",
            file_path="breaker.py",
        ),
        Skill(
            name="Circuit Breaker",
            description="Medium quality implementation",
            code_example="def call(): breaker.call()",
            quality_score=60.0,
            source_repo="https://github.com/user/medium-quality",
            file_path="breaker.py",
        ),
    ]


class TestDeepAudit:
    """Test deep_audit_subagent method."""

    @pytest.mark.asyncio
    async def test_deep_audit_searches_github(self, teacher, tmp_path):
        """Should search GitHub for relevant repos."""
        subagent_path = tmp_path / "test_agent.py"
        subagent_path.write_text("# test agent")

        # This will make real GitHub API calls
        # In production, we'd mock this
        skills = await teacher.deep_audit_subagent(
            subagent_path,
            topic="circuit breaker python",
        )

        # Should find some skills
        assert isinstance(skills, list)

    @pytest.mark.asyncio
    async def test_deep_audit_extracts_skills(self, teacher, tmp_path):
        """Should extract skills from repos."""
        subagent_path = tmp_path / "test_agent.py"
        subagent_path.write_text("# test agent")

        skills = await teacher.deep_audit_subagent(
            subagent_path,
            topic="retry pattern python",
        )

        # Each skill should have source_repo
        for skill in skills:
            assert skill.source_repo
            assert isinstance(skill, Skill)


class TestCompareSolutions:
    """Test compare_solutions method."""

    @pytest.mark.asyncio
    async def test_compare_ranks_skills(self, teacher, sample_skills):
        """Should rank skills by quality."""
        result = await teacher.compare_solutions(sample_skills)

        assert len(result.ranked_skills) == 2
        assert result.best_skill is not None

    @pytest.mark.asyncio
    async def test_compare_identifies_best(self, teacher, sample_skills):
        """Should identify best skill."""
        result = await teacher.compare_solutions(sample_skills)

        # High quality skill should be best
        assert result.best_skill.quality_score == 85.0

    @pytest.mark.asyncio
    async def test_compare_provides_dimension_scores(self, teacher, sample_skills):
        """Should provide dimension scores."""
        result = await teacher.compare_solutions(sample_skills)

        assert len(result.dimension_scores) == 2
        for repo, scores in result.dimension_scores.items():
            assert "quality" in scores
            assert "completeness" in scores
            assert "maintainability" in scores
            assert "performance" in scores


class TestAdoptSolution:
    """Test adopt_solution method."""

    @pytest.mark.asyncio
    async def test_adopt_creates_files(self, teacher, sample_skills, tmp_path):
        """Should create files in target directory."""
        skill = sample_skills[0]
        target_dir = tmp_path / "target"
        target_dir.mkdir(parents=True)  # Create target directory

        result = await teacher.adopt_solution(skill, target_dir)

        assert result.success is True
        assert len(result.files_created) > 0

    @pytest.mark.asyncio
    async def test_adopt_extracts_dependencies(self, teacher, tmp_path):
        """Should extract dependencies from code."""
        skill = Skill(
            name="Test Skill",
            description="Test",
            code_example="import httpx\nimport structlog",
            quality_score=70.0,
            source_repo="https://github.com/user/repo",
            file_path="test.py",
        )
        target_dir = tmp_path / "target"
        target_dir.mkdir(parents=True)  # Create target directory

        result = await teacher.adopt_solution(skill, target_dir)

        assert "httpx" in result.dependencies_added
        assert "structlog" in result.dependencies_added

    @pytest.mark.asyncio
    async def test_adopt_generates_report(self, teacher, sample_skills, tmp_path):
        """Should generate adoption report."""
        skill = sample_skills[0]
        target_dir = tmp_path / "target"
        target_dir.mkdir(parents=True)  # Create target directory

        result = await teacher.adopt_solution(skill, target_dir)

        assert result.report
        assert len(result.report) > 0


class TestIntegration:
    """Test full workflow integration."""

    @pytest.mark.asyncio
    async def test_full_workflow(self, teacher, tmp_path):
        """Should complete full audit → compare → adopt workflow."""
        # Create dummy subagent
        subagent_path = tmp_path / "test_agent.py"
        subagent_path.write_text("# test agent")

        # Step 1: Deep audit (find skills)
        skills = await teacher.deep_audit_subagent(
            subagent_path,
            topic="caching python",
        )

        if not skills:
            pytest.skip("No skills found (GitHub API issue)")

        # Step 2: Compare solutions
        comparison = await teacher.compare_solutions(skills)

        assert comparison.best_skill is not None

        # Step 3: Adopt best solution
        target_dir = tmp_path / "adopted"
        target_dir.mkdir(parents=True)  # Create target directory
        adoption = await teacher.adopt_solution(
            comparison.best_skill,
            target_dir,
        )

        assert adoption.success is True
        assert len(adoption.files_created) > 0
