"""Tests for sprint execution events.

This module tests all sprint execution events:
- Phase 2.1 (Sprint Planning): SprintPlanningStartedEvent, SprintPlanCreatedEvent, SprintApprovedEvent
- Phase 2.3 (Sprint Review): SprintReviewStartedEvent, SprintReportGeneratedEvent
- Phase 2.4 (Sprint Retrospective): SprintRetrospectiveStartedEvent, SprintLessonsLearnedEvent, SprintCompletedEvent

All tests verify:
- Event structure and types
- Priority levels
- Data validation
- Model relationships
"""

from datetime import UTC, datetime

import pytest

from meai.events.sprint_events import (
    ActionItem,
    SprintApprovedData,
    SprintApprovedEvent,
    SprintCompletedData,
    SprintCompletedEvent,
    SprintLessonsLearnedData,
    SprintLessonsLearnedEvent,
    SprintMetrics,
    SprintPlanCreatedData,
    SprintPlanCreatedEvent,
    SprintPlanningStartedData,
    SprintPlanningStartedEvent,
    SprintReportGeneratedData,
    SprintReportGeneratedEvent,
    SprintRetrospectiveStartedData,
    SprintRetrospectiveStartedEvent,
    SprintReviewStartedData,
    SprintReviewStartedEvent,
    SprintSummary,
    SprintTask,
    TaskDependency,
)


# ============================================================================
# Phase 2.1: Sprint Planning Events
# ============================================================================


def test_sprint_planning_started_event():
    """Test SprintPlanningStartedEvent structure and priority."""
    event = SprintPlanningStartedEvent(
        source="operator",
        target="seo-magister",
        data=SprintPlanningStartedData(
            project_id="proj-001",
            sprint_id="sprint-001",
            sprint_number=1,
            start_date=datetime(2026, 5, 8, tzinfo=UTC),
            end_date=datetime(2026, 5, 22, tzinfo=UTC),
            available_hours=80,
        ),
    )

    assert event.type == "sprint.planning.started"
    assert event.priority == 1  # P1 - high priority
    assert event.source == "operator"
    assert event.target == "seo-magister"
    assert event.data.project_id == "proj-001"
    assert event.data.sprint_id == "sprint-001"
    assert event.data.sprint_number == 1
    assert event.data.available_hours == 80


def test_sprint_task_model():
    """Test SprintTask model with dependencies."""
    task = SprintTask(
        task_id="task-001",
        magister="seo-magister",
        capability="analyze_competitors",
        description="Analyze top 5 competitors",
        estimated_hours=8,
        priority="high",
        dependencies=["task-000"],
    )

    assert task.task_id == "task-001"
    assert task.magister == "seo-magister"
    assert task.capability == "analyze_competitors"
    assert task.estimated_hours == 8
    assert task.priority == "high"
    assert task.dependencies == ["task-000"]


def test_task_dependency_model():
    """Test TaskDependency model with blocking and soft dependencies."""
    # Blocking dependency
    blocking_dep = TaskDependency(
        task_id="task-002",
        depends_on=["task-001"],
        dependency_type="blocking",
    )

    assert blocking_dep.task_id == "task-002"
    assert blocking_dep.depends_on == ["task-001"]
    assert blocking_dep.dependency_type == "blocking"

    # Soft dependency
    soft_dep = TaskDependency(
        task_id="task-003",
        depends_on=["task-001", "task-002"],
        dependency_type="soft",
    )

    assert soft_dep.dependency_type == "soft"
    assert len(soft_dep.depends_on) == 2


def test_sprint_plan_created_event():
    """Test SprintPlanCreatedEvent with tasks and dependencies."""
    tasks = [
        SprintTask(
            task_id="task-001",
            magister="seo-magister",
            capability="analyze_competitors",
            description="Analyze competitors",
            estimated_hours=8,
            priority="high",
            dependencies=[],
        ),
        SprintTask(
            task_id="task-002",
            magister="content-magister",
            capability="generate_content",
            description="Generate blog posts",
            estimated_hours=12,
            priority="medium",
            dependencies=["task-001"],
        ),
    ]

    dependencies = [
        TaskDependency(
            task_id="task-002",
            depends_on=["task-001"],
            dependency_type="blocking",
        ),
    ]

    event = SprintPlanCreatedEvent(
        source="operator",
        target="all-magisters",
        data=SprintPlanCreatedData(
            project_id="proj-001",
            sprint_id="sprint-001",
            tasks=tasks,
            dependencies=dependencies,
            total_estimated_hours=20,
            requires_approval=True,
        ),
    )

    assert event.type == "sprint.plan.created"
    assert event.priority == 1  # P1 - high priority
    assert len(event.data.tasks) == 2
    assert len(event.data.dependencies) == 1
    assert event.data.total_estimated_hours == 20
    assert event.data.requires_approval is True


