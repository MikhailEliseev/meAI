# Budget Optimizer Agent - Спецификация

**Дата:** 2026-05-11  
**Magister:** Ads Magister  
**Приоритет:** P1  
**Статус:** Draft

---

## 🎯 РОЛЬ И НАЗНАЧЕНИЕ

### Основная роль:
Автономный агент для оптимизации бюджетов рекламных кампаний на основе данных о производительности. Анализирует метрики (ROI, CPA, конверсии), принимает решения об оптимальном распределении бюджета и автоматически применяет изменения на всех платформах.

### Что делает:
- ✅ Оптимизирует ставки (bid optimization) на основе производительности кампаний
- ✅ Распределяет бюджет между кампаниями (budget allocation) по ROI/конверсиям/LTV
- ✅ Контролирует равномерное расходование бюджета (budget pacing)
- ✅ Максимизирует ROI с учётом медицинской специфики (сезонность, LTV, geo)
- ✅ Автоматически применяет изменения на всех платформах (Яндекс.Директ, VK Ads, myTarget, Telegram Ads, Дзен)
- ✅ Адаптируется к изменениям производительности в реальном времени

### Что НЕ делает:
- ❌ Не создаёт новые кампании (это задача Campaign Manager Agent)
- ❌ Не анализирует конкурентов (это задача Competitive Intelligence Agent)
- ❌ Не генерирует креативы (это задача Content Magister)
- ❌ Не собирает метрики (это задача Performance Monitor Agent)

### Место в иерархии:
```
Ads Magister
    ↓
Ads Orchestrator
    ↓
Budget Optimizer Agent ← вы здесь
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
  "subagent_id": "budget-optimizer",
  "payload": {
    "account_id": "string",
    "platform": "yandex_direct" | "vk_ads" | "mytarget" | "telegram_ads" | "dzen",
    "campaigns": [
      {
        "campaign_id": "string",
        "name": "string",
        "status": "active" | "paused",
        "budget_daily": 1000.0,
        "strategy": "manual_cpc" | "target_cpa" | "maximize_conversions" | "target_roas",
        "metrics": {
          "spend": 5000.0,
          "clicks": 250,
          "conversions": 10,
          "cpa": 500.0,
          "roi": 25.0,
          "quality_score": 7.5
        }
      }
    ],
    "kpi": {
      "target_cpa": 600.0,
      "target_roi": 20.0,
      "target_drr": 5.0,
      "daily_budget": 10000.0
    },
    "optimization_mode": "bid_optimization" | "budget_allocation" | "budget_pacing" | "roi_optimization",
    "constraints": {
      "min_daily_budget": 300.0,
      "max_daily_budget": 50000.0,
      "max_step_up_pct": 20.0,
      "max_step_down_pct": 25.0
    }
  }
}
```

**Обязательные параметры:**
- `account_id` (string) - ID рекламного аккаунта
- `platform` (string) - Платформа (yandex_direct, vk_ads, mytarget, telegram_ads, dzen)
- `campaigns` (array) - Список кампаний с метриками
- `kpi` (object) - Целевые KPI
- `optimization_mode` (string) - Режим оптимизации

**Опциональные параметры:**
- `constraints` (object) - Ограничения оптимизации (по умолчанию: min=300, max=50000, step_up=20%, step_down=25%)

---

## 📤 ВЫХОДНЫЕ ДАННЫЕ

### Отправляет Orchestrator:

**Формат события:**
```json
{
  "event_type": "subagent.task.completed",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "budget-optimizer",
  "payload": {
    "status": "success" | "partial_success" | "failure",
    "result": {
      "optimization_actions": [
        {
          "campaign_id": "string",
          "action_type": "set_daily_budget" | "change_strategy" | "pause_campaign",
          "current_value": 1000.0,
          "new_value": 1200.0,
          "reason": "Scale profitable campaign (CPA 20% below target)",
          "expected_impact": {
            "roi_change": "+5%",
            "cpa_change": "-10%"
          }
        }
      ],
      "summary": {
        "total_campaigns": 10,
        "optimized_campaigns": 7,
        "paused_campaigns": 1,
        "budget_reallocated": 5000.0,
        "expected_roi_improvement": "+8%"
      }
    },
    "metrics": {
      "execution_time_ms": 2500,
      "campaigns_analyzed": 10,
      "actions_generated": 8
    },
    "errors": []
  }
}
```

