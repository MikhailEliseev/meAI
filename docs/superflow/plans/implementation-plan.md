# Implementation Plan: Business-Oriented CI Report

**Date:** 2026-05-05  
**Version:** 1.0 (Draft - awaiting spec review)  
**Status:** Draft  
**Governance:** Critical mode  
**Git Workflow:** Stacked PRs

---

## Overview

### Goal
Implement 18 business-oriented detectors and business report format in 5 sequential sprints using stacked PRs.

### Timeline
- **Total:** 8-10 hours
- **Sprints:** 5 (stacked PRs)
- **Review:** Dual-model per sprint (Critical mode)

### Branch Strategy
```
main
 └─> feat/ci-business-report-sprint-1 (Phase 1: 10 detectors)
      └─> feat/ci-business-report-sprint-2 (Phase 2: 7 detectors)
           └─> feat/ci-business-report-sprint-3 (Phase 3: Report format)
                └─> feat/ci-business-report-sprint-4 (Phase 4: Testing)
                     └─> feat/ci-business-report-sprint-5 (Phase 5: Docs)
```

---

## Sprint 1: Technology Stack Detectors (3-4 hours)

### Goal
Add 10 technology stack detectors to CI Deep Analyzer

### Tasks

#### 1.1 Create detector methods (2 hours)
- [ ] `_detect_cms()` - WordPress, Bitrix, Tilda, Wix, Joomla, Custom
- [ ] `_detect_analytics()` - GA, Yandex.Metrika, GTM, FB Pixel, VK Pixel
- [ ] `_detect_call_tracking()` - Calltouch, Callibri, CoMagic, Ringostat
- [ ] `_detect_live_chat()` - Jivo, Carrot, Bitrix24, Intercom
- [ ] `_detect_messengers()` - WhatsApp, Telegram, Viber buttons
- [ ] `_detect_booking_systems()` - YCLIENTS, Dikidi, custom forms
- [ ] `_detect_payment_systems()` - Stripe, PayPal, Yandex.Kassa, Tinkoff
- [ ] `_detect_cdn()` - Cloudflare, Akamai, CloudFront
- [ ] `_detect_hosting()` - Beget, Timeweb, AWS (via headers/DNS)
- [ ] `_detect_ab_testing()` - Google Optimize, VWO, Optimizely

**Implementation pattern:**
```python
def _detect_cms(self, html: str, headers: dict) -> dict:
    """Detect CMS with confidence scoring"""
    patterns = {
        "WordPress": ["wp-content", "wp-includes", "wp-json"],
        "Bitrix": ["bitrix/templates", "1C-Bitrix"],
        # ... more patterns
    }
    
    detected = None
    evidence = []
    confidence = 0.0
    
    for cms, patterns_list in patterns.items():
        matches = sum(1 for p in patterns_list if p in html)
        if matches > 0:
            detected = cms
            evidence = [p for p in patterns_list if p in html]
            confidence = min(1.0, matches / len(patterns_list) * 1.5)
            break
    
    if not detected:
        detected = "Custom"
        confidence = 0.5
    
    return {
        "cms": detected,
        "confidence": confidence,
        "evidence": evidence,
        "business_context": self._get_cms_context(detected)
    }
```

#### 1.2 Integrate into analysis pipeline (30 minutes)
- [ ] Update `_analyze_single_page()` to call new detectors
- [ ] Add results to page analysis output
- [ ] Update aggregation logic in `_aggregate_analysis()`

#### 1.3 Unit tests (1 hour)
- [ ] Test each detector with positive cases
- [ ] Test each detector with negative cases
- [ ] Test confidence scoring
- [ ] Test edge cases (multiple CMS patterns, etc.)

#### 1.4 Integration test (30 minutes)
- [ ] Test on 1 real competitor (Frau Clinic)
- [ ] Validate all 10 detectors work
- [ ] Check confidence scores are reasonable
- [ ] Verify no false positives

### Acceptance Criteria
- ✅ All 10 detectors implemented
- ✅ Unit tests passing (>90% coverage)
- ✅ Integration test on 1 competitor successful
- ✅ Confidence scores calibrated
- ✅ Code review passed

### Deliverables
- Modified: `ci_deep_analyzer.py` (+500 lines)
- New: `tests/test_detectors_sprint1.py`
- PR: `feat/ci-business-report-sprint-1` from `main`

---

## Sprint 2: Marketing Intelligence Detectors (2-3 hours)

### Goal
Add 7 marketing intelligence detectors

### Tasks

#### 2.1 Create detector methods (1.5 hours)
- [ ] `_detect_retargeting()` - FB, VK, myTarget, Google Ads pixels
- [ ] `_detect_email_marketing()` - Mailchimp, SendPulse, Unisender
- [ ] `_detect_crm()` - AmoCRM, Bitrix24, Salesforce
- [ ] `_detect_quiz_lead_magnets()` - Interactive forms, calculators
- [ ] `_detect_social_proof()` - Reviews widgets, testimonials
- [ ] `_detect_geo_targeting()` - Location-based content
- [ ] `_detect_promo_mechanics()` - Discounts, timers, popups

#### 2.2 Integrate & test (1-1.5 hours)
- [ ] Update analysis pipeline
- [ ] Unit tests for all 7 detectors
- [ ] Integration test on 2 competitors

### Acceptance Criteria
- ✅ All 7 detectors implemented
- ✅ Tests passing
- ✅ Integration test on 2 competitors successful

### Deliverables
- Modified: `ci_deep_analyzer.py` (+350 lines)
- New: `tests/test_detectors_sprint2.py`
- PR: `feat/ci-business-report-sprint-2` from `sprint-1`

---

## Sprint 3: Business Report Format (1-2 hours)

