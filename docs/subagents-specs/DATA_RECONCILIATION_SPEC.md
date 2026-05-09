# Data Reconciliation Agent - Спецификация

**Дата:** 2026-05-09  
**Magister:** Analytics Magister  
**Приоритет:** P0 (Критичный)  
**Статус:** Ready

---

## 🎯 РОЛЬ И НАЗНАЧЕНИЕ

### Основная роль:
Data Reconciliation Agent сверяет данные из всех источников аналитики, находит истину в расхождениях и предоставляет надёжные данные для принятия решений в data-driven агентстве.

### Что делает:
- ✅ Сверяет метрики из всех источников (GA, Метрика, Keys.so, Direct API, VK Ads, CallTouch, Roistat, CRM)
- ✅ Проверяет доступность источников и адекватность данных
- ✅ Определяет допустимые отклонения (5-10%) и находит аномалии
- ✅ Усредняет данные из разных источников для получения истины
- ✅ Обнаруживает неработающие источники и аномальные данные
- ✅ Эскалирует критичные проблемы Operator

### Что НЕ делает:
- ❌ НЕ собирает данные (это делает Data Collector Agent)
- ❌ НЕ анализирует данные (это делает Analytics Magister)
- ❌ НЕ принимает бизнес-решения (это делает Analytics Magister)

### Место в иерархии:
```
Analytics Magister
    ↓
Analytics Orchestrator
    ↓
Data Reconciliation Agent ← вы здесь
```

---

## 📥 ВХОДНЫЕ ДАННЫЕ

### Получает от Analytics Orchestrator:

**Формат события:**
```json
{
  "event_type": "data_reconciliation.requested",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "data-reconciliation",
  "payload": {
    "period": {
      "start_date": "2026-05-08",
      "end_date": "2026-05-08"
    },
    "metrics": "all",
    "sources": "all",
    "deviation_threshold": 0.10,
    "trigger": "scheduled|manual"
  }
}
```

**Обязательные параметры:**
- `period` (object) - Период данных для сверки (start_date, end_date)
- `metrics` (string) - "all" или список конкретных метрик
- `sources` (string) - "all" или список конкретных источников

**Опциональные параметры:**
- `deviation_threshold` (float) - Допустимое отклонение (по умолчанию 0.10 = 10%)
- `trigger` (string) - Тип запуска (scheduled = автоматически утром, manual = по запросу)

---

## 📤 ВЫХОДНЫЕ ДАННЫЕ

### Отправляет Analytics Orchestrator:

**Формат события:**
```json
{
  "event_type": "data_reconciliation.completed",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "data-reconciliation",
  "payload": {
    "status": "success" | "partial_success" | "failure",
    "result": {
      "reconciled_data": {
        "visits": {
          "sources": {
            "google_analytics": 1000,
            "yandex_metrica": 1200,
            "keys_so": 1100
          },
          "average": 1100,
          "deviation": 0.083,
          "reliable": true
        },
        "conversions": {
          "sources": {
            "google_analytics": 50,
            "yandex_metrica": 52,
            "calltouch": 51
          },
          "average": 51,
          "deviation": 0.02,
          "reliable": true
        }
      },
      "issues": [
        {
          "type": "source_unavailable",
          "source": "roistat",
          "severity": "warning",
          "message": "Roistat API unavailable, excluded from reconciliation"
        },
        {
          "type": "high_deviation",
          "metric": "ad_spend",
          "deviation": 0.15,
          "severity": "critical",
          "message": "Ad spend deviation 15% exceeds threshold 10%"
        },
        {
          "type": "anomaly",
          "metric": "visits",
          "source": "keys_so",
          "value": 1000000,
          "expected_range": "800-1200",
          "severity": "critical",
          "message": "Keys.so shows 1M visits vs expected 1K - marked as unreliable"
        }
      ],
      "summary": {
        "total_metrics": 15,
        "reconciled": 13,
        "issues": 2,
        "sources_available": 7,
        "sources_unavailable": 1
      }
    },
    "metrics": {
      "execution_time_ms": 45000,
      "sources_checked": 8,
      "api_calls": 24
    },
    "errors": []
  }
}
```

