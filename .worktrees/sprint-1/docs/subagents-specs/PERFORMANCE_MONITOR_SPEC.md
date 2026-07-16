# Performance Monitor Agent - Спецификация

**Дата:** 2026-05-11  
**Magister:** Ads Magister  
**Приоритет:** P1  
**Статус:** Draft

---

## 🎯 РОЛЬ И НАЗНАЧЕНИЕ

### Основная роль:
Performance Monitor Agent — автономный агент мониторинга производительности рекламных кампаний с итеративным подходом к сбору метрик и детекцией аномалий для своевременного выявления проблем.

### Что делает:
- ✅ Собирает метрики производительности кампаний (CTR, CPC, CPA, конверсии, ROI, Quality Score)
- ✅ Детектирует аномалии в метриках (резкие падения CTR, рост CPA, падение конверсий)
- ✅ Отправляет алерты при отклонениях >20% от baseline
- ✅ Адаптируется к сезонным паттернам медицинского маркетинга
- ✅ Мониторит мульти-платформенные кампании (Яндекс.Директ, VK Ads, myTarget, Telegram Ads, Дзен)

### Что НЕ делает:
- ❌ Не изменяет бюджеты кампаний (это делает Budget Optimizer Agent)
- ❌ Не управляет кампаниями (это делает Campaign Manager Agent)
- ❌ Не анализирует долгосрочные тренды (это делает Analytics Agent)
- ❌ Не работает в режиме real-time 24/7 (использует оптимальную частоту проверок)

### Место в иерархии:
```
Ads Magister
    ↓
Ads Orchestrator
    ↓
Performance Monitor Agent ← вы здесь
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
  "subagent_id": "performance-monitor",
  "payload": {
    "platform": "yandex_direct",
    "campaign_ids": ["123", "456"],
    "check_interval_minutes": 60,
    "metrics": ["ctr", "cpc", "cpa", "conversions", "roi"],
    "baseline_period_days": 30
  }
}
```

**Обязательные параметры:**
- `platform` (string) - Платформа для мониторинга (yandex_direct, vk_ads, mytarget, telegram_ads, dzen)
- `campaign_ids` (array) - Список ID кампаний для мониторинга
- `check_interval_minutes` (int) - Частота проверок в минутах (рекомендуется 30-60)
- `metrics` (array) - Список метрик для мониторинга

**Опциональные параметры:**
- `baseline_period_days` (int) - Период для расчёта baseline (по умолчанию 30 дней)
- `anomaly_threshold_percent` (float) - Порог для детекции аномалий (по умолчанию 20%)
- `alert_channels` (array) - Каналы для алертов (telegram, event_bus)

---

## 📤 ВЫХОДНЫЕ ДАННЫЕ

### Отправляет Orchestrator:

**Формат события:**
```json
{
  "event_type": "subagent.task.completed",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "performance-monitor",
  "payload": {
    "status": "success",
    "result": {
      "platform": "yandex_direct",
      "campaigns_checked": 2,
      "anomalies_detected": 1,
      "anomalies": [
        {
          "campaign_id": "123",
          "metric": "ctr",
          "current_value": 2.1,
          "baseline_value": 3.5,
          "deviation_percent": -40.0,
          "severity": "high",
          "timestamp": "2026-05-11T08:00:00Z"
        }
      ],
      "alerts_sent": 1
    },
    "metrics": {
      "execution_time_ms": 5234,
      "campaigns_processed": 2,
      "api_calls_made": 4
    },
    "errors": []
  }
}
```

**Структура результата:**
- `campaigns_checked` (int) - Количество проверенных кампаний
- `anomalies_detected` (int) - Количество обнаруженных аномалий
- `anomalies` (array) - Список аномалий с деталями
- `alerts_sent` (int) - Количество отправленных алертов

**Метрики:**
- `execution_time_ms` - Время выполнения в миллисекундах
- `campaigns_processed` - Количество обработанных кампаний
- `api_calls_made` - Количество вызовов API платформ

---

## 🔄 АЛГОРИТМ РАБОТЫ

### Шаг 1: Получение задачи и валидация
1. Подписаться на события `subagent.task.assigned`
2. Фильтровать по `subagent_id == "performance-monitor"`
3. Валидировать входные параметры:
   - Проверить наличие обязательных параметров
   - Проверить валидность platform (поддерживаемые платформы)
   - Проверить валидность campaign_ids (не пустой массив)
   - Проверить валидность check_interval_minutes (>0)

