# Phase 16: Hermes Knowledge Training — Research

**Researched:** 2026-05-19
**Domain:** LLM Agent Knowledge Encoding / Multi-mode AI Persona Engineering
**Confidence:** HIGH

## Summary

Phase 16 is a documentation-and-prompt-engineering phase: create a comprehensive SOUL.md that encodes complete system knowledge into the Hermes AIAgent persona. Unlike typical phases that build new features, this phase produces a single critical artifact — the SOUL.md — that determines how well Hermes understands and operates the entire AIM agency.

The current SOUL.md (333 lines) is solid as a foundation but has significant gaps versus the actual codebase. It describes 4 Magisters with inaccurate subagent lists, mentions 6 tools when 8 exist, and lacks entire knowledge domains (Token Economy, Lead Dossier System, Omni-Channel Follow-up, WOW-Data Strategy details, Agent Orchestration mechanics, Russian legal compliance).

**Primary recommendation:** Rewrite SOUL.md from the codebase ground truth — not by patching the existing version. Map every subagent file to a capability description, document all 8 MCP tools with exact I/O schemas, add the 4 missing knowledge domains, and restructure into a progressive-disclosure format optimized for LLM context windows.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Knowledge encoding (SOUL.md) | Hermes Container | — | SOUL.md is loaded by AIAgent at startup inside the hermes Docker container |
| Mode-based behavior switching | Hermes Container | Next.js Frontend | Mode determined by Next.js (X-Client-Mode header), behavior encoded in SOUL.md |
| Agent orchestration knowledge | Hermes Container | AIM API Backend | Hermes needs to know HOW to orchestrate; actual orchestration happens via HTTP calls |
| MCP tool definitions | Hermes Container | AIM API Backend | Tools registered in Hermes registry; handlers call AIM API endpoints |
| Russian market knowledge | Hermes Container | — | Static knowledge encoded in SOUL.md, used for client communication |
| Client workflow knowledge | Hermes Container | — | Process descriptions in SOUL.md guide Hermes behavior |

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Hermes должен знать архитектуру всех 4 Magisters (SEO, Content, Ads, Analytics) — их субагентов, API clients, и что каждый умеет
- **D-02:** Режимы работы (PRESALE/ACTIVE/ADMIN) — полное описание поведения в каждом
- **D-03:** WOW-Data Strategy — какие данные показывать клиенту, 7 блоков бесплатного аудита
- **D-04:** Принцип «3 числа» — пациенты/срок/цена — как отвечать клиенту
- **D-05:** Token Economy — Tier 0/1/2, когда запускать дорогие анализы
- **D-06:** Lead Dossier System — структура папок, статусы лида
- **D-07:** Omni-Channel Follow-up — сайт → Telegram → Email, догонялки по дням
- **D-08:** Agent Orchestration — как Hermes запускает Magisters через MCP tools
- **D-09:** Российский рынок — ФЗ-152, ЮKassa, Яндекс.Директ/Метрика, российские соцсети
- **D-10:** Все 8 MCP tools (6 AIM + 2 Telegram) с детальным описанием входов/выходов

### Claude's Discretion
- Структура и формат SOUL.md (один файл или несколько skills)
- Уровень детализации по каждому domain
- Приоритетность разделов в SOUL.md

