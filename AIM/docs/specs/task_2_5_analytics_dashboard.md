# Task 2.5: Analytics Dashboard

**Phase:** 11 - Client Acquisition  
**Sprint:** 2 - Lead Generation  
**Estimated Time:** 10 hours  
**Priority:** High  
**Status:** Planning

---

## Overview

Real-time analytics dashboard for monitoring lead acquisition, email campaigns, and conversion metrics. Provides actionable insights for optimizing marketing performance.

---

## Objectives

1. **Lead Analytics** - Track lead capture, scoring, and conversion rates
2. **Email Campaign Metrics** - Monitor email workflows, engagement, and ROI
3. **Conversion Funnel** - Visualize lead journey from capture to conversion
4. **Real-time Updates** - Live metrics with WebSocket updates
5. **Export & Reporting** - Generate reports for stakeholders

---

## Components

### 1. Analytics Service (`services/analytics/analytics_service.py`)

**Responsibilities:**
- Aggregate metrics from database
- Calculate KPIs (conversion rates, ROI, engagement)
- Generate time-series data for charts
- Cache frequently accessed metrics

**Key Methods:**
```python
async def get_lead_metrics(
    start_date: datetime,
    end_date: datetime,
    tier: Optional[str] = None,
) -> LeadMetrics

async def get_email_metrics(
    start_date: datetime,
    end_date: datetime,
    workflow_tier: Optional[str] = None,
) -> EmailMetrics

async def get_conversion_funnel(
    start_date: datetime,
    end_date: datetime,
) -> ConversionFunnel

async def get_real_time_stats() -> RealTimeStats
```

**Metrics to Track:**

**Lead Metrics:**
- Total leads captured
- Leads by tier (Hot/Warm/Cold)
- Leads by source (Landing Page, Referral, Organic, etc.)
- Leads by specialty
- Average lead score
- Lead capture rate (leads/day)
- Duplicate rate

**Email Metrics:**
- Emails sent/scheduled/failed
- Delivery rate (delivered/sent)
- Open rate (opened/delivered)
- Click rate (clicked/opened)
- Unsubscribe rate
- Bounce rate
- Complaint rate (spam reports)
- Emails by tier (Hot/Warm/Cold)
- Average time to open
- Average time to click

**Conversion Metrics:**
- Lead-to-task conversion rate (Linear tasks created)
- Lead-to-email conversion rate (workflows triggered)
- Email-to-engagement rate (opened + clicked)
- Tier distribution over time
- Score distribution

**Time-Series Data:**
- Leads per day/week/month
- Email engagement over time
- Conversion rates over time
- Score trends

### 2. Analytics Schemas (`schemas/analytics.py`)

**Data Models:**
```python
class LeadMetrics(BaseModel):
    total_leads: int
    leads_by_tier: dict[str, int]  # {"hot": 10, "warm": 20, "cold": 5}
    leads_by_source: dict[str, int]
    leads_by_specialty: dict[str, int]
    average_score: float
    capture_rate: float  # leads per day
    duplicate_rate: float  # percentage
    time_series: list[TimeSeriesPoint]

class EmailMetrics(BaseModel):
    total_sent: int
    total_scheduled: int
    total_failed: int
    delivery_rate: float  # percentage
    open_rate: float  # percentage
    click_rate: float  # percentage
    unsubscribe_rate: float
    bounce_rate: float
    complaint_rate: float
    emails_by_tier: dict[str, int]
    avg_time_to_open: float  # minutes
    avg_time_to_click: float  # minutes
    time_series: list[TimeSeriesPoint]

class ConversionFunnel(BaseModel):
    leads_captured: int
    leads_scored: int
    tasks_created: int
    emails_sent: int
    emails_opened: int
    emails_clicked: int
    conversion_rates: dict[str, float]

class RealTimeStats(BaseModel):
    leads_today: int
    emails_sent_today: int
    active_workflows: int
    pending_emails: int
    hot_leads_count: int
    last_updated: datetime

class TimeSeriesPoint(BaseModel):
    timestamp: datetime
    value: float
    label: str  # "2026-05-16", "Week 20", etc.
```

### 3. Dashboard API Endpoints (`api/analytics.py`)

**FastAPI Routes:**
```python
@router.get("/analytics/leads")
async def get_lead_analytics(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    tier: Optional[str] = None,
) -> LeadMetrics

@router.get("/analytics/emails")
async def get_email_analytics(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    tier: Optional[str] = None,
) -> EmailMetrics

@router.get("/analytics/funnel")
async def get_conversion_funnel(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
) -> ConversionFunnel

@router.get("/analytics/realtime")
async def get_realtime_stats() -> RealTimeStats

@router.get("/analytics/export")
async def export_report(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    format: str = Query("csv", regex="^(csv|json|pdf)$"),
) -> FileResponse
```

### 4. Real-time Updates (WebSocket)

**WebSocket Endpoint:**
```python
@router.websocket("/ws/analytics")
async def analytics_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            stats = await analytics_service.get_real_time_stats()
            await websocket.send_json(stats.dict())
            await asyncio.sleep(5)  # Update every 5 seconds
    except WebSocketDisconnect:
        pass
```

### 5. Report Generator (`services/analytics/report_generator.py`)

**Export Formats:**
- CSV: Tabular data for Excel
- JSON: Raw data for integrations
- PDF: Formatted report with charts (using ReportLab)

**Report Sections:**
- Executive Summary (KPIs)
- Lead Acquisition (charts + tables)
- Email Campaign Performance
- Conversion Funnel
- Recommendations (based on metrics)

