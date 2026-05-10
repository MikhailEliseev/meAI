# Campaign Manager Agent - Спецификация

**Дата:** 2026-05-10  
**Magister:** Ads Magister  
**Приоритет:** P1  
**Статус:** Ready

---

## 🎯 РОЛЬ И НАЗНАЧЕНИЕ

### Основная роль:
Campaign Manager Agent — автоматизированный менеджер рекламных кампаний для медицинского маркетинга. Создаёт, запускает и управляет кампаниями в Яндекс.Директ и Google Ads, обеспечивая соответствие медицинским требованиям (152-ФЗ, Google Healthcare policy) и оптимальное распределение бюджета.

### Что делает:
- ✅ Создаёт рекламные кампании через API (Яндекс.Директ v5, Google Ads)
- ✅ Валидирует compliance (152-ФЗ, Google Healthcare policy) перед запуском
- ✅ Группирует ключевые слова в ad groups (10-15 keywords per group)
- ✅ Генерирует compliant ad copy с обязательными disclaimers
- ✅ Настраивает bidding strategies (Manual CPC, Target CPA, Maximize Conversions)
- ✅ Мониторит moderation status и обрабатывает rejections
- ✅ Связывает conversion goals (Яндекс.Метрика, Google Analytics)

### Что НЕ делает:
- ❌ Keyword research (делает Keyword Research Agent)
- ❌ Landing page creation (делает Landing Content Agent)
- ❌ Budget optimization (делает Budget Optimizer Agent)
- ❌ Performance monitoring (делает Performance Monitor Agent)
- ❌ Medical fact-checking (делает Medical Fact-Checker Agent)

### Место в иерархии:
```
Ads Magister
    ↓
Ads Orchestrator
    ↓
Campaign Manager Agent ← вы здесь
```

---

## 📥 ВХОДНЫЕ ДАННЫЕ

### Получает от Orchestrator:

**Формат события:**
```json
{
  "event_type": "subagent.task.assigned",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "campaign-manager",
  "payload": {
    "campaign_brief": {
      "goal": "leads",
      "budget": 50000,
      "duration": 30,
      "target_audience": {
        "geo": ["Москва", "Санкт-Петербург"],
        "age": "25-54",
        "interests": ["здоровье", "медицина"]
      },
      "services": ["кардиология консультация", "ЭКГ"]
    },
    "keywords": [
      {"keyword": "кардиолог консультация", "intent": "informational", "volume": 1200},
      {"keyword": "кардиолог запись", "intent": "transactional", "volume": 800}
    ],
    "landing_pages": ["https://example.com/cardiology"],
    "brand_guidelines": {
      "tone": "professional",
      "disclaimers": ["Лицензия №ЛО-77-01-012345", "Имеются противопоказания"]
    },
    "compliance_rules": {
      "prohibited_terms": ["гарантируем", "лучший", "100%"],
      "mandatory_disclaimers": true
    }
  }
}
```

**Обязательные параметры:**
- `campaign_brief` (object) - Бриф кампании от Ads Magister
  - `goal` (string) - Цель: "leads", "traffic", "brand_awareness"
  - `budget` (float) - Бюджет в рублях
  - `duration` (int) - Длительность в днях
  - `target_audience` (object) - Целевая аудитория (geo, age, interests)
  - `services` (array) - Услуги для продвижения
- `keywords` (array) - Ключевые слова от Keyword Research Agent
- `landing_pages` (array) - URL лендингов от Landing Content Agent

**Опциональные параметры:**
- `brand_guidelines` (object) - Бренд-гайды (tone, disclaimers)
- `compliance_rules` (object) - Правила compliance (prohibited_terms, mandatory_disclaimers)

---

## 📤 ВЫХОДНЫЕ ДАННЫЕ

### Отправляет Orchestrator:

