# Codebase Structure

**Analysis Date:** 2026-06-19

## Directory Layout

### Local (Development):
```
AIM/hermes/                                    # Hermes AI agent — root of all agent code
├── app/                                       # FastAPI application
│   ├── main.py                                # FastAPI server — routes, SSE, metrics, health
│   ├── auth.py                                # Bearer token authentication
│   ├── agent_wrapper.py                       # AIAgent lifecycle — prompts, sessions, caching
│   ├── agent_wrapper_optimized.py             # Mode-specific system prompts
│   ├── telegram_gateway.py                    # Telegram webhook + getUpdates polling
│   ├── knowledge_router.py                    # Knowledge vault REST API
│   ├── session_context.py                     # Session context management
│   ├── omniroute_direct.py                    # Legacy: direct OmniRoute LLM proxy calls
│   ├── voice_transcriber.py                   # Voice → text via AssemblyAI
│   ├── token_economy.py                       # Token usage tracking
│   ├── routers/                               # FastAPI routers
│   │   └── session_api.py                     # GET /api/session/{hash} — archive retrieval
│   ├── tools/                                 # Tool handlers — registered in hermes-agent registry
│   │   ├── __init__.py                        # Tool registration: register_all_tools(), register_debug_tools()
│   │   ├── run_prescan.py                     # 3-stage intelligence gathering → /api/presale/prescan-staged
│   │   ├── find_competitors.py                # Apify competitor search → /api/competitors/find
│   │   ├── run_ci_analysis.py                 # Competitive intelligence deep analysis → /api/competitors/analyze
│   │   ├── present_competitors.py             # Save competitor list → /api/competitors/save
│   │   ├── run_seo_audit.py                   # SEO audit → /api/seo/audit
│   │   ├── run_content_analysis.py            # Content analysis → /api/content/analyze
│   │   ├── run_ads_report.py                  # Ads report → /api/ads/report
│   │   ├── run_content_gaps.py                # Content gap analysis
│   │   ├── run_pagespeed.py                   # PageSpeed analysis
│   │   ├── run_review_platforms.py            # Review platform analysis
│   │   ├── run_smi_mentions.py                # SMI mentions monitoring
│   │   ├── run_ads_intelligence.py            # Ads intelligence
│   │   ├── run_web_search.py                  # Web search tool
│   │   ├── run_aim_scout.py                   # Full aim-scout pipeline
│   │   ├── run_full_scout.py                  # Complete scout tool
│   │   ├── run_background_pipeline.py         # Fire-and-forget background pipeline
│   │   ├── run_validation_check.py            # Validation check against prescan data
│   │   ├── run_hh_analysis.py                 # HeadHunter job market analysis
│   │   ├── run_doctor_dossiers.py             # Doctor dossier research
│   │   ├── run_instagram_content.py           # Instagram content analysis
│   │   ├── geo_optimizer_tools.py             # Geographical optimization
│   │   ├── find_company_financials.py         # Company financials from nalog.ru → /api/companies/financials
│   │   ├── quick_overview.py                  # Quick Perplexity intel (~5-10s)
│   │   ├── orchestrate.py                     # Unified orchestrator tool
│   │   ├── finalize_research.py               # Research finalization
│   │   ├── publish_scout_report.py            # Publish scout report to URL
│   │   ├── generate_html_report.py            # HTML report in AIM design system
│   │   ├── collect_contact.py                 # Contact collection → /api/leads
│   │   ├── qualify_lead.py                    # Lead qualification → /api/sales/qualify
│   │   ├── escalate_to_manager.py             # Escalate to human manager → /api/sales/escalate
│   │   ├── show_all_leads.py                  # List all leads → /api/leads
│   │   ├── get_lead_pipeline.py               # Lead pipeline report → /api/sales/pipeline
│   │   ├── show_project_status.py             # Project status → /api/projects/{id}/status
│   │   ├── update_knowledge.py                # Knowledge update → /api/sales/knowledge/update
│   │   ├── send_telegram_file.py              # Send files via Telegram Bot API
│   │   ├── telegram_tools.py                  # Telegram utility tools
│   │   ├── service_categorizer.py             # Medical service categorization
│   │   ├── quality_gate.py                    # Quality gate for pipeline results
│   │   ├── deep_research_merge.py             # Deep research data merging
│   │   ├── shell_exec.py                      # Shell command execution (hermes-debug)
│   │   ├── web_scraper.py                     # Web scraping (hermes-debug)
│   │   ├── external_api.py                    # External API debug (hermes-debug)
│   │   ├── bitrix_scraper.py                  # Bitrix24 scraping (hermes-debug)
│   │   ├── firecrawl_web.py                   # Firecrawl web tool (hermes-debug)
│   │   ├── test_deep_research_merge.py        # Test for deep_research_merge
│   │   └── test_service_categorizer.py        # Test for service_categorizer
│   └── prompts/                               # Static prompt templates
│       ├── sell_presentation.txt              # Sales presentation prompt
│       └── quick_overview.txt                 # Quick overview prompt
├── skills/                                    # LLM-loaded skill documents (SKILL.md)
│   ├── aim/                                   # Core AIM identity package
│   │   ├── SOUL.md                            # ~69KB — full agent identity, tool catalog, protocols
│   │   ├── BOOTSTRAP.md                       # Self-study protocol (first-run only)
│   │   ├── services.md                        # Agency service descriptions and pricing
│   │   ├── processes.md                       # Internal processes and workflows
│   │   ├── kpi.md                             # Key performance indicators
│   │   └── learnings.md                       # Accumulated lessons from conversations
│   ├── client-onboarding-pipeline/            # Full 15-phase onboarding protocol (v5.5.0)
│   │   ├── SKILL.md                           # 15-phase execution checklist with tool patterns
│   │   └── templates/
│   │       └── client-kp-template.html        # HTML proposal template
│   ├── presale-pipeline/                      # Auto-orchestration presale pipeline (v3.3.0)
│   │   ├── SKILL.md                           # 8-skill auto-orchestration with Full Auto mode
│   │   ├── references/
│   │   │   └── vacancy-intel.md               # Vacancy market intelligence reference
│   │   └── schemas/
│   │       └── presale-state.template.json    # Presale state tracking schema
│   ├── deep-research-phase-0/                 # Deep research skill (v1.0)
│   │   └── SKILL.md                           # Doctor research protocol
│   └── software-development/                  # Development-focused skills
│       └── presale-pipeline/
│           ├── assets/
│           │   └── template-prescan-dual-theme.html  # HTML template
│           └── references/
│               └── design-system-dual-theme.md       # Design system reference
├── knowledge/                                 # Knowledge vault — Hermes memory system
│   ├── brand/                                 # Brand knowledge
│   ├── learnings/                             # Per-domain learnings (market conditions, etc.)
│   ├── proposals/                             # Generated client proposals
│   │   └── psyholog48/                        # Per-client proposal directories
│   ├── tools/                                 # Tool-specific knowledge
│   ├── pricing.md                             # Pricing reference
│   └── ingest.py                              # LLM-based knowledge ingestion pipeline
├── scripts/                                   # Container lifecycle scripts
│   ├── copy_soul.sh                           # Copy SOUL.md + supplementary files to /opt/data/
│   └── bootstrap.sh                           # First-run self-study trigger (via /api/chat)
├── patches/                                   # Monkey patches for external libraries
│   ├── __init__.py
│   └── firecrawl_provider_bank.py             # Firecrawl API key rotation patch
├── tests/                                     # Test suite
│   └── test_presale_flow.py                   # Integration tests for presale pipeline
├── data/                                      # Local data directory (gitignored)
├── mcp-proxy/                                 # MCP protocol bridge
│   └── proxy.py                               # MCP proxy server
├── work/                                      # Working files
│   └── presale/                               # Presale-related work files
│       └── arclinic-fresh-2026-06-08/         # Per-client work directory
├── docs/                                      # Documentation
│   ├── ACTIVATION_SEQUENCE.md                 # Startup sequence documentation
│   └── TOOL_TRAINING_GUIDE.md                 # How tools are trained/configured
├── Dockerfile                                 # Container image definition
├── requirements.txt                           # Python dependencies (hermes-agent==0.14.0, httpx, etc.)
├── .current-task                              # Single-line current task marker
├── 3PHASE_PIPELINE.md                         # Detailed 3-phase presale pipeline (for mode prompt)
├── BUGS_AND_FINDINGS.md                       # Bug tracker and findings log
├── TESTING_REPORT.md                          # Comprehensive testing report
└── re-run_tools.py                            # Tool re-run utility script
```

