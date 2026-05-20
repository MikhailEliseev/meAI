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
meAI/                           # Command Center (ты работаешь отсюда)
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
- Ты работаешь из `/Users/mikhaileliseev/Desktop/Dev/meAI` (командный пункт)
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

## Complete Before Next Rule

**КРИТИЧЕСКИ ВАЖНО:** Доводим до 100% перед переходом к следующей задаче.

**Правило:**
- Пока не улучшим существующее до конца, не переходим к другой задаче
- Не предлагаем "Вариант 1, Вариант 2, Вариант 3"
- Просто делаем до упора то, что должны делать по плану
- 100% результат = все stubs заменены на real implementations, все тесты проходят, всё работает

**Запрещено:**
- Предлагать варианты выбора, когда текущая задача не завершена
- Переходить к новым фичам, пока существующие не доведены до 100%
- Оставлять stubs "на потом"

**Разрешено:**
- Только когда текущая задача на 100% завершена, можно предлагать следующую

**Применение:**
- Если есть 6 Magisters со stubs → улучшаем их до real implementations
- Только после 100% completion → переходим к новым Magisters
- Фокус на качестве текущей задачи, не на количестве задач

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

## Large File Write Rule

**КРИТИЧЕСКИ ВАЖНО:** Write tool имеет ограничение на размер content параметра (~20-30 KB).

**Симптомы проблемы:**
- ❌ `402 rate limit` ошибка — это НЕ про API лимиты, а про **слишком большой контекст в одном запросе**
- ❌ `The required parameter 'content' is missing` — параметр отброшен из-за размера
- ❌ `The required parameter 'X' is missing` — любой параметр может быть отброшен
- ❌ Любая странная ошибка при записи файла 200+ строк

**Правило:** ВСЕГДА разбивай большие файлы (200+ строк) на части. Не жди ошибки!

1. **Разбей на части ЗАРАНЕЕ:**
   - Первая часть (150-200 строк) → Write tool
   - Остальные части → Bash append через `cat >> file << 'EOF'`

2. **Проверь результат:**
   - `wc -l file` — количество строк
   - `ls -lh file` — размер файла

**Пример:**
```python
# Шаг 1: Создать файл с начальным содержимым
Write(file_path="spec.md", content="[первые 150-200 строк]")

# Шаг 2: Добавить остальное через Bash
Bash(command="""cat >> spec.md << 'EOF'
[остальное содержимое]
EOF""")

# Шаг 3: Проверить
Bash(command="wc -l spec.md && ls -lh spec.md")
```

**Почему это работает:**
- Write tool передаёт content через API (есть лимит)
- Bash append пишет напрямую в файл (нет лимита)
- Результат идентичен полной записи

**Применение:**
- Спецификации агентов (обычно 30-50 KB)
- Большие конфигурационные файлы
- Документация с примерами кода

## Spec Writer Rule

**КРИТИЧЕСКИ ВАЖНО:** Всегда используй spec-writer skill при создании спецификаций агентов.

**Правило:** При создании любой спецификации агента/субагента:
1. **Запускай spec-writer skill** — `/spec-writer [название агента]`
2. **Skill автоматически выполнит deep-research** — глубокое исследование темы
3. **Получишь больше деталей** — статистика, API, лучшие практики, метрики
4. **Спецификация будет полнее** — не только твои знания, но и актуальные данные

**Почему это важно:**
- Твои знания могут быть неполными или устаревшими
- Deep research находит актуальную статистику с источниками
- Исследование выявляет API, инструменты, метрики, которые ты мог упустить
- Качество спецификации выше — больше деталей, примеров, данных

**Примеры:**
- ✅ GEO Optimization Agent — через spec-writer получили статистику (900M ChatGPT users/week, 44.2% цитирований из первых 30%)
- ✅ Исследование выявило правило первых 50 слов, FAQPage schema, llms.txt
- ✅ Нашли реальные API (GEO Tracker AI, Perplexity API) с ценами и лимитами
- ✅ **Competitor Content Analyzer (2026-05-12)** — первый тест GitHub-integrated подхода:
  - 4 production-ready репо (880+ звёзд): python-seo-analyzer, python-for-seo, seo-analyzer, ai-content-detector
  - Архитектурные паттерны: circuit breaker, exponential backoff, rate limiting, caching
  - API стоимость: SEMrush $499.95/мес, Ahrefs $949/мес, Playwright бесплатно
  - Yandex vs Google: keyword density 2-3% vs 0.5-1.5%, user behavior vs backlinks
  - 25+ примеров кода (адаптированы из production)
  - Качество: 15 источников, 87/100 credibility, 100% claim verification
  - Стоимость: $0.15 из $3.00 бюджета (95% экономия)
  - Время: 58 минут