**Формат события:**
```json
{
  "event_type": "subagent.task.completed",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "campaign-manager",
  "payload": {
    "status": "success",
    "result": {
      "campaign_id": "12345678",
      "platform": "yandex_direct",
      "campaign_structure": {
        "ad_groups": [
          {
            "id": "111",
            "name": "Cardiology Consultation - Informational",
            "keywords": ["кардиолог консультация", "кардиолог прием"],
            "ads": [{"id": "222", "headline": "Кардиолог в Москве", "description": "..."}]
          }
        ]
      },
      "moderation_status": "pending",
      "launch_status": "scheduled",
      "warnings": []
    },
    "metrics": {
      "execution_time_ms": 4500,
      "ad_groups_created": 3,
      "ads_created": 6,
      "keywords_added": 45,
      "compliance_score": 95
    },
    "errors": []
  }
}
```

**Структура результата:**
- `campaign_id` (string) - ID созданной кампании
- `platform` (string) - Платформа: "yandex_direct" или "google_ads"
- `campaign_structure` (object) - Структура кампании (ad_groups, ads, keywords)
- `moderation_status` (string) - Статус модерации: "pending", "approved", "rejected"
- `launch_status` (string) - Статус запуска: "scheduled", "active", "paused"
- `warnings` (array) - Предупреждения (если есть)

**Метрики:**
- `execution_time_ms` - Время выполнения (target: <300,000 ms = 5 min)
- `ad_groups_created` - Количество созданных ad groups
- `ads_created` - Количество созданных объявлений
- `keywords_added` - Количество добавленных ключевых слов
- `compliance_score` - Оценка compliance (0-100, target: ≥90)

---

## 🔄 АЛГОРИТМ РАБОТЫ

### Шаг 1: Валидация входных данных (30 сек)

**Действия:**
1. Проверить наличие обязательных параметров (campaign_brief, keywords, landing_pages)
2. Валидировать budget (≥1,000 RUB/day)
3. Валидировать duration (≥30 days для learning period)
4. Валидировать keywords (50-200 keywords recommended)
5. Проверить доступность landing pages (HTTP 200)

**Критерии успеха:**
- Все обязательные параметры присутствуют
- Budget ≥1,000 RUB/day
- Duration ≥30 days
- Keywords: 50-200 штук
- Landing pages доступны (HTTP 200)

**Обработка ошибок:**
- Если validation failed → вернуть `status: "failure"` с описанием ошибок
- Если warnings (например, budget <1,000 RUB/day) → продолжить с warnings


### Шаг 2: Compliance validation (60 сек)

**Действия:**
1. Сканировать ad copy на prohibited terms (гарантируем, лучший, 100%, излечение)
2. Проверить наличие mandatory disclaimers (противопоказания, лицензия)
3. Валидировать landing pages:
   - Medical license visible (regex: `Лицензия №?[А-Я]{2}-\d{2}-\d{2}-\d{6}`)
   - Contraindications disclaimer present
   - Fast load time (<3 seconds)
   - Mobile-responsive
4. Рассчитать compliance score (0-100)

**Критерии успеха:**
- Compliance score ≥90
- No prohibited terms in ad copy
- All mandatory disclaimers present
- Landing pages compliant

**Обработка ошибок:**
- Если compliance score <90 → блокировать submission, вернуть violations
- Если compliance score 90-100 → продолжить с warnings (если есть)

**Код:**
```python
def validate_compliance(ad_copy, landing_url):
    score = 100
    violations = []
    
    # Check prohibited terms
    prohibited = ["гарантируем", "лучший", "100%", "излечение"]
    for term in prohibited:
        if term in ad_copy.lower():
            score -= 20
            violations.append(f"Prohibited term: {term}")
    
    # Check disclaimer
    if "противопоказания" not in ad_copy.lower():
        score -= 10
        violations.append("Missing contraindications disclaimer")
    
    # Check landing page
    html = fetch_page(landing_url)
    if not re.search(r"Лицензия №?[А-Я]{2}-\d{2}-\d{2}-\d{6}", html):
        score -= 30
        violations.append("Medical license not visible")
    
    return {"score": max(0, score), "violations": violations}
```

