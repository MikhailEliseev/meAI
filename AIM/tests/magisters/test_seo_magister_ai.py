"""
Tests for SEO Magister AI
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from AIM.src.aim.magisters.seo_magister_ai import SEOMagisterAI
from AIM.src.aim.ai.seo.schemas import (
    ContentQualityScore,
    EntityAnalysis,
    SERPAnalysis,
    SERPFeature,
    ConversationalOptimization,
    SEOAnalysisResult,
    Entity,
)


@pytest.fixture
def mock_llm_client():
    """Mock LLM client."""
    client = MagicMock()
    client.generate = AsyncMock()
    return client


@pytest.fixture
def mock_seo_analyzer():
    """Mock SEO Analyzer with async close."""
    with patch("AIM.src.aim.magisters.seo_magister_ai.SEOAnalyzer") as MockAnalyzer:
        mock_analyzer = MagicMock()
        mock_analyzer.close = AsyncMock()
        mock_analyzer.analyze = AsyncMock()
        MockAnalyzer.return_value = mock_analyzer
        yield MockAnalyzer


@pytest.fixture
def mock_traditional_result():
    """Mock traditional SEO analysis result."""
    return {
        "url": "https://example.com",
        "correlation_id": "test-123",
        "status": "success",
        "timestamp": "2026-05-16T13:00:00Z",
        "duration_seconds": 5.5,
        "scores": {
            "overall": 75.0,
            "technical": 80.0,
            "content": 70.0,
            "links": 75.0,
        },
        "summary": "Good SEO health",
        "recommendations": [
            {
                "priority": "high",
                "category": "technical",
                "issue": "Missing sitemap",
                "action": "Create sitemap.xml",
            }
        ],
        "details": {},
    }


@pytest.fixture
def mock_ai_result():
    """Mock AI SEO analysis result."""
    return SEOAnalysisResult(
        url="https://example.com",
        content_quality=ContentQualityScore(
            overall=85.0,
            newsworthiness=80.0,
            expertise=90.0,
            experience=85.0,
            authoritativeness=88.0,
            trustworthiness=92.0,
            transparency=75.0,
            readability=82.0,
            recommendations=["Add author bio"],
        ),
        entity_analysis=EntityAnalysis(
            entities=[
                Entity(text="Москва", label="GPE", start=0, end=6, confidence=0.95),
            ],
            density=3.5,
            schema_suggestions=["Organization", "Place"],
            related_entities=["Связь организация-место"],
            knowledge_graph_ready=True,
        ),
        serp_analysis=SERPAnalysis(
            query="test query",
            featured_snippet="Test snippet",
            paa_questions=["Question 1?"],
            knowledge_panel={"title": "Test"},
            competitor_gaps=["Gap 1"],
            serp_features=[
                SERPFeature(
                    type="featured_snippet",
                    present=True,
                    owned=False,
                    opportunity_score=90.0,
                )
            ],
            top_10_urls=["https://example.com"],
        ),
        conversational=ConversationalOptimization(
            ai_overviews_score=85.0,
            chatgpt_score=80.0,
            perplexity_score=90.0,
            conversational_queries=["How to?"],
            answer_box_ready=True,
            faq_suggestions=[{"question": "Q?", "answer": "A."}],
            citation_score=88.0,
        ),
        overall_score=87.5,
        priority_actions=[
            "🎓 Expertise: Add author credentials",
            "🏷️ Entities: Increase entity density",
        ],
        estimated_impact="HIGH - Significant improvement possible",
    )


@pytest.mark.asyncio
class TestSEOMagisterAI:
    """Test SEO Magister AI class."""

    async def test_init(self, mock_llm_client, mock_seo_analyzer):
        """Test initialization."""
        magister = SEOMagisterAI(
            llm_client=mock_llm_client,
            serp_api_key="test_key",
            timeout=600,
        )

        assert magister.ai_analyzer is not None
        assert magister.timeout == 600

        await magister.close()
        magister.ai_analyzer.close.assert_called_once()

    async def test_coordinate_analysis_with_ai(
        self,
        mock_llm_client,
        mock_seo_analyzer,
        mock_traditional_result,
        mock_ai_result,
    ):
        """Test coordinate analysis with AI enabled."""
        magister = SEOMagisterAI(
            llm_client=mock_llm_client,
            serp_api_key="test_key",
        )

        # Mock parent coordinate_analysis
        with patch.object(
            SEOMagisterAI.__bases__[0],
            "coordinate_analysis",
            new_callable=AsyncMock,
            return_value=mock_traditional_result,
        ):
            # Mock AI analysis
            magister._run_ai_analysis = AsyncMock(return_value=mock_ai_result)

            result = await magister.coordinate_analysis(
                url="https://example.com",
                target_query="test query",
                include_serp=True,
                include_ai=True,
            )

            assert result["status"] == "success"
            assert result["url"] == "https://example.com"
            assert "traditional_seo" in result
            assert "ai_seo" in result
            assert "combined_score" in result
            assert "combined_recommendations" in result

            # Check combined score (50% traditional + 50% AI)
            expected_combined = (75.0 * 0.5) + (87.5 * 0.5)
            assert result["combined_score"] == round(expected_combined, 1)

            # Check AI results structure
            assert result["ai_seo"]["status"] == "success"
            assert result["ai_seo"]["overall_score"] == 87.5
            assert "content_quality" in result["ai_seo"]
            assert "entity_analysis" in result["ai_seo"]
            assert "conversational" in result["ai_seo"]
            assert "serp_analysis" in result["ai_seo"]

        await magister.close()

    async def test_coordinate_analysis_without_ai(
        self,
        mock_llm_client,
        mock_seo_analyzer,
        mock_traditional_result,
    ):
        """Test coordinate analysis with AI disabled."""
        magister = SEOMagisterAI(
            llm_client=mock_llm_client,
            serp_api_key="test_key",
        )

        # Mock parent coordinate_analysis
        with patch.object(
            SEOMagisterAI.__bases__[0],
            "coordinate_analysis",
            new_callable=AsyncMock,
            return_value=mock_traditional_result,
        ):
            result = await magister.coordinate_analysis(
                url="https://example.com",
                include_ai=False,
            )

            assert result["status"] == "success"
            assert "traditional_seo" in result
            assert result["ai_seo"]["status"] == "not_included"
            assert result["combined_score"] == 75.0  # Only traditional

        await magister.close()

    async def test_run_ai_analysis_success(self, mock_llm_client, mock_seo_analyzer):
        """Test successful AI analysis."""
        magister = SEOMagisterAI(
            llm_client=mock_llm_client,
            serp_api_key="test_key",
        )

        # Mock httpx client
        mock_response = MagicMock()
        mock_response.text = "<html><body>Test content</body></html>"

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            # Mock AI analyzer
            mock_result = MagicMock()
            magister.ai_analyzer.analyze = AsyncMock(return_value=mock_result)

            result = await magister._run_ai_analysis(
                url="https://example.com",
                target_query="test query",
                include_serp=True,
            )

            assert result == mock_result
            magister.ai_analyzer.analyze.assert_called_once()

        await magister.close()

    async def test_run_ai_analysis_error(self, mock_llm_client, mock_seo_analyzer):
        """Test AI analysis error handling."""
        magister = SEOMagisterAI(
            llm_client=mock_llm_client,
            serp_api_key="test_key",
        )

        # Mock httpx client to raise error
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=Exception("Network error")
            )

            result = await magister._run_ai_analysis(
                url="https://example.com",
                target_query="test query",
                include_serp=True,
            )

            assert result["status"] == "error"
            assert "Network error" in result["error"]

        await magister.close()

    async def test_combine_results_with_ai(
        self,
        mock_llm_client,
        mock_seo_analyzer,
        mock_traditional_result,
        mock_ai_result,
    ):
        """Test combining traditional and AI results."""
        from datetime import datetime, timezone

        magister = SEOMagisterAI(
            llm_client=mock_llm_client,
            serp_api_key="test_key",
        )

        start_time = datetime.now(timezone.utc)

        result = await magister._combine_results(
            url="https://example.com",
            correlation_id="test-123",
            traditional_result=mock_traditional_result,
            ai_result=mock_ai_result,
            start_time=start_time,
        )

        assert result["status"] == "success"
        assert result["url"] == "https://example.com"
        assert "traditional_seo" in result
        assert "ai_seo" in result
        assert "combined_score" in result
        assert "score_breakdown" in result
        assert "combined_recommendations" in result

        # Check score breakdown
        assert result["score_breakdown"]["traditional"] == 75.0
        assert result["score_breakdown"]["ai"] == 87.5

        # Check combined score
        expected = (75.0 * 0.5) + (87.5 * 0.5)
        assert result["combined_score"] == round(expected, 1)

        await magister.close()

    async def test_combine_results_ai_error(
        self,
        mock_llm_client,
        mock_seo_analyzer,
        mock_traditional_result,
    ):
        """Test combining results when AI analysis failed."""
        from datetime import datetime, timezone

        magister = SEOMagisterAI(
            llm_client=mock_llm_client,
            serp_api_key="test_key",
        )

        start_time = datetime.now(timezone.utc)
        ai_error = {"status": "error", "error": "AI failed"}

        result = await magister._combine_results(
            url="https://example.com",
            correlation_id="test-123",
            traditional_result=mock_traditional_result,
            ai_result=ai_error,
            start_time=start_time,
        )

        assert result["status"] == "success"
        assert result["ai_seo"]["status"] == "error"
        assert result["combined_score"] == 75.0  # Only traditional

        await magister.close()

    async def test_generate_combined_recommendations(
        self,
        mock_llm_client,
        mock_seo_analyzer,
        mock_traditional_result,
        mock_ai_result,
    ):
        """Test generating combined recommendations."""
        magister = SEOMagisterAI(
            llm_client=mock_llm_client,
            serp_api_key="test_key",
        )

        recommendations = magister._generate_combined_recommendations(
            traditional_result=mock_traditional_result,
            ai_result=mock_ai_result,
        )

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert len(recommendations) <= 10  # Max 10

        # Check structure
        for rec in recommendations:
            assert "source" in rec
            assert rec["source"] in ["traditional", "ai"]
            assert "priority" in rec
            assert "category" in rec
            assert "issue" in rec
            assert "action" in rec

        # Check that high priority comes first
        priorities = [rec["priority"] for rec in recommendations]
        assert priorities[0] == "high"

        await magister.close()

    async def test_timeout_handling(self, mock_llm_client, mock_seo_analyzer):
        """Test timeout handling."""
        magister = SEOMagisterAI(
            llm_client=mock_llm_client,
            serp_api_key="test_key",
            timeout=1,  # 1 second timeout
        )

        # Mock parent to timeout
        async def slow_analysis(*args, **kwargs):
            import asyncio
            await asyncio.sleep(2)
            return {}

        with patch.object(
            SEOMagisterAI.__bases__[0],
            "coordinate_analysis",
            new_callable=AsyncMock,
            side_effect=slow_analysis,
        ):
            result = await magister.coordinate_analysis(
                url="https://example.com",
                include_ai=False,
            )

            assert result["status"] == "error"
            assert "timeout" in result["error"].lower()

        await magister.close()

    async def test_exception_handling(self, mock_llm_client, mock_seo_analyzer):
        """Test general exception handling."""
        magister = SEOMagisterAI(
            llm_client=mock_llm_client,
            serp_api_key="test_key",
        )

        # Mock parent to raise exception
        with patch.object(
            SEOMagisterAI.__bases__[0],
            "coordinate_analysis",
            new_callable=AsyncMock,
            side_effect=Exception("Test error"),
        ):
            result = await magister.coordinate_analysis(
                url="https://example.com",
                include_ai=False,
            )

            assert result["status"] == "error"
            assert "Test error" in result["error"]

        await magister.close()