**Применение:**
- Создаёшь новую спецификацию → запускай spec-writer
- Дорабатываешь существующую → запускай spec-writer для проверки упущений
- Не уверен в деталях → spec-writer найдёт актуальную информацию

**Экономия времени:**
- Без skill: 2-3 часа (интервью + написание + проверка)
- Со skill: 45-60 минут (автоматическое исследование + создание)
- Экономия: ~60-70%

**Валидация GitHub-integrated подхода (2026-05-12):**
- ✅ Подход работает! Находит production-ready паттерны, реальные API costs, battle-tested архитектуру
- ✅ GitHub repos дают то, что традиционное исследование пропускает: edge cases, retry logic, cost optimization
- ✅ Качество выше: 100% claim verification, 87/100 avg credibility, 25+ code examples
- ✅ Стоимость ниже: $0.15 вместо ожидаемых $1-3 (эффективный поиск)

## Teacher Agent — Continuous System Learning

**КРИТИЧЕСКИ ВАЖНО:** Teacher Agent — это Chief Learning Officer системы. Его единственная задача — следить за всеми источниками знаний и обучать остальных агентов.

**Принцип:** Система должна постоянно учиться и улучшаться, не устаревать.

**Workflow Teacher Agent (каждые 2-4 недели):**

```
Teacher Agent
  ↓
1. Читает список критических субагентов
  ↓
2. Для каждого субагента:
   ├─ Проверяет дату последнего обучения
   ├─ Запускает GitHub Search (новые топовые репо за период)
   ├─ Запускает Deep Research (новые best practices, API updates)
   ├─ Сравнивает с текущей реализацией субагента
   └─ Генерирует "Learning Report" с gap analysis
  ↓
3. Приоритизирует обновления:
   ├─ 🔴 CRITICAL: Новые алгоритмы/API (внедрить немедленно)
   ├─ 🟡 HIGH: Улучшения производительности (запланировать)
   └─ 🟢 LOW: Опциональные фичи (backlog)
  ↓
4. Создаёт задачи для обновления субагентов
  ↓
5. Сохраняет в Obsidian vault:
   └─ obsidian/teacher/wiki/learning-cycles/YYYY-MM-DD.md
```

**Что проверяет Teacher:**

1. **GitHub Monitoring:**
   - Новые топовые репо по теме субагента (за последние 2-4 недели)
   - Обновления в существующих репо (commits, releases)
   - Новые паттерны и архитектуры
   - Новые библиотеки/инструменты

2. **Industry Updates:**
   - Новые best practices (статьи, документация)
   - Обновления API (breaking changes, новые фичи)
   - Изменения алгоритмов (Google updates, Яндекс updates)
   - Новые compliance требования

3. **Performance Metrics:**
   - Метрики субагента (precision, recall, speed)
   - Сравнение с бенчмарками из GitHub
   - Bottlenecks и optimization opportunities

4. **Gap Analysis:**
   - Что есть в топовых GitHub решениях, но нет у нас
   - Что устарело в нашей реализации
   - Что можно улучшить

**Learning Report Format:**

```markdown
# Learning Cycle: YYYY-MM-DD

## Субагент: [Name]

### GitHub Findings
- **New Repo:** `user/repo` (stars, released date)
  - Feature: [что нового]
  - Architecture: [подход]
  - **Action:** [что внедрить]

### Industry Updates
- [Update description]
- **Action:** [что изменить]

### Performance Gap
- Current: [текущие метрики]
- Benchmark: [бенчмарк из GitHub]
- **Action:** [как оптимизировать]

### Recommendations
🔴 CRITICAL (implement now):
1. [Критичное обновление]

🟡 HIGH (plan for next sprint):
1. [Важное улучшение]

🟢 LOW (backlog):
1. [Опциональная фича]
```

**Obsidian Vault Structure:**

