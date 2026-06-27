# Phase 27: Presale Conveyor — JSON Contract + State Machine + Quality Gate

**Gathered:** 2026-06-06
**Status:** Ready for planning
**Source:** User gap analysis — 3 holes that hurt at scale

<domain>
## Phase Boundary

**Проблема:** 7 tools работают, но говорят на разных языках. HTML-генератор сшивает разрозненные markdown-таблицы вручную. State теряется при компактизации. Hard Gate — человеческий, не программный.

**Три дыры:**
1. **Нет формата данных между скиллами** — каждый скилл выдаёт свой формат (markdown, таблицы, карточки). HTML-генератор сшивает вручную → context bloat, ошибки.
2. **Нет state machine** — прогресс хранится в «голове» модели + текстовом current-context.json. При компакте/перезагрузке теряется.
3. **Нет автоматического quality gate** — «0 не проверено» проверяется глазами. На 24 врачах + 5 конкурентах человеческий фактор.

**Цель:** Превратить набор скиллов в конвейер: единый JSON-формат данных, structured state machine, программный quality gate.

**Граница:** 
- Схема PresaleData + адаптация html-kp-generator под чтение JSON
- State machine spec + запись/чтение presale-state.json
- quality-gate.py как валидатор
- Сами 6 скиллов НЕ переписываем — адаптеры сделаем позже
</domain>

<decisions>
## Implementation Decisions

### D-01: PresaleData JSON schema
Единая схема в `/root/work/presale/{client}/data.json`. Каждый скилл пишет в свою секцию:
- `data.clinic` — tech-auditor + financial-fetcher
- `data.doctors[]` — social-verifier (per doctor: name, ig_username, followers, verified)
- `data.competitors[]` — competitor-scorer (per competitor: name, revenue, strengths)
- `data.content` — content-analyzer (per-expert cards, winning formats)
- `data.reels` — reel-scraper (per doctor: reel_urls[])
- `data.geo` — GEO audit results

html-kp-generator читает готовый `data.json` и не думает про сбор.

### D-02: Presale state machine
Файл `/root/work/presale/{client}/presale-state.json`:
```json
{
  "client": "yutskovskaya",
  "url": "https://yutskovskaya.ru",
  "phase": 2,
  "step": "social-audit",
  "completed": ["phase1-site", "phase1-finance"],
  "pending": ["phase2-pass2", "phase2-pass3"],
  "errors": [],
  "started_at": "2026-06-06T08:00:00Z",
  "updated_at": "2026-06-06T08:15:00Z"
}
```
Обновляется атомарно после каждого шага. Читается при старте сессии.

### D-03: quality-gate.py
Скрипт `/root/bin/quality-gate.py` — валидатор:
- Читает `data.json` + `presale-state.json`
- Проверяет: каждый врач → social audit, каждый конкурент → финансы, GEO → у всех
- 0 gaps → PASS, иначе FAIL + список незакрытого
- Возвращает exit code 1 при FAIL — блокирует HTML

### D-04: html-kp-generator адаптация
Обновить SKILL.md: читать `data.json` вместо markdown-таблиц. Принимать JSON на вход.
</decisions>

<canonical_refs>
### На сервере
- `/root/work/presale/` — рабочая директория пресейлов
- `/root/.hermes/skills/software-development/html-kp-generator/SKILL.md` — v1.1.0
- `/root/.hermes/skills/software-development/presale-pipeline/SKILL.md` — v3.0.0 (55 строк)
</canonical_refs>
