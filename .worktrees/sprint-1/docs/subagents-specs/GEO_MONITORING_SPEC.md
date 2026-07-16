# GEO Monitoring Agent — Спецификация

**Версия:** 1.0.0  
**Дата создания:** 2026-05-10  
**Родительский Magister:** SEO Magister  
**Приоритет:** P1 (критичный для AI-эпохи)

---

## 1. Обзор

### 1.1 Назначение

**GEO Monitoring Agent** — автономный агент для непрерывного мониторинга видимости бренда в AI-поисковых системах (ChatGPT, Perplexity, Claude, Google AI Overviews).

**Ключевая задача:** Отслеживать упоминания бренда, измерять Share of Voice, детектировать изменения в цитированиях и алертить о критических событиях.

### 1.2 Роль в системе

**GEO Monitoring Agent** — это "радар" для AI-видимости:
- Мониторит упоминания бренда в AI-ответах 24/7
- Измеряет Share of Voice vs конкуренты
- Детектирует появление/исчезновение из AI-ответов
- Отслеживает источники цитирований
- Алертит о критических изменениях

**Отличие от Web Analytics Agent:**
- Web Analytics → трафик на сайт (прошлое)
- GEO Monitoring → видимость в AI (настоящее и будущее)

### 1.3 Уникальная ценность

**Почему это критично:**
1. **AI-поиск растёт экспоненциально** — 900M ChatGPT users/week, 1B+ Perplexity queries/month
2. **85% цитирований из чужих доменов** — нужно знать, где упоминают бренд
3. **Раннее обнаружение проблем** — если бренд исчез из AI-ответов, нужно знать немедленно
4. **Конкурентная разведка** — кто доминирует в AI-ответах по вашим темам

**Метрика успеха:** Обнаружение изменений в AI-видимости за < 24 часа.

### 1.4 Границы ответственности

**Что делает:**
- ✅ Мониторит упоминания бренда в AI-ответах
- ✅ Измеряет Share of Voice (% упоминаний vs конкуренты)
- ✅ Отслеживает источники цитирований (Reddit, Wikipedia, блоги)
- ✅ Детектирует изменения в позициях
- ✅ Алертит о критических событиях
- ✅ Генерирует еженедельные отчёты

**Что НЕ делает:**
- ❌ Не оптимизирует контент (это GEO Optimization Agent)
- ❌ Не создаёт контент (это GEO Content Agent)
- ❌ Не анализирует традиционный SEO (это Search Console Agent)
- ❌ Не мониторит веб-трафик (это Web Analytics Agent)

**Backlog (будущие фичи):**
- Sentiment analysis упоминаний бренда
- Автоматическое реагирование на негативные упоминания
- Прогнозирование трендов AI-видимости
- Интеграция с социальными сетями

### 1.5 Связанные агенты

**Координация с другими агентами:**

| Агент | Взаимодействие | Формат данных |
|-------|----------------|---------------|
| **GEO Optimization Agent** | Получает алерты о падении видимости → запрашивает оптимизацию | Event Bus (JSON) |
| **GEO Content Agent** | Получает данные о популярных темах → запрашивает контент | Event Bus (JSON) |
| **SEO Magister** | Отчитывается о GEO метриках | Event Bus (JSON) |
| **Keyword Research Agent** | Получает список целевых запросов для мониторинга | Event Bus (JSON) |
| **Competitor Analysis Agent** | Получает данные о конкурентах для сравнения | Event Bus (JSON) |

**Отличия от похожих агентов:**

| Критерий | GEO Monitoring | Web Analytics | Search Console |
|----------|----------------|---------------|----------------|
| **Источник данных** | AI-поисковики | Google Analytics | Google Search Console |
| **Метрики** | Share of Voice, упоминания | Трафик, конверсии | Позиции, клики |
| **Временной горизонт** | Реал-тайм (24ч) | Исторический | Исторический |
| **Фокус** | AI-видимость | Поведение пользователей | Традиционный SEO |

---

## 2. Входные данные

### 2.1 Источники данных

**Обязательные источники:**
1. **Целевые запросы** (от Keyword Research Agent)
2. **Список конкурентов** (от Competitor Analysis Agent)
3. **Бренд-термины** (из конфигурации проекта)

**Опциональные источники:**
4. **GEO Tracker AI API** (платный, $99/мес)
5. **Публичные AI-ответы** (парсинг через Playwright)

### 2.2 Обязательные параметры

```python
class MonitoringConfig(BaseModel):
    """Конфигурация мониторинга"""
    
    # Бренд
    brand_name: str  # "iamaim.ru"
    brand_aliases: list[str]  # ["AIM", "AI Marketing", "iamaim"]
    
    # Целевые запросы
    target_queries: list[str]  # ["медицинский маркетинг", "SEO для клиник"]
    
    # Конкуренты
    competitors: list[str]  # ["competitor1.ru", "competitor2.ru"]
    
    # Частота проверок
    check_interval_hours: int = 24  # Каждые 24 часа
    
    # Алерты
    alert_threshold_drop: int = 20  # Алерт если Share of Voice упал >20%
```

