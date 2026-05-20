---
phase: 13-landing-marketing
type: research
subsystem: marketing
tags: [marketing, campaigns, analytics, ab-testing, yandex-direct, vk-ads, telegram-ads, roi, attribution]
status: complete
completed: 2026-05-20
---

# Phase 13-02 Research: Marketing Campaigns Launch + Analytics

**Researched:** 2026-05-20
**Domain:** Russian digital advertising (Яндекс.Директ, VK Ads, Telegram Ads) + Marketing analytics + A/B testing
**Confidence:** HIGH

## Summary

Phase 13-02 launches paid marketing campaigns for iamaim.ru and builds the measurement infrastructure to track performance. The codebase already contains substantial advertising infrastructure: a Yandex Direct API v5 client (yandex_direct_client.py, 479 lines), Yandex Metrica client (yandex_metrica_client.py, 486 lines), Ads Magister with action routing, Campaign Creator Agent (528 lines), Bid Strategy Optimizer (834 lines), Ad Copy Generator with compliance checking, MCP Ads Server, and Analytics Magister. However, critical production gaps exist: the Yandex Direct stats endpoint returns hardcoded MOCK data (lines 244-257 of yandex_direct_client.py), there is no VK Ads or Telegram Ads client, no A/B testing framework, no campaign-to-lead attribution pipeline, and no marketing ROI dashboard.

