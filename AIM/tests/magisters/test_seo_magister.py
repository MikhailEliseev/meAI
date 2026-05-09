"""Unit tests for SEO Magister."""

from unittest.mock import AsyncMock, patch
import pytest

from aim.magisters.seo_magister import SEOMagister


@pytest.fixture
def magister():
    """Create SEO Magister instance."""
    return SEOMagister(timeout=60)


@pytest.fixture
def sample_technical_result():
    """Sample technical agent result."""
    return {
        "agent": "technical-agent",
        "url": "https://example.com",
        "correlation_id": "test-123",
        "status": "success",
        "timestamp": "2026-05-09T13:00:00Z",
        "duration_seconds": 5.2,
        "results": {
            "robots_txt": {
                "exists": True,
                "allows_crawling": True,
                "content": "User-agent: *\nAllow: /"
            },
            "sitemap_xml": {
                "exists": True,
                "valid": True,
                "url_count": 50
            },
            "meta_tags": {
                "title": "Medical Clinic - Best Healthcare Services",
                "description": "Professional medical services with experienced doctors. Book your appointment today for quality healthcare."
            },
            "performance": {
                "score": 85,
                "fcp": 1.2,
                "lcp": 2.1,
                "cls": 0.05
            },
            "schema_org": {
                "count": 3,
                "types": ["Organization", "MedicalClinic", "LocalBusiness"]
            }
        }
    }


@pytest.fixture
def sample_content_result():
    """Sample content agent result."""
    return {
        "agent": "content-agent",
        "url": "https://example.com",
        "correlation_id": "test-123",
        "status": "success",
        "timestamp": "2026-05-09T13:00:00Z",
        "duration_seconds": 3.8,
        "results": {
            "headers": {
                "h1_count": 1,
                "h2_count": 5,
                "h3_count": 8,
                "broken_hierarchy": False
            },
            "keywords": {
                "total": 150,
                "top_keywords": [
                    {"keyword": "medical", "count": 15, "density": 10.0},
                    {"keyword": "clinic", "count": 12, "density": 8.0}
                ]
            },
            "readability": {
                "flesch_reading_ease": 65.5,
                "flesch_kincaid_grade": 8.2,
                "gunning_fog": 9.1
            },
            "content_quality": {
                "word_count": 850,
                "paragraph_count": 12,
                "image_count": 5,
                "alt_text_coverage": 100.0
            },
            "structure": {
                "semantic_score": 85,
                "has_main": True,
                "has_nav": True,
                "has_footer": True
            }
        }
    }


@pytest.fixture
def sample_links_result():
    """Sample links agent result."""
    return {
        "agent": "links-agent",
        "url": "https://example.com",
        "correlation_id": "test-123",
        "status": "success",
        "timestamp": "2026-05-09T13:00:00Z",
        "duration_seconds": 4.5,
        "results": {
            "internal_links": {
                "total": 25,
                "unique": 18,
                "most_linked": [
                    {"url": "https://example.com/services", "count": 5}
                ]
            },
            "external_links": {
                "total": 8,
                "unique": 7,
                "nofollow_count": 3,
                "nofollow_percentage": 37.5
            },
            "anchor_text": {
                "total": 33,
                "empty_count": 0,
                "empty_percentage": 0.0,
                "generic_count": 2,
                "generic_percentage": 6.1
            },
            "broken_links": {
                "checked": 20,
                "broken_count": 0,
                "working_count": 20,
                "broken_percentage": 0.0
            }
        }
    }


