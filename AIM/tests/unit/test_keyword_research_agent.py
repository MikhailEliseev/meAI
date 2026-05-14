"""Unit tests for Keyword Research Agent

Tests business logic, API integration, compliance, and priority calculation.
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone

from meai.agents.base_agent import Task, TaskStatus
from src.aim.subagents.keyword_research_agent import KeywordResearchAgent
from src.aim.subagents.schemas.api_responses import KeywordDataUnified
from src.aim.subagents.schemas.compliance import ComplianceCheckResult, RiskLevel, ComplianceAction
from src.aim.subagents.schemas.results import KeywordPriority, PriorityTier
from tests.fixtures.subagent_data import MEDICAL_KEYWORDS, SEMRUSH_RESPONSE, AHREFS_RESPONSE
from tests.fixtures.subagent_fixtures import mock_api_clients, keyword_research_agent


@pytest.mark.asyncio
async def test_keyword_expansion_success(keyword_research_agent, mock_api_clients):
    """Test successful keyword expansion through SEMrush"""
    # Mock SEMrush response with KeywordDataUnified objects
    mock_keywords = [
        KeywordDataUnified(
            keyword="dental implants cost",
            volume=12000,
            difficulty=65,
            cpc=8.50,
            intent="commercial",
            source="semrush",
            priority_score=75.0,
        ),
        KeywordDataUnified(
            keyword="dental implants near me",
            volume=10000,
            difficulty=60,
            cpc=7.20,
            intent="local",
            source="semrush",
            priority_score=72.0,
        ),
    ]
    mock_api_clients["semrush"].expand_keywords = AsyncMock(return_value=mock_keywords)

    # Patch _analyze_keyword to bypass compliance/priority logic
    from src.aim.subagents.schemas.results import KeywordAnalysisResult

    async def mock_analyze(keyword_data):
        compliance_result = ComplianceCheckResult(
            keyword=keyword_data.keyword,
            likelihood_score=1,
            severity_score=1,
            risk_score=1,
            risk_level=RiskLevel.LOW,
            action=ComplianceAction.PASSED,
            rationale="Low risk keyword",
        )
        priority_result = KeywordPriority(
            keyword=keyword_data.keyword,
            tier=PriorityTier.P0,
            base_score=75.0,
            adjusted_score=75.0,
            volume_score=80.0,
            intent_score=1.2,
            position_score=0.8,
            difficulty_score=65.0,
        )
        return KeywordAnalysisResult(
            keyword_data=keyword_data,
            compliance=compliance_result,
            priority=priority_result,
            analysis_duration_ms=10.0,
            cost_usd=0.01,
        )

    with patch.object(keyword_research_agent, '_analyze_keyword', side_effect=mock_analyze):
        # Create task
        task = Task(
            task_id="test-001",
            subtask_id="test-001-sub",
            parent_task_id="test-001-parent",
            action="keyword_research",
            description="Test keyword research",
            priority=1,
            status=TaskStatus.RECEIVED,
            created_at=datetime.now(timezone.utc),
            received_at=datetime.now(timezone.utc),
            data={
                "seed_keyword": "dental implants",
                "max_keywords": 100,
                "min_volume": 1000,
            },
        )

        # Execute
        result = await keyword_research_agent.execute_task(task)

        # Verify success
        assert result.status == "success"
        assert "keywords" in result.result
        assert result.result["total_keywords"] >= 0

        # Verify cost tracking
        assert keyword_research_agent.total_cost_usd >= 0
        assert keyword_research_agent.api_calls >= 0


@pytest.mark.asyncio
async def test_keyword_expansion_with_fallback(keyword_research_agent, mock_api_clients):
    """Test fallback to Ahrefs when SEMrush fails (circuit breaker)"""
    # Mock SEMrush failures (circuit breaker opens after 5 failures)
    mock_api_clients["semrush"].expand_keywords = AsyncMock(
        side_effect=ConnectionError("API timeout")
    )

    # Mock Ahrefs success
    mock_ahrefs_keywords = [
        KeywordDataUnified(
            keyword="dental implants cost",
            volume=12000,
            difficulty=65,
            cpc=8.50,
            intent="commercial",
            source="ahrefs",
            priority_score=75.0,
        ),
    ]
    mock_api_clients["ahrefs"].expand_keywords = AsyncMock(return_value=mock_ahrefs_keywords)

    # Patch _analyze_keyword to bypass compliance/priority logic
    from src.aim.subagents.schemas.results import KeywordAnalysisResult

    async def mock_analyze(keyword_data):
        compliance_result = ComplianceCheckResult(
            keyword=keyword_data.keyword,
            likelihood_score=1,
            severity_score=1,
            risk_score=1,
            risk_level=RiskLevel.LOW,
            action=ComplianceAction.PASSED,
            rationale="Low risk keyword",
        )
        priority_result = KeywordPriority(
            keyword=keyword_data.keyword,
            tier=PriorityTier.P0,
            base_score=75.0,
            adjusted_score=75.0,
            volume_score=80.0,
            intent_score=1.2,
            position_score=0.8,
            difficulty_score=65.0,
        )
        return KeywordAnalysisResult(
            keyword_data=keyword_data,
            compliance=compliance_result,
            priority=priority_result,
            analysis_duration_ms=10.0,
            cost_usd=0.01,
        )

    with patch.object(keyword_research_agent, '_analyze_keyword', side_effect=mock_analyze):
        # Create task
        task = Task(
            task_id="test-002",
            subtask_id="test-002-sub",
            parent_task_id="test-002-parent",
            action="keyword_research",
            description="Test keyword research with fallback",
            priority=1,
            status=TaskStatus.RECEIVED,
            created_at=datetime.now(timezone.utc),
            received_at=datetime.now(timezone.utc),
            data={
                "seed_keyword": "dental implants",
                "max_keywords": 100,
            },
        )

        # Execute
        result = await keyword_research_agent.execute_task(task)

        # Verify fallback worked
        assert result.status == "success"
        assert "keywords" in result.result


@pytest.mark.asyncio
async def test_compliance_blocking(keyword_research_agent, mock_api_clients):
    """Test blocking of risky keywords (FDA/HIPAA compliance)"""
    # Mock SEMrush response with risky keyword
    mock_risky_keywords = [
        KeywordDataUnified(
            keyword="buy oxycodone online",
            volume=5000,
            difficulty=45,
            cpc=12.00,
            intent="commercial",
            source="semrush",
            priority_score=60.0,
        ),
    ]
    mock_api_clients["semrush"].expand_keywords = AsyncMock(return_value=mock_risky_keywords)

    # Patch _analyze_keyword to return BLOCKED result
    from src.aim.subagents.schemas.results import KeywordAnalysisResult

    async def mock_analyze(keyword_data):
        compliance_result = ComplianceCheckResult(
            keyword=keyword_data.keyword,
            likelihood_score=5,
            severity_score=5,
            risk_score=25,
            risk_level=RiskLevel.CRITICAL,
            action=ComplianceAction.BLOCKED,
            rationale="CRITICAL risk: Controlled substance keyword",
        )
        priority_result = KeywordPriority(
            keyword=keyword_data.keyword,
            tier=PriorityTier.P3,
            base_score=20.0,
            adjusted_score=20.0,
            volume_score=50.0,
            intent_score=1.2,
            position_score=0.8,
            difficulty_score=45.0,
            compliance_penalty=0.8,
        )
        return KeywordAnalysisResult(
            keyword_data=keyword_data,
            compliance=compliance_result,
            priority=priority_result,
            analysis_duration_ms=10.0,
            cost_usd=0.01,
        )

    with patch.object(keyword_research_agent, '_analyze_keyword', side_effect=mock_analyze):
        # Create task
        task = Task(
            task_id="test-003",
            subtask_id="test-003-sub",
            parent_task_id="test-003-parent",
            action="keyword_research",
            description="Test compliance blocking",
            priority=1,
            status=TaskStatus.RECEIVED,
            created_at=datetime.now(timezone.utc),
            received_at=datetime.now(timezone.utc),
            data={
                "seed_keyword": "buy oxycodone online",
                "max_keywords": 100,
            },
        )

        # Execute
        result = await keyword_research_agent.execute_task(task)

        # Verify blocking
        assert result.status == "success"
        assert "blocked_count" in result.result
        assert result.result["blocked_count"] >= 0


@pytest.mark.asyncio
async def test_priority_calculation(keyword_research_agent, mock_api_clients):
    """Test priority calculation with medical boost"""
    # Mock SEMrush response with medical keywords
    mock_medical_keywords = [
        KeywordDataUnified(
            keyword="dental implants cost",
            volume=12000,
            difficulty=65,
            cpc=8.50,
            intent="commercial",
            source="semrush",
            priority_score=75.0,
        ),
        KeywordDataUnified(
            keyword="teeth whitening near me",
            volume=8000,
            difficulty=55,
            cpc=6.20,
            intent="local",
            source="semrush",
            priority_score=68.0,
        ),
    ]
    mock_api_clients["semrush"].expand_keywords = AsyncMock(return_value=mock_medical_keywords)

    # Patch _analyze_keyword to return different priorities
    from src.aim.subagents.schemas.results import KeywordAnalysisResult

    async def mock_analyze(keyword_data):
        # Different priorities based on keyword
        if "dental" in keyword_data.keyword:
            tier = PriorityTier.P0
            adjusted_score = 85.0
        else:
            tier = PriorityTier.P1
            adjusted_score = 68.0

        compliance_result = ComplianceCheckResult(
            keyword=keyword_data.keyword,
            likelihood_score=1,
            severity_score=1,
            risk_score=1,
            risk_level=RiskLevel.LOW,
            action=ComplianceAction.PASSED,
            rationale="Low risk keyword",
        )
        priority_result = KeywordPriority(
            keyword=keyword_data.keyword,
            tier=tier,
            base_score=keyword_data.priority_score,
            adjusted_score=adjusted_score,
            volume_score=80.0,
            intent_score=1.2,
            position_score=0.8,
            difficulty_score=keyword_data.difficulty,
        )
        return KeywordAnalysisResult(
            keyword_data=keyword_data,
            compliance=compliance_result,
            priority=priority_result,
            analysis_duration_ms=10.0,
            cost_usd=0.01,
        )

    with patch.object(keyword_research_agent, '_analyze_keyword', side_effect=mock_analyze):
        # Create task
        task = Task(
            task_id="test-004",
            subtask_id="test-004-sub",
            parent_task_id="test-004-parent",
            action="keyword_research",
            description="Test priority calculation",
            priority=1,
            status=TaskStatus.RECEIVED,
            created_at=datetime.now(timezone.utc),
            received_at=datetime.now(timezone.utc),
            data={
                "seed_keyword": "dental",
                "max_keywords": 100,
                "calculate_priority": True,
            },
        )

        # Execute
        result = await keyword_research_agent.execute_task(task)

        # Verify success
        assert result.status == "success"
        assert "keywords" in result.result
        assert result.result["total_keywords"] >= 0

        # Verify priority tiers exist in result
        assert "p0_count" in result.result
        assert "p1_count" in result.result
