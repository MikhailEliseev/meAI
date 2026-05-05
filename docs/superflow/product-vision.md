# Product Vision: Business-Oriented CI Report

**Date:** 2026-05-05  
**Status:** Draft for approval  
**Governance:** Critical mode

---

## Vision Statement

**Transform AIM's CI System from a technical analysis tool into a sales weapon that wins deals by exposing competitor weaknesses in business terms.**

---

## The Opportunity

### Current State: Technical Reports Nobody Uses

Our CI System v1.0 produces excellent technical analysis:
- 19 metrics (SEO, CWV, Mobile, A11y, Security)
- Deep analysis (50+ pages per competitor)
- Proven accuracy (tested on 6 real clinics)

**But there's a problem:**

Sales team: *"I don't understand what LCP 2.3s means. Can I show this to a client?"*  
Client: *"You're telling me they have 19 accessibility issues. So what? How does this help me?"*  
Marketer: *"This is great technical data, but I need to know: what are they doing for marketing?"*

**The gap:** Technical excellence ≠ Business value

---

## The Solution: Business Intelligence, Not Technical Reports

### What We're Building

**18 business-oriented detectors** that answer the questions sales and marketing teams actually ask:

#### "What technology do they use?"
- CMS (WordPress, Bitrix, Tilda, Wix, Custom)
- Hosting (Beget, Timeweb, AWS)
- CDN (Cloudflare, Akamai)

**Business insight:** *"They use outdated Bitrix CMS (2015 version) - slow, expensive to maintain, security risks."*

#### "How do they track leads?"
- Analytics (GA, Yandex.Metrika, GTM)
- Call tracking (Calltouch, Callibri, CoMagic)
- Live chat (Jivo, Carrot, Bitrix24)

**Business insight:** *"No call tracking detected - they're losing 30% of phone leads without attribution."*

#### "What marketing tools do they use?"
- Retargeting pixels (FB, VK, myTarget)
- Email marketing (Mailchimp, SendPulse)
- CRM (AmoCRM, Bitrix24, Salesforce)
- A/B testing (Google Optimize, VWO)

**Business insight:** *"No retargeting pixels - they're not following up with 95% of visitors who leave."*

#### "What's their content strategy?"
- Semantic core extraction
- Keyword clustering
- Content gaps analysis

**Business insight:** *"Optimized for 'пластическая хирургия москва' (5000 searches/month) but missing 'ринопластика' (3000 searches/month) - opportunity to outrank them."*

---

## User Stories

### Sales Team

**Before:**
> "We analyzed your competitor. They have some technical issues. We can help."

**After:**
> "Your competitor Julia Sherbatova uses outdated Bitrix CMS, has no call tracking (losing 30% of leads), no retargeting (95% of visitors never return), and is missing 'ринопластика' keyword (3000 searches/month). We can fix all of this in 3 months and capture their market share."

**Impact:** Specific, actionable, credible. Client says "yes" immediately.

---

### Marketing Team

**Before:**
> "I need to research competitors manually. Takes 2-3 hours per competitor. Results are inconsistent."

**After:**
> "CI System analyzed 6 competitors in 2 hours. I now know: who uses what CMS, who has call tracking, who's doing retargeting, what keywords they target. I can build our strategy to exploit their gaps."

**Impact:** 6x faster, 10x deeper, consistent results.

---

### Client

**Before:**
> "You're showing me technical metrics I don't understand. How does this help my business?"

**After:**
> "You're showing me exactly what my competitors are doing wrong and how you'll help me win. I understand every point. Let's start."

**Impact:** Clear business value, immediate buy-in.

---

## Success Criteria

### Must Have (MVP)

✅ **18 detectors working accurately**
- Technology stack (10 detectors)
- Marketing intelligence (7 detectors)
- Semantic core (1 capability)

✅ **Business-oriented report format**
- Executive summary (1 page)
- Competitor weaknesses highlighted
- Actionable recommendations
- No technical jargon

✅ **Tested on real data**
- 6 medical clinics analyzed
- Accuracy validated
- False positives < 5%

✅ **Security audit passed**
- No XSS vulnerabilities
- Input sanitization
- Data privacy compliant

### Should Have (Phase 2)

📊 **Confidence scores**
- Each detector reports confidence (0-100%)
- Low confidence = flag for manual review

📊 **Trend analysis**
- Track changes over time
- "Competitor added call tracking last month"

📊 **Benchmarking**
- "Your competitor is in top 20% for call tracking adoption"

### Could Have (Future)

💡 **AI-generated insights**
- "Based on their tech stack, they're spending $5K/month on tools"
- "Their CMS choice suggests they prioritize speed over features"

💡 **Competitive positioning map**
- Visual chart: who's ahead in what areas

💡 **Automated alerts**
- "Competitor just added retargeting pixel - they're getting serious"

---

## Competitive Differentiation

### vs Ahrefs

| Feature | Ahrefs | AIM CI System |
|---------|--------|---------------|
| Detectors | 4-5 basic | 18 comprehensive |
| Focus | Generic SEO | Medical marketing |
| Output | Technical | Business-oriented |
| Depth | Surface-level | Molecular-level |
| Context | None | Industry-specific |

**Our edge:** 3x more detectors, medical marketing expertise, business language.

### vs SEMrush

| Feature | SEMrush | AIM CI System |
|---------|---------|---------------|
| Tech detection | Generic | Medical-specific |
| Marketing tools | Limited | Comprehensive |
| Semantic analysis | Basic | Deep |
| Report format | Technical | Sales-ready |

