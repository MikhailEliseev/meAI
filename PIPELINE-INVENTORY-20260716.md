# Инвентаризация Competitors V2 Pipeline (2026-07-16)

> Полная карта: что есть, что работает, что отваливается, что грузит систему.
> Основа для решений «урезать / перенести на другие фазы / оптимизировать».

---

## 🏗️ Архитектура Pipeline (6 этапов)

```
Stage 0: Client profile + ИНН + revenue
    ↓
Stage 1: Discover brands (Perplexity 3 промпта ‖ SearXNG)
    ↓
Stage 2: Resolve brands → ИНН (brand_resolver, 4 уровня)
    ↓
Stage 3: Enrich ФНС financials + revenue corridor filter + top-N
    ↓
Stage 3.5a: Backfill из ОКВЭД-реестра (если < count)
    ↓
Stage 3.5b: Post-selection enrichment (doctors ‖ Instagram ‖ website)  ← ВСЕ ПАРАЛЛЕЛЬНО
    ↓
Stage 3.5c: CLIENT audit (SEO/GEO + Firecrawl + doctors)
```

---

## 📊 Этап: что делает, источники, время, статус

### Stage 0 — Client Profile + ИНН + Revenue
| Аспект | Детали |
|--------|--------|
| **Что делает** | Extract client profile (specialization, city, company_name); resolve client ИНН; get real revenue from ФНС |
| **Источники** | `extract_client_profile()` (Firecrawl scrape сайта клиента) → `brand_resolver` → `bo.nalog` |
| **Время** | ~10-15s |
| **Статус** | ✅ Работает. Revenue из ФНС достаётся. |
| **Проблемы** | `client_employee_count: null` (СЧЛ не всегда отдаётся ФНС); `client_doctors: null` (scrape_doctors не находит для JS-heavy сайтов) |

### Stage 1 — Discover Brands
| Аспект | Детали |
|--------|--------|
| **Что делает** | 2 канала параллельно: Perplexity (3 промпта × limit 20) + SearXNG |
| **Источники** | Perplexity `sonar` (API) ‖ SearXNG (мёртв!) |
| **Время** | ~15-20s |
| **Статус** | ⚠️ Perplexity работает (даёт ~20-25 брендов), **SearXNG мёртв** (0 результатов, но не блокирует — fallback) |
| **Проблемы** | Perplexity недетерминирован (каждый прогон — разные бренды); 3 промпта частично компенсируют |

### Stage 2 — Resolve Brands → ИНН
| Аспект | Детали |
|--------|--------|
| **Что делает** | Каждый бренд → юридическое лицо → ИНН. 4 уровня резолва. |
| **Уровни** | L1: `bo.nalog` search → L2: Firecrawl scrape website → ИНН из страницы → L3: Perplexity → L4: fallback |
| **Время** | ~20-40s (max_brands=40, semaphore=15) |
| **Статус** | ✅ Работает после фикс. toriclinic: resolved 21/44 брендов (23 rejected) |
| **Проблемы** | L2 (Firecrawl scrape) — самый тяжёлый и медленный. Для 5 unresolved брендов = 5× scrape. Это точка оптимизации. |

### Stage 3 — ФНС Enrichment + Filter
| Аспект | Детали |
|--------|--------|
| **Что делает** | `get_financials` (revenue, profit, trend) + `get_organization` (reg_date, scl_count) для каждого. Revenue corridor filter (0.3×–3× клиента). |
| **Источники** | `bo.nalog` (get_financials, get_organization) |
| **Время** | ~20-30s |
| **Статус** | ✅ Работает. Все конкуренты получают выручку/прибыль/тренд/рег.дату. |
| **Проблемы** | `scl_count` (СЧЛ) = null у многих (ФНС не отдаёт для части компаний). `geo_lat/lon: null` (не извлекается). |