### Шаг 2: Расчёт baseline для метрик
1. Получить исторические данные за baseline_period_days (по умолчанию 30 дней)
2. Рассчитать статистические показатели для каждой метрики:
   - Среднее значение (mean)
   - Стандартное отклонение (std_dev)
   - Минимум и максимум
3. Учесть сезонные паттерны:
   - День недели (понедельник vs пятница)
   - Время месяца (начало vs конец)
   - Медицинская сезонность (грипп зимой, аллергии весной)
4. Сохранить baseline в памяти для сравнения

**Пример расчёта baseline:**
```python
def calculate_baseline(historical_data, metric):
    # Фильтруем по дню недели (если сегодня понедельник, берём только понедельники)
    day_of_week = datetime.now().weekday()
    filtered_data = [d for d in historical_data if d['day_of_week'] == day_of_week]
    
    # Рассчитываем статистику
    values = [d[metric] for d in filtered_data]
    mean = sum(values) / len(values)
    std_dev = calculate_std_dev(values, mean)
    
    # Baseline = mean ± 2 * std_dev (95% confidence interval)
    return {
        'mean': mean,
        'std_dev': std_dev,
        'lower_bound': mean - 2 * std_dev,
        'upper_bound': mean + 2 * std_dev
    }
```

### Шаг 3: Сбор текущих метрик
1. Для каждой платформы вызвать соответствующий API:
   - Яндекс.Директ: `/api/v5/reports` (статистика кампаний)
   - VK Ads: `/api/v2/statistics/campaigns` (метрики кампаний)
   - myTarget: `/api/v2/statistics/campaigns` (статистика)
   - Telegram Ads: `/api/v1/stats` (метрики)
   - Дзен: `/api/v1/campaigns/stats` (статистика)
2. Обработать ответы API:
   - Нормализовать данные (привести к единому формату)
   - Извлечь нужные метрики (CTR, CPC, CPA, конверсии, ROI)
   - Обработать ошибки API (retry с exponential backoff)
3. Сохранить текущие метрики для сравнения

**Пример нормализации данных:**
```python
def normalize_metrics(platform, raw_data):
    if platform == 'yandex_direct':
        return {
            'ctr': raw_data['Ctr'],
            'cpc': raw_data['AvgCpc'],
            'cpa': raw_data['CostPerConversion'],
            'conversions': raw_data['Conversions'],
            'roi': raw_data['Revenue'] / raw_data['Cost'] if raw_data['Cost'] > 0 else 0
        }
    elif platform == 'vk_ads':
        return {
            'ctr': raw_data['ctr'],
            'cpc': raw_data['spent'] / raw_data['clicks'] if raw_data['clicks'] > 0 else 0,
            'cpa': raw_data['spent'] / raw_data['conversions'] if raw_data['conversions'] > 0 else 0,
            'conversions': raw_data['conversions'],
            'roi': raw_data['revenue'] / raw_data['spent'] if raw_data['spent'] > 0 else 0
        }
    # ... другие платформы
```

### Шаг 4: Детекция аномалий
1. Для каждой метрики сравнить текущее значение с baseline:
   - Рассчитать отклонение: `deviation = (current - baseline_mean) / baseline_mean * 100`
   - Проверить выход за пределы: `current < lower_bound OR current > upper_bound`
   - Определить severity на основе отклонения:
     - `low`: 20-30% отклонение
     - `medium`: 30-50% отклонение
     - `high`: >50% отклонение
2. Применить фильтры для снижения false positives:
   - Игнорировать аномалии в первые 24 часа после запуска кампании
   - Учитывать сезонные паттерны (например, понедельник vs пятница)
   - Проверять стабильность аномалии (2-3 проверки подряд)
3. Сохранить обнаруженные аномалии

