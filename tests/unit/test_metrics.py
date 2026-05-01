"""Tests for Metrics Collector"""

import pytest
from datetime import datetime, timedelta, timezone
from meai.monitoring.metrics import MetricsCollector
from meai.storage.database import Database


@pytest.mark.asyncio
async def test_record_metric():
    """Test recording metrics"""
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.connect()

    collector = MetricsCollector(db)

    await collector.record_counter("api_calls", 1, {"endpoint": "/health"})
    await collector.record_gauge("memory_usage", 1024.5, {"unit": "MB"})

    # Query metrics
    metrics = await collector.get_metrics("api_calls")
    assert len(metrics) == 1

    await db.disconnect()


@pytest.mark.asyncio
async def test_get_metric_summary():
    """Test getting metric summary statistics"""
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.connect()

    collector = MetricsCollector(db)

    # Record multiple values
    await collector.record_gauge("cpu_usage", 10.0)
    await collector.record_gauge("cpu_usage", 20.0)
    await collector.record_gauge("cpu_usage", 30.0)

    # Get summary
    summary = await collector.get_metric_summary("cpu_usage")
    assert summary["count"] == 3
    assert summary["avg"] == 20.0
    assert summary["min"] == 10.0
    assert summary["max"] == 30.0

    await db.disconnect()


@pytest.mark.asyncio
async def test_cleanup_old_metrics():
    """Test cleaning up old metrics"""
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.connect()

    collector = MetricsCollector(db)

    # Record metric
    await collector.record_counter("test", 1)

    # Manually set old timestamp
    async with db.session() as session:
        from sqlalchemy import update, text
        from meai.storage.models import Metric
        stmt = update(Metric).values(
            timestamp=datetime.now(timezone.utc) - timedelta(days=60)
        )
        await session.execute(stmt)

    # Cleanup
    deleted = await collector.cleanup_old_metrics(older_than=timedelta(days=30))
    assert deleted == 1

    await db.disconnect()


@pytest.mark.asyncio
async def test_record_counter():
    """Test recording counter metric"""
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.connect()

    collector = MetricsCollector(db)

    await collector.record_counter("requests", 1)
    await collector.record_counter("requests", 1)
    await collector.record_counter("requests", 1)

    metrics = await collector.get_metrics("requests")
    assert len(metrics) == 3

    await db.disconnect()


@pytest.mark.asyncio
async def test_record_gauge():
    """Test recording gauge metric"""
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.connect()

    collector = MetricsCollector(db)

    await collector.record_gauge("temperature", 25.5)
    await collector.record_gauge("temperature", 26.0)

    metrics = await collector.get_metrics("temperature")
    assert len(metrics) == 2

    await db.disconnect()


@pytest.mark.asyncio
async def test_record_histogram():
    """Test recording histogram metric"""
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.connect()

    collector = MetricsCollector(db)

    await collector.record_histogram("response_time", 0.5)
    await collector.record_histogram("response_time", 1.2)
    await collector.record_histogram("response_time", 0.8)

    metrics = await collector.get_metrics("response_time")
    assert len(metrics) == 3

    await db.disconnect()


@pytest.mark.asyncio
async def test_metrics_with_labels():
    """Test recording metrics with labels"""
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.connect()

    collector = MetricsCollector(db)

    await collector.record_counter("requests", 1, {"method": "GET", "path": "/api"})
    await collector.record_counter("requests", 1, {"method": "POST", "path": "/api"})

    metrics = await collector.get_metrics("requests")
    assert len(metrics) == 2

    await db.disconnect()


@pytest.mark.asyncio
async def test_get_metrics_with_limit():
    """Test getting metrics with limit"""
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.connect()

    collector = MetricsCollector(db)

    # Record 5 metrics
    for i in range(5):
        await collector.record_counter("test", 1)

    # Get only 3
    metrics = await collector.get_metrics("test", limit=3)
    assert len(metrics) == 3

    await db.disconnect()
