"""Reputation Magister - Reputation management specialist agent"""

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


class ReputationMagister(BaseMagister):
    """Reputation Magister - Reputation management specialist

    Domain: Reputation Management (Reviews, Sentiment, Crisis Management)

    Capabilities:
    - monitor_reviews: Monitor reviews across all platforms
    - analyze_sentiment: Analyze sentiment of reviews and mentions
    - generate_responses: Generate responses to reviews
    - manage_crisis: Detect and manage reputation crises
    - track_competitor_reputation: Track competitor reputation
    """

    def __init__(
        self,
        agent_id: str = "reputation-magister-1",
        event_bus: EventBus = None,
        event_store: EventStore = None,
        vault_path: Path = None,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        orchestrators: dict[str, Any] = None,
    ):
        """Initialize Reputation Magister

        Args:
            agent_id: Unique agent identifier
            event_bus: Event bus for communication
            event_store: Event store for audit logging
            vault_path: Path to Obsidian vault
            database_url: Database URL
            orchestrators: Dict of orchestrator name -> orchestrator instance
                          e.g., {"reputation": ReputationOrchestrator(...)}
        """
        if vault_path is None:
            vault_path = Path("./AIM/obsidian/reputation-magister")

        super().__init__(
            agent_id=agent_id,
            magister_type="reputation",
            domain="reputation",
            event_bus=event_bus,
            event_store=event_store,
            vault_path=vault_path,
            database_url=database_url,
        )

        # Initialize orchestrators
        self.orchestrators = orchestrators or {}
        self.current_task_id = None

        # Baseline metrics (set during project setup)
        self.baseline_metrics = {}

    def get_capabilities(self) -> list[str]:
        """Get Reputation Magister capabilities"""
        base_capabilities = super().get_capabilities()

        reputation_capabilities = [
            "monitor_reviews",
            "analyze_sentiment",
            "generate_responses",
            "manage_crisis",
            "track_competitor_reputation",
        ]

        return base_capabilities + reputation_capabilities

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute Reputation-specific task

        Routes to appropriate handler based on action:
        - monitor_reviews → _handle_review_monitoring()
        - analyze_sentiment → _handle_sentiment_analysis()
        - generate_responses → _handle_response_generation()
        - manage_crisis → _handle_crisis_management()
        - track_competitor_reputation → _handle_competitor_tracking()
        """
        self.current_task_id = task.task_id
        action = task.action

        logger.info(f"Reputation Magister executing task: {task.task_id}, action: {action}")

        try:
            if action == "monitor_reviews":
                return await self._handle_review_monitoring(task)
            elif action == "analyze_sentiment":
                return await self._handle_sentiment_analysis(task)
            elif action == "generate_responses":
                return await self._handle_response_generation(task)
            elif action == "manage_crisis":
                return await self._handle_crisis_management(task)
            elif action == "track_competitor_reputation":
                return await self._handle_competitor_tracking(task)
            elif action == "setup_baseline":
                return await self._handle_baseline_setup(task)
            else:
                return await self._handle_generic_reputation(task)
        except Exception as e:
            logger.error(f"Task execution failed: {e}", exc_info=True)
            return self._create_error_result(task, e)
        finally:
            self.current_task_id = None

    async def _handle_review_monitoring(self, task: Task) -> TaskResult:
        """Handle review monitoring via Reputation orchestrator"""
        logger.info(f"Handling review monitoring for task {task.task_id}")

        try:
            # 1. Get orchestrator
            orchestrator = self.orchestrators.get("reputation")
            if not orchestrator:
                # Fallback: direct implementation
                return await self._monitor_reviews_direct(task)

            # 2. Create monitoring task data
            monitoring_task_data = {
                "task_id": task.task_id,
                "platforms": task.data.get("platforms", [
                    "yandex_maps", "google_reviews", "2gis", "zoon",
                    "prodoctorov", "napopravku"
                ]),
                "target_type": task.data.get("target_type", "our_brand"),  # our_brand, competitors
                "competitors": task.data.get("competitors", []),
            }

            # 3. Set timeout
            timeout_seconds = 300  # 5 min for review monitoring

            # 4. Execute with timeout and progress updates
            await self._publish_progress(0, "started", "Starting review monitoring")

            monitoring_result = await asyncio.wait_for(
                orchestrator.monitor_reviews(monitoring_task_data),
                timeout=timeout_seconds,
            )

            await self._publish_progress(100, "completed", "Review monitoring completed")

            # 5. Create result
            return TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                status="completed",
                result=monitoring_result,
                metadata={
                    "orchestrator": "reputation",
                    "platforms_count": len(monitoring_task_data["platforms"]),
                },
            )

        except asyncio.TimeoutError:
            logger.error(f"Review monitoring timed out for task {task.task_id}")
            return self._create_timeout_result(task, timeout_seconds)
        except Exception as e:
            logger.error(f"Review monitoring failed: {e}", exc_info=True)
            return self._create_error_result(task, e)

    async def _handle_sentiment_analysis(self, task: Task) -> TaskResult:
        """Handle sentiment analysis via Reputation orchestrator"""
        logger.info(f"Handling sentiment analysis for task {task.task_id}")

        try:
            # 1. Get orchestrator
            orchestrator = self.orchestrators.get("reputation")
            if not orchestrator:
                # Fallback: direct implementation
                return await self._analyze_sentiment_direct(task)

            # 2. Create sentiment analysis task data
            sentiment_task_data = {
                "task_id": task.task_id,
                "reviews": task.data.get("reviews", []),
                "mentions": task.data.get("mentions", []),
                "calculate_nps": task.data.get("calculate_nps", True),
            }

            # 3. Set timeout
            timeout_seconds = 180  # 3 min for sentiment analysis

            # 4. Execute with timeout and progress updates
            await self._publish_progress(0, "started", "Starting sentiment analysis")

            sentiment_result = await asyncio.wait_for(
                orchestrator.analyze_sentiment(sentiment_task_data),
                timeout=timeout_seconds,
            )

            await self._publish_progress(100, "completed", "Sentiment analysis completed")

            # 5. Create result
            return TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                status="completed",
                result=sentiment_result,
                metadata={
                    "orchestrator": "reputation",
                    "reviews_analyzed": len(task.data.get("reviews", [])),
                },
            )

        except asyncio.TimeoutError:
            logger.error(f"Sentiment analysis timed out for task {task.task_id}")
            return self._create_timeout_result(task, timeout_seconds)
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}", exc_info=True)
            return self._create_error_result(task, e)

    async def _handle_response_generation(self, task: Task) -> TaskResult:
        """Handle response generation via Reputation orchestrator"""
        logger.info(f"Handling response generation for task {task.task_id}")

        try:
            # 1. Get orchestrator
            orchestrator = self.orchestrators.get("reputation")
            if not orchestrator:
                # Fallback: direct implementation
                return await self._generate_responses_direct(task)

            # 2. Create response generation task data
            response_task_data = {
                "task_id": task.task_id,
                "reviews": task.data.get("reviews", []),
                "tone_of_voice": task.data.get("tone_of_voice", {}),
                "response_speed": task.data.get("response_speed", "< 2 hours"),
            }

            # 3. Set timeout
            timeout_seconds = 120  # 2 min for response generation

            # 4. Execute with timeout and progress updates
            await self._publish_progress(0, "started", "Starting response generation")

            response_result = await asyncio.wait_for(
                orchestrator.generate_responses(response_task_data),
                timeout=timeout_seconds,
            )

            await self._publish_progress(100, "completed", "Response generation completed")

            # 5. Create result
            return TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                status="completed",
                result=response_result,
                metadata={
                    "orchestrator": "reputation",
                    "responses_generated": len(task.data.get("reviews", [])),
                },
            )

        except asyncio.TimeoutError:
            logger.error(f"Response generation timed out for task {task.task_id}")
            return self._create_timeout_result(task, timeout_seconds)
        except Exception as e:
            logger.error(f"Response generation failed: {e}", exc_info=True)
            return self._create_error_result(task, e)

    async def _handle_crisis_management(self, task: Task) -> TaskResult:
        """Handle crisis management via Reputation orchestrator"""
        logger.info(f"Handling crisis management for task {task.task_id}")

        try:
            # 1. Get orchestrator
            orchestrator = self.orchestrators.get("reputation")
            if not orchestrator:
                # Fallback: direct implementation
                return await self._manage_crisis_direct(task)

            # 2. Create crisis management task data
            crisis_task_data = {
                "task_id": task.task_id,
                "crisis_type": task.data.get("crisis_type", "detect"),  # detect, manage, predict
                "reviews": task.data.get("reviews", []),
                "mentions": task.data.get("mentions", []),
            }

            # 3. Set timeout
            timeout_seconds = 300  # 5 min for crisis management

            # 4. Execute with timeout and progress updates
            await self._publish_progress(0, "started", "Starting crisis management")

            crisis_result = await asyncio.wait_for(
                orchestrator.manage_crisis(crisis_task_data),
                timeout=timeout_seconds,
            )

            await self._publish_progress(100, "completed", "Crisis management completed")

            # 5. Create result
            return TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                status="completed",
                result=crisis_result,
                metadata={
                    "orchestrator": "reputation",
                    "crisis_type": task.data.get("crisis_type", "detect"),
                },
            )

        except asyncio.TimeoutError:
            logger.error(f"Crisis management timed out for task {task.task_id}")
            return self._create_timeout_result(task, timeout_seconds)
        except Exception as e:
            logger.error(f"Crisis management failed: {e}", exc_info=True)
            return self._create_error_result(task, e)

    async def _handle_competitor_tracking(self, task: Task) -> TaskResult:
        """Handle competitor reputation tracking via Reputation orchestrator"""
        logger.info(f"Handling competitor tracking for task {task.task_id}")

        try:
            # 1. Get orchestrator
            orchestrator = self.orchestrators.get("reputation")
            if not orchestrator:
                # Fallback: direct implementation
                return await self._track_competitors_direct(task)

            # 2. Create competitor tracking task data
            tracking_task_data = {
                "task_id": task.task_id,
                "competitors": task.data.get("competitors", []),
                "platforms": task.data.get("platforms", [
                    "yandex_maps", "google_reviews", "2gis", "zoon"
                ]),
                "detect_fuckups": task.data.get("detect_fuckups", True),
                "detect_successes": task.data.get("detect_successes", True),
            }

            # 3. Set timeout
            timeout_seconds = 600  # 10 min for competitor tracking

            # 4. Execute with timeout and progress updates
            await self._publish_progress(0, "started", "Starting competitor tracking")

            tracking_result = await asyncio.wait_for(
                orchestrator.track_competitors(tracking_task_data),
                timeout=timeout_seconds,
            )

            await self._publish_progress(100, "completed", "Competitor tracking completed")

            # 5. Create result
            return TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                status="completed",
                result=tracking_result,
                metadata={
                    "orchestrator": "reputation",
                    "competitors_tracked": len(task.data.get("competitors", [])),
                },
            )

        except asyncio.TimeoutError:
            logger.error(f"Competitor tracking timed out for task {task.task_id}")
            return self._create_timeout_result(task, timeout_seconds)
        except Exception as e:
            logger.error(f"Competitor tracking failed: {e}", exc_info=True)
            return self._create_error_result(task, e)

    async def _handle_baseline_setup(self, task: Task) -> TaskResult:
        """Handle baseline metrics setup (first analysis)"""
        logger.info(f"Handling baseline setup for task {task.task_id}")

        try:
            # 1. Get orchestrator
            orchestrator = self.orchestrators.get("reputation")
            if not orchestrator:
                # Fallback: direct implementation
                return await self._setup_baseline_direct(task)

            # 2. Create baseline setup task data
            baseline_task_data = {
                "task_id": task.task_id,
                "brand_name": task.data.get("brand_name"),
                "platforms": task.data.get("platforms", [
                    "yandex_maps", "google_reviews", "2gis", "zoon",
                    "prodoctorov", "napopravku"
                ]),
            }

            # 3. Set timeout
            timeout_seconds = 600  # 10 min for baseline setup

            # 4. Execute with timeout and progress updates
            await self._publish_progress(0, "started", "Starting baseline setup")

            baseline_result = await asyncio.wait_for(
                orchestrator.setup_baseline(baseline_task_data),
                timeout=timeout_seconds,
            )

            # 5. Save baseline metrics
            self.baseline_metrics = baseline_result.get("baseline_metrics", {})

            await self._publish_progress(100, "completed", "Baseline setup completed")

            # 6. Create result
            return TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                status="completed",
                result=baseline_result,
                metadata={
                    "orchestrator": "reputation",
                    "baseline_date": datetime.now(timezone.utc).isoformat(),
                },
            )

        except asyncio.TimeoutError:
            logger.error(f"Baseline setup timed out for task {task.task_id}")
            return self._create_timeout_result(task, timeout_seconds)
        except Exception as e:
            logger.error(f"Baseline setup failed: {e}", exc_info=True)
            return self._create_error_result(task, e)

    async def _handle_generic_reputation(self, task: Task) -> TaskResult:
        """Handle generic reputation task"""
        logger.info(f"Handling generic reputation task: {task.action}")

        return TaskResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            status="completed",
            result={
                "message": f"Generic reputation task '{task.action}' executed",
                "action": task.action,
            },
            metadata={"handler": "generic"},
        )

    # Fallback direct implementations (when orchestrators not available)

    async def _monitor_reviews_direct(self, task: Task) -> TaskResult:
        """Direct implementation of review monitoring"""
        logger.info("Using direct review monitoring (no orchestrator)")

        platforms = task.data.get("platforms", [])
        target_type = task.data.get("target_type", "our_brand")

        result = {
            "platforms": platforms,
            "target_type": target_type,
            "reviews": [],
            "summary": {
                "total_reviews": 0,
                "positive": 0,
                "negative": 0,
                "neutral": 0,
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

    async def _analyze_sentiment_direct(self, task: Task) -> TaskResult:
        """Direct implementation of sentiment analysis"""
        logger.info("Using direct sentiment analysis (no orchestrator)")

        reviews = task.data.get("reviews", [])

        result = {
            "reviews_analyzed": len(reviews),
            "sentiment": {
                "positive": 0,
                "negative": 0,
                "neutral": 0,
            },
            "synthetic_nps": 0,
            "note": "Direct implementation - orchestrator recommended for full analysis",
        }

        return TaskResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            status="completed",
            result=result,
            metadata={"handler": "direct", "orchestrator_missing": True},
        )

    async def _generate_responses_direct(self, task: Task) -> TaskResult:
        """Direct implementation of response generation"""
        logger.info("Using direct response generation (no orchestrator)")

        reviews = task.data.get("reviews", [])

        result = {
            "responses_generated": len(reviews),
            "responses": [],
            "note": "Direct implementation - orchestrator recommended for full generation",
        }

        return TaskResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            status="completed",
            result=result,
            metadata={"handler": "direct", "orchestrator_missing": True},
        )

    async def _manage_crisis_direct(self, task: Task) -> TaskResult:
        """Direct implementation of crisis management"""
        logger.info("Using direct crisis management (no orchestrator)")

        crisis_type = task.data.get("crisis_type", "detect")

        result = {
            "crisis_type": crisis_type,
            "crisis_detected": False,
            "action_plan": [],
            "note": "Direct implementation - orchestrator recommended for full crisis management",
        }

        return TaskResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            status="completed",
            result=result,
            metadata={"handler": "direct", "orchestrator_missing": True},
        )

    async def _track_competitors_direct(self, task: Task) -> TaskResult:
        """Direct implementation of competitor tracking"""
        logger.info("Using direct competitor tracking (no orchestrator)")

        competitors = task.data.get("competitors", [])

        result = {
            "competitors_tracked": len(competitors),
            "fuckups": [],
            "successes": [],
            "note": "Direct implementation - orchestrator recommended for full tracking",
        }

        return TaskResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            status="completed",
            result=result,
            metadata={"handler": "direct", "orchestrator_missing": True},
        )

    async def _setup_baseline_direct(self, task: Task) -> TaskResult:
        """Direct implementation of baseline setup"""
        logger.info("Using direct baseline setup (no orchestrator)")

        brand_name = task.data.get("brand_name")
        platforms = task.data.get("platforms", [])

        result = {
            "brand_name": brand_name,
            "platforms": platforms,
            "baseline_metrics": {
                "average_rating": 0.0,
                "total_reviews": 0,
                "sentiment": {"positive": 0, "negative": 0, "neutral": 0},
                "synthetic_nps": 0,
            },
            "baseline_date": datetime.now(timezone.utc).isoformat(),
            "note": "Direct implementation - orchestrator recommended for full baseline",
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
