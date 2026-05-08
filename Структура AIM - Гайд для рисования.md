---
excalidraw-plugin: parsed
tags:
  - excalidraw
---
# Структура AIM Agency - Гайд для Excalidraw

## 🎯 Что рисовать

Полная архитектура AI-first медицинского маркетингового агентства с тремя слоями иерархии.

---

## 📐 Слой 1: Стратегический (Strategy Layer)

### YOU (Human)
```
┌─────────────────────┐
│        YOU          │
│   (Medical          │
│    Marketer)        │
└─────────────────────┘
         │
         │ стратегические вопросы
         ▼
```

### ARCHITECT
```
┌─────────────────────────────────────┐
│          ARCHITECT                  │
│   (Strategic Decision Maker)        │
│                                     │
│  • Анализ контекста                │
│  • Генерация альтернатив            │
│  • Принятие решений                 │
│  • Обучение на результатах          │
└─────────────────────────────────────┘
         │
         │ стратегические решения
         ▼
```

**Компоненты Architect:**
- Decision Maker (выбор стратегии)
- Orchestrator (координация)
- Rollback System (откат при ошибках)

---

## 📐 Слой 2: Тактический (Tactical Layer)

### OPERATOR
```
┌─────────────────────────────────────┐
│           OPERATOR                  │
│   (Autonomous Operations Director)  │
│                                     │
│  • Получение задач                 │
│  • Тактические решения             │
│  • Делегирование агентам           │
│  • Сбор результатов                │
│  • Отчёты YOU                      │
└─────────────────────────────────────┘
         │
         │ делегирование через Event Bus
         ▼
```

**Стратегии выполнения:**
- Direct (1 задача → 1 агент)
- Sequential (последовательно)
- Parallel (параллельно)
- Hybrid (фазы с подзадачами)

---

## 📐 Слой 3: Исполнительный (Execution Layer)

### Три домена с Magisters + Subagents

```
┌──────────────────────────────────────────────────────────┐
│                    EXECUTION LAYER                       │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │SEO MAGISTER │  │CONTENT      │  │ADS MAGISTER │    │
│  │             │  │MAGISTER     │  │             │    │
│  │  Координ.   │  │             │  │  Координ.   │    │
│  │  SEO домена │  │  Координ.   │  │  Ads домена │    │
│  │             │  │  Content    │  │             │    │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │
│         │                │                │            │
│    ┌────┴────┐      ┌────┴────┐      ┌────┴────┐      │
│    │         │      │         │      │         │      │
│    ▼         ▼      ▼         ▼      ▼         ▼      │
│  ┌───┐    ┌───┐  ┌───┐    ┌───┐  ┌───┐    ┌───┐     │
│  │SEO│    │SEO│  │Cont│   │Cont│ │Ads│    │Ads│     │
│  │Sub│    │Sub│  │Sub │   │Sub │ │Sub│    │Sub│     │
│  │ 1 │    │ 2 │  │ 1  │   │ 2  │ │ 1 │    │ 2 │     │
│  └───┘    └───┘  └───┘    └───┘  └───┘    └───┘     │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**SEO Domain:**
- SEO Magister (координатор)
  - SEO Subagent 1 (анализ конкурентов)
  - SEO Subagent 2 (подбор ключевых слов)
  - SEO Subagent 3 (оптимизация контента)
  - SEO Subagent 4 (мониторинг позиций)

**Content Domain:**
- Content Magister (координатор)
  - Content Subagent 1 (генерация контента)
  - Content Subagent 2 (редактура)
  - Content Subagent 3 (SEO-оптимизация)
  - Content Subagent 4 (планирование публикаций)

**Ads Domain:**
- Ads Magister (координатор)
  - Ads Subagent 1 (создание кампаний)
  - Ads Subagent 2 (оптимизация бюджета)
  - Ads Subagent 3 (A/B тестирование)
  - Ads Subagent 4 (анализ конверсий)

---

## 📐 Инфраструктура (Infrastructure)

### Event Bus (Шина Событий)
```
┌─────────────────────────────────────┐
│          EVENT BUS                  │
│   (Async Messaging System)          │
│                                     │
│  • Priority Queues (P0-P3)         │
│  • Pub/Sub                         │
│  • Agent Communication             │
└─────────────────────────────────────┘
```

### Memory System (Obsidian Vaults)
```
┌─────────────────────────────────────┐
│       MEMORY SYSTEM                 │
│   (Obsidian Vaults - LLM Wiki)      │
│                                     │
│  obsidian/                          │
│  ├── architect/      (стратегия)   │
│  ├── operator/       (тактика)     │
│  ├── seo-magister/   (SEO домен)   │
│  ├── content-magister/ (контент)   │
│  └── ads-magister/   (реклама)     │
└─────────────────────────────────────┘
```

### Database (SQLite)
```
┌─────────────────────────────────────┐
│          DATABASE                   │
│   (SQLite + SQLAlchemy Async)       │
│                                     │
│  • Tasks                           │
│  • Metrics                         │
│  • Logs                            │
│  • Decisions                       │
└─────────────────────────────────────┘
```

### Event Store (Audit Log)
```
┌─────────────────────────────────────┐
│        EVENT STORE                  │
│   (Immutable Audit Log)             │
│                                     │
│  • Event Sourcing                  │
│  • Replay                          │
│  • Debugging                       │
└─────────────────────────────────────┘
```

---

## 🔄 Полный поток данных (E2E Flow)

```
1. YOU
   │
   │ "Запустить iamaim.ru успешно"
   ▼
