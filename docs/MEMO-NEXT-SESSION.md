# 📝 ПАМЯТКА ДЛЯ СЛЕДУЮЩЕЙ СЕССИИ

**Дата:** 2026-05-09 20:37 GMT+3  
**Контекст:** Завершили Этап 1.1, готовы к Этапу 1.2

---

## ✅ ЧТО СДЕЛАНО

### Этап 1.1: P0 Subagents (ЗАВЕРШЁН)

Создано 4 критичных спецификации:
1. ✅ Medical Fact-Checker Agent (`docs/subagents-specs/MEDICAL_FACT_CHECKER_SPEC.md`, ~15 KB)
2. ✅ Data Reconciliation Agent (`docs/subagents-specs/DATA_RECONCILIATION_SPEC.md`, ~20 KB)
3. ✅ Tone of Voice Agent (`docs/subagents-specs/TONE_OF_VOICE_SPEC.md`, ~18 KB)
4. ✅ Data Collector Agent (`docs/subagents-specs/DATA_COLLECTOR_SPEC.md`, ~22 KB)

### Оптимизация процесса (ГОТОВО)

1. ✅ **Упрощённый шаблон интервью** (`docs/templates/SIMPLIFIED_INTERVIEW_TEMPLATE.md`)
   - 10-12 вопросов вместо 32
   - 5 блоков вместо 8
   - Автоматическое заполнение стандартных секций
   - Экономия времени ~60-70%

2. ✅ **Архитектурные паттерны** (`docs/ARCHITECTURE-COMMUNICATION.md`)
   - Стандартные паттерны коммуникации (Event Bus, эскалация)
   - Общие правила хранения данных (БД + Obsidian)
   - Типовая обработка ошибок (retry 10x, graceful degradation)
   - Стандартные метрики и тестирование
   - Mock Data Rule (НИКОГДА в production!)

3. ✅ **Отчёт о завершении** (`docs/PHASE-1-STAGE-1.1-COMPLETE.md`)

---

## 🎯 ЧТО ДАЛЬШЕ

### Этап 1.2: P1 Subagents (СЛЕДУЮЩИЙ)

**Цель:** Создать 15 спецификаций для основных каналов  
**Время:** 3.75 часа (с новым форматом, было бы 10 часов)  
**Формат:** Упрощённое интервью (10-12 вопросов)

**Агенты для спецификации (15 шт):**

**SEO (3):**
1. Keyword Research Agent
2. Web Analytics Agent
3. Search Console Agent

**Content (3):**
4. Blog Content Agent
5. Landing Content Agent
6. Editor Agent

**Ads (3):**
7. Campaign Manager Agent
8. Budget Optimizer Agent
9. Performance Monitor Agent

**Social (3):**
10. Trend Watcher Agent (⭐⭐⭐ критичный!)
11. Content Scheduler Agent
12. AI Sales Admin Agent

**Analytics (3):**
13. Competitor Analysis Agent
14. Report Generator Agent
15. Data Processor Agent

---

## 📋 КАК РАБОТАТЬ С НОВЫМ ФОРМАТОМ

### Шаг 1: Прочитать шаблоны (ОБЯЗАТЕЛЬНО!)

```bash
# Перед началом интервью прочитай:
Read docs/templates/SIMPLIFIED_INTERVIEW_TEMPLATE.md
Read docs/ARCHITECTURE-COMMUNICATION.md
```

### Шаг 2: Провести упрощённое интервью (5 блоков)

**Блок 1: Роль и уникальность (3 вопроса)**
- Что делает агент?
- Почему это критично?
- Что НЕ делает?

**Блок 2: Входные данные (2 вопроса)**
- Какие данные нужны?
- Специфичные требования?

**Блок 3: Алгоритм (3 вопроса)**
- Основные шаги?
- Специфичная логика?
- Внешние API?

**Блок 4: Результаты (2 вопроса)**
- Что возвращает?
- Как измерять качество?

**Блок 5: Особенности (2 вопроса)**
- Специфичные ошибки?
- Особенности интеграции?

### Шаг 3: Автоматически заполнить стандартные секции

