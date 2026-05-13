"""
Ads Services Layer.

High-level business logic for campaign management, content optimization, and analytics.
"""

from AIM.src.aim.subagents.ads.services.campaign_service import CampaignService
from AIM.src.aim.subagents.ads.services.content_optimizer import ContentOptimizer
from AIM.src.aim.subagents.ads.services.analytics_service import AnalyticsService

__all__ = [
    "CampaignService",
    "ContentOptimizer",
    "AnalyticsService",
]
