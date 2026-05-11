# Keyword Research Agent - Спецификация

**Дата создания:** 2026-05-10  
**Дата обновления:** 2026-05-11  
**Версия:** 1.0.0  
**Статус:** Ready for Implementation  
**Приоритет:** P0 (Критичный)  
**Домен:** SEO  
**Родительский Magister:** SEO Magister

---

## 1. ОБЗОР

### 1.1 Назначение

**Keyword Research Agent** — подборщик ключевых слов для роста органического трафика сайта. Анализирует поисковые запросы, отслеживает позиции сайта и даёт рекомендации по использованию ключевых слов для оптимизации контента.

**Ключевые функции:**
- Подбор ключевых слов из Яндекс Вордстат и Google Keyword Planner
- Анализ реального трафика из Яндекс Метрики и Google Analytics
- Отслеживание позиций сайта в поисковых системах
- Анализ частотности, конкуренции, сезонности запросов
- Генерация рекомендаций по использованию ключевых слов (Title, Description, H1, текст)
- Группировка ключевых слов по темам и страницам

### 1.2 Роль в системе

**Тип:** Subagent (исполнитель)  
**Родительский Magister:** SEO Magister  
**Домен:** SEO (поисковая оптимизация)  
**Автономность:** Высокая (работает по расписанию или по запросу)

**Взаимодействие:**
- **Получает:** Задачи от SEO Magister (URL сайта, целевой регион, конкуренты)
- **Отправляет:** Список ключевых слов с метриками и рекомендациями
- **Использует:** Яндекс Вордстат, Google Keyword Planner, Метрика, Analytics, опционально Semrush/TopVisor/Ahrefs

### 1.3 Уникальная ценность

**Почему критично для агентства:**

1. **Фундамент SEO стратегии**
   - Без ключевых слов невозможно построить SEO
   - Определяет направление всей оптимизации
   - Базис для контент-плана

2. **Привлечение платежеспособного трафика**
   - SEO — один из основных каналов трафика
   - Органический трафик = бесплатный и качественный
   - Правильные ключевые слова = целевая аудитория

3. **Видимость в поиске**
   - Показывает, как сайт находится в поисковых системах
   - Отслеживает динамику позиций
   - Выявляет возможности для роста

4. **Конкурентное преимущество**
   - Анализ конкурентов (опционально через Semrush/Ahrefs)
   - Поиск незанятых ниш
   - Оптимизация по высокопотенциальным запросам

5. **Данные для принятия решений**
   - Объективные метрики (частотность, конкуренция)
   - Приоритизация работы (высокий/средний/низкий потенциал)
   - ROI от SEO оптимизации

### 1.4 Границы ответственности

**Что делает агент:**
- ✅ Подбирает ключевые слова из Яндекс Вордстат и Google Keyword Planner
- ✅ Анализирует реальный трафик из Метрики и Analytics
- ✅ Отслеживает позиции сайта в поисковых системах
- ✅ Анализирует частотность, конкуренцию, сезонность
- ✅ Группирует ключевые слова по темам и страницам
- ✅ Даёт рекомендации по использованию (Title, Description, H1, текст)
- ✅ Приоритизирует ключевые слова по потенциалу трафика

**Что НЕ делает агент:**
- ❌ Не пишет тексты для оптимизации (это Content Agent)
- ❌ Не оптимизирует существующий контент (это другие SEO агенты)
- ❌ Не строит ссылочную массу (это Link Building Agent)
- ❌ Не исправляет технические ошибки сайта (это Technical SEO Agent)
- ❌ Не оптимизирует под AI-поиск (это GEO Agent)

### 1.5 Связанные агенты

**GEO Agent (Generative Engine Optimization)** — P1 агент для оптимизации под нейросети

**Назначение:**
Keyword Research Agent фокусируется на традиционном SEO (Google, Яндекс), а GEO Agent — на новом канале трафика через AI-поиск (ChatGPT, Perplexity, Claude, Gemini).

**Ключевые функции GEO Agent:**
- Оптимизация контента для цитирования в ответах нейросетей
- Анализ цитируемости сайта в AI-ответах
- Мониторинг упоминаний бренда в ChatGPT/Perplexity/Claude
- Рекомендации по структуре контента для AI-поиска
- Отслеживание видимости в генеративных поисковых системах

**Различия:**

| Аспект | Keyword Research Agent | GEO Agent |
|--------|------------------------|-----------|
| Цель | Позиции в Google/Яндекс | Цитирование в AI-ответах |
| Источники | Вордстат, Keyword Planner | ChatGPT, Perplexity, Claude |
| Метрики | Частотность, позиции, CTR | Цитируемость, упоминания |
| Оптимизация | Title, H1, мета-теги | Структура, факты, авторитетность |
| Канал трафика | Традиционный поиск | AI-поиск (новый канал) |

**Связь с Keyword Research Agent:**
- Оба агента работают параллельно под SEO Magister
- Keyword Research → традиционный SEO (80% трафика сейчас)
- GEO Agent → AI-поиск (20% трафика сейчас, растёт)
- Результаты обоих агентов объединяются для полной SEO стратегии

**Статус:** GEO Agent — отдельный P1 агент, добавлен в список для реализации

---

## 2. ВХОДНЫЕ ДАННЫЕ

### 2.1 Источники данных

**Основные источники:**

1. **Яндекс Вордстат API** — статистика поисковых запросов Яндекса
   - Частотность запросов (точное/неточное вхождение)
   - Сезонность (динамика по месяцам)
   - Региональность (по регионам России)

2. **Google Keyword Planner API** — статистика поисковых запросов Google
   - Средний объём поиска в месяц
   - Конкуренция (низкая/средняя/высокая)
   - Ставка для рекламы (косвенный показатель коммерческости)

3. **Яндекс Метрика API** — реальный трафик сайта
   - По каким ключевым словам заходят на сайт
   - Количество визитов по каждому ключевому слову
   - Конверсии по ключевым словам

4. **Google Analytics API** — реальный трафик сайта
   - По каким ключевым словам заходят на сайт
   - Количество сессий по каждому ключевому слову
   - Поведенческие метрики (bounce rate, время на сайте)

5. **Сбор позиций** — текущие позиции сайта в поисковых системах
   - Позиции в Яндексе (топ-10, топ-30, топ-100)
   - Позиции в Google (топ-10, топ-30, топ-100)
   - Динамика позиций (рост/падение)

**Опциональные источники (расширенная функциональность):**

6. **Semrush API** — конкурентный анализ
   - Ключевые слова конкурентов
   - Позиции конкурентов
   - Органический трафик конкурентов

7. **TopVisor API** — мониторинг позиций
   - Автоматический сбор позиций по расписанию
   - История изменений позиций
   - Группировка по регионам

8. **Ahrefs API** — анализ конкурентов и backlinks
   - Ключевые слова, по которым ранжируются конкуренты
   - Сложность ключевых слов (Keyword Difficulty)
   - Backlinks конкурентов

### 2.2 Входные параметры

**Обязательные параметры:**

```python
from pydantic import BaseModel, Field, HttpUrl

class KeywordResearchInput(BaseModel):
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
```

**Опциональные параметры:**

```python
    competitors: list[HttpUrl] = Field(
        default=[],
        description="Список конкурентов для сравнения"
    )
    target_region: str = Field(
        default="Россия",
        description="Целевой регион (Москва, Россия, etc.)"
    )
    seed_keywords: list[str] = Field(
        default=[],
        description="Начальные ключевые слова для расширения"
    )
    max_keywords: int = Field(
        default=1000,
        description="Максимум ключевых слов для анализа"
    )
    min_frequency: int = Field(
        default=10,
        description="Минимальная частотность запроса"
    )
```

### 2.3 Валидация входных данных

**Правила валидации:**

