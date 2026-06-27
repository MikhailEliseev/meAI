---
phase: 4
plan: 04-05
subsystem: orchestrator
tags: [orchestrator, pass3, strategy, offer, whitefields, prompts, llm-generation, d-24, sec-01, sec-02, sec-03, sec-04, sec-05, dat-01, dat-02, dat-04, dat-05]

# Dependency graph
requires:
  - "04-01: find_company_financials revenue_dynamics + clinic_metrics output fields"
  - "04-02: find_doctor_handles structured_regalia field"
  - "04-03: run_forum_pains + run_media_urls tools (registered, returns patient_fears_hint + mentions_by_source)"
  - "04-04: Pass 1 phase4_rules instructs LLM to call Phase 4 tools; Pass 2 18-item QC checklist"
provides:
  - "Pass 3 _build_prompt extended with items 7-15 covering all Phase 4 sections"
  - "D-24 SATISFIED: LLM receives explicit generation rules for each new section type"
  - "9 new kwargs contract documented for generate_html_report: strategy_section, offer_section, whitefields_matrix, merged_experts, content_analysis+patient_fears, revenue_dynamics, clinic_metrics_humanized, media_urls, ratings_data"
affects:
  - "04-06 (HTML Data Sections — renders Phase 4 sections per new Pass 3 prompt instructions)"
  - "04-07 (HTML Competitor Cards — uses whitefields_matrix kwarg structure defined in item 9)"
  - "04-08 (deploy — pass_fill_assemble.py ships via docker cp)"
  - "generate_html_report consumer (must accept new kwargs in Plan 04-06/04-07)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Additive prompt items (7-15) appended to existing items 1-6 — backward compatible"
    - "Per-section kwarg contract — each item names the kwarg the LLM must pass to generate_html_report"
    - "Strict rule encoding (D-13) in prompt: 'НЕ показывай секцию динамики ВОВСЕ' is unambiguous instruction, not LLM judgement"
    - "LLM-as-translator pattern (D-21) — LLM translates OKVED codes to human language at report-time, not data-time"

key-files:
  created: []
  modified:
    - AIM/hermes/app/orchestrator/pass_fill_assemble.py

key-decisions:
  - "Items 7-15 appended AFTER existing items 1-6 — preserves Phase 3 instagram/niche/coverage instructions priority ordering"
  - "Each new item names its source tool + field (find_company_financials.clinic_metrics, run_forum_pains.patient_fears_hint, etc.) — LLM has explicit data contract"
  - "D-13 strict rule encoded as 'НЕ показывай секцию динамики ВОВСЕ' + 'не нарушай' emphasis — eliminates LLM's temptation to extrapolate from partial data"
  - "D-21 OKVED translation deferred to LLM at report-time (not data-time in find_company_financials) — keeps data layer schema pure, leverages LLM knowledge"
  - "Item 14 media URLs rendered as 'ПРОСТОЙ СПИСОК' (not cards with logos) per D-17 — explicit MVP scope guard against scope creep"
  - "9 new kwargs documented: strategy_section, offer_section, whitefields_matrix, merged_experts, content_analysis+patient_fears (kwargs), revenue_dynamics, clinic_metrics_humanized, media_urls, ratings_data"

patterns-established:
  - "Pattern: per-section generation rules in prompt — each new report section gets its own numbered item with (a) source data, (b) expected structure, (c) kwarg name"
  - "Pattern: explicit kwarg naming convention — {section_name}_section or {data_name} kwarg, documented in prompt for downstream generate_html_report consumer"
  - "Pattern: strict-rule emphasis markers ('ВОВСЕ', 'не нарушай', 'D-13 strict rule') — used when LLM might otherwise extrapolate from partial data"
  - "Pattern: LLM-deferred translation — semantic transformations (OKVED → human) encoded as LLM instructions, not data-layer logic"

requirements-completed: [SEC-01, SEC-02, SEC-03, SEC-04, SEC-05, DAT-01, DAT-02, DAT-04, DAT-05]

# Metrics
duration: 2min
completed: 2026-06-24
---

# Phase 4 Plan 04-05: Pass 3 Prompt — Strategy/Offer/Whitefields/Регалии/Страхи Generation Rules Summary

**Pass 3 `_build_prompt` extended with 9 new numbered items (7-15) instructing the LLM how to generate each Phase 4 report section: Strategy (5 directions × 4 basis sources), Offer (CTA + concrete steps), Whitefields (4×4 matrix), Experts+регалии (site + Instagram merge), Content Analysis+страхи (top-5 from forums), Revenue dynamics (D-13 strict <3-year rule), Clinic metrics (LLM OKVED translation), Media URLs (simple list, pr_needed honest block), Ratings (2 platforms minimum).**

