"""Researcher Agent for multi-source knowledge collection"""

import json
from datetime import datetime, timezone
from typing import Any

from meai.agents.base_agent import Agent, Task, TaskResult
from meai.integrations.perplexity import PerplexityClient
from meai.integrations.youtube import YouTubeClient
from meai.integrations.telegram import TelegramClient


class ResearcherAgent(Agent):
    """Researcher Agent for collecting knowledge from multiple sources

    Capabilities:
    - research_topic: Deep research via Perplexity API
    - monitor_youtube: Monitor YouTube channels for new content
    - monitor_telegram: Monitor Telegram channels for messages
    - validate_source: Evaluate source quality and trustworthiness
    """

    def __init__(
        self,
        agent_id: str = "researcher",
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        vault_path: str = "./obsidian",
        perplexity_api_key: str | None = None,
        youtube_api_key: str | None = None,
        telegram_api_id: str | None = None,
        telegram_api_hash: str | None = None,
    ):
        """Initialize Researcher Agent

        Args:
            agent_id: Agent identifier
            database_url: Database connection URL
            vault_path: Path to Obsidian vault
            perplexity_api_key: Perplexity API key
            youtube_api_key: YouTube API key
            telegram_api_id: Telegram API ID
            telegram_api_hash: Telegram API hash
        """
        super().__init__(
            agent_id=agent_id,
            agent_type="researcher",
            database_url=database_url,
            vault_path=vault_path,
        )

        # Initialize API clients
        self.perplexity = (
            PerplexityClient(api_key=perplexity_api_key)
            if perplexity_api_key
            else None
        )
        self.youtube = (
            YouTubeClient(api_key=youtube_api_key) if youtube_api_key else None
        )
        self.telegram = TelegramClient() if telegram_api_id and telegram_api_hash else None
        self.telegram_api_id = telegram_api_id
        self.telegram_api_hash = telegram_api_hash

        # Trusted domains for source validation
        self.trusted_domains = [
            "moz.com",
            "google.com",
            "searchengineland.com",
            "semrush.com",
            "ahrefs.com",
        ]

    def get_capabilities(self) -> list[str]:
        """Get list of researcher capabilities

        Returns:
            List of action names
        """
        return [
            "research_topic",
            "monitor_youtube",
            "monitor_telegram",
            "validate_source",
        ]

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute research task

        Args:
            task: Task to execute

        Returns:
            Task result with findings
        """
        start_time = datetime.now(timezone.utc)

        try:
            if task.action == "research_topic":
                result = await self._research_topic(task)
            elif task.action == "monitor_youtube":
                result = await self._monitor_youtube(task)
            elif task.action == "monitor_telegram":
                result = await self._monitor_telegram(task)
            elif task.action == "validate_source":
                result = await self._validate_source(task)
            else:
                raise ValueError(f"Unknown action: {task.action}")

            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()

            return TaskResult(
                subtask_id=task.subtask_id,
                agent_id=self.agent_id,
                action=task.action,
                status="success",
                result=result,
                error=None,
                duration_seconds=duration,
                completed_at=end_time,
            )

        except Exception as e:
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()

            return TaskResult(
                subtask_id=task.subtask_id,
                agent_id=self.agent_id,
                action=task.action,
                status="failed",
                result={},
                error=str(e),
                duration_seconds=duration,
                completed_at=end_time,
            )

    async def _research_topic(self, task: Task) -> dict[str, Any]:
        """Research topic using Perplexity

        Args:
            task: Task with research query in description

        Returns:
            Research findings with content and sources
        """
        if not self.perplexity:
            raise RuntimeError("Perplexity API key not configured")

        # Extract query from task description
        query = task.description

        # Perform research
        findings = await self.perplexity.research(query)

        return {
            "query": query,
            "content": findings["content"],
            "sources": findings["sources"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _monitor_youtube(self, task: Task) -> dict[str, Any]:
        """Monitor YouTube channel for new videos

        Args:
            task: Task with channel ID in description

        Returns:
            List of recent videos
        """
        if not self.youtube:
            raise RuntimeError("YouTube API key not configured")

        # Extract channel ID from task description
        channel_id = task.description.split()[-1]  # Assume last word is channel ID

        # Get recent videos
        videos = await self.youtube.get_channel_videos(channel_id, max_results=10)

        return {
            "channel_id": channel_id,
            "videos": videos,
            "count": len(videos),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _monitor_telegram(self, task: Task) -> dict[str, Any]:
        """Monitor Telegram channel for new messages

        Args:
            task: Task with channel username in description

        Returns:
            List of recent messages
        """
        if not self.telegram:
            raise RuntimeError("Telegram API credentials not configured")

        # Connect if not connected
        if not self.telegram.connected:
            await self.telegram.connect(
                api_id=self.telegram_api_id, api_hash=self.telegram_api_hash
            )

        # Extract channel from task description
        channel = task.description.split()[-1]  # Assume last word is channel

        # Get recent messages
        messages = await self.telegram.get_channel_messages(channel, limit=50)

        return {
            "channel": channel,
            "messages": messages,
            "count": len(messages),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _validate_source(self, task: Task) -> dict[str, Any]:
        """Validate source quality and trustworthiness

        Args:
            task: Task with source URL in description

        Returns:
            Source validation result
        """
        # Extract URL from task description
        url = task.description.split()[-1]  # Assume last word is URL

        # Simple validation based on trusted domains
        domain = url.split("//")[-1].split("/")[0]
        is_trusted = any(trusted in domain for trusted in self.trusted_domains)

        # Calculate quality score (0-100)
        quality_score = 90 if is_trusted else 50

        return {
            "url": url,
            "domain": domain,
            "is_trusted": is_trusted,
            "quality_score": quality_score,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
