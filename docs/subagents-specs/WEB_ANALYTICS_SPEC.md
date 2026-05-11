# Web Analytics Agent - Спецификация

**Дата создания:** 2026-05-10  
**Версия:** 1.0  
**Статус:** Draft  
**Приоритет:** P1 (Важный)  
**Домен:** SEO  
**Родительский Magister:** SEO Magister

---

## 1. ОБЗОР

### 1.1 Назначение

**Web Analytics Agent** — главный аналитик системы, который собирает метрики со всех счётчиков и источников, отслеживает отклонения и передаёт данные в сыром виде для анализа верхнего уровня.

**Ключевые функции:**
- Сбор метрик из Яндекс Метрики и Google Analytics
- Отслеживание отклонений и аномалий
- Анализ источников трафика и конверсий
- Усреднение данных при расхождениях между источниками
- Передача данных в сыром виде (без выводов)

### 1.2 Роль в системе

**Тип:** Subagent (исполнитель)  
**Родительский Magister:** SEO Magister  
**Домен:** SEO (поисковая оптимизация)  
**Автономность:** Высокая (работает по расписанию)

**Взаимодействие:**
- **Получает:** Задачи от SEO Magister (URL сайта, период анализа)
- **Отправляет:** Метрики в сыром виде (цифры день за днём)
- **Использует:** Яндекс Метрика API, Google Analytics API, опционально Яндекс Вебмастер и Google Search Console

### 1.3 Уникальная ценность

**Почему критично для агентства:**

1. **Данные = основа решений**
   - Без аналитики невозможно понять, куда двигаться
   - Данные показывают, что работает, что нет
   - Объективная картина для принятия решений

2. **Отслеживание динамики**
   - Видим изменения день за днём
   - Выявляем аномалии и отклонения
   - Реагируем на проблемы быстро

3. **Источники трафика**
   - Понимаем, откуда приходят пациенты
   - Видим, какие каналы конвертируются
   - Оптимизируем бюджет на основе данных

4. **Конверсии и результаты**
   - Отслеживаем цели и конверсии
   - Видим, какие источники приносят результат
   - Измеряем ROI от SEO

5. **Единый источник правды**
   - Все метрики в одном месте
   - Усреднение при расхождениях
   - Консистентные данные для всей системы

### 1.4 Границы ответственности

**Что делает агент:**
- ✅ Собирает метрики из Яндекс Метрики и Google Analytics
- ✅ Собирает данные из Яндекс Вебмастера и Google Search Console (опционально)
- ✅ Отслеживает отклонения и аномалии
- ✅ Усредняет данные при расхождениях между источниками
- ✅ Передаёт данные в сыром виде (цифры день за днём)
- ✅ Сохраняет историю метрик в БД и Obsidian

**Что НЕ делает агент:**
- ❌ Не делает выводы и рекомендации (это задача SEO Magister)
- ❌ Не имплементирует изменения (это задача других агентов)
- ❌ Не строит прогнозы (это задача аналитических агентов верхнего уровня)
- ❌ Не создаёт отчёты (это задача Report Generator Agent)

---

## 2. ВХОДНЫЕ ДАННЫЕ

### 2.1 Источники данных

**Основные источники:**

1. **Яндекс Метрика API** — максимальное количество данных
   - Трафик (визиты, посетители, просмотры)
   - Источники трафика (поисковые системы, соцсети, прямые заходы)
   - Конверсии (цели, e-commerce)
   - Поведение (глубина просмотра, время на сайте, отказы)
   - Технические данные (браузеры, устройства, регионы)

2. **Google Analytics API** — максимальное количество данных
   - Сессии и пользователи
   - Источники и каналы трафика
   - Цели и конверсии
   - E-commerce транзакции
   - Поведенческие метрики
   - Демография и интересы

**Опциональные источники:**

3. **Яндекс Вебмастер API** — данные из поисковой выдачи Яндекса
   - Запросы, по которым показывается сайт
   - Позиции в выдаче
   - CTR (кликабельность)
   - Индексация страниц

4. **Google Search Console API** — данные из поисковой выдачи Google
   - Запросы и показы
   - Клики и CTR
   - Средняя позиция
   - Проблемы индексации

### 2.2 Входные параметры

**Обязательные параметры:**

```python
from pydantic import BaseModel, Field, HttpUrl
from datetime import date

class WebAnalyticsInput(BaseModel):
    site_url: HttpUrl = Field(
        ...,
        description="URL сайта для анализа"
    )
    project_id: str = Field(
        ...,
        description="ID проекта (для изоляции данных)"
    )
    yandex_metrika_token: str = Field(
        ...,
        description="Токен Яндекс Метрики"
    )
    google_analytics_token: str = Field(
        ...,
        description="Токен Google Analytics"
    )
    date_from: date = Field(
        ...,
        description="Начало периода анализа"
    )
    date_to: date = Field(
        ...,
        description="Конец периода анализа"
    )
```

