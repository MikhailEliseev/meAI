# Content Scheduler Agent - Спецификация

**Версия:** 1.0  
**Дата создания:** 2026-05-09  
**Автор:** Mikhail Eliseev (via meAI Architect)  
**Статус:** Draft  
**Приоритет:** P1 (Критичный)

---

## 1. ОБЗОР

### 1.1 Назначение

**Content Scheduler Agent** — автономный контент-менеджер, который получает готовый контент от других агентов, формирует контент-план, получает утверждение от пользователя и публикует контент по расписанию во все каналы (соцсети, блог, мессенджеры).

### 1.2 Роль в системе

**Родительский Magister:** Social Magister  
**Тип:** Execution Subagent  
**Домен:** Social Media Management, Content Publishing, Scheduling

### 1.3 Уникальная ценность

Content Scheduler Agent позволяет:
- **Централизованное управление публикациями** — один контент-план для всех каналов
- **Автоматизация публикаций** — контент публикуется по расписанию без ручной работы
- **Контроль и прозрачность** — пользователь видит весь контент-план и статусы публикаций
- **Гибкость** — можно изменить контент-план после утверждения (добавить/удалить/перенести)

**Критичность:** Без Content Scheduler контент создаётся, но не публикуется → нет результата, нет статистики, нет трафика.

### 1.4 Границы ответственности

**Что делает:**
- Получает готовый контент от агентов (Content Magister, Trend Watcher, Blog Content Agent, etc.)
- Формирует контент-план (календарь публикаций)
- Отправляет контент-план на утверждение пользователю (через Operator)
- Публикует контент по расписанию после утверждения
- Следит за статусом публикаций (опубликовано/ошибка/отложено/в очереди)
- Retry при ошибках публикации (10 попыток)
- Уведомляет пользователя о проблемах (через Telegram бот, раз в день вечером)

**Что НЕ делает:**
- Не создаёт контент (это задача Content Magister и его копирайтеров)
- Не монтирует ролики (это задача монтажёра)
- Не пишет тексты (это задача Blog Content Agent, Landing Content Agent, etc.)
- Не анализирует эффективность публикаций (это задача Analytics Magister)

---

## 2. ВХОДНЫЕ ДАННЫЕ

### 2.1 Источники данных

**Основные источники контента:**
- **Content Magister** — статьи для блога, тексты для лендингов
- **Trend Watcher Agent** — сценарии и ролики для соцсетей
- **Blog Content Agent** — статьи для блога
- **Landing Content Agent** — тексты для лендингов
- **AI Sales Admin Agent** — посты для соцсетей

**Дополнительные источники:**
- **Пользователь** — ручное добавление контента в контент-план
- **Стратегический блок + клиент** — расписание публикаций (когда публиковать)

### 2.2 Обязательные параметры

```python
class ContentSchedulerInput(BaseModel):
    content_items: list[ContentItem]  # Список контента для публикации
    schedule_strategy: str = "auto"  # Стратегия расписания (auto/manual)
    approval_required: bool = True  # Требуется утверждение контент-плана
    notification_time: str = "20:00"  # Время ежедневного уведомления (GMT+3)

class ContentItem(BaseModel):
    content_id: str  # ID контента
    content_type: str  # Тип: post, article, video, story, reel
    content_text: str  # Текст поста/статьи
    content_media: list[str] = []  # Медиафайлы (URLs или paths)
    target_channels: list[str]  # Каналы: instagram, youtube, telegram, vk, dzen, blog, etc.
    scheduled_time: datetime | None = None  # Время публикации (если manual)
    priority: int = 1  # Приоритет (1-5, где 5 = высокий)
    source_agent: str  # Агент-источник контента
```

### 2.3 Опциональные параметры

