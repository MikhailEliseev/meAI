"""Tests for On-Page SEO Optimizer."""

import pytest

from src.aim.subagents.seo.onpage_optimizer import (
    OnPageOptimizer,
    OnPageReport,
    TitleTagAnalysis,
    MetaDescriptionAnalysis,
    HeaderStructure,
    ContentAnalysis,
    InternalLinking,
    ImageOptimization,
    URLAnalysis,
)


@pytest.fixture
def optimizer():
    """Create On-Page SEO Optimizer instance."""
    return OnPageOptimizer()


@pytest.fixture
def sample_html():
    """Sample HTML for testing."""
    return """
    <html>
    <head>
        <title>Dental Implants in Moscow - Best Clinic 2026</title>
        <meta name="description" content="Professional dental implants in Moscow. 15 years experience. Book consultation today!">
    </head>
    <body>
        <h1>Dental Implants in Moscow</h1>
        <p>We provide professional dental implant services with 15 years of experience.</p>
        <h2>Why Choose Us</h2>
        <p>Our clinic offers the best dental implant solutions in Moscow.</p>
        <h3>Our Services</h3>
        <ul>
            <li>Single tooth implants</li>
            <li>Multiple tooth implants</li>
            <li>Full arch restoration</li>
        </ul>
        <img src="clinic.jpg" alt="Dental clinic interior">
        <img src="doctor.jpg">
        <a href="/services">Our Services</a>
        <a href="/contact">Contact Us</a>
        <a href="https://example.com">External Link</a>
    </body>
    </html>
    """


@pytest.mark.asyncio
async def test_analyze_complete_report(optimizer, sample_html):
    """Test complete on-page analysis."""
    report = await optimizer.analyze(
        url="https://example.com/dental-implants-moscow",
        target_keyword="dental implants",
        html_content=sample_html,
    )

    assert isinstance(report, OnPageReport)
    assert report.url == "https://example.com/dental-implants-moscow"
    assert isinstance(report.title_tag, TitleTagAnalysis)
    assert isinstance(report.meta_description, MetaDescriptionAnalysis)
    assert isinstance(report.headers, HeaderStructure)
    assert isinstance(report.content, ContentAnalysis)
    assert isinstance(report.internal_linking, InternalLinking)
    assert isinstance(report.images, ImageOptimization)
    assert isinstance(report.url_analysis, URLAnalysis)
    assert 0 <= report.overall_score <= 100
    assert len(report.priority_issues) > 0
    assert len(report.quick_wins) > 0


@pytest.mark.asyncio
async def test_analyze_title_tag(optimizer, sample_html):
    """Test title tag analysis."""
    title = await optimizer._analyze_title_tag(sample_html, "dental implants")

    assert isinstance(title, TitleTagAnalysis)
    assert title.title == "Dental Implants in Moscow - Best Clinic 2026"
    assert title.length > 0
    assert title.has_keyword is True
    assert title.keyword_position > 0
    assert isinstance(title.issues, list)
    assert isinstance(title.recommendations, list)


@pytest.mark.asyncio
async def test_analyze_title_tag_missing_keyword(optimizer):
    """Test title tag without keyword."""
    html = "<html><head><title>Best Clinic 2026</title></head></html>"
    title = await optimizer._analyze_title_tag(html, "dental implants")

    assert title.has_keyword is False
    assert title.keyword_position == 0
    assert any("keyword" in issue.lower() for issue in title.issues)


@pytest.mark.asyncio
async def test_analyze_meta_description(optimizer, sample_html):
    """Test meta description analysis."""
    meta = await optimizer._analyze_meta_description(sample_html, "dental implants")

    assert isinstance(meta, MetaDescriptionAnalysis)
    assert len(meta.description) > 0
    assert meta.has_keyword is True
    assert meta.has_cta is True  # "Book consultation"
    assert isinstance(meta.issues, list)
    assert isinstance(meta.recommendations, list)


@pytest.mark.asyncio
async def test_analyze_meta_description_no_cta(optimizer):
    """Test meta description without CTA."""
    html = '<html><head><meta name="description" content="Professional dental implants in Moscow."></head></html>'
    meta = await optimizer._analyze_meta_description(html, "dental implants")

    assert meta.has_cta is False
    assert any("cta" in issue.lower() for issue in meta.issues)


