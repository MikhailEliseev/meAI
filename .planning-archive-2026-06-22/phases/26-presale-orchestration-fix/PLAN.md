# Phase 26: Presale Pipeline — Skill Path Fix & Orchestration

**Status:** Planned
**Goal:** Hermes загружает 7 presale tools по имени (`skill_view(name='social-verifier')`), parent SKILL.md оркестрирует их через Goal Loop + Hard Gate.

## Tasks

### Task 1: Flatten skill directory structure
**Type:** refactor
**Target:** server (root@138.16.224.188)

Переместить 7 подскиллов из `software-development/presale-pipeline/` на один уровень вверх — в `software-development/`. Это единственный способ гарантировать, что `skill_view(name='social-verifier')` работает без полного пути.

```bash
cd /root/.hermes/skills/software-development/
mv presale-pipeline/social-verifier .
mv presale-pipeline/content-analyzer .
mv presale-pipeline/competitor-scorer .
mv presale-pipeline/financial-fetcher .
mv presale-pipeline/html-kp-generator .
mv presale-pipeline/tech-auditor .
mv presale-pipeline/reel-scraper .
```

**Verify:** `ls -d /root/.hermes/skills/software-development/*/` показывает 7 скиллов + presale-pipeline/

### Task 2: Rewrite parent SKILL.md как LLM-first orchestration layer
**Type:** create
**Target:** `/root/.hermes/skills/software-development/presale-pipeline/SKILL.md`

Новый parent SKILL.md (цель: < 200 строк):

**Структура:**
```markdown
---
name: presale-pipeline
title: Presale Pipeline Orchestrator
description: LLM-first orchestration — 7 tools + Goal Loop + Hard Gate
version: 3.0.0
depends_on:
  hermes_skills:
    social-verifier: ">=1.0"
    content-analyzer: ">=1.0"
    competitor-scorer: ">=1.1"
    financial-fetcher: ">=1.1"
    html-kp-generator: ">=1.1"
    tech-auditor: ">=1.0"
    reel-scraper: ">=1.0"
---

# Presale Pipeline v3.0.0 — LLM-First Orchestration

## Model Routing
- **Flash (deepseek-v4-flash)**: сбор данных → все 6 tools (social-verifier, content-analyzer, competitor-scorer, financial-fetcher, tech-auditor, reel-scraper)
- **Pro (deepseek-v4-pro)**: анализ + HTML → html-kp-generator

## Phase Sequence

### Phase 0: Init
1. skill_view(name='tech-auditor') — предварительный аудит сайта
2. skill_view(name='financial-fetcher') — собрать финансы клиники
3. Сохранить результат: /root/work/presale/{client}/log.jsonl

### Phase 1: Collect (Flash, параллельно)
4. skill_view(name='social-verifier') — 5 проходов, найти всех врачей
5. skill_view(name='competitor-scorer') — найти и скорить конкурентов
6. skill_view(name='reel-scraper') — собрать Reels для топ-врачей

### Phase 2: Analyze (Flash → Pro)
7. skill_view(name='content-analyzer') — per-expert карточки + 4 формата
8. run Gap Audit: сравнить собранное с эталонным чек-листом

### Phase 3: Hard Gate
9. Если gaps > 0 → Goal Loop: вернуться к Phase 1 для незакрытых gaps
10. Если gaps = 0 → переход к Phase 4

### Phase 4: HTML (Pro)
11. skill_view(name='html-kp-generator') — 12-block HTML
12. Pre-generation snapshot: сохранить все собранные данные
13. Post-generation validation: 12 критериев (Freshness, Verifiability, So What...)

## Hard Gate Rules
- 🚫 HTML НЕ генерируется, пока есть хотя бы 1 непроверенный атрибут
- ✅ Каждый факт должен иметь минимум 2 источника (confidence ≥ verified)
- ⚠️ Single-source факты помечаются как «требует уточнения»

## Goal Loop
- Режим: «повторяй, пока gaps > 0»
- Stopping condition: gaps = 0 ИЛИ 3 полных цикла без новых данных
- Max iterations: 3 полных цикла на фазу

## Structured Log
Все шаги пишут в `/root/work/presale/{client}/log.jsonl`:
```json
{"ts":"...", "phase":0, "tool":"tech-auditor", "status":"ok", "duration_s":12.3, "findings":8}
{"ts":"...", "phase":1, "tool":"social-verifier", "status":"ok", "duration_s":45.1, "doctors_found":5}
```

## Использование
Пользователь: «Сделай пресейл https://clinic.ru»
Hermes: 
1. Загружает presale-pipeline (этот файл)
2. Исполняет Phases 0-4, загружая tools по имени
3. На Hard Gate проверяет gaps
4. Если gaps > 0 → Goal Loop
5. Генерирует HTML только при gaps = 0
```

**Verify:** `wc -l /root/.hermes/skills/software-development/presale-pipeline/SKILL.md` < 200

### Task 3: Archive legacy SKILL.md → reference
**Type:** refactor
**Target:** server

```bash
mv /root/.hermes/skills/software-development/presale-pipeline/SKILL.md \
   /root/.hermes/skills/software-development/presale-pipeline/references/SKILL.md.v2.61.0-legacy
```

Старый файл (92KB, 757 строк) остаётся как референс для CSS, дизайн-системы, ключей, истории ошибок. НЕ как активный скилл.

### Task 4: Restart Hermes to pick up new paths
**Type:** ops
**Target:** server

```bash
systemctl restart hermes-work.service
systemctl status hermes-work.service --no-pager | head -5
```

### Task 5: Verify all 7 tools loadable by name
**Type:** verify
**Target:** server

Отправить тестовое сообщение в @iamaim_bot:
«Загрузи social-verifier, content-analyzer, competitor-scorer, financial-fetcher, html-kp-generator, tech-auditor, reel-scraper и покажи их версии»

**Критерий успеха:** Hermes загружает все 7 tools через `skill_view(name='...')` и показывает их metadata (version).

### Task 6: Verify new parent orchestration loads
**Type:** verify
**Target:** server

Отправить: «Загрузи presale-pipeline и покажи его фазы»

**Критерий успеха:** Hermes показывает Phase 0-4 с Hard Gate, Goal Loop и model routing.

## Files

### Modify (1):
1. `/root/.hermes/skills/software-development/presale-pipeline/SKILL.md` — полная перезапись (v2.61.0 → v3.0.0)

### Move (7):
2-8. 7 подскиллов: presale-pipeline/{name}/ → software-development/{name}/

### Archive (1):
9. Старый SKILL.md → references/SKILL.md.v2.61.0-legacy

## Verification

1. `ls -d /root/.hermes/skills/software-development/{social-verifier,content-analyzer,competitor-scorer,financial-fetcher,html-kp-generator,tech-auditor,reel-scraper}` — все 7 на месте
2. `wc -l /root/.hermes/skills/software-development/presale-pipeline/SKILL.md` < 200
3. systemctl status hermes-work.service = active
4. Hermes в чате загружает все 7 tools по короткому имени
5. Hermes показывает новый presale-pipeline v3.0.0 с Hard Gate и Goal Loop
