"""Tests for Landing Page Analyzer."""

import pytest

from src.aim.subagents.ads.landing_page_analyzer import (
    LandingPageAnalyzer,
    LandingPageReport,
    RelevanceAnalysis,
    ConversionOptimization,
    UserExperience,
    MobileOptimization,
    PerformanceAnalysis,
)


@pytest.fixture
def analyzer():
    """Create Landing Page Analyzer instance."""
    return LandingPageAnalyzer()


@pytest.fixture
def sample_html():
    """Sample HTML for testing."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dental Implants - Best Clinic in Moscow</title>
        <meta name="description" content="Professional dental implants. Book consultation today!">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body>
        <nav>
            <a href="/">Home</a>
            <a href="/services">Services</a>
            <a href="/contact">Contact</a>
        </nav>
        <h1>Dental Implants</h1>
        <p>We offer professional dental implants with 15 years of experience.</p>
        <button>Book Consultation</button>
        <form>
            <input type="text" name="name" placeholder="Name">
            <input type="email" name="email" placeholder="Email">
            <input type="tel" name="phone" placeholder="Phone">
            <button type="submit">Submit</button>
        </form>
        <div class="testimonial">
            <p>"Great service!" - John Doe</p>
        </div>
        <img src="trust-badge.png" alt="Certified Clinic">
    </body>
    </html>
    """


@pytest.mark.asyncio
async def test_analyze_complete_report(analyzer, sample_html):
    """Test complete landing page analysis."""
    report = await analyzer.analyze(
        url="https://example.com/dental-implants",
        html_content=sample_html,
        ad_headline="Dental Implants Moscow",
        ad_keyword="dental implants",
    )

    assert isinstance(report, LandingPageReport)
    assert report.url == "https://example.com/dental-implants"
    assert isinstance(report.relevance, RelevanceAnalysis)
    assert isinstance(report.conversion, ConversionOptimization)
    assert isinstance(report.ux, UserExperience)
    assert isinstance(report.mobile, MobileOptimization)
    assert isinstance(report.performance, PerformanceAnalysis)
    assert 0 <= report.overall_quality_score <= 100
    assert report.quality_rating in ["excellent", "good", "fair", "poor"]


@pytest.mark.asyncio
async def test_analyze_relevance(analyzer, sample_html):
    """Test relevance analysis."""
    relevance = await analyzer._analyze_relevance(
        html=sample_html,
        keyword="dental implants",
        headline="Dental Implants Moscow",
    )

    assert isinstance(relevance, RelevanceAnalysis)
    assert 0 <= relevance.keyword_match_score <= 100
    assert 0 <= relevance.headline_relevance <= 100
    assert 0 <= relevance.content_relevance <= 100
    assert 0 <= relevance.cta_alignment <= 100
    assert 0 <= relevance.overall_relevance <= 100


@pytest.mark.asyncio
async def test_analyze_relevance_high_match(analyzer):
    """Test relevance with high keyword match."""
    html = """
    <html>
    <head><title>Dental Implants Moscow</title></head>
    <body>
        <h1>Dental Implants</h1>
        <p>Best dental implants in Moscow. Professional implants service.</p>
        <button>Book Consultation</button>
    </body>
    </html>
    """
    relevance = await analyzer._analyze_relevance(
        html=html,
        keyword="dental implants",
        headline="Dental Implants Moscow",
    )

    assert relevance.keyword_match_score > 50
    assert relevance.content_relevance > 0


@pytest.mark.asyncio
async def test_analyze_conversion(analyzer, sample_html):
    """Test conversion analysis."""
    conversion = await analyzer._analyze_conversion(sample_html)

    assert isinstance(conversion, ConversionOptimization)
    assert conversion.cta_count >= 0
    assert 0 <= conversion.cta_visibility <= 100
    assert conversion.form_complexity in ["simple", "moderate", "complex"]
    assert conversion.form_fields_count >= 0
    assert isinstance(conversion.trust_signals, list)
    assert isinstance(conversion.urgency_elements, list)
    assert isinstance(conversion.social_proof, list)
    assert 0 <= conversion.conversion_score <= 100


@pytest.mark.asyncio
async def test_analyze_conversion_multiple_ctas(analyzer):
    """Test conversion with multiple CTAs."""
    html = """
    <html>
    <body>
        <button>Book Now</button>
        <a href="/contact">Contact Us</a>
        <button>Get Started</button>
    </body>
    </html>
    """
    conversion = await analyzer._analyze_conversion(html)

    assert conversion.cta_count >= 2


@pytest.mark.asyncio
async def test_analyze_conversion_no_cta(analyzer):
    """Test conversion without CTA."""
    html = "<html><body><p>Just some text</p></body></html>"
    conversion = await analyzer._analyze_conversion(html)

    assert conversion.cta_count == 0


@pytest.mark.asyncio
async def test_analyze_ux(analyzer, sample_html):
    """Test UX analysis."""
    ux = await analyzer._analyze_ux(sample_html)

    assert isinstance(ux, UserExperience)
    assert 0 <= ux.navigation_clarity <= 100
    assert 0 <= ux.content_readability <= 100
    assert 0 <= ux.visual_hierarchy <= 100
    assert 0 <= ux.distraction_score <= 100
    assert 0 <= ux.ux_score <= 100


@pytest.mark.asyncio
async def test_analyze_ux_good_navigation(analyzer):
    """Test UX with good navigation."""
    html = """
    <html>
    <body>
        <nav>
            <a href="/">Home</a>
            <a href="/services">Services</a>
            <a href="/about">About</a>
            <a href="/contact">Contact</a>
        </nav>
        <h1>Main Heading</h1>
        <h2>Subheading</h2>
        <p>Content here.</p>
    </body>
    </html>
    """
    ux = await analyzer._analyze_ux(html)

    assert ux.navigation_clarity > 0


