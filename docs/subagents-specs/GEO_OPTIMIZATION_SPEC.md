# GEO Optimization Agent - Спецификация

**Версия:** 1.0  
**Дата создания:** 2026-05-10  
**Автор:** Mikhail Eliseev (via meAI Architect)  
**Статус:** Draft  
**Приоритет:** P1 (⭐⭐⭐ Критичный)

---

## 1. ОБЗОР

### 1.1 Назначение

**GEO Optimization Agent** — автономный агент для оптимизации контента под AI-поиск (ChatGPT, Perplexity, Claude, Gemini). Агент анализирует существующий контент и применяет GEO-практики для увеличения видимости в ответах нейросетей на 40%+.

**GEO (Generative Engine Optimization)** — практика оптимизации контента для появления в AI-генерируемых ответах. В отличие от SEO (оптимизация для поисковых систем), GEO фокусируется на цитируемости контента нейросетями.

### 1.2 Роль в системе

**Родительский Magister:** SEO Magister  
**Тип:** Execution Subagent  
**Домен:** AI Search Optimization, Content Structure, Citation Engineering

**Связанные агенты:**
- **Keyword Research Agent** — традиционный SEO (Google, Яндекс)
- **GEO Monitoring Agent** — мониторинг упоминаний в AI
- **GEO Content Agent** — создание контента для AI-поиска
- **Content Magister** — источник контента для оптимизации

### 1.3 Уникальная ценность

GEO Optimization Agent позволяет:
- **Увеличить видимость в AI на 40%** — доказанная эффективность GEO-практик
- **Стать источником для нейросетей** — контент цитируется в ответах ChatGPT, Perplexity, Claude
- **Захватить новый канал трафика** — AI-поиск растёт (900M пользователей ChatGPT в неделю, 1B+ запросов Perplexity в месяц)
- **Опередить конкурентов** — большинство компаний ещё не работают с GEO

**Критичность:** AI-поиск становится основным каналом трафика. Если вашей компании нет в AI-ответах — вы не существуете для огромной части аудитории. Позиция #1 в Google даёт CTR на 38% меньше, чем год назад.

### 1.4 Границы ответственности

**Что делает:**
- Анализ существующего контента на сайте
- Применение правила первых 50 слов (front-loading критичной информации)
- Добавление структурированных данных (FAQPage schema)
- Создание llms.txt файла для AI-краулеров
- Оптимизация структуры контента (заголовки, списки, таблицы)
- Добавление цитируемых элементов (статистика, определения, уникальные данные)
- Проверка robots.txt (разрешение для GPTBot, ClaudeBot, PerplexityBot)
- Генерация рекомендаций по улучшению цитируемости

**Что НЕ делает:**
- Не создаёт новый контент с нуля (это GEO Content Agent)
- Не мониторит упоминания в AI (это GEO Monitoring Agent)
- Не работает с традиционным SEO (это Keyword Research Agent)
- Не публикует контент на сторонние платформы (Reddit, Wikipedia)

### 1.5 Связанные агенты

**GEO Monitoring Agent** — мониторинг упоминаний бренда в AI-поиске:
- Отслеживает brand mention frequency в ChatGPT, Perplexity, Claude
- Измеряет AI visibility и share of voice
- Проверяет accuracy of representation
- Сравнивает с конкурентами

**GEO Content Agent** — создание контента специально для AI-поиска:
- Пишет цитируемый контент (статистика, определения, уникальные данные)
- Создаёт контент для сторонних платформ (Reddit, Wikipedia, отзовики)
- Генерирует FAQ-секции и структурированные ответы

**Различия между агентами:**

| Аспект | GEO Optimization Agent | GEO Monitoring Agent | GEO Content Agent |
|--------|------------------------|----------------------|-------------------|
| Задача | Оптимизация существующего контента | Мониторинг упоминаний в AI | Создание нового контента для AI |
| Входные данные | URL страниц сайта | Список брендов и запросов | Темы и ключевые слова |
| Выходные данные | Оптимизированный контент + рекомендации | Метрики видимости + алерты | Готовый цитируемый контент |
| Частота работы | По запросу или раз в месяц | Ежедневно | По запросу |
| Канал трафика | AI-поиск (оптимизация) | AI-поиск (мониторинг) | AI-поиск (создание) |

**Связь:** Все три агента работают параллельно под SEO Magister и дополняют друг друга для полного покрытия AI-поиска.

---

## 2. ВХОДНЫЕ ДАННЫЕ

### 2.1 Источники данных

**Основной источник:**
- **URL страниц сайта** — контент для оптимизации (статьи, лендинги, продуктовые страницы)

**Дополнительные источники:**
- **Content Magister** — список приоритетных страниц для оптимизации
- **GEO Monitoring Agent** — данные о текущей видимости в AI
- **Keyword Research Agent** — целевые темы и запросы

### 2.2 Обязательные параметры

```python
class GEOOptimizationInput(BaseModel):
    urls: list[str]  # Список URL для оптимизации
    target_ai_platforms: list[str] = ["chatgpt", "perplexity", "claude", "gemini"]  # Целевые AI-платформы
    optimization_level: str = "standard"  # Уровень оптимизации: minimal, standard, aggressive
    brand_name: str  # Название бренда для упоминаний
    industry: str  # Индустрия (для контекста оптимизации)
```

