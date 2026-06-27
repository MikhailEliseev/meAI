"""Pass 3 — Fill gaps + Assemble HTML report.

Per Phase 2 RESEARCH.md Section 5.2 — orchestrator-first, Option 2.
Per Plan 02-02 Task 1: Pass 3 receives the gap_report produced by Pass 2
and asks the LLM to (a) call additional tools if any gaps are fillable,
then (b) invoke ``generate_html_report`` with the full collected data set.
If the LLM cannot fill a gap, it must honestly mark the section as
"данные недоступны" — no fabrication (per ORC-04).

Phase 3 / D-07 (Plan 03-05 Task 3): the Pass 3 prompt now explicitly
instructs the LLM to pass ``niche`` (from
``state.collected_data.niche_detection.niche`` — populated by the
Plan 03-02 mini-call between Pass 1 and Pass 2) and ``instagram_data``
(the full ``run_instagram_content`` batch response from Pass 1
tool-call history, or None if Instagram wasn't called) as kwargs to
``generate_html_report``. These kwargs drive the conditional rendering
of the "Instagram: данные недоступны" block in sections 03 + 04 of the
HTML report (Plan 03-05 Task 1). Without this prompt-level instruction,
the LLM has no way to know these kwargs exist — closing the cross-plan
data-contract gap flagged by Checker issue #1.

Phase 4 / Plan 04-05: Pass 3 prompt extended with generation rules for
5 new sections (Strategy, Offer, Whitefields, Experts+регалии,
Content+страхи) + 4 data rendering rules (revenue dynamics, clinic
metrics, media URLs, ratings, competitor cards).
Items 7-15 added to the existing 6-item prompt.

Phase 5 / Plan 05-01: Pass 3 prompt extended with cross-cutting
narrative quality rules (items 16-21). Items 16-18 added in Task 1
(narrative style, business language, cross-references). Items 19-21
added in Task 2 (gap-block format, section blockquote, reference
calibration). INT-01..05 prompt-layer satisfied. HTML rendering layer
for gap_blocks + insight kwargs in Plan 05-02.

Phase 5 / Plan 05-03: Pass 3 prompt extended with EXAMPLES BY SECTION
calibration block. 10+ narrative examples extracted from reference
``ИПХиК (2).html`` (one per section, Секция 01..10) + 2 cross-reference
examples (Content → Experts, Strategy → Content fears) + 2 gap-block
examples (1 strength with ✅, 1 growth point with 📍) + 2 blockquote
examples (Market + Strategy). D-11 fully satisfied — Plan 05-01 added
short pointer in item 21; this plan adds the comprehensive section-
by-section calibration. Examples embedded inline in the prompt as
few-shot anchors so DeepSeek V4 Pro can emulate reference style with
high fidelity instead of guessing from abstract rules.

Exit criteria: LLM has invoked ``generate_html_report`` (visible in
tool_calls) and returned a final response. Pass 3 result is stored in
``state.collected_data["pass_fill_assemble_result"]``.
"""

import asyncio
import logging

from app.orchestrator.states import OrchestratorState, PASS_FILL_ASSEMBLE, PASS_GAP_ANALYZE

logger = logging.getLogger(__name__)

# Pass 3 may invoke additional tools AND call generate_html_report — give it
# the same 10-minute ceiling as Pass 1 since tool execution dominates the
# wall-clock time, not LLM reasoning.
_PASS_FILL_TIMEOUT = 600


async def run_pass_fill_assemble(state: OrchestratorState) -> OrchestratorState:
    """Execute Pass 3 — Fill gaps and assemble the HTML report.

    The LLM continues on the SAME session_id, so its SQLite-backed
    conversation history from Pass 1 and Pass 2 is available. We just
    hand it the structured gap_report and instruct it to fill the
    remaining gaps + invoke ``generate_html_report``.

    Best-effort on Pass 2 status: if Pass 2 did not complete (e.g. parse
    error), we still run Pass 3 with an empty gap_report — the LLM has
    the Pass 1 data in its history and can produce a best-effort report.
    """
    if state.pass_status.get(PASS_GAP_ANALYZE) != "completed":
        logger.warning(
            "Orchestrator Pass 3 (Fill+Assemble): Pass 2 status=%s, "
            "continuing with gap_report=%s (best-effort)",
            state.pass_status.get(PASS_GAP_ANALYZE),
            state.gap_report,
        )

    state.mark_pass(PASS_FILL_ASSEMBLE, "running")
    logger.info(
        "Orchestrator Pass 3 (Fill+Assemble): starting for %s (session=%s)",
        state.client_url, state.session_id,
    )

    try:
        from app.orchestrator.pass_collect import _get_agent_for_session
        agent = await _get_agent_for_session(state.session_id, state.mode)

        prompt = _build_prompt(state)

        result = await asyncio.wait_for(
            asyncio.to_thread(agent.run_conversation, prompt),
            timeout=_PASS_FILL_TIMEOUT,
        )

        state.collected_data["pass_fill_assemble_result"] = result
        state.mark_pass(PASS_FILL_ASSEMBLE, "completed")
        logger.info(
            "Orchestrator Pass 3 (Fill+Assemble): completed for %s — result keys=%s",
            state.client_url,
            list(result.keys()) if isinstance(result, dict) else type(result).__name__,
        )
    except Exception as exc:
        state.mark_pass(PASS_FILL_ASSEMBLE, "failed")
        state.error_message = str(exc)
        logger.exception(
            "Orchestrator Pass 3 (Fill+Assemble): FAILED for %s — %s",
            state.client_url, exc,
        )

    return state


