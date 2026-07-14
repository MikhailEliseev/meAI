# Phase 4: Базовый сценарий (база → кнопки) — Summary

**Phase:** 04-base-flow-buttons
**Completed:** 2026-07-14
**Status:** ✅ COMPLETE — URL → база → suggestions работает

---

## Что сделано

Сценарий «база → кнопки → по запросу» формализован в backend. Клиент шлёт URL → Гермес автоматически вызывает quick_overview + find_competitors → выдаёт базу (рынок + конкуренты + питч AIM) → эмитит SSE `suggestions` с 2-4 адаптивными кнопками.

## Доказательства (evidence)

### E2E: «Проанализируй клинику https://stomus.ru»
- **Время: 239с (3.99 мин)** — FLOW-02 ≤4 мин ✅ (впритык)
- **2 тулза вызваны**: quick_overview + find_competitors (FLOW-01)
- **661 токен** связного ответа
- **SSE suggestions: 4 кнопки** (CHAT-01):
  - Глубокий анализ конкурентов → run_ci_analysis
  - Упоминания в СМИ → run_smi_mentions
  - Анализ отзывов → run_review_platforms
  - Анализ соцсетей → run_instagram_content
- **Маркер [SUGGESTIONS] вырезан** из текста (MARKER_IN_RAW=0)

### Регрессия
- health ✅, простой чат (85 токенов) ✅, все контейнеры healthy ✅

## Архитектура

1. **Промпт усилен**: жёсткое правило «при URL → quick_overview + find_competitors → база → [SUGGESTIONS] маркер → ждёшь».
2. **SSE suggestions (CHAT-01)**: модель пишет `[SUGGESTIONS]...[/SUGGESTIONS]` в конце → backend парсит → эмитит `{"type":"suggestions","buttons":[...]}` → вырезает маркер.
3. **Адаптивность (CHAT-05)**: модель сама выбирает кнопки по результату базы (промпт инструктирует: плохие отзывы → «анализ отзывов», активный IG → «анализ соцсетей»).
4. **Fallback**: если маркера нет → 4 кнопки по умолчанию.
5. **Streaming-safe перехват**: маркер стримится токенами → буферизую хвост, не стримлю если может быть началом `[SUGGESTIONS]`.

## Нюанс

**239с — впритык к 4 мин.** find_competitors (Apify Google Maps) занимает ~120-150с. Это узкое место. Если потребуется быстрее — параллельный запуск тулов (сейчас последовательный).

## Покрытые требования

| ID | Статус |
|---|---|
| FLOW-01 (URL → quick_overview + find_competitors) | ✅ |
| FLOW-02 (база ≤4 мин) | ✅ 239с |
| FLOW-03 (кнопки + свободный ввод) | ✅ |
| FLOW-04 (питч AIM в конце базы) | ✅ в промпте |
| CHAT-01 (SSE suggestions) | ✅ |
| CHAT-05 (адаптивные кнопки) | ✅ |

## Что дальше (Phase 5)

Фронтенд: useStreamChat.js → case 'suggestions' → рендер кнопок в ChatBubble.jsx. Клик → текст → тул. + generate_html_report (Wave 2 из Phase 3).

---

*Phase 04 — COMPLETE*
