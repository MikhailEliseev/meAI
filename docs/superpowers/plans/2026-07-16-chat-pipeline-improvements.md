# План доработок чата и pipeline (16 июля 2026)

> Чекпоинт: `checkpoint-20260716-2309`. Всё ниже — следующие шаги.

---

## Текущее состояние (факты из тестов)

| Компонент | Статус | Доказательство |
|-----------|--------|----------------|
| Конкуренты (5, hybrid ФНС+Perplexity) | ✅ | doctorplastic 74s, medsi 9.7B |
| Сетевые клиники (агрегат сети) | ✅ | МЕДСИ 6 филиалов → 9.7 млрд |
| Геофильтр | ✅ | Все конкуренты из correct города |
| UnifiedKeyPool Firecrawl | ✅ | 3 теста, 14/15 стабильно |
| GEO/SEO аудит клиента | ✅ | GEO=70, Яндекс=4.8★ |
| SUGGESTIONS рендер | ✅ | 2 кнопки: соцсети + SEO |
| DNS-проверка домена | ✅ | seeline 301s→60s |
| run_review_platforms | ⚠️ | Tool работает, но LLM не вызывает (1 раз за всё время) |
| Врачи клиента | ❌ | Часто null, Perplexity fallback написан но не срабатывает |
| Бренды клиента (сеть) | ❌ | Школа Юцковской и пр. не показываются |

---

## Задача 1: Отзывы в чате — run_review_platforms [КРИТИЧНО]

**Проблема:** LLM упрямо вызывает 3 tool'а (extract_clinic_profile, quick_overview, find_competitors), игнорируя `run_review_platforms` (4-й). За весь день — 1 вызов.

Tool работает (проверено вручную: Я.Карты 5.0★, ProDoctorov, 2ГИС, темы хвалят/критикуют). Проблема в том что LLM не выбирает его.

**Подход:** Не полагаться на LLM. Вызывать `run_review_platforms` **принудительно из кода** в `llm.py`, параллельно с find_competitors — по тому же принципу что auto-inject ИНН.

**Шаги:**
1. В `chat_with_tools()` (llm.py): после завершения первого turn'а, проверить — если был вызван `find_competitors` но НЕ `run_review_platforms`, и у нас есть `url` → запустить `run_review_platforms` автоматически.
2. Результат добавить в `collected_results["run_review_platforms"]` → `_build_formatted_blocks()` уже умеет его показывать.
3. Убрать `run_review_platforms` из SUGGESTIONS кнопок (он теперь вызывается автоматически).

**Файлы:**
- `AIM/hermes-v2/app/llm.py` — автовызов после первого turn'а
- `AIM/hermes-v2/app/prompts/dialogue.py` — убрать из кнопок

**Проверка:**
- Тест через чат: URL клиники → блок «⭐ Отзывы пациентов» появляется
- Логи: `review_platforms OK` при каждом прогоне

**Риск:** Добавляет ~10-15s к pipeline (Perplexity запрос). Но отзывы — ключевая ценность.

---

## Задача 2: Врачи клиента — почему null [ВЫСОКО]

**Проблема:** `client_doctors` часто null. Pipeline вызывает `scrape_doctors(url)` (Firecrawl). Если Firecrawl ключи исчерпаны или сайт JS-heavy → None. Perplexity fallback написан (Шаг 3 в `scrape_doctors`), но срабатывает только после того как Firecrawl полностью провален.

**Подход:** Для клиента использовать **СЧЛ из ФНС** (среднесписочная численность) — уже есть `client_employee_count`. Показывать как «сотрудников» вместо «врачей». Плюс Perplexity fallback сделать primary для клиента.

**Шаги:**
1. В `find_competitors()` Stage 3.5c: если `scrape_doctors` вернул None → сразу Perplexity (уже написано, проверить что работает).
2. В `llm.py` `_build_formatted_blocks()`: если `client_doctors` null но `client_employee_count` есть → показывать СЧЛ как «сотрудников».
3. В промпте: LLM не пишет «врачей не найдено» если есть СЧЛ.

**Файлы:**
- `AIM/src/aim/services/competitor_matcher_v2.py` — Stage 3.5c
- `AIM/hermes-v2/app/llm.py` — _build_formatted_blocks
- `AIM/hermes-v2/app/formatters/overview.py` — отображение

**Проверка:**
- doctorplastic: врачи найдены (через Perplexity или СЧЛ)
- Логи: `doctors_perplexity_fallback` или СЧЛ показан

---

## Задача 3: Сопутствующие бренды клиента [СРЕДНЕ]

**Проблема:** Клиника Юцковской включает школу, косметологию, ещё бренды. Pipeline показывает только основное юрлицо.

**Подход:** В `quick_overview` (Perplexity) спросить не только о врачах, но и о связанных брендах/подразделениях.

**Шаги:**
1. В `perplexity_tools.py` промпт `quick_overview`: добавить «Есть ли у клиники связанные бренды, школа, подразделения?»
2. В `format_overview()`: добавить блок «Связанные бренды» если найдены.

**Файлы:**
- `AIM/hermes-v2/app/tools/perplexity_tools.py`
- `AIM/hermes-v2/app/formatters/overview.py`

**Проверка:**
- yutskovskaya.ru: показывается «Школа Юцковской» и другие бренды

---

## Задача 4: Фазы 2-3 — проверить что кнопки работают [СРЕДНЕ]

**Проблема:** SUGGESTIONS даёт 2 кнопки (📸 Анализ соцсетей, 🔍 SEO-аудит). Нужно проверить что при клике они реально запускают tool и показывают результат.

**Шаги:**
1. Тест через чат: отправить URL → дождаться базового анализа → кликнуть «📸 Анализ соцсетей»
2. Проверить: `run_instagram_content` вызывается, IG анализ показывается
3. Кликнуть «🔍 SEO-аудит» → `seo_audit` вызывается, результат показывается
4. Если не работает — починить

**Проверка:**
- Кнопка → tool → результат в чате

---

## Задача 5: Время pipeline при count=5 [НИЗКО]

**Проблема:** 74-132s для 5 конкурентов. Цель <90s для большинства.

**Текущий breakdown (оценка):**
- Stage 0 (client profile): ~15s
- Stage 1 (Perplexity + registry parallel): ~15s
- Stage 2 (resolve 25 brands): ~20s
- Stage 3 (enrich): ~15s
- Stage 3.4 (deep enrich top-5): ~10s
- Stage 3.5b (IG/doctors/website top-5): ~20s
- Stage 3.5c (client audit): ~15s

**Возможные оптимизации:**
1. Perplexity кэш по (специализация+город), TTL 1 день → Stage 1 из кэша = 0s при повторе
2. SEO аудит клиента запустить **параллельно** с Stage 3 (сейчас последовательно)
3. Уменьшить `max_brands` с 25 до 20

**Файлы:**
- `AIM/src/aim/services/competitor_matcher_v2.py`

---

## Порядок выполнения

1. **Задача 1** (Отзывы) — главная ценность, видна пользователю
2. **Задача 2** (Врачи) — частая жалоба «не нашёл»
3. **Задача 4** (Кнопки) — проверить что фазы 2-3 работают
4. **Задача 3** (Бренды) — nice-to-have
5. **Задача 5** (Время) — оптимизация после функционала

---

## Откат

```
git checkout checkpoint-20260716-2309
```

Бэкап сервера: `/opt/backups/code-checkpoint-20260716-2309.tar.gz`