### Шаг 3: Группировка ключевых слов (30 сек)

**Действия:**
1. Группировать keywords по intent (informational, transactional, emergency)
2. Создать ad groups (10-15 keywords per group, range: 5-20)
3. Назначить match types (phrase match по умолчанию)
4. Добавить negative keywords (free, cheap, DIY, home remedy)

**Критерии успеха:**
- Ad groups: 10-15 keywords each (optimal)
- All keywords assigned to ad groups
- Negative keywords added

**Обработка ошибок:**
- Если ad group >20 keywords → split into multiple groups
- Если ad group <5 keywords → merge with similar group

**Код:**
```python
def group_keywords(keywords):
    # Group by intent
    groups = {
        "informational": [],
        "transactional": [],
        "emergency": []
    }
    
    for kw in keywords:
        groups[kw["intent"]].append(kw)
    
    # Create ad groups (10-15 keywords each)
    ad_groups = []
    for intent, kws in groups.items():
        # Split into chunks of 10-15
        for i in range(0, len(kws), 12):
            chunk = kws[i:i+12]
            ad_groups.append({
                "name": f"{service} - {intent.capitalize()}",
                "keywords": chunk,
                "negative_keywords": ["free", "cheap", "DIY", "home remedy"]
            })
    
    return ad_groups
```

### Шаг 4: Генерация ad copy (60 сек)

**Действия:**
1. Для каждого ad group сгенерировать 2-3 объявления
2. Использовать compliant copywriting formulas (AIDA, PAS adapted)
3. Соблюдать character limits:
   - Яндекс: 30 chars headline, 81 chars description
   - Google: 30 chars headline (×3), 90 chars description (×2)
4. Добавить mandatory disclaimers
5. Добавить ad extensions (sitelinks, callouts, structured snippets)

**Критерии успеха:**
- 2-3 ads per ad group
- All ads compliant (no prohibited terms)
- Character limits respected
- Disclaimers present

**Обработка ошибок:**
- Если ad copy exceeds character limit → truncate or rephrase
- Если prohibited term detected → remove and regenerate

**Пример ad copy:**
```
Headline: "Кардиолог в Москве" (19 chars)
Description: "Консультация опытных кардиологов. ЭКГ, нагрузочные тесты. Лицензия ЛО-77-01-012345. Имеются противопоказания." (81 chars)

Sitelinks:
- "Записаться онлайн" → /booking
- "Наши врачи" → /doctors
- "Цены" → /pricing

Callouts:
- "Лицензированный медцентр"
- "Опыт 20+ лет"
- "Принимаем страховки"
```

### Шаг 5: Создание кампании через API (90 сек)

**Действия:**
1. Authenticate (Яндекс.Директ OAuth или Google Ads service account)
2. Create campaign (TEXT_CAMPAIGN для Яндекс, Search для Google)
3. Set bidding strategy (Manual CPC для новых кампаний)
4. Set budget and schedule
5. Link Метрика/Analytics counter
6. Create ad groups (batch operation, max 10 per batch)
7. Create ads (batch operation)
8. Add keywords (batch operation)
9. Add ad extensions

**Критерии успеха:**
- Campaign created (campaign_id returned)
- All ad groups created
- All ads created
- All keywords added
- API error rate <1%

**Обработка ошибок:**
- HTTP 429 (rate limit) → exponential backoff (1s, 2s, 4s, 8s)
- HTTP 500 (server error) → retry up to 3 times
- HTTP 400 (client error) → log and return failure

