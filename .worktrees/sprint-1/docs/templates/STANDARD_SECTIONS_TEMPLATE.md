# Шаблон стандартных секций (6-11) для спецификаций Subagents

**Дата создания:** 2026-05-09  
**Цель:** Ускорить создание спецификаций за счёт переиспользования стандартных блоков

---

## 📋 ИНСТРУКЦИЯ ПО ИСПОЛЬЗОВАНИЮ

1. Скопировать этот файл
2. Заменить все плейсхолдеры `{НАЗВАНИЕ}` на реальные значения
3. Добавить специфичные детали (ошибки, тесты, API ключи)
4. Склеить с уникальными секциями 1-5
5. Готово!

**Время:** ~10 минут

---

## ПЛЕЙСХОЛДЕРЫ

- `{AGENT_NAME}` — название агента (например, "Keyword Research Agent")
- `{AGENT_ID}` — ID агента (например, "keyword-research")
- `{MAGISTER_NAME}` — название Magister (например, "SEO Magister")
- `{MAGISTER_ID}` — ID Magister (например, "seo-magister")
- `{DOMAIN}` — домен (например, "seo", "content", "ads", "social", "analytics")
- `{ACTION}` — действие (например, "keyword_research", "content_generation", "trend_monitoring")
- `{EVENT_TYPE}` — тип события (например, "seo.keyword_research", "content.generation")

---

## 6. ИНТЕГРАЦИИ

### 6.1 Event Bus

**Получение задач от {MAGISTER_NAME}:**
```json
{
  "event_type": "{EVENT_TYPE}.requested",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "{AGENT_ID}",
  "payload": {
    // специфичные параметры задачи
  }
}
```