@pytest.mark.asyncio
async def test_analyze_headers(optimizer, sample_html):
    """Test header structure analysis."""
    headers = await optimizer._analyze_headers(sample_html, "dental implants")

    assert isinstance(headers, HeaderStructure)
    assert headers.h1_count == 1
    assert len(headers.h1_text) == 1
    assert headers.h2_count > 0
    assert headers.h3_count > 0
    assert headers.has_keyword_in_h1 is True
    assert isinstance(headers.issues, list)
    assert isinstance(headers.recommendations, list)


@pytest.mark.asyncio
async def test_analyze_headers_multiple_h1(optimizer):
    """Test multiple H1 tags."""
    html = "<html><body><h1>First H1</h1><h1>Second H1</h1></body></html>"
    headers = await optimizer._analyze_headers(html, "dental implants")

    assert headers.h1_count == 2
    assert any("multiple" in issue.lower() for issue in headers.issues)


@pytest.mark.asyncio
async def test_analyze_content(optimizer, sample_html):
    """Test content analysis."""
    content = await optimizer._analyze_content(sample_html, "dental implants")

    assert isinstance(content, ContentAnalysis)
    assert content.word_count > 0
    assert content.keyword_density >= 0
    assert content.keyword_count > 0
    assert content.paragraph_count > 0
    assert content.has_lists is True
    assert content.has_images is True
    assert isinstance(content.issues, list)
    assert isinstance(content.recommendations, list)


@pytest.mark.asyncio
async def test_analyze_content_short(optimizer):
    """Test short content."""
    html = "<html><body><p>Short content here.</p></body></html>"
    content = await optimizer._analyze_content(html, "dental implants")

    assert content.word_count < 300
    assert any("short" in issue.lower() for issue in content.issues)


@pytest.mark.asyncio
async def test_analyze_internal_linking(optimizer, sample_html):
    """Test internal linking analysis."""
    linking = await optimizer._analyze_internal_linking(sample_html)

    assert isinstance(linking, InternalLinking)
    assert linking.total_links > 0
    assert linking.internal_links > 0
    assert linking.external_links > 0
    assert linking.internal_links + linking.external_links == linking.total_links
    assert isinstance(linking.issues, list)
    assert isinstance(linking.recommendations, list)


@pytest.mark.asyncio
async def test_analyze_images(optimizer, sample_html):
    """Test image optimization analysis."""
    images = await optimizer._analyze_images(sample_html)

    assert isinstance(images, ImageOptimization)
    assert images.total_images == 2
    assert images.images_with_alt == 1
    assert images.images_without_alt == 1
    assert 0 <= images.alt_text_quality <= 100
    assert isinstance(images.issues, list)
    assert isinstance(images.recommendations, list)


@pytest.mark.asyncio
async def test_analyze_images_all_with_alt(optimizer):
    """Test images with alt text."""
    html = '<html><body><img src="1.jpg" alt="Image 1"><img src="2.jpg" alt="Image 2"></body></html>'
    images = await optimizer._analyze_images(html)

    assert images.total_images == 2
    assert images.images_with_alt == 2
    assert images.images_without_alt == 0


@pytest.mark.asyncio
async def test_analyze_url(optimizer):
    """Test URL structure analysis."""
    url_analysis = await optimizer._analyze_url(
        "https://example.com/dental-implants-moscow",
        "dental implants",
    )

    assert isinstance(url_analysis, URLAnalysis)
    assert url_analysis.url == "https://example.com/dental-implants-moscow"
    assert url_analysis.length > 0
    assert url_analysis.has_keyword is True
    assert url_analysis.depth >= 0
    assert isinstance(url_analysis.issues, list)
    assert isinstance(url_analysis.recommendations, list)


@pytest.mark.asyncio
async def test_analyze_url_no_keyword(optimizer):
    """Test URL without keyword."""
    url_analysis = await optimizer._analyze_url(
        "https://example.com/services/page1",
        "dental implants",
    )

    assert url_analysis.has_keyword is False
    assert any("keyword" in issue.lower() for issue in url_analysis.issues)


