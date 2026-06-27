"""
generate_report — Hermes tool: Generate & Publish Presale Report

Generates HTML report using canonical template, publishes to WordPress,
returns report URL.

Per D-16: WordPress REST API publishing via POST /wp-json/wp/v2/pages
Per D-19: Returns report URL for SSE event
"""

import json
import logging
import os
from pathlib import Path
import httpx
from tools.registry import registry

logger = logging.getLogger(__name__)

# Import the new template-based generator
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from generate_html_report import generate_report_html, sections_from_orchestrator_output

WP_API_BASE = os.getenv("WP_API_BASE", "http://wordpress:80")
WP_AUTH_USER = os.getenv("WP_AUTH_USER", "")
WP_AUTH_PASSWORD = os.getenv("WP_AUTH_PASSWORD", "")


async def handle_generate_report(
    session_hash: str,
    clinic_name: str,
    orchestrator_data: dict,
    **kwargs
) -> str:
    """Generate HTML report and publish to WordPress.

    Args:
        session_hash: 8-char session identifier
        clinic_name: Clinic name for title and slug
        orchestrator_data: Full output from 3-pass orchestrator

    Returns:
        JSON with report URL and status
    """
    try:
        # 1. Generate HTML from template
        sections = sections_from_orchestrator_output(orchestrator_data)
        output_path = Path(f"/opt/data/memories/proposals/{session_hash}/report.html")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info("Generating report for %s (session: %s)", clinic_name, session_hash)
        success = generate_report_html(clinic_name, sections, output_path)
        if not success:
            return json.dumps({"error": "Failed to generate report HTML"}, ensure_ascii=False)

        # 2. Read generated HTML
        html_content = output_path.read_text(encoding="utf-8")
        logger.info("Generated HTML: %d bytes", len(html_content))

        # 3. Publish to WordPress
        slug = clinic_name.lower().replace(" ", "-").replace(".", "-").replace("«", "").replace("»", "")
        slug = f"report-{slug}-{session_hash[:6]}"

        logger.info("Publishing to WordPress: slug=%s", slug)

        # Check if WordPress auth is configured
        if not WP_AUTH_USER or not WP_AUTH_PASSWORD:
            logger.warning("WordPress authentication not configured (WP_AUTH_USER/WP_AUTH_PASSWORD missing)")
            # Save locally but don't publish
            return json.dumps({
                "error": "WordPress authentication not configured",
                "local_path": str(output_path),
                "session_hash": session_hash,
                "status": "saved_locally"
            }, ensure_ascii=False)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{WP_API_BASE}/wp-json/wp/v2/pages",
                json={
                    "title": f"{clinic_name} — Пресейл-отчёт AIM",
                    "content": html_content,
                    "slug": slug,
                    "status": "publish",  # Public immediately
                    "meta": {
                        "session_hash": session_hash,
                        "generated_at": str(output_path.stat().st_mtime)
                    }
                },
                auth=(WP_AUTH_USER, WP_AUTH_PASSWORD)
            )
            response.raise_for_status()
            wp_data = response.json()
            report_url = wp_data.get("link", "")

            logger.info("Report published: %s", report_url)

            # 4. Push SSE event (report-ready per D-19)
            try:
                from app.main import push_report_ready
                push_report_ready(report_url, session_hash)
            except ImportError:
                logger.warning("push_report_ready not available (main.py not updated yet)")

            return json.dumps({
                "report_url": report_url,
                "session_hash": session_hash,
                "status": "published",
                "local_path": str(output_path)
            }, ensure_ascii=False)

    except httpx.HTTPStatusError as e:
        logger.error("WordPress API error: %s", e)
        error_detail = ""
        try:
            error_detail = e.response.json()
        except:
            error_detail = e.response.text[:200]
        return json.dumps({
            "error": "Failed to publish to WordPress",
            "status_code": e.response.status_code,
            "detail": str(error_detail),
            "local_path": str(output_path) if 'output_path' in locals() else None
        }, ensure_ascii=False)
    except Exception as e:
        logger.exception("Report generation failed")
        return json.dumps({
            "error": str(e),
            "local_path": str(output_path) if 'output_path' in locals() else None
        }, ensure_ascii=False)


registry.register(
    name="generate_report",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "generate_report",
            "description": "Generate HTML presale report and publish to WordPress. Creates a beautiful dual-theme report page with all analysis data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_hash": {
                        "type": "string",
                        "description": "8-character session ID (hex)"
                    },
                    "clinic_name": {
                        "type": "string",
                        "description": "Full clinic name for the report title"
                    },
                    "orchestrator_data": {
                        "type": "object",
                        "description": "Full orchestrator output with all collected data (financials, competitors, instagram, seo, content, whitefields, etc.)"
                    }
                },
                "required": ["session_hash", "clinic_name", "orchestrator_data"]
            }
        }
    },
    handler=handle_generate_report,
    check_fn=lambda: True,
    is_async=True,
    description="Generate and publish presale report to WordPress",
    emoji="📄"
)
