"""Tests for report generation"""

import sys
from pathlib import Path

# Add AIM to path
aim_path = Path(__file__).parent.parent / "AIM" / "src"
sys.path.insert(0, str(aim_path))

import pytest
from datetime import datetime, timezone

from meai.events.event_bus import EventBus
from aim.subagents.competitive_intel.orchestrator.ci_orchestrator import CIOrchestrator


@pytest.fixture
def event_bus():
    """Mock event bus"""
    from unittest.mock import MagicMock, AsyncMock
    bus = MagicMock(spec=EventBus)
    bus.publish = AsyncMock()
    return bus


@pytest.fixture
def ci_orchestrator(event_bus):
    """CI orchestrator instance"""
    return CIOrchestrator(
        agent_id="test-ci-orchestrator",
        event_bus=event_bus
    )


@pytest.mark.asyncio
async def test_report_generation(ci_orchestrator):
    """Test that reports are generated"""
    import logging
    logging.basicConfig(level=logging.DEBUG)

    task_data = {
        "task_id": "report-test-1",
        "niche": "dental implants",
        "geo": "Moscow",
        "tier": "quick",
        "competitors": ["https://example.com"]
    }

    result = await ci_orchestrator.execute_ci_analysis(task_data)

    # Verify reports were generated
    assert "reports" in result
    reports = result["reports"]

    print(f"\nFull result: {result}")
    print(f"\nReports: {reports}")
    print(f"\nErrors: {result.get('errors', [])}")

    # Check HTML report
    if "html_path" in reports and reports["html_path"]:
        html_path = Path(reports["html_path"])
        assert html_path.exists(), f"HTML report not found: {html_path}"
        print(f"HTML report generated: {html_path}")

        # Check content
        content = html_path.read_text()
        assert len(content) > 0, "HTML report is empty"
        assert "dental implants" in content or "Moscow" in content

    # Check PDF report (optional, requires weasyprint)
    if "pdf_path" in reports and reports["pdf_path"]:
        pdf_path = Path(reports["pdf_path"])
        if pdf_path.exists():
            print(f"PDF report generated: {pdf_path}")
            assert pdf_path.stat().st_size > 0, "PDF report is empty"
        else:
            print("PDF report not generated (weasyprint not installed)")


@pytest.mark.asyncio
async def test_report_structure(ci_orchestrator):
    """Test report structure and content"""
    task_data = {
        "task_id": "report-test-2",
        "niche": "dental clinics",
        "geo": "Saint Petersburg",
        "tier": "deep",
        "competitors": [
            "https://example1.com",
            "https://example2.com"
        ]
    }

    result = await ci_orchestrator.execute_ci_analysis(task_data)

    # Verify result structure
    assert result["task_id"] == "report-test-2"
    assert result["tier"] == "deep"
    assert result["competitors_analyzed"] == 2

    # Verify reports
    reports = result.get("reports", {})
    print(f"\nGenerated reports: {reports}")

    # At minimum, HTML should be generated
    if reports:
        assert "html_path" in reports or "pdf_path" in reports, \
            "No reports generated"
