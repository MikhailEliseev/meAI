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


class MagisterCoordinator:
    """Coordinates delegation to Magisters through Event Bus

    This is the bridge between Operator and the learning system (Magisters → Subagents).
    Instead of delegating directly to low-level agents, Operator delegates to Magisters,
    who then coordinate their Subagents.
    """

    def __init__(self, event_bus: EventBus, operator_id: str):
        """Initialize MagisterCoordinator

        Args:
            event_bus: Event Bus for messaging
            operator_id: Operator's agent ID
        """
        self.event_bus = event_bus
        self.operator_id = operator_id

        # Map capabilities to Magisters
        self.capability_to_magister = {
            # SEO Magister capabilities
            "analyze_keywords": "seo-magister-1",
            "optimize_content": "seo-magister-1",
            "analyze_competitors": "seo-magister-1",
            "track_rankings": "seo-magister-1",
            "audit_technical_seo": "seo-magister-1",

            # Content Magister capabilities
            "generate_content": "content-magister-1",
            "edit_content": "content-magister-1",
            "plan_content": "content-magister-1",
            "analyze_performance": "content-magister-1",
            "optimize_for_seo": "content-magister-1",

            # Ads Magister capabilities
            "create_campaign": "ads-magister-1",
            "optimize_budget": "ads-magister-1",
            "ab_test": "ads-magister-1",
            "target_audience": "ads-magister-1",

            # SMM Magister capabilities
            "create_post": "smm-magister-1",
            "schedule_posts": "smm-magister-1",
            "engage_audience": "smm-magister-1",
            "analyze_metrics": "smm-magister-1",
            "manage_campaigns": "smm-magister-1",

            # Analytics Magister capabilities
            "analyze_data": "analytics-magister-1",
            "create_report": "analytics-magister-1",
            "track_metrics": "analytics-magister-1",
            "predict_trends": "analytics-magister-1",

            # Intelligence Magister capabilities
            "research_market": "intelligence-magister-1",
            "analyze_trends": "intelligence-magister-1",
            "monitor_competitors": "intelligence-magister-1",
            "identify_opportunities": "intelligence-magister-1",
            "strategic_insights": "intelligence-magister-1",
        }

    async def delegate_to_magister(self, subtask: Subtask) -> None:
        """Delegate subtask to appropriate Magister

        Args:
            subtask: Subtask to delegate

        Steps:
        1. Identify Magister from capability
        2. Create magister_task message
        3. Publish to Event Bus with high priority
        4. Magister will receive and delegate to Subagents
        """
        # Get Magister for this capability
        magister_id = self.capability_to_magister.get(
            subtask.action,
            "seo-magister-1"  # Default fallback
        )

        # Create message for Magister
        message = Message(
            from_agent=self.operator_id,
            to_agent=magister_id,
            message_type="magister_task",
            priority=subtask.priority,
            payload={
                "subtask_id": subtask.subtask_id,
                "parent_task_id": subtask.parent_task_id,
                "operator_task_id": subtask.parent_task_id,  # For result tracking
                "action": subtask.action,
                "description": subtask.description,
                "dependencies": subtask.dependencies,
                "deadline": None,  # Can add deadline logic later
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # Publish to Event Bus
        await self.event_bus.publish(message)

    def get_magister_for_capability(self, capability: str) -> str:
        """Get Magister ID for a capability

        Args:
            capability: Capability name

        Returns:
            Magister agent ID
        """
        return self.capability_to_magister.get(capability, "seo-magister-1")


class Operator:
    """Autonomous Operational Director

    Responsibilities:
    - Receive tasks from user or Architect
    - Make tactical decisions (how to execute)
    - Delegate subtasks to Magisters (not directly to agents)
    - Monitor execution
    - Collect results from Magisters
    - Aggregate reports
    - Report to user
    """

    # Agent timeouts (configurable) - now for Magisters
    AGENT_TIMEOUTS = {
        "seo-magister-1": timedelta(minutes=30),
        "content-magister-1": timedelta(minutes=45),
        "ads-magister-1": timedelta(minutes=20),
        "smm-magister-1": timedelta(minutes=25),
        "analytics-magister-1": timedelta(minutes=35),
        "intelligence-magister-1": timedelta(minutes=40),
    }

    # Retry settings
    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 5

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

        # Magister Coordinator (bridge to learning system)
        self.magister_coordinator = MagisterCoordinator(self.event_bus, self.agent_id)

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
        action_lower = task.action.lower()
        desc_lower = task.description.lower()

        # SEO capabilities
        if any(kw in action_lower or kw in desc_lower for kw in ["seo", "keyword", "ranking", "competitor", "search"]):
            capabilities.extend(["analyze_keywords", "optimize_content", "analyze_competitors"])

        # Content capabilities
        if any(kw in action_lower or kw in desc_lower for kw in ["content", "article", "blog", "write", "post"]):
            capabilities.extend(["generate_content", "edit_content", "optimize_for_seo"])

        # Ads capabilities
        if any(kw in action_lower or kw in desc_lower for kw in ["ads", "campaign", "advertising", "ppc", "budget"]):
            capabilities.extend(["create_campaign", "optimize_budget", "ab_test"])

        # SMM capabilities
        if any(kw in action_lower or kw in desc_lower for kw in ["social", "smm", "facebook", "instagram", "linkedin"]):
            capabilities.extend(["create_post", "schedule_posts", "engage_audience"])

        # Analytics capabilities
        if any(kw in action_lower or kw in desc_lower for kw in ["analytics", "data", "metrics", "report", "analyze"]):
            capabilities.extend(["analyze_data", "create_report", "track_metrics"])

        # Intelligence capabilities (enhanced CI detection)
        ci_keywords = [
            "competitor", "конкурент",
            "competitive intelligence", "конкурентная разведка",
            "market analysis", "анализ рынка",
            "benchmark", "бенчмарк",
            "competitor analysis", "анализ конкурентов",
            "market research", "исследование рынка"
        ]

        if any(kw in action_lower or kw in desc_lower for kw in ci_keywords):
            capabilities.append("monitor_competitors")

        # SEO capabilities
        seo_keywords = [
            "seo", "keyword", "keywords", "ключевые слова", "ключевое слово",
            "optimize", "оптимизация", "оптимизировать",
            "ranking", "позиции", "ранжирование",
            "content optimization", "оптимизация контента",
            "technical seo", "технический seo",
            "search engine", "поисковая оптимизация"
        ]

        if any(kw in action_lower or kw in desc_lower for kw in seo_keywords):
            capabilities.append("analyze_keywords")

        # Content capabilities
        content_keywords = [
            "content", "контент",
            "article", "статья",
            "write", "написать", "писать",
            "generate", "генерировать", "создать",
            "blog", "блог",
            "copywriting", "копирайтинг"
        ]

        if any(kw in action_lower or kw in desc_lower for kw in content_keywords):
            capabilities.append("generate_content")

        # General intelligence capabilities
        if any(kw in action_lower or kw in desc_lower for kw in ["market", "research", "intelligence", "trends", "insights"]):
            capabilities.extend(["research_market", "analyze_trends", "identify_opportunities"])

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
        """Delegate subtask to Magister (not directly to agent)

        Args:
            subtask: Subtask to delegate

        Steps:
        1. Update subtask status
        2. Store in database
        3. Delegate to Magister via MagisterCoordinator
        4. Write to vault
        """
        # Update status
        subtask.status = TaskStatus.DELEGATED

        # Store subtask in database
        await self._store_subtask(subtask)

        # Delegate to Magister (not directly to agent!)
        await self.magister_coordinator.delegate_to_magister(subtask)

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
        """Handle task result from agent with retry logic

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

        # Check if failed and should retry
        if payload["status"] == "failed":
            subtask = await self._get_subtask(payload["subtask_id"])

            if subtask:
                # Get retry count from result metadata
                retry_count = subtask.get("retry_count", 0)

                if retry_count < self.MAX_RETRIES:
                    # Retry task
                    await self._retry_subtask(subtask, retry_count + 1)
                    return

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
        6. Report to user
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

        # Report to user
        await self.report_to_user(report)

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

        # Collect metrics using new method
        metrics = await self.collect_metrics(task_id)

        # Identify issues
        issues = []
        for result in results:
            if "errors" in result["result"]:
                issues.extend(result["result"]["errors"])
            if result["result"].get("error"):
                issues.append(f"{result['action']}: {result['result']['error']}")

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

    async def report_to_user(self, report: Report) -> dict[str, Any]:
        """Report aggregated results to user

        Args:
            report: Aggregated report

        Returns:
            User-friendly report dict
        """
        # Create user-friendly report
        user_report = {
            "task_id": report.task_id,
            "status": "completed",
            "summary": report.summary,
            "insights": report.insights,
            "metrics": report.metrics,
            "issues": report.issues,
            "recommendations": report.recommendations,
            "completed_at": report.created_at.isoformat(),
        }

        # Write to vault for user
        await self._write_user_report(user_report)

        # Publish user notification event
        await self._notify_user(user_report)

        return user_report

    async def _write_user_report(self, user_report: dict[str, Any]) -> None:
        """Write user report to vault

        Args:
            user_report: User-friendly report
        """
        content = f"""---
task_id: {user_report['task_id']}
status: {user_report['status']}
completed: {user_report['completed_at']}
---

# Task Completed: {user_report['task_id']}

## Summary
{user_report['summary']}

## Key Insights
{chr(10).join(f"- {insight}" for insight in user_report['insights']) if user_report['insights'] else "No insights"}

## Performance Metrics
```json
{json.dumps(user_report['metrics'], indent=2)}
```

## Issues Encountered
{chr(10).join(f"- {issue}" for issue in user_report['issues']) if user_report['issues'] else "No issues"}

## Recommendations
{chr(10).join(f"- {rec}" for rec in user_report['recommendations'])}

---

**Report generated by Operator**
**Time:** {user_report['completed_at']}
"""

        await self.vault.write_file(
            f"operator/user-reports/report-{user_report['task_id']}.md",
            content,
        )

    async def _notify_user(self, user_report: dict[str, Any]) -> None:
        """Notify user about completed task

        Args:
            user_report: User-friendly report
        """
        # Publish notification event
        await self.event_bus.publish(
            Message(
                from_agent=self.agent_id,
                to_agent="user",
                message_type="task_completed",
                priority=0,  # High priority
                payload=user_report,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        )

    async def get_user_report(self, task_id: str) -> dict[str, Any] | None:
        """Get user report for a task

        Args:
            task_id: Task ID

        Returns:
            User report dict or None if not found
        """
        # Get report from database
        async with self.db.session() as session:
            result = await session.execute(
                text("""
                SELECT report_id, summary, insights, metrics, issues,
                       recommendations, created_at
                FROM operator_reports
                WHERE task_id = :task_id
                """),
                {"task_id": task_id},
            )
            row = result.fetchone()

        if not row:
            return None

        return {
            "task_id": task_id,
            "status": "completed",
            "summary": row[1],
            "insights": json.loads(row[2]),
            "metrics": json.loads(row[3]),
            "issues": json.loads(row[4]),
            "recommendations": json.loads(row[5]),
            "completed_at": row[6] if isinstance(row[6], str) else (row[6].isoformat() if row[6] else None),
        }

    async def _get_subtask(self, subtask_id: str) -> dict[str, Any] | None:
        """Get subtask by ID

        Args:
            subtask_id: Subtask ID

        Returns:
            Subtask dict or None
        """
        async with self.db.session() as session:
            result = await session.execute(
                text("""
                SELECT subtask_id, parent_task_id, agent_id, action, description,
                       dependencies, priority, status, result, created_at, completed_at
                FROM operator_subtasks
                WHERE subtask_id = :subtask_id
                """),
                {"subtask_id": subtask_id},
            )
            row = result.fetchone()

        if not row:
            return None

        # Parse result to get retry_count
        result_data = json.loads(row[8]) if row[8] else {}

        return {
            "subtask_id": row[0],
            "parent_task_id": row[1],
            "agent_id": row[2],
            "action": row[3],
            "description": row[4],
            "dependencies": json.loads(row[5]),
            "priority": row[6],
            "status": row[7],
            "result": result_data,
            "retry_count": result_data.get("retry_count", 0),
            "created_at": row[9],
            "completed_at": row[10],
        }

    async def _retry_subtask(
        self,
        subtask: dict[str, Any],
        retry_count: int,
    ) -> None:
        """Retry failed subtask

        Args:
            subtask: Failed subtask
            retry_count: Current retry attempt
        """
        # Wait before retry
        await asyncio.sleep(self.RETRY_DELAY_SECONDS)

        # Create new subtask with retry count
        retry_subtask = Subtask(
            subtask_id=subtask["subtask_id"],
            parent_task_id=subtask["parent_task_id"],
            agent_id=subtask["agent_id"],
            action=subtask["action"],
            description=f"{subtask['description']} (Retry {retry_count}/{self.MAX_RETRIES})",
            dependencies=subtask["dependencies"],
            priority=subtask["priority"],
            status=TaskStatus.RECEIVED,
            result={"retry_count": retry_count},
            created_at=subtask["created_at"],
            completed_at=None,
        )

        # Update in database with retry count
        async with self.db.session() as session:
            await session.execute(
                text("""
                UPDATE operator_subtasks
                SET status = :status,
                    result = :result,
                    completed_at = NULL
                WHERE subtask_id = :subtask_id
                """),
                {
                    "status": TaskStatus.RECEIVED.value,
                    "result": json.dumps({"retry_count": retry_count}),
                    "subtask_id": subtask["subtask_id"],
                },
            )
            await session.commit()

        # Re-delegate
        await self.delegate_to_agent(retry_subtask)

        # Log retry
        await self._log_retry(subtask, retry_count)

    async def _log_retry(
        self,
        subtask: dict[str, Any],
        retry_count: int,
    ) -> None:
        """Log subtask retry

        Args:
            subtask: Subtask being retried
            retry_count: Retry attempt number
        """
        log_content = f"""---
subtask_id: {subtask['subtask_id']}
retry_count: {retry_count}
max_retries: {self.MAX_RETRIES}
logged_at: {datetime.now(timezone.utc).isoformat()}
---

# Retry: {subtask['action']}

## Subtask
{subtask['description']}

## Agent
{subtask['agent_id']}

## Retry Attempt
{retry_count} of {self.MAX_RETRIES}

## Previous Result
```json
{json.dumps(subtask.get('result', {}), indent=2)}
```
"""

        await self.vault.write_file(
            f"operator/retries/{subtask['subtask_id']}-retry-{retry_count}.md",
            log_content,
        )

    async def monitor_timeouts(self) -> None:
        """Monitor and handle task timeouts

        Should be called periodically (e.g., every minute)
        """
        now = datetime.now(timezone.utc)

        # Get all in-progress subtasks
        async with self.db.session() as session:
            result = await session.execute(
                text("""
                SELECT subtask_id, agent_id, action, created_at, result
                FROM operator_subtasks
                WHERE status IN ('delegated', 'in_progress')
                """)
            )
            subtasks = result.fetchall()

        for row in subtasks:
            subtask_id, agent_id, action, created_at, result_json = row

            # Check timeout
            timeout = self.AGENT_TIMEOUTS.get(agent_id, timedelta(minutes=30))
            elapsed = now - created_at

            if elapsed > timeout:
                # Handle timeout
                await self._handle_timeout(subtask_id, agent_id, action)

    async def _handle_timeout(
        self,
        subtask_id: str,
        agent_id: str,
        action: str,
    ) -> None:
        """Handle subtask timeout

        Args:
            subtask_id: Timed out subtask
            agent_id: Agent that timed out
            action: Action that timed out
        """
        # Mark as failed
        await self._update_subtask_result(
            subtask_id=subtask_id,
            status="failed",
            result={"error": "timeout", "agent_id": agent_id},
            completed_at=datetime.now(timezone.utc).isoformat(),
        )

        # Log timeout
        await self._log_timeout(subtask_id, agent_id, action)

        # Get subtask for retry
        subtask = await self._get_subtask(subtask_id)

        if subtask:
            # Trigger retry logic via _handle_task_result
            await self._handle_task_result(
                Message(
                    from_agent=agent_id,
                    to_agent=self.agent_id,
                    message_type="task_result",
                    priority=1,
                    payload={
                        "subtask_id": subtask_id,
                        "parent_task_id": subtask["parent_task_id"],
                        "status": "failed",
                        "result": {"error": "timeout"},
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                    },
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            )

    async def _log_timeout(
        self,
        subtask_id: str,
        agent_id: str,
        action: str,
    ) -> None:
        """Log subtask timeout

        Args:
            subtask_id: Timed out subtask
            agent_id: Agent that timed out
            action: Action that timed out
        """
        timeout = self.AGENT_TIMEOUTS.get(agent_id, timedelta(minutes=30))

        log_content = f"""---
subtask_id: {subtask_id}
agent_id: {agent_id}
action: {action}
timeout: {timeout}
logged_at: {datetime.now(timezone.utc).isoformat()}
---

# Timeout: {action}

## Agent
{agent_id}

## Action
{action}

## Timeout Duration
{timeout}

## Status
Task exceeded timeout and was marked as failed.
Retry logic will be triggered automatically.
"""

        await self.vault.write_file(
            f"operator/timeouts/{subtask_id}-timeout.md",
            log_content,
        )

    async def collect_metrics(self, task_id: str) -> dict[str, Any]:
        """Collect performance metrics for task

        Args:
            task_id: Task ID

        Returns:
            Metrics dict
        """
        async with self.db.session() as session:
            # Get task timing
            result = await session.execute(
                text("""
                SELECT created_at, updated_at
                FROM operator_tasks
                WHERE task_id = :task_id
                """),
                {"task_id": task_id},
            )
            task_row = result.fetchone()

            # Get subtask stats
            result = await session.execute(
                text("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    AVG(CASE
                        WHEN completed_at IS NOT NULL AND created_at IS NOT NULL
                        THEN (JULIANDAY(completed_at) - JULIANDAY(created_at)) * 86400
                        ELSE NULL
                    END) as avg_duration
                FROM operator_subtasks
                WHERE parent_task_id = :task_id
                """),
                {"task_id": task_id},
            )
            stats = result.fetchone()

        if not task_row or not stats:
            return {}

        total = stats[0] or 0
        completed = stats[1] or 0
        failed = stats[2] or 0
        avg_duration = stats[3] or 0

        # Calculate total duration
        total_duration = 0
        if task_row[1] and task_row[0]:
            # Parse timestamps if they're strings
            if isinstance(task_row[0], str):
                from datetime import datetime
                created = datetime.fromisoformat(task_row[0].replace('Z', '+00:00'))
                updated = datetime.fromisoformat(task_row[1].replace('Z', '+00:00'))
                total_duration = (updated - created).total_seconds()
            else:
                total_duration = (task_row[1] - task_row[0]).total_seconds()

        return {
            "total_subtasks": total,
            "completed": completed,
            "failed": failed,
            "success_rate": completed / total if total > 0 else 0,
            "avg_duration_seconds": avg_duration,
            "total_duration_seconds": total_duration,
        }
