# Архитектурные паттерны коммуникации AIM

**Дата создания:** 2026-05-09  
**Цель:** Задокументировать стандартные паттерны взаимодействия между компонентами системы

---

## 🏗️ ИЕРАРХИЯ СИСТЕМЫ

```
USER (Human)
    ↓
ARCHITECT (Strategy Layer)
    ↓
OPERATOR (Tactical Layer)
    ↓
MAGISTERS (Domain Layer)
    ↓
ORCHESTRATORS (Coordination Layer)
    ↓
SUBAGENTS (Execution Layer)
```

---

## 🔄 ПАТТЕРНЫ КОММУНИКАЦИИ

### 1. Magister → Subagent (через Event Bus)

**Формат запроса:**
```json
{
  "event_type": "{domain}.{action}.requested",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "{subagent-name}",
  "payload": {
    // специфичные данные задачи
  }
}
```

**Формат ответа:**
```json
{
  "event_type": "{domain}.{action}.completed",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "{subagent-name}",
  "payload": {
    "status": "success" | "partial" | "failed",
    "result": {
      // результаты работы
    },
    "metrics": {
      "execution_time_ms": 180000,
      // другие метрики
    },
    "errors": []
  }
}
```

**Примеры:**
- `seo.analysis.requested` → `seo.analysis.completed`
- `content.generation.requested` → `content.generation.completed`
- `data_collection.requested` → `data_collection.completed`

---

### 2. Orchestrator → Subagents (параллельная координация)

**Стратегии выполнения:**

**Parallel (параллельно):**
- Все Subagents запускаются одновременно
- Результаты собираются по мере завершения
- Используется для независимых задач

**Sequential (последовательно):**
- Subagents запускаются по очереди
- Следующий ждёт завершения предыдущего
- Используется для зависимых задач

**Hybrid (гибридно):**
- Фазы выполняются последовательно
- Внутри фазы Subagents работают параллельно
- Используется для сложных workflow

**Пример (SEO Orchestrator):**
```json
{
  "strategy": "parallel",
  "subagents": [
    {
      "subagent_id": "technical-seo",
      "priority": 1
    },
    {
      "subagent_id": "content-seo",
      "priority": 1
    },
    {
      "subagent_id": "links-seo",
      "priority": 1
    }
  ]
}
```

---

### 3. Эскалация ошибок (вверх по иерархии)

**Путь эскалации:**
```
Subagent → Orchestrator → Magister → Operator → User → Architect
```

**Формат события эскалации:**
```json
{
  "event_type": "escalation.required",
  "correlation_id": "uuid",
  "source": "{subagent-id}",
  "severity": "warning" | "critical",
  "payload": {
    "error_type": "API_UNAVAILABLE",
    "message": "Source unavailable for 3 consecutive days",
    "context": {
      // дополнительный контекст
    },
    "escalation_path": ["Magister", "Operator", "User", "Architect"]
  }
}
```

**Когда эскалировать:**
- Critical errors (блокируют работу системы)
- Длительная недоступность источников (3+ дня)
- Высокое отклонение данных (>10%)
- Некорректные данные (отрицательные метрики)

---

## 💾 ХРАНЕНИЕ ДАННЫХ

### База данных (структурированные данные)

**Что хранить:**
- Метрики и числовые данные
- Результаты выполнения задач
- История событий (дублирование Event Store)
- Конфигурация агентов

**Структура таблиц:**
```sql
-- Пример для Data Collector
CREATE TABLE collected_metrics (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    date DATE NOT NULL,
    project_id TEXT,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_source_date (source, date),
    INDEX idx_project_date (project_id, date)
);
```

---

### Obsidian vault (неструктурированные знания)

**Структура (LLM Wiki Pattern):**
```
obsidian/{magister-name}/
├── raw/                    # Слой 1: Источники (immutable)
│   └── {source}/
│       └── YYYY-MM-DD.md
├── wiki/                   # Слой 2: Структурированное знание
│   ├── index.md           # Каталог всех страниц
│   ├── log.md             # Хронология операций
│   ├── concepts/          # Концепции и паттерны
│   ├── technologies/      # Технологии и инструменты
│   ├── strategies/        # Стратегии и методы
│   ├── agents/            # Агенты системы
│   ├── workflows/         # Процессы и workflow
│   ├── projects/          # Проекты
│   ├── sources/           # Обработанные источники
│   └── connections/       # Связи и синтезы
├── decisions/             # Слой 3: Стратегические решения
└── SCHEMA.md             # Правила и конвенции
```

**Формат файла в raw/:**
```markdown
---
source: ga
date: 2026-05-09
metrics_count: 15
collected_at: 2026-05-09T02:35:45Z
status: processed
output: wiki/sources/ga-2026-05-09.md
---

# Google Analytics - 2026-05-09

## Метрики

- Sessions: 1000
- Users: 800
- Bounce Rate: 45%
...
```

**Формат log.md:**
```markdown
## [2026-05-09 02:35] data_collection | Collected 120 metrics from 8 sources
## [2026-05-09 14:20] data_reconciliation | Averaged data, deviation 3.2%
## [2026-05-09 15:45] anomaly_detected | Sessions dropped 50% (warning)
```

---

## 🔧 ОБРАБОТКА ОШИБОК

### Стандартные типы ошибок:

**INVALID_INPUT:**
- Причина: Пустые обязательные параметры, неверный формат
- Действие: Вернуть failure сразу
- Retry: Нет

**API_ERROR:**
- Причина: Временная недоступность API
- Действие: Retry с exponential backoff
- Retry: 10 попыток, 1 минута интервал

**TIMEOUT:**
- Причина: Превышено максимальное время выполнения
- Действие: Вернуть partial_success с собранными данными
- Retry: Нет

