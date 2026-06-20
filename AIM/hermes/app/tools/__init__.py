"""
AIM Operations Tools — Hermes toolset "aim-operations"

Registered via Hermes internal tool registry (tools/registry.py), NOT MCP stdio.
See RESEARCH.md Pitfall 5: internal registry tools are available to AIAgent when
enabled_toolsets=["aim-operations"] is set. MCP server mode (hermes mcp serve)
is for EXTERNAL MCP clients only.

All handlers make real HTTP calls to AIM API via internal Docker network (D-14, D-15).
AIM_API_BASE = "http://aim-app:8000"
"""

import logging

logger = logging.getLogger(__name__)


def _import_tool(module_name: str) -> bool:
    """Import a tool module by name. Returns True on success, logs and returns False on error."""
    try:
        __import__(f"app.tools.{module_name}", fromlist=[module_name])
        return True
    except Exception as e:
        logger.error(f"Failed to import tool {module_name}: {e}")
        return False


def register_all_tools() -> None:
    """Register all AIM operation tools in the Hermes registry.

    Called once at FastAPI app startup.
    Each tool module registers itself via registry.register() at module level.
    Imports are wrapped so one broken tool doesn't kill the rest.
    """

    count_before = len(_get_registry_tools())
    logger.info(f"Tools before registration: {count_before}")

    # === Phase 0: Prelude (2 tools) ===
    _import_tool("orchestrate")
    _import_tool("quick_overview")

    # === Phase 1: Discovery / Scout (10 tools) ===
    _import_tool("run_prescan")
    _import_tool("run_aim_scout")
    _import_tool("run_full_scout")
    _import_tool("run_background_pipeline")
    _import_tool("run_validation_check")
    _import_tool("quality_gate")
    _import_tool("service_categorizer")
    _import_tool("run_web_search")
    _import_tool("find_company_financials")
    _import_tool("telegram_tools")

    # === Phase 2: Competitive Intelligence (11 tools) ===
    _import_tool("find_competitors")
    _import_tool("present_competitors")
    _import_tool("run_ci_analysis")
    _import_tool("run_seo_audit")
    _import_tool("run_content_analysis")
    _import_tool("run_content_gaps")
    _import_tool("run_ads_report")
    _import_tool("run_ads_intelligence")
    _import_tool("run_pagespeed")
    _import_tool("run_review_platforms")
    _import_tool("run_smi_mentions")

    # === Phase 3: People & Content (5 tools) ===
    _import_tool("run_hh_analysis")
    _import_tool("run_doctor_dossiers")
    _import_tool("run_instagram_content")
    _import_tool("geo_optimizer_tools")
    _import_tool("finalize_research")

    # === Phase 3.5: Report Generation (2 tools) ===
    _import_tool("publish_scout_report")
    _import_tool("generate_html_report")

    # === Sales / CRM (8 tools) ===
    _import_tool("collect_contact")
    _import_tool("qualify_lead")
    _import_tool("escalate_to_manager")
    _import_tool("show_all_leads")
    _import_tool("get_lead_pipeline")
    _import_tool("show_project_status")
    _import_tool("update_knowledge")
    _import_tool("send_telegram_file")

    count_after = len(_get_registry_tools())
    logger.info(
        f"Registered {count_after} AIM operations tools "
        f"(+{count_after - count_before} new)"
    )


def _get_registry_tools():
    """Get the internal _tools dict from the framework registry."""
    from tools.registry import registry
    return registry._tools


def register_debug_tools() -> None:
    """Register Hermes debug tools."""
    _import_tool("shell_exec")
    _import_tool("web_scraper")
    _import_tool("external_api")
    _import_tool("bitrix_scraper")
    _import_tool("firecrawl_web")
    logger.info("Registered 15 debug tools")


__all__ = ["register_all_tools", "register_debug_tools"]
