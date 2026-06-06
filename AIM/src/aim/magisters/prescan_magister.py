"""PrescanMagister — wraps PrescanOrchestrator as a proper Magister.

Extends BaseMagister pattern. Internally delegates to the existing
PrescanOrchestrator.prescan_staged() — no changes to PrescanOrchestrator.

Publishes prescan events via EventBus:
    prescan.stage.completed — after each stage (1, 2, 3)
    prescan.completed       — final aggregated result
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from meai.agents.magister_base import BaseMagister

logger = logging.getLogger("aim.magisters.prescan")


class PrescanMagister(BaseMagister):
    """Magister wrapper around PrescanOrchestrator.

    Usage:
        magister = PrescanMagister(
            magister_id="prescan-1",
            database_url="...",
            event_bus=shared_bus,
        )
        await magister.initialize()
        result = await magister.run_prescan("https://clinic.ru")
    """

    def __init__(
        self,
        magister_id: str = "prescan-magister",
        database_url: str = "",
        vault_path: str = "./AIM/obsidian",
        event_bus=None,
    ):
        super().__init__(
            magister_id=magister_id,
            database_url=database_url,
            vault_path=vault_path,
        )
        if event_bus is not None:
            self.event_bus = event_bus

    async def identify_subagents(self, action: str) -> list[str]:
        """Prescan doesn't use subagents — it's a monolithic pipeline."""
        return []

    async def aggregate_results(self, subagent_results: list[dict]) -> dict:
        """Prescan aggregates stages internally — pass-through."""
        return {"summary": "Prescan results aggregated by PrescanOrchestrator"}

    async def run_prescan(
        self,
        url: str,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        """Run 3-stage prescan via existing PrescanOrchestrator.

        Args:
            url: Client clinic website URL.
            force_refresh: Skip CompanyProfileModel cache.

        Returns:
            Dict with stage_1, stage_2, stage_3 and optional _errors.
        """
        from src.aim.services.prescan_orchestrator import PrescanOrchestrator

        async def _publish_stage(stage: int, name: str, data: dict, is_final: bool):
            """Publish stage completion to EventBus."""
            try:
                from meai.events.event_bus import Event

                await self.event_bus.publish(Event(
                    event_type="prescan.stage.completed",
                    payload={
                        "magister_id": self.magister_id,
                        "url": url,
                        "stage": stage,
                        "stage_name": name,
                        "is_final": is_final,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                ))
            except Exception:
                logger.debug("EventBus publish skipped (not initialized)")

        orchestrator = PrescanOrchestrator()
        try:
            result = await orchestrator.prescan_staged(
                url=url,
                progress_callback=_publish_stage,
                force_refresh=force_refresh,
            )

            # Publish completion event
            try:
                from meai.events.event_bus import Event

                await self.event_bus.publish(Event(
                    event_type="prescan.completed",
                    payload={
                        "magister_id": self.magister_id,
                        "url": url,
                        "has_errors": bool(result.get("_errors")),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                ))
            except Exception:
                pass

            return result
        finally:
            await orchestrator.close()
