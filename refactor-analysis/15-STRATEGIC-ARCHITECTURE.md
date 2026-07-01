# 15 — СТРАТЕГИЧЕСКАЯ АРХИТЕКТУРА AIM

**Дата:** 30 июня 2026, 18:00 UTC
**Метод:** Архитектурный анализ + проверка предположений + исторический контекст
**Длительность:** 3 часа суммарно (после тактических итераций)

---

## 🎯 ТЕЗИС

**AIM сегодня — это не "продукт", это конгломерат из 5 разных архитектур, которые Михаил построил за 2 месяца, каждая следующая наследовала код предыдущей без чистки.**

```
meAI Core (1-3 мая)          ← academic framework
  ↓
AIM Agency (3-5 мая)          ← мультиагентство
  ↓
PRESALE v3.3.0 (6-7 июня)    ← первый рабочий
  ↓
Hermes v7 (20 июня)           ← PipelineEngine
  ↓
Phase 9 Chat Pro (27 июня)    ← UX layer
```

**Каждая итерация добавляла слой, не удаляя предыдущие.** Результат: 16 контейнеров, 67 tools, 53 endpoints, 4 источника инструкций для LLM (SOUL.md + PRESALE промпт + Skills + Phase 9 prompts). Внутри — единственный рабочий путь: URL → run_full_scout → pipeline → HTML отчёт.

---

# 🔍 ЧАСТЬ 1: АНАЛИЗ 7 СТРАТЕГИЧЕСКИХ ПРОБЛЕМ

---

## Проблема #1: Идентичность продукта размыта

**SOUL.md (106 KB, runtime) описывает:**
> "Я Operator, AI-операционный директор маркетингового агентства AIM. Под капотом — армия AI-агентов (4 Magisters, 70+ субагентов)."

**PRESALE промпт (agent_wrapper.py) описывает:**
> "Ты Hermes, разведчик. Когда клиент даёт URL — вызови run_full_scout, который прогонит 13-фазный pipeline."

**Реальность:**
- Magisters и субагенты не зарегистрированы как tools
- LLM получает **обе** инструкции одновременно
- LLM может пытаться вызвать "магистра" → fail → confusion

**Архитектурный долг:** 2 года развития продуктов=identity divorced от кода.

### Решение

**Одна идентичность:**
> "AIM = чат-бот пресейла для медицинских клиник. Захват URL → 13-фазный pipeline → HTML отчёт. Цель: продать платную консультацию Михаилу."

Удалить из SOUL.md всё упоминание магистров/субагентов/Operator. SOUL.md = canonical identity, не более.

---

## Проблема #2: Слоистая архитектура избыточна и дублирующая

**Текущие 16 контейнеров:**

```
Client
  ↓
aim-nginx (1) — TLS termination
  ↓
aim-wordpress (2) — CMS, landing, chat
  ↓
aim-frontend (3) — Next.js (почти не используется)
  ↓
aim-hermes (4) — LLM orchestrator + tools wrappers
  ↓
aim-app (5) — реальная бизнес-логика
  ↓
aim-postgres (6) — БД (не используется в pipeline)
aim-mysql (7) — WordPress DB
aim-redis (8) — cache
aim-paperclip (9) — unknown (2.76 GB)
aim-prometheus, aim-grafana, aim-alertmanager, aim-node-exporter, aim-postgres-exporter (10-14)
aim-headroom-proxy (15) — НЕ существует (только в docs)
  ↓
External APIs (16): DeepSeek, Apify, Firecrawl, etc.
```

### Анализ каждого слоя

**aim-nginx** ✅ нужен (routing, TLS)
**aim-wordpress** ✅ нужен (CMS, landing, chat UI)
**aim-frontend** ❌ НЕ нужен (landing уже в WordPress)
**aim-hermes** ✅ нужен (LLM, tool registry)
**aim-app** ✅ нужен (бизнес-логика, БД), но 70% endpoints не используется
**aim-postgres** ❌ НЕ нужен (SQLite достаточно для текущей нагрузки 46 чатов/24h)
**aim-mysql** ✅ нужен (WordPress DB)
**aim-redis** ✅ нужен (cache + очереди)
**aim-paperclip** ❌ НЕ нужен (решение Михаила — удалить)
**aim-monitoring (5 контейнеров)** ⚠️ опционально, можно оставить
**aim-headroom-proxy** ❌ НЕ существует (просто удалить docs)

