"""Content Magister V2 - Coordinates P1 Content Subagents

Orchestrates three P1 Content subagents to perform comprehensive content workflow:
1. Content Brief Generator - Create content briefs
2. Content Quality Checker - Validate content quality
3. Content Calendar Manager - Schedule and track content

This is the production-ready version integrating Phase 3 trained subagents.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import structlog

from aim.subagents.content.content_brief_generator import (
    ContentBriefGenerator,
    ContentBrief,
)
from aim.subagents.content.content_quality_checker import (
    ContentQualityChecker,
    ContentQualityReport,
)
from aim.subagents.content.content_calendar_manager import (
    ContentCalendarManager,
    ContentCalendarReport,
)
from aim.magisters.linear_mixin import LinearMixin


@dataclass
class ContentWorkflowReport:
    """Complete content workflow report."""

    topic: str
    generated_at: str
    duration_seconds: float

    # Phase 1: Content Brief
    content_brief: ContentBrief

    # Phase 2: Quality Check
    quality_check: ContentQualityReport | None

    # Phase 3: Calendar Planning
    calendar_planning: ContentCalendarReport

    # Overall metrics
    overall_score: float  # 0-100
    priority_actions: list[str]
    estimated_effort: str  # low, medium, high

    # Workflow metadata
    workflow_status: str  # success, partial, failed
    errors: list[str]


class ContentMagisterV2(LinearMixin):
    """
    Content Magister V2 - Production-ready content workflow orchestrator.

    Coordinates three P1 subagents in a sequential workflow:
    1. Content Brief Generator → Create detailed content brief
    2. Content Quality Checker → Validate content quality (optional)
    3. Content Calendar Manager → Schedule and track content

    Each phase uses results from previous phases for context-aware planning.
    """

    def __init__(
        self,
        linear_client: Optional[Any] = None,
        linear_enabled: bool = False,
    ):
        """Initialize Content Magister V2.

        Args:
            linear_client: Optional LinearClient for task tracking
            linear_enabled: Enable Linear integration
        """
        self.logger = structlog.get_logger()
        self.brief_generator = ContentBriefGenerator()
        self.quality_checker = ContentQualityChecker()
        self.calendar_manager = ContentCalendarManager()

        # Setup Linear integration
        self.setup_linear(linear_client, linear_enabled)

    async def execute_workflow(
        self,
        topic: str,
        target_keyword: str | None = None,
        content_text: str | None = None,
        schedule_date: str | None = None,
    ) -> ContentWorkflowReport:
        """
        Execute complete content workflow.

        Args:
            topic: Content topic
            target_keyword: Optional target keyword for SEO
            content_text: Optional content text for quality check
            schedule_date: Optional schedule date (YYYY-MM-DD)

        Returns:
            Complete content workflow report
        """
        self.logger.info("content_workflow_start", topic=topic)
        start_time = datetime.now()
        errors = []

        # Update Linear status
        self.update_linear_status("in_progress")
        self.add_linear_progress_update("Content Workflow", "started", f"Topic: {topic}")

        # Phase 1: Content Brief Generation
        self.logger.info("phase_1_start", phase="content_brief")
        self.add_linear_progress_update("Phase 1: Content Brief", "in_progress")
        try:
            brief = await self.brief_generator.generate(
                target_keyword=target_keyword or topic,
                competitor_urls=[],
            )
            self.logger.info(
                "phase_1_complete",
                word_count=brief.recommended_word_count,
                topics=brief.total_topics,
            )
            self.add_linear_progress_update(
                "Phase 1: Content Brief", "completed",
                f"Word count: {brief.recommended_word_count}, Topics: {brief.total_topics}",
            )
        except Exception as e:
            self.logger.error("phase_1_failed", error=str(e))
            errors.append(f"Content Brief Generation failed: {str(e)}")
            self.add_linear_progress_update("Phase 1: Content Brief", "failed", str(e))
            # Create empty brief to continue workflow
            brief = ContentBrief(
                target_keyword=target_keyword or topic,
                timestamp=datetime.now().isoformat(),
                search_volume=0,
                keyword_difficulty=0.0,
                search_intent="unknown",
                recommended_word_count=0,
                word_count_range=(0, 0),
                tone="",
                header_structure=[],
                topics_to_cover=[],
                total_topics=0,
                questions_to_answer=[],
                total_questions=0,
                competitor_avg_word_count=0,
                competitor_urls=[],
                top_performing_competitor=None,
                title_suggestions=[],
                meta_description_suggestion="",
            )

        # Phase 2: Content Quality Check (optional, only if content provided)
        quality_report = None
        if content_text:
            self.logger.info("phase_2_start", phase="quality_check")
            self.add_linear_progress_update("Phase 2: Quality Check", "in_progress")
            try:
                quality_report = await self.quality_checker.check(
                    url="",
                    content=content_text,
                    target_keyword=target_keyword or brief.target_keyword,
                )
                self.logger.info(
                    "phase_2_complete",
                    overall_score=quality_report.overall_quality_score,
                    grade=quality_report.quality_grade,
                )
                self.add_linear_progress_update(
                    "Phase 2: Quality Check", "completed",
                    f"Score: {quality_report.overall_quality_score}, Grade: {quality_report.quality_grade}",
                )
            except Exception as e:
                self.logger.error("phase_2_failed", error=str(e))
                errors.append(f"Quality Check failed: {str(e)}")
                self.add_linear_progress_update("Phase 2: Quality Check", "failed", str(e))
        else:
            self.logger.info("phase_2_skipped", reason="no_content_provided")

        # Phase 3: Calendar Planning
        self.logger.info("phase_3_start", phase="calendar_planning")
        self.add_linear_progress_update("Phase 3: Calendar Planning", "in_progress")
        try:
            calendar_report = await self.calendar_manager.get_calendar(
                period="month",
            )
            self.logger.info(
                "phase_3_complete",
                scheduled_items=len(calendar_report.calendar_items),
            )
            self.add_linear_progress_update(
                "Phase 3: Calendar Planning", "completed",
                f"Scheduled: {len(calendar_report.calendar_items)} items",
            )
        except Exception as e:
            self.logger.error("phase_3_failed", error=str(e))
            errors.append(f"Calendar Planning failed: {str(e)}")
            self.add_linear_progress_update("Phase 3: Calendar Planning", "failed", str(e))
            # Create empty calendar report to continue workflow
            from aim.subagents.content.content_calendar_manager import (
                CalendarMetrics,
            )

            calendar_report = ContentCalendarReport(
                period="month",
                generated_at=datetime.now().isoformat(),
                calendar_items=[],
                channel_schedules=[],
                content_gaps=[],
                deadline_alerts=[],
                metrics=CalendarMetrics(
                    total_items=0,
                    published_count=0,
                    scheduled_count=0,
                    draft_count=0,
                    overdue_count=0,
                    completion_rate=0.0,
                    avg_production_time=0.0,
                    channel_distribution={},
                ),
                recommendations=[],
            )

        # Calculate overall metrics
        overall_score = self._calculate_overall_score(
            brief, quality_report, calendar_report
        )

        priority_actions = self._generate_priority_actions(
            brief, quality_report, calendar_report
        )

        estimated_effort = self._estimate_effort(brief, quality_report)

        # Determine workflow status
        if not errors:
            workflow_status = "success"
        elif len(errors) < 3:
            workflow_status = "partial"
        else:
            workflow_status = "failed"

        duration = (datetime.now() - start_time).total_seconds()

        report = ContentWorkflowReport(
            topic=topic,
            generated_at=datetime.now().isoformat(),
            duration_seconds=round(duration, 2),
            content_brief=brief,
            quality_check=quality_report,
            calendar_planning=calendar_report,
            overall_score=round(overall_score, 1),
            priority_actions=priority_actions,
            estimated_effort=estimated_effort,
            workflow_status=workflow_status,
            errors=errors,
        )

        # Final Linear status update
        self.update_linear_status(workflow_status)
        self.add_linear_comment(
            f"✅ **Content Workflow Completed**\n\n"
            f"**Overall Score:** {overall_score:.1f}/100\n"
            f"**Duration:** {duration:.1f}s\n\n"
            f"**Top Priority Actions:**\n" +
            "\n".join(f"- {action}" for action in priority_actions[:3])
        )

        self.logger.info(
            "content_workflow_complete",
            topic=topic,
            overall_score=overall_score,
            workflow_status=workflow_status,
            duration=duration,
        )

        return report

    def _calculate_overall_score(
        self,
        brief: ContentBrief,
        quality_report: ContentQualityReport | None,
        calendar_report: ContentCalendarReport,
    ) -> float:
        """
        Calculate overall content score.

        Weighting:
        - Content Brief: 40% (completeness)
        - Quality Check: 40% (if available, otherwise skip)
        - Calendar Planning: 20% (scheduling quality)
        """
        # Brief score: based on completeness
        brief_score = min(
            (len(brief.header_structure) * 10)
            + (brief.total_topics * 5)
            + (brief.total_questions * 5),
            100,
        )

        # Quality score: direct from report if available
        quality_score = quality_report.overall_quality_score if quality_report else None

        # Calendar score: based on scheduled items and gaps
        calendar_score = max(
            100 - (len(calendar_report.content_gaps) * 10)
            - (len(calendar_report.deadline_alerts) * 15),
            0,
        )

        # Weighted average
        if quality_score is not None:
            overall = (
                (brief_score * 0.4) + (quality_score * 0.4) + (calendar_score * 0.2)
            )
        else:
            # Without quality check, redistribute weight
            overall = (brief_score * 0.6) + (calendar_score * 0.4)

        return overall

    def _generate_priority_actions(
        self,
        brief: ContentBrief,
        quality_report: ContentQualityReport | None,
        calendar_report: ContentCalendarReport,
    ) -> list[str]:
        """Generate top 5 priority actions."""
        actions = []

        # From content brief
        if brief.recommended_word_count > 0:
            actions.append(
                f"Write {brief.recommended_word_count} words on '{brief.target_keyword}'"
            )

        # From quality check (top 2 priority issues)
        if quality_report:
            for issue in quality_report.priority_issues[:2]:
                actions.append(issue)

        # From calendar planning (top gap)
        if calendar_report.content_gaps:
            gap = calendar_report.content_gaps[0]
            actions.append(f"Fill content gap: {gap.topic} ({gap.keyword})")

        # From calendar conflicts
        if calendar_report.deadline_alerts:
            alert = calendar_report.deadline_alerts[0]
            actions.append(f"Urgent: {alert.title} due in {alert.days_remaining} days")

        return actions[:5]  # Top 5 only

    def _estimate_effort(
        self, brief: ContentBrief, quality_report: ContentQualityReport | None
    ) -> str:
        """Estimate effort required."""
        word_count = brief.recommended_word_count

        # Base effort on word count
        if word_count < 500:
            base_effort = "low"
        elif word_count < 1500:
            base_effort = "medium"
        else:
            base_effort = "high"

        # Adjust based on quality issues
        if quality_report and len(quality_report.priority_issues) > 5:
            if base_effort == "low":
                base_effort = "medium"
            elif base_effort == "medium":
                base_effort = "high"

        return base_effort

    async def execute_brief_generation_only(
        self, target_keyword: str, competitor_urls: list[str] | None = None
    ) -> ContentBrief:
        """Execute only content brief generation phase."""
        return await self.brief_generator.generate(
            target_keyword=target_keyword,
            competitor_urls=competitor_urls or [],
        )

    async def execute_quality_check_only(
        self, content: str, target_keyword: str
    ) -> ContentQualityReport:
        """Execute only quality check phase."""
        return await self.quality_checker.check(
            url="",
            content=content,
            target_keyword=target_keyword,
        )

    async def execute_calendar_planning_only(
        self,
        period: str = "month",
    ) -> ContentCalendarReport:
        """Execute only calendar planning phase."""
        return await self.calendar_manager.get_calendar(
            period=period,
        )