```python
class ContentSchedulerOptionalInput(BaseModel):
    content_plan_tool: str = "airtable"  # Инструмент для контент-плана (airtable/notion/google_sheets)
    retry_attempts: int = 10  # Количество попыток retry при ошибке
    retry_interval_minutes: int = 5  # Интервал между попытками
    optimal_times: dict[str, list[str]] = {
        "instagram": ["08:00-09:00", "18:00-20:00"],  # Утро и вечер (пики активности)
        "youtube": ["12:00-14:00", "19:00-21:00"],
        "telegram": ["09:00-10:00", "20:00-22:00"]
    }
```

### 2.4 Валидация входных данных

**Правила валидации:**
- `content_items` не может быть пустым списком
- Каждый `ContentItem` должен иметь `content_text` или `content_media`
- `target_channels` не может быть пустым списком
- `scheduled_time` должен быть в будущем (если указан)
- `notification_time` должен быть в формате HH:MM

**Обработка ошибок валидации:**
- Если валидация не прошла → вернуть `INVALID_INPUT` с описанием ошибки
- Логировать в Event Store
- Не формировать контент-план

---

## 3. АЛГОРИТМ РАБОТЫ

### 3.1 Основные шаги

**Шаг 1: Получение готового контента**
- Получить список контента от агентов через Event Bus
- Валидировать каждый `ContentItem`
- Сохранить контент в базу данных со статусом `pending_schedule`
- Логировать в Event Store

**Шаг 2: Формирование контент-плана**
- Определить оптимальное время публикации для каждого контента:
  - Если `scheduled_time` указан вручную → использовать его
  - Если `schedule_strategy = "auto"` → определить по `optimal_times` для каждого канала
  - Учитывать приоритет контента (высокий приоритет → раньше)
- Создать контент-план в выбранном инструменте (Airtable/Notion/Google Sheets):
  - Календарь публикаций (дата, время, канал, контент)
  - Статусы для каждой публикации (pending_approval, approved, published, failed, cancelled)
  - Возможность редактирования (добавить/удалить/перенести)
- Сохранить контент-план в Obsidian (`wiki/content_plans/`)

**Шаг 3: Отправка контент-плана на утверждение**
- Отправить контент-план пользователю через Operator
- Формат: ссылка на Airtable/Notion/Google Sheets с календарём
- Пользователь может:
  - Утвердить весь план
  - Отправить на правку (указать, что изменить)
  - Удалить/добавить/перенести публикации
- Ждать утверждения (статус `pending_approval`)

**Шаг 4: Публикация контента по расписанию**
- После утверждения контент-плана:
  - Изменить статус на `approved`
  - Запланировать публикации по расписанию
- В назначенное время для каждой публикации:
  - Получить контент из базы данных
  - Опубликовать через API соответствующего канала
  - Обновить статус на `published` (если успешно) или `failed` (если ошибка)
  - Логировать в Event Store

**Шаг 5: Мониторинг статусов публикаций**
- Отслеживать статус каждой публикации в реальном времени
- Обновлять статусы в контент-плане (Airtable/Notion/Google Sheets)
- Сохранять историю в Obsidian (`wiki/publications/`)

**Шаг 6: Обработка ошибок и retry**
- Если публикация не удалась:
  - Retry 10 раз с интервалом 5 минут
  - Если все попытки исчерпаны → изменить статус на `failed`
  - Уведомить пользователя (через Telegram бот, раз в день вечером)
- Логировать все ошибки в Event Store

**Шаг 7: Ежедневные уведомления**
- Раз в день вечером (по умолчанию 20:00 GMT+3):
  - Собрать статистику за день (опубликовано/ошибки/отложено)
  - Отправить уведомление пользователю через Telegram бот
  - Формат: "Сегодня опубликовано: 5, ошибок: 2, в очереди: 3"

### 3.2 Специфичная логика

**Определение оптимального времени публикации:**
- Анализ активности аудитории (если есть статистика)
- Использование `optimal_times` для каждого канала:
  - Instagram: утро (08:00-09:00) и вечер (18:00-20:00)
  - YouTube: обед (12:00-14:00) и вечер (19:00-21:00)
  - Telegram: утро (09:00-10:00) и вечер (20:00-22:00)
- Распределение публикаций равномерно (не все в одно время)

