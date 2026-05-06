import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "AIM" / "src"))
import pytest
from unittest.mock import MagicMock, AsyncMock
from meai.events.event_bus import EventBus
from aim.subagents.analytics.orchestrator.analytics_orchestrator import AnalyticsOrchestrator

@pytest.fixture
def analytics_orchestrator():
    bus = MagicMock(spec=EventBus)
    bus.publish = AsyncMock()
    return AnalyticsOrchestrator("test-analytics", bus)

@pytest.mark.asyncio
async def test_execute_metrics_tracking(analytics_orchestrator):
    result = await analytics_orchestrator.execute_metrics_tracking({"task_id": "t1", "metrics_type": "kpi"})
    assert result["task_id"] == "t1"
    assert "results" in result

@pytest.mark.asyncio
async def test_with_progress(analytics_orchestrator):
    calls = []
    async def cb(s, st, m): calls.append((s, st, m))
    await analytics_orchestrator.execute_metrics_tracking({"task_id": "t2", "metrics_type": "kpi"}, cb)
    assert len(calls) >= 2

@pytest.mark.asyncio
async def test_error_handling(analytics_orchestrator):
    result = await analytics_orchestrator.execute_metrics_tracking({"task_id": "t3", "metrics_type": "unknown"})
    assert result["task_id"] == "t3"

@pytest.mark.asyncio
async def test_execution_time(analytics_orchestrator):
    result = await analytics_orchestrator.execute_metrics_tracking({"task_id": "t4", "metrics_type": "kpi"})
    assert result["execution_time_seconds"] >= 0