### 2.3 Опциональные параметры

```python
class AdvancedMonitoringConfig(BaseModel):
    """Расширенная конфигурация"""
    
    # AI-платформы для мониторинга
    platforms: list[str] = ["chatgpt", "perplexity", "claude", "google_ai"]
    
    # Источники цитирований
    citation_sources: list[str] = ["reddit", "wikipedia", "blogs", "news"]
    
    # Sentiment analysis
    enable_sentiment: bool = False
    
    # Webhook для алертов
    webhook_url: Optional[str] = None
```

### 2.4 Валидация входных данных

```python
async def validate_config(self, config: MonitoringConfig) -> ValidationResult:
    """Валидация конфигурации мониторинга"""
    
    errors = []
    
    # Проверка бренда
    if not config.brand_name:
        errors.append("brand_name is required")
    
    # Проверка запросов
    if not config.target_queries:
        errors.append("target_queries is required (min 1)")
    
    if len(config.target_queries) > 100:
        errors.append("target_queries: max 100 queries allowed")
    
    # Проверка конкурентов
    if len(config.competitors) > 20:
        errors.append("competitors: max 20 competitors allowed")
    
    # Проверка интервала
    if config.check_interval_hours < 1:
        errors.append("check_interval_hours: min 1 hour")
    
    if config.check_interval_hours > 168:  # 7 дней
        errors.append("check_interval_hours: max 168 hours (7 days)")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors
    )
```

---

## 3. Алгоритм работы

### 3.1 Общая схема

```
1. Получить конфигурацию мониторинга
2. Для каждого целевого запроса:
   a. Выполнить запрос в AI-платформах
   b. Извлечь упоминания бренда и конкурентов
   c. Определить источники цитирований
   d. Рассчитать Share of Voice
3. Сравнить с предыдущими результатами
4. Детектировать изменения
5. Генерировать алерты (если нужно)
6. Сохранить результаты в Obsidian + БД
7. Отправить отчёт через Event Bus
```

### 3.2 Детальные шаги

#### Шаг 1: Выполнение запросов в AI-платформах

```python
async def query_ai_platforms(
    self,
    query: str,
    platforms: list[str]
) -> dict[str, AIResponse]:
    """Выполнить запрос во всех AI-платформах"""
    
    results = {}
    
    for platform in platforms:
        try:
            if platform == "chatgpt":
                # Парсинг публичных ответов ChatGPT
                response = await self._query_chatgpt(query)
            
            elif platform == "perplexity":
                # Парсинг Perplexity через Playwright
                response = await self._query_perplexity(query)
            
            elif platform == "claude":
                # Парсинг Claude через Playwright
                response = await self._query_claude(query)
            
            elif platform == "google_ai":
                # Google AI Overviews через Search API
                response = await self._query_google_ai(query)
            
            results[platform] = response
            
        except Exception as e:
            logger.error(f"Failed to query {platform}: {e}")
            results[platform] = None
    
    return results
```

#### Шаг 2: Извлечение упоминаний

```python
async def extract_mentions(
    self,
    response: AIResponse,
    brand_terms: list[str],
    competitors: list[str]
) -> MentionData:
    """Извлечь упоминания бренда и конкурентов"""
    
    text = response.text.lower()
    
    # Поиск упоминаний бренда
    brand_mentions = []
    for term in brand_terms:
        if term.lower() in text:
            # Извлечь контекст (50 слов до и после)
            context = self._extract_context(text, term, window=50)
            brand_mentions.append({
                "term": term,
                "context": context,
                "position": text.index(term.lower())
            })
    
    # Поиск упоминаний конкурентов
    competitor_mentions = []
    for competitor in competitors:
        if competitor.lower() in text:
            context = self._extract_context(text, competitor, window=50)
            competitor_mentions.append({
                "competitor": competitor,
                "context": context,
                "position": text.index(competitor.lower())
            })
    
    return MentionData(
        brand_mentions=brand_mentions,
        competitor_mentions=competitor_mentions,
        total_brand_count=len(brand_mentions),
        total_competitor_count=len(competitor_mentions)
    )
```

#### Шаг 3: Определение источников цитирований

```python
async def extract_citation_sources(
    self,
    response: AIResponse
) -> list[CitationSource]:
    """Извлечь источники цитирований из AI-ответа"""
    
    sources = []
    
    # Парсинг ссылок из ответа
    for link in response.links:
        # Определить тип источника
        source_type = self._classify_source(link.url)
        
        sources.append(CitationSource(
            url=link.url,
            domain=self._extract_domain(link.url),
            type=source_type,  # reddit, wikipedia, blog, news
            title=link.title,
            snippet=link.snippet
        ))
    
    return sources
```

#### Шаг 4: Расчёт Share of Voice

