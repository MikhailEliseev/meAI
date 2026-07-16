# PRESALE Flow Redesign — Design Spec

**Date:** 2026-06-02
**Status:** Approved
**Type:** Architecture + Flow Redesign

## Objective

Переработать PRESALE-поток Hermes: от последовательного «SEO-аудит → спросить → найти конкурентов → проанализировать» к умному диалогу с параллельным сбором данных, поиском конкурентов с gap на рост (+20-50% оборота), и возможностью клиента предложить своих конкурентов (с опечатками, названиями).

## Current Flow (AS-IS)

```
1. URL
2. SEO-аудит (run_seo_audit, 10-15 сек)
3. Спросить про конкурентов
4. find_competitors (120-180 сек)
5. Оценка релевантности
6. CI-анализ (run_ci_analysis, 3+ мин)
7. Финальный отчёт (история → данные)
8. Сбор контакта
```

Проблемы текущего потока:
- Клиент ждёт 10-15 сек SEO-аудита, потом ещё 120-180 сек конкурентов — две паузы вместо одной
- Нет данных об обороте клиента до поиска конкурентов → конкуренты находятся без учёта масштаба
- Если клиент даёт своих конкурентов — нет AI-распознавания (опечатки, названия без URL)
- Нет быстрого среза отзывов и соцсетей на этапе pre-sale (только в deep-анализе)

## New Flow (TO-BE)

```
1. URL — «Скиньте сайт — я быстро посмотрю»
2. Prescan (5 потоков параллельно, 60-90 сек, с прогрессом)
   ├─ Услуги/направления/врачи/цены (service_extractor)
   ├─ Оборот (rusprofile/nalog по ИНН)
   ├─ SEO-косяки (быстрый аудит)
   ├─ Отзывы (первые 20, рейтинг, что хвалят/жалуются)
   └─ Соцсети (последний пост за 2 недели)
3. find_competitors с gap +20-50% оборота (120-180 сек)
4. Развилка: «Смотрим этих (чуть выше по обороту) или приложите своих?»
5а. Свои → find_competitors(named_competitors=...) → Google Maps + веб-поиск
5б. Подтверждение списка → present_competitors
6. Deep-анализ (расширенный CI, 3+ мин)
   ├─ SEO (ключевые слова, позиции, структура)
   ├─ Отзывы (тематический анализ: что хвалят/жалуются)
   ├─ Врачи (имена, опыт, ключевые персоны)
   ├─ Соцсети (посты, вовлечённость)
   ├─ Реклама (каналы, креативы)
   └─ Цены (матрица по услугам)
7. Финальный отчёт (история → данные) + контакт
```

Ключевые отличия:
- **Одна пауза вместо двух:** шаги 2+3 = один блок ожидания с прогрессом
- **Gap на рост:** конкуренты с оборотом +20-50% → «вот куда расти»
- **Prescan даёт немедленную ценность:** SEO-косяки, отзывы, соцсети — сразу
- **AI-распознавание:** клиент пишет названия с опечатками → система находит через Google Maps + веб-поиск
- **Deep вместо quick:** после выбора конкурентов — полный разбор, не быстрый CI

## API Changes

### 1. NEW: `POST /api/presale/prescan`

**Назначение:** Параллельный экспресс-сбор данных о сайте клиента.

```python
class PrescanRequest(BaseModel):
    url: str

class PrescanResult(BaseModel):
    # -- service_extractor --
    specialization: str
    city: str
    services: list[str]
    doctors: list[dict]       # [{name, title, order_on_page}]
    price_hints: list[dict]   # [{service, price}]

    # -- nalog --
    inn: str
    revenue_year: int | None
    profit_year: int | None
    financial_year: int | None

    # -- SEO quick scan --
    seo_score: int
    seo_issues: list[str]     # ["не адаптирован под мобильные", "загрузка 4.2 сек"]

    # -- reviews quick scan --
    rating: float | None
    reviews_count: int
    review_themes: dict       # {praise: [...], complaints: [...]}

    # -- social --
    last_post_date: str | None        # ISO date or None
    last_post_platform: str | None    # "vk", "telegram", "instagram"
```

**Реализация:** `PrescanOrchestrator` (~150 строк) — запускает 5 существующих сервисов параллельно через `asyncio.gather`, агрегирует результат. Никакой новой логики извлечения данных — только оркестрация.

### 2. MODIFIED: `POST /api/competitors/find`

Добавляется опциональное поле:

```python
class FindCompetitorsRequest(BaseModel):
    url: str
    count: int = 3
    named_competitors: list[str] | None = None
    client_revenue: int | None = None  # NEW
```

**Логика в CompetitorMatcher:** если `client_revenue` передан → бонус +8-12 очков в `_score_one()` для конкурентов с оборотом в диапазоне `[client_revenue * 1.2, client_revenue * 1.5]`. Не жёсткий фильтр (чтобы не потерять релевантных), а повышающий коэффициент.

`named_competitors` уже поддерживается — используется для шага 5а (клиент дал своих).

### 3. MODIFIED: `POST /api/competitors/analyze`

Расширяется с quick-tier (4 фазы) до deep-tier: добавляются фазы для глубокого анализа врачей, соцсетей и рекламы. Контракт ответа не меняется — существующие поля получают более полные данные.

## Pacing & Progress

Hermes показывает промежуточные результаты (вариант Б из обсуждения):

```
«Вижу стоматологию в Казани, 12 врачей, оборот ~3 млн...»     ← prescan: услуги + оборот
«По SEO: сайт не адаптирован под мобильные, загрузка 4.2 сек»   ← prescan: SEO-косяки
«Отзывы: 4.3★, 47 отзывов — хвалят врачей, жалуются на очереди» ← prescan: отзывы
«Последний пост в VK — 3 дня назад»                              ← prescan: соцсети
«Ищу конкурентов с оборотом 3.6–4.5 млн, похожие услуги...»     ← переход к шагу 3
```

Прогресс передаётся через существующий механизм `push_tool_progress` в Hermes.

## Competitor Identification (Шаг 5а)

Когда клиент даёт своих конкурентов:

1. Hermes вызывает `find_competitors(url, named_competitors=["Смайл Клиник", "Дентал Проффи", "на Тверской"])`
2. CompetitorMatcher для каждого имени запускает:
   - Apify Google Maps search (название + город)
   - Если не найдено → веб-поиск (SerpAPI fallback)
3. Что найдено → возвращает с confidence score
4. Что не найдено → возвращает в `not_found` (Hermes: «Не нашёл „на Тверской которая", уточните сайт?»)

## SOUL.md Changes

PRESALE-секция (строки 35-220) переписывается под 7 новых шагов. Формат сохраняется:
- Пошаговые инструкции с примерами диалогов
- Что можно/нельзя в PRESALE
- Принципы: живой диалог, не протокол
- Промежуточный прогресс обязателен

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `AIM/src/aim/api/presale.py` | NEW | `POST /api/presale/prescan` endpoint |
| `AIM/src/aim/services/prescan_orchestrator.py` | NEW | PrescanOrchestrator — параллельный запуск 5 сервисов |
| `AIM/src/aim/api/competitors.py` | MODIFY | `FindCompetitorsRequest` +`client_revenue` |
| `AIM/src/aim/services/competitor_matcher.py` | MODIFY | Gap-бонус в scoring при `client_revenue` |
| `AIM/src/aim/subagents/competitive_intel/orchestrator/ci_orchestrator.py` | MODIFY | Deep-tier: фазы врачей, соцсетей, рекламы |
| `AIM/hermes/skills/aim/SOUL.md` | MODIFY | PRESALE-секция (7 шагов вместо 8) |
| `AIM/hermes/app/tools/run_prescan.py` | NEW | Hermes tool: вызывает `/api/presale/prescan` |
| `AIM/hermes/app/tools/find_competitors.py` | MODIFY | +`client_revenue` параметр |
| `AIM/hermes/app/agent_wrapper.py` | MODIFY | `_presale_prompt()` синхронизирован с новым SOUL.md |

## What Does NOT Change

- `find_company_financials` tool — остаётся для точечных запросов
- `run_seo_audit` tool — остаётся для ACTIVE-режима
- `run_ci_analysis` tool — остаётся, но вызов идёт с `tier=deep`
- `collect_contact`, `present_competitors`, `qualify_lead` — без изменений
- ACTIVE и ADMIN режимы Hermes — без изменений

## Success Criteria

1. Prescan возвращает агрегированные данные за < 90 сек
2. find_competitors с `client_revenue` поднимает конкурентов с +20-50% оборотом в топ
3. `named_competitors` корректно находит клиники по названиям с опечатками
4. Deep-анализ покрывает: SEO, отзывы, врачей, соцсети, рекламу, цены
5. Hermes ведёт диалог с промежуточным прогрессом (не молча)
6. Все существующие тесты проходят
7. Новые тесты для PrescanOrchestrator и gap-scoring