**Опциональные параметры:**

```python
    yandex_webmaster_token: str | None = Field(
        default=None,
        description="Токен Яндекс Вебмастера (опционально)"
    )
    google_search_console_token: str | None = Field(
        default=None,
        description="Токен Google Search Console (опционально)"
    )
    metrics: list[str] = Field(
        default=["visits", "users", "pageviews", "bounce_rate", "conversions"],
        description="Список метрик для сбора"
    )
```

### 2.3 Валидация входных данных

**Правила валидации:**

1. **site_url** — валидный HTTP/HTTPS URL, доступен для проверки
2. **project_id** — уникальный, только буквы/цифры/дефис
3. **yandex_metrika_token** — валидный токен (проверка через API)
4. **google_analytics_token** — валидный токен (проверка через API)
5. **date_from, date_to** — date_from <= date_to, не более 365 дней между датами
6. **metrics** — список поддерживаемых метрик

**Ошибки валидации:**
- `INVALID_URL` — неверный формат URL
- `INVALID_PROJECT_ID` — неверный формат project_id
- `INVALID_TOKEN` — неверный токен API
- `INVALID_DATE_RANGE` — неверный диапазон дат
- `INVALID_METRICS` — неподдерживаемые метрики

---

## 3. АЛГОРИТМ РАБОТЫ

### 3.1 Основные шаги

**Алгоритм (5 шагов):**

1. **Сбор данных со всех источников**
   - Яндекс Метрика (трафик, источники, конверсии, поведение)
   - Google Analytics (сессии, пользователи, цели)
   - Яндекс Вебмастер (опционально — запросы, позиции)
   - Google Search Console (опционально — клики, показы)

2. **Усреднение данных**
   - Если есть расхождения между Яндекс Метрикой и Google Analytics
   - Формула: среднее арифметическое или взвешенное среднее
   - Сохранение исходных данных для аудита

3. **Отслеживание отклонений**
   - Сравнение с предыдущим периодом
   - Выявление аномалий (резкие изменения > 20%)
   - Пометка аномальных дней

4. **Проверка ошибок получения**
   - API недоступны
   - Данные неполные (пропущенные дни)
   - Расхождения > 50% между источниками

5. **Передача данных дальше**
   - Сохранение в БД (структурированные метрики)
   - Сохранение в Obsidian (история, динамика)
   - Отправка SEO Magister через Event Bus

### 3.2 Детальный workflow

**Шаг 1: Сбор данных из Яндекс Метрики**

```python
async def collect_yandex_metrika(
    site_url: str,
    date_from: date,
    date_to: date,
    metrics: list[str]
) -> list[dict]:
    """
    Сбор метрик из Яндекс Метрики
    
    Returns:
        [
            {
                "date": "2026-05-10",
                "visits": 1000,
                "users": 800,
                "pageviews": 3000,
                "bounce_rate": 0.45,
                "conversions": 50
            },
            ...
        ]
    """
```

**Шаг 2: Сбор данных из Google Analytics**

```python
async def collect_google_analytics(
    site_url: str,
    date_from: date,
    date_to: date,
    metrics: list[str]
) -> list[dict]:
    """
    Сбор метрик из Google Analytics
    
    Returns:
        [
            {
                "date": "2026-05-10",
                "sessions": 950,
                "users": 780,
                "pageviews": 2900,
                "bounce_rate": 0.48,
                "conversions": 48
            },
            ...
        ]
    """
```

**Шаг 3: Усреднение данных**

```python
async def average_data(
    yandex_data: list[dict],
    google_data: list[dict]
) -> list[dict]:
    """
    Усреднение данных при расхождениях
    
    Формула: среднее арифметическое
    (yandex_value + google_value) / 2
    
    Returns:
        [
            {
                "date": "2026-05-10",
                "visits": 975,  # (1000 + 950) / 2
                "users": 790,   # (800 + 780) / 2
                "pageviews": 2950,
                "bounce_rate": 0.465,
                "conversions": 49,
                "source_yandex": {"visits": 1000, ...},
                "source_google": {"sessions": 950, ...}
            },
            ...
        ]
    """
```

**Шаг 4: Отслеживание отклонений**

```python
async def detect_anomalies(
    current_data: list[dict],
    previous_data: list[dict]
) -> list[dict]:
    """
    Выявление аномалий (резкие изменения > 20%)
    
    Returns:
        [
            {
                "date": "2026-05-10",
                "metric": "visits",
                "current_value": 1000,
                "previous_value": 500,
                "change_percent": 100.0,
                "is_anomaly": True
            },
            ...
        ]
    """
```