```python
def calculate_share_of_voice(
    self,
    brand_mentions: int,
    competitor_mentions: int
) -> float:
    """Рассчитать Share of Voice (%)"""
    
    total_mentions = brand_mentions + competitor_mentions
    
    if total_mentions == 0:
        return 0.0
    
    share_of_voice = (brand_mentions / total_mentions) * 100
    
    return round(share_of_voice, 2)
```

#### Шаг 5: Детекция изменений

```python
async def detect_changes(
    self,
    current: MonitoringResult,
    previous: MonitoringResult
) -> list[Change]:
    """Детектировать изменения в AI-видимости"""
    
    changes = []
    
    # Изменение Share of Voice
    sov_delta = current.share_of_voice - previous.share_of_voice
    if abs(sov_delta) >= 10:  # Изменение >10%
        changes.append(Change(
            type="share_of_voice",
            metric="Share of Voice",
            old_value=previous.share_of_voice,
            new_value=current.share_of_voice,
            delta=sov_delta,
            severity="critical" if abs(sov_delta) >= 20 else "warning"
        ))
    
    # Появление в новых платформах
    new_platforms = set(current.platforms) - set(previous.platforms)
    if new_platforms:
        changes.append(Change(
            type="new_platform",
            metric="Platform Coverage",
            old_value=len(previous.platforms),
            new_value=len(current.platforms),
            delta=len(new_platforms),
            severity="info",
            details=f"New platforms: {', '.join(new_platforms)}"
        ))
    
    # Исчезновение из платформ
    lost_platforms = set(previous.platforms) - set(current.platforms)
    if lost_platforms:
        changes.append(Change(
            type="lost_platform",
            metric="Platform Coverage",
            old_value=len(previous.platforms),
            new_value=len(current.platforms),
            delta=-len(lost_platforms),
            severity="critical",
            details=f"Lost platforms: {', '.join(lost_platforms)}"
        ))
    
    return changes
```

#### Шаг 6: Генерация алертов

```python
async def generate_alerts(
    self,
    changes: list[Change],
    threshold: int = 20
) -> list[Alert]:
    """Генерировать алерты о критических изменениях"""
    
    alerts = []
    
    for change in changes:
        if change.severity == "critical":
            alerts.append(Alert(
                type=change.type,
                severity="critical",
                message=self._format_alert_message(change),
                timestamp=datetime.now(),
                action_required=True
            ))
    
    return alerts
```


---

## 4. Выходные данные

### 4.1 Структура результата

```python
class MonitoringResult(BaseModel):
    """Результат мониторинга AI-видимости"""
    
    # Метаданные
    timestamp: datetime
    query: str
    platforms: list[str]
    
    # Упоминания
    brand_mentions: int
    competitor_mentions: int
    share_of_voice: float  # %
    
    # Источники цитирований
    citation_sources: list[CitationSource]
    
    # Изменения
    changes: list[Change]
    
    # Алерты
    alerts: list[Alert]
    
    # Детали по платформам
    platform_details: dict[str, PlatformResult]
```

### 4.2 Формат отчёта

```python
class MonitoringReport(BaseModel):
    """Еженедельный отчёт мониторинга"""
    
    # Период
    period_start: datetime
    period_end: datetime
    
    # Агрегированные метрики
    avg_share_of_voice: float
    total_mentions: int
    platform_coverage: int  # Количество платформ
    
    # Топ запросы
    top_queries: list[QueryPerformance]
    
    # Топ источники цитирований
    top_citation_sources: list[CitationSource]
    
    # Тренды
    trends: list[Trend]
    
    # Рекомендации
    recommendations: list[str]
```

### 4.3 Event Bus события

```python
# Событие: мониторинг завершён
await event_bus.publish(Event(
    type="geo.monitoring.completed",
    source="geo-monitoring-agent",
    data={
        "query": "медицинский маркетинг",
        "share_of_voice": 35.5,
        "brand_mentions": 12,
        "competitor_mentions": 22,
        "platforms": ["chatgpt", "perplexity"],
        "changes_detected": 2,
        "alerts_generated": 1
    }
))

# Событие: критический алерт
await event_bus.publish(Event(
    type="geo.monitoring.alert",
    source="geo-monitoring-agent",
    priority="critical",
    data={
        "alert_type": "share_of_voice_drop",
        "query": "SEO для клиник",
        "old_value": 45.0,
        "new_value": 22.0,
        "delta": -23.0,
        "action_required": True,
        "recommended_action": "Request optimization from GEO Optimization Agent"
    }
))
```

---

## 5. Метрики успеха

### 5.1 KPI агента

| Метрика | Целевое значение | Измерение |
|---------|------------------|-----------|
| **Uptime** | > 99% | Процент времени работы |
| **Check Frequency** | Каждые 24ч | Интервал проверок |
| **Detection Latency** | < 24 часа | Время обнаружения изменений |
| **False Positive Rate** | < 5% | Процент ложных алертов |
| **Platform Coverage** | 4/4 платформы | ChatGPT, Perplexity, Claude, Google AI |

### 5.2 Бизнес-метрики