### 2.3 Опциональные параметры

```python
class GEOOptimizationOptionalInput(BaseModel):
    priority_keywords: list[str] = []  # Приоритетные ключевые слова для оптимизации
    competitor_urls: list[str] = []  # URL конкурентов для сравнения
    existing_llms_txt: str = None  # Существующий llms.txt (если есть)
    schema_markup_enabled: bool = True  # Добавлять ли FAQPage schema
    create_llms_txt: bool = True  # Создавать ли llms.txt файл
    check_robots_txt: bool = True  # Проверять ли robots.txt
```

### 2.4 Валидация входных данных

**Правила валидации:**
- `urls` не может быть пустым списком
- Каждый URL должен быть валидным (начинаться с http:// или https://)
- `optimization_level` должен быть одним из: minimal, standard, aggressive
- `brand_name` не может быть пустым
- `target_ai_platforms` должен содержать минимум 1 платформу

**Обработка ошибок валидации:**
- Если валидация не прошла → вернуть `INVALID_INPUT` с описанием ошибки
- Логировать в Event Store
- Не выполнять задачу

---

## 3. АЛГОРИТМ РАБОТЫ

### 3.1 Общая схема

**8 основных шагов:**

1. **Анализ текущего контента** — извлечение HTML, парсинг структуры
2. **Проверка технической готовности** — robots.txt, llms.txt, schema markup
3. **Применение правила первых 50 слов** — front-loading критичной информации
4. **Оптимизация структуры** — заголовки, списки, таблицы, FAQ
5. **Добавление цитируемых элементов** — статистика, определения, уникальные данные
6. **Генерация структурированных данных** — FAQPage schema, llms.txt
7. **Проверка качества оптимизации** — GEO score (0-100)
8. **Генерация отчёта и рекомендаций** — что сделано, что нужно улучшить

### 3.2 Детальное описание шагов

**Шаг 1: Анализ текущего контента**

- Извлечь HTML страницы (Playwright или requests)
- Парсинг структуры:
  - Заголовки (H1-H6)
  - Параграфы (первые 50 слов, остальной текст)
  - Списки (ul, ol)
  - Таблицы
  - Изображения (alt text)
  - Ссылки (внутренние, внешние)
- Извлечь существующий schema markup (если есть)
- Определить тип контента (статья, лендинг, продуктовая страница)

**Шаг 2: Проверка технической готовности**

- **robots.txt:**
  - Проверить наличие файла
  - Проверить, что GPTBot, ClaudeBot, PerplexityBot НЕ заблокированы
  - Если заблокированы → добавить в рекомендации разблокировать

- **llms.txt:**
  - Проверить наличие файла в корне сайта
  - Если нет → создать базовый llms.txt
  - Если есть → проверить структуру и дополнить

- **Schema markup:**
  - Проверить наличие FAQPage schema
  - Проверить наличие Article schema
  - Если нет → добавить в рекомендации

**Шаг 3: Применение правила первых 50 слов**

**Правило:** 44.2% всех AI-цитат приходятся на первые 30% текста страницы. Если главный ответ закопан в середине статьи, LLM его просто не подхватит.

**Действия:**
- Извлечь первые 50 слов текста
- Проверить, содержат ли они прямой ответ на главный вопрос
- Если нет → переписать первый абзац:
  - Начать с прямого ответа на главный вопрос
  - Использовать ключевые слова из заголовка
  - Добавить контекст (кто, что, где, когда, почему)
  - Длина: 50-100 слов

**Пример оптимизации:**

**До:**
```
В этой статье мы рассмотрим различные аспекты медицинского маркетинга. 
Сначала поговорим о истории, потом о современных трендах...
```

**После:**
```
Медицинский маркетинг — это комплекс стратегий для привлечения пациентов 
в клиники через digital-каналы (SEO, контент, реклама). Эффективный 
медицинский маркетинг увеличивает поток пациентов на 40-60% за 6 месяцев 
при бюджете от 100,000₽/месяц.
```

**Шаг 4: Оптимизация структуры**

**AI любит структуру:** Чёткие иерархии, списки, таблицы, FAQ-секции, пошаговые гайды, краткие определения.

**Действия:**

1. **Заголовки:**
   - Проверить иерархию (H1 → H2 → H3)
   - Добавить ключевые слова в заголовки
   - Сделать заголовки описательными (не "Введение", а "Что такое медицинский маркетинг")

2. **Списки:**
   - Преобразовать длинные параграфы в списки (где уместно)
   - Использовать нумерованные списки для шагов
   - Использовать маркированные списки для перечислений

3. **Таблицы:**
   - Добавить таблицы для сравнений
   - Добавить таблицы для данных и статистики
   - Использовать чёткие заголовки столбцов

4. **FAQ-секции:**
   - Добавить секцию "Часто задаваемые вопросы"
   - Минимум 3-5 вопросов
   - Прямые ответы на каждый вопрос (50-100 слов)

**Шаг 5: Добавление цитируемых элементов**

**Цель:** Создать "citation bait" — элементы, которые AI будет цитировать.

**Типы цитируемых элементов:**

1. **Уникальная статистика:**
   - Собственные исследования
   - Данные из практики
   - Метрики и результаты

2. **Чёткие определения:**
   - Определение ключевых терминов
   - Краткие и точные формулировки
   - Контекст использования

3. **Пошаговые инструкции:**
   - Нумерованные списки
   - Конкретные действия
   - Ожидаемые результаты

4. **Экспертные мнения:**
   - Цитаты экспертов
   - Кейсы и примеры
   - Уникальные инсайты

**Действия:**
- Найти места для добавления статистики
- Добавить определения ключевых терминов
- Преобразовать описания в пошаговые инструкции
- Добавить экспертные комментарии (если есть)

**Шаг 6: Генерация структурированных данных**

**FAQPage Schema:**

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [{
    "@type": "Question",
    "name": "Что такое медицинский маркетинг?",
    "acceptedAnswer": {
      "@type": "Answer",
      "text": "Медицинский маркетинг — это комплекс стратегий для привлечения пациентов в клиники через digital-каналы (SEO, контент, реклама). Эффективный медицинский маркетинг увеличивает поток пациентов на 40-60% за 6 месяцев."
    }
  }]
}
```

**llms.txt:**

```markdown
# Название сайта

