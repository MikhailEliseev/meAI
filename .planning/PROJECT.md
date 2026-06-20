# Hermes v7 SOUL Redesign

## What This Is

Переработка «души» (SOUL.md) AI-агента Hermes v7 для медицинского маркетингового агентства AIM (iamaim.ru). Устранение архитектурного конфликта между SOUL.md («я сам выбираю инструменты») и PipelineEngine (`engine.py` — Python-машина состояний, жёстко контролирующая последовательность 13 фаз). Полная зачистка мёртвого кода и перезапуск с чистой архитектурой.

## Core Value

**LLM — интерпретатор данных, НЕ оркестратор.** Python (PipelineEngine) контролирует последовательность фаз и обработку ошибок. LLM получает результаты фазы → интерпретирует → возвращает вывод. Это устраняет корневую причину неполных отчётов.

## Requirements

### Validated

- ✓ Pipeline Engine v7 с 13 фазами (PERPLEXITY → TECH AUDIT → ... → PRESENTATION) — работает на сервере в `hermes-20.06`
- ✓ 14 зарегистрированных tools в `_TOOL_HANDLERS` (engine.py:40-55)
- ✓ PhaseContract с retry-логикой и key rotation
- ✓ DeepSeek V4 Pro как модель (`deepseek-v4-pro`)

### Active

- [ ] Переписать SOUL.md — убрать язык автономности, вшить 13 фаз как обязательный алгоритм
- [ ] Переписать SKILL.md (client-onboarding-pipeline) — убрать «не жёсткий скрипт»
- [ ] Удалить 33 мёртвых тула из контейнера `hermes-20.06`
- [ ] Задеплоить новый SOUL.md на сервер через `docker cp`
- [ ] Перезапустить Hermes gateway
- [ ] Проверить на реальном пресейле

### Out of Scope

- Изменение `engine.py` или `phases.py` — пайплайн работает, проблема только в SOUL.md
- Изменение модели (DeepSeek V4 Pro остаётся)
- Миграция на другой фреймворк
- Переписывание тулов — только удаление мёртвых

## Context

- **Сервер:** Польша, Docker-контейнер `hermes-20.06`, `ssh aim`
- **Бекап v7:** `/Users/mikhaileliseev/Desktop/backups/hermes-v7/` (78 файлов проанализированы)
- **Корень проблемы:** SOUL.md (строка 11: «Я сам решаю, какие инструменты вызвать, в каком порядке») конфликтует с PipelineEngine, который жёстко контролирует последовательность фаз. LLM следовала инструкциям SOUL.md → игнорировала пайплайн → неполные отчёты.
- **SOUL-v3.md уже написан** — новый SOUL с правильным позиционированием LLM как интерпретатора
- **V7-REDESIGN.md** — полный проектный документ в `AIM/hermes/V7-REDESIGN.md`
- **33 мёртвых файла** идентифицированы (не в `_TOOL_HANDLERS`, не импортируются pipeline-обработчиками)
- **Hermes Handbook:** `/opt/data/AIM_HANDBOOK.md` на сервере

## Constraints

- **Runtime:** Docker-контейнер `hermes-20.06`, нельзя ломать работающий пайплайн
- **Модель:** DeepSeek V4 Pro, стримы рвутся на ~120с
- **Совместимость:** Новый SOUL.md должен работать с существующим `engine.py` и `phases.py`
- **Деплой:** Только через `docker cp` + перезапуск gateway (нельзя пересобирать образ)
- **Без даунтайма:** Фазы не должны прерываться при деплое SOUL.md (это просто текстовый файл)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| LLM = интерпретатор, не оркестратор | PipelineEngine уже жёстко контролирует фазы; SOUL.md должен это отражать | — Pending |
| 13 фаз как MANDATORY алгоритм | Фазы в phases.py идут строго последовательно; SOUL не должен говорить о гибкости | — Pending |
| Удалить все 33 мёртвых тула | Не используются в `_TOOL_HANDLERS`, создают путаницу и риск неправильного вызова | — Pending |
| Не трогать engine.py/phases.py | Пайплайн работает корректно; проблема только в инструкциях LLM | — Pending |
| SOUL-v3 сохраняет tone/ниши/KP-правила | Это ценные наработки, не связанные с проблемой автономности | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition:**
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone:**
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-20 after GSD project initialization*