**Структура результата:**
- `reconciled_data` (object) - Сверенные данные по каждой метрике
  - `sources` (object) - Значения из каждого источника
  - `average` (number) - Усреднённое значение (истина)
  - `deviation` (float) - Максимальное отклонение между источниками
  - `reliable` (boolean) - Флаг надёжности данных
- `issues` (array) - Список проблем (недоступные источники, высокие отклонения, аномалии)
- `summary` (object) - Сводка по сверке

**Метрики:**
- `execution_time_ms` - Время выполнения
- `sources_checked` - Количество проверенных источников
- `api_calls` - Количество API вызовов

---

## 🔄 АЛГОРИТМ РАБОТЫ

### Шаг 1: Получение задачи
1. Подписаться на события `data_reconciliation.requested`
2. Фильтровать по `subagent_id == "data-reconciliation"`
3. Валидировать входные параметры (period, metrics, sources)

### Шаг 2: Сбор данных из источников
1. Получить данные от Data Collector Agent (или напрямую из источников)
2. Для каждого источника:
   - Проверить доступность API (вернул ли данные?)
   - Проверить формат данных (корректный JSON/структура?)
   - Проверить полноту данных (все метрики присутствуют?)

### Шаг 3: Проверка доступности источников
1. Если источник недоступен (API error, timeout):
   - Повторить попытку через 3-5 минут (до 3 попыток)
   - Если всё равно недоступен → добавить в `issues` с типом `source_unavailable`
   - Исключить из дальнейшей сверки
2. Если доступен только 1 источник:
   - Использовать его данные как истину
   - Пометить `reliable: false` (низкая уверенность)

### Шаг 4: Проверка исторической адекватности
1. Для каждого источника и метрики:
   - Сравнить с историческими данными (вчера, неделю назад)
   - Если резкое изменение (>10x):
     - Проверить другие источники (показывают ли они такой же рост?)
     - Если все источники показывают рост → это реальный рост (добавить в `issues` с типом `anomaly`, severity `info`)
     - Если только один источник → это аномалия (добавить в `issues` с типом `anomaly`, severity `critical`, исключить из сверки)

### Шаг 5: Сравнение между источниками
1. Для каждой метрики:
   - Собрать значения из всех доступных источников
   - Вычислить среднее значение
   - Вычислить максимальное отклонение: `max_deviation = max(|value - average|) / average`
2. Если отклонение > порога (10%):
   - Добавить в `issues` с типом `high_deviation`, severity `critical`
   - Эскалировать Operator (событие `escalation.required`)
   - Вернуть ошибку Analytics Magister

### Шаг 6: Вычисление истины
1. Для каждой метрики:
   - Усреднить значения из всех надёжных источников
   - Установить флаг `reliable`:
     - `true` если отклонение ≤ 10% и доступно ≥2 источников
     - `false` если отклонение > 10% или доступен только 1 источник
2. Для метрик, доступных только в одном источнике:
   - Просто передать значение из этого источника
   - Пометить как "не сверено" (добавить в `issues` с типом `single_source`)

### Шаг 7: Формирование результата
1. Собрать `reconciled_data` со всеми метриками
2. Собрать `issues` со всеми проблемами
3. Сформировать `summary`
4. Определить `status`:
   - `success` если все метрики сверены без критичных проблем
   - `partial_success` если есть некритичные проблемы (недоступные источники, single_source)
   - `failure` если критичные проблемы (high_deviation, все источники недоступны)

### Шаг 8: Сохранение результатов
1. Сохранить в базу данных Analytics Magister:
   - Таблица `reconciled_metrics` (дата, метрика, источники, среднее, отклонение)
