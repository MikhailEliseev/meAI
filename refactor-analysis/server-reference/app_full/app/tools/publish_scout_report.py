"""publish_scout_report — Hermes tool: Publish scout report as a beautiful WordPress page.

Reads scout data from /opt/data/sessions-archive/{slug}/ via session_archive.load_all_data(),
generates a self-contained HTML report page (using the same builder as generate_html_report),
inserts it into WordPress via direct DB, and returns the public URL.

Registered in Hermes internal registry under toolset "aim-operations".
"""

import json
import logging
import os
import random
import string
from datetime import datetime, timezone

import pymysql

from tools.registry import registry
from app.tools.session_archive import load_all_data, SESSIONS_ROOT

logger = logging.getLogger(__name__)

WP_DB_HOST = os.getenv("WP_DB_HOST", "wp-db")
WP_DB_USER = os.getenv("WP_DB_USER", "wp_user")
WP_DB_PASSWORD = os.getenv("WP_DB_PASSWORD", "")
WP_DB_NAME = os.getenv("WP_DB_NAME", "wordpress")

SCOUT_DATA_DIR = "/opt/data/competitors"


def _random_slug(length: int = 8) -> str:
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choices(chars, k=length))


def _list_available_slugs() -> list:
    """List available scout data directories from both sources."""
    slugs = []
    for base in (SESSIONS_ROOT, SCOUT_DATA_DIR):
        try:
            if os.path.isdir(base):
                for d in os.listdir(base):
                    full = os.path.join(base, d)
                    if os.path.isdir(full):
                        data_dir = os.path.join(full, "data")
                        data_json = os.path.join(full, "data.json")
                        if (os.path.isdir(data_dir) and os.listdir(data_dir)) or os.path.exists(data_json):
                            slugs.append(d)
        except OSError:
            pass
    return sorted(set(slugs))


async def handle_publish_scout_report(slug=None, url=None, already_published=False, **kwargs) -> str:
    """Publish a scout report as a beautiful WordPress page.

    Reads scout data from /opt/data/sessions-archive/{slug}/ (v7 pipeline format),
    generates HTML report, and inserts into WordPress.

    Args:
        slug: Scout data slug (e.g. 'full-test-toriclinic'). Reads from sessions-archive.
        url: If already published, just return the URL.
        already_published: Flag indicating the report is already live.
    """
    if isinstance(slug, dict):
        d = slug
        slug = d.get("slug", "")
        url = d.get("url", "")
        already_published = d.get("already_published", False)

    # Already published — just confirm
    if url and already_published:
        logger.info("Scout report already published at %s, skipping duplicate", url)
        return json.dumps({
            "status": "already_published",
            "url": url,
            "message": "Report was already published by generate_html_report",
        }, ensure_ascii=False)

    if not slug:
        return json.dumps({"error": "slug is required — the scout data identifier"})

    # 1. Try to load session archive data (v7 pipeline format)
    data = load_all_data(slug)

    if not data or len(data) <= 1:
        # Fallback: try legacy data.json format
        for base in (SCOUT_DATA_DIR, SESSIONS_ROOT):
            data_path = os.path.join(base, slug, "data.json")
            if os.path.exists(data_path):
                try:
                    with open(data_path, "r") as f:
                        data = json.load(f)
                    break
                except (json.JSONDecodeError, OSError):
                    pass

        if not data or len(data) <= 1:
            return json.dumps({
                "error": f"Scout data not found for slug '{slug}'",
                "detail": f"Checked {SESSIONS_ROOT}/{slug}/data/ and {SCOUT_DATA_DIR}/{slug}/data.json",
                "available_slugs": _list_available_slugs(),
            })

    # 2. Build HTML using canonical builder (1 июля 2026: Google Fonts + 14 классов)
    from app.tools.build_report import build_report_html

    meta = data.get("metadata", {}) or {}
    title = meta.get("company_name") or slug
    html = build_report_html(data, title)

    # 3. Publish to WordPress
    if not WP_DB_PASSWORD:
        # Save locally
        report_path = os.path.join(SESSIONS_ROOT, slug, "report.html")
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html)
        return json.dumps({
            "status": "saved_locally",
            "path": report_path,
            "url": None,
            "slug": slug,
        }, ensure_ascii=False)

    page_slug = _random_slug()
    wp_title = f"AIM Scout — {title}"

    conn = None
    try:
        conn = pymysql.connect(
            host=WP_DB_HOST,
            user=WP_DB_USER,
            password=WP_DB_PASSWORD,
            database=WP_DB_NAME,
            charset="utf8mb4",
            connect_timeout=5,
        )

        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        with conn.cursor() as cur:
            cur.execute("SELECT ID FROM wp_posts WHERE post_name = %s LIMIT 1", (page_slug,))
            attempts = 0
            while cur.fetchone() and attempts < 10:
                page_slug = _random_slug()
                cur.execute("SELECT ID FROM wp_posts WHERE post_name = %s LIMIT 1", (page_slug,))
                attempts += 1

            cur.execute(
                """INSERT INTO wp_posts
                   (post_author, post_date, post_date_gmt, post_content, post_title,
                    post_status, comment_status, ping_status, post_name, post_type,
                    post_excerpt, to_ping, pinged, post_content_filtered, menu_order)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    1, now, now, html, wp_title,
                    "publish", "closed", "closed", page_slug, "page",
                    "", "", "", "", 0,
                ),
            )
            post_id = cur.lastrowid
        conn.commit()

        url = f"https://iamaim.ru/{page_slug}"
        logger.info("Scout report published: slug=%s post_id=%s url=%s", slug, post_id, url)

        # Also save locally
        report_path = os.path.join(SESSIONS_ROOT, slug, "report.html")
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html)

        return json.dumps({
            "status": "published",
            "url": url,
            "slug": page_slug,
            "post_id": post_id,
            "title": wp_title,
        }, ensure_ascii=False)

    except pymysql.Error as e:
        logger.error("MySQL error: %s", e)
        return json.dumps({"error": f"Database error: {str(e)}"})
    except Exception as e:
        logger.exception("Failed to publish report")
        return json.dumps({"error": f"Failed to publish page: {str(e)}"})
    finally:
        if conn:
            conn.close()


registry.register(
    name="publish_scout_report",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "publish_scout_report",
            "description": "Публикует готовый scout-отчёт как красивую страницу на iamaim.ru. "
                           "Читает данные из /opt/data/sessions-archive/{slug}/, "
                           "генерирует HTML-страницу с классами дизайн-системы AIM и вставляет в WordPress. "
                           "Возвращает публичный URL вида https://iamaim.ru/{random-slug}. "
                           "Вызывай после завершения всех фаз сканирования.",
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {
                        "type": "string",
                        "description": "[REQUIRED] Идентификатор сканирования (например 'full-test-toriclinic')",
                    },
                },
                "required": ["slug"],
            },
        },
    },
    handler=handle_publish_scout_report,
    check_fn=lambda: bool(WP_DB_PASSWORD),
    is_async=True,
    description="Publish scout report as a beautiful WordPress page on iamaim.ru",
    emoji="📄",
)
