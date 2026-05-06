# CI Business Report - Usage Guide

**Version:** 1.0  
**Last Updated:** 2026-05-06

---

## Overview

CI Business Report System анализирует конкурентов и генерирует бизнес-ориентированные отчёты в PDF и HTML форматах.

## Quick Start

### 1. Basic Analysis

```python
import asyncio
from aim.subagents.competitive_intel.agents.ci_deep_analyzer import CIDeepAnalyzer
from aim.core.task import Task

async def analyze_competitor():
    # Create analyzer
    analyzer = CIDeepAnalyzer(
        agent_id="ci_analyzer",
        database_url="sqlite:///aim.db",
        vault_path="./obsidian"
    )
    
    # Create task
    task = Task(
        subtask_id="analyze_competitor_1",
        action="deep_analysis",
        payload={
            "competitors": [
                {
                    "name": "Frau Klinik",
                    "url": "https://frauklinik.ru"
                }
            ]
        }
    )
    
    # Execute analysis
    result = await analyzer.execute_task(task)
    
    return result.result

# Run
analysis = asyncio.run(analyze_competitor())
print(f"Analyzed: {analysis['name']}")
print(f"Pages: {analysis['total_pages_found']}")
```

### 2. Generate Business Report

```python
from aim.subagents.competitive_intel.agents.business_report import BusinessReportGenerator

# Create report generator
report_gen = BusinessReportGenerator(analysis)

# Generate HTML report
html_path = report_gen.generate_html("reports/frau_klinik.html")
print(f"HTML report: {html_path}")

# Generate PDF report (requires WeasyPrint)
try:
    pdf_path = report_gen.generate_pdf("reports/frau_klinik.pdf")
    print(f"PDF report: {pdf_path}")
except ImportError:
    print("WeasyPrint not installed. Install with: pip install weasyprint")
```

### 3. Analyze Multiple Competitors

```python
async def analyze_multiple():
    analyzer = CIDeepAnalyzer(
        agent_id="ci_analyzer",
        database_url="sqlite:///aim.db",
        vault_path="./obsidian"
    )
    
    competitors = [
        {"name": "Frau Klinik", "url": "https://frauklinik.ru"},
        {"name": "Tori Clinic", "url": "https://toriclinic.ru"},
        {"name": "Platinental", "url": "https://platinental.ru"}
    ]
    
    task = Task(
        subtask_id="analyze_multiple",
        action="deep_analysis",
        payload={"competitors": competitors}
    )
    
    result = await analyzer.execute_task(task)
    
    # Generate reports for each
    for profile in result.result['deep_profiles']:
        report_gen = BusinessReportGenerator(profile)
        report_gen.generate_html(f"reports/{profile['name']}.html")
    
    return result.result

# Run
results = asyncio.run(analyze_multiple())
print(f"Analyzed {len(results['deep_profiles'])} competitors")
```

---

## Understanding the Report

### Overall Score (0-100)

Комбинация технологического стека и маркетинговой зрелости:
- **0-40:** Начальный уровень
- **41-70:** Средний уровень
- **71-100:** Продвинутый уровень

### Marketing Maturity

Оценка маркетинговых инструментов (0-100):
- **Начальный (0-40):** 0-2 инструмента
- **Средний (41-70):** 3-5 инструментов
- **Продвинутый (71-100):** 6-7 инструментов

### Strengths & Weaknesses

**Strengths (Top 3):**
- Что конкурент делает хорошо
- Какие инструменты использует эффективно

**Weaknesses (Top 3):**
- Что конкурент упускает
- Какие инструменты отсутствуют

### Opportunities

**Top 3 рекомендации:**
- Что можно сделать лучше конкурента
- Какие инструменты внедрить первыми

---

## Detectors Reference

### Technology Stack (Sprint 1)

#### 1. CMS Detection
```python
result = analyzer._detect_cms(html, headers)
# Returns: {"cms": "WordPress", "confidence": 1.0, "business_context": "..."}
```

**Detects:**
- WordPress, Bitrix, Tilda, Wix, Joomla, Custom

**Headers used:**
- X-Powered-By

#### 2. Analytics Detection
```python
result = analyzer._detect_analytics(html)
# Returns: {"analytics": {"google_analytics": {"detected": True, ...}}}
```

**Detects:**
- Google Analytics, Yandex.Metrika, Google Tag Manager, Facebook Pixel, VK Pixel

#### 3. Call Tracking
```python
result = analyzer._detect_call_tracking(html)
# Returns: {"provider": "Calltouch", "detected": True, ...}
```

**Detects:**
- Calltouch, Callibri, CoMagic, Ringostat

#### 4. Live Chat
```python
result = analyzer._detect_live_chat(html)
# Returns: {"provider": "Jivo", "detected": True, ...}
```

**Detects:**
- Jivo, Carrot, Bitrix24, Intercom

#### 5. Messengers
```python
result = analyzer._detect_messengers(html)
# Returns: {"messengers": {"WhatsApp": True, "Telegram": True}, "count": 2}
```

**Detects:**
- WhatsApp, Telegram, Viber

#### 6. Booking Systems
```python
result = analyzer._detect_booking_systems(html)
# Returns: {"system": "YCLIENTS", "detected": True, ...}
```

**Detects:**
- YCLIENTS, Dikidi, Custom

#### 7. Payment Systems
```python
result = analyzer._detect_payment_systems(html)
# Returns: {"systems": {"Yandex.Kassa": True}, "count": 1}
```

**Detects:**
- Stripe, PayPal, Yandex.Kassa, Tinkoff, Robokassa

#### 8. CDN Detection
```python
result = analyzer._detect_cdn(html)
# Returns: {"provider": "Cloudflare", "detected": True, ...}
```

