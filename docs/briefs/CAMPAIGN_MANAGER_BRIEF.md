# Бриф: Campaign Manager Agent

**Дата:** 2026-05-10  
**Приоритет:** P1  
**Родительский Magister:** Ads Magister

## Назначение

Campaign Manager Agent — автоматизированный менеджер рекламных кампаний для медицинского маркетинга. Создаёт, запускает и управляет кампаниями в Яндекс.Директ и Google Ads, обеспечивая соответствие медицинским требованиям и оптимальное распределение бюджета.

**Основная задача:** Превратить маркетинговую стратегию в работающие рекламные кампании через автоматизированное создание, настройку и запуск.

## Контекст и специфика

**Медицинская специфика:**
- Compliance: 152-ФЗ (РФ), Google Ads Healthcare policy, Яндекс ограничения
- Запрещённые claims (гарантии результата, "лучший", "100% эффективность")
- Обязательные disclaimers (лицензия, противопоказания)
- Ограничения на таргетинг (нельзя по диагнозам, можно по симптомам)

**Платформы:**
- Яндекс.Директ (основная для РФ)
- Google Ads (дополнительная)
- Двойная модерация (автоматическая + ручная)

**Типы кампаний:**
- Поиск (текстовые объявления)
- РСЯ/КМС (баннеры, адаптивные объявления)
- Ретаргетинг (аудитории сайта)
- Lookalike (похожие аудитории)

## Интеграции

**Входные данные:**
- `campaign_brief` (dict) — бриф кампании от Ads Magister
  - `goal` (str) — цель (leads, traffic, brand_awareness)
  - `budget` (float) — бюджет в рублях
  - `duration` (int) — длительность в днях
  - `target_audience` (dict) — ЦА (geo, age, interests)
  - `services` (list) — услуги для продвижения
- `landing_pages` (list) — URL лендингов
- `brand_guidelines` (dict) — бренд-гайды
- `compliance_rules` (dict) — правила compliance

**Выходные данные:**
- `campaign_id` (str) — ID созданной кампании
- `campaign_structure` (dict) — структура кампании
  - `ad_groups` (list) — группы объявлений
  - `ads` (list) — объявления
  - `keywords` (list) — ключевые слова
  - `targeting` (dict) — настройки таргетинга
- `moderation_status` (str) — статус модерации
- `launch_status` (str) — статус запуска
- `warnings` (list) — предупреждения (если есть)

**Связанные агенты:**
- **Keyword Research Agent** — источник ключевых слов
- **Landing Content Agent** — источник лендингов
- **Budget Optimizer Agent** — оптимизация бюджета
- **Performance Monitor Agent** — мониторинг результатов
- **Medical Fact-Checker Agent** — проверка медицинских claims

**Внешние API:**
- **Яндекс.Директ API v5** — создание и управление кампаниями
- **Google Ads API** — создание и управление кампаниями
- **Яндекс.Метрика API** — настройка целей
- **Google Analytics API** — настройка целей

## Приоритеты исследования

### 🔴 КРИТИЧНО (обязательно глубоко изучить)

1. **Яндекс.Директ API v5**
   - Структура кампаний (Campaign → AdGroup → Ad → Keyword)
   - Типы кампаний (TEXT_CAMPAIGN, MOBILE_APP_CAMPAIGN, DYNAMIC_TEXT_CAMPAIGN)
   - Стратегии назначения ставок (HIGHEST_POSITION, WB_MAXIMUM_CLICKS, etc.)
   - Ограничения API (rate limits, batch operations)
   - Модерация (статусы, причины отклонения)

2. **Google Ads API**
   - Структура кампаний (Campaign → AdGroup → Ad → Keyword)
   - Healthcare policy (restricted content, certification requirements)
   - Responsive Search Ads (RSA) — до 15 заголовков, 4 описания
   - Smart Bidding стратегии (Target CPA, Maximize Conversions)
   - Модерация и policy violations

3. **Медицинская compliance для рекламы**
   - 152-ФЗ РФ (реклама медицинских услуг)
   - Запрещённые формулировки (гарантии, превосходство, "лучший")
   - Обязательные disclaimers (лицензия, противопоказания)
   - Google Ads Healthcare policy (certification, restricted content)
   - Яндекс ограничения (медицина, здоровье)

4. **Структура рекламных кампаний**
   - Иерархия (Campaign → AdGroup → Ad → Keyword)
   - Группировка ключевых слов (по intent, по услуге, по geo)
   - Типы соответствия (broad, phrase, exact)
   - Negative keywords (минус-слова)
   - Ad extensions (расширения объявлений)

### 🟡 ВАЖНО (изучить, но не так глубоко)

1. **Стратегии назначения ставок**
   - Manual CPC (ручное управление)
   - Automated bidding (автоматические стратегии)
   - Target CPA (целевая цена конверсии)
   - Maximize Conversions (максимум конверсий)
   - ROAS (return on ad spend)

