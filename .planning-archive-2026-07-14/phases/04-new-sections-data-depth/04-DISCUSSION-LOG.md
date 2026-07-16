# Phase 4: New Sections & Data Depth - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-24
**Phase:** 4-New Sections & Data Depth
**Areas discussed:** Strategy section, Revenue dynamics, Media URLs, Whitefields matrix, Competitor data source, Experts extension, Patient fears, Ratings scope

---

## Gray Areas Selection

**User selected for discussion:**
- Strategy section (SEC-01)
- 3-year revenue (DAT-01)
- Media URLs (DAT-02)
- Whitefields matrix (SEC-03)

**Single-question decisions:**
- Competitor data source (DAT-03): Multi-source with fallback
- Experts extension (SEC-04): Регалии с сайта клиники
- Patient fears (SEC-05): Скрейп форумов и отзывов
- Ratings scope (DAT-05): ПроДокторов + Яндекс.Карты

---

## Strategy Section (SEC-01)

### Approach

| Option | Description | Selected |
|--------|-------------|----------|
| LLM из всех данных | Pass 3 prompt: на основе всех собранных данных (competitors, instagram_gaps, patient_fears, content_gaps) сгенерируй 5 направлений под эту клинику | ✓ |
| Гибрид: 5 осей + контекст | 5 осей фиксированы, для каждой LLM генерит шаги из данных | |
| Шаблон с placeholders | Полный шаблон, LLM подставляет значения | |

**User's choice:** LLM из всех данных
**Notes:** Самый адаптивный подход, полная персонализация под клинику.

### Basis (multi-select)

| Option | Description | Selected |
|--------|-------------|----------|
| Конкуренты (best practices) | Что работает у конкурентов успешно → рекомендовать повторить | ✓ |
| Content gaps врачей | Где врачи слабы в Instagram → точка роста | ✓ |
| Страхи пациентов (секция 04) | Закрыть страхи контент-планом | ✓ |
| Reputation gaps | Где клиент проигрывает в рейтингах/отзывах | ✓ |

**User's choice:** All 4 sources
**Notes:** Полнаяbasis = максимально обоснованные рекомендации.

---

## 3-Year Revenue (DAT-01)

### Source

| Option | Description | Selected |
|--------|-------------|----------|
| bo.nalog.ru (первоисточник) | Официальный, бесплатно, уже в find_company_financials | |
| rusprofile.ru (удобнее) | Структурированный вывод, может блокировать scrape | |
| Chain: nalog→rusprofile→rsp | Fallback chain, более робастный | ✓ |
| LLM-driven | LLM сама решает какой источник вызывать | |

**User's choice:** Chain: nalog→rusprofile→rsp
**Notes:** Robust approach — если nalog пустой, пробует следующий.

### Fallback for missing year

| Option | Description | Selected |
|--------|-------------|----------|
| Честная надпись | Показать что есть + 'за X год недоступно' | |
| Не показывать если <3 лет | Строго: только если все 3 года есть | ✓ |
| Прогноз LLM (опасно) | Экстраполяция — нарушение ORC-04 | |
| Пометка 'частично' | Мягче, показывает что есть | |

**User's choice:** Не показывать если <3 лет
**Notes:** Жёсткое правило — никаких вводящих в заблуждение partial-data.

---

## Media URLs (DAT-02)

### Source

| Option | Description | Selected |
|--------|-------------|----------|
| Multi-search по СМИ | firecrawl_search для каждого из 5 СМИ отдельно | ✓ |
| Perplexity batch-query | Один perplexity_search с продуманным промптом | |
| run_smi_mentions (existing) | Проверить существующий инструмент | |
| Проф. медиа-мониторинг | Brand Analytics / Mention / Medialogia (платный) | |

**User's choice:** Multi-search по СМИ
**Notes:** 5 вызовов (Forbes, RBC, Vademecum, Kommersant, ТАСС). Дорого, но максимально точно.

### Rendering

| Option | Description | Selected |
|--------|-------------|----------|
| Карточки с лого | Отдельная карточка на каждое СМИ-упоминание | |
| Список с гиперссылками | Простой список: СМИ — заголовок — дата — ссылка | ✓ |
| Честный блок 'нет упоминаний' | Если 0 упоминаний — отдельный блок | |

