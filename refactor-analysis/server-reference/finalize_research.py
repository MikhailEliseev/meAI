"""
finalize_research — Hermes tool: Finalize Research & Notify

Called at the END of a deep research session. Archives the conversation,
saves to Second Brain, notifies Mikhail via Telegram, and returns a
beautiful "report ready" card for the client.

Registered in Hermes internal registry under toolset "aim-operations".
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from tools.registry import registry

logger = logging.getLogger(__name__)

# Session archive base URL (WordPress endpoint)
ARCHIVE_BASE_URL = os.getenv("ARCHIVE_BASE_URL", "https://iamaim.ru/wp-json/aim/v1/session")


async def handle_finalize_research(
    session_id=None,
    client_url=None,
    client_name=None,
    summary=None,
    publish_html_report=None,
    **kwargs,
) -> str:
    """Finalize a deep research session: archive, notify, return report link.

    Call this AFTER completing deep research (prescan + competitors + CI analysis
    + all deep-dive tools). It archives the full conversation, saves to Second Brain,
    sends a Telegram notification to Mikhail, and returns a formatted "report ready"
    card for the client.

    Args:
        session_id: Current Hermes session ID (from context)
        client_url: Client clinic website URL
        client_name: Client clinic name (optional, for notification)
        summary: Brief summary of what was analyzed (1-2 sentences)
        publish_html_report: If True, also generate and publish an AIM design system
            HTML report page on iamaim.ru (optional, default False)

    Returns:
        JSON with session_hash, session_url, report_url (if published), and pre-formatted card HTML
    """
    if isinstance(session_id, dict):
        d = session_id
        session_id = d.get("session_id", "")
        if not client_url:
            client_url = d.get("client_url", "")
        if not client_name:
            client_name = d.get("client_name", "")
        if not summary:
            summary = d.get("summary", "")
        if publish_html_report is None:
            publish_html_report = d.get("publish_html_report", False)

    # Fallback: if LLM didn't pass session_id, read from thread-local context
    if not session_id:
        from app.session_context import get_current_session
        session_id = get_current_session()
        if session_id:
            logger.info("Using session_id from thread-local context: %s", session_id)

    if not session_id:
        return json.dumps({"error": "session_id is required"})

    logger.info("Finalizing research for session %s (client: %s, url: %s)",
                 session_id, client_name, client_url)

    # ── Archive session ────────────────────────────────────────────────
    from app.session_archiver import archive_session, SESSIONS_ROOT

    session_hash = archive_session(session_id)
    if not session_hash:
        logger.error("Failed to archive session %s", session_id)
        return json.dumps({
            "error": "Failed to archive session",
            "detail": f"Session {session_id} not found in database or archiving failed",
        })

    session_url = f"{ARCHIVE_BASE_URL}/{session_hash}"

    # ── Save prescan/CI data to session archive ────────────────────────
    _copy_tool_data_to_archive(session_id, session_hash)

    # ── Notify Mikhail via Telegram ────────────────────────────────────
    await _notify_admin(session_id, session_hash, session_url, client_url, client_name, summary)

    # ── Build result ───────────────────────────────────────────────────
    now = datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M")

    report_card = {
        "type": "report_ready",
        "session_hash": session_hash,
        "session_url": session_url,
        "archived_at": now,
        "client_url": client_url,
        "client_name": client_name,
        "summary": summary or f"Полный разбор сайта {client_url or 'клиники'} — финансы, SEO, конкуренты, отзывы, реклама, контент.",
    }

    # ── Optionally generate HTML report ──────────────────────────────
    if publish_html_report:
        try:
            from .generate_html_report import handle_generate_html_report
            report_json = await handle_generate_html_report(
                session_hash=session_hash,
                client_name=client_name,
                client_url=client_url,
            )
            report = json.loads(report_json)
            report_url = report.get("url")
            if report_url:
                report_card["report_url"] = report_url
                logger.info("HTML report published at %s", report_url)
        except Exception as e:
            logger.warning("Failed to generate HTML report: %s", e)

    logger.info("Research finalized: session=%s hash=%s url=%s",
                 session_id, session_hash, session_url)

    return json.dumps(report_card, ensure_ascii=False, indent=2)


def _copy_tool_data_to_archive(session_id: str, session_hash: str) -> None:
    """Copy prescan, CI analysis, and aim-scout data from /opt/data/ and /tmp to session archive."""
    from app.session_archiver import SESSIONS_ROOT

    session_dir = SESSIONS_ROOT / session_hash
    if not session_dir.exists():
        return

    reports_dir = Path("/opt/data/reports")

    # Copy prescan data
    if reports_dir.exists():
        try:
            prescan_files = sorted(
                reports_dir.glob("prescan-*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            if prescan_files:
                import shutil
                shutil.copy(prescan_files[0], session_dir / "prescan-data.json")
                logger.info("Copied prescan data to archive: %s", prescan_files[0].name)
        except Exception as e:
            logger.warning("Failed to copy prescan data: %s", e)

        # Copy CI analysis report if exists
        try:
            ci_files = sorted(
                reports_dir.glob("ci-analysis-*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            if ci_files:
                import shutil
                shutil.copy(ci_files[0], session_dir / "ci-analysis.json")
                logger.info("Copied CI analysis to archive: %s", ci_files[0].name)
        except Exception as e:
            logger.warning("Failed to copy CI data: %s", e)

    # Copy aim-scout data from /tmp
    try:
        tmp_dir = Path("/tmp")
        scout_files = sorted(
            tmp_dir.glob("*-scout-brief.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if scout_files:
            import shutil
            shutil.copy(scout_files[0], session_dir / "aim-scout-data.json")
            logger.info("Copied aim-scout data to archive: %s", scout_files[0].name)
    except Exception as e:
        logger.warning("Failed to copy aim-scout data: %s", e)


async def _notify_admin(
    session_id: str,
    session_hash: str,
    session_url: str,
    client_url: str | None,
    client_name: str | None,
    summary: str | None,
) -> None:
    """Send Telegram notification to Mikhail about completed research."""
    try:
        from app.telegram_gateway import _send_telegram_message_sync
        import threading

        # Get admin chat ID from env var (first one) or fallback to Mikhail's
        admin_ids = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "338744075")
        admin_chat_id = int(admin_ids.split(",")[0].strip())

        label = client_name or client_url or "неизвестная клиника"
        url_line = f"Сайт: {client_url}" if client_url else ""

        text = (
            f"🔔 <b>Новое исследование завершено</b>\n\n"
            f"Клиника: <b>{label}</b>\n"
            f"{url_line}\n"
            f"Анализ: {summary or 'полный прескан + конкуренты + CI'}\n\n"
            f"📄 <a href=\"{session_url}\">Открыть отчёт</a>\n"
            f"🔗 <code>{session_url}</code>\n\n"
            f"Session: <code>{session_id[:30]}...</code>\n"
            f"Hash: <code>{session_hash}</code>"
        )

        # Run in thread to avoid blocking
        def _send():
            _send_telegram_message_sync(admin_chat_id, text)

        thread = threading.Thread(target=_send, daemon=True)
        thread.start()

        logger.info("Telegram notification sent for session %s", session_hash)

    except Exception as e:
        logger.warning("Failed to send Telegram notification: %s", e)


registry.register(
    name="finalize_research",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "finalize_research",
            "description": (
                "Finalize a deep research session and generate a report link for the client. "
                "Call this at the END of a deep research conversation — after prescan, "
                "competitor analysis, CI analysis, and any deep-dive tools (pagespeed, "
                "reviews, ads, content gaps, etc.) are complete. "
                "Archives the full conversation, saves to Second Brain, notifies Mikhail "
                "via Telegram, and returns a report URL the client can open. "
                "CRITICAL: call this BEFORE collect_contact — the report link builds trust "
                "and shows the client you delivered real value."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "[REQUIRED] Current Hermes session ID (from conversation context)",
                    },
                    "client_url": {
                        "type": "string",
                        "description": "Client clinic website URL that was analyzed",
                    },
                    "client_name": {
                        "type": "string",
                        "description": "Client clinic name (optional, for notification)",
                    },
                    "summary": {
                        "type": "string",
                        "description": "Brief summary of what was analyzed — 1-2 sentences (e.g., 'Разбор сайта, поиск 5 конкурентов, CI-анализ, отзывы на 8 платформах')",
                    },
                    "publish_html_report": {
                        "type": "boolean",
                        "description": "Set to true to also generate and publish a beautiful AIM design system HTML report page on iamaim.ru. The report URL will be included in the response.",
                    },
                },
                "required": ["session_id"],
            },
        },
    },
    handler=handle_finalize_research,
    check_fn=lambda: True,
    is_async=True,
    description="Archive session, save to Second Brain, notify admin, return report URL",
    emoji="📄",
)