def test_sprint_approved_event():
    """Test SprintApprovedEvent structure."""
    event = SprintApprovedEvent(
        source="user",
        target="operator",
        data=SprintApprovedData(
            project_id="proj-001",
            sprint_id="sprint-001",
            approved_by="user",
            approved_at=datetime(2026, 5, 8, 10, 0, tzinfo=UTC),
            comments="Looks good, proceed",
        ),
    )

    assert event.type == "sprint.approved"
    assert event.priority == 1  # P1 - high priority
    assert event.data.approved_by == "user"
    assert event.data.comments == "Looks good, proceed"


# ============================================================================
# Phase 2.3: Sprint Review Events
# ============================================================================


def test_sprint_review_started_event():
    """Test SprintReviewStartedEvent structure."""
    event = SprintReviewStartedEvent(
        source="operator",
        target="all-magisters",
        data=SprintReviewStartedData(
            project_id="proj-001",
            sprint_id="sprint-001",
            review_date=datetime(2026, 5, 22, tzinfo=UTC),
        ),
    )

    assert event.type == "sprint.review.started"
    assert event.priority == 1  # P1 - high priority
    assert event.data.project_id == "proj-001"
    assert event.data.sprint_id == "sprint-001"


def test_sprint_summary_model():
    """Test SprintSummary model."""
    summary = SprintSummary(
        completed_tasks=8,
        total_tasks=10,
        completion_rate=0.8,
        hours_planned=80,
        hours_actual=75,
        achievements=[
            "Completed competitor analysis",
            "Generated 5 blog posts",
        ],
        challenges=[
            "API rate limits slowed data collection",
        ],
    )

    assert summary.completed_tasks == 8
    assert summary.total_tasks == 10
    assert summary.completion_rate == 0.8
    assert summary.hours_planned == 80
    assert summary.hours_actual == 75
    assert len(summary.achievements) == 2
    assert len(summary.challenges) == 1


def test_sprint_metrics_model():
    """Test SprintMetrics model."""
    metrics = SprintMetrics(
        velocity=8,
        quality_score=0.92,
        client_satisfaction=4.5,
        magister_performance={
            "seo-magister": 0.95,
            "content-magister": 0.88,
            "ads-magister": 0.90,
        },
    )

    assert metrics.velocity == 8
    assert metrics.quality_score == 0.92
    assert metrics.client_satisfaction == 4.5
    assert len(metrics.magister_performance) == 3
    assert metrics.magister_performance["seo-magister"] == 0.95


def test_sprint_report_generated_event():
    """Test SprintReportGeneratedEvent with summary and metrics."""
    from meai.events.task_events import Deliverable

    summary = SprintSummary(
        completed_tasks=8,
        total_tasks=10,
        completion_rate=0.8,
        hours_planned=80,
        hours_actual=75,
        achievements=["Completed analysis"],
        challenges=["Rate limits"],
    )

    metrics = SprintMetrics(
        velocity=8,
        quality_score=0.92,
        client_satisfaction=4.5,
        magister_performance={"seo-magister": 0.95},
    )

    deliverables = [
        Deliverable(
            type="report",
            title="Sprint Report",
            description="Sprint 1 summary",
            file_path="/reports/sprint-001.pdf",
            requires_approval=False,
        ),
    ]

    event = SprintReportGeneratedEvent(
        source="operator",
        target="user",
        data=SprintReportGeneratedData(
            project_id="proj-001",
            sprint_id="sprint-001",
            summary=summary,
            metrics=metrics,
            deliverables=deliverables,
            generated_at=datetime(2026, 5, 22, 16, 0, tzinfo=UTC),
        ),
    )

    assert event.type == "sprint.report.generated"
    assert event.priority == 1  # P1 - high priority
    assert event.data.summary.completed_tasks == 8
    assert event.data.metrics.velocity == 8
    assert len(event.data.deliverables) == 1


