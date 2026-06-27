"""Pass 2 — Gap-analyze with full 18-item QC coverage checklist.

Per Phase 2 RESEARCH.md Section 5.4 — QC checklist (15 items at Phase 2).
Per Plan 02-03 Task 2: this Pass 2 uses the FULL 15-item checklist from
qc_checklist.py (replacing the minimal 5-item checklist that shipped in
Plan 02-02). For each item the LLM must self-assess:
  - status: 'filled' | 'partial' | 'missing' | 'not_applicable'
  - detail: 1 sentence describing what exists or what's lacking
  - reason: for partial/missing, WHY (tool not called, returned error,
    source has no data)

Phase 4 / Plan 04-04 expansion: checklist grew from 15 to 18 items
(items 16 clinic_metrics, 17 ratings, 18 expert_regalia). Prompt
template references 18 items, fallback defaults to 18 total.

The LLM is instructed to output a strict JSON (no markdown fences, no
commentary) so we can parse it back into ``state.gap_report`` for Pass 3
and compute coverage % via coverage_reporter.calc_coverage (ORC-03, QC-03).

Per ORC-04 honest-data principle: missing items MUST be marked as missing
with a reason — never fabricated. The prompt explicitly says so.

Phase 3 / Plan 03-03 (D-05 + D-08): The Pass 2 prompt is now niche-aware.
The template carries a ``{niche_instruction}`` placeholder populated at
call time based on ``state.niche`` (mini-call output from Plan 03-02).
The prompt encodes the Instagram HARD FAIL rule (D-05):
  - critical niche + run_instagram_content NOT called  -> item 5 'missing',
    coverage = FAIL even if 14/15 other items are filled.
  - critical niche + run_instagram_content called but 'no data'
    -> item 5 'filled' with reason (D-06 legitimate no-data).
  - non-critical niche -> item 5 'not_applicable', not counted in
    filled/missing (D-08 conditional item).
Runtime hard-FAIL override + conditional-total recomputation live in
Plan 03-06; this layer is prompt-level only.

Phase 3 / Plan 03-04 (D-10 adaptive cohort): The Pass 2 prompt now
includes adaptive-cohort evaluation guidance for items 4 (Experts),
6 (Content themes), and 7 (Content gaps). When the Instagram-active
cohort (from batch response ``top_by_followers``) differs from the
site-top-5 cohort (tituled experts without Instagram), the LLM must
apply cohort-aware rules: item 4 filled if >=3 doctors with ФИО +
(regalia OR Instagram metrics); item 6 filled if >=3 themes from
any Instagram-active doctor (not necessarily site-top-5); item 7
filled if >=2 gaps with severity from any analyzed profile's
content_gaps field. This mirrors the Pass 1 adaptive top-5 rule
(D-10) and accounts for the realistic scenario where a clinic's
top-5 site doctors don't have Instagram but other doctors do.

Phase 4 / Plan 04-04: Checklist expanded from 15 to 18 items.
Items 16 (clinic_metrics), 17 (ratings), 18 (expert_regalia) added.
Template references 18 items. Fallback report defaults to 18 total.
"""

import asyncio
import json
import logging
import re

from app.orchestrator.qc_checklist import (
    QC_CHECKLIST,
    render_checklist_for_llm,
)
from app.orchestrator.states import OrchestratorState, PASS_GAP_ANALYZE

logger = logging.getLogger(__name__)

# Pass 2 is just LLM self-reflection — no tool dispatch. 240s ceiling
# (up from 180s in 02-02) because 18 items take longer than 5 for the
# LLM to evaluate each one against its pass criterion.
_PASS_GAP_TIMEOUT = 240

# Regex to extract the first {...} JSON block from an LLM response. LLMs
# sometimes wrap JSON in markdown fences or add prose around it. re.DOTALL
# lets the match span newlines (the JSON is multi-line).
_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)

