# Search Console Agent - Спецификация

**Дата создания:** 2026-05-10  
**Версия:** 1.0  
**Статус:** Ready for Implementation  
**Приоритет:** P1 (Важный)  
**Домен:** SEO  
**Родительский Magister:** SEO Magister

---

## 1. ОБЗОР

### 1.1 Назначение

**Search Console Agent** — глаза системы в поисковых системах, который собирает данные о том, как сайт показывается в поисковой выдаче.

**Ключевые функции:**
- Сбор данных из Google Search Console и Яндекс Вебмастера
- Отслеживание запросов, позиций, показов, кликов, CTR
- Мониторинг проблем индексации
- Выявление ошибок сканирования и штрафов
- Передача данных в сыром виде для анализа верхнего уровня

### 1.2 Роль в системе

**Тип:** Subagent (исполнитель)  
**Родительский Magister:** SEO Magister  
**Домен:** SEO (поисковая оптимизация)  
**Автономность:** Высокая (работает по расписанию)

**Взаимодействие:**
- **Получает:** Задачи от SEO Magister (URL сайта, период анализа)
- **Отправляет:** Данные о поисковой выдаче (запросы, позиции, проблемы)
- **Использует:** Google Search Console API, Яндекс Вебмастер API

### 1.3 Уникальная ценность

**Почему критично для агентства:**

1. **Видимость в поиске**
   - Показывает, как сайт находится в поисковых системах
   - Видим запросы, по которым показывается сайт
   - Понимаем позиции в выдаче

2. **Упущенные возможности**
   - Web Analytics показывает, кто пришёл
   - Search Console показывает, кто НЕ пришёл (показы без кликов)
   - Низкий CTR = упущенный трафик

3. **Проблемы индексации**
   - Страницы не попали в индекс
   - Ошибки сканирования (поисковик не может прочитать)
   - Штрафы (сайт понижен в выдаче)

4. **Диагностика проблем**
   - Почему трафик не растёт?
   - Какие страницы не индексируются?
   - Какие запросы имеют низкий CTR?

5. **Данные для оптимизации**
   - Какие запросы приносят показы, но не клики
   - Какие страницы нужно оптимизировать
   - Какие проблемы нужно исправить

### 1.4 Границы ответственности

**Что делает агент:**
- ✅ Собирает данные из Google Search Console и Яндекс Вебмастера
- ✅ Отслеживает запросы, позиции, показы, клики, CTR
- ✅ Мониторит проблемы индексации, ошибки сканирования, штрафы
- ✅ Объединяет данные по запросам и страницам
- ✅ Передаёт данные в сыром виде (без выводов)
- ✅ Сохраняет историю в БД и Obsidian

**Что НЕ делает агент:**
- ❌ Не собирает метрики трафика (это Web Analytics Agent)
- ❌ Не анализирует конкурентов (это Competitor Analysis Agent)
- ❌ Не делает выводы и рекомендации (это задача SEO Magister)
- ❌ Не исправляет проблемы (это задача других агентов)

---

## 2. ВХОДНЫЕ ДАННЫЕ

### 2.1 Источники данных

**Обязательные источники:**

1. **Google Search Console API** — данные о поисковой выдаче Google
   - Запросы (queries)
   - Показы (impressions)
   - Клики (clicks)
   - CTR (click-through rate)
   - Средняя позиция (average position)
   - Проблемы индексации (coverage issues)
   - Ошибки сканирования (crawl errors)

2. **Яндекс Вебмастер API** — данные о поисковой выдаче Яндекса
   - Запросы (queries)
   - Показы (impressions)
   - Клики (clicks)
   - CTR (click-through rate)
   - Средняя позиция (average position)
   - Проблемы индексации (indexing issues)
   - Ошибки сканирования (crawl errors)

### 2.2 Входные параметры

**Обязательные параметры:**

```python
from pydantic import BaseModel, Field, HttpUrl
from datetime import date

class SearchConsoleInput(BaseModel):
    site_url: HttpUrl = Field(
        ...,
        description="URL сайта для анализа"
    )
    project_id: str = Field(
        ...,
        description="ID проекта (для изоляции данных)"
    )
    google_search_console_token: str = Field(
        ...,
        description="Токен Google Search Console"
    )
    yandex_webmaster_token: str = Field(
        ...,
        description="Токен Яндекс Вебмастера"
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
    dimensions: list[str] = Field(
        default=["query", "page", "date"],
        description="Измерения для группировки данных"
    )
    row_limit: int = Field(
        default=1000,
        description="Максимальное количество строк в результате"
    )
```

