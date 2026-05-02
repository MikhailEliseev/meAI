# meAI Assistant

## Project Overview

**meAI** — CEO-архитектор, который проектирует и создаёт **AIM** (AI-first medical marketing agency at iamaim.ru).

**Two-Level System:**
- **meAI** (здесь, `/Users/mikhaileliseev/Desktop/Dev/!meAI`) — архитектор агентства
- **AIM Agency** (там, `/Users/mikhaileliseev/Desktop/Dev/AIM`) — само агентство с Опером и агентами

**User Role:** Medical marketer building AI-first agency  
**Stack:** Python 3.11+, FastAPI, SQLite, Obsidian  
**Started:** 2026-05-01 with Superflow greenfield scaffolding

## Development Philosophy: Deep & Correct

**Принцип:** Делаем всё глубоко и правильно, без спешки.
- Строим самую сложную систему, но самую рабочую
- Полная автономность всех компонентов
- Каждый агент — это код с логикой, не просто vault
- Никаких заглушек и "потом доделаем"

## Architecture

### Three-Layer Hierarchy

```
YOU (Human)
  ↓ strategic questions
ARCHITECT (Strategy Layer)
  ↓ strategic decisions
OPERATOR (Tactical Layer)
  ↓ task delegation
AGENTS (Execution Layer)
  ↓ results
OPERATOR
  ↓ aggregated report
YOU
```

### Architect (Strategy Layer)

**Architect** — стратегический советник (`src/meai/core/architect.py`):
- Принимает стратегические решения
- Анализирует контекст и ограничения
- Генерирует и оценивает альтернативы
- Выдаёт решения с обоснованием и уверенностью
- Хранит историю решений для обучения

**Использование:**
```python
from scripts.aim_cli import ask_architect

decision = await ask_architect(
    goal="Launch iamaim.ru successfully",
    constraints=["budget < 10000", "time < 3 months"],
    resources={"budget": 8000, "team": 3}
)
```

### Operator (Tactical Layer)

**Operator** — автономный операционный директор (`src/meai/agents/operator.py`):
- **Получает задачи** от YOU или Architect
- **Принимает тактические решения** (кому делегировать, как распределить)
- **Делегирует задачи** агентам через Event Bus
- **Собирает результаты** от агентов
- **Агрегирует отчёты** и отправляет YOU
- **Имеет собственную логику** принятия решений

**Ключевые методы:**
- `receive_task()` — получить задачу от YOU/Architect
- `make_tactical_decision()` — решить, как выполнить задачу
- `delegate_to_agent()` — делегировать агенту через Event Bus
- `collect_results()` — собрать результаты от агентов
- `report_to_user()` — отчитаться YOU

**Стратегии выполнения:**
- **Direct** — одна задача, один агент
- **Sequential** — задачи выполняются последовательно
- **Parallel** — задачи выполняются параллельно
- **Hybrid** — фазы с параллельными подзадачами

### Agents (Execution Layer)

**Агенты** — автономные исполнители с кодом и логикой:

**SEO Agent** (`src/meai/agents/seo_agent.py` - TODO):
- Анализ конкурентов
- Подбор ключевых слов
- Оптимизация контента
- Мониторинг позиций

**Content Agent** (`src/meai/agents/content_agent.py` - TODO):
- Генерация контента
- Редактура и проверка
- SEO-оптимизация текстов
- Планирование публикаций

**Ads Agent** (`src/meai/agents/ads_agent.py` - TODO):
- Создание кампаний
- Оптимизация бюджета
- A/B тестирование
- Анализ конверсий

**Базовый класс Agent** (`src/meai/agents/base_agent.py` - TODO):
```python
class Agent:
    async def receive_task(self, task: Task) -> None
    async def execute_task(self, task: Task) -> TaskResult
    async def report_result(self, result: TaskResult) -> None
    async def learn_from_feedback(self, feedback: Feedback) -> None
```

## Core Components

