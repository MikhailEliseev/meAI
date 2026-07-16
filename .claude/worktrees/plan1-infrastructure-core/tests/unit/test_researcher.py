# tests/unit/test_researcher.py
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone
from meai.agents.researcher import ResearcherAgent
from meai.agents.base_agent import Task, TaskStatus


@pytest.mark.asyncio
async def test_researcher_initialization():
    """Test ResearcherAgent can be initialized"""
    agent = ResearcherAgent(
        agent_id="researcher",
        database_url="sqlite+aiosqlite:///:memory:",
    )

    assert agent.agent_id == "researcher"
    assert agent.agent_type == "researcher"


@pytest.mark.asyncio
async def test_researcher_capabilities():
    """Test researcher capabilities"""
    agent = ResearcherAgent(
        agent_id="researcher",
        database_url="sqlite+aiosqlite:///:memory:",
    )

    capabilities = agent.get_capabilities()

    assert "research_topic" in capabilities
    assert "monitor_youtube" in capabilities
    assert "monitor_telegram" in capabilities
    assert "validate_source" in capabilities


@pytest.mark.asyncio
async def test_research_topic():
    """Test research_topic capability"""
    agent = ResearcherAgent(
        agent_id="researcher",
        database_url="sqlite+aiosqlite:///:memory:",
        perplexity_api_key="test-key",
    )

    await agent.initialize()

    # Mock Perplexity response
    mock_result = {
        "content": "SEO best practices include keyword research and quality content.",
        "sources": ["https://moz.com/seo", "https://google.com/seo"],
    }

    with patch.object(agent.perplexity, 'research', new_callable=AsyncMock) as mock_research:
        mock_research.return_value = mock_result

        task = Task(
            task_id="task-001",
            subtask_id="subtask-001",
            parent_task_id="task-001",
            action="research_topic",
            description="Research SEO best practices",
            priority=1,
            status=TaskStatus.RECEIVED,
            created_at=datetime.now(timezone.utc),
            received_at=datetime.now(timezone.utc),
        )

        result = await agent.execute_task(task)

        assert result.status == "success"
        assert "content" in result.result
        assert "sources" in result.result
        assert len(result.result["sources"]) == 2

    await agent.shutdown()


@pytest.mark.asyncio
async def test_monitor_youtube():
    """Test monitor_youtube capability"""
    agent = ResearcherAgent(
        agent_id="researcher",
        database_url="sqlite+aiosqlite:///:memory:",
        youtube_api_key="test-key",
    )

    await agent.initialize()

    # Mock YouTube response
    mock_videos = [
        {
            "video_id": "video1",
            "title": "SEO Tips",
            "description": "Learn SEO",
            "published_at": "2024-01-01T00:00:00Z",
        }
    ]

    with patch.object(agent.youtube, 'get_channel_videos', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_videos

        task = Task(
            task_id="task-002",
            subtask_id="subtask-002",
            parent_task_id="task-002",
            action="monitor_youtube",
            description="Monitor YouTube channel UC_test",
            priority=1,
            status=TaskStatus.RECEIVED,
            created_at=datetime.now(timezone.utc),
            received_at=datetime.now(timezone.utc),
        )

        result = await agent.execute_task(task)

        assert result.status == "success"
        assert "videos" in result.result
        assert len(result.result["videos"]) == 1

    await agent.shutdown()


@pytest.mark.asyncio
async def test_validate_source():
    """Test validate_source capability"""
    agent = ResearcherAgent(
        agent_id="researcher",
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await agent.initialize()

    task = Task(
        task_id="task-003",
        subtask_id="subtask-003",
        parent_task_id="task-003",
        action="validate_source",
        description="Validate source quality for https://moz.com",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
    )

    result = await agent.execute_task(task)

    assert result.status == "success"
    assert "url" in result.result
    assert "quality_score" in result.result
    assert "is_trusted" in result.result

    await agent.shutdown()


@pytest.mark.asyncio
async def test_unknown_action():
    """Test handling of unknown action"""
    agent = ResearcherAgent(
        agent_id="researcher",
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await agent.initialize()

    task = Task(
        task_id="task-004",
        subtask_id="subtask-004",
        parent_task_id="task-004",
        action="unknown_action",
        description="Unknown action",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
    )

    result = await agent.execute_task(task)

    assert result.status == "failed"
    assert "Unknown action" in result.error

    await agent.shutdown()
