"""
Tests for LearningScheduler.
"""

import pytest
from datetime import datetime

from AIM.src.aim.teacher.scheduling.learning_scheduler import (
    LearningScheduler,
    LearningStrategy,
    ResearchDepth,
    LearningTask,
    LearningPlan,
)
from AIM.src.aim.teacher.scheduling.system_auditor import (
    SystemAuditReport,
    SubagentHealth,
    SubagentStatus,
    Priority,
)


@pytest.fixture
def learning_scheduler():
    """Create LearningScheduler instance."""
    return LearningScheduler(
        time_per_quick=15,
        time_per_standard=30,
        time_per_deep=60,
        cost_per_quick=0.50,
        cost_per_standard=1.50,
        cost_per_deep=3.00,
    )


@pytest.fixture
def sample_audit_report():
    """Create sample audit report."""
    priority_queue = [
        SubagentHealth(
            name="content_gap_analysis",
            status=SubagentStatus.DEGRADED,
            priority=Priority.P1,
            reason="High error rate: 12%",
        ),
        SubagentHealth(
            name="keyword_research",
            status=SubagentStatus.DEGRADED,
            priority=Priority.P2,
            reason="Not taught for 45 days",
        ),
        SubagentHealth(
            name="technical_seo",
            status=SubagentStatus.HEALTHY,
            priority=Priority.P3,
            reason="Routine update",
        ),
        SubagentHealth(
            name="competitor_analyzer",
            status=SubagentStatus.HEALTHY,
            priority=Priority.P4,
            reason="Optional improvement",
        ),
    ]

    return SystemAuditReport(
        timestamp=datetime.now(),
        total_subagents=4,
        healthy=2,
        degraded=2,
        missing=0,
        deprecated=0,
        priority_queue=priority_queue,
        summary="Test audit report",
    )


@pytest.mark.asyncio
async def test_create_task_p1_deep_research(learning_scheduler):
    """Test task creation for P1 priority (deep research)."""
    subagent = SubagentHealth(
        name="test_agent",
        status=SubagentStatus.DEGRADED,
        priority=Priority.P1,
        reason="Critical issue",
    )

    task = learning_scheduler._create_task(subagent)

    assert task.subagent_name == "test_agent"
    assert task.priority == Priority.P1
    assert task.research_depth == ResearchDepth.DEEP
    assert task.estimated_time_minutes == 60
    assert task.estimated_cost_usd == 3.00


@pytest.mark.asyncio
async def test_create_task_p2_standard_research(learning_scheduler):
    """Test task creation for P2 priority (standard research)."""
    subagent = SubagentHealth(
        name="test_agent",
        status=SubagentStatus.DEGRADED,
        priority=Priority.P2,
        reason="Not taught for 45 days",
    )

    task = learning_scheduler._create_task(subagent)

    assert task.research_depth == ResearchDepth.STANDARD
    assert task.estimated_time_minutes == 30
    assert task.estimated_cost_usd == 1.50


@pytest.mark.asyncio
async def test_create_task_p4_quick_research(learning_scheduler):
    """Test task creation for P4 priority (quick research)."""
    subagent = SubagentHealth(
        name="test_agent",
        status=SubagentStatus.HEALTHY,
        priority=Priority.P4,
        reason="Optional improvement",
    )

    task = learning_scheduler._create_task(subagent)

    assert task.research_depth == ResearchDepth.QUICK
    assert task.estimated_time_minutes == 15
    assert task.estimated_cost_usd == 0.50


@pytest.mark.asyncio
async def test_create_learning_plan_sequential(learning_scheduler, sample_audit_report):
    """Test learning plan creation with sequential strategy."""
    plan = await learning_scheduler.create_learning_plan(
        audit_report=sample_audit_report,
        strategy=LearningStrategy.SEQUENTIAL,
    )

    assert isinstance(plan, LearningPlan)
    assert plan.strategy == LearningStrategy.SEQUENTIAL
    assert plan.total_subagents == 4
    assert len(plan.tasks) == 4

    # Sequential = one task per wave
    assert len(plan.execution_order) == 4
    assert all(len(wave) == 1 for wave in plan.execution_order)


@pytest.mark.asyncio
async def test_create_learning_plan_parallel(learning_scheduler, sample_audit_report):
    """Test learning plan creation with parallel strategy."""
    plan = await learning_scheduler.create_learning_plan(
        audit_report=sample_audit_report,
        strategy=LearningStrategy.PARALLEL,
    )

    assert plan.strategy == LearningStrategy.PARALLEL

    # Parallel = all tasks in one wave
    assert len(plan.execution_order) == 1
    assert len(plan.execution_order[0]) == 4


