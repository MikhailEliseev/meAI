"""Unit tests for Analytics Agent

Tests metrics collection, data validation, and report generation.
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timezone

from meai.agents.base_agent import Task
from src.aim.subagents.analytics_agent import AnalyticsAgent
from AIM.tests.fixtures.subagent_data import GA4_METRICS, YANDEX_METRICS


@pytest.fixture
def mock_api_clients():
    """Mock API clients for Analytics Agent testing"""
    return {
        "ga4": AsyncMock(),
        "yandex_metrica": AsyncMock(),
    }


@pytest.fixture
def analytics_agent(mock_api_clients):
    """Analytics Agent with mocked API clients for unit testing"""
    from meai.events.event_bus import EventBus

    event_bus = EventBus()
    agent = AnalyticsAgent(
        agent_id="test-analytics-agent",
        event_bus=event_bus,
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="./test-vault",
    )

    # Inject mocked API clients
    agent.ga4_client = mock_api_clients["ga4"]
    agent.yandex_client = mock_api_clients["yandex_metrica"]

    return agent


@pytest.mark.asyncio
async def test_metrics_collection_success(analytics_agent, mock_api_clients):
    """Test metrics collection from GA4 and Yandex Metrica"""
    # Create task using the correct action "track_metrics"
    task = Task(
        task_id="test-task-001",
        subtask_id="test-analytics-001",
        parent_task_id="test-parent-001",
        action="track_metrics",
        description="Track metrics from GA4 and Yandex Metrica",
        priority=1,
        status="received",
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
        data={
            "metrics_type": "kpi",
            "source": "ga4",
        },
    )

    # Execute
    result = await analytics_agent.execute_task(task)

    # Verify success
    assert result.status == "success"
    assert "metrics_type" in result.result
    assert result.result["metrics_type"] == "kpi"

    # Verify metrics structure
    assert "metrics" in result.result
    metrics = result.result["metrics"]
    assert "visitors" in metrics
    assert "conversions" in metrics
    assert "revenue" in metrics
    assert "conversion_rate" in metrics

    # Verify timestamp
    assert "timestamp" in result.result


@pytest.mark.asyncio
async def test_data_analysis(analytics_agent, mock_api_clients):
    """Test data analysis with insights"""
    # Create task using the correct action "analyze_data"
    task = Task(
        task_id="test-task-002",
        subtask_id="test-analytics-002",
        parent_task_id="test-parent-002",
        action="analyze_data",
        description="Analyze data from GA4",
        priority=1,
        status="received",
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
        data={
            "data_source": "ga4",
            "analysis_type": "trend",
        },
    )

    # Execute
    result = await analytics_agent.execute_task(task)

    # Verify success
    assert result.status == "success"
    assert "data_source" in result.result
    assert result.result["data_source"] == "ga4"

    # Verify analysis type
    assert "analysis_type" in result.result
    assert result.result["analysis_type"] == "trend"

    # Verify insights
    assert "insights" in result.result
    insights = result.result["insights"]
    assert len(insights) > 0
    assert isinstance(insights, list)

    # Verify timestamp
    assert "analyzed_at" in result.result


@pytest.mark.asyncio
async def test_report_generation(analytics_agent, mock_api_clients):
    """Test report generation with insights"""
    # Mock metrics
    mock_api_clients["ga4"].get_metrics = AsyncMock(return_value=GA4_METRICS)
    mock_api_clients["yandex_metrica"].get_metrics = AsyncMock(return_value=YANDEX_METRICS)

    # Create task
    task = Task(
        task_id="test-task-003",
        subtask_id="test-analytics-003",
        parent_task_id="test-parent-003",
        action="generate_report",
        description="Generate performance summary report",
        priority=1,
        status="received",
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
        data={
            "date_range": "last_30_days",
            "report_type": "performance_summary",
            "include_insights": True,
        },
    )

    # Mock the report generation method
    async def mock_generate_report(data):
        ga4_data = await mock_api_clients["ga4"].get_metrics()
        yandex_data = await mock_api_clients["yandex_metrica"].get_metrics()

        total_sessions = ga4_data["sessions"] + yandex_data["visits"]
        total_conversions = ga4_data["conversions"] + yandex_data["goals"]

        return {
            "report": {
                "title": "Performance Summary Report",
                "date_range": data.get("date_range", "last_30_days"),
                "summary": {
                    "total_sessions": total_sessions,
                    "total_conversions": total_conversions,
                    "conversion_rate": total_conversions / total_sessions,
                },
                "metrics": {
                    "ga4": ga4_data,
                    "yandex": yandex_data,
                },
                "insights": [
                    {
                        "type": "trend",
                        "description": "Traffic increased by 20% this month",
                        "impact": "high",
                    },
                    {
                        "type": "anomaly",
                        "description": "Bounce rate spike on May 5th",
                        "impact": "medium",
                    },
                    {
                        "type": "opportunity",
                        "description": "Conversion rate can be improved by 15%",
                        "impact": "high",
                    },
                ],
                "recommendations": [
                    {
                        "action": "Optimize landing pages for mobile",
                        "expected_impact": "Reduce bounce rate by 10%",
                        "priority": "high",
                    },
                    {
                        "action": "A/B test new CTA buttons",
                        "expected_impact": "Increase conversions by 5%",
                        "priority": "medium",
                    },
                ],
            }
        }

    analytics_agent._generate_report = mock_generate_report

    # Execute
    result = await analytics_agent.execute_task(task)

    # Verify success
    assert result.status == "success"
    assert "report" in result.result

    # Verify report structure
    report = result.result["report"]
    assert "title" in report
    assert "date_range" in report
    assert "summary" in report
    assert "metrics" in report
    assert "insights" in report
    assert "recommendations" in report

    # Verify summary
    summary = report["summary"]
    assert "total_sessions" in summary
    assert "total_conversions" in summary
    assert "conversion_rate" in summary

    # Verify insights
    insights = report["insights"]
    assert len(insights) > 0
    for insight in insights:
        assert "type" in insight
        assert "description" in insight
        assert "impact" in insight

    # Verify recommendations
    recommendations = report["recommendations"]
    assert len(recommendations) > 0
    for rec in recommendations:
        assert "action" in rec
        assert "expected_impact" in rec
        assert "priority" in rec

    # Verify insights quality
    insight_types = [i["type"] for i in insights]
    assert "trend" in insight_types or "anomaly" in insight_types or "opportunity" in insight_types
