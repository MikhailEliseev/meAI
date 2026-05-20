"""
ROI Calculator — Return on Ad Spend (ROAS) and Return on Investment (ROI).

Computes campaign-level and channel-level ROI from campaign cost data
and revenue data (from ЮKassa payments).
"""

from dataclasses import dataclass
from datetime import datetime

import structlog


@dataclass
class ChannelROI:
    """ROI breakdown for a single marketing channel."""
    channel: str
    total_cost: float
    total_revenue: float
    conversions: int
    roas: float
    roi: float


@dataclass
class CampaignROIReport:
    """Aggregated ROI report across all channels."""
    total_cost: float
    total_revenue: float
    overall_roas: float
    overall_roi: float
    channels: list[ChannelROI]
    timestamp: str


class ROICalculator:
    """Computes ROAS and ROI from campaign cost and revenue data."""

    def __init__(self):
        self.logger = structlog.get_logger()

    def calculate_roas(self, cost: float, revenue: float) -> float:
        if cost <= 0:
            return 0.0
        return round(revenue / cost, 2)

    def calculate_roi(self, cost: float, revenue: float) -> float:
        if cost <= 0:
            return 0.0
        return round((revenue - cost) / cost, 2)

    def channel_breakdown(
        self,
        channel_data: list[dict],
    ) -> list[ChannelROI]:
        results = []
        for ch in channel_data:
            roas = self.calculate_roas(ch["cost"], ch["revenue"])
            roi = self.calculate_roi(ch["cost"], ch["revenue"])
            results.append(ChannelROI(
                channel=ch["channel"],
                total_cost=ch["cost"],
                total_revenue=ch["revenue"],
                conversions=ch.get("conversions", 0),
                roas=roas,
                roi=roi,
            ))
        return results

    def generate_report(self, channel_data: list[dict]) -> CampaignROIReport:
        channels = self.channel_breakdown(channel_data)

        total_cost = sum(ch.total_cost for ch in channels)
        total_revenue = sum(ch.total_revenue for ch in channels)
        overall_roas = self.calculate_roas(total_cost, total_revenue)
        overall_roi = self.calculate_roi(total_cost, total_revenue)

        report = CampaignROIReport(
            total_cost=total_cost,
            total_revenue=total_revenue,
            overall_roas=overall_roas,
            overall_roi=overall_roi,
            channels=channels,
            timestamp=datetime.now().isoformat(),
        )

        self.logger.info(
            "roi_report_generated",
            overall_roas=overall_roas,
            channels=len(channels),
        )
        return report
