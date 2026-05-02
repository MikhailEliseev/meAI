"""Unit tests for Quality Updater"""

import pytest
from unittest.mock import AsyncMock, patch

from meai.learning.quality_updater import QualityUpdater
from meai.learning.experience_tracker import ExperienceTracker


@pytest.mark.asyncio
async def test_quality_updater_initialization():
    """Test QualityUpdater can be initialized"""
    tracker = ExperienceTracker(database_url="sqlite+aiosqlite:///:memory:")
    await tracker.initialize()

    updater = QualityUpdater(
        experience_tracker=tracker,
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await updater.initialize()

    assert updater is not None

    await updater.shutdown()
    await tracker.shutdown()


@pytest.mark.asyncio
async def test_calculate_new_quality_score():
    """Test calculating new quality score based on experience"""
    tracker = ExperienceTracker(database_url="sqlite+aiosqlite:///:memory:")
    await tracker.initialize()

    updater = QualityUpdater(
        experience_tracker=tracker,
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await updater.initialize()

    # Record experiences
    for i in range(10):
        outcome = "success" if i < 8 else "failure"
        score = 0.9 if i < 8 else 0.2

        await tracker.record_experience(
            magister_id="seo-magister-1",
            task_id=f"task-{i}",
            knowledge_ids=["knowledge-test"],
            outcome=outcome,
            outcome_score=score,
        )

    # Calculate new quality score
    # Original: 7.0, Success rate: 0.8, Avg score: 0.74
    new_score = await updater.calculate_new_quality_score(
        knowledge_id="knowledge-test",
        current_score=7.0,
    )

    # Should increase (good performance)
    assert new_score > 7.0
    assert new_score <= 10.0

    await updater.shutdown()
    await tracker.shutdown()


@pytest.mark.asyncio
async def test_update_knowledge_quality():
    """Test updating knowledge quality in Teacher"""
    tracker = ExperienceTracker(database_url="sqlite+aiosqlite:///:memory:")
    await tracker.initialize()

    updater = QualityUpdater(
        experience_tracker=tracker,
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await updater.initialize()

    # Record good experiences
    for i in range(5):
        await tracker.record_experience(
            magister_id="seo-magister-1",
            task_id=f"task-{i}",
            knowledge_ids=["knowledge-test"],
            outcome="success",
            outcome_score=0.9,
        )

    # Mock Teacher update
    with patch.object(updater, '_update_teacher_quality', new_callable=AsyncMock) as mock_update:
        mock_update.return_value = True

        # Update quality
        result = await updater.update_knowledge_quality(
            knowledge_id="knowledge-test",
            current_score=7.0,
        )

        assert result["updated"] is True
        assert result["new_score"] > 7.0
        mock_update.assert_called_once()

    await updater.shutdown()
    await tracker.shutdown()


@pytest.mark.asyncio
async def test_quality_decrease_on_poor_performance():
    """Test quality decreases with poor performance"""
    tracker = ExperienceTracker(database_url="sqlite+aiosqlite:///:memory:")
    await tracker.initialize()

    updater = QualityUpdater(
        experience_tracker=tracker,
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await updater.initialize()

    # Record poor experiences
    for i in range(10):
        await tracker.record_experience(
            magister_id="seo-magister-1",
            task_id=f"task-{i}",
            knowledge_ids=["knowledge-test"],
            outcome="failure",
            outcome_score=0.2,
        )

    # Calculate new quality score
    new_score = await updater.calculate_new_quality_score(
        knowledge_id="knowledge-test",
        current_score=8.0,
    )

    # Should decrease (poor performance)
    assert new_score < 8.0
    assert new_score >= 1.0  # Minimum score

    await updater.shutdown()
    await tracker.shutdown()


@pytest.mark.asyncio
async def test_batch_update_qualities():
    """Test batch updating multiple knowledge items"""
    tracker = ExperienceTracker(database_url="sqlite+aiosqlite:///:memory:")
    await tracker.initialize()

    updater = QualityUpdater(
        experience_tracker=tracker,
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await updater.initialize()

    # Record experiences for multiple knowledge items
    for knowledge_id in ["knowledge-1", "knowledge-2", "knowledge-3"]:
        for i in range(5):
            await tracker.record_experience(
                magister_id="seo-magister-1",
                task_id=f"task-{knowledge_id}-{i}",
                knowledge_ids=[knowledge_id],
                outcome="success",
                outcome_score=0.8,
            )

    # Mock Teacher updates
    with patch.object(updater, '_update_teacher_quality', new_callable=AsyncMock) as mock_update:
        mock_update.return_value = True

        # Batch update
        knowledge_items = [
            {"id": "knowledge-1", "current_score": 7.0},
            {"id": "knowledge-2", "current_score": 6.5},
            {"id": "knowledge-3", "current_score": 8.0},
        ]

        results = await updater.batch_update_qualities(knowledge_items)

        assert len(results) == 3
        assert all(r["updated"] for r in results)
        assert mock_update.call_count == 3

    await updater.shutdown()
    await tracker.shutdown()


@pytest.mark.asyncio
async def test_get_quality_update_recommendations():
    """Test getting recommendations for quality updates"""
    tracker = ExperienceTracker(database_url="sqlite+aiosqlite:///:memory:")
    await tracker.initialize()

    updater = QualityUpdater(
        experience_tracker=tracker,
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await updater.initialize()

    # Record experiences with varying performance
    # Good performance
    for i in range(10):
        await tracker.record_experience(
            magister_id="seo-magister-1",
            task_id=f"task-good-{i}",
            knowledge_ids=["knowledge-good"],
            outcome="success",
            outcome_score=0.9,
        )

    # Poor performance
    for i in range(10):
        await tracker.record_experience(
            magister_id="seo-magister-1",
            task_id=f"task-poor-{i}",
            knowledge_ids=["knowledge-poor"],
            outcome="failure",
            outcome_score=0.2,
        )

    # Get recommendations
    recommendations = await updater.get_quality_update_recommendations(
        min_usage_count=5,
    )

    assert len(recommendations) >= 2
    assert any(r["knowledge_id"] == "knowledge-good" for r in recommendations)
    assert any(r["knowledge_id"] == "knowledge-poor" for r in recommendations)

    await updater.shutdown()
    await tracker.shutdown()