| Метрика | Целевое значение | Описание |
|---------|------------------|----------|
| **Share of Voice** | > 30% | Доля упоминаний бренда vs конкуренты |
| **Platform Presence** | 100% | Присутствие на всех 4 платформах |
| **Citation Sources** | > 10 уникальных | Количество источников цитирований |
| **Alert Response Time** | < 4 часа | Время реакции на критические алерты |

### 5.3 Дашборд метрик

```python
# Grafana dashboard
{
    "title": "GEO Monitoring Dashboard",
    "panels": [
        {
            "title": "Share of Voice Trend",
            "type": "graph",
            "targets": [
                "SELECT share_of_voice FROM monitoring_results WHERE time > now() - 30d"
            ]
        },
        {
            "title": "Platform Coverage",
            "type": "stat",
            "targets": [
                "SELECT COUNT(DISTINCT platform) FROM monitoring_results WHERE time > now() - 1d"
            ]
        },
        {
            "title": "Alerts by Severity",
            "type": "piechart",
            "targets": [
                "SELECT COUNT(*) FROM alerts GROUP BY severity WHERE time > now() - 7d"
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
# Запрос на мониторинг
@event_bus.subscribe("geo.monitoring.requested")
async def handle_monitoring_request(event: Event):
    config = MonitoringConfig(**event.data)
    result = await self.monitor(config)
    await self.publish_result(result)

# Обновление списка конкурентов
@event_bus.subscribe("competitors.updated")
async def handle_competitors_update(event: Event):
    await self.update_competitors(event.data["competitors"])
```

**Публикации (исходящие события):**
```python
# Мониторинг завершён
await event_bus.publish(Event(
    type="geo.monitoring.completed",
    source="geo-monitoring-agent",
    data=result.dict()
))

# Критический алерт
await event_bus.publish(Event(
    type="geo.monitoring.alert",
    source="geo-monitoring-agent",
    priority="critical",
    data=alert.dict()
))

# Еженедельный отчёт
await event_bus.publish(Event(
    type="geo.monitoring.report",
    source="geo-monitoring-agent",
    data=report.dict()
))
```

### 6.2 Эскалация к SEO Magister

**Когда эскалировать:**
1. Share of Voice упал > 20%
2. Бренд исчез из AI-ответов на критичных запросах
3. Конкурент доминирует (Share of Voice > 70%)
4. Технические проблемы (AI-боты заблокированы)

```python
async def escalate_to_magister(self, issue: Issue):
    """Эскалация критичной проблемы к SEO Magister"""
    
    await event_bus.publish(Event(
        type="geo.monitoring.escalation",
        source="geo-monitoring-agent",
        target="seo-magister",
        priority="high",
        data={
            "issue_type": issue.type,
            "severity": "critical",
            "description": issue.description,
            "recommended_actions": issue.recommended_actions,
            "correlation_id": self.correlation_id
        }
    ))
```

### 6.3 Obsidian vault структура

```
AIM/obsidian/geo-monitoring-agent/
├── raw/
│   └── monitoring-results/          # Сырые результаты мониторинга
│       ├── 2024-05-10-chatgpt.json
│       └── 2024-05-10-perplexity.json
├── wiki/
│   ├── index.md                     # Каталог страниц
│   ├── log.md                       # Хронология операций
│   ├── concepts/
│   │   ├── share-of-voice.md       # Концепция Share of Voice
│   │   └── citation-sources.md     # Типы источников цитирований
│   ├── queries/
│   │   ├── medical-marketing.md    # История мониторинга запроса
│   │   └── seo-for-clinics.md
│   ├── platforms/
│   │   ├── chatgpt.md              # Особенности ChatGPT
│   │   ├── perplexity.md           # Особенности Perplexity
│   │   └── google-ai.md            # Особенности Google AI
│   ├── competitors/
│   │   ├── competitor1.md          # Анализ конкурента 1
│   │   └── competitor2.md          # Анализ конкурента 2
│   └── alerts/
│       ├── 2024-05-10-sov-drop.md  # Алерт о падении Share of Voice
│       └── 2024-05-11-platform-loss.md
├── decisions/
│   └── monitoring-strategy.md       # Стратегия мониторинга
└── SCHEMA.md                        # Правила vault
```

### 6.4 Формат данных (JSON + MD)

**JSON для Event Bus:**
```json
{
  "type": "geo.monitoring.completed",
  "source": "geo-monitoring-agent",
  "data": {
    "query": "медицинский маркетинг",
    "share_of_voice": 35.5,
    "brand_mentions": 12,
    "platforms": ["chatgpt", "perplexity"]
  }
}
```

**Markdown для Obsidian:**
```markdown
---
query: медицинский маркетинг
date: 2024-05-10
share_of_voice: 35.5
status: processed
---

# Мониторинг: медицинский маркетинг

## Результаты

- **Share of Voice:** 35.5% (+5.2% за неделю)
- **Упоминания бренда:** 12
- **Упоминания конкурентов:** 22
- **Платформы:** ChatGPT, Perplexity

## Источники цитирований

1. Reddit r/marketing (3 упоминания)
2. Wikipedia "Medical Marketing" (2 упоминания)
3. iamaim.ru/blog (1 упоминание)
```

