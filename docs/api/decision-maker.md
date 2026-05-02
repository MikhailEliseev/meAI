# Decision Maker API Reference

> Strategy selection and learning from outcomes

## Overview

**Decision Maker** — компонент для выбора оптимальных стратегий с обучением на основе исторических данных. Оценивает стратегии, отслеживает результаты и улучшает выбор со временем.

## Class: `DecisionMaker`

### Constructor

```python
from meai.core.decision_maker import DecisionMaker
from meai.storage.database import Database

db = Database("sqlite+aiosqlite:///./data/meai.db")
await db.connect()

decision_maker = DecisionMaker(db)
```

**Parameters:**
- `db` (Database) — Database instance for storing strategy outcomes

---

## Methods

### `select_strategy(strategies: list[Strategy], criteria: dict) -> Strategy`

Select optimal strategy based on criteria and historical data.

**Parameters:**
- `strategies` (list[Strategy]) — Available strategies to choose from
- `criteria` (dict) — Selection criteria (max_cost, min_quality, etc.)

**Returns:**
- `Strategy` — Selected optimal strategy

**Example:**

```python
from meai.core.decision_maker import Strategy

strategies = [
    Strategy(
        name="Fast Approach",
        description="Quick execution with higher risk",
        expected_cost=50,
        expected_quality=7,
        risk_level="high"
    ),
    Strategy(
        name="Balanced Approach",
        description="Balanced cost and quality",
        expected_cost=75,
        expected_quality=8,
        risk_level="medium"
    ),
    Strategy(
        name="Premium Approach",
        description="High quality, higher cost",
        expected_cost=100,
        expected_quality=9,
        risk_level="low"
    )
]

selected = await decision_maker.select_strategy(
    strategies,
    criteria={"max_cost": 80, "min_quality": 7}
)

print(f"Selected: {selected.name}")
print(f"Cost: {selected.expected_cost}")
print(f"Quality: {selected.expected_quality}")
```

**Output:**
```
Selected: Balanced Approach
Cost: 75
Quality: 8
```

---

### `track_outcome(strategy: Strategy, outcome: StrategyOutcome) -> None`

Track strategy execution outcome for learning.

**Parameters:**
- `strategy` (Strategy) — Strategy that was executed
- `outcome` (StrategyOutcome) — Execution outcome

**Returns:**
- None

**Example:**

```python
from meai.core.decision_maker import StrategyOutcome

# Execute strategy
selected = await decision_maker.select_strategy(strategies, criteria)

# ... execute the strategy ...

# Track outcome
outcome = StrategyOutcome(
    strategy_name=selected.name,
    actual_cost=78,        # Slightly over estimate
    actual_quality=8.5,    # Better than expected
    success=True,
    notes="Completed on time, exceeded quality expectations"
)

await decision_maker.track_outcome(selected, outcome)
```

---

### `get_strategy_history(strategy_name: str) -> list[StrategyRecord]`

Get execution history for a strategy.

**Parameters:**
- `strategy_name` (str) — Name of the strategy

**Returns:**
- `list[StrategyRecord]` — List of past executions

**Example:**

```python
history = await decision_maker.get_strategy_history("Balanced Approach")

for record in history:
    print(f"{record.timestamp}: Cost={record.actual_cost}, Quality={record.actual_quality}")
```

---

### `get_strategy_insights(strategy_name: str) -> dict`

Get insights from strategy execution history.

**Parameters:**
- `strategy_name` (str) — Name of the strategy

**Returns:**
- `dict` — Insights with success rate, avg cost, avg quality

**Example:**

```python
insights = await decision_maker.get_strategy_insights("Balanced Approach")

print(f"Total executions: {insights['total_executions']}")
print(f"Success rate: {insights['success_rate']:.1%}")
print(f"Average cost: ${insights['avg_cost']:.2f}")
print(f"Average quality: {insights['avg_quality']:.1f}/10")
```

**Output:**
```
Total executions: 15
Success rate: 86.7%
Average cost: $76.50
Average quality: 8.2/10
```

---

### `compare_strategies(strategies: list[Strategy]) -> list[dict]`

Compare strategies with historical data.

**Parameters:**
- `strategies` (list[Strategy]) — Strategies to compare

**Returns:**
- `list[dict]` — Comparison results sorted by score

**Example:**

```python
comparison = await decision_maker.compare_strategies(strategies)

for result in comparison:
    print(f"{result['strategy']}: Score={result['score']:.1f}")
    print(f"  Expected: ${result['expected_cost']}, Quality={result['expected_quality']}")
    print(f"  Historical: {result['historical_executions']} runs, {result['historical_success_rate']:.1%} success")
```

**Output:**
```
Balanced Approach: Score=105.3
  Expected: $75, Quality=8
  Historical: 15 runs, 86.7% success

Premium Approach: Score=95.0
  Expected: $100, Quality=9
  Historical: 8 runs, 100.0% success

Fast Approach: Score=70.5
  Expected: $50, Quality=7
  Historical: 12 runs, 66.7% success
```

---

### `score_strategy(strategy: Strategy, criteria: dict) -> float`

Score a single strategy.

**Parameters:**
- `strategy` (Strategy) — Strategy to score
- `criteria` (dict) — Scoring criteria

**Returns:**
- `float` — Strategy score

**Example:**

```python
strategy = Strategy(
    name="Test Strategy",
    description="Test",
    expected_cost=60,
    expected_quality=8,
    risk_level="medium"
)

score = decision_maker.score_strategy(
    strategy,
    criteria={"max_cost": 100, "min_quality": 7}
)

print(f"Score: {score}")  # 100.0
```

---

## Data Classes

### `Strategy`

Strategy definition.