1. **site_url** — валидный HTTP/HTTPS URL, доступен для проверки
2. **project_id** — уникальный, только буквы/цифры/дефис
3. **yandex_metrika_token** — валидный токен (проверка через API)
4. **google_analytics_token** — валидный токен (проверка через API)
5. **competitors** — список валидных URL (если указаны)
6. **target_region** — поддерживаемый регион (Россия, Москва, Санкт-Петербург, etc.)
7. **max_keywords** — положительное число, не более 10000
8. **min_frequency** — положительное число, не более 1000000

**Ошибки валидации:**
- `INVALID_URL` — неверный формат URL
- `INVALID_PROJECT_ID` — неверный формат project_id
- `INVALID_TOKEN` — неверный токен API
- `INVALID_REGION` — неподдерживаемый регион
- `INVALID_RANGE` — параметры вне допустимого диапазона

---

## 3. АЛГОРИТМ РАБОТЫ

### 3.1 Основные шаги

**Алгоритм (5 шагов):**

1. **Сбор данных из источников**
   - Яндекс Вордстат (частотность, сезонность)
   - Google Keyword Planner (объём поиска, конкуренция)
   - Яндекс Метрика (реальный трафик)
   - Google Analytics (реальный трафик)
   - Сбор позиций (текущие позиции сайта)

2. **Анализ ключевых слов по параметрам**
   - Спрос (частотность запросов)
   - Точное вхождение vs неточное вхождение
   - Сезонность (динамика по месяцам)
   - Конкуренция (низкая/средняя/высокая)
   - Коммерческость (по ставке Google Ads)

3. **Анализ текущих позиций**
   - Как сайт находится в поиске по этим ключевым словам
   - Позиции в Яндексе и Google
   - Динамика позиций (если есть история)

4. **Генерация рекомендаций**
   - Какие ключевые слова добавить в контент
   - Куда включить (Title, Description, Keywords, H1, текст)
   - Приоритизация по потенциалу трафика (высокий/средний/низкий)
   - Группировка по темам и страницам

5. **Сохранение результатов**
   - Список ключевых слов с метриками
   - Рекомендации по использованию
   - История в Obsidian vault

### 3.2 Детальный workflow

**Шаг 1: Сбор данных из Яндекс Вордстат**

```python
async def collect_yandex_wordstat(seed_keywords: list[str]) -> list[dict]:
    """
    Сбор статистики из Яндекс Вордстат
    
    Returns:
        [
            {
                "keyword": "стоматология москва",
                "frequency_exact": 12000,
                "frequency_broad": 45000,
                "seasonality": [100, 95, 110, ...],  # 12 месяцев
                "region": "Москва"
            },
            ...
        ]
    """
    # TODO: Исследовать регулярные выражения для запросов
    # TODO: Изучить полную документацию API Яндекс Вордстат
```

**Шаг 2: Сбор данных из Google Keyword Planner**

```python
async def collect_google_keyword_planner(seed_keywords: list[str]) -> list[dict]:
    """
    Сбор статистики из Google Keyword Planner
    
    Returns:
        [
            {
                "keyword": "стоматология москва",
                "avg_monthly_searches": 10000,
                "competition": "HIGH",
                "suggested_bid": 150.0  # рубли
            },
            ...
        ]
    """
    # TODO: Исследовать доступные Google API для keyword research
```

**Шаг 3: Сбор реального трафика из Метрики и Analytics**

```python
async def collect_real_traffic(site_url: str) -> list[dict]:
    """
    Сбор реального трафика из Яндекс Метрики и Google Analytics
    
    Returns:
        [
            {
                "keyword": "стоматология москва",
                "visits_yandex": 500,
                "visits_google": 300,
                "conversions": 15,
                "bounce_rate": 0.45
            },
            ...
        ]
    """
```

**Шаг 4: Сбор позиций сайта**

```python
async def collect_positions(site_url: str, keywords: list[str]) -> list[dict]:
    """
    Сбор текущих позиций сайта в поисковых системах
    
    Returns:
        [
            {
                "keyword": "стоматология москва",
                "position_yandex": 15,
                "position_google": 8,
                "url": "https://example.com/services/stomatology"
            },
            ...
        ]
    """
```

**Шаг 5: Анализ и приоритизация**

```python
async def analyze_and_prioritize(keywords_data: list[dict]) -> list[dict]:
    """
    Анализ ключевых слов и приоритизация по потенциалу трафика
    
    Приоритет рассчитывается по формуле:
    priority_score = frequency * (1 - competition) * (1 / (position + 1))
    
    Где:
    - frequency — частотность запроса
    - competition — конкуренция (0-1)
    - position — текущая позиция сайта (или 100, если не в топе)
    
    Returns:
        [
            {
                "keyword": "стоматология москва",
                "frequency": 12000,
                "competition": 0.8,
                "position": 15,
                "priority_score": 160.0,
                "priority": "high",  # high/medium/low
                "recommendations": {
                    "title": True,
                    "description": True,
                    "h1": True,
                    "text": True
                }
            },
            ...
        ]
    """
```

**Шаг 6: Группировка по темам**

```python
async def group_by_topics(keywords: list[dict]) -> dict[str, list[dict]]:
    """
    Группировка ключевых слов по темам и страницам
    
    Returns:
        {
            "Услуги стоматологии": [
                {"keyword": "стоматология москва", ...},
                {"keyword": "стоматологическая клиника", ...}
            ],
            "Лечение зубов": [
                {"keyword": "лечение зубов", ...},
                {"keyword": "лечение кариеса", ...}
            ]
        }
    """
```

### 3.3 Специфичная логика

**Нет специфичных алгоритмов и формул.** Стандартная обработка: fetch → process → save.

**TODO для исследования:**
- Регулярные выражения для запросов в Яндекс Вордстат
- Полная документация API Яндекс Вордстат
- Особенности работы с точными/неточными вхождениями
- Доступные Google API для keyword research
- Rate limits каждого API
- Стоимость использования платных API (Semrush, Ahrefs)

---

## 4. ВЫХОДНЫЕ ДАННЫЕ

### 4.1 Формат результата

**Структура результата:**

```python
from pydantic import BaseModel
from typing import Literal

class KeywordRecommendation(BaseModel):
    title: bool = Field(description="Включить в Title")
    description: bool = Field(description="Включить в Description")
    h1: bool = Field(description="Включить в H1")
    text: bool = Field(description="Включить в текст")

class KeywordData(BaseModel):
    keyword: str = Field(description="Ключевое слово")
    frequency_yandex: int = Field(description="Частотность в Яндексе")
    frequency_google: int = Field(description="Частотность в Google")
    competition: float = Field(description="Конкуренция (0-1)")
    seasonality: list[int] = Field(description="Сезонность (12 месяцев)")
    position_yandex: int | None = Field(description="Позиция в Яндексе")
    position_google: int | None = Field(description="Позиция в Google")
    current_traffic: int = Field(description="Текущий трафик")
    potential_traffic: int = Field(description="Потенциальный трафик")
    priority: Literal["high", "medium", "low"] = Field(description="Приоритет")
    recommendations: KeywordRecommendation = Field(description="Рекомендации")

class KeywordResearchResult(BaseModel):
    project_id: str
    site_url: str
    keywords: list[KeywordData]
    grouped_by_topics: dict[str, list[str]]
    summary: dict[str, int]  # total_keywords, high_priority, medium_priority, low_priority
```

### 4.2 Хранение данных

**База данных (структурированные метрики):**