**Структура результата:**
- `optimization_actions` (array) - Список действий для применения
- `summary` (object) - Сводка оптимизации
- `expected_impact` (object) - Ожидаемое влияние на метрики

**Метрики:**
- `execution_time_ms` - Время выполнения в миллисекундах
- `campaigns_analyzed` - Количество проанализированных кампаний
- `actions_generated` - Количество сгенерированных действий

---

## 🔄 АЛГОРИТМ РАБОТЫ

### Шаг 1: Получение задачи и валидация
1. Подписаться на события `subagent.task.assigned`
2. Фильтровать по `subagent_id == "budget-optimizer"`
3. Валидировать входные параметры:
   - Проверить наличие обязательных полей
   - Проверить корректность метрик (spend >= 0, clicks >= 0, etc.)
   - Проверить constraints (min < max, step_up > 0, etc.)
4. Если валидация не прошла → вернуть failure с описанием ошибки

### Шаг 2: Анализ производительности кампаний
1. **Рассчитать эффективность каждой кампании:**
   ```python
   def calculate_campaign_score(campaign, kpi, config):
       """
       Scoring algorithm based on existing YandexDirect implementation.
       """
       clicks = max(campaign.metrics.clicks, 0)
       conversions = max(campaign.metrics.conversions, 0)
       spend = max(campaign.metrics.spend, 0.0)
       
       # Quality score (if enough conversions)
       if conversions >= config.min_conversions_for_confident:
           cpa_score = clamp(kpi.target_cpa / campaign.metrics.cpa, 0.4, 1.8)
           roi_score = clamp(1.0 + campaign.metrics.roi / 100.0, 0.5, 1.8)
           quality = 0.55 * cpa_score + 0.45 * roi_score
       else:
           # Cold campaign penalty
           quality = 1.0
           if clicks >= config.cold_clicks_threshold and conversions == 0:
               quality = 0.7
           if spend >= kpi.target_cpa and conversions == 0:
               quality = min(quality, 0.6)
       
       # Volume score
       volume = clamp(0.8 + min(clicks, 200) / 250.0, 0.8, 1.6)
       
       return clamp(quality * volume, 0.1, 3.0)
   ```

2. **Выявить проблемные кампании (hard stop triggers):**
   - Нет конверсий при значительных тратах (spend > target_cpa * 2.5)
   - Много кликов без конверсий (clicks > 30, conversions = 0)
   - CPA значительно выше целевого (cpa > target_cpa * 1.5)

3. **Классифицировать кампании:**
   - **Profitable** (score > 1.2, cpa < target_cpa * 0.85) → увеличить бюджет
   - **Acceptable** (score 0.8-1.2, cpa близко к target) → оставить без изменений
   - **Underperforming** (score < 0.8, cpa > target_cpa * 1.3) → снизить бюджет
   - **Critical** (hard stop trigger) → пауза или резкое снижение

### Шаг 3: Применение стратегии оптимизации

**Режим: bid_optimization**
1. Для кампаний с CPA > target_cpa * 1.3:
   - Переключить на автоматическую стратегию (Target CPA или Maximize Conversions)
   - Снизить бюджет на 15% для контроля рисков
2. Для кампаний с CPA > target_cpa * 1.5:
   - Снизить бюджет на 25%
   - Рассмотреть паузу, если нет улучшений за 3 дня

**Режим: budget_allocation**
1. Рассчитать целевой бюджет для каждой кампании:
   ```python
   total_score = sum(max(score, 0.05) for score in campaign_scores)
   target_budget = total_daily_budget * (campaign_score / total_score)
   ```
2. Применить бонусы/штрафы:
   - **Бонус +10%** если CPA < target_cpa * 0.85 и ROI > 20%
   - **Штраф -15%** если CPA > target_cpa * 1.3
   - **Штраф -35%** если hard stop trigger (без паузы)
3. Ограничить изменения (volatility control):
   - Максимальное увеличение: +20% от текущего бюджета
   - Максимальное снижение: -25% от текущего бюджета
   - Минимальный бюджет: 300 руб/день
   - Минимальное изменение: 100 руб (игнорировать мелкие корректировки)

