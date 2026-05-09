# Medical Fact-Checker Agent - Спецификация

**Дата:** 2026-05-09  
**Magister:** Content Magister  
**Приоритет:** P0 (Критичный)  
**Статус:** Ready

---

## 🎯 РОЛЬ И НАЗНАЧЕНИЕ

### Основная роль:
Medical Fact-Checker Agent проверяет медицинские факты во всём контенте перед публикацией, чтобы предотвратить распространение непроверенной информации, которая может навредить здоровью людей.

### Что делает:
- ✅ Проверяет медицинские факты во всём контенте (статьи, посты, реклама, скрипты звонков)
- ✅ Использует Perplexity для доступа к академическим источникам
- ✅ Применяет принцип массового консенсуса при противоречиях
- ✅ Предлагает корректные альтернативы для неверных фактов
- ✅ Сохраняет историю проверок в Obsidian для обучения
- ✅ Блокирует публикацию контента с непроверенными фактами

### Что НЕ делает:
- ❌ НЕ пишет контент (только проверяет факты)
- ❌ НЕ принимает решения об использовании фактов (это делает Content Magister)
- ❌ НЕ даёт рекомендации по контексту использования фактов

### Место в иерархии:
```
Content Magister
    ↓
Content Orchestrator
    ↓
Medical Fact-Checker Agent ← вы здесь
```

---

## 📥 ВХОДНЫЕ ДАННЫЕ

### Получает от Content Orchestrator:

**Формат события:**
```json
{
  "event_type": "fact_check.requested",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "medical-fact-checker",
  "payload": {
    "content": "markdown text with medical facts",
    "content_type": "article|post|ad|call_script",
    "medical_specialty": ["dentistry", "cosmetology", "general"],
    "urgency": "blocking|async",
    "source_vault": "content-magister/wiki/drafts/article-123.md"
  }
}
```

**Обязательные параметры:**
- `content` (string) - Текст для проверки в формате Markdown
- `content_type` (string) - Тип контента (article, post, ad, call_script)
- `medical_specialty` (array) - Медицинские специальности (для тегирования)

**Опциональные параметры:**
- `urgency` (string) - Приоритет проверки (blocking = до публикации, async = фоновая)
- `source_vault` (string) - Путь к исходному файлу в Obsidian

---

## 📤 ВЫХОДНЫЕ ДАННЫЕ

### Отправляет Content Orchestrator:

**Формат события:**
```json
{
  "event_type": "fact_check.completed",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "medical-fact-checker",
  "payload": {
    "status": "approved" | "rejected" | "partial",
    "result": {
      "facts_checked": [
        {
          "fact": "Original fact text",
          "status": "✅ verified" | "❌ incorrect" | "🔄 corrected",
          "confidence": 0.95,
          "sources": ["url1", "url2"],
          "alternative": "Corrected fact text (if incorrect)",
          "specialty_tags": ["dentistry"]
        }
      ],
      "summary": {
        "total_facts": 10,
        "verified": 8,
        "incorrect": 1,
        "corrected": 1
      }
    },
    "metrics": {
      "execution_time_ms": 180000,
      "perplexity_queries": 10,
      "sources_checked": 45
    },
    "errors": [],
    "blocking_issues": [
      {
        "fact": "Incorrect fact that blocks publication",
        "reason": "Contradicts medical consensus",
        "severity": "critical"
      }
    ]
  }
}
```

**Структура результата:**
- `facts_checked` (array) - Список проверенных фактов с вердиктами
- `summary` (object) - Сводка по проверке
- `blocking_issues` (array) - Критичные проблемы, блокирующие публикацию

**Метрики:**
- `execution_time_ms` - Время выполнения (обычно несколько минут)
- `perplexity_queries` - Количество запросов к Perplexity
- `sources_checked` - Количество проверенных источников

---

## 🔄 АЛГОРИТМ РАБОТЫ

### Шаг 1: Получение задачи
1. Подписаться на события `fact_check.requested`
2. Фильтровать по `subagent_id == "medical-fact-checker"`
3. Валидировать входные параметры (content, content_type, medical_specialty)

### Шаг 2: Извлечение медицинских фактов
1. Парсинг Markdown контента
2. Извлечение утверждений, связанных со здоровьем
3. Классификация фактов по типам:
   - Прямые медицинские утверждения (например, "процедура X лечит Y")
   - Общие утверждения о здоровье (например, "стресс влияет на здоровье")
   - Пограничные случаи (проверять всё равно)
