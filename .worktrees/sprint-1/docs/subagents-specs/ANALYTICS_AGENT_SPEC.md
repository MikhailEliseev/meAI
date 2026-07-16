# Analytics Agent Specification

**Version:** 2.0.0  
**Last Updated:** 2026-05-11  
**Status:** ✅ Ready for Implementation  
**Parent Magister:** Ads Magister  
**Priority:** P1

---

## 1. Overview

### 1.1 Purpose

Analytics Agent — комплексный аналитический агент для агрегации метрик, построения дашбордов и предиктивной аналитики в системе медицинского маркетинга. Собирает данные от всех агентов Ads Magister (Performance Monitor, Budget Optimizer, Campaign Manager), создаёт единую картину производительности и предоставляет инсайты для принятия решений.

**Ключевые возможности:**
- **ETL Pipeline:** Medallion architecture (bronze/silver/gold) с idempotent операциями для безопасных retry и backfill
- **Time-Series Aggregation:** Hierarchical rollups (1m → 5m → 1h → 1d) с 95% экономией storage
- **Data Quality:** >99% completeness через dead letter queues и validation gates
- **Predictive Analytics:** ARIMA для трендов, Prophet для сезонности, LSTM для сложных паттернов
- **Dashboard Design:** Obsidian Dataview с KPI cards, trend charts, drill-down tables
- **Report Export:** JSON (agents), Excel/CSV (stakeholders) с форматированием через openpyxl

### 1.2 Role in System

Analytics Agent выполняет роль **центрального аналитического хаба** в Ads Magister:

```
Performance Monitor ──┐
                      ├──> Analytics Agent ──> ETL Pipeline (Bronze/Silver/Gold)
Budget Optimizer ─────┤                    ├──> Dashboards (Obsidian)
                      │                    ├──> Reports (JSON/Excel/CSV)
Campaign Manager ─────┘                    └──> Predictions (ARIMA/Prophet/LSTM)
```

**Взаимодействие:**
- **Входные данные:** Raw events от Performance Monitor (метрики кампаний), Budget Optimizer (оптимизация бюджетов), Campaign Manager (контекст кампаний)
- **Выходные данные:** Агрегированные метрики (JSON), дашборды (Obsidian Markdown), отчёты (Excel/CSV), прогнозы (JSON)
- **Частота:** Ежедневная агрегация (scheduled batch) + ad-hoc анализ (on-demand)

### 1.3 Key Statistics

**Medical Marketing Analytics Benchmarks:**

- **Data Volume:** 10,000-50,000 events/day для среднего медицинского маркетинга
- **Aggregation Time:** <15 минут для 10K-50K events (target), <1 час для 100K-500K events
- **Dashboard Load Time:** <2 секунды для Obsidian dashboard с 20-30 метриками
- **Report Generation:** <30 секунд для Excel export с форматированием
- **Data Quality Score:** >99% (completeness >99%, null rate <1%, duplicate rate <0.1%)
- **Forecast Accuracy:** >85% MAPE для сезонных трендов (Prophet на медицинских данных)

**Storage Optimization:**
- 1-minute raw: 1,440 records/day (100% storage)
- 5-minute rollup: 288 records/day (20% storage)
- 1-hour rollup: 24 records/day (1.7% storage)
- 1-day rollup: 1 record/day (0.07% storage)
- **Total savings:** 95% через hierarchical rollups

**Medical Marketing Seasonality:**
- Winter (Dec-Feb): +40% demand (flu, respiratory)
- Spring (Mar-May): +25% demand (allergies, cosmetic prep)
- Summer (Jun-Aug): +15% demand (sports medicine, dermatology)
- Fall (Sep-Nov): +20% demand (back-to-school, preventive care)

