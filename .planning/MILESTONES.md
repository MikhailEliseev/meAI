# MILESTONES — meAI_1 Гермес v2

## Milestone 1: Interactive Chat Redesign (2026-07-14 → 2026-07-22)
**Статус:** ✅ Completed

**8 фаз:**
1. Walking Skeleton (контейнер + health + find_competitors)
2. Диалоговый сервер + промпт
3. Перенос тулов (13 зарегистрировано)
4. Базовый сценарий (база → кнопки)
5. Кнопки в Theme-чате + отчёт
6. Деплой на прод + nginx
7. V2 Competitor Pipeline (точность данных)
8. V2 Pipeline стабильность (Apify отзывы, auto-calls, pre-stream)

**Результат:**
- Чат работает на iamaim.ru через hermes-v2
- 4 блока данных: профиль, конкуренты, отзывы, аудит
- Apify для отзывов (Яндекс.Карты + 2ГИС) — точные рейтинги
- Auto-call financials (ФНС выручка)
- Perplexity для профиля/обзора
- SearXNG для поиска конкурентов
- 72/72 тестов PASS

---

## Milestone 2: v3 Feature Parity (2026-07-22 → ...)
**Статус:** 🔄 Planning

**Цель:** Перенос ключевых функций v1 в v2 — HTML-отчёты и QC critique.

**Функции:**
- HTML-отчёты на iamaim.ru/{slug} (build_report + WordPress publish)
- QC critique (18-пунктный чеклист + LLM-критика)

**Не включено (отложено):** Telegram бот, Mode system
