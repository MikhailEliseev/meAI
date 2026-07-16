# Trend Watcher Agent - Спецификация

**Версия:** 1.0  
**Дата создания:** 2026-05-09  
**Автор:** Mikhail Eliseev (via meAI Architect)  
**Статус:** Draft  
**Приоритет:** P1 (⭐⭐⭐ Критичный)

---

## 1. ОБЗОР

### 1.1 Назначение

**Trend Watcher Agent** — автономный агент для мониторинга трендов в социальных сетях (Instagram, YouTube Shorts), анализа виральных роликов конкурентов и генерации ТЗ для создания собственного контента на основе обнаруженных трендов.

### 1.2 Роль в системе

**Родительский Magister:** Social Magister  
**Тип:** Execution Subagent  
**Домен:** Social Media Marketing, Trend Analysis, Content Strategy

### 1.3 Уникальная ценность

Trend Watcher Agent позволяет:
- **Быстро реагировать на тренды** — обнаружение виральных роликов за 6 часов
- **Быть первыми по охватам** — генерация ТЗ до того, как тренд устареет
- **Собирать трафик и делать продажи** — один виральный ролик может дать огромный охват

**Критичность:** Без Trend Watcher агентство теряет возможность быстро реагировать на тренды и упускает потенциальный трафик.

### 1.4 Границы ответственности

**Что делает:**
- Мониторинг аккаунтов конкурентов в соцсетях
- Отбор виральных роликов по коэффициенту виральности
- Транскрибация аудио из роликов
- Визуальный анализ роликов (срезы каждые 5 секунд)
- Генерация сценария на основе анализа
- Генерация описания для поста
- Генерация ТЗ для монтажёра (кадры, камеры, визуальные элементы)
- Расчёт метрик виральности
- Статистика по взлетевшим роликам

**Что НЕ делает:**
- Не монтирует ролики (это задача монтажёра)
- Не публикует контент (это задача Content Scheduler Agent)
- Не зависит от Tone of Voice Agent (пишет сценарий независимо, т.к. это тренд)
- Не генерирует аудио и аватары (это в backlog, функция 2)

---

## 2. ВХОДНЫЕ ДАННЫЕ

### 2.1 Источники данных

**Основной источник:**
- **Apify Instagram Web Scraper API** — мониторинг аккаунтов конкурентов

**Дополнительные источники:**
- **Assembly AI** — транскрибация аудио из роликов
- **Claude API** — генерация сценария и описания поста
- **Google Cloud Vision API** (или аналог) — визуальный анализ кадров

### 2.2 Обязательные параметры

```python
class TrendWatcherInput(BaseModel):
    competitor_accounts: list[str]  # Список аккаунтов конкурентов (Instagram handles)
    monitoring_interval_hours: int = 6  # Интервал мониторинга (по умолчанию 6 часов)
    min_views_threshold: int = 10000  # Минимальное количество просмотров для анализа
    max_video_age_hours: int = 48  # Максимальный возраст ролика для анализа
    api_keys_pool: list[dict]  # Пул API ключей Apify (для ротации)
```

### 2.3 Опциональные параметры

```python
class TrendWatcherOptionalInput(BaseModel):
    platforms: list[str] = ["instagram", "youtube_shorts"]  # Платформы для мониторинга
    visual_analysis_interval_sec: int = 5  # Интервал срезов для визуального анализа
    virality_coefficient_formula: str = "custom"  # Формула расчёта виральности
    language_filter: list[str] = ["ru", "en"]  # Языки для анализа
```

### 2.4 Валидация входных данных

**Правила валидации:**
- `competitor_accounts` не может быть пустым списком
- `monitoring_interval_hours` должен быть > 0 и <= 24
- `min_views_threshold` должен быть >= 1000
- `api_keys_pool` должен содержать минимум 1 ключ

**Обработка ошибок валидации:**
- Если валидация не прошла → вернуть `INVALID_INPUT` с описанием ошибки
- Логировать в Event Store
- Не выполнять задачу

---

## 3. АЛГОРИТМ РАБОТЫ