> Краткое описание (1-2 предложения)

Контекст: кто мы, что делаем, для кого

## Основные разделы

- [Услуги](url): Описание услуг
- [Цены](url): Прайс-лист
- [Контакты](url): Как связаться

## Дополнительно

- [Блог](url): Статьи и новости
- [Кейсы](url): Примеры работ
```

**Шаг 7: Проверка качества оптимизации**

**GEO Score (0-100):**

- **Правило первых 50 слов** (20 баллов):
  - Прямой ответ в первых 50 словах: +20
  - Ответ в первых 100 словах: +10
  - Ответ дальше: 0

- **Структура контента** (30 баллов):
  - Чёткая иерархия заголовков: +10
  - Списки и таблицы: +10
  - FAQ-секция: +10

- **Цитируемые элементы** (30 баллов):
  - Уникальная статистика: +10
  - Чёткие определения: +10
  - Пошаговые инструкции: +10

- **Техническая готовность** (20 баллов):
  - FAQPage schema: +7
  - llms.txt: +7
  - robots.txt (AI боты разрешены): +6

**Интерпретация:**
- 80-100: Отлично оптимизирован
- 60-79: Хорошо оптимизирован
- 40-59: Требуется улучшение
- 0-39: Плохо оптимизирован

**Шаг 8: Генерация отчёта и рекомендаций**

**Отчёт включает:**

1. **Сводка:**
   - GEO Score (0-100)
   - Количество оптимизированных страниц
   - Основные улучшения

2. **Детали по каждой странице:**
   - URL
   - GEO Score до/после
   - Что было сделано
   - Что нужно улучшить

3. **Технические рекомендации:**
   - robots.txt (если нужно исправить)
   - llms.txt (если нужно создать/обновить)
   - Schema markup (если нужно добавить)

4. **Контентные рекомендации:**
   - Какие страницы требуют переписывания
   - Какие элементы добавить (статистика, определения)
   - Какие FAQ-секции создать

### 3.3 Специфичная логика

**Уровни оптимизации:**

1. **Minimal (быстрая оптимизация, 5-10 минут на страницу):**
   - Только правило первых 50 слов
   - Проверка robots.txt
   - Базовый llms.txt

2. **Standard (стандартная оптимизация, 15-20 минут на страницу):**
   - Правило первых 50 слов
   - Оптимизация структуры (заголовки, списки)
   - FAQPage schema
   - llms.txt
   - robots.txt

3. **Aggressive (глубокая оптимизация, 30-40 минут на страницу):**
   - Всё из Standard
   - Добавление цитируемых элементов (статистика, определения)
   - Создание FAQ-секций
   - Оптимизация изображений (alt text)
   - Анализ конкурентов

**Приоритизация страниц:**

Если передано много URL, оптимизировать в порядке приоритета:
1. Главная страница
2. Продуктовые страницы (услуги, товары)
3. Популярные статьи блога (по трафику)
4. Лендинги
5. Остальные страницы

---

## 4. ВЫХОДНЫЕ ДАННЫЕ

### 4.1 Формат результата

```python
class GEOOptimizationResult(BaseModel):
    summary: GEOOptimizationSummary
    pages: list[OptimizedPage]
    technical_recommendations: TechnicalRecommendations
    content_recommendations: ContentRecommendations
    llms_txt_content: str  # Сгенерированный llms.txt
    schema_markup: dict  # Сгенерированный FAQPage schema
```

### 4.2 Структура данных

**GEOOptimizationSummary:**
```python
class GEOOptimizationSummary(BaseModel):
    total_pages: int
    optimized_pages: int
    average_geo_score_before: float
    average_geo_score_after: float
    improvement_percentage: float
    optimization_level: str
    execution_time_minutes: float
```

**OptimizedPage:**
```python
class OptimizedPage(BaseModel):
    url: str
    geo_score_before: int  # 0-100
    geo_score_after: int  # 0-100
    improvements: list[str]  # Список улучшений
    recommendations: list[str]  # Что ещё нужно сделать
    optimized_content: str  # Оптимизированный HTML
    first_50_words_before: str
    first_50_words_after: str
```

**TechnicalRecommendations:**
```python
class TechnicalRecommendations(BaseModel):
    robots_txt_issues: list[str]
    llms_txt_created: bool
    schema_markup_added: bool
    ai_bots_blocked: list[str]  # Список заблокированных ботов