**Режим: budget_pacing**
1. Рассчитать текущий темп расходования:
   ```python
   days_in_month = 30
   days_passed = current_day
   days_remaining = days_in_month - days_passed
   
   spent_pct = total_spend / monthly_budget
   time_pct = days_passed / days_in_month
   
   pacing_ratio = spent_pct / time_pct  # 1.0 = идеально, >1.0 = перерасход, <1.0 = недорасход
   ```
2. Корректировать дневные бюджеты:
   - Если pacing_ratio > 1.2 (перерасход 20%+) → снизить бюджеты на 15-20%
   - Если pacing_ratio < 0.8 (недорасход 20%+) → увеличить бюджеты на 10-15%
   - Если 0.9 < pacing_ratio < 1.1 → оставить без изменений
3. Учесть сезонность (медицинская специфика):
   - Грипп/ОРВИ: увеличить бюджет зимой (декабрь-февраль) на 20-30%
   - Аллергии: увеличить бюджет весной (март-май) на 15-25%
   - Косметология: увеличить бюджет перед летом (апрель-май) на 20-30%

**Режим: roi_optimization**
1. Приоритизировать кампании по ROI:
   - ROI > 30%: увеличить бюджет на 15-20%
   - ROI 15-30%: оставить без изменений
   - ROI 5-15%: снизить бюджет на 10-15%
   - ROI < 5%: снизить бюджет на 20-25% или пауза
2. Учесть LTV (lifetime value) для медицинского маркетинга:
   - Пациенты возвращаются → LTV = 3-5x первой покупки
   - Корректировать target_cpa с учётом LTV: `effective_target_cpa = target_cpa * ltv_multiplier`
3. Geo-специфичное распределение:
   - Москва/СПб: более высокий CPA допустим (больше платёжеспособность)
   - Регионы: более строгий контроль CPA

### Шаг 4: Генерация действий
1. Для каждой кампании создать OptimizationAction:
   ```python
   action = {
       "campaign_id": campaign.id,
       "action_type": "set_daily_budget" | "change_strategy" | "pause_campaign",
       "current_value": current_budget,
       "new_value": target_budget,
       "reason": "Scale profitable campaign (CPA 20% below target, ROI 25%)",
       "expected_impact": {
           "roi_change": "+5%",
           "cpa_change": "-10%"
       }
   }
   ```
2. Приоритизировать действия:
   - **P0 (критичные)**: Паузы кампаний с hard stop trigger
   - **P1 (важные)**: Снижение бюджетов underperforming кампаний
   - **P2 (оптимизация)**: Увеличение бюджетов profitable кампаний
3. Валидировать действия:
   - Проверить, что новый бюджет в пределах constraints (min/max)
   - Проверить, что изменение не превышает max_step_up/down
   - Проверить, что сумма бюджетов не превышает target_daily_budget

### Шаг 5: Формирование результата
1. Собрать все действия в массив `optimization_actions`
2. Рассчитать summary:
   - `total_campaigns` - всего кампаний проанализировано
   - `optimized_campaigns` - кампаний с изменениями
   - `paused_campaigns` - кампаний на паузу
   - `budget_reallocated` - сумма перераспределённого бюджета
   - `expected_roi_improvement` - ожидаемое улучшение ROI
3. Рассчитать метрики выполнения:
   - `execution_time_ms` - время выполнения
   - `campaigns_analyzed` - количество проанализированных кампаний
   - `actions_generated` - количество сгенерированных действий

### Шаг 6: Отправка результата
1. Сформировать событие `subagent.task.completed`
2. Отправить в Event Bus
3. Логировать в Event Store
4. Сохранить в Obsidian vault:
   - Результаты оптимизации
   - Метрики производительности
   - Инсайты (какие кампании profitable, какие underperforming)

---

## 🔧 ИНТЕГРАЦИИ

### Внешние сервисы:

**Яндекс.Директ API v5:**
- API endpoint: `https://api.direct.yandex.com/json/v5/`
- Методы:
  - `campaigns.update` - изменение бюджета кампании
  - `bids.set` - изменение ставок
  - `campaigns.suspend` - пауза кампании
- Аутентификация: OAuth 2.0 token
- Rate limit: 10 requests/second, 100,000 requests/day
- Документация: https://yandex.ru/dev/direct/doc/dg/concepts/about.html
- Стоимость: Бесплатно (в рамках лимитов)