### Goal
Create business-oriented report generator (PDF + HTML)

### Tasks

#### 3.1 Create BusinessReportGenerator (1 hour)
- [ ] New file: `business_report.py`
- [ ] Class: `BusinessReportGenerator`
- [ ] Method: `generate_pdf()` - using ReportLab
- [ ] Method: `generate_html()` - using Jinja2
- [ ] Method: `_map_technical_to_business()` - context mapping

#### 3.2 Report templates (30 minutes)
- [ ] HTML template: `templates/business_report.html`
- [ ] PDF template structure
- [ ] Executive summary section
- [ ] Technology stack section
- [ ] Marketing intelligence section
- [ ] Competitive analysis section

#### 3.3 Test report generation (30 minutes)
- [ ] Test PDF generation
- [ ] Test HTML generation
- [ ] Validate report structure
- [ ] Check business context mapping

### Acceptance Criteria
- ✅ PDF report generates successfully
- ✅ HTML report generates successfully
- ✅ Business context is clear and actionable
- ✅ Report format is professional

### Deliverables
- New: `business_report.py` (~300 lines)
- New: `templates/business_report.html`
- Modified: `ci_deep_analyzer.py` (integrate report generation)
- PR: `feat/ci-business-report-sprint-3` from `sprint-2`

---

## Sprint 4: Testing & Validation (1-2 hours)

### Goal
Test on 6 real competitors and validate accuracy

### Tasks

#### 4.1 Run full analysis (1 hour)
- [ ] Analyze Frau Clinic
- [ ] Analyze Julia Sherbatova
- [ ] Analyze CIDK
- [ ] Analyze Tori Clinic
- [ ] Analyze Remedy Lab
- [ ] Analyze Platinental

#### 4.2 Validate results (30 minutes)
- [ ] Manual verification of each detector
- [ ] Check false positive rate (<5%)
- [ ] Validate confidence scores
- [ ] Review business context accuracy

#### 4.3 Fix issues (30 minutes)
- [ ] Fix any false positives
- [ ] Calibrate confidence scores
- [ ] Update business context if needed

### Acceptance Criteria
- ✅ All 6 competitors analyzed successfully
- ✅ False positive rate < 5%
- ✅ Confidence scores accurate
- ✅ Business reports are actionable

### Deliverables
- Test results: `AIM/data/ci-deep/validation_results.json`
- Bug fixes: `ci_deep_analyzer.py` (if needed)
- PR: `feat/ci-business-report-sprint-4` from `sprint-3`

---

## Sprint 5: Documentation (30 minutes)

### Goal
Document new features and usage

### Tasks

#### 5.1 Update documentation (20 minutes)
- [ ] Update README with new detectors
- [ ] Document business report format
- [ ] Add usage examples
- [ ] Create troubleshooting guide

#### 5.2 Create examples (10 minutes)
- [ ] Example: Generate business report
- [ ] Example: Interpret confidence scores
- [ ] Example: Customize report format

### Acceptance Criteria
- ✅ Documentation complete
- ✅ Examples working
- ✅ Troubleshooting guide helpful

### Deliverables
- Updated: `README.md`
- New: `docs/business-report-guide.md`
- New: `examples/generate_business_report.py`
- PR: `feat/ci-business-report-sprint-5` from `sprint-4`

---

## Review Process (Critical Mode)

### Per-Sprint Review
After each sprint:
1. **Code Review** (dual-model)
   - Technical reviewer: architecture, security, performance
   - Product reviewer: user value, business context
2. **Test Verification**
   - Run all tests
   - Validate on real data
3. **Approval Gate**
   - Both reviewers must approve
   - Fix any HIGH/CRITICAL issues before merge

### Final Review (Before Phase 3)
After Sprint 5:
1. **End-to-end test** on all 6 competitors
2. **Security audit** (input validation, XSS, privacy)
3. **Performance test** (speed, scalability)
4. **User acceptance** (show reports to stakeholders)

---

## Risk Mitigation

### Risk 1: False Positives
**Mitigation:** 
- Confidence scoring
- Manual validation on 6 competitors
- Golden dataset testing

### Risk 2: Time Overrun
**Mitigation:**
- Stacked PRs allow incremental delivery
- Can ship Sprint 1-2 if Sprint 3-5 delayed
- Critical mode ensures quality over speed

### Risk 3: Security Issues
**Mitigation:**
- Input sanitization in every detector
- Security review per sprint
- XSS testing on competitor HTML

---

## Success Metrics

### Technical
- ✅ All 18 detectors implemented
- ✅ False positive rate < 5%
- ✅ Test coverage > 90%
- ✅ Performance: <30 minutes per competitor

### Business
- ✅ Reports are actionable (sales team can use immediately)
- ✅ Business context is clear (no technical jargon)
- ✅ Competitive differentiation (vs Ahrefs/SEMrush)

---

## Dependencies

### External
- ReportLab (PDF generation)
- Jinja2 (HTML templating)
- Existing CI Deep Analyzer

### Internal
- Sprint 2 depends on Sprint 1 (same file)
- Sprint 3 depends on Sprint 1+2 (needs detector data)
- Sprint 4 depends on Sprint 1+2+3 (full system test)
- Sprint 5 depends on Sprint 1-4 (document everything)

---

## Rollback Plan

### Per-Sprint Rollback
If sprint fails review:
1. Revert PR
2. Fix issues
3. Re-submit for review

### Full Rollback
If entire initiative fails:
1. Revert all 5 PRs (stacked, so easy)
2. Main branch unchanged
3. No impact on production

---

**Status:** Draft (awaiting spec review feedback)  
**Next:** Incorporate review feedback, finalize plan, get user approval
