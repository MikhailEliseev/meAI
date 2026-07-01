# 03 — ЦЕЛЕВАЯ АРХИТЕКТУРА AIM v2

**Дата:** 1 июля 2026
**Статус:** Канон для переписывания

---

## 🎯 ОДНОЙ ФРАЗОЙ

**Минимум компонентов. Максимум автономии. Один pipeline. Один отчёт. Один путь к публикации.**

---

## 🏗️ КОМПОНЕНТНАЯ ДИАГРАММА

```
                    ┌──────────────────────────────────┐
                    │     КЛИЕНТ (браузер / Telegram)   │
                    └────────────────┬─────────────────┘
                                     │
                                     ▼
                    ┌──────────────────────────────────┐
                    │   NGINX reverse proxy + SSL       │
                    │   (iamaim.ru, port 443)           │
                    └────────┬───────────────┬──────────┘
                             │               │
                  /api/*     │               │  /*
                  /chat      │               │  /wp-*
                             ▼               ▼
              ┌──────────────────────┐  ┌─────────────────────┐
              │  HERMES (FastAPI)    │  │  WORDPRESS (PHP)    │
              │  Python 3.11         │  │  Theme: aim-theme   │
              │  port 8000 (внутр.)  │  │                     │
              │                      │  │  - Landing page     │
              │  - /api/chat         │  │  - Chat UI          │
              │  - /api/chat/stream  │  │  - Blog             │
              │  - /telegram/webhook │  │  - 90 страниц       │
              │  - /health           │  │  - Scout reports    │
              │  - /metrics          │  │    (8-char slug,    │
              │                      │  │     raw HTML)       │
              └────────┬─────────────┘  └──────────┬──────────┘
                       │                           │
                       │                           │
              ┌────────▼─────────┐        ┌────────▼─────────┐
              │  HERMES-AGENT    │        │  MariaDB         │
              │  library v0.14   │        │  (wp_data)       │
              │                  │        └──────────────────┘
              │  - SOUL.md       │
              │  - tool registry │
              │  - SessionDB     │
              │  - skills        │
              └────┬─────────┬───┘
                   │         │
                   │         │ SQLite state.db
                   │         ▼
                   │  ┌──────────────┐
                   │  │ /opt/data/   │
                   │  │ (volume)     │
                   │  │ - sessions/  │
                   │  │ - reports/   │
                   │  │ - memories/  │
                   │  └──────────────┘
                   │
                   ▼ tools call
     ┌──────────────────────────────────────┐
     │       ВНЕШНИЕ API                    │
     │  - DeepSeek API (LLM)                │
     │  - Apify (14 keys, scraping)         │
     │  - Firecrawl (15 keys, scraping)     │
     │  - Brave Search                      │
     │  - Perplexity                        │
     │  - nalog.ru (ГИР БО финансы)         │
     │  - 2ГИС, Яндекс.Карты, ПроДокторов   │
     │  - Telegram Bot API                  │
     │  - AssemblyAI (voice transcription)  │
     └──────────────────────────────────────┘
```

### Внешние зависимости

- **Redis** (опционально): кеш, rate limiting. Можно убрать в MVP.
- **Prometheus + Grafana**: мониторинг. Опционально для MVP, обязательно для production.

---

## 📦 КОМПОНЕНТЫ (детально)

### 1. NGINX Reverse Proxy

**Контейнер:** `aim-nginx` (или host nginx)

**Маршруты:**
```
/                    → WordPress (landing, blog)
/api/*               → Hermes FastAPI
/chat                → Hermes FastAPI /api/chat/stream
/telegram/webhook    → Hermes FastAPI
/wp-content/*        → WordPress static (CSS, JS, images)
/wp-admin/*          → WordPress admin
/{8-char-slug}      → WordPress (custom page template, raw HTML)
/reports/{slug}      → (опционально) nginx direct serve из /opt/data/reports/
```

**SSL:** Let's Encrypt, autorenewal
**Security headers:**
- `X-Frame-Options: DENY` (для scout-постов)
- `X-Content-Type-Options: nosniff`
- `Content-Security-Policy: default-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com`

### 2. HERMES Container

**Контейнер:** `aim-hermes` (Python 3.11-slim)
**Порт:** 8000 (только внутренний)
**Volume:** `aim_hermes_data:/opt/data/`