**VK Ads API:**
- API endpoint: `https://ads.vk.com/api/v2/`
- Методы:
  - `campaigns.update` - изменение бюджета
  - `ads.update` - изменение ставок
- Аутентификация: Access token
- Rate limit: 3 requests/second
- Документация: https://ads.vk.com/help/articles/api_documentation
- Стоимость: Бесплатно

**myTarget API:**
- API endpoint: `https://target.my.com/api/v2/`
- Методы:
  - `campaigns/{id}.json` - изменение бюджета (PATCH)
- Аутентификация: OAuth 2.0
- Rate limit: 60 requests/minute
- Документация: https://target.my.com/doc/api/
- Стоимость: Бесплатно

**Telegram Ads API:**
- API endpoint: `https://ads.telegram.org/api/`
- Методы: (документация ограничена, доступ по заявке)
- Аутентификация: API token
- Rate limit: Неизвестно (требует уточнения)
- Документация: https://ads.telegram.org/
- Стоимость: Бесплатно

**Дзен API:**
- API endpoint: `https://dzen.ru/api/v1/`
- Методы: (документация ограничена)
- Аутентификация: OAuth 2.0
- Rate limit: Неизвестно (требует уточнения)
- Документация: https://yandex.ru/dev/zen/doc/
- Стоимость: Бесплатно

### Внутренние зависимости:

- **Event Bus** (обязательно) - получение задач, отправка результатов
- **Event Store** (обязательно) - логирование всех событий
- **Obsidian vault** (обязательно) - сохранение результатов и инсайтов
- **Campaign Manager Agent** (обязательно) - применение изменений бюджетов
- **Performance Monitor Agent** (обязательно) - источник метрик
- **Analytics Agent** (опционально) - дополнительная аналитика (LTV, сезонность)

---

## 📊 МЕТРИКИ УСПЕХА

### Качественные метрики:

**Точность оптимизации:**
- Метрика: Процент кампаний с улучшением метрик после оптимизации
- Целевое значение: > 70%
- Как измерять: Сравнить метрики до/после оптимизации за 7 дней

**ROI improvement:**
- Метрика: Средний прирост ROI после оптимизации
- Целевое значение: +5-10%
- Как измерять: (ROI_after - ROI_before) / ROI_before * 100%

**CPA reduction:**
- Метрика: Среднее снижение CPA после оптимизации
- Целевое значение: -10-15%
- Как измерять: (CPA_after - CPA_before) / CPA_before * 100%

**Quality Score improvement:**
- Метрика: Средний прирост Quality Score
- Целевое значение: +0.5-1.0 балла
- Как измерять: Quality_Score_after - Quality_Score_before

### Производительность:

**Скорость:**
- Среднее время выполнения: < 3 секунды
- 95-й перцентиль: < 5 секунд
- Максимальное время: < 10 секунд

**Надёжность:**
- Success rate: > 95%
- Partial success rate: > 99%
- Failure rate: < 1%

**Throughput:**
- Кампаний в секунду: > 10
- Максимальная нагрузка: 100 кампаний за запрос

### Бизнес-метрики:

**Влияние на прибыль:**
- ROI improvement: +5-10% в среднем
- CPA reduction: -10-15% в среднем
- Budget utilization: > 95% (эффективное использование бюджета)
- Wasted spend reduction: -20-30% (снижение неэффективных трат)

**Автономность:**
- Процент решений без вмешательства человека: > 90%
- Время на ручную корректировку: < 10% от общего времени

---

## 🧪 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ

### Пример 1: Успешная оптимизация profitable кампании

**Входные данные:**
```json
{
  "account_id": "12345",
  "platform": "yandex_direct",
  "campaigns": [
    {
      "campaign_id": "67890",
      "name": "Стоматология Москва",
      "status": "active",
      "budget_daily": 1000.0,
      "strategy": "manual_cpc",
      "metrics": {
        "spend": 5000.0,
        "clicks": 250,
        "conversions": 12,
        "cpa": 416.67,
        "roi": 28.5,
        "quality_score": 8.2
      }
    }
  ],
  "kpi": {
    "target_cpa": 600.0,
    "target_roi": 20.0,
    "daily_budget": 10000.0
  },
  "optimization_mode": "budget_allocation"
}
```

