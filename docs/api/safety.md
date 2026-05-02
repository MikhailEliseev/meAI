# Safety Components API Reference

> Loop detection, timeouts, context monitoring, health checks, metrics

## Loop Detector

Prevents infinite delegation chains.

```python
from meai.safety.loop_detector import LoopDetector

detector = LoopDetector(max_depth=5)

# Track delegation
detector.track_delegation("operator", "seo-agent")
detector.track_delegation("seo-agent", "content-agent")

# Check for loops
if detector.detect_loop("content-agent", "operator"):
    print("⚠️ Loop detected!")

# Check depth
if detector.is_max_depth_exceeded("content-agent"):
    print("⚠️ Max depth exceeded!")

# Get chain
chain = detector.get_chain("content-agent")
print(f"Chain: {' -> '.join(chain)}")

# Reset
detector.reset_agent("seo-agent")
```

**Features:**
- Max depth: 5 levels (configurable)
- Circular delegation detection
- Self-call detection
- Chain tracking

---

## Timeout Manager

Manages operation timeouts.

```python
from meai.safety.timeout_manager import TimeoutManager

manager = TimeoutManager(default_timeout=300)  # 5 minutes

# Run with timeout
async with manager.timeout(operation_id="task-123"):
    result = await long_running_task()

# Custom timeout
async with manager.timeout(operation_id="quick-task", timeout=30):
    result = await quick_task()

# Cancel operation
await manager.cancel_operation("task-123")

# Get active operations
active = manager.get_active_operations()
print(f"Active: {len(active)}")
```

**Features:**
- Default timeout: 5 minutes
- Custom timeouts per operation
- Graceful cancellation
- Active operation tracking

---

## Context Monitor

Enforces 40% rule for context usage.

```python
from meai.safety.context_monitor import ContextMonitor

monitor = ContextMonitor(
    max_tokens=200000,
    warning_threshold=0.4,
    critical_threshold=0.8
)

# Track usage
monitor.add_tokens(50000)

# Check status
if monitor.should_compact():
    print("⚠️ Should compact context")

# Get status
status = monitor.get_status()
print(f"Usage: {status['usage_percent']:.1%}")
print(f"Remaining: {status['remaining_tokens']}")

# Reset
monitor.reset()
```

**Features:**
- 40% warning threshold
- 80% critical threshold
- Auto-compact recommendations
- Token tracking

---

## Health Checker

Monitors component health.

```python
from meai.monitoring.health import HealthChecker

checker = HealthChecker()

# Register components
checker.register_component("database", db.health)
checker.register_component("vault", vault.health)

# Check all
status = await checker.check_all()
print(f"Overall: {status['status']}")

# Check specific
db_status = await checker.check_component("database")
print(f"Database: {db_status['status']}")

# Get uptime
uptime = checker.get_uptime()
print(f"Uptime: {uptime}")
```

**Features:**
- Component registration
- Parallel health checks
- Uptime tracking
- Overall status aggregation

---

## Metrics Collector

Collects performance metrics.

```python
from meai.monitoring.metrics import MetricsCollector

metrics = MetricsCollector(db)

# Record counter
await metrics.record_metric(
    name="tasks_completed",
    value=1,
    metric_type="counter"
)

# Record gauge
await metrics.record_metric(
    name="active_agents",
    value=5,
    metric_type="gauge"
)

# Record histogram
await metrics.record_metric(
    name="task_duration_ms",
    value=1234,
    metric_type="histogram"
)

# Get summary
summary = await metrics.get_metric_summary(
    name="tasks_completed",
    hours=24
)
print(f"Total: {summary['total']}")
print(f"Average: {summary['average']}")

# Cleanup old metrics
await metrics.cleanup_old_metrics(days=30)
```

**Metric Types:**
- **Counter:** Incrementing values (tasks completed, errors)
- **Gauge:** Current values (active agents, memory usage)
- **Histogram:** Distributions (durations, sizes)

**Features:**
- Time-series storage
- Aggregation (sum, avg, min, max)
- Automatic cleanup
- Label support

---

## Usage Example

```python
# Initialize all safety components
loop_detector = LoopDetector(max_depth=5)
timeout_manager = TimeoutManager(default_timeout=300)
context_monitor = ContextMonitor(max_tokens=200000)
health_checker = HealthChecker()
metrics = MetricsCollector(db)

# Register health checks
health_checker.register_component("database", db.health)
health_checker.register_component("vault", vault.health)

# Execute task with safety
async def execute_task(task_id: str):
    # Check loop
    if loop_detector.is_max_depth_exceeded("agent"):
        raise RuntimeError("Max depth exceeded")
    
    # Check context
    if context_monitor.should_compact():
        await compact_context()
    
    # Execute with timeout
    async with timeout_manager.timeout(operation_id=task_id):
        result = await process_task(task_id)
    
    # Record metrics
    await metrics.record_metric(
        name="tasks_completed",
        value=1,
        metric_type="counter"
    )
    
    return result
```

---

## Best Practices

### Loop Detection
- Track all delegations
- Reset chains after completion
- Set appropriate max depth (5 is good default)

### Timeouts
- Use default timeout for most operations
- Set shorter timeouts for quick tasks
- Handle TimeoutError gracefully

### Context Monitoring
- Check before large operations
- Compact at 40% threshold
- Reset after compaction

### Health Checks
- Register all critical components
- Check health periodically (every minute)
- Alert on unhealthy status

### Metrics
- Record all important events
- Use appropriate metric types
- Clean up old metrics regularly
- Add labels for filtering

---

## See Also

- [Orchestrator API](orchestrator.md) — Workflow coordination
- [Architecture: Safety](../architecture/safety.md)
