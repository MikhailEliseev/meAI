# meAI Assistant

## Session Recovery (READ THIS FIRST!)

**При обрыве сессии:**

1. **Читай `SESSION.md`** — текущее состояние работы (что делали, что дальше)
2. **Проверь `CHECKPOINTS.md`** — последний чекпоинт и статус компонентов
3. **Смотри `obsidian/*/wiki/log.md`** — операционная история агентов
4. **Auto-memory загружается автоматически** — знания о проекте

**Цель:** Восстановление контекста за < 2 минуты

**Важно:** Всегда обновляй `SESSION.md` при завершении задачи или переходе к новой.

---

## Project Overview

**meAI** — CEO-архитектор, который проектирует и создаёт **AIM** (AI-first medical marketing agency at iamaim.ru).

**Architecture:**
```
!meAI/                          # Command Center (ты работаешь отсюда)
├── src/meai/                   # Framework (базовые классы)
│   ├── core/                   # Architect, Orchestrator, Decision Maker
│   ├── agents/                 # Base: Operator, BaseMagister, BaseAgent
│   ├── events/                 # Event Bus, Event Store
│   ├── memory/                 # Obsidian integration
│   └── storage/                # Database
├── AIM/                        # 🎯 Agency (приложение)
│   ├── src/aim/                # Конкретная реализация
│   │   ├── magisters/          # SEO, Content, Ads Magisters
│   │   └── subagents/          # Конкретные субагенты
│   ├── obsidian/               # Vaults агентов (LLM Wiki)
│   │   ├── operator/
│   │   ├── seo-magister/
│   │   ├── content-magister/
│   │   └── ads-magister/
│   └── data/                   # База агентства
├── obsidian/architect/         # Твой vault
├── scripts/                    # CLI для управления
└── SESSION.md                  # Текущая работа
```

**Workflow:**
- Ты работаешь из `/Users/mikhaileliseev/Desktop/Dev/!meAI` (командный пункт)
- Используешь `/architect` для стратегических решений
- Architect создаёт код в `AIM/` (агентство)
- Framework (`src/meai/`) переиспользуется агентством (`AIM/`)

**User Role:** Medical marketer building AI-first agency  
**Stack:** Python 3.11+, FastAPI, SQLite, Obsidian  
**Started:** 2026-05-01 with Superflow greenfield scaffolding

## Development Philosophy: Deep & Correct

**Принцип:** Делаем всё глубоко и правильно, без спешки.
- Строим самую сложную систему, но самую рабочую
- Полная автономность всех компонентов
- Каждый агент — это код с логикой, не просто vault
- Никаких заглушек и "потом доделаем"

## Quality Over Speed Rule

**КРИТИЧЕСКИ ВАЖНО:** Качество важнее скорости. Всегда.

**Правило:**
- Мы никуда не торопимся, даже если система будет работать день или два
- Главное — качество, которое разбирает конкурентов по молекулам
- Каждый агент должен делать свою работу глубоко и тщательно
- Поверхностный анализ = катастрофа

**Примеры:**
- ❌ CI Tech Agent анализирует только главную страницу за 1 секунду
- ✅ CI Tech Agent анализирует 50+ страниц, структуру, контент за 10 минут

**Почему это важно:**
- Поверхностный анализ не даёт конкурентных преимуществ
- Клиенты платят за глубину, не за скорость
- Качественный анализ = находим то, что конкуренты пропустили

**Применение:**
- Если агент работает быстро, но поверхностно → переделать на глубокий анализ
- Если есть выбор между "быстро" и "качественно" → всегда выбирать качественно
- Время работы агента не критично (1 минута vs 1 час vs 1 день)

## Mock Data Rule

**КРИТИЧЕСКИ ВАЖНО:** Никаких mock данных в production коде.

**Правило:** Если агенту нужны данные для работы, он должен:
1. **Запросить у пользователя** через AskUserQuestion (URL, API ключи, параметры)
2. **Получить реальные данные** из источника (API, веб-скрапинг, файлы)
3. **Обработать реальные данные** и вернуть результат

**Запрещено:**
- Mock данные в коде агента
- Hardcoded примеры вместо реальных данных
- "Заглушки на потом"

**Исключения:**
- Unit тесты (только в `tests/` директории)
- Примеры в документации (только в комментариях/docstrings)

**Примеры правильного подхода:**
```python
# ✅ ПРАВИЛЬНО
async def collect_metrics(self, url: str):
    # Запрашиваем URL у пользователя
    if not url:
        url = await self.ask_user("Введите URL сайта для анализа")
    
    # Получаем реальные данные
    response = await self.fetch(url)
    return self.parse(response)

# ❌ НЕПРАВИЛЬНО
async def collect_metrics(self):
    # Mock данные
    return {"traffic": 1000, "bounce_rate": 0.5}
```

## Excalidraw Diagrams Rule