### Server (`ssh aim` — /opt/hermes-data/):
```
/opt/hermes-data/                              # Hermes persistent data (Docker volume mount)
├── .env                                       # Environment variables (HERMES_API_KEY, API keys)
├── config.yaml                                # hermes-agent configuration (model, providers, limits)
├── SOUL.md                                    # Copied from /opt/hermes/skills/aim/SOUL.md at startup
├── state.db                                   # SQLite session database (21MB+)
├── kanban.db                                  # Kanban state database
├── gateway_state.json                         # Gateway state
├── gateway.pid                                # Gateway process PID
├── .bootstrapped                              # Bootstrap completion flag
├── skills/                                    # Runtime skills (curated by the system)
│   └── aim/
│       ├── aim-operations/                    # Runtime curated skills
│       └── client-onboarding-pipeline/        # Runtime pipeline skill
├── sessions/                                  # Session data directory (SQLite access)
├── knowledge/                                 # Knowledge vault data (persistent)
│   ├── brand/                                 # Brand assets
│   ├── learnings/                             # Learning files
│   ├── proposals/                             # Client proposals
│   │   └── psyholog48/
│   ├── raw/executions/                        # Raw execution logs
│   ├── wiki/learnings/                        # Structured learnings
│   ├── wiki/patterns/                         # Extracted patterns
│   ├── decisions/rules/                       # Decision rules
│   └── tools/                                 # Tool-specific knowledge
├── memories/                                  # Agent memory files
├── reports/                                   # Generated reports
│   ├── av-clinic/                             # Per-client report directories
│   └── iphk/
├── logs/                                      # Log files
│   └── curator/                               # Curator agent logs
├── backups/                                   # Backup archives
│   └── hermes_full_20260618_213733/           # Full backup from 2026-06-18
│       ├── keys/                              # API key pool
│       ├── memories/                          # Memory backup
│       ├── scripts/                           # Script backup
│       └── skills/                            # Skills backup (including ui-ux-pro-max)
├── keys/                                      # API key pool and rotation state
├── scripts/                                   # Server-side scripts
├── cron/                                      # Cron job output
├── cache/                                     # Cache directories
│   ├── documents/                             # Cached documents
│   └── screenshots/                           # Cached screenshots
├── chat-exports/                              # Exported chat sessions
├── sandboxes/                                 # Development sandboxes
│   └── singularity/                           # Container sandbox
├── audio_cache/                               # Telegram voice message cache
├── image_cache/                               # Downloaded image cache
├── decisions/rules/                           # Decision rules from learnings
├── hooks/                                     # Runtime hooks
├── pairing/                                   # Client pairing data
├── bin/                                       # Binary utilities
├── raw/executions/                            # Raw execution records
└── wiki/                                      # Wiki knowledge
    ├── learnings/                             # Structured learnings
    └── patterns/                              # Pattern library
```

