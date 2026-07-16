"""AI Magister - AI systems architect agent"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from meai.agents.magisters.base_magister import BaseMagister
from meai.agents.base_agent import Task, TaskResult
from meai.events import EventBus, EventStore
from meai.events.event_bus import Message

logger = logging.getLogger(__name__)


class AIMagister(BaseMagister):
    """AI Magister - AI systems architect

    Domain: AI Systems (Agent Design, Training, Optimization)

    Capabilities:
    - design_ai_agents: Design AI agents for other Magisters
    - train_agents: Train agents on project data
    - optimize_prompts: Optimize prompts and models
    - monitor_quality: Monitor AI quality and performance
    """

    def __init__(
        self,
        agent_id: str = "ai-magister-1",
        event_bus: EventBus = None,
        event_store: EventStore = None,
        vault_path: Path = None,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        orchestrators: dict[str, Any] = None,
    ):
        """Initialize AI Magister

        Args:
            agent_id: Unique agent identifier
            event_bus: Event bus for communication
            event_store: Event store for audit logging
            vault_path: Path to Obsidian vault
            database_url: Database URL
            orchestrators: Dict of orchestrator name -> orchestrator instance
                          e.g., {"ai": AIOrchestrator(...)}
        """
        if vault_path is None:
            vault_path = Path("./AIM/obsidian/ai-magister")

        super().__init__(
            agent_id=agent_id,
            magister_type="ai",
            domain="ai",
            event_bus=event_bus,
            event_store=event_store,
            vault_path=vault_path,
            database_url=database_url,
        )

        # Initialize orchestrators
        self.orchestrators = orchestrators or {}
        self.current_task_id = None

    def get_capabilities(self) -> list[str]:
        """Get AI Magister capabilities"""
        base_capabilities = super().get_capabilities()

        ai_capabilities = [
            "design_ai_agents",
            "train_agents",
            "optimize_prompts",
            "monitor_quality",
        ]

        return base_capabilities + ai_capabilities

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute AI-specific task

        Routes to appropriate handler based on action:
        - design_ai_agents → _handle_agent_design()
        - train_agents → _handle_agent_training()
        - optimize_prompts → _handle_prompt_optimization()
        - monitor_quality → _handle_quality_monitoring()
        """
        self.current_task_id = task.task_id
        action = task.action

        logger.info(f"AI Magister executing task: {task.task_id}, action: {action}")

        try:
            if action == "design_ai_agents":
                return await self._handle_agent_design(task)
            elif action == "train_agents":
                return await self._handle_agent_training(task)
            elif action == "optimize_prompts":
                return await self._handle_prompt_optimization(task)
            elif action == "monitor_quality":
                return await self._handle_quality_monitoring(task)
            else:
                return await self._handle_generic_ai(task)
        except Exception as e:
            logger.error(f"Task execution failed: {e}", exc_info=True)
            return self._create_error_result(task, e)
        finally:
            self.current_task_id = None

    async def _handle_agent_design(self, task: Task) -> TaskResult:
        """Handle AI agent design via AI orchestrator"""
        logger.info(f"Handling agent design for task {task.task_id}")

        try:
            # 1. Get orchestrator
            orchestrator = self.orchestrators.get("ai")
            if not orchestrator:
                # Fallback: direct implementation
                return await self._design_agents_direct(task)

            # 2. Create agent design task data
            design_task_data = {
                "task_id": task.task_id,
                "magister_type": task.data.get("magister_type"),  # seo, content, ads, etc.
                "agent_purpose": task.data.get("agent_purpose"),
                "capabilities_needed": task.data.get("capabilities_needed", []),
                "domain_knowledge": task.data.get("domain_knowledge", {}),
            }

            # 3. Set timeout
            timeout_seconds = 600  # 10 min for agent design

            # 4. Execute with timeout and progress updates
            await self._publish_progress(0, "started", "Starting agent design")

            design_result = await asyncio.wait_for(
                orchestrator.design_agent(design_task_data),
                timeout=timeout_seconds,
            )

            await self._publish_progress(100, "completed", "Agent design completed")

            # 5. Create result
            return TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                status="completed",
                result=design_result,
                metadata={
                    "orchestrator": "ai",
                    "magister_type": task.data.get("magister_type"),
                },
            )

        except asyncio.TimeoutError:
            logger.error(f"Agent design timed out for task {task.task_id}")
            return self._create_timeout_result(task, timeout_seconds)
        except Exception as e:
            logger.error(f"Agent design failed: {e}", exc_info=True)
            return self._create_error_result(task, e)

    async def _handle_agent_training(self, task: Task) -> TaskResult:
        """Handle agent training via AI orchestrator"""
        logger.info(f"Handling agent training for task {task.task_id}")

        try:
            # 1. Get orchestrator
            orchestrator = self.orchestrators.get("ai")
            if not orchestrator:
                # Fallback: direct implementation
                return await self._train_agents_direct(task)

            # 2. Create training task data
            training_task_data = {
                "task_id": task.task_id,
                "agent_id": task.data.get("agent_id"),
                "training_data": task.data.get("training_data", []),
                "training_type": task.data.get("training_type", "fine_tune"),  # fine_tune, few_shot, rag
            }

            # 3. Set timeout
            timeout_seconds = 1800  # 30 min for training

            # 4. Execute with timeout and progress updates
            await self._publish_progress(0, "started", "Starting agent training")

            training_result = await asyncio.wait_for(
                orchestrator.train_agent(training_task_data),
                timeout=timeout_seconds,
            )

            await self._publish_progress(100, "completed", "Agent training completed")

            # 5. Create result
            return TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                status="completed",
                result=training_result,
                metadata={
                    "orchestrator": "ai",
                    "training_type": task.data.get("training_type", "fine_tune"),
                },
            )

        except asyncio.TimeoutError:
            logger.error(f"Agent training timed out for task {task.task_id}")
            return self._create_timeout_result(task, timeout_seconds)
        except Exception as e:
            logger.error(f"Agent training failed: {e}", exc_info=True)
            return self._create_error_result(task, e)

    async def _handle_prompt_optimization(self, task: Task) -> TaskResult:
        """Handle prompt optimization via AI orchestrator"""
        logger.info(f"Handling prompt optimization for task {task.task_id}")

        try:
            # 1. Get orchestrator
            orchestrator = self.orchestrators.get("ai")
            if not orchestrator:
                # Fallback: direct implementation
                return await self._optimize_prompts_direct(task)

            # 2. Create optimization task data
            optimization_task_data = {
                "task_id": task.task_id,
                "agent_id": task.data.get("agent_id"),
                "current_prompt": task.data.get("current_prompt"),
                "performance_metrics": task.data.get("performance_metrics", {}),
                "optimization_goal": task.data.get("optimization_goal", "quality"),  # quality, speed, cost
            }

            # 3. Set timeout
            timeout_seconds = 300  # 5 min for optimization

            # 4. Execute with timeout and progress updates
            await self._publish_progress(0, "started", "Starting prompt optimization")

            optimization_result = await asyncio.wait_for(
                orchestrator.optimize_prompt(optimization_task_data),
                timeout=timeout_seconds,
            )

            await self._publish_progress(100, "completed", "Prompt optimization completed")

            # 5. Create result
            return TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                status="completed",
                result=optimization_result,
                metadata={
                    "orchestrator": "ai",
                    "optimization_goal": task.data.get("optimization_goal", "quality"),
                },
            )

        except asyncio.TimeoutError:
            logger.error(f"Prompt optimization timed out for task {task.task_id}")
            return self._create_timeout_result(task, timeout_seconds)
        except Exception as e:
            logger.error(f"Prompt optimization failed: {e}", exc_info=True)
            return self._create_error_result(task, e)

    async def _handle_quality_monitoring(self, task: Task) -> TaskResult:
        """Handle quality monitoring via AI orchestrator"""
        logger.info(f"Handling quality monitoring for task {task.task_id}")

        try:
            # 1. Get orchestrator
            orchestrator = self.orchestrators.get("ai")
            if not orchestrator:
                # Fallback: direct implementation
                return await self._monitor_quality_direct(task)

            # 2. Create monitoring task data
            monitoring_task_data = {
                "task_id": task.task_id,
                "agent_id": task.data.get("agent_id"),
                "time_range": task.data.get("time_range", "week"),
                "metrics": task.data.get("metrics", ["accuracy", "latency", "cost"]),
            }

            # 3. Set timeout
            timeout_seconds = 180  # 3 min for monitoring

            # 4. Execute with timeout and progress updates
            await self._publish_progress(0, "started", "Starting quality monitoring")

            monitoring_result = await asyncio.wait_for(
                orchestrator.monitor_quality(monitoring_task_data),
                timeout=timeout_seconds,
            )

            await self._publish_progress(100, "completed", "Quality monitoring completed")

            # 5. Create result
            return TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                status="completed",
                result=monitoring_result,
                metadata={
                    "orchestrator": "ai",
                    "time_range": task.data.get("time_range", "week"),
                },
            )

        except asyncio.TimeoutError:
            logger.error(f"Quality monitoring timed out for task {task.task_id}")
            return self._create_timeout_result(task, timeout_seconds)
        except Exception as e:
            logger.error(f"Quality monitoring failed: {e}", exc_info=True)
            return self._create_error_result(task, e)

    async def _handle_generic_ai(self, task: Task) -> TaskResult:
        """Handle generic AI task"""
        logger.info(f"Handling generic AI task: {task.action}")

        return TaskResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            status="completed",
            result={
                "message": f"Generic AI task '{task.action}' executed",
                "action": task.action,
            },
            metadata={"handler": "generic"},
        )

    # Fallback direct implementations (when orchestrators not available)

    async def _design_agents_direct(self, task: Task) -> TaskResult:
        """Direct implementation of agent design"""
        logger.info("Using direct agent design (no orchestrator)")

        magister_type = task.data.get("magister_type")
        agent_purpose = task.data.get("agent_purpose")

        result = {
            "magister_type": magister_type,
            "agent_purpose": agent_purpose,
            "agent_design": {
                "architecture": "To be designed",
                "capabilities": [],
                "prompts": {},
            },
            "note": "Direct implementation - orchestrator recommended for full design",
        }

        return TaskResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            status="completed",
            result=result,
            metadata={"handler": "direct", "orchestrator_missing": True},
        )

    async def _train_agents_direct(self, task: Task) -> TaskResult:
        """Direct implementation of agent training"""
        logger.info("Using direct agent training (no orchestrator)")

        agent_id = task.data.get("agent_id")
        training_type = task.data.get("training_type", "fine_tune")

        result = {
            "agent_id": agent_id,
            "training_type": training_type,
            "training_status": "Not implemented",
            "note": "Direct implementation - orchestrator recommended for full training",
        }

        return TaskResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            status="completed",
            result=result,
            metadata={"handler": "direct", "orchestrator_missing": True},
        )

    async def _optimize_prompts_direct(self, task: Task) -> TaskResult:
        """Direct implementation of prompt optimization"""
        logger.info("Using direct prompt optimization (no orchestrator)")

        agent_id = task.data.get("agent_id")
        optimization_goal = task.data.get("optimization_goal", "quality")

        result = {
            "agent_id": agent_id,
            "optimization_goal": optimization_goal,
            "optimized_prompt": "To be optimized",
            "note": "Direct implementation - orchestrator recommended for full optimization",
        }

        return TaskResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            status="completed",
            result=result,
            metadata={"handler": "direct", "orchestrator_missing": True},
        )

    async def _monitor_quality_direct(self, task: Task) -> TaskResult:
        """Direct implementation of quality monitoring"""
        logger.info("Using direct quality monitoring (no orchestrator)")

        agent_id = task.data.get("agent_id")
        time_range = task.data.get("time_range", "week")

        result = {
            "agent_id": agent_id,
            "time_range": time_range,
            "quality_metrics": {
                "accuracy": 0.0,
                "latency": 0.0,
                "cost": 0.0,
            },
            "note": "Direct implementation - orchestrator recommended for full monitoring",
        }

        return TaskResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            status="completed",
            result=result,
            metadata={"handler": "direct", "orchestrator_missing": True},
        )

    async def _publish_progress(
        self, progress: int, status: str, message: str
    ) -> None:
        """Publish progress update"""
        if not self.current_task_id:
            return

        await self.event_bus.publish(
            Message(
                id=f"progress-{self.current_task_id}-{datetime.now(timezone.utc).timestamp()}",
                type="task.progress",
                source=self.agent_id,
                target="operator",
                priority=3,
                data={
                    "task_id": self.current_task_id,
                    "progress": progress,
                    "status": status,
                    "message": message,
                },
            )
        )

    def _create_timeout_result(self, task: Task, timeout_seconds: int) -> TaskResult:
        """Create timeout result"""
        return TaskResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            status="failed",
            result={"error": f"Task timed out after {timeout_seconds} seconds"},
            metadata={"timeout": timeout_seconds},
        )

    def _create_error_result(self, task: Task, error: Exception) -> TaskResult:
        """Create error result"""
        return TaskResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            status="failed",
            result={"error": str(error)},
            metadata={"error_type": type(error).__name__},
        )
