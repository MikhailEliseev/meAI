# Phase 4: New Sections & Data Depth - Context

**Gathered:** 2026-06-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Доставить отчёты пресейла со всеми 10 секциями референса `ИПХиК (2).html` и глубокими данными — Strategy, Offer, Whitefields добавлены; динамика выручки за 3 года; конкретные URL СМИ-публикаций; детальные карточки конкурентов.

**Внутри scope:**
- 5 новых/расширенных секций отчёта: Strategy (09), Offer (10), Whitefields matrix (07), Experts+ (03), Content Analysis+ (04)
- 5 углублённых данных: 3-year revenue dynamics, media URLs, competitor cards, clinic metrics, ratings/reviews
- Multi-source fallback для внешних данных (revenue, competitors, media)
- LLM-генерация Strategy и Offer из собранных данных
- Скрейпинг сайтов клиник для регалий врачей
- Скрейпинг форумов/отзывов для страхов пациентов
- Сбор рейтингов с ПроДокторов + Яндекс.Карты

**Вне scope:**
- Переписывание HTML дизайн-системы (канон — Phase 3 closed this)
- Нарративная глубина интерпретации (Phase 5 — Deep Interpretation)
- Синхронизация SOUL.md/SKILL.md/phases.py (Phase 6 — Documentation Sync)
- Новые источники данных кроме перечисленных ( nouveaux-API — backlog)

</domain>

<decisions>
## Implementation Decisions

### Strategy Section (SEC-01) — LLM-driven

- **D-01:** Strategy генерируется LLM в Pass 3 из ВСЕХ собранных данных (competitors, instagram_gaps, patient_fears, content_gaps, reputation_gaps). Не шаблон, не placeholders — полная LLM-генерация под конкретную клинику.
- **D-02:** 5 направлений фиксированы как каркас (content, Telegram, GEO, reputation, cross-promo), но СОДЕРЖИМОЕ каждого направления — LLM генерирует конкретные шаги под эту клинику. Не "создайте Telegram-канал", а "создайте Telegram-канал, посты 3/нед, контент: {до/после пациентов с согласия}, потому что конкурент {X} имеет 50K подписчиков при +20%/мес".
- **D-03:** Basis для рекомендаций (ALL 4):
  1. **Конкуренты (best practices)** — что работает у конкурентов, рекомендовать клиенту повторить
  2. **Content gaps врачей** — где врачи слабы в Instagram (из секции 04), там точка роста
  3. **Страхи пациентов** — топ-5 страхов (из секции 04 форумов), закрыть контент-планом
  4. **Reputation gaps** — где клиент проигрывает в рейтингах/отзывах (ПроДокторов, Яндекс.Карты)

### Offer Section (SEC-02) — Claude's Discretion

- **D-04:** Offer section («Что AIM может сделать для клиники») следует тому же паттерну что SEC-01 — LLM-генерация из собранных данных. Конкретные шаги + CTA. Claude определяет структуру (виджеты, таймлайн, тарифы, что-то ещё) на этапе планирования.

### Whitefields Matrix (SEC-03)

- **D-05:** 4 категории колонок в матрице:
  1. **Услуги** — пластика груди/липосакция/инъекции/лазер/нити (✓/✗)
  2. **Цены** — топ-3 услуги (диапазон ₽)
  3. **Врачи** — количество хирургов/косметологов, регалии (КМН, профессор)
  4. **Digital presence** — Instagram K, Telegram, SEO rank, рейтинг
- **D-06:** Размер: **client + 3 конкурента = 4 columns** (минимум). Если prescan нашёл больше — брать топ-3 по выручке или по релевантности. Если меньше 3 конкурентов — честная надпись в отчёте.
- **D-07:** Источник данных — каждая ячейка берётся из уже собранных данных (competitors analysis, find_doctor_handles, run_instagram_content, find_company_financials). Не отдельный API-call.

### Experts Section (SEC-04) — расширение Phase 3