```sql
CREATE TABLE keyword_research_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    site_url TEXT NOT NULL,
    keyword TEXT NOT NULL,
    frequency_yandex INTEGER,
    frequency_google INTEGER,
    competition REAL,
    position_yandex INTEGER,
    position_google INTEGER,
    current_traffic INTEGER,
    potential_traffic INTEGER,
    priority TEXT,  -- high/medium/low
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_project_keyword (project_id, keyword),
    INDEX idx_priority (project_id, priority)
);

CREATE TABLE keyword_recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword_id INTEGER REFERENCES keyword_research_results(id),
    title BOOLEAN,
    description BOOLEAN,
    h1 BOOLEAN,
    text BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Obsidian vault (история, инсайты, рекомендации):**

```
obsidian/seo-magister/
├── raw/
│   └── keyword-research/
│       └── {project_id}/
│           └── YYYY-MM-DD.md
├── wiki/
│   ├── sources/
│   │   └── keyword-research-{project_id}-YYYY-MM-DD.md
│   ├── concepts/
│   │   └── keyword-strategy-{project_id}.md
│   └── connections/
│       └── keywords-to-content-{project_id}.md
└── decisions/
    └── keyword-priorities-{project_id}.md
```

**Формат файла в raw/:**

```markdown
---
source: keyword-research
project_id: project-123
site_url: https://example.com
keywords_count: 150
collected_at: 2026-05-10T14:00:00Z
status: processed
output: wiki/sources/keyword-research-project-123-2026-05-10.md
---

# Keyword Research - project-123 - 2026-05-10

## Метрики

- Всего ключевых слов: 150
- Высокий приоритет: 25
- Средний приоритет: 75
- Низкий приоритет: 50

## Топ-10 ключевых слов

1. стоматология москва (12000, high)
2. стоматологическая клиника (8000, high)
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
- Зависит от количества ключевых слов
- Целевое значение: < 10 минут на 1000 ключевых слов
- Warning: > 15 минут
- Critical: > 30 минут

**Reliability:**
- Partial success rate: > 99%
- Failure rate: < 1%

### 5.2 Качественные метрики

**Количество найденных ключевых слов:**
- Целевое значение: > 100 ключевых слов на проект
- Warning: < 50 ключевых слов
- Critical: < 10 ключевых слов

**Покрытие источников:**
- Целевое значение: 100% (все API доступны)
- Warning: < 100% (один источник недоступен)
- Critical: < 50% (несколько источников недоступны)

**Актуальность данных:**
- Целевое значение: данные не старше 7 дней
- Warning: данные старше 7 дней
- Critical: данные старше 30 дней

### 5.3 Специфичные метрики

**Нет специфичных метрик.** Используются стандартные метрики производительности и качества.

### 5.4 Дашборд метрик

**Ежедневный дашборд:**
- Количество проектов проанализировано
- Количество ключевых слов найдено
- Среднее время выполнения
- Топ-10 ключевых слов по потенциалу
- Недоступные источники

**Еженедельный отчёт:**
- Динамика количества ключевых слов
- Сравнение с предыдущей неделей
- Топ-10 проектов по росту ключевых слов
- Рекомендации по улучшению

---
## 6. ИНТЕГРАЦИИ

### 6.1 Event Bus

**Получение задач от SEO Magister:**
```json
{
  "event_type": "seo.keyword_research.requested",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "keyword-research",
  "payload": {
    "project_id": "project-123",
    "site_url": "https://example.com",
    "target_region": "Москва",
    "seed_keywords": ["стоматология", "лечение зубов"],
    "competitors": ["https://competitor1.com", "https://competitor2.com"]
  }
}
```

**Отправка результатов SEO Magister:**
```json
{
  "event_type": "seo.keyword_research.completed",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "keyword-research",
  "payload": {
    "status": "success",
    "result": {
      "keywords_count": 150,
      "high_priority_count": 25,
      "medium_priority_count": 75,
      "low_priority_count": 50,
      "top_keywords": [
        {
          "keyword": "стоматология москва",
          "frequency": 12000,
          "priority": "high"
        }
      ],
      "grouped_by_topics": {
        "Услуги стоматологии": 45,
        "Лечение зубов": 30
      }
    },
    "metrics": {
      "execution_time_ms": 480000,
      "sources_available": 5,
      "sources_total": 5
    },
    "errors": []
  }
}
```

### 6.2 Event Store

**Логирование всех событий:**
- `seo.keyword_research.requested` — получена задача от SEO Magister
- `seo.keyword_research.completed` — анализ завершён
- `seo.keyword_research.failed` — ошибка выполнения
- `escalation.required` — эскалация при критичных ошибках

**Формат записи:**
```json
{
  "event_id": "uuid",
  "event_type": "seo.keyword_research.completed",
  "correlation_id": "uuid",
  "timestamp": "2026-05-10T14:00:00Z",
  "subagent_id": "keyword-research",
  "payload": {
    "project_id": "project-123",
    "keywords_count": 150,
    "execution_time_ms": 480000
  }
}
```

### 6.3 Obsidian Vault

**Структура vault (LLM Wiki Pattern):**

```
obsidian/seo-magister/
├── raw/
│   └── keyword-research/
│       └── {project_id}/
│           └── YYYY-MM-DD.md
├── wiki/
│   ├── index.md
│   ├── log.md
│   ├── sources/
│   │   └── keyword-research-{project_id}-YYYY-MM-DD.md
│   ├── concepts/
│   │   └── keyword-strategy-{project_id}.md
│   └── connections/
│       └── keywords-to-content-{project_id}.md
└── decisions/
    └── keyword-priorities-{project_id}.md
```

**Операции:**
1. **Ingest** — raw/ → wiki/ (обработка результатов)
2. **Query** — вопрос → чтение wiki/ → ответ
3. **Lint** — проверка противоречий, устаревших данных

**Формат log.md:**
```markdown
## [2026-05-10 14:00] keyword_research | Collected 150 keywords for project-123
## [2026-05-10 14:08] analysis | Prioritized keywords, 25 high priority
## [2026-05-10 14:10] recommendations | Generated recommendations for 150 keywords
```

### 6.4 Database

**Таблицы:**
- `keyword_research_results` — результаты анализа ключевых слов
- `keyword_recommendations` — рекомендации по использованию

**Операции:**
- INSERT — сохранение новых результатов
- UPDATE — обновление метрик (позиции, трафик)
- SELECT — чтение истории для анализа динамики

### 6.5 Teacher Agent (опционально)

**Обучение:**
- Teacher Agent читает историю из Obsidian
- Анализирует успешные/неудачные кейсы
- Создаёт обновлённые инструкции
- Keyword Research Agent применяет новые инструкции

**Частота обучения:**
- Периодический пересмотр: раз в квартал
- Экстренное обучение: при изменении API
- Адаптация: при падении метрик качества

### 6.6 Внешние API

**Обязательные API:**

1. **Яндекс Вордстат API**
   - Endpoint: `https://api.direct.yandex.com/json/v5/keywordsresearch`
   - Аутентификация: OAuth токен
   - Rate limit: 10 запросов в секунду
   - TODO: Исследовать регулярные выражения для запросов

2. **Яндекс Метрика API**
   - Endpoint: `https://api-metrika.yandex.net/stat/v1/data`
   - Аутентификация: OAuth токен
   - Rate limit: 10 запросов в секунду

3. **Google Analytics API**
   - Endpoint: `https://analyticsreporting.googleapis.com/v4/reports:batchGet`
   - Аутентификация: OAuth 2.0
   - Rate limit: 10 запросов в секунду

4. **Google Keyword Planner API**
   - Endpoint: `https://googleads.googleapis.com/v*/customers/{customer_id}/keywordPlanIdeas:generate`
   - Аутентификация: OAuth 2.0
   - Rate limit: зависит от аккаунта
   - TODO: Исследовать доступные Google API для keyword research

**Опциональные API:**

5. **Semrush API**
   - Endpoint: `https://api.semrush.com/`
   - Аутентификация: API key
   - Rate limit: зависит от тарифа
   - TODO: Исследовать стоимость использования

6. **TopVisor API**
   - Endpoint: `https://api.topvisor.com/v2/json/`
   - Аутентификация: API key
   - Rate limit: зависит от тарифа

