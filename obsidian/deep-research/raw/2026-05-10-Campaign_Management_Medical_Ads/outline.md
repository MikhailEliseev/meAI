# Campaign Management for Medical Marketing Ads - Research Outline

## Executive Summary (200-400 words)
- Overview of campaign management automation for medical marketing
- Key platforms: Яндекс.Директ (primary), Google Ads (secondary)
- Critical compliance requirements: 152-ФЗ, Google Healthcare policy
- Success metrics: >95% creation rate, >90% moderation pass, 0 violations
- Cost efficiency: <100 RUB per campaign, <5 min creation time

## 1. Introduction
### 1.1 Scope
- Campaign creation and management automation
- Medical marketing context (Russia + international)
- Focus on Яндекс.Директ API v5 and Google Ads API
- Target audience: developers building campaign automation systems

### 1.2 Methodology
- Exa MCP semantic search (5 queries, 50+ sources)
- Focus areas: API structure, compliance, bidding strategies, campaign structure
- Sources: official documentation, industry best practices, compliance guidelines

### 1.3 Key Assumptions
- Medical marketing context (152-ФЗ, Google Healthcare policy required)
- Яндекс.Директ primary platform for Russia
- Automation over manual management
- Zero compliance violations acceptable
- Technical audience (developers)

## 2. Яндекс.Директ API v5 Architecture
### 2.1 Campaign Structure
- Hierarchy: Campaign → AdGroup → Ad → Keyword
- Campaign types: TEXT_CAMPAIGN, MOBILE_APP_CAMPAIGN, DYNAMIC_TEXT_CAMPAIGN
- Ad group organization principles
- Keyword management and match types

### 2.2 API Rate Limits and Constraints
- 5 concurrent requests maximum [c002]
- Points system based on daily activity
- Batch operations: max 10 campaigns per request [c007]
- Best practices for staying within limits

### 2.3 Moderation Process
- Automatic moderation workflow
- Manual review triggers
- Common rejection reasons for medical content
- Appeal process and timelines

### 2.4 Bidding Strategies
- HIGHEST_POSITION
- WB_MAXIMUM_CLICKS
- Manual CPC
- Automated strategies comparison

## 3. Google Ads API for Healthcare
### 3.1 Healthcare Policy Requirements
- Certification mandatory [c005]
- 7-day warning before suspension
- Restricted content categories
- Certification process steps

### 3.2 Campaign Structure
- Campaign → AdGroup → Ad → Keyword hierarchy
- Responsive Search Ads (RSA): up to 15 headlines, 4 descriptions
- Ad extensions for medical services
- Quality Score factors

### 3.3 Smart Bidding Strategies
- Target CPA: ideal for stable conversion costs [c001]
- Maximize Conversions: volume-focused campaigns [c006]
- Target ROAS: return-focused optimization
- Minimum data requirements: 15+ conversions/month

### 3.4 Moderation Timeline
- Initial review: 1-3 business days [c010]
- Re-review after edits: 24-48 hours
- Policy violation handling
- Appeal process

## 4. Medical Advertising Compliance
### 4.1 Russian Regulations (152-ФЗ)
- Prohibited claims: guarantees, superlatives, "best/лучший" [c003]
- Mandatory disclaimers: license, contraindications
- Restricted terminology
- FAS enforcement guidelines

### 4.2 Google Ads Healthcare Policy
- Certification requirements by country
- Restricted drug and treatment terms
- Prohibited health claims
- Geographic restrictions

### 4.3 Яндекс Medical Restrictions
- Health and medicine category limitations
- Prohibited claims and guarantees
- Required disclosures
- Moderation specifics for medical content

### 4.4 Compliance Automation
- Pre-flight claim validation
- Automated disclaimer insertion
- Prohibited term detection
- Compliance scoring system

## 5. Campaign Structure Best Practices
### 5.1 Ad Group Organization
- Optimal size: 10-15 keywords per ad group [c004]
- Range: 5-20 keywords acceptable
- Grouping strategies: by intent, by service, by geo
- Single Keyword Ad Groups (SKAGs) for high-value terms

