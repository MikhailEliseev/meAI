# Experience Learning System

## Overview

Experience Learning — это система обучения на опыте, которая автоматически улучшает качество знаний на основе реальных результатов выполнения задач.

**Компоненты:**

1. **ExperienceTracker** - Записывает результаты задач
2. **QualityUpdater** - Обновляет качество знаний
3. **DeprecationManager** - Удаляет устаревшие знания
4. **LearningAnalytics** - Аналитика и insights

## Architecture

```
Task Execution
    ↓
ExperienceTracker.record_experience()
    ↓
Knowledge Stats Updated
    ↓
QualityUpdater.calculate_new_quality_score()
    ↓
Teacher's Qdrant Metadata Updated
    ↓
DeprecationManager.should_deprecate()
    ↓
Low Performers Deprecated
    ↓
LearningAnalytics.get_insights()
```

## ExperienceTracker

### Purpose

Записывает результаты выполнения задач и отслеживает использование знаний.

### Initialization

```python
from meai.learning import ExperienceTracker

tracker = ExperienceTracker(
    database_url="sqlite+aiosqlite:///./data/meai.db"
)

await tracker.initialize()
```

### Recording Experiences

```python
# Record successful task
experience_id = await tracker.record_experience(
    magister_id="seo-magister-1",
    task_id="task-123",
    knowledge_ids=["knowledge-1", "knowledge-2"],
    outcome="success",
    outcome_score=0.9,
    feedback="Task completed successfully with high quality",
)

# Record failed task
experience_id = await tracker.record_experience(
    magister_id="seo-magister-1",
    task_id="task-124",
    knowledge_ids=["knowledge-3"],
    outcome="failure",
    outcome_score=0.2,
    feedback="Knowledge was outdated",
)
```

### Querying Statistics

```python
# Get knowledge stats
stats = await tracker.get_knowledge_stats("knowledge-1")

print(f"Total uses: {stats['total_uses']}")
print(f"Success rate: {stats['success_rate']:.1%}")
print(f"Average score: {stats['average_score']:.2f}")
print(f"Last used: {stats['last_used_at']}")

# Get Magister experiences
experiences = await tracker.get_magister_experiences(
    magister_id="seo-magister-1",
    limit=50
)

# Get recent experiences
recent = await tracker.get_recent_experiences(limit=100)
```

### Database Schema

**experiences table:**
```sql
CREATE TABLE experiences (
    id TEXT PRIMARY KEY,
    magister_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    knowledge_ids TEXT NOT NULL,  -- JSON array
    outcome TEXT NOT NULL,         -- success/failure/partial
    outcome_score REAL,            -- 0.0 - 1.0
    feedback TEXT,
    created_at TIMESTAMP NOT NULL
)
```

**knowledge_stats table (denormalized):**
```sql
CREATE TABLE knowledge_stats (
    knowledge_id TEXT PRIMARY KEY,
    total_uses INTEGER DEFAULT 0,
    successful_uses INTEGER DEFAULT 0,
    failed_uses INTEGER DEFAULT 0,
    total_score REAL DEFAULT 0.0,
    last_used_at TIMESTAMP,
    updated_at TIMESTAMP NOT NULL
)
```

## QualityUpdater

### Purpose

Автоматически обновляет качество знаний на основе реального опыта использования.

### Algorithm

**Weighted formula:**
```python
target_from_success = 1.0 + (success_rate * 9.0)
target_from_score = 1.0 + (average_score * 9.0)
target_score = (target_from_success * 0.6) + (target_from_score * 0.4)
adjustment = (target_score - current_score) * learning_rate
new_score = clamp(current_score + adjustment, 1.0, 10.0)
```

**Weights:**
- Success rate: 60% (более важен)
- Average score: 40%

### Initialization

```python
from meai.learning import QualityUpdater

updater = QualityUpdater(
    experience_tracker=tracker,
    database_url="sqlite+aiosqlite:///./data/meai.db",
    learning_rate=0.3,           # How quickly to adjust (0.0-1.0)
    min_usage_for_update=5,      # Minimum data needed
)

await updater.initialize()
```

### Updating Quality

```python
# Single update
result = await updater.update_knowledge_quality(
    knowledge_id="knowledge-1",
    current_score=7.0,
)

print(f"Old score: {result['old_score']}")
print(f"New score: {result['new_score']}")
print(f"Adjustment: {result['adjustment']}")
print(f"Reason: {result['reason']}")

# Batch update
items = [
    {"id": "knowledge-1", "current_score": 7.0},
    {"id": "knowledge-2", "current_score": 6.5},
    {"id": "knowledge-3", "current_score": 8.0},
]

results = await updater.batch_update_qualities(items)
```

### Getting Recommendations

```python
# Get update recommendations
recommendations = await updater.get_quality_update_recommendations(
    min_usage_count=10,
    min_adjustment_threshold=0.5,
)

for rec in recommendations:
    print(f"Knowledge: {rec['knowledge_id']}")
    print(f"  Current: {rec['current_score']:.1f}")
    print(f"  Recommended: {rec['recommended_score']:.1f}")
    print(f"  Adjustment: {rec['adjustment']:+.1f}")
    print(f"  Priority: {rec['priority']}")
```