# ============================================================================
# Phase 2.4: Sprint Retrospective Events
# ============================================================================


def test_sprint_retrospective_started_event():
    """Test SprintRetrospectiveStartedEvent structure."""
    event = SprintRetrospectiveStartedEvent(
        source="operator",
        target="all-magisters",
        data=SprintRetrospectiveStartedData(
            project_id="proj-001",
            sprint_id="sprint-001",
            retrospective_date=datetime(2026, 5, 23, tzinfo=UTC),
        ),
    )

    assert event.type == "sprint.retrospective.started"
    assert event.priority == 2  # P2 - normal priority
    assert event.data.project_id == "proj-001"


def test_action_item_model():
    """Test ActionItem model."""
    action = ActionItem(
        description="Implement rate limit handling",
        assignee="seo-magister",
        deadline=datetime(2026, 5, 30, tzinfo=UTC),
        priority="high",
    )

    assert action.description == "Implement rate limit handling"
    assert action.assignee == "seo-magister"
    assert action.priority == "high"


def test_sprint_lessons_learned_event():
    """Test SprintLessonsLearnedEvent with action items."""
    action_items = [
        ActionItem(
            description="Add retry logic for API calls",
            assignee="seo-magister",
            deadline=datetime(2026, 5, 30, tzinfo=UTC),
            priority="high",
        ),
        ActionItem(
            description="Improve task estimation accuracy",
            assignee="operator",
            deadline=datetime(2026, 6, 1, tzinfo=UTC),
            priority="medium",
        ),
    ]

    event = SprintLessonsLearnedEvent(
        source="operator",
        target="all-magisters",
        data=SprintLessonsLearnedData(
            project_id="proj-001",
            sprint_id="sprint-001",
            what_went_well=[
                "Good collaboration between magisters",
                "High quality deliverables",
            ],
            what_needs_improvement=[
                "Better handling of API rate limits",
                "More accurate time estimates",
            ],
            action_items=action_items,
        ),
    )

    assert event.type == "sprint.lessons.learned"
    assert event.priority == 2  # P2 - normal priority
    assert len(event.data.what_went_well) == 2
    assert len(event.data.what_needs_improvement) == 2
    assert len(event.data.action_items) == 2


def test_sprint_completed_event():
    """Test SprintCompletedEvent structure."""
    event = SprintCompletedEvent(
        source="operator",
        target="user",
        data=SprintCompletedData(
            project_id="proj-001",
            sprint_id="sprint-001",
            completed_at=datetime(2026, 5, 23, 17, 0, tzinfo=UTC),
            final_status="completed",
            next_sprint_id="sprint-002",
        ),
    )

    assert event.type == "sprint.completed"
    assert event.priority == 2  # P2 - normal priority
    assert event.data.final_status == "completed"
    assert event.data.next_sprint_id == "sprint-002"


# ============================================================================
# Edge Cases and Validation
# ============================================================================


def test_sprint_task_without_dependencies():
    """Test SprintTask with empty dependencies list."""
    task = SprintTask(
        task_id="task-001",
        magister="seo-magister",
        capability="analyze_competitors",
        description="Analyze competitors",
        estimated_hours=8,
        priority="high",
        dependencies=[],
    )

    assert task.dependencies == []


def test_sprint_summary_with_zero_completion():
    """Test SprintSummary with zero completion rate."""
    summary = SprintSummary(
        completed_tasks=0,
        total_tasks=10,
        completion_rate=0.0,
        hours_planned=80,
        hours_actual=0,
        achievements=[],
        challenges=["Sprint cancelled due to client request"],
    )

    assert summary.completion_rate == 0.0
    assert summary.completed_tasks == 0


def test_sprint_metrics_with_empty_magister_performance():
    """Test SprintMetrics with no magister performance data."""
    metrics = SprintMetrics(
        velocity=0,
        quality_score=0.0,
        client_satisfaction=0.0,
        magister_performance={},
    )

    assert metrics.magister_performance == {}


def test_action_item_without_deadline():
    """Test ActionItem with optional deadline."""
    action = ActionItem(
        description="Review process improvements",
        assignee="operator",
        deadline=None,
        priority="low",
    )

    assert action.deadline is None


