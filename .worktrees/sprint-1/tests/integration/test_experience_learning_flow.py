"""Integration test: Complete experience learning flow"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from meai.learning.experience_tracker import ExperienceTracker
from meai.learning.quality_updater import QualityUpdater
from meai.learning.deprecation_manager import DeprecationManager
from meai.learning.learning_analytics import LearningAnalytics


@pytest.mark.asyncio
async def test_complete_learning_flow():
    """Test complete experience learning flow

    Scenario:
    1. Magister uses knowledge in tasks
    2. ExperienceTracker records outcomes
    3. QualityUpdater adjusts quality scores
    4. DeprecationManager deprecates poor performers
    5. LearningAnalytics provides insights
    """
    # Initialize components
    tracker = ExperienceTracker(database_url="sqlite+aiosqlite:///:memory:")
    await tracker.initialize()

    updater = QualityUpdater(
        experience_tracker=tracker,
        database_url="sqlite+aiosqlite:///:memory:",
    )
    await updater.initialize()

    deprecation = DeprecationManager(
        experience_tracker=tracker,
        database_url="sqlite+aiosqlite:///:memory:",
    )
    await deprecation.initialize()

    analytics = LearningAnalytics(
        experience_tracker=tracker,
        quality_updater=updater,
        deprecation_manager=deprecation,
    )

    # Step 1: Record experiences for good knowledge
    for i in range(20):
        await tracker.record_experience(
            magister_id="seo-magister-1",
            task_id=f"task-good-{i}",
            knowledge_ids=["knowledge-good"],
            outcome="success",
            outcome_score=0.9,
        )

    # Step 2: Record experiences for poor knowledge
    for i in range(20):
        await tracker.record_experience(
            magister_id="seo-magister-1",
            task_id=f"task-poor-{i}",
            knowledge_ids=["knowledge-poor"],
            outcome="failure",
            outcome_score=0.2,
        )

    # Step 3: Update quality scores
    with patch.object(updater, '_update_teacher_quality', new_callable=AsyncMock) as mock_update:
        mock_update.return_value = True

        # Update good knowledge (should increase)
        good_result = await updater.update_knowledge_quality(
            knowledge_id="knowledge-good",
            current_score=7.0,
        )

        assert good_result["new_score"] > 7.0
        assert good_result["adjustment"] > 0

        # Update poor knowledge (should decrease)
        poor_result = await updater.update_knowledge_quality(
            knowledge_id="knowledge-poor",
            current_score=7.0,
        )

        assert poor_result["new_score"] < 7.0
        assert poor_result["adjustment"] < 0

    # Step 4: Check deprecation
    should_deprecate_good, _ = await deprecation.should_deprecate(
        knowledge_id="knowledge-good",
        current_quality=good_result["new_score"],
    )
    assert should_deprecate_good is False

    should_deprecate_poor, reason = await deprecation.should_deprecate(
        knowledge_id="knowledge-poor",
        current_quality=poor_result["new_score"],
    )
    assert should_deprecate_poor is True

    # Step 5: Deprecate poor knowledge
    deprecation_result = await deprecation.deprecate_knowledge(
        knowledge_id="knowledge-poor",
        reason=reason,
        current_quality=poor_result["new_score"],
    )
    assert deprecation_result["deprecated"] is True

    # Step 6: Get analytics
    health = await analytics.get_system_health()
    assert health["overall_success_rate"] == 0.5  # 50% success (20 good, 20 poor)
    assert health["active_deprecated"] == 1

    # Good knowledge report
    good_report = await analytics.get_knowledge_performance_report("knowledge-good")
    assert good_report["performance_grade"] in ["A", "B"]
    assert good_report["usage_stats"]["success_rate"] == 1.0

    # Poor knowledge report
    poor_report = await analytics.get_knowledge_performance_report("knowledge-poor")
    assert poor_report["performance_grade"] == "F"
    assert poor_report["deprecation_info"] is not None
    assert poor_report["deprecation_info"]["active"] is True

    # Cleanup
    await tracker.shutdown()
    await updater.shutdown()
    await deprecation.shutdown()


@pytest.mark.asyncio
async def test_quality_improvement_cycle():
    """Test quality improvement over multiple cycles

    Scenario:
    1. Knowledge starts with poor performance
    2. Quality decreases, gets deprecated
    3. Knowledge is updated (externally)
    4. New experiences show improvement
    5. Quality increases, gets undeprecated
    """
    tracker = ExperienceTracker(database_url="sqlite+aiosqlite:///:memory:")
    await tracker.initialize()

    updater = QualityUpdater(
        experience_tracker=tracker,
        database_url="sqlite+aiosqlite:///:memory:",
    )
    await updater.initialize()

    deprecation = DeprecationManager(
        experience_tracker=tracker,
        database_url="sqlite+aiosqlite:///:memory:",
    )
    await deprecation.initialize()

    # Cycle 1: Poor performance
    for i in range(20):
        await tracker.record_experience(
            magister_id="seo-magister-1",
            task_id=f"task-cycle1-{i}",
            knowledge_ids=["knowledge-improving"],
            outcome="failure",
            outcome_score=0.2,
        )

    # Update quality (should decrease)
    with patch.object(updater, '_update_teacher_quality', new_callable=AsyncMock) as mock_update:
        mock_update.return_value = True

        result1 = await updater.update_knowledge_quality(
            knowledge_id="knowledge-improving",
            current_score=7.0,
        )

        assert result1["new_score"] < 7.0

    # Deprecate
    await deprecation.deprecate_knowledge(
        knowledge_id="knowledge-improving",
        reason="Poor performance in cycle 1",
        current_quality=result1["new_score"],
    )

    # Cycle 2: Improved performance (after knowledge update)
    for i in range(20):
        await tracker.record_experience(
            magister_id="seo-magister-1",
            task_id=f"task-cycle2-{i}",
            knowledge_ids=["knowledge-improving"],
            outcome="success",
            outcome_score=0.9,
        )

    # Update quality (should increase)
    with patch.object(updater, '_update_teacher_quality', new_callable=AsyncMock) as mock_update:
        mock_update.return_value = True

        result2 = await updater.update_knowledge_quality(
            knowledge_id="knowledge-improving",
            current_score=result1["new_score"],
        )

        assert result2["new_score"] > result1["new_score"]

    # Check if should undeprecate
    should_deprecate, _ = await deprecation.should_deprecate(
        knowledge_id="knowledge-improving",
        current_quality=result2["new_score"],
    )

    if not should_deprecate:
        # Undeprecate
        undeprecate_result = await deprecation.undeprecate_knowledge(
            knowledge_id="knowledge-improving",
            reason="Quality improved after update",
        )
        assert undeprecate_result["undeprecated"] is True

    # Cleanup
    await tracker.shutdown()
    await updater.shutdown()
    await deprecation.shutdown()


@pytest.mark.asyncio
async def test_batch_quality_updates():
    """Test batch quality updates for multiple knowledge items"""
    tracker = ExperienceTracker(database_url="sqlite+aiosqlite:///:memory:")
    await tracker.initialize()

    updater = QualityUpdater(
        experience_tracker=tracker,
        database_url="sqlite+aiosqlite:///:memory:",
    )
    await updater.initialize()

    # Create experiences for multiple knowledge items
    knowledge_items = ["knowledge-1", "knowledge-2", "knowledge-3"]

    for knowledge_id in knowledge_items:
        # Varying performance
        success_rate = 0.5 + (int(knowledge_id[-1]) * 0.2)

        for i in range(20):
            outcome = "success" if i < (20 * success_rate) else "failure"
            score = 0.9 if outcome == "success" else 0.2

            await tracker.record_experience(
                magister_id="seo-magister-1",
                task_id=f"task-{knowledge_id}-{i}",
                knowledge_ids=[knowledge_id],
                outcome=outcome,
                outcome_score=score,
            )

    # Batch update
    with patch.object(updater, '_update_teacher_quality', new_callable=AsyncMock) as mock_update:
        mock_update.return_value = True

        items = [
            {"id": "knowledge-1", "current_score": 7.0},
            {"id": "knowledge-2", "current_score": 7.0},
            {"id": "knowledge-3", "current_score": 7.0},
        ]

        results = await updater.batch_update_qualities(items)

        assert len(results) == 3

        # knowledge-1: 50% success → should decrease
        assert results[0]["new_score"] < 7.0

        # knowledge-2: 70% success → should stay similar or increase slightly
        # knowledge-3: 90% success → should increase
        assert results[2]["new_score"] > results[1]["new_score"]

    # Cleanup
    await tracker.shutdown()
    await updater.shutdown()


@pytest.mark.asyncio
async def test_auto_deprecation_workflow():
    """Test automatic deprecation workflow"""
    tracker = ExperienceTracker(database_url="sqlite+aiosqlite:///:memory:")
    await tracker.initialize()

    deprecation = DeprecationManager(
        experience_tracker=tracker,
        database_url="sqlite+aiosqlite:///:memory:",
    )
    await deprecation.initialize()

    # Create multiple knowledge items with varying performance
    # Poor performers
    for knowledge_id in ["poor-1", "poor-2"]:
        for i in range(25):
            await tracker.record_experience(
                magister_id="seo-magister-1",
                task_id=f"task-{knowledge_id}-{i}",
                knowledge_ids=[knowledge_id],
                outcome="failure",
                outcome_score=0.1,
            )

    # Good performers
    for knowledge_id in ["good-1", "good-2"]:
        for i in range(25):
            await tracker.record_experience(
                magister_id="seo-magister-1",
                task_id=f"task-{knowledge_id}-{i}",
                knowledge_ids=[knowledge_id],
                outcome="success",
                outcome_score=0.9,
            )

    # Scan for candidates
    candidates = await deprecation.scan_for_deprecation_candidates(min_usage_count=20)

    # Should find poor performers
    assert len(candidates) >= 2
    poor_candidates = [c for c in candidates if c["knowledge_id"].startswith("poor-")]
    assert len(poor_candidates) == 2

    # Auto-deprecate (dry run first)
    dry_run_results = await deprecation.auto_deprecate_low_performers(
        min_usage_count=20,
        dry_run=True,
    )

    assert len(dry_run_results) >= 2

    # Auto-deprecate (real)
    real_results = await deprecation.auto_deprecate_low_performers(
        min_usage_count=20,
        dry_run=False,
    )

    assert len(real_results) >= 2
    assert all(r["deprecated"] for r in real_results)

    # Verify deprecated
    deprecated = await deprecation.get_deprecated_knowledge()
    assert len(deprecated) >= 2

    # Cleanup
    await tracker.shutdown()
    await deprecation.shutdown()


@pytest.mark.asyncio
async def test_learning_analytics_insights():
    """Test learning analytics insights"""
    tracker = ExperienceTracker(database_url="sqlite+aiosqlite:///:memory:")
    await tracker.initialize()

    updater = QualityUpdater(
        experience_tracker=tracker,
        database_url="sqlite+aiosqlite:///:memory:",
    )
    await updater.initialize()

    deprecation = DeprecationManager(
        experience_tracker=tracker,
        database_url="sqlite+aiosqlite:///:memory:",
    )
    await deprecation.initialize()

    analytics = LearningAnalytics(
        experience_tracker=tracker,
        quality_updater=updater,
        deprecation_manager=deprecation,
    )

    # Create diverse experiences
    for i in range(50):
        knowledge_id = f"knowledge-{i % 5}"
        outcome = "success" if i % 3 != 0 else "failure"
        score = 0.8 if outcome == "success" else 0.3

        await tracker.record_experience(
            magister_id="seo-magister-1",
            task_id=f"task-{i}",
            knowledge_ids=[knowledge_id],
            outcome=outcome,
            outcome_score=score,
        )

    # System health
    health = await analytics.get_system_health()
    assert "overall_success_rate" in health
    assert "health_score" in health
    assert 0 <= health["health_score"] <= 10

    # Magister performance
    magister_report = await analytics.get_magister_performance_report("seo-magister-1")
    assert magister_report["total_tasks"] == 50
    assert "performance_grade" in magister_report

    # Top performers
    top_performers = await analytics.get_top_performing_knowledge(limit=3, min_usage=5)
    assert len(top_performers) > 0
    assert all("performance_score" in p for p in top_performers)

    # Cleanup
    await tracker.shutdown()
    await updater.shutdown()
    await deprecation.shutdown()
