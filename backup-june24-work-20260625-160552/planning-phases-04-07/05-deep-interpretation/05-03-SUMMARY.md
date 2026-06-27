---
phase: 05-deep-interpretation
plan: 03
subsystem: orchestrator
tags: [orchestrator, pass3, prompt, few-shot, reference-calibration, narrative-examples, reference-html, d-11, int-01, int-02, int-03, int-04, int-05]

# Dependency graph
requires:
  - "05-01: Pass 3 _build_prompt items 16-21 (narrative quality rules + short reference calibration pointer in item 21)"
  - "05-CONTEXT D-11: ИПХиК (2).html as canonical style truth — reference for example extraction"
provides:
  - "Pass 3 _build_prompt EXAMPLES BY SECTION calibration block — 10 section-specific narrative examples (Секция 01..10)"
  - "2 labeled cross-reference examples (Content→Experts with Мельников нарко-рубрика, Strategy→Content fears with видя что {страх})"
  - "2 gap-block examples (✅ strength «масштаб и академическая база», 📍 growth «цифровое присутствие — ориентир: Олимп Клиник»)"
  - "2 blockquote examples (Секция 02 «Отрыв не в деньгах — отрыв в масштабе», Секция 09 «рост органического трафика в 3-5x»)"
  - "ОБЩИЕ ПРИНЦИПЫ block summarizing 5 narrative rules extracted from examples"
  - "D-11 FULLY satisfied (Plan 05-01 item 21 was short pointer; this plan adds comprehensive section-by-section calibration)"
affects:
  - "Phase 7 (Test on 3 Niches): few-shot anchors are the primary defense against LLM style drift; test reports MUST show reference-style depth across all 10 sections"
  - "Future prompt tuning: if Phase 7 reveals persistent style gaps in specific section types, add more examples for those sections"
  - "Token budget monitoring: prompt now ~18.3KB (~4575 tokens) — sub-4% of DeepSeek 128K context; room for future expansion but track growth"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Reference-anchored few-shot calibration — concrete narrative examples embedded directly in prompt as section-labeled (Секция NN) style anchors"
    - "Anti-overfitting disclaimer at calibration block header: «НЕ копируй конкретные цифры — бери цифры из данных клиента; эти образцы показывают СТИЛЬ и ГЛУБИНУ» (mitigates T-05-03-T)"
    - "Sub-labeled indented examples within section block (Gap-блок, Blockquote, Cross-reference) — gives LLM clear structural anchors within each section type"
    - "ОБЩИЕ ПРИНЦИПЫ block at end synthesizes 5 abstract rules from concrete examples — bridges inductive (examples) and deductive (rules) learning modes"

key-files:
  created: []
  modified:
    - path: AIM/hermes/app/orchestrator/pass_fill_assemble.py
      lines_before: 362
      lines_after: 443
      changes:
        - "+12 lines: module docstring Phase 5 / Plan 05-03 context block"
        - "+69 lines: EXAMPLES BY SECTION calibration block appended to _build_prompt return string (ПРИМЕРЫ ИЗ РЕФЕРЕНСА header + 10 section examples + 2 cross-refs + 2 gap-blocks + 2 blockquotes + ОБЩИЕ ПРИНЦИПЫ)"

