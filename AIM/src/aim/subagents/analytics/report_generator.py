"""
Report Generator - Automated Marketing Report Generation.

Generates comprehensive marketing reports with data visualization,
insights, and recommendations for stakeholders.

Based on: Marketing Analytics Best Practices + Data Storytelling Principles
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import structlog


@dataclass
class ReportMetrics:
    """Core metrics for report."""

    period: str  # e.g., "2026-05-01 to 2026-05-14"
    total_traffic: int
    total_conversions: int
    total_revenue: float  # RUB
    total_cost: float  # RUB
    roi: float  # Return on investment (%)
    conversion_rate: float  # %
    avg_order_value: float  # RUB


@dataclass
class ChannelPerformance:
    """Channel performance breakdown."""

    channel: str  # seo, ads, social, email, direct
    traffic: int
    conversions: int
    revenue: float  # RUB
    cost: float  # RUB
    roi: float  # %
    conversion_rate: float  # %
    trend: str  # up, down, stable


@dataclass
class KeyInsight:
    """Key insight from data."""

    title: str
    description: str
    impact: str  # high, medium, low
    metric_change: float  # % change
    recommendation: str


@dataclass
class GoalProgress:
    """Goal progress tracking."""

    goal_name: str
    target_value: float
    current_value: float
    progress_percent: float  # 0-100
    status: str  # on_track, at_risk, behind
    days_remaining: int


@dataclass
class CompetitorComparison:
    """Competitor comparison data."""

    metric: str
    our_value: float
    competitor_avg: float
    difference_percent: float  # % difference
    position: str  # leading, competitive, behind


@dataclass
class Recommendation:
    """Actionable recommendation."""

    priority: str  # high, medium, low
    category: str  # seo, ads, content, technical
    title: str
    description: str
    expected_impact: str
    effort: str  # low, medium, high
    timeline: str  # immediate, short_term, long_term


@dataclass
class MarketingReport:
    """Complete marketing report."""

    report_id: str
    report_name: str
    period: str
    generated_at: str

    # Core sections
    executive_summary: str
    metrics: ReportMetrics
    channel_performance: list[ChannelPerformance]
    key_insights: list[KeyInsight]
    goal_progress: list[GoalProgress]
    competitor_comparison: list[CompetitorComparison]
    recommendations: list[Recommendation]

    # Metadata
    report_type: str  # weekly, monthly, quarterly, custom
    audience: str  # executive, manager, analyst


class ReportGenerator:
    """
    Report Generator.

    Generates comprehensive marketing reports with insights and recommendations.
    """

    def __init__(self):
        """Initialize Report Generator."""
        self.logger = structlog.get_logger()

    async def generate(
        self,
        report_name: str,
        period: str,
        report_type: str = "monthly",
        audience: str = "manager",
        data: dict[str, Any] | None = None,
    ) -> MarketingReport:
        """
        Generate marketing report.

        Args:
            report_name: Report name
            period: Reporting period (e.g., "2026-05-01 to 2026-05-14")
            report_type: Report type (weekly, monthly, quarterly, custom)
            audience: Target audience (executive, manager, analyst)
            data: Report data (if None, will fetch)

        Returns:
            Complete marketing report
        """
        self.logger.info(
            "report_generation_start",
            report_name=report_name,
            period=period,
            report_type=report_type,
        )

        # Fetch data if not provided
        if data is None:
            data = await self._fetch_report_data(period)

        # Step 1: Calculate core metrics
        metrics = await self._calculate_metrics(data)

        # Step 2: Analyze channel performance
        channel_performance = await self._analyze_channels(data)

        # Step 3: Extract key insights
        key_insights = await self._extract_insights(data, metrics, channel_performance)

        # Step 4: Track goal progress
        goal_progress = await self._track_goals(data)

        # Step 5: Compare with competitors
        competitor_comparison = await self._compare_competitors(data)

        # Step 6: Generate recommendations
        recommendations = await self._generate_recommendations(
            metrics, channel_performance, key_insights, goal_progress
        )

        # Step 7: Write executive summary
        executive_summary = await self._write_executive_summary(
            metrics, key_insights, audience
        )

        report = MarketingReport(
            report_id=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            report_name=report_name,
            period=period,
            generated_at=datetime.now().isoformat(),
            executive_summary=executive_summary,
            metrics=metrics,
            channel_performance=channel_performance,
            key_insights=key_insights,
            goal_progress=goal_progress,
            competitor_comparison=competitor_comparison,
            recommendations=recommendations,
            report_type=report_type,
            audience=audience,
        )

        self.logger.info(
            "report_generation_complete",
            report_id=report.report_id,
            insights_count=len(key_insights),
        )

        return report

    async def _fetch_report_data(self, period: str) -> dict[str, Any]:
        """Fetch report data from analytics systems."""
        # Mock data for now (will integrate with real analytics)
        return {
            "total_traffic": 50000,
            "total_conversions": 500,
            "total_revenue": 2500000.0,
            "total_cost": 500000.0,
            "channels": {
                "seo": {
                    "traffic": 20000,
                    "conversions": 250,
                    "revenue": 1250000.0,
                    "cost": 100000.0,
                    "prev_traffic": 18000,
                },
                "ads": {
                    "traffic": 15000,
                    "conversions": 150,
                    "revenue": 750000.0,
                    "cost": 300000.0,
                    "prev_traffic": 16000,
                },
                "social": {
                    "traffic": 10000,
                    "conversions": 80,
                    "revenue": 400000.0,
                    "cost": 80000.0,
                    "prev_traffic": 9000,
                },
                "email": {
                    "traffic": 3000,
                    "conversions": 15,
                    "revenue": 75000.0,
                    "cost": 10000.0,
                    "prev_traffic": 2500,
                },
                "direct": {
                    "traffic": 2000,
                    "conversions": 5,
                    "revenue": 25000.0,
                    "cost": 10000.0,
                    "prev_traffic": 2000,
                },
            },
            "goals": [
                {"name": "Monthly Revenue", "target": 3000000.0, "current": 2500000.0},
                {"name": "Conversions", "target": 600, "current": 500},
                {"name": "ROI", "target": 500.0, "current": 400.0},
            ],
            "competitors": {
                "conversion_rate": {"ours": 1.0, "avg": 0.8},
                "avg_order_value": {"ours": 5000.0, "avg": 4500.0},
                "traffic_growth": {"ours": 15.0, "avg": 10.0},
            },
        }

    async def _calculate_metrics(self, data: dict[str, Any]) -> ReportMetrics:
        """Calculate core metrics."""
        total_traffic = data.get("total_traffic", 0)
        total_conversions = data.get("total_conversions", 0)
        total_revenue = data.get("total_revenue", 0.0)
        total_cost = data.get("total_cost", 0.0)

        roi = ((total_revenue - total_cost) / total_cost * 100) if total_cost > 0 else 0.0
        conversion_rate = (
            (total_conversions / total_traffic * 100) if total_traffic > 0 else 0.0
        )
        avg_order_value = (
            (total_revenue / total_conversions) if total_conversions > 0 else 0.0
        )

        return ReportMetrics(
            period=data.get("period", "N/A"),
            total_traffic=total_traffic,
            total_conversions=total_conversions,
            total_revenue=total_revenue,
            total_cost=total_cost,
            roi=round(roi, 2),
            conversion_rate=round(conversion_rate, 2),
            avg_order_value=round(avg_order_value, 2),
        )

    async def _analyze_channels(
        self, data: dict[str, Any]
    ) -> list[ChannelPerformance]:
        """Analyze channel performance."""
        channels_data = data.get("channels", {})
        channel_performance = []

        for channel, perf in channels_data.items():
            traffic = perf.get("traffic", 0)
            conversions = perf.get("conversions", 0)
            revenue = perf.get("revenue", 0.0)
            cost = perf.get("cost", 0.0)

            roi = ((revenue - cost) / cost * 100) if cost > 0 else 0.0
            conversion_rate = (conversions / traffic * 100) if traffic > 0 else 0.0

            # Determine trend
            prev_traffic = perf.get("prev_traffic", traffic)
            if traffic > prev_traffic * 1.1:
                trend = "up"
            elif traffic < prev_traffic * 0.9:
                trend = "down"
            else:
                trend = "stable"

            channel_performance.append(
                ChannelPerformance(
                    channel=channel,
                    traffic=traffic,
                    conversions=conversions,
                    revenue=revenue,
                    cost=cost,
                    roi=round(roi, 2),
                    conversion_rate=round(conversion_rate, 2),
                    trend=trend,
                )
            )

        # Sort by revenue (descending)
        channel_performance.sort(key=lambda x: x.revenue, reverse=True)

        return channel_performance

    async def _extract_insights(
        self,
        data: dict[str, Any],
        metrics: ReportMetrics,
        channels: list[ChannelPerformance],
    ) -> list[KeyInsight]:
        """Extract key insights from data."""
        insights = []

        # Insight 1: Best performing channel
        if channels:
            best_channel = channels[0]
            insights.append(
                KeyInsight(
                    title=f"{best_channel.channel.upper()} is top revenue driver",
                    description=f"{best_channel.channel.upper()} generated {best_channel.revenue:,.0f} RUB "
                    f"({best_channel.revenue / metrics.total_revenue * 100:.1f}% of total revenue)",
                    impact="high",
                    metric_change=best_channel.roi,
                    recommendation=f"Increase investment in {best_channel.channel.upper()} by 20%",
                )
            )

        # Insight 2: ROI performance
        if metrics.roi >= 400:
            insights.append(
                KeyInsight(
                    title="Strong ROI performance",
                    description=f"Overall ROI of {metrics.roi:.1f}% exceeds industry average",
                    impact="high",
                    metric_change=metrics.roi,
                    recommendation="Maintain current strategy and scale successful campaigns",
                )
            )
        elif metrics.roi < 200:
            insights.append(
                KeyInsight(
                    title="ROI below target",
                    description=f"Current ROI of {metrics.roi:.1f}% needs improvement",
                    impact="high",
                    metric_change=metrics.roi,
                    recommendation="Review and optimize underperforming channels",
                )
            )

        # Insight 3: Channel trends
        growing_channels = [ch for ch in channels if ch.trend == "up"]
        if growing_channels:
            channel_names = ", ".join([ch.channel.upper() for ch in growing_channels])
            insights.append(
                KeyInsight(
                    title=f"Growth in {channel_names}",
                    description=f"{len(growing_channels)} channel(s) showing positive growth",
                    impact="medium",
                    metric_change=15.0,
                    recommendation=f"Capitalize on momentum in {channel_names}",
                )
            )

        return insights

    async def _track_goals(self, data: dict[str, Any]) -> list[GoalProgress]:
        """Track goal progress."""
        goals_data = data.get("goals", [])
        goal_progress = []

        for goal in goals_data:
            name = goal.get("name", "Unknown")
            target = goal.get("target", 0.0)
            current = goal.get("current", 0.0)

            progress = (current / target * 100) if target > 0 else 0.0

            # Determine status
            if progress >= 90:
                status = "on_track"
            elif progress >= 70:
                status = "at_risk"
            else:
                status = "behind"

            goal_progress.append(
                GoalProgress(
                    goal_name=name,
                    target_value=target,
                    current_value=current,
                    progress_percent=round(progress, 2),
                    status=status,
                    days_remaining=14,  # Mock value
                )
            )

        return goal_progress

    async def _compare_competitors(
        self, data: dict[str, Any]
    ) -> list[CompetitorComparison]:
        """Compare with competitors."""
        competitors_data = data.get("competitors", {})
        comparisons = []

        for metric, values in competitors_data.items():
            our_value = values.get("ours", 0.0)
            competitor_avg = values.get("avg", 0.0)

            difference = (
                ((our_value - competitor_avg) / competitor_avg * 100)
                if competitor_avg > 0
                else 0.0
            )

            # Determine position
            if difference > 10:
                position = "leading"
            elif difference > -10:
                position = "competitive"
            else:
                position = "behind"

            comparisons.append(
                CompetitorComparison(
                    metric=metric.replace("_", " ").title(),
                    our_value=our_value,
                    competitor_avg=competitor_avg,
                    difference_percent=round(difference, 2),
                    position=position,
                )
            )

        return comparisons

    async def _generate_recommendations(
        self,
        metrics: ReportMetrics,
        channels: list[ChannelPerformance],
        insights: list[KeyInsight],
        goals: list[GoalProgress],
    ) -> list[Recommendation]:
        """Generate actionable recommendations."""
        recommendations = []

        # Recommendation 1: Scale best channel
        if channels:
            best_channel = channels[0]
            recommendations.append(
                Recommendation(
                    priority="high",
                    category=best_channel.channel,
                    title=f"Scale {best_channel.channel.upper()} investment",
                    description=f"Increase budget by 20% to capitalize on {best_channel.roi:.1f}% ROI",
                    expected_impact=f"+{best_channel.revenue * 0.2:,.0f} RUB revenue",
                    effort="low",
                    timeline="immediate",
                )
            )

        # Recommendation 2: Optimize underperforming channels
        low_roi_channels = [ch for ch in channels if ch.roi < 200]
        if low_roi_channels:
            for channel in low_roi_channels[:2]:  # Top 2 underperformers
                recommendations.append(
                    Recommendation(
                        priority="medium",
                        category=channel.channel,
                        title=f"Optimize {channel.channel.upper()} campaigns",
                        description=f"Current ROI of {channel.roi:.1f}% needs improvement",
                        expected_impact=f"+{channel.revenue * 0.3:,.0f} RUB potential",
                        effort="medium",
                        timeline="short_term",
                    )
                )

        # Recommendation 3: Address behind goals
        behind_goals = [g for g in goals if g.status == "behind"]
        if behind_goals:
            goal = behind_goals[0]
            recommendations.append(
                Recommendation(
                    priority="high",
                    category="strategy",
                    title=f"Accelerate {goal.goal_name} progress",
                    description=f"Currently at {goal.progress_percent:.1f}% of target with {goal.days_remaining} days remaining",
                    expected_impact="Goal achievement",
                    effort="high",
                    timeline="immediate",
                )
            )

        return recommendations

    async def _write_executive_summary(
        self,
        metrics: ReportMetrics,
        insights: list[KeyInsight],
        audience: str,
    ) -> str:
        """Write executive summary."""
        # Adjust detail level based on audience
        if audience == "executive":
            summary = (
                f"Revenue: {metrics.total_revenue:,.0f} RUB | "
                f"ROI: {metrics.roi:.1f}% | "
                f"Conversions: {metrics.total_conversions:,}. "
            )
            if insights:
                summary += f"Key insight: {insights[0].title}."
        else:
            summary = (
                f"Period: {metrics.period}. "
                f"Generated {metrics.total_revenue:,.0f} RUB revenue from {metrics.total_traffic:,} visitors "
                f"with {metrics.roi:.1f}% ROI. "
                f"Conversion rate: {metrics.conversion_rate:.2f}%. "
            )
            if insights:
                summary += f"Top insight: {insights[0].description}"

        return summary


# ==============================================================================
# Added by Teacher Agent: report-generator
# ==============================================================================

from typing import Optional, List, Dict, Any
import asyncio

async def send_notification(
        self,
        user_id: int,
        event_type: str,
        data: Dict[str, Any],
        channels: Optional[List[str]] = None,
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        Send notification to user's configured channels.

        Args:
            user_id: User ID
            event_type: Type of event
            data: Event data
            channels: Specific channels to use (None = use user preferences)
            force: Skip rate limiting and preferences check

        Returns:
            Dict with results for each channel
        """
        if event_type not in self.VALID_EVENTS:
            return {
                "success": False,
                "error": f"Invalid event type: {event_type}",
            }

        # Get user settings
        settings = self._get_user_settings(user_id)
        if not settings:
            return {
                "success": False,
                "error": "User notification settings not found",
            }

        # Check if user wants this notification type
        if not force and not self._should_notify(settings, event_type):
            return {
                "success": True,
                "message": "Notification skipped (user preferences)",
                "channels": {},
            }

        # Determine channels to use
        if not channels:
            channels = self._get_enabled_channels(settings)

        if not channels:
            return {
                "success": True,
                "message": "No channels configured",
                "channels": {},
            }

        # Add timestamp to data
        data["timestamp"] = datetime.now(timezone.utc).isoformat()

        # Send to each channel
        results = {}
        for channel in channels:
            try:
                result = await self._send_to_channel(channel, settings, event_type, data, force)
                results[channel] = result
            except Exception as e:
                logger.error(f"Failed to send {channel} notification: {e}")
                results[channel] = {"success": False, "error": str(e)}

        return {
            "success": any(r.get("success") for r in results.values()),
            "channels": results,
        }