### 3.1 Основные шаги

**Шаг 1: Мониторинг аккаунтов конкурентов**
- Получить список аккаунтов из `competitor_accounts`
- Для каждого аккаунта запросить последние ролики через Apify Instagram Web Scraper API
- Использовать ротацию API ключей из `api_keys_pool` (если ключ исчерпан → переключиться на следующий)
- Собрать метаданные: views, likes, comments, publish_date, video_url

**Шаг 2: Отбор виральных роликов**
- Рассчитать коэффициент виральности для каждого ролика
- Формула виральности (предварительная, требует исследования):
  ```
  virality_score = (views / hours_since_publish) * (1 + engagement_rate)
  engagement_rate = (likes + comments) / views
  ```
- Отфильтровать ролики с `virality_score` выше порога
- Приоритизировать по убыванию `virality_score`

**Шаг 3: Транскрибация аудио**
- Скачать видео по `video_url`
- Извлечь аудиодорожку
- Отправить на транскрибацию через Assembly AI
- Если язык не русский → перевести на русский через Assembly AI Translation
- Сохранить транскрипт в Obsidian (`raw/transcripts/`)

**Шаг 4: Визуальный анализ**
- Извлечь кадры из видео каждые 5 секунд
- Отправить кадры на анализ через Google Cloud Vision API (или Claude Vision)
- Получить описание каждого кадра: объекты, текст, композиция, цвета
- Сохранить анализ в Obsidian (`raw/visual_analysis/`)

**Шаг 5: Генерация сценария**
- Объединить транскрипт + визуальный анализ
- Отправить в Claude API с промптом:
  ```
  "На основе транскрипта и визуального анализа виральногоролика создай сценарий для аналогичного ролика в медицинском маркетинге. 
  Сценарий должен быть человечным, коротким, цепляющим. 
  Формат: [Кадр 1] описание, [Кадр 2] описание, текст озвучки."
  ```
- Получить сценарий от Claude
- Сохранить в Obsidian (`wiki/scenarios/`)

**Шаг 6: Генерация ТЗ для монтажёра**
- На основе визуального анализа создать ТЗ:
  - Какие камеры использовать (крупный план, средний, общий)
  - Какие визуальные элементы показать (графика, текст, объекты)
  - Какие переходы между кадрами
  - Какая музыка/звуки (если есть в оригинале)
- Сохранить ТЗ в Obsidian (`wiki/briefs/`)

**Шаг 7: Генерация описания для поста**
- Отправить сценарий в Claude API с промптом:
  ```
  "Напиши короткое описание для поста в Instagram (2-3 предложения), которое цепляет и мотивирует посмотреть ролик. 
  Стиль: человечный, без воды, с призывом к действию."
  ```
- Получить описание от Claude
- Сохранить в Obsidian (`wiki/post_descriptions/`)

**Шаг 8: Расчёт метрик и статистика**
- Сохранить метрики виральности в базу данных
- Обновить статистику по взлетевшим роликам
- Логировать в Event Store

### 3.2 Специфичная логика

**Коэффициент виральности (требует исследования):**
- Текущая формула: `virality_score = (views / hours_since_publish) * (1 + engagement_rate)`
- Необходимо провести исследование для уточнения формулы
- Факторы: скорость набора просмотров, engagement rate, время с момента публикации

**Определение "тренд набирает скорость":**
- Сравнить текущий `virality_score` с предыдущим замером (6 часов назад)
- Если рост > 50% → тренд набирает скорость
- Если рост < 10% → тренд замедляется

**Пороги для отбора роликов:**
- Минимум 10,000 просмотров за 24 часа
- `virality_score` > 500 (требует калибровки)
- Возраст ролика < 48 часов

### 3.3 Внешние API

**Apify Instagram Web Scraper API:**
- Endpoint: `https://api.apify.com/v2/acts/apify~instagram-scraper/runs`
- Аутентификация: API token в headers
- Rate limits: зависит от плана (используем пул бесплатных аккаунтов по $5)
- Ротация ключей: если ключ исчерпан → переключиться на следующий из `api_keys_pool`

