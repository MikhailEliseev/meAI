---
phase: 03-instagram-integration
plan: 04
subsystem: orchestrator
tags: [orchestrator, prompt-engineering, adaptive-top5, doctor-discovery, batch-cohort, instagram-active, d-10, d-11]

# Dependency graph
requires:
  - phase: 03-instagram-integration
    provides: 03-03 — niche-aware Pass 1 + Pass 2 prompt scaffolding (instagram_rule conditional block + _CHECKLIST_PROMPT_TEMPLATE niche_instruction placeholder)
  - phase: 03-instagram-integration
    provides: 03-06 — runtime hard-FAIL override (independent of this prompt-only plan)
  - phase: 03-instagram-integration
    provides: 03-02 — state.niche + state.collected_data["niche_detection"] populated by mini-call
provides:
  - pass_collect._build_pass_collect_prompt — rule 5 added to critical branch (ADAPTIVE TOP-5 RULE)
  - pass_collect._build_pass_collect_prompt — shorter ADAPTIVE TOP-5 NOTE added to non-critical branch
  - pass_gap_analyze._CHECKLIST_PROMPT_TEMPLATE — new "АДАПТИВНЫЕ ПРАВИЛА ДЛЯ ПУНКТОВ 4 / 6 / 7" block
  - Pass 1 prompt references run_instagram_content batch response field "top_by_followers" (load-bearing)
  - Pass 2 prompt references "top_by_followers" + content_gaps fields (load-bearing)
  - D-09 reinforced: find_doctor_handles primary source (called FIRST in Pass 1 per Plan 03-03, cohort logic added here)
  - D-10 satisfied: adaptive top-5 selection logic (site-position primary, followers_count fallback)
  - D-11 satisfied: batch size 8-10 (single run_instagram_content call per presale)
affects: [03-05, phase-04, phase-08]

# Tech tracking
tech-stack:
  added: []  # no new libraries — pure Python stdlib (ast for verification)
  patterns:
  - "Two-cohort prompt pattern: site-top-5 (титулованные эксперты, могут быть без Instagram) vs Instagram-active-top-5 (from top_by_followers). Both cohorts legitimate, different report sections."
  - "Adaptive fallback rule: IF site-top-5 returns 5 'no data' results THEN pick top-5 for section 04 from top_by_followers array (Instagram-active cohort)"
  - "Section routing rule: section 03 (Experts) shows BOTH cohorts (regalia + metrics); section 04 (Content Analysis) uses ONLY Instagram-active cohort (no content to analyze otherwise)"
  - "Cohort-aware QC items: item 4 (Experts) filled if >=3 doctors with ФИО + (regalia OR Instagram metrics); item 6 (Content themes) filled if >=3 themes from any Instagram-active doctor; item 7 (Content gaps) filled if >=2 gaps with severity from any profile's content_gaps field"
  - "Load-bearing field reference: prompt mentions 'top_by_followers' explicitly so LLM knows which batch-response field to consult (matches run_instagram_content.py line 140 schema)"
  - "Defensive 'is_critical=False' adaptive note: optional Instagram path still applies cohort logic if LLM decides to call run_instagram_content"
  - "Bilingual cohort labels: 'Instagram-active' (English) + 'титулованные эксперты' / 'КМН' / 'профессора' (Russian) — matches LLM working language"

key-files:
  created: []
  modified:
  - AIM/hermes/app/orchestrator/pass_collect.py (+51 lines: rule 5 adaptive top-5 for critical branch + ADAPTIVE TOP-5 NOTE for non-critical branch + module + helper docstring updates)
  - AIM/hermes/app/orchestrator/pass_gap_analyze.py (+18 lines: new adaptive-cohort block for items 4/6/7 in _CHECKLIST_PROMPT_TEMPLATE + module docstring update)