```

**ContentRecommendations:**
```python
class ContentRecommendations(BaseModel):
    pages_need_rewrite: list[str]  # URL страниц для переписывания
    missing_faq_sections: list[str]  # URL страниц без FAQ
    missing_statistics: list[str]  # URL страниц без статистики
    missing_definitions: list[str]  # URL страниц без определений
```

### 4.3 Сохранение результатов

**Obsidian vault:**
- `wiki/optimizations/` — отчёты по оптимизациям
- `wiki/recommendations/` — рекомендации по улучшению

**База данных:**
- Таблица `geo_optimizations` — история оптимизаций
- Таблица `geo_scores` — GEO Score по страницам (для трекинга динамики)

**Event Bus:**
- Событие `geo.optimization.completed` с результатами

---

## 5. МЕТРИКИ УСПЕХА

### 5.1 KPI агента

**Основные метрики:**

1. **GEO Score Improvement:**
   - Средний прирост GEO Score: > +20 баллов
   - Процент страниц с GEO Score > 80: > 60%
   - Процент страниц с GEO Score > 60: > 90%

2. **Execution Performance:**
   - Success rate: > 95%
   - Execution time: < 20 минут на страницу (standard level)
   - Error rate: < 5%

3. **Technical Implementation:**
   - llms.txt created: 100% (если не существует)
   - FAQPage schema added: > 80% страниц
   - robots.txt fixed: 100% (если были проблемы)

4. **Content Quality:**
   - First 50 words optimized: 100% страниц
   - FAQ sections added: > 60% страниц
   - Citation elements added: > 40% страниц

### 5.2 Бизнес-метрики

**Отслеживаются GEO Monitoring Agent:**

1. **AI Visibility:**
   - Brand mention frequency в ChatGPT/Perplexity: +40% за 3 месяца
   - AI share of voice: > 20% в нише
   - Citation rate: > 30% запросов

2. **Traffic Impact:**
   - Трафик из AI-источников: +50% за 6 месяцев
   - Conversion rate из AI: 4x выше органического поиска
   - Registrations из AI: 10x чаще

3. **Competitive Position:**
   - Упоминаний больше, чем у конкурентов: > 2x
   - Позиция в AI-ответах: Top 3 источника

### 5.3 Дашборд метрик

**Real-time метрики:**
- Количество оптимизированных страниц сегодня
- Средний GEO Score (до/после)
- Количество созданных llms.txt файлов
- Количество добавленных FAQPage schema

**Исторические метрики:**
- Динамика GEO Score по неделям
- Количество оптимизаций в месяц
- Топ-10 страниц по GEO Score
- Топ-10 страниц по приросту GEO Score

**Алерты:**
- GEO Score < 40 после оптимизации → Warning
- Execution time > 30 минут на страницу → Warning
- Error rate > 10% → Critical
- AI боты заблокированы в robots.txt → Critical

---

## 6. КОММУНИКАЦИЯ

### 6.1 Event Bus

**Подписки (входящие события):**

```python
# Запрос на оптимизацию от SEO Magister
{
  "event_type": "seo.geo_optimization.requested",
  "payload": {
    "urls": ["https://example.com/page1", "https://example.com/page2"],
    "optimization_level": "standard",
    "priority": "high"
  }
}

# Запрос на оптимизацию от Content Magister
{
  "event_type": "content.published",
  "payload": {
    "url": "https://example.com/new-article",
    "content_type": "article",
    "auto_optimize": true
  }
}
```

**Публикации (исходящие события):**

```python
# Оптимизация завершена
{
  "event_type": "geo.optimization.completed",
  "payload": {
    "urls": ["https://example.com/page1"],
    "geo_score_before": 45,
    "geo_score_after": 78,
    "improvements": ["first_50_words", "faq_section", "schema_markup"],
    "execution_time_minutes": 18.5
  }
}

# Оптимизация не удалась
{
  "event_type": "geo.optimization.failed",
  "payload": {
    "url": "https://example.com/page1",
    "error": "PAGE_NOT_ACCESSIBLE",
    "retry_count": 3
  }
}

# Технические проблемы обнаружены
{
  "event_type": "geo.technical_issues.detected",
  "payload": {
    "issues": ["ai_bots_blocked", "no_llms_txt"],
    "severity": "high",
    "recommendations": ["unblock_gptbot", "create_llms_txt"]
  }
}
```

### 6.2 Эскалация

**Уровни эскалации:**

1. **Info** — информационные события:
   - Оптимизация завершена успешно
   - GEO Score улучшен
   - llms.txt создан

2. **Warning** — предупреждения:
   - GEO Score < 60 после оптимизации
   - Execution time > 25 минут
   - Некоторые рекомендации не применены

3. **Critical** — критичные проблемы:
   - AI боты заблокированы в robots.txt
   - Страница недоступна для оптимизации
   - Error rate > 10%
   - GEO Score < 40 после оптимизации

**Эскалация к SEO Magister:**
- При Critical уровне → немедленная эскалация
- При Warning уровне → эскалация через 1 час (если не исправлено)
- При Info уровне → только логирование

### 6.3 Obsidian Integration

**Структура vault:**

```
obsidian/geo-optimization-agent/
├── raw/
│   └── pages/                    # Исходный HTML страниц
├── wiki/
│   ├── index.md                  # Каталог оптимизаций
│   ├── log.md                    # Хронология операций
│   ├── optimizations/            # Отчёты по оптимизациям
│   │   ├── 2026-05-10-page1.md
│   │   └── 2026-05-10-page2.md
│   ├── recommendations/          # Рекомендации
│   │   └── 2026-05-10-technical.md
│   ├── scores/                   # История GEO Score
│   │   └── 2026-05-10-scores.md
│   └── llms-txt/                 # Сгенерированные llms.txt
│       └── example-com.md
└── decisions/
    └── optimization-strategies.md