1. **Strategy Layer** (`src/meai/core/`)
   - `architect.py` — Strategic decision making (IMPLEMENTED)
   - `decision_maker.py` — Strategy selection with learning (IMPLEMENTED)
   - `orchestrator.py` — Async coordination (IMPLEMENTED)
   - `rollback.py` — Snapshot + event replay (IMPLEMENTED)

2. **Tactical Layer** (`src/meai/agents/`)
   - `operator.py` — Autonomous operational director (IMPLEMENTED ✅)
   - `base_agent.py` — Base class for all agents (TODO)
   - `seo_agent.py` — SEO execution agent (TODO)
   - `content_agent.py` — Content execution agent (TODO)
   - `ads_agent.py` — Ads execution agent (TODO)

3. **Infrastructure** (`src/meai/`)
   - `events/event_bus.py` — Async messaging (P0-P3) (IMPLEMENTED ✅)
   - `events/event_store.py` — Immutable audit log (IMPLEMENTED)
   - `memory/obsidian.py` — Vault integration (IMPLEMENTED ✅)
   - `storage/database.py` — SQLAlchemy async (IMPLEMENTED ✅)
   - `agents/factory.py` — Agent creation (IMPLEMENTED)

4. **Memory System** (`obsidian/`)
   - `operator/` — Operator's vault (decisions, tasks, reports)
   - `seo-agent/` — SEO agent's vault (analysis, keywords, reports)
   - `content-agent/` — Content agent's vault (articles, plans)
   - `ads-agent/` — Ads agent's vault (campaigns, metrics)
   - `SYSTEM.md` — Registry of all agents

5. **Data Layer** (`data/`)
   - SQLite for structured data (tasks, metrics, logs, decisions)
   - Obsidian for unstructured knowledge and agent memory

## Key Files

| File | Purpose | Status |
|------|---------|--------|
| `src/meai/core/architect.py` | Strategic decision making | ✅ IMPLEMENTED |
| `src/meai/core/decision_maker.py` | Strategy selection with learning | ✅ IMPLEMENTED |
| `src/meai/core/orchestrator.py` | Async coordination | ✅ IMPLEMENTED |
| `src/meai/core/rollback.py` | Snapshot + event replay | ✅ IMPLEMENTED |
| `src/meai/agents/operator.py` | Autonomous Operator | ✅ IMPLEMENTED |
| `src/meai/agents/base_agent.py` | Base agent class | ⏳ TODO |
| `src/meai/agents/seo_agent.py` | SEO agent implementation | ⏳ TODO |
| `src/meai/agents/content_agent.py` | Content agent implementation | ⏳ TODO |
| `src/meai/agents/ads_agent.py` | Ads agent implementation | ⏳ TODO |
| `src/meai/events/event_bus.py` | Async messaging system | ✅ IMPLEMENTED |
| `src/meai/events/event_store.py` | Immutable audit log | ✅ IMPLEMENTED |
| `src/meai/memory/obsidian.py` | Obsidian vault integration | ✅ IMPLEMENTED |
| `src/meai/agents/factory.py` | Agent creation | ✅ IMPLEMENTED |
| `scripts/aim_cli.py` | CLI for Architect | ✅ IMPLEMENTED |
| `scripts/use_architect.py` | Architect usage examples | ✅ IMPLEMENTED |
| `scripts/create_aim_agency.py` | Agency creation script | ✅ IMPLEMENTED |
| `scripts/test_aim_agency.py` | Agency testing script | ✅ IMPLEMENTED |
| `scripts/test_operator.py` | Operator testing script | ✅ IMPLEMENTED |

## Commands

- `source venv/bin/activate` — Activate virtual environment
- `python scripts/test_operator.py` — Test Operator
- `uvicorn meai.main:app --reload` — Start development server (TODO)
- `pytest` — Run tests (TODO)
- `ruff check . && ruff format .` — Lint and format
- `mypy src/` — Type checking

## Conventions

### Code Style
- Python 3.11+ with type hints
- Async/await for I/O operations
- Pydantic for data validation
- SQLAlchemy 2.0 async for database

### Memory Management
- All context goes to `obsidian/` as markdown
- Use frontmatter for metadata
- Link related notes with `[[wikilinks]]`
- Daily notes in `obsidian/daily/YYYY-MM-DD.md`

