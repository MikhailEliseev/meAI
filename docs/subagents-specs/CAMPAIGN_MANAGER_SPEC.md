# Campaign Manager Agent - Спецификация

**Дата:** 2026-05-10  
**Magister:** Ads Magister  
**Приоритет:** P1  
**Статус:** Ready for Implementation

---

## 🎯 РОЛЬ И НАЗНАЧЕНИЕ

### Основная роль:
Campaign Manager Agent — автоматизированный менеджер рекламных кампаний для медицинского маркетинга с фокусом на **оптимальную структуру кампаний** для максимального Quality Score. Создаёт кампании на 5 платформах (Яндекс.Директ, VK Ads, myTarget, Telegram Ads, Дзен) с автоматической compliance validation и полным циклом модерации.

**Ключевой принцип:** Quality over Speed — качество структуры кампании важнее скорости создания.

### Что делает:
- ✅ Создаёт оптимальную структуру кампаний (Campaign → AdGroup → Ad → Keyword)
- ✅ Группирует ключевые слова по intent и услуге (10-15 keywords per ad group)
- ✅ Обеспечивает Quality Score 7-10 через релевантность объявлений
- ✅ Автоматически валидирует и корректирует compliance (152-ФЗ РФ)
- ✅ Мониторит модерацию (каждые 15 минут, timeout 1-3 дня)
- ✅ Обрабатывает отклонения модерации (анализ → исправление → повторная отправка)
- ✅ Поддерживает 5 платформ с приоритетами (P0: Яндекс.Директ, P1: VK Ads, P2: остальные)

### Что НЕ делает:
- ❌ Keyword research (делает Keyword Research Agent)
- ❌ Landing page creation (делает Landing Content Agent)
- ❌ Budget optimization (делает Budget Optimizer Agent)
- ❌ Performance monitoring (делает Performance Monitor Agent)

### Место в иерархии:
```
Ads Magister
    ↓
Campaign Manager Agent ← вы здесь
    ↓
[Keyword Research Agent, Landing Content Agent] → входные данные
[Budget Optimizer Agent, Performance Monitor Agent] → выходные данные
```

### Уникальная ценность:
- **Оптимальная структура:** 10-15 keywords per ad group для Quality Score 7-10
- **Compliance automation:** Автоматическая валидация + коррекция 152-ФЗ
- **Полный цикл модерации:** Мониторинг каждые 15 минут + автообработка отклонений
- **Multi-platform:** 5 платформ с единым интерфейсом

---

## 📥 ВХОДНЫЕ ДАННЫЕ

### Получает от других агентов:

**От Keyword Research Agent:**
```json
{
  "keywords": [
    {
      "keyword": "лечение зубов москва",
      "frequency": 1500,
      "competition": "medium",
      "cpc": 120,
      "intent": "transactional"
    },
    {
      "keyword": "стоматология цены",
      "frequency": 800,
      "competition": "high",
      "cpc": 150,
      "intent": "commercial"
    }
  ]
}
```

**От Landing Content Agent:**
```json
{
  "landing_pages": [
    {
      "url": "https://example.com/services/teeth-treatment",
      "title": "Лечение зубов в Москве",
      "description": "Профессиональное лечение зубов без боли",
      "usp": "Гарантия 2 года, современное оборудование",
      "license": "Лицензия №ЛО-77-01-012345"
    }
  ]
}
```

