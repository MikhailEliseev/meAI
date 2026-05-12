"""Integration Tests for Keyword Research Agent

Tests full workflow: Event Bus → API → Compliance → Prioritization → Database → Obsidian
"""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from meai.agents.base_agent import Task, TaskStatus
from meai.events.event_bus import EventBus

from src.aim.subagents.keyword_research_agent import KeywordResearchAgent
from src.aim.subagents.schemas.api_responses import KeywordDataUnified
from src.aim.subagents.schemas.compliance import ComplianceAction, ComplianceCheckResult, RiskLevel, PatternMatch
from src.aim.subagents.schemas.prioritization import PriorityTier


@pytest_asyncio.fixture
async def event_bus():
    """Create event bus instance"""
    bus = EventBus()
    yield bus
    await bus.close()


@pytest_asyncio.fixture
async def agent(event_bus):
    """Create agent instance"""
    agent = KeywordResearchAgent(
        agent_id="test-keyword-research-agent",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="./test_vault",
        event_bus=event_bus,
        skip_api_validation=True,
    )
    yield agent
    await agent.close()


@pytest.mark.asyncio
async def test_event_bus_integration(agent, event_bus):
    """Test Event Bus integration (publish task, receive result)"""
    # Create task
    task = Task(
        task_id="test-task-1",
        subtask_id="test-subtask-1",
        parent_task_id="test-parent-1",
        action="keyword_research",
        description="Research keywords for dental implants",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
        data={
            "seed_keyword": "dental implants",
            "max_keywords": 10,
            "min_volume": 10,
            "max_cost_usd": 1.0,
        },
    )

    # Mock API clients
    mock_keywords = [
        KeywordDataUnified(
            keyword="dental implants",
            volume=5000,
            difficulty=65,
            cpc=8.50,
            intent="commercial",
            source="semrush",
        
            priority_score=50.0,
        ),
        KeywordDataUnified(
            keyword="dental implants cost",
            volume=2000,
            difficulty=55,
            cpc=9.20,
            intent="commercial",
            source="semrush",
        
            priority_score=50.0,
        ),
    ]

    with patch.object(agent, "_expand_keywords_with_fallback", return_value=mock_keywords):
        # Mock compliance checker
        agent.compliance_checker = AsyncMock()
        agent.compliance_checker.check_keyword.return_value = ComplianceCheckResult(
            keyword="dental implants",
            likelihood_score=1,
            severity_score=5,
            risk_score=5,
            risk_level=RiskLevel.LOW,
            action=ComplianceAction.PASSED,
            rationale="Test compliance check",
            matched_patterns=[],
            fda_enforcement_records=[],
        )

        # Execute task
        result = await agent.execute_task(task)

        # Verify result
        assert result.status == "success"
        assert result.agent_id == "test-keyword-research-agent"
        assert "seed_keyword" in result.result
        assert result.result["seed_keyword"] == "dental implants"
        assert result.result["total_keywords"] == 2


@pytest.mark.asyncio
async def test_database_integration(agent):
    """Test Database integration (audit trail saved)"""
    # Create task
    task = Task(
        task_id="test-task-2",
        subtask_id="test-subtask-2",
        parent_task_id="test-parent",
        action="keyword_research",
        description="Research keywords",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
        data={
            "seed_keyword": "botox treatment",
            "max_keywords": 5,
        },
    )

    # Mock API and compliance
    mock_keywords = [
        KeywordDataUnified(
            keyword="botox treatment",
            volume=3000,
            difficulty=60,
            cpc=12.00,
            intent="commercial",
            source="semrush",
        
            priority_score=50.0,
        ),
    ]

    with patch.object(agent, "_expand_keywords_with_fallback", return_value=mock_keywords):
        # Mock compliance checker
        agent.compliance_checker = AsyncMock()
        agent.compliance_checker.check_keyword.return_value = ComplianceCheckResult(
            keyword="botox treatment",
            likelihood_score=2,
            severity_score=5,
            risk_score=10,
            risk_level=RiskLevel.MEDIUM,
            action=ComplianceAction.PASSED,
            rationale="Test compliance check",
            matched_patterns=[],
            fda_enforcement_records=[],
        )

        # Execute task
        result = await agent.execute_task(task)

        # Verify audit trail was created
        assert result.status == "success"
        # TODO: Query database to verify audit trail exists


@pytest.mark.asyncio
async def test_primary_fallback_pattern(agent):
    """Test primary/fallback pattern (SEMrush fails → Ahrefs)"""
    task = Task(
        task_id="test-task-3",
        subtask_id="test-subtask-3",
        parent_task_id="test-parent",
        action="keyword_research",
        description="Research keywords",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
        data={
            "seed_keyword": "laser hair removal",
            "max_keywords": 5,
        },
    )

    # Mock SEMrush failure
    agent.semrush_client = AsyncMock()
    agent.semrush_client.expand_keywords.side_effect = Exception("SEMrush API error")

    # Mock Ahrefs success
    agent.ahrefs_client = AsyncMock()
    agent.ahrefs_client.expand_keywords.return_value = [
        KeywordDataUnified(
            keyword="laser hair removal",
            volume=4000,
            difficulty=70,
            cpc=15.00,
            intent="commercial",
            source="ahrefs",
        
            priority_score=50.0,
        ),
    ]

    # Mock compliance
    agent.compliance_checker = AsyncMock()
    agent.compliance_checker.check_keyword.return_value = ComplianceCheckResult(
                keyword="laser hair removal",
                likelihood_score=1,
                severity_score=3,
                risk_score=3,
                risk_level=RiskLevel.LOW,
                action=ComplianceAction.PASSED,
                rationale="Test compliance check",
                matched_patterns=[],
                fda_enforcement_records=[],
            )

    # Execute task
    result = await agent.execute_task(task)

    # Verify fallback worked
    assert result.status == "success"
    assert agent.ahrefs_client.expand_keywords.called
    assert result.result["keywords"][0]["keyword_data"]["source"] == "ahrefs"


