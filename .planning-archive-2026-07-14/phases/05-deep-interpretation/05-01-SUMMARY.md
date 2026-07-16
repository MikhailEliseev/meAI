---
phase: 05-deep-interpretation
plan: 01
subsystem: orchestrator
tags: [orchestrator, pass3, prompt, narrative, business-language, cross-references, gap-blocks, blockquote, reference-calibration, int-01, int-02, int-03, int-04, int-05, d-02, d-03, d-04, d-05, d-06, d-07, d-09, d-10, d-11]

# Dependency graph
requires:
  - "04-05: Pass 3 _build_prompt items 7-15 (Phase 4 section generation rules — target of Phase 5 additive extension)"
  - "05-CONTEXT: D-01..D-12 locked decisions for narrative quality rules"
provides:
  - "Pass 3 _build_prompt extended with cross-cutting narrative quality rules (items 16-21)"
  - "Items 16-18 (Task 1): NARRATIVE STYLE, BUSINESS LANGUAGE dictionary, CROSS-REFERENCES rule"
  - "Items 19-21 (Task 2): GAP-BLOCK FORMAT with ✅/📍 emoji, SECTION BLOCKQUOTE with section-insight CSS class, REFERENCE CALIBRATION to ИПХиК (2).html"
  - "Two new kwarg contracts for downstream Plan 05-02: gap_blocks (list[dict]) and insight (str)"
  - "INT-01..05 SATISFIED at prompt layer (HTML rendering deferred to Plan 05-02)"
affects:
  - "05-02 (HTML renderers extend): must render gap_blocks list + insight string per section per new prompt kwarg contract"
  - "05-03 (Reference calibration follow-up): may add more few-shot examples from ИПХиК (2).html if LLM style drift detected"
  - "Phase 7 (Test on 3 Niches): narrative quality will be the primary acceptance criterion for report acceptance"
  - "generate_html_report consumer (Plan 05-02): must accept gap_blocks + insight kwargs in each _build_*_section signature"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Cross-cutting narrative quality rules appended AFTER per-section generation rules (items 7-15) — preserves LLM attention hierarchy"
    - "Reference-anchored prompt calibration — ИПХиК (2).html serves as few-shot canon embedded directly in prompt item 21"
    - "Business-language translation dictionary — 5 entries (LCP/Bounce rate/CLS/DA/Backlinks) with literal translation phrases the LLM must use ALONGSIDE the metric value"
    - "Kwarg contract documentation in prompt — each narrative rule names the exact kwarg the LLM must pass to generate_html_report"
    - "Emoji-delimited structured format — ✅ (strength) and 📍 (growth point) provide visual anchors that survive LLM paraphrasing"

key-files:
  created: []
  modified:
    - AIM/hermes/app/orchestrator/pass_fill_assemble.py

key-decisions:
  - "Items 16-21 appended AFTER items 1-15 (not inserted mid-prompt) — Phase 3 instagram/niche items and Phase 4 section generation rules dominate LLM attention budget; narrative quality rules are refinement layer applied to already-generated section content"
  - "Item 16 NARRATIVE STYLE includes literal contrast pair: «Выручка: 4.3 млрд» (bad, metric dump) vs «Клиника ИПХиК стабильно удерживает топ-3 позицию» (good, narrative with number) — concrete negative example eliminates LLM's temptation to default to metric dump"
  - "Item 17 BUSINESS LANGUAGE uses Russian translations of technical jargon — culturally aligned with Russian clinic clients and Russian-language reference HTML; numbers stay in original form (LCP 7.3s) with human interpretation appended, not replacing"
  - "Item 18 CROSS-REFERENCES gives 4 explicit patterns (Strategy→fears, Offer→gaps, Content→Experts, Whitefields→all) — without specific pattern templates the LLM treats cross-references as optional; named patterns make them mandatory"
  - "Item 19 gap_blocks kwarg contract documented as list[dict] with type field ('strength'|'growth') — structured for Plan 05-02 HTML renderer to iterate and apply CSS classes (.gap-strength, .gap-growth) per CONTEXT D-08"
  - "Item 20 insight kwarg documented as string (not dict) — single blockquote per section, simplifies HTML rendering"
  - "Item 21 includes 4 few-shot narrative examples (About +79% / Market лидер / Strategy активы / Offer система) — concrete style anchors reduce LLM drift across diverse clinic niches"
  - "Plan internal inconsistency in Task 1 verification assertion (expected 'задержка' but plan action specifies 'задержки' Russian genitive inflection) — relaxed to substring 'задержк' which matches plan action spec literally"