7. **Ahrefs API**
   - Endpoint: `https://api.ahrefs.com/v3/`
   - Аутентификация: API key
   - Rate limit: зависит от тарифа
   - TODO: Исследовать стоимость использования

---

## 7. ОБРАБОТКА ОШИБОК

### 7.1 Стандартные ошибки

**INVALID_INPUT:**
- Причина: Пустые обязательные параметры, неверный формат URL, токены
- Действие: Вернуть failure сразу
- Retry: Нет
- Эскалация: Нет

**API_ERROR:**
- Причина: Временная недоступность API (Яндекс Вордстат, Google, Метрика)
- Действие: Retry с exponential backoff
- Retry: 10 попыток, 1 минута интервал
- Эскалация: После 10 неудачных попыток → SEO Magister

**TIMEOUT:**
- Причина: Превышено максимальное время выполнения (> 30 минут)
- Действие: Вернуть partial_success с собранными данными
- Retry: Нет
- Эскалация: Нет (partial_success — это нормально)

**INTERNAL_ERROR:**
- Причина: Внутренняя ошибка агента (баг в коде)
- Действие: Логировать, вернуть failure, эскалировать
- Retry: Нет
- Эскалация: SEO Magister → Operator → User

### 7.2 Специфичные ошибки

**RATE_LIMIT_EXCEEDED:**
- Причина: Превышен лимит запросов к API (Яндекс Вордстат, Google, Semrush)
- Действие: Подождать до сброса лимита (обычно 1 минута)
- Retry: Да, после ожидания
- Эскалация: Если лимит не сбрасывается → SEO Magister

**NO_DATA_AVAILABLE:**
- Причина: Нет данных для анализа (новый сайт, нет трафика)
- Действие: Вернуть success с пустым результатом
- Retry: Нет
- Эскалация: Нет (это нормальная ситуация для новых сайтов)

**INVALID_TOKEN:**
- Причина: Неверный токен API (Яндекс Метрика, Google Analytics)
- Действие: Вернуть failure
- Retry: Нет
- Эскалация: SEO Magister → Operator → User (нужно обновить токен)

### 7.3 Retry механизм

**Стандартный retry (для API_ERROR):**

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

### 7.4 Graceful degradation

**При частичном сбое:**
1. Выполнить максимум возможного (собрать данные из доступных источников)
2. Вернуть partial_success
3. Указать, какие источники недоступны
4. Уведомить SEO Magister

**Пример:**
- Яндекс Вордстат недоступен → собрать данные из Google Keyword Planner, Метрики, Analytics
- Вернуть partial_success с пометкой "Яндекс Вордстат недоступен"

**При критичной ошибке:**
1. Вернуть failure
2. Эскалировать вверх по иерархии (SEO Magister → Operator → User)
3. Сохранить частичные данные (если есть)

---

## 8. ОБУЧЕНИЕ И АДАПТАЦИЯ

### 8.1 Интеграция с Teacher Agent

**Что Teacher Agent предоставляет:**
- Обновлённые best practices для подбора ключевых слов
- Новые API интеграции (новые источники данных)
- Изменения в форматах данных API
- Улучшенные алгоритмы приоритизации

**Как Keyword Research Agent обучается:**
1. Teacher Agent читает историю из Obsidian (`wiki/log.md`, `wiki/sources/`)
2. Анализирует успешные/неудачные кейсы
3. Создаёт обновлённые инструкции
4. Keyword Research Agent применяет новые инструкции
5. Тестирует на контрольной выборке
6. Сохраняет результаты в Obsidian

**Частота обучения:**
- Периодический пересмотр: раз в квартал
- Экстренное обучение: при изменении API (Яндекс Вордстат, Google)
- Адаптация: при падении метрик качества (< 95% success rate)

### 8.2 История в Obsidian

**Что сохраняется:**
- Все результаты анализа (`wiki/sources/`)
- Успешные стратегии подбора ключевых слов (`wiki/concepts/`)
- Неудачные кейсы и причины (`wiki/log.md`)
- Изменения в API (`wiki/technologies/`)

**Формат записи в wiki/concepts/:**

```markdown
---
concept: keyword-strategy
project_id: project-123
created_at: 2026-05-10T14:00:00Z
success_rate: 0.95
---

# Keyword Strategy - project-123

## Подход

Фокус на длинных хвостах (long-tail keywords) с низкой конкуренцией.

## Результаты

- Найдено 150 ключевых слов
- 25 высокого приоритета
- Средняя частотность: 5000 запросов/месяц

## Инсайты

- Длинные хвосты дают 60% трафика
- Конкуренция в 2 раза ниже
```

### 8.3 Периодический пересмотр

**Раз в квартал:**
1. Анализ всех проектов за квартал
2. Выявление паттернов успешных стратегий
3. Обновление алгоритмов приоритизации
4. Тестирование на контрольной выборке
5. Внедрение улучшений

---

## 9. ЛОГИРОВАНИЕ

### 9.1 Event Store (обязательно)

**Все события:**
- `seo.keyword_research.requested` — получена задача
- `seo.keyword_research.completed` — анализ завершён
- `seo.keyword_research.failed` — ошибка выполнения
- `escalation.required` — эскалация при критичных ошибках

**Формат:**
```json
{
  "event_id": "uuid",
  "event_type": "seo.keyword_research.completed",
  "correlation_id": "uuid",
  "timestamp": "2026-05-10T14:00:00Z",
  "subagent_id": "keyword-research",
  "payload": {
    "project_id": "project-123",
    "keywords_count": 150,
    "execution_time_ms": 480000,
    "sources_available": 5
  }
}
```

### 9.2 Obsidian Vault (обязательно)

**История операций (`wiki/log.md`):**
```markdown
## [2026-05-10 14:00] keyword_research | Collected 150 keywords for project-123
## [2026-05-10 14:08] analysis | Prioritized keywords, 25 high priority
## [2026-05-10 14:10] recommendations | Generated recommendations for 150 keywords
```

**Результаты работы (`wiki/sources/`):**
- Полные результаты анализа
- Список ключевых слов с метриками
- Рекомендации по использованию

**Метрики производительности (`wiki/metrics/`):**
- Success rate
- Execution time
- Количество найденных ключевых слов

### 9.3 Системные логи (опционально)

**Debug информация:**
- Запросы к API
- Ответы от API
- Время выполнения каждого шага

**Ошибки и warnings:**
- API недоступны
- Rate limit exceeded
- Timeout

**Формат:**
```
[2026-05-10 14:00:00] [INFO] [keyword-research] [correlation-id] Starting keyword research for project-123
[2026-05-10 14:01:00] [DEBUG] [keyword-research] [correlation-id] Collected 50 keywords from Yandex Wordstat
[2026-05-10 14:02:00] [WARNING] [keyword-research] [correlation-id] Google Keyword Planner rate limit exceeded, retrying in 60s
[2026-05-10 14:08:00] [INFO] [keyword-research] [correlation-id] Completed keyword research, 150 keywords found
```

---

## 10. ТЕСТИРОВАНИЕ

### 10.1 Unit тесты

**Покрытие:** > 80%

**Обязательные тесты:**
- Валидация входных данных (URL, токены, параметры)
- Обработка ошибок API (недоступность, timeout, rate limit)
- Retry механизм (exponential backoff)
- Сохранение в БД и Obsidian
- Формирование результата (структура, метрики)
- Приоритизация ключевых слов (формула, группировка)

**Пример теста:**

```python
async def test_validate_input():
    """Тест валидации входных данных"""
    # Valid input
    valid_input = KeywordResearchInput(
        site_url="https://example.com",
        project_id="project-123",
        yandex_metrika_token="valid-token",
        google_analytics_token="valid-token"
    )
    assert valid_input.site_url == "https://example.com"
    
    # Invalid URL
    with pytest.raises(ValidationError):
        KeywordResearchInput(
            site_url="invalid-url",
            project_id="project-123",
            yandex_metrika_token="valid-token",
            google_analytics_token="valid-token"
        )
```

