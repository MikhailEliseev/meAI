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

## Milestone 2: v3 Feature Parity (2026-07-22 → 2026-07-22)
**Статус:** ✅ Completed

**Цель:** Перенос ключевых функций v1 в v2 — HTML-отчёты и QC critique.

**Фазы:**
- Phase 9: HTML Builder Migration — canonical CSS дизайн-системы, build_report_html
- Phase 10: WordPress Publisher — publish_report на MariaDB, URL https://iamaim.ru/{slug}
- **Полировка (5 раундов):**
  - Минималистичная таблица конкурентов (стиль чата)
  - Тема синхронизирована с кнопкой сайта (html[data-theme=dark])
  - GPU-оптимизация ripple (transform: scale, 0 layout-shift)
  - Ripple уменьшен в 2 раза (15 колец вместо 30)
  - Убрана медальность и дубль-кнопка темы

**Результат:**
- Красивый отчёт на iamaim.ru/{slug} (Hero + 4 секции + CTA + footer)
- Dual theme (светлая Inter+Playfair / тёмная Art Deco Gold) через кнопку сайта
- GPU-оптимизированная ripple-анимация без мерцания
- 34/34 тестов PASS, tag: `report-generator-v6-done`
- Smoke: https://iamaim.ru/6hk3z8o3/

**Не включено (отложено в M3):** QC critique, Telegram, Mode system

---

## Milestone 3: Chat Report Delivery (2026-07-22 → ...)
**Статус:** 🔄 Planning

**Цель:** Доставка отчёта пользователю из чата + скачивание.

**Функции:**
- Hermes-v2 генерирует отчёт в конце диалога
- Карточка в чате с кнопкой «Открыть отчёт»
- Кнопка «Скачать отчёт» (PDF/HTML)
- QC critique (опционально — перенос из v1)

**Не включено (отложено):** Telegram бот, Mode system, auth

**Плановые фазы:**
- Phase 11: Chat Report Integration (SSE report-ready + карточка в чате)
- Phase 12: Report Download (кнопка + эндпоинт)
- Phase 13: QC Critique (18-пунктный чеклист)
