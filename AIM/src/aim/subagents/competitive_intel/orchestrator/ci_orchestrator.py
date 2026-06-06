"""
CI Orchestrator Agent - Universal Competitive Intelligence System

Координирует 23 специализированных агента через 16 фаз для полной конкурентной разведки.
Три уровня глубины: Quick (1-4), Deep (1-9), Full (1-16).
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import json
import os
import asyncio
import logging

from meai.agents.base_agent import Agent, Task, TaskResult
from meai.events.event_bus import Event, EventBus, Message
from meai.memory.obsidian import ObsidianVault

logger = logging.getLogger(__name__)


class CIOrchestrator(Agent):
    """
    CI Orchestrator - главный координатор конкурентной разведки.

    Управляет 23 агентами через 16 фаз:
    - Phases 1-4: Quick analysis (Scout, Auditor, Reputation)
    - Phases 5-9: Deep analysis (7 parallel agents + FactChecker + Strategist)
    - Phases 10-16: Full pipeline (TW agents + Offer Generator)
    """

    def __init__(
        self,
        agent_id: str,
        event_bus: EventBus,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        vault_path: str = "AIM/obsidian/ci-orchestrator"
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="ci-orchestrator",
            database_url=database_url,
            vault_path=vault_path,
        )
        self.event_bus = event_bus
        self.vault = ObsidianVault(vault_path)
        self.state_file = "AIM/data/ci-state.json"

        # Tier definitions
        self.tiers = {
            "quick": {"phases": range(1, 5), "time": "15 min", "cost": "low"},
            "deep": {"phases": range(1, 10), "time": "45 min", "cost": "medium"},
            "full": {"phases": range(1, 17), "time": "90 min", "cost": "high"}
        }

        # Agent mapping to phases
        self.phase_agents = {
            1: "ci-scout",
            2: "ci-auditor",
            3: "ci-auditor",
            4: "ci-reputation",
            5: ["ci-finance", "ci-vacancies", "ci-tech", "ci-site-crawler",
                "ci-content", "ci-pricing", "ci-ecosystem", "ci-backlink", "ci-rank-tracker"],  # Parallel
            6: "ci-factchecker",
            7: "ci-strategist",
            8: "ci-strategist",
            9: "ci-prioritizer",
            10: "ci-marketing-strategy",
            11: "tw-competitor-scout",
            12: "tw-creative-collector",
            13: "tw-creative-analyzer",
            14: "tw-pattern-finder",
            15: "tw-traffic-analyzer",
            16: "ci-offer-generator"
        }

        # Agent registry (lazy initialization)
        self._agent_instances = {}

        # Completed results from EventBus delegation (correlation_id:agent_name → result)
        self._completed_results: Dict[str, Dict[str, Any]] = {}

        # Phase-pending Events for dict-based completion signalling (avoids N transient subscribers)
        self._phase_pending: Dict[str, asyncio.Event] = {}

        # Phase-specific timeouts (seconds) — agents have different runtime profiles
        self._phase_timeouts: Dict[int, float] = {
            1: 420.0,   # ci-scout: Apify + DaData fallback + parallel HTTP profile building (15 sites × 15s)
            2: 180.0,   # ci-auditor: httpx scraping (technical + content + ux_ui) — 3+ competitors × HTML+PageSpeed
            3: 180.0,   # ci-auditor: competitive comparison
            4: 120.0,   # ci-reputation: multi-platform review scraping
            5: 300.0,   # 9 parallel agents: ci-site-crawler needs time to crawl 10 sites
            6: 60.0,    # ci-factchecker: cross-reference validation
            7: 60.0,    # ci-strategist: synthesis + positioning
            8: 60.0,    # ci-strategist: GTM + recommendations
            9: 60.0,    # ci-prioritizer: insight scoring + action plan
        }

        # Persistent subscriber: collects ALL ci.agent.completed events for audit trail
        self.event_bus.subscribe("ci.agent.completed", self._on_agent_completed)

    async def _get_agent(self, agent_name: str):
        """Get or create agent instance (lazy initialization with EventBus setup).

        After Wave 1: agents share the orchestrator's EventBus, report_result is bridged
        to publish ci.agent.completed Events, and agent.initialize() is called to start
        DB connection and vault.
        """
        if agent_name in self._agent_instances:
            return self._agent_instances[agent_name]

        # Get database_url from parent Agent class
        db_url = getattr(self, 'database_url', "sqlite+aiosqlite:///./data/meai.db")
        vault = str(getattr(self, 'vault_path', './obsidian'))

        # Import and create agent
        try:
            if agent_name == "ci-scout":
                from src.aim.subagents.competitive_intel.agents.ci_scout import CIScoutAgent
                agent = CIScoutAgent(agent_id=f"{self.agent_id}-scout", database_url=db_url, vault_path=vault)
            elif agent_name == "ci-auditor":
                from src.aim.subagents.competitive_intel.agents.ci_auditor import CIAuditorAgent
                agent = CIAuditorAgent(agent_id=f"{self.agent_id}-auditor", database_url=db_url, vault_path=vault)
            elif agent_name == "ci-reputation":
                from src.aim.subagents.competitive_intel.agents.ci_reputation import CIReputationAgent
                agent = CIReputationAgent(agent_id=f"{self.agent_id}-reputation", database_url=db_url, vault_path=vault, brave_api_key=os.getenv("BRAVE_API_KEY"))
            elif agent_name == "ci-finance":
                from src.aim.subagents.competitive_intel.agents.ci_finance import CIFinanceAgent
                agent = CIFinanceAgent(agent_id=f"{self.agent_id}-finance", database_url=db_url, vault_path=vault)
            elif agent_name == "ci-vacancies":
                from src.aim.subagents.competitive_intel.agents.ci_vacancies import CIVacanciesAgent
                agent = CIVacanciesAgent(agent_id=f"{self.agent_id}-vacancies", database_url=db_url, vault_path=vault)
            elif agent_name == "ci-tech":
                from src.aim.subagents.competitive_intel.agents.ci_tech_real import CITechAgent
                agent = CITechAgent(agent_id=f"{self.agent_id}-tech", database_url=db_url, vault_path=vault)
            elif agent_name == "ci-site-crawler":
                from src.aim.subagents.competitive_intel.agents.ci_site_crawler import CISiteCrawlerAgent
                agent = CISiteCrawlerAgent(agent_id=f"{self.agent_id}-crawler", database_url=db_url, vault_path=vault)
            elif agent_name == "ci-content":
                from src.aim.subagents.competitive_intel.agents.ci_content_improved import CIContentAgentImproved
                agent = CIContentAgentImproved(agent_id=f"{self.agent_id}-content", database_url=db_url, vault_path=vault)
            elif agent_name == "ci-pricing":
                from src.aim.subagents.competitive_intel.agents.ci_pricing import CIPricingAgent
                agent = CIPricingAgent(agent_id=f"{self.agent_id}-pricing", database_url=db_url, vault_path=vault)
            elif agent_name == "ci-ecosystem":
                from src.aim.subagents.competitive_intel.agents.ci_ecosystem import CIEcosystemAgent
                agent = CIEcosystemAgent(agent_id=f"{self.agent_id}-ecosystem", database_url=db_url, vault_path=vault)
            elif agent_name == "ci-backlink":
                from src.aim.subagents.competitive_intel.agents.ci_backlink import CIBacklinkAgent
                agent = CIBacklinkAgent(agent_id=f"{self.agent_id}-backlink", database_url=db_url, vault_path=vault)
            elif agent_name == "ci-rank-tracker":
                from src.aim.subagents.competitive_intel.agents.ci_rank_tracker import CIRankTrackerAgent
                agent = CIRankTrackerAgent(agent_id=f"{self.agent_id}-ranktracker", database_url=db_url, vault_path=vault)
            elif agent_name == "ci-factchecker":
                from src.aim.subagents.competitive_intel.agents.ci_factchecker import CIFactcheckerAgent
                agent = CIFactcheckerAgent(agent_id=f"{self.agent_id}-factchecker", database_url=db_url, vault_path=vault)
            elif agent_name == "ci-strategist":
                from src.aim.subagents.competitive_intel.agents.ci_strategist import CIStrategistAgent
                agent = CIStrategistAgent(agent_id=f"{self.agent_id}-strategist", database_url=db_url, vault_path=vault)
            elif agent_name == "ci-prioritizer":
                from src.aim.subagents.competitive_intel.agents.ci_prioritizer import CIPrioritizerAgent
                agent = CIPrioritizerAgent(agent_id=f"{self.agent_id}-prioritizer", database_url=db_url, vault_path=vault)
            elif agent_name == "ci-marketing-strategy":
                from src.aim.subagents.competitive_intel.agents.ci_marketing_strategy import CIMarketingStrategyAgent
                agent = CIMarketingStrategyAgent(agent_id=f"{self.agent_id}-marketing", database_url=db_url, vault_path=vault)
            elif agent_name == "ci-offer-generator":
                from src.aim.subagents.competitive_intel.agents.ci_offer_generator import CIOfferGeneratorAgent
                agent = CIOfferGeneratorAgent(agent_id=f"{self.agent_id}-offer", database_url=db_url, vault_path=vault)
            else:
                # TW agents not implemented yet - return None
                return None

            # ── Wave 1: EventBus injection + report_result bridge + initialization ──

            # Inject shared EventBus (replaces agent's own per-instance EventBus)
            agent.event_bus = self.event_bus

            # Track per-phase correlation_id for the bridge to use
            agent._ci_correlation_id: Optional[str] = None

            # Bridge report_result to publish ci.agent.completed Event on shared EventBus
            _original_report = agent.report_result

            async def _bridged_report(result):
                await _original_report(result)
                # Publish ci.agent.completed Event so the orchestrator's
                # transient callback in _execute_single_phase can catch it
                corr_id = getattr(agent, '_ci_correlation_id', 'unknown')
                await self.event_bus.publish(Event(
                    event_type="ci.agent.completed",
                    payload={
                        "correlation_id": corr_id,
                        "agent": agent_name,
                        "phase": None,  # Set by _execute_single_phase via agent._ci_correlation_id
                        "status": result.status if hasattr(result, 'status') else 'completed',
                        "result": result.result if hasattr(result, 'result') else {},
                    }
                ))

            agent.report_result = _bridged_report

            # Initialize agent (DB, vault, event bus)
            await agent.initialize()

            self._agent_instances[agent_name] = agent
            return agent

        except ImportError as e:
            logger.warning(f"Failed to import agent {agent_name}: {e}")
            return None

    async def _on_agent_completed(self, event: Event) -> None:
        """Persistent handler for ci.agent.completed events — stores results for audit trail
        and signals phase-pending waiters via dict-based approach.

        Collects ALL agent completion events regardless of which phase initiated them.
        The dict-based _phase_pending replaces per-phase transient subscribers, eliminating
        N-callback amplification during parallel phase execution (Phase 5 with 9 agents).
        """
        correlation_id = event.payload.get("correlation_id", "unknown")
        agent_name = event.payload.get("agent", "unknown")
        key = f"{correlation_id}:{agent_name}"
        self._completed_results[key] = {
            "agent": agent_name,
            "phase": event.payload.get("phase"),
            "status": event.payload.get("status"),
            "result": event.payload.get("result", {}),
            "timestamp": event.timestamp.isoformat() if hasattr(event.timestamp, 'isoformat') else str(event.timestamp),
        }

        # Signal phase-specific waiters via dict-based approach (avoids N transient subscribers)
        phase_event = self._phase_pending.pop(correlation_id, None)
        if phase_event:
            phase_event.set()

    async def execute_ci_analysis(
        self,
        task_data: Dict[str, Any],
        progress_callback: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Execute CI analysis for Intelligence Magister integration.

        Args:
            task_data: Task data dict with:
                - task_id: Task identifier
                - niche: Business niche
                - geo: Geographic location
                - target_audience: Target audience (optional)
                - price_segment: Price segment (optional)
                - tier: Analysis tier (quick/deep/full)
                - competitors: List of competitor URLs
                - deadline: Task deadline (optional)
            progress_callback: Async callback for progress updates
                               Called with (phase: int, status: str, message: str)

        Returns:
            Dict with CI analysis results:
                - task_id: Task identifier
                - tier: Analysis tier used
                - phases_executed: List of executed phase numbers
                - execution_time_seconds: Total execution time
                - competitors_analyzed: Number of competitors analyzed
                - findings: Analysis findings dict
                - reports: Dict with report file paths
                - errors: List of error messages
        """
        start_time = datetime.now()
        tier = task_data.get("tier", "deep")
        task_id = task_data.get("task_id", "unknown")
        url = task_data.get("url", "")
        niche = task_data.get("niche", "")
        geo = task_data.get("geo", "")

        # Generate correlation_id for cross-event traceability
        correlation_id = f"ci-{uuid4().hex[:8]}"

        # Publish execution started event
        await self.event_bus.publish(Event(
            event_type="ci.execution.started",
            payload={
                "correlation_id": correlation_id,
                "task_id": task_id,
                "url": url,
                "niche": niche,
                "geo": geo,
                "tier": tier,
            }
        ))

        try:
            # Get phases for tier
            phases = list(self.tiers[tier]["phases"])

            # Quick tier optimization — route to fast path
            if tier == "quick":
                return await self._run_quick_analysis(task_data, correlation_id)

            # Execute phases with progress updates
            findings = {}
            errors = []
            competitors_list = task_data.get("competitors", [])  # Initial URLs

            for phase_num in phases:
                if progress_callback:
                    await progress_callback(
                        phase_num,
                        "in_progress",
                        f"Executing phase {phase_num}"
                    )

                try:
                    # Get agent(s) for this phase
                    agent_names = self.phase_agents.get(phase_num)

                    # Skip duplicate agent phases (same agent as previous phase = duplicate)
                    if phase_num > 1:
                        prev_agent = self.phase_agents.get(phase_num - 1)
                        if agent_names == prev_agent and prev_agent is not None:
                            prev_key = f"phase_{phase_num - 1}"
                            if prev_key in findings:
                                dup_result = dict(findings[prev_key])
                                dup_result["phase"] = phase_num
                                dup_result["_deduplicated"] = True
                                findings[f"phase_{phase_num}"] = dup_result
                                continue

                    # Prepare phase-specific task data
                    phase_task_data = task_data.copy()
                    phase_task_data["correlation_id"] = correlation_id
                    # Pass the target URL as our_url for backlink comparison
                    phase_task_data["our_url"] = url
                    # Pass accumulated phase results so downstream agents
                    # (strategist, prioritizer) can extract insights
                    phase_task_data["previous_results"] = {k: v for k, v in findings.items()}

                    # Phase 1 uses initial URLs, Phase 2+ uses results from Phase 1
                    if phase_num == 1:
                        phase_task_data["competitors"] = competitors_list
                    else:
                        # Use top_for_analysis from Phase 1 if available
                        if "phase_1" in findings and "result" in findings["phase_1"]:
                            phase1_result = findings["phase_1"]["result"]
                            top = phase1_result.get("top_for_analysis", [])
                            if top:
                                # Normalize: bare URL strings → competitor dicts
                                if isinstance(top[0], str):
                                    phase_task_data["competitors"] = [
                                        {"name": _extract_name_from_url(u), "url": u} for u in top
                                    ]
                                else:
                                    phase_task_data["competitors"] = top
                            else:
                                # Fallback: convert URLs to objects with extracted names
                                phase_task_data["competitors"] = [
                                    {"name": _extract_name_from_url(url), "url": url} for url in competitors_list
                                ]
                        else:
                            # Fallback: convert URLs to objects with extracted names
                            phase_task_data["competitors"] = [
                                {"name": _extract_name_from_url(url), "url": url} for url in competitors_list
                            ]

                    phase_timeout = self._phase_timeouts.get(phase_num, 60.0)
                    if isinstance(agent_names, list):
                        # Phase 5: Parallel execution (direct=True bypasses EventBus poll loop)
                        phase_result = await self._execute_parallel_phase(
                            phase_num, agent_names, phase_task_data, timeout=phase_timeout, direct=True
                        )
                    else:
                        # Single agent execution (direct=True bypasses EventBus poll loop)
                        phase_result = await self._execute_single_phase(
                            phase_num, agent_names, phase_task_data, timeout=phase_timeout, direct=True
                        )

                    findings[f"phase_{phase_num}"] = phase_result
                except Exception as e:
                    errors.append(f"Phase {phase_num} failed: {str(e)}")

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()

            # Validate results quality
            quality_score = self._calculate_quality_score(findings, phases)

            # Count actual competitors from Phase 1 results (ci-scout)
            actual_competitors = _count_actual_competitors(findings, task_data)

            # Generate reports
            reports = await self._generate_reports(task_id, findings, task_data)

            summary = {
                "tier": tier,
                "phases_executed": len(phases),
                "execution_time_seconds": int(execution_time),
                "competitors_analyzed": actual_competitors,
                "quality_score": quality_score,
                "errors_count": len(errors),
            }

            # Publish execution completed event
            await self.event_bus.publish(Event(
                event_type="ci.execution.completed",
                payload={
                    "correlation_id": correlation_id,
                    "task_id": task_id,
                    "summary": summary,
                }
            ))

            # Build presale-friendly fields from findings
            presale = self._build_quick_summary(findings, task_data)

            # Return structured result
            return {
                "task_id": task_id,
                "tier": tier,
                "phases_executed": phases,
                "execution_time_seconds": int(execution_time),
                "competitors_analyzed": actual_competitors,
                "findings": findings,
                "reports": reports,
                "quality_score": quality_score,
                "errors": errors,
                "correlation_id": correlation_id,
                **presale,
            }

        except Exception as e:
            return {
                "task_id": task_id,
                "tier": tier,
                "phases_executed": [],
                "execution_time_seconds": 0,
                "competitors_analyzed": 0,
                "findings": {},
                "reports": {},
                "errors": [f"CI analysis failed: {str(e)}"]
            }

    async def _run_quick_analysis(
        self,
        task_data: Dict[str, Any],
        correlation_id: str,
    ) -> Dict[str, Any]:
        """Run quick-tier CI analysis (phases 1-4 only) — optimized pre-sale path.

        Uses PipelineRunner + ComparisonMatrix for fast deterministic
        analysis without LLM calls, suitable for pre-sale chatbot context (<~10s).
        """
        start_time = datetime.now()
        tier = "quick"
        task_id = task_data.get("task_id", "unknown")

        try:
            phases = list(self.tiers[tier]["phases"])  # [1, 2, 3, 4]
            findings = {}
            errors = []
            competitors_list = task_data.get("competitors", [])

            for phase_num in phases:
                try:
                    agent_names = self.phase_agents.get(phase_num)

                    # Skip duplicate agent phases
                    if phase_num > 1:
                        prev_agent = self.phase_agents.get(phase_num - 1)
                        if agent_names == prev_agent and prev_agent is not None:
                            prev_key = f"phase_{phase_num - 1}"
                            if prev_key in findings:
                                dup_result = dict(findings[prev_key])
                                dup_result["phase"] = phase_num
                                dup_result["_deduplicated"] = True
                                findings[f"phase_{phase_num}"] = dup_result
                                continue

                    phase_task_data = task_data.copy()
                    phase_task_data["correlation_id"] = correlation_id
                    phase_task_data["previous_results"] = {k: v for k, v in findings.items()}

                    # Quick tier: skip ci-scout when competitors are already provided
                    # (from find_competitors in PRESALE Step 4). Apify takes 30-60s.
                    has_named_competitors = bool(task_data.get("competitors", []))
                    if phase_num == 1 and (len(competitors_list) <= 1 or has_named_competitors):
                        findings["phase_1"] = {
                            "phase": 1, "agent": "ci-scout", "status": "skipped",
                            "result": {"top_for_analysis": task_data.get("competitors", []), "competitors_found": len(task_data.get("competitors", [])),
                                       "reason": "competitors_provided_skip_scout"}
                        }
                        continue

                    # Phase 1 uses initial URLs, phase 2+ uses results from phase 1
                    if phase_num == 1:
                        phase_task_data["competitors"] = competitors_list
                    else:
                        if "phase_1" in findings and "result" in findings["phase_1"]:
                            phase1_result = findings["phase_1"]["result"]
                            top = phase1_result.get("top_for_analysis", [])
                            if top:
                                # Normalize: bare URL strings → competitor dicts
                                if isinstance(top[0], str):
                                    phase_task_data["competitors"] = [
                                        {"name": _extract_name_from_url(u), "url": u} for u in top
                                    ]
                                else:
                                    phase_task_data["competitors"] = top
                            else:
                                phase_task_data["competitors"] = [
                                    {"name": _extract_name_from_url(url), "url": url} for url in competitors_list
                                ]
                        else:
                            phase_task_data["competitors"] = [
                                {"name": _extract_name_from_url(url), "url": url} for url in competitors_list
                            ]

                    if isinstance(agent_names, list):
                        phase_result = await self._execute_parallel_phase(
                            phase_num, agent_names, phase_task_data,
                            timeout=self._phase_timeouts.get(phase_num, 60.0), direct=True
                        )
                    else:
                        phase_result = await self._execute_single_phase(
                            phase_num, agent_names, phase_task_data,
                            timeout=self._phase_timeouts.get(phase_num, 60.0), direct=True
                        )

                    findings[f"phase_{phase_num}"] = phase_result
                except Exception as e:
                    errors.append(f"Phase {phase_num} failed: {str(e)}")

            execution_time = (datetime.now() - start_time).total_seconds()
            quality_score = self._calculate_quality_score(findings, phases)

            # Count actual competitors (quick tier: from phase 2+ data, since phase 1 is often skipped)
            actual_competitors = _count_actual_competitors(findings, task_data)

            reports = await self._generate_reports(task_id, findings, task_data)

            summary = {
                "tier": tier,
                "phases_executed": len(phases),
                "execution_time_seconds": int(execution_time),
                "competitors_analyzed": actual_competitors,
                "quality_score": quality_score,
                "errors_count": len(errors),
            }

            await self.event_bus.publish(Event(
                event_type="ci.execution.completed",
                payload={
                    "correlation_id": correlation_id,
                    "task_id": task_id,
                    "summary": summary,
                }
            ))

            # Build presale-friendly fields from findings
            presale = self._build_quick_summary(findings, task_data)

            return {
                "task_id": task_id,
                "tier": tier,
                "phases_executed": phases,
                "execution_time_seconds": int(execution_time),
                "competitors_analyzed": actual_competitors,
                "findings": findings,
                "reports": reports,
                "quality_score": quality_score,
                "errors": errors,
                "correlation_id": correlation_id,
                **presale,
            }

        except Exception as e:
            return {
                "task_id": task_id,
                "tier": tier,
                "phases_executed": [],
                "execution_time_seconds": 0,
                "competitors_analyzed": 0,
                "findings": {},
                "reports": {},
                "errors": [f"Quick CI analysis failed: {str(e)}"],
            }

    def _build_quick_summary(
        self,
        findings: Dict[str, Any],
        task_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build presale-friendly summary fields from phase findings.

        Produces a rich narrative structure (not a template string) so Hermes
        can tell a compelling human story with concrete discoveries, not just
        recite numbers.

        Returns: narrative, chat_summary, feature_matrix, wow, pricing_comparison,
        positioning_map, competitive_highlights, steal_worthy_tactics, top_recommendation.
        """
        niche = task_data.get("niche", "medical")
        geo = task_data.get("geo", "")
        competitors = task_data.get("competitors", [])

        # ── Extract data from all phases ──
        phase1 = findings.get("phase_1", {})
        scout_result = phase1.get("result", {}) if isinstance(phase1, dict) else {}
        top_competitors = scout_result.get("top_for_analysis", []) if isinstance(scout_result, dict) else []

        phase2 = findings.get("phase_2", {})
        auditor_result = phase2.get("result", {}) if isinstance(phase2, dict) else {}

        phase4 = findings.get("phase_4", {})
        rep_result = phase4.get("result", {}) if isinstance(phase4, dict) else {}

        phase5 = findings.get("phase_5", {})
        phase5_results = phase5.get("results", {}) if isinstance(phase5, dict) else {}

        pricing_agent = phase5_results.get("ci-pricing", {})
        pricing_result = pricing_agent.get("result", {}) if isinstance(pricing_agent, dict) else {}

        tech_agent = phase5_results.get("ci-tech", {})
        tech_result = tech_agent.get("result", {}) if isinstance(tech_agent, dict) else {}

        content_agent = phase5_results.get("ci-content", {})
        content_result = content_agent.get("result", {}) if isinstance(content_agent, dict) else {}

        vacancies_agent = phase5_results.get("ci-vacancies", {})
        vacancies_result = vacancies_agent.get("result", {}) if isinstance(vacancies_agent, dict) else {}

        finance_agent = phase5_results.get("ci-finance", {})
        finance_result = finance_agent.get("result", {}) if isinstance(finance_agent, dict) else {}

        ecosystem_agent = phase5_results.get("ci-ecosystem", {})
        ecosystem_result = ecosystem_agent.get("result", {}) if isinstance(ecosystem_agent, dict) else {}

        phase7 = findings.get("phase_7", {})
        strategy_result = phase7.get("result", {}) if isinstance(phase7, dict) else {}

        phase9 = findings.get("phase_9", {})
        prioritizer_result = phase9.get("result", {}) if isinstance(phase9, dict) else {}

        # ── WOW numbers ──
        wow = _compute_wow_from_findings(findings)

        # ── Competitor count ──
        comp_list = top_competitors if top_competitors else competitors
        competitor_count = len(comp_list)

        # ── Build rich feature matrix ──
        feature_matrix = {}
        for c in comp_list:
            name = c.get("name", c) if isinstance(c, dict) else str(c)
            url = c.get("url", c) if isinstance(c, dict) else str(c)
            seo_score = _extract_auditor_seo_score(auditor_result, url)
            rep_rating = _extract_reputation_rating(rep_result, name)
            # Fallback: use rating from find_competitors if reputation phase failed
            if rep_rating is None and isinstance(c, dict):
                rep_rating = c.get("rating")
            has_pricing = _has_pricing_data_from_agent(pricing_result, name)
            has_booking = _has_online_booking(auditor_result)

            # Human-readable SEO interpretation
            seo_label = "не проверен"
            if isinstance(seo_score, (int, float)):
                if seo_score >= 80:
                    seo_label = "отличный уровень — сайт хорошо находят в поиске"
                elif seo_score >= 60:
                    seo_label = "нормальный уровень — можно улучшить"
                elif seo_score >= 40:
                    seo_label = "ниже среднего — есть над чем работать"
                else:
                    seo_label = "слабый — нужно серьёзно улучшать"

            # Human-readable reputation
            rep_label = "нет данных"
            if isinstance(rep_rating, (int, float)) and rep_rating > 0:
                if rep_rating >= 4.5:
                    rep_label = f"отличная репутация ({rep_rating}★)"
                elif rep_rating >= 4.0:
                    rep_label = f"хорошая репутация ({rep_rating}★)"
                elif rep_rating >= 3.0:
                    rep_label = f"средняя репутация ({rep_rating}★)"
                else:
                    rep_label = f"слабая репутация ({rep_rating}★)"

            feature_matrix[name] = {
                "url": url,
                "seo_score": seo_score,
                "seo_label": seo_label,
                "rating": rep_rating,
                "reputation_label": rep_label,
                "pricing_visible": has_pricing,
                "online_booking": has_booking,
            }

        # ── Build rich pricing comparison ──
        pricing_comparison = {}
        pricing_profiles = pricing_result.get("pricing_profiles", []) if isinstance(pricing_result, dict) else []

        # Fallback: extract price hints from auditor HTML scraping (quick tier)
        auditor_hints = {}
        if not pricing_profiles:
            auditor_audits = auditor_result.get("audits", [])
            for audit in auditor_audits:
                if not isinstance(audit, dict):
                    continue
                audit_name = audit.get("name", audit.get("url", ""))
                for dim_data in audit.get("dimensions", {}).values():
                    if isinstance(dim_data, dict) and "_pricing_hints" in dim_data:
                        auditor_hints[audit_name] = dim_data["_pricing_hints"]
                        break

        for c in comp_list:
            name = c.get("name", c) if isinstance(c, dict) else str(c)
            prices = _extract_prices_from_agent(pricing_profiles, name)
            primary = prices.get("primary_consult")
            popular = prices.get("popular_service")

            # Use auditor HTML price hints as fallback
            if primary is None and name in auditor_hints:
                hints = auditor_hints[name]
                hint_min = hints.get("price_range_min")
                hint_max = hints.get("price_range_max")
                if hint_min and hint_max:
                    primary = hint_min
                    popular = hint_max

            pricing_comparison[name] = {
                "primary_consult": primary,
                "popular_service": popular,
                "price_positioning": _classify_price_positioning(primary, pricing_profiles),
            }

        # ── Competitive highlights (surprising/interesting findings) ──
        highlights = _extract_competitive_highlights(findings, comp_list)

        # ── Positioning map ──
        competitive_intensity = "unknown"
        if competitor_count >= 10:
            competitive_intensity = "высокая"
        elif competitor_count >= 4:
            competitive_intensity = "средняя"
        elif competitor_count >= 1:
            competitive_intensity = "низкая"

        digital_maturity = "unknown"
        seo_score_val = _extract_auditor_seo_score(auditor_result)
        if isinstance(seo_score_val, (int, float)):
            if seo_score_val >= 80:
                digital_maturity = "высокая"
            elif seo_score_val >= 50:
                digital_maturity = "средняя"
            else:
                digital_maturity = "низкая"

        positioning_map = {
            "competitive_intensity": competitive_intensity,
            "digital_maturity": digital_maturity,
            "market_size": "средний" if competitor_count >= 5 else "небольшой",
            "readable": (
                f"Рынок {niche} {f'в {geo}' if geo else ''}: "
                f"конкуренция {competitive_intensity}, "
                f"уровень диджитализации {digital_maturity}. "
                f"Найдено {competitor_count} конкурентов."
            ),
        }

        # ── Build rich narrative ──
        # Extract reputation data for top competitors
        rep_scores = rep_result.get("reputation_scores", []) if isinstance(rep_result, dict) else []
        top_rated = _top_n_by(rep_scores, "avg_rating", 3) if rep_scores else []
        most_reviewed = _top_n_by(rep_scores, "total_reviews", 3) if rep_scores else []

        # Extract vacancy data
        vacancy_profiles = vacancies_result.get("vacancy_profiles", []) if isinstance(vacancies_result, dict) else []
        hiring_leaders = [vp for vp in vacancy_profiles if (vp.get("open_vacancies") or 0) >= 5]
        hiring_leaders.sort(key=lambda x: x.get("open_vacancies") or 0, reverse=True)

        # Extract finance data
        finance_profiles = finance_result.get("financial_profiles", []) if isinstance(finance_result, dict) else []
        revenue_leaders = sorted(
            [fp for fp in finance_profiles if fp.get("revenue_year")],
            key=lambda x: x.get("revenue_year", 0), reverse=True
        )[:3]

        # Extract ecosystem data
        ecosystem_profiles = ecosystem_result.get("ecosystem_profiles", []) if isinstance(ecosystem_result, dict) else []

        # Extract content insights
        content_profiles = content_result.get("content_profiles", []) if isinstance(content_result, dict) else []

        # Extract tech insights
        tech_profiles = tech_result.get("tech_profiles", []) if isinstance(tech_result, dict) else []

        # Build narrative structure
        patients_str = f"~{wow.get('patients_per_month', '?')}" if wow.get('patients_per_month') else "?"
        time_str = f"{wow.get('time_to_result_weeks', '?')}" if wow.get('time_to_result_weeks') else "?"

        # Opening hook
        opening = (
            f"Проанализировал рынок {niche} {f'в {geo}' if geo else ''}. "
            f"Нашёл {competitor_count} конкурентов. "
        )
        if competitive_intensity == "высокая":
            opening += "Рынок конкурентный, но это хороший знак — значит есть спрос и деньги."
        elif competitive_intensity == "средняя":
            opening += "Конкуренция умеренная — хорошее окно возможностей для усиления."
        else:
            opening += "Конкуренция низкая — можно занять лидирующую позицию."

        # Key findings as bullet-point observations
        key_findings = []
        for h in highlights[:5]:
            key_findings.append(h)

        if top_rated:
            best = top_rated[0]
            key_findings.append(
                f"Лучшая репутация у «{best.get('name', '?')}» — "
                f"{best.get('avg_rating', '?')}★ на основе {best.get('total_reviews', '?')} отзывов"
            )

        if hiring_leaders:
            hl = hiring_leaders[0]
            key_findings.append(
                f"«{hl.get('name', '?')}» активно нанимает — {hl.get('open_vacancies', '?')} открытых вакансий. "
                f"Это признак роста бизнеса."
            )

        if revenue_leaders:
            rl = revenue_leaders[0]
            rev = rl.get("revenue_year")
            if rev and rev > 0:
                rev_str = f"{rev/1_000_000:.1f} млн ₽" if rev >= 1_000_000 else f"{rev:,.0f} ₽".replace(",", " ")
                key_findings.append(
                    f"Крупнейший игрок по выручке — «{rl.get('name', '?')}»: {rev_str} в год"
                )

        # Digital gaps
        if digital_maturity in ("низкая", "средняя"):
            key_findings.append(
                f"Уровень диджитализации рынка — {digital_maturity}. "
                f"Большинство конкурентов слабо представлены в интернете — это ваш шанс вырваться вперёд."
            )

        # Unexpected finding
        unexpected = None
        # Find competitor with best rating but low SEO (great offline, weak online)
        for rep_item in rep_scores:
            name = rep_item.get("name", "")
            if (rep_item.get("avg_rating") or 0) >= 4.5:
                seo = _extract_auditor_seo_score(auditor_result, name if isinstance(name, str) else "")
                if isinstance(seo, (int, float)) and seo < 60:
                    unexpected = (
                        f"У «{name}» отличная репутация ({rep_item.get('avg_rating')}★, "
                        f"{rep_item.get('total_reviews', '?')} отзывов), но сайт практически невидим в поиске. "
                        f"При правильном продвижении их пациенты могут стать вашими."
                    )
                    break
        if not unexpected and highlights:
            unexpected = highlights[0] if highlights else None

        # Client potential
        if patients_str != "?":
            potential = (
                f"Ваш потенциал — {patients_str} пациентов в месяц. "
                f"Первые результаты через {time_str} недель активного продвижения. "
            )
            if revenue_leaders:
                avg_rev = sum(
                    fp.get("revenue_year", 0) for fp in revenue_leaders if fp.get("revenue_year")
                ) / max(len([fp for fp in revenue_leaders if fp.get("revenue_year")]), 1)
                if avg_rev > 0:
                    potential += f"Ориентир по выручке — конкуренты делают в среднем {avg_rev/1_000_000:.1f} млн ₽ в год."
        else:
            potential = "Нужно больше данных для точной оценки потенциала."

        # Narrative as dict (Hermes can assemble into natural speech)
        narrative = {
            "opening": opening,
            "key_findings": key_findings,
            "unexpected_finding": unexpected,
            "client_potential": potential,
        }

        # ── Rich chat_summary (not a template string anymore) ──
        geo_str = f"в {geo}" if geo else ""
        summary_parts = [
            f"Аудит рынка {niche} {geo_str}".strip(),
            f"Найдено {competitor_count} конкурентов",
            f"Интенсивность конкуренции: {competitive_intensity}",
            f"Уровень диджитализации: {digital_maturity}",
        ]
        if patients_str != "?":
            summary_parts.append(f"Потенциал: {patients_str} пациентов/мес (первые результаты — {time_str} нед.)")
        if highlights:
            summary_parts.append(f"Главная находка: {highlights[0][:200]}")
        chat_summary = ". ".join(summary_parts) + "."

        # ── Steal-worthy tactics ──
        steal_worthy = _extract_steal_worthy_tactics(findings)

        # ── Top recommendation ──
        top_rec = _extract_top_recommendation(findings, feature_matrix)

        return {
            "narrative": narrative,
            "chat_summary": chat_summary,
            "feature_matrix": feature_matrix,
            "pricing_comparison": pricing_comparison,
            "positioning_map": positioning_map,
            "competitive_highlights": highlights,
            "steal_worthy_tactics": steal_worthy,
            "top_recommendation": top_rec,
            "wow": wow,
        }

    async def _execute_single_phase(
        self,
        phase_num: int,
        agent_name: str,
        task_data: Dict[str, Any],
        timeout: float = 60.0,
        direct: bool = False,
    ) -> Dict[str, Any]:
        """Execute single agent phase.

        With direct=True (quick tier): calls agent.receive_task() directly,
        bypassing EventBus message polling. Faster and more reliable.

        With direct=False (deep/full tier): publishes task.request Message and
        waits for ci.agent.completed Event via EventBus delegation.

        timeout: max wait for agent completion.
        """
        agent = await self._get_agent(agent_name)

        if agent is None:
            # Agent not implemented - return stub result
            logger.warning(f"Agent {agent_name} not implemented, using stub")
            await asyncio.sleep(0.1)
            return {
                "phase": phase_num,
                "agent": agent_name,
                "status": "stub",
                "message": f"Agent {agent_name} not implemented yet"
            }

        # Create Task for agent
        from meai.agents.base_agent import Task, TaskStatus
        task = Task(
            task_id=f"{task_data.get('task_id', 'unknown')}-phase-{phase_num}",
            subtask_id=f"phase-{phase_num}",
            parent_task_id=task_data.get("task_id", "unknown"),
            action="analyze",
            description=f"Phase {phase_num}: {agent_name}",
            priority=1,
            status=TaskStatus.RECEIVED,
            created_at=datetime.now(timezone.utc),
            received_at=datetime.now(timezone.utc)
        )

        # Set task payload
        prev = task_data.get("previous_results", {})
        task.payload = {
            "niche": task_data.get("niche", ""),
            "geo": task_data.get("geo", ""),
            "target_audience": task_data.get("target_audience", ""),
            "price_segment": task_data.get("price_segment", "mid"),
            "competitors": task_data.get("competitors", []),
            "our_url": task_data.get("our_url", ""),
            "url": task_data.get("url", ""),
            "previous_results": prev,
        }
        logger.info(
            "Phase %d (%s): previous_results has %d keys: %s",
            phase_num, agent_name, len(prev), list(prev.keys()),
        )

        correlation_id = task_data.get("correlation_id", task_data.get("task_id", "unknown"))
        phase_correlation = f"{correlation_id}-{phase_num}"

        # Set correlation_id on agent so the bridged report_result can use it
        agent._ci_correlation_id = phase_correlation

        # ── Direct execution (bypasses EventBus poll loop) ──
        if direct:
            logger.info(
                "Direct execution: %s phase %d (timeout=%.0fs)",
                agent_name, phase_num, timeout,
            )
            try:
                await asyncio.wait_for(agent.receive_task(task), timeout=timeout)
                # Bridged report_result published ci.agent.completed → stored in _completed_results
                # Key format: "{phase_correlation}:{agent_name}" (set by _on_agent_completed)
                expected_key = f"{phase_correlation}:{agent_name}"
                val = self._completed_results.get(expected_key)
                if val:
                    return {
                        "phase": phase_num,
                        "agent": agent_name,
                        "status": val.get("status", "completed"),
                        "result": val.get("result", {}),
                    }
                # Fallback: task completed but no event captured
                logger.warning(
                    "Direct execution for %s phase %d: no result in _completed_results (key=%s)",
                    agent_name, phase_num, expected_key,
                )
                return {
                    "phase": phase_num,
                    "agent": agent_name,
                    "status": "completed_no_event",
                    "result": {},
                }
            except asyncio.TimeoutError:
                logger.warning(
                    "Direct execution timeout for %s phase %d after %.0fs",
                    agent_name, phase_num, timeout,
                )
                return {
                    "phase": phase_num,
                    "agent": agent_name,
                    "status": "timeout",
                    "error": f"Agent {agent_name} did not complete within {timeout:.0f}s",
                    "result": {},
                }
            except Exception as e:
                logger.error(
                    "Direct execution failed for %s phase %d: %s",
                    agent_name, phase_num, e,
                )
                return {
                    "phase": phase_num,
                    "agent": agent_name,
                    "status": "failed",
                    "error": str(e)[:200],
                    "result": {},
                }

        # ── Deep/full tier: EventBus delegation ──
        # Publish audit trail event
        await self.event_bus.publish(Event(
            event_type="ci.task.dispatched",
            payload={
                "correlation_id": phase_correlation,
                "agent": agent_name,
                "phase": phase_num,
                "task_action": "analyze",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ))

        # Publish task.request Message targeting the agent (EventBus delegation)
        await self.event_bus.publish(Message(
            from_agent=self.agent_id,
            to_agent=agent.agent_id,
            message_type="task.request",
            priority=1,
            payload={
                "correlation_id": phase_correlation,
                "task": {
                    "task_id": task.task_id,
                    "subtask_id": task.subtask_id,
                    "parent_task_id": task.parent_task_id,
                    "action": task.action,
                    "description": task.description,
                    "priority": task.priority,
                    "payload": task.payload,
                    "data": {"correlation_id": phase_correlation},
                },
            },
            timestamp=datetime.now(timezone.utc),
        ))

        # Wait for agent to complete via dict-based phase pending.
        # _on_agent_completed signals the Event (single persistent subscriber),
        # avoiding N transient subscribers during parallel phase execution.
        completion_event = asyncio.Event()
        completion_result: Dict[str, Any] = {}

        self._phase_pending[phase_correlation] = completion_event

        try:
            await asyncio.wait_for(completion_event.wait(), timeout=timeout)
            # Retrieve matching result from _completed_results
            for key, val in self._completed_results.items():
                if key.startswith(phase_correlation):
                    completion_result.update(val)
                    break
            return {
                "phase": phase_num,
                "agent": agent_name,
                "status": completion_result.get("status", "completed"),
                "result": completion_result.get("result", {}),
            }
        except asyncio.TimeoutError:
            logger.warning(
                "EventBus delegation timeout for %s phase %d after %.0fs",
                agent_name, phase_num, timeout,
            )
            return {
                "phase": phase_num,
                "agent": agent_name,
                "status": "timeout",
                "error": f"Agent {agent_name} did not complete within {timeout:.0f}s",
                "result": {},
            }
        finally:
            self._phase_pending.pop(phase_correlation, None)

    async def _execute_parallel_phase(
        self,
        phase_num: int,
        agent_names: List[str],
        task_data: Dict[str, Any],
        timeout: float = 60.0,
        direct: bool = False,
    ) -> Dict[str, Any]:
        """Execute multiple agents in parallel (Phase 5)"""
        tasks = []

        for agent_name in agent_names:
            tasks.append(self._execute_single_phase(phase_num, agent_name, task_data, timeout=timeout, direct=direct))

        # Execute in parallel with error handling
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect results
        agent_results = {}
        errors = []
        success_count = 0
        fail_count = 0

        for i, result in enumerate(results):
            agent_name = agent_names[i]
            if isinstance(result, Exception):
                errors.append(f"{agent_name}: {str(result)}")
                agent_results[agent_name] = {"status": "failed", "error": str(result)}
                fail_count += 1
            else:
                agent_results[agent_name] = result
                agent_status = result.get("status", "unknown")
                if agent_status in ("success", "completed"):
                    success_count += 1
                elif agent_status in ("failed", "timeout", "stub", "completed_no_event"):
                    fail_count += 1
                    errors.append(f"{agent_name}: {agent_status}")

        # Determine overall status based on individual agent statuses
        if fail_count == len(agent_names):
            parallel_status = "failed"
        elif success_count == len(agent_names):
            parallel_status = "success"
        else:
            parallel_status = "partial"

        return {
            "phase": phase_num,
            "parallel": True,
            "agents": agent_names,
            "results": agent_results,
            "errors": errors,
            "status": parallel_status
        }

    def _calculate_quality_score(
        self,
        findings: Dict[str, Any],
        phases_executed: List[int]
    ) -> Dict[str, Any]:
        """Calculate quality score for CI analysis results"""

        # Count successful phases
        successful_phases = 0
        partial_phases = 0
        failed_phases = 0

        for phase_key, phase_data in findings.items():
            status = phase_data.get("status", "unknown")
            if status == "success":
                successful_phases += 1
            elif status == "partial":
                partial_phases += 1
            elif status == "failed" or status == "stub":
                failed_phases += 1

        total_phases = len(phases_executed)

        # Calculate completeness (0-100) — partial phases count as half
        effective_successes = successful_phases + (partial_phases * 0.5)
        completeness = int((effective_successes / total_phases * 100)) if total_phases > 0 else 0

        # Calculate confidence level
        if completeness >= 90:
            confidence = "high"
        elif completeness >= 70:
            confidence = "medium"
        else:
            confidence = "low"

        # Overall quality score (0-100)
        quality_score = completeness

        return {
            "score": quality_score,
            "confidence": confidence,
            "completeness": completeness,
            "successful_phases": successful_phases,
            "partial_phases": partial_phases,
            "failed_phases": failed_phases,
            "total_phases": total_phases
        }

    async def _generate_reports(
        self,
        task_id: str,
        findings: Dict[str, Any],
        task_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate simple HTML/JSON reports from CI findings"""
        logger.info(f"Starting report generation for task {task_id}")

        try:
            # Generate reports directory (absolute path from module location)
            reports_dir = Path(__file__).resolve().parents[5] / "reports" / task_id
            reports_dir.mkdir(parents=True, exist_ok=True)

            # Generate simple HTML report
            html_path = reports_dir / "report.html"
            html_content = self._generate_simple_html(task_id, findings, task_data)
            html_path.write_text(html_content, encoding='utf-8')
            logger.info(f"HTML report generated: {html_path}")

            # Generate JSON report
            json_path = reports_dir / "report.json"
            json_content = {
                "task_id": task_id,
                "niche": task_data.get("niche", ""),
                "geo": task_data.get("geo", ""),
                "tier": task_data.get("tier", ""),
                "analysis_date": datetime.now(timezone.utc).isoformat(),
                "competitors": task_data.get("competitors", []),
                "findings": findings
            }
            json_path.write_text(json.dumps(json_content, indent=2, ensure_ascii=False), encoding='utf-8')
            logger.info(f"JSON report generated: {json_path}")

            result = {
                "html_path": str(html_path),
                "json_path": str(json_path)
            }
            logger.info(f"Report generation complete: {result}")
            return result

        except Exception as e:
            logger.error(f"Report generation failed: {e}", exc_info=True)
            return {}

    def _generate_simple_html(
        self,
        task_id: str,
        findings: Dict[str, Any],
        task_data: Dict[str, Any]
    ) -> str:
        """Generate simple HTML report"""
        niche = task_data.get("niche", "Unknown")
        geo = task_data.get("geo", "Unknown")
        tier = task_data.get("tier", "unknown")
        competitors = task_data.get("competitors", [])

        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CI Analysis Report - {task_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .meta {{ background: #f9f9f9; padding: 15px; border-radius: 4px; margin: 20px 0; }}
        .meta p {{ margin: 5px 0; }}
        .phase {{ background: #fff; border-left: 4px solid #2196F3; padding: 15px; margin: 15px 0; }}
        .phase h3 {{ margin-top: 0; color: #2196F3; }}
        .success {{ color: #4CAF50; }}
        .failed {{ color: #f44336; }}
        pre {{ background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Competitive Intelligence Analysis</h1>

        <div class="meta">
            <p><strong>Task ID:</strong> {task_id}</p>
            <p><strong>Niche:</strong> {niche}</p>
            <p><strong>Geo:</strong> {geo}</p>
            <p><strong>Tier:</strong> {tier.upper()}</p>
            <p><strong>Competitors:</strong> {len(competitors)}</p>
            <p><strong>Date:</strong> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        </div>

        <h2>📊 Analysis Results</h2>
"""

        # Add findings for each phase
        for phase_key, phase_data in findings.items():
            phase_num = phase_key.replace("phase_", "")
            agent_name = phase_data.get("agent", "unknown")
            status = phase_data.get("status", "unknown")
            status_class = "success" if status == "success" else "failed"

            html += f"""
        <div class="phase">
            <h3>Phase {phase_num}: {agent_name}</h3>
            <p><strong>Status:</strong> <span class="{status_class}">{status}</span></p>
"""

            # Add result summary if available
            if "result" in phase_data and isinstance(phase_data["result"], dict):
                result = phase_data["result"]
                if "total_found" in result:
                    html += f"<p><strong>Total Found:</strong> {result['total_found']}</p>"
                if "top_selected" in result:
                    html += f"<p><strong>Top Selected:</strong> {result['top_selected']}</p>"

            html += "        </div>\n"

        html += """
        <h2>📄 Full Data</h2>
        <p>Complete analysis data is available in the JSON report.</p>
    </div>
</body>
</html>
"""
        return html

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute CI analysis task via execute_ci_analysis (Agent interface).

        Extracts analysis parameters from task payload and delegates to the
        unified execute_ci_analysis() path. The old _execute_phases →
        _delegate_to_agent stub chain has been removed — EventBus delegation
        is the ONLY execution path.
        """
        try:
            await self._log_start(task)

            tier = self._detect_tier(task.payload)
            await self._check_stale_data()

            task_data = {
                "task_id": task.task_id,
                "niche": task.payload.get("niche", ""),
                "geo": task.payload.get("geo", ""),
                "tier": tier,
                "competitors": task.payload.get("competitors", []),
                "target_audience": task.payload.get("target_audience", ""),
                "price_segment": task.payload.get("price_segment", "mid"),
            }
            result = await self.execute_ci_analysis(task_data)

            # Log completion using new result structure
            phases_executed = result.get("phases_executed", [])
            logger.info(
                "Завершена задача %s: %d фаз выполнено",
                task.task_id, len(phases_executed),
            )
            state = {
                "last_run": datetime.now().isoformat(),
                "last_task_id": task.task_id,
                "last_tier": tier,
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)

            return TaskResult(
                task_id=task.task_id,
                status="completed" if not result.get("errors") else "failed",
                result=result,
            )

        except Exception as e:
            await self._log_error(task, str(e))
            return TaskResult(
                task_id=task.task_id,
                status="failed",
                result={"error": str(e)}
            )

    def _detect_tier(self, payload: Dict[str, Any]) -> str:
        """
        Определить tier анализа из payload.

        Tier 1 (quick): "быстрый анализ", "посмотри", "кто конкуренты"
        Tier 2 (deep): default для большинства запросов
        Tier 3 (full): "полный", "всё", "коммерческое", "предложение"
        """
        depth = payload.get("depth", "").lower()
        request = payload.get("request", "").lower()

        # Explicit depth
        if depth in ["quick", "deep", "full"]:
            return depth

        # Detect from request
        quick_keywords = ["быстрый", "посмотри", "кто конкуренты", "обзор"]
        full_keywords = ["полный", "всё", "коммерческое", "предложение", "ceo", "pitch"]

        if any(kw in request for kw in quick_keywords):
            return "quick"
        elif any(kw in request for kw in full_keywords):
            return "full"
        else:
            return "deep"  # default

    async def _check_stale_data(self):
        """
        Проверить актуальность данных.

        Если последний анализ > 30 дней → предупреждение
        Если > 60 дней → рекомендация пересканировать фазы 1-5
        Если > 90 дней → рекомендация полного пересканирования
        """
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)

            last_run = state.get("last_run")
            if not last_run:
                return

            last_date = datetime.fromisoformat(last_run)
            days_ago = (datetime.now() - last_date).days

            if days_ago > 90:
                await self.vault.log_operation(
                    "stale_data_warning",
                    f"⚠️ Данные устарели ({days_ago} дней). Рекомендуется полный пересканирование."
                )
            elif days_ago > 60:
                await self.vault.log_operation(
                    "stale_data_warning",
                    f"⚠️ Данные устарели ({days_ago} дней). Рекомендуется пересканировать фазы 1-5."
                )
            elif days_ago > 30:
                await self.vault.log_operation(
                    "stale_data_warning",
                    f"⚠️ Данные могут быть устаревшими ({days_ago} дней)."
                )
        except FileNotFoundError:
            # Первый запуск
            pass

    async def _log_start(self, task: Task):
        """Логировать начало выполнения задачи."""
        await self.vault.log_operation(
            "task_start",
            f"Начало задачи {task.id}: {task.payload.get('niche')} в {task.payload.get('geo')}"
        )

    async def _log_completion(self, task: Task, results: Dict[str, Any]):
        """Логировать завершение задачи."""
        await self.vault.log_operation(
            "task_complete",
            f"Завершена задача {task.id}: {len(results['phases_executed'])} фаз выполнено"
        )

        # Обновить state file
        state = {
            "last_run": datetime.now().isoformat(),
            "last_task_id": task.id,
            "last_tier": results["tier"]
        }

        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

    async def _log_error(self, task: Task, error: str):
        """Логировать ошибку."""
        await self.vault.log_operation(
            "task_error",
            f"Ошибка в задаче {task.id}: {error}"
        )

    # ── Phase 21: Matrix-based analysis methods ───────────────────────
    # These methods operate on ComparisonMatrix-like objects (used by tests
    # and the CiMarketingAnalyzer proxy) to extract tactics, SWOT, recommendations,
    # and generate human-readable analysis summaries.

    def _extract_tactics_from_matrix(self, matrix) -> List["StealWorthyTactic"]:
        """Extract steal-worthy tactics from a comparison matrix.

        Analyzes competitor features, SEO scores, pricing visibility, and website
        gaps to produce actionable tactical recommendations sorted by impact.
        """
        from src.aim.services.ci.models import StealWorthyTactic
        from src.aim.services.ci_marketing_analysis import _tactic_impact_effort

        comps = getattr(matrix, "competitors", [])

        if not comps:
            return []

        tactics: List[StealWorthyTactic] = []
        client_features = getattr(matrix, "client", {}).get("features", [])
        client_feat_set = set((f or "").lower() for f in client_features)

        for comp in comps:
            name = str(comp.get("name", "Конкурент"))
            website = comp.get("website", {}) or {}
            features = website.get("features", []) or []

            # Feature-based tactics from competitors
            for feat in features[:3]:
                impact, effort = _tactic_impact_effort(feat)
                tactics.append(StealWorthyTactic(
                    source_competitor=name,
                    tactic_description=f"Внедрить «{feat}» как у {name}",
                    why_it_works=f"{name} использует «{feat}» для привлечения пациентов",
                    expected_impact=impact,
                    estimated_effort=effort,
                ))

            # Website gaps — features client is missing
            missing = website.get("missing", []) or []
            for feat in features:
                if (feat or "").lower() not in client_feat_set:
                    tactics.append(StealWorthyTactic(
                        source_competitor=name,
                        tactic_description=f"Добавить «{feat}» — есть у {name}",
                        why_it_works=f"Пациенты ожидают «{feat}» — {name} уже предлагает это",
                        expected_impact="High",
                        estimated_effort="Medium",
                    ))

            # Pricing transparency — competitor hides prices
            if website.get("pricing_visible") is False:
                tactics.append(StealWorthyTactic(
                    source_competitor=name,
                    tactic_description="Прозрачные цены на сайте",
                    why_it_works=f"{name} не показывает цены, клиенты ищут прозрачность",
                    expected_impact="High",
                    estimated_effort="Low",
                ))

        # SEO exploit — target competitor with weakest SEO
        scored = [(c.get("seo", {}).get("score", 100) or 100, c) for c in comps]
        if scored:
            worst_score, worst_comp = min(scored, key=lambda x: x[0])
            if worst_score < 60:
                name = worst_comp.get("name", "конкурент")
                tactics.append(StealWorthyTactic(
                    source_competitor=name,
                    tactic_description=f"SEO-оптимизация — обойти {name} в поиске",
                    why_it_works=f"У {name} слабое SEO ({worst_score}/100)",
                    expected_impact="High",
                    estimated_effort="Medium",
                ))

        # Deduplicate by tactic_description
        seen: set[str] = set()
        uniq: List[StealWorthyTactic] = []
        for t in tactics:
            key = t.tactic_description
            if key not in seen:
                seen.add(key)
                uniq.append(t)

        # Sort by impact: High → Medium → Low
        impact_order = {"High": 0, "Medium": 1, "Low": 2}
        uniq.sort(key=lambda t: impact_order.get(t.expected_impact, 2))

        return uniq[:8]

    def _extract_swot_from_matrix(self, matrix) -> dict:
        """Build SWOT analysis dict from comparison matrix data."""

        comps = getattr(matrix, "competitors", [])

        if not comps:
            return {
                "strengths": [
                    "Вы лучше знаете локальный рынок",
                    "Индивидуальный подход к пациентам",
                    "Гибкость в принятии решений",
                ],
                "weaknesses": [
                    "Ограниченный бюджет на маркетинг",
                    "Меньше узнаваемость чем у конкурентов",
                ],
                "opportunities": [
                    "Растущий спрос на медицинские услуги",
                    "Возможность привлечь пациентов через онлайн",
                ],
                "threats": [
                    "Конкуренты могут усилить рекламу",
                    "Изменения в законодательстве",
                ],
            }

        strengths: list[str] = []
        weaknesses: list[str] = []
        opportunities: list[str] = []
        threats: list[str] = []

        for comp in comps:
            name = str(comp.get("name", "Конкурент"))
            seo = comp.get("seo", {}) or {}
            website = comp.get("website", {}) or {}
            social = comp.get("social", {}) or {}
            financials = comp.get("financials", {}) or {}

            seo_score = seo.get("score", 100) or 100
            seo_issues = seo.get("issues", []) or []

            # Strengths — competitor weaknesses we can exploit
            if seo_score < 70:
                strengths.append(f"Слабое SEO у {name} — возможность обойти в поиске")
            features = website.get("features", []) or []
            if features:
                strengths.append(f"Можно перенять фишки сайта {name}: {', '.join(features[:3])}")
            doctors = comp.get("doctors", []) or []
            if doctors:
                strengths.append(f"Команда врачей у {name} — можно привлечь похожих специалистов")

            # Weaknesses — competitor strengths to watch out for
            if seo_score >= 80:
                weaknesses.append(f"Сильное SEO у {name} ({seo_score}/100) — трудно обойти")
            rev = financials.get("latest_revenue")
            if rev and rev > 30_000_000:
                weaknesses.append(f"{name} имеет значительную выручку ({rev:,.0f} руб)")
            social_platforms = [p for p, v in social.items()
                               if isinstance(v, dict) and v.get("exists")]
            if len(social_platforms) >= 2:
                weaknesses.append(f"{name} активен в соцсетях: {', '.join(social_platforms)}")

            # Opportunities — competitor gaps we can fill
            missing = website.get("missing", []) or []
            if missing:
                opportunities.append(f"{name} не хватает: {', '.join(missing[:3])} — предложите это")
            if website.get("pricing_visible") is False:
                opportunities.append(f"{name} скрывает цены — публикуйте свои")

            # Threats — competitor advantages
            ratings = [r for r in [
                comp.get("gm_rating", 0),
                comp.get("yandex_rating", 0),
                comp.get("prodoctorov_rating", 0),
            ] if r]
            avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
            if avg_rating >= 4.0:
                threats.append(f"Высокий рейтинг {name} ({avg_rating:.1f}) — сильная репутация")
            trend = str(financials.get("trend", ""))
            if "раст" in trend.lower():
                threats.append(f"{name} растёт — усиление конкуренции")

        # Ensure at least 1 item per quadrant
        if not strengths:
            strengths.append("Вы лучше знаете локальный рынок")
        if not weaknesses:
            weaknesses.append("Недостаточно данных для оценки конкурентов")
        if not opportunities:
            opportunities.append("Займите нишу с лучшим сервисом")
        if not threats:
            threats.append("Рынок может измениться — будьте гибкими")

        return {
            "strengths": strengths[:5],
            "weaknesses": weaknesses[:5],
            "opportunities": opportunities[:5],
            "threats": threats[:5],
        }

    def _top_rec_from_matrix(self, matrix) -> str:
        """Return the single most actionable recommendation from a matrix."""

        comps = getattr(matrix, "competitors", [])

        if not comps:
            return "Соберите данные о конкурентах для получения рекомендаций."

        # Target competitor with weakest SEO
        scored = [(c.get("seo", {}).get("score", 100) or 100, c) for c in comps]
        worst_score, worst_comp = min(scored, key=lambda x: x[0])
        name = worst_comp.get("name", "конкурент")

        return (
            f"Главная возможность — обойти **{name}** по SEO: "
            f"у них {worst_score}/100, "
            f"исправьте ошибки которые мы нашли на их сайте, и вы выше."
        )

    def _generate_analysis_summary(
        self,
        matrix,
        swot: dict,
        tactics: list,
        rec: str,
        wow: dict,
    ) -> str:
        """Generate a human-readable analysis summary from matrix + derived data."""

        comps = getattr(matrix, "competitors", [])

        if not comps:
            return "Не удалось найти конкурентов для анализа."

        lines: list[str] = []

        # Overview
        lines.append("Обзор конкурентной среды")
        lines.append(f"Проанализировано {len(comps)} конкурентов.")
        lines.append("")

        # Per competitor
        lines.append("## По конкурентам")
        for comp in comps:
            name = comp.get("name", "Конкурент")
            seo = comp.get("seo", {}) or {}
            lines.append(f"**{name}**: SEO {seo.get('score', '?')}/100")
        lines.append("")

        # SWOT
        lines.append("## SWOT-анализ")
        if swot.get("strengths"):
            lines.append("Сильные стороны: " + ", ".join(swot["strengths"][:3]))
        if swot.get("weaknesses"):
            lines.append("Слабые стороны: " + ", ".join(swot["weaknesses"][:3]))
        lines.append("")

        # Tactics section (only when non-empty)
        if tactics:
            lines.append("## Что можно внедрить")
            for t in tactics[:5]:
                lines.append(f"- {t.tactic_description} ({t.expected_impact} impact, {t.estimated_effort} effort)")
            lines.append("")

        # WOW section (only when wow has patients_per_month)
        if wow and wow.get("patients_per_month"):
            ppm = wow["patients_per_month"]
            ttr = wow.get("time_to_result_weeks", "?")
            lines.append("## Прогноз по пациентам")
            lines.append(f"Ожидаемый прирост: {ppm} пациентов в месяц, результат через {ttr} недель")
            lines.append("")

        # Recommendation
        lines.append("## Главная рекомендация")
        lines.append(rec)

        return "\n".join(lines)

    def get_capabilities(self) -> List[str]:
        """Возвращает список возможностей агента."""
        return [
            "competitive_intelligence",
            "market_analysis",
            "competitor_audit",
            "reputation_analysis",
            "financial_intelligence",
            "hr_intelligence",
            "tech_stack_analysis",
            "content_strategy_analysis",
            "pricing_intelligence",
            "ad_intelligence",
            "traffic_analysis",
            "strategy_synthesis"
        ]


def _extract_steal_worthy_tactics(findings: Dict[str, Any]) -> list:
    """Extract steal-worthy tactics from ci-auditor findings + reputation data.

    Three sources of tactics:
    1. Competitor strengths (score >= 60): "copy what works"
    2. Competitor weaknesses (score < 50): "fill the gap" opportunities
    3. Reputation data: review volume/rating insights
    """
    tactics = []
    seen_tactics = set()

    # ── Source 1: Competitor strengths (copy what works) ──
    for phase_key in ("phase_3", "phase_2"):
        phase = findings.get(phase_key, {})
        if not isinstance(phase, dict):
            continue
        auditor_result = phase.get("result", {}) or {}
        audits = auditor_result.get("audits", [])
        if not audits:
            continue

        for audit in audits:
            if not isinstance(audit, dict):
                continue
            name = audit.get("name", audit.get("url", ""))
            dims = audit.get("dimensions", {})

            for dim_name, checks in dims.items():
                if not isinstance(checks, dict):
                    continue
                for check_key, check_data in checks.items():
                    if not isinstance(check_data, dict):
                        continue
                    score = check_data.get("score", 0) or 0
                    status = check_data.get("status", "")
                    check_label = check_data.get("name", check_data.get("check", check_key))

                    # Strength-based tactic: score >= 60 (lowered from 80)
                    if status in ("pass", "good") and isinstance(score, (int, float)) and score >= 60:
                        dedup_key = f"strength:{name}:{check_label}"
                        if dedup_key in seen_tactics:
                            continue
                        seen_tactics.add(dedup_key)
                        tactics.append({
                            "source_competitor": name,
                            "tactic_description": f"Внедрить «{check_label}» как у {name}",
                            "why_it_works": f"{name} имеет {score}/100 по параметру «{check_label}»",
                            "expected_impact": "High" if score >= 85 else "Medium",
                            "estimated_effort": "Medium",
                        })

    # ── Source 2: Competitor weaknesses → our opportunities ──
    critical_gap_checks = {"online_booking", "mobile_friendly", "https", "contact_forms", "chat"}
    for phase_key in ("phase_3", "phase_2"):
        phase = findings.get(phase_key, {})
        if not isinstance(phase, dict):
            continue
        auditor_result = phase.get("result", {}) or {}
        audits = auditor_result.get("audits", [])
        if not audits:
            continue

        for audit in audits:
            if not isinstance(audit, dict):
                continue
            name = audit.get("name", audit.get("url", ""))
            dims = audit.get("dimensions", {})

            for dim_name, checks in dims.items():
                if not isinstance(checks, dict):
                    continue
                for check_key, check_data in checks.items():
                    if not isinstance(check_data, dict):
                        continue
                    score = check_data.get("score", 0) or 0
                    check_label = check_data.get("name", check_data.get("check", check_key))

                    if (isinstance(score, (int, float)) and score < 50
                            and check_key in critical_gap_checks):
                        dedup_key = f"gap:{name}:{check_label}"
                        if dedup_key in seen_tactics:
                            continue
                        seen_tactics.add(dedup_key)
                        tactics.append({
                            "source_competitor": name,
                            "tactic_description": f"Обойти {name} — внедрить «{check_label}» (у них {score}/100)",
                            "why_it_works": f"{name} отстаёт по «{check_label}» ({score}/100) — легко их превзойти",
                            "expected_impact": "High",
                            "estimated_effort": "Low" if check_key in ("https", "mobile_friendly") else "Medium",
                        })

    # ── Source 3: Reputation-based tactics ──
    phase4 = findings.get("phase_4", {})
    rep_result = phase4.get("result", {}) if isinstance(phase4, dict) else {}
    rep_scores = rep_result.get("reputation_scores", {})
    if isinstance(rep_scores, dict):
        for comp_name, rep_data in rep_scores.items():
            if not isinstance(rep_data, dict):
                continue
            rating = rep_data.get("rating")
            review_count = rep_data.get("review_count", 0)
            if isinstance(rating, (int, float)) and rating >= 4.5 and review_count < 30:
                dedup_key = f"rep:{comp_name}:low_reviews"
                if dedup_key not in seen_tactics:
                    seen_tactics.add(dedup_key)
                    tactics.append({
                        "source_competitor": comp_name,
                        "tactic_description": f"Обойти {comp_name} по отзывам — у них {rating}★ но всего {review_count} отзывов",
                        "why_it_works": f"Малое количество отзывов ({review_count}) при высоком рейтинге — уязвимость. Запустите кампанию сбора отзывов и обойдите их.",
                        "expected_impact": "High",
                        "estimated_effort": "Medium",
                    })

    # Sort: High impact first, then by effort (Low before Medium)
    effort_order = {"Low": 0, "Medium": 1, "High": 2}
    tactics.sort(key=lambda t: (0 if t["expected_impact"] == "High" else 1,
                                 effort_order.get(t.get("estimated_effort", "Medium"), 1)))
    return tactics[:7]


def _extract_top_recommendation(
    findings: Dict[str, Any], feature_matrix: Dict[str, Any]
) -> str:
    """Generate the single most actionable recommendation from findings."""
    if not feature_matrix:
        return "Соберите данные о конкурентах для получения рекомендаций."

    # Find competitor with weakest SEO
    weakest = None
    weakest_score = 999
    for name, data in feature_matrix.items():
        score = data.get("seo_score")
        if isinstance(score, (int, float)) and score < weakest_score:
            weakest_score = score
            weakest = name

    if weakest and weakest_score < 70:
        return (
            f"Главная возможность — обойти **{weakest}** по SEO: "
            f"у них {weakest_score}/100, а у лидеров 70+. "
            f"Исправьте ошибки на сайте, добавьте контент по услугам — и вы выше."
        )

    # Find competitor with best SEO as benchmark
    best = None
    best_score = 0
    for name, data in feature_matrix.items():
        score = data.get("seo_score")
        if isinstance(score, (int, float)) and score > best_score:
            best_score = score
            best = name

    if best:
        return (
            f"Ориентируйтесь на **{best}** (SEO {best_score}/100) — "
            f"это ваш главный цифровой конкурент. Проанализируйте их стратегию "
            f"и адаптируйте лучшие практики."
        )

    return "Проведите полный SEO-аудит для выявления точек роста."


def _extract_name_from_url(url: str) -> str:
    """Extract a human-readable company name from a URL/domain.

    Converts 'https://yutskovskaya.ru/' → 'Yutskovskaya'
    or 'yutskovskaya.ru' → 'Yutskovskaya'.
    """
    if not url:
        return "Unknown"
    # Strip protocol and path
    domain = url.replace("https://", "").replace("http://", "").rstrip("/").split("/")[0]
    # Remove www. prefix
    domain = domain.removeprefix("www.")
    # Take the domain name part (before TLD), capitalize
    name_part = domain.split(".")[0]
    # Capitalize first letter
    if name_part:
        name_part = name_part[0].upper() + name_part[1:] if len(name_part) > 1 else name_part.upper()
    return name_part or "Unknown"


def _count_actual_competitors(findings: Dict[str, Any], task_data: Dict[str, Any]) -> int:
    """Count actual competitors from ci-scout results, falling back to task_data input.

    Phase 1 (ci-scout) returns top_for_analysis — the real list of competitors found.
    Phase 2 (ci-auditor) returns audits — one per competitor analyzed.
    Falls back to task_data competitors count if neither phase has results.
    """
    # Try Phase 1 — ci-scout's top_for_analysis
    phase1 = findings.get("phase_1", {})
    if isinstance(phase1, dict):
        scout_result = phase1.get("result", {}) or {}
        top = scout_result.get("top_for_analysis", [])
        if isinstance(top, list) and top:
            return len(top)

    # Try Phase 2 — ci-auditor's audits array
    phase2 = findings.get("phase_2", {})
    if isinstance(phase2, dict):
        auditor_result = phase2.get("result", {}) or {}
        audits = auditor_result.get("audits", [])
        if isinstance(audits, list) and audits:
            return len(audits)

    # Fallback: initial input
    competitors = task_data.get("competitors", [])
    return len(competitors) if competitors else 0


def _compute_wow_from_findings(findings: Dict[str, Any]) -> Dict[str, Any]:
    """Compute WOW estimates from phase findings (shared by quick and compact paths)."""
    phase1 = findings.get("phase_1", {})
    scout_result = phase1.get("result", {}) if isinstance(phase1, dict) else {}
    competitors = scout_result.get("top_for_analysis", [])
    competitor_count = len(competitors) if isinstance(competitors, list) else 0

    phase2 = findings.get("phase_2", {})
    auditor_result = phase2.get("result", {}) if isinstance(phase2, dict) else {}
    audit_scores = auditor_result.get("scores", {}) or {}
    avg_score = 0
    if isinstance(audit_scores, dict):
        scores = [v for v in audit_scores.values() if isinstance(v, (int, float))]
        if scores:
            avg_score = sum(scores) / len(scores)

    phase4 = findings.get("phase_4", {})
    rep_result = phase4.get("result", {}) if isinstance(phase4, dict) else {}
    avg_rating = rep_result.get("avg_rating", 0) or 0

    base = 10 + competitor_count * 5
    if 0 < avg_score < 50:
        base += 15
    elif 0 < avg_score < 70:
        base += 5

    if 0 < avg_score < 50:
        weeks = 4
    elif 0 < avg_score < 70:
        weeks = 8
    else:
        weeks = 12

    if competitor_count <= 2:
        cost = 800
    elif competitor_count <= 5:
        cost = 1200
    else:
        cost = 1800

    if avg_rating > 0 and avg_rating < 4.0:
        cost = max(500, cost - 300)

    return {
        "patients_per_month": max(5, base),
        "time_to_result_weeks": weeks,
        "cost_per_patient_rub": cost,
        "is_estimated": True,
    }


def _extract_auditor_seo_score(auditor_result: Dict[str, Any], url: str = "") -> Any:
    """Extract an overall SEO score from ci-auditor's nested result structure.

    ci-auditor returns: {audits: [{dimensions: {technical: {check: {score}}, content: {check: {score}}}}]}
    This flattens all dimension scores into a single 0-100 number.
    Returns "?" if no scores found.
    """
    if not isinstance(auditor_result, dict):
        return "?"

    # Try direct seo_score first (if auditor starts returning it)
    if "seo_score" in auditor_result:
        return auditor_result["seo_score"]

    audits = auditor_result.get("audits", [])
    if not audits:
        return "?"

    # Find the audit matching this URL, or use the first one
    target = None
    for a in audits:
        if isinstance(a, dict):
            if url and a.get("url") == url:
                target = a
                break
            if target is None:
                target = a

    if not target:
        return "?"

    dimensions = target.get("dimensions", {})
    if not dimensions:
        return "?"

    all_scores = []
    for dim_name, checks in dimensions.items():
        if isinstance(checks, dict):
            for check_key, check_data in checks.items():
                if isinstance(check_data, dict):
                    score = check_data.get("score")
                    if isinstance(score, (int, float)):
                        all_scores.append(score)

    if not all_scores:
        return "?"

    avg = sum(all_scores) / len(all_scores)
    return round(avg, 1)


def _extract_reputation_rating(rep_result: Dict[str, Any], competitor_name: str = "") -> Any:
    """Extract average rating from ci-reputation's nested result structure.

    ci-reputation returns: {reputation_scores: [{name, overall_score, avg_rating}]}
    or: {reviews_data: [{name, avg_rating}]}.
    Returns None if no rating found.
    """
    if not isinstance(rep_result, dict):
        return None

    # Try direct avg_rating first
    if "avg_rating" in rep_result and rep_result["avg_rating"] is not None:
        return rep_result["avg_rating"]

    # Try reputation_scores array
    scores = rep_result.get("reputation_scores", [])
    if isinstance(scores, list):
        for s in scores:
            if isinstance(s, dict):
                if competitor_name and s.get("name") != competitor_name:
                    continue
                rating = s.get("avg_rating") or s.get("overall_score")
                if isinstance(rating, (int, float)):
                    return round(rating, 1)

    # Try reviews_data array
    reviews = rep_result.get("reviews_data", [])
    if isinstance(reviews, list):
        for r in reviews:
            if isinstance(r, dict):
                if competitor_name and r.get("name") != competitor_name:
                    continue
                rating = r.get("avg_rating")
                if isinstance(rating, (int, float)):
                    return round(rating, 1)

    return None


def _has_pricing_data_from_agent(pricing_result: Dict[str, Any], competitor_name: str) -> bool:
    """Check if ci-pricing agent found real pricing data for a competitor."""
    profiles = pricing_result.get("pricing_profiles", []) if isinstance(pricing_result, dict) else []
    for p in profiles:
        if isinstance(p, dict) and p.get("name") == competitor_name:
            if p.get("prices") and p["prices"].get("count", 0) > 0:
                return True
            if p.get("avg_check") is not None:
                return True
    return False


def _extract_prices_from_agent(
    pricing_profiles: List[Dict[str, Any]], competitor_name: str
) -> Dict[str, Any]:
    """Extract real pricing info from ci-pricing agent profiles."""
    for p in pricing_profiles:
        if isinstance(p, dict) and p.get("name") == competitor_name:
            prices = p.get("prices", {})
            return {
                "primary_consult": prices.get("budget_range"),
                "popular_service": prices.get("mid_range"),
                "avg_check": p.get("avg_check"),
                "price_segment": p.get("price_segment"),
                "price_transparency": p.get("price_transparency"),
                "confidence": p.get("confidence", 0),
            }
    return {"primary_consult": None, "popular_service": None, "avg_check": None,
            "price_segment": None, "price_transparency": False, "confidence": 0}


def _has_pricing_data(auditor_result: Dict[str, Any]) -> bool:
    """Check if ci-auditor found pricing information on the site."""
    if not isinstance(auditor_result, dict):
        return False
    audits = auditor_result.get("audits", [])
    for a in (audits or []):
        if isinstance(a, dict):
            dims = a.get("dimensions", {})
            for dim_checks in dims.values():
                if isinstance(dim_checks, dict):
                    for check in dim_checks.values():
                        if isinstance(check, dict) and check.get("status") == "pass":
                            if check.get("score", 0) and isinstance(check.get("score"), (int, float)):
                                if check["score"] > 60:
                                    return True
    return False


def _has_online_booking(auditor_result: Dict[str, Any]) -> bool:
    """Check if ci-auditor detected online booking capability."""
    if not isinstance(auditor_result, dict):
        return False
    text = str(auditor_result).lower()
    return any(kw in text for kw in ("booking", "запись", "form", "callback", "widget"))


def _extract_prices(auditor_result: Dict[str, Any]) -> Dict[str, Any]:
    """Extract pricing info from ci-auditor result."""
    return {"primary_consult": None, "popular_service": None}


def _classify_price_positioning(
    primary_consult: Any, all_profiles: List[Dict[str, Any]]
) -> str:
    """Classify competitor's price positioning relative to market average."""
    if primary_consult is None:
        return "неизвестно"
    if not isinstance(primary_consult, (int, float)):
        return "неизвестно"
    others = []
    for p in (all_profiles or []):
        prices = p.get("prices", {})
        val = prices.get("budget_range")
        if isinstance(val, (int, float)) and val > 0:
            others.append(val)
    if not others:
        return "неизвестно"
    avg = sum(others) / len(others)
    ratio = primary_consult / avg if avg > 0 else 1
    if ratio < 0.8:
        return "ниже рынка (демпинг?)"
    elif ratio < 1.2:
        return "среднерыночная"
    else:
        return "выше рынка (премиум)"


def _extract_competitive_highlights(
    findings: Dict[str, Any], comp_list: List[Dict[str, Any]]
) -> List[str]:
    """Extract surprising/interesting competitive findings for narrative."""
    highlights = []

    # Check reputation gaps
    rep_result = findings.get("phase_4", {}).get("result", {})
    rep_scores = rep_result.get("reputation_scores", []) if isinstance(rep_result, dict) else []
    for rs in rep_scores:
        rating = rs.get("avg_rating", 0)
        reviews = rs.get("total_reviews", 0)
        if isinstance(rating, (int, float)) and rating >= 4.7 and isinstance(reviews, (int, float)) and reviews >= 100:
            highlights.append(
                f"«{rs.get('name', '?')}» собрал {reviews} отзывов с рейтингом {rating}★ — "
                f"пациенты довольны и активно делятся мнением"
            )
    if len(highlights) > 3:
        highlights = highlights[:3]

    # Check vacancy surges (growth signals)
    phase5 = findings.get("phase_5", {})
    vac_agent = phase5.get("results", {}).get("ci-vacancies", {}) if isinstance(phase5, dict) else {}
    vac_result = vac_agent.get("result", {}) if isinstance(vac_agent, dict) else {}
    for vp in vac_result.get("vacancy_profiles", [])[:5]:
        if (vp.get("open_vacancies") or 0) >= 10:
            highlights.append(
                f"«{vp.get('name', '?')}» нанимает {vp.get('open_vacancies')}+ сотрудников — "
                f"активно растёт и расширяется"
            )

    # Check ecosystem strength
    eco_agent = phase5.get("results", {}).get("ci-ecosystem", {}) if isinstance(phase5, dict) else {}
    eco_result = eco_agent.get("result", {}) if isinstance(eco_agent, dict) else {}
    for ep in eco_result.get("ecosystem_profiles", [])[:5]:
        channels = ep.get("channels_count", 0) or len(ep.get("social_links", []))
        if channels >= 4:
            highlights.append(
                f"«{ep.get('name', '?')}» представлен на {channels} digital-площадках — "
                f"максимальный охват аудитории"
            )

    # Check tech leaders
    tech_agent = phase5.get("results", {}).get("ci-tech", {}) if isinstance(phase5, dict) else {}
    tech_result = tech_agent.get("result", {}) if isinstance(tech_agent, dict) else {}
    tech_profiles = tech_result.get("tech_profiles", []) if isinstance(tech_result, dict) else []
    for tp in tech_profiles[:5]:
        stack = tp.get("tech_stack", []) if isinstance(tp.get("tech_stack"), list) else []
        if len(stack) >= 5:
            highlights.append(
                f"«{tp.get('name', '?')}» использует {len(stack)} технологий на сайте — "
                f"технически продвинутая клиника"
            )

    return highlights[:8]


def _top_n_by(items: List[Dict[str, Any]], key: str, n: int) -> List[Dict[str, Any]]:
    """Return top N items sorted by key (descending), skipping None/missing values."""
    filtered = [
        item for item in items
        if isinstance(item, dict) and item.get(key) is not None
    ]
    filtered.sort(key=lambda x: x.get(key, 0), reverse=True)
    return filtered[:n]
