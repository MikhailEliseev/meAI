"""Tests for Ads integration"""

import sys
from pathlib import Path
aim_path = Path(__file__).parent.parent / "AIM" / "src"
sys.path.insert(0, str(aim_path))

import pytest
from unittest.mock import MagicMock, AsyncMock

from meai.events.event_bus import EventBus
from aim.subagents.ads.orchestrator.ads_orchestrator import AdsOrchestrator


@pytest.fixture
def event_bus():
    bus = MagicMock(spec=EventBus)
    bus.publish = AsyncMock()
    return bus


@pytest.fixture
def ads_orchestrator(event_bus):
    return AdsOrchestrator(
        agent_id="test-ads-orchestrator",
        event_bus=event_bus
    )


@pytest.mark.asyncio
async def test_execute_campaign_creation(ads_orchestrator):
    task_data = {"task_id": "test-1", "campaign_type": "ppc"}
    result = await ads_orchestrator.execute_campaign_creation(task_data)
    assert result["task_id"] == "test-1"
    assert "results" in result


@pytest.mark.asyncio
async def test_ads_orchestrator_with_progress(ads_orchestrator):
    progress_calls = []
    async def progress_callback(step, status, message):
        progress_calls.append((step, status, message))
    
    task_data = {"task_id": "test-2", "campaign_type": "ppc"}
    result = await ads_orchestrator.execute_campaign_creation(task_data, progress_callback)
    assert len(progress_calls) >= 2


@pytest.mark.asyncio
async def test_ads_orchestrator_error_handling(ads_orchestrator):
    task_data = {"task_id": "test-3", "campaign_type": "unknown"}
    result = await ads_orchestrator.execute_campaign_creation(task_data)
    assert result["task_id"] == "test-3"


@pytest.mark.asyncio
async def test_ads_orchestrator_execution_time(ads_orchestrator):
    task_data = {"task_id": "test-4", "campaign_type": "ppc"}
    result = await ads_orchestrator.execute_campaign_creation(task_data)
    assert result["execution_time_seconds"] >= 0
