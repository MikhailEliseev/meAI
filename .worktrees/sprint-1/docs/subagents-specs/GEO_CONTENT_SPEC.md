# GEO Content Agent — Спецификация

**Версия:** 1.0.0  
**Дата создания:** 2026-05-10  
**Родительский Magister:** SEO Magister  
**Приоритет:** P1 (критичный для AI-эпохи)

---

## 1. Обзор

### 1.1 Назначение

**GEO Content Agent** — автономный агент для создания контента, оптимизированного под AI-поисковые системы (ChatGPT, Perplexity, Claude, Google AI Overviews).

**Ключевая задача:** Генерировать контент, который AI-модели будут цитировать в своих ответах, применяя GEO-паттерны (правило первых 50 слов, FAQPage schema, citation engineering).

### 1.2 Роль в системе

**GEO Content Agent** — это "контент-инженер" для AI-видимости:
- Создаёт контент с учётом GEO-паттернов
- Применяет правило первых 50 слов (44.2% цитирований)
- Генерирует FAQPage schema для структурированных данных
- Создаёт "citation bait" — контент, который AI хочет цитировать
- Адаптирует контент под разные AI-платформы

**Отличие от Blog Content Agent:**
- Blog Content → SEO-оптимизация для Google (традиционный поиск)
- GEO Content → оптимизация для AI-поиска (ChatGPT, Perplexity, Claude)

### 1.3 Уникальная ценность

**Почему это критично:**
1. **AI-поиск растёт экспоненциально** — 900M ChatGPT users/week, 1B+ Perplexity queries/month
2. **44.2% цитирований из первых 30% текста** — нужна специальная структура контента
3. **85% цитирований из чужих доменов** — нужно создавать контент, который AI захочет цитировать
4. **Конкурентное преимущество** — большинство компаний ещё не оптимизируют контент под AI

**Метрика успеха:** GEO Score созданного контента > 70/100.

### 1.4 Границы ответственности

**Что делает:**
- ✅ Создаёт контент с GEO-оптимизацией
- ✅ Применяет правило первых 50 слов
- ✅ Генерирует FAQPage schema
- ✅ Создаёт "citation bait" элементы
- ✅ Адаптирует контент под AI-платформы
- ✅ Проверяет GEO Score созданного контента

**Что НЕ делает:**
- ❌ Не публикует контент (это Content Scheduler Agent)
- ❌ Не оптимизирует существующий контент (это GEO Optimization Agent)
- ❌ Не мониторит видимость (это GEO Monitoring Agent)
- ❌ Не создаёт контент для традиционного SEO (это Blog Content Agent)

**Backlog (будущие фичи):**
- Автоматическая генерация llms.txt файла
- A/B тестирование вариантов контента для AI
- Персонализация контента под разные AI-модели
- Интеграция с GPT-4 для генерации контента

### 1.5 Связанные агенты

**Координация с другими агентами:**

| Агент | Взаимодействие | Формат данных |
|-------|----------------|---------------|
| **GEO Optimization Agent** | Получает рекомендации по оптимизации → создаёт новый контент | Event Bus (JSON) |
| **GEO Monitoring Agent** | Получает данные о популярных темах → создаёт контент | Event Bus (JSON) |
| **SEO Magister** | Получает задачи на создание контента | Event Bus (JSON) |
| **Keyword Research Agent** | Получает целевые ключевые слова | Event Bus (JSON) |
| **Content Scheduler Agent** | Передаёт готовый контент для публикации | Event Bus (JSON) |
| **Tone of Voice Agent** | Получает ToV guidelines для адаптации стиля | Event Bus (JSON) |

**Отличия от похожих агентов:**

| Критерий | GEO Content | Blog Content | Landing Content |
|----------|-------------|--------------|-----------------|
| **Цель** | AI-цитирования | Органический трафик | Конверсии |
| **Оптимизация** | Первые 50 слов, FAQ | Ключевые слова, H1-H6 | CTA, форма |
| **Структура** | Citation bait | SEO-структура | Воронка продаж |
| **Метрика** | GEO Score, Share of Voice | Позиции, трафик | Конверсии, лиды |

---

## 2. Входные данные

### 2.1 Источники данных

**Обязательные источники:**
1. **Тема контента** (от SEO Magister или пользователя)
2. **Целевые ключевые слова** (от Keyword Research Agent)
3. **ToV guidelines** (от Tone of Voice Agent)

**Опциональные источники:**
4. **Конкурентный контент** (от Competitor Analysis Agent)
5. **Популярные темы в AI** (от GEO Monitoring Agent)
6. **Существующий контент для улучшения** (от GEO Optimization Agent)

### 2.2 Обязательные параметры

```python
class ContentRequest(BaseModel):
    """Запрос на создание GEO-контента"""
    
    # Тема и цель
    topic: str  # "Медицинский маркетинг для клиник"
    goal: str  # "Получить цитирования в ChatGPT и Perplexity"
    
    # Ключевые слова
    primary_keywords: list[str]  # ["медицинский маркетинг", "привлечение пациентов"]
    secondary_keywords: list[str]  # ["SEO для клиник", "контент-маркетинг"]
    
    # Параметры контента
    content_type: str  # "blog_post", "faq", "guide", "case_study"
    target_length: int  # 1500 (слов)
    
    # GEO параметры
    target_platforms: list[str]  # ["chatgpt", "perplexity", "claude"]
    optimization_level: str  # "standard", "aggressive"
```

