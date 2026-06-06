"""
VK Ads API Client - Campaign Management.

Manages VK Ads advertising campaigns using VK Marketing API.
Provides campaign creation, stats retrieval, and budget management.

Based on: VK Ads API (vk.com/dev/ads_api)
"""

import asyncio
from dataclasses import dataclass

import httpx
import structlog


@dataclass
class VKCampaignInfo:
    """VK Ads campaign information."""

    id: int
    name: str
    status: str  # active, paused, deleted, archived
    daily_budget: float  # RUB (converted from kopecks)
    start_time: int  # Unix timestamp
    end_time: int | None  # Unix timestamp, 0 = no end
    platform: str  # vk, ok, vk_ads


class VKAPIError(Exception):
    """VK API returned an error response."""


class VKAdsClient:
    """VK Ads Marketing API Client."""

    BASE_URL = "https://api.vk.com/method"
    API_VERSION = "5.199"

    def __init__(self, access_token: str | None = None):
        self.access_token = access_token
        self.timeout = httpx.Timeout(30.0)
        self.logger = structlog.get_logger()

    async def _call(self, method: str, **params) -> dict:
        """Generic VK API call with auth and error handling."""
        params["access_token"] = self.access_token
        params["v"] = self.API_VERSION

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.BASE_URL}/{method}",
                data=params,
            )
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                error_msg = data["error"].get("error_msg", "Unknown VK error")
                raise VKAPIError(error_msg)

            return data["response"]

    async def get_campaigns(self, account_id: int) -> list[VKCampaignInfo]:
        """Get all campaigns for an ad account."""
        self.logger.info("vk_get_campaigns", account_id=account_id)

        result = await self._call(
            "ads.getCampaigns",
            account_id=account_id,
        )

        campaigns = []
        for item in result:
            daily_budget_kopecks = item.get("day_limit", 0)
            campaigns.append(
                VKCampaignInfo(
                    id=item["id"],
                    name=item["name"],
                    status=item["status"],
                    daily_budget=daily_budget_kopecks / 100,  # kopecks → RUB
                    start_time=item.get("start_time", 0),
                    end_time=item.get("end_time", None),
                    platform=item.get("platform", "vk"),
                )
            )

        self.logger.info("vk_campaigns_fetched", count=len(campaigns))
        return campaigns

    async def sync_campaigns_to_db(
        self,
        db_session_factory,
        account_id: int,
        campaign_ids: list[int] | None = None,
    ) -> int:
        """Fetch VK campaigns and sync to Campaign DB table.

        Uses upsert logic: inserts new campaigns, updates existing ones
        matched by external_id + platform.

        Args:
            db_session_factory: Async callable returning an async context manager.
            account_id: VK Ads account ID.
            campaign_ids: Specific campaigns to sync (None = all).

        Returns:
            Number of campaigns synced to DB.
        """
        from datetime import datetime, timezone

        from sqlalchemy import select
        from src.aim.models.campaign_models import Campaign

        campaigns = await self.get_campaigns(account_id=account_id)
        if campaign_ids:
            campaigns = [c for c in campaigns if c.id in campaign_ids]

        if not campaigns:
            self.logger.info("vk_sync_no_campaigns")
            return 0

        synced = 0
        async with db_session_factory() as db:
            for ci in campaigns:
                result = await db.execute(
                    select(Campaign).where(
                        Campaign.external_id == str(ci.id),
                        Campaign.platform == "vk",
                    )
                )
                existing = result.scalar_one_or_none()

                if existing:
                    existing.name = ci.name
                    existing.status = ci.status
                    existing.daily_budget = ci.daily_budget
                    self.logger.debug("vk_sync_updated", external_id=str(ci.id))
                else:
                    db.add(
                        Campaign(
                            external_id=str(ci.id),
                            name=ci.name,
                            platform="vk",
                            status=ci.status,
                            daily_budget=ci.daily_budget,
                            currency="RUB",
                            start_date=(
                                datetime.fromtimestamp(ci.start_time, tz=timezone.utc)
                                if ci.start_time
                                else datetime.now(timezone.utc)
                            ),
                            created_at=datetime.now(timezone.utc),
                        )
                    )
                    self.logger.debug("vk_sync_created", external_id=str(ci.id))
                synced += 1

            await db.commit()

        self.logger.info("vk_sync_complete", synced_count=synced)
        return synced

    async def get_campaign_stats(
        self,
        account_id: int,
        campaign_ids: list[int],
        date_from: str,
        date_to: str,
    ) -> list:
        """Get campaign statistics from VK Ads."""
        self.logger.info("vk_get_stats", campaign_ids=campaign_ids)

        result = await self._call(
            "ads.getStatistics",
            account_id=account_id,
            ids_type="campaign",
            ids=",".join(str(cid) for cid in campaign_ids),
            period="day",
            date_from=date_from,
            date_to=date_to,
        )

        from src.aim.subagents.ads.yandex_direct_client import CampaignStats

        stats = []
        for item in result:
            campaign_id = item.get("id", 0)
            inner_stats = item.get("stats", [])
            for day in inner_stats:
                stats.append(
                    CampaignStats(
                        campaign_id=campaign_id,
                        impressions=int(day.get("impressions", 0)),
                        clicks=int(day.get("clicks", 0)),
                        cost=float(day.get("spent", "0")),
                        conversions=int(day.get("reach", 0)),
                        ctr=round(float(day.get("ctr", 0)), 2),
                        cpc=round(float(day.get("cpc", 0)), 2),
                        cpa=round(float(day.get("cpa", 0)), 2),
                        date=day.get("day", date_to),
                    )
                )

        self.logger.info("vk_stats_fetched", count=len(stats))
        return stats

    async def create_campaign(
        self,
        account_id: int,
        name: str,
        daily_budget: float,  # RUB
        start_time: int = 0,  # Unix timestamp, 0 = immediately
    ) -> int:
        """Create a new VK Ads campaign. Returns campaign ID."""
        self.logger.info("vk_create_campaign", name=name, daily_budget=daily_budget)

        daily_budget_kopecks = int(daily_budget * 100)  # RUB → kopecks

        result = await self._call(
            "ads.createCampaigns",
            account_id=account_id,
            data=f'[{{"name":"{name}","day_limit":{daily_budget_kopecks},"start_time":{start_time},"status":1}}]',
        )

        campaign_id = result[0]["id"]
        self.logger.info("vk_campaign_created", campaign_id=campaign_id)
        return campaign_id