**Приоритизация публикаций:**
- Если несколько постов на одно время в один канал:
  - Публиковать по приоритету (5 → 1)
  - Сдвигать низкоприоритетные на +15 минут
- Если несколько постов на одно время в разные каналы:
  - Публиковать параллельно (без конфликтов)

**Обработка дубликатов:**
- Проверять, не был ли этот контент уже опубликован
- Если дубликат → пропустить публикацию, уведомить пользователя

### 3.3 Внешние API

**Социальные сети:**
- **Instagram Graph API** — публикация постов, stories, reels
- **YouTube Data API v3** — публикация shorts, videos
- **Telegram Bot API** — публикация в каналы/группы
- **VK API** — публикация постов
- **Яндекс.Дзен API** — публикация статей

**Блог и сайт:**
- **WordPress API** — публикация статей в блог
- **Bitrix24 API** — обновление контента на сайте

**Контент-план:**
- **Airtable API** — создание и обновление контент-плана
- **Notion API** — альтернатива Airtable
- **Google Sheets API** — альтернатива Airtable

**Fallback (если API недоступен):**
- **Post My Post** — сторонний сервис для публикации в соцсети
- **Buffer API** — альтернативный сервис

---

## 4. ВЫХОДНЫЕ ДАННЫЕ

### 4.1 Формат результата

```python
class ContentSchedulerResult(BaseModel):
    status: Literal["success", "partial", "failed"]
    content_plan_url: str  # URL контент-плана (Airtable/Notion/Google Sheets)
    publications_total: int  # Всего публикаций в плане
    publications_approved: int  # Утверждено пользователем
    publications_published: int  # Опубликовано
    publications_failed: int  # Ошибки
    publications_pending: int  # В очереди
    publications: list[PublicationStatus]  # Статусы всех публикаций
    metrics: ContentSchedulerMetrics
    errors: list[str] = []

class PublicationStatus(BaseModel):
    content_id: str
    content_type: str
    target_channel: str
    scheduled_time: datetime
    actual_publish_time: datetime | None
    status: Literal["pending_approval", "approved", "published", "failed", "cancelled"]
    error_message: str | None = None
    retry_attempts: int = 0
    post_url: str | None = None  # URL опубликованного поста (если успешно)

class ContentSchedulerMetrics(BaseModel):
    execution_time_ms: int
    content_items_received: int
    publications_scheduled: int
    api_calls_made: int
    retry_attempts_total: int
```

### 4.2 Сохранение результатов

**База данных:**
```sql
CREATE TABLE content_plan (
    id INTEGER PRIMARY KEY,
    content_id TEXT NOT NULL,
    content_type TEXT NOT NULL,
    content_text TEXT,
    target_channel TEXT NOT NULL,
    scheduled_time TIMESTAMP NOT NULL,
    actual_publish_time TIMESTAMP,
    status TEXT NOT NULL,  -- pending_approval, approved, published, failed, cancelled
    error_message TEXT,
    retry_attempts INTEGER DEFAULT 0,
    post_url TEXT,
    source_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_status_time (status, scheduled_time),
    INDEX idx_channel_time (target_channel, scheduled_time)
);

CREATE TABLE publication_history (
    id INTEGER PRIMARY KEY,
    content_id TEXT NOT NULL,
    target_channel TEXT NOT NULL,
    published_at TIMESTAMP NOT NULL,
    post_url TEXT,
    views INTEGER,
    likes INTEGER,
    comments INTEGER,
    INDEX idx_content_channel (content_id, target_channel)
);
```

**Obsidian vault:**
```
obsidian/social-magister/
├── raw/
│   └── content_items/
│       └── {content_id}_{date}.md
├── wiki/
│   ├── content_plans/
│   │   └── plan_{week}_{year}.md
│   ├── publications/
│   │   └── {channel}_{date}.md
│   └── sources/
│       └── scheduler_log_{date}.md
```

---

## 5. МЕТРИКИ КАЧЕСТВА

