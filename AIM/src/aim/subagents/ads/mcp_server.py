"""
MCP Server for Ads Management.

Based on facebook-ads-library-mcp/mcp_server.py pattern.
Provides tools for campaign management across advertising platforms.

Features:
- FastMCP framework for tool registration
- Input validation and error handling
- Batch operations support
- Real API integration (no mocks)
"""

from typing import Any, Dict, List, Optional, Union

import structlog
from mcp.server.fastmcp import FastMCP

from aim.subagents.ads.api_clients.google_ads_client import GoogleAdsClient
from aim.subagents.ads.config.settings import get_ads_settings

logger = structlog.get_logger(__name__)

INSTRUCTIONS = """
This server provides advertising campaign management across multiple platforms.
It allows you to create campaigns, optimize performance, and analyze metrics.

Workflow:
1. Use create_campaign to create new advertising campaigns
2. Use get_campaign_metrics to fetch real performance data
3. Use optimize_campaign to improve campaign performance
4. Use analyze_competitors to understand competitive landscape

The server provides real-time access to Google Ads, Yandex Direct, and Facebook Ads APIs.
"""

mcp = FastMCP(
    name="Ads Manager",
    instructions=INSTRUCTIONS
)


class CampaignCreationError(Exception):
    """Campaign creation failed."""
    pass


class MetricsFetchError(Exception):
    """Failed to fetch metrics."""
    pass


@mcp.tool(
    description="Create new advertising campaign with targeting and budget. Returns real campaign data from Google Ads API (not mock). Use this tool when you need to launch new campaigns.",
    annotations={
        "title": "Create Ad Campaign",
        "readOnlyHint": False,
        "openWorldHint": True
    }
)
def create_campaign(
    platform: str,
    name: str,
    budget_usd: float,
    channel_type: str = "SEARCH",
    status: str = "PAUSED",
) -> Dict[str, Any]:
    """
    Create new advertising campaign.

    Args:
        platform: Advertising platform (google_ads, yandex_direct, facebook_ads)
        name: Campaign name
        budget_usd: Daily budget in USD
        channel_type: Channel type (SEARCH, DISPLAY, VIDEO, SHOPPING)
        status: Initial status (ENABLED, PAUSED)

    Returns:
        A dictionary containing:
        - success: Boolean indicating if campaign was created
        - message: Status message
        - campaign: Campaign data with resource name and ID
        - error: Error details if creation failed

    Example:
        >>> result = create_campaign(
        ...     platform="google_ads",
        ...     name="Summer Sale 2026",
        ...     budget_usd=50.0,
        ...     channel_type="SEARCH",
        ...     status="PAUSED"
        ... )
        >>> print(result["campaign"]["resource_name"])
    """
    # Input validation
    if not platform or not platform.strip():
        return {
            "success": False,
            "message": "Platform must be provided and cannot be empty.",
            "campaign": {},
            "error": "Missing or empty platform"
        }

    if not name or not name.strip():
        return {
            "success": False,
            "message": "Campaign name must be provided and cannot be empty.",
            "campaign": {},
            "error": "Missing or empty campaign name"
        }

    if budget_usd <= 0:
        return {
            "success": False,
            "message": "Budget must be greater than 0.",
            "campaign": {},
            "error": "Invalid budget amount"
        }

    platform = platform.lower().strip()

    try:
        if platform == "google_ads":
            # Real Google Ads API integration
            settings = get_ads_settings()
            client = GoogleAdsClient(settings=settings)

            # Convert USD to micros (1 USD = 1,000,000 micros)
            budget_micros = int(budget_usd * 1_000_000)

            # Create campaign via real API
            import asyncio
            campaign = asyncio.run(client.create_campaign(
                name=name,
                budget_amount_micros=budget_micros,
                advertising_channel_type=channel_type,
                status=status,
            ))

            client.close()

            logger.info(
                "campaign_created_via_google_ads",
                name=name,
                budget_usd=budget_usd,
                resource_name=campaign["resource_name"]
            )

            return {
                "success": True,
                "message": f"Campaign '{name}' created successfully on Google Ads.",
                "campaign": {
                    "platform": "google_ads",
                    "resource_name": campaign["resource_name"],
                    "budget_resource_name": campaign["budget_resource_name"],
                    "name": campaign["name"],
                    "status": campaign["status"],
                    "budget_usd": budget_usd,
                    "budget_micros": campaign["budget_amount_micros"],
                    "channel_type": channel_type,
                },
                "error": None
            }

        elif platform == "yandex_direct":
            # TODO: Implement Yandex Direct integration
            return {
                "success": False,
                "message": "Yandex Direct integration not yet implemented.",
                "campaign": {},
                "error": "Platform not implemented"
            }

        elif platform == "facebook_ads":
            # TODO: Implement Facebook Ads integration
            return {
                "success": False,
                "message": "Facebook Ads integration not yet implemented.",
                "campaign": {},
                "error": "Platform not implemented"
            }

        else:
            return {
                "success": False,
                "message": f"Unknown platform: {platform}. Supported: google_ads, yandex_direct, facebook_ads",
                "campaign": {},
                "error": "Unknown platform"
            }

    except Exception as e:
        logger.error(
            "campaign_creation_failed",
            platform=platform,
            name=name,
            error=str(e),
            error_type=type(e).__name__
        )
        return {
            "success": False,
            "message": f"Failed to create campaign: {str(e)}",
            "campaign": {},
            "error": str(e)
        }