**Выходные данные:**
```json
{
  "status": "success",
  "result": {
    "optimization_actions": [
      {
        "campaign_id": "67890",
        "action_type": "set_daily_budget",
        "current_value": 1000.0,
        "new_value": 1200.0,
        "reason": "Scale profitable campaign (CPA 31% below target, ROI 42% above target, Quality Score 8.2)",
        "expected_impact": {
          "roi_change": "+5%",
          "cpa_change": "-5%",
          "conversions_change": "+20%"
        }
      }
    ],
    "summary": {
      "total_campaigns": 1,
      "optimized_campaigns": 1,
      "paused_campaigns": 0,
      "budget_reallocated": 200.0,
      "expected_roi_improvement": "+5%"
    }
  },
  "metrics": {
    "execution_time_ms": 1250,
    "campaigns_analyzed": 1,
    "actions_generated": 1
  }
}
```

### Пример 2: Пауза underperforming кампании

**Входные данные:**
```json
{
  "account_id": "12345",
  "platform": "yandex_direct",
  "campaigns": [
    {
      "campaign_id": "11111",
      "name": "Косметология регионы",
      "status": "active",
      "budget_daily": 800.0,
      "strategy": "manual_cpc",
      "metrics": {
        "spend": 2500.0,
        "clicks": 150,
        "conversions": 0,
        "cpa": null,
        "roi": null,
        "quality_score": 4.5
      }
    }
  ],
  "kpi": {
    "target_cpa": 600.0,
    "target_roi": 20.0,
    "daily_budget": 10000.0
  },
  "optimization_mode": "bid_optimization"
}
```

**Выходные данные:**
```json
{
  "status": "success",
  "result": {
    "optimization_actions": [
      {
        "campaign_id": "11111",
        "action_type": "pause_campaign",
        "current_value": "active",
        "new_value": "paused",
        "reason": "Hard stop: no conversions with spend 2500 RUB (4.2x target CPA), 150 clicks",
        "expected_impact": {
          "wasted_spend_reduction": "800 RUB/day"
        }
      }
    ],
    "summary": {
      "total_campaigns": 1,
      "optimized_campaigns": 0,
      "paused_campaigns": 1,
      "budget_reallocated": -800.0,
      "expected_roi_improvement": "N/A"
    }
  },
  "metrics": {
    "execution_time_ms": 980,
    "campaigns_analyzed": 1,
    "actions_generated": 1
  }
}
```

### Пример 3: Множественная оптимизация с перераспределением

**Входные данные:**
```json
{
  "account_id": "12345",
  "platform": "yandex_direct",
  "campaigns": [
    {
      "campaign_id": "c1",
      "name": "Кампания A (profitable)",
      "budget_daily": 1000.0,
      "metrics": {"spend": 5000, "conversions": 12, "cpa": 416.67, "roi": 28.5}
    },
    {
      "campaign_id": "c2",
      "name": "Кампания B (acceptable)",
      "budget_daily": 1500.0,
      "metrics": {"spend": 7500, "conversions": 13, "cpa": 576.92, "roi": 21.0}
    },
    {
      "campaign_id": "c3",
      "name": "Кампания C (underperforming)",
      "budget_daily": 2000.0,
      "metrics": {"spend": 10000, "conversions": 12, "cpa": 833.33, "roi": 8.5}
    }
  ],
  "kpi": {"target_cpa": 600.0, "target_roi": 20.0, "daily_budget": 4500.0},
  "optimization_mode": "budget_allocation"
}
```

**Выходные данные:**
```json
{
  "status": "success",
  "result": {
    "optimization_actions": [
      {
        "campaign_id": "c1",
        "action_type": "set_daily_budget",
        "current_value": 1000.0,
        "new_value": 1200.0,
        "reason": "Scale profitable campaign (score 1.45, CPA 31% below target)"
      },
      {
        "campaign_id": "c2",
        "action_type": "set_daily_budget",
        "current_value": 1500.0,
        "new_value": 1800.0,
        "reason": "Maintain acceptable performance (score 1.05, CPA 4% below target)"
      },
      {
        "campaign_id": "c3",
        "action_type": "set_daily_budget",
        "current_value": 2000.0,
        "new_value": 1500.0,
        "reason": "Reduce underperforming campaign (score 0.65, CPA 39% above target)"
      }
    ],
    "summary": {
      "total_campaigns": 3,
      "optimized_campaigns": 3,
      "paused_campaigns": 0,
      "budget_reallocated": 500.0,
      "expected_roi_improvement": "+8%"
    }
  },
  "metrics": {
    "execution_time_ms": 2100,
    "campaigns_analyzed": 3,
    "actions_generated": 3
  }
}
```