patterns-established:
  - "Pattern: cross-cutting quality rules — when a prompt needs both per-section generation rules AND style/format rules, generation rules come first (items 7-15), quality rules appended after (items 16-21)"
  - "Pattern: kwarg contract documentation in prompt — each prompt item names the kwarg the LLM must pass to the downstream tool, enabling clean separation between prompt layer (this plan) and HTML rendering layer (Plan 05-02)"
  - "Pattern: reference-anchored calibration — when targeting a specific output style, embed few-shot examples from the reference directly in the prompt with section labels (Секция About/Market/Strategy/Offer)"
  - "Pattern: emoji-delimited structured output — ✅ and 📍 as semantic delimiters that survive LLM paraphrasing, enabling reliable HTML extraction in downstream renderer"

requirements-completed: [INT-01, INT-02, INT-03, INT-04, INT-05]

# Metrics
duration: 5min
completed: 2026-06-24
---

# Phase 5 Plan 05-01: Pass 3 Prompt — Narrative Quality Rules Summary

**Pass 3 `_build_prompt` extended with 6 cross-cutting narrative quality rules (items 16-21) transforming section content from metric dumps into business-language narratives calibrated to the `ИПХиК (2).html` reference: 2-3 paragraphs per section (item 16), 5-entry business jargon dictionary (item 17), inter-section cross-references (item 18), ✅ strength + 📍 growth gap-blocks with competitor benchmarks (item 19), section-ending strategic insight blockquote with `section-insight` CSS class (item 20), and 4 embedded few-shot narrative examples from the reference HTML (item 21).**

## Performance

- **Duration:** ~5 min (PLAN_START 02:17:24Z → PLAN_END 02:22:30Z, 306s)
- **Started:** 2026-06-24T02:17:24Z
- **Completed:** 2026-06-24T02:22:30Z
- **Tasks:** 2 (Task 1: items 16-18; Task 2: items 19-21)
- **Files modified:** 1 (`AIM/hermes/app/orchestrator/pass_fill_assemble.py`)
- **Commits:** 2 (one per task) + 1 metadata commit (SUMMARY + STATE)
- **Lines added:** 105 (54 Task 1 + 51 Task 2)

## Accomplishments

- **6 new numbered items (16-21) appended** to the existing 15-item `_build_prompt` return string. Total prompt items: 21.
- **Module docstring updated** with Phase 5 / Plan 05-01 context block — documents narrative quality rules added in Tasks 1+2.
- **INT-01 (narrative rewrite) SATISFIED at prompt layer** — item 16 NARRATIVE STYLE rule with concrete good/bad example pair.
- **INT-02 (cross-linked sections) SATISFIED at prompt layer** — item 18 CROSS-REFERENCES with 4 explicit inter-section patterns (Strategy→fears, Offer→gaps, Content→Experts, Whitefields→all).
- **INT-03 (business language) SATISFIED at prompt layer** — item 17 BUSINESS LANGUAGE with 5-entry jargon translation dictionary (LCP, Bounce rate, CLS, DA, Backlinks).
- **INT-04 (gap-blocks format) PARTIALLY SATISFIED** — item 19 GAP-BLOCK FORMAT with ✅/📍 structure documented + `gap_blocks` kwarg contract (list[dict]); HTML rendering deferred to Plan 05-02.
- **INT-05 (blockquote per section) PARTIALLY SATISFIED** — item 20 SECTION BLOCKQUOTE with `<blockquote class="section-insight">` HTML format + `insight` kwarg contract (string); HTML rendering deferred to Plan 05-02.
- **D-11 reference calibration** — item 21 embeds 4 few-shot narrative examples extracted from `ИПХиК (2).html` (About +79% revenue dynamics, Market leadership phrasing, Strategy chain-of-arguments, Offer concrete USP).
- **Two new kwarg contracts documented** for downstream Plan 05-02 HTML renderers: `gap_blocks` (list of `{'type': 'strength'|'growth', 'title': str, 'description': str}` dicts) and `insight` (string per section).
- **Function signature unchanged:** `_build_prompt(state: OrchestratorState) -> str`
- **`_PASS_FILL_TIMEOUT=600` unchanged** — prompt expansion is text-only, doesn't affect runtime characteristics.
- **`run_pass_fill_assemble` body unchanged** — only the prompt builder was modified.

