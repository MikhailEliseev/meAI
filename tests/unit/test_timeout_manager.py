"""Tests for Timeout Manager"""

import pytest
import asyncio
from meai.safety.timeout_manager import TimeoutManager


@pytest.mark.asyncio
async def test_operation_timeout():
    """Test operation timeout"""
    manager = TimeoutManager(default_timeout=1.0)

    async def slow_operation():
        await asyncio.sleep(2.0)
        return "done"

    # Should timeout
    with pytest.raises(asyncio.TimeoutError):
        await manager.run_with_timeout(slow_operation())


@pytest.mark.asyncio
async def test_operation_completes_within_timeout():
    """Test operation completes successfully within timeout"""
    manager = TimeoutManager(default_timeout=2.0)

    async def fast_operation():
        await asyncio.sleep(0.1)
        return "done"

    result = await manager.run_with_timeout(fast_operation())
    assert result == "done"


@pytest.mark.asyncio
async def test_custom_timeout():
    """Test custom timeout overrides default"""
    manager = TimeoutManager(default_timeout=5.0)

    async def slow_operation():
        await asyncio.sleep(2.0)
        return "done"

    # Should timeout with custom 1 second timeout
    with pytest.raises(asyncio.TimeoutError):
        await manager.run_with_timeout(slow_operation(), timeout=1.0)


@pytest.mark.asyncio
async def test_cancel_operation():
    """Test canceling a tracked operation"""
    manager = TimeoutManager()

    async def long_operation():
        await asyncio.sleep(10.0)
        return "done"

    # Start operation in background
    task = asyncio.create_task(
        manager.run_with_timeout_tracked(
            long_operation(),
            operation_id="op-1",
        )
    )

    # Wait a bit
    await asyncio.sleep(0.1)

    # Cancel it
    await manager.cancel_operation("op-1")

    # Task should be cancelled
    with pytest.raises(asyncio.CancelledError):
        await task


@pytest.mark.asyncio
async def test_cancel_all_operations():
    """Test canceling all active operations"""
    manager = TimeoutManager()

    async def long_operation():
        await asyncio.sleep(10.0)
        return "done"

    # Start multiple operations
    tasks = [
        asyncio.create_task(
            manager.run_with_timeout_tracked(long_operation(), f"op-{i}")
        )
        for i in range(3)
    ]

    await asyncio.sleep(0.1)

    # Cancel all
    await manager.cancel_all()

    # All tasks should be cancelled
    for task in tasks:
        with pytest.raises(asyncio.CancelledError):
            await task


@pytest.mark.asyncio
async def test_get_active_operations():
    """Test getting list of active operations"""
    manager = TimeoutManager()

    async def long_operation():
        await asyncio.sleep(10.0)

    # Start operations
    tasks = [
        asyncio.create_task(
            manager.run_with_timeout_tracked(long_operation(), f"op-{i}")
        )
        for i in range(3)
    ]

    await asyncio.sleep(0.1)

    active = manager.get_active_operations()
    assert len(active) == 3
    assert "op-0" in active
    assert "op-1" in active
    assert "op-2" in active

    # Cleanup
    await manager.cancel_all()


@pytest.mark.asyncio
async def test_operation_with_id():
    """Test operation tracking with ID"""
    manager = TimeoutManager(default_timeout=2.0)

    async def fast_operation():
        await asyncio.sleep(0.1)
        return "done"

    result = await manager.run_with_timeout(
        fast_operation(),
        operation_id="test-op"
    )
    assert result == "done"


@pytest.mark.asyncio
async def test_cancel_nonexistent_operation():
    """Test canceling non-existent operation doesn't raise error"""
    manager = TimeoutManager()

    # Should not raise error
    await manager.cancel_operation("nonexistent")