## Performance

- **Duration:** ~2 min (PLAN_START 00:36:10Z → PLAN_END 00:38:53Z, 163s)
- **Started:** 2026-06-24T00:36:10Z
- **Completed:** 2026-06-24T00:38:53Z
- **Tasks:** 1 (Task 1: Add Phase 4 section generation rules to `_build_prompt`)
- **Files modified:** 1 (`pass_fill_assemble.py`)
- **Commits:** 1
- **Lines added:** 94 (94 insertions, 0 deletions)

## Accomplishments

- **9 new numbered items (7-15) appended** to the existing 6-item `_build_prompt` return string. Total prompt items: 15.
- **Module docstring updated** with Phase 4 / Plan 04-05 context block — documents what was added and references items 7-15.
- **D-24 SATISFIED** — LLM now receives explicit generation rules for each new section type, covering all SEC-01..05 + DAT-01..05 requirements.
- **Each new item follows consistent structure:**
  - Section name + reference HTML section number (e.g., "(секция 09)" for Strategy)
  - Explicit source data references (tool name + field name, e.g., "find_doctor_handles structured_regalia")
  - Expected output structure (5 directions, 4×4 matrix, top-5 list, etc.)
  - Kwarg name to pass to `generate_html_report`
- **D-13 strict <3-year rule** encoded with emphasis markers ("ВОВСЕ", "не нарушай") to eliminate LLM extrapolation from partial data.
- **D-21 OKVED translation** deferred to LLM at report-time with concrete examples ("86.21 → Общая медицинская практика").
- **D-17 simple list** explicitly contrasted with "карточки с лого (избыточно для MVP)" — MVP scope guard.
- **D-18 honest block** for 0 media mentions with PR recommendation feedback loop to Strategy section.
- **Items 1-6 (Phase 3)** preserved unchanged — backward compatible with existing Phase 3 instagram/niche/coverage kwargs contract.
- **Function signature unchanged:** `_build_prompt(state: OrchestratorState) -> str`
- **`_PASS_FILL_TIMEOUT=600` unchanged** — prompt expansion is text-only, doesn't affect runtime characteristics
- **`run_pass_fill_assemble` body unchanged** — only the prompt builder was modified

## Task Commits

1. **Task 1:** `feat(04-05): extend Pass 3 prompt with 9 Phase 4 section generation rules (D-24)` — `1e0aed6`

## Files Modified

| File | Lines Changed | Reason |
|------|---------------|--------|
| `AIM/hermes/app/orchestrator/pass_fill_assemble.py` | +94/-0 | Module docstring updated with Phase 4 block; items 7-15 appended to return string (Strategy, Offer, Whitefields, Experts, Content+страхи, Revenue dynamics, Clinic metrics, Media URLs, Ratings) |

## Items Added to `_build_prompt` (Items 7-15)

| Item | Section | Requirements Covered | Key Rules |
|------|---------|----------------------|-----------|
| 7 | Strategy (09) | SEC-01, D-01..03 | 5 fixed directions × LLM-generated content; 4 explicit basis sources (конкуренты, content_gaps, страхи, reputation); 2-3 concrete steps per direction with цифрами from data |
| 8 | Offer (10) | SEC-02, D-04 | Same pattern as Strategy; LLM-generated concrete steps + CTA; specific AIM services (контент-продакшн, SEO, репутация-менеджмент, Telegram-маркетинг) |
| 9 | Whitefields matrix (07) | SEC-03, D-05..07 | 4 categories × 4 columns: Услуги/Цены/Врачи/Digital × клиент+3 конкурента; each cell from specific tool field |
| 10 | Experts with регалии (03) | SEC-04, D-08..09 | Мёрдж по ФИО: site-scraped регалии + Instagram метрики; explicitly handles 3 cases (both, site-only, instagram-only) |
| 11 | Content Analysis with страхи (04) | SEC-05, D-10..11 | Top-5 врача (Instagram-active когорта); top-5 страхов from `run_forum_pains patient_fears_hint` with mention counts |
| 12 | Revenue dynamics | DAT-01, D-13..14 | Strict <3-year rule: `dynamics_available=False → НЕ показывай секцию ВОВСЕ`; honest label; D-13 emphasis markers |
| 13 | Clinic metrics (About) | DAT-04, D-21 | LLM translates OKVED codes to human language at report-time with examples (86.21 → Общая медицинская практика) |
| 14 | Media URLs (05) | DAT-02, D-17..18 | ПРОСТОЙ СПИСОК (not cards); `{Source} — "{Title}" — {Date} → {URL}` format; pr_needed honest block + Strategy feedback loop |
| 15 | Ratings | DAT-05, D-22 | Minimum 2 platforms: ПроДокторов + Яндекс.Карты; rating + review count + themes |

