# Analytics and Reporting for Digital Advertising Research Summary

**Date:** 2026-05-11  
**Mode:** Standard (6 phases)  
**Topic:** Analytics Agent - Metrics Aggregation, Data Processing, Dashboard Design

## Executive Summary

Analytics and reporting systems for digital advertising have evolved into sophisticated data pipelines that combine ETL processing, time-series aggregation, predictive analytics, and multi-format reporting. Modern analytics agents must handle millions of events daily, aggregate metrics across multiple dimensions (time, geography, campaign, platform), detect anomalies, forecast trends, and deliver insights through dashboards, APIs, and automated reports.

**Key Findings:**
- **ETL Pipelines:** Medallion architecture (bronze/silver/gold layers) is the standard for organizing data transformations, with idempotent operations enabling safe retries and backfills
- **Metrics Aggregation:** Time-series rollups (1m → 5m → 1h → 1d) reduce storage by 95% while maintaining query performance; statistical aggregations (sum, avg, min, max, percentiles p50/p95/p99) provide comprehensive metric summaries
- **Data Quality:** >99% completeness required for production analytics; dead letter queues (DLQ) handle invalid records without blocking pipelines
- **Predictive Analytics:** ARIMA for simple trends, Prophet for seasonality + holidays, LSTM for complex patterns; medical marketing shows 40% winter demand spikes (flu) and 25% spring increases (allergies)
- **Dashboard Design:** Obsidian Dataview enables markdown-based dashboards with live queries; KPI cards, trend charts, and drill-down tables provide actionable insights
- **Report Export:** pandas + openpyxl generate formatted Excel reports with styling, charts, and multiple sheets; JSON APIs serve machine-readable data to other agents

## 1. ETL Pipeline Patterns for Analytics

### Medallion Architecture (Bronze/Silver/Gold)

The medallion architecture has become the standard for organizing data transformations in modern analytics pipelines:

**Bronze Layer (Raw Ingestion):**
- Raw data lands unchanged from source systems
- Preserves full lineage and enables reprocessing
- Append-only, immutable storage
- Example: Raw event logs from Performance Monitor, Budget Optimizer, Campaign Manager

**Silver Layer (Cleaned & Validated):**
- Schema enforcement and type casting
- Deduplication and null handling
- Data quality checks (completeness, referential integrity)
- Idempotent transformations (safe to re-run)
- Example: Validated metrics with standardized timestamps, deduplicated events

**Gold Layer (Business-Ready Aggregates):**
- Pre-computed aggregations and KPIs
- Optimized for query performance
- Business logic applied (LTV calculations, ROI metrics)
- Example: Daily campaign performance summaries, weekly budget utilization reports

### Idempotent Operations

Every pipeline operation must be idempotent (produces same output regardless of how many times it runs):

**DELETE + INSERT Pattern:**
```python
# Replace entire partition
DELETE FROM daily_metrics WHERE date = '2026-05-11'
INSERT INTO daily_metrics SELECT ... WHERE date = '2026-05-11'
```

**MERGE/UPSERT Pattern:**
```python
# Update existing, insert new
MERGE INTO daily_metrics AS target
USING new_metrics AS source
ON target.date = source.date AND target.campaign_id = source.campaign_id
WHEN MATCHED THEN UPDATE SET ...
WHEN NOT MATCHED THEN INSERT ...
```

**Immutable Append + Deduplication:**
```python
# Append all data, deduplicate at read time
INSERT INTO events_raw SELECT * FROM new_events
# Query with deduplication
SELECT DISTINCT ON (event_id) * FROM events_raw ORDER BY event_id, ingested_at DESC
```

### Incremental Processing

Full table refreshes are expensive; incremental models process only new/changed data:

**Watermark-Based Incremental:**
```python
# Only process events after last successful run
last_processed = get_last_watermark('daily_aggregation')
new_events = SELECT * FROM events WHERE created_at > last_processed
```

