# SERVER-LOCAL DIVERGENCE — КРИТИЧЕСКИЙ ОТЧЁТ

**Дата создания:** 1 июля 2026, 18:00 UTC
**Цель:** Зафиксировать расхождения между локальным репозиторием и production-сервером `aim-hermes` (контейнер на 78.17.128.169), чтобы вернуть единую истину.

---

## 📊 EXECUTIVE SUMMARY

**Состояние:** локальный репозиторий и production-сервер **рассинхронизированы критически**. Только **26 из 93 .py файлов (28%)** совпадают. Сервер был обновлён напрямую через `docker cp` без обратной синхронизации в git, а локально велись активные разработки, не дошедшие до сервера.

**Направление расхождений — двустороннее:**
- Локальный репо новее для расширенных инструментов (`run_hh_analysis`, `run_review_platforms` v2)
- Сервер новее для pipeline (`engine.py`, `generate_html_report.py`) и мелких hotfixes
- Есть файлы-сироты: существуют только с одной стороны

**Без восстановления синхронизации — любая работа рискует быть потеряна или сломать production.**

---

## 🔢 ПОЛНАЯ СТАТИСТИКА

| Категория | Количество | Процент |
|---|---|---|
| Всего .py файлов локально | 85 | — |
| Всего .py файлов на сервере | 79 | — |
| **Идентичных файлов** | 26 | 28% |
| **Различающихся файлов** | 45 | 48% |
| **Только локально** | 14 | 15% |
| **Только на сервере** | 8 | 9% |
| **Общий объём локально** | 17 458 строк | — |
| **Общий объём на сервере** | 15 357 строк | — |
| **Чистая разница (локал - сервер)** | **+2 101 строка** | — |

---

## 📁 РАЗБИВКА ПО ДИРЕКТОРИЯМ

| Директория | Diff | + Local | - Server | Комментарий |
|---|---|---|---|---|
| `app/` (root) | 3 | 2 | 0 | `main.py`, `agent_wrapper.py` и др. — критичные |
| `app/pipeline/` | 1 | 0 | **5** | 🚨 **Pipeline почти отсутствует локально** |
| `app/tools/` | 41 | 12 | 3 | Основная зона расхождений |

---

## 🚨 КРИТИЧНЫЕ НАХОДКИ

### 1. `pipeline/` почти полностью отсутствует локально

**Только на сервере:**
- `pipeline/file_guard.py` — файрвол для фаз
- `pipeline/mode_gate.py` — управление режимами
- `pipeline/test_all_phases.py` — комплексные тесты
- `pipeline/test_phase.py` — тесты фаз
- `pipeline/test_tools.py` — тесты инструментов

**Локально пустой:** `pipeline/__init__.py` (md5=d41d8cd98f00b204e9800998ecf8427e — это empty file signature). На сервере он содержит код.

**Следствие:** локально нельзя запустить pipeline тесты или отладить phases.

### 2. `tools/engine.py` — огромный файл-сирота на сервере (1641 строка)

**Только на сервере:** `tools/engine.py` (1 641 строка, 74 KB)

Это дубликат или альтернатива `pipeline/engine.py`. Существование двух engine.py — это архитектурная путаница.

### 3. `tools/generate_html_report.py` — 704 строки только на сервере

Критический инструмент генерации HTML отчётов. Локально отсутствует. Это значит — **локальная разработка не может сгенерировать отчёт**, как на production.

### 4. Stage 2/Stage 3 fact_check

- Сервер: 865 строк (Stage 2 + фиксы 1 июля)
- Локально: 1 448 строк (Stage 3 — HH/Review/SMI)
- Расхождение по format API: Stage 3 был написан под локальные v2 инструментов, а сервер использует v1 — Stage 3 не будет работать без обновления инструментов

### 5. Массовые мелкие правки +3 строк

Множество файлов на сервере имеют +3 строки (`escalate_to_manager.py`, `quick_overview.py`, `run_ads_report.py`, и т.д.). Это типичный паттерн — добавление import или одной функции без обновления локала.

---

## 📋 КАТЕГОРИИ РАСХОЖДЕНИЙ

