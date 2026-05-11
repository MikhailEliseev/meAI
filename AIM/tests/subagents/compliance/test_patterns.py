"""
Tests for Prohibited Pattern Library

Tests pattern matching accuracy, performance, and coverage.
"""

import pytest
import time
from pathlib import Path

from aim.subagents.compliance.patterns import ProhibitedPatternLibrary


@pytest.fixture
def pattern_library():
    """Create pattern library instance"""
    return ProhibitedPatternLibrary()


class TestPatternLibrary:
    """Test pattern library initialization and basic operations"""

    def test_library_loads_patterns(self, pattern_library):
        """Test that patterns are loaded from YAML"""
        assert pattern_library.get_pattern_count() > 0
        assert len(pattern_library.get_categories()) > 0

    def test_library_has_expected_categories(self, pattern_library):
        """Test that expected categories are present"""
        categories = pattern_library.get_categories()

        expected = [
            "cure_claims",
            "treatment_claims",
            "diagnostic_claims",
            "prevention_claims",
            "guarantees",
            "fda_misrepresentation",
        ]

        for category in expected:
            assert category in categories

    def test_library_has_100_plus_patterns(self, pattern_library):
        """Test that library has 100+ patterns"""
        count = pattern_library.get_pattern_count()
        assert count >= 100, f"Expected 100+ patterns, got {count}"


class TestPatternMatching:
    """Test pattern matching accuracy"""

    def test_cure_claims_detected(self, pattern_library):
        """Test that cure claims are detected"""
        keywords = [
            "cure diabetes naturally",
            "cures cancer",
            "eliminate arthritis",
            "eradicate disease",
        ]

        for keyword in keywords:
            matches = pattern_library.check_keyword(keyword)
            assert len(matches) > 0, f"No matches for: {keyword}"
            assert any(m.category == "cure_claims" for m in matches)

    def test_treatment_claims_detected(self, pattern_library):
        """Test that treatment claims are detected"""
        keywords = [
            "treat cancer naturally",
            "therapy for diabetes",
            "medication for depression",
        ]

        for keyword in keywords:
            matches = pattern_library.check_keyword(keyword)
            assert len(matches) > 0, f"No matches for: {keyword}"
            assert any(m.category == "treatment_claims" for m in matches)

    def test_fda_misrepresentation_detected(self, pattern_library):
        """Test that FDA misrepresentation is detected"""
        keywords = [
            "FDA approved supplement",
            "FDA certified vitamin",
            "FDA endorsed herb",
        ]

        for keyword in keywords:
            matches = pattern_library.check_keyword(keyword)
            assert len(matches) > 0, f"No matches for: {keyword}"
            assert any(m.category == "fda_misrepresentation" for m in matches)

    def test_guarantees_detected(self, pattern_library):
        """Test that guarantees are detected"""
        keywords = [
            "guaranteed weight loss",
            "100% effective cure",
            "permanent relief",
            "no side effects",
        ]

        for keyword in keywords:
            matches = pattern_library.check_keyword(keyword)
            assert len(matches) > 0, f"No matches for: {keyword}"
            assert any(m.category == "guarantees" for m in matches)

    def test_high_risk_diseases_detected(self, pattern_library):
        """Test that high-risk disease claims are detected"""
        keywords = [
            "covid cure",
            "coronavirus treatment",
            "cancer cure",
            "HIV prevention",
        ]

        for keyword in keywords:
            matches = pattern_library.check_keyword(keyword)
            assert len(matches) > 0, f"No matches for: {keyword}"
            # Should match either high_risk_diseases or cure/treatment claims
            assert len(matches) >= 1

    def test_safe_keywords_pass(self, pattern_library):
        """Test that safe keywords don't trigger false positives"""
        safe_keywords = [
            "dental implants near me",
            "cosmetic dentistry",
            "teeth whitening cost",
            "orthodontist consultation",
        ]

        for keyword in safe_keywords:
            matches = pattern_library.check_keyword(keyword)
            # Safe keywords should have no matches or only low-severity matches
            if matches:
                max_severity = max(m.severity for m in matches)
                assert max_severity <= 2, f"False positive for safe keyword: {keyword}"


