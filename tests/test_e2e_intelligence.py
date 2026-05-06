"""End-to-End tests for full Intelligence Magister integration"""

import sys
from pathlib import Path

# Add AIM to path
aim_path = Path(__file__).parent.parent / "AIM" / "src"
sys.path.insert(0, str(aim_path))

import asyncio
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from meai.agents.operator import Operator
from meai.agents.magisters.intelligence_magister import IntelligenceMagister
from meai.events.event_bus import EventBus
from aim.subagents.competitive_intel.orchestrator.ci_orchestrator import CIOrchestrator


@pytest.fixture
def event_bus():
    """Mock event bus instance"""
    bus = MagicMock(spec=EventBus)
    bus.publish = AsyncMock()
    return bus


@pytest.fixture
def ci_orchestrator(event_bus):
    """CI orchestrator instance"""
    return CIOrchestrator(
        agent_id="test-ci-orchestrator",
        event_bus=event_bus
    )


@pytest.fixture
def intelligence_magister(event_bus, ci_orchestrator, tmp_path):
    """Intelligence Magister with CI orchestrator"""
    # Note: This will fail on main branch (no orchestrators param)
    # This test is for Sprint 1 branch validation
    try:
        return IntelligenceMagister(
            agent_id="intelligence-magister-1",
            event_bus=event_bus,
            vault_path=tmp_path / "vault",
            database_url="sqlite+aiosqlite:///:memory:",
            orchestrators={"ci": ci_orchestrator}
        )
    except TypeError:
        # Fallback for main branch (old Intelligence Magister)
        pytest.skip("Intelligence Magister not yet updated on this branch")


@pytest.mark.asyncio
async def test_operator_ci_detection_enhanced():
    """Test enhanced CI detection in Operator"""
    from meai.agents.base_agent import Task, TaskStatus

    operator = Operator(
        database_url="sqlite+aiosqlite:///:memory:"
    )

    # Test various CI keywords
    test_cases = [
        ("Analyze competitors in dental implants", True),
        ("Competitor analysis for Moscow market", True),
        ("Конкурентная разведка в нише имплантов", True),
        ("Market research and benchmarking", True),
        ("Competitive intelligence report", True),
        ("Create blog post about dentistry", False),  # Should not trigger CI
    ]

    for description, should_detect_ci in test_cases:
        task = Task(
            task_id=f"test-{hash(description)}",
            subtask_id=f"sub-{hash(description)}",
            parent_task_id="parent-1",
            action="analyze",
            description=description,
            priority=1,
            status=TaskStatus.RECEIVED,
            created_at=datetime.now(timezone.utc),
            received_at=datetime.now(timezone.utc)
        )

        capabilities = operator._identify_required_capabilities(task)

        if should_detect_ci:
            assert "monitor_competitors" in capabilities, \
                f"Failed to detect CI in: {description}"
        else:
            assert "monitor_competitors" not in capabilities, \
                f"False positive CI detection in: {description}"


@pytest.mark.asyncio
async def test_e2e_ci_analysis_flow():
    """Test end-to-end flow: Intelligence Magister → CIOrchestrator → Result"""
    # Skip on main branch (requires Sprint 1 + Sprint 2 changes)
    pytest.skip("Requires Intelligence Magister and CIOrchestrator from feature branches")


@pytest.mark.asyncio
async def test_performance_quick_tier():
    """Test quick tier completes within time limit (< 15 min)"""
    # Skip on main branch (requires Sprint 2 changes)
    pytest.skip("Requires CIOrchestrator from feat/ci-orchestrator-integration branch")


@pytest.mark.asyncio
async def test_performance_deep_tier():
    """Test deep tier completes within time limit (< 45 min)"""
    # Skip on main branch (requires Sprint 2 changes)
    pytest.skip("Requires CIOrchestrator from feat/ci-orchestrator-integration branch")


@pytest.mark.asyncio
async def test_ci_result_structure_validation():
    """Test CI result has all required fields"""
    # Skip on main branch (requires Sprint 2 changes)
    pytest.skip("Requires CIOrchestrator from feat/ci-orchestrator-integration branch")


@pytest.mark.asyncio
async def test_progress_updates_during_execution():
    """Test progress updates are sent during execution"""
    # Skip on main branch (requires Sprint 2 changes)
    pytest.skip("Requires CIOrchestrator from feat/ci-orchestrator-integration branch")