**Шаг 5: Проверка ошибок получения**

```python
async def check_data_quality(
    yandex_data: list[dict],
    google_data: list[dict]
) -> dict:
    """
    Проверка качества данных
    
    Returns:
        {
            "sources_available": ["yandex", "google"],
            "sources_unavailable": [],
            "missing_dates": [],
            "large_discrepancies": [
                {
                    "date": "2026-05-10",
                    "metric": "visits",
                    "yandex": 1000,
                    "google": 400,
                    "discrepancy_percent": 60.0
                }
            ]
        }
    """
```

### 3.3 Специфичная логика

**Нет специфичных алгоритмов и формул.** Стандартная обработка: fetch → process → save.

**Усреднение данных:**
- Среднее арифметическое: `(yandex_value + google_value) / 2`
- Применяется только если расхождение < 50%
- Если расхождение > 50% → флаг `large_discrepancy`, сохранение обоих значений

---

## 4. ВЫХОДНЫЕ ДАННЫЕ

### 4.1 Формат результата

**Структура результата:**

```python
from pydantic import BaseModel
from datetime import date

class DailyMetrics(BaseModel):
    date: date = Field(description="Дата")
    visits: int = Field(description="Визиты (усреднённое)")
    users: int = Field(description="Пользователи (усреднённое)")
    pageviews: int = Field(description="Просмотры страниц (усреднённое)")
    bounce_rate: float = Field(description="Показатель отказов (усреднённое)")
    conversions: int = Field(description="Конверсии (усреднённое)")
    source_yandex: dict = Field(description="Исходные данные Яндекс Метрики")
    source_google: dict = Field(description="Исходные данные Google Analytics")
    is_anomaly: bool = Field(description="Есть ли аномалии в этот день")

class WebAnalyticsResult(BaseModel):
    project_id: str
    site_url: str
    date_from: date
    date_to: date
    daily_metrics: list[DailyMetrics]
    anomalies: list[dict]
    data_quality: dict
    summary: dict  # total_visits, avg_bounce_rate, total_conversions, etc.
```

### 4.2 Хранение данных

**База данных (структурированные метрики):**

```sql
CREATE TABLE web_analytics_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    site_url TEXT NOT NULL,
    date DATE NOT NULL,
    visits INTEGER,
    users INTEGER,
    pageviews INTEGER,
    bounce_rate REAL,
    conversions INTEGER,
    source_yandex TEXT,  -- JSON
    source_google TEXT,  -- JSON
    is_anomaly BOOLEAN DEFAULT FALSE,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_project_date (project_id, date),
    UNIQUE (project_id, date)
);

CREATE TABLE web_analytics_anomalies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    date DATE NOT NULL,
    metric TEXT NOT NULL,
    current_value REAL,
    previous_value REAL,
    change_percent REAL,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Obsidian vault (история, динамика):**

```
obsidian/seo-magister/
├── raw/
│   └── web-analytics/
│       └── {project_id}/
│           └── YYYY-MM-DD.md
├── wiki/
│   ├── sources/
│   │   └── web-analytics-{project_id}-YYYY-MM-DD.md
│   ├── concepts/
│   │   └── traffic-dynamics-{project_id}.md
│   └── connections/
│       └── analytics-to-keywords-{project_id}.md
└── decisions/
    └── traffic-anomalies-{project_id}.md
```

**Формат файла в raw/:**

```markdown
---
source: web-analytics
project_id: project-123
site_url: https://example.com
date_from: 2026-05-01
date_to: 2026-05-10
metrics_count: 10
collected_at: 2026-05-10T16:00:00Z
status: processed
output: wiki/sources/web-analytics-project-123-2026-05-10.md
---

# Web Analytics - project-123 - 2026-05-01 to 2026-05-10

## Метрики

- Всего визитов: 10000
- Средний bounce rate: 45%
- Всего конверсий: 500
- Аномалий: 2

## Динамика по дням

