"""
Yandex Direct API Client - Campaign Management.

Manages Yandex Direct advertising campaigns using official API v5.
Provides campaign creation, budget optimization, and performance monitoring.

Based on: Yandex Direct API v5 (official)
Documentation: https://yandex.ru/dev/direct/doc/
"""

import asyncio
import csv
import io
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx
import structlog


@dataclass
class CampaignInfo:
    """Campaign information."""

    id: int
    name: str
    status: str
    type: str
    daily_budget: float
    currency: str
    start_date: str
    end_date: str | None


@dataclass
class CampaignStats:
    """Campaign statistics."""

    campaign_id: int
    impressions: int
    clicks: int
    cost: float
    conversions: int
    ctr: float
    cpc: float
    cpa: float
    date: str


@dataclass
class BudgetRecommendation:
    """Budget optimization recommendation."""

    campaign_id: int
    campaign_name: str
    current_budget: float
    recommended_budget: float
    change: float
    change_percent: float
    reason: str


@dataclass
class AdGroupInfo:
    """Ad group information."""

    id: int
    campaign_id: int
    name: str
    status: str
    region_ids: list[int]


@dataclass
class DirectAPIResult:
    """Yandex Direct API operation result."""

    success: bool
    campaigns: list[CampaignInfo]
    stats: list[CampaignStats]
    recommendations: list[BudgetRecommendation]
    timestamp: str
    error: str | None = None