**Формат события (Event Bus):**
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
      "platforms": ["yandex_direct", "vk_ads"],
      "target_audience": {
        "geo": ["Москва", "Санкт-Петербург"],
        "age": "25-54",
        "interests": ["здоровье", "медицина"]
      },
      "services": ["лечение зубов", "имплантация"]
    },
    "keywords": [...],
    "landing_pages": [...],
    "compliance_rules": {
      "prohibited_terms": ["гарантируем", "лучший", "100%", "излечение"],
      "mandatory_disclaimers": ["Имеются противопоказания", "Лицензия №..."]
    }
  }
}
```

**Обязательные параметры:**
- `campaign_brief.goal` (string) - Цель: "leads", "traffic", "brand_awareness"
- `campaign_brief.budget` (float) - Бюджет в рублях (≥1,000 RUB/day)
- `campaign_brief.duration` (int) - Длительность в днях (≥30 для learning period)
- `campaign_brief.platforms` (array) - Платформы: ["yandex_direct", "vk_ads", "mytarget", "telegram_ads", "dzen"]
- `keywords` (array) - Ключевые слова с метриками (50-200 recommended)
- `landing_pages` (array) - URL посадочных страниц

**Опциональные параметры:**
- `compliance_rules` (object) - Правила compliance (по умолчанию: 152-ФЗ РФ)
- `bidding_strategy` (string) - Стратегия ставок (по умолчанию: "manual_cpc")

---

## 📤 ВЫХОДНЫЕ ДАННЫЕ

### Отправляет через Event Bus:

**Формат события (успех):**
```json
{
  "event_type": "subagent.task.completed",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "campaign-manager",
  "payload": {
    "status": "success",
    "result": {
      "campaign_id": "12345",
      "platform": "yandex_direct",
      "status": "moderation_pending",
      "structure": {
        "ad_groups": 5,
        "ads": 15,
        "keywords": 75
      },
      "quality_score": 8.5,
      "compliance_status": "validated",
      "moderation_status": "pending",
      "campaign_url": "https://direct.yandex.ru/campaigns/12345"
    },
    "metrics": {
      "execution_time_ms": 25000,
      "ad_groups_created": 5,
      "ads_created": 15,
      "keywords_added": 75,
      "compliance_score": 95,
      "quality_score_avg": 8.5
    }
  }
}
```

**Формат события (ошибка):**
```json
{
  "event_type": "subagent.task.failed",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "campaign-manager",
  "payload": {
    "status": "failure",
    "error": {
      "code": "COMPLIANCE_VIOLATION",
      "message": "Ad copy contains prohibited term: 'гарантируем'",
      "details": {
        "violations": [
          {
            "type": "prohibited_term",
            "term": "гарантируем",
            "location": "ad_group_1.ad_2.headline"
          }
        ]
      }
    }
  }
}
```

**Структура результата:**
- `campaign_id` (string) - ID созданной кампании
- `platform` (string) - Платформа
- `status` (string) - Статус: "moderation_pending", "active", "paused"
- `structure` (object) - Структура кампании (ad_groups, ads, keywords count)
- `quality_score` (float) - Средний Quality Score (target: 7-10)
- `compliance_status` (string) - Статус compliance: "validated", "violations_found"
- `moderation_status` (string) - Статус модерации: "pending", "approved", "rejected"

---

## 🔄 АЛГОРИТМ РАБОТЫ

### Шаг 1: Валидация входных данных (30 сек)

**Действия:**
1. Проверить наличие обязательных параметров
2. Валидировать budget (≥1,000 RUB/day)
3. Валидировать duration (≥30 days для learning period)
4. Валидировать keywords (50-200 recommended)
5. Проверить доступность landing pages (HTTP 200)

**Критерии успеха:**
- Все обязательные параметры присутствуют
- Budget ≥1,000 RUB/day
- Duration ≥30 days
- Keywords: 50-200 штук
- Landing pages доступны

**Обработка ошибок:**
- Если validation failed → вернуть `status: "failure"` с описанием ошибок
- Если warnings → продолжить с warnings в результате


### Шаг 2: Группировка ключевых слов (2 мин)

**Действия:**
1. Группировать keywords по intent:
   - **Informational** (как, что такое, симптомы) → отдельная ad group
   - **Commercial** (цены, стоимость, отзывы) → отдельная ad group
   - **Transactional** (запись, консультация, купить) → отдельная ad group
2. Группировать по услуге (если несколько услуг)
3. Оптимизировать размер групп: 10-15 keywords per ad group
4. Назначить match types:
   - Broad match для discovery (20% keywords)
   - Phrase match для основного трафика (60% keywords)
   - Exact match для high-intent (20% keywords)

**Критерии успеха:**
- Ad groups: 3-10 групп
- Keywords per ad group: 10-15 (оптимально для Quality Score)
- Match types распределены: 20% broad, 60% phrase, 20% exact

**Обработка ошибок:**
- Если keywords <50 → warning "Недостаточно ключевых слов для оптимальной структуры"
- Если ad groups >10 → warning "Слишком много групп, рекомендуется объединить"

**Пример группировки:**
```python
# Ad Group 1: Informational
keywords = [
    "кардиолог что лечит",
    "симптомы сердечной недостаточности",
    "как проверить сердце"
]

