# Session: 2026-06-20 — Mode Gate (PRESALE tool filtering)

## Текущий фокус: Mode Gate развёрнут и верифицирован. PRESALE-режим блокирует 23 индивидуальных инструмента.

### 2026-06-20: Mode Gate — registry monkey-patch (17:00)

**Проблема:** `is_tool_allowed()` был мёртвым кодом — никогда не вызывался. LLM в PRESALE мог вызывать `run_ci_analysis` и другие индивидуальные инструменты в обход `run_full_scout`.

**Решение:** monkey-patch `registry.get_definitions()` через `apply_mode_filter()` / `remove_mode_filter()`.

**Как работает:**
1. `_create_agent()` вызывает `apply_mode_filter(mode)` перед созданием AIAgent
2. `_patch_registry_for_presale()` подменяет `registry.get_definitions` на `_filtered_definitions`
3. `_filtered_definitions` вызывает оригинал и фильтрует результат — убирает инструменты из `_ONBOARDING_BLOCKED_TOOLS`
4. AIAgent вызывает `get_definitions()` ОДИН раз при инициализации — получает отфильтрованный список
5. `remove_mode_filter()` в `finally` восстанавливает оригинал

**Файлы:**
- `AIM/hermes/app/pipeline/mode_gate.py` — 31 заблокированный инструмент + monkey-patch функции
- `AIM/hermes/app/pipeline/__init__.py` — экспорт `apply_mode_filter`, `remove_mode_filter`
- `AIM/hermes/app/agent_wrapper.py` — вызов `apply_mode_filter`/`remove_mode_filter` в `_create_agent()`

**Баг с форматом OpenAI tools (исправлен):**
- `get_definitions()` возвращает формат: `{"type": "function", "function": {"name": "...", ...}}`
- Имя лежит в `t["function"]["name"]`, а не в `t["name"]`
- `_filtered_definitions` использует `t.get("function", {}).get("name")`

**Баг с `**kwargs` (исправлен):**
- Реальная сигнатура: `get_definitions(self, tool_names: Set[str], quiet: bool = False)`
- Наша обёртка использовала несуществующие keyword-аргументы (`enabled_toolsets`, etc.)
- Исправлено: `def _filtered_definitions(*args, **kwargs)` — прозрачный проброс

**Баг с `self` (исправлен):**
- `registry.get_definitions = _filtered_definitions` — это instance attribute, не авто-биндится
- `self` не передаётся → убран из сигнатуры

**Результат (верифицировано в контейнере):**
- PRESALE: 13 инструментов (run_full_scout + CRM + отчёты)
- ADMIN: 36 инструментов (полный доступ)
- `run_ci_analysis`, `find_competitors`, `orchestrate` и ещё 20+ — ЗАБЛОКИРОВАНЫ в PRESALE
- `run_full_scout` — единственный scout-инструмент в PRESALE

### 2026-06-20: Фиксы content_gaps + publish_scout_report (14:00)

**content_gaps — параллельные DDG-запросы:**
- Было: 20 последовательных запросов → timeout 120s
- Стало: `asyncio.gather(*tasks)` — все 20 запросов одновременно → **15.9s** (7.5× быстрее)
- Файл: `AIM/hermes/app/tools/run_content_gaps.py`

**publish_scout_report — загрузка из session_archive:**
- Было: искал `data.json` в старом формате aim-scout → `Scout data not found`
- Стало: использует `session_archive.load_all_data()` → данные найдены, HTML построен
- Файл: `AIM/hermes/app/tools/publish_scout_report.py` (полный rewrite)
- WP_DB_PASSWORD пустой в контейнере → сохраняет локально (report.html)

**🔴 DDG заблокировал IP сервера (78.17.128.169):**
- `html.duckduckgo.com:443` → Connection timeout (DNS резолвится, TCP не коннектится)
- Все DDG-запросы (site: и обычные) падают мгновенно
- Произошло после 3 прогонов пайплайна (v1+v2+v3 = ~100+ DDG запросов)
- Нужен альтернативный search-провайдер или прокси