2. Сохранить в Obsidian vault Analytics Magister:
   - Путь: `AIM/obsidian/analytics-magister/wiki/reconciliation/YYYY-MM-DD.md`
   - Формат: Markdown таблица с результатами

### Шаг 9: Отправка результата
1. Отправить событие `data_reconciliation.completed` через Event Bus
2. Логировать в Event Store с correlation_id
3. Если `status: "failure"` → эскалировать Operator (событие `escalation.required`)

---

## 🔧 ИНТЕГРАЦИИ

### Внешние сервисы:

**Google Analytics API:**
- API endpoint: `https://analyticsdata.googleapis.com/v1beta`
- Аутентификация: OAuth 2.0
- Rate limit: 10 requests/second
- Документация: https://developers.google.com/analytics/devguides/reporting/data/v1

**Яндекс Метрика API:**
- API endpoint: `https://api-metrika.yandex.net/stat/v1/data`
- Аутентификация: OAuth token
- Rate limit: 10 requests/second
- Документация: https://yandex.ru/dev/metrika/doc/api2/api_v1/intro.html

**Keys.so API:**
- API endpoint: `https://api.keys.so/v1`
- Аутентификация: API key
- Rate limit: 100 requests/minute
- Документация: https://keys.so/docs

**Яндекс Директ API:**
- API endpoint: `https://api.direct.yandex.com/json/v5`
- Аутентификация: OAuth token
- Rate limit: 10 requests/second
- Документация: https://yandex.ru/dev/direct/doc/dg/concepts/about.html

**VK Ads API:**
- API endpoint: `https://api.vk.com/method/ads.getStatistics`
- Аутентификация: Access token
- Rate limit: 3 requests/second
- Документация: https://dev.vk.com/ru/api/ads

**CallTouch API:**
- API endpoint: `https://api.calltouch.ru/calls-service/RestAPI`
- Аутентификация: API key
- Rate limit: 10 requests/second
- Документация: https://www.calltouch.ru/support/api/

**Roistat API:**
- API endpoint: `https://cloud.roistat.com/api/v1`
- Аутентификация: API key
- Rate limit: 10 requests/second
- Документация: https://help.roistat.com/api/

### Внутренние зависимости:

- Event Bus (обязательно) - получение задач, отправка результатов
- Event Store (обязательно) - логирование всех сверок
- Data Collector Agent (опционально) - получение данных из источников
- Analytics Magister database (обязательно) - сохранение результатов
- Obsidian vault (обязательно) - сохранение истории сверок
- Operator (опционально) - эскалация при критичных проблемах

---

## 📊 МЕТРИКИ УСПЕХА

### Качественные метрики:

**Точность сверки:**
- Метрика: Процент успешных сверок без критичных ошибок
- Целевое значение: > 95%
- Как измерять: Аудит случайной выборки, сравнение с ручной сверкой

**Метрики в пределах отклонения:**
- Метрика: Процент метрик с отклонением ≤ 10%
- Целевое значение: > 90%
- Как измерять: Автоматический подсчёт из результатов сверок

### Производительность:

**Скорость:**
- Среднее время выполнения: < 5 минут (для ежедневной сверки)
- 95-й перцентиль: < 10 минут
- Максимальное время: < 15 минут

**Надёжность:**
- Success rate: > 95%
- Partial success rate: > 99%
- Failure rate: < 1%

### Бизнес-метрики:

**Влияние на качество решений:**
- Точность данных для принятия решений (целевое: > 95%)
- Снижение количества ошибочных решений из-за неверных данных (целевое: -80%)
- Экономия времени на ручную сверку (целевое: -90%)

---

## 🧪 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ

### Пример 1: Успешная сверка (все источники согласны)

**Входные данные:**
```json
{
  "period": {
    "start_date": "2026-05-08",
    "end_date": "2026-05-08"
  },
  "metrics": "all",
  "sources": "all",
  "deviation_threshold": 0.10,
  "trigger": "scheduled"
}
```

