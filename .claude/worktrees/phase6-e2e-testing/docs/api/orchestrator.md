# Orchestrator API Reference

> Async coordination of components and workflows

## Overview

**Orchestrator** — компонент для асинхронной координации операций. Управляет параллельным выполнением задач, последовательными workflow и health checks компонентов.

## Class: `Orchestrator`

### Constructor

```python
from meai.core.orchestrator import Orchestrator

orchestrator = Orchestrator()
```

**Parameters:**
- None (stateless component)

---

## Methods

### `register_component(name: str, health_check: Callable) -> None`

Register component for orchestration.

**Parameters:**
- `name` (str) — Component name
- `health_check` (Callable) — Async function that returns health status

**Returns:**
- None

**Example:**

```python
async def database_health():
    return {"status": "healthy", "connections": 5}

async def vault_health():
    return {"status": "healthy", "files": 1234}

orchestrator.register_component("database", database_health)
orchestrator.register_component("vault", vault_health)
```

---

### `check_all_components() -> dict[str, dict]`

Check health of all registered components in parallel.

**Parameters:**
- None

**Returns:**
- `dict[str, dict]` — Health status for each component

**Example:**

```python
status = await orchestrator.check_all_components()

for name, health in status.items():
    print(f"{name}: {health['status']}")
```

**Output:**
```
database: healthy
vault: healthy
event_store: healthy
```

**Error Handling:**

```python
# If component fails, error is captured
status = await orchestrator.check_all_components()

if status["database"]["status"] == "error":
    print(f"Database error: {status['database']['error']}")
```

---

### `execute_workflow(workflow: list[Callable]) -> list[Any]`

Execute workflow steps sequentially.

**Parameters:**
- `workflow` (list[Callable]) — List of async functions to execute in order

**Returns:**
- `list[Any]` — Results from each step

**Example:**

```python
async def step1():
    print("Step 1: Initialize")
    return "initialized"

async def step2():
    print("Step 2: Process")
    return "processed"

async def step3():
    print("Step 3: Finalize")
    return "finalized"

results = await orchestrator.execute_workflow([step1, step2, step3])
print(results)  # ["initialized", "processed", "finalized"]
```

**Output:**
```
Step 1: Initialize
Step 2: Process
Step 3: Finalize
["initialized", "processed", "finalized"]
```

**Error Handling:**

```python
async def failing_step():
    raise RuntimeError("Step failed")

try:
    results = await orchestrator.execute_workflow([step1, failing_step, step3])
except RuntimeError as e:
    print(f"Workflow stopped: {e}")
    # step3 will NOT execute
```

---

### `execute_parallel(operations: list[Callable]) -> list[Any]`

Execute operations in parallel.

**Parameters:**
- `operations` (list[Callable]) — List of async functions to execute concurrently

**Returns:**
- `list[Any]` — Results from each operation (exceptions included)

**Example:**

```python
import asyncio

async def task1():
    await asyncio.sleep(1)
    return "task1 done"

async def task2():
    await asyncio.sleep(1)
    return "task2 done"

async def task3():
    await asyncio.sleep(1)
    return "task3 done"

import time
start = time.time()
results = await orchestrator.execute_parallel([task1, task2, task3])
duration = time.time() - start

print(f"Results: {results}")
print(f"Duration: {duration:.2f}s")  # ~1s (parallel), not ~3s (sequential)
```

**Output:**
```
Results: ["task1 done", "task2 done", "task3 done"]
Duration: 1.02s
```

**Error Handling:**

```python
async def failing_task():
    raise ValueError("Task failed")

results = await orchestrator.execute_parallel([task1, failing_task, task3])

# Check results
for i, result in enumerate(results):
    if isinstance(result, Exception):
        print(f"Task {i} failed: {result}")
    else:
        print(f"Task {i} succeeded: {result}")
```

**Output:**
```
Task 0 succeeded: task1 done
Task 1 failed: Task failed
Task 2 succeeded: task3 done
```

---

## Use Cases

### 1. Health Monitoring

```python
# Register all components
orchestrator.register_component("database", db.health)
orchestrator.register_component("event_store", event_store.health)
orchestrator.register_component("vault", vault.health)

# Check all in parallel
status = await orchestrator.check_all_components()

# Determine overall health
all_healthy = all(
    s.get("status") == "healthy" 
    for s in status.values()
)

if not all_healthy:
    print("⚠️ System degraded")
    for name, health in status.items():
        if health.get("status") != "healthy":
            print(f"  {name}: {health}")
```

---

### 2. Sequential Workflow

```python
# Agent creation workflow
async def create_vault():
    vault = await vault_manager.create("agent-123")
    return vault

async def generate_prompt():
    prompt = await prompt_generator.generate("agent-123")
    return prompt

async def register_agent():
    await registry.register("agent-123")
    return "registered"

# Execute in order
results = await orchestrator.execute_workflow([
    create_vault,
    generate_prompt,
    register_agent
])

print("Agent created successfully")
```

