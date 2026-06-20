# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-20)

**Core value:** LLM — интерпретатор данных, НЕ оркестратор. Python контролирует последовательность фаз.
**Current focus:** Phase 1 — SOUL.md переработка личности

## Current Status

- **Milestone:** v1.0 (initial)
- **Active Phase:** Phase 1 (SOUL.md rewrite)
- **Progress:** 0/3 phases complete

## Phase Status

| Phase | Status | Plans | Started |
|-------|--------|-------|---------|
| Phase 1: SOUL.md rewrite | ⏳ Pending | 0/1 | — |
| Phase 2: SKILL + dead code | ⏳ Pending | 0/2 | — |
| Phase 3: Deploy & verify | ⏳ Pending | 0/2 | — |

## Key Resources

- **SOUL-v3.md (черновик):** /tmp/SOUL-v3.md
- **V7-REDESIGN.md:** AIM/hermes/V7-REDESIGN.md
- **Backup v7:** /Users/mikhaileliseev/Desktop/backups/hermes-v7/
- **Pipeline engine:** backups/hermes-v7/app/pipeline/engine.py
- **Phases:** backups/hermes-v7/app/pipeline/phases.py
- **Server:** ssh aim, container hermes-20.06
- **SOUL на сервере:** /opt/hermes/SOUL.md (в контейнере)
- **SKILL на сервере:** /opt/hermes/skills/aim/client-onboarding-pipeline/SKILL.md (в контейнере)

## Next Actions

1. Открыть /tmp/SOUL-v3.md — финальная проверка
2. `docker cp` SOUL-v3.md в hermes-20.06:/opt/hermes/SOUL.md
3. Перейти к Phase 2

---
*Last updated: 2026-06-20 after GSD initialization*