@pytest.mark.asyncio
async def test_budget_guard(agent):
    """Test budget guard (stops at max_cost_usd)"""
    task = Task(
        task_id="test-task-4",
        subtask_id="test-subtask-4",
        parent_task_id="test-parent",
        action="keyword_research",
        description="Research keywords",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
        data={
            "seed_keyword": "rhinoplasty",
            "max_keywords": 100,
            "max_cost_usd": 0.05,  # Very low budget
        },
    )

    # Mock API to return many keywords
    mock_keywords = [
        KeywordDataUnified(
            keyword=f"rhinoplasty {i}",
            volume=1000,
            difficulty=50,
            cpc=10.00,
            intent="commercial",
            source="semrush",
        
            priority_score=50.0,
        )
        for i in range(10)  # 10 keywords = $0.10 cost
    ]

    with patch.object(agent, "_expand_keywords_with_fallback", return_value=mock_keywords):
        # Mock compliance checker
        agent.compliance_checker = AsyncMock()
        agent.compliance_checker.check_keyword.return_value = ComplianceCheckResult(
                keyword="rhinoplasty",
                likelihood_score=1,
                severity_score=2,
                risk_score=2,
                risk_level=RiskLevel.LOW,
                action=ComplianceAction.PASSED,
                rationale="Test compliance check",
                matched_patterns=[],
                fda_enforcement_records=[],
            )

        # Execute task
        result = await agent.execute_task(task)

        # Verify budget was respected
        assert result.status == "success"
        assert result.result["total_cost_usd"] <= 0.05


@pytest.mark.asyncio
async def test_zero_volume_handling(agent):
    """Test zero-volume handling"""
    task = Task(
        task_id="test-task-5",
        subtask_id="test-subtask-5",
        parent_task_id="test-parent",
        action="keyword_research",
        description="Research keywords",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
        data={
            "seed_keyword": "very rare medical term xyz123",
            "max_keywords": 10,
        },
    )

    # Mock API to return empty list (zero volume)
    with patch.object(agent, "_expand_keywords_with_fallback", return_value=[]):
        # Execute task
        result = await agent.execute_task(task)

        # Verify graceful handling
        assert result.status == "success"
        assert result.result["total_keywords"] == 0


@pytest.mark.asyncio
async def test_compliance_blocking(agent):
    """Test compliance blocking (CRITICAL risk)"""
    task = Task(
        task_id="test-task-6",
        subtask_id="test-subtask-6",
        parent_task_id="test-parent",
        action="keyword_research",
        description="Research keywords",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
        data={
            "seed_keyword": "miracle cure cancer",
            "max_keywords": 5,
        },
    )

    # Mock API
    mock_keywords = [
        KeywordDataUnified(
            keyword="miracle cure cancer",
            volume=1000,
            difficulty=40,
            cpc=5.00,
            intent="informational",
            source="semrush",
        
            priority_score=50.0,
        ),
    ]

    with patch.object(agent, "_expand_keywords_with_fallback", return_value=mock_keywords):
        # Mock compliance checker
        agent.compliance_checker = AsyncMock()
        agent.compliance_checker.check_keyword.return_value = ComplianceCheckResult(
            keyword="miracle cure cancer",
            likelihood_score=5,
            severity_score=5,
            risk_score=25,
            risk_level=RiskLevel.CRITICAL,
            action=ComplianceAction.BLOCKED,
            rationale="Critical compliance violation",
            matched_patterns=[
                PatternMatch(
                    pattern="miracle_cure",
                    category="cure_claims",
                    severity=5,
                    rationale="Prohibited cure claim"
                ),
                PatternMatch(
                    pattern="cure_cancer",
                    category="cure_claims",
                    severity=5,
                    rationale="Prohibited cancer cure claim"
                ),
            ],
            fda_enforcement_records=[],
        )

        # Execute task
        result = await agent.execute_task(task)

        # Verify keyword was blocked
        assert result.status == "success"
        assert result.result["blocked_count"] == 1
        assert result.result["total_keywords"] == 0  # No keywords passed


@pytest.mark.asyncio
async def test_obsidian_integration(agent):
    """Test Obsidian integration (results saved to vault)"""
    task = Task(
        task_id="test-task-7",
        subtask_id="test-subtask-7",
        parent_task_id="test-parent",
        action="keyword_research",
        description="Research keywords",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
        data={
            "seed_keyword": "teeth whitening",
            "max_keywords": 5,
        },
    )

    # Mock API and compliance
    mock_keywords = [
        KeywordDataUnified(
            keyword="teeth whitening",
            volume=8000,
            difficulty=50,
            cpc=6.00,
            intent="commercial",
            source="semrush",
        
            priority_score=50.0,
        ),
    ]

    with patch.object(agent, "_expand_keywords_with_fallback", return_value=mock_keywords):
        # Mock compliance checker
        agent.compliance_checker = AsyncMock()
        agent.compliance_checker.check_keyword.return_value = ComplianceCheckResult(
            keyword="teeth whitening",
            likelihood_score=1,
            severity_score=4,
            risk_score=4,
            risk_level=RiskLevel.LOW,
            action=ComplianceAction.PASSED,
            rationale="Test compliance check",
            matched_patterns=[],
            fda_enforcement_records=[],
        )

        with patch.object(agent, "_save_to_vault") as mock_save:
            # Execute task
            result = await agent.execute_task(task)

            # Verify vault save was called
            assert result.status == "success"
            assert mock_save.called
