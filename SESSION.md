# Session: 2026-06-20 — Hermes v7 SOUL Redesign

## Текущий фокус: Commit & cleanup deployment fixes

### 2026-06-20: 16-Phase Pipeline — Deployed & Verified

| Задача | Статус |
|--------|--------|
| session_archive.py, run_full_scout.py, 5 стабов | ✅ Commit 293069a |
| phases.py (13→16, float IDs), states.py (int→float) | ✅ Commit 293069a |
| firecrawl_key_bank.py fix (classify_exhaustion, get_next_key, active_count) | ✅ Deployed |
| agent_wrapper.py LLM_PROVIDER support | ✅ Deployed |
| docker-compose.yml OMNIROUTE_URL | ✅ Deployed |
| .env.production — DeepSeek API key | ✅ sk-37839c50424c4d37b0c2a071eb3d5e55 |
| Тестовый прогон toriclinic.ru #1 | ✅ 17/17 фаз, были ошибки mark_exhausted |
| Тестовый прогон toriclinic.ru #2 | ✅ 17/17 фаз, без ошибок, отчёт mhz6urmb |
| Все 37 aim-operations + 15 debug тулов | ✅ Регистрируются без ImportError |
| AIM API 500 (run_seo_audit, run_content_analysis) | ⚠️ Баги на стороне aim-app, не Hermes |
| Firecrawl ключи | ⚠️ Большинство exhausted (402) |

### Что задеплоено
- **16-фазный пайплайн:** tool-based ONBOARDING (LLM вызывает run_full_scout)
- **Float phase IDs:** 0.0, 0.5, 0.75, 0.8, 1.0, 2.0, 3.0, 3.2, 3.5, 3.6, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0
- **LLM:** DeepSeek через OMNIROUTE_URL=https://api.deepseek.com/v1
- **Ключи:** FirecrawlKeyBank с ротацией 11 ключей
- **Удалено:** «Проактивная автономность», Magister-архитектура, старый пресейл-флоу, уроки psyholog48, orchestrate/run_prescan
- **Сохранено:** тон (Вы/ты, Привет зайка), 7 специализаций, КП-правила, самообучение, критические правила

### Архитектура контейнера hermes-20.06
- **HERMES_HOME:** `/opt/data/SOUL.md` (volume: `/opt/hermes-data/SOUL.md`)
- **SOUL.md в образе:** `/opt/hermes/skills/aim/SOUL.md` (обновлён)
- **14 тулов:** `/opt/hermes/app/tools/`
- **Pipeline:** `/opt/hermes/app/pipeline/`
- **FastAPI:** `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- **Gateway:** `/usr/local/bin/hermes gateway run --accept-hooks`

### 14 зарегистрированных тулов (_TOOL_HANDLERS)
find_competitors, run_seo_audit, run_content_analysis, run_ci_analysis,
run_pagespeed, run_smi_mentions, web_search, run_hh_analysis,
run_review_platforms, run_doctor_dossiers, run_content_gaps,
find_company_financials, generate_html_report, publish_scout_report

### Next: тестовый прогон на toriclinic.ru для верификации всех 13 фаз
