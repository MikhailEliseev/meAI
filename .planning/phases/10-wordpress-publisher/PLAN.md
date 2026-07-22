# PLAN.md — Phase 10: WordPress Publisher

> **Phase:** 10
> **Milestone:** 2 (v3 Feature Parity)
> **Created:** 2026-07-22
> **REQ:** REQ-1.3
> **Depends on:** Phase 9 (HTML Builder)

---

## Goal

Создать модуль публикации HTML-отчёта в WordPress (iamaim.ru/{slug}). Принимает HTML-строку от Phase 9 builder, вставляет в `wp_posts` через MySQL (pymysql), возвращает публичный URL.

## Architecture

```
build_report_html(data, title)         ← Phase 9 (готово)
        │
        ▼ HTML string
publish_report(html, title) → URL      ← Phase 10 (этот план)
        │
        ├── pymysql.connect(aim-mysql)
        ├── INSERT INTO wp_posts (post_content, post_status=publish, post_type=page)
        ├── генерация slug (8 символов)
        └── return {"url": "https://iamaim.ru/{slug}", "post_id": N}
```

Один файл: `hermes-v2/app/report_builder/publisher.py`

## Tasks

### Task 1: Добавить pymysql в requirements.txt

**Files:**
- Modify: `AIM/hermes-v2/requirements.txt`

**What:** Добавить `pymysql` в зависимости. Сейчас requirements.txt содержит только fastapi, uvicorn, httpx, openai.

### Task 2: publisher.py — публикация в WordPress

**Files:**
- Create: `AIM/hermes-v2/app/report_builder/publisher.py`

**What:** Перенос логики из v1 `publish_scout_report.py` (строки 32-34, 120-205), адаптированный под v2:

```python
import os, random, string, logging
from datetime import datetime, timezone
import pymysql

logger = logging.getLogger(__name__)

WP_DB_HOST = os.getenv("WP_DB_HOST", "aim-mysql")
WP_DB_USER = os.getenv("WP_DB_USER", "wp_user")
WP_DB_PASSWORD = os.getenv("WP_DB_PASSWORD", "")
WP_DB_NAME = os.getenv("WP_DB_NAME", "wordpress")


def _random_slug(length: int = 8) -> str:
    """Генерация случайного slug для URL."""
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choices(chars, k=length))


async def publish_report(html: str, title: str) -> dict:
    """Публикует HTML-отчёт как страницу WordPress.

    Args:
        html: Готовый HTML (от build_report_html)
        title: Заголовок страницы (название клиники)

    Returns:
        {"status": "published", "url": "https://iamaim.ru/{slug}",
         "slug": "...", "post_id": N}
        или {"status": "saved_locally", "path": "..."} если нет DB
    """
    # Если нет пароля DB — сохраняем локально
    if not WP_DB_PASSWORD:
        report_path = f"/opt/data/reports/{_random_slug()}.html"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html)
        return {"status": "saved_locally", "path": report_path, "url": None}

    page_slug = _random_slug()
    wp_title = f"AIM — {title}"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    conn = None
    try:
        conn = pymysql.connect(
            host=WP_DB_HOST, user=WP_DB_USER,
            password=WP_DB_PASSWORD, database=WP_DB_NAME,
            charset="utf8mb4", connect_timeout=5,
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
                (1, now, now, html, wp_title,
                 "publish", "closed", "closed", page_slug, "page",
                 "", "", "", "", 0),
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
```

**Адаптации от v1:**
- Убран `session_archive.load_all_data` (v2 не использует файлы сессий)
- Убран `build_report_html` вызов (HTML приходит готовым от Phase 9)
- Убран `push_report_ready` (это Phase 11 — Chat Integration)
- `WP_DB_HOST` default: `aim-mysql` (не `wp-db`)
- Функция `publish_report(html, title)` вместо handler `handle_publish_scout_report`

### Task 3: Обновить __init__.py

**Files:**
- Modify: `AIM/hermes-v2/app/report_builder/__init__.py`

**What:** Добавить экспорт `publish_report`:

```python
from app.report_builder.builder import build_report_html
from app.report_builder.adapter import build_data_dict
from app.report_builder.publisher import publish_report
```

### Task 4: Тест publisher (мок MySQL)

**Files:**
- Create: `AIM/hermes-v2/tests/test_publisher.py`

**What:** Unit-тест с моком pymysql:
- `test_publish_report_success` — мок pymysql.connect → проверка INSERT, возврат URL
- `test_publish_report_no_db` — WP_DB_PASSWORD пустой → saved_locally
- `test_random_slug` — 8 символов, lowercase+digits
- `test_slug_uniqueness_retry` — мок возвращает существующий slug при первом запросе

### Task 5: Smoke-тест на сервере

**What:** На сервере:
1. Установить pymysql в контейнер
2. Вызвать `publish_report("<html>test</html>", "Test Clinic")`
3. Проверить что страница создалась: `curl https://iamaim.ru/{slug}`
4. Проверить в БД: `SELECT * FROM wp_posts WHERE post_name = '{slug}'`

---

## Risks

1. **pymysql не в Docker образе** — requirements.txt обновится, но нужен rebuild. Решение: Task 1 + deploy.
2. **wpautop WordPress** — может поломать HTML. Решение: builder уже минифицирует HTML в одну строку (Phase 9).
3. **Дубликаты slug** — решено retry-loop (до 10 попыток).
4. **aim-mysql доступ из hermes-v2** — проверено: оба в `aim-network`, WP_DB env vars проброшены.