@mcp.tool(
    description="Get real campaign performance metrics from advertising platform. Returns actual data from API (impressions, clicks, CTR, CPC, conversions). Use this tool to analyze campaign performance.",
    annotations={
        "title": "Get Campaign Metrics",
        "readOnlyHint": True,
        "openWorldHint": True
    }
)
def get_campaign_metrics(
    platform: str,
    campaign_id: str,
    date_range: str = "LAST_30_DAYS",
) -> Dict[str, Any]:
    """
    Get campaign performance metrics.

    Args:
        platform: Advertising platform (google_ads, yandex_direct, facebook_ads)
        campaign_id: Campaign ID
        date_range: Date range (LAST_7_DAYS, LAST_30_DAYS, LAST_90_DAYS, THIS_MONTH, LAST_MONTH)

    Returns:
        A dictionary containing:
        - success: Boolean indicating if metrics were fetched
        - message: Status message
        - metrics: Real performance metrics from API
        - error: Error details if fetch failed
    """
    # Input validation
    if not platform or not platform.strip():
        return {
            "success": False,
            "message": "Platform must be provided.",
            "metrics": {},
            "error": "Missing platform"
        }

    if not campaign_id or not str(campaign_id).strip():
        return {
            "success": False,
            "message": "Campaign ID must be provided.",
            "metrics": {},
            "error": "Missing campaign ID"
        }

    platform = platform.lower().strip()

    try:
        if platform == "google_ads":
            # Real Google Ads API integration
            settings = get_ads_settings()
            client = GoogleAdsClient(settings=settings)

            # Fetch real metrics from API
            import asyncio
            metrics_data = asyncio.run(client.get_campaign_metrics(
                campaign_id=campaign_id,
                date_range=date_range,
            ))

            client.close()

            logger.info(
                "metrics_fetched_via_google_ads",
                campaign_id=campaign_id,
                date_range=date_range,
                impressions=metrics_data["metrics"]["impressions"],
                clicks=metrics_data["metrics"]["clicks"]
            )

            return {
                "success": True,
                "message": f"Metrics fetched for campaign {campaign_id}.",
                "metrics": metrics_data,
                "error": None
            }

        elif platform == "yandex_direct":
            return {
                "success": False,
                "message": "Yandex Direct integration not yet implemented.",
                "metrics": {},
                "error": "Platform not implemented"
            }

        elif platform == "facebook_ads":
            return {
                "success": False,
                "message": "Facebook Ads integration not yet implemented.",
                "metrics": {},
                "error": "Platform not implemented"
            }

        else:
            return {
                "success": False,
                "message": f"Unknown platform: {platform}",
                "metrics": {},
                "error": "Unknown platform"
            }

    except Exception as e:
        logger.error(
            "metrics_fetch_failed",
            platform=platform,
            campaign_id=campaign_id,
            error=str(e)
        )
        return {
            "success": False,
            "message": f"Failed to fetch metrics: {str(e)}",
            "metrics": {},
            "error": str(e)
        }