```

**Формат записи в log.md:**

```markdown
## [2026-05-10 18:30] optimization_completed | Page optimized: example.com/page1

**Input:**
- URL: https://example.com/page1
- Optimization level: standard

**Output:**
- GEO Score: 45 → 78 (+33)
- Improvements: first_50_words, faq_section, schema_markup
- Execution time: 18.5 minutes

**Status:** ✅ Success
```

### 6.4 Формат данных

**JSON для Event Bus:**
- Все события в JSON формате
- Стандартные поля: event_type, timestamp, correlation_id, payload

**Markdown для Obsidian:**
- Отчёты по оптимизациям в Markdown
- Рекомендации в Markdown
- История GEO Score в Markdown (таблицы)

**Обоснование гибридного подхода:**
- JSON для координации между агентами (Event Bus)
- Markdown для памяти и обучения (Obsidian)
- JSON легко парсится программно
- Markdown легко читается человеком и LLM

---

## 7. ОБРАБОТКА ОШИБОК

### 7.1 Общие ошибки

**NETWORK_ERROR:**
- Причина: Сеть недоступна, таймаут
- Действие: Retry 3 раза с exponential backoff (5, 10, 20 секунд)
- Эскалация: Warning (если > 3 попыток)

**INVALID_INPUT:**
- Причина: Невалидные входные данные
- Действие: Вернуть ошибку с описанием проблемы
- Retry: Нет
- Эскалация: Info

**RATE_LIMIT_EXCEEDED:**
- Причина: Превышен лимит запросов к внешнему API
- Действие: Подождать указанное время (Retry-After header)
- Retry: Да, после ожидания
- Эскалация: Warning

### 7.2 Специфичные ошибки

**PAGE_NOT_ACCESSIBLE:**
- Причина: Страница недоступна (404, 403, 500)
- Действие:
  1. Проверить URL (может быть опечатка)
  2. Retry 3 раза с интервалом 10 секунд
  3. Если не помогло → пропустить страницу
  4. Добавить в рекомендации "проверить доступность страницы"
- Retry: 3 попытки
- Эскалация: Warning

**AI_BOTS_BLOCKED:**
- Причина: GPTBot, ClaudeBot или PerplexityBot заблокированы в robots.txt
- Действие:
  1. Добавить в рекомендации "разблокировать AI ботов"
  2. Показать, какие именно боты заблокированы
  3. Предложить исправленный robots.txt
- Retry: Нет (требуется ручное исправление)
- Эскалация: Critical

**CONTENT_TOO_SHORT:**
- Причина: Контент страницы < 100 слов (недостаточно для оптимизации)
- Действие:
  1. Пропустить оптимизацию
  2. Добавить в рекомендации "увеличить объём контента"
  3. Минимум рекомендуемый: 500+ слов
- Retry: Нет
- Эскалация: Info

**SCHEMA_MARKUP_INVALID:**
- Причина: Существующий schema markup невалиден
- Действие:
  1. Попытаться исправить автоматически
  2. Если не получается → добавить в рекомендации
  3. Показать ошибки валидации
- Retry: Нет
- Эскалация: Warning

**OPTIMIZATION_FAILED:**
- Причина: Не удалось улучшить GEO Score (остался < 40)
- Действие:
  1. Проанализировать причины (контент слишком короткий, нет структуры)
  2. Добавить детальные рекомендации
  3. Предложить переписать контент с нуля
- Retry: Нет
- Эскалация: Warning

### 7.3 Retry стратегия

**Exponential backoff:**
```python
def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except RetryableError as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 5 * (2 ** attempt)  # 5, 10, 20 секунд
            time.sleep(wait_time)