## Verification Results

| Check | Result |
|-------|--------|
| AST parse: `pass_fill_assemble.py` syntax valid | OK |
| `_build_prompt(state)` returns string | OK |
| Numbered items count: 15 (was 6) | OK |
| Item 1 (fill gaps) preserved | OK |
| Item 2 (generate_html_report) preserved | OK |
| Item 3 (ORC-04 honest) preserved | OK |
| Item 4 (coverage_metadata) preserved | OK |
| Item 5 (niche) preserved | OK |
| Item 6 (instagram_data) preserved | OK |
| Item 7 Strategy present + 'STRATEGY SECTION' marker | OK |
| Item 8 Offer present + 'OFFER SECTION' marker | OK |
| Item 9 Whitefields present + 'WHITEFIELDS MATRIX' marker | OK |
| Item 10 Experts present + 'регали' marker | OK |
| Item 11 Content Analysis present + 'страх' marker | OK |
| Item 12 Revenue dynamics present + 'revenue_dynamics' marker | OK |
| Item 13 Clinic metrics present + 'clinic_metrics' marker | OK |
| Item 14 Media URLs present + 'media_urls' marker | OK |
| Item 15 Ratings present + 'ratings' marker | OK |
| D-03 Strategy basis 1 (КОНКУРЕНТ) referenced | OK |
| D-03 Strategy basis 2 (CONTENT GAPS) referenced | OK |
| D-03 Strategy basis 3 (СТРАХ) referenced | OK |
| D-03 Strategy basis 4 (REPUTATION) referenced | OK |
| D-05 Whitefields category УСЛУГИ | OK |
| D-05 Whitefields category ЦЕНЫ | OK |
| D-05 Whitefields category ВРАЧИ | OK |
| D-05 Whitefields category DIGITAL | OK |
| D-13 strict <3-year rule: `dynamics_available` check | OK |
| D-13 strict <3-year rule: 'НЕ показывай' instruction | OK |
| D-21 OKVED translation: 'ОКВЭД' reference | OK |
| D-21 OKVED translation: '86.21' example OR 'человеческ' | OK |
| D-17 Media: 'ПРОСТОЙ СПИСОК' OR 'список' instruction | OK |
| D-18 Media: `pr_needed` OR '0 упоминан' honest block | OK |
| Function signature: `_build_prompt(state: OrchestratorState) -> str` | OK |
| `_PASS_FILL_TIMEOUT == 600` | OK |
| `run_pass_fill_assemble` is async | OK |
| Prompt length: 6480 chars (was ~1500 before Phase 4) | OK |

## Decisions Made

- **Items 7-15 appended AFTER item 6** (not inserted in the middle). Phase 3 instagram/niche/coverage items (4-6) are the load-bearing kwargs contract — placing Phase 4 items after preserves the LLM attention hierarchy. The Phase 3 items are also more critical because they unblock conditional HTML rendering (no-instagram block); Phase 4 items are all about generation, not gating.
- **Each item names its source tool + field explicitly** (e.g., "из find_doctor_handles structured_regalia"). The LLM has all tool results in its Pass 1 history but needs explicit pointer to which field contains the relevant data — without this, the LLM might guess or skip.
- **D-13 strict rule encoded with emphasis markers** ("НЕ показывай секцию динамики ВОВСЕ" + "Это D-13 strict rule — не нарушай"). Without emphasis, LLMs tend to extrapolate from partial data ("you have 2 years, I'll show 2 years") — emphasis markers signal this is a hard rule, not a suggestion.
- **D-21 OKVED translation deferred to LLM** at report-time, not data-time. Alternative considered: hard-code OKVED→human dictionary in `find_company_financials.py`. Rejected because (a) LLM has broader OKVED knowledge than any practical dictionary, (b) keeps data layer schema pure (just codes), (c) LLM can handle edge cases (combined codes, deprecated codes, regional variations).
- **D-17 simple list explicitly contrasted with cards+logos** ("НЕ карточки с лого (избыточно для MVP)"). This serves as a scope guard — without explicit rejection of cards, future iterations might add card UI complexity. The "MVP" framing anchors scope.
- **Item 14 includes Strategy feedback loop** ("в Strategy (09) рекомендуй PR-активность"). When media URLs = 0, the Strategy section should mention PR — closing the loop between data gap and recommendation. This is a small but important data flow.
- **Item 10 Experts explicitly handles 3 merge cases** (both data sources, site-only, instagram-only). Without this, LLM might omit doctors who appear in only one source. The "instagram_only" tag preserves traceability — downstream consumer knows the source.
- **9 distinct kwargs documented** (strategy_section, offer_section, whitefields_matrix, merged_experts, content_analysis+patient_fears, revenue_dynamics, clinic_metrics_humanized, media_urls, ratings_data). These become the contract for `generate_html_report` (Plan 04-06/04-07) — each kwarg has a specific name and expected structure.