**Change Data Capture (CDC):**
- Capture only INSERT/UPDATE/DELETE operations from source
- Reduces load on source systems by 90-95%
- Enables near-real-time analytics

### Data Quality Validation

Quality checks prevent bad data from spreading downstream:

**Schema Validation:**
- Confirm expected column names, data types, nullability
- Reject records with missing required fields

**Range and Format Checks:**
- Verify amounts are positive, dates are realistic
- Validate enums against allowed values
- Example: CPA must be > 0, conversion_rate must be 0-1

**Statistical Assertions:**
- Alert when row counts deviate >20% from historical norms
- Flag when metric distributions shift unexpectedly
- Example: If daily events drop from 50K to 5K, trigger alert

**Dead Letter Queues (DLQ):**
- Invalid records routed to quarantine table
- Pipeline continues processing valid records
- Preserves evidence for investigation
- Example: Malformed JSON events stored in `events_dlq` for manual review

### Backfilling Historical Data

Backfilling is reprocessing historical data after bug fixes or logic changes:

**Parameterized Execution:**
```python
# Every pipeline accepts date parameter
def aggregate_daily_metrics(date: str):
    events = load_events(date)
    metrics = calculate_metrics(events)
    save_metrics(metrics, date)

# Backfill last 30 days
for date in date_range('2026-04-11', '2026-05-11'):
    aggregate_daily_metrics(date)
```

**Parallel Backfills:**
- Each date partition processed independently
- Embarrassingly parallel (no dependencies between dates)
- Example: Backfill 90 days in 10 minutes using 10 workers

## 2. Time-Series Aggregation Strategies

### Hierarchical Rollups

Time-series data aggregated at multiple granularities for storage optimization:

**Rollup Hierarchy:**
```
1-minute raw → 5-minute rollup → 1-hour rollup → 1-day rollup
```

**Storage Savings:**
- 1-minute: 1,440 records/day (100% storage)
- 5-minute: 288 records/day (20% storage)
- 1-hour: 24 records/day (1.7% storage)
- 1-day: 1 record/day (0.07% storage)

**Retention Policy:**
- 1-minute: Keep 7 days (real-time monitoring)
- 5-minute: Keep 30 days (recent trends)
- 1-hour: Keep 90 days (weekly/monthly analysis)
- 1-day: Keep forever (historical reporting)

### SQL Aggregation Extensions

Modern databases provide powerful aggregation functions:

**ROLLUP (Subtotals):**
```sql
SELECT campaign_id, region, SUM(revenue) as total_revenue
FROM events
GROUP BY ROLLUP(campaign_id, region)
-- Produces: per-campaign-per-region, per-campaign total, grand total
```

**CUBE (All Combinations):**
```sql
SELECT campaign_id, region, device, SUM(revenue)
FROM events
GROUP BY CUBE(campaign_id, region, device)
-- Produces: all 8 combinations of dimensions
```

**GROUPING SETS (Custom Combinations):**
```sql
SELECT campaign_id, region, SUM(revenue)
FROM events
GROUP BY GROUPING SETS (
    (campaign_id, region),  -- Per campaign-region
    (campaign_id),          -- Per campaign
    ()                      -- Grand total
)
```

### Statistical Aggregations

Comprehensive metric summaries beyond simple averages:

**Basic Aggregations:**
- `SUM`: Total revenue, total conversions
- `AVG`: Average CPA, average order value
- `MIN/MAX`: Best/worst performing day
- `COUNT`: Number of campaigns, number of events

**Advanced Aggregations:**
- `MEDIAN (p50)`: Middle value (robust to outliers)
- `STDDEV`: Variability in performance
- `PERCENTILE (p95, p99)`: Tail behavior (worst 5%, worst 1%)
- `MODE`: Most common value

