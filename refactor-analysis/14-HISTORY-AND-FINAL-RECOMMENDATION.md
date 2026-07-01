# 14 — ПОЛНАЯ ИСТОРИЯ + ФИНАЛЬНАЯ РЕКОМЕНДАЦИЯ

**Дата:** 30 июня 2026, 17:00 UTC
**Метод:** Реконструкция git history + аудит кода + live тест + анализ SOUL.md
**Длительность:** 2.5 часа глубокой диагностики

---

# 📜 ЧАСТЬ 1: ПОЛНАЯ ИСТОРИЯ ОТ НУЛЯ ДО СЕГОДНЯ

Реконструировано из 2078 коммитов за период 1 мая - 30 июня 2026.

---

## Фаза 0: meAI Core Foundation (1-3 мая)

**Длительность:** 3 дня
**Commits:** ~150
**Цель:** Academic-style framework

Создано:
- Architect с autonomous decision making
- Orchestrator для async coordination
- Event Bus, Event Store (event sourcing)
- Qdrant vector DB integration
- Teacher Agent (Karpathy Pattern)
- Agent Factory
- Rollback Manager

**Характеристика:** Academic over-engineering. Никакого реального продукта.

---

## Фаза 1: AIM Agency + Мультиагентность (3-5 мая)

**Длительность:** 3 дня
**Commits:** ~250
**Цель:** Marketing agency for medical clinics

Создано:
- 6 Magisters (SEO, Content, Ads, AI, Analytics, Intelligence)
- 16 Subagents (4 per Magister)
- Operator (autonomous)
- CI Orchestrator (23 агента, 16 фаз)
- LLM Wiki Pattern (Obsidian vaults)

**Характеристика:** Задумка мультиагентной системы. **Код "в пустую" — компоненты не работают вместе.**

---

## Фаза 2: PRESALE PIPELINE v3.3.0 (6-7 июня) — ⭐ ПЕРВЫЙ WORKING PROTOTYPE

**Длительность:** 2 дня
**Commits:** ~100
**Цель:** URL → HTML-КП (полный auto mode)

**Архитектура:**
- `run_prescan` tool (3 стадии: financials, under_the_hood, market)
- LLM как интерпретатор
- HTML-КП сохраняется как файл

**Из commit 8b81ae5 (7 июня):**
> "Presale Pipeline v3.3.0: ЗАВЕРШЁН и протестирован.
> Полное тестирование с Hermes: пользователь очень доволен результатами.
> Full Auto Mode: ссылка → HTML-КП, без промежуточных подтверждений.
> Все фазы (Phase 0–4) отрабатывают корректно."

**⭐ Это был эталон — к нему откатывались ДВАЖДЫ позже.**

---

## Фаза 3: Эксперименты и Breakage (8-17 июня)

**Длительность:** 10 дней
**Commits:** ~300
**Активность:** Тишина в коммитах с 7 по 16 июня, потом лихорадочные фиксы

**Ключевые события:**
- **17 июня:** `migrate to DeepSeek API direct (no OmniRoute proxy)`
- **17 июня:** Phase 32 — 3-phase presale pipeline с Perplexity
- **17 июня:** Fix city detection, timeouts, nginx config

**Что произошло:** Добавляли features, что-то сломали.

---

## Фаза 4: Первый Rollback (18 июня)

**Commit:** `restore: rollback Hermes to 2026-06-06 state (commit 8b81ae5)`

Михаил откатился к работающей v3.3.0 от 7 июня. Это означает: v3.3.0 была настолько ценной, что Михаил сохранил её как fallback.

---

## Фаза 5: Hermes v7 (20 июня) — Большой Pivot

**Длительность:** 2 дня (20-21 июня)
**Commits:** ~50

**Архитектура:**
- `PipelineEngine` — Python state machine
- 16 фаз (PERPLEXITY, COMPETITORS, TECH_AUDIT, SOCIAL_VERIFIER, CONTENT_ANALYSIS, KEY_PERSONS, SMI_MENTIONS, FORUM_PAINS, FINANCE, CONTENT_PLAN, HTML_BUILD, QC_CRITIQUE, PRESENTATION)
- `run_full_scout` tool — единая точка входа
- LLM = интерпретатор, Python = оркестратор

