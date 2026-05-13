"""
Tests for SkillTeacher.

Tests:
- Integration point analysis
- Pattern adaptation
- Code integration
- Test generation
- Metrics measurement
- Improvement calculation
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from AIM.src.aim.teacher.skills.skill_comparator import (
    ComparisonResult,
    SkillScore,
)
from AIM.src.aim.teacher.skills.skill_teacher import (
    AdaptedCode,
    IntegrationPoint,
    SkillTeacher,
    TeachingResult,
)


@pytest.fixture
def skill_teacher():
    """Create SkillTeacher instance."""
    return SkillTeacher()


@pytest.fixture
def sample_skill():
    """Create sample skill comparison."""
    return ComparisonResult(
        skill_name="Circuit Breaker",
        skill_type="error_handling",
        github_score=SkillScore(
            completeness=90.0,
            quality=85.0,
            security=95.0,
            performance=80.0,
            total=87.5,
        ),
        our_score=SkillScore(
            completeness=60.0,
            quality=70.0,
            security=75.0,
            performance=65.0,
            total=67.5,
        ),
        improvement_potential=20.0,
        recommendation="ADOPT",
        rationale="GitHub implementation has better error handling",
        github_implementation="class CircuitBreaker: ...",
        our_implementation="# No circuit breaker",
        metadata={},
    )


@pytest.fixture
def sandbox_path(tmp_path):
    """Create sandbox directory structure."""
    sandbox = tmp_path / "sandbox"
    subagent_dir = sandbox / "AIM" / "src" / "aim" / "subagents" / "keyword-research"
    subagent_dir.mkdir(parents=True)

    # Create sample files
    (subagent_dir / "api_client.py").write_text("# API client")
    (subagent_dir / "base.py").write_text("# Base class")

    # Create test directory
    test_dir = sandbox / "AIM" / "tests" / "subagents" / "keyword-research"
    test_dir.mkdir(parents=True)

    # Create requirements.txt
    (sandbox / "requirements.txt").write_text("httpx>=0.27.0\n")

    return sandbox


class TestIntegrationPointAnalysis:
    """Test integration point analysis."""

    @pytest.mark.asyncio
    async def test_find_integration_points_for_error_handling(
        self, skill_teacher, sample_skill, sandbox_path
    ):
        """Should find files that need error handling."""
        points = await skill_teacher._analyze_integration_points(
            sample_skill, "keyword-research", sandbox_path
        )

        assert len(points) > 0
        assert all(isinstance(p, IntegrationPoint) for p in points)
        assert any("client" in p.file_path.name for p in points)

    @pytest.mark.asyncio
    async def test_prioritize_by_file_pattern(
        self, skill_teacher, sample_skill, sandbox_path
    ):
        """Should prioritize files matching skill type pattern."""
        points = await skill_teacher._analyze_integration_points(
            sample_skill, "keyword-research", sandbox_path
        )

        # Should find api_client.py (matches *_client.py pattern)
        file_names = [p.file_path.name for p in points]
        assert "api_client.py" in file_names

    @pytest.mark.asyncio
    async def test_limit_integration_points(
        self, skill_teacher, sample_skill, sandbox_path
    ):
        """Should limit to top 5 integration points."""
        # Create many files
        subagent_dir = sandbox_path / "AIM" / "src" / "aim" / "subagents" / "keyword-research"
        for i in range(10):
            (subagent_dir / f"client_{i}.py").write_text(f"# Client {i}")

        points = await skill_teacher._analyze_integration_points(
            sample_skill, "keyword-research", sandbox_path
        )

        assert len(points) <= 5

    @pytest.mark.asyncio
    async def test_handle_missing_subagent(
        self, skill_teacher, sample_skill, sandbox_path
    ):
        """Should handle missing subagent gracefully."""
        points = await skill_teacher._analyze_integration_points(
            sample_skill, "nonexistent-subagent", sandbox_path
        )

        assert len(points) == 0


class TestPatternAdaptation:
    """Test pattern adaptation."""

    @pytest.mark.asyncio
    async def test_adapt_circuit_breaker_pattern(self, skill_teacher, sample_skill):
        """Should adapt circuit breaker pattern to our architecture."""
        adapted = await skill_teacher._adapt_pattern(
            sample_skill, "keyword-research", []
        )

        assert isinstance(adapted, AdaptedCode)
        assert "pybreaker" in adapted.adapted_pattern
        assert "EventBus" in adapted.adapted_pattern
        assert "ObsidianVault" in adapted.adapted_pattern
        assert "async" in adapted.adapted_pattern

    @pytest.mark.asyncio
    async def test_adaptation_includes_dependencies(
        self, skill_teacher, sample_skill
    ):
        """Should include required dependencies."""
        adapted = await skill_teacher._adapt_pattern(
            sample_skill, "keyword-research", []
        )

        assert len(adapted.dependencies) > 0
        assert any("pybreaker" in dep for dep in adapted.dependencies)

    @pytest.mark.asyncio
    async def test_adaptation_includes_imports(
        self, skill_teacher, sample_skill
    ):
        """Should include required imports."""
        adapted = await skill_teacher._adapt_pattern(
            sample_skill, "keyword-research", []
        )

        assert len(adapted.imports) > 0
        assert any("EventBus" in imp for imp in adapted.imports)

    @pytest.mark.asyncio
    async def test_adaptation_notes_explain_changes(
        self, skill_teacher, sample_skill
    ):
        """Should explain what was adapted and why."""
        adapted = await skill_teacher._adapt_pattern(
            sample_skill, "keyword-research", []
        )

        assert len(adapted.adaptation_notes) > 0
        assert "production-ready" in adapted.adaptation_notes.lower()


class TestCodeIntegration:
    """Test code integration."""

    @pytest.mark.asyncio
    async def test_add_dependencies_to_requirements(
        self, skill_teacher, sandbox_path
    ):
        """Should add dependencies to requirements.txt."""
        adapted = AdaptedCode(
            original_pattern="",
            adapted_pattern="",
            adaptation_notes="",
            dependencies=["pybreaker>=1.0.0"],
            imports=[],
        )

        changes = await skill_teacher._integrate_code(adapted, [], sandbox_path)

        requirements = (sandbox_path / "requirements.txt").read_text()
        assert "pybreaker>=1.0.0" in requirements
        assert str(sandbox_path / "requirements.txt") in changes

    @pytest.mark.asyncio
    async def test_track_changed_files(self, skill_teacher, sandbox_path):
        """Should track all changed files."""
        adapted = AdaptedCode(
            original_pattern="",
            adapted_pattern="",
            adaptation_notes="",
            dependencies=["pybreaker>=1.0.0"],
            imports=[],
        )

        integration_points = [
            IntegrationPoint(
                file_path=sandbox_path / "AIM" / "src" / "aim" / "subagents" / "keyword-research" / "api_client.py",
                class_name="APIClient",
                function_name=None,
                line_number=None,
                reason="Needs circuit breaker",
            )
        ]

        changes = await skill_teacher._integrate_code(
            adapted, integration_points, sandbox_path
        )

        assert len(changes) > 0


class TestTestGeneration:
    """Test test generation."""

    @pytest.mark.asyncio
    async def test_create_test_file(
        self, skill_teacher, sample_skill, sandbox_path
    ):
        """Should create test file for skill."""
        tests = await skill_teacher._write_tests(
            sample_skill, "keyword-research", sandbox_path
        )

        assert len(tests) == 1
        test_file = Path(tests[0])
        assert test_file.exists()
        assert "test_error_handling" in test_file.name

    @pytest.mark.asyncio
    async def test_test_file_has_proper_structure(
        self, skill_teacher, sample_skill, sandbox_path
    ):
        """Should create test file with proper structure."""
        tests = await skill_teacher._write_tests(
            sample_skill, "keyword-research", sandbox_path
        )

        test_content = Path(tests[0]).read_text()
        assert "import pytest" in test_content
        assert "class Test" in test_content
        assert "def test_" in test_content

    @pytest.mark.asyncio
    async def test_test_file_includes_integration_tests(
        self, skill_teacher, sample_skill, sandbox_path
    ):
        """Should include integration tests with Event Bus."""
        tests = await skill_teacher._write_tests(
            sample_skill, "keyword-research", sandbox_path
        )

        test_content = Path(tests[0]).read_text()
        assert "event_bus" in test_content.lower()


class TestMetricsMeasurement:
    """Test metrics measurement."""

    @pytest.mark.asyncio
    async def test_measure_before_metrics(
        self, skill_teacher, sandbox_path
    ):
        """Should measure metrics before teaching."""
        metrics = await skill_teacher._measure_metrics(
            "keyword-research", sandbox_path
        )

        assert "test_coverage" in metrics
        assert "code_quality" in metrics
        assert "complexity" in metrics
        assert "error_rate" in metrics
        assert "performance" in metrics

    @pytest.mark.asyncio
    async def test_metrics_are_numeric(
        self, skill_teacher, sandbox_path
    ):
        """Should return numeric metrics."""
        metrics = await skill_teacher._measure_metrics(
            "keyword-research", sandbox_path
        )

        assert all(isinstance(v, (int, float)) for v in metrics.values())


class TestImprovementCalculation:
    """Test improvement calculation."""

    def test_calculate_improvement_for_higher_is_better(self, skill_teacher):
        """Should calculate improvement for metrics where higher is better."""
        before = {"test_coverage": 75.0, "code_quality": 8.0}
        after = {"test_coverage": 90.0, "code_quality": 9.0}

        improvement = skill_teacher._calculate_improvement(before, after)

        assert improvement > 0  # Should show improvement

    def test_calculate_improvement_for_lower_is_better(self, skill_teacher):
        """Should calculate improvement for metrics where lower is better."""
        before = {"error_rate": 10.0, "complexity": 20.0}
        after = {"error_rate": 5.0, "complexity": 15.0}

        improvement = skill_teacher._calculate_improvement(before, after)

        assert improvement > 0  # Should show improvement

    def test_handle_no_improvement(self, skill_teacher):
        """Should handle case with no improvement."""
        before = {"test_coverage": 80.0}
        after = {"test_coverage": 80.0}

        improvement = skill_teacher._calculate_improvement(before, after)

        assert improvement == 0.0

    def test_handle_regression(self, skill_teacher):
        """Should handle regression (negative improvement)."""
        before = {"test_coverage": 90.0}
        after = {"test_coverage": 75.0}

        improvement = skill_teacher._calculate_improvement(before, after)

        assert improvement < 0  # Should show regression


class TestTeachingDocumentation:
    """Test teaching documentation."""

    @pytest.mark.asyncio
    async def test_document_teaching_process(
        self, skill_teacher, sample_skill
    ):
        """Should document the teaching process."""
        integration_points = [
            IntegrationPoint(
                file_path=Path("api_client.py"),
                class_name="APIClient",
                function_name=None,
                line_number=None,
                reason="Needs circuit breaker",
            )
        ]

        notes = await skill_teacher._document_teaching(
            sample_skill,
            integration_points,
            improvement=15.5,
            test_results={"passed": True, "coverage": 85.0},
        )

        assert "Circuit Breaker" in notes
        assert "error_handling" in notes
        assert "15.5%" in notes
        assert "85.0%" in notes

    @pytest.mark.asyncio
    async def test_documentation_includes_integration_points(
        self, skill_teacher, sample_skill
    ):
        """Should list all integration points."""
        integration_points = [
            IntegrationPoint(
                file_path=Path("api_client.py"),
                class_name=None,
                function_name=None,
                line_number=None,
                reason="Needs circuit breaker",
            ),
            IntegrationPoint(
                file_path=Path("base.py"),
                class_name=None,
                function_name=None,
                line_number=None,
                reason="Base class needs error handling",
            ),
        ]

        notes = await skill_teacher._document_teaching(
            sample_skill,
            integration_points,
            improvement=10.0,
            test_results={"passed": True, "coverage": 80.0},
        )

        assert "api_client.py" in notes
        assert "base.py" in notes


class TestFullTeachingWorkflow:
    """Test full teaching workflow."""

    @pytest.mark.asyncio
    async def test_teach_skill_end_to_end(
        self, skill_teacher, sample_skill, sandbox_path
    ):
        """Should teach skill end-to-end."""
        result = await skill_teacher.teach_skill(
            sample_skill, "keyword-research", sandbox_path
        )

        assert isinstance(result, TeachingResult)
        assert result.skill_name == "Circuit Breaker"
        assert result.skill_type == "error_handling"
        assert result.target_subagent == "keyword-research"

    @pytest.mark.asyncio
    async def test_teaching_result_includes_metrics(
        self, skill_teacher, sample_skill, sandbox_path
    ):
        """Should include before/after metrics."""
        result = await skill_teacher.teach_skill(
            sample_skill, "keyword-research", sandbox_path
        )

        assert len(result.before_metrics) > 0
        assert len(result.after_metrics) > 0
        assert isinstance(result.improvement, float)

    @pytest.mark.asyncio
    async def test_teaching_result_includes_changes(
        self, skill_teacher, sample_skill, sandbox_path
    ):
        """Should track code changes and tests."""
        result = await skill_teacher.teach_skill(
            sample_skill, "keyword-research", sandbox_path
        )

        assert len(result.code_changes) > 0
        assert len(result.tests_added) > 0

    @pytest.mark.asyncio
    async def test_teaching_result_includes_documentation(
        self, skill_teacher, sample_skill, sandbox_path
    ):
        """Should include teaching notes."""
        result = await skill_teacher.teach_skill(
            sample_skill, "keyword-research", sandbox_path
        )

        assert len(result.teaching_notes) > 0
        assert "Circuit Breaker" in result.teaching_notes

    @pytest.mark.asyncio
    async def test_mark_as_successful_when_tests_pass(
        self, skill_teacher, sample_skill, sandbox_path
    ):
        """Should mark as successful when tests pass and improvement > 0."""
        result = await skill_teacher.teach_skill(
            sample_skill, "keyword-research", sandbox_path
        )

        # Mock returns passed=True and improvement > 0
        assert result.taught_successfully is True
