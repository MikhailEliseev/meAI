# Data Collector Agent - Спецификация

**Дата:** 2026-05-09  
**Magister:** Analytics Magister  
**Приоритет:** P0 (Критичный)  
**Статус:** Ready

---

## 🎯 РОЛЬ И НАЗНАЧЕНИЕ

### Основная роль:
Data Collector Agent собирает метрики со всех источников данных ежедневно, чтобы обеспечить data-driven подход агентства. Без актуальных данных невозможно принимать обоснованные решения.

### Что делает:
- ✅ Собирает метрики из 8 источников ежедневно (GA, Metrica, Keys.so, Direct, VK Ads, CallTouch, Roistat, CRM)
- ✅ Запускается автоматически по расписанию (2-3 AM)
- ✅ Сохраняет raw данные в БД + Obsidian
- ✅ Уведомляет Analytics Magister о завершении сбора
- ✅ Детектирует аномалии (отклонение >50% от предыдущего дня)
- ✅ Эскалирует критичные проблемы вверх по иерархии

### Что НЕ делает:
- ❌ НЕ агрегирует данные (это делает Data Processor Agent)
- ❌ НЕ валидирует данные (это делает Data Reconciliation Agent)
- ❌ НЕ анализирует данные (это делает Analytics Magister)
- ❌ НЕ использует mock данные (НИКОГДА!)

### Место в иерархии:
```
Analytics Magister
    ↓
Data Collector Agent ← вы здесь
```

---

## 📥 ВХОДНЫЕ ДАННЫЕ

### Получает от Analytics Magister:

**Формат события:**
```json
{
  "event_type": "data_collection.requested",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "data-collector",
  "payload": {
    "collection_type": "daily|monthly|on_demand",
    "date_range": {
      "start": "2026-05-08",
      "end": "2026-05-09"
    },
    "sources": ["ga", "metrica", "keys_so", "direct", "vk_ads", "calltouch", "roistat", "crm"],
    "project_id": "uuid"
  }
}
```

**Обязательные параметры:**
- `collection_type` (string) - Тип сбора (daily, monthly, on_demand)
- `date_range` (object) - Диапазон дат для сбора
- `sources` (array) - Список источников для сбора

**Опциональные параметры:**
- `project_id` (string) - ID проекта (если сбор для конкретного проекта)

---

## 📤 ВЫХОДНЫЕ ДАННЫЕ

### Отправляет Analytics Magister:

**Формат события:**
```json
{
  "event_type": "data_collection.completed",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "data-collector",
  "payload": {
    "status": "success" | "partial" | "failed",
    "result": {
      "collected_sources": ["ga", "metrica", "keys_so"],
      "failed_sources": ["direct"],
      "data_summary": {
        "ga": {
          "metrics_count": 15,
          "date_range": "2026-05-08 to 2026-05-09",
          "storage_path": "obsidian/analytics-magister/raw/ga/2026-05-09.md"
        }
      },
      "anomalies": [
        {
          "source": "ga",
          "metric": "sessions",
          "current_value": 500,
          "previous_value": 1000,
          "deviation_percent": -50,
          "severity": "warning"
        }
      ]
    },
    "metrics": {
      "execution_time_ms": 180000,
      "sources_attempted": 8,
      "sources_succeeded": 7,
      "sources_failed": 1,
      "total_metrics_collected": 120
    },
    "errors": [
      {
        "source": "direct",
        "error_type": "API_UNAVAILABLE",
        "message": "Connection timeout after 10 retries",
        "retry_count": 10
      }
    ]
  }
}
```

**Структура результата:**
- `collected_sources` (array) - Успешно собранные источники
- `failed_sources` (array) - Источники с ошибками
- `data_summary` (object) - Краткая информация по каждому источнику
- `anomalies` (array) - Обнаруженные аномалии (отклонение >50%)

**Метрики:**
- `execution_time_ms` - Время выполнения (обычно 3-5 минут)
- `sources_attempted` - Количество попыток сбора
- `sources_succeeded` - Успешные сборы
- `sources_failed` - Неудачные сборы

---

## 🔄 АЛГОРИТМ РАБОТЫ

### Шаг 1: Получение задачи
1. Подписаться на события `data_collection.requested`
2. Фильтровать по `subagent_id == "data-collector"`
3. Валидировать входные параметры (collection_type, date_range, sources)

### Шаг 2: Сбор данных из источников
1. Для каждого источника из списка:
   - Подключиться к API источника
   - Запросить метрики за указанный период
   - Применить retry механизм при временных сбоях (10 попыток, 1 минута интервал)
   - Сохранить raw данные без обработки
