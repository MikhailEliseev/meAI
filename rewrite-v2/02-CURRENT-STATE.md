# 02 — ТЕКУЩЕЕ СОСТОЯНИЕ (что есть сейчас)

**Дата аудита:** 1 июля 2026
**Метод:** чтение кода локально + предыдущие 4 раунда проверок (104+ тестов)
**Принцип:** Только факты из измерения. Никаких "я думаю".

---

## 📊 ЦИФРЫ ПРОЕКТА

| Метрика | Значение | Источник |
|---|---|---|
| Длительность разработки | 2 месяца (1 мая → 30 июня 2026) | git log |
| Количество коммитов | 2078 | git log |
| Docker контейнеры (running) | 16 | docker ps |
| Docker образы | 14, 13.1 GB общий размер | docker images |
| Persistent volumes | 11, 886 MB | docker volume ls |
| Hermes tools зарегистрировано | 67 (CLAUDE.md говорит 33) | registry.register() calls |
| Hermes skills | 5 | /opt/hermes/skills/ |
| Hermes SQLite сессии | 32 сессии, 161 сообщение | /opt/data/state.db |
| REST endpoints aim-app | 53 (по OpenAPI) | FastAPI docs |
| Таблицы в PostgreSQL | 45 (все пустые) | psql \dt |
| WordPress страниц | 90 (после cleanup 27 июня) | wp_posts |
| Python файлов в `src/aim/` | 134 + 76 тестов | find |
| Markdown файлов в корне AIM | 233 | find |
| Активность за 24h (29-30 июня) | 46 chat calls, 58 tool calls | nginx access log |
| Disk usage | 24 GB / 69 GB (36%) | df -h |
| Server uptime | 2 days 10 hours | uptime |
| Load average | 0.29 / 0.25 / 0.26 (низкая) | uptime |

---

## 🏗️ ЧТО РАБОТАЕТ (ядро)

### 1. Hermes Chat (Production)

**Где:** `AIM/hermes/` локально, container `aim-hermes` на сервере

**Что работает:**
- ✅ FastAPI сервер на порту 8000 (внутри Docker сети)
- ✅ Streaming chat endpoint `/api/chat/stream` (SSE, deadline 600s)
- ✅ Sync chat endpoint `/api/chat` (для быстрых ответов)
- ✅ Telegram gateway (webhook + polling, telethon user-client)
- ✅ Session persistence (SQLite, /opt/data/state.db, 32 сессии)
- ✅ Bearer auth (`HERMES_API_KEY`)
- ✅ Metrics endpoint `/metrics` (Prometheus)
- ✅ Health endpoint `/health`

**Промпт-инжиниринг:**
- ✅ SOUL.md (106 KB runtime, 47 KB в образе — РАССИНХРОН)
- ✅ 4 режима: PRESALE, ACTIVE, ADMIN, SALES_ADMIN
- ✅ PRESALE промпт говорит: "вызови ТОЛЬКО run_full_scout" (фикс от 29 июня)
- ✅ 3-сообщений финальный формат (контраст → точки роста → отчёт)

### 2. LLM Integration

- ✅ DeepSeek V4 Pro как primary (`LLM_MODEL=ds/deepseek-v4-pro`)
- ✅ Direct API call (без OmniRoute proxy с 17 июня)
- ✅ Function calling через hermes-agent library
- ✅ Token economy tracking (`/opt/data/state.db`)
- ✅ Async через ThreadPoolExecutor (900s timeout)

### 3. Tool Registry (67 tools)

**Распределение:**
- **aim-operations toolset** (~33 tools): prescan, find_competitors, ci_analysis, seo_audit, content_audit, ads_report, leads, sales, onboarding
- **hermes-debug toolset** (~15 tools): shell_exec, file_read, file_write, web_fetch, web_search, firecrawl_web, bitrix_scrape, browser_screenshot
- **aim-scout toolset** (~19 tools): 13 фаз pipeline + вспомогательные

