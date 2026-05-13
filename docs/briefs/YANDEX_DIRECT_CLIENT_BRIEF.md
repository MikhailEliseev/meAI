# Бриф: Yandex Direct API Client

**Дата:** 2026-05-14  
**Приоритет:** P0 (Critical)  
**Родительский Magister:** Ads Magister

## Назначение

Production-ready Python клиент для Yandex Direct API v5 с unified interface (совместимым с Google Ads Client), включая resilience patterns, medical advertising compliance, и comprehensive campaign management.

## Контекст и специфика

### Особенности предметной области

1. **Rate Limits (КРИТИЧНО):**
   - 5 concurrent connections (НЕ 10 req/s как в документации)
   - 100,000 points/day
   - Error 152 (not enough points) стоит 20 points на retry → НИКОГДА не retry

2. **Medical Advertising Compliance:**
   - Federal Law 38-FZ Article 24
   - Обязательный disclaimer: "Имеются противопоказания. Необходима консультация специалиста"
   - Запрещено: testimonials, guarantees, targeting minors, comparisons
   - Требуется: license number, issuing authority, issue date

3. **Production Gaps:**
   - Reference implementation (yandex-ads-mcp, 1,871 lines, 120 tools) отличный для API structure
   - НО: отсутствуют production resilience patterns (circuit breaker, exponential backoff, rate limit detection)
   - НО: не использует Changes service (80-90% reduction in API calls)

4. **Budget Format:**
   - Currency: Russian Rubles (RUB)
   - Format: Micros (1 ruble = 1,000,000 micros)
   - Conversion: `int(rubles * 1_000_000)`

## Интеграции

### Входные данные

**От Ads Magister:**
- Campaign parameters (name, budget, targeting, strategy)
- Ad copy and creatives
- Keywords and bids
- Medical license information (for medical campaigns)

**От Analytics Magister:**
- Performance metrics requests
- Conversion tracking setup
- Goal IDs for optimization

### Выходные данные

**К Ads Magister:**
- Campaign creation results (IDs, status)
- Campaign performance metrics
- Moderation status
- Error reports

**К Analytics Magister:**
- Campaign statistics (impressions, clicks, CTR, CPC, conversions)
- Budget utilization
- Points usage tracking

### Связанные агенты

- **Ads Magister** — родительский Magister, управляет рекламными кампаниями
- **Google Ads Client** — параллельный клиент, unified interface должен совпадать
- **Analytics Magister** — получает метрики и статистику
- **Content Magister** — предоставляет ad copy для кампаний

### Внешние API

**Yandex Direct API v5:**
- Base URL: `https://api.direct.yandex.com/json/v5/{service}`
- Sandbox URL: `https://api-sandbox.direct.yandex.com/json/v5/{service}`
- OAuth 2.0: `https://oauth.yandex.com/token`
- 18 services: Campaigns, AdGroups, Ads, Keywords, Bids, Reports, Changes, etc.

**Yandex OAuth:**
- Authorization: `https://oauth.yandex.ru/authorize`
- Token exchange: `https://oauth.yandex.ru/token`
- Required scope: `direct:api`

## Приоритеты исследования

### 🔴 КРИТИЧНО (обязательно глубоко изучить)

1. **Connection Pooling (5 connections max)**
   - httpx.AsyncClient with limits
   - Prevent error 506 (too many connections)
   - Connection reuse for performance

2. **Circuit Breaker Pattern**
   - pybreaker with fail_max=5, reset_timeout=60s
   - Prevent cascading failures
   - Fail fast when API is down

3. **Rate Limit Detection**
   - Error 152 → DO NOT RETRY (costs 20 points)
   - Error 506 → Reduce connections
   - Error 1002 → Refresh OAuth token
   - Points budget tracking (100k/day)

4. **Exponential Backoff**
   - tenacity with 3 attempts max
   - Wait: 1s → 2s → 4s (max 30s)
   - Retry only on network errors (NOT API errors)