**Алгоритм детекции аномалий:**
```python
def detect_anomalies(current_metrics, baseline, threshold_percent=20):
    anomalies = []
    
    for metric, current_value in current_metrics.items():
        baseline_mean = baseline[metric]['mean']
        lower_bound = baseline[metric]['lower_bound']
        upper_bound = baseline[metric]['upper_bound']
        
        # Рассчитываем отклонение
        deviation = ((current_value - baseline_mean) / baseline_mean) * 100
        
        # Проверяем выход за пределы
        if current_value < lower_bound or current_value > upper_bound:
            # Определяем severity
            abs_deviation = abs(deviation)
            if abs_deviation >= 50:
                severity = 'high'
            elif abs_deviation >= 30:
                severity = 'medium'
            else:
                severity = 'low'
            
            anomalies.append({
                'metric': metric,
                'current_value': current_value,
                'baseline_value': baseline_mean,
                'deviation_percent': deviation,
                'severity': severity,
                'timestamp': datetime.now().isoformat()
            })
    
    return anomalies
```

**Статистические методы детекции:**
- **Z-score**: Количество стандартных отклонений от среднего
  - Формула: `z = (x - μ) / σ`
  - Порог: |z| > 2.5 (99% confidence interval)
  - Подходит для стабильных метрик без сезонности
  
- **ARIMA (AutoRegressive Integrated Moving Average)**: Модель временных рядов
  - Учитывает тренды и сезонность
  - Лучше для циклических данных (недельные паттерны)
  - Требует чистых исторических данных
  
- **Isolation Forest**: ML алгоритм для изоляции аномалий
  - Не требует нормального распределения
  - Хорошо работает с многомерными данными
  - Требует обучения на исторических данных

**Выбор метода:**
- Для простых метрик (CTR, CPC) → Z-score
- Для метрик с сезонностью (конверсии по дням недели) → ARIMA
- Для комплексного анализа нескольких метрик → Isolation Forest

### Шаг 5: Отправка алертов
1. Для каждой обнаруженной аномалии:
   - Сформировать сообщение алерта с деталями
   - Определить каналы для отправки (Telegram, Event Bus)
   - Отправить алерт через соответствующий канал
2. Логировать отправленные алерты в Event Store
3. Обновить счётчик alerts_sent

**Формат алерта для Telegram:**
```
🚨 Аномалия в кампании!

Платформа: Яндекс.Директ
Кампания: #123 "Весенняя акция"
Метрика: CTR
Текущее значение: 2.1%
Baseline: 3.5%
Отклонение: -40.0%
Severity: HIGH

Рекомендация: Проверить креативы и таргетинг
```

**Формат события для Event Bus:**
```json
{
  "event_type": "performance.anomaly.detected",
  "correlation_id": "uuid",
  "subagent_id": "performance-monitor",
  "payload": {
    "platform": "yandex_direct",
    "campaign_id": "123",
    "metric": "ctr",
    "current_value": 2.1,
    "baseline_value": 3.5,
    "deviation_percent": -40.0,
    "severity": "high",
    "timestamp": "2026-05-11T08:00:00Z",
    "recommendation": "Check creatives and targeting"
  }
}
```

### Шаг 6: Формирование результата
1. Собрать результаты обработки:
   - Количество проверенных кампаний
   - Количество обнаруженных аномалий
   - Список аномалий с деталями
   - Количество отправленных алертов
2. Рассчитать метрики выполнения:
   - Время выполнения (execution_time_ms)
   - Количество обработанных кампаний (campaigns_processed)
   - Количество вызовов API (api_calls_made)
3. Сформировать событие результата

### Шаг 7: Отправка результата
1. Отправить событие `subagent.task.completed` в Event Bus
2. Логировать результат в Event Store
3. Сохранить метрики в Obsidian vault для обучения

---

## 🔧 ИНТЕГРАЦИИ

### Внешние сервисы:

**Яндекс.Директ API:**
- API endpoint: `https://api.direct.yandex.com/json/v5/reports`
- Аутентификация: OAuth 2.0 token
- Rate limit: 10 запросов/секунду, 100,000 запросов/день
- Стоимость: Бесплатно (в рамках лимитов)
- Документация: https://yandex.ru/dev/direct/doc/reports/reports.html
- Метрики: Impressions, Clicks, Ctr, AvgCpc, Cost, Conversions, CostPerConversion, Revenue, ROI
- Особенности:
  - Данные доступны с задержкой ~15 минут
  - Финализация метрик через 24 часа
  - Spend данные финализируются через 3 дня

**VK Ads API:**
- API endpoint: `https://ads.vk.ru/api/v2/statistics/campaigns`
- Аутентификация: Access token
- Rate limit: 3 запроса/секунду
- Стоимость: Бесплатно
- Документация: https://ads.vk.ru/help/partner/partner_api/partner_statistics_api
- Метрики: shows, clicks, ctr, amount, cpm, conversions
- Особенности:
  - Статистика за период до 92 дней
  - Максимум 200 объектов в одном запросе