# Full 18-item checklist prompt. Plan 02-03 Task 2 swapped this in for the
# minimal 5-item prompt that shipped in 02-02. Phase 3 / Plan 03-03 adds
# the {niche_instruction} placeholder (D-05 + D-08) and the not_applicable
# status for non-critical-niche item 5. Phase 4 / Plan 04-04 expands from
# 15 to 18 items (clinic_metrics, ratings, expert_regalia).
_CHECKLIST_PROMPT_TEMPLATE = """Клиника: {client_url}

Сравни собранные в Pass 1 данные с 18-item QC checklist:
{checklist_render}

{niche_instruction}

Для КАЖДОГО пункта: status (filled/partial/missing/not_applicable) + detail (1 предложение что есть/не хватает) + reason (для missing/partial).

INSTAGRAM (пункт 5): critical-niche + не вызван → status='missing' (HARD FAIL). Critical + вызван но no data → 'filled'. Non-critical → 'not_applicable'.

ADAPTIVE: пункт 4 filled если ≥3 врачей с ФИО + регалии ИЛИ Instagram-метрики. Пункт 6/7 filled если ≥3 темы/gaps для Instagram-active врачей.

ВЫВЕДИ ТОЛЬКО JSON (без markdown):
{{"items": [{{"id": 1, "status": "...", "detail": "...", "reason": ""}}, ...], "summary": {{"filled": N, "partial": P, "missing": M, "not_applicable": NA, "total": 18}}}}

Честно: нет данных → missing с reason. Только валидный JSON.
"""


async def run_pass_gap_analyze(state: OrchestratorState) -> OrchestratorState:
    """Execute Pass 2 — Gap analysis with minimal 5-item checklist.

    Sends the checklist prompt to the same AIAgent session used in Pass 1
    so the LLM can inspect its own tool-call history. The response must be
    a JSON object matching the schema documented in the prompt. On parse
    failure we fall back to a ``parse_error`` report so Pass 3 still has
    SOMETHING to work with — Pass 3 handles missing/empty gap_report
    gracefully (best-effort mode).
    """
    state.mark_pass(PASS_GAP_ANALYZE, "running")
    logger.info(
        "Orchestrator Pass 2 (Gap-analyze): starting for %s (session=%s)",
        state.client_url, state.session_id,
    )

    try:
        from app.orchestrator.pass_collect import _get_agent_for_session
        from app.orchestrator.qc_checklist import is_niche_instagram_critical
        agent = await _get_agent_for_session(state.session_id, state.mode)

        niche = state.niche or "unknown"
        if is_niche_instagram_critical(niche):
            niche_instruction = (
                f"НИША: {niche} — Instagram-critical=True. "
                "Пункт 5 (Instagram analysis) ОБЯЗАТЕЛЕН. "
                "Если run_instagram_content не вызван — пункт 5 'missing' "
                "(HARD FAIL). Если вызван, но 'no data' — пункт 5 'filled' "
                "с reason (D-06). См. правила ниже."
            )
        elif niche == "unknown":
            niche_instruction = (
                "НИША: unknown (mini-call failed). Применяй правило: если "
                "в собранных данных есть признаки cosmetology / plastic "
                "surgery как ОСНОВНОГО профиля клиники — считай нишу "
                "Instagram-critical и применяй HARD FAIL правило для "
                "пункта 5. Если признаков нет — пункт 5 может быть "
                "'not_applicable'."
            )
        else:
            niche_instruction = (
                f"НИША: {niche} — Instagram-critical=False. "
                "Пункт 5 (Instagram analysis) — status='not_applicable'. "
                "Не считай этот пункт в filled/missing — только "
                "'not_applicable'."
            )

        prompt = _CHECKLIST_PROMPT_TEMPLATE.format(
            client_url=state.client_url,
            checklist_render=render_checklist_for_llm(),
            niche_instruction=niche_instruction,
        )

        result = await asyncio.wait_for(
            asyncio.to_thread(agent.run_conversation, prompt),
            timeout=_PASS_GAP_TIMEOUT,
        )

        # Extract LLM text from the result dict — same field path used in
        # agent_wrapper.run_agent_sync (final_response -> response -> content).
        reply_text = _extract_reply_text(result)

        parsed = _parse_gap_json(reply_text)
        state.gap_report = parsed
        state.collected_data["pass_gap_analyze_result"] = {
            "raw_response": reply_text,
            "parsed": parsed,
        }
        state.mark_pass(PASS_GAP_ANALYZE, "completed")
        logger.info(
            "Orchestrator Pass 2 (Gap-analyze): completed for %s — summary=%s",
            state.client_url,
            parsed.get("summary") if isinstance(parsed, dict) else "n/a",
        )
    except Exception as exc:
        state.mark_pass(PASS_GAP_ANALYZE, "failed")
        state.error_message = str(exc)
        # Still populate gap_report so Pass 3 has a deterministic shape to read.
        state.gap_report = {
            "items": [],
            "summary": {"filled": 0, "missing": 0, "total": 18},
            "error": str(exc),
        }
        logger.exception(
            "Orchestrator Pass 2 (Gap-analyze): FAILED for %s — %s",
            state.client_url, exc,
        )

    return state


