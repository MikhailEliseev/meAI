"""publisher — публикация HTML-отчёта в WordPress (iamaim.ru/{slug}).

Перенесено из v1 publish_scout_report.py, адаптировано под v2:
- HTML приходит готовым (от build_report_html Phase 9)
- Нет session_archive (v2 не использует файлы сессий)
- push_report_ready → Phase 11 (Chat Integration)
- Phase 12: get_report_html_by_slug для PDF download

MySQL: INSERT INTO wp_posts (post_content, post_status=publish, post_type=page).
Возвращает URL: https://iamaim.ru/{random-slug}.
"""
import json
import logging
import os
import random
import string
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

WP_DB_HOST = os.getenv("WP_DB_HOST", "aim-mysql")
WP_DB_USER = os.getenv("WP_DB_USER", "wp_user")
WP_DB_PASSWORD = os.getenv("WP_DB_PASSWORD", "")
WP_DB_NAME = os.getenv("WP_DB_NAME", "wordpress")


def _get_wp_db_config() -> dict:
    """Возвращает конфиг для MySQL подключения."""
    return {
        "host": WP_DB_HOST,
        "user": WP_DB_USER,
        "password": WP_DB_PASSWORD,
        "db": WP_DB_NAME,
        "charset": "utf8mb4",
        "connect_timeout": 5,
    }


def _random_slug(length: int = 8) -> str:
    """Генерация случайного slug для URL (lowercase + digits)."""
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choices(chars, k=length))


async def publish_report(html: str, title: str) -> dict:
    """Публикует HTML-отчёт как страницу WordPress.

    Args:
        html: Готовый HTML (от build_report_html).
        title: Заголовок страницы (название клиники).

    Returns:
        {"status": "published", "url": "https://iamaim.ru/{slug}",
         "slug": "...", "post_id": N}
        или {"status": "saved_locally", "path": "..."} если нет DB.
        или {"status": "error", "error": "..."} при ошибке.
    """
    # Если нет пароля DB — сохраняем локально
    if not WP_DB_PASSWORD:
        slug = _random_slug()
        report_path = f"/opt/data/reports/{slug}.html"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info("Report saved locally (no DB): %s", report_path)
        return {"status": "saved_locally", "path": report_path, "url": None, "slug": slug}

    import pymysql

    page_slug = _random_slug()
    wp_title = f"AIM — {title}"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

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
        with conn.cursor() as cur:
            # Проверка уникальности slug (до 10 попыток)
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
        logger.info("Report published: slug=%s post_id=%s url=%s", page_slug, post_id, url)
        return {"status": "published", "url": url, "slug": page_slug, "post_id": post_id}

    except pymysql.Error as e:
        logger.error("MySQL error: %s", e)
        return {"status": "error", "error": f"Database error: {e}"}
    except Exception as e:
        logger.exception("Failed to publish report")
        return {"status": "error", "error": str(e)}
    finally:
        if conn:
            conn.close()


async def get_report_html_by_slug(slug: str) -> str | None:
    """Читает HTML отчёта из MySQL по slug (Phase 12).
    
    Args:
        slug: URL slug отчёта (например 'btu2vneu')
    
    Returns:
        HTML-строка отчёта или None если не найден
    """
    if not WP_DB_PASSWORD:
        # Fallback: читаем из локального файла
        # W-CRITICAL: validate slug to prevent path traversal (../../etc/passwd)
        import re as _re
        if not _re.match(r'^[a-z0-9-]{1,32}$', slug):
            logger.warning("Rejected suspicious slug in local fallback: %r", slug)
            return None
        report_path = os.path.join("/opt/data/reports", f"{slug}.html")
        if os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as f:
                return f.read()
        return None
    
    import aiomysql
    
    config = _get_wp_db_config()
    try:
        conn = await aiomysql.connect(**config)
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT post_content FROM wp_posts WHERE post_name = %s AND post_type = 'page' LIMIT 1",
                    (slug,)
                )
                row = await cur.fetchone()
                return row[0] if row else None
        finally:
            conn.close()
    except Exception as e:
        logger.error("Failed to read report HTML for slug=%s: %s", slug, e)
        return None