### Docker Container (`docker exec hermes` — /opt/hermes/):
```
/opt/hermes/                                   # Application code (Docker image layer)
├── app/                                       # FastAPI application (same as local AIM/hermes/app/)
│   ├── main.py
│   ├── auth.py
│   ├── agent_wrapper.py
│   ├── agent_wrapper_optimized.py
│   ├── telegram_gateway.py
│   ├── knowledge_router.py
│   ├── voice_transcriber.py
│   ├── token_economy.py
│   ├── omniroute_direct.py
│   ├── routers/
│   │   └── session_api.py
│   ├── tools/                                 # Tool handlers (SERVER VERSION — simpler set)
│   │   ├── __init__.py                        # register_all_tools(): orchestrate + 16 legacy + rotate_api_key
│   │   ├── orchestrate.py                     # Unified orchestrator
│   │   ├── quick_overview.py                  # Quick Perplexity intel
│   │   ├── run_prescan.py                     # Staged + legacy fallback
│   │   ├── find_competitors.py
│   │   ├── run_ci_analysis.py
│   │   ├── present_competitors.py
│   │   ├── run_seo_audit.py
│   │   ├── run_content_analysis.py
│   │   ├── run_content_gaps.py
│   │   ├── run_ads_report.py
│   │   ├── run_ads_intelligence.py
│   │   ├── run_pagespeed.py
│   │   ├── run_review_platforms.py
│   │   ├── run_smi_mentions.py
│   │   ├── run_web_search.py
│   │   ├── run_aim_scout.py
│   │   ├── run_validation_check.py
│   │   ├── run_hh_analysis.py
│   │   ├── run_doctor_dossiers.py
│   │   ├── run_instagram_content.py
│   │   ├── geo_optimizer_tools.py
│   │   ├── finalize_research.py
│   │   ├── find_company_financials.py
│   │   ├── rotate_api_key.py
│   │   ├── collect_contact.py
│   │   ├── qualify_lead.py
│   │   ├── escalate_to_manager.py
│   │   ├── show_all_leads.py
│   │   ├── get_lead_pipeline.py
│   │   ├── show_project_status.py
│   │   ├── update_knowledge.py
│   │   ├── send_telegram_file.py
│   │   ├── service_categorizer.py
│   │   ├── deep_research_merge.py
│   │   ├── shell_exec.py                      # Debug toolset
│   │   ├── web_scraper.py
│   │   ├── external_api.py
│   │   ├── bitrix_scraper.py
│   │   └── firecrawl_web.py
│   └── prompts/
│       ├── sell_presentation.txt
│       └── quick_overview.txt
├── skills/                                    # Built into image at build time (r/o)
│   ├── aim/
│   │   ├── SOUL.md
│   │   ├── services.md
│   │   ├── processes.md
│   │   └── kpi.md
│   └── ...
├── knowledge/                                 # Built into image at build time
│   ├── vault.py
│   ├── ingest.py
│   ├── teacher_sync.py
│   ├── pricing.md
│   └── ...
├── scripts/
│   ├── copy_soul.sh
│   └── bootstrap.sh
├── patches/
│   └── firecrawl_provider_bank.py
├── requirements.txt
└── Dockerfile
```