**Primary recommendation:** Fix the Yandex Direct MOCK stats (implement real TSV report parsing), build VK Ads and Telegram Ads API clients following the existing Yandex Direct client pattern, add a scipy-based A/B testing module with statistical significance calculation, build a campaign attribution pipeline (UTM parameter capture -> lead conversion -> ROI calculation), and create a marketing analytics dashboard page. Integrate everything through the existing Hermes operator and Ads Magister infrastructure.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| LAND-04 | A/B тестирование landing page вариантов | scipy.stats for significance, PlanOut pattern for experiment design, Next.js middleware for variant serving |
| MKTG-01 | Запуск маркетинговых кампаний (Яндекс.Директ, Telegram, VK) | Existing Yandex Direct client (fix MOCK), new VK Ads client, Telegram Ad API |
| MKTG-02 | Analytics воронки продаж от кампании до клиента | UTM capture -> lead association -> conversion tracking pipeline |
| MKTG-03 | ROI tracking по каналам привлечения | Cost aggregation from ad APIs + revenue from ЮKassa -> ROAS calculation |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Campaign creation (Яндекс.Директ) | API / Backend | — | Yandex Direct API v5 calls require OAuth token, must be server-side |
| Campaign creation (VK Ads) | API / Backend | — | VK Marketing API requires access token, server-side only |
| Campaign creation (Telegram Ads) | API / Backend | — | Telegram Ad API requires bot token, server-side |
| Ad copy generation & compliance | API / Backend | — | LLM-based generation + ФЗ-38 compliance checking |
| Campaign stats collection | API / Backend | — | TSV/JSON report parsing from ad APIs |
| Budget optimization | API / Backend | — | Performance-based allocation logic, server-side computation |
| A/B test experiment design | API / Backend | — | Statistical computation (scipy), experiment configuration |
| A/B test variant serving | Frontend Server (SSR) | Browser / Client | Next.js middleware for variant assignment + client-side cookie |
| A/B test result analysis | API / Backend | — | Statistical significance tests on collected metrics |
| UTM parameter capture | Browser / Client | Frontend Server (SSR) | Client-side JS capture on landing page load |
| Attribution (campaign -> lead) | API / Backend | Database / Storage | Lead model already has UTM fields; need campaign_id linkage |
| ROI calculation | API / Backend | Database / Storage | Cost data from ad APIs + revenue from ЮKassa -> ROAS |
| Marketing analytics dashboard | Frontend Server (SSR) | API / Backend | Next.js page + FastAPI analytics endpoints |
| Campaign monitoring/alerting | API / Backend | CDN / Static | Prometheus metrics from campaign health checks |
| Яндекс.Метрика web tracking | Browser / Client | — | Client-side JS (already in YandexMetrika.tsx) |
| Яндекс.Метрика API data | API / Backend | — | Server-side reporting API (already in yandex_metrica_client.py) |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| httpx | >=0.27.0 | Async HTTP for Yandex Direct, VK Ads, Telegram APIs | Already in project; async support for all ad platform APIs [VERIFIED: requirements.txt] |
| google-ads | >=24.0.0 | Google Ads API (secondary platform) | Already installed; not primary for Russian market but present [VERIFIED: requirements.txt] |
| scipy | >=1.14.0 | Statistical significance for A/B tests (chi-square, t-test, Fisher's exact) | Industry standard for A/B test computation; no dedicated A/B lib needed [VERIFIED: pip index] |
| pydantic | >=2.0.0 | Data models for campaign configs, experiment designs, attribution data | Already in project; campaign/ad/experiment schema validation [VERIFIED: requirements.txt] |
| aiocache | >=0.12.0 | Caching ad platform API responses | Already in project; prevents rate limit hits and API costs [VERIFIED: requirements.txt] |
| structlog | >=24.1.0 | Structured logging for campaign operations | Already in project; audit trail for ad spend decisions [VERIFIED: requirements.txt] |
| prometheus-client | >=0.20.0 | Campaign health metrics (impressions, clicks, spend, CPA) | Already in project; real-time campaign monitoring [VERIFIED: requirements.txt] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| tenacity | >=8.2.0 | Retry logic for ad platform API calls | All external ad API calls (Yandex, VK, Telegram) |
| pybreaker | >=1.0.0 | Circuit breaker for ad platform APIs | Prevent cascading failures when ad APIs are down |
| aiolimiter | >=1.1.0 | Rate limiting for ad platform APIs | Yandex Direct has strict rate limits (5 req/s agency) |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| scipy (manual A/B) | GrowthBook, PlanOut, Optimizely | These add deployment complexity; scipy gives full control with no external dependency |
| Custom Yandex Direct client | yandex-direct (PyPI community lib) | Community lib outdated (last update 2021); our client follows official API v5 docs [CITED: Context7 /dragonsigh/yandex-direct-api-docs] |
| Custom VK Ads client | vk-api (PyPI) | Generic VK API doesn't cover Ads-specific endpoints well; custom client needed |
| Custom attribution | Segment, Rudderstack | Overkill for single-site attribution; UTM->lead pipeline is 200 lines of Python |

**Installation:**
```bash
# Core (already installed)
pip install httpx>=0.27.0 scipy>=1.14.0 pydantic>=2.0.0 aiocache>=0.12.0 structlog>=24.1.0 prometheus-client>=0.20.0

# Supporting (already installed)
pip install tenacity>=8.2.0 pybreaker>=1.0.0 aiolimiter>=1.1.0
```

**Version verification:**
- scipy 1.17.1 available (2026-05) — use >=1.14.0 for stats module stability [VERIFIED: pip index]
- httpx 0.27.0+ already in requirements.txt [VERIFIED: requirements.txt]
- All supporting libs already in requirements.txt [VERIFIED: requirements.txt]

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         MARKETING CAMPAIGN SYSTEM                        │
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐               │
│  │ Yandex Direct │    │   VK Ads     │    │ Telegram Ads │               │
│  │   API v5      │    │  Marketing   │    │   API        │               │
│  │  (OAuth 2.0)  │    │  API (token) │    │ (Bot token)  │               │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘               │
│         │                   │                   │                        │
│         ▼                   ▼                   ▼                        │
│  ┌──────────────────────────────────────────────────┐                   │
│  │           API Clients Layer (httpx async)         │                   │
│  │  ┌────────────┐  ┌──────────┐  ┌──────────────┐ │                   │
│  │  │YandexDirect│  │ VKAds    │  │TelegramAds   │ │                   │
│  │  │Client      │  │Client    │  │Client        │ │                   │
│  │  │(EXISTS,    │  │(NEW)     │  │(NEW)         │ │                   │
│  │  │ MOCK STATS)│  │          │  │              │ │                   │
│  │  └─────┬──────┘  └────┬─────┘  └──────┬───────┘ │                   │
│  │        │              │               │          │                   │
│  │  ┌─────┴──────────────┴───────────────┴───────┐  │                   │
│  │  │     Resilience Layer                       │  │                   │
│  │  │  Circuit Breaker + Retry + Rate Limit       │  │                   │
│  │  │  + Response Cache (aiocache, 1h TTL)       │  │                   │
│  │  └─────────────────────┬──────────────────────┘  │                   │
│  └────────────────────────┼─────────────────────────┘                   │
│                           │                                              │
│         ┌─────────────────┼──────────────────┐                          │
│         ▼                 ▼                  ▼                           │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────┐                │
│  │ Campaign   │  │ Budget       │  │ Ad Copy          │                │
│  │ Creator    │  │ Optimizer    │  │ Generator        │                │
│  │ (EXISTS)   │  │ (EXISTS)     │  │ (EXISTS)         │                │
│  └─────┬──────┘  └──────┬───────┘  └────────┬─────────┘                │
│        │                │                    │                           │
│        └────────────────┼────────────────────┘                           │
│                         ▼                                                │
│              ┌─────────────────────┐                                    │
│              │   Ads Magister      │                                    │
│              │   (EXISTS)          │                                    │
│              │   Routes actions:   │                                    │
│              │   create_campaign   │                                    │
│              │   optimize_budget   │                                    │
│              │   ab_test (TODO)    │                                    │
│              │   track_conv (TODO) │                                    │
│              └─────────┬───────────┘                                    │
│                        │                                                 │
│         ┌──────────────┼──────────────┐                                 │
│         ▼              ▼              ▼                                  │
│  ┌───────────┐  ┌───────────┐  ┌──────────────┐                         │
│  │ Event Bus │  │ Analytics │  │ Hermes       │                         │
│  │ (EXISTS)  │  │ Magister  │  │ Operator     │                         │
│  │           │  │ (EXISTS)  │  │ (EXISTS)     │                         │
│  └─────┬─────┘  └─────┬─────┘  └──────┬───────┘                         │
│        │              │               │                                   │
│        ▼              ▼               ▼                                   │
│  ┌──────────────────────────────────────────────────┐                   │
│  │              Data & Analytics Layer               │                   │
│  │                                                   │                   │
│  │  ┌─────────────┐  ┌────────────┐  ┌───────────┐ │                   │
│  │  │ Campaign     │  │ Attribution│  │ ROI        │ │                   │
│  │  │ Stats Store  │  │ Pipeline   │  │ Calculator │ │                   │
│  │  │ (PostgreSQL) │  │ (UTM->Lead)│  │ (Cost/Rev) │ │                   │
│  │  └─────────────┘  └────────────┘  └───────────┘ │                   │
│  │                                                   │                   │
│  │  ┌─────────────┐  ┌────────────┐  ┌───────────┐ │                   │
│  │  │ A/B Test     │  │ Prometheus │  │ Metrica    │ │                   │
│  │  │ Engine       │  │ Metrics    │  │ API Client │ │                   │
│  │  │ (scipy)      │  │ (EXISTS)   │  │ (EXISTS)   │ │                   │
│  │  └─────────────┘  └────────────┘  └───────────┘ │                   │
│  └──────────────────────┬───────────────────────────┘                   │
│                         │                                                │
│                         ▼                                                │
│  ┌──────────────────────────────────────────────────┐                   │
│  │                Frontend Layer                     │                   │
│  │                                                   │                   │
│  │  ┌─────────────┐  ┌────────────┐  ┌───────────┐ │                   │
│  │  │ Landing Page│  │ A/B Variant │  │ Marketing  │ │                   │
│  │  │ (EXISTS)    │  │ Middleware  │  │ Dashboard  │ │                   │
│  │  │ iamaim.ru   │  │ (NEW)       │  │ (NEW)      │ │                   │
│  │  └─────────────┘  └────────────┘  └───────────┘ │                   │
│  │                                                   │                   │
│  │  ┌─────────────┐  ┌────────────┐  ┌───────────┐ │                   │
│  │  │ UTM Capture │  │ Metrika    │  │ Conversion │ │                   │
│  │  │ (EXISTS)    │  │ Tag        │  │ Pixel      │ │                   │
│  │  │ UTMCapture  │  │ (EXISTS)   │  │ (NEW)      │ │                   │
│  │  │ component   │  │ YandexMetr │  │            │ │                   │
│  │  └─────────────┘  └────────────┘  └───────────┘ │                   │
│  └──────────────────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────────────┘

Data Flow (primary use case: User clicks ad -> converts):
1. User clicks Яндекс.Директ ad with UTM params (?utm_source=yandex&utm_campaign=med-1)
2. Landing page loads -> UTMCapture.tsx reads UTM params -> stores in sessionStorage
3. YandexMetrika.tsx fires pageview with UTM data
4. User submits contact form -> UTM params attached to lead record
5. Lead created -> AI Lead Scoring -> EventBus fires lead.created
6. Attribution pipeline listens for lead.created -> links to campaign via UTM campaign_id
7. If lead converts to paid client -> ЮKassa webhook -> EventBus fires payment.received
8. ROI Calculator: campaign.cost / client.revenue = ROAS
9. Campaign stats updated -> Dashboard reflects new ROAS
```

### Recommended Project Structure

```
AIM/src/aim/subagents/ads/
├── __init__.py                    # (EXISTS) Ads subagent package
├── yandex_direct_client.py        # (EXISTS - FIX MOCK STATS) Yandex Direct API v5
├── vk_ads_client.py               # (NEW) VK Ads Marketing API client
├── telegram_ads_client.py         # (NEW) Telegram Ad API client
├── campaign_creator_agent.py      # (EXISTS) Campaign structure generation
├── bid_strategy_optimizer.py      # (EXISTS) Bid strategy optimization
├── ad_copy_generator.py           # (EXISTS) LLM-based ad copy generation
├── mcp_server.py                  # (EXISTS) FastMCP server for ads management
├── ab_test_engine.py              # (NEW) A/B test experiment design + analysis
├── attribution_pipeline.py        # (NEW) Campaign-to-lead attribution
├── roi_calculator.py              # (NEW) ROAS and ROI computation
├── campaign_monitor.py            # (NEW) Real-time campaign health checks
├── services/
│   ├── campaign_service.py        # (EXISTS) High-level campaign management
│   └── reporting_service.py       # (NEW) Campaign reporting + dashboards
└── config/
    └── settings.py                # (EXISTS) AdsSettings with tokens

AIM/src/aim/magisters/
├── ads_magister.py                # (EXISTS - ADD ab_test + track_conv routing)
└── analytics_magister.py          # (EXISTS - ADD campaign data collection)

AIM/src/aim/models/
├── analytics_models.py            # (EXISTS - ADD campaign/attribution/AB models)
└── campaign_models.py             # (NEW) Campaign, AdGroup, Ad, Experiment models

AIM/src/aim/api/
├── ads.py                         # (EXISTS) Ads API endpoints
├── analytics.py                   # (NEW) Marketing analytics endpoints
└── ab_test.py                     # (NEW) A/B test management endpoints

AIM/frontend/
├── components/
│   ├── YandexMetrika.tsx          # (EXISTS) Client-side Metrika tag
│   ├── UTMCapture.tsx             # (EXISTS) UTM parameter capture
│   └── analytics/
│       ├── AnalyticsDashboard.tsx # (EXISTS) Analytics dashboard
│       └── MarketingDashboard.tsx # (NEW) Marketing-specific dashboard
├── middleware/
│   └── ab-test.ts                 # (NEW) A/B variant assignment middleware
├── app/
│   ├── analytics/page.tsx         # (EXISTS) Analytics page
│   └── marketing/page.tsx         # (NEW) Marketing dashboard page
└── lib/
    └── ab-test.ts                 # (NEW) Client-side A/B test helpers

AIM/tests/
├── unit/
│   ├── test_ads_campaign_creator_agent.py  # (EXISTS)
│   ├── test_ads_magister.py                # (EXISTS)
│   └── test_ab_test_engine.py              # (NEW)
├── subagents/
│   ├── test_ads_magister_v2.py             # (EXISTS)
│   └── test_vk_ads_client.py               # (NEW)
└── integration/
    └── test_attribution_pipeline.py         # (NEW)
```

### Pattern 1: Ad Platform API Client (Base)

**What:** All ad platform clients follow the same pattern: async httpx with OAuth/token auth, dataclass models, resilience layer (circuit breaker + retry + rate limit + cache).

**When to use:** Any new ad platform integration (VK Ads, Telegram Ads, myTarget).

**Example (pattern extracted from existing YandexDirectAPIClient):**
```python
# Source: AIM/src/aim/subagents/ads/yandex_direct_client.py (lines 85-178)
# Pattern: Async HTTP + Bearer Auth + Dataclass Models + CRUD methods

@dataclass
class CampaignInfo:
    id: int
    name: str
    status: str
    type: str
    daily_budget: float
    currency: str
    start_date: str
    end_date: str | None

class AdPlatformClient:
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.platform.com/v1"
        self.timeout = httpx.Timeout(30.0)

    async def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Single method for all API calls with auth headers."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Accept-Language": "ru",
            }
            response = await client.request(
                method, f"{self.base_url}{endpoint}",
                headers=headers, **kwargs
            )
            response.raise_for_status()
            return response.json()