```

**Retry только для:**
- NETWORK_ERROR
- RATE_LIMIT_EXCEEDED
- PAGE_NOT_ACCESSIBLE (временные проблемы)

**Не retry для:**
- INVALID_INPUT (требуется исправление входных данных)
- AI_BOTS_BLOCKED (требуется ручное исправление robots.txt)
- CONTENT_TOO_SHORT (требуется добавление контента)

### 7.4 Graceful degradation

**Если не удалось выполнить полную оптимизацию:**

1. **Minimal fallback:**
   - Применить только правило первых 50 слов
   - Проверить robots.txt
   - Вернуть partial_success

2. **Partial success:**
   - Выполнить то, что получилось
   - Вернуть список того, что не удалось
   - Добавить рекомендации по исправлению

3. **Complete failure:**
   - Вернуть detailed error report
   - Добавить в рекомендации "обратиться к разработчику"
   - Эскалация к SEO Magister

---

## 8. ТЕСТИРОВАНИЕ

### 8.1 Unit тесты

**Тестируемые компоненты:**

1. **Парсинг контента:**
   - Извлечение заголовков
   - Извлечение первых 50 слов
   - Извлечение списков и таблиц
   - Извлечение schema markup

2. **Оптимизация контента:**
   - Применение правила первых 50 слов
   - Генерация FAQ-секций
   - Добавление цитируемых элементов

3. **Генерация структурированных данных:**
   - FAQPage schema
   - llms.txt
   - robots.txt проверка

4. **Расчёт GEO Score:**
   - Правильность расчёта (0-100)
   - Учёт всех компонентов
   - Граничные случаи

**Пример теста:**

```python
def test_first_50_words_optimization():
    # Arrange
    original_content = "В этой статье мы рассмотрим..."
    expected_optimized = "Медицинский маркетинг — это комплекс..."
    
    # Act
    optimized = optimize_first_50_words(original_content, topic="медицинский маркетинг")
    
    # Assert
    assert len(optimized.split()) <= 100
    assert "медицинский маркетинг" in optimized.lower()
    assert optimized.startswith("Медицинский маркетинг")
```

### 8.2 Integration тесты

**Тестируемые сценарии:**

1. **End-to-end оптимизация:**
   - Получить URL
   - Извлечь контент
   - Оптимизировать
   - Сгенерировать отчёт
   - Проверить GEO Score

2. **Event Bus интеграция:**
   - Получить событие `seo.geo_optimization.requested`
   - Выполнить оптимизацию
   - Отправить событие `geo.optimization.completed`

3. **Obsidian интеграция:**
   - Сохранить отчёт в vault
   - Обновить log.md
   - Проверить структуру файлов

**Пример теста:**

```python
async def test_end_to_end_optimization():
    # Arrange
    url = "https://example.com/test-page"
    optimization_input = GEOOptimizationInput(
        urls=[url],
        optimization_level="standard",
        brand_name="Test Brand",
        industry="healthcare"
    )
    
    # Act
    result = await geo_optimization_agent.optimize(optimization_input)
    
    # Assert
    assert result.summary.optimized_pages == 1
    assert result.pages[0].geo_score_after > result.pages[0].geo_score_before
    assert result.llms_txt_content is not None
    assert len(result.schema_markup) > 0
```

### 8.3 E2E тесты

**Тестируемые workflow:**

1. **Полный цикл оптимизации:**
   - SEO Magister запрашивает оптимизацию
   - GEO Optimization Agent выполняет
   - GEO Monitoring Agent проверяет результат
   - Отчёт отправляется пользователю

2. **Оптимизация нового контента:**
   - Content Magister публикует статью
   - GEO Optimization Agent автоматически оптимизирует
   - Результат сохраняется в Obsidian

3. **Обработка ошибок:**
   - Страница недоступна
   - Retry 3 раза
   - Эскалация к SEO Magister
   - Уведомление пользователя

**Пример теста:**

```python
async def test_full_optimization_workflow():
    # Arrange
    seo_magister = SEOMagister()
    geo_optimization_agent = GEOOptimizationAgent()
    
    # Act
    await seo_magister.request_geo_optimization(
        urls=["https://example.com/page1"],
        priority="high"
    )
    
    # Wait for completion
    result = await wait_for_event("geo.optimization.completed", timeout=60)
    
    # Assert
    assert result["payload"]["geo_score_after"] > 60
    assert "first_50_words" in result["payload"]["improvements"]
```

### 8.4 Performance тесты

**Метрики производительности:**

1. **Execution time:**
   - Minimal level: < 10 минут на страницу
   - Standard level: < 20 минут на страницу
   - Aggressive level: < 40 минут на страницу

2. **Throughput:**
   - Параллельная оптимизация: 5 страниц одновременно
   - Throughput: > 15 страниц в час (standard level)

3. **Memory usage:**
   - < 500 MB на страницу
   - < 2 GB для 10 страниц параллельно

**Пример теста:**

```python
async def test_optimization_performance():
    # Arrange
    urls = [f"https://example.com/page{i}" for i in range(10)]
    start_time = time.time()
    
    # Act
    results = await geo_optimization_agent.optimize_batch(urls, level="standard")
    
    # Assert
    execution_time = time.time() - start_time
    assert execution_time < 200  # < 20 минут на страницу * 10 страниц
    assert all(r.geo_score_after > r.geo_score_before for r in results)
```

---


---

## 9. Примеры использования

### 9.1 Базовый сценарий

```python
from aim.subagents.geo_optimization_agent import GEOOptimizationAgent

# Инициализация агента
agent = GEOOptimizationAgent(
    vault_path="AIM/obsidian/geo-optimization-agent",
    event_bus=event_bus
)

# Оптимизация страницы
result = await agent.optimize_page(
    url="https://iamaim.ru/blog/medical-marketing-guide",
    optimization_level="standard",
    target_keywords=["медицинский маркетинг", "привлечение пациентов"]
)

print(f"GEO Score: {result.geo_score}/100")
print(f"Recommendations: {len(result.recommendations)}")
```

### 9.2 Пакетная оптимизация

```python
# Оптимизация нескольких страниц
urls = [
    "https://iamaim.ru/blog/seo-for-clinics",
    "https://iamaim.ru/blog/content-marketing",
    "https://iamaim.ru/blog/paid-ads"
]