**myTarget API:**
- API endpoint: `https://target.my.com/api/v2/statistics/campaigns/day.json`
- Аутентификация: Access token
- Rate limit: Не указан явно (рекомендуется 1-2 запроса/секунду)
- Стоимость: Бесплатно
- Документация: https://target.my.com/help/advertisers/api_arrangement/en
- Метрики: shows, clicks, ctr, spent, conversions
- Особенности:
  - Статистика по дням
  - Поддержка geo-статистики

**Telegram Ads API:**
- API endpoint: `https://ads.telegram.org/api/v1/stats`
- Аутентификация: API key
- Rate limit: 60 запросов/минуту
- Стоимость: Бесплатно
- Документация: https://ads.telegram.org/api
- Метрики: impressions, clicks, ctr, spend, conversions
- Особенности:
  - Near real-time данные (обновление каждые ~15 минут)
  - Максимум 30 дней в одном запросе

**Дзен API:**
- API endpoint: `https://dzen.ru/api/v1/campaigns/stats`
- Аутентификация: OAuth 2.0
- Rate limit: Не указан явно
- Стоимость: Бесплатно
- Документация: https://yandex.ru/dev/zen/doc/
- Метрики: views, clicks, ctr, spent
- Особенности:
  - Статистика по дням
  - Ограниченный набор метрик

### Внутренние зависимости:

- **Event Bus** (обязательно) - для получения задач и отправки результатов
- **Event Store** (обязательно) - для логирования всех событий
- **Obsidian vault** (обязательно) - для сохранения метрик и обучения
- **Budget Optimizer Agent** (опционально) - получатель алертов об аномалиях
- **Analytics Agent** (опционально) - получатель метрик для агрегации
- **Telegram Bot API** (опционально) - для отправки алертов в Telegram

---

## 📊 МЕТРИКИ УСПЕХА

### Качественные метрики:

**Точность детекции аномалий:**
- Метрика: Precision (доля истинных аномалий среди обнаруженных)
- Целевое значение: > 80%
- Как измерять: `True Positives / (True Positives + False Positives)`
- Benchmark: Google Analytics anomaly detection достигает 85-90% precision

**Полнота детекции:**
- Метрика: Recall (доля обнаруженных аномалий среди всех реальных)
- Целевое значение: > 90%
- Как измерять: `True Positives / (True Positives + False Negatives)`
- Benchmark: Adobe Analytics anomaly detection достигает 92-95% recall

**Своевременность алертов:**
- Метрика: Time to detect (время от возникновения аномалии до алерта)
- Целевое значение: < 60 минут
- Как измерять: `Alert timestamp - Anomaly start timestamp`
- Benchmark: Trackingplan обнаруживает аномалии в течение 30-60 минут

### Производительность:

**Скорость:**
- Среднее время выполнения: < 30 секунд (для 10 кампаний)
- 95-й перцентиль: < 60 секунд
- Максимальное время: < 120 секунд

**Надёжность:**
- Success rate: > 95%
- Partial success rate: > 99% (при частичном сбое API одной платформы)
- Failure rate: < 1%

**Эффективность API:**
- API calls per check: < 5 (для 10 кампаний)
- API error rate: < 5%
- Retry success rate: > 90%

### Бизнес-метрики:

**Влияние на прибыль:**
- Предотвращённые потери бюджета: > $1000/месяц (за счёт раннего обнаружения проблем)
- ROI мониторинга: > 10:1 (экономия на предотвращённых потерях vs стоимость API calls)
- Время реакции на проблемы: < 1 час (vs 24+ часов без мониторинга)

**Операционная эффективность:**
- Снижение ручного мониторинга: > 80% (автоматизация проверок)
- False positive rate: < 20% (не более 1 ложного алерта на 5 реальных)
- Alert fatigue prevention: < 5 алертов/день (не перегружать команду)

---

## 🧪 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ

### Пример 1: Успешное выполнение (аномалия обнаружена)

**Входные данные:**
```json
{
  "platform": "yandex_direct",
  "campaign_ids": ["123", "456"],
  "check_interval_minutes": 60,
  "metrics": ["ctr", "cpc", "cpa", "conversions"],
  "baseline_period_days": 30,
  "anomaly_threshold_percent": 20
}
```

