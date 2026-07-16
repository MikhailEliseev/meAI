# Architect API Reference

> Autonomous decision making with context analysis

## Overview

**Architect** — компонент для автономного принятия решений. Анализирует контекст, генерирует варианты, оценивает их и выбирает оптимальное решение.

## Class: `Architect`

### Constructor

```python
from meai.core.architect import Architect
from meai.storage.database import Database

db = Database("sqlite+aiosqlite:///./data/meai.db")
await db.connect()

architect = Architect(db)
```

**Parameters:**
- `db` (Database) — Database instance for storing decisions

---

## Methods

### `make_decision(context: DecisionContext) -> Decision`

Make autonomous decision based on context.

**Parameters:**
- `context` (DecisionContext) — Decision context with goal, constraints, and resources

**Returns:**
- `Decision` — Decision with action, rationale, confidence, and alternatives

**Example:**

```python
from meai.core.architect import DecisionContext

context = DecisionContext(
    goal="Optimize SEO strategy",
    constraints=["budget < 1000", "timeline < 2 weeks"],
    available_resources={"team": 3, "tools": ["ahrefs", "semrush"]}
)

decision = await architect.make_decision(context)

print(f"Action: {decision.action}")
print(f"Rationale: {decision.rationale}")
print(f"Confidence: {decision.confidence:.2f}")
print(f"Alternatives: {decision.alternatives}")
```

**Output:**
```
Action: execute_optimize_seo_strategy
Rationale: Direct execution of goal
Confidence: 0.80
Alternatives: ['cautious_optimize_seo_strategy', 'minimal_optimize_seo_strategy']
```

---

### `analyze_context(context: DecisionContext) -> dict`

Analyze decision context.

**Parameters:**
- `context` (DecisionContext) — Context to analyze

**Returns:**
- `dict` — Analysis with feasibility, risks, and recommendations

**Example:**

```python
analysis = await architect.analyze_context(context)

print(f"Feasibility: {analysis['feasibility']}")
print(f"Risks: {analysis['risks']}")
print(f"Recommendations: {analysis['recommendations']}")
```

**Output:**
```
Feasibility: high
Risks: ['budget_constraint']
Recommendations: ['Mitigate 1 identified risks']
```

---

### `evaluate_options(options: list[dict], context: DecisionContext) -> dict`

Evaluate and select best option.

**Parameters:**
- `options` (list[dict]) — List of options to evaluate
- `context` (DecisionContext) — Decision context

**Returns:**
- `dict` — Best option with action and rationale

**Example:**

```python
options = [
    {
        "action": "fast_approach",
        "rationale": "Quick execution",
        "cost": 30,
        "quality": 6
    },
    {
        "action": "quality_approach",
        "rationale": "High quality",
        "cost": 100,
        "quality": 10
    }
]

best = await architect.evaluate_options(options, context)
print(f"Best option: {best['action']}")
```

---

### `get_decision_history(limit: int = 10) -> list[Decision]`

Get decision history.

**Parameters:**
- `limit` (int) — Maximum number of decisions to return (default: 10)

**Returns:**
- `list[Decision]` — List of past decisions

**Example:**

```python
history = await architect.get_decision_history(limit=5)

for decision in history:
    print(f"{decision.timestamp}: {decision.action} (confidence: {decision.confidence:.2f})")
```

---

## Data Classes

### `DecisionContext`

Context for decision making.

**Fields:**
- `goal` (str) — Goal to achieve
- `constraints` (list[str]) — List of constraints
- `available_resources` (dict[str, Any]) — Available resources

**Example:**

```python
from meai.core.architect import DecisionContext

context = DecisionContext(
    goal="Launch new marketing campaign",
    constraints=[
        "budget < 5000",
        "timeline < 1 month",
        "team_size = 2"
    ],
    available_resources={
        "budget": 4500,
        "team": ["marketer", "designer"],
        "tools": ["mailchimp", "canva"]
    }
)
```

---

### `Decision`

Decision result.

**Fields:**
- `action` (str) — Action to take
- `rationale` (str) — Reasoning behind the decision
- `confidence` (float) — Confidence level (0.0 - 1.0)
- `alternatives` (list[str]) — Alternative actions considered
- `timestamp` (datetime) — When decision was made