**КРИТИЧЕСКИ ВАЖНО:** Excalidraw диаграммы должны максимально чётко отражать реальную структуру кода.

**Правило:** Если что-то реализовано в коде, оно ОБЯЗАНО быть правильно отражено в Excalidraw диаграмме.

**Примеры:**
- Domain Analytics субагенты (SEO/Content/Ads/AI Analytics) - это 5-е субагенты своих Magisters → должны быть визуально под своими Magisters, а не в общем блоке
- Analytics Magister субагенты (Data Collector, Data Processor, etc.) → должны быть под Analytics Magister
- Иерархия Magister → Subagents должна быть визуально очевидна

**Почему это важно:**
- Диаграмма - это документация архитектуры
- Несоответствие код ↔ диаграмма вводит в заблуждение
- Визуальная структура помогает понять систему

**Когда обновлять:**
- После создания нового Magister/Subagent
- После изменения архитектурных связей
- После рефакторинга иерархии

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

**Базовый класс Agent** (`src/meai/agents/base_agent.py` - ✅ IMPLEMENTED):
```python
class Agent(ABC):
    @abstractmethod
    async def execute_task(self, task: Task) -> TaskResult
    
    @abstractmethod
    def get_capabilities(self) -> list[str]
    
    async def receive_task(self, task: Task) -> None
    async def report_result(self, result: TaskResult) -> None
    async def learn_from_feedback(self, feedback: Feedback) -> None
    async def get_performance_metrics(self) -> dict[str, Any]
```

## Core Components

1. **Strategy Layer** (`src/meai/core/`)
   - `architect.py` — Strategic decision making (IMPLEMENTED)
   - `decision_maker.py` — Strategy selection with learning (IMPLEMENTED)
   - `orchestrator.py` — Async coordination (IMPLEMENTED)
   - `rollback.py` — Snapshot + event replay (IMPLEMENTED)

2. **Tactical Layer** (`src/meai/agents/`)
   - `operator.py` — Autonomous operational director (✅ IMPLEMENTED)
   - `base_agent.py` — Base class for all agents (✅ IMPLEMENTED)
   - `seo_agent.py` — SEO execution agent (TODO)
   - `content_agent.py` — Content execution agent (TODO)
   - `ads_agent.py` — Ads execution agent (TODO)

3. **Infrastructure** (`src/meai/`)
   - `events/event_bus.py` — Async messaging (P0-P3) (IMPLEMENTED ✅)
   - `events/event_store.py` — Immutable audit log (IMPLEMENTED)
   - `memory/obsidian.py` — Vault integration (IMPLEMENTED ✅)
   - `storage/database.py` — SQLAlchemy async (IMPLEMENTED ✅)
   - `agents/factory.py` — Agent creation (IMPLEMENTED)

4. **Memory System** (Obsidian vaults with LLM Wiki pattern)
   - `obsidian/architect/` — Architect's strategic vault (в корне !meAI)
   - `AIM/obsidian/operator/` — Operator's tactical vault
   - `AIM/obsidian/seo-magister/` — SEO Magister's domain vault
   - `AIM/obsidian/content-magister/` — Content Magister's domain vault
   - `AIM/obsidian/ads-magister/` — Ads Magister's domain vault

5. **Data Layer**
   - `data/` — meAI framework database (в корне !meAI)
   - `AIM/data/` — AIM agency database
   - SQLite for structured data (tasks, metrics, logs, decisions)
   - Obsidian for unstructured knowledge and agent memory

## Key Files

| File                               | Purpose                          | Status        |
| ---------------------------------- | -------------------------------- | ------------- |
| `src/meai/core/architect.py`       | Strategic decision making        | ✅ IMPLEMENTED |
| `src/meai/core/decision_maker.py`  | Strategy selection with learning | ✅ IMPLEMENTED |
| `src/meai/core/orchestrator.py`    | Async coordination               | ✅ IMPLEMENTED |
| `src/meai/core/rollback.py`        | Snapshot + event replay          | ✅ IMPLEMENTED |
| `src/meai/agents/operator.py`      | Autonomous Operator              | ✅ IMPLEMENTED |
| `src/meai/agents/base_agent.py`    | Base agent class                 | ✅ IMPLEMENTED |
| `src/meai/agents/seo_agent.py`     | SEO agent implementation         | ⏳ TODO        |
| `src/meai/agents/content_agent.py` | Content agent implementation     | ⏳ TODO        |
| `src/meai/agents/ads_agent.py`     | Ads agent implementation         | ⏳ TODO        |
| `src/meai/events/event_bus.py`     | Async messaging system           | ✅ IMPLEMENTED |
| `src/meai/events/event_store.py`   | Immutable audit log              | ✅ IMPLEMENTED |
| `src/meai/memory/obsidian.py`      | Obsidian vault integration       | ✅ IMPLEMENTED |
| `src/meai/agents/factory.py`       | Agent creation                   | ✅ IMPLEMENTED |
| `scripts/aim_cli.py`               | CLI for Architect                | ✅ IMPLEMENTED |
| `scripts/use_architect.py`         | Architect usage examples         | ✅ IMPLEMENTED |
| `scripts/create_aim_agency.py`     | Agency creation script           | ✅ IMPLEMENTED |
| `scripts/test_aim_agency.py`       | Agency testing script            | ✅ IMPLEMENTED |
| `scripts/test_operator.py`         | Operator testing script          | ✅ IMPLEMENTED |
| `scripts/test_base_agent.py`       | Base agent testing script        | ✅ IMPLEMENTED |

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

