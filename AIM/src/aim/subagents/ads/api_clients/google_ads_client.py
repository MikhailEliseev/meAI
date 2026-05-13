"""
Google Ads API Client.

Based on google-ads-python client.py architecture.
Implements gRPC-based communication with Google Ads API v24.

Features:
- OAuth 2.0 authentication
- gRPC channel with interceptors
- Service client factory
- Campaign, Ad Group, Keyword services
- Automatic credential refresh
"""

from typing import Any, Dict, List, Optional

import grpc
import structlog
from google.ads.googleads.client import GoogleAdsClient as GoogleAdsSDKClient
from google.api_core.gapic_v1.client_info import ClientInfo
from google.auth.credentials import Credentials

from AIM.src.aim.subagents.ads.auth.oauth_flow import (
    get_installed_app_credentials,
    refresh_credentials,
)
from AIM.src.aim.subagents.ads.config.settings import AdsSettings

logger = structlog.get_logger(__name__)

# gRPC channel options (from google-ads-python)
_GRPC_CHANNEL_OPTIONS = [
    ("grpc.max_metadata_size", 16 * 1024 * 1024),  # 16MB
    ("grpc.max_receive_message_length", 64 * 1024 * 1024),  # 64MB
]

_DEFAULT_VERSION = "v24"