**Выходные данные:**
```json
{
  "status": "success",
  "result": {
    "reconciled_data": {
      "visits": {
        "sources": {
          "google_analytics": 1000,
          "yandex_metrica": 1050,
          "keys_so": 980
        },
        "average": 1010,
        "deviation": 0.035,
        "reliable": true
      },
      "conversions": {
        "sources": {
          "google_analytics": 50,
          "yandex_metrica": 52,
          "calltouch": 51
        },
        "average": 51,
        "deviation": 0.02,
        "reliable": true
      }
    },
    "issues": [],
    "summary": {
      "total_metrics": 15,
      "reconciled": 15,
      "issues": 0,
      "sources_available": 8,
      "sources_unavailable": 0
    }
  },
  "metrics": {
    "execution_time_ms": 45000,
    "sources_checked": 8,
    "api_calls": 24
  }
}
```

### Пример 2: Частичный успех (один источник недоступен)

**Входные данные:**
```json
{
  "period": {
    "start_date": "2026-05-08",
    "end_date": "2026-05-08"
  },
  "metrics": "all",
  "sources": "all",
  "deviation_threshold": 0.10,
  "trigger": "manual"
}
```

**Выходные данные:**
```json
{
  "status": "partial_success",
  "result": {
    "reconciled_data": {
      "visits": {
        "sources": {
          "google_analytics": 1000,
          "yandex_metrica": 1050
        },
        "average": 1025,
        "deviation": 0.024,
        "reliable": true
      }
    },
    "issues": [
      {
        "type": "source_unavailable",
        "source": "roistat",
        "severity": "warning",
        "message": "Roistat API unavailable after 3 retry attempts, excluded from reconciliation"
      }
    ],
    "summary": {
      "total_metrics": 15,
      "reconciled": 15,
      "issues": 1,
      "sources_available": 7,
      "sources_unavailable": 1
    }
  },
  "metrics": {
    "execution_time_ms": 180000,
    "sources_checked": 8,
    "api_calls": 27
  }
}
```

### Пример 3: Критичная ошибка (высокое отклонение)

**Входные данные:**
```json
{
  "period": {
    "start_date": "2026-05-08",
    "end_date": "2026-05-08"
  },
  "metrics": "all",
  "sources": "all",
  "deviation_threshold": 0.10,
  "trigger": "scheduled"
}
```

**Выходные данные:**
```json
{
  "status": "failure",
  "result": {
    "reconciled_data": {
      "ad_spend": {
        "sources": {
          "yandex_direct": 50000,
          "vk_ads": 60000,
          "calltouch": 52000
        },
        "average": 54000,
        "deviation": 0.15,
        "reliable": false
      }
    },
    "issues": [
      {
        "type": "high_deviation",
        "metric": "ad_spend",
        "deviation": 0.15,
        "severity": "critical",
        "message": "Ad spend deviation 15% exceeds threshold 10%",
        "sources": {
          "yandex_direct": 50000,
          "vk_ads": 60000,
          "calltouch": 52000
        }
      }
    ],
    "summary": {
      "total_metrics": 15,
      "reconciled": 14,
      "issues": 1,
      "sources_available": 8,
      "sources_unavailable": 0
    }
  },
  "metrics": {
    "execution_time_ms": 50000,
    "sources_checked": 8,
    "api_calls": 24
  },
  "errors": [
    {
      "code": "HIGH_DEVIATION",
      "message": "Critical deviation detected, escalating to Operator"
    }
  ]
}
```

### Пример 4: Аномалия (один источник показывает нереальные данные)

**Входные данные:**
```json
{
  "period": {
    "start_date": "2026-05-08",
    "end_date": "2026-05-08"
  },
  "metrics": "all",
  "sources": "all",
  "deviation_threshold": 0.10,
  "trigger": "scheduled"
}
```

