"""
Ads Services Layer.

High-level business logic for campaign management, content optimization, and analytics.
"""

from src.aim.subagents.ads.services.campaign_service import CampaignService
from src.aim.subagents.ads.services.content_optimizer import ContentOptimizer
from src.aim.subagents.ads.services.analytics_service import AnalyticsService

__all__ = [
    "CampaignService",
    "ContentOptimizer",
    "AnalyticsService",
]