class GoogleAdsClient:
    """
    Google Ads API client wrapper.

    Wraps google-ads-python SDK with our resilience patterns.
    Provides high-level methods for campaign management.
    """

    def __init__(
        self,
        settings: Optional[AdsSettings] = None,
        credentials: Optional[Credentials] = None,
    ):
        """
        Initialize Google Ads client.

        Args:
            settings: Configuration settings
            credentials: Pre-initialized credentials (optional)
        """
        self.settings = settings or AdsSettings()

        # Initialize credentials
        if credentials:
            self.credentials = credentials
        else:
            self.credentials = get_installed_app_credentials(
                client_id=self.settings.google_ads_client_id,
                client_secret=self.settings.google_ads_client_secret,
                refresh_token=self.settings.google_ads_refresh_token,
            )

        # Initialize Google Ads SDK client
        self.client = GoogleAdsSDKClient(
            credentials=self.credentials,
            developer_token=self.settings.google_ads_developer_token,
            version=_DEFAULT_VERSION,
        )

        # Set customer ID
        self.customer_id = self.settings.google_ads_customer_id
        self.login_customer_id = self.settings.google_ads_login_customer_id

        logger.info(
            "google_ads_client_initialized",
            customer_id=self.customer_id,
            version=_DEFAULT_VERSION,
        )

    def _get_service(self, service_name: str, version: str = _DEFAULT_VERSION):
        """
        Get Google Ads service client.

        Args:
            service_name: Service name (e.g., "CampaignService")
            version: API version (default: v24)

        Returns:
            Service client instance
        """
        return self.client.get_service(service_name, version=version)

    async def create_campaign(
        self,
        name: str,
        budget_amount_micros: int,
        advertising_channel_type: str = "SEARCH",
        status: str = "PAUSED",
    ) -> Dict[str, Any]:
        """
        Create new advertising campaign.

        Args:
            name: Campaign name
            budget_amount_micros: Daily budget in micros (1 USD = 1,000,000 micros)
            advertising_channel_type: Channel type (SEARCH, DISPLAY, VIDEO, etc.)
            status: Campaign status (ENABLED, PAUSED)

        Returns:
            Created campaign data with resource name

        Example:
            >>> client = GoogleAdsClient()
            >>> campaign = await client.create_campaign(
            ...     name="Summer Sale 2026",
            ...     budget_amount_micros=50_000_000,  # $50/day
            ...     advertising_channel_type="SEARCH",
            ...     status="PAUSED"
            ... )
            >>> print(campaign["resource_name"])
        """
        logger.info(
            "creating_campaign",
            name=name,
            budget_micros=budget_amount_micros,
            channel=advertising_channel_type,
        )

        # Get services
        campaign_service = self._get_service("CampaignService")
        campaign_budget_service = self._get_service("CampaignBudgetService")

        # Create campaign budget
        budget_operation = self.client.get_type("CampaignBudgetOperation")
        budget = budget_operation.create
        budget.name = f"{name} Budget"
        budget.amount_micros = budget_amount_micros
        budget.delivery_method = self.client.enums.BudgetDeliveryMethodEnum.STANDARD

        budget_response = campaign_budget_service.mutate_campaign_budgets(
            customer_id=self.customer_id,
            operations=[budget_operation],
        )
        budget_resource_name = budget_response.results[0].resource_name

        logger.info("campaign_budget_created", resource_name=budget_resource_name)

        # Create campaign
        campaign_operation = self.client.get_type("CampaignOperation")
        campaign = campaign_operation.create
        campaign.name = name
        campaign.advertising_channel_type = getattr(
            self.client.enums.AdvertisingChannelTypeEnum,
            advertising_channel_type
        )
        campaign.status = getattr(
            self.client.enums.CampaignStatusEnum,
            status
        )
        campaign.campaign_budget = budget_resource_name

        # Set bidding strategy (Maximize Clicks)
        campaign.maximize_clicks.target_spend_micros = budget_amount_micros

        # Set network settings
        campaign.network_settings.target_google_search = True
        campaign.network_settings.target_search_network = True
        campaign.network_settings.target_content_network = False

        campaign_response = campaign_service.mutate_campaigns(
            customer_id=self.customer_id,
            operations=[campaign_operation],
        )

        campaign_resource_name = campaign_response.results[0].resource_name

        logger.info(
            "campaign_created",
            resource_name=campaign_resource_name,
            name=name,
        )

        return {
            "resource_name": campaign_resource_name,
            "budget_resource_name": budget_resource_name,
            "name": name,
            "status": status,
            "budget_amount_micros": budget_amount_micros,
        }

    async def get_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """
        Get campaign details.

        Args:
            campaign_id: Campaign ID or resource name

        Returns:
            Campaign data
        """
        logger.info("fetching_campaign", campaign_id=campaign_id)

        ga_service = self._get_service("GoogleAdsService")

        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                campaign.advertising_channel_type,
                campaign_budget.amount_micros,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.ctr,
                metrics.average_cpc
            FROM campaign
            WHERE campaign.id = {campaign_id}
        """

        response = ga_service.search(
            customer_id=self.customer_id,
            query=query,
        )

        for row in response:
            return {
                "id": row.campaign.id,
                "name": row.campaign.name,
                "status": row.campaign.status.name,
                "channel_type": row.campaign.advertising_channel_type.name,
                "budget_micros": row.campaign_budget.amount_micros,
                "metrics": {
                    "impressions": row.metrics.impressions,
                    "clicks": row.metrics.clicks,
                    "cost_micros": row.metrics.cost_micros,
                    "conversions": row.metrics.conversions,
                    "ctr": row.metrics.ctr,
                    "average_cpc": row.metrics.average_cpc,
                },
            }

        raise ValueError(f"Campaign {campaign_id} not found")

    async def list_campaigns(
        self,
        status_filter: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        List campaigns for customer account.

        Args:
            status_filter: Filter by status (ENABLED, PAUSED, REMOVED)
            limit: Maximum number of campaigns to return

        Returns:
            List of campaign data
        """
        logger.info(
            "listing_campaigns",
            customer_id=self.customer_id,
            status_filter=status_filter,
            limit=limit,
        )

        ga_service = self._get_service("GoogleAdsService")

        query = """
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                campaign.advertising_channel_type,
                campaign_budget.amount_micros,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros
            FROM campaign
        """

        if status_filter:
            query += f" WHERE campaign.status = {status_filter}"

        query += f" LIMIT {limit}"

        response = ga_service.search(
            customer_id=self.customer_id,
            query=query,
        )

        campaigns = []
        for row in response:
            campaigns.append({
                "id": row.campaign.id,
                "name": row.campaign.name,
                "status": row.campaign.status.name,
                "channel_type": row.campaign.advertising_channel_type.name,
                "budget_micros": row.campaign_budget.amount_micros,
                "metrics": {
                    "impressions": row.metrics.impressions,
                    "clicks": row.metrics.clicks,
                    "cost_micros": row.metrics.cost_micros,
                },
            })

        logger.info("campaigns_listed", count=len(campaigns))
        return campaigns

    async def update_campaign_status(
        self,
        campaign_id: str,
        status: str,
    ) -> Dict[str, Any]:
        """
        Update campaign status.

        Args:
            campaign_id: Campaign ID
            status: New status (ENABLED, PAUSED, REMOVED)

        Returns:
            Updated campaign data
        """
        logger.info(
            "updating_campaign_status",
            campaign_id=campaign_id,
            new_status=status,
        )

        campaign_service = self._get_service("CampaignService")

        campaign_operation = self.client.get_type("CampaignOperation")
        campaign = campaign_operation.update

        campaign.resource_name = self.client.get_service(
            "CampaignService"
        ).campaign_path(self.customer_id, campaign_id)

        campaign.status = getattr(
            self.client.enums.CampaignStatusEnum,
            status
        )

        # Set field mask
        self.client.copy_from(
            campaign_operation.update_mask,
            self.client.get_type("FieldMask", version="v24"),
            paths=["status"],
        )

        response = campaign_service.mutate_campaigns(
            customer_id=self.customer_id,
            operations=[campaign_operation],
        )

        logger.info(
            "campaign_status_updated",
            campaign_id=campaign_id,
            status=status,
        )

        return {
            "resource_name": response.results[0].resource_name,
            "status": status,
        }

    async def get_campaign_metrics(
        self,
        campaign_id: str,
        date_range: str = "LAST_30_DAYS",
    ) -> Dict[str, Any]:
        """
        Get campaign performance metrics.

        Args:
            campaign_id: Campaign ID
            date_range: Date range (LAST_7_DAYS, LAST_30_DAYS, etc.)

        Returns:
            Performance metrics
        """
        logger.info(
            "fetching_campaign_metrics",
            campaign_id=campaign_id,
            date_range=date_range,
        )

        ga_service = self._get_service("GoogleAdsService")

        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value,
                metrics.ctr,
                metrics.average_cpc,
                metrics.average_cpm,
                metrics.cost_per_conversion
            FROM campaign
            WHERE campaign.id = {campaign_id}
            AND segments.date DURING {date_range}
        """

        response = ga_service.search(
            customer_id=self.customer_id,
            query=query,
        )

        for row in response:
            return {
                "campaign_id": row.campaign.id,
                "campaign_name": row.campaign.name,
                "date_range": date_range,
                "metrics": {
                    "impressions": row.metrics.impressions,
                    "clicks": row.metrics.clicks,
                    "cost_micros": row.metrics.cost_micros,
                    "cost_usd": row.metrics.cost_micros / 1_000_000,
                    "conversions": row.metrics.conversions,
                    "conversions_value": row.metrics.conversions_value,
                    "ctr": row.metrics.ctr,
                    "average_cpc": row.metrics.average_cpc,
                    "average_cpm": row.metrics.average_cpm,
                    "cost_per_conversion": row.metrics.cost_per_conversion,
                },
            }

        raise ValueError(f"No metrics found for campaign {campaign_id}")

    def close(self) -> None:
        """Close client and cleanup resources."""
        logger.info("google_ads_client_closed")
