"""Unit tests for Content Magister"""

import asyncio
import pytest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from meai.agents.magisters.content_magister import ContentMagister
from meai.agents.base_agent import Task, TaskResult
from meai.events.event_bus import EventBus


@pytest.fixture
def event_bus():
    """Mock event bus"""
    bus = MagicMock(spec=EventBus)
    bus.publish = AsyncMock()
    return bus


@pytest.fixture
def mock_seo_orchestrator():
    """Mock CI orchestrator"""
    orchestrator = AsyncMock()
    orchestrator.execute_ci_analysis = AsyncMock(return_value={
        "task_id": "test-task-1",
        "tier": "deep",
        "phases_executed": [1, 2, 3, 4, 5],
        "execution_time_seconds": 100,
        "competitors_analyzed": 3,
        "findings": {
            "competitor_profiles": [
                {"name": "Competitor 1", "url": "https://example1.com"},
                {"name": "Competitor 2", "url": "https://example2.com"},
                {"name": "Competitor 3", "url": "https://example3.com"},
            ]
        },
        "reports": {
            "pdf_path": "/tmp/report.pdf",
            "html_path": "/tmp/report.html"
        },
        "errors": []
    })
    return orchestrator


@pytest.fixture
def content_magister(event_bus, mock_seo_orchestrator, tmp_path):
    """Content Magister instance with mocked dependencies"""
    return ContentMagister(
        agent_id="test-intelligence-magister",
        event_bus=event_bus,
        vault_path=tmp_path / "vault",
        database_url="sqlite+aiosqlite:///:memory:",
        orchestrators={"ci": mock_seo_orchestrator}
    )


@pytest.mark.asyncio
async def test_execute_task_routing_content_generation(content_magister, mock_seo_orchestrator):
    """Test that execute_task routes generate_content to CI handler"""
    # Create a mock task object with data attribute
    task = MagicMock()
    task.task_id = "test-task-1"
    task.description = "Analyze 3 competitors"
    task.priority = 1
    task.deadline = None
    task.data = {
        "action": "generate_content",
        "niche": "dental implants",
        "geo": "Moscow",
        "depth": "quick",
        "competitors": [
            "https://example1.com",
            "https://example2.com",
            "https://example3.com"
        ]
    }

    result = await content_magister.execute_task(task)

    # Verify CI orchestrator was called
    mock_seo_orchestrator.execute_ci_analysis.assert_called_once()

    # Verify result
    assert result.status == "success"
    assert result.subtask_id == "test-task-1"
    assert "findings" in result.result


@pytest.mark.asyncio
async def test_handle_content_generation_success(content_magister, mock_seo_orchestrator, event_bus):
    """Test successful competitor analysis"""
    task = MagicMock()
    task.task_id = "test-task-2"
    task.description = "Analyze competitors"
    task.priority = 1
    task.deadline = None
    task.data = {
        "action": "generate_content",
        "niche": "dental implants",
        "geo": "Moscow",
        "depth": "deep",
        "competitors": ["https://example.com"]
    }

    # Set current_task_id so progress updates work
    content_magister.current_task_id = task.task_id

    result = await content_magister._handle_content_generation(task)

    # Verify result
    assert result.status == "success"
    assert result.result["competitors_analyzed"] == 3

    # Verify progress updates were published
    assert event_bus.publish.call_count >= 2  # At least start and complete


@pytest.mark.asyncio
async def test_store_content_result(content_magister, tmp_path):
    """Test CI result storage in vault"""
    result = {
        "task_id": "test-task-3",
        "tier": "deep",
        "phases_executed": [1, 2, 3],
        "execution_time_seconds": 100,
        "competitors_analyzed": 2,
        "findings": {"test": "data"},
        "reports": {},
        "errors": []
    }

    await content_magister._store_content_result(result)

    # Verify file was created
    result_file = tmp_path / "vault" / "wiki" / "sources" / "ci-test-task-3.md"
    assert result_file.exists()

    # Verify content
    content = result_file.read_text()
    assert "test-task-3" in content
    assert "deep" in content
    assert "competitors_analyzed: 2" in content


