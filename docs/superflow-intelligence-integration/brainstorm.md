# Intelligence Magister Integration - Brainstorming

**Date:** 2026-05-06  
**Phase:** Discovery - Brainstorming  
**Status:** Evaluating approaches

---

## Problem Statement

Integrate Intelligence Magister with CI System to enable:
1. Operator → Intelligence Magister task delegation
2. Intelligence Magister → CI Agents orchestration
3. Result aggregation and reporting back to Operator

---

## Approach 1: Direct CI Integration (Simple)

**Concept:** Intelligence Magister directly imports and calls CI agents

```python
class IntelligenceMagister(BaseMagister):
    async def execute_task(self, task: Task) -> TaskResult:
        # Import CI agents
        from aim.subagents.competitive_intel.agents.ci_deep_analyzer import CIDeepAnalyzer
        
        # Create and run
        analyzer = CIDeepAnalyzer(...)
        result = await analyzer.execute_task(task)
        
        return result
```

**Pros:**
- ✅ Простая реализация
- ✅ Быстро (1-2 часа)
- ✅ Прямой контроль над CI агентами

**Cons:**
- ❌ Tight coupling (Intelligence Magister зависит от AIM)
- ❌ Нарушает архитектуру (Framework → Application dependency)
- ❌ Сложно тестировать изолированно
- ❌ Не масштабируется на другие Magisters

**Verdict:** ❌ Не подходит (нарушает архитектуру)

---

## Approach 2: Event Bus Orchestration (Architectural)

**Concept:** Intelligence Magister оркестрирует через Event Bus

```python
class IntelligenceMagister(BaseMagister):
    async def execute_task(self, task: Task) -> TaskResult:
        # 1. Publish task to CI agents via Event Bus
        await self.event_bus.publish(Event(
            type="ci.analyze_competitor",
            data={"url": task.data["url"]},
            priority=1
        ))
        
        # 2. Subscribe to results
        results = []
        async for event in self.event_bus.subscribe("ci.result.*"):
            results.append(event.data)
            if len(results) == expected_count:
                break
        
        # 3. Aggregate and return
        return self.aggregate_results(results)
```

**Pros:**
- ✅ Правильная архитектура (loose coupling)
- ✅ Масштабируется на другие Magisters
- ✅ Легко тестировать (mock Event Bus)
- ✅ CI агенты могут быть в другом процессе/сервисе

**Cons:**
- ⚠️ Сложнее реализация (3-4 часа)
- ⚠️ Нужна регистрация CI агентов в Event Bus
- ⚠️ Нужна логика ожидания результатов

**Verdict:** ✅ Правильный подход, но сложнее

---

## Approach 3: Hybrid (Pragmatic)

**Concept:** Intelligence Magister как адаптер между Event Bus и CI

```python
class IntelligenceMagister(BaseMagister):
    def __init__(self, ...):
        super().__init__(...)
        # Register CI orchestrator
        self.ci_orchestrator = CIOrchestrator(
            event_bus=self.event_bus,
            ci_agents_path="AIM/src/aim/subagents/competitive_intel"
        )
    
    async def execute_task(self, task: Task) -> TaskResult:
        # Delegate to orchestrator
        result = await self.ci_orchestrator.execute(task)
        
        # Store in vault
        await self.store_result(result)
        
        return result
```

**CIOrchestrator:**
- Живёт в AIM (application layer)
- Знает про CI агентов
- Общается через Event Bus
- Intelligence Magister не знает деталей CI

**Pros:**
- ✅ Правильная архитектура (separation of concerns)
- ✅ Intelligence Magister остаётся generic
- ✅ CI логика изолирована в AIM
- ✅ Легко добавить другие orchestrators (SEO, Content)
- ✅ Умеренная сложность (2-3 часа)

**Cons:**
- ⚠️ Дополнительный слой абстракции
- ⚠️ Нужно создать CIOrchestrator

**Verdict:** ✅✅ Лучший баланс архитектуры и прагматизма

---

## Approach 4: Plugin System (Over-engineered)

**Concept:** Intelligence Magister загружает CI как plugin

```python
class IntelligenceMagister(BaseMagister):
    def __init__(self, ...):
        super().__init__(...)
        self.plugins = PluginManager()
        self.plugins.load("competitive_intel")
    
    async def execute_task(self, task: Task) -> TaskResult:
        plugin = self.plugins.get("competitive_intel")
        return await plugin.execute(task)
```

**Pros:**
- ✅ Максимальная гибкость
- ✅ Hot-reload plugins
- ✅ Изоляция

**Cons:**
- ❌ Over-engineering для текущей задачи
- ❌ Долго (5-6 часов)
- ❌ Сложность без явной выгоды

**Verdict:** ❌ Overkill для MVP

---

## Recommended Approach: #3 (Hybrid)

**Why:**
1. **Правильная архитектура** - Framework не зависит от Application
2. **Прагматичность** - Не over-engineering, но и не костыль
3. **Масштабируемость** - Легко добавить SEO/Content orchestrators
4. **Тестируемость** - Можно тестировать слои независимо
5. **Время** - 2-3 часа (приемлемо для Critical mode)

---

## Implementation Plan (High-Level)

### Sprint 1: Intelligence Magister Core (1.5h)
1. Implement `execute_task()` in Intelligence Magister
2. Add task routing logic (analyze_competitor → CI)
3. Add result storage to vault
4. Unit tests

### Sprint 2: CI Orchestrator (1h)
1. Create `CIOrchestrator` class in AIM
2. Integrate with CI Deep Analyzer
3. Event Bus communication
4. Error handling

### Sprint 3: Integration & Testing (1h)
1. End-to-end test: Operator → Intelligence → CI → Report
2. Integration tests
3. Documentation
4. Performance testing

**Total:** 3.5 hours

---

## Open Questions

1. **Q:** Как Intelligence Magister узнаёт о доступных orchestrators?
   **A:** Registry pattern или config file

2. **Q:** Что если CI агент падает?
   **A:** Retry logic + timeout в orchestrator

3. **Q:** Как передавать большие результаты (PDF reports)?
   **A:** Через file path, не через Event Bus payload

4. **Q:** Нужна ли очередь задач для CI?
   **A:** Пока нет, но можно добавить позже

---

## Next Steps

1. ✅ Research complete
2. ✅ Brainstorming complete
3. → Present approaches to user
4. → Get approval on Approach #3
5. → Create detailed technical spec
6. → Create implementation plan
7. → User approval
8. → Phase 2 execution

---

**Status:** Ready for user review  
**Recommended:** Approach #3 (Hybrid)  
**ETA:** 3.5 hours implementation
