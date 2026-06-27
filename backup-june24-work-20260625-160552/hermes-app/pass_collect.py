"""Pass 1 — Collect.

Per Phase 2 RESEARCH.md Section 5.2 — orchestrator-first, Option 2.
Per Plan 02-02 Task 1: Pass 1 lets the LLM act as a "free artist" — it
calls any relevant tools from the full registry of 49 (per ORC-02) without
a hard-coded sequence. The orchestrator does NOT wire individual tools;
it just sends a prompt and lets the AIAgent dispatch via its registry.

Exit criteria: LLM has called the tools it deemed relevant and returned a
final response. Pass 1 result is stored in ``state.collected_data`` for
Pass 2's gap analysis.

Phase 3 / Plan 03-03 (D-04 + D-06): The Pass 1 prompt is now niche-aware.
For Instagram-critical niches (cosmetology / plastic_surgery per D-03, as
detected by the mini-call in Plan 03-02) the prompt makes Instagram
analysis MANDATORY and enforces doctor-discovery ordering:
    1. find_doctor_handles FIRST (returns 8-10 doctor Instagram handles)
    2. run_instagram_content SECOND (batch call with the handles list)
    3. On 'no data' for a handle — retry with alternative handles (D-06)
For non-critical niches the prompt tells the LLM Instagram is optional
and not to waste tokens on it. The runtime hard-FAIL override lives in
Plan 03-06; this layer is prompt-only.

Phase 3 / Plan 03-04 (D-10 + D-11): The Pass 1 prompt is now further
augmented with the adaptive top-5 cohort selection rule. The batch
response from run_instagram_content includes a "top_by_followers" array
(doctors sorted by follower count — who actually maintains their social
media). Site-top-5 often == tituled experts (КМН, professors) WITHOUT
Instagram; Instagram-active-top-5 may be doctors #6-#10 on the site.
Both cohorts are legitimate: section 03 (Experts) shows both with
regalia + metrics; section 04 (Content Analysis) uses only the
Instagram-active cohort (no content to analyze for doctors without
Instagram). Batch size 8-10 (D-11) covers both cohorts in one call.
"""

import asyncio
import logging

from app.orchestrator.states import OrchestratorState, PASS_COLLECT

logger = logging.getLogger(__name__)

# 10 minutes — matches the ThreadPoolExecutor ceiling used by run_agent_sync
# for the synchronous AIAgent path. DeepSeek V4 Pro streams break at ~120s;
# wrapping in asyncio.to_thread + wait_for means the orchestrator never
# hangs the FastAPI event loop even when a tool call stalls.
_PASS_COLLECT_TIMEOUT = 600


async def run_pass_collect(state: OrchestratorState) -> OrchestratorState:
    """Execute Pass 1 — Collect data for the clinic URL.

    Sends a structured prompt to the AIAgent that tells it to act as a
    free artist: call any relevant tools from its catalogue (49 available
    in aim-operations toolset), work in parallel where possible, and NOT
    generate HTML yet (that is Pass 3).

    On any exception the pass is marked ``failed`` and ``state.error_message``
    is set. The caller (``run_three_pass``) decides how to react — it will
    short-circuit if Pass 1 fails because Pass 2 needs collected data.
    """
    state.mark_pass(PASS_COLLECT, "running")
    logger.info(
        "Orchestrator Pass 1 (Collect): starting for %s (session=%s)",
        state.client_url, state.session_id,
    )

    try:
        agent = await _get_agent_for_session(state.session_id, state.mode)

        prompt = _build_pass_collect_prompt(state)

        result = await asyncio.wait_for(
            asyncio.to_thread(agent.run_conversation, prompt),
            timeout=_PASS_COLLECT_TIMEOUT,
        )

        state.collected_data["pass_collect_result"] = result
        state.mark_pass(PASS_COLLECT, "completed")
        logger.info(
            "Orchestrator Pass 1 (Collect): completed for %s — result keys=%s",
            state.client_url,
            list(result.keys()) if isinstance(result, dict) else type(result).__name__,
        )
    except Exception as exc:
        state.mark_pass(PASS_COLLECT, "failed")
        state.error_message = str(exc)
        logger.exception(
            "Orchestrator Pass 1 (Collect): FAILED for %s — %s",
            state.client_url, exc,
        )

    return state


async def _get_agent_for_session(session_id: str, mode: str):
    """Return a cached AIAgent for ``session_id`` or create a new one.

    Lazy import to avoid circular dependency: ``app.agent_wrapper`` imports
    many tool modules at module load, which import from
    ``tools.registry``. Importing it at the top of this module would force
    the whole tool graph to load on first orchestrator import. We defer
    until the first pass actually needs an agent.
    """
    from app.agent_wrapper import _agent_cache, _create_agent

    cached = _agent_cache.get(session_id)
    if cached is not None:
        agent, _, _ = cached
        return agent

    agent = _create_agent(session_id, mode)
    return agent


