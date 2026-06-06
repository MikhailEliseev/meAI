"""KnowledgeBridge — connects Hermes learnings to AIM's AgentLearning system.

Bridges the gap between:
  - Hermes auto-learnings  → /opt/data/memories/learnings/
  - Hermes teacher reports → hermes/knowledge/learnings/
  - AIM AgentLearning     → obsidian/architect/wiki/lessons/
  - HermesKnowledgeVault  → hermes/knowledge/

Two-way sync via EventBus subscriptions:
  Hermes → AIM: auto-learnings and teacher reports → Obsidian lessons/
  AIM → Hermes: magister execution results → HermesKnowledgeVault

Usage:
    bridge = KnowledgeBridge(event_bus=shared_bus)
    await bridge.start()
    # ... magisters run, events flow ...
    await bridge.stop()
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("aim.orchestration.knowledge_bridge")


class KnowledgeBridge:
    """Bridges Hermes and AIM knowledge systems via EventBus."""

    def __init__(
        self,
        event_bus=None,
        hermes_memories_path: str = "/opt/data/memories/learnings",
        hermes_knowledge_path: str = "AIM/hermes/knowledge",
        aim_lessons_path: str = "obsidian/architect/wiki/lessons",
    ):
        self._event_bus = event_bus
        self._hermes_memories = Path(hermes_memories_path)
        self._hermes_knowledge = Path(hermes_knowledge_path)
        self._aim_lessons = Path(aim_lessons_path)
        self._subscribed = False

    async def start(self) -> None:
        """Subscribe to EventBus events relevant to knowledge sync."""
        if self._event_bus is None:
            logger.info("KnowledgeBridge: no EventBus, running in passive mode")
            return

        await self._event_bus.subscribe(
            "prescan.completed",
            self._on_prescan_completed,
        )
        await self._event_bus.subscribe(
            "seo.analysis.completed",
            self._on_seo_completed,
        )
        await self._event_bus.subscribe(
            "ci.execution.completed",
            self._on_ci_completed,
        )
        self._subscribed = True
        logger.info("KnowledgeBridge: subscribed to prescan, seo, ci events")

        # Initial sync: pull existing Hermes learnings into AIM
        await self.sync_hermes_to_aim()

    async def stop(self) -> None:
        """Unsubscribe from EventBus."""
        if self._event_bus and self._subscribed:
            await self._event_bus.unsubscribe("prescan.completed", self._on_prescan_completed)
            await self._event_bus.unsubscribe("seo.analysis.completed", self._on_seo_completed)
            await self._event_bus.unsubscribe("ci.execution.completed", self._on_ci_completed)
            self._subscribed = False

    # ── Event handlers — AIM → Hermes ──────────────────────────────────

    async def _on_prescan_completed(self, event) -> None:
        """Forward prescan results to HermesKnowledgeVault."""
        try:
            from AIM.hermes.knowledge.vault import HermesKnowledgeVault

            vault = HermesKnowledgeVault(base_path=str(self._hermes_knowledge))
            await vault.ingest_execution(event)
            logger.debug("KnowledgeBridge: prescan → Hermes vault")
        except Exception as e:
            logger.debug("KnowledgeBridge: prescan sync failed: %s", e)

    async def _on_seo_completed(self, event) -> None:
        """Forward SEO results to HermesKnowledgeVault."""
        try:
            from AIM.hermes.knowledge.vault import HermesKnowledgeVault

            vault = HermesKnowledgeVault(base_path=str(self._hermes_knowledge))
            await vault.ingest_execution(event)
            logger.debug("KnowledgeBridge: seo → Hermes vault")
        except Exception as e:
            logger.debug("KnowledgeBridge: seo sync failed: %s", e)

    async def _on_ci_completed(self, event) -> None:
        """Forward CI execution results to HermesKnowledgeVault."""
        try:
            from AIM.hermes.knowledge.vault import HermesKnowledgeVault

            vault = HermesKnowledgeVault(base_path=str(self._hermes_knowledge))
            await vault.ingest_execution(event)
            logger.debug("KnowledgeBridge: ci → Hermes vault")
        except Exception as e:
            logger.debug("KnowledgeBridge: ci sync failed: %s", e)

    # ── Hermes → AIM sync ──────────────────────────────────────────────

    async def sync_hermes_to_aim(self) -> int:
        """Pull Hermes auto-learnings and teacher reports into AIM's lessons/.

        Converts markdown learnings to AgentLearning-compatible format
        with YAML frontmatter (title, date, category, severity, tags, status).

        Returns:
            Number of learnings synced.
        """
        synced = 0
        self._aim_lessons.mkdir(parents=True, exist_ok=True)

        # 1. Auto-learnings from /opt/data/memories/learnings/
        synced += self._sync_directory(
            source=self._hermes_memories,
            category="hermes-auto",
            severity="medium",
        )

        # 2. Teacher reports from hermes/knowledge/learnings/
        teacher_path = self._hermes_knowledge / "learnings"
        synced += self._sync_directory(
            source=teacher_path,
            category="teacher-report",
            severity="high",
        )

        if synced:
            logger.info("KnowledgeBridge: synced %d learnings Hermes → AIM", synced)
        return synced

    def _sync_directory(self, source: Path, category: str, severity: str) -> int:
        """Sync learnings from a directory into AIM lessons/."""
        synced = 0
        if not source.exists():
            return synced

        for md_file in source.glob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                lesson_file = self._aim_lessons / f"{category}__{md_file.name}"

                if lesson_file.exists():
                    continue  # Already synced

                # Wrap in AgentLearning-compatible frontmatter
                wrapped = self._wrap_as_lesson(
                    content=content,
                    title=md_file.stem,
                    category=category,
                    severity=severity,
                )
                lesson_file.write_text(wrapped, encoding="utf-8")
                synced += 1
            except Exception as e:
                logger.debug("KnowledgeBridge: failed to sync %s: %s", md_file, e)

        return synced

    @staticmethod
    def _wrap_as_lesson(
        content: str,
        title: str,
        category: str,
        severity: str,
    ) -> str:
        """Wrap raw markdown content as an AgentLearning-compatible lesson."""
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return f"""---
title: {title}
date: {date_str}
category: {category}
severity: {severity}
tags: [hermes, auto-learning]
status: active
---

{content}
"""