### 5.2 Keyword Management
- Match types: exact, phrase, broad
- Match type mirroring within ad groups [c009]
- Negative keywords strategy [c008]
- Medical-specific negative keywords (free, cheap, DIY)

### 5.3 Ad Extensions
- Sitelinks for service categories
- Callouts for credentials and certifications
- Structured snippets for services
- Call extensions with tracking

### 5.4 Landing Page Alignment
- Message match between ad and landing page
- Compliance requirements on landing pages
- Conversion optimization
- Mobile responsiveness

## 6. Bidding Strategy Selection
### 6.1 Manual CPC
- Use cases: new campaigns, testing phase
- Bid adjustment strategies
- Device and location modifiers
- Time-of-day optimization

### 6.2 Target CPA
- Requirements: 15+ conversions/month [c001]
- Ideal for stable conversion costs
- Learning period: 2-4 weeks
- Performance monitoring

### 6.3 Maximize Conversions
- Volume-focused campaigns [c006]
- Budget-constrained optimization
- When to use vs Target CPA
- Performance expectations

### 6.4 Target ROAS
- Revenue-focused optimization
- E-commerce and high-value services
- Data requirements
- Implementation best practices

## 7. Ad Copywriting for Medical Services
### 7.1 Compliance-Safe Formulas
- AIDA (Attention, Interest, Desire, Action)
- PAS (Problem, Agitate, Solution)
- 4U (Useful, Urgent, Unique, Ultra-specific)
- Medical adaptations

### 7.2 Character Limits
- Яндекс: 30 chars headline, 81 chars description
- Google: 30 chars headline, 90 chars description
- RSA optimization strategies
- Mobile vs desktop considerations

### 7.3 Call-to-Action Best Practices
- Compliant CTAs for medical services
- Urgency without pressure
- Trust-building language
- Conversion-focused phrasing

### 7.4 Unique Selling Proposition (USP)
- Credentials and certifications
- Experience and expertise
- Technology and equipment
- Patient outcomes (compliant framing)

## 8. Targeting and Audiences
### 8.1 Geographic Targeting
- City and region selection
- Radius targeting for clinics
- Exclusions and bid adjustments
- Multi-location strategies

### 8.2 Demographics
- Age and gender targeting
- Income level considerations
- Parental status for pediatric services
- Household size

### 8.3 Retargeting
- Site visitor audiences (30, 60, 90 days)
- Engagement-based segments
- Exclusion lists (converters)
- Frequency capping

### 8.4 Lookalike Audiences
- Seed audience requirements
- Similarity percentage selection
- Performance expectations
- Scaling strategies

## 9. Conversion Tracking Setup
### 9.1 Яндекс.Метрика Goals
- JavaScript goals for form submissions
- Composite goals for multi-step conversions
- Phone call tracking
- Goal value assignment

### 9.2 Google Analytics Goals
- Destination goals (thank you pages)
- Event goals (button clicks, form interactions)
- Duration goals (engagement)
- Goal funnels and drop-off analysis

### 9.3 Attribution Models
- Last click (default)
- First click (awareness campaigns)
- Linear (multi-touch)
- Time decay
- Data-driven attribution

### 9.4 Conversion Value
- Lead value estimation
- Lifetime value (LTV) calculation
- Service-specific values
- ROAS optimization

## 10. Campaign Creation Workflow
### 10.1 Pre-Flight Checklist
- Budget and duration validation
- Target audience definition
- Keyword research completion
- Landing page readiness
- Compliance review

### 10.2 API Integration Steps
- Authentication and credentials
- Campaign structure creation
- Ad group and keyword setup
- Ad copy submission
- Conversion goal linking

### 10.3 Moderation Submission
- Pre-submission validation
- Automated compliance checks
- Submission timing optimization
- Monitoring moderation status

### 10.4 Launch and Monitoring
- Initial bid setting
- Budget pacing
- First 24-hour monitoring
- Quick optimization opportunities