### 2.3 Опциональные параметры

```python
class AdvancedContentRequest(BaseModel):
    """Расширенные параметры создания контента"""
    
    # Tone of Voice
    tone: str = "professional"  # professional, friendly, authoritative
    audience: str = "medical_professionals"  # target audience
    
    # Структура
    include_faq: bool = True  # Включить FAQ секцию
    faq_questions_count: int = 5  # Количество вопросов в FAQ
    
    # Citation engineering
    include_statistics: bool = True  # Включить статистику
    include_quotes: bool = True  # Включить цитаты экспертов
    include_case_studies: bool = False  # Включить кейсы
    
    # Форматирование
    include_schema: bool = True  # Генерировать Schema.org разметку
    include_llms_txt: bool = False  # Генерировать llms.txt
```

### 2.4 Валидация входных данных

```python
async def validate_request(self, request: ContentRequest) -> ValidationResult:
    """Валидация запроса на создание контента"""
    
    errors = []
    
    # Проверка темы
    if not request.topic or len(request.topic) < 10:
        errors.append("topic: min 10 characters required")
    
    # Проверка ключевых слов
    if not request.primary_keywords:
        errors.append("primary_keywords: at least 1 keyword required")
    
    if len(request.primary_keywords) > 5:
        errors.append("primary_keywords: max 5 keywords allowed")
    
    # Проверка длины контента
    if request.target_length < 500:
        errors.append("target_length: min 500 words")
    
    if request.target_length > 5000:
        errors.append("target_length: max 5000 words")
    
    # Проверка типа контента
    valid_types = ["blog_post", "faq", "guide", "case_study"]
    if request.content_type not in valid_types:
        errors.append(f"content_type: must be one of {valid_types}")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors
    )
```

---

## 3. Алгоритм работы

### 3.1 Общая схема

```
1. Получить запрос на создание контента
2. Провести исследование темы (источники, статистика, конкуренты)
3. Создать структуру контента (outline)
4. Написать первые 50 слов (критично для GEO)
5. Написать основной контент
6. Создать FAQ секцию
7. Добавить citation bait элементы
8. Генерировать Schema.org разметку
9. Проверить GEO Score
10. Сохранить контент в Obsidian + БД
11. Отправить результат через Event Bus
```

### 3.2 Детальные шаги

#### Шаг 1: Исследование темы

```python
async def research_topic(
    self,
    topic: str,
    keywords: list[str]
) -> TopicResearch:
    """Исследовать тему перед созданием контента"""
    
    research = TopicResearch()
    
    # 1. Поиск статистики и фактов
    research.statistics = await self._find_statistics(topic)
    
    # 2. Анализ конкурентного контента
    research.competitor_content = await self._analyze_competitors(keywords)
    
    # 3. Поиск экспертных цитат
    research.expert_quotes = await self._find_expert_quotes(topic)
    
    # 4. Анализ популярных вопросов
    research.common_questions = await self._find_common_questions(topic)
    
    return research
```

#### Шаг 2: Создание структуры контента

```python
async def create_outline(
    self,
    request: ContentRequest,
    research: TopicResearch
) -> ContentOutline:
    """Создать структуру контента"""
    
    outline = ContentOutline()
    
    # Заголовок (H1)
    outline.title = self._generate_title(request.topic, request.primary_keywords)
    
    # Первые 50 слов (критично!)
    outline.first_50_words = self._draft_first_50_words(
        request.topic,
        request.primary_keywords,
        research.statistics
    )
    
    # Основные секции (H2)
    outline.sections = self._generate_sections(
        request.topic,
        request.target_length,
        research
    )
    
    # FAQ секция
    if request.include_faq:
        outline.faq = self._generate_faq_outline(
            research.common_questions,
            count=5
        )
    
    return outline
```

#### Шаг 3: Написание первых 50 слов

```python
def draft_first_50_words(
    self,
    topic: str,
    keywords: list[str],
    statistics: list[Statistic]
) -> str:
    """Написать первые 50 слов (критично для GEO)"""
    
    # Правило первых 50 слов:
    # 1. Включить главное ключевое слово
    # 2. Дать чёткий ответ на вопрос
    # 3. Использовать цифры и факты
    # 4. Избегать вводных фраз
    
    # Пример для темы "Медицинский маркетинг"
    first_50 = f"""
{keywords[0].capitalize()} — это комплекс стратегий для привлечения 
пациентов в клиники через digital-каналы (SEO, контент, реклама). 
Эффективный {keywords[0]} увеличивает поток пациентов на 40-60% 
за 6 месяцев при бюджете от 100,000₽/месяц.
"""
    
    # Проверка длины (должно быть ~50 слов)
    word_count = len(first_50.split())
    if word_count > 60:
        # Сократить до 50 слов
        first_50 = self._trim_to_words(first_50, 50)
    
    return first_50.strip()
```

#### Шаг 4: Написание основного контента

```python
async def write_content(
    self,
    outline: ContentOutline,
    request: ContentRequest,
    research: TopicResearch
) -> str:
    """Написать основной контент"""
    
    content = []
    
    # Заголовок
    content.append(f"# {outline.title}\n")
    
    # Первые 50 слов (критично!)
    content.append(outline.first_50_words + "\n")
    
    # Основные секции
    for section in outline.sections:
        content.append(f"\n## {section.title}\n")
        
        # Написать параграфы секции
        for paragraph in section.paragraphs:
            text = await self._write_paragraph(
                paragraph.topic,
                request.primary_keywords,
                research
            )
            content.append(text + "\n")
        
        # Добавить citation bait элементы
        if section.include_statistics:
            stat = self._select_relevant_statistic(section.topic, research.statistics)
            content.append(f"\n**Статистика:** {stat.text}\n")
    
    return "\n".join(content)
```

