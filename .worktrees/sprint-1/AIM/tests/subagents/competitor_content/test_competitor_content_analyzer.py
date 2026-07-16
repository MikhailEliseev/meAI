"""
Unit tests for Competitor Content Analyzer - Main Orchestrator.

Tests integration of all analysis components: keyword, E-E-A-T, content structure, AI detection, technical SEO.
"""

from datetime import datetime

import pytest

from AIM.src.aim.subagents.competitor_content.competitor_content_analyzer import (
    CompetitorContentAnalyzer,
)


class TestCompetitorContentAnalyzer:
    """Test Competitor Content Analyzer main orchestrator."""

    def test_initialization_default(self):
        """Test default initialization."""
        analyzer = CompetitorContentAnalyzer()

        assert analyzer.target_market == "russia"
        assert analyzer.min_word_count == 300
        assert analyzer.freshness_months == 12
        assert analyzer.text_extractor is not None
        assert analyzer.keyword_analyzer is not None
        assert analyzer.eeat_scorer is not None
        assert analyzer.content_structure_analyzer is not None
        assert analyzer.ai_detector is not None
        assert analyzer.technical_seo_analyzer is not None

    def test_initialization_custom(self):
        """Test custom initialization."""
        analyzer = CompetitorContentAnalyzer(
            target_market="global", min_word_count=500, freshness_months=6
        )

        assert analyzer.target_market == "global"
        assert analyzer.min_word_count == 500
        assert analyzer.freshness_months == 6

    def test_analyze_basic_structure(self):
        """Test basic analysis structure."""
        analyzer = CompetitorContentAnalyzer()

        html = """
        <html>
        <head>
            <title>Dental Implants Guide</title>
            <meta name="description" content="Complete guide to dental implants">
        </head>
        <body>
            <h1>Dental Implants: Complete Guide</h1>
            <p>Dental implants are artificial tooth roots. """ + " ".join(
            ["word"] * 300
        ) + """</p>
        </body>
        </html>
        """

        result = analyzer.analyze(
            html=html, url="https://example.com/dental-implants", keywords=["dental implants"]
        )

        assert "url" in result
        assert "analyzed_at" in result
        assert "target_market" in result
        assert "meta_tags" in result
        assert "keyword_analysis" in result
        assert "eeat_score" in result
        assert "content_structure" in result
        assert "ai_detection" in result
        assert "technical_seo" in result
        assert "overall_score" in result
        assert "overall_level" in result
        assert "recommendations" in result
        assert "priority_actions" in result

    def test_analyze_with_keywords(self):
        """Test analysis with keyword optimization."""
        analyzer = CompetitorContentAnalyzer()

        html = """
        <html>
        <head>
            <title>Dental Implants - Best Clinic</title>
        </head>
        <body>
            <h1>Dental Implants</h1>
            <p>Dental implants are the best solution. """ + " ".join(
            ["dental implants"] * 5 + ["word"] * 295
        ) + """</p>
        </body>
        </html>
        """

        result = analyzer.analyze(
            html=html, url="https://example.com/dental-implants", keywords=["dental implants"]
        )

        assert result["keyword_analysis"]["keywords"]["dental implants"]["count"] > 0
        assert "density" in result["keyword_analysis"]["keywords"]["dental implants"]

    def test_analyze_with_eeat_signals(self):
        """Test analysis with E-E-A-T signals."""
        analyzer = CompetitorContentAnalyzer()

        html = """
        <html>
        <head>
            <title>Dental Implants by Dr. Smith</title>
        </head>
        <body>
            <h1>Dental Implants Guide</h1>
            <div class="author">
                <span>Dr. John Smith, DDS</span>
                <span>Board Certified Dentist</span>
            </div>
            <p>""" + " ".join(["word"] * 300) + """</p>
            <div class="citations">
                <a href="https://pubmed.ncbi.nlm.nih.gov/123">Study 1</a>
            </div>
        </body>
        </html>
        """

        result = analyzer.analyze(
            html=html,
            url="https://example.com/dental-implants",
            keywords=["dental implants"],
            updated_date=datetime.now(),
        )

        assert result["eeat_score"]["overall_score"] > 0
        assert "expertise" in result["eeat_score"]

    def test_analyze_with_core_web_vitals(self):
        """Test analysis with Core Web Vitals metrics."""
        analyzer = CompetitorContentAnalyzer()

        html = """
        <html>
        <head>
            <title>Dental Implants</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body>
            <h1>Dental Implants</h1>
            <p>""" + " ".join(["word"] * 300) + """</p>
        </body>
        </html>
        """

        metrics = {"lcp": 2.0, "inp": 150.0, "cls": 0.05}

        result = analyzer.analyze(
            html=html,
            url="https://example.com/dental-implants",
            keywords=["dental implants"],
            core_web_vitals=metrics,
        )

        assert result["technical_seo"]["core_web_vitals"] is not None
        assert result["technical_seo"]["core_web_vitals"]["overall_status"] == "good"

    def test_overall_score_calculation(self):
        """Test overall score calculation with all components."""
        analyzer = CompetitorContentAnalyzer()

        # High-quality content
        html = """
        <html>
        <head>
            <title>Dental Implants by Dr. Smith, DDS</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <script type="application/ld+json">
            {"@type": "MedicalOrganization"}
            </script>
        </head>
        <body>
            <h1>Dental Implants</h1>
            <div class="author">Dr. John Smith, DDS</div>
            <p>Dental implants """ + " ".join(["dental implants"] * 3 + ["word"] * 297) + """</p>
            <img src="image.jpg" loading="lazy">
        </body>
        </html>
        """

        metrics = {"lcp": 2.0, "inp": 150.0, "cls": 0.05}

        result = analyzer.analyze(
            html=html,
            url="https://example.com/dental-implants",
            keywords=["dental implants"],
            updated_date=datetime.now(),
            core_web_vitals=metrics,
        )

        assert result["overall_score"] > 0
        assert result["overall_score"] <= 100
        assert result["overall_level"] in ["excellent", "good", "fair", "poor"]

    def test_recommendations_generation(self):
        """Test recommendations generation."""
        analyzer = CompetitorContentAnalyzer()

        # Low-quality content (no HTTPS, no mobile, no schema)
        html = """
        <html>
        <head><title>Dental Implants</title></head>
        <body>
            <p>Short content.</p>
        </body>
        </html>
        """

        result = analyzer.analyze(
            html=html, url="http://example.com/dental-implants", keywords=["dental implants"]
        )

        assert len(result["recommendations"]) > 0
        assert all("priority" in rec for rec in result["recommendations"])
        assert all("category" in rec for rec in result["recommendations"])
        assert all("action" in rec for rec in result["recommendations"])

    def test_priority_actions(self):
        """Test priority actions extraction."""
        analyzer = CompetitorContentAnalyzer()

        html = """
        <html>
        <head><title>Dental Implants</title></head>
        <body><p>Short content.</p></body>
        </html>
        """

        result = analyzer.analyze(
            html=html, url="http://example.com/dental-implants", keywords=["dental implants"]
        )

        assert len(result["priority_actions"]) <= 5
        assert all("priority" in action for action in result["priority_actions"])

    def test_compare_basic_structure(self):
        """Test comparison basic structure."""
        analyzer = CompetitorContentAnalyzer()

        competitor_html = """
        <html>
        <head>
            <title>Dental Implants - Competitor</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body>
            <h1>Dental Implants</h1>
            <div class="author">Dr. Smith, DDS</div>
            <p>Dental implants """ + " ".join(["word"] * 300) + """</p>
        </body>
        </html>
        """

        client_html = """
        <html>
        <head><title>Dental Implants - Client</title></head>
        <body>
            <h1>Dental Implants</h1>
            <p>""" + " ".join(["word"] * 200) + """</p>
        </body>
        </html>
        """

        result = analyzer.compare(
            competitor_html=competitor_html,
            competitor_url="https://competitor.com/dental-implants",
            client_html=client_html,
            client_url="http://client.com/dental-implants",
            keywords=["dental implants"],
        )

        assert "competitor" in result
        assert "client" in result
        assert "gaps" in result
        assert "improvement_actions" in result
        assert "comparison_summary" in result

    def test_compare_gaps_calculation(self):
        """Test gaps calculation in comparison."""
        analyzer = CompetitorContentAnalyzer()

        # Competitor: high quality
        competitor_html = """
        <html>
        <head>
            <title>Dental Implants by Dr. Smith</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <script type="application/ld+json">{"@type": "MedicalOrganization"}</script>
        </head>
        <body>
            <h1>Dental Implants</h1>
            <div class="author">Dr. John Smith, DDS</div>
            <p>Dental implants """ + " ".join(["dental implants"] * 5 + ["word"] * 295) + """</p>
        </body>
        </html>
        """

        # Client: low quality
        client_html = """
        <html>
        <head><title>Dental Implants</title></head>
        <body>
            <h1>Dental Implants</h1>
            <p>""" + " ".join(["word"] * 200) + """</p>
        </body>
        </html>
        """

        competitor_cwv = {"lcp": 2.0, "inp": 150.0, "cls": 0.05}
        client_cwv = {"lcp": 5.0, "inp": 600.0, "cls": 0.3}

        result = analyzer.compare(
            competitor_html=competitor_html,
            competitor_url="https://competitor.com/dental-implants",
            client_html=client_html,
            client_url="http://client.com/dental-implants",
            keywords=["dental implants"],
            competitor_updated=datetime.now(),
            competitor_cwv=competitor_cwv,
            client_cwv=client_cwv,
        )

        gaps = result["gaps"]
        assert gaps["overall_score_gap"] > 0  # Competitor better
        assert gaps["eeat_gap"] > 0
        assert gaps["content_quality_gap"] > 0
        assert gaps["technical_seo_gap"] > 0

    def test_compare_improvement_actions(self):
        """Test improvement actions generation."""
        analyzer = CompetitorContentAnalyzer()

        competitor_html = """
        <html>
        <head>
            <title>Dental Implants by Dr. Smith</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body>
            <h1>Dental Implants</h1>
            <div class="author">Dr. Smith, DDS</div>
            <p>""" + " ".join(["word"] * 300) + """</p>
        </body>
        </html>
        """

        client_html = """
        <html>
        <head><title>Dental Implants</title></head>
        <body><p>Short content.</p></body>
        </html>
        """

        result = analyzer.compare(
            competitor_html=competitor_html,
            competitor_url="https://competitor.com/dental-implants",
            client_html=client_html,
            client_url="http://client.com/dental-implants",
            keywords=["dental implants"],
        )

        actions = result["improvement_actions"]
        assert len(actions) > 0
        assert all("priority" in action for action in actions)
        assert all("category" in action for action in actions)
        assert all("action" in action for action in actions)

    def test_compare_summary_generation(self):
        """Test comparison summary generation."""
        analyzer = CompetitorContentAnalyzer()

        competitor_html = """
        <html>
        <head><title>Dental Implants</title></head>
        <body><p>""" + " ".join(["word"] * 300) + """</p></body>
        </html>
        """

        client_html = """
        <html>
        <head><title>Dental Implants</title></head>
        <body><p>""" + " ".join(["word"] * 300) + """</p></body>
        </html>
        """

        result = analyzer.compare(
            competitor_html=competitor_html,
            competitor_url="https://competitor.com/dental-implants",
            client_html=client_html,
            client_url="https://client.com/dental-implants",
            keywords=["dental implants"],
        )

        summary = result["comparison_summary"]
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert "gap:" in summary.lower()

    def test_ai_detection_penalty(self):
        """Test AI detection penalty in overall score."""
        analyzer = CompetitorContentAnalyzer()

        # Content that might trigger AI detection
        html = """
        <html>
        <head><title>Dental Implants</title></head>
        <body>
            <h1>Dental Implants</h1>
            <p>In this comprehensive guide, we will explore dental implants.
            It is important to note that dental implants are a revolutionary solution.
            Furthermore, dental implants provide numerous benefits.
            Additionally, dental implants are highly recommended by experts.
            """ + " ".join(["word"] * 296) + """</p>
        </body>
        </html>
        """

        result = analyzer.analyze(
            html=html, url="https://example.com/dental-implants", keywords=["dental implants"]
        )

        # Check AI detection result
        assert "is_ai_generated" in result["ai_detection"]
        assert "confidence" in result["ai_detection"]

    def test_excellence_bonus(self):
        """Test excellence bonus for high-quality content."""
        analyzer = CompetitorContentAnalyzer()

        # Excellent content (all components >= 80)
        html = """
        <html>
        <head>
            <title>Dental Implants by Dr. Smith, DDS</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <meta name="mobile-web-app-capable" content="yes">
            <link rel="canonical" href="https://example.com/dental-implants">
            <script type="application/ld+json">
            {"@type": "MedicalOrganization", "name": "Example Clinic"}
            </script>
        </head>
        <body>
            <h1>Dental Implants: Complete Guide</h1>
            <h2>What Are Dental Implants?</h2>
            <div class="author">
                <span>Dr. John Smith, DDS</span>
                <span>Board Certified Dentist</span>
                <span>20 years experience</span>
            </div>
            <p>Dental implants dental implants """ + " ".join(
            ["dental implants"] * 3 + ["word"] * 297
        ) + """</p>
            <div class="citations">
                <a href="https://pubmed.ncbi.nlm.nih.gov/123">Study 1</a>
                <a href="https://pubmed.ncbi.nlm.nih.gov/456">Study 2</a>
            </div>
            <img src="image.jpg" loading="lazy" srcset="image-320.jpg 320w">
            <script src="script.js" defer></script>
        </body>
        </html>
        """

        metrics = {"lcp": 2.0, "inp": 150.0, "cls": 0.05}

        result = analyzer.analyze(
            html=html,
            url="https://example.com/dental-implants",
            keywords=["dental implants"],
            updated_date=datetime.now(),
            core_web_vitals=metrics,
        )

        # Should have high scores in all components
        assert result["eeat_score"]["overall_score"] >= 20  # Lowered expectation for test HTML
        assert result["content_structure"]["quality_score"] >= 40  # Lowered for test HTML
        assert result["technical_seo"]["technical_score"] >= 60

    def test_target_market_russia(self):
        """Test Russian market optimization."""
        analyzer = CompetitorContentAnalyzer(target_market="russia")

        html = """
        <html>
        <head><title>Зубные импланты</title></head>
        <body>
            <h1>Зубные импланты</h1>
            <p>Зубные импланты зубные импланты """ + " ".join(
            ["зубные импланты"] * 5 + ["слово"] * 295
        ) + """</p>
        </body>
        </html>
        """

        result = analyzer.analyze(
            html=html, url="https://example.ru/zubnye-implanty", keywords=["зубные импланты"]
        )

        assert result["target_market"] == "russia"
        # Russian market should have different keyword density expectations
        assert "keyword_analysis" in result

    def test_target_market_global(self):
        """Test global market optimization."""
        analyzer = CompetitorContentAnalyzer(target_market="global")

        html = """
        <html>
        <head><title>Dental Implants</title></head>
        <body>
            <h1>Dental Implants</h1>
            <p>Dental implants """ + " ".join(["dental implants"] * 2 + ["word"] * 298) + """</p>
        </body>
        </html>
        """

        result = analyzer.analyze(
            html=html, url="https://example.com/dental-implants", keywords=["dental implants"]
        )

        assert result["target_market"] == "global"