## Directory Purposes

**`AIM/hermes/app/`:**
- Purpose: FastAPI application — all runtime Python code
- Contains: Server entry point, auth, agent wrapper, tools, routers, gateway, knowledge management
- Key files: `main.py` (FastAPI server), `agent_wrapper.py` (AIAgent lifecycle), `tools/__init__.py` (registry)

**`AIM/hermes/app/tools/`:**
- Purpose: Tool handlers — registered in hermes-agent's tool registry, translate LLM tool calls into HTTP requests to aim-app
- Contains: One Python file per tool, each registering itself via `registry.register()` at module import
- Key files: `__init__.py` (registration orchestrator), `run_prescan.py` (primary presale tool), `find_competitors.py` (competitor discovery)

**`AIM/hermes/skills/`:**
- Purpose: LLM-loaded Markdown documents — define agent behaviors, workflows, and domain knowledge
- Contains: SKILL.md files with YAML frontmatter (name, version, triggers, description)
- Key files: `aim/SOUL.md` (69KB identity), `client-onboarding-pipeline/SKILL.md` (v5.5.0), `presale-pipeline/SKILL.md` (v3.3.0)

**`/opt/hermes-data/` (server):**
- Purpose: Runtime persistent data — everything Hermes writes at runtime
- Contains: `.env` (secrets), `config.yaml` (live config), `state.db` (21MB SQLite sessions), SOUL.md (runtime copy), skills/ (curated), knowledge/ (vault data), sessions/ (session state), reports/ (generated reports)
- Generated (written by Hermes at runtime): learnings, proposals, reports, raw executions, wiki patterns