**Выходные данные:**
```json
{
  "status": "success",
  "result": {
    "platform": "yandex_direct",
    "campaigns_checked": 2,
    "anomalies_detected": 1,
    "anomalies": [
      {
        "campaign_id": "123",
        "metric": "ctr",
        "current_value": 2.1,
        "baseline_value": 3.5,
        "deviation_percent": -40.0,
        "severity": "high",
        "timestamp": "2026-05-11T08:00:00Z"
      }
    ],
    "alerts_sent": 1
  },
  "metrics": {
    "execution_time_ms": 5234,
    "campaigns_processed": 2,
    "api_calls_made": 2
  }
}
```

### Пример 2: Успешное выполнение (аномалий нет)

**Входные данные:**
```json
{
  "platform": "vk_ads",
  "campaign_ids": ["789"],
  "check_interval_minutes": 30,
  "metrics": ["ctr", "cpc"],
  "baseline_period_days": 30
}
```

**Выходные данные:**
```json
{
  "status": "success",
  "result": {
    "platform": "vk_ads",
    "campaigns_checked": 1,
    "anomalies_detected": 0,
    "anomalies": [],
    "alerts_sent": 0
  },
  "metrics": {
    "execution_time_ms": 2100,
    "campaigns_processed": 1,
    "api_calls_made": 1
  }
}
```

### Пример 3: Частичный успех (одна платформа недоступна)

**Входные данные:**
```json
{
  "platform": "mytarget",
  "campaign_ids": ["111", "222"],
  "check_interval_minutes": 60,
  "metrics": ["ctr", "cpc", "conversions"]
}
```

**Выходные данные:**
```json
{
  "status": "partial_success",
  "result": {
    "platform": "mytarget",
    "campaigns_checked": 1,
    "anomalies_detected": 0,
    "anomalies": [],
    "alerts_sent": 0
  },
  "metrics": {
    "execution_time_ms": 8500,
    "campaigns_processed": 1,
    "api_calls_made": 4
  },
  "errors": [
    {
      "code": "API_TIMEOUT",
      "message": "Campaign 222: API request timed out after 3 retries",
      "details": {
        "campaign_id": "222",
        "platform": "mytarget",
        "retry_count": 3
      }
    }
  ]
}
```

### Пример 4: Ошибка (невалидные параметры)

**Входные данные:**
```json
{
  "platform": "unknown_platform",
  "campaign_ids": [],
  "check_interval_minutes": -10
}
```

**Выходные данные:**
```json
{
  "status": "failure",
  "result": null,
  "metrics": {
    "execution_time_ms": 50,
    "campaigns_processed": 0,
    "api_calls_made": 0
  },
  "errors": [
    {
      "code": "INVALID_INPUT",
      "message": "Validation failed",
      "details": {
        "platform": "Unsupported platform: unknown_platform",
        "campaign_ids": "campaign_ids cannot be empty",
        "check_interval_minutes": "check_interval_minutes must be positive"
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
- Примеры:
  - Пустой массив campaign_ids
  - Неподдерживаемая платформа
  - Отрицательный check_interval_minutes

**Ошибка внешнего API:**
- Код: `EXTERNAL_API_ERROR`
- Действие: Retry с exponential backoff (1s, 2s, 4s)
- Retry: До 3 попыток
- Примеры:
  - HTTP 500 (Internal Server Error)
  - HTTP 503 (Service Unavailable)
  - Network timeout

**Rate limit:**
- Код: `RATE_LIMIT_EXCEEDED`
- Действие: Wait и retry после указанного времени
- Retry: До 2 попыток
- Примеры:
  - HTTP 429 (Too Many Requests)
  - Яндекс.Директ: "RESOURCE_TEMPORARILY_EXHAUSTED"
  - VK Ads: Rate limit 3 req/sec

**Timeout:**
- Код: `API_TIMEOUT`
- Действие: Вернуть partial_success с обработанными кампаниями
- Retry: Нет (уже было 3 попытки)
- Примеры:
  - API не ответил за 30 секунд
  - Сетевой timeout

**Недостаточно данных для baseline:**
- Код: `INSUFFICIENT_DATA`
- Действие: Пропустить детекцию аномалий для этой кампании
- Retry: Нет
- Примеры:
  - Кампания запущена менее 7 дней назад
  - Нет исторических данных

**Внутренняя ошибка:**
- Код: `INTERNAL_ERROR`
- Действие: Логировать, вернуть failure
- Retry: Нет
- Примеры:
  - Ошибка парсинга JSON
  - Ошибка расчёта статистики
  - Ошибка записи в Event Store

### Graceful degradation:

При частичном сбое:
1. Обработать максимум кампаний (пропустить проблемные)
2. Вернуть partial_success с результатами
3. Указать, какие кампании не удалось обработать
4. Отправить алерты для успешно обработанных кампаний
5. Логировать ошибки для анализа

**Пример graceful degradation:**
```python
def monitor_campaigns(campaign_ids, platform):
    results = []
    errors = []
    
    for campaign_id in campaign_ids:
        try:
            metrics = fetch_metrics(campaign_id, platform)
            baseline = calculate_baseline(campaign_id)
            anomalies = detect_anomalies(metrics, baseline)
            results.append({
                'campaign_id': campaign_id,
                'anomalies': anomalies
            })
        except APIError as e:
            errors.append({
                'campaign_id': campaign_id,
                'error': str(e)
            })
            continue  # Продолжаем с следующей кампанией
    
    # Возвращаем partial_success если есть и результаты, и ошибки
    if results and errors:
        return 'partial_success', results, errors
    elif results:
        return 'success', results, []
    else:
        return 'failure', [], errors
