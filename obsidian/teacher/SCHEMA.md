---
title: "Teacher Agent Vault Schema"
type: schema
created: 2026-05-03T08:38
---

# Teacher Agent Vault Schema

## Purpose

**Teacher (Ректор) — центр обучающей системы агентства.**

Получает знания из Architect wiki, распределяет магистрам, обрабатывает обратную связь, улучшает стратегию обучения.

## Structure (LLM Wiki Pattern)

```
teacher/
├── raw/                        # Входящие знания (от Architect)
├── wiki/                       # Структурированное знание
│   ├── index.md               # Каталог знаний
│   ├── log.md                 # Хронология операций
│   ├── magisters/             # Информация о магистрах
│   ├── strategies/            # Стратегии обучения
│   ├── feedback/              # Обратная связь от магистров
│   └── escalations/           # Эскалации к Operator
├── decisions/                 # Решения Teacher
└── SCHEMA.md                  # Этот файл
```

## Operations

### 1. Ingest (Обработка знаний)

**Источник:** Architect wiki (sources/, connections/, strategies/)

**Процесс:**
1. Получить уведомление о новом wiki-документе
2. Определить релевантных магистров
3. Создать задачи для магистров
4. Залогировать в wiki/log.md

**Результат:** Знание распределено магистрам

### 2. Feedback (Обратная связь)

**Источник:** Magisters через Event Bus

**Типы:**
- `missing_knowledge` - не хватает знаний
- `outdated_info` - информация устарела
- `system_improvement` - предложение улучшения
- `escalation` - эскалация к Operator

**Процесс:**
1. Получить feedback от магистра
2. Обработать согласно типу
3. Создать задачу (поиск знаний / обновление / эскалация)
4. Залогировать в wiki/feedback/

**Результат:** Проблема решена или эскалирована

### 3. Strategy (Стратегия обучения)

**Цель:** Улучшать эффективность обучения

**Метрики:**
- Knowledge distribution time
- Feedback response time
- Magister satisfaction
- System improvement rate

**Процесс:**
1. Анализировать метрики
2. Выявлять паттерны в feedback
3. Обновлять стратегию обучения
4. Уведомлять магистров о изменениях

**Результат:** Система обучения улучшается

## Frontmatter Standards

### raw/ files

```yaml
---
title: "Название"
source: "architect/wiki/sources/filename.md"
created: 2026-05-03T08:00:00Z
type: "knowledge_update"
relevant_magisters: ["seo-magister", "content-magister"]
status: "pending"  # pending → processing → distributed
---
```

### wiki/ files

```yaml
---
title: "Название"
type: "magister_info | strategy | feedback | escalation"
created: 2026-05-03T08:00:00Z
priority: "critical | high | medium | low"
status: "active | resolved | escalated"
tags:
  - tag1
  - tag2
---
```

### decisions/ files

```yaml
---
title: "Название решения"
type: "decision"
created: 2026-05-03T08:00:00Z
decision_type: "strategy_update | magister_creation | escalation"
impact: "high | medium | low"
status: "approved | implemented"
---
```

## Communication

### Входящие:
- Architect wiki → Teacher raw/
- Magisters feedback → Teacher wiki/feedback/

### Исходящие:
- Teacher → Magisters (через Event Bus)
- Teacher → Operator (эскалации через Event Bus)

## Rules

1. **Всегда следовать LLM Wiki Pattern** (raw → wiki → decisions)
2. **Обрабатывать feedback в течение 1 часа**
3. **Распределять знания в течение 5 минут**
4. **Логировать все операции в wiki/log.md**
5. **Эскалировать системные проблемы Operator**
6. **Обновлять стратегию на основе метрик**

## Metrics

**Target:**
- Knowledge distribution: <5 минут
- Feedback response: <1 час
- Magister satisfaction: >80%
- System improvements: 1+/неделя

**Tracking:**
- wiki/log.md - хронология операций
- wiki/strategies/metrics.md - метрики эффективности

---

**Last updated:** 2026-05-03T08:38:00Z