@pytest.mark.asyncio
async def test_timeout_handling(content_magister, mock_seo_orchestrator):
    """Test timeout handling for long-running tasks"""
    # Make orchestrator hang
    async def slow_execution(*args, **kwargs):
        await asyncio.sleep(10)
        return {}

    mock_seo_orchestrator.execute_ci_analysis = slow_execution

    task = MagicMock()
    task.task_id = "test-task-4"
    task.description = "Analyze competitors"
    task.priority = 1
    task.deadline = None
    task.data = {
        "action": "generate_content",
        "niche": "test",
        "geo": "test",
        "depth": "quick",  # 15 min timeout
        "competitors": ["https://example.com"]
    }

    # Override timeout for test
    with patch.object(content_magister, '_handle_content_generation') as mock_handler:
        async def timeout_handler(task):
            try:
                await asyncio.wait_for(slow_execution(), timeout=0.1)
            except asyncio.TimeoutError:
                return content_magister._create_timeout_result(task, 900)

        mock_handler.side_effect = timeout_handler
        result = await content_magister.execute_task(task)

    # Verify timeout result
    assert result.status == "failed"
    assert "timed out" in result.error


@pytest.mark.asyncio
async def test_validate_content_result_success(content_magister):
    """Test CI result validation with valid data"""
    result = {
        "task_id": "test-task-5",
        "findings": {"test": "data"},
        "competitors_analyzed": 3,
        "reports": {}
    }

    validated = content_magister._validate_content_result(result)

    assert validated == result


@pytest.mark.asyncio
async def test_validate_content_result_missing_task_id(content_magister):
    """Test CI result validation fails on missing task_id"""
    result = {
        "findings": {"test": "data"},
        "competitors_analyzed": 3
    }

    with pytest.raises(ValueError, match="Missing task_id"):
        content_magister._validate_content_result(result)


@pytest.mark.asyncio
async def test_validate_content_result_no_competitors(content_magister):
    """Test CI result validation fails when no competitors analyzed"""
    result = {
        "task_id": "test-task-6",
        "findings": {"test": "data"},
        "competitors_analyzed": 0
    }

    with pytest.raises(ValueError, match="No competitors analyzed"):
        content_magister._validate_content_result(result)


@pytest.mark.asyncio
async def test_progress_updates(content_magister, event_bus):
    """Test progress update publishing"""
    content_magister.current_task_id = "test-task-7"

    await content_magister._publish_progress(1, "started", "Phase 1 started")

    # Verify Event Bus publish was called
    event_bus.publish.assert_called_once()

    # Verify message structure
    call_args = event_bus.publish.call_args[0][0]
    assert call_args.message_type == "task_progress"
    assert call_args.payload["task_id"] == "test-task-7"
    assert call_args.payload["phase"] == 1
    assert call_args.payload["status"] == "started"


@pytest.mark.asyncio
async def test_orchestrator_not_registered(content_magister):
    """Test error when CI orchestrator not registered"""
    # Remove orchestrator
    content_magister.orchestrators = {}

    task = MagicMock()
    task.task_id = "test-task-8"
    task.description = "Analyze competitors"
    task.priority = 1
    task.deadline = None
    task.data = {
        "action": "generate_content",
        "niche": "test",
        "geo": "test",
        "competitors": []
    }

    result = await content_magister.execute_task(task)

    # Verify error result
    assert result.status == "failed"
    assert "not registered" in result.error


@pytest.mark.asyncio
async def test_generic_intelligence_fallback(content_magister):
    """Test fallback to generic intelligence for unknown actions"""
    task = MagicMock()
    task.task_id = "test-task-9"
    task.description = "Test unknown action"
    task.priority = 1
    task.deadline = None
    task.data = {
        "action": "unknown_action"
    }

    with patch.object(content_magister, 'search_knowledge', new_callable=AsyncMock) as mock_search:
        mock_search.return_value = [{"result": "test"}]

        result = await content_magister.execute_task(task)

    # Verify fallback was used
    assert result.status == "success"
    assert result.result["source"] == "knowledge_search"
    mock_search.assert_called_once()
