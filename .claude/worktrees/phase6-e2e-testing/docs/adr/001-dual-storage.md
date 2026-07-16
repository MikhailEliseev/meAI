# ADR-001: Dual Storage (SQLite + Obsidian)

**Date:** 2026-05-01  
**Status:** Accepted  
**Deciders:** Mikhail Eliseev, Claude Opus 4.6

## Context

meAI нужно хранить два типа данных:
1. Структурированные (метаданные, метрики, события)
2. Неструктурированные (память агентов, контекст, learnings)

## Decision

Используем **dual storage** подход:
- **SQLite** для структурированных данных
- **Obsidian** для неструктурированных знаний

## Rationale

### Почему SQLite?
- ✅ Async support (aiosqlite)
- ✅ Zero configuration
- ✅ Fast queries
- ✅ ACID transactions
- ✅ Perfect for MVP

### Почему Obsidian?
- ✅ Human-readable (markdown)
- ✅ Visual graph view
- ✅ Full-text search
- ✅ Rich ecosystem (plugins)
- ✅ Git-friendly

### Почему не одно решение?
- ❌ PostgreSQL — overkill для MVP
- ❌ MongoDB — не нужна схема-less база
- ❌ Только файлы — нет быстрых queries
- ❌ Только база — не human-readable

## Consequences

### Positive
- Лучшее из двух миров
- Быстрые queries + human-readable память
- Легко бэкапить оба
- Можно мигрировать на PostgreSQL позже

### Negative
- Два хранилища для управления
- Нужна синхронизация
- Больше кода для поддержки

## Alternatives Considered

1. **Only PostgreSQL** — rejected (overkill, не human-readable)
2. **Only Files** — rejected (нет быстрых queries)
3. **MongoDB** — rejected (не нужна NoSQL)

## See Also

- [Storage Architecture](../architecture/storage.md)
- [Database API](../api/database.md)
- [Obsidian API](../api/obsidian.md)
