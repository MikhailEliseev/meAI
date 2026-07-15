# Hermes Phase 7 — Speed & Data Quality

**Дата:** 2026-07-15
**Статус:** Approved
**Скоуп:** Базовый сценарий (URL → таблица конкурентов с выручкой + кнопки)

## Проблема

Базовый анализ URL занимает **274с (4.5 мин)** вместо целевых ≤2 мин:
- 55% времени — `find_competitors` (151с, Apify → Google Maps)
- 19% — молчание при non-streaming LLM call (62с суммарно)
- Лишние тулы (`extract_clinic_profile` → `perplexity_search`)
- Тулы выполняются последовательно, не параллельно
- Конкуренты — «ближайшие по карте», не «достижимые по выручке»
- Нет финансовых данных (выручка) по конкурентам

## Решение

### 1. Параллельный запуск тулов

**Было:** extract_clinic_profile → quick_overview → find_competitors (последовательно, ~182с)
**Будет:** extract_clinic_profile ∥ quick_overview ∥ find_competitors (параллельно, ~120с)

Реализация: в `llm.py` — когда LLM возвращает несколько tool_calls в одном ответе, выполнять их через `asyncio.gather`.

### 2. Streaming tool-call detection

**Было:** `stream=False` для всех вызовов с tools= (10-52с молчания)
**Будет:** `stream=True` для tool-call detection — модель стримит, мы парсим tool_calls из стрима

Для GLM-5.2: если модель не поддерживает streaming tool-calls нативно, используем hybrid:
- Отправляем `stream=True`
- Накапливаем delta в буфер
- Когда видим tool_calls в накопленном response — выполняем

### 3. Обновлённый pipeline

```
URL клиента
  │
  ├─ [Параллельно] ────────────────────────────────────────────┐
  │  ├─ extract_clinic_profile (Perplexity, ~3-5с)             │
  │  │   → ИНН, юрлицо, город, специализация, адрес            │
  │  ├─ quick_overview (Perplexity, ~5-10с)                    │  ~60-120с
  │  └─ find_competitors (Apify, ~60-120с)                    │  (параллельно)
  │      → 15-30 кандидатов (имя, ИНН, рейтинг, отзывы)        │
  └────────────────────────────────────────────────────────────┘
  │
  ├─ [Когда extract_clinic_profile готов — не ждём остальных]
  │   └─ ПРИМЕРНО: через 3-5с у нас уже есть ИНН клиента
  │
  ├─ [Когда find_competitors готов]
  │   └─ enrich_competitors(кандидаты)
  │       Для каждого кандидата с ИНН → запрос выручки
  │       Источник: rusprofile.ru / Perplexity с ИНН
  │       ~10-15с (параллельные запросы)
  │
  ├─ filter_competitors(client_revenue, candidates)
  │   ├─ Фильтр по выручке: клиент_rev * 0.7 .. клиент_rev * 1.5
  │   ├─ Фильтр по специализации
  │   ├─ Сортировка: ближайшие к верхней границе (достижимые)
  │   └─ Top 3-5
  │
  └─ LLM streaming ответ
      └─ Таблица конкурентов + текст + suggestions кнопки
```

### 4. Источник данных по выручке

**Приоритет (по надёжности):**
1. **Perplexity с конкретным ИНН** — «Выручка ООО "Название" ИНН 7708698635 за 2023-2024 год»
   - С ИНН Perplexity намного точнее, чем по названию
   - Если Perplexity вернул выручку — используем её
2. **rusprofile.ru** — парсинг через Firecrawl (по ИНН)
   - Показывает выручку из ЕГРЮЛ/бухгалтерской отчётности
3. **Оценка** — если данные не найдены, помечаем как «оценочно»

**Формат результата:**
```json
{
  "inn": "7708698635",
  "name": "ООО Стоматология",
  "revenue": 65000000,
  "revenue_year": 2023,
  "is_estimate": false
}
```

