"""Integration tests for Intelligence Magister + CIOrchestrator"""

import sys
from pathlib import Path

# Add AIM to path
aim_path = Path(__file__).parent.parent / "AIM" / "src"
sys.path.insert(0, str(aim_path))

import asyncio
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from meai.agents.magisters.intelligence_magister import IntelligenceMagister
from meai.events.event_bus import EventBus
from aim.subagents.competitive_intel.orchestrator.ci_orchestrator import CIOrchestrator


@pytest.fixture
def event_bus():
    """Mock event bus"""
    bus = MagicMock(spec=EventBus)
    bus.publish = AsyncMock()
    return bus


@pytest.fixture
def ci_orchestrator(event_bus):
    """Real CI orchestrator instance"""
    return CIOrchestrator(
        agent_id="test-ci-orchestrator",
        event_bus=event_bus
    )


@pytest.mark.asyncio
async def test_execute_ci_analysis_quick_tier(ci_orchestrator):
    """Test CI analysis execution with quick tier"""
    task_data = {
        "task_id": "test-1",
        "niche": "dental implants",
        "geo": "Moscow",
        "tier": "quick",
        "competitors": [
            "https://example1.com",
            "https://example2.com"
        ]
    }

    result = await ci_orchestrator.execute_ci_analysis(task_data)

    # Verify result structure
    assert result["task_id"] == "test-1"
    assert result["tier"] == "quick"
    assert result["phases_executed"] == [1, 2, 3, 4]
    assert result["competitors_analyzed"] == 2
    assert "findings" in result
    assert "reports" in result
    assert isinstance(result["errors"], list)


@pytest.mark.asyncio
async def test_execute_ci_analysis_deep_tier(ci_orchestrator):
    """Test CI analysis execution with deep tier"""
    task_data = {
        "task_id": "test-2",
        "niche": "dental implants",
        "geo": "Moscow",
        "tier": "deep",
        "competitors": ["https://example.com"]
    }

    result = await ci_orchestrator.execute_ci_analysis(task_data)

    # Verify deep tier executes phases 1-9
    assert result["tier"] == "deep"
    assert result["phases_executed"] == list(range(1, 10))
    assert len(result["findings"]) == 9  # 9 phases


@pytest.mark.asyncio
async def test_execute_ci_analysis_with_progress_callback(ci_orchestrator):
    """Test CI analysis with progress callback"""
    progress_updates = []

    async def progress_callback(phase, status, message):
        progress_updates.append({
            "phase": phase,
            "status": status,
            "message": message
        })

    task_data = {
        "task_id": "test-3",
        "niche": "test",
        "geo": "test",
        "tier": "quick",
        "competitors": []
    }

    result = await ci_orchestrator.execute_ci_analysis(
        task_data,
        progress_callback=progress_callback
    )

    # Verify progress updates were called
    assert len(progress_updates) == 4  # 4 phases for quick tier
    assert all(u["status"] == "in_progress" for u in progress_updates)
    assert progress_updates[0]["phase"] == 1
    assert progress_updates[-1]["phase"] == 4


@pytest.mark.asyncio
async def test_intelligence_magister_to_ci_orchestrator_integration(ci_orchestrator):
    """Test full integration: Intelligence Magister → CIOrchestrator (direct call)"""
    # Test direct call to CI orchestrator (simulating Intelligence Magister integration)
    task_data = {
        "task_id": "integration-test-1",
        "niche": "dental implants",
        "geo": "Moscow",
        "tier": "quick",
        "competitors": [
            "https://example1.com",
            "https://example2.com",
            "https://example3.com"
        ]
    }

    # Track progress updates
    progress_updates = []

    async def progress_callback(phase, status, message):
        progress_updates.append({"phase": phase, "status": status})

    result = await ci_orchestrator.execute_ci_analysis(
        task_data,
        progress_callback=progress_callback
    )

    # Verify result
    assert result["tier"] == "quick"
    assert result["competitors_analyzed"] == 3
    assert result["phases_executed"] == [1, 2, 3, 4]
    assert len(progress_updates) == 4  # 4 phases


@pytest.mark.asyncio
async def test_ci_orchestrator_tier_selection(ci_orchestrator):
    """Test tier selection logic"""
    # Quick tier
    quick_data = {"task_id": "t1", "tier": "quick", "competitors": []}
    quick_result = await ci_orchestrator.execute_ci_analysis(quick_data)
    assert quick_result["phases_executed"] == [1, 2, 3, 4]

    # Deep tier
    deep_data = {"task_id": "t2", "tier": "deep", "competitors": []}
    deep_result = await ci_orchestrator.execute_ci_analysis(deep_data)
    assert deep_result["phases_executed"] == list(range(1, 10))

    # Full tier
    full_data = {"task_id": "t3", "tier": "full", "competitors": []}
    full_result = await ci_orchestrator.execute_ci_analysis(full_data)
    assert full_result["phases_executed"] == list(range(1, 17))


@pytest.mark.asyncio
async def test_ci_orchestrator_error_handling(ci_orchestrator):
    """Test error handling in CI orchestrator"""
    # Invalid tier should default to deep
    task_data = {
        "task_id": "error-test",
        "tier": "invalid_tier",
        "competitors": []
    }

    # Should not raise, should handle gracefully
    result = await ci_orchestrator.execute_ci_analysis(task_data)

    # Verify it defaulted to deep or handled error
    assert "task_id" in result
    assert "errors" in result


@pytest.mark.asyncio
async def test_ci_orchestrator_execution_time_tracking(ci_orchestrator):
    """Test execution time is tracked"""
    task_data = {
        "task_id": "time-test",
        "tier": "quick",
        "competitors": []
    }

    result = await ci_orchestrator.execute_ci_analysis(task_data)

    # Verify execution time is recorded
    assert "execution_time_seconds" in result
    assert result["execution_time_seconds"] >= 0
    assert isinstance(result["execution_time_seconds"], int)