def test_calculate_overall_score(optimizer):
    """Test overall score calculation."""
    # Perfect elements
    title = TitleTagAnalysis(
        title="Dental Implants Moscow",
        length=55,
        has_keyword=True,
        keyword_position=1,
        is_optimal_length=True,
        issues=[],
        recommendations=[],
    )
    meta = MetaDescriptionAnalysis(
        description="Professional dental implants in Moscow. Book today!",
        length=155,
        has_keyword=True,
        has_cta=True,
        is_optimal_length=True,
        issues=[],
        recommendations=[],
    )
    headers = HeaderStructure(
        h1_count=1,
        h1_text=["Dental Implants"],
        h2_count=3,
        h3_count=2,
        has_keyword_in_h1=True,
        hierarchy_valid=True,
        issues=[],
        recommendations=[],
    )
    content = ContentAnalysis(
        word_count=500,
        keyword_density=1.5,
        keyword_count=7,
        readability_score=65.0,
        paragraph_count=5,
        avg_paragraph_length=100.0,
        has_lists=True,
        has_images=True,
        issues=[],
        recommendations=[],
    )
    linking = InternalLinking(
        total_links=5,
        internal_links=4,
        external_links=1,
        broken_links=0,
        anchor_text_optimized=True,
        link_depth=2,
        issues=[],
        recommendations=[],
    )
    images = ImageOptimization(
        total_images=3,
        images_with_alt=3,
        images_without_alt=0,
        alt_text_quality=100.0,
        large_images=0,
        webp_usage=100.0,
        issues=[],
        recommendations=[],
    )
    url = URLAnalysis(
        url="https://example.com/dental-implants",
        length=40,
        has_keyword=True,
        is_readable=True,
        has_special_chars=False,
        depth=1,
        issues=[],
        recommendations=[],
    )

    score = optimizer._calculate_overall_score(
        title, meta, headers, content, linking, images, url
    )

    assert score == 100.0


def test_identify_priority_issues(optimizer):
    """Test priority issues identification."""
    title = TitleTagAnalysis(
        title="Best Clinic",
        length=20,
        has_keyword=False,
        keyword_position=0,
        is_optimal_length=False,
        issues=["No keyword"],
        recommendations=[],
    )
    meta = MetaDescriptionAnalysis(
        description="Great clinic",
        length=50,
        has_keyword=False,
        has_cta=False,
        is_optimal_length=False,
        issues=["No keyword"],
        recommendations=[],
    )
    headers = HeaderStructure(
        h1_count=0,
        h1_text=[],
        h2_count=0,
        h3_count=0,
        has_keyword_in_h1=False,
        hierarchy_valid=False,
        issues=["No H1"],
        recommendations=[],
    )
    content = ContentAnalysis(
        word_count=100,
        keyword_density=0.0,
        keyword_count=0,
        readability_score=50.0,
        paragraph_count=1,
        avg_paragraph_length=100.0,
        has_lists=False,
        has_images=False,
        issues=["Too short"],
        recommendations=[],
    )

    issues = optimizer._identify_priority_issues(title, meta, headers, content)

    assert len(issues) > 0
    assert any("CRITICAL" in issue for issue in issues)
    assert any("title" in issue.lower() for issue in issues)


def test_identify_quick_wins(optimizer):
    """Test quick wins identification."""
    title = TitleTagAnalysis(
        title="Short",
        length=5,
        has_keyword=True,
        keyword_position=1,
        is_optimal_length=False,
        issues=["Too short"],
        recommendations=[],
    )
    meta = MetaDescriptionAnalysis(
        description="No CTA here",
        length=155,
        has_keyword=True,
        has_cta=False,
        is_optimal_length=True,
        issues=["No CTA"],
        recommendations=[],
    )
    images = ImageOptimization(
        total_images=3,
        images_with_alt=1,
        images_without_alt=2,
        alt_text_quality=33.3,
        large_images=0,
        webp_usage=0.0,
        issues=["Missing alt"],
        recommendations=[],
    )

    quick_wins = optimizer._identify_quick_wins(title, meta, images)

    assert len(quick_wins) > 0
    assert any("cta" in win.lower() for win in quick_wins)
    assert any("alt" in win.lower() for win in quick_wins)
