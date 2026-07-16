"""Unit tests for Deprecation Manager"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch

from meai.learning.deprecation_manager import DeprecationManager
from meai.learning.experience_tracker import ExperienceTracker


@pytest.mark.asyncio
async def test_deprecation_manager_initialization():
    """Test DeprecationManager can be initialized"""
    tracker = ExperienceTracker(database_url="sqlite+aiosqlite:///:memory:")
    await tracker.initialize()

    manager = DeprecationManager(
        experience_tracker=tracker,
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await manager.initialize()

    assert manager is not None

    await manager.shutdown()
    await tracker.shutdown()


@pytest.mark.asyncio
async def test_should_deprecate_low_quality():
    """Test deprecation decision for low quality knowledge"""
    tracker = ExperienceTracker(database_url="sqlite+aiosqlite:///:memory:")
    await tracker.initialize()

    manager = DeprecationManager(
        experience_tracker=tracker,
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await manager.initialize()

    # Record poor performance
    for i in range(20):
        await tracker.record_experience(
            magister_id="seo-magister-1",
            task_id=f"task-{i}",
            knowledge_ids=["knowledge-poor"],
            outcome="failure",
            outcome_score=0.2,
        )

    # Check if should deprecate
    should_deprecate, reason = await manager.should_deprecate(
        knowledge_id="knowledge-poor",
        current_quality=3.0,
    )

    assert should_deprecate is True
    assert "low quality" in reason.lower() or "poor performance" in reason.lower()

    await manager.shutdown()
    await tracker.shutdown()


@pytest.mark.asyncio
async def test_should_not_deprecate_good_quality():
    """Test no deprecation for good quality knowledge"""
    tracker = ExperienceTracker(database_url="sqlite+aiosqlite:///:memory:")
    await tracker.initialize()

    manager = DeprecationManager(
        experience_tracker=tracker,
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await manager.initialize()

    # Record good performance
    for i in range(20):
        await tracker.record_experience(
            magister_id="seo-magister-1",
            task_id=f"task-{i}",
            knowledge_ids=["knowledge-good"],
            outcome="success",
            outcome_score=0.9,
        )

    # Check if should deprecate
    should_deprecate, reason = await manager.should_deprecate(
        knowledge_id="knowledge-good",
        current_quality=8.5,
    )

    assert should_deprecate is False

    await manager.shutdown()
    await tracker.shutdown()


@pytest.mark.asyncio
async def test_deprecate_knowledge():
    """Test deprecating knowledge"""
    tracker = ExperienceTracker(database_url="sqlite+aiosqlite:///:memory:")
    await tracker.initialize()

    manager = DeprecationManager(
        experience_tracker=tracker,
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await manager.initialize()

    # Deprecate knowledge
    result = await manager.deprecate_knowledge(
        knowledge_id="knowledge-test",
        reason="Low quality score after 20 uses",
        current_quality=2.5,
    )

    assert result["deprecated"] is True
    assert result["knowledge_id"] == "knowledge-test"
    assert result["reason"] == "Low quality score after 20 uses"

    # Verify in database
    deprecations = await manager.get_deprecated_knowledge()
    assert len(deprecations) == 1
    assert deprecations[0]["knowledge_id"] == "knowledge-test"

    await manager.shutdown()
    await tracker.shutdown()


@pytest.mark.asyncio
async def test_scan_for_deprecation_candidates():
    """Test scanning for deprecation candidates"""
    tracker = ExperienceTracker(database_url="sqlite+aiosqlite:///:memory:")
    await tracker.initialize()

    manager = DeprecationManager(
        experience_tracker=tracker,
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await manager.initialize()

    # Create knowledge with varying performance
    # Poor performance
    for i in range(20):
        await tracker.record_experience(
            magister_id="seo-magister-1",
            task_id=f"task-poor-{i}",
            knowledge_ids=["knowledge-poor"],
            outcome="failure",
            outcome_score=0.2,
        )

    # Good performance
    for i in range(20):
        await tracker.record_experience(
            magister_id="seo-magister-1",
            task_id=f"task-good-{i}",
            knowledge_ids=["knowledge-good"],
            outcome="success",
            outcome_score=0.9,
        )

    # Scan for candidates
    candidates = await manager.scan_for_deprecation_candidates(
        min_usage_count=10,
    )

    # Should find poor performing knowledge
    assert len(candidates) > 0
    poor_candidate = next((c for c in candidates if c["knowledge_id"] == "knowledge-poor"), None)
    assert poor_candidate is not None
    assert poor_candidate["should_deprecate"] is True

    await manager.shutdown()
    await tracker.shutdown()


@pytest.mark.asyncio
async def test_auto_deprecate_low_performers():
    """Test automatic deprecation of low performers"""
    tracker = ExperienceTracker(database_url="sqlite+aiosqlite:///:memory:")
    await tracker.initialize()

    manager = DeprecationManager(
        experience_tracker=tracker,
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await manager.initialize()

    # Create poor performing knowledge
    for i in range(30):
        await tracker.record_experience(
            magister_id="seo-magister-1",
            task_id=f"task-{i}",
            knowledge_ids=["knowledge-auto-deprecate"],
            outcome="failure",
            outcome_score=0.1,
        )

    # Auto deprecate
    results = await manager.auto_deprecate_low_performers(
        min_usage_count=20,
        dry_run=False,
    )

    assert len(results) > 0
    assert any(r["knowledge_id"] == "knowledge-auto-deprecate" for r in results)

    # Verify deprecated
    deprecations = await manager.get_deprecated_knowledge()
    assert any(d["knowledge_id"] == "knowledge-auto-deprecate" for d in deprecations)

    await manager.shutdown()
    await tracker.shutdown()


@pytest.mark.asyncio
async def test_undeprecate_knowledge():
    """Test undeprecating knowledge"""
    tracker = ExperienceTracker(database_url="sqlite+aiosqlite:///:memory:")
    await tracker.initialize()

    manager = DeprecationManager(
        experience_tracker=tracker,
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await manager.initialize()

    # Deprecate first
    await manager.deprecate_knowledge(
        knowledge_id="knowledge-test",
        reason="Test deprecation",
        current_quality=3.0,
    )

    # Undeprecate
    result = await manager.undeprecate_knowledge(
        knowledge_id="knowledge-test",
        reason="Quality improved after update",
    )

    assert result["undeprecated"] is True

    # Verify not in deprecated list
    deprecations = await manager.get_deprecated_knowledge()
    assert not any(d["knowledge_id"] == "knowledge-test" and d["active"] for d in deprecations)

    await manager.shutdown()
    await tracker.shutdown()


@pytest.mark.asyncio
async def test_get_deprecation_stats():
    """Test getting deprecation statistics"""
    tracker = ExperienceTracker(database_url="sqlite+aiosqlite:///:memory:")
    await tracker.initialize()

    manager = DeprecationManager(
        experience_tracker=tracker,
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await manager.initialize()

    # Deprecate some knowledge
    for i in range(5):
        await manager.deprecate_knowledge(
            knowledge_id=f"knowledge-{i}",
            reason="Low quality",
            current_quality=2.0 + i * 0.5,
        )

    # Get stats
    stats = await manager.get_deprecation_stats()

    assert stats["total_deprecated"] == 5
    assert stats["active_deprecated"] == 5

    await manager.shutdown()
    await tracker.shutdown()
