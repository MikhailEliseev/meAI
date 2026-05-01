"""Tests for Health Checker"""

import pytest
from meai.monitoring.health import HealthChecker


@pytest.mark.asyncio
async def test_health_check():
    """Test basic health check"""
    checker = HealthChecker()

    # Register component
    async def db_health():
        return {"status": "healthy"}

    checker.register_component("database", db_health)

    # Check health
    health = await checker.check_health()
    assert health["status"] == "healthy"
    assert "database" in health["components"]
    assert health["components"]["database"]["status"] == "healthy"


@pytest.mark.asyncio
async def test_unhealthy_component():
    """Test detecting unhealthy component"""
    checker = HealthChecker()

    async def failing_health():
        return {"status": "unhealthy", "error": "Connection failed"}

    checker.register_component("database", failing_health)

    health = await checker.check_health()
    assert health["status"] == "unhealthy"
    assert health["components"]["database"]["status"] == "unhealthy"


@pytest.mark.asyncio
async def test_component_exception():
    """Test handling component check exception"""
    checker = HealthChecker()

    async def broken_health():
        raise RuntimeError("Check failed")

    checker.register_component("broken", broken_health)

    health = await checker.check_health()
    assert health["status"] == "unhealthy"
    assert "error" in health["components"]["broken"]


@pytest.mark.asyncio
async def test_check_specific_component():
    """Test checking specific component health"""
    checker = HealthChecker()

    async def db_health():
        return {"status": "healthy"}

    checker.register_component("database", db_health)

    result = await checker.check_component("database")
    assert result["status"] == "healthy"


@pytest.mark.asyncio
async def test_multiple_components():
    """Test checking multiple components"""
    checker = HealthChecker()

    async def db_health():
        return {"status": "healthy"}

    async def cache_health():
        return {"status": "healthy"}

    checker.register_component("database", db_health)
    checker.register_component("cache", cache_health)

    health = await checker.check_health()
    assert health["status"] == "healthy"
    assert len(health["components"]) == 2


@pytest.mark.asyncio
async def test_uptime_tracking():
    """Test uptime tracking"""
    checker = HealthChecker()

    health = await checker.check_health()
    assert "uptime_seconds" in health
    assert health["uptime_seconds"] >= 0


@pytest.mark.asyncio
async def test_timestamp_in_health():
    """Test timestamp is included in health check"""
    checker = HealthChecker()

    health = await checker.check_health()
    assert "timestamp" in health


@pytest.mark.asyncio
async def test_check_nonexistent_component():
    """Test checking non-existent component"""
    checker = HealthChecker()

    result = await checker.check_component("nonexistent")
    assert result["status"] == "unknown"
    assert "error" in result
