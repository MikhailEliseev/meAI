# ROADMAP.md — Milestone 2: v3 Feature Parity

> **Создан:** 2026-07-22
> **Предыдущие фазы:** 1-8 (Milestone 1, completed)

---

## Phases

| Phase | Название | Описание | Зависимости |
|-------|----------|----------|-------------|
| 9 | HTML Builder Migration | Перенос build_report.py из v1 → v2, адаптация под формат v2 | — |
| 10 | WordPress Publisher | Публикация HTML-отчёта на iamaim.ru/{slug} через MySQL | Phase 9 |
| 11 | Chat Integration | Интеграция отчёта в чат: SSE report-ready, кнопка, placeholder | Phase 10 |
| 12 | QC Critique | 18-пунктный чеклист качества + интеграция в отчёт | Phase 9 |
| 13 | E2E + Deploy | Полный тест: чат → отчёт → ссылка → качество | Phases 9-12 |

---

## Phase Details

### Phase 9: HTML Builder Migration
**Цель:** Перенести HTML builder из v1 в v2, адаптировать под v2 данные.

**Задачи:**
- Создать `hermes-v2/app/report_builder/` модуль
- Перенести `build_report.py` (1580 строк) → адаптировать
- Заменить v1 pipeline data format на v2 collected_results format
- Сохранить AIM Design System (14 canonical классов, шрифты, theme toggle)
- Тесты: unit-тесты на builder (мок данных → HTML)

### Phase 10: WordPress Publisher
**Цель:** Публикация HTML-отчёта как страницы WordPress.

**Задачи:**
- Перенести `publish_scout_report.py` (237 строк)
- Адаптировать под v2 (убрать session_archive, брать HTML напрямую)
- pymysql → wp_posts insert (status=publish, type=page)
- Генерация slug (6 символов)
- Возврат `https://iamaim.ru/{slug}`
- Тесты: мок MySQL → проверка insert

### Phase 11: Chat Integration
**Цель:** Чат автоматически публикует отчёт и показывает ссылку.

**Задачи:**
- В `chat_with_tools`: после streaming, вызвать publish_report
- SSE-событие `report-ready` с URL
- Фронтенд `chat-inline.php`: обработка `report-ready` → кнопка
- Placeholder-страница при первом ответе (опционально)
- Тесты: e2e (мок → SSE → URL)

### Phase 12: QC Critique
**Цель:** Проверка качества отчёта перед публикацией.

**Задачи:**
- Перенести `qc_checklist.py` (342 строки)
- Адаптировать под v2 collected_results
- 18 пунктов: about, market, competitors, experts, instagram, content, media, forum, financials, strategy, offer, reputation
- PASS_THRESHOLD = 80%
- Включить QC-секцию в HTML-отчёт
- Тесты: unit-тесты на чеклист (мок данных → PASS/FAIL)

### Phase 13: E2E + Deploy
**Цель:** Полный тест пайплайна: чат → данные → отчёт → ссылка → QC.

**Задачи:**
- E2E тест: отправить URL в чат → получить ссылку на отчёт
- Проверить отчёт на реальной клинике (arclinic.ru)
- QC coverage ≥ 80%
- Деплой на прод
- Smoke-тест через браузер
