"""Unit tests for Analytics Magister orchestration

Tests Analytics Magister coordination logic in isolation using mocked methods.
Covers: task routing, data collection, report generation, error handling.
"""

import pytest
from unittest.mock import AsyncMock
from pathlib import Path

from AIM.tests.fixtures.magister_fixtures import mock_analytics_subagents, analytics_magister


@pytest.mark.asyncio
async def test_analytics_magister_execute_task_success():
    """Should route tasks to correct subagents

    Scenario: Various task types (collect_data, analyze_performance, generate_report, get_insights)
    Expected: Correct delegation to subagents, status="delegated" or "success"
    """
    # Arrange: Create real AnalyticsMagister (not using fixture for this test)
    from src.aim.magisters.analytics_magister import AnalyticsMagister
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        mock_event_bus = AsyncMock()

        magister = AnalyticsMagister(
            magister_id="test-analytics",
            event_bus=mock_event_bus,
            vault_path=tmp_path / "vault",
            data_path=tmp_path / "data",
        )

        # Mock delegation method
        magister._delegate_to_subagent = AsyncMock()

        # Act & Assert: Test task routing

        # Collect data
        result = await magister.execute_task({"type": "collect_data", "sources": ["yandex_metrika"]})
        assert result["status"] == "delegated"
        assert result["subagent"] == "data_collector"
        magister._delegate_to_subagent.assert_called()

        # Analyze performance
        magister._delegate_to_subagent.reset_mock()
        result = await magister.execute_task({"type": "analyze_performance", "period": "last_month"})
        assert result["status"] == "delegated"
        assert result["subagent"] == "performance_analyzer"
        magister._delegate_to_subagent.assert_called()

        # Get insights
        magister._delegate_to_subagent.reset_mock()
        result = await magister.execute_task({"type": "get_insights", "focus_area": "traffic"})
        assert result["status"] == "delegated"
        assert result["subagent"] == "insights_generator"
        magister._delegate_to_subagent.assert_called()


@pytest.mark.asyncio
async def test_analytics_magister_generate_report_success():
    """Should generate report with collected data

    Scenario: generate_report task with mock data
    Expected: Report file created, summary returned, event published
    """
    # Arrange: Create real AnalyticsMagister
    from src.aim.magisters.analytics_magister import AnalyticsMagister
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        mock_event_bus = AsyncMock()

        magister = AnalyticsMagister(
            magister_id="test-analytics",
            event_bus=mock_event_bus,
            vault_path=tmp_path / "vault",
            data_path=tmp_path / "data",
        )

        # Mock data collection
        magister._collect_report_data = AsyncMock(return_value={
            "summary": {
                "total_sessions": 10000,
                "total_users": 7500,
                "conversion_rate": 3.5,
                "revenue": 150000,
            },
            "metrics": {
                "traffic": {"growth": "+15%"},
                "conversions": {"growth": "+8%"},
            },
            "insights": ["Traffic growing steadily"],
            "recommendations": ["Increase budget"],
        })

        # Act: Generate report
        result = await magister.execute_task({
            "type": "generate_report",
            "report_type": "monthly",
            "period": "last_month",
        })

        # Assert: Report generated
        assert result["status"] == "success"
        assert "report_file" in result
        assert Path(result["report_file"]).exists()
        assert result["summary"]["total_sessions"] == 10000

        # Verify event published
        mock_event_bus.publish.assert_called_once()


@pytest.mark.asyncio
async def test_analytics_magister_collect_report_data_partial_failure():
    """Should handle partial failure in data collection gracefully

    Scenario: _collect_report_data returns incomplete data
    Expected: Report generation continues with available data
    """
    # Arrange: Create real AnalyticsMagister
    from src.aim.magisters.analytics_magister import AnalyticsMagister
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        mock_event_bus = AsyncMock()

        magister = AnalyticsMagister(
            magister_id="test-analytics",
            event_bus=mock_event_bus,
            vault_path=tmp_path / "vault",
            data_path=tmp_path / "data",
        )

        # Mock incomplete data collection
        magister._collect_report_data = AsyncMock(return_value={
            "summary": {"total_sessions": 5000},  # Partial data
            "metrics": {},  # Empty metrics
            "insights": [],  # No insights
            "recommendations": [],  # No recommendations
        })

        # Act: Generate report with partial data
        result = await magister.execute_task({
            "type": "generate_report",
            "report_type": "weekly",
        })

        # Assert: Report generated with partial data
        assert result["status"] == "success"
        assert result["summary"]["total_sessions"] == 5000
        assert "report_file" in result


@pytest.mark.asyncio
async def test_analytics_magister_execute_task_full_failure():
    """Should handle full failure (unknown task type)

    Scenario: execute_task receives unknown task type
    Expected: Returns error status with message
    """
    # Arrange: Create real AnalyticsMagister
    from src.aim.magisters.analytics_magister import AnalyticsMagister
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        mock_event_bus = AsyncMock()

        magister = AnalyticsMagister(
            magister_id="test-analytics",
            event_bus=mock_event_bus,
            vault_path=tmp_path / "vault",
            data_path=tmp_path / "data",
        )

        # Act: Execute unknown task type
        result = await magister.execute_task({"type": "unknown_task"})

        # Assert: Error returned
        assert result["status"] == "error"
        assert "Unknown task type" in result["message"]