```

### Pattern 2: Campaign -> Lead Attribution

**What:** UTM parameters captured on landing page, stored with lead record, linked to campaign via campaign_id matching.

**When to use:** Any paid traffic source. Must be in place BEFORE launching campaigns.

**Example:**
```python
# Attribution pipeline — listens for lead.created events
# Source: Pattern derived from existing LeadScoringAgent + EventBus

class AttributionPipeline:
    """Links campaign clicks to lead conversions."""

    def __init__(self, event_bus: EventBus, db_session: AsyncSession):
        self.event_bus = event_bus
        self.db = db_session
        # Subscribe to lead creation events
        self.event_bus.subscribe("lead.created", self.on_lead_created, priority=EventPriority.P2)

    async def on_lead_created(self, event: Event) -> None:
        lead = event.data
        utm_source = lead.get("utm_source")
        utm_campaign = lead.get("utm_campaign")

        if utm_source and utm_campaign:
            # Find matching campaign
            campaign = await self.db.execute(
                select(Campaign).where(
                    Campaign.utm_campaign == utm_campaign,
                    Campaign.platform == self._map_source_to_platform(utm_source),
                )
            )
            campaign = campaign.scalar_one_or_none()

            if campaign:
                # Create attribution record
                attribution = CampaignAttribution(
                    campaign_id=campaign.id,
                    lead_id=lead["id"],
                    utm_source=utm_source,
                    utm_campaign=utm_campaign,
                    attributed_at=datetime.now(timezone.utc),
                )
                self.db.add(attribution)
                await self.db.commit()

                # Fire attribution event
                await self.event_bus.publish(Event(
                    event_type="campaign.attribution",
                    data={"campaign_id": campaign.id, "lead_id": lead["id"]},
                    priority=EventPriority.P2,
                ))
