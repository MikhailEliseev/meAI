"""Timeout manager - enforce operation timeouts"""

import asyncio
from typing import Any, Coroutine, TypeVar, Optional
import structlog

logger = structlog.get_logger()

T = TypeVar("T")


class TimeoutManager:
    """Manage operation timeouts with graceful cancellation"""

    def __init__(self, default_timeout: float = 300.0):  # 5 minutes default
        """Initialize Timeout Manager

        Args:
            default_timeout: Default timeout in seconds
        """
        self.default_timeout = default_timeout
        self.active_operations: dict[str, asyncio.Task] = {}

    async def run_with_timeout(
        self,
        coro: Coroutine[Any, Any, T],
        timeout: Optional[float] = None,
        operation_id: Optional[str] = None,
    ) -> T:
        """Run coroutine with timeout

        Args:
            coro: Coroutine to run
            timeout: Timeout in seconds (uses default if None)
            operation_id: Optional operation identifier for logging

        Returns:
            Result of the coroutine

        Raises:
            asyncio.TimeoutError: If operation exceeds timeout
        """
        timeout = timeout or self.default_timeout

        if operation_id:
            logger.info(
                "timeout.operation_started",
                operation_id=operation_id,
                timeout=timeout,
            )

        try:
            result = await asyncio.wait_for(coro, timeout=timeout)

            if operation_id:
                logger.info("timeout.operation_completed", operation_id=operation_id)

            return result

        except asyncio.TimeoutError:
            if operation_id:
                logger.error(
                    "timeout.operation_exceeded",
                    operation_id=operation_id,
                    timeout=timeout,
                )
            raise

        finally:
            if operation_id and operation_id in self.active_operations:
                del self.active_operations[operation_id]

    async def run_with_timeout_tracked(
        self,
        coro: Coroutine[Any, Any, T],
        operation_id: str,
        timeout: Optional[float] = None,
    ) -> T:
        """Run coroutine with timeout and track it

        Args:
            coro: Coroutine to run
            operation_id: Operation identifier
            timeout: Timeout in seconds (uses default if None)

        Returns:
            Result of the coroutine

        Raises:
            asyncio.TimeoutError: If operation exceeds timeout
        """
        task = asyncio.create_task(coro)
        self.active_operations[operation_id] = task

        try:
            return await self.run_with_timeout(
                task,
                timeout=timeout,
                operation_id=operation_id,
            )
        except asyncio.TimeoutError:
            # Cancel the task
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            raise

    async def cancel_operation(self, operation_id: str) -> None:
        """Cancel a tracked operation

        Args:
            operation_id: Operation identifier
        """
        if operation_id not in self.active_operations:
            logger.warning("timeout.operation_not_found", operation_id=operation_id)
            return

        task = self.active_operations[operation_id]
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            logger.info("timeout.operation_cancelled", operation_id=operation_id)

        # Remove from active operations if still there
        if operation_id in self.active_operations:
            del self.active_operations[operation_id]

    async def cancel_all(self) -> None:
        """Cancel all active operations"""
        operation_ids = list(self.active_operations.keys())

        for operation_id in operation_ids:
            await self.cancel_operation(operation_id)

        logger.info("timeout.all_cancelled", count=len(operation_ids))

    def get_active_operations(self) -> list[str]:
        """Get list of active operation IDs

        Returns:
            List of operation IDs
        """
        return list(self.active_operations.keys())