---

## Database Queries

**Optimized Queries:**

```sql
-- Lead metrics by tier
SELECT 
    tier,
    COUNT(*) as count,
    AVG(score) as avg_score
FROM leads
WHERE created_at BETWEEN :start_date AND :end_date
GROUP BY tier;

-- Email engagement rates
SELECT 
    sw.tier,
    COUNT(DISTINCT se.id) as sent,
    COUNT(DISTINCT CASE WHEN ee.event_type = 'opened' THEN ee.email_id END) as opened,
    COUNT(DISTINCT CASE WHEN ee.event_type = 'clicked' THEN ee.email_id END) as clicked
FROM scheduled_emails se
JOIN email_workflows ew ON se.workflow_id = ew.id
LEFT JOIN email_events ee ON se.id = ee.email_id
WHERE se.sent_at BETWEEN :start_date AND :end_date
GROUP BY ew.tier;

-- Conversion funnel
SELECT 
    COUNT(DISTINCT l.id) as leads,
    COUNT(DISTINCT lt.id) as tasks,
    COUNT(DISTINCT ew.id) as workflows,
    COUNT(DISTINCT se.id) as emails_sent,
    COUNT(DISTINCT CASE WHEN ee.event_type = 'opened' THEN ee.email_id END) as emails_opened
FROM leads l
LEFT JOIN linear_tasks lt ON l.id = lt.lead_id
LEFT JOIN email_workflows ew ON l.id = ew.lead_id
LEFT JOIN scheduled_emails se ON ew.id = se.workflow_id
LEFT JOIN email_events ee ON se.id = ee.email_id
WHERE l.created_at BETWEEN :start_date AND :end_date;

-- Time series (leads per day)
SELECT 
    DATE(created_at) as date,
    COUNT(*) as count
FROM leads
WHERE created_at BETWEEN :start_date AND :end_date
GROUP BY DATE(created_at)
ORDER BY date;
```

**Indexes for Performance:**
```sql
CREATE INDEX idx_leads_created_at ON leads(created_at);
CREATE INDEX idx_leads_tier ON leads(tier);
CREATE INDEX idx_scheduled_emails_sent_at ON scheduled_emails(sent_at);
CREATE INDEX idx_email_events_email_id ON email_events(email_id);
CREATE INDEX idx_email_events_event_type ON email_events(event_type);
```

---

## Caching Strategy

**Redis Cache:**
- Real-time stats: 30 seconds TTL
- Daily metrics: 5 minutes TTL
- Weekly/monthly metrics: 1 hour TTL

**Cache Keys:**
```python
f"analytics:leads:{start_date}:{end_date}:{tier}"
f"analytics:emails:{start_date}:{end_date}:{tier}"
f"analytics:funnel:{start_date}:{end_date}"
f"analytics:realtime"
```

---

## Testing Strategy

### Unit Tests (`tests/services/analytics/`)

**Test Coverage:**
1. **test_analytics_service.py** (20 tests)
   - Lead metrics calculation
   - Email metrics calculation
   - Conversion funnel calculation
   - Real-time stats
   - Time series generation
   - Edge cases (no data, single lead, etc.)

2. **test_report_generator.py** (10 tests)
   - CSV export
   - JSON export
   - PDF export
   - Report formatting
   - Error handling

### Integration Tests (`tests/api/`)

3. **test_analytics_api.py** (15 tests)
   - GET /analytics/leads
   - GET /analytics/emails
   - GET /analytics/funnel
   - GET /analytics/realtime
   - GET /analytics/export
   - WebSocket connection
   - Date range validation
   - Tier filtering

**Total:** 45 tests

---

## Dependencies

```txt
# Already installed:
fastapi>=0.115.0
sqlalchemy>=2.0.0
redis>=5.0.1

# New dependencies:
reportlab>=4.0.0  # PDF generation
pillow>=10.0.0    # Image processing for charts
matplotlib>=3.8.0 # Chart generation (optional, for PDF reports)
```

---

## Implementation Plan

### Step 1: Analytics Service (4h)
- Create `AnalyticsService` class
- Implement metric calculation methods
- Add database queries with SQLAlchemy
- Add caching with Redis

### Step 2: Schemas & API (2h)
- Create Pydantic schemas for metrics
- Implement FastAPI endpoints
- Add WebSocket endpoint for real-time updates

### Step 3: Report Generator (2h)
- Implement CSV export
- Implement JSON export
- Implement PDF export with ReportLab

### Step 4: Testing (2h)
- Write unit tests for AnalyticsService
- Write unit tests for ReportGenerator
- Write integration tests for API endpoints
- Test WebSocket real-time updates

---

## Success Criteria

- ✅ All 45 tests passing
- ✅ Real-time stats update every 5 seconds
- ✅ API response time < 500ms (with caching)
- ✅ Export reports in CSV/JSON/PDF formats
- ✅ Accurate metrics (validated against raw data)
- ✅ WebSocket connection stable for 1+ hour

---

## Future Enhancements (Phase 12+)

- Interactive charts (Chart.js, Plotly)
- Custom date ranges and filters
- Alerts and notifications (threshold-based)
- Predictive analytics (forecast lead volume)
- A/B testing metrics
- Multi-tenant analytics (per client)
- Mobile-responsive dashboard UI

---

## Notes

- Focus on backend API first (frontend dashboard in Phase 12)
- Use existing email/lead data for testing
- Cache aggressively to reduce database load
- Real-time updates via WebSocket (not polling)
- PDF reports for stakeholder presentations
