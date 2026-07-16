# Phase N: Competitor Intelligence — Consumer Signals

**Status:** PLAN  
**Priority:** P0 (после Pre-Sale v2)  
**Estimated:** 2–3 дня

## Problem

Сейчас система отвечает на вопрос «кто существует?»:
- **Tier 1 (DaData):** юридические лица с OKVED 86.X
- **Tier 2 (OSM):** физические точки на карте

Но не отвечает на «куда реально ходят люди?» и «что о них говорят?». Выдача реестра ≠ рыночная реальность.

## Goal

Добавить потребительские сигналы в конкурентный анализ:
1. **Popularity** — куда ходят (рейтинги, отзывы, поисковая выдача)
2. **Sentiment** — что говорят (NLP-анализ отзывов: цены, сервис, боль)
3. **Visibility** — кого видят (organic search, карточки организаций)
4. **Trending** — кто растёт/падает (мониторинг изменений)

## Architecture

```
Tier 1: DaData           → юридическое существование + финансы
Tier 2: OpenStreetMap    → физическое присутствие + координаты
Tier 3: Yandex Maps      → рейтинг + отзывы + популярность  🆕
Tier 4: 2GIS             → региональный охват + филиалы     🆕
Tier 5: Search Visibility → поисковая выдача (Яндекс)       🆕
Tier 6: Review NLP        → анализ текстов отзывов           🆕
Tier 7: Review Monitoring → отслеживание изменений           🆕

                      ┌─ Merge & Deduplicate ─┐
                      │  (name + coordinates   │
                      │   + phone cross-ref)   │
                      └──────────┬─────────────┘
                                 ↓
                      ┌─ Enriched Competitor ─┐
                      │  • legal (DaData)      │
                      │  • physical (OSM)      │
                      │  • popularity (Yandex) │
                      │  • sentiment (NLP)     │
                      │  • visibility (Search) │
                      └────────────────────────┘
```

## Scoring (updated weights)

```
revenue_match    × 0.20  (↓ 0.35)
location_score   × 0.15  (↓ 0.25)
service_overlap  × 0.15  (↓ 0.25)
data_quality     × 0.10  (↓ 0.15)
popularity       × 0.25  (🆕 — рейтинг + отзывы)
  ├─ rating_score  (0.6) — средняя оценка (2ГИС + Яндекс)
  └─ review_score  (0.4) — количество отзывов (log-шкала)
visibility       × 0.15  (🆕 — поисковая выдача)
  ├─ serp_position (0.5) — позиция в выдаче по ключевым запросам
  └─ maps_presence (0.5) — наличие карточки организации
```

### Popularity formula

```python
# Нормализация рейтинга: 3.0 → 0.0, 5.0 → 1.0
rating_score = max(0.0, (org.avg_rating - 3.0) / 2.0)

# Количество отзывов: log-шкала (10 ≠ 100 ≠ 1000)
review_score = min(log(org.reviews_count + 1) / log(200), 1.0)

popularity = 0.6 * rating_score + 0.4 * review_score
```

## Sub-Phase 1: Yandex Maps Integration (Tier 3)

**API:** Yandex Maps HTTP API (search-maps.yandex.ru)  
**Key:** Бесплатный, 25K запросов/день  
**Endpoint:** `GET /v1/?text=стоматология+город&type=biz&lang=ru_RU`

**Данные с Яндекс.Карт:**

| Сигнал | Поле API | Вес в scoring |
|--------|----------|---------------|
| Рейтинг | `rating` (1.0–5.0) | 60% popularity |
| Количество отзывов | `reviews_count` | 40% popularity |
| Категория | `categories[]` | cross-ref с specialization |
| Координаты | `geometry` | cross-ref с OSM |
| Адрес | `address` | cross-ref с DaData |
| Телефон | `phone` | dedup key |
| Сайт | `url` | enrichment |
| Часы работы | `hours` | сигнал активности |
| Фото | `photos_count` | сигнал активности |

**Cross-reference стратегия:**
```
Yandex org → match by name + coords (<200m) → OSM place
           → match by name + city → DaData company
           → match by phone → any existing candidate
```

## Sub-Phase 2: 2GIS Integration (Tier 4)

**API:** 2GIS Catalog API (api.2gis.ru)  
**Key:** Бесплатный, 1000 запросов/день  

Особенно силён в регионах (за пределами МСК/СПБ). Часто имеет более полные данные по медицинским организациям чем Яндекс.

## Sub-Phase 3: Search Visibility (Tier 5)