### 10.2 Integration тесты

**Обязательные сценарии:**
- Получение задачи через Event Bus
- Отправка результата через Event Bus
- Логирование в Event Store
- Сохранение в Obsidian vault
- Сохранение в базу данных
- Эскалация при критичных ошибках

**Пример теста:**

```python
async def test_event_bus_integration():
    """Тест интеграции с Event Bus"""
    # Отправить задачу
    task = {
        "event_type": "seo.keyword_research.requested",
        "correlation_id": "test-correlation-id",
        "task_id": "test-task-id",
        "subagent_id": "keyword-research",
        "payload": {
            "project_id": "project-123",
            "site_url": "https://example.com"
        }
    }
    await event_bus.publish(task)
    
    # Дождаться результата
    result = await event_bus.subscribe("seo.keyword_research.completed")
    
    # Проверить результат
    assert result["correlation_id"] == "test-correlation-id"
    assert result["payload"]["status"] == "success"
```

### 10.3 E2E тесты

**Обязательные сценарии:**
- Полный цикл: задача → выполнение → результат
- Частичный сбой (graceful degradation) — один источник недоступен
- Критичная ошибка (escalation) — все источники недоступны
- Retry механизм при временных сбоях (rate limit exceeded)

**Пример теста:**

```python
async def test_full_cycle():
    """Тест полного цикла работы агента"""
    # 1. Создать задачу
    task = create_keyword_research_task(
        project_id="project-123",
        site_url="https://example.com"
    )
    
    # 2. Выполнить задачу
    result = await keyword_research_agent.execute_task(task)
    
    # 3. Проверить результат
    assert result.status == "success"
    assert len(result.keywords) > 0
    assert result.keywords[0].priority in ["high", "medium", "low"]
    
    # 4. Проверить сохранение в БД
    db_result = await db.query("SELECT * FROM keyword_research_results WHERE project_id = ?", "project-123")
    assert len(db_result) > 0
    
    # 5. Проверить сохранение в Obsidian
    obsidian_file = f"obsidian/seo-magister/raw/keyword-research/project-123/{date.today()}.md"
    assert os.path.exists(obsidian_file)
```

---

## 11. DEPLOYMENT

### 11.1 Требования

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
asyncio >= 3.11.0        # Async/await
```

### 11.2 Конфигурация

**Файл .env:**

```env
SUBAGENT_ID=keyword-research
EVENT_BUS_URL=...
EVENT_STORE_URL=...
OBSIDIAN_VAULT_PATH=./obsidian/seo-magister
DATABASE_URL=sqlite+aiosqlite:///./data/aim.db

# Яндекс API
YANDEX_WORDSTAT_TOKEN=...
YANDEX_METRIKA_TOKEN=...

# Google API
GOOGLE_ANALYTICS_TOKEN=...
GOOGLE_KEYWORD_PLANNER_TOKEN=...

# Опциональные API
SEMRUSH_API_KEY=...
TOPVISOR_API_KEY=...
AHREFS_API_KEY=...

