# tests/unit/test_base_agent.py
import pytest
from datetime import datetime, timezone
from meai.agents.base_agent import Agent, Task, TaskResult, Feedback, TaskStatus


class TestAgent(Agent):
    """Test agent implementation"""

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute test task"""
        return TaskResult(
            subtask_id=task.subtask_id,
            agent_id=self.agent_id,
            action=task.action,
            status="success",
            result={"message": "Task completed"},
            error=None,
            duration_seconds=0.1,
            completed_at=datetime.now(timezone.utc),
        )

    def get_capabilities(self) -> list[str]:
        """Get test capabilities"""
        return ["test_action", "another_action"]


@pytest.mark.asyncio
async def test_agent_initialization():
    """Test Agent can be initialized"""
    agent = TestAgent(
        agent_id="test-agent",
        agent_type="test",
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="./obsidian",
    )

    assert agent.agent_id == "test-agent"
    assert agent.agent_type == "test"
    assert agent.tasks_completed == 0
    assert agent.tasks_failed == 0


@pytest.mark.asyncio
async def test_agent_get_capabilities():
    """Test getting agent capabilities"""
    agent = TestAgent(
        agent_id="test-agent",
        agent_type="test",
        database_url="sqlite+aiosqlite:///:memory:",
    )

    capabilities = agent.get_capabilities()
    assert "test_action" in capabilities
    assert "another_action" in capabilities


@pytest.mark.asyncio
async def test_agent_receive_and_execute_task():
    """Test receiving and executing a task"""
    agent = TestAgent(
        agent_id="test-agent",
        agent_type="test",
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await agent.initialize()

    # Create task
    task = Task(
        task_id="task-001",
        subtask_id="subtask-001",
        parent_task_id="task-001",
        action="test_action",
        description="Test task",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
    )

    # Receive task (this will execute it)
    await agent.receive_task(task)

    # Check metrics
    assert agent.tasks_completed == 1
    assert agent.tasks_failed == 0

    await agent.shutdown()


@pytest.mark.asyncio
async def test_agent_performance_metrics():
    """Test getting performance metrics"""
    agent = TestAgent(
        agent_id="test-agent",
        agent_type="test",
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await agent.initialize()

    # Execute a task
    task = Task(
        task_id="task-001",
        subtask_id="subtask-001",
        parent_task_id="task-001",
        action="test_action",
        description="Test task",
        priority=1,
        status=TaskStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc),
    )

    await agent.receive_task(task)

    # Get metrics
    metrics = await agent.get_performance_metrics()

    assert metrics["agent_id"] == "test-agent"
    assert metrics["tasks_completed"] == 1
    assert metrics["tasks_failed"] == 0
    assert metrics["success_rate"] == 1.0

    await agent.shutdown()


@pytest.mark.asyncio
async def test_agent_learn_from_feedback():
    """Test learning from feedback"""
    agent = TestAgent(
        agent_id="test-agent",
        agent_type="test",
        database_url="sqlite+aiosqlite:///:memory:",
    )

    await agent.initialize()

    # Create feedback
    feedback = Feedback(
        feedback_id="feedback-001",
        subtask_id="subtask-001",
        rating=5,
        comment="Great work!",
        created_at=datetime.now(timezone.utc),
    )

    # Learn from feedback (should not raise)
    await agent.learn_from_feedback(feedback)

    await agent.shutdown()
