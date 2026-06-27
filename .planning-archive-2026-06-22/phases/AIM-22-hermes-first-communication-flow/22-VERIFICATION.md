---
phase: 22-hermes-first-communication-flow
verified: 2026-06-01T12:00:00Z
status: human_needed
score: 7/7 truths verified
overrides_applied: 0
re_verification: false
human_verification:
  - test: "End-to-end PRESALE conversation with Hermes — give him a real website URL and verify he follows the 8-step flow conversationally (asks for URL first, does NOT fire all tools at once, reports quick audit before asking for competitors, evaluates relevance, delivers friendly summary before detailed breakdown)"
    expected: "Hermes leads a natural 8-step dialogue: requests URL → runs quick audit and reports findings conversationally → asks for 2-3 competitors or offers to find them → evaluates competitor relevance with verdicts → confirms selection → runs full CI analysis → delivers friendly conversational summary FIRST followed by detailed breakdown with tables → collects contact"
    why_human: "Conversational tone, step ordering, report format quality, and cross-file prompt alignment can only be verified through actual interaction with the deployed Hermes system. Code-level checks confirm the prompt structure is correct, but behavioral execution depends on the LLM interpreting the prompts as intended."
  - test: "Verify Hermes does NOT revert to 'launch all tools in parallel' behavior when given a URL in the first message"
    expected: "Hermes still responds conversationally (e.g., 'Ага, смотрю ваш сайт...') rather than dumping parallel tool output immediately"
    why_human: "LLM prompt adherence to 'НЕ запускаю одновременно' instruction can only be validated through real interaction."
---

# Phase 22: Hermes PRESALE Conversation Flow Redesign — Verification Report

**Phase Goal:** Redesign the PRESALE conversation flow in Hermes to be a live, step-by-step dialogue — not a rigid protocolized report.

**Verified:** 2026-06-01T12:00:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Hermes asks for website URL as first conversational step (does NOT launch tools immediately) | VERIFIED | SOUL.md Шаг 1 (lines 50-56): "Моё первое сообщение — попросить URL. Больше ничего не делаю." / "Не запускаю инструменты без URL." Example: "Скиньте ссылку на ваш сайт — я быстро посмотрю что у вас и как." agent_wrapper.py line 135 references "Шаг 1 — запрос URL" |
| 2 | Hermes analyzes website and reports key directions, doctors, and revenue in conversational tone | VERIFIED | SOUL.md Шаг 2 (lines 60-73): calls run_seo_audit, extracts specialization/city/services/patients/revenue. Reports: "Ага, смотрю. Вы стоматология в Казани. Ключевые направления: имплантация, протезирование, лечение зубов... Оборот примерно 2-3 млн ₽." Doctor data flows through CI analysis (Шаг 6-7): "какие врачи работают" / "такие врачи ключевые" |
| 3 | Hermes asks for 2-3 named competitors OR offers to find them via find_competitors | VERIFIED | SOUL.md Шаг 3 (lines 79-86): "Кого вы считаете своими прямыми конкурентами? Назовите 2-3 клиники. Если не уверены — я сам поищу кто есть рядом с вами." Explicit branching: named → Шаг 4 with named_competitors; not sure → Шаг 4 with autopoisearch |
| 4 | Hermes evaluates each competitor by revenue, size, location and gives relevance verdict | VERIFIED | SOUL.md Шаг 4 (lines 89-101): Calls find_competitors, extracts brand_name, revenue_year, profit_year, location_score, total_score. Example verdicts: "Дентал Профи — это ваш прямой конкурент... выручка ~5 млн ₽... Очень релевантно" / "частично релевантно" / "не совсем релевантно" |
| 5 | Hermes runs full CI analysis on confirmed competitors covering reviews, doctors, directions, money, SEO, ads, social | VERIFIED | SOUL.md Шаг 6 (lines 113-119): Calls run_ci_analysis(url, specialization, city, services, competitors, client_revenue, client_rating). Explains: "что пациенты пишут в отзывах, какие врачи работают, ключевые направления, финансовые показатели (из налоговой), SEO, рекламу, соцсети" |
| 6 | Final report has friendly conversational summary FIRST, detailed breakdown SECOND | VERIFIED | SOUL.md Шаг 7 (lines 123-152): "КРИТИЧЕСКИ: Две части, именно в таком порядке." / "ЧАСТЬ 1 — Дружеские выводы (СНАЧАЛА)" / "ЧАСТЬ 2 — Детальный разбор (ПОТОМ)". agent_wrapper.py (lines 146-151): "всегда ДВЕ части, именно в таком порядке. Сначала — свободный разговорный вывод... Потом — структурированный детальный разбор" |
| 7 | Tone throughout is natural and conversational — как будто друг рассказал, specialist talking, not machine | VERIFIED | SOUL.md line 39: "Тон: как будто друг рассказал" / line 39: "ЖИВОЙ ДИАЛОГ, НЕ ПРОТОКОЛ" / line 176: approved phrases: "ага", "смотрите", "вот это интересно", "знаете что я заметил". agent_wrapper.py line 138: "Разговорный, как будто друг рассказывает. Используй фразы вроде смотрите, ага, у вас" |

