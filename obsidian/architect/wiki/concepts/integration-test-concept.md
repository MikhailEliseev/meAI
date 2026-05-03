---
title: "Integration Test Concept"
type: concept
tags: [integration, testing, teacher-agent, monitor]
created: 2026-05-03T09:20
source: [[20260503-0814-integration-test]]
status: active
---

# Integration Test Concept

## Суть концепции

Тестирование интеграции Monitor + Teacher Agent для автоматического распределения знаний.

## Ключевые компоненты

1. **Monitor** - обнаруживает новые файлы в raw/
2. **Gatekeeper** - проверяет качество
3. **Teacher Agent** - распределяет знания магистрам
4. **Event Bus** - связывает компоненты

## Workflow

```
raw/file.md
    ↓
Monitor обнаруживает
    ↓
Gatekeeper проверяет
    ↓
PASS → wiki создан
    ↓
Monitor уведомляет Teacher
    ↓
Teacher распределяет магистрам
```

## Применимость для AIM Agency

**High potential** - автоматизация обучения агентов критична для масштабирования.

## Связи

- [[monitor-gatekeeper-integration]] - базовая интеграция
- [[teacher-agent-implementation]] - реализация Teacher
- [[synthesis-strategy-aim-agency-v2]] - стратегия синтеза

## Следующие шаги

1. Реализовать Monitor Level 2 (автоматическое создание wiki)
2. Протестировать полный цикл: raw → wiki → Teacher → Magisters
3. Создать базы знаний для субагентов