---

## 🔒 ОБРАБОТКА ОШИБОК

### Типы ошибок:

**Валидация входных данных:**
- Код: `INVALID_INPUT`
- Примеры:
  - Отсутствуют обязательные поля (account_id, campaigns, kpi)
  - Некорректные метрики (spend < 0, clicks < 0)
  - Некорректные constraints (min > max)
- Действие: Вернуть failure сразу с описанием ошибки
- Retry: Нет

**Ошибка внешнего API (платформа недоступна):**
- Код: `EXTERNAL_API_ERROR`
- Примеры:
  - Яндекс.Директ API вернул 500
  - VK Ads API timeout
  - Rate limit exceeded
- Действие: Retry с exponential backoff (1s, 2s, 4s)
- Retry: До 3 попыток
- Fallback: Вернуть partial_success с обработанными кампаниями

**Недостаточно данных для оптимизации:**
- Код: `INSUFFICIENT_DATA`
- Примеры:
  - Кампания без метрик (spend=0, clicks=0, conversions=0)
  - Все кампании "холодные" (нет конверсий)
- Действие: Пропустить кампанию, продолжить с остальными
- Retry: Нет
- Результат: partial_success с пропущенными кампаниями в errors

**Timeout:**
- Код: `TIMEOUT`
- Действие: Вернуть partial_success с обработанными кампаниями
- Retry: Нет
- Лимит: 10 секунд на весь запрос

**Внутренняя ошибка:**
- Код: `INTERNAL_ERROR`
- Действие: Логировать stack trace, вернуть failure
- Retry: Нет

### Graceful degradation:

При частичном сбое:
1. Обработать максимум кампаний
2. Вернуть partial_success
3. Указать в errors, какие кампании не удалось обработать и почему
4. Позволить Orchestrator решить, что делать дальше (retry, skip, escalate)

**Пример partial_success:**
```json
{
  "status": "partial_success",
  "result": {
    "optimization_actions": [/* успешно обработанные */],
    "summary": {
      "total_campaigns": 10,
      "optimized_campaigns": 7,
      "skipped_campaigns": 3
    }
  },
  "errors": [
    {
      "code": "INSUFFICIENT_DATA",
      "message": "Campaign c8 has no metrics (spend=0, clicks=0)",
      "campaign_id": "c8"
    },
    {
      "code": "EXTERNAL_API_ERROR",
      "message": "VK Ads API timeout after 3 retries",
      "campaign_id": "c9"
    }
  ]
}
```

---

## 🧠 ОБУЧЕНИЕ И АДАПТАЦИЯ

### Источники обучения:

**От Ads Magister:**
- Обновлённые best practices по bid optimization
- Новые стратегии назначения ставок (Target ROAS, Portfolio bidding)
- Изменения в алгоритмах платформ (Яндекс, VK, myTarget)
- Медицинская специфика (сезонность, LTV, compliance)

**Из собственного опыта:**
- Успешные оптимизации (какие действия привели к улучшению метрик)
- Неудачные попытки (какие действия не сработали)
- Корреляции (какие факторы влияют на успех оптимизации)
- A/B тесты (сравнение разных стратегий)

**Из Obsidian vault:**
- Исторические данные оптимизаций
- Паттерны profitable/underperforming кампаний
- Сезонные тренды (когда увеличивать/снижать бюджеты)
- Geo-специфичные инсайты (какие регионы эффективнее)

### Адаптация:

**Когда адаптироваться:**
- Метрики падают ниже целевых (ROI improvement < 5%, CPA reduction < 10%)
- Появляются новые best practices от Magister
- Изменяются внешние условия (сезонность, конкуренция, алгоритмы платформ)
- Обнаружены новые паттерны в данных