**Assembly AI:**
- Endpoint: `https://api.assemblyai.com/v2/transcript`
- Аутентификация: API key в headers
- Rate limits: бесплатный план (проверить лимиты)
- Функции: транскрибация + перевод

**Google Cloud Vision API (или аналог):**
- Endpoint: `https://vision.googleapis.com/v1/images:annotate`
- Аутентификация: API key или OAuth
- Функции: object detection, text detection, label detection

**Claude API:**
- Endpoint: `https://api.anthropic.com/v1/messages`
- Аутентификация: API key в headers
- Модель: `claude-opus-4-7` (для максимальной человечности текста)
- Функции: генерация сценария, описания поста

---

## 4. ВЫХОДНЫЕ ДАННЫЕ

### 4.1 Формат результата

```python
class TrendWatcherResult(BaseModel):
    status: Literal["success", "partial", "failed"]
    trends_found: int  # Количество найденных трендов
    trends: list[TrendAnalysis]  # Список проанализированных трендов
    metrics: TrendWatcherMetrics
    errors: list[str] = []

class TrendAnalysis(BaseModel):
    video_url: str
    competitor_account: str
    virality_score: float
    views: int
    engagement_rate: float
    publish_date: datetime
    transcript: str  # Транскрипт аудио
    visual_analysis: list[FrameAnalysis]  # Анализ кадров
    scenario: str  # Сгенерированный сценарий
    voiceover_text: str  # Текст для озвучки
    editor_brief: str  # ТЗ для монтажёра
    post_description: str  # Описание для поста
    approval_required: bool = True  # Требуется согласование перед публикацией

class FrameAnalysis(BaseModel):
    timestamp_sec: int
    description: str
    objects: list[str]
    text_detected: str
    composition: str
    colors: list[str]

class TrendWatcherMetrics(BaseModel):
    execution_time_ms: int
    accounts_monitored: int
    videos_analyzed: int
    trends_detected: int
    api_calls_made: int
    api_keys_rotated: int
```

### 4.2 Сохранение результатов

**База данных:**
```sql
CREATE TABLE trend_analysis (
    id INTEGER PRIMARY KEY,
    video_url TEXT NOT NULL,
    competitor_account TEXT NOT NULL,
    virality_score REAL NOT NULL,
    views INTEGER NOT NULL,
    engagement_rate REAL NOT NULL,
    publish_date TIMESTAMP NOT NULL,
    scenario TEXT,
    post_description TEXT,
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_virality (virality_score DESC),
    INDEX idx_account_date (competitor_account, publish_date)
);

CREATE TABLE viral_stats (
    id INTEGER PRIMARY KEY,
    trend_id INTEGER REFERENCES trend_analysis(id),
    published_by_us BOOLEAN DEFAULT FALSE,
    our_views INTEGER,
    our_engagement_rate REAL,
    success BOOLEAN,
    published_at TIMESTAMP,
    INDEX idx_success (success, published_at)
);
```

**Obsidian vault:**
```
obsidian/social-magister/
├── raw/
│   ├── transcripts/
│   │   └── {video_id}_{date}.md
│   └── visual_analysis/
│       └── {video_id}_{date}.md
├── wiki/
│   ├── scenarios/
│   │   └── {trend_name}_{date}.md
│   ├── briefs/
│   │   └── {trend_name}_editor_brief_{date}.md
│   ├── post_descriptions/
│   │   └── {trend_name}_post_{date}.md
│   └── sources/
│       └── trend_analysis_{date}.md
```

---

## 5. МЕТРИКИ КАЧЕСТВА

### 5.1 Производительность

**Success rate:**
- Целевое значение: > 95%
- Warning: < 95%
- Critical: < 90%

**Execution time:**
- Целевое значение: < 10 минут на 1 ролик
- Warning: > 15 минут
- Critical: > 30 минут

### 5.2 Качественные метрики

**Процент роликов, которые "взлетели" после публикации:**
- Целевое значение: > 30% (из предложенных трендов)
- Измерение: `(наши_виральные_ролики / всего_опубликовано_по_трендам) * 100`
- Критерий "взлетел": > 50,000 просмотров за 48 часов

