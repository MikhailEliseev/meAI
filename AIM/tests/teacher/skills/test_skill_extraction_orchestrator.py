"""
Tests for SkillExtractionOrchestrator.

Tests:
- Full workflow orchestration
- Component coordination
- Report generation
- Error handling
- Strategy selection
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from AIM.src.aim.teacher.skills.skill_comparator import (
    ComparisonResult,
    SkillScore,
)
from AIM.src.aim.teacher.skills.skill_extractor import (
    ExtractedSkill,
    SkillType,
)
from AIM.src.aim.teacher.skills.skill_extraction_orchestrator import (
    SkillExtractionOrchestrator,
    SkillExtractionReport,
)
from AIM.src.aim.teacher.skills.skill_selector import (
    SelectedSkill,
    SelectionCriteria,
)
from AIM.src.aim.teacher.skills.skill_teacher import TeachingResult


@pytest.fixture
def orchestrator():
    """Create SkillExtractionOrchestrator instance."""
    return SkillExtractionOrchestrator()


@pytest.fixture
def sample_extraction_result():
    """Create sample extraction result."""
    return [
        ExtractedSkill(
            skill_type=SkillType.ERROR_HANDLING,
            name="Circuit Breaker",
            description="Circuit breaker pattern",
            code_snippet="class CircuitBreaker: ...",
            file_path="api_client.py",
            line_start=10,
            line_end=50,
            confidence=0.9,
            dependencies=[],
            metadata={},
        ),
        ExtractedSkill(
            skill_type=SkillType.RETRY,
            name="Retry Logic",
            description="Exponential backoff retry",
            code_snippet="@retry(...)",
            file_path="api_client.py",
            line_start=60,
            line_end=80,
            confidence=0.85,
            dependencies=["tenacity"],
            metadata={},
        ),
    ]


@pytest.fixture
def sample_comparisons():
    """Create sample skill comparisons."""
    return [
        ComparisonResult(
            skill_type=SkillType.ERROR_HANDLING,
            github_score=SkillScore(
                skill_type=SkillType.ERROR_HANDLING,
                source="github",
                completeness=90.0,
                quality=85.0,
                performance=80.0,
                maintainability=85.0,
                security=95.0,
                total_score=87.5,
                strengths=["Robust error handling"],
                weaknesses=["Complex setup"],
                metadata={},
            ),
            our_score=SkillScore(
                skill_type=SkillType.ERROR_HANDLING,
                source="ours",
                completeness=60.0,
                quality=70.0,
                performance=65.0,
                maintainability=70.0,
                security=75.0,
                total_score=67.5,
                strengths=["Simple"],
                weaknesses=["Missing circuit breaker"],
                metadata={},
            ),
            recommendation="adopt",
            gap_analysis="Better error handling",
            action_items=["Implement circuit breaker"],
        ),
        ComparisonResult(
            skill_type=SkillType.RETRY,
            github_score=SkillScore(
                skill_type=SkillType.RETRY,
                source="github",
                completeness=85.0,
                quality=80.0,
                performance=75.0,
                maintainability=80.0,
                security=90.0,
                total_score=82.5,
                strengths=["Exponential backoff"],
                weaknesses=["Limited configuration"],
                metadata={},
            ),
            our_score=SkillScore(
                skill_type=SkillType.RETRY,
                source="ours",
                completeness=80.0,
                quality=75.0,
                performance=70.0,
                maintainability=75.0,
                security=85.0,
                total_score=77.5,
                strengths=["Simple retry"],
                weaknesses=["No backoff"],
                metadata={},
            ),
            recommendation="improve",
            gap_analysis="Minor improvement",
            action_items=["Add exponential backoff"],
        ),
    ]


@pytest.fixture
def sample_selection_result(sample_comparisons):
    """Create sample selection result."""
    return {
        "skills_to_adopt": [
            SelectedSkill(
                comparison=sample_comparisons[0],
                selection_score=85.0,
                selection_reason="High improvement potential",
                priority=1,
                metadata={},
            )
        ],
        "skills_to_keep": [sample_comparisons[1]],
        "skills_to_skip": [],
    }


@pytest.fixture
def sample_teaching_results():
    """Create sample teaching results."""
    return [
        TeachingResult(
            skill_name="Circuit Breaker",
            skill_type="error_handling",
            target_subagent="keyword-research",
            taught_successfully=True,
            integration_points=[],
            before_metrics={"test_coverage": 75.0},
            after_metrics={"test_coverage": 90.0},
            improvement=20.0,
            code_changes=["api_client.py"],
            tests_added=["test_circuit_breaker.py"],
            teaching_notes="Successfully taught",
            metadata={},
        )
    ]


class TestWorkflowOrchestration:
    """Test full workflow orchestration."""

    @pytest.mark.asyncio
    async def test_extract_and_teach_full_workflow(
        self,
        orchestrator,
        sample_extraction_result,
        sample_comparisons,
        sample_selection_result,
        sample_teaching_results,
        tmp_path,
    ):
        """Should orchestrate full workflow end-to-end."""
        # Mock all components
        orchestrator.extractor.extract_skills = AsyncMock(
            return_value=sample_extraction_result
        )
        orchestrator.comparator.compare_skill = AsyncMock(
            side_effect=sample_comparisons
        )
        orchestrator.selector.select_skills = MagicMock(
            return_value=sample_selection_result
        )
        orchestrator.teacher.teach_skill = AsyncMock(
            return_value=sample_teaching_results[0]
        )

        report = await orchestrator.extract_and_teach(
            github_repo_url="https://github.com/user/repo",
            target_subagent="keyword-research",
            adoption_strategy="balanced",
            sandbox_path=tmp_path,
        )

        assert isinstance(report, SkillExtractionReport)
        assert report.github_repo_url == "https://github.com/user/repo"
        assert report.target_subagent == "keyword-research"

    @pytest.mark.asyncio
    async def test_workflow_calls_all_components(
        self,
        orchestrator,
        sample_extraction_result,
        sample_comparisons,
        sample_selection_result,
        sample_teaching_results,
        tmp_path,
    ):
        """Should call all components in correct order."""
        # Mock components
        orchestrator.extractor.extract_skills = AsyncMock(
            return_value=sample_extraction_result
        )
        orchestrator.comparator.compare_skill = AsyncMock(
            side_effect=sample_comparisons
        )
        orchestrator.selector.select_skills = MagicMock(
            return_value=sample_selection_result
        )
        orchestrator.teacher.teach_skill = AsyncMock(
            return_value=sample_teaching_results[0]
        )

        await orchestrator.extract_and_teach(
            "https://github.com/user/repo",
            "keyword-research",
            sandbox_path=tmp_path,
        )

        # Verify all components called
        orchestrator.extractor.extract_skills.assert_called_once()
        assert orchestrator.comparator.compare_skill.call_count == 2
        orchestrator.selector.select_skills.assert_called_once()
        orchestrator.teacher.teach_skill.assert_called_once()


class TestReportGeneration:
    """Test report generation."""

    @pytest.mark.asyncio
    async def test_report_includes_all_results(
        self,
        orchestrator,
        sample_extraction_result,
        sample_comparisons,
        sample_selection_result,
        sample_teaching_results,
        tmp_path,
    ):
        """Should include all results in report."""
        orchestrator.extractor.extract_skills = AsyncMock(
            return_value=sample_extraction_result
        )
        orchestrator.comparator.compare_skill = AsyncMock(
            side_effect=sample_comparisons
        )
        orchestrator.selector.select_skills = MagicMock(
            return_value=sample_selection_result
        )
        orchestrator.teacher.teach_skill = AsyncMock(
            return_value=sample_teaching_results[0]
        )

        report = await orchestrator.extract_and_teach(
            "https://github.com/user/repo",
            "keyword-research",
            sandbox_path=tmp_path,
        )

        assert report.extraction_result == sample_extraction_result
        assert len(report.comparisons) == 2
        assert report.selection_result == sample_selection_result
        assert len(report.teaching_results) == 1

    @pytest.mark.asyncio
    async def test_report_calculates_statistics(
        self,
        orchestrator,
        sample_extraction_result,
        sample_comparisons,
        sample_selection_result,
        sample_teaching_results,
        tmp_path,
    ):
        """Should calculate statistics correctly."""
        orchestrator.extractor.extract_skills = AsyncMock(
            return_value=sample_extraction_result
        )
        orchestrator.comparator.compare_skill = AsyncMock(
            side_effect=sample_comparisons
        )
        orchestrator.selector.select_skills = MagicMock(
            return_value=sample_selection_result
        )
        orchestrator.teacher.teach_skill = AsyncMock(
            return_value=sample_teaching_results[0]
        )

        report = await orchestrator.extract_and_teach(
            "https://github.com/user/repo",
            "keyword-research",
            sandbox_path=tmp_path,
        )

        assert report.skills_adopted == 1
        assert report.skills_kept == 1
        assert report.skills_skipped == 0
        assert report.overall_improvement == 20.0

    @pytest.mark.asyncio
    async def test_report_includes_timing(
        self,
        orchestrator,
        sample_extraction_result,
        sample_comparisons,
        sample_selection_result,
        sample_teaching_results,
        tmp_path,
    ):
        """Should include timing information."""
        orchestrator.extractor.extract_skills = AsyncMock(
            return_value=sample_extraction_result
        )
        orchestrator.comparator.compare_skill = AsyncMock(
            side_effect=sample_comparisons
        )
        orchestrator.selector.select_skills = MagicMock(
            return_value=sample_selection_result
        )
        orchestrator.teacher.teach_skill = AsyncMock(
            return_value=sample_teaching_results[0]
        )

        report = await orchestrator.extract_and_teach(
            "https://github.com/user/repo",
            "keyword-research",
            sandbox_path=tmp_path,
        )

        assert report.total_time > 0
        assert report.report_timestamp is not None


class TestStrategySelection:
    """Test adoption strategy selection."""

    def test_aggressive_strategy_criteria(self, orchestrator):
        """Should use low thresholds for aggressive strategy."""
        criteria = orchestrator._get_selection_criteria("aggressive")

        assert criteria.min_score_threshold == 60.0
        assert criteria.min_improvement_threshold == 5.0
        assert criteria.max_skills_per_type == 5
        assert criteria.prioritize_security is False

    def test_conservative_strategy_criteria(self, orchestrator):
        """Should use high thresholds for conservative strategy."""
        criteria = orchestrator._get_selection_criteria("conservative")

        assert criteria.min_score_threshold == 80.0
        assert criteria.min_improvement_threshold == 15.0
        assert criteria.max_skills_per_type == 2
        assert criteria.prioritize_security is True
        assert criteria.budget_limit == 10

    def test_balanced_strategy_criteria(self, orchestrator):
        """Should use medium thresholds for balanced strategy."""
        criteria = orchestrator._get_selection_criteria("balanced")

        assert criteria.min_score_threshold == 70.0
        assert criteria.min_improvement_threshold == 10.0
        assert criteria.max_skills_per_type == 3
        assert criteria.prioritize_security is True


class TestErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_handle_teaching_failure_gracefully(
        self,
        orchestrator,
        sample_extraction_result,
        sample_comparisons,
        sample_selection_result,
        tmp_path,
    ):
        """Should handle teaching failures gracefully."""
        orchestrator.extractor.extract_skills = AsyncMock(
            return_value=sample_extraction_result
        )
        orchestrator.comparator.compare_skill = AsyncMock(
            side_effect=sample_comparisons
        )
        orchestrator.selector.select_skills = MagicMock(
            return_value=sample_selection_result
        )
        orchestrator.teacher.teach_skill = AsyncMock(
            side_effect=Exception("Teaching failed")
        )

        report = await orchestrator.extract_and_teach(
            "https://github.com/user/repo",
            "keyword-research",
            sandbox_path=tmp_path,
        )

        # Should complete despite teaching failure
        assert isinstance(report, SkillExtractionReport)
        assert len(report.teaching_results) == 0

    @pytest.mark.asyncio
    async def test_calculate_improvement_with_no_successful_teachings(
        self,
        orchestrator,
        sample_extraction_result,
        sample_comparisons,
        sample_selection_result,
        tmp_path,
    ):
        """Should handle case with no successful teachings."""
        orchestrator.extractor.extract_skills = AsyncMock(
            return_value=sample_extraction_result
        )
        orchestrator.comparator.compare_skill = AsyncMock(
            side_effect=sample_comparisons
        )
        orchestrator.selector.select_skills = MagicMock(
            return_value=sample_selection_result
        )
        orchestrator.teacher.teach_skill = AsyncMock(
            side_effect=Exception("Teaching failed")
        )

        report = await orchestrator.extract_and_teach(
            "https://github.com/user/repo",
            "keyword-research",
            sandbox_path=tmp_path,
        )

        assert report.overall_improvement == 0.0


class TestReportFormatting:
    """Test report formatting."""

    def test_format_report_as_markdown(
        self, orchestrator, sample_extraction_result, sample_comparisons
    ):
        """Should format report as markdown."""
        report = SkillExtractionReport(
            github_repo_url="https://github.com/user/repo",
            target_subagent="keyword-research",
            extraction_result=sample_extraction_result,
            comparisons=sample_comparisons,
            selection_result={
                "skills_to_adopt": [],
                "skills_to_keep": [],
                "skills_to_skip": [],
            },
            teaching_results=[],
            overall_improvement=0.0,
            skills_adopted=0,
            skills_kept=0,
            skills_skipped=2,
            total_time=5.5,
            report_timestamp=None,
        )

        md = orchestrator.format_report(report)

        assert "# Skill Extraction Report" in md
        assert "https://github.com/user/repo" in md
        assert "keyword-research" in md
        assert "Circuit Breaker" in md
        assert "Retry Logic" in md

    def test_formatted_report_includes_all_sections(
        self, orchestrator, sample_extraction_result, sample_comparisons
    ):
        """Should include all report sections."""
        report = SkillExtractionReport(
            github_repo_url="https://github.com/user/repo",
            target_subagent="keyword-research",
            extraction_result=sample_extraction_result,
            comparisons=sample_comparisons,
            selection_result={
                "skills_to_adopt": [],
                "skills_to_keep": [],
                "skills_to_skip": [],
            },
            teaching_results=[],
            overall_improvement=0.0,
            skills_adopted=0,
            skills_kept=0,
            skills_skipped=2,
            total_time=5.5,
            report_timestamp=None,
        )

        md = orchestrator.format_report(report)

        assert "## Summary" in md
        assert "## Extracted Skills" in md
        assert "## Comparisons" in md
        assert "## Selection Results" in md
        assert "## Teaching Results" in md
        assert "## Conclusion" in md