- **D-08:** Phase 3 дал ФИО + Instagram-метрики. Phase 4 добавляет регалии из сайта клиники: КМН/профессор/ДМН, стаж, образование. Источник — site scrape staff/doctors pages через `find_doctor_handles` (он уже скрейпит сайт) или новый lightweight-scraper.
- **D-09:** Соединение данных: Instagram-данные (Phase 3) + регалии (Phase 4) мёрджатся по ФИО врача. LLM ответственный за resolution неоднозначностей (variations в ФИО).

### Content Analysis (SEC-05) — дополнение страхов

- **D-10:** Phase 3 дал стиль/темы/пробелы Instagram. Phase 4 добавляет **Топ-5 страхов пациентов** через скрейп форумов:
  - ПроДокторов (отзывы по врачу/клинике)
  - Otzovik
  - IRecommend
  - Woman.ru (health section)
- **D-11:** LLM извлекает топ-5 страхов из текстов отзывов (не из star ratings). Формат: «{страх} — {почему упоминается} ({кол-во упоминаний})». Например: «Больно — 47 упоминаний из 120 отзывов».

### Revenue Dynamics (DAT-01) — fallback chain

- **D-12:** Multi-source fallback chain в порядке приоритета:
  1. `bo.nalog.ru` (ГИР БО) — первоисточник, бесплатно, авторитетно. Уже используется в `find_company_financials`.
  2. `rusprofile.ru` — расширенные финансы, может иметь исторические данные
  3. `rsp.ru` / RusПрофиль — backup источник
- **D-13:** **Strict <3-year rule:** если за все 3 года данных нет — **НЕ показывать секцию динамики**, честная надпись «Динамика выручки недоступна — нет данных в открытых источниках». Если есть 1-2 года — тоже не показывать (строго). Цель: исключить вводящий в заблуждение partial-data.
- **D-14:** Формат отчёта при наличии 3 лет: таблица год → выручка → YoY %, и blockquote с выводом («+79% за 3 года, растёт быстрее рынка на X%»).

### Media URLs (DAT-02) — multi-search

- **D-15:** Multi-search по 5 СМИ через `firecrawl_search`:
  ```python
  for smi in ['Forbes', 'RBC', 'Vademecum', 'Kommersant', 'ТАСС']:
      results = firecrawl_search(f'{clinic_name} {smi}')
      → URLs + dates + titles
  ```
- **D-16:** Если firecrawl_search недоступен — fallback на `perplexity_search` с тем же промптом.
- **D-17:** Рендеринг: **простой список с гиперссылками** (`Forbes — "Топ-10 клиник" — 12.03.24 → ссылка`). Не карточки с лого (избыточно для MVP).
- **D-18:** Честный блок если 0 упоминаний: «В СМИ не упоминалась за последние 3 года» + рекомендация PR-активности в Strategy section.

### Competitor Cards (DAT-03) — multi-source с fallback

- **D-19:** Для каждого конкурента оркестратор вызывает источники в порядке:
  1. `find_company_financials` (nalog.ru) — выручка, год основания, ОКВЭД, сотрудники
  2. `perplexity_search` или `rusprofile` scrape — доп. финансы (если nalog пустой)
  3. `firecrawl_scrape` сайта конкурента — хирурги, специфика, услуги
  4. `run_instagram_content` — для critical niches (Phase 3 infrastructure)
- **D-20:** Карточка конкурента содержит: название, год, выручка (текущий год), # хирургов/косметологов, Instagram handle (если есть), специфика (LLM из site scrape).

### Clinic Metrics (DAT-04)

- **D-21:** Раздел метрик клиники (в About section) берётся из собранных данных: выручка, прибыль, сотрудники, лицензии, ОКВЭД на человеческом языке. Источник — `find_company_financials` + `run_prescan` ( лицензии с сайта). LLM переводит ОКВЭД-коды в человеческий язык.

### Ratings (DAT-05) — минимум платформ

- **D-22:** Только 2 платформы: **ПроДокторов** + **Яндекс.Карты**. Минимум для MVP. Остальные (2ГИС, Google, Zoon, Отзовик, IRecommend) — backlog.
- **D-23:** Источник: существующие инструменты (если есть `run_review_platforms`) или site-scrape / API для двух выбранных платформ.

### Pass 3 Prompt Architecture