### Категория A: Локальная версия значительно новее (нужно деплоить)

| Файл | Локал → Сервер | Что добавлено |
|---|---|---|
| `tools/run_hh_analysis.py` | 799 → 223 (+576) | 4-pass анализ с Apify, Perplexity, fallback |
| `tools/run_instagram_content.py` | 723 → 371 (+352) | Расширенный анализ Instagram |
| `tools/run_content_analysis.py` | 286 → 115 (+171) | Глубокий анализ контента |
| `tools/run_content_gaps.py` | 433 → 244 (+189) | Gap analysis с детализацией |
| `tools/_search_fallback.py` | 604 → 355 (+249) | Perplexity→Firecrawl chain |
| `tools/run_review_platforms.py` | 294 → 216 (+78) | v2 с Perplexity вместо DDG |
| `tools/web_scraper.py` | 326 → 288 (+38) | Доп. обработки |

### Категория B: Серверная версия новее (нужно подтянуть локально)

| Файл | Локал → Сервер | Природа изменений |
|---|---|---|
| `tools/escalate_to_manager.py` | 122 → 156 (+34) | Доп. логика эскалации |
| `tools/firecrawl_web.py` | 854 → 881 (+27) | Hotfix для firecrawl |
| `tools/run_prescan.py` | 522 → 517 (-5) | Рефакторинг |
| `tools/find_competitors.py` | 218 → 212 (-6) | Чистка |
| `pipeline/__init__.py` | 0 → N/A | Критично — pipeline registration |
| `pipeline/states.py` | last change 29 июня | Свежие правки |
| `agent_wrapper.py` | last change 29 июня | Свежие правки |
| `main.py` | last change 29 июня | Свежие правки |
| `tools/build_report.py` | change 1 июля | Самый свежий |

### Категория C: Файлы-сироты только локально

| Файл | Строк | Назначение |
|---|---|---|
| `tools/find_doctor_handles.py` | 1 539 | Поиск врачей (большой!) |
| `tools/run_tech_seo_audit.py` | 429 | Технический SEO аудит |
| `tools/run_media_urls.py` | 426 | Извлечение URL медиа |
| `tools/run_forum_pains.py` | 378 | Форум pains анализ |
| `tools/zai_tools.py` | 376 | ZAI integration |
| `tools/post_report.py` | 363 | Публикация отчётов |
| `tools/run_lighthouse.py` | 277 | Lighthouse runner |
| `tools/test_regalia_extraction.py` | 189 | Тест регалий |
| `tools/test_financials_dynamics.py` | 171 | Тест финансов |
| `tools/generate_report.py` | 167 | Генератор отчётов |
| `tools/read_report_reference.py` | 92 | Чтение reference |
| `tools/_file_cache.py` | 117 | Кеш файлов |
| `file_guard.py` | ? | Дублирует pipeline/file_guard.py? |
| `qc_checklist.py` | ? | QC чек-лист |

### Категория D: Файлы-сироты только на сервере

| Файл | Строк | Назначение |
|---|---|---|
| `pipeline/engine.py` | 1 641 | 🚨 Pipeline v7 ядро |
| `pipeline/file_guard.py` | ? | Файрвол фаз |
| `pipeline/mode_gate.py` | ? | Mode gate |
| `pipeline/test_all_phases.py` | ? | E2E тесты |
| `pipeline/test_phase.py` | ? | Тесты фаз |
| `pipeline/test_tools.py` | ? | Тесты инструментов |
| `tools/engine.py` | 1 641 | 🚨 Дубликат? |
| `tools/generate_html_report.py` | 704 | Генератор HTML |
| `tools/test_presale_pipeline.py` | 206 | Тесты presale |

---

## 🎯 СТРАТЕГИЯ ВОССТАНОВЛЕНИЯ

### Принцип: сервер = source of truth для **production-критичных** файлов; локал = source of truth для **новых инструментов**

### Этап 1: Восстановить pipeline локально (СРОЧНО)

**Цель:** вернуть локальному репозиторию способность запускать pipeline.