# Ad Group 2: Commercial
keywords = [
    "кардиолог цены москва",
    "стоимость консультации кардиолога",
    "кардиолог отзывы"
]

# Ad Group 3: Transactional
keywords = [
    "кардиолог запись онлайн",
    "записаться к кардиологу москва",
    "консультация кардиолога"
]
```

### Шаг 3: Compliance validation и auto-correction (2 мин)

**Действия:**
1. Сканировать ad copy на prohibited terms (152-ФЗ РФ):
   - "гарантируем", "гарантия результата"
   - "лучший", "самый эффективный"
   - "100%", "полностью излечим"
   - "без противопоказаний"
2. Проверить наличие mandatory disclaimers:
   - "Имеются противопоказания. Необходима консультация специалиста."
   - "Лицензия №ЛО-77-01-012345"
3. **Auto-correction** (если violations found):
   - Заменить prohibited terms на compliant alternatives
   - Добавить mandatory disclaimers в description
4. Валидировать landing pages:
   - Medical license visible (regex: `Лицензия №?[А-Я]{2}-\d{2}-\d{2}-\d{6}`)
   - Contraindications disclaimer present
   - Fast load time (<3 seconds)
5. Рассчитать compliance score (0-100)

**Критерии успеха:**
- Compliance score ≥90
- No prohibited terms in ad copy (после auto-correction)
- All mandatory disclaimers present
- Landing pages compliant

**Обработка ошибок:**
- Если compliance score <90 после auto-correction → блокировать submission, вернуть violations
- Если landing page не compliant → warning, но продолжить (ответственность Landing Content Agent)

**Пример auto-correction:**
```python
# Before
headline = "Лучший кардиолог в Москве. Гарантируем результат!"