**Выходные данные:**
```json
{
  "status": "partial_success",
  "result": {
    "reconciled_data": {
      "visits": {
        "sources": {
          "google_analytics": 1000,
          "yandex_metrica": 1050
        },
        "average": 1025,
        "deviation": 0.024,
        "reliable": true
      }
    },
    "issues": [
      {
        "type": "anomaly",
        "metric": "visits",
        "source": "keys_so",
        "value": 1000000,
        "expected_range": "800-1200",
        "severity": "critical",
        "message": "Keys.so shows 1M visits vs expected 1K - marked as unreliable and excluded",
        "action": "Source excluded from reconciliation, Operator notified"
      }
    ],
    "summary": {
      "total_metrics": 15,
      "reconciled": 15,
      "issues": 1,
      "sources_available": 7,
      "sources_unavailable": 0
    }
  },
  "metrics": {
    "execution_time_ms": 55000,
    "sources_checked": 8,
    "api_calls": 24
  }
}
```

---

## 🔒 ОБРАБОТКА ОШИБОК

### Типы ошибок:

**Валидация входных данных:**
- Код: `INVALID_INPUT`
- Действие: Вернуть failure сразу
- Retry: Нет
- Пример: Некорректный формат даты, отрицательный deviation_threshold

**Ошибка API источника:**
- Код: `SOURCE_API_ERROR`
- Действие: Retry с exponential backoff (3-5 минут между попытками)
- Retry: До 3 попыток
- Если все попытки неудачны → исключить источник, добавить в `issues`

**Все источники недоступны:**
- Код: `ALL_SOURCES_UNAVAILABLE`
- Действие: Вернуть failure, эскалировать Operator
- Retry: Нет
- Сообщение: "Невозможно выполнить сверку, все источники недоступны"

**Высокое отклонение (>10%):**
- Код: `HIGH_DEVIATION`
- Действие: Вернуть failure, эскалировать Operator
- Retry: Нет
- Сообщение: "Отклонение {metric} составляет {deviation}%, превышает порог {threshold}%"

**Аномальные данные:**
- Код: `ANOMALY_DETECTED`
- Действие: Исключить источник из сверки, уведомить Operator
- Retry: Нет
- Сообщение: "Источник {source} показывает аномальные данные для {metric}: {value} vs ожидаемый диапазон {range}"

**Timeout:**
- Код: `TIMEOUT`
- Действие: Вернуть partial_success с обработанными метриками
- Retry: Нет
- Максимальное время: 15 минут

**Внутренняя ошибка:**
- Код: `INTERNAL_ERROR`
- Действие: Логировать, вернуть failure, эскалировать Operator
- Retry: Нет

### Graceful degradation:

При частичном сбое:
1. Обработать максимум метрик
2. Вернуть partial_success
3. Указать, какие метрики не удалось сверить
4. Позволить Analytics Magister решить, что делать дальше

При критичной ошибке:
1. Вернуть failure
2. Эскалировать Operator (событие `escalation.required`)
3. Сохранить детали ошибки для анализа

---

## 🧠 ОБУЧЕНИЕ И АДАПТАЦИЯ

### Источники обучения:

**От Teacher Agent:**
- Обновление алгоритмов сверки
- Новые источники данных для интеграции
- Оптимизация порогов отклонений
- Best practices работы с API

**Из собственного опыта:**
- История сверок (какие источники чаще ошибаются)
- Паттерны аномалий (типичные ошибки источников)
- Корреляции между источниками
- Оптимальные пороги отклонений для разных метрик

**От Analytics Magister:**
- Обратная связь: "эта сверка была правильной/неправильной"
- Запросы на новые метрики
- Изменение приоритетов источников

### Адаптация:

**Когда адаптироваться:**
- Появляются новые источники данных
- Изменяются API источников
- Метрики точности падают ниже 95%
- Teacher Agent предоставляет обновлённые алгоритмы

**Как адаптироваться:**
1. Teacher Agent по расписанию обучает агента:
   - Анализирует историю сверок
   - Выявляет паттерны ошибок
   - Оптимизирует пороги отклонений
   - Обновляет приоритеты источников