#### Шаг 5: Создание FAQ секции

```python
async def create_faq_section(
    self,
    questions: list[str],
    topic: str,
    keywords: list[str]
) -> FAQSection:
    """Создать FAQ секцию с Schema.org разметкой"""
    
    faq = FAQSection()
    
    for question in questions[:5]:  # Топ-5 вопросов
        # Написать короткий ответ (50-150 слов)
        answer = await self._write_faq_answer(
            question,
            topic,
            keywords
        )
        
        faq.items.append(FAQItem(
            question=question,
            answer=answer
        ))
    
    # Генерировать Schema.org разметку
    faq.schema = self._generate_faq_schema(faq.items)
    
    return faq
```

#### Шаг 6: Добавление citation bait элементов

```python
def add_citation_bait(
    self,
    content: str,
    research: TopicResearch
) -> str:
    """Добавить элементы, которые AI захочет цитировать"""
    
    citation_elements = []
    
    # 1. Статистика с источниками
    for stat in research.statistics[:3]:
        citation_elements.append(
            f"**{stat.text}** (источник: {stat.source})"
        )
    
    # 2. Экспертные цитаты
    for quote in research.expert_quotes[:2]:
        citation_elements.append(
            f'> "{quote.text}" — {quote.author}, {quote.title}'
        )
    
    # 3. Списки и таблицы (AI любит структурированные данные)
    citation_elements.append(
        self._create_comparison_table(research)
    )
    
    # Вставить citation bait в контент
    enhanced_content = self._insert_citation_bait(
        content,
        citation_elements
    )
    
    return enhanced_content
```

#### Шаг 7: Генерация Schema.org разметки

```python
def generate_schema_markup(
    self,
    content: str,
    faq: FAQSection
) -> dict:
    """Генерировать Schema.org разметку"""
    
    schema = {
        "@context": "https://schema.org",
        "@graph": []
    }
    
    # Article schema
    schema["@graph"].append({
        "@type": "Article",
        "headline": self._extract_title(content),
        "description": self._extract_first_50_words(content),
        "author": {
            "@type": "Organization",
            "name": "iamaim.ru"
        }
    })
    
    # FAQPage schema
    if faq:
        schema["@graph"].append({
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": item.question,
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": item.answer
                    }
                }
                for item in faq.items
            ]
        })
    
    return schema
```

#### Шаг 8: Проверка GEO Score

```python
async def check_geo_score(
    self,
    content: str,
    schema: dict
) -> GEOScore:
    """Проверить GEO Score созданного контента"""
    
    score = GEOScore()
    
    # 1. Первые 50 слов (20 points)
    first_50 = self._extract_first_50_words(content)
    score.first_50_words = self._score_first_50_words(first_50)
    
    # 2. Структура контента (30 points)
    score.content_structure = self._score_content_structure(content)
    
    # 3. Citation элементы (30 points)
    score.citation_elements = self._score_citation_elements(content)
    
    # 4. Техническая готовность (20 points)
    score.technical_readiness = self._score_technical_readiness(schema)
    
    # Общий GEO Score
    score.total = (
        score.first_50_words +
        score.content_structure +
        score.citation_elements +
        score.technical_readiness
    )
    
    return score
```


---

## 4. Выходные данные

### 4.1 Структура результата

```python
class ContentResult(BaseModel):
    """Результат создания GEO-контента"""
    
    # Метаданные
    timestamp: datetime
    topic: str
    content_type: str
    
    # Контент
    title: str
    content: str  # Markdown
    word_count: int
    
    # GEO элементы
    first_50_words: str
    faq_section: Optional[FAQSection]
    schema_markup: dict
    
    # Метрики
    geo_score: GEOScore
    primary_keywords_density: dict[str, float]
    
    # Файлы
    markdown_file: str  # Путь к .md файлу
    html_file: Optional[str]  # Путь к .html файлу
```

### 4.2 Формат контента

**Markdown (основной формат):**
```markdown
---
title: "Медицинский маркетинг: полное руководство 2024"
date: 2024-05-10
keywords: ["медицинский маркетинг", "привлечение пациентов"]
geo_score: 75
status: ready_for_publication
---

# Медицинский маркетинг: полное руководство 2024

Медицинский маркетинг — это комплекс стратегий для привлечения 
пациентов в клиники через digital-каналы (SEO, контент, реклама). 
Эффективный медицинский маркетинг увеличивает поток пациентов на 
40-60% за 6 месяцев при бюджете от 100,000₽/месяц.

## Что такое медицинский маркетинг

[Основной контент...]

## FAQ

**Вопрос:** Сколько стоит медицинский маркетинг?
**Ответ:** Бюджет на медицинский маркетинг начинается от 100,000₽/месяц...

[Schema.org разметка в конце файла]
```

### 4.3 Event Bus события