# After auto-correction
headline = "Опытный кардиолог в Москве. Современные методы лечения"
description = "Профессиональная консультация кардиолога. Имеются противопоказания. Необходима консультация специалиста. Лицензия №ЛО-77-01-012345"
```

### Шаг 4: Генерация ad copy (3 мин)

**Действия:**
1. Для каждой ad group создать 2-3 объявления (A/B testing)
2. Генерировать headlines:
   - Включить keyword из группы (для релевантности)
   - Длина: 30 символов (Яндекс.Директ), 30 chars (Google Ads)
   - Использовать dynamic keyword insertion: `{KeyWord}`
3. Генерировать descriptions:
   - Включить УТП из landing page
   - Добавить mandatory disclaimers
   - Длина: 81 символ (Яндекс.Директ), 90 chars (Google Ads)
4. Добавить call-to-action:
   - "Записаться онлайн", "Получить консультацию", "Узнать цены"

**Критерии успеха:**
- 2-3 ads per ad group
- Headlines содержат keywords
- Descriptions содержат УТП + disclaimers
- CTA присутствует

**Обработка ошибок:**
- Если headline >30 символов → обрезать и добавить "..."
- Если description >81 символ → обрезать disclaimers до минимума

**Пример ad copy:**
```json
{
  "ad_group": "Cardiology Consultation - Transactional",
  "ads": [
    {
      "headline": "Кардиолог в Москве - Запись",
      "description": "Консультация опытного кардиолога. Современное оборудование. Имеются противопоказания. Лицензия №ЛО-77-01-012345",
      "cta": "Записаться онлайн",
      "url": "https://example.com/cardiology"
    },
    {
      "headline": "{KeyWord} - Консультация",
      "description": "Профессиональная диагностика сердца. Без очередей. Имеются противопоказания. Лицензия №ЛО-77-01-012345",
      "cta": "Получить консультацию",
      "url": "https://example.com/cardiology"
    }
  ]
}
```

### Шаг 5: Создание кампании через API (5 мин)

**Действия:**
1. Выбрать платформу из `campaign_brief.platforms`
2. Получить credentials из storage (OAuth2 tokens)
3. Создать campaign через API:
   - **Яндекс.Директ API v5:** `campaigns.add` (max 5 concurrent requests, batch max 10 campaigns)
   - **VK Ads API:** `ads.createCampaigns`
   - **myTarget API:** `campaigns.create` (rate limit: 1-200 req/hour)
   - **Telegram Ads API:** `createCampaign`
   - **Дзен API:** `campaigns.create`
4. Создать ad groups через API
5. Создать ads через API
6. Добавить keywords через API
7. Настроить bidding strategy:
   - **Manual CPC** (по умолчанию для новых кампаний)
   - **Target CPA** (если ≥15 conversions за последние 30 дней)
   - **Maximize Conversions** (если budget позволяет)
8. Связать conversion goals (Яндекс.Метрика, Google Analytics)

**Критерии успеха:**
- Campaign created (HTTP 200, campaign_id returned)
- Ad groups created (HTTP 200)
- Ads created (HTTP 200)
- Keywords added (HTTP 200)
- Bidding strategy set
- Conversion goals linked

**Обработка ошибок:**
- Если API error → retry 3 times с exponential backoff (1s, 2s, 4s)
- Если rate limit → wait и retry
- Если authentication error → вернуть `status: "failure"` с описанием

**Пример API call (Яндекс.Директ):**
```python
import requests

headers = {
    "Authorization": f"Bearer {access_token}",
    "Accept-Language": "ru",
    "Content-Type": "application/json; charset=utf-8",
    "Client-Login": client_login  # для агентских аккаунтов
}

body = {
    "method": "add",
    "params": {
        "Campaigns": [
            {
                "Name": "Cardiology - Moscow",
                "StartDate": "2026-05-11",
                "Type": "TEXT_CAMPAIGN",
                "TextCampaign": {
                    "BiddingStrategy": {
                        "Search": {
                            "BiddingStrategyType": "HIGHEST_POSITION"
                        },
                        "Network": {
                            "BiddingStrategyType": "SERVING_OFF"
                        }
                    },
                    "Settings": [
                        {
                            "Option": "ADD_METRICA_TAG",
                            "Value": "YES"
                        }
                    ]
                }
            }
        ]
    }
}

response = requests.post(
    "https://api.direct.yandex.com/json/v5/campaigns",
    json=body,
    headers=headers,
    timeout=30
)
```

### Шаг 6: Мониторинг модерации (до 3 дней)

**Действия:**
1. Запустить мониторинг moderation status (каждые 15 минут)
2. Проверять статус через API:
   - **Яндекс.Директ:** `campaigns.get` → `State`, `Status`
   - **VK Ads:** `ads.getCampaigns` → `status`
   - **myTarget:** `campaigns.get` → `status`
3. Обрабатывать статусы:
   - **pending** → продолжить мониторинг
   - **approved** → вернуть `status: "success"`, `moderation_status: "approved"`
   - **rejected** → перейти к Шагу 7 (обработка отклонений)
4. Timeout: 3 дня (72 часа)
   - Если moderation pending >3 дней → вернуть warning, но считать успехом

**Критерии успеха:**
- Moderation approved в течение 3 дней
- Или timeout 3 дня (считается успехом с warning)

**Обработка ошибок:**
- Если moderation rejected → перейти к Шагу 7

**Пример мониторинга:**
```python
import asyncio