**Запросы:** «стоматология + город», «лечение зубов + город», «имплантация + город»  
**Источник:** Яндекс.Search (через SerpAPI или Playwright)

**Сигналы:**
- Позиция в органической выдаче (топ-3, топ-10)
- Наличие карточки организации (knowledge panel)
- Сниппеты (рейтинг в выдаче, часы работы)
- Рекламные объявления (кто платит за Директ)

## Sub-Phase 4: Review NLP (Tier 6)

**Источники:** Яндекс.Карты, 2GIS, ПроДокторов, СберЗдоровье  
**Модель:** DeepSeek V4 Pro (через OmniRoute) — summarization, не классификация

**Что извлекаем:**

| Тема | Примеры | Сигнал для клиента |
|------|---------|-------------------|
| Цены | «дорого», «дёшево», «цены выросли» | Ценовое позиционирование |
| Сервис | «вежливый администратор», «очередь» | Качество обслуживания |
| Врачи | «хороший врач», «грубый» | Репутация специалистов |
| Оборудование | «старое», «новый томограф» | Тех. оснащение |
| Боль | «больно», «без боли» | Комфорт процедур |
| Чистота | «грязно», «стерильно» | Санитарные стандарты |
| Запись | «не дозвониться», «онлайн запись» | Удобство записи |

**Формат вывода (NLP summary per competitor):**
```json
{
  "clinic": "Стоматология Стар",
  "review_count": 200,
  "avg_rating": 4.7,
  "themes": {
    "pricing": {"sentiment": "neutral", "mentions": 15, "summary": "Цены средние по рынку"},
    "service": {"sentiment": "positive", "mentions": 45, "summary": "Хвалят администраторов"},
    "doctors": {"sentiment": "positive", "mentions": 60, "summary": "Врач Иванов — звезда"},
    "equipment": {"sentiment": "positive", "mentions": 12, "summary": "Новый томограф"},
    "pain": {"sentiment": "positive", "mentions": 30, "summary": "Лечат без боли"}
  },
  "competitive_insight": "Сильный сервис + врачи. Слабое место — цены (15 жалоб). Растут."
}
```

## Sub-Phase 5: Review Monitoring (Tier 7)

**Частота:** Каждые 2 недели (cron)  
**Хранилище:** `AIM/data/competitor_monitoring/{city}/{clinic}.json`

**Что отслеживаем:**
- Δ rating (растёт/падает)
- Δ review_count (много новых отзывов = активность)
- Новые темы в отзывах (внезапный негатив про врача)
- Новые конкуренты (появился кто-то с кучей отзывов)

**Алерты:**
- Конкурент набрал +50 отзывов за месяц → 🔴 активно растёт
- Рейтинг упал на 0.3+ → 🟡 проблемы у конкурента (окно возможностей)
- Новый конкурент с рейтингом 4.8+ → 🔴 угроза

## Implementation Order

1. **Yandex Maps client** (2h) — Tier 3, максимальный ROI
2. **Popularity scoring** (1h) — rating + reviews в формулу
3. **Cross-reference engine** (2h) — Yandex ↔ OSM ↔ DaData по имени/координатам/телефону
4. **2GIS client** (1.5h) — Tier 4, региональный охват
5. **Search visibility** (2h) — Яндекс.Search organic + карточки
6. **Review NLP** (3h) — DeepSeek summarization тем отзывов
7. **Review monitoring** (2h) — cron + алерты + хранилище

## Success Metrics

- Топ-3 конкурентов имеют реальные отзывы и рейтинги
- Popularity score различает конкурентов с одинаковыми OKVED
- NLP выдаёт минимум 3 темы на конкурента
- Мониторинг ловит изменения за ≤ 2 недели

## API Keys Required

| Сервис | Где получить | Стоимость |
|--------|-------------|-----------|
| Yandex Maps | developer.tech.yandex.ru | Бесплатно (25K/день) |
| 2GIS | api.2gis.ru | Бесплатно (1K/день) |
| SerpAPI | serpapi.com | $50/мес (для Яндекс.Search) |

## Integration Points

- `competitor_matcher.py` — новый Tier 3-7 discovery + updated scoring
- `yandex_maps.py` — async HTTP client
- `dgis_client.py` — async HTTP client
- `review_nlp.py` — NLP summarization via OmniRoute
- `search_visibility.py` — Яндекс.Search scraping
- `review_monitor.py` — cron-based monitoring
- `cross_reference.py` — multi-source dedup engine