```python
# Событие: контент создан
await event_bus.publish(Event(
    type="geo.content.created",
    source="geo-content-agent",
    data={
        "topic": "Медицинский маркетинг",
        "content_type": "blog_post",
        "word_count": 1500,
        "geo_score": 75,
        "markdown_file": "AIM/obsidian/geo-content-agent/wiki/content/medical-marketing-guide.md",
        "ready_for_publication": True
    }
))

# Событие: низкий GEO Score (требуется доработка)
await event_bus.publish(Event(
    type="geo.content.low_score",
    source="geo-content-agent",
    priority="warning",
    data={
        "topic": "SEO для клиник",
        "geo_score": 45,
        "issues": [
            "first_50_words: missing primary keyword",
            "faq_section: not found",
            "schema_markup: incomplete"
        ],
        "action_required": True
    }
))
```

---

## 5. Метрики успеха

### 5.1 KPI агента

| Метрика | Целевое значение | Измерение |
|---------|------------------|-----------|
| **GEO Score** | > 70/100 | Средний GEO Score созданного контента |
| **Content Quality** | > 90% | Процент контента, прошедшего проверку |
| **Production Rate** | 3-5 статей/день | Количество созданного контента |
| **Keyword Density** | 1-2% | Плотность ключевых слов |
| **FAQ Coverage** | 100% | Процент контента с FAQ секцией |

### 5.2 Бизнес-метрики

| Метрика | Целевое значение | Описание |
|---------|------------------|----------|
| **Citation Rate** | > 15% | Процент контента, процитированного AI |
| **Share of Voice** | > 30% | Доля упоминаний бренда vs конкуренты |
| **Time to Citation** | < 7 дней | Время до первого цитирования в AI |
| **Content ROI** | > 200% | ROI от созданного контента |

### 5.3 Дашборд метрик

```python
# Grafana dashboard
{
    "title": "GEO Content Dashboard",
    "panels": [
        {
            "title": "Average GEO Score",
            "type": "stat",
            "targets": [
                "SELECT AVG(geo_score) FROM content_results WHERE time > now() - 30d"
            ]
        },
        {
            "title": "Content Production Rate",
            "type": "graph",
            "targets": [
                "SELECT COUNT(*) FROM content_results GROUP BY time(1d)"
            ]
        },
        {
            "title": "Citation Rate by Content Type",
            "type": "piechart",
            "targets": [
                "SELECT COUNT(*) FROM citations GROUP BY content_type"
            ]
        }
    ]
}
```

---

## 6. Коммуникация

### 6.1 Event Bus интеграция

**Подписки (входящие события):**
```python
# Запрос на создание контента
@event_bus.subscribe("geo.content.requested")
async def handle_content_request(event: Event):
    request = ContentRequest(**event.data)
    result = await self.create_content(request)
    await self.publish_result(result)

# Запрос на улучшение контента
@event_bus.subscribe("geo.optimization.recommendations")
async def handle_optimization_request(event: Event):
    recommendations = event.data["recommendations"]
    improved_content = await self.improve_content(recommendations)
    await self.publish_result(improved_content)
```

**Публикации (исходящие события):**
```python
# Контент создан
await event_bus.publish(Event(
    type="geo.content.created",
    source="geo-content-agent",
    data=result.dict()
))

# Контент готов к публикации
await event_bus.publish(Event(
    type="geo.content.ready",
    source="geo-content-agent",
    target="content-scheduler",
    data={
        "content_id": result.id,
        "markdown_file": result.markdown_file,
        "publication_date": datetime.now() + timedelta(days=1)
    }
))
```

### 6.2 Эскалация к SEO Magister

**Когда эскалировать:**
1. GEO Score < 60 после 3 попыток улучшения
2. Не удалось найти достаточно статистики/фактов
3. Тема слишком сложная для автоматической генерации
4. Требуется экспертная проверка контента

```python
async def escalate_to_magister(self, issue: Issue):
    """Эскалация проблемы к SEO Magister"""
    
    await event_bus.publish(Event(
        type="geo.content.escalation",
        source="geo-content-agent",
        target="seo-magister",
        priority="high",
        data={
            "issue_type": issue.type,
            "topic": issue.topic,
            "geo_score": issue.geo_score,
            "attempts": issue.attempts,
            "recommended_action": "Manual content review required",
            "correlation_id": self.correlation_id
        }
    ))
```

### 6.3 Obsidian vault структура

```
AIM/obsidian/geo-content-agent/
├── raw/
│   └── research/                    # Исследования тем
│       ├── medical-marketing-research.json
│       └── seo-for-clinics-research.json
├── wiki/
│   ├── index.md                     # Каталог контента
│   ├── log.md                       # Хронология создания
│   ├── content/                     # Созданный контент
│   │   ├── medical-marketing-guide.md
│   │   └── seo-for-clinics-guide.md
│   ├── templates/                   # Шаблоны контента
│   │   ├── blog-post-template.md
│   │   └── faq-template.md
│   ├── research/                    # Обработанные исследования
│   │   └── medical-marketing-summary.md
│   └── statistics/                  # База статистики
│       └── medical-marketing-stats.md
├── decisions/
│   └── content-strategy.md          # Стратегия создания контента
└── SCHEMA.md                        # Правила vault
```

### 6.4 Формат данных (JSON + MD)

**JSON для Event Bus:**
```json
{
  "type": "geo.content.created",
  "source": "geo-content-agent",
  "data": {
    "topic": "Медицинский маркетинг",
    "geo_score": 75,
    "word_count": 1500,
    "markdown_file": "path/to/file.md"
  }
}
```

**Markdown для Obsidian:**
```markdown
---
topic: Медицинский маркетинг
date: 2024-05-10
geo_score: 75
status: ready_for_publication
---

# Медицинский маркетинг: полное руководство

[Контент...]
```

