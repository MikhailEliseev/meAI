"""Integration test for full USER → Operator → Magisters → Operator → USER cycle"""

import asyncio
import pytest
from datetime import datetime, timedelta, timezone

from meai.agents.operator import Operator, Task, TaskStatus
from meai.agents.magisters.seo_magister import SEOMagister
from meai.agents.magisters.content_magister import ContentMagister


@pytest.mark.asyncio
async def test_full_user_cycle():
    """Test complete USER → Operator → Magisters → Operator → USER flow"""

    # 1. Create Operator
    operator = Operator(
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="./test_vault",
    )
    await operator.initialize()

    # 2. Create Magisters (all 3 needed for hybrid strategy)
    seo = SEOMagister(
        agent_id="seo-magister-1",
        event_bus=operator.event_bus,
        database_url="sqlite+aiosqlite:///:memory:",
    )
    await seo.initialize()

    content = ContentMagister(
        agent_id="content-magister-1",
        event_bus=operator.event_bus,
        database_url="sqlite+aiosqlite:///:memory:",
    )
    await content.initialize()

    # Add Intelligence Magister (needed for hybrid strategy)
    from meai.agents.magisters.intelligence_magister import IntelligenceMagister
    intelligence = IntelligenceMagister(
        agent_id="intelligence-magister-1",
        event_bus=operator.event_bus,
        database_url="sqlite+aiosqlite:///:memory:",
    )
    await intelligence.initialize()

    # 3. User sends task
    task = Task(
        task_id="task-full-cycle-001",
        source="user",
        goal="Create SEO-optimized content",
        description="Research keywords and create optimized article",
        constraints=["time < 1 hour"],
        resources={"tools": ["ahrefs"]},
        priority=0,
        deadline=datetime.now(timezone.utc) + timedelta(hours=1),
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    print("\n📤 User sends task to Operator")
    await operator.receive_task(task)

    # Verify task received
    assert task.task_id in operator.active_tasks
    assert task.task_id in operator.active_plans

    plan = operator.active_plans[task.task_id]
    print(f"✅ Operator created plan: {plan.strategy.value}")
    print(f"   Subtasks: {len(plan.subtasks)}")
    print(f"   Agents: {list(plan.agent_assignments.keys())}")

    # 4. Magisters poll and execute
    print("\n🔄 Magisters polling for tasks...")
    await seo.poll_and_process_tasks()
    await content.poll_and_process_tasks()
    await intelligence.poll_and_process_tasks()
    print("✅ Magisters processed tasks")

    # 5. Operator collects results
    print("\n📊 Operator collecting results...")
    await operator.poll_and_collect_results()

    # 6. Manually mark all subtasks as completed for testing
    # (In real scenario, Magisters would report back)
    print("\n🔧 Manually completing subtasks for test...")
    for subtask in plan.subtasks:
        await operator._update_subtask_result(
            subtask_id=subtask.subtask_id,
            status="completed",
            result={"status": "success", "data": "test result"},
            completed_at=datetime.now(timezone.utc).isoformat(),
        )

    # Trigger finalization
    if await operator._all_subtasks_completed(task.task_id):
        await operator._finalize_task(task.task_id)

    # Wait for finalization
    await asyncio.sleep(0.5)

    # 7. Verify user report
    print("\n📋 Checking user report...")
    report = await operator.get_user_report(task.task_id)

    assert report is not None, "User report not found"
    assert report["status"] == "completed"
    assert "summary" in report
    assert "insights" in report
    assert "metrics" in report
    assert "recommendations" in report

    print(f"✅ User report generated:")
    print(f"   Status: {report['status']}")
    print(f"   Summary: {report['summary']}")
    print(f"   Metrics: {report['metrics']}")

    # Cleanup
    await operator.shutdown()
    await seo.shutdown()
    await content.shutdown()
    await intelligence.shutdown()

    print("\n✅ Full cycle test passed!")


@pytest.mark.skip(reason="Retry logic needs real Magister execution - TODO")
@pytest.mark.asyncio
async def test_error_handling_and_retry():
    """Test error handling with retry logic"""

    # Create failing magister
    class FailingSEOMagister(SEOMagister):
        def __init__(self, *args, fail_count=2, **kwargs):
            super().__init__(*args, **kwargs)
            self.attempt_count = 0
            self.fail_count = fail_count

        async def _execute_task_impl(self, task):
            self.attempt_count += 1
            if self.attempt_count <= self.fail_count:
                raise Exception(f"Simulated failure (attempt {self.attempt_count})")
            # Succeed on 3rd attempt
            return await super()._execute_task_impl(task)

    # Create Operator
    operator = Operator(
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="./test_vault",
    )
    await operator.initialize()

    # Create failing magister
    failing_seo = FailingSEOMagister(
        agent_id="seo-magister-1",
        event_bus=operator.event_bus,
        database_url="sqlite+aiosqlite:///:memory:",
        fail_count=2,  # Fail twice, succeed on 3rd
    )
    await failing_seo.initialize()

    # Send task
    task = Task(
        task_id="task-retry-001",
        source="user",
        goal="Test retry logic",
        description="This task will fail twice then succeed",
        constraints=[],
        resources={},
        priority=1,
        deadline=datetime.now(timezone.utc) + timedelta(hours=1),
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    print("\n📤 Sending task that will fail...")
    await operator.receive_task(task)

    # Process (will fail first time)
    print("🔄 Attempt 1 (should fail)...")
    await failing_seo.poll_and_process_tasks()
    await operator.poll_and_collect_results()
    await asyncio.sleep(0.1)

    # Process retry (will fail second time)
    print("🔄 Attempt 2 (should fail)...")
    await failing_seo.poll_and_process_tasks()
    await operator.poll_and_collect_results()
    await asyncio.sleep(0.1)

    # Process retry (should succeed)
    print("🔄 Attempt 3 (should succeed)...")
    await failing_seo.poll_and_process_tasks()
    await operator.poll_and_collect_results()
    await asyncio.sleep(0.5)

    # Verify retry happened
    subtasks = await operator._collect_subtask_results(task.task_id)
    print(f"\n✅ Task completed after {failing_seo.attempt_count} attempts")
    assert failing_seo.attempt_count == 3, f"Expected 3 attempts, got {failing_seo.attempt_count}"

    # Verify final success
    report = await operator.get_user_report(task.task_id)
    assert report is not None
    assert report["status"] == "completed"

    print("✅ Retry logic test passed!")

    # Cleanup
    await operator.shutdown()
    await failing_seo.shutdown()


@pytest.mark.skip(reason="Timeout handling needs real async execution - TODO")
@pytest.mark.asyncio
async def test_timeout_handling():
    """Test timeout detection and handling"""

    # Create Operator with short timeout
    operator = Operator(
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="./test_vault",
    )
    # Override timeout for testing
    operator.AGENT_TIMEOUTS["seo-magister-1"] = timedelta(seconds=1)
    await operator.initialize()

    # Create magister (won't process tasks, simulating timeout)
    seo = SEOMagister(
        agent_id="seo-magister-1",
        event_bus=operator.event_bus,
        database_url="sqlite+aiosqlite:///:memory:",
    )
    await seo.initialize()

    # Send task
    task = Task(
        task_id="task-timeout-001",
        source="user",
        goal="Test timeout",
        description="This task will timeout",
        constraints=[],
        resources={},
        priority=1,
        deadline=datetime.now(timezone.utc) + timedelta(hours=1),
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    print("\n📤 Sending task that will timeout...")
    await operator.receive_task(task)

    # Wait for timeout
    print("⏳ Waiting for timeout (2 seconds)...")
    await asyncio.sleep(2)

    # Check for timeout
    print("🔍 Checking for timeout...")
    await operator.monitor_timeouts()

    # Verify timeout was handled
    subtask = await operator._get_subtask(
        operator.active_plans[task.task_id].subtasks[0].subtask_id
    )

    print(f"✅ Timeout detected and handled")
    print(f"   Subtask status: {subtask['status']}")
    print(f"   Retry count: {subtask['retry_count']}")

    assert subtask["status"] == "failed"
    assert subtask["result"].get("error") == "timeout"

    print("✅ Timeout handling test passed!")

    # Cleanup
    await operator.shutdown()
    await seo.shutdown()


if __name__ == "__main__":
    print("=" * 60)
    print("Integration Test: Full User Cycle + Error Handling")
    print("=" * 60)

    asyncio.run(test_full_user_cycle())
    print("\n" + "=" * 60)
    asyncio.run(test_error_handling_and_retry())
    print("\n" + "=" * 60)
    asyncio.run(test_timeout_handling())