| Дата       | Визиты | Пользователи | Конверсии |
|------------|--------|--------------|-----------|
| 2026-05-01 | 1000   | 800          | 50        |
| 2026-05-02 | 950    | 780          | 48        |
...
```

---

## 5. МЕТРИКИ КАЧЕСТВА

### 5.1 Производительность

**Success rate:**
- Целевое значение: > 95%
- Warning: < 95%
- Critical: < 90%

**Execution time:**
- Зависит от объёма данных и периода
- Целевое значение: < 5 минут на 30 дней данных
- Warning: > 10 минут
- Critical: > 20 минут

**Reliability:**
- Partial success rate: > 99%
- Failure rate: < 1%

### 5.2 Качественные метрики

**Покрытие источников:**
- Целевое значение: 100% (все API доступны)
- Warning: < 100% (один источник недоступен)
- Critical: < 50% (несколько источников недоступны)

**Актуальность данных:**
- Целевое значение: данные не старше 1 дня
- Warning: данные старше 1 дня
- Critical: данные старше 3 дней

**Качество данных:**
- Целевое значение: расхождения < 10% между источниками
- Warning: расхождения 10-50%
- Critical: расхождения > 50%

### 5.3 Специфичные метрики

**Нет специфичных метрик.** Используются стандартные метрики производительности и качества.

### 5.4 Дашборд метрик

**Ежедневный дашборд:**
- Количество проектов проанализировано
- Среднее время выполнения
- Недоступные источники
- Аномалии за день
- Расхождения между источниками

**Еженедельный отчёт:**
- Динамика метрик по всем проектам
- Сравнение с предыдущей неделей
- Топ-10 проектов по росту трафика
- Топ-10 аномалий

---
## 6. ИНТЕГРАЦИИ

### 6.1 Event Bus Integration

**Входящие события:**

```python
# Получение задачи от SEO Magister
@event_handler("seo.web_analytics.requested")
async def handle_analytics_request(event: Event):
    """
    Обработка запроса на сбор метрик
    
    Event payload:
        {
            "correlation_id": "uuid",
            "site_url": "https://example.com",
            "project_id": "project-123",
            "date_from": "2026-05-01",
            "date_to": "2026-05-10",
            "metrics": ["visits", "users", "pageviews", "bounce_rate", "conversions"],
            "yandex_metrika_token": "...",
            "google_analytics_token": "...",
            "yandex_webmaster_token": "..." (optional),
            "google_search_console_token": "..." (optional)
        }
    """
```

**Исходящие события:**

```python
# Отправка результатов SEO Magister
await event_bus.publish(Event(
    type="seo.web_analytics.completed",
    correlation_id=correlation_id,
    payload={
        "project_id": "project-123",
        "site_url": "https://example.com",
        "date_from": "2026-05-01",
        "date_to": "2026-05-10",
        "daily_metrics": [...],
        "anomalies": [...],
        "data_quality": {...},
        "summary": {...},
        "obsidian_output": "obsidian/seo-magister/wiki/sources/web-analytics-project-123-2026-05-10.md"
    }
))

# Отправка ошибки
await event_bus.publish(Event(
    type="seo.web_analytics.failed",
    correlation_id=correlation_id,
    payload={
        "error_code": "API_UNAVAILABLE",
        "error_message": "Яндекс Метрика API недоступен",
        "retry_after": 300
    }
))
```

### 6.2 API Integrations

**Яндекс Метрика API:**

```python
from aiohttp import ClientSession

class YandexMetrikaClient:
    BASE_URL = "https://api-metrika.yandex.net/stat/v1/data"
    
    async def get_metrics(
        self,
        counter_id: str,
        date_from: date,
        date_to: date,
        metrics: list[str]
    ) -> list[dict]:
        """
        Получение метрик из Яндекс Метрики
        
        Metrics:
            - ym:s:visits (визиты)
            - ym:s:users (пользователи)
            - ym:s:pageviews (просмотры)
            - ym:s:bounceRate (показатель отказов)
            - ym:s:goal<N>reaches (конверсии)
        """
        async with ClientSession() as session:
            params = {
                "ids": counter_id,
                "date1": date_from.isoformat(),
                "date2": date_to.isoformat(),
                "metrics": ",".join(metrics),
                "dimensions": "ym:s:date",
                "oauth_token": self.token
            }
            async with session.get(self.BASE_URL, params=params) as response:
                return await response.json()
```

**Google Analytics API:**

```python
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest

class GoogleAnalyticsClient:
    async def get_metrics(
        self,
        property_id: str,
        date_from: date,
        date_to: date,
        metrics: list[str]
    ) -> list[dict]:
        """
        Получение метрик из Google Analytics
        
        Metrics:
            - sessions (сессии)
            - totalUsers (пользователи)
            - screenPageViews (просмотры)
            - bounceRate (показатель отказов)
            - conversions (конверсии)
        """
        client = BetaAnalyticsDataClient()
        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[{
                "start_date": date_from.isoformat(),
                "end_date": date_to.isoformat()
            }],
            metrics=[{"name": m} for m in metrics],
            dimensions=[{"name": "date"}]
        )
        response = await client.run_report(request)
        return self._parse_response(response)
```

**Яндекс Вебмастер API (опционально):**

```python
class YandexWebmasterClient:
    BASE_URL = "https://api.webmaster.yandex.net/v4"
    
    async def get_search_queries(
        self,
        host_id: str,
        date_from: date,
        date_to: date
    ) -> list[dict]:
        """
        Получение поисковых запросов из Яндекс Вебмастера
        
        Returns:
            [
                {
                    "query": "медицинская клиника москва",
                    "impressions": 1000,
                    "clicks": 50,
                    "ctr": 0.05,
                    "position": 5.2
                },
                ...
            ]
        """