**Detects:**
- Cloudflare, Akamai, CloudFront, Fastly

#### 9. Hosting Detection
```python
result = analyzer._detect_hosting(html, headers)
# Returns: {"provider": "Beget", "detected": True, ...}
```

**Detects:**
- Beget, Timeweb, AWS, Google Cloud

**Headers used:**
- Server

#### 10. A/B Testing
```python
result = analyzer._detect_ab_testing(html)
# Returns: {"tool": "Google Optimize", "detected": True, ...}
```

**Detects:**
- Google Optimize, VWO, Optimizely

---

### Marketing Intelligence (Sprint 2)

#### 11. Retargeting Pixels
```python
result = analyzer._detect_retargeting(html)
# Returns: {"pixels": {"Facebook": True, "VK": True}, "count": 2}
```

**Detects:**
- Facebook, VK, myTarget, Google Ads

#### 12. Email Marketing
```python
result = analyzer._detect_email_marketing(html)
# Returns: {"platform": "Mailchimp", "detected": True, ...}
```

**Detects:**
- Mailchimp, SendPulse, Unisender, GetResponse

#### 13. CRM Integration
```python
result = analyzer._detect_crm(html)
# Returns: {"crm": "AmoCRM", "detected": True, ...}
```

**Detects:**
- AmoCRM, Bitrix24, Salesforce, HubSpot

#### 14. Quiz/Lead Magnets
```python
result = analyzer._detect_quiz_lead_magnets(html)
# Returns: {"detected": True, "confidence": 0.7, ...}
```

**Detects:**
- Quiz, Calculator, Interactive forms

#### 15. Social Proof
```python
result = analyzer._detect_social_proof(html)
# Returns: {"elements": {"reviews": True, "ratings": True}, "count": 2}
```

**Detects:**
- Reviews, Ratings, Counters, Certificates

#### 16. Geo-Targeting
```python
result = analyzer._detect_geo_targeting(html)
# Returns: {"detected": True, "confidence": 0.8, ...}
```

**Detects:**
- Geolocation, City selector, Location-based content

#### 17. Promo Mechanics
```python
result = analyzer._detect_promo_mechanics(html)
# Returns: {"mechanics": {"discount": True, "timer": True}, "count": 2}
```

**Detects:**
- Discounts, Timers, Popups, Urgency

---

## Advanced Usage

### Custom Analysis

```python
# Analyze specific page types only
task = Task(
    subtask_id="analyze_homepage",
    action="deep_analysis",
    payload={
        "competitors": [{"name": "Clinic", "url": "https://clinic.ru"}],
        "page_types": ["homepage", "services"]  # Only these types
    }
)
```

### Error Handling

```python
try:
    result = await analyzer.execute_task(task)
    
    if result.status == "failed":
        print(f"Analysis failed: {result.error}")
    else:
        # Process results
        for profile in result.result['deep_profiles']:
            if 'error' in profile:
                print(f"Error for {profile['name']}: {profile['error']}")
            else:
                # Generate report
                report_gen = BusinessReportGenerator(profile)
                report_gen.generate_html(f"reports/{profile['name']}.html")
                
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Accessing Raw Data

```python
# Get raw detector results
analysis = asyncio.run(analyze_competitor())

for page in analysis['pages_analyzed_data']:
    print(f"\nPage: {page['url']}")
    print(f"CMS: {page['cms']['cms']}")
    print(f"Analytics: {page['analytics']['analytics']}")
    print(f"Call Tracking: {page['call_tracking']['provider']}")
    # ... etc
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'meai'"

**Solution:** Ensure you're running from the correct directory with meai framework installed.

```bash
cd /Users/mikhaileliseev/Desktop/Dev/!meAI
export PYTHONPATH=/Users/mikhaileliseev/Desktop/Dev/!meAI/AIM/src:$PYTHONPATH
```

### Issue: "WeasyPrint not installed"

**Solution:** Install WeasyPrint for PDF generation:

```bash
pip install weasyprint
```

Or use HTML reports only:

```python
# Skip PDF generation
report_gen.generate_html("report.html")  # Works without WeasyPrint
```

### Issue: "Failed to fetch" errors

**Possible causes:**
- Website blocks automated requests
- SSL certificate issues
- Network timeout

**Solution:** Check logs and retry with different User-Agent:

```python
# Analyzer rotates User-Agents automatically
# If still failing, website may have strong anti-bot protection
```

### Issue: Low detection accuracy

**Possible causes:**
- Website uses custom implementations
- JavaScript-heavy site (requires rendering)
- Obfuscated code

**Solution:** Check raw HTML and adjust patterns if needed.

---

## Best Practices

### 1. Batch Analysis

Analyze multiple competitors in one task for efficiency:

```python
# Good: One task, multiple competitors
task = Task(payload={"competitors": [c1, c2, c3]})

# Avoid: Multiple tasks for each competitor
# (creates unnecessary overhead)
```

### 2. Report Storage

Organize reports by date and competitor:

```python
from datetime import datetime

date = datetime.now().strftime("%Y-%m-%d")
report_gen.generate_html(f"reports/{date}/{competitor_name}.html")
```

### 3. Error Logging

Always check for errors in results:

```python
if 'error' in profile:
    logger.error(f"Analysis failed for {profile['name']}: {profile['error']}")
else:
    # Process successful result
    pass
```

### 4. Performance

For large-scale analysis:
- Use async/await properly
- Limit concurrent requests
- Cache results when possible

---

## Examples

See `AIM/tests/integration_test.py` for complete working example.

---

**Questions?** Check `docs/superflow/` for technical documentation.
