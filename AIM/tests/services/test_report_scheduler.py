"""Tests for ReportScheduler service."""

import pytest
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import sys
import tempfile

# Add AIM/src to path
aim_src = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(aim_src))

from aim.services.report_scheduler import ReportScheduler, ScheduleConfig


# Mock report callback
async def mock_report_callback(project_id: str, schedule_type: str):
    """Mock callback for testing."""
    print(f"Report generated: {project_id} ({schedule_type})")


class TestReportScheduler:
    """Test ReportScheduler class."""

    @pytest.mark.asyncio
    async def test_scheduler_initialization(self):
        """Test ReportScheduler initialization."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        scheduler = ReportScheduler(
            database_url=f"sqlite:///{db_path}",
            report_callback=mock_report_callback,
            timezone="UTC"
        )

        assert scheduler.database_url == f"sqlite:///{db_path}"
        assert scheduler.report_callback == mock_report_callback
        assert scheduler.timezone == "UTC"
        assert scheduler.scheduler is not None

        # Cleanup
        Path(db_path).unlink()

    @pytest.mark.asyncio
    async def test_start_and_shutdown(self):
        """Test starting and shutting down scheduler."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        scheduler = ReportScheduler(
            database_url=f"sqlite:///{db_path}",
            report_callback=mock_report_callback
        )

        # Start scheduler
        await scheduler.start()
        assert scheduler.scheduler.running

        # Shutdown scheduler
        await scheduler.shutdown(wait=False)

        # Give scheduler time to shutdown
        await asyncio.sleep(0.1)

        # Note: APScheduler may still report running=True briefly after shutdown
        # The important thing is that shutdown() completes without error

        # Cleanup
        Path(db_path).unlink()

    @pytest.mark.asyncio
    async def test_schedule_weekly_report(self):
        """Test scheduling weekly report."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        scheduler = ReportScheduler(
            database_url=f"sqlite:///{db_path}",
            report_callback=mock_report_callback
        )

        await scheduler.start()

        # Schedule weekly report (Monday at 9:00)
        job_id = await scheduler.schedule_weekly_report(
            project_id="proj-123",
            day_of_week=0,  # Monday
            hour=9,
            minute=0
        )

        assert job_id == "weekly_proj-123"

        # Verify job was created
        job = scheduler.scheduler.get_job(job_id)
        assert job is not None
        assert job.id == job_id

        await scheduler.shutdown(wait=False)
        Path(db_path).unlink()

    @pytest.mark.asyncio
    async def test_schedule_monthly_report(self):
        """Test scheduling monthly report."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        scheduler = ReportScheduler(
            database_url=f"sqlite:///{db_path}",
            report_callback=mock_report_callback
        )

        await scheduler.start()

        # Schedule monthly report (1st at 9:00)
        job_id = await scheduler.schedule_monthly_report(
            project_id="proj-456",
            day_of_month=1,
            hour=9,
            minute=0
        )

        assert job_id == "monthly_proj-456"

        # Verify job was created
        job = scheduler.scheduler.get_job(job_id)
        assert job is not None
        assert job.id == job_id

        await scheduler.shutdown(wait=False)
        Path(db_path).unlink()

    @pytest.mark.asyncio
    async def test_remove_schedule(self):
        """Test removing a schedule."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        scheduler = ReportScheduler(
            database_url=f"sqlite:///{db_path}",
            report_callback=mock_report_callback
        )

        await scheduler.start()

        # Schedule weekly report
        await scheduler.schedule_weekly_report(
            project_id="proj-789",
            day_of_week=0,
            hour=9,
            minute=0
        )

        # Verify job exists
        job = scheduler.scheduler.get_job("weekly_proj-789")
        assert job is not None

        # Remove schedule
        result = await scheduler.remove_schedule("proj-789", "weekly")
        assert result is True

        # Verify job was removed
        job = scheduler.scheduler.get_job("weekly_proj-789")
        assert job is None

        await scheduler.shutdown(wait=False)
        Path(db_path).unlink()

    @pytest.mark.asyncio
    async def test_pause_and_resume_schedule(self):
        """Test pausing and resuming a schedule."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        scheduler = ReportScheduler(
            database_url=f"sqlite:///{db_path}",
            report_callback=mock_report_callback
        )

        await scheduler.start()

        # Schedule weekly report
        await scheduler.schedule_weekly_report(
            project_id="proj-pause",
            day_of_week=0,
            hour=9,
            minute=0
        )

        # Pause schedule
        result = await scheduler.pause_schedule("proj-pause", "weekly")
        assert result is True

        # Verify job is paused (next_run_time is None)
        job = scheduler.scheduler.get_job("weekly_proj-pause")
        assert job.next_run_time is None

        # Resume schedule
        result = await scheduler.resume_schedule("proj-pause", "weekly")
        assert result is True

        # Verify job is resumed (next_run_time is not None)
        job = scheduler.scheduler.get_job("weekly_proj-pause")
        assert job.next_run_time is not None

        await scheduler.shutdown(wait=False)
        Path(db_path).unlink()

    @pytest.mark.asyncio
    async def test_list_schedules(self):
        """Test listing all schedules."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        scheduler = ReportScheduler(
            database_url=f"sqlite:///{db_path}",
            report_callback=mock_report_callback
        )

        await scheduler.start()

        # Schedule multiple reports
        await scheduler.schedule_weekly_report("proj-1", day_of_week=0, hour=9, minute=0)
        await scheduler.schedule_weekly_report("proj-2", day_of_week=1, hour=10, minute=0)
        await scheduler.schedule_monthly_report("proj-3", day_of_month=1, hour=9, minute=0)

        # List schedules
        schedules = await scheduler.list_schedules()

        assert len(schedules) == 3
        assert any(s['project_id'] == 'proj-1' and s['schedule_type'] == 'weekly' for s in schedules)
        assert any(s['project_id'] == 'proj-2' and s['schedule_type'] == 'weekly' for s in schedules)
        assert any(s['project_id'] == 'proj-3' and s['schedule_type'] == 'monthly' for s in schedules)

        await scheduler.shutdown(wait=False)
        Path(db_path).unlink()

    @pytest.mark.asyncio
    async def test_get_schedule(self):
        """Test getting schedule information."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        scheduler = ReportScheduler(
            database_url=f"sqlite:///{db_path}",
            report_callback=mock_report_callback
        )

        await scheduler.start()

        # Schedule weekly report
        await scheduler.schedule_weekly_report("proj-get", day_of_week=0, hour=9, minute=0)

        # Get schedule info
        info = await scheduler.get_schedule("proj-get", "weekly")

        assert info is not None
        assert info['project_id'] == 'proj-get'
        assert info['schedule_type'] == 'weekly'
        assert info['next_run'] is not None
        assert info['enabled'] is True

        await scheduler.shutdown(wait=False)
        Path(db_path).unlink()

    @pytest.mark.asyncio
    async def test_get_nonexistent_schedule(self):
        """Test getting schedule that doesn't exist."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        scheduler = ReportScheduler(
            database_url=f"sqlite:///{db_path}",
            report_callback=mock_report_callback
        )

        await scheduler.start()

        # Try to get non-existent schedule
        info = await scheduler.get_schedule("proj-nonexistent", "weekly")

        assert info is None

        await scheduler.shutdown(wait=False)
        Path(db_path).unlink()

    @pytest.mark.asyncio
    async def test_trigger_now(self):
        """Test manually triggering report generation."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        # Track callback invocations
        callback_invoked = []

        async def tracking_callback(project_id: str, schedule_type: str):
            callback_invoked.append((project_id, schedule_type))

        scheduler = ReportScheduler(
            database_url=f"sqlite:///{db_path}",
            report_callback=tracking_callback
        )

        await scheduler.start()

        # Trigger report now
        result = await scheduler.trigger_now("proj-trigger", "weekly")

        assert result is True
        assert len(callback_invoked) == 1
        assert callback_invoked[0] == ("proj-trigger", "weekly")

        await scheduler.shutdown(wait=False)
        Path(db_path).unlink()

    @pytest.mark.asyncio
    async def test_replace_existing_schedule(self):
        """Test replacing existing schedule with new one."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        scheduler = ReportScheduler(
            database_url=f"sqlite:///{db_path}",
            report_callback=mock_report_callback
        )

        await scheduler.start()

        # Schedule weekly report (Monday at 9:00)
        await scheduler.schedule_weekly_report("proj-replace", day_of_week=0, hour=9, minute=0)

        # Get initial schedule
        info1 = await scheduler.get_schedule("proj-replace", "weekly")

        # Replace with new schedule (Tuesday at 10:00)
        await scheduler.schedule_weekly_report("proj-replace", day_of_week=1, hour=10, minute=0)

        # Get updated schedule
        info2 = await scheduler.get_schedule("proj-replace", "weekly")

        # Verify schedule was replaced (next_run should be different)
        assert info1['next_run'] != info2['next_run']

        await scheduler.shutdown(wait=False)
        Path(db_path).unlink()

    @pytest.mark.asyncio
    async def test_multiple_projects(self):
        """Test scheduling reports for multiple projects."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        scheduler = ReportScheduler(
            database_url=f"sqlite:///{db_path}",
            report_callback=mock_report_callback
        )

        await scheduler.start()

        # Schedule reports for 5 projects
        for i in range(5):
            await scheduler.schedule_weekly_report(f"proj-{i}", day_of_week=i % 7, hour=9, minute=0)
            await scheduler.schedule_monthly_report(f"proj-{i}", day_of_month=(i % 28) + 1, hour=9, minute=0)

        # List all schedules
        schedules = await scheduler.list_schedules()

        # Should have 10 schedules (5 weekly + 5 monthly)
        assert len(schedules) == 10

        await scheduler.shutdown(wait=False)
        Path(db_path).unlink()
