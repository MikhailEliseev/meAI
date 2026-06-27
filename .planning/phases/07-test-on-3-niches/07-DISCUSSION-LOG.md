# Phase 7: Test on 3 Niches - Discussion Log

**Date:** 2026-06-24
**Phase:** 7-Test on 3 Niches
**Mode:** --auto (user sleeping)

---

## Auto-mode Decisions

[auto] [Test niches] — Q: "Which 3 niches?" → Selected: "Plastic (iphk.ru, has reference) + Dental + Cosmetology" (recommended per ROADMAP)

[auto] [Execution strategy] — Q: "How to execute?" → Selected: "3 parallel plans, one per niche, each triggers + waits + scores" (recommended)

[auto] [PRESALE vs ADMIN] — Q: "Test modes?" → Selected: "Both — PRESALE via Telegram bot, ADMIN via curl" (recommended per TST-03, TST-04)

[auto] [QC scoring] — Q: "How to score?" → Selected: "QC checklist % + 5-criteria style comparison with reference" (recommended)

[auto] [Output format] — Q: "Where to save?" → Selected: "/opt/data/memories/proposals/[client-slug]/proposal.html + feedback.md" (recommended)

[auto] [Failure handling] — Q: "If test fails?" → Selected: "Record as KNOWN ISSUE, continue, aggregate report for Phase 8 go/no-go" (recommended)

[auto] [Implementation split] — Q: "How many plans?" → Selected: "3-4 plans (one per niche + optional aggregate)" (recommended)

## Claude's Discretion

- Точный способ триггера
- Выбор клиник для dental/cosmetology
- Длительность wait per test
- Format feedback.md
- LLM-as-judge vs manual scoring

## Deferred Ideas

- A/B-тесты отчётов — backlog
- UAT с реальными клиентами — backlog
- Multi-language tests — backlog
- Load testing — backlog
