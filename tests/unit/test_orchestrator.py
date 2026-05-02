"""Tests for Orchestrator"""

import pytest
import asyncio
from meai.core.orchestrator import Orchestrator


@pytest.mark.asyncio
async def test_orchestrator_coordinates_components():
    """Test orchestrator coordinates multiple components"""
    orchestrator = Orchestrator()

    # Register components
    async def db_health():
        return {"status": "healthy"}

    async def vault_health():
        return {"status": "healthy"}

    orchestrator.register_component("database", db_health)
    orchestrator.register_component("vault", vault_health)

    # Check all components
    status = await orchestrator.check_all_components()

    assert status["database"]["status"] == "healthy"
    assert status["vault"]["status"] == "healthy"


@pytest.mark.asyncio
async def test_orchestrator_handles_component_failure():
    """Test orchestrator handles component failures gracefully"""
    orchestrator = Orchestrator()

    async def failing_component():
        raise RuntimeError("Component failed")

    async def healthy_component():
        return {"status": "healthy"}

    orchestrator.register_component("failing", failing_component)
    orchestrator.register_component("healthy", healthy_component)

    status = await orchestrator.check_all_components()

    assert status["failing"]["status"] == "error"
    assert "Component failed" in status["failing"]["error"]
    assert status["healthy"]["status"] == "healthy"


@pytest.mark.asyncio
async def test_orchestrator_executes_workflow():
    """Test orchestrator executes workflow steps sequentially"""
    orchestrator = Orchestrator()

    results = []

    async def step1():
        results.append(1)
        return "step1"

    async def step2():
        results.append(2)
        return "step2"

    async def step3():
        results.append(3)
        return "step3"

    workflow_results = await orchestrator.execute_workflow([step1, step2, step3])

    assert results == [1, 2, 3]
    assert workflow_results == ["step1", "step2", "step3"]


@pytest.mark.asyncio
async def test_orchestrator_workflow_stops_on_error():
    """Test orchestrator stops workflow on error"""
    orchestrator = Orchestrator()

    results = []

    async def step1():
        results.append(1)
        return "step1"

    async def failing_step():
        results.append(2)
        raise RuntimeError("Step failed")

    async def step3():
        results.append(3)
        return "step3"

    with pytest.raises(RuntimeError, match="Step failed"):
        await orchestrator.execute_workflow([step1, failing_step, step3])

    # Only first two steps should execute
    assert results == [1, 2]


@pytest.mark.asyncio
async def test_orchestrator_executes_parallel():
    """Test orchestrator executes operations in parallel"""
    orchestrator = Orchestrator()

    async def operation1():
        await asyncio.sleep(0.1)
        return "op1"

    async def operation2():
        await asyncio.sleep(0.1)
        return "op2"

    async def operation3():
        await asyncio.sleep(0.1)
        return "op3"

    import time
    start = time.time()
    results = await orchestrator.execute_parallel([operation1, operation2, operation3])
    duration = time.time() - start

    # Should complete in ~0.1s (parallel), not ~0.3s (sequential)
    assert duration < 0.2
    assert results == ["op1", "op2", "op3"]


@pytest.mark.asyncio
async def test_orchestrator_parallel_with_exceptions():
    """Test orchestrator handles exceptions in parallel execution"""
    orchestrator = Orchestrator()

    async def success_op():
        return "success"

    async def failing_op():
        raise ValueError("Operation failed")

    results = await orchestrator.execute_parallel([success_op, failing_op])

    assert results[0] == "success"
    assert isinstance(results[1], ValueError)
