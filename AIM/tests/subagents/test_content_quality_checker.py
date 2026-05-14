"""Tests for Content Quality Checker."""

import pytest

from AIM.src.aim.subagents.content.content_quality_checker import (
    ContentQualityChecker,
    ContentQualityReport,
    ReadabilityAnalysis,
    GrammarAnalysis,
    UniquenessAnalysis,
    EEATAnalysis,
    ContentDepthAnalysis,
    EngagementAnalysis,
)


@pytest.fixture
def checker():
    """Create Content Quality Checker instance."""
    return ContentQualityChecker()


@pytest.fixture
def sample_content():
    """Sample content for testing."""
    return """
    Dental implants are a modern solution for missing teeth. They provide a permanent
    replacement that looks and functions like natural teeth. In my experience working
    with patients for over 15 years, dental implants have transformed countless lives.

    According to recent studies, dental implants have a 95% success rate. This makes
    them one of the most reliable dental procedures available today.

    For example, one of our patients received implants after losing teeth in an accident.
    The results were amazing, and they regained their confidence completely.

    If you're considering dental implants, contact our clinic today for a consultation.
    """


@pytest.mark.asyncio
async def test_check_complete_report(checker, sample_content):
    """Test complete content quality check."""
    report = await checker.check(
        url="https://example.com/dental-implants",
        content=sample_content,
        target_keyword="dental implants",
    )

    assert isinstance(report, ContentQualityReport)
    assert report.url == "https://example.com/dental-implants"
    assert isinstance(report.readability, ReadabilityAnalysis)
    assert isinstance(report.grammar, GrammarAnalysis)
    assert isinstance(report.uniqueness, UniquenessAnalysis)
    assert isinstance(report.eeat, EEATAnalysis)
    assert isinstance(report.depth, ContentDepthAnalysis)
    assert isinstance(report.engagement, EngagementAnalysis)
    assert 0 <= report.overall_quality_score <= 100
    assert report.quality_grade in ["A+", "A", "B", "C", "D", "F"]


@pytest.mark.asyncio
async def test_analyze_readability(checker, sample_content):
    """Test readability analysis."""
    readability = await checker._analyze_readability(sample_content)

    assert isinstance(readability, ReadabilityAnalysis)
    assert 0 <= readability.flesch_reading_ease <= 100
    assert readability.flesch_kincaid_grade >= 0
    assert readability.avg_sentence_length > 0
    assert readability.avg_word_length > 0
    assert 0 <= readability.complex_words_percent <= 100
    assert readability.readability_level in [
        "very_easy", "easy", "medium", "difficult", "very_difficult"
    ]


@pytest.mark.asyncio
async def test_analyze_readability_long_sentences(checker):
    """Test readability with long sentences."""
    content = "This is a very long sentence with many words that goes on and on and on and on and on and on and on and on and on and on and on and on."
    readability = await checker._analyze_readability(content)

    assert readability.avg_sentence_length > 25
    assert any("long sentences" in issue.lower() for issue in readability.issues)


@pytest.mark.asyncio
async def test_analyze_grammar(checker, sample_content):
    """Test grammar analysis."""
    grammar = await checker._analyze_grammar(sample_content)

    assert isinstance(grammar, GrammarAnalysis)
    assert grammar.total_errors >= 0
    assert grammar.spelling_errors >= 0
    assert grammar.grammar_errors >= 0
    assert grammar.punctuation_errors >= 0
    assert grammar.style_issues >= 0
    assert grammar.error_rate >= 0
    assert isinstance(grammar.issues, list)


@pytest.mark.asyncio
async def test_analyze_uniqueness(checker, sample_content):
    """Test uniqueness analysis."""
    uniqueness = await checker._analyze_uniqueness(sample_content)

    assert isinstance(uniqueness, UniquenessAnalysis)
    assert 0 <= uniqueness.uniqueness_score <= 100
    assert isinstance(uniqueness.duplicate_phrases, list)
    assert isinstance(uniqueness.plagiarism_detected, bool)
    assert 0 <= uniqueness.ai_generated_probability <= 100