```bash
# Скопировать 5 отсутствующих pipeline файлов с сервера в локальный git
cp refactor-analysis/server-reference/app_full/app/pipeline/file_guard.py AIM/hermes/app/pipeline/
cp refactor-analysis/server-reference/app_full/app/pipeline/mode_gate.py AIM/hermes/app/pipeline/
cp refactor-analysis/server-reference/app_full/app/pipeline/test_all_phases.py AIM/hermes/app/pipeline/
cp refactor-analysis/server-reference/app_full/app/pipeline/test_phase.py AIM/hermes/app/pipeline/
cp refactor-analysis/server-reference/app_full/app/pipeline/test_tools.py AIM/hermes/app/pipeline/

# Заменить пустой __init__.py на серверный
cp refactor-analysis/server-reference/app_full/app/pipeline/__init__.py AIM/hermes/app/pipeline/__init__.py
```

### Этап 2: Вернуть generate_html_report.py и engine.py локально

```bash
# Tools, которых нет локально
cp refactor-analysis/server-reference/app_full/app/tools/engine.py AIM/hermes/app/tools/
cp refactor-analysis/server-reference/app_full/app/tools/generate_html_report.py AIM/hermes/app/tools/
cp refactor-analysis/server-reference/app_full/app/tools/test_presale_pipeline.py AIM/hermes/app/tools/
```

⚠️ **Диагностика:** `tools/engine.py` и `pipeline/engine.py` — оба существуют. Нужно разобраться, какой используется.

### Этап 3: Подтянуть серверные hotfixes локально

Для каждого файла из Категории B сделать diff и решить — нужно ли подтянуть в git.

```bash
# Пример для build_report.py (1 июля — свежий)
diff AIM/hermes/app/tools/build_report.py \
     refactor-analysis/server-reference/app_full/app/tools/build_report.py
```

### Этап 4: Зафиксировать новые локальные инструменты как "не на production"

Создать `tools/NOT_DEPLOYED.md` со списком файлов из Категории C, которые локально есть, но не на production. Это объяснит будущему мне/вам — почему они не работают.

### Этап 5: Решить судьбу Stage 3 fact_check

Текущий Stage 3 (`run_fact_check.py` 1448 строк) написан под **локальные v2** инструментов (`run_review_platforms` с Perplexity, `run_hh_analysis` с 4-pass). Сервер использует **v1** этих инструментов с другим API.

**Три варианта:**
1. **Деплоить инструменты v2 + Stage 3** вместе (риск: может сломать pipeline)
2. **Переписать Stage 3 под серверные v1** API (потеря Perplexity-функциональности)
3. **Отложить Stage 3** до обновления инструментов

---

## 🛡️ ПРАВИЛА БУДУЩЕЙ РАБОТЫ

Чтобы это не повторилось:

### Правило 1: Перед любым деплоем — синхронизировать вниз

```bash
# Встроить в скрипт auto-commit-deploy.sh
docker exec aim-hermes sh -c 'cd /opt/hermes && tar cf - app/' | \
  tar -xvf - -C refactor-analysis/server-snapshot-$(date +%Y%m%d)
```

### Правило 2: Любой docker cp ВВЕРХ идёт через git

Никогда не править файл на локали и не деплоить без git commit с описанием изменений. Ручные `docker cp` в продакшн без коммита — **запрещены**.

### Правило 3: Раз в неделю — полный diff server vs local

Создать скрипт `scripts/check-server-sync.sh` который запускает md5-сравнение и репортит расхождения.

---

## 📍 ГДЕ ЧТО НАХОДИТСЯ

| Что | Где |
|---|---|
| Этот документ | `refactor-analysis/SERVER-LOCAL-DIVERGENCE.md` |
| Полный md5 отчёт | `refactor-analysis/server-reference/divergence_full_report.txt` |
| Серверные версии (tools) | `refactor-analysis/server-reference/*.py` |
| Серверные версии (вся app/) | `refactor-analysis/server-reference/app_full/app/` |
| Backup Stage 2 | `AIM/hermes/app/tools/run_fact_check.py.bak.stage2` |
| Reference Stage 2 | `AIM/hermes/app/tools/run_fact_check.py.server-stage2-reference` |
| Результаты теста 3 сайтов | `AIM/hermes/app/tools/test_three_sites_results.json` |