async def monitor_moderation(campaign_id: str, platform: str, timeout_hours: int = 72):
    start_time = time.time()
    check_interval = 15 * 60  # 15 минут
    
    while True:
        status = await check_moderation_status(campaign_id, platform)
        
        if status == "approved":
            return {"status": "approved", "time_elapsed": time.time() - start_time}
        
        if status == "rejected":
            return {"status": "rejected", "time_elapsed": time.time() - start_time}
        
        if time.time() - start_time > timeout_hours * 3600:
            return {"status": "timeout", "time_elapsed": time.time() - start_time}
        
        await asyncio.sleep(check_interval)
```

### Шаг 7: Обработка отклонений модерации (30 мин)

**Действия:**
1. Получить rejection reasons через API
2. Анализировать причины:
   - **Compliance violations** (152-ФЗ) → исправить ad copy
   - **Policy violations** (платформа) → исправить согласно policy
   - **Technical issues** (broken links, etc.) → исправить технические проблемы
3. Исправить нарушения:
   - Обновить ad copy через API
   - Обновить landing page URL (если нужно)
   - Обновить keywords (если нужно)
4. Повторно отправить на модерацию
5. Вернуться к Шагу 6 (мониторинг)

**Критерии успеха:**
- Rejection reasons проанализированы
- Нарушения исправлены
- Кампания повторно отправлена на модерацию

**Обработка ошибок:**
- Если rejection reasons неясны → вернуть `status: "failure"` с описанием
- Если исправление невозможно → вернуть `status: "failure"` с рекомендациями

**Пример обработки rejection:**
```python
rejection_reasons = [
    {
        "type": "PROHIBITED_CONTENT",
        "message": "Ad contains prohibited medical claim",
        "location": "ad_group_1.ad_2.description"
    }
]

# Исправление
for reason in rejection_reasons:
    if reason["type"] == "PROHIBITED_CONTENT":
        # Удалить prohibited content
        ad_copy = remove_prohibited_terms(ad_copy)
        # Добавить disclaimers
        ad_copy = add_mandatory_disclaimers(ad_copy)
        # Обновить через API
        await update_ad(ad_id, ad_copy)
```

---

## 🔗 ИНТЕГРАЦИИ

### Внешние API

**1. Яндекс.Директ API v5 (P0 - основная платформа)**
- **Endpoint:** `https://api.direct.yandex.com/json/v5/`
- **Authentication:** OAuth2 (Authorization Code Grant)
- **Rate limits:** Max 5 concurrent requests, batch max 10 campaigns
- **Methods:**
  - `campaigns.add` - Создание кампании
  - `adgroups.add` - Создание групп объявлений
  - `ads.add` - Создание объявлений
  - `keywords.add` - Добавление ключевых слов
  - `campaigns.get` - Получение статуса модерации
- **Pricing:** Бесплатно (платформа берёт комиссию с рекламного бюджета)
- **Documentation:** https://yandex.ru/dev/direct/doc/dg/concepts/about.html

**2. VK Ads API (P1 - полная поддержка)**
- **Endpoint:** `https://ads.vk.com/api/v2/`
- **Authentication:** OAuth2 (Client Credentials Grant)
- **Rate limits:** 3 requests/second
- **Methods:**
  - `ads.createCampaigns` - Создание кампании
  - `ads.createAds` - Создание объявлений
  - `ads.getCampaigns` - Получение статуса
- **Pricing:** Бесплатно
- **Documentation:** https://dev.vk.com/ru/api/ads

**3. myTarget API (P2 - базовая поддержка)**
- **Endpoint:** `https://target.my.com/api/v2/`
- **Authentication:** OAuth2
- **Rate limits:** 1-200 requests/hour (зависит от метода)
- **Methods:**
  - `campaigns.create` - Создание кампании
  - `banners.create` - Создание баннеров
