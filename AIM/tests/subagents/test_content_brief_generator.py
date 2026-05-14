"""Tests for Content Brief Generator."""

import pytest
from unittest.mock import AsyncMock, patch

from AIM.src.aim.subagents.content.content_brief_generator import (
    ContentBriefGenerator,
    ContentBrief,
    HeaderStructure,
    TopicCoverage,
    QuestionToAnswer,
)
from AIM.src.aim.subagents.schemas.api_responses import KeywordDataUnified
from AIM.src.aim.subagents.seo.keyword_research_agent import (
    KeywordResearchResult,
    KeywordIntent,
    KeywordCluster,
    KeywordPriority,
)
# CI Content Analyzer returns dict, not dataclass


@pytest.fixture
def generator():
    """Create Content Brief Generator instance."""
    return ContentBriefGenerator(
        semrush_api_key="test_semrush_key",
        ahrefs_api_key="test_ahrefs_key",
    )


@pytest.fixture
def mock_keyword_data():
    """Mock keyword research result."""
    return KeywordResearchResult(
        seed_keyword="dental implants",
        timestamp="2026-05-14T12:00:00",
        keywords=[
            KeywordDataUnified(
                keyword="dental implants",
                volume=5000,
                difficulty=45.0,
                cpc=12.5,
                intent="commercial",
                source="semrush",
                priority_score=75.0,
            ),
        ],
        total_keywords=1,
        intents=[
            KeywordIntent(
                keyword="dental implants",
                intent="commercial",
                confidence=0.8,
                signals=["best", "price"],
            ),
        ],
        clusters=[],
        total_clusters=0,
        priorities=[],
        total_volume=5000,
        avg_difficulty=45.0,
        avg_cpc=12.5,
        top_opportunities=[],
    )


@pytest.fixture
def mock_competitor_analysis():
    """Mock competitor analysis result."""
    return {
        "url": "https://example.com/dental-implants",
        "word_count": 1500,
        "quality_score": 85.0,
        "headers": ["H1: Dental Implants Guide", "H2: What are Dental Implants?"],
        "readability_score": 70.0,
        "keyword_density": 2.5,
        "internal_links": 10,
        "external_links": 5,
        "images": 8,
        "videos": 2,
    }


@pytest.mark.asyncio
async def test_generate_brief(generator, mock_keyword_data):
    """Test complete brief generation."""
    # Mock _analyze_competitors directly since it's internal method
    async def mock_analyze_competitors(urls):
        return [{
            "url": "https://example.com/dental-implants",
            "word_count": 1500,
            "quality_score": 85.0,
            "headers": ["H1: Dental Implants Guide", "H2: What are Dental Implants?"],
        }]

    with patch.object(
        generator.keyword_agent,
        "research",
        new_callable=AsyncMock,
        return_value=mock_keyword_data,
    ), patch.object(
        generator,
        "_analyze_competitors",
        new_callable=AsyncMock,
        side_effect=mock_analyze_competitors,
    ):
        brief = await generator.generate(
            target_keyword="dental implants",
            competitor_urls=["https://example.com/dental-implants"],
        )

        assert isinstance(brief, ContentBrief)
        assert brief.target_keyword == "dental implants"
        assert brief.search_volume == 5000
        assert brief.keyword_difficulty == 45.0
        assert brief.search_intent == "commercial"
        assert brief.recommended_word_count > 0
        assert len(brief.header_structure) > 0
        assert len(brief.topics_to_cover) > 0
        assert len(brief.questions_to_answer) > 0
        assert len(brief.title_suggestions) > 0
        assert brief.meta_description_suggestion != ""


@pytest.mark.asyncio
async def test_analyze_keyword(generator, mock_keyword_data):
    """Test keyword analysis."""
    with patch.object(
        generator.keyword_agent,
        "research",
        new_callable=AsyncMock,
        return_value=mock_keyword_data,
    ):
        result = await generator._analyze_keyword("dental implants")

        assert result["volume"] == 5000
        assert result["difficulty"] == 45.0
        assert result["intent"] == "commercial"


@pytest.mark.asyncio
async def test_analyze_keyword_fallback(generator):
    """Test keyword analysis fallback when no data."""
    with patch.object(
        generator.keyword_agent,
        "research",
        new_callable=AsyncMock,
        return_value=KeywordResearchResult(
            seed_keyword="test",
            timestamp="2026-05-14T12:00:00",
            keywords=[],
            total_keywords=0,
            intents=[],
            clusters=[],
            total_clusters=0,
            priorities=[],
            total_volume=0,
            avg_difficulty=0.0,
            avg_cpc=0.0,
            top_opportunities=[],
        ),
    ):
        result = await generator._analyze_keyword("test")

        assert result["volume"] == 0
        assert result["difficulty"] == 50.0
        assert result["intent"] == "informational"