**Код (Яндекс.Директ):**
```python
async def create_campaign_yandex(campaign_data):
    # Step 1: Create campaign
    campaign = {
        "Name": campaign_data["name"],
        "StartDate": campaign_data["start_date"],
        "Type": "TEXT_CAMPAIGN",
        "TextCampaign": {
            "BiddingStrategy": {
                "Search": {"BiddingStrategyType": "HIGHEST_POSITION"},
                "Network": {"BiddingStrategyType": "SERVING_OFF"}
            },
            "Settings": [
                {"Option": "ADD_METRICA_TAG", "Value": "YES"},
                {"Option": "METRICA_COUNTER_ID", "Value": str(metrika_id)}
            ]
        }
    }
    
    response = await api.call("campaigns", "add", {"Campaigns": [campaign]})
    campaign_id = response["AddResults"][0]["Id"]
    
    # Step 2: Create ad groups (batch)
    ad_groups = [
        {
            "Name": group["name"],
            "CampaignId": campaign_id,
            "RegionIds": [213],  # Moscow
            "NegativeKeywords": group["negative_keywords"]
        }
        for group in campaign_data["ad_groups"]
    ]
    
    response = await api.call("adgroups", "add", {"AdGroups": ad_groups})
    ad_group_ids = [r["Id"] for r in response["AddResults"]]
    
    # Step 3: Create ads (batch)
    ads = []
    for i, group in enumerate(campaign_data["ad_groups"]):
        for ad in group["ads"]:
            ads.append({
                "AdGroupId": ad_group_ids[i],
                "TextAd": {
                    "Title": ad["headline"],
                    "Text": ad["description"],
                    "Href": campaign_data["landing_url"],
                    "Mobile": "NO"
                }
            })
    
    response = await api.call("ads", "add", {"Ads": ads})
    
    # Step 4: Add keywords (batch)
    keywords = []
    for i, group in enumerate(campaign_data["ad_groups"]):
        for kw in group["keywords"]:
            keywords.append({
                "AdGroupId": ad_group_ids[i],
                "Keyword": kw["keyword"],
                "Bid": 50000000,  # 50 RUB in micros
                "StrategyPriority": "NORMAL"
            })
    
    response = await api.call("keywords", "add", {"Keywords": keywords})
    
    return campaign_id
```

### Шаг 6: Мониторинг модерации (до 3 дней)

**Действия:**
1. Poll moderation status каждые 15 минут (во время business hours)
2. Отслеживать статус: DRAFT → MODERATION → ACCEPTED/REJECTED
3. Если REJECTED → получить rejection reasons
4. Если REJECTED → попытаться auto-fix (remove prohibited terms, add disclaimers)
5. Если auto-fix невозможен → alert human operator

**Критерии успеха:**
- Moderation status = ACCEPTED
- Moderation pass rate >90%
- Average approval time <3 days

**Обработка ошибок:**
- Если REJECTED и auto-fix failed → вернуть `status: "partial_success"` с rejection reasons
- Если moderation timeout (>5 days) → alert human operator

**Код:**
```python
async def monitor_moderation(campaign_id):
    max_attempts = 288  # 3 days × 24 hours × 4 checks/hour
    attempt = 0
    
    while attempt < max_attempts:
        status = await api.call("campaigns", "get", {
            "SelectionCriteria": {"Ids": [campaign_id]},
            "FieldNames": ["Id", "Status", "State"]
        })
        
        campaign_status = status["Campaigns"][0]["Status"]
        
        if campaign_status == "ACCEPTED":
            return {"status": "approved", "attempts": attempt}
        elif campaign_status == "REJECTED":
            reasons = await get_rejection_reasons(campaign_id)
            # Try auto-fix
            if can_auto_fix(reasons):
                await fix_and_resubmit(campaign_id, reasons)
            else:
                return {"status": "rejected", "reasons": reasons}
        
        # Wait 15 minutes
        await asyncio.sleep(900)
        attempt += 1
    
    return {"status": "timeout", "attempts": attempt}
```

### Шаг 7: Запуск кампании (10 сек)

**Действия:**
1. После moderation approval → set campaign status to ACTIVE
2. Verify campaign is running (impressions >0 within 1 hour)
3. Monitor first 24 hours (CTR, CPC, conversions)