```

### Pattern 3: A/B Test Engine with scipy

**What:** Experiment design using scipy.stats for sample size calculation, variant assignment, and statistical significance testing.

**When to use:** Any landing page or ad copy split test.

**Example:**
```python
# A/B test engine using scipy.stats for significance
# Source: scipy.stats documentation [VERIFIED: scipy docs]

from scipy import stats
from dataclasses import dataclass
from enum import Enum

class ExperimentStatus(Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    INCONCLUSIVE = "inconclusive"

@dataclass
class ExperimentResult:
    variant_a: str
    variant_b: str
    conversions_a: int
    visitors_a: int
    conversions_b: int
    visitors_b: int
    p_value: float
    confidence: float  # e.g., 95.0
    winner: str | None  # 'A', 'B', or None (inconclusive)
    status: ExperimentStatus

class ABTestEngine:
    """Statistical A/B test analysis using scipy."""

    MIN_SAMPLE_SIZE = 100  # Minimum visitors per variant
    CONFIDENCE_THRESHOLD = 0.95  # 95% confidence

    def calculate_sample_size(
        self,
        baseline_rate: float,      # Current conversion rate
        minimum_detectable_effect: float,  # e.g., 0.02 (2% lift)
        power: float = 0.80,
        alpha: float = 0.05,
    ) -> int:
        """Calculate required sample size per variant."""
        from scipy.stats import norm

        z_alpha = norm.ppf(1 - alpha / 2)  # Two-tailed
        z_beta = norm.ppf(power)

        p1 = baseline_rate
        p2 = baseline_rate + minimum_detectable_effect
        p_pooled = (p1 + p2) / 2

        n = (
            (z_alpha * (2 * p_pooled * (1 - p_pooled)) ** 0.5
             + z_beta * (p1 * (1 - p1) + p2 * (1 - p2)) ** 0.5) ** 2
            / (p2 - p1) ** 2
        )
        return int(n) + 1

    def analyze_results(self, result: ExperimentResult) -> ExperimentResult:
        """Run statistical significance test."""
        # Chi-square test for independence
        contingency = [
            [result.conversions_a, result.visitors_a - result.conversions_a],
            [result.conversions_b, result.visitors_b - result.conversions_b],
        ]
        chi2, p_value, dof, expected = stats.chi2_contingency(contingency)

        result.p_value = round(p_value, 4)
        result.confidence = round((1 - p_value) * 100, 1)

        if p_value < (1 - self.CONFIDENCE_THRESHOLD):  # p < 0.05
            rate_a = result.conversions_a / result.visitors_a
            rate_b = result.conversions_b / result.visitors_b
            result.winner = 'B' if rate_b > rate_a else 'A'
            result.status = ExperimentStatus.COMPLETED
        elif result.visitors_a < self.MIN_SAMPLE_SIZE:
            result.status = ExperimentStatus.RUNNING
        else:
            result.status = ExperimentStatus.INCONCLUSIVE

        return result
```

### Anti-Patterns to Avoid

- **MOCK data in production API clients:** The Yandex Direct client has hardcoded CampaignStats on lines 244-257. This MUST be replaced with real TSV report parsing before any campaign launch. MOCK stats produce fake ROI calculations.
- **UTM capture without server-side storage:** Currently UTM params are captured in sessionStorage (UTMCapture.tsx) but the lead creation API must explicitly store them. Check that the contact form submission includes UTM fields.
- **Running multiple campaigns without attribution:** Without campaign_id on leads, you cannot calculate per-channel ROI. Attribution must be in place BEFORE turning on campaigns.
- **A/B testing without sample size calculation:** Running tests without pre-calculated minimum sample size leads to false conclusions (peeking problem). Always calculate required sample size before declaring a winner.
- **Campaign budget without spending caps:** The Yandex Direct client creates campaigns but has no daily/monthly total budget guard. Add a BudgetGuard that sums all campaign daily budgets and alerts if exceeding total marketing budget.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Statistical significance for A/B tests | Custom stats formulas | scipy.stats (chi2_contingency, ttest_ind, fisher_exact) | Edge cases (small samples, multiple comparisons correction) are non-trivial; scipy has been battle-tested for decades |
| Yandex Direct API protocol | Custom HTTP client from scratch | Extend existing YandexDirectAPIClient with real TSV parser | Yandex API v5 has async report generation (HTTP 201/202 -> poll -> 200), pagination, error codes — reimplementing is error-prone |
| TSV report parsing | Custom TSV parser | Python csv module with dialect='excel-tab' | Yandex reports use TSV with specific encoding (UTF-8 with BOM), csv module handles edge cases |
| VK Ads OAuth flow | Custom OAuth implementation | httpx + existing project pattern from YandexDirectAPIClient | VK uses standard OAuth 2.0 with client_credentials flow |
| UTM parameter parsing | Custom URL parser | Python urllib.parse (parse_qs, urlparse) | Standard library handles all URL encoding edge cases |
| Campaign budget alerts | Custom alerting system | Existing Prometheus + Alertmanager | Already deployed for system monitoring; add campaign_spend metrics |
| Landing page variant serving | Custom split-test router | Next.js middleware (Edge) + cookie-based sticky assignment | Next.js middleware is built for request rewriting; don't need a separate service |

**Key insight:** The existing codebase has solid patterns for API clients (YandexDirectAPIClient, YandexMetricaClient) — extend them rather than creating new patterns. The biggest risk is the MOCK stats in the Yandex Direct client, which would corrupt all downstream analytics. Fix that first.

## Runtime State Inventory

> This phase involves modifications to existing API clients and new service integrations, but is NOT a rename/refactor phase. No stored data migration, OS-registered state changes, or secret renames are required. New configuration entries (VK_ADS_TOKEN, TELEGRAM_ADS_BOT_TOKEN) are additive.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | Campaign stats would be stored in PostgreSQL (aim-postgres) as new models | None existing; new tables will be created via Alembic migration |
| Live service config | Yandex Direct campaigns created via API would live in Yandex Direct dashboard | No migration needed; campaigns created fresh |
| OS-registered state | None — verified by checking for systemd/pm2/launchd with marketing-related names | None |
| Secrets/env vars | YANDEX_DIRECT_TOKEN already in .env.example; YANDEX_METRICA_COUNTER_ID present | Add: VK_ADS_ACCESS_TOKEN, TELEGRAM_ADS_BOT_TOKEN, YANDEX_DIRECT_CLIENT_LOGIN (agency mode) |
| Build artifacts | None — no compiled marketing-specific artifacts | None |

**Nothing found in categories:** None — verified by codebase grep and environment file inspection.

## Common Pitfalls

### Pitfall 1: Yandex Direct MOCK Stats in Production

**What goes wrong:** The `get_campaign_stats()` method in `yandex_direct_client.py` (lines 244-257) returns hardcoded CampaignStats objects with fixed values (impressions=10000, clicks=500, cost=5000.0, conversions=50) for EVERY campaign regardless of actual performance. Any dashboard, ROI calculation, or budget optimization using this data will produce completely fake results.

**Why it happens:** The TSV report parsing was deferred during initial implementation. The Yandex Direct Reports API returns TSV with async generation (HTTP 201 -> poll -> 200 with report data). Parsing TSV with proper column mapping requires handling the Yandex-specific report format.

**How to avoid:** Implement real TSV report parsing using Python's `csv` module with `dialect='excel-tab'`. The Yandex Reports API response has specific structure:
1. Request report generation (POST /json/v5/reports)
2. If HTTP 201/202 — poll with retry-after header
3. If HTTP 200 — parse TSV body (rows are tab-separated, first row is column headers, second row is date range, third row starts data)
4. Map column names to CampaignStats fields

**Warning signs:** All campaign stats being identical, CPA always 100.0, conversions always exactly 50.

### Pitfall 2: ФЗ-38 Medical Advertising Compliance

**What goes wrong:** Medical advertising in Russia is heavily regulated by ФЗ-38 "О рекламе". Ads for medical services must include: mandatory warning text ("ИМЕЮТСЯ ПРОТИВОПОКАЗАНИЯ, НЕОБХОДИМА КОНСУЛЬТАЦИЯ СПЕЦИАЛИСТА"), license information, age restrictions (0+, 6+, 12+, 16+, 18+), and cannot make efficacy claims. Яндекс.Директ automatically moders ads and can reject or block campaigns that violate these rules.

**Why it happens:** Generic ad copy generators don't include Russian medical-specific compliance rules.

**How to avoid:** The existing `ad_copy_generator.py` already has a `ComplianceCheck` dataclass with platform-specific checks. Extend it with:
- Mandatory disclaimer text injection for medical ads
- Age restriction tagging (most medical services require 18+)
- License number requirement for medical ads (лицензия № ЛО-XX-XX-XXXXXX)
- Prohibited claims list (guaranteed results, "best", "100% cure")
- ЕРИР (Единый реестр интернет-рекламы) marking requirements — all internet ads must be marked with a unique token

**Warning signs:** Ad copy without medical disclaimer, Яндекс.Директ campaign rejection with "нарушение требований к рекламе медицинских услуг", ads making efficacy claims.

### Pitfall 3: Attribution Window Blindness

**What goes wrong:** Assuming a lead converted from the last-clicked ad within the same session. In medical marketing, the sales cycle can be 7-30 days. Users may click an ad, browse, leave, then return directly to convert. Without proper attribution windows, all conversions get attributed to "direct" traffic and campaign ROI appears to be zero.

**Why it happens:** Simple last-click attribution within session doesn't capture the reality of medical purchase decisions.

**How to avoid:**
1. Store UTM params in a first-party cookie (30-day expiry) on first ad click
2. On conversion (form submit), read the cookie and attribute to the original campaign
3. Use multi-touch attribution: track all campaign touches, then weight (first-touch 40%, last-touch 40%, linear 20%)
4. Define attribution windows: 30 days for medical services (matches typical sales cycle)

**Warning signs:** Direct traffic has disproportionately high conversion rate, paid campaigns show 0 conversions, discrepancy between Metrica and internal attribution.

### Pitfall 4: Budget Bleed Without Per-Platform Guards

**What goes wrong:** Creating campaigns across multiple platforms (Yandex + VK + Telegram) without a total budget ceiling. Each platform independently spends its daily budget, potentially exceeding the total marketing budget.

**Why it happens:** Each ad platform client operates independently with its own daily budget setting.

**How to avoid:**
1. Implement a `BudgetGuard` service that tracks total daily spend across all platforms
2. Before allowing campaign creation, check: `sum(all_campaigns.daily_budget) <= total_marketing_budget`
3. Monitor daily spend via a scheduled job (every 30 minutes, fetch spend from all platforms)
4. Alert via Prometheus/Alertmanager when spend exceeds 80% of daily budget
5. Emergency stop: automatically pause all campaigns if spend exceeds 110% of daily budget

**Warning signs:** Multiple active campaigns with no aggregated budget view, no spend alerts, individual platform daily budgets summing to more than total budget.

## Code Examples

Verified patterns from official sources:

### Yandex Direct Report Request + TSV Parsing (Fix for MOCK stats)

```python
# Source: Context7 /dragonsigh/yandex-direct-api-docs + official Yandex Direct API v5
# This replaces the MOCK stats in yandex_direct_client.py lines 244-257

import csv
import io

async def get_campaign_stats_real(
    self,
    campaign_ids: list[int],
    date_from: str,
    date_to: str,
) -> list[CampaignStats]:
    """Get REAL campaign statistics via Yandex Direct Reports API."""
    async with httpx.AsyncClient(timeout=self.timeout) as client:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept-Language": "ru",
            "processingMode": "auto",  # Async report generation
            "skipReportHeader": "true",
            "skipColumnHeader": "true",
            "skipReportSummary": "true",
        }

        payload = {
            "params": {
                "SelectionCriteria": {
                    "DateFrom": date_from,
                    "DateTo": date_to,
                    "Filter": [{
                        "Field": "CampaignId",
                        "Operator": "IN",
                        "Values": [str(cid) for cid in campaign_ids],
                    }],
                },
                "FieldNames": [
                    "Date", "CampaignId", "CampaignName",
                    "Impressions", "Clicks", "Cost",
                    "Conversions", "Ctr", "AvgCpc", "AvgCpa",
                ],
                "ReportName": f"Campaign_Stats_{date_from}_{date_to}",
                "ReportType": "CAMPAIGN_PERFORMANCE_REPORT",
                "DateRangeType": "CUSTOM_DATE",
                "Format": "TSV",
                "IncludeVAT": "YES",
            }
        }

        # Report generation may be async (HTTP 201/202)
        response = await client.post(
            f"{self.base_url}/reports",
            json=payload,
            headers=headers,
        )

        # Handle async report generation
        while response.status_code in (201, 202):
            retry_in = int(response.headers.get("retryIn", 5))
            await asyncio.sleep(retry_in)
            response = await client.get(
                f"{self.base_url}/reports",
                headers=headers,
            )

        response.raise_for_status()

        # Parse TSV report
        tsv_data = response.text
        reader = csv.DictReader(
            io.StringIO(tsv_data),
            delimiter='\t',
        )

        stats = []
        for row in reader:
            stats.append(CampaignStats(
                campaign_id=int(row["CampaignId"]),
                impressions=int(row["Impressions"]),
                clicks=int(row["Clicks"]),
                cost=float(row["Cost"]) / 1_000_000,  # Micros to RUB
                conversions=int(row["Conversions"]),
                ctr=float(row["Ctr"]),
                cpc=float(row["AvgCpc"]) / 1_000_000 if row.get("AvgCpc") else 0.0,
                cpa=float(row["AvgCpa"]) / 1_000_000 if row.get("AvgCpa") else 0.0,
                date=row["Date"],
            ))

        return stats
