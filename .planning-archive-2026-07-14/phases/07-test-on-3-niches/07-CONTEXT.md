# Phase 7: Test on 3 Niches - Context

**Gathered:** 2026-06-24 (--auto mode — user sleeping)
**Status:** Ready for planning

<domain>
## Phase Boundary

Валидация системы на 3 реальных пресейлах в разных нишах: пластическая хирургия (iphk.ru — есть референс `ИПХиК (2).html`), стоматология, косметология. Каждый тест должен производить полный HTML-отчёт с ≥80% покрытия QC-чек-листа реальными данными.

**Внутри scope:**
- 3 end-to-end пресейла через orchestrator (ORCHESTRATOR_MODE=1)
- Каждый прогон: trigger → wait → collect HTML report → score against QC checklist
- PRESALE mode test (через Telegram-бота как реальный клиент)
- ADMIN mode test (manual trigger для конкретной клиники)
- Фиксация результатов: proposal.html + feedback.md в `/opt/data/memories/proposals/[client-slug]/`
- Сравнение с референс `ИПХиК (2).html` (style + depth + coverage)

**Вне scope:**
- Новые фичи (Phase 3-6 closed)
- Правки найденных багов в runtime (это Phase 8 или patch)
- Изменение архитектуры
- Деплой (Phase 8)

</domain>

<decisions>
## Implementation Decisions

### Test Niches

- **D-01:** 3 ниши:
  1. **Пластическая хирургия** — `iphk.ru` (есть референс `ИПХиК (2).html` для сравнения)
  2. **Стоматология** — клиника на выбор админа (из действующих клиентов или новых лидов)
  3. **Косметология** — клиника на выбор (instagram-critical ниша, проверяет Phase 3 Instagram integration)
- **D-02:** Если нет конкретной клиники для стоматология/косметология — использовать demo URLs из `/opt/data/memories/proposals/` (исторические) или найти новую через Perplexity search «стоматология москва топ-5»

### Test Execution Strategy

- **D-03:** 3 плана параллельно (один на каждую нишу) — каждый вызывает `ORCHESTRATOR_MODE=1` + trigger через `/api/chat/stream` endpoint или CLI.
- **D-04:** Каждый план:
  1. Trigger presale (`curl POST /api/chat` с клиникой URL)
  2. Wait 15-20 min для завершения 3-pass cycle
  3. Find latest HTML report in `/opt/data/memories/proposals/`
  4. Score report against 18-item QC checklist
  5. Compare sections to reference `ИПХиК (2).html`
  6. Write `feedback.md` с оценками и предложениями
- **D-05:** Если presale не завершился за 30 min — таймаут, отметить как FAILED, продолжить с другой нишей.

### PRESALE vs ADMIN Mode Tests (TST-03, TST-04)

- **D-06:** PRESALE mode test = триггер через Telegram-бота (как клиент пишет «Сделай пресейл для X»). Telegram gateway → Hermes → orchestrator.
- **D-07:** ADMIN mode test = триггер через ADMIN chat (Михаил вручную) или curl с `X-Client-Mode: ADMIN` header.

### QC Scoring

- **D-08:** Каждый тест оценивается по QC checklist: % filled (target ≥80%), % not_applicable (для non-critical niche Instagram items), % missing.
- **D-09:** Сравнение стиля с референсом: subjectively scored (LLM-as-judge или admin manual) по 5 критериям:
  1. Narrative vs metric dump
  2. Business language
  3. Gap-blocks present
  4. Blockquote per section
  5. Cross-references between sections

### Output Format

- **D-10:** Для каждого теста: `proposal.html` + `feedback.md` в `/opt/data/memories/proposals/[client-slug]/`. `feedback.md` содержит:
  - QC checklist score
  - Style comparison
  - Missing sections
  - Identified bugs
  - Recommendations for Phase 8 fixes

### Failure Handling

- **D-11:** Если тест выявил критический баг — зафиксировать в `feedback.md`, отметить как KNOWN ISSUE, продолжить с другими нишами. Phase 8 может включать patch plan.
- **D-12:** Если все 3 теста провалились — это BLOCKER для Phase 8 deploy. Остановить и потребовать ручного вмешательства.

### Implementation Split

- **D-13:** 3-4 плана:
  - **07-01:** Тест на пластической хирургии (iphk.ru) с сравнением с референсом
  - **07-02:** Тест на стоматологии
  - **07-03:** Тест на косметологии
  - **07-04:** (optional) Агрегированный отчёт + go/no-go для Phase 8

### Claude's Discretion

- Точный способ триггера пресейла (curl vs ssh docker exec vs Telegram test)
- Выбор конкретных клиник для стоматологии/косметологии
- Длительность wait per test (15-30 min)
- Format feedback.md
- LLM-as-judge vs manual scoring

### Folded Todos

(нет — --auto mode)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Reference HTML Report (STYLE CANON)
- `/Users/mikhaileliseev/Downloads/ИПХиК (2).html` — 78KB, 965 lines, 10 sections. Использовать как canon для style comparison.

### Prior Phase Summaries
- `.planning/phases/03-instagram-integration/03-VERIFICATION.md` — Phase 3 integration
- `.planning/phases/04-new-sections-data-depth/04-VERIFICATION.md` — Phase 4 integration
- `.planning/phases/05-deep-interpretation/05-VERIFICATION.md` — Phase 5 narrative quality

### Deployed System State
- `aim-hermes` container — Phase 3-6 deployed
- `_TOOL_HANDLERS` = 26 entries
- `QC_CHECKLIST` = 18 items v1.2.0
- `ORCHESTRATOR_MODE` = unset (OPT-IN preserved — tests will set it to 1)

### Project-Level
- `.planning/PROJECT.md` — Core value, constraints
- `.planning/REQUIREMENTS.md` §Test (TST-01..05) — Phase 7 requirements
- `CLAUDE.md` — constraints, deploy pattern, SSH convention

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `aim-hermes` container — running, healthy, all Phase 3-6 changes deployed
- `/api/chat/stream` endpoint — SSE streaming presale trigger
- Telegram bot — PRESALE mode entry point
- `/opt/data/memories/proposals/` — output directory for HTML reports
- `QC_CHECKLIST` (18 items) — scoring rubric
- `generate_html_report.py` — HTML renderer with all 10 sections

### Established Patterns
- **Honest reporting:** «данные недоступны» — если пресейл не нашёл данные, это отмечается в отчёте
- **Orchestrator opt-in:** ORCHESTRATOR_MODE=1 для new orchestrator path, unset для PipelineEngine fallback

### Integration Points
- `aim-hermes:/api/chat/stream` — presale trigger
- `/opt/data/memories/proposals/[client-slug]/proposal.html` — output
- `ssh aim "docker exec -e ORCHESTRATOR_MODE=1 aim-hermes ..."` — env injection

</code_context>

<specifics>
## Specific Ideas

- 3 ниши: пластическая хирургия (iphk.ru, есть референс), стоматология, косметология
- Каждый тест: ≥80% QC coverage target
- PRESALE mode (Telegram) + ADMIN mode (curl) tests
- Output: proposal.html + feedback.md per ниша
- Сравнение с референсом по 5 style criteria

</specifics>

<deferred>
## Deferred Ideas

- A/B-тесты отчётов — backlog
- User acceptance testing с реальными клиентами — backlog
- Multi-language tests (English) — backlog
- Load testing (10 параллельных пресейлов) — backlog

</deferred>

---

*Phase: 7-Test on 3 Niches*
*Context gathered: 2026-06-24 (--auto mode)*