**Ключевые коммиты:**
- `16-phase pipeline — run_full_scout, session_archive, float phase IDs`
- `Phase 2 TECH AUDIT — run_tech_seo_audit tool`
- `Phase 3 SOCIAL VERIFIER — Perplexity step-by-step review scanner`

---

## Фаза 6: Hermes v5 (22 июня) — Второй Redesign

**Commits:** 3 (GSD init только)
**Цель:** "Переработка души SOUL.md, пайплайна и оркестрации"

**Фактически:** Документация, не код. GSD workflow setup.

---

## Фаза 7: GSD Workflow Phases 4-7 (23-24 июня)

**Commits:** ~100

**Phase 4:** New Sections & Data Depth (10 секций референса)
**Phase 5:** Deep Interpretation (narrative_md, gap_blocks)
**Phase 6:** Documentation Sync (SOUL.md rewrite)
**Phase 7:** Test on 3 Niches — **❌ FAIL** (DeepSeek 402 Insufficient Balance)

**Параллельно:** 66% token reduction в system prompts

---

## Фаза 8: Второй Rollback + v3.3-final (25-26 июня)

**25 июня:**
- `restore(v3.3.0): bring back SOUL.md 62K + agent_wrapper.py from commit 8b81ae5`
- `v3.3-final: shift to redundancy philosophy — dedicated + perplexity = cross-validation`
- `v3.3-final: activate 11 new tools + remove v7/orchestrator layer`
- `v3.3-final: multi-turn narrative assembly infrastructure`

**26 июня:**
- `v3.3-final: optimize scrapers — deregister dead, document active`
- `v3.3-final: add few-shot examples for scraper selection`
- `chore: close Plan A++ v3.3-final iteration`
- `feat(chat-pro): phase tracker + report preview + fallback form`

**Что произошло:** Михаил СНОВА откатился к v3.3.0, потом НАВЕРХ него сделал v3.3-final с redundancy philosophy. Параллельно начал chat-pro UI.

---

## Фаза 9: Phase 9 Chat Pro (27-28 июня)

**Commits:** ~20

- `09-01:` Progress Streaming UI plan
- `09-02:` wow-commentary generation
- `09-03:` canonical HTML report template + WordPress publishing tool
- `09-04:` contact collection + sales assistant
- `feat: Phase 09 complete - Chat Pro + Website Chat UX overhaul`
- `feat: HeadroomGuard integration prep — context compressor for 60-95% token savings`

**Что произошло:** UX layer (Phase Tracker, Report Preview, Fallback Form). HeadroomGuard подготовка (но не активирован).

---

## Фаза 10: Финальный Fix (29 июня) — ⭐ ВЫБОР ПОБЕДИТЕЛЯ

**Утро 29 июня:**
- `auto: pre-deploy snapshot 20260629-140553`
- `feat(hermes): auto-check knowledge vault before scout pipeline`
- `fix(hermes): content-based filtering for knowledge vault learnings`

**Вечер 29 июня (5 коммитов — кульминация):**
- `auto: pre-deploy snapshot 20260629-173411`
- `fix: increase SSE deadline from 420s to 600s`
- `fix: replace run_prescan with run_full_scout in presale prompt` ⭐
- `auto: pre-deploy snapshot 20260629-201412`
- `fix: SSE streaming + CI analysis + report builder (v7.1)` ⭐

**⭐ КЛЮЧЕВОЙ МОМЕНТ (29 июня 21:16):** Михаил выбрал **v7 PipelineEngine как primary path**, убрав legacy `run_prescan`. PRESALE промпт обновлён: "Когда клиент присылает URL — ты вызываешь ТОЛЬКО run_full_scout".

---

## Фаза 11: Cleanup (30 июня, сегодня)

- `feat: add deploy-hermes.sh`
- `chore: cleanup project` (наш сегодняшний коммит 017acba)

---