**`/opt/hermes/` (Docker container):**
- Purpose: Application code from Docker image — built at deploy time, read-only at runtime
- Contains: Same code as `AIM/hermes/app/`, `AIM/hermes/knowledge/`, `AIM/hermes/skills/`, `AIM/hermes/scripts/`
- Key difference from local: tools/__init__.py on server registers 18 tools (simpler set), local version registers 38+ tools

**`/opt/data/` (Docker volume):**
- Purpose: Persistent data volume — survives container restarts and redeploys
- Contains: state.db, SOUL.md, .env, config.yaml, knowledge/, sessions/, memories/, reports/, skills/
- Mounted at HERMES_HOME (`/opt/data`)

## Key File Locations

**Entry Points:**
- `AIM/hermes/app/main.py:103`: FastAPI app creation
- `AIM/hermes/app/main.py:263`: POST /api/chat — synchronous chat
- `AIM/hermes/app/main.py:312`: POST /api/chat/stream — SSE streaming chat
- `AIM/hermes/app/main.py:188`: GET /health — health check + metrics
- `AIM/hermes/app/telegram_gateway.py:110`: POST /telegram/webhook — Telegram webhook
- `AIM/hermes/Dockerfile:87`: Container ENTRYPOINT — copy_soul.sh + uvicorn

**Configuration:**
- `AIM/hermes/Dockerfile:62-71`: ENV variables (HERMES_HOME, PYTHONUNBUFFERED, OMNIROUTE_URL)
- `/opt/hermes-data/config.yaml`: Runtime hermes-agent configuration (model, providers, limits, toolset, compression)
- `AIM/hermes/requirements.txt`: Python dependencies (hermes-agent==0.14.0, httpx, telethon, assemblyai)
- `AIM/hermes/app/auth.py:13`: HERMES_API_KEY from env

**Core Logic:**
- `AIM/hermes/app/agent_wrapper.py:397`: `_create_agent()` — AIAgent factory with all config
- `AIM/hermes/app/agent_wrapper.py:538`: `run_agent_sync()` — main sync execution path
- `AIM/hermes/app/agent_wrapper.py:679`: `run_agent()` — async wrapper for FastAPI
- `AIM/hermes/app/agent_wrapper.py:110`: `build_system_prompt()` — SOUL.md + mode prompt assembly
- `AIM/hermes/app/agent_wrapper_optimized.py:149`: `_presale_prompt()` — 3-phase presale flow definition
- `AIM/hermes/app/tools/__init__.py:28`: `register_all_tools()` — tool registration orchestrator
- `AIM/hermes/app/tools/__init__.py:102`: `register_debug_tools()` — debug toolset registration

**Testing:**
- `AIM/hermes/tests/test_presale_flow.py`: Integration tests for presale pipeline
- `AIM/hermes/TESTING_REPORT.md`: 23KB comprehensive testing report

**Documentation:**
- `AIM/hermes/docs/ACTIVATION_SEQUENCE.md`: Startup sequence
- `AIM/hermes/docs/TOOL_TRAINING_GUIDE.md`: Tool configuration/training
- `AIM/hermes/3PHASE_PIPELINE.md`: 18KB detailed 3-phase presale pipeline

## Naming Conventions

**Files:**
- Tool modules: snake_case matching tool name — `run_prescan.py`, `find_competitors.py`, `show_all_leads.py`
- System files: UPPERCASE for identity/protocol — `SOUL.md`, `SKILL.md`, `BOOTSTRAP.md`, `Dockerfile`
- Documentation: UPPERCASE_SNAKE — `ACTIVATION_SEQUENCE.md`, `BUGS_AND_FINDINGS.md`, `TESTING_REPORT.md`
- Shell scripts: snake_case — `copy_soul.sh`, `bootstrap.sh`
- Session/data stores: dot-prefixed hidden — `.current-task`, `.bootstrapped`

