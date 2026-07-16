# Phase 6: Documentation Sync - Context

**Gathered:** 2026-06-24 (--auto mode — user sleeping)
**Status:** Ready for planning

<domain>
## Phase Boundary

Привести документацию в соответствие с кодом: SOUL.md, SKILL.md (aim-scout), phases.py, engine.py _TOOL_HANDLERS — всё должно описывать одну и ту же систему. Никаких фантомных фаз (0.5, 0.75, 0.8, 3.2), никаких рассинхронов (13 vs 14 vs 16).

**Внутри scope:**
- Синхронизация `SOUL.md` (на сервере и в репо) с 3-pass orchestrator + 18-item QC + Phase 3-5 фичами
- Синхронизация `skills/aim-scout/SKILL.md` — описать оркестратор + чек-лист, не «FULL AUTO pipeline»
- Синхронизация `phases.py` — удалить фантомные фазы, привести к истине
- Синхронизация `engine.py:_TOOL_HANDLERS` — все 26 инструментов описаны
- Удаление фантомных фаз 0.5/0.75/0.8/3.2 из всех документов

**Вне scope:**
- Новые фичи (Phase 3-5 closed this)
- Изменение runtime поведения (этот phase только документация)
- Переписывание дизайн-системы (канон)

</domain>

<decisions>
## Implementation Decisions

### Source of Truth

- **D-01:** КОД = source of truth. Документация зеркалит код, не наоборот. Если код имеет 3-pass orchestrator → SOUL.md описывает 3-pass orchestrator. Если _TOOL_HANDLERS имеет 26 entries → SKILL.md перечисляет 26.
- **D-02:** Конкретные артефакты-источники:
  - `AIM/hermes/app/orchestrator/three_pass.py` — 3-pass цикл
  - `AIM/hermes/app/orchestrator/qc_checklist.py` — 18-item QC checklist v1.2.0
  - `AIM/hermes/app/pipeline/engine.py:_TOOL_HANDLERS` — 26 entries
  - `AIM/hermes/app/pipeline/phases.py` — PipelineEngine phases (если используется)
  - `AIM/hermes/app/orchestrator/pass_collect.py / pass_gap_analyze.py / pass_fill_assemble.py` — actual prompts

### SOUL.md Update Strategy (SYN-01, SYN-02)

- **D-03:** Полная переработка SOUL.md:
  - Раздел "Architecture" — описать 3-pass cycle (Collect → Gap-analyze → Fill+Assemble)
  - Раздел "Tools" — 26 tools grouped (aim-operations + hermes-debug)
  - Раздел "QC Checklist" — 18 items
  - Раздел "Modes" — PRESALE/ACTIVE/ADMIN/SALES_ADMIN (без изменений)
  - Раздел "Niche Detection" — Phase 3 mini-call между Pass 1 и Pass 2
  - Раздел "Instagram Integration" — Phase 3 Instagram-critical для plastic/cosmetology
  - УДАЛИТЬ: жёсткую последовательность фаз 0-12, упоминания магистров, фантомные фазы

### SKILL.md (aim-scout) Update Strategy (SYN-03)

- **D-04:** aim-scout SKILL.md описывает:
  - PipelineEngine как fallback mode (ORCHESTRATOR_MODE=0)
  - 3-pass orchestrator как основной mode (ORCHESTRATOR_MODE=1)
  - 18-item QC checklist as coverage metric
  - Инструменты как каталог, не как pipeline
- **D-05:** УДАЛИТЬ "FULL AUTO pipeline" язык. Заменить на "3-pass LLM-orchestrator with QC checklist".

### phases.py Cleanup (SYN-01)

- **D-06:** phases.py в коде — если используется только как PipelineEngine fallback, оставить 13-phase структуру но с пометкой "LEGACY: only used when ORCHESTRATOR_MODE=0". Если не используется вообще — переместить в `phases_legacy.py` с deprecation notice.
- **D-07:** Удалить фантомные фазы (0.5, 0.75, 0.8, 3.2) — они существуют только в серверной v3 SOUL.md, после D-03 будут удалены автоматически.

### engine.py _TOOL_HANDLERS Sync (SYN-04)

- **D-08:** engine.py уже синхронизирован после Phase 4 deploy (26 entries). Добавить assertion тест: `_TOOL_HANDLERS_COUNT >= 26`. Если в будущем добавятся tools и забудут _TOOL_HANDLERS — тест упадёт.
- **D-09:** Документировать в SKILL.md список всех 26 tools с категориями (aim-operations 18 tools + hermes-debug tools).

### Phantom Phase Removal (SYN-05)

- **D-10:** Полный grep по SOUL.md, SKILL.md, phases.py на "0.5", "0.75", "0.8", "3.2" → удалить все упоминания. Если в серверной SOUL.md — обновить на сервере через docker cp.