key-decisions:
  - "Rule 5 placed AFTER existing rules 1-4 (not before) — preserves Plan 03-03 ordering rule (find_doctor_handles FIRST) as rule 1; adaptive top-5 is a post-batch rule, conceptually downstream of the ordering rule"
  - "ADAPTIVE TOP-5 NOTE added to is_critical=False branch (not just critical) — non-critical niches may still optionally call run_instagram_content; if they do, they should apply the same cohort logic for consistency"
  - "Field name 'top_by_followers' referenced VERBATIM in prompt text (not paraphrased) — the LLM needs the exact JSON key to extract the cohort from the batch response. Mismatched name would break the adaptive fallback."
  - "Two-cohort model used consistently across Pass 1 + Pass 2: site-top-5 cohort (сайт-top + регалии) + Instagram-active cohort (top_by_followers). Section routing: section 03 = both, section 04 = Instagram-active only."
  - "Russian title 'КМН, профессора' included verbatim in prompt — matches the typical real-world titles of site-top-5 doctors who don't have Instagram (per CONTEXT.md 'Specific Ideas' section)"
  - "Batch size 8-10 referenced in BOTH critical and non-critical branches — D-11 applies to both paths (critical: mandatory batch; non-critical: optional batch if LLM decides to call)"
  - "Item 4 rule: 'filled if >=3 doctors with ФИО + (regalia OR metrics)' — lenient OR (not strict AND) because site-top-5 doctors have regalia but no metrics, Instagram-active doctors have metrics but may have fewer regalia"
  - "Item 6 rule explicitly says 'Не требует тем для всех топ-5 сайта' — prevents LLM from marking item 6 missing just because site-top-5 has no Instagram content"
  - "Module docstring (pass_collect.py) updated with new paragraph documenting Phase 3 / D-10 + D-11 adaptive cohort logic — downstream agents reading the docstring see the full picture"
  - "Helper docstring (_build_pass_collect_prompt) extended with 'Per Phase 3 / Plan 03-04' block — mirrors Plan 03-03 block structure for consistency"
  - "Adaptive rules block placed AFTER HARD-FAIL rule block in Pass 2 template — keeps HARD-FAIL (Plan 03-03) as the primary Instagram rule; adaptive cohort rules are secondary refinements for items 4/6/7"

patterns-established:
  - "Adaptive top-5 fallback in prompts: explicit IF/THEN structure ('if site-top-5 all no data THEN pick from top_by_followers'). LLM-applied at runtime — no Python code change needed for the fallback."
  - "Two-cohort model as canonical framing: 'сайт-top + Instagram-active' — both legitimate, different sections. Framing introduced in Pass 1, reinforced in Pass 2, will be rendered in HTML (Plan 03-05)."
  - "Cohort-aware QC item evaluation: items 4/6/7 filled based on cohort composition, not just raw count. Item 4 = ФИО + (regalia OR metrics); item 6 = themes from Instagram-active only; item 7 = gaps from any analyzed profile."
  - "Batch size in prompt text: '8-10 handles' — explicit number, not vague 'several'. LLM knows the exact batch size to pass to run_instagram_content."

requirements-completed: [IG-03]

# Metrics
duration: 3.2min
completed: 2026-06-23
---

# Phase 3 Plan 04: Adaptive Top-5 Doctor Discovery (Pass 1+2 Prompts) Summary

**Pass 1 prompt now encodes the adaptive top-5 cohort selection rule (D-10): if a clinic's site-top-5 doctors are all tituled experts without Instagram (5 'no data' results from run_instagram_content), the LLM picks the top-5 for section 04 (Content Analysis) from the batch response's `top_by_followers` field — the Instagram-active cohort, which may be doctors #6-#10 on the site. Section 03 (Experts) shows BOTH cohorts with regalia + metrics; section 04 uses only the Instagram-active cohort. Pass 2 prompt now includes cohort-aware evaluation rules for items 4, 6, 7 — item 4 filled if >=3 doctors with ФИО + (regalia OR Instagram metrics); item 6 filled if >=3 themes from any Instagram-active doctor; item 7 filled if >=2 gaps with severity from any profile's content_gaps field. Plan 03-03 rules (HARD-FAIL, niche_instruction, not_applicable, find_doctor_handles ordering, batch 8-10, D-06 retry) all preserved.**

## Performance

- **Duration:** ~3.2 min (start 18:14:59Z, end 18:18:12Z)
- **Tasks:** 2/2 complete (all `type="auto"`, no checkpoints)
- **Files modified:** 2 (pass_collect.py, pass_gap_analyze.py)
- **Files created:** 0
- **Commits:** 2 task commits + 1 final docs commit (this SUMMARY)

## Accomplishments

