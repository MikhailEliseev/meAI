"""
Telegram Ads API Client.

Manages Telegram advertising campaigns using Telegram Bot API.
Telegram Ads allow promoted messages in public channels.

Based on: Telegram Bot API (core.telegram.org/bots/api)
"""

from dataclasses import dataclass

import httpx
import structlog


@dataclass
class TelegramCampaignInfo:
    """Telegram ad campaign information."""

    id: int
    title: str
    channel_username: str
    status: str  # active, paused, completed
    daily_budget: float  # RUB
    total_spent: float  # RUB
    impressions: int
    clicks: int
    ctr: float
    start_date: str
    end_date: str | None


class TelegramAPIError(Exception):
    """Telegram API returned an error response."""


class TelegramAdsClient:
    """Telegram Ad API Client for promoted messages."""

    BASE_URL = "https://api.telegram.org"

    def __init__(self, bot_token: str | None = None):
        self.bot_token = bot_token
        self.timeout = httpx.Timeout(30.0)
        self.logger = structlog.get_logger()

    async def _call(self, method: str, **params) -> dict:
        """Generic Telegram API call with error handling."""
        url = f"{self.BASE_URL}/bot{self.bot_token}/{method}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=params)
            response.raise_for_status()
            data = response.json()

            if not data.get("ok", False):
                error_desc = data.get("description", "Unknown Telegram error")
                raise TelegramAPIError(error_desc)

            return data.get("result", {})

    async def get_campaigns(self) -> list[TelegramCampaignInfo]:
        """Get all active ad campaigns for this bot."""
        self.logger.info("telegram_get_campaigns")

        result = await self._call("getAdCampaigns")

        campaigns = []
        for item in result if isinstance(result, list) else []:
            campaigns.append(
                TelegramCampaignInfo(
                    id=item.get("id", 0),
                    title=item.get("title", ""),
                    channel_username=item.get("channel_username", ""),
                    status=item.get("status", "unknown"),
                    daily_budget=float(item.get("daily_budget", 0)),
                    total_spent=float(item.get("total_spent", 0)),
                    impressions=int(item.get("impressions", 0)),
                    clicks=int(item.get("clicks", 0)),
                    ctr=float(item.get("ctr", 0.0)),
                    start_date=item.get("start_date", ""),
                    end_date=item.get("end_date"),
                )
            )

        self.logger.info("telegram_campaigns_fetched", count=len(campaigns))
        return campaigns

    async def sync_campaigns_to_db(
        self,
        db_session_factory,
        campaign_ids: list[int] | None = None,
    ) -> int:
        """Fetch Telegram ad campaigns and sync to Campaign DB table.

        Uses upsert logic: inserts new campaigns, updates existing ones
        matched by external_id + platform.

        Args:
            db_session_factory: Async callable returning an async context manager.
            campaign_ids: Specific campaigns to sync (None = all).

        Returns:
            Number of campaigns synced to DB.
        """
        from datetime import datetime, timezone

        from sqlalchemy import select
        from aim.models.campaign_models import Campaign

        campaigns = await self.get_campaigns()
        if campaign_ids:
            campaigns = [c for c in campaigns if c.id in campaign_ids]

        if not campaigns:
            self.logger.info("telegram_sync_no_campaigns")
            return 0

        synced = 0
        async with db_session_factory() as db:
            for ci in campaigns:
                result = await db.execute(
                    select(Campaign).where(
                        Campaign.external_id == str(ci.id),
                        Campaign.platform == "telegram",
                    )
                )
                existing = result.scalar_one_or_none()

                if existing:
                    existing.name = ci.title
                    existing.status = ci.status
                    existing.daily_budget = ci.daily_budget
                    existing.total_spent = ci.total_spent
                    self.logger.debug("telegram_sync_updated", external_id=str(ci.id))
                else:
                    db.add(
                        Campaign(
                            external_id=str(ci.id),
                            name=ci.title,
                            platform="telegram",
                            status=ci.status,
                            daily_budget=ci.daily_budget,
                            currency="RUB",
                            total_spent=ci.total_spent,
                            start_date=(
                                datetime.fromisoformat(ci.start_date)
                                if ci.start_date
                                else datetime.now(timezone.utc)
                            ),
                            end_date=(
                                datetime.fromisoformat(ci.end_date)
                                if ci.end_date
                                else None
                            ),
                            created_at=datetime.now(timezone.utc),
                        )
                    )
                    self.logger.debug(
                        "telegram_sync_created", external_id=str(ci.id)
                    )
                synced += 1

            await db.commit()

        self.logger.info("telegram_sync_complete", synced_count=synced)
        return synced

    async def get_campaign_stats(
        self,
        campaign_ids: list[int],
        date_from: str,
        date_to: str,
    ) -> list:
        """Get campaign statistics from Telegram."""
        self.logger.info("telegram_get_stats", campaign_ids=campaign_ids)

        from aim.subagents.ads.yandex_direct_client import CampaignStats

        stats = []
        for campaign_id in campaign_ids:
            result = await self._call(
                "getAdCampaignStats",
                campaign_id=campaign_id,
                date_from=date_from,
                date_to=date_to,
            )

            if isinstance(result, dict):
                stats.append(
                    CampaignStats(
                        campaign_id=campaign_id,
                        impressions=int(result.get("impressions", 0)),
                        clicks=int(result.get("clicks", 0)),
                        cost=float(result.get("spent", 0)),
                        conversions=int(result.get("conversions", 0)),
                        ctr=round(float(result.get("ctr", 0)), 2),
                        cpc=round(float(result.get("cpc", 0)), 2),
                        cpa=round(float(result.get("cpa", 0)), 2),
                        date=date_to,
                    )
                )

        self.logger.info("telegram_stats_fetched", count=len(stats))
        return stats

    async def create_campaign(
        self,
        channel_username: str,
        title: str,
        daily_budget: float,  # RUB
        message_text: str,
    ) -> int:
        """Create a Telegram ad campaign. Returns campaign ID."""
        self.logger.info(
            "telegram_create_campaign",
            channel=channel_username,
            title=title,
        )

        result = await self._call(
            "createAdCampaign",
            channel_username=channel_username,
            title=title,
            daily_budget=daily_budget,
            message_text=message_text,
        )

        campaign_id = result.get("campaign_id", 0)
        self.logger.info("telegram_campaign_created", campaign_id=campaign_id)
        return campaign_id
