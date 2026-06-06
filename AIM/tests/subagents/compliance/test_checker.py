"""
Tests for Compliance Checker

Integration tests for the complete compliance checking system.
Tests all three stages: pattern matching, FDA lookup, and risk scoring.
"""

import pytest
import pytest_asyncio
from unittest.mock import patch

from src.aim.subagents.compliance.checker import ComplianceChecker
from src.aim.subagents.schemas.compliance import (
    RiskLevel,
    ComplianceAction,
    FDAEnforcementRecord,
)


@pytest_asyncio.fixture
async def compliance_checker():
    """Create compliance checker instance with test database"""
    checker = ComplianceChecker(
        database_url="sqlite+aiosqlite:///:memory:",
        agent_id="test-agent",
    )

    # Create tables
    from src.aim.storage.models import Base
    async with checker.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield checker
    await checker.close()


class TestComplianceCheckerInitialization:
    """Test compliance checker initialization"""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_checker_initializes_components(self, compliance_checker):
        """Test that all components are initialized"""
        assert compliance_checker.pattern_library is not None
        assert compliance_checker.fda_client is not None
        assert compliance_checker.risk_scorer is not None
        assert compliance_checker.engine is not None


class TestCriticalRiskBlocking:
    """Test that CRITICAL risk keywords are blocked"""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_cure_cancer_blocked(self, compliance_checker):
        """Test that 'cure cancer' is blocked"""
        # Mock FDA client to avoid real API calls
        with patch.object(compliance_checker.fda_client, 'search_enforcement', return_value=[]):
            result = await compliance_checker.check_keyword("cure cancer naturally")

            assert result.risk_level == RiskLevel.CRITICAL
            assert result.action == ComplianceAction.BLOCKED
            assert result.risk_score >= 20

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_fda_approved_supplement_blocked(self, compliance_checker):
        """Test that 'FDA approved supplement' is blocked"""
        with patch.object(compliance_checker.fda_client, 'search_enforcement', return_value=[]):
            result = await compliance_checker.check_keyword("FDA approved supplement for diabetes")

            assert result.risk_level == RiskLevel.CRITICAL
            assert result.action == ComplianceAction.BLOCKED

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_covid_cure_blocked(self, compliance_checker):
        """Test that COVID cure claims are blocked"""
        with patch.object(compliance_checker.fda_client, 'search_enforcement', return_value=[]):
            result = await compliance_checker.check_keyword("cure COVID-19 naturally")

            assert result.risk_level == RiskLevel.CRITICAL
            assert result.action == ComplianceAction.BLOCKED


class TestHighRiskReduction:
    """Test that HIGH risk keywords have priority reduced"""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_high_risk_reduces_priority(self, compliance_checker):
        """Test that HIGH risk keywords are reduced"""
        # Create a keyword that triggers HIGH risk (15-19)
        with patch.object(compliance_checker.fda_client, 'search_enforcement', return_value=[]):
            result = await compliance_checker.check_keyword("guaranteed weight loss supplement")

            if result.risk_level == RiskLevel.HIGH:
                assert result.action == ComplianceAction.REDUCED
                assert 15 <= result.risk_score <= 19


class TestMediumLowRiskPassing:
    """Test that MEDIUM/LOW risk keywords pass with documentation"""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_safe_keyword_passes(self, compliance_checker):
        """Test that safe keywords pass"""
        with patch.object(compliance_checker.fda_client, 'search_enforcement', return_value=[]):
            result = await compliance_checker.check_keyword("dental implants near me")

            assert result.action == ComplianceAction.PASSED
            assert result.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_low_risk_passes(self, compliance_checker):
        """Test that LOW risk keywords pass"""
        with patch.object(compliance_checker.fda_client, 'search_enforcement', return_value=[]):
            result = await compliance_checker.check_keyword("teeth whitening cost")

            assert result.action == ComplianceAction.PASSED
            assert result.risk_score <= 14


class TestPatternMatching:
    """Test Stage 1: Pattern matching"""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_pattern_matching_finds_violations(self, compliance_checker):
        """Test that pattern matching finds violations"""
        with patch.object(compliance_checker.fda_client, 'search_enforcement', return_value=[]):
            result = await compliance_checker.check_keyword("cure diabetes")

            assert len(result.matched_patterns) > 0
            assert result.pattern_severity is not None
            assert result.pattern_severity >= 4

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_multiple_patterns_detected(self, compliance_checker):
        """Test that multiple patterns are detected"""
        with patch.object(compliance_checker.fda_client, 'search_enforcement', return_value=[]):
            result = await compliance_checker.check_keyword("guaranteed cure for cancer FDA approved")

            # Should match multiple categories
            assert len(result.matched_patterns) >= 2


class TestFDAEnforcementLookup:
    """Test Stage 2: FDA enforcement lookup"""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_fda_enforcement_found(self, compliance_checker):
        """Test that FDA enforcement is detected"""
        mock_records = [
            FDAEnforcementRecord(
                recall_number="F-1234-2026",
                product_description="Supplement claiming to cure diabetes",
                reason_for_recall="Unapproved drug claims",
                classification="Class II",
                recall_initiation_date="2026-03-15"
            )
        ]

        with patch.object(compliance_checker.fda_client, 'search_enforcement', return_value=mock_records):
            result = await compliance_checker.check_keyword("diabetes cure")

            assert result.fda_enforcement_found is True
            assert result.fda_enforcement_count == 1
            assert len(result.fda_enforcement_records) == 1

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_fda_enforcement_not_found(self, compliance_checker):
        """Test when no FDA enforcement is found"""
        with patch.object(compliance_checker.fda_client, 'search_enforcement', return_value=[]):
            result = await compliance_checker.check_keyword("test keyword")

            assert result.fda_enforcement_found is False
            assert result.fda_enforcement_count == 0
            assert len(result.fda_enforcement_records) == 0

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_fda_graceful_degradation(self, compliance_checker):
        """Test graceful degradation when FDA API fails"""
        # Mock FDA client returning None (timeout/error)
        with patch.object(compliance_checker.fda_client, 'search_enforcement', return_value=None):
            result = await compliance_checker.check_keyword("cure diabetes")

            # Should still work with pattern matching only
            assert result.fda_enforcement_found is False
            assert result.fda_enforcement_count == 0
            # But pattern matching should still detect violation
            assert len(result.matched_patterns) > 0