**Score:** 7/7 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `AIM/hermes/skills/aim/SOUL.md` | PRESALE section: 8 steps, conversational tone, Шаг 1-8 markers | VERIFIED | 147 lines (PRESALE section, lines 35-180). All 8 steps present with markers. All 5 key tools referenced. "Что нельзя" and "Что можно и нужно" guidance included. |
| `AIM/hermes/app/agent_wrapper.py` | `_presale_prompt()`: no parallel-first, step-by-step guidance, friendly-first report | VERIFIED | 42-line return string (lines 127-168). 8-step dialogue reference, conversational tone instruction, friendly-first report format. All core principles retained ("Цифры из инструментов", "Бизнес-язык", "Контакт — в конце"). |
| `AIM/hermes/tests/test_presale_flow.py` | 8 tests passing, validates flow consistency across both files | VERIFIED | 8/8 tests passing (0.01s). Tests cover: step count, parallel-first removal, conversational phrases, report structure, core principles, cross-file consistency. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| SOUL.md PRESALE section | agent_wrapper.py `_presale_prompt()` | Mode prompt at agent creation | WIRED | build_system_prompt() (line 81-91) combines SOUL.md + mode prompt. get_mode_prompt("PRESALE") (line 112) calls _presale_prompt(). _create_agent() (line 255) passes ephemeral_system_prompt=get_mode_prompt(mode). _presale_prompt() (line 135) references "SOUL.md описывает 8 шагов диалога" |
| PRESALE flow (SOUL.md) | find_competitors tool | Step 4 of conversation flow | WIRED | SOUL.md Шаг 4 (line 91): "Вызываю find_competitors(url, named_competitors=[...])". Шаг 3 (line 84): branch to named_competitors or autopoisearch. agent_wrapper.py (line 156): "find_competitors — поиск и оценка конкурентов (Шаг 4)" |
| PRESALE flow (SOUL.md) | run_ci_analysis tool | Step 6 of conversation flow | WIRED | SOUL.md Шаг 6 (line 115): "запускаю run_ci_analysis(url, specialization, city, services, competitors, client_revenue, client_rating)". agent_wrapper.py (line 158): "run_ci_analysis — глубокий анализ конкурентов (Шаг 6)" |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| All 8 validation tests pass | `python -m pytest AIM/hermes/tests/test_presale_flow.py -v` | 8 passed in 0.01s | PASS |
| Old parallel-first absent (SOUL.md) | `grep -c "запускаю ВСЕ нужные инструменты ОДНОВРЕМЕННО" SOUL.md` | 0 matches | PASS |
| Old parallel-first absent (agent_wrapper.py) | `grep -c "ОДНОВРЕМЕННО\|ВСЕГДА параллельно" agent_wrapper.py` | 0 matches | PASS |
| "одновременно" only in negative context | SOUL.md negative form | "❌ Не запускаю все инструменты одновременно на первом же сообщении — это убивает диалог" | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| 22-FLOW-01 | 22-01-PLAN.md | Step-by-step conversational flow (Шаг 1-8) | SATISFIED | SOUL.md PRESALE section contains all 8 steps with markers; agent_wrapper.py references all 8 steps |
| 22-FLOW-02 | 22-01-PLAN.md | Conversational tone — как будто друг рассказал | SATISFIED | SOUL.md lines 39, 176; agent_wrapper.py lines 135, 138 |
| 22-FLOW-03 | 22-01-PLAN.md | Multi-entity financials awareness | SATISFIED | SOUL.md Шаг 2 (line 75): "если 2+ юрлица, объяснить что финансы агрегированы" |
| 22-FLOW-04 | 22-01-PLAN.md | Report: friendly summary BEFORE detailed breakdown | SATISFIED | SOUL.md Шаг 7 (lines 125-152); agent_wrapper.py (lines 146-151) |
| 22-FLOW-05 | 22-01-PLAN.md | Old parallel-first pattern removed from both files | SATISFIED | Confirmed absent from both SOUL.md and agent_wrapper.py |
| 22-FLOW-06 | 22-01-PLAN.md | _presale_prompt() synced with new SOUL.md flow | SATISFIED | agent_wrapper.py references all 8 steps; test_mode_prompt_and_soul_consistent PASSED |
| 22-FLOW-07 | 22-01-PLAN.md | Tests validate cross-file flow consistency | SATISFIED | 8/8 tests pass, including cross-file consistency test |