### Stage 3.5a — Backfill из ОКВЭД-реестра
| Аспект | Детали |
|--------|--------|
| **Что делает** | Если Perplexity дал < count конкурентов — добирает из bo.nalog по ОКВЭД 86.xx + регион |
| **Когда срабатывает** | Почти всегда для count=10 (Perplexity даёт ~20, но после corridor filter остаётся мало) |
| **Время** | ~10-20s |
| **Статус** | ⚠️ Работает, но даёт **географически нерелевантные** результаты |
| **🔴 КРИТИЧЕСКАЯ ПРОБЛЕМА** | toriclinic (Москва): 9 из 10 конкурентов из backfill — **Томск, Брянск, Геленджик, Барнаул, Липецк, Самара, Ессентуки**. Регион=77 (Москва) в запросе, но companies из других регионов проходят. **Нет жёсткой геофильтрации.** |

### Stage 3.5b — Post-Selection Enrichment (3 параллельно)
| Подэтап | Что делает | Источник | Время | Статус |
|---------|-----------|----------|-------|--------|
| **doctors** | Perplexity: «сколько врачей в клинике X» | Perplexity | ~10-15s | ⚠️ Только для top-N без employee_count. 4/10 filled. |
| **Instagram** | handle → followers (SearXNG → Firecrawl → Apify) | Apify IG scraper | ~20-30s | ⚠️ 6/10 filled. Fallback chain сложный. |
| **website** | CMS, размер, страницы, соцсети | Firecrawl scrape | ~30-50s | 🔴 **Самый тяжёлый этап**. 10 конкурентов × scrape = долго. |

**Firecrawl счёт scrape-запросов за один pipeline (toriclinic, 172s):**
- Stage 0: 1 (client site)
- Stage 3.5b website: ~10-15 (competitor sites + searches)
- Stage 3.5c client: 2-3 (audit + doctors + socials)
- **Итого: ~15-20 Firecrawl scrape запросов** ← основная нагрузка

### Stage 3.5c — Client Audit
| Аспект | Детали |
|--------|--------|
| **Что делает** | GEO Score, AI crawlers, Schema, llms.txt, CMS, robots.txt, VK followers, Yandex rating, media mentions |
| **Источники** | Firecrawl (1 scrape сайта) + httpx (robots.txt) |
| **Время** | ~10-15s |
| **Статус** | ✅ Работает хорошо. toriclinic: GEO=55, yandex=5.0★ (681 отзывов), VK=456, CMS=OpenCart |
| **Проблемы** | `client_doctors: null` (scrape_doctors fails on JS sites). media_mentions=0 (не всегда находит). |

---

## 🔌 Источники данных — статус

| Источник | Назначение | Статус | Примечание |
|----------|-----------|--------|------------|
| **Perplexity `sonar`** | Brand discovery, doctors estimate | ✅ Работает | Недетерминирован. 3 промпта + limit 20 |
| **bo.nalog.gov.ru** | ФНС: revenue, profit, org data, ОКВЭД search | ✅ Работает | Основа pipeline. scl_count не у всех |
| **Firecrawl** (15 ключей) | Scrape сайтов: CMS, socials, doctors | ⚠️ Перегружен | ~15-20 запросов/pipeline. 500 errors. TTL 1h recovery |
| **Apify IG scraper** | Instagram followers | ✅ Работает | 14 ключей. Fallback после SearXNG/Firecrawl |
| **SearXNG** | Web search (brands + IG discovery) | ❌ МЁРТВ | 0 результатов. Не блокирует (fallback). Контейнер жив, но не отдаёт. |

---

## 📋 Поля данных — что заполняется, что пустое

### Client (торикlinik тест)
| Поле | Значение | Статус |
|------|----------|--------|
| revenue | 1,223,000 ₽ | ✅ ФНС |
| profit | 685,000 ₽ | ✅ ФНС |
| cms | OpenCart | ✅ Firecrawl |
| GEO score | 55/100 | ✅ seo_auditor |
| yandex_rating | 5.0 (681 отзывов) | ✅ seo_auditor |
| vk_followers | 456 | ✅ seo_auditor |
| AI crawlers | 7/7 открыты | ✅ seo_auditor |
| socials (IG/VK/TG) | Все найдены | ✅ Firecrawl |
| registration_date | 2024-03-21 | ✅ ФНС |
| **doctors** | **null** | ❌ scrape_doctors fails |
| **employee_count** | **null** | ❌ ФНС не отдаёт sclCount |
| **media_mentions** | 0 | ⚠️ Не находит |

