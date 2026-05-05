# Technical Specification: Business-Oriented CI Report

**Date:** 2026-05-05  
**Version:** 1.0  
**Status:** Draft for review  
**Governance:** Critical mode

---

## Overview

### Goal
Add 18 business-oriented detectors to CI Deep Analyzer and create a business-focused report format that transforms technical analysis into sales-ready competitive intelligence.

### Success Criteria
- ✅ All 18 detectors implemented and tested
- ✅ Accuracy validated on 6 real competitors
- ✅ Business report format (PDF + HTML)
- ✅ Security audit passed
- ✅ Confidence scores for all detectors
- ✅ False positive rate < 5%

### Non-Goals (Deferred to Phase 2)
- ❌ Change detection & alerts
- ❌ AI-generated narrative reports
- ❌ Actionable playbooks
- ❌ Temporal analysis

---

## Architecture

### Component Overview

```
CI Deep Analyzer (existing)
├── _analyze_single_page()          # Entry point
├── _analyze_seo()                  # Existing
├── _analyze_content()              # Existing
├── _analyze_technical()            # Existing - EXTEND
├── _analyze_schema()               # Existing
├── _analyze_core_web_vitals()      # Existing
├── _analyze_mobile_usability()     # Existing
├── _analyze_accessibility()        # Existing
├── _analyze_security()             # Existing
└── NEW METHODS:
    ├── _detect_cms()               # Detector 1
    ├── _detect_analytics()         # Detector 2
    ├── _detect_call_tracking()     # Detector 3
    ├── _detect_live_chat()         # Detector 4
    ├── _detect_messengers()        # Detector 5
    ├── _detect_booking_systems()   # Detector 6
    ├── _detect_payment_systems()   # Detector 7
    ├── _detect_cdn()               # Detector 8
    ├── _detect_hosting()           # Detector 9
    ├── _detect_ab_testing()        # Detector 10
    ├── _detect_retargeting()       # Detector 11
    ├── _detect_email_marketing()   # Detector 12
    ├── _detect_crm()               # Detector 13
    ├── _detect_quiz_lead_magnets() # Detector 14
    ├── _detect_social_proof()      # Detector 15
    ├── _detect_geo_targeting()     # Detector 16
    ├── _detect_promo_mechanics()   # Detector 17
    └── _extract_semantic_core()    # Detector 18

Business Report Generator (new file)
└── business_report.py
    ├── BusinessReportGenerator
    ├── generate_pdf()
    ├── generate_html()
    └── _map_technical_to_business()
```

---

## Detailed Design

### Phase 1: Technology Stack Detectors (10 detectors)

#### Detector 1: CMS Detection

**Method:** `_detect_cms(html: str, headers: dict) -> dict`

**Detection patterns:**
```python
{
    "WordPress": ["wp-content", "wp-includes", "wp-json"],
    "Bitrix": ["bitrix/templates", "1C-Bitrix", "/bitrix/"],
    "Tilda": ["tilda.cc", "tilda.ws", "tildacdn.com"],
    "Wix": ["wix.com", "wixstatic.com"],
    "Joomla": ["joomla", "/components/com_"],
    "Custom": None  # Default if no match
}
```

**Output:**
```python
{
    "cms": "WordPress" | "Bitrix" | "Tilda" | "Wix" | "Joomla" | "Custom",
    "confidence": 0.0-1.0,
    "evidence": ["wp-content found", "wp-json API detected"],
    "business_context": "WordPress CMS - flexible, large plugin ecosystem"
}
```

**Confidence scoring:**
- 1.0: Multiple strong signals (3+ patterns)
- 0.8: 2 patterns
- 0.6: 1 pattern
- 0.3: Weak signal (generic pattern)

---

#### Detector 2: Analytics Detection

**Method:** `_detect_analytics(html: str) -> dict`

**Detection patterns:**
```python
{
    "Google Analytics": [r"UA-\d+", r"G-[A-Z0-9]+", "gtag.js", "analytics.js"],
    "Yandex.Metrika": ["mc.yandex.ru", "metrika/tag.js", r"ym\(\d+"],
    "Google Tag Manager": ["googletagmanager.com/gtm.js", r"GTM-[A-Z0-9]+"],
    "Facebook Pixel": ["facebook.net/en_US/fbevents.js", r"fbq\("],
    "VK Pixel": ["vk.com/js/api/openapi.js", r"VK\.Retargeting"]
}
```

**Output:**
```python
{
    "analytics": {
        "google_analytics": {"detected": True, "confidence": 0.95, "id": "UA-12345"},
        "yandex_metrika": {"detected": True, "confidence": 1.0, "id": "87654321"},
        "google_tag_manager": {"detected": False},
        "facebook_pixel": {"detected": True, "confidence": 0.8},
        "vk_pixel": {"detected": False}
    },
    "business_context": "Full analytics stack - data-driven decision making"
}
```

