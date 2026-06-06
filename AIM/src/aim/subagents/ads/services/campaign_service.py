"""
Campaign Service - High-level campaign management operations.

Provides business logic layer on top of GoogleAdsClient.
Handles campaign CRUD, budget management, targeting configuration.
"""

from typing import Any, Dict, List, Optional
import structlog

from src.aim.subagents.ads.api_clients.google_ads_client import GoogleAdsClient
from src.aim.subagents.ads.config.settings import AdsSettings

logger = structlog.get_logger(__name__)


class CampaignService:
    """
    Campaign management service.
    
    Provides high-level operations for campaign lifecycle:
    - Create campaigns with validation
    - Update campaign settings
    - Manage budgets
    - Configure targeting
    - Bulk operations
    """
    
    def __init__(
        self,
        settings: Optional[AdsSettings] = None,
        client: Optional[GoogleAdsClient] = None,
    ):
        """
        Initialize campaign service.
        
        Args:
            settings: Configuration settings
            client: Pre-initialized GoogleAdsClient (optional)
        """
        self.settings = settings or AdsSettings()
        self.client = client or GoogleAdsClient(settings=self.settings)
        
        logger.info("campaign_service_initialized")
    
    async def create_campaign_with_validation(
        self,
        name: str,
        budget_usd: float,
        channel_type: str = "SEARCH",
        status: str = "PAUSED",
        validate_budget: bool = True,
    ) -> Dict[str, Any]:
        """
        Create campaign with business logic validation.
        
        Args:
            name: Campaign name
            budget_usd: Daily budget in USD
            channel_type: Advertising channel (SEARCH, DISPLAY, VIDEO, SHOPPING)
            status: Initial status (ENABLED, PAUSED)
            validate_budget: Whether to validate budget against limits
        
        Returns:
            Campaign data with validation results
        
        Raises:
            ValueError: If validation fails
        """
        logger.info(
            "creating_campaign_with_validation",
            name=name,
            budget_usd=budget_usd,
            channel_type=channel_type,
        )
        
        # Validate budget
        if validate_budget:
            if budget_usd < 1.0:
                raise ValueError("Budget must be at least $1.00")
            if budget_usd > 10000.0:
                logger.warning(
                    "high_budget_detected",
                    budget_usd=budget_usd,
                    name=name,
                )
        
        # Validate channel type
        valid_channels = ["SEARCH", "DISPLAY", "VIDEO", "SHOPPING", "MULTI_CHANNEL"]
        if channel_type not in valid_channels:
            raise ValueError(
                f"Invalid channel type: {channel_type}. "
                f"Must be one of: {', '.join(valid_channels)}"
            )
        
        # Validate status
        valid_statuses = ["ENABLED", "PAUSED"]
        if status not in valid_statuses:
            raise ValueError(
                f"Invalid status: {status}. "
                f"Must be one of: {', '.join(valid_statuses)}"
            )
        
        # Create campaign via API
        budget_micros = int(budget_usd * 1_000_000)
        campaign = await self.client.create_campaign(
            name=name,
            budget_amount_micros=budget_micros,
            advertising_channel_type=channel_type,
            status=status,
        )
        
        logger.info(
            "campaign_created_with_validation",
            resource_name=campaign["resource_name"],
            name=name,
        )
        
        return {
            **campaign,
            "validation": {
                "budget_validated": validate_budget,
                "channel_validated": True,
                "status_validated": True,
            }
        }
    
    async def update_campaign_budget(
        self,
        campaign_id: str,
        new_budget_usd: float,
    ) -> Dict[str, Any]:
        """
        Update campaign budget.
        
        Args:
            campaign_id: Campaign ID
            new_budget_usd: New daily budget in USD
        
        Returns:
            Updated campaign data
        """
        logger.info(
            "updating_campaign_budget",
            campaign_id=campaign_id,
            new_budget_usd=new_budget_usd,
        )
        
        # Validate budget
        if new_budget_usd < 1.0:
            raise ValueError("Budget must be at least $1.00")
        
        # Get current campaign
        campaign = await self.client.get_campaign(campaign_id)
        
        # Calculate budget change
        old_budget_usd = campaign["budget_micros"] / 1_000_000
        budget_change_pct = ((new_budget_usd - old_budget_usd) / old_budget_usd) * 100
        
        logger.info(
            "budget_change_calculated",
            campaign_id=campaign_id,
            old_budget_usd=old_budget_usd,
            new_budget_usd=new_budget_usd,
            change_pct=budget_change_pct,
        )
        
        # TODO: Implement budget update via Google Ads API
        # This requires CampaignBudgetService.mutate_campaign_budgets()
        
        return {
            "campaign_id": campaign_id,
            "old_budget_usd": old_budget_usd,
            "new_budget_usd": new_budget_usd,
            "budget_change_pct": budget_change_pct,
            "status": "pending_implementation",
        }
    
    async def bulk_create_campaigns(
        self,
        campaigns: List[Dict[str, Any]],
        validate_each: bool = True,
    ) -> Dict[str, Any]:
        """
        Create multiple campaigns in bulk.
        
        Args:
            campaigns: List of campaign configs (name, budget_usd, channel_type, status)
            validate_each: Whether to validate each campaign
        
        Returns:
            Bulk operation results with success/failure counts
        """
        logger.info(
            "bulk_creating_campaigns",
            count=len(campaigns),
            validate_each=validate_each,
        )
        
        results = {
            "total": len(campaigns),
            "successful": 0,
            "failed": 0,
            "campaigns": [],
            "errors": [],
        }
        
        for idx, campaign_config in enumerate(campaigns):
            try:
                campaign = await self.create_campaign_with_validation(
                    name=campaign_config["name"],
                    budget_usd=campaign_config["budget_usd"],
                    channel_type=campaign_config.get("channel_type", "SEARCH"),
                    status=campaign_config.get("status", "PAUSED"),
                    validate_budget=validate_each,
                )
                
                results["successful"] += 1
                results["campaigns"].append({
                    "index": idx,
                    "name": campaign_config["name"],
                    "resource_name": campaign["resource_name"],
                    "status": "success",
                })
                
            except Exception as e:
                logger.error(
                    "bulk_campaign_creation_failed",
                    index=idx,
                    name=campaign_config.get("name", "unknown"),
                    error=str(e),
                )
                
                results["failed"] += 1
                results["errors"].append({
                    "index": idx,
                    "name": campaign_config.get("name", "unknown"),
                    "error": str(e),
                })
        
        logger.info(
            "bulk_campaign_creation_completed",
            total=results["total"],
            successful=results["successful"],
            failed=results["failed"],
        )
        
        return results
    
    async def get_campaign_summary(
        self,
        campaign_id: str,
        include_metrics: bool = True,
    ) -> Dict[str, Any]:
        """
        Get comprehensive campaign summary.
        
        Args:
            campaign_id: Campaign ID
            include_metrics: Whether to include performance metrics
        
        Returns:
            Campaign summary with details and metrics
        """
        logger.info(
            "fetching_campaign_summary",
            campaign_id=campaign_id,
            include_metrics=include_metrics,
        )
        
        # Get campaign details
        campaign = await self.client.get_campaign(campaign_id)
        
        summary = {
            "campaign_id": campaign["id"],
            "name": campaign["name"],
            "status": campaign["status"],
            "channel_type": campaign["channel_type"],
            "budget_usd": campaign["budget_micros"] / 1_000_000,
        }
        
        # Add metrics if requested
        if include_metrics:
            metrics = await self.client.get_campaign_metrics(
                campaign_id=campaign_id,
                date_range="LAST_30_DAYS",
            )
            summary["metrics"] = metrics["metrics"]
        
        logger.info(
            "campaign_summary_fetched",
            campaign_id=campaign_id,
            name=campaign["name"],
        )
        
        return summary
    
    async def pause_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Pause campaign."""
        return await self.client.update_campaign_status(
            campaign_id=campaign_id,
            status="PAUSED",
        )
    
    async def enable_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Enable campaign."""
        return await self.client.update_campaign_status(
            campaign_id=campaign_id,
            status="ENABLED",
        )
    
    async def remove_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Remove campaign."""
        return await self.client.update_campaign_status(
            campaign_id=campaign_id,
            status="REMOVED",
        )
    
    def close(self) -> None:
        """Close service and cleanup resources."""
        self.client.close()
        logger.info("campaign_service_closed")
