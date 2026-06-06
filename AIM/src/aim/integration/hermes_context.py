"""Hermes Context Provider — Magisters query Hermes before delegating tasks.

Usage in Magister.plan_task_with_ci():

    from src.aim.integration.hermes_context import HermesContextProvider
    hermes = HermesContextProvider()
    context = await hermes.get_context(domain="seo", action="competitive_analysis")
    plan["hermes_context"] = context
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class HermesContextProvider:
    """Fetches knowledge context from Hermes before task delegation."""

    def __init__(self, hermes_url: Optional[str] = None):
        self.hermes_url = (hermes_url or
                           os.getenv("HERMES_URL", "http://localhost:8000")).rstrip("/")

    async def get_context(self, domain: str, action: str) -> dict:
        """Query Hermes for patterns/learnings/rules relevant to domain+action.

        Returns empty context on failure — Magisters must work without Hermes.
        """
        import httpx

        url = f"{self.hermes_url}/api/knowledge/context"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url, params={"domain": domain, "action": action})
                resp.raise_for_status()
                return resp.json()
        except httpx.ConnectError:
            logger.debug(f"Hermes not reachable at {self.hermes_url} — skipping context")
        except httpx.TimeoutException:
            logger.debug(f"Hermes timeout at {self.hermes_url} — skipping context")
        except Exception as e:
            logger.debug(f"Hermes context query failed: {e}")

        return {"patterns": [], "learnings": [], "rules": [], "query": f"{domain}:{action}"}

    async def enrich_task(self, domain: str, action: str, task_payload: dict) -> dict:
        """Enrich task payload with Hermes context.

        Returns modified payload with 'hermes_context' key added.
        Fails gracefully — if Hermes unavailable, task proceeds without context.
        """
        context = await self.get_context(domain, action)
        task_payload["hermes_context"] = context
        task_payload["enriched"] = bool(context.get("patterns") or context.get("learnings"))
        return task_payload
