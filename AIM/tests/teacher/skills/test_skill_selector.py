"""
Tests for SkillSelector.
"""

import pytest

from AIM.src.aim.teacher.skills.skill_extractor import (
    ExtractedSkill,
    SkillType,
)
from AIM.src.aim.teacher.skills.skill_comparator import (
    SkillComparator,
    SkillScore,
    ComparisonResult,
)
from AIM.src.aim.teacher.skills.skill_selector import (
    SkillSelector,
    SelectionCriteria,
    SelectedSkill,
)


@pytest.fixture
def selector():
    """Create SkillSelector with default criteria."""
    return SkillSelector()


@pytest.fixture
def high_quality_comparison():
    """High quality GitHub skill (should be selected)."""
    github_score = SkillScore(
        skill_type=SkillType.CIRCUIT_BREAKER,
        source="github",
        completeness=90.0,
        quality=85.0,
        performance=80.0,
        maintainability=85.0,
        security=90.0,
        total_score=87.0,
        strengths=["completeness", "quality", "security"],
        weaknesses=[],
        metadata={},
    )

    our_score = SkillScore(
        skill_type=SkillType.CIRCUIT_BREAKER,
        source="ours",
        completeness=60.0,
        quality=55.0,
        performance=50.0,
        maintainability=60.0,
        security=65.0,
        total_score=59.0,
        strengths=[],
        weaknesses=["quality", "performance"],
        metadata={},
    )

    return ComparisonResult(
        skill_type=SkillType.CIRCUIT_BREAKER,
        github_score=github_score,
        our_score=our_score,
        recommendation="adopt",
        gap_analysis="Significant gaps in quality and security",
        action_items=["Adopt GitHub implementation"],
    )


@pytest.fixture
def low_quality_comparison():
    """Low quality GitHub skill (should be filtered out)."""
    github_score = SkillScore(
        skill_type=SkillType.RETRY,
        source="github",
        completeness=50.0,
        quality=45.0,
        performance=40.0,
        maintainability=50.0,
        security=55.0,
        total_score=48.0,
        strengths=[],
        weaknesses=["quality", "performance"],
        metadata={},
    )

    our_score = SkillScore(
        skill_type=SkillType.RETRY,
        source="ours",
        completeness=45.0,
        quality=40.0,
        performance=35.0,
        maintainability=45.0,
        security=50.0,
        total_score=43.0,
        strengths=[],
        weaknesses=["quality", "performance"],
        metadata={},
    )

    return ComparisonResult(
        skill_type=SkillType.RETRY,
        github_score=github_score,
        our_score=our_score,
        recommendation="improve",
        gap_analysis="Minor improvements",
        action_items=["Improve quality"],
    )


@pytest.fixture
def medium_quality_comparison():
    """Medium quality GitHub skill (borderline)."""
    github_score = SkillScore(
        skill_type=SkillType.CACHING,
        source="github",
        completeness=75.0,
        quality=70.0,
        performance=65.0,
        maintainability=70.0,
        security=75.0,
        total_score=72.0,
        strengths=["completeness", "security"],
        weaknesses=[],
        metadata={},
    )

    our_score = SkillScore(
        skill_type=SkillType.CACHING,
        source="ours",
        completeness=60.0,
        quality=55.0,
        performance=50.0,
        maintainability=60.0,
        security=65.0,
        total_score=59.0,
        strengths=[],
        weaknesses=["quality", "performance"],
        metadata={},
    )

    return ComparisonResult(
        skill_type=SkillType.CACHING,
        github_score=github_score,
        our_score=our_score,
        recommendation="improve",
        gap_analysis="Some gaps in quality",
        action_items=["Improve quality and performance"],
    )


@pytest.mark.asyncio
async def test_select_high_quality_skills(selector, high_quality_comparison):
    """Test selecting high quality skills."""
    selected = selector.select_skills([high_quality_comparison])

    assert len(selected) == 1
    assert selected[0].comparison.skill_type == SkillType.CIRCUIT_BREAKER
    assert selected[0].priority == 1


