"""
Tests for Risk Scoring Framework

Tests likelihood calculation, severity calculation, risk scoring, and action determination.
"""

import pytest

from src.aim.subagents.compliance.risk_scorer import RiskScorer
from src.aim.subagents.schemas.compliance import (
    RiskLevel,
    ComplianceAction,
    PatternMatch,
    FDAEnforcementRecord,
)


@pytest.fixture
def risk_scorer():
    """Create risk scorer instance"""
    return RiskScorer()


@pytest.fixture
def sample_pattern_matches():
    """Sample pattern matches for testing"""
    return [
        PatternMatch(
            pattern="cure.*diabetes",
            category="cure_claims",
            severity=5,
            rationale="FDA prohibits cure claims for diabetes"
        ),
        PatternMatch(
            pattern="guaranteed.*results",
            category="guarantees",
            severity=4,
            rationale="Guaranteed results are prohibited"
        ),
    ]


@pytest.fixture
def sample_fda_records():
    """Sample FDA enforcement records"""
    return [
        FDAEnforcementRecord(
            recall_number="F-1234-2026",
            product_description="Supplement claiming to cure diabetes",
            reason_for_recall="Unapproved drug claims",
            classification="Class II",
            recall_initiation_date="2026-03-15"
        ),
    ]


class TestLikelihoodCalculation:
    """Test likelihood score calculation"""

    def test_likelihood_from_pattern_severity(self, risk_scorer):
        """Test that likelihood is based on pattern severity"""
        patterns = [
            PatternMatch(pattern="test", category="cure_claims", severity=5, rationale="test")
        ]

        likelihood = risk_scorer.calculate_likelihood(patterns, fda_enforcement_count=0)
        assert likelihood == 5

    def test_likelihood_bonus_for_fda_enforcement(self, risk_scorer):
        """Test that FDA enforcement increases likelihood"""
        patterns = [
            PatternMatch(pattern="test", category="cure_claims", severity=3, rationale="test")
        ]

        # No FDA enforcement
        likelihood_no_fda = risk_scorer.calculate_likelihood(patterns, fda_enforcement_count=0)
        assert likelihood_no_fda == 3

        # With FDA enforcement
        likelihood_with_fda = risk_scorer.calculate_likelihood(patterns, fda_enforcement_count=1)
        assert likelihood_with_fda == 4  # +1 bonus

        # Multiple FDA enforcements
        likelihood_multiple = risk_scorer.calculate_likelihood(patterns, fda_enforcement_count=3)
        assert likelihood_multiple == 5  # +2 bonus (capped at 5)

    def test_likelihood_bonus_for_multiple_patterns(self, risk_scorer):
        """Test that multiple patterns increase likelihood"""
        patterns = [
            PatternMatch(pattern="test1", category="cure_claims", severity=3, rationale="test"),
            PatternMatch(pattern="test2", category="guarantees", severity=3, rationale="test"),
            PatternMatch(pattern="test3", category="fda_misrepresentation", severity=3, rationale="test"),
        ]

        likelihood = risk_scorer.calculate_likelihood(patterns, fda_enforcement_count=0)
        assert likelihood == 4  # 3 + 1 bonus for multiple patterns

    def test_likelihood_capped_at_5(self, risk_scorer):
        """Test that likelihood is capped at 5"""
        patterns = [
            PatternMatch(pattern="test", category="cure_claims", severity=5, rationale="test")
        ]

        likelihood = risk_scorer.calculate_likelihood(patterns, fda_enforcement_count=10)
        assert likelihood == 5  # Capped at 5

    def test_likelihood_minimum_1_for_no_patterns(self, risk_scorer):
        """Test that likelihood is minimum 1 for no patterns"""
        likelihood = risk_scorer.calculate_likelihood([], fda_enforcement_count=0)
        assert likelihood == 1


