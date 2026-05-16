"""
Ads Services Layer.

High-level business logic for campaign management, content optimization, and analytics.
"""

from aim.subagents.ads.services.campaign_service import CampaignService
from aim.subagents.ads.services.content_optimizer import ContentOptimizer
from aim.subagents.ads.services.analytics_service import AnalyticsService

__all__ = [
    "CampaignService",
    "ContentOptimizer",
    "AnalyticsService",
]