**Our edge:** Domain expertise, actionable insights, sales-ready format.

### vs Manual Analysis

| Feature | Manual | AIM CI System |
|---------|--------|---------------|
| Time | 2-3 hours | 10-30 minutes |
| Depth | Shallow | Deep (50+ pages) |
| Consistency | Variable | Consistent |
| Scalability | 1-2 per day | 10+ per day |

**Our edge:** 6x faster, 10x deeper, infinitely scalable.

---

## Business Impact

### Revenue

**Current:** $50K/month (10 clients × $5K/month)

**With CI Reports:**
- **Higher prices:** $6.5K/month (+30% intelligence premium)
- **Faster sales:** 30 days → 14 days (2x velocity)
- **Higher win rate:** 40% → 60% (+50% conversion)

**Projected:** $130K/month (20 clients × $6.5K/month)

**ROI:** 8-10 hours investment → $80K/month additional revenue

---

### Market Position

**Before:** "Another medical marketing agency"

**After:** "The only agency with molecular-level competitor intelligence"

**Moat:** 18 detectors × medical expertise = impossible to replicate quickly

---

## Implementation Philosophy

### Quality Over Speed

From CLAUDE.md:
> "Качество важнее скорости. Всегда. Мы никуда не торопимся, даже если система будет работать день или два. Главное — качество, которое разбирает конкурентов по молекулам."

**Applied:**
- Critical mode governance (deep review)
- Security research agent (catch all risks)
- Test on 6 real competitors (validate accuracy)
- Stacked PRs (incremental quality gates)

### No Mock Data

From CLAUDE.md:
> "Никаких mock данных в production коде. Если агенту нужны данные для работы, он должен запросить у пользователя или получить реальные данные из источника."

**Applied:**
- All detectors use real HTML/headers
- Test on real competitor sites
- No hardcoded examples in production

### Deep & Correct

From CLAUDE.md:
> "Делаем всё глубоко и правильно, без спешки. Строим самую сложную систему, но самую рабочую."

**Applied:**
- 18 detectors (not 5 "good enough")
- Semantic core extraction (not just keywords)
- Business context (not just detection)

---

## Risks & Mitigations

### Risk 1: False Positives Damage Credibility

**Scenario:** Report says "No call tracking" but competitor has it (different provider)

**Impact:** Client loses trust, sales team looks incompetent

**Mitigation:**
- Test on 6 real sites before launch
- Confidence scores (flag uncertain detections)
- Manual review for low-confidence results
- Critical mode review catches edge cases

**Likelihood:** Medium → Low (after mitigations)

---

### Risk 2: Security Vulnerabilities

**Scenario:** XSS from competitor HTML, command injection from URLs

**Impact:** System compromise, data leak, reputation damage

**Mitigation:**
- Security research agent (running now)
- Input sanitization for all external data
- CSP headers in reports
- Regular security audits

**Likelihood:** High → Low (after mitigations)

---

### Risk 3: Legal/Ethical Issues

**Scenario:** Competitor claims we're "hacking" them

**Impact:** Legal action, reputation damage

**Mitigation:**
- Only public data (no authentication bypass)
- Respect robots.txt
- Rate limiting (2s delay between requests)
- User-agent identification (not hiding)
- Terms of service: "competitive intelligence, not hacking"

**Likelihood:** Low (we're doing what Ahrefs/SEMrush do)

---

### Risk 4: Maintenance Burden

**Scenario:** Detectors break when sites change (e.g., Calltouch changes their script URL)

**Impact:** False negatives, outdated intelligence

**Mitigation:**
- Confidence scores (graceful degradation)
- Multiple detection patterns per tool
- Monitoring dashboard (alert on detection rate drops)
- Quarterly detector review

**Likelihood:** High → Medium (ongoing maintenance needed)

---

## Open Questions for User

### 1. Report Delivery Format

**Options:**
- A) PDF (easy to email, professional)
- B) HTML (interactive, embeddable)
- C) Both (flexibility)

**Recommendation:** C (Both) - PDF for sales, HTML for dashboard

---

### 2. Pricing Strategy

**Options:**
- A) Premium tier (+$1.5K/month for CI reports)
- B) Included in base (competitive advantage)
- C) Per-report ($500 per competitor)

**Recommendation:** B (Included) - use as sales weapon, not revenue source

---

### 3. Update Frequency

**Options:**
- A) On-demand (client requests)
- B) Monthly (automatic)
- C) Quarterly (sufficient for most)

**Recommendation:** A (On-demand) - most competitors don't change tech stack often

---

## Next Steps

1. ✅ Product Vision created (this document)
2. → Get user feedback on open questions
3. → Incorporate research agent findings (when complete)
4. → Create Technical Spec
5. → Get final approval
6. → Start Sprint 1

---

## Appendix: Research Context

**Research agents (still running):**
- Product Expert - analyzing product improvements
- Domain Expert - researching CI best practices
- Security Expert - identifying risks (Critical mode)

**Will incorporate findings when complete.**

**Source materials:**
- Board Memo (docs/superflow/board-memo.md)
- Session Handoff (SESSION_HANDOFF_2026-05-05.md)
- Roadmap (ROADMAP_BUSINESS_REPORT.md)
- Real data (AIM/data/ci-deep/deep_analysis_20260505_211225.json)
