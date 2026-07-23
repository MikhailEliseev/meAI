# STATE.md — Milestone 3: Chat Report Delivery

**Обновлено:** 2026-07-23
**Текущая фаза:** Phase 12 (planning)

## Milestone 2 — ✅ COMPLETED
- [x] Phase 9: HTML Builder Migration — canonical CSS дизайн-системы
- [x] Phase 10: WordPress Publisher — publish_report на MariaDB
- [x] **Доп. раунды полировки** (между фазами):
  - Минималистичная таблица конкурентов (стиль чата, не громоздкая)
  - Тема синхронизирована с сайтом (html[data-theme=dark])
  - GPU-оптимизация ripple (transform: scale, не width/height → 0 layout-shift)
  - Ripple уменьшен в 2 раза (15 колец вместо 30)
  - Убрана медальность, убрана дубль-кнопка темы

**Тег:** `report-generator-v6-done`
**Smoke:** https://iamaim.ru/6hk3z8o3/

## Milestone 3 — 🔄 IN PROGRESS
**Цель:** Доставка отчёта пользователю из чата + скачивание.

### Completed фазы
- [x] **Phase 11: Chat Report Integration** ✅ 2026-07-22
  - Автопубликация отчёта в конце диалога (триггер: find_competitors)
  - SSE event `report-ready` с URL отчёта
  - Карточка в чате с кнопкой «Открыть отчёт»
  - Гвард дубликатов через БД (W-3 fix)
  - URL отчёта сохраняется в БД (I-2 fix)
  - Стрим использует parseMarkdown (fix ::: blocks)
  - **Тег:** `phase-11-review-fixed`
  - **UAT:** 8/8 PASS
  - **Smoke:** https://iamaim.ru/btu2vneu/

### Pending фазы
- [ ] Phase 12: Report Download (planning)
  - Кнопка «Скачать отчёт» в карточке чата
  - Эндпоинт `/api/report/{slug}/download` — отдаёт HTML как файл
  - (Опционально) PDF-конвертация
- [ ] Phase 13: QC Critique (опционально, перенос из v1)
  - 18-пунктный чеклист качества
  - LLM-critique перед публикацией

### Blockers
- Нет

### Notes
- Report builder и publisher — работают в проде
- Phase 11 fixes (W-1/W-2/W-3/I-2) — все задеплоены
- 137/138 тестов PASS (1 несвязанный fail в test_llm.py)