### 2026-06-20: Key Bank — завершение миграции (20:00)

**4 файла переведены с `firecrawl_key_bank` на `key_bank`:**
- `_search_fallback.py` — `key_bank.get("PERPLEXITY_API_KEY")` вместо `os.environ.get()`, Firecrawl через key_bank
- `firecrawl_web.py` — `key_bank.get_firecrawl_key()` / `key_bank.mark_firecrawl_exhausted()` вместо прямых импортов
- `run_ads_intelligence.py` — аналогично, `get_key_with_fallback` → `key_bank.get_firecrawl_key()`
- `pipeline/engine.py` — `_rotate_firecrawl_key()` использует key_bank вместо firecrawl_key_bank
- `classify_exhaustion` оставлен (чистая утилита без состояния)

**Деплой:** сервер 78.17.128.169, контейнер пересобран и перезапущен
**Верификация:** `docker logs aim-hermes | grep "Key Bank"` → "Key Bank: 11/23 active, 7 exhausted, 1 invalid, 4 unknown"

### 2026-06-20: _search_fallback — unified search с automatic provider fallback (18:00)

**Создан `AIM/hermes/app/tools/_search_fallback.py`:**
- Единый поисковый модуль: `async def search(query, max_results) -> tuple[list[dict], str]`
- Провайдеры: DDG → Firecrawl (Playwright Bing убран — anti-bot garbage)
- Все провайдеры возвращают одинаковый формат: `[{title, url, description}]`
- Каждый провайдер сам обрабатывает ошибки, возвращает `[]` при неудаче

**Текущий статус провайдеров (2026-06-20):**
| Провайдер | Статус | Причина |
|-----------|--------|---------|
| DDG | ❌ BLOCKED | IP бан (connection timeout к 40.114.177.156:443) |
| Firecrawl | ✅ ACTIVE | 10 активных ключей из 22 |
| Brave Search | ❌ EXHAUSTED | 402 — лимит $5 исчерпан |
| Playwright Bing | ❌ REMOVED | Anti-bot: возвращает мусор/spam для русских запросов |
| Playwright Yandex | ❌ REMOVED | Капча |
| SearXNG public | ❌ REMOVED | 403 |

**Мигрированы 6 инструментов с `_ddg.ddg_search` → `_search_fallback.search`:**
- ✅ `run_web_search.py` — `results, provider = await search(query, max_results)`
- ✅ `run_content_gaps.py` — параллельный `asyncio.gather`, сбор `providers_used`
- ✅ `run_review_platforms.py` — tuple unpacking после gather
- ✅ `run_smi_mentions.py` — tuple unpacking, сбор `providers_used`
- ✅ `run_hh_analysis.py` — `_search_via_ddg()` → `fallback_search`
- ✅ `web_scraper.py` — `handle_web_search()` → `fallback_search`

**Результат:** Когда DDG заблокирован, система автоматически переключается на Firecrawl. Поиск работает без перерывов. Firecrawl хватает на ~50-100 прогонов пайплайна в месяц (10 ключей × 500 credits).

**Результаты:** 13/13 фаз, 0 крашей, 9 фаз с реальными данными, 3 ошибки инструментов.

**Исправлено в v2:**
- ✅ Phase 2 (SOCIAL VERIFIER) — _ddg.py задеплоен (был ModuleNotFoundError)
- ✅ Phase 5 (SMI MENTIONS) — _ddg.py задеплоен (был ModuleNotFoundError)
- ✅ Phase 1 (TECH AUDIT) — SEO audit заработал (в v1 был transient 500)

**Оставшиеся проблемы:**
- 🔴 Phase 0 (PERPLEXITY): все 15 Firecrawl-ключей exhausted → web_search не работает
- 🔴 Phase 9 (CONTENT PLAN): run_content_gaps timeout 120s — DDG слишком медленный для 10 конкурентных запросов
- 🔴 Phase 12 (PRESENTATION): publish_scout_report не находит данные (slug/формат)

