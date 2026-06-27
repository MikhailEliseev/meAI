"""run_three_pass — main entry point for the 3-pass orchestrator cycle.

Per Phase 2 RESEARCH.md Section 5.2 — Option 2: orchestrator-first.
Per Plan 02-02 Task 1: this module wires Pass 1 (Collect), Pass 2
(Gap-analyze), and Pass 3 (Fill+Assemble) into a single sequential flow.
Each pass is a separate ``AIAgent.run_conversation()`` call on the SAME
``session_id`` — the LLM's SQLite-backed history from Pass 1 is visible
during Pass 2, and so on. This is what makes the cycle "3 distinct
passes" rather than one mega-prompt (RESEARCH.md design decision 1).

Per Phase 3 / D-01..03: between Pass 1 and Pass 2 a niche-detection
mini-call runs. It uses the same AIAgent session as Pass 1, returns a
structured ``{instagram_critical, niche, reason}`` verdict, and populates
``state.niche`` (and ``state.collected_data["niche_detection"]`` with the
full verdict) for downstream consumption. Plan 03-03 will use
``state.niche`` to enforce the mandatory Instagram rule in Pass 2.

Per QC-02: QC gate between Pass 2 and Pass 3 — SOFT (warning only), does
NOT block Pass 3 from running. If coverage < 80% Pass 3 receives the
missing items list and is asked to fill them. If Pass 3 cannot fill an
item, the HTML report shows it as "данные недоступны" with the reason
(per ORC-04 honest-data principle).

Per QC-03: final coverage report (as dict) saved in
``state.collected_data["coverage_report_final"]`` for HTML rendering.

Per ORC-05: PipelineEngine fallback is wired at the ``agent_wrapper.py``
level (Task 2 of plan 02-02), NOT here. If ``run_three_pass`` raises,
the caller in ``run_agent_sync`` / ``run_agent`` catches it and falls
back to the existing PRESALE path.

Per Phase 3 / D-05 + D-08: the QC gate now applies niche-conditional
logic for Instagram item 5 via the ``_apply_niche_conditional_coverage``
helper. The helper runs BOTH after the Pass 2 calc_coverage AND after
the final (post-Pass 3) calc_coverage. Three branches:
  - Critical niche (plastic_surgery, cosmetology): HARD FAIL override —
    if item 5 is missing, force status='FAIL' regardless of filled count.
  - Non-critical niche: drop item 5 from total (17 vs 18 after Phase 4
    expansion), populate not_applicable_items, filter missing_items to
    exclude id==5, recompute coverage_pct.
  - Unknown niche: return report unchanged (safe fallback).
This is the runtime enforcement of what Plan 03-03 enforced at the
prompt level — the LLM is instructed to FAIL itself, but this helper
catches any LLM deviation.
"""

import logging
from dataclasses import asdict
from datetime import datetime, timezone

from app.orchestrator.coverage_reporter import (
    CoverageReport,
    calc_coverage,
    format_coverage_text,
)
from app.orchestrator.states import (
    OrchestratorState,
    PASS_COLLECT,
    PASS_GAP_ANALYZE,
    PASS_FILL_ASSEMBLE,
)

logger = logging.getLogger(__name__)


