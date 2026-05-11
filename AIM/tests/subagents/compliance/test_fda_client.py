"""
Tests for FDA API Client

Tests openFDA integration, caching, rate limiting, and graceful degradation.
"""

import pytest
import pytest_asyncio
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from AIM.src.aim.subagents.compliance.fda_client import FDAClient
from AIM.src.aim.subagents.schemas.compliance import FDAEnforcementRecord


@pytest_asyncio.fixture
async def fda_client():
    """Create FDA client instance"""
    client = FDAClient(cache_ttl=60, rate_limit_per_minute=240)
    yield client
    await client.close()


class TestFDAClientInitialization:
    """Test FDA client initialization"""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test that client initializes correctly"""
        client = FDAClient()
        assert client.base_url == "https://api.fda.gov"
        assert client.cache_ttl == 86400  # 24 hours
        assert client.rate_limit_per_minute == 240
        await client.close()

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_custom_settings(self):
        """Test custom cache and rate limit settings"""
        client = FDAClient(cache_ttl=3600, rate_limit_per_minute=120)
        assert client.cache_ttl == 3600
        assert client.rate_limit_per_minute == 120
        await client.close()


class TestFDAEnforcementSearch:
    """Test FDA enforcement search functionality"""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_search_returns_list(self, fda_client):
        """Test that search returns a list"""
        # Mock the HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "recall_number": "F-1234-2026",
                    "product_description": "Test product",
                    "reason_for_recall": "Unapproved drug claims",
                    "classification": "Class II",
                    "recall_initiation_date": "2026-03-15",
                }
            ]
        }

        with patch.object(fda_client.client, 'get', return_value=mock_response) as mock_get:
            mock_get.return_value = mock_response

            results = await fda_client.search_enforcement("diabetes cure")

            assert isinstance(results, list)
            assert len(results) > 0
            assert isinstance(results[0], FDAEnforcementRecord)

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_search_no_results_returns_empty_list(self, fda_client):
        """Test that no results returns empty list"""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch.object(fda_client.client, 'get', return_value=mock_response):
            results = await fda_client.search_enforcement("nonexistent keyword")

            assert results == []

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_search_parses_enforcement_records(self, fda_client):
        """Test that enforcement records are parsed correctly"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "recall_number": "F-5678-2026",
                    "product_description": "Supplement claiming to cure cancer",
                    "reason_for_recall": "Unapproved new drug",
                    "classification": "Class I",
                    "recall_initiation_date": "2026-04-20",
                }
            ]
        }

        with patch.object(fda_client.client, 'get', return_value=mock_response):
            results = await fda_client.search_enforcement("cancer cure")

            assert len(results) == 1
            record = results[0]
            assert record.recall_number == "F-5678-2026"
            assert record.classification == "Class I"
            assert "cancer" in record.product_description.lower()


class TestFDACaching:
    """Test FDA client caching"""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_cache_hit_avoids_api_call(self, fda_client):
        """Test that cached results avoid API calls"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}

        with patch.object(fda_client.client, 'get', return_value=mock_response) as mock_get:
            # First call - should hit API
            await fda_client.search_enforcement("test keyword")
            assert mock_get.call_count == 1

            # Second call - should use cache
            await fda_client.search_enforcement("test keyword")
            assert mock_get.call_count == 1  # Still 1, no new call

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_different_keywords_not_cached_together(self, fda_client):
        """Test that different keywords have separate cache entries"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}

        with patch.object(fda_client.client, 'get', return_value=mock_response) as mock_get:
            await fda_client.search_enforcement("keyword1")
            await fda_client.search_enforcement("keyword2")

            assert mock_get.call_count == 2  # Two different API calls


class TestFDARateLimiting:
    """Test FDA client rate limiting"""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_rate_limiting_delays_requests(self, fda_client):
        """Test that rate limiting adds delays between requests"""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch.object(fda_client.client, 'get', return_value=mock_response):
            import time
            start = time.time()

            # Make 3 rapid requests
            await fda_client.search_enforcement("test1")
            await fda_client.search_enforcement("test2")
            await fda_client.search_enforcement("test3")

            duration = time.time() - start

            # With 240 req/min = 4 req/sec = 0.25s between requests
            # 3 requests should take at least 0.5s (2 intervals)
            assert duration >= 0.4  # Allow some tolerance


class TestFDAGracefulDegradation:
    """Test graceful degradation on errors"""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_timeout_returns_none(self, fda_client):
        """Test that timeout returns None for graceful degradation"""
        import httpx

        with patch.object(fda_client.client, 'get', side_effect=httpx.TimeoutException("Timeout")):
            result = await fda_client.search_enforcement("test keyword")

            assert result is None

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_http_error_returns_none(self, fda_client):
        """Test that HTTP errors return None"""
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 500
        error = httpx.HTTPStatusError("Server error", request=MagicMock(), response=mock_response)

        with patch.object(fda_client.client, 'get', side_effect=error):
            result = await fda_client.search_enforcement("test keyword")

            assert result is None

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_unexpected_error_returns_none(self, fda_client):
        """Test that unexpected errors return None"""
        with patch.object(fda_client.client, 'get', side_effect=Exception("Unexpected error")):
            result = await fda_client.search_enforcement("test keyword")

            assert result is None


class TestFDAQueryConstruction:
    """Test FDA API query construction"""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_search_query_format(self, fda_client):
        """Test that search query is formatted correctly"""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch.object(fda_client.client, 'get', return_value=mock_response) as mock_get:
            await fda_client.search_enforcement("diabetes cure", limit=5)

            # Check that get was called with correct params
            call_args = mock_get.call_args
            assert call_args is not None

            params = call_args[1].get('params', {})
            assert 'search' in params
            assert 'diabetes cure' in params['search']
            assert params['limit'] == 5


class TestFDAClientCleanup:
    """Test client cleanup"""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_client_closes_properly(self):
        """Test that client closes HTTP connection"""
        client = FDAClient()

        # Mock the aclose method
        with patch.object(client.client, 'aclose', new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
