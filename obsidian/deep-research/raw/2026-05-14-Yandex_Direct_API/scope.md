# Research Scope: Yandex Direct API v5 Python Client

**Date:** 2026-05-14  
**Mode:** Deep (8 phases)  
**Estimated Duration:** 10-20 minutes

## Core Research Question

How to build a production-ready Yandex Direct API v5 Python client with unified interface matching Google Ads Client, including resilience patterns, medical advertising compliance, and comprehensive campaign management?

## Stakeholder Perspectives

1. **Developer (Primary):** Needs clear API architecture, authentication flow, error handling patterns, code examples
2. **Medical Marketer:** Requires compliance understanding, moderation rules, restricted keywords
3. **DevOps Engineer:** Needs rate limit handling, monitoring, deployment considerations
4. **Business Analyst:** Wants cost analysis, API pricing, usage limits

## Scope Boundaries

### IN SCOPE (Critical - Deep Investigation)

1. **API Architecture & Authentication**
   - REST endpoints structure
   - OAuth 2.0 implementation details
   - Token refresh mechanism
   - Rate limits (10 req/s, 100k units/day)
   - Error codes and handling

2. **Campaign Management**
   - Campaign types (Search, РСЯ, Smart Banners, Master Campaigns)
   - Targeting options (geo, demographics, interests)
   - Budget management (manual, automatic, weekly)
   - Status management (enabled, paused, archived)

3. **Metrics & Reporting**
   - Available metrics (impressions, clicks, CTR, CPC, conversions)
   - Statistics API endpoints
   - Data aggregation periods
   - Report formats

4. **Error Handling & Resilience**
   - Common API errors
   - Retry strategies for rate limits
   - Exponential backoff patterns
   - Circuit breaker implementation

5. **Medical Advertising Compliance**
   - Russian healthcare advertising regulations
   - Required licenses
   - Moderation rules
   - Restricted keywords and phrases

### IN SCOPE (Important - Standard Investigation)

6. **Bid Strategies**
   - Manual bidding
   - Automatic bidding
   - Weekly budget optimization
   - Target CPA/ROAS

7. **Ad Formats**
   - Text-graphic ads
   - Smart banners
   - Dynamic ads
   - Ad extensions (sitelinks, callouts)

8. **Keyword Management**
   - Adding/removing keywords
   - Match types
   - Bid adjustments
   - Negative keywords

9. **Budget Pacing**
   - Even distribution
   - Daily limits
   - Weekly budgets

### OUT OF SCOPE (Optional - Surface Level or Skip)

- Advanced retargeting features
- Lookalike audiences
- Dynamic remarketing
- Deep Yandex Metrica integration (goals, segments, cohorts)
- Wordstat API (keyword research, traffic forecasting)

## Success Criteria

### Technical Completeness
- ✅ Complete API v5 endpoint documentation
- ✅ OAuth 2.0 implementation guide with code
- ✅ Rate limit handling patterns with examples
- ✅ Error handling strategies with retry logic
- ✅ 10+ code examples from production repositories

### Compliance Coverage
- ✅ Medical advertising requirements documented
- ✅ License requirements identified
- ✅ Moderation rules explained
- ✅ Restricted keywords list or guidelines

### Implementation Readiness
- ✅ Unified interface design matching Google Ads Client
- ✅ Resilience patterns (Circuit Breaker, Retry, Rate Limiting)
- ✅ Production-ready code examples
- ✅ Testing strategies

### Source Quality
- ✅ 25+ sources (deep mode threshold)
- ✅ Average credibility >70/100
- ✅ Mix of official docs, GitHub repos, industry articles
- ✅ Recent sources (2024-2026) + foundational older sources

## Key Assumptions to Validate

1. **API Stability:** Yandex Direct API v5 is stable and recommended (vs v4 or v4.5)
2. **Python Support:** Official or community Python SDKs exist and are maintained
3. **OAuth 2.0:** Standard OAuth 2.0 flow works (not proprietary auth)
4. **Rate Limits:** 10 req/s and 100k units/day are current limits
5. **Medical Compliance:** Specific regulations exist for medical advertising in Russia
6. **Unified Interface:** Yandex API structure allows unified interface with Google Ads

## Research Strategy

### Phase 3 (RETRIEVE) - Parallel Search Angles

1. **Official Documentation** (keyword search)
   - "yandex direct api v5 documentation"
   - "yandex direct api authentication oauth"
   - "yandex direct api rate limits"

2. **GitHub Repositories** (code search)
   - "yandex direct api python"
   - "yandex ads mcp"
   - Clone and study: https://github.com/Yurich-ru/yandex-ads-mcp

3. **Technical Implementation** (keyword search)
   - "yandex direct api error handling"
   - "yandex direct api retry logic"
   - "yandex direct api circuit breaker"

4. **Campaign Management** (semantic search)
   - "yandex direct campaign types targeting"
   - "yandex direct smart banners master campaigns"
   - "yandex direct budget management strategies"

5. **Metrics & Reporting** (keyword search)
   - "yandex direct api statistics metrics"
   - "yandex direct api reporting endpoints"
   - "yandex direct conversion tracking"

6. **Medical Compliance** (Russian sources preferred)
   - "яндекс директ медицинская реклама требования"
   - "yandex direct medical advertising compliance russia"
   - "yandex direct healthcare advertising regulations"

7. **Comparison & Best Practices** (semantic search)
   - "yandex direct vs google ads api comparison"
   - "yandex direct api best practices python"
   - "yandex direct api production implementation"

8. **Recent Developments** (date-filtered 2024-2026)
   - "yandex direct api 2025 updates"
   - "yandex direct api 2026 changes"

### Sub-Agent Deployment

- **Agent 1:** Deep dive into yandex-ads-mcp repository (architecture, patterns, code quality)
- **Agent 2:** Official Yandex Direct API documentation analysis (endpoints, parameters, examples)
- **Agent 3:** Medical advertising compliance research (Russian regulations, licenses, restrictions)
- **Agent 4:** Production implementation patterns (error handling, resilience, monitoring)

## Quality Gates

- **Phase 3 completion:** 25+ sources, avg credibility >70/100, OR 10 minutes elapsed
- **Phase 4 verification:** Core claims have 3+ independent sources
- **Phase 6 critique:** Persona-based review (Skeptical Practitioner, Implementation Engineer)
- **Phase 8 delivery:** Complete report >30KB, all citations verified, no placeholders

## Output Deliverables

1. **Markdown Report** (primary source of truth)
2. **sources.jsonl** (source registry with canonical IDs)
3. **evidence.jsonl** (evidence store with quotes and locators)
4. **claims.jsonl** (claim ledger with support status)
5. **run_manifest.json** (query, mode, assumptions, config)
6. **HTML Report** (McKinsey style, auto-opened)
7. **PDF Report** (professional print, auto-opened)

---

**Status:** Scope defined, ready for Phase 2 (PLAN)
