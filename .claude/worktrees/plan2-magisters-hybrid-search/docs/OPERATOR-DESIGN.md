# Operator Design

## Overview

**Operator** — автономный операционный директор AIM Agency.

**Роль:** Тактический слой между стратегией (Architect) и исполнением (Agents).

## Core Responsibilities

1. **Receive Tasks** — получать задачи от YOU или Architect
2. **Make Tactical Decisions** — решать, как выполнить задачу
3. **Delegate to Agents** — распределять подзадачи между агентами
4. **Monitor Execution** — отслеживать выполнение задач
5. **Collect Results** — собирать результаты от агентов
6. **Aggregate Reports** — формировать сводные отчёты
7. **Report to User** — отчитываться YOU

## Implementation Status

✅ **IMPLEMENTED** (2026-05-02)
- Full autonomous Operator with 850+ lines of code
- 4 execution strategies: Direct, Sequential, Parallel, Hybrid
- Task analysis and tactical decision making
- Agent delegation via Event Bus
- Database and Obsidian vault integration
- Comprehensive tests passing

See `src/meai/agents/operator.py` for full implementation.

## Architecture

```
┌─────────────────────────────────────────┐
│           OPERATOR                      │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────────────────────────┐  │
│  │   Task Receiver                  │  │
│  │   - Receive from YOU/Architect   │  │
│  │   - Validate task                │  │
│  │   - Store in vault               │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │   Tactical Decision Maker        │  │
│  │   - Analyze task                 │  │
│  │   - Choose strategy              │  │
│  │   - Break into subtasks          │  │
│  │   - Select agents                │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │   Task Delegator                 │  │
│  │   - Send via Event Bus           │  │
│  │   - Set priorities               │  │
│  │   - Track assignments            │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │   Execution Monitor              │  │
│  │   - Track progress               │  │
│  │   - Handle timeouts              │  │
│  │   - Detect failures              │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │   Result Collector               │  │
│  │   - Receive from Event Bus       │  │
│  │   - Validate results             │  │
│  │   - Store in vault               │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │   Report Aggregator              │  │
│  │   - Combine results              │  │
│  │   - Generate insights            │  │
│  │   - Format report                │  │
│  └──────────────────────────────────┘  │
│                                         │
└─────────────────────────────────────────┘
```

## Execution Strategies

### 1. Direct Strategy
- **When:** Single capability required
- **How:** One agent, direct delegation
- **Example:** "Analyze competitors" → SEO Agent

### 2. Sequential Strategy
- **When:** Tasks have dependencies
- **How:** Execute one after another
- **Example:** "Research keywords → Optimize content"

### 3. Parallel Strategy
- **When:** Independent tasks, high priority
- **How:** All agents work simultaneously
- **Example:** "SEO analysis + Content creation + Ad setup"

### 4. Hybrid Strategy
- **When:** Complex tasks with phases
- **How:** Phases with parallel subtasks
- **Example:** Phase 1 (parallel: research, setup) → Phase 2 (parallel: execution)

## Decision Making Logic

### Strategy Selection

Operator выбирает стратегию на основе:

1. **Task Complexity**
   - Simple (1 agent) → Direct
   - Medium (2-3 agents) → Sequential or Parallel
   - Complex (4+ agents) → Hybrid

2. **Dependencies**
   - No dependencies → Parallel
   - Linear dependencies → Sequential
   - Partial dependencies → Hybrid

3. **Priority**
   - P0 (Critical) → Fastest strategy
   - P1 (High) → Balanced
   - P2-P3 → Resource-efficient

4. **Resource Availability**
   - All agents available → Parallel
   - Some busy → Sequential or wait

### Agent Selection

Operator выбирает агентов на основе:

1. **Capability Match** — Task requires SEO → SEO Agent
2. **Agent Load** — Prefer agents with fewer active tasks
3. **Agent Performance** — Track success rate per agent
4. **Task History** — Prefer agents with experience

## Database Schema

