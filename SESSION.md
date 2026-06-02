# Session: 2026-06-02

## Phase 22: PRESALE Flow Redesign — COMPLETED ✅

**Date:** 2026-06-02
**Status:** Все code changes реализованы, 27/27 unit-тестов проходят. E2E-тест требует Docker.

### Новый 7-шаговый PRESALE-поток

```
1. Client URL → run_prescan (5 параллельных потоков, 60-90s)
   ├─ structure: specialization, city, services, doctors, prices
   ├─ financials: INN extraction → nalog.ru → revenue/profit
   ├─ seo: quick SEO scan (score, mobile, SSL, speed)
   ├─ reviews: rating, count, praise, complaints
   └─ social: last post date, platform, links

2. prescan.revenue → find_competitors(client_revenue=X)
   └─ Gap-scoring: +0.08–0.12 bonus когда оборот конкурента в [1.2x, 1.5x]

3. "Смотрим этих конкурентов или вы приложите своих?"
   └─ Ветвление: auto-competitors vs named_competitors

4. Если named → идентификация клиник (опечатки, названия) → поиск сайтов

5. Выбранные конкуренты → run_ci_analysis (deep-tier)
   └─ Полный сбор: SEO-аудит, отзывы, соцсети, контент-анализ

6. Формирование финального отчёта

7. Сбор контактов → Telegram-нотификация
```

### Реализованные файлы

#### Новые (4):
- `AIM/src/aim/api/presale.py` — POST /api/presale/prescan endpoint
- `AIM/hermes/app/tools/run_prescan.py` — Hermes tool для prescan
- `AIM/tests/unit/test_prescan_orchestrator.py` — 11 тестов PrescanOrchestrator
- `AIM/tests/unit/test_competitor_gap_scoring.py` — 16 тестов gap-scoring

#### Изменённые (6):
- `AIM/src/aim/main.py` — +presale_router
- `AIM/src/aim/api/competitors.py` — +client_revenue в FindCompetitorsRequest
- `AIM/src/aim/services/competitor_matcher.py` — gap-bonus в _score_one()
- `AIM/hermes/app/tools/__init__.py` — +run_prescan (16 tools)
- `AIM/hermes/app/tools/find_competitors.py` — +client_revenue параметр
- `AIM/hermes/app/agent_wrapper.py` — полностью новый _presale_prompt() под 7 шагов

### Тесты: 27/27 PASSED

**TestGapBonusFormula (9):** formula tests — ratio boundaries, center peak, zero revenue
**TestGapBonusApplied (2):** bonus increases score, score ≤ 1.0 cap
**TestRevenueMatch (5):** 1:1 = 0.8, 2x = 1.0 peak, zero = 0.5
**TestPrescanResult (2):** empty/full serialization
**TestPrescanOrchestrator (3):** URL normalization, error isolation, progress callback
**TestINNValidation (6):** valid 10/12-digit, invalid checksum/short/empty/non-digit

### Отложено
- #48/#49: Баг-фиксы (rating 0.0, API quotas)
- E2E-тест на реальных клиниках (требует Docker: aim-app + aim-hermes)
