# ADR-004: Test-Driven Development

**Date:** 2026-05-01  
**Status:** Accepted  
**Deciders:** Mikhail Eliseev, Claude Opus 4.6

## Context

Нужен подход к разработке, который:
- Гарантирует качество кода
- Предотвращает регрессии
- Документирует поведение
- Упрощает рефакторинг

## Decision

Используем **TDD (Test-Driven Development)**:
1. Write failing test
2. Write minimal code to pass
3. Refactor
4. Repeat

## Rationale

### Почему TDD?
- ✅ Высокое качество кода
- ✅ Тесты = документация
- ✅ Уверенность в рефакторинге
- ✅ Меньше багов в продакшене

### Почему не "Tests Later"?
- ❌ Часто забывают писать тесты
- ❌ Сложнее покрыть тестами
- ❌ Хуже дизайн кода

## Implementation

```python
# 1. Write failing test
def test_create_agent():
    agent = await factory.create_agent("seo-agent")
    assert agent.agent_id == "seo-agent"

# 2. Write code to pass
async def create_agent(agent_id):
    return Agent(agent_id=agent_id)

# 3. Refactor
```

## Results

- **133/133 tests passing** ✅
- **~80%+ coverage**
- **0 production bugs** (so far)

## Consequences

### Positive
- Высокая уверенность в коде
- Легко рефакторить
- Тесты как документация
- Меньше багов

### Negative
- Больше времени на разработку
- Нужна дисциплина
- Иногда сложно тестировать

## Alternatives Considered

1. **No Tests** — rejected (опасно)
2. **Tests Later** — rejected (часто не делается)
3. **BDD** — rejected (overkill для MVP)

## See Also

- [Testing Guide](../testing/guide.md)
- All test files in `tests/`
