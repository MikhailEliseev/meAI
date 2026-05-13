"""
Tests for SkillComparator.

Tests:
- Multi-dimensional skill comparison (quality, completeness, maintainability, performance)
- Ranking skills by total score
- Identifying best implementation
- Edge cases (single skill, empty list, identical skills)
"""

from pathlib import Path

import pytest

from AIM.src.aim.teacher.skills.skill_selector import Skill
from AIM.src.aim.teacher.skills.skill_comparator import (
    SkillComparator,
    ComparisonResult,
)


@pytest.fixture
def comparator():
    """Create SkillComparator instance."""
    return SkillComparator()


@pytest.fixture
def high_quality_skill():
    """Create high quality skill fixture."""
    return Skill(
        name="Circuit Breaker",
        description="Production-ready circuit breaker with error handling",
        code_example="""
async def call_api(self):
    try:
        return await self.breaker.call(self._do_call)
    except Exception as e:
        logger.error("api_call_failed", error=str(e))
        raise
""",
        quality_score=85.0,
        source_repo="https://github.com/user/high-quality-repo",
        file_path="circuit_breaker.py",
    )


@pytest.fixture
def medium_quality_skill():
    """Create medium quality skill fixture."""
    return Skill(
        name="Circuit Breaker",
        description="Basic circuit breaker implementation",
        code_example="""
def call_api(self):
    return self.breaker.call(self._do_call)
""",
        quality_score=60.0,
        source_repo="https://github.com/user/medium-repo",
        file_path="breaker.py",
    )


@pytest.fixture
def low_quality_skill():
    """Create low quality skill fixture."""
    return Skill(
        name="Circuit Breaker",
        description="Simple circuit breaker",
        code_example="""
def call():
    pass
""",
        quality_score=30.0,
        source_repo="https://github.com/user/low-repo",
        file_path="simple.py",
    )


class TestSkillComparison:
    """Test skill comparison."""

    @pytest.mark.asyncio
    async def test_compare_two_skills(self, comparator, high_quality_skill, medium_quality_skill):
        """Should compare two skills across dimensions."""
        result = await comparator.compare(
            [high_quality_skill, medium_quality_skill]
        )

        assert len(result.ranked_skills) == 2
        assert result.best_skill is not None
        assert len(result.dimension_scores) == 2

    @pytest.mark.asyncio
    async def test_rank_by_total_score(self, comparator, high_quality_skill, medium_quality_skill, low_quality_skill):
        """Should rank skills by total score."""
        result = await comparator.compare(
            [low_quality_skill, high_quality_skill, medium_quality_skill]
        )

        # Should be ranked: high > medium > low
        assert result.ranked_skills[0] == high_quality_skill
        assert result.ranked_skills[1] == medium_quality_skill
        assert result.ranked_skills[2] == low_quality_skill

    @pytest.mark.asyncio
    async def test_identify_best_skill(self, comparator, high_quality_skill, medium_quality_skill):
        """Should identify best skill."""
        result = await comparator.compare(
            [medium_quality_skill, high_quality_skill]
        )

        assert result.best_skill == high_quality_skill


class TestMultiDimensionalScoring:
    """Test multi-dimensional scoring."""

    @pytest.mark.asyncio
    async def test_score_quality_dimension(self, comparator, high_quality_skill):
        """Should score quality dimension."""
        result = await comparator.compare([high_quality_skill])

        scores = result.dimension_scores[high_quality_skill.source_repo]
        assert "quality" in scores
        assert 0.0 <= scores["quality"] <= 100.0

    @pytest.mark.asyncio
    async def test_score_completeness_dimension(self, comparator, high_quality_skill):
        """Should score completeness dimension."""
        result = await comparator.compare([high_quality_skill])

        scores = result.dimension_scores[high_quality_skill.source_repo]
        assert "completeness" in scores
        assert 0.0 <= scores["completeness"] <= 100.0

    @pytest.mark.asyncio
    async def test_score_maintainability_dimension(self, comparator, high_quality_skill):
        """Should score maintainability dimension."""
        result = await comparator.compare([high_quality_skill])

        scores = result.dimension_scores[high_quality_skill.source_repo]
        assert "maintainability" in scores
        assert 0.0 <= scores["maintainability"] <= 100.0

    @pytest.mark.asyncio
    async def test_score_performance_dimension(self, comparator, high_quality_skill):
        """Should score performance dimension."""
        result = await comparator.compare([high_quality_skill])

        scores = result.dimension_scores[high_quality_skill.source_repo]
        assert "performance" in scores
        assert 0.0 <= scores["performance"] <= 100.0

    @pytest.mark.asyncio
    async def test_higher_score_for_async(self, comparator):
        """Should give higher performance score for async code."""
        async_skill = Skill(
            name="Async API",
            description="Async implementation",
            code_example="async def fetch(): await client.get()",
            quality_score=70.0,
            source_repo="https://github.com/user/async-repo",
            file_path="async.py",
        )

        sync_skill = Skill(
            name="Sync API",
            description="Sync implementation",
            code_example="def fetch(): return client.get()",
            quality_score=70.0,
            source_repo="https://github.com/user/sync-repo",
            file_path="sync.py",
        )

        result = await comparator.compare([async_skill, sync_skill])

        async_perf = result.dimension_scores[async_skill.source_repo]["performance"]
        sync_perf = result.dimension_scores[sync_skill.source_repo]["performance"]
        assert async_perf > sync_perf

    @pytest.mark.asyncio
    async def test_higher_score_for_error_handling(self, comparator):
        """Should give higher quality score for error handling."""
        with_errors = Skill(
            name="With Errors",
            description="Has error handling",
            code_example="try: call() except Exception: handle()",
            quality_score=70.0,
            source_repo="https://github.com/user/with-errors",
            file_path="errors.py",
        )

        without_errors = Skill(
            name="Without Errors",
            description="No error handling",
            code_example="call()",
            quality_score=70.0,
            source_repo="https://github.com/user/without-errors",
            file_path="no_errors.py",
        )

        result = await comparator.compare([with_errors, without_errors])

        with_quality = result.dimension_scores[with_errors.source_repo]["quality"]
        without_quality = result.dimension_scores[without_errors.source_repo]["quality"]
        assert with_quality > without_quality


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_compare_single_skill(self, comparator, high_quality_skill):
        """Should handle single skill comparison."""
        result = await comparator.compare([high_quality_skill])

        assert len(result.ranked_skills) == 1
        assert result.best_skill == high_quality_skill
        assert high_quality_skill.source_repo in result.dimension_scores

    @pytest.mark.asyncio
    async def test_compare_empty_list(self, comparator):
        """Should handle empty skill list."""
        result = await comparator.compare([])

        assert len(result.ranked_skills) == 0
        assert result.best_skill is None
        assert len(result.dimension_scores) == 0

    @pytest.mark.asyncio
    async def test_compare_identical_skills(self, comparator):
        """Should handle skills with identical scores."""
        skill1 = Skill(
            name="Same",
            description="Same description",
            code_example="same code",
            quality_score=70.0,
            source_repo="https://github.com/user/repo1",
            file_path="file1.py",
        )

        skill2 = Skill(
            name="Same",
            description="Same description",
            code_example="same code",
            quality_score=70.0,
            source_repo="https://github.com/user/repo2",
            file_path="file2.py",
        )

        result = await comparator.compare([skill1, skill2])

        # Should still rank them (order may vary)
        assert len(result.ranked_skills) == 2
        assert result.best_skill in [skill1, skill2]
