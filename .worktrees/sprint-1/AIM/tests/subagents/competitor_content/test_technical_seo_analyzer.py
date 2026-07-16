"""
Unit tests for Technical SEO Analyzer.

Tests technical SEO analysis: Core Web Vitals, mobile optimization, page speed, schema markup.
"""

import pytest

from AIM.src.aim.subagents.competitor_content.technical_seo_analyzer import (
    TechnicalSEOAnalyzer,
)


class TestTechnicalSEOAnalyzer:
    """Test Technical SEO Analyzer functionality."""

    def test_initialization_default(self):
        """Test default initialization."""
        analyzer = TechnicalSEOAnalyzer()

        assert analyzer.lcp_threshold == 2.5
        assert analyzer.inp_threshold == 200.0
        assert analyzer.cls_threshold == 0.1

    def test_initialization_custom(self):
        """Test custom initialization."""
        analyzer = TechnicalSEOAnalyzer(
            lcp_threshold=3.0, inp_threshold=250.0, cls_threshold=0.15
        )

        assert analyzer.lcp_threshold == 3.0
        assert analyzer.inp_threshold == 250.0
        assert analyzer.cls_threshold == 0.15

    def test_analyze_basic_structure(self):
        """Test basic analysis structure."""
        analyzer = TechnicalSEOAnalyzer()

        html = "<html><head><title>Test</title></head><body><p>Content</p></body></html>"
        url = "https://example.com/page"

        result = analyzer.analyze(html, url)

        assert "mobile_optimization" in result
        assert "page_speed" in result
        assert "schema_markup" in result
        assert "security" in result
        assert "meta_tags" in result
        assert "technical_score" in result
        assert "technical_level" in result

    def test_core_web_vitals_good(self):
        """Test Core Web Vitals analysis with good metrics."""
        analyzer = TechnicalSEOAnalyzer()

        metrics = {"lcp": 2.0, "inp": 150.0, "cls": 0.05}

        html = "<html><body><p>Content</p></body></html>"
        result = analyzer.analyze(html, "https://example.com", metrics=metrics)

        cwv = result["core_web_vitals"]
        assert cwv["lcp"]["status"] == "good"
        assert cwv["inp"]["status"] == "good"
        assert cwv["cls"]["status"] == "good"
        assert cwv["overall_status"] == "good"

    def test_core_web_vitals_needs_improvement(self):
        """Test Core Web Vitals with needs improvement metrics."""
        analyzer = TechnicalSEOAnalyzer()

        metrics = {"lcp": 3.0, "inp": 300.0, "cls": 0.15}

        html = "<html><body><p>Content</p></body></html>"
        result = analyzer.analyze(html, "https://example.com", metrics=metrics)

        cwv = result["core_web_vitals"]
        assert cwv["lcp"]["status"] == "needs_improvement"
        assert cwv["inp"]["status"] == "needs_improvement"
        assert cwv["cls"]["status"] == "needs_improvement"
        assert cwv["overall_status"] == "needs_improvement"

    def test_core_web_vitals_poor(self):
        """Test Core Web Vitals with poor metrics."""
        analyzer = TechnicalSEOAnalyzer()

        metrics = {"lcp": 5.0, "inp": 600.0, "cls": 0.3}

        html = "<html><body><p>Content</p></body></html>"
        result = analyzer.analyze(html, "https://example.com", metrics=metrics)

        cwv = result["core_web_vitals"]
        assert cwv["lcp"]["status"] == "poor"
        assert cwv["inp"]["status"] == "poor"
        assert cwv["cls"]["status"] == "poor"
        assert cwv["overall_status"] == "poor"

    def test_mobile_optimization_full(self):
        """Test mobile optimization with all features."""
        analyzer = TechnicalSEOAnalyzer()

        html = """
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <meta name="mobile-web-app-capable" content="yes">
            <link rel="stylesheet" media="screen and (max-width: 768px)" href="mobile.css">
        </head>
        <body><p>Content</p></body>
        </html>
        """

        result = analyzer.analyze(html, "https://example.com")

        mobile = result["mobile_optimization"]
        assert mobile["has_viewport"] is True
        assert mobile["has_width_device"] is True
        assert mobile["has_initial_scale"] is True
        assert mobile["has_media_queries"] is True
        assert mobile["has_mobile_meta_tags"] is True
        assert mobile["mobile_score"] == 100
        assert mobile["mobile_friendly"] is True

    def test_mobile_optimization_minimal(self):
        """Test mobile optimization with minimal features."""
        analyzer = TechnicalSEOAnalyzer()

        html = "<html><head><title>Test</title></head><body><p>Content</p></body></html>"

        result = analyzer.analyze(html, "https://example.com")

        mobile = result["mobile_optimization"]
        assert mobile["has_viewport"] is False
        assert mobile["mobile_score"] == 0
        assert mobile["mobile_friendly"] is False

    def test_page_speed_images_optimization(self):
        """Test page speed analysis with image optimization."""
        analyzer = TechnicalSEOAnalyzer()

        html = """
        <html>
        <body>
            <img src="image1.jpg" loading="lazy" srcset="image1-320.jpg 320w, image1-640.jpg 640w">
            <img src="image2.jpg" loading="lazy">
            <img src="image3.jpg">
        </body>
        </html>
        """

        result = analyzer.analyze(html, "https://example.com")

        page_speed = result["page_speed"]
        assert page_speed["images"]["total"] == 3
        assert page_speed["images"]["with_lazy_loading"] == 2
        assert page_speed["images"]["with_srcset"] == 1
        assert page_speed["images"]["lazy_loading_percentage"] > 0

    def test_page_speed_scripts_optimization(self):
        """Test page speed analysis with script optimization."""
        analyzer = TechnicalSEOAnalyzer()

        html = """
        <html>
        <head>
            <script src="script1.js" async></script>
            <script src="script2.js" defer></script>
            <script src="script3.js"></script>
        </head>
        <body><p>Content</p></body>
        </html>
        """

        result = analyzer.analyze(html, "https://example.com")

        page_speed = result["page_speed"]
        assert page_speed["scripts"]["total"] == 3
        assert page_speed["scripts"]["with_async"] == 1
        assert page_speed["scripts"]["with_defer"] == 1
        assert page_speed["scripts"]["optimized_percentage"] > 0

    def test_page_speed_resource_hints(self):
        """Test page speed analysis with resource hints."""
        analyzer = TechnicalSEOAnalyzer()

        html = """
        <html>
        <head>
            <link rel="preload" href="font.woff2" as="font">
            <link rel="prefetch" href="next-page.html">
            <link rel="preconnect" href="https://cdn.example.com">
            <link rel="dns-prefetch" href="https://analytics.example.com">
        </head>
        <body><p>Content</p></body>
        </html>
        """

        result = analyzer.analyze(html, "https://example.com")

        page_speed = result["page_speed"]
        assert page_speed["resource_hints"]["preload"] == 1
        assert page_speed["resource_hints"]["prefetch"] == 1
        assert page_speed["resource_hints"]["preconnect"] == 1
        assert page_speed["resource_hints"]["dns_prefetch"] == 1
        assert page_speed["resource_hints"]["total"] == 4

    def test_schema_markup_json_ld(self):
        """Test schema markup detection with JSON-LD."""
        analyzer = TechnicalSEOAnalyzer()

        html = """
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "MedicalOrganization",
                "name": "Example Clinic"
            }
            </script>
        </head>
        <body><p>Content</p></body>
        </html>
        """

        result = analyzer.analyze(html, "https://example.com")

        schema = result["schema_markup"]
        assert schema["has_json_ld"] is True
        assert schema["json_ld_count"] == 1
        assert schema["has_structured_data"] is True

    def test_schema_markup_microdata(self):
        """Test schema markup detection with Microdata."""
        analyzer = TechnicalSEOAnalyzer()

        html = """
        <html>
        <body>
            <div itemscope itemtype="https://schema.org/MedicalOrganization">
                <span itemprop="name">Example Clinic</span>
            </div>
        </body>
        </html>
        """

        result = analyzer.analyze(html, "https://example.com")

        schema = result["schema_markup"]
        assert schema["has_microdata"] is True
        assert schema["microdata_count"] == 1
        assert "MedicalOrganization" in schema["schema_types"]
        assert schema["has_structured_data"] is True

    def test_schema_markup_none(self):
        """Test schema markup detection with no structured data."""
        analyzer = TechnicalSEOAnalyzer()

        html = "<html><body><p>Content</p></body></html>"

        result = analyzer.analyze(html, "https://example.com")

        schema = result["schema_markup"]
        assert schema["has_json_ld"] is False
        assert schema["has_microdata"] is False
        assert schema["has_rdfa"] is False
        assert schema["has_structured_data"] is False

    def test_security_https(self):
        """Test security analysis with HTTPS."""
        analyzer = TechnicalSEOAnalyzer()

        html = "<html><body><p>Content</p></body></html>"

        result = analyzer.analyze(html, "https://example.com")

        security = result["security"]
        assert security["is_https"] is True
        assert security["has_mixed_content"] is False
        assert security["security_score"] == 100

    def test_security_http(self):
        """Test security analysis with HTTP."""
        analyzer = TechnicalSEOAnalyzer()

        html = "<html><body><p>Content</p></body></html>"

        result = analyzer.analyze(html, "http://example.com")

        security = result["security"]
        assert security["is_https"] is False
        assert security["security_score"] == 0

    def test_security_mixed_content(self):
        """Test security analysis with mixed content."""
        analyzer = TechnicalSEOAnalyzer()

        html = """
        <html>
        <body>
            <img src="http://example.com/image.jpg">
            <script src="http://example.com/script.js"></script>
        </body>
        </html>
        """

        result = analyzer.analyze(html, "https://example.com")

        security = result["security"]
        assert security["is_https"] is True
        assert security["has_mixed_content"] is True
        assert security["mixed_content_count"] == 2
        assert security["security_score"] == 50

    def test_meta_tags_canonical(self):
        """Test meta tags analysis with canonical."""
        analyzer = TechnicalSEOAnalyzer()

        html = """
        <html>
        <head>
            <link rel="canonical" href="https://example.com/page">
        </head>
        <body><p>Content</p></body>
        </html>
        """

        result = analyzer.analyze(html, "https://example.com")

        meta = result["meta_tags"]
        assert meta["has_canonical"] is True
        assert meta["canonical_url"] == "https://example.com/page"

    def test_meta_tags_robots(self):
        """Test meta tags analysis with robots."""
        analyzer = TechnicalSEOAnalyzer()

        html = """
        <html>
        <head>
            <meta name="robots" content="index, follow">
        </head>
        <body><p>Content</p></body>
        </html>
        """

        result = analyzer.analyze(html, "https://example.com")

        meta = result["meta_tags"]
        assert meta["has_robots"] is True
        assert meta["robots_content"] == "index, follow"

    def test_meta_tags_hreflang(self):
        """Test meta tags analysis with hreflang."""
        analyzer = TechnicalSEOAnalyzer()

        html = """
        <html>
        <head>
            <link rel="alternate" hreflang="en" href="https://example.com/en">
            <link rel="alternate" hreflang="ru" href="https://example.com/ru">
        </head>
        <body><p>Content</p></body>
        </html>
        """

        result = analyzer.analyze(html, "https://example.com")

        meta = result["meta_tags"]
        assert meta["has_hreflang"] is True
        assert meta["hreflang_count"] == 2

    def test_technical_score_excellent(self):
        """Test technical score calculation - excellent."""
        analyzer = TechnicalSEOAnalyzer()

        html = """
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <meta name="mobile-web-app-capable" content="yes">
            <link rel="canonical" href="https://example.com/page">
            <link rel="preload" href="font.woff2" as="font">
            <script type="application/ld+json">{"@type": "MedicalOrganization"}</script>
        </head>
        <body>
            <img src="image.jpg" loading="lazy">
            <script src="script.js" defer></script>
        </body>
        </html>
        """

        metrics = {"lcp": 2.0, "inp": 150.0, "cls": 0.05}
        result = analyzer.analyze(html, "https://example.com", metrics=metrics)

        assert result["technical_score"] >= 80
        assert result["technical_level"] == "excellent"

    def test_technical_score_poor(self):
        """Test technical score calculation - poor."""
        analyzer = TechnicalSEOAnalyzer()

        html = "<html><body><p>Content</p></body></html>"

        result = analyzer.analyze(html, "http://example.com")

        assert result["technical_score"] < 40
        assert result["technical_level"] == "poor"

    def test_technical_level_classification(self):
        """Test technical level classification."""
        analyzer = TechnicalSEOAnalyzer()

        assert analyzer._get_technical_level(85) == "excellent"
        assert analyzer._get_technical_level(70) == "good"
        assert analyzer._get_technical_level(50) == "fair"
        assert analyzer._get_technical_level(30) == "poor"