**Скорость реакции на тренд:**
- Целевое значение: < 12 часов (от обнаружения до ТЗ)
- Измерение: `время_создания_ТЗ - время_публикации_оригинала`
- Warning: > 24 часов (тренд может устареть)

**Точность предсказания виральности:**
- Целевое значение: > 50% (из предложенных трендов реально взлетели)
- Измерение: `(взлетевшие_тренды / всего_предложено) * 100`

### 5.3 Мониторинг

**Алерты:**
- Success rate < 95% → Warning
- Success rate < 90% → Critical
- Execution time > 15 минут → Warning
- API ключи исчерпаны (все из пула) → Critical
- Процент взлетевших роликов < 20% → Warning

**Дашборд метрик:**
- Количество мониторингов в день
- Количество найденных трендов
- Процент success / partial / failed
- Среднее время выполнения
- Топ-10 виральных роликов
- Статистика по взлетевшим роликам (наши vs конкуренты)
---

## 6. ИНТЕГРАЦИИ

### 6.1 Event Bus

**Получение задач от Social Magister:**
```json
{
  "event_type": "social.trend_monitoring.requested",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "trend-watcher",
  "payload": {
    "competitor_accounts": ["@competitor1", "@competitor2"],
    "monitoring_interval_hours": 6,
    "min_views_threshold": 10000
  }
}
```

**Отправка результатов Social Magister:**
```json
{
  "event_type": "social.trend_monitoring.completed",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "trend-watcher",
  "payload": {
    "status": "success",
    "result": {
      "trends_found": 5,
      "trends": [/* TrendAnalysis objects */],
      "approval_required": true
    },
    "metrics": {
      "execution_time_ms": 480000,
      "accounts_monitored": 10,
      "videos_analyzed": 50,
      "trends_detected": 5
    }
  }
}
```

### 6.2 Event Store

**Логирование всех событий:**
- `social.trend_monitoring.requested` — получена задача
- `social.trend_monitoring.completed` — задача завершена
- `social.trend_monitoring.failed` — задача провалена
- `escalation.required` — эскалация критичной ошибки

**Формат записи:**
```json
{
  "event_id": "uuid",
  "event_type": "social.trend_monitoring.completed",
  "correlation_id": "uuid",
  "timestamp": "2026-05-09T02:35:45Z",
  "subagent_id": "trend-watcher",
  "payload": {/* event data */}
}
```

### 6.3 Obsidian Vault

**Путь:** `obsidian/social-magister/`

**Операции:**
- **Ingest:** Сохранение транскриптов, визуального анализа в `raw/`
- **Query:** Чтение истории трендов для анализа паттернов
- **Lint:** Проверка противоречий, устаревших данных

**Специальные файлы:**
- `wiki/log.md` — хронология всех операций
- `wiki/index.md` — каталог всех трендов
- `wiki/sources/trend_analysis_{date}.md` — сводка по трендам

### 6.4 Database

**Таблицы:**
- `trend_analysis` — результаты анализа трендов
- `viral_stats` — статистика по взлетевшим роликам

**Операции:**
- INSERT: сохранение новых трендов
- SELECT: чтение истории для статистики
- UPDATE: обновление статуса публикации

### 6.5 Teacher Agent

**Интеграция:**
- Teacher Agent читает `wiki/log.md` и `wiki/concepts/`
- Анализирует успешные/неудачные тренды
- Обновляет формулу виральности
- Улучшает промпты для генерации сценариев

**Частота обучения:**
- Периодический пересмотр: раз в квартал
- Экстренное обучение: при падении метрик качества < 20%

### 6.6 Внешние API

**Apify Instagram Web Scraper API:**
- Мониторинг аккаунтов конкурентов
- Сбор метаданных роликов
- Ротация API ключей

**Assembly AI:**
- Транскрибация аудио
- Перевод на русский язык

**Google Cloud Vision API:**
- Визуальный анализ кадров
- Определение объектов, текста, композиции

