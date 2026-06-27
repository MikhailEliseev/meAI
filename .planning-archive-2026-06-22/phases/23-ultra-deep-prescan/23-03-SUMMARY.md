# 23-03: Hermes Staged Prescan Integration — COMPLETED

**Date:** 2026-06-03
**Status:** ✅ All 3 tasks completed and verified

## What was done

### Task 1: run_prescan.py rewrite (500 lines)
- `handle_run_prescan` now calls `/api/presale/prescan-staged` (staged endpoint)
- Progress messages pushed via `push_tool_progress` as each stage "completes" (simulated from single response)
- Returns merged JSON with `stage_1_financials`, `stage_2_under_the_hood`, `stage_3_market` + denormalized backward-compat fields
- Falls back to legacy `/api/presale/prescan` on 404
- Timeout increased to 150s
- Registry description updated with 3-stage flow language
- Helper functions: `_narrate_stage_1/2/3`, `_build_merged_summary`, `_legacy_prescan`, `_compute_years_on_market`, `_fmt_rub`

### Task 2: SOUL.md updates
- **Шаг 2** completely rewritten with 3-stage descriptions (Финансовый хук → Под капотом → Рынок)
- Each stage described in detail: what it gathers, what to show client, timing
- Example progressive narration added for all 3 stages
- **run_prescan tool entry** updated with stage_1/2/3 field references
- **PROHIBITIONS** extended: no waiting for all stages, no skipping stage order, no find_competitors before prescan complete
- **ANTI-HALLUCINATION** rules added for staged data fields

### Task 3: PRESALE prompt (_presale_prompt) updates
- Added **"🎭 ТРЁХСТАДИЙНАЯ РАЗВЕДКА"** section with stage-by-stage narration rules
- Added **"⚠️ ПРАВИЛО: НЕ ЖДИ ВСЕ СТАДИИ"** section — sequential 3-message story pattern
- Stage data blocks referenced by name: `stage_1_financials`, `stage_2_under_the_hood`, `stage_3_market`
- **run_prescan bullet** in "Как рассказывать данные" updated for staged flow
- All existing rules preserved: first-move rule, anti-hallucination, business language

## Files changed
- `AIM/hermes/app/tools/run_prescan.py` — rewritten (500 lines, +284 from original)
- `AIM/hermes/skills/aim/SOUL.md` — Шаг 2 + tools catalog + PROHIBITIONS updated
- `AIM/hermes/app/agent_wrapper.py` — _presale_prompt extended with staged flow rules

## Verification
- [x] run_prescan calls `/api/presale/prescan-staged`
- [x] 3 progress messages pushed via push_tool_progress
- [x] Returns merged JSON with stage_1/2/3 blocks
- [x] Falls back to old `/api/presale/prescan` on 404
- [x] SOUL.md describes 3-stage flow with explicit stage descriptions
- [x] SOUL.md includes АНТИГАЛЛЮЦИНАЦИЯ rules for staged data
- [x] PRESALE prompt teaches sequential 3-message narration
- [x] PRESALE prompt references stage_1/2/3 by name
- [x] "ПРАВИЛО ПЕРВОГО ХОДА" preserved
- [x] Anti-hallucination rules preserved
- [x] No new dependencies
- [x] All syntax checks pass

## Next: Phase 23 complete
All 3 plans executed: 23-01 (database + API), 23-02 (pipeline + tests), 23-03 (Hermes integration).
Ready for deploy and manual testing via Telegram.