5. **Medical Compliance Validator**
   - Required disclaimer check
   - Prohibited phrases detection (30+ phrases)
   - License validation
   - Age targeting restrictions

6. **Changes Service Optimization**
   - 80-90% reduction in API calls
   - Check for changes before fetching full data
   - Cache management

### 🟡 ВАЖНО (изучить, но не так глубоко)

1. **Unified Interface Design**
   - Match Google Ads Client method signatures
   - Internal mapping (USD ↔ RUB, status codes, campaign types)
   - Unified response format

2. **OAuth Token Management**
   - Token validation
   - Re-authorization flow
   - Agency account support (Client-Login header)

3. **Bidding Strategies**
   - 8 strategies for search campaigns
   - WB_MAXIMUM_CLICKS, PAY_FOR_CONVERSION, AVERAGE_CPA, etc.
   - Strategy-specific parameters

4. **Budget Management**
   - Daily budget vs weekly spend limits
   - STANDARD vs DISTRIBUTED modes
   - Budget pacing

### 🟢 ОПЦИОНАЛЬНО (можно пропустить или поверхностно)

1. **Advanced Retargeting**
   - Lookalike audiences
   - Custom audience segments

2. **Deep Yandex Metrica Integration**
   - Goals, segments, cohorts
   - Advanced analytics

3. **Wordstat API**
   - Keyword research
   - Traffic forecasting

## Дополнительные материалы

**Deep Research:** `~/Documents/Yandex_Direct_API_Research_20260514/Yandex_Direct_API_Research_Report.md`
- 2,218 lines, 65 KB
- 93 evidence items, 87/100 avg credibility
- 18+ code examples
- 8 phases completed (SCOPE → PACKAGE)

**GitHub Repository (КРИТИЧНО изучить):**
- `https://github.com/Yurich-ru/yandex-ads-mcp`
- 1,871 lines, 120 tools
- Production API structure
- OAuth implementation
- Agency account support
- **НО:** отсутствуют resilience patterns

**Связанные спецификации:**
- Google Ads Client (для unified interface)
- Ads Magister (родительский)
- Analytics Magister (метрики)

**TODO из других агентов:**
- Ads Magister: интеграция с Yandex Direct Client
- Analytics Magister: сбор метрик из Yandex Direct
- Content Magister: генерация ad copy с medical compliance

## Ключевые решения из исследования

### 1. Rate Limits (КРИТИЧЕСКАЯ КОРРЕКЦИЯ)

**Было (неправильно):** 10 requests/second  
**Стало (правильно):** 5 concurrent connections + 100k points/day

**Импликация:** Нужен connection pooling, НЕ rate limiting

### 2. Production Gaps

**yandex-ads-mcp отличный для:**
- API structure (18 services, 120 tools)
- OAuth flow
- Agency accounts

**yandex-ads-mcp НЕ имеет:**
- Circuit breaker
- Exponential backoff
- Rate limit detection
- Changes service optimization

**Решение:** Взять API structure из yandex-ads-mcp + добавить resilience patterns

### 3. Medical Compliance

**Обязательно:**
- Disclaimer в КАЖДОМ объявлении
- License validation
- Prohibited phrases check
- Age targeting restrictions

**Решение:** MedicalAdValidator class с автоматической проверкой

### 4. Cost Optimization

**Changes Service:**
- Проверка изменений перед fetching
- 80-90% reduction in API calls
- Cache management

**Решение:** Обязательно использовать Changes service для monitoring

## Метрики успеха

**Performance:**
- < 5 concurrent connections (prevent error 506)
- < 100k points/day (prevent error 152)
- 80-90% API call reduction (via Changes service)

**Reliability:**
- Circuit breaker opens after 5 failures
- Exponential backoff: 1s → 30s max
- Zero retries on error 152

**Compliance:**
- 100% medical ads have disclaimer
- 0 prohibited phrases in production
- 100% license validation

**Interface:**
- 100% method signature match with Google Ads Client
- Unified response format
- Seamless Services Layer integration