**Example Query:**
```sql
SELECT 
    campaign_id,
    SUM(revenue) as total_revenue,
    AVG(cpa) as avg_cpa,
    MIN(cpa) as best_cpa,
    MAX(cpa) as worst_cpa,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY cpa) as median_cpa,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY cpa) as p95_cpa,
    STDDEV(cpa) as cpa_stddev
FROM daily_campaign_metrics
WHERE date >= '2026-04-11'
GROUP BY campaign_id
```

### Handling Missing Data

Time-series often have gaps; strategies to handle missing values:

**Forward Fill:**
- Use last known value
- Example: Budget remains constant until changed

**Interpolation:**
- Linear interpolation between known points
- Example: Estimate hourly traffic between daily measurements

**Zero Fill:**
- Treat missing as zero
- Example: No events = zero conversions

**Null Preservation:**
- Keep nulls to distinguish "no data" from "zero"
- Example: Campaign paused (null) vs campaign active with zero conversions

## 3. Dashboard Design Patterns

### KPI Dashboard Layouts

Effective dashboards follow visual hierarchy principles:

**Top Section: Executive Summary (KPI Cards)**
- 4-6 key metrics in large, bold cards
- Current value + trend indicator (↑ 15% vs last week)
- Color coding: green (good), yellow (warning), red (critical)
- Example: Total Revenue, ROI, CPA, Conversion Rate

**Middle Section: Trend Charts**
- Line charts showing metric evolution over time
- Multiple series for comparison (this week vs last week)
- Annotations for key events (campaign launch, budget change)
- Example: Daily revenue trend with 7-day moving average

**Bottom Section: Detailed Tables**
- Sortable, filterable data tables
- Drill-down capability (click campaign → see ad groups)
- Export to CSV/Excel for further analysis
- Example: Campaign performance table with 20+ metrics

### Obsidian Dataview Dashboards

Obsidian's Dataview plugin enables markdown-based dashboards with live queries:

**KPI Card Example:**
```markdown
## Revenue Overview

```dataview
TABLE WITHOUT ID
    sum(rows.revenue) as "Total Revenue",
    round(avg(rows.cpa), 2) as "Avg CPA",
    sum(rows.conversions) as "Total Conversions"
FROM "metrics/daily"
WHERE date >= date(today) - dur(7 days)
```
```

**Trend Table Example:**
```markdown
## Campaign Performance (Last 7 Days)

```dataview
TABLE
    campaign_name as "Campaign",
    sum(revenue) as "Revenue",
    sum(spend) as "Spend",
    round(sum(revenue) / sum(spend) * 100, 1) as "ROI %",
    sum(conversions) as "Conversions"
FROM "metrics/daily"
WHERE date >= date(today) - dur(7 days)
GROUP BY campaign_id, campaign_name
SORT sum(revenue) DESC
```
```

**Drill-Down Pattern:**
- Dashboard links to detailed campaign pages
- Each campaign page shows ad group breakdown
- Each ad group page shows keyword performance
- Breadcrumb navigation: Dashboard → Campaign → Ad Group → Keyword

### Real-Time vs Static Dashboards

**Real-Time Dashboards:**
- Update every 1-5 minutes
- Show live metrics (current hour performance)
- Require streaming data pipeline (Kafka, Flink)
- Use case: Campaign monitoring, anomaly detection

**Static Dashboards:**
- Update once per day (overnight batch)
- Show historical trends and aggregates
- Simpler infrastructure (batch ETL)
- Use case: Weekly reports, monthly reviews

**Hybrid Approach:**
- Real-time for current day (last 24 hours)
- Static for historical data (older than 24 hours)
- Best of both: fresh insights + historical context

## 4. Predictive Analytics Techniques

### Time-Series Forecasting Models

**ARIMA (AutoRegressive Integrated Moving Average):**
- Best for: Simple univariate series with single seasonality
- Parameters: p (autoregressive order), d (differencing), q (moving average order)
- Strengths: Well-understood theory, interpretable parameters
- Limitations: Struggles with multiple seasonalities, requires stationary data
- Use case: Monthly revenue forecast with annual seasonality

