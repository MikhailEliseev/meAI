# ADR-005: Obsidian for Agent Memory

**Date:** 2026-05-01  
**Status:** Accepted  
**Deciders:** Mikhail Eliseev, Claude Opus 4.6

## Context

Агентам нужна память для:
- Хранения контекста
- Накопления learnings
- Логирования задач
- Записи решений

## Decision

Используем **Obsidian** (markdown files) для памяти агентов.

## Rationale

### Почему Obsidian?
- ✅ **Human-readable** — можно читать в любом редакторе
- ✅ **Visual graph** — видно связи между заметками
- ✅ **Full-text search** — быстрый поиск
- ✅ **Rich ecosystem** — плагины, темы
- ✅ **Git-friendly** — легко версионировать
- ✅ **Markdown** — универсальный формат
- ✅ **Wikilinks** — связи между заметками

### Почему не база данных?
- ❌ Не human-readable
- ❌ Нет визуального графа
- ❌ Сложнее редактировать вручную

### Почему не plain files?
- ❌ Нет графа связей
- ❌ Нет rich UI
- ❌ Хуже поиск

## Implementation

```
obsidian/agents/{agent_id}/
├── README.md
├── memory/
│   ├── context.md
│   └── learnings.md
├── tasks/
└── decisions/
```

## Use Cases

1. **Debugging** — читаем память агента
2. **Analysis** — граф связей
3. **Editing** — правим вручную
4. **Backup** — git commit

## Consequences

### Positive
- Легко читать и редактировать
- Визуальный граф знаний
- Отличный UX для разработчиков
- Git-friendly

### Negative
- Нужно устанавливать Obsidian
- Файловая система (не база)
- Нет транзакций

## Alternatives Considered

1. **PostgreSQL** — rejected (не human-readable)
2. **Plain files** — rejected (нет графа)
3. **Notion** — rejected (проприетарный)
4. **Roam Research** — rejected (дорого)

## See Also

- [Obsidian Vault API](../api/obsidian.md)
- [Tutorial: Memory System](../tutorials/02-memory-system.md)
- [ADR-001: Dual Storage](001-dual-storage.md)