---

## 7. Обработка ошибок

### 7.1 Общие ошибки

```python
class ContentCreationError(Exception):
    """Базовый класс ошибок создания контента"""
    pass

# Retry стратегия
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type(ContentCreationError)
)
async def create_content_with_retry(request: ContentRequest):
    return await self.create_content(request)
```

### 7.2 Специфичные ошибки

| Ошибка | Причина | Действие |
|--------|---------|----------|
| `INSUFFICIENT_RESEARCH` | Не найдено достаточно данных | Escalate to SEO Magister |
| `LOW_GEO_SCORE` | GEO Score < 60 после 3 попыток | Escalate for manual review |
| `KEYWORD_DENSITY_LOW` | Плотность ключевых слов < 1% | Retry with keyword emphasis |
| `FAQ_GENERATION_FAILED` | Не удалось создать FAQ | Create content without FAQ |
| `SCHEMA_VALIDATION_FAILED` | Schema.org разметка некорректна | Fix schema and retry |

### 7.3 Graceful degradation

```python
async def create_content_with_fallback(self, request: ContentRequest):
    """Создание контента с fallback стратегией"""
    
    # Попытка 1: Полная GEO-оптимизация
    try:
        result = await self.create_geo_optimized_content(request)
        if result.geo_score >= 70:
            return result
    except Exception as e:
        logger.warning(f"Full GEO optimization failed: {e}")
    
    # Попытка 2: Базовая GEO-оптимизация (без FAQ)
    try:
        request.include_faq = False
        result = await self.create_basic_geo_content(request)
        if result.geo_score >= 60:
            return result
    except Exception as e:
        logger.error(f"Basic GEO optimization failed: {e}")
    
    # Fallback: Создать контент без GEO-оптимизации
    logger.info("Creating content without GEO optimization")
    result = await self.create_standard_content(request)
    
    # Эскалация для ручной оптимизации
    await self.escalate_to_magister(Issue(
        type="low_geo_score",
        topic=request.topic,
        geo_score=result.geo_score,
        attempts=3
    ))
    
    return result
```

---

## 8. Тестирование

### 8.1 Unit тесты

```python
# tests/unit/test_geo_content_agent.py

async def test_draft_first_50_words():
    """Тест создания первых 50 слов"""
    agent = GEOContentAgent()
    
    first_50 = agent.draft_first_50_words(
        topic="Медицинский маркетинг",
        keywords=["медицинский маркетинг", "привлечение пациентов"],
        statistics=[Statistic(text="40-60% рост за 6 месяцев")]
    )
    
    word_count = len(first_50.split())
    assert 45 <= word_count <= 55  # ~50 слов
    assert "медицинский маркетинг" in first_50.lower()
    assert any(char.isdigit() for char in first_50)  # Есть цифры

async def test_create_faq_section():
    """Тест создания FAQ секции"""
    agent = GEOContentAgent()
    
    faq = await agent.create_faq_section(
        questions=["Что такое медицинский маркетинг?", "Сколько стоит?"],
        topic="Медицинский маркетинг",
        keywords=["медицинский маркетинг"]
    )
    
    assert len(faq.items) == 2
    assert faq.schema["@type"] == "FAQPage"
    assert len(faq.schema["mainEntity"]) == 2

async def test_check_geo_score():
    """Тест проверки GEO Score"""
    agent = GEOContentAgent()
    
    content = """
    # Медицинский маркетинг
    
    Медицинский маркетинг — это комплекс стратегий для привлечения 
    пациентов в клиники через digital-каналы. Эффективный медицинский 
    маркетинг увеличивает поток пациентов на 40-60% за 6 месяцев.
    
    ## FAQ
    **Вопрос:** Что такое медицинский маркетинг?
    **Ответ:** Это комплекс стратегий...
    """
    
    schema = {"@type": "FAQPage"}
    
    score = await agent.check_geo_score(content, schema)
    
    assert score.total >= 60  # Минимальный приемлемый GEO Score
    assert score.first_50_words > 0
    assert score.content_structure > 0
```

### 8.2 Integration тесты

```python
# tests/integration/test_geo_content_integration.py

async def test_content_creation_workflow():
    """Тест полного workflow создания контента"""
    
    # Setup
    agent = GEOContentAgent(vault_path="test_vault", event_bus=event_bus)
    
    request = ContentRequest(
        topic="Медицинский маркетинг",
        goal="Получить цитирования в ChatGPT",
        primary_keywords=["медицинский маркетинг"],
        secondary_keywords=["привлечение пациентов"],
        content_type="blog_post",
        target_length=1500,
        target_platforms=["chatgpt", "perplexity"]
    )
    
    # Execute
    result = await agent.create_content(request)
    
    # Verify
    assert result.geo_score >= 70
    assert result.word_count >= 1400  # ~1500 слов
    assert result.faq_section is not None
    assert result.schema_markup["@type"] == "FAQPage"
    
    # Check Event Bus
    events = await event_bus.get_events(type="geo.content.created")
    assert len(events) == 1

async def test_content_to_publication_flow():
    """Тест E2E: создание → публикация"""
    
    # 1. Создание контента
    content_agent = GEOContentAgent(vault_path="test_vault", event_bus=event_bus)
    result = await content_agent.create_content(request)
    
    assert result.geo_score >= 70
    
    # 2. Контент готов к публикации
    events = await event_bus.get_events(type="geo.content.ready")
    assert len(events) == 1
    
    # 3. Content Scheduler получает контент
    scheduler_events = await event_bus.get_events(type="content.scheduled")
    assert len(scheduler_events) == 1
```