2. Параллельный сбор из всех источников (async)
3. Timeout для каждого источника: 5 минут

### Шаг 3: Детекция аномалий
1. Для каждой метрики:
   - Сравнить с предыдущим днём
   - Если отклонение >50% → добавить в список аномалий
   - Severity: warning (50-80%), critical (>80%)
2. Аномалии сохраняются в результат, но НЕ блокируют сбор

### Шаг 4: Сохранение данных
1. **В базу данных:**
   - Таблица: `collected_metrics`
   - Поля: `source`, `metric_name`, `metric_value`, `date`, `project_id`, `collected_at`
   - Индексы: `(source, date)`, `(project_id, date)`
2. **В Obsidian vault:**
   - Путь: `obsidian/analytics-magister/raw/{source}/YYYY-MM-DD.md`
   - Формат: Markdown с frontmatter
   - Frontmatter: `source`, `date`, `metrics_count`, `collected_at`

### Шаг 5: Обработка ошибок
1. **Отсутствие данных:**
   - Если источник недоступен 3 дня подряд → critical anomaly
   - Эскалация: Analytics Magister → Operator → User → Architect
2. **Некорректные данные:**
   - Отрицательные метрики, нулевые значения (где невозможны)
   - Уведомление вверх по иерархии
   - Данные НЕ сохраняются
3. **Частичные сбои:**
   - 7 из 8 источников доступны → status: "partial"
   - Уведомление Analytics Magister
   - Сбор продолжается для доступных источников

### Шаг 6: Отправка результата
1. Отправить событие `data_collection.completed` через Event Bus
2. Логировать в Event Store с correlation_id
3. Если `status: "failed"` → эскалировать Operator (событие `escalation.required`)

---

## 🔧 ИНТЕГРАЦИИ

### Внешние сервисы:

**Google Analytics 4:**
- API endpoint: `https://analyticsdata.googleapis.com/v1beta`
- Аутентификация: OAuth 2.0
- Rate limit: 10 requests/second
- Документация: https://developers.google.com/analytics/devguides/reporting/data/v1

**Яндекс Метрика:**
- API endpoint: `https://api-metrika.yandex.net/stat/v1/data`
- Аутентификация: OAuth token
- Rate limit: 10 requests/second
- Документация: https://yandex.ru/dev/metrika/doc/api2/api_v1/intro.html

**Keys.so:**
- API endpoint: `https://api.keys.so/v1`
- Аутентификация: API key
- Rate limit: 100 requests/minute
- Документация: https://keys.so/docs/api

**Яндекс Директ:**
- API endpoint: `https://api.direct.yandex.com/json/v5`
- Аутентификация: OAuth token
- Rate limit: 10 requests/second
- Документация: https://yandex.ru/dev/direct/doc/dg/concepts/about.html

**VK Ads:**
- API endpoint: `https://ads.vk.com/api/v2`
- Аутентификация: Access token
- Rate limit: 3 requests/second
- Документация: https://ads.vk.com/help/articles/api_intro

**CallTouch:**
- API endpoint: `https://api.calltouch.ru/calls-service/RestAPI`
- Аутентификация: API key
- Rate limit: 10 requests/second
- Документация: https://www.calltouch.ru/support/api/

**Roistat:**
- API endpoint: `https://cloud.roistat.com/api/v1`
- Аутентификация: API key
- Rate limit: 10 requests/second
- Документация: https://help.roistat.com/articles/integration/api/

**CRM (amoCRM):**
- API endpoint: `https://{subdomain}.amocrm.ru/api/v4`
- Аутентификация: OAuth 2.0
- Rate limit: 7 requests/second
- Документация: https://www.amocrm.ru/developers/content/crm_platform/

### Внутренние зависимости:

- Event Bus (обязательно) - получение задач, отправка результатов
- Event Store (обязательно) - логирование всех сборов
- Obsidian vault (обязательно) - сохранение raw данных
- Database (обязательно) - хранение метрик
- Teacher Agent (опционально) - обучение и обновление API интеграций
- Analytics Magister (обязательно) - координация сбора данных

---

## 📊 МЕТРИКИ УСПЕХА

### Качественные метрики:

**Полнота сбора:**
- Метрика: Процент успешно собранных источников
- Целевое значение: 95-99% (идеально 100%)
- Как измерять: `sources_succeeded / sources_attempted`

**Доступность источников:**
- Метрика: Процент времени, когда источник доступен
- Целевое значение: >90% для каждого источника
- Как измерять: Мониторинг за 30 дней

### Производительность:

**Скорость:**
- Среднее время выполнения: 3-5 минут (для всех 8 источников)
- 95-й перцентиль: < 10 минут
- Максимальное время: < 15 минут

