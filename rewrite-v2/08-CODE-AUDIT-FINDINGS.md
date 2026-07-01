# 08 — АУДИТ КОДА (1 июля 2026)

**Статус:** Частичный (2 из 4 аудитов завершены)
**Принцип:** Только факты из кода

---

## 🚨 КРИТИЧНЫЕ НАХОДКИ

### 1. Canonical reference НЕ там где CLAUDE.md говорит

- **CLAUDE.md указывает:** `AIM/wordpress-core/wp-content/themes/aim-theme/design-showcase-dual-theme.html`
- **Реально:** `/Users/mikhaileliseev/Desktop/Dev/meAI_1/AIM/frontend/design-showcase-dual-theme.html` (2513 строк)

Все документы в rewrite-v2/ содержали **неправильный путь**.

### 2. `generate_html_report.py` НЕ подключает шрифты Google Fonts

Это и есть **главная причина хаоса**:

```python
# В CSS есть переменные:
--font-heading: 'Playfair Display', Georgia, serif;
--font-body: 'Jost', -apple-system, sans-serif;
```

**НО:** в файле нет ни `<link>`, ни `@import url(...fonts.googleapis...)`.

**Результат:** у пользователей без локальных Jost/Playfair — fallback на `-apple-system`/`Georgia`. Шрифт СЛУЧАЙНЫЙ. Отсюда «разнородные отчёты».

### 3. `generate_html_report.py` (актуальный в pipeline) — только 1 из 14 canonical классов

Только `.cta-box`. **НЕТ:**
- `.glass-card`, `.glass-stat`
- `.metric-tag-green/red/yellow/blue/gray`
- `.surface-block-green/red`
- `.glass-table-wrap`
- `.theme-toggle`
- `.ripple`
- `.sec-tag`

### 4. `post_report.py` использует Inter (НЕ canonical)

```
canonical:  Jost + Playfair Display
post_report: Inter + Playfair Display ← НЕПРАВИЛЬНО
```

### 5. `generate_html_report_v7_backup.py` — МЁРТВЫЙ КОД

903 строки, никем не импортируется.

---

## 📊 PipelineEngine — РЕАЛЬНОЕ состояние

### Фаз: 13 (НЕ 16, НЕ 15)

| ID | Имя | Tools | LLM интерпретация |
|----|-----|-------|-------------------|
| 0 | PERPLEXITY | perplexity_search | ✅ |
| 1 | COMPETITORS | find_competitors, run_ci_analysis | ✅ |
| 2 | TECH AUDIT | run_pagespeed, run_seo_audit | ✅ |
| 3 | SOCIAL VERIFIER | run_review_platforms | ✅ |
| 4 | CONTENT ANALYSIS | run_content_analysis | ✅ |
| 5 | KEY PERSONS | run_hh_analysis, run_doctor_dossiers | ✅ |
| 6 | SMI MENTIONS | run_smi_mentions | ✅ |
| 7 | FORUM PAINS | web_search | ✅ |
| 8 | FINANCE | find_company_financials | ✅ |
| 9 | CONTENT PLAN | run_content_gaps | ✅ |
| 10 | HTML BUILD | **generate_html_report** | ❌ (Python only) |
| 11 | QC CRITIQUE | (none, LLM only) | ✅ |
| 12 | PRESENTATION | **publish_scout_report** | ❌ |

### LLM НЕ генерирует HTML напрямую

Архитектура гибридная:
- LLM пишет `_interpretation` поля (markdown текст)
- Python (`generate_html_report._build_report_html`) собирает HTML из этих полей
- В самой фазе 10 LLM **НЕ вызывается** (`llm_interpret=False`)

**Это хорошо.** Значит проблема НЕ в том что «LLM забывает canonical». Проблема в том что **`generate_html_report.py` не canonical**.

---

## ⚠️ DEAD CODE / БАГИ

### 1. `_extract_key_findings` всегда возвращает пустой список

`run_full_scout.py:271-277` ищет в accumulated_data ключи:
- `"PRE-FLIGHT"`, `"COMPETITOR MATRIX"`, `"GAPS & ADVANTAGES"`, `"FINANCIAL: FNS+"`, `"RATINGS & REVIEWS"`

**Но этих имён фаз НЕТ в PHASES list** (там: PERPLEXITY, COMPETITORS, ...).

**Результат:** `key_findings` в финальном ответе всегда `[]`.

