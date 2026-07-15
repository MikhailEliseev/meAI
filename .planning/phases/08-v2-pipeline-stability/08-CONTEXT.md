# Phase 8: V2 Pipeline — стабильность и покрытие - Context

**Gathered:** 2026-07-15
**Status:** Ready for planning
**Source:** Тесты IPHK из Phase 7, наблюдение недетерминированности Perplexity

<domain>
## Phase Boundary

Доработка v2 пайплайна для стабильности и надёжности. Pipeline работает (Phase 7), но результаты варьируются между запусками из-за недетерминированности Perplexity.

**Входит в фазу:**
1. Retry при пустом Perplexity (главная проблема — иногда 0 брендов)
2. Overfetch кандидатов (12 брендов → топ-5 после резолва)
3. Кэш bo.nalog (быстрый повторный запрос)
4. Дедуп сетей (многоточные клиники с одним ИНН)

**Не входит:**
- Новые источники данных
- Изменение архитектуры pipeline
- UI/UX чата (golden state)

</domain>

<decisions>
## Implementation Decisions

### D1: Retry стратегия для Perplexity
Perplexity иногда возвращает 0 брендов (видели в логах: `perplexity=0`). Это не ошибка API — LLM просто не сформировал ответ.

Решение: до 2 retry с разными подходами:
1. Попытка 1: основной промпт (текущий COMPETITOR_DISCOVERY_PROMPT)
2. Попытка 2 (если 0 брендов): упрощённый промпт — «Назови 12 самых известных клиник {specialization} в {city}»
3. Если 0 после retry → SearXNG-only (уже работает, находит 6-8 брендов)

**Locked:** retry в `_discover_via_perplexity`, не в оркестраторе.

### D2: Overfetch — 12 кандидатов вместо 10
Запрашиваем 12 брендов у Perplexity (в промпте), SearXNG limit=20.
После merge+dedup+resolve остаётся ~8-10 валидных → берём топ-5.
Если резолвится <5 → расширяем коридор (уже 0.1×–10×, дальше — все с выручкой).

**Locked:** изменить число в промпте и searxng limit.

### D3: Кэш — уже работает, проверить
BfoNalogClient уже имеет in-memory кэш (TTL 3600с, key=search:{query}).
Проблема: новый BfoNalogClient() создаётся на каждый запрос → кэш теряется.

Решение: сделать BfoNalogClient singleton (как DaDataClient — `get_nalog_client()`).
Тогда повторный IPHK → кэш-хиты → <5с.

**Locked:** singleton паттерн, не per-request instance.

### D4: Дедуп сетей
Phase 7 добавил `_dedup_by_inn` — уже работает (СМ-Клиника Волгоградский и Сенежская → одна запись).
Нужно: проверить что дедуп срабатывает consistently + логировать когда дубли найдены.

Дополнительно: если бренд один но ИНН разные (разные юрлица одной сети) — оставить обе, но добавить в match_reason «сеть: <бренд>».

**Locked:** дедуп по ИНН уже есть, добавить логирование + бренд-дедуп опционально.

</decisions>

<canonical_refs>
## Canonical References

### Существующий код (база для доработки)
- `AIM/src/aim/services/competitor_matcher_v2.py` — `_discover_via_perplexity`, `_discover_via_searxng`, pipeline
- `AIM/src/aim/services/brand_resolver.py` — `resolve_brands_batch`, `_dedup_by_inn`
- `AIM/src/aim/services/nalog/bfo_client.py` — кэш (`_cache`, `_cache_ttl`), rate limiter
- `AIM/src/aim/services/rusprofile/client.py` — паттерн singleton (`get_dadata_client()`)

</canonical_refs>

<specifics>
## Specific Ideas

### Наблюдения из тестов IPHK (Phase 7)
- Запуск 1: perplexity=0 (пусто), searxng=2 → только 2 конкурента
- Запуск 2: perplexity=10, searxng=6 → 8 уникальных → 5 после фильтра
- Запуск 3: perplexity=8, searxng=8 → 8 уникальных → 5 после фильтра
- Время: 11-15с (варьируется)

### Retry промпт (упрощённый)
```
Назови 12 самых известных клиник {specialization} в {city}.
Только названия, по одному на строку. Без объяснений.
```

### Singleton паттерн (из DaDataClient)
```python
_nalog_client: BfoNalogClient | None = None

def get_nalog_client() -> BfoNalogClient:
    global _nalog_client
    if _nalog_client is None:
        _nalog_client = BfoNalogClient()
    return _nalog_client
```

</specifics>

<deferred>
## Deferred Ideas

- A/B тестирование промптов (какой даёт больше релевантных брендов)
- Сохранение результатов в БД (Redis) для аналитики
- Метрики качества (precision/recall vs эталон)

</deferred>

---

*Phase: 08-v2-pipeline-stability*
*Context gathered: 2026-07-15 via наблюдения из Phase 7 тестов*
