---

excalidraw-plugin: parsed
tags: [excalidraw]

---
==⚠  Switch to EXCALIDRAW VIEW in the MORE OPTIONS menu of this document. ⚠== You can decompress Drawing data with the command palette: 'Decompress current Excalidraw file'. For more info check in plugin settings under 'Saving'


## Drawing
```compressed-json
N4IgLgngDgpiBcIYA8DGBDANgSwCYCd0B3EAGhADcZ8BnbAewDsEAmcm+gV31TkQAswYKDXgB6MQHNsYfpwBGAOlT0AtmIBeNCtlQbs6RmPry6uA4wC0KDDgLFLUTJ2lH8MTDHQ0YNMWHRJMRZFFhCAZjIkT1UYRjAaBABtAF1ydCgoAGUAsD5QSXw8LOwNPkZOTExyHRgiACF0VABrQq5GXABhekx6fAQQAGIAM1GxkABfCaA==
```
%%

---

# 📐 Структура AIM Agency - Полное описание

## 🎯 Общая архитектура

AIM (AI-first Medical Marketing Agency) — трёхслойная иерархическая система с автономными агентами.

### Три слоя иерархии

```
┌─────────────────────────────────────────────────────────┐
│  STRATEGY LAYER (Стратегический слой)                   │
│                                                          │
│  YOU (Human) ──► ARCHITECT (Strategic Decision Maker)   │
│                                                          │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  TACTICAL LAYER (Тактический слой)                      │
│                                                          │
│  OPERATOR (Autonomous Operations Director)              │
│                                                          │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  EXECUTION LAYER (Исполнительный слой)                  │
│                                                          │
│  MAGISTERS ──► SUBAGENTS                                │
│  (Координаторы доменов → Исполнители задач)            │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 🟦 STRATEGY LAYER (Стратегический слой)

### YOU (Human)
- **Роль:** Medical marketer, основатель агентства
- **Задачи:** Постановка стратегических целей
- **Взаимодействие:** Задаёт вопросы Architect, получает отчёты от Operator

### ARCHITECT (Стратегический советник)
- **Файл:** `src/meai/core/architect.py`
- **Статус:** ✅ IMPLEMENTED
- **Функции:**
  - Анализ контекста и ограничений
  - Генерация альтернативных стратегий
  - Принятие стратегических решений
  - Обучение на результатах

**Компоненты:**
- **Decision Maker** — выбор стратегии с обучением
- **Orchestrator** — координация async задач
- **Rollback System** — откат при ошибках

---

## 🟩 TACTICAL LAYER (Тактический слой)

### OPERATOR (Автономный операционный директор)
- **Файл:** `src/meai/agents/operator.py`
- **Статус:** ✅ IMPLEMENTED
- **Функции:**
  - Получение задач от Architect
  - Принятие тактических решений
  - Делегирование задач агентам через Event Bus
  - Сбор результатов от агентов
  - Агрегация и отчёт YOU

**Стратегии выполнения:**
- **Direct** — одна задача, один агент
- **Sequential** — последовательное выполнение
- **Parallel** — параллельное выполнение
- **Hybrid** — фазы с параллельными подзадачами

---

## 🟨 EXECUTION LAYER (Исполнительный слой)

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

### 1. SEO Domain

**SEO Magister** (Координатор SEO домена)
- **Файл:** `AIM/src/aim/magisters/seo_magister.py`
- **Статус:** ⏳ TODO
- **Vault:** `AIM/obsidian/seo-magister/`

**SEO Subagents:**
1. **SEO Subagent 1** — Анализ конкурентов
2. **SEO Subagent 2** — Подбор ключевых слов
3. **SEO Subagent 3** — Оптимизация контента
4. **SEO Subagent 4** — Мониторинг позиций

### 2. Content Domain

**Content Magister** (Координатор контента)
- **Файл:** `AIM/src/aim/magisters/content_magister.py`
- **Статус:** ⏳ TODO
- **Vault:** `AIM/obsidian/content-magister/`

**Content Subagents:**
1. **Content Subagent 1** — Генерация контента
2. **Content Subagent 2** — Редактура и проверка
3. **Content Subagent 3** — SEO-оптимизация текстов
4. **Content Subagent 4** — Планирование публикаций

### 3. Ads Domain

**Ads Magister** (Координатор рекламы)
- **Файл:** `AIM/src/aim/magisters/ads_magister.py`
- **Статус:** ⏳ TODO
- **Vault:** `AIM/obsidian/ads-magister/`

**Ads Subagents:**
1. **Ads Subagent 1** — Создание кампаний
2. **Ads Subagent 2** — Оптимизация бюджета
3. **Ads Subagent 3** — A/B тестирование
4. **Ads Subagent 4** — Анализ конверсий

---

## 🟪 INFRASTRUCTURE (Инфраструктура)

### Event Bus (Шина событий)
- **Файл:** `src/meai/events/event_bus.py`
- **Статус:** ✅ IMPLEMENTED
- **Функции:**
  - Async messaging между агентами
  - Priority queues (P0-P3)
  - Pub/Sub паттерн
  - Гарантированная доставка

### Event Store (Хранилище событий)
- **Файл:** `src/meai/events/event_store.py`
- **Статус:** ✅ IMPLEMENTED
- **Функции:**
  - Immutable audit log
  - Event sourcing
  - Replay для отладки
  - История всех операций

### Memory System (Obsidian Vaults)
- **Файл:** `src/meai/memory/obsidian.py`
- **Статус:** ✅ IMPLEMENTED
- **Паттерн:** LLM Wiki (Karpathy)

**Структура vaults:**
```
obsidian/
├── architect/           # Стратегические решения
├── operator/            # Тактические планы
├── seo-magister/        # SEO домен
├── content-magister/    # Content домен
└── ads-magister/        # Ads домен
```

**Каждый vault:**
```
vault/
├── raw/                 # Исходные данные (immutable)
├── wiki/                # Структурированное знание
│   ├── index.md        # Каталог
│   ├── log.md          # История операций
│   ├── concepts/       # Концепции
│   ├── strategies/     # Стратегии
│   └── sources/        # Обработанные источники
└── decisions/          # Решения
```

### Database (SQLite)
- **Файл:** `src/meai/storage/database.py`
- **Статус:** ✅ IMPLEMENTED
- **Технология:** SQLAlchemy 2.0 async
- **Хранит:**
  - Tasks (задачи)
  - Metrics (метрики)
  - Logs (логи)
  - Decisions (решения)

### Agent Factory
- **Файл:** `src/meai/agents/factory.py`
- **Статус:** ✅ IMPLEMENTED
- **Функции:**
  - Создание агентов
  - Конфигурация
  - Dependency injection

---

## 🔄 Полный E2E поток (End-to-End Flow)

```
1. YOU
   │
   │ "Запустить iamaim.ru успешно"
   │
   ▼