### Competitors (10 шт, toriclinic тест)
| Поле | Заполнено | Статус |
|------|-----------|--------|
| revenue_year | 10/10 | ✅ |
| profit_year | 10/10 | ✅ |
| revenue_trend | 10/10 | ✅ growing/declining |
| registration_date | 10/10 | ✅ |
| okved_main | 10/10 | ✅ |
| instagram_followers | 6/10 | ⚠️ |
| instagram_handle | 6/10 | ⚠️ |
| website_cms | 8/10 | ⚠️ |
| socials (vk/tg) | 5/10 | ⚠️ |
| employee_count | 4/10 | ⚠️ Perplexity estimate |
| **rating** | **0/10** | ❌ Всегда null |
| **reviews_count** | **0/10** | ❌ Всегда null |
| **geo_lat/lon** | **0/10** | ❌ Всегда null |
| **services** | **0/10** | ❌ Всегда [] |
| **website** | 7/10 | ⚠️ 3 без сайта (rusprofile ссылки) |

---

## ⏱️ Профиль времени (toriclinic, 172s)

| Этап | Время (оценка) | % от общего |
|------|----------------|-------------|
| Stage 0 (client) | ~15s | 9% |
| Stage 1 (discovery) | ~20s | 12% |
| Stage 2 (resolve 44→40) | ~30s | 17% |
| Stage 3 (ФНС enrich + filter) | ~25s | 15% |
| Stage 3.5a (backfill ОКВЭД) | ~15s | 9% |
| **Stage 3.5b (doctors+IG+website)** | **~45s** | **26%** ← самая тяжёлая |
| Stage 3.5c (client audit) | ~15s | 9% |
| Прочее (сеть, dedup, filter) | ~7s | 4% |

**Главный пожиратель времени: Firecrawl scrape** (~15-20 запросов за pipeline).

---

## 🔴 Топ-5 проблем (по влиянию на результат)

### 1. Географическая нерелевантность конкурентов
**Симптом:** toriclinic (Москва) → конкуренты из Томска, Брянска, Барнаула.
**Причина:** Backfill из ОКВЭД-реестра фильтрует по region=77, но компании с другими регионами в адресе проходят. Нет жёсткой geo-валидации после выборки.
**Влияние:** Огромное — конкуренты физически не конкуренты.

### 2. rating / reviews_count / geo — всегда null
**Симптом:** Ни у одного конкурента нет рейтинга, отзывов, координат.
**Причина:** Эти поля **нигде не enrich'ятся** в pipeline. Нет источника данных для рейтинга конкурентов. (F9 — Yandex rating через Firecrawl — провалилась: 404 от Yandex).
**Влияние:** Большое — клиент видит пустые колонки.

### 3. services = [] всегда
**Симптом:** Услуги пустые у всех.
**Причина:** Поле существует в модели, но **никогда не заполняется**. Нет extraction из сайтов.
**Влияние:** Среднее — нет детализации по услугам.

### 4. Firecrawl — bottleneck и нестабильность
**Симптом:** ~15-20 scrape запросов за pipeline; 500 errors (с retry 3×); ~45s на Stage 3.5b.
**Причина:** Каждый конкурент = 1-2 scrape (website find + scrape). Budget=5, но count=10.
**Влияние:** Время (26% pipeline) + риск таймаутов.

### 5. Perplexity недетерминирован
**Симптом:** Каждый прогон — разные бренды (только 2/15 совпадают между прогонами).
**Причина:** LLM temperature, даже 3 промпта не гарантируют стабильность.
**Влияние:** Воспроизводимость — клиент может увидеть разных конкурентов при перезапуске.

---

## ✅ Что хорошо работает (НЕ ТРОГАТЬ)

1. **ФНС financials** — revenue/profit/trend/registration_date у всех
2. **UnifiedKeyPool** — 14 Apify + 15 Firecrawl ключей, ротация, TTL recovery
3. **Анти-галлюцинация** — таблицы из кода, raw JSON скрыт от LLM
4. **GEO/SEO аудит клиента** — 14 метрик, GEO Score, AI crawlers, Schema
5. **Instagram fallback chain** — SearXNG → Firecrawl → Apify (6/10 filled)
6. **Revenue corridor filter** — релевантность по выручке
7. **Dedup by ИНН** с confident-resolve (имя → legal name overlap)
8. **Related entity filter** — фильтр дочерних компаний клиента
