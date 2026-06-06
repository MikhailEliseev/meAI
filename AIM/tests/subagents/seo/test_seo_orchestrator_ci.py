"""
Tests for SEO Orchestrator with CI Research Agent integration
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from meai.agents.base_agent import Task, TaskResult, TaskStatus
from meai.events.event_bus import EventBus

from src.aim.subagents.seo.orchestrator.seo_orchestrator import SEOOrchestrator


@pytest.fixture
def event_bus():
    """Create mock event bus"""
    return MagicMock(spec=EventBus)


@pytest.fixture
def orchestrator(event_bus):
    """Create SEO Orchestrator instance"""
    return SEOOrchestrator(
        agent_id="test-seo-orchestrator",
        event_bus=event_bus,
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="test-vault"
    )


def test_capabilities_include_competitor_intelligence(orchestrator):
    """Test that capabilities include competitor_intelligence"""
    capabilities = orchestrator.get_capabilities()
    assert "competitor_intelligence" in capabilities
    assert "keyword_analysis" in capabilities
    assert "content_optimization" in capabilities
    assert "technical_audit" in capabilities


@pytest.mark.asyncio
async def test_execute_competitor_intelligence_missing_industry(orchestrator):
    """Test competitor intelligence with missing industry"""
    task_data = {
        "task_id": "test-task-1",
        "analysis_type": "competitor_intelligence",
        "target": "https://example.com"
    }

    result = await orchestrator.execute_seo_analysis(task_data)

    assert result["analysis_type"] == "competitor_intelligence"
    assert result["results"]["status"] == "error"
    assert "industry" in result["results"]["error"]


@pytest.mark.asyncio
async def test_execute_competitor_intelligence_success(orchestrator):
    """Test successful competitor intelligence analysis"""

    # Mock CIResearchAgent
    mock_ci_result = TaskResult(
        subtask_id="ci-test-task-1",
        agent_id="ci-research-test-task-1",
        action="research_competitors",
        status="success",
        result={
            "benchmark_report": {
                "competitor_profiles": [
                    {"domain": "competitor1.com"},
                    {"domain": "competitor2.com"},
                    {"domain": "competitor3.com"}
                ],
                "growth_laws": [
                    {"law": "SEO-first acquisition", "prevalence": 0.8}
                ],
                "do_copy": [
                    {"pattern": "Free consultation", "ice_score": 500}
                ],
                "do_ignore": [
                    {"pattern": "TV advertising", "reason": "Too expensive"}
                ],
                "sequencing_roadmap": [
                    {"phase": 1, "duration": "1-2 weeks"}
                ]
            }
        },
        error=None,
        duration_seconds=10,
        completed_at=datetime.now(timezone.utc)
    )

    with patch('AIM.src.aim.subagents.seo.orchestrator.seo_orchestrator.CIResearchAgent') as MockCIAgent:
        mock_agent = AsyncMock()
        mock_agent.execute_task.return_value = mock_ci_result
        MockCIAgent.return_value = mock_agent

        task_data = {
            "task_id": "test-task-1",
            "analysis_type": "competitor_intelligence",
            "industry": "dental clinics",
            "target": "https://example.com",
            "max_competitors": 5,
            "research_depth": "standard",
            "api_keys": {"semrush": "test-key"}
        }

        result = await orchestrator.execute_seo_analysis(task_data)

        assert result["analysis_type"] == "competitor_intelligence"
        assert result["results"]["status"] == "completed"
        assert result["results"]["industry"] == "dental clinics"
        assert result["results"]["competitors_analyzed"] == 3
        assert len(result["results"]["growth_laws"]) == 1
        assert len(result["results"]["copy_patterns"]) == 1
        assert len(result["results"]["ignore_patterns"]) == 1
        assert len(result["results"]["roadmap"]) == 1


@pytest.mark.asyncio
async def test_execute_competitor_intelligence_with_progress_callback(orchestrator):
    """Test competitor intelligence with progress callback"""

    progress_updates = []

    async def progress_callback(step: int, status: str, message: str):
        progress_updates.append({"step": step, "status": status, "message": message})

    # Mock CIResearchAgent
    mock_ci_result = TaskResult(
        subtask_id="ci-test-task-1",
        agent_id="ci-research-test-task-1",
        action="research_competitors",
        status="success",
        result={
            "benchmark_report": {
                "competitor_profiles": [],
                "growth_laws": [],
                "do_copy": [],
                "do_ignore": [],
                "sequencing_roadmap": []
            }
        },
        error=None,
        duration_seconds=10,
        completed_at=datetime.now(timezone.utc)
    )

    with patch('AIM.src.aim.subagents.seo.orchestrator.seo_orchestrator.CIResearchAgent') as MockCIAgent:
        mock_agent = AsyncMock()
        mock_agent.execute_task.return_value = mock_ci_result
        MockCIAgent.return_value = mock_agent

        task_data = {
            "task_id": "test-task-1",
            "analysis_type": "competitor_intelligence",
            "industry": "dental clinics"
        }

        result = await orchestrator.execute_seo_analysis(task_data, progress_callback)

        # Check progress updates
        assert len(progress_updates) >= 3
        assert progress_updates[0]["message"] == "Starting competitor_intelligence analysis"
        assert any("Initializing" in u["message"] for u in progress_updates)
        assert any("complete" in u["message"].lower() for u in progress_updates)


@pytest.mark.asyncio
async def test_execute_competitor_intelligence_failure(orchestrator):
    """Test competitor intelligence analysis failure"""

    # Mock CIResearchAgent with failure
    mock_ci_result = TaskResult(
        subtask_id="ci-test-task-1",
        agent_id="ci-research-test-task-1",
        action="research_competitors",
        status="failed",
        result={},
        error="API rate limit exceeded",
        duration_seconds=5,
        completed_at=datetime.now(timezone.utc)
    )

    with patch('AIM.src.aim.subagents.seo.orchestrator.seo_orchestrator.CIResearchAgent') as MockCIAgent:
        mock_agent = AsyncMock()
        mock_agent.execute_task.return_value = mock_ci_result
        MockCIAgent.return_value = mock_agent

        task_data = {
            "task_id": "test-task-1",
            "analysis_type": "competitor_intelligence",
            "industry": "dental clinics"
        }

        result = await orchestrator.execute_seo_analysis(task_data)

        assert result["analysis_type"] == "competitor_intelligence"
        assert result["results"]["status"] == "error"
        assert "rate limit" in result["results"]["error"].lower()