### Решение

**С 16 до 8-9 контейнеров:**
```
aim-nginx
aim-wordpress + aim-mysql (WordPress + DB)
aim-hermes (LLM orchestrator)
aim-app (business logic) + aim-redis (cache)
aim-prometheus + aim-grafana (monitoring, optional)
```

Убрать: aim-frontend, aim-paperclip, aim-postgres, aim-headroom, postgres-exporter, node-exporter.

---

## Проблема #3: 67 Tools при реальной потребности в 15-20

**Из аудита: tools вызывают 16 aim-app endpoints.** Pipeline (run_full_scout) внутри вызывает хендлеры через _TOOL_HANDLERS (engine.py:54-83).

### Категории tools и их реальная необходимость

**Pipeline-core (нужны):** ~14 шт
- run_full_scout (главный)
- find_competitors, run_ci_analysis
- run_seo_audit, run_tech_seo_audit (внутренний)
- run_content_analysis, run_content_gaps
- run_lighthouse, run_pagespeed, run_validation_check
- run_review_platforms, run_smi_mentions
- run_doctor_dossiers, run_hh_analysis
- find_company_financials

**CRM (не нужны сейчас):** ~7 шт
- collect_contact, qualify_lead, escalate_to_manager
- show_all_leads, get_lead_pipeline, show_project_status
- update_knowledge

**Scraping (избыточны):** ~13 шт
- 9 firecrawl_*, 2 crawlee_*, scrapy_crawl, web_scraper, bitrix_scraper
- LLM не должен видеть все 13 — должен видеть 1 canonical

**Search (избыточны):** ~5 шт
- web_search, _ddg, _search_fallback, perplexity_search, perplexity_deep_analyze
- Достаточно 2: web_search + perplexity_search

**File ops:** ~3 шт (file_read, file_write, generate_html_report)
**System:** ~5 шт (shell_exec, restart_myself, pip_install, etc.)
**Telegram:** 3 шт (если нужен Telegram bot)
**External:** aim-scout, present_competitors, publish_scout_report, post_report, read_report_reference, quick_overview, finalize_research, orchestrate, run_background_pipeline

### Решение

**С 67 до ~20 LLM-visible tools:**

LLM видит:
1. run_full_scout (главный, запускает всё)
2. collect_contact (финальный capture)
3. update_knowledge (опционально)
4. publish_scout_report (финальный публикатор)

**Скрыть от LLM** (используются только внутри PipelineEngine):
- Все отдельные run_*, find_*

**Зарезервировать для debug/admin:**
- shell_exec, file_read, restart_myself (только в ADMIN mode)

---

## Проблема #4: 3 источника инструкций для LLM

Сегодня LLM получает:
1. **SOUL.md** (106 KB) — identity, catalog, поведение
2. **Mode prompt** (PRESALE/ACTIVE/ADMIN, ~5 KB) — правила режима
3. **Skills** (5 шт, каждая 5-50 KB) — узкие промпты для задач
4. **Phase 9 prompts** — UX layer (chat inline pro)

Итого ~150-200 KB системного промпта = 50K+ токенов перед каждым запросом.

**Проблемы:**
- Источники конфликтуют (SOUL.md = Operator, PRESALE = Hermes)
- LLM не знает кто прав
- Дорого (50K токенов × 46 чатов = 2.3M токенов/день только на системный промпт)

### Решение

**Один canonical промпт:**

1. **SOUL.md** = единственный источник identity + catalog + поведения. ~30 KB.
2. **Mode prompt** удалён, слит в SOUL.md.
3. **Skills** упрощены — оставить только `aim-scout` (если pipeline нужно объяснить детально).
4. **Phase 9 prompts** — отдельная история (UX, не LLM).

---

## Проблема #5: Публикация отчётов — архитектурно неправильно

**Сегодня:** HTML вставляется в `wp_posts.post_content` через SQL INSERT. WordPress применяет `wpautop` → HTML ломается.

