# Phase 7 Summary — V2 Competitor Pipeline: точность данных

**Дата:** 2026-07-15
**Статус:** ✅ Завершено
**Время выполнения:** 1 сессия

## Что сделано

4 доработки гибридного v2 пайплайна подбора конкурентов (Perplexity + SearXNG + bo.nalog), все протестированы на IPHK:

### COMP-04: Нормализация брендов
- `normalize_brand_name()` в brand_resolver.py — regex убирает гео-привязки
- «Медиал на Ленинском проспекте» → «Медиал» → головное юрлицо
- Паттерны: «на <улица>», «в <переулок>», «метро X», «г. Y», «№N»
- Все 5 тестов прошли

### COMP-01: Резолв ИНН клиента
- `_resolve_client_inn()` — многоуровневый fallback: site scrape → bo.nalog → Perplexity
- IPHK: Perplexity нашёл ИНН 7708698635 → ФНС подтвердила выручку 4.1 млрд (не 80М оценка)
- Коридор 0.1×–10× теперь работает с реальной выручкой

### COMP-02: Instagram enrichment
- **Изначально:** Apify (200с latency) → переписано на **SearXNG** (3с)
- `instagram_enricher.py` — поиск "instagram <бренд> <город>" → сниппеты Google/Bing/DDG содержат и handle, и подписчиков
- SearXNG обходит блокировку Instagram в РФ (клиники не могут ставить ссылки на сайтах)
- 4/5 конкурентов получили IG данные
- Handle-фильтр отсекает домены (.ru, .com) — фикс бага `@iphk.ru`

### COMP-03: Врачи (обобщённо)
- `_enrich_doctors_batch()` — Perplexity оценка для топ-5
- **Обобщено:** «врачи» вместо «хирурги» (клиника может быть любой специализации)
- Sanity check: 1–300 врачей (отсекает галлюцинации типа 752)
- 4/5 конкурентов получили оценку

## Финальный тест (IPHK, 5 конкурентов)

```
#  Конкурент              Выручка   Тренд     Врач  IG
1  Клиника ЛАНЦЕТЪ        4.6 млрд  growing   30    11K
2  Клиника «Атлас»        6.0 млрд  growing   32    ~0
3  Институт ПХ            1.1 млрд  growing   45    -
4  Скандинавия            932 млн   growing   28    47K
5  Фрау Клиник            784 млн   growing   -     32K

Покрытие: Конкурент 5/5 | Выручка 5/5 | ИНН 5/5 | Тренд 5/5 | Врачи 4/5 | Instagram 4/5
Время: ~15с
```

## Трансформация (V1 → V2)

| Параметр | V1 (Google Maps) | V2 (Perplexity+ФНС) |
|---|---|---|
| Источник | Соседи по карте | Бизнес-конкуренты по масштабу |
| Выручка | 0/5 | 5/5 (ФНС) |
| ИНН | 0/5 | 5/5 |
| ОКВЭД | 0/5 | 5/5 |
| Врачи | 0/5 | 4/5 |
| Instagram | 0/5 | 4/5 (SearXNG) |
| Время | 75с | ~15с |

## Файлы

### Новые
- `services/brand_resolver.py` — бренд→ИНН + normalize_brand_name
- `services/competitor_matcher_v2.py` — оркестратор (4 этапа)
- `services/lib/searxng_client.py` — SearXNG клиент
- `services/lib/perplexity_client.py` — Perplexity API для aim-app
- `services/lib/instagram_enricher.py` — IG через SearXNG сниппеты
- `searxng-settings.yml` — SearXNG конфиг

### Модифицированные
- `api/competitors.py` — strategy dispatch, CompetitorJson поля
- `docker-compose.yml` — SearXNG сервис + env vars
- `hermes-v2/tools/competitors.py` — strategy=v2 по умолчанию

## Архитектурные решения

1. **SearXNG для Instagram** (не Apify) — бесплатный, 3с, обходит блокировку РФ
2. **Perplexity для ИНН клиента** — когда site scrape не находит ИНН
3. **«Врачи» не «хирурги»** — обобщение для любой специализации
4. **Коридор 0.1×–10×** — широкий, для крупных и мелких клиентов
5. **Нормализация брендов** — перед bo.nalog резолвом

## Известные ограничения
- Perplexity недетерминирован — иногда perplexity=0 (нужен retry)
- Не тестировалось на немедицинских клиниках и сельских регионах
- SearXNG IG: «0» = аккаунт найден, подписчиков <1000

## Деплой
Код собран в образ `aim:latest`, задеплоен на прод (ssh aim). SearXNG контейнер работает через docker-compose. Откат: `strategy=v1`.
