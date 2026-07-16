# Бриф: Analytics Agent

**Дата:** 2026-05-11  
**Приоритет:** P1  
**Родительский Magister:** Ads Magister

## Назначение

Комплексный аналитический агент для агрегации метрик, построения дашбордов и предиктивной аналитики. Собирает данные от всех агентов (Performance Monitor, Budget Optimizer, Campaign Manager), создаёт единую картину производительности и предоставляет инсайты для принятия решений.

## Контекст и специфика

**Основные функции:**
- Агрегация метрик от всех агентов Ads Magister
- Построение дашбордов и визуализация данных
- Предиктивная аналитика и прогнозирование трендов
- Экспорт отчётов в множественных форматах

**Метрики для отслеживания:**
- **Эффективность рекламы:** ROI, CPA, конверсии, CTR, Quality Score
- **Жизненный цикл пациента:** LTV, CAC, retention rate, referral rate
- **Финансовые метрики:** Бюджет, расход, темп расходования, budget utilization
- **Производительность агентов:** Execution time, success rate, error rate

**Форматы отчётов:**
- JSON для других агентов (автоматическая обработка)
- Dashboard в Obsidian (Markdown таблицы и графики)
- Excel/CSV экспорт для ручного анализа
- Множественные форматы для разных целей

**Частота агрегации:**
- Раз в день (ежедневные сводки и отчёты)
- По запросу (ad-hoc анализ)

**Медицинская специфика:**
- Сезонные паттерны (грипп зимой, аллергии весной, косметология перед летом)
- LTV оптимизация (пациенты возвращаются)
- Geo-специфичное бюджетирование (разные регионы = разная стоимость)
- Referral value (пациенты приводят других пациентов)

## Интеграции

**Входные данные:**
- Performance Monitor Agent — метрики производительности кампаний
- Budget Optimizer Agent — данные об оптимизации бюджетов
- Campaign Manager Agent — контекст кампаний и изменения
- Event Store — исторические данные всех событий

**Выходные данные:**
- Ads Magister — агрегированные отчёты и инсайты
- Obsidian vault — дашборды и визуализация
- Файловая система — экспорт в Excel/CSV
- Другие агенты — JSON данные для автоматической обработки

**Связанные агенты:**
- Performance Monitor Agent — источник метрик производительности
- Budget Optimizer Agent — источник данных об оптимизации
- Campaign Manager Agent — источник контекста кампаний

**Внешние API:**
- Нет прямых интеграций с внешними API (получает данные через Event Bus)

## Приоритеты исследования

### 🔴 КРИТИЧНО (обязательно глубоко изучить)

1. **Metrics aggregation strategies**
   - Методы агрегации метрик из множественных источников
   - Time-series aggregation (hourly, daily, weekly, monthly)
   - Rollup strategies (sum, avg, min, max, percentiles)
   - Handling missing data and gaps
   - Deduplication and conflict resolution

2. **Data processing pipelines**
   - ETL patterns для аналитических данных
   - Batch vs streaming processing
   - Data validation and quality checks
   - Performance optimization для больших объёмов данных
   - Incremental processing (не пересчитывать всё каждый раз)

3. **Dashboard design patterns**
   - Effective data visualization principles
   - KPI dashboard layouts
   - Drill-down and filtering patterns
   - Real-time vs static dashboards
   - Markdown-based dashboards в Obsidian

### 🟡 ВАЖНО (изучить, но не так глубоко)

1. **Predictive analytics techniques**
   - Time-series forecasting (ARIMA, Prophet, LSTM)
   - Trend detection and anomaly prediction
   - Seasonality modeling
   - Confidence intervals and uncertainty quantification
   - Medical marketing specific patterns

2. **Reporting formats and export**
   - JSON schema design для machine-readable отчётов
   - Excel/CSV generation best practices
   - PDF report generation
   - Email report delivery
   - API endpoints для отчётов

3. **Performance metrics and benchmarks**
   - Medical marketing KPI benchmarks
   - Industry standards для ROI, CPA, LTV
   - Comparative analysis (vs competitors, vs historical)
   - Goal setting and tracking

### 🟢 ОПЦИОНАЛЬНО (можно пропустить или поверхностно)

1. **Advanced visualization techniques**
   - Interactive charts and graphs
   - Heatmaps, scatter plots, correlation matrices
   - Geospatial visualization
   - Custom chart types

2. **Machine learning for insights**
   - Automated insight generation
   - Pattern recognition
   - Recommendation systems
   - Causal inference

3. **Real-time analytics**
   - Streaming data processing
   - Real-time dashboards
   - Live alerts and notifications

## Дополнительные материалы

**Интервью:** Проведено 2026-05-11  
**Связанные спецификации:** Performance Monitor Agent, Budget Optimizer Agent, Campaign Manager Agent  
**TODO из других агентов:** Получатель метрик от всех агентов Ads Magister