**Критерии успеха:**
- Campaign status = ACTIVE
- Impressions >0 within 1 hour
- No critical errors

**Обработка ошибок:**
- Если impressions = 0 after 1 hour → increase bids by 20-30%
- Если CTR <1% after 24 hours → review ad copy

---

## 📊 МЕТРИКИ УСПЕХА

### Качество (Quality Metrics)

**Campaign Creation Success Rate:**
- **Target:** >95%
- **Calculation:** (Successful creations / Total attempts) × 100
- **Measurement:** Track per platform (Яндекс, Google)
- **Alert:** If <90%

**Moderation Pass Rate:**
- **Target:** >90%
- **Calculation:** (Approved campaigns / Total submitted) × 100
- **Measurement:** Track per platform and rejection reason
- **Alert:** If <85%

**Compliance Violations:**
- **Target:** 0
- **Measurement:** Account warnings, suspensions, policy violations
- **Alert:** Immediate on any violation

**Ad Relevance Score:**
- **Target:** >7/10 (Google Quality Score)
- **Measurement:** Track per ad group
- **Alert:** If <5/10

### Производительность (Performance Metrics)

**Time to Create Campaign:**
- **Target:** <5 minutes
- **Measurement:** Time from task received to campaign_id returned
- **Breakdown:**
  - Validation: 30s
  - Compliance: 60s
  - Grouping: 30s
  - Ad copy: 60s
  - API calls: 90s
  - Total: ~4.5 minutes
- **Alert:** If >10 minutes

**Time to Launch:**
- **Target:** <10 minutes (after moderation)
- **Measurement:** Time from moderation approval to campaign active
- **Alert:** If >30 minutes

**API Uptime:**
- **Target:** >99%
- **Measurement:** (Successful API calls / Total API calls) × 100
- **Alert:** If <98%

**API Error Rate:**
- **Target:** <1%
- **Measurement:** (API errors / Total API calls) × 100
- **Breakdown:** Track by error type (429, 500, 400)
- **Alert:** If >2%

### Стоимость (Cost Metrics)

**API Cost per Campaign:**
- **Target:** <100 RUB
- **Actual:** ~0 RUB (Яндекс and Google APIs free within limits)
- **Measurement:** Track API usage against limits

**Infrastructure Cost:**
- **Target:** <500 RUB/month per 100 campaigns
- **Actual:** ~50-100 RUB/month (server, database)

---

## 🔗 КОММУНИКАЦИЯ С ДРУГИМИ АГЕНТАМИ

### Получает данные от:

**1. Keyword Research Agent:**
- **Что получает:** Список ключевых слов с intent и volume
- **Формат:** `[{"keyword": "...", "intent": "...", "volume": 1200}]`
- **Когда:** Перед созданием кампании
- **Обработка:** Группирует keywords в ad groups (10-15 per group)

**2. Landing Content Agent:**
- **Что получает:** URL лендингов
- **Формат:** `["https://example.com/cardiology"]`
- **Когда:** Перед созданием кампании
- **Обработка:** Валидирует landing pages (license, disclaimer, load time)

**3. Medical Fact-Checker Agent:**
- **Что получает:** Validation результаты для ad copy
- **Формат:** `{"compliant": true, "violations": []}`
- **Когда:** После генерации ad copy, перед submission
- **Обработка:** Блокирует submission если violations detected

### Отправляет данные:

**1. Budget Optimizer Agent:**
- **Что отправляет:** Campaign structure и initial bids
- **Формат:** `{"campaign_id": "...", "ad_groups": [...], "initial_bids": {...}}`
- **Когда:** После создания кампании
- **Цель:** Для оптимизации бюджета и bids

**2. Performance Monitor Agent:**
- **Что отправляет:** Campaign ID для мониторинга
- **Формат:** `{"campaign_id": "...", "platform": "yandex_direct"}`
- **Когда:** После запуска кампании
- **Цель:** Для отслеживания performance (CTR, CPA, ROAS)