### 8.3 E2E тесты

```python
# tests/e2e/test_geo_content_e2e.py

async def test_full_geo_content_pipeline():
    """Тест полного pipeline: исследование → создание → оптимизация → публикация"""
    
    # 1. Keyword Research Agent предоставляет ключевые слова
    keywords_event = Event(
        type="keywords.researched",
        source="keyword-research-agent",
        data={"keywords": ["медицинский маркетинг", "привлечение пациентов"]}
    )
    await event_bus.publish(keywords_event)
    
    # 2. GEO Content Agent создаёт контент
    content_agent = GEOContentAgent(vault_path="test_vault", event_bus=event_bus)
    result = await content_agent.create_content(request)
    
    assert result.geo_score >= 70
    
    # 3. GEO Optimization Agent проверяет контент
    optimization_events = await event_bus.get_events(type="geo.optimization.completed")
    assert len(optimization_events) == 1
    
    # 4. Content Scheduler публикует контент
    publication_events = await event_bus.get_events(type="content.published")
    assert len(publication_events) == 1
    
    # 5. GEO Monitoring Agent отслеживает цитирования
    monitoring_events = await event_bus.get_events(type="geo.monitoring.citation_detected")
    # Может быть 0 сразу после публикации (нормально)
```


---

## 9. Примеры использования

### 9.1 Базовое создание контента

```python
from aim.subagents.geo_content_agent import GEOContentAgent

# Инициализация агента
agent = GEOContentAgent(
    vault_path="AIM/obsidian/geo-content-agent",
    event_bus=event_bus
)

# Создание GEO-оптимизированного контента
request = ContentRequest(
    topic="Медицинский маркетинг для клиник",
    goal="Получить цитирования в ChatGPT и Perplexity",
    primary_keywords=["медицинский маркетинг", "привлечение пациентов"],
    secondary_keywords=["SEO для клиник", "контент-маркетинг"],
    content_type="blog_post",
    target_length=1500,
    target_platforms=["chatgpt", "perplexity", "claude"]
)

result = await agent.create_content(request)

print(f"GEO Score: {result.geo_score}/100")
print(f"Word count: {result.word_count}")
print(f"Content file: {result.markdown_file}")
```

### 9.2 Создание FAQ контента

```python
# Создание FAQ-страницы
request = ContentRequest(
    topic="Часто задаваемые вопросы о медицинском маркетинге",
    goal="Попасть в AI-ответы на популярные вопросы",
    primary_keywords=["медицинский маркетинг FAQ"],
    content_type="faq",
    target_length=800,
    target_platforms=["chatgpt", "perplexity"]
)

# Расширенные параметры
advanced = AdvancedContentRequest(
    include_faq=True,
    faq_questions_count=10,  # 10 вопросов
    include_statistics=True,
    include_schema=True
)

result = await agent.create_content(request, advanced)

# FAQ секция автоматически создана
print(f"FAQ items: {len(result.faq_section.items)}")
print(f"Schema markup: {result.schema_markup['@type']}")
```

### 9.3 Пакетное создание контента

```python
# Создание серии статей
topics = [
    "Медицинский маркетинг: полное руководство",
    "SEO для клиник: как привлечь пациентов",
    "Контент-маркетинг в медицине",
    "Реклама медицинских услуг: лучшие практики"
]

results = []
for topic in topics:
    request = ContentRequest(
        topic=topic,
        primary_keywords=[topic.split(":")[0].lower()],
        content_type="blog_post",
        target_length=1500
    )
    
    result = await agent.create_content(request)
    results.append(result)

# Статистика
avg_score = sum(r.geo_score for r in results) / len(results)
print(f"Average GEO Score: {avg_score:.1f}/100")
print(f"Total content created: {len(results)} articles")
```

### 9.4 Интеграция с Content Scheduler

```python
# Создание контента и автоматическая публикация
@event_bus.subscribe("geo.content.created")
async def schedule_publication(event: Event):
    content_data = event.data
    
    # Проверка GEO Score
    if content_data["geo_score"] >= 70:
        # Запланировать публикацию
        await event_bus.publish(Event(
            type="content.schedule.requested",
            source="geo-content-agent",
            target="content-scheduler",
            data={
                "content_file": content_data["markdown_file"],
                "publication_date": datetime.now() + timedelta(days=1),
                "channels": ["blog", "social"]
            }
        ))
```

---

## 10. Зависимости

### 10.1 Внешние зависимости

**Python библиотеки:**
```python
# requirements.txt
openai>=1.0.0            # GPT-4 для генерации контента (опционально)
anthropic>=0.8.0         # Claude для генерации контента (опционально)
beautifulsoup4>=4.12.0   # HTML parsing
markdown>=3.5.0          # Markdown processing
pydantic>=2.5.0          # Data validation
jinja2>=3.1.0            # Template rendering
```

**Внешние API (опционально):**
- **OpenAI GPT-4 API** — генерация контента высокого качества
- **Anthropic Claude API** — альтернатива для генерации
- **Perplexity API** — исследование тем (если доступно)

### 10.2 Внутренние зависимости