def test_sprint_approved_without_comments():
    """Test SprintApprovedEvent without comments."""
    event = SprintApprovedEvent(
        source="user",
        target="operator",
        data=SprintApprovedData(
            project_id="proj-001",
            sprint_id="sprint-001",
            approved_by="user",
            approved_at=datetime(2026, 5, 8, 10, 0, tzinfo=UTC),
            comments=None,
        ),
    )

    assert event.data.comments is None


def test_sprint_completed_without_next_sprint():
    """Test SprintCompletedEvent without next sprint."""
    event = SprintCompletedEvent(
        source="operator",
        target="user",
        data=SprintCompletedData(
            project_id="proj-001",
            sprint_id="sprint-001",
            completed_at=datetime(2026, 5, 23, 17, 0, tzinfo=UTC),
            final_status="completed",
            next_sprint_id=None,
        ),
    )

    assert event.data.next_sprint_id is None


# ============================================================================
# Priority Validation
# ============================================================================


def test_sprint_planning_events_priority():
    """Test that sprint planning events have P1 priority."""
    planning_started = SprintPlanningStartedEvent(
        source="operator",
        target="seo-magister",
        data=SprintPlanningStartedData(
            project_id="proj-001",
            sprint_id="sprint-001",
            sprint_number=1,
            start_date=datetime(2026, 5, 8, tzinfo=UTC),
            end_date=datetime(2026, 5, 22, tzinfo=UTC),
            available_hours=80,
        ),
    )

    plan_created = SprintPlanCreatedEvent(
        source="operator",
        target="all-magisters",
        data=SprintPlanCreatedData(
            project_id="proj-001",
            sprint_id="sprint-001",
            tasks=[],
            dependencies=[],
            total_estimated_hours=0,
            requires_approval=True,
        ),
    )

    approved = SprintApprovedEvent(
        source="user",
        target="operator",
        data=SprintApprovedData(
            project_id="proj-001",
            sprint_id="sprint-001",
            approved_by="user",
            approved_at=datetime(2026, 5, 8, 10, 0, tzinfo=UTC),
            comments=None,
        ),
    )

    assert planning_started.priority == 1
    assert plan_created.priority == 1
    assert approved.priority == 1


def test_sprint_review_events_priority():
    """Test that sprint review events have P1 priority."""
    review_started = SprintReviewStartedEvent(
        source="operator",
        target="all-magisters",
        data=SprintReviewStartedData(
            project_id="proj-001",
            sprint_id="sprint-001",
            review_date=datetime(2026, 5, 22, tzinfo=UTC),
        ),
    )

    report_generated = SprintReportGeneratedEvent(
        source="operator",
        target="user",
        data=SprintReportGeneratedData(
            project_id="proj-001",
            sprint_id="sprint-001",
            summary=SprintSummary(
                completed_tasks=0,
                total_tasks=0,
                completion_rate=0.0,
                hours_planned=0,
                hours_actual=0,
                achievements=[],
                challenges=[],
            ),
            metrics=SprintMetrics(
                velocity=0,
                quality_score=0.0,
                client_satisfaction=0.0,
                magister_performance={},
            ),
            deliverables=[],
            generated_at=datetime(2026, 5, 22, 16, 0, tzinfo=UTC),
        ),
    )

    assert review_started.priority == 1
    assert report_generated.priority == 1


def test_sprint_retrospective_events_priority():
    """Test that sprint retrospective events have P2 priority."""
    retrospective_started = SprintRetrospectiveStartedEvent(
        source="operator",
        target="all-magisters",
        data=SprintRetrospectiveStartedData(
            project_id="proj-001",
            sprint_id="sprint-001",
            retrospective_date=datetime(2026, 5, 23, tzinfo=UTC),
        ),
    )

    lessons_learned = SprintLessonsLearnedEvent(
        source="operator",
        target="all-magisters",
        data=SprintLessonsLearnedData(
            project_id="proj-001",
            sprint_id="sprint-001",
            what_went_well=[],
            what_needs_improvement=[],
            action_items=[],
        ),
    )

    completed = SprintCompletedEvent(
        source="operator",
        target="user",
        data=SprintCompletedData(
            project_id="proj-001",
            sprint_id="sprint-001",
            completed_at=datetime(2026, 5, 23, 17, 0, tzinfo=UTC),
            final_status="completed",
            next_sprint_id=None,
        ),
    )

    assert retrospective_started.priority == 2
    assert lessons_learned.priority == 2
    assert completed.priority == 2