**Claude API:**
- Генерация сценария
- Генерация описания поста

---

## 7. ОБРАБОТКА ОШИБОК

### 7.1 Стандартные ошибки

**INVALID_INPUT:**
- Причина: Пустой список `competitor_accounts`, неверные параметры
- Действие: Вернуть failure сразу
- Retry: Нет
- Логирование: Event Store + системные логи

**API_ERROR:**
- Причина: Временная недоступность Apify, Assembly AI, Claude API
- Действие: Retry с exponential backoff (10 попыток, 1 минута интервал)
- Если все попытки исчерпаны → вернуть partial_success с собранными данными
- Логирование: Event Store + системные логи

**TIMEOUT:**
- Причина: Превышено максимальное время выполнения (30 минут)
- Действие: Вернуть partial_success с проанализированными трендами
- Retry: Нет
- Логирование: Event Store + Obsidian

**INTERNAL_ERROR:**
- Причина: Внутренняя ошибка агента (баг в коде)
- Действие: Логировать, вернуть failure, эскалировать
- Retry: Нет
- Эскалация: Social Magister → Operator → User

### 7.2 Специфичные ошибки

**API_KEY_EXHAUSTED:**
- Причина: Все API ключи из пула исчерпаны
- Действие: 
  1. Переключиться на следующий ключ из `api_keys_pool`
  2. Если все ключи исчерпаны → вернуть partial_success
  3. Уведомить пользователя о необходимости пополнить пул ключей
- Retry: Нет (переключение на следующий ключ)
- Эскалация: Critical (если все ключи исчерпаны)

**VIDEO_NO_AUDIO:**
- Причина: Ролик без звука (только визуальный контент)
- Действие: 
  1. Пропустить транскрибацию
  2. Выполнить только визуальный анализ
  3. Генерировать сценарий на основе визуального анализа
  4. Пометить в результате: `audio_available: false`
- Retry: Нет
- Логирование: Event Store + Obsidian

**VIDEO_FOREIGN_LANGUAGE:**
- Причина: Ролик на иностранном языке (не русский)
- Действие:
  1. Транскрибировать на оригинальном языке
  2. Перевести на русский через Assembly AI Translation
  3. Сохранить оба варианта (оригинал + перевод)
  4. Генерировать сценарий на русском
- Retry: Нет
- Логирование: Event Store + Obsidian

**TREND_OUTDATED:**
- Причина: Тренд уже устарел (возраст ролика > 48 часов)
- Действие:
  1. Пропустить этот тренд
  2. Не генерировать ТЗ
  3. Логировать в статистику (для анализа паттернов)
- Retry: Нет
- Логирование: Obsidian

**DOWNLOAD_FAILED:**
- Причина: Не удалось скачать видео (удалено, приватное, геоблок)
- Действие:
  1. Retry 3 раза с интервалом 30 секунд
  2. Если не удалось → пропустить этот ролик
  3. Логировать причину
- Retry: 3 попытки
- Логирование: Event Store + Obsidian

### 7.3 Эскалация

**Путь эскалации:**
```
Trend Watcher → Social Magister → Operator → User → Architect
```

**Когда эскалировать:**
- Все API ключи исчерпаны (Critical)
- Success rate < 90% в течение 3 дней (Critical)
- Процент взлетевших роликов < 10% (Warning)
- Внутренняя ошибка агента (Critical)