- **Pricing:** Бесплатно
- **Documentation:** https://target.my.com/doc/api/

**4. Telegram Ads API (P2 - базовая поддержка)**
- **Endpoint:** `https://ads.telegram.org/api/`
- **Authentication:** API Token
- **Rate limits:** 100 requests/minute
- **Methods:**
  - `createCampaign` - Создание кампании
  - `createAd` - Создание объявления
- **Pricing:** Бесплатно
- **Documentation:** https://core.telegram.org/ads

**5. Дзен API (P2 - базовая поддержка)**
- **Endpoint:** `https://dzen.ru/api/v1/`
- **Authentication:** OAuth2
- **Rate limits:** 10 requests/second
- **Methods:**
  - `campaigns.create` - Создание кампании
  - `ads.create` - Создание объявления
- **Pricing:** Бесплатно
- **Documentation:** https://yandex.ru/dev/zen/doc/

### Связанные агенты

**Входные данные от:**
- **Keyword Research Agent** → keywords с метриками (frequency, competition, cpc, intent)
- **Landing Content Agent** → landing pages с URL, title, description, УТП, license

**Выходные данные для:**
- **Budget Optimizer Agent** → campaign_id, platform, structure для оптимизации бюджета
- **Performance Monitor Agent** → campaign_id, platform для мониторинга метрик

---

## 📊 МЕТРИКИ УСПЕХА

### Качество структуры:
- **Quality Score:** 7-10 (target: ≥8.0)
  - Expected CTR: 40% веса
  - Ad Relevance: 30% веса
  - Landing Page Experience: 30% веса
- **Релевантность объявлений:** >90% (keywords в headlines)
- **Оптимальная группировка:** 10-15 keywords per ad group

### Модерация:
- **Moderation pass rate:** >90% (target: ≥95%)
- **Compliance violations:** 0 (после auto-correction)
- **Time to approval:** <3 дня (72 часа)
- **Rejection rate:** <10% (target: ≤5%)

### Эффективность:
- **Campaign creation time:** <30 минут (качество важнее скорости)
- **Cost per campaign:** <500 рублей (с учётом всех платформ)
- **API success rate:** >95% (retry на ошибках)

### Бенчмарки (из исследования):
- **Baseline rejection rate:** 15-22% (без pre-flight auditing)
- **Optimized rejection rate:** 4-6% (с pre-flight auditing)
- **Quality Score improvement:** +2-3 points (с оптимальной структурой)

---

## 🔧 ОБРАБОТКА ОШИБОК

### Типы ошибок:

**1. Validation errors (Шаг 1)**
- **Причина:** Некорректные входные данные
- **Обработка:** Вернуть `status: "failure"` с описанием ошибок
- **Retry:** Нет (требуется исправление входных данных)

**2. Compliance violations (Шаг 3)**
- **Причина:** Prohibited terms в ad copy
- **Обработка:** Auto-correction → если не помогло, вернуть `status: "failure"`
- **Retry:** Нет (требуется ручное исправление)

**3. API errors (Шаг 5)**
- **Причина:** API недоступен, rate limit, authentication error
- **Обработка:** Retry 3 times с exponential backoff (1s, 2s, 4s)
- **Retry:** Да (3 попытки)

**4. Moderation rejection (Шаг 7)**
- **Причина:** Policy violations, compliance violations
- **Обработка:** Анализ причин → исправление → повторная отправка
- **Retry:** Да (до 3 раз)

### Retry стратегия:

```python
import asyncio
from typing import Callable, Any

async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0
) -> Any:
    """Retry function with exponential backoff."""
    delay = initial_delay
    
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            
            await asyncio.sleep(delay)
            delay *= backoff_factor
```

### Logging:

