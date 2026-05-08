"""Tests for project lifecycle events."""

import pytest
from datetime import datetime
from uuid import UUID

from meai.events.base import BaseEvent, ProjectStatus
from meai.events.project_events import (
    # Phase -1 (Pre-Sale)
    ProjectCreatedEvent,
    ProjectCreatedData,
    # Phase 0 (Setup)
    InfrastructureSetupStartedEvent,
    InfrastructureSetupCompletedEvent,
    SetupTask,
    # Phase 1 (Baseline)
    BaselineCollectionStartedEvent,
    BaselineDataCollectedEvent,
    BaselineAggregationCompletedEvent,
    BaselineTask,
    # Phase 1.5 (Strategy Planning)
    StrategyPlanningStartedEvent,
    StrategyProposalReadyEvent,
    StrategyReviewRequestedEvent,
    StrategyModifiedEvent,
    StrategyApprovedEvent,
    StrategyModification,
)


class TestProjectCreatedEvent:
    """Test Phase -1 (Pre-Sale) - ProjectCreatedEvent."""

    def test_project_created_event_with_all_fields(self):
        """Test ProjectCreatedEvent with all fields."""
        project_data = ProjectCreatedData(
            project_id="proj-001",
            client_name="Test Client",
            client_domain="testclient.com",
            client_contact="contact@testclient.com",
            industry="Healthcare",
            initial_status=ProjectStatus.PRE_SALE,
            source="Website Form",
            created_at=datetime.now(),
            notes="Initial contact from website",
        )

        event = ProjectCreatedEvent(
            source="operator",
            target="project_manager",
            data=project_data,
        )

        assert event.type == "project.created"
        assert event.source == "operator"
        assert event.target == "project_manager"
        assert event.priority == 1
        assert isinstance(event.id, UUID)
        assert isinstance(event.timestamp, datetime)
        assert event.data.project_id == "proj-001"
        assert event.data.client_name == "Test Client"
        assert event.data.client_domain == "testclient.com"
        assert event.data.client_contact == "contact@testclient.com"
        assert event.data.industry == "Healthcare"
        assert event.data.initial_status == ProjectStatus.PRE_SALE
        assert event.data.source == "Website Form"
        assert event.data.notes == "Initial contact from website"

    def test_project_created_event_with_minimal_fields(self):
        """Test ProjectCreatedEvent with minimal required fields."""
        project_data = ProjectCreatedData(
            project_id="proj-002",
            client_name="Minimal Client",
            client_domain="minimal.com",
            client_contact="contact@minimal.com",
            industry="Tech",
            initial_status=ProjectStatus.LEAD,
            source="Referral",
            created_at=datetime.now(),
        )

        event = ProjectCreatedEvent(
            source="operator",
            target="project_manager",
            data=project_data,
        )

        assert event.data.project_id == "proj-002"
        assert event.data.notes is None

    def test_project_created_event_inherits_from_base_event(self):
        """Test that ProjectCreatedEvent inherits from BaseEvent."""
        project_data = ProjectCreatedData(
            project_id="proj-003",
            client_name="Test",
            client_domain="test.com",
            client_contact="test@test.com",
            industry="Tech",
            initial_status=ProjectStatus.LEAD,
            source="Direct",
            created_at=datetime.now(),
        )

        event = ProjectCreatedEvent(
            source="operator",
            target="project_manager",
            data=project_data,
        )

        assert isinstance(event, BaseEvent)


