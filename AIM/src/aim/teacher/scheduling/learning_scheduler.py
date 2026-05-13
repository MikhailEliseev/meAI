"""
Learning Scheduler - Create and prioritize learning plans.

Takes system audit report and creates prioritized learning plan
with time/cost estimates and execution strategy.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import structlog

from AIM.src.aim.teacher.scheduling.system_auditor import (
    SystemAuditReport,
    SubagentHealth,
    Priority,
)

logger = structlog.get_logger()


class LearningStrategy(str, Enum):
    """Learning execution strategy."""
    SEQUENTIAL = "sequential"  # One by one (safe, slow)
    PARALLEL = "parallel"      # Multiple in parallel (fast, risky)
    BATCH = "batch"            # Group by category (balanced)


class ResearchDepth(str, Enum):
    """Research depth level."""
    QUICK = "quick"       # 5-10 min, ~$0.50
    STANDARD = "standard" # 10-20 min, ~$1.50
    DEEP = "deep"         # 20-40 min, ~$3.00


@dataclass
class LearningTask:
    """Single learning task for a subagent."""
    subagent_name: str
    priority: Priority
    reason: str
    research_depth: ResearchDepth
    estimated_time_minutes: int
    estimated_cost_usd: float
    dependencies: list[str] = field(default_factory=list)


@dataclass
class LearningPlan:
    """Complete learning plan for system."""
    created_at: datetime
    strategy: LearningStrategy
    total_subagents: int
    total_estimated_time_minutes: int
    total_estimated_cost_usd: float
    tasks: list[LearningTask]
    execution_order: list[list[str]]  # Waves of parallel execution


class LearningScheduler:
    """
    Create learning plans from system audit reports.

    Priority mapping:
    - P1 (CRITICAL): High error rate, system failures → deep research
    - P2 (HIGH): Not taught for >4 weeks → standard research
    - P3 (MEDIUM): Routine updates → standard research
    - P4 (LOW): Optional improvements → quick research

    Strategies:
    - Sequential: Teach one by one (safe, slow)
      - Best for: Critical updates, high-risk changes
      - Risk: Low
      - Time: Longest

    - Parallel: Teach multiple in parallel (fast, risky)
      - Best for: Independent subagents, routine updates
      - Risk: Medium
      - Time: Shortest

    - Batch: Group by category (SEO, Content, Ads)
      - Best for: Related subagents, coordinated updates
      - Risk: Low-Medium
      - Time: Medium
    """

    def __init__(
        self,
        time_per_quick: int = 15,      # minutes
        time_per_standard: int = 30,   # minutes
        time_per_deep: int = 60,       # minutes
        cost_per_quick: float = 0.50,  # USD
        cost_per_standard: float = 1.50,  # USD
        cost_per_deep: float = 3.00,   # USD
    ):
        self.time_per_quick = time_per_quick
        self.time_per_standard = time_per_standard
        self.time_per_deep = time_per_deep
        self.cost_per_quick = cost_per_quick
        self.cost_per_standard = cost_per_standard
        self.cost_per_deep = cost_per_deep

        logger.info(
            "learning_scheduler_initialized",
            time_per_quick=time_per_quick,
            time_per_standard=time_per_standard,
            time_per_deep=time_per_deep,
        )

    async def create_learning_plan(
        self,
        audit_report: SystemAuditReport,
        strategy: LearningStrategy = LearningStrategy.SEQUENTIAL,
    ) -> LearningPlan:
        """
        Create learning plan from audit report.

        Args:
            audit_report: System audit report
            strategy: Execution strategy (sequential/parallel/batch)

        Returns:
            LearningPlan with tasks and execution order
        """
        logger.info(
            "creating_learning_plan",
            total_subagents=audit_report.total_subagents,
            strategy=strategy,
        )

        # 1. Create tasks from priority queue
        tasks = []
        for subagent in audit_report.priority_queue:
            task = self._create_task(subagent)
            tasks.append(task)

        # 2. Calculate totals
        total_time = sum(t.estimated_time_minutes for t in tasks)
        total_cost = sum(t.estimated_cost_usd for t in tasks)

        # 3. Determine execution order based on strategy
        execution_order = self._create_execution_order(tasks, strategy)

        # 4. Create plan
        plan = LearningPlan(
            created_at=datetime.now(),
            strategy=strategy,
            total_subagents=len(tasks),
            total_estimated_time_minutes=total_time,
            total_estimated_cost_usd=total_cost,
            tasks=tasks,
            execution_order=execution_order,
        )

        logger.info(
            "learning_plan_created",
            total_subagents=plan.total_subagents,
            total_time_minutes=plan.total_estimated_time_minutes,
            total_cost_usd=plan.total_estimated_cost_usd,
            strategy=plan.strategy,
        )

        return plan

    def _create_task(self, subagent: SubagentHealth) -> LearningTask:
        """
        Create learning task for subagent.

        Priority → Research depth mapping:
        - P1 (critical) → deep research
        - P2 (high) → standard research
        - P3 (medium) → standard research
        - P4 (low) → quick research
        """
        # Determine research depth based on priority
        if subagent.priority == Priority.P1:
            depth = ResearchDepth.DEEP
            time = self.time_per_deep
            cost = self.cost_per_deep
        elif subagent.priority in [Priority.P2, Priority.P3]:
            depth = ResearchDepth.STANDARD
            time = self.time_per_standard
            cost = self.cost_per_standard
        else:  # P4
            depth = ResearchDepth.QUICK
            time = self.time_per_quick
            cost = self.cost_per_quick

        return LearningTask(
            subagent_name=subagent.name,
            priority=subagent.priority,
            reason=subagent.reason,
            research_depth=depth,
            estimated_time_minutes=time,
            estimated_cost_usd=cost,
        )

    def _create_execution_order(
        self,
        tasks: list[LearningTask],
        strategy: LearningStrategy,
    ) -> list[list[str]]:
        """
        Create execution order based on strategy.

        Returns:
            List of waves, where each wave is a list of subagent names
            that can be executed in parallel.
        """
        if strategy == LearningStrategy.SEQUENTIAL:
            # One task per wave
            return [[task.subagent_name] for task in tasks]

        elif strategy == LearningStrategy.PARALLEL:
            # All tasks in one wave (if independent)
            # For now, simple implementation - all in one wave
            # TODO: Check dependencies
            return [[task.subagent_name for task in tasks]]

        else:  # BATCH
            # Group by category (SEO, Content, Ads, etc.)
            # For now, simple implementation - group by priority
            waves = []
            current_priority = None
            current_wave = []

            for task in tasks:
                if task.priority != current_priority:
                    if current_wave:
                        waves.append(current_wave)
                    current_wave = [task.subagent_name]
                    current_priority = task.priority
                else:
                    current_wave.append(task.subagent_name)

            if current_wave:
                waves.append(current_wave)

            return waves

    def format_plan(self, plan: LearningPlan) -> str:
        """
        Format learning plan as human-readable text.

        Returns:
            Formatted plan string
        """
        output = f"""
