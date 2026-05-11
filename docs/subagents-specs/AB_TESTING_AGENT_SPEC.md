# A/B Testing Agent - Спецификация

**Дата:** 2026-05-11  
**Magister:** Ads Magister  
**Приоритет:** P2  
**Статус:** Ready for Implementation

---

## 🎯 РОЛЬ И НАЗНАЧЕНИЕ

### Основная роль:
A/B Testing Agent проводит статистически валидные эксперименты для оптимизации рекламных кампаний и лендингов. Тестирует все элементы рекламных объявлений (изображения, заголовки, тексты, tone of voice, таргетинг) и лендингов, используя данные от CustDev и интеграции с Яндекс.Вариокуб/Метрика.

### Что делает:
- ✅ Проводит A/B тесты рекламных объявлений (изображения, заголовки, тексты, tone of voice)
- ✅ Тестирует лендинги через Яндекс.Вариокуб (структура, CTA, формы, визуальные элементы)
- ✅ Рассчитывает статистическую значимость (p-value, confidence intervals, power analysis)
- ✅ Определяет размер выборки и длительность теста (sample size calculation, MDE)
- ✅ Применяет победителей автоматически через Google Ads / Яндекс.Директ API
- ✅ Проверяет соответствие законодательству (ФЗ-38, ФЗ-323) перед запуском тестов
- ✅ Интегрируется с CustDev данными через Brand Analytics Agent

### Что НЕ делает:
- ❌ Не создаёт креативы (получает варианты от Campaign Manager Agent)
- ❌ Не управляет бюджетами (делегирует Budget Optimizer Agent)
- ❌ Не анализирует конкурентов (делегирует Analytics Agent)
- ❌ Не принимает стратегические решения (отчитывается Ads Magister)

### Место в иерархии:
```
Ads Magister
    ↓
Ads Orchestrator
    ↓
A/B Testing Agent ← вы здесь
```

### Уникальная ценность:
**Статистическая строгость + медицинская специфика:**
- Использует two-proportion z-test для сравнения конверсий (не просто "больше кликов")
- Рассчитывает sample size ПЕРЕД тестом (не "запустим и посмотрим")
- Учитывает медицинскую специфику: низкие конверсии (2-5%), сезонность, законодательные ограничения
- Проверяет compliance с ФЗ-38 и ФЗ-323 автоматически (запрещённые формулировки, обязательные disclaimers)

**Статистика:**
- **900M+ ChatGPT users/week** — AI-оптимизированный контент критичен для видимости
- **Standard A/B test:** 95% confidence (p < 0.05), 80% power (1-β = 0.8)
- **Medical marketing baseline:** 2-5% conversion (vs 5-10% e-commerce) → требует 2-4x больше sample size
- **Peeking problem:** Проверка результатов до достижения sample size увеличивает false positive rate с 5% до 20-30%
- **Minimum test duration:** 14 дней (capture weekly cycles), независимо от достижения sample size

---

## 📥 ВХОДНЫЕ ДАННЫЕ

### Получает от Orchestrator:

**Формат события:**
```json
{
  "event_type": "subagent.task.assigned",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "ab-testing-agent",
  "payload": {
    "test_type": "ad_creative" | "landing_page" | "bidding_strategy",
    "variants": [
      {
        "variant_id": "control",
        "name": "Control",
        "elements": {
          "headline": "Лечение варикоза",
          "description": "Консультация флеболога",
          "image_url": "https://...",
          "cta": "Записаться"
        }
      },
      {
        "variant_id": "treatment",
        "name": "Treatment",
        "elements": {
          "headline": "Современные методы лечения варикоза",
          "description": "Опытные флебологи",
          "image_url": "https://...",
          "cta": "Получить консультацию"
        }
      }
    ],
    "target_metric": "conversion_rate" | "ctr" | "cpa",
    "baseline_conversion_rate": 0.03,
    "minimum_detectable_effect": 0.15,
    "significance_level": 0.05,
    "statistical_power": 0.80,
    "campaign_id": "uuid",
    "traffic_allocation": {
      "control": 0.5,
      "treatment": 0.5
    },
    "max_duration_days": 28
  }
}
```

**Обязательные параметры:**
- `test_type` (string) - Тип теста: ad_creative, landing_page, bidding_strategy
- `variants` (array) - Массив вариантов для тестирования (минимум 2, максимум 4)
- `target_metric` (string) - Целевая метрика: conversion_rate, ctr, cpa
- `baseline_conversion_rate` (float) - Текущая конверсия (для расчёта sample size)
- `campaign_id` (string) - ID кампании для привязки результатов

**Опциональные параметры:**
- `minimum_detectable_effect` (float) - Минимальный детектируемый эффект (default: 0.15 = 15% relative lift)
- `significance_level` (float) - Уровень значимости (default: 0.05 = 95% confidence)
- `statistical_power` (float) - Статистическая мощность (default: 0.80 = 80% power)
- `traffic_allocation` (object) - Распределение трафика между вариантами (default: равномерное)
- `max_duration_days` (int) - Максимальная длительность теста (default: 28 дней)

### Получает от других агентов:

**От Campaign Manager Agent:**
- Варианты объявлений для тестирования
- Настройки кампаний (таргетинг, бюджет, расписание)

**От Performance Monitor Agent:**
- Текущие метрики производительности (baseline conversion rate, CTR, CPA)
- Исторические данные для расчёта sample size

**От Brand Analytics Agent:**
- CustDev данные (реальные конверсии, продажи, LTV)
- Кассовые данные клиник для валидации результатов

**От Analytics Agent:**
- Сезонные паттерны (грипп зимой, аллергии весной)
- Geo-специфичные данные (разные регионы = разная стоимость)

---

## 📤 ВЫХОДНЫЕ ДАННЫЕ

### Отправляет Orchestrator:

**Формат события:**
```json
{
  "event_type": "subagent.task.completed",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "ab-testing-agent",
  "payload": {
    "status": "success" | "partial_success" | "failure",
    "result": {
      "test_id": "uuid",
      "winner": {
        "variant_id": "treatment",
        "variant_name": "Treatment",
        "confidence_level": 0.95,
        "p_value": 0.023,
        "absolute_lift": 0.005,
        "relative_lift": 0.167,
        "confidence_interval": {
          "lower": 0.08,
          "upper": 0.25
        }
      },
      "variants_performance": [
        {
          "variant_id": "control",
          "visitors": 10000,
          "conversions": 300,
          "conversion_rate": 0.030,
          "standard_error": 0.0017
        },
        {
          "variant_id": "treatment",
          "visitors": 10000,
          "conversions": 350,
          "conversion_rate": 0.035,
          "standard_error": 0.0018
        }
      ],
      "statistical_analysis": {
        "z_score": 2.27,
        "p_value": 0.023,
        "significance_level": 0.05,
        "is_significant": true,
        "statistical_power": 0.82,
        "sample_size_reached": true,
        "minimum_duration_met": true
      },
      "test_metadata": {
        "start_date": "2026-05-01",
        "end_date": "2026-05-15",
        "duration_days": 14,
        "total_visitors": 20000,
        "total_conversions": 650
      },
      "recommendations": [
        "Deploy winner (Treatment) to 100% of traffic",
        "Expected improvement: +16.7% conversion rate",
        "Estimated monthly impact: +50 conversions, +500K RUB revenue"
      ],
      "compliance_check": {
        "passed": true,
        "issues": []
      }
    },
    "metrics": {
      "execution_time_ms": 45000,
      "tests_completed": 1,
      "variants_tested": 2,
      "sample_size_calculated": 20000,
      "actual_sample_size": 20000
    },
    "errors": []
  }
}
```