**Example:**

```python
decision = await architect.make_decision(context)

# Access fields
print(decision.action)           # "execute_launch_campaign"
print(decision.rationale)        # "Direct execution of goal"
print(decision.confidence)       # 0.85
print(decision.alternatives)     # ["cautious_launch_campaign", ...]
print(decision.timestamp)        # 2026-05-02 10:30:00
```

---

## Decision Scoring

Architect scores options based on:

1. **Quality Score** (quality × 10)
2. **Cost Efficiency** (+20 if within budget, bonus for savings)
3. **Quality Requirement** (+15 if meets minimum quality)
4. **Risk Penalty** (low: 0, medium: -5, high: -15)

**Example Scoring:**

```python
# Option A: Fast but risky
{
    "quality": 6,      # 60 points
    "cost": 30,        # +20 (under budget) + 10 (savings bonus)
    "risk": "high"     # -15 penalty
}
# Total: 75 points

# Option B: Balanced
{
    "quality": 8,      # 80 points
    "cost": 75,        # +20 (under budget) + 5 (savings bonus)
    "risk": "medium"   # -5 penalty
}
# Total: 100 points ← Winner
```

---

## Confidence Calculation

Confidence is calculated based on:

- **Base confidence:** 0.5
- **Feasibility:** +0.3 (high), +0.1 (medium), 0 (low)
- **Risks:** -0.1 per identified risk
- **Quality:** +0.2 if quality ≥ 8

**Example:**

```python
# High feasibility, 1 risk, quality 9
confidence = 0.5 + 0.3 - 0.1 + 0.2 = 0.9

# Medium feasibility, 3 risks, quality 6
confidence = 0.5 + 0.1 - 0.3 + 0.0 = 0.3
```

---

## Database Schema

Decisions are stored in `decisions` table:

```sql
CREATE TABLE decisions (
    id INTEGER PRIMARY KEY,
    goal TEXT NOT NULL,
    action TEXT NOT NULL,
    rationale TEXT NOT NULL,
    confidence REAL NOT NULL,
    context JSON NOT NULL,
    timestamp DATETIME NOT NULL
);

CREATE INDEX idx_decisions_timestamp ON decisions(timestamp);
```

---

## Best Practices

### 1. Provide Clear Goals

```python
# ❌ Bad
context = DecisionContext(
    goal="do something",
    constraints=[],
    available_resources={}
)

# ✅ Good
context = DecisionContext(
    goal="Increase organic traffic by 30% in Q2",
    constraints=["budget < 2000", "no paid ads"],
    available_resources={"team": 2, "tools": ["ahrefs"]}
)
```

### 2. Include Relevant Constraints

```python
# ✅ Good constraints
constraints = [
    "budget < 5000",           # Numeric constraint
    "timeline < 2 weeks",      # Time constraint
    "team_size = 3",           # Resource constraint
    "no external vendors"      # Policy constraint
]
```

### 3. Track Decision History

```python
# Make decision
decision = await architect.make_decision(context)

# Later: review past decisions
history = await architect.get_decision_history(limit=10)

for d in history:
    if d.confidence < 0.5:
        print(f"Low confidence decision: {d.action}")
```

### 4. Handle Low Confidence

```python
decision = await architect.make_decision(context)

if decision.confidence < 0.6:
    print(f"⚠️ Low confidence ({decision.confidence:.2f})")
    print(f"Consider alternatives: {decision.alternatives}")
    
    # Ask for human approval
    approved = await ask_human_approval(decision)
    if not approved:
        # Try alternative
        pass
```

---

## Error Handling

```python
try:
    decision = await architect.make_decision(context)
except RuntimeError as e:
    print(f"Decision making failed: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## Performance

- **Decision time:** ~10-50ms
- **Database writes:** 1 per decision
- **Memory usage:** Minimal (stateless)

---

## See Also

- [Decision Maker API](decision-maker.md) — Strategy selection
- [Orchestrator API](orchestrator.md) — Async coordination
- [Event Store API](event-store.md) — Audit trail