```python
import logging

logger = logging.getLogger("campaign_manager")

# Логировать все ошибки
logger.error(f"API error: {error_message}", extra={
    "campaign_id": campaign_id,
    "platform": platform,
    "attempt": attempt,
    "error_code": error_code
})

# Логировать compliance violations
logger.warning(f"Compliance violation: {violation}", extra={
    "ad_group": ad_group_id,
    "ad": ad_id,
    "violation_type": violation_type
})
```

---

## 🧪 ТЕСТИРОВАНИЕ

### Unit тесты:

**1. Тест группировки ключевых слов:**
```python
def test_keyword_grouping():
    keywords = [
        {"keyword": "кардиолог что лечит", "intent": "informational"},
        {"keyword": "кардиолог цены", "intent": "commercial"},
        {"keyword": "кардиолог запись", "intent": "transactional"}
    ]
    
    groups = group_keywords_by_intent(keywords)
    
    assert len(groups) == 3
    assert groups["informational"][0]["keyword"] == "кардиолог что лечит"
    assert len(groups["transactional"]) == 1
```

**2. Тест compliance validation:**
```python
def test_compliance_validation():
    ad_copy = "Лучший кардиолог в Москве. Гарантируем результат!"
    
    violations = validate_compliance(ad_copy)
    
    assert len(violations) == 2
    assert violations[0]["term"] == "Лучший"
    assert violations[1]["term"] == "Гарантируем"
```

**3. Тест auto-correction:**
```python
def test_auto_correction():
    ad_copy = "Лучший кардиолог. Гарантируем результат!"
    
    corrected = auto_correct_compliance(ad_copy)
    
    assert "Лучший" not in corrected
    assert "Гарантируем" not in corrected
    assert "Имеются противопоказания" in corrected
```

### Integration тесты:

**1. Тест создания кампании (Яндекс.Директ):**
```python
async def test_create_campaign_yandex():
    campaign_brief = {
        "goal": "leads",
        "budget": 50000,
        "duration": 30,
        "platforms": ["yandex_direct"]
    }
    
    result = await campaign_manager.create_campaign(campaign_brief)
    
    assert result["status"] == "success"
    assert result["campaign_id"] is not None
    assert result["quality_score"] >= 7.0
```

**2. Тест модерации:**
```python
async def test_moderation_monitoring():
    campaign_id = "12345"
    
    status = await campaign_manager.monitor_moderation(campaign_id, timeout_hours=0.1)
    
    assert status["status"] in ["approved", "rejected", "timeout"]
```

### E2E тесты:

**Сценарий: Создание кампании от начала до конца**
```python
async def test_e2e_campaign_creation():
    # 1. Подготовить входные данные
    keywords = load_keywords_from_keyword_research_agent()
    landing_pages = load_landing_pages_from_landing_content_agent()
    
    # 2. Создать кампанию
    result = await campaign_manager.execute_task({
        "campaign_brief": {...},
        "keywords": keywords,
        "landing_pages": landing_pages
    })
    
    # 3. Проверить результат
    assert result["status"] == "success"
    assert result["quality_score"] >= 7.0
    assert result["compliance_score"] >= 90
    assert result["moderation_status"] in ["pending", "approved"]
```

---

## 🚀 DEPLOYMENT

### Docker контейнер:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Установить зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Скопировать код
COPY src/ ./src/
COPY config/ ./config/

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

# Запустить агента
CMD ["python", "-m", "src.campaign_manager"]
```

### Environment variables:

```bash
# API credentials
YANDEX_DIRECT_CLIENT_ID=xxx
YANDEX_DIRECT_CLIENT_SECRET=xxx
YANDEX_DIRECT_ACCESS_TOKEN=xxx
VK_ADS_ACCESS_TOKEN=xxx
MYTARGET_ACCESS_TOKEN=xxx
TELEGRAM_ADS_TOKEN=xxx
DZEN_ACCESS_TOKEN=xxx

