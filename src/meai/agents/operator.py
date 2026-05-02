"""Operator - Autonomous Operational Director for AIM Agency

The Operator is the tactical layer between strategy (Architect) and execution (Agents).
It receives tasks, makes tactical decisions, delegates to agents, monitors execution,
collects results, and reports back to the user.
"""

import asyncio
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from sqlalchemy import text
from meai.events.event_bus import EventBus, Message
from meai.memory.obsidian import ObsidianVault
from meai.storage.database import Database


class TaskStatus(str, Enum):
    """Task execution status"""

    RECEIVED = "received"
    ANALYZING = "analyzing"
    DELEGATED = "delegated"
    IN_PROGRESS = "in_progress"
    COLLECTING = "collecting"
    COMPLETED = "completed"
    FAILED = "failed"


class ExecutionStrategy(str, Enum):
    """Task execution strategy"""

    DIRECT = "direct"  # Single agent, no coordination
    SEQUENTIAL = "sequential"  # One after another
    PARALLEL = "parallel"  # All at once
    HYBRID = "hybrid"  # Phases with parallel subtasks


@dataclass
class Task:
    """Task received from user or Architect"""

    task_id: str
    source: str  # "user" or "architect"
    goal: str
    description: str
    constraints: list[str]
    resources: dict[str, Any]
    priority: int  # 0-3 (P0 = highest)
    deadline: datetime | None
    status: TaskStatus
    created_at: datetime
    updated_at: datetime


@dataclass
class Subtask:
    """Subtask delegated to an agent"""

    subtask_id: str
    parent_task_id: str
    agent_id: str
    action: str
    description: str
    dependencies: list[str]  # subtask_ids that must complete first
    priority: int
    status: TaskStatus
    result: dict[str, Any] | None
    created_at: datetime
    completed_at: datetime | None


@dataclass
class TacticalPlan:
    """Plan for executing a task"""

    plan_id: str
    task_id: str
    strategy: ExecutionStrategy
    subtasks: list[Subtask]
    agent_assignments: dict[str, list[str]]  # agent_id -> subtask_ids
    estimated_duration: timedelta
    risk_level: str  # "low", "medium", "high"
    created_at: datetime


@dataclass
class Report:
    """Aggregated report for a completed task"""

    report_id: str
    task_id: str
    summary: str
    insights: list[str]
    metrics: dict[str, Any]
    issues: list[str]
    recommendations: list[str]
    created_at: datetime


