# Phase 25: Presale Pipeline Tool Extraction — Context

**Gathered:** 2026-06-06
**Status:** Ready for planning
**Source:** Devil's Advocate Critique (36/36 FAIL, 843 строки) + LLM-First Orchestration vision

<domain>
## Phase Boundary

**Проблема:** SKILL.md v2.55.0 — монолит на 757 строк, 55 патчей без рефакторинга. Всё в одном файле: CSS ripple, бизнес-логика, ключи, дизайн, история ошибок. 36 из 36 критериев качества — FAIL. Это главный пример хардкод-оркестрации в системе.

**Цель:** Разобрать SKILL.md на отдельные инструменты (skills), которые Hermes вызывает по своему усмотрению. LLM решает, что и когда вызывать. SKILL.md остаётся как fallback.

**Граница:** Только пресейл-пайплайн (SKILL.md + references на сервере). Prescan API, Competitor Discovery, SEO-аудит НЕ трогаем — они работают.

**Бэкап:** `/root/.hermes/backups/2026-06-06_v2.55.0_snapshot/` (512 KB)
**Сервер:** ssh root@138.16.224.188
</domain>

<decisions>
## Implementation Decisions

### D-01: Инкрементальное извлечение
SKILL.md не переписывается. Инструменты извлекаются один за другим из монолита. Каждый новый tool работает параллельно с SKILL.md, пока не докажет, что даёт тот же или лучший результат. SKILL.md = fallback.

### D-02: Первый инструмент — Instagram Doctor Verifier
Самый сложный кусок (240+ API-вызовов, 5 проходов). Если его извлечь — паттерн масштабируется на остальные компоненты. На вход: список врачей. На выход: верифицированные соцсети с pass-маркерами.

### D-03: SKILL.md v2.55.0 НЕ ТРОГАЕМ
Он продолжает работать как fallback. Любая ошибка в новом tool → возврат к SKILL.md. Никакого риска потери результата.

### D-04: Структура tool
Каждый tool — отдельный skill-файл в `/root/.hermes/skills/software-development/presale-pipeline/` на сервере. Чёткий вход, чёткий выход, независимое тестирование, свой timeout/budget.

### D-05: 5-pass система сохраняется
Pass 1-5 логика переносится в tool без изменений. Оптимизация (stopping conditions, cost guards) — следующими итерациями после извлечения.

### D-06: Ключи и прокси наследуются
Apify/Firecrawl ключи остаются в `/root/.hermes/keys/`. Новый tool использует существующий механизм ротации.

### D-07: Метрика успеха
Instagram Verifier tool находит >= тех же врачей, что и полный SKILL.md на эталоне ampermy.

### D-08: LLM-First оркестрация
После извлечения инструментов Hermes получает их как отдельные tools и сам решает, какие вызывать и в каком порядке. Никакого P5-FIX, никаких хардкод-последовательностей.
</decisions>

<canonical_refs>
## Canonical References

### На сервере (ssh root@138.16.224.188)
- `/root/.hermes/skills/software-development/presale-pipeline/SKILL.md` — v2.55.0 (757 строк)
- `/root/.hermes/skills/software-development/presale-pipeline/presale-pipeline-devils-advocate-critique.md` — 36/36 FAIL
- `/root/.hermes/skills/software-development/presale-pipeline/references/` — справочники
- `/root/work/presale-ampermy.html` — эталонный HTML
- `/root/.knowledge/competitors/moscow/wellness/ampermy-competitors.md` — эталонные конкуренты
- `/root/.hermes/backups/2026-06-06_v2.55.0_snapshot/` — полный бэкап

### В репозитории
- `CLAUDE.md` — LLM-First Tool Orchestration, секция "Что НЕ использовать"
- `/opt/data/AIM_HANDBOOK.md` — инструменты Hermes (на сервере)
</canonical_refs>

<specifics>
## Specific Ideas

### Приоритет извлечения

| # | Tool | Сложность | Что делает |
|---|------|-----------|------------|
| 1 | Instagram Doctor Verifier | Высокая | 5-pass поиск соцсетей врачей |
| 2 | HTML-KP Generator | Средняя | Генерация 12-блочного HTML |
| 3 | Competitor Scorer | Средняя | Скоринг и сравнение конкурентов |
| 4 | Financial Fetcher | Низкая | ГИР БО + nalog.ru |

### Критические проблемы (из critique)
1. Монолит 757 строк — CSS + бизнес-логика + ключи
2. Данные размазаны по 7+ слоям
3. 5-pass без stopping conditions
4. Правило «Не останавливаться» → cost explosion
5. Context bloat к HTML-фазе (60-80K токенов)
6. Cross-contamination между сессиями
</specifics>

<deferred>
## Deferred Ideas

- Полный рефакторинг 12 Apify ключей (отдельная фаза)
- Context budget guard + checkpoint-система
- Pass 5 удаление или on-demand
- Cost guard для правила «Не останавливаться»
- Остальные инструменты (HTML-KP, Competitor Scorer, Financial Fetcher) — после Instagram Verifier
</deferred>

---

*Phase: 25-llm-first-orchestration*
*Context gathered: 2026-06-06 via Devil's Advocate Critique*