```
obsidian/teacher/
├── wiki/
│   ├── learning-cycles/          # Отчёты по циклам обучения
│   ├── subagents/                # Профили субагентов
│   ├── github-tracking/          # Отслеживание GitHub репо
│   └── industry-updates/         # Обновления индустрии
└── decisions/
    └── learning-strategy.md      # Стратегия обучения
```

**Метрики успеха Teacher Agent:**
- **Coverage:** % критических субагентов проверено
- **Freshness:** Средний возраст знаний субагентов (< 4 недели)
- **Impact:** % рекомендаций внедрено
- **Performance:** Улучшение метрик субагентов после обновления

**Почему это важно:**
- Система не устаревает (знания обновляются каждые 2-4 недели)
- Автоматическое отслеживание лучших практик из GitHub
- Проактивное обучение (не ждём проблем, предупреждаем их)
- Continuous improvement всей системы

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
   - `obsidian/architect/` — Architect's strategic vault (в корне meAI)
   - `AIM/obsidian/operator/` — Operator's tactical vault
   - `AIM/obsidian/seo-magister/` — SEO Magister's domain vault
   - `AIM/obsidian/content-magister/` — Content Magister's domain vault
   - `AIM/obsidian/ads-magister/` — Ads Magister's domain vault

5. **Data Layer**
   - `data/` — meAI framework database (в корне meAI)
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
- `obsidian/deep-research/` - Deep research tracking vault

Это НЕ рекомендация - это ЗАКОН для всех Obsidian пространств в системе.

### Deep Research Tracking Rule

**КРИТИЧЕСКИ ВАЖНО:** Все deep-research исследования ОБЯЗАНЫ архивироваться в `obsidian/deep-research/` vault.

**Правило:** После каждого deep-research:
1. **Запустить Ingest** — `python scripts/ingest_research.py ~/Documents/[Topic]_Research_[YYYYMMDD]/`
2. **Vault автоматически сохранит:**
   - Исходный отчёт в `raw/`
   - Метаданные (токены, стоимость, время) в `manifest.json`
   - Обновит статистику в `wiki/statistics/usage.md`
   - Добавит запись в `wiki/log.md`

**Почему это важно:**
- Отслеживание реальной стоимости исследований
- Выявление возможностей переиспользования (похожие темы)
- Оптимизация стратегии на основе данных
- История всех исследований для будущего анализа

**Примеры:**
- ✅ После создания Blog Content Agent → ingest исследование
- ✅ Перед новым исследованием → проверить `wiki/topics/` на похожие темы
- ✅ Раз в неделю → проверить `wiki/statistics/usage.md` для анализа трендов

**Применение:**
- Создаёшь спецификацию через spec-writer → автоматически запускается deep-research → после завершения запусти ingest
- Перед новым исследованием → проверь vault на похожие темы для переиспользования
- Если стоимость растёт → проверь `decisions/cost-optimization.md` для стратегии

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
- Работаешь из корня `/Users/mikhaileliseev/Desktop/Dev/meAI`
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

## Sprint 1: Keyword Research Agent - Core Infrastructure ✅

**Completed:** 2026-05-11

**Summary:**
- Built production-ready API clients layer for keyword research
- Implemented resilience patterns (circuit breaker, retry, rate limiting, caching)
- Created data validation with Pydantic schemas
- Added comprehensive test coverage (27 tests passing)
- Budget control and cost tracking

**Components Added:**

### 1. API Clients Layer (`AIM/src/aim/subagents/api_clients/`)

**Base Client** (`base.py`):
- Circuit breaker (fail_max=5, reset_timeout=60s)
- Retry with exponential backoff (1s → 30s max)
- Token bucket rate limiting
- 1-hour response caching
- Prometheus metrics
- Structured logging

**SEMrush Client** (`semrush.py`):
- Keyword Magic Tool API integration
- Pagination (100 keywords per page)
- Budget guard ($0.01 per request)
- Zero-volume handling with suggestions
- Intent detection
- Min volume filtering

**Ahrefs Client** (`ahrefs.py`):
- Fallback provider
- Keywords Explorer API
- Difficulty normalization
- Parent topic detection

### 2. Data Validation (`AIM/src/aim/subagents/schemas/`)

**API Response Schemas** (`api_responses.py`):
- `SEMrushKeywordData` - SEMrush response validation
- `AhrefsKeywordData` - Ahrefs response with normalization
- `KeywordDataUnified` - Cross-source unified format
- Field validators (volume, CPC, difficulty)
- Intent type validation