```

---

## 🧠 ОБУЧЕНИЕ И АДАПТАЦИЯ

### Источники обучения:

**От Ads Magister:**
- Best practices по мониторингу рекламных кампаний
- Актуальные пороги для детекции аномалий
- Обновления алгоритмов детекции
- Новые метрики для отслеживания

**Из собственного опыта:**
- Успешные кейсы детекции (true positives)
- Ложные срабатывания (false positives)
- Пропущенные аномалии (false negatives)
- Метрики точности и полноты

**Из Obsidian vault:**
- Исторические данные метрик
- Паттерны аномалий (сезонные, платформенные)
- Корреляции между метриками
- Эффективность разных методов детекции

### Адаптация:

**Когда адаптироваться:**
- Precision падает ниже 80% (слишком много false positives)
- Recall падает ниже 90% (пропускаем реальные аномалии)
- Появляются новые сезонные паттерны
- Изменяются характеристики платформ (новые метрики, API changes)

**Как адаптироваться:**
1. **Обновление baseline:**
   - Пересчитать baseline с учётом новых данных
   - Учесть новые сезонные паттерны
   - Обновить пороги детекции
   
2. **Настройка порогов:**
   - Увеличить порог при высоком false positive rate
   - Уменьшить порог при высоком false negative rate
   - Адаптировать пороги для разных платформ
   
3. **Улучшение алгоритмов:**
   - Переключиться на более сложный метод (Z-score → ARIMA)
   - Добавить ML модель для детекции (Isolation Forest)
   - Учесть корреляции между метриками

**Пример адаптации порогов:**
```python
def adapt_thresholds(historical_performance):
    precision = calculate_precision(historical_performance)
    recall = calculate_recall(historical_performance)
    
    current_threshold = get_current_threshold()
    
    if precision < 0.8:  # Слишком много false positives
        new_threshold = current_threshold * 1.1  # Увеличиваем порог на 10%
    elif recall < 0.9:  # Пропускаем реальные аномалии
        new_threshold = current_threshold * 0.9  # Уменьшаем порог на 10%
    else:
        new_threshold = current_threshold  # Оставляем как есть
    
    update_threshold(new_threshold)
    log_adaptation(precision, recall, current_threshold, new_threshold)