**Формат эскалации:**
```json
{
  "event_type": "escalation.required",
  "correlation_id": "uuid",
  "source": "trend-watcher",
  "severity": "critical",
  "payload": {
    "error_type": "API_KEY_EXHAUSTED",
    "message": "All API keys from pool exhausted, monitoring stopped",
    "context": {
      "api_keys_total": 20,
      "api_keys_exhausted": 20,
      "last_successful_monitoring": "2026-05-09T02:35:45Z"
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
- Если транскрибация не удалась → выполнить только визуальный анализ
- Если визуальный анализ не удался → использовать только транскрипт
- Если Claude API недоступен → сохранить транскрипт и визуальный анализ для ручной обработки

---

## 8. ОБУЧЕНИЕ И АДАПТАЦИЯ

### 8.1 Интеграция с Teacher Agent

**Что Teacher Agent предоставляет:**
- Обновлённую формулу виральности (на основе статистики)
- Улучшенные промпты для генерации сценариев
- Новые паттерны виральных роликов
- Рекомендации по приоритизации трендов

**Как Trend Watcher обучается:**
1. Teacher Agent читает `wiki/log.md` и `wiki/concepts/`
2. Анализирует успешные тренды (наши ролики взлетели)
3. Анализирует неудачные тренды (наши ролики не взлетели)
4. Создаёт обновлённые инструкции
5. Trend Watcher применяет новые инструкции
6. Тестирует на контрольной выборке (10 трендов)
7. Сохраняет результаты в Obsidian

**Частота обучения:**
- Периодический пересмотр: раз в квартал
- Экстренное обучение: при падении метрик качества < 20%
- Адаптация: при изменении алгоритмов соцсетей

### 8.2 История в Obsidian

**Структура:**
```
obsidian/social-magister/wiki/
├── log.md                    # Хронология операций
├── concepts/
│   ├── virality_patterns.md  # Паттерны виральности
│   ├── successful_trends.md  # Успешные тренды
│   └── failed_trends.md      # Неудачные тренды
├── strategies/
│   └── trend_selection.md    # Стратегии отбора трендов
└── connections/
    └── trend_correlations.md # Связи между трендами
```

**Формат log.md:**
```markdown
## [2026-05-09 02:35] trend_monitoring | Found 5 viral trends, 3 approved
## [2026-05-09 08:40] trend_published | Trend "medical_hack_123" published, 50K views in 24h
## [2026-05-09 14:20] trend_failed | Trend "health_tip_456" published, only 2K views
```

### 8.3 Адаптация

**Автоматическая адаптация:**
- Если процент взлетевших роликов < 20% → запросить обучение у Teacher Agent
- Если новый тренд не подходит под текущую формулу виральности → логировать для анализа
- Если изменились алгоритмы соцсетей → Teacher Agent обновляет стратегию

**Ручная адаптация:**
- Пользователь может обновить `competitor_accounts` через Social Magister
- Пользователь может изменить `min_views_threshold` для калибровки
- Пользователь может добавить новые платформы (TikTok, YouTube)

---

## 9. ЛОГИРОВАНИЕ

### 9.1 Event Store (обязательно)

**Логируемые события:**
- `social.trend_monitoring.requested` — получена задача
- `social.trend_monitoring.completed` — задача завершена
- `social.trend_monitoring.failed` — задача провалена
- `escalation.required` — эскалация критичной ошибки

**Формат:**
```json
{
  "event_id": "uuid",
  "event_type": "social.trend_monitoring.completed",
  "correlation_id": "uuid",
  "timestamp": "2026-05-09T02:35:45Z",
  "subagent_id": "trend-watcher",
  "payload": {
    "status": "success",
    "trends_found": 5,
    "execution_time_ms": 480000
  }
}
```

### 9.2 Obsidian Vault (обязательно)

**История операций (`wiki/log.md`):**
```markdown
## [2026-05-09 02:35] trend_monitoring | Found 5 viral trends from 10 accounts
## [2026-05-09 02:40] scenario_generated | Created scenario for trend "medical_hack_123"
## [2026-05-09 02:42] editor_brief_created | ТЗ for editor ready, approval required
```

**Результаты работы:**
- `wiki/scenarios/` — сгенерированные сценарии
- `wiki/briefs/` — ТЗ для монтажёра
- `wiki/post_descriptions/` — описания для постов
- `wiki/sources/` — сводки по трендам

**Метрики производительности:**
- `wiki/metrics/virality_stats.md` — статистика виральности
- `wiki/metrics/success_rate.md` — процент взлетевших роликов

### 9.3 Системные логи (опционально)

**Debug информация:**
- API запросы и ответы
- Ротация API ключей
- Время выполнения каждого шага

**Ошибки и warnings:**
- Ошибки API
- Таймауты
- Недоступные ролики

**Формат:**
```
[2026-05-09 02:35:45] [INFO] [trend-watcher] [correlation-id-123] Started monitoring 10 accounts
[2026-05-09 02:36:12] [WARNING] [trend-watcher] [correlation-id-123] API key exhausted, switching to next
[2026-05-09 02:40:30] [ERROR] [trend-watcher] [correlation-id-123] Failed to download video: 403 Forbidden
```

---

## 10. ТЕСТИРОВАНИЕ

### 10.1 Unit тесты

**Покрытие:** > 80%

**Обязательные тесты:**
- Валидация входных данных (`test_validate_input`)
- Расчёт коэффициента виральности (`test_calculate_virality_score`)
- Ротация API ключей (`test_api_key_rotation`)
- Обработка ошибок API (`test_api_error_handling`)
- Retry механизм (`test_retry_with_backoff`)
- Сохранение в БД (`test_save_to_database`)
- Сохранение в Obsidian (`test_save_to_obsidian`)
- Формирование результата (`test_format_result`)

**Примеры:**
```python
def test_calculate_virality_score():
    views = 100000
    hours_since_publish = 24
    likes = 5000
    comments = 500
    engagement_rate = (likes + comments) / views
    expected_score = (views / hours_since_publish) * (1 + engagement_rate)
    
    result = calculate_virality_score(views, hours_since_publish, likes, comments)
    assert result == expected_score

