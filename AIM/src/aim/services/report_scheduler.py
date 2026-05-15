"""Report scheduler service - schedules automated report generation."""

from typing import Optional, Callable, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR


logger = logging.getLogger(__name__)


@dataclass
class ScheduleConfig:
    """Configuration for report schedule."""
    project_id: str
    schedule_type: str  # 'weekly' or 'monthly'
    day_of_week: Optional[int] = None  # 0-6 (Monday-Sunday) for weekly
    day_of_month: Optional[int] = None  # 1-31 for monthly
    hour: int = 9  # Hour to send (0-23)
    minute: int = 0  # Minute to send (0-59)
    enabled: bool = True


class ReportScheduler:
    """Schedules automated report generation and delivery.

    Uses APScheduler to trigger report generation at specified intervals:
    - Weekly reports (every Monday at 9am by default)
    - Monthly reports (1st of month at 9am by default)

    Jobs are persisted to SQLite database for durability.

    Example:
        scheduler = ReportScheduler(
            database_url="sqlite:///reports.db",
            report_callback=generate_and_send_report
        )

        await scheduler.start()

        # Schedule weekly report
        await scheduler.schedule_weekly_report(
            project_id="proj-123",
            day_of_week=0,  # Monday
            hour=9,
            minute=0
        )

        # Schedule monthly report
        await scheduler.schedule_monthly_report(
            project_id="proj-456",
            day_of_month=1,  # 1st of month
            hour=9,
            minute=0
        )

        # List all schedules
        schedules = await scheduler.list_schedules()

        # Remove schedule
        await scheduler.remove_schedule(project_id="proj-123", schedule_type="weekly")

        await scheduler.shutdown()
    """

    def __init__(
        self,
        database_url: str,
        report_callback: Callable,
        timezone: str = "UTC",
    ):
        """Initialize report scheduler.

        Args:
            database_url: SQLAlchemy database URL for job persistence
            report_callback: Async function to call for report generation
                            Should accept (project_id: str, schedule_type: str)
            timezone: Timezone for scheduling (default: UTC)
        """
        self.database_url = database_url
        self.report_callback = report_callback
        self.timezone = timezone

        # Setup job store
        jobstores = {
            'default': SQLAlchemyJobStore(url=database_url)
        }

        # Setup executor
        executors = {
            'default': AsyncIOExecutor()
        }

        # Job defaults
        job_defaults = {
            'coalesce': True,  # Combine missed runs
            'max_instances': 1,  # One instance per job
            'misfire_grace_time': 3600,  # 1 hour grace period
        }

        # Create scheduler
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=timezone,
        )

        # Add event listeners
        self.scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED
        )
        self.scheduler.add_listener(
            self._job_error_listener,
            EVENT_JOB_ERROR
        )

    async def start(self) -> None:
        """Start the scheduler."""
        self.scheduler.start()
        logger.info("Report scheduler started")

    async def shutdown(self, wait: bool = True) -> None:
        """Shutdown the scheduler.

        Args:
            wait: Wait for running jobs to complete
        """
        self.scheduler.shutdown(wait=wait)
        logger.info("Report scheduler shutdown")

    async def schedule_weekly_report(
        self,
        project_id: str,
        day_of_week: int = 0,  # Monday
        hour: int = 9,
        minute: int = 0,
    ) -> str:
        """Schedule weekly report generation.

        Args:
            project_id: Project ID
            day_of_week: Day of week (0=Monday, 6=Sunday)
            hour: Hour to send (0-23)
            minute: Minute to send (0-59)

        Returns:
            Job ID
        """
        job_id = f"weekly_{project_id}"

        # Create cron trigger
        trigger = CronTrigger(
            day_of_week=day_of_week,
            hour=hour,
            minute=minute,
            timezone=self.timezone,
        )

        # Add job
        job = self.scheduler.add_job(
            self.report_callback,
            trigger=trigger,
            args=[project_id, "weekly"],
            id=job_id,
            name=f"Weekly report for {project_id}",
            replace_existing=True,
        )

        logger.info(
            f"Scheduled weekly report for {project_id}: "
            f"day_of_week={day_of_week}, hour={hour}, minute={minute}"
        )

        return job.id

    async def schedule_monthly_report(
        self,
        project_id: str,
        day_of_month: int = 1,
        hour: int = 9,
        minute: int = 0,
    ) -> str:
        """Schedule monthly report generation.

        Args:
            project_id: Project ID
            day_of_month: Day of month (1-31)
            hour: Hour to send (0-23)
            minute: Minute to send (0-59)

        Returns:
            Job ID
        """
        job_id = f"monthly_{project_id}"

        # Create cron trigger
        trigger = CronTrigger(
            day=day_of_month,
            hour=hour,
            minute=minute,
            timezone=self.timezone,
        )

        # Add job
        job = self.scheduler.add_job(
            self.report_callback,
            trigger=trigger,
            args=[project_id, "monthly"],
            id=job_id,
            name=f"Monthly report for {project_id}",
            replace_existing=True,
        )

        logger.info(
            f"Scheduled monthly report for {project_id}: "
            f"day={day_of_month}, hour={hour}, minute={minute}"
        )

        return job.id

    async def remove_schedule(
        self,
        project_id: str,
        schedule_type: str,
    ) -> bool:
        """Remove a scheduled report.

        Args:
            project_id: Project ID
            schedule_type: 'weekly' or 'monthly'

        Returns:
            True if removed, False if not found
        """
        job_id = f"{schedule_type}_{project_id}"

        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed {schedule_type} schedule for {project_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to remove schedule {job_id}: {e}")
            return False

    async def pause_schedule(
        self,
        project_id: str,
        schedule_type: str,
    ) -> bool:
        """Pause a scheduled report.

        Args:
            project_id: Project ID
            schedule_type: 'weekly' or 'monthly'

        Returns:
            True if paused, False if not found
        """
        job_id = f"{schedule_type}_{project_id}"

        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Paused {schedule_type} schedule for {project_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to pause schedule {job_id}: {e}")
            return False

    async def resume_schedule(
        self,
        project_id: str,
        schedule_type: str,
    ) -> bool:
        """Resume a paused schedule.

        Args:
            project_id: Project ID
            schedule_type: 'weekly' or 'monthly'

        Returns:
            True if resumed, False if not found
        """
        job_id = f"{schedule_type}_{project_id}"

        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Resumed {schedule_type} schedule for {project_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to resume schedule {job_id}: {e}")
            return False

    async def list_schedules(self) -> List[Dict[str, Any]]:
        """List all scheduled reports.

        Returns:
            List of schedule information
        """
        jobs = self.scheduler.get_jobs()

        schedules = []
        for job in jobs:
            # Parse job ID
            parts = job.id.split('_', 1)
            if len(parts) != 2:
                continue

            schedule_type, project_id = parts

            # Get next run time
            next_run = job.next_run_time

            schedules.append({
                'project_id': project_id,
                'schedule_type': schedule_type,
                'next_run': next_run.isoformat() if next_run else None,
                'enabled': not job.next_run_time is None,
                'trigger': str(job.trigger),
            })

        return schedules

    async def get_schedule(
        self,
        project_id: str,
        schedule_type: str,
    ) -> Optional[Dict[str, Any]]:
        """Get schedule information for a project.

        Args:
            project_id: Project ID
            schedule_type: 'weekly' or 'monthly'

        Returns:
            Schedule information or None if not found
        """
        job_id = f"{schedule_type}_{project_id}"

        try:
            job = self.scheduler.get_job(job_id)
            if not job:
                return None

            return {
                'project_id': project_id,
                'schedule_type': schedule_type,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'enabled': job.next_run_time is not None,
                'trigger': str(job.trigger),
            }
        except Exception as e:
            logger.warning(f"Failed to get schedule {job_id}: {e}")
            return None

    async def trigger_now(
        self,
        project_id: str,
        schedule_type: str,
    ) -> bool:
        """Trigger report generation immediately (outside schedule).

        Args:
            project_id: Project ID
            schedule_type: 'weekly' or 'monthly'

        Returns:
            True if triggered, False if failed
        """
        try:
            await self.report_callback(project_id, schedule_type)
            logger.info(f"Manually triggered {schedule_type} report for {project_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to trigger report for {project_id}: {e}")
            return False

    def _job_executed_listener(self, event) -> None:
        """Handle job execution event."""
        logger.info(
            f"Job {event.job_id} executed successfully at {event.scheduled_run_time}"
        )

    def _job_error_listener(self, event) -> None:
        """Handle job error event."""
        logger.error(
            f"Job {event.job_id} failed: {event.exception}",
            exc_info=event.exception
        )