### Deferred Ideas (OUT OF SCOPE)
None — всё в scope фазы.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| D-01 | Magister architecture knowledge | Section: Magister Architecture (Ground Truth) |
| D-02 | PRESALE/ACTIVE/ADMIN modes | Section: Mode Behavior Specification |
| D-03 | WOW-Data Strategy (7 blocks) | Section: WOW-Data Strategy |
| D-04 | "3 numbers" principle | Section: Presale Communication Framework |
| D-05 | Token Economy (Tier 0/1/2) | Section: Token Economy |
| D-06 | Lead Dossier System | Section: Lead Dossier System |
| D-07 | Omni-Channel Follow-up | Section: Omni-Channel Follow-up |
| D-08 | Agent Orchestration via MCP | Section: Agent Orchestration Mechanics |
| D-09 | Russian market specifics | Section: Russian Market Knowledge |
| D-10 | All MCP tools I/O specs | Section: MCP Tools Catalog |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| hermes-agent[mcp,messaging,web,anthropic] | >=0.14.0 | AIAgent framework, tool registry, MCP support | Official Hermes framework — we use it, must document for |
| Python | 3.11 | Runtime | Dockerfile-specified version |
| FastAPI | 0.1.0 (app version) | HTTP wrapper for Hermes | Existing infrastructure |
| OmniRoute (OpenAI-compatible) | custom | LLM API proxy (routes to DeepSeek V4) | Existing infrastructure |
| httpx | latest (in requirements.txt) | HTTP client for tool handlers | Async HTTP calls to AIM API |
| Telethon | latest | Telegram user-client for outgoing messages | D-16, D-19 |
| openai | latest | Direct OmniRoute client (omniroute_direct.py) | Telegram gateway bypass |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| run_agent (AIAgent) | bundled with hermes-agent | Core agent loop, session management, tool invocation | Always — this is what loads SOUL.md |
| tools.registry | bundled with hermes-agent | Internal tool registration (NOT MCP stdio) | Tool registration at startup |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Single SOUL.md | Multiple skill files with progressive loading | Hermes loads SOUL.md at startup as identity; skill files are supplementary knowledge. SOUL.md should be the comprehensive reference; additional skill files (services.md, processes.md, kpi.md) are already loaded as supplementary context by AIAgent |
| Hand-written SOUL.md | Auto-generated from code annotations | Auto-generation would be stale quickly. Manual SOUL.md with codebase audit ensures accuracy |

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        NEXT.JS FRONTEND                         │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐ │
│  │ Web Chat UI  │  │ Admin Panel  │  │ Client Status → Mode  │ │
│  └──────┬───────┘  └──────┬───────┘  │ Determiner           │ │
│         │                 │           └───────────┬───────────┘ │
│         │    X-Client-Mode: PRESALE|ACTIVE|ADMIN  │             │
│         └─────────────────┬───────────────────────┘             │
└───────────────────────────┼─────────────────────────────────────┘
                            │ POST /api/chat + Bearer token
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     HERMES CONTAINER (FastAPI)                   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    AIAgent (run_agent)                     │  │
│  │  ┌────────────┐  ┌──────────────┐  ┌──────────────────┐  │  │
│  │  │ SOUL.md    │  │ Mode Prompt  │  │ Tool Registry    │  │  │
│  │  │ (identity) │  │ (behavior)   │  │ (8 tools)        │  │  │
│  │  └────────────┘  └──────────────┘  └────────┬─────────┘  │  │
│  │  ┌──────────────────────────────────────────┐│           │  │
│  │  │   Skill Files (supplementary context)     ││           │  │
│  │  │   services.md, processes.md, kpi.md       ││           │  │
│  │  └──────────────────────────────────────────┘│           │  │
│  └──────────────────────────────────────────────┼───────────┘  │
│                                                  │              │
│  ┌───────────────────────────────────────────────┼──────────┐  │
│  │              Telegram Gateway                  │          │  │
│  │  ┌──────────────┐  ┌─────────────────────┐    │          │  │
│  │  │ Bot API      │  │ Telethon (user)     │    │          │  │
│  │  │ (polling)    │  │ send_message,       │    │          │  │
│  │  │ receive msg   │  │ search_chats        │    │          │  │
│  │  └──────┬───────┘  └──────────┬──────────┘    │          │  │
│  │         │                     │                │          │  │
│  │         │   omniroute_direct  │                │          │  │
│  │         └──────┬──────────────┘                │          │  │
│  └────────────────┼───────────────────────────────┼──────────┘  │
│                   │                               │              │
│                   ▼                               ▼              │
│  ┌────────────────────────────┐  ┌────────────────────────────┐ │
│  │   OmniRoute (DeepSeek V4)  │  │   AIM Tool HTTP Handlers   │ │
│  │   193.111.152.14:7451      │  │   http://app:8000/api/*   │ │
│  └────────────────────────────┘  └────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AIM BACKEND (FastAPI)                       │
│                                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐      │
│  │ SEO      │ │ Content  │ │ Ads      │ │ Analytics    │      │
│  │ Magister │ │ Magister │ │ Magister │ │ Magister     │      │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘      │
│       │             │            │               │              │
│  ┌────┴─────────────┴────────────┴───────────────┴───────┐     │
│  │                  Subagent Ecosystem                     │     │
│  │  70+ subagents across 10+ packages                     │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐      │
│  │ Lead     │ │ Payment  │ │ Email    │ │ Onboarding   │      │
│  │ Capture  │ │ (ЮKassa) │ │ (SendGrid│ │ (Контур.     │      │
│  │          │ │          │ │ )        │ │ Диадок)      │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

### Recommended Project Structure (SOUL.md in context of Hermes)

```
AIM/hermes/
├── skills/aim/
│   ├── SOUL.md              # PRIMARY ARTIFACT — comprehensive system knowledge
│   ├── services.md          # Service catalog (already comprehensive)
│   ├── processes.md         # Business processes (already comprehensive)
│   └── kpi.md              # KPI framework (already comprehensive)
├── app/
│   ├── main.py             # FastAPI wrapper
│   ├── agent_wrapper.py    # AIAgent session management + mode prompts
│   ├── omniroute_direct.py # Direct LLM client (Telegram path)
│   ├── auth.py             # Bearer token auth
│   ├── telegram_gateway.py # Bot API + Telethon integration
│   └── tools/              # 8 MCP tool handlers
│       ├── run_seo_audit.py
│       ├── run_content_analysis.py
│       ├── run_ads_report.py
│       ├── show_project_status.py
│       ├── collect_contact.py
│       ├── show_all_leads.py
│       └── telegram_tools.py  # search_chats + send_message
```

### Pattern 1: Progressive Disclosure SOUL.md Structure

**What:** Organize SOUL.md so that the most frequently needed knowledge loads first, with progressively deeper detail in subsequent sections. This maximizes effective context window usage.

**When to use:** For any comprehensive LLM persona document.

**Structure recommendation:**
1. **Identity + Mode Switching** (always relevant — top of file)
2. **Tool Catalog** (needed every interaction — immediately after identity)
3. **Presale Workflow + "3 Numbers"** (most common scenario — keep compact)
4. **Active Project Workflow** (second most common)
5. **Admin Workflow** (rare, but complete)
6. **Magister Architecture** (deep knowledge — referenced when tools are called)
7. **Russian Market + Compliance** (referenced when relevant)
8. **Token Economy** (governs when to use expensive tools)
9. **Lead Dossier + Follow-up** (administrative knowledge)
10. **Self-Improvement Rules** (meta-cognition)