- **D-24:** Pass 3 prompt расширяется: LLM получает все собранные данные + явные инструкции для каждой новой секции (Strategy, Offer, Whitefields matrix). Шаблон: «На основе {collected_data} сгенерируй секцию Strategy с 5 направлениями...», и т.д. для каждой секции.
- **D-25:** QC checklist (из Phase 2) расширяется: добавить пункты для новых секций (Strategy present? Offer present? Whitefields 4×4 matrix? Media URLs >= 1? Ratings present?). Total items: 15 → ~20-22.

### Claude's Discretion

- Точная структура Pass 3 prompt для Strategy и Offer (какие kwargs передавать, как форматировать вывод)
- Какой именно scraper использовать для регалий врачей (расширение find_doctor_handles или новый lightweight)
- Какой инструмент использовать для рейтингов (существующий или новый скрейпер)
- Реализация multi-search для СМИ (последовательно 5 вызовов или батч)
- Формат карточек конкурентов (фиксированная шаблонная карточка vs LLM-generated блок)
- Точные QC checklist items для новых секций
- Деплой изменений на сервер (docker cp per Phase 3 pattern)

### Folded Todos

(нет — cross-reference todos не производился)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 3 Architecture (Instagram + Orchestrator)
- `.planning/phases/03-instagram-integration/03-CONTEXT.md` — Phase 3 decisions (orchestrator, mini-call, hard-FAIL pattern, deploy via docker cp)
- `.planning/phases/03-instagram-integration/03-VERIFICATION.md` — Phase 3 verification (orchestrator wiring, QC 15-item checklist with item 5 = Instagram)
- `AIM/hermes/app/orchestrator/three_pass.py` — 3-pass entry point, between-pass hooks (where to add new sections logic)
- `AIM/hermes/app/orchestrator/pass_collect.py` — Pass 1 prompt (where to add collection rules for new data)
- `AIM/hermes/app/orchestrator/pass_gap_analyze.py` — Pass 2 QC prompt (where to add new QC items)
- `AIM/hermes/app/orchestrator/pass_fill_assemble.py` — Pass 3 prompt (where to add Strategy/Offer/Whitefields generation rules)
- `AIM/hermes/app/orchestrator/qc_checklist.py` — 15-item QC_CHECKLIST (extend to ~20-22 items)

### Phase 2 Architecture (3-pass + QC)
- `.planning/phases/02-3-pass-orchestrator-coverage-checklist/02-VERIFICATION.md` — full orchestrator spec, soft QC gate behavior, coverage report format
- `AIM/hermes/app/orchestrator/coverage_reporter.py` — CoverageReport dataclass (extend with new items)

### HTML Reporter
- `AIM/hermes/app/tools/generate_html_report.py` — HTML reporter in design-system AIM (dual theme, glass cards). Add new sections: Strategy (09), Offer (10), Whitefields matrix (07), Media list with URLs, Competitor cards
- `AIM/wordpress-core/wp-content/themes/aim-theme/design-showcase-dual-theme.html` — canonical design-system reference

### Existing Tools
- `AIM/hermes/app/tools/find_company_financials.py` — financials from nalog.ru (use for 3-year revenue + clinic metrics + competitor cards)
- `AIM/hermes/app/tools/run_smi_mentions.py` — existing СМI-mentions tool (check if suitable for media URLs DAT-02)
- `AIM/hermes/app/tools/run_review_platforms.py` — existing review platform scraper (check if covers ПроДокторов/Яндекс.Карты for DAT-05)
- `AIM/hermes/app/tools/firecrawl_search` (in registry) — for media multi-search
- `AIM/hermes/app/tools/find_doctor_handles.py` — site scrape for doctor info (extend for регалии SEC-04)
- `AIM/hermes/app/pipeline/engine.py:_TOOL_HANDLERS` — 24 entries after Phase 3 (add new tools if needed)

### Reference HTML Report
- `ИПХиК (2).html` (referenced in PROJECT.md) — 78KB, 10 sections, канон для полноты отчёта
- `AIM/wordpress-core/wp-content/themes/aim-theme/design-showcase-dual-theme.html` — дизайн-система