╔═══════════════════════════════════════════════════════════╗
║  Learning Plan Created - {plan.created_at.strftime('%Y-%m-%d %H:%M')}                 ║
╚═══════════════════════════════════════════════════════════╝

Strategy: {plan.strategy.value}
Total subagents: {plan.total_subagents}
Estimated time: {self._format_time(plan.total_estimated_time_minutes)}
Estimated cost: ${plan.total_estimated_cost_usd:.2f}

Tasks:
"""

        for i, task in enumerate(plan.tasks, 1):
            priority_emoji = {
                Priority.P1: "🔴",
                Priority.P2: "🟡",
                Priority.P3: "🟢",
                Priority.P4: "⚪",
            }

            output += f"{i}. {priority_emoji[task.priority]} [{task.priority.name}] {task.subagent_name} "
            output += f"({task.research_depth.value}, {task.estimated_time_minutes} min, ${task.estimated_cost_usd:.2f})\n"
            output += f"   Reason: {task.reason}\n"

        output += f"\nExecution order ({len(plan.execution_order)} waves):\n"
        for i, wave in enumerate(plan.execution_order, 1):
            output += f"Wave {i}: {', '.join(wave)}\n"

        return output

    def _format_time(self, minutes: int) -> str:
        """Format time in human-readable format."""
        if minutes < 60:
            return f"{minutes} minutes"
        else:
            hours = minutes // 60
            mins = minutes % 60
            if mins == 0:
                return f"{hours} hour{'s' if hours > 1 else ''}"
            else:
                return f"{hours} hour{'s' if hours > 1 else ''} {mins} minutes"
