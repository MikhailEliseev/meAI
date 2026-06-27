# Hermes v5 — Full Coverage Reports

## What This Is

Переработка «души» (SOUL.md), пайплайна и оркестрации AI-агента Hermes для производства **полных отчётов пресейла** — на уровне референса `ИПХиК (2).html` (10 секций, 965 строк, 78 KB). Отказ от жёсткого pipeline-подхода v3/v7 («LLM = интерпретатор») в пользу **LLM-оркестратора с 3-проходным циклом**: сбор → анализ пробелов → допосбор + финальная сборка.

Проблема: текущий гибрид v4 (LLM-оркестратор + формальный pipeline) покрывает только ~30% данных, которые Hermes реально может собрать. Инструменты есть (40+), но LLM их не использует. Причины — требуют исследования.

## Core Value

**Полнота данных через LLM-оркестратора с авторежимом 3 проходов.**

```
Проход 1: СБОР — LLM вызывает инструменты по ситуации, собирает сырьё
Проход 2: ГЭП-АНАЛИЗ — LLM сравнивает собранное с чек-листом покрытия
Проход 3: ДОПОСБОР + СБОРКА — LLM заполняет пробелы, генерирует отчёт
```

Это воспроизводит успешный паттерн v1 (когда админ вручную просил «перезапусти, обогати данные»), но в авторежиме — без ручного вмешательства.

## Requirements

### Validated

- ✓ 40+ инструментов Hermes зарегистрировано в `register_all_tools()` (`app/tools/__init__.py`)
- ✓ PipelineEngine v7 с 13 фазами работает на сервере (`/opt/hermes/app/pipeline/phases.py`)
- ✓ HTML-репортёр `generate_html_report` в дизайн-системе AIM (dual theme, glass cards)
- ✓ Референс-отчёт `ИПХиК (2).html` — 78 KB, 965 строк, 10 секций, канон для полноты
- ✓ Инструмент `run_instagram_content` существует, зарегистрирован для LLM, но не подключён к pipeline
- ✓ Deploy-инфраструктура: `ssh aim`, контейнер `aim-hermes`, volume `aim_hermes_data`
- ✓ 3 версии SOUL.md доступны для анализа (v3 интерпретатор / v3 расширенная / v4 оркестратор)

### Active

- [ ] Исследовать причину: почему LLM v4 пропускает инструменты и фазы (промпт / модель / pipeline-ограничение / комбинация)
- [ ] Подключить `run_instagram_content` к оркестратору (не только как LLM-tool, но и как обязательный шаг для косметологии/пластики)
- [ ] Реализовать 3-проходный цикл: Сбор → Гэп-анализ → Допосбор + Сборка
- [ ] Добавить фазу/секцию Strategy (5 конкретных направлений на основе данных)
- [ ] Добавить фазу/секцию Offer/CTA («Что AIM может сделать для клиники»)
- [ ] Динамика выручки за 3 года (сейчас только текущий год из ГИР БО)
- [ ] Конкретные ссылки на СМИ-публикации (сейчас только счётчики по категориям)
- [ ] QC-чек-лист покрытия: 10-20 пунктов (Instagram врачей собран? Стратегия? Динамика? СМИ-ссылки? ...)
- [ ] Синхронизировать SOUL.md + SKILL.md + phases.py — убрать рассинхрон 13/14/16 фаз
- [ ] Переписать `interpretation_prompt` для каждой фазы под референс (нарратив вместо дампа метрик)
- [ ] Тестирование на 3-5 реальных пресейлах разных ниш

### Out of Scope

- Смена LLM-модели (DeepSeek V4 Pro остаётся) — модель работает, проблема в оркестрации
- Миграция на другой фреймворк (FastAPI + hermes-agent остаются)
- Переписывание дизайн-системы HTML-отчётов (dual theme, glass cards — канон)
- Удаление PipelineEngine — остаётся как один из режимов, не единственный
- Поддержка государственных клиник (ГАУЗ/ГБУЗ/МУЗ) — вне бизнеса AIM

## Context

### Сервер и инфраструктура
- **Сервер:** Польша, `ssh aim`, Docker-контейнер `aim-hermes`
- **HERMES_HOME:** `/opt/data` (volume `aim_hermes_data`)
- **SOUL.md в контейнере:** `/opt/data/SOUL.md` (сейчас v4, 668 строк)
- **Skills:** `/opt/hermes/skills/` (ro-монтирование из `/opt/aim/AIM/hermes/skills`)
- **Деплой:** `docker cp` + перезапуск gateway (нельзя пересобирать образ)

### Три версии SOUL.md (эволюция)
1. **v3 (интерпретатор):** `skills/aim/SOUL.backup.md` локально, 327 строк, 14 фаз. LLM только интерпретирует, Python оркестрирует. Привело к коротким отчётам — LLM не обогащает.
2. **v3 расширенная:** `/opt/hermes-data/SOUL.md` на сервере, 344 строки, 16 фаз. Не используется (HERMES_HOME указывает на `/opt/data`, не `/opt/hermes-data`).
3. **v4 (оркестратор):** `/opt/data/SOUL.md` в контейнере, 668 строк, 40+ инструментов в каталоге. LLM «свободный художник». Привело к ~30% покрытия — LLM пропускает инструменты.