def _build_pass_collect_prompt(state: OrchestratorState) -> str:
    """Build the Pass 1 prompt, augmented with niche-aware Instagram rule.

    Per Phase 3 / Plan 03-03 (D-04 mandatory mechanism + D-06 retry):
      - Reads ``state.collected_data["niche_detection"]`` (set by the
        mini-call in Plan 03-02) to determine ``instagram_critical``.
      - Falls back to checking ``state.niche in CRITICAL_NICHES`` if the
        verdict dict is missing the boolean (belt + suspenders).
      - If critical: prompt mandates find_doctor_handles →
        run_instagram_content ordering with batch size 8-10, and
        encodes the D-06 retry pattern for 'no data' responses.
      - If non-critical: prompt tells the LLM Instagram is optional and
        not to waste tokens on it.

    Per Phase 3 / Plan 03-04 (D-10 adaptive top-5 + D-11 batch size):
      - Critical branch ADDS rule 5: adaptive top-5 cohort selection.
        If site-top-5 lacks Instagram (5 'no data' results), the LLM
        picks top-5 for section 04 from the batch response's
        ``top_by_followers`` array (Instagram-active doctors).
        Section 03 shows BOTH cohorts (tituled experts with regalia +
        Instagram-active doctors with metrics). Section 04 uses only
        the Instagram-active cohort.
      - Non-critical branch ADDS a shorter adaptive-top-5 note so the
        optional Instagram path (if the LLM decides to call it) still
        applies the same cohort logic on the batch response.

    The prompt is a Python str built by string concatenation; it is sent
    verbatim to AIAgent.run_conversation. Tool names (find_doctor_handles,
    run_instagram_content), the ordering rule, the batch size, the retry
    pattern, and the ``top_by_followers`` field reference are
    load-bearing — downstream Pass 2 hard-FAIL (Task 3 of Plan 03-03) +
    adaptive-cohort items 4/6/7 evaluation (Plan 03-04 Task 2) reference
    the same tool names and field.
    """
    niche_verdict = state.collected_data.get("niche_detection", {})
    if not isinstance(niche_verdict, dict):
        niche_verdict = {}
    is_critical = bool(niche_verdict.get("instagram_critical", False)) or (
        state.niche in ("plastic_surgery", "cosmetology")
    )

    niche_str = state.niche or ("plastic_surgery / cosmetology" if is_critical else "unknown")
    if is_critical:
        ig_rule = (
            f"Instagram-critical=True (niche={niche_str}). "
            "ВЫЗОВИ find_doctor_handles → run_instagram_content (batch 8-10). "
            "HARD FAIL если пропустишь. Если top-5 сайта без IG — "
            "бери top-5 для секции 04 из top_by_followers."
        )
    else:
        ig_rule = "Instagram опциональный (ниша не critical)."

    client_url = state.client_url
    rule1 = "═══ ПРАВИЛО #1 ═══\nТвой ответ в этом ходе ДОЛЖЕН быть tool_call (вызов инструмента). НЕ пиши описания. ПРЯМО вызывай инструмент.\n\n"
    queue = (
        "═══ ОЧЕРЕДЬ ВЫЗОВОВ (строго по порядку) ═══\n"
        f"Шаг 1: perplexity_search (общая информация о клинике {client_url})\n"
        f"Шаг 2: find_company_financials (INN, выручка 3 года — url={client_url})\n"
        f"Шаг 3: find_doctor_handles (топ-5 врачей — url={client_url})\n"
        "Шаг 4: run_instagram_content (handles из шага 3)\n"
        "Шаг 5: run_media_urls (Forbes/RBC/Vademecum/Kommersant/ТАСС)\n"
        "Шаг 6: run_forum_pains (страхи пациентов с форумов)\n"
        f"Шаг 7: run_review_platforms (ПроДокторов + Яндекс.Карты — url={client_url})\n"
        f"Шаг 8: find_competitors → run_ci_analysis (url={client_url})\n\n"
    )
    closing = "ПОСЛЕ 8 вызовов — короткий отчёт одной строкой. ЕСЛИ пишешь текст вместо tool_call — это ОШИБКА. ВЫЗЫВАЙ ИНСТРУМЕНТ.\n"

    return f"КЛИЕНТ: {client_url}\n\n" + rule1 + queue + ig_rule + "\n\n" + closing