class TestSeverityCalculation:
    """Test severity score calculation"""

    def test_severity_from_disease_mentions(self, risk_scorer):
        """Test that disease mentions increase severity"""
        patterns = []
        fda_records = []

        # High severity diseases
        severity_cancer = risk_scorer.calculate_severity("cure cancer", patterns, fda_records)
        assert severity_cancer == 5

        severity_covid = risk_scorer.calculate_severity("covid treatment", patterns, fda_records)
        assert severity_covid == 5

        # Medium severity diseases
        severity_diabetes = risk_scorer.calculate_severity("diabetes cure", patterns, fda_records)
        assert severity_diabetes == 4

        # Low severity conditions
        severity_acne = risk_scorer.calculate_severity("acne treatment", patterns, fda_records)
        assert severity_acne >= 2

    def test_severity_from_claim_types(self, risk_scorer):
        """Test that claim types increase severity"""
        cure_pattern = PatternMatch(
            pattern="cure", category="cure_claims", severity=5, rationale="test"
        )

        severity = risk_scorer.calculate_severity("test keyword", [cure_pattern], [])
        assert severity == 5  # Cure claims are always severe

    def test_severity_from_fda_classification(self, risk_scorer, sample_fda_records):
        """Test that FDA classification increases severity"""
        # Class II record
        severity_class2 = risk_scorer.calculate_severity("test", [], sample_fda_records)
        assert severity_class2 >= 2

        # Class I record (most serious)
        class1_record = FDAEnforcementRecord(
            recall_number="F-5678-2026",
            product_description="Test",
            reason_for_recall="Test",
            classification="Class I",
            recall_initiation_date="2026-03-15"
        )

        severity_class1 = risk_scorer.calculate_severity("test", [], [class1_record])
        assert severity_class1 >= 3

    def test_severity_capped_at_5(self, risk_scorer):
        """Test that severity is capped at 5"""
        patterns = [
            PatternMatch(pattern="cure", category="cure_claims", severity=5, rationale="test")
        ]
        fda_records = [
            FDAEnforcementRecord(
                recall_number="F-1",
                product_description="Test",
                reason_for_recall="Test",
                classification="Class I",
                recall_initiation_date="2026-03-15"
            )
        ]

        severity = risk_scorer.calculate_severity("cure cancer", patterns, fda_records)
        assert severity == 5  # Capped at 5


class TestRiskScoreCalculation:
    """Test risk score calculation"""

    def test_risk_score_is_likelihood_times_severity(self, risk_scorer):
        """Test that risk score = likelihood × severity"""
        risk_score = risk_scorer.calculate_risk_score(likelihood=5, severity=5)
        assert risk_score == 25

        risk_score = risk_scorer.calculate_risk_score(likelihood=3, severity=4)
        assert risk_score == 12

        risk_score = risk_scorer.calculate_risk_score(likelihood=1, severity=1)
        assert risk_score == 1


class TestRiskLevelDetermination:
    """Test risk level classification"""

    def test_critical_risk_level(self, risk_scorer):
        """Test CRITICAL risk level (20-25)"""
        assert risk_scorer.determine_risk_level(25) == RiskLevel.CRITICAL
        assert risk_scorer.determine_risk_level(20) == RiskLevel.CRITICAL

    def test_high_risk_level(self, risk_scorer):
        """Test HIGH risk level (15-19)"""
        assert risk_scorer.determine_risk_level(19) == RiskLevel.HIGH
        assert risk_scorer.determine_risk_level(15) == RiskLevel.HIGH

    def test_medium_risk_level(self, risk_scorer):
        """Test MEDIUM risk level (8-14)"""
        assert risk_scorer.determine_risk_level(14) == RiskLevel.MEDIUM
        assert risk_scorer.determine_risk_level(8) == RiskLevel.MEDIUM

    def test_low_risk_level(self, risk_scorer):
        """Test LOW risk level (1-7)"""
        assert risk_scorer.determine_risk_level(7) == RiskLevel.LOW
        assert risk_scorer.determine_risk_level(1) == RiskLevel.LOW


class TestActionDetermination:
    """Test action determination from risk level"""

    def test_critical_risk_blocks_keyword(self, risk_scorer):
        """Test that CRITICAL risk blocks keyword"""
        action = risk_scorer.determine_action(RiskLevel.CRITICAL)
        assert action == ComplianceAction.BLOCKED

    def test_high_risk_reduces_priority(self, risk_scorer):
        """Test that HIGH risk reduces priority"""
        action = risk_scorer.determine_action(RiskLevel.HIGH)
        assert action == ComplianceAction.REDUCED

    def test_medium_risk_passes(self, risk_scorer):
        """Test that MEDIUM risk passes"""
        action = risk_scorer.determine_action(RiskLevel.MEDIUM)
        assert action == ComplianceAction.PASSED

    def test_low_risk_passes(self, risk_scorer):
        """Test that LOW risk passes"""
        action = risk_scorer.determine_action(RiskLevel.LOW)
        assert action == ComplianceAction.PASSED


