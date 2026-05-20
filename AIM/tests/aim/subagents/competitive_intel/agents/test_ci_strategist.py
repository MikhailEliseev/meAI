"""
NO-MOCK-04: Tests for "3 numbers" computation in ci_strategist.

Verifies that ci_strategist computes patients/month, time-to-result,
and cost-per-patient using real formulas (not random generation).
"""

import pytest
from unittest.mock import patch, MagicMock

# Real benchmarks from ci_strategist.__init__ (Russian medical market, 2024-2025)
CONVERSION_BENCHMARKS = {
    "стоматология": {"low": 0.02, "mid": 0.035, "high": 0.05},
    "косметология": {"low": 0.02, "mid": 0.03, "high": 0.045},
    "пластическая_хирургия": {"low": 0.01, "mid": 0.02, "high": 0.03},
    "гинекология": {"low": 0.015, "mid": 0.025, "high": 0.04},
    "офтальмология": {"low": 0.02, "mid": 0.03, "high": 0.045},
    "default": {"low": 0.015, "mid": 0.025, "high": 0.04},
}

NICHE_COMPLEXITY = {
    "стоматология": 1.0,
    "косметология": 1.1,
    "пластическая_хирургия": 1.3,
    "гинекология": 0.9,
    "офтальмология": 0.85,
    "default": 1.0,
}


def _make_strategist():
    """Create CIStrategistAgent with mocked __init__ and required attributes."""
    from aim.subagents.competitive_intel.agents.ci_strategist import CIStrategistAgent

    with patch.object(CIStrategistAgent, '__init__', lambda self, **kw: None):
        agent = CIStrategistAgent.__new__(CIStrategistAgent)
        agent.vault = MagicMock()
        agent.agent_id = "test-strategist"
        agent.conversion_benchmarks = CONVERSION_BENCHMARKS
        agent.niche_complexity = NICHE_COMPLEXITY
    return agent


@pytest.mark.asyncio
class TestThreeNumbersComputation:
    """Verify the "3 numbers" (patients/month, time-to-result, cost-per-patient)."""

    async def test_estimate_patients_per_month_with_traffic_data(self):
        """ci_strategist computes patients/month from traffic * conversion."""
        agent = _make_strategist()

        traffic_data = {
            "monthly_organic_traffic": 5000,
            "conversion_rate": 0.025,
        }

        result = agent._estimate_patients_per_month(
            traffic_data=traffic_data,
            niche="стоматология",
        )

        assert isinstance(result, dict)
        assert "patients_per_month" in result
        patients = result["patients_per_month"]
        # Should have low/mid/high scenarios
        if isinstance(patients, dict):
            assert patients.get("low", 0) > 0
            assert patients.get("mid", 0) > 0
            assert patients.get("high", 0) > 0
            # Mid should be ~175 (5000 * 0.035)
            assert 50 < patients.get("mid", 0) < 500
        else:
            assert patients > 0
            assert patients < 500

    async def test_estimate_cost_per_patient_formula(self):
        """ci_strategist cost_per_patient = CPC / conversion_rate."""
        agent = _make_strategist()

        result = agent._estimate_cost_per_patient(
            avg_cpc=150,  # RUB (Russian medical default)
            conversion_rate=0.025,
        )

        assert isinstance(result, dict)
        assert "cost_per_patient" in result
        cost = result["cost_per_patient"]
        # 150 / 0.025 = 6000 RUB
        assert cost == 6000

    async def test_estimate_time_to_result_with_factors(self):
        """ci_strategist time_to_result factors niche complexity and competition."""
        agent = _make_strategist()

        result = agent._estimate_time_to_result(
            niche="пластическая_хирургия",  # complexity 1.3
            competition_level="high",       # factor 1.3
            budget_level="low",             # factor 1.4
        )

        assert isinstance(result, dict)
        time_val = result.get("estimated_months", 0)
        # Base 4.0 * 1.3 * 1.3 * 1.4 ≈ 9.5 months
        assert time_val > 3
        assert time_val <= 24

    async def test_estimate_patients_default_niche(self):
        """ci_strategist uses default benchmarks for unknown niches."""
        agent = _make_strategist()

        traffic_data = {"monthly_organic_traffic": 3000}

        result = agent._estimate_patients_per_month(
            traffic_data=traffic_data,
            niche="unknown_niche",
        )

        assert isinstance(result, dict)
        assert "patients_per_month" in result