---

## 7. Обработка ошибок

### 7.1 Общие ошибки

```python
class MonitoringError(Exception):
    """Базовый класс ошибок мониторинга"""
    pass

# Retry стратегия
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type(MonitoringError)
)
async def monitor_with_retry(config: MonitoringConfig):
    return await self.monitor(config)
```

### 7.2 Специфичные ошибки

| Ошибка | Причина | Действие |
|--------|---------|----------|
| `PLATFORM_UNAVAILABLE` | AI-платформа недоступна | Retry через 5 минут, skip если 3 попытки |
| `RATE_LIMIT_EXCEEDED` | Превышен лимит запросов | Wait 1 час, затем retry |
| `PARSING_FAILED` | Не удалось распарсить ответ | Log error, skip query |
| `NO_MENTIONS_FOUND` | Бренд не найден в ответах | Normal case, log info |
| `INVALID_CONFIG` | Некорректная конфигурация | Escalate to SEO Magister |

### 7.3 Graceful degradation

```python
async def monitor_with_fallback(self, config: MonitoringConfig):
    """Мониторинг с fallback стратегией"""
    
    results = {}
    
    # Попытка 1: GEO Tracker AI API (платный)
    try:
        results = await self.monitor_via_api(config)
        return results
    except Exception as e:
        logger.warning(f"API monitoring failed: {e}")
    
    # Попытка 2: Парсинг публичных ответов
    try:
        results = await self.monitor_via_parsing(config)
        return results
    except Exception as e:
        logger.error(f"Parsing monitoring failed: {e}")
    
    # Fallback: Использовать кэшированные данные
    cached = await self.get_cached_results(config.query)
    if cached:
        logger.info("Using cached results")
        return cached
    
    # Последний вариант: Эскалация
    await self.escalate_to_magister(Issue(
        type="monitoring_failed",
        description="All monitoring methods failed",
        severity="critical"
    ))
```

---

## 8. Тестирование

### 8.1 Unit тесты

```python
# tests/unit/test_geo_monitoring_agent.py

async def test_extract_mentions():
    """Тест извлечения упоминаний"""
    agent = GEOMonitoringAgent()
    
    response = AIResponse(
        text="iamaim.ru is a great medical marketing agency. competitor1.ru is also good.",
        links=[]
    )
    
    mentions = await agent.extract_mentions(
        response,
        brand_terms=["iamaim.ru", "iamaim"],
        competitors=["competitor1.ru"]
    )
    
    assert mentions.total_brand_count == 1
    assert mentions.total_competitor_count == 1

async def test_calculate_share_of_voice():
    """Тест расчёта Share of Voice"""
    agent = GEOMonitoringAgent()
    
    sov = agent.calculate_share_of_voice(
        brand_mentions=12,
        competitor_mentions=22
    )
    
    assert sov == 35.29  # 12/(12+22) * 100

async def test_detect_changes():
    """Тест детекции изменений"""
    agent = GEOMonitoringAgent()
    
    current = MonitoringResult(share_of_voice=35.0, platforms=["chatgpt"])
    previous = MonitoringResult(share_of_voice=55.0, platforms=["chatgpt", "perplexity"])
    
    changes = await agent.detect_changes(current, previous)
    
    assert len(changes) == 2  # SOV drop + platform loss
    assert changes[0].severity == "critical"
```

### 8.2 Integration тесты

```python
# tests/integration/test_geo_monitoring_integration.py

async def test_monitoring_workflow():
    """Тест полного workflow мониторинга"""
    
    # Setup
    agent = GEOMonitoringAgent(vault_path="test_vault", event_bus=event_bus)
    
    config = MonitoringConfig(
        brand_name="iamaim.ru",
        brand_aliases=["iamaim"],
        target_queries=["медицинский маркетинг"],
        competitors=["competitor1.ru"],
        check_interval_hours=24
    )
    
    # Execute
    result = await agent.monitor(config)
    
    # Verify
    assert result.share_of_voice >= 0
    assert result.share_of_voice <= 100
    assert len(result.platform_details) > 0
    
    # Check Event Bus
    events = await event_bus.get_events(type="geo.monitoring.completed")
    assert len(events) == 1

async def test_alert_generation():
    """Тест генерации алертов"""
    
    agent = GEOMonitoringAgent(vault_path="test_vault", event_bus=event_bus)
    
    # Simulate SOV drop
    current = MonitoringResult(share_of_voice=20.0)
    previous = MonitoringResult(share_of_voice=45.0)
    
    changes = await agent.detect_changes(current, previous)
    alerts = await agent.generate_alerts(changes, threshold=20)
    
    assert len(alerts) == 1
    assert alerts[0].severity == "critical"
    
    # Check Event Bus
    events = await event_bus.get_events(type="geo.monitoring.alert")
    assert len(events) == 1
```

