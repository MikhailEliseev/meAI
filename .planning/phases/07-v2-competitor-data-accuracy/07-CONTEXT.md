# Phase 7: V2 Competitor Pipeline — точность данных - Context

**Gathered:** 2026-07-15
**Status:** Ready for planning
**Source:** Эмпирический тест на IPHK (iphk.ru) + сравнение с эталонной таблицей

<domain>
## Phase Boundary

Доработка гибридного v2 пайплайна подбора конкурентов (Perplexity + SearXNG + bo.nalog), созданного в предыдущей сессии. V2 уже работает (8 конкурентов с ИНН, ОКВЭД, выручкой, трендом за ~8с), но 4 колонки эталонной таблицы требуют доработки.

**Входит в фазу:**
1. Резолв ИНН клиента (для коридора выручки)
2. Instagram-колонка (подписчики)
3. Число хирургов (дообогащение)
4. Нормализация брендов (убрать гео-привязки)

**Не входит:**
- Переписывание v2 архитектуры (уже работает)
- Изменение чат-UI (не трогаем golden state)
- Новые источники данных (источники определены)

</domain>

<decisions>
## Implementation Decisions

### D1: Резолв ИНН клиента — многоуровневый fallback
ИНН клиента критичен: без него коридор выручки (0.3×–3×) не работает, и конкуренты отбираются «топ по размеру» вместо «ближайшие по масштабу».

Цепочка (попытка в порядке, первая удачная выигрывает):
1. Скрапинг сайта (footer/privacy/оферта) — `_extract_inn` уже есть в service_extractor.py
2. bo.nalog search по company_name с сайта
3. Perplexity: «какой ИНН у клиники X» → bo.nalog валидация (анти-галлюцинация)
4. Если всё失败 → fallback на оценку (текущее поведение)

**Locked:** использовать существующий `_extract_inn` + `resolve_brand_to_inn` для клиента.

### D2: Instagram — Apify для топ-5 только
Instagram enrichment медленный (Apify ~5-10с на профиль). Делаем только для финального топ-5, после сортировки.

Цепочка:
1. Скрапинг сайта конкурента → найти IG ссылку (instagram.com/<handle>)
2. Если нет на сайте → Perplexity «instagram <бренд>»
3. Apify `instagram-profile-scraper` → followersCount
4. Заполнить `instagram_followers`, `instagram_handle` в CompetitorJson

**Locked:** Apify инструмент `run_instagram_content` уже есть в hermes-v2. Для aim-app нужен свой Apify клиент (ключи в /opt/data/apify_keys.json).

### D3: Хирурги — Perplexity + скрапинг fallback
Текущее состояние: Perplexity даёт `surgeons_estimate` в этапе 1, но не всегда. Для топ-5 без оценки:
1. Perplexity запрос: «сколько врачей/хирургов в клинике <бренд>»
2. Скрапинг раздела «Врачи/Команда/О нас» → подсчёт карточек

**Locked:** минимальный Perplexity запрос для топ-5 (не для всех).

### D4: Нормализация брендов — regex перед резолвом
Perplexity возвращает бренды с гео-привязками: «Медиал на Ленинском проспекте», «ЕМС в Орловском переулке». Это отделения, не бренды. bo.nalog по таким названиям находит мелкие юрлица.

Нормализация (до резолва brand→INN):
- Убрать: «на <улица>», «на <проспект>», «в <переулок>», «<№N>», «<адрес>», «<метро>»
- «Медиал на Ленинском проспекте» → «Медиал»
- «ЕМС в Орловском переулке» → «ЕМС»
- «ОН Клиник на Таганке» → «ОН Клиник»

**Locked:** regex-фильтр в brand_resolver.py или в competitor_matcher_v2.py перед этапом 2.

### D5: Где живёт код
Все изменения в aim-app (не hermes-v2):
- `services/competitor_matcher_v2.py` — оркестратор (этап 0 доработка)
- `services/brand_resolver.py` — нормализация + резолв
- `services/lib/perplexity_client.py` — Perplexity для ИНН/хирургов
- НОВЫЙ: `services/lib/instagram_enricher.py` — Apify IG client для aim-app

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Существующий код (база для доработки)
- `AIM/src/aim/services/competitor_matcher_v2.py` — v2 оркестратор (этап 0, 1, 2, 3)
- `AIM/src/aim/services/brand_resolver.py` — бренд → ИНН через bo.nalog
- `AIM/src/aim/services/lib/perplexity_client.py` — Perplexity API клиент
- `AIM/src/aim/services/lib/searxng_client.py` — SearXNG клиент
- `AIM/src/aim/services/nalog/bfo_client.py` — ФНС финансовый клиент (BfoNalogClient)
- `AIM/src/aim/services/service_extractor.py` — `_extract_inn`, `extract_client_profile`
- `AIM/src/aim/api/competitors.py` — API endpoint (strategy dispatch, CompetitorJson)

### Instagram (в hermes-v2, паттерн для копирования)
- `AIM/hermes-v2/app/tools/run_instagram_content.py` — Apify IG scraper (handle → followers)
- `AIM/hermes-v2/app/lib/apify_client.py` — Apify client с key rotation

### Apify ключи
- `/opt/data/apify_keys.json` на сервере — пул ключей (status=active)

</canonical_refs>

<specifics>
## Specific Ideas

### Эталонная таблица (целевой результат)
| Конкурент | Выручка | Тренд | Хирургов | Instagram |
|---|---|---|---|---|
| ИПХиК | 4.3 млрд | +79% (3 года) | 150+ | ~587K |
| Seline | 2.3 млрд | +19.1% | 10+ | 27K |
| GMTClinic | 742 млн | Стабильный | 8+ | 31K |
| Фрау Клиник | 137 млн | -15.1% | 5+ | ~8K |

### Текущие пробелы (из теста IPHK)
1. `company=None inn=None` — профиль клиента не извлечён → выручка = оценка
2. `surgeons_count=None` у части конкурентов (Perplexity не дал оценку)
3. `instagram_followers=None` у всех (Instagram enrichment не реализован)
4. «Медиал на Ленинском проспекте» → резолвится к мелкому юрлицу (3 млн вместо головного)

### Промпт Perplexity для ИНН клиента
```
Найди ИНН клиники: {company_name}, {city}, сайт {url}
Верни ТОЛЬКО число (10-12 цифр) или null.
```

</specifics>

<deferred>
## Deferred Ideas

- Рейтинги и отзывы (Google Maps/Yandex) — сейчас не в эталонной таблице, можно добавить позже
- Скрапинг цен конкурентов — отдельная задача
- Автоматическое определение специализации через ОКВЭД → категории услуг

</deferred>

---

*Phase: 07-v2-competitor-data-accuracy*
*Context gathered: 2026-07-15 via эмпирический тест + эталонная таблица*