**Структура результата:**
- `test_id` (string) - Уникальный ID теста
- `winner` (object) - Победивший вариант с метриками
  - `variant_id` (string) - ID варианта
  - `confidence_level` (float) - Уровень уверенности (0.95 = 95%)
  - `p_value` (float) - P-value (< 0.05 = significant)
  - `absolute_lift` (float) - Абсолютный прирост (0.005 = +0.5 percentage points)
  - `relative_lift` (float) - Относительный прирост (0.167 = +16.7%)
  - `confidence_interval` (object) - Доверительный интервал для lift
- `variants_performance` (array) - Метрики всех вариантов
- `statistical_analysis` (object) - Детальный статистический анализ
- `recommendations` (array) - Рекомендации по применению результатов
- `compliance_check` (object) - Результат проверки на соответствие законодательству

**Метрики:**
- `execution_time_ms` - Время выполнения теста (включая сбор данных)
- `tests_completed` - Количество завершённых тестов
- `variants_tested` - Количество протестированных вариантов
- `sample_size_calculated` - Рассчитанный размер выборки
- `actual_sample_size` - Фактический размер выборки

### Отправляет другим агентам:

**Campaign Manager Agent:**
- Результаты тестов для применения победителей
- Рекомендации по обновлению объявлений

**Performance Monitor Agent:**
- Обновлённые baseline метрики после применения победителей
- Исторические данные тестов для анализа трендов

**Analytics Agent:**
- Метрики тестов для агрегации и отчётности
- Инсайты о том, что работает (tone of voice, CTA, изображения)

---

## 🔄 АЛГОРИТМ РАБОТЫ

### Шаг 1: Получение задачи и валидация

**1.1 Подписка на события:**
```python
await event_bus.subscribe(
    event_type="subagent.task.assigned",
    handler=self.handle_task,
    filter={"subagent_id": "ab-testing-agent"}
)
```

**1.2 Валидация входных параметров:**
```python
# Проверка обязательных параметров
assert len(variants) >= 2, "Minimum 2 variants required"
assert len(variants) <= 4, "Maximum 4 variants allowed"
assert 0 < baseline_conversion_rate < 1, "Invalid baseline"
assert 0 < minimum_detectable_effect < 1, "Invalid MDE"
assert significance_level in [0.01, 0.05, 0.10], "Invalid alpha"
assert statistical_power in [0.80, 0.90, 0.95], "Invalid power"

# Проверка распределения трафика
assert sum(traffic_allocation.values()) == 1.0, "Traffic allocation must sum to 1.0"
```

**1.3 Compliance check (медицинская реклама):**
```python
compliance_result = await self.check_medical_compliance(variants)
if not compliance_result.passed:
    return {
        "status": "failure",
        "errors": [{
            "code": "COMPLIANCE_VIOLATION",
            "message": "Variants violate medical advertising law",
            "details": compliance_result.issues
        }]
    }
```

**Запрещённые формулировки (ФЗ-38, ФЗ-323):**
- ❌ "Гарантируем полное излечение" (guarantees of results)
- ❌ "100% результат" (unrealistic expectations)
- ❌ "Вылечим за 3 дня" (misleading claims)
- ❌ "Лучшая клиника в России" (unsubstantiated claims)
- ❌ "Избавим от боли навсегда" (guarantees)

**Обязательные элементы:**
- ✅ "Имеются противопоказания. Необходима консультация специалиста."
- ✅ Номер лицензии и орган выдачи
- ✅ Disclaimer для "до/после" изображений (если есть)

### Шаг 2: Расчёт sample size и длительности теста

**2.1 Sample size calculation:**

**Формула (two-proportion z-test):**
```
n = (Z_α/2 + Z_β)² × [p₁(1-p₁) + p₂(1-p₂)] / (p₂ - p₁)²

где:
n = sample size per variant
Z_α/2 = z-score for significance level (1.96 for 95% confidence, two-tailed)
Z_β = z-score for power (0.84 for 80% power, 1.28 for 90% power)
p₁ = baseline conversion rate
p₂ = expected conversion rate after improvement (p₁ + δ)
δ = absolute minimum detectable effect (p₁ × MDE_relative)
```

**Пример расчёта:**
```python
# Входные данные
baseline = 0.03  # 3% baseline conversion
mde_relative = 0.15  # 15% relative lift
alpha = 0.05  # 95% confidence
power = 0.80  # 80% power

# Расчёт
z_alpha = 1.96  # для alpha=0.05 (two-tailed)
z_beta = 0.84   # для power=0.80
delta_absolute = baseline * mde_relative  # 0.0045
p2 = baseline + delta_absolute  # 0.0345

# Sample size per variant
numerator = (z_alpha + z_beta) ** 2
denominator = delta_absolute ** 2
variance = baseline * (1 - baseline) + p2 * (1 - p2)
n_per_variant = (numerator * variance) / denominator

# Результат: ~21,000 visitors per variant (42,000 total)
```

**2.2 Test duration estimation:**
```python
# Минимальная длительность: 14 дней (capture weekly cycles)
min_duration_days = 14

# Оценка длительности на основе трафика
daily_traffic = await self.get_daily_traffic(campaign_id)
estimated_days = math.ceil(n_per_variant * len(variants) / daily_traffic)

# Итоговая длительность
test_duration_days = max(min_duration_days, estimated_days)

# Проверка на максимальную длительность
if test_duration_days > max_duration_days:
    # Недостаточно трафика для теста
    return {
        "status": "failure",
        "errors": [{
            "code": "INSUFFICIENT_TRAFFIC",
            "message": f"Test requires {test_duration_days} days, max allowed {max_duration_days}",
            "details": {
                "required_sample": n_per_variant * len(variants),
                "daily_traffic": daily_traffic,
                "estimated_days": test_duration_days
            }
        }]
    }
```

**2.3 MDE trade-off analysis:**

| Relative MDE | Absolute Effect (3% baseline) | Sample per Variant | Total Sample | Duration (1000 visitors/day) |
|--------------|-------------------------------|-------------------|--------------|------------------------------|
| 5%           | 0.15%                         | ~255,000          | ~510,000     | ~510 days (IMPRACTICAL)      |
| 10%          | 0.30%                         | ~64,000           | ~128,000     | ~128 days (TOO LONG)         |
| 15%          | 0.45%                         | ~28,000           | ~56,000      | ~56 days (ACCEPTABLE)        |
| 20%          | 0.60%                         | ~16,000           | ~32,000      | ~32 days (GOOD)              |
| 30%          | 0.90%                         | ~7,000            | ~14,000      | ~14 days (MINIMUM)           |

**Рекомендация:** Для медицинского маркетинга использовать MDE = 15-25% (баланс между чувствительностью и практичностью).

### Шаг 3: Запуск теста

**3.1 Создание тестовых вариантов:**

