"""Mini-call niche detector — runs between Pass 1 (Collect) and Pass 2 (Gap-analyze).

Per Phase 3 / D-01..03 of the Instagram Integration plan:

- D-01: Niche is determined by the LLM from Pass 1 context (not keyword list
  or ОКВЭД lookup).
- D-02: Implemented as a short, single-purpose LLM call between Pass 1 and
  Pass 2. Returns a structured boolean verdict
  ``{instagram_critical, niche, reason}``.
- D-03: Boundary rule — Instagram-critical only if cosmetology or plastic
  surgery is the clinic's MAIN profile (>50% services or stated as primary).
  Dental-with-cosmetic add-ons must NOT trigger.

The detector reuses the SAME AIAgent session as Pass 1 so the LLM sees the
collected conversation history. On any failure (timeout, parse error,
exception) the detector returns a deterministic fallback dict
(``instagram_critical=False, niche="unknown"``) so Pass 2 always has a value
to read — Pass 2 must never hard-FAIL on a niche-detection failure.
"""

import asyncio
import json
import logging
import re

from app.orchestrator.states import OrchestratorState

logger = logging.getLogger(__name__)

# Mini-call ceiling — D-02 budgets ~5s API time. DeepSeek V4 Pro latency
# varies; 30s gives margin for slow responses without blocking the 3-pass
# cycle. On timeout the detector logs + returns the fallback dict.
_NICHE_DETECT_TIMEOUT = 30

# Regex to extract the first {...} JSON block from an LLM response. LLMs
# sometimes wrap JSON in markdown fences or add prose around it. re.DOTALL
# lets the match span newlines (the JSON is multi-line). Replicated here
# (instead of importing from pass_gap_analyze) to keep this module
# self-contained and to avoid an import cycle if pass_gap_analyze ever
# changes its regex constant.
_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)

# Boundary-rule prompt (Russian — matches the LLM's primary working language
# in Pass 1). The >50% rule and the "add-on service" exclusion implement D-03.
_NICHE_DETECT_PROMPT_TEMPLATE = """Ты только что собрал данные о клинике {client_url} в Pass 1.

Определи, является ли Instagram-маркетинг КРИТИЧНЫМ для этой клиники:
- instagram_critical=true только если косметология или пластическая хирургия — ОСНОВНОЙ профиль клиники (>50% услуг или заявлен как главный)
- Если эстетические процедуры — доп. услуга (стоматология с косметологией, общая медицина с косметологией) → instagram_critical=false
- Учитывай:specialization_clinic > specialization_doctor. Если клиника позиционируется как "многопрофильная" — проверь, занимает ли косметология/пластика >50% visible услуг на сайте.

ВЫВЕДИ результат КАК JSON (без markdown, без текста вокруг):
{{"instagram_critical": true|false, "niche": "plastic_surgery"|"cosmetology"|"dental"|"general_medicine"|"other", "reason": "1 предложение пояснение"}}

ВАЖНО: только валидный JSON, без markdown fences, без пояснений.
"""


async def detect_instagram_critical_niche(state: OrchestratorState) -> dict:
    """Run the mini-call niche detection between Pass 1 and Pass 2.

    Args:
        state: OrchestratorState after Pass 1 has completed. ``state.session_id``
            is reused so the AIAgent's Pass 1 conversation history is visible
            to the LLM during this mini-call (per D-02).

    Returns:
        Dict with keys ``instagram_critical`` (bool), ``niche`` (str),
        ``reason`` (str). On ANY failure (timeout, parse error, exception)
        returns a deterministic fallback dict
        ``{"instagram_critical": False, "niche": "unknown", "reason": ...}``
        so Pass 2 can proceed without aborting the 3-pass cycle.
    """
    try:
        # Lazy import — same pattern as pass_gap_analyze.py:82 to avoid any
        # circular dependency at module load time.
        from app.orchestrator.pass_collect import _get_agent_for_session

        agent = await _get_agent_for_session(state.session_id, state.mode)

        prompt = _NICHE_DETECT_PROMPT_TEMPLATE.format(client_url=state.client_url)

        result = await asyncio.wait_for(
            asyncio.to_thread(agent.run_conversation, prompt),
            timeout=_NICHE_DETECT_TIMEOUT,
        )

        reply_text = _extract_reply_text(result)

        verdict = _parse_verdict_json(reply_text)
        if verdict is None:
            raise ValueError(f"could not parse JSON verdict from reply: {reply_text[:200]!r}")

        normalized = _normalize_verdict(verdict)
        logger.info(
            "Niche detection for %s: instagram_critical=%s, niche=%s, reason=%s",
            state.client_url,
            normalized["instagram_critical"],
            normalized["niche"],
            normalized["reason"],
        )
        return normalized
    except Exception as exc:
        # Timeout, parse failure, agent error — any exception lands here.
        # We log + return the fallback dict. The 3-pass cycle MUST continue.
        logger.warning(
            "Niche detection for %s FAILED — returning fallback (non-critical). "
            "Error: %s",
            state.client_url, exc,
        )
        return {
            "instagram_critical": False,
            "niche": "unknown",
            "reason": "mini-call failed — treating as non-critical to avoid false hard-FAIL",
            "error": str(exc),
        }


def _extract_reply_text(result) -> str:
    """Pull the assistant's final text from an AIAgent.run_conversation() result.

    Mirrors ``pass_gap_analyze._extract_reply_text``: final_response ->
    response -> content -> str(result). Replicated here (not imported) so
    this module stays self-contained and survives any future refactor of
    pass_gap_analyze.
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


def _parse_verdict_json(reply_text: str):
    """Parse the LLM's JSON verdict from ``reply_text``.

    Tries direct ``json.loads`` first (LLM followed instructions), then
    falls back to regex extraction of the first ``{...}`` block. Returns
    ``None`` on total failure (caller raises -> fallback dict).
    """
    if not reply_text:
        return None

    # Strip markdown code fences if present.
    cleaned = re.sub(r"^```(?:json)?\s*", "", reply_text.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    match = _JSON_BLOCK_RE.search(reply_text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None

    return None


def _normalize_verdict(verdict) -> dict:
    """Coerce parsed JSON into the canonical ``{instagram_critical, niche, reason}`` shape.

    - ``instagram_critical``: bool(parsed[key]) — accepts Python truthy/falsy
      from JSON (``true``/``false``) plus permissive coercion for strings.
    - ``niche``: kept as-is if str, else ``"unknown"``.
    - ``reason``: kept as-is if str, else ``""``.
    """
    if not isinstance(verdict, dict):
        return {
            "instagram_critical": False,
            "niche": "unknown",
            "reason": "verdict was not a dict",
        }

    raw_crit = verdict.get("instagram_critical", False)
    if isinstance(raw_crit, bool):
        crit = raw_crit
    elif isinstance(raw_crit, str):
        crit = raw_crit.strip().lower() in ("true", "1", "yes", "da", "да")
    else:
        crit = bool(raw_crit)

    niche_raw = verdict.get("niche", "unknown")
    niche = niche_raw if isinstance(niche_raw, str) and niche_raw.strip() else "unknown"

    reason_raw = verdict.get("reason", "")
    reason = reason_raw if isinstance(reason_raw, str) else ""

    return {
        "instagram_critical": crit,
        "niche": niche,
        "reason": reason,
    }