**Структура файлов (целевая):**
```
/opt/hermes/
├── app/
│   ├── main.py                # FastAPI server (≤400 строк)
│   ├── auth.py                # Bearer auth
│   ├── agent_wrapper.py       # AIAgent lifecycle (≤400 строк)
│   ├── telegram_gateway.py    # Telegram integration
│   ├── pipeline/
│   │   ├── engine.py          # PipelineEngine (≤500 строк)
│   │   ├── phases.py          # Описание 13 фаз
│   │   └── states.py          # State machine
│   └── tools/
│       ├── __init__.py        # Registry
│       ├── run_full_scout.py  # Единая точка входа
│       ├── find_competitors.py
│       ├── find_company_financials.py
│       ├── run_tech_seo_audit.py
│       ├── run_lighthouse.py
│       ├── run_content_analysis.py
│       ├── run_smi_mentions.py
│       ├── run_forum_pains.py
│       ├── run_review_platforms.py
│       ├── find_doctor_handles.py
│       ├── run_hh_analysis.py
│       ├── build_report.py    # ⭐ НОВЫЙ: полная дизайн-система
│       ├── publish_scout_report.py
│       ├── collect_contact.py
│       └── key_bank.py        # Rotation: Apify + Firecrawl
├── skills/
│   ├── aim/SOUL.md            # Идентичность LLM (≤30 KB)
│   └── client-onboarding-pipeline/SKILL.md
└── tests/
    ├── test_pipeline.py
    ├── test_report_builder.py
    └── test_publish.py
```

**Размер:**
- Сейчас 67 tools → цель 15-20 tools (LLM-visible)
- Сейчас 760 строк agent_wrapper → цель 400 строк
- Сейчас 698 строк generate_html_report → цель 0 (удалить), новый build_report 600-800 строк

### 3. WORDPRESS Container

**Контейнер:** `aim-wordpress` (PHP 8.2 + Apache или PHP-FPM)
**Theme:** `aim-theme` v3.0 (новая, очищенная)

**Структура темы (целевая):**
```
wp-content/themes/aim-theme/
├── style.css                  # Theme metadata
├── theme.css                  # canonical CSS (из design-showcase)
├── functions.php              # Минимум hooks (≤150 строк)
├── index.php                  # Template: raw HTML для scout ИЛИ landing
├── front-page.php             # Landing page
├── page-blog.php              # Blog listing
├── single.php                 # Blog post template
├── header.php                 # С шапкой сайта
├── footer.php                 # С футером
├── scout-privacy.php          # Privacy filters (из текущей версии)
├── chat/
│   ├── chat-inline.php        # Chat bubble widget
│   └── chat-pro.html          # Full-page chat
├── design-showcase-dual-theme.html  # Canonical reference
├── assets/
│   ├── js/
│   │   ├── chat-stream.js     # SSE client
│   │   ├── theme-toggle.js    # localStorage theme
│   │   └── progress-bar.js    # Pipeline progress UI
│   ├── css/
│   │   ├── chat.css           # Chat widget styles
│   │   └── blog.css           # Blog styles
│   └── images/
└── inc/
    ├── enqueue.php            # Скрипты и стили
    └── shortcodes.php         # Если нужны шорткоды
```

**Custom page template для scout-постов:**

`index.php` должен определять scout-пост по паттерну:
```php
$post = get_queried_object();
$is_scout_report = (
    is_page() && !is_admin() && !is_search() && !is_archive()
    && !is_feed() && !is_preview() && !is_comment_feed() && !is_404()
    && $post instanceof WP_Post
    && empty($post->post_password)
    && preg_match('/^[a-z0-9]{8}$/', $post->post_name)
    && strpos($post->post_content, '<!DOCTYPE html>') === 0
    && strpos($post->post_content, '</html>') !== false
);

if ($is_scout_report) {
    header('Content-Type: text/html; charset=utf-8');
    header('Cache-Control: no-store, no-cache, must-revalidate');
    header('Content-Length: ' . strlen($post->post_content));
    echo $post->post_content;
    exit;
}

// Обычный WordPress рендеринг (landing, blog, etc.)
get_header();
if (have_posts()) {
    while (have_posts()) { the_post(); the_content(); }
}
get_footer();
```

**КРИТИЧНО:** `strlen()` НЕ `mb_strlen()`. Content-Length = байты, не символы.

### 4. MariaDB Container

**Контейнер:** `aim-mysql`
**БД:** `wordpress`
**Юзер:** `wp_user`

**Использование:**
- WordPress pages (90 штук)
- Scout reports (как pages с 8-char slug)
- Post meta
- Опции темы

**НЕ использование:**
- CRM данные (не нужно)
- Лиды (в SQLite state.db)
- Аналитика (в Prometheus)

### 5. Redis Container (опционально)

**Контейнер:** `aim-redis`
**Использование:**
- Rate limiting для API ключей
- Cache для дорогих запросов (Lighthouse, ГИР БО)
- Очереди для фоновых задач

**Можно убрать в MVP**, добавить когда нагрузка растёт.

---

## 🔄 ПОТОКИ ДАННЫХ