### 8.3 E2E тесты

```python
# tests/e2e/test_geo_monitoring_e2e.py

async def test_monitoring_to_optimization_flow():
    """Тест E2E: мониторинг → алерт → оптимизация"""
    
    # 1. Мониторинг детектирует падение Share of Voice
    monitoring_agent = GEOMonitoringAgent(vault_path="test_vault", event_bus=event_bus)
    result = await monitoring_agent.monitor(config)
    
    assert result.share_of_voice < 30  # Критичное падение
    
    # 2. Генерируется алерт
    events = await event_bus.get_events(type="geo.monitoring.alert")
    assert len(events) == 1
    
    # 3. GEO Optimization Agent получает запрос
    optimization_events = await event_bus.get_events(type="geo.optimization.requested")
    assert len(optimization_events) == 1
    
    # 4. Оптимизация выполняется
    optimization_agent = GEOOptimizationAgent(vault_path="test_vault", event_bus=event_bus)
    opt_result = await optimization_agent.optimize_page(url=config.url)
    
    assert opt_result.geo_score > 60
```


---

## 9. Примеры использования

### 9.1 Базовый мониторинг

```python
from aim.subagents.geo_monitoring_agent import GEOMonitoringAgent

# Инициализация агента
agent = GEOMonitoringAgent(
    vault_path="AIM/obsidian/geo-monitoring-agent",
    event_bus=event_bus
)

# Запуск мониторинга
config = MonitoringConfig(
    brand_name="iamaim.ru",
    brand_aliases=["iamaim", "AIM"],
    target_queries=["медицинский маркетинг", "SEO для клиник"],
    competitors=["competitor1.ru", "competitor2.ru"],
    check_interval_hours=24
)

result = await agent.monitor(config)

print(f"Share of Voice: {result.share_of_voice}%")
print(f"Brand mentions: {result.brand_mentions}")
print(f"Platforms: {', '.join(result.platforms)}")
```

### 9.2 Непрерывный мониторинг

```python
# Запуск непрерывного мониторинга (каждые 24 часа)
async def continuous_monitoring():
    agent = GEOMonitoringAgent(vault_path="test_vault", event_bus=event_bus)
    
    while True:
        try:
            result = await agent.monitor(config)
            
            # Проверка алертов
            if result.alerts:
                for alert in result.alerts:
                    await agent.handle_alert(alert)
            
            # Ожидание следующей проверки
            await asyncio.sleep(config.check_interval_hours * 3600)
            
        except Exception as e:
            logger.error(f"Monitoring failed: {e}")
            await asyncio.sleep(3600)  # Retry через 1 час

# Запуск в фоне
asyncio.create_task(continuous_monitoring())
```

### 9.3 Генерация еженедельного отчёта

```python
# Генерация отчёта за последние 7 дней
report = await agent.generate_weekly_report(
    period_start=datetime.now() - timedelta(days=7),
    period_end=datetime.now()
)

print(f"Average Share of Voice: {report.avg_share_of_voice}%")
print(f"Total mentions: {report.total_mentions}")
print(f"Platform coverage: {report.platform_coverage}/4")

# Топ запросы
for query in report.top_queries[:5]:
    print(f"- {query.query}: {query.share_of_voice}%")
```

### 9.4 Интеграция с Telegram

```python
# Отправка алертов в Telegram
@event_bus.subscribe("geo.monitoring.alert")
async def send_telegram_alert(event: Event):
    alert = Alert(**event.data)
    
    message = f"""
🚨 GEO Alert: {alert.type}

Query: {alert.query}
Old value: {alert.old_value}%
New value: {alert.new_value}%
Delta: {alert.delta:+.1f}%

Action required: {alert.action_required}
"""
    
    await telegram_bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=message
    )
```

---

## 10. Зависимости

### 10.1 Внешние зависимости

**Python библиотеки:**
```python
# requirements.txt
playwright>=1.40.0        # Browser automation
beautifulsoup4>=4.12.0    # HTML parsing
aiohttp>=3.9.0           # Async HTTP client
pydantic>=2.5.0          # Data validation
schedule>=1.2.0          # Task scheduling
```

**Внешние API (опционально):**
- **GEO Tracker AI API** ($99/мес) — расширенная аналитика
- **Reddit API** (бесплатно) — мониторинг упоминаний на Reddit
- **Wikipedia API** (бесплатно) — проверка упоминаний в Wikipedia

**Браузер:**
- Playwright (Chromium) для парсинга AI-ответов

### 10.2 Внутренние зависимости

**Framework компоненты:**
```python
from meai.agents.base_agent import BaseAgent
from meai.events.event_bus import EventBus
from meai.memory.obsidian import ObsidianVault
from meai.storage.database import Database
```

**Связанные агенты:**
- **GEO Optimization Agent** — получает запросы на оптимизацию при падении Share of Voice
- **GEO Content Agent** — получает данные о популярных темах
- **SEO Magister** — получает отчёты и эскалации
- **Keyword Research Agent** — предоставляет целевые запросы
- **Competitor Analysis Agent** — предоставляет список конкурентов