---

#### Detector 3: Call Tracking Detection

**Method:** `_detect_call_tracking(html: str) -> dict`

**Detection patterns:**
```python
{
    "Calltouch": ["calltouch.ru", "ct-widget"],
    "Callibri": ["callibri.ru", "clbr"],
    "CoMagic": ["comagic.ru", "comagic-widget"],
    "Ringostat": ["ringostat.com", "roistat"]
}
```

**Output:**
```python
{
    "call_tracking": {
        "provider": "Calltouch" | None,
        "detected": True | False,
        "confidence": 0.0-1.0
    },
    "business_context": "Call tracking enabled - optimizing phone lead attribution"
}
```

---

#### Detectors 4-10: Similar structure

- **Detector 4:** Live Chat (Jivo, Carrot, Bitrix24, Intercom)
- **Detector 5:** Messengers (WhatsApp, Telegram, Viber buttons)
- **Detector 6:** Booking Systems (YCLIENTS, Dikidi, custom forms)
- **Detector 7:** Payment Systems (Stripe, PayPal, Yandex.Kassa, Tinkoff)
- **Detector 8:** CDN (Cloudflare, Akamai, CloudFront)
- **Detector 9:** Hosting (Beget, Timeweb, AWS - via headers/DNS)
- **Detector 10:** A/B Testing (Google Optimize, VWO, Optimizely)

---

### Phase 2: Marketing Intelligence Detectors (7 detectors)

#### Detectors 11-17: Pattern-based detection

- **Detector 11:** Retargeting Pixels (FB, VK, myTarget, Google Ads)
- **Detector 12:** Email Marketing (Mailchimp, SendPulse, Unisender)
- **Detector 13:** CRM Integration (AmoCRM, Bitrix24, Salesforce)
- **Detector 14:** Quiz/Lead Magnets (interactive forms, calculators)
- **Detector 15:** Social Proof (reviews widgets, testimonials)
- **Detector 16:** Geo-Targeting (location-based content)
- **Detector 17:** Promo Mechanics (discounts, timers, popups)

---

### Phase 3: Semantic Intelligence

#### Detector 18: Semantic Core Extraction

**Method:** `_extract_semantic_core(html: str, url: str) -> dict`

**Extraction strategy:**
1. Extract keywords from:
   - Title tag
   - Meta keywords (if present)
   - H1-H3 headings
   - First 500 words of content
   - Alt text from images
   - URL structure

2. Analyze keyword density
3. Identify primary vs secondary keywords
4. Detect keyword clustering

**Output:**
```python
{
    "primary_keywords": ["пластическая хирургия москва", "ботокс"],
    "secondary_keywords": ["ринопластика", "блефаропластика"],
    "keyword_density": {"ботокс": 0.03, "пластическая хирургия": 0.02},
    "content_topics": ["facial procedures", "body contouring"],
    "business_context": "Optimized for high-volume keywords in Moscow market"
}
```

---

## Business Report Format

### New File: `business_report.py`

```python
class BusinessReportGenerator:
    """Generate business-oriented CI reports"""
    
    def __init__(self, deep_analysis: dict):
        self.analysis = deep_analysis
        
    def generate_pdf(self, output_path: str) -> str:
        """Generate PDF report using ReportLab"""
        pass
        
    def generate_html(self, output_path: str) -> str:
        """Generate HTML report with charts"""
        pass
        
    def _map_technical_to_business(self) -> dict:
        """Map technical metrics to business insights"""
        return {
            "technology_stack": self._summarize_tech_stack(),
            "marketing_maturity": self._score_marketing_tools(),
            "competitive_positioning": self._identify_strengths_weaknesses(),
            "opportunities": self._find_opportunities()
        }
```

### Report Structure

**Executive Summary (1 page):**
- Competitor name & URL
- Overall score (0-100)
- Key strengths (top 3)
- Key weaknesses (top 3)
- Biggest opportunity

**Technology Stack (1-2 pages):**
- CMS & hosting
- Analytics & tracking
- Marketing tools
- Payment & booking systems

**Marketing Intelligence (1-2 pages):**
- Lead generation tools
- Retargeting & remarketing
- Email marketing
- CRM integration

**Content Strategy (1 page):**
- Semantic core
- Primary keywords
- Content gaps
- SEO optimization level

**Competitive Analysis (1 page):**
- Comparison matrix (You vs Them)
- Strengths to defend
- Weaknesses to exploit
- Recommended actions

---

## Security Considerations

### Input Validation

**All external data must be sanitized:**
```python
def _sanitize_html(html: str) -> str:
    """Remove potentially dangerous content"""
    # Remove script tags
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    # Remove event handlers
    html = re.sub(r'\son\w+\s*=\s*["\'][^"\']*["\']', '', html, flags=re.IGNORECASE)
    return html
```