key-decisions:
  - "Calibration block placed AFTER item 21 (not as new numbered item) — preserves Phase 5/05-01 item numbering (1-21) and frames the block as a structured reference appendix rather than an additional rule"
  - "Each section example wrapped with section-type label (Секция NN (Name)) — LLM can map each example to its target section type when generating"
  - "Header includes anti-overfitting clause «НЕ копируй конкретные цифры» — mitigates T-05-03-T (LLM copying ИПХиК-specific numbers instead of using client data)"
  - "2 cross-reference examples chosen to span different section pairs (Content→Experts in Секция 04, Strategy→Content fears in Секция 09) — demonstrates that cross-references apply across multiple section boundaries, not just one pattern"
  - "2 gap-block examples cover both border styles — strength uses ✅ (green border pattern in reference HTML line 419), growth uses 📍 (default border in reference HTML line 429); LLM can see both CSS classes"
  - "2 blockquote examples chosen from Секция 02 (Market strategic insight) and Секция 09 (Strategy expected outcome) — covers two distinct blockquote purposes: insight vs. projection"
  - "ОБЩИЕ ПРИНЦИПЫ block placed after concrete examples — synthesizes 5 rules LLM should extract; mirrors Plan 05-01 items 16-20 but inplain language derived from examples (inductive reinforcement)"
  - "All extracted text is RUSSIAN (preserved from reference) — no translation, matches canonical reference language"

patterns-established:
  - "Pattern: reference calibration block — when targeting a specific output style, embed curated few-shot examples per section type in a dedicated calibration block (separate from numbered rules)"
  - "Pattern: anti-overfitting disclaimer — when embedding examples with real data, explicitly forbid copying example data into output; examples are STYLE anchors, not DATA sources"
  - "Pattern: section-labeled examples — prefix each example with section-type label so LLM can map example → target section during generation"
  - "Pattern: principles-after-examples — when both concrete examples and abstract rules are needed, examples first (inductive), then principles (deductive synthesis)"

requirements-completed: [INT-01, INT-02, INT-03, INT-04, INT-05]

# Metrics
duration: 7min
completed: 2026-06-24T03:27:24Z
---

# Phase 5 Plan 05-03: Reference Calibration — EXAMPLES BY SECTION Block Summary

**Pass 3 `_build_prompt` extended with comprehensive EXAMPLES BY SECTION calibration block: 10 narrative examples extracted from canonical reference `ИПХиК (2).html` (one per section, Секция 01..10), 2 labeled cross-reference examples (Content→Experts, Strategy→Content fears), 2 gap-block examples (✅ strength + 📍 growth with competitor benchmark), 2 blockquote examples (Market insight + Strategy projection), plus an ОБЩИЕ ПРИНЦИПЫ block synthesizing 5 narrative rules from the examples. D-11 FULLY satisfied — Plan 05-01 item 21 was a short 4-snippet pointer; this plan adds the comprehensive section-by-section calibration that gives DeepSeek V4 Pro concrete few-shot anchors for every section type.**

## Performance

- **Duration:** ~7 min (PLAN_START 03:20:06Z → PLAN_END 03:27:24Z, 438s)
- **Started:** 2026-06-24T03:20:06Z
- **Completed:** 2026-06-24T03:27:24Z
- **Tasks:** 1 (Task 1: extract 10+ examples from reference + embed EXAMPLES block)
- **Files modified:** 1 (`AIM/hermes/app/orchestrator/pass_fill_assemble.py`)
- **Commits:** 1 task commit + 1 metadata commit (SUMMARY + STATE)
- **Lines added:** 81 (12 docstring + 69 EXAMPLES block)
- **File size:** 362 → 443 lines

## Accomplishments