**User's choice:** Список с гиперссылками
**Notes:** Компактнее, быстрее рендерить.

---

## Whitefields Matrix (SEC-03)

### Columns (multi-select)

| Option | Description | Selected |
|--------|-------------|----------|
| Услуги (что делают) | ✓/✗ для топ-услуг | ✓ |
| Цены | Диапазоны ₽ на топ-3 услуги | ✓ |
| Врачи (количество, регалии) | Кол-во, КМН, профессора | ✓ |
| Digital presence | Inst K, Telegram, SEO rank, рейтинг | ✓ |

**User's choice:** All 4 categories
**Notes:** Полная матрица — 4 категории × N конкурентов.

### Rows (concurrency count)

| Option | Description | Selected |
|--------|-------------|----------|
| 3 конкурента (минимум) | client + 3 = 4 columns | ✓ |
| 5 конкурентов (развернуто) | client + 5 = 6 columns | |
| Адаптивно 3-5 | Зависит от prescan | |

**User's choice:** 3 конкурента
**Notes:** Минимум для сравнения, помещается на экран.

---

## Competitor Data Source (DAT-03)

| Option | Description | Selected |
|--------|-------------|----------|
| Multi-source с fallback | nalog → rusprofile → site scrape → Instagram | ✓ |
| Только nalog.ru + site scrape | Минимум источников | |
| Существующий CI Scout | Переиспользовать subagents/competitive_intel | |
| LLM-driven | LLM сама решает | |

**User's choice:** Multi-source с fallback
**Notes:** Оркестратор пробует источники по порядку, fallback на следующий при пустоте.

---

## Experts Extension (SEC-04)

| Option | Description | Selected |
|--------|-------------|----------|
| Регалии с сайта клиники | КМН/профессор/ДМН, стаж, образование (через site scrape) | ✓ |
| Пропустить (Phase 3 закрыл) | Ничего не делать | |
| + Фото и контакты | Доп. поля (Telegram, WhatsApp, кабинет) | |

**User's choice:** Регалии с сайта клиники
**Notes:** Расширение find_doctor_handles или новый scraper.

---

## Patient Fears (SEC-05)

| Option | Description | Selected |
|--------|-------------|----------|
| Скрейп форумов и отзывов | ПроДокторов, Otzovik, IRecommend, Woman.ru | ✓ |
| Perplexity (общие по нише) | Общие страхи, без персонализации | |
| Отложить на Phase 5 | Сосредоточиться на данных | |

**User's choice:** Скрейп форумов и отзывов
**Notes:** LLM извлекает топ-5 страхов из текстов (не star ratings).

---

## Ratings Scope (DAT-05)

| Option | Description | Selected |
|--------|-------------|----------|
| ПроДокторов | Основной мед-отзовик РФ | ✓ |
| Яндекс.Карты | Локальные отзывы | ✓ |
| 2ГИС | Второй по значимости локальный | |
| Google/Zoon/Отзовик/IRecommend | Дополнительные платформы | |

**User's choice:** ПроДокторов + Яндекс.Карты
**Notes:** Минимум для MVP, остальные — backlog.

---

## Claude's Discretion

- Точная структура Pass 3 prompt для Strategy и Offer (какие kwargs, формат вывода)
- Какой scraper для регалий (расширение find_doctor_handles или новый lightweight)
- Какой инструмент для рейтингов (существующий run_review_platforms или новый)
- Реализация multi-search для СМИ (последовательно 5 вызовов или батч)
- Формат карточек конкурентов (фиксированный шаблон или LLM-generated блок)
- Точные QC checklist items для новых секций (15 → ~20-22)
- Деплой изменений на сервер (docker cp per Phase 3 pattern)

## Deferred Ideas

- Расширение рейтингов на 2ГИС, Google Maps, Zoon, Отзовик, IRecommend — DAT-05 v2 (backlog)
- Карточки с лого СМИ — UI polish (Phase 5 или позже)
- Прогноз выручки LLM при частичных данных — отклонено (нарушение ORC-04)
- Ручной список СМИ-упоминаний от админом — backlog (для VIP-клиентов)
- Brand Analytics / Mention / Medialogia — платные медиа-мониторинги, не в текущем бюджете