**Что работает стабильно:**
- `run_full_scout` — запускает PipelineEngine, 13 фаз (см. ниже)
- `find_competitors` — Apify + key rotation (14 ключей)
- `find_company_financials` — nalog.ru ГИР БО парсинг
- `run_ci_analysis` — глубокий анализ конкурентов
- `run_seo_audit` — SEO/tech аудит через Lighthouse
- `firecrawl_web` — scraping с key rotation (15 ключей)
- `publish_scout_report` — INSERT в wp_posts

### 4. Pipeline Engine (v7)

**Файлы:**
- `AIM/hermes/app/pipeline/engine.py` — основной движок
- `AIM/hermes/app/pipeline/phases.py` — описание 13 фаз
- `AIM/hermes/app/pipeline/states.py` — state machine

**Поток:**
```
run_full_scout(url)
  → PipelineEngine.execute(session_id, url, mode, chat_id)
    → 13 фаз последовательно (с session_archive сохранением)
      → Фаза 0: Perplexity research (prescan/market)
      → Фаза 1: Apify + find_competitors
      → Фаза 2: Lighthouse + run_tech_seo_audit
      → Фаза 3: Reviews (2ГИС, Яндекс.Карты, ПроДокторов)
      → Фаза 4: run_content_analysis (firecrawl)
      → Фаза 5: find_doctor_handles
      → Фаза 6: run_smi_mentions (Brave + Perplexity)
      → Фаза 7: run_forum_pains
      → Фаза 8: find_company_financials (nalog.ru)
      → Фаза 9: run_content_gaps (LLM synthesis)
      → Фаза 10: HTML assembly (generate_html_report)
      → Фаза 11: run_validation_check (QC)
      → Фаза 12: publish_scout_report (INSERT в wp_posts)
    → return JSON: { client_name, phases[], report_url, key_findings[] }
```

**Реальное время прогона:**
- example.ru (тестовый): 3:24
- iphk.ru (реальный): 8:00
- diamond-clinic.ru: ~6-7 минут

### 5. WordPress Stack

- ✅ WordPress 6.x в Docker container `aim-wordpress`
- ✅ PHP 8.2, MariaDB 10.11 в `aim-mysql`
- ✅ Theme: `aim-theme` v2.1.76 (активна)
- ✅ 90 страниц (после cleanup 27 июня — 27 скрыто в draft)
- ✅ Custom page template для scout-постов (см. ниже — фикс от 1 июля)
- ✅ Privacy filters (scout-privacy.php v2 от 1 июля)

### 6. Design System (canonical reference)

**Файл:** `AIM/wordpress-core/wp-content/themes/aim-theme/design-showcase-dual-theme.html` (2521 строка)