### 5.1 Производительность

**Success rate:**
- Целевое значение: > 95%
- Warning: < 95%
- Critical: < 90%

**Execution time:**
- Целевое значение: < 5 секунд на 1 публикацию
- Warning: > 10 секунд
- Critical: > 30 секунд

### 5.2 Качественные метрики

**Процент успешных публикаций:**
- Целевое значение: > 95% (из запланированных)
- Измерение: `(published / total_scheduled) * 100`
- Warning: < 95%
- Critical: < 90%

**Соблюдение расписания:**
- Целевое значение: публикация в точное время ±5 минут
- Измерение: `|actual_publish_time - scheduled_time|`
- Warning: > 5 минут
- Critical: > 15 минут

**Скорость реакции на ошибки:**
- Целевое значение: retry в течение 5 минут
- Уведомление пользователя: в течение 24 часов (ежедневное уведомление)

### 5.3 Мониторинг

**Алерты:**
- Success rate < 95% → Warning
- Success rate < 90% → Critical
- Публикация опоздала > 15 минут → Warning
- API недоступен > 1 час → Critical
- Все retry исчерпаны → Critical

**Дашборд метрик:**
- Количество публикаций в день
- Процент success / failed / pending
- Среднее время публикации
- Топ-10 ошибок
- Статистика по каналам (какой канал чаще падает)
---

## 6. ИНТЕГРАЦИИ

### 6.1 Event Bus

**Получение задач от Social Magister:**
```json
{
  "event_type": "social.content_scheduling.requested",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "content-scheduler",
  "payload": {
    "content_items": [/* ContentItem objects */],
    "schedule_strategy": "auto",
    "approval_required": true
  }
}
```

**Отправка результатов Social Magister:**
```json
{
  "event_type": "social.content_scheduling.completed",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "content-scheduler",
  "payload": {
    "status": "success",
    "result": {
      "content_plan_url": "https://airtable.com/...",
      "publications_total": 15,
      "publications_approved": 15,
      "publications_published": 12,
      "publications_failed": 2,
      "publications_pending": 1
    },
    "metrics": {
      "execution_time_ms": 3500,
      "content_items_received": 15,
      "publications_scheduled": 15
    }
  }
}
```

### 6.2 Event Store

**Логирование всех событий:**
- `social.content_scheduling.requested` — получена задача
- `social.content_scheduling.completed` — задача завершена
- `social.content_scheduling.failed` — задача провалена
- `social.publication.published` — контент опубликован
- `social.publication.failed` — публикация не удалась
- `escalation.required` — эскалация критичной ошибки

**Формат записи:**
```json
{
  "event_id": "uuid",
  "event_type": "social.publication.published",
  "correlation_id": "uuid",
  "timestamp": "2026-05-09T22:30:00Z",
  "subagent_id": "content-scheduler",
  "payload": {
    "content_id": "content-123",
    "target_channel": "instagram",
    "post_url": "https://instagram.com/p/...",
    "scheduled_time": "2026-05-09T22:30:00Z",
    "actual_publish_time": "2026-05-09T22:30:03Z"
  }
}
```

### 6.3 Obsidian Vault

**Путь:** `obsidian/social-magister/`

**Операции:**
- **Ingest:** Сохранение контента и контент-планов в `raw/`
- **Query:** Чтение истории публикаций для анализа
- **Lint:** Проверка противоречий, устаревших данных

**Специальные файлы:**
- `wiki/log.md` — хронология всех операций
- `wiki/index.md` — каталог всех контент-планов
- `wiki/content_plans/plan_{week}_{year}.md` — контент-план на неделю

### 6.4 Database

**Таблицы:**
- `content_plan` — контент-план и статусы публикаций
- `publication_history` — история опубликованного контента

**Операции:**
- INSERT: сохранение нового контента в план
- SELECT: чтение контент-плана для публикации
- UPDATE: обновление статусов публикаций

### 6.5 Teacher Agent

