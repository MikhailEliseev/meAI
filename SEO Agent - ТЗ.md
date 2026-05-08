# SEO Agent - Техническое Задание

## Общая информация

**Название:** SEO Agent (SEO Агент)  
**Тип:** Execution Layer Agent  
**Статус:** ⏳ TODO  
**Приоритет:** P1  
**Дедлайн:** 2026-05-10  
**Файл:** `src/meai/agents/seo_agent.py`

## Описание

SEO Agent — автономный агент для выполнения SEO-задач в рамках медицинского маркетингового агентства AIM. Отвечает за анализ конкурентов, подбор ключевых слов, оптимизацию контента и мониторинг позиций.

## Зависимости

- ✅ **Base Agent** — базовый класс агента
- ✅ **Event Bus** — коммуникация с другими агентами
- ⏳ **Obsidian Integration** — хранение знаний и результатов
- ✅ **Database** — сохранение метрик и задач

## Функциональные требования

### 1. Анализ конкурентов
- Сбор данных о конкурентах (домены, ключевые слова, позиции)
- Анализ контента конкурентов
- Выявление сильных и слабых сторон
- Сохранение результатов в Obsidian vault

### 2. Подбор ключевых слов
- Генерация семантического ядра
- Анализ частотности и конкуренции
- Кластеризация ключевых слов
- Приоритизация по потенциалу

### 3. Оптимизация контента
- Анализ существующего контента
- Рекомендации по улучшению (title, description, H1-H6)
- Проверка плотности ключевых слов
- SEO-аудит страниц

### 4. Мониторинг позиций
- Отслеживание позиций по ключевым словам
- Уведомления об изменениях
- Анализ динамики
- Отчеты по результатам

## Технические требования

### Класс SEOAgent

```python
from meai.agents.base_agent import Agent
from meai.events.event_bus import EventBus
from meai.memory.obsidian import ObsidianVault

class SEOAgent(Agent):
    """SEO Agent для выполнения SEO-задач"""
    
    def __init__(
        self,
        agent_id: str,
        event_bus: EventBus,
        vault: ObsidianVault,
        config: dict[str, Any]
    ):
        super().__init__(agent_id, event_bus, vault)
        self.config = config
    
    async def execute_task(self, task: Task) -> TaskResult:
        """Выполнить SEO-задачу"""
        pass
    
    def get_capabilities(self) -> list[str]:
        """Возвращает список возможностей агента"""
        return [
            "competitor_analysis",
            "keyword_research",
            "content_optimization",
            "position_monitoring"
        ]
    
    async def analyze_competitors(self, domains: list[str]) -> dict:
        """Анализ конкурентов"""
        pass
    
    async def research_keywords(self, topic: str) -> list[str]:
        """Подбор ключевых слов"""
        pass
    
    async def optimize_content(self, content: str, keywords: list[str]) -> str:
        """Оптимизация контента"""
        pass
    
    async def monitor_positions(self, keywords: list[str]) -> dict:
        """Мониторинг позиций"""
        pass
```

### Интеграция с Event Bus

```python
# Подписка на события
await event_bus.subscribe("seo.task.new", seo_agent.receive_task)

# Публикация результатов
await event_bus.publish(Event(
    type="seo.task.completed",
    data={"task_id": task.id, "result": result},
    priority=Priority.NORMAL
))
```

### Хранение в Obsidian

```
obsidian/seo-agent/
├── raw/                    # Исходные данные
│   ├── competitors/        # Данные о конкурентах
│   └── keywords/           # Списки ключевых слов
├── wiki/                   # Обработанное знание
│   ├── index.md           # Каталог
│   ├── log.md             # История операций
│   ├── concepts/          # SEO концепции
│   ├── strategies/        # SEO стратегии
│   └── sources/           # Обработанные источники
└── decisions/             # Решения по SEO
```

## Критерии приёмки

- [ ] Класс SEOAgent наследуется от Base Agent
- [ ] Реализованы все 4 основные функции
- [ ] Интеграция с Event Bus работает
- [ ] Результаты сохраняются в Obsidian vault
- [ ] Метрики записываются в базу данных
- [ ] Написаны unit-тесты (coverage > 80%)
- [ ] Написаны integration-тесты
- [ ] Документация в docstrings
- [ ] Type hints для всех методов

## Тестирование

### Unit-тесты
```python
# tests/agents/test_seo_agent.py
async def test_analyze_competitors():
    agent = SEOAgent(...)
    result = await agent.analyze_competitors(["example.com"])
    assert "keywords" in result
    assert "positions" in result
```

### Integration-тесты
```python
# tests/integration/test_seo_workflow.py
async def test_seo_task_workflow():
    # Создать задачу
    task = Task(type="seo.competitor_analysis", ...)
    
    # Отправить через Event Bus
    await event_bus.publish(Event(...))
    
    # Проверить результат
    result = await wait_for_result(task.id)
    assert result.status == "completed"
```

## Примечания

- Агент должен быть полностью автономным
- Все внешние API вызовы должны быть async
- Обработка ошибок через try/except с логированием
- Таймауты для всех внешних запросов
- Graceful degradation при недоступности сервисов

## Связанные документы

- [[Base Agent]] — базовый класс
- [[Event Bus]] — система событий
- [[Obsidian Integration]] — работа с vault
- [[SEO Magister]] — координатор SEO домена