# Configuration
CAMPAIGN_MANAGER_TIMEOUT=1800  # 30 минут
MODERATION_CHECK_INTERVAL=900  # 15 минут
MODERATION_TIMEOUT=259200      # 3 дня
COMPLIANCE_SCORE_THRESHOLD=90
QUALITY_SCORE_TARGET=8.0

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Health check:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "uptime": get_uptime(),
        "api_status": {
            "yandex_direct": await check_yandex_direct_api(),
            "vk_ads": await check_vk_ads_api()
        }
    }
```

---

## 📝 CHANGELOG

### Version 1.0.0 (2026-05-10)
- ✅ Создание кампаний на 5 платформах (Яндекс.Директ, VK Ads, myTarget, Telegram Ads, Дзен)
- ✅ Оптимальная группировка ключевых слов (10-15 per ad group)
- ✅ Compliance validation + auto-correction (152-ФЗ РФ)
- ✅ Мониторинг модерации (каждые 15 минут, timeout 3 дня)
- ✅ Обработка отклонений модерации (анализ → исправление → повторная отправка)
- ✅ Quality Score optimization (target: 7-10)

---

## 📋 TODO

### Высокий приоритет:
- [ ] Добавить поддержку Google Ads (требуется Healthcare certification)
- [ ] Реализовать A/B testing объявлений (автоматическое переключение на winner)
- [ ] Добавить dynamic keyword insertion для всех платформ
- [ ] Реализовать автоматическое обновление ставок на основе Quality Score

### Средний приоритет:
- [ ] Добавить поддержку расширений объявлений (sitelinks, callouts)
- [ ] Реализовать multi-language support (английский, немецкий)
- [ ] Добавить интеграцию с CRM для lead tracking
- [ ] Реализовать автоматическое создание negative keywords

### Низкий приоритет:
- [ ] Добавить поддержку видео объявлений (YouTube, VK Video)
- [ ] Реализовать автоматическое создание landing pages (интеграция с Landing Content Agent)
- [ ] Добавить ML-модель для предсказания Quality Score

---

## 📚 ПРИЛОЖЕНИЕ A: ИССЛЕДОВАНИЕ

### Источник:
Multi-Platform Campaign Management Research (2026-05-10)

### Ключевые находки:

**1. Оптимальная структура кампаний:**
- 10-15 keywords per ad group оптимально для Quality Score
- Quality Score components: Expected CTR (40%), Ad Relevance (30%), Landing Page Experience (30%)
- Match types: 20% broad, 60% phrase, 20% exact

**2. Compliance automation:**
- 152-ФЗ РФ: запрещены гарантии, превосходство, "лучший", "100%"
- Mandatory disclaimers: "Имеются противопоказания", "Лицензия №..."
- Pre-flight auditing снижает rejection rate с 15-22% до 4-6%

**3. Модерация:**
- Яндекс.Директ: 80% автоматическая модерация (5-30 мин), 20% ручная (24-48 часов)
- VK Ads: аналогично Яндекс.Директ
- myTarget: 1-3 дня на модерацию
- Мониторинг каждые 15 минут оптимален

**4. API rate limits:**
- Яндекс.Директ: max 5 concurrent requests, batch max 10 campaigns
- VK Ads: 3 requests/second
- myTarget: 1-200 requests/hour (зависит от метода)
- Telegram Ads: 100 requests/minute
- Дзен: 10 requests/second

**5. Bidding strategies:**
- Manual CPC: для новых кампаний (первые 30 дней)
- Target CPA: требуется ≥15 conversions за последние 30 дней
- Maximize Conversions: требуется достаточный budget
- Target ROAS: требуется ≥50 conversions

### Gaps в исследовании:
- Яндекс.Директ exact rate limits (указано "max 5 concurrent", но нет деталей)
- Telegram Ads API documentation (ограниченный доступ)
- Дзен API access (требуется партнёрский статус)

---

**Конец спецификации**