### 2.3 Валидация входных данных

**Правила валидации:**

1. **site_url** — валидный HTTP/HTTPS URL, доступен для проверки
2. **project_id** — уникальный, только буквы/цифры/дефис
3. **google_search_console_token** — валидный токен (проверка через API)
4. **yandex_webmaster_token** — валидный токен (проверка через API)
5. **date_from, date_to** — date_from <= date_to, не более 365 дней между датами
6. **dimensions** — список поддерживаемых измерений (query, page, date, country, device)
7. **row_limit** — от 1 до 25000 (лимит API)

**Ошибки валидации:**
- `INVALID_URL` — неверный формат URL
- `INVALID_PROJECT_ID` — неверный формат project_id
- `INVALID_TOKEN` — неверный токен API
- `INVALID_DATE_RANGE` — неверный диапазон дат
- `INVALID_DIMENSIONS` — неподдерживаемые измерения
- `INVALID_ROW_LIMIT` — неверный лимит строк

---

## 3. АЛГОРИТМ РАБОТЫ

### 3.1 Основные шаги

**Алгоритм (5 шагов):**

1. **Сбор данных из Google Search Console**
   - Запросы (queries) с метриками (показы, клики, CTR, позиции)
   - Страницы (pages) с метриками
   - Проблемы индексации (coverage issues)
   - Ошибки сканирования (crawl errors)

2. **Сбор данных из Яндекс Вебмастера**
   - Запросы (queries) с метриками (показы, клики, CTR, позиции)
   - Страницы (pages) с метриками
   - Проблемы индексации (indexing issues)
   - Ошибки сканирования (crawl errors)

3. **Объединение данных**
   - По запросам (если запрос есть и в Google, и в Яндексе)
   - По страницам (если страница есть в обоих источниках)
   - Сохранение исходных данных для аудита

4. **Проверка ошибок получения**
   - API недоступны
   - Данные неполные (пропущенные дни)
   - Проблемы с токенами

5. **Передача данных дальше**
   - Сохранение в БД (структурированные метрики)
   - Сохранение в Obsidian (история, проблемы)
   - Отправка SEO Magister через Event Bus

### 3.2 Детальный workflow

**Шаг 1: Сбор данных из Google Search Console**

```python
async def collect_google_search_console(
    site_url: str,
    date_from: date,
    date_to: date,
    dimensions: list[str]
) -> dict:
    """
    Сбор данных из Google Search Console
    
    Returns:
        {
            "queries": [
                {
                    "query": "медицинская клиника москва",
                    "impressions": 1000,
                    "clicks": 50,
                    "ctr": 0.05,
                    "position": 5.2
                },
                ...
            ],
            "pages": [
                {
                    "page": "https://example.com/services",
                    "impressions": 500,
                    "clicks": 25,
                    "ctr": 0.05
                },
                ...
            ],
            "coverage_issues": [
                {
                    "type": "excluded",
                    "reason": "Noindex tag",
                    "count": 10
                },
                ...
            ],
            "crawl_errors": [
                {
                    "url": "https://example.com/broken",
                    "error": "404 Not Found"
                },
                ...
            ]
        }
    """
```

**Шаг 2: Сбор данных из Яндекс Вебмастера**

```python
async def collect_yandex_webmaster(
    site_url: str,
    date_from: date,
    date_to: date
) -> dict:
    """
    Сбор данных из Яндекс Вебмастера
    
    Returns:
        {
            "queries": [
                {
                    "query": "медицинская клиника москва",
                    "impressions": 800,
                    "clicks": 40,
                    "ctr": 0.05,
                    "position": 6.1
                },
                ...
            ],
            "pages": [
                {
                    "page": "https://example.com/services",
                    "impressions": 400,
                    "clicks": 20,
                    "ctr": 0.05
                },
                ...
            ],
            "indexing_issues": [
                {
                    "type": "not_indexed",
                    "reason": "Robots.txt blocked",
                    "count": 5
                },
                ...
            ],
            "crawl_errors": [
                {
                    "url": "https://example.com/broken",
                    "error": "404 Not Found"
                },
                ...
            ]
        }
    """
```

