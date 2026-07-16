# Domain Analytics Architecture Specification

**Date:** 2026-05-05  
**Status:** Approved for Implementation  
**Confidence:** 88%  
**Decision ID:** domain-analytics-two-level-arch

---

## Executive Summary

Реализация двухуровневой архитектуры аналитики, где каждый Magister имеет собственного Domain Analytics субагента (5-й субагент) для сбора и агрегации доменных метрик. Эти субагенты передают обработанные данные центральному Analytics Magister для стратегического кросс-доменного анализа.

**Ключевое преимущество:** Каждый домен знает свои метрики лучше всех и агрегирует их локально, а Analytics Magister работает с уже обработанными данными.

---

## Problem Statement

### Текущая проблема

Analytics Magister пытается централизованно собирать гетерогенные метрики из разных доменов:
- SEO метрики (позиции, органический трафик, backlinks)
- Content метрики (публикации, engagement, качество)
- Ads метрики (кампании, CTR, ROAS, бюджет)
- AI метрики (токены, latency, качество генерации)

**Проблема:** Каждый домен имеет уникальные метрики, источники данных и логику агрегации. Централизованный сбор создаёт tight coupling и не масштабируется.

### Почему это критично

1. **Гетерогенность метрик** - разные домены имеют разные KPI
2. **Разные источники данных** - каждый домен работает со своими API
3. **Доменная экспертиза** - только SEO Magister знает, как правильно агрегировать SEO метрики
4. **Масштабируемость** - добавление нового домена не должно менять Analytics Magister

---

## Solution: Two-Level Analytics Architecture

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Analytics Magister                        │
│                  (Strategic Analysis)                        │
│                                                              │
│  Capabilities:                                               │
│  - Cross-domain correlation analysis                         │
│  - Strategic insights generation                             │
│  - Executive reporting                                       │
│  - Trend forecasting across domains                          │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ Aggregated Domain Metrics
                   │
        ┌──────────┴──────────┬──────────┬──────────┐
        │                     │          │          │
        ▼                     ▼          ▼          ▼
┌───────────────┐    ┌───────────────┐  ...    ┌───────────────┐
│ SEO Analytics │    │Content Analytics│       │ Ads Analytics │
│   Subagent    │    │   Subagent     │       │   Subagent    │
│  (5th agent)  │    │  (5th agent)   │       │  (5th agent)  │
└───────┬───────┘    └───────┬────────┘       └───────┬───────┘
        │                    │                         │
        │ Domain Metrics     │                         │
        │                    │                         │
        ▼                    ▼                         ▼
┌───────────────┐    ┌───────────────┐       ┌───────────────┐
│ SEO Magister  │    │Content Magister│       │ Ads Magister  │
│               │    │                │       │               │
│ 4 subagents   │    │ 4 subagents    │       │ 4 subagents   │
└───────────────┘    └────────────────┘       └───────────────┘
```

### Key Principles

1. **Local Aggregation** - каждый домен агрегирует свои метрики локально
2. **Domain Expertise** - доменные субагенты знают свои метрики лучше всех
3. **Loose Coupling** - Analytics Magister не знает о внутренних метриках доменов
4. **Standardized Interface** - все Domain Analytics субагенты используют единый формат данных

---

## Component Design

### 1. Base Domain Analytics Agent

**File:** `AIM/src/aim/subagents/base_domain_analytics.py`

**Purpose:** Базовый класс для всех Domain Analytics субагентов

**Key Methods:**

```python
class BaseDomainAnalytics(ABC):
    """Base class for Domain Analytics Subagents"""
    
    @abstractmethod
    async def collect_metrics(
        self, 
        date_range: dict
    ) -> DomainMetrics:
        """Collect domain-specific metrics"""
        pass
    
    @abstractmethod
    async def aggregate_metrics(
        self, 
        raw_metrics: list
    ) -> AggregatedMetrics:
        """Aggregate raw metrics into domain summary"""
        pass
    
    async def publish_to_analytics(
        self, 
        metrics: AggregatedMetrics
    ) -> None:
        """Publish aggregated metrics to Analytics Magister"""
        await self.event_bus.publish(Event(
            event_type="analytics.domain_metrics_ready",
            payload={
                "domain": self.domain,
                "metrics": metrics.dict(),
                "timestamp": datetime.now().isoformat()
            }
        ))
```

**Data Models:**

```python
class DomainMetrics(BaseModel):
    """Raw domain metrics"""
    domain: str
    period: dict
    raw_data: dict
    collected_at: datetime