**Надёжность:**
- Success rate: > 95%
- Partial success rate: > 99%
- Failure rate: < 1%

### Бизнес-метрики:

**Актуальность данных:**
- Данные собираются ежедневно в 2-3 AM
- Доступны для анализа к 9 AM
- Задержка: < 7 часов

**Детекция аномалий:**
- Процент обнаруженных аномалий: измеряется
- False positive rate: < 10%
- False negative rate: < 5%

---

## 🧪 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ

### Пример 1: Успешный ежедневный сбор

**Входные данные:**
```json
{
  "collection_type": "daily",
  "date_range": {
    "start": "2026-05-08",
    "end": "2026-05-09"
  },
  "sources": ["ga", "metrica", "keys_so", "direct", "vk_ads", "calltouch", "roistat", "crm"]
}
```

**Выходные данные:**
```json
{
  "status": "success",
  "result": {
    "collected_sources": ["ga", "metrica", "keys_so", "direct", "vk_ads", "calltouch", "roistat", "crm"],
    "failed_sources": [],
    "data_summary": {
      "ga": {
        "metrics_count": 15,
        "date_range": "2026-05-08 to 2026-05-09",
        "storage_path": "obsidian/analytics-magister/raw/ga/2026-05-09.md"
      }
    },
    "anomalies": []
  },
  "metrics": {
    "execution_time_ms": 180000,
    "sources_attempted": 8,
    "sources_succeeded": 8,
    "sources_failed": 0,
    "total_metrics_collected": 120
  }
}
```

### Пример 2: Частичный сбор с аномалией

**Входные данные:**
```json
{
  "collection_type": "daily",
  "date_range": {
    "start": "2026-05-08",
    "end": "2026-05-09"
  },
  "sources": ["ga", "metrica", "keys_so", "direct"]
}
```

**Выходные данные:**
```json
{
  "status": "partial",
  "result": {
    "collected_sources": ["ga", "metrica", "keys_so"],
    "failed_sources": ["direct"],
    "data_summary": {
      "ga": {
        "metrics_count": 15,
        "date_range": "2026-05-08 to 2026-05-09",
        "storage_path": "obsidian/analytics-magister/raw/ga/2026-05-09.md"
      }
    },
    "anomalies": [
      {
        "source": "ga",
        "metric": "sessions",
        "current_value": 500,
        "previous_value": 1000,
        "deviation_percent": -50,
        "severity": "warning"
      }
    ]
  },
  "metrics": {
    "execution_time_ms": 240000,
    "sources_attempted": 4,
    "sources_succeeded": 3,
    "sources_failed": 1,
    "total_metrics_collected": 45
  },
  "errors": [
    {
      "source": "direct",
      "error_type": "API_UNAVAILABLE",
      "message": "Connection timeout after 10 retries",
      "retry_count": 10
    }
  ]
}
```

### Пример 3: Критичная аномалия (источник недоступен 3 дня)

**Выходные данные:**
```json
{
  "status": "partial",
  "result": {
    "collected_sources": ["ga", "metrica", "keys_so", "vk_ads", "calltouch", "roistat", "crm"],
    "failed_sources": ["direct"],
    "anomalies": [
      {
        "source": "direct",
        "metric": "availability",
        "current_value": 0,
        "days_unavailable": 3,
        "severity": "critical",
        "escalation_required": true
      }
    ]
  },
  "errors": [
    {
      "source": "direct",
      "error_type": "CRITICAL_UNAVAILABILITY",
      "message": "Source unavailable for 3 consecutive days",
      "escalation_path": ["Analytics Magister", "Operator", "User", "Architect"]
    }
  ]
}
```

---

## 🔒 ОБРАБОТКА ОШИБОК

### Типы ошибок:

**Валидация входных данных:**
- Код: `INVALID_INPUT`
- Действие: Вернуть failure сразу
- Retry: Нет
- Пример: Пустой sources, неверный date_range

**Ошибка API источника:**
- Код: `API_ERROR`
- Действие: Retry с exponential backoff (10 попыток, 1 минута интервал)
- Retry: До 10 попыток
- Fallback: Пропустить источник, продолжить сбор

**Отсутствие данных (3 дня):**
- Код: `CRITICAL_UNAVAILABILITY`
- Действие: Эскалация вверх по иерархии
- Retry: Нет
- Эскалация: Analytics Magister → Operator → User → Architect

**Некорректные данные:**
- Код: `INVALID_DATA`
- Действие: Уведомление вверх по иерархии, данные НЕ сохраняются
- Retry: Нет
- Примеры: Отрицательные метрики, нулевые значения (где невозможны)