### Memory Management - LLM Wiki Pattern (FUNDAMENTAL)

**CRITICAL RULE:** Все Obsidian vaults и пространства субагентов ОБЯЗАНЫ следовать паттерну LLM Wiki от Andrej Karpathy.

**Паттерн как "Отче наш":**
- Wiki = persistent, compounding artifact (не RAG, а compiled knowledge)
- Три слоя: raw sources (immutable) → wiki (LLM-generated) → schema (rules)
- Три операции: Ingest (обработка), Query (вопросы), Lint (проверка здоровья)

**Обязательная структура для КАЖДОГО vault:**

```
vault/
├── raw/                    # Слой 1: Источники (immutable)
├── wiki/                   # Слой 2: Структурированное знание
│   ├── index.md           # Content-oriented каталог
│   ├── log.md             # Chronological запись операций
│   ├── concepts/          # Концепции и паттерны
│   ├── technologies/      # Технологии и инструменты
│   ├── strategies/        # Стратегии и методы
│   ├── agents/            # Агенты системы
│   ├── workflows/         # Процессы и workflow
│   ├── projects/          # Проекты
│   ├── sources/           # Обработанные источники (summary)
│   └── connections/       # Связи и синтезы
├── decisions/             # Слой 3: Стратегические решения
└── SCHEMA.md             # Правила и конвенции vault
```

**Коммуникация между vaults:**
- Каждый vault имеет свой wiki/ с 8 категориями
- Субагенты читают wiki/ других агентов (не raw/)
- Синтезы создаются в connections/
- Решения фиксируются в decisions/

**Операции (обязательные):**
1. **Ingest** - raw/ → wiki/ (создание/обновление страниц по категориям)
2. **Query** - вопрос → чтение wiki/ → ответ с цитатами → новая страница
3. **Lint** - проверка противоречий, orphans, gaps, устаревших данных

**Специальные файлы:**
- `index.md` - каталог всех страниц с статистикой
- `log.md` - хронология всех операций (формат: `## [YYYY-MM-DD HH:MM] operation | Description`)

**Правило обработки:**
- ВСЕГДА проверяй frontmatter `status: processed` перед чтением
- Если `status: processed` → читай wiki/ (из поля `output`)
- Если нет → читай raw/ и обрабатывай

**Примеры vaults:**
- `obsidian/architect/` - Architect's strategic vault
- `obsidian/operator/` - Operator's tactical vault
- `obsidian/seo-agent/` - SEO agent's execution vault
- `obsidian/content-agent/` - Content agent's execution vault

Это НЕ рекомендация - это ЗАКОН для всех Obsidian пространств в системе.

### AIM Agency Context
- Medical marketing focus
- AI-first approach
- Domain: iamaim.ru
- Target: Building agency infrastructure and processes

### Project Structure

**Framework vs Application:**

```
src/meai/           # Framework (переиспользуемый)
├── core/           # Базовые компоненты (Architect, Orchestrator)
├── agents/         # Базовые классы (Operator, BaseMagister, BaseAgent)
├── events/         # Event Bus, Event Store
├── memory/         # Obsidian integration
└── storage/        # Database

AIM/                # Application (конкретное агентство)
├── src/aim/        # Конкретная реализация
│   ├── magisters/  # SEO, Content, Ads Magisters
│   └── subagents/  # Конкретные субагенты
├── obsidian/       # Vaults агентов
└── data/           # База агентства
```

**Импорты:**
```python
# В AIM/src/aim/magisters/seo_magister.py
from meai.agents.magister_base import BaseMagister  # Framework
from meai.events.event_bus import EventBus          # Framework

class SEOMagister(BaseMagister):  # Конкретная реализация
    ...
```

**Разработка:**
- Работаешь из корня `/Users/mikhaileliseev/Desktop/Dev/!meAI`
- Framework код в `src/meai/`
- Agency код в `AIM/src/aim/`
- Всё в одном репо, но логически разделено

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
- ✅ Agent base class implemented
- Next: Implement SEO Agent
- Next: Implement Content Agent
- Next: Implement Ads Agent
- Next: Add result collection and reporting
- Next: End-to-end test

<!-- updated-by-superflow:2026-05-02 -->