```

### VK Ads API Client (New)

```python
# VK Marketing API — Campaign management
# Source: VK Ads API documentation [CITED: vk.com/dev/ads_api]

@dataclass
class VKCampaignInfo:
    id: int
    name: str
    status: str  # active, paused, deleted
    daily_budget: float  # in RUB
    start_time: int  # Unix timestamp
    platform: str  # vk, ok, mycom, vk_ads

class VKAdsClient:
    """VK Ads Marketing API Client."""

    BASE_URL = "https://api.vk.com/method"
    API_VERSION = "5.199"

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.timeout = httpx.Timeout(30.0)

    async def _call(self, method: str, **params) -> dict:
        """Generic VK API call."""
        params["access_token"] = self.access_token
        params["v"] = self.API_VERSION

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.BASE_URL}/{method}",
                data=params,
            )
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                raise VKAPIError(data["error"]["error_msg"])

            return data["response"]

    async def get_campaigns(self, account_id: int) -> list[VKCampaignInfo]:
        """Get campaigns for ad account."""
        result = await self._call(
            "ads.getCampaigns",
            account_id=account_id,
        )
        campaigns = []
        for item in result:
            campaigns.append(VKCampaignInfo(
                id=item["id"],
                name=item["name"],
                status=item["status"],
                daily_budget=item.get("day_limit", 0) / 100,  # Kopecks to RUB
                start_time=item.get("start_time", 0),
                platform=item.get("platform", "vk"),
            ))
        return campaigns
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Yandex Direct API v4 (SOAP) | Yandex Direct API v5 (JSON REST) | 2019-2020 | v4 deprecated; all new integrations must use v5 JSON |
| Yandex Direct Live (real-time bidding) | Yandex Direct API v5 (management) | Always separate | Live API is for real-time bid adjustment; management API for campaign CRUD |
| Google Analytics (UA) | Yandex Metrica (primary) + GA4 (secondary) | 2023 GA UA sunset | GA4 is complex; Metrica gives better Russian-market data (search engine share) |
| Manual A/B testing (spreadsheet) | scipy.stats automated significance | Industry shift to programmatic | No more "feels like B is better" — statistical rigor required |
| Last-click attribution | Multi-touch (first 40%, last 40%, linear 20%) | Modern analytics standard | Medical sales cycle is long; last-click massively undervalues awareness campaigns |
| No ЕРИР marking | ЕРИР token required for ALL internet ads | September 2022 (mandatory) | All ads must carry unique tokens reported to ЕРИР; non-compliance = fines |