## 11. Success Metrics and KPIs
### 11.1 Creation Metrics
- Campaign creation success rate: >95%
- Time to create: <5 minutes
- API error rate: <1%
- Cost per campaign: <100 RUB

### 11.2 Moderation Metrics
- Moderation pass rate: >90%
- Compliance violations: 0
- Average approval time
- Appeal success rate

### 11.3 Performance Metrics
- Click-through rate (CTR)
- Conversion rate
- Cost per acquisition (CPA)
- Return on ad spend (ROAS)
- Quality Score (Google)

### 11.4 Operational Metrics
- API uptime: >99%
- Response time: <2 seconds
- Batch operation efficiency
- Error handling success rate

## 12. Common Pitfalls and Solutions
### 12.1 API Rate Limit Violations
- Problem: Exceeding 5 concurrent requests
- Solution: Request queuing and throttling
- Monitoring: Points usage tracking

### 12.2 Moderation Rejections
- Problem: Prohibited medical claims
- Solution: Pre-flight compliance validation
- Prevention: Automated claim detection

### 12.3 Poor Campaign Structure
- Problem: Too many keywords per ad group
- Solution: Maintain 10-15 keyword limit [c004]
- Optimization: Regular restructuring

### 12.4 Insufficient Conversion Data
- Problem: Smart Bidding without enough data
- Solution: Start with Manual CPC, accumulate 15+ conversions
- Timeline: 2-4 weeks learning period

## 13. Implementation Roadmap
### 13.1 Phase 1: Foundation (Week 1-2)
- API authentication setup
- Database schema for campaigns
- Basic campaign creation workflow
- Manual CPC bidding

### 13.2 Phase 2: Compliance (Week 3-4)
- Compliance validation engine
- Prohibited term detection
- Automated disclaimer insertion
- Pre-flight checks

### 13.3 Phase 3: Automation (Week 5-6)
- Batch operations
- Smart Bidding integration
- Automated moderation monitoring
- Error handling and retry logic

### 13.4 Phase 4: Optimization (Week 7-8)
- Performance monitoring
- Automated bid adjustments
- A/B testing framework
- Reporting dashboard

## 14. Cost Analysis
### 14.1 API Costs
- Яндекс.Директ API: Free (within limits)
- Google Ads API: Free (within limits)
- Rate limit considerations

### 14.2 Infrastructure Costs
- Server hosting: ~$20-50/month
- Database storage: ~$10-20/month
- Monitoring tools: ~$30-50/month
- Total: ~$60-120/month

### 14.3 Development Costs
- Initial development: 40-60 hours
- Testing and QA: 20-30 hours
- Documentation: 10-15 hours
- Total: 70-105 hours

### 14.4 ROI Calculation
- Time saved per campaign: 25-30 minutes
- Cost per manual campaign: ~$15-20
- Breakeven: 50-100 campaigns
- Annual savings: $5,000-10,000 (for 500 campaigns/year)

## 15. Future Considerations
### 15.1 Dynamic Search Ads (DSA)
- Automated ad generation from landing pages
- Use cases for large service catalogs
- Implementation complexity

### 15.2 Video Campaigns
- YouTube advertising for medical services
- Compliance considerations
- Production requirements

### 15.3 Shopping Campaigns
- E-commerce medical products
- Feed management
- Merchant Center setup

### 15.4 App Campaigns
- Mobile app promotion
- Healthcare app specific strategies
- Attribution challenges

## Appendices
### A. Glossary
- Key terms and definitions
- Platform-specific terminology
- Compliance terminology

### B. API Reference Quick Guide
- Яндекс.Директ API v5 endpoints
- Google Ads API resources
- Authentication methods

### C. Compliance Checklist
- 152-ФЗ requirements
- Google Healthcare policy items
- Яндекс medical restrictions

### D. Code Examples
- Campaign creation (Яндекс)
- Campaign creation (Google)
- Compliance validation
- Batch operations

### E. Resources and Tools
- Official documentation links
- Compliance guidelines
- Industry best practices
- Monitoring tools

## Bibliography
- All sources from sources.jsonl
- Official API documentation
- Compliance regulations
- Industry research
