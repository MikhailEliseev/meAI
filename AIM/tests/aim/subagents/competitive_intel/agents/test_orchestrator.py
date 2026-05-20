"""
NO-MOCK-05: Tests for orchestrator quality_score null-awareness.

Verifies that CIOrchestrator._calculate_quality_score() reflects
structured null rate — when most API-gated agents return
data_source="unavailable", quality_score should be downgraded.
"""

import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.asyncio
class TestOrchestratorQualityScore:
    """Verify orchestrator quality_score detects structured null saturation."""

    async def test_quality_score_high_when_all_data_real(self):
        """quality_score should be high when all agents return real data."""
        from aim.subagents.competitive_intel.orchestrator.ci_orchestrator import CIOrchestrator

        with patch.object(CIOrchestrator, '__init__', lambda self, **kw: None):
            orchestrator = CIOrchestrator.__new__(CIOrchestrator)

            findings = {
                "phase_1": {
                    "status": "success",
                    "result": {"data_source": "serpapi", "confidence": 0.9, "competitors": 10}
                },
                "phase_2": {
                    "status": "success",
                    "result": {"data_source": "pagespeed", "confidence": 0.85, "score": 78}
                },
                "phase_3": {
                    "status": "success",
                    "result": {"data_source": "real", "confidence": 0.8, "checks_passed": 25}
                },
            }
            phases_executed = [1, 2, 3]

            score = orchestrator._calculate_quality_score(findings, phases_executed)

            assert isinstance(score, dict)
            assert score["score"] > 80  # 3/3 success = 100%

    async def test_quality_score_degraded_when_most_data_null(self):
        """quality_score should be low when >50% agents return structured null."""
        from aim.subagents.competitive_intel.orchestrator.ci_orchestrator import CIOrchestrator

        with patch.object(CIOrchestrator, '__init__', lambda self, **kw: None):
            orchestrator = CIOrchestrator.__new__(CIOrchestrator)

            findings = {
                "phase_1": {
                    "status": "failed",
                    "result": {
                        "data_source": "unavailable",
                        "confidence": 0.0,
                        "note": "SERPAPI_KEY not configured",
                    }
                },
                "phase_2": {
                    "status": "failed",
                    "result": {
                        "data_source": "unavailable",
                        "confidence": 0.0,
                        "note": "PAGESPEED_API_KEY not configured",
                    }
                },
                "phase_3": {
                    "status": "success",
                    "result": {"data_source": "real", "confidence": 0.8, "checks_passed": 25}
                },
            }
            phases_executed = [1, 2, 3]

            score = orchestrator._calculate_quality_score(findings, phases_executed)

            assert isinstance(score, dict)
            # 1/3 success = 33% → score < 50
            assert score["score"] < 50
            # Confidence should be downgraded
            assert score["confidence"] == "low"

    async def test_quality_score_detects_complete_null(self):
        """quality_score should be minimal when ALL agents return structured null."""
        from aim.subagents.competitive_intel.orchestrator.ci_orchestrator import CIOrchestrator

        with patch.object(CIOrchestrator, '__init__', lambda self, **kw: None):
            orchestrator = CIOrchestrator.__new__(CIOrchestrator)

            findings = {
                "phase_1": {
                    "status": "stub",
                    "result": {"data_source": "unavailable", "confidence": 0.0}
                },
                "phase_2": {
                    "status": "stub",
                    "result": {"data_source": "unavailable", "confidence": 0.0}
                },
            }
            phases_executed = [1, 2]

            score = orchestrator._calculate_quality_score(findings, phases_executed)

            assert isinstance(score, dict)
            # 0/2 success = 0%
            assert score["score"] == 0
            assert score["confidence"] == "low"
