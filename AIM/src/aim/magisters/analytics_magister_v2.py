"""Analytics Magister V2 - Coordinates P1 Analytics Subagents

Orchestrates three P1 Analytics subagents to perform comprehensive analytics workflow:
1. Traffic Analyzer - Analyze website traffic patterns
2. Conversion Tracker - Track conversions and revenue
3. Report Generator - Generate marketing reports

This is the production-ready version integrating Phase 3 trained subagents.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import structlog

from aim.subagents.analytics.traffic_analyzer import (
    TrafficAnalyzer,
    TrafficReport,
)
from aim.subagents.analytics.conversion_tracker import (
    ConversionTracker,
    ConversionReport,
)
from aim.subagents.analytics.report_generator import (
    ReportGenerator,
    MarketingReport,
)
from aim.magisters.linear_mixin import LinearMixin


@dataclass
class AnalyticsWorkflowReport:
    """Complete analytics workflow report."""

    period: str
    generated_at: str
    duration_seconds: float

    # Phase 1: Traffic Analysis
    traffic_analysis: TrafficReport

    # Phase 2: Conversion Tracking
    conversion_tracking: ConversionReport

    # Phase 3: Report Generation
    marketing_report: MarketingReport

    # Overall metrics
    overall_score: float  # 0-100
    priority_actions: list[str]
    estimated_impact: str  # high, medium, low

    # Workflow metadata
    workflow_status: str  # success, partial, failed
    errors: list[str]


class AnalyticsMagisterV2(LinearMixin):
    """
    Analytics Magister V2 - Production-ready analytics workflow orchestrator.

    Coordinates three P1 subagents in a sequential workflow:
    1. Traffic Analyzer → Analyze website traffic patterns
    2. Conversion Tracker → Track conversions and revenue
    3. Report Generator → Generate comprehensive marketing reports

    Each phase uses results from previous phases for context-aware reporting.
    """

    def __init__(
        self,
        linear_client: Optional[Any] = None,
        linear_enabled: bool = False,
    ):
        """Initialize Analytics Magister V2.

        Args:
            linear_client: Optional LinearClient for task tracking
            linear_enabled: Enable Linear integration
        """
        self.logger = structlog.get_logger()
        self.traffic_analyzer = TrafficAnalyzer()
        self.conversion_tracker = ConversionTracker()
        self.report_generator = ReportGenerator()

        # Setup Linear integration
        self.setup_linear(linear_client, linear_enabled)

    async def execute_workflow(
        self,
        start_date: str,
        end_date: str,
        report_name: str = "Marketing Analytics Report",
        report_type: str = "monthly",
        audience: str = "manager",
        source: str = "ga4",
    ) -> AnalyticsWorkflowReport:
        """
        Execute complete analytics workflow.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            report_name: Report name
            report_type: Report type (weekly, monthly, quarterly, custom)
            audience: Target audience (executive, manager, analyst)
            source: Data source (ga4, yandex, both)

        Returns:
            Complete analytics workflow report
        """
        self.logger.info("analytics_workflow_start", period=f"{start_date} to {end_date}")
        start_time = datetime.now()
        errors = []

        # Update Linear status
        self.update_linear_status("in_progress")
        self.add_linear_progress_update("Analytics Workflow", "started", f"Period: {start_date} to {end_date}")

        # Phase 1: Traffic Analysis
        self.logger.info("phase_1_start", phase="traffic_analysis")
        self.add_linear_progress_update("Phase 1: Traffic Analysis", "in_progress")
        try:
            traffic_report = await self.traffic_analyzer.analyze(
                start_date=start_date,
                end_date=end_date,
                source=source,
            )
            self.logger.info(
                "phase_1_complete",
                total_sessions=traffic_report.total_sessions,
                total_users=traffic_report.total_users,
            )
            self.add_linear_progress_update(
                "Phase 1: Traffic Analysis", "completed",
                f"Sessions: {traffic_report.total_sessions}, Users: {traffic_report.total_users}",
            )
        except Exception as e:
            self.logger.error("phase_1_failed", error=str(e))
            errors.append(f"Traffic Analysis failed: {str(e)}")
            self.add_linear_progress_update("Phase 1: Traffic Analysis", "failed", str(e))
            # Create empty traffic report to continue workflow
            from aim.subagents.analytics.traffic_analyzer import (
                TrafficReport,
                UserBehavior,
                BounceAnalysis,
                SessionAnalysis,
            )

            traffic_report = TrafficReport(
                start_date=start_date,
                end_date=end_date,
                timestamp=datetime.now().isoformat(),
                traffic_sources=[],
                total_sessions=0,
                total_users=0,
                total_pageviews=0,
                user_behavior=UserBehavior(
                    new_users=0,
                    returning_users=0,
                    total_users=0,
                    new_user_rate=0.0,
                    pages_per_session=0.0,
                    avg_session_duration=0.0,
                ),
                conversion_funnel=[],
                overall_conversion_rate=0.0,
                bounce_analysis=BounceAnalysis(
                    overall_bounce_rate=0.0,
                    bounce_by_source={},
                    high_bounce_pages=[],
                    low_bounce_pages=[],
                ),
                session_analysis=SessionAnalysis(
                    avg_duration=0.0,
                    median_duration=0.0,
                    duration_by_source={},
                    short_sessions=0,
                    medium_sessions=0,
                    long_sessions=0,
                ),
                insights=[],
            )

        # Phase 2: Conversion Tracking
        self.logger.info("phase_2_start", phase="conversion_tracking")
        self.add_linear_progress_update("Phase 2: Conversion Tracking", "in_progress")
        try:
            conversion_report = await self.conversion_tracker.track(
                start_date=start_date,
                end_date=end_date,
                source=source,
            )
            self.logger.info(
                "phase_2_complete",
                total_conversions=conversion_report.total_conversions,
                total_revenue=conversion_report.revenue_metrics.total_revenue,
            )
            self.add_linear_progress_update(
                "Phase 2: Conversion Tracking", "completed",
                f"Conversions: {conversion_report.total_conversions}, Revenue: {conversion_report.revenue_metrics.total_revenue}",
            )
        except Exception as e:
            self.logger.error("phase_2_failed", error=str(e))
            errors.append(f"Conversion Tracking failed: {str(e)}")
            self.add_linear_progress_update("Phase 2: Conversion Tracking", "failed", str(e))
            # Create empty conversion report to continue workflow
            from aim.subagents.analytics.conversion_tracker import (
                ConversionReport,
                RevenueMetrics,
                ROIMetrics,
            )

            conversion_report = ConversionReport(
                start_date=start_date,
                end_date=end_date,
                timestamp=datetime.now().isoformat(),
                goals=[],
                total_conversions=0,
                overall_conversion_rate=0.0,
                attributions=[],
                top_converting_source="",
                customer_journeys=[],
                avg_touchpoints=0.0,
                avg_time_to_conversion=0.0,
                revenue_metrics=RevenueMetrics(
                    total_revenue=0.0,
                    avg_order_value=0.0,
                    transactions=0,
                    revenue_per_session=0.0,
                    revenue_per_user=0.0,
                ),
                roi_metrics=ROIMetrics(
                    total_cost=0.0,
                    total_revenue=0.0,
                    total_profit=0.0,
                    roi_percent=0.0,
                    roas=0.0,
                ),
                insights=[],
            )

        # Phase 3: Report Generation
        self.logger.info("phase_3_start", phase="report_generation")
        self.add_linear_progress_update("Phase 3: Report Generation", "in_progress")
        try:
            # Prepare data for report generator
            report_data = {
                "period": f"{start_date} to {end_date}",
                "total_traffic": traffic_report.total_sessions,
                "total_conversions": conversion_report.total_conversions,
                "total_revenue": conversion_report.revenue_metrics.total_revenue,
                "total_cost": conversion_report.roi_metrics.total_cost,
            }

            marketing_report = await self.report_generator.generate(
                report_name=report_name,
                period=f"{start_date} to {end_date}",
                report_type=report_type,
                audience=audience,
                data=report_data,
            )
            self.logger.info(
                "phase_3_complete",
                report_id=marketing_report.report_id,
            )
            self.add_linear_progress_update(
                "Phase 3: Report Generation", "completed",
                f"Report ID: {marketing_report.report_id}",
            )
        except Exception as e:
            self.logger.error("phase_3_failed", error=str(e))
            errors.append(f"Report Generation failed: {str(e)}")
            self.add_linear_progress_update("Phase 3: Report Generation", "failed", str(e))
            # Create empty marketing report to continue workflow
            from aim.subagents.analytics.report_generator import (
                MarketingReport,
                ReportMetrics,
            )

            marketing_report = MarketingReport(
                report_id="error",
                report_name=report_name,
                period=f"{start_date} to {end_date}",
                generated_at=datetime.now().isoformat(),
                executive_summary="Report generation failed",
                metrics=ReportMetrics(
                    period=f"{start_date} to {end_date}",
                    total_traffic=0,
                    total_conversions=0,
                    total_revenue=0.0,
                    total_cost=0.0,
                    roi=0.0,
                    conversion_rate=0.0,
                    avg_order_value=0.0,
                ),
                channel_performance=[],
                key_insights=[],
                goal_progress=[],
                competitor_comparison=[],
                recommendations=[],
                report_type=report_type,
                audience=audience,
            )

        # Calculate overall metrics
        overall_score = self._calculate_overall_score(
            traffic_report, conversion_report, marketing_report
        )

        priority_actions = self._generate_priority_actions(
            traffic_report, conversion_report, marketing_report
        )

        estimated_impact = self._estimate_impact(
            overall_score, traffic_report, conversion_report
        )

        # Determine workflow status
        if not errors:
            workflow_status = "success"
        elif len(errors) < 3:
            workflow_status = "partial"
        else:
            workflow_status = "failed"

        duration = (datetime.now() - start_time).total_seconds()

        report = AnalyticsWorkflowReport(
            period=f"{start_date} to {end_date}",
            generated_at=datetime.now().isoformat(),
            duration_seconds=round(duration, 2),
            traffic_analysis=traffic_report,
            conversion_tracking=conversion_report,
            marketing_report=marketing_report,
            overall_score=round(overall_score, 1),
            priority_actions=priority_actions,
            estimated_impact=estimated_impact,
            workflow_status=workflow_status,
            errors=errors,
        )

        # Final Linear status update
        self.update_linear_status(workflow_status)
        self.add_linear_comment(
            f"✅ **Analytics Workflow Completed**\n\n"
            f"**Overall Score:** {overall_score:.1f}/100\n"
            f"**Duration:** {duration:.1f}s\n"
            f"**Impact:** {estimated_impact}\n\n"
            f"**Top Priority Actions:**\n" +
            "\n".join(f"- {action}" for action in priority_actions[:3])
        )

        self.logger.info(
            "analytics_workflow_complete",
            period=f"{start_date} to {end_date}",
            overall_score=overall_score,
            workflow_status=workflow_status,
            duration=duration,
        )

        return report

    def _calculate_overall_score(
        self,
        traffic: TrafficReport,
        conversion: ConversionReport | None,
        marketing: MarketingReport | None,
    ) -> float:
        """
        Calculate overall analytics score.

        Weighting:
        - Traffic Quality: 30% (bounce rate, session duration)
        - Conversion Performance: 40% (conversion rate, ROI)
        - Report Completeness: 30% (insights, recommendations)
        """
        # Traffic quality score (lower bounce = better, higher duration = better)
        traffic_score = 0.0
        if traffic.bounce_analysis.overall_bounce_rate > 0:
            # Inverse bounce rate (60% bounce = 40 score)
            bounce_score = max(0, 100 - traffic.bounce_analysis.overall_bounce_rate)
            # Session duration score (3 min = 100, 1 min = 33)
            duration_score = min(100, (traffic.session_analysis.avg_duration / 180) * 100)
            traffic_score = (bounce_score * 0.5) + (duration_score * 0.5)

        # Conversion performance score
        conversion_score = 0.0
        if conversion and conversion.overall_conversion_rate > 0:
            # Conversion rate score (10% = 100, 1% = 10)
            conv_rate_score = min(100, conversion.overall_conversion_rate * 10)
            # ROI score (400% = 100, 100% = 25)
            roi_score = min(100, (conversion.roi_metrics.roi_percent / 400) * 100)
            conversion_score = (conv_rate_score * 0.5) + (roi_score * 0.5)

        # Report completeness score
        report_score = 0.0
        if marketing:
            insights_count = len(marketing.key_insights)
            recommendations_count = len(marketing.recommendations)
            report_score = min(100, (insights_count * 20) + (recommendations_count * 10))

        # Weighted average
        if conversion is not None and marketing is not None:
            # All three phases available
            overall = (
                (traffic_score * 0.3)
                + (conversion_score * 0.4)
                + (report_score * 0.3)
            )
        elif conversion is not None:
            # Traffic + conversion only
            overall = (traffic_score * 0.6) + (conversion_score * 0.4)
        elif marketing is not None:
            # Traffic + report only
            overall = (traffic_score * 0.6) + (report_score * 0.4)
        else:
            # Traffic only
            overall = traffic_score

        return overall

    def _generate_priority_actions(
        self,
        traffic: TrafficReport,
        conversion: ConversionReport,
        marketing: MarketingReport,
    ) -> list[str]:
        """Generate top 5 priority actions."""
        actions = []

        # From traffic analysis (top insight)
        if traffic.insights:
            actions.append(f"Traffic: {traffic.insights[0]}")

        # From conversion tracking (top insight)
        if conversion.insights:
            actions.append(f"Conversion: {conversion.insights[0]}")

        # From marketing report (top 2 recommendations)
        if marketing.recommendations:
            for rec in marketing.recommendations[:2]:
                actions.append(
                    f"{rec.priority.upper()}: {rec.title}"
                )

        # Add key insights if space available
        if len(actions) < 5 and marketing.key_insights:
            actions.append(f"Insight: {marketing.key_insights[0].title}")

        return actions[:5]  # Top 5 only

    def _estimate_impact(
        self,
        overall_score: float,
        traffic: TrafficReport | None,
        conversion: ConversionReport | None,
    ) -> str:
        """Estimate potential impact of improvements."""
        # Base impact on overall score
        if overall_score < 50:
            base_impact = "high"
        elif overall_score < 70:
            base_impact = "medium"
        else:
            base_impact = "low"

        # Adjust based on conversion performance
        if conversion and conversion.roi_metrics.roi_percent < 100:
            # Low ROI = high impact potential
            if base_impact == "medium":
                base_impact = "high"

        # Adjust based on traffic quality
        if traffic and traffic.bounce_analysis.overall_bounce_rate > 60:
            # High bounce = high impact potential
            if base_impact == "medium":
                base_impact = "high"

        return base_impact

    async def execute_traffic_analysis_only(
        self,
        start_date: str,
        end_date: str,
        source: str = "ga4",
    ) -> TrafficReport:
        """Execute only traffic analysis phase."""
        return await self.traffic_analyzer.analyze(
            start_date=start_date,
            end_date=end_date,
            source=source,
        )

    async def execute_conversion_tracking_only(
        self,
        start_date: str,
        end_date: str,
        source: str = "ga4",
    ) -> ConversionReport:
        """Execute only conversion tracking phase."""
        return await self.conversion_tracker.track(
            start_date=start_date,
            end_date=end_date,
            source=source,
        )

    async def execute_report_generation_only(
        self,
        report_name: str,
        period: str,
        report_type: str = "monthly",
        audience: str = "manager",
    ) -> MarketingReport:
        """Execute only report generation phase."""
        return await self.report_generator.generate(
            report_name=report_name,
            period=period,
            report_type=report_type,
            audience=audience,
        )
