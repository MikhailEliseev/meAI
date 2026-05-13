"""
System Auditor - Audit all subagents and handle missing/deprecated.

Discovers all subagents, checks health, classifies by status,
prioritizes for teaching, and handles missing/deprecated subagents.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()


class SubagentStatus(str, Enum):
    """Subagent health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    MISSING = "missing"
    DEPRECATED = "deprecated"


class Priority(int, Enum):
    """Learning priority levels."""
    P1 = 1  # Critical - high error rate, system failures
    P2 = 2  # High - not taught for >4 weeks
    P3 = 3  # Medium - routine updates
    P4 = 4  # Low - optional improvements


@dataclass
class SubagentHealth:
    """Health status of a subagent."""
    name: str
    status: SubagentStatus
    last_taught: datetime | None = None
    performance_metrics: dict[str, float] = field(default_factory=dict)
    needs_update: bool = False
    priority: Priority = Priority.P4
    reason: str = ""
    spec_path: str | None = None
    code_path: str | None = None


@dataclass
class SystemAuditReport:
    """System-wide audit report."""
    timestamp: datetime
    total_subagents: int
    healthy: int
    degraded: int
    missing: int
    deprecated: int
    priority_queue: list[SubagentHealth]
    summary: str


class SystemAuditor:
    """
    Audit all subagents in the system.

    Discovery sources:
    1. Registry files (if exists)
    2. Spec files in docs/subagents-specs/
    3. Obsidian vaults in AIM/obsidian/

    Health checks:
    - Code exists at expected path
    - Last taught date (from Obsidian)
    - Performance metrics (from database)
    - Git history (for missing subagents)

    Status classification:
    - healthy: Working well, taught recently
    - degraded: Working but metrics falling or not taught for >4 weeks
    - missing: Code absent (deleted/renamed)
    - deprecated: Marked as obsolete

    Priority assignment:
    - P1: Critical (high error rate, system failures)
    - P2: High (not taught for >4 weeks)
    - P3: Medium (routine updates)
    - P4: Low (optional improvements)
    """

    def __init__(
        self,
        project_root: Path,
        degraded_threshold_days: int = 28,  # 4 weeks
        critical_subagents: list[str] | None = None,
    ):
        self.project_root = project_root
        self.degraded_threshold_days = degraded_threshold_days
        self.critical_subagents = critical_subagents or [
            "keyword_research",
            "content_gap_analysis",
            "technical_seo",
        ]

        self.specs_dir = project_root / "docs" / "subagents-specs"
        self.code_dir = project_root / "AIM" / "src" / "aim" / "subagents"
        self.obsidian_dir = project_root / "AIM" / "obsidian"

        logger.info(
            "system_auditor_initialized",
            project_root=str(project_root),
            degraded_threshold_days=degraded_threshold_days,
        )

    async def audit_all_subagents(self) -> SystemAuditReport:
        """
        Audit all subagents in the system.

        Returns:
            SystemAuditReport with health status and priority queue
        """
        logger.info("starting_system_audit")

        # 1. Discover all subagents
        subagents = await self._discover_subagents()
        logger.info("subagents_discovered", count=len(subagents))

        # 2. Check health for each
        health_checks = [
            self._check_subagent_health(name, spec_path, code_path)
            for name, spec_path, code_path in subagents
        ]
        health_results = await asyncio.gather(*health_checks)

        # 3. Classify by status
        healthy = [h for h in health_results if h.status == SubagentStatus.HEALTHY]
        degraded = [h for h in health_results if h.status == SubagentStatus.DEGRADED]
        missing = [h for h in health_results if h.status == SubagentStatus.MISSING]
        deprecated = [h for h in health_results if h.status == SubagentStatus.DEPRECATED]

        # 4. Handle missing subagents
        for subagent in missing:
            await self._handle_missing_subagent(subagent)

        # 5. Prioritize for teaching
        priority_queue = self._create_priority_queue(health_results)

        # 6. Create report
        report = SystemAuditReport(
            timestamp=datetime.now(),
            total_subagents=len(health_results),
            healthy=len(healthy),
            degraded=len(degraded),
            missing=len(missing),
            deprecated=len(deprecated),
            priority_queue=priority_queue,
            summary=self._create_summary(health_results),
        )

        logger.info(
            "system_audit_complete",
            total=report.total_subagents,
            healthy=report.healthy,
            degraded=report.degraded,
            missing=report.missing,
            deprecated=report.deprecated,
        )

        return report

    async def _discover_subagents(self) -> list[tuple[str, str, str]]:
        """
        Discover all subagents from specs and code.

        Returns:
            List of (name, spec_path, code_path) tuples
        """
        subagents = {}

        # 1. From spec files
        if self.specs_dir.exists():
            for spec_file in self.specs_dir.glob("*_SPEC.md"):
                name = spec_file.stem.replace("_SPEC", "").lower()
                spec_path = str(spec_file)
                code_path = str(self.code_dir / name / f"{name}.py")
                subagents[name] = (name, spec_path, code_path)

        # 2. From code directories
        if self.code_dir.exists():
            for code_dir in self.code_dir.iterdir():
                if code_dir.is_dir() and not code_dir.name.startswith("_"):
                    name = code_dir.name
                    if name not in subagents:
                        spec_path = str(self.specs_dir / f"{name.upper()}_SPEC.md")
                        code_path = str(code_dir / f"{name}.py")
                        subagents[name] = (name, spec_path, code_path)

        return list(subagents.values())

    async def _check_subagent_health(
        self,
        name: str,
        spec_path: str,
        code_path: str,
    ) -> SubagentHealth:
        """
        Check health of a single subagent.

        Returns:
            SubagentHealth with status and priority
        """
        # Check if code exists
        code_exists = Path(code_path).exists()

        # Check if spec exists
        spec_exists = Path(spec_path).exists()

        # Get last taught date (mock - would read from Obsidian)
        last_taught = await self._get_last_taught_date(name)

        # Get performance metrics (mock - would read from database)
        metrics = await self._get_performance_metrics(name)

        # Determine status
        if not code_exists:
            status = SubagentStatus.MISSING
            reason = "Code not found"
            priority = Priority.P1 if name in self.critical_subagents else Priority.P3
        elif not spec_exists:
            status = SubagentStatus.DEGRADED
            reason = "Spec missing"
            priority = Priority.P2
        elif last_taught and (datetime.now() - last_taught).days > self.degraded_threshold_days:
            status = SubagentStatus.DEGRADED
            reason = f"Not taught for {(datetime.now() - last_taught).days} days"
            priority = Priority.P2
        elif metrics.get("error_rate", 0) > 0.1:  # >10% error rate
            status = SubagentStatus.DEGRADED
            reason = f"High error rate: {metrics['error_rate']:.1%}"
            priority = Priority.P1
        else:
            status = SubagentStatus.HEALTHY
            reason = "Working well"
            priority = Priority.P3

        return SubagentHealth(
            name=name,
            status=status,
            last_taught=last_taught,
            performance_metrics=metrics,
            needs_update=(status != SubagentStatus.HEALTHY),
            priority=priority,
            reason=reason,
            spec_path=spec_path if spec_exists else None,
            code_path=code_path if code_exists else None,
        )

    async def _get_last_taught_date(self, name: str) -> datetime | None:
        """Get last taught date from Obsidian vault."""
        # Mock implementation - would read from Obsidian
        # For now, return random dates for testing
        import random
        days_ago = random.randint(0, 60)
        return datetime.now() - timedelta(days=days_ago)

    async def _get_performance_metrics(self, name: str) -> dict[str, float]:
        """Get performance metrics from database."""
        # Mock implementation - would read from database
        # For now, return random metrics for testing
        import random
        return {
            "error_rate": random.uniform(0, 0.2),
            "success_rate": random.uniform(0.8, 1.0),
            "avg_response_time": random.uniform(0.5, 5.0),
        }

    async def _handle_missing_subagent(self, subagent: SubagentHealth) -> None:
        """
        Handle missing subagent (code deleted/renamed).

        Actions:
        1. Check git history - was it renamed?
        2. If renamed → update registry
        3. If deleted → mark as deprecated
        4. If critical → alert user via Operator
        """
        logger.warning("handling_missing_subagent", name=subagent.name)

        # Check git history
        git_log = await self._check_git_history(subagent.name)

        if git_log.get("renamed_to"):
            # Renamed - update registry
            new_name = git_log["renamed_to"]
            logger.info(
                "subagent_renamed",
                old_name=subagent.name,
                new_name=new_name,
            )
            # TODO: Update registry

        elif git_log.get("deleted"):
            # Deleted - mark deprecated
            logger.info("subagent_deleted", name=subagent.name)

            # If critical - alert
            if subagent.name in self.critical_subagents:
                logger.error(
                    "critical_subagent_missing",
                    name=subagent.name,
                    message=f"🚨 Critical subagent {subagent.name} was deleted!",
                )
                # TODO: Send alert via Event Bus

    async def _check_git_history(self, name: str) -> dict[str, Any]:
        """
        Check git history for subagent.

        Returns:
            Dict with 'renamed_to' or 'deleted' keys
        """
        # Mock implementation - would run git log
        # For now, return empty dict
        return {}

    def _create_priority_queue(
        self,
        health_results: list[SubagentHealth],
    ) -> list[SubagentHealth]:
        """
        Create priority queue for teaching.

        Sort by:
        1. Priority (P1 > P2 > P3 > P4)
        2. Status (degraded > healthy)
        3. Last taught date (oldest first)
        """
        # Filter out missing and deprecated
        teachable = [
            h for h in health_results
            if h.status not in [SubagentStatus.MISSING, SubagentStatus.DEPRECATED]
        ]

        # Sort by priority, then status, then last taught
        sorted_queue = sorted(
            teachable,
            key=lambda h: (
                h.priority.value,
                0 if h.status == SubagentStatus.DEGRADED else 1,
                h.last_taught or datetime.min,
            ),
        )

        return sorted_queue

    def _create_summary(self, health_results: list[SubagentHealth]) -> str:
        """Create human-readable summary."""
        total = len(health_results)
        healthy = sum(1 for h in health_results if h.status == SubagentStatus.HEALTHY)
        degraded = sum(1 for h in health_results if h.status == SubagentStatus.DEGRADED)
        missing = sum(1 for h in health_results if h.status == SubagentStatus.MISSING)
        deprecated = sum(1 for h in health_results if h.status == SubagentStatus.DEPRECATED)

        summary = f"""
╔═══════════════════════════════════════════════════════════╗
║  System Audit Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}                  ║
╚═══════════════════════════════════════════════════════════╝

Total subagents: {total}
✅ Healthy: {healthy}
⚠️  Degraded: {degraded}
❌ Missing: {missing}
🗑️  Deprecated: {deprecated}
"""

        # Add degraded details
        if degraded > 0:
            degraded_list = [h for h in health_results if h.status == SubagentStatus.DEGRADED]
            summary += "\nDegraded subagents:\n"
            for h in degraded_list:
                summary += f"   - {h.name} ({h.reason})\n"

        # Add missing details
        if missing > 0:
            missing_list = [h for h in health_results if h.status == SubagentStatus.MISSING]
            summary += "\nMissing subagents:\n"
            for h in missing_list:
                summary += f"   - {h.name} (code not found)\n"

        return summary
