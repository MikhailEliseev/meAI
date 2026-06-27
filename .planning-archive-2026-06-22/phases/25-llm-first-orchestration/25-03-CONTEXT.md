# Phase 25-03: Gap Closure to Ampermy Etalon — Context

**Gathered:** 2026-06-06
**Status:** Ready for planning
**Source:** User gap analysis vs ampermy etalon (presale-ampermy.html)

<domain>
## Phase Boundary

**Проблема:** 4 инструмента извлечены из SKILL.md, но качество пресейла не дотягивает до эталона ampermy. Конкретные gaps:

1. **Нет технического аудита сайта** — 8 параметров (скорость, битые ссылки, мета-теги, h1, alt, карта сайта). Для Ampermy с 1C-Bitrix и проблемами индексации — х2 аргумент.
2. **Контент-анализ только TOP-2 экспертов** — Алифер, Анаит ок. Остальные 8 не проанализированы: форматы-победители, вовлечение, виральные посты с цифрами.
3. **Нет виральных тем конкурентов** — Wellcure, Некрасова. Что у них виральное? Как адаптировать под Ampermy?
4. **Instagram глубже не копнули** — Reel Scraper не запускали. Для Алифер (135K аудитории) нужен анализ форматов. **БЕЗ визуального анализа** (ffmpeg/AssemblyAI). Только ссылки на reels с target=_blank.

**Цель:** Закрыть 4 gaps, чтобы качество пресейла соответствовало эталону ampermy.

**Граница:** Только пресейл-инструменты. Визуальный анализ Reels — на постконтрактной фазе.
</domain>

<decisions>
## Implementation Decisions

### D-01: Технический аудит — отдельный tool
Новый skill `tech-auditor`: 8 параметров сайта. На вход: URL. На выход: таблица с результатами + приоритеты фиксов. Lighthouse/PageSpeed для скорости, crawl для битых ссылок, парсинг meta/h1/alt/sitemap.

### D-02: Контент-анализ ВСЕХ 10 экспертов
Расширить social-verifier или создать `content-analyzer` tool. Для каждого из 10 экспертов: форматы-победители, вовлечение (лайки/комменты), виральные посты с цифрами. Не только TOP-2.

### D-03: Виральные темы конкурентов
Добавить в competitor-scorer или создать отдельный шаг: поиск виральных постов конкурентов (Wellcure, Некрасова и др.), анализ тем, адаптация под клиента.

### D-04: Reel Scraper без визуального анализа
Для Instagram-экспертов (особенно Алифер, 135K): собрать Reels через Apify Instagram Reel Scraper, дать ссылки с target=_blank. **Без** ffmpeg кадров и AssemblyAI транскрипции. Визуальный анализ — постконтракт.

### D-05: Инструменты как Hermes skills
Все новые инструменты — отдельные SKILL.md в `/root/.hermes/skills/software-development/presale-pipeline/`. Чёткий вход, выход, fallback на SKILL.md.

### D-06: Эталон качества
Результат на ampermy должен соответствовать `/root/work/presale-ampermy.html` (23KB, сгенерирован 5 июня).
</decisions>

<canonical_refs>
## Canonical References

### На сервере (ssh root@138.16.224.188)
- `/root/.hermes/skills/software-development/presale-pipeline/SKILL.md` — v2.57.0 (607 строк, fallback)
- `/root/.hermes/skills/software-development/presale-pipeline/social-verifier/SKILL.md` — 5-pass Instagram verifier
- `/root/.hermes/skills/software-development/presale-pipeline/html-kp-generator/SKILL.md` — 12-block HTML-КП
- `/root/.hermes/skills/software-development/presale-pipeline/financial-fetcher/SKILL.md` — financial data
- `/root/.hermes/skills/software-development/presale-pipeline/competitor-scorer/SKILL.md` — competitor scoring
- `/root/work/presale-ampermy.html` — эталонный HTML (23KB)
- `/root/.knowledge/competitors/moscow/wellness/ampermy-competitors.md` — конкуренты ampermy
- `/root/.hermes/backups/2026-06-06_v2.55.0_snapshot/` — бэкап v2.55.0

### В репозитории
- `CLAUDE.md` — LLM-First Tool Orchestration
</canonical_refs>

<specifics>
## Specific Ideas

### Gaps → Tools mapping

| # | Gap | Tool | Приоритет |
|---|-----|------|-----------|
| 1 | Технический аудит | `tech-auditor` | HIGH |
| 2 | Контент-анализ 10 экспертов | `content-analyzer` (или расширение social-verifier) | HIGH |
| 3 | Виральные темы конкурентов | расширение `competitor-scorer` | MEDIUM |
| 4 | Instagram Reels (ссылки) | `reel-scraper` (без визуала) | MEDIUM |

### Что НЕ делаем
- ffmpeg кадры Reels
- AssemblyAI транскрипция
- Визуальный анализ форматов (talking head / монтаж / слайд-шоу)
- Всё это → постконтрактная фаза
</specifics>

<deferred>
## Deferred Ideas

- Визуальный анализ Reels (ffmpeg + AssemblyAI) — постконтракт
- Cost guard для всех инструментов
- Context budget guard
- Pass 5 removal из social-verifier
</deferred>

---

*Phase: 25-03-gap-closure-ampermy-etalon*
*Context gathered: 2026-06-06 via user gap analysis*