```

---

## 📝 ЛОГИРОВАНИЕ

### Что логировать:

**В Event Store (обязательно):**
- Все входящие события (`subagent.task.assigned`)
- Все исходящие события (`subagent.task.completed`, `performance.anomaly.detected`)
- Correlation ID для трейсинга
- Timestamp каждого события

**В Obsidian vault (обязательно):**
- Результаты мониторинга (метрики, аномалии)
- Baseline для каждой кампании
- Метрики производительности (execution_time, api_calls)
- Инсайты и паттерны (сезонность, корреляции)

**В системные логи (опционально):**
- Debug информация (API requests/responses)
- Ошибки и warnings
- Performance traces (время выполнения каждого шага)

### Формат логов:

```
[2026-05-11 08:00:00] [INFO] [performance-monitor] [corr-123] Started monitoring 2 campaigns on yandex_direct
[2026-05-11 08:00:05] [DEBUG] [performance-monitor] [corr-123] Fetched metrics for campaign 123: CTR=2.1%, CPC=$0.50
[2026-05-11 08:00:10] [WARNING] [performance-monitor] [corr-123] Anomaly detected: campaign 123, CTR dropped 40%
[2026-05-11 08:00:15] [INFO] [performance-monitor] [corr-123] Alert sent to Telegram
[2026-05-11 08:00:20] [INFO] [performance-monitor] [corr-123] Completed monitoring: 2 campaigns, 1 anomaly, 1 alert
```

---

## 🧪 ТЕСТИРОВАНИЕ

### Unit тесты:

**Покрытие:** > 80%

**Обязательные тесты:**
- Валидация входных данных (валидные/невалидные параметры)
- Расчёт baseline (с разными наборами данных)
- Детекция аномалий (с известными аномалиями)
- Нормализация данных (для каждой платформы)
- Обработка ошибок API (timeout, rate limit, 500)
- Формирование алертов (Telegram, Event Bus)

### Integration тесты:

**Обязательные сценарии:**
- Получение задачи от Orchestrator
- Вызов API платформ (с mock данными)
- Отправка результата Orchestrator
- Логирование в Event Store
- Сохранение в Obsidian vault
- Отправка алертов в Telegram

### E2E тесты:

**Обязательные сценарии:**
- Полный цикл: задача → сбор метрик → детекция → алерт → результат
- Обработка аномалий (с реальными данными)
- Graceful degradation (при частичном сбое API)
- Адаптация порогов (при изменении precision/recall)

---

## 🚀 DEPLOYMENT

### Требования:

**Окружение:**
- Python 3.11+
- Event Bus доступен
- Event Store доступен
- Obsidian vault доступен
- Доступ к API платформ (токены, ключи)

**Зависимости:**
- `httpx >= 0.24.0` - для HTTP запросов к API
- `pydantic >= 2.0.0` - для валидации данных
- `numpy >= 1.24.0` - для статистических расчётов
- `scipy >= 1.10.0` - для расчёта Z-score
- `statsmodels >= 0.14.0` - для ARIMA моделей
- `scikit-learn >= 1.3.0` - для Isolation Forest

**Конфигурация:**
```env
SUBAGENT_ID=performance-monitor
EVENT_BUS_URL=...
EVENT_STORE_URL=...
OBSIDIAN_VAULT_PATH=...

# API credentials
YANDEX_DIRECT_TOKEN=...
VK_ADS_TOKEN=...
MYTARGET_TOKEN=...
TELEGRAM_ADS_API_KEY=...
DZEN_TOKEN=...

# Telegram bot
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...

# Monitoring settings
DEFAULT_CHECK_INTERVAL_MINUTES=60
DEFAULT_BASELINE_PERIOD_DAYS=30
DEFAULT_ANOMALY_THRESHOLD_PERCENT=20
```

### Мониторинг:

**Метрики для алертов:**
- Precision < 80% → Warning
- Recall < 90% → Warning
- Success rate < 95% → Critical
- Avg execution time > 60 seconds → Warning
- API error rate > 10% → Critical

---

## 📚 СВЯЗАННЫЕ ДОКУМЕНТЫ

### Спецификации:
- `ADS_MAGISTER_SPEC.md` - Спецификация родительского Magister
- `ADS_ORCHESTRATOR_SPEC.md` - Спецификация родительского Orchestrator
- `BUDGET_OPTIMIZER_SPEC.md` - Спецификация Budget Optimizer Agent (получатель алертов)
- `ANALYTICS_AGENT_SPEC.md` - Спецификация Analytics Agent (получатель метрик)

### Код:
- `AIM/src/aim/subagents/ads/performance_monitor.py` - Реализация
- `AIM/tests/subagents/ads/test_performance_monitor.py` - Тесты

### Документация:
- Event Bus API
- Event Store API
- Obsidian integration guide
- Яндекс.Директ API documentation
- VK Ads API documentation
- myTarget API documentation

---

**Дата создания:** 2026-05-11  
**Автор:** Mikhail Eliseev (via meAI Architect)  
**Версия:** 1.0  
**Статус:** Draft
