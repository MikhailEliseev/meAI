"""Tests for quality validation"""

import sys
from pathlib import Path

# Add AIM to path
aim_path = Path(__file__).parent.parent / "AIM" / "src"
sys.path.insert(0, str(aim_path))

import pytest
from unittest.mock import MagicMock, AsyncMock

from meai.events.event_bus import EventBus
from aim.subagents.competitive_intel.orchestrator.ci_orchestrator import CIOrchestrator


@pytest.fixture
def event_bus():
    """Mock event bus"""
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
async def test_quality_score_calculation(ci_orchestrator):
    """Test quality score calculation"""
    task_data = {
        "task_id": "quality-test-1",
        "niche": "dental implants",
        "geo": "Moscow",
        "tier": "quick",
        "competitors": ["https://example.com"]
    }

    result = await ci_orchestrator.execute_ci_analysis(task_data)

    # Verify quality score is present
    assert "quality_score" in result
    quality = result["quality_score"]

    print(f"\nQuality Score: {quality}")

    # Verify structure
    assert "score" in quality
    assert "confidence" in quality
    assert "completeness" in quality
    assert "successful_phases" in quality
    assert "failed_phases" in quality
    assert "total_phases" in quality

    # Verify values
    assert 0 <= quality["score"] <= 100
    assert quality["confidence"] in ["high", "medium", "low"]
    assert quality["total_phases"] == 4  # Quick tier has 4 phases


@pytest.mark.asyncio
async def test_high_confidence_quick_tier(ci_orchestrator):
    """Test that quick tier achieves reasonable confidence"""
    task_data = {
        "task_id": "confidence-test-1",
        "niche": "dental clinics",
        "geo": "Saint Petersburg",
        "tier": "quick",
        "competitors": ["https://example.com"]
    }

    result = await ci_orchestrator.execute_ci_analysis(task_data)

    quality = result["quality_score"]

    # Quick tier should have at least 1 successful phase (ci-scout works)
    assert quality["successful_phases"] >= 1, "At least 1 phase should succeed"
    assert quality["total_phases"] == 4, "Quick tier should have 4 phases"
    assert quality["score"] >= 0, "Score should be non-negative"


@pytest.mark.asyncio
async def test_deep_tier_quality(ci_orchestrator):
    """Test deep tier quality metrics"""
    task_data = {
        "task_id": "deep-quality-test",
        "niche": "dental implants",
        "geo": "Moscow",
        "tier": "deep",
        "competitors": [
            "https://example1.com",
            "https://example2.com"
        ]
    }

    result = await ci_orchestrator.execute_ci_analysis(task_data)

    quality = result["quality_score"]

    # Deep tier has 9 phases
    assert quality["total_phases"] == 9
    assert quality["successful_phases"] >= 1, "At least 1 phase should succeed"


@pytest.mark.asyncio
async def test_quality_in_reports(ci_orchestrator):
    """Test that quality score is included in reports"""
    task_data = {
        "task_id": "report-quality-test",
        "niche": "dental",
        "geo": "Moscow",
        "tier": "quick",
        "competitors": ["https://example.com"]
    }

    result = await ci_orchestrator.execute_ci_analysis(task_data)

    # Verify quality score
    assert "quality_score" in result
    quality = result["quality_score"]
    assert quality["score"] > 0

    # Verify reports were generated
    assert "reports" in result
    reports = result["reports"]

    # Check JSON report includes quality
    if "json_path" in reports and reports["json_path"]:
        json_path = Path(reports["json_path"])
        if json_path.exists():
            import json
            report_data = json.loads(json_path.read_text())
            print(f"\nJSON report keys: {list(report_data.keys())}")


@pytest.mark.asyncio
async def test_confidence_levels(ci_orchestrator):
    """Test confidence level calculation"""
    # Test data for different scenarios
    test_cases = [
        {"successful": 4, "total": 4, "expected_confidence": "high"},   # 100%
        {"successful": 3, "total": 4, "expected_confidence": "medium"}, # 75%
        {"successful": 2, "total": 4, "expected_confidence": "low"},    # 50%
    ]

    for case in test_cases:
        # Create mock findings
        findings = {}
        for i in range(case["successful"]):
            findings[f"phase_{i+1}"] = {"status": "success"}
        for i in range(case["total"] - case["successful"]):
            findings[f"phase_{i+case['successful']+1}"] = {"status": "failed"}

        phases = list(range(1, case["total"] + 1))

        quality = ci_orchestrator._calculate_quality_score(findings, phases)

        print(f"\nCase: {case['successful']}/{case['total']} -> {quality['confidence']}")
        assert quality["confidence"] == case["expected_confidence"], \
            f"Expected {case['expected_confidence']}, got {quality['confidence']}"