2. ARCHITECT
   │
   │ • Анализ контекста (бюджет, время, ресурсы)
   │ • Генерация альтернатив (3-5 стратегий)
   │ • Выбор оптимальной стратегии
   │ • Решение: "SEO + Content + Ads параллельно"
   │
   ▼
3. OPERATOR
   │
   │ • Получение стратегического решения
   │ • Тактическое решение: Parallel Strategy
   │ • Декомпозиция на задачи для доменов
   │
   ▼
4. EVENT BUS (Делегирование)
   │
   ├──► SEO MAGISTER
   │    │ • Получение задачи "SEO оптимизация"
   │    │ • Декомпозиция на подзадачи
   │    │
   │    ├──► SEO Subagent 1: Анализ конкурентов
   │    ├──► SEO Subagent 2: Подбор ключевых слов
   │    ├──► SEO Subagent 3: Оптимизация контента
   │    └──► SEO Subagent 4: Мониторинг позиций
   │
   ├──► CONTENT MAGISTER
   │    │ • Получение задачи "Создание контента"
   │    │ • Декомпозиция на подзадачи
   │    │
   │    ├──► Content Subagent 1: Генерация статей
   │    ├──► Content Subagent 2: Редактура
   │    ├──► Content Subagent 3: SEO-оптимизация
   │    └──► Content Subagent 4: Планирование публикаций
   │
   └──► ADS MAGISTER
        │ • Получение задачи "Рекламные кампании"
        │ • Декомпозиция на подзадачи
        │
        ├──► Ads Subagent 1: Создание кампаний
        ├──► Ads Subagent 2: Оптимизация бюджета
        ├──► Ads Subagent 3: A/B тестирование
        └──► Ads Subagent 4: Анализ конверсий