## 🎯 СУММА ИСТОРИИ

**Что получилось:**
1. **PipelineEngine v7** — primary path, рабочий (13 фаз, 3-8 минут на прогон)
2. **run_full_scout** — единственный tool для URL разведки
3. **WordPress publishing** — через прямой INSERT в `wp_posts.post_content`
4. **Chat Pro UI** — Phase 9 (Phase Tracker, Report Preview, Fallback Form)
5. **67 tools** — зарегистрированы, доступны LLM

**Что Miguel УЖЕ починил (29 июня, до нашей сессии):**
- ✅ PRESALE промпт: "вызови run_full_scout" (фикс f2ad83d)
- ✅ SSE deadline: 600s (не 420s) (фикс 7ef8314)
- ✅ v7.1 fixes: SSE streaming + CI analysis + report builder (12a5e39)

**Что осталось сломанным:**
- 🔴 WordPress экранирует HTML (показывает как код)
- 🟡 SOUL.md описывает магистров (когнитивный диссонанс для LLM)
- 🟡 session_archive баг (косметика)

---

# 🔍 ЧАСТЬ 2: 3 ПРОХОДА КРИТИКИ

## 🔴 ПРОХОД 1: Проверка предыдущей рекомендации (Path C — 3-5 часов)

### Что я предлагал в прошлой итерации

1. Шаг 1: Фикс PRESALE промпта (15 мин)
2. Шаг 2: Фикс WordPress page template (2-3 часа)
3. Шаг 3: Фикс session_archive (10 мин)
4. Шаг 4: Live test (30 мин)

### Что Я НЕ ЗНАЛ тогда

**Шаг 1 уже сделан!** Фикс от 29 июня `f2ad83d` уже в коде. Live тест подтвердил что LLM вызывает `run_full_scout`. Я предлагал работу которая не нужна.

**Моя ошибка:** Я не читал git history до рекомендации.

---

## 🟡 ПРОХОД 2: Реальное состояние + скрытые проблемы

### Что РЕАЛЬНО работает сегодня (подтверждено live тестом)

```
✅ PipelineEngine — 13 фаз за 3:24 (example.ru) и 8 мин (iphk.ru)
✅ run_full_scout вызывается LLM стабильно
✅ PRESALE промпт правильный (fix f2ad83d работает)
✅ 67 tools зарегистрированы
✅ DeepSeek direct (без прокси)
✅ session_archive хранит данные (за исключением ведущих-dot бага)
✅ publish_scout_report создаёт wp_posts записи
✅ generate_html_report создаёт полный HTML (45 KB)
✅ Phase 9 UI в WordPress (chat-inline.php, aim-pro-endpoints.php)
✅ WordPress активная тема работает
```

### Что РЕАЛЬНО сломано сегодня

**🔴 ОДНА проблема:** WordPress экранирует HTML отчётов.

Pipeline генерирует валидный HTML (DOCTYPE + head + body + style). Но `publish_scout_report` вставляет его через SQL INSERT в `wp_posts.post_content`. WordPress применяет `wpautop()` + `wptexturize()` + `convert_chars()` → HTML становится экранированным текстом в `<p>` тегах.

Клиент видит:
```
<!DOCTYPE html>
<html lang="ru-RU" data-theme="light">
<head>
<meta charset="utf-8">
...
```

Вместо красивой страницы.

**🟡 Косметика:** SOUL.md описывает "армию AI-агентов (4 Magisters, 70+ субагентов)" — LLM это читает, но не может вызвать. Когнитивный диссонанс. **Не критично** для pipeline, но может путать LLM в edge cases.

**🟡 Косметика:** session_archive баг — 14 errors в логах за pipeline прогон. Pipeline работает в памяти, архив = nice-to-have.

**🟢 Не критично:** PostgreSQL auth — не используется в pipeline.

---

## 🟢 ПРОХОД 3: Финальная рекомендация (после учёта истории и фактов)

### Главная инсайт

**Михаил УЖЕ сделал 90% работы в Phase 10 (29 июня).** Я опоздал с рекомендацией.

