"""SharedEventBus — singleton EventBus for the entire AIM application.

Replaces per-request EventBus creation (e.g., _get_orchestrator in seo.py).
Initialized once at app startup, shared by all Magisters and the HermesOrchestrator.

Usage:
    from src.aim.orchestration.shared_event_bus import get_shared_event_bus

    bus = await get_shared_event_bus()
    await bus.publish(event)
"""

from __future__ import annotations

import asyncio
import logging
import os

from meai.events.event_bus import EventBus

logger = logging.getLogger("aim.orchestration.shared_event_bus")

_shared_bus: EventBus | None = None
_init_lock = asyncio.Lock()


async def get_shared_event_bus() -> EventBus:
    """Get or create the shared EventBus singleton."""
    global _shared_bus
    if _shared_bus is not None:
        return _shared_bus

    async with _init_lock:
        if _shared_bus is not None:
            return _shared_bus

        database_url = os.getenv(
            "DATABASE_URL", "sqlite+aiosqlite:///./data/aim.db"
        )
        _shared_bus = EventBus(database_url=database_url)
        await _shared_bus.initialize()
        logger.info("SharedEventBus initialized")
        return _shared_bus


async def shutdown_shared_event_bus() -> None:
    """Close the shared EventBus."""
    global _shared_bus
    if _shared_bus is not None:
        await _shared_bus.close()
        _shared_bus = None
        logger.info("SharedEventBus shut down")


def _reset_shared_event_bus() -> None:
    """Reset the singleton (for testing only)."""
    global _shared_bus
    _shared_bus = None
