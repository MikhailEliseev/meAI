"""Email Scheduler with APScheduler

Cron job for processing scheduled emails at regular intervals.

Part of: Phase 11 Sprint 2 - Task 2.4
"""

import logging
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.aim.services.email.workflow_engine import WorkflowEngine

logger = logging.getLogger(__name__)


class EmailScheduler:
    """Manages scheduled email processing with APScheduler.

    Responsibilities:
    - Run cron job to process due emails
    - Handle scheduler lifecycle (start/stop)
    - Error handling and logging

    Example:
        scheduler = EmailScheduler(session_factory)
        await scheduler.start()
        # ... application runs ...
        await scheduler.stop()
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        cron_expression: str = "*/5 * * * *",  # Every 5 minutes
    ):
        """Initialize email scheduler.

        Args:
            session_factory: SQLAlchemy async session factory
            cron_expression: Cron expression for job frequency
                            Default: "*/5 * * * *" (every 5 minutes)
        """
        self.session_factory = session_factory
        self.cron_expression = cron_expression
        self.scheduler: Optional[AsyncIOScheduler] = None

    async def start(self) -> None:
        """Start the scheduler.

        Creates APScheduler instance and adds email processing job.
        """
        if self.scheduler is not None:
            logger.warning("Scheduler already started")
            return

        logger.info("Starting email scheduler")

        # Create scheduler
        self.scheduler = AsyncIOScheduler()

        # Add email processing job
        self.scheduler.add_job(
            self._process_emails_job,
            trigger=CronTrigger.from_crontab(self.cron_expression),
            id="process_scheduled_emails",
            name="Process Scheduled Emails",
            replace_existing=True,
            max_instances=1,  # Prevent concurrent runs
        )

        # Start scheduler
        self.scheduler.start()
        logger.info(
            f"Email scheduler started with cron: {self.cron_expression}"
        )

    async def stop(self) -> None:
        """Stop the scheduler gracefully."""
        if self.scheduler is None:
            logger.warning("Scheduler not started")
            return

        logger.info("Stopping email scheduler")
        self.scheduler.shutdown(wait=True)
        self.scheduler = None
        logger.info("Email scheduler stopped")

    async def _process_emails_job(self) -> None:
        """Process scheduled emails (cron job).

        Finds emails due for sending and marks them as ready.
        Actual sending happens in EmailSender service.
        """
        logger.info("Running scheduled email processing job")

        try:
            # Create database session
            async with self.session_factory() as session:
                engine = WorkflowEngine(session)

                # Process due emails
                ready_emails = await engine.process_scheduled_emails(
                    batch_size=100
                )

                if ready_emails:
                    logger.info(
                        f"Processed {len(ready_emails)} scheduled emails"
                    )
                    for email in ready_emails:
                        logger.debug(
                            f"Email ready: {email.id} to {email.recipient_email}"
                        )
                else:
                    logger.debug("No emails due for sending")

        except Exception as e:
            logger.error(f"Error processing scheduled emails: {e}", exc_info=True)

    async def trigger_manual_run(self) -> None:
        """Manually trigger email processing (for testing/debugging).

        Raises:
            RuntimeError: If scheduler not started
        """
        if self.scheduler is None:
            raise RuntimeError("Scheduler not started")

        logger.info("Manually triggering email processing")
        await self._process_emails_job()

    def is_running(self) -> bool:
        """Check if scheduler is running.

        Returns:
            True if scheduler is running, False otherwise
        """
        return self.scheduler is not None and self.scheduler.running

    def get_next_run_time(self) -> Optional[str]:
        """Get next scheduled run time.

        Returns:
            ISO format timestamp of next run, or None if not scheduled
        """
        if self.scheduler is None:
            return None

        job = self.scheduler.get_job("process_scheduled_emails")
        if job and job.next_run_time:
            return job.next_run_time.isoformat()

        return None


# Singleton instance for application-wide use
_scheduler_instance: Optional[EmailScheduler] = None


def get_scheduler() -> Optional[EmailScheduler]:
    """Get global scheduler instance.

    Returns:
        EmailScheduler instance or None if not initialized
    """
    return _scheduler_instance


def init_scheduler(
    session_factory: async_sessionmaker[AsyncSession],
    cron_expression: str = "*/5 * * * *",
) -> EmailScheduler:
    """Initialize global scheduler instance.

    Args:
        session_factory: SQLAlchemy async session factory
        cron_expression: Cron expression for job frequency

    Returns:
        Initialized EmailScheduler instance
    """
    global _scheduler_instance

    if _scheduler_instance is not None:
        logger.warning("Scheduler already initialized")
        return _scheduler_instance

    _scheduler_instance = EmailScheduler(session_factory, cron_expression)
    return _scheduler_instance


async def start_scheduler() -> None:
    """Start global scheduler instance.

    Raises:
        RuntimeError: If scheduler not initialized
    """
    if _scheduler_instance is None:
        raise RuntimeError(
            "Scheduler not initialized. Call init_scheduler() first."
        )

    await _scheduler_instance.start()


async def stop_scheduler() -> None:
    """Stop global scheduler instance.

    Raises:
        RuntimeError: If scheduler not initialized
    """
    if _scheduler_instance is None:
        raise RuntimeError(
            "Scheduler not initialized. Call init_scheduler() first."
        )

    await _scheduler_instance.stop()
