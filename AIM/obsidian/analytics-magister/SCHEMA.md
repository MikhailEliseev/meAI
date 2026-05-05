---
name: Analytics Magister
type: magister
specialization: analytics
created: 2026-05-05
status: active
---

# Analytics Magister Schema

## Роль
Магистр аналитики и статистики - координирует сбор, обработку и анализ данных из всех маркетинговых каналов.

## Специализация
- Сбор данных из Яндекс.Метрики, Google Analytics, рекламных кабинетов
- Обработка и маркировка данных
- Анализ эффективности кампаний
- Генерация инсайтов для стратегических решений

## Субагенты (4)

### 1. Data Collector Agent
**Задача:** Сбор данных из всех источников
**Источники:**
- Яндекс.Метрика
- Google Analytics
- Яндекс.Директ
- Google Ads
- VK Ads
- Facebook Ads

**Метрики:**
- Traffic: sessions, users, pageviews, bounce_rate
- Conversions: goals, transactions, revenue, conversion_rate
- Campaigns: impressions, clicks, ctr, cpc, cpa, roas
- Engagement: avg_session_duration, pages_per_session, return_rate

### 2. Data Processor Agent
**Задача:** Обработка, маркировка, нормализация данных
**Функции:**
- Очистка данных от аномалий
- Маркировка по источникам и кампаниям
- Нормализация форматов
- Агрегация по периодам
- Сохранение в единый формат

### 3. Performance Analyzer Agent
**Задача:** Анализ эффективности кампаний
**Функции:**
- Сравнение периодов (week-over-week, month-over-month)
- Анализ ROI и ROAS по каналам
- Выявление трендов
- Определение лучших/худших кампаний
- Расчёт attribution моделей

### 4. Insights Generator Agent
**Задача:** Генерация инсайтов и рекомендаций
**Функции:**
- Выявление паттернов и аномалий
- Генерация actionable рекомендаций
- Прогнозирование трендов
- Определение точек роста
- Формирование стратегических выводов

## Возможности (Capabilities)
- collect_data - сбор данных из источников
- analyze_performance - анализ эффективности
- generate_report - генерация отчётов
- get_insights - получение инсайтов
- track_metrics - отслеживание метрик
- compare_periods - сравнение периодов
- identify_trends - выявление трендов
- provide_recommendations - предоставление рекомендаций

## Интеграция

### Event Bus
**Подписки:**
- `operator.task.analytics.*` - задачи от Operator
- `*.campaign.completed` - завершение кампаний
- `*.data.updated` - обновление данных

**Публикации:**
- `analytics.report_generated` - отчёт сгенерирован
- `analytics.insight_found` - найден инсайт
- `analytics.alert` - критическое изменение метрик

### Другие Magisters
- **SEO Magister:** предоставляет данные по органическому трафику
- **Content Magister:** предоставляет данные по контенту
- **Ads Magister:** предоставляет данные по рекламным кампаниям
- **CI System:** использует аналитику для конкурентного анализа

## Хранение данных

### Obsidian Vault
`AIM/obsidian/analytics-magister/`
- raw/ - сырые данные от субагентов
- wiki/ - обработанные инсайты и отчёты
- decisions/ - стратегические решения на основе данных

### Database
`AIM/data/analytics/`
- metrics.db - метрики по периодам
- reports/ - сгенерированные отчёты (JSON)
- insights/ - найденные инсайты

## Workflow

1. **Сбор данных** (Data Collector)
   - Подключение к API источников
   - Загрузка метрик за период
   - Сохранение в raw/

2. **Обработка** (Data Processor)
   - Очистка и нормализация
   - Маркировка и агрегация
   - Сохранение в БД

3. **Анализ** (Performance Analyzer)
   - Расчёт показателей
   - Сравнение периодов
   - Выявление трендов

4. **Инсайты** (Insights Generator)
   - Генерация выводов
   - Формирование рекомендаций
   - Создание отчётов

## Метрики производительности
- Количество обработанных источников
- Частота обновления данных
- Точность прогнозов
- Количество сгенерированных инсайтов
- Время генерации отчётов

## Примеры задач

### Ежедневный мониторинг
```python
{
    "type": "collect_data",
    "sources": ["yandex_metrika", "google_analytics"],
    "date_range": {"start": "yesterday", "end": "today"}
}
```

### Анализ эффективности кампании
```python
{
    "type": "analyze_performance",
    "period": "last_month",
    "campaigns": ["yandex_direct_campaign_1"],
    "compare_with": "previous_month"
}
```

### Генерация месячного отчёта
```python
{
    "type": "generate_report",
    "report_type": "monthly",
    "period": "last_month",
    "recipients": ["ceo@example.com"]
}
```

### Получение инсайтов
```python
{
    "type": "get_insights",
    "focus_area": "conversion_optimization"
}
```