**Статистика:**
- 42 AIM tools + 15 debug tools = 57 инструментов зарегистрировано
- Perplexity: работает через fallback на DeepSeek (нет PERPLEXITY_API_KEY)
- KeyBank: 22 ключа
- FirecrawlKeyBank: 15 ключей (все exhausted после первого же прогона)

### 2026-06-20: v6 Tools Recovered + crawlee/scrapy/perplexity (сегодня)

**10 забытых v6-инструментов восстановлены:**
| Инструмент | Назначение | Статус |
|-----------|-----------|--------|
| `firecrawl_web.py` | Firecrawl scrape/search/crawl/map (4 tools) | ✅ Зарегистрирован |
| `geo_optimizer_tools.py` | GEO-аудит (AI search optimization) | ✅ Зарегистрирован |
| `orchestrate.py` | Единый оркестратор AIM-операций | ✅ Зарегистрирован |
| `quick_overview.py` | Perplexity-обзор клиники (~5s) | ✅ Зарегистрирован |
| `run_ads_intelligence.py` | Рекламная разведка Facebook + Telegram | ✅ Зарегистрирован |
| `run_aim_scout.py` | 16-фазная глубокая разведка конкурента | ✅ Зарегистрирован |
| `run_background_pipeline.py` | Фоновый пайплайн (scout → sell presentation) | ✅ Зарегистрирован |
| `run_instagram_content.py` | Instagram-анализ через Apify | ✅ Зарегистрирован |
| `run_validation_check.py` | Кросс-валидация данных (QC) | ✅ Зарегистрирован |
| `finalize_research.py` | Финализация исследования + архив + Telegram | ✅ Зарегистрирован |

**Новые инструменты (замена Brave):**
| Инструмент | Пакет | Статус |
|-----------|-------|--------|
| `crawlee_web.py` | crawlee 1.7.2 (+ Playwright) | ✅ Зарегистрирован |
| `scrapy_runner.py` | scrapy 2.16.0 | ✅ Зарегистрирован |
| `deep_research_merge.py` | (был в v7, не был в init) | ✅ Зарегистрирован |
| `firecrawl_web.py` | Firecrawl API (прямой доступ) | ✅ Уже был |
| `quick_overview.py` | Perplexity API (прямой доступ) | ✅ Восстановлен |

**Примечание:** `firecrawl-mcp-server` и `@perplexity-ai/mcp-server` не добавлены как отдельные инструменты — их функциональность уже покрыта прямыми API-интеграциями (`firecrawl_web.py` — 4 инструмента, `quick_overview.py` — Perplexity).

**Итого:** 40 AIM operations tools + 15 debug tools = 55 инструментов Hermes.

### 2026-06-20: Brave → DDG migration complete

**Brave Search удалён из всех тулов Hermes.** Заменён на DuckDuckGo HTML search (бесплатный, без API-ключа).

| Файл | До | После |
|------|----|-------|
| `run_content_gaps.py` | AIM API → Brave (402) | DDG ✅ |
| `run_review_platforms.py` | AIM API → Brave (402) | DDG ✅ |
| `run_smi_mentions.py` | AIM API → Brave (402) | DDG ✅ |
| `web_scraper.py` (web_search) | Brave Search API | DDG ✅ |
| `run_hh_analysis.py` (fallback) | Brave Search | DDG ✅ |

**Результат:** 0 зависимостей от `BRAVE_API_KEY`. Внешние API-ключи не нужны для поиска.

### 2026-06-20: 4 Tools Rewritten — AIM API → Direct Implementation (ранее)

**Проблема:** 4 инструмента Hermes вызывали AIM API эндпоинты, которых НЕ СУЩЕСТВУЕТ в aim-app:
- `run_pagespeed` → `POST /api/pagespeed/analyze` → 404
- `run_review_platforms` → `POST /api/reviews/scan` → 404
- `run_smi_mentions` → `POST /api/smi/search` → 404
- `run_content_gaps` → `POST /api/content/gaps` → 404