class TestRationaleGeneration:
    """Test rationale generation"""

    def test_rationale_includes_risk_level(self, risk_scorer, sample_pattern_matches):
        """Test that rationale includes risk level"""
        rationale = risk_scorer.generate_rationale(
            keyword="cure diabetes",
            risk_level=RiskLevel.CRITICAL,
            risk_score=25,
            likelihood=5,
            severity=5,
            pattern_matches=sample_pattern_matches,
            fda_enforcement_count=1,
        )

        assert "CRITICAL" in rationale

    def test_rationale_includes_pattern_categories(self, risk_scorer, sample_pattern_matches):
        """Test that rationale includes pattern categories"""
        rationale = risk_scorer.generate_rationale(
            keyword="cure diabetes",
            risk_level=RiskLevel.CRITICAL,
            risk_score=25,
            likelihood=5,
            severity=5,
            pattern_matches=sample_pattern_matches,
            fda_enforcement_count=0,
        )

        assert "cure_claims" in rationale or "guarantees" in rationale

    def test_rationale_includes_fda_enforcement(self, risk_scorer, sample_pattern_matches):
        """Test that rationale mentions FDA enforcement"""
        rationale = risk_scorer.generate_rationale(
            keyword="cure diabetes",
            risk_level=RiskLevel.CRITICAL,
            risk_score=25,
            likelihood=5,
            severity=5,
            pattern_matches=sample_pattern_matches,
            fda_enforcement_count=2,
        )

        assert "FDA enforcement" in rationale
        assert "2" in rationale

    def test_rationale_includes_scoring(self, risk_scorer, sample_pattern_matches):
        """Test that rationale includes scoring details"""
        rationale = risk_scorer.generate_rationale(
            keyword="cure diabetes",
            risk_level=RiskLevel.CRITICAL,
            risk_score=25,
            likelihood=5,
            severity=5,
            pattern_matches=sample_pattern_matches,
            fda_enforcement_count=1,
        )

        assert "Likelihood=5" in rationale
        assert "Severity=5" in rationale
        assert "Risk=25" in rationale

    def test_rationale_includes_action(self, risk_scorer, sample_pattern_matches):
        """Test that rationale includes action"""
        # CRITICAL - BLOCK
        rationale_critical = risk_scorer.generate_rationale(
            keyword="cure diabetes",
            risk_level=RiskLevel.CRITICAL,
            risk_score=25,
            likelihood=5,
            severity=5,
            pattern_matches=sample_pattern_matches,
            fda_enforcement_count=1,
        )
        assert "BLOCK" in rationale_critical

        # HIGH - REDUCE
        rationale_high = risk_scorer.generate_rationale(
            keyword="test",
            risk_level=RiskLevel.HIGH,
            risk_score=16,
            likelihood=4,
            severity=4,
            pattern_matches=sample_pattern_matches,
            fda_enforcement_count=0,
        )
        assert "REDUCE" in rationale_high

        # MEDIUM - PASS
        rationale_medium = risk_scorer.generate_rationale(
            keyword="test",
            risk_level=RiskLevel.MEDIUM,
            risk_score=9,
            likelihood=3,
            severity=3,
            pattern_matches=sample_pattern_matches,
            fda_enforcement_count=0,
        )
        assert "PASS" in rationale_medium


class TestCompleteScoring:
    """Test complete scoring workflow"""

    def test_score_keyword_returns_complete_result(self, risk_scorer, sample_pattern_matches, sample_fda_records):
        """Test that score_keyword returns all required fields"""
        result = risk_scorer.score_keyword(
            keyword="cure diabetes",
            pattern_matches=sample_pattern_matches,
            fda_enforcement_count=1,
            fda_enforcement_records=sample_fda_records,
        )

        assert "likelihood_score" in result
        assert "severity_score" in result
        assert "risk_score" in result
        assert "risk_level" in result
        assert "action" in result
        assert "rationale" in result

        assert isinstance(result["risk_level"], RiskLevel)
        assert isinstance(result["action"], ComplianceAction)

    def test_critical_risk_example(self, risk_scorer):
        """Test CRITICAL risk example: cure claims for serious disease"""
        patterns = [
            PatternMatch(
                pattern="cure.*cancer",
                category="cure_claims",
                severity=5,
                rationale="Cure claims for cancer are prohibited"
            )
        ]
        fda_records = [
            FDAEnforcementRecord(
                recall_number="F-1234-2026",
                product_description="Cancer cure supplement",
                reason_for_recall="Unapproved drug claims",
                classification="Class I",
                recall_initiation_date="2026-03-15"
            )
        ]

        result = risk_scorer.score_keyword(
            keyword="cure cancer naturally",
            pattern_matches=patterns,
            fda_enforcement_count=1,
            fda_enforcement_records=fda_records,
        )

        assert result["risk_level"] == RiskLevel.CRITICAL
        assert result["action"] == ComplianceAction.BLOCKED
        assert result["risk_score"] >= 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