```

**Google Search Console API (опционально):**

```python
from googleapiclient.discovery import build

class GoogleSearchConsoleClient:
    async def get_search_analytics(
        self,
        site_url: str,
        date_from: date,
        date_to: date
    ) -> list[dict]:
        """
        Получение данных из Google Search Console
        
        Returns:
            [
                {
                    "query": "medical clinic moscow",
                    "impressions": 800,
                    "clicks": 40,
                    "ctr": 0.05,
                    "position": 6.1
                },
                ...
            ]
        """
```

### 6.3 Database Integration

**Сохранение метрик:**

```python
from meai.storage.database import get_session
from sqlalchemy import insert, select

async def save_metrics(metrics: list[DailyMetrics]):
    async with get_session() as session:
        for metric in metrics:
            stmt = insert(web_analytics_metrics).values(
                project_id=metric.project_id,
                site_url=metric.site_url,
                date=metric.date,
                visits=metric.visits,
                users=metric.users,
                pageviews=metric.pageviews,
                bounce_rate=metric.bounce_rate,
                conversions=metric.conversions,
                source_yandex=json.dumps(metric.source_yandex),
                source_google=json.dumps(metric.source_google),
                is_anomaly=metric.is_anomaly
            ).on_conflict_do_update(
                index_elements=["project_id", "date"],
                set_={
                    "visits": metric.visits,
                    "users": metric.users,
                    "pageviews": metric.pageviews,
                    "bounce_rate": metric.bounce_rate,
                    "conversions": metric.conversions,
                    "is_anomaly": metric.is_anomaly
                }
            )
            await session.execute(stmt)
        await session.commit()
```

### 6.4 Obsidian Integration

**Сохранение в vault:**

```python
from meai.memory.obsidian import ObsidianVault

async def save_to_obsidian(result: WebAnalyticsResult):
    vault = ObsidianVault("obsidian/seo-magister")
    
    # Сохранение в raw/
    raw_path = f"raw/web-analytics/{result.project_id}/{result.date_to}.md"
    await vault.write_note(
        path=raw_path,
        content=format_raw_data(result),
        frontmatter={
            "source": "web-analytics",
            "project_id": result.project_id,
            "site_url": result.site_url,
            "date_from": result.date_from.isoformat(),
            "date_to": result.date_to.isoformat(),
            "metrics_count": len(result.daily_metrics),
            "collected_at": datetime.now(UTC).isoformat(),
            "status": "processed",
            "output": f"wiki/sources/web-analytics-{result.project_id}-{result.date_to}.md"
        }
    )
    
    # Сохранение в wiki/sources/
    wiki_path = f"wiki/sources/web-analytics-{result.project_id}-{result.date_to}.md"
    await vault.write_note(
        path=wiki_path,
        content=format_wiki_summary(result),
        frontmatter={
            "type": "source",
            "agent": "web-analytics",
            "project_id": result.project_id,
            "date": result.date_to.isoformat()
        }
    )
```

---

## 7. ОБРАБОТКА ОШИБОК

### 7.1 Типы ошибок

**API_UNAVAILABLE:**
- Яндекс Метрика API недоступен
- Google Analytics API недоступен
- Яндекс Вебмастер API недоступен
- Google Search Console API недоступен

**Стратегия:**
- Retry с exponential backoff (10 попыток)
- Если один источник недоступен → продолжить с другими (graceful degradation)
- Если все источники недоступны → эскалация → SEO Magister

**TIMEOUT:**
- Долгий сбор данных (> 10 минут)

**Стратегия:**
- Увеличить timeout до 20 минут
- Если всё равно timeout → разбить период на части (по неделям)
- Собрать данные по частям → объединить

**INVALID_INPUT:**
- Неверный URL сайта
- Неверный project_id
- Неверные токены API
- Неверный диапазон дат

**Стратегия:**
- Валидация входных данных перед выполнением
- Возврат ошибки с описанием проблемы
- Эскалация → SEO Magister

**RATE_LIMIT_EXCEEDED:**
- Превышен лимит запросов к API

**Стратегия:**
- Подождать до сброса лимита (retry_after из заголовков)
- Retry с exponential backoff
- Если лимит не сбрасывается → эскалация → SEO Magister

**DATA_QUALITY_ISSUE:**
- Расхождения > 50% между источниками
- Пропущенные дни в данных
- Неполные данные

**Стратегия:**
- Флаг `large_discrepancy` в результате
- Сохранение обоих значений (Яндекс и Google)
- Предупреждение в отчёте
- Продолжить выполнение (partial success)

### 7.2 Retry механизм

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

@retry(
    stop=stop_after_attempt(10),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type((APIUnavailableError, TimeoutError))
)
async def fetch_with_retry(api_call: Callable):
    """
    Retry механизм для API вызовов
    
    - 10 попыток
    - Exponential backoff: 4s, 8s, 16s, 32s, 60s, 60s, ...
    - Retry только для API_UNAVAILABLE и TIMEOUT
    """
    return await api_call()
```