**Шаг 3: Объединение данных**

```python
async def merge_data(
    google_data: dict,
    yandex_data: dict
) -> dict:
    """
    Объединение данных по запросам и страницам
    
    Returns:
        {
            "queries": [
                {
                    "query": "медицинская клиника москва",
                    "google": {
                        "impressions": 1000,
                        "clicks": 50,
                        "ctr": 0.05,
                        "position": 5.2
                    },
                    "yandex": {
                        "impressions": 800,
                        "clicks": 40,
                        "ctr": 0.05,
                        "position": 6.1
                    },
                    "total_impressions": 1800,
                    "total_clicks": 90
                },
                ...
            ],
            "pages": [...],
            "issues": {
                "google": [...],
                "yandex": [...]
            }
        }
    """
```

**Шаг 4: Проверка ошибок получения**

```python
async def check_data_quality(
    google_data: dict,
    yandex_data: dict
) -> dict:
    """
    Проверка качества данных
    
    Returns:
        {
            "sources_available": ["google", "yandex"],
            "sources_unavailable": [],
            "missing_dates": [],
            "issues_count": {
                "google": 10,
                "yandex": 5
            }
        }
    """
```

### 3.3 Специфичная логика

**Нет специфичных алгоритмов и формул.** Стандартная обработка: fetch → process → save.

**Объединение данных:**
- Простое объединение по ключу (query или page)
- Сохранение исходных данных от каждого источника
- Подсчёт общих показателей (total_impressions, total_clicks)

---

## 4. ВЫХОДНЫЕ ДАННЫЕ

### 4.1 Формат результата

**Структура результата:**

```python
from pydantic import BaseModel
from datetime import date

class QueryMetrics(BaseModel):
    query: str = Field(description="Поисковый запрос")
    google_impressions: int | None = Field(description="Показы в Google")
    google_clicks: int | None = Field(description="Клики в Google")
    google_ctr: float | None = Field(description="CTR в Google")
    google_position: float | None = Field(description="Средняя позиция в Google")
    yandex_impressions: int | None = Field(description="Показы в Яндексе")
    yandex_clicks: int | None = Field(description="Клики в Яндексе")
    yandex_ctr: float | None = Field(description="CTR в Яндексе")
    yandex_position: float | None = Field(description="Средняя позиция в Яндексе")
    total_impressions: int = Field(description="Всего показов")
    total_clicks: int = Field(description="Всего кликов")

class PageMetrics(BaseModel):
    page: str = Field(description="URL страницы")
    google_impressions: int | None = Field(description="Показы в Google")
    google_clicks: int | None = Field(description="Клики в Google")
    google_ctr: float | None = Field(description="CTR в Google")
    yandex_impressions: int | None = Field(description="Показы в Яндексе")
    yandex_clicks: int | None = Field(description="Клики в Яндексе")
    yandex_ctr: float | None = Field(description="CTR в Яндексе")
    total_impressions: int = Field(description="Всего показов")
    total_clicks: int = Field(description="Всего кликов")

class IndexingIssue(BaseModel):
    source: str = Field(description="Источник (google/yandex)")
    type: str = Field(description="Тип проблемы")
    reason: str = Field(description="Причина")
    count: int = Field(description="Количество страниц")
    urls: list[str] = Field(description="Примеры URL")

class SearchConsoleResult(BaseModel):
    project_id: str
    site_url: str
    date_from: date
    date_to: date
    queries: list[QueryMetrics]
    pages: list[PageMetrics]
    indexing_issues: list[IndexingIssue]
    crawl_errors: list[dict]
    data_quality: dict
    summary: dict  # total_impressions, total_clicks, avg_ctr, avg_position, etc.
```

### 4.2 Хранение данных

**База данных (структурированные метрики):**