**Как адаптироваться:**
1. Получить обновлённые знания от Ads Magister
2. Протестировать на небольшой выборке (10-20% кампаний)
3. Сравнить метрики до/после (A/B тест за 7-14 дней)
4. Если улучшение подтверждено (ROI +5%+, CPA -10%+) → применить ко всем кампаниям
5. Сохранить результаты в Obsidian vault для будущего обучения

**Примеры адаптации:**
- Обнаружено, что кампании с Quality Score > 8 дают ROI на 15% выше → увеличить бонус для таких кампаний с +10% до +15%
- Сезонный паттерн: грипп/ОРВИ зимой → автоматически увеличивать бюджеты на 20-30% в декабре-феврале
- Geo-инсайт: Москва даёт CPA на 30% выше, но LTV в 2x больше → корректировать target_cpa для Москвы: `target_cpa_moscow = target_cpa * 1.3`

---

## 📝 ЛОГИРОВАНИЕ

### Что логировать:

**В Event Store (обязательно):**
- Все входящие события `subagent.task.assigned`
- Все исходящие события `subagent.task.completed`
- Correlation ID для трейсинга
- Timestamp каждого события

**В Obsidian vault (обязательно):**
- Результаты оптимизации (какие действия сгенерированы)
- Метрики производительности (execution_time, campaigns_analyzed)
- Инсайты:
  - Profitable кампании (score > 1.2, CPA < target * 0.85)
  - Underperforming кампании (score < 0.8, CPA > target * 1.3)
  - Hard stop triggers (паузы кампаний)
  - Сезонные паттерны
  - Geo-специфичные инсайты

**В системные логи (опционально):**
- Debug информация (расчёт scores, промежуточные значения)
- Ошибки и warnings (API errors, validation errors)
- Performance traces (время выполнения каждого шага)

### Формат логов:

```
[2026-05-11 11:30:45] [INFO] [budget-optimizer] [corr-id-12345] Optimized 10 campaigns: 7 improved, 1 paused, 2 skipped
[2026-05-11 11:30:45] [DEBUG] [budget-optimizer] [corr-id-12345] Campaign c1: score=1.45, CPA=416.67 (31% below target), action=increase_budget +20%
[2026-05-11 11:30:46] [ERROR] [budget-optimizer] [corr-id-12345] VK Ads API error: timeout after 3 retries for campaign c9
```

---

## 🧪 ТЕСТИРОВАНИЕ

### Unit тесты:

**Покрытие:** > 80%

**Обязательные тесты:**
- `test_calculate_campaign_score()` - расчёт score для разных сценариев
- `test_classify_campaigns()` - классификация profitable/acceptable/underperforming/critical
- `test_bid_optimization_strategy()` - логика bid optimization
- `test_budget_allocation_strategy()` - логика budget allocation
- `test_budget_pacing_strategy()` - логика budget pacing
- `test_roi_optimization_strategy()` - логика ROI optimization
- `test_apply_constraints()` - применение constraints (min/max, step_up/down)
- `test_validate_input()` - валидация входных данных
- `test_handle_insufficient_data()` - обработка кампаний без метрик
- `test_graceful_degradation()` - partial_success при ошибках

### Integration тесты:

**Обязательные сценарии:**
- `test_receive_task_from_orchestrator()` - получение задачи через Event Bus
- `test_send_result_to_orchestrator()` - отправка результата через Event Bus
- `test_log_to_event_store()` - логирование в Event Store
- `test_save_to_obsidian()` - сохранение в Obsidian vault
- `test_external_api_integration()` - интеграция с Яндекс.Директ API (mock)
- `test_retry_on_api_error()` - retry при ошибках API

### E2E тесты:

**Обязательные сценарии:**
- `test_full_optimization_cycle()` - полный цикл: задача → анализ → оптимизация → результат
- `test_multiple_campaigns_optimization()` - оптимизация 10+ кампаний
- `test_hard_stop_trigger()` - пауза кампании при hard stop
- `test_budget_reallocation()` - перераспределение бюджета между кампаниями
- `test_seasonal_adjustment()` - учёт сезонности (грипп зимой, аллергии весной)
- `test_geo_specific_optimization()` - geo-специфичная оптимизация (Москва vs регионы)
- `test_ltv_adjustment()` - учёт LTV для медицинского маркетинга

---

## 🚀 DEPLOYMENT