2. **Таргетинг и аудитории**
   - Geo-таргетинг (города, регионы)
   - Демография (возраст, пол)
   - Интересы и поведение
   - Ретаргетинг (аудитории сайта)
   - Lookalike (похожие аудитории)

3. **Копирайтинг объявлений**
   - Формулы (AIDA, PAS, 4U)
   - Заголовки (до 30 символов Яндекс, 30 chars Google)
   - Описания (до 81 символа Яндекс, 90 chars Google)
   - Call-to-action (CTA)
   - Уникальное торговое предложение (УТП)

4. **Конверсионные цели**
   - Яндекс.Метрика цели (JavaScript, Composite)
   - Google Analytics цели (Destination, Event, Duration)
   - Атрибуция (last click, first click, linear)
   - Ценность конверсии

### 🟢 ОПЦИОНАЛЬНО (можно пропустить или поверхностно)

1. Динамические объявления (DSA)
2. Shopping кампании (для e-commerce)
3. Video кампании (YouTube)
4. App campaigns (мобильные приложения)

## Метрики успеха

**Качество:**
- Campaign creation success rate: > 95%
- Moderation pass rate: > 90%
- Compliance violations: 0
- Ad relevance score: > 7/10

**Производительность:**
- Time to create campaign: < 5 минут
- Time to launch: < 10 минут (после модерации)
- API uptime: > 99%
- Error rate: < 1%

**Стоимость:**
- Яндекс.Директ API: бесплатно (в рамках лимитов)
- Google Ads API: бесплатно (в рамках лимитов)
- Total cost per campaign: < 100 рублей (только API calls)

## Дополнительные материалы

**Интервью:** Нет (создано через бриф)  
**Связанные спецификации:**
- `KEYWORD_RESEARCH_SPEC.md` — источник ключевых слов
- `LANDING_CONTENT_SPEC.md` — источник лендингов
- `BUDGET_OPTIMIZER_SPEC.md` (TODO) — оптимизация бюджета
- `PERFORMANCE_MONITOR_SPEC.md` (TODO) — мониторинг результатов

**TODO из других агентов:**
- Keyword Research Agent: "Campaign Manager должен использовать кластеры ключевых слов"
- Landing Content Agent: "Campaign Manager должен проверять соответствие объявления и лендинга"

## Workflow (детальный)

```
1. Получить campaign_brief от Ads Magister
2. Validate brief (budget, duration, target_audience)
   ↓
3. Get keywords from Keyword Research Agent
   ↓
4. Group keywords by intent/service (ad groups)
   ↓
5. Generate ad copy for each ad group
   ↓
6. Check compliance (Medical Fact-Checker Agent)
   ↓
7. Create campaign structure (Яндекс.Директ API)
   ↓
8. Set up conversion goals (Яндекс.Метрика API)
   ↓
9. Submit for moderation
   ↓
10. Wait for moderation approval
   ↓
11. Launch campaign
   ↓
12. Send campaign_id + structure to Ads Magister
```

**Параллелизация:**
- Шаги 3-4 можно выполнять параллельно (keywords + grouping)
- Шаги 7-8 можно выполнять параллельно (campaign creation + goals setup)

## Примеры использования

**Пример 1: Создание поисковой кампании**
```python
result = await campaign_manager_agent.execute({
    "campaign_brief": {
        "goal": "leads",
        "budget": 50000,  # 50,000 рублей
        "duration": 30,  # 30 дней
        "target_audience": {
            "geo": ["Москва", "Санкт-Петербург"],
            "age": "25-54",
            "interests": ["здоровье", "медицина"]
        },
        "services": ["кардиология консультация", "ЭКГ"]
    },
    "landing_pages": ["https://example.com/cardiology"],
    "brand_guidelines": {...},
    "compliance_rules": {...}
})

# result.campaign_id: "12345678"
# result.campaign_structure: {"ad_groups": [...], "ads": [...], "keywords": [...]}
# result.moderation_status: "pending"
# result.launch_status: "scheduled"
```

**Пример 2: Создание ретаргетинговой кампании**
```python
result = await campaign_manager_agent.execute({
    "campaign_brief": {
        "goal": "conversions",
        "budget": 30000,
        "duration": 14,
        "target_audience": {
            "retargeting": "site_visitors_30_days",
            "geo": ["Россия"]
        },
        "services": ["кардиология консультация"]
    },
    "landing_pages": ["https://example.com/cardiology-promo"],
    "brand_guidelines": {...},
    "compliance_rules": {...}
})

# result.campaign_id: "87654321"
# result.campaign_structure: {"ad_groups": [...], "ads": [...], "targeting": {...}}
# result.moderation_status: "approved"
# result.launch_status: "active"
```

---

**Автор:** Mikhail Eliseev (via meAI Architect)  
**Статус:** ✅ Готов для deep-research