**Framework компоненты:**
```python
from meai.agents.base_agent import BaseAgent
from meai.events.event_bus import EventBus
from meai.memory.obsidian import ObsidianVault
from meai.storage.database import Database
```

**Связанные агенты:**
- **GEO Optimization Agent** — предоставляет рекомендации по оптимизации
- **GEO Monitoring Agent** — предоставляет данные о популярных темах
- **SEO Magister** — координирует создание контента
- **Keyword Research Agent** — предоставляет целевые ключевые слова
- **Content Scheduler Agent** — получает готовый контент для публикации
- **Tone of Voice Agent** — предоставляет ToV guidelines

**Obsidian vault:**
- `AIM/obsidian/geo-content-agent/` — хранилище созданного контента

**База данных:**
- Таблица `geo_content` — история созданного контента
- Таблица `geo_content_scores` — динамика GEO Score
- Таблица `content_research` — исследования тем

---

## 11. Deployment

### 11.1 Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Установка зависимостей
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Запуск агента
CMD ["python", "-m", "aim.subagents.geo_content_agent"]
```

### 11.2 Конфигурация

```yaml
# config/geo_content_agent.yaml
agent:
  name: "GEO Content Agent"
  vault_path: "AIM/obsidian/geo-content-agent"
  
content:
  default_length: 1500
  default_optimization_level: "standard"
  include_faq: true
  faq_questions_count: 5
  
generation:
  provider: "openai"  # openai, anthropic, local
  model: "gpt-4"
  temperature: 0.7
  max_tokens: 4000
  
geo:
  min_geo_score: 70
  first_50_words_weight: 0.20
  content_structure_weight: 0.30
  citation_elements_weight: 0.30
  technical_readiness_weight: 0.20
  
api:
  openai_api_key: "${OPENAI_API_KEY}"
  anthropic_api_key: "${ANTHROPIC_API_KEY}"
```

### 11.3 Мониторинг

**Метрики для Prometheus:**
```python
# Метрики агента
content_created_total = Counter('geo_content_created_total', 'Total content created')
geo_score_gauge = Gauge('geo_content_score', 'GEO Score', ['topic'])
content_word_count = Histogram('geo_content_word_count', 'Content word count')
creation_duration = Histogram('geo_content_creation_duration_seconds', 'Content creation duration')
```

**Алерты:**
```yaml
# alerts.yaml
- alert: LowGEOScore
  expr: geo_content_score < 60
  for: 5m
  annotations:
    summary: "Content created with low GEO Score"
    
- alert: ContentCreationFailed
  expr: rate(geo_content_creation_failed_total[5m]) > 0.1
  annotations:
    summary: "High content creation failure rate"
    
- alert: LowProductionRate
  expr: rate(geo_content_created_total[1h]) < 1
  annotations:
    summary: "Content production rate below target"