- **EXAMPLES BY SECTION calibration block appended** after item 21 in `_build_prompt` return string. Header: «ПРИМЕРЫ ИЗ РЕФЕРЕНСА (стиль и глубина — CANON, НЕ копируй конкретные цифры — бери цифры из данных клиента; эти образцы показывают СТИЛЬ и ГЛУБИНУ нарратива)».
- **10 section-specific examples embedded** — one per reference section (Секция 01 About, 02 Market, 03 Experts, 04 Content Analysis, 05 Media, 06 Competitor Cards, 07 Whitefields, 08 Presence, 09 Strategy, 10 Offer).
- **2 cross-reference examples labeled** — Секция 04 (Мельников → топ-страх наркоз/реабилитация from Секция 03 audience + Секция 04 fears list), Секция 09 (Strategy → страх 'наркоз' from Секция 04).
- **2 gap-block examples labeled** — Секция 02 strength «✅ Сильная сторона: масштаб и академическая база (150+ хирургов, 88 лет истории, 6 товарных знаков)», Секция 02 growth «📍 Точка роста: цифровое присутствие — ориентир: Олимп Клиник (Telegram-канал, MedicalBusiness Schema)».
- **2 blockquote examples labeled** — Секция 02 «Отрыв не в деньгах — отрыв в масштабе» (insight), Секция 09 «Это даст рост органического трафика в 3-5x при бюджете ниже, чем у конкурентов» (projection).
- **ОБЩИЕ ПРИНЦИПЫ block** synthesizes 5 narrative rules from concrete examples: (a) первая фраза = ВЫВОД с цифрой, (b) каждая цифра сопровождается сравнением, (c) каждая секция заканчивается blockquote, (d) cross-references органически вплетаются, (e) бизнес-язык с конкретными фразами.
- **Anti-overfitting disclaimer in block header** — explicitly forbids copying reference numbers; reinforces that examples are STYLE anchors only (mitigates T-05-03-T tampering threat).
- **Module docstring updated** with Phase 5 / Plan 05-03 context block — documents EXAMPLES BY SECTION calibration, references D-11 full satisfaction, describes relationship to Plan 05-01 item 21 (pointer) and this plan (comprehensive).
- **D-11 FULLY SATISFIED** — Plan 05-01 item 21 was a short 4-snippet pointer («образцы стиля (few-shot)»); this plan adds the comprehensive section-by-section calibration block with all 10 sections covered + cross-references + gap-blocks + blockquotes.
- **Function signature unchanged:** `_build_prompt(state: OrchestratorState) -> str`.
- **`_PASS_FILL_TIMEOUT=600` unchanged** — text-only expansion, no runtime characteristics affected.
- **`run_pass_fill_assemble` body unchanged** — only the prompt builder was modified.

## Task Commits

1. **Task 1: Extract 10+ narrative examples from reference HTML and embed as EXAMPLES block in Pass 3 prompt** — `8015c1f` (feat)

## Files Modified

| File | Lines Changed | Reason |
|------|---------------|--------|
| `AIM/hermes/app/orchestrator/pass_fill_assemble.py` | +81/-0 | Module docstring updated with Phase 5 / Plan 05-03 block; EXAMPLES BY SECTION calibration block appended to `_build_prompt` return string (10 section examples + 2 cross-references + 2 gap-blocks + 2 blockquotes + ОБЩИЕ ПРИНЦИПЫ) |

## EXAMPLES Block Structure

| Block Component | Count | Sections Covered |
|-----------------|-------|------------------|
| Section-specific examples (Секция NN) | 10 | 01 About, 02 Market, 03 Experts, 04 Content, 05 Media, 06 Competitor Cards, 07 Whitefields, 08 Presence, 09 Strategy, 10 Offer |
| Cross-reference examples | 2 | Секция 04 (Content→Experts+ fears), Секция 09 (Strategy→Content fears) |
| Gap-block examples (✅ strength) | 1 | Секция 02 (масштаб и академическая база) |
| Gap-block examples (📍 growth) | 1 | Секция 02 (цифровое присутствие — ориентир Олимп Клиник) |
| Blockquote examples | 2 | Секция 02 (Отрыв в масштабе), Секция 09 (рост трафика 3-5x) |
| ОБЩИЕ ПРИНЦИПЫ rules | 5 | Synthesis across all examples |

## Verification Results