### 2. `KeyExhaustionError` и `PhaseTimeoutError` — недостижимы

Определены, но нигде не `raise`. Соответствующие `except` ветки — dead code.

### 3. `file_guard.py` отсутствует локально

`engine.py:26` импортирует `from .file_guard import get_key_rotator`, но файла нет в `app/pipeline/`. Возможно на сервере, но в локальном репо ImportError.

### 4. `PHASE_0_PREFLIGHT` определена, но НЕ включена в PHASES

`phases.py:53-65` определяет pre-flight фазу с `on_permanent_failure="abort"`, но в `PHASES` списке (phases.py:437-451) её нет. Мёртвая декларация.

### 5. `placeholder_post_id` / `placeholder_page_url` не в dataclass

`engine.py:285-286` добавляет атрибуты к PipelineState, которых нет в определении. Python позволяет, но грязно.

---

## 📋 ТАБЛИЦА ГЕНЕРАТОРОВ

| Генератор | Шрифт | Canonical классы | Google Fonts | В pipeline? | Строк |
|-----------|-------|------------------|--------------|-------------|-------|
| `generate_html_report.py` | Jost+Playfair (только в vars) | 1/14 (`.cta-box`) | ❌ НЕ подключает | ✅ Phase 10 | 698 |
| `generate_html_report_v7_backup.py` | (нет) | 1/14 (`.surface-block`) | ❌ | ❌ Мёртвый | 903 |
| `post_report.py` | **Inter**+Playfair | 2/14 (`.cta-box`, `.ripple`) | ✅ `@import` | ❌ Отдельный path | 363 |
| `/tmp/migrate_scout_design.py` | Jost+Playfair | 5/14 | ✅ `<link>` | ❌ One-shot | 508 |
| **canonical** (frontend/) | **Jost+Playfair** | **14/14** | ✅ `<link>` | — | 2513 |

---

## 🔄 ВЫЗОВ В PIPELINE

Точная цепочка:

```
run_full_scout(url)
  → PipelineEngine.execute()
    → Phase 0-9: собирают данные, LLM интерпретирует
    → Phase 10 (HTML BUILD):
        engine.py:748 → _persist_session_to_disk(state)
        engine.py:579 → handler = generate_html_report.handle_generate_html_report
        engine.py:585 → result = await handler(session_hash, title, client_name, client_url)
        generate_html_report.py:567 → data = load_all_data(session_hash)  # читает с диска
        generate_html_report.py:579 → html = _build_report_html(data, title)
    → Phase 11 (QC): LLM проверяет
    → Phase 12 (PRESENTATION):
        publish_scout_report.py:107 → from generate_html_report import _build_report_html
        publish_scout_report.py:111 → html = _build_report_html(data, title)  # ЕЩЁ РАЗ
        publish_scout_report.py:132 → pymysql.connect()
        publish_scout_report.py:143 → cur.execute("INSERT INTO wp_posts...")
```

**Двойной вызов генератора:** и в Phase 10, и в Phase 12.

---

## 🎯 ЧТО ИЗМЕНИЛОСЬ В МОЁМ ПЛАНЕ

### Было в плане (до аудита):

> LLM генерирует HTML и забывает canonical → нужен build_report.py чтобы LLM не генерил HTML

### Стало после аудита:

**LLM УЖЕ не генерирует HTML.** Python (`generate_html_report.py`) собирает HTML.

**Реальная проблема:** `generate_html_report.py` просто **не canonical** — нет шрифтов, нет классов, нет theme toggle, нет ripple.

### Обновлённый план

**Шаг 1:** Создать `build_report.py` с canonical:
- Скопировать CSS из `AIM/frontend/design-showcase-dual-theme.html` (НЕ из CLAUDE.md пути)
- `<link>` на Google Fonts (Playfair Display + Jost) — ОБЯЗАТЕЛЬНО
- Все 14 canonical классов
- Theme toggle + ripple + бейджи

**Шаг 2:** Заменить вызов в engine.py:748 + publish_scout_report.py:107.

**Шаг 3:** Удалить:
- `generate_html_report.py` (698 строк)
- `generate_html_report_v7_backup.py` (903 строки мёртвого кода)
- Опционально `/tmp/migrate_scout_design.py`

**Шаг 4:** (бонус) Починить `_extract_key_findings` в run_full_scout.py:271 — заменить устаревшие имена фаз.

---

## ❓ ЧТО ОСТАЛОСЬ НЕ ПРОВЕРЕНО

