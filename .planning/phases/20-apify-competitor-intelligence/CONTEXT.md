# Phase 20: Apify-Based Competitor Intelligence — Context

## Source: Architectural Decision (2026-05-25)

Полный отказ от Yandex/OSM/DomainGuess подхода в пользу Apify scraping platform. Текущий пайплайн сломан: Yandex API key невалидный (403), OSM медленный, DomainGuess генерирует нерелевантные домены.

## Current Pipeline (BROKEN)

```
Client URL → service_extractor.py → CompetitorMatcher
                ↓                        ↓
         specialization          1. Yandex Maps (403 ❌)
         city                    2. OSM Overpass (медленно)
         services                3. DaData (нет website)
                                 4. Yandex Web Search (captcha ❌)
                                 5. DomainGuess (нерелевантные домены ❌)
                                 6. Social Discovery (минимальный результат)
                                 ↓
                           Merge + Score → top-3
```

**Проблемы:**
- 183 секунды на поиск (цель <60s)
- Yandex Maps API key `69c48132-03b0-4fbe-8120-4a439b19621a` — 403 Forbidden
- Yandex Web Search блокирует через captcha
- DomainGuess: grib-prom.ru для клиники «ЦВК» (это сайт про выставку продуктов)
- Social links: 1/3 конкурентов имеет youtube, остальные пустые
- DaData не возвращает website ни для одной компании

## Target Pipeline (Apify-First)

```
Client URL → service_extractor.py → CompetitorMatcher
                ↓                        ↓
         specialization          1. Apify Google Maps (основной)
         city                    2. Apify Instagram Scraper (соцсети)
         services                3. Apify Website Content Crawler (сервисы)
                                 4. DaData + rusprofile (финансы, enrichment)
                                 ↓
                           Merge + Score → top-3
```

## Apify Actors — Подробный Анализ

### 1. Google Maps Scraper (`compass/crawler-google-places`)

**URL:** https://apify.com/compass/crawler-google-places
**Pricing:** ~$5/1000 results (Apify platform credits)
**Cost per search:** ~$0.10-0.25 (50 результатов × $5/1000)

**Возможности:**
- Обходит 120-result лимит Google Maps API через zooming на тайлах карты
- Возвращает: name, address, phone, website, rating, reviewsCount, categories, location (lat/lng), openingHours, socialMedia
- Поддерживает includeSocialMedia: true (извлекает Facebook, Instagram, Twitter из карточки)
- Поддерживает includeReviews: true (тексты отзывов с датами)
- Поддерживает поиск по searchString + location (город/адрес)
- Язык: lang="ru" для российского рынка

**Run input:**
```python
{
    "searchString": "стоматология",
    "location": "Москва",
    "maxResults": 50,
    "language": "ru",
    "includeSocialMedia": True,
    "includeReviews": False,  # дороже, опционально
    "proxyConfig": {"useApifyProxy": True},
}
```

**Output fields (ключевые):**
| Поле | Описание | Использование |
|------|----------|---------------|
| title | Название организации | Name matching |
| address | Полный адрес | Location scoring |
| phone | Телефон | Dedup key |
| website | Сайт клиники | Scraping target |
| location.lat/lng | Координаты | Distance calc |
| rating | Рейтинг (1.0-5.0) | Popularity score |
| reviewsCount | Количество отзывов | Popularity score |
| categories[] | Google категории | Specialization matching |
| socialMedia | Соцсети из карточки | Social enrichment |
| placeId | Google Place ID | Dedup |
| permanentlyClosed | Закрыто ли | Filter out |

### 2. Instagram Scraper (`apify/instagram-scraper`)

**URL:** https://apify.com/apify/instagram-scraper
**Pricing:** ~$5/1000 results
**Cost per search:** ~$0.005-0.01 (2-3 профиля клиник)

**Возможности:**
- Скрапит Instagram-профили без авторизации (публичные данные)
- Извлекает: bio, posts, followers, following, hashtags, mentions
- Может искать по username и hashtag

