"""Email Sender with SendGrid Integration

Sends emails via SendGrid API with retry logic and tracking.

Part of: Phase 11 Sprint 2 - Task 2.4
"""

import logging
from typing import Optional
from uuid import UUID

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, TrackingSettings, ClickTracking, OpenTracking
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aim.models import ScheduledEmail
from aim.services.email.workflow_state_manager import WorkflowStateManager

logger = logging.getLogger(__name__)


class EmailSender:
    """Sends emails via SendGrid with tracking and error handling.

    Responsibilities:
    - Send emails via SendGrid API
    - Track SendGrid message IDs
    - Handle SendGrid errors with retry
    - Update email status after sending

    Example:
        sender = EmailSender(api_key="SG.xxx", db_session)
        await sender.send_email(email_id)
    """

    def __init__(
        self,
        api_key: str,
        db: AsyncSession,
        from_email: str = "me@iamaim.ru",
        from_name: str = "Михаил Елисеев | AIM Agency",
        max_retries: int = 3,
    ):
        """Initialize email sender.

        Args:
            api_key: SendGrid API key
            db: Database session
            from_email: Sender email address
            from_name: Sender display name
            max_retries: Max retry attempts for failed sends
        """
        self.api_key = api_key
        self.db = db
        self.from_email = from_email
        self.from_name = from_name
        self.max_retries = max_retries
        self.client = SendGridAPIClient(api_key)
        self.state_manager = WorkflowStateManager(db)

    async def send_email(self, email_id: UUID) -> bool:
        """Send a scheduled email via SendGrid.

        Args:
            email_id: ScheduledEmail UUID

        Returns:
            True if sent successfully, False otherwise

        Raises:
            ValueError: If email not found
        """
        # Load email
        result = await self.db.execute(
            select(ScheduledEmail).where(ScheduledEmail.id == email_id)
        )
        email = result.scalar_one_or_none()
        if not email:
            raise ValueError(f"Email not found: {email_id}")

        # Check if already sent
        if email.status == "sent":
            logger.warning(f"Email {email_id} already sent")
            return True

        # Check retry limit
        if email.retry_count >= self.max_retries:
            logger.error(
                f"Email {email_id} exceeded max retries ({self.max_retries})"
            )
            await self.state_manager.update_on_email_failed(
                email_id, f"Exceeded max retries ({self.max_retries})"
            )
            return False

        try:
            # Create SendGrid message
            message = Mail(
                from_email=(self.from_email, self.from_name),
                to_emails=email.recipient_email,
                subject=email.subject,
                html_content=email.html_content,
                plain_text_content=email.text_content,
            )

            # Enable tracking
            message.tracking_settings = TrackingSettings(
                click_tracking=ClickTracking(enable=True, enable_text=False),
                open_tracking=OpenTracking(enable=True),
            )

            # Add custom args for webhook tracking
            message.custom_arg = [
                {"email_id": str(email_id)},
                {"workflow_id": str(email.workflow_id)},
            ]

            # Send via SendGrid
            response = self.client.send(message)

            # Check response
            if response.status_code in (200, 201, 202):
                # Extract message ID from headers
                sendgrid_message_id = response.headers.get("X-Message-Id")

                # Update email record
                email.sendgrid_message_id = sendgrid_message_id

                # Update workflow state
                await self.state_manager.update_on_email_sent(email_id)

                logger.info(
                    f"Email {email_id} sent successfully to {email.recipient_email}"
                )
                return True
            else:
                # SendGrid error
                error_msg = f"SendGrid error: {response.status_code} - {response.body}"
                logger.error(error_msg)
                await self.state_manager.update_on_email_failed(
                    email_id, error_msg
                )
                return False

        except Exception as e:
            # Network or other error
            error_msg = f"Failed to send email: {str(e)}"
            logger.error(error_msg, exc_info=True)
            await self.state_manager.update_on_email_failed(email_id, error_msg)
            return False

    async def send_batch(self, email_ids: list[UUID]) -> dict[str, int]:
        """Send multiple emails in batch.

        Args:
            email_ids: List of ScheduledEmail UUIDs

        Returns:
            Dict with counts: {"sent": N, "failed": M}
        """
        results = {"sent": 0, "failed": 0}

        for email_id in email_ids:
            try:
                success = await self.send_email(email_id)
                if success:
                    results["sent"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                logger.error(
                    f"Error sending email {email_id}: {e}", exc_info=True
                )
                results["failed"] += 1

        logger.info(
            f"Batch send complete: {results['sent']} sent, {results['failed']} failed"
        )
        return results

    async def send_test_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str,
    ) -> bool:
        """Send a test email (not tracked in database).

        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML body
            text_content: Plain text body

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            message = Mail(
                from_email=(self.from_email, self.from_name),
                to_emails=to_email,
                subject=subject,
                html_content=html_content,
                plain_text_content=text_content,
            )

            response = self.client.send(message)

            if response.status_code in (200, 201, 202):
                logger.info(f"Test email sent to {to_email}")
                return True
            else:
                logger.error(
                    f"Test email failed: {response.status_code} - {response.body}"
                )
                return False

        except Exception as e:
            logger.error(f"Test email error: {e}", exc_info=True)
            return False

    async def get_send_statistics(self) -> dict:
        """Get email sending statistics.

        Returns:
            Dict with counts by status
        """
        result = await self.db.execute(select(ScheduledEmail))
        emails = result.scalars().all()

        stats = {
            "total": len(emails),
            "pending": sum(1 for e in emails if e.status == "pending"),
            "sent": sum(1 for e in emails if e.status == "sent"),
            "failed": sum(1 for e in emails if e.status == "failed"),
            "cancelled": sum(1 for e in emails if e.status == "cancelled"),
        }

        # Calculate retry stats
        retried_emails = [e for e in emails if e.retry_count > 0]
        stats["retried"] = len(retried_emails)
        stats["avg_retries"] = (
            sum(e.retry_count for e in retried_emails) / len(retried_emails)
            if retried_emails
            else 0.0
        )

        return stats

    def validate_api_key(self) -> bool:
        """Validate SendGrid API key.

        Returns:
            True if API key is valid, False otherwise
        """
        try:
            # Try to get API key info
            response = self.client.client.api_keys.get()
            return response.status_code == 200
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return False