@pytest.mark.asyncio
async def test_create_learning_plan_batch(learning_scheduler, sample_audit_report):
    """Test learning plan creation with batch strategy."""
    plan = await learning_scheduler.create_learning_plan(
        audit_report=sample_audit_report,
        strategy=LearningStrategy.BATCH,
    )

    assert plan.strategy == LearningStrategy.BATCH

    # Batch = group by priority (4 different priorities = 4 waves)
    assert len(plan.execution_order) == 4


@pytest.mark.asyncio
async def test_plan_cost_calculation(learning_scheduler, sample_audit_report):
    """Test total cost calculation."""
    plan = await learning_scheduler.create_learning_plan(
        audit_report=sample_audit_report,
        strategy=LearningStrategy.SEQUENTIAL,
    )

    # P1 (deep) + P2 (standard) + P3 (standard) + P4 (quick)
    # = $3.00 + $1.50 + $1.50 + $0.50 = $6.50
    assert plan.total_estimated_cost_usd == 6.50


@pytest.mark.asyncio
async def test_plan_time_calculation(learning_scheduler, sample_audit_report):
    """Test total time calculation."""
    plan = await learning_scheduler.create_learning_plan(
        audit_report=sample_audit_report,
        strategy=LearningStrategy.SEQUENTIAL,
    )

    # P1 (60) + P2 (30) + P3 (30) + P4 (15) = 135 minutes
    assert plan.total_estimated_time_minutes == 135


@pytest.mark.asyncio
async def test_tasks_ordered_by_priority(learning_scheduler, sample_audit_report):
    """Test that tasks are ordered by priority."""
    plan = await learning_scheduler.create_learning_plan(
        audit_report=sample_audit_report,
        strategy=LearningStrategy.SEQUENTIAL,
    )

    # Should be ordered P1, P2, P3, P4
    assert plan.tasks[0].priority == Priority.P1
    assert plan.tasks[1].priority == Priority.P2
    assert plan.tasks[2].priority == Priority.P3
    assert plan.tasks[3].priority == Priority.P4


@pytest.mark.asyncio
async def test_format_plan_output(learning_scheduler, sample_audit_report):
    """Test plan formatting."""
    plan = await learning_scheduler.create_learning_plan(
        audit_report=sample_audit_report,
        strategy=LearningStrategy.SEQUENTIAL,
    )

    formatted = learning_scheduler.format_plan(plan)

    assert "Learning Plan Created" in formatted
    assert "Strategy: sequential" in formatted
    assert "Total subagents: 4" in formatted
    assert "$6.50" in formatted
    assert "content_gap_analysis" in formatted
    assert "🔴 [P1]" in formatted  # P1 emoji


@pytest.mark.asyncio
async def test_format_time_minutes(learning_scheduler):
    """Test time formatting for minutes."""
    formatted = learning_scheduler._format_time(45)
    assert formatted == "45 minutes"


@pytest.mark.asyncio
async def test_format_time_hours(learning_scheduler):
    """Test time formatting for hours."""
    formatted = learning_scheduler._format_time(120)
    assert formatted == "2 hours"


@pytest.mark.asyncio
async def test_format_time_hours_and_minutes(learning_scheduler):
    """Test time formatting for hours and minutes."""
    formatted = learning_scheduler._format_time(135)
    assert formatted == "2 hours 15 minutes"


@pytest.mark.asyncio
async def test_empty_audit_report(learning_scheduler):
    """Test plan creation with empty audit report."""
    empty_report = SystemAuditReport(
        timestamp=datetime.now(),
        total_subagents=0,
        healthy=0,
        degraded=0,
        missing=0,
        deprecated=0,
        priority_queue=[],
        summary="Empty report",
    )

    plan = await learning_scheduler.create_learning_plan(
        audit_report=empty_report,
        strategy=LearningStrategy.SEQUENTIAL,
    )

    assert plan.total_subagents == 0
    assert plan.total_estimated_time_minutes == 0
    assert plan.total_estimated_cost_usd == 0.0
    assert len(plan.tasks) == 0


@pytest.mark.asyncio
async def test_custom_time_costs(learning_scheduler):
    """Test scheduler with custom time/cost settings."""
    custom_scheduler = LearningScheduler(
        time_per_quick=10,
        time_per_standard=20,
        time_per_deep=40,
        cost_per_quick=0.25,
        cost_per_standard=1.00,
        cost_per_deep=2.00,
    )

    subagent = SubagentHealth(
        name="test_agent",
        status=SubagentStatus.DEGRADED,
        priority=Priority.P1,
        reason="Critical",
    )

    task = custom_scheduler._create_task(subagent)

    assert task.estimated_time_minutes == 40
    assert task.estimated_cost_usd == 2.00
