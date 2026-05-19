"""AIAgent wrapper — session management + sync-to-async adapter.

Per Pitfall 2: SQLite session DB needs per-session serialization to avoid
"database is locked" errors. asyncio.Lock per session_id.

Per Pitfall 7: AIAgent.run_conversation() is SYNCHRONOUS (returns Dict[str, Any]).
Must wrap in loop.run_in_executor() for FastAPI async endpoints.
"""

import asyncio
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Per-session locks to serialize concurrent requests (Pitfall 2)
_session_locks: dict[str, asyncio.Lock] = {}

OMNIROUTE_URL = os.getenv("OMNIROUTE_URL", "http://138.16.224.188:20128/v1")
OMNIROUTE_AUTH = os.getenv("OMNIROUTE_AUTH", "sk-a10f604cd99e7a50-dd1d5a-56e30050")
DEFAULT_MODEL = os.getenv("HERMES_MODEL", "deepseek/deepseek-v4-pro")


def get_session_lock(session_id: str) -> asyncio.Lock:
    """Get or create a per-session asyncio.Lock for SQLite concurrency safety."""
    if session_id not in _session_locks:
        _session_locks[session_id] = asyncio.Lock()
    return _session_locks[session_id]


def get_mode_prompt(mode: str) -> str:
    """Return ephemeral_system_prompt based on mode (D-26).

    Next.js determines mode from client status in DB and passes it in
    X-Client-Mode header. Hermes trusts this header (D-26, D-28).
    """
    prompts = {
        "PRESALE": (
            "You are in PRESALE mode. Task: demonstrate WOW data in 2-3 minutes, "
            "collect contact information. You are the first touchpoint for potential clients. "
            "Focus on 3 numbers: patients per month, timeline, cost per patient. "
            "Use run_seo_audit to analyze the website and collect_contact to save the lead."
        ),
        "ACTIVE": (
            "You are in ACTIVE PROJECT mode. Task: respond to client about their project, "
            "show KPIs, provide status updates, escalate issues to Mikhail. "
            "Use show_project_status to get current project data. "
            "Use run_seo_audit, run_content_analysis, run_ads_report for specific reports."
        ),
        "ADMIN": (
            "You are in ADMIN mode. Full system access. You are communicating with "
            "Mikhail Eliseev (agency founder). Be direct and data-driven. "
            "Use show_all_leads to view lead pipeline. "
            "Use show_project_status for any project. Discuss system architecture if needed."
        ),
    }
    return prompts.get(mode, prompts["PRESALE"])


async def run_agent(
    message: str,
    session_id: str | None = None,
    mode: str = "PRESALE",
) -> dict:
    """Run AIAgent.conversation (sync) in executor thread and return result.

    Per Pitfall 7: AIAgent.run_conversation() is synchronous.
    Wrapping in run_in_executor keeps FastAPI event loop free.

    Per Pitfall 2: per-session asyncio.Lock prevents SQLite concurrency errors.

    OmniRoute uses OpenAI-compatible API at /v1 — provider="custom" + api_mode="openai_chat".
    """
    from run_agent import AIAgent

    lock = get_session_lock(session_id or "new")

    async with lock:
        loop = asyncio.get_running_loop()

        def _run_sync():
            agent = AIAgent(
                base_url=OMNIROUTE_URL,
                api_key=OMNIROUTE_AUTH,
                provider="custom",
                api_mode="openai_chat",
                model=DEFAULT_MODEL,
                session_id=session_id,
                load_soul_identity=True,
                ephemeral_system_prompt=get_mode_prompt(mode),
                enabled_toolsets=["aim-operations"],
                max_iterations=15,
                quiet_mode=True,
            )
            response = agent.run_conversation(message)
            return {
                "reply": response.get("response", response.get("content", str(response))),
                "session_id": agent.session_id,
                "tool_calls": response.get("tool_calls", []),
            }

        return await loop.run_in_executor(None, _run_sync)
