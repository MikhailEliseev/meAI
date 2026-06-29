"""Pipeline Engine — Python-controlled 13-phase scout pipeline.

LLM — интерпретатор данных, НЕ оркестратор.
Python контролирует последовательность фаз и обработку ошибок.

Phase-by-phase progress (per Plan 06-29):
    progress_callback is called before and after each phase so the SSE
    layer can emit structured phase-progress events to the frontend.
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)

# ── Phase status ──────────────────────────────────────────────────────
class PhaseStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    no_data = "no_data"
    permanent_failure = "permanent_failure"
    tool_failed = "tool_failed"
    timed_out = "timed_out"
    skipped = "skipped"


# ── Phase contract ────────────────────────────────────────────────────
@dataclass
class PhaseContract:
    """Per-phase execution contract."""
    max_retries: int = 0
    retry_on_key_exhaustion: bool = False
    allow_no_data: bool = False
    timeout: int = 120
    on_permanent_failure: str = "skip"  # "skip" | "abort"


# ── Phase result ──────────────────────────────────────────────────────
@dataclass
class PhaseResult:
    status: PhaseStatus = PhaseStatus.pending
    data: dict | None = None
    duration_seconds: float | None = None
    error_message: str | None = None
    llm_interpretation: str | None = None


# ── Phase definition ──────────────────────────────────────────────────
@dataclass
class Phase:
    phase_id: int
    name: str
    tools: list[str]
    contract: PhaseContract = field(default_factory=PhaseContract)


# ── Pipeline state ────────────────────────────────────────────────────
@dataclass
class PipelineState:
    session_id: str = ""
    client_url: str = ""
    client_name: str = ""
    client_city: str = ""
    client_specialization: str = ""
    client_inn: str = ""
    current_phase: int = -1
    phases: dict[int, PhaseResult] = field(default_factory=dict)
    retry_counts: dict[int, int] = field(default_factory=dict)
    accumulated_data: dict = field(default_factory=dict)
    started_at: str = ""
    mode: str = "ONBOARDING"


# ── 13 Phases (aligned with Plan 06-29 PhaseTracker) ─────────────────
PHASES: list[Phase] = [
    Phase(0, "PERPLEXITY",
          tools=["perplexity_search"],
          contract=PhaseContract(timeout=120, on_permanent_failure="skip")),
    Phase(1, "COMPETITORS",
          tools=["find_competitors", "run_ci_analysis"],
          contract=PhaseContract(max_retries=3, timeout=600, retry_on_key_exhaustion=True, on_permanent_failure="skip")),
    Phase(2, "TECH AUDIT",
          tools=["run_pagespeed", "run_tech_seo_audit"],
          contract=PhaseContract(timeout=300, on_permanent_failure="skip")),
    Phase(3, "SOCIAL VERIFIER",
          tools=["run_review_platforms"],
          contract=PhaseContract(timeout=180, allow_no_data=True, on_permanent_failure="skip")),
    Phase(4, "CONTENT ANALYSIS",
          tools=["run_content_analysis"],
          contract=PhaseContract(timeout=120, on_permanent_failure="skip")),
    Phase(5, "KEY PERSONS",
          tools=["find_doctor_handles", "run_instagram_content"],
          contract=PhaseContract(timeout=240, allow_no_data=True, on_permanent_failure="skip")),
    Phase(6, "SMI MENTIONS",
          tools=["run_smi_mentions"],
          contract=PhaseContract(timeout=120, allow_no_data=True, on_permanent_failure="skip")),
    Phase(7, "FORUM PAINS",
          tools=["web_search"],
          contract=PhaseContract(timeout=120, allow_no_data=True, on_permanent_failure="skip")),
    Phase(8, "FINANCE",
          tools=["find_company_financials"],
          contract=PhaseContract(timeout=60, allow_no_data=True, on_permanent_failure="skip")),
    Phase(9, "CONTENT PLAN",
          tools=["run_content_gaps"],
          contract=PhaseContract(timeout=120, allow_no_data=True, on_permanent_failure="skip")),
    Phase(10, "HTML BUILD",
          tools=["generate_html_report"],
          contract=PhaseContract(timeout=180, on_permanent_failure="abort")),
    Phase(11, "QC CRITIQUE",
          tools=[],  # LLM-only phase — critique via interpretation prompt
          contract=PhaseContract(timeout=90, on_permanent_failure="skip")),
    Phase(12, "PRESENTATION",
          tools=["publish_scout_report"],
          contract=PhaseContract(timeout=60, on_permanent_failure="skip")),
]

# Build name → phase index lookup
_PHASE_INDEX: dict[str, int] = {p.name: p.phase_id for p in PHASES}


class PipelineEngine:
    """Python-controlled 13-phase scout pipeline.

    LLM is used as a data interpreter per phase, not as an orchestrator.
    The engine iterates phases sequentially, calls tool handlers directly,
    handles retries and key rotation, and persists all data.
    """

    def __init__(self):
        self._tool_handlers = self._build_tool_handlers()

    # ── Tool handler registry ────────────────────────────────────────
    def _build_tool_handlers(self) -> dict[str, Callable]:
        """Build map of tool_name → async handler callable."""
        handlers: dict[str, Callable] = {}

        # Import tool handlers lazily to avoid circular imports
        try:
            from app.tools.run_full_scout import handle_run_full_scout
        except ImportError:
            handle_run_full_scout = None

        # web_search
        try:
            from app.tools.web_search import handle_web_search
            handlers["web_search"] = handle_web_search
        except ImportError:
            pass

        # perplexity_search
        try:
            from app.tools.perplexity_search import handle_perplexity_search
            handlers["perplexity_search"] = handle_perplexity_search
        except ImportError:
            pass

        # run_pagespeed
        try:
            from app.tools.run_pagespeed import handle_run_pagespeed
            handlers["run_pagespeed"] = handle_run_pagespeed
        except ImportError:
            pass

        # run_tech_seo_audit / run_seo_audit
        try:
            from app.tools.run_tech_seo_audit import handle_run_tech_seo_audit
            handlers["run_tech_seo_audit"] = handle_run_tech_seo_audit
            handlers["run_seo_audit"] = handle_run_tech_seo_audit
        except ImportError:
            pass

        # find_competitors
        try:
            from app.tools.find_competitors import handle_find_competitors
            handlers["find_competitors"] = handle_find_competitors
        except ImportError:
            pass

        # run_review_platforms
        try:
            from app.tools.run_review_platforms import handle_run_review_platforms
            handlers["run_review_platforms"] = handle_run_review_platforms
        except ImportError:
            pass

        # run_content_analysis
        try:
            from app.tools.run_content_analysis import handle_run_content_analysis
            handlers["run_content_analysis"] = handle_run_content_analysis
        except ImportError:
            pass

        # run_hh_analysis (part of KEY PERSONS)
        try:
            from app.tools.run_hh_analysis import handle_run_hh_analysis
            handlers["run_hh_analysis"] = handle_run_hh_analysis
        except ImportError:
            pass

        # find_doctor_handles
        try:
            from app.tools.find_doctor_handles import handle_find_doctor_handles
            handlers["find_doctor_handles"] = handle_find_doctor_handles
        except ImportError:
            pass

        # run_doctor_dossiers
        try:
            from app.tools.run_doctor_dossiers import handle_run_doctor_dossiers
            handlers["run_doctor_dossiers"] = handle_run_doctor_dossiers
        except ImportError:
            pass

        # run_instagram_content
        try:
            from app.tools.run_instagram_content import handle_run_instagram_content
            handlers["run_instagram_content"] = handle_run_instagram_content
        except ImportError:
            pass

        # run_ci_analysis
        try:
            from app.tools.run_ci_analysis import handle_run_ci_analysis
            handlers["run_ci_analysis"] = handle_run_ci_analysis
        except ImportError:
            pass

        # run_smi_mentions
        try:
            from app.tools.run_smi_mentions import handle_run_smi_mentions
            handlers["run_smi_mentions"] = handle_run_smi_mentions
        except ImportError:
            pass

        # run_content_gaps
        try:
            from app.tools.run_content_gaps import handle_run_content_gaps
            handlers["run_content_gaps"] = handle_run_content_gaps
        except ImportError:
            pass

        # find_company_financials
        try:
            from app.tools.find_company_financials import handle_find_company_financials
            handlers["find_company_financials"] = handle_find_company_financials
        except ImportError:
            pass

        # generate_html_report
        try:
            from app.tools.generate_html_report import handle_generate_html_report
            handlers["generate_html_report"] = handle_generate_html_report
        except ImportError:
            pass

        # publish_scout_report
        try:
            from app.tools.publish_scout_report import handle_publish_scout_report
            handlers["publish_scout_report"] = handle_publish_scout_report
        except ImportError:
            pass

        # Additional tools available in the registry
        for name in ("perplexity_deep_analyze", "firecrawl_extract", "firecrawl_batch_scrape",
                     "firecrawl_agent", "crawlee_scrape", "crawlee_search", "scrapy_crawl",
                     "run_media_urls", "run_forum_pains"):
            if name not in handlers:
                try:
                    mod = __import__(f"app.tools.{name}", fromlist=[f"handle_{name}"])
                    handler = getattr(mod, f"handle_{name}", None)
                    if handler:
                        handlers[name] = handler
                except (ImportError, AttributeError):
                    pass

        return handlers

    # ── Main entry point ─────────────────────────────────────────────
    async def execute(
        self,
        session_id: str = "",
        client_url: str = "",
        client_name: str = "",
        mode: str = "ONBOARDING",
        chat_id: int = 0,
        progress_callback: Callable | None = None,
    ) -> PipelineState:
        """Execute all 13 phases sequentially.

        Args:
            session_id: Session identifier
            client_url: Target clinic website URL
            client_name: Optional clinic name
            mode: Execution mode (ONBOARDING / PRESALE)
            chat_id: Telegram chat_id for progress updates
            progress_callback: Optional callback(phase_id, phase_name, status,
                message, duration_seconds) for SSE phase-progress events.

        Returns:
            PipelineState with all phase results and accumulated data.
        """
        state = PipelineState(
            session_id=session_id,
            client_url=client_url,
            client_name=client_name,
            mode=mode,
            started_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )

        # ── PRE-FLIGHT: determine city, specialization ───────────────
        await self._pre_flight(state, client_url)

        # ── Execute phases ───────────────────────────────────────────
        for phase in PHASES:
            phase_id = phase.phase_id
            state.current_phase = phase_id
            state.phases[phase_id] = PhaseResult()

            # ── Notify: phase started ───────────────────────────────
            if progress_callback:
                try:
                    progress_callback(
                        phase_id=phase_id,
                        phase_name=phase.name,
                        status="started",
                    )
                except Exception as e:
                    logger.warning("progress_callback(started) failed: %s", e)

            # ── Execute phase with retries ───────────────────────────
            t0 = time.time()
            result = await self._execute_phase(phase, state)

            duration = round(time.time() - t0, 1)
            result.duration_seconds = duration
            state.phases[phase_id] = result

            # ── Store in accumulated_data ────────────────────────────
            key = f"{phase.name}_result"
            state.accumulated_data[key] = result.data if result.data else {}
            if result.llm_interpretation:
                state.accumulated_data[f"{phase.name}_interpretation"] = result.llm_interpretation

            # ── Extract city / specialization from early phases ──────
            if phase_id == 0 and result.data:
                data = result.data if isinstance(result.data, dict) else {}
                if not state.client_city:
                    state.client_city = data.get("city", "")
                if not state.client_specialization:
                    state.client_specialization = data.get("specialization", "")

            # ── Notify: phase completed ──────────────────────────────
            if progress_callback:
                try:
                    progress_callback(
                        phase_id=phase_id,
                        phase_name=phase.name,
                        status=result.status.value,
                        message="",
                        duration_seconds=duration,
                    )
                except Exception as e:
                    logger.warning("progress_callback(completed) failed: %s", e)

            # ── Abort on critical failure ────────────────────────────
            if result.status == PhaseStatus.permanent_failure:
                if phase.contract.on_permanent_failure == "abort":
                    logger.error(
                        "Pipeline ABORTED at phase %d (%s): %s",
                        phase_id, phase.name, result.error_message,
                    )
                    break

            logger.info(
                "Phase %d/%d %s: %s (%.1fs)",
                phase_id + 1, len(PHASES), phase.name, result.status.value, duration,
            )

        return state

    # ── Pre-flight ────────────────────────────────────────────────────
    async def _pre_flight(self, state: PipelineState, url: str) -> None:
        """Determine city, specialization, and INN before phase execution."""
        if not url:
            return

        # Try to scrape the website for basic metadata
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc.replace("www.", "")

            # Use firecrawl or web_fetch for quick overview
            handler = self._tool_handlers.get("firecrawl_extract")
            if handler:
                try:
                    raw = await handler(
                        urls=[url],
                        prompt="Extract: clinic name, city, specialization, INN if present",
                    )
                    if isinstance(raw, str):
                        raw = json.loads(raw)
                    if isinstance(raw, dict):
                        data = raw.get("data", raw)
                        state.client_name = str(data.get("clinic_name", state.client_name or ""))
                        state.client_city = str(data.get("city", ""))
                        state.client_specialization = str(data.get("specialization", ""))
                        state.client_inn = str(data.get("inn", ""))
                except Exception:
                    pass
        except Exception as e:
            logger.warning("Pre-flight failed: %s", e)

    # ── Phase executor ────────────────────────────────────────────────
    async def _execute_phase(self, phase: Phase, state: PipelineState) -> PhaseResult:
        """Execute a single phase with retry logic.

        Calls the tool handlers listed in phase.tools, collects results,
        and returns a PhaseResult with status and data.
        """
        contract = phase.contract
        result = PhaseResult(status=PhaseStatus.running)
        collected: dict[str, Any] = {}

        last_error: str | None = None
        max_attempts = 1 + contract.max_retries

        for attempt in range(max_attempts):
            try:
                for tool_name in phase.tools:
                    handler = self._tool_handlers.get(tool_name)
                    if handler is None:
                        logger.warning("Phase %s: tool %s not found in handlers", phase.name, tool_name)
                        continue

                    try:
                        tool_result = await asyncio.wait_for(
                            self._call_tool(handler, tool_name, state),
                            timeout=contract.timeout,
                        )
                        collected[tool_name] = tool_result
                    except asyncio.TimeoutError:
                        logger.warning("Phase %s: tool %s timed out after %ds",
                                       phase.name, tool_name, contract.timeout)
                        if contract.max_retries > 0 and attempt < max_attempts - 1:
                            continue
                        result.status = PhaseStatus.timed_out
                        result.error_message = f"Tool {tool_name} timed out after {contract.timeout}s"
                        return result

                # All tools succeeded
                break

            except Exception as e:
                last_error = str(e)
                logger.warning("Phase %s attempt %d/%d failed: %s",
                               phase.name, attempt + 1, max_attempts, last_error)
                if contract.retry_on_key_exhaustion and "exhausted" in last_error.lower():
                    # Try key rotation
                    try:
                        from app.file_guard import get_key_rotator
                        rotator = get_key_rotator()
                        if rotator:
                            rotated = rotator()
                            if rotated:
                                logger.info("Key rotated, retrying phase %s", phase.name)
                                continue
                    except Exception:
                        pass
                if attempt < max_attempts - 1:
                    await asyncio.sleep(2)
                else:
                    result.status = PhaseStatus.tool_failed
                    result.error_message = last_error
                    return result

        # ── Determine final status ───────────────────────────────────
        if collected:
            result.data = collected
            # Check if data is meaningful or just empty
            has_data = any(
                v and (not isinstance(v, dict) or v)
                for v in collected.values()
            )
            if has_data:
                result.status = PhaseStatus.completed
            elif contract.allow_no_data:
                result.status = PhaseStatus.no_data
                result.error_message = "No data found (allowed)"
            else:
                result.status = PhaseStatus.no_data
        else:
            if contract.allow_no_data:
                result.status = PhaseStatus.no_data
                result.error_message = "No tools produced data (allowed)"
            else:
                result.status = PhaseStatus.tool_failed
                result.error_message = last_error or "No tools executed"

        return result

    async def _call_tool(self, handler: Callable, tool_name: str, state: PipelineState) -> Any:
        """Call a tool handler with appropriate arguments based on tool name."""
        url = state.client_url
        city = state.client_city
        name = state.client_name
        inn = state.client_inn
        specialization = state.client_specialization

        # Route arguments based on tool expectations
        tool_args_map: dict[str, dict] = {
            "perplexity_search": {
                "query": f"клиника {name or ''} {city or ''} {specialization or ''} медицинский рынок конкуренты тренды",
            },
            "find_competitors": {
                "url": url,
                "client_name": name,
                "client_city": city,
                "client_revenue": state.accumulated_data.get("PERPLEXITY_result", {}).get("revenue"),
            },
            "run_ci_analysis": {
                "url": url,
                "client_name": name,
            },
            "run_pagespeed": {"url": url},
            "run_seo_audit": {"url": url},
            "run_tech_seo_audit": {"url": url},
            "run_review_platforms": {"url": url, "client_name": name},
            "run_content_analysis": {"url": url},
            "run_hh_analysis": {"url": url, "client_name": name},
            "find_doctor_handles": {"url": url, "client_name": name},
            "run_doctor_dossiers": {"url": url, "client_name": name},
            "run_instagram_content": {"url": url, "client_name": name},
            "run_smi_mentions": {"url": url, "client_name": name},
            "web_search": {
                "query": f"пациенты {specialization or 'клиника'} {city or ''} отзывы форум боли страхи",
            },
            "find_company_financials": {
                "url": url,
                "inn": inn,
                "client_name": name,
            },
            "run_content_gaps": {"url": url},
            "generate_html_report": {
                "client_url": url,
                "client_name": name,
                "session_hash": state.session_id[:8] if state.session_id else "",
            },
            "publish_scout_report": {
                "session_id": state.session_id,
                "client_name": name,
            },
        }

        args = tool_args_map.get(tool_name, {"url": url})
        try:
            result = await handler(**args)
            return result
        except TypeError:
            # Fallback: try with just url
            try:
                return await handler(url=url)
            except Exception:
                # Last resort: try with client_name
                try:
                    return await handler(url=url, client_name=name)
                except Exception:
                    raise