class TestPatternPerformance:
    """Test pattern matching performance"""

    def test_pattern_matching_under_10ms(self, pattern_library):
        """Test that pattern matching is <10ms per keyword"""
        keywords = [
            "cure diabetes",
            "treat cancer",
            "FDA approved supplement",
            "guaranteed weight loss",
            "dental implants near me",
        ]

        for keyword in keywords:
            start = time.perf_counter()
            matches = pattern_library.check_keyword(keyword)
            duration_ms = (time.perf_counter() - start) * 1000

            assert duration_ms < 10, f"Pattern matching took {duration_ms:.2f}ms (>10ms) for: {keyword}"

    def test_batch_performance(self, pattern_library):
        """Test batch processing performance"""
        keywords = [
            "cure diabetes",
            "treat cancer",
            "FDA approved",
            "guaranteed results",
            "dental implants",
        ] * 20  # 100 keywords

        start = time.perf_counter()
        for keyword in keywords:
            pattern_library.check_keyword(keyword)
        duration = time.perf_counter() - start

        avg_ms = (duration / len(keywords)) * 1000
        assert avg_ms < 10, f"Average pattern matching: {avg_ms:.2f}ms (>10ms)"


class TestSeverityScoring:
    """Test severity scoring"""

    def test_max_severity_calculation(self, pattern_library):
        """Test max severity calculation"""
        keyword = "cure cancer with FDA approved supplement"
        matches = pattern_library.check_keyword(keyword)

        assert len(matches) > 0
        max_severity = pattern_library.get_max_severity(matches)
        assert max_severity == 5  # Should be maximum severity

    def test_severity_levels(self, pattern_library):
        """Test that severity levels are correct"""
        # CRITICAL severity (5)
        critical_keywords = [
            "cure cancer",
            "FDA approved supplement",
            "treat COVID-19",
        ]

        for keyword in critical_keywords:
            matches = pattern_library.check_keyword(keyword)
            if matches:
                max_severity = pattern_library.get_max_severity(matches)
                assert max_severity >= 4, f"Expected high severity for: {keyword}"

    def test_empty_matches_return_none(self, pattern_library):
        """Test that empty matches return None for max severity"""
        keyword = "dental implants"
        matches = pattern_library.check_keyword(keyword)

        if not matches:
            max_severity = pattern_library.get_max_severity(matches)
            assert max_severity is None


class TestPatternCategories:
    """Test pattern category operations"""

    def test_get_patterns_by_category(self, pattern_library):
        """Test getting patterns by category"""
        cure_patterns = pattern_library.get_patterns_by_category("cure_claims")
        assert len(cure_patterns) > 0

        for pattern in cure_patterns:
            assert "pattern" in pattern
            assert "severity" in pattern
            assert "rationale" in pattern

    def test_get_high_severity_patterns(self, pattern_library):
        """Test getting high severity patterns"""
        high_severity = pattern_library.get_high_severity_patterns(min_severity=4)
        assert len(high_severity) > 0

        for pattern in high_severity:
            assert pattern["severity"] >= 4

    def test_pattern_has_required_fields(self, pattern_library):
        """Test that all patterns have required fields"""
        for category in pattern_library.get_categories():
            patterns = pattern_library.get_patterns_by_category(category)

            for pattern in patterns:
                assert "pattern" in pattern
                assert "severity" in pattern
                assert "rationale" in pattern
                assert 1 <= pattern["severity"] <= 5


class TestCaseInsensitivity:
    """Test case-insensitive matching"""

    def test_case_insensitive_matching(self, pattern_library):
        """Test that matching is case-insensitive"""
        keywords = [
            "CURE DIABETES",
            "Cure Diabetes",
            "cure diabetes",
            "CuRe DiAbEtEs",
        ]

        results = [pattern_library.check_keyword(kw) for kw in keywords]

        # All should have same number of matches
        match_counts = [len(matches) for matches in results]
        assert len(set(match_counts)) == 1, "Case sensitivity detected"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