class AggregatedMetrics(BaseModel):
    """Aggregated domain metrics"""
    domain: str
    period: dict
    summary: dict  # High-level summary
    kpis: dict     # Key Performance Indicators
    trends: dict   # Trend analysis
    insights: list # Domain-specific insights
    aggregated_at: datetime
```

### 2. SEO Analytics Subagent

**File:** `AIM/src/aim/subagents/seo/seo_analytics_agent.py`

**Purpose:** Собирает и агрегирует SEO метрики

**Metrics:**
- Organic traffic (sessions, users, pageviews)
- Keyword rankings (positions, visibility)
- Backlinks (total, quality, growth)
- Technical SEO (crawl errors, page speed)

**Data Sources:**
- Google Search Console
- Яндекс.Вебмастер
- Ahrefs/Semrush API
- Google Analytics (organic segment)

**Aggregation Logic:**
```python
async def aggregate_metrics(self, raw_metrics: list) -> AggregatedMetrics:
    """
    Агрегация SEO метрик:
    - Суммирование органического трафика
    - Расчёт средней позиции по ключевым словам
    - Анализ динамики backlinks
    - Выявление технических проблем
    """
    return AggregatedMetrics(
        domain="seo",
        summary={
            "organic_traffic": sum(m.sessions for m in raw_metrics),
            "avg_position": calculate_avg_position(raw_metrics),
            "backlinks_growth": calculate_backlinks_growth(raw_metrics)
        },
        kpis={
            "organic_sessions": total_sessions,
            "keyword_visibility": visibility_score,
            "domain_authority": da_score
        },
        trends={
            "traffic_trend": "growing",
            "rankings_trend": "stable",
            "backlinks_trend": "growing"
        },
        insights=[
            "Organic traffic вырос на 15% за месяц",
            "TOP-10 позиций увеличилось на 8 ключевых слов",
            "Получено 23 новых качественных backlinks"
        ]
    )
```

### 3. Content Analytics Subagent

**File:** `AIM/src/aim/subagents/content/content_analytics_agent.py`

**Purpose:** Собирает и агрегирует Content метрики

**Metrics:**
- Publications (count, frequency, types)
- Engagement (views, time on page, shares)
- Quality (readability, SEO score, uniqueness)
- Performance (top content, conversions)

**Data Sources:**
- CMS API (WordPress, etc.)
- Google Analytics (content reports)
- Social media APIs
- Internal quality checks

**Aggregation Logic:**
```python
async def aggregate_metrics(self, raw_metrics: list) -> AggregatedMetrics:
    """
    Агрегация Content метрик:
    - Подсчёт публикаций по типам
    - Расчёт среднего engagement
    - Оценка качества контента
    - Выявление top performers
    """
    return AggregatedMetrics(
        domain="content",
        summary={
            "total_publications": count_publications(raw_metrics),
            "avg_engagement": calculate_avg_engagement(raw_metrics),
            "quality_score": calculate_quality_score(raw_metrics)
        },
        kpis={
            "publications_count": total_pubs,
            "avg_time_on_page": avg_time,
            "content_quality": quality_score
        },
        trends={
            "publication_frequency": "increasing",
            "engagement_trend": "stable",
            "quality_trend": "improving"
        },
        insights=[
            "Опубликовано 12 статей за месяц (+20%)",
            "Среднее время на странице: 4:32 мин",
            "3 статьи попали в TOP-10 по engagement"
        ]
    )
```

### 4. Ads Analytics Subagent

**File:** `AIM/src/aim/subagents/ads/ads_analytics_agent.py`

**Purpose:** Собирает и агрегирует Ads метрики

**Metrics:**
- Campaign performance (impressions, clicks, CTR)
- Budget utilization (spend, CPC, CPA)
- Conversions (goals, revenue, ROAS)
- Channel comparison (Yandex vs Google vs VK)

**Data Sources:**
- Яндекс.Директ API
- Google Ads API
- VK Ads API
- Facebook Ads API

**Aggregation Logic:**
```python
async def aggregate_metrics(self, raw_metrics: list) -> AggregatedMetrics:
    """
    Агрегация Ads метрик:
    - Суммирование показов и кликов
    - Расчёт средних CPC, CPA, ROAS
    - Сравнение каналов
    - Анализ бюджета
    """
    return AggregatedMetrics(
        domain="ads",
        summary={
            "total_spend": sum(m.spend for m in raw_metrics),
            "total_conversions": sum(m.conversions for m in raw_metrics),
            "avg_roas": calculate_avg_roas(raw_metrics)
        },
        kpis={
            "total_impressions": total_impressions,
            "avg_ctr": avg_ctr,
            "roas": roas
        },
        trends={
            "spend_trend": "stable",
            "conversions_trend": "growing",
            "roas_trend": "improving"
        },
        insights=[
            "ROAS вырос до 4.2 (+15%)",
            "Яндекс.Директ показывает лучший CPA: 850 руб",
            "Рекомендуется увеличить бюджет на 20%"
        ]
    )
