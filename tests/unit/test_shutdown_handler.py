"""Tests for Shutdown Handler"""

import pytest
import asyncio
from meai.safety.shutdown_handler import ShutdownHandler


@pytest.mark.asyncio
async def test_register_cleanup():
    """Test registering cleanup callback"""
    handler = ShutdownHandler()

    cleanup_called = []

    async def cleanup():
        cleanup_called.append(True)

    handler.register_cleanup(cleanup)

    # Trigger shutdown
    await handler.shutdown()

    assert len(cleanup_called) == 1


@pytest.mark.asyncio
async def test_multiple_cleanup_callbacks():
    """Test executing multiple cleanup callbacks in order"""
    handler = ShutdownHandler()

    order = []

    async def cleanup1():
        order.append(1)

    async def cleanup2():
        order.append(2)

    async def cleanup3():
        order.append(3)

    handler.register_cleanup(cleanup1)
    handler.register_cleanup(cleanup2)
    handler.register_cleanup(cleanup3)

    await handler.shutdown()

    assert order == [1, 2, 3]


@pytest.mark.asyncio
async def test_cleanup_error_handling():
    """Test continuing cleanup even if one callback fails"""
    handler = ShutdownHandler()

    executed = []

    async def cleanup1():
        executed.append(1)

    async def cleanup2():
        raise RuntimeError("Cleanup failed")

    async def cleanup3():
        executed.append(3)

    handler.register_cleanup(cleanup1)
    handler.register_cleanup(cleanup2)
    handler.register_cleanup(cleanup3)

    await handler.shutdown()

    # Should execute all callbacks despite error
    assert executed == [1, 3]


@pytest.mark.asyncio
async def test_shutdown_idempotent():
    """Test shutdown can be called multiple times safely"""
    handler = ShutdownHandler()

    call_count = []

    async def cleanup():
        call_count.append(1)

    handler.register_cleanup(cleanup)

    await handler.shutdown()
    await handler.shutdown()
    await handler.shutdown()

    # Cleanup should only run once
    assert len(call_count) == 1


@pytest.mark.asyncio
async def test_wait_for_shutdown():
    """Test waiting for shutdown signal"""
    handler = ShutdownHandler()

    # Start waiting in background
    wait_task = asyncio.create_task(handler.wait_for_shutdown())

    # Give it time to start waiting
    await asyncio.sleep(0.1)

    # Should not be done yet
    assert not wait_task.done()

    # Trigger shutdown
    await handler.shutdown()

    # Now should be done
    await asyncio.wait_for(wait_task, timeout=1.0)
    assert wait_task.done()


@pytest.mark.asyncio
async def test_is_shutdown_requested():
    """Test checking if shutdown was requested"""
    handler = ShutdownHandler()

    assert not handler.is_shutdown_requested()

    await handler.shutdown()

    assert handler.is_shutdown_requested()


@pytest.mark.asyncio
async def test_shutdown_event():
    """Test shutdown event is set"""
    handler = ShutdownHandler()

    assert not handler.shutdown_event.is_set()

    await handler.shutdown()

    assert handler.shutdown_event.is_set()


@pytest.mark.asyncio
async def test_is_shutting_down_flag():
    """Test is_shutting_down flag prevents duplicate execution"""
    handler = ShutdownHandler()

    call_count = []

    async def cleanup():
        call_count.append(1)
        # Simulate slow cleanup
        await asyncio.sleep(0.1)

    handler.register_cleanup(cleanup)

    # Start two shutdowns concurrently
    await asyncio.gather(
        handler.shutdown(),
        handler.shutdown(),
    )

    # Should only execute once
    assert len(call_count) == 1