- Pass 1 prompt (`_build_pass_collect_prompt` critical branch) extended with rule 5 "ADAPTIVE TOP-5 RULE":
  - Explains site-top-5 vs Instagram-active-top-5 cohort divergence
  - Explicit fallback: if site-top-5 returns 5 'no data' results → pick top-5 for section 04 from `top_by_followers` field
  - Section 03 shows BOTH cohorts; section 04 uses Instagram-active cohort only
  - Normalizes "профессор КМН без Instagram" as a valid expert for section 03 but not section 04
- Pass 1 prompt (`_build_pass_collect_prompt` non-critical branch) extended with shorter "ADAPTIVE TOP-5 NOTE":
  - Optional Instagram path still applies cohort logic
  - Covers non-critical niches that decide to call run_instagram_content anyway
- Pass 2 prompt (`_CHECKLIST_PROMPT_TEMPLATE`) extended with new block "АДАПТИВНЫЕ ПРАВИЛА ДЛЯ ПУНКТОВ 4 (Experts) И 6 (Content themes) И 7 (Content gaps)":
  - Item 4 (Experts): filled if >=3 doctors with ФИО + at least one of (a) regalia from site OR (b) Instagram metrics from batch response
  - Item 6 (Content themes): filled if >=3 themes with percentages from any Instagram-active doctor (from `top_by_followers`) — does NOT require themes for all site-top-5
  - Item 7 (Content gaps): filled if >=2 gaps with severity from any analyzed profile's `content_gaps` field
- Module docstring (pass_collect.py) updated with Phase 3 / Plan 03-04 paragraph documenting D-10 + D-11 adaptive cohort logic
- Helper docstring (`_build_pass_collect_prompt`) extended with "Per Phase 3 / Plan 03-04" block mirroring Plan 03-03 block structure
- Module docstring (pass_gap_analyze.py) updated with Phase 3 / Plan 03-04 paragraph documenting cohort-aware items 4/6/7 evaluation
- All Plan 03-03 rules preserved byte-identical (find_doctor_handles ordering, batch 8-10, D-06 retry, HARD FAIL warning, niche_instruction placeholder, is_niche_instagram_critical import, not_applicable status)

## Task Commits

Each task was committed atomically:

1. **Task 1: Augment Pass 1 prompt with adaptive top-5 selection rule (D-10) + batch cohort explanation** — `9dfc630` (feat)
2. **Task 2: Augment Pass 2 prompt with adaptive-cohort evaluation guidance for items 4 (Experts), 6 (Content themes), and 7 (Content gaps)** — `44af99c` (feat)

**Plan metadata commit:** created after this SUMMARY.

## Files Modified

### `AIM/hermes/app/orchestrator/pass_collect.py` (+51 lines, -5 lines)

- Module docstring: added Phase 3 / Plan 03-04 paragraph documenting adaptive top-5 cohort selection rule (D-10) + batch size 8-10 (D-11)
- `_build_pass_collect_prompt` helper docstring: extended with "Per Phase 3 / Plan 03-04 (D-10 adaptive top-5 + D-11 batch size)" block documenting rule 5 + non-critical branch adaptive note
- `is_critical=True` branch: rule 4 changed from ending with `\n\n` to `\n`; new rule 5 "ADAPTIVE TOP-5 RULE" added with 5 sub-bullets:
  - find_doctor_handles returns top 8-10 by site position; top-5 site often == tituled experts (КМН, профессора) without Instagram
  - run_instagram_content batch JSON contains `top_by_followers` field — doctors sorted by followers_count
  - IF site-top-5 returns 5 'no data' results THEN pick top-5 for section 04 from `top_by_followers`
  - Section 03 (Experts) shows BOTH cohorts; section 04 (Content Analysis) uses Instagram-active cohort only
  - "профессор КМН без Instagram" = valid expert for section 03, not for section 04
- `is_critical=False` branch: rule changed from ending with `\n\n` to `\n`; new "ADAPTIVE TOP-5 NOTE" added — shorter adaptive cohort logic for optional Instagram path
- `_get_agent_for_session`, `_PASS_COLLECT_TIMEOUT` (600s), `run_pass_collect` body, exception handling unchanged

### `AIM/hermes/app/orchestrator/pass_gap_analyze.py` (+18 lines, -0 lines)