### Поток 1: URL → Scout Pipeline → Отчёт (PRIMARY)

```
1. Клиент пишет "https://my-clinic.ru" в чат
2. Nginx → WordPress → chat-stream.js → Hermes /api/chat/stream
3. Hermes auth → agent_wrapper → AIAgent (SOUL.md + PRESALE промпт)
4. LLM определяет: URL → вызывает run_full_scout(url)
5. run_full_scout → PipelineEngine.execute()
6. PipelineEngine запускает 13 фаз:
   - Каждая фаза вызывает tools
   - Каждый tool → внешний API
   - PipelineEngine сохраняет данные в session_archive
   - Прогресс стримится в чат через SSE
7. После фазы 10: HTML отчёт собран
8. Фаза 12: publish_scout_report → INSERT в wp_posts
9. run_full_scout возвращает JSON: {report_url, key_findings, client_name}
10. LLM получает JSON, формирует 3 финальных сообщения
11. SSE стримит сообщения в чат
12. Клиент видит ссылку, кликает
13. Nginx → WordPress → index.php (custom template)
14. index.php: 8-char slug + DOCTYPE → echo raw HTML
15. Клиент видит красивый отчёт
```

### Поток 2: Telegram Chat (опциональный)

```
1. Клиент пишет @AIM_bot в Telegram
2. Telegram Bot API → webhook → Hermes /telegram/webhook
3. telegram_gateway → run_agent_sync (с locking)
4. Дальше как поток 1
5. Ответ отправляется через Bot API
```

### Поток 3: Admin monitoring (опциональный)

```
1. Михаил открывает https://iamaim.ru/wp-admin
2. Логинится в WordPress
3. Видит список scout reports (через WP_Query)
4. Может редактировать → НЕ должно ломать HTML (custom template)
5. Может удалять (через trash)
```

---

## 🧱 ПРИНЦИПЫ АРХИТЕКТУРЫ

### Принцип 1: LLM-оркестратор + Python pipeline

**LLM (Hermes)** решает:
- Какой режим (PRESALE, ACTIVE, ADMIN)
- Когда вызвать run_full_scout
- Какой тон ответа
- Какую информацию запросить у клиента

**Python (PipelineEngine)** решает:
- Какие 13 фаз выполнить
- В каком порядке
- Что делать если фаза упала
- Как собрать данные в отчёт

**Разделение ответственности:** LLM НЕ решает что вызывать внутри pipeline. Python НЕ решает что отвечать клиенту.

### Принцип 2: Единая точка входа

**Один tool для разведки:** `run_full_scout`. LLM НЕ вызывает отдельные фазы.
**Один генератор отчётов:** `build_report.py` (новый). Никаких дублей.
**Один способ публикации:** `publish_scout_report.py` → INSERT в wp_posts → custom page template.

### Принцип 3: Standalone HTML для scout-постов

Scout-посты = self-contained HTML документ (DOCTYPE → html → head → body → /html).
- НЕ используют WordPress header/footer
- НЕ подвержены wpautop, wptexturize
- НЕ требуют page template meta
- Рендерятся через `echo $post->post_content; exit;`

### Принцип 4: Идемпотентность

Pipeline можно перезапустить. Каждая фаза:
- Сохраняет результат в session_archive
- При повторном запуске может взять кеш (если data_hash совпадает)
- Не ломает предыдущие результаты

### Принцип 5: Privacy by design

- Scout-посты: `noindex, nofollow` meta
- Sitemap: scout-посты исключены (`post__not_in`)
- REST API: 403 для scout-постов
- Old named URLs: 301 redirect на главную
- Fragment posts: post_status='draft'

### Принцип 6: Минимум moving parts

- 4 контейнера (Hermes + WordPress + MariaDB + Nginx) вместо 16
- SQLite вместо PostgreSQL (хватит для MVP)
- Redis — опционально
- Без Prometheus/Grafana в MVP (можно добавить после)

---

## 🗂️ СТРУКТУРА КАТАЛОГОВ (целевая)

```
/opt/aim/
├── docker-compose.yml          # Минимальный (4-5 сервисов)
├── .env                        # API ключи (не в git!)
├── nginx/
│   └── aim.conf                # Конфиг nginx
├── hermes/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/                    # Python код (см. выше)
│   ├── skills/                 # SOUL.md и skills
│   └── tests/
├── wordpress-core/
│   ├── wp-config.php
│   └── wp-content/
│       ├── themes/aim-theme/   # См. выше
│       └── plugins/            # Минимум: WP Rocket, Rank Math SEO
└── scripts/
    ├── deploy.sh               # Деплой
    ├── backup.sh               # Бэкап
    └── health-check.sh         # Smoke test
```

---

## 🔐 ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ

```bash
# LLM
DEEPSEEK_API_KEY=sk-...
LLM_MODEL=ds/deepseek-v4-pro

# Apify (14 keys)
APIFY_API_TOKEN=apify_api_key_...
APIFY_API_TOKEN_01=apify_api_key_...
... (до _13)

# Firecrawl (15 keys)
FIRECRAWL_API_KEY=fc-...
FIRECRAWL_API_KEY_01=fc-...
... (до _14)

# Search
BRAVE_API_KEY=BSA...
PERPLEXITY_API_KEY=pplx-...

# WordPress DB
WP_DB_HOST=mysql
WP_DB_USER=wp_user
WP_DB_PASSWORD=...
WP_DB_NAME=wordpress

# Hermes auth
HERMES_API_KEY=hmr_...

# Telegram
TELEGRAM_BOT_TOKEN=...
TELEGRAM_ADMIN_CHAT_ID=...
TELEGRAM_API_ID=...
TELEGRAM_API_HASH=...
TELEGRAM_WEBHOOK_URL=https://iamaim.ru/telegram/webhook

# Voice
ASSEMBLYAI_API_KEY=...

# Misc
HERMES_HOME=/opt/data
SESSIONS_ROOT=/opt/data/sessions-archive
ARCHIVE_BASE_URL=https://iamaim.ru/wp-json/aim/v1/session
```

---

## 📊 РАЗМЕР И ПРОИЗВОДИТЕЛЬНОСТЬ

### Целевые метрики

| Метрика | Цель | Текущее |
|---|---|---|
| Контейнеров running | 4-5 | 16 |
| Размер Docker образов | 4-5 GB | 13 GB |
| Disk usage | 5-8 GB | 24 GB |
| Tools в registry | 15-20 | 67 |
| Размер SOUL.md | 25-35 KB | 106 KB |
| Время pipeline (example.ru) | 3-5 мин | 3:24 ✅ |
| Время pipeline (реальная клиника) | 5-8 мин | 8:00 ✅ |
| Time to first byte (TTFB) | <300ms | ~500ms |
| Chat streaming start | <2s | ~3s |

### Тестирование производительности

После MVP — нагрузочное тестирование:
- 1 одновременный клиент = baseline
- 5 одновременных = цель для MVP
- 20 одновременных = цель для v2.0

---

## 🚀 ЧТО ОСТАВЛЯЕМ КАК ЕСТЬ

1. **DeepSeek API** — основная LLM, не меняем
2. **hermes-agent library v0.14** — стабильная, не трогаем
3. **Apify + Firecrawl** — rotation работает
4. **Telegram Bot API** — стабильно
5. **WordPress core** — обновляем только minor версии
6. **aim-theme** — рефакторим, не пересоздаём

---

## 🛠️ ЧТО ПЕРЕПИСЫВАЕМ С НУЛЯ

1. **PipelineEngine** (`app/pipeline/engine.py`) — упростить, сделать читаемым
2. **build_report.py** — НОВЫЙ генератор отчётов (полная дизайн-система)
3. **publish_scout_report.py** — упростить (только INSERT)
4. **SOUL.md** — новая идентичность (Hermes = аналитик, не оператор)
5. **PRESALE промпт** — упростить (или переименовать в ANALYSIS)
6. **WordPress index.php** — custom template (уже сделано 1 июля)
7. **scout-privacy.php** — уже сделано v2 (1 июля)

---

## ⚠️ АРХИТЕКТУРНЫЕ РЕШЕНИЯ, КОТОРЫЕ НАДО ПРИНЯТЬ

### Решение 1: SQLite vs PostgreSQL для leads/sales

- **SQLite:** проще, хватает для MVP, нет auth проблем
- **PostgreSQL:** масштабируемо, но требует фикса auth

**Рекомендация:** SQLite для MVP. PostgreSQL — после.

### Решение 2: iframe vs custom page template для scout-постов

- **iframe** (как в post_report.py): полная изоляция CSS, но лишний запрос
- **custom page template** (как сейчас): один запрос, но риски CSS конфликтов

**Рекомендация:** custom page template (как уже сделано). Standalone HTML с DOCTYPE = достаточно изоляции.

### Решение 3: Next.js vs WordPress для landing

- **Next.js:** современный стек, но лишний контейнер
- **WordPress:** один контейнер, легче поддержка

**Рекомендация Михаил уже дал:** WordPress. Next.js убрать.

### Решение 4: Redis vs in-memory cache

- **Redis:** persistent, multi-process
- **in-memory:** быстрее, но теряется при рестарте

**Рекомендация:** Redis опционально. В MVP — in-memory.

---

*Этот документ — целевая архитектура. Любые отклонения требуют обновления этого файла.*
