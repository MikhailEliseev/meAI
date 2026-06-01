---
plan: 22-01
phase: 22-hermes-first-communication-flow
status: complete
tasks_completed: 3/3
tests_passing: 8/8
commits: 3
---
# Plan 22-01: Hermes PRESALE Conversation Flow Redesign

## What was built

Redesigned Hermes PRESALE mode from a "parallel-first fire-everything" approach into a natural 8-step conversational dialogue. Hermes now leads the client through: URL request → quick audit → competitor gathering → relevance evaluation → confirmation → full CI analysis → friendly report + detailed breakdown → contact collection.

### Changes

1. **SOUL.md PRESALE section (122 lines added, 41 removed)**
   - Replaced old parallel-first instruction with 8-step conversational flow
   - Each step has example phrases and behaviour guidance
   - Report structure: friendly summary FIRST (conversational, no tables), detailed breakdown SECOND
   - Tone: "как будто друг рассказал" — conversational, not robotic
   - Multi-entity awareness mentioned in Step 2
   - New "Что нельзя" aligns with new flow (no parallel launch, no report without friendly intro)

2. **_presale_prompt() in agent_wrapper.py (22 lines added, 12 removed)**
   - Removed "Сразу к делу" / "ВСЕГДА параллельно" instructions
   - Added step-by-step dialogue guidance referencing SOUL.md's 8 steps
   - Added conversational tone instruction
   - Added report format: friendly-first, detailed-second
   - Retained core principles: Цифры из инструментов, Бизнес-язык, Контакт в конце
   - Updated tool ordering: run_seo_audit first, find_competitors second

3. **test_presale_flow.py (168 lines, new file)**
   - 8 tests validating cross-file consistency
   - Coverage: step count, parallel-first removal, conversational tone, report structure, core principles
   - Handles agent_wrapper.py import via source parsing (hermes_state is Docker-only)

### Files modified

| File | Lines | Type |
|------|-------|------|
| AIM/hermes/skills/aim/SOUL.md | +122/-41 | Modified |
| AIM/hermes/app/agent_wrapper.py | +22/-12 | Modified |
| AIM/hermes/tests/test_presale_flow.py | +168 | New |

### Key design decisions

- SOUL.md carries the full conversational flow; _presale_prompt() adds execution context
- Report format: Part 1 (friendly, no markdown) MUST come before Part 2 (detailed, with tables)
- The word "одновременно" appears in negative context ("НЕ запускаю одновременно") — tests verify old POSITIVE patterns are gone
- Tests parse agent_wrapper.py source rather than importing (avoids Docker-only hermes_state dependency)

### Self-Check: PASSED