@pytest.mark.asyncio
async def test_filter_low_quality_skills(selector, low_quality_comparison):
    """Test filtering out low quality skills."""
    selected = selector.select_skills([low_quality_comparison])

    # Should be filtered out (score < 70)
    assert len(selected) == 0


@pytest.mark.asyncio
async def test_select_medium_quality_skills(selector, medium_quality_comparison):
    """Test selecting medium quality skills."""
    selected = selector.select_skills([medium_quality_comparison])

    # Should pass (score >= 70, improvement >= 10)
    assert len(selected) == 1
    assert selected[0].comparison.skill_type == SkillType.CACHING


@pytest.mark.asyncio
async def test_priority_ranking(selector, high_quality_comparison, medium_quality_comparison):
    """Test priority ranking (high quality first)."""
    selected = selector.select_skills([
        medium_quality_comparison,
        high_quality_comparison,
    ])

    assert len(selected) == 2
    # High quality should be priority 1
    assert selected[0].comparison.skill_type == SkillType.CIRCUIT_BREAKER
    assert selected[0].priority == 1
    # Medium quality should be priority 2
    assert selected[1].comparison.skill_type == SkillType.CACHING
    assert selected[1].priority == 2


@pytest.mark.asyncio
async def test_custom_threshold():
    """Test custom score threshold."""
    criteria = SelectionCriteria(
        min_score_threshold=80.0,  # Higher threshold
        min_improvement_threshold=10.0,
    )
    selector = SkillSelector(criteria=criteria)

    # Create comparison with score 75 (below threshold)
    github_score = SkillScore(
        skill_type=SkillType.RATE_LIMITING,
        source="github",
        completeness=75.0,
        quality=75.0,
        performance=75.0,
        maintainability=75.0,
        security=75.0,
        total_score=75.0,
        strengths=[],
        weaknesses=[],
        metadata={},
    )

    our_score = SkillScore(
        skill_type=SkillType.RATE_LIMITING,
        source="ours",
        completeness=60.0,
        quality=60.0,
        performance=60.0,
        maintainability=60.0,
        security=60.0,
        total_score=60.0,
        strengths=[],
        weaknesses=[],
        metadata={},
    )

    comparison = ComparisonResult(
        skill_type=SkillType.RATE_LIMITING,
        github_score=github_score,
        our_score=our_score,
        recommendation="improve",
        gap_analysis="Some gaps",
        action_items=["Improve"],
    )

    selected = selector.select_skills([comparison])

    # Should be filtered out (75 < 80)
    assert len(selected) == 0


@pytest.mark.asyncio
async def test_improvement_threshold():
    """Test improvement threshold filtering."""
    criteria = SelectionCriteria(
        min_score_threshold=70.0,
        min_improvement_threshold=20.0,  # Higher improvement required
    )
    selector = SkillSelector(criteria=criteria)

    # Create comparison with small improvement (15 points)
    github_score = SkillScore(
        skill_type=SkillType.ERROR_HANDLING,
        source="github",
        completeness=75.0,
        quality=75.0,
        performance=75.0,
        maintainability=75.0,
        security=75.0,
        total_score=75.0,
        strengths=[],
        weaknesses=[],
        metadata={},
    )

    our_score = SkillScore(
        skill_type=SkillType.ERROR_HANDLING,
        source="ours",
        completeness=60.0,
        quality=60.0,
        performance=60.0,
        maintainability=60.0,
        security=60.0,
        total_score=60.0,
        strengths=[],
        weaknesses=[],
        metadata={},
    )

    comparison = ComparisonResult(
        skill_type=SkillType.ERROR_HANDLING,
        github_score=github_score,
        our_score=our_score,
        recommendation="improve",
        gap_analysis="Some gaps",
        action_items=["Improve"],
    )

    selected = selector.select_skills([comparison])

    # Should be filtered out (improvement 15 < 20)
    assert len(selected) == 0