**Для рекламных объявлений (Google Ads / Яндекс.Директ):**
```python
# Google Ads API
for variant in variants:
    ad = await google_ads.create_ad(
        campaign_id=campaign_id,
        ad_group_id=ad_group_id,
        headline=variant.elements.headline,
        description=variant.elements.description,
        final_url=variant.elements.landing_url,
        image_url=variant.elements.image_url,
        status="ENABLED"
    )
    variant_ads[variant.variant_id] = ad.id

# Яндекс.Директ API
for variant in variants:
    ad = await yandex_direct.create_text_ad(
        campaign_id=campaign_id,
        ad_group_id=ad_group_id,
        title=variant.elements.headline,
        text=variant.elements.description,
        href=variant.elements.landing_url,
        status="ACCEPTED"
    )
    variant_ads[variant.variant_id] = ad.id
```

**Для лендингов (Яндекс.Вариокуб):**
```python
# Яндекс.Вариокуб через Метрику (web interface, no public API)
# Требуется ручная настройка через интерфейс Метрики
# Агент отправляет инструкции пользователю:
instructions = {
    "platform": "Яндекс.Метрика",
    "steps": [
        "1. Открыть Яндекс.Метрику → Эксперименты",
        "2. Создать новый эксперимент",
        f"3. Добавить варианты: {[v.name for v in variants]}",
        f"4. Настроить распределение трафика: {traffic_allocation}",
        f"5. Установить цель: {target_metric}",
        "6. Запустить эксперимент"
    ],
    "variants": [
        {
            "name": v.name,
            "url": v.elements.landing_url,
            "changes": v.elements.changes
        }
        for v in variants
    ]
}

# Отправить инструкции пользователю через AskUserQuestion
await self.ask_user_to_setup_variocube(instructions)
```

**3.2 Настройка трекинга:**
```python
# Яндекс.Метрика goals
for variant in variants:
    goal = await yandex_metrika.create_goal(
        counter_id=counter_id,
        name=f"Test {test_id} - {variant.name} - Conversion",
        type="url",
        conditions=[{
            "type": "contain",
            "url": "/thank-you"
        }]
    )
    variant_goals[variant.variant_id] = goal.id

# Google Ads conversion tracking
conversion_action = await google_ads.create_conversion_action(
    name=f"Test {test_id} - Conversion",
    category="PURCHASE",
    value_settings={
        "default_value": 1.0,
        "always_use_default_value": True
    }
)
```

**3.3 Запись метаданных теста:**
```python
test_metadata = {
    "test_id": test_id,
    "test_type": test_type,
    "start_date": datetime.now().isoformat(),
    "planned_end_date": (datetime.now() + timedelta(days=test_duration_days)).isoformat(),
    "variants": variants,
    "sample_size_per_variant": n_per_variant,
    "total_sample_size": n_per_variant * len(variants),
    "significance_level": significance_level,
    "statistical_power": statistical_power,
    "minimum_detectable_effect": minimum_detectable_effect,
    "baseline_conversion_rate": baseline_conversion_rate,
    "status": "running"
}

await event_store.append(
    stream_id=f"ab-test-{test_id}",
    event_type="test.started",
    data=test_metadata
)

await obsidian.save(
    vault="ads-magister",
    path=f"ab-tests/{test_id}/metadata.md",
    content=self.format_test_metadata(test_metadata)
)
```

### Шаг 4: Мониторинг теста (без peeking)

**4.1 Ежедневный сбор данных (БЕЗ анализа):**
```python
# Собираем данные, но НЕ проверяем significance
daily_data = await self.collect_daily_metrics(test_id)

# Сохраняем в Event Store
await event_store.append(
    stream_id=f"ab-test-{test_id}",
    event_type="test.daily_metrics",
    data=daily_data
)

# Проверяем только технические проблемы
technical_issues = self.check_technical_issues(daily_data)
if technical_issues:
    await self.alert_technical_issues(test_id, technical_issues)
```

**4.2 Проверка условий завершения (БЕЗ peeking):**
```python
# Проверяем ТОЛЬКО эти условия (НЕ смотрим на p-value)
conditions_met = {
    "sample_size_reached": total_visitors >= required_sample_size,
    "minimum_duration_met": days_running >= 14,
    "maximum_duration_exceeded": days_running >= max_duration_days
}

# Завершаем тест ТОЛЬКО если оба условия выполнены
if conditions_met["sample_size_reached"] and conditions_met["minimum_duration_met"]:
    await self.finalize_test(test_id)
elif conditions_met["maximum_duration_exceeded"]:
    # Максимальная длительность достигнута, завершаем принудительно
    await self.finalize_test(test_id, reason="max_duration_exceeded")
```

**КРИТИЧНО:** НЕ проверять p-value до достижения обоих условий (sample size + 14 дней). Peeking увеличивает false positive rate с 5% до 20-30%.

**4.3 Мониторинг guardrail metrics:**
```python
# Проверяем метрики, которые НЕ должны ухудшиться
guardrails = {
    "cost_per_conversion": {
        "threshold": baseline_cpa * 1.2,  # Не более +20%
        "current": current_cpa
    },
    "quality_score": {
        "threshold": baseline_quality_score - 1,  # Не менее -1
        "current": current_quality_score
    },
    "bounce_rate": {
        "threshold": baseline_bounce_rate * 1.1,  # Не более +10%
        "current": current_bounce_rate
    }
}

# Если guardrail нарушен, останавливаем тест
for metric, values in guardrails.items():
    if values["current"] > values["threshold"]:
        await self.stop_test_early(
            test_id=test_id,
            reason=f"Guardrail violated: {metric}",
            details=values
        )
```


### Шаг 5: Финализация теста и статистический анализ

**5.1 Сбор финальных данных:**
```python
# Получить финальные метрики от всех источников
final_metrics = await self.collect_final_metrics(test_id)

# Структура данных
variants_data = []
for variant in variants:
    data = {
        "variant_id": variant.variant_id,
        "variant_name": variant.name,
        "visitors": final_metrics[variant.variant_id]["visitors"],
        "conversions": final_metrics[variant.variant_id]["conversions"],
        "conversion_rate": final_metrics[variant.variant_id]["conversions"] / final_metrics[variant.variant_id]["visitors"],
        "revenue": final_metrics[variant.variant_id].get("revenue", 0)
    }
    variants_data.append(data)
```

**5.2 Two-proportion z-test:**
```python
# Формула z-теста
def calculate_z_test(control, treatment):
    """
    Z = (p̂₂ - p̂₁) / SE
    SE = √[p̂₁(1-p̂₁)/n₁ + p̂₂(1-p̂₂)/n₂]
    """
    p1 = control["conversion_rate"]
    p2 = treatment["conversion_rate"]
    n1 = control["visitors"]
    n2 = treatment["visitors"]
    
    # Standard error (unpooled)
    se = math.sqrt(
        (p1 * (1 - p1) / n1) + 
        (p2 * (1 - p2) / n2)
    )
    
    # Z-score
    z_score = (p2 - p1) / se
    
    # P-value (two-tailed)
    p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
    
    return {
        "z_score": z_score,
        "p_value": p_value,
        "is_significant": p_value < significance_level
    }

# Применить к данным
control = variants_data[0]  # Control всегда первый
treatment = variants_data[1]  # Treatment второй
z_test_result = calculate_z_test(control, treatment)
```