---

## 📌 ОБНОВЛЕНИЕ ОТ 1 ИЮЛЯ 19:00 — ЗАВЕРШЁННЫЕ РЕШЕНИЯ

После создания этого документа были исследованы 2 "критичных" файла-сироты. Результаты:

### `tools/engine.py` (1641 строк, только на сервере) — LEGACY DUPLICATE

**Вердикт:** мёртвый код, дубликат `pipeline/engine.py`.

**Доказательства:**
- `tools/engine.py` создан **20 июня**, `pipeline/engine.py` обновлён **1 июля**
- Никакой код не делает `from app.tools.engine import` (0 упоминаний)
- Весь код использует `from app.pipeline.engine import PipelineEngine`
- Содержимое — старая версия Pipeline Engine (до refactor)

**Рекомендация:** удалить с сервера (destructive — требует подтверждения Михаила).

### `tools/generate_html_report.py` (704 строк, только на сервере) — ВОССТАНОВЛЕН

**Вердикт:** активный файл, **скопирован в локал**.

**Доказательства:**
- `tools/__init__.py:79` делает `from . import generate_html_report` → регистрирует как LLM tool
- Без этого файла **локальная установка ломается** с ImportError
- Handler `handle_generate_html_report` регистрируется через `registry.register`
- Локальный `scripts/generate_html_report.py` (430 строк, Jinja2) — это **другая экспериментальная версия**, не заменяет серверную

**Особенность:** есть **два пути** для генерации отчётов:
- **Pipeline internal:** `pipeline/engine.py:53` → `build_report.handle_generate_html_report`
- **LLM direct call:** через toolset → `generate_html_report.handle_generate_html_report`

`build_report.py` (750 строк, identical локал vs сервер) — это canonical HTML builder (Google Fonts, 14 классов). Используется в pipeline.

**Действие:** ✅ Скопирован в `AIM/hermes/app/tools/generate_html_report.py`. MD5 совпадает с сервером.

### `tools/test_presale_pipeline.py` (206 строк, только на сервере) — ЕЩЁ НЕ ИССЛЕДОВАН

Оставлен на будущее. Скорее всего smoke test для presale flow.

### Текущая статистика после восстановления

| Метрика | До | После |
|---|---|---|
| Идентичных файлов | 32 (42%) | **33 (43%)** |
| Различающихся | 44 | 44 |
| Только локально | 14 | 14 |
| Только на сервере | 3 | **2** (убрали generate_html_report) |

---

## 🎯 ОСТАЁТСЯ НЕ РЕШЁННЫМ

1. **44 различающихся файлов** — нужно для каждого индивидуальное ревью
2. **`tools/engine.py` legacy** (на сервере) — удалять или нет?
3. **`tools/test_presale_pipeline.py`** — скопировать локально или игнорировать?
4. **`scripts/generate_html_report.py`** (локальный Jinja2 эксперимент) — архивировать или развивать?
5. **14 файлов только локально** — деплоить на сервер или удалить из локала?

---

## ✅ СЛЕДУЮЩИЕ ДЕЙСТВИЯ (ПРИОРИТЕТ)

1. **🔴 СЕГОДНЯ:** Восстановить `pipeline/` файлы локально (Этап 1)
2. **🔴 СЕГОДНЯ:** Скопировать `tools/engine.py` и `tools/generate_html_report.py` (Этап 2)
3. **🟡 ЗАВТРА:** Обновить `MEMORY.md` и `CLAUDE.md` с уроком
4. **🟡 ЗАВТРА:** Создать `scripts/check-server-sync.sh`
5. **🟢 ПОТОМ:** Решить судьбу Stage 3 (после восстановления синхронизации)
6. **🟢 ПОТОМ:** Для каждой Категории B — индивидуальное ревью и коммит

---

*Этот документ — точка отсчёта для возврата к единой истине. Без этого этапа любая дальнейшая работа — это продолжение двухмесячного хаоса.*
