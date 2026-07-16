import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "AIM" / "src"))
import pytest
from unittest.mock import MagicMock, AsyncMock
from meai.events.event_bus import EventBus
from aim.subagents.social.orchestrator.social_orchestrator import SocialOrchestrator

@pytest.fixture
def social_orchestrator():
    return SocialOrchestrator("test", MagicMock(spec=EventBus, publish=AsyncMock()))

@pytest.mark.asyncio
async def test_execute(social_orchestrator):
    r = await social_orchestrator.execute_post_publishing({"task_id": "t1", "post_type": "tweet"})
    assert r["task_id"] == "t1" and "results" in r

@pytest.mark.asyncio
async def test_progress(social_orchestrator):
    c = []
    async def cb(s,st,m): c.append(1)
    await social_orchestrator.execute_post_publishing({"task_id": "t2", "post_type": "tweet"}, cb)
    assert len(c) >= 2

@pytest.mark.asyncio
async def test_error(social_orchestrator):
    r = await social_orchestrator.execute_post_publishing({"task_id": "t3", "post_type": "unknown"})
    assert r["task_id"] == "t3"

@pytest.mark.asyncio
async def test_time(social_orchestrator):
    r = await social_orchestrator.execute_post_publishing({"task_id": "t4", "post_type": "tweet"})
    assert r["execution_time_seconds"] >= 0
