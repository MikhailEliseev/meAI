"""
Unit tests for KeywordAnalyzer.

Tests market-specific thresholds, LSI extraction, and placement analysis.
"""

import pytest

from AIM.src.aim.subagents.competitor_content.keyword_analyzer import KeywordAnalyzer


class TestKeywordAnalyzer:
    """Test KeywordAnalyzer functionality."""

    def test_yandex_market_thresholds(self):
        """Test Yandex market uses 2-3% keyword density."""
        analyzer = KeywordAnalyzer(market="yandex")

        assert analyzer.min_density == 0.02
        assert analyzer.max_density == 0.03
        assert analyzer.market == "yandex"

    def test_google_market_thresholds(self):
        """Test Google market uses 0.5-1.5% keyword density."""
        analyzer = KeywordAnalyzer(market="google")

        assert analyzer.min_density == 0.005
        assert analyzer.max_density == 0.015
        assert analyzer.market == "google"

    def test_default_market_is_google(self):
        """Test default market is Google."""
        analyzer = KeywordAnalyzer()

        assert analyzer.market == "google"
        assert analyzer.min_density == 0.005

    def test_analyze_keyword_density_optimal(self):
        """Test keyword density analysis with optimal density."""
        analyzer = KeywordAnalyzer(market="google")

        # 1% density (10 occurrences in 1000 words) - optimal for Google
        text = "dental implants " * 10 + "other words " * 990
        result = analyzer.analyze_keyword_density(
            text=text, target_keyword="dental implants", total_words=1000
        )

        assert result["keyword"] == "dental implants"
        assert result["count"] == 10
        assert 0.005 <= result["density"] <= 0.015  # Within Google range
        assert result["status"] == "optimal"
        assert result["market"] == "google"

    def test_analyze_keyword_density_too_low(self):
        """Test keyword density too low detection."""
        analyzer = KeywordAnalyzer(market="google")

        # 0.2% density (2 occurrences in 1000 words) - too low
        text = "dental implants " * 2 + "other words " * 998
        result = analyzer.analyze_keyword_density(
            text=text, target_keyword="dental implants", total_words=1000
        )

        assert result["status"] == "too_low"
        assert result["density"] < 0.005
        assert "Increase keyword usage" in result["recommendation"]

    def test_analyze_keyword_density_too_high(self):
        """Test keyword density too high detection."""
        analyzer = KeywordAnalyzer(market="google")

        # 3% density (30 occurrences in 1000 words) - too high for Google
        text = "dental implants " * 30 + "other words " * 970
        result = analyzer.analyze_keyword_density(
            text=text, target_keyword="dental implants", total_words=1000
        )

        assert result["status"] == "too_high"
        assert result["density"] > 0.015
        assert "Reduce keyword usage" in result["recommendation"]

    def test_analyze_keyword_density_yandex_vs_google(self):
        """Test same density evaluated differently for Yandex vs Google."""
        # 2.5% density (25 occurrences in 1000 words)
        text = "dental implants " * 25 + "other words " * 975

        # Google: too high
        google_analyzer = KeywordAnalyzer(market="google")
        google_result = google_analyzer.analyze_keyword_density(
            text=text, target_keyword="dental implants", total_words=1000
        )
        assert google_result["status"] == "too_high"

        # Yandex: optimal
        yandex_analyzer = KeywordAnalyzer(market="yandex")
        yandex_result = yandex_analyzer.analyze_keyword_density(
            text=text, target_keyword="dental implants", total_words=1000
        )
        assert yandex_result["status"] == "optimal"

    def test_analyze_keyword_density_case_insensitive(self):
        """Test keyword matching is case-insensitive."""
        analyzer = KeywordAnalyzer(market="google")

        text = "Dental Implants DENTAL IMPLANTS dental implants " * 3
        result = analyzer.analyze_keyword_density(
            text=text, target_keyword="dental implants", total_words=100
        )

        assert result["count"] == 9  # All variations counted

    def test_analyze_keyword_density_empty_text(self):
        """Test handling of empty text."""
        analyzer = KeywordAnalyzer(market="google")

        result = analyzer.analyze_keyword_density(
            text="", target_keyword="dental implants", total_words=0
        )

        assert result["count"] == 0
        assert result["density"] == 0.0
        assert result["status"] == "missing"

    def test_extract_lsi_keywords(self):
        """Test LSI keyword extraction."""
        analyzer = KeywordAnalyzer(market="google")

        keywords = {
            "dental": 50,
            "implants": 45,
            "teeth": 30,
            "surgery": 25,
            "procedure": 20,
            "cost": 15,
            "pain": 10,
            "recovery": 8,
            "the": 100,  # Should be filtered (too common)
            "a": 80,  # Should be filtered
        }

        lsi = analyzer.extract_lsi_keywords(
            keywords=keywords, target_keyword="dental implants", min_count=2
        )

        # Check LSI keywords extracted
        assert len(lsi) > 0
        assert all(kw["count"] >= 2 for kw in lsi)
        assert all(kw["type"] == "lsi" for kw in lsi)

        # Check target keyword not in LSI
        lsi_keywords = [kw["keyword"] for kw in lsi]
        assert "dental" not in lsi_keywords
        assert "implants" not in lsi_keywords

        # Check sorted by frequency
        if len(lsi) > 1:
            assert lsi[0]["count"] >= lsi[1]["count"]

    def test_extract_lsi_keywords_min_count_filter(self):
        """Test LSI keywords filtered by minimum count."""
        analyzer = KeywordAnalyzer(market="google")

        keywords = {"teeth": 5, "surgery": 3, "pain": 1}

        lsi = analyzer.extract_lsi_keywords(
            keywords=keywords, target_keyword="dental", min_count=3
        )

        # Only keywords with count >= 3
        assert len(lsi) == 2
        assert all(kw["count"] >= 3 for kw in lsi)

    def test_analyze_keyword_placement_all_present(self):
        """Test keyword placement when keyword is in all locations."""
        analyzer = KeywordAnalyzer(market="google")

        title = "Dental Implants Guide"
        headings = {
            "h1": ["Dental Implants Overview"],
            "h2": ["What are Dental Implants?", "Cost of Dental Implants"],
            "h3": ["Dental Implants Procedure"],
        }
        text = (
            "dental implants " * 50
            + "middle content " * 400
            + "dental implants " * 50
        )

        result = analyzer.analyze_keyword_placement(
            target_keyword="dental implants",
            title=title,
            headings=headings,
            text=text,
        )

        assert result["placements"]["in_title"] is True
        assert result["placements"]["in_h1"] is True
        assert result["placements"]["in_h2"] is True
        assert result["placements"]["in_h3"] is True
        assert result["placements"]["in_first_100_words"] is True
        assert result["placements"]["in_last_100_words"] is True
        assert result["score"] == 100.0
        assert len(result["recommendations"]) == 0

    def test_analyze_keyword_placement_missing_critical(self):
        """Test keyword placement with missing critical placements."""
        analyzer = KeywordAnalyzer(market="google")

        title = "Guide to Teeth Replacement"  # No keyword
        headings = {"h1": ["Overview"], "h2": ["Cost"]}  # No keyword
        text = "middle content " * 500  # No keyword in first/last 100

        result = analyzer.analyze_keyword_placement(
            target_keyword="dental implants",
            title=title,
            headings=headings,
            text=text,
        )

        assert result["placements"]["in_title"] is False
        assert result["placements"]["in_h1"] is False
        assert result["placements"]["in_first_100_words"] is False
        assert result["score"] < 50.0
        assert "Add keyword to title tag" in result["recommendations"]
        assert "Add keyword to H1 heading" in result["recommendations"]
        assert "Add keyword to first 100 words" in result["recommendations"]

    def test_analyze_keyword_placement_case_insensitive(self):
        """Test keyword placement matching is case-insensitive."""
        analyzer = KeywordAnalyzer(market="google")

        title = "DENTAL IMPLANTS Guide"
        headings = {"h1": ["Dental Implants Overview"]}
        text = "Dental Implants " * 100

        result = analyzer.analyze_keyword_placement(
            target_keyword="dental implants",
            title=title,
            headings=headings,
            text=text,
        )

        assert result["placements"]["in_title"] is True
        assert result["placements"]["in_h1"] is True

    def test_analyze_market_optimization_optimal(self):
        """Test market optimization analysis with optimal scores."""
        analyzer = KeywordAnalyzer(market="google")

        density_analysis = {
            "keyword": "dental implants",
            "count": 10,
            "density": 0.01,
            "status": "optimal",
            "recommendation": "Optimal",
            "market": "google",
            "target_range": "0.50%-1.50%",
        }

        placement_analysis = {
            "placements": {
                "in_title": True,
                "in_h1": True,
                "in_first_100_words": True,
            },
            "score": 100.0,
            "recommendations": [],
        }

        lsi_keywords = [{"keyword": f"lsi{i}", "count": 5} for i in range(7)]

        result = analyzer.analyze_market_optimization(
            density_analysis=density_analysis,
            placement_analysis=placement_analysis,
            lsi_keywords=lsi_keywords,
            total_words=1000,
        )

        assert result["market"] == "google"
        assert result["overall_score"] >= 90.0
        assert result["density_score"] == 100
        assert result["placement_score"] == 100.0
        assert result["lsi_count"] == 7
        assert 5.0 <= result["lsi_per_1000_words"] <= 10.0
        assert result["lsi_status"] == "optimal"

    def test_analyze_market_optimization_yandex_recommendations(self):
        """Test Yandex-specific recommendations."""
        analyzer = KeywordAnalyzer(market="yandex")

        density_analysis = {
            "keyword": "dental implants",
            "count": 5,
            "density": 0.005,
            "status": "too_low",
            "recommendation": "Increase",
            "market": "yandex",
            "target_range": "2.00%-3.00%",
        }

        placement_analysis = {"placements": {}, "score": 50.0, "recommendations": []}

        lsi_keywords = []

        result = analyzer.analyze_market_optimization(
            density_analysis=density_analysis,
            placement_analysis=placement_analysis,
            lsi_keywords=lsi_keywords,
            total_words=1000,
        )

        assert result["market"] == "yandex"
        assert any(
            "Yandex optimization" in rec for rec in result["recommendations"]
        )
        assert any(
            "Yandex tolerates higher keyword density" in rec
            for rec in result["recommendations"]
        )

    def test_analyze_market_optimization_google_recommendations(self):
        """Test Google-specific recommendations."""
        analyzer = KeywordAnalyzer(market="google")

        density_analysis = {
            "keyword": "dental implants",
            "count": 30,
            "density": 0.03,
            "status": "too_high",
            "recommendation": "Reduce",
            "market": "google",
            "target_range": "0.50%-1.50%",
        }

        placement_analysis = {"placements": {}, "score": 50.0, "recommendations": []}

        lsi_keywords = []

        result = analyzer.analyze_market_optimization(
            density_analysis=density_analysis,
            placement_analysis=placement_analysis,
            lsi_keywords=lsi_keywords,
            total_words=1000,
        )

        assert result["market"] == "google"
        assert any(
            "Google optimization" in rec for rec in result["recommendations"]
        )
        assert any(
            "Google prefers lower keyword density" in rec
            for rec in result["recommendations"]
        )

    def test_analyze_market_optimization_lsi_too_low(self):
        """Test LSI keyword count too low detection."""
        analyzer = KeywordAnalyzer(market="google")

        density_analysis = {
            "keyword": "dental implants",
            "count": 10,
            "density": 0.01,
            "status": "optimal",
            "recommendation": "Optimal",
            "market": "google",
            "target_range": "0.50%-1.50%",
        }

        placement_analysis = {"placements": {}, "score": 100.0, "recommendations": []}

        lsi_keywords = [{"keyword": "teeth", "count": 5}]  # Only 1 LSI keyword

        result = analyzer.analyze_market_optimization(
            density_analysis=density_analysis,
            placement_analysis=placement_analysis,
            lsi_keywords=lsi_keywords,
            total_words=1000,
        )

        assert result["lsi_status"] == "too_low"
        assert result["lsi_per_1000_words"] < 5.0
        assert any("Add more LSI keywords" in rec for rec in result["recommendations"])