**5.3 Confidence intervals:**
```python
def calculate_confidence_interval(control, treatment, confidence_level=0.95):
    """
    CI = (p̂₂ - p̂₁) ± Z* × SE_diff
    """
    p1 = control["conversion_rate"]
    p2 = treatment["conversion_rate"]
    n1 = control["visitors"]
    n2 = treatment["visitors"]
    
    # Difference in conversion rates
    diff = p2 - p1
    
    # Standard error of difference
    se_diff = math.sqrt(
        (p1 * (1 - p1) / n1) + 
        (p2 * (1 - p2) / n2)
    )
    
    # Z* for confidence level
    z_star = stats.norm.ppf(1 - (1 - confidence_level) / 2)  # 1.96 for 95%
    
    # Confidence interval
    margin_of_error = z_star * se_diff
    ci_lower = diff - margin_of_error
    ci_upper = diff + margin_of_error
    
    # Relative lift confidence interval
    relative_lift = diff / p1
    relative_ci_lower = ci_lower / p1
    relative_ci_upper = ci_upper / p1
    
    return {
        "absolute_lift": diff,
        "absolute_ci_lower": ci_lower,
        "absolute_ci_upper": ci_upper,
        "relative_lift": relative_lift,
        "relative_ci_lower": relative_ci_lower,
        "relative_ci_upper": relative_ci_upper
    }

ci_result = calculate_confidence_interval(control, treatment)
```

**5.4 Statistical power (post-hoc):**
```python
def calculate_actual_power(control, treatment, significance_level=0.05):
    """
    Рассчитать фактическую мощность теста на основе реальных данных
    """
    p1 = control["conversion_rate"]
    p2 = treatment["conversion_rate"]
    n1 = control["visitors"]
    n2 = treatment["visitors"]
    
    # Effect size (Cohen's h)
    effect_size = 2 * (math.asin(math.sqrt(p2)) - math.asin(math.sqrt(p1)))
    
    # Critical z-value
    z_alpha = stats.norm.ppf(1 - significance_level / 2)
    
    # Non-centrality parameter
    ncp = effect_size * math.sqrt(n1 * n2 / (n1 + n2))
    
    # Power = P(reject H0 | H1 is true)
    power = 1 - stats.norm.cdf(z_alpha - ncp)
    
    return power

actual_power = calculate_actual_power(control, treatment)
```

**5.5 Winner selection:**
```python
# Определить победителя
if z_test_result["is_significant"]:
    # Статистически значимая разница
    if treatment["conversion_rate"] > control["conversion_rate"]:
        winner = treatment
        winner_id = treatment["variant_id"]
    else:
        winner = control
        winner_id = control["variant_id"]
    
    # Проверить business significance
    min_worthwhile_lift = 0.10  # 10% минимальный lift для внедрения
    if abs(ci_result["relative_lift"]) < min_worthwhile_lift:
        # Статистически значимо, но не бизнес-значимо
        winner_status = "statistically_significant_but_not_business_significant"
        recommendation = "No winner - lift too small to justify implementation cost"
    else:
        winner_status = "significant"
        recommendation = f"Deploy winner ({winner['variant_name']}) to 100% of traffic"
else:
    # Нет статистически значимой разницы
    winner = None
    winner_id = None
    winner_status = "no_significant_difference"
    recommendation = "No winner - continue with control variant"
```

### Шаг 6: Формирование результата и рекомендаций

**6.1 Структура результата:**
```python
result = {
    "test_id": test_id,
    "winner": {
        "variant_id": winner_id,
        "variant_name": winner["variant_name"] if winner else None,
        "confidence_level": confidence_level,
        "p_value": z_test_result["p_value"],
        "absolute_lift": ci_result["absolute_lift"],
        "relative_lift": ci_result["relative_lift"],
        "confidence_interval": {
            "lower": ci_result["relative_ci_lower"],
            "upper": ci_result["relative_ci_upper"]
        }
    } if winner else None,
    "variants_performance": variants_data,
    "statistical_analysis": {
        "z_score": z_test_result["z_score"],
        "p_value": z_test_result["p_value"],
        "significance_level": significance_level,
        "is_significant": z_test_result["is_significant"],
        "statistical_power": actual_power,
        "sample_size_reached": True,
        "minimum_duration_met": True
    },
    "test_metadata": {
        "start_date": test_metadata["start_date"],
        "end_date": datetime.now().isoformat(),
        "duration_days": (datetime.now() - datetime.fromisoformat(test_metadata["start_date"])).days,
        "total_visitors": sum(v["visitors"] for v in variants_data),
        "total_conversions": sum(v["conversions"] for v in variants_data)
    },
    "recommendations": [],
    "compliance_check": compliance_result
}
```

**6.2 Генерация рекомендаций:**
```python
recommendations = []

if winner_status == "significant":
    # Победитель найден
    recommendations.append(f"Deploy winner ({winner['variant_name']}) to 100% of traffic")
    
    # Оценка impact
    baseline_conversions = control["conversions"]
    expected_improvement = baseline_conversions * ci_result["relative_lift"]
    expected_revenue = expected_improvement * avg_conversion_value
    
    recommendations.append(
        f"Expected improvement: {ci_result['relative_lift']:.1%} conversion rate"
    )
    recommendations.append(
        f"Estimated monthly impact: +{expected_improvement:.0f} conversions, "
        f"+{expected_revenue:.0f} RUB revenue"
    )
    
    # Gradual rollout
    recommendations.append(
        "Recommended rollout: Week 1 (25%), Week 2 (50%), Week 3 (100%)"
    )
    
elif winner_status == "statistically_significant_but_not_business_significant":
    # Статистически значимо, но lift слишком мал
    recommendations.append(
        f"No winner - lift ({ci_result['relative_lift']:.1%}) below minimum worthwhile ({min_worthwhile_lift:.1%})"
    )
    recommendations.append("Continue with control variant")
    recommendations.append("Consider testing larger changes for bigger impact")
    
else:
    # Нет значимой разницы
    recommendations.append("No winner - no statistically significant difference detected")
    recommendations.append("Continue with control variant")
    
    # Анализ причин
    if actual_power < 0.80:
        recommendations.append(
            f"Test was underpowered (power={actual_power:.2f}, target=0.80). "
            f"Consider increasing sample size or MDE for future tests."
        )
    
    if test_metadata["duration_days"] < 14:
        recommendations.append(
            "Test duration was less than 14 days - may have missed weekly patterns"
        )

result["recommendations"] = recommendations
```

### Шаг 7: Отправка результата и сохранение

**7.1 Отправка результата Orchestrator:**
```python
await event_bus.publish(
    event_type="subagent.task.completed",
    correlation_id=correlation_id,
    task_id=task_id,
    subagent_id="ab-testing-agent",
    payload={
        "status": "success",
        "result": result,
        "metrics": {
            "execution_time_ms": execution_time_ms,
            "tests_completed": 1,
            "variants_tested": len(variants),
            "sample_size_calculated": test_metadata["total_sample_size"],
            "actual_sample_size": result["test_metadata"]["total_visitors"]
        },
        "errors": []
    }
)
```

**7.2 Сохранение в Event Store:**
```python
await event_store.append(
    stream_id=f"ab-test-{test_id}",
    event_type="test.completed",
    data={
        "test_id": test_id,
        "result": result,
        "timestamp": datetime.now().isoformat()
    }
)
```

