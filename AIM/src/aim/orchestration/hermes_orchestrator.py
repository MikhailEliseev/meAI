"""HermesOrchestrator — single entry point for all Hermes→AIM operations.

Replaces 16 scattered HTTP-wrapped tools with ONE unified orchestrate() method.
Each operation delegates to the appropriate Magister or service, publishes
results via shared EventBus, and returns a standardized response.

Operations:
    prescan          → PrescanOrchestrator.prescan_staged()
    seo_audit        → SEOMagister.coordinate_analysis()
    content_analysis → ContentMagister
    ads_report       → AdsMagister
    competitor_analysis → CIOrchestrator
    lead_management  → CRM pipeline
    knowledge_query  → KnowledgeBridge
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

logger = logging.getLogger("aim.orchestration.hermes")


class HermesOrchestrator:
    """Central orchestrator — Hermes's single interface to AIM.

    Hermes calls orchestrate(operation, params) → gets back structured result.
    No more 16 different HTTP wrappers for 16 different API endpoints.
    """

    def __init__(self, event_bus=None, database_url: str = ""):
        self._event_bus = event_bus
        self._database_url = database_url
        self._operations = {
            "prescan": self._handle_prescan,
            "seo_audit": self._handle_seo_audit,
            "content_analysis": self._handle_content_analysis,
            "ads_report": self._handle_ads_report,
            "competitor_analysis": self._handle_competitor_analysis,
            "lead_management": self._handle_lead_management,
            "knowledge_query": self._handle_knowledge_query,
        }

    async def orchestrate(
        self,
        operation: str,
        params: dict[str, Any],
        progress_callback=None,
    ) -> dict[str, Any]:
        """Route an operation to the appropriate handler.

        Args:
            operation: One of the registered operation names.
            params: Operation-specific parameters (url, inn, query, etc.).
            progress_callback: Optional async callable(status, message).

        Returns:
            {"status": "success"|"error", "operation": str, "result": ...}
        """
        if operation not in self._operations:
            known = ", ".join(self._operations)
            return {
                "status": "error",
                "operation": operation,
                "error": f"Unknown operation. Available: {known}",
            }

        handler = self._operations[operation]
        try:
            result = await handler(params, progress_callback)
            return {"status": "success", "operation": operation, "result": result}
        except Exception as e:
            logger.exception("Operation '%s' failed", operation)
            return {"status": "error", "operation": operation, "error": str(e)}

    # ── Operation handlers ──────────────────────────────────────────────

    async def _handle_prescan(
        self, params: dict, progress_callback=None
    ) -> dict[str, Any]:
        """Run 3-stage prescan via PrescanOrchestrator."""
        from src.aim.services.prescan_orchestrator import PrescanOrchestrator

        url = params.get("url", "")
        if not url:
            raise ValueError("url is required for prescan operation")

        force_refresh = params.get("force_refresh", False)

        orchestrator = PrescanOrchestrator()
        try:
            result = await orchestrator.prescan_staged(
                url=url,
                progress_callback=progress_callback,
                force_refresh=force_refresh,
            )
            return result
        finally:
            await orchestrator.close()

    async def _handle_seo_audit(
        self, params: dict, progress_callback=None
    ) -> dict[str, Any]:
        """Run SEO analysis via SEOMagister."""
        url = params.get("url", "")
        if not url:
            raise ValueError("url is required for seo_audit operation")

        from src.aim.magisters.seo_magister import SEOMagister

        magister = SEOMagister(timeout=params.get("timeout", 600))
        return await magister.coordinate_analysis(url=url)

    async def _handle_content_analysis(
        self, params: dict, progress_callback=None
    ) -> dict[str, Any]:
        """Run content analysis."""
        url = params.get("url", "")
        if not url:
            raise ValueError("url is required for content_analysis operation")

        try:
            from src.aim.magisters.content_magister import ContentMagister
            magister = ContentMagister()
            return await magister.coordinate_analysis(url=url)
        except ImportError:
            return {"status": "not_implemented", "message": "ContentMagister not available yet"}

    async def _handle_ads_report(
        self, params: dict, progress_callback=None
    ) -> dict[str, Any]:
        """Get ads performance report."""
        client_id = params.get("client_id", "")
        period = params.get("period", "30d")

        try:
            from src.aim.magisters.ads_magister import AdsMagister
            magister = AdsMagister()
            return await magister.get_report(client_id=client_id, period=period)
        except ImportError:
            return {"status": "not_implemented", "message": "AdsMagister not available yet"}

    async def _handle_competitor_analysis(
        self, params: dict, progress_callback=None
    ) -> dict[str, Any]:
        """Run CIOrchestrator for competitor analysis."""
        import uuid

        url = params.get("url", "")
        if not url:
            raise ValueError("url is required for competitor_analysis operation")

        competitors = params.get("competitors", [])
        niche = params.get("niche", "medical")
        tier = params.get("tier", "quick")

        from src.aim.subagents.competitive_intel.orchestrator.ci_orchestrator import CIOrchestrator
        from meai.events.event_bus import EventBus
        import os

        database_url = self._database_url or os.getenv(
            "DATABASE_URL", "sqlite+aiosqlite:///./data/aim.db"
        )
        event_bus = self._event_bus or EventBus(database_url=database_url)
        if not self._event_bus:
            await event_bus.initialize()

        orchestrator = CIOrchestrator(
            agent_id=f"hermes-orch-{uuid.uuid4().hex[:8]}",
            event_bus=event_bus,
            database_url=database_url,
            vault_path="AIM/obsidian/ci-orchestrator",
        )

        result = await orchestrator.execute_ci_analysis(
            task_data={
                "task_id": f"ci-{uuid.uuid4().hex[:8]}",
                "url": url,
                "competitors": [url] + [c for c in competitors if c != url],
                "niche": niche,
                "geo": params.get("geo", params.get("city", "")),
                "tier": tier,
            },
            progress_callback=progress_callback,
        )
        return result

    async def _handle_lead_management(
        self, params: dict, progress_callback=None
    ) -> dict[str, Any]:
        """Manage leads — collect, list, qualify."""
        action = params.get("action", "list")

        if action == "collect":
            try:
                import httpx
                async with httpx.AsyncClient(timeout=15.0) as client:
                    r = await client.post(
                        "http://localhost:8000/api/leads",
                        json=params.get("lead_data", {}),
                    )
                    r.raise_for_status()
                    return r.json()
            except Exception as e:
                return {"error": f"Lead collection failed: {e}"}

        elif action == "list":
            try:
                import httpx
                async with httpx.AsyncClient(timeout=15.0) as client:
                    r = await client.get(
                        "http://localhost:8000/api/leads",
                        params={"period": params.get("period", ""), "status": params.get("status", "")},
                    )
                    r.raise_for_status()
                    return r.json()
            except Exception as e:
                return {"error": f"Lead listing failed: {e}"}

        elif action == "qualify":
            try:
                import httpx
                async with httpx.AsyncClient(timeout=15.0) as client:
                    r = await client.post(
                        "http://localhost:8000/api/sales/qualify",
                        json=params,
                    )
                    r.raise_for_status()
                    return r.json()
            except Exception as e:
                return {"error": f"Lead qualification failed: {e}"}

        return {"error": f"Unknown lead action: {action}"}

    async def _handle_knowledge_query(
        self, params: dict, progress_callback=None
    ) -> dict[str, Any]:
        """Query AIM knowledge base."""
        query = params.get("query", "")
        domain = params.get("domain", "")

        try:
            from src.aim.integration.hermes_context import HermesContextProvider
            provider = HermesContextProvider()
            context = await provider.get_context(domain=domain or "general", action=query)
            return {"context": context}
        except ImportError:
            return {"status": "not_implemented", "message": "Knowledge query not available yet"}
        except Exception as e:
            logger.warning("Knowledge query failed: %s", e)
            return {"error": str(e)}