### Implementation Split

- **D-11:** 3 плана:
  - **06-01:** SOUL.md rewrite (локально + сервер)
  - **06-02:** SKILL.md (aim-scout) rewrite + phases.py cleanup
  - **06-03:** engine.py assertion test + phantom phase grep removal + deploy

### Claude's Discretion

- Точная структура разделов SOUL.md
- Стиль языка (формальный/дружелюбный)
- Сколько деталей про 3-pass cycle включить
- Как именно обновить серверную SOUL.md (docker cp + restart? или atomic replace?)
- Нужно ли отдельные ARCHITECTURE.md / TOOLS.md / QC.md или всё в SOUL.md

### Folded Todos

(нет — --auto mode)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Source-of-Truth Code Files
- `AIM/hermes/app/orchestrator/three_pass.py` — 3-pass cycle implementation
- `AIM/hermes/app/orchestrator/qc_checklist.py` — 18-item QC_CHECKLIST v1.2.0
- `AIM/hermes/app/orchestrator/pass_collect.py` — Pass 1 prompt
- `AIM/hermes/app/orchestrator/pass_gap_analyze.py` — Pass 2 prompt
- `AIM/hermes/app/orchestrator/pass_fill_assemble.py` — Pass 3 prompt (items 1-21 + EXAMPLES BY SECTION)
- `AIM/hermes/app/orchestrator/niche_detector.py` — Phase 3 mini-call module
- `AIM/hermes/app/orchestrator/states.py` — OrchestratorState with niche field
- `AIM/hermes/app/orchestrator/coverage_reporter.py` — CoverageReport with not_applicable_items
- `AIM/hermes/app/pipeline/engine.py` — _TOOL_HANDLERS (26 entries)
- `AIM/hermes/app/pipeline/phases.py` — PipelineEngine phases (if still used)
- `AIM/hermes/app/tools/__init__.py` — register_all_tools()

### Documentation Targets
- `AIM/hermes/skills/aim/SOUL.md` — primary identity prompt (server: /opt/data/SOUL.md)
- `AIM/hermes/skills/aim-scout/SKILL.md` — scout skill
- `AIM/hermes/app/pipeline/phases.py` — if phantom phases

### Prior Phase Verifications (for accurate mirroring)
- `.planning/phases/02-3-pass-orchestrator-coverage-checklist/02-VERIFICATION.md`
- `.planning/phases/03-instagram-integration/03-VERIFICATION.md`
- `.planning/phases/04-new-sections-data-depth/04-VERIFICATION.md`
- `.planning/phases/05-deep-interpretation/05-VERIFICATION.md`

### Project-Level
- `.planning/PROJECT.md` — три версии SOUL.md history
- `.planning/REQUIREMENTS.md` §Sync (SYN-01..05) — Phase 6 requirements
- `CLAUDE.md` — constraints

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Все Phase 3-5 SUMMARY файлы — фактическая архитектура системы для зеркалирования
- `_TOOL_HANDLERS` (26 entries after Phase 4) — tool catalog
- `QC_CHECKLIST` v1.2.0 (18 items) — QC metric
- `ORCHESTRATOR_MODE` env var — opt-in switch

### Established Patterns
- **Honest reporting:** «данные недоступны» применяется и к документации — если фаза не используется, явно указать DEPRECATED
- **Docker cp deploy:** через `cat local | ssh aim "docker exec -i aim-hermes tee remote"` pattern

### Integration Points
- Server `/opt/data/SOUL.md` (cached in _soul_md_cache) — needs update
- Repo `AIM/hermes/skills/aim/SOUL.md` — source for Docker image layer
- `AIM/hermes/skills/aim-scout/SKILL.md` — scout skill
- `AIM/hermes/app/pipeline/phases.py` — if still referenced

</code_context>

<specifics>
## Specific Ideas

- КОД = source of truth, документация зеркалит
- Удалить фантомные фазы (0.5, 0.75, 0.8, 3.2) — grep everywhere
- SOUL.md описывает 3-pass cycle + LLM-orchestrator + 26 tools + 18-item QC
- aim-scout SKILL.md: "3-pass orchestrator with QC checklist", не "FULL AUTO pipeline"
- engine.py assertion тест на >=26 entries

</specifics>

<deferred>
## Deferred Ideas

- Полная замена SOUL.md на structured JSON/YAML — backlog
- Автоматическая генерация SOUL.md из кода — backlog
- ADR (Architecture Decision Records) — backlog
- Двуязычная документация (RU/EN) — backlog

</deferred>

---

*Phase: 6-Documentation Sync*
*Context gathered: 2026-06-24 (--auto mode)*
