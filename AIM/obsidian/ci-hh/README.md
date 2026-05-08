# HH Agent - HeadHunter Competitive Intelligence

**Статус:** ✅ Структура создана, ⏳ Требуется OAuth или Playwright

## Описание

HH Agent — микроагент для конкурентной разведки через HeadHunter API.
Отслеживает вакансии конкурентов для анализа их стратегий найма.

## Что отслеживаем

1. **Открытые вакансии** — какие позиции ищут (направления развития)
2. **Требования** — технологии, навыки, опыт
3. **Зарплаты** — рыночные ставки
4. **География** — экспансия в регионы
5. **Динамика** — новые/закрытые вакансии

## Архитектура

```
HH Agent
├── Monitor — сбор снимков вакансий
├── Analyze — анализ отдельных вакансий
├── Detect Changes — выявление изменений
└── Generate Report — еженедельные отчёты
```

## Vault Structure (LLM Wiki Pattern)

```
obsidian/ci-hh/
├── raw/
│   └── snapshots/           # Снимки вакансий по датам
│       └── YYYY-MM-DD/
│           └── {employer_id}.json
├── wiki/
│   ├── index.md            # Каталог страниц
│   ├── log.md              # Хронология операций
│   ├── competitors/        # Профили конкурентов
│   ├── vacancies/          # Анализ вакансий
│   ├── technologies/       # Тренды технологий
│   ├── strategies/         # Стратегии конкурентов
│   ├── insights/           # Отчёты
│   └── alerts/             # Изменения
└── decisions/              # Рекомендации
```

## Текущий статус

### ✅ Реализовано

- Структура агента (наследует от `Agent`)
- Vault с LLM Wiki паттерном
- Методы для мониторинга, анализа, детекции изменений
- Генерация отчётов
- Тестовый скрипт

### ⏳ Требуется

**Проблема:** HH API возвращает 403 Forbidden без OAuth токена

**Решения:**

1. **OAuth Application Token** (рекомендуется)
   - Зарегистрировать приложение на https://dev.hh.ru
   - Получить токен
   - Обновить агента для работы с токеном

2. **Playwright Web Scraping** (альтернатива)
   - Использовать MCP Playwright tools
   - Парсить публичные страницы hh.ru
   - Обход OAuth через браузер

3. **Mock Data** (для тестирования)
   - Создать тестовые данные
   - Проверить логику агента
   - Заменить на реальные данные позже

## Использование

### С OAuth (когда будет токен)

```python
from aim.agents.ci_swarm.hh_agent import HHAgent, Competitor

competitors = [
    Competitor(
        employer_id="1740",
        name="Яндекс",
        industry="IT",
    ),
]

agent = HHAgent(
    agent_id="hh-agent-001",
    database_url="sqlite+aiosqlite:///./data/aim.db",
    vault_path="./obsidian/ci-hh",
    competitors=competitors,
)

# Monitor competitors
task = Task(
    task_id="task-001",
    subtask_id="subtask-001",
    parent_task_id="parent-001",
    action="monitor_competitors",
    description="Collect vacancy snapshots",
    priority=1,
    status=TaskStatus.RECEIVED,
    created_at=datetime.now(),
    received_at=datetime.now(),
)

result = await agent.execute_task(task)
```

### С Playwright (альтернатива)

```python
from aim.agents.ci_swarm.hh_agent_playwright import HHAgentPlaywright

agent = HHAgentPlaywright(
    agent_id="hh-agent-pw-001",
    database_url="sqlite+aiosqlite:///./data/aim.db",
    vault_path="./obsidian/ci-hh",
    competitors=competitors,
)

# Same API as OAuth version
```

## Capabilities

- `monitor_competitors` — собрать снимки вакансий всех конкурентов
- `analyze_vacancy` — проанализировать отдельную вакансию
- `detect_changes` — выявить изменения между снимками
- `generate_report` — создать еженедельный отчёт

## Интеграция с Operator

HH Agent работает через Event Bus:

```python
# Operator delegates task
await operator.delegate_to_agent(
    agent_id="hh-agent-001",
    task=Task(action="monitor_competitors", ...)
)

# Agent executes and reports back
result = await agent.execute_task(task)
await agent.report_result(result)
```

## Следующие шаги

1. ✅ Создать структуру агента
2. ✅ Реализовать базовый функционал
3. ✅ Создать vault с LLM Wiki
4. ⏳ Получить OAuth токен от HH
5. ⏳ Обновить агента для работы с токеном
6. ⏳ Или реализовать Playwright версию
7. ⏳ Интегрировать с Operator
8. ⏳ Создать CI Magister (координатор)
9. ⏳ Добавить другие микроагенты (Web, Social, News)

## Файлы

- `hh_agent.py` — основной агент (OAuth версия)
- `hh_agent_playwright.py` — альтернатива с Playwright
- `test_hh_agent.py` — тестовый скрипт
- `SCHEMA.md` — структура vault
- `HH_API_AUTH.md` — документация по авторизации

---

**Создано:** 2026-05-04T19:26:00+03:00  
**Статус:** Структура готова, требуется OAuth или Playwright
