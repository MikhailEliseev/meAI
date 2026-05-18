"""Query profiling middleware — logs slow database queries.

Adds timing to SQLAlchemy queries and exposes slow-query log.
"""

import time
from collections import defaultdict

from sqlalchemy import event
from sqlalchemy.engine import Engine


class QueryProfiler:
    """Collects query execution statistics.

    Hooks into SQLAlchemy engine events to capture timing.
    """

    def __init__(self, slow_query_threshold_ms: float = 100.0):
        self.slow_query_threshold = slow_query_threshold_ms
        self._total_queries = 0
        self._total_time_ms = 0.0
        self._slow_queries: list[dict] = []

    def reset(self) -> None:
        self._total_queries = 0
        self._total_time_ms = 0.0
        self._slow_queries.clear()

    @property
    def stats(self) -> dict:
        return {
            "total_queries": self._total_queries,
            "total_time_ms": round(self._total_time_ms, 2),
            "avg_time_ms": round(self._total_time_ms / max(self._total_queries, 1), 2),
            "slow_queries": len(self._slow_queries),
        }

    def _before_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        conn._aim_query_start = time.monotonic()

    def _after_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        elapsed = (time.monotonic() - conn._aim_query_start) * 1000
        self._total_queries += 1
        self._total_time_ms += elapsed

        if elapsed > self.slow_query_threshold:
            self._slow_queries.append({
                "statement": str(statement)[:200],
                "params": str(parameters)[:200] if parameters else None,
                "elapsed_ms": round(elapsed, 2),
            })

    def attach(self, engine: Engine) -> None:
        event.listen(engine, "before_cursor_execute", self._before_cursor_execute)
        event.listen(engine, "after_cursor_execute", self._after_cursor_execute)


# Global profiler instance
_profiler: QueryProfiler | None = None


def get_profiler() -> QueryProfiler:
    global _profiler
    if _profiler is None:
        _profiler = QueryProfiler()
    return _profiler


class QueryProfilingMiddleware:
    """ASGI middleware for query profiling per request."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        profiler = get_profiler()
        profiler.reset()

        start = time.monotonic()
        await self.app(scope, receive, send)
        total_ms = (time.monotonic() - start) * 1000

        if profiler._slow_queries:
            import logging
            logger = logging.getLogger("aim.performance")
            logger.warning(
                "slow_request",
                extra={
                    "path": scope.get("path", ""),
                    "total_ms": round(total_ms, 2),
                    "query_stats": profiler.stats,
                    "slow_queries": profiler._slow_queries,
                },
            )
