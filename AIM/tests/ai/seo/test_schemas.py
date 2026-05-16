"""
Tests for SEO schemas
"""

import pytest
from pydantic import ValidationError

from aim.ai.seo.schemas import (
    Entity,
    ContentQualityScore,
    EntityAnalysis,
    SERPAnalysis,
    SERPFeature,
    ConversationalOptimization,
    SEOAnalysisResult,
)


class TestEntity:
    """Test Entity schema."""

    def test_valid_entity(self):
        """Test valid entity creation."""
        entity = Entity(
            text="Москва",
            label="GPE",
            start=0,
            end=6,
            confidence=0.95,
        )

        assert entity.text == "Москва"
        assert entity.label == "GPE"
        assert entity.start == 0
        assert entity.end == 6
        assert entity.confidence == 0.95

    def test_entity_confidence_bounds(self):
        """Test entity confidence validation."""
        # Valid confidence
        entity = Entity(text="Test", label="ORG", start=0, end=4, confidence=0.5)
        assert entity.confidence == 0.5

        # Invalid confidence (< 0)
        with pytest.raises(ValidationError):
            Entity(text="Test", label="ORG", start=0, end=4, confidence=-0.1)

        # Invalid confidence (> 1)
        with pytest.raises(ValidationError):
            Entity(text="Test", label="ORG", start=0, end=4, confidence=1.1)


class TestContentQualityScore:
    """Test ContentQualityScore schema."""

    def test_valid_score(self):
        """Test valid content quality score."""
        score = ContentQualityScore(
            overall=85.5,
            newsworthiness=80.0,
            expertise=90.0,
            experience=85.0,
            authoritativeness=88.0,
            trustworthiness=92.0,
            transparency=75.0,
            readability=82.0,
            recommendations=["Добавить автора", "Улучшить структуру"],
        )

        assert score.overall == 85.5
        assert score.expertise == 90.0
        assert len(score.recommendations) == 2

    def test_score_bounds(self):
        """Test score validation (0-100)."""
        # Valid scores
        score = ContentQualityScore(
            overall=50.0,
            newsworthiness=0.0,
            expertise=100.0,
            experience=50.0,
            authoritativeness=50.0,
            trustworthiness=50.0,
            transparency=50.0,
            readability=50.0,
            recommendations=[],
        )
        assert score.newsworthiness == 0.0
        assert score.expertise == 100.0

        # Invalid score (< 0)
        with pytest.raises(ValidationError):
            ContentQualityScore(
                overall=-1.0,
                newsworthiness=50.0,
                expertise=50.0,
                experience=50.0,
                authoritativeness=50.0,
                trustworthiness=50.0,
                transparency=50.0,
                readability=50.0,
                recommendations=[],
            )

        # Invalid score (> 100)
        with pytest.raises(ValidationError):
            ContentQualityScore(
                overall=101.0,
                newsworthiness=50.0,
                expertise=50.0,
                experience=50.0,
                authoritativeness=50.0,
                trustworthiness=50.0,
                transparency=50.0,
                readability=50.0,
                recommendations=[],
            )


class TestEntityAnalysis:
    """Test EntityAnalysis schema."""

    def test_valid_analysis(self):
        """Test valid entity analysis."""
        entities = [
            Entity(text="Москва", label="GPE", start=0, end=6, confidence=0.95),
            Entity(text="Google", label="ORG", start=10, end=16, confidence=0.90),
        ]

        analysis = EntityAnalysis(
            entities=entities,
            density=3.5,
            schema_suggestions=["Organization", "Place"],
            related_entities=["Связь организация-место"],
            knowledge_graph_ready=True,
        )

        assert len(analysis.entities) == 2
        assert analysis.density == 3.5
        assert analysis.knowledge_graph_ready is True

    def test_density_bounds(self):
        """Test density validation."""
        # Valid density
        analysis = EntityAnalysis(
            entities=[],
            density=5.0,
            schema_suggestions=[],
            related_entities=[],
            knowledge_graph_ready=False,
        )
        assert analysis.density == 5.0

        # Invalid density (< 0)
        with pytest.raises(ValidationError):
            EntityAnalysis(
                entities=[],
                density=-1.0,
                schema_suggestions=[],
                related_entities=[],
                knowledge_graph_ready=False,
            )


class TestSERPFeature:
    """Test SERPFeature schema."""

    def test_valid_feature(self):
        """Test valid SERP feature."""
        feature = SERPFeature(
            type="featured_snippet",
            present=True,
            owned=False,
            opportunity_score=90.0,
        )

        assert feature.type == "featured_snippet"
        assert feature.present is True
        assert feature.owned is False
        assert feature.opportunity_score == 90.0

    def test_opportunity_score_bounds(self):
        """Test opportunity score validation."""
        # Valid score
        feature = SERPFeature(
            type="knowledge_graph",
            present=True,
            owned=True,
            opportunity_score=50.0,
        )
        assert feature.opportunity_score == 50.0

        # Invalid score (< 0)
        with pytest.raises(ValidationError):
            SERPFeature(
                type="paa",
                present=True,
                owned=False,
                opportunity_score=-1.0,
            )

        # Invalid score (> 100)
        with pytest.raises(ValidationError):
            SERPFeature(
                type="paa",
                present=True,
                owned=False,
                opportunity_score=101.0,
            )