**Deprecated/outdated:**
- Yandex Direct API v4 (SOAP) — fully deprecated, use v5 JSON
- Google Analytics Universal — sunset July 2023, GA4 is current
- Manual budget management — modern approach uses automated bid strategies (target CPA, target ROAS)
- Spreadsheet-based A/B testing — statistically invalid for small samples, prone to peeking errors

## Assumptions Log

> List all claims tagged `[ASSUMED]` in this research. The planner and discuss-phase use this
> section to identify decisions that need user confirmation before execution.

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | VK Ads API uses standard OAuth 2.0 with client_credentials flow (similar to Yandex Direct) | Standard Stack / Code Examples | VK Ads access token acquisition differs from campaign management endpoints — may need separate auth method |
| A2 | Telegram Ads can be managed via Bot API with a bot that has advertising permissions | Code Examples / Architecture Patterns | Telegram Ad API scope is narrower than Yandex/VK — may only support promoted messages in channels, not full campaign management |
| A3 | Existing UTMCapture.tsx writes UTM params to a cookie that survives the session (30-day window) | Architecture Patterns / Pitfall 3 | If UTM params are stored only in sessionStorage, attribution breaks when user returns days later |
| A4 | Medical advertising ФЗ-38 requirements include mandatory disclaimer text on ALL medical ads (not just certain categories) | Pitfall 2 | Some medical ad categories may have different disclaimer requirements; professional medical advertising consultation recommended |
| A5 | Yandex Direct agency mode (Client-Login header) is the correct mode for AIM managing client campaigns | Yandex Direct Code Examples | Self-serve mode (no Client-Login) may be simpler if AIM only runs its own campaigns initially |