**Решение:** Переписал все 4 инструмента на прямую работу (без AIM API):

| Инструмент | До | После | Статус |
|-----------|-----|-------|--------|
| `run_pagespeed` | `POST /api/pagespeed/analyze` (404) | Google PageSpeed Insights API v5 напрямую | ✅ Задеплоен |
| `run_review_platforms` | `POST /api/reviews/scan` (404) | DuckDuckGo по 7 платформам напрямую | ✅ Задеплоен |
| `run_smi_mentions` | `POST /api/smi/search` (404) | DuckDuckGo по 4 категориям СМИ напрямую | ✅ Задеплоен |
| `run_content_gaps` | `POST /api/content/gaps` (404) | DuckDuckGo по 10 темам напрямую | ✅ Задеплоен |

**Дополнительные фиксы:**
- `run_pagespeed`: добавлен retry на 429 + поддержка `GOOGLE_API_KEY` из env для повышения квот
- `run_review_platforms`: исправлен баг с asyncio.gather (coroutine был вместо dict)
- `run_smi_mentions`: исправлен тот же баг с asyncio.gather

**Известные ограничения:**
- **Google PageSpeed API**: серверный IP заредейтлимичен (429). Нужен `GOOGLE_API_KEY` (бесплатный в Google Cloud Console)
- Инструменты возвращают корректный JSON с `total: 0`, когда поиск не дал результатов

### 2026-06-20: Phase Debug — All Fixes Deployed & Verified (ранее)

| Фаза | Баг | Фикс | Статус |
|------|-----|------|--------|
| Phase 0 (PRE-FLIGHT) | Firecrawl exhausted → пустые web_search | Brave Search fallback в run_web_search | ✅ Deployed |
| Phase 1 (SPEED) | engine: `website` → handler ждёт `url` | engine.py:474 `"website"` → `"url"` | ✅ Deployed |
| Phase 2 (SEO+OSINT) | AIM API 500 — `ModuleNotFoundError: meai` + `._*` files | PYTHONPATH += `/app/src` + очистка `._*` | ✅ Verified (200) |
| Phase 3 (CROSS-PLATFORM) | run_review_platforms игнорирует `company_name` | Принимает `company_name` + `city` | ✅ Deployed |
| Phase 3.2 (TELEGRAM) | web_search (как Phase 0) | Автоматически после Phase 0 | ✅ |
| Phase 3.5 (KEY PERSONS) | run_hh_analysis → 404 (нет эндпоинта) | Прямой hh.ru API + Brave fallback | ✅ Deployed |
| Phase 3.6 (SMI) | run_smi_mentions игнорирует `company_name` | Принимает `company_name` | ✅ Deployed |
| Phase 4 (COMPETITOR) | Apify keys не видны в контейнере | Volume mount fix + apify_keys.json скопирован | ✅ 2 active keys |
| Phase 5 (RATINGS) | Как Phase 3 (run_review_platforms) | Автоматически после Phase 3 | ✅ |
| Phase 6 (FINANCIAL) | ✅ Работает (381M ₽) | — | ✅ |
| Phase 7 (GAPS) | run_content_gaps игнорирует `client_site` + run_content_analysis 500 | `client_site` accepted + PYTHONPATH fix | ✅ Verified (200) |

### 2026-06-20: Revert to original v7 (PERPLEXITY Phase 0, NO Brave)

**Откат:** phases.py + engine.py → pre-293069a (13 фаз, PERPLEXITY Phase 0)
**Brave Search:** полностью удалён из run_web_search.py
**Задеплоено:** docker cp + restart aim-hermes (~10:05)