**Корневая проблема:** Использование WordPress как backend для отчётов — костыль. WordPress = CMS для редактируемого контента (страницы, посты), а не для автоматической публикации HTML.

### Архитектурные варианты

**Вариант A: Nginx direct file serving (минимум)**
- HTML сохраняется в `/opt/data/reports/{slug}.html`
- Nginx: `location /reports/ { root /opt/data; }`
- URL: `https://iamaim.ru/reports/{slug}`
- ✅ Просто, быстро, без PHP
- ❌ Нет metrics, нет auth

**Вариант B: Отдельный micro-service (правильнее)**
- Контейнер `aim-reports` (Python FastAPI)
- Хранит HTML + metadata в SQLite
- Отдаёт по URL `https://reports.iamaim.ru/{slug}` или `/reports/{slug}`
- ✅ Полный контроль, metrics, future auth
- ❌ Ещё один контейнер

**Вариант C: WordPress custom template (быстрый фикс)**
- Файл `page-scout-report.php`, `echo post_content` без фильтров
- ✅ Быстро (1 час)
- ❌ Остаются зависимости от WordPress (миграции, фильтры, кеш)

### Решение

**Стратегически правильно = Вариант A** (простота, минимум движущихся частей).

**Тактически (для быстрого MVP) = Вариант C** (быстрый фикс), потом мигрировать на A.

---

## Проблема #6: aim-app перегружен (70% не используется)

**Текущее состояние aim-app:**
- 53 REST endpoints
- 45 таблиц PostgreSQL (все пустые)
- 134 Python файла в `src/aim/`
- 19 magisters + 133 subagents (deprecated)
- EventBus (4 строки в БД за 2 месяца)

**Реально используются:**
- 16 endpoints из 53
- Tools: find_competitors, run_ci_analysis, run_seo_audit, etc.
- Apify, Firecrawl, DaData, nalog.ru интеграции
- Prescan orchestrator

### Решение

**Из aim-app удалить:**
- ❌ Все magisters/subagents (152 файла)
- ❌ EventBus + tables
- ❌ `/api/onboarding/*` (6 endpoints, не используется)
- ❌ `/api/analytics/*` (5 endpoints, не используется)
- ❌ `/api/email/*` (2 endpoints)
- ❌ `/api/gdpr/*` (1 endpoint)
- ❌ `/api/sales/*` (если не делаем CRM)
- ❌ PostgreSQL целиком (всё в SQLite)
- ❌ CI orchestrator (23 агента)