**7.3 Сохранение в Obsidian vault:**
```python
# Форматировать результат в Markdown
report_md = f"""# A/B Test Report: {test_id}

## Test Overview
- **Test Type:** {test_type}
- **Start Date:** {result['test_metadata']['start_date']}
- **End Date:** {result['test_metadata']['end_date']}
- **Duration:** {result['test_metadata']['duration_days']} days
- **Total Visitors:** {result['test_metadata']['total_visitors']:,}
- **Total Conversions:** {result['test_metadata']['total_conversions']:,}

## Winner
{f"**{result['winner']['variant_name']}** (p={result['winner']['p_value']:.4f})" if result['winner'] else "No winner"}

{f"- **Absolute Lift:** +{result['winner']['absolute_lift']:.4f} ({result['winner']['absolute_lift']*100:.2f} percentage points)" if result['winner'] else ""}
{f"- **Relative Lift:** +{result['winner']['relative_lift']:.2%}" if result['winner'] else ""}
{f"- **95% CI:** [{result['winner']['confidence_interval']['lower']:.2%}, {result['winner']['confidence_interval']['upper']:.2%}]" if result['winner'] else ""}

## Variants Performance

| Variant | Visitors | Conversions | Conversion Rate |
|---------|----------|-------------|-----------------|
{chr(10).join(f"| {v['variant_name']} | {v['visitors']:,} | {v['conversions']:,} | {v['conversion_rate']:.2%} |" for v in result['variants_performance'])}

## Statistical Analysis
- **Z-score:** {result['statistical_analysis']['z_score']:.2f}
- **P-value:** {result['statistical_analysis']['p_value']:.4f}
- **Significance Level:** {result['statistical_analysis']['significance_level']}
- **Is Significant:** {result['statistical_analysis']['is_significant']}
- **Statistical Power:** {result['statistical_analysis']['statistical_power']:.2%}

## Recommendations
{chr(10).join(f"- {rec}" for rec in result['recommendations'])}

## Compliance Check
- **Passed:** {result['compliance_check']['passed']}
{chr(10).join(f"- **Issue:** {issue}" for issue in result['compliance_check']['issues']) if result['compliance_check']['issues'] else ""}
"""

await obsidian.save(
    vault="ads-magister",
    path=f"ab-tests/{test_id}/report.md",
    content=report_md
)
```

### Шаг 8: Автоматическое применение победителя (опционально)

**8.1 Gradual rollout:**
```python
if winner and auto_deploy_enabled:
    # Week 1: 25% traffic to winner
    await self.deploy_winner(
        test_id=test_id,
        winner_variant_id=winner_id,
        traffic_percentage=0.25,
        duration_days=7
    )
    
    # Schedule Week 2: 50% traffic
    await self.schedule_deployment(
        test_id=test_id,
        winner_variant_id=winner_id,
        traffic_percentage=0.50,
        start_date=datetime.now() + timedelta(days=7),
        duration_days=7
    )
    
    # Schedule Week 3: 100% traffic
    await self.schedule_deployment(
        test_id=test_id,
        winner_variant_id=winner_id,
        traffic_percentage=1.00,
        start_date=datetime.now() + timedelta(days=14),
        duration_days=None  # Permanent
    )
```

**8.2 Deployment через Google Ads API:**
```python
async def deploy_winner(self, test_id, winner_variant_id, traffic_percentage):
    # Получить ID объявлений
    winner_ad_id = variant_ads[winner_variant_id]
    loser_ad_ids = [ad_id for vid, ad_id in variant_ads.items() if vid != winner_variant_id]
    
    # Обновить статусы
    if traffic_percentage == 1.0:
        # 100% трафика на победителя - отключить проигравших
        for loser_ad_id in loser_ad_ids:
            await google_ads.update_ad(
                ad_id=loser_ad_id,
                status="PAUSED"
            )
        
        await google_ads.update_ad(
            ad_id=winner_ad_id,
            status="ENABLED"
        )
    else:
        # Частичный rollout - использовать ad rotation
        await google_ads.update_ad_group(
            ad_group_id=ad_group_id,
            ad_rotation_mode="OPTIMIZE",  # Яндекс автоматически распределит
            ads=[
                {"ad_id": winner_ad_id, "weight": traffic_percentage},
                {"ad_id": loser_ad_ids[0], "weight": 1 - traffic_percentage}
            ]
        )
```

**8.3 Мониторинг после deployment:**
```python
# Отслеживать метрики после применения победителя
await self.monitor_post_deployment(
    test_id=test_id,
    winner_variant_id=winner_variant_id,
    baseline_metrics={
        "conversion_rate": control["conversion_rate"],
        "cpa": baseline_cpa,
        "quality_score": baseline_quality_score
    },
    duration_days=14
)

# Если метрики ухудшились - откатить
if post_deployment_metrics["conversion_rate"] < baseline_metrics["conversion_rate"] * 0.95:
    await self.rollback_deployment(test_id, reason="metrics_degraded")
```

---

## 🔧 ИНТЕГРАЦИИ

### Внешние сервисы:

**Google Ads API:**
- API endpoint: `https://googleads.googleapis.com/v16/`
- Аутентификация: OAuth 2.0
- Rate limit: 15,000 operations/day (developer token)
- Документация: https://developers.google.com/google-ads/api/docs/start
- **Операции:**
  - `AdService.MutateAds` - создание/обновление объявлений
  - `AdGroupAdService.MutateAdGroupAds` - управление объявлениями в группах
  - `GoogleAdsService.Search` - получение метрик (impressions, clicks, conversions)
  - `ConversionActionService.MutateConversionActions` - настройка конверсий

**Яндекс.Директ API:**
- API endpoint: `https://api.direct.yandex.com/json/v5/`
- Аутентификация: OAuth token
- Rate limit: 100,000 units/day
- Документация: https://yandex.ru/dev/direct/doc/dg/concepts/about.html
- **Операции:**
  - `ads.add` - создание объявлений
  - `ads.update` - обновление объявлений
  - `ads.suspend` / `ads.resume` - пауза/возобновление
  - `reports.get` - получение статистики

**Яндекс.Метрика API:**
- API endpoint: `https://api-metrika.yandex.net/`
- Аутентификация: OAuth token
- Rate limit: 10 requests/second
- Документация: https://yandex.ru/dev/metrika/
- **Операции:**
  - `stat/v1/data` - получение статистики (visitors, conversions, bounce rate)
  - `management/v1/counter/{counterId}/goals` - управление целями
  - `management/v1/counter/{counterId}/experiments` - эксперименты (Вариокуб)

**Яндекс.Вариокуб:**
- **Важно:** Нет публичного API
- Интеграция через веб-интерфейс Яндекс.Метрики
- Агент отправляет инструкции пользователю для ручной настройки
- Результаты доступны через Метрика API (`experiments` endpoint)

### Внутренние зависимости:

**Обязательные:**
- Event Bus - получение задач, отправка результатов
- Event Store - логирование всех событий теста
- Obsidian vault - сохранение отчётов и инсайтов

**Опциональные:**
- Campaign Manager Agent - получение вариантов для тестирования
- Performance Monitor Agent - baseline метрики
- Brand Analytics Agent - CustDev данные
- Analytics Agent - сезонные паттерны

---

## 📊 МЕТРИКИ УСПЕХА

### Качественные метрики:

**Точность статистического анализа:**
- Метрика: False positive rate (Type I error)
- Целевое значение: ≤ 5% (α = 0.05)
- Как измерять: Доля тестов с p < 0.05 при отсутствии реальной разницы (A/A тесты)

**Полнота тестирования:**
- Метрика: Statistical power (1 - β)
- Целевое значение: ≥ 80%
- Как измерять: Post-hoc power analysis на завершённых тестах

**Compliance rate:**
- Метрика: Доля тестов, прошедших проверку на соответствие ФЗ-38/ФЗ-323
- Целевое значение: 100%
- Как измерять: Количество тестов с `compliance_check.passed = true` / общее количество тестов

### Производительность:

**Скорость:**
- Среднее время расчёта sample size: < 1 секунда
- Среднее время статистического анализа: < 5 секунд
- Среднее время deployment победителя: < 30 секунд

**Надёжность:**
- Success rate: > 95% (тесты завершаются успешно)
- Partial success rate: > 99% (включая частичные результаты)
- Failure rate: < 1% (критические ошибки)

### Бизнес-метрики:

**Влияние на конверсии:**
- Средний lift от победивших вариантов: > 15%
- Доля тестов с победителем: > 40% (не все тесты должны иметь победителя)
- ROI от A/B тестирования: > 300% (выгода от улучшений vs стоимость тестирования)

**Эффективность тестирования:**
- Среднее время до результата: < 21 день (14 дней minimum + запас)
- Доля тестов, достигших sample size: > 90%
- Доля тестов, остановленных досрочно (guardrail violations): < 5%

---


## 🧪 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ

### Пример 1: Успешный тест с победителем

**Входные данные:**
```json
{
  "test_type": "ad_creative",
  "variants": [
    {
      "variant_id": "control",
      "name": "Control",
      "elements": {
        "headline": "Лечение варикоза",
        "description": "Консультация флеболога. Имеются противопоказания. Необходима консультация специалиста.",
        "cta": "Записаться"
      }
    },
    {
      "variant_id": "treatment",
      "name": "Treatment",
      "elements": {
        "headline": "Современные методы лечения варикоза",
        "description": "Опытные флебологи. Имеются противопоказания. Необходима консультация специалиста.",
        "cta": "Получить консультацию"
      }
    }
  ],
  "target_metric": "conversion_rate",
  "baseline_conversion_rate": 0.03,
  "minimum_detectable_effect": 0.15,
  "campaign_id": "campaign-123"
}
```

**Выходные данные:**
```json
{
  "status": "success",
  "result": {
    "test_id": "test-456",
    "winner": {
      "variant_id": "treatment",
      "variant_name": "Treatment",
      "confidence_level": 0.95,
      "p_value": 0.023,
      "absolute_lift": 0.005,
      "relative_lift": 0.167,
      "confidence_interval": {
        "lower": 0.08,
        "upper": 0.25
      }
    },
    "variants_performance": [
      {
        "variant_id": "control",
        "visitors": 10000,
        "conversions": 300,
        "conversion_rate": 0.030
      },
      {
        "variant_id": "treatment",
        "visitors": 10000,
        "conversions": 350,
        "conversion_rate": 0.035
      }
    ],
    "statistical_analysis": {
      "z_score": 2.27,
      "p_value": 0.023,
      "is_significant": true,
      "statistical_power": 0.82
    },
    "recommendations": [
      "Deploy winner (Treatment) to 100% of traffic",
      "Expected improvement: +16.7% conversion rate",
      "Estimated monthly impact: +50 conversions, +500K RUB revenue"
    ]
  }
}
```

### Пример 2: Тест без победителя (нет значимой разницы)

**Входные данные:**
```json
{
  "test_type": "ad_creative",
  "variants": [
    {
      "variant_id": "control",
      "name": "Control",
      "elements": {
        "headline": "Лечение аллергии",
        "cta": "Записаться"
      }
    },
    {
      "variant_id": "treatment",
      "name": "Treatment",
      "elements": {
        "headline": "Избавьтесь от аллергии",
        "cta": "Записаться"
      }
    }
  ],
  "target_metric": "conversion_rate",
  "baseline_conversion_rate": 0.025,
  "campaign_id": "campaign-789"
}
```

**Выходные данные:**
```json
{
  "status": "success",
  "result": {
    "test_id": "test-790",
    "winner": null,
    "variants_performance": [
      {
        "variant_id": "control",
        "visitors": 15000,
        "conversions": 375,
        "conversion_rate": 0.025
      },
      {
        "variant_id": "treatment",
        "visitors": 15000,
        "conversions": 390,
        "conversion_rate": 0.026
      }
    ],
    "statistical_analysis": {
      "z_score": 0.78,
      "p_value": 0.435,
      "is_significant": false,
      "statistical_power": 0.81
    },
    "recommendations": [
      "No winner - no statistically significant difference detected",
      "Continue with control variant",
      "Consider testing larger changes for bigger impact"
    ]
  }
}
```

### Пример 3: Ошибка compliance (нарушение законодательства)

**Входные данные:**
```json
{
  "test_type": "ad_creative",
  "variants": [
    {
      "variant_id": "control",
      "name": "Control",
      "elements": {
        "headline": "Лечение варикоза",
        "description": "Консультация флеболога"
      }
    },
    {
      "variant_id": "treatment",
      "name": "Treatment (ILLEGAL)",
      "elements": {
        "headline": "Гарантируем полное излечение варикоза",
        "description": "100% результат за 3 дня"
      }
    }
  ],
  "target_metric": "conversion_rate",
  "baseline_conversion_rate": 0.03,
  "campaign_id": "campaign-999"
}
```

**Выходные данные:**
```json
{
  "status": "failure",
  "result": null,
  "errors": [
    {
      "code": "COMPLIANCE_VIOLATION",
      "message": "Variants violate medical advertising law (FZ-38, FZ-323)",
      "details": {
        "variant_id": "treatment",
        "issues": [
          "Prohibited: guarantee of treatment results ('Гарантируем полное излечение')",
          "Prohibited: unrealistic expectations ('100% результат')",
          "Prohibited: misleading timeframe ('за 3 дня')",
          "Missing: required disclaimer ('Имеются противопоказания. Необходима консультация специалиста.')",
          "Missing: license information"
        ]
      }
    }
  ]
}
```

### Пример 4: Ошибка недостаточного трафика

**Входные данные:**
```json
{
  "test_type": "ad_creative",
  "variants": [
    {"variant_id": "control", "name": "Control"},
    {"variant_id": "treatment", "name": "Treatment"}
  ],
  "target_metric": "conversion_rate",
  "baseline_conversion_rate": 0.02,
  "minimum_detectable_effect": 0.10,
  "max_duration_days": 28,
  "campaign_id": "campaign-low-traffic"
}
```

**Выходные данные:**
```json
{
  "status": "failure",
  "result": null,
  "errors": [
    {
      "code": "INSUFFICIENT_TRAFFIC",
      "message": "Test requires 85 days, max allowed 28 days",
      "details": {
        "required_sample": 128000,
        "daily_traffic": 1500,
        "estimated_days": 85,
        "max_duration_days": 28,
        "recommendation": "Increase MDE to 15-20% or increase traffic allocation"
      }
    }
  ]
}
```

---

## 🔒 ОБРАБОТКА ОШИБОК