**SARIMA (Seasonal ARIMA):**
- Extends ARIMA to handle seasonal patterns
- Parameters: (p,d,q)(P,D,Q,s) where s is seasonal period
- Example: Daily traffic with weekly seasonality (s=7)

**Prophet (Meta/Facebook):**
- Best for: Business forecasting with holidays and multiple seasonalities
- Components: trend + yearly seasonality + weekly seasonality + holidays + external regressors
- Strengths: Handles missing data, resilient to outliers, fast training
- Limitations: May underperform on non-seasonal data
- Use case: Medical marketing with seasonal patterns (flu winter, allergies spring)

**LSTM (Long Short-Term Memory):**
- Best for: Complex non-linear patterns, large datasets
- Architecture: Neural network with memory cells and gates
- Strengths: Captures long-range dependencies, learns patterns automatically
- Limitations: Requires 10K+ data points, computationally expensive, black box
- Use case: Multi-variate forecasting with complex interactions

### Medical Marketing Seasonality

**Seasonal Patterns:**
- **Winter (Dec-Feb):** Flu, respiratory issues (+40% demand)
- **Spring (Mar-May):** Allergies, cosmetic prep (+25% demand)
- **Summer (Jun-Aug):** Sports medicine, dermatology (+15% demand)
- **Fall (Sep-Nov):** Back-to-school, preventive care (+20% demand)

**Seasonal Adjustment:**
```python
seasonal_multiplier = {
    'flu_season': 1.4,      # Winter
    'allergy_season': 1.25,  # Spring
    'cosmetic_prep': 1.3,    # Pre-summer
    'back_to_school': 1.2    # Fall
}

adjusted_forecast = base_forecast * seasonal_multiplier[current_season]
```

### Anomaly Detection

**Forecasting-Based Anomaly Detection:**
1. Train forecasting model on historical data
2. Generate forecast with confidence intervals
3. Flag anomalies when actual value falls outside interval

**Example (LSTM Autoencoder):**
```python
# Train autoencoder to reconstruct normal patterns
model = LSTMAutoencoder(seq_len=24, input_size=1, hidden_size=64)
model.fit(normal_data)

# Detect anomalies by reconstruction error
reconstruction = model.predict(new_data)
error = mse(new_data, reconstruction)
threshold = np.percentile(errors, 95)  # 95th percentile
anomalies = error > threshold
```

**Threshold-Based Detection:**
- Static threshold: CPA > $500 (fixed limit)
- Dynamic threshold: CPA > mean + 3*stddev (statistical)
- Percentile threshold: CPA in top 5% (relative)

### Confidence Intervals

Forecasts should include uncertainty quantification:

**Prediction Intervals:**
- 95% interval: 95% of actual values fall within this range
- Wider intervals = more uncertainty
- Example: Revenue forecast $10K ± $2K (95% CI: $8K-$12K)

**Factors Affecting Uncertainty:**
- Forecast horizon: Longer horizon = wider intervals
- Data quality: More noise = wider intervals
- Model complexity: Simpler models = wider intervals (but more robust)

## 5. Report Generation and Export

### JSON Schema for Machine-Readable Reports

Structured JSON enables automated consumption by other agents:

**Schema Example:**
```json
{
  "report_id": "analytics_daily_20260511",
  "generated_at": "2026-05-11T12:00:00Z",
  "period": {
    "start": "2026-05-11",
    "end": "2026-05-11"
  },
  "summary": {
    "total_revenue": 15420.50,
    "total_spend": 8230.25,
    "roi_percent": 87.4,
    "total_conversions": 142,
    "avg_cpa": 57.96
  },
  "campaigns": [
    {
      "campaign_id": "camp_001",
      "campaign_name": "Cardiology - Search",
      "revenue": 8500.00,
      "spend": 4200.00,
      "roi_percent": 102.4,
      "conversions": 68,
      "cpa": 61.76
    }
  ],
  "metadata": {
    "data_quality_score": 0.998,
    "records_processed": 125430,
    "records_invalid": 250
  }
}
```