- Module docstring: added Phase 3 / Plan 03-04 paragraph documenting cohort-aware items 4/6/7 evaluation rules
- `_CHECKLIST_PROMPT_TEMPLATE`: new block "АДАПТИВНЫЕ ПРАВИЛА ДЛЯ ПУНКТОВ 4 (Experts) И 6 (Content themes) И 7 (Content gaps)" added AFTER the existing "ВАЖНОЕ ПРАВИЛО ДЛЯ INSTAGRAM (пункт 5)" block and BEFORE the JSON format instruction:
  - Item 4 rule: filled if >=3 doctors with ФИО + (regalia OR Instagram metrics); explicit mention of `top_by_followers` fallback path
  - Item 6 rule: filled if >=3 themes with percentages from any Instagram-active doctor; explicit note "Не требует тем для всех топ-5 сайта"
  - Item 7 rule: filled if >=2 gaps with severity from any profile's `content_gaps` field
- `run_pass_gap_analyze` body, `_extract_reply_text`, `_parse_gap_json`, `_ensure_summary`, `_fallback_report`, `_JSON_BLOCK_RE`, `_PASS_GAP_TIMEOUT` (240s), niche_instruction builder logic — all unchanged

## Pass 1 Adaptive Top-5 Rule (Critical Niche Branch, Rule 5)

```
5. ADAPTIVE TOP-5 RULE (важно для ниши {niche}):
   - find_doctor_handles вернёт топ-8-10 врачей по позиции на сайте клиники.
     Часто топ-5 на сайте — это титулованные эксперты (КМН, профессора) БЕЗ Instagram.
   - run_instagram_content batch вернёт JSON с полем 'top_by_followers' —
     это топ-doctors отсортированные по followers_count, кто РЕАЛЬНО ведёт соцсети.
   - Если топ-5 на сайте все без Instagram (5 ошибок 'no data') —
     ВЫБЕРИ top-5 для секции Content Analysis (04) из 'top_by_followers' поля
     (Instagram-active врачи, могут быть врачи #6-#10 на сайте).
   - Секция Experts (03) показывает ВСЕХ топ-врачей с регалиями
     (сайт-top + Instagram-active). Секция Content Analysis (04) —
     только для врачей с реальными Instagram метриками.
   - Это нормальная ситуация: 'профессор КМН без Instagram' — валидный
     эксперт для секции 03, но не подходит для секции 04 (нет контента для анализа).
```

## Pass 1 Adaptive Top-5 Note (Non-Critical Niche Branch)

```
ADAPTIVE TOP-5 NOTE: если всё же вызываешь run_instagram_content с batch handles
(8-10) — ответ содержит 'top_by_followers' поле (врачи отсортированные по
followers_count). Если топ-5 сайта без Instagram — бери top-5 для секции
Content Analysis (04) из 'top_by_followers'. Секция Experts (03) показывает
оба когорты (сайт-top с регалиями + Instagram-active с метриками).
```

## Pass 2 Adaptive-Cohort Items 4/6/7 Rules

```
АДАПТИВНЫЕ ПРАВИЛА ДЛЯ ПУНКТОВ 4 (Experts) И 6 (Content themes) И 7 (Content gaps):
- Пункт 4 (Experts) — status='filled' если есть ≥3 врачей с ФИО + хотя бы один из:
  (a) регалии с сайта клиники (КМН, профессор, стаж), ИЛИ
  (b) Instagram-метрики из run_instagram_content ответа.
  Если сайт-top-5 без Instagram, но в 'top_by_followers' есть ≥3 Instagram-active
  врачей — это filled. Если вообще нет ни ФИО, ни метрик — missing.
- Пункт 6 (Content themes) — status='filled' если есть ≥3 темы с процентами для любого
  из Instagram-active врачей (from 'top_by_followers'). Не требует тем для всех топ-5
  сайта — только для тех, у кого реально есть Instagram-контент.
- Пункт 7 (Content gaps) — status='filled' если есть ≥2 gaps с severity из
  run_instagram_content ответа (из поля 'content_gaps' любого проанализированного врача).
```

## Verification Artifacts