results = await agent.optimize_batch(
    urls=urls,
    optimization_level="aggressive",
    parallel=True,
    max_workers=3
)

# Агрегация результатов
avg_score = sum(r.geo_score for r in results) / len(results)
print(f"Average GEO Score: {avg_score:.1f}/100")
```

### 9.3 Интеграция с Content Magister

```python
# Content Magister запрашивает оптимизацию
await event_bus.publish(Event(
    type="geo.optimization.requested",
    source="content-magister",
    data={
        "url": "https://iamaim.ru/blog/new-article",
        "optimization_level": "standard",
        "target_keywords": ["медицинский маркетинг"],
        "correlation_id": "cm-2024-001"
    }
))

# GEO Agent обрабатывает и отвечает
# Event: geo.optimization.completed
```

### 9.4 Мониторинг изменений

```python
# Проверка изменений после оптимизации
before = await agent.analyze_page(url)
await agent.apply_recommendations(url, recommendations)
after = await agent.analyze_page(url)

improvement = after.geo_score - before.geo_score
print(f"GEO Score improvement: +{improvement} points")
```

---

## 10. Зависимости

### 10.1 Внешние зависимости

**Python библиотеки:**
```python
# requirements.txt
beautifulsoup4>=4.12.0    # HTML parsing
lxml>=5.0.0               # XML/HTML processing
playwright>=1.40.0        # Browser automation
aiohttp>=3.9.0           # Async HTTP client
pydantic>=2.5.0          # Data validation
```

**Внешние API:**
- **Нет обязательных внешних API** — агент работает автономно
- **Опционально:** GEO Tracker AI API (для расширенной аналитики)

**Браузер:**
- Playwright (Chromium) для рендеринга JavaScript

### 10.2 Внутренние зависимости

**Framework компоненты:**
```python
from meai.agents.base_agent import BaseAgent
from meai.events.event_bus import EventBus
from meai.memory.obsidian import ObsidianVault
from meai.storage.database import Database
```

**Связанные агенты:**
- **Content Magister** — запрашивает оптимизацию контента
- **SEO Magister** — координирует SEO стратегию
- **Keyword Research Agent** — предоставляет целевые ключевые слова
- **Web Analytics Agent** — предоставляет метрики трафика

**Obsidian vault:**
- `AIM/obsidian/geo-optimization-agent/` — хранилище знаний агента

**База данных:**
- Таблица `geo_optimizations` — история оптимизаций
- Таблица `geo_scores` — динамика GEO Score

---

## 11. Deployment

### 11.1 Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Установка Playwright
RUN pip install playwright && \
    playwright install chromium && \
    playwright install-deps

# Копирование кода
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Запуск агента
CMD ["python", "-m", "aim.subagents.geo_optimization_agent"]
```

### 11.2 Конфигурация

```yaml
# config/geo_optimization_agent.yaml
agent:
  name: "GEO Optimization Agent"
  vault_path: "AIM/obsidian/geo-optimization-agent"
  
optimization:
  default_level: "standard"
  max_parallel_pages: 5
  timeout_seconds: 60
  
scoring:
  first_50_words_weight: 0.20
  content_structure_weight: 0.30
  citation_elements_weight: 0.30
  technical_readiness_weight: 0.20
  
ai_bots:
  - "GPTBot"
  - "ClaudeBot"
  - "PerplexityBot"
  - "Google-Extended"
  
monitoring:
  check_interval_hours: 24
  alert_threshold_drop: 10  # Alert if GEO Score drops >10 points
```

### 11.3 Мониторинг

**Метрики для Prometheus:**
```python
# Метрики агента
geo_optimizations_total = Counter('geo_optimizations_total', 'Total optimizations')
geo_score_gauge = Gauge('geo_score', 'Current GEO Score', ['url'])
optimization_duration = Histogram('optimization_duration_seconds', 'Optimization duration')
```

**Алерты:**
```yaml
# alerts.yaml
- alert: GEOScoreDropped
  expr: geo_score < 60
  for: 1h
  annotations:
    summary: "GEO Score dropped below 60"
    
- alert: OptimizationFailed
  expr: rate(geo_optimizations_failed_total[5m]) > 0.1
  annotations:
    summary: "High optimization failure rate"
```

### 11.4 Логирование

```python
# Структурированное логирование
logger.info(
    "optimization_completed",
    extra={
        "url": url,
        "geo_score": result.geo_score,
        "optimization_level": level,
        "duration_seconds": duration,
        "recommendations_count": len(result.recommendations)
    }
)
```

---

## 12. Changelog

### Version 1.0.0 (2026-05-10)

**Создана спецификация:**
- ✅ Базовая архитектура агента
- ✅ Алгоритм оптимизации (8 шагов)
- ✅ GEO Score методология (0-100)
- ✅ Три уровня оптимизации (minimal, standard, aggressive)
- ✅ Интеграция с Event Bus
- ✅ Obsidian vault структура
- ✅ Метрики и KPI
- ✅ Обработка ошибок
- ✅ Тестирование (unit, integration, e2e)

**Основано на исследовании:**
- Правило первых 50 слов (44.2% цитирований)
- FAQPage schema для структурированных данных
- llms.txt для AI-краулеров
- Citation engineering паттерны
- Статистика: 900M ChatGPT users/week, 1B+ Perplexity queries/month

---