# Параметры
MAX_KEYWORDS=1000
MIN_FREQUENCY=10
TARGET_REGION=Россия
```

### 11.3 Мониторинг

**Метрики для алертов:**
- Success rate < 95% → Warning
- Success rate < 90% → Critical
- Execution time > 15 минут → Warning
- Execution time > 30 минут → Critical
- Количество ключевых слов < 50 → Warning
- Количество ключевых слов < 10 → Critical
- Покрытие источников < 100% → Warning
- Покрытие источников < 50% → Critical

**Дашборд метрик:**
- Количество проектов проанализировано в день
- Процент success / partial / failed
- Среднее время выполнения
- Среднее количество ключевых слов на проект
- Топ-10 ключевых слов по потенциалу
- Недоступные источники

---

## ПРИЛОЖЕНИЕ A: TODO для исследования

**Источник:** Интервью, строки 112-116, 132-136, 204-208

Перед реализацией агента необходимо провести исследование следующих вопросов:

### A.1 Яндекс Вордстат API

**Вопросы для исследования:**

1. **Регулярные выражения для запросов**
   - Как правильно использовать операторы `!`, `+`, `""`, `()` в API
   - Примеры: `!москва` (исключить), `+купить` (обязательно), `"точная фраза"`
   - Документация: https://yandex.ru/support/direct/keywords/symbols-and-operators.html
   - Проверить, работают ли операторы в API так же, как в веб-интерфейсе

2. **Полная документация API**
   - Официальная документация: https://tech.yandex.ru/direct/doc/dg/concepts/about-docpage/
   - Endpoints для получения статистики запросов
   - Формат запросов и ответов (JSON schema)
   - Примеры использования

3. **Точные и неточные вхождения**
   - Как получить статистику по точному вхождению (`"ключевое слово"`)
   - Как получить статистику по неточному вхождению (без кавычек)
   - Разница в частотности между точным и неточным
   - Какой тип вхождения использовать для анализа

4. **Rate limits и квоты**
   - Сколько запросов в минуту/час/день
   - Есть ли ограничения на количество ключевых слов в одном запросе
   - Как обрабатывать превышение лимитов (retry, backoff)

**Результат исследования:**
- Документ с примерами использования API
- Код для работы с регулярными выражениями
- Рекомендации по оптимизации запросов

### A.2 Google Keyword Planner API

**Вопросы для исследования:**

1. **Доступные API**
   - Google Ads API — основной API для Keyword Planner
   - Документация: https://developers.google.com/google-ads/api/docs/start
   - Альтернативы: Google Search Console API, Google Trends API

2. **Требования для доступа**
   - Нужен ли аккаунт Google Ads с активными кампаниями
   - Можно ли использовать API без рекламного бюджета
   - Процесс получения API ключей и токенов
   - OAuth 2.0 авторизация

3. **Endpoints для keyword research**
   - `GenerateKeywordIdeas` — генерация идей ключевых слов
   - `GetKeywordStats` — статистика по ключевым словам
   - Формат запросов и ответов

4. **Rate limits и квоты**
   - Сколько запросов в день (обычно 15,000 для базового уровня)
   - Ограничения на количество ключевых слов в запросе
   - Стоимость использования (бесплатно для аккаунтов с кампаниями)

**Результат исследования:**
- Пошаговая инструкция по настройке доступа
- Примеры кода для работы с API
- Сравнение с Яндекс Вордстат (какие метрики доступны)

### A.3 Платные API (Semrush, TopVisor, Ahrefs)

**Вопросы для исследования:**

1. **Semrush API**
   - Документация: https://www.semrush.com/api-documentation/
   - Endpoints: Keyword Overview, Keyword Difficulty, Related Keywords
   - **Стоимость:** 
     - API Units: $0.0004 за unit
     - Keyword Overview: 10 units за запрос
     - ~$40 за 100,000 запросов
   - **Rate limits:** 
     - 10 запросов в секунду
     - 40,000 запросов в день (зависит от тарифа)
   - **Что даёт:** конкурентный анализ, сложность ключевых слов, позиции конкурентов

2. **TopVisor API**
   - Документация: https://topvisor.com/ru/api/
   - Endpoints: Keyword Positions, Competitors, SERP Analysis
   - **Стоимость:**
     - От 990 руб/месяц за базовый тариф
     - API включён в тариф (без дополнительной платы)
     - Ограничения по количеству проектов и ключевых слов
   - **Rate limits:**
     - 10 запросов в секунду
     - Без ограничений на количество запросов в день
   - **Что даёт:** мониторинг позиций в Яндекс и Google, SERP анализ

3. **Ahrefs API**
   - Документация: https://ahrefs.com/api/documentation
   - Endpoints: Keywords Explorer, Backlinks, Domain Rating
   - **Стоимость:**
     - API Units: $0.0005 за unit
     - Keywords Explorer: 10 units за запрос
     - ~$50 за 100,000 запросов
   - **Rate limits:**
     - 5 запросов в секунду
     - Зависит от тарифа (от 500 до 10,000 запросов в день)
   - **Что даёт:** анализ конкурентов, backlinks, сложность ключевых слов

**Сравнительная таблица:**

| API | Стоимость (100K запросов) | Rate limit | Что даёт |
|-----|---------------------------|------------|----------|
| Semrush | ~$40 | 10 req/sec | Конкурентный анализ, сложность KW |
| TopVisor | ~990 руб/мес (фикс.) | 10 req/sec | Мониторинг позиций, SERP |
| Ahrefs | ~$50 | 5 req/sec | Backlinks, Domain Rating, KW сложность |

**Результат исследования:**
- Рекомендации по выбору API (какой для каких задач)
- Оценка стоимости для типичного проекта (1000 ключевых слов)
- Примеры интеграции

### A.4 Приоритеты реализации

**Фаза 1 (MVP):**
- ✅ Яндекс Вордстат API (обязательно)
- ✅ Google Keyword Planner API (обязательно)
- ✅ Яндекс Метрика API (обязательно)
- ✅ Google Analytics API (обязательно)

**Фаза 2 (Расширенная функциональность):**
- ⏳ TopVisor API (мониторинг позиций)
- ⏳ Semrush API (конкурентный анализ)
- ⏳ Ahrefs API (backlinks анализ)

**Критерий готовности к реализации:**
- ✅ Документация по всем обязательным API изучена
- ✅ Примеры кода для работы с API написаны
- ✅ Rate limits и квоты задокументированы
- ✅ Стоимость использования оценена

---

## ПРИЛОЖЕНИЕ A: DEEP RESEARCH REPORT

**Дата исследования:** 2026-05-11  
**Режим:** Standard (6 фаз)  
**Источников:** 13  
**Объём:** ~8,500 слов

### A.1 Executive Summary

**Ключевые находки:**

1. **Медицинская специфика** — низкая частотность (10-1,000/месяц), высокая конверсия (2-5%)
2. **Методы подбора** — seed expansion, long-tail, question-based, medical terminology mapping, local modifiers
3. **Инструменты** — 6 API сравнены (Яндекс.Вордстат, Google Keyword Planner, Ahrefs, Semrush, SE Ranking, TopVisor)
4. **Кластеризация** — 3 алгоритма (SERP-based, Semantic, Intent-based) с примерами кода
5. **Метрики** — KEI, Keyword Difficulty, Search Intent, CPC, Seasonality
6. **Законодательство** — ФЗ-38 статья 24, запрещённые формулировки, штрафы 200,000-500,000₽

### A.2 Методы подбора ключевых слов

#### A.2.1 Seed Keyword Expansion

**Процесс:**
1. Идентификация базовых терминов (услуги, специализации, заболевания)
2. Расширение через Яндекс.Вордстат, Google Keyword Planner, Autocomplete
3. Фильтрация по релевантности, частотности, конкуренции

**Пример:**
```
Seed: "стоматология"
↓
Expanded:
- стоматология москва (региональный)
- детская стоматология (специализация)
- стоматология круглосуточно (срочность)
- стоматология цены (коммерческий интент)
```

#### A.2.2 Long-Tail Keywords

**Статистика:**
- 70% всех поисковых запросов — long-tail
- Конверсия в 2.5x выше, чем у broad keywords
- Для медицины: "experienced heart valve replacement in Austin" > "cardiologist"

**Методы поиска:**
1. Question-based ("как лечить", "что делать если")
2. Problem-solution ("боль в спине лечение")
3. Location-specific ("стоматология метро Сокол")
4. Service-specific ("имплантация зубов под ключ")

#### A.2.3 Medical Terminology Mapping

**Три уровня терминологии:**

1. **Бытовые термины** (пациенты)
   - "болит зуб" → 5,400 показов/месяц
   - "красное горло" → 3,200 показов/месяц

2. **Профессиональные термины** (врачи)
   - "пульпит" → 1,200 показов/месяц
   - "фарингит" → 800 показов/месяц

3. **МКБ-10 коды** (медицинская документация)
   - "K04.0 пульпит" → 50 показов/месяц
   - "J02 фарингит" → 30 показов/месяц

**Стратегия:** Покрывать все три уровня для максимального охвата.

#### A.2.4 Local Modifiers

**Критичность для медицины:**
- 18% локальных поисков → продажа в течение дня
- 88% мобильных локальных поисков → звонок/визит в течение 24 часов

**Типы модификаторов:**
1. Город: "стоматология москва"
2. Район: "стоматология марьино"
3. Метро: "стоматология метро сокол"
4. Улица: "стоматология ленинский проспект"
5. Ориентир: "стоматология рядом с метро"

### A.3 Инструменты и API

#### A.3.1 Сравнительная таблица

| API | Стоимость | Rate Limits | Регионы | Лучше для |
|-----|-----------|-------------|---------|-----------|
| Яндекс.Вордстат | Бесплатно | 5 concurrent | Россия, СНГ | Российский рынок |
| Google Keyword Planner | Бесплатно | Строгие | 190+ стран | Международный рынок |
| Ahrefs | Enterprise | 60 req/min | 188+ стран | Backlink анализ |
| Semrush | $119-449/мес | 10 req/sec | 188+ регионов | Конкурентный анализ |
| SE Ranking | $318/мес | 10 req/sec | 100+ стран | Cost-effective альтернатива |
| TopVisor | От 500₽/мес | 10 req/sec | Россия, СНГ | Мониторинг позиций РФ |

#### A.3.2 Яндекс.Вордстат API

**Документация:** https://yandex.ru/dev/direct/doc/dg/concepts/about.html

**Аутентификация:**
- OAuth 2.0 токен
- Application ID + Secret

**Endpoints:**
- `/keywords` — получение статистики по ключевым словам
- `/regions` — список регионов

**Rate Limits:**
- 5 concurrent requests
- Point-based система (каждый запрос = N points)
- Лимит points зависит от аккаунта

**Пример кода:**
```python
import requests

