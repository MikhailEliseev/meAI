# [SUBAGENT_NAME] - Спецификация

**Дата:** YYYY-MM-DD  
**Magister:** [Parent Magister Name]  
**Приоритет:** P0 / P1 / P2 / P3  
**Статус:** Draft / Ready / Implemented

---

## 🎯 РОЛЬ И НАЗНАЧЕНИЕ

### Основная роль:
[Краткое описание роли Subagent в 1-2 предложениях]

### Что делает:
- ✅ [Основная задача 1]
- ✅ [Основная задача 2]
- ✅ [Основная задача 3]

### Что НЕ делает:
- ❌ [Что не входит в зону ответственности 1]
- ❌ [Что не входит в зону ответственности 2]

### Место в иерархии:
```
[Parent Magister]
    ↓
[Parent Orchestrator]
    ↓
[THIS SUBAGENT] ← вы здесь
```

---

## 📥 ВХОДНЫЕ ДАННЫЕ

### Получает от Orchestrator:

**Формат события:**
```json
{
  "event_type": "subagent.task.assigned",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "[subagent-name]",
  "payload": {
    "input_param_1": "value",
    "input_param_2": "value"
  }
}
```

**Обязательные параметры:**
- `input_param_1` (string) - Описание параметра
- `input_param_2` (int) - Описание параметра

**Опциональные параметры:**
- `optional_param_1` (string) - Описание параметра

---

## 📤 ВЫХОДНЫЕ ДАННЫЕ

### Отправляет Orchestrator:

**Формат события:**
```json
{
  "event_type": "subagent.task.completed",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "[subagent-name]",
  "payload": {
    "status": "success" | "partial_success" | "failure",
    "result": {
      "output_param_1": "value",
      "output_param_2": "value"
    },
    "metrics": {
      "execution_time_ms": 1234,
      "items_processed": 10
    },
    "errors": []
  }
}
```

**Структура результата:**
- `output_param_1` (string) - Описание результата
- `output_param_2` (array) - Описание результата

**Метрики:**
- `execution_time_ms` - Время выполнения в миллисекундах
- `items_processed` - Количество обработанных элементов

---

## 🔄 АЛГОРИТМ РАБОТЫ

### Шаг 1: Получение задачи
1. Подписаться на события `subagent.task.assigned`
2. Фильтровать по `subagent_id == "[subagent-name]"`
3. Валидировать входные параметры

### Шаг 2: Обработка данных
1. [Описание шага обработки 1]
2. [Описание шага обработки 2]
3. [Описание шага обработки 3]

### Шаг 3: Формирование результата
1. Собрать результаты обработки
2. Рассчитать метрики
3. Сформировать событие результата

### Шаг 4: Отправка результата
1. Отправить событие `subagent.task.completed`
2. Логировать в Event Store
3. Сохранить в Obsidian vault

---

## 🔧 ИНТЕГРАЦИИ

### Внешние сервисы:

**[Service Name 1]:**
- API endpoint: `https://api.example.com/v1/endpoint`
- Аутентификация: API key
- Rate limit: 100 requests/minute
- Документация: [ссылка]

**[Service Name 2]:**
- API endpoint: `https://api.example2.com/v1/endpoint`
- Аутентификация: OAuth 2.0
- Rate limit: 1000 requests/hour
- Документация: [ссылка]

### Внутренние зависимости:

- Event Bus (обязательно)
- Event Store (обязательно)
- Obsidian vault (обязательно)
- [Другой Subagent] (опционально)

---

## 📊 МЕТРИКИ УСПЕХА

### Качественные метрики:

**Точность:**
- Метрика: [Название метрики]
- Целевое значение: [Значение]
- Как измерять: [Описание]

**Полнота:**
- Метрика: [Название метрики]
- Целевое значение: [Значение]
- Как измерять: [Описание]

### Производительность:

**Скорость:**
- Среднее время выполнения: < X секунд
- 95-й перцентиль: < Y секунд
- Максимальное время: < Z секунд

**Надёжность:**
- Success rate: > 95%
- Partial success rate: > 99%
- Failure rate: < 1%

### Бизнес-метрики:

**Влияние на прибыль:**
- [Метрика 1]: [Целевое значение]
- [Метрика 2]: [Целевое значение]

---

## 🧪 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ

### Пример 1: Успешное выполнение

**Входные данные:**
```json
{
  "input_param_1": "example_value",
  "input_param_2": 42
}
```

**Выходные данные:**
```json
{
  "status": "success",
  "result": {
    "output_param_1": "processed_value",
    "output_param_2": [1, 2, 3]
  },
  "metrics": {
    "execution_time_ms": 1234,
    "items_processed": 3
  }
}
```

### Пример 2: Частичный успех

**Входные данные:**
```json
{
  "input_param_1": "example_value",
  "input_param_2": 42
}
```

