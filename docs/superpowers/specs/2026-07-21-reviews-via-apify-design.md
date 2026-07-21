# Spec: Отзывы через Apify (замена Perplexity для run_review_platforms)

**Дата:** 2026-07-21
**Статус:** Approved
**Подход:** B (гибрид) — отзывы на Apify, остальное Perplexity остаётся

---

## Контекст и проблема

**Главная боль (по словам пользователя):** Perplexity даёт бесполезный вывод в блоке отзывов — рейтинги и кол-во отзывов галлюцинируются (4.9 вместо 4.2, «отзывов 681» когда их 12), общие фразы вместо конкретики. $50 потрачено на API без удовлетворительного результата.

**Корень проблемы:** Perplexity — LLM-поисковик, он угадывает рейтинги по веб-фрагментам. Но рейтинги/отзывы — это структурированные данные на конкретных площадках (Яндекс.Карты, 2ГИС, ПроДокторов). LLM-поиск — неправильный инструмент для этой задачи. Нужны прямые скраперы.

**Дополнительный фактор:** Perplexity quota исчерпана с 17 июля 23:59 (401 на всех Perplexity-тулах). Отзывы сейчас вообще не работают.

---

## Решение

Переписать `run_review_platforms.py`: вместо вызова Perplexity → параллельный вызов 2 Apify actors через существующий `UnifiedKeyPool` (14 ключей уже есть в `/opt/aim-keys/apify.json`).

**Остальные Perplexity-тулы НЕ трогаем:** `quick_overview`, `extract_clinic_profile`, `perplexity_search`, `run_smi_mentions` остаются на Perplexity (там веб-поиск уместен).

---

## Data flow

```
Клиент: URL клиники (например arclinic.ru)
  │
  ├─ extract_clinic_profile (Perplexity, БЕЗ ИЗМЕНЕНИЙ)
  │   → {company_name: "ARclinic", city: "Санкт-Петербург", inn: "...", ...}
  │     ↑ auto-inject в run_review_platforms через profile_cache (уже работает)
  ↓
run_review_platforms(company_name="ARclinic", city="Санкт-Петербург", url="arclinic.ru")
  │
  ├─ asyncio.gather:
  │   ├─ yandex_reviews.search("ARclinic, Санкт-Петербург")
  │   │    → Apify zen-studio/yandex-maps-reviews-scraper
  │   │    → {rating: 4.2, reviews_count: 47, reviews: [...], address: "..."}
  │   │
  │   └─ gis2_reviews.search("ARclinic, Санкт-Петербург")
  │        → Apify m_mamaev/2gis-places-scraper
  │        → {rating: 4.5, reviews_count: 23, address: "..."}
  │
  ↓
result: {
  "yandex": {"rating": 4.2, "reviews": 47, "praise": [...из текстов...], "criticism": [...]},
  "twogis": {"rating": 4.5, "reviews": 23},
  "prodoctorov": null,  # пропускаем в v1
  "summary": "..."      # генерируется из реальных данных
}
  │
  ↓
_format_reviews_block() в llm.py (БЕЗ ИЗМЕНЕНИЙ) → блок "04 — ОТЗЫВЫ"
```

---

## Компоненты

### 1. `AIM/hermes-v2/app/lib/yandex_reviews.py` (НОВЫЙ, ~150 строк)

Обёртка над `zen-studio/yandex-maps-reviews-scraper` через `UnifiedKeyPool`.

```python
async def search(company_name: str, city: str, url: str = None) -> dict | None:
    """Найти клинику на Яндекс.Картах и вернуть рейтинги + отзывы.

    Возвращает:
        {
            "rating": float | None,         # точный рейтинг с Яндекса
            "reviews_count": int | None,    # точное кол-во отзывов
            "reviews": list[dict],          # топ-отзывы (текст, оценка, дата)
            "address": str | None,
            "categories": list[str],
        }
    или None если клиника не найдена.
    """
```

- Использует `get_apify_pool()` из `app.lib.apify_client` (14 ключей, уже настроено)
- Ротация ключей при 429/402 через `UnifiedKeyPool.mark_exhausted()` (механизм уже есть)
- Actor input: `{"searchStrings": ["{company_name}, {city}"], "maxReviews": 20, "placeId": [...]}`
- Polling: start run → wait → get dataset (как `run_instagram_content.py`)

### 2. `AIM/hermes-v2/app/lib/gis2_reviews.py` (НОВЫЙ, ~100 строк)

Обёртка над `m_mamaev/2gis-places-scraper`. Аналогично yandex_reviews, но для 2ГИС.

### 3. `AIM/hermes-v2/app/tools/run_review_platforms.py` (ПЕРЕПИСАН, ~180 строк)

Было: `_build_query()` → `perplexity_chat()` → `_parse_response()` (regex-парсинг текста).