---

### 3. Parallel Data Processing

```python
# Process multiple agents in parallel
async def process_agent(agent_id: str):
    # Heavy processing
    await asyncio.sleep(2)
    return f"{agent_id} processed"

agent_ids = ["agent-1", "agent-2", "agent-3", "agent-4", "agent-5"]

# Create tasks
tasks = [
    lambda aid=aid: process_agent(aid)
    for aid in agent_ids
]

# Execute in parallel
results = await orchestrator.execute_parallel(tasks)

print(f"Processed {len(results)} agents in ~2s")
```

---

### 4. Startup Sequence

```python
# System startup workflow
async def initialize_database():
    await db.connect()
    return "database ready"

async def initialize_event_store():
    await event_store.initialize()
    return "event_store ready"

async def initialize_vault():
    await vault.initialize()
    return "vault ready"

async def start_api():
    await api.start()
    return "api ready"

# Sequential startup
results = await orchestrator.execute_workflow([
    initialize_database,
    initialize_event_store,
    initialize_vault,
    start_api
])

print("System started:", results)
```

---

### 5. Graceful Shutdown

```python
# Shutdown all components in parallel
async def shutdown_api():
    await api.stop()
    return "api stopped"

async def shutdown_database():
    await db.disconnect()
    return "database closed"

async def shutdown_event_store():
    await event_store.close()
    return "event_store closed"

# Parallel shutdown (faster)
results = await orchestrator.execute_parallel([
    shutdown_api,
    shutdown_database,
    shutdown_event_store
])

print("System shutdown complete")
```

---

## Best Practices

### 1. Use Parallel for Independent Tasks

```python
# ✅ Good: Independent tasks in parallel
results = await orchestrator.execute_parallel([
    fetch_user_data,
    fetch_product_data,
    fetch_analytics_data
])

# ❌ Bad: Sequential when parallel is possible
user_data = await fetch_user_data()
product_data = await fetch_product_data()
analytics_data = await fetch_analytics_data()
```

### 2. Use Workflow for Dependencies

```python
# ✅ Good: Sequential when steps depend on each other
results = await orchestrator.execute_workflow([
    create_user,      # Must happen first
    send_welcome,     # Needs user ID
    log_signup        # Needs both
])

# ❌ Bad: Parallel when there are dependencies
results = await orchestrator.execute_parallel([
    create_user,
    send_welcome,     # May fail if user not created yet
    log_signup
])
```

### 3. Handle Errors Gracefully

```python
# Check for errors in parallel execution
results = await orchestrator.execute_parallel(tasks)

successes = [r for r in results if not isinstance(r, Exception)]
failures = [r for r in results if isinstance(r, Exception)]

print(f"✅ {len(successes)} succeeded")
print(f"❌ {len(failures)} failed")

if failures:
    # Retry failed tasks
    retry_tasks = [tasks[i] for i, r in enumerate(results) if isinstance(r, Exception)]
    retry_results = await orchestrator.execute_parallel(retry_tasks)
```

### 4. Monitor Component Health

```python
# Periodic health checks
import asyncio

async def health_monitor():
    while True:
        status = await orchestrator.check_all_components()
        
        unhealthy = [
            name for name, health in status.items()
            if health.get("status") != "healthy"
        ]
        
        if unhealthy:
            print(f"⚠️ Unhealthy components: {unhealthy}")
        
        await asyncio.sleep(60)  # Check every minute

# Run in background
asyncio.create_task(health_monitor())
```

---

## Performance

- **Component checks:** Parallel execution, ~10-50ms total
- **Workflow execution:** Sequential, sum of step times
- **Parallel execution:** Concurrent, max of task times
- **Memory usage:** Minimal (stateless)

---

## Comparison: Sequential vs Parallel

```python
# Sequential (slow)
start = time.time()
result1 = await task1()  # 1s
result2 = await task2()  # 1s
result3 = await task3()  # 1s
duration = time.time() - start
# Duration: ~3s

# Parallel (fast)
start = time.time()
results = await orchestrator.execute_parallel([task1, task2, task3])
duration = time.time() - start
# Duration: ~1s (3x faster!)
```

---

## Error Handling

```python
# Workflow: stops on first error
try:
    results = await orchestrator.execute_workflow([step1, step2, step3])
except Exception as e:
    print(f"Workflow failed at step: {e}")

# Parallel: captures all errors
results = await orchestrator.execute_parallel([task1, task2, task3])
for i, result in enumerate(results):
    if isinstance(result, Exception):
        print(f"Task {i} failed: {result}")
```

---

## See Also

- [Architect API](architect.md) — Autonomous decisions
- [Decision Maker API](decision-maker.md) — Strategy selection
- [Rollback API](rollback.md) — Recovery system