@pytest.mark.asyncio
async def test_analyze_mobile(analyzer, sample_html):
    """Test mobile analysis."""
    mobile = await analyzer._analyze_mobile(sample_html)

    assert isinstance(mobile, MobileOptimization)
    assert isinstance(mobile.is_mobile_friendly, bool)
    assert isinstance(mobile.viewport_configured, bool)
    assert isinstance(mobile.touch_targets_adequate, bool)
    assert isinstance(mobile.text_readable, bool)
    assert 0 <= mobile.mobile_score <= 100


@pytest.mark.asyncio
async def test_analyze_mobile_with_viewport(analyzer):
    """Test mobile with viewport meta."""
    html = """
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body>
        <button style="min-width: 48px; min-height: 48px;">Click</button>
    </body>
    </html>
    """
    mobile = await analyzer._analyze_mobile(html)

    assert mobile.viewport_configured is True


@pytest.mark.asyncio
async def test_analyze_mobile_no_viewport(analyzer):
    """Test mobile without viewport meta."""
    html = "<html><body><p>Content</p></body></html>"
    mobile = await analyzer._analyze_mobile(html)

    assert mobile.viewport_configured is False


@pytest.mark.asyncio
async def test_analyze_performance(analyzer):
    """Test performance analysis."""
    performance = await analyzer._analyze_performance("https://example.com")

    assert isinstance(performance, PerformanceAnalysis)
    assert performance.load_time > 0
    assert performance.page_size > 0
    assert performance.requests_count > 0
    assert 0 <= performance.performance_score <= 100


def test_calculate_overall_score(analyzer):
    """Test overall score calculation."""
    relevance = RelevanceAnalysis(
        keyword_match_score=80.0,
        headline_relevance=90.0,
        content_relevance=85.0,
        cta_alignment=75.0,
        overall_relevance=82.5,
        issues=[],
        recommendations=[],
    )
    conversion = ConversionOptimization(
        cta_count=2,
        cta_visibility=80.0,
        form_complexity="simple",
        form_fields_count=3,
        trust_signals=["badge", "testimonial"],
        urgency_elements=["limited time"],
        social_proof=["review"],
        conversion_score=75.0,
        recommendations=[],
    )
    ux = UserExperience(
        navigation_clarity=80.0,
        content_readability=70.0,
        visual_hierarchy=85.0,
        distraction_score=20.0,
        ux_score=80.0,
        issues=[],
        recommendations=[],
    )
    mobile = MobileOptimization(
        is_mobile_friendly=True,
        viewport_configured=True,
        touch_targets_adequate=True,
        text_readable=True,
        mobile_score=85.0,
        issues=[],
        recommendations=[],
    )
    performance = PerformanceAnalysis(
        load_time=2.5,
        page_size=300.0,
        requests_count=25,
        performance_score=75.0,
        issues=[],
        recommendations=[],
    )

    score = analyzer._calculate_overall_score(
        relevance, conversion, ux, mobile, performance
    )

    assert 0 <= score <= 100
    assert score > 70


def test_determine_rating(analyzer):
    """Test quality rating determination."""
    assert analyzer._determine_rating(90) == "excellent"
    assert analyzer._determine_rating(75) == "good"
    assert analyzer._determine_rating(60) == "good"  # >= 60 is "good"
    assert analyzer._determine_rating(50) == "fair"
    assert analyzer._determine_rating(30) == "poor"


def test_identify_priority_issues(analyzer):
    """Test priority issues identification."""
    relevance = RelevanceAnalysis(
        keyword_match_score=30.0,
        headline_relevance=40.0,
        content_relevance=35.0,
        cta_alignment=50.0,
        overall_relevance=38.75,
        issues=["Low keyword match"],
        recommendations=[],
    )
    conversion = ConversionOptimization(
        cta_count=0,
        cta_visibility=0.0,
        form_complexity="simple",
        form_fields_count=0,
        trust_signals=[],
        urgency_elements=[],
        social_proof=[],
        conversion_score=20.0,
        recommendations=[],
    )
    mobile = MobileOptimization(
        is_mobile_friendly=False,
        viewport_configured=False,
        touch_targets_adequate=False,
        text_readable=False,
        mobile_score=30.0,
        issues=["No viewport meta"],
        recommendations=[],
    )

    issues = analyzer._identify_priority_issues(relevance, conversion, mobile)

    assert len(issues) > 0


def test_identify_quick_wins(analyzer):
    """Test quick wins identification."""
    conversion = ConversionOptimization(
        cta_count=0,
        cta_visibility=0.0,
        form_complexity="simple",
        form_fields_count=3,
        trust_signals=[],
        urgency_elements=[],
        social_proof=[],
        conversion_score=40.0,
        recommendations=[],
    )
    ux = UserExperience(
        navigation_clarity=70.0,
        content_readability=60.0,
        visual_hierarchy=65.0,
        distraction_score=30.0,
        ux_score=65.0,
        issues=[],
        recommendations=[],
    )
    mobile = MobileOptimization(
        is_mobile_friendly=False,
        viewport_configured=False,
        touch_targets_adequate=True,
        text_readable=True,
        mobile_score=60.0,
        issues=[],
        recommendations=[],
    )

    quick_wins = analyzer._identify_quick_wins(conversion, ux, mobile)

    assert len(quick_wins) > 0