**Интеграция:**
- Teacher Agent читает `wiki/log.md` и `wiki/publications/`
- Анализирует успешные/неудачные публикации
- Оптимизирует `optimal_times` для каждого канала
- Улучшает стратегию retry

**Частота обучения:**
- Периодический пересмотр: раз в квартал
- Адаптация: при падении success rate < 90%

### 6.6 Внешние API

**Социальные сети:**
- Instagram Graph API, YouTube Data API v3, Telegram Bot API, VK API, Яндекс.Дзен API

**Блог и сайт:**
- WordPress API, Bitrix24 API

**Контент-план:**
- Airtable API, Notion API, Google Sheets API

**Fallback:**
- Post My Post, Buffer API

---

## 7. ОБРАБОТКА ОШИБОК

### 7.1 Стандартные ошибки

**INVALID_INPUT:**
- Причина: Пустой список `content_items`, неверные параметры
- Действие: Вернуть failure сразу
- Retry: Нет
- Логирование: Event Store + системные логи

**API_ERROR:**
- Причина: Временная недоступность API (Instagram, YouTube, etc.)
- Действие: Retry с exponential backoff (10 попыток, 5 минут интервал)
- Если все попытки исчерпаны → изменить статус на `failed`, уведомить пользователя
- Логирование: Event Store + системные логи

**TIMEOUT:**
- Причина: Превышено максимальное время выполнения (30 секунд на публикацию)
- Действие: Вернуть partial_success, пометить публикацию как `failed`
- Retry: Нет
- Логирование: Event Store + Obsidian

**INTERNAL_ERROR:**
- Причина: Внутренняя ошибка агента (баг в коде)
- Действие: Логировать, вернуть failure, эскалировать
- Retry: Нет
- Эскалация: Social Magister → Operator → User

### 7.2 Специфичные ошибки

**API_UNAVAILABLE:**
- Причина: API платформы недоступен (Instagram down, YouTube down)
- Действие:
  1. Retry 10 раз с интервалом 5 минут
  2. Если все попытки исчерпаны → использовать fallback (Post My Post, Buffer)
  3. Если fallback не помог → изменить статус на `failed`
  4. Уведомить пользователя (через Telegram бот, раз в день вечером)
- Retry: 10 попыток
- Эскалация: Warning (если > 1 час)

**CONTENT_MODERATION_FAILED:**
- Причина: Контент не прошёл модерацию платформы (Instagram заблокировал пост)
- Действие:
  1. Изменить статус на `failed`
  2. Сохранить причину блокировки
  3. Уведомить пользователя немедленно (критичная ошибка)
  4. Не retry (модерация не пройдёт повторно)
- Retry: Нет
- Эскалация: Critical

**DUPLICATE_PUBLICATION:**
- Причина: Тот же контент уже был опубликован в этот канал
- Действие:
  1. Пропустить публикацию
  2. Изменить статус на `cancelled`
  3. Уведомить пользователя (через ежедневное уведомление)
- Retry: Нет
- Логирование: Event Store + Obsidian

**CONTENT_PLAN_NOT_APPROVED:**
- Причина: Контент-план не утверждён пользователем
- Действие:
  1. Не публиковать контент
  2. Ждать утверждения
  3. Напомнить пользователю через 24 часа (если не утверждён)
- Retry: Нет
- Логирование: Event Store

**SCHEDULED_TIME_PASSED:**
- Причина: Запланированное время публикации уже прошло (агент был недоступен)
- Действие:
  1. Опубликовать немедленно (если < 1 часа прошло)
  2. Пропустить публикацию (если > 1 часа прошло)
  3. Уведомить пользователя
- Retry: Нет
- Логирование: Event Store + Obsidian

### 7.3 Эскалация

**Путь эскалации:**
```
Content Scheduler → Social Magister → Operator → User → Architect
```

**Когда эскалировать:**
- API недоступен > 1 час (Warning)
- Success rate < 90% в течение 3 дней (Critical)
- Контент не прошёл модерацию (Critical)
- Внутренняя ошибка агента (Critical)