**3. Ads Orchestrator:**
- **Что отправляет:** Campaign creation result
- **Формат:** См. секцию "Выходные данные"
- **Когда:** После завершения задачи (success/failure)

---

## ⚠️ ОБРАБОТКА ОШИБОК

### Типы ошибок:

**1. Validation Errors (Client-side):**
- **Причины:** Missing parameters, invalid budget, invalid duration
- **Обработка:** Return `status: "failure"` с описанием ошибок
- **Retry:** No (требуется исправление входных данных)
- **Alert:** Log warning, не требует human intervention

**2. Compliance Errors:**
- **Причины:** Prohibited terms, missing disclaimers, landing page issues
- **Обработка:** Block submission, return violations
- **Retry:** After auto-fix (remove prohibited terms, add disclaimers)
- **Alert:** If auto-fix failed → alert human operator

**3. API Errors:**

**HTTP 429 (Rate Limit):**
- **Причина:** Exceeding 5 concurrent requests (Яндекс)
- **Обработка:** Exponential backoff (1s, 2s, 4s, 8s)
- **Retry:** Yes, up to 5 attempts
- **Alert:** If >5 rate limit errors in 1 hour

**HTTP 500 (Server Error):**
- **Причина:** Platform server issues
- **Обработка:** Retry up to 3 times with 5-second delay
- **Retry:** Yes, up to 3 attempts
- **Alert:** If all retries failed

**HTTP 400 (Client Error):**
- **Причина:** Invalid request (malformed data, missing fields)
- **Обработка:** Log error details, return failure
- **Retry:** No (требуется исправление request)
- **Alert:** Immediate (indicates bug in code)

**4. Moderation Errors:**
- **Причины:** Prohibited claims, missing license, landing page issues
- **Обработка:** Try auto-fix (remove terms, add disclaimers), resubmit
- **Retry:** Yes, up to 2 attempts
- **Alert:** If auto-fix failed or 2nd rejection → alert human operator

### Retry Strategy:

```python
async def api_call_with_retry(method, params, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await api.call(method, params)
        except HTTP429Error:
            # Exponential backoff
            await asyncio.sleep(2 ** attempt)
        except HTTP500Error:
            # Fixed delay
            await asyncio.sleep(5)
        except HTTP400Error:
            # No retry for client errors
            raise
    
    raise MaxRetriesExceededError(f"Failed after {max_retries} attempts")
```

---

## 🧪 ТЕСТИРОВАНИЕ

### Unit Tests:

**1. Validation Logic:**
```python
def test_validate_campaign_brief():
    # Valid brief
    brief = {"goal": "leads", "budget": 50000, "duration": 30}
    assert validate_brief(brief) == {"valid": True, "errors": []}
    
    # Invalid budget
    brief = {"goal": "leads", "budget": 500, "duration": 30}
    result = validate_brief(brief)
    assert result["valid"] == False
    assert "budget" in result["errors"][0]
```

**2. Compliance Validation:**
```python
def test_compliance_validation():
    # Compliant ad copy
    ad_copy = "Кардиолог в Москве. Консультация опытных врачей. Лицензия ЛО-77-01-012345. Имеются противопоказания."
    result = validate_compliance(ad_copy, "https://example.com")
    assert result["score"] >= 90
    
    # Non-compliant (prohibited term)
    ad_copy = "Лучший кардиолог в Москве. Гарантируем излечение."
    result = validate_compliance(ad_copy, "https://example.com")
    assert result["score"] < 90
    assert len(result["violations"]) > 0
```

**3. Keyword Grouping:**
```python
def test_keyword_grouping():
    keywords = [
        {"keyword": "кардиолог консультация", "intent": "informational"},
        {"keyword": "кардиолог запись", "intent": "transactional"}
    ]
    groups = group_keywords(keywords)
    
    # Check ad group size (10-15 keywords)
    for group in groups:
        assert 5 <= len(group["keywords"]) <= 20
```

