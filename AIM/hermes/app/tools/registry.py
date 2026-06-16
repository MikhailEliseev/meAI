"""Hermes internal tool registry — minimal stub for test execution.

In production, this would be the full Hermes tool registration system.
For unit testing generate_html_report.py, we need a registry singleton
with a .register() method that the module calls at module level.
"""


class _Registry:
    """Stub registry singleton for test execution."""

    def __init__(self):
        self._tools: dict = {}

    def register(self, name: str, toolset: str = "", schema: dict = None,
                 handler=None, check_fn=None, is_async: bool = False,
                 description: str = "", emoji: str = ""):
        """Register a tool in the Hermes registry."""
        self._tools[name] = {
            "toolset": toolset,
            "schema": schema,
            "handler": handler,
            "check_fn": check_fn,
            "is_async": is_async,
            "description": description,
            "emoji": emoji,
        }


registry = _Registry()