### 7.3 Graceful degradation

```python
async def collect_all_sources(
    site_url: str,
    date_from: date,
    date_to: date
) -> dict[str, list[dict]]:
    """
    Сбор данных со всех источников с graceful degradation
    
    Если один источник недоступен → продолжить с другими
    """
    results = {}
    
    # Яндекс Метрика (обязательный)
    try:
        results["yandex"] = await fetch_yandex_metrika(site_url, date_from, date_to)
    except Exception as e:
        logger.error(f"Яндекс Метрика недоступна: {e}")
        results["yandex"] = None
    
    # Google Analytics (обязательный)
    try:
        results["google"] = await fetch_google_analytics(site_url, date_from, date_to)
    except Exception as e:
        logger.error(f"Google Analytics недоступен: {e}")
        results["google"] = None
    
    # Яндекс Вебмастер (опциональный)
    try:
        results["yandex_webmaster"] = await fetch_yandex_webmaster(site_url, date_from, date_to)
    except Exception as e:
        logger.warning(f"Яндекс Вебмастер недоступен: {e}")
        results["yandex_webmaster"] = None
    
    # Google Search Console (опциональный)
    try:
        results["google_search_console"] = await fetch_google_search_console(site_url, date_from, date_to)
    except Exception as e:
        logger.warning(f"Google Search Console недоступен: {e}")
        results["google_search_console"] = None
    
    # Проверка: хотя бы один обязательный источник доступен
    if results["yandex"] is None and results["google"] is None:
        raise AllSourcesUnavailableError("Все обязательные источники недоступны")
    
    return results
```

---

## 8. ОБУЧЕНИЕ И АДАПТАЦИЯ

### 8.1 Обучение на результатах

**Нет специфичного обучения.** Агент не обучается на результатах.

**Возможные улучшения в будущем:**
- Обучение на аномалиях (какие аномалии были ложными)
- Обучение на расхождениях (какие источники точнее)
- Обучение на качестве данных (какие источники надёжнее)

### 8.2 Адаптация к изменениям

**Адаптация к изменениям API:**
- Версионирование API клиентов
- Автоматическое обновление при изменении API
- Fallback на старые версии при ошибках

**Адаптация к новым источникам:**
- Модульная архитектура (легко добавить новый источник)
- Конфигурация источников в БД
- Динамическая загрузка источников

---

## 9. ЛОГИРОВАНИЕ И МОНИТОРИНГ

### 9.1 Логирование

**Уровни логирования:**

```python
import structlog

logger = structlog.get_logger("web_analytics_agent")

# INFO — нормальная работа
logger.info(
    "metrics_collected",
    project_id=project_id,
    date_from=date_from,
    date_to=date_to,
    sources=["yandex", "google"],
    metrics_count=len(daily_metrics)
)

# WARNING — частичный успех
logger.warning(
    "source_unavailable",
    project_id=project_id,
    source="yandex_webmaster",
    error="API timeout"
)

# ERROR — ошибка выполнения
logger.error(
    "collection_failed",
    project_id=project_id,
    error_code="API_UNAVAILABLE",
    error_message="Яндекс Метрика API недоступен"
)
```

### 9.2 Метрики для мониторинга

**Prometheus метрики:**

```python
from prometheus_client import Counter, Histogram, Gauge

# Счётчики
web_analytics_requests_total = Counter(
    "web_analytics_requests_total",
    "Total number of web analytics requests",
    ["project_id", "status"]
)

web_analytics_api_calls_total = Counter(
    "web_analytics_api_calls_total",
    "Total number of API calls",
    ["source", "status"]
)

# Гистограммы
web_analytics_duration_seconds = Histogram(
    "web_analytics_duration_seconds",
    "Duration of web analytics collection",
    ["project_id"]
)

# Gauges
web_analytics_sources_available = Gauge(
    "web_analytics_sources_available",
    "Number of available sources",
    ["project_id"]
)

web_analytics_anomalies_detected = Gauge(
    "web_analytics_anomalies_detected",
    "Number of anomalies detected",
    ["project_id"]
)
```

### 9.3 Event Store логирование

**Все события логируются в Event Store:**