@pytest.mark.asyncio
async def test_budget_limit():
    """Test budget limit (max skills to select)."""
    criteria = SelectionCriteria(
        min_score_threshold=70.0,
        min_improvement_threshold=10.0,
        budget_limit=2,  # Only select top 2
    )
    selector = SkillSelector(criteria=criteria)

    # Create 3 high quality comparisons
    comparisons = []
    for i, skill_type in enumerate([SkillType.CIRCUIT_BREAKER, SkillType.RETRY, SkillType.CACHING]):
        github_score = SkillScore(
            skill_type=skill_type,
            source="github",
            completeness=80.0 + i * 5,
            quality=80.0 + i * 5,
            performance=80.0 + i * 5,
            maintainability=80.0 + i * 5,
            security=80.0 + i * 5,
            total_score=80.0 + i * 5,
            strengths=[],
            weaknesses=[],
            metadata={},
        )

        our_score = SkillScore(
            skill_type=skill_type,
            source="ours",
            completeness=60.0,
            quality=60.0,
            performance=60.0,
            maintainability=60.0,
            security=60.0,
            total_score=60.0,
            strengths=[],
            weaknesses=[],
            metadata={},
        )

        comparison = ComparisonResult(
            skill_type=skill_type,
            github_score=github_score,
            our_score=our_score,
            recommendation="adopt",
            gap_analysis="Gaps",
            action_items=["Adopt"],
        )
        comparisons.append(comparison)

    selected = selector.select_skills(comparisons)

    # Should only select top 2
    assert len(selected) == 2
    # Should be highest scores (CACHING and RETRY)
    assert selected[0].comparison.skill_type == SkillType.CACHING
    assert selected[1].comparison.skill_type == SkillType.RETRY


@pytest.mark.asyncio
async def test_max_skills_per_type():
    """Test max skills per type limit."""
    criteria = SelectionCriteria(
        min_score_threshold=70.0,
        min_improvement_threshold=10.0,
        max_skills_per_type=2,  # Max 2 per type
    )
    selector = SkillSelector(criteria=criteria)

    # Create 3 circuit breaker comparisons
    comparisons = []
    for i in range(3):
        github_score = SkillScore(
            skill_type=SkillType.CIRCUIT_BREAKER,
            source="github",
            completeness=80.0 + i * 5,
            quality=80.0 + i * 5,
            performance=80.0 + i * 5,
            maintainability=80.0 + i * 5,
            security=80.0 + i * 5,
            total_score=80.0 + i * 5,
            strengths=[],
            weaknesses=[],
            metadata={},
        )

        our_score = SkillScore(
            skill_type=SkillType.CIRCUIT_BREAKER,
            source="ours",
            completeness=60.0,
            quality=60.0,
            performance=60.0,
            maintainability=60.0,
            security=60.0,
            total_score=60.0,
            strengths=[],
            weaknesses=[],
            metadata={},
        )

        comparison = ComparisonResult(
            skill_type=SkillType.CIRCUIT_BREAKER,
            github_score=github_score,
            our_score=our_score,
            recommendation="adopt",
            gap_analysis="Gaps",
            action_items=["Adopt"],
        )
        comparisons.append(comparison)

    selected = selector.select_skills(comparisons)

    # Should only select top 2 circuit breakers
    assert len(selected) == 2
    assert all(s.comparison.skill_type == SkillType.CIRCUIT_BREAKER for s in selected)


@pytest.mark.asyncio
async def test_security_prioritization():
    """Test security prioritization."""
    criteria = SelectionCriteria(
        min_score_threshold=70.0,
        min_improvement_threshold=10.0,
        prioritize_security=True,
    )
    selector = SkillSelector(criteria=criteria)

    # Create two comparisons: one with high security, one with high quality
    high_security = SkillScore(
        skill_type=SkillType.CIRCUIT_BREAKER,
        source="github",
        completeness=75.0,
        quality=70.0,
        performance=70.0,
        maintainability=70.0,
        security=95.0,  # Very high security
        total_score=75.0,
        strengths=["security"],
        weaknesses=[],
        metadata={},
    )

    high_quality = SkillScore(
        skill_type=SkillType.RETRY,
        source="github",
        completeness=85.0,
        quality=90.0,  # Very high quality
        performance=80.0,
        maintainability=85.0,
        security=70.0,
        total_score=82.0,  # Higher total score
        strengths=["quality"],
        weaknesses=[],
        metadata={},
    )

    our_score = SkillScore(
        skill_type=SkillType.CIRCUIT_BREAKER,
        source="ours",
        completeness=60.0,
        quality=60.0,
        performance=60.0,
        maintainability=60.0,
        security=60.0,
        total_score=60.0,
        strengths=[],
        weaknesses=[],
        metadata={},
    )

    comp1 = ComparisonResult(
        skill_type=SkillType.CIRCUIT_BREAKER,
        github_score=high_security,
        our_score=our_score,
        recommendation="adopt",
        gap_analysis="Gaps",
        action_items=["Adopt"],
    )

    comp2 = ComparisonResult(
        skill_type=SkillType.RETRY,
        github_score=high_quality,
        our_score=our_score,
        recommendation="adopt",
        gap_analysis="Gaps",
        action_items=["Adopt"],
    )

    selected = selector.select_skills([comp1, comp2])

    # High security should be priority 1 (despite lower total score)
    assert len(selected) == 2
    assert selected[0].comparison.skill_type == SkillType.CIRCUIT_BREAKER
    assert selected[0].priority == 1