### 5. Логика отбора конкурентов

```python
def filter_competitors(client_revenue, candidates, specialization=None):
    if not client_revenue:
        # Если выручка клиента неизвестна — берём top-3 по рейтингу
        return sorted(candidates, key=lambda c: c.rating, reverse=True)[:3]
    
    # Диапазон: от -30% до +50% от клиента
    # (-30% = тоже показываем, +50% = верхняя планка достижимости)
    min_rev = client_revenue * 0.7
    max_rev = client_revenue * 1.5
    
    filtered = [c for c in candidates 
                if c.revenue and min_rev <= c.revenue <= max_rev]
    
    if len(filtered) < 2:
        # Расширяем диапазон если мало кандидатов
        min_rev = client_revenue * 0.5
        max_rev = client_revenue * 2.0
        filtered = [c for c in candidates 
                    if c.revenue and min_rev <= c.revenue <= max_rev]
    
    # Сортировка: по выручке (ближайшие к верхней границе = мотивация)
    return sorted(filtered, key=lambda c: c.revenue)[:5]
```

### 6. Формат ответа (таблица)

LLM генерирует Markdown-таблицу, фронтенд рендерит через marked.js:

```markdown
## Ваша клиника на рынке

| | Выручка/год | Отзывы | Рейтинг |
|--|------------|--------|---------|
| **[Имя клиники]** | ~50 млн ₽ | 312 | ⭐ 4.7 |
| Стоматология Смит | **65 млн ₽** (+30%) | 450 | ⭐ 4.8 |
| Доктор Зуб | **58 млн ₽** (+16%) | 280 | ⭐ 4.6 |

> 🎯 Все три конкурента — достижимая цель. Разница в выручке 16-44%.
```

### 7. Обновлённый системный промпт

Ключевые изменения:
- Убрать «честность о качестве данных» (3 абзаца = лишние токены, latency)
- Убрать auto-inject extract_clinic_profile → find_competitors (теперь это делает LLM)
- Добавить формат таблицы в output
- Добавить инструкцию: «Параллельно вызови 3 тула: extract_clinic_profile, quick_overview, find_competitors»

### 8. Ожидаемые тайминги (после фикса)

| Этап | Было | Будет |
|------|------|-------|
| First token (LLM streaming) | 10с | 2-3с |
| extract_clinic_profile | 13с (serially) | 3-5с (parallel) |
| quick_overview | 28с (serially) | 5-10с (parallel) |
| find_competitors | 151с | 60-120с (parallel) |
| enrich_competitors | — | 10-15с (parallel per candidate) |
| Финальный LLM ответ | 52с (non-stream) | 5-10с (streaming) |
| **ИТОГО** | **274с** | **~80-140с = 1.3-2.3 мин** |

### 9. Изменения в файлах

| Файл | Изменение |
|------|-----------|
| `hermes-v2/app/llm.py` | Параллельное выполнение tool_calls через asyncio.gather; streaming tool-call detection |
| `hermes-v2/app/prompts/dialogue.py` | Новый системный промпт (короткий, таблица, параллельные тулы) |
| `hermes-v2/app/tools/competitors.py` | Возвращать 15-30 кандидатов с ИНН |
| `hermes-v2/app/tools/competitors.py` (new) | `enrich_competitors()` — ИНН → выручка через Perplexity/Firecrawl |
| `hermes-v2/app/tools/competitors.py` (new) | `filter_competitors()` — фильтр по выручке ±30% |
| `hermes-v2/app/main.py` | Sync с продом, учесть новые tool event types |
| `AIM/theme/chat-inline.php` | Поддержка таблиц в Markdown rendering |

### Out of scope (для следующей фазы)

- Улучшение quality данных для других тулов (Instagram, отзывы, реклама, СМИ)
- Telegram-бот миграция
- Удаление старого aim-hermes
- WordPress dashboard для просмотра сессий

---
*Created: 2026-07-15*
