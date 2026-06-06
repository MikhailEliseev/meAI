"""
Attribution Pipeline — UTM-to-Lead-to-Campaign Tracking.

Listens for lead.created events on the EventBus and attributes them
to marketing campaigns via UTM parameter matching.
"""

from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from meai.events.event_bus import EventBus, Event, EventPriority
from src.aim.models.campaign_models import Campaign, CampaignAttribution


class AttributionPipeline:
    """Links campaign clicks to lead conversions via UTM matching."""

    def __init__(self, event_bus: EventBus, db_session_factory):
        self.event_bus = event_bus
        self.db_factory = db_session_factory
        self.logger = structlog.get_logger()
        self._subscribed = False

    def start(self) -> None:
        """Subscribe to lead.created events."""
        if self._subscribed:
            return
        self.event_bus.subscribe(
            "lead.created",
            self.on_lead_created,
        )
        self._subscribed = True
        self.logger.info("attribution_pipeline_started")

    async def on_lead_created(self, event: Event) -> None:
        """Handle lead.created event — attribute to campaign if UTM present."""
        lead = event.payload
        utm_source = lead.get("utm_source")
        utm_campaign = lead.get("utm_campaign")

        if not utm_source or not utm_campaign:
            self.logger.debug("attribution_skip_no_utm", lead_id=lead.get("id"))
            return

        async with self.db_factory() as db:
            result = await db.execute(
                select(Campaign).where(
                    Campaign.utm_source == utm_source,
                    Campaign.utm_campaign == utm_campaign,
                    Campaign.status == "active",
                )
            )
            campaign = result.scalar_one_or_none()

            if not campaign:
                self.logger.debug(
                    "attribution_no_matching_campaign",
                    utm_source=utm_source,
                    utm_campaign=utm_campaign,
                )
                return

            attribution = CampaignAttribution(
                campaign_id=campaign.id,
                lead_id=lead["id"],
                utm_source=utm_source,
                utm_campaign=utm_campaign,
                utm_medium=lead.get("utm_medium"),
                attributed_at=datetime.now(timezone.utc),
            )
            db.add(attribution)
            await db.commit()

            self.logger.info(
                "attribution_created",
                campaign_id=campaign.id,
                lead_id=lead["id"],
                campaign_name=campaign.name,
            )

            await self.event_bus.publish(Event(
                event_type="campaign.attribution",
                payload={
                    "campaign_id": campaign.id,
                    "lead_id": lead["id"],
                    "attribution_id": attribution.id,
                },
            ))