def _extract_reply_text(result) -> str:
    """Pull the assistant's final text from an AIAgent.run_conversation() result.

    Mirrors the field-path fallback used in ``agent_wrapper.run_agent_sync``:
    final_response -> response -> content -> str(result).
    """
    if not isinstance(result, dict):
        return str(result)

    for key in ("final_response", "response", "content"):
        val = result.get(key)
        if isinstance(val, str) and val.strip():
            return val
        if isinstance(val, dict):
            inner = val.get("content") or val.get("text")
            if isinstance(inner, str) and inner.strip():
                return inner
    return str(result)


def _parse_gap_json(reply_text: str) -> dict:
    """Parse the LLM's JSON gap-report from ``reply_text``.

    Tries direct ``json.loads`` first (LLM followed instructions). Falls
    back to regex extraction of the first ``{...}`` block (LLM added
    prose around the JSON). On total failure returns a deterministic
    fallback dict so Pass 3 always has a dict to read.
    """
    if not reply_text:
        return _fallback_report("empty_response", "")

    # Strip markdown code fences if present (```json ... ```).
    cleaned = re.sub(r"^```(?:json)?\s*", "", reply_text.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())

    # Attempt 1: direct parse.
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict) and "items" in parsed:
            _ensure_summary(parsed)
            return parsed
    except json.JSONDecodeError:
        pass

    # Attempt 2: regex-extract first {...} block, then parse.
    match = _JSON_BLOCK_RE.search(reply_text)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, dict):
                if "items" not in parsed:
                    parsed = {"items": [], "summary": parsed}
                _ensure_summary(parsed)
                return parsed
        except json.JSONDecodeError as exc:
            return _fallback_report(f"json_decode_error: {exc}", reply_text)

    return _fallback_report("no_json_found", reply_text)


def _ensure_summary(report: dict) -> None:
    """Make sure ``report["summary"]`` has filled/missing/not_applicable/total keys.

    Per Phase 3 / Plan 03-03 (D-08): ``not_applicable`` items are counted
    separately so they do not inflate the missing count. Downstream
    coverage math (Plan 03-06 ``_apply_niche_conditional_coverage``)
    re computes the effective total as ``total - not_applicable`` for
    non-critical niches.
    """
    items = report.get("items", [])
    if not isinstance(items, list):
        report["items"] = []
        items = []

    filled = sum(
        1 for it in items
        if isinstance(it, dict) and it.get("status") == "filled"
    )
    missing = sum(
        1 for it in items
        if isinstance(it, dict) and it.get("status") in ("missing", "partial")
    )
    not_applicable = sum(
        1 for it in items
        if isinstance(it, dict) and it.get("status") == "not_applicable"
    )
    report.setdefault("summary", {})
    report["summary"].setdefault("filled", filled)
    report["summary"].setdefault("missing", missing)
    report["summary"].setdefault("not_applicable", not_applicable)
    report["summary"].setdefault("total", len(items) if items else 18)


def _fallback_report(reason: str, raw: str) -> dict:
    """Build a deterministic gap_report when JSON parsing fails."""
    return {
        "items": [],
        "summary": {
            "filled": 0,
            "missing": 18,
            "not_applicable": 0,
            "total": 18,
        },
        "parse_error": reason,
        "raw_response": raw[:1000] if raw else "",
    }