**Sources:**
- [Data Pipeline Best Practices 2026](https://dataworkers.io/resources/data-pipeline-best-practices-2026/) — Medallion architecture, idempotency
- [Databricks Lakeflow ETL](https://databricks.com/resources/architectures/build-production-etl-with-lakeflow-declarative-pipelines) — Bronze/silver/gold layers
- [Time-Series Forecasting Guide](https://www.geeksforgeeks.org/deep-learning/arima-vs-prophet-vs-lstm/) — ARIMA vs Prophet vs LSTM
- [Medical Marketing Benchmarks](https://foundrycro.com/blog/healthcare-marketing-benchmarks-by-specialty/) — Industry KPIs

---

## 2. Input Data

### 2.1 Required Parameters

Analytics Agent получает данные через Event Bus от других агентов Ads Magister:

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional

@dataclass
class AnalyticsTaskInput:
    """Input parameters for Analytics Agent task."""
    
    # Task configuration
    task_type: Literal[
        "daily_aggregation",      # Scheduled daily batch
        "ad_hoc_analysis",        # On-demand analysis
        "dashboard_update",       # Refresh Obsidian dashboard
        "report_export",          # Generate Excel/CSV report
        "forecast_generation",    # Generate predictions
        "backfill"               # Reprocess historical data
    ]
    date_range: tuple[datetime, datetime]  # Start and end dates
    
    # Data sources (optional, defaults to all)
    sources: Optional[list[Literal[
        "performance_monitor",
        "budget_optimizer",
        "campaign_manager"
    ]]] = None
    
    # Metrics to aggregate (optional, defaults to all)
    metrics: Optional[list[str]] = None  # ["roi", "cpa", "conversions", "ltv", "cac"]
    
    # Output format (for report_export)
    output_format: Literal["json", "markdown", "excel", "csv"] = "json"
    
    # Aggregation granularity
    granularity: Literal["hourly", "daily", "weekly", "monthly"] = "daily"
    
    # Filters (optional)
    filters: Optional[dict[str, any]] = None  # {"platform": "yandex", "campaign_id": "123"}
    
    # Backfill parameters (for backfill task_type)
    backfill_mode: Literal["full", "incremental"] = "incremental"
    idempotent: bool = True  # Ensure safe re-runs
```

**Example Event (Daily Aggregation):**
```json
{
  "event_type": "analytics.task.requested",
  "priority": "P1",
  "payload": {
    "task_type": "daily_aggregation",
    "date_range": ["2026-05-11T00:00:00Z", "2026-05-11T23:59:59Z"],
    "sources": ["performance_monitor", "budget_optimizer", "campaign_manager"],
    "metrics": ["roi", "cpa", "conversions", "ltv", "cac", "spend", "revenue"],
    "granularity": "daily",
    "idempotent": true
  },
  "metadata": {
    "requested_by": "ads_magister",
    "requested_at": "2026-05-12T08:00:00Z"
  }
}
```

**Example Event (Report Export):**
```json
{
  "event_type": "analytics.report.requested",
  "priority": "P2",
  "payload": {
    "task_type": "report_export",
    "date_range": ["2026-05-01T00:00:00Z", "2026-05-11T23:59:59Z"],
    "output_format": "excel",
    "metrics": ["roi", "cpa", "conversions", "spend", "revenue"],
    "granularity": "daily",
    "filters": {"platform": "yandex"}
  },
  "metadata": {
    "requested_by": "stakeholder",
    "requested_at": "2026-05-11T15:30:00Z"
  }
}
```

### 2.2 Data Sources

Analytics Agent читает данные из Event Store (immutable audit log):

**Performance Monitor Events:**
```python
{
  "event_type": "performance.metrics.collected",
  "timestamp": "2026-05-11T12:00:00Z",
  "payload": {
    "campaign_id": "camp_001",
    "platform": "yandex",
    "metrics": {
      "impressions": 15420,
      "clicks": 892,
      "conversions": 68,
      "spend": 4200.50,
      "revenue": 8500.00,
      "ctr": 0.0578,
      "cpa": 61.76,
      "roi": 1.024
    }
  }
}
```

**Budget Optimizer Events:**
```python
{
  "event_type": "budget.optimized",
  "timestamp": "2026-05-11T09:00:00Z",
  "payload": {
    "campaign_id": "camp_001",
    "old_budget": 5000.00,
    "new_budget": 4200.00,
    "reason": "cpa_above_target",
    "expected_impact": {
      "cpa_reduction": 0.15,
      "roi_improvement": 0.08
    }
  }
}
```

**Campaign Manager Events:**
```python
{
  "event_type": "campaign.updated",
  "timestamp": "2026-05-11T10:30:00Z",
  "payload": {
    "campaign_id": "camp_001",
    "campaign_name": "Cardiology - Search",
    "status": "active",
    "target_cpa": 60.00,
    "target_roi": 1.00,
    "specialty": "cardiology",
    "region": "moscow"
  }
}
```

### 2.3 Validation Rules

**Schema Validation:**
- `task_type`: Must be one of allowed values
- `date_range`: Start date must be <= end date, both must be valid ISO 8601
- `metrics`: All metric names must exist in metric registry
- `output_format`: Must be supported format (json/markdown/excel/csv)

**Business Logic Validation:**
- Date range must not exceed 365 days (prevent excessive data loading)
- Backfill requests require explicit confirmation (destructive operation)
- Ad-hoc analysis limited to 10 concurrent requests (prevent resource exhaustion)

**Data Quality Checks:**
- Event timestamps must be within date_range ± 1 hour (clock skew tolerance)
- Metric values must be non-negative (revenue, spend, conversions)
- Required fields must be present (campaign_id, timestamp, metrics)

---

## 3. Algorithm and Workflow

### 3.1 ETL Pipeline Architecture

Analytics Agent использует **Medallion Architecture** (bronze/silver/gold layers) для организации data transformations:

```
┌─────────────────────────────────────────────────────────────────┐
│                        ETL PIPELINE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  BRONZE LAYER (Raw Ingestion)                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Event Store → Raw Events (Immutable, Append-Only)      │    │
│  │ - Performance Monitor events                            │    │
│  │ - Budget Optimizer events                               │    │
│  │ - Campaign Manager events                               │    │
│  │ Retention: 90 days                                      │    │
│  └────────────────────────────────────────────────────────┘    │
│                           ↓                                      │
│  SILVER LAYER (Cleaned & Validated)                             │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Data Quality Gates:                                     │    │
│  │ 1. Schema enforcement (type casting, null handling)     │    │
│  │ 2. Deduplication (by event_id + timestamp)             │    │
│  │ 3. Validation (range checks, referential integrity)    │    │
│  │ 4. Dead Letter Queue (invalid records quarantined)     │    │
│  │ Idempotent: DELETE + INSERT by partition               │    │
│  │ Retention: 180 days                                     │    │
│  └────────────────────────────────────────────────────────┘    │
│                           ↓                                      │
│  GOLD LAYER (Business-Ready Aggregates)                         │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Pre-computed Aggregations:                              │    │
│  │ - Daily campaign metrics (ROI, CPA, conversions)        │    │
│  │ - Weekly budget utilization                             │    │
│  │ - Monthly LTV/CAC ratios                                │    │
│  │ - Seasonal adjustments (flu +40%, allergies +25%)      │    │
│  │ Hierarchical Rollups: 1m → 5m → 1h → 1d               │    │
│  │ Retention: Forever (compressed)                         │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Daily Aggregation Workflow

**Step 1: Extract (Bronze Layer)**
```python
async def extract_raw_events(date_range: tuple[datetime, datetime]) -> list[Event]:
    """
    Extract raw events from Event Store for given date range.
    
    Returns:
        List of raw events (immutable, append-only)
    """
    events = await event_store.query(
        event_types=[
            "performance.metrics.collected",
            "budget.optimized",
            "campaign.updated"
        ],
        start_time=date_range[0],
        end_time=date_range[1]
    )
    
    logger.info(f"Extracted {len(events)} raw events from Event Store")
    return events
```

**Step 2: Transform (Silver Layer)**
```python
async def transform_and_validate(raw_events: list[Event]) -> tuple[list[CleanEvent], list[InvalidEvent]]:
    """
    Clean, validate, and deduplicate events.
    
    Returns:
        Tuple of (valid_events, invalid_events)
        Invalid events sent to Dead Letter Queue
    """
    valid_events = []
    invalid_events = []
    
    # Deduplication by event_id + timestamp
    seen_ids = set()
    
    for event in raw_events:
        # Schema enforcement
        try:
            clean_event = CleanEvent.from_raw(event)
        except ValidationError as e:
            invalid_events.append(InvalidEvent(event, error=str(e)))
            continue
        
        # Deduplication
        event_key = (clean_event.event_id, clean_event.timestamp)
        if event_key in seen_ids:
            logger.warning(f"Duplicate event detected: {event_key}")
            continue
        seen_ids.add(event_key)
        
        # Range validation
        if not validate_metric_ranges(clean_event.metrics):
            invalid_events.append(InvalidEvent(event, error="Invalid metric ranges"))
            continue
        
        valid_events.append(clean_event)
    
    # Send invalid events to Dead Letter Queue
    if invalid_events:
        await dead_letter_queue.send(invalid_events)
        logger.warning(f"Sent {len(invalid_events)} invalid events to DLQ")
    
    # Idempotent write: DELETE + INSERT by date partition
    await silver_table.delete_partition(date=date_range[0].date())
    await silver_table.insert(valid_events)
    
    logger.info(f"Transformed {len(valid_events)} valid events to Silver layer")
    return valid_events, invalid_events
```

**Step 3: Load (Gold Layer)**
```python
async def aggregate_metrics(clean_events: list[CleanEvent], granularity: str = "daily") -> dict:
    """
    Aggregate metrics with statistical summaries.
    
    Returns:
        Dict with aggregated metrics by campaign/platform/date
    """
    # Group by dimensions
    grouped = defaultdict(lambda: {
        "revenue": [],
        "spend": [],
        "conversions": [],
        "cpa": [],
        "roi": []
    })
    
    for event in clean_events:
        key = (event.campaign_id, event.platform, event.date)
        grouped[key]["revenue"].append(event.metrics.revenue)
        grouped[key]["spend"].append(event.metrics.spend)
        grouped[key]["conversions"].append(event.metrics.conversions)
        grouped[key]["cpa"].append(event.metrics.cpa)
        grouped[key]["roi"].append(event.metrics.roi)
    
    # Calculate statistical aggregations
    aggregated = {}
    for key, metrics in grouped.items():
        campaign_id, platform, date = key
        aggregated[key] = {
            "campaign_id": campaign_id,
            "platform": platform,
            "date": date,
            # Sum aggregations
            "total_revenue": sum(metrics["revenue"]),
            "total_spend": sum(metrics["spend"]),
            "total_conversions": sum(metrics["conversions"]),
            # Average aggregations
            "avg_cpa": statistics.mean(metrics["cpa"]),
            "avg_roi": statistics.mean(metrics["roi"]),
            # Min/Max aggregations
            "min_cpa": min(metrics["cpa"]),
            "max_cpa": max(metrics["cpa"]),
            # Statistical aggregations
            "median_cpa": statistics.median(metrics["cpa"]),
            "stddev_cpa": statistics.stdev(metrics["cpa"]) if len(metrics["cpa"]) > 1 else 0,
            "p95_cpa": np.percentile(metrics["cpa"], 95),
            "p99_cpa": np.percentile(metrics["cpa"], 99),
            # Calculated metrics
            "calculated_roi": (sum(metrics["revenue"]) / sum(metrics["spend"]) - 1) * 100 if sum(metrics["spend"]) > 0 else 0
        }
    
    # Idempotent write: MERGE/UPSERT by (campaign_id, platform, date)
    await gold_table.merge(
        source=aggregated.values(),
        on=["campaign_id", "platform", "date"],
        update_cols=["total_revenue", "total_spend", "avg_cpa", "avg_roi", ...],
        insert_cols="*"
    )
    
    logger.info(f"Aggregated {len(aggregated)} metric groups to Gold layer")
    return aggregated
```

### 3.3 Hierarchical Rollups

**Time-Series Rollup Strategy:**
```python
async def create_hierarchical_rollups(daily_metrics: dict) -> None:
    """
    Create hierarchical rollups for storage optimization.
    
    Rollup hierarchy: 1-minute → 5-minute → 1-hour → 1-day
    Storage savings: 95% (from 1,440 records/day to 1 record/day)
    """
    # 1-minute raw (keep 7 days)
    await metrics_1m.insert(daily_metrics)
    await metrics_1m.delete_older_than(days=7)
    
    # 5-minute rollup (keep 30 days)
    rollup_5m = await aggregate_time_window(daily_metrics, window="5min")
    await metrics_5m.merge(rollup_5m)
    await metrics_5m.delete_older_than(days=30)
    
    # 1-hour rollup (keep 90 days)
    rollup_1h = await aggregate_time_window(daily_metrics, window="1hour")
    await metrics_1h.merge(rollup_1h)
    await metrics_1h.delete_older_than(days=90)
    
    # 1-day rollup (keep forever)
    rollup_1d = await aggregate_time_window(daily_metrics, window="1day")
    await metrics_1d.merge(rollup_1d)
    
    logger.info("Created hierarchical rollups (1m/5m/1h/1d)")
```

### 3.4 Seasonal Adjustment

**Medical Marketing Seasonality:**
```python
def apply_seasonal_adjustment(metrics: dict, date: datetime) -> dict:
    """
    Apply seasonal multipliers for medical marketing.
    
    Seasonality patterns:
    - Winter (Dec-Feb): +40% demand (flu, respiratory)
    - Spring (Mar-May): +25% demand (allergies, cosmetic prep)
    - Summer (Jun-Aug): +15% demand (sports medicine)
    - Fall (Sep-Nov): +20% demand (back-to-school, preventive)
    """
    seasonal_multipliers = {
        "flu_season": 1.4,       # Dec-Feb
        "allergy_season": 1.25,  # Mar-May
        "cosmetic_prep": 1.3,    # May-Jun (pre-summer)
        "back_to_school": 1.2    # Sep-Nov
    }
    
    # Determine current season
    month = date.month
    if month in [12, 1, 2]:
        season = "flu_season"
    elif month in [3, 4, 5]:
        season = "allergy_season"
    elif month in [6, 7, 8]:
        season = "cosmetic_prep"
    else:
        season = "back_to_school"
    
    multiplier = seasonal_multipliers[season]
    
    # Adjust forecast metrics
    adjusted_metrics = metrics.copy()
    adjusted_metrics["seasonal_multiplier"] = multiplier
    adjusted_metrics["adjusted_forecast"] = metrics["base_forecast"] * multiplier
    
    return adjusted_metrics
```

### 3.5 Backfilling Historical Data

**Backfill Workflow:**
```python
async def backfill_historical_data(start_date: datetime, end_date: datetime, mode: str = "incremental") -> None:
    """
    Reprocess historical data after bug fixes or logic changes.
    
    Args:
        start_date: Start of backfill period
        end_date: End of backfill period
        mode: "full" (reprocess all) or "incremental" (only missing/changed)
    """
    # Generate date range
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Parallel backfill (each date independent)
    tasks = []
    for date in date_range:
        task = asyncio.create_task(
            aggregate_daily_metrics(
                date_range=(date, date + timedelta(days=1)),
                idempotent=True  # Safe to re-run
            )
        )
        tasks.append(task)
    
    # Execute in parallel (10 workers)
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Log results
    success_count = sum(1 for r in results if not isinstance(r, Exception))
    logger.info(f"Backfill completed: {success_count}/{len(date_range)} days successful")
```

---

## 4. Output Data

### 4.1 JSON Output (Machine-Readable)

**Daily Aggregation Result:**
```json
{
  "report_id": "analytics_daily_20260511",
  "generated_at": "2026-05-12T08:00:00Z",
  "period": {
    "start": "2026-05-11T00:00:00Z",
    "end": "2026-05-11T23:59:59Z"
  },
  "summary": {
    "total_revenue": 15420.50,
    "total_spend": 8230.25,
    "roi_percent": 87.4,
    "total_conversions": 142,
    "avg_cpa": 57.96,
    "ltv_cac_ratio": 3.2
  },
  "campaigns": [
    {
      "campaign_id": "camp_001",
      "campaign_name": "Cardiology - Search",
      "platform": "yandex",
      "specialty": "cardiology",
      "region": "moscow",
      "metrics": {
        "revenue": 8500.00,
        "spend": 4200.00,
        "roi_percent": 102.4,
        "conversions": 68,
        "cpa": 61.76,
        "avg_cpa": 61.76,
        "min_cpa": 45.20,
        "max_cpa": 89.50,
        "median_cpa": 59.30,
        "p95_cpa": 82.10,
        "stddev_cpa": 12.45
      }
    }
  ],
  "metadata": {
    "data_quality_score": 0.998,
    "records_processed": 125430,
    "records_invalid": 250,
    "processing_time_seconds": 847
  }
}
```

**Forecast Output:**
```json
{
  "forecast_id": "forecast_20260511_7day",
  "generated_at": "2026-05-11T12:00:00Z",
  "model": "prophet",
  "forecast_horizon_days": 7,
  "predictions": [
    {
      "date": "2026-05-12",
      "metric": "revenue",
      "forecast": 16200.00,
      "lower_bound": 14500.00,
      "upper_bound": 18000.00,
      "confidence_interval": 0.95,
      "seasonal_multiplier": 1.25
    }
  ],
  "model_performance": {
    "mape": 8.5,
    "rmse": 1250.30,
    "mae": 980.50
  }
}
```

### 4.2 Obsidian Dashboard (Markdown)

**KPI Dashboard Example:**
```markdown
# Analytics Dashboard - 2026-05-11

## Executive Summary

| Metric | Value | Trend |
|--------|-------|-------|
| Total Revenue | $15,420 | ↑ 15% |
| Total Spend | $8,230 | ↓ 5% |
| ROI | 87.4% | ↑ 22% |
| Conversions | 142 | ↑ 18% |
| Avg CPA | $57.96 | ↓ 12% |
| LTV:CAC Ratio | 3.2:1 | ✅ Target |

## Campaign Performance (Last 7 Days)

```dataview
TABLE
    campaign_name as "Campaign",
    sum(revenue) as "Revenue",
    sum(spend) as "Spend",
    round(sum(revenue) / sum(spend) * 100, 1) as "ROI %",
    sum(conversions) as "Conversions",
    round(sum(spend) / sum(conversions), 2) as "CPA"
FROM "metrics/daily"
WHERE date >= date(today) - dur(7 days)
GROUP BY campaign_id, campaign_name
SORT sum(revenue) DESC
```

## Seasonal Trends

**Current Season:** Spring (Allergy Season)  
**Seasonal Multiplier:** 1.25x (+25% demand)  
**Peak Specialties:** Allergology, Dermatology, ENT

## Alerts

- ⚠️ Campaign "Orthopedics - Display" CPA above target ($89.50 vs $60.00)
- ✅ All other campaigns within target ranges
- 📈 Revenue trending +15% vs last week
```

### 4.3 Excel Report (Formatted)

**Multi-Sheet Excel Report:**
```python
async def generate_excel_report(metrics: dict, output_path: str) -> None:
    """
    Generate formatted Excel report with multiple sheets.
    
    Sheets:
    1. Summary - Executive KPIs
    2. Campaigns - Detailed campaign metrics
    3. Daily Trends - Time-series data
    4. Forecasts - 7-day predictions
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    
    wb = Workbook()
    
    # Sheet 1: Summary
    ws_summary = wb.active
    ws_summary.title = "Summary"
    
    # Header styling
    header_font = Font(bold=True, color="FFFFFF", size=12)
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    
    # Write summary data
    summary_data = [
        ["Metric", "Value", "Trend"],
        ["Total Revenue", f"${metrics['total_revenue']:,.2f}", "↑ 15%"],
        ["Total Spend", f"${metrics['total_spend']:,.2f}", "↓ 5%"],
        ["ROI", f"{metrics['roi_percent']:.1f}%", "↑ 22%"],
        ["Conversions", metrics['total_conversions'], "↑ 18%"],
        ["Avg CPA", f"${metrics['avg_cpa']:.2f}", "↓ 12%"]
    ]
    
    for row in summary_data:
        ws_summary.append(row)
    
    # Apply header styling
    for cell in ws_summary[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')
    
    # Auto-adjust column widths
    for column in ws_summary.columns:
        max_length = max(len(str(cell.value)) for cell in column)
        ws_summary.column_dimensions[column[0].column_letter].width = max_length + 2
    
    # Sheet 2: Campaigns
    ws_campaigns = wb.create_sheet("Campaigns")
    campaigns_df = pd.DataFrame(metrics['campaigns'])
    for row in dataframe_to_rows(campaigns_df, index=False, header=True):
        ws_campaigns.append(row)
    
    # Apply header styling
    for cell in ws_campaigns[1]:
        cell.font = header_font
        cell.fill = header_fill
    
    # Sheet 3: Daily Trends
    ws_trends = wb.create_sheet("Daily Trends")
    trends_df = pd.DataFrame(metrics['daily_trends'])
    for row in dataframe_to_rows(trends_df, index=False, header=True):
        ws_trends.append(row)
    
    # Save workbook
    wb.save(output_path)
    logger.info(f"Excel report saved to {output_path}")
```

### 4.4 Event Bus Notifications

**Success Event:**
```json
{
  "event_type": "analytics.aggregation.completed",
  "priority": "P2",
  "payload": {
    "task_id": "analytics_daily_20260511",
    "status": "success",
    "date_range": ["2026-05-11T00:00:00Z", "2026-05-11T23:59:59Z"],
    "metrics_summary": {
      "total_revenue": 15420.50,
      "total_conversions": 142,
      "roi_percent": 87.4
    },
    "outputs": {
      "json_report": "reports/analytics_daily_20260511.json",
      "excel_report": "reports/analytics_daily_20260511.xlsx",
      "dashboard_updated": "obsidian/ads-magister/dashboards/analytics.md"
    },
    "processing_time_seconds": 847,
    "data_quality_score": 0.998
  },
  "metadata": {
    "completed_at": "2026-05-12T08:14:07Z"
  }
}
```

**Error Event:**
```json
{
  "event_type": "analytics.aggregation.failed",
  "priority": "P0",
  "payload": {
    "task_id": "analytics_daily_20260511",
    "status": "failed",
    "error": {
      "type": "DataQualityError",
      "message": "Data completeness below threshold: 92% (required >99%)",
      "details": {
        "missing_events": 8500,
        "total_expected": 100000,
        "completeness_percent": 92.0
      }
    },
    "retry_strategy": "exponential_backoff",
    "next_retry_at": "2026-05-12T08:30:00Z"
  },
  "metadata": {
    "failed_at": "2026-05-12T08:10:00Z"
  }
}
```

---

## 5. Success Metrics

### 5.1 Performance Metrics

**Aggregation Performance:**
- **Target:** <15 minutes for 10K-50K events
- **Measurement:** `processing_time_seconds` in output
- **Threshold:** Alert if >20 minutes

**Dashboard Load Time:**
- **Target:** <2 seconds for Obsidian dashboard
- **Measurement:** Time from request to render
- **Threshold:** Alert if >5 seconds

**Report Generation:**
- **Target:** <30 seconds for Excel export
- **Measurement:** Time from request to file saved
- **Threshold:** Alert if >60 seconds

### 5.2 Data Quality Metrics

**Completeness:**
- **Target:** >99% (null rate <1%)
- **Measurement:** `(total_records - null_records) / total_records`
- **Threshold:** Alert if <99%

**Accuracy:**
- **Target:** >99.9% (validation pass rate)
- **Measurement:** `valid_records / total_records`
- **Threshold:** Alert if <99%

**Timeliness:**
- **Target:** <1 hour lag (event to dashboard)
- **Measurement:** `dashboard_updated_at - event_timestamp`
- **Threshold:** Alert if >2 hours

**Duplicate Rate:**
- **Target:** <0.1%
- **Measurement:** `duplicate_records / total_records`
- **Threshold:** Alert if >0.5%

### 5.3 Forecast Accuracy

**MAPE (Mean Absolute Percentage Error):**
- **Target:** <15% for 7-day forecast
- **Measurement:** `mean(|actual - forecast| / actual) * 100`
- **Threshold:** Alert if >20%

**RMSE (Root Mean Square Error):**
- **Target:** <$2,000 for revenue forecast
- **Measurement:** `sqrt(mean((actual - forecast)^2))`
- **Threshold:** Alert if >$3,000

**Confidence Interval Coverage:**
- **Target:** 95% of actuals within 95% CI
- **Measurement:** `count(actual in [lower, upper]) / total`
- **Threshold:** Alert if <90%

### 5.4 Business Impact Metrics

**Decision Support:**
- **Target:** 80% of budget decisions informed by analytics
- **Measurement:** Survey Budget Optimizer usage
- **Threshold:** Alert if <70%

**Insight Actionability:**
- **Target:** 90% of alerts result in action
- **Measurement:** Track alert → action conversion
- **Threshold:** Alert if <80%

**Stakeholder Satisfaction:**
- **Target:** 4.5/5 rating for report quality
- **Measurement:** Quarterly stakeholder survey
- **Threshold:** Alert if <4.0/5

---

## 6. Communication Patterns

### 6.1 Event Bus Integration

**Subscribe to Events:**
```python
# Analytics Agent subscribes to these events
SUBSCRIBED_EVENTS = [
    "performance.metrics.collected",  # From Performance Monitor
    "budget.optimized",               # From Budget Optimizer
    "campaign.updated",               # From Campaign Manager
    "analytics.task.requested"        # From Ads Magister
]
```

**Publish Events:**
```python
# Analytics Agent publishes these events
PUBLISHED_EVENTS = [
    "analytics.aggregation.completed",  # Success notification
    "analytics.aggregation.failed",     # Error notification
    "analytics.report.generated",       # Report ready
    "analytics.forecast.updated",       # New predictions available
    "analytics.alert.triggered"         # Anomaly detected
]
```

### 6.2 Request-Response Pattern

**Synchronous Request (Ad-Hoc Analysis):**
```python
async def handle_ad_hoc_request(request: AnalyticsTaskInput) -> dict:
    """
    Handle synchronous ad-hoc analysis request.
    
    Returns:
        Aggregated metrics within 30 seconds
    """
    # Validate request
    validate_input(request)
    
    # Execute analysis
    metrics = await aggregate_metrics(
        date_range=request.date_range,
        filters=request.filters,
        granularity=request.granularity
    )
    
    # Return immediately
    return {
        "status": "success",
        "metrics": metrics,
        "generated_at": datetime.utcnow().isoformat()
    }
```

**Asynchronous Request (Daily Aggregation):**
```python
async def handle_daily_aggregation(request: AnalyticsTaskInput) -> str:
    """
    Handle asynchronous daily aggregation request.
    
    Returns:
        Task ID for tracking progress
    """
    # Create task
    task_id = f"analytics_daily_{request.date_range[0].strftime('%Y%m%d')}"
    
    # Execute in background
    asyncio.create_task(
        execute_daily_aggregation(task_id, request)
    )
    
    # Return task ID immediately
    return task_id
```

### 6.3 Error Handling

**Retry Strategy:**
```python
async def execute_with_retry(func, max_retries: int = 3, backoff_factor: float = 2.0):
    """
    Execute function with exponential backoff retry.
    
    Retry delays: 1s, 2s, 4s
    """
    for attempt in range(max_retries):
        try:
            return await func()
        except TransientError as e:
            if attempt == max_retries - 1:
                raise
            delay = backoff_factor ** attempt
            logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
            await asyncio.sleep(delay)
```

**Dead Letter Queue:**
```python
async def send_to_dlq(invalid_events: list[InvalidEvent]) -> None:
    """
    Send invalid events to Dead Letter Queue for investigation.
    
    DLQ retention: 30 days
    """
    await event_store.publish(
        event_type="analytics.dlq.received",
        payload={
            "invalid_events": [
                {
                    "event_id": e.event_id,
                    "error": e.error,
                    "raw_data": e.raw_data
                }
                for e in invalid_events
            ],
            "count": len(invalid_events)
        }
    )
    
    logger.warning(f"Sent {len(invalid_events)} events to DLQ")
```

---

## 7. Error Handling

### 7.1 Common Errors

**DataQualityError:**
```python
class DataQualityError(Exception):
    """Raised when data quality below threshold."""
    
    def __init__(self, completeness: float, threshold: float = 0.99):
        self.completeness = completeness
        self.threshold = threshold
        super().__init__(
            f"Data completeness {completeness:.1%} below threshold {threshold:.1%}"
        )
```

**Solution:**
- Check Event Store for missing events
- Verify upstream agents (Performance Monitor, Budget Optimizer) are running
- Extend date range to capture late-arriving events
- If persistent, trigger backfill for missing dates

**AggregationTimeoutError:**
```python
class AggregationTimeoutError(Exception):
    """Raised when aggregation exceeds time limit."""
    
    def __init__(self, elapsed_seconds: int, limit_seconds: int = 1800):
        self.elapsed_seconds = elapsed_seconds
        self.limit_seconds = limit_seconds
        super().__init__(
            f"Aggregation timeout: {elapsed_seconds}s exceeded limit {limit_seconds}s"
        )
```

**Solution:**
- Reduce date range (process smaller batches)
- Increase worker parallelism
- Optimize SQL queries (add indexes, partition pruning)
- Scale compute resources (more CPU/memory)

**ForecastModelError:**
```python
class ForecastModelError(Exception):
    """Raised when forecast model fails to train or predict."""
    
    def __init__(self, model: str, error: str):
        self.model = model
        self.error = error
        super().__init__(f"Forecast model '{model}' failed: {error}")
```

**Solution:**
- Check data quality (sufficient history, no gaps)
- Try alternative model (ARIMA → Prophet → LSTM)
- Adjust model parameters (seasonality, trend)
- Fall back to simple baseline (moving average)

### 7.2 Error Recovery

**Automatic Recovery:**
```python
async def execute_with_recovery(task: AnalyticsTaskInput) -> dict:
    """
    Execute task with automatic error recovery.
    
    Recovery strategies:
    1. Retry with exponential backoff (transient errors)
    2. Fall back to incremental mode (timeout errors)
    3. Skip invalid records and continue (data quality errors)
    """
    try:
        return await execute_task(task)
    
    except DataQualityError as e:
        logger.warning(f"Data quality issue: {e}")
        # Skip invalid records, continue with valid data
        return await execute_task(task, skip_invalid=True)
    
    except AggregationTimeoutError as e:
        logger.warning(f"Aggregation timeout: {e}")
        # Fall back to incremental mode (smaller batches)
        return await execute_task_incremental(task)
    
    except ForecastModelError as e:
        logger.error(f"Forecast model failed: {e}")
        # Fall back to simple baseline
        return await execute_baseline_forecast(task)
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        # Publish error event
        await event_bus.publish(
            event_type="analytics.aggregation.failed",
            payload={"error": str(e), "task": task}
        )
        raise
```

**Manual Intervention:**
- **DLQ Review:** Weekly review of Dead Letter Queue for patterns
- **Backfill Requests:** Manual approval for large backfills (>30 days)
- **Model Retraining:** Quarterly retraining of forecast models with new data

### 7.3 Monitoring and Alerts

**CloudWatch Metrics:**
```python
# Publish metrics to CloudWatch
await cloudwatch.put_metric_data(
    Namespace='Analytics',
    MetricData=[
        {
            'MetricName': 'AggregationTime',
            'Value': processing_time_seconds,
            'Unit': 'Seconds'
        },
        {
            'MetricName': 'DataQualityScore',
            'Value': data_quality_score,
            'Unit': 'None'
        },
        {
            'MetricName': 'ForecastMAPE',
            'Value': forecast_mape,
            'Unit': 'Percent'
        }
    ]
)
```

**Alert Rules:**
- **Critical:** Data quality <95% → Page on-call
- **Warning:** Aggregation time >20 minutes → Slack notification
- **Info:** Forecast MAPE >15% → Email report

---

---

## 8. Стратегия тестирования

### 8.1 Unit Tests

**Тестирование компонентов:**

```python
# tests/test_analytics_agent.py
import pytest
from datetime import datetime, timedelta
from aim.subagents.analytics_agent import AnalyticsAgent
from meai.events.event_store import Event

@pytest.fixture
async def analytics_agent():
    agent = AnalyticsAgent(
        agent_id="analytics-test",
        vault_path="./test_vault",
        db_path="./test_data/analytics.db"
    )
    await agent.initialize()
    return agent

@pytest.mark.asyncio
async def test_extract_raw_events(analytics_agent):
    """Test extraction of raw events from Event Store."""
    date_range = (datetime(2026, 5, 1), datetime(2026, 5, 2))
    events = await analytics_agent.extract_raw_events(date_range)
    
    assert len(events) > 0
    assert all(isinstance(e, Event) for e in events)
    assert all(date_range[0] <= e.timestamp < date_range[1] for e in events)

@pytest.mark.asyncio
async def test_transform_and_validate(analytics_agent):
    """Test data transformation and validation."""
    raw_events = [
        Event(type="performance.metrics.collected", data={"roi": 2.5, "cpa": 150}),
        Event(type="performance.metrics.collected", data={"roi": -1.0, "cpa": 150}),  # Invalid ROI
        Event(type="performance.metrics.collected", data={"roi": 2.5}),  # Missing CPA
    ]
    
    valid, invalid = await analytics_agent.transform_and_validate(raw_events)
    
    assert len(valid) == 1
    assert len(invalid) == 2
    assert valid[0].data["roi"] == 2.5
    assert invalid[0].error_type == "range_violation"
    assert invalid[1].error_type == "missing_field"

@pytest.mark.asyncio
async def test_hierarchical_rollup(analytics_agent):
    """Test hierarchical time-series rollup."""
    hourly_data = [
        {"timestamp": datetime(2026, 5, 1, i), "roi": 2.0 + i * 0.1, "cpa": 150 - i}
        for i in range(24)
    ]
    
    daily_rollup = await analytics_agent.rollup_to_daily(hourly_data)
    
    assert daily_rollup["date"] == datetime(2026, 5, 1).date()
    assert daily_rollup["roi_avg"] == pytest.approx(3.15, rel=0.01)
    assert daily_rollup["cpa_avg"] == pytest.approx(138.5, rel=0.01)
    assert daily_rollup["roi_p95"] > daily_rollup["roi_avg"]

@pytest.mark.asyncio
async def test_seasonal_adjustment(analytics_agent):
    """Test seasonal adjustment for medical marketing."""
    base_metrics = {"roi": 2.0, "conversions": 100}
    
    # Winter (flu season)
    winter_adjusted = await analytics_agent.apply_seasonal_adjustment(
        base_metrics, month=1
    )
    assert winter_adjusted["roi"] == pytest.approx(2.8, rel=0.01)  # +40%
    assert winter_adjusted["conversions"] == pytest.approx(140, rel=0.01)
    
    # Spring (allergy season)
    spring_adjusted = await analytics_agent.apply_seasonal_adjustment(
        base_metrics, month=4
    )
    assert spring_adjusted["roi"] == pytest.approx(2.5, rel=0.01)  # +25%

@pytest.mark.asyncio
async def test_forecast_generation(analytics_agent):
    """Test predictive forecasting with ARIMA."""
    historical_data = [
        {"date": datetime(2026, 5, 1) + timedelta(days=i), "roi": 2.0 + i * 0.05}
        for i in range(30)
    ]
    
    forecast = await analytics_agent.generate_forecast(
        historical_data, metric="roi", horizon_days=7
    )
    
    assert len(forecast) == 7
    assert all("date" in f and "roi_forecast" in f for f in forecast)
    assert all("confidence_lower" in f and "confidence_upper" in f for f in forecast)
    assert forecast[0]["roi_forecast"] > 2.0  # Trend continuation

@pytest.mark.asyncio
async def test_idempotent_write(analytics_agent):
    """Test idempotent write operations."""
    date = datetime(2026, 5, 1).date()
    data = [{"roi": 2.5, "cpa": 150}]
    
    # First write
    await analytics_agent.write_to_silver(date, data)
    result1 = await analytics_agent.read_from_silver(date)
    
    # Second write (same data)
    await analytics_agent.write_to_silver(date, data)
    result2 = await analytics_agent.read_from_silver(date)
    
    assert result1 == result2  # Idempotent
    assert len(result2) == 1  # No duplicates
```

### 8.2 Integration Tests

**Тестирование E2E workflow:**

```python
# tests/integration/test_analytics_workflow.py
import pytest
from datetime import datetime, timedelta
from aim.subagents.analytics_agent import AnalyticsAgent
from meai.events.event_bus import EventBus

@pytest.mark.asyncio
async def test_daily_aggregation_workflow():
    """Test complete daily aggregation workflow."""
    agent = AnalyticsAgent(agent_id="analytics-integration")
    event_bus = EventBus()
    
    # Simulate events from Performance Monitor
    for i in range(100):
        await event_bus.publish(Event(
            type="performance.metrics.collected",
            data={"roi": 2.0 + i * 0.01, "cpa": 150 - i * 0.5, "conversions": 10 + i}
        ))
    
    # Trigger daily aggregation
    task = AnalyticsTaskInput(
        task_type="daily_aggregation",
        date_range=(datetime(2026, 5, 1), datetime(2026, 5, 2)),
        sources=["performance_monitor"],
        granularity="daily"
    )
    
    result = await agent.execute_task(task)
    
    assert result.status == "success"
    assert "aggregated_metrics" in result.data
    assert result.data["aggregated_metrics"]["roi_avg"] > 2.0
    assert result.data["data_quality_score"] > 0.99

@pytest.mark.asyncio
async def test_dashboard_generation():
    """Test Obsidian dashboard generation."""
    agent = AnalyticsAgent(agent_id="analytics-dashboard")
    
    task = AnalyticsTaskInput(
        task_type="dashboard_update",
        date_range=(datetime(2026, 5, 1), datetime(2026, 5, 8)),
        output_format="markdown"
    )
    
    result = await agent.execute_task(task)
    
    dashboard_path = agent.vault_path / "wiki" / "dashboards" / "weekly_performance.md"
    assert dashboard_path.exists()
    
    content = dashboard_path.read_text()
    assert "```dataview" in content
    assert "ROI" in content
    assert "CPA" in content

@pytest.mark.asyncio
async def test_report_export():
    """Test Excel report export."""
    agent = AnalyticsAgent(agent_id="analytics-export")
    
    task = AnalyticsTaskInput(
        task_type="report_export",
        date_range=(datetime(2026, 5, 1), datetime(2026, 5, 8)),
        output_format="excel"
    )
    
    result = await agent.execute_task(task)
    
    assert result.status == "success"
    assert "report_path" in result.data
    
    report_path = Path(result.data["report_path"])
    assert report_path.exists()
    assert report_path.suffix == ".xlsx"
```

### 8.3 Data Quality Tests

**Тестирование качества данных:**

```python
# tests/test_data_quality.py
import pytest
from aim.subagents.analytics_agent import AnalyticsAgent

@pytest.mark.asyncio
async def test_completeness_check():
    """Test data completeness validation."""
    agent = AnalyticsAgent(agent_id="analytics-quality")
    
    data = [
        {"roi": 2.5, "cpa": 150, "conversions": 10},
        {"roi": 2.3, "cpa": None, "conversions": 12},  # Missing CPA
        {"roi": 2.7, "cpa": 145, "conversions": 15},
    ]
    
    quality_score = await agent.calculate_completeness(data)
    
    assert quality_score == pytest.approx(0.889, rel=0.01)  # 8/9 fields present

@pytest.mark.asyncio
async def test_duplicate_detection():
    """Test duplicate record detection."""
    agent = AnalyticsAgent(agent_id="analytics-dedup")
    
    data = [
        {"timestamp": datetime(2026, 5, 1, 10), "roi": 2.5},
        {"timestamp": datetime(2026, 5, 1, 10), "roi": 2.5},  # Duplicate
        {"timestamp": datetime(2026, 5, 1, 11), "roi": 2.3},
    ]
    
    deduplicated = await agent.remove_duplicates(data)
    
    assert len(deduplicated) == 2
    assert deduplicated[0]["timestamp"] == datetime(2026, 5, 1, 10)

@pytest.mark.asyncio
async def test_anomaly_detection():
    """Test anomaly detection in metrics."""
    agent = AnalyticsAgent(agent_id="analytics-anomaly")
    
    data = [{"roi": 2.0 + i * 0.1} for i in range(30)]
    data.append({"roi": 10.0})  # Anomaly
    
    anomalies = await agent.detect_anomalies(data, metric="roi")
    
    assert len(anomalies) == 1
    assert anomalies[0]["roi"] == 10.0
    assert anomalies[0]["z_score"] > 3.0
```

### 8.4 Performance Tests

**Тестирование производительности:**

```python
# tests/test_performance.py
import pytest
import time
from aim.subagents.analytics_agent import AnalyticsAgent

@pytest.mark.asyncio
async def test_aggregation_performance():
    """Test aggregation performance with 50K events."""
    agent = AnalyticsAgent(agent_id="analytics-perf")
    
    # Generate 50K events
    events = [
        Event(type="performance.metrics.collected", data={"roi": 2.0, "cpa": 150})
        for _ in range(50000)
    ]
    
    start = time.time()
    result = await agent.aggregate_events(events)
    duration = time.time() - start
    
    assert duration < 900  # < 15 minutes
    assert result["event_count"] == 50000

@pytest.mark.asyncio
async def test_dashboard_load_time():
    """Test dashboard generation time."""
    agent = AnalyticsAgent(agent_id="analytics-dashboard-perf")
    
    start = time.time()
    await agent.generate_dashboard(date_range=(datetime(2026, 5, 1), datetime(2026, 5, 8)))
    duration = time.time() - start
    
    assert duration < 2.0  # < 2 seconds
```

---

## 9. Примеры использования

### 9.1 Daily Aggregation

**Ежедневная агрегация метрик:**

```python
from aim.subagents.analytics_agent import AnalyticsAgent, AnalyticsTaskInput
from datetime import datetime, timedelta

# Initialize agent
agent = AnalyticsAgent(
    agent_id="analytics-daily",
    vault_path="./AIM/obsidian/analytics-magister",
    db_path="./AIM/data/analytics.db"
)

# Define task
task = AnalyticsTaskInput(
    task_type="daily_aggregation",
    date_range=(
        datetime.now() - timedelta(days=1),
        datetime.now()
    ),
    sources=["performance_monitor", "budget_optimizer", "campaign_manager"],
    granularity="daily",
    output_format="json"
)

# Execute
result = await agent.execute_task(task)

print(f"Status: {result.status}")
print(f"Aggregated Metrics: {result.data['aggregated_metrics']}")
print(f"Data Quality Score: {result.data['data_quality_score']}")
```

**Output:**
```json
{
  "status": "success",
  "data": {
    "aggregated_metrics": {
      "roi_avg": 2.45,
      "roi_median": 2.40,
      "roi_p95": 3.20,
      "cpa_avg": 145.30,
      "conversions_sum": 1250,
      "ltv_avg": 5800.00,
      "cac_avg": 180.50,
      "retention_rate": 0.68
    },
    "data_quality_score": 0.995,
    "event_count": 12450,
    "processing_time_seconds": 420
  }
}
```

### 9.2 Ad-Hoc Analysis

**Анализ конкретной кампании:**

```python
task = AnalyticsTaskInput(
    task_type="ad_hoc_analysis",
    date_range=(datetime(2026, 5, 1), datetime(2026, 5, 8)),
    sources=["performance_monitor"],
    metrics=["roi", "cpa", "conversions"],
    filters={"campaign_id": "camp_12345"},
    granularity="hourly",
    output_format="excel"
)

result = await agent.execute_task(task)

print(f"Report saved to: {result.data['report_path']}")
```

**Output:**
```
Report saved to: ./AIM/reports/campaign_12345_analysis_20260508.xlsx
```

### 9.3 Dashboard Update

**Обновление Obsidian dashboard:**

```python
task = AnalyticsTaskInput(
    task_type="dashboard_update",
    date_range=(datetime(2026, 5, 1), datetime(2026, 5, 8)),
    sources=["performance_monitor", "budget_optimizer"],
    output_format="markdown"
)

result = await agent.execute_task(task)

# Dashboard created at: ./AIM/obsidian/analytics-magister/wiki/dashboards/weekly_performance.md
```

**Generated Dashboard:**
```markdown
# Weekly Performance Dashboard

**Period:** 2026-05-01 to 2026-05-08

## Key Metrics

| Metric | Value | Change |
|--------|-------|--------|
| ROI | 2.45 | +12% |
| CPA | ₽145.30 | -8% |
| Conversions | 1,250 | +15% |
| LTV | ₽5,800 | +5% |

## Performance by Source

```dataview
TABLE roi, cpa, conversions
FROM "wiki/metrics"
WHERE date >= date(2026-05-01) AND date <= date(2026-05-08)
SORT roi DESC
```

## Trend Analysis

- **ROI Trend:** Upward (+12% week-over-week)
- **CPA Trend:** Downward (-8% week-over-week)
- **Seasonality:** Spring allergy season (+25% baseline)
```

### 9.4 Forecast Generation

**Прогнозирование метрик на 7 дней:**

```python
task = AnalyticsTaskInput(
    task_type="forecast_generation",
    date_range=(datetime(2026, 4, 1), datetime(2026, 5, 1)),  # Historical data
    metrics=["roi", "conversions"],
    output_format="json"
)

result = await agent.execute_task(task)

forecast = result.data["forecast"]
for day in forecast:
    print(f"{day['date']}: ROI={day['roi_forecast']:.2f} (±{day['confidence_interval']:.2f})")
```

**Output:**
```
2026-05-02: ROI=2.48 (±0.15)
2026-05-03: ROI=2.52 (±0.18)
2026-05-04: ROI=2.55 (±0.21)
2026-05-05: ROI=2.58 (±0.24)
2026-05-06: ROI=2.61 (±0.27)
2026-05-07: ROI=2.64 (±0.30)
2026-05-08: ROI=2.67 (±0.33)
```

### 9.5 Backfill Historical Data

**Пересчёт исторических данных:**

```python
task = AnalyticsTaskInput(
    task_type="backfill",
    date_range=(datetime(2026, 4, 1), datetime(2026, 5, 1)),
    sources=["performance_monitor", "budget_optimizer"],
    backfill_mode="incremental",  # Only missing dates
    idempotent=True
)

result = await agent.execute_task(task)

print(f"Backfilled {result.data['dates_processed']} dates")
print(f"Skipped {result.data['dates_skipped']} existing dates")
```

---

## 10. Зависимости

### 10.1 Python Packages

**Core Dependencies:**

```toml
[tool.poetry.dependencies]
python = "^3.11"
pandas = "^2.2.0"           # Data manipulation
numpy = "^1.26.0"           # Numerical operations
sqlalchemy = "^2.0.0"       # Database ORM
aiosqlite = "^0.20.0"       # Async SQLite
pydantic = "^2.6.0"         # Data validation
openpyxl = "^3.1.0"         # Excel export
statsmodels = "^0.14.0"     # ARIMA forecasting
prophet = "^1.1.5"          # Time-series forecasting
scikit-learn = "^1.4.0"     # Anomaly detection
```

**Optional Dependencies:**

```toml
[tool.poetry.group.ml.dependencies]
tensorflow = "^2.15.0"      # LSTM forecasting (optional)
torch = "^2.2.0"            # PyTorch (optional)
```

### 10.2 External Services

**Event Store:**
- **Purpose:** Source of raw events from all agents
- **Protocol:** Event Bus (async pub/sub)
- **Data Format:** JSON events with timestamp, type, data
- **Retention:** 90 days (configurable)

**Obsidian Vault:**
- **Purpose:** Dashboard storage and visualization
- **Path:** `./AIM/obsidian/analytics-magister/`
- **Format:** Markdown with Dataview queries
- **Sync:** Local filesystem (no API)

**Database:**
- **Type:** SQLite (async)
- **Path:** `./AIM/data/analytics.db`
- **Tables:** `bronze_events`, `silver_events`, `gold_aggregates`, `forecasts`
- **Backup:** Daily snapshots to `./AIM/backups/`

### 10.3 API Integrations

**None required** — Analytics Agent operates entirely on internal data from Event Bus and Event Store.

### 10.4 System Requirements

**Minimum:**
- Python 3.11+
- 4 GB RAM
- 10 GB disk space (for 90 days of events)

**Recommended:**
- Python 3.11+
- 8 GB RAM
- 50 GB disk space (for historical data + forecasts)
- SSD for faster aggregation

---

## 11. Deployment

### 11.1 Docker Configuration

**Dockerfile:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-dev

# Copy application
COPY AIM/ ./AIM/
COPY src/ ./src/

# Create data directories
RUN mkdir -p /app/AIM/data /app/AIM/obsidian/analytics-magister

# Set environment variables
ENV PYTHONPATH=/app
ENV ANALYTICS_DB_PATH=/app/AIM/data/analytics.db
ENV ANALYTICS_VAULT_PATH=/app/AIM/obsidian/analytics-magister

# Run agent
CMD ["python", "-m", "aim.subagents.analytics_agent"]
```

**docker-compose.yml:**

```yaml
version: '3.8'

services:
  analytics-agent:
    build: .
    container_name: analytics-agent
    volumes:
      - ./AIM/data:/app/AIM/data
      - ./AIM/obsidian:/app/AIM/obsidian
      - ./AIM/reports:/app/AIM/reports
    environment:
      - ANALYTICS_DB_PATH=/app/AIM/data/analytics.db
      - ANALYTICS_VAULT_PATH=/app/AIM/obsidian/analytics-magister
      - LOG_LEVEL=INFO
    restart: unless-stopped
    networks:
      - aim-network

networks:
  aim-network:
    external: true
```

### 11.2 Environment Variables

```bash
# Database
ANALYTICS_DB_PATH=./AIM/data/analytics.db

# Obsidian
ANALYTICS_VAULT_PATH=./AIM/obsidian/analytics-magister

# Event Bus
EVENT_BUS_URL=redis://localhost:6379

# Logging
LOG_LEVEL=INFO
LOG_FILE=./AIM/logs/analytics.log

# Performance
MAX_WORKERS=4
BATCH_SIZE=1000
AGGREGATION_TIMEOUT=900  # 15 minutes

# Data Quality
MIN_COMPLETENESS=0.99
MAX_NULL_RATE=0.01
MAX_DUPLICATE_RATE=0.001
```

### 11.3 Scaling Considerations

**Horizontal Scaling:**
- Analytics Agent is stateless (except for database)
- Can run multiple instances with shared database
- Use database connection pooling (max 10 connections per instance)

**Vertical Scaling:**
- Increase `MAX_WORKERS` for parallel processing
- Increase RAM for larger batch sizes
- Use SSD for faster I/O

**Data Partitioning:**
- Partition database by date (monthly partitions)
- Archive old data to cold storage (S3, GCS)
- Keep last 90 days in hot storage

---

## 12. Changelog

### Version 2.0.0 (2026-05-11)

**Major Rewrite:**
- Complete rewrite based on deep-research findings
- Added Medallion architecture (bronze/silver/gold layers)
- Implemented hierarchical rollups (1m→5m→1h→1d)
- Added seasonal adjustment for medical marketing
- Implemented predictive analytics (ARIMA/Prophet/LSTM)
- Added Obsidian dashboard generation
- Added Excel/CSV report export
- Improved data quality validation (>99% completeness)
- Added idempotent operations (DELETE + INSERT)
- Added Dead Letter Queue for invalid records

**Research Sources:**
- 30 high-quality sources from deep-research
- Topics: ETL pipelines, time-series aggregation, dashboard design, predictive analytics, medical marketing KPIs

**Breaking Changes:**
- New `AnalyticsTaskInput` dataclass (replaces old input format)
- New database schema (bronze/silver/gold tables)
- New output format (JSON with nested metrics)

### Version 1.0.0 (2026-05-11)

**Initial Release:**
- Basic aggregation functionality
- Simple dashboard generation
- JSON output only

---

## 13. TODO и будущие улучшения

### 13.1 Short-Term (Next Sprint)

- [ ] **Real-time Streaming:** Implement streaming aggregation (Apache Kafka, Apache Flink)
- [ ] **Advanced Visualizations:** Add interactive charts (Plotly, Altair) to dashboards
- [ ] **Automated Insights:** Generate natural language insights from metrics
- [ ] **Alerting System:** Send alerts on anomalies (Slack, email, Telegram)

### 13.2 Medium-Term (Next Quarter)

- [ ] **Machine Learning Insights:** Train models for pattern recognition
- [ ] **Causal Inference:** Identify causal relationships between metrics
- [ ] **Multi-Tenant Support:** Support multiple agencies in one instance
- [ ] **API Endpoints:** Expose metrics via REST API for external tools

### 13.3 Long-Term (Next Year)

- [ ] **Distributed Processing:** Migrate to Apache Spark for large-scale data
- [ ] **Data Warehouse:** Migrate to ClickHouse or BigQuery for analytics
- [ ] **Advanced Forecasting:** Implement ensemble models (ARIMA + Prophet + LSTM)
- [ ] **Recommendation Engine:** Suggest optimization actions based on metrics

---

## Приложение A: Полный отчёт исследования

**Источник:** `/Users/mikhaileliseev/Documents/Analytics_Research_20260511/research_summary.md`

**Ключевые находки:**

1. **Medallion Architecture:**
   - Bronze (raw) → Silver (cleaned) → Gold (aggregated)
   - 95% storage savings with hierarchical rollups
   - Idempotent operations (DELETE + INSERT, MERGE/UPSERT)

2. **Time-Series Forecasting:**
   - ARIMA: Simple trends, fast, interpretable
   - Prophet: Seasonality + holidays, robust to missing data
   - LSTM: Complex patterns, requires more data

3. **Medical Marketing Seasonality:**
   - Winter: +40% (flu, cold)
   - Spring: +25% (allergies)
   - Summer: +15% (cosmetic procedures)
   - Fall: +20% (back-to-school checkups)

4. **Data Quality Gates:**
   - Completeness: >99%
   - Null rate: <1%
   - Duplicate rate: <0.1%
   - Dead Letter Queue for invalid records

5. **Dashboard Design:**
   - Obsidian Dataview for live queries
   - Markdown tables for static reports
   - KPI cards for key metrics
   - Drill-down with filters

6. **Report Export:**
   - pandas + openpyxl for Excel
   - Multiple sheets (summary, details, charts)
   - Formatted cells (colors, borders, fonts)
   - Auto-width columns

**Полный отчёт:** 30 источников, 15,000+ слов, 8 секций

---

## Приложение B: Medical Marketing KPI Benchmarks

**Industry Standards (2026):**

| Metric | Benchmark | Source |
|--------|-----------|--------|
| ROI | 2.0-3.5x | Medical Marketing Association |
| CPA | ₽100-200 | Google Ads Healthcare Benchmarks |
| Conversion Rate | 3-5% | Healthcare Marketing Report 2026 |
| LTV | ₽5,000-10,000 | Patient Lifetime Value Study |
| CAC | ₽150-250 | Healthcare Acquisition Cost Report |
| Retention Rate | 60-75% | Patient Retention Study 2026 |
| Referral Rate | 15-25% | Medical Referral Benchmarks |

**Seasonal Adjustments:**

| Season | Adjustment | Reason |
|--------|------------|--------|
| Winter (Dec-Feb) | +40% | Flu, cold, respiratory issues |
| Spring (Mar-May) | +25% | Allergies, seasonal checkups |
| Summer (Jun-Aug) | +15% | Cosmetic procedures, elective surgery |
| Fall (Sep-Nov) | +20% | Back-to-school checkups, flu shots |

**Geo-Specific Multipliers:**

| Region | Multiplier | Reason |
|--------|------------|--------|
| Moscow | 1.5x | Higher income, more competition |
| St. Petersburg | 1.3x | Second-largest market |
| Regional Capitals | 1.0x | Baseline |
| Small Cities | 0.7x | Lower income, less competition |

---

**Конец спецификации**

**Статус:** ✅ Ready for Implementation  
**Версия:** 2.0.0  
**Дата:** 2026-05-11  
**Размер:** ~2,075 строк, ~65 KB  
**Исследование:** Analytics_Research_20260511 (30 источников)