def test_api_key_rotation():
    api_keys_pool = [{"key": "key1"}, {"key": "key2"}, {"key": "key3"}]
    exhausted_keys = ["key1"]
    
    next_key = get_next_api_key(api_keys_pool, exhausted_keys)
    assert next_key == {"key": "key2"}
```

### 10.2 Integration тесты

**Обязательные сценарии:**
- Получение задачи через Event Bus (`test_receive_task_from_event_bus`)
- Отправка результата через Event Bus (`test_send_result_to_event_bus`)
- Логирование в Event Store (`test_log_to_event_store`)
- Сохранение в Obsidian vault (`test_save_to_obsidian_vault`)
- Сохранение в базу данных (`test_save_to_database`)
- Эскалация при критичных ошибках (`test_escalation_on_critical_error`)
- Интеграция с Apify API (`test_apify_integration`)
- Интеграция с Assembly AI (`test_assembly_ai_integration`)
- Интеграция с Claude API (`test_claude_api_integration`)

### 10.3 E2E тесты

**Обязательные сценарии:**
- Полный цикл: задача → мониторинг → анализ → генерация → результат (`test_full_cycle`)
- Частичный сбой (graceful degradation): транскрибация не удалась, но визуальный анализ выполнен (`test_partial_failure`)
- Критичная ошибка (escalation): все API ключи исчерпаны (`test_critical_error_escalation`)
- Retry механизм при временных сбоях API (`test_retry_on_api_error`)
- Ротация API ключей при исчерпании (`test_api_key_rotation_e2e`)

**Пример E2E теста:**
```python
async def test_full_cycle():
    # 1. Создать задачу
    task = {
        "competitor_accounts": ["@test_competitor"],
        "monitoring_interval_hours": 6,
        "min_views_threshold": 10000
    }
    
    # 2. Отправить задачу через Event Bus
    await event_bus.publish("social.trend_monitoring.requested", task)
    
    # 3. Дождаться результата
    result = await event_bus.subscribe("social.trend_monitoring.completed")
    
    # 4. Проверить результат
    assert result["status"] == "success"
    assert result["trends_found"] > 0
    assert len(result["trends"]) > 0
    
    # 5. Проверить сохранение в БД
    db_record = await database.query("SELECT * FROM trend_analysis WHERE video_url = ?", result["trends"][0]["video_url"])
    assert db_record is not None
    
    # 6. Проверить сохранение в Obsidian
    obsidian_file = f"obsidian/social-magister/wiki/scenarios/{result['trends'][0]['video_url']}.md"
    assert os.path.exists(obsidian_file)
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
ffmpeg-python >= 0.2.0       # Обработка видео
pillow >= 10.0.0             # Обработка изображений
```

### 11.2 Конфигурация (.env)

```env
SUBAGENT_ID=trend-watcher
EVENT_BUS_URL=...
EVENT_STORE_URL=...
OBSIDIAN_VAULT_PATH=./obsidian/social-magister
DATABASE_URL=sqlite+aiosqlite:///./data/aim.db

