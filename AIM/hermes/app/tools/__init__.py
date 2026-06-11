"""
AIM Operations Tools — Hermes toolset "aim-operations"

Registered via Hermes internal tool registry (tools/registry.py), NOT MCP stdio.
See RESEARCH.md Pitfall 5: internal registry tools are available to AIAgent when
enabled_toolsets=["aim-operations"] is set. MCP server mode (hermes mcp serve)
is for EXTERNAL MCP clients only.

All handlers make real HTTP calls to AIM API via internal Docker network (D-14, D-15).
AIM_API_BASE = "http://app:8000"
"""

import logging

logger = logging.getLogger(__name__)


def register_all_tools() -> None:
    """Register all AIM operation tools in the Hermes registry.

    Called once at FastAPI app startup. Each tool module imports itself
    and calls registry.register() at module level, so importing them
    here is sufficient to register.

    UNIFIED TOOL (replaces 16 individual tools):
    - orchestrate           -> POST http://app:8000/api/hermes/orchestrate

    Legacy tools (kept for backward compatibility):
    - run_seo_audit        -> POST http://app:8000/api/seo/audit
    - run_content_analysis -> POST http://app:8000/api/content/analyze
    - run_ads_report       -> POST http://app:8000/api/ads/report
    - show_project_status  -> GET  http://app:8000/api/projects/{project_id}/status
    - collect_contact      -> POST http://app:8000/api/leads
    - show_all_leads       -> GET  http://app:8000/api/leads
    - qualify_lead         -> POST http://app:8000/api/sales/qualify
    - escalate_to_manager  -> POST http://app:8000/api/sales/escalate
    - get_lead_pipeline    -> GET  http://app:8000/api/sales/pipeline
    - update_knowledge     -> PUT  http://app:8000/api/sales/knowledge/update
    - run_prescan          -> POST http://app:8000/api/presale/prescan
    - find_competitors     -> POST http://app:8000/api/competitors/find
    - present_competitors  -> POST http://app:8000/api/competitors/save
    - run_ci_analysis      -> POST http://app:8000/api/competitors/analyze
    - find_company_financials -> GET http://app:8000/api/companies/financials
    - send_telegram_file   -> Bot API sendDocument/sendPhoto
    """
    # Unified orchestrator — PRIMARY tool
    from . import orchestrate           # noqa: F401

    # Legacy tools — kept for backward compatibility
    from . import run_seo_audit          # noqa: F401
    from . import run_content_analysis   # noqa: F401
    from . import run_ads_report         # noqa: F401
    from . import show_project_status    # noqa: F401
    from . import collect_contact        # noqa: F401
    from . import show_all_leads         # noqa: F401
    from . import qualify_lead           # noqa: F401
    from . import escalate_to_manager    # noqa: F401
    from . import get_lead_pipeline      # noqa: F401
    from . import update_knowledge       # noqa: F401
    from . import run_prescan          # noqa: F401
    from . import find_competitors       # noqa: F401
    from . import present_competitors    # noqa: F401
    from . import run_ci_analysis        # noqa: F401
    from . import find_company_financials # noqa: F401
    from . import send_telegram_file     # noqa: F401
    from . import telegram_tools         # noqa: F401  # send_message_as_user, search_chats, bind_chat, list_chats
    from . import geo_optimizer_tools    # noqa: F401  # run_geo_audit

    logger.info("Registered 20 AIM operations tools: orchestrate + 19 tools")


def register_debug_tools() -> None:
    """Register Hermes debug tools — shell_exec, file_read, api_debug, file_write,
    pip_install, restart_myself, web_fetch, web_search, browser_screenshot, call_api,
    bitrix_scrape.

    Toolset "hermes-debug" gives Hermes full access to the container
    for self-diagnostics, web access, package management, browser automation, and self-restart.
    """
    from . import shell_exec  # noqa: F401
    from . import web_scraper  # noqa: F401
    from . import external_api  # noqa: F401
    from . import bitrix_scraper  # noqa: F401
    from . import firecrawl_web  # noqa: F401
    logger.info("Registered 15 debug tools: shell_exec, file_read, api_debug, file_write, pip_install, restart_myself, web_fetch, web_search, browser_screenshot, call_api, bitrix_scrape, firecrawl_scrape, firecrawl_search, firecrawl_crawl, firecrawl_map")


__all__ = ["register_all_tools", "register_debug_tools"]
