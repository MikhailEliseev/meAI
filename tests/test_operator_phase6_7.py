"""Tests for Operator Phase 6-7: Quality Validation and Comprehensive Reporting"""

import asyncio
import pytest
import pytest_asyncio
from datetime import datetime, timezone
from meai.agents.operator import Operator, Task, TaskStatus


@pytest_asyncio.fixture
async def operator():
    """Create Operator instance for testing"""
    op = Operator(
        database_url="sqlite+aiosqlite:///:memory:",
        vault_path="./test_vault"
    )
    await op.initialize()
    yield op
    await op.shutdown()


@pytest.mark.asyncio
async def test_phase6_quality_validation_success(operator):
    """Test Phase 6: Quality validation with successful results"""
    task_id = "test-task-1"

    # Mock results (all successful)
    results = [
        {
            "subtask_id": "sub-1",
            "agent_id": "seo-magister-1",
            "action": "analyze_keywords",
            "description": "Analyze keywords",
            "result": {
                "status": "success",
                "data": {"keywords": ["test", "seo"]},
                "insights": ["Found 2 keywords"]
            },
            "completed_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "subtask_id": "sub-2",
            "agent_id": "content-magister-1",
            "action": "generate_content",
            "description": "Generate content",
            "result": {
                "status": "success",
                "data": {"content": "Test content"},
                "insights": ["Generated 100 words"]
            },
            "completed_at": datetime.now(timezone.utc).isoformat(),
        },
    ]

    # Run validation
    validation = await operator._validate_quality(task_id, results)

    # Assertions
    assert validation["passed"] is True
    assert validation["quality_score"] == 1.0
    assert validation["checks"]["completeness"]["passed"] is True
    assert validation["checks"]["accuracy"]["passed"] is True
    assert len(validation["errors"]) == 0


@pytest.mark.asyncio
async def test_phase6_quality_validation_with_errors(operator):
    """Test Phase 6: Quality validation with errors"""
    task_id = "test-task-2"

    # Mock results (with errors)
    results = [
        {
            "subtask_id": "sub-1",
            "agent_id": "seo-magister-1",
            "action": "analyze_keywords",
            "description": "Analyze keywords",
            "result": {
                "status": "error",
                "error": "API timeout",
            },
            "completed_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "subtask_id": "sub-2",
            "agent_id": "content-magister-1",
            "action": "generate_content",
            "description": "Generate content",
            "result": {},  # Empty result
            "completed_at": datetime.now(timezone.utc).isoformat(),
        },
    ]

    # Run validation
    validation = await operator._validate_quality(task_id, results)

    # Assertions
    assert validation["passed"] is False
    assert validation["quality_score"] < 1.0
    assert validation["checks"]["completeness"]["passed"] is False
    assert validation["checks"]["accuracy"]["passed"] is False
    assert len(validation["errors"]) > 0


@pytest.mark.asyncio
async def test_phase6_quality_validation_empty_results(operator):
    """Test Phase 6: Quality validation with no results"""
    task_id = "test-task-3"
    results = []

    # Run validation
    validation = await operator._validate_quality(task_id, results)

    # Assertions
    assert validation["passed"] is False
    assert "No results to validate" in validation["errors"]