**Timeout:**
- Код: `TIMEOUT`
- Действие: Вернуть partial_success с собранными данными
- Retry: Нет
- Максимальное время на источник: 5 минут

**Внутренняя ошибка:**
- Код: `INTERNAL_ERROR`
- Действие: Логировать, вернуть failure, эскалировать Operator
- Retry: Нет

### Graceful degradation:

При частичном сбое:
1. Собрать данные из доступных источников
2. Вернуть partial_success
3. Указать, какие источники недоступны
4. Уведомить Analytics Magister

При критичной ошибке:
1. Вернуть failure
2. Эскалировать Operator (событие `escalation.required`)
3. Сохранить частичные данные (если есть)

---

## 🧠 ОБУЧЕНИЕ И АДАПТАЦИЯ

### Источники обучения:

**От Teacher Agent:**
- Обновлённые API интеграции (новые поля, изменённые форматы)
- Документация по подключению к источникам
- Best practices сбора данных
- Новые источники данных

**Из собственного опыта:**
- Минимальное обучение (агент только собирает данные)
- Запоминание, какие источники чаще падают (для приоритизации retry)
- История аномалий в Obsidian

**Из Obsidian vault:**
- История сборов (`wiki/log.md`)
- Аномалии и паттерны (`wiki/concepts/`)
- Метрики производительности (`wiki/metrics/`)

### Адаптация:

**Когда адаптироваться:**
- Изменения в API источников (новые поля, форматы)
- Добавление новых источников данных
- Изменение расписания сбора
- Обновление списка метрик

**Как адаптироваться:**
1. Teacher Agent обучает агента:
   - Читает документацию нового API
   - Создаёт инструкции по подключению
   - Обновляет код интеграции
2. Агент применяет новые инструкции:
   - Обновляет конфигурацию источников
   - Тестирует подключение
   - Сохраняет результаты в Obsidian

### Пересмотр источников:

**Частота:** Раз в квартал

**Что пересматривать:**
- Список источников данных
- Приоритеты источников (если Keys.so стабильнее GA, менять веса?)
- Метрики для сбора
- Расписание сбора

---

## 📝 ЛОГИРОВАНИЕ

### Что логировать:

**В Event Store (обязательно):**
- Все входящие события `data_collection.requested`
- Все исходящие события `data_collection.completed`
- Все эскалации `escalation.required`
- Correlation ID для трейсинга

**В Obsidian vault (обязательно):**
- Raw данные из источников (`raw/{source}/YYYY-MM-DD.md`)
- История сборов (`wiki/log.md`)
- Аномалии (`wiki/concepts/anomalies.md`)
- Метрики производительности (`wiki/metrics/`)

**В системные логи (опционально):**
- Debug информация (запросы к API, ответы)
- Ошибки и warnings (недоступность API, timeout)
- Performance traces (время выполнения каждого шага)

### Формат логов:

```
[YYYY-MM-DD HH:MM:SS] [LEVEL] [data-collector] [correlation_id] Message
```

**Пример:**
```
[2026-05-09 02:30:15] [INFO] [data-collector] [abc-123] Received data_collection.requested for daily collection
[2026-05-09 02:30:16] [DEBUG] [data-collector] [abc-123] Collecting from 8 sources
[2026-05-09 02:35:45] [INFO] [data-collector] [abc-123] Completed collection: 8 sources, 120 metrics
[2026-05-09 02:35:46] [INFO] [data-collector] [abc-123] Sent data_collection.completed
```

---

## 🧪 ТЕСТИРОВАНИЕ

### Unit тесты:

**Покрытие:** > 80%

**Обязательные тесты:**
- Валидация входных данных (пустой sources, неверный date_range)
- Подключение к API источников (mock API)
- Retry механизм (10 попыток, 1 минута интервал)
- Детекция аномалий (отклонение >50%)
- Сохранение в БД и Obsidian
- Обработка ошибок API (timeout, unavailable)

### Integration тесты:

**Обязательные сценарии:**
- Получение задачи от Analytics Magister через Event Bus
- Отправка результата Analytics Magister через Event Bus
- Логирование в Event Store
- Сохранение в Obsidian vault
- Сохранение в базу данных
- Эскалация Operator при критичных ошибках

### E2E тесты:

**Обязательные сценарии:**
- Полный цикл: задача → сбор → сохранение → результат
- Сбор из всех 8 источников (mock API)
- Частичный сбор (7 из 8 источников доступны)
- Детекция аномалий (отклонение >50%)
- Критичная недоступность (3 дня подряд)
- Retry механизм при временных сбоях

