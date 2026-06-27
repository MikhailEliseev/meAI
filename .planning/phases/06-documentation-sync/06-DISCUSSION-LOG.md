# Phase 6: Documentation Sync - Discussion Log

**Date:** 2026-06-24
**Phase:** 6-Documentation Sync
**Mode:** --auto (user sleeping)

---

## Auto-mode Decisions

[auto] [Source of truth] — Q: "Code or docs?" → Selected: "Code is truth, docs mirror" (recommended)

[auto] [SOUL.md strategy] — Q: "How to update?" → Selected: "Full rewrite based on actual code" (recommended)

[auto] [SKILL.md aim-scout] — Q: "Describe orchestrator or pipeline?" → Selected: "3-pass orchestrator with QC checklist, remove FULL AUTO pipeline" (recommended)

[auto] [phases.py] — Q: "Cleanup strategy?" → Selected: "Keep as LEGACY if used, mark deprecated" (recommended)

[auto] [engine.py _TOOL_HANDLERS] — Q: "Sync strategy?" → Selected: "Add assertion test for >=26 entries" (recommended)

[auto] [Phantom phases] — Q: "Remove 0.5/0.75/0.8/3.2?" → Selected: "Full grep + remove everywhere" (recommended)

[auto] [Implementation split] — Q: "How many plans?" → Selected: "3 plans: SOUL.md / SKILL.md+phases.py / engine.py+deploy" (recommended)

## Claude's Discretion

- Точная структура разделов SOUL.md
- Стиль языка
- Сколько деталей включить
- Метод обновления серверной SOUL.md
- Раздельные ARCHITECTURE.md / TOOLS.md / QC.md или всё в SOUL.md

## Deferred Ideas

- SOUL.md как structured JSON/YAML — backlog
- Авто-генерация из кода — backlog
- ADR — backlog
- Двуязычная документация — backlog