### Integration Tests:

**1. End-to-End Campaign Creation:**
```python
async def test_create_campaign_e2e():
    # Prepare test data
    campaign_data = {
        "campaign_brief": {...},
        "keywords": [...],
        "landing_pages": [...]
    }
    
    # Execute
    result = await campaign_manager.execute(campaign_data)
    
    # Verify
    assert result["status"] == "success"
    assert result["campaign_id"] is not None
    assert result["metrics"]["compliance_score"] >= 90
    
    # Cleanup
    await delete_test_campaign(result["campaign_id"])
```

**2. API Integration:**
```python
async def test_yandex_api_integration():
    # Test authentication
    assert await yandex_api.authenticate() == True
    
    # Test campaign creation
    campaign = {"Name": "Test Campaign", ...}
    response = await yandex_api.call("campaigns", "add", {"Campaigns": [campaign]})
    assert "AddResults" in response
    assert response["AddResults"][0]["Id"] is not None
```

### Manual Testing Checklist:

✅ **Pre-Launch:**
- [ ] Create test campaign with valid data
- [ ] Verify compliance validation (test prohibited terms)
- [ ] Verify landing page validation (test missing license)
- [ ] Verify keyword grouping (check ad group sizes)
- [ ] Verify ad copy generation (check character limits)

✅ **Launch:**
- [ ] Submit campaign to platform
- [ ] Monitor moderation status
- [ ] Verify campaign approved
- [ ] Verify campaign active (impressions >0)

✅ **Post-Launch:**
- [ ] Monitor first 24 hours (CTR, CPC)
- [ ] Verify conversion tracking working
- [ ] Check for policy violations

---

## 📦 ЗАВИСИМОСТИ

### Внешние API:

**1. Яндекс.Директ API v5:**
- **URL:** https://api.direct.yandex.com/json/v5/
- **Authentication:** OAuth 2.0 (access token)
- **Rate Limits:** 5 concurrent requests, points-based daily limit
- **Cost:** Free (within limits)
- **Documentation:** https://yandex.ru/dev/direct/doc/

**2. Google Ads API:**
- **URL:** https://googleads.googleapis.com/
- **Authentication:** Service account (OAuth 2.0)
- **Rate Limits:** 15,000 operations/day (standard access)
- **Cost:** Free (within limits)
- **Documentation:** https://developers.google.com/google-ads/api/docs/

**3. Яндекс.Метрика API:**
- **URL:** https://api-metrika.yandex.net/
- **Purpose:** Conversion goal setup
- **Authentication:** OAuth 2.0
- **Cost:** Free

**4. Google Analytics API:**
- **URL:** https://analyticsreporting.googleapis.com/
- **Purpose:** Conversion goal setup
- **Authentication:** Service account
- **Cost:** Free

### Python Libraries:

```python
# requirements.txt
aiohttp==3.9.1          # Async HTTP client
pydantic==2.5.0         # Data validation
sqlalchemy==2.0.23      # Database ORM
asyncio==3.4.3          # Async operations
python-dotenv==1.0.0    # Environment variables
```

### Internal Dependencies:

- **Event Bus:** Для получения задач и отправки результатов
- **Database:** Для хранения campaign metadata
- **Obsidian Vault:** Для логирования операций

---

## 🚀 DEPLOYMENT

### Environment Variables:

```bash
# Яндекс.Директ
YANDEX_DIRECT_ACCESS_TOKEN=your_token_here
YANDEX_DIRECT_CLIENT_LOGIN=your_login_here

# Google Ads
GOOGLE_ADS_DEVELOPER_TOKEN=your_token_here
GOOGLE_ADS_CLIENT_ID=your_client_id_here
GOOGLE_ADS_CLIENT_SECRET=your_secret_here
GOOGLE_ADS_REFRESH_TOKEN=your_refresh_token_here

# Метрика / Analytics
YANDEX_METRIKA_ACCESS_TOKEN=your_token_here
GOOGLE_ANALYTICS_SERVICE_ACCOUNT=path/to/service_account.json

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/campaigns.db

# Event Bus
EVENT_BUS_URL=redis://localhost:6379
```