### AIM Agency Context
- Medical marketing focus
- AI-first approach
- Domain: iamaim.ru
- Target: Building agency infrastructure and processes

## Workflow

### Phase 1: Strategic Planning (YOU → ARCHITECT)

1. YOU задаёшь стратегический вопрос Architect
2. Architect анализирует контекст и ограничения
3. Architect генерирует альтернативы
4. Architect выдаёт решение с обоснованием
5. Решение сохраняется в базу для обучения

**Пример:**
```python
from scripts.aim_cli import ask_architect

decision = await ask_architect(
    goal="Launch iamaim.ru successfully",
    constraints=["budget < 10000", "time < 3 months"],
    resources={"budget": 8000, "team": 3}
)
print(decision.action)
print(decision.rationale)
```

### Phase 2: Tactical Execution (ARCHITECT → OPERATOR → AGENTS)

1. Architect передаёт стратегическое решение Operator
2. Operator принимает тактическое решение (как выполнить)
3. Operator делегирует задачи агентам через Event Bus
4. Агенты выполняют задачи автономно
5. Агенты отправляют результаты Operator через Event Bus
6. Operator агрегирует результаты
7. Operator отчитывается YOU

**Пример:**
```python
# Operator receives strategic decision
await operator.receive_task(task_from_architect)

# Operator makes tactical decision
tactical_plan = await operator.make_tactical_decision(task)

# Operator delegates to agents
for subtask in tactical_plan.subtasks:
    await operator.delegate_to_agent(subtask)

# Operator collects results
results = await operator.collect_results()

# Operator reports to YOU
await operator.report_to_user(results)
```

### Phase 3: Learning & Improvement

1. Operator и агенты сохраняют результаты в vaults
2. Architect анализирует историю решений
3. Decision Maker обучается на результатах
4. Система улучшает качество решений

## Environment Variables

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
OBSIDIAN_VAULT_PATH=./obsidian
DATABASE_URL=sqlite+aiosqlite:///./data/meai.db
LOG_LEVEL=INFO
```

## Model Selection Strategy

### Task-Based Model Usage

Используй разные модели для разных типов задач:

- **Tasks 1-10 (Infrastructure):** Sonnet 4.5 - Setup, config, database, Obsidian, event store
- **Tasks 11-17 (Safety & Monitoring):** Sonnet 4.5 - Loop detector, timeouts, health checks, metrics
- **Tasks 18-20 (Deployment):** Haiku 4.5 + Opus review - FastAPI, Docker, tests, docs
- **Tasks 21-25 (Core Components):** Opus 4.6 ⭐ - Architect, Decision Maker, Orchestrator, Registry, Rollback

### Switching Models in Claude Code

Use `/model <name>` command:
- `/model opus` - For complex architecture (Tasks 21-25)
- `/model sonnet` - For standard implementation (Tasks 1-17)
- `/model haiku` - For boilerplate code (Tasks 18-20)

### Why This Strategy?

- **Quality:** Opus для сложной логики (Tasks 21-25)
- **Cost:** Sonnet для стандартных задач (Tasks 1-17)
- **Speed:** Haiku для boilerplate (Tasks 18-20)
- **Savings:** ~60% vs all-Opus (~$85-160 vs $200-300)

## Notes

- This is a **terminal-based assistant** — no separate UI
- All interaction happens in Claude Code CLI
- Obsidian vault is the persistent memory
- Skills are invoked directly through Claude Code

## Current Status

**Phase 3 (Part 1) - COMPLETED ✅**
- Operator implemented with full autonomy
- Infrastructure created (Database, Event Bus, Obsidian)
- Tests passing (2 tasks, 12 subtasks delegated)
- Documentation complete

**Phase 3 (Part 2) - IN PROGRESS ⏳**
- Next: Implement Agent base class
- Next: Implement SEO, Content, Ads agents
- Next: Add result collection and reporting
- Next: End-to-end test

<!-- updated-by-superflow:2026-05-02 -->