**Что включено:**
- ✅ Light theme (монументально-чёрный на белом)
- ✅ Dark theme (Art Deco gold #c9a96e на #0d0d0d)
- ✅ Glass cards с `backdrop-filter: blur(20px) saturate(1.4)`
- ✅ Card-breathe анимация
- ✅ Water ripple background (в light теме)
- ✅ Playfair Display + Jost Google Fonts
- ✅ Metric tags (5 цветов: green/yellow/red/blue/gray)
- ✅ Surface blocks (green/red variants)
- ✅ Glass tables, timeline, CTA blocks
- ✅ Theme toggle (localStorage `aim-theme`)

### 7. Infrastructure Stack

- ✅ Nginx reverse proxy (SSL termination через Let's Encrypt)
- ✅ Prometheus + Grafana + Alertmanager (мониторинг)
- ✅ postgres-exporter + node-exporter
- ✅ Redis для кеша и очередей
- ✅ Internal Docker network `aim_aim-network`

---

## 🚨 ЧТО СЛОМАНО ИЛИ НЕДОДЕЛАНО

### 🔴 КРИТИЧНО (блокирует MVP)

#### 1. Три разных генератора HTML отчётов

В коде существуют ТРИ разных способа сгенерировать HTML отчёт:

| Файл | Строк | Что делает | Стиль |
|------|-------|------------|-------|
| `generate_html_report.py` | 698 | Старый генератор, делает `<style>` + `<div data-aim="report">` + секции | Минималистичный, чёрно-белый, БЕЗ glass cards, БЕЗ бейджей |
| `post_report.py` | 363 | Новый генератор, делает полный `<!DOCTYPE>` с iframe-изоляцией | Полная дизайн-система, шрифт **Inter** (НЕ canonical Jost!) |
| `migrate_scout_design.py` | 508 | Миграция старых постов в новую дизайн-систему | Базовая (glass cards + dark), но БЕЗ бейджей, ripple, toggle |

**Конфликт:** pipeline (engine.py → фаза 10) вызывает `generate_html_report._build_report_html()`. Это СТАРЫЙ генератор. `post_report.py` НЕ подключён к pipeline.

**Результат:** отчёты выглядят плохо. Без бейджей, без ripple, без theme toggle.

#### 2. Шрифт Inter vs Jost

- Canonical (design-showcase): **Jost** + Playfair Display
- post_report.py: **Inter** + Playfair Display (НЕПРАВИЛЬНО)
- migrate_scout_design.py: **Jost** + Playfair Display (ПРАВИЛЬНО)

post_report.py использует неправильный шрифт. Нужен канонический Jost.

#### 3. WordPress header/footer конфликт

Когда scout-пост рендерится в WordPress:
- Если через `the_content()` → wpautop ломает HTML
- Если через custom page template → может не работать с шапкой сайта

**Фикс от 1 июля:** `index.php` theme делает `echo $post->post_content; exit;` для 8-char slug постов с DOCTYPE. Это работает, но:
- ❌ НЕ выводит шапку сайта (что и нужно!)
- ✅ Правильно: scout-посты = standalone HTML, БЕЗ шапки

#### 4. SOUL.md рассинхрон

- `/opt/data/SOUL.md` (runtime): 106 KB, 1411 строк, описывает "армию AI-агентов" (устарело)
- `/opt/hermes/skills/aim/SOUL.md` (в образе): 47 KB, 760 строк, описывает "aim-operator-v4" (актуально)
- `copy_soul.sh` НЕ обновляет при наличии файла в volume

**Результат:** LLM видит смешанные инструкции. Когнитивный диссонанс.

### 🟡 ВАЖНО (не блокирует MVP, но мешает)

#### 5. PostgreSQL auth сломан

```
aim-app → postgres:5432 → InvalidPasswordError for user "aim_user"
```

- `/ready` endpoint возвращает `database: false`
- 45 таблиц создано, все пустые
- Backend endpoints (leads, sales, onboarding) падают
- **НЕ критично для MVP**: pipeline использует SQLite, а не PostgreSQL

#### 6. session_archive баг

- Логи: `[ERROR] session_archive: failed to save` (14 ошибок за pipeline прогон)
- Данные между фазами теряются
- Pipeline работает в памяти, archive = nice-to-have
- **НЕ критично**: данные восстанавливаются из state.db

#### 7. 67 tools — слишком много

- LLM путается в ассортименте
- 9 firecrawl variants, 3 scraping approaches
- Много дублирующих run_* tools
- LLM может вызвать "не тот" tool

#### 8. Двойной путь (LLM-driven vs Python-driven)

В коде два подхода одновременно:
- LLM-оркестратор (каждый tool вызывается отдельно через function calling)
- Python-driven pipeline (run_full_scout вызывает PipelineEngine)

PRESALE промпт говорит "вызови ТОЛЬКО run_full_scout", но LLM иногда всё равно вызывает отдельные tools.

#### 9. Бесконечные test_vault_* папки в корне проекта

```
test_vault/
test_vault_ads/
test_vault_campaign/
test_vault_content/
test_vault_keyword/
test_vault_seo/
test_vault_writer/
```

Это Obsidian vaults от мультиагентной задумки. Не используются, но занимают место и путают.

### 🟢 КОСМЕТИКА (не критично)

#### 10. Backup-файлы не очищены

- `backup-june24-work-20260625-160552/` (полная копия проекта)
- `hermes-backup-20260618/` (417 KB)
- 30+ `.bak` / `.backup-*` файлов в разных точках

#### 11. .venv в репо

- `/opt/aim/AIM/.venv` — 236 MB
- Дублирует Docker образ
- Замусоривает git status

#### 12. Логи без ротации

- `/opt/aim/AIM/logs/app.log` — 62 MB один файл
- `/opt/aim/AIM/logs/nginx/` — 25 MB

#### 13.aim-theme/node_modules в volume

- 15.7 MB в WordPress volume
- Должен быть только build-time, не runtime

---

## 🧟 ZOMBIE КОД (не используется, но занимает место)

### Магистры (19 файлов, ~3 MB)

`AIM/src/aim/magisters/`:
- ads_magister, content_magister, seo_magister, ai_magister, analytics_magister, intelligence_magister
- Каждый имеет 4 variant файла (v1, v2, base, custom)

**В Hermes tools НИ ОДНОГО импорта magisters.** CLAUDE.md явно говорит "Магистры deprecated".

### Субагенты (133 файла, ~5 MB)

`AIM/src/aim/subagents/`:
- CI Orchestrator (23 агента, 16 фаз — заменён на PipelineEngine)
- Множество субагентов для каждой магистры

**В Hermes tools НИ ОДНОГО импорта subagents.** Полностью мёртвый код.

### EventBus (2692 строки)

`AIM/src/aim/events/`:
- Event Bus, Event Store (event sourcing)
- Реализован, но НЕ используется ни в одном pipeline

### aim-paperclip (2.76 GB образ)

- Container работает, но что делает — неизвестно
- Внутри binary `/opt/data/bin/tirith` (22 MB)
- Михаил решил: УДАЛИТЬ (эксперимент, не нужен)

### aim-frontend (Next.js)

- Container `aim-frontend` на порту 3099
- Landing page в Next.js
- Дублирует WordPress landing
- Михаил: лендинг будет на WordPress, Next.js убрать

### meai framework (дубликат)

- `/opt/aim/src/meai` — 868 KB
- `/opt/aim/AIM/src/meai` — 820 KB
- Структура идентична
- Один не нужен

---

## 📋 ИСТОРИЯ ИЗМЕНЕНИЙ (последние 7 дней)

### 25 июня — Rollback #2 к v3.3.0
```
restore(v3.3.0): bring back SOUL.md 62K + agent_wrapper.py from commit 8b81ae5
v3.3-final: shift to redundancy philosophy
v3.3-final: activate 11 new tools + remove v7/orchestrator layer
v3.3-final: multi-turn narrative assembly infrastructure
```

### 26 июня — Cleanup
```
v3.3-final: optimize scrapers — deregister dead, document active
v3.3-final: add few-shot examples for scraper selection
chore: close Plan A++ v3.3-final iteration
feat(chat-pro): phase tracker + report preview + fallback form
```

### 27-28 июня — Phase 9 Chat Pro
```
09-01: Progress Streaming UI plan
09-02: wow-commentary generation
09-03: canonical HTML report template + WordPress publishing tool
09-04: contact collection + sales assistant
feat: Phase 09 complete - Chat Pro + Website Chat UX overhaul
feat: HeadroomGuard integration prep
```

### 29 июня — Финальный фикс (PRESALE → run_full_scout)
```
fix: increase SSE deadline from 420s to 600s
fix: replace run_prescan with run_full_scout in presale prompt ⭐
fix: SSE streaming + CI analysis + report builder (v7.1) ⭐
```

### 30 июня — Cleanup
```
feat: add deploy-hermes.sh
chore: cleanup project
```

### 1 июля (сегодня) — Privacy + Display
```
feat: scout-privacy.php v2 (sitemap, REST API, redirects)
feat: index.php raw HTML render для scout-постов
feat: hide 63 fragment/named scout постов (draft)
feat: migrate_scout_design.py (17 постов мигрировано в дизайн-систему)
```

---

## 📦 ЧТО МОЖНО ПЕРЕИСПОЛЬЗОВАТЬ (без изменений)

### API ключи и credentials

- ✅ 14 Apify keys (`APIFY_API_TOKEN` + `_01` до `_13`)
- ✅ 15 Firecrawl keys (`FIRECRAWL_API_KEY` + `_01` до `_14`)
- ✅ DeepSeek API key
- ✅ Brave Search API key
- ✅ Perplexity API key
- ✅ AssemblyAI key (для voice messages)
- ✅ Telegram bot token + API ID/Hash
- ✅ Let's Encrypt SSL сертификаты

Все ключи в `/opt/data/.env` — переезжают с сервера без изменений.

### Domain knowledge

- ✅ Список review платформ (2ГИС, Яндекс.Карты, ПроДокторов, Zoon)
- ✅ Шаблоны для gov клиник фильтрации (`competitor_matcher.py:_is_state_healthcare()`)
- ✅ Knowledge vault с историей переходов (`/opt/data/memories/`)
- ✅ 32 сессии с реальными диалогами (полезно для тестов)
- ✅ Список тестовых URLs (example.ru, iphk.ru, diamond-clinic.ru)

### Дизайн-система

- ✅ Canonical reference: `design-showcase-dual-theme.html` (2521 строка)
- ✅ CSS переменные: `theme.css`
- ✅ WordPress theme v2.1.76
- ✅ Chat Pro UI компоненты

### Инструменты (с рефакторингом)

Полезные tools, которые можно оставить:
- `run_full_scout` — точка входа
- `find_competitors` — поиск конкурентов
- `find_company_financials` — nalog.ru
- `run_tech_seo_audit` / `run_seo_audit` — SEO
- `run_lighthouse` / `run_pagespeed` — скорость
- `run_content_analysis` — контент
- `run_smi_mentions` — СМИ
- `run_forum_pains` — форумы
- `run_review_platforms` — отзывы
- `find_doctor_handles` — врачи
- `run_hh_analysis` — HeadHunter
- `publish_scout_report` — публикация (с переделкой)

Удалить как дубликаты:
- `quick_overview` (внутри run_full_scout)
- `orchestrate` (мёртвый код)
- `finalize_research` (не используется)
- `read_report_reference` (косметика)
- `run_validation_check` (встроить в pipeline)
- `quality_gate` (встроить в pipeline)
- `9 firecrawl variants` (оставить 1)
- `3 scraping approaches` (оставить 1 — firecrawl)

### Infrastructure

- ✅ Docker compose v3 (367 строк)
- ✅ Nginx config (с location блоками для /api/, /chat, /wp-content, /wp-admin)
- ✅ Prometheus + Grafana dashboards
- ✅ Monitoring stack

---

## 🎯 ГОТОВНОСТЬ К REWRITE

| Компонент | Сохранить | Рефакторить | Переписать | Удалить |
|-----------|-----------|-------------|------------|---------|
| Hermes FastAPI | ✅ | 🟡 (упрощение промптов) | — | — |
| Hermes agent_wrapper | ✅ | 🟡 (убрать multi-mode) | — | — |
| 67 tools → 20 tools | ✅ ядро | 🟡 | — | ❌ 47 дубликатов |
| PipelineEngine v7 | — | — | ✅ чистая имплементация | — |
| generate_html_report.py | — | — | ❌ УДАЛИТЬ полностью | ✅ |
| post_report.py | — | 🟡 (Inter → Jost) | ✅ Полная дизайн-система | — |
| publish_scout_report.py | ✅ логика | 🟡 (page template) | — | — |
| WordPress theme | ✅ | 🟡 (cleanup) | — | — |
| aim-app backend | — | — | — | ❌ УДАЛИТЬ |
| PostgreSQL | — | — | — | ❌ УДАЛИТЬ (SQLite хватает) |
| aim-frontend Next.js | — | — | — | ❌ УДАЛИТЬ |
| aim-paperclip | — | — | — | ❌ УДАЛИТЬ |
| Магистры + субагенты | — | — | — | ❌ УДАЛИТЬ (152 файла) |
| EventBus | — | — | — | ❌ УДАЛИТЬ |
| Monitoring stack | ✅ | — | — | — |

**Итог:** ~70% существующего кода можно переиспользовать или рефакторить. ~30% — удалить как мёртвый.

---

*Этот документ — карта текущего состояния. Любые новые измерения должны обновлять цифры.*