**Key insight:** The AIAgent loads the entire SOUL.md into context. Placing the most critical sections first ensures they are "closest" in the attention window.

### Pattern 2: Tool-Centric Knowledge Encoding

**What:** For each MCP tool, encode: (1) what it does, (2) when to use it, (3) what inputs it needs, (4) what outputs to expect, (5) how to interpret results for the client.

**Example:**
```markdown
### tool: run_seo_audit
- **What:** Full SEO audit of a clinic website
- **When:** PRESALE (after getting URL), ACTIVE (client asks about SEO performance), ADMIN (manual audit)
- **Input:** URL (string, required) — website URL to audit
- **Output:** JSON with patients_per_month, time_to_result, cost_per_patient, technical_score, competitor_comparison
- **Client communication:** Extract 3 numbers. Present as "ВАШ РЕЗУЛЬТАТ". Don't explain SEO — explain patients.
- **Cost (Token Economy):** Tier 1 (moderate — 1 API call)
```

### Anti-Patterns to Avoid

- **Vague subagent descriptions:** Current SOUL.md says "Technical SEO Auditor" but no such file exists. Real subagent is `ci_tech.py`, `ci_tech_real.py`, `technical_agent.py`. SOUL.md must reference actual code artifacts.
- **Missing tool specs:** Current SOUL.md lists tool NAMES without input/output schemas. Hermes needs to know exact parameters to use tools correctly.
- **No cost awareness:** Hermes should know which tools are expensive (Tier 2) and avoid using them casually in PRESALE mode.
- **Mode leakage:** Behavior rules for PRESALE bleeding into ACTIVE mode descriptions. Each mode section must be self-contained.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| LLM persona encoding | Custom prompt format | SOUL.md loaded via `load_soul_identity=True` in AIAgent | AIAgent natively loads SOUL.md from HERMES_HOME. Custom loading breaks the toolset integration |
| Mode behavior switching | Prompt concatenation | `ephemeral_system_prompt` via agent_wrapper.get_mode_prompt() | AIAgent supports this natively; mode prompt overlays on top of SOUL identity |
| Tool documentation | Separate API docs | Inline tool specs in SOUL.md using the function schema directly from code | Hermes needs tool knowledge IN its context window; external docs are invisible to the LLM |
| System architecture knowledge | Auto-discovery | Manual audit of AIM/src/aim/subagents/ and AIM/src/aim/magisters/ | LLM can't introspect the codebase at runtime; architecture must be encoded |
| Knowledge freshness | Periodic manual updates | Trigger: after any new Magister/Subagent/tool is added | Knowledge rot is the #1 failure mode |

**Key insight:** SOUL.md is the ONLY source of truth the LLM sees. Every capability not documented here is invisible to Hermes.

## Knowledge Gap Analysis: Current SOUL.md vs Actual Codebase

### Magister Architecture — Gaps

| SOUL.md Claim | Reality (Codebase Ground Truth) | Severity |
|---------------|-------------------------------|----------|
| SEO Magister subagents: Technical SEO Auditor, Keyword Research Agent, Competitor Analyzer, Backlink Analyst, Local SEO Agent, SERP Monitor | Actual: ci_tech.py, ci_tech_real.py, technical_agent.py, ci_backlink.py, ci_rank_tracker.py, keyword_research_agent.py, ci_strategist.py, ci_scout.py, ci_site_crawler.py, ci_orchestrator.py, serp_tracker.py, links_agent.py, onpage_optimizer.py, schema_generator.py, yandex_metrica_client.py, ga4_client.py, topic_clusterer.py, cluster_analyzer.py, traffic_analyzer.py, embeddings_generator.py, web_scraper.py (plus ~15 more CI agents) | HIGH — subagent names don't match real code |
| Content Magister subagents: Medical Copywriter, Medical Editor, Content Planner, Blog Manager, GEO Content Optimizer | Actual: content_writer_agent.py, content_quality_checker.py, content_brief_generator.py, content_calendar_manager.py, content_optimizer.py, ci_factchecker.py, ai_content_detector.py, text_extractor.py, gap_detector.py, serp_overlap_clusterer.py, opportunity_scorer.py, brief_generator.py, architecture_planner.py, eeat_scorer.py | HIGH — real subagents are more detailed and specialized |
| Ads Magister subagents: YandexDirect Manager, VK Ads Manager, Telegram Ads Manager, Budget Optimizer, Creative Generator, A/B Testing Agent | Actual: yandex_direct_client.py, bid_strategy_optimizer.py, ad_copy_generator.py, landing_page_analyzer.py, conversion_tracker.py, campaign_service.py, google_ads_client.py, oauth_flow.py, mcp_server.py | MEDIUM — approximately correct but missing real names |
| Analytics Magister subagents: Data Collector, Data Processor, KPI Tracker, Report Generator, Anomaly Detector, Forecast Engine | Actual: analytics_agent.py, analytics_service.py, report_generator.py, business_report.py, ci_finance.py, prioritization/calculator.py, schemas/results.py | MEDIUM — real names differ |
| Competitive Intel not mentioned at all | Major CI ecosystem exists: ci_auditor.py, ci_orchestrator.py, ci_deep_analyzer.py, ci_ecosystem.py, ci_marketing_strategy.py, ci_offer_generator.py, ci_pricing.py, ci_prioritizer.py, ci_qa_validator.py, ci_reputation.py, ci_research_agent.py, ci_vacancies.py, ci_url_validator.py, competitive_intel/ package | HIGH — entire capability domain is invisible to Hermes |