```sql
CREATE TABLE search_console_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    site_url TEXT NOT NULL,
    date DATE NOT NULL,
    query TEXT NOT NULL,
    google_impressions INTEGER,
    google_clicks INTEGER,
    google_ctr REAL,
    google_position REAL,
    yandex_impressions INTEGER,
    yandex_clicks INTEGER,
    yandex_ctr REAL,
    yandex_position REAL,
    total_impressions INTEGER,
    total_clicks INTEGER,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_project_date (project_id, date),
    INDEX idx_query (query)
);

CREATE TABLE search_console_pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    site_url TEXT NOT NULL,
    date DATE NOT NULL,
    page TEXT NOT NULL,
    google_impressions INTEGER,
    google_clicks INTEGER,
    google_ctr REAL,
    yandex_impressions INTEGER,
    yandex_clicks INTEGER,
    yandex_ctr REAL,
    total_impressions INTEGER,
    total_clicks INTEGER,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_project_date (project_id, date),
    INDEX idx_page (page)
);

CREATE TABLE search_console_issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    site_url TEXT NOT NULL,
    date DATE NOT NULL,
    source TEXT NOT NULL,  -- google/yandex
    type TEXT NOT NULL,
    reason TEXT NOT NULL,
    count INTEGER,
    urls TEXT,  -- JSON array
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Obsidian vault (история, проблемы):**

```
obsidian/seo-magister/
├── raw/
│   └── search-console/
│       └── {project_id}/
│           └── YYYY-MM-DD.md
├── wiki/
│   ├── sources/
│   │   └── search-console-{project_id}-YYYY-MM-DD.md
│   ├── concepts/
│   │   └── search-visibility-{project_id}.md
│   └── connections/
│       └── search-console-to-analytics-{project_id}.md
└── decisions/
    └── indexing-issues-{project_id}.md
```

**Формат файла в raw/:**

```markdown
---
source: search-console
project_id: project-123
site_url: https://example.com
date_from: 2026-05-01
date_to: 2026-05-10
queries_count: 100
pages_count: 50
issues_count: 5
collected_at: 2026-05-10T16:00:00Z
status: processed
output: wiki/sources/search-console-project-123-2026-05-10.md
---

# Search Console - project-123 - 2026-05-01 to 2026-05-10

## Метрики

- Всего запросов: 100
- Всего показов: 10000
- Всего кликов: 500
- Средний CTR: 5%
- Средняя позиция: 8.5
- Проблем индексации: 5

## Топ-10 запросов

| Запрос | Показы | Клики | CTR | Позиция |
|--------|--------|-------|-----|---------|
| медицинская клиника москва | 1000 | 50 | 5% | 5.2 |
...

## Проблемы индексации

- Excluded (Noindex tag): 10 страниц
- Not indexed (Robots.txt blocked): 5 страниц
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
- Целевое значение: 100% (оба API доступны)
- Warning: < 100% (один источник недоступен)
- Critical: < 50% (оба источника недоступны)

**Актуальность данных:**
- Целевое значение: данные не старше 1 дня
- Warning: данные старше 1 дня
- Critical: данные старше 3 дней

**Качество данных:**
- Целевое значение: нет пропущенных дней
- Warning: 1-2 пропущенных дня
- Critical: > 2 пропущенных дней

### 5.3 Специфичные метрики

**Нет специфичных метрик.** Используются стандартные метрики производительности и качества.

### 5.4 Дашборд метрик

**Ежедневный дашборд:**
- Количество проектов проанализировано
- Среднее время выполнения
- Недоступные источники
- Проблемы индексации за день
- Топ-10 запросов с низким CTR

**Еженедельный отчёт:**
- Динамика показов и кликов по всем проектам
- Сравнение с предыдущей неделей
- Топ-10 проектов по росту показов
- Топ-10 проблем индексации

---
## 6. ИНТЕГРАЦИИ

### 6.1 Event Bus Integration

**Входящие события:**

```python
# Получение задачи от SEO Magister
@event_handler("seo.search_console.requested")
async def handle_search_console_request(event: Event):
    """
    Обработка запроса на сбор данных из Search Console
    
    Event payload:
        {
            "correlation_id": "uuid",
            "site_url": "https://example.com",
            "project_id": "project-123",
            "date_from": "2026-05-01",
            "date_to": "2026-05-10",
            "google_search_console_token": "...",
            "yandex_webmaster_token": "...",
            "dimensions": ["query", "page", "date"],
            "row_limit": 1000
        }
    """
```

**Исходящие события:**

```python
# Отправка результатов SEO Magister
await event_bus.publish(Event(
    type="seo.search_console.completed",
    correlation_id=correlation_id,
    payload={
        "project_id": "project-123",
        "site_url": "https://example.com",
        "date_from": "2026-05-01",
        "date_to": "2026-05-10",
        "queries": [...],
        "pages": [...],
        "indexing_issues": [...],
        "crawl_errors": [...],
        "data_quality": {...},
        "summary": {...},
        "obsidian_output": "obsidian/seo-magister/wiki/sources/search-console-project-123-2026-05-10.md"
    }
))

# Отправка ошибки
await event_bus.publish(Event(
    type="seo.search_console.failed",
    correlation_id=correlation_id,
    payload={
        "error_code": "API_UNAVAILABLE",
        "error_message": "Google Search Console API недоступен",
        "retry_after": 300
    }
))
```

