# Medical Compliance - Key Findings

## FDA Enforcement Verification

### openFDA API
```python
GET https://api.fda.gov/drug/enforcement.json?search=reason_for_recall:"[claim_keyword]"&limit=100
```

**Key Points:**
- All claims need "competent and reliable scientific evidence" (RCTs, peer-reviewed)
- Off-label prohibition (cannot promote unapproved uses)
- Comparative claims require head-to-head clinical data

## HIPAA Compliance Detection

### Critical Rule (HHS OCR 2022, reaffirmed 2024)
Standard analytics = PHI disclosure when:
- Page is patient-facing (appointment booking, symptom checkers)
- Tracking pixel transmits: IP + page URL + user agent
- Third-party receives data (Meta Pixel, GA, TikTok)

### Detection Method
```python
# Automated scanning for:
1. Tracking pixels on patient-facing pages (Meta, GA, LinkedIn)
2. Form data transmission to non-BAA vendors
3. Logged-in portal tracking (ZERO third-party tags allowed)
```

### Compliant Architecture
- ✅ Server-side conversion tracking (PHI stripped pre-transmission)
- ✅ Strict event allowlist (only non-PHI events)
- ✅ BAA requirement for all vendors touching PHI

## AMA Ethical Standards

### Prohibited Practices
- ❌ Outcome guarantees ("100% success rate")
- ❌ Diagnosis-assumptive targeting ("Do you have diabetes?")
- ❌ Emotional manipulation (fear-based urgency)
- ❌ Unsubstantiated superiority ("Best surgeon in [city]")

### Compliant Messaging Framework
| Retire | Use Instead |
|--------|-------------|
| "Cure", "Eliminate", "Guaranteed" | "Manage", "Treat", "May help" |
| "Diabetics", "Cancer patients" | "People managing diabetes" |
| "Act now", "Limited time" | "Schedule when ready" |
| "Best", "#1", "Leading" | "Experienced", "Board-certified" |

## Risk Scoring Framework

### Four-Tier Classification
**Formula:** Likelihood (1-5) × Severity (1-5) = Risk Score (1-25)

| Risk | Score | Financial Impact | Action |
|------|-------|------------------|--------|
| CRITICAL | 20-25 | >$1M | Immediate legal review + halt |
| HIGH | 15-19 | $250K-$1M | Compliance review + medical sign-off |
| MEDIUM | 8-14 | $50K-$250K | Internal review + revisions |
| LOW | 1-7 | <$50K | Monitor + fix in next update |

## Pre-Launch Compliance Scorecard (20 Points)

**Ad Copy (5 pts):**
- [ ] No outcome guarantees (1 pt)
- [ ] Evidence-based claims only (1 pt)
- [ ] Problem-aware language (1 pt)
- [ ] Proper disclaimers (1 pt)
- [ ] No diagnosis-assumptive targeting (1 pt)

**Tracking & Privacy (5 pts):**
- [ ] No third-party pixels on patient pages (2 pts)
- [ ] BAAs signed with all PHI vendors (2 pts)
- [ ] Privacy notice updated (1 pt)

**Score Interpretation:**
- 16-20: Launch-ready
- 11-15: Strengthen before launch
- ≤10: Invest in compliance foundation first

## Implementation Recommendations

1. ✅ Build compliance scanner using openFDA API
2. ✅ Automated tracking pixel detection on patient-facing pages
3. ✅ Language pattern flagging (prohibited terms)
4. ✅ Risk score calculation pre-publication (flag ≥15)