**Obsidian vault:**
- `AIM/obsidian/geo-monitoring-agent/` — хранилище результатов мониторинга

**База данных:**
- Таблица `geo_monitoring_results` — история мониторинга
- Таблица `geo_alerts` — история алертов
- Таблица `geo_share_of_voice` — динамика Share of Voice

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
CMD ["python", "-m", "aim.subagents.geo_monitoring_agent"]
```

### 11.2 Конфигурация

```yaml
# config/geo_monitoring_agent.yaml
agent:
  name: "GEO Monitoring Agent"
  vault_path: "AIM/obsidian/geo-monitoring-agent"
  
monitoring:
  check_interval_hours: 24
  platforms:
    - chatgpt
    - perplexity
    - claude
    - google_ai
  
alerts:
  threshold_drop: 20  # Alert if Share of Voice drops >20%
  webhook_url: "https://hooks.slack.com/services/..."
  
api:
  geo_tracker_enabled: false
  geo_tracker_api_key: "${GEO_TRACKER_API_KEY}"
  
scheduling:
  enabled: true
  cron: "0 2 * * *"  # Каждый день в 2:00 AM
```

### 11.3 Мониторинг

**Метрики для Prometheus:**
```python
# Метрики агента
monitoring_checks_total = Counter('geo_monitoring_checks_total', 'Total monitoring checks')
share_of_voice_gauge = Gauge('geo_share_of_voice', 'Current Share of Voice', ['query'])
alerts_generated_total = Counter('geo_alerts_generated_total', 'Total alerts generated', ['severity'])
monitoring_duration = Histogram('geo_monitoring_duration_seconds', 'Monitoring duration')
```

**Алерты:**
```yaml
# alerts.yaml
- alert: ShareOfVoiceDropped
  expr: geo_share_of_voice < 20
  for: 1h
  annotations:
    summary: "Share of Voice dropped below 20%"
    
- alert: PlatformLost
  expr: rate(geo_platform_lost_total[5m]) > 0
  annotations:
    summary: "Brand disappeared from AI platform"
    
- alert: MonitoringFailed
  expr: rate(geo_monitoring_checks_failed_total[5m]) > 0.1
  annotations:
    summary: "High monitoring failure rate"
```

### 11.4 Логирование

```python
# Структурированное логирование
logger.info(
    "monitoring_completed",
    extra={
        "query": config.query,
        "share_of_voice": result.share_of_voice,
        "brand_mentions": result.brand_mentions,
        "platforms": result.platforms,
        "duration_seconds": duration,
        "alerts_generated": len(result.alerts)
    }
)
```

### 11.5 Scheduling

```python
# Автоматический запуск мониторинга по расписанию
import schedule

def schedule_monitoring():
    """Настроить расписание мониторинга"""
    
    # Каждый день в 2:00 AM
    schedule.every().day.at("02:00").do(run_monitoring)
    
    # Каждую неделю в понедельник в 9:00 AM (отчёт)
    schedule.every().monday.at("09:00").do(generate_weekly_report)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