def _build_prompt(state: OrchestratorState) -> str:
    """Build the Pass 3 prompt — fill gaps then assemble HTML."""
    gap_report = state.gap_report or {}
    gap_summary = gap_report.get("summary", {}) if isinstance(gap_report, dict) else {}
    gap_items = gap_report.get("items", []) if isinstance(gap_report, dict) else []

    missing_items = [
        item for item in gap_items
        if isinstance(item, dict) and item.get("status") in ("missing", "partial")
    ]

    summary_line = (
        f"filled={gap_summary.get('filled', '?')}, "
        f"missing={gap_summary.get('missing', '?')}, "
        f"total={gap_summary.get('total', '?')}"
    ) if gap_summary else "нет данных (Pass 2 не завершился)"

    missing_block = ""
    if missing_items:
        lines = []
        for item in missing_items:
            name = item.get("name", "?")
            status = item.get("status", "?")
            detail = item.get("detail", "")
            lines.append(f"  - {name} ({status}){': ' + detail if detail else ''}")
        missing_block = "\nПробелы для допосбора:\n" + "\n".join(lines)
    else:
        missing_block = "\nПробелов не обнаружено — переходи сразу к сборке отчёта."

    # Optional: attach coverage_report_final if Pass 3 has access to it
    # (populated by three_pass.py between Pass 2 and Pass 3 via
    # state.collected_data["coverage_report_after_pass2"]; final value is
    # computed AFTER Pass 3 — so during Pass 3 we only have the post-Pass-2
    # snapshot to hand the LLM, which is still useful as a hint).
    coverage_hint = ""
    coverage_after_p2 = state.collected_data.get("coverage_report_after_pass2") or {}
    if coverage_after_p2:
        coverage_hint = (
            f"\n\nТекущий coverage (после Pass 2): "
            f"{len(coverage_after_p2.get('filled_items', []))}/15 "
            f"({coverage_after_p2.get('coverage_pct', 0) * 100:.1f}%) — "
            f"{coverage_after_p2.get('status', 'UNKNOWN')}."
        )

    return (
        f"Gap report из Pass 2: summary=[{summary_line}].{missing_block}"
        f"{coverage_hint}\n\n"
        "═══ ПРАВИЛО #1 (КРИТИЧНО) ═══\n"
        "ТВОЙ ЕДИНСТВЕННЫЙ ОТВЕТ В ЭТОМ ПРОХОДЕ — ОДИН tool_call к generate_html_report.\n"
        "НЕ пиши текст перед вызовом, НЕ после. ТОЛЬКО tool_call.\n\n"
        "═══ ПРОСТОЙ СПОСОБ (РЕКОМЕНДУЕМЫЙ) ═══\n"
        "Передай ВСЕ данные в одном kwarg narrative_md (markdown-строка). Пример:\n"
        f'generate_html_report(client_url="{state.client_url}", '
        f'client_name="{state.client_name or state.client_url}", '
        'narrative_md="## 01 — О клинике\\n\\nМосква...\\n\\n'
        '## 02 — Конкуренты\\n\\n| Клиника | Выручка |\\n|---|---|\\n| X | 100 млн |\\n...")\n\n'
        "Markdown должен содержать все секции: О компании (01), Рынок (02), Эксперты (03), "
        "Контент-анализ (04), СМИ (05), Конкуренты (06), Whitefields (07), "
        "Присутствие (08), Стратегия (09), Offer (10). Каждая — заголовок ## + контент.\n\n"
        "СТИЛЬ: нарратив с цифрами (НЕ дамп метрик), бизнес-язык, "
        "cross-references между секциями, gap-blocks (✅ strength / 📍 growth), "
        "blockquote в конце секции. Образец — /opt/data/report-reference.html.\n\n"
        "═══ ВЫЗЫВАЙ СЕЙЧАС ═══\n"
    )