@pytest.mark.asyncio
async def test_phase7_comprehensive_report_generation(operator):
    """Test Phase 7: Comprehensive report generation"""
    task_id = "test-task-4"

    # Create task
    task = Task(
        task_id=task_id,
        source="user",
        goal="Test comprehensive reporting",
        description="Test task",
        constraints=[],
        resources={},
        priority=1,
        deadline=None,
        status=TaskStatus.IN_PROGRESS,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    operator.active_tasks[task_id] = task

    # Mock results
    results = [
        {
            "subtask_id": "sub-1",
            "agent_id": "seo-magister-1",
            "action": "analyze_keywords",
            "description": "Analyze keywords",
            "result": {
                "status": "success",
                "data": {"keywords": ["test", "seo"]},
                "insights": ["Found 2 high-value keywords"],
                "summary": "Keyword analysis completed"
            },
            "completed_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "subtask_id": "sub-2",
            "agent_id": "content-magister-1",
            "action": "generate_content",
            "description": "Generate content",
            "result": {
                "status": "success",
                "data": {"content": "Test content"},
                "insights": ["Generated SEO-optimized content"],
                "summary": "Content generation completed"
            },
            "completed_at": datetime.now(timezone.utc).isoformat(),
        },
    ]

    # Mock validation result (success)
    validation_result = {
        "passed": True,
        "quality_score": 1.0,
        "checks": {
            "completeness": {"passed": True, "issues": []},
            "consistency": {"passed": True, "issues": []},
            "accuracy": {"passed": True, "issues": []},
            "magister_coverage": {"passed": True, "issues": []},
        },
        "errors": [],
        "warnings": [],
    }

    # Generate report
    report = await operator._generate_comprehensive_report(
        task_id, results, validation_result
    )

    # Assertions
    assert report.task_id == task_id
    assert "2/2" in report.summary  # 2 successful subtasks
    assert "Quality Score: 100" in report.summary
    assert len(report.insights) > 0
    assert "quality_validation" in report.metrics
    assert "magister_coverage" in report.metrics
    assert report.metrics["magister_coverage"]["total_magisters"] == 2
    assert len(report.recommendations) > 0


@pytest.mark.asyncio
async def test_phase7_report_with_failed_validation(operator):
    """Test Phase 7: Report generation with failed validation"""
    task_id = "test-task-5"

    # Create task
    task = Task(
        task_id=task_id,
        source="user",
        goal="Test failed validation reporting",
        description="Test task",
        constraints=[],
        resources={},
        priority=1,
        deadline=None,
        status=TaskStatus.IN_PROGRESS,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    operator.active_tasks[task_id] = task

    # Mock results with errors
    results = [
        {
            "subtask_id": "sub-1",
            "agent_id": "seo-magister-1",
            "action": "analyze_keywords",
            "description": "Analyze keywords",
            "result": {
                "status": "error",
                "error": "API timeout",
            },
            "completed_at": datetime.now(timezone.utc).isoformat(),
        },
    ]

    # Mock validation result (failed)
    validation_result = {
        "passed": False,
        "quality_score": 0.5,
        "checks": {
            "completeness": {"passed": False, "issues": ["Missing data"]},
            "consistency": {"passed": True, "issues": []},
            "accuracy": {"passed": False, "issues": ["API timeout error"]},
            "magister_coverage": {"passed": True, "issues": []},
        },
        "errors": ["Missing data", "API timeout error"],
        "warnings": [],
    }

    # Generate report
    report = await operator._generate_comprehensive_report(
        task_id, results, validation_result
    )

    # Assertions
    assert report.task_id == task_id
    assert "Quality validation failed" in report.insights[0]
    assert len(report.issues) > 0
    assert "Review quality validation issues" in report.recommendations[0]
    assert report.metrics["quality_validation"]["passed"] is False


@pytest.mark.asyncio
async def test_phase7_magister_grouping(operator):
    """Test Phase 7: Results grouped by Magister"""
    task_id = "test-task-6"

    # Create task
    task = Task(
        task_id=task_id,
        source="user",
        goal="Test Magister grouping",
        description="Test task",
        constraints=[],
        resources={},
        priority=1,
        deadline=None,
        status=TaskStatus.IN_PROGRESS,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    operator.active_tasks[task_id] = task

    # Mock results from 3 different Magisters
    results = [
        {
            "subtask_id": "sub-1",
            "agent_id": "seo-magister-1",
            "action": "analyze_keywords",
            "description": "SEO task 1",
            "result": {
                "status": "success",
                "insights": ["SEO insight 1"],
            },
            "completed_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "subtask_id": "sub-2",
            "agent_id": "seo-magister-1",
            "action": "optimize_content",
            "description": "SEO task 2",
            "result": {
                "status": "success",
                "insights": ["SEO insight 2"],
            },
            "completed_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "subtask_id": "sub-3",
            "agent_id": "content-magister-1",
            "action": "generate_content",
            "description": "Content task",
            "result": {
                "status": "success",
                "insights": ["Content insight"],
            },
            "completed_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "subtask_id": "sub-4",
            "agent_id": "ads-magister-1",
            "action": "create_campaign",
            "description": "Ads task",
            "result": {
                "status": "success",
                "insights": ["Ads insight"],
            },
            "completed_at": datetime.now(timezone.utc).isoformat(),
        },
    ]

    # Mock validation result
    validation_result = {
        "passed": True,
        "quality_score": 1.0,
        "checks": {
            "completeness": {"passed": True, "issues": []},
            "consistency": {"passed": True, "issues": []},
            "accuracy": {"passed": True, "issues": []},
            "magister_coverage": {"passed": True, "issues": []},
        },
        "errors": [],
        "warnings": [],
    }

    # Generate report
    report = await operator._generate_comprehensive_report(
        task_id, results, validation_result
    )

    # Assertions
    assert report.metrics["magister_coverage"]["total_magisters"] == 3
    assert "seo-magister-1" in report.metrics["magister_coverage"]["magisters"]
    assert "content-magister-1" in report.metrics["magister_coverage"]["magisters"]
    assert "ads-magister-1" in report.metrics["magister_coverage"]["magisters"]
    assert report.metrics["magister_coverage"]["subtasks_per_magister"]["seo-magister-1"] == 2
    assert report.metrics["magister_coverage"]["subtasks_per_magister"]["content-magister-1"] == 1
    assert report.metrics["magister_coverage"]["subtasks_per_magister"]["ads-magister-1"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