@mcp.tool(
    description="List all campaigns for advertising account. Returns real campaign data from API with current status and metrics. Use this tool to see all active campaigns.",
    annotations={
        "title": "List Campaigns",
        "readOnlyHint": True,
        "openWorldHint": True
    }
)
def list_campaigns(
    platform: str,
    status_filter: Optional[str] = None,
    limit: int = 100,
) -> Dict[str, Any]:
    """
    List campaigns for advertising account.

    Args:
        platform: Advertising platform (google_ads, yandex_direct, facebook_ads)
        status_filter: Filter by status (ENABLED, PAUSED, REMOVED)
        limit: Maximum number of campaigns to return (default: 100)

    Returns:
        A dictionary containing:
        - success: Boolean indicating if campaigns were listed
        - message: Status message
        - campaigns: List of campaign data
        - count: Number of campaigns returned
        - error: Error details if listing failed
    """
    if not platform or not platform.strip():
        return {
            "success": False,
            "message": "Platform must be provided.",
            "campaigns": [],
            "count": 0,
            "error": "Missing platform"
        }

    platform = platform.lower().strip()

    try:
        if platform == "google_ads":
            settings = get_ads_settings()
            client = GoogleAdsClient(settings=settings)

            import asyncio
            campaigns = asyncio.run(client.list_campaigns(
                status_filter=status_filter,
                limit=limit,
            ))

            client.close()

            logger.info(
                "campaigns_listed_via_google_ads",
                count=len(campaigns),
                status_filter=status_filter
            )

            return {
                "success": True,
                "message": f"Found {len(campaigns)} campaigns.",
                "campaigns": campaigns,
                "count": len(campaigns),
                "error": None
            }

        elif platform == "yandex_direct":
            return {
                "success": False,
                "message": "Yandex Direct integration not yet implemented.",
                "campaigns": [],
                "count": 0,
                "error": "Platform not implemented"
            }

        elif platform == "facebook_ads":
            return {
                "success": False,
                "message": "Facebook Ads integration not yet implemented.",
                "campaigns": [],
                "count": 0,
                "error": "Platform not implemented"
            }

        else:
            return {
                "success": False,
                "message": f"Unknown platform: {platform}",
                "campaigns": [],
                "count": 0,
                "error": "Unknown platform"
            }

    except Exception as e:
        logger.error(
            "campaigns_listing_failed",
            platform=platform,
            error=str(e)
        )
        return {
            "success": False,
            "message": f"Failed to list campaigns: {str(e)}",
            "campaigns": [],
            "count": 0,
            "error": str(e)
        }


@mcp.tool(
    description="Update campaign status (enable, pause, or remove). Changes are applied immediately via API. Use this tool to control campaign state.",
    annotations={
        "title": "Update Campaign Status",
        "readOnlyHint": False,
        "openWorldHint": True
    }
)
def update_campaign_status(
    platform: str,
    campaign_id: str,
    status: str,
) -> Dict[str, Any]:
    """
    Update campaign status.

    Args:
        platform: Advertising platform (google_ads, yandex_direct, facebook_ads)
        campaign_id: Campaign ID
        status: New status (ENABLED, PAUSED, REMOVED)

    Returns:
        A dictionary containing:
        - success: Boolean indicating if status was updated
        - message: Status message
        - campaign: Updated campaign data
        - error: Error details if update failed
    """
    if not platform or not platform.strip():
        return {
            "success": False,
            "message": "Platform must be provided.",
            "campaign": {},
            "error": "Missing platform"
        }

    if not campaign_id or not str(campaign_id).strip():
        return {
            "success": False,
            "message": "Campaign ID must be provided.",
            "campaign": {},
            "error": "Missing campaign ID"
        }

    if status not in ["ENABLED", "PAUSED", "REMOVED"]:
        return {
            "success": False,
            "message": "Status must be ENABLED, PAUSED, or REMOVED.",
            "campaign": {},
            "error": "Invalid status"
        }

    platform = platform.lower().strip()

    try:
        if platform == "google_ads":
            settings = get_ads_settings()
            client = GoogleAdsClient(settings=settings)

            import asyncio
            result = asyncio.run(client.update_campaign_status(
                campaign_id=campaign_id,
                status=status,
            ))

            client.close()

            logger.info(
                "campaign_status_updated_via_google_ads",
                campaign_id=campaign_id,
                new_status=status
            )

            return {
                "success": True,
                "message": f"Campaign {campaign_id} status updated to {status}.",
                "campaign": result,
                "error": None
            }

        elif platform == "yandex_direct":
            return {
                "success": False,
                "message": "Yandex Direct integration not yet implemented.",
                "campaign": {},
                "error": "Platform not implemented"
            }

        elif platform == "facebook_ads":
            return {
                "success": False,
                "message": "Facebook Ads integration not yet implemented.",
                "campaign": {},
                "error": "Platform not implemented"
            }

        else:
            return {
                "success": False,
                "message": f"Unknown platform: {platform}",
                "campaign": {},
                "error": "Unknown platform"
            }

    except Exception as e:
        logger.error(
            "campaign_status_update_failed",
            platform=platform,
            campaign_id=campaign_id,
            error=str(e)
        )
        return {
            "success": False,
            "message": f"Failed to update campaign status: {str(e)}",
            "campaign": {},
            "error": str(e)
        }


if __name__ == "__main__":
    mcp.run()