### Quality Update History

```python
# Get history for specific knowledge
history = await updater.get_quality_update_history(
    knowledge_id="knowledge-1",
    limit=10
)

# Get all recent updates
all_history = await updater.get_quality_update_history(limit=100)
```

### Configuration

```python
# Adjust learning rate
updater.learning_rate = 0.5  # Faster adjustment

# Adjust minimum usage
updater.min_usage_for_update = 10  # More data required
```

## DeprecationManager

### Purpose

Автоматически помечает устаревшие или низкокачественные знания для удаления.

### Deprecation Criteria

1. **Low quality score** - Quality < 3.0 after 20+ uses
2. **Low success rate** - Success rate < 30% with sufficient data
3. **Poor outcomes** - Average score < 0.4 consistently

### Initialization

```python
from meai.learning import DeprecationManager

deprecation = DeprecationManager(
    experience_tracker=tracker,
    database_url="sqlite+aiosqlite:///./data/meai.db",
    quality_threshold=3.0,
    success_rate_threshold=0.3,
    min_usage_for_deprecation=20,
)

await deprecation.initialize()
```

### Checking Deprecation

```python
# Check if should deprecate
should_deprecate, reason = await deprecation.should_deprecate(
    knowledge_id="knowledge-1",
    current_quality=2.5,
)

if should_deprecate:
    print(f"Should deprecate: {reason}")
```

### Deprecating Knowledge

```python
# Manual deprecation
result = await deprecation.deprecate_knowledge(
    knowledge_id="knowledge-1",
    reason="Low quality score after 25 uses",
    current_quality=2.5,
    deprecated_by="admin",
)

print(f"Deprecated: {result['deprecated']}")
print(f"Deprecation ID: {result['deprecation_id']}")
```

### Scanning for Candidates

```python
# Scan for deprecation candidates
candidates = await deprecation.scan_for_deprecation_candidates(
    min_usage_count=20
)

for candidate in candidates:
    print(f"Knowledge: {candidate['knowledge_id']}")
    print(f"  Quality: {candidate['estimated_quality']:.1f}")
    print(f"  Success rate: {candidate['success_rate']:.1%}")
    print(f"  Reason: {candidate['reason']}")
    print(f"  Priority: {candidate['priority']}")
```

### Auto-Deprecation

```python
# Dry run (preview only)
results = await deprecation.auto_deprecate_low_performers(
    min_usage_count=20,
    dry_run=True,
)

print(f"Would deprecate {len(results)} items")

# Real deprecation
results = await deprecation.auto_deprecate_low_performers(
    min_usage_count=20,
    dry_run=False,
)

print(f"Deprecated {len(results)} items")
```

### Undeprecation

```python
# Restore deprecated knowledge
result = await deprecation.undeprecate_knowledge(
    knowledge_id="knowledge-1",
    reason="Quality improved after update",
)

print(f"Undeprecated: {result['undeprecated']}")
```

### Getting Deprecated Knowledge

```python
# Get active deprecations
deprecated = await deprecation.get_deprecated_knowledge(active_only=True)

# Get all deprecations (including undeprecated)
all_deprecated = await deprecation.get_deprecated_knowledge(active_only=False)
```

## LearningAnalytics

### Purpose

Предоставляет аналитику и insights по системе обучения.

### Initialization

```python
from meai.learning import LearningAnalytics

analytics = LearningAnalytics(
    experience_tracker=tracker,
    quality_updater=updater,
    deprecation_manager=deprecation,
)
```

### System Health

```python
# Get overall system health
health = await analytics.get_system_health()

print(f"Health Score: {health['health_score']}/10")
print(f"Success Rate: {health['overall_success_rate']:.1%}")
print(f"Avg Score: {health['average_outcome_score']:.2f}")
print(f"Deprecated: {health['active_deprecated']}")
```

**Health Score Calculation:**
```python
success_points = success_rate * 4.0      # 0-4 points
score_points = avg_score * 4.0           # 0-4 points
deprecation_points = 2.0 if dep_rate < 0.2 else
                     1.0 if dep_rate < 0.5 else 0.0
health_score = success_points + score_points + deprecation_points  # 0-10
```

### Knowledge Performance Report

```python
# Detailed knowledge report
report = await analytics.get_knowledge_performance_report("knowledge-1")

print(f"Performance Grade: {report['performance_grade']}")
print(f"Usage Stats: {report['usage_stats']}")
print(f"Quality History: {len(report['quality_history'])} updates")
print(f"Deprecation: {report['deprecation_info']}")
print(f"Recommendations:")
for rec in report['recommendations']:
    print(f"  - {rec}")
```

**Performance Grades:**
- A: 90%+ combined score
- B: 80-89%
- C: 70-79%
- D: 60-69%
- F: <60%

### Magister Performance Report

```python
# Magister performance
report = await analytics.get_magister_performance_report("seo-magister-1")

print(f"Grade: {report['performance_grade']}")
print(f"Total Tasks: {report['total_tasks']}")
print(f"Success Rate: {report['success_rate']:.1%}")
print(f"Avg Score: {report['average_score']:.2f}")
```

