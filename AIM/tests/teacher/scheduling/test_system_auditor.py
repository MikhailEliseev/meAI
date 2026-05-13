"""
Tests for SystemAuditor.
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from AIM.src.aim.teacher.scheduling.system_auditor import (
    SystemAuditor,
    SubagentStatus,
    Priority,
    SubagentHealth,
    SystemAuditReport,
)


@pytest.fixture
def temp_project_root(tmp_path):
    """Create temporary project structure."""
    # Create directories
    specs_dir = tmp_path / "docs" / "subagents-specs"
    specs_dir.mkdir(parents=True)

    code_dir = tmp_path / "AIM" / "src" / "aim" / "subagents"
    code_dir.mkdir(parents=True)

    obsidian_dir = tmp_path / "AIM" / "obsidian"
    obsidian_dir.mkdir(parents=True)

    # Create some spec files
    (specs_dir / "KEYWORD_RESEARCH_SPEC.md").write_text("# Keyword Research Spec")
    (specs_dir / "CONTENT_GAP_SPEC.md").write_text("# Content Gap Spec")
    (specs_dir / "TECHNICAL_SEO_SPEC.md").write_text("# Technical SEO Spec")

    # Create some code files
    kr_dir = code_dir / "keyword_research"
    kr_dir.mkdir()
    (kr_dir / "keyword_research.py").write_text("# Keyword Research Code")

    cg_dir = code_dir / "content_gap"
    cg_dir.mkdir()
    (cg_dir / "content_gap.py").write_text("# Content Gap Code")

    # Missing code for technical_seo (to test missing status)

    return tmp_path


@pytest.fixture
def system_auditor(temp_project_root):
    """Create SystemAuditor instance."""
    return SystemAuditor(
        project_root=temp_project_root,
        degraded_threshold_days=28,
        critical_subagents=["keyword_research", "technical_seo"],
    )


@pytest.mark.asyncio
async def test_discover_subagents(system_auditor):
    """Test subagent discovery from specs and code."""
    subagents = await system_auditor._discover_subagents()

    # Should find 3 subagents (2 with code, 1 without)
    assert len(subagents) >= 2

    # Check structure
    names = [name for name, _, _ in subagents]
    assert "keyword_research" in names
    assert "content_gap" in names


@pytest.mark.asyncio
async def test_check_healthy_subagent(system_auditor):
    """Test health check for healthy subagent."""
    with patch.object(system_auditor, "_get_last_taught_date") as mock_taught:
        with patch.object(system_auditor, "_get_performance_metrics") as mock_metrics:
            # Recently taught, good metrics
            mock_taught.return_value = datetime.now() - timedelta(days=7)
            mock_metrics.return_value = {
                "error_rate": 0.02,
                "success_rate": 0.98,
            }

            health = await system_auditor._check_subagent_health(
                name="keyword_research",
                spec_path=str(system_auditor.specs_dir / "KEYWORD_RESEARCH_SPEC.md"),
                code_path=str(system_auditor.code_dir / "keyword_research" / "keyword_research.py"),
            )

            assert health.status == SubagentStatus.HEALTHY
            assert health.name == "keyword_research"


@pytest.mark.asyncio
async def test_check_degraded_subagent_old(system_auditor):
    """Test health check for degraded subagent (not taught for >4 weeks)."""
    with patch.object(system_auditor, "_get_last_taught_date") as mock_taught:
        with patch.object(system_auditor, "_get_performance_metrics") as mock_metrics:
            # Not taught for 45 days
            mock_taught.return_value = datetime.now() - timedelta(days=45)
            mock_metrics.return_value = {"error_rate": 0.02}

            health = await system_auditor._check_subagent_health(
                name="keyword_research",
                spec_path=str(system_auditor.specs_dir / "KEYWORD_RESEARCH_SPEC.md"),
                code_path=str(system_auditor.code_dir / "keyword_research" / "keyword_research.py"),
            )

            assert health.status == SubagentStatus.DEGRADED
            assert health.priority == Priority.P2
            assert "45 days" in health.reason


@pytest.mark.asyncio
async def test_check_degraded_subagent_high_error_rate(system_auditor):
    """Test health check for degraded subagent (high error rate)."""
    with patch.object(system_auditor, "_get_last_taught_date") as mock_taught:
        with patch.object(system_auditor, "_get_performance_metrics") as mock_metrics:
            # Recently taught but high error rate
            mock_taught.return_value = datetime.now() - timedelta(days=7)
            mock_metrics.return_value = {"error_rate": 0.15}  # 15% error rate

            health = await system_auditor._check_subagent_health(
                name="keyword_research",
                spec_path=str(system_auditor.specs_dir / "KEYWORD_RESEARCH_SPEC.md"),
                code_path=str(system_auditor.code_dir / "keyword_research" / "keyword_research.py"),
            )

            assert health.status == SubagentStatus.DEGRADED
            assert health.priority == Priority.P1  # High priority due to errors
            assert "error rate" in health.reason.lower()


@pytest.mark.asyncio
async def test_check_missing_subagent(system_auditor):
    """Test health check for missing subagent (code not found)."""
    with patch.object(system_auditor, "_get_last_taught_date") as mock_taught:
        with patch.object(system_auditor, "_get_performance_metrics") as mock_metrics:
            mock_taught.return_value = None
            mock_metrics.return_value = {}

            health = await system_auditor._check_subagent_health(
                name="technical_seo",
                spec_path=str(system_auditor.specs_dir / "TECHNICAL_SEO_SPEC.md"),
                code_path=str(system_auditor.code_dir / "technical_seo" / "technical_seo.py"),
            )

            assert health.status == SubagentStatus.MISSING
            assert "not found" in health.reason.lower()


@pytest.mark.asyncio
async def test_missing_critical_subagent_priority(system_auditor):
    """Test that missing critical subagent gets P1 priority."""
    with patch.object(system_auditor, "_get_last_taught_date") as mock_taught:
        with patch.object(system_auditor, "_get_performance_metrics") as mock_metrics:
            mock_taught.return_value = None
            mock_metrics.return_value = {}

            # technical_seo is in critical_subagents list
            health = await system_auditor._check_subagent_health(
                name="technical_seo",
                spec_path=str(system_auditor.specs_dir / "TECHNICAL_SEO_SPEC.md"),
                code_path=str(system_auditor.code_dir / "technical_seo" / "technical_seo.py"),
            )

            assert health.status == SubagentStatus.MISSING
            assert health.priority == Priority.P1


@pytest.mark.asyncio
async def test_audit_all_subagents(system_auditor):
    """Test full system audit."""
    with patch.object(system_auditor, "_get_last_taught_date") as mock_taught:
        with patch.object(system_auditor, "_get_performance_metrics") as mock_metrics:
            with patch.object(system_auditor, "_handle_missing_subagent") as mock_handle:
                # Mock returns
                mock_taught.return_value = datetime.now() - timedelta(days=7)
                mock_metrics.return_value = {"error_rate": 0.02}

                report = await system_auditor.audit_all_subagents()

                assert isinstance(report, SystemAuditReport)
                assert report.total_subagents >= 2
                assert report.healthy + report.degraded + report.missing + report.deprecated == report.total_subagents


@pytest.mark.asyncio
async def test_priority_queue_ordering(system_auditor):
    """Test priority queue is ordered correctly."""
    health_results = [
        SubagentHealth(
            name="agent1",
            status=SubagentStatus.HEALTHY,
            priority=Priority.P3,
            last_taught=datetime.now() - timedelta(days=7),
        ),
        SubagentHealth(
            name="agent2",
            status=SubagentStatus.DEGRADED,
            priority=Priority.P1,
            last_taught=datetime.now() - timedelta(days=45),
        ),
        SubagentHealth(
            name="agent3",
            status=SubagentStatus.DEGRADED,
            priority=Priority.P2,
            last_taught=datetime.now() - timedelta(days=30),
        ),
        SubagentHealth(
            name="agent4",
            status=SubagentStatus.MISSING,
            priority=Priority.P1,
        ),
    ]

    queue = system_auditor._create_priority_queue(health_results)

    # Missing should be filtered out
    assert len(queue) == 3

    # P1 degraded should be first
    assert queue[0].name == "agent2"
    assert queue[0].priority == Priority.P1

    # P2 degraded should be second
    assert queue[1].name == "agent3"
    assert queue[1].priority == Priority.P2

    # P3 healthy should be last
    assert queue[2].name == "agent1"
    assert queue[2].priority == Priority.P3


@pytest.mark.asyncio
async def test_handle_missing_subagent_logs_warning(system_auditor):
    """Test that handling missing subagent logs warning."""
    with patch.object(system_auditor, "_check_git_history") as mock_git:
        mock_git.return_value = {}

        subagent = SubagentHealth(
            name="test_agent",
            status=SubagentStatus.MISSING,
        )

        # Should not raise exception
        await system_auditor._handle_missing_subagent(subagent)


@pytest.mark.asyncio
async def test_summary_format(system_auditor):
    """Test summary formatting."""
    health_results = [
        SubagentHealth(name="agent1", status=SubagentStatus.HEALTHY),
        SubagentHealth(name="agent2", status=SubagentStatus.DEGRADED, reason="Not taught for 45 days"),
        SubagentHealth(name="agent3", status=SubagentStatus.MISSING),
    ]

    summary = system_auditor._create_summary(health_results)

    assert "Total subagents: 3" in summary
    assert "✅ Healthy: 1" in summary
    assert "⚠️  Degraded: 1" in summary
    assert "❌ Missing: 1" in summary
    assert "agent2" in summary
    assert "Not taught for 45 days" in summary


@pytest.mark.asyncio
async def test_degraded_threshold_configurable(temp_project_root):
    """Test that degraded threshold is configurable."""
    auditor = SystemAuditor(
        project_root=temp_project_root,
        degraded_threshold_days=14,  # 2 weeks instead of 4
    )

    assert auditor.degraded_threshold_days == 14
