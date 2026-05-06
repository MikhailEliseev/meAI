"""Tests for SEO integration"""

import sys
from pathlib import Path
aim_path = Path(__file__).parent.parent / "AIM" / "src"
sys.path.insert(0, str(aim_path))

import pytest
from unittest.mock import MagicMock, AsyncMock

from meai.events.event_bus import EventBus
from aim.subagents.seo.orchestrator.seo_orchestrator import SEOOrchestrator


@pytest.fixture
def event_bus():
    bus = MagicMock(spec=EventBus)
    bus.publish = AsyncMock()
    return bus


@pytest.fixture
def seo_orchestrator(event_bus):
    return SEOOrchestrator(
        agent_id="test-seo-orchestrator",
        event_bus=event_bus
    )


@pytest.mark.asyncio
async def test_execute_seo_analysis_keyword(seo_orchestrator):
    """Test keyword analysis"""
    task_data = {
        "task_id": "test-1",
        "analysis_type": "keyword",
        "target": "dental clinics",
        "niche": "dental",
        "geo": "Moscow"
    }
    
    result = await seo_orchestrator.execute_seo_analysis(task_data)
    
    assert result["task_id"] == "test-1"
    assert result["analysis_type"] == "keyword"
    assert "results" in result
    assert "execution_time_seconds" in result


@pytest.mark.asyncio
async def test_execute_seo_analysis_with_progress(seo_orchestrator):
    """Test progress callbacks"""
    progress_calls = []
    
    async def progress_callback(step, status, message):
        progress_calls.append((step, status, message))
    
    task_data = {
        "task_id": "test-2",
        "analysis_type": "keyword",
        "target": "dental",
        "niche": "dental",
        "geo": "Moscow"
    }
    
    result = await seo_orchestrator.execute_seo_analysis(task_data, progress_callback)
    
    assert len(progress_calls) >= 2
    assert result["task_id"] == "test-2"


@pytest.mark.asyncio
async def test_seo_orchestrator_error_handling(seo_orchestrator):
    """Test error handling"""
    task_data = {
        "task_id": "test-3",
        "analysis_type": "unknown",
        "target": "test"
    }
    
    result = await seo_orchestrator.execute_seo_analysis(task_data)
    
    assert result["task_id"] == "test-3"
    assert "results" in result


@pytest.mark.asyncio
async def test_seo_orchestrator_execution_time(seo_orchestrator):
    """Test execution time tracking"""
    task_data = {
        "task_id": "test-4",
        "analysis_type": "keyword",
        "target": "test"
    }
    
    result = await seo_orchestrator.execute_seo_analysis(task_data)
    
    assert result["execution_time_seconds"] >= 0