### MCP Tools — Gaps

| SOUL.md | Reality | Gap |
|---------|---------|-----|
| Lists 6 tools, names only | 8 tools registered: 6 AIM ops + 2 Telegram (search_telegram_chats, send_telegram_message) | Missing 2 Telegram tools |
| No input/output specs | Each tool has full function schema with `parameters` and `required` fields | Must add complete schemas |
| No usage context (when/why) | Tools have mode-specific usage rules | Must add per-mode usage guidance |

### Missing Knowledge Domains

| Domain | In SOUL.md? | Priority |
|--------|------------|----------|
| Token Economy (Tier 0/1/2) | No | HIGH |
| Lead Dossier System | No | HIGH |
| Omni-Channel Follow-up | No | HIGH |
| WOW-Data 7 audit blocks | No (only "3 numbers" mentioned) | HIGH |
| Agent Orchestration mechanics | Partial (mentions commands, not HOW they work) | HIGH |
| Russian legal compliance (ФЗ-152) | No | MEDIUM |
| Контур.Диадок workflow | No (mentioned in processes.md) | MEDIUM |
| ЮKassa payment flow | No (mentioned in processes.md) | MEDIUM |
| Hermes internal architecture | No | LOW |
| Docker deployment context | No | LOW |

## MCP Tools Catalog (Complete Ground Truth)

All tools registered in `AIM/hermes/app/tools/` via `tools.registry.register()`. Toolset name: `"aim-operations"`.

### Tool 1: run_seo_audit
```
Registration: run_seo_audit.py
Backend: POST http://app:8000/api/seo/audit
Mode access: PRESALE, ACTIVE, ADMIN
Token tier: Tier 1 (moderate — 1 API call)

Inputs:
  url: string (REQUIRED) — Website URL to audit, e.g., "https://clinic.ru"

Outputs (JSON):
  patients_per_month: int — estimated monthly patient acquisition
  time_to_result: int — estimated weeks to first results
  cost_per_patient: float — estimated acquisition cost per patient
  technical_score: float — technical health score (0-100)
  competitor_comparison: object — comparison with competitor benchmarks

Use in PRESALE: After getting URL → show "3 numbers" → collect contact
Use in ACTIVE: When client asks about SEO performance
Use in ADMIN: Manual audit trigger
```

### Tool 2: run_content_analysis
```
Registration: run_content_analysis.py
Backend: POST http://app:8000/api/content/analyze
Mode access: ACTIVE, ADMIN
Token tier: Tier 1 (moderate)

Inputs:
  url: string (REQUIRED) — Website URL to analyze
  content_type: string (optional, default="all") — "all" | "blog" | "services" | "landing"

Outputs (JSON):
  quality_score per page type
  medical_accuracy: float (0-100)
  seo_optimization_score: float (0-100)
  readability_score: float
  conversion_effectiveness: float
  recommendations: list[string]

Use in ACTIVE: When client asks about content quality
```

### Tool 3: run_ads_report
```
Registration: run_ads_report.py
Backend: POST http://app:8000/api/ads/report
Mode access: ACTIVE, ADMIN
Token tier: Tier 1 (moderate)

Inputs:
  project_id: string (REQUIRED) — Project ID
  period: string (optional, default="month") — "week" | "month" | "quarter"

Outputs (JSON):
  roas: float — Return on Ad Spend
  cpc: float — Cost per Click
  ctr: float — Click-Through Rate (%)
  conversion_rate: float (%)
  budget_utilization: float (%)
  platform_breakdown: object — per-platform metrics (Yandex, VK, Telegram)

Use in ACTIVE: Weekly/monthly client reports
```

### Tool 4: show_project_status
```
Registration: show_project_status.py
Backend: GET http://app:8000/api/projects/{project_id}/status
Mode access: ACTIVE, ADMIN
Token tier: Tier 0 (cheap — simple GET)

Inputs:
  project_id: string (REQUIRED) — Project ID

Outputs (JSON):
  active_tasks: list
  recent_kpis: object
  sprint_progress: object
  blockers: list
  magister_statuses: object — which Magisters are active and their state

Use in ACTIVE: Any time client asks "how's my project going?"
Use in ADMIN: Agency overview of all projects
```

### Tool 5: collect_contact
```
Registration: collect_contact.py
Backend: POST http://app:8000/api/leads
Mode access: PRESALE (primary), ADMIN
Token tier: Tier 0 (cheap — simple POST)

Inputs:
  contact_type: string (REQUIRED) — "telegram" | "email" | "phone"
  contact_value: string (REQUIRED) — @username | email@domain.com | +7...
  website: string (optional) — client's website URL
  name: string (optional) — client's name
  source: string (optional, default="web_chat") — lead source

Outputs (JSON):
  lead_id: string — unique lead identifier
  status: string — "new"
  dossier_path: string — lead folder path

CRITICAL RULE: Only ask for contact AFTER showing WOW data (3 numbers).
Never ask for contact first — it kills conversion.
Only accept telegram, email, or phone. Reject other types.
```

