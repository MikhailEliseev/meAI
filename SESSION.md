# Session: 2026-06-06

## Текущий фокус: Phase 26 + 28 выполнены и задеплоены

### Что сделано

**Phase 28 (Deep Research Phase 0):**
- deep_research_merge.py + 30 unit-тестов
- deep-research-phase-0/SKILL.md (487 строк, 5 Steps, tier classification)
- presale-pipeline v3.6.0 (Phase 0 интегрирован)
- quality_gate.py + presale-state.template.json обновлены
- 5 коммитов, всё задеплоено на сервер

**Phase 26 (Key Unification) — все 4 шага уже были на сервере:**
- Symlink apify_keys.json → /opt/aim/AIM/data/
- Monkey-patch firecrawl_provider_bank в hermes_cli/main.py
- web.search_backend = firecrawl, disabled_toolsets = []
- healthcheck_keys.py + cron (каждые 6 часов)

**Phase 26 (Presale Orchestration Fix):**
- Task 1: Flatten — уже сделано (7 skills на верхнем уровне)
- Task 2: Parent SKILL.md rewrite — v3.0.0 (122 строки, LLM-first orchestration)
- Task 3: Archive legacy → references/SKILL.md.v3.6.0-legacy

### Следующие шаги
- Ждать активности @iamaim_bot — проверить что новый SKILL.md v3.0.0 работает
- Phase 27 (если есть в ROADMAP)
