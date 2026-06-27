# Phase 26: Presale Pipeline — Skill Path Fix & Orchestration

**Gathered:** 2026-06-06
**Status:** Ready for planning
**Source:** Hermes final verdict — Yutskovskaya presale v1 post-mortem

<domain>
## Phase Boundary

**Проблема:** 7 standalone tools извлечены из SKILL.md (Phase 25), но Hermes не может загрузить их через `skill_view()` по коротким именам. Инструменты физически лежат в `/root/.hermes/skills/software-development/presale-pipeline/{name}/`, но в `skills_list` показываются без полного пути.

**Доказательство:** Hermes в финальном вердикте: «Если presale-pipeline говорит "загрузи social-verifier" — я не могу загрузить через `skill_view(name='social-verifier')`. Нужен полный путь: `skill_view(name='software-development/presale-pipeline/social-verifier')`».

**Корневые причины из post-mortem:**
1. Skills физически вложены в presale-pipeline/ — это создаёт проблему разрешения имён
2. Parent SKILL.md не содержит полных путей для LLM-first оркестрации
3. Hard Gate (0 gaps перед HTML) описан в теории, но не enforcement на практике
4. Нет structured log на каждый шаг — невозможно отладить сбой

**Цель:** Hermes должен вызывать 7 скиллов пресейла по имени без префикса, а parent SKILL.md — правильно оркестрировать их с Hard Gate и structured log.

**Граница:** Только фикс путей + parent orchestration SKILL.md. Сами инструменты (social-verifier, content-analyzer и др.) НЕ модифицируются.
</domain>

<decisions>
## Implementation Decisions

### D-01: Flatten skill paths — каждый tool как отдельный скилл верхнего уровня
Переместить каждый из 7 tools из `software-development/presale-pipeline/{name}/` → `software-development/{name}/`. Это устраняет проблему с путями — `skill_view(name='social-verifier')` будет работать.

Альтернатива (править все ссылки на полные пути): хуже, потому что LLM может сгенерировать любое имя. Flat structure — единственный надёжный вариант.

### D-02: Parent SKILL.md — LLM-first оркестрация
Заново написать `/root/.hermes/skills/software-development/presale-pipeline/SKILL.md` как тонкий orchestration layer (цель: < 200 строк):
- Ссылки на 7 tools по ИМЕНИ (не пути)
- Hard Gate: validate_gaps() перед HTML
- Model routing: Flash → сбор данных, Pro → анализ + HTML
- Structured log: каждый шаг пишет в `/root/work/presale/{client}/log.jsonl`
- Goal Loop: повторять сбор, пока gaps > 0

### D-03: Старый SKILL.md → reference
Текущий SKILL.md (92KB, 757 строк) переместить в `references/SKILL.md.v2.61.0-legacy`. Он остаётся как референс (CSS, дизайн-система, ключи, история ошибок), но не как активный скилл.

### D-04: Проверка — test-presale на Yutskovskaya
После фикса путей: запустить тестовый пресейл через Goal Loop. Критерий успеха: все 7 tools вызваны, 0 gaps перед HTML, HTML сгенерирован.
</decisions>

<canonical_refs>
## Canonical References

### На сервере (ssh root@138.16.224.188)
- `/root/.hermes/skills/software-development/presale-pipeline/SKILL.md` — v2.61.0 (92KB, 757 строк)
- `/root/.hermes/skills/software-development/presale-pipeline/social-verifier/SKILL.md` — 5-pass verifier
- `/root/.hermes/skills/software-development/presale-pipeline/content-analyzer/SKILL.md` — expert content cards
- `/root/.hermes/skills/software-development/presale-pipeline/competitor-scorer/SKILL.md` — competitor scoring
- `/root/.hermes/skills/software-development/presale-pipeline/financial-fetcher/SKILL.md` — 7 sources, 3 iterations
- `/root/.hermes/skills/software-development/presale-pipeline/html-kp-generator/SKILL.md` — 12 blocks
- `/root/.hermes/skills/software-development/presale-pipeline/tech-auditor/SKILL.md` — 8 parameters
- `/root/.hermes/skills/software-development/presale-pipeline/reel-scraper/SKILL.md` — Instagram Reels
- `/root/.hermes/skills/software-development/presale-pipeline/references/` — 25+ reference files
- `/root/.hermes/config.yaml` — display.busy_input_mode=queue (уже пофикшен)
</canonical_refs>

---
*Phase: 26-presale-orchestration-fix*
*Context gathered: 2026-06-06 via Hermes final verdict + server inspection*