Два агента были прерваны / провалились:

1. **WordPress theme audit** — прерван пользователем
   - Не проверено: какие именно PHP файлы в теме, что в index.php, scout-privacy.php, theme.css
   - Не проверено: где chat UI

2. **Hermes tools audit** — провалился (rate limit)
   - Не проверено: сколько РЕАЛЬНО tools зарегистрировано
   - Не проверено: что в SOUL.md
   - Не проверено: какие tools мёртвые

---

## ✅ ХИРУРГИЯ — ШАГ 1: CANONICAL BUILD_REPORT.PY (1 июля 2026, 08:20 UTC)

**Создан:** `AIM/hermes/app/tools/build_report.py` (795 строк)

**Что внутри:**
- ✅ Google Fonts через `<link>` (Playfair Display + Jost)
- ✅ Все 14 canonical классов:
  - `.metric-tag-{green,yellow,red,blue,gray}` + `.metric-tag-dot`
  - `.surface-block`
  - `.card-glass` + `.glass-stat` + `.glass-stats-wrap` + `.glass-table-wrap`
  - `.cta-box` + `.btn-primary`
  - `.sec-tag`
  - `.theme-toggle` (с localStorage persistence)
  - `.water-ripples` + `.ripple-ring` (только light theme)
- ✅ Dual theme CSS (light/dark) с переменными
- ✅ Animations: `card-breathe`, `glass-glow`, `water-ripple`
- ✅ Theme toggle JS с localStorage (`aim-theme`)
- ✅ Responsive (@media max-width: 768px)

**Референс:** `AIM/frontend/design-showcase-dual-theme.html` (строки 1-1043, полный CSS)

**Функции:**
- `build_report_html(data: dict, title: str) -> str` — генератор HTML
- `handle_generate_html_report(...)` — async handler для pipeline

## ✅ ХИРУРГИЯ — ШАГ 2: ЗАМЕНА ВЫЗОВОВ (1 июля 2026, 08:22 UTC)

**Изменено 3 файла:**

1. **`AIM/hermes/app/pipeline/engine.py:53`**
   ```python
   # Было:
   "generate_html_report": ("app.tools.generate_html_report", "handle_generate_html_report"),

   # Стало:
   "generate_html_report": ("app.tools.build_report", "handle_generate_html_report"),
   ```

2. **`AIM/hermes/app/tools/publish_scout_report.py:107`**
   ```python
   # Было:
   from app.tools.generate_html_report import _build_report_html
   html = _build_report_html(data, title)

   # Стало:
   from app.tools.build_report import build_report_html
   html = build_report_html(data, title)
   ```

3. **`AIM/hermes/app/tools/build_report.py`** — создан с нуля (795 строк)

## ✅ ХИРУРГИЯ — ШАГ 3: УДАЛЕНИЕ МЁРТВОГО КОДА (1 июля 2026, 08:23 UTC)

**Удалено 2 файла (1601 строка):**

1. `AIM/hermes/app/tools/generate_html_report.py` — 698 строк
   - Только 1/14 canonical классов (`.cta-box`)
   - Нет Google Fonts подключения
   - Шрифты fallback на `-apple-system`/`Georgia`

2. `AIM/hermes/app/tools/generate_html_report_v7_backup.py` — 903 строки
   - Никем не импортируется
   - Полностью мёртвый код

**Результат:**
- **До:** 698 + 903 = 1601 строка некачественного кода
- **После:** 795 строк canonical кода
- **Экономия:** -806 строк (-50%)

**Следующий шаг:** Smoke test на сервере.

---

## 📁 ФАЙЛЫ ДАЛЬНЕЙШЕГО АУДИТА (когда лимиты восстановятся)

```
AIM/wordpress-core/wp-content/themes/aim-theme/
├── index.php              ← custom template logic
├── functions.php          ← hooks
├── scout-privacy.php      ← privacy filters
├── theme.css              ← canonical CSS?
├── chat/
│   ├── chat-inline.php    ← bubble widget
│   └── chat-pro.html      ← full-page chat
└── ...

AIM/hermes/skills/aim/SOUL.md              ← identity
AIM/hermes/app/agent_wrapper.py            ← mode prompts
AIM/hermes/app/tools/__init__.py           ← registry
```

---

*Документ создан как snapshot. Хирургия начата 1 июля 08:20 UTC — canonical build_report.py готов, следующий шаг: замена вызовов в pipeline.*