### Tool 6: show_all_leads
```
Registration: show_all_leads.py
Backend: GET http://app:8000/api/leads?period={period}&status={status}
Mode access: ADMIN ONLY
Token tier: Tier 0 (cheap — simple GET)

Inputs:
  period: string (optional, default="week") — "today" | "week" | "month" | "all"
  status: string (optional, default="all") — "new" | "qualified" | "audited" | "contacted" | "active" | "completed" | "closed" | "all"

Outputs (JSON):
  list of lead objects:
    - lead_id: string
    - name: string
    - website: string
    - contact_type: string
    - contact_value: string
    - status: string
    - created_at: datetime
    - source: string

Use in ADMIN: Daily pipeline check, weekly reports to Mikhail
```

### Tool 7: search_telegram_chats
```
Registration: telegram_tools.py
Backend: Telethon user-client (as Mikhail)
Mode access: ADMIN
Token tier: Tier 1 (Telethon API call)

Inputs:
  query: string (REQUIRED) — search query for chat/channel name
  limit: integer (optional, default=10) — max results

Outputs (JSON):
  list of chat objects:
    - name: string
    - id: int
    - type: string
    - unread_count: int
```

### Tool 8: send_telegram_message
```
Registration: telegram_tools.py
Backend: Telethon user-client (as Mikhail)
Mode access: ADMIN
Token tier: Tier 1 (Telethon API call)

Inputs:
  peer: string (REQUIRED) — @username, phone number, or chat ID
  message: string (REQUIRED) — text to send

Outputs (JSON):
  status: "sent"
  peer: string
```

## Agent Orchestration Mechanics (D-08)

Hermes does NOT directly instantiate Magisters or subagents. The orchestration flow is:

1. **Hermes receives chat message** → AIAgent processes through SOUL.md + mode prompt
2. **AIAgent decides to use a tool** → calls tool function by name
3. **Tool handler makes HTTP request** → POST/GET to `http://app:8000/api/*`
4. **AIM Backend receives request** → routes to appropriate endpoint
5. **Backend endpoint invokes Magister** → Magister coordinates subagents
6. **Result flows back** → Backend → Tool handler → AIAgent → Hermes response

Critical knowledge for Hermes:
- All Magisters live in AIM Backend (app:8000), NOT in Hermes container
- Hermes can only interact via the 8 registered tools
- Hermes cannot choose WHICH subagent to call — it calls tools, and the Backend routes to the correct Magister
- Telethon tools (search_telegram_chats, send_telegram_message) execute directly in Hermes container via Telethon client

## Token Economy (D-05)

Must be added as a new SOUL.md section:

| Tier | Cost | Tools | When to Use | Rule |
|------|------|-------|-------------|------|
| Tier 0 | Free/cheap | show_project_status, collect_contact, show_all_leads | Anytime | Simple GET/POST, no AI processing |
| Tier 1 | Moderate | run_seo_audit, run_content_analysis, run_ads_report, search_telegram_chats, send_telegram_message | After client qualification | 1 API call + AI processing |
| Tier 2 | Expensive | Not exposed as tools (internal Magister operations) | After contract | Full Magister orchestration with multiple subagents |

**Rules:**
- PRESALE: Tier 0 + Tier 1 (run_seo_audit ONLY)
- PRESALE: NEVER use Tier 2 — this requires contract
- ACTIVE: Tier 0 + Tier 1 — all project-related tools
- ADMIN: All tiers unrestricted

## Lead Dossier System (D-06)

Must be added as a new SOUL.md section:

```
Lead statuses:
  new → qualified → audited → contacted → active → completed | closed

Folder structure (on server):
  /opt/data/leads/{lead_id}/
  ├── profile.json        # lead metadata, website, contact info
  ├── chat_history.json   # full chat transcript
  ├── audit_result.json   # SEO audit output (if run_seo_audit was called)
  ├── status.json         # current status + status history
  └── dossier.md          # human-readable lead summary
```

## Omni-Channel Follow-up (D-07)

Must be added as a new SOUL.md section:

```
Channel sequence:
  1. Website chat (iamaim.ru) → Hermes PRESALE mode
  2. Telegram deep link → bind session → continue chat in Telegram
  3. Email follow-up via SendGrid (automated by AIM Backend):
     - Hot leads: instant email after contact collected
     - Warm leads: 3 emails (day 0, day 3, day 7)
     - Cold leads: weekly digest

Day-based follow-up rules:
  Day 0: Thank you + audit summary
  Day 3: Case study relevant to their specialty
  Day 7: "Mikhail is available for a call — book a slot"
  Day 14: Last chance before lead goes cold
```

## WOW-Data Strategy — 7 Free Audit Blocks (D-03)

Must be added as a new SOUL.md section. These are what run_seo_audit returns, but Hermes needs to know how to present them:

```
Block 1: Техническое здоровье сайта (PageSpeed, Core Web Vitals, mobile)
Block 2: Позиции в поиске (топ-3, топ-10, динамика vs конкуренты)
Block 3: Трафик и потенциал роста (текущий трафик, упущенный трафик)
Block 4: Анализ конкурентов (3-5 клиник, gap analysis)
Block 5: Контент-анализ (качество, полнота, медицинская достоверность)
Block 6: Локальное SEO (Яндекс.Карты, 2ГИС, отзывы)
Block 7: Прогноз пациентов (3 числа: пациенты/мес, срок, стоимость)

Presentation rule: NEVER show all 7 blocks at once in PRESALE.
Show blocks 1-2 initially, then blocks 3-4, then blocks 7 (the "3 numbers").
Unfold progressively — each reveal deepens engagement.
```