```python
# Начало выполнения
await event_store.append(Event(
    type="web_analytics.started",
    correlation_id=correlation_id,
    payload={
        "project_id": project_id,
        "site_url": site_url,
        "date_from": date_from,
        "date_to": date_to
    }
))

# Сбор данных из источника
await event_store.append(Event(
    type="web_analytics.source_collected",
    correlation_id=correlation_id,
    payload={
        "source": "yandex",
        "metrics_count": len(metrics),
        "duration_ms": duration
    }
))

# Обнаружение аномалии
await event_store.append(Event(
    type="web_analytics.anomaly_detected",
    correlation_id=correlation_id,
    payload={
        "date": "2026-05-10",
        "metric": "visits",
        "current_value": 1000,
        "previous_value": 500,
        "change_percent": 100.0
    }
))

# Завершение выполнения
await event_store.append(Event(
    type="web_analytics.completed",
    correlation_id=correlation_id,
    payload={
        "project_id": project_id,
        "metrics_count": len(daily_metrics),
        "anomalies_count": len(anomalies),
        "duration_ms": duration
    }
))
```

---

## 10. ТЕСТИРОВАНИЕ

### 10.1 Unit тесты

**Тестирование сбора данных:**

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_collect_yandex_metrika():
    """Тест сбора данных из Яндекс Метрики"""
    client = YandexMetrikaClient(token="test_token")
    
    with patch.object(client, "_fetch") as mock_fetch:
        mock_fetch.return_value = {
            "data": [
                {"dimensions": [{"name": "2026-05-10"}], "metrics": [1000, 800, 3000, 0.45, 50]}
            ]
        }
        
        result = await client.get_metrics(
            counter_id="12345",
            date_from=date(2026, 5, 10),
            date_to=date(2026, 5, 10),
            metrics=["visits", "users", "pageviews", "bounce_rate", "conversions"]
        )
        
        assert len(result) == 1
        assert result[0]["date"] == "2026-05-10"
        assert result[0]["visits"] == 1000
```

**Тестирование усреднения данных:**

```python
@pytest.mark.asyncio
async def test_average_data():
    """Тест усреднения данных между источниками"""
    yandex_data = [{"date": "2026-05-10", "visits": 1000}]
    google_data = [{"date": "2026-05-10", "sessions": 950}]
    
    result = await average_data(yandex_data, google_data)
    
    assert result[0]["date"] == "2026-05-10"
    assert result[0]["visits"] == 975  # (1000 + 950) / 2
```

**Тестирование обнаружения аномалий:**

```python
@pytest.mark.asyncio
async def test_detect_anomalies():
    """Тест обнаружения аномалий"""
    current_data = [{"date": "2026-05-10", "visits": 1000}]
    previous_data = [{"date": "2026-05-09", "visits": 500}]
    
    anomalies = await detect_anomalies(current_data, previous_data)
    
    assert len(anomalies) == 1
    assert anomalies[0]["is_anomaly"] is True
    assert anomalies[0]["change_percent"] == 100.0
```

### 10.2 Integration тесты

**Тестирование полного цикла:**

```python
@pytest.mark.asyncio
async def test_full_cycle():
    """Тест полного цикла сбора метрик"""
    agent = WebAnalyticsAgent()
    
    task = Task(
        id="test-task",
        type="web_analytics",
        payload={
            "site_url": "https://example.com",
            "project_id": "test-project",
            "date_from": "2026-05-01",
            "date_to": "2026-05-10",
            "yandex_metrika_token": "test_token",
            "google_analytics_token": "test_token"
        }
    )
    
    result = await agent.execute_task(task)
    
    assert result.status == "success"
    assert len(result.data["daily_metrics"]) == 10
    assert "anomalies" in result.data
    assert "data_quality" in result.data
```

### 10.3 E2E тесты

**Тестирование через Event Bus:**

```python
@pytest.mark.asyncio
async def test_e2e_event_bus():
    """E2E тест через Event Bus"""
    event_bus = EventBus()
    agent = WebAnalyticsAgent(event_bus=event_bus)
    
    # Подписка на результат
    result_received = asyncio.Event()
    result_data = {}
    
    @event_handler("seo.web_analytics.completed")
    async def handle_result(event: Event):
        result_data.update(event.payload)
        result_received.set()
    
    # Отправка запроса
    await event_bus.publish(Event(
        type="seo.web_analytics.requested",
        correlation_id="test-correlation",
        payload={
            "site_url": "https://example.com",
            "project_id": "test-project",
            "date_from": "2026-05-01",
            "date_to": "2026-05-10",
            "yandex_metrika_token": "test_token",
            "google_analytics_token": "test_token"
        }
    ))
    
    # Ожидание результата
    await asyncio.wait_for(result_received.wait(), timeout=30)
    
    assert result_data["project_id"] == "test-project"
    assert len(result_data["daily_metrics"]) == 10
