# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-20)

**Core value:** LLM — интерпретатор данных, НЕ оркестратор. Python контролирует последовательность фаз.
**Current focus:** Phase 3 — Deploy & verify (тестовый прогон)

## Current Status

- **Milestone:** v1.0 (initial)
- **Active Phase:** Phase 3 (Deploy & verify)
- **Progress:** 2/3 phases complete

## Phase Status

| Phase | Status | Plans | Started |
|-------|--------|-------|---------|
| Phase 1: SOUL.md rewrite | ✅ Complete | 1/1 | 2026-06-20 |
| Phase 2: SKILL + dead code | ✅ Complete | 2/2 | 2026-06-20 |
| Phase 3: Deploy & verify | ⏳ Pending | 0/2 | — |

## Key Resources

- **SOUL-v3.md (активный):** `/root/.hermes/SOUL.md` в контейнере hermes-20.06
- **V7-REDESIGN.md:** AIM/hermes/V7-REDESIGN.md
- **Backup v7:** /Users/mikhaileliseev/Desktop/backups/hermes-v7/
- **Pipeline engine:** /opt/hermes/app/pipeline/engine.py (в контейнере)
- **14 тулов:** /opt/hermes/app/tools/ (в контейнере)
- **Server:** ssh aim, container hermes-20.06
- **SOUL на сервере:** `/root/.hermes/SOUL.md` (HERMES_HOME, v3)
- **SKILL на сервере:** `/opt/hermes/skills/aim/client-onboarding-pipeline/SKILL.md` (v7.0.0)

## Next Actions

1. Запустить тестовый пресейл (например toriclinic.ru)
2. Проверить что все 13 фаз выполняются без ошибок
3. Обновить PROJECT.md — перенести DEPLOY в Validated
4. Отметить milestone v1.0 как Complete

---
*Last updated: 2026-06-20 after Phase 2 completion*