## 13. Исследования и TODO

### 13.1 Приоритет 1: MVP (Фаза 1)

**Базовая функциональность:**
- ✅ Анализ первых 50 слов
- ✅ Проверка структуры контента (H1-H6, списки)
- ✅ Валидация FAQPage schema
- ✅ Проверка robots.txt для AI-ботов
- ✅ GEO Score расчёт (0-100)

**Требуется реализация:**
- [ ] Playwright интеграция для рендеринга JavaScript
- [ ] Парсинг Schema.org разметки
- [ ] Генерация рекомендаций по оптимизации
- [ ] Сохранение результатов в Obsidian vault

### 13.2 Приоритет 2: Расширенная аналитика (Фаза 2)

**Мониторинг упоминаний бренда:**
- [ ] Интеграция с ChatGPT API (если доступно)
- [ ] Интеграция с Perplexity API (если доступно)
- [ ] Парсинг публичных AI-ответов
- [ ] Отслеживание Share of Voice

**Конкурентный анализ:**
- [ ] Сравнение GEO Score с конкурентами
- [ ] Анализ источников цитирований конкурентов
- [ ] Benchmark по индустрии

### 13.3 Приоритет 3: Автоматизация (Фаза 3)

**Автоматическая оптимизация:**
- [ ] Генерация оптимизированных первых 50 слов
- [ ] Автоматическое создание FAQPage schema
- [ ] Генерация llms.txt файла
- [ ] A/B тестирование вариантов контента

**Интеграция с CMS:**
- [ ] WordPress plugin для автоматической оптимизации
- [ ] API для интеграции с другими CMS
- [ ] Webhook для уведомлений об изменениях

### 13.4 Исследовательские задачи

**TODO для изучения:**

1. **GEO Tracker AI API**
   - Документация: https://geotracker.ai/docs
   - Стоимость: $99/месяц (до 1000 проверок)
   - Функции: мониторинг упоминаний, Share of Voice, конкурентный анализ
   - Приоритет: Фаза 2

2. **ChatGPT Search API**
   - Статус: Пока недоступно публично
   - Альтернатива: Парсинг публичных ответов через Playwright
   - Приоритет: Фаза 2

3. **Perplexity API**
   - Статус: Закрытая beta
   - Альтернатива: Парсинг публичных ответов
   - Приоритет: Фаза 2

4. **Reddit API для GEO**
   - Документация: https://www.reddit.com/dev/api
   - Стоимость: Бесплатно (до 100 запросов/минуту)
   - Функции: поиск упоминаний бренда, анализ контекста
   - Приоритет: Фаза 2

5. **Wikipedia API**
   - Документация: https://www.mediawiki.org/wiki/API
   - Стоимость: Бесплатно
   - Функции: проверка наличия упоминаний, анализ контекста
   - Приоритет: Фаза 2

### 13.5 Метрики для исследования

**Вопросы для валидации:**
- Какой минимальный GEO Score для попадания в AI-ответы?
- Как часто AI-модели обновляют индекс?
- Какие факторы влияют на выбор источника для цитирования?
- Как измерить ROI от GEO оптимизации?

**Эксперименты:**
- A/B тест: оптимизированная vs неоптимизированная страница
- Корреляция GEO Score и частоты цитирований
- Влияние FAQPage schema на видимость в AI

---

## Приложение A: Статистика и исследования

### A.1 Ключевые метрики GEO (2024-2026)

**Рост AI-поиска:**
- ChatGPT: 900M пользователей/неделю (2024)
- Perplexity: 1B+ запросов/месяц (2024)
- Google AI Overviews: 1B+ пользователей (2024)

**Эффективность оптимизации:**
- +40% видимость после GEO оптимизации
- 44.2% цитирований из первых 30% текста
- 85% цитирований из доменов, которыми вы не владеете

**Источники цитирований:**
- Reddit: 46.7% источников Perplexity
- Wikipedia: 47.9% источников ChatGPT
- Новостные сайты: 15-20% источников
- Блоги и форумы: 10-15% источников

### A.2 Лучшие практики

**Правило первых 50 слов:**
- Включить целевые ключевые слова
- Дать чёткий ответ на вопрос
- Использовать цифры и факты
- Избегать вводных фраз

**FAQPage schema:**
- Минимум 3-5 вопросов
- Чёткие, короткие ответы (50-150 слов)
- Использовать естественный язык
- Включать целевые ключевые слова

**llms.txt:**
```
# iamaim.ru

## About
AI-first medical marketing agency specializing in patient acquisition.

## Services
- Medical SEO
- Content Marketing
- Paid Advertising
- Analytics & Reporting

## Contact
Email: hello@iamaim.ru
```

### A.3 Инструменты для GEO

**Бесплатные:**
- Schema.org Validator
- Google Rich Results Test
- Lighthouse (PageSpeed Insights)

**Платные:**
- GEO Tracker AI ($99/мес) — мониторинг упоминаний
- Semrush ($119/мес) — конкурентный анализ
- Ahrefs ($99/мес) — анализ обратных ссылок

---

**Дата создания:** 2026-05-10 21:30 GMT+3  
**Автор:** Mikhail Eliseev (via meAI Architect)  
**Версия:** 1.0.0  
**Статус:** ✅ Готов к реализации  
**Размер:** ~1500 строк, ~45 KB

