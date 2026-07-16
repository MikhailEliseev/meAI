# ADR-002: Event Sourcing

**Date:** 2026-05-01  
**Status:** Accepted  
**Deciders:** Mikhail Eliseev, Claude Opus 4.6

## Context

Нужен способ:
- Отслеживать все изменения в системе
- Восстанавливать состояние после сбоев
- Иметь полный audit trail
- Дебажить проблемы

## Decision

Используем **Event Sourcing** паттерн:
- Все изменения = immutable события
- События хранятся в Event Store
- Состояние = replay событий

## Rationale

### Почему Event Sourcing?
- ✅ Complete audit trail
- ✅ Time travel (восстановление на любой момент)
- ✅ Easy debugging
- ✅ Replay для recovery
- ✅ Analytics из событий

### Почему не CRUD?
- ❌ Теряется история изменений
- ❌ Нет audit trail
- ❌ Сложно дебажить
- ❌ Невозможно восстановить прошлое состояние

## Implementation

```python
Event {
    aggregate_id: "agent-123",
    event_type: "task_completed",
    payload: {...},
    timestamp: "...",
    idempotency_key: "unique"
}
```

## Consequences

### Positive
- Полная история всех действий
- Легко понять что произошло
- Можно replay для восстановления
- Отличный debugging

### Negative
- Больше записей в базу
- Нужно проектировать события
- Replay может быть медленным

## Alternatives Considered

1. **CRUD** — rejected (нет истории)
2. **Change Data Capture** — rejected (сложнее)
3. **Audit Log** — rejected (не полный)

## See Also

- [Event Sourcing Architecture](../architecture/event-sourcing.md)
- [Event Store API](../api/event-store.md)
- [Tutorial: Event Sourcing](../tutorials/03-event-sourcing.md)