class TestInfrastructureSetupEvents:
    """Test Phase 0 (Setup) - Infrastructure Setup Events."""

    def test_infrastructure_setup_started_event(self):
        """Test InfrastructureSetupStartedEvent."""
        tasks = [
            SetupTask(
                task_id="setup-001",
                task_type="obsidian_vault",
                description="Create Obsidian vault for project",
                assigned_to="infrastructure_agent",
            ),
            SetupTask(
                task_id="setup-002",
                task_type="database",
                description="Initialize project database",
                assigned_to="infrastructure_agent",
            ),
        ]

        event = InfrastructureSetupStartedEvent(
            source="operator",
            target="infrastructure_agent",
            project_id="proj-001",
            tasks=tasks,
        )

        assert event.type == "infrastructure.setup.started"
        assert event.source == "operator"
        assert event.target == "infrastructure_agent"
        assert event.priority == 1
        assert event.project_id == "proj-001"
        assert len(event.tasks) == 2
        assert event.tasks[0].task_id == "setup-001"
        assert event.tasks[0].task_type == "obsidian_vault"
        assert event.tasks[1].task_id == "setup-002"
        assert event.tasks[1].task_type == "database"

    def test_infrastructure_setup_completed_event(self):
        """Test InfrastructureSetupCompletedEvent."""
        event = InfrastructureSetupCompletedEvent(
            source="infrastructure_agent",
            target="operator",
            project_id="proj-001",
            completed_tasks=["setup-001", "setup-002"],
            setup_summary="All infrastructure tasks completed successfully",
        )

        assert event.type == "infrastructure.setup.completed"
        assert event.source == "infrastructure_agent"
        assert event.target == "operator"
        assert event.priority == 1
        assert event.project_id == "proj-001"
        assert len(event.completed_tasks) == 2
        assert event.setup_summary == "All infrastructure tasks completed successfully"

    def test_setup_task_model(self):
        """Test SetupTask model."""
        task = SetupTask(
            task_id="setup-003",
            task_type="api_keys",
            description="Configure API keys",
            assigned_to="config_agent",
        )

        assert task.task_id == "setup-003"
        assert task.task_type == "api_keys"
        assert task.description == "Configure API keys"
        assert task.assigned_to == "config_agent"


class TestBaselineCollectionEvents:
    """Test Phase 1 (Baseline) - Baseline Collection Events."""

    def test_baseline_collection_started_event(self):
        """Test BaselineCollectionStartedEvent."""
        tasks = [
            BaselineTask(
                task_id="baseline-001",
                domain="SEO",
                metric_type="rankings",
                description="Collect current keyword rankings",
                assigned_to="seo_magister",
            ),
            BaselineTask(
                task_id="baseline-002",
                domain="Content",
                metric_type="content_audit",
                description="Audit existing content",
                assigned_to="content_magister",
            ),
        ]

        event = BaselineCollectionStartedEvent(
            source="operator",
            target=["seo_magister", "content_magister"],
            project_id="proj-001",
            tasks=tasks,
        )

        assert event.type == "baseline.collection.started"
        assert event.source == "operator"
        assert event.target == ["seo_magister", "content_magister"]
        assert event.priority == 1
        assert event.project_id == "proj-001"
        assert len(event.tasks) == 2
        assert event.tasks[0].domain == "SEO"
        assert event.tasks[1].domain == "Content"

    def test_baseline_data_collected_event(self):
        """Test BaselineDataCollectedEvent."""
        metrics = {
            "organic_traffic": 5000,
            "keyword_rankings": {"keyword1": 5, "keyword2": 12},
            "backlinks": 150,
        }

        event = BaselineDataCollectedEvent(
            source="seo_magister",
            target="operator",
            project_id="proj-001",
            domain="SEO",
            metrics=metrics,
            collection_timestamp=datetime.now(),
        )

        assert event.type == "baseline.data.collected"
        assert event.source == "seo_magister"
        assert event.target == "operator"
        assert event.priority == 1
        assert event.project_id == "proj-001"
        assert event.domain == "SEO"
        assert event.metrics["organic_traffic"] == 5000
        assert len(event.metrics["keyword_rankings"]) == 2

    def test_baseline_aggregation_completed_event(self):
        """Test BaselineAggregationCompletedEvent."""
        aggregated_data = {
            "SEO": {"traffic": 5000, "rankings": 50},
            "Content": {"pages": 100, "word_count": 50000},
            "Ads": {"spend": 10000, "conversions": 200},
        }

        event = BaselineAggregationCompletedEvent(
            source="operator",
            target="architect",
            project_id="proj-001",
            aggregated_data=aggregated_data,
            summary="Baseline data collected from all domains",
        )

        assert event.type == "baseline.aggregation.completed"
        assert event.source == "operator"
        assert event.target == "architect"
        assert event.priority == 1
        assert event.project_id == "proj-001"
        assert len(event.aggregated_data) == 3
        assert event.aggregated_data["SEO"]["traffic"] == 5000
        assert event.summary == "Baseline data collected from all domains"

    def test_baseline_task_model(self):
        """Test BaselineTask model."""
        task = BaselineTask(
            task_id="baseline-003",
            domain="Ads",
            metric_type="campaign_performance",
            description="Collect ad campaign metrics",
            assigned_to="ads_magister",
        )

        assert task.task_id == "baseline-003"
        assert task.domain == "Ads"
        assert task.metric_type == "campaign_performance"
        assert task.description == "Collect ad campaign metrics"
        assert task.assigned_to == "ads_magister"