**Note:** Requirements 22-FLOW-01 through 22-FLOW-07 are declared in PLAN.md frontmatter but do not appear in `.planning/REQUIREMENTS.md`. These are phase-local requirements scoped to this execution only.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | (none) | (none) | (none) | No debt markers (TBD/FIXME/XXX/TODO), stubs, or empty implementations in any modified file |

**SOUL.md PRESALE section line count:** 147 lines (specified range: 150-300). Slightly under the minimum by 3 lines. Content is comprehensive — all 8 steps with detailed examples, tool references, multi-entity coverage, "Что нельзя" and "Что можно и нужно" guidance. This minor deviation does not affect goal achievement.

### Human Verification Required

#### 1. End-to-End PRESALE Conversation Flow

**Test:** Start a PRESALE conversation with Hermes on iamaim.ru with a real clinic website URL. Observe the full conversation flow.

**Expected:** Hermes leads a natural 8-step dialogue:
1. Asks for URL (does NOT fire tools immediately)
2. Runs quick audit (run_seo_audit), reports findings conversationally
3. Asks for 2-3 competitors or offers to find them
4. Evaluates each competitor with relevance verdicts
5. Confirms selection before proceeding
6. Runs full CI analysis, explains what he will look at
7. Delivers friendly conversational summary FIRST (no tables, no markdown headers), THEN detailed breakdown with tables
8. Collects contact

**Why human:** Conversational tone, step ordering, report format quality, and cross-file prompt alignment can only be verified through actual interaction with the deployed Hermes system. Code-level checks confirm the prompt structure is correct, but behavioral execution depends on the LLM interpreting the prompts as intended.

#### 2. Parallel-First Regression Check

**Test:** Give Hermes a URL in the very first message (skip the "ask for URL" step). Observe whether he still follows the conversational flow or reverts to launching tools in parallel.

**Expected:** Hermes still responds conversationally (e.g., "Ага, смотрю ваш сайт...") rather than dumping parallel tool output immediately. He should acknowledge the URL and proceed to step 2 naturally, not jump to running all tools at once.

**Why human:** LLM prompt adherence to "НЕ запускаю одновременно" instruction can only be validated through real interaction. The SOUL.md prompt explicitly says "❌ Не запускаю все инструменты одновременно на первом же сообщении" but LLMs can sometimes ignore negative instructions.

## Gaps Summary

No blocking gaps found. All 7 truths verified, all artifacts substantive and wired, all 8 tests passing at 8/8, all old parallel-first patterns removed, no anti-patterns detected.

**Minor deviation noted:** SOUL.md PRESALE section is 147 lines (spec requested 150-300). This is 3 lines under the minimum. Content coverage is comprehensive and the deviation is cosmetic — it does not impact goal achievement.

**Status: human_needed** — Two human verification items are required to confirm behavioral quality of the conversational flow, as code-level verification cannot assess LLM-driven dialogue quality, tone naturalness, or step-ordering adherence at runtime.

---

_Verified: 2026-06-01T12:00:00Z_
_Verifier: Claude (gsd-verifier)_