**Отправка результатов {MAGISTER_NAME}:**
```json
{
  "event_type": "{EVENT_TYPE}.completed",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "{AGENT_ID}",
  "payload": {
    "status": "success",
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

### 6.2 Event Store

**Логирование всех событий:**
- `{EVENT_TYPE}.requested` — получена задача
- `{EVENT_TYPE}.completed` — задача завершена
- `{EVENT_TYPE}.failed` — задача провалена
- `escalation.required` — эскалация критичной ошибки

**Формат записи:**
```json
{
  "event_id": "uuid",
  "event_type": "{EVENT_TYPE}.completed",
  "correlation_id": "uuid",
  "timestamp": "2026-05-09T22:30:00Z",
  "subagent_id": "{AGENT_ID}",
  "payload": {/* event data */}
}
```

### 6.3 Obsidian Vault

**Путь:** `obsidian/{MAGISTER_ID}/`

**Операции:**
- **Ingest:** Сохранение данных в `raw/`
- **Query:** Чтение истории для анализа
- **Lint:** Проверка противоречий, устаревших данных

**Специальные файлы:**
- `wiki/log.md` — хронология всех операций
- `wiki/index.md` — каталог всех страниц
- `wiki/sources/{AGENT_ID}_{date}.md` — сводки по работе агента

### 6.4 Database

**Таблицы:**
- `{AGENT_ID}_results` — результаты работы агента
- `{AGENT_ID}_history` — история выполнения задач

**Операции:**
- INSERT: сохранение новых результатов
- SELECT: чтение истории для анализа
- UPDATE: обновление статусов

### 6.5 Teacher Agent

**Интеграция:**
- Teacher Agent читает `wiki/log.md` и `wiki/concepts/`
- Анализирует успешные/неудачные кейсы
- Обновляет best practices
- Улучшает алгоритмы и промпты

**Частота обучения:**
- Периодический пересмотр: раз в квартал
- Экстренное обучение: при падении метрик качества
- Адаптация: при изменении внешних API

### 6.6 Внешние API

**[ДОБАВИТЬ СПИСОК ВНЕШНИХ API]**

Пример:
- **API Name** — описание, endpoint, аутентификация, rate limits

---

## 7. ОБРАБОТКА ОШИБОК

### 7.1 Стандартные ошибки

**INVALID_INPUT:**
- Причина: Пустые обязательные параметры, неверный формат
- Действие: Вернуть failure сразу
- Retry: Нет
- Логирование: Event Store + системные логи

**API_ERROR:**
- Причина: Временная недоступность внешнего API
- Действие: Retry с exponential backoff (10 попыток, 1 минута интервал)
- Если все попытки исчерпаны → вернуть partial_success с собранными данными
- Логирование: Event Store + системные логи

**TIMEOUT:**
- Причина: Превышено максимальное время выполнения
- Действие: Вернуть partial_success с частичными результатами
- Retry: Нет
- Логирование: Event Store + Obsidian

**INTERNAL_ERROR:**
- Причина: Внутренняя ошибка агента (баг в коде)
- Действие: Логировать, вернуть failure, эскалировать
- Retry: Нет
- Эскалация: {MAGISTER_NAME} → Operator → User

### 7.2 Специфичные ошибки

**[ДОБАВИТЬ 2-5 СПЕЦИФИЧНЫХ ОШИБОК]**

Пример:
```
**ERROR_NAME:**
- Причина: описание
- Действие: что делать
- Retry: да/нет
- Эскалация: уровень (Warning/Critical)
```

### 7.3 Эскалация

**Путь эскалации:**
```
{AGENT_NAME} → {MAGISTER_NAME} → Operator → User → Architect
```

**Когда эскалировать:**
- Critical errors (блокируют работу системы)
- Success rate < 90% в течение 3 дней
- Специфичные критичные ошибки

**Формат эскалации:**
```json
{
  "event_type": "escalation.required",
  "correlation_id": "uuid",
  "source": "{AGENT_ID}",
  "severity": "critical",
  "payload": {
    "error_type": "ERROR_NAME",
    "message": "Error description",
    "context": {
      // дополнительный контекст
    },
    "escalation_path": ["{MAGISTER_NAME}", "Operator", "User"]
  }
}
```

### 7.4 Graceful Degradation

**При частичном сбое:**
1. Выполнить максимум возможного
2. Вернуть `partial_success`
3. Указать, что не удалось выполнить
4. Уведомить {MAGISTER_NAME}

**Примеры:**
- Если API недоступен → использовать кэшированные данные
- Если часть данных не получена → вернуть то, что есть
- Если критичная ошибка → эскалировать немедленно

---

## 8. ОБУЧЕНИЕ И АДАПТАЦИЯ

### 8.1 Интеграция с Teacher Agent

**Что Teacher Agent предоставляет:**
- Обновлённые best practices
- Улучшенные алгоритмы и формулы
- Новые паттерны успешных кейсов
- Рекомендации по оптимизации

**Как {AGENT_NAME} обучается:**
1. Teacher Agent читает `wiki/log.md` и `wiki/concepts/`
2. Анализирует успешные/неудачные кейсы
3. Создаёт обновлённые инструкции
4. {AGENT_NAME} применяет новые инструкции
5. Тестирует на контрольной выборке
6. Сохраняет результаты в Obsidian

**Частота обучения:**
- Периодический пересмотр: раз в квартал
- Экстренное обучение: при падении метрик качества
- Адаптация: при изменении внешних API или алгоритмов

### 8.2 История в Obsidian

**Структура:**
```
obsidian/{MAGISTER_ID}/wiki/
├── log.md                    # Хронология операций
├── concepts/
│   ├── {concept_1}.md        # Концепции и паттерны
│   └── {concept_2}.md
├── strategies/
│   └── {strategy}.md         # Стратегии и методы
└── connections/
    └── {connections}.md      # Связи и синтезы
```

**Формат log.md:**
```markdown
## [2026-05-09 22:30] {action} | Description of what happened
## [2026-05-09 22:35] {action} | Another action description
```

### 8.3 Адаптация

**Автоматическая адаптация:**
- Если метрики качества падают → запросить обучение у Teacher Agent
- Если новые паттерны обнаружены → логировать для анализа
- Если изменились внешние API → Teacher Agent обновляет стратегию

**Ручная адаптация:**
- Пользователь может изменить параметры через {MAGISTER_NAME}
- Пользователь может добавить новые источники данных
- Пользователь может изменить пороги и лимиты

---

## 9. ЛОГИРОВАНИЕ

### 9.1 Event Store (обязательно)

**Логируемые события:**
- `{EVENT_TYPE}.requested` — получена задача
- `{EVENT_TYPE}.completed` — задача завершена
- `{EVENT_TYPE}.failed` — задача провалена
- `escalation.required` — эскалация критичной ошибки

**Формат:**
```json
{
  "event_id": "uuid",
  "event_type": "{EVENT_TYPE}.completed",
  "correlation_id": "uuid",
  "timestamp": "2026-05-09T22:30:00Z",
  "subagent_id": "{AGENT_ID}",
  "payload": {/* event data */}
}
```

### 9.2 Obsidian Vault (обязательно)

**История операций (`wiki/log.md`):**
```markdown
## [2026-05-09 22:30] {action} | Description
## [2026-05-09 22:35] {action} | Another description
```

**Результаты работы:**
- `wiki/sources/` — обработанные источники
- `wiki/concepts/` — концепции и паттерны
- `wiki/strategies/` — стратегии и методы

**Метрики производительности:**
- `wiki/metrics/success_rate.md` — процент успешных выполнений
- `wiki/metrics/execution_time.md` — время выполнения

### 9.3 Системные логи (опционально)

**Debug информация:**
- API запросы и ответы
- Время выполнения каждого шага
- Промежуточные результаты

**Ошибки и warnings:**
- Ошибки API
- Таймауты
- Валидация данных

**Формат:**
```
[2026-05-09 22:30:00] [INFO] [{AGENT_ID}] [correlation-id-123] Message
[2026-05-09 22:30:03] [ERROR] [{AGENT_ID}] [correlation-id-123] Error message
```

---

## 10. ТЕСТИРОВАНИЕ

### 10.1 Unit тесты

**Покрытие:** > 80%

**Обязательные тесты:**
- Валидация входных данных (`test_validate_input`)
- Обработка ошибок API (`test_api_error_handling`)
- Retry механизм (`test_retry_with_backoff`)
- Сохранение в БД (`test_save_to_database`)
- Сохранение в Obsidian (`test_save_to_obsidian`)
- Формирование результата (`test_format_result`)

**[ДОБАВИТЬ 2-3 СПЕЦИФИЧНЫХ ТЕСТА]**

Пример:
```python
def test_specific_logic():
    # Тест специфичной логики агента
    pass