class TestSEOMagister:
    """Test SEO Magister."""

    @pytest.mark.asyncio
    async def test_coordinate_analysis_success(
        self, magister, sample_technical_result, sample_content_result, sample_links_result
    ):
        """Test successful analysis coordination."""
        # Mock all three agents
        with patch.object(magister.technical_agent, 'analyze', new_callable=AsyncMock) as mock_tech, \
             patch.object(magister.content_agent, 'analyze', new_callable=AsyncMock) as mock_content, \
             patch.object(magister.links_agent, 'analyze', new_callable=AsyncMock) as mock_links:

            mock_tech.return_value = sample_technical_result
            mock_content.return_value = sample_content_result
            mock_links.return_value = sample_links_result

            result = await magister.coordinate_analysis("https://example.com", "test-123")

        assert result["status"] == "success"
        assert result["url"] == "https://example.com"
        assert result["correlation_id"] == "test-123"
        assert "scores" in result
        assert "summary" in result
        assert "recommendations" in result
        assert "details" in result

        # Verify scores
        scores = result["scores"]
        assert "overall" in scores
        assert "technical" in scores
        assert "content" in scores
        assert "links" in scores
        assert 0 <= scores["overall"] <= 100
        assert 0 <= scores["technical"] <= 100
        assert 0 <= scores["content"] <= 100
        assert 0 <= scores["links"] <= 100

        # Verify all agents were called
        mock_tech.assert_called_once_with("https://example.com", "test-123")
        mock_content.assert_called_once_with("https://example.com", "test-123")
        mock_links.assert_called_once_with("https://example.com", "test-123")

    @pytest.mark.asyncio
    async def test_coordinate_analysis_with_agent_error(self, magister, sample_content_result, sample_links_result):
        """Test analysis when one agent fails."""
        # Mock technical agent to fail, others succeed
        with patch.object(magister.technical_agent, 'analyze', new_callable=AsyncMock) as mock_tech, \
             patch.object(magister.content_agent, 'analyze', new_callable=AsyncMock) as mock_content, \
             patch.object(magister.links_agent, 'analyze', new_callable=AsyncMock) as mock_links:

            mock_tech.side_effect = Exception("Network error")
            mock_content.return_value = sample_content_result
            mock_links.return_value = sample_links_result

            result = await magister.coordinate_analysis("https://example.com", "test-456")

        # Should still succeed with partial results
        assert result["status"] == "success"
        assert result["details"]["technical"]["status"] == "error"
        assert result["details"]["content"]["status"] == "success"
        assert result["details"]["links"]["status"] == "success"

        # Technical score should be 0
        assert result["scores"]["technical"] == 0.0
        assert result["scores"]["content"] > 0
        assert result["scores"]["links"] > 0

    @pytest.mark.asyncio
    async def test_calculate_technical_score_perfect(self, magister, sample_technical_result):
        """Test technical score calculation with perfect result."""
        score = magister._calculate_technical_score(sample_technical_result)

        # Should be high score (robots + sitemap + meta + performance + schema)
        assert score >= 80
        assert score <= 100

    @pytest.mark.asyncio
    async def test_calculate_technical_score_poor(self, magister):
        """Test technical score calculation with poor result."""
        poor_result = {
            "status": "success",
            "results": {
                "robots_txt": {"exists": False},
                "sitemap_xml": {"exists": False},
                "meta_tags": {"title": "", "description": ""},
                "performance": {"score": 20},
                "schema_org": {"count": 0}
            }
        }

        score = magister._calculate_technical_score(poor_result)

        # Should be low score
        assert score < 30

    @pytest.mark.asyncio
    async def test_calculate_content_score_perfect(self, magister, sample_content_result):
        """Test content score calculation with perfect result."""
        score = magister._calculate_content_score(sample_content_result)

        # Should be high score
        assert score >= 80
        assert score <= 100

    @pytest.mark.asyncio
    async def test_calculate_content_score_poor(self, magister):
        """Test content score calculation with poor result."""
        poor_result = {
            "status": "success",
            "results": {
                "headers": {"h1_count": 0, "broken_hierarchy": True},
                "readability": {"flesch_reading_ease": 20},
                "content_quality": {
                    "word_count": 50,
                    "image_count": 0,
                    "alt_text_coverage": 0
                },
                "structure": {"semantic_score": 20}
            }
        }

        score = magister._calculate_content_score(poor_result)

        # Should be low score
        assert score < 30

    @pytest.mark.asyncio
    async def test_calculate_links_score_perfect(self, magister, sample_links_result):
        """Test links score calculation with perfect result."""
        score = magister._calculate_links_score(sample_links_result)

        # Should be high score
        assert score >= 80
        assert score <= 100

    @pytest.mark.asyncio
    async def test_calculate_links_score_poor(self, magister):
        """Test links score calculation with poor result."""
        poor_result = {
            "status": "success",
            "results": {
                "internal_links": {"total": 2, "unique": 2},
                "external_links": {"total": 1, "nofollow_percentage": 100},
                "anchor_text": {
                    "empty_percentage": 50,
                    "generic_percentage": 80
                },
                "broken_links": {"broken_percentage": 30}
            }
        }

        score = magister._calculate_links_score(poor_result)

        # Should be low score
        assert score < 30

    @pytest.mark.asyncio
    async def test_generate_recommendations_high_scores(
        self, magister, sample_technical_result, sample_content_result, sample_links_result
    ):
        """Test recommendations with high scores (few recommendations)."""
        recommendations = magister._generate_recommendations(
            sample_technical_result,
            sample_content_result,
            sample_links_result,
            85.0, 85.0, 85.0
        )

        # Should have few or no recommendations
        assert len(recommendations) <= 3

    @pytest.mark.asyncio
    async def test_generate_recommendations_low_scores(self, magister):
        """Test recommendations with low scores (many recommendations)."""
        poor_tech = {
            "status": "success",
            "results": {
                "robots_txt": {"exists": False},
                "sitemap_xml": {"exists": False},
                "performance": {"score": 30},
                "schema_org": {"count": 0}
            }
        }

        poor_content = {
            "status": "success",
            "results": {
                "headers": {"h1_count": 0},
                "content_quality": {"word_count": 100, "alt_text_coverage": 20},
                "readability": {"flesch_reading_ease": 30}
            }
        }

        poor_links = {
            "status": "success",
            "results": {
                "internal_links": {"total": 3},
                "anchor_text": {"generic_percentage": 50},
                "broken_links": {"broken_count": 5}
            }
        }

        recommendations = magister._generate_recommendations(
            poor_tech, poor_content, poor_links,
            30.0, 30.0, 30.0
        )

        # Should have many recommendations
        assert len(recommendations) >= 5

        # Should have high priority items
        high_priority = [r for r in recommendations if r["priority"] == "high"]
        assert len(high_priority) > 0

    @pytest.mark.asyncio
    async def test_generate_summary(self, magister):
        """Test summary generation."""
        summary = magister._generate_summary(75.0, 80.0, 70.0, 75.0)

        assert "Good" in summary  # 75 is "Good" rating
        assert "80.0" in summary or "80" in summary  # Technical score
        assert "70.0" in summary or "70" in summary  # Content score

    @pytest.mark.asyncio
    async def test_weighted_scoring(
        self, magister, sample_technical_result, sample_content_result, sample_links_result
    ):
        """Test that weighted scoring is applied correctly (40% tech, 30% content, 30% links)."""
        with patch.object(magister.technical_agent, 'analyze', new_callable=AsyncMock) as mock_tech, \
             patch.object(magister.content_agent, 'analyze', new_callable=AsyncMock) as mock_content, \
             patch.object(magister.links_agent, 'analyze', new_callable=AsyncMock) as mock_links:

            mock_tech.return_value = sample_technical_result
            mock_content.return_value = sample_content_result
            mock_links.return_value = sample_links_result

            result = await magister.coordinate_analysis("https://example.com")

        scores = result["scores"]

        # Verify weighted calculation
        expected_overall = (
            scores["technical"] * 0.4 +
            scores["content"] * 0.3 +
            scores["links"] * 0.3
        )

        assert abs(scores["overall"] - expected_overall) < 0.1

    @pytest.mark.asyncio
    async def test_correlation_id_generation(self, magister, sample_technical_result, sample_content_result, sample_links_result):
        """Test that correlation ID is generated if not provided."""
        with patch.object(magister.technical_agent, 'analyze', new_callable=AsyncMock) as mock_tech, \
             patch.object(magister.content_agent, 'analyze', new_callable=AsyncMock) as mock_content, \
             patch.object(magister.links_agent, 'analyze', new_callable=AsyncMock) as mock_links:

            mock_tech.return_value = sample_technical_result
            mock_content.return_value = sample_content_result
            mock_links.return_value = sample_links_result

            result = await magister.coordinate_analysis("https://example.com")

        # Should have auto-generated correlation ID
        assert "correlation_id" in result
        assert result["correlation_id"].startswith("seo-analysis-")