```sql
-- Tasks table
CREATE TABLE operator_tasks (
    task_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    goal TEXT NOT NULL,
    description TEXT,
    constraints TEXT,
    resources TEXT,
    priority INTEGER NOT NULL,
    deadline TIMESTAMP,
    status TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

-- Tactical plans table
CREATE TABLE operator_plans (
    plan_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    strategy TEXT NOT NULL,
    subtasks TEXT NOT NULL,
    agent_assignments TEXT,
    estimated_duration INTEGER,
    risk_level TEXT,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (task_id) REFERENCES operator_tasks(task_id)
);

-- Subtasks table
CREATE TABLE operator_subtasks (
    subtask_id TEXT PRIMARY KEY,
    parent_task_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    action TEXT NOT NULL,
    description TEXT,
    dependencies TEXT,
    priority INTEGER NOT NULL,
    status TEXT NOT NULL,
    result TEXT,
    created_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    FOREIGN KEY (parent_task_id) REFERENCES operator_tasks(task_id)
);

-- Reports table
CREATE TABLE operator_reports (
    report_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    summary TEXT NOT NULL,
    insights TEXT,
    metrics TEXT,
    issues TEXT,
    recommendations TEXT,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (task_id) REFERENCES operator_tasks(task_id)
);
```

## Vault Structure

```
obsidian/operator/
├── tasks/
│   ├── task-001.md          # Received tasks
│   ├── task-002.md
│   └── ...
├── plans/
│   ├── plan-001.md          # Tactical plans
│   ├── plan-002.md
│   └── ...
├── delegations/
│   ├── delegation-001.md    # Delegation records
│   ├── delegation-002.md
│   └── ...
├── monitoring/
│   ├── task-001.md          # Execution monitoring
│   ├── task-002.md
│   └── ...
├── results/
│   ├── task-001-results.md  # Collected results
│   ├── task-002-results.md
│   └── ...
├── reports/
│   ├── task-001-report.md   # Aggregated reports
│   ├── task-002-report.md
│   └── ...
└── user-reports/
    ├── report-001.md        # Reports sent to YOU
    ├── report-002.md
    └── ...
```

## Usage Example

```python
from meai.agents.operator import Operator, Task, TaskStatus
from datetime import datetime, timedelta, timezone

# Initialize Operator
operator = Operator(
    database_url="sqlite+aiosqlite:///./data/meai.db",
    vault_path="./obsidian"
)
await operator.initialize()

# Create task
task = Task(
    task_id="task-001",
    source="user",
    goal="Launch comprehensive marketing campaign",
    description="Create SEO strategy, generate content, set up ads",
    constraints=["budget < 5000", "time < 1 week"],
    resources={"budget": 4500, "tools": ["ahrefs", "google-ads"]},
    priority=0,  # Critical
    deadline=datetime.now(timezone.utc) + timedelta(days=7),
    status=TaskStatus.RECEIVED,
    created_at=datetime.now(timezone.utc),
    updated_at=datetime.now(timezone.utc),
)

# Operator processes task
await operator.receive_task(task)

# Operator automatically:
# 1. Analyzes task complexity
# 2. Creates tactical plan (Hybrid strategy)
# 3. Breaks into 9 subtasks
# 4. Assigns to 3 agents (SEO, Content, Ads)
# 5. Delegates via Event Bus
# 6. Stores everything in database and vault
```

## Test Results

```
✅ Test 1: Simple Task (Direct Strategy)
   - 1 task → 3 subtasks → 1 agent (SEO)
   - Strategy: Sequential
   - Risk: Low
   - Duration: 1:30:00

✅ Test 2: Complex Task (Hybrid Strategy)
   - 1 task → 9 subtasks → 3 agents
   - Strategy: Hybrid (phases with parallel execution)
   - Risk: High
   - Duration: 4:45:00

✅ Database: 2 tasks, 2 plans, 12 subtasks stored
✅ Vault: 44 files created (tasks, plans, delegations)
```

## Next Steps

**Phase 3 Part 2:**
1. ⏳ Implement Agent base class
2. ⏳ Implement SEO, Content, Ads agents
3. ⏳ Add result collection (`collect_results()`)
4. ⏳ Add report aggregation (`aggregate_report()`)
5. ⏳ Add user reporting (`report_to_user()`)
6. ⏳ End-to-end test: YOU → Operator → Agents → Operator → YOU