@pytest.mark.asyncio
async def test_analyze_eeat(checker, sample_content):
    """Test E-E-A-T analysis."""
    eeat = await checker._analyze_eeat(sample_content)

    assert isinstance(eeat, EEATAnalysis)
    assert 0 <= eeat.experience_score <= 100
    assert 0 <= eeat.expertise_score <= 100
    assert 0 <= eeat.authoritativeness_score <= 100
    assert 0 <= eeat.trustworthiness_score <= 100
    assert 0 <= eeat.overall_eeat_score <= 100
    assert isinstance(eeat.signals_found, list)
    assert isinstance(eeat.missing_signals, list)


@pytest.mark.asyncio
async def test_analyze_eeat_with_signals(checker):
    """Test E-E-A-T with strong signals."""
    content = """
    In my experience as a certified dentist with 20 years of expertise,
    I have published research in dental journals. According to studies
    from Harvard Medical School, this approach is proven effective.
    """
    eeat = await checker._analyze_eeat(content)

    assert eeat.experience_score > 0
    assert eeat.expertise_score > 0
    assert eeat.trustworthiness_score > 0
    assert len(eeat.signals_found) > 0


@pytest.mark.asyncio
async def test_analyze_depth(checker, sample_content):
    """Test content depth analysis."""
    depth = await checker._analyze_depth(sample_content, "dental implants")

    assert isinstance(depth, ContentDepthAnalysis)
    assert depth.word_count > 0
    assert 0 <= depth.topic_coverage_score <= 100
    assert depth.subtopics_covered >= 0
    assert isinstance(depth.subtopics_missing, list)
    assert isinstance(depth.has_examples, bool)
    assert isinstance(depth.has_data, bool)
    assert isinstance(depth.has_visuals, bool)
    assert depth.depth_level in ["shallow", "moderate", "comprehensive", "expert"]


@pytest.mark.asyncio
async def test_analyze_depth_shallow(checker):
    """Test shallow content depth."""
    content = "Short content here. Not much depth."
    depth = await checker._analyze_depth(content, None)

    assert depth.word_count < 500
    assert depth.depth_level == "shallow"
    assert any("expand" in rec.lower() for rec in depth.recommendations)


@pytest.mark.asyncio
async def test_analyze_engagement(checker, sample_content):
    """Test engagement analysis."""
    engagement = await checker._analyze_engagement(sample_content)

    assert isinstance(engagement, EngagementAnalysis)
    assert 0 <= engagement.hook_strength <= 100
    assert 0 <= engagement.storytelling_score <= 100
    assert 0 <= engagement.emotional_appeal <= 100
    assert isinstance(engagement.call_to_action_present, bool)
    assert 0 <= engagement.multimedia_usage <= 100
    assert 0 <= engagement.engagement_score <= 100


@pytest.mark.asyncio
async def test_analyze_engagement_with_cta(checker):
    """Test engagement with CTA."""
    content = "Great content here. Contact us today to get started!"
    engagement = await checker._analyze_engagement(content)

    assert engagement.call_to_action_present is True


@pytest.mark.asyncio
async def test_analyze_engagement_no_cta(checker):
    """Test engagement without CTA."""
    content = "Just some content without any call to action."
    engagement = await checker._analyze_engagement(content)

    assert engagement.call_to_action_present is False
    assert any("call-to-action" in rec.lower() for rec in engagement.recommendations)