### 6.2 API Integrations

**Google Search Console API:**

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

class GoogleSearchConsoleClient:
    def __init__(self, credentials: Credentials):
        self.service = build('searchconsole', 'v1', credentials=credentials)
    
    async def get_search_analytics(
        self,
        site_url: str,
        date_from: date,
        date_to: date,
        dimensions: list[str] = ["query"]
    ) -> list[dict]:
        """
        Получение данных о поисковой выдаче
        
        Returns:
            [
                {
                    "keys": ["медицинская клиника москва"],
                    "impressions": 1000,
                    "clicks": 50,
                    "ctr": 0.05,
                    "position": 5.2
                },
                ...
            ]
        """
        request = {
            'startDate': date_from.isoformat(),
            'endDate': date_to.isoformat(),
            'dimensions': dimensions,
            'rowLimit': 25000
        }
        
        response = self.service.searchanalytics().query(
            siteUrl=site_url,
            body=request
        ).execute()
        
        return response.get('rows', [])
    
    async def get_coverage_issues(
        self,
        site_url: str
    ) -> list[dict]:
        """
        Получение проблем индексации
        
        Returns:
            [
                {
                    "type": "excluded",
                    "reason": "Noindex tag",
                    "count": 10,
                    "examples": [...]
                },
                ...
            ]
        """
        response = self.service.urlInspection().index().inspect(
            body={'inspectionUrl': site_url, 'siteUrl': site_url}
        ).execute()
        
        return response.get('inspectionResult', {}).get('indexStatusResult', {})
```

**Яндекс Вебмастер API:**

```python
from aiohttp import ClientSession

class YandexWebmasterClient:
    BASE_URL = "https://api.webmaster.yandex.net/v4"
    
    def __init__(self, token: str):
        self.token = token
    
    async def get_search_queries(
        self,
        host_id: str,
        date_from: date,
        date_to: date
    ) -> list[dict]:
        """
        Получение поисковых запросов
        
        Returns:
            [
                {
                    "query": "медицинская клиника москва",
                    "impressions": 800,
                    "clicks": 40,
                    "ctr": 0.05,
                    "position": 6.1
                },
                ...
            ]
        """
        async with ClientSession() as session:
            url = f"{self.BASE_URL}/user/{host_id}/search-queries/popular"
            params = {
                "date_from": date_from.isoformat(),
                "date_to": date_to.isoformat()
            }
            headers = {
                "Authorization": f"OAuth {self.token}"
            }
            
            async with session.get(url, params=params, headers=headers) as response:
                data = await response.json()
                return data.get('queries', [])
    
    async def get_indexing_issues(
        self,
        host_id: str
    ) -> list[dict]:
        """
        Получение проблем индексации
        
        Returns:
            [
                {
                    "type": "not_indexed",
                    "reason": "Robots.txt blocked",
                    "count": 5,
                    "urls": [...]
                },
                ...
            ]
        """
        async with ClientSession() as session:
            url = f"{self.BASE_URL}/user/{host_id}/indexing-stats"
            headers = {
                "Authorization": f"OAuth {self.token}"
            }
            
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                return data.get('issues', [])
```

### 6.3 Database Integration

**Сохранение метрик:**

```python
from meai.storage.database import get_session
from sqlalchemy import insert, select

async def save_queries(queries: list[QueryMetrics]):
    async with get_session() as session:
        for query in queries:
            stmt = insert(search_console_queries).values(
                project_id=query.project_id,
                site_url=query.site_url,
                date=query.date,
                query=query.query,
                google_impressions=query.google_impressions,
                google_clicks=query.google_clicks,
                google_ctr=query.google_ctr,
                google_position=query.google_position,
                yandex_impressions=query.yandex_impressions,
                yandex_clicks=query.yandex_clicks,
                yandex_ctr=query.yandex_ctr,
                yandex_position=query.yandex_position,
                total_impressions=query.total_impressions,
                total_clicks=query.total_clicks
            ).on_conflict_do_update(
                index_elements=["project_id", "date", "query"],
                set_={
                    "google_impressions": query.google_impressions,
                    "google_clicks": query.google_clicks,
                    "yandex_impressions": query.yandex_impressions,
                    "yandex_clicks": query.yandex_clicks,
                    "total_impressions": query.total_impressions,
                    "total_clicks": query.total_clicks
                }
            )
            await session.execute(stmt)
        await session.commit()
