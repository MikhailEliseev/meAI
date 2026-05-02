"""Unit tests for Experience Tracker"""

import pytest
from datetime import datetime, timezone

from meai.learning.experience_tracker import ExperienceTracker


@pytest.mark.asyncio
async def test_experience_tracker_initialization():
    """Test ExperienceTracker can be initialized"""
    tracker = ExperienceTracker(database_url="sqlite+aiosqlite:///:memory:")

    await tracker.initialize()

    assert tracker is not None

    await tracker.shutdown()


@pytest.mark.asyncio
async def test_record_experience():
    """Test recording task experience"""
    tracker = ExperienceTracker(database_url="sqlite+aiosqlite:///:memory:")
    await tracker.initialize()

    # Record successful experience
    experience_id = await tracker.record_experience(
        magister_id="seo-magister-1",
        task_id="task-123",
        knowledge_ids=["knowledge-1", "knowledge-2"],
        outcome="success",
        outcome_score=0.9,
        feedback="Task completed successfully",
    )

    assert experience_id is not None
    assert experience_id.startswith("exp-")

    await tracker.shutdown()


@pytest.mark.asyncio
async def test_get_knowledge_success_rate():
    """Test calculating knowledge success rate"""
    tracker = ExperienceTracker(database_url="sqlite+aiosqlite:///:memory:")
    await tracker.initialize()

    # Record multiple experiences
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

    # Calculate success rate
    success_rate = await tracker.get_knowledge_success_rate("knowledge-test")

    assert success_rate == 0.8  # 8 out of 10

    await tracker.shutdown()


@pytest.mark.asyncio
async def test_get_knowledge_average_score():
    """Test calculating average outcome score"""
    tracker = ExperienceTracker(database_url="sqlite+aiosqlite:///:memory:")
    await tracker.initialize()

    # Record experiences with different scores
    scores = [0.9, 0.8, 0.7, 0.6, 0.5]

    for i, score in enumerate(scores):
        await tracker.record_experience(
            magister_id="seo-magister-1",
            task_id=f"task-{i}",
            knowledge_ids=["knowledge-test"],
            outcome="success",
            outcome_score=score,
        )

    # Calculate average score
    avg_score = await tracker.get_knowledge_average_score("knowledge-test")

    assert avg_score == 0.7  # (0.9 + 0.8 + 0.7 + 0.6 + 0.5) / 5

    await tracker.shutdown()


@pytest.mark.asyncio
async def test_get_knowledge_usage_count():
    """Test counting knowledge usage"""
    tracker = ExperienceTracker(database_url="sqlite+aiosqlite:///:memory:")
    await tracker.initialize()

    # Record multiple uses
    for i in range(5):
        await tracker.record_experience(
            magister_id="seo-magister-1",
            task_id=f"task-{i}",
            knowledge_ids=["knowledge-test"],
            outcome="success",
            outcome_score=0.8,
        )

    # Get usage count
    usage_count = await tracker.get_knowledge_usage_count("knowledge-test")

    assert usage_count == 5

    await tracker.shutdown()


@pytest.mark.asyncio
async def test_get_magister_experiences():
    """Test getting all experiences for a Magister"""
    tracker = ExperienceTracker(database_url="sqlite+aiosqlite:///:memory:")
    await tracker.initialize()

    # Record experiences for different Magisters
    await tracker.record_experience(
        magister_id="seo-magister-1",
        task_id="task-1",
        knowledge_ids=["knowledge-1"],
        outcome="success",
        outcome_score=0.9,
    )

    await tracker.record_experience(
        magister_id="seo-magister-1",
        task_id="task-2",
        knowledge_ids=["knowledge-2"],
        outcome="failure",
        outcome_score=0.3,
    )

    await tracker.record_experience(
        magister_id="content-magister-1",
        task_id="task-3",
        knowledge_ids=["knowledge-3"],
        outcome="success",
        outcome_score=0.8,
    )

    # Get SEO Magister experiences
    experiences = await tracker.get_magister_experiences("seo-magister-1")

    assert len(experiences) == 2
    assert all(exp["magister_id"] == "seo-magister-1" for exp in experiences)

    await tracker.shutdown()


@pytest.mark.asyncio
async def test_get_recent_experiences():
    """Test getting recent experiences"""
    tracker = ExperienceTracker(database_url="sqlite+aiosqlite:///:memory:")
    await tracker.initialize()

    # Record multiple experiences
    for i in range(15):
        await tracker.record_experience(
            magister_id="seo-magister-1",
            task_id=f"task-{i}",
            knowledge_ids=[f"knowledge-{i}"],
            outcome="success",
            outcome_score=0.8,
        )

    # Get recent experiences (limit 10)
    recent = await tracker.get_recent_experiences(limit=10)

    assert len(recent) == 10

    await tracker.shutdown()