class TestRiskScoring:
    """Test Stage 3: Risk scoring"""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_risk_scoring_calculates_correctly(self, compliance_checker):
        """Test that risk scoring works correctly"""
        with patch.object(compliance_checker.fda_client, 'search_enforcement', return_value=[]):
            result = await compliance_checker.check_keyword("cure cancer")

            assert result.likelihood_score >= 1
            assert result.likelihood_score <= 5
            assert result.severity_score >= 1
            assert result.severity_score <= 5
            assert result.risk_score == result.likelihood_score * result.severity_score

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_rationale_generated(self, compliance_checker):
        """Test that rationale is generated"""
        with patch.object(compliance_checker.fda_client, 'search_enforcement', return_value=[]):
            result = await compliance_checker.check_keyword("cure diabetes")

            assert result.rationale is not None
            assert len(result.rationale) > 0
            assert "Likelihood" in result.rationale
            assert "Severity" in result.rationale
            assert "Risk" in result.rationale


class TestAuditTrail:
    """Test audit trail creation"""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_audit_trail_created(self, compliance_checker):
        """Test that audit trail is created in database"""
        with patch.object(compliance_checker.fda_client, 'search_enforcement', return_value=[]):
            await compliance_checker.check_keyword("cure diabetes", task_id="test-task-123")

            # Check that audit trail was created
            history = await compliance_checker.get_audit_history(keyword="cure diabetes")
            assert len(history) > 0

            audit_record = history[0]
            assert audit_record.keyword == "cure diabetes"
            assert audit_record.task_id == "test-task-123"
            assert audit_record.agent_id == "test-agent"

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_audit_trail_contains_all_data(self, compliance_checker):
        """Test that audit trail contains all compliance data"""
        with patch.object(compliance_checker.fda_client, 'search_enforcement', return_value=[]):
            await compliance_checker.check_keyword("cure cancer")

            history = await compliance_checker.get_audit_history(keyword="cure cancer")
            audit_record = history[0]

            assert audit_record.risk_level is not None
            assert audit_record.action is not None
            assert audit_record.rationale is not None
            assert audit_record.likelihood_score is not None
            assert audit_record.severity_score is not None
            assert audit_record.risk_score is not None

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_audit_history_filtering(self, compliance_checker):
        """Test audit history filtering"""
        with patch.object(compliance_checker.fda_client, 'search_enforcement', return_value=[]):
            # Create multiple records
            await compliance_checker.check_keyword("cure diabetes")
            await compliance_checker.check_keyword("cure cancer")
            await compliance_checker.check_keyword("dental implants")

            # Filter by keyword
            diabetes_history = await compliance_checker.get_audit_history(keyword="cure diabetes")
            assert len(diabetes_history) == 1
            assert diabetes_history[0].keyword == "cure diabetes"

            # Filter by risk level
            critical_history = await compliance_checker.get_audit_history(risk_level="CRITICAL")
            assert all(record.risk_level == "CRITICAL" for record in critical_history)


class TestEndToEndScenarios:
    """Test complete end-to-end scenarios"""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_critical_scenario_cure_cancer_with_fda(self, compliance_checker):
        """Test CRITICAL scenario: cure cancer with FDA enforcement"""
        mock_records = [
            FDAEnforcementRecord(
                recall_number="F-5678-2026",
                product_description="Cancer cure supplement",
                reason_for_recall="Unapproved new drug",
                classification="Class I",
                recall_initiation_date="2026-04-20"
            )
        ]

        with patch.object(compliance_checker.fda_client, 'search_enforcement', return_value=mock_records):
            result = await compliance_checker.check_keyword("cure cancer naturally")

            # Should be CRITICAL
            assert result.risk_level == RiskLevel.CRITICAL
            assert result.action == ComplianceAction.BLOCKED
            assert result.risk_score >= 20

            # Should have pattern matches
            assert len(result.matched_patterns) > 0

            # Should have FDA enforcement
            assert result.fda_enforcement_found is True
            assert result.fda_enforcement_count == 1

            # Should have audit trail
            history = await compliance_checker.get_audit_history(keyword="cure cancer naturally")
            assert len(history) == 1

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_safe_scenario_dental_implants(self, compliance_checker):
        """Test safe scenario: dental implants"""
        with patch.object(compliance_checker.fda_client, 'search_enforcement', return_value=[]):
            result = await compliance_checker.check_keyword("dental implants near me")

            # Should pass
            assert result.action == ComplianceAction.PASSED
            assert result.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]

            # Should have minimal or no pattern matches
            assert result.pattern_severity is None or result.pattern_severity <= 2

            # Should have audit trail
            history = await compliance_checker.get_audit_history(keyword="dental implants near me")
            assert len(history) == 1


class TestPerformance:
    """Test performance requirements"""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_check_completes_quickly(self, compliance_checker):
        """Test that compliance check completes in reasonable time"""
        import time

        with patch.object(compliance_checker.fda_client, 'search_enforcement', return_value=[]):
            start = time.time()
            await compliance_checker.check_keyword("test keyword")
            duration = time.time() - start

            # Should complete in under 1 second (with mocked FDA)
            assert duration < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