**Использование для конкурентной разведки:**
- Найти Instagram-профиль по website/названию клиники
- Извлечь bio (услуги, специализация, tone of voice)
- Количество followers = сигнал популярности
- Посты = контент-стратегия конкурента (что продвигают, акции, tone)

**Run input:**
```python
{
    "usernames": ["clinic_name_from_google_maps"],
    "resultsLimit": 20,
}
```

### 3. Website Content Crawler (`apify/website-content-crawler`)

**URL:** https://apify.com/apify/website-content-crawler
**Pricing:** ~$10/1000 pages
**Cost per search:** ~$0.30 (3 конкурента × 10 страниц = 30 pages)

**Возможности:**
- Adaptive mode: сначала HTTP запрос (быстро), если JS-rendered → Firefox/Playwright (медленно)
- Извлекает: title, text, html, metadata, headings, links
- Обходит до N страниц на домен (crawlDepth, maxPagesPerDomain)
- Сохраняет скриншоты (опционально)
- Удаляет cookie banners и popups

**Использование для конкурентной разведки:**
- Извлечь список услуг с сайта конкурента (реальные услуги вместо constructed!)
- Извлечь цены (если есть)
- Извлечь врачей/специалистов
- Извлечь акции и спецпредложения
- Извлечь tone of voice и маркетинговые сообщения

**Run input:**
```python
{
    "startUrls": [{"url": "https://competitor-clinic.ru"}],
    "maxPagesPerDomain": 10,
    "crawlDepth": 1,
    "saveHtml": False,
    "removeCookieWarnings": True,
}
```

### 4. TikTok Scraper (`clockworks/tiktok-scraper`) — Опционально

**Использование:** Для клиник, активно ведущих TikTok (пока редкость в РФ-медицине)

## Техническая Интеграция

### Apify Python SDK

```bash
pip install apify-client
```

```python
from apify_client import ApifyClientAsync

client = ApifyClientAsync(token='APIFY_API_TOKEN')

# Google Maps
async def find_competitors_google_maps(query, location, count=50):
    run = await client.actor('compass/crawler-google-places').call(
        run_input={
            'searchString': query,
            'location': location,
            'maxResults': count,
            'language': 'ru',
            'includeSocialMedia': True,
        },
        run_timeout=timedelta(minutes=5),
        memory_mbytes=2048,
    )
    if run and run.get('defaultDatasetId'):
        dataset = client.dataset(run['defaultDatasetId'])
        return [item async for item in dataset.iterate_items()]
    return []

# Website Crawler
async def crawl_competitor_website(url, max_pages=10):
    run = await client.actor('apify/website-content-crawler').call(
        run_input={
            'startUrls': [{'url': url}],
            'maxPagesPerDomain': max_pages,
            'crawlDepth': 1,
            'saveHtml': False,
            'removeCookieWarnings': True,
        },
        run_timeout=timedelta(minutes=3),
        memory_mbytes=1024,
    )
    if run and run.get('defaultDatasetId'):
        dataset = client.dataset(run['defaultDatasetId'])
        return [item async for item in dataset.iterate_items()]
    return []
```

### Интеграция в CompetitorMatcher

**Новый метод `_discover_google_maps()`:**

```python
async def _discover_google_maps(
    self, specialization: str, city: str, count: int = 50
) -> list[CompanyProfile]:
    """Discover competitors via Apify Google Maps Scraper."""
    query = f"{specialization} {city}"
    results = await find_competitors_google_maps(query, city, count)
    
    profiles = []
    for item in results:
        profile = CompanyProfile(
            legal_name=item.get("title", ""),
            website=item.get("website"),
            social_links=item.get("socialMedia", {}),
            geo_lat=item.get("location", {}).get("lat"),
            geo_lon=item.get("location", {}).get("lng"),
            rating=item.get("rating"),
            reviews_count=item.get("reviewsCount"),
            source_specialization=specialization,
            data_source="apify_google_maps",
        )
        profiles.append(profile)
    
    return profiles
```

### DaData + rusprofile (СОХРАНЯЕМ для финансов)