**URL validation:**
```python
def _validate_url(url: str) -> bool:
    """Validate URL before fetching"""
    parsed = urlparse(url)
    # Only HTTP/HTTPS
    if parsed.scheme not in ['http', 'https']:
        return False
    # No localhost/private IPs
    if parsed.hostname in ['localhost', '127.0.0.1']:
        return False
    return True
```

### Data Privacy

**PII handling:**
- Do NOT store emails, phones, names from competitor sites
- Redact sensitive data in reports
- Add disclaimer: "Competitive intelligence from public sources only"

**GDPR compliance:**
- Only analyze public data
- Respect robots.txt
- Rate limiting (2s delay between requests)
- User-agent identification

---

## Testing Strategy

### Unit Tests

**Test each detector independently:**
```python
def test_detect_cms_wordpress():
    html = '<link href="/wp-content/themes/...">'
    result = analyzer._detect_cms(html, {})
    assert result['cms'] == 'WordPress'
    assert result['confidence'] >= 0.8

def test_detect_analytics_google():
    html = '<script>gtag("config", "G-ABC123")</script>'
    result = analyzer._detect_analytics(html)
    assert result['analytics']['google_analytics']['detected'] == True
```

### Integration Tests

**Test on 6 real competitors:**
1. Frau Clinic
2. Julia Sherbatova
3. CIDK
4. Tori Clinic
5. Remedy Lab
6. Platinental

**Validation criteria:**
- Accuracy: Manual verification of each detector
- False positive rate < 5%
- Confidence scores calibrated
- Business context makes sense

### Golden Dataset

**Create test fixtures:**
```python
GOLDEN_DATASET = {
    "wordpress_site": {
        "html": "...",
        "expected": {"cms": "WordPress", "confidence": 1.0}
    },
    "bitrix_site": {
        "html": "...",
        "expected": {"cms": "Bitrix", "confidence": 0.95}
    }
}
```

---

## Performance Requirements

### Speed
- Single page analysis: < 5 seconds
- Full competitor analysis (50 pages): 10-30 minutes
- Report generation: < 10 seconds

### Reliability
- Uptime: 99.9%
- Error rate: < 1%
- Graceful degradation on API failures

### Scalability
- Support 10+ concurrent analyses
- Handle 1000+ competitors in database
- Report generation queue

---

## Deployment Plan

### Phase 1: Technology Stack (Sprint 1)
- Add 10 detectors to `ci_deep_analyzer.py`
- Update `_analyze_single_page()` to call new methods
- Unit tests for each detector
- Integration test on 1 competitor

### Phase 2: Marketing Intelligence (Sprint 2)
- Add 7 detectors
- Update aggregation logic
- Integration test on 3 competitors

### Phase 3: Business Report (Sprint 3)
- Create `business_report.py`
- Implement PDF generation
- Implement HTML generation
- Test report format

### Phase 4: Testing & Validation (Sprint 4)
- Test on all 6 competitors
- Validate accuracy
- Calibrate confidence scores
- Fix false positives

### Phase 5: Documentation (Sprint 5)
- Update README
- Create usage examples
- Document detector patterns
- Create troubleshooting guide

---

## Monitoring & Maintenance

### Metrics to Track
- Detector accuracy per competitor
- False positive rate per detector
- Confidence score distribution
- Report generation time
- API error rate

### Alerts
- False positive rate > 5%
- Confidence score < 0.5 for any detector
- Report generation failure
- API timeout

### Maintenance Schedule
- Quarterly detector review (patterns may change)
- Monthly accuracy validation
- Weekly error log review

---

## Open Questions

### Resolved ✅
1. Report format: Both (PDF + HTML)
2. Pricing: Included in base package
3. Update frequency: On-demand

### Still Open 🤔
1. PDF library: ReportLab vs WeasyPrint?
2. Chart library: Matplotlib vs Plotly?
3. Hosting detection: DNS lookup or header-based?

---

## Appendix

### Dependencies
```python
# Existing
aiohttp
beautifulsoup4
lxml

# New
reportlab  # PDF generation
jinja2     # HTML templating
matplotlib # Charts (optional)
```

### File Structure
```
AIM/src/aim/subagents/competitive_intel/
├── agents/
│   ├── ci_deep_analyzer.py      # MODIFY (add 18 detectors)
│   └── business_report.py       # NEW
├── templates/
│   ├── business_report.html     # NEW
│   └── business_report_pdf.html # NEW
└── tests/
    ├── test_detectors.py        # NEW
    └── test_business_report.py  # NEW
```

### Estimated Effort
- Sprint 1 (10 detectors): 3-4 hours
- Sprint 2 (7 detectors): 2-3 hours
- Sprint 3 (report format): 1-2 hours
- Sprint 4 (testing): 1-2 hours
- Sprint 5 (docs): 30 minutes
- **Total: 8-10 hours**

---

**Status:** Ready for review  
**Next:** Dual-model spec review (Critical mode)
