"""Client Project Progress Tracking

Tracks progress metrics for client projects:
- Tasks completed / total tasks
- Budget spent / total budget
- Timeline progress (on track / at risk / behind)
- Quality scores from Magisters
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

import structlog


class TimelineStatus(str, Enum):
    """Timeline status indicators."""

    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    BEHIND = "behind"
    AHEAD = "ahead"


@dataclass
class TaskProgress:
    """Task completion progress."""

    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    pending_tasks: int
    completion_rate: float  # 0.0 to 1.0

    @property
    def completion_percent(self) -> float:
        """Completion percentage (0-100)."""
        return self.completion_rate * 100


@dataclass
class BudgetProgress:
    """Budget utilization progress."""

    total_budget: float
    spent_budget: float
    remaining_budget: float
    utilization_rate: float  # 0.0 to 1.0
    projected_total: Optional[float] = None  # Projected final spend

    @property
    def utilization_percent(self) -> float:
        """Budget utilization percentage (0-100)."""
        return self.utilization_rate * 100

    @property
    def is_over_budget(self) -> bool:
        """Check if over budget."""
        return self.spent_budget > self.total_budget

    @property
    def budget_health(self) -> str:
        """Budget health indicator."""
        if self.is_over_budget:
            return "over_budget"
        elif self.utilization_rate > 0.9:
            return "critical"
        elif self.utilization_rate > 0.75:
            return "warning"
        else:
            return "healthy"


@dataclass
class TimelineProgress:
    """Timeline progress tracking."""

    start_date: datetime
    end_date: datetime
    current_date: datetime
    elapsed_days: int
    total_days: int
    remaining_days: int
    time_progress: float  # 0.0 to 1.0
    work_progress: float  # 0.0 to 1.0 (from tasks)
    status: TimelineStatus

    @property
    def time_percent(self) -> float:
        """Time elapsed percentage (0-100)."""
        return self.time_progress * 100

    @property
    def work_percent(self) -> float:
        """Work completed percentage (0-100)."""
        return self.work_progress * 100

    @property
    def is_on_track(self) -> bool:
        """Check if project is on track."""
        return self.status == TimelineStatus.ON_TRACK

    @property
    def progress_delta(self) -> float:
        """Difference between work and time progress."""
        return self.work_progress - self.time_progress


@dataclass
class QualityMetrics:
    """Quality scores from Magisters."""

    seo_score: Optional[float] = None  # 0-100
    content_score: Optional[float] = None  # 0-100
    ads_score: Optional[float] = None  # 0-100
    overall_score: Optional[float] = None  # 0-100

    @property
    def has_scores(self) -> bool:
        """Check if any scores are available."""
        return any([self.seo_score, self.content_score, self.ads_score])

    def calculate_overall(self) -> float:
        """Calculate overall quality score."""
        scores = [
            s for s in [self.seo_score, self.content_score, self.ads_score] if s is not None
        ]
        if not scores:
            return 0.0
        return sum(scores) / len(scores)


@dataclass
class ProjectProgress:
    """Complete project progress report."""

    project_id: str
    client_name: str
    generated_at: datetime
    tasks: TaskProgress
    budget: BudgetProgress
    timeline: TimelineProgress
    quality: QualityMetrics

    @property
    def overall_health(self) -> str:
        """Overall project health indicator."""
        # Critical if over budget or significantly behind
        if self.budget.is_over_budget or self.timeline.status == TimelineStatus.BEHIND:
            return "critical"

        # Warning if budget critical or at risk
        if (
            self.budget.budget_health == "critical"
            or self.timeline.status == TimelineStatus.AT_RISK
        ):
            return "warning"

        # Healthy if on track
        if self.timeline.is_on_track and self.budget.budget_health == "healthy":
            return "healthy"

        return "attention_needed"

    @property
    def summary(self) -> str:
        """Human-readable summary."""
        return (
            f"{self.client_name}: "
            f"{self.tasks.completion_percent:.0f}% complete, "
            f"{self.budget.utilization_percent:.0f}% budget used, "
            f"{self.timeline.status.value}"
        )


class ProgressTracker:
    """Tracks progress for client projects."""

    def __init__(self):
        self.logger = structlog.get_logger()

    def calculate_task_progress(
        self, total: int, completed: int, in_progress: int
    ) -> TaskProgress:
        """Calculate task completion progress."""
        pending = total - completed - in_progress
        completion_rate = completed / total if total > 0 else 0.0

        return TaskProgress(
            total_tasks=total,
            completed_tasks=completed,
            in_progress_tasks=in_progress,
            pending_tasks=pending,
            completion_rate=completion_rate,
        )

    def calculate_budget_progress(
        self, total_budget: float, spent_budget: float, completion_rate: float
    ) -> BudgetProgress:
        """Calculate budget utilization progress."""
        remaining = total_budget - spent_budget
        utilization_rate = spent_budget / total_budget if total_budget > 0 else 0.0

        # Project final spend based on current burn rate
        projected_total = None
        if completion_rate > 0:
            projected_total = spent_budget / completion_rate

        return BudgetProgress(
            total_budget=total_budget,
            spent_budget=spent_budget,
            remaining_budget=remaining,
            utilization_rate=utilization_rate,
            projected_total=projected_total,
        )

    def calculate_timeline_progress(
        self,
        start_date: datetime,
        end_date: datetime,
        work_progress: float,
        current_date: Optional[datetime] = None,
    ) -> TimelineProgress:
        """Calculate timeline progress."""
        if current_date is None:
            current_date = datetime.now(timezone.utc)

        # Calculate time elapsed
        total_days = (end_date - start_date).days
        elapsed_days = (current_date - start_date).days
        remaining_days = (end_date - current_date).days

        time_progress = elapsed_days / total_days if total_days > 0 else 0.0

        # Determine status based on work vs time progress
        delta = work_progress - time_progress

        if delta >= 0.1:  # 10% ahead
            status = TimelineStatus.AHEAD
        elif delta >= -0.05:  # Within 5%
            status = TimelineStatus.ON_TRACK
        elif delta >= -0.15:  # 5-15% behind
            status = TimelineStatus.AT_RISK
        else:  # More than 15% behind
            status = TimelineStatus.BEHIND

        return TimelineProgress(
            start_date=start_date,
            end_date=end_date,
            current_date=current_date,
            elapsed_days=elapsed_days,
            total_days=total_days,
            remaining_days=remaining_days,
            time_progress=time_progress,
            work_progress=work_progress,
            status=status,
        )

    def calculate_quality_metrics(
        self,
        seo_score: Optional[float] = None,
        content_score: Optional[float] = None,
        ads_score: Optional[float] = None,
    ) -> QualityMetrics:
        """Calculate quality metrics from Magister scores."""
        quality = QualityMetrics(
            seo_score=seo_score,
            content_score=content_score,
            ads_score=ads_score,
        )

        if quality.has_scores:
            quality.overall_score = quality.calculate_overall()

        return quality

    def generate_progress_report(
        self,
        project_id: str,
        client_name: str,
        total_tasks: int,
        completed_tasks: int,
        in_progress_tasks: int,
        total_budget: float,
        spent_budget: float,
        start_date: datetime,
        end_date: datetime,
        seo_score: Optional[float] = None,
        content_score: Optional[float] = None,
        ads_score: Optional[float] = None,
    ) -> ProjectProgress:
        """
        Generate complete progress report.

        Args:
            project_id: Linear project ID
            client_name: Client company name
            total_tasks: Total number of tasks
            completed_tasks: Number of completed tasks
            in_progress_tasks: Number of in-progress tasks
            total_budget: Total project budget
            spent_budget: Budget spent so far
            start_date: Project start date
            end_date: Project end date
            seo_score: SEO quality score (0-100)
            content_score: Content quality score (0-100)
            ads_score: Ads quality score (0-100)

        Returns:
            Complete project progress report
        """
        # Calculate task progress
        tasks = self.calculate_task_progress(
            total=total_tasks,
            completed=completed_tasks,
            in_progress=in_progress_tasks,
        )

        # Calculate budget progress
        budget = self.calculate_budget_progress(
            total_budget=total_budget,
            spent_budget=spent_budget,
            completion_rate=tasks.completion_rate,
        )

        # Calculate timeline progress
        timeline = self.calculate_timeline_progress(
            start_date=start_date,
            end_date=end_date,
            work_progress=tasks.completion_rate,
        )

        # Calculate quality metrics
        quality = self.calculate_quality_metrics(
            seo_score=seo_score,
            content_score=content_score,
            ads_score=ads_score,
        )

        report = ProjectProgress(
            project_id=project_id,
            client_name=client_name,
            generated_at=datetime.now(timezone.utc),
            tasks=tasks,
            budget=budget,
            timeline=timeline,
            quality=quality,
        )

        self.logger.info(
            "progress_report_generated",
            project_id=project_id,
            client_name=client_name,
            overall_health=report.overall_health,
            completion_rate=tasks.completion_rate,
            budget_utilization=budget.utilization_rate,
            timeline_status=timeline.status.value,
        )

        return report

    def format_report(self, report: ProjectProgress) -> str:
        """Format progress report as human-readable text."""
        lines = []

        # Header
        lines.append("=" * 80)
        lines.append(f"Project Progress Report: {report.client_name}")
        lines.append("=" * 80)
        lines.append("")

        # Overall health
        health_emoji = {
            "healthy": "🟢",
            "warning": "🟡",
            "attention_needed": "🟠",
            "critical": "🔴",
        }
        lines.append(
            f"Overall Health: {health_emoji[report.overall_health]} {report.overall_health.upper()}"
        )
        lines.append("")

        # Tasks
        lines.append("📋 Tasks Progress")
        lines.append(f"  Completed: {report.tasks.completed_tasks}/{report.tasks.total_tasks}")
        lines.append(f"  In Progress: {report.tasks.in_progress_tasks}")
        lines.append(f"  Pending: {report.tasks.pending_tasks}")
        lines.append(f"  Completion: {report.tasks.completion_percent:.1f}%")
        lines.append("")

        # Budget
        lines.append("💰 Budget Progress")
        lines.append(f"  Total: {report.budget.total_budget:,.0f} ₽")
        lines.append(f"  Spent: {report.budget.spent_budget:,.0f} ₽")
        lines.append(f"  Remaining: {report.budget.remaining_budget:,.0f} ₽")
        lines.append(f"  Utilization: {report.budget.utilization_percent:.1f}%")
        if report.budget.projected_total:
            lines.append(f"  Projected Total: {report.budget.projected_total:,.0f} ₽")
        lines.append(f"  Health: {report.budget.budget_health}")
        lines.append("")

        # Timeline
        lines.append("📅 Timeline Progress")
        lines.append(f"  Start: {report.timeline.start_date.strftime('%Y-%m-%d')}")
        lines.append(f"  End: {report.timeline.end_date.strftime('%Y-%m-%d')}")
        lines.append(f"  Elapsed: {report.timeline.elapsed_days}/{report.timeline.total_days} days")
        lines.append(f"  Remaining: {report.timeline.remaining_days} days")
        lines.append(f"  Time Progress: {report.timeline.time_percent:.1f}%")
        lines.append(f"  Work Progress: {report.timeline.work_percent:.1f}%")
        lines.append(f"  Status: {report.timeline.status.value}")
        lines.append("")

        # Quality
        if report.quality.has_scores:
            lines.append("⭐ Quality Metrics")
            if report.quality.seo_score is not None:
                lines.append(f"  SEO Score: {report.quality.seo_score:.1f}/100")
            if report.quality.content_score is not None:
                lines.append(f"  Content Score: {report.quality.content_score:.1f}/100")
            if report.quality.ads_score is not None:
                lines.append(f"  Ads Score: {report.quality.ads_score:.1f}/100")
            if report.quality.overall_score is not None:
                lines.append(f"  Overall Score: {report.quality.overall_score:.1f}/100")
            lines.append("")

        # Summary
        lines.append("=" * 80)
        lines.append(f"Summary: {report.summary}")
        lines.append("=" * 80)

        return "\n".join(lines)