class TestSERPAnalysis:
    """Test SERPAnalysis schema."""

    def test_valid_analysis(self):
        """Test valid SERP analysis."""
        features = [
            SERPFeature(
                type="featured_snippet",
                present=True,
                owned=False,
                opportunity_score=90.0,
            ),
        ]

        analysis = SERPAnalysis(
            query="стоматология москва",
            featured_snippet="Стоматология в Москве...",
            paa_questions=["Сколько стоит?", "Где лучше?"],
            knowledge_panel={"title": "Стоматология", "type": "MedicalBusiness"},
            competitor_gaps=["Featured snippet не занят"],
            serp_features=features,
            top_10_urls=["https://example.com"],
        )

        assert analysis.query == "стоматология москва"
        assert len(analysis.paa_questions) == 2
        assert len(analysis.serp_features) == 1


class TestConversationalOptimization:
    """Test ConversationalOptimization schema."""

    def test_valid_optimization(self):
        """Test valid conversational optimization."""
        opt = ConversationalOptimization(
            ai_overviews_score=85.0,
            chatgpt_score=80.0,
            perplexity_score=90.0,
            conversational_queries=["Как выбрать клинику?"],
            answer_box_ready=True,
            faq_suggestions=[{"question": "Q?", "answer": "A."}],
            citation_score=88.0,
        )

        assert opt.ai_overviews_score == 85.0
        assert opt.answer_box_ready is True
        assert len(opt.faq_suggestions) == 1

    def test_score_bounds(self):
        """Test score validation."""
        # Valid scores
        opt = ConversationalOptimization(
            ai_overviews_score=0.0,
            chatgpt_score=100.0,
            perplexity_score=50.0,
            conversational_queries=[],
            answer_box_ready=False,
            faq_suggestions=[],
            citation_score=75.0,
        )
        assert opt.ai_overviews_score == 0.0
        assert opt.chatgpt_score == 100.0

        # Invalid score
        with pytest.raises(ValidationError):
            ConversationalOptimization(
                ai_overviews_score=-1.0,
                chatgpt_score=50.0,
                perplexity_score=50.0,
                conversational_queries=[],
                answer_box_ready=False,
                faq_suggestions=[],
                citation_score=50.0,
            )


class TestSEOAnalysisResult:
    """Test SEOAnalysisResult schema."""

    def test_valid_result(self):
        """Test valid SEO analysis result."""
        content_quality = ContentQualityScore(
            overall=85.0,
            newsworthiness=80.0,
            expertise=90.0,
            experience=85.0,
            authoritativeness=88.0,
            trustworthiness=92.0,
            transparency=75.0,
            readability=82.0,
            recommendations=[],
        )

        entity_analysis = EntityAnalysis(
            entities=[],
            density=3.5,
            schema_suggestions=["Organization"],
            related_entities=[],
            knowledge_graph_ready=True,
        )

        conversational = ConversationalOptimization(
            ai_overviews_score=85.0,
            chatgpt_score=80.0,
            perplexity_score=90.0,
            conversational_queries=[],
            answer_box_ready=True,
            faq_suggestions=[],
            citation_score=88.0,
        )

        result = SEOAnalysisResult(
            url="https://example.com",
            content_quality=content_quality,
            entity_analysis=entity_analysis,
            serp_analysis=None,
            conversational=conversational,
            overall_score=87.5,
            priority_actions=["Action 1", "Action 2"],
            estimated_impact="HIGH",
        )

        assert result.url == "https://example.com"
        assert result.overall_score == 87.5
        assert len(result.priority_actions) == 2
        assert result.estimated_impact == "HIGH"

    def test_overall_score_bounds(self):
        """Test overall score validation."""
        content_quality = ContentQualityScore(
            overall=85.0,
            newsworthiness=80.0,
            expertise=90.0,
            experience=85.0,
            authoritativeness=88.0,
            trustworthiness=92.0,
            transparency=75.0,
            readability=82.0,
            recommendations=[],
        )

        entity_analysis = EntityAnalysis(
            entities=[],
            density=3.5,
            schema_suggestions=[],
            related_entities=[],
            knowledge_graph_ready=False,
        )

        conversational = ConversationalOptimization(
            ai_overviews_score=85.0,
            chatgpt_score=80.0,
            perplexity_score=90.0,
            conversational_queries=[],
            answer_box_ready=False,
            faq_suggestions=[],
            citation_score=88.0,
        )

        # Invalid overall score (< 0)
        with pytest.raises(ValidationError):
            SEOAnalysisResult(
                url="https://example.com",
                content_quality=content_quality,
                entity_analysis=entity_analysis,
                serp_analysis=None,
                conversational=conversational,
                overall_score=-1.0,
                priority_actions=[],
                estimated_impact="LOW",
            )

        # Invalid overall score (> 100)
        with pytest.raises(ValidationError):
            SEOAnalysisResult(
                url="https://example.com",
                content_quality=content_quality,
                entity_analysis=entity_analysis,
                serp_analysis=None,
                conversational=conversational,
                overall_score=101.0,
                priority_actions=[],
                estimated_impact="LOW",
            )