## Prompt Token Cost Estimate

- **Before Phase 4:** ~1500 chars (~375 tokens at 4 chars/token for Russian text)
- **After Phase 4:** 6480 chars (~1620 tokens)
- **Delta:** +4980 chars (~1245 tokens)
- **Per presale call:** One Pass 3 invocation per report — adds ~1.2K tokens to system prompt
- **DeepSeek V4 Pro context:** 128K tokens — 1.2K delta is <1% of context budget
- **Cost impact:** Negligible (sub-cent per report at DeepSeek pricing)

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written.

**Total deviations:** 0

## Issues Encountered

None.

## User Setup Required

None — pure Python prompt-string change, no external services or environment variables.

## Threat Model Compliance

| Threat | Mitigation Status |
|--------|------------------|
| T-04-05-T (Tampering — LLM could fabricate Strategy/Offer content not based on data) | mitigate — prompt explicitly says "ИЗ СОБРАННЫХ ДАННЫХ" and references specific tool fields (`content_gaps`, `patient_fears_hint`, etc.); ORC-04 honest-data principle enforced via item 3 ("НЕ выдумывай") |
| T-04-05-I (Info disclosure — LLM generates content from collected clinic data) | accept — data already in LLM's Pass 1 history — prompt doesn't expose new data, just references it |
| T-04-05-D (DoS — longer prompt → more LLM tokens) | accept — prompt is ~6.5KB text; DeepSeek V4 Pro handles 16K token output; existing `_PASS_FILL_TIMEOUT=600s` sufficient |
| T-04-05-E (EoP — not applicable) | accept — pure prompt expansion, no privilege change |
| T-04-05-SC (Supply chain — no new packages) | accept — pure Python string changes |

## Next Phase Readiness

- **Ready for downstream consumers:**
  - **04-06 (HTML Data Sections):** Can now implement HTML rendering for the 9 new kwargs documented in items 7-15. The kwarg contract is: `strategy_section`, `offer_section`, `whitefields_matrix`, `merged_experts`, `content_analysis`, `patient_fears`, `revenue_dynamics`, `clinic_metrics_humanized`, `media_urls`, `ratings_data`
  - **04-07 (HTML Competitor Cards):** Uses `whitefields_matrix` kwarg structure defined in item 9 (4 categories × 4 columns)
  - **04-08 (Deploy):** `pass_fill_assemble.py` ships via `docker cp` to `aim-hermes` container. No new pip dependencies, no schema migrations, no container restart needed (Python lazy-imports).
- **No blockers** — code is local-only (not deployed), deployment happens in Plan 04-08 (Wave 4).

## Self-Check: PASSED

- ✓ `AIM/hermes/app/orchestrator/pass_fill_assemble.py` — file exists, AST parses cleanly, 257 lines (was 163 — +94 for items 7-15 + docstring update)
- ✓ Commit `1e0aed6` — FOUND in git log (Task 1: Pass 3 prompt Phase 4 extension)
- ✓ All plan verification assertions pass (15 items, all required patterns present, D-03/D-05/D-13/D-17/D-18/D-21 rules encoded)
- ✓ Regression: Phase 3 items 1-6 (fill gaps, generate_html_report, ORC-04 honest, coverage_metadata, niche, instagram_data) preserved
- ✓ Function signature unchanged: `_build_prompt(state: OrchestratorState) -> str`
- ✓ `_PASS_FILL_TIMEOUT=600` unchanged
- ✓ `run_pass_fill_assemble` body unchanged (still async, still uses `_get_agent_for_session`)

---
*Phase: 04-new-sections-data-depth*
*Completed: 2026-06-24T00:38:53Z*