## Task Commits

1. **Task 1: Add prompt items 16-18 (narrative style + business language + cross-references)** — `2b8a64d` (feat)
2. **Task 2: Add prompt items 19-21 (gap-block format + section blockquote + reference calibration)** — `48447ad` (feat)

## Files Modified

| File | Lines Changed | Reason |
|------|---------------|--------|
| `AIM/hermes/app/orchestrator/pass_fill_assemble.py` | +105/-2 | Module docstring updated with Phase 5 block; items 16-21 appended to return string (NARRATIVE STYLE, BUSINESS LANGUAGE, CROSS-REFERENCES, GAP-BLOCK FORMAT, SECTION BLOCKQUOTE, REFERENCE CALIBRATION) |

## Items Added to `_build_prompt` (Items 16-21)

| Item | Rule | Req | D-Ref | Key Constraints |
|------|------|-----|-------|-----------------|
| 16 | NARRATIVE STYLE | INT-01 | D-02 | 2-3 paragraphs per section with conclusions and numbers; explicit good («ИПХиК топ-3») vs bad («Выручка: 4.3 млрд») example; rule triple (a/b/c) for paragraph structure |
| 17 | BUSINESS LANGUAGE | INT-03 | D-05, D-06 | 5-entry translation dictionary (LCP/Bounce/CLS/DA/Backlinks); numbers stay accompanied by human interpretation, not replaced |
| 18 | CROSS-REFERENCES | INT-02 | D-03, D-04 | Minimum 1 cross-ref per section; 4 explicit patterns (Strategy→04, Offer→gaps, Content→03, Whitefields→all); LLM-generated, no hardcod links |
| 19 | GAP-BLOCK FORMAT | INT-04 | D-07 | 2-4 gap-blocks per section with ✅ strength (data number) + 📍 growth (competitor benchmark); `gap_blocks` kwarg = list[dict] with type/title/description fields |
| 20 | SECTION BLOCKQUOTE | INT-05 | D-09, D-10 | Each section ends with `<blockquote class="section-insight">`; `insight` kwarg = string; ORC-04 honest principle when no insight possible |
| 21 | REFERENCE CALIBRATION | — | D-11 | `ИПХиК (2).html` as canonical style truth; 4 embedded few-shot examples (About/Market/Strategy/Offer) |

## Verification Results

| Check | Result |
|-------|--------|
| AST parse: `pass_fill_assemble.py` syntax valid | OK |
| Numbered items count: 21 (was 15 after Phase 4) | OK |
| Item 16 NARRATIVE STYLE present | OK |
| Item 17 BUSINESS LANGUAGE present | OK |
| Item 18 CROSS-REFERENCES present | OK |
| Item 19 GAP-BLOCK FORMAT present | OK |
| Item 20 SECTION BLOCKQUOTE present | OK |
| Item 21 REFERENCE CALIBRATION present | OK |
| ✅ strength emoji present | OK |
| 📍 growth emoji present | OK |
| `section-insight` CSS class referenced | OK |
| `ИПХиК (2).html` reference pointer | OK |
| Few-shot example `+79% за 3 года` embedded | OK |
| LCP business translation: «каждая секунда задержк[и]» | OK (Rule 1 deviation — see below) |
| Bounce rate business translation present | OK |
| `страхи пациентов` cross-ref keyword present | OK |
| D-02..D-11 decision references all present | OK |
| REGRESSION: Phase 3 items 1-6 preserved | OK |
| REGRESSION: Phase 4 items 7-15 markers preserved (STRATEGY SECTION, OFFER SECTION, WHITEFIELDS MATRIX, EXPERTS SECTION, CONTENT ANALYSIS, REVENUE DYNAMICS, CLINIC METRICS, MEDIA URLS, RATINGS) | OK |
| Function signature: `_build_prompt(state: OrchestratorState) -> str` | OK |
| `_PASS_FILL_TIMEOUT == 600` | OK |
| `run_pass_fill_assemble` is async | OK |
| File line count: 362 (was 257 after Phase 4; min required 290) | OK |
| Prompt block size: ~13.9KB (was 6.5KB after Phase 4) | OK |

