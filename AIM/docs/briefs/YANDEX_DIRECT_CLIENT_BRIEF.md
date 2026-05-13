# Бриф: Yandex Direct API Client

**Дата:** 2026-05-13  
**Приоритет:** P0  
**Родительский компонент:** Ads Subagent

## Назначение

Интеграция с Яндекс.Директ API v5 для создания и управления рекламными кампаниями на российском рынке. Unified interface с Google Ads Client для бесшовной работы Services Layer с обеими платформами.

## Контекст и специфика

**Платформа:**
- Яндекс.Директ — основная платформа контекстной рекламы в RU
- API v5 (REST-based, не gRPC как Google)
- OAuth 2.0 для авторизации
- Лимиты: 10 запросов/сек, 100,000 units/день

**Медицинская специфика:**
- Требования для медицинской рекламы в Яндекс.Директ
- Лицензии и ограничения
- Модерация медицинского контента

**Приоритетные типы кампаний:**
- Поиск (текстово-графические объявления)
- РСЯ (Рекламная Сеть Яндекса)
- Смарт-баннеры
- Мастер кампаний

**Geo-targeting:**
- Поддержка региональных кампаний (Москва, регионы)

**Budget management:**
- Ручное управление бюджетом
- Автоматическое управление
- Недельный бюджет

## Интеграции

**Входные данные:**
- Campaign parameters (name, budget, targeting)
- Ad copy (headlines, text, sitelinks)
- Keywords (phrases, match types, bids)

**Выходные данные:**
- Campaign IDs, resource names
- Metrics (impressions, clicks, CTR, CPC, conversions)
- Status updates

**Связанные компоненты:**
- `CampaignService` (должен работать с Yandex так же как с Google)
- `ContentOptimizer` (A/B testing cross-platform)
- `AnalyticsService` (unified metrics)

**Внешние API:**
- Yandex Direct API v5
- Yandex Metrica API (для конверсий)
- Wordstat API (для подбора ключевых слов)

**Unified interface методы:**
- `create_campaign()` - создание кампании
- `get_metrics()` - получение метрик
- `update_status()` - изменение статуса
- `list_campaigns()` - список кампаний

## Приоритеты исследования

### 🔴 КРИТИЧНО (обязательно глубоко изучить)
1. **Yandex Direct API v5 architecture** (REST endpoints, authentication, rate limits)
2. **Campaign types и targeting** (типы кампаний, geo, demographics, interests)
3. **Metrics и reporting** (какие метрики доступны, как получать, формат данных)
4. **Error handling** (типичные ошибки API, retry strategies, rate limit handling)
5. **Medical advertising compliance** (требования для медицинской рекламы)

### 🟡 ВАЖНО (изучить, но не так глубоко)
1. **Bid strategies** (ручное, автоматическое, недельный бюджет, оптимизация конверсий)
2. **Ad formats** (текстово-графические, смарт-баннеры, динамические объявления)
3. **Keyword management** (добавление, удаление, изменение ставок)
4. **Budget pacing** (равномерное расходование бюджета)

### 🟢 ОПЦИОНАЛЬНО (можно пропустить или поверхностно)
1. **Advanced features** (ретаргетинг, lookalike audiences, динамический ремаркетинг)
2. **Yandex Metrica deep integration** (цели, сегменты, когорты)
3. **Wordstat API** (подбор ключевых слов, прогноз трафика)

## Дополнительные материалы

**Интервью:** Проведено 2026-05-13  
**Связанные спецификации:**
- Google Ads Client (AIM/src/aim/subagents/ads/api_clients/google_ads_client.py)
- Base Client (AIM/src/aim/subagents/ads/api_clients/base_client.py)

**Референсы:**
- yandex-ads-mcp (https://github.com/Yurich-ru/yandex-ads-mcp)