**Формат эскалации:**
```json
{
  "event_type": "escalation.required",
  "correlation_id": "uuid",
  "source": "content-scheduler",
  "severity": "critical",
  "payload": {
    "error_type": "CONTENT_MODERATION_FAILED",
    "message": "Instagram blocked post due to policy violation",
    "context": {
      "content_id": "content-123",
      "target_channel": "instagram",
      "moderation_reason": "Spam detected"
    },
    "escalation_path": ["Social Magister", "Operator", "User"]
  }
}
```

### 7.4 Graceful Degradation

**При частичном сбое:**
1. Выполнить максимум возможного
2. Вернуть `partial_success`
3. Указать, что не удалось выполнить
4. Уведомить Social Magister

**Примеры:**
- Если Instagram API недоступен → опубликовать в остальные каналы (YouTube, Telegram, etc.)
- Если Airtable API недоступен → использовать Google Sheets для контент-плана
- Если все API недоступны → сохранить контент в очередь, попробовать позже

---

## 8. ОБУЧЕНИЕ И АДАПТАЦИЯ

### 8.1 Интеграция с Teacher Agent

**Что Teacher Agent предоставляет:**
- Оптимизированные `optimal_times` для каждого канала (на основе статистики)
- Улучшенную стратегию retry (сколько попыток, какой интервал)
- Рекомендации по приоритизации публикаций
- Паттерны успешных публикаций

**Как Content Scheduler обучается:**
1. Teacher Agent читает `wiki/log.md` и `wiki/publications/`
2. Анализирует успешные публикации (высокий engagement)
3. Анализирует неудачные публикации (ошибки, низкий engagement)
4. Создаёт обновлённые инструкции
5. Content Scheduler применяет новые инструкции
6. Тестирует на контрольной выборке (10 публикаций)
7. Сохраняет результаты в Obsidian

**Частота обучения:**
- Периодический пересмотр: раз в квартал
- Экстренное обучение: при падении success rate < 90%
- Адаптация: при изменении алгоритмов соцсетей

### 8.2 История в Obsidian

**Структура:**
```
obsidian/social-magister/wiki/
├── log.md                    # Хронология операций
├── concepts/
│   ├── optimal_times.md      # Оптимальное время публикаций
│   ├── successful_posts.md   # Успешные публикации
│   └── failed_posts.md       # Неудачные публикации
├── strategies/
│   └── scheduling_strategy.md # Стратегии планирования
└── connections/
    └── channel_correlations.md # Связи между каналами
```

**Формат log.md:**
```markdown
## [2026-05-09 22:30] publication | Published post to Instagram, 50K views in 24h
## [2026-05-09 22:35] publication_failed | YouTube API unavailable, retry in 5 min
## [2026-05-09 23:00] content_plan_approved | User approved 15 publications for next week
```

### 8.3 Адаптация

**Автоматическая адаптация:**
- Если success rate < 90% → запросить обучение у Teacher Agent
- Если новый канал добавлен → Teacher Agent определяет `optimal_times`
- Если изменились алгоритмы соцсетей → Teacher Agent обновляет стратегию

**Ручная адаптация:**
- Пользователь может изменить `optimal_times` через Social Magister
- Пользователь может изменить `retry_attempts` для калибровки
- Пользователь может добавить новые каналы (TikTok, LinkedIn, etc.)

---

## 9. ЛОГИРОВАНИЕ

### 9.1 Event Store (обязательно)

**Логируемые события:**
- `social.content_scheduling.requested` — получена задача
- `social.content_scheduling.completed` — задача завершена
- `social.content_scheduling.failed` — задача провалена
- `social.publication.published` — контент опубликован
- `social.publication.failed` — публикация не удалась
- `escalation.required` — эскалация критичной ошибки

**Формат:**
```json
{
  "event_id": "uuid",
  "event_type": "social.publication.published",
  "correlation_id": "uuid",
  "timestamp": "2026-05-09T22:30:00Z",
  "subagent_id": "content-scheduler",
  "payload": {
    "content_id": "content-123",
    "target_channel": "instagram",
    "post_url": "https://instagram.com/p/...",
    "scheduled_time": "2026-05-09T22:30:00Z",
    "actual_publish_time": "2026-05-09T22:30:03Z"
  }
}
```