```

### 5. AI Analytics Subagent

**File:** `AIM/src/aim/subagents/ai/ai_analytics_agent.py`

**Purpose:** Собирает и агрегирует AI метрики

**Metrics:**
- Token usage (input, output, total)
- Latency (response time, p95, p99)
- Quality (user ratings, regenerations)
- Cost (per request, per domain)

**Data Sources:**
- Internal AI logs
- Anthropic API usage
- User feedback database
- Cost tracking system

**Aggregation Logic:**
```python
async def aggregate_metrics(self, raw_metrics: list) -> AggregatedMetrics:
    """
    Агрегация AI метрик:
    - Суммирование токенов
    - Расчёт средней latency
    - Анализ качества генерации
    - Подсчёт стоимости
    """
    return AggregatedMetrics(
        domain="ai",
        summary={
            "total_tokens": sum(m.tokens for m in raw_metrics),
            "avg_latency": calculate_avg_latency(raw_metrics),
            "quality_score": calculate_quality_score(raw_metrics)
        },
        kpis={
            "tokens_per_day": tokens_per_day,
            "avg_response_time": avg_latency,
            "user_satisfaction": satisfaction_score
        },
        trends={
            "usage_trend": "growing",
            "latency_trend": "stable",
            "quality_trend": "improving"
        },
        insights=[
            "Использовано 2.5M токенов за месяц",
            "Средняя latency: 1.2s (в пределах SLA)",
            "User satisfaction: 4.7/5.0"
        ]
    )
```

### 6. Updated Analytics Magister

**File:** `AIM/src/aim/magisters/analytics_magister.py` (refactor)

**Changes:**

1. **Remove direct data collection** - больше не собирает данные напрямую
2. **Add domain metrics aggregation** - агрегирует данные от Domain Analytics субагентов
3. **Add cross-domain analysis** - анализирует корреляции между доменами
4. **Add strategic insights** - генерирует стратегические выводы

**New Methods:**

```python
class AnalyticsMagister(BaseMagister):
    """
    Analytics Magister - Strategic cross-domain analysis
    
    Responsibilities:
    - Aggregate metrics from Domain Analytics subagents
    - Cross-domain correlation analysis
    - Strategic insights generation
    - Executive reporting
    """
    
    async def aggregate_domain_metrics(
        self, 
        domain_metrics: list[AggregatedMetrics]
    ) -> CrossDomainMetrics:
        """
        Агрегация метрик от всех доменов
        
        Анализирует:
        - Корреляции между доменами
        - Общие тренды
        - Стратегические возможности
        """
        pass
    
    async def analyze_cross_domain_correlations(
        self, 
        metrics: CrossDomainMetrics
    ) -> list[Correlation]:
        """
        Анализ корреляций между доменами
        
        Примеры:
        - SEO traffic ↑ → Ads CPA ↓ (органика снижает стоимость привлечения)
        - Content quality ↑ → SEO rankings ↑ (качество влияет на позиции)
        - AI usage ↑ → Content output ↑ (автоматизация ускоряет производство)
        """
        pass
    
    async def generate_strategic_insights(
        self, 
        correlations: list[Correlation]
    ) -> list[StrategicInsight]:
        """
        Генерация стратегических инсайтов
        
        Примеры:
        - "Увеличение SEO бюджета на 20% снизит Ads CPA на 15%"
        - "Качество контента коррелирует с органическим трафиком (r=0.85)"
        - "AI автоматизация окупается за 2 месяца"
        """
        pass
```

---

## Data Flow

### 1. Daily Metrics Collection

```
09:00 UTC - Scheduled Task
    │
    ├─→ SEO Analytics Subagent
    │   ├─ Collect from Google Search Console
    │   ├─ Collect from Яндекс.Вебмастер
    │   ├─ Aggregate SEO metrics
    │   └─ Publish to Analytics Magister
    │
    ├─→ Content Analytics Subagent
    │   ├─ Collect from CMS
    │   ├─ Collect from Google Analytics
    │   ├─ Aggregate Content metrics
    │   └─ Publish to Analytics Magister
    │
    ├─→ Ads Analytics Subagent
    │   ├─ Collect from Яндекс.Директ
    │   ├─ Collect from Google Ads
    │   ├─ Aggregate Ads metrics
    │   └─ Publish to Analytics Magister
    │
    └─→ AI Analytics Subagent
        ├─ Collect from internal logs
        ├─ Collect from Anthropic API
        ├─ Aggregate AI metrics
        └─ Publish to Analytics Magister

