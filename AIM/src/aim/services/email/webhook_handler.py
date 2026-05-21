"""SendGrid Webhook Handler

Processes webhook events from SendGrid for email tracking.

Part of: Phase 11 Sprint 2 - Task 2.4
"""

import hashlib
import hmac
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from aim.services.email.workflow_state_manager import WorkflowStateManager

logger = logging.getLogger(__name__)


class WebhookHandler:
    """Handles SendGrid webhook events for email tracking.

    Responsibilities:
    - Verify webhook signatures (security)
    - Parse SendGrid event payloads
    - Record events in database
    - Update workflow state based on events

    SendGrid Event Types:
    - processed: Message has been received and is ready to be delivered
    - dropped: Message was dropped (invalid email, spam, etc.)
    - delivered: Message has been successfully delivered
    - deferred: Recipient's email server temporarily rejected message
    - bounce: Receiving server could not or would not accept message
    - open: Recipient has opened the HTML message
    - click: Recipient clicked on a link within the message
    - spam_report: Recipient marked message as spam
    - unsubscribe: Recipient clicked on the unsubscribe link
    - group_unsubscribe: Recipient unsubscribed from a specific group
    - group_resubscribe: Recipient resubscribed to a specific group

    Example:
        handler = WebhookHandler(db_session, webhook_secret="xxx")

        # In FastAPI endpoint:
        @app.post("/webhooks/sendgrid")
        async def sendgrid_webhook(
            request: Request,
            signature: str = Header(None, alias="X-Twilio-Email-Event-Webhook-Signature"),
            timestamp: str = Header(None, alias="X-Twilio-Email-Event-Webhook-Timestamp"),
        ):
            body = await request.body()
            events = await request.json()

            # Verify signature
            if not handler.verify_signature(body, signature, timestamp):
                raise HTTPException(status_code=401, detail="Invalid signature")

            # Process events
            await handler.process_events(events)
            return {"status": "ok"}
    """

    def __init__(
        self,
        db: AsyncSession,
        webhook_secret: Optional[str] = None,
    ):
        """Initialize webhook handler.

        Args:
            db: Database session
            webhook_secret: SendGrid webhook verification key (optional)
        """
        self.db = db
        self.webhook_secret = webhook_secret
        self.state_manager = WorkflowStateManager(db)

    def verify_signature(
        self,
        payload: bytes,
        signature: str,
        timestamp: str,
    ) -> bool:
        """Verify SendGrid webhook signature.

        Args:
            payload: Raw request body
            signature: X-Twilio-Email-Event-Webhook-Signature header
            timestamp: X-Twilio-Email-Event-Webhook-Timestamp header

        Returns:
            True if signature is valid, False otherwise
        """
        if not self.webhook_secret:
            logger.warning("Webhook secret not configured, skipping verification")
            return True

        try:
            # Construct signed payload
            signed_payload = timestamp.encode() + payload

            # Calculate expected signature
            expected_signature = hmac.new(
                self.webhook_secret.encode(),
                signed_payload,
                hashlib.sha256,
            ).hexdigest()

            # Compare signatures (constant-time comparison)
            return hmac.compare_digest(signature, expected_signature)

        except Exception as e:
            logger.error(f"Signature verification error: {e}", exc_info=True)
            return False

    async def process_events(self, events: list[dict]) -> dict[str, int]:
        """Process batch of SendGrid webhook events.

        Args:
            events: List of event dictionaries from SendGrid

        Returns:
            Dict with processing stats: {"processed": N, "failed": M}
        """
        stats = {"processed": 0, "failed": 0, "skipped": 0}

        for event in events:
            try:
                result = await self._process_single_event(event)
                if result is False:  # Explicitly skipped
                    stats["skipped"] += 1
                else:
                    stats["processed"] += 1
            except Exception as e:
                logger.error(
                    f"Error processing event: {e}",
                    exc_info=True,
                    extra={"event": event},
                )
                stats["failed"] += 1

        logger.info(
            f"Processed {stats['processed']} events, {stats['failed']} failed, {stats['skipped']} skipped"
        )
        return stats

    async def _process_single_event(self, event: dict) -> bool:
        """Process a single SendGrid event.

        Args:
            event: Event dictionary from SendGrid

        Returns:
            True if processed, False if skipped

        Raises:
            ValueError: If event is invalid or email_id not found
        """
        # Extract event data
        event_type = event.get("event")
        if not event_type:
            raise ValueError("Event type missing")

        # Get email_id from custom args
        email_id_str = event.get("email_id")
        if not email_id_str:
            logger.warning(f"Event missing email_id: {event}")
            return False  # Skip this event

        try:
            email_id = UUID(email_id_str)
        except ValueError:
            raise ValueError(f"Invalid email_id format: {email_id_str}")

        # Parse timestamp
        timestamp = event.get("timestamp")
        if timestamp:
            occurred_at = datetime.fromtimestamp(timestamp)
        else:
            occurred_at = datetime.now(timezone.utc)

        # Map SendGrid event types to our event types
        event_type_mapping = {
            "processed": "sent",
            "delivered": "delivered",
            "open": "opened",
            "click": "clicked",
            "bounce": "bounced",
            "dropped": "bounced",
            "deferred": "bounced",
            "spam_report": "complained",
            "unsubscribe": "unsubscribed",
            "group_unsubscribe": "unsubscribed",
        }

        mapped_event_type = event_type_mapping.get(event_type)
        if not mapped_event_type:
            logger.warning(f"Unknown event type: {event_type}")
            return False  # Skip unknown event types

        # Extract relevant event data
        event_data = {
            "sendgrid_event": event_type,
            "email": event.get("email"),
            "reason": event.get("reason"),
            "response": event.get("response"),
            "url": event.get("url"),  # For click events
            "useragent": event.get("useragent"),
            "ip": event.get("ip"),
        }

        # Remove None values
        event_data = {k: v for k, v in event_data.items() if v is not None}

        # Record event
        await self.state_manager.record_email_event(
            email_id=email_id,
            event_type=mapped_event_type,
            event_data=event_data,
        )

        logger.debug(
            f"Recorded {mapped_event_type} event for email {email_id}"
        )

        return True  # Successfully processed

    async def get_webhook_statistics(self) -> dict:
        """Get webhook processing statistics.

        Returns:
            Dict with event counts by type
        """
        from aim.models import EmailEvent
        from sqlalchemy import func, select

        # Count events by type
        result = await self.db.execute(
            select(
                EmailEvent.event_type,
                func.count(EmailEvent.id).label("count"),
            ).group_by(EmailEvent.event_type)
        )

        stats = {row.event_type: row.count for row in result}

        # Add total
        stats["total"] = sum(stats.values())

        return stats

    def get_webhook_url(self, base_url: str) -> str:
        """Get webhook URL for SendGrid configuration.

        Args:
            base_url: Application base URL (e.g., "https://iamaim.ru")

        Returns:
            Full webhook URL
        """
        return f"{base_url.rstrip('/')}/api/webhooks/sendgrid"

    def get_webhook_setup_instructions(self, base_url: str) -> str:
        """Get instructions for setting up SendGrid webhook.

        Args:
            base_url: Application base URL

        Returns:
            Setup instructions as formatted string
        """
        webhook_url = self.get_webhook_url(base_url)

        instructions = f"""
SendGrid Webhook Setup Instructions
====================================

1. Go to SendGrid Dashboard: https://app.sendgrid.com/settings/mail_settings

2. Navigate to: Mail Settings → Event Webhook

3. Enable Event Webhook

4. Set HTTP POST URL:
   {webhook_url}

5. Select events to track:
   ✓ Processed
   ✓ Delivered
   ✓ Opened
   ✓ Clicked
   ✓ Bounced
   ✓ Dropped
   ✓ Spam Reports
   ✓ Unsubscribes

6. Enable "Event Webhook Status" (toggle to ON)

7. (Optional) Enable "Signed Event Webhook" for security
   - Copy the "Verification Key"
   - Set SENDGRID_WEBHOOK_SECRET in .env

8. Click "Save"

9. Test webhook:
   - Send a test email via SendGrid
   - Check application logs for webhook events
   - Verify events appear in database (email_events table)

Webhook URL: {webhook_url}
"""
        return instructions.strip()