**Fields:**
- `name` (str) — Strategy name
- `description` (str) — Strategy description
- `expected_cost` (float) — Expected cost
- `expected_quality` (float) — Expected quality (0-10)
- `risk_level` (str) — Risk level: "low", "medium", "high"

**Example:**

```python
from meai.core.decision_maker import Strategy

strategy = Strategy(
    name="Agile Sprint",
    description="2-week sprint with daily standups",
    expected_cost=5000,
    expected_quality=8.5,
    risk_level="medium"
)
```

---

### `StrategyOutcome`

Strategy execution outcome.

**Fields:**
- `strategy_name` (str) — Name of executed strategy
- `actual_cost` (float) — Actual cost incurred
- `actual_quality` (float) — Actual quality achieved
- `success` (bool) — Whether execution was successful
- `notes` (str) — Additional notes

**Example:**

```python
from meai.core.decision_maker import StrategyOutcome

outcome = StrategyOutcome(
    strategy_name="Agile Sprint",
    actual_cost=5200,      # 4% over budget
    actual_quality=9.0,    # Better than expected
    success=True,
    notes="Sprint completed successfully, delivered all features"
)
```

---

## Scoring Algorithm

Strategies are scored based on:

1. **Quality Score** (quality × 10)
2. **Cost Efficiency**
   - +20 if within max_cost
   - Bonus: (savings / max_cost) × 10
3. **Quality Requirement** (+15 if ≥ min_quality)
4. **Risk Penalty**
   - Low: 0
   - Medium: -5
   - High: -15
5. **Historical Bonus** (success_rate × 20)

**Example:**

```python
# Strategy: Balanced Approach
# Expected: cost=75, quality=8, risk=medium
# Criteria: max_cost=100, min_quality=7
# Historical: 15 runs, 86.7% success

score = (
    8 * 10          # Quality: 80
    + 20            # Within budget: +20
    + (25/100)*10   # Savings bonus: +2.5
    + 15            # Meets quality: +15
    - 5             # Medium risk: -5
    + 0.867 * 20    # Historical: +17.3
)
# Total: 129.8
```

---

## Learning System

Decision Maker learns from outcomes:

1. **Track every execution** with actual cost/quality
2. **Calculate success rate** per strategy
3. **Adjust scores** based on historical performance
4. **Prefer proven strategies** over untested ones

**Example Learning:**

```python
# Initial selection (no history)
selected = await decision_maker.select_strategy(strategies, criteria)
# → Selects based on expected values only

# After 10 executions with 90% success
selected = await decision_maker.select_strategy(strategies, criteria)
# → Gets +18 bonus points from historical success
# → More likely to be selected again
```

---

## Database Schema

Strategy outcomes are stored in `strategy_outcomes` table:

```sql
CREATE TABLE strategy_outcomes (
    id INTEGER PRIMARY KEY,
    strategy_name TEXT NOT NULL,
    expected_cost REAL NOT NULL,
    expected_quality REAL NOT NULL,
    actual_cost REAL NOT NULL,
    actual_quality REAL NOT NULL,
    success BOOLEAN NOT NULL,
    notes TEXT NOT NULL,
    timestamp DATETIME NOT NULL
);

CREATE INDEX idx_strategy_outcomes_name ON strategy_outcomes(strategy_name);
CREATE INDEX idx_strategy_outcomes_timestamp ON strategy_outcomes(timestamp);
```

---

## Best Practices

### 1. Always Track Outcomes

```python
# ✅ Good: Track every execution
selected = await decision_maker.select_strategy(strategies, criteria)

# Execute strategy
result = await execute_strategy(selected)

# Track outcome
outcome = StrategyOutcome(
    strategy_name=selected.name,
    actual_cost=result.cost,
    actual_quality=result.quality,
    success=result.success,
    notes=result.notes
)
await decision_maker.track_outcome(selected, outcome)
```

### 2. Use Realistic Estimates

```python
# ❌ Bad: Unrealistic estimates
Strategy(
    name="Magic Solution",
    expected_cost=1,      # Too optimistic
    expected_quality=10,  # Perfect quality unlikely
    risk_level="low"      # Underestimating risk
)

# ✅ Good: Realistic estimates
Strategy(
    name="Proven Approach",
    expected_cost=5000,   # Based on past data
    expected_quality=8,   # Achievable target
    risk_level="medium"   # Honest risk assessment
)
```

### 3. Review Insights Regularly

```python
# Check strategy performance monthly
for strategy_name in ["Fast", "Balanced", "Premium"]:
    insights = await decision_maker.get_strategy_insights(strategy_name)
    
    if insights['success_rate'] < 0.7:
        print(f"⚠️ {strategy_name} has low success rate: {insights['success_rate']:.1%}")
    
    if insights['avg_cost'] > insights['expected_cost'] * 1.2:
        print(f"⚠️ {strategy_name} consistently over budget")
```

### 4. Compare Before Deciding

```python
# Compare strategies with historical data
comparison = await decision_maker.compare_strategies(strategies)

# Show top 3
for result in comparison[:3]:
    print(f"{result['strategy']}: Score={result['score']:.1f}")
    print(f"  Success rate: {result['historical_success_rate']:.1%}")
```

---

## Error Handling

```python
try:
    selected = await decision_maker.select_strategy(strategies, criteria)
except ValueError as e:
    print(f"Invalid strategy or criteria: {e}")
except RuntimeError as e:
    print(f"Selection failed: {e}")
```

---

## Performance

- **Selection time:** ~5-20ms
- **Database reads:** 1 per strategy (for insights)
- **Database writes:** 1 per outcome tracked
- **Memory usage:** Minimal (stateless)

---

## See Also

- [Architect API](architect.md) — Autonomous decisions
- [Orchestrator API](orchestrator.md) — Async coordination
- [Event Store API](event-store.md) — Audit trail