### Docker Deployment:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY .env .

CMD ["python", "-m", "src.aim.subagents.campaign_manager"]
```

### Health Checks:

```python
async def health_check():
    checks = {
        "yandex_api": await yandex_api.ping(),
        "google_api": await google_api.ping(),
        "database": await db.ping(),
        "event_bus": await event_bus.ping()
    }
    
    all_healthy = all(checks.values())
    return {"healthy": all_healthy, "checks": checks}
```

---

## 📝 CHANGELOG

### v1.0.0 (2026-05-10)
- ✅ Initial specification created
- ✅ Based on deep-research findings (Campaign_Management_Medical_Ads_Research_20260510)
- ✅ Яндекс.Директ API v5 integration specified
- ✅ Google Ads API integration specified
- ✅ Compliance validation (152-ФЗ, Google Healthcare policy)
- ✅ Campaign structure (10-15 keywords per ad group)
- ✅ Bidding strategies (Manual CPC, Target CPA, Maximize Conversions)
- ✅ Moderation monitoring
- ✅ Error handling and retry logic

---

## 📚 TODO

### P0 (Critical):
- [ ] Implement Яндекс.Директ API integration
- [ ] Implement Google Ads API integration
- [ ] Implement compliance validation engine
- [ ] Implement keyword grouping logic
- [ ] Implement ad copy generation

### P1 (High):
- [ ] Implement moderation monitoring
- [ ] Implement error handling and retry logic
- [ ] Add unit tests (validation, compliance, grouping)
- [ ] Add integration tests (API, end-to-end)

### P2 (Medium):
- [ ] Implement batch operations optimization
- [ ] Add performance monitoring
- [ ] Add automated bid adjustments
- [ ] Implement A/B testing for ad copy

### P3 (Low):
- [ ] Add support for Dynamic Search Ads (DSA)
- [ ] Add support for Shopping campaigns
- [ ] Add support for Video campaigns

---

## 📖 ПРИЛОЖЕНИЕ A: ИССЛЕДОВАНИЕ

**Источник:** Campaign Management for Medical Marketing Ads Research (2026-05-10)

**Ключевые находки:**

1. **Яндекс.Директ API v5:**
   - Max 5 concurrent requests [c002]
   - Batch operations: max 10 campaigns [c007]
   - Points-based rate limiting
   - Manual moderation for medical ads (1-3 days)

2. **Google Ads API:**
   - Healthcare certification mandatory [c005]
   - Smart Bidding requires 15+ conversions/month [c001]
   - Moderation: 1-3 days initial, 24-48 hours re-review [c010]
   - 7-day warning before suspension [c005]

3. **Medical Compliance:**
   - 152-ФЗ: No guarantees, no superlatives, mandatory disclaimers [c003]
   - Google Healthcare: Certification, restricted content, 7-day warning
   - Prohibited: "гарантируем", "лучший", "100%", "cure", "best"
   - Mandatory: License number, contraindications disclaimer

4. **Campaign Structure:**
   - Optimal ad group size: 10-15 keywords [c004]
   - Match type mirroring within ad groups [c009]
   - Negative keywords critical [c008] (free, cheap, DIY)

5. **Bidding Strategies:**
   - Manual CPC: Start here (2-4 weeks)
   - Target CPA: Stable costs [c001], 15+ conversions/month
   - Maximize Conversions: Volume focus [c006]

**Полный отчёт:** `~/Documents/Campaign_Management_Medical_Ads_Research_20260510/`

---

**Автор:** Mikhail Eliseev (via meAI Architect)  
**Дата создания:** 2026-05-10  
**Статус:** ✅ Ready for implementation