# Apify API (пул ключей)
APIFY_API_KEYS=["key1", "key2", "key3", ...]

# Assembly AI
ASSEMBLY_AI_API_KEY=...

# Google Cloud Vision API
GOOGLE_CLOUD_VISION_API_KEY=...

# Claude API
ANTHROPIC_API_KEY=...

# Настройки мониторинга
MONITORING_INTERVAL_HOURS=6
MIN_VIEWS_THRESHOLD=10000
MAX_VIDEO_AGE_HOURS=48
VISUAL_ANALYSIS_INTERVAL_SEC=5
```

### 11.3 Мониторинг

**Метрики для алертов:**
- Success rate < 95% → Warning
- Success rate < 90% → Critical
- Execution time > 15 минут → Warning
- Процент взлетевших роликов < 20% → Warning
- Все API ключи исчерпаны → Critical

**Дашборд метрик:**
- Количество мониторингов в день
- Количество найденных трендов
- Процент success / partial / failed
- Среднее время выполнения
- Топ-10 виральных роликов
- Статистика по взлетевшим роликам (наши vs конкуренты)
- Использование API ключей (сколько осталось)

---

## 12. BACKLOG (будущие функции)

### 12.1 Функция 2: Генерация аудио и аватара

**Описание:**
- Генерация аудио через Loven Labs на основе написанного текста озвучки
- Генерация аватара через Heijan для визуализации спикера

**Статус:** Backlog (не приоритет)

**Зависимости:**
- Loven Labs API
- Heijan API

### 12.2 Функция 3: Поддержка YouTube Shorts

**Описание:**
- Мониторинг YouTube Shorts (в дополнение к Instagram)
- Анализ трендов на YouTube

**Статус:** Backlog

**Зависимости:**
- YouTube Data API v3

### 12.3 Функция 4: Автоматическая публикация

**Описание:**
- Автоматическая публикация роликов после согласования
- Интеграция с Content Scheduler Agent

**Статус:** Backlog

**Зависимости:**
- Content Scheduler Agent (P1)

---

## 13. ИССЛЕДОВАНИЯ (TODO)

### 13.1 Формула виральности

**Задача:** Провести исследование для уточнения формулы расчёта коэффициента виральности

**Текущая формула:**
```
virality_score = (views / hours_since_publish) * (1 + engagement_rate)
engagement_rate = (likes + comments) / views
```

**Что исследовать:**
- Влияние скорости набора просмотров
- Влияние engagement rate (likes, comments, shares)
- Влияние времени с момента публикации
- Влияние алгоритмов соцсетей (рекомендации)
- Сравнение с реальными виральными роликами

**Метод:**
- Собрать данные по 100+ виральным роликам
- Проанализировать корреляции
- Откалибровать формулу
- Протестировать на контрольной выборке

**Срок:** 1-2 недели

### 13.2 Пороги для отбора роликов

**Задача:** Определить оптимальные пороги для отбора виральных роликов

**Текущие пороги:**
- Минимум 10,000 просмотров за 24 часа
- `virality_score` > 500
- Возраст ролика < 48 часов

**Что исследовать:**
- Оптимальный порог просмотров (10K? 50K? 100K?)
- Оптимальный порог `virality_score`
- Оптимальный возраст ролика (24h? 48h? 72h?)

**Метод:**
- A/B тестирование разных порогов
- Измерение процента взлетевших роликов
- Выбор оптимальных значений

**Срок:** 2-3 недели

---

**Дата создания:** 2026-05-09  
**Автор:** Mikhail Eliseev (via meAI Architect)  
**Статус:** Draft  
**Версия:** 1.0
