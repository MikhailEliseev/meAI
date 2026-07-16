"""Graceful shutdown handler with cleanup"""

import asyncio
import signal
from typing import Callable, Coroutine, Any
import structlog

logger = structlog.get_logger()


class ShutdownHandler:
    """Handle graceful shutdown with cleanup"""

    def __init__(self):
        """Initialize Shutdown Handler"""
        self.cleanup_callbacks: list[Callable[[], Coroutine[Any, Any, None]]] = []
        self.shutdown_event = asyncio.Event()
        self.is_shutting_down = False

    def register_cleanup(
        self,
        callback: Callable[[], Coroutine[Any, Any, None]],
    ) -> None:
        """Register cleanup callback

        Args:
            callback: Async cleanup function to call on shutdown
        """
        self.cleanup_callbacks.append(callback)
        logger.debug("shutdown.callback_registered")

    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for SIGINT and SIGTERM"""
        loop = asyncio.get_event_loop()

        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(
                sig,
                lambda s=sig: asyncio.create_task(self._handle_signal(s)),
            )

        logger.info("shutdown.signals_registered")

    async def _handle_signal(self, sig: signal.Signals) -> None:
        """Handle shutdown signal

        Args:
            sig: Signal received
        """
        logger.info("shutdown.signal_received", signal=sig.name)
        await self.shutdown()

    async def shutdown(self) -> None:
        """Execute graceful shutdown"""
        if self.is_shutting_down:
            logger.warning("shutdown.already_in_progress")
            return

        self.is_shutting_down = True
        logger.info("shutdown.started")

        # Run cleanup callbacks
        for i, callback in enumerate(self.cleanup_callbacks):
            try:
                logger.info("shutdown.cleanup", step=i + 1, total=len(self.cleanup_callbacks))
                await callback()
            except Exception as e:
                logger.error("shutdown.cleanup_failed", step=i + 1, error=str(e))

        # Set shutdown event
        self.shutdown_event.set()

        logger.info("shutdown.completed")

    async def wait_for_shutdown(self) -> None:
        """Wait for shutdown signal"""
        await self.shutdown_event.wait()

    def is_shutdown_requested(self) -> bool:
        """Check if shutdown was requested

        Returns:
            True if shutdown was requested
        """
        return self.shutdown_event.is_set()