### Learning Trends

```python
# Get trends over last 7 days
trends = await analytics.get_learning_trends(days=7)

print(f"Trend: {trends['trend']}")  # improving/declining/stable
print(f"Total Experiences: {trends['total_experiences']}")
print(f"Overall Success Rate: {trends['overall_success_rate']:.1%}")

# Daily metrics
for day in trends['daily_metrics']:
    print(f"{day['date']}: {day['success_rate']:.1%} ({day['total_tasks']} tasks)")
```

### Top Performers

```python
# Get top performing knowledge
top = await analytics.get_top_performing_knowledge(
    limit=10,
    min_usage=10
)

for i, performer in enumerate(top, 1):
    print(f"#{i}: {performer['knowledge_id']}")
    print(f"  Performance: {performer['performance_score']:.2f}")
    print(f"  Success Rate: {performer['success_rate']:.1%}")
    print(f"  Usage: {performer['usage_count']}")
```

## Complete Workflow Example

```python
from meai.learning import (
    ExperienceTracker,
    QualityUpdater,
    DeprecationManager,
    LearningAnalytics,
)

# Initialize components
tracker = ExperienceTracker()
await tracker.initialize()

updater = QualityUpdater(experience_tracker=tracker)
await updater.initialize()

deprecation = DeprecationManager(experience_tracker=tracker)
await deprecation.initialize()

analytics = LearningAnalytics(
    experience_tracker=tracker,
    quality_updater=updater,
    deprecation_manager=deprecation,
)

# 1. Record experiences
for i in range(20):
    await tracker.record_experience(
        magister_id="seo-magister-1",
        task_id=f"task-{i}",
        knowledge_ids=["knowledge-1"],
        outcome="success" if i < 16 else "failure",
        outcome_score=0.9 if i < 16 else 0.2,
    )

# 2. Update quality
result = await updater.update_knowledge_quality(
    knowledge_id="knowledge-1",
    current_score=7.0,
)
print(f"Quality: {result['old_score']} → {result['new_score']}")

# 3. Check deprecation
should_dep, reason = await deprecation.should_deprecate(
    knowledge_id="knowledge-1",
    current_quality=result['new_score'],
)
print(f"Should deprecate: {should_dep} ({reason})")

# 4. Get analytics
health = await analytics.get_system_health()
print(f"System Health: {health['health_score']}/10")

report = await analytics.get_knowledge_performance_report("knowledge-1")
print(f"Performance Grade: {report['performance_grade']}")
```

## Performance

| Operation | Latency | Notes |
|-----------|---------|-------|
| Record experience | 5-10ms | SQLite insert + stats update |
| Get stats | 1-5ms | Single query |
| Update quality | 10-20ms | Calculate + log |
| Scan candidates | 100-200ms | For 100 items |
| System health | 50-100ms | Aggregation queries |

## Best Practices

1. **Record all experiences** - Even failures provide valuable data
2. **Update quality periodically** - Run batch updates daily/weekly
3. **Monitor deprecation candidates** - Review before auto-deprecating
4. **Use analytics** - Track trends and system health
5. **Set appropriate thresholds** - Adjust based on your use case

## Configuration Examples

### Conservative (slow learning)

```python
updater = QualityUpdater(
    experience_tracker=tracker,
    learning_rate=0.1,           # Slow adjustment
    min_usage_for_update=20,     # More data required
)

deprecation = DeprecationManager(
    experience_tracker=tracker,
    quality_threshold=2.0,       # Lower threshold
    success_rate_threshold=0.2,  # Lower threshold
    min_usage_for_deprecation=50, # Much more data
)
```

### Aggressive (fast learning)

```python
updater = QualityUpdater(
    experience_tracker=tracker,
    learning_rate=0.5,           # Fast adjustment
    min_usage_for_update=3,      # Less data required
)

deprecation = DeprecationManager(
    experience_tracker=tracker,
    quality_threshold=4.0,       # Higher threshold
    success_rate_threshold=0.4,  # Higher threshold
    min_usage_for_deprecation=10, # Less data
)
```

## Troubleshooting

### Quality not updating

```python
# Check if enough data
stats = await tracker.get_knowledge_stats("knowledge-1")
if stats['total_uses'] < updater.min_usage_for_update:
    print(f"Need {updater.min_usage_for_update - stats['total_uses']} more uses")
```

### Unexpected deprecation

```python
# Check deprecation criteria
stats = await tracker.get_knowledge_stats("knowledge-1")
print(f"Quality: {current_quality}")
print(f"Success rate: {stats['success_rate']:.1%}")
print(f"Avg score: {stats['average_score']:.2f}")
print(f"Usage: {stats['total_uses']}")

# Check thresholds
print(f"Quality threshold: {deprecation.quality_threshold}")
print(f"Success rate threshold: {deprecation.success_rate_threshold}")
```

## See Also

- [Magisters](magisters.md) - Domain specialists
- [Teacher Agent](teacher.md) - Knowledge management
- [API Reference](api-reference.md) - Complete API docs
