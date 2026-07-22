# STATE.md — Milestone 2: v3 Feature Parity

**Обновлено:** 2026-07-22
**Текущая фаза:** (не начата — Phase 9 следующая)

## Milestone 2 Goals
- HTML-отчёты на iamaim.ru/{slug} (REQ-1)
- QC critique (REQ-2)

## Pending
- [ ] Phase 9: HTML Builder Migration
- [ ] Phase 10: WordPress Publisher
- [ ] Phase 11: Chat Integration
- [ ] Phase 12: QC Critique
- [ ] Phase 13: E2E + Deploy

## Blockers
- Нет

## Notes
- v1 исходники: `AIM/hermes/app/tools/build_report.py` (1580 строк), `publish_scout_report.py` (237), `qc_checklist.py` (342)
- MySQL доступ: aim-mysql (MariaDB 11), WP_DB_* env vars в docker-compose
- Фронтенд: `chat-inline.php` (НЕ golden — golden не используется)
