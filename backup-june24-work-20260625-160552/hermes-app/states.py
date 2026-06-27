"""OrchestratorState — in-memory state for one 3-pass run.

Per Phase 2 RESEARCH.md Section 5.2 — orchestrator-first.
Per Plan 02-02 design decision 5: OrchestratorState is a simple dataclass,
NOT persisted to SQLite. Long-term persistence flows through SessionDB via
the AIAgent's own conversation history. If a run crashes, it restarts from
scratch — same as PipelineEngine today.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


# Pass names used as keys in ``OrchestratorState.pass_status``
PASS_COLLECT = "collect"
PASS_GAP_ANALYZE = "gap_analyze"
PASS_FILL_ASSEMBLE = "fill_assemble"

_ALL_PASSES = (PASS_COLLECT, PASS_GAP_ANALYZE, PASS_FILL_ASSEMBLE)


@dataclass
class OrchestratorState:
    """In-memory state for a single 3-pass orchestrator run.

    Attributes:
        session_id: Chat session ID — reused across all 3 passes so the
            AIAgent's SQLite-backed conversation history persists between
            passes (the LLM "remembers" Pass 1 during Pass 2, etc.).
        client_url: URL of the clinic site being researched.
        client_name: Optional clinic name (filled in if known).
        mode: Agent mode — "PRESALE" by default. Orchestrator is wired for
            PRESALE in ``agent_wrapper.py`` (Task 2 of plan 02-02).
        chat_id: Telegram chat_id (0 = not Telegram).
        pass_status: Dict ``{pass_name: "pending"|"running"|"completed"|"failed"}``.
            Updated by each pass via :meth:`mark_pass`.
        collected_data: Dict with raw pass results. Keys:
            ``pass_collect_result``, ``pass_fill_assemble_result``.
        gap_report: Dict filled by Pass 2 (``{"items": [...], "summary": {...}}``).
            Empty until Pass 2 runs.
        html_report_path: Optional path/URL of generated HTML (filled by Pass 3
            if the LLM calls ``generate_html_report`` and we can extract path).
        started_at / completed_at: ISO-formatted UTC timestamps.
        error_message: Last error message from a failed pass (empty if none).
        niche: Instagram-criticality verdict from the mini-call between Pass 1
            and Pass 2 (per Phase 3 D-01..03). Values: "" (mini-call not yet
            run), "plastic_surgery" / "cosmetology" (instagram-critical=True),
            "dental" / "general_medicine" / etc. (instagram-critical=False),
            "unknown" (mini-call failed — Pass 2 should treat as non-critical
            to avoid false-hard-FAIL).
    """

    session_id: str
    client_url: str
    client_name: str = ""
    mode: str = "PRESALE"
    chat_id: int = 0
    pass_status: dict = field(default_factory=dict)
    collected_data: dict = field(default_factory=dict)
    gap_report: dict = field(default_factory=dict)
    html_report_path: str = ""
    started_at: str = ""
    completed_at: str = ""
    error_message: str = ""
    niche: str = ""

    def mark_pass(self, pass_name: str, status: str) -> None:
        """Update the status of a pass.

        Args:
            pass_name: One of ``collect``, ``gap_analyze``, ``fill_assemble``.
            status: ``pending`` | ``running`` | ``completed`` | ``failed``.
        """
        self.pass_status[pass_name] = status

    def is_complete(self) -> bool:
        """Return True only when all 3 passes have status "completed"."""
        return all(
            self.pass_status.get(name) == "completed"
            for name in _ALL_PASSES
        )


def utc_now_iso() -> str:
    """Return current UTC time as ISO-formatted string (helper for callers)."""
    return datetime.now(timezone.utc).isoformat()