### 9.2 Obsidian Vault (обязательно)

**История операций (`wiki/log.md`):**
```markdown
## [2026-05-09 22:30] publication | Published post to Instagram, content_id: content-123
## [2026-05-09 22:35] publication_failed | YouTube API unavailable, retry attempt 1/10
## [2026-05-09 23:00] content_plan_approved | User approved 15 publications for next week
```

**Результаты работы:**
- `wiki/content_plans/` — контент-планы на неделю/месяц
- `wiki/publications/` — история публикаций по каналам
- `wiki/sources/` — сводки по публикациям

**Метрики производительности:**
- `wiki/metrics/success_rate.md` — процент успешных публикаций
- `wiki/metrics/channel_stats.md` — статистика по каналам

### 9.3 Системные логи (опционально)

**Debug информация:**
- API запросы и ответы
- Retry попытки
- Время выполнения каждой публикации

**Ошибки и warnings:**
- Ошибки API
- Таймауты
- Модерация контента

**Формат:**
```
[2026-05-09 22:30:00] [INFO] [content-scheduler] [correlation-id-123] Publishing to Instagram: content-123
[2026-05-09 22:30:03] [INFO] [content-scheduler] [correlation-id-123] Published successfully: https://instagram.com/p/...
[2026-05-09 22:35:00] [ERROR] [content-scheduler] [correlation-id-124] YouTube API unavailable, retry 1/10
```

---

## 10. ТЕСТИРОВАНИЕ

### 10.1 Unit тесты

**Покрытие:** > 80%

**Обязательные тесты:**
- Валидация входных данных (`test_validate_input`)
- Определение оптимального времени (`test_determine_optimal_time`)
- Приоритизация публикаций (`test_prioritize_publications`)
- Обработка ошибок API (`test_api_error_handling`)
- Retry механизм (`test_retry_with_backoff`)
- Сохранение в БД (`test_save_to_database`)
- Сохранение в Obsidian (`test_save_to_obsidian`)
- Формирование результата (`test_format_result`)

**Примеры:**
```python
def test_determine_optimal_time():
    content_item = ContentItem(
        content_type="post",
        target_channels=["instagram"],
        scheduled_time=None
    )
    optimal_times = {"instagram": ["08:00-09:00", "18:00-20:00"]}
    
    result = determine_optimal_time(content_item, optimal_times)
    assert result.hour in [8, 18, 19, 20]

def test_prioritize_publications():
    items = [
        ContentItem(priority=1, content_id="low"),
        ContentItem(priority=5, content_id="high"),
        ContentItem(priority=3, content_id="medium")
    ]
    
    result = prioritize_publications(items)
    assert result[0].content_id == "high"
    assert result[1].content_id == "medium"
    assert result[2].content_id == "low"
```

### 10.2 Integration тесты

**Обязательные сценарии:**
- Получение задачи через Event Bus (`test_receive_task_from_event_bus`)
- Отправка результата через Event Bus (`test_send_result_to_event_bus`)
- Логирование в Event Store (`test_log_to_event_store`)
- Сохранение в Obsidian vault (`test_save_to_obsidian_vault`)
- Сохранение в базу данных (`test_save_to_database`)
- Эскалация при критичных ошибках (`test_escalation_on_critical_error`)
- Интеграция с Instagram API (`test_instagram_integration`)
- Интеграция с YouTube API (`test_youtube_integration`)
- Интеграция с Airtable API (`test_airtable_integration`)

### 10.3 E2E тесты

**Обязательные сценарии:**
- Полный цикл: контент → контент-план → утверждение → публикация → статус (`test_full_cycle`)
- Частичный сбой (graceful degradation): Instagram API недоступен, но YouTube опубликован (`test_partial_failure`)
- Критичная ошибка (escalation): контент не прошёл модерацию (`test_moderation_failure`)
- Retry механизм при временных сбоях API (`test_retry_on_api_error`)
- Изменение контент-плана после утверждения (`test_modify_approved_plan`)