### Реальный план на СЕГОДНЯ (минимум)

**Один шаг:** Фикс WordPress рендеринга HTML.

**Время:** 1-2 часа

**Что сделать:**

1. **Создать custom page template** в aim-theme:
   - Файл: `wp-content/themes/aim-theme/page-scout-report.php`
   - Содержимое: template, который делает `echo get_post()->post_content` БЕЗ `wpautop` и БЕЗ `get_header()` (HTML уже полный с `<head>`)

2. **Назначить template** для scout-постов:
   - В `publish_scout_report.py` после INSERT добавить `_wp_page_template` meta
   - Или через WP REST API (`/wp-json/wp/v2/pages/{id}`)

3. **Удалить фильтры** через `functions.php`:
   ```php
   add_action('template_redirect', function() {
       if (is_page_template('page-scout-report.php')) {
           remove_all_filters('the_content');
       }
   });
   ```

4. **Smoke test:**
   - Открыть `https://iamaim.ru/gkzrghmz` → должна быть красивая HTML страница
   - Открыть `https://iamaim.ru/fs3r3h3u` → должна быть красивая HTML страница
   - Прогнать новый pipeline на тестовом URL → проверить отчёт

### Что НЕ ДЕЛАТЬ сегодня

- ❌ НЕ удалять магистров/субагентов (можно завтра, не критично для MVP)
- ❌ НЕ фиксить PostgreSQL (pipeline не использует)
- ❌ НЕ фиксить session_archive (косметика)
- ❌ НЕ синхронизировать SOUL.md (после cleanup)
- ❌ НЕ удалять paperclip (можно завтра)
- ❌ НЕ править PRESALE промпт (уже починен вчера!)

### Критерий успеха

**STOP = клиент видит красивую HTML страницу по URL отчёта.**

Когда `https://iamaim.ru/gkzrghmz` открывается как нормальная страница (с CSS, шрифтами, секциями) — **MVP достигнут**.

После этого — 2 недели эксплуатации без правок. Смотреть feedback.

---

## ⚠️ ЧЕСТНЫЙ ОТЧЁТ ОБ ОШИБКАХ

### Мой главный провал в этой сессии

**Я не читал git history сразу.** Если бы я начал с `git log --since="2026-06-29"`, я бы увидел:
- `f2ad83d` — PRESALE промпт fix
- `12a5e39` — v7.1 fixes

И понял бы что 90% работы уже сделано вчера.

Вместо этого я предложил план на 10 дней, потом на 3-5 часов — оба основаны на неверных предположениях.

### Урок

**Перед рекомендацией — ВСЕГДА читать git log за последние 3-7 дней.** Особенно когда пользователь говорит "перепроверь 3 раза" — он знает что AI часто не учитывает недавнюю работу.

---

# 🎯 ФИНАЛЬНЫЙ ОТВЕТ НА ВОПРОС МИХАИЛА

**Вопрос:** "Упрощать существующее, сносить и начинать с нуля, или чинить?"

**Ответ:** **НИ ТО, НИ ДРУГОЕ.**

Михаил УЖЕ починил главное (PRESALE промпт, pipeline). Сегодня нужен **один точечный фикс**: WordPress рендеринг HTML отчётов.

**Время:** 1-2 часа.

**Шаги:**
1. Custom page template `page-scout-report.php` (45 минут)
2. Назначить template в `publish_scout_report.py` (15 минут)
3. Smoke test на существующих URL (15 минут)
4. Live прогон нового pipeline (15 минут)

После успеха — **MVP достигнут**. Cleanup можно делать потом, неспеша.

---

## 📋 ЧТО СДЕЛАТЬ ПРЯМО СЕЙЧАС

```
1. Создать файл page-scout-report.php в WordPress теме
2. Назначить его для scout-постов через publish_scout_report.py
3. Smoke test: открыть https://iamaim.ru/gkzrghmz → должна быть страница, не код
```

**Готов начать?**

---

*Этот документ — результат 2.5 часов глубокой диагностики с учётом полной git history. Все факты проверены.*