### Типы ошибок:

**Валидация входных данных:**
- Код: `INVALID_INPUT`
- Действие: Вернуть failure сразу
- Retry: Нет
- **Примеры:**
  - Менее 2 вариантов
  - Baseline conversion rate вне диапазона (0, 1)
  - MDE вне диапазона (0, 1)
  - Traffic allocation не суммируется в 1.0

**Compliance violation:**
- Код: `COMPLIANCE_VIOLATION`
- Действие: Вернуть failure с детальным списком нарушений
- Retry: Нет (требуется исправление вариантов)
- **Примеры:**
  - Гарантии результата лечения
  - Отсутствие обязательных disclaimers
  - Запрещённые формулировки

**Недостаточный трафик:**
- Код: `INSUFFICIENT_TRAFFIC`
- Действие: Вернуть failure с рекомендациями
- Retry: Нет (требуется изменение параметров)
- **Рекомендации:**
  - Увеличить MDE (тестировать более крупные изменения)
  - Увеличить max_duration_days
  - Увеличить traffic allocation (больше трафика на тест)

**Ошибка внешнего API:**
- Код: `EXTERNAL_API_ERROR`
- Действие: Retry с exponential backoff
- Retry: До 3 попыток
- **Примеры:**
  - Google Ads API rate limit
  - Яндекс.Директ API timeout
  - Яндекс.Метрика API unavailable

**Guardrail violation:**
- Код: `GUARDRAIL_VIOLATION`
- Действие: Остановить тест досрочно, вернуть partial_success
- Retry: Нет
- **Примеры:**
  - CPA увеличился более чем на 20%
  - Quality Score упал более чем на 1
  - Bounce rate увеличился более чем на 10%

**Timeout:**
- Код: `TIMEOUT`
- Действие: Вернуть partial_success с обработанными данными
- Retry: Нет
- **Примеры:**
  - Тест не достиг sample size за max_duration_days
  - API не отвечает в течение 60 секунд

**Внутренняя ошибка:**
- Код: `INTERNAL_ERROR`
- Действие: Логировать, вернуть failure
- Retry: Нет
- **Примеры:**
  - Ошибка в расчёте z-score
  - Ошибка сохранения в Event Store
  - Ошибка форматирования отчёта

### Graceful degradation:

**При частичном сбое:**
1. Обработать максимум данных
2. Вернуть partial_success
3. Указать, что не удалось обработать
4. Позволить Orchestrator решить, что делать дальше

**Пример partial_success:**
```json
{
  "status": "partial_success",
  "result": {
    "test_id": "test-123",
    "winner": null,
    "variants_performance": [
      {"variant_id": "control", "visitors": 8000, "conversions": 240},
      {"variant_id": "treatment", "visitors": 8000, "conversions": 260}
    ],
    "statistical_analysis": {
      "is_significant": false,
      "note": "Test stopped early due to guardrail violation"
    }
  },
  "errors": [
    {
      "code": "GUARDRAIL_VIOLATION",
      "message": "CPA increased by 25% (threshold: 20%)",
      "details": {
        "baseline_cpa": 1000,
        "current_cpa": 1250,
        "threshold": 1200
      }
    }
  ]
}
```

---

## 🧠 ОБУЧЕНИЕ И АДАПТАЦИЯ

### Источники обучения:

**От Ads Magister:**
- Best practices по A/B тестированию в медицинском маркетинге
- Актуальные изменения в законодательстве (ФЗ-38, ФЗ-323)
- Обновления алгоритмов Google Ads / Яндекс.Директ
- Сезонные паттерны и корректировки

**Из собственного опыта:**
- Успешные тесты (какие элементы работают: tone of voice, CTA, изображения)
- Неудачные тесты (что не сработало и почему)
- Метрики результатов (средний lift, success rate, время до результата)
- Compliance issues (какие формулировки вызывают проблемы)

**Из Obsidian vault:**
- Исторические данные тестов
- Паттерны победителей (что общего у успешных вариантов)
- Корреляции с результатами (какие факторы влияют на успех)
- Инсайты от других агентов (Analytics, Performance Monitor)

### Адаптация:

**Когда адаптироваться:**
- Success rate падает ниже 95%
- Средний lift от победителей падает ниже 10%
- Доля тестов с compliance violations растёт
- Изменяются законодательные требования
- Появляются новые best practices в индустрии

**Как адаптироваться:**
1. Получить обновлённые знания от Ads Magister
2. Протестировать на небольшой выборке (1-2 теста)
3. Сравнить метрики до/после
4. Применить, если улучшение подтверждено (success rate +5%, lift +3%)

**Примеры адаптации:**
- **Compliance rules:** Обновить список запрещённых формулировок при изменении законодательства
- **Sample size calculation:** Скорректировать baseline conversion rates на основе исторических данных
- **MDE recommendations:** Адаптировать рекомендуемый MDE на основе успешности тестов
- **Guardrail thresholds:** Ужесточить или ослабить пороги на основе false positive rate

---

## 📝 ЛОГИРОВАНИЕ

### Что логировать:

**В Event Store (обязательно):**
- Все входящие события (`subagent.task.assigned`)
- Все исходящие события (`subagent.task.completed`)
- Ключевые этапы теста:
  - `test.started` - начало теста
  - `test.daily_metrics` - ежедневные метрики
  - `test.guardrail_violation` - нарушение guardrail
  - `test.completed` - завершение теста
  - `test.winner_deployed` - применение победителя
- Correlation ID для трейсинга

**В Obsidian vault (обязательно):**
- Результаты выполнения (отчёты в Markdown)
- Метрики производительности (execution time, success rate)
- Инсайты и паттерны (что работает, что нет)
- Compliance issues (какие формулировки вызвали проблемы)

**В системные логи (опционально):**
- Debug информация (расчёты sample size, z-score)
- Ошибки и warnings (API errors, timeouts)
- Performance traces (время выполнения каждого шага)

### Формат логов:

```
[YYYY-MM-DD HH:MM:SS] [LEVEL] [ab-testing-agent] [correlation_id] Message
```

**Примеры:**
```
[2026-05-11 10:00:00] [INFO] [ab-testing-agent] [corr-123] Test started: test-456
[2026-05-11 10:00:01] [INFO] [ab-testing-agent] [corr-123] Sample size calculated: 20000 visitors
[2026-05-11 10:00:02] [INFO] [ab-testing-agent] [corr-123] Compliance check passed
[2026-05-15 10:00:00] [INFO] [ab-testing-agent] [corr-123] Test completed: winner=treatment, p=0.023
[2026-05-15 10:00:01] [INFO] [ab-testing-agent] [corr-123] Winner deployed: 25% traffic
```

---

## 🧪 ТЕСТИРОВАНИЕ

### Unit тесты:

**Покрытие:** > 80%

**Обязательные тесты:**
- **Валидация входных данных:**
  - `test_validate_variants_count()` - проверка количества вариантов (2-4)
  - `test_validate_baseline_conversion_rate()` - проверка baseline (0 < rate < 1)
  - `test_validate_traffic_allocation()` - проверка суммы allocation = 1.0
  
- **Sample size calculation:**
  - `test_calculate_sample_size_standard()` - стандартный расчёт
  - `test_calculate_sample_size_low_baseline()` - низкий baseline (2%)
  - `test_calculate_sample_size_high_mde()` - высокий MDE (30%)
  