@pytest.mark.asyncio
async def test_selection_reason_generation(selector, high_quality_comparison):
    """Test selection reason generation."""
    selected = selector.select_skills([high_quality_comparison])

    assert len(selected) == 1
    reason = selected[0].selection_reason

    # Should mention quality and improvement
    assert "quality" in reason.lower() or "excellent" in reason.lower()
    assert "improvement" in reason.lower() or "points" in reason.lower()


@pytest.mark.asyncio
async def test_format_selection_report(selector, high_quality_comparison, medium_quality_comparison):
    """Test selection report formatting."""
    selected = selector.select_skills([
        high_quality_comparison,
        medium_quality_comparison,
    ])

    report = selector.format_selection_report(selected)

    assert isinstance(report, str)
    assert "# Skill Selection Report" in report
    assert "**Selected:** 2 skills" in report  # Fixed: uses bold markdown
    assert "Circuit Breaker" in report
    assert "Caching" in report
    assert "Priority Score:" in report
    assert "Action Items:" in report


@pytest.mark.asyncio
async def test_selected_skill_structure(selector, high_quality_comparison):
    """Test SelectedSkill structure."""
    selected = selector.select_skills([high_quality_comparison])

    skill = selected[0]

    assert hasattr(skill, "comparison")
    assert hasattr(skill, "selection_score")
    assert hasattr(skill, "selection_reason")
    assert hasattr(skill, "priority")
    assert hasattr(skill, "metadata")

    assert isinstance(skill.comparison, ComparisonResult)
    assert isinstance(skill.selection_score, float)
    assert isinstance(skill.selection_reason, str)
    assert isinstance(skill.priority, int)
    assert isinstance(skill.metadata, dict)


@pytest.mark.asyncio
async def test_filter_keep_ours_recommendation(selector):
    """Test filtering out 'keep_ours' recommendations."""
    github_score = SkillScore(
        skill_type=SkillType.CIRCUIT_BREAKER,
        source="github",
        completeness=75.0,
        quality=75.0,
        performance=75.0,
        maintainability=75.0,
        security=75.0,
        total_score=75.0,
        strengths=[],
        weaknesses=[],
        metadata={},
    )

    our_score = SkillScore(
        skill_type=SkillType.CIRCUIT_BREAKER,
        source="ours",
        completeness=80.0,
        quality=80.0,
        performance=80.0,
        maintainability=80.0,
        security=80.0,
        total_score=80.0,  # Our implementation is better
        strengths=[],
        weaknesses=[],
        metadata={},
    )

    comparison = ComparisonResult(
        skill_type=SkillType.CIRCUIT_BREAKER,
        github_score=github_score,
        our_score=our_score,
        recommendation="keep_ours",  # Should be filtered
        gap_analysis="Our implementation is better",
        action_items=["Keep ours"],
    )

    selected = selector.select_skills([comparison])

    # Should be filtered out (recommendation is keep_ours)
    assert len(selected) == 0


@pytest.mark.asyncio
async def test_empty_comparisons(selector):
    """Test with empty comparisons list."""
    selected = selector.select_skills([])

    assert len(selected) == 0
