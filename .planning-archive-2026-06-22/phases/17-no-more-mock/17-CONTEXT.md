# Phase 17: No More Mock Data — CONTEXT

**Gathered:** 2026-05-19
**Status:** Ready for planning

## Phase Boundary

Заменить ВСЕ mock/synthetic данные в CI-агентах на реальные данные из веб-скрапинга и API. Подключить существующие API-клиенты (SEMrush, Ahrefs, GA4, Yandex Metrica, Playwright) к CI-пайплайну. Вычислять обещанные «3 числа» (пациенты/месяц, время-до-результата, цена-за-пациента). Убрать все `random.randint()`, `random.uniform()`, хардкоженные названия вроде «Дента», «Смайл», «ул. Примерная».

**Результат:** Система готова к запуску в реальный мир — без мультиков, без «Здоровье Лаб».

## Implementation Decisions

### D-01: Критический путь — ci_scout (GATEWAY)
ci_scout — первая точка входа в CI-пайплайн. Его mock-данные контаминируют ВСЕ downstream-агенты.
- **LOCKED:** Заменить `_generate_test_competitors()` на реальный поиск конкурентов через SerpAPI + SEMrush Domain Intelligence
- **LOCKED:** Убрать хардкоженные названия (`["Дента", "Смайл", "Зубная Фея"]`)
- **LOCKED:** Убрать сгенерированные URL (`f"https://{self._slugify(name)}.ru"`)
- **LOCKED:** Убрать `random.randint()` для рейтингов, адресов

### D-02: MOCK → REAL агенты (14 агентов)
Агенты, которые используют `random` или хардкоженные данные:
- ci_auditor — `random.randint(60, 95)` для всех 28 чеков → заменить на реальный PageSpeed API + HTML-анализ
- ci_reputation — `random.randint(20, 200)` отзывов → заменить на реальный скрапинг Яндекс.Карты/2ГИС/ПроДокторов
- ci_content — заменить на trafilatura + BeautifulSoup (по образцу ci_content_improved)
- ci_pricing — реальный скрапинг страниц цен
- ci_finance — удалить random financial data
- ci_vacancies — заменить на hh.ru API (уже есть hh_agent_playwright)
- ci_ecosystem — реальный анализ цифровой экосистемы
- ci_rank_tracker — подключить SerpAPI для реального отслеживания позиций
- ci_site_crawler — использовать существующий web_scraper (Playwright + Trafilatura)
- ci_backlink — подключить SEMrush/Ahrefs backlink API
- ci_marketing_strategy — logic-only (OK), но должен получать реальные данные
- ci_offer_generator — logic-only (OK)
- ci_prioritizer — logic-only (OK)
- ci_strategist — logic-only (OK)

### D-03: REAL-уже агенты (улучшить, не переписывать)
- ci_tech_real — уже делает реальные HTTP-запросы ✅
- ci_content_improved — уже использует trafilatura/httpx/BeautifulSoup ✅
- ci_deep_analyzer — уже делает BFS crawl + PageSpeed API ✅
- ci_url_validator — уже валидирует URL ✅
- ci_backlink — сейчас mock → подключить SEMrush backlinks API
- ci_qa_validator — logic-only (OK)
- ci_factchecker — logic-only (OK)
- business_report — logic-only (OK)

### D-04: Интеграция существующих API-клиентов
20+ реальных API-клиентов существуют, но НЕ подключены к CI-пайплайну:
- `AIM/src/aim/subagents/api_clients/semrush.py` — Keyword Magic Tool
- `AIM/src/aim/subagents/api_clients/semrush_client.py` — Domain Intelligence (конкуренты, backlinks)
- `AIM/src/aim/subagents/api_clients/ahrefs.py` — Ahrefs fallback
- `AIM/src/aim/subagents/api_clients/ga4_client.py` — Google Analytics 4
- `AIM/src/aim/subagents/api_clients/yandex_metrica_client.py` — Yandex Metrica
- `AIM/src/aim/subagents/api_clients/web_scraper.py` — Playwright + Trafilatura
- `AIM/src/aim/ai/seo/serp_analyzer.py` — SerpAPI real-time SERP
- `AIM/src/aim/agents/ci_swarm/hh_agent_playwright.py` — hh.ru вакансии
- **LOCKED:** Все CI-агенты должны использовать эти клиенты вместо mock-данных
- **LOCKED:** Circuit breaker, retry, rate limiting уже встроены в API-клиенты

### D-05: «3 числа» — patients/month, time-to-result, cost-per-patient
SOUL.md обещает эти метрики, но CI-пайплайн их НЕ вычисляет.
- patients_per_month — оценка на основе трафика × конверсии (из GA4/Metrica + бенчмарков)
- time_to_result — на основе сложности ниши и конкурентности
- cost_per_patient — на основе CPC (из SEMrush/Ahrefs) × conversion rate
- **LOCKED:** Добавить вычисление в ci_strategist или business_report

### D-06: CIOrchestrator — Direct Execution Path
Сейчас API-эндпоинты (seo.py, content.py) используют прямой вызов `orchestrator.execute_ci_analysis()`. Этот путь РАБОТАЕТ. Event Bus delegation path — сломанный скелет.
- **LOCKED:** Фокусируемся на Direct Execution Path (используется API)
- Event Bus delegation — отложить до следующей фазы

### D-07: Российский рынок — данные
- Яндекс.Карты / 2ГИС / ПроДокторов для отзывов
- Яндекс.Метрика для трафика
- Яндекс.Директ для рекламных данных
- hh.ru для вакансий (уже есть клиент)
- **LOCKED:** Все данные должны быть из российских источников (не Google Maps, не Yelp)

## Claude's Discretion

- Приоритетность: какие mock-агенты фиксить первыми (critical path: ci_scout → ci_auditor → ci_reputation → остальные)
- Архитектура: создавать ли универсальный `BaseRealAgent` с общими паттернами скрапинга
- Метод оценки «3 чисел» — какие именно формулы использовать
- Wave structure: как группировать планы для параллельного выполнения

## Specific Ideas

Из запросов пользователя:
1. «Никаких mock данных в production коде» — CLAUDE.md Mock Data Rule
2. «Мы делаем систему рабочую а не мультики» — каждая метрика должна быть из реального источника
3. «Как мне это запускать в мир?» — после фазы система должна быть launchable
4. «Максимальное количество инфы» — глубокий анализ, не поверхностный
5. «Все тестировать» — E2E тесты с реальными сайтами

## Deferred Ideas

- Event Bus delegation path — починить позже (сейчас не используется)
- CI-агенты для западного рынка — вне scope (фокус на РФ)
- Real-time мониторинг конкурентов — future phase

---

*Phase: 17-no-more-mock*
*Context gathered: 2026-05-19*
