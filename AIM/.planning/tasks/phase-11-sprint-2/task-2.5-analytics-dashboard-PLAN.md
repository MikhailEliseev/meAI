# Task 2.5: Analytics Dashboard - Implementation Plan

**Phase:** 11 - Client Acquisition  
**Sprint:** 2 - Lead Generation  
**Estimated Time:** 10 hours  
**Status:** In Progress  
**Started:** 2026-05-16 23:53 GMT+3

---

## Implementation Steps

### Step 1: Analytics Service Core (4h)

**Files to Create:**
- `AIM/src/aim/services/analytics/__init__.py`
- `AIM/src/aim/services/analytics/analytics_service.py` (500 lines)
- `AIM/src/aim/schemas/analytics.py` (300 lines)

**Implementation:**

1. **Schemas** (`schemas/analytics.py`):
   ```python
   class LeadMetrics(BaseModel)
   class EmailMetrics(BaseModel)
   class ConversionFunnel(BaseModel)
   class RealTimeStats(BaseModel)
   class TimeSeriesPoint(BaseModel)
   ```

2. **AnalyticsService** (`services/analytics/analytics_service.py`):
   - `get_lead_metrics()` - Aggregate lead data by tier/source/specialty
   - `get_email_metrics()` - Calculate email engagement rates
   - `get_conversion_funnel()` - Track lead journey stages
   - `get_real_time_stats()` - Current day statistics
   - `_calculate_time_series()` - Generate time-series data
   - `_get_cached_metrics()` - Redis caching helper

**Database Queries:**
- Lead metrics by tier (COUNT, AVG score)
- Email engagement rates (delivery, open, click)
- Conversion funnel (leads → tasks → emails → engagement)
- Time series (leads per day/week/month)

**Caching:**
- Redis cache with TTL (30s for real-time, 5min for daily, 1h for weekly)
- Cache keys: `analytics:leads:{start}:{end}:{tier}`

---

### Step 2: API Endpoints (2h)

**Files to Create:**
- `AIM/src/aim/api/analytics.py` (250 lines)

**Endpoints:**
```python
GET /api/analytics/leads?start_date=...&end_date=...&tier=...
GET /api/analytics/emails?start_date=...&end_date=...&tier=...
GET /api/analytics/funnel?start_date=...&end_date=...
GET /api/analytics/realtime
GET /api/analytics/export?start_date=...&end_date=...&format=csv|json|pdf
WS  /ws/analytics (WebSocket for real-time updates)
```

**Implementation:**
- FastAPI router with dependency injection
- Query parameter validation (dates, tier enum)
- WebSocket connection for real-time stats (5s interval)
- Error handling (404, 422, 500)

---

### Step 3: Report Generator (2h)

**Files to Create:**
- `AIM/src/aim/services/analytics/report_generator.py` (350 lines)

**Export Formats:**

1. **CSV Export:**
   - Lead metrics table
   - Email metrics table
   - Conversion funnel table
   - Time series data

2. **JSON Export:**
   - Raw metrics data
   - Structured for API consumption

3. **PDF Export:**
   - Executive summary (KPIs)
   - Lead acquisition charts
   - Email campaign performance
   - Conversion funnel visualization
   - Recommendations section

**Dependencies:**
- reportlab (PDF generation)
- pillow (image processing)
- csv (built-in)

---

### Step 4: Testing (2h)

**Files to Create:**
- `AIM/tests/services/analytics/__init__.py`
- `AIM/tests/services/analytics/test_analytics_service.py` (450 lines, 20 tests)
- `AIM/tests/services/analytics/test_report_generator.py` (300 lines, 10 tests)
- `AIM/tests/api/test_analytics_api.py` (400 lines, 15 tests)

**Test Coverage:**

1. **test_analytics_service.py** (20 tests):
   - Lead metrics calculation (5 tests)
   - Email metrics calculation (5 tests)
   - Conversion funnel (3 tests)
   - Real-time stats (2 tests)
   - Time series generation (3 tests)
   - Edge cases (2 tests)

2. **test_report_generator.py** (10 tests):
   - CSV export (3 tests)
   - JSON export (2 tests)
   - PDF export (3 tests)
   - Error handling (2 tests)

3. **test_analytics_api.py** (15 tests):
   - GET /analytics/leads (3 tests)
   - GET /analytics/emails (3 tests)
   - GET /analytics/funnel (2 tests)
   - GET /analytics/realtime (2 tests)
   - GET /analytics/export (3 tests)
   - WebSocket connection (2 tests)

**Total:** 45 tests

---

## Database Indexes

**Add to migration:**
```sql
CREATE INDEX idx_leads_created_at ON leads(created_at);
CREATE INDEX idx_leads_tier ON leads(tier);
CREATE INDEX idx_scheduled_emails_sent_at ON scheduled_emails(sent_at);
CREATE INDEX idx_email_events_email_id ON email_events(email_id);
CREATE INDEX idx_email_events_event_type ON email_events(event_type);
```

---

## Dependencies to Add

```txt
reportlab>=4.0.0  # PDF generation
pillow>=10.0.0    # Image processing
```

---

## Implementation Order

1. ✅ Create specification (task_2_5_analytics_dashboard.md)
2. ✅ Create implementation plan (this file)
3. ⏳ Step 1: Analytics Service Core (4h)
   - Create schemas
   - Implement AnalyticsService
   - Add database queries
   - Add Redis caching
4. ⏳ Step 2: API Endpoints (2h)
   - Create FastAPI router
   - Implement REST endpoints
   - Add WebSocket endpoint
5. ⏳ Step 3: Report Generator (2h)
   - CSV export
   - JSON export
   - PDF export
6. ⏳ Step 4: Testing (2h)
   - Unit tests for AnalyticsService
   - Unit tests for ReportGenerator
   - Integration tests for API

---

## Success Criteria

- ✅ All 45 tests passing
- ✅ API response time < 500ms (with caching)
- ✅ Real-time stats update every 5 seconds via WebSocket
- ✅ Export reports in CSV/JSON/PDF formats
- ✅ Accurate metrics validated against raw data

---

## Notes

- Use existing Lead, EmailWorkflow, ScheduledEmail, EmailEvent models
- Cache aggressively to reduce database load
- WebSocket for real-time updates (not polling)
- PDF reports for stakeholder presentations
- Focus on backend API (frontend dashboard in Phase 12)
