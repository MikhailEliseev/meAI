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
                from aim.subagents.competitive_intel.agents.ci_scout import CIScoutAgent
                agent = CIScoutAgent(agent_id=f"{self.agent_id}-scout", database_url=db_url, vault_path=vault)
            elif agent_name == "ci-auditor":
                from aim.subagents.competitive_intel.agents.ci_auditor import CIAuditorAgent
                agent = CIAuditorAgent(agent_id=f"{self.agent_id}-auditor", database_url=db_url, vault_path=vault)
            elif agent_name == "ci-reputation":
                from aim.subagents.competitive_intel.agents.ci_reputation import CIReputationAgent
                agent = CIReputationAgent(agent_id=f"{self.agent_id}-reputation", database_url=db_url, vault_path=vault)
            elif agent_name == "ci-finance":
                from aim.subagents.competitive_intel.agents.ci_finance import CIFinanceAgent
                agent = CIFinanceAgent(agent_id=f"{self.agent_id}-finance", database_url=db_url, vault_path=vault)
            elif agent_name == "ci-vacancies":
                from aim.subagents.competitive_intel.agents.ci_vacancies import CIVacanciesAgent
                agent = CIVacanciesAgent(agent_id=f"{self.agent_id}-vacancies", database_url=db_url, vault_path=vault)
            elif agent_name == "ci-tech":
                from aim.subagents.competitive_intel.agents.ci_tech_real import CITechAgent
                agent = CITechAgent(agent_id=f"{self.agent_id}-tech", database_url=db_url, vault_path=vault)
            elif agent_name == "ci-site-crawler":
                from aim.subagents.competitive_intel.agents.ci_site_crawler import CISiteCrawlerAgent
                agent = CISiteCrawlerAgent(agent_id=f"{self.agent_id}-crawler", database_url=db_url, vault_path=vault)
            elif agent_name == "ci-content":
                from aim.subagents.competitive_intel.agents.ci_content_improved import CIContentAgentImproved
                agent = CIContentAgentImproved(agent_id=f"{self.agent_id}-content", database_url=db_url, vault_path=vault)
            elif agent_name == "ci-pricing":
                from aim.subagents.competitive_intel.agents.ci_pricing import CIPricingAgent
                agent = CIPricingAgent(agent_id=f"{self.agent_id}-pricing", database_url=db_url, vault_path=vault)
            elif agent_name == "ci-ecosystem":
                from aim.subagents.competitive_intel.agents.ci_ecosystem import CIEcosystemAgent
                agent = CIEcosystemAgent(agent_id=f"{self.agent_id}-ecosystem", database_url=db_url, vault_path=vault)
            elif agent_name == "ci-backlink":
                from aim.subagents.competitive_intel.agents.ci_backlink import CIBacklinkAgent
                agent = CIBacklinkAgent(agent_id=f"{self.agent_id}-backlink", database_url=db_url, vault_path=vault)
            elif agent_name == "ci-rank-tracker":
                from aim.subagents.competitive_intel.agents.ci_rank_tracker import CIRankTrackerAgent
                agent = CIRankTrackerAgent(agent_id=f"{self.agent_id}-ranktracker", database_url=db_url, vault_path=vault)
            elif agent_name == "ci-factchecker":
                from aim.subagents.competitive_intel.agents.ci_factchecker import CIFactcheckerAgent
                agent = CIFactcheckerAgent(agent_id=f"{self.agent_id}-factchecker", database_url=db_url, vault_path=vault)
            elif agent_name == "ci-strategist":
                from aim.subagents.competitive_intel.agents.ci_strategist import CIStrategistAgent
                agent = CIStrategistAgent(agent_id=f"{self.agent_id}-strategist", database_url=db_url, vault_path=vault)
            elif agent_name == "ci-prioritizer":
                from aim.subagents.competitive_intel.agents.ci_prioritizer import CIPrioritizerAgent
                agent = CIPrioritizerAgent(agent_id=f"{self.agent_id}-prioritizer", database_url=db_url, vault_path=vault)
            elif agent_name == "ci-marketing-strategy":
                from aim.subagents.competitive_intel.agents.ci_marketing_strategy import CIMarketingStrategyAgent
                agent = CIMarketingStrategyAgent(agent_id=f"{self.agent_id}-marketing", database_url=db_url, vault_path=vault)
            elif agent_name == "ci-offer-generator":
                from aim.subagents.competitive_intel.agents.ci_offer_generator import CIOfferGeneratorAgent
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
        """Persistent handler for ci.agent.completed events — stores results for audit trail.

        Collects ALL agent completion events regardless of which phase initiated them.
        The transient per-phase callback in _execute_single_phase handles phase-specific
        correlation_id matching; this persistent handler serves as the audit trail.
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

                    # Prepare phase-specific task data
                    phase_task_data = task_data.copy()
                    phase_task_data["correlation_id"] = correlation_id

                    # Phase 1 uses initial URLs, Phase 2+ uses results from Phase 1
                    if phase_num == 1:
                        phase_task_data["competitors"] = competitors_list
                    else:
                        # Use top_for_analysis from Phase 1 if available
                        if "phase_1" in findings and "result" in findings["phase_1"]:
                            phase1_result = findings["phase_1"]["result"]
                            if "top_for_analysis" in phase1_result:
                                phase_task_data["competitors"] = phase1_result["top_for_analysis"]
                            else:
                                # Fallback: convert URLs to simple objects
                                phase_task_data["competitors"] = [
                                    {"name": url, "url": url} for url in competitors_list
                                ]
                        else:
                            # Fallback: convert URLs to simple objects
                            phase_task_data["competitors"] = [
                                {"name": url, "url": url} for url in competitors_list
                            ]

                    if isinstance(agent_names, list):
                        # Phase 5: Parallel execution
                        phase_result = await self._execute_parallel_phase(
                            phase_num, agent_names, phase_task_data
                        )
                    else:
                        # Single agent execution
                        phase_result = await self._execute_single_phase(
                            phase_num, agent_names, phase_task_data
                        )

                    findings[f"phase_{phase_num}"] = phase_result
                except Exception as e:
                    errors.append(f"Phase {phase_num} failed: {str(e)}")

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()

            # Validate results quality
            quality_score = self._calculate_quality_score(findings, phases)

            # Generate reports
            reports = await self._generate_reports(task_id, findings, task_data)

            summary = {
                "tier": tier,
                "phases_executed": len(phases),
                "execution_time_seconds": int(execution_time),
                "competitors_analyzed": len(task_data.get("competitors", [])),
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

            # Return structured result
            return {
                "task_id": task_id,
                "tier": tier,
                "phases_executed": phases,
                "execution_time_seconds": int(execution_time),
                "competitors_analyzed": len(task_data.get("competitors", [])),
                "findings": findings,
                "reports": reports,
                "quality_score": quality_score,
                "errors": errors,
                "correlation_id": correlation_id,
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

    async def _execute_single_phase(
        self,
        phase_num: int,
        agent_name: str,
        task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute single agent phase via EventBus delegation.

        Publishes a task.request Message targeting the agent and waits for the
        ci.agent.completed Event with matching correlation_id. No fallback to
        direct agent.execute_task() — EventBus delegation is the ONLY path.
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
            task_id=task_data.get("task_id", "unknown"),
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
        task.payload = {
            "niche": task_data.get("niche", ""),
            "geo": task_data.get("geo", ""),
            "target_audience": task_data.get("target_audience", ""),
            "price_segment": task_data.get("price_segment", "mid"),
            "competitors": task_data.get("competitors", [])
        }

        correlation_id = task_data.get("correlation_id", task_data.get("task_id", "unknown"))
        phase_correlation = f"{correlation_id}-{phase_num}"

        # Set correlation_id on agent so the bridged report_result can use it
        agent._ci_correlation_id = phase_correlation

        # ── EventBus delegation ──
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

        # Wait for agent to complete via EventBus
        # Agent's poll loop picks up task.request, executes via _execute_and_report(),
        # and the bridged report_result() publishes ci.agent.completed Event.
        # The transient callback below catches it.
        completion_event = asyncio.Event()
        completion_result: Dict[str, Any] = {}

        async def on_agent_completed(event: Event):
            if event.payload.get("correlation_id") == phase_correlation:
                completion_result.update(event.payload)
                completion_event.set()

        self.event_bus.subscribe("ci.agent.completed", on_agent_completed)

        try:
            await asyncio.wait_for(completion_event.wait(), timeout=60.0)
            return {
                "phase": phase_num,
                "agent": agent_name,
                "status": completion_result.get("status", "completed"),
                "result": completion_result.get("result", {}),
            }
        except asyncio.TimeoutError:
            logger.error(
                "EventBus delegation timeout for %s phase %d after 60s",
                agent_name, phase_num,
            )
            return {
                "phase": phase_num,
                "agent": agent_name,
                "status": "timeout",
                "error": f"Agent {agent_name} did not complete within 60s",
                "result": {},
            }
        finally:
            self.event_bus.unsubscribe("ci.agent.completed", on_agent_completed)

    async def _execute_parallel_phase(
        self,
        phase_num: int,
        agent_names: List[str],
        task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute multiple agents in parallel (Phase 5)"""
        tasks = []

        for agent_name in agent_names:
            tasks.append(self._execute_single_phase(phase_num, agent_name, task_data))

        # Execute in parallel with error handling
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect results
        agent_results = {}
        errors = []

        for i, result in enumerate(results):
            agent_name = agent_names[i]
            if isinstance(result, Exception):
                errors.append(f"{agent_name}: {str(result)}")
                agent_results[agent_name] = {"status": "failed", "error": str(result)}
            else:
                agent_results[agent_name] = result

        return {
            "phase": phase_num,
            "parallel": True,
            "agents": agent_names,
            "results": agent_results,
            "errors": errors
        }

    def _calculate_quality_score(
        self,
        findings: Dict[str, Any],
        phases_executed: List[int]
    ) -> Dict[str, Any]:
        """Calculate quality score for CI analysis results"""

        # Count successful phases
        successful_phases = 0
        failed_phases = 0

        for phase_key, phase_data in findings.items():
            status = phase_data.get("status", "unknown")
            if status == "success":
                successful_phases += 1
            elif status == "failed" or status == "stub":
                failed_phases += 1

        total_phases = len(phases_executed)

        # Calculate completeness (0-100)
        completeness = int((successful_phases / total_phases * 100)) if total_phases > 0 else 0

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
            # Generate reports directory
            reports_dir = Path("AIM/reports") / task_id
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

    async def _execute_phase_stub(self, phase_num: int, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stub for phase execution (to be implemented with real CI agents).

        Args:
            phase_num: Phase number to execute
            task_data: Task data

        Returns:
            Phase results dict
        """
        # TODO: Implement real phase execution with CI agents
        await asyncio.sleep(0.1)  # Simulate work
        return {
            "phase": phase_num,
            "status": "completed",
            "data": f"Phase {phase_num} results"
        }

    async def execute_task(self, task: Task) -> TaskResult:
        """
        Выполнить задачу конкурентной разведки.

        Args:
            task: Задача с payload:
                - niche: ниша (обязательно)
                - geo: город (обязательно)
                - target_audience: целевая аудитория (опционально)
                - depth: quick/deep/full (опционально, default: deep)

        Returns:
            TaskResult с результатами анализа
        """
        try:
            # Логирование начала
            await self._log_start(task)

            # Определить tier
            tier = self._detect_tier(task.payload)

            # Проверить stale data
            await self._check_stale_data()

            # Выполнить фазы
            results = await self._execute_phases(tier, task.payload)

            # Логирование завершения
            await self._log_completion(task, results)

            return TaskResult(
                task_id=task.id,
                status="completed",
                result=results
            )

        except Exception as e:
            await self._log_error(task, str(e))
            return TaskResult(
                task_id=task.id,
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

    async def _execute_phases(self, tier: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выполнить фазы анализа для выбранного tier.

        Args:
            tier: quick/deep/full
            payload: данные задачи

        Returns:
            Агрегированные результаты всех фаз
        """
        phases = self.tiers[tier]["phases"]
        results = {
            "tier": tier,
            "phases_executed": [],
            "phase_results": {}
        }

        for phase in phases:
            phase_result = await self._execute_phase(phase, payload, results)
            results["phases_executed"].append(phase)
            results["phase_results"][f"phase_{phase}"] = phase_result

        return results

    async def _execute_phase(
        self,
        phase: int,
        payload: Dict[str, Any],
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Выполнить одну фазу анализа.

        Args:
            phase: номер фазы (1-16)
            payload: данные задачи
            previous_results: результаты предыдущих фаз

        Returns:
            Результат фазы
        """
        agents = self.phase_agents.get(phase)

        if not agents:
            return {"status": "skipped", "reason": "no agents for phase"}

        # Parallel execution for phase 5
        if isinstance(agents, list):
            return await self._execute_parallel_agents(agents, payload, previous_results)
        else:
            return await self._execute_single_agent(agents, payload, previous_results)

    async def _execute_parallel_agents(
        self,
        agents: List[str],
        payload: Dict[str, Any],
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Выполнить несколько агентов параллельно (фаза 5).

        Args:
            agents: список agent_id
            payload: данные задачи
            previous_results: результаты предыдущих фаз

        Returns:
            Агрегированные результаты всех агентов
        """
        tasks = []
        for agent_id in agents:
            task = Task(
                id=f"{self.agent_id}_{agent_id}_{datetime.now().timestamp()}",
                type=f"ci_{agent_id.replace('-', '_')}",
                payload={
                    **payload,
                    "previous_results": previous_results
                }
            )
            tasks.append(self._delegate_to_agent(agent_id, task))

        # Выполнить параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Агрегировать результаты
        aggregated = {
            "agents_executed": agents,
            "results": {}
        }

        for agent_id, result in zip(agents, results):
            if isinstance(result, Exception):
                aggregated["results"][agent_id] = {
                    "status": "failed",
                    "error": str(result)
                }
            else:
                aggregated["results"][agent_id] = result

        return aggregated

    async def _execute_single_agent(
        self,
        agent_id: str,
        payload: Dict[str, Any],
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Выполнить одного агента.

        Args:
            agent_id: ID агента
            payload: данные задачи
            previous_results: результаты предыдущих фаз

        Returns:
            Результат агента
        """
        task = Task(
            id=f"{self.agent_id}_{agent_id}_{datetime.now().timestamp()}",
            type=f"ci_{agent_id.replace('-', '_')}",
            payload={
                **payload,
                "previous_results": previous_results
            }
        )

        return await self._delegate_to_agent(agent_id, task)

    async def _delegate_to_agent(self, agent_id: str, task: Task) -> Dict[str, Any]:
        """
        Делегировать задачу агенту через Event Bus.

        Args:
            agent_id: ID агента
            task: задача

        Returns:
            Результат агента
        """
        # Отправить событие через Event Bus
        await self.event_bus.publish(Event(
            event_type=f"task.{agent_id}",
            payload=task.to_dict(),
        ))

        # Логировать делегирование
        await self.vault.log_operation(
            "delegate",
            f"Делегировал задачу {task.id} агенту {agent_id}"
        )

        # TODO: Ждать результат от агента через Event Bus
        # Пока возвращаем заглушку
        return {
            "agent_id": agent_id,
            "status": "delegated",
            "task_id": task.id
        }

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