**Выходные данные:**
```json
{
  "status": "partial_success",
  "result": {
    "output_param_1": "processed_value",
    "output_param_2": [1, 2]
  },
  "metrics": {
    "execution_time_ms": 2345,
    "items_processed": 2
  },
  "errors": [
    {
      "code": "ITEM_PROCESSING_FAILED",
      "message": "Failed to process item 3",
      "details": {}
    }
  ]
}
```

### Пример 3: Ошибка

**Входные данные:**
```json
{
  "input_param_1": "invalid_value",
  "input_param_2": -1
}
```

**Выходные данные:**
```json
{
  "status": "failure",
  "result": null,
  "metrics": {
    "execution_time_ms": 100,
    "items_processed": 0
  },
  "errors": [
    {
      "code": "INVALID_INPUT",
      "message": "input_param_2 must be positive",
      "details": {
        "param": "input_param_2",
        "value": -1
      }
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

**Ошибка внешнего API:**
- Код: `EXTERNAL_API_ERROR`
- Действие: Retry с exponential backoff
- Retry: До 3 попыток

**Timeout:**
- Код: `TIMEOUT`
- Действие: Вернуть partial_success с обработанными данными
- Retry: Нет

**Внутренняя ошибка:**
- Код: `INTERNAL_ERROR`
- Действие: Логировать, вернуть failure
- Retry: Нет

### Graceful degradation:

При частичном сбое:
1. Обработать максимум данных
2. Вернуть partial_success
3. Указать, что не удалось обработать
4. Позволить Orchestrator решить, что делать дальше

---

## 🧠 ОБУЧЕНИЕ И АДАПТАЦИЯ

### Источники обучения:

**От Magister:**
- Best practices по направлению
- Актуальные техники
- Обновления алгоритмов

**Из собственного опыта:**
- Успешные кейсы (что сработало)
- Неудачные попытки (что не сработало)
- Метрики результатов

**Из Obsidian vault:**
- Исторические данные
- Паттерны и инсайты
- Корреляции с результатами

### Адаптация:

**Когда адаптироваться:**
- Метрики падают ниже целевых
- Появляются новые best practices
- Изменяются внешние условия

**Как адаптироваться:**
1. Получить обновлённые знания от Magister
2. Протестировать на небольшой выборке
3. Сравнить метрики до/после
4. Применить, если улучшение подтверждено

---

## 📝 ЛОГИРОВАНИЕ

### Что логировать:

**В Event Store (обязательно):**
- Все входящие события
- Все исходящие события
- Correlation ID для трейсинга

**В Obsidian vault (обязательно):**
- Результаты выполнения
- Метрики производительности
- Инсайты и паттерны

**В системные логи (опционально):**
- Debug информация
- Ошибки и warnings
- Performance traces

### Формат логов:

```
[YYYY-MM-DD HH:MM:SS] [LEVEL] [subagent-name] [correlation_id] Message
```

---

## 🧪 ТЕСТИРОВАНИЕ

### Unit тесты:

**Покрытие:** > 80%

**Обязательные тесты:**
- Валидация входных данных
- Обработка корректных данных
- Обработка некорректных данных
- Обработка граничных случаев
- Обработка ошибок внешних API

### Integration тесты:

**Обязательные сценарии:**
- Получение задачи от Orchestrator
- Отправка результата Orchestrator
- Логирование в Event Store
- Сохранение в Obsidian vault

### E2E тесты:

**Обязательные сценарии:**
- Полный цикл: задача → обработка → результат
- Обработка ошибок
- Graceful degradation

---

## 🚀 DEPLOYMENT

### Требования:

**Окружение:**
- Python 3.11+
- Event Bus доступен
- Event Store доступен
- Obsidian vault доступен

**Зависимости:**
- [Библиотека 1] >= X.Y.Z
- [Библиотека 2] >= X.Y.Z

**Конфигурация:**
```env
SUBAGENT_ID=[subagent-name]
EVENT_BUS_URL=...
EVENT_STORE_URL=...
OBSIDIAN_VAULT_PATH=...
EXTERNAL_API_KEY=...
```

### Мониторинг:

**Метрики для алертов:**
- Success rate < 95% → Warning
- Success rate < 90% → Critical
- Avg execution time > X seconds → Warning
- 95th percentile > Y seconds → Critical

---

## 📚 СВЯЗАННЫЕ ДОКУМЕНТЫ

### Спецификации:
- `[Parent Magister]_SPEC.md` - Спецификация родительского Magister
- `[Parent Orchestrator]_SPEC.md` - Спецификация родительского Orchestrator

### Код:
- `AIM/src/aim/subagents/[domain]/[subagent_name].py` - Реализация
- `AIM/tests/subagents/[domain]/test_[subagent_name].py` - Тесты

### Документация:
- Event Bus API
- Event Store API
- Obsidian integration guide

---

**Дата создания:** YYYY-MM-DD  
**Автор:** [Имя]  
**Версия:** 1.0  
**Статус:** [Draft / Ready / Implemented]