DaData остаётся ТОЛЬКО для:
1. Поиска юрлица по названию (name → INN)
2. Получения финансовых данных через rusprofile

Больше НЕ используется для:
- Первичного поиска конкурентов (заменён на Apify Google Maps)
- Гео-поиска (заменён на Google Maps)

## Cost Estimate

| Операция | Actor | Стоимость |
|----------|-------|-----------|
| Поиск 50 конкурентов | Google Maps | $0.25 |
| Instagram профили (3 шт.) | Instagram Scraper | $0.015 |
| Скрапинг сайтов (3 × 10 стр.) | Website Content Crawler | $0.30 |
| **Итого за один поиск** | | **~$0.57** |
| DaData enrichment | DaData API | бесплатно |
| rusprofile enrichment | rusprofile | бесплатно |

**При 100 поисках/месяц:** ~$57/мес

## Ожидаемые Улучшения

| Метрика | Текущий (Yandex) | Целевой (Apify) |
|---------|------------------|-----------------|
| Время поиска | 183s | 15-30s (параллельные запросы) |
| Website coverage | ~10% | ~80%+ (Google Maps + Website Crawler) |
| Social links | ~5% | ~60%+ (Instagram + Google Maps социальные ссылки) |
| Реальные услуги | 0% (constructed) | ~90% (Website Content Crawler) |
| Рейтинг/отзывы | 0 (Yandex сломан) | ~95% |
| Точность доменов | ~30% (DomainGuess) | ~95% (Google Maps) |

## Файлы, Которые Будут Затронуты

| Файл | Что меняется |
|------|-------------|
| `AIM/src/aim/services/competitor_matcher.py` | Замена _discover_yandex_maps → _discover_google_maps, удаление DomainGuess, новый merge pipeline |
| `AIM/src/aim/services/yandex_maps_search.py` | ⚠️ УДАЛИТЬ (полная замена) |
| `AIM/src/aim/services/yandex_web_search.py` | ⚠️ УДАЛИТЬ (полная замена) |
| `AIM/src/aim/services/social_discovery.py` | ⚠️ УДАЛИТЬ (заменён на Apify Instagram) |
| `AIM/src/aim/services/apify_client.py` | **НОВЫЙ** — общий клиент Apify с retry/circuit breaker |
| `AIM/src/aim/services/apify_google_maps.py` | **НОВЫЙ** — Google Maps scraper integration |
| `AIM/src/aim/services/apify_website_crawler.py` | **НОВЫЙ** — Website Content Crawler для извлечения услуг |
| `AIM/src/aim/services/apify_instagram.py` | **НОВЫЙ** — Instagram Scraper для соцсетей |
| `AIM/.env.example` | +APIFY_API_TOKEN |
| `AIM/.env.production` | +APIFY_API_TOKEN |

## Requirements (ключевые)

**APIFY-01:** Apify Google Maps заменяет Yandex Maps + OSM как первичный источник конкурентов
**APIFY-02:** Website Content Crawler извлекает реальные услуги с сайтов конкурентов (вместо constructed)
**APIFY-03:** Instagram Scraper извлекает социальные сигналы (followers, bio)
**APIFY-04:** DaData + rusprofile используется только для финансового обогащения
**APIFY-05:** Время поиска < 60s (через параллельные запросы к Apify)
**APIFY-06:** Website есть у 80%+ найденных конкурентов
**APIFY-07:** Старые файлы (yandex_maps_search, yandex_web_search, social_discovery) удалены
**APIFY-08:** Общий ApifyClient с resilience-паттернами (retry, circuit breaker, rate limiting)

## Success Criteria

1. `POST /api/competitors/find` возвращает 3 конкурентов с реальными website и услугами
2. Website есть у >= 80% конкурентов (сейчас ~10%)
3. Услуги извлечены из реальных сайтов, не constructed из OKVED
4. Время ответа < 60 секунд
5. Все старые тесты проходят или заменены
6. Новый ApifyClient покрыт тестами
7. Интеграционный тест: yutskovskaya.ru находит конкурентов с website и реальными услугами