## Russian Market Knowledge (D-09)

Must be expanded from current minimal mentions to a comprehensive section:

```
Legal compliance:
  - ФЗ-152 "О персональных данных": AES-256-GCM encryption, consent tracking, 7-year retention
  - ФЗ-323 "Об охране здоровья": medical content must reference clinical guidelines
  - ФЗ "О рекламе": mandatory disclaimer "ИМЕЮТСЯ ПРОТИВОПОКАЗАНИЯ..."

Payment: ЮKassa (async_yookassa) — cards, SBP, e-wallets

Document signing: Контур.Диадок (Russian E-signature)

Platforms (Russian market, NOT Western):
  - Яндекс.Директ (NOT Google Ads)
  - Яндекс.Метрика (NOT Google Analytics as primary)
  - Яндекс.Вебмастер (NOT Google Search Console as primary)
  - 2ГИС, Яндекс.Карты (local SEO)
  - VK Ads, Telegram Ads (social)
  - ПроДокторов, НаПоправку (medical review aggregators)

Social networks: VK (primary), Telegram (primary), NOT Facebook/Instagram

Western services that DON'T work in Russia:
  - Stripe, Helcim (payment) → ЮKassa instead
  - DocuSign → Контур.Диадок instead
  - Google Ads → Яндекс.Директ instead
  - HIPAA (US only, not applicable) → ФЗ-152 instead
```

## Code Examples

### SOUL.md Structure Template (Recommended)

```markdown
---
name: aim-operator
description: AIM Operator — единый AI-интерфейс агентства iamaim.ru
---

# AIM Operator — SOUL

## Идентичность (Identity)
[Who I am — 1 paragraph, loaded first]

## Режимы работы (Mode Switching)
[How mode is determined, 3 modes with self-contained behavior for each]

## Инструменты (Tool Catalog)
[All 8 tools with: what, when, inputs, outputs, usage rules]

## Магистры и субагенты (System Architecture)
[Hierarchical: Magister → Subagent list → What each does]

## Процессы (Workflows)
[Presale, Onboarding, Active, Escalation, Reporting]

## WOW-Данные и «3 числа» (WOW-Data Strategy)
[7 blocks, how to present, "3 numbers" framework]

## Token Economy
[Tier 0/1/2, when to launch expensive analyses]

## Lead Dossier и Follow-up
[Statuses, folder structure, omni-channel sequence]

## Российский рынок
[Legal, payments, platforms, compliance]

## Услуги и цены
[4 packages + individual projects]

## KPI Framework
[North Star + per-domain KPIs]

## Стиль общения
[Language, format, handling errors, identity]

## Самообучение
[Auto-skill creation rules]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Direct DeepSeek API calls | Hermes AIAgent with SOUL.md + tool registry | Phase 15 | Hermes now has identity, tools, and mode-based behavior |
| 6 tools (AIM ops only) | 8 tools (+2 Telegram: search_chats, send_message) | Phase 15 | Hermes can search Telegram and send messages as Mikhail |
| SOUL.md as standalone identity | SOUL.md + supplementary skill files (services.md, processes.md, kpi.md) | Phase 15 | Knowledge is modular but SOUL.md is the primary artifact |
| Manual SOUL.md editing | Codebase-audited SOUL.md rewrite | Phase 16 (this phase) | SOUL.md will accurately reflect the codebase |

**Deprecated/outdated:**
- Direct DeepSeek API calls from Next.js: replaced by Hermes as sole LLM gateway (Phase 15)
- SOUL.md subagent lists: inaccurate vs actual codebase (fixing in Phase 16)
- 6-tool assumption: actually 8 tools (fixing in Phase 16)

## Common Pitfalls

### Pitfall 1: Knowledge Rot — SOUL.md Drifts from Codebase
**What goes wrong:** New subagents/Magisters are added to AIM but SOUL.md is never updated. Hermes becomes ignorant of new capabilities over time.
**Why it happens:** SOUL.md is a manual artifact; code changes don't trigger SOUL.md updates.
**How to avoid:** Add a CI check: after any commit that adds/removes a file in `AIM/src/aim/subagents/` or `AIM/src/aim/magisters/`, flag for SOUL.md review. Document this in CLAUDE.md.
**Warning signs:** Hermes says "I can't do that" when the capability exists. Subagent count in SOUL.md < actual file count.

### Pitfall 2: Vague Tool Descriptions
**What goes wrong:** SOUL.md lists tool names without input/output specs. Hermes calls tools with wrong parameters or doesn't call them at all because it doesn't know the exact interface.
**Why it happens:** Tool schemas exist in Python code (registry.register()) but aren't reflected in SOUL.md.
**How to avoid:** Copy the exact `parameters` schema from each tool's `registry.register()` call into SOUL.md. Keep it synchronized.
**Warning signs:** Hermes hallucinates tool parameters. Tool calls fail with schema validation errors.

### Pitfall 3: Mode Confusion
**What goes wrong:** Hermes uses PRESALE behavior in ACTIVE mode (or vice versa). The mode prompt overlay isn't enough — SOUL.md needs clear behavioral boundaries.
**Why it happens:** Mode prompt from `get_mode_prompt()` is only 2-3 sentences. SOUL.md's mode sections are long and the LLM may mix rules between modes.
**How to avoid:** Make each mode section SELF-CONTAINED. Don't say "see PRESALE section for tools" — list available tools directly in each mode section. Use visual separators (`---`).
**Warning signs:** Hermes tries to collect contact from an active client. Hermes shows technical details to a presale lead.

### Pitfall 4: SOUL.md Too Large for Context Window
**What goes wrong:** Comprehensive SOUL.md exceeds effective context window, causing the LLM to forget early sections.
**Why it happens:** Current SOUL.md is 333 lines (~8K tokens). After adding 4 missing domains + detailed tool specs + real subagent lists, it could reach 800-1000 lines (~20-25K tokens). With supplementary skill files, total context could exceed effective window.
**How to avoid:** Use progressive disclosure: critical sections first (identity, mode switching, tools). Deep knowledge later (subagent lists, compliance details). Supplementary skill files (services.md, processes.md, kpi.md) are loaded as separate context, not concatenated.
**Warning signs:** Hermes forgets pricing in long conversations. Mode behavior degrades after multiple tool calls.

### Pitfall 5: Telethon/Telegram Tools Without Clear ADMIN Gate
**What goes wrong:** Hermes uses Telegram tools (send_telegram_message, search_telegram_chats) in PRESALE or ACTIVE mode, sending messages as Mikhail to random contacts.
**Why it happens:** The tool registry doesn't enforce mode-based access control at the tool level. AIAgent tool calling is governed only by the prompt.
**How to avoid:** In SOUL.md, add explicit CRITICAL rules: "Telegram tools (search_telegram_chats, send_telegram_message) are ADMIN-ONLY. Never use in PRESALE or ACTIVE mode. If a non-admin asks, respond 'Я передам ваш запрос Михаилу.'"
**Warning signs:** Hermes searches Telegram chats when a presale client asks "do you work with clinics in my city?"

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing project standard) |
| Config file | none — manual validation for SOUL.md |
| Quick run command | `pytest AIM/tests/ -x -q` |
| Full suite command | `pytest AIM/tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| D-01 | SOUL.md lists ALL Magisters with correct subagent names | manual review | N/A — manual audit | N/A |
| D-02 | Mode sections are self-contained with correct behavior | manual review | N/A | N/A |
| D-03 | 7 WOW blocks documented with presentation rules | manual review | N/A | N/A |
| D-04 | "3 numbers" framework explicitly described | manual review | N/A | N/A |
| D-05 | Token Economy tiers documented with rules | manual review | N/A | N/A |
| D-06 | Lead Dossier statuses and folder structure documented | manual review | N/A | N/A |
| D-07 | Omni-Channel follow-up sequence documented | manual review | N/A | N/A |
| D-08 | Agent orchestration flow documented | manual review | N/A | N/A |
| D-09 | Russian market compliance documented | manual review | N/A | N/A |
| D-10 | All 8 tools documented with exact I/O schemas | manual review | N/A | N/A |