| Check | Result |
|-------|--------|
| AST parse: `pass_fill_assemble.py` syntax valid | OK |
| Header «ПРИМЕРЫ ИЗ РЕФЕРЕНСА» present | OK |
| All 10 section labels (Секция 01..10) present | OK |
| Cross-reference label present (8 mentions total) | OK |
| Strength emoji ✅ present | OK |
| Growth emoji 📍 present | OK |
| Blockquote label present (10 mentions total) | OK |
| Items 16 (NARRATIVE STYLE) preserved — regression check | OK |
| Item 21 (REFERENCE CALIBRATION) preserved — regression check | OK |
| Phase 4 item 7 (STRATEGY SECTION) preserved — regression check | OK |
| Function signature `_build_prompt(state: OrchestratorState) -> str:` unchanged | OK |
| `_PASS_FILL_TIMEOUT = 600` unchanged | OK |
| File line count: 443 (was 362; +81 for docstring + EXAMPLES block) | OK |
| Prompt block length: 18302 chars (~4575 tokens, <20KB budget) | OK |
| `run_pass_fill_assemble` still async | OK |
| No file deletions in commit (post-commit check) | OK |

## Prompt Token Cost Estimate

- **Before Plan 05-03:** ~13900 chars (~3475 tokens)
- **After Plan 05-03:** ~18302 chars (~4575 tokens)
- **Delta:** +4402 chars (~1100 tokens)
- **Per presale call:** One Pass 3 invocation per report — adds ~1.1K tokens to system prompt
- **DeepSeek V4 Pro context:** 128K tokens — 1.1K delta is <1% of context budget
- **Cost impact:** Negligible (sub-cent per report at DeepSeek pricing)

## Decisions Made