class Operator:
    """Autonomous Operational Director

    Responsibilities:
    - Receive tasks from user or Architect
    - Make tactical decisions (how to execute)
    - Delegate subtasks to agents
    - Monitor execution
    - Collect results
    - Aggregate reports
    - Report to user
    """

    # Agent timeouts (configurable)
    AGENT_TIMEOUTS = {
        "seo-magister-1": timedelta(minutes=30),
        "content-magister-1": timedelta(minutes=45),
        "ads-magister-1": timedelta(minutes=20),
        "smm-magister-1": timedelta(minutes=25),
        "analytics-magister-1": timedelta(minutes=35),
        "intelligence-magister-1": timedelta(minutes=40),
    }

    # Agent capabilities
    AGENT_CAPABILITIES = {
        "seo-magister-1": ["analyze_keywords", "optimize_content", "analyze_competitors", "track_rankings", "audit_technical_seo"],
        "content-magister-1": ["generate_content", "edit_content", "plan_content", "analyze_performance", "optimize_for_seo"],
        "ads-magister-1": ["create_campaign", "optimize_budget", "analyze_performance", "ab_test", "target_audience"],
        "smm-magister-1": ["create_post", "schedule_posts", "engage_audience", "analyze_metrics", "manage_campaigns"],
        "analytics-magister-1": ["analyze_data", "create_report", "track_metrics", "predict_trends", "optimize_performance"],
        "intelligence-magister-1": ["research_market", "analyze_trends", "monitor_competitors", "identify_opportunities", "strategic_insights"],
    }

    def __init__(self, database_url: str, vault_path: str = "./obsidian"):
        """Initialize Operator

        Args:
            database_url: Database connection URL
            vault_path: Path to Obsidian vault root
        """
        self.db = Database(database_url)
        self.vault = ObsidianVault(vault_path)
        self.event_bus = EventBus(database_url)
        self.agent_id = "operator"

        # Active tasks tracking
        self.active_tasks: dict[str, Task] = {}
        self.active_plans: dict[str, TacticalPlan] = {}

    async def initialize(self) -> None:
        """Initialize Operator components"""
        await self.db.connect()
        await self.vault.initialize()
        await self.event_bus.initialize()

        # Create database tables
        await self._create_tables()

        # Subscribe to agent events
        await self._subscribe_to_events()

    async def shutdown(self) -> None:
        """Shutdown Operator"""
        await self.event_bus.close()
        await self.db.disconnect()

    async def _create_tables(self) -> None:
        """Create Operator database tables"""
        async with self.db.session() as session:
            await session.execute(
                text("""
                CREATE TABLE IF NOT EXISTS operator_tasks (
                    task_id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    goal TEXT NOT NULL,
                    description TEXT,
                    constraints TEXT,
                    resources TEXT,
                    priority INTEGER NOT NULL,
                    deadline TIMESTAMP,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                )
                """)
            )

            await session.execute(
                text("""
                CREATE TABLE IF NOT EXISTS operator_plans (
                    plan_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    subtasks TEXT NOT NULL,
                    agent_assignments TEXT,
                    estimated_duration INTEGER,
                    risk_level TEXT,
                    created_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (task_id) REFERENCES operator_tasks(task_id)
                )
                """)
            )

            await session.execute(
                text("""
                CREATE TABLE IF NOT EXISTS operator_subtasks (
                    subtask_id TEXT PRIMARY KEY,
                    parent_task_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    description TEXT,
                    dependencies TEXT,
                    priority INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    result TEXT,
                    created_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (parent_task_id) REFERENCES operator_tasks(task_id)
                )
                """)
            )

            await session.execute(
                text("""
                CREATE TABLE IF NOT EXISTS operator_reports (
                    report_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    insights TEXT,
                    metrics TEXT,
                    issues TEXT,
                    recommendations TEXT,
                    created_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (task_id) REFERENCES operator_tasks(task_id)
                )
                """)
            )

            await session.commit()

    async def _subscribe_to_events(self) -> None:
        """Subscribe to agent result events"""
        # Operator uses message polling pattern, not event subscription
        # Results are collected via poll_and_collect_results() method
        pass

    async def receive_task(self, task: Task) -> None:
        """Receive task from user or Architect

        Args:
            task: Task to execute

        Steps:
        1. Validate task structure
        2. Store in database
        3. Write to vault
        4. Publish event
        5. Trigger tactical decision making
        """
        # Update status
        task.status = TaskStatus.RECEIVED
        task.updated_at = datetime.now(timezone.utc)

        # Store in database
        async with self.db.session() as session:
            await session.execute(
                text("""
                INSERT INTO operator_tasks
                (task_id, source, goal, description, constraints, resources,
                 priority, deadline, status, created_at, updated_at)
                VALUES (:task_id, :source, :goal, :description, :constraints, :resources,
                        :priority, :deadline, :status, :created_at, :updated_at)
                """),
                {
                    "task_id": task.task_id,
                    "source": task.source,
                    "goal": task.goal,
                    "description": task.description,
                    "constraints": json.dumps(task.constraints),
                    "resources": json.dumps(task.resources),
                    "priority": task.priority,
                    "deadline": task.deadline,
                    "status": task.status.value,
                    "created_at": task.created_at,
                    "updated_at": task.updated_at,
                },
            )
            await session.commit()

        # Write to vault
        await self._write_task_to_vault(task)

        # Track active task
        self.active_tasks[task.task_id] = task

        # Publish event
        await self.event_bus.publish(
            Message(
                from_agent=self.agent_id,
                to_agent=self.agent_id,
                message_type="task.received",
                priority=task.priority,
                payload={"task_id": task.task_id, "source": task.source, "goal": task.goal},
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        )

        # Make tactical decision
        await self.make_tactical_decision(task)

    async def make_tactical_decision(self, task: Task) -> TacticalPlan:
        """Make tactical decision on how to execute task

        Args:
            task: Task to plan

        Returns:
            Tactical plan with subtasks and agent assignments

        Steps:
        1. Analyze task complexity
        2. Identify required capabilities
        3. Choose execution strategy
        4. Break into subtasks
        5. Assign agents to subtasks
        6. Estimate duration and risks
        7. Store plan in database
        8. Write to vault
        9. Execute plan
        """
        # Update status
        task.status = TaskStatus.ANALYZING
        await self._update_task_status(task)

        # Analyze task and identify required capabilities
        required_capabilities = self._identify_required_capabilities(task)

        # Choose execution strategy
        strategy = self._choose_strategy(task, required_capabilities)

        # Break into subtasks
        subtasks = self._create_subtasks(task, required_capabilities, strategy)

        # Assign agents
        agent_assignments = self._assign_agents(subtasks)

        # Estimate duration
        estimated_duration = self._estimate_duration(subtasks, strategy)

        # Assess risk
        risk_level = self._assess_risk(task, subtasks)

        # Create plan
        plan = TacticalPlan(
            plan_id=f"plan-{uuid4().hex[:8]}",
            task_id=task.task_id,
            strategy=strategy,
            subtasks=subtasks,
            agent_assignments=agent_assignments,
            estimated_duration=estimated_duration,
            risk_level=risk_level,
            created_at=datetime.now(timezone.utc),
        )

        # Store in database
        await self._store_plan(plan)

        # Write to vault
        await self._write_plan_to_vault(plan)

        # Track active plan
        self.active_plans[task.task_id] = plan

        # Execute plan
        await self._execute_plan(plan)

        return plan

    def _identify_required_capabilities(self, task: Task) -> list[str]:
        """Identify required agent capabilities from task

        Args:
            task: Task to analyze

        Returns:
            List of required capability names
        """
        capabilities = []

        # Simple keyword matching (can be enhanced with LLM)
        goal_lower = task.goal.lower()
        desc_lower = task.description.lower()

        # SEO capabilities
        if any(kw in goal_lower or kw in desc_lower for kw in ["seo", "keyword", "ranking", "competitor", "search"]):
            capabilities.extend(["analyze_keywords", "optimize_content", "analyze_competitors"])

        # Content capabilities
        if any(kw in goal_lower or kw in desc_lower for kw in ["content", "article", "blog", "write", "post"]):
            capabilities.extend(["generate_content", "edit_content", "optimize_for_seo"])

        # Ads capabilities
        if any(kw in goal_lower or kw in desc_lower for kw in ["ads", "campaign", "advertising", "ppc", "budget"]):
            capabilities.extend(["create_campaign", "optimize_budget", "ab_test"])

        # SMM capabilities
        if any(kw in goal_lower or kw in desc_lower for kw in ["social", "smm", "facebook", "instagram", "linkedin"]):
            capabilities.extend(["create_post", "schedule_posts", "engage_audience"])

        # Analytics capabilities
        if any(kw in goal_lower or kw in desc_lower for kw in ["analytics", "data", "metrics", "report", "analyze"]):
            capabilities.extend(["analyze_data", "create_report", "track_metrics"])

        # Intelligence capabilities
        if any(kw in goal_lower or kw in desc_lower for kw in ["market", "research", "intelligence", "trends", "insights"]):
            capabilities.extend(["research_market", "analyze_trends", "monitor_competitors"])

        return list(set(capabilities))  # Remove duplicates

    def _choose_strategy(self, task: Task, required_capabilities: list[str]) -> ExecutionStrategy:
        """Choose execution strategy based on task and capabilities

        Args:
            task: Task to execute
            required_capabilities: Required capabilities

        Returns:
            Execution strategy
        """
        num_capabilities = len(required_capabilities)

        # Simple task -> direct
        if num_capabilities == 1:
            return ExecutionStrategy.DIRECT

        # Check for dependencies
        has_dependencies = self._has_dependencies(required_capabilities)

        # High priority -> parallel if possible
        if task.priority <= 1 and not has_dependencies:
            return ExecutionStrategy.PARALLEL

        # Dependencies -> sequential or hybrid
        if has_dependencies:
            if num_capabilities > 3:
                return ExecutionStrategy.HYBRID
            return ExecutionStrategy.SEQUENTIAL

        # Default -> parallel
        return ExecutionStrategy.PARALLEL

    def _has_dependencies(self, capabilities: list[str]) -> bool:
        """Check if capabilities have dependencies

        Args:
            capabilities: List of capabilities

        Returns:
            True if there are dependencies
        """
        # Define capability dependencies
        dependencies = {
            "optimize_content": ["analyze_keywords"],  # Need keywords before optimizing
            "optimize_for_seo": ["generate_content"],  # Need content before SEO optimization
            "ab_test": ["create_campaign"],  # Need campaign before testing
            "analyze_performance": ["create_campaign", "generate_content"],  # Need content/campaign before analysis
        }

        for cap in capabilities:
            if cap in dependencies:
                for dep in dependencies[cap]:
                    if dep in capabilities:
                        return True

        return False

    def _create_subtasks(
        self, task: Task, required_capabilities: list[str], strategy: ExecutionStrategy
    ) -> list[Subtask]:
        """Create subtasks from required capabilities

        Args:
            task: Parent task
            required_capabilities: Required capabilities
            strategy: Execution strategy

        Returns:
            List of subtasks
        """
        subtasks = []
        now = datetime.now(timezone.utc)

        # Map capabilities to agents
        capability_to_agent = {}
        for agent_id, caps in self.AGENT_CAPABILITIES.items():
            for cap in caps:
                capability_to_agent[cap] = agent_id

        # Create subtasks
        for i, capability in enumerate(required_capabilities):
            agent_id = capability_to_agent.get(capability, "seo-magister-1")  # Default to SEO Magister

            # Determine dependencies based on strategy
            dependencies = []
            if strategy == ExecutionStrategy.SEQUENTIAL and i > 0:
                dependencies.append(subtasks[i - 1].subtask_id)
            elif strategy == ExecutionStrategy.HYBRID:
                # Group into phases (simplified)
                if capability in ["optimize_content", "optimize_for_seo", "ab_test", "analyze_performance"]:
                    # These depend on earlier tasks
                    for st in subtasks:
                        if st.action in ["analyze_keywords", "generate_content", "create_campaign"]:
                            dependencies.append(st.subtask_id)

            subtask = Subtask(
                subtask_id=f"subtask-{uuid4().hex[:8]}",
                parent_task_id=task.task_id,
                agent_id=agent_id,
                action=capability,
                description=f"{capability.replace('_', ' ').title()} for: {task.goal}",
                dependencies=dependencies,
                priority=task.priority,
                status=TaskStatus.RECEIVED,
                result=None,
                created_at=now,
                completed_at=None,
            )

            subtasks.append(subtask)

        return subtasks

    def _assign_agents(self, subtasks: list[Subtask]) -> dict[str, list[str]]:
        """Create agent assignment map

        Args:
            subtasks: List of subtasks

        Returns:
            Map of agent_id -> list of subtask_ids
        """
        assignments: dict[str, list[str]] = {}

        for subtask in subtasks:
            if subtask.agent_id not in assignments:
                assignments[subtask.agent_id] = []
            assignments[subtask.agent_id].append(subtask.subtask_id)

        return assignments

    def _estimate_duration(self, subtasks: list[Subtask], strategy: ExecutionStrategy) -> timedelta:
        """Estimate task duration

        Args:
            subtasks: List of subtasks
            strategy: Execution strategy

        Returns:
            Estimated duration
        """
        # Simple estimation: sum of agent timeouts
        total = timedelta()

        if strategy == ExecutionStrategy.PARALLEL:
            # Max of all subtask durations
            max_duration = timedelta()
            for subtask in subtasks:
                agent_timeout = self.AGENT_TIMEOUTS.get(subtask.agent_id, timedelta(minutes=30))
                if agent_timeout > max_duration:
                    max_duration = agent_timeout
            total = max_duration
        else:
            # Sum of all subtask durations
            for subtask in subtasks:
                agent_timeout = self.AGENT_TIMEOUTS.get(subtask.agent_id, timedelta(minutes=30))
                total += agent_timeout

        return total

    def _assess_risk(self, task: Task, subtasks: list[Subtask]) -> str:
        """Assess task risk level

        Args:
            task: Task
            subtasks: List of subtasks

        Returns:
            Risk level: "low", "medium", "high"
        """
        # Simple risk assessment
        risk_score = 0

        # High priority = higher risk
        if task.priority == 0:
            risk_score += 2

        # Many subtasks = higher risk
        if len(subtasks) > 5:
            risk_score += 2
        elif len(subtasks) > 3:
            risk_score += 1

        # Tight deadline = higher risk
        if task.deadline:
            time_until_deadline = task.deadline - datetime.now(timezone.utc)
            if time_until_deadline < timedelta(hours=24):
                risk_score += 2
            elif time_until_deadline < timedelta(days=3):
                risk_score += 1

        # Map score to level
        if risk_score >= 4:
            return "high"
        elif risk_score >= 2:
            return "medium"
        return "low"

    async def _execute_plan(self, plan: TacticalPlan) -> None:
        """Execute tactical plan

        Args:
            plan: Plan to execute
        """
        task = self.active_tasks[plan.task_id]
        task.status = TaskStatus.DELEGATED
        await self._update_task_status(task)

        # Delegate based on strategy
        if plan.strategy == ExecutionStrategy.DIRECT:
            await self._execute_direct(plan)
        elif plan.strategy == ExecutionStrategy.SEQUENTIAL:
            await self._execute_sequential(plan)
        elif plan.strategy == ExecutionStrategy.PARALLEL:
            await self._execute_parallel(plan)
        elif plan.strategy == ExecutionStrategy.HYBRID:
            await self._execute_hybrid(plan)

    async def _execute_direct(self, plan: TacticalPlan) -> None:
        """Execute plan with single agent

        Args:
            plan: Plan to execute
        """
        subtask = plan.subtasks[0]
        await self.delegate_to_agent(subtask)

    async def _execute_sequential(self, plan: TacticalPlan) -> None:
        """Execute plan sequentially

        Args:
            plan: Plan to execute
        """
        for subtask in plan.subtasks:
            await self.delegate_to_agent(subtask)
            # In real implementation, would wait for completion before next

    async def _execute_parallel(self, plan: TacticalPlan) -> None:
        """Execute plan in parallel

        Args:
            plan: Plan to execute
        """
        # Delegate all subtasks at once
        for subtask in plan.subtasks:
            await self.delegate_to_agent(subtask)

    async def _execute_hybrid(self, plan: TacticalPlan) -> None:
        """Execute plan in hybrid mode (phases with parallel subtasks)

        Args:
            plan: Plan to execute
        """
        # Group subtasks by dependencies
        phases: list[list[Subtask]] = []
        remaining = plan.subtasks.copy()

        while remaining:
            # Find subtasks with no dependencies or all dependencies completed
            phase = []
            for subtask in remaining:
                if not subtask.dependencies:
                    phase.append(subtask)

            if not phase:
                # All remaining have dependencies - take first batch
                phase = remaining[:3]  # Arbitrary batch size

            phases.append(phase)
            for subtask in phase:
                remaining.remove(subtask)

        # Execute phases
        for phase in phases:
            for subtask in phase:
                await self.delegate_to_agent(subtask)
            # In real implementation, would wait for phase completion

    async def delegate_to_agent(self, subtask: Subtask) -> None:
        """Delegate subtask to agent

        Args:
            subtask: Subtask to delegate

        Steps:
        1. Create Message with subtask details
        2. Set priority
        3. Publish to Event Bus
        4. Update subtask status
        5. Write to vault
        """
        # Update status
        subtask.status = TaskStatus.DELEGATED

        # Store subtask in database
        await self._store_subtask(subtask)

        # Create message
        message = Message(
            from_agent=self.agent_id,
            to_agent=subtask.agent_id,
            message_type="task_assignment",
            priority=subtask.priority,
            payload={
                "subtask_id": subtask.subtask_id,
                "parent_task_id": subtask.parent_task_id,
                "action": subtask.action,
                "description": subtask.description,
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # Publish to Event Bus
        await self.event_bus.publish(message)

        # Write to vault
        await self._write_delegation_to_vault(subtask)

    async def _store_plan(self, plan: TacticalPlan) -> None:
        """Store plan in database"""
        async with self.db.session() as session:
            await session.execute(
                text("""
                INSERT INTO operator_plans
                (plan_id, task_id, strategy, subtasks, agent_assignments,
                 estimated_duration, risk_level, created_at)
                VALUES (:plan_id, :task_id, :strategy, :subtasks, :agent_assignments,
                        :estimated_duration, :risk_level, :created_at)
                """),
                {
                    "plan_id": plan.plan_id,
                    "task_id": plan.task_id,
                    "strategy": plan.strategy.value,
                    "subtasks": json.dumps([asdict(st) for st in plan.subtasks], default=str),
                    "agent_assignments": json.dumps(plan.agent_assignments),
                    "estimated_duration": int(plan.estimated_duration.total_seconds()),
                    "risk_level": plan.risk_level,
                    "created_at": plan.created_at,
                },
            )
            await session.commit()

    async def _store_subtask(self, subtask: Subtask) -> None:
        """Store subtask in database"""
        async with self.db.session() as session:
            await session.execute(
                text("""
                INSERT OR REPLACE INTO operator_subtasks
                (subtask_id, parent_task_id, agent_id, action, description,
                 dependencies, priority, status, result, created_at, completed_at)
                VALUES (:subtask_id, :parent_task_id, :agent_id, :action, :description,
                        :dependencies, :priority, :status, :result, :created_at, :completed_at)
                """),
                {
                    "subtask_id": subtask.subtask_id,
                    "parent_task_id": subtask.parent_task_id,
                    "agent_id": subtask.agent_id,
                    "action": subtask.action,
                    "description": subtask.description,
                    "dependencies": json.dumps(subtask.dependencies),
                    "priority": subtask.priority,
                    "status": subtask.status.value,
                    "result": json.dumps(subtask.result) if subtask.result else None,
                    "created_at": subtask.created_at,
                    "completed_at": subtask.completed_at,
                },
            )
            await session.commit()

    async def _update_task_status(self, task: Task) -> None:
        """Update task status in database"""
        task.updated_at = datetime.now(timezone.utc)

        async with self.db.session() as session:
            await session.execute(
                text("""
                UPDATE operator_tasks
                SET status = :status, updated_at = :updated_at
                WHERE task_id = :task_id
                """),
                {
                    "status": task.status.value,
                    "updated_at": task.updated_at,
                    "task_id": task.task_id,
                },
            )
            await session.commit()

    async def _write_task_to_vault(self, task: Task) -> None:
        """Write task to vault"""
        content = f"""---
task_id: {task.task_id}
source: {task.source}
priority: P{task.priority}
status: {task.status.value}
created: {task.created_at.isoformat()}
updated: {task.updated_at.isoformat()}
---

# Task: {task.goal}

## Description
{task.description}

## Constraints
{chr(10).join(f"- {c}" for c in task.constraints)}

## Resources
```json
{json.dumps(task.resources, indent=2)}
```

## Deadline
{task.deadline.isoformat() if task.deadline else "None"}
"""

        await self.vault.write_file(f"operator/tasks/{task.task_id}.md", content)

    async def _write_plan_to_vault(self, plan: TacticalPlan) -> None:
        """Write plan to vault"""
        content = f"""---
plan_id: {plan.plan_id}
task_id: {plan.task_id}
strategy: {plan.strategy.value}
risk_level: {plan.risk_level}
estimated_duration: {plan.estimated_duration}
created: {plan.created_at.isoformat()}
---

# Tactical Plan: {plan.task_id}

## Strategy
{plan.strategy.value.upper()}

## Risk Level
{plan.risk_level.upper()}

## Estimated Duration
{plan.estimated_duration}

## Subtasks

{chr(10).join(f"### {i+1}. {st.action} ({st.agent_id}){chr(10)}- **ID:** {st.subtask_id}{chr(10)}- **Description:** {st.description}{chr(10)}- **Dependencies:** {', '.join(st.dependencies) if st.dependencies else 'None'}{chr(10)}- **Status:** {st.status.value}{chr(10)}" for i, st in enumerate(plan.subtasks))}

## Agent Assignments

{chr(10).join(f"- **{agent_id}:** {len(subtask_ids)} subtasks" for agent_id, subtask_ids in plan.agent_assignments.items())}
"""

        await self.vault.write_file(f"operator/plans/{plan.plan_id}.md", content)

    async def _write_delegation_to_vault(self, subtask: Subtask) -> None:
        """Write delegation to vault"""
        content = f"""---
subtask_id: {subtask.subtask_id}
parent_task_id: {subtask.parent_task_id}
agent_id: {subtask.agent_id}
action: {subtask.action}
status: {subtask.status.value}
created: {subtask.created_at.isoformat()}
---

# Delegation: {subtask.action}

## Agent
{subtask.agent_id}

## Action
{subtask.action}

## Description
{subtask.description}

## Dependencies
{chr(10).join(f"- {dep}" for dep in subtask.dependencies) if subtask.dependencies else "None"}

## Priority
P{subtask.priority}

## Status
{subtask.status.value}
"""

        await self.vault.write_file(f"operator/delegations/{subtask.subtask_id}.md", content)

    async def poll_and_collect_results(self) -> None:
        """Poll for task results from agents and process them

        This method should be called periodically to check for completed tasks.
        """
        # Get pending messages for Operator
        messages = await self.event_bus.get_messages(
            agent_id=self.agent_id,
            status="pending",
            limit=50,
        )

        for message in messages:
            if message.message_type == "task_result":
                try:
                    await self._handle_task_result(message)
                    await self.event_bus.mark_processed(message.message_id)
                except Exception as e:
                    await self.event_bus.mark_failed(
                        message.message_id,
                        str(e),
                    )

    async def _handle_task_result(self, message: Message) -> None:
        """Handle task result from agent

        Args:
            message: Message from agent with task result
        """
        payload = message.payload

        # Update subtask in database
        await self._update_subtask_result(
            subtask_id=payload["subtask_id"],
            status=payload["status"],
            result=payload["result"],
            completed_at=payload.get("completed_at"),
        )

        # Check if all subtasks completed
        parent_task_id = payload["parent_task_id"]
        if await self._all_subtasks_completed(parent_task_id):
            await self._finalize_task(parent_task_id)

    async def _update_subtask_result(
        self,
        subtask_id: str,
        status: str,
        result: dict[str, Any],
        completed_at: str | None = None,
    ) -> None:
        """Update subtask with result

        Args:
            subtask_id: Subtask ID
            status: Task status
            result: Task result
            completed_at: Completion timestamp
        """
        async with self.db.session() as session:
            await session.execute(
                text("""
                UPDATE operator_subtasks
                SET status = :status,
                    result = :result,
                    completed_at = :completed_at
                WHERE subtask_id = :subtask_id
                """),
                {
                    "status": status,
                    "result": json.dumps(result),
                    "completed_at": completed_at,
                    "subtask_id": subtask_id,
                },
            )
            await session.commit()

    async def _all_subtasks_completed(self, task_id: str) -> bool:
        """Check if all subtasks for a task are completed

        Args:
            task_id: Parent task ID

        Returns:
            True if all subtasks completed
        """
        async with self.db.session() as session:
            result = await session.execute(
                text("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
                FROM operator_subtasks
                WHERE parent_task_id = :task_id
                """),
                {"task_id": task_id},
            )
            row = result.fetchone()

        if row is None:
            return False

        total, completed = row[0], row[1]
        return total > 0 and total == completed

    async def _finalize_task(self, task_id: str) -> None:
        """Finalize task after all subtasks completed

        Args:
            task_id: Task ID

        Steps:
        1. Collect all subtask results
        2. Aggregate into report
        3. Store in database
        4. Write to vault
        5. Update task status
        """
        # Collect results
        results = await self._collect_subtask_results(task_id)

        # Aggregate report
        report = await self._aggregate_report(task_id, results)

        # Store report
        await self._store_report(report)

        # Write to vault
        await self._write_report_to_vault(report)

        # Update task status
        task = self.active_tasks.get(task_id)
        if task:
            task.status = TaskStatus.COMPLETED
            await self._update_task_status(task)

    async def _collect_subtask_results(self, task_id: str) -> list[dict[str, Any]]:
        """Collect all subtask results for a task

        Args:
            task_id: Parent task ID

        Returns:
            List of subtask results
        """
        async with self.db.session() as session:
            result = await session.execute(
                text("""
                SELECT subtask_id, agent_id, action, description, result, completed_at
                FROM operator_subtasks
                WHERE parent_task_id = :task_id
                ORDER BY completed_at ASC
                """),
                {"task_id": task_id},
            )
            rows = result.fetchall()

        results = []
        for row in rows:
            results.append({
                "subtask_id": row[0],
                "agent_id": row[1],
                "action": row[2],
                "description": row[3],
                "result": json.loads(row[4]) if row[4] else {},
                "completed_at": row[5],
            })

        return results

    async def _aggregate_report(
        self,
        task_id: str,
        results: list[dict[str, Any]],
    ) -> Report:
        """Aggregate subtask results into a report

        Args:
            task_id: Task ID
            results: List of subtask results

        Returns:
            Aggregated report
        """
        task = self.active_tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        # Generate summary
        summary = f"Completed {len(results)} subtasks for: {task.goal}"

        # Extract insights
        insights = []
        for result in results:
            if "insights" in result["result"]:
                insights.extend(result["result"]["insights"])

        # Collect metrics
        metrics = {
            "total_subtasks": len(results),
            "agents_involved": len(set(r["agent_id"] for r in results)),
            "completion_time": self._calculate_completion_time(results),
        }

        # Identify issues
        issues = []
        for result in results:
            if "errors" in result["result"]:
                issues.extend(result["result"]["errors"])

        # Generate recommendations
        recommendations = [
            f"Review {result['action']} results from {result['agent_id']}"
            for result in results
        ]

        return Report(
            report_id=f"report-{uuid4().hex[:8]}",
            task_id=task_id,
            summary=summary,
            insights=insights,
            metrics=metrics,
            issues=issues,
            recommendations=recommendations,
            created_at=datetime.now(timezone.utc),
        )

    def _calculate_completion_time(self, results: list[dict[str, Any]]) -> str:
        """Calculate total completion time

        Args:
            results: List of subtask results

        Returns:
            Completion time as string
        """
        if not results:
            return "0s"

        # Find earliest and latest completion times
        completed_times = [
            datetime.fromisoformat(r["completed_at"])
            for r in results
            if r.get("completed_at")
        ]

        if not completed_times:
            return "0s"

        duration = max(completed_times) - min(completed_times)
        return str(duration)

    async def _store_report(self, report: Report) -> None:
        """Store report in database

        Args:
            report: Report to store
        """
        async with self.db.session() as session:
            await session.execute(
                text("""
                INSERT INTO operator_reports
                (report_id, task_id, summary, insights, metrics, issues, recommendations, created_at)
                VALUES (:report_id, :task_id, :summary, :insights, :metrics, :issues, :recommendations, :created_at)
                """),
                {
                    "report_id": report.report_id,
                    "task_id": report.task_id,
                    "summary": report.summary,
                    "insights": json.dumps(report.insights),
                    "metrics": json.dumps(report.metrics),
                    "issues": json.dumps(report.issues),
                    "recommendations": json.dumps(report.recommendations),
                    "created_at": report.created_at,
                },
            )
            await session.commit()

    async def _write_report_to_vault(self, report: Report) -> None:
        """Write report to vault

        Args:
            report: Report to write
        """
        content = f"""---
report_id: {report.report_id}
task_id: {report.task_id}
created: {report.created_at.isoformat()}
---

# Task Report: {report.task_id}

## Summary
{report.summary}

## Insights
{chr(10).join(f"- {insight}" for insight in report.insights) if report.insights else "None"}

## Metrics
```json
{json.dumps(report.metrics, indent=2)}
```

## Issues
{chr(10).join(f"- {issue}" for issue in report.issues) if report.issues else "None"}

## Recommendations
{chr(10).join(f"- {rec}" for rec in report.recommendations)}
"""

        await self.vault.write_file(f"operator/reports/{report.report_id}.md", content)