class TestStrategyPlanningEvents:
    """Test Phase 1.5 (Strategy Planning) - Strategy Planning Events."""

    def test_strategy_planning_started_event(self):
        """Test StrategyPlanningStartedEvent."""
        baseline_summary = {
            "current_traffic": 5000,
            "current_rankings": 50,
            "content_pages": 100,
        }

        event = StrategyPlanningStartedEvent(
            source="operator",
            target="architect",
            project_id="proj-001",
            baseline_summary=baseline_summary,
        )

        assert event.type == "strategy.planning.started"
        assert event.source == "operator"
        assert event.target == "architect"
        assert event.priority == 1
        assert event.project_id == "proj-001"
        assert event.baseline_summary["current_traffic"] == 5000

    def test_strategy_proposal_ready_event(self):
        """Test StrategyProposalReadyEvent."""
        proposal = {
            "goals": ["Increase traffic by 50%", "Improve rankings for 20 keywords"],
            "tactics": ["Content creation", "Link building", "Technical SEO"],
            "timeline": "6 months",
            "budget": 50000,
        }

        event = StrategyProposalReadyEvent(
            source="architect",
            target="operator",
            project_id="proj-001",
            proposal=proposal,
        )

        assert event.type == "strategy.proposal.ready"
        assert event.source == "architect"
        assert event.target == "operator"
        assert event.priority == 1
        assert event.project_id == "proj-001"
        assert len(event.proposal["goals"]) == 2
        assert event.proposal["budget"] == 50000

    def test_strategy_review_requested_event(self):
        """Test StrategyReviewRequestedEvent."""
        proposal = {
            "goals": ["Goal 1", "Goal 2"],
            "tactics": ["Tactic 1", "Tactic 2"],
        }

        event = StrategyReviewRequestedEvent(
            source="operator",
            target="user",
            project_id="proj-001",
            proposal=proposal,
            review_deadline=datetime.now(),
        )

        assert event.type == "strategy.review.requested"
        assert event.source == "operator"
        assert event.target == "user"
        assert event.priority == 1
        assert event.project_id == "proj-001"
        assert len(event.proposal["goals"]) == 2
        assert isinstance(event.review_deadline, datetime)

    def test_strategy_modified_event(self):
        """Test StrategyModifiedEvent."""
        modifications = [
            StrategyModification(
                field="budget",
                old_value=50000,
                new_value=40000,
                reason="Budget constraints",
            ),
            StrategyModification(
                field="timeline",
                old_value="6 months",
                new_value="8 months",
                reason="Extended timeline for reduced budget",
            ),
        ]

        event = StrategyModifiedEvent(
            source="user",
            target="architect",
            project_id="proj-001",
            modifications=modifications,
        )

        assert event.type == "strategy.modified"
        assert event.source == "user"
        assert event.target == "architect"
        assert event.priority == 1
        assert event.project_id == "proj-001"
        assert len(event.modifications) == 2
        assert event.modifications[0].field == "budget"
        assert event.modifications[0].new_value == 40000
        assert event.modifications[1].reason == "Extended timeline for reduced budget"

    def test_strategy_approved_event(self):
        """Test StrategyApprovedEvent."""
        final_strategy = {
            "goals": ["Goal 1", "Goal 2"],
            "tactics": ["Tactic 1", "Tactic 2"],
            "budget": 40000,
            "timeline": "8 months",
        }

        event = StrategyApprovedEvent(
            source="user",
            target="operator",
            project_id="proj-001",
            final_strategy=final_strategy,
            approval_timestamp=datetime.now(),
        )

        assert event.type == "strategy.approved"
        assert event.source == "user"
        assert event.target == "operator"
        assert event.priority == 1
        assert event.project_id == "proj-001"
        assert event.final_strategy["budget"] == 40000
        assert isinstance(event.approval_timestamp, datetime)

    def test_strategy_modification_model(self):
        """Test StrategyModification model."""
        modification = StrategyModification(
            field="goals",
            old_value=["Goal 1", "Goal 2"],
            new_value=["Goal 1", "Goal 2", "Goal 3"],
            reason="Added additional goal based on client feedback",
        )

        assert modification.field == "goals"
        assert len(modification.old_value) == 2
        assert len(modification.new_value) == 3
        assert modification.reason == "Added additional goal based on client feedback"