# Запуск в фоне
asyncio.create_task(schedule_monitoring())
```

---

## 12. Changelog

### Version 1.0.0 (2026-05-10)

**Создана спецификация:**
- ✅ Базовая архитектура агента
- ✅ Алгоритм мониторинга (6 шагов)
- ✅ Share of Voice расчёт
- ✅ Детекция изменений
- ✅ Генерация алертов
- ✅ Интеграция с Event Bus
- ✅ Obsidian vault структура
- ✅ Метрики и KPI
- ✅ Обработка ошибок
- ✅ Тестирование (unit, integration, e2e)
- ✅ Scheduling для автоматического мониторинга

**Основано на исследовании:**
- 900M ChatGPT users/week
- 1B+ Perplexity queries/month
- 85% цитирований из чужих доменов
- Reddit (46.7% источников Perplexity)
- Wikipedia (47.9% источников ChatGPT)

---

## 13. Исследования и TODO

### 13.1 Приоритет 1: MVP (Фаза 1)

**Базовая функциональность:**
- ✅ Парсинг AI-ответов через Playwright
- ✅ Извлечение упоминаний бренда и конкурентов
- ✅ Расчёт Share of Voice
- ✅ Детекция изменений
- ✅ Генерация алертов

**Требуется реализация:**
- [ ] Playwright интеграция для ChatGPT, Perplexity, Claude
- [ ] Извлечение источников цитирований
- [ ] Сохранение результатов в Obsidian vault
- [ ] Scheduling для автоматического мониторинга
- [ ] Webhook для алертов (Slack, Telegram)

### 13.2 Приоритет 2: Расширенная аналитика (Фаза 2)

**GEO Tracker AI API:**
- [ ] Интеграция с GEO Tracker AI API ($99/мес)
- [ ] Автоматический мониторинг упоминаний
- [ ] Share of Voice по индустрии
- [ ] Конкурентный бенчмарк

**Sentiment Analysis:**
- [ ] Анализ тональности упоминаний
- [ ] Детекция негативных упоминаний
- [ ] Автоматическое реагирование на негатив

**Источники цитирований:**
- [ ] Reddit API для мониторинга упоминаний
- [ ] Wikipedia API для проверки статей
- [ ] Парсинг новостных сайтов
- [ ] Мониторинг блогов и форумов

### 13.3 Приоритет 3: Прогнозирование (Фаза 3)

**Predictive Analytics:**
- [ ] Прогнозирование трендов Share of Voice
- [ ] Детекция аномалий в упоминаниях
- [ ] Предсказание падения видимости
- [ ] Рекомендации по превентивным действиям

**Machine Learning:**
- [ ] Модель для классификации источников
- [ ] Модель для предсказания Share of Voice
- [ ] Автоматическая оптимизация стратегии мониторинга

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
   - Приоритет: Фаза 1 (парсинг), Фаза 2 (API)

3. **Perplexity API**
   - Статус: Закрытая beta
   - Альтернатива: Парсинг публичных ответов
   - Приоритет: Фаза 1 (парсинг), Фаза 2 (API)

4. **Reddit API**
   - Документация: https://www.reddit.com/dev/api
   - Стоимость: Бесплатно (до 100 запросов/минуту)
   - Функции: поиск упоминаний бренда, анализ контекста
   - Приоритет: Фаза 2

5. **Wikipedia API**
   - Документация: https://www.mediawiki.org/wiki/API
   - Стоимость: Бесплатно
   - Функции: проверка наличия упоминаний, анализ контекста
   - Приоритет: Фаза 2

6. **Sentiment Analysis API**
   - Варианты: Google Cloud NLP, AWS Comprehend, Azure Text Analytics
   - Стоимость: ~$1-2 за 1000 запросов
   - Функции: анализ тональности упоминаний
   - Приоритет: Фаза 2

### 13.5 Метрики для исследования

**Вопросы для валидации:**
- Как часто AI-модели обновляют индекс?
- Какие факторы влияют на Share of Voice?
- Как измерить ROI от мониторинга?
- Какая корреляция между Share of Voice и трафиком?

**Эксперименты:**
- Корреляция Share of Voice и органического трафика
- Влияние упоминаний на Reddit на Share of Voice
- Эффективность алертов (время реакции vs результат)

---

## Приложение A: Статистика и исследования

### A.1 Ключевые метрики AI-поиска (2024-2026)

**Рост AI-поиска:**
- ChatGPT: 900M пользователей/неделю (2024)
- Perplexity: 1B+ запросов/месяц (2024)
- Google AI Overviews: 1B+ пользователей (2024)
- Claude: 100M+ пользователей (2024)

**Источники цитирований:**
- Reddit: 46.7% источников Perplexity
- Wikipedia: 47.9% источников ChatGPT
- Новостные сайты: 15-20% источников
- Блоги и форумы: 10-15% источников

**Важность мониторинга:**
- 85% цитирований из доменов, которыми вы не владеете
- 40% видимость увеличивается после GEO оптимизации
- < 24 часа — критичное время реакции на падение Share of Voice

### A.2 Лучшие практики мониторинга

**Частота проверок:**
- Минимум: 1 раз в 24 часа
- Рекомендуется: 2 раза в день (утро + вечер)
- Критичные запросы: каждые 6 часов

**Алерты:**
- Share of Voice упал > 20% → критичный алерт
- Бренд исчез из платформы → критичный алерт
- Конкурент доминирует (>70%) → предупреждение
- Новый источник цитирований → информация

**Реакция на алерты:**
- Критичный алерт → реакция < 4 часа
- Предупреждение → реакция < 24 часа
- Информация → review в еженедельном отчёте

### A.3 Инструменты для мониторинга

**Бесплатные:**
- Playwright для парсинга AI-ответов
- Reddit API для мониторинга упоминаний
- Wikipedia API для проверки статей

**Платные:**
- GEO Tracker AI ($99/мес) — автоматический мониторинг
- Brand24 ($49/мес) — мониторинг упоминаний в интернете
- Mention ($29/мес) — алерты о упоминаниях бренда

### A.4 Benchmark по индустрии

**Medical Marketing (средние значения):**
- Share of Voice: 25-35%
- Platform Coverage: 3-4 платформы
- Citation Sources: 8-12 уникальных источников
- Alert Response Time: 6-12 часов

**Топ-игроки (лидеры рынка):**
- Share of Voice: 50-70%
- Platform Coverage: 4/4 платформы
- Citation Sources: 20+ уникальных источников
- Alert Response Time: < 2 часа

---

**Дата создания:** 2026-05-10 21:45 GMT+3  
**Автор:** Mikhail Eliseev (via meAI Architect)  
**Версия:** 1.0.0  
**Статус:** ✅ Готов к реализации  
**Размер:** ~1400 строк, ~48 KB