### 3. Configuration (`AIM/src/aim/config/`)

**Settings** (`settings.py`):
- Environment variable management
- API key validation
- Cost control parameters
- Rate limiting configuration
- Cache TTL settings

### 4. Testing (`AIM/tests/`)

**Test Coverage:**
- `test_base.py` - Base client resilience patterns (9 tests)
- `test_semrush.py` - SEMrush client functionality (9 tests)
- `test_ahrefs.py` - Ahrefs client functionality (9 tests)
- `keyword_data.py` - Mock data fixtures

**All 27 tests passing ✅**

### 5. Dependencies Added

```
httpx>=0.27.0,<0.28.0           # HTTP client
pybreaker>=1.0.0,<2.0.0         # Circuit breaker
tenacity>=8.2.0,<9.0.0          # Retry logic
aiolimiter>=1.1.0,<2.0.0        # Rate limiting
aiocache[redis]>=0.12.0,<0.13.0 # Caching
prometheus-client>=0.20.0       # Metrics
structlog>=24.1.0               # Logging
```

### Environment Variables

Add to `.env`:
```bash
# Keyword Research API Keys
SEMRUSH_API_KEY=your_semrush_key_here
AHREFS_API_KEY=your_ahrefs_key_here  # Optional fallback

# Budget and Limits
MAX_COST_USD=5.0                     # Max cost per request
MIN_KEYWORDS=100                     # Min keywords to return
MIN_VOLUME=10                        # Min search volume filter

# Caching and Rate Limiting
CACHE_TTL=3600                       # Cache TTL in seconds
RATE_LIMIT_CAPACITY=10               # Rate limiter capacity
RATE_LIMIT_REFILL=1.0                # Requests per second
```

### Cost Analysis

**Per Analysis:**
- SEMrush: $0.01 per API call
- Typical analysis: 1-5 calls = $0.01-$0.05
- Budget guard prevents overruns
- Cache reduces repeat costs

**Example:**
- 100 keywords, min volume 10: ~$0.04
- 500 keywords, min volume 50: ~$0.20
- Max budget $5.00 = up to 500 API calls

### Usage Example

```python
from AIM.src.aim.config.settings import get_api_settings
from AIM.src.aim.subagents.api_clients.semrush import SEMrushClient

# Load settings
settings = get_api_settings()

# Create client
client = SEMrushClient(
    api_key=settings.semrush_api_key,
    rate_limit_capacity=settings.rate_limit_capacity,
    rate_limit_refill=settings.rate_limit_refill,
)

# Expand keywords
keywords = await client.expand_keywords(
    seed_keyword="dental implants",
    max_keywords=100,
    min_volume=10,
    max_cost_usd=5.0,
)

# Close client
await client.close()
```

### Testing Commands

```bash
# Run all tests
pytest AIM/tests/subagents/api_clients/ -v

# Run specific test file
pytest AIM/tests/subagents/api_clients/test_semrush.py -v

# Run with coverage
pytest AIM/tests/subagents/api_clients/ --cov=AIM/src/aim/subagents/api_clients

# Run single test
pytest AIM/tests/subagents/api_clients/test_base.py::test_circuit_breaker_opens_after_failures -v
```

### Files Changed (15 files, 2,040+ lines)

**New Files:**
- `AIM/src/aim/subagents/api_clients/__init__.py`
- `AIM/src/aim/subagents/api_clients/base.py` (350 lines)
- `AIM/src/aim/subagents/api_clients/semrush.py` (280 lines)
- `AIM/src/aim/subagents/api_clients/ahrefs.py` (250 lines)
- `AIM/src/aim/subagents/schemas/__init__.py`
- `AIM/src/aim/subagents/schemas/api_responses.py` (200 lines)
- `AIM/tests/fixtures/__init__.py`
- `AIM/tests/fixtures/keyword_data.py` (150 lines)
- `AIM/tests/subagents/api_clients/__init__.py`
- `AIM/tests/subagents/api_clients/test_base.py` (280 lines)
- `AIM/tests/subagents/api_clients/test_semrush.py` (250 lines)
- `AIM/tests/subagents/api_clients/test_ahrefs.py` (250 lines)