### Требования:

**Окружение:**
- Python 3.11+
- Event Bus доступен
- Event Store доступен
- Obsidian vault доступен
- Доступ к внешним API (Яндекс.Директ, VK Ads, myTarget, Telegram Ads, Дзен)

**Зависимости:**
- `pydantic >= 2.0` - валидация данных
- `httpx >= 0.24` - HTTP клиент для API
- `tenacity >= 8.2` - retry logic
- `python-dateutil >= 2.8` - работа с датами (сезонность)

**Конфигурация:**
```env
SUBAGENT_ID=budget-optimizer
EVENT_BUS_URL=redis://localhost:6379
EVENT_STORE_URL=postgresql://localhost:5432/event_store
OBSIDIAN_VAULT_PATH=/path/to/obsidian/ads-magister

# API credentials
YANDEX_DIRECT_TOKEN=...
VK_ADS_TOKEN=...
MYTARGET_TOKEN=...
TELEGRAM_ADS_TOKEN=...
DZEN_TOKEN=...

# Optimization config
MIN_DAILY_BUDGET=300.0
MAX_DAILY_BUDGET=50000.0
MAX_STEP_UP_PCT=20.0
MAX_STEP_DOWN_PCT=25.0
MIN_CONVERSIONS_FOR_CONFIDENT=2
COLD_CLICKS_THRESHOLD=25
```

### Мониторинг:

**Метрики для алертов:**
- Success rate < 95% → Warning
- Success rate < 90% → Critical
- Avg execution time > 3 seconds → Warning
- 95th percentile > 5 seconds → Critical
- ROI improvement < 5% (за 7 дней) → Warning
- CPA reduction < 10% (за 7 дней) → Warning
- External API errors > 5% → Warning

**Дашборд метрик:**
- Количество оптимизаций в день
- Средний ROI improvement
- Средний CPA reduction
- Процент paused кампаний
- Распределение по optimization_mode
- Топ profitable кампании
- Топ underperforming кампании

---

## 📚 СВЯЗАННЫЕ ДОКУМЕНТЫ

### Спецификации:
- `ADS_MAGISTER_SPEC.md` - Спецификация родительского Magister
- `ADS_ORCHESTRATOR_SPEC.md` - Спецификация родительского Orchestrator
- `CAMPAIGN_MANAGER_SPEC.md` - Спецификация Campaign Manager Agent
- `PERFORMANCE_MONITOR_SPEC.md` - Спецификация Performance Monitor Agent

### Код:
- `AIM/src/aim/subagents/ads/budget_optimizer.py` - Реализация
- `AIM/tests/subagents/ads/test_budget_optimizer.py` - Тесты
- `AIM/Old/YandexDirect/src/yad_agent/agents/budget_guardian.py` - Существующая реализация (reference)
- `AIM/Old/YandexDirect/src/yad_agent/agents/bidding.py` - Существующая реализация (reference)
- `AIM/Old/YandexDirect/src/yad_agent/agents/optimizer.py` - Существующая реализация (reference)

### Документация:
- Event Bus API
- Event Store API
- Obsidian integration guide
- Яндекс.Директ API v5 documentation
- VK Ads API documentation
- myTarget API documentation

---

## 📋 CHANGELOG

### Version 1.0 (2026-05-11)
- Initial specification
- Поддержка 4 режимов оптимизации: bid_optimization, budget_allocation, budget_pacing, roi_optimization
- Поддержка 5 платформ: Яндекс.Директ (P0), VK Ads (P1), myTarget/Telegram Ads/Дзен (P2)
- Медицинская специфика: сезонность, LTV, geo-специфичное бюджетирование
- Автономность: полная автономность принятия решений и применения изменений
- Алгоритм scoring на основе существующей реализации YandexDirect
- Graceful degradation при ошибках (partial_success)

### TODO (Future versions)
- Machine learning для прогнозирования оптимальных бюджетов
- A/B тестирование разных стратегий оптимизации
- Автоматическая адаптация constraints на основе исторических данных
- Интеграция с Google Ads (если потребуется)
- Real-time оптимизация (сейчас batch processing)

---

**Дата создания:** 2026-05-11  
**Автор:** Mikhail Eliseev (via meAI Architect)  
**Версия:** 1.0  
**Статус:** Draft
