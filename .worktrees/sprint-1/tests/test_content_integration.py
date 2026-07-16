"""Tests for Content integration"""

import sys
from pathlib import Path
aim_path = Path(__file__).parent.parent / "AIM" / "src"
sys.path.insert(0, str(aim_path))

import pytest
from unittest.mock import MagicMock, AsyncMock

from meai.events.event_bus import EventBus
from aim.subagents.content.orchestrator.content_orchestrator import ContentOrchestrator


@pytest.fixture
def event_bus():
    bus = MagicMock(spec=EventBus)
    bus.publish = AsyncMock()
    return bus


@pytest.fixture
def content_orchestrator(event_bus):
    return ContentOrchestrator(
        agent_id="test-content-orchestrator",
        event_bus=event_bus
    )


@pytest.mark.asyncio
async def test_execute_content_generation(content_orchestrator):
    """Test content generation"""
    task_data = {
        "task_id": "test-1",
        "content_type": "article",
        "topic": "dental implants"
    }
    
    result = await content_orchestrator.execute_content_generation(task_data)
    
    assert result["task_id"] == "test-1"
    assert "results" in result


@pytest.mark.asyncio
async def test_content_orchestrator_with_progress(content_orchestrator):
    """Test progress callbacks"""
    progress_calls = []
    
    async def progress_callback(step, status, message):
        progress_calls.append((step, status, message))
    
    task_data = {
        "task_id": "test-2",
        "content_type": "article",
        "topic": "dental"
    }
    
    result = await content_orchestrator.execute_content_generation(task_data, progress_callback)
    
    assert len(progress_calls) >= 2
    assert result["task_id"] == "test-2"


@pytest.mark.asyncio
async def test_content_orchestrator_error_handling(content_orchestrator):
    """Test error handling"""
    task_data = {
        "task_id": "test-3",
        "content_type": "unknown"
    }
    
    result = await content_orchestrator.execute_content_generation(task_data)
    
    assert result["task_id"] == "test-3"


@pytest.mark.asyncio
async def test_content_orchestrator_execution_time(content_orchestrator):
    """Test execution time tracking"""
    task_data = {
        "task_id": "test-4",
        "content_type": "article"
    }
    
    result = await content_orchestrator.execute_content_generation(task_data)
    
    assert result["execution_time_seconds"] >= 0