### Рассинхрон фаз (корень хаоса)
- **phases.py в коде:** 13 фаз (0–12)
- **aim-scout/SKILL.md:** 14 фаз (0–13)
- **серверная v3 SOUL.md:** 16 фаз (0, 0.5, 0.75, 0.8, 1, 2, 3, 3.2, 3.5, 3.6, 4, 5, 6, 7, 8, 9, 10)
- **engine.py _TOOL_HANDLERS:** 19 инструментов (подмножество из 40+)

### Референс `ИПХиК (2).html` — целевой идеал
10 секций:
1. About (ОКВЭД, лицензии, динамика выручки за 3 года)
2. Market (таблица 8 конкурентов: выручка, тренд, хирурги, Instagram + gap-блоки)
3. Experts (ТОП-5 врачей: ФИО, регалии, подписчики, avg лайки/просмотры, стиль)
4. Content Analysis (по каждому врачу: стиль, темы, пробелы, потенциал + Топ-5 страхов)
5. Media (Forbes, RBC, Vademecum, Kommersant — с конкретными ссылками и датами)
6. Competitors (детальные карточки 8 клиник: выручка, год, хирурги, Instagram, специфика)
7. Whitefields (матрица: клиент vs 3 конкурента по полям)
8. Presence (тех. аудит: что хорошо, что исправить, приоритеты)
9. Strategy (5 направлений: контент, Telegram, GEO, репутация, кросс-промо)
10. Offer («Что AIM может сделать для клиники»)

### Корневые причины 30% покрытия (гипотезы для исследования)
1. **Instagram полностью отсутствует** — критично для косметологии/пластики (40% контента референса)
2. **Нет фаз Strategy и Offer** — отчёт заканчивается на данных, без рекомендаций
3. **Динамика выручки** — только текущий год, не 3 года
4. **СМИ-ссылки** — счётчики вместо конкретных публикаций
5. **Интерпретация недостаточно глубокая** — узкие промпты, «дамп метрик» вместо нарратива
6. **HTML BUILD не связывает секции** — страхи пациентов (04) не ведут к стратегии (09)
7. **SOUL.md даёт слишком много свободы** — LLM решает «не обязательно» и пропускает

### Архив предыдущего GSD-проекта
`.planning-archive-2026-06-22/` — предыдущий GSD-проект «Hermes v7 SOUL Redesign» (20 июня). Устарел: помечено Phase 1-2 complete, но фактически в контейнере v4, не v3. PROJECT.md, ROADMAP.md, STATE.md, CHECKPOINTS.md, BACKLOG.md — доступны для справки.

## Constraints

- **Runtime:** Docker-контейнер `aim-hermes`, нельзя ломать работающий пресейл-поток
- **Модель:** DeepSeek V4 Pro, стримы рвутся на ~120с — long-running фазы нужно бить
- **Деплой:** Только через `docker cp` + перезапуск gateway (нельзя пересобирать образ)
- **Без даунтайма:** Фазы не должны прерываться при деплое изменений
- **Бюджет:** 1-2 месяца полноценной переработки (согласовано с пользователем)
- **Метрика успеха:** QC-чек-лист покрытия 10-20 пунктов (Instagram? Strategy? Offer? Динамика? СМИ-ссылки? ...)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| LLM-оркестратор (не интерпретатор) | Из опыта v1: оркестратор давал более полные отчёты, чем жёсткий pipeline v3/v7. Пользователь явно подтвердил. | — Pending |
| 3-проходный цикл автоматически | Воспроизводит успешный паттерн v1 (ручные итерации), но без участия админа. Сбор → Гэп-анализ → Допосбор + Сборка. | — Pending |
| Полнота данных > структура | Пользователь выбрал: «Полнота данных важнее структуры». Референс — ориентир, не догма. | — Pending |
| Полноценная переработка (1-2 месяца) | Пользователь готов. Полная переработка pipeline + интерпретация + HTML-репортёр + все инструменты. | — Pending |
| QC-чек-лист как метрика успеха | Объективная оценка покрытия, не субъективное «нравится/не нравится». | — Pending |
| Сохранить DeepSeek V4 Pro | Не менять модель. Проблема в оркестрации и промптах, не в модели. | — Pending |
| Сохранить дизайн-систему HTML | Dual theme, glass cards — канон. Менять контент, не оформление. | — Pending |
| Подключить run_instagram_content | Критично для косметологии/пластики — 40% контента референса. | — Pending |
| Исследовать причину пропуска инструментов | Пользователь не знает, почему LLM v4 пропускает. First phase — research. | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-23 after Phase 2 completion (3-Pass Orchestrator + QC Checklist)*

## Current State (Phase 2 complete — 2026-06-23)

**Phase 2 finished** — 3 plans, 9 commits, all 9 requirements (ORC-01..05, QC-01..04) verified at code level.

- ✅ P0 `_unwrap_tool_output` NameError fixed in `generate_html_report.py` (restores PipelineEngine HTML BUILD)
- ✅ 3-pass orchestrator built in new module `app/orchestrator/` (Collect → Gap-analyze → Fill+Assemble)
- ✅ Full 15-item QC checklist with soft QC gate + coverage % rendering in HTML report
- ✅ `ORCHESTRATOR_MODE=1` env var = opt-in (default OFF — production safe)
- ⚠ Human UAT pending (4 items) — explicitly deferred to Phase 8 deploy + live LLM testing
- → Next: Phase 3 (Instagram Integration)