Используй паттерны из `docs/ARCHITECTURE-COMMUNICATION.md`:
- Интеграции (Event Bus, Event Store, Obsidian, Database)
- Обработка ошибок (INVALID_INPUT, API_ERROR, TIMEOUT, INTERNAL_ERROR)
- Обучение (Teacher Agent, раз в квартал)
- Логирование (Event Store, Obsidian, системные логи)
- Тестирование (Unit 80%+, Integration, E2E)
- Deployment (Python 3.11+, зависимости, мониторинг)

### Шаг 4: Создать спецификацию

Используй шаблон `docs/templates/SUBAGENT_SPEC_TEMPLATE.md` как основу.

---

## 🔑 ВАЖНЫЕ ПРАВИЛА (НЕ ЗАБЫТЬ!)

### 1. НЕ переспрашивать стандартные вещи:
- ❌ "Как агент взаимодействует с Magister?" → Event Bus (стандарт)
- ❌ "Где хранить данные?" → БД + Obsidian (стандарт)
- ❌ "Как обрабатывать ошибки API?" → Retry 10x, 1 min (стандарт)
- ❌ "Нужна ли интеграция с Teacher Agent?" → Да (стандарт)

### 2. Mock Data Rule:
- ❌ НИКОГДА не использовать mock данные в production коде
- ✅ Всегда запрашивать реальные данные

### 3. Quality Over Speed:
- ✅ Качество важнее скорости
- ✅ Глубокий анализ важнее быстрого результата

### 4. Complete Before Next:
- ✅ Доводим каждую спецификацию до 100%
- ✅ Никаких "доделаем потом"

---

## 📊 ПРОГРЕСС

**ФАЗА 1:** 🚀 В процессе  
- Этап 1.1: ✅ ЗАВЕРШЁН (4/4 P0 спецификации)
- Этап 1.2: ⏳ Готов к старту (15 P1 агентов)
- Этап 1.3: ⏳ Ожидание (9 Orchestrators)
- Этап 1.4: ⏳ Ожидание (системные компоненты)

**Прогресс ФАЗЫ 1:** 8.7% (4/46 спецификаций)  
**Общий прогресс:** ~2% (13-20 недель до production)

---

## 🎯 ПЕРВЫЙ ШАГ В СЛЕДУЮЩЕЙ СЕССИИ

1. Прочитать эту памятку
2. Прочитать `docs/templates/SIMPLIFIED_INTERVIEW_TEMPLATE.md`
3. Прочитать `docs/ARCHITECTURE-COMMUNICATION.md`
4. Спросить пользователя: "Начинаем Этап 1.2? С какого агента начнём?"
5. Провести упрощённое интервью (10-12 вопросов)
6. Создать спецификацию

---

## 📁 КЛЮЧЕВЫЕ ФАЙЛЫ

**Спецификации P0:**
- `docs/subagents-specs/MEDICAL_FACT_CHECKER_SPEC.md`
- `docs/subagents-specs/DATA_RECONCILIATION_SPEC.md`
- `docs/subagents-specs/TONE_OF_VOICE_SPEC.md`
- `docs/subagents-specs/DATA_COLLECTOR_SPEC.md`

**Шаблоны:**
- `docs/templates/SIMPLIFIED_INTERVIEW_TEMPLATE.md` (новый, упрощённый)
- `docs/templates/SUBAGENT_SPEC_TEMPLATE.md` (базовый шаблон)

**Документация:**
- `docs/ARCHITECTURE-COMMUNICATION.md` (стандартные паттерны)
- `docs/MASTER-PLAN.md` (общий план проекта)
- `docs/SUBAGENTS-PRIORITIZATION.md` (приоритеты агентов)
- `docs/PHASE-1-STAGE-1.1-COMPLETE.md` (отчёт о завершении)

**Текущая работа:**
- `SESSION.md` (обновлён, статус Этап 1.1 ✅)

---

## 🚨 BACKLOG (не забыть!)

1. **Doctor Agent** (P1)
   - Мониторинг здоровья системы
   - Сигнализация о "заболевших" компонентах
   - Hourly ping для критичных компонентов

2. **Synthetic CustDev**
   - Проверить версию (old vs new)
   - Путь: `AIM/old/` или `AIM/src/aim/tools/`

---

**Дата создания:** 2026-05-09 20:37 GMT+3  
**Статус:** ✅ Готово к следующей сессии  
**Следующий шаг:** Этап 1.2 - Keyword Research Agent (или другой P1 агент по выбору пользователя)