### Sampling Rate
- **Per task commit:** Manual review of written SOUL.md section
- **Per wave merge:** Full SOUL.md review against codebase
- **Phase gate:** End-to-end test: Hermes starts with new SOUL.md, makes tool calls, shows correct mode behavior

### Wave 0 Gaps
- [ ] No automated test for SOUL.md accuracy (this is a documentation phase)
- [ ] Manual validation checklist needed: verify subagent names, tool schemas, mode behaviors
- [ ] Framework: none needed — this is a content creation phase

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | Yes | HERMES_API_KEY Bearer token (auth.py), ADMIN mode protection at Next.js layer |
| V3 Session Management | Yes | AIAgent session_id per conversation, Telegram chat_id binding |
| V4 Access Control | Yes | Mode-based tool access (SOUL.md enforced), ADMIN-only tools |
| V5 Input Validation | Yes | Pydantic models in FastAPI (ChatRequest), contact_type validation in collect_contact |
| V6 Cryptography | Yes | API key for internal service communication, ФЗ-152 field-level encryption at AIM layer |

### Known Threat Patterns for Hermes

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Prompt injection via user message | Spoofing | Hermes mode is set by Next.js (trusted), X-Client-Mode header, not from user input |
| Tool misuse (ADMIN tools in PRESALE) | Elevation of Privilege | SOUL.md explicit rules, mode prompt overlay, ADMIN mode requires NextAuth role=admin at Next.js layer |
| Credential leakage in SOUL.md | Information Disclosure | NEVER put API keys, tokens, or secrets in SOUL.md — reference env vars |
| Session hijacking via session_id | Spoofing | session_id generated by AIAgent internally, bound to conversation context |
| Telegram deep link spoofing (D-18) | Spoofing | web_session_id is server-generated, single-use (popped from _session_bindings) |

## Environment Availability

### Step 2.6: Dependency Audit

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| hermes-agent | AIAgent runtime | ✗ (inside Docker only) | >=0.14.0 | Docker build — not needed for SOUL.md creation |
| Python 3.11 | Runtime | ✓ | 3.14 (host) | SOUL.md is a markdown file — no Python needed to write it |
| OmniRoute | LLM API | ✓ (remote) | custom | Not needed for SOUL.md creation |
| Docker | Container build | — | — | Not needed for this phase |

**Missing dependencies with no fallback:**
- None — this phase produces a markdown file (SOUL.md), no runtime dependencies required