2. При появлении новых источников:
   - Автоматически включать в сверку
   - Тестировать на исторических данных
   - Определять надёжность источника
3. Адаптация порогов отклонений:
   - **Пока жёсткий порог 10%** (на первое время)
   - В будущем: динамическая адаптация на основе истории
   - Если GA и Метрика всегда расходятся на 8% → возможно, сделать это нормой

### Приоритизация источников:

**Текущий подход:**
- Все источники равны (нет приоритизации)
- Усреднение без весов

**Будущая адаптация:**
- Динамическая приоритизация на основе надёжности
- Источники с меньшим количеством ошибок получают больший вес
- Teacher Agent обучает приоритеты на основе истории

---

## 📝 ЛОГИРОВАНИЕ

### Что логировать:

**В Event Store (обязательно):**
- Все входящие события `data_reconciliation.requested`
- Все исходящие события `data_reconciliation.completed`
- Все эскалации `escalation.required`
- Correlation ID для трейсинга

**В базу данных Analytics Magister (обязательно):**
- Таблица `reconciled_metrics`:
  - `date`, `metric`, `source`, `value`, `average`, `deviation`, `reliable`
- Таблица `reconciliation_issues`:
  - `date`, `type`, `metric`, `source`, `severity`, `message`

**В Obsidian vault Analytics Magister (обязательно):**
- Путь: `AIM/obsidian/analytics-magister/wiki/reconciliation/YYYY-MM-DD.md`
- Формат: Markdown таблица с результатами сверки
- Включает: все метрики, источники, отклонения, проблемы

**В системные логи (опционально):**
- Debug информация (API запросы, ответы)
- Ошибки и warnings (недоступность API, timeout)
- Performance traces (время выполнения каждого шага)

### Формат логов:

```
[YYYY-MM-DD HH:MM:SS] [LEVEL] [data-reconciliation] [correlation_id] Message
```

**Пример:**
```
[2026-05-09 09:00:15] [INFO] [data-reconciliation] [abc-123] Received data_reconciliation.requested for 2026-05-08
[2026-05-09 09:00:16] [DEBUG] [data-reconciliation] [abc-123] Checking 8 sources for 15 metrics
[2026-05-09 09:02:45] [WARNING] [data-reconciliation] [abc-123] Roistat API unavailable, retrying...
[2026-05-09 09:05:15] [ERROR] [data-reconciliation] [abc-123] Roistat API unavailable after 3 attempts, excluding
[2026-05-09 09:05:30] [INFO] [data-reconciliation] [abc-123] Completed reconciliation: 15 metrics, 1 issue
[2026-05-09 09:05:31] [INFO] [data-reconciliation] [abc-123] Sent data_reconciliation.completed
```

---

## 🧪 ТЕСТИРОВАНИЕ

### Unit тесты:

**Покрытие:** > 80%

**Обязательные тесты:**
- Валидация входных данных
- Проверка доступности источников
- Вычисление среднего и отклонения
- Обнаружение аномалий
- Обработка ошибок API
- Формирование результата

### Integration тесты:

**Обязательные сценарии:**
- Получение задачи от Analytics Orchestrator через Event Bus
- Отправка результата Analytics Orchestrator через Event Bus
- Логирование в Event Store
- Сохранение в базу данных Analytics Magister
- Сохранение в Obsidian vault
- Эскалация Operator при критичных проблемах

### E2E тесты:

**Обязательные сценарии:**
- Полный цикл: задача → сбор данных → сверка → результат
- Все источники доступны и согласны → success
- Один источник недоступен → partial_success
- Высокое отклонение → failure + escalation
- Аномальные данные → partial_success + exclusion + notification
- Все источники недоступны → failure + escalation

**Тестовые кейсы:**
- Mock данные из 8 источников с отклонением 5% → success
- Mock данные с одним недоступным источником → partial_success
- Mock данные с отклонением 15% → failure + escalation
- Mock данные с аномалией (1M вместо 1K) → partial_success + exclusion