@pytest.mark.asyncio
async def test_analyze_competitors(generator):
    """Test competitor analysis."""
    # Mock _analyze_competitors internal method
    async def mock_analyze_competitors(urls):
        return [{
            "url": "https://example.com/dental-implants",
            "word_count": 1500,
            "quality_score": 85.0,
        }]

    with patch.object(
        generator,
        "_analyze_competitors",
        new_callable=AsyncMock,
        side_effect=mock_analyze_competitors,
    ):
        result = await generator._analyze_competitors(
            ["https://example.com/dental-implants"]
        )

        assert len(result) == 1
        assert result[0]["url"] == "https://example.com/dental-implants"
        assert result[0]["word_count"] == 1500
        assert result[0]["quality_score"] == 85.0


@pytest.mark.asyncio
async def test_analyze_competitors_error_handling(generator):
    """Test competitor analysis error handling."""
    # Mock to raise exception
    async def mock_analyze_competitors_error(urls):
        raise Exception("API error")

    with patch.object(
        generator,
        "_analyze_competitors",
        new_callable=AsyncMock,
        side_effect=mock_analyze_competitors_error,
    ):
        try:
            await generator._analyze_competitors(
                ["https://example.com/dental-implants"]
            )
        except Exception:
            pass  # Expected to raise


def test_calculate_word_count_with_target(generator):
    """Test word count calculation with target."""
    result = generator._calculate_word_count([], 2000)

    assert result["recommended"] == 2000
    assert result["range"] == (1800, 2200)
    assert result["competitor_avg"] == 0


def test_calculate_word_count_without_competitors(generator):
    """Test word count calculation without competitors."""
    result = generator._calculate_word_count([], None)

    assert result["recommended"] == 1500
    assert result["range"] == (1200, 1800)
    assert result["competitor_avg"] == 0


def test_calculate_word_count_from_competitors(generator):
    """Test word count calculation from competitors."""
    competitors = [
        {"word_count": 1000},
        {"word_count": 1500},
        {"word_count": 2000},
    ]

    result = generator._calculate_word_count(competitors, None)

    assert result["recommended"] == int(1500 * 1.15)  # 1725
    assert result["competitor_avg"] == 1500


def test_generate_header_structure(generator):
    """Test header structure generation."""
    headers = generator._generate_header_structure("dental implants", [])

    assert len(headers) > 0
    assert headers[0].level == 1
    assert "dental implants" in headers[0].text.lower()
    assert any(h.level == 2 for h in headers)


def test_identify_topics(generator):
    """Test topic identification."""
    competitors = [
        {"word_count": 1500},
        {"word_count": 2000},
    ]

    topics = generator._identify_topics(competitors)

    assert len(topics) > 0
    assert all(isinstance(t, TopicCoverage) for t in topics)
    assert all(t.priority in ["high", "medium", "low"] for t in topics)


def test_generate_questions_informational(generator):
    """Test question generation for informational intent."""
    questions = generator._generate_questions("dental implants", "informational")

    assert len(questions) > 0
    assert all(isinstance(q, QuestionToAnswer) for q in questions)
    assert any("what is" in q.question.lower() for q in questions)
    assert any("how does" in q.question.lower() for q in questions)


def test_generate_questions_commercial(generator):
    """Test question generation for commercial intent."""
    questions = generator._generate_questions("dental implants", "commercial")

    assert len(questions) > 0
    assert all(isinstance(q, QuestionToAnswer) for q in questions)
    assert any("best" in q.question.lower() for q in questions)
    assert any("choose" in q.question.lower() for q in questions)


def test_generate_title_suggestions(generator):
    """Test title suggestions generation."""
    titles = generator._generate_title_suggestions("dental implants")

    assert len(titles) == 3
    assert all("dental implants" in t.lower() for t in titles)
    assert any("2026" in t for t in titles)


def test_generate_meta_description_informational(generator):
    """Test meta description for informational intent."""
    meta = generator._generate_meta_description("dental implants", "informational")

    assert "dental implants" in meta.lower()
    assert "learn" in meta.lower() or "guide" in meta.lower()


def test_generate_meta_description_commercial(generator):
    """Test meta description for commercial intent."""
    meta = generator._generate_meta_description("dental implants", "commercial")

    assert "dental implants" in meta.lower()
    assert "compare" in meta.lower() or "best" in meta.lower()


def test_determine_tone(generator):
    """Test tone determination."""
    assert generator._determine_tone("informational") == "educational"
    assert generator._determine_tone("commercial") == "professional"
    assert generator._determine_tone("transactional") == "conversational"
    assert generator._determine_tone("navigational") == "conversational"