## Prompt Token Cost Estimate

- **Before Phase 5:** ~6480 chars (~1620 tokens at 4 chars/token for Russian text)
- **After Phase 5:** ~13900 chars (~3475 tokens)
- **Delta:** +7420 chars (~1855 tokens)
- **Per presale call:** One Pass 3 invocation per report — adds ~1.9K tokens to system prompt
- **DeepSeek V4 Pro context:** 128K tokens — 1.9K delta is ~1.5% of context budget
- **Cost impact:** Negligible (sub-cent per report at DeepSeek pricing)

## Decisions Made

- **Items 16-21 appended AFTER Phase 4 items 7-15** (not inserted mid-prompt). The Phase 3+4 items define WHAT to generate per section (kwarg names, source data fields); the Phase 5 items define HOW to write each section (narrative style, business language, cross-refs). Placing quality rules AFTER generation rules preserves the LLM's focus on data coverage first, then refinement.
- **Item 16 includes explicit bad/good example pair** (metric dump vs narrative). Without the negative example, LLMs default to safe-but-unhelpful metric-dump format because that's what most training data looks like. The contrast pair telegraphs the desired transformation.
- **Item 17 translation dictionary has 5 fixed entries** (not exhaustive). Adding all possible technical jargon would bloat the prompt. The 5 entries cover the most common metric-dump offenders in presale reports (LCP/Bounce rate/CLS for technical SEO, DA/Backlinks for authority). Other metrics fall under general item 17 rule «сопровождай человеческой интерпретацией».
- **Item 18 specifies 4 explicit cross-reference patterns**. Generic «add cross-references» instructions are ignored by LLMs. Naming the specific section-to-section pattern pairs (Strategy↔fears, Offer↔gaps, Content↔Experts, Whitefields↔all) makes the rule testable and unambiguous.
- **Item 19 gap_blocks contract = list[dict]** with type field. Alternative considered: separate `strengths` and `growth_points` kwargs. Rejected because (a) interleaving strengths and growths in narrative order tells a better story, (b) single list is simpler for HTML renderer to iterate.
- **Item 20 insight contract = string** (not dict). Single blockquote per section doesn't need structured fields. String is the simplest contract.
- **Item 21 embeds 4 few-shot examples directly in prompt** (not separate reference file). Alternative considered: tell LLM to read `ИПХиК (2).html` at runtime. Rejected because (a) the file is on user's local machine, not in container, (b) embedding examples in prompt is faster (no file I/O), (c) curated examples are higher-quality than raw HTML scraping.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Task 1 verification assertion inflection mismatch**
- **Found during:** Task 1 (Add prompt items 16-18)
- **Issue:** Plan's verification assertion `assert 'LCP' in content and 'задержка' in content` requires exact substring `'задержка'`, but plan action specifies text using `'задержки'` (Russian genitive inflection after «секунда»). The two strings are different character sequences (`задержка` vs `задержки`) — natural Russian grammar dictates genitive case here, which the plan action correctly encodes.
- **Fix:** Relaxed verification to `'задержк'` (shared stem) which matches both the plan action specification AND the literal text added to the prompt. The semantic intent (LCP → delay → loses patients) is fully encoded in the prompt.
- **Files modified:** none (verification logic only — no source code change)
- **Verification:** AST parse OK; `grep -c 'задержк' AIM/hermes/app/orchestrator/pass_fill_assemble.py` returns 3 (one in narrative style example, two in business language dictionary entries).
- **Committed in:** `2b8a64d` (Task 1 commit; deviation documented in commit body)

---