| Check | Result |
|-------|--------|
| `pass_collect.py` AST parse | OK (1 new rule 5 in critical branch + 1 new adaptive note in non-critical branch) |
| `pass_gap_analyze.py` AST parse | OK (1 new block "АДАПТИВНЫЕ ПРАВИЛА" in _CHECKLIST_PROMPT_TEMPLATE) |
| `_build_pass_collect_prompt` critical niche build | OK — contains "ADAPTIVE TOP-5 RULE", "top_by_followers", "КМН", "Content Analysis (04)", "Experts (03)" |
| `_build_pass_collect_prompt` non-critical niche build | OK — contains "ADAPTIVE TOP-5 NOTE", "top_by_followers", "Content Analysis (04)", "Experts (03)" |
| `_CHECKLIST_PROMPT_TEMPLATE.format(client_url, checklist_render, niche_instruction)` | OK — all 3 placeholders filled, adaptive block present |
| Pass 1 prompt references `top_by_followers` field | Yes (load-bearing field name from run_instagram_content.py line 140) |
| Pass 1 prompt mentions "КМН" or "профессора" | Yes (Russian titles for tituled experts without Instagram) |
| Pass 1 prompt references sections 03 + 04 | Yes (Experts + Content Analysis) |
| Pass 1 prompt batch size "8-10" | Yes (D-11 batch size) |
| Pass 2 prompt references `top_by_followers` | Yes (item 4 + item 6 rules) |
| Pass 2 prompt has item 4 evaluation rule | Yes (filled if >=3 doctors with ФИО + regalia OR metrics) |
| Pass 2 prompt has item 6 evaluation rule | Yes (filled if >=3 themes from any Instagram-active doctor) |
| Pass 2 prompt has item 7 evaluation rule | Yes (filled if >=2 gaps with severity from content_gaps) |
| Regression: Plan 03-03 `find_doctor_handles` rule (Pass 1) | Present (rule 1 unchanged) |
| Regression: Plan 03-03 `run_instagram_content` rule (Pass 1) | Present (rule 2 unchanged) |
| Regression: Plan 03-03 `instagram_critical` check (Pass 1) | Present (is_critical boolean unchanged) |
| Regression: Plan 03-03 D-06 retry rule (Pass 1) | Present (rule 3 unchanged) |
| Regression: Plan 03-03 HARD FAIL warning (Pass 1) | Present (rule 4 unchanged) |
| Regression: Plan 03-03 `niche_instruction` placeholder (Pass 2) | Present (line 79 unchanged) |
| Regression: Plan 03-03 `is_niche_instagram_critical` import (Pass 2) | Present (line 106 unchanged) |
| Regression: Plan 03-03 `not_applicable` status (Pass 2) | Present (line 82, 89 unchanged) |
| Regression: Plan 03-03 Instagram HARD-FAIL rule block (Pass 2) | Present (lines 86-89 unchanged) |
| Regression: `_PASS_COLLECT_TIMEOUT` (600s) | Unchanged |
| Regression: `_PASS_GAP_TIMEOUT` (240s) | Unchanged |
| Regression: `_get_agent_for_session` | Unchanged |
| Regression: `_extract_reply_text`, `_parse_gap_json`, `_ensure_summary`, `_fallback_report`, `_JSON_BLOCK_RE` | Unchanged |
| Regression: `ORCHESTRATOR_MODE=0` default path | Yes — all changes inside orchestrator/; main.py, agent_wrapper.py, engine.py untouched |
| Post-commit deletion check | None (no tracked files deleted across 2 commits) |
| Untracked file check | None created by this plan |

## Decisions Made

1. **Rule 5 placed AFTER rules 1-4 (not before)** — Preserves Plan 03-03 ordering rule (find_doctor_handles FIRST) as rule 1. Adaptive top-5 is conceptually downstream of the ordering rule: the LLM must first call find_doctor_handles (rule 1), then run_instagram_content (rule 2), then apply retry logic (rule 3), then respect HARD FAIL (rule 4), and only THEN apply adaptive top-5 logic to the batch response (rule 5). Order reflects runtime sequence.

2. **ADAPTIVE TOP-5 NOTE added to is_critical=False branch** — Non-critical niches may still optionally call run_instagram_content (e.g., dental clinic with active Instagram). If they do, they should apply the same cohort logic for consistency between critical and non-critical paths. Without this note, the non-critical branch would produce incoherent reports if Instagram was called (metrics scattered across both cohorts without routing rules).