**INTERNAL_ERROR:**
- Причина: Внутренняя ошибка агента
- Действие: Логировать, вернуть failure, эскалировать
- Retry: Нет

### Retry механизм (стандартный):

```python
async def retry_with_backoff(func, max_retries=10, base_delay=60):
    """
    Retry функции с exponential backoff
    
    Args:
        func: Async функция для retry
        max_retries: Максимум попыток (default: 10)
        base_delay: Базовая задержка в секундах (default: 60)
    """
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)  # exponential backoff
            await asyncio.sleep(delay)
```

### Graceful degradation:

**При частичном сбое:**
1. Выполнить максимум возможного
2. Вернуть partial_success
3. Указать, что не удалось выполнить
4. Уведомить Magister

**При критичной ошибке:**
1. Вернуть failure
2. Эскалировать вверх по иерархии
3. Сохранить частичные данные (если есть)

---

## 🧠 ОБУЧЕНИЕ И АДАПТАЦИЯ

### Интеграция с Teacher Agent:

**Что Teacher Agent предоставляет:**
- Обновлённые best practices
- Новые API интеграции
- Изменения в форматах данных
- Улучшенные промпты и алгоритмы

**Как Subagent обучается:**
1. Teacher Agent читает историю из Obsidian
2. Анализирует успешные/неудачные кейсы
3. Создаёт обновлённые инструкции
4. Subagent применяет новые инструкции
5. Тестирует на контрольной выборке
6. Сохраняет результаты в Obsidian

**Частота обучения:**
- Периодический пересмотр: раз в квартал
- Экстренное обучение: при изменении API
- Адаптация: при падении метрик качества

---

## 📊 МЕТРИКИ (стандартные)

### Производительность:

**Success rate:**
- Целевое значение: > 95%
- Warning: < 95%
- Critical: < 90%

**Execution time:**
- Измеряется в `metrics.execution_time_ms`
- 95-й перцентиль: зависит от агента
- Максимальное время: зависит от агента

**Reliability:**
- Partial success rate: > 99%
- Failure rate: < 1%

### Качественные метрики:

Специфичны для каждого агента (определяются в спецификации)

---

## 🧪 ТЕСТИРОВАНИЕ (стандартное)

### Unit тесты:

**Покрытие:** > 80%

**Обязательные тесты:**
- Валидация входных данных
- Обработка ошибок API
- Retry механизм
- Сохранение в БД и Obsidian
- Формирование результата

### Integration тесты:

**Обязательные сценарии:**
- Получение задачи через Event Bus
- Отправка результата через Event Bus
- Логирование в Event Store
- Сохранение в Obsidian vault
- Сохранение в базу данных
- Эскалация при критичных ошибках

### E2E тесты:

**Обязательные сценарии:**
- Полный цикл: задача → выполнение → результат
- Частичный сбой (graceful degradation)
- Критичная ошибка (escalation)
- Retry механизм при временных сбоях

---

## 🚀 DEPLOYMENT (стандартное)

### Требования:

**Окружение:**
- Python 3.11+
- Event Bus доступен
- Event Store доступен
- Obsidian vault доступен
- Database доступна

**Зависимости:**
```txt
httpx >= 0.24.0          # API запросы
pydantic >= 2.0.0        # Валидация данных
sqlalchemy >= 2.0.0      # База данных
python-frontmatter >= 1.0.0  # Obsidian frontmatter
```

**Конфигурация (.env):**
```env
SUBAGENT_ID={subagent-name}
EVENT_BUS_URL=...
EVENT_STORE_URL=...
OBSIDIAN_VAULT_PATH=./obsidian/{magister-name}
DATABASE_URL=sqlite+aiosqlite:///./data/aim.db

# API keys (специфичные для агента)
```

### Мониторинг:

**Метрики для алертов:**
- Success rate < 95% → Warning
- Success rate < 90% → Critical
- Execution time > threshold → Warning
- Специфичные метрики агента

**Дашборд метрик:**
- Количество выполнений в день
- Процент success / partial / failed
- Среднее время выполнения
- Топ-10 ошибок

---

## 📝 ЛОГИРОВАНИЕ (стандартное)

### Event Store (обязательно):
- Все входящие события `*.requested`
- Все исходящие события `*.completed`
- Все эскалации `escalation.required`
- Correlation ID для трейсинга

### Obsidian vault (обязательно):
- История операций (`wiki/log.md`)
- Результаты работы (`wiki/sources/`, `wiki/concepts/`)
- Метрики производительности (`wiki/metrics/`)

### Системные логи (опционально):
- Debug информация
- Ошибки и warnings
- Performance traces

**Формат:**
```
[YYYY-MM-DD HH:MM:SS] [LEVEL] [subagent-id] [correlation_id] Message
```

---

## 🔒 ПРАВИЛА

### Mock данные:
- ❌ НИКОГДА не использовать mock данные в production коде
- ✅ Всегда запрашивать реальные данные у пользователя или из источников
- ✅ Mock данные только в unit тестах

### Качество vs Скорость:
- ✅ Качество важнее скорости
- ✅ Глубокий анализ важнее быстрого результата
- ✅ Время работы агента не критично (1 минута vs 1 час vs 1 день)

### Complete Before Next:
- ✅ Доводим каждый компонент до 100%
- ✅ Никаких "доделаем потом"
- ✅ Переход к следующему только после завершения текущего

---

**Дата создания:** 2026-05-09 20:30 GMT+3  
**Автор:** Mikhail Eliseev (via meAI Architect)  
**Статус:** Ready  
**Применение:** Все Subagents, Orchestrators, Magisters
