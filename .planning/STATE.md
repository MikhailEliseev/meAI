# STATE.md — Milestone 3: Chat Report Delivery

**Обновлено:** 2026-07-22
**Текущая фаза:** (Milestone 3 в планнинге)

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

## Milestone 3 — 🔄 PLANNING
**Цель:** Доставка отчёта пользователю из чата + скачивание.

### Pending фазы
- [ ] Phase 11: Chat Report Integration
  - hermes-v2 генерирует отчёт в конце диалога (4 блока готовы)
  - SSE event `report-ready` с URL отчёта
  - Карточка в чате с кнопкой «Открыть отчёт»
- [ ] Phase 12: Report Download
  - Кнопка «Скачать отчёт» (PDF или HTML файл)
  - Эндпоинт `/api/report/{slug}/download`
- [ ] Phase 13: QC Critique (опционально, перенос из v1)
  - 18-пунктный чеклист качества
  - LLM-critique перед публикацией

### Blockers
- Нет

### Notes
- Report builder (`report_builder/`) и publisher (`publish_report`) — готовы
- chat-inline.php уже имеет `.report-ready-card` CSS (надо проверить)
- hermes-v2 main.py: нужен триггер «конец диалога → publish_report»