def _apply_niche_conditional_coverage(
    report: CoverageReport, niche: str,
) -> CoverageReport:
    """Apply niche-conditional logic to a CoverageReport (Phase 3 / D-05 + D-08).

    Three branches:

    - **Critical niche** (``plastic_surgery``, ``cosmetology``): hard-FAIL
      override (D-05). If item 5 is missing or absent from
      ``report.filled_items``, force ``status='FAIL'`` regardless of the
      number of other items filled. This is the runtime enforcement of
      the Instagram-mandatory rule for Instagram-critical niches — the
      prompt layer (Plan 03-03) tells the LLM to FAIL; this layer
      catches any LLM deviation.
    - **Non-critical niche**: conditional total (D-08). Drop item 5 from
      the effective total (17 vs 18 after Phase 4 expansion), populate
      ``report.not_applicable_items`` with a single entry for item 5,
      filter ``missing_items`` to exclude ``id == 5``, recompute
      coverage_pct with the new denominator, and re-evaluate PASS/FAIL
      against :data:`PASS_THRESHOLD`.
    - **Unknown niche**: return the input report unchanged. When the
      mini-call failed (state.niche == "unknown") we do NOT apply any
      override — safer to fall through to the original LLM-derived
      coverage than to risk a false hard-FAIL or a false item-5-drop.

    Args:
        report: The CoverageReport returned by :func:`calc_coverage`.
        niche: The niche verdict string from ``state.niche``. One of
            ``"plastic_surgery"``, ``"cosmetology"`` (critical),
            ``"dental"``, ``"general_medicine"``, ``"other"``
            (non-critical), or ``"unknown"`` (mini-call failed).

    Returns:
        The same ``report`` instance, mutated in place with any niche
        conditional adjustments. Returning the same object preserves
        identity for callers that want to compare before/after.
    """
    from app.orchestrator.qc_checklist import (
        PASS_THRESHOLD,
        applicable_items,
        is_niche_instagram_critical,
    )

    if niche == "unknown":
        logger.debug(
            "Niche conditional: niche=unknown — returning report unchanged "
            "(safe fallback)"
        )
        return report

    if is_niche_instagram_critical(niche):
        # Hard-FAIL override (D-05): Instagram-critical niche must have
        # item 5 filled. If not, force FAIL regardless of other items.
        # Item 5 is "filled" iff id 5 in filled_items and not in
        # missing_items. The LLM may have marked it missing (honest),
        # partial, or absent entirely — all of those trigger override.
        item5_filled = (
            5 in report.filled_items
            and 5 not in [m.get("id") for m in report.missing_items]
        )
        if not item5_filled:
            report.status = "FAIL"
            # Ensure item 5 appears in missing_items (synthetic entry if
            # absent) — Pass 3 will see it in missing_for_pass3 and try
            # to fill it on the next round.
            if 5 not in [m.get("id") for m in report.missing_items]:
                report.missing_items.append({
                    "id": 5,
                    "name": "Instagram analysis for cosmetology/plastic",
                    "reason": (
                        "Instagram-critical niche but run_instagram_content "
                        "not called in Pass 1"
                    ),
                    "detail": "",
                })
            logger.warning(
                "QC HARD FAIL override: niche=%s is Instagram-critical but "
                "item 5 missing — forcing coverage=FAIL (filled=%d/%d)",
                niche, len(report.filled_items), report.total_items,
            )
        else:
            logger.info(
                "Niche conditional: niche=%s critical, item 5 filled — no override",
                niche,
            )
        return report

    # Non-critical niche — conditional total (D-08).
    applicable_total = len(applicable_items(niche))  # 14 for non-critical
    not_applicable_entries: list[dict] = []
    # Item 5 is the only conditional item per Plan 03-03 Task 1.
    applicable_ids = [a["id"] for a in applicable_items(niche)]
    if 5 not in applicable_ids:
        not_applicable_entries.append({
            "id": 5,
            "name": "Instagram analysis for cosmetology/plastic",
            "reason": f"not_applicable for non-critical niche ({niche})",
        })

    # Filter missing_items to exclude id==5 (it's not_applicable, not
    # missing — Plan 03-05 HTML renders these distinctly).
    filtered_missing = [
        m for m in report.missing_items if m.get("id") != 5
    ]
    # Recompute coverage with the new total. filled_count stays the
    # same — item 5 was never in filled_items for non-critical niches
    # (LLM is told to mark it not_applicable in Pass 2 per Plan 03-03).
    filled_count = len(report.filled_items)
    new_pct = filled_count / applicable_total if applicable_total else 0.0
    new_status = "PASS" if new_pct >= PASS_THRESHOLD else "FAIL"

    report.total_items = applicable_total
    report.missing_items = filtered_missing
    report.not_applicable_items = not_applicable_entries
    report.coverage_pct = new_pct
    report.status = new_status

    logger.info(
        "QC niche-conditional: niche=%s, applicable_total=%d (item 5 dropped), "
        "coverage=%.1f%% — %s",
        niche, applicable_total, new_pct * 100, new_status,
    )
    return report