**Functions:**
- Tool handlers: `handle_<tool_name>` — `handle_run_prescan()`, handler is typically an async function
- Registration: `register_all_tools()`, `register_debug_tools()`
- Internal helpers: `_underscore_prefixed` — `_create_agent()`, `_presale_prompt()`, `_get_thread_lock()`
- Mode prompts: `_<mode>_prompt()` — `_presale_prompt()`, `_active_prompt()`

**Directories:**
- Tools: each tool is one `.py` file in `tools/` — no subdirectories
- Skills: `skills/<skill-name>/` with mandatory `SKILL.md` + optional `templates/`, `references/`, `scripts/`
- Knowledge: `knowledge/<domain>/` — brand, learnings, proposals, tools

**Environment Variables:**
- UPPERCASE_SNAKE — `HERMES_HOME`, `LLM_MODEL`, `TELEGRAM_BOT_TOKEN`, `AIM_API_BASE`, `OMNIROUTE_URL`

## Where to Add New Code

**New Tool (aim-operations toolset):**
- Primary code: `AIM/hermes/app/tools/<tool_name>.py` — implement handler function + `registry.register()` call at module level
- Registration: Add `_import_tool("<tool_name>")` in `register_all_tools()` in `AIM/hermes/app/tools/__init__.py`
- Tests: `AIM/hermes/tests/test_<tool_name>.py`

**New Debug Tool (hermes-debug toolset):**
- Primary code: `AIM/hermes/app/tools/<tool_name>.py`
- Registration: Add `_import_tool("<tool_name>")` in `register_debug_tools()` in `AIM/hermes/app/tools/__init__.py`

**New Skill:**
- Primary code: `AIM/hermes/skills/<skill-name>/SKILL.md` — YAML frontmatter with `name`, `version`, `description`, `triggers`
- Templates: `AIM/hermes/skills/<skill-name>/templates/`
- References: `AIM/hermes/skills/<skill-name>/references/`
- The skill is loaded by LLM via `skill_view(name='<skill-name>')` at runtime

**New Mode (e.g., PARTNER):**
- Prompt: Add `_partner_prompt()` function in `AIM/hermes/app/agent_wrapper_optimized.py`
- Registration: Add to `get_mode_prompt()` dict in `AIM/hermes/app/agent_wrapper.py:140`
- Mode detection: Update `_get_mode()` in `AIM/hermes/app/telegram_gateway.py:36`

**New SOUL.md Section:**
- Edit: `AIM/hermes/skills/aim/SOUL.md` (source of truth)
- Deploy: Rebuild Docker image (or restart container — `copy_soul.sh` will recopy if source is newer)

**New Config Parameter:**
- Edit: `/opt/hermes-data/config.yaml` on server (runtime config)
- The hermes-agent library reads config.yaml via its own config system

## Special Directories

**`AIM/hermes/app/__pycache__/`:**
- Purpose: Python bytecode cache
- Generated: Yes (automatically by Python)
- Committed: No (gitignored)

**`AIM/hermes/skills/`:**
- Purpose: Source of truth for skill documents — built into Docker image at build time
- Generated: No (hand-authored)
- Committed: Yes (in version control)
- Server equivalent: Copied into Docker image via `COPY skills/ ./skills/` in Dockerfile; runtime curated version exists at `/opt/data/skills/`

**`/opt/hermes-data/` (server volume):**
- Purpose: All runtime persistent data — state, config, knowledge, memories
- Generated: Yes (created/modified at runtime by Hermes)
- Committed: No (Docker volume, backed up separately)
- Mechanism: Docker volume mount — `-v /opt/hermes-data:/opt/data`

**`AIM/hermes/knowledge/`:**
- Purpose: Knowledge vault code + seed data — built into Docker image
- Generated: Partially (seed data hand-authored, runtime files generated)
- Committed: Yes (code + seed data)
- Server equivalent: `/opt/data/knowledge/` is the runtime vault instance

---

*Structure analysis: 2026-06-19*