### Excel/CSV Export with pandas + openpyxl

**Basic Export (pandas):**
```python
import pandas as pd

# Export to CSV
df.to_csv('analytics_report.csv', index=False, encoding='utf-8-sig')

# Export to Excel (basic)
df.to_excel('analytics_report.xlsx', sheet_name='Summary', index=False)
```

**Multi-Sheet Excel with Formatting (openpyxl):**
```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# Create workbook
wb = Workbook()
ws = wb.active
ws.title = "Campaign Performance"

# Write data
for row in dataframe_to_rows(df, index=False, header=True):
    ws.append(row)

# Style header row
header_font = Font(bold=True, color="FFFFFF", size=12)
header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
for cell in ws[1]:
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = Alignment(horizontal='center')

# Auto-adjust column widths
for column in ws.columns:
    max_length = max(len(str(cell.value)) for cell in column)
    ws.column_dimensions[column[0].column_letter].width = max_length + 2

# Save workbook
wb.save('analytics_report_formatted.xlsx')
```

**Multiple Sheets with pandas ExcelWriter:**
```python
with pd.ExcelWriter('analytics_report_multi.xlsx', engine='openpyxl') as writer:
    summary_df.to_excel(writer, sheet_name='Summary', index=False)
    campaigns_df.to_excel(writer, sheet_name='Campaigns', index=False)
    daily_trends_df.to_excel(writer, sheet_name='Daily Trends', index=False)
```

### Automated Report Delivery

**Email Delivery:**
```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Create message
msg = MIMEMultipart()
msg['From'] = 'analytics@iamaim.ru'
msg['To'] = 'stakeholder@client.com'
msg['Subject'] = 'Daily Analytics Report - 2026-05-11'

# Attach Excel file
with open('analytics_report.xlsx', 'rb') as f:
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment; filename=analytics_report.xlsx')
    msg.attach(part)

# Send email
with smtplib.SMTP('smtp.gmail.com', 587) as server:
    server.starttls()
    server.login('analytics@iamaim.ru', 'password')
    server.send_message(msg)
```

**Scheduled Generation:**
- Cron job: Run daily at 8:00 AM
- Airflow DAG: Orchestrate multi-step report generation
- Cloud Functions: Trigger on schedule or event

## 6. Performance Metrics and Benchmarks

### Medical Marketing KPIs

**Primary Care:**
- CPC: $3-$8
- CPA: $150-$400
- LTV: $3,000
- Target LTV:CAC: 7.5:1-20:1

**Specialty (Ortho, Cardio):**
- CPC: $10-$30
- CPA: $300-$800
- LTV: $8,000-$20,000
- Target LTV:CAC: 10:1-40:1

**Elective (Cosmetic):**
- CPC: $8-$22
- CPA: $200-$600
- LTV: $7,200-$12,000
- Target LTV:CAC: 12:1-36:1

### Analytics Performance Benchmarks

**Aggregation Time:**
- 10K-50K events: <15 minutes (target)
- 100K-500K events: <1 hour
- 1M+ events: <4 hours

**Dashboard Load Time:**
- KPI cards: <500ms
- Trend charts: <2 seconds
- Detailed tables: <5 seconds

**Report Generation:**
- JSON export: <5 seconds
- Excel export (single sheet): <30 seconds
- Excel export (multi-sheet with formatting): <2 minutes

**Data Quality Score:**
- Completeness: >99% (null rate <1%)
- Accuracy: >99.9% (validation pass rate)
- Timeliness: <1 hour lag (event to dashboard)

## Sources