- **Statistical analysis:**
  - `test_z_test_significant()` - значимая разница (p < 0.05)
  - `test_z_test_not_significant()` - незначимая разница (p > 0.05)
  - `test_confidence_interval()` - расчёт доверительного интервала
  - `test_statistical_power()` - расчёт мощности теста
  
- **Compliance check:**
  - `test_compliance_pass()` - корректные варианты
  - `test_compliance_fail_guarantee()` - гарантии результата
  - `test_compliance_fail_missing_disclaimer()` - отсутствие disclaimer
  
- **Обработка ошибок:**
  - `test_insufficient_traffic()` - недостаточно трафика
  - `test_guardrail_violation()` - нарушение guardrail
  - `test_api_error_retry()` - retry при ошибке API

### Integration тесты:

**Обязательные сценарии:**
- **Получение задачи от Orchestrator:**
  - `test_receive_task_from_orchestrator()` - подписка на события
  - `test_filter_by_subagent_id()` - фильтрация по subagent_id
  
- **Отправка результата Orchestrator:**
  - `test_send_result_success()` - успешный результат
  - `test_send_result_failure()` - ошибка
  
- **Логирование в Event Store:**
  - `test_log_test_started()` - логирование начала теста
  - `test_log_test_completed()` - логирование завершения
  
- **Сохранение в Obsidian vault:**
  - `test_save_report_markdown()` - сохранение отчёта
  - `test_save_metadata()` - сохранение метаданных

### E2E тесты:

**Обязательные сценарии:**
- **Полный цикл успешного теста:**
  - Получение задачи → валидация → расчёт sample size → запуск теста → мониторинг → статистический анализ → отправка результата
  - Проверка: winner определён, p < 0.05, recommendations сгенерированы
  
- **Тест без победителя:**
  - Полный цикл с незначимой разницей (p > 0.05)
  - Проверка: winner = null, recommendations = "No winner"
  
- **Compliance violation:**
  - Попытка запуска теста с запрещёнными формулировками
  - Проверка: status = "failure", errors содержат COMPLIANCE_VIOLATION
  
- **Guardrail violation:**
  - Тест с ухудшением CPA более чем на 20%
  - Проверка: тест остановлен досрочно, status = "partial_success"

---

## 🚀 DEPLOYMENT

### Требования:

**Окружение:**
- Python 3.11+
- Event Bus доступен
- Event Store доступен
- Obsidian vault доступен
- Google Ads API credentials
- Яндекс.Директ API token
- Яндекс.Метрика API token

**Зависимости:**
```
scipy >= 1.11.0          # Statistical functions (z-test, confidence intervals)
numpy >= 1.24.0          # Numerical computations
pandas >= 2.0.0          # Data manipulation
pydantic >= 2.0.0        # Data validation
aiohttp >= 3.8.0         # Async HTTP client
google-ads >= 22.0.0     # Google Ads API
yandex-direct >= 1.0.0   # Яндекс.Директ API (unofficial)
```

**Конфигурация:**
```env
SUBAGENT_ID=ab-testing-agent
EVENT_BUS_URL=...
EVENT_STORE_URL=...
OBSIDIAN_VAULT_PATH=...

# Google Ads API
GOOGLE_ADS_DEVELOPER_TOKEN=...
GOOGLE_ADS_CLIENT_ID=...
GOOGLE_ADS_CLIENT_SECRET=...
GOOGLE_ADS_REFRESH_TOKEN=...
GOOGLE_ADS_CUSTOMER_ID=...

# Яндекс.Директ API
YANDEX_DIRECT_TOKEN=...

# Яндекс.Метрика API
YANDEX_METRIKA_TOKEN=...
YANDEX_METRIKA_COUNTER_ID=...

# A/B Testing defaults
DEFAULT_SIGNIFICANCE_LEVEL=0.05
DEFAULT_STATISTICAL_POWER=0.80
DEFAULT_MINIMUM_DETECTABLE_EFFECT=0.15
DEFAULT_MAX_DURATION_DAYS=28
```

### Мониторинг:

**Метрики для алертов:**
- Success rate < 95% → Warning
- Success rate < 90% → Critical
- Avg execution time > 60 seconds → Warning
- Compliance violation rate > 5% → Warning
- Compliance violation rate > 10% → Critical
- False positive rate > 10% (A/A tests) → Critical

**Дашборд метрик:**
- Количество запущенных тестов (за день/неделю/месяц)
- Доля тестов с победителем (target: > 40%)
- Средний lift от победителей (target: > 15%)
- Среднее время до результата (target: < 21 день)
- Success rate (target: > 95%)
- Compliance violation rate (target: < 1%)

---

## 📚 СВЯЗАННЫЕ ДОКУМЕНТЫ

### Спецификации:
- `ADS_MAGISTER_SPEC.md` - Спецификация родительского Magister
- `ADS_ORCHESTRATOR_SPEC.md` - Спецификация родительского Orchestrator
- `CAMPAIGN_MANAGER_AGENT_SPEC.md` - Источник вариантов для тестирования
- `PERFORMANCE_MONITOR_AGENT_SPEC.md` - Источник baseline метрик
- `ANALYTICS_AGENT_SPEC.md` - Источник сезонных паттернов

### Код:
- `AIM/src/aim/subagents/ads/ab_testing_agent.py` - Реализация
- `AIM/tests/subagents/ads/test_ab_testing_agent.py` - Тесты

### Документация:
- Event Bus API
- Event Store API
- Obsidian integration guide
- Google Ads API documentation: https://developers.google.com/google-ads/api/docs/start
- Яндекс.Директ API documentation: https://yandex.ru/dev/direct/
- Яндекс.Метрика API documentation: https://yandex.ru/dev/metrika/

### Исследования:
- `~/Documents/AB_Testing_Research_20260511/research_summary.md` - Deep research report
- `obsidian/deep-research/raw/2026-05-11-AB_Testing/` - Archived research

### Законодательство:
- Федеральный закон 38-ФЗ "О рекламе": http://www.consultant.ru/document/cons_doc_LAW_58968/
- Федеральный закон 323-ФЗ "Об охране здоровья": http://www.consultant.ru/document/cons_doc_LAW_121895/

---

## 📋 CHANGELOG

### Version 1.0.0 (2026-05-11)

**Создана спецификация на основе:**
- Brief от пользователя (интервью 2026-05-11)
- Deep research (standard mode, 18 источников)
- Шаблон SUBAGENT_SPEC_TEMPLATE.md

**Ключевые особенности:**
- Статистически валидное A/B тестирование (two-proportion z-test, confidence intervals, power analysis)
- Sample size calculation ПЕРЕД тестом (не "запустим и посмотрим")
- Compliance check для медицинской рекламы (ФЗ-38, ФЗ-323)
- Интеграция с Google Ads, Яндекс.Директ, Яндекс.Метрика, Яндекс.Вариокуб
- Автоматическое применение победителей с gradual rollout
- Guardrail metrics для защиты от ухудшения ключевых метрик
- Graceful degradation при частичных сбоях

**Статус:** ✅ Ready for Implementation

---

**Дата создания:** 2026-05-11  
**Автор:** Mikhail Eliseev (via meAI Architect + spec-writer skill)  
**Версия:** 1.0.0  
**Статус:** Ready for Implementation