5. SUBAGENTS (Выполнение)
   │
   │ • Каждый subagent выполняет свою задачу
   │ • Сохраняет результаты в Obsidian vault
   │ • Записывает метрики в Database
   │ • Публикует результат в Event Bus
   │
   ▼
6. MAGISTERS (Агрегация)
   │
   │ • Собирают результаты от subagents
   │ • Агрегируют по домену
   │ • Публикуют сводный результат в Event Bus
   │
   ▼
7. OPERATOR (Сбор результатов)
   │
   │ • Получает результаты от всех Magisters
   │ • Агрегирует в единый отчёт
   │ • Формирует executive summary
   │
   ▼
8. YOU (Получение отчёта)
   │
   │ • Читает отчёт от Operator
   │ • Даёт обратную связь
   │
   ▼
9. ARCHITECT (Обучение)
   │
   │ • Получает feedback от YOU
   │ • Обновляет Decision Maker
   │ • Улучшает будущие решения
   │
   └──► Цикл повторяется
```

---

## 🎨 Цветовая схема для визуализации

- 🟦 **Стратегический слой** (YOU, ARCHITECT) — синий
- 🟩 **Тактический слой** (OPERATOR) — зелёный
- 🟨 **Исполнительный слой** (MAGISTERS, SUBAGENTS) — жёлтый
- 🟪 **Инфраструктура** (Event Bus, Database, Obsidian) — фиолетовый

**Связи:**
- ➡️ **Команды** (сверху вниз) — сплошные стрелки
- ⬅️ **Результаты** (снизу вверх) — пунктирные стрелки
- ↔️ **Взаимодействие** (между агентами) — двойные стрелки

---

## 📊 Статус компонентов

### ✅ Реализовано (IMPLEMENTED)
- Architect (стратегический слой)
- Decision Maker (обучение)
- Orchestrator (координация)
- Rollback System (откат)
- Operator (тактический слой)
- Base Agent (базовый класс)
- Event Bus (коммуникация)
- Event Store (аудит)
- Obsidian Integration (память)
- Database (хранилище)
- Agent Factory (создание агентов)

### ⏳ В разработке (TODO)
- SEO Magister + Subagents
- Content Magister + Subagents
- Ads Magister + Subagents
- FastAPI Server (API)
- Docker Setup (деплой)
- Monitoring (мониторинг)

---

## 🎯 Ключевые принципы архитектуры

1. **Иерархия:** Три чётких слоя (Strategy → Tactical → Execution)
2. **Автономность:** Каждый агент принимает решения самостоятельно
3. **Async:** Все операции асинхронные через Event Bus
4. **Memory:** Каждый агент имеет свой Obsidian vault (LLM Wiki)
5. **Learning:** Система обучается на результатах (Decision Maker)
6. **Rollback:** Возможность отката при ошибках (Event Store + Snapshots)
7. **Observability:** Полный аудит через Event Store и Database

---

**Дата создания:** 2026-05-05  
**Версия:** 1.0  
**Статус:** Active Development