```

### 10.2 Integration тесты

**Обязательные сценарии:**
- Получение задачи через Event Bus (`test_receive_task_from_event_bus`)
- Отправка результата через Event Bus (`test_send_result_to_event_bus`)
- Логирование в Event Store (`test_log_to_event_store`)
- Сохранение в Obsidian vault (`test_save_to_obsidian_vault`)
- Сохранение в базу данных (`test_save_to_database`)
- Эскалация при критичных ошибках (`test_escalation_on_critical_error`)
- Интеграция с внешними API (`test_external_api_integration`)

### 10.3 E2E тесты

**Обязательные сценарии:**
- Полный цикл: задача → выполнение → результат (`test_full_cycle`)
- Частичный сбой (graceful degradation) (`test_partial_failure`)
- Критичная ошибка (escalation) (`test_critical_error_escalation`)
- Retry механизм при временных сбоях API (`test_retry_on_api_error`)

**Пример E2E теста:**
```python
async def test_full_cycle():
    # 1. Создать задачу
    task = {/* task data */}
    
    # 2. Отправить задачу через Event Bus
    await event_bus.publish("{EVENT_TYPE}.requested", task)
    
    # 3. Дождаться результата
    result = await event_bus.subscribe("{EVENT_TYPE}.completed")
    
    # 4. Проверить результат
    assert result["status"] == "success"
    
    # 5. Проверить сохранение в БД
    db_record = await database.query("SELECT * FROM {AGENT_ID}_results WHERE id = ?", result["id"])
    assert db_record is not None
    
    # 6. Проверить сохранение в Obsidian
    obsidian_file = f"obsidian/{MAGISTER_ID}/wiki/sources/{AGENT_ID}_{date}.md"
    assert os.path.exists(obsidian_file)
```

---

## 11. DEPLOYMENT

### 11.1 Требования

**Окружение:**
- Python 3.11+
- Event Bus доступен
- Event Store доступен
- Obsidian vault доступен (`obsidian/{MAGISTER_ID}/`)
- Database доступна (`data/aim.db`)

**Зависимости:**
```txt
httpx >= 0.24.0              # API запросы
pydantic >= 2.0.0            # Валидация данных
sqlalchemy >= 2.0.0          # База данных
python-frontmatter >= 1.0.0  # Obsidian frontmatter
```

### 11.2 Конфигурация (.env)

```env
SUBAGENT_ID={AGENT_ID}
EVENT_BUS_URL=...
EVENT_STORE_URL=...
OBSIDIAN_VAULT_PATH=./obsidian/{MAGISTER_ID}
DATABASE_URL=sqlite+aiosqlite:///./data/aim.db

# [ДОБАВИТЬ API КЛЮЧИ]
# Пример:
# API_NAME_API_KEY=...
# API_NAME_ENDPOINT=...
```

### 11.3 Мониторинг

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
- Специфичные метрики агента

---

**Дата создания:** 2026-05-09  
**Автор:** Mikhail Eliseev (via meAI Architect)  
**Статус:** Ready  
**Применение:** Все спецификации P1 агентов