3. **Field name `top_by_followers` referenced VERBATIM** — The exact JSON key from run_instagram_content.py batch response (line 140). The LLM needs the precise key name to extract the cohort via JSON path. A paraphrased name (e.g., "топ по подписчикам") would force the LLM to guess the field, increasing hallucination risk. Verified the field name against run_instagram_content.py source before committing.

4. **Two-cohort model (site-top + Instagram-active) introduced in Pass 1, reinforced in Pass 2** — Consistent vocabulary across passes ensures the LLM applies the same mental model when generating Pass 2 gap_report AND when generating Pass 3 HTML. Plan 03-05 (HTML rendering) can consume the same cohort framing.

5. **Russian titles "КМН" + "профессора" used verbatim** — These are the real-world Russian medical titles (Кандидат Медицинских Наук, профессор) typically held by site-top-5 doctors who don't maintain Instagram. Using the actual titles makes the prompt concrete for the LLM (DeepSeek V4 Pro, which handles Russian medical terminology fluently).

6. **Item 4 rule uses OR (not AND) for regalia/metrics** — A site-top-5 doctor may have regalia (КМН, стаж) but no Instagram metrics; an Instagram-active doctor may have metrics but fewer regalia (younger cosmetologist). The OR ensures both types count toward "filled". An AND would incorrectly mark item 4 missing when only one cohort provides data.

7. **Item 6 rule explicitly says "Не требует тем для всех топ-5 сайта"** — Defensive wording to prevent the LLM from marking item 6 missing just because site-top-5 has no Instagram content. Without this explicit note, the LLM might apply the literal pass criterion (">=3 themes with percentages per top doctor") to the wrong cohort.

8. **Item 7 rule references `content_gaps` field explicitly** — Matches run_instagram_content.py response schema (base["content_gaps"], line 383). The LLM needs the exact field name to extract gaps from the batch response profiles array.

9. **Adaptive rules block placed AFTER HARD-FAIL block in Pass 2 template** — HARD-FAIL (Plan 03-03, item 5) is the primary Instagram rule; adaptive cohort rules (items 4/6/7) are secondary refinements. Placing adaptive rules AFTER keeps the most critical rule (item 5) at the top of the LLM's attention.

10. **Module docstring + helper docstring updates mirror Plan 03-03 structure** — Each docstring block follows the "Phase 3 / Plan 03-0X (D-NN + D-MM):" pattern established by Plan 03-03. Future maintainers see a consistent narrative across Phase 3 plans.

## Deviations from Plan

None — plan executed exactly as written. Both tasks followed the action steps verbatim:

- Task 1: Module docstring updated with Phase 3 / D-10 paragraph ✓; helper docstring `_build_pass_collect_prompt` extended with Plan 03-04 block ✓; rule 5 added to `is_critical=True` branch AFTER existing rules 1-4 and BEFORE closing `\n\n` ✓; shorter adaptive note added to `is_critical=False` branch ✓; `state.niche` used for `{niche_label}` substitution ✓; Plan 03-03 rules preserved (no regression) ✓; function signature + timeout + exception handling unchanged ✓
- Task 2: Module docstring updated ✓; new section "АДАПТИВНЫЕ ПРАВИЛА ДЛЯ ПУНКТОВ 4 / 6 / 7" added AFTER Instagram HARD-FAIL block and BEFORE JSON format instruction ✓; all 3 item rules cover the two-cohort scenario ✓; Plan 03-03 niche_instruction + is_niche_instagram_critical + not_applicable preserved ✓; `_extract_reply_text`, `_parse_gap_json`, `_ensure_summary`, `_fallback_report`, `_JSON_BLOCK_RE`, `_PASS_GAP_TIMEOUT` unchanged ✓

## Known Stubs

None. All prompt logic is fully implemented across both branches (critical + non-critical) of Pass 1 and fully integrated into Pass 2 template. No placeholder values, no TODO/FIXME, no unfinished cohort routing.

## Threat Flags

None. The threat surface (LLM prompt text for medical marketing AI orchestrator) is fully covered by the plan's existing threat model:

- T-03-04-S (Spoofing — LLM fabricates top_by_followers entries): partially mitigated by Pass 2 self-evaluation cross-check (items 4/6/7 filled only if run_instagram_content was actually called, visible in tool-call history). Runtime hard-FAIL from Plan 03-06 catches missing calls. Full cross-check against actual tool-call history is future hardening (documented in plan threat register).
- T-03-04-T (Tampering — prompt rules overwritten): accept; single-writer per session, no concurrent modification risk.
- T-03-04-R (Repudiation — LLM doesn't log cohort decision): accept; tool calls persisted in SessionDB; Pass 2 prompt forces reason field per item.
- T-03-04-I (Info disclosure — doctor handles sent to LLM): accept; handles are public Instagram usernames, no PII beyond what Pass 1 already collected.
- T-03-04-D (DoS — larger batch 8-10 vs 5 increases Perplexity load): mitigated by D-11 explicitly approving 90-300s batch cost as acceptable; Perplexity has account-level rate limits; bounded by single presale run.
- T-03-04-E (EoP): N/A — no privilege change, pure prompt engineering.
- T-03-04-SC (Supply chain): accept — no new packages, pure prompt-text changes.

## User Setup Required

None — purely additive orchestrator prompt changes, opt-in via `ORCHESTRATOR_MODE=1` (default OFF). Production presale flow unaffected. No deployment required for this plan (changes are prompt-level; they take effect next time the orchestrator runs).

## Next Phase Readiness

- **Ready for Plan 03-05** (HTML rendering) — the two-cohort model (site-top + Instagram-active) introduced in this plan's prompts is the canonical framing Plan 03-05 needs to render sections 03 + 04. Section 03 shows both cohorts with distinct visual treatment (regalia badge for tituled, metrics badge for Instagram-active). Section 04 shows only Instagram-active cohort with metrics, themes, gaps. Plan 03-05 can read `top_by_followers` from `state.collected_data["pass_collect_result"]` (visible to LLM at Pass 3 assembly time).
- **D-09 SATISFIED** — find_doctor_handles designated as primary handle source (Plan 03-03 rule 1 + reinforced here through the cohort explanation in rule 5).
- **D-10 SATISFIED** — Adaptive top-5 selection rule encoded in Pass 1 prompt (rule 5) + Pass 2 cohort-aware items 4/6/7 evaluation rules. Site-top-5 primary, followers_count fallback when tituled experts lack Instagram.
- **D-11 SATISFIED** — Batch size 8-10 referenced in BOTH critical and non-critical branches of Pass 1 prompt. Single run_instagram_content call per presale.
- **IG-03 SATISFIED (with Plan 03-05 HTML rendering)** — For each top-5 doctor, the report contains followers, avg likes/views, content style, themes (in %), gaps, potential — sourced from run_instagram_content v2 response schema (verified in Plan 01-04 at 9.5/10 reference field coverage). This plan ensures the LLM picks the RIGHT top-5 (Instagram-active, not tituled-only) so section 04 has real data instead of empty placeholders.

## Self-Check: PASSED

- FOUND: `AIM/hermes/app/orchestrator/pass_collect.py` (with rule 5 "ADAPTIVE TOP-5 RULE" in critical branch + "ADAPTIVE TOP-5 NOTE" in non-critical branch + `top_by_followers` field reference + КМН/профессора + Content Analysis (04) + Experts (03) + module + helper docstrings updated)
- FOUND: `AIM/hermes/app/orchestrator/pass_gap_analyze.py` (with new block "АДАПТИВНЫЕ ПРАВИЛА ДЛЯ ПУНКТОВ 4 (Experts) И 6 (Content themes) И 7 (Content gaps)" + `top_by_followers` reference + items 4/6/7 cohort-aware rules + Plan 03-03 rules preserved)
- FOUND: commit `9dfc630` (Task 1: feat — Pass 1 prompt augmented with adaptive top-5 cohort selection rule D-10)
- FOUND: commit `44af99c` (Task 2: feat — Pass 2 prompt augmented with adaptive-cohort evaluation rules for items 4/6/7)
- FOUND: `.planning/phases/03-instagram-integration/03-04-SUMMARY.md` (this file)

---
*Phase: 03-instagram-integration*
*Completed: 2026-06-23*
