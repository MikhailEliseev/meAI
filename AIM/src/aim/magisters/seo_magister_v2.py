"""SEO Magister V2 - Coordinates P1 SEO Subagents

Orchestrates three P1 SEO subagents to perform comprehensive SEO workflow:
1. Keyword Research Agent - Find target keywords
2. On-Page SEO Optimizer - Optimize page elements
3. Schema Markup Generator - Add structured data

This is the production-ready version integrating Phase 3 trained subagents.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import structlog

from AIM.src.aim.subagents.seo.keyword_research_agent import (
    KeywordResearchAgent,
    KeywordResearchResult,
)
from AIM.src.aim.subagents.seo.onpage_optimizer import (
    OnPageOptimizer,
    OnPageReport,
)
from AIM.src.aim.subagents.seo.schema_generator import (
    SchemaGenerator,
    SchemaReport,
)
from AIM.src.aim.magisters.linear_mixin import LinearMixin


@dataclass
class SEOWorkflowReport:
    """Complete SEO workflow report."""

    url: str
    generated_at: str
    duration_seconds: float

    # Phase 1: Keyword Research
    keyword_research: KeywordResearchResult

    # Phase 2: On-Page Optimization
    on_page_optimization: OnPageReport

    # Phase 3: Schema Markup
    schema_markup: SchemaReport

    # Overall metrics
    overall_score: float  # 0-100
    priority_actions: list[str]
    estimated_impact: str  # high, medium, low

    # Workflow metadata
    workflow_status: str  # success, partial, failed
    errors: list[str]


class SEOMagisterV2(LinearMixin):
    """
    SEO Magister V2 - Production-ready SEO workflow orchestrator.

    Coordinates three P1 subagents in a sequential workflow:
    1. Keyword Research → Find target keywords
    2. On-Page Optimization → Optimize page for keywords
    3. Schema Markup → Add structured data

    Each phase uses results from previous phases for context-aware optimization.
    """

    def __init__(
        self,
        linear_client: Optional[Any] = None,
        linear_enabled: bool = False,
    ):
        """Initialize SEO Magister V2.

        Args:
            linear_client: Optional LinearClient for task tracking
            linear_enabled: Enable Linear integration
        """
        self.logger = structlog.get_logger()
        self.keyword_agent = KeywordResearchAgent()
        self.onpage_agent = OnPageOptimizer()
        self.schema_agent = SchemaGenerator()

        # Setup Linear integration
        self.setup_linear(linear_client, linear_enabled)

    async def execute_workflow(
        self,
        url: str,
        seed_keyword: str,
        html_content: str | None = None,
    ) -> SEOWorkflowReport:
        """
        Execute complete SEO workflow.

        Args:
            url: Target URL to optimize
            seed_keyword: Seed keyword for research
            html_content: Optional HTML content (if None, will fetch)

        Returns:
            Complete SEO workflow report
        """
        self.logger.info("seo_workflow_start", url=url, seed_keyword=seed_keyword)
        start_time = datetime.now()
        errors = []

        # Update Linear status to in_progress
        self.update_linear_status("in_progress")
        self.add_linear_progress_update("SEO Workflow", "started", f"Analyzing {url}")

        # Phase 1: Keyword Research
        self.logger.info("phase_1_start", phase="keyword_research")
        self.add_linear_progress_update("Phase 1: Keyword Research", "in_progress")
        try:
            keyword_report = await self.keyword_agent.research(
                seed_keyword=seed_keyword,
                max_keywords=50,
                min_volume=10,
            )
            self.logger.info(
                "phase_1_complete",
                keywords_found=len(keyword_report.keywords),
                top_keyword=keyword_report.top_opportunities[0].keyword
                if keyword_report.top_opportunities
                else None,
            )
            self.add_linear_progress_update(
                "Phase 1: Keyword Research",
                "completed",
                f"Found {len(keyword_report.keywords)} keywords",
            )
        except Exception as e:
            self.logger.error("phase_1_failed", error=str(e))
            errors.append(f"Keyword Research failed: {str(e)}")
            self.add_linear_progress_update("Phase 1: Keyword Research", "failed", str(e))
            # Create empty report to continue workflow
            keyword_report = KeywordResearchResult(
                seed_keyword=seed_keyword,
                timestamp=datetime.now().isoformat(),
                keywords=[],
                total_keywords=0,
                intents=[],
                clusters=[],
                total_clusters=0,
                priorities=[],
                total_volume=0,
                avg_difficulty=0.0,
                avg_cpc=0.0,
                top_opportunities=[],
            )

        # Phase 2: On-Page Optimization
        self.logger.info("phase_2_start", phase="on_page_optimization")
        self.add_linear_progress_update("Phase 2: On-Page Optimization", "in_progress")
        try:
            # Use top keyword from research as target
            target_keyword = (
                keyword_report.top_opportunities[0].keyword
                if keyword_report.top_opportunities
                else seed_keyword
            )

            onpage_report = await self.onpage_agent.analyze(
                url=url,
                target_keyword=target_keyword,
                html_content=html_content,
            )
            self.logger.info(
                "phase_2_complete",
                overall_score=onpage_report.overall_score,
                priority_issues=len(onpage_report.priority_issues),
            )
            self.add_linear_progress_update(
                "Phase 2: On-Page Optimization",
                "completed",
                f"Score: {onpage_report.overall_score}/100, {len(onpage_report.priority_issues)} priority issues",
            )
        except Exception as e:
            self.logger.error("phase_2_failed", error=str(e))
            errors.append(f"On-Page Optimization failed: {str(e)}")
            self.add_linear_progress_update("Phase 2: On-Page Optimization", "failed", str(e))
            # Create empty report to continue workflow
            from AIM.src.aim.subagents.seo.onpage_optimizer import (
                TitleTagAnalysis,
                MetaDescriptionAnalysis,
                HeaderStructure,
                ContentAnalysis,
                InternalLinking,
                ImageOptimization,
                URLAnalysis,
            )

            onpage_report = OnPageReport(
                url=url,
                timestamp=datetime.now().isoformat(),
                title_tag=TitleTagAnalysis(
                    title="",
                    length=0,
                    has_keyword=False,
                    keyword_position=0,
                    is_optimal_length=False,
                    issues=["Analysis failed"],
                    recommendations=[],
                ),
                meta_description=MetaDescriptionAnalysis(
                    description="",
                    length=0,
                    has_keyword=False,
                    has_cta=False,
                    is_optimal_length=False,
                    issues=["Analysis failed"],
                    recommendations=[],
                ),
                headers=HeaderStructure(
                    h1_count=0,
                    h1_text=[],
                    h2_count=0,
                    h3_count=0,
                    has_keyword_in_h1=False,
                    hierarchy_valid=False,
                    issues=["Analysis failed"],
                    recommendations=[],
                ),
                content=ContentAnalysis(
                    word_count=0,
                    keyword_density=0.0,
                    keyword_count=0,
                    readability_score=0.0,
                    paragraph_count=0,
                    avg_paragraph_length=0.0,
                    has_lists=False,
                    has_images=False,
                    issues=["Analysis failed"],
                    recommendations=[],
                ),
                internal_linking=InternalLinking(
                    total_links=0,
                    internal_links=0,
                    external_links=0,
                    broken_links=0,
                    anchor_text_optimized=False,
                    link_depth=0,
                    issues=["Analysis failed"],
                    recommendations=[],
                ),
                images=ImageOptimization(
                    total_images=0,
                    images_with_alt=0,
                    images_without_alt=0,
                    alt_text_quality=0.0,
                    large_images=0,
                    webp_usage=0.0,
                    issues=["Analysis failed"],
                    recommendations=[],
                ),
                url_analysis=URLAnalysis(
                    url=url,
                    length=len(url),
                    has_keyword=False,
                    is_readable=False,
                    has_special_chars=False,
                    depth=0,
                    issues=["Analysis failed"],
                    recommendations=[],
                ),
                overall_score=0.0,
                priority_issues=[],
                quick_wins=[],
            )

        # Phase 3: Schema Markup
        self.logger.info("phase_3_start", phase="schema_markup")
        self.add_linear_progress_update("Phase 3: Schema Markup", "in_progress")
        try:
            schema_report = await self.schema_agent.analyze_page(
                url=url,
                html_content=html_content,
            )
            self.logger.info(
                "phase_3_complete",
                schemas_found=len(schema_report.schemas),
                missing_schemas=len(schema_report.missing_schemas),
            )
            self.add_linear_progress_update(
                "Phase 3: Schema Markup",
                "completed",
                f"Found {len(schema_report.schemas)} schemas, {len(schema_report.missing_schemas)} missing",
            )
        except Exception as e:
            self.logger.error("phase_3_failed", error=str(e))
            errors.append(f"Schema Markup failed: {str(e)}")
            self.add_linear_progress_update("Phase 3: Schema Markup", "failed", str(e))
            # Create empty report to continue workflow
            schema_report = SchemaReport(
                url=url,
                timestamp=datetime.now().isoformat(),
                schemas=[],
                validation_results=[],
                missing_schemas=[],
                rich_results_eligible=False,
                overall_score=0.0,
            )

        # Calculate overall metrics
        overall_score = self._calculate_overall_score(
            keyword_report, onpage_report, schema_report
        )

        priority_actions = self._generate_priority_actions(
            keyword_report, onpage_report, schema_report
        )

        estimated_impact = self._estimate_impact(overall_score, priority_actions)

        # Determine workflow status
        if not errors:
            workflow_status = "success"
        elif len(errors) < 3:
            workflow_status = "partial"
        else:
            workflow_status = "failed"

        duration = (datetime.now() - start_time).total_seconds()

        report = SEOWorkflowReport(
            url=url,
            generated_at=datetime.now().isoformat(),
            duration_seconds=round(duration, 2),
            keyword_research=keyword_report,
            on_page_optimization=onpage_report,
            schema_markup=schema_report,
            overall_score=round(overall_score, 1),
            priority_actions=priority_actions,
            estimated_impact=estimated_impact,
            workflow_status=workflow_status,
            errors=errors,
        )

        self.logger.info(
            "seo_workflow_complete",
            url=url,
            overall_score=overall_score,
            workflow_status=workflow_status,
            duration=duration,
        )

        # Update Linear with final status
        if workflow_status == "success":
            self.update_linear_status("completed")
            self.add_linear_comment(
                f"✅ **SEO Workflow Completed**\n\n"
                f"**Overall Score:** {overall_score:.1f}/100\n"
                f"**Duration:** {duration:.1f}s\n"
                f"**Impact:** {estimated_impact}\n\n"
                f"**Top Priority Actions:**\n" +
                "\n".join(f"- {action}" for action in priority_actions[:3])
            )
        elif workflow_status == "partial":
            self.update_linear_status("completed")
            self.add_linear_comment(
                f"⚠️ **SEO Workflow Partially Completed**\n\n"
                f"**Overall Score:** {overall_score:.1f}/100\n"
                f"**Errors:** {len(errors)}\n\n" +
                "\n".join(f"- {error}" for error in errors)
            )
        else:
            self.update_linear_status("failed")
            self.add_linear_comment(
                f"❌ **SEO Workflow Failed**\n\n"
                f"**Errors:** {len(errors)}\n\n" +
                "\n".join(f"- {error}" for error in errors)
            )

        return report

    def _calculate_overall_score(
        self,
        keyword_report: KeywordResearchResult,
        onpage_report: OnPageReport,
        schema_report: SchemaReport,
    ) -> float:
        """
        Calculate overall SEO score.

        Weighting:
        - Keyword Research: 30% (opportunity quality)
        - On-Page Optimization: 50% (most critical)
        - Schema Markup: 20% (nice to have)
        """
        # Keyword score: based on opportunities found
        keyword_score = min(len(keyword_report.top_opportunities) * 10, 100)

        # On-page score: direct from report
        onpage_score = onpage_report.overall_score

        # Schema score: direct from report
        schema_score = schema_report.overall_score

        # Weighted average
        overall = (keyword_score * 0.3) + (onpage_score * 0.5) + (schema_score * 0.2)

        return overall

    def _generate_priority_actions(
        self,
        keyword_report: KeywordResearchResult,
        onpage_report: OnPageReport,
        schema_report: SchemaReport,
    ) -> list[str]:
        """Generate top 5 priority actions."""
        actions = []

        # From keyword research
        if keyword_report.top_opportunities:
            top_kw = keyword_report.top_opportunities[0]
            actions.append(
                f"Target '{top_kw.keyword}' (volume: {top_kw.volume}, difficulty: {top_kw.difficulty})"
            )

        # From on-page optimization (top 3 priority issues)
        for issue in onpage_report.priority_issues[:3]:
            actions.append(issue)

        # From schema markup (top missing schema)
        if schema_report.missing_schemas:
            missing = schema_report.missing_schemas[0]
            actions.append(f"Add {missing} schema markup")

        return actions[:5]  # Top 5 only

    def _estimate_impact(self, overall_score: float, priority_actions: list[str]) -> str:
        """Estimate impact of implementing recommendations."""
        if overall_score < 40:
            return "high"  # Low score = high impact potential
        elif overall_score < 70:
            return "medium"
        else:
            return "low"  # Already good = low impact

    async def execute_keyword_research_only(
        self, seed_keyword: str, max_keywords: int = 50
    ) -> KeywordResearchResult:
        """Execute only keyword research phase."""
        return await self.keyword_agent.research(
            seed_keyword=seed_keyword,
            max_keywords=max_keywords,
            min_volume=10,
        )

    async def execute_onpage_optimization_only(
        self, url: str, target_keyword: str, html_content: str | None = None
    ) -> OnPageReport:
        """Execute only on-page optimization phase."""
        return await self.onpage_agent.analyze(
            url=url,
            target_keyword=target_keyword,
            html_content=html_content,
        )

    async def execute_schema_generation_only(
        self, url: str, html_content: str | None = None
    ) -> SchemaReport:
        """Execute only schema markup phase."""
        return await self.schema_agent.analyze_page(
            url=url,
            html_content=html_content,
        )