def test_calculate_overall_score(checker):
    """Test overall score calculation."""
    readability = ReadabilityAnalysis(
        flesch_reading_ease=70.0,
        flesch_kincaid_grade=8.0,
        avg_sentence_length=15.0,
        avg_word_length=5.0,
        complex_words_percent=10.0,
        readability_level="easy",
        issues=[],
        recommendations=[],
    )
    grammar = GrammarAnalysis(
        total_errors=2,
        spelling_errors=1,
        grammar_errors=1,
        punctuation_errors=0,
        style_issues=0,
        error_rate=0.5,
        issues=[],
        recommendations=[],
    )
    uniqueness = UniquenessAnalysis(
        uniqueness_score=90.0,
        duplicate_phrases=[],
        plagiarism_detected=False,
        ai_generated_probability=10.0,
        issues=[],
        recommendations=[],
    )
    eeat = EEATAnalysis(
        experience_score=80.0,
        expertise_score=80.0,
        authoritativeness_score=60.0,
        trustworthiness_score=80.0,
        overall_eeat_score=75.0,
        signals_found=["Experience", "Expertise"],
        missing_signals=[],
        recommendations=[],
    )
    depth = ContentDepthAnalysis(
        word_count=1500,
        topic_coverage_score=80.0,
        subtopics_covered=6,
        subtopics_missing=[],
        has_examples=True,
        has_data=True,
        has_visuals=True,
        depth_level="comprehensive",
        recommendations=[],
    )
    engagement = EngagementAnalysis(
        hook_strength=60.0,
        storytelling_score=40.0,
        emotional_appeal=50.0,
        call_to_action_present=True,
        multimedia_usage=70.0,
        engagement_score=64.0,
        recommendations=[],
    )

    score = checker._calculate_overall_score(
        readability, grammar, uniqueness, eeat, depth, engagement
    )

    assert 0 <= score <= 100
    assert score > 70  # Should be good quality


def test_determine_grade(checker):
    """Test quality grade determination."""
    assert checker._determine_grade(96) == "A+"
    assert checker._determine_grade(92) == "A"
    assert checker._determine_grade(85) == "B"
    assert checker._determine_grade(75) == "C"
    assert checker._determine_grade(65) == "D"
    assert checker._determine_grade(50) == "F"


def test_identify_priority_issues(checker):
    """Test priority issues identification."""
    readability = ReadabilityAnalysis(
        flesch_reading_ease=25.0,  # Very difficult
        flesch_kincaid_grade=15.0,
        avg_sentence_length=30.0,
        avg_word_length=7.0,
        complex_words_percent=20.0,
        readability_level="very_difficult",
        issues=["Low readability"],
        recommendations=[],
    )
    grammar = GrammarAnalysis(
        total_errors=50,
        spelling_errors=20,
        grammar_errors=20,
        punctuation_errors=10,
        style_issues=0,
        error_rate=5.0,  # High error rate
        issues=[],
        recommendations=[],
    )
    uniqueness = UniquenessAnalysis(
        uniqueness_score=65.0,  # Low uniqueness
        duplicate_phrases=[],
        plagiarism_detected=False,
        ai_generated_probability=10.0,
        issues=["Low uniqueness"],
        recommendations=[],
    )
    eeat = EEATAnalysis(
        experience_score=20.0,
        expertise_score=20.0,
        authoritativeness_score=20.0,
        trustworthiness_score=20.0,
        overall_eeat_score=20.0,  # Weak E-E-A-T
        signals_found=[],
        missing_signals=["All signals missing"],
        recommendations=[],
    )

    issues = checker._identify_priority_issues(readability, grammar, uniqueness, eeat)

    assert len(issues) > 0
    assert any("CRITICAL" in issue for issue in issues)


def test_identify_quick_wins(checker):
    """Test quick wins identification."""
    grammar = GrammarAnalysis(
        total_errors=5,
        spelling_errors=3,
        grammar_errors=2,
        punctuation_errors=0,
        style_issues=0,
        error_rate=1.0,
        issues=[],
        recommendations=[],
    )
    engagement = EngagementAnalysis(
        hook_strength=60.0,
        storytelling_score=40.0,
        emotional_appeal=50.0,
        call_to_action_present=False,  # Missing CTA
        multimedia_usage=30.0,
        engagement_score=46.0,
        recommendations=[],
    )
    depth = ContentDepthAnalysis(
        word_count=800,
        topic_coverage_score=60.0,
        subtopics_covered=4,
        subtopics_missing=[],
        has_examples=False,  # Missing examples
        has_data=True,
        has_visuals=False,
        depth_level="moderate",
        recommendations=[],
    )

    quick_wins = checker._identify_quick_wins(grammar, engagement, depth)

    assert len(quick_wins) > 0
    assert any("grammar" in win.lower() or "spelling" in win.lower() for win in quick_wins)
    assert any("call-to-action" in win.lower() for win in quick_wins)
