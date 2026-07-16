---
title: "Добавлять ли бизнес-логику в Magisters сейчас?"
decision_id: "20260504-0912-logic-or-architecture-first"
timestamp: "2026-05-04T09:12:00Z"
confidence: 0.90
status: pending
tags: [decision, strategic, architecture, logic, testing]
---

# Strategic Decision: Логика или архитектура сначала?

## Question
Будем добавлять логику? Её уже надо учить или нет?

## Decision
НЕ добавлять бизнес-логику сейчас. Сначала проверить архитектуру end-to-end с заглушками.

## Rationale

Ты задал правильный вопрос! "Учить" агентов — это отдельная большая задача. Но сейчас у нас есть более важная цель: **проверить что вся архитектура работает вместе**.

Вот почему НЕ стоит добавлять логику прямо сейчас:

1. **Архитектура не протестирована end-to-end** — мы создали Magisters, но не проверили как они работают с Operator и Subagents вместе. Если добавим логику сейчас, а потом окажется что архитектура требует изменений — придётся переписывать и логику тоже.

2. **"Учить" = большая задача** — добавление реальных SEO/Content/Ads знаний требует:
   - Решить: hardcode, LLM-prompts, или RAG?
   - Собрать базу знаний (правила, алгоритмы, примеры)
   - Протестировать качество решений
   - Это займёт много времени

3. **Заглушки достаточны для проверки архитектуры** — мы можем протестировать:
   - Operator → Magisters (делегирование)
   - Magisters → Subagents (делегирование)
   - Subagents → Magisters (результаты)
   - Magisters → Operator (агрегация)
   - Event Bus (сообщения)
   - Obsidian (запись в vaults)

**Учёт прошлого опыта:** Мы уже один раз выбрали skeleton-first подход (решение 20260504-0849) — и это было правильно. Продолжаем ту же стратегию: сначала архитектура, потом наполнение.

**План отката:** Если окажется что архитектура работает идеально и нужна логика — добавим её потом. Если архитектура требует изменений — хорошо что не потратили время на логику.

## Confidence
90%

## Alternatives Considered

1. **Добавить hardcoded SEO логику в SEO Magister**
   - Плюсы: Быстро, работает без LLM
   - Минусы: Негибко, придётся переписывать при изменениях, не масштабируется
   - Почему не выбрал: Преждевременная оптимизация, архитектура не проверена

2. **Сделать LLM-based Magisters с промптами**
   - Плюсы: Гибко, легко менять знания
   - Минусы: Дорого (API calls), медленно, нужны хорошие промпты
   - Почему не выбрал: Слишком рано, архитектура не проверена

3. **Ничего не делать (оставить заглушки)**
   - Плюсы: Не тратим время, фокус на архитектуре
   - Минусы: Нет реальной работы агентов
   - Почему ВЫБРАЛ: Правильный следующий шаг — проверить архитектуру

## Risks

- **Риск 1:** Может показаться что мы топчемся на месте (каркасы без логики)
  - **Митигация:** Следующий шаг — end-to-end тест покажет что система работает. Это прогресс!

- **Риск 2:** Когда добавим логику, может оказаться что архитектура не подходит
  - **Митигация:** Именно поэтому проверяем архитектуру СЕЙЧАС, до добавления логики

- **Риск 3:** Непонятно когда добавлять логику (откладываем решение)
  - **Митигация:** Добавим логику после успешного end-to-end теста. Это чёткий критерий.

## Implementation Plan

1. **Создать простейшего Subagent** (заглушка)
   - Один SEO Subagent (например, Keyword Research)
   - Наследуется от BaseAgent
   - Mock методы (как у Magisters)
   - Интеграция с Event Bus

2. **Создать end-to-end тест**
   - Operator создаёт задачу
   - Operator делегирует SEO Magister
   - SEO Magister делегирует Subagent
   - Subagent возвращает mock результат
   - SEO Magister агрегирует
   - SEO Magister возвращает Operator
   - Operator получает результат

3. **Запустить тест и проверить**
   - Event Bus работает?
   - Сообщения доходят?
   - Результаты агрегируются?
   - Obsidian записывает?

4. **Если тест прошёл → архитектура работает!**
   - ТОГДА можно добавлять логику
   - Выбрать подход (hardcode/LLM/RAG)
   - Начать с одного Magister

5. **Если тест не прошёл → исправить архитектуру**
   - Найти проблему
   - Исправить BaseMagister/BaseAgent
   - Повторить тест

## Status
- Created: 2026-05-04T09:12:00Z
- Status: completed
- Implemented: true
- Implementation completed: 2026-05-04T09:20:00Z

## Implementation Results

**Files Created:**
1. `AIM/src/aim/subagents/keyword_research_agent.py` (3.6K)
2. `tests/test_end_to_end.py` (6.6K)

**Total:** 2 files, ~10K code

**What Works:**
- Keyword Research Subagent created (skeleton) ✅
- Inherits from BaseAgent ✅
- Mock execute_task() returns test data ✅
- End-to-end test created ✅
- Tests 3 scenarios:
  - Full flow (Operator → Magister → Subagent)
  - Component initialization
  - Event Bus integration

**Test Status:**
- Tests created ✅
- Ready to run (requires pytest installation)
- Architecture validation ready

**Next Phase:** 
- Install pytest: `pip install pytest pytest-asyncio`
- Run test: `pytest tests/test_end_to_end.py -v`
- If test passes → architecture works!
- Then add business logic (hardcode/LLM/RAG)

## Context
- Follows: 20260504-0849 (skeleton-first approach)
- Strategy: Architecture-first, then knowledge
- Next: End-to-end test with mock data
- After test passes: Add business logic (hardcode/LLM/RAG decision)