**Modified Files:**
- `AIM/src/aim/config/settings.py` (added APISettings)
- `AIM/.env.example` (added API keys)
- `requirements.txt` (added 7 dependencies)

### Next Steps

**Sprint 2: Keyword Research Agent - Analysis Layer**
- Implement keyword analyzer
- Add clustering and grouping
- Intent classification
- Priority scoring
- Competitive analysis

---

## Current Status

**Sprint 1 - COMPLETED ✅** (2026-05-11)
- API clients layer with resilience patterns
- Data validation and schemas
- Configuration management
- 27 tests passing
- Budget control implemented

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

<!-- updated-by-sprint-1:2026-05-11 -->

## Teacher Agent - КРИТИЧЕСКОЕ ПРАВИЛО

**ЗАПРЕЩЕНО:**
- ❌ Copy-paste одинаковых паттернов во все субагенты
- ❌ "Обучение" без deep research для каждого субагента
- ❌ Общие решения (Circuit Breaker, Retry, Rate Limiting) для всех
- ❌ Пропускать GitHub search специализированных решений
- ❌ Не анализировать код из найденных репо

**ОБЯЗАТЕЛЬНО:**
- ✅ Для КАЖДОГО субагента: индивидуальное deep research
- ✅ GitHub search с правильными запросами (например: "yandex direct api python" для Ads)
- ✅ Клонирование и изучение кода из топовых репо
- ✅ Извлечение специфичных для домена паттернов
- ✅ Каждый субагент получает уникальное обучение

**Пример правильного подхода:**

