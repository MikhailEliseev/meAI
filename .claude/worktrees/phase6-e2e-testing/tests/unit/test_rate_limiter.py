"""Tests for Rate Limiter"""

import pytest
import asyncio
from datetime import timedelta
from meai.monitoring.rate_limiter import RateLimiter


@pytest.mark.asyncio
async def test_acquire_within_limit():
    """Test acquiring tokens within rate limit"""
    limiter = RateLimiter(max_requests=10, window=timedelta(seconds=1))

    # Should succeed
    assert await limiter.acquire() is True
    assert await limiter.acquire() is True


@pytest.mark.asyncio
async def test_rate_limit_exceeded():
    """Test rate limit exceeded"""
    limiter = RateLimiter(max_requests=2, window=timedelta(seconds=10))

    # First two should succeed
    assert await limiter.acquire() is True
    assert await limiter.acquire() is True

    # Third should fail
    assert await limiter.acquire() is False


@pytest.mark.asyncio
async def test_window_reset():
    """Test rate limit resets after window"""
    limiter = RateLimiter(max_requests=2, window=timedelta(seconds=0.5))

    # Use up limit
    assert await limiter.acquire() is True
    assert await limiter.acquire() is True
    assert await limiter.acquire() is False

    # Wait for window to reset
    await asyncio.sleep(0.6)

    # Should work again
    assert await limiter.acquire() is True


@pytest.mark.asyncio
async def test_get_remaining():
    """Test getting remaining requests"""
    limiter = RateLimiter(max_requests=5, window=timedelta(seconds=1))

    assert limiter.get_remaining() == 5

    await limiter.acquire()
    assert limiter.get_remaining() == 4

    await limiter.acquire()
    assert limiter.get_remaining() == 3


@pytest.mark.asyncio
async def test_get_wait_time():
    """Test getting wait time until next available slot"""
    limiter = RateLimiter(max_requests=2, window=timedelta(seconds=1))

    # Use up limit
    await limiter.acquire()
    await limiter.acquire()

    # Should have wait time
    wait_time = limiter.get_wait_time()
    assert wait_time > 0
    assert wait_time <= 1.0


@pytest.mark.asyncio
async def test_reset():
    """Test resetting rate limiter"""
    limiter = RateLimiter(max_requests=2, window=timedelta(seconds=10))

    # Use up limit
    await limiter.acquire()
    await limiter.acquire()
    assert await limiter.acquire() is False

    # Reset
    limiter.reset()

    # Should work again
    assert await limiter.acquire() is True


@pytest.mark.asyncio
async def test_get_stats():
    """Test getting rate limiter statistics"""
    limiter = RateLimiter(max_requests=5, window=timedelta(seconds=1))

    await limiter.acquire()
    await limiter.acquire()

    stats = limiter.get_stats()
    assert stats["total_requests"] == 2
    assert stats["remaining"] == 3
    assert stats["max_requests"] == 5


@pytest.mark.asyncio
async def test_concurrent_requests():
    """Test concurrent request handling"""
    limiter = RateLimiter(max_requests=5, window=timedelta(seconds=1))

    # Make 10 concurrent requests
    results = await asyncio.gather(*[limiter.acquire() for _ in range(10)])

    # Only 5 should succeed
    assert sum(results) == 5