2. ARCHITECT
   │
   │ Анализ → Альтернативы → Решение
   │ "Стратегия: SEO + Content + Ads"
   ▼
3. OPERATOR
   │
   │ Тактическое решение: Parallel Strategy
   │ Делегирование через Event Bus
   ▼
4. EVENT BUS
   │
   ├──► SEO MAGISTER
   │    │
   │    ├──► SEO Subagent 1 (анализ конкурентов)
   │    ├──► SEO Subagent 2 (ключевые слова)
   │    └──► SEO Subagent 3 (оптимизация)
   │
   ├──► CONTENT MAGISTER
   │    │
   │    ├──► Content Subagent 1 (генерация)
   │    ├──► Content Subagent 2 (редактура)
   │    └──► Content Subagent 3 (SEO-оптимизация)
   │
   └──► ADS MAGISTER
        │
        ├──► Ads Subagent 1 (кампании)
        ├──► Ads Subagent 2 (бюджет)
        └──► Ads Subagent 3 (A/B тесты)
   
5. Результаты через Event Bus
   │
   ▼
6. OPERATOR
   │
   │ Агрегация результатов
   │ Формирование отчёта
   ▼
7. YOU
   │
   │ Получение отчёта
   └──► Обратная связь → ARCHITECT (обучение)
```

---

## 🎨 Цветовая схема для Excalidraw

**Слои:**
- 🟦 **Стратегический** (YOU, ARCHITECT) — синий
- 🟩 **Тактический** (OPERATOR) — зелёный
- 🟨 **Исполнительный** (MAGISTERS, SUBAGENTS) — жёлтый
- 🟪 **Инфраструктура** (Event Bus, Database, Obsidian) — фиолетовый

**Связи:**
- ➡️ **Команды** (сверху вниз) — сплошные стрелки
- ⬅️ **Результаты** (снизу вверх) — пунктирные стрелки
- ↔️ **Взаимодействие** (между агентами) — двойные стрелки

---

## 📝 Ключевые принципы для визуализации

1. **Иерархия сверху вниз:** YOU → ARCHITECT → OPERATOR → MAGISTERS → SUBAGENTS
2. **Горизонтальные домены:** SEO | Content | Ads (на одном уровне)
3. **Инфраструктура снизу:** Event Bus, Database, Obsidian (фундамент)
4. **Двунаправленные потоки:** Команды вниз, результаты вверх
5. **Автономность:** Каждый агент — отдельный блок с логикой

---

## 🎯 Что важно показать

✅ **Три слоя иерархии** (Strategy → Tactical → Execution)
✅ **Три домена** (SEO, Content, Ads)
✅ **Magisters как координаторы** доменов
✅ **Subagents как исполнители** конкретных задач
✅ **Event Bus как центральная шина** коммуникации
✅ **Obsidian vaults** для каждого агента
✅ **Полный E2E поток** от YOU до результата

---

**Используй этот гайд для рисования в Excalidraw!** 🎨

==⚠  Switch to EXCALIDRAW VIEW in the MORE OPTIONS menu of this document. ⚠== You can decompress Drawing data with the command palette: 'Decompress current Excalidraw file'. For more info check in plugin settings under 'Saving'


## Drawing
```compressed-json
N4IgLgngDgpiBcIYA8DGBDANgSwCYCd0B3EAGhADcZ8BnbAewDsEAmcm+gV31TkQAswYKDXgB6MQHNsYfpwBGAOlT0AtmIBeNCtlQbs6RmPry6uA4wC0KDDgLFLUTJ2lH8MTDHQ0YNMWHRJMRZFFhCAZjIkT1UYRjAaBABtAF1ydCgoAGUAsD5QSXw8LOwNPkZOTExyHRgiACF0VABrQq5GXABhekx6fAQQAGIAM1GxkABfCaA==
```
%%