**Ads субагент:**
1. Deep research: "yandex direct api python", "yandex ads mcp"
2. Найти: yandex-ads-mcp (https://github.com/Yurich-ru/yandex-ads-mcp)
3. Клонировать и изучить код
4. Извлечь специфичные паттерны для Яндекс.Директ
5. Адаптировать под наш Ads субагент

**SEO субагент:**
1. Deep research: "python seo tools", "serp api python"
2. Найти специализированные SEO библиотеки
3. Изучить их архитектуру
4. Извлечь SEO-specific паттерны
5. Адаптировать под наш SEO субагент

**Content субагент:**
1. Deep research: "content generation python", "ai content writer"
2. Найти content generation решения
3. Изучить их подход
4. Извлечь content-specific паттерны
5. Адаптировать под наш Content субагент

**Правило:** Каждый субагент — это отдельное исследование, отдельные решения, отдельное обучение.


## Russian Market Adaptation Rule

**КРИТИЧЕСКИ ВАЖНО:** AIM работает на российском рынке. Западные сервисы и практики нужно адаптировать под российскую юрисдикцию.

**Правило:** Берём лучшие технические решения с Запада, но адаптируем под российский рынок и законодательство.

### Что НЕ применяется в России:

**Compliance & Legal:**
- ❌ HIPAA (США) - не применяется в РФ
- ❌ GDPR (ЕС) - частично применяется, но не критично
- ❌ FDA regulations (США) - не применяется в РФ
- ⚠️ Вместо: ФЗ-152 "О персональных данных", ФЗ-323 "Об охране здоровья"

**Payment Processors:**
- ❌ Stripe - не работает в РФ
- ❌ Helcim - не работает в РФ
- ❌ Authorize.net - не работает в РФ
- ⚠️ Вместо: ЮKassa (Яндекс), CloudPayments, Тинькoff Acquiring, Сбербанк Acquiring

**Document Signing:**
- ❌ DocuSign - работает, но дорого и не популярно в РФ
- ⚠️ Вместо: Контур.Диадок, СБИС, Такском (российские ЭЦП)

**Email Services:**
- ✅ SendGrid - работает в РФ (уже используем в Phase 9)
- ✅ Mailgun - работает в РФ
- ⚠️ Альтернативы: UniSender (российский), SendPulse (российский)

### Что применяется (технические решения):

**Архитектурные паттерны (берём с Запада):**
- ✅ AI Lead Scoring (30+ факторов)
- ✅ Automated Onboarding (AI document processing)
- ✅ Conversion-optimized Landing Pages
- ✅ Real-time Analytics
- ✅ Multi-tenant Architecture
- ✅ Event-driven Architecture
- ✅ Circuit Breaker, Retry, Rate Limiting

**Технологии (берём с Запада):**
- ✅ Next.js, React, TypeScript
- ✅ FastAPI, Python, PostgreSQL
- ✅ Redis, Docker, Kubernetes
- ✅ OpenAI, Claude, Gemini
- ✅ Prometheus, Grafana

### Стратегия адаптации:

**Для каждого западного решения:**

1. **Анализ:**
   - Что делает сервис/практика?
   - Какую проблему решает?
   - Какие технические паттерны использует?

2. **Адаптация:**
   - Применимо ли в РФ юридически?
   - Есть ли российские аналоги?
   - Можно ли реализовать самостоятельно?

3. **Решение:**
   - ✅ Применяется как есть (технические паттерны)
   - ⚠️ Заменяется российским аналогом (сервисы)
   - 🔧 Реализуется самостоятельно (если нет аналога)
   - ⏸️ Откладывается (если не критично)

### Примеры адаптации:

**Phase 11: Client Acquisition**

**Западное решение:**
- Helcim (payment) + DocuSign (signatures) + HIPAA compliance

**Российская адаптация:**
- ЮKassa/CloudPayments (payment) + Контур.Диадок (signatures) + ФЗ-152 compliance
- Или: Заглушка на первом этапе, реализация позже

**Технические паттерны (берём без изменений):**
- AI Lead Scoring (30+ факторов) ✅
- Automated Onboarding (AI OCR + NLP) ✅
- Landing Page optimization ✅
- Email automation workflows ✅

### Для Teacher Agent и Исследователей:

**При исследовании западных практик:**

1. **Изучай технические решения** (архитектура, алгоритмы, паттерны)
   - Это универсально и применимо везде

2. **Адаптируй сервисы** (payment, legal, compliance)
   - Ищи российские аналоги
   - Или реализуй самостоятельно

3. **Замешивай российские практики:**
   - Яндекс.Директ вместо Google Ads (частично)
   - Яндекс.Метрика вместо Google Analytics (частично)
   - ВКонтакте, Telegram вместо Facebook, Twitter
   - Российские законы (ФЗ-152, ФЗ-323) вместо HIPAA/GDPR

4. **Бери лучшее с Запада:**
   - Технические паттерны (AI, ML, архитектура)
   - Open-source библиотеки
   - Best practices (тестирование, CI/CD, мониторинг)

### Приоритеты:

**Высокий приоритет (делаем сейчас):**
- ✅ Технические паттерны с Запада
- ✅ Open-source решения
- ✅ Архитектурные best practices

**Средний приоритет (делаем позже):**
- ⚠️ Российские payment processors (ЮKassa, CloudPayments)
- ⚠️ Российские ЭЦП (Контур.Диадок)
- ⚠️ ФЗ-152 compliance

**Низкий приоритет (можно пропустить):**
- ⏸️ HIPAA compliance (не применяется в РФ)
- ⏸️ FDA regulations (не применяется в РФ)
- ⏸️ Западные сервисы, не работающие в РФ

### Заглушки (Stubs):

**Когда западный сервис не применим:**

1. **Создай заглушку** (stub/mock)
2. **Документируй** что нужно заменить
3. **Продолжай разработку** остальных компонентов
4. **Вернись позже** для замены на российский аналог

**Пример (Phase 11):**

```python
# AIM/src/aim/services/payment/helcim_client.py (STUB)
class HelcimClient:
    """
    STUB: Helcim не работает в РФ.
    TODO: Заменить на ЮKassa или CloudPayments.
    
    Пока возвращаем mock данные для разработки.
    """
    async def process_payment(self, amount: float) -> PaymentResult:
        # Mock implementation
        return PaymentResult(
            success=True,
            transaction_id="STUB-" + str(uuid.uuid4()),
            amount=amount,
        )
```

### Итого:

**Берём с Запада:**
- ✅ Технические решения (AI, архитектура, паттерны)
- ✅ Open-source библиотеки
- ✅ Best practices

**Адаптируем под РФ:**
- ⚠️ Сервисы (payment, legal, compliance)
- ⚠️ Законодательство (ФЗ-152 вместо HIPAA)
- ⚠️ Платформы (Яндекс, VK вместо Google, Facebook)

**Пропускаем:**
- ⏸️ Западные compliance требования (HIPAA, FDA)
- ⏸️ Сервисы, не работающие в РФ (Stripe, Helcim)

**Правило:** Лучшая техника с Запада + российские реалии = конкурентное преимущество.