---

## 🚀 DEPLOYMENT

### Требования:

**Окружение:**
- Python 3.11+
- Event Bus доступен
- Event Store доступен
- Analytics Magister database доступна
- Obsidian vault доступен (`AIM/obsidian/analytics-magister/`)

**Зависимости:**
- `httpx >= 0.24.0` (для API запросов)
- `pydantic >= 2.0.0` (для валидации данных)
- `sqlalchemy >= 2.0.0` (для работы с БД)
- `python-frontmatter >= 1.0.0` (для работы с Obsidian frontmatter)
- `numpy >= 1.24.0` (для вычисления статистики)

**Конфигурация:**
```env
SUBAGENT_ID=data-reconciliation
EVENT_BUS_URL=...
EVENT_STORE_URL=...
ANALYTICS_DB_URL=sqlite+aiosqlite:///./AIM/data/analytics.db
OBSIDIAN_VAULT_PATH=./AIM/obsidian/analytics-magister
DEVIATION_THRESHOLD=0.10
RETRY_ATTEMPTS=3
RETRY_DELAY_SECONDS=180
```

**API ключи для источников:**
```env
GOOGLE_ANALYTICS_CREDENTIALS=...
YANDEX_METRICA_TOKEN=...
KEYS_SO_API_KEY=...
YANDEX_DIRECT_TOKEN=...
VK_ADS_TOKEN=...
CALLTOUCH_API_KEY=...
ROISTAT_API_KEY=...
```

### Мониторинг:

**Метрики для алертов:**
- Success rate < 95% → Warning
- Success rate < 90% → Critical
- Avg execution time > 10 minutes → Warning
- 95th percentile > 15 minutes → Critical
- High deviation rate > 5% → Warning
- High deviation rate > 10% → Critical
- Sources unavailable > 2 → Warning
- All sources unavailable → Critical (эскалация Operator)

**Дашборд метрик:**
- Количество сверок в день
- Процент success / partial_success / failure
- Среднее время сверки
- Топ-10 метрик с высоким отклонением
- Топ-10 ненадёжных источников
- История доступности источников

---

## 📚 СВЯЗАННЫЕ ДОКУМЕНТЫ

### Спецификации:
- `ANALYTICS_MAGISTER_SPEC.md` - Спецификация родительского Magister
- `ANALYTICS_ORCHESTRATOR_SPEC.md` - Спецификация родительского Orchestrator (TODO)
- `DATA_COLLECTOR_SPEC.md` - Спецификация Data Collector Agent (TODO)
- `TEACHER_AGENT_SPEC.md` - Спецификация Teacher Agent (TODO)

### Код:
- `AIM/src/aim/subagents/analytics/data_reconciliation.py` - Реализация (TODO)
- `AIM/tests/subagents/analytics/test_data_reconciliation.py` - Тесты (TODO)

### Документация:
- Event Bus API
- Event Store API
- Analytics Magister database schema
- Obsidian integration guide
- API документация источников (GA, Метрика, Keys.so, Direct, VK Ads, CallTouch, Roistat)

### База данных:
- `AIM/data/analytics.db` - SQLite база Analytics Magister
- Таблицы: `reconciled_metrics`, `reconciliation_issues`

### Obsidian Vault:
- `AIM/obsidian/analytics-magister/wiki/reconciliation/` - История сверок
- `AIM/obsidian/analytics-magister/wiki/log.md` - Операционная история

---

**Дата создания:** 2026-05-09  
**Автор:** Mikhail Eliseev (via meAI Architect)  
**Версия:** 1.0  
**Статус:** Ready

**Критичность:** ⭐⭐⭐⭐⭐ (P0 - блокирует запуск системы)  
**Причина:** От него зависит ВСЁ. Data-driven агентство не может работать без надёжных данных. Все решения принимаются на основе метрик, поэтому точность данных критична.