### Project-Level
- `.planning/PROJECT.md` — Core value, constraints, три версии SOUL.md
- `.planning/REQUIREMENTS.md` §Sections (SEC-01..05) + §Data Depth (DAT-01..05) — Phase 4 requirements
- `CLAUDE.md` — AIM context, design-system, Hermes architecture, deploy constraints

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/orchestrator/three_pass.py` (Post-Phase 3) — 3-pass cycle with mini-call niche detection between Pass 1/2 + `_apply_niche_conditional_coverage` helper. Same architecture for new sections.
- `app/orchestrator/pass_collect.py` (Post-Phase 3) — `_build_pass_collect_prompt(state)` helper with niche-aware rules. Extend for new collection rules (media search, forum scrape).
- `app/orchestrator/pass_fill_assemble.py` — Pass 3 prompt with kwargs instructions. Extend with Strategy/Offer/Whitefields kwargs.
- `app/tools/generate_html_report.py` — Phase 3 added `_build_no_instagram_block` + `_maybe_build_no_instagram_block`. Same pattern for new sections.
- `app/tools/find_company_financials.py` — existing nalog.ru integration. Extend with multi-year query (DAT-01).
- `app/tools/run_smi_mentions.py` — VERIFY EXISTS. If suitable, adapt for DAT-02 media URLs.
- `app/tools/run_review_platforms.py` — VERIFY EXISTS. If covers ПроДокторов/Яндекс.Карты, use for DAT-05.

### Established Patterns
- **Orchestrator-first (Phase 2-3):** LLM выбирает инструменты, `_TOOL_HANDLERS` для fallback. Новые инструменты добавляются в registry + `_TOOL_HANDLERS`.
- **Soft QC gate + hard-FAIL override (Phase 2-3):** QC checklist soft, кроме niche-critical Instagram item. Phase 4 добавляет новые items (Strategy? Offer? Whitefields?) — определить hard/soft per-item.
- **Mini-call pattern (Phase 3):** Короткие LLM-вызовы между проходами. Можно использовать для niche-specific data extraction (например, extract страхи из отзывов).
- **Honest reporting (Phase 2-3):** «данные недоступны: {reason}» вместо прочерков. Применить ко всем новым секциям.
- **Deploy via docker cp (Phase 3):** Деплой через `docker cp` + restart gateway, без rebuild image.

### Integration Points
- `engine.py:_TOOL_HANDLERS` — добавить новые инструменты (если появляются новые scrapers)
- `pass_collect.py` — добавить collection rules для media/forums
- `pass_gap_analyze.py` — расширить QC checklist на ~5-7 новых items
- `pass_fill_assemble.py` — добавить Strategy/Offer/Whitefields generation rules
- `generate_html_report.py` — добавить рендеринг 3-4 новых секций
- `qc_checklist.py` — расширить QC_CHECKLIST с новыми items

</code_context>

<specifics>
## Specific Ideas

- Strategy section — explicit basis из 4 источников (конкуренты + gaps + страхи + reputation), не "general advice"
- Whitefields — именно **матрица** 4×4, не список content_gaps. 4 категории колонок фиксированы (Услуги/Цены/Врачи/Digital)
- Revenue — **строгое правило <3 лет = не показывать**. Не пытаться экстраполировать или показывать частичные данные.
- Media — multi-search по 5 конкретным СМИ (Forbes/RBC/Vademecum/Kommersant/ТАСС), не общий web search
- Страхи пациентов — топ-5 из **текстов отзывов** (не star ratings), с количеством упоминаний
- Competitor cards — multi-source с fallback chain (nalog → rusprofile → site → Instagram)

</specifics>

<deferred>
## Deferred Ideas

- Расширение рейтингов на 2ГИС, Google Maps, Zoon, Отзовик, IRecommend — DAT-05 v2 (backlog)
- Карточки с лого СМИ вместо простого списка — UI polish (Phase 5 или позже)
- Прогноз выручки LLM при частичных данных — отклонено (нарушает ORC-04 «не выдумывать»)
- Ручной список СМИ-упоминаний от админа — backlog (для VIP-клиентов)
- Brand Analytics / Mention / Medialogia — платные медиа-мониторинги, не в текущем бюджете

</deferred>

---

*Phase: 4-New Sections & Data Depth*
*Context gathered: 2026-06-24*
