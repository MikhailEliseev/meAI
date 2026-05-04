---
title: "Создать каркасы Magisters без бизнес-логики"
decision_id: "20260504-0849-magisters-skeleton"
timestamp: "2026-05-04T08:49:00Z"
confidence: 0.92
status: pending
tags: [decision, strategic, magisters, skeleton]
---

# Strategic Decision: Каркасы Magisters

## Question
Может пока просто создадим каркас? Не наделяем никого знаниями?

## Decision
Создать каркасы всех трёх Magisters (SEO, Content, Ads) без бизнес-логики

## Rationale

Ты прав — сначала каркас, потом наполнение! Создав каркасы всех трёх Magisters сразу, мы:

1. **Проверим архитектуру целиком** — увидим как Operator → 3 Magisters → Subagents работает вместе
2. **Сэкономим время** — не тратим на детали, которые могут измениться
3. **Получим полную картину** — сразу видно всю структуру агентства
4. **Упростим тестирование** — можем протестировать делегирование без реальной логики

Каркас = класс + методы-заглушки + интеграция с Event Bus + vault. Никакой SEO/Content/Ads логики — только структура.

**Учёт прошлого опыта:** Предыдущий план (20260504-0845) был слишком детальным для первого шага. Каркас — правильный подход для проверки архитектуры.

**План отката:** Если каркасы не заработают — вернёмся к BaseMagister, доработаем базовый класс.

## Confidence
92%

## Alternatives Considered

1. **Полная реализация одного Magister (предыдущий план)**
   - Плюсы: Сразу работающий агент
   - Минусы: Долго, много деталей, может потребоваться переделка
   - Почему не выбрал: Пользователь хочет сначала каркас

2. **Каркас только SEO Magister**
   - Плюсы: Фокус на одном агенте
   - Минусы: Не увидим полную картину, придётся повторять для других
   - Почему не выбрал: Раз каркас, то сразу всех трёх — быстрее

3. **Ничего не делать (подождать)**
   - Плюсы: Больше времени на обдумывание
   - Минусы: Нет прогресса
   - Почему не выбрал: Структура готова, каркас — быстрая проверка

## Risks

- **Риск 1:** Каркас без логики = нечего тестировать по-настоящему
  - **Митигация:** Добавим минимальные заглушки, которые возвращают mock-результаты для тестов

- **Риск 2:** Может оказаться, что BaseMagister требует доработки
  - **Митигация:** Каркас покажет это быстро, до того как напишем много кода

- **Риск 3:** Три каркаса одновременно = больше файлов для отладки
  - **Митигация:** Каркасы простые (50-100 строк каждый), легко отлаживать

## Implementation Plan

1. **Создать SEO Magister каркас** (`AIM/src/aim/magisters/seo_magister.py`)
   - Класс наследуется от BaseMagister
   - Методы-заглушки (pass или mock return)
   - Интеграция с Event Bus
   - Vault path настроен

2. **Создать Content Magister каркас** (`AIM/src/aim/magisters/content_magister.py`)
   - Аналогично SEO Magister
   - Свой vault path

3. **Создать Ads Magister каркас** (`AIM/src/aim/magisters/ads_magister.py`)
   - Аналогично SEO Magister
   - Свой vault path

4. **Создать базовый тест** (`tests/test_magisters_skeleton.py`)
   - Проверка что все три Magister создаются
   - Проверка интеграции с Event Bus
   - Проверка vault paths

5. **Обновить документацию** (`AIM/README.md`)
   - Добавить информацию о каркасах
   - Пометить что это skeleton (без логики)

## Status
- Created: 2026-05-04T08:49:00Z
- Status: completed
- Implemented: true
- Implementation completed: 2026-05-04T08:56:00Z

## Implementation Results

**Files Created:**
1. `AIM/src/aim/magisters/seo_magister.py` (2.9K)
2. `AIM/src/aim/magisters/content_magister.py` (3.0K)
3. `AIM/src/aim/magisters/ads_magister.py` (2.9K)
4. `tests/test_magisters_skeleton.py` (6.1K)
5. `AIM/README.md` (updated)

**Total:** 5 files, ~15K code

**What Works:**
- All three Magisters inherit from BaseMagister ✅
- Event Bus integration configured ✅
- Obsidian vaults paths set ✅
- Mock methods return test data ✅
- Tests verify structure ✅

**What's Missing (by design):**
- Business logic (SEO/Content/Ads knowledge)
- Real subagent identification
- Real result aggregation
- Database initialization

**Next Phase:** Add business logic to one Magister (SEO recommended)

## Context
- Supersedes: 20260504-0845-agency-implementation-plan (был слишком детальным)
- Approach: Skeleton-first (каркас → логика)
- Next: После каркасов — наполнение знаниями по одному Magister