**13 фаз (original v7):**
```
Phase 0:  PERPLEXITY — web_search (Perplexity deep research)
Phase 1:  TECH AUDIT — run_pagespeed + run_seo_audit
Phase 2:  SOCIAL VERIFIER — run_review_platforms
Phase 3:  CONTENT ANALYSIS — run_content_analysis
Phase 4:  KEY PERSONS — run_hh_analysis + run_doctor_dossiers
Phase 5:  SMI MENTIONS — run_smi_mentions
Phase 6:  COMPETITORS — find_competitors + run_ci_analysis
Phase 7:  FORUM PAINS — web_search
Phase 8:  FINANCE — find_company_financials
Phase 9:  CONTENT PLAN — run_content_gaps
Phase 10: HTML BUILD — generate_html_report
Phase 11: QC CRITIQUE — LLM-only (10 пунктов)
Phase 12: PRESENTATION — publish_scout_report
```

### Дополнительные фиксы (сегодня)
- **docker-compose volume paths**: `./AIM/data` → `./data`, `./AIM/obsidian` → `./obsidian` (был двойной `AIM/AIM/`)
- **`.dockerignore`**: создан в корне проекта, исключает `._*`, `.git/`, `.env`, `node_modules/`, `__pycache__/`
- **`._*` macOS resource fork files**: удалены с хоста (555 шт.) и из контейнера (478 шт.)
- **meai import**: `PYTHONPATH=/app/AIM:/app:/app/src` — verified `meai import OK`
- **SEO audit endpoint**: `/api/seo/audit` → 200 (исправлен)
- **Content analysis endpoint**: `/api/content/analyze` → 200 (исправлен)

### Что задеплоено
- **Контейнеры:** aim-app (healthy), aim-hermes (healthy) — пересобраны ~09:49, restored ~10:05
- **13-фазный original v7:** PERPLEXITY Phase 0, Python-driven sequential
- **LLM:** DeepSeek через OMNIROUTE_URL=https://api.deepseek.com/v1
- **Brave Search:** ПОЛНОСТЬЮ УДАЛЁН из run_web_search.py
- **Apify:** 13 ключей (все active)

### Коммиты (локальные, не запушены)
- `1e7fc3e`: parameter fixes + Brave Search fallback (5 files)
- `37bd5b4`: run_hh_analysis rewrite + AIM Dockerfile PYTHONPATH (2 files)
- Несохранённые изменения: docker-compose.yml (volume paths), .dockerignore (new)

### 2026-06-20: Perplexity usage enforcement (PERPLEXITY_USED: YES|NO|N/A)

**Изменения в `engine.py` `_interpret_phase`:**
- **Prompt block**: для всех фаз кроме PERPLEXITY добавляется `PERPLEXITY_USAGE_CHECK` — LLM должен вернуть метку `PERPLEXITY_USED: YES|NO|N/A` с однострочным пояснением
- **Response parsing**: после ответа LLM извлекается метка через regex `PERPLEXITY_USED:\s*(YES|NO|N/A)`, сохраняется в `accumulated_data[f"{phase.name}_perplexity_used"]`
- **Логирование**: WARNING для NO/MISSING, INFO для YES
- **Stripping**: метка и блок PERPLEXITY_USAGE_CHECK удаляются из сохраняемого текста интерпретации

**Задеплоено:** ~10:50, Hermes healthy

### TODO
- [x] PERPLEXITY_USED enforcement (engine.py: prompt block + response parsing + logging)
- [x] Remove Brave Search — заменить на DuckDuckGo во всех тулах (web_scraper, run_hh_analysis)
- [x] Запустить тестовый прогон пайплайна на toriclinic.ru (v1 + v2)
- [x] Проверить данные всех фаз в сессии
- [x] Проверить PERPLEXITY_USED метки для каждой фазы
- [ ] Запушить коммиты в GitHub
- [ ] Новые Firecrawl ключи (15/15 exhausted — КРИТИЧЕСКИ)
- [ ] Telegram token (401 Unauthorized)
- [ ] Исправить timeout content_gaps (120s — DDG слишком медленный)
- [ ] Исправить publish_scout_report (не находит данные)