**Total deviations:** 1 auto-fixed (1 bug in plan verification logic)
**Impact on plan:** Zero impact on deliverable. Source code matches plan action specification verbatim. Only the verification assertion was relaxed to match Russian grammar rules. No scope creep.

## Issues Encountered

None.

## User Setup Required

None — pure Python prompt-string change, no external services or environment variables.

## Threat Model Compliance

| Threat | Mitigation Status |
|--------|------------------|
| T-05-01-T (Tampering — LLM could fabricate narrative not based on data) | mitigate — item 16 explicitly says «с цифрами из данных»; item 21 (reference calibration) anchors to real reference style; item 20 (blockquote) references ORC-04 honest principle for «данные недоступны» case; existing item 3 ORC-04 enforcement preserved |
| T-05-01-I (Info disclosure — prompt rules describe how to write about collected data) | accept — no new data exposed; LLM already has Pass 1 history; prompt just instructs how to format |
| T-05-01-D (DoS — longer prompt → more LLM tokens per Pass 3 invocation) | accept — prompt expansion ~7.4KB (~1.9K tokens); sub-2% of DeepSeek V4 Pro 128K context budget; existing `_PASS_FILL_TIMEOUT=600s` sufficient |
| T-05-01-E (EoP — not applicable) | accept — pure prompt text expansion, no privilege change |
| T-05-01-X (XSS — item 20 instructs LLM to generate `<blockquote class="section-insight">`) | mitigate — this plan is prompt-only; the LLM output is NOT injected raw into final HTML; it flows through `generate_html_report._esc()` helper in Plan 05-02 (HTML rendering layer). No raw HTML rendering in this plan. |
| T-05-01-SC (Supply chain — no new packages) | accept — pure Python string changes |

## Next Phase Readiness

- **Ready for downstream consumers:**
  - **05-02 (HTML renderers extend):** Can now implement HTML rendering for the 2 new kwargs contracts: `gap_blocks` (list[dict] with type/title/description fields) per item 19, and `insight` (string) per item 20. Each of the 10 `_build_*_section` functions needs to accept these kwargs and render design-system HTML (`<blockquote class="section-insight">` and `.gap-block` / `.gap-strength` / `.gap-growth` CSS classes per CONTEXT D-08).
  - **05-03 (Reference calibration follow-up):** Item 21 already embeds 4 few-shot examples. Plan 05-03 can extend with more examples if LLM style drift is detected during Phase 7 testing.
  - **Phase 7 (Test on 3 Niches):** Narrative quality rules in items 16-21 are the primary acceptance criteria. Test reports MUST show 2-3 paragraphs per section (item 16), business jargon translations (item 17), inter-section references (item 18), gap-blocks with competitor benchmarks (item 19), section blockquotes (item 20), and reference-style depth (item 21).
- **No blockers** — code is local-only (not deployed), deployment happens in Phase 8 (Zero-Downtime Deploy).

## Self-Check: PASSED

- ✓ `AIM/hermes/app/orchestrator/pass_fill_assemble.py` — file exists, AST parses cleanly, 362 lines (was 257 — +105 for items 16-21 + docstring update)
- ✓ Commit `2b8a64d` — FOUND in git log (Task 1: items 16-18 narrative + business + cross-references)
- ✓ Commit `48447ad` — FOUND in git log (Task 2: items 19-21 gap-block + blockquote + reference)
- ✓ All plan verification assertions pass (21 items, all required patterns present, D-02..D-11 rules encoded)
- ✓ Regression: Phase 3 items 1-6 (fill gaps, generate_html_report, ORC-04 honest, coverage_metadata, niche, instagram_data) preserved
- ✓ Regression: Phase 4 items 7-15 (Strategy, Offer, Whitefields, Experts, Content, Revenue, Clinic metrics, Media, Ratings) preserved
- ✓ Function signature unchanged: `_build_prompt(state: OrchestratorState) -> str`
- ✓ `_PASS_FILL_TIMEOUT=600` unchanged
- ✓ `run_pass_fill_assemble` body unchanged (still async, still uses `_get_agent_for_session`)
- ✓ min_lines requirement (290) satisfied — file has 362 lines

---
*Phase: 05-deep-interpretation*
*Completed: 2026-06-24T02:22:30Z*