class TestEventInheritance:
    """Test that all events properly inherit from BaseEvent."""

    def test_all_events_inherit_from_base_event(self):
        """Test that all project events inherit from BaseEvent."""
        # Phase -1
        project_data = ProjectCreatedData(
            project_id="test",
            client_name="Test",
            client_domain="test.com",
            client_contact="test@test.com",
            industry="Tech",
            initial_status=ProjectStatus.LEAD,
            source="Test",
            created_at=datetime.now(),
        )
        assert isinstance(
            ProjectCreatedEvent(source="test", target="test", data=project_data),
            BaseEvent,
        )

        # Phase 0
        assert isinstance(
            InfrastructureSetupStartedEvent(
                source="test", target="test", project_id="test", tasks=[]
            ),
            BaseEvent,
        )
        assert isinstance(
            InfrastructureSetupCompletedEvent(
                source="test",
                target="test",
                project_id="test",
                completed_tasks=[],
                setup_summary="test",
            ),
            BaseEvent,
        )

        # Phase 1
        assert isinstance(
            BaselineCollectionStartedEvent(
                source="test", target="test", project_id="test", tasks=[]
            ),
            BaseEvent,
        )
        assert isinstance(
            BaselineDataCollectedEvent(
                source="test",
                target="test",
                project_id="test",
                domain="test",
                metrics={},
                collection_timestamp=datetime.now(),
            ),
            BaseEvent,
        )
        assert isinstance(
            BaselineAggregationCompletedEvent(
                source="test",
                target="test",
                project_id="test",
                aggregated_data={},
                summary="test",
            ),
            BaseEvent,
        )

        # Phase 1.5
        assert isinstance(
            StrategyPlanningStartedEvent(
                source="test", target="test", project_id="test", baseline_summary={}
            ),
            BaseEvent,
        )
        assert isinstance(
            StrategyProposalReadyEvent(
                source="test", target="test", project_id="test", proposal={}
            ),
            BaseEvent,
        )
        assert isinstance(
            StrategyReviewRequestedEvent(
                source="test",
                target="test",
                project_id="test",
                proposal={},
                review_deadline=datetime.now(),
            ),
            BaseEvent,
        )
        assert isinstance(
            StrategyModifiedEvent(
                source="test", target="test", project_id="test", modifications=[]
            ),
            BaseEvent,
        )
        assert isinstance(
            StrategyApprovedEvent(
                source="test",
                target="test",
                project_id="test",
                final_strategy={},
                approval_timestamp=datetime.now(),
            ),
            BaseEvent,
        )