```

### 6.4 Obsidian Integration

**Сохранение в vault:**

```python
from meai.memory.obsidian import ObsidianVault

async def save_to_obsidian(result: SearchConsoleResult):
    vault = ObsidianVault("obsidian/seo-magister")
    
    # Сохранение в raw/
    raw_path = f"raw/search-console/{result.project_id}/{result.date_to}.md"
    await vault.write_note(
        path=raw_path,
        content=format_raw_data(result),
        frontmatter={
            "source": "search-console",
            "project_id": result.project_id,
            "site_url": result.site_url,
            "date_from": result.date_from.isoformat(),
            "date_to": result.date_to.isoformat(),
            "queries_count": len(result.queries),
            "pages_count": len(result.pages),
            "issues_count": len(result.indexing_issues),
            "collected_at": datetime.now(UTC).isoformat(),
            "status": "processed",
            "output": f"wiki/sources/search-console-{result.project_id}-{result.date_to}.md"
        }
    )
    
    # Сохранение в wiki/sources/
    wiki_path = f"wiki/sources/search-console-{result.project_id}-{result.date_to}.md"
    await vault.write_note(
        path=wiki_path,
        content=format_wiki_summary(result),
        frontmatter={
            "type": "source",
            "agent": "search-console",
            "project_id": result.project_id,
            "date": result.date_to.isoformat()
        }
    )
```

---

## 7. ОБРАБОТКА ОШИБОК

### 7.1 Типы ошибок

**API_UNAVAILABLE:**
- Google Search Console API недоступен
- Яндекс Вебмастер API недоступен

**Стратегия:**
- Retry с exponential backoff (10 попыток)
- Если один источник недоступен → продолжить с другим (graceful degradation)
- Если оба источника недоступны → эскалация → SEO Magister

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

**SITE_NOT_VERIFIED:**
- Сайт не верифицирован в Search Console или Вебмастере

**Стратегия:**
- Возврат ошибки с инструкцией по верификации
- Эскалация → User (нужно верифицировать сайт)

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
) -> dict[str, dict]:
    """
    Сбор данных со всех источников с graceful degradation
    
    Если один источник недоступен → продолжить с другим
    """
    results = {}
    
    # Google Search Console (обязательный)
    try:
        results["google"] = await fetch_google_search_console(site_url, date_from, date_to)
    except Exception as e:
        logger.error(f"Google Search Console недоступен: {e}")
        results["google"] = None
    
    # Яндекс Вебмастер (обязательный)
    try:
        results["yandex"] = await fetch_yandex_webmaster(site_url, date_from, date_to)
    except Exception as e:
        logger.error(f"Яндекс Вебмастер недоступен: {e}")
        results["yandex"] = None
    
    # Проверка: хотя бы один источник доступен
    if results["google"] is None and results["yandex"] is None:
        raise AllSourcesUnavailableError("Все источники недоступны")
    
    return results
```

---

## 8. ОБУЧЕНИЕ И АДАПТАЦИЯ

### 8.1 Обучение на результатах

**Нет специфичного обучения.** Агент не обучается на результатах.

**Возможные улучшения в будущем:**
- Обучение на проблемах индексации (какие проблемы критичны)
- Обучение на запросах (какие запросы важны для бизнеса)
- Обучение на CTR (какой CTR считается низким для разных позиций)

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

logger = structlog.get_logger("search_console_agent")

# INFO — нормальная работа
logger.info(
    "data_collected",
    project_id=project_id,
    date_from=date_from,
    date_to=date_to,
    sources=["google", "yandex"],
    queries_count=len(queries),
    pages_count=len(pages)
)

# WARNING — частичный успех
logger.warning(
    "source_unavailable",
    project_id=project_id,
    source="google",
    error="API timeout"
)

