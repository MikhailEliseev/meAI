"""Контур.Диадок Polling Service

Контур.Диадок does NOT support webhooks. This service polls GetNewEvents (V8)
to detect document status changes. Replaces KontourWebhookHandler.

Strategy:
- 30s interval during active documents
- Exponential backoff to 5min when idle

Part of: Phase 12-02 — Контур.Диадок integration
"""

from __future__ import annotations

import asyncio
from typing import Callable, Awaitable

import httpx
import structlog

logger = structlog.get_logger()

EventHandler = Callable[[dict], Awaitable[None]]


class KontourPoller:
    """Polls Контур.Диадок GetNewEvents (V8) for document status changes."""

    def __init__(
        self,
        auth,
        api_url: str = "https://diadoc-api.kontur.ru",
        organization_box_id: str = "",
        poll_interval: float = 30.0,
        idle_interval: float = 300.0,
        idle_after_cycles: int = 5,
    ):
        self.auth = auth
        self.api_url = api_url
        self.organization_box_id = organization_box_id
        self.poll_interval = poll_interval
        self.idle_interval = idle_interval
        self.idle_after_cycles = idle_after_cycles
        self._index_key: str = ""
        self._running = False
        self._task: asyncio.Task | None = None
        self._client = httpx.AsyncClient(timeout=30.0)
        self._handlers: dict[str, EventHandler] = {}
        self._empty_cycles = 0

    def on_event(self, event_type: str) -> Callable:
        """Decorator to register event handler."""
        def decorator(func: EventHandler) -> EventHandler:
            self._handlers[event_type] = func
            return func
        return decorator

    async def start(self) -> None:
        """Start polling loop."""
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("kontour_poller_started", interval=self.poll_interval)

    async def stop(self) -> None:
        """Stop polling loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self._client.aclose()
        logger.info("kontour_poller_stopped")

    async def _poll_loop(self) -> None:
        """Main polling loop — call GetNewEvents, dispatch to handlers."""
        while self._running:
            try:
                token = await self.auth.get_token()
                params = {"boxId": self.organization_box_id}
                if self._index_key:
                    params["afterIndexKey"] = self._index_key

                events_response = await self._client.get(
                    f"{self.api_url}/V8/GetNewEvents",
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                )
                events_response.raise_for_status()
                events = events_response.json()

                if events.get("TotalCount", 0) > 0:
                    self._empty_cycles = 0
                    for event in events.get("Events", []):
                        event_type = event.get("EventType", "")
                        handler = self._handlers.get(event_type)
                        if handler:
                            await handler(event)
                        else:
                            logger.debug(
                                "kontour_unhandled_event", event_type=event_type
                            )
                    self._index_key = events.get("NextIndexKey", self._index_key)
                else:
                    self._empty_cycles += 1

                if self._empty_cycles >= self.idle_after_cycles:
                    await asyncio.sleep(self.idle_interval)
                else:
                    await asyncio.sleep(self.poll_interval)

            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error("kontour_poll_error", error=str(e))
                await asyncio.sleep(self.poll_interval)
