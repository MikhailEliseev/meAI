"""Session context — thread-local storage for the current session_id.

Tools like finalize_research need the session_id but the LLM doesn't know it.
We store it in a thread-local variable that run_agent_sync sets before running
the agent, and tools read when they need it.
"""

import threading

_ctx = threading.local()


def set_current_session(session_id: str) -> None:
    """Set the session_id for the current thread."""
    _ctx.session_id = session_id


def get_current_session() -> str | None:
    """Get the session_id for the current thread, or None if not set."""
    return getattr(_ctx, "session_id", None)