- **Calibration block placed AFTER item 21 (not as item 22).** Alternative considered: insert as new numbered item 22. Rejected because (a) it would require renumbering if more rules are added later, (b) the block is structurally different from rules (it's an APPENDIX of examples, not a new rule), (c) placing after the closing rule «возвращайся к референсу как канону» reads naturally — «here's the canon, and here are the concrete examples».
- **Each example prefixed with section-type label (Секция NN (Name)).** LLM needs explicit anchors to know which section type each example targets. Without labels, LLM treats examples as generic style samples; with labels, LLM can directly map «I'm generating Секция 06 (Competitor Cards) — let me check the Секция 06 example».
- **Anti-overfitting disclaimer at block header.** T-05-03-T threat (LLM copying ИПХиК numbers like «4.3 млрд» into unrelated client reports) is real — DeepSeek V4 Pro follows few-shot examples closely. Disclaimer «НЕ копируй конкретные цифры — бери цифры из данных клиента» + existing ORC-04 honest principle + Plan 05-01 item 16 «с цифрами из данных» together mitigate this.
- **Two cross-references spanning different section pairs.** Showing only one cross-ref pattern would suggest cross-refs are limited to that pair. Two examples (Content↔Experts, Strategy↔Content) demonstrate the GENERAL pattern applies across any section boundary.
- **Two blockquotes with distinct purposes.** Секция 02 blockquote («Отрыв не в деньгах») is a strategic INSIGHT about the current state. Секция 09 blockquote («рост органического трафика») is a PROJECTION about expected outcome. Showing both purposes prevents LLM from defaulting to only one blockquote style.
- **ОБЩИЕ ПРИНЦИПЫ block placed AFTER concrete examples.** Pedagogical principle: concrete-first, abstract-second. LLM sees the examples inductively, then the abstract rules serve as deductive reinforcement. Mirrors the structure of Plan 05-01 items 16-20 but in plain language derived from the examples themselves.
- **Examples preserve original Russian text verbatim from reference** (no translation). Plan extraction rule 6 «Preserve original Russian text». Reference is Russian; client reports are Russian; examples must be Russian.

## Deviations from Plan

None — plan executed exactly as written. The plan provided exact text for each example (lines 147-213 of PLAN.md); the executor embedded that text verbatim with minor formatting adjustments (header includes anti-overfitting clause from the plan's threat model mitigation, section labels use consistent «Секция NN» format).

**Total deviations:** 0

## Issues Encountered

None.

## User Setup Required

None — pure Python prompt-string change, no external services or environment variables.

## Threat Model Compliance

| Threat | Mitigation Status |
|--------|------------------|
| T-05-03-T (Tampering — LLM could mimic examples too literally, copying reference numbers instead of using client data) | mitigate — anti-overfitting disclaimer at block header «НЕ копируй конкретные цифры — бери цифры из данных клиента; эти образцы показывают СТИЛЬ и ГЛУБИНУ»; existing ORC-04 honest principle (Phase 2) + Plan 05-01 item 16 «с цифрами из данных» both still enforced; ОБЩИЕ ПРИНЦИПЫ block reinforces «каждая цифра сопровождается сравнением» (comparison requires client data, not reference data) |
| T-05-03-I (Info disclosure — reference examples contain real clinic data ИПХиК revenue, doctor names) | accept — reference is a PUBLIC document already shared with the client as a sales asset; embedding in LLM prompt doesn't expose new data; LLM has its own collected data for the actual client |
| T-05-03-D (DoS — more examples → longer prompt → more tokens) | accept — prompt expansion +4.4KB (~1.1K tokens); total prompt 18.3KB (~4.6K tokens), sub-4% of DeepSeek 128K context; existing `_PASS_FILL_TIMEOUT=600s` sufficient |
| T-05-03-E (EoP — not applicable) | accept — pure prompt text expansion, no privilege change |
| T-05-03-SC (Supply chain — no new packages) | accept — pure Python string changes |

## Next Phase Readiness

- **Ready for downstream consumers:**
  - **Phase 7 (Test on 3 Niches):** Few-shot anchors are the primary defense against LLM style drift. Test reports MUST show reference-style depth across all 10 sections. If any section type consistently produces weak output in Phase 7 testing, add more examples for that specific section in a future plan.
  - **Future prompt tuning:** Prompt token budget has ~107KB remaining (128K context - 18.3K prompt - ~2K output reservation - other context). Comfortable headroom for future Phase 6/7 additions.
- **No blockers** — code is local-only (not deployed), deployment happens in Phase 8 (Zero-Downtime Deploy). The `pass_fill_assemble.py` module already runs in the container (deployed in Plan 04-08); this plan's text-only changes will be deployed via `docker cp` in Phase 8 alongside any other Phase 5+ prompt updates.

## Self-Check: PASSED

- ✓ `AIM/hermes/app/orchestrator/pass_fill_assemble.py` — file exists, AST parses cleanly, 443 lines (was 362 — +81 for docstring + EXAMPLES block)
- ✓ Commit `8015c1f` — FOUND in git log (Task 1: EXAMPLES BY SECTION calibration block)
- ✓ All plan verification assertions pass (header present, 10 sections, cross-references, gap-blocks ✅/📍, blockquotes, regression items 16+21 preserved, Phase 4 item 7 preserved, function signature + timeout unchanged)
- ✓ Regression: Phase 3 items 1-6 (fill gaps, generate_html_report, ORC-04 honest, coverage_metadata, niche, instagram_data) preserved
- ✓ Regression: Phase 4 items 7-15 (Strategy, Offer, Whitefields, Experts, Content, Revenue, Clinic metrics, Media, Ratings) preserved
- ✓ Regression: Plan 05-01 items 16-21 (NARRATIVE STYLE, BUSINESS LANGUAGE, CROSS-REFERENCES, GAP-BLOCK FORMAT, SECTION BLOCKQUOTE, REFERENCE CALIBRATION) preserved
- ✓ Function signature unchanged: `_build_prompt(state: OrchestratorState) -> str`
- ✓ `_PASS_FILL_TIMEOUT=600` unchanged
- ✓ `run_pass_fill_assemble` body unchanged (still async, still uses `_get_agent_for_session`)
- ✓ No file deletions in commit (post-commit check)
- ✓ Prompt block 18302 chars < 20000 budget

---
*Phase: 05-deep-interpretation*
*Completed: 2026-06-24T03:27:24Z*