class YandexDirectAPIClient:
    """
    Yandex Direct API Client.

    Manages advertising campaigns using Yandex Direct API v5.
    """

    def __init__(self, token: str | None = None):
        """
        Initialize Yandex Direct API Client.

        Args:
            token: Yandex Direct API OAuth token
        """
        self.logger = structlog.get_logger()
        self.token = token
        self.base_url = "https://api.direct.yandex.com/json/v5"
        self.timeout = httpx.Timeout(30.0)

    async def get_campaigns(
        self,
        campaign_ids: list[int] | None = None,
    ) -> list[CampaignInfo]:
        """
        Get campaign information.

        Args:
            campaign_ids: Specific campaign IDs (None = all campaigns)

        Returns:
            List of campaign information
        """
        self.logger.info(
            "fetching_campaigns",
            campaign_ids=campaign_ids,
        )

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Accept-Language": "ru",
            }

            payload = {
                "method": "get",
                "params": {
                    "SelectionCriteria": {},
                    "FieldNames": [
                        "Id",
                        "Name",
                        "Status",
                        "Type",
                        "DailyBudget",
                        "Currency",
                        "StartDate",
                        "EndDate",
                    ],
                },
            }

            if campaign_ids:
                payload["params"]["SelectionCriteria"]["Ids"] = campaign_ids

            response = await client.post(
                f"{self.base_url}/campaigns",
                json=payload,
                headers=headers,
            )
            await response.raise_for_status()
            data = await response.json()

            campaigns = []
            for campaign_data in data.get("result", {}).get("Campaigns", []):
                daily_budget = campaign_data.get("DailyBudget", {})

                campaigns.append(
                    CampaignInfo(
                        id=campaign_data["Id"],
                        name=campaign_data["Name"],
                        status=campaign_data["Status"],
                        type=campaign_data["Type"],
                        daily_budget=daily_budget.get("Amount", 0.0) / 1_000_000,  # Micros to currency
                        currency=campaign_data.get("Currency", "RUB"),
                        start_date=campaign_data.get("StartDate", ""),
                        end_date=campaign_data.get("EndDate"),
                    )
                )

            self.logger.info(
                "campaigns_fetched",
                count=len(campaigns),
            )

            return campaigns

    async def sync_campaigns_to_db(
        self,
        db_session_factory,
        campaign_ids: list[int] | None = None,
    ) -> int:
        """Fetch campaigns from Yandex Direct API and sync to Campaign DB table.

        Uses upsert logic: inserts new campaigns, updates existing ones
        matched by external_id + platform.

        Args:
            db_session_factory: Async callable returning an async context manager
                (e.g., async_session_maker).
            campaign_ids: Specific campaigns to sync (None = all campaigns).

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
            self.logger.info("sync_campaigns_no_campaigns_to_sync")
            return 0

        synced = 0
        async with db_session_factory() as db:
            for campaign_info in campaigns:
                result = await db.execute(
                    select(Campaign).where(
                        Campaign.external_id == str(campaign_info.id),
                        Campaign.platform == "yandex",
                    )
                )
                existing = result.scalar_one_or_none()

                if existing:
                    existing.name = campaign_info.name
                    existing.status = campaign_info.status
                    existing.daily_budget = campaign_info.daily_budget
                    existing.currency = campaign_info.currency
                    if campaign_info.end_date:
                        existing.end_date = datetime.fromisoformat(campaign_info.end_date)
                    self.logger.debug(
                        "sync_campaign_updated",
                        external_id=str(campaign_info.id),
                        name=campaign_info.name,
                    )
                else:
                    db.add(
                        Campaign(
                            external_id=str(campaign_info.id),
                            name=campaign_info.name,
                            platform="yandex",
                            status=campaign_info.status,
                            daily_budget=campaign_info.daily_budget,
                            currency=campaign_info.currency,
                            start_date=datetime.fromisoformat(campaign_info.start_date),
                            end_date=(
                                datetime.fromisoformat(campaign_info.end_date)
                                if campaign_info.end_date
                                else None
                            ),
                            created_at=datetime.now(timezone.utc),
                        )
                    )
                    self.logger.debug(
                        "sync_campaign_created",
                        external_id=str(campaign_info.id),
                        name=campaign_info.name,
                    )
                synced += 1

            await db.commit()

        self.logger.info("sync_campaigns_complete", synced_count=synced)
        return synced

    async def get_campaign_stats(
        self,
        campaign_ids: list[int],
        date_from: str,
        date_to: str,
    ) -> list[CampaignStats]:
        """
        Get campaign statistics.

        Args:
            campaign_ids: Campaign IDs to get stats for
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)

        Returns:
            List of campaign statistics
        """
        self.logger.info(
            "fetching_campaign_stats",
            campaign_ids=campaign_ids,
            date_from=date_from,
            date_to=date_to,
        )

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Accept-Language": "ru",
                "processingMode": "auto",
                "skipReportHeader": "true",
                "skipColumnHeader": "true",
                "skipReportSummary": "true",
            }

            payload = {
                "params": {
                    "SelectionCriteria": {
                        "DateFrom": date_from,
                        "DateTo": date_to,
                        "Filter": [{
                            "Field": "CampaignId",
                            "Operator": "IN",
                            "Values": [str(cid) for cid in campaign_ids],
                        }],
                    },
                    "FieldNames": [
                        "Date", "CampaignId", "CampaignName",
                        "Impressions", "Clicks", "Cost",
                        "Conversions", "Ctr", "AvgCpc", "AvgCpa",
                    ],
                    "ReportName": f"Campaign_Stats_{date_from}_{date_to}",
                    "ReportType": "CAMPAIGN_PERFORMANCE_REPORT",
                    "DateRangeType": "CUSTOM_DATE",
                    "Format": "TSV",
                    "IncludeVAT": "YES",
                }
            }

            response = await client.post(
                f"{self.base_url}/reports",
                json=payload,
                headers=headers,
            )

            # Handle async report generation (HTTP 201/202 → poll with retryIn header)
            poll_count = 0
            while response.status_code in (201, 202):
                poll_count += 1
                if poll_count > 10:
                    raise TimeoutError(
                        f"Yandex Reports API: report not ready after {poll_count} polling attempts"
                    )
                retry_in = int(response.headers.get("retryIn", 5))
                await asyncio.sleep(retry_in)
                response = await client.get(
                    f"{self.base_url}/reports",
                    headers=headers,
                )

            response.raise_for_status()

            # Parse TSV response using csv module
            tsv_data = response.text
            if not tsv_data.strip():
                self.logger.info("campaign_stats_empty")
                return []

            reader = csv.DictReader(
                io.StringIO(tsv_data),
                delimiter="\t",
            )

            stats = []
            for row in reader:
                # Yandex returns costs in micros (1/1,000,000 of currency unit)
                cost_micros = float(row.get("Cost", "0"))
                cpc_micros = float(row.get("AvgCpc", "0"))
                cpa_micros = float(row.get("AvgCpa", "0"))

                stats.append(CampaignStats(
                    campaign_id=int(row["CampaignId"]),
                    impressions=int(row.get("Impressions", "0")),
                    clicks=int(row.get("Clicks", "0")),
                    cost=round(cost_micros / 1_000_000, 2),
                    conversions=int(row.get("Conversions", "0")),
                    ctr=round(float(row.get("Ctr", "0")), 2),
                    cpc=round(cpc_micros / 1_000_000, 2) if cpc_micros else 0.0,
                    cpa=round(cpa_micros / 1_000_000, 2) if cpa_micros else 0.0,
                    date=row.get("Date", date_to),
                ))

            self.logger.info(
                "campaign_stats_fetched",
                count=len(stats),
            )

            return stats

    async def optimize_budgets(
        self,
        campaigns: list[CampaignInfo],
        stats: list[CampaignStats],
        total_budget: float,
    ) -> list[BudgetRecommendation]:
        """
        Generate budget optimization recommendations.

        Args:
            campaigns: List of campaigns
            stats: Campaign statistics
            total_budget: Total available budget

        Returns:
            List of budget recommendations
        """
        self.logger.info(
            "optimizing_budgets",
            campaigns_count=len(campaigns),
            total_budget=total_budget,
        )

        recommendations = []

        # Create stats lookup
        stats_dict = {s.campaign_id: s for s in stats}

        # Calculate performance scores
        campaign_scores = []
        for campaign in campaigns:
            if campaign.id in stats_dict:
                stat = stats_dict[campaign.id]

                # Performance score: conversions / cost (ROI proxy)
                if stat.cost > 0:
                    score = stat.conversions / stat.cost
                else:
                    score = 0.0

                campaign_scores.append((campaign, stat, score))

        # Sort by performance score
        campaign_scores.sort(key=lambda x: x[2], reverse=True)

        # Allocate budget proportionally to performance
        total_score = sum(score for _, _, score in campaign_scores)

        for campaign, stat, score in campaign_scores:
            if total_score > 0:
                # Allocate budget based on performance
                recommended_budget = (score / total_score) * total_budget
            else:
                # Equal distribution if no performance data
                recommended_budget = total_budget / len(campaigns)

            change = recommended_budget - campaign.daily_budget
            change_percent = (
                (change / campaign.daily_budget * 100)
                if campaign.daily_budget > 0
                else 0.0
            )

            # Generate reason
            if change > 0:
                reason = f"High performance (CPA: {stat.cpa:.2f}, {stat.conversions} conversions). Increase budget to scale."
            elif change < 0:
                reason = f"Low performance (CPA: {stat.cpa:.2f}, {stat.conversions} conversions). Reduce budget."
            else:
                reason = "Optimal budget allocation."

            recommendations.append(
                BudgetRecommendation(
                    campaign_id=campaign.id,
                    campaign_name=campaign.name,
                    current_budget=campaign.daily_budget,
                    recommended_budget=round(recommended_budget, 2),
                    change=round(change, 2),
                    change_percent=round(change_percent, 1),
                    reason=reason,
                )
            )

        self.logger.info(
            "budget_optimization_complete",
            recommendations_count=len(recommendations),
        )

        return recommendations

    async def create_campaign(
        self,
        name: str,
        daily_budget: float,
        start_date: str,
        end_date: str | None = None,
    ) -> int:
        """
        Create new campaign.

        Args:
            name: Campaign name
            daily_budget: Daily budget in currency
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), optional

        Returns:
            Created campaign ID
        """
        self.logger.info(
            "creating_campaign",
            name=name,
            daily_budget=daily_budget,
        )

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Accept-Language": "ru",
            }

            payload = {
                "method": "add",
                "params": {
                    "Campaigns": [
                        {
                            "Name": name,
                            "StartDate": start_date,
                            "Type": "TEXT_CAMPAIGN",
                            "TextCampaign": {
                                "BiddingStrategy": {
                                    "Search": {
                                        "BiddingStrategyType": "HIGHEST_POSITION",
                                    },
                                    "Network": {
                                        "BiddingStrategyType": "SERVING_OFF",
                                    },
                                },
                                "Settings": [],
                            },
                            "DailyBudget": {
                                "Amount": int(daily_budget * 1_000_000),  # Currency to micros
                                "Mode": "STANDARD",
                            },
                        }
                    ]
                },
            }

            if end_date:
                payload["params"]["Campaigns"][0]["EndDate"] = end_date

            response = await client.post(
                f"{self.base_url}/campaigns",
                json=payload,
                headers=headers,
            )
            await response.raise_for_status()
            data = await response.json()

            campaign_id = data["result"]["AddResults"][0]["Id"]

            self.logger.info(
                "campaign_created",
                campaign_id=campaign_id,
            )

            return campaign_id


async def main():
    """Example usage."""
    import os

    token = os.getenv("YANDEX_DIRECT_TOKEN")
    if not token:
        print("Error: YANDEX_DIRECT_TOKEN environment variable not set")
        return

    client = YandexDirectAPIClient(token=token)

    # Get campaigns
    campaigns = await client.get_campaigns()
    print(f"Total campaigns: {len(campaigns)}")

    if campaigns:
        # Get stats for first campaign
        campaign_ids = [c.id for c in campaigns[:3]]
        stats = await client.get_campaign_stats(
            campaign_ids=campaign_ids,
            date_from="2026-05-01",
            date_to="2026-05-14",
        )

        # Optimize budgets
        recommendations = await client.optimize_budgets(
            campaigns=campaigns[:3],
            stats=stats,
            total_budget=10000.0,
        )

        print("\nBudget Recommendations:")
        for rec in recommendations:
            print(
                f"  {rec.campaign_name}: "
                f"{rec.current_budget:.2f} → {rec.recommended_budget:.2f} "
                f"({rec.change:+.2f}, {rec.change_percent:+.1f}%)"
            )
            print(f"    Reason: {rec.reason}")


if __name__ == "__main__":
    asyncio.run(main())