**Пример E2E теста:**
```python
async def test_full_cycle():
    # 1. Создать контент
    content_items = [
        ContentItem(
            content_id="test-123",
            content_type="post",
            content_text="Test post",
            target_channels=["instagram"],
            scheduled_time=datetime.now() + timedelta(minutes=5)
        )
    ]
    
    # 2. Отправить задачу через Event Bus
    await event_bus.publish("social.content_scheduling.requested", {
        "content_items": content_items,
        "approval_required": True
    })
    
    # 3. Дождаться формирования контент-плана
    result = await event_bus.subscribe("social.content_scheduling.completed")
    assert result["status"] == "success"
    assert result["content_plan_url"] is not None
    
    # 4. Утвердить контент-план (симуляция пользователя)
    await approve_content_plan(result["content_plan_url"])
    
    # 5. Дождаться публикации
    await asyncio.sleep(300)  # Ждём 5 минут
    
    # 6. Проверить статус публикации
    db_record = await database.query(
        "SELECT * FROM content_plan WHERE content_id = ?",
        "test-123"
    )
    assert db_record["status"] == "published"
    assert db_record["post_url"] is not None
```

---

## 11. DEPLOYMENT

### 11.1 Требования

**Окружение:**
- Python 3.11+
- Event Bus доступен
- Event Store доступен
- Obsidian vault доступен (`obsidian/social-magister/`)
- Database доступна (`data/aim.db`)

**Зависимости:**
```txt
httpx >= 0.24.0              # API запросы
pydantic >= 2.0.0            # Валидация данных
sqlalchemy >= 2.0.0          # База данных
python-frontmatter >= 1.0.0  # Obsidian frontmatter
schedule >= 1.2.0            # Планирование публикаций
pytz >= 2023.3               # Работа с таймзонами
```

### 11.2 Конфигурация (.env)

```env
SUBAGENT_ID=content-scheduler
EVENT_BUS_URL=...
EVENT_STORE_URL=...
OBSIDIAN_VAULT_PATH=./obsidian/social-magister
DATABASE_URL=sqlite+aiosqlite:///./data/aim.db

# Instagram API
INSTAGRAM_ACCESS_TOKEN=...
INSTAGRAM_BUSINESS_ACCOUNT_ID=...

# YouTube API
YOUTUBE_API_KEY=...
YOUTUBE_CHANNEL_ID=...

# Telegram Bot API
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHANNEL_ID=...

# VK API
VK_ACCESS_TOKEN=...
VK_GROUP_ID=...

# Яндекс.Дзен API
DZEN_API_KEY=...

# WordPress API
WORDPRESS_URL=...
WORDPRESS_USERNAME=...
WORDPRESS_PASSWORD=...

# Airtable API
AIRTABLE_API_KEY=...
AIRTABLE_BASE_ID=...

# Настройки планирования
CONTENT_PLAN_TOOL=airtable  # airtable/notion/google_sheets
RETRY_ATTEMPTS=10
RETRY_INTERVAL_MINUTES=5
NOTIFICATION_TIME=20:00  # GMT+3
```

### 11.3 Мониторинг

**Метрики для алертов:**
- Success rate < 95% → Warning
- Success rate < 90% → Critical
- Публикация опоздала > 15 минут → Warning
- API недоступен > 1 час → Critical
- Контент не прошёл модерацию → Critical

**Дашборд метрик:**
- Количество публикаций в день
- Процент success / failed / pending
- Среднее время публикации
- Топ-10 ошибок
- Статистика по каналам (какой канал чаще падает)
- Соблюдение расписания (±5 минут)

---

**Дата создания:** 2026-05-09  
**Автор:** Mikhail Eliseev (via meAI Architect)  
**Статус:** Draft  
**Версия:** 1.0
