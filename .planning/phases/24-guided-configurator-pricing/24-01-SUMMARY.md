---
phase: 24-guided-configurator-pricing
plan: "01"
subsystem: hermes-pricing
tags: [configurator, pricing, presale, categorization, guided-configuration]
depends_on: []
provides: [LEGO-configurator, ServiceCategorizer, 4-category-pricing, handoff-mechanic]
affects: [QUALITY.md, SOUL.md, agent_wrapper.py, service_categorizer, HTML-CP]
tech-stack:
  added: [stdlib-dataclasses, Literal-typing]
  patterns: [rules-engine, deep-copy-immutable-defaults, revenue-gap-amplification]
requires: [prescan-api]
key-files:
  created:
    - AIM/hermes/app/tools/service_categorizer.py
    - AIM/hermes/app/tools/test_service_categorizer.py
    - AIM/hermes/knowledge/proposals/categorization_rules.md
  modified:
    - AIM/hermes/knowledge/proposals/QUALITY.md
    - AIM/hermes/skills/aim/SOUL.md
    - AIM/hermes/app/agent_wrapper.py
  verified:
    - AIM/hermes/knowledge/proposals/configurator_template.html
decisions:
  - "4-category model: БАЗА(locked)/РЕКОМЕНДОВАНО(pre-checked)/ОПЦИОНАЛЬНО(unchecked)/СЛЕДУЮЩИЙ ЭТАП(locked+deferred)"
  - "Блок 5 КП: нарративное обоснование вместо таблицы с ценами"
  - "Блок 10 КП: форма-конструктор с живым JS-пересчётом"
  - "Шаг 6 PRESALE: выжимка в чате (3 пункта + цена + результат + ссылка) вместо полного КП"
  - "Шаг 7 PRESALE: handoff на Михаила, не робот-апсейл"
  - "ServiceCategorizer: stdlib-only (dataclasses+typing), no external dependencies"
metrics:
  duration: "8m37s"
  completed: "2026-06-03T17:27:11Z"
  tasks: 3
  commits: 5
  files_changed: 6
  tests: "5/5"
---

# Phase 24 Plan 01: Guided Configurator Pricing Summary

Replaced 3-tier pricing (Базовый/Оптимальный/Максимальный) with 4-category LEGO configurator (БАЗА/РЕКОМЕНДОВАНО/ОПЦИОНАЛЬНО/СЛЕДУЮЩИЙ ЭТАП). Updated PRESALE dialog: step 6 gives chat summary + link to CP, step 7 hands off to Mikhail. Created ServiceCategorizer rules engine.

## Tasks Completed

| # | Name | Commit | Type |
|---|------|--------|------|
| 1 | Update QUALITY.md + SOUL.md — CP knowledge foundation | 36141ce | feat |
| 2 | Update _presale_prompt() — steps 6 and 7 | 88bed68 | feat |
| 3 | Create ServiceCategorizer + categorization_rules.md | 34b15c7, 3ca8536, f432fb2 | test+feat+docs |

## Key Changes

### QUALITY.md
- Block 5 renamed: «Что включено / Цена (3 уровня)» → «Нарративное обоснование услуг»
- Block 10 renamed: «Контакты + CTA» → «Конфигуратор» (4 categories, checkboxes, live total, contact form)
- Replaced «Трёхуровневое ценообразование» section with «Guided Configuration — 4 категории»
- Red flags: 3-level price flag replaced with 4-category checks + prescan data validation + chat summary format
- CP Quality Score: added «Соответствие категорий prescan» (0.10), adjusted weights (sum=1.0)

### SOUL.md
- Rule 19, block 5: narrative justification instead of 3-tier price
- Rule 19, block 10: configurator form instead of «Контакты + CTA»
- Rule 23: replaced «Цена — всегда 3 уровня» with «Цена — guided configuration с 4 категориями»
- New rule 23.1: Hermes does NOT write CP in chat — short summary with 3 points + price + result + link
- New rule 23.2: Step 7 handoff to Mikhail, not robot upsell
- Rule 32 red flags: updated for 4 categories + chat summary verification

### agent_wrapper.py (`_presale_prompt()`)
- Step 6: «Формат финального отчёта (Шаг 7)» → «Формат финального отчёта (Шаг 6 — Выжимка в чате)»
- Step 7: new «Handoff на Михаила» section with 3 client action paths
- New principles: CP as separate HTML file, handoff not upsell
- file_write added to PRESALE tools
- All 3-tier pricing mentions removed

### ServiceCategorizer (NEW)
- `service_categorizer.py`: rules engine with 5 categorization rules
  - **SEO**: score<40 or no sitemap/structured_data → recommended; score>=60 → optional
  - **Ads**: no campaigns → recommended; has campaigns → optional
  - **Content**: <10 pages → optional (not selected); >=10 → optional (selected)
  - **Social**: empty social_links → next_stage (locked); active → optional
  - **Revenue**: >=20% gap → amplify all recommended services (selected=True)
- 5/5 tests pass: poor SEO, good SEO, critical case + revenue gap, category validity, audit always base+locked

### categorization_rules.md (NEW)
- Knowledge file: 4 category definitions, 5 rule tables, integration guide for CP blocks 5/10, example walkthrough

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all components are fully implemented.

## Threat Flags

None — existing threat model covers all changes. ServiceCategorizer is stdlib-only (no npm/pip installs).

## Self-Check: PASSED

- [x] QUALITY.md — no 3-tier mentions, new blocks 5/10, guided configuration section, red flags updated
- [x] SOUL.md — new rules 23/23.1/23.2, updated 19/32, no old pricing patterns
- [x] agent_wrapper.py — steps 6 (summary) + 7 (handoff), new principles, no old patterns
- [x] service_categorizer.py — 5/5 tests pass, all categories valid
- [x] categorization_rules.md — exists, contains rule tables and examples
- [x] configurator_template.html — exists, contains recalcTotal(), cfg-item, cfg-checkbox
