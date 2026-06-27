---
phase: 29-hermes-multi-tenant-pm
plan: 02
subsystem: hermes
tags: [pm, integration, presale, second-brain, context-preservation, tests]
depends_on:
  requires:
    - 29-01 (PM scripts, SKILL.md, templates, research)
  provides:
    - presale-pipeline Phase 0 project setup
    - Second Brain search/ingest integration
    - context-preservation restore after /new
    - 10 integration tests full lifecycle
affects:
  - presale-pipeline/SKILL.md (new depends_on, Phase 0 Step 0, Phase 5)
  - project-management/SKILL.md (expanded sections 4, 5, 6)
tech-stack:
  added: []
  patterns: [integration tests, subprocess.run, pytest tmp_path, flock concurrency]
key-files:
  created:
    - AIM/hermes/tests/test_pm_integration.py (686 lines, 10 integration tests)
  modified:
    - AIM/hermes/skills/presale-pipeline/SKILL.md (188 -> 215 lines)
    - AIM/hermes/skills/project-management/SKILL.md (284 -> 401 lines)
decisions:
  - "presale-pipeline Phase 0 вызывает project-management для создания/проверки проекта перед Deep Research (D-17)"
  - "PM-скилл содержит 3 сценария presale integration: новый клиент, повторный заход, пост-presale данные (D-17)"
  - "Second Brain: search-kb с 3 уровнями (глобальный, проект, клиент) + ingest-clinic.py с флагами (D-18)"
  - "Context preservation: автоматическое сохранение после каждого действия, ротация чекпоинтов (max 10), restore из чекпоинта после /new (D-19)"
  - "Правила безопасности контекста: context.json без ПДн, ФЗ-152 через encrypted_lead_dossier (D-19)"
  - "move-project обновляет registry metadata, но не перемещает директорию на диске"
metrics:
  duration: 591s
  completed_date: "2026-06-07T08:55:49Z"
---

# Phase 29 Plan 02: PM Skill Ecosystem Integration Summary

**One-liner:** Integrated PM skill with presale-pipeline (Phase 0 project setup + Phase 5 handoff), Second Brain (search-kb + ingest-clinic), and context-preservation (restore after /new); 10 integration tests covering full lifecycle.

## Tasks Completed

| Task | Name | Type | Commit | Status |
|------|------|------|--------|--------|
| 1 | Integrate PM with presale-pipeline | auto | b501dc3 | Done |
| 2 | Integrate PM with Second Brain + context-preservation | auto | d8075ab | Done |
| 3 | Integration tests (TDD) | auto (tdd) | d64985a, 35cb241 | Done |

## What Was Built

### Task 1: Presale-Pipeline Integration

**presale-pipeline/SKILL.md (215 lines):**
- YAML depends_on: added `project-management: ">=1.0"`
- Phase 0 renamed to "Project Setup + Deep Research" with Step 0 (create/verify project) before Deep Research
- Phase 4 (HTML): deliverables instruction to save to `deliverables/index.html`
- Phase 5 (Save & Handoff): data.json finalization, shared/ duplication (doctors, financials, competitors, site-meta), context checkpoint, client notification

**project-management/SKILL.md Section 4 expanded:**
- Scenario A: presale for new client (7-step algorithm)
- Scenario B: presale for returning client (v2/v3 auto-increment)
- Scenario C: post-presale data reuse in PM operations
- LLM rules: never disclose infrastructure operations, snake_case slugs, shared/ only after Phase 5

### Task 2: Second Brain + Context Preservation

**project-management/SKILL.md Sections 5-6 expanded:**

Section 5 (Second Brain):
- search-kb: global, per-project, per-client levels
- Usage scenarios: competitor search, KP examples, best practices
- ingest-clinic.py: with --specialization, --revenue, --doctors-count flags
- Rule: aggregate-only data in global Second Brain

Section 6 (Context Preservation):
- Auto-save after every significant action
- Checkpoint rotation: max 10, oldest auto-deleted
- Restore after /new: 5-step algorithm (detect -> load -> remind -> respond -> wait)
- Restore from checkpoint: find last valid by timestamp
- Context Security: no PII in context.json, ФЗ-152 via encrypted_lead_dossier, PII detection -> delete + move to dossier

### Task 3: Integration Tests (10 tests, all passing)