10:00 UTC - Analytics Magister
    │
    ├─ Receive all domain metrics
    ├─ Aggregate cross-domain metrics
    ├─ Analyze correlations
    ├─ Generate strategic insights
    └─ Publish daily report
```

### 2. Event Bus Communication

**Events:**

```python
# Domain Analytics → Analytics Magister
"analytics.domain_metrics_ready"
{
    "domain": "seo",
    "metrics": AggregatedMetrics,
    "timestamp": "2026-05-05T09:15:00Z"
}

# Analytics Magister → Operator
"analytics.daily_report_ready"
{
    "report_type": "daily",
    "cross_domain_metrics": CrossDomainMetrics,
    "strategic_insights": list[StrategicInsight],
    "timestamp": "2026-05-05T10:00:00Z"
}

# Analytics Magister → All Magisters
"analytics.alert"
{
    "severity": "high",
    "message": "SEO traffic dropped 25% - investigate",
    "affected_domains": ["seo", "content"],
    "timestamp": "2026-05-05T14:30:00Z"
}
```

---

## Implementation Plan

### Phase 1: Base Infrastructure (Day 1)

**Tasks:**
1. ✅ Create `BaseDomainAnalytics` class
2. ✅ Define data models (`DomainMetrics`, `AggregatedMetrics`, `CrossDomainMetrics`)
3. ✅ Update Event Bus with new event types
4. ✅ Create Obsidian vault structure for Domain Analytics

**Files:**
- `AIM/src/aim/subagents/base_domain_analytics.py`
- `AIM/src/aim/models/analytics_models.py`
- `AIM/obsidian/*/wiki/analytics/` (for each Magister)

**Tests:**
- Unit tests for `BaseDomainAnalytics`
- Event Bus integration tests

### Phase 2: Domain Analytics Subagents (Day 2-3)

**Tasks:**
1. ✅ Implement SEO Analytics Subagent
2. ✅ Implement Content Analytics Subagent
3. ✅ Implement Ads Analytics Subagent
4. ✅ Implement AI Analytics Subagent

**Files:**
- `AIM/src/aim/subagents/seo/seo_analytics_agent.py`
- `AIM/src/aim/subagents/content/content_analytics_agent.py`
- `AIM/src/aim/subagents/ads/ads_analytics_agent.py`
- `AIM/src/aim/subagents/ai/ai_analytics_agent.py`

**Tests:**
- Unit tests for each subagent
- Integration tests with mock data sources

### Phase 3: Analytics Magister Refactor (Day 4)

**Tasks:**
1. ✅ Refactor Analytics Magister to work with Domain Analytics
2. ✅ Implement cross-domain aggregation
3. ✅ Implement correlation analysis
4. ✅ Implement strategic insights generation

**Files:**
- `AIM/src/aim/magisters/analytics_magister.py` (refactor)

**Tests:**
- Integration tests with all Domain Analytics subagents
- End-to-end test of full analytics pipeline

### Phase 4: Integration & Testing (Day 5)

**Tasks:**
1. ✅ Integrate with existing Magisters
2. ✅ Update Excalidraw diagram
3. ✅ End-to-end testing
4. ✅ Documentation

**Files:**
- `Excalidraw/AIM-Agency-Architecture.excalidraw.md` (update)
- `docs/analytics-architecture.md` (create)

**Tests:**
- Full system integration test
- Performance testing
- Load testing

---

## Obsidian Vault Structure

Each Magister gets analytics section in their vault:

```
AIM/obsidian/{magister}/
├── wiki/
│   ├── analytics/                    # NEW
│   │   ├── daily-metrics.md         # Daily metrics log
│   │   ├── trends.md                # Trend analysis
│   │   ├── insights.md              # Domain insights
│   │   └── correlations.md          # Cross-domain correlations
│   ├── concepts/
│   ├── technologies/
│   └── ...
└── SCHEMA.md
```

Analytics Magister vault:

```
AIM/obsidian/analytics-magister/
├── wiki/
│   ├── cross-domain/                # NEW
│   │   ├── correlations.md         # Cross-domain correlations
│   │   ├── strategic-insights.md   # Strategic insights
│   │   └── executive-reports.md    # Executive reports
│   ├── domains/                     # NEW
│   │   ├── seo-metrics.md          # SEO domain summary
│   │   ├── content-metrics.md      # Content domain summary
│   │   ├── ads-metrics.md          # Ads domain summary
│   │   └── ai-metrics.md           # AI domain summary
│   └── ...
└── SCHEMA.md
```

---

## Success Metrics

### Technical Metrics

- ✅ All 4 Domain Analytics subagents implemented
- ✅ Analytics Magister refactored
- ✅ Event Bus integration working
- ✅ All tests passing (unit + integration + E2E)
- ✅ Documentation complete

### Business Metrics

- **Data Quality:** 95%+ accuracy in metric aggregation
- **Latency:** < 5 min from collection to insights
- **Coverage:** 100% of domain metrics captured
- **Insights Quality:** 80%+ actionable insights
- **Correlation Accuracy:** 70%+ correlation predictions validated

### Operational Metrics

- **Uptime:** 99.9% availability
- **Performance:** < 10s for cross-domain analysis
- **Scalability:** Support for 10+ domains without refactor
- **Maintainability:** < 1 hour to add new domain

---

## Risks & Mitigation

### Risk 1: Data Source API Changes

**Impact:** High  
**Probability:** Medium  
**Mitigation:**
- Abstract data source access behind interfaces
- Version API clients
- Monitor API deprecation notices
- Implement fallback data sources

### Risk 2: Metric Heterogeneity

**Impact:** Medium  
**Probability:** High  
**Mitigation:**
- Standardized `AggregatedMetrics` format
- Domain-specific extensions allowed
- Clear documentation of metric definitions
- Validation at aggregation boundaries

### Risk 3: Performance at Scale

**Impact:** Medium  
**Probability:** Low  
**Mitigation:**
- Async processing throughout
- Caching of aggregated metrics
- Incremental updates (not full recalculation)
- Database indexing on time-series data

### Risk 4: Cross-Domain Correlation Accuracy

**Impact:** Low  
**Probability:** Medium  
**Mitigation:**
- Start with simple correlations (Pearson r)
- Validate correlations with historical data
- Human review of strategic insights
- Confidence scores on all correlations

---

## Alternatives Considered

### Alternative 1: Centralized Analytics (Current)

**Pros:**
- Simple architecture
- Single point of control
- Easy to understand

**Cons:**
- Tight coupling between domains
- Analytics Magister knows too much
- Hard to scale
- Domain expertise lost

**Verdict:** ❌ Rejected - doesn't scale, tight coupling

### Alternative 2: Fully Distributed Analytics

**Pros:**
- Maximum decoupling
- Each Magister fully autonomous
- Easy to add new domains

**Cons:**
- No cross-domain analysis
- Duplicate analytics logic
- Hard to get strategic insights
- No central reporting

**Verdict:** ❌ Rejected - loses strategic value

### Alternative 3: Two-Level Architecture (Chosen)

**Pros:**
- Balance of decoupling and coordination
- Domain expertise preserved
- Cross-domain analysis possible
- Scalable architecture

**Cons:**
- More complex than centralized
- Requires standardized interfaces
- Two levels of aggregation

**Verdict:** ✅ **CHOSEN** - best balance of trade-offs

---

## Open Questions

1. **Q:** How to handle real-time vs batch analytics?  
   **A:** Domain Analytics = batch (daily), Analytics Magister = real-time alerts

2. **Q:** What if a domain doesn't have analytics data yet?  
   **A:** Domain Analytics returns empty metrics, Analytics Magister handles gracefully

3. **Q:** How to version metric definitions?  
   **A:** Include `schema_version` in `AggregatedMetrics`, support backward compatibility

4. **Q:** How to handle metric conflicts between domains?  
   **A:** Each domain owns its metrics, Analytics Magister resolves at aggregation

---

## Next Steps

1. **Create base infrastructure** (Phase 1)
2. **Implement Domain Analytics subagents** (Phase 2-3)
3. **Refactor Analytics Magister** (Phase 4)
4. **Update Excalidraw diagram** (Phase 4)
5. **End-to-end testing** (Phase 5)
6. **Documentation** (Phase 5)

---

## References

- `CLAUDE.md` - Development philosophy ("Deep & Correct")
- `src/meai/agents/magister_base.py` - BaseMagister pattern
- `AIM/src/aim/magisters/seo_magister.py` - Example of aggregation logic
- `AIM/src/aim/magisters/analytics_magister.py` - Current implementation (to refactor)
- LLM Wiki Pattern - Obsidian vault structure

---

**Approved by:** Architect  
**Implementation Start:** 2026-05-05  
**Estimated Completion:** 2026-05-10 (5 days)  
**Priority:** P1 (High)