Стало:
```python
async def handle_run_review_platforms(company_name=None, city=None, url=None, **kwargs):
    # Кэш (10 мин) — ОСТАВЛЯЕМ, не меняем
    cache_key = f"{company_name}|{city}|{url}"
    if cached := _get_cache(cache_key):
        return cached

    # Параллельный вызов 2 площадок
    yandex_result, gis2_result = await asyncio.gather(
        yandex_reviews.search(company_name, city, url),
        gis2_reviews.search(company_name, city, url),
        return_exceptions=True,
    )

    # Сборка результата в ТОТ ЖЕ формат (обратная совместимость с _format_reviews_block)
    result = {
        "yandex": _normalize_yandex(yandex_result),
        "twogis": _normalize_gis2(gis2_result),
        "prodoctorov": None,  # пропускаем
        "summary": _build_summary(yandex_result, gis2_result),
    }

    _set_cache(cache_key, json.dumps(result, ensure_ascii=False))
    return json.dumps(result, ensure_ascii=False)
```

**Ключевое:** интерфейс тулa (имя, schema, возвращаемый JSON-формат) **не меняется**. `_format_reviews_block()` в `llm.py` работает без правок.

### Что НЕ меняется
- `app/lib/perplexity.py` — остаётся как есть (для других тулов)
- `app/tools/perplexity_tools.py` — остаётся (quick_overview, extract_clinic_profile, perplexity_search, run_smi_mentions)
- `app/llm.py` — не трогаем (auto-inject, форматтер, оркестрация)
- `app/lib/apify_client.py` — используем как есть (UnifiedKeyPool готов)
- `app/lib/key_pool.py` — не трогаем
- Регистрация тулa — `run_review_platforms` имя сохраняется

---

## Fallback стратегия

| Ситуация | Действие |
|---|---|
| ✅ Apify нашёл клинику на Яндекс.Картах | Точные данные |
| ⚠️ Не нашёл по search | Пробуем `startUrls` с url клиники (если домен совпадает) |
| ⚠️ 2ГИС не нашёл | `twogis: null`, блок строится без 2ГИС |
| ⚠️ Все Apify ключи исчерпаны (429 на всех 14) | Возвращаем `{"error": "all apify keys exhausted"}`, блок показывает «отзывы временно недоступны» |
| ⚠️ ProDoctorov | Пропускаем (`prodoctorov: null`) |

---

## Тесты

### Новый файл `AIM/hermes-v2/tests/test_reviews_apify.py`

```python
# test_yandex_reviews_normalization
#   - mock Apify response → проверить нормализацию в {rating, reviews_count, ...}
# test_search_no_results
#   - actor вернул пустой dataset → вернуть None
# test_key_rotation_on_429
#   - первый ключ 429 → пул отдаёт второй → успех
# test_run_review_platforms_both_platforms
#   - mock обоих actors → проверить итоговый JSON-формат совместим с _format_reviews_block
# test_cache_hit
#   - второй вызов в течение 10 мин → без обращения к Apify
```

Все тесты без сети (monkeypatch httpx/Apify client).

---

## Метрики успеха

| Метрика | Сейчас (Perplexity) | После (Apify) |
|---|---|---|
| Точность рейтинга | ~50% (часто выдуман) | ~100% (с самой площадки) |
| Точность кол-ва отзывов | ~30% | ~100% |
| Реальные тексты отзывов | Нет (общие темы) | Да (топ-20 текстов) |
| Цена за клинику | ~$0.50-1.50 (Perplexity sonar) | ~$0.10-0.30 (2 Apify runs) |
| Время выполнения | 5-10 сек | 20-60 сек (кэш 10 мин сглаживает) |
| Зависимость от Perplexity quota | Да (падает при 401) | Нет (отдельный пул) |

---

## Риски и смягчения

1. **Apify actor ломается при смене вёрстки Яндекс.Карт.** Смягчение: это responsibility Apify actor maintainer, не наша. Подписка на actor = включены фиксы.
2. **Actor не находит клинику.** Смягчение: fallback на `startUrls`, потом `null` — блок строится частично.
3. **Медленнее Perplexity.** Смягчение: кэш 10 мин (уже есть), параллельный `asyncio.gather` для 2 платформ.
4. **Расход Apify ключей.** Смягчение: 14 ключей в пуле + free tier каждого actor (~$5/мес бесплатно через Apify platform credits).

---

## Out of scope (не делаем в этой итерации)

- ❌ Перенос `quick_overview`/`extract_clinic_profile` с Perplexity (веб-поиск там уместен)
- ❌ ProDoctorov скрапер (нет готового actor)
- ❌ Подключение SearXNG (поднят, но не нужен для отзывов)
- ❌ Перенос остальных v1 тулов
- ❌ HTML builder / WordPress publishing (отдельная большая задача)

---

## Файлы для изменения/создания

| Файл | Действие | Строк |
|---|---|---|
| `AIM/hermes-v2/app/lib/yandex_reviews.py` | СОЗДАТЬ | ~150 |
| `AIM/hermes-v2/app/lib/gis2_reviews.py` | СОЗДАТЬ | ~100 |
| `AIM/hermes-v2/app/tools/run_review_platforms.py` | ПЕРЕПИСАТЬ | ~180 |
| `AIM/hermes-v2/tests/test_reviews_apify.py` | СОЗДАТЬ | ~120 |
| `AIM/hermes-v2/requirements.txt` | ДОБАВИТЬ apify-client (если нужно) | +1 |

Итого: ~550 строк нового/изменённого кода.