# ERROR — ошибка выполнения
logger.error(
    "collection_failed",
    project_id=project_id,
    error_code="API_UNAVAILABLE",
    error_message="Google Search Console API недоступен"
)
```

### 9.2 Метрики для мониторинга

**Prometheus метрики:**

```python
from prometheus_client import Counter, Histogram, Gauge

# Счётчики
search_console_requests_total = Counter(
    "search_console_requests_total",
    "Total number of search console requests",
    ["project_id", "status"]
)

search_console_api_calls_total = Counter(
    "search_console_api_calls_total",
    "Total number of API calls",
    ["source", "status"]
)

# Гистограммы
search_console_duration_seconds = Histogram(
    "search_console_duration_seconds",
    "Duration of search console data collection",
    ["project_id"]
)

# Gauges
search_console_sources_available = Gauge(
    "search_console_sources_available",
    "Number of available sources",
    ["project_id"]
)

search_console_issues_detected = Gauge(
    "search_console_issues_detected",
    "Number of indexing issues detected",
    ["project_id", "source"]
)
```

### 9.3 Event Store логирование

**Все события логируются в Event Store:**

```python
# Начало выполнения
await event_store.append(Event(
    type="search_console.started",
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
    type="search_console.source_collected",
    correlation_id=correlation_id,
    payload={
        "source": "google",
        "queries_count": len(queries),
        "pages_count": len(pages),
        "duration_ms": duration
    }
))

# Обнаружение проблемы индексации
await event_store.append(Event(
    type="search_console.issue_detected",
    correlation_id=correlation_id,
    payload={
        "source": "google",
        "type": "excluded",
        "reason": "Noindex tag",
        "count": 10
    }
))