async def run_three_pass(
    session_id: str,
    client_url: str,
    client_name: str = "",
    mode: str = "PRESALE",
    chat_id: int = 0,
) -> OrchestratorState:
    """Run the 3-pass cycle: Collect → Gap-analyze → Fill+Assemble.

    Args:
        session_id: Chat session ID — reused across all 3 passes so the
            AIAgent's conversation history persists between passes.
        client_url: Clinic URL to research.
        client_name: Optional clinic name.
        mode: Agent mode (default "PRESALE" — orchestrator is wired for
            PRESALE in ``agent_wrapper.py``).
        chat_id: Telegram chat_id (0 = not Telegram).

    Returns:
        OrchestratorState with ``pass_status`` filled for all 3 passes.
        Check ``state.is_complete()`` / ``state.error_message`` for outcome.
    """
    state = OrchestratorState(
        session_id=session_id,
        client_url=client_url,
        client_name=client_name,
        mode=mode,
        chat_id=chat_id,
        started_at=datetime.now(timezone.utc).isoformat(),
    )

    logger.info(
        "Orchestrator: starting 3-pass cycle for %s (session=%s, mode=%s)",
        client_url, session_id, mode,
    )

    # ── Pass 1: Collect ─────────────────────────────────────────────────
    from app.orchestrator.pass_collect import run_pass_collect
    state = await run_pass_collect(state)

    if state.pass_status.get(PASS_COLLECT) != "completed":
        logger.error(
            "Orchestrator: aborting after Pass 1 — status=%s, error=%s",
            state.pass_status.get(PASS_COLLECT),
            state.error_message,
        )
        state.completed_at = datetime.now(timezone.utc).isoformat()
        return state

    # ── Niche detection mini-call (Phase 3 / D-01..03) ──────────────────
    # Short LLM call that decides if this clinic is Instagram-critical.
    # Uses the SAME AIAgent session as Pass 1 so the LLM sees collected
    # context. Returns {instagram_critical, niche, reason}. On ANY failure
    # the detector returns a fallback dict (instagram_critical=False,
    # niche="unknown") — we do NOT wrap this call in try/except, the
    # detector owns its own failure path.
    from app.orchestrator.niche_detector import detect_instagram_critical_niche
    niche_verdict = await detect_instagram_critical_niche(state)
    state.niche = niche_verdict.get("niche", "unknown")
    state.collected_data["niche_detection"] = niche_verdict
    logger.info(
        "Orchestrator: niche detection for %s — instagram_critical=%s, "
        "niche=%s, reason=%s",
        state.client_url,
        niche_verdict.get("instagram_critical"),
        niche_verdict.get("niche"),
        niche_verdict.get("reason"),
    )

    # ── Pass 2: Gap-analyze ─────────────────────────────────────────────
    # Lazy import: pass_gap_analyze is implemented in Task 2 of plan 02-02.
    # Importing at module top would have created a NameError in Task 1
    # before the file existed. Keeping the lazy import even after Task 2
    # so the wiring stays explicit and testable.
    from app.orchestrator.pass_gap_analyze import run_pass_gap_analyze
    state = await run_pass_gap_analyze(state)

    if state.pass_status.get(PASS_GAP_ANALYZE) != "completed":
        logger.warning(
            "Orchestrator: Pass 2 status=%s, continuing to Pass 3 (best-effort) "
            "with gap_report=%s",
            state.pass_status.get(PASS_GAP_ANALYZE),
            state.gap_report,
        )

    # ── QC gate (soft, per QC-02) ───────────────────────────────────────
    # Compute coverage after Pass 2. If < 80% → Pass 3 receives the
    # missing items list and is asked to fill them. SOFT gate: warning
    # only — we never block Pass 3, the report is always produced (with
    # honest "данные недоступны" markers for items that can't be filled).
    coverage_after_p2 = calc_coverage(state.gap_report)
    # Phase 3 / D-05 + D-08 — apply niche-conditional logic (hard-FAIL
    # for critical + missing Instagram; conditional total for non-critical).
    # Helper is a no-op when niche == "unknown" (safe fallback).
    niche_for_coverage = state.niche or "unknown"
    coverage_after_p2 = _apply_niche_conditional_coverage(
        coverage_after_p2, niche_for_coverage,
    )
    state.collected_data["coverage_report_after_pass2"] = asdict(coverage_after_p2)
    logger.info(
        "QC gate after Pass 2: coverage=%.1f%%, status=%s, filled=%s, missing=%s",
        coverage_after_p2.coverage_pct * 100,
        coverage_after_p2.status,
        coverage_after_p2.filled_items,
        [m.get("id") for m in coverage_after_p2.missing_items],
    )
    if coverage_after_p2.status == "FAIL":
        logger.warning(
            "QC gate: coverage %.1f%% below 80%% threshold — Pass 3 will attempt "
            "to fill %d missing items",
            coverage_after_p2.coverage_pct * 100,
            len(coverage_after_p2.missing_items),
        )
        state.collected_data["missing_for_pass3"] = coverage_after_p2.missing_items
    else:
        logger.info(
            "QC gate: coverage already at PASS — Pass 3 will polish + generate HTML"
        )

    # ── Pass 3: Fill + Assemble ─────────────────────────────────────────
    from app.orchestrator.pass_fill_assemble import run_pass_fill_assemble
    state = await run_pass_fill_assemble(state)

    # ── Final coverage (post-Pass 3) ────────────────────────────────────
    # If Pass 3 successfully filled gaps, it should have updated
    # state.gap_report (we trust the LLM to mark items filled via its own
    # output, or — for the simpler implementation — leave it unchanged).
    # We recalc on the (possibly updated) gap_report. The result is the
    # FINAL coverage that gets rendered into the HTML report (QC-03).
    final_coverage = calc_coverage(state.gap_report)
    # Phase 3 / D-05 + D-08 — apply niche-conditional logic to final
    # coverage. Same helper as after Pass 2; for critical niches this
    # may force FAIL if Pass 3 didn't manage to fill item 5.
    final_coverage = _apply_niche_conditional_coverage(
        final_coverage, niche_for_coverage,
    )
    state.collected_data["coverage_report_final"] = asdict(final_coverage)
    logger.info(
        "Final QC coverage: %.1f%% — %s\n%s",
        final_coverage.coverage_pct * 100,
        final_coverage.status,
        format_coverage_text(final_coverage),
    )

    state.completed_at = datetime.now(timezone.utc).isoformat()

    # ── Programmatic HTML fallback ────────────────────────────────
    # If LLM didn't produce an HTML report (LLM may answer with text instead
    # of tool_call, or generate_html_report may fail on session_hash path),
    # we build one ourselves from state.collected_data. This guarantees the
    # orchestrator always produces an HTML artifact (per Phase 7 D-10).
    if not state.html_report_path:
        try:
            html_path = _build_fallback_html(state, client_url, client_name)
            if html_path:
                state.html_report_path = html_path
                logger.info(
                    "Orchestrator: programmatic HTML fallback saved to %s",
                    html_path,
                )
        except Exception as e:
            logger.exception("Orchestrator: HTML fallback failed: %s", e)

    logger.info(
        "Orchestrator: 3-pass cycle complete for %s — pass_status=%s, "
        "is_complete=%s",
        client_url, state.pass_status, state.is_complete(),
    )
    return state


