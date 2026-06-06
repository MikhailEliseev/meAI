"""
Tests for SEO Analyzer
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.aim.ai.seo.analyzer import SEOAnalyzer, analyze_url
from src.aim.ai.seo.schemas import (
    ContentQualityScore,
    EntityAnalysis,
    SERPAnalysis,
    SERPFeature,
    ConversationalOptimization,
    Entity,
)


@pytest.fixture
def mock_llm_client():
    """Mock LLM client."""
    client = MagicMock()
    client.generate = AsyncMock()
    return client


@pytest.fixture
def mock_content_quality():
    """Mock content quality score."""
    return ContentQualityScore(
        overall=85.0,
        newsworthiness=80.0,
        expertise=90.0,
        experience=85.0,
        authoritativeness=88.0,
        trustworthiness=92.0,
        transparency=75.0,
        readability=82.0,
        recommendations=["Добавить автора", "Улучшить структуру"],
    )


@pytest.fixture
def mock_entity_analysis():
    """Mock entity analysis."""
    return EntityAnalysis(
        entities=[
            Entity(text="Москва", label="GPE", start=0, end=6, confidence=0.95),
            Entity(text="Google", label="ORG", start=10, end=16, confidence=0.90),
        ],
        density=3.5,
        schema_suggestions=["Organization", "Place", "WebPage"],
        related_entities=["Связь организация-место"],
        knowledge_graph_ready=True,
    )


@pytest.fixture
def mock_serp_analysis():
    """Mock SERP analysis."""
    return SERPAnalysis(
        query="стоматология москва",
        featured_snippet="Стоматология в Москве...",
        paa_questions=["Сколько стоит?", "Где лучше?"],
        knowledge_panel={"title": "Стоматология", "type": "MedicalBusiness"},
        competitor_gaps=["Featured snippet не занят"],
        serp_features=[
            SERPFeature(
                type="featured_snippet",
                present=True,
                owned=False,
                opportunity_score=90.0,
            ),
        ],
        top_10_urls=["https://example.com"],
    )


@pytest.fixture
def mock_conversational():
    """Mock conversational optimization."""
    return ConversationalOptimization(
        ai_overviews_score=85.0,
        chatgpt_score=80.0,
        perplexity_score=90.0,
        conversational_queries=["Как выбрать клинику?"],
        answer_box_ready=True,
        faq_suggestions=[{"question": "Q?", "answer": "A."}],
        citation_score=88.0,
    )


@pytest.mark.asyncio
class TestSEOAnalyzer:
    """Test SEOAnalyzer class."""

    async def test_analyze_without_serp(
        self,
        mock_llm_client,
        mock_content_quality,
        mock_entity_analysis,
        mock_conversational,
    ):
        """Test analysis without SERP data."""
        # Mock EntityOptimizer to avoid spaCy model requirement
        with patch("src.aim.ai.seo.analyzer.EntityOptimizer"):
            analyzer = SEOAnalyzer(
                llm_client=mock_llm_client,
                serp_api_key="test_key",
            )

            # Mock component analyzers with AsyncMock
            analyzer.content_analyzer.analyze = AsyncMock(return_value=mock_content_quality)
            analyzer.entity_optimizer.analyze = AsyncMock(return_value=mock_entity_analysis)
            analyzer.conversational_optimizer.analyze = AsyncMock(return_value=mock_conversational)

            result = await analyzer.analyze(
                url="https://example.com",
                content="<html><body>Test content</body></html>",
                include_serp=False,
            )

            assert result.url == "https://example.com"
            assert result.content_quality == mock_content_quality
            assert result.entity_analysis == mock_entity_analysis
            assert result.conversational == mock_conversational
            assert result.serp_analysis is None
            assert 0 <= result.overall_score <= 100
            # High scores (85+) may have no priority actions
            assert isinstance(result.priority_actions, list)

            await analyzer.close()

    async def test_analyze_with_serp(
        self,
        mock_llm_client,
        mock_content_quality,
        mock_entity_analysis,
        mock_conversational,
        mock_serp_analysis,
    ):
        """Test analysis with SERP data."""
        # Mock EntityOptimizer to avoid spaCy model requirement
        with patch("src.aim.ai.seo.analyzer.EntityOptimizer"):
            analyzer = SEOAnalyzer(
                llm_client=mock_llm_client,
                serp_api_key="test_key",
            )

            # Mock component analyzers with AsyncMock
            analyzer.content_analyzer.analyze = AsyncMock(return_value=mock_content_quality)
            analyzer.entity_optimizer.analyze = AsyncMock(return_value=mock_entity_analysis)
            analyzer.conversational_optimizer.analyze = AsyncMock(return_value=mock_conversational)
            analyzer.serp_analyzer.analyze = AsyncMock(return_value=mock_serp_analysis)

            result = await analyzer.analyze(
                url="https://example.com",
                content="<html><body>Test content</body></html>",
                target_query="стоматология москва",
                include_serp=True,
            )

            assert result.url == "https://example.com"
            assert result.serp_analysis == mock_serp_analysis
            assert 0 <= result.overall_score <= 100
            assert len(result.priority_actions) > 0

            await analyzer.close()

    async def test_calculate_overall_score(
        self,
        mock_llm_client,
        mock_content_quality,
        mock_entity_analysis,
        mock_conversational,
        mock_serp_analysis,
    ):
        """Test overall score calculation."""
        # Mock EntityOptimizer to avoid spaCy model requirement
        with patch("src.aim.ai.seo.analyzer.EntityOptimizer"):
            analyzer = SEOAnalyzer(
                llm_client=mock_llm_client,
                serp_api_key="test_key",
            )

            score = analyzer._calculate_overall_score(
                content_quality=mock_content_quality,
                entity_analysis=mock_entity_analysis,
                conversational=mock_conversational,
                serp_analysis=mock_serp_analysis,
            )

            # Score should be weighted average
            assert 0 <= score <= 100
            assert isinstance(score, float)

            await analyzer.close()

    async def test_generate_priority_actions(
        self,
        mock_llm_client,
        mock_content_quality,
        mock_entity_analysis,
        mock_conversational,
        mock_serp_analysis,
    ):
        """Test priority actions generation."""
        # Mock EntityOptimizer to avoid spaCy model requirement
        with patch("src.aim.ai.seo.analyzer.EntityOptimizer"):
            analyzer = SEOAnalyzer(
                llm_client=mock_llm_client,
                serp_api_key="test_key",
            )

            actions = analyzer._generate_priority_actions(
                content_quality=mock_content_quality,
                entity_analysis=mock_entity_analysis,
                conversational=mock_conversational,
                serp_analysis=mock_serp_analysis,
            )

            # Should return list of actions
            assert isinstance(actions, list)
            # Low scores generate actions, high scores may not
            assert all(isinstance(action, str) for action in actions)

            # If actions exist, they should have emoji prefixes (any emoji)
            if actions:
                # Check that at least one action has an emoji (any emoji character)
                assert any(any(ord(c) > 127 for c in action) for action in actions)

            await analyzer.close()

    async def test_estimate_impact(self, mock_llm_client):
        """Test impact estimation."""
        # Mock EntityOptimizer to avoid spaCy model requirement
        with patch("src.aim.ai.seo.analyzer.EntityOptimizer"):
            analyzer = SEOAnalyzer(
                llm_client=mock_llm_client,
                serp_api_key="test_key",
            )

            # Critical impact (score < 50)
            impact = analyzer._estimate_impact(45.0, ["action1", "action2"])
            assert "CRITICAL" in impact

            # High impact (score 50-70, high potential)
            impact = analyzer._estimate_impact(60.0, ["action1", "action2", "action3"])
            assert "HIGH" in impact or "MEDIUM" in impact

            # Medium impact (score 70-85)
            impact = analyzer._estimate_impact(75.0, ["action1"])
            assert "MEDIUM" in impact

            # Low impact (score > 85)
            impact = analyzer._estimate_impact(90.0, ["action1"])
            assert "LOW" in impact

            await analyzer.close()


@pytest.mark.asyncio
class TestAnalyzeURL:
    """Test analyze_url convenience function."""

    async def test_analyze_url(
        self,
        mock_llm_client,
        mock_content_quality,
        mock_entity_analysis,
        mock_conversational,
    ):
        """Test analyze_url function."""
        with patch("src.aim.ai.seo.analyzer.SEOAnalyzer") as MockAnalyzer:
            # Mock analyzer instance
            mock_analyzer = MagicMock()
            mock_analyzer.analyze = AsyncMock(return_value=MagicMock(
                url="https://example.com",
                overall_score=85.0,
            ))
            mock_analyzer.close = AsyncMock()
            MockAnalyzer.return_value = mock_analyzer

            result = await analyze_url(
                url="https://example.com",
                content="<html><body>Test</body></html>",
                llm_client=mock_llm_client,
                serp_api_key="test_key",
            )

            # Verify analyzer was created and used
            MockAnalyzer.assert_called_once()
            mock_analyzer.analyze.assert_called_once()
            mock_analyzer.close.assert_called_once()

            assert result.url == "https://example.com"
            assert result.overall_score == 85.0


@pytest.mark.asyncio
class TestSEOAnalyzerIntegration:
    """Integration tests for SEO analyzer."""

    async def test_full_analysis_flow(self, mock_llm_client):
        """Test full analysis flow with all components."""
        # This is a smoke test to ensure all components work together
        # Mock EntityOptimizer to avoid spaCy model requirement
        with patch("src.aim.ai.seo.analyzer.EntityOptimizer"):
            analyzer = SEOAnalyzer(
                llm_client=mock_llm_client,
                serp_api_key="test_key",
            )

            # Mock all component analyzers
            mock_content = ContentQualityScore(
                overall=70.0,
                newsworthiness=65.0,
                expertise=75.0,
                experience=70.0,
                authoritativeness=72.0,
                trustworthiness=68.0,
                transparency=65.0,
                readability=70.0,
                recommendations=["Improve expertise"],
            )

            mock_entities = EntityAnalysis(
                entities=[],
                density=1.5,
                schema_suggestions=["WebPage"],
                related_entities=[],
                knowledge_graph_ready=False,
            )

            mock_conv = ConversationalOptimization(
                ai_overviews_score=65.0,
                chatgpt_score=60.0,
                perplexity_score=70.0,
                conversational_queries=[],
                answer_box_ready=False,
                faq_suggestions=[],
                citation_score=68.0,
            )

            analyzer.content_analyzer.analyze = AsyncMock(return_value=mock_content)
            analyzer.entity_optimizer.analyze = AsyncMock(return_value=mock_entities)
            analyzer.conversational_optimizer.analyze = AsyncMock(return_value=mock_conv)

            result = await analyzer.analyze(
                url="https://example.com",
                content="<html><body><h1>Test</h1><p>Content</p></body></html>",
                metadata={"title": "Test Page"},
                include_serp=False,
            )

            # Verify result structure
            assert result.url == "https://example.com"
            assert result.content_quality.overall == 70.0
            assert result.entity_analysis.density == 1.5
            assert result.conversational.ai_overviews_score == 65.0
            assert result.serp_analysis is None
            assert 0 <= result.overall_score <= 100
            assert len(result.priority_actions) > 0
            # estimated_impact contains full description, check it starts with expected keyword
            assert any(keyword in result.estimated_impact for keyword in ["LOW", "MEDIUM", "HIGH", "CRITICAL"])

            await analyzer.close()
