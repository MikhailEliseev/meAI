"""Ads Magister V2 - Coordinates P1 Ads Subagents

Orchestrates three P1 Ads subagents to perform comprehensive advertising workflow:
1. Ad Copy Generator - Create ad copy variants
2. Landing Page Analyzer - Validate landing page quality
3. Bid Strategy Optimizer - Optimize bid strategies

This is the production-ready version integrating Phase 3 trained subagents.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import structlog

from src.aim.subagents.ads.ad_copy_generator import (
    AdCopyGenerator,
    AdCopySet,
)
from src.aim.subagents.ads.landing_page_analyzer import (
    LandingPageAnalyzer,
    LandingPageReport,
)
from src.aim.subagents.ads.bid_strategy_optimizer import (
    BidStrategyOptimizer,
    BidOptimizationReport,
)
from src.aim.magisters.linear_mixin import LinearMixin


@dataclass
class AdsWorkflowReport:
    """Complete ads workflow report."""

    campaign_name: str
    generated_at: str
    duration_seconds: float

    # Phase 1: Ad Copy Generation
    ad_copy: AdCopySet

    # Phase 2: Landing Page Analysis
    landing_page: LandingPageReport | None

    # Phase 3: Bid Optimization
    bid_optimization: BidOptimizationReport | None

    # Overall metrics
    overall_score: float  # 0-100
    priority_actions: list[str]
    estimated_impact: str  # high, medium, low

    # Workflow metadata
    workflow_status: str  # success, partial, failed
    errors: list[str]


class AdsMagisterV2(LinearMixin):
    """
    Ads Magister V2 - Production-ready ads workflow orchestrator.

    Coordinates three P1 subagents in a sequential workflow:
    1. Ad Copy Generator → Create ad copy variants
    2. Landing Page Analyzer → Validate landing page quality
    3. Bid Strategy Optimizer → Optimize bid strategies

    Each phase uses results from previous phases for context-aware optimization.
    """

    def __init__(
        self,
        linear_client: Optional[Any] = None,
        linear_enabled: bool = False,
    ):
        """Initialize Ads Magister V2.

        Args:
            linear_client: Optional LinearClient for task tracking
            linear_enabled: Enable Linear integration
        """
        self.logger = structlog.get_logger()
        self.ad_copy_generator = AdCopyGenerator()
        self.landing_page_analyzer = LandingPageAnalyzer()
        self.bid_optimizer = BidStrategyOptimizer()

        # Setup Linear integration
        self.setup_linear(linear_client, linear_enabled)

    async def execute_workflow(
        self,
        campaign_name: str,
        target_keyword: str,
        product_name: str,
        benefits: list[str],
        landing_page_url: str | None = None,
        campaign_id: str | None = None,
        platform: str = "yandex",
    ) -> AdsWorkflowReport:
        """
        Execute complete ads workflow.

        Args:
            campaign_name: Campaign name
            target_keyword: Target keyword for ads
            product_name: Product/service name
            benefits: List of product benefits
            landing_page_url: Optional landing page URL for analysis
            campaign_id: Optional campaign ID for bid optimization
            platform: Platform (yandex, google, both)

        Returns:
            Complete ads workflow report
        """
        self.logger.info("ads_workflow_start", campaign=campaign_name)
        start_time = datetime.now()
        errors = []

        # Update Linear status
        self.update_linear_status("in_progress")
        self.add_linear_progress_update("Ads Workflow", "started", f"Campaign: {campaign_name}")

        # Phase 1: Ad Copy Generation
        self.logger.info("phase_1_start", phase="ad_copy_generation")
        self.add_linear_progress_update("Phase 1: Ad Copy", "in_progress")
        try:
            ad_copy = await self.ad_copy_generator.generate(
                target_keyword=target_keyword,
                product_name=product_name,
                benefits=benefits,
                platform=platform,
            )
            self.logger.info(
                "phase_1_complete",
                total_variants=ad_copy.total_variants,
                yandex_variants=len(ad_copy.yandex_variants),
                google_variants=len(ad_copy.google_variants),
            )
            self.add_linear_progress_update(
                "Phase 1: Ad Copy", "completed",
                f"Variants: {ad_copy.total_variants} (Yandex: {len(ad_copy.yandex_variants)}, Google: {len(ad_copy.google_variants)})",
            )
        except Exception as e:
            self.logger.error("phase_1_failed", error=str(e))
            errors.append(f"Ad Copy Generation failed: {str(e)}")
            self.add_linear_progress_update("Phase 1: Ad Copy", "failed", str(e))
            # Create empty ad copy set to continue workflow
            from src.aim.subagents.ads.ad_copy_generator import (
                AdCopySet,
            )

            ad_copy = AdCopySet(
                target_keyword=target_keyword,
                timestamp=datetime.now().isoformat(),
                variants=[],
                total_variants=0,
                headlines=[],
                total_headlines=0,
                descriptions=[],
                total_descriptions=0,
                ctas=[],
                total_ctas=0,
                yandex_variants=[],
                google_variants=[],
            )

        # Phase 2: Landing Page Analysis (optional, only if URL provided)
        landing_page_report = None
        if landing_page_url:
            self.logger.info("phase_2_start", phase="landing_page_analysis")
            self.add_linear_progress_update("Phase 2: Landing Page", "in_progress")
            try:
                # Use first ad variant headline for relevance check
                ad_headline = (
                    ad_copy.variants[0].headline if ad_copy.variants else None
                )

                landing_page_report = await self.landing_page_analyzer.analyze(
                    url=landing_page_url,
                    ad_keyword=target_keyword,
                    ad_headline=ad_headline,
                )
                self.logger.info(
                    "phase_2_complete",
                    overall_score=landing_page_report.overall_quality_score,
                    rating=landing_page_report.quality_rating,
                )
                self.add_linear_progress_update(
                    "Phase 2: Landing Page", "completed",
                    f"Score: {landing_page_report.overall_quality_score}, Rating: {landing_page_report.quality_rating}",
                )
            except Exception as e:
                self.logger.error("phase_2_failed", error=str(e))
                errors.append(f"Landing Page Analysis failed: {str(e)}")
                self.add_linear_progress_update("Phase 2: Landing Page", "failed", str(e))
        else:
            self.logger.info("phase_2_skipped", reason="no_landing_page_url")

        # Phase 3: Bid Optimization (optional, only if campaign_id provided)
        bid_optimization_report = None
        if campaign_id:
            self.logger.info("phase_3_start", phase="bid_optimization")
            self.add_linear_progress_update("Phase 3: Bid Optimization", "in_progress")
            try:
                bid_optimization_report = await self.bid_optimizer.optimize(
                    campaign_id=campaign_id,
                    campaign_name=campaign_name,
                    platform=platform,
                )
                self.logger.info(
                    "phase_3_complete",
                    optimization_score=bid_optimization_report.optimization_score,
                )
                self.add_linear_progress_update(
                    "Phase 3: Bid Optimization", "completed",
                    f"Score: {bid_optimization_report.optimization_score}",
                )
            except Exception as e:
                self.logger.error("phase_3_failed", error=str(e))
                errors.append(f"Bid Optimization failed: {str(e)}")
                self.add_linear_progress_update("Phase 3: Bid Optimization", "failed", str(e))
        else:
            self.logger.info("phase_3_skipped", reason="no_campaign_id")

        # Calculate overall metrics
        overall_score = self._calculate_overall_score(
            ad_copy, landing_page_report, bid_optimization_report
        )

        priority_actions = self._generate_priority_actions(
            ad_copy, landing_page_report, bid_optimization_report
        )

        estimated_impact = self._estimate_impact(
            overall_score, landing_page_report, bid_optimization_report
        )

        # Determine workflow status
        if not errors:
            workflow_status = "success"
        elif len(errors) < 3:
            workflow_status = "partial"
        else:
            workflow_status = "failed"

        duration = (datetime.now() - start_time).total_seconds()

        report = AdsWorkflowReport(
            campaign_name=campaign_name,
            generated_at=datetime.now().isoformat(),
            duration_seconds=round(duration, 2),
            ad_copy=ad_copy,
            landing_page=landing_page_report,
            bid_optimization=bid_optimization_report,
            overall_score=round(overall_score, 1),
            priority_actions=priority_actions,
            estimated_impact=estimated_impact,
            workflow_status=workflow_status,
            errors=errors,
        )

        # Final Linear status update
        self.update_linear_status(workflow_status)
        self.add_linear_comment(
            f"✅ **Ads Workflow Completed**\n\n"
            f"**Overall Score:** {overall_score:.1f}/100\n"
            f"**Duration:** {duration:.1f}s\n"
            f"**Impact:** {estimated_impact}\n\n"
            f"**Top Priority Actions:**\n" +
            "\n".join(f"- {action}" for action in priority_actions[:3])
        )

        self.logger.info(
            "ads_workflow_complete",
            campaign=campaign_name,
            overall_score=overall_score,
            workflow_status=workflow_status,
            duration=duration,
        )

        return report

    def _calculate_overall_score(
        self,
        ad_copy: AdCopySet,
        landing_page: LandingPageReport | None,
        bid_optimization: BidOptimizationReport | None,
    ) -> float:
        """
        Calculate overall ads score.

        Weighting:
        - Ad Copy: 40% (variant quality and compliance)
        - Landing Page: 30% (if available, otherwise skip)
        - Bid Optimization: 30% (if available, otherwise skip)
        """
        # Ad copy score: based on compliant variants
        compliant_variants = sum(
            1 for v in ad_copy.variants if v.compliance.is_compliant
        )
        total_variants = ad_copy.total_variants
        ad_copy_score = (
            (compliant_variants / total_variants * 100) if total_variants > 0 else 0
        )

        # Landing page score: direct from report if available
        landing_page_score = (
            landing_page.overall_quality_score if landing_page else None
        )

        # Bid optimization score: direct from report if available
        bid_optimization_score = (
            bid_optimization.optimization_score if bid_optimization else None
        )

        # Weighted average
        if landing_page_score is not None and bid_optimization_score is not None:
            # All three phases available
            overall = (
                (ad_copy_score * 0.4)
                + (landing_page_score * 0.3)
                + (bid_optimization_score * 0.3)
            )
        elif landing_page_score is not None:
            # Ad copy + landing page only
            overall = (ad_copy_score * 0.6) + (landing_page_score * 0.4)
        elif bid_optimization_score is not None:
            # Ad copy + bid optimization only
            overall = (ad_copy_score * 0.6) + (bid_optimization_score * 0.4)
        else:
            # Ad copy only
            overall = ad_copy_score

        return overall

    def _generate_priority_actions(
        self,
        ad_copy: AdCopySet,
        landing_page: LandingPageReport | None,
        bid_optimization: BidOptimizationReport | None,
    ) -> list[str]:
        """Generate top 5 priority actions."""
        actions = []

        # From ad copy (top non-compliant variant)
        non_compliant = [v for v in ad_copy.variants if not v.compliance.is_compliant]
        if non_compliant:
            variant = non_compliant[0]
            if variant.compliance.violations:
                actions.append(
                    f"Fix ad copy violations: {variant.compliance.violations[0]}"
                )

        # From landing page (top 2 priority issues)
        if landing_page:
            for issue in landing_page.priority_issues[:2]:
                actions.append(issue)

        # From bid optimization (top priority action)
        if bid_optimization:
            if bid_optimization.priority_actions:
                actions.append(bid_optimization.priority_actions[0])

        # Add quick wins if space available
        if len(actions) < 5:
            if landing_page and landing_page.quick_wins:
                actions.append(f"Quick win: {landing_page.quick_wins[0]}")

        if len(actions) < 5:
            if bid_optimization and bid_optimization.quick_wins:
                actions.append(f"Quick win: {bid_optimization.quick_wins[0]}")

        return actions[:5]  # Top 5 only

    def _estimate_impact(
        self,
        overall_score: float,
        landing_page: LandingPageReport | None,
        bid_optimization: BidOptimizationReport | None,
    ) -> str:
        """Estimate potential impact of improvements."""
        # Base impact on overall score
        if overall_score < 50:
            base_impact = "high"
        elif overall_score < 70:
            base_impact = "medium"
        else:
            base_impact = "low"

        # Adjust based on bid optimization potential
        if bid_optimization:
            if (
                not bid_optimization.strategy.is_optimal
                and bid_optimization.strategy.expected_improvement > 10
            ):
                # Strategy change can have high impact
                if base_impact == "medium":
                    base_impact = "high"

        # Adjust based on landing page issues
        if landing_page:
            critical_issues = [
                issue
                for issue in landing_page.priority_issues
                if "CRITICAL" in issue
            ]
            if critical_issues and base_impact == "medium":
                base_impact = "high"

        return base_impact

    async def execute_ad_copy_generation_only(
        self,
        target_keyword: str,
        product_name: str,
        benefits: list[str],
        platform: str = "both",
    ) -> AdCopySet:
        """Execute only ad copy generation phase."""
        return await self.ad_copy_generator.generate(
            target_keyword=target_keyword,
            product_name=product_name,
            benefits=benefits,
            platform=platform,
        )

    async def execute_landing_page_analysis_only(
        self,
        url: str,
        ad_keyword: str | None = None,
        ad_headline: str | None = None,
    ) -> LandingPageReport:
        """Execute only landing page analysis phase."""
        return await self.landing_page_analyzer.analyze(
            url=url,
            ad_keyword=ad_keyword,
            ad_headline=ad_headline,
        )

    async def execute_bid_optimization_only(
        self,
        campaign_id: str,
        campaign_name: str,
        platform: str,
    ) -> BidOptimizationReport:
        """Execute only bid optimization phase."""
        return await self.bid_optimizer.optimize(
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            platform=platform,
        )