def _build_fallback_html(state, client_url: str, client_name: str) -> str | None:
    """Build HTML report programmatically from state.collected_data.

    Used when LLM Pass 3 didn't successfully invoke generate_html_report.
    Extracts tool outputs from Pass 1 message history + builds a minimal
    but complete HTML via _build_report_html.
    """
    import json
    import os
    from datetime import datetime

    # Collect tool outputs from all passes' message history
    collected = {}
    pass_results = [
        state.collected_data.get("pass_collect_result"),
        state.collected_data.get("pass_gap_analyze_result"),
        state.collected_data.get("pass_fill_assemble_result"),
    ]
    for result in pass_results:
        if not result or not isinstance(result, dict):
            continue
        messages = result.get("messages", [])
        for msg in messages:
            content = msg.get("content", "")
            if not isinstance(content, list):
                continue
            for c in content:
                if not isinstance(c, dict):
                    continue
                if c.get("type") != "tool_result":
                    continue
                tool_content = c.get("content", "")
                if isinstance(tool_content, list):
                    for tc in tool_content:
                        if isinstance(tc, dict) and tc.get("type") == "text":
                            tool_content = tc.get("text", "")
                            break
                if not isinstance(tool_content, str):
                    continue
                # Try parse as JSON
                try:
                    parsed = json.loads(tool_content)
                    if isinstance(parsed, dict):
                        for k, v in parsed.items():
                            if k not in collected and v:
                                collected[k] = v
                except (json.JSONDecodeError, TypeError):
                    pass

    # Build minimal data dict for _build_report_html
    data = {
        "metadata": {
            "url": client_url,
            "company_name": client_name or "Клиника",
        },
        "collected_data": collected,
    }

    # Mix in LLM-generated sections from state.collected_data if any
    cd = state.collected_data or {}
    niche = cd.get("niche_detection", {}).get("niche", "")
    instagram_data = collected.get("instagram_data") or collected.get("run_instagram_content")
    coverage_metadata = cd.get("coverage_report_final")

    try:
        from app.tools.generate_html_report import _build_report_html
        html = _build_report_html(
            data,
            client_name or "AIM Presale Report",
            coverage_metadata=coverage_metadata,
            niche=niche,
            instagram_data=instagram_data,
        )
    except Exception as e:
        logger.exception("Orchestrator: _build_report_html failed: %s", e)
        return None

    if not html:
        return None

    # Save to /opt/data/memories/proposals/{slug}/proposal.html
    slug = (client_name or client_url or "report").replace("https://", "").replace("http://", "")
    slug = "".join(c if c.isalnum() or c == "-" else "-" for c in slug)[:60]
    proposals_dir = os.environ.get("PROPOSALS_DIR", "/opt/data/memories/proposals")
    target_dir = os.path.join(proposals_dir, slug)
    os.makedirs(target_dir, exist_ok=True)
    target = os.path.join(target_dir, "proposal.html")
    with open(target, "w", encoding="utf-8") as f:
        f.write(html)
    return target