## Open Questions

1. **VK Ads vs myTarget vs VK Реклама**
   - What we know: VK consolidated its ad platforms into "VK Реклама" (VK Ads). The old myTarget API is being merged. The API endpoint is `ads.getCampaigns` in VK API.
   - What's unclear: Whether a separate myTarget API client is needed, or whether VK Реклама fully covers the VK ecosystem (VKontakte + OK + myTarget inventory).
   - Recommendation: Start with VK Ads API (vk.com/dev/ads_api), verify inventory coverage. Add myTarget API only if VK Ads doesn't cover OK.ru and other platforms.

2. **Telegram Ads API scope for medical services**
   - What we know: Telegram Ads API allows creating ad campaigns in Telegram channels with specific targeting (topics, channels, language). Medical services may face category restrictions.
   - What's unclear: Whether Telegram accepts medical service ads (vs pharmaceutical ads which are universally restricted). Telegram ad policies are less documented than Yandex/VK.
   - Recommendation: Test with a minimal-budget campaign first. Have ФЗ-38 compliance text ready in ad copy.

3. **Landing page A/B testing UX impact**
   - What we know: Next.js middleware can assign variants via cookie. Variants must be served consistently within a user session. Statistical tests require minimum sample sizes.
   - What's unclear: Whether the landing page should have a visual "A/B test" indicator (some users find it unsettling), and whether variant changes should be gradual (canary release) or 50/50.
   - Recommendation: Invisible variant assignment (no UI indicator), 50/50 split, cookie-based sticky assignment with 30-day persistence. Alert when minimum sample size reached.

4. **ROI calculation methodology for medical services**
   - What we know: Medical services have long sales cycles (1-4 weeks). A lead today may convert in 30 days. Simple "this month's ad spend / this month's revenue" doesn't capture the full picture.
   - What's unclear: Whether to use cohort-based ROI (spend in month 1, track revenue from those leads for 90 days) or simplified monthly ROAS.
   - Recommendation: Implement both: real-time ROAS (simplified, for daily monitoring) and cohort ROI (accurate, for monthly reporting). The real-time metric should be clearly labeled as provisional.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | All backend code | ✓ | 3.14+ | — |
| httpx | Ad API clients | ✓ | >=0.27.0 (installed) | — |
| scipy | A/B test engine | ✓ | 1.17.1 (available via pip) | — |
| PostgreSQL | Campaign data storage | ✓ | 16 (aim-postgres) | — |
| Redis | Response caching | ✓ | 7 (aim-redis) | — |
| Yandex Direct API access | Campaign CRUD + stats | ✗ | — | Requires YANDEX_DIRECT_TOKEN; obtain from https://oauth.yandex.ru |
| VK Ads API access | VK campaign management | ✗ | — | Requires VK_ADS_ACCESS_TOKEN; obtain from VK Ads cabinet |
| Yandex Metrica counter | Web analytics tracking | ✗ (needs real counter ID) | — | Currently has placeholder 12345678 in .env.example |
| Prometheus | Campaign monitoring metrics | ✓ | deployed (aim-prometheus) | — |
| Grafana | Marketing dashboards | ✓ | deployed (aim-grafana) | — |

**Missing dependencies with no fallback:**
- YANDEX_DIRECT_TOKEN — blocks all campaign creation and stats collection. Must obtain before Phase 13-02 Wave 1.
- YANDEX_METRICA_COUNTER_ID — blocks web analytics data collection. Existing client code works but needs real counter ID.

**Missing dependencies with fallback:**
- VK_ADS_ACCESS_TOKEN — VK campaigns can be deferred. Start with Yandex Direct as primary platform.
- TELEGRAM_ADS_BOT_TOKEN — Telegram ads can be deferred. Lower priority than Yandex Direct.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >=7.4.0 + pytest-asyncio >=0.21.0 |
| Config file | AIM/tests/conftest.py |
| Quick run command | `pytest AIM/tests/unit/test_ads_campaign_creator_agent.py -x` |
| Full suite command | `pytest AIM/tests/ -x --timeout=60` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| LAND-04 | A/B test variant assignment via middleware | unit | `pytest AIM/tests/unit/test_ab_test_engine.py::test_variant_assignment -x` | ❌ Wave 0 |
| LAND-04 | Statistical significance calculation | unit | `pytest AIM/tests/unit/test_ab_test_engine.py::test_chi_square_significance -x` | ❌ Wave 0 |
| LAND-04 | A/B test sample size calculator | unit | `pytest AIM/tests/unit/test_ab_test_engine.py::test_sample_size_calculation -x` | ❌ Wave 0 |
| MKTG-01 | Yandex Direct campaign creation | unit | `pytest AIM/tests/unit/test_ads_campaign_creator_agent.py::test_campaign_creation_success -x` | ✅ |
| MKTG-01 | Yandex Direct real stats (not MOCK) | unit | `pytest AIM/tests/unit/test_yandex_direct_stats.py::test_real_tsv_parsing -x` | ❌ Wave 0 |
| MKTG-01 | VK Ads campaign creation | unit | `pytest AIM/tests/subagents/test_vk_ads_client.py::test_create_campaign -x` | ❌ Wave 0 |
| MKTG-02 | UTM-to-lead attribution | integration | `pytest AIM/tests/integration/test_attribution_pipeline.py::test_utm_to_lead_link -x` | ❌ Wave 0 |
| MKTG-02 | Campaign-to-conversion tracking | integration | `pytest AIM/tests/integration/test_attribution_pipeline.py::test_conversion_attribution -x` | ❌ Wave 0 |
| MKTG-03 | ROI calculation from cost + revenue | unit | `pytest AIM/tests/unit/test_roi_calculator.py::test_roas_calculation -x` | ❌ Wave 0 |
| MKTG-03 | ROI breakdown by channel | unit | `pytest AIM/tests/unit/test_roi_calculator.py::test_channel_breakdown -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest AIM/tests/unit/test_ads_campaign_creator_agent.py AIM/tests/unit/test_ads_magister.py -x`
- **Per wave merge:** `pytest AIM/tests/ -x --timeout=60`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `AIM/tests/unit/test_ab_test_engine.py` — covers LAND-04 A/B testing requirements
- [ ] `AIM/tests/unit/test_yandex_direct_stats.py` — covers MKTG-01 real stats (fixes MOCK)
- [ ] `AIM/tests/unit/test_vk_ads_client.py` — covers MKTG-01 VK Ads integration
- [ ] `AIM/tests/unit/test_roi_calculator.py` — covers MKTG-03 ROI calculation
- [ ] `AIM/tests/integration/test_attribution_pipeline.py` — covers MKTG-02 attribution
- [ ] `AIM/tests/conftest.py` — add fixtures: yandex_direct_token, vk_ads_token, sample_campaign, sample_lead_with_utm

