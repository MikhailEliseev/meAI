"""Brand Magister - Brand strategy specialist agent"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from meai.agents.magisters.base_magister import BaseMagister
from meai.agents.base_agent import Task, TaskResult
from meai.events.event_bus import EventBus, Message

logger = logging.getLogger(__name__)


class BrandMagister(BaseMagister):
    """Brand Magister - Brand strategy specialist

    Domain: Brand Strategy (Branding, Positioning, Tone of Voice)

    Capabilities:
    - analyze_competitor_brands: Analyze competitor brand positioning
    - conduct_custdev: Conduct customer development (synthetic + real)
    - generate_tone_of_voice: Generate Tone of Voice for segments
    - analyze_visual_brand: Visual brand analysis (static + dynamic)
    - monitor_brand_mentions: Monitor brand mentions across channels
    """

    def __init__(
        self,
        agent_id: str = "brand-magister-1",
        event_bus: EventBus = None,
        vault_path: Path = None,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        orchestrators: dict[str, Any] = None,
    ):
        """Initialize Brand Magister

        Args:
            agent_id: Unique agent identifier
            event_bus: Event bus for communication
            vault_path: Path to Obsidian vault
            database_url: Database URL
            orchestrators: Dict of orchestrator name -> orchestrator instance
                          e.g., {"custdev": CustDevOrchestrator(...)}
        """
        if vault_path is None:
            vault_path = Path("./AIM/obsidian/brand-magister")

        super().__init__(
            agent_id=agent_id,
            magister_type="brand",
            domain="brand",
            event_bus=event_bus,
            vault_path=vault_path,
            database_url=database_url,
        )

        # Initialize orchestrators
        self.orchestrators = orchestrators or {}
        self.current_task_id = None

    def get_capabilities(self) -> list[str]:
        """Get Brand Magister capabilities"""
        base_capabilities = super().get_capabilities()

        brand_capabilities = [
            "analyze_competitor_brands",
            "conduct_custdev",
            "generate_tone_of_voice",
            "analyze_visual_brand",
            "monitor_brand_mentions",
        ]

        return base_capabilities + brand_capabilities

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute Brand-specific task

        Routes to appropriate handler based on action:
        - analyze_competitor_brands → _handle_competitor_brand_analysis()
        - conduct_custdev → _handle_custdev()
        - generate_tone_of_voice → _handle_tov_generation()
        - analyze_visual_brand → _handle_visual_analysis()
        - monitor_brand_mentions → _handle_brand_monitoring()
        """
        self.current_task_id = task.task_id
        action = task.action

        logger.info(f"Brand Magister executing task: {task.task_id}, action: {action}")

        try:
            if action == "analyze_competitor_brands":
                return await self._handle_competitor_brand_analysis(task)
            elif action == "conduct_custdev":
                return await self._handle_custdev(task)
            elif action == "generate_tone_of_voice":
                return await self._handle_tov_generation(task)
            elif action == "analyze_visual_brand":
                return await self._handle_visual_analysis(task)
            elif action == "monitor_brand_mentions":
                return await self._handle_brand_monitoring(task)
            else:
                return await self._handle_generic_brand(task)
        except Exception as e:
            logger.error(f"Task execution failed: {e}", exc_info=True)
            return self._create_error_result(task, e)
        finally:
            self.current_task_id = None

    async def _handle_competitor_brand_analysis(self, task: Task) -> TaskResult:
        """Handle competitor brand analysis via Brand Analysis orchestrator"""
        logger.info(f"Handling competitor brand analysis for task {task.task_id}")

        try:
            # 1. Get orchestrator
            orchestrator = self.orchestrators.get("brand_analysis")
            if not orchestrator:
                # Fallback: direct implementation
                return await self._analyze_competitor_brands_direct(task)

            # 2. Create brand analysis task data
            analysis_task_data = {
                "task_id": task.task_id,
                "analysis_type": "competitor_brands",
                "competitors": task.data.get("competitors", []),
                "aspects": task.data.get("aspects", ["visual", "positioning", "tov"]),
            }

            # 3. Set timeout
            timeout_seconds = 600  # 10 min for brand analysis

            # 4. Execute with timeout and progress updates
            await self._publish_progress(0, "started", "Starting competitor brand analysis")

            analysis_result = await asyncio.wait_for(
                orchestrator.analyze_brands(analysis_task_data),
                timeout=timeout_seconds,
            )

            await self._publish_progress(100, "completed", "Competitor brand analysis completed")

            # 5. Create result
            return TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                status="completed",
                result=analysis_result,
                metadata={
                    "orchestrator": "brand_analysis",
                    "competitors_analyzed": len(task.data.get("competitors", [])),
                },
            )

        except asyncio.TimeoutError:
            logger.error(f"Competitor brand analysis timed out for task {task.task_id}")
            return self._create_timeout_result(task, timeout_seconds)
        except Exception as e:
            logger.error(f"Competitor brand analysis failed: {e}", exc_info=True)
            return self._create_error_result(task, e)

    async def _handle_custdev(self, task: Task) -> TaskResult:
        """Handle customer development via CustDev orchestrator"""
        logger.info(f"Handling CustDev for task {task.task_id}")

        try:
            # 1. Get orchestrator
            orchestrator = self.orchestrators.get("custdev")
            if not orchestrator:
                # Fallback: direct implementation
                return await self._conduct_custdev_direct(task)

            # 2. Create CustDev task data
            custdev_task_data = {
                "task_id": task.task_id,
                "custdev_type": task.data.get("custdev_type", "both"),  # synthetic, real, both
                "project_id": task.data.get("project_id"),
                "segments": task.data.get("segments", []),
            }

            # 3. Set timeout
            timeout_seconds = 900  # 15 min for CustDev

            # 4. Execute with timeout and progress updates
            await self._publish_progress(0, "started", "Starting customer development")

            custdev_result = await asyncio.wait_for(
                orchestrator.conduct_custdev(custdev_task_data),
                timeout=timeout_seconds,
            )

            await self._publish_progress(100, "completed", "Customer development completed")

            # 5. Create result
            return TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                status="completed",
                result=custdev_result,
                metadata={
                    "orchestrator": "custdev",
                    "custdev_type": task.data.get("custdev_type", "both"),
                },
            )

        except asyncio.TimeoutError:
            logger.error(f"CustDev timed out for task {task.task_id}")
            return self._create_timeout_result(task, timeout_seconds)
        except Exception as e:
            logger.error(f"CustDev failed: {e}", exc_info=True)
            return self._create_error_result(task, e)

    async def _handle_tov_generation(self, task: Task) -> TaskResult:
        """Handle Tone of Voice generation via ToV orchestrator"""
        logger.info(f"Handling ToV generation for task {task.task_id}")

        try:
            # 1. Get orchestrator
            orchestrator = self.orchestrators.get("tov")
            if not orchestrator:
                # Fallback: direct implementation
                return await self._generate_tov_direct(task)

            # 2. Create ToV task data
            tov_task_data = {
                "task_id": task.task_id,
                "segments": task.data.get("segments", []),
                "custdev_data": task.data.get("custdev_data", {}),
                "brand_positioning": task.data.get("brand_positioning", {}),
            }

            # 3. Set timeout
            timeout_seconds = 300  # 5 min for ToV generation

            # 4. Execute with timeout and progress updates
            await self._publish_progress(0, "started", "Starting ToV generation")

            tov_result = await asyncio.wait_for(
                orchestrator.generate_tov(tov_task_data),
                timeout=timeout_seconds,
            )

            await self._publish_progress(100, "completed", "ToV generation completed")

            # 5. Create result
            return TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                status="completed",
                result=tov_result,
                metadata={
                    "orchestrator": "tov",
                    "segments_count": len(task.data.get("segments", [])),
                },
            )

        except asyncio.TimeoutError:
            logger.error(f"ToV generation timed out for task {task.task_id}")
            return self._create_timeout_result(task, timeout_seconds)
        except Exception as e:
            logger.error(f"ToV generation failed: {e}", exc_info=True)
            return self._create_error_result(task, e)

    async def _handle_visual_analysis(self, task: Task) -> TaskResult:
        """Handle visual brand analysis via Brand Analysis orchestrator"""
        logger.info(f"Handling visual analysis for task {task.task_id}")

        try:
            # 1. Get orchestrator
            orchestrator = self.orchestrators.get("brand_analysis")
            if not orchestrator:
                # Fallback: direct implementation
                return await self._analyze_visual_brand_direct(task)

            # 2. Create visual analysis task data
            visual_task_data = {
                "task_id": task.task_id,
                "analysis_type": "visual",
                "target_url": task.data.get("target_url"),
                "analysis_mode": task.data.get("analysis_mode", "static"),  # static, dynamic, both
                "webvisor_enabled": task.data.get("webvisor_enabled", False),
            }

            # 3. Set timeout
            timeout_seconds = 600  # 10 min for visual analysis

            # 4. Execute with timeout and progress updates
            await self._publish_progress(0, "started", "Starting visual brand analysis")

            visual_result = await asyncio.wait_for(
                orchestrator.analyze_visual_brand(visual_task_data),
                timeout=timeout_seconds,
            )

            await self._publish_progress(100, "completed", "Visual brand analysis completed")

            # 5. Create result
            return TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                status="completed",
                result=visual_result,
                metadata={
                    "orchestrator": "brand_analysis",
                    "analysis_mode": task.data.get("analysis_mode", "static"),
                },
            )

        except asyncio.TimeoutError:
            logger.error(f"Visual analysis timed out for task {task.task_id}")
            return self._create_timeout_result(task, timeout_seconds)
        except Exception as e:
            logger.error(f"Visual analysis failed: {e}", exc_info=True)
            return self._create_error_result(task, e)

    async def _handle_brand_monitoring(self, task: Task) -> TaskResult:
        """Handle brand mentions monitoring via Brand Monitoring orchestrator"""
        logger.info(f"Handling brand monitoring for task {task.task_id}")

        try:
            # 1. Get orchestrator
            orchestrator = self.orchestrators.get("brand_monitoring")
            if not orchestrator:
                # Fallback: direct implementation
                return await self._monitor_brand_mentions_direct(task)

            # 2. Create monitoring task data
            monitoring_task_data = {
                "task_id": task.task_id,
                "brand_name": task.data.get("brand_name"),
                "channels": task.data.get("channels", ["telegram", "media", "social"]),
                "time_range": task.data.get("time_range", "week"),
            }

            # 3. Set timeout
            timeout_seconds = 300  # 5 min for monitoring

            # 4. Execute with timeout and progress updates
            await self._publish_progress(0, "started", "Starting brand monitoring")

            monitoring_result = await asyncio.wait_for(
                orchestrator.monitor_brand(monitoring_task_data),
                timeout=timeout_seconds,
            )

            await self._publish_progress(100, "completed", "Brand monitoring completed")

            # 5. Create result
            return TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                status="completed",
                result=monitoring_result,
                metadata={
                    "orchestrator": "brand_monitoring",
                    "channels": task.data.get("channels", []),
                },
            )

        except asyncio.TimeoutError:
            logger.error(f"Brand monitoring timed out for task {task.task_id}")
            return self._create_timeout_result(task, timeout_seconds)
        except Exception as e:
            logger.error(f"Brand monitoring failed: {e}", exc_info=True)
            return self._create_error_result(task, e)

    async def _handle_generic_brand(self, task: Task) -> TaskResult:
        """Handle generic brand task"""
        logger.info(f"Handling generic brand task: {task.action}")

        return TaskResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            status="completed",
            result={
                "message": f"Generic brand task '{task.action}' executed",
                "action": task.action,
            },
            metadata={"handler": "generic"},
        )

    # Fallback direct implementations (when orchestrators not available)

    async def _analyze_competitor_brands_direct(self, task: Task) -> TaskResult:
        """Direct implementation of competitor brand analysis"""
        logger.info("Using direct competitor brand analysis (no orchestrator)")

        competitors = task.data.get("competitors", [])
        aspects = task.data.get("aspects", ["visual", "positioning", "tov"])

        result = {
            "competitors_analyzed": len(competitors),
            "aspects": aspects,
            "analysis": {
                "visual_style": "Analysis requires orchestrator implementation",
                "positioning": "Analysis requires orchestrator implementation",
                "tone_of_voice": "Analysis requires orchestrator implementation",
            },
            "note": "Direct implementation - orchestrator recommended for full analysis",
        }

        return TaskResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            status="completed",
            result=result,
            metadata={"handler": "direct", "orchestrator_missing": True},
        )

    async def _conduct_custdev_direct(self, task: Task) -> TaskResult:
        """Direct implementation of customer development"""
        logger.info("Using direct CustDev (no orchestrator)")

        custdev_type = task.data.get("custdev_type", "both")

        result = {
            "custdev_type": custdev_type,
            "segments": [],
            "activating_knowledge": [],
            "tone_of_voice_recommendations": [],
            "note": "Direct implementation - orchestrator recommended for full CustDev",
        }

        return TaskResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            status="completed",
            result=result,
            metadata={"handler": "direct", "orchestrator_missing": True},
        )

    async def _generate_tov_direct(self, task: Task) -> TaskResult:
        """Direct implementation of ToV generation"""
        logger.info("Using direct ToV generation (no orchestrator)")

        segments = task.data.get("segments", [])

        result = {
            "segments": segments,
            "tone_of_voice": {},
            "note": "Direct implementation - orchestrator recommended for full ToV generation",
        }

        return TaskResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            status="completed",
            result=result,
            metadata={"handler": "direct", "orchestrator_missing": True},
        )

    async def _analyze_visual_brand_direct(self, task: Task) -> TaskResult:
        """Direct implementation of visual brand analysis"""
        logger.info("Using direct visual analysis (no orchestrator)")

        target_url = task.data.get("target_url")
        analysis_mode = task.data.get("analysis_mode", "static")

        result = {
            "target_url": target_url,
            "analysis_mode": analysis_mode,
            "visual_elements": {},
            "critical_points": [],
            "note": "Direct implementation - orchestrator recommended for full visual analysis",
        }

        return TaskResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            status="completed",
            result=result,
            metadata={"handler": "direct", "orchestrator_missing": True},
        )

    async def _monitor_brand_mentions_direct(self, task: Task) -> TaskResult:
        """Direct implementation of brand monitoring"""
        logger.info("Using direct brand monitoring (no orchestrator)")

        brand_name = task.data.get("brand_name")
        channels = task.data.get("channels", [])

        result = {
            "brand_name": brand_name,
            "channels": channels,
            "mentions": [],
            "sentiment": {"positive": 0, "negative": 0, "neutral": 0},
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
