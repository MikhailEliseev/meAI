"""Unit tests for API Clients - Simplified Version

Tests focus on successful scenarios with mock data.
VCR tests are separate and require real API keys for recording.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from src.aim.subagents.api_clients.base import TokenBucketRateLimiter
from src.aim.subagents.api_clients.semrush import SEMrushClient
from src.aim.subagents.api_clients.ahrefs import AhrefsClient


class TestTokenBucketRateLimiter:
    """Test rate limiter implementation"""

    @pytest.mark.asyncio
    async def test_acquire_single_token(self):
        """Should acquire single token immediately"""
        limiter = TokenBucketRateLimiter(capacity=10, refill_rate=1.0)
        await limiter.acquire(1)
        assert limiter.tokens < 10

    @pytest.mark.asyncio
    async def test_acquire_multiple_tokens(self):
        """Should acquire multiple tokens"""
        limiter = TokenBucketRateLimiter(capacity=10, refill_rate=1.0)
        await limiter.acquire(5)
        assert limiter.tokens == pytest.approx(5.0, abs=0.1)

    @pytest.mark.asyncio
    async def test_refill_over_time(self):
        """Should refill tokens over time"""
        import asyncio
        limiter = TokenBucketRateLimiter(capacity=10, refill_rate=10.0)
        await limiter.acquire(10)
        await asyncio.sleep(0.5)
        await limiter.acquire(1)
        assert limiter.tokens >= 3.0

    @pytest.mark.asyncio
    async def test_blocks_when_empty(self):
        """Should block when no tokens available"""
        import asyncio
        import time
        limiter = TokenBucketRateLimiter(capacity=1, refill_rate=2.0)
        await limiter.acquire(1)
        start = time.monotonic()
        await limiter.acquire(1)
        elapsed = time.monotonic() - start
        assert elapsed >= 0.4


class TestSEMrushClient:
    """Test SEMrush API client with mocks"""

    @pytest.mark.asyncio
    async def test_expand_keywords_success(self):
        """Should expand keywords successfully with mock data"""
        client = SEMrushClient(
            api_key="test_key",
            rate_limit_capacity=10,
            rate_limit_refill=1.0,
        )

        # Mock successful response (must match SEMrushKeywordData schema)
        mock_data = [
            {
                "keyword": "dental implants",
                "volume": 10000,
                "cpc": 15.50,
                "competition": 0.85,
                "difficulty": 65,
                "intent": "commercial",
            },
            {
                "keyword": "dental implants cost",
                "volume": 5000,
                "cpc": 12.30,
                "competition": 0.75,
                "difficulty": 58,
                "intent": "commercial",
            },
        ]

        async def mock_fetch(*args, **kwargs):
            return mock_data

        client._fetch_keyword_page = mock_fetch

        keywords = await client.expand_keywords(
            seed_keyword="dental implants",
            max_keywords=10,
            min_volume=100,
        )

        assert len(keywords) == 2
        assert all(k["volume"] >= 100 for k in keywords)
        assert all(k["keyword"] for k in keywords)

        await client.close()

    @pytest.mark.asyncio
    async def test_budget_guard(self):
        """Should respect budget limits"""
        client = SEMrushClient(
            api_key="test_key",
            rate_limit_capacity=10,
            rate_limit_refill=1.0,
        )

        call_count = 0

        async def mock_fetch(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return [{"keyword": f"kw{i}", "volume": 1000, "cpc": 1.0, "competition": 0.5, "difficulty": 50, "intent": "informational"}
                    for i in range(100)]

        client._fetch_keyword_page = mock_fetch

        # Request many keywords with small budget
        keywords = await client.expand_keywords(
            seed_keyword="test",
            max_keywords=1000,
            max_cost_usd=0.03,  # Only 3 calls allowed
        )

        # Should stop at budget limit
        assert call_count <= 3
        assert len(keywords) <= 300

        await client.close()

    @pytest.mark.asyncio
    async def test_empty_results_handling(self):
        """Should handle empty results gracefully"""
        client = SEMrushClient(
            api_key="test_key",
            rate_limit_capacity=10,
            rate_limit_refill=1.0,
        )

        async def mock_fetch(*args, **kwargs):
            return []

        async def mock_suggestions(*args, **kwargs):
            return ["suggestion1", "suggestion2"]

        client._fetch_keyword_page = mock_fetch
        client._get_keyword_suggestions = mock_suggestions

        # Should raise ValueError with suggestions
        with pytest.raises(ValueError, match="No keywords found"):
            await client.expand_keywords(
                seed_keyword="xyzabc123",
                max_keywords=10,
            )

        await client.close()


class TestAhrefsClient:
    """Test Ahrefs API client with mocks"""

    @pytest.mark.asyncio
    async def test_expand_keywords_success(self):
        """Should expand keywords successfully with mock data"""
        client = AhrefsClient(
            api_key="test_key",
            rate_limit_capacity=10,
            rate_limit_refill=1.0,
        )

        # Mock successful response
        mock_data = {
            "keywords": [
                {
                    "keyword": "dental implants",
                    "volume": 10000,
                    "difficulty": 45,
                    "cpc": 15.50,
                    "parent_topic": "dental procedures",
                },
                {
                    "keyword": "dental implants cost",
                    "volume": 5000,
                    "difficulty": 38,
                    "cpc": 12.30,
                    "parent_topic": "dental procedures",
                },
            ]
        }

        async def mock_request(*args, **kwargs):
            return mock_data

        client._make_request = mock_request

        keywords = await client.expand_keywords(
            seed_keyword="dental implants",
            max_keywords=10,
            min_volume=100,
        )

        assert len(keywords) == 2
        assert all(k["volume"] >= 100 for k in keywords)
        assert all(0 <= k["difficulty"] <= 100 for k in keywords)

        await client.close()