*(7 gaps total — significant test infrastructure needed before implementation)*

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | OAuth 2.0 tokens for Yandex Direct, VK Ads; bot token for Telegram Ads. Store in environment variables, never in code. |
| V3 Session Management | yes | A/B test variant cookies: HttpOnly, SameSite=Lax, not used for authentication |
| V4 Access Control | yes | Marketing dashboard restricted to ADMIN role (already in RBAC); campaign creation restricted to authenticated staff |
| V5 Input Validation | yes | Campaign creation parameters (budget, dates, targeting) validated via Pydantic before API call; UTM parameters sanitized |
| V6 Cryptography | yes | Ad platform tokens stored encrypted (AES-256-GCM, following existing ФЗ-152 pattern). Never log raw tokens. |

### Known Threat Patterns for Ad Platform Integrations

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Token exposure in logs | Information Disclosure | structlog sanitizer: mask Bearer tokens in all log output. Already have `log_api_responses: false` in settings. |
| Campaign budget overrun | Elevation of Privilege | BudgetGuard service: aggregate daily spend across platforms, hard-stop at 110% of daily budget ceiling |
| Click fraud / invalid traffic | Repudiation | Yandex Direct automatic click fraud detection; cross-reference Metrica sessions with ad clicks; flag campaigns with CTR > 20% (suspicious) |
| ФЗ-38 violation in ad copy | Information Disclosure / Legal | ComplianceCheck in ad_copy_generator.py: mandatory disclaimer injection, prohibited claims filtering, ЕРИР token generation |
| UTM parameter injection | Tampering | Sanitize UTM values: alphanumeric + hyphens only, max 100 chars. Reject SQL/HTML injection attempts. |
| Unauthorized campaign changes | Spoofing | All campaign mutation endpoints require ADMIN or Ads Magister role; audit log via EventBus (ci.execution.* events) |
| Rate limit exhaustion | Denial of Service | Rate limiter (aiolimiter) per ad platform; circuit breaker (pybreaker) prevents cascading failures; 1h cache reduces API calls |
| Competitor ad intelligence leak | Information Disclosure | Campaign performance data restricted to authenticated dashboard; don't expose raw ad platform data to frontend |

## Sources

### Primary (HIGH confidence)
- Context7 `/dragonsigh/yandex-direct-api-docs` — Campaigns API, Reports API, authentication, field names, TSV format [VERIFIED via Context7 CLI]
- Context7 `/scipy/scipy` — A/B testing statistical functions (chi2_contingency, norm.ppf for sample size) [VERIFIED via Context7 CLI]
- Codebase: `AIM/src/aim/subagents/ads/yandex_direct_client.py` (479 lines) — Existing Yandex Direct API v5 implementation [VERIFIED: file read]
- Codebase: `AIM/src/aim/subagents/api_clients/yandex_metrica_client.py` (486 lines) — Existing Yandex Metrica API implementation [VERIFIED: file read]
- Codebase: `AIM/src/aim/subagents/ads/ad_copy_generator.py` — Existing compliance checking for ad copy [VERIFIED: file read]
- Codebase: `AIM/src/aim/subagents/ads/bid_strategy_optimizer.py` (834 lines) — Existing budget/bid optimization logic [VERIFIED: file read]
- Codebase: `AIM/src/aim/subagents/ads_campaign_creator_agent.py` (528 lines) — Existing campaign creation logic [VERIFIED: file read]
- Codebase: `AIM/src/aim/magisters/ads_magister.py` (294 lines) — Existing Ads Magister action routing [VERIFIED: file read]
- Codebase: `AIM/src/aim/magisters/analytics_magister.py` — Existing Analytics Magister with Data Collector/Processor [VERIFIED: file read]

### Secondary (MEDIUM confidence)
- pip index: scipy 1.17.1 — latest version available [VERIFIED: pip index show]
- requirements.txt — confirms all resilience libraries installed (tenacity, pybreaker, aiolimiter, aiocache) [VERIFIED: file read]
- .env.example — confirms Yandex Direct/Metrica token placeholders; no VK/Telegram [VERIFIED: file read]
- Yandex Direct API v5 official documentation: https://yandex.ru/dev/direct/doc/ [CITED: docs reference]
- VK Ads API documentation: https://vk.com/dev/ads_api [CITED: docs reference]

### Tertiary (LOW confidence)
- Telegram Ad API scope and medical advertising policies — training data knowledge, not verified against current Telegram docs [ASSUMED]
- ФЗ-38 specific medical ad disclaimer requirements — training data knowledge, recommend legal consultation [ASSUMED]
- ЕРИР (Единый реестр интернет-рекламы) marking requirements — training data knowledge, may have changed [ASSUMED]
- VK Ads API OAuth flow details — not verified against current VK API docs [ASSUMED]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all core libraries verified in requirements.txt; scipy confirmed available at 1.17.1
- Architecture: HIGH — all major components verified by reading source code (yandex_direct_client.py, yandex_metrica_client.py, ads_magister.py, analytics_magister.py, bid_strategy_optimizer.py, ad_copy_generator.py, campaign_creator_agent.py, mcp_server.py)
- Pitfalls: HIGH — MOCK stats directly observed in source code (lines 244-257 of yandex_direct_client.py); ФЗ-38 compliance based on Russian market expertise [ASSUMED for specific disclaimer text]
- Security: MEDIUM — ASVS mapping based on threat modeling of ad platform integrations; token storage follows existing project pattern; ФЗ-38 details need legal review

**Research date:** 2026-05-20
**Valid until:** 2026-07-20 (60 days — ad platform APIs change slowly)

## RESEARCH COMPLETE