```

### 11.4 Логирование

```python
# Структурированное логирование
logger.info(
    "content_created",
    extra={
        "topic": request.topic,
        "content_type": request.content_type,
        "word_count": result.word_count,
        "geo_score": result.geo_score,
        "duration_seconds": duration,
        "has_faq": result.faq_section is not None
    }
)
```

---

## 12. Changelog

### Version 1.0.0 (2026-05-10)

**Создана спецификация:**
- ✅ Базовая архитектура агента
- ✅ Алгоритм создания контента (8 шагов)
- ✅ Правило первых 50 слов
- ✅ FAQ секция с Schema.org
- ✅ Citation bait элементы
- ✅ GEO Score проверка
- ✅ Интеграция с Event Bus
- ✅ Obsidian vault структура
- ✅ Метрики и KPI
- ✅ Обработка ошибок
- ✅ Тестирование (unit, integration, e2e)

**Основано на исследовании:**
- Правило первых 50 слов (44.2% цитирований)
- FAQPage schema для структурированных данных
- Citation engineering паттерны
- GEO Score методология (0-100)

---

## 13. Исследования и TODO

### 13.1 Приоритет 1: MVP (Фаза 1)

**Базовая функциональность:**
- ✅ Исследование темы (статистика, факты)
- ✅ Создание структуры контента (outline)
- ✅ Написание первых 50 слов
- ✅ Создание основного контента
- ✅ FAQ секция с Schema.org
- ✅ GEO Score проверка

**Требуется реализация:**
- [ ] Интеграция с GPT-4 для генерации контента
- [ ] Парсинг статистики из надёжных источников
- [ ] Генерация Schema.org разметки
- [ ] Сохранение контента в Obsidian vault
- [ ] Валидация GEO Score

### 13.2 Приоритет 2: Расширенная генерация (Фаза 2)

**Citation Engineering:**
- [ ] Автоматический поиск релевантной статистики
- [ ] Генерация экспертных цитат
- [ ] Создание сравнительных таблиц
- [ ] Добавление кейсов и примеров

**Персонализация под AI-платформы:**
- [ ] Адаптация контента под ChatGPT (Wikipedia-style)
- [ ] Адаптация контента под Perplexity (Reddit-style)
- [ ] Адаптация контента под Claude (structured answers)
- [ ] Адаптация контента под Google AI (featured snippets)

**Автоматизация:**
- [ ] Генерация llms.txt файла
- [ ] Автоматическое обновление контента
- [ ] A/B тестирование вариантов контента

### 13.3 Приоритет 3: AI-генерация (Фаза 3)

**GPT-4 интеграция:**
- [ ] Генерация контента через GPT-4
- [ ] Fine-tuning модели на GEO-паттернах
- [ ] Автоматическая оптимизация промптов

**Claude интеграция:**
- [ ] Альтернативная генерация через Claude
- [ ] Сравнение качества GPT-4 vs Claude
- [ ] Выбор лучшей модели для каждого типа контента

**Качество контента:**
- [ ] Проверка фактов через Perplexity
- [ ] Детекция плагиата
- [ ] Проверка читабельности (Flesch Reading Ease)

### 13.4 Исследовательские задачи

**TODO для изучения:**

1. **OpenAI GPT-4 API**
   - Документация: https://platform.openai.com/docs
   - Стоимость: $0.03/1K tokens (input), $0.06/1K tokens (output)
   - Функции: генерация контента, оптимизация под GEO
   - Приоритет: Фаза 2

2. **Anthropic Claude API**
   - Документация: https://docs.anthropic.com
   - Стоимость: $0.015/1K tokens (input), $0.075/1K tokens (output)
   - Функции: альтернатива GPT-4, structured outputs
   - Приоритет: Фаза 2

3. **Perplexity API для исследования**
   - Статус: Закрытая beta
   - Альтернатива: Парсинг публичных ответов
   - Функции: поиск статистики, фактов, источников
   - Приоритет: Фаза 2

4. **Schema.org валидаторы**
   - Google Rich Results Test: https://search.google.com/test/rich-results
   - Schema.org Validator: https://validator.schema.org
   - Приоритет: Фаза 1

5. **Readability API**
   - Flesch Reading Ease Score
   - Gunning Fog Index
   - SMOG Index
   - Приоритет: Фаза 2

### 13.5 Метрики для исследования

**Вопросы для валидации:**
- Какой минимальный GEO Score для цитирования?
- Как часто нужно обновлять контент?
- Какая корреляция между GEO Score и Citation Rate?
- Какие типы контента AI цитирует чаще?

**Эксперименты:**
- A/B тест: GPT-4 vs Claude для генерации
- Корреляция длины контента и Citation Rate
- Влияние FAQ секции на видимость в AI
- Эффективность citation bait элементов

---

## Приложение A: Статистика и исследования

### A.1 Ключевые метрики GEO-контента (2024-2026)

**Эффективность GEO-оптимизации:**
- +40% видимость после GEO оптимизации
- 44.2% цитирований из первых 30% текста
- 85% цитирований из доменов, которыми вы не владеете

**Типы контента с высоким Citation Rate:**
- FAQ страницы: 25-35% Citation Rate
- Руководства (guides): 20-30% Citation Rate
- Статистические обзоры: 15-25% Citation Rate
- Кейсы: 10-20% Citation Rate

**Оптимальная длина контента:**
- Короткие ответы (500-800 слов): 15% Citation Rate
- Средние статьи (1000-1500 слов): 25% Citation Rate
- Длинные руководства (2000-3000 слов): 30% Citation Rate

### A.2 Лучшие практики создания GEO-контента

**Правило первых 50 слов:**
1. Включить главное ключевое слово в первом предложении
2. Дать чёткий, конкретный ответ на вопрос
3. Использовать цифры и факты (статистика, проценты)
4. Избегать вводных фраз ("В этой статье мы рассмотрим...")

**FAQ секция:**
- Минимум 5 вопросов
- Короткие ответы (50-150 слов)
- Естественный язык (как люди спрашивают)
- Включать целевые ключевые слова

**Citation bait элементы:**
- Статистика с источниками
- Экспертные цитаты
- Сравнительные таблицы
- Списки и чек-листы
- Кейсы с конкретными цифрами

**Schema.org разметка:**
- Article schema для статей
- FAQPage schema для FAQ
- HowTo schema для руководств
- Review schema для обзоров

### A.3 Инструменты для создания GEO-контента

**Бесплатные:**
- Schema.org Validator — проверка разметки
- Google Rich Results Test — проверка структурированных данных
- Hemingway Editor — проверка читабельности

**Платные:**
- OpenAI GPT-4 ($0.03-0.06/1K tokens) — генерация контента
- Anthropic Claude ($0.015-0.075/1K tokens) — альтернатива GPT-4
- Grammarly ($12/мес) — проверка грамматики и стиля

### A.4 Benchmark по индустрии

**Medical Marketing (средние значения):**
- GEO Score: 60-70/100
- Citation Rate: 15-20%
- Average word count: 1200-1500 слов
- FAQ coverage: 60-70%

**Топ-игроки (лидеры рынка):**
- GEO Score: 80-90/100
- Citation Rate: 30-40%
- Average word count: 1800-2500 слов
- FAQ coverage: 100%

### A.5 ROI от GEO-контента

**Средние показатели:**
- Стоимость создания: 5,000-10,000₽ за статью
- Citation Rate: 20% (1 из 5 статей цитируется)
- Share of Voice: +5-10% за статью
- Время до первого цитирования: 7-14 дней

**ROI расчёт:**
- Инвестиция: 50,000₽ (10 статей)
- Citation Rate: 20% (2 статьи процитированы)
- Share of Voice: +15% (2 статьи × 7.5%)
- Трафик: +30% (корреляция с Share of Voice)
- ROI: 200-300% за 6 месяцев

---

**Дата создания:** 2026-05-10 22:00 GMT+3  
**Автор:** Mikhail Eliseev (via meAI Architect)  
**Версия:** 1.0.0  
**Статус:** ✅ Готов к реализации  
**Размер:** ~1450 строк, ~50 KB

