# Session: 2026-05-26

## Phase 20: Apify-Based Competitor Intelligence — COMPLETED ✅

**Date:** 2026-05-25/26 GMT+3
**Status:** Все 6 задач выполнены, полная замена Yandex/OSM/DomainGuess на Apify Google Maps

### Выполненные задачи

#### Task 1: ApifyClient ✅
- `AIM/src/aim/services/apify_client.py` — общий клиент с circuit breaker (5 failures → open 60s), retry с exponential backoff (3 попытки, базовый delay 2s), rate limiting
- Синглтон: `get_apify_client()`
- Исправлен импорт: `apify_client.errors.ApifyApiError` (v3.0.1)

#### Task 2: Google Maps Scraper ✅
- `AIM/src/aim/services/apify_google_maps.py` — `discover_competitors_google_maps()`
- Поиск через `compass/crawler-google-places` с `searchStringsArray`
- Маппит результаты в `CompanyProfile` (website, rating, reviews, social_links, geo_lat/lon)
- Подтверждено: 100% website coverage для российских медклиник

#### Task 3: Прямой скрапинг услуг ✅
- `AIM/src/aim/services/scraping_service.py` — httpx+BeautifulSoup скрапер
- 60+ ключевых слов для российских медуслуг
- `scrape_services(url)` и `scrape_services_batch(urls)`
- Замена Apify Website Content Crawler (OOM на бесплатном тарифе)
- Добавлен `extract_social_links()` + `SOCIAL_DOMAINS` (из social_discovery.py)

#### Task 4: Переписан CompetitorMatcher ✅
- Новый Apify-first pipeline: `find_competitors()` → Google Maps → DaData enrichment → scraping → rusprofile → Score
- Удалены старые методы: `_search_osm_candidates`, `_search_yandex_candidates`, `_lookup_osm_on_dadata`, `_lookup_yandex_on_dadata`, `_merge_candidates`
- Удалены OSM-хелперы: `_AMENITY_PRIORITY`, `_filter_osm_by_specialization`, `_AMENITY_OKVED_MAP`, `_osm_amenity_to_okved`, `_format_osm_address`
- Удалена `_verify_website`
- Обновлена `_score_visibility` для apify_google_maps (0.85) и apify_google_maps+dadata (0.95)
- 1769 строк (было 2593)

#### Task 5: Удаление старых файлов ✅
- ❌ `yandex_maps_search.py` — удалён
- ❌ `yandex_web_search.py` — удалён
- ❌ `yandex_maps.py` — удалён
- ❌ `social_discovery.py` — удалён (`extract_social_links` перемещён в scraping_service.py)
- `ci_marketing_analysis.py` — импорт обновлён на scraping_service

#### Task 6: Валидация ✅
- Все импорты чисты
- `_score_visibility` корректно обрабатывает новые data_source
- `_dedup_candidates` работает
- `extract_social_links` работает из scraping_service
- `.env.example` — добавлен `APIFY_API_TOKEN`

### Новый пайплайн

```
Client URL → service_extractor.py → CompetitorMatcher
                ↓                        ↓
         specialization          1. Apify Google Maps (основной)
         city                    2. DaData (только INN/финансы)
         services                3. scraping_service.py (услуги)
                                 4. rusprofile (финансовые данные)
                                 ↓
                           Merge + Score → top-3
```

### Новые файлы
- `AIM/src/aim/services/apify_client.py`
- `AIM/src/aim/services/apify_google_maps.py`
- `AIM/src/aim/services/scraping_service.py`

### Изменённые файлы
- `AIM/src/aim/services/competitor_matcher.py` — полная переработка (2593 → 1769 строк)
- `AIM/src/aim/services/ci_marketing_analysis.py` — импорт из scraping_service
- `AIM/.env.example` — +APIFY_API_TOKEN

### Удалённые файлы
- `AIM/src/aim/services/yandex_maps_search.py`
- `AIM/src/aim/services/yandex_web_search.py`
- `AIM/src/aim/services/yandex_maps.py`
- `AIM/src/aim/services/social_discovery.py`

### Next Steps
- [ ] Деплой на продакшен (138.16.224.188)
- [ ] Добавить APIFY_API_TOKEN в `.env.production`
- [ ] Интеграционный тест: yutskovskaya.ru через Apify Google Maps
- [ ] Проверить баланс Apify