**Missing dependencies with fallback:**
- hermes-agent: only needed to TEST the SOUL.md, not to write it. Testing can be done inside Docker container.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | AIAgent loads entire SOUL.md into context window (no truncation) | Architecture Patterns | If SOUL.md is too large, later sections may be ignored. Mitigated by progressive disclosure structure. |
| A2 | Supplementary skill files (services.md, processes.md, kpi.md) are loaded separately by AIAgent, not concatenated with SOUL.md | Architecture Patterns | If they ARE concatenated, total context could exceed window. LOW risk — these files are well-structured. |
| A3 | Token Economy tiers (0/1/2) map to tool costs as described | Token Economy | If actual costs differ, Hermes may over- or under-use tools. User should validate cost structure. |
| A4 | Lead Dossier folder structure at /opt/data/leads/ matches the described structure | Lead Dossier | If structure differs, Hermes will misdescribe the system to users. Verify with actual Docker volume mount. |
| A5 | Hermes-agent `load_soul_identity=True` loads SOUL.md from HERMES_HOME/SOUL.md (via copy_soul.sh) | Architecture Patterns | If path is different, SOUL.md won't load. Verified by code: Dockerfile copies skills/ to /opt/hermes/skills/, copy_soul.sh copies skills/aim/ to /opt/data/. |
| A6 | The current services.md, processes.md, and kpi.md are accurate and don't need major updates | Knowledge Gaps | These files are already comprehensive (894 lines total). Minor updates may be needed but not a full rewrite. |

## Open Questions

1. **SOUL.md size limit — what is the effective context window?**
   - What we know: AIAgent loads SOUL.md + supplementary skills + mode prompt + conversation history
   - What's unclear: Exact token budget for SOUL.md vs conversation. DeepSeek V4 context is large but effective window for precise instruction following may be smaller.
   - Recommendation: Keep SOUL.md under 600 lines (~15K tokens). Move deep reference material to separate skill files loaded on-demand.

2. **Should subagent lists be exhaustive or representative?**
   - What we know: 70+ subagent files exist. Listing all would bloat SOUL.md.
   - What's unclear: Does Hermes need to know every subagent name, or just capability categories?
   - Recommendation: Group subagents by capability (e.g., "Technical SEO: ci_tech.py, ci_tech_real.py, technical_agent.py, ci_site_crawler.py — handles PageSpeed, Core Web Vitals, crawlability"). List key files without full detail.

3. **How to keep SOUL.md synchronized with codebase changes?**
   - What we know: No automated sync mechanism exists.
   - What's unclear: Should we build a CI check, a pre-commit hook, or rely on manual discipline?
   - Recommendation: Add to CLAUDE.md: "When adding a new Magister/Subagent/tool, update Hermes SOUL.md." Simple manual rule for now.

## Sources

### Primary (HIGH confidence — verified in codebase)
- `AIM/hermes/skills/aim/SOUL.md` — Current SOUL.md (333 lines). [VERIFIED: codebase read]
- `AIM/hermes/app/tools/` — All 8 tool implementations with exact schemas. [VERIFIED: codebase read]
- `AIM/hermes/app/agent_wrapper.py` — Mode prompt construction, AIAgent configuration. [VERIFIED: codebase read]
- `AIM/hermes/app/main.py` — FastAPI wrapper, /api/chat endpoint, metrics. [VERIFIED: codebase read]
- `AIM/hermes/app/telegram_gateway.py` — Bot API + Telethon integration. [VERIFIED: codebase read]
- `AIM/hermes/skills/aim/services.md` — Service catalog (193 lines). [VERIFIED: codebase read]
- `AIM/hermes/skills/aim/processes.md` — Business processes (148 lines). [VERIFIED: codebase read]
- `AIM/hermes/skills/aim/kpi.md` — KPI framework (220 lines). [VERIFIED: codebase read]
- `AIM/hermes/Dockerfile` — Container config, HERMES_HOME, copy_soul.sh. [VERIFIED: codebase read]
- `AIM/src/aim/magisters/` — All 4 Magister implementations. [VERIFIED: codebase read]
- `AIM/src/aim/subagents/` — 70+ subagent files across 10+ packages. [VERIFIED: codebase read]

### Secondary (MEDIUM confidence)
- `AIM/hermes/app/omniroute_direct.py` — Direct LLM client. [VERIFIED: codebase read]
- `AIM/hermes/app/auth.py` — Bearer token auth. [VERIFIED: codebase read]
- `AIM/hermes/requirements.txt` — Dependency list. [VERIFIED: codebase read]

### Tertiary (LOW confidence — training data assumptions)
- LLM knowledge encoding best practices (progressive disclosure, persona engineering). [ASSUMED]
- Token Economy cost tiers — actual API costs not measured. [ASSUMED]
- AIAgent context window behavior with SOUL.md + skill files. [ASSUMED]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified via codebase inspection and requirements.txt
- Architecture: HIGH — entire Hermes codebase read and mapped
- Pitfalls: MEDIUM — pitfalls 1-3 verified by codebase analysis, pitfalls 4-5 are architectural assumptions
- Tool catalog: HIGH — all 8 tools read from source with exact schemas
- Knowledge gaps: HIGH — systematic comparison of SOUL.md vs actual codebase files

**Research date:** 2026-05-19
**Valid until:** 2026-06-19 (30 days — stable domain, but subagent count may change)