**Тестовые кейсы:**
- Все источники доступны → success
- 7 из 8 источников доступны → partial
- Все источники недоступны → failure + escalation
- Аномалия обнаружена → warning в результате
- Критичная аномалия (3 дня) → escalation

---

## 🚀 DEPLOYMENT

### Требования:

**Окружение:**
- Python 3.11+
- Event Bus доступен
- Event Store доступен
- Obsidian vault доступен (`obsidian/analytics-magister/`)
- Database доступна

**Зависимости:**
- `httpx >= 0.24.0` (для API запросов)
- `pydantic >= 2.0.0` (для валидации данных)
- `sqlalchemy >= 2.0.0` (для работы с БД)
- `python-frontmatter >= 1.0.0` (для работы с Obsidian frontmatter)
- `schedule >= 1.2.0` (для cron-based scheduling)

**Конфигурация:**
```env
SUBAGENT_ID=data-collector
EVENT_BUS_URL=...
EVENT_STORE_URL=...
OBSIDIAN_VAULT_PATH=./obsidian/analytics-magister
DATABASE_URL=sqlite+aiosqlite:///./data/aim.db

# API keys для источников
GA_API_KEY=...
METRICA_API_KEY=...
KEYS_SO_API_KEY=...
DIRECT_API_KEY=...
VK_ADS_API_KEY=...
CALLTOUCH_API_KEY=...
ROISTAT_API_KEY=...
CRM_API_KEY=...
```

### Мониторинг:

**Метрики для алертов:**
- Success rate < 95% → Warning
- Success rate < 90% → Critical
- Source unavailable 3 days → Critical (эскалация)
- Anomaly detected (>50% deviation) → Warning
- Anomaly detected (>80% deviation) → Critical
- Execution time > 10 minutes → Warning
- Execution time > 15 minutes → Critical

**Дашборд метрик:**
- Количество сборов в день
- Процент success / partial / failed
- Среднее время сбора
- Доступность источников (за 30 дней)
- Топ-10 аномалий
- Топ-10 ошибок

### Расписание:

**Ежедневный сбор:**
- Время: 2-3 AM (ночью, когда нагрузка минимальна)
- Cron: `0 2 * * *` (каждый день в 2:00 AM)
- Источники: все 8

**Ежемесячный сбор:**
- Время: 1-е число месяца, 3 AM
- Cron: `0 3 1 * *` (1-го числа в 3:00 AM)
- Источники: все 8
- Агрегация: за весь месяц

**On-demand сбор:**
- Триггер: событие `data_collection.requested` с `collection_type: "on_demand"`
- Источники: указанные в запросе

---

## 📚 СВЯЗАННЫЕ ДОКУМЕНТЫ

### Спецификации:
- `ANALYTICS_MAGISTER_SPEC.md` - Спецификация родительского Magister (TODO)
- `DATA_RECONCILIATION_SPEC.md` - Спецификация агента валидации данных (✅ READY)
- `DATA_PROCESSOR_SPEC.md` - Спецификация агента обработки данных (TODO)
- `TEACHER_AGENT_SPEC.md` - Спецификация Teacher Agent (TODO)

### Код:
- `AIM/src/aim/subagents/analytics/data_collector.py` - Реализация (TODO)
- `AIM/tests/subagents/analytics/test_data_collector.py` - Тесты (TODO)

### Документация:
- Event Bus API
- Event Store API
- Obsidian integration guide
- Google Analytics API: https://developers.google.com/analytics/devguides/reporting/data/v1
- Яндекс Метрика API: https://yandex.ru/dev/metrika/doc/api2/api_v1/intro.html
- Keys.so API: https://keys.so/docs/api

### Obsidian Vault:
- `obsidian/analytics-magister/raw/{source}/` - Raw данные из источников
- `obsidian/analytics-magister/wiki/log.md` - Операционная история
- `obsidian/analytics-magister/wiki/concepts/anomalies.md` - Аномалии и паттерны

### Backlog:
- **TODO:** Создать Doctor Agent для мониторинга здоровья системы
  - Сигнализирует Operator и Architect о том, кто "заболел" в системе
  - Проверяет доступность всех компонентов (Magisters, Subagents, API)
  - Hourly ping для критичных компонентов

---

**Дата создания:** 2026-05-09  
**Автор:** Mikhail Eliseev (via meAI Architect)  
**Версия:** 1.0  
**Статус:** Ready

**Критичность:** ⭐⭐⭐⭐⭐ (P0 - блокирует запуск системы)  
**Причина:** Без актуальных данных невозможен data-driven подход. Все решения агентства основаны на метриках.