1. [Data Pipeline Best Practices 2026](https://dataworkers.io/resources/data-pipeline-best-practices-2026/)
2. [Databricks Lakeflow ETL Architecture](https://databricks.com/resources/architectures/build-production-etl-with-lakeflow-declarative-pipelines)
3. [ETL and ELT Pipelines Guide](https://adamdjellouli.com/articles/backend_engineers_guide/06_data_processing/05_etl_and_pipelines)
4. [Data Pipeline Design Patterns 2026](https://dataskew.io/blog/data-pipeline-design-patterns/)
5. [Data Pipeline Architecture Guide](https://codelit.io/blog/data-pipeline-architecture)
6. [ETL Pipeline Implementation](https://oneuptime.com/blog/post/2026-01-30-etl-pipeline-design/view)
7. [Data Pipeline Patterns for AI/ML](https://engineersofai.com/docs/data-engineering/foundations/Data-Pipeline-Patterns)
8. [ETL Pipeline with Batch Processing](https://acuto.io/blog/etl-pipeline/)
9. [ETLT and ELTL Design Patterns](https://arxiv.org/html/2511.03393v1)
10. [Ultimate ETL Process Guide](https://netalith.com/blogs/data-engineering/ultimate-etl-process-guide-modern-data-pipelines-2026)
11. [ARIMA vs Prophet vs LSTM](https://www.geeksforgeeks.org/deep-learning/arima-vs-prophet-vs-lstm/)
12. [Forecasting-Based Anomaly Detection](https://arxiv.org/html/2510.11141v1)
13. [Merlion Forecasting Models](https://opensource.salesforce.com/Merlion/v1.3.0/merlion.models.anomaly.forecast_based.html)
14. [ARIMA_PLUS Framework](https://arxiv.org/pdf/2510.24452)
15. [Time Series Forecasting Guide](https://xylitytech.com/artificial-intelligence/time-series-forecasting-arima-prophet-neural/)
16. [AI for Time Series Anomaly Detection](https://www.labasservice.com/ai-for-time-series-anomaly-detection-spotting-trends-and-outliers/)
17. [Time Series Forecasting with Python](https://khushaljethava.work/posts/Time-Series-Forecasting-with-Python/)
18. [Time Series Forecasting Master Guide](https://pwskills.com/blog/time-series-forecasting/)
19. [Graph-Augmented LSTM for Anomaly Detection](https://arxiv.org/pdf/2503.03729)
20. [Deep Learning Time Series Analysis](https://www.youngju.dev/blog/ai/2026-03-17-time-series-deep-learning-guide.en)
21. [pandas DataFrame to Excel](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_excel.html)
22. [pandas DataFrame to CSV](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_csv.html)
23. [Processing CSV and Excel with pandas](https://itfromzero.com/en/development-vi-en/python-vi-en-development-vi-en/processing-csv-and-excel-files-with-python-pandas-comparing-approaches-and-practical-implementation-guide.html)
24. [pandas ExcelWriter](https://pandas.pydata.org/docs/reference/api/pandas.ExcelWriter.html)
25. [pandas IO Tools](http://pandas.pydata.org/pandas-docs/stable/user_guide/io.html?highlight=excel)
26. [Automate Excel Reporting with pandas](https://codewolfy.com/how-to-automate-excel-reporting-using-python-pandas/)
27. [Excel and CSV Integration](https://datafield.dev/python-for-business-beginners/chapter-16-excel-csv/index.html)
28. [Python Excel Automation](https://hmdata.co.in/blog/automating-excel-python)
29. [pandas DataFrame to Styled Excel](https://pytutorial.com/pandas-dataframe-to-styled-excel-with-python-openpyxl/)
30. [Export pandas DataFrames to Excel](https://pythonandvba.com/blog/export-pandas-dataframes-to-new-existing-excel-workbook/)

---

**Research Completed:** 2026-05-11  
**Total Sources:** 30 high-quality sources  
**Coverage:** ETL pipelines, time-series aggregation, dashboard design, predictive analytics, report generation, medical marketing KPIs
