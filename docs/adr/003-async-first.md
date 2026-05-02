# ADR-003: Async-First Architecture

**Date:** 2026-05-01  
**Status:** Accepted  
**Deciders:** Mikhail Eliseev, Claude Opus 4.6

## Context

meAI выполняет много I/O операций:
- Database queries
- File operations
- API calls
- Agent communication

## Decision

Используем **async-first** подход:
- Все I/O операции async
- asyncio для concurrency
- SQLAlchemy 2.0 async
- aiosqlite для SQLite

## Rationale

### Почему Async?
- ✅ Параллельное выполнение
- ✅ Лучшая производительность
- ✅ Меньше блокировок
- ✅ Масштабируемость

### Почему не Sync?
- ❌ Блокирующие операции
- ❌ Хуже производительность
- ❌ Сложнее масштабировать

### Почему не Threading?
- ❌ GIL в Python
- ❌ Сложнее отлаживать
- ❌ Race conditions

## Implementation

```python
# Async everywhere
async def create_agent():
    async with db.session() as session:
        agent = Agent(...)
        session.add(agent)
    
    await vault.write_file(...)
    await event_store.append_event(...)
```

## Consequences

### Positive
- 3-5x лучше throughput
- Параллельное выполнение задач
- Современный Python подход
- Готово к scale

### Negative
- Все должно быть async
- Сложнее для новичков
- Нужно понимать asyncio

## Alternatives Considered

1. **Sync** — rejected (плохая производительность)
2. **Threading** — rejected (GIL, race conditions)
3. **Multiprocessing** — rejected (overkill для MVP)

## See Also

- [Architecture Overview](../architecture/overview.md)
- [Orchestrator API](../api/orchestrator.md)
