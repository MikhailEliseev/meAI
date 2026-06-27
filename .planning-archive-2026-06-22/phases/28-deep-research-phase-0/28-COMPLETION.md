---
phase: 28-deep-research-phase-0
status: COMPLETED
completed_date: 2026-06-06
version: 3.2.0
---

# Phase 28: Deep Research Phase 0 — Завершение

**One-liner:** Автономный pre-flight deep research с трёхуровневой классификацией врачей (star/core/team), интегрированный как обязательная Phase 0 перед каждым пресейлом.

## Что сделано

### Компоненты

| Компонент | Файл | Строк | Статус |
|-----------|------|-------|--------|
| SKILL.md | `AIM/hermes/skills/deep-research-phase-0/SKILL.md` | 491 | Задеплоен |
| Python helper | `AIM/hermes/app/tools/deep_research_merge.py` | 361 | Задеплоен (30/30 тестов) |
| Presale Pipeline v3.2.0 | `AIM/hermes/skills/presale-pipeline/SKILL.md` | ~160 | Задеплоен |
| Quality Gate | `AIM/hermes/app/tools/quality_gate.py` | 155 | Задеплоен |
| State Template | `AIM/hermes/skills/presale-pipeline/schemas/presale-state.template.json` | 26 | Задеплоен |

### Ключевые фичи

1. **Three-Tier Doctor Classification**: 12 regex-паттернов для российских мед.степеней (д.м.н., к.м.н., профессор, заслуженный врач РФ и др.)
2. **Tier-dependent Research Depth**: star (7-10 search), core (5), team (2-3)
3. **Full Auto Mode**: никаких подтверждений, ссылка → результат
4. **Political Firewall**: полная изоляция политического контента
5. **Atomic JSON Merge**: через tempfile + os.rename(), LLM никогда не пишет JSON напрямую

### Коммиты

| Commit | Описание |
|--------|----------|
| `89449d3` | TDD RED: 30 тестов |
| `4f2fd68` | TDD GREEN: 30/30 тестов проходят |
| `cd83488` | SKILL.md для deep-research-phase-0 |
| `520608f` | Интеграция в presale-pipeline v3.6.0 |
| `c57714f` | Документирование Phase 28 |

## Подтверждение приёмки

- [x] Все файлы на сервере (138.16.224.188)
- [x] 30/30 unit тестов проходят
- [x] Пресейл-пайплайн протестирован пользователем через Telegram
- [x] Full Auto Mode работает: бот не спрашивает подтверждений
- [x] Political Firewall активен в обоих скиллах
- [x] Пользователь подтвердил: «Очень нравится на Pre-Sale»

## Бэклог (не входит в Phase 28)

- Больше маркетинговых выводов в КП
- Phase 13-02: Яндекс.Директ
- Phase 13-03: VK/Telegram Ads