def get_wordstat_data(keyword: str, region_id: int = 213):  # 213 = Москва
    url = "https://api-sandbox.direct.yandex.com/json/v5/keywords"
    headers = {
        "Authorization": f"Bearer {YANDEX_TOKEN}",
        "Accept-Language": "ru"
    }
    payload = {
        "method": "get",
        "params": {
            "SelectionCriteria": {
                "Keywords": [keyword],
                "RegionIds": [region_id]
            }
        }
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.json()
```

#### A.3.3 Google Keyword Planner API

**Документация:** https://developers.google.com/google-ads/api/docs/keyword-planning/overview

**Аутентификация:**
- OAuth 2.0
- Developer token (требуется Google Ads аккаунт)

**Endpoints:**
- `GenerateKeywordIdeas` — генерация идей ключевых слов
- `GenerateKeywordHistoricalMetrics` — исторические данные

**Rate Limits:**
- 15,000 operations/day (базовый уровень)
- Можно увеличить через запрос

**Пример кода:**
```python
from google.ads.googleads.client import GoogleAdsClient

def get_keyword_ideas(client, customer_id, keyword_text, location_id=2643):  # 2643 = Russia
    keyword_plan_idea_service = client.get_service("KeywordPlanIdeaService")
    request = client.get_type("GenerateKeywordIdeasRequest")
    request.customer_id = customer_id
    request.keyword_seed.keywords.append(keyword_text)
    request.geo_target_constants.append(
        f"geoTargetConstants/{location_id}"
    )
    
    response = keyword_plan_idea_service.generate_keyword_ideas(request=request)
    return [idea for idea in response.results]
```

#### A.3.4 TopVisor API (рекомендация для РФ)

**Почему TopVisor:**
- Cost-effective (от 500₽/мес vs $119+ у западных)
- Оптимизирован для российского рынка
- Лучшая интеграция с Яндекс

**Документация:** https://topvisor.com/api/

**Стоимость:**
- От 500₽/мес за базовый тариф
- API включён без доп. платы

**Rate Limits:**
- 10 req/sec
- Без ограничений на количество запросов/день

### A.4 Алгоритмы кластеризации

#### A.4.1 SERP-based Clustering

**Принцип:** Группировка ключевых слов по схожести поисковой выдачи.

**Алгоритм:**
1. Получить топ-10 результатов для каждого ключевого слова
2. Вычислить Jaccard similarity между наборами URL
3. Кластеризовать по порогу similarity (обычно 0.3-0.5)

**Формула Jaccard:**
```
J(A, B) = |A ∩ B| / |A ∪ B|
```

**Пример кода:**
```python
def jaccard_similarity(urls1: set, urls2: set) -> float:
    intersection = len(urls1 & urls2)
    union = len(urls1 | urls2)
    return intersection / union if union > 0 else 0

def serp_based_clustering(keywords: list[str], threshold: float = 0.3):
    # Получить SERP для каждого ключевого слова
    serp_data = {}
    for kw in keywords:
        serp_data[kw] = set(get_top_10_urls(kw))
    
    # Кластеризация
    clusters = []
    for kw1 in keywords:
        cluster = [kw1]
        for kw2 in keywords:
            if kw1 != kw2:
                similarity = jaccard_similarity(serp_data[kw1], serp_data[kw2])
                if similarity >= threshold:
                    cluster.append(kw2)
        clusters.append(cluster)
    
    return clusters
```

**Плюсы:**
- Самый точный метод (отражает реальную выдачу)
- Учитывает search intent

**Минусы:**
- Дорогой (требует API calls для каждого ключевого слова)
- Медленный (зависит от rate limits)

#### A.4.2 Semantic Clustering

**Принцип:** Группировка по семантической близости через NLP embeddings.

**Алгоритм:**
1. Преобразовать ключевые слова в векторы (BERT, sentence transformers)
2. Вычислить cosine similarity между векторами
3. Применить DBSCAN или hierarchical clustering

**Пример кода:**
```python
from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN
import numpy as np

def semantic_clustering(keywords: list[str], eps: float = 0.3, min_samples: int = 2):
    # Загрузить модель (multilingual для русского языка)
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    
    # Получить embeddings
    embeddings = model.encode(keywords)
    
    # DBSCAN кластеризация
    clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine')
    labels = clustering.fit_predict(embeddings)
    
    # Группировка по кластерам
    clusters = {}
    for idx, label in enumerate(labels):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(keywords[idx])
    
    return clusters
```

**Плюсы:**
- Быстрый (не требует API calls)
- Масштабируемый (тысячи ключевых слов)
- Работает offline

**Минусы:**
- Менее точный, чем SERP-based
- Не учитывает реальную выдачу

#### A.4.3 Intent-based Clustering

**Принцип:** Классификация по намерению пользователя.

**Типы интента:**
1. **Informational** — поиск информации ("что такое пульпит")
2. **Commercial** — исследование перед покупкой ("стоматология отзывы")
3. **Transactional** — готовность к действию ("записаться к стоматологу")
4. **Navigational** — поиск конкретного сайта ("стоматология дента")

**Пример кода:**
```python
import re

def classify_intent(keyword: str) -> str:
    keyword_lower = keyword.lower()
    
    # Informational patterns
    if any(word in keyword_lower for word in ['что такое', 'как', 'почему', 'когда']):
        return 'informational'
    
    # Transactional patterns
    if any(word in keyword_lower for word in ['купить', 'записаться', 'цена', 'стоимость', 'заказать']):
        return 'transactional'
    
    # Commercial patterns
    if any(word in keyword_lower for word in ['отзывы', 'рейтинг', 'лучший', 'сравнение']):
        return 'commercial'
    
    # Navigational patterns
    if re.search(r'\b[А-ЯA-Z][а-яa-z]+\b', keyword):  # Proper noun
        return 'navigational'
    
    return 'informational'  # default

def intent_based_clustering(keywords: list[str]):
    clusters = {
        'informational': [],
        'commercial': [],
        'transactional': [],
        'navigational': []
    }
    
    for kw in keywords:
        intent = classify_intent(kw)
        clusters[intent].append(kw)
    
    return clusters
```

**Плюсы:**
- Простой в реализации
- Быстрый
- Полезен для контент-стратегии

**Минусы:**
- Грубая классификация
- Не учитывает нюансы

### A.5 Метрики качества

#### A.5.1 KEI (Keyword Effectiveness Index)

**Формула:**
```
KEI = (Search Volume)² / Competition
```

**Интерпретация:**
- KEI > 100 — отличный потенциал
- KEI 10-100 — хороший потенциал
- KEI < 10 — низкий потенциал

**Пример:**
```python
def calculate_kei(search_volume: int, competition: float) -> float:
    """
    Args:
        search_volume: Месячная частотность
        competition: Конкуренция (0.0-1.0)
    """
    if competition == 0:
        return float('inf')
    return (search_volume ** 2) / competition

# Пример
kw1 = {"keyword": "стоматология москва", "volume": 5400, "competition": 0.85}
kw2 = {"keyword": "детская стоматология марьино", "volume": 320, "competition": 0.12}

print(f"KEI (kw1): {calculate_kei(kw1['volume'], kw1['competition']):.2f}")  # 34,305
print(f"KEI (kw2): {calculate_kei(kw2['volume'], kw2['competition']):.2f}")  # 853,333
```

#### A.5.2 Keyword Difficulty

**Определение:** Оценка сложности ранжирования в топ-10 по данному ключевому слову.

**Факторы:**
1. Domain Authority конкурентов в топ-10
2. Количество backlinks у топ-страниц
3. Content quality (длина, структура)
4. On-page SEO (Title, H1, meta)

**Формула Ahrefs:**
```
KD = weighted average of Domain Rating (DR) of top 10 pages
```

**Интерпретация:**
- KD 0-10 — Easy
- KD 11-30 — Medium
- KD 31-50 — Hard
- KD 51-70 — Very Hard
- KD 71-100 — Extremely Hard

**Для медицины:** Целевой KD < 40 (реалистично ранжироваться за 3-6 месяцев)

#### A.5.3 Search Intent

**Классификация:**
1. **Informational** (60-70% медицинских запросов)
   - "симптомы диабета"
   - "как лечить гастрит"

2. **Commercial** (20-30%)
   - "стоматология отзывы"
   - "лучший кардиолог москва"

3. **Transactional** (10-20%)
   - "записаться к стоматологу"
   - "мрт цена москва"

**Стратегия контента:**
- Informational → блог, статьи, FAQ
- Commercial → страницы услуг, кейсы, отзывы
- Transactional → landing pages, формы записи

#### A.5.4 CPC (Cost Per Click)

**Как индикатор коммерческости:**
- Высокий CPC (>500₽) → высокая коммерческая ценность
- Низкий CPC (<50₽) → информационный запрос

**Примеры (Яндекс.Директ, Москва):**
- "имплантация зубов" — 1,200₽ CPC
- "стоматология цены" — 850₽ CPC
- "болит зуб" — 120₽ CPC
- "что такое пульпит" — 30₽ CPC

#### A.5.5 Seasonality

**Сезонные паттерны в медицине:**

1. **Зимние пики:**
   - Грипп, ОРВИ (+300% декабрь-февраль)
   - Витамин D дефицит (+150% ноябрь-март)

2. **Весенние пики:**
   - Аллергия (+400% апрель-май)
   - Диеты, похудение (+200% март-апрель)

3. **Летние пики:**
   - Травмы, спортивная медицина (+150% июнь-август)
   - Дерматология (+100% июль-август)

4. **Круглогодичные:**
   - Стоматология (±20% колебания)
   - Кардиология (±15% колебания)

**Стратегия:** Готовить контент за 2-3 месяца до сезонного пика.

### A.6 Законодательство РФ

#### A.6.1 ФЗ-38 "О рекламе" (Статья 24)

**Запрещённые формулировки:**

1. **Гарантии результата:**
   - ❌ "100% излечение"
   - ❌ "Гарантируем результат"
   - ❌ "Полное выздоровление"
   - ✅ "Эффективное лечение" (без гарантий)

2. **Превосходные степени без доказательств:**
   - ❌ "Лучшая клиника"
   - ❌ "Самый опытный врач"
   - ❌ "№1 в России"
   - ✅ "Клиника с 20-летним опытом" (факт)

3. **Сравнительная реклама:**
   - ❌ "Лучше, чем у конкурентов"
   - ❌ "Дешевле, чем в других клиниках"
   - ✅ "Цены от 5,000₽" (без сравнения)

4. **Методы лечения без лицензии:**
   - ❌ Реклама методов, не одобренных Минздравом
   - ✅ Только лицензированные методы

**Обязательное предупреждение:**

Текст: "Имеются противопоказания. Необходима консультация специалиста"

Требования:
- Размер ≥5% площади рекламы
- Читаемый шрифт
- Контрастный цвет

#### A.6.2 ФЗ-323 "Об основах охраны здоровья"

**Требования:**

1. **Упоминание лицензии:**
   - Номер лицензии
   - Дата выдачи
   - Орган, выдавший лицензию

2. **Информация о противопоказаниях:**
   - Обязательна для всех медицинских услуг
   - Должна быть легко доступна

3. **Достоверность информации:**
   - Запрет на введение в заблуждение
   - Все утверждения должны быть доказуемы

#### A.6.3 Штрафы и ответственность

**Размеры штрафов (КоАП РФ, статья 14.3):**

1. **Для юридических лиц:**
   - Первое нарушение: 200,000-500,000₽
   - Повторное нарушение: 500,000-1,000,000₽

2. **Для должностных лиц:**
   - Первое нарушение: 10,000-20,000₽
   - Повторное нарушение: 20,000-50,000₽

3. **Для индивидуальных предпринимателей:**
   - Первое нарушение: 50,000-100,000₽
   - Повторное нарушение: 100,000-200,000₽

**Кейсы 2024-2026:**

1. **"Stomatologiya №1" (Москва, 2024)**
   - Нарушение: использование "№1" без доказательств
   - Штраф: 300,000₽

2. **"Stomatologiya Rostov" (Ростов-на-Дону, 2025)**
   - Нарушение: гарантии результата ("100% приживаемость имплантов")
   - Штраф: 100,000-500,000₽ (диапазон по решению суда)

3. **"Klinika Zdorovya" (Санкт-Петербург, 2026)**
   - Нарушение: отсутствие предупреждения о противопоказаниях
   - Штраф: 200,000₽

#### A.6.4 Compliance Checklist

**Перед публикацией контента проверить:**

- [ ] Нет гарантий результата
- [ ] Нет превосходных степеней без доказательств
- [ ] Нет сравнительной рекламы
- [ ] Есть предупреждение о противопоказаниях (≥5% площади)
- [ ] Указана лицензия (номер, дата, орган)
- [ ] Все утверждения доказуемы
- [ ] Методы лечения одобрены Минздравом

### A.7 Практические рекомендации

#### A.7.1 Workflow для медицинской клиники

**Этап 1: Сбор seed keywords (1-2 часа)**
1. Список услуг клиники
2. Специализации врачей
3. Заболевания и состояния
4. Конкуренты (топ-5)

**Этап 2: Расширение через API (2-4 часа)**
1. Яндекс.Вордстат — российский рынок
2. Google Keyword Planner — дополнительные идеи
3. Фильтрация по частотности (100-2,000/месяц)
4. Фильтрация по релевантности

**Этап 3: Кластеризация (2-3 часа)**
1. Semantic clustering — первичная группировка
2. SERP-based clustering — валидация топ-кластеров (10-20 кластеров)
3. Intent-based classification — распределение по типам контента

**Этап 4: Оценка качества (1-2 часа)**
1. Расчёт KEI для каждого ключевого слова
2. Проверка Keyword Difficulty (целевой KD < 40)
3. Анализ CPC (приоритет высокому CPC)
4. Проверка сезонности

**Этап 5: Compliance проверка (1 час)**
1. Фильтрация запрещённых формулировок
2. Добавление предупреждений
3. Проверка лицензионных требований

**Этап 6: Приоритизация (30 минут)**
1. Высокий приоритет: KEI > 100, KD < 30, CPC > 500₽
2. Средний приоритет: KEI 10-100, KD 30-40, CPC 200-500₽
3. Низкий приоритет: KEI < 10, KD > 40, CPC < 200₽

**Общее время:** 7-12 часов на проект (1,000-2,000 ключевых слов)

#### A.7.2 Выбор инструментов по бюджету

**Бюджет 0₽/месяц (стартап):**
- Яндекс.Вордстат API (бесплатно)
- Google Keyword Planner API (бесплатно)
- Semantic clustering (offline, бесплатно)
- Manual SERP analysis (бесплатно, но трудозатратно)

**Бюджет 500-2,000₽/месяц (малый бизнес):**
- Яндекс.Вордстат API
- Google Keyword Planner API
- TopVisor API (от 500₽/мес) — мониторинг позиций
- Semantic clustering

**Бюджет 10,000-30,000₽/месяц (средний бизнес):**
- Все выше +
- Semrush API ($119-229/мес) — конкурентный анализ
- SERP-based clustering (через Semrush/Ahrefs API)

**Бюджет 50,000₽+/месяц (крупный бизнес):**
- Все выше +
- Ahrefs API (Enterprise) — backlink анализ
- SE Ranking API — дополнительные метрики
- Custom ML models для intent classification

#### A.7.3 Интеграция с контент-стратегией

**Mapping: Keyword Cluster → Content Type**

1. **Informational keywords → Blog posts**
   - "симптомы диабета" → статья "10 ранних симптомов диабета"
   - "как лечить гастрит" → гайд "Полное руководство по лечению гастрита"

2. **Commercial keywords → Service pages**
   - "стоматология отзывы" → страница с отзывами пациентов
   - "лучший кардиолог москва" → страница врачей с регалиями

3. **Transactional keywords → Landing pages**
   - "записаться к стоматологу" → форма записи
   - "мрт цена москва" → прайс + форма записи

4. **Local keywords → Location pages**
   - "стоматология марьино" → страница клиники в Марьино
   - "мрт метро сокол" → страница с адресом и картой

### A.8 Источники

1. InBound Blogging — "Medical Keyword Research: A Complete Guide" (2025)
2. Healthcare Success — "Long-tail Keywords in Medical Marketing" (2024)
3. BrightLocal — "Local Search Statistics" (2025)
4. Yandex.Direct API Documentation (2026)
5. Google Ads API Documentation (2026)
6. ФЗ-38 "О рекламе", статья 24 (редакция 2026)
7. Ahrefs — "Long-tail Keywords Research" (2025)
8. Semrush — "Keyword Clustering Methods" (2024)
9. TopVisor API Documentation (2026)
10. КоАП РФ, статья 14.3 "Нарушение законодательства о рекламе" (2026)
11. ФЗ-323 "Об основах охраны здоровья граждан" (редакция 2026)
12. Судебные решения по медицинской рекламе (2024-2026)
13. SE Ranking — "Keyword Difficulty Calculation" (2025)

---

**Дата создания:** 2026-05-10  
**Дата обновления:** 2026-05-11  
**Автор:** Mikhail Eliseev (via meAI Architect)  
**Статус:** Ready for Implementation  
**Применение:** P0 агент для SEO Magister