**Оставить в aim-app:**
- ✅ /api/competitors/* (разведка)
- ✅ /api/seo/* (аудит)
- ✅ /api/content/* (контент-анализ)
- ✅ /api/presale/* (prescan)
- ✅ /api/companies/* (финансы)
- ✅ /api/ads/* (отчёты)

**Результат:** aim-app уменьшается с 53 до 16 endpoints, с 134 до ~50 файлов.

---

## Проблема #7: Деплой и обновления хаотичны

**Сегодня:**
- `docker cp file aim-hermes:/path && docker restart aim-hermes` — hotfixes
- `docker-compose build hermes && docker-compose up -d hermes` — для重构
- `deploy-hermes.sh` — недавний скрипт (30 июня)
- `auto-commit-deploy.sh` — protection от потери изменений
- `copy_soul.sh` — копирует SOUL.md с условием (баг)

**Проблемы:**
- SOUL.md "застревает" в volume (копируется только если новее)
- Backup-файлы накапливаются (main.py.backup-phase09-*)
- 4 docker-compose файла (главный + 3 backups/overrides)
- Нет CI/CD

### Решение

**Принципы деплоя:**
1. Git = единственный источник кода
2. Любой hotfix = commit + push + ssh + git pull + docker restart
3. Никаких `docker cp` файлов в обход git
4. `copy_soul.sh` всегда копирует (без условия)
5. Один canonical compose файл

---

# 🏗️ ЧАСТЬ 2: ЦЕЛЕВАЯ АРХИТЕКТУРА

---

## Видение продукта (одна фраза)

> **AIM = AI-чат на iamaim.ru. Клиент-владелец клиники пишет URL → через 5-8 минут получает ссылку на HTML-отчёт с анализом конкурентов, рынка, своих слабых мест и рекомендациями AIM.**

## Минимальная архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                     Internet / iamaim.ru                     │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│              aim-nginx (routing + TLS)                       │
│  - /  → aim-wordpress                                        │
│  - /api/chat → aim-hermes                                    │
│  - /reports/ → filesystem (Nginx direct serve)               │
└──────────────────────────────┬──────────────────────────────┘
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
       ┌──────────────┐ ┌──────────┐ ┌──────────────┐
       │ aim-wordpress │ │aim-hermes│ │ /opt/data/   │
       │  + aim-mysql  │ │  (FastAPI│ │ reports/     │
       │               │ │   + LLM  │ │ *.html       │
       │  - Landing    │ │  + tools)│ │              │
       │  - Chat UI    │ │          │ │              │
       │  - 90 pages   │ │  1 tool: │ │              │
       │               │ │  run_full│ │              │
       └──────────────┘ │  _scout  │ └──────────────┘
                        │  + 5 CRM │
                        └─────┬────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │   aim-app       │
                     │   (FastAPI)     │
                     │                 │
                     │  16 endpoints:  │
                     │  - competitors  │
                     │  - seo          │
                     │  - content      │
                     │  - presale      │
                     │  - companies    │
                     │  - ads          │
                     │                 │
                     │  + aim-redis    │
                     └────────┬────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │   External APIs │
                     │  - DeepSeek     │
                     │  - Apify (14)   │
                     │  - Firecrawl(15)│
                     │  - Perplexity   │
                     │  - DaData       │
                     │  - nalog.ru     │
                     │  - Brave Search │
                     │  - AssemblyAI   │
                     └─────────────────┘
```

## Компоненты (8 контейнеров, 4 GB места)

| Контейнер | Образ | Назначение |
|---|---|---|
| aim-nginx | nginx:alpine (94 MB) | TLS, routing |
| aim-wordpress | wordpress:php8.2-fpm (431 MB) | CMS + landing + chat |
| aim-mysql | mariadb:11 (458 MB) | WordPress DB |
| aim-hermes | aim-hermes:latest (3.21 GB) | LLM orchestrator |
| aim-app | aim:latest (3.13 GB) | Business logic |
| aim-redis | redis:7-alpine (58 MB) | Cache |
| aim-prometheus | prom/prometheus (593 MB) | Metrics (optional) |
| aim-grafana | grafana/grafana (1.47 GB) | Dashboard (optional) |

**Удалить (по сравнению с текущим):**
- ❌ aim-frontend (281 MB) — landing в WordPress
- ❌ aim-paperclip (2.76 GB) — unknown
- ❌ aim-postgres (396 MB) — SQLite достаточно
- ❌ aim-headroom-proxy (нет контейнера, только docs)
- ❌ aim-postgres-exporter, aim-node-exporter, aim-alertmanager — optional

**Экономия:** ~3.4 GB образов + 1 контейнер в runtime.

## Data Flow (правильный путь)

```
1. Client открывает iamaim.ru
2. Nginx → aim-wordpress → front-page.php (с chat-inline)
3. Client пишет URL в чат
4. chat-inline.js → /api/chat (Nginx → aim-hermes)
5. aim-hermes → AIAgent.run_conversation(message, tools)
6. LLM видит 5 tools: run_full_scout, collect_contact, publish_scout_report, update_knowledge, web_search
7. LLM вызывает run_full_scout(url)
8. run_full_scout → PipelineEngine.execute()
9. PipelineEngine прогоняет 13 фаз, каждая → aim-app endpoint
10. aim-app → Apify/Firecrawl/DaData → данные
11. PipelineEngine сохраняет данные в /opt/data/sessions-archive/{hash}/data/
12. После всех фаз → generate_html_report → HTML файл (45 KB)
13. publish_scout_report → сохраняет HTML в /opt/data/reports/{slug}.html
14. URL возвращается в JSON → LLM → клиент
15. Client открывает https://iamaim.ru/reports/{slug}
16. Nginx отдаёт HTML напрямую (без PHP, без wpautop)
17. Client видит красивый отчёт
```

**Время end-to-end:** 5-8 минут.
**Точек отказа:** 4 (LLM, aim-app, внешние API, Nginx).

---

# 🛣️ ЧАСТЬ 3: ПУТЬ ЭВОЛЮЦИИ (6-12 МЕСЯЦЕВ)

---

## Этап 0: СЕГОДНЯ — Точечный фикс (1-2 часа)

**Что сделать:**
- Custom page template `page-scout-report.php` (тактический фикс WordPress wpautop)
- Smoke test: https://iamaim.ru/gkzrghmz → должна быть красивая страница

**Результат:** Клиент видит красивый отчёт. **MVP functional.**

**STOP criterion:** старый отчёт gkzrghmz отображается как страница (не код).

---

## Этап 1: СТАБИЛИЗАЦИЯ (1-2 недели)

**Цель:** закрепить MVP, удалить criticalмусор.

**Задачи:**
1. Удалить aim-paperclip + tirith binary (-2.8 GB)
2. Удалить aim-frontend (-281 MB, если landing на WordPress)
3. Починить session_archive баг (10 минут)
4. Обновить SOUL.md — убрать упоминания магистров/Operator
5. Обновить CLAUDE.md — 67 tools → ~20, 16 контейнеров → 8
6. Создать `docs/CURRENT-STATE.md` — canonical описание

**Критерий успеха:** 2 недели без регрессий, 5+ успешных pipeline прогонов на реальных клиентах.

---

## Этап 2: АРХИТЕКТУРНЫЙ CLEANUP (1-2 месяца)

**Цель:** упростить архитектуру, удалить deprecated код.

**Задачи:**
1. Удалить aim-postgres → миграция на SQLite для всего
2. Удалить из aim-app:
   - Все magisters (19 файлов)
   - Все subagents (133 файла)
   - EventBus
   - Неиспользуемые endpoints (37 шт)
3. Сократить tools с 67 до ~20 LLM-visible
4. Объединить SOUL.md + mode prompts в один canonical промпт (~30 KB)
5. Мигрировать отчёты: WordPress INSERT → Nginx direct serve
6. Удалить obsidian vaults (28 из 30)

**Критерий успеха:** Codebase ~50% меньше, все ещё работает.

---

## Этап 3: PRODUCT GROWTH (3-6 месяцев)

**Цель:** добавить features на чистую архитектуру.

**Возможные направления (выбор Михаила):**
- A. Telegram sales bot (если нужен доп. канал)
- B. CRM (если появились клиенты и нужно вести сделки)
- C. Multi-niche (расширить с пластики на стоматологию, косметологию, etc.)
- D. Subscription model (платный доступ к глубоким отчётам)
- E. API для партнёров (если B2B2C)

**Принцип:** добавлять только когда бизнес-потребность подтверждена.

---

## Этап 4: SCALE (6-12 месяцев)

**Цель:** горизонтальное масштабирование, если будет рост.

**Только если:**
- 100+ клиентов в день
- Несколько серверов
- Команда разработчиков

**Возможное:**
- CI/CD pipeline (GitHub Actions)
- Multi-server deployment (Docker Swarm / Kubernetes)
- Analytics dashboard
- A/B testing

**Не делать раньше необходимости.**

---

# 💡 ЧАСТЬ 4: КЛЮЧЕВЫЕ АРХИТЕКТУРНЫЕ ПРИНЦИПЫ

---

## Принцип 1: Single Source of Truth

**Принцип:** Для каждого аспекта системы — один canonical источник.

| Аспект | Источник |
|---|---|
| Identity LLM | SOUL.md (только) |
| Каталог tools | SOUL.md (только) |
| Поведение LLM | SOUL.md (только) |
| Код | git (только) |
| Конфигурация env | .env.production (только) |
| Состояние сессий | state.db (только) |
| Отчёты | /opt/data/reports/*.html (только) |

**Удалить:** mode prompts (слить в SOUL.md), дубликаты (meai в 2 местах), backup-файлы.

---

## Принцип 2: LLM-First, но не LLM-Only

**Принцип:** LLM решает что делать, Python гарантирует как.

- LLM выбирает: "вызову run_full_scout для этого URL"
- Python гарантирует: "если run_full_scout вызван — 13 фаз пройдут последовательно"

**Не делать:**
- LLM принимает решения внутри pipeline (медленно, ненадёжно)
- Python решает какой tool вызвать (потеря гибкости)

---

## Принцип 3: Simple Before Smart

**Принцип:** каждый компонент делает одну вещь, хорошо.

- aim-nginx — routing
- aim-wordpress — CMS
- aim-hermes — LLM orchestration
- aim-app — business logic
- aim-redis — cache

**Не делать:**
- aim-app с embedded LLM
- aim-hermes с PostgreSQL
- aim-wordpress с backend logic (кроме necessary endpoints)

---

## Принцип 4: Delete Over Fix

**Принцип:** если код не используется — удалить, не чинить.

- 37 неиспользуемых aim-app endpoints → удалить
- 47 неиспользуемых tools → скрыть от LLM
- 152 файла магистров → удалить
- EventBus → удалить

**Исключение:** данные (state.db, sessions-archive) — не удалять без backup.

---

## Принцип 5: Git is the Deploy

**Принцип:** состояние на сервере = состояние в git (main branch).

- Любое изменение → commit → push → ssh aim → git pull → restart
- Никаких `docker cp` в обход git
- Никаких backup-файлов (всё в git history)

---

# 🎯 ЧАСТЬ 5: ЧТО ДЕЛАТЬ ПРЯМО СЕЙЧАС

---

## Главная рекомендация

**Не начинать с тактического фикса.** Начать с **архитектурного решения**.

### Шаг 1 (сегодня, 1 час): Зафиксировать видение

**Действие:** Прочитать этот документ. Согласиться или оспорить видение.

**Вопросы для Михаила:**
1. Согласен ли, что AIM = "чат пресейла + HTML отчёт" (не мультиагентство)?
2. Согласен ли упростить до 8 контейнеров?
3. Согласен ли перенести отчёты с WordPress INSERT на Nginx direct serve?
4. Согласен ли с этапами 0-4?

### Шаг 2 (завтра, 1-2 часа): Точечный фикс для MVP

**Действие:** Custom page template в WordPress (тактический fix).

**Цель:** Клиент видит красивый отчёт сегодня/завтра.

### Шаг 3 (1-2 недели): Этап 1 стабилизация

**Действие:** Удалить criticalмусор (paperclip, frontend, починить баги).

### Шаг 4 (1-2 месяца): Этап 2 архитектурный cleanup

**Действие:** Упростить до минимума, обновить документы.

---

# ⚠️ ГЛАВНОЕ ОТЛИЧИЕ ОТ ПРЕДЫДУЩИХ РЕКОМЕНДАЦИЙ

**Предыдущие рекомендации (мои ошибки):**
- План на 10 дней (детальный, неверный)
- План на 3-5 часов (тактический, без контекста)
- План на 1-2 часа (одно действие, без стратегии)

**Эта рекомендация:**
- Архитектурное видение продукта
- Путь эволюции на 6-12 месяцев
- Чёткие принципы для будущих решений
- Конкретные шаги СЕГОДНЯ + план на 1-2 месяца

**Разница:** Я не говорю "что починить". Я говорю "какая система должна быть". Фикс WordPress — это тактика в рамках стратегии, не стратегия.

---

# 📋 ИТОГ

**Сегодня AIM — это:**
- Конгломерат из 5 архитектур
- 16 контейнеров (нужно 8)
- 67 tools (нужно ~20)
- 53 endpoints (нужно 16)
- 3 источника инструкций (нужен 1)

**Через 6 месяцев AIM должен быть:**
- Чёткий продукт (чат пресейла + HTML отчёт)
- 8 контейнеров
- ~20 LLM-visible tools
- 16 aim-app endpoints
- 1 canonical SOUL.md
- Простая публикация отчётов (Nginx direct)

**Путь:** Этап 0 (фикс) → Этап 1 (стабилизация) → Этап 2 (cleanup) → Этап 3 (growth).

**Сегодняшний шаг:** Согласовать видение (этот документ). Потом — тактический фикс.

---

*Этот документ — стратегический анализ. Любые тактические решения должны соответствовать этим принципам.*