```

---

## 11. DEPLOYMENT

### 11.1 Конфигурация

**Environment variables:**

```bash
# API токены
YANDEX_METRIKA_TOKEN=your_token_here
GOOGLE_ANALYTICS_TOKEN=your_token_here
YANDEX_WEBMASTER_TOKEN=your_token_here  # optional
GOOGLE_SEARCH_CONSOLE_TOKEN=your_token_here  # optional

# Настройки
WEB_ANALYTICS_TIMEOUT=600  # 10 минут
WEB_ANALYTICS_RETRY_ATTEMPTS=10
WEB_ANALYTICS_RETRY_BACKOFF=4  # секунды

# База данных
DATABASE_URL=sqlite+aiosqlite:///./data/meai.db

# Obsidian
OBSIDIAN_VAULT_PATH=./obsidian/seo-magister

# Event Bus
EVENT_BUS_URL=redis://localhost:6379/0
```

### 11.2 Docker

**Dockerfile:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY AIM/ AIM/

CMD ["python", "-m", "aim.subagents.web_analytics"]
```

**docker-compose.yml:**

```yaml
version: '3.8'

services:
  web-analytics-agent:
    build: .
    environment:
      - YANDEX_METRIKA_TOKEN=${YANDEX_METRIKA_TOKEN}
      - GOOGLE_ANALYTICS_TOKEN=${GOOGLE_ANALYTICS_TOKEN}
      - DATABASE_URL=sqlite+aiosqlite:///./data/meai.db
      - EVENT_BUS_URL=redis://redis:6379/0
    volumes:
      - ./data:/app/data
      - ./obsidian:/app/obsidian
    depends_on:
      - redis
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

### 11.3 Мониторинг

**Health check endpoint:**

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent": "web-analytics",
        "version": "1.0.0",
        "sources": {
            "yandex_metrika": await check_yandex_metrika(),
            "google_analytics": await check_google_analytics()
        }
    }
```

**Prometheus metrics endpoint:**

```python
from prometheus_client import generate_latest

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )
```

### 11.4 Scaling

**Horizontal scaling:**
- Агент stateless → можно запустить несколько инстансов
- Event Bus распределяет задачи между инстансами
- Каждый инстанс обрабатывает свои задачи независимо

**Vertical scaling:**
- Увеличение CPU для параллельной обработки источников
- Увеличение RAM для кэширования данных
- Увеличение network bandwidth для API вызовов

---

## ПРИЛОЖЕНИЯ

### A. Примеры использования

**Пример 1: Базовый сбор метрик**

```python
from aim.subagents.web_analytics import WebAnalyticsAgent

agent = WebAnalyticsAgent()

result = await agent.execute_task(Task(
    type="web_analytics",
    payload={
        "site_url": "https://example.com",
        "project_id": "project-123",
        "date_from": "2026-05-01",
        "date_to": "2026-05-10",
        "yandex_metrika_token": "...",
        "google_analytics_token": "..."
    }
))

print(f"Собрано метрик: {len(result.data['daily_metrics'])}")
print(f"Обнаружено аномалий: {len(result.data['anomalies'])}")
```

**Пример 2: Сбор с опциональными источниками**

```python
result = await agent.execute_task(Task(
    type="web_analytics",
    payload={
        "site_url": "https://example.com",
        "project_id": "project-123",
        "date_from": "2026-05-01",
        "date_to": "2026-05-10",
        "yandex_metrika_token": "...",
        "google_analytics_token": "...",
        "yandex_webmaster_token": "...",  # опционально
        "google_search_console_token": "..."  # опционально
    }
))
```

### B. FAQ

**Q: Что делать, если один источник недоступен?**
A: Агент продолжит работу с другими источниками (graceful degradation). Результат будет помечен как `partial_success`.

**Q: Как часто нужно собирать метрики?**
A: Рекомендуется ежедневно. Агент может работать по расписанию через Event Bus.

**Q: Что делать при расхождениях > 50% между источниками?**
A: Агент сохранит оба значения и пометит флагом `large_discrepancy`. SEO Magister примет решение о дальнейших действиях.

**Q: Можно ли добавить новые источники данных?**
A: Да, архитектура модульная. Новые источники добавляются через конфигурацию.

### C. Changelog

**v1.0.0 (2026-05-10)**
- Первая версия спецификации
- Основные источники: Яндекс Метрика, Google Analytics
- Опциональные источники: Яндекс Вебмастер, Google Search Console
- Усреднение данных при расхождениях
- Обнаружение аномалий
- Graceful degradation
- Retry механизм (10 попыток)
- Event Bus интеграция
- Obsidian интеграция

---

**Дата создания:** 2026-05-10  
**Версия:** 1.0  
**Статус:** Draft  
**Автор:** meAI Architect  
**Следующий шаг:** Имплементация агента в `AIM/src/aim/subagents/web_analytics.py`