4. Тегирование фактов по специальностям (dentistry, cosmetology, general)

### Шаг 3: Проверка фактов через Perplexity
1. Для каждого факта:
   - Сформировать запрос к Perplexity с сильным промптом
   - Запросить академические источники
   - Проверить актуальность источников (предпочтение свежим)
2. При противоречиях источников:
   - Применить принцип массового консенсуса
   - Если больше источников поддерживают факт A, чем факт B → выбрать A
3. При недоступности Perplexity:
   - Использовать альтернативный источник (Google Search)
   - Использовать Claude Deep Research skill (https://github.com/199-biotechnologies/claude-deep-research-skill)
   - Если все источники недоступны → вернуть ошибку

### Шаг 4: Формирование результата
1. Для каждого факта:
   - ✅ Verified - факт подтверждён (confidence > 0.95)
   - ❌ Incorrect - факт неверен (предложить корректную альтернативу)
   - 🔄 Corrected - факт частично верен (предложить более точную формулировку)
2. Если есть критичные ошибки:
   - Добавить в `blocking_issues`
   - Установить `status: "rejected"`
3. Если все факты проверены:
   - Установить `status: "approved"`
4. Если есть некритичные замечания:
   - Установить `status: "partial"`

### Шаг 5: Сохранение истории
1. Сохранить результаты в Obsidian vault:
   - Путь: `obsidian/medical-fact-checker/wiki/checks/YYYY-MM-DD-{task_id}.md`
   - Формат: Markdown с frontmatter (дата, content_type, specialty, результаты)
2. Обновить индекс проверенных фактов:
   - Путь: `obsidian/medical-fact-checker/wiki/facts-index.md`
   - Добавить новые проверенные факты для переиспользования

### Шаг 6: Отправка результата
1. Отправить событие `fact_check.completed` через Event Bus
2. Логировать в Event Store с correlation_id
3. Если `status: "rejected"` → эскалировать Operator (событие `escalation.required`)

---

## 🔧 ИНТЕГРАЦИИ

### Внешние сервисы:

**Perplexity API (основной):**
- API endpoint: `https://api.perplexity.ai/chat/completions`
- Аутентификация: API key
- Rate limit: 50 requests/minute (Pro plan)
- Документация: https://docs.perplexity.ai/
- Особенности: Доступ к академическим источникам (PubMed, Google Scholar)

**Google Search API (резервный):**
- API endpoint: `https://www.googleapis.com/customsearch/v1`
- Аутентификация: API key
- Rate limit: 100 queries/day (free tier)
- Документация: https://developers.google.com/custom-search

**Claude Deep Research Skill (резервный):**
- GitHub: https://github.com/199-biotechnologies/claude-deep-research-skill
- Использование: Через Claude Code CLI
- Особенности: Глубокий анализ научных источников

### Внутренние зависимости:

- Event Bus (обязательно) - получение задач, отправка результатов
- Event Store (обязательно) - логирование всех проверок
- Obsidian vault (обязательно) - сохранение истории, индекс фактов
- Teacher Agent (опционально) - обучение и обновление best practices
- Operator (опционально) - эскалация при блокировке публикации

---

## 📊 МЕТРИКИ УСПЕХА

### Качественные метрики:

**Точность проверки:**
- Метрика: Процент правильно проверенных фактов
- Целевое значение: > 95% (идеально > 99%)
- Как измерять: Аудит случайной выборки (когда доступен доктор)

**Полнота проверки:**
- Метрика: Процент найденных медицинских фактов в тексте
- Целевое значение: 100% (все факты должны быть найдены)
- Как измерять: Ручная проверка выборки текстов

### Производительность:

**Скорость:**
- Среднее время выполнения: несколько минут (зависит от количества фактов)
- 95-й перцентиль: < 10 минут
- Максимальное время: < 15 минут

**Надёжность:**
- Success rate: > 95%
- Partial success rate: > 99%
- Failure rate: < 1%

### Бизнес-метрики:

**Влияние на качество:**
- Снижение количества жалоб на неточности (целевое: -80%)
- Увеличение доверия к контенту (измерение: опросы, NPS)
- Экономия времени доктора на проверку (целевое: -50%)

**Примечание:** Бизнес-метрики заложены в систему, но измерение может быть недоступно на старте.

---

## 🧪 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ

### Пример 1: Успешная проверка статьи

**Входные данные:**
```json
{
  "content": "# Отбеливание зубов\n\nПроцедура отбеливания зубов безопасна при правильном применении. Она использует перекись водорода концентрацией 10-35%.",
  "content_type": "article",
  "medical_specialty": ["dentistry"],
  "urgency": "blocking"
}
```

**Выходные данные:**
```json
{
  "status": "approved",
  "result": {
    "facts_checked": [
      {
        "fact": "Процедура отбеливания зубов безопасна при правильном применении",
        "status": "✅ verified",
        "confidence": 0.97,
        "sources": [
          "https://pubmed.ncbi.nlm.nih.gov/12345678",
          "https://scholar.google.com/article/xyz"
        ],
        "specialty_tags": ["dentistry"]
      },
      {
        "fact": "Она использует перекись водорода концентрацией 10-35%",
        "status": "✅ verified",
        "confidence": 0.99,
        "sources": [
          "https://pubmed.ncbi.nlm.nih.gov/87654321"
        ],
        "specialty_tags": ["dentistry"]
      }
    ],
    "summary": {
      "total_facts": 2,
      "verified": 2,
      "incorrect": 0,
      "corrected": 0
    }
  },
  "metrics": {
    "execution_time_ms": 120000,
    "perplexity_queries": 2,
    "sources_checked": 8
  }
}
```

### Пример 2: Частичная проверка с корректировкой

**Входные данные:**
```json
{
  "content": "# Витамин C\n\nВитамин C полностью излечивает простуду за 24 часа.",
  "content_type": "post",
  "medical_specialty": ["general"],
  "urgency": "blocking"
}
```

**Выходные данные:**
```json
{
  "status": "partial",
  "result": {
    "facts_checked": [
      {
        "fact": "Витамин C полностью излечивает простуду за 24 часа",
        "status": "🔄 corrected",
        "confidence": 0.92,
        "sources": [
          "https://pubmed.ncbi.nlm.nih.gov/11111111",
          "https://pubmed.ncbi.nlm.nih.gov/22222222"
        ],
        "alternative": "Витамин C может сократить продолжительность простуды на 8-10%, но не излечивает её полностью",
        "specialty_tags": ["general"]
      }
    ],
    "summary": {
      "total_facts": 1,
      "verified": 0,
      "incorrect": 0,
      "corrected": 1
    }
  },
  "metrics": {
    "execution_time_ms": 90000,
    "perplexity_queries": 1,
    "sources_checked": 12
  },
  "blocking_issues": []
}
```

### Пример 3: Блокировка публикации

**Входные данные:**
```json
{
  "content": "# Лечение рака\n\nСода полностью излечивает рак на любой стадии.",
  "content_type": "article",
  "medical_specialty": ["general"],
  "urgency": "blocking"
}
```

**Выходные данные:**
```json
{
  "status": "rejected",
  "result": {
    "facts_checked": [
      {
        "fact": "Сода полностью излечивает рак на любой стадии",
        "status": "❌ incorrect",
        "confidence": 0.99,
        "sources": [
          "https://pubmed.ncbi.nlm.nih.gov/33333333",
          "https://cancer.org/debunking-myths"
        ],
        "alternative": "Нет научных доказательств эффективности соды в лечении рака. Лечение рака требует профессиональной медицинской помощи.",
        "specialty_tags": ["general"]
      }
    ],
    "summary": {
      "total_facts": 1,
      "verified": 0,
      "incorrect": 1,
      "corrected": 0
    }
  },
  "metrics": {
    "execution_time_ms": 150000,
    "perplexity_queries": 1,
    "sources_checked": 20
  },
  "blocking_issues": [
    {
      "fact": "Сода полностью излечивает рак на любой стадии",
      "reason": "Опасная дезинформация, противоречит медицинскому консенсусу",
      "severity": "critical"
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
- Пример: Пустой content, неизвестный content_type

**Ошибка Perplexity API:**
- Код: `PERPLEXITY_ERROR`
- Действие: Retry с exponential backoff, затем fallback на Google Search
- Retry: До 3 попыток
- Fallback: Google Search API → Claude Deep Research skill

**Ошибка всех источников:**
- Код: `ALL_SOURCES_UNAVAILABLE`
- Действие: Вернуть failure, эскалировать Operator
- Retry: Нет
- Сообщение: "Невозможно проверить факты, все источники недоступны"

**Timeout:**
- Код: `TIMEOUT`
- Действие: Вернуть partial_success с проверенными фактами
- Retry: Нет
- Максимальное время: 15 минут

**Внутренняя ошибка:**
- Код: `INTERNAL_ERROR`
- Действие: Логировать, вернуть failure, эскалировать Operator
- Retry: Нет

### Graceful degradation:

При частичном сбое:
1. Проверить максимум фактов
2. Вернуть partial_success
3. Указать, какие факты не удалось проверить
4. Позволить Content Magister решить, что делать дальше

При критичной ошибке:
1. Вернуть failure
2. Эскалировать Operator (событие `escalation.required`)
3. Блокировать публикацию до ручной проверки

---

## 🧠 ОБУЧЕНИЕ И АДАПТАЦИЯ

### Источники обучения:

**От Teacher Agent:**
- Best practices медицинской проверки
- Обновления медицинских стандартов
- Новые источники для проверки
- Улучшенные промпты для Perplexity

**Из собственного опыта:**
- История проверок в Obsidian
- Успешные кейсы (какие источники были надёжны)
- Неудачные попытки (какие источники оказались ненадёжны)
- Метрики точности проверок

**Из Obsidian vault:**
- Индекс проверенных фактов (`wiki/facts-index.md`)
- Исторические данные проверок (`wiki/checks/`)
- Паттерны и инсайты (`wiki/concepts/`)
- Корреляции с результатами (`wiki/connections/`)

### Адаптация:

**Когда адаптироваться:**
- Появляются новые медицинские данные (автоматически перепроверять старые факты)
- Изменяются медицинские стандарты (периодический пересмотр критериев)
- Метрики точности падают ниже 95%
- Teacher Agent предоставляет обновлённые best practices

**Как адаптироваться:**
1. Teacher Agent по расписанию обучает агента:
   - Читает историю проверок из Obsidian
   - Анализирует успешные/неудачные кейсы
   - Обновляет промпты для Perplexity
   - Обновляет список надёжных источников
2. При появлении новых данных:
   - Автоматически перепроверять факты из индекса
   - Обновлять статус фактов в `wiki/facts-index.md`
   - Уведомлять Content Magister о потенциально устаревших материалах (опционально)
3. Периодический пересмотр (раз в квартал):
   - Teacher Agent проверяет актуальность критериев
   - Обновляет правила проверки
   - Тестирует на контрольной выборке

### Специализация по направлениям:

**Тегирование фактов:**
- Каждый факт тегируется по специальностям: `["dentistry", "cosmetology", "general"]`
- Мультидисциплинарные факты имеют несколько тегов
- Teacher Agent может обучать специфичным правилам для каждой специальности

**Примеры:**
- Факт "Отбеливание зубов безопасно" → `["dentistry"]`
- Факт "Стресс влияет на кожу" → `["cosmetology", "general"]`
- Факт "Витамин C укрепляет иммунитет" → `["general"]`

---

## 📝 ЛОГИРОВАНИЕ

### Что логировать:

**В Event Store (обязательно):**
- Все входящие события `fact_check.requested`
- Все исходящие события `fact_check.completed`
- Все эскалации `escalation.required`
- Correlation ID для трейсинга

**В Obsidian vault (обязательно):**
- Результаты каждой проверки (`wiki/checks/YYYY-MM-DD-{task_id}.md`)
- Индекс проверенных фактов (`wiki/facts-index.md`)
- Метрики производительности (`wiki/log.md`)
- Инсайты и паттерны (`wiki/concepts/`)

**В системные логи (опционально):**
- Debug информация (запросы к Perplexity, источники)
- Ошибки и warnings (недоступность API, timeout)
- Performance traces (время выполнения каждого шага)

### Формат логов:

```
[YYYY-MM-DD HH:MM:SS] [LEVEL] [medical-fact-checker] [correlation_id] Message
```

**Пример:**
```
[2026-05-09 14:30:15] [INFO] [medical-fact-checker] [abc-123] Received fact_check.requested for article
[2026-05-09 14:30:16] [DEBUG] [medical-fact-checker] [abc-123] Extracted 5 medical facts
[2026-05-09 14:32:45] [INFO] [medical-fact-checker] [abc-123] Completed fact check: 5 verified, 0 incorrect
[2026-05-09 14:32:46] [INFO] [medical-fact-checker] [abc-123] Sent fact_check.completed
```

---

## 🧪 ТЕСТИРОВАНИЕ

### Unit тесты:

**Покрытие:** > 80%

**Обязательные тесты:**
- Валидация входных данных (пустой content, неизвестный content_type)
- Извлечение медицинских фактов из текста
- Парсинг результатов Perplexity
- Формирование результата проверки
- Обработка ошибок API (Perplexity недоступен, timeout)
- Сохранение в Obsidian vault

### Integration тесты:

**Обязательные сценарии:**
- Получение задачи от Content Orchestrator через Event Bus
- Отправка результата Content Orchestrator через Event Bus
- Логирование в Event Store
- Сохранение в Obsidian vault
- Эскалация Operator при блокировке публикации

### E2E тесты:

**Обязательные сценарии:**
- Полный цикл: задача → извлечение фактов → проверка → результат
- Проверка с Perplexity (mock API)
- Fallback на Google Search при недоступности Perplexity
- Блокировка публикации при критичных ошибках
- Graceful degradation при частичном сбое

**Тестовые кейсы:**
- Статья с правильными фактами → approved
- Статья с неправильными фактами → rejected + blocking_issues
- Статья с частично верными фактами → partial + corrected
- Статья без медицинских фактов → approved (пустой список)
- Perplexity недоступен → fallback на Google Search
- Все источники недоступны → failure + escalation

---

## 🚀 DEPLOYMENT

### Требования:

**Окружение:**
- Python 3.11+
- Event Bus доступен
- Event Store доступен
- Obsidian vault доступен (`obsidian/medical-fact-checker/`)

**Зависимости:**
- `httpx >= 0.24.0` (для API запросов)
- `pydantic >= 2.0.0` (для валидации данных)
- `markdown >= 3.4.0` (для парсинга Markdown)
- `python-frontmatter >= 1.0.0` (для работы с Obsidian frontmatter)

**Конфигурация:**
```env
SUBAGENT_ID=medical-fact-checker
EVENT_BUS_URL=...
EVENT_STORE_URL=...
OBSIDIAN_VAULT_PATH=./obsidian/medical-fact-checker
PERPLEXITY_API_KEY=...
GOOGLE_SEARCH_API_KEY=...
GOOGLE_SEARCH_ENGINE_ID=...
```

### Мониторинг:

**Метрики для алертов:**
- Success rate < 95% → Warning
- Success rate < 90% → Critical
- Avg execution time > 10 minutes → Warning
- 95th percentile > 15 minutes → Critical
- Perplexity API errors > 10% → Warning
- All sources unavailable → Critical (эскалация Operator)

**Дашборд метрик:**
- Количество проверок в день
- Процент approved / partial / rejected
- Среднее время проверки
- Количество блокировок публикации
- Топ-10 проверенных фактов
- Топ-10 источников

---

## 📚 СВЯЗАННЫЕ ДОКУМЕНТЫ

### Спецификации:
- `CONTENT_MAGISTER_SPEC.md` - Спецификация родительского Magister
- `CONTENT_ORCHESTRATOR_SPEC.md` - Спецификация родительского Orchestrator (TODO)
- `TEACHER_AGENT_SPEC.md` - Спецификация Teacher Agent (TODO)

### Код:
- `AIM/src/aim/subagents/content/medical_fact_checker.py` - Реализация (TODO)
- `AIM/tests/subagents/content/test_medical_fact_checker.py` - Тесты (TODO)

### Документация:
- Event Bus API
- Event Store API
- Obsidian integration guide
- Perplexity API documentation: https://docs.perplexity.ai/

### Obsidian Vault:
- `obsidian/medical-fact-checker/wiki/checks/` - История проверок
- `obsidian/medical-fact-checker/wiki/facts-index.md` - Индекс проверенных фактов
- `obsidian/medical-fact-checker/wiki/log.md` - Операционная история

---

**Дата создания:** 2026-05-09  
**Автор:** Mikhail Eliseev (via meAI Architect)  
**Версия:** 1.0  
**Статус:** Ready

**Критичность:** ⭐⭐⭐⭐⭐ (P0 - блокирует запуск системы)  
**Причина:** Дело касается здоровья человека. Непроверенная информация может привести к летальному исходу.