| # | Test | What it covers |
|---|------|---------------|
| 1 | test_full_lifecycle | create -> bind -> context -> checkpoint -> detect -> restore |
| 2 | test_project_isolation | Two projects, no context leaks between chat_ids |
| 3 | test_shared_access | One client, two projects, shared/ created once |
| 4 | test_presale_data_handoff | data.json in project_dir, readable after creation |
| 5 | test_context_restore_after_new | pending_tasks preserved after checkpoint restore |
| 6 | test_registry_concurrency | 5 parallel add-chat, flock safety, registry intact |
| 7 | test_move_project_preserves_data | Registry metadata updated, context survives |
| 8 | test_checkpoint_rotation | 15 checkpoints -> max 10 retained |
| 9 | test_missing_registry_recovery | Auto-create valid registry on first command |
| 10 | test_corrupted_context_recovery | Corrupted JSON -> error message, exit code 1 |

All tests use `tmp_path` fixtures and `subprocess.run()` to execute scripts with `--registry-file` and `--projects-root` isolation flags.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed move-project test: missing --projects-root flag**
- **Found during:** Task 3 (test 7), GREEN phase
- **Issue:** `move-project` call in test didn't pass `--projects-root`, causing workdir to use default `/root/projects` instead of temp directory
- **Fix:** Added `--projects-root` flag to move-project call; changed verification to read context.json directly from old directory (move-project updates registry metadata, not directory on disk)
- **Files modified:** `AIM/hermes/tests/test_pm_integration.py`
- **Commit:** 35cb241

## Verification Results

### Automated Checks

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| project-management in presale-pipeline | >= 1 | 2 | PASS |
| pm-create-project in presale-pipeline | >= 1 | 1 | PASS |
| pm-detect-context in presale-pipeline | >= 1 | 1 | PASS |
| deliverables in presale-pipeline | >= 1 | 1 | PASS |
| shared/ in presale-pipeline | >= 1 | 5 | PASS |
| data.json in project-management | >= 1 | 6 | PASS |
| search-kb in project-management | >= 1 | 7 | PASS |
| ingest-clinic in project-management | >= 1 | 2 | PASS |
| Context Preservation in project-management | >= 1 | 1 | PASS |
| pm-detect-context in project-management | >= 1 | 12 | PASS |
| pm-context.py restore in project-management | >= 1 | 1 | PASS |
| checkpoints in project-management | >= 1 | 3 | PASS |
| ФЗ-152/ПДн in project-management | >= 1 | 4 | PASS |
| Integration tests pass | 10/10 | 10/10 | PASS |

### Success Criteria

- [x] presale-pipeline Phase 0 starts with Step 0: create/verify project via project-management
- [x] presale-pipeline Phase 5 (Save & Handoff) saves data.json, duplicates to shared/, creates checkpoint
- [x] HTML-KP saved to deliverables/index.html
- [x] PM-skill contains detailed search-kb instructions (global, project, client)
- [x] PM-skill contains detailed ingest-clinic.py instructions (knowledge saving)
- [x] PM-skill contains context restoration algorithm after /new (5 steps)
- [x] PM-skill contains context security rules (no PII in context.json, ФЗ-152)
- [x] PM-skill contains presale integration scenarios (new client, returning client)
- [x] 10 integration tests pass, covering full lifecycle

### TDD Gate Compliance

| Gate | Commit | Status |
|------|--------|--------|
| RED | d64985a: `test(29-02): add integration tests for PM skill full lifecycle` | PASS |
| GREEN | 35cb241: `fix(29-02): fix move-project test — add missing --projects-root flag` | PASS |

## Threat Flags

No new threat surface beyond what was specified in the plan's threat model. All mitigations (T-29-08 through T-29-12) are addressed in SKILL.md content:
- T-29-08 (client_slug extraction): snake_case validation rule in SKILL.md
- T-29-09 (shared/ data): aggregate-only rule in Section 5
- T-29-10 (context.json PII): Context Security Rules in Section 6
- T-29-11 (bind/create elevation): admin-only (user_id=322367335) enforced in Section 8
- T-29-12 (checkpoint DoS): max 10 rotation in Section 6

## Self-Check: PASSED

| Item | Status |
|------|--------|
| SUMMARY.md exists | PASS |
| presale-pipeline/SKILL.md modified (215 lines) | PASS |
| project-management/SKILL.md modified (401 lines, >280) | PASS |
| test_pm_integration.py exists (686 lines, >100) | PASS |
| Commit b501dc3 (Task 1) | PASS |
| Commit d8075ab (Task 2) | PASS |
| Commit d64985a (Task 3 RED) | PASS |
| Commit 35cb241 (Task 3 GREEN) | PASS |