# Завершение выполнения
await event_store.append(Event(
    type="search_console.completed",
    correlation_id=correlation_id,
    payload={
        "project_id": project_id,
        "queries_count": len(queries),
        "pages_count": len(pages),
        "issues_count": len(issues),
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
async def test_collect_google_search_console():
    """Тест сбора данных из Google Search Console"""
    client = GoogleSearchConsoleClient(credentials=mock_credentials)
    
    with patch.object(client.service.searchanalytics(), "query") as mock_query:
        mock_query.return_value.execute.return_value = {
            "rows": [
                {
                    "keys": ["медицинская клиника москва"],
                    "impressions": 1000,
                    "clicks": 50,
                    "ctr": 0.05,
                    "position": 5.2
                }
            ]
        }
        
        result = await client.get_search_analytics(
            site_url="https://example.com",
            date_from=date(2026, 5, 1),
            date_to=date(2026, 5, 10),
            dimensions=["query"]
        )
        
        assert len(result) == 1
        assert result[0]["keys"][0] == "медицинская клиника москва"
        assert result[0]["impressions"] == 1000
```

**Тестирование объединения данных:**

```python
@pytest.mark.asyncio
async def test_merge_data():
    """Тест объединения данных по запросам"""
    google_data = {
        "queries": [
            {"query": "медицинская клиника москва", "impressions": 1000, "clicks": 50}
        ]
    }
    yandex_data = {
        "queries": [
            {"query": "медицинская клиника москва", "impressions": 800, "clicks": 40}
        ]
    }
    
    result = await merge_data(google_data, yandex_data)
    
    assert len(result["queries"]) == 1
    assert result["queries"][0]["query"] == "медицинская клиника москва"
    assert result["queries"][0]["total_impressions"] == 1800
    assert result["queries"][0]["total_clicks"] == 90
```

### 10.2 Integration тесты

**Тестирование полного цикла:**

```python
@pytest.mark.asyncio
async def test_full_cycle():
    """Тест полного цикла сбора данных"""
    agent = SearchConsoleAgent()
    
    task = Task(
        id="test-task",
        type="search_console",
        payload={
            "site_url": "https://example.com",
            "project_id": "test-project",
            "date_from": "2026-05-01",
            "date_to": "2026-05-10",
            "google_search_console_token": "test_token",
            "yandex_webmaster_token": "test_token"
        }
    )
    
    result = await agent.execute_task(task)
    
    assert result.status == "success"
    assert len(result.data["queries"]) > 0
    assert len(result.data["pages"]) > 0
    assert "indexing_issues" in result.data
    assert "data_quality" in result.data
```

### 10.3 E2E тесты

**Тестирование через Event Bus:**

```python
@pytest.mark.asyncio
async def test_e2e_event_bus():
    """E2E тест через Event Bus"""
    event_bus = EventBus()
    agent = SearchConsoleAgent(event_bus=event_bus)
    
    # Подписка на результат
    result_received = asyncio.Event()
    result_data = {}
    
    @event_handler("seo.search_console.completed")
    async def handle_result(event: Event):
        result_data.update(event.payload)
        result_received.set()
    
    # Отправка запроса
    await event_bus.publish(Event(
        type="seo.search_console.requested",
        correlation_id="test-correlation",
        payload={
            "site_url": "https://example.com",
            "project_id": "test-project",
            "date_from": "2026-05-01",
            "date_to": "2026-05-10",
            "google_search_console_token": "test_token",
            "yandex_webmaster_token": "test_token"
        }
    ))
    
    # Ожидание результата
    await asyncio.wait_for(result_received.wait(), timeout=30)
    
    assert result_data["project_id"] == "test-project"
    assert len(result_data["queries"]) > 0
```

---

## 11. DEPLOYMENT

### 11.1 Конфигурация

**Environment variables:**

```bash
# API токены
GOOGLE_SEARCH_CONSOLE_TOKEN=your_token_here
YANDEX_WEBMASTER_TOKEN=your_token_here

# Настройки
SEARCH_CONSOLE_TIMEOUT=600  # 10 минут
SEARCH_CONSOLE_RETRY_ATTEMPTS=10
SEARCH_CONSOLE_RETRY_BACKOFF=4  # секунды

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

CMD ["python", "-m", "aim.subagents.search_console"]
```

**docker-compose.yml:**

```yaml
version: '3.8'

services:
  search-console-agent:
    build: .
    environment:
      - GOOGLE_SEARCH_CONSOLE_TOKEN=${GOOGLE_SEARCH_CONSOLE_TOKEN}
      - YANDEX_WEBMASTER_TOKEN=${YANDEX_WEBMASTER_TOKEN}
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
        "agent": "search-console",
        "version": "1.0.0",
        "sources": {
            "google": await check_google_search_console(),
            "yandex": await check_yandex_webmaster()
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

**Пример 1: Базовый сбор данных**

```python
from aim.subagents.search_console import SearchConsoleAgent

agent = SearchConsoleAgent()

result = await agent.execute_task(Task(
    type="search_console",
    payload={
        "site_url": "https://example.com",
        "project_id": "project-123",
        "date_from": "2026-05-01",
        "date_to": "2026-05-10",
        "google_search_console_token": "...",
        "yandex_webmaster_token": "..."
    }
))

print(f"Собрано запросов: {len(result.data['queries'])}")
print(f"Собрано страниц: {len(result.data['pages'])}")
print(f"Обнаружено проблем: {len(result.data['indexing_issues'])}")
```

**Пример 2: Сбор с группировкой по страницам**

```python
result = await agent.execute_task(Task(
    type="search_console",
    payload={
        "site_url": "https://example.com",
        "project_id": "project-123",
        "date_from": "2026-05-01",
        "date_to": "2026-05-10",
        "google_search_console_token": "...",
        "yandex_webmaster_token": "...",
        "dimensions": ["page", "query"]  # группировка по страницам и запросам
    }
))
```

### B. FAQ

**Q: Что делать, если один источник недоступен?**
A: Агент продолжит работу с другим источником (graceful degradation). Результат будет помечен как `partial_success`.

**Q: Как часто нужно собирать данные?**
A: Рекомендуется ежедневно. Агент может работать по расписанию через Event Bus.

**Q: Что делать при проблемах индексации?**
A: Агент только собирает данные о проблемах. SEO Magister анализирует их и принимает решение о дальнейших действиях.

**Q: Можно ли добавить новые источники данных?**
A: Да, архитектура модульная. Новые источники добавляются через конфигурацию.

### C. Changelog

**v1.0.0 (2026-05-10)**
- Первая версия спецификации
- Источники: Google Search Console, Яндекс Вебмастер
- Сбор запросов, страниц, проблем индексации
- Объединение данных по запросам и страницам
- Graceful degradation
- Retry механизм (10 попыток)
- Event Bus интеграция
- Obsidian интеграция

---

**Дата создания:** 2026-05-10  
**Версия:** 1.0  
**Статус:** ✅ Готов к имплементации  
**Автор:** meAI Architect  
**Следующий шаг:** Имплементация агента в `AIM/src/aim/subagents/search_console.py`
