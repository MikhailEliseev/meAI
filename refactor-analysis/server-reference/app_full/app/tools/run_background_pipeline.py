"""
run_background_pipeline — Hermes tool: Phase 2 background scout + Phase 3 sell presentation

Called after collect_contact in _presale_prompt(). The client is gone —
this tool runs without waiting for a response.

Phase 2 (background, 1-2 hours):
  1. Calls run_full_scout → all 12+ scout tools sequentially
  2. Results saved to /opt/data/sessions-archive/{hash}/
  3. HTML report generated (if generate_html_report available)

Phase 3 (sell presentation):
  4. Loads all data from session archive
  5. Sends to Perplexity API with sell_presentation prompt
  6. Saves presentation text alongside other data

Timeout: 3600 seconds (1 hour). Client receives results via Telegram/email
after completion (future: Telegram delivery).

Registered in Hermes internal registry under toolset "aim-operations".
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from tools.registry import registry

logger = logging.getLogger(__name__)

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")
PERPLEXITY_BASE_URL = "https://api.perplexity.ai"
PERPLEXITY_MODEL = "sonar-pro"
REQUEST_TIMEOUT = 3600.0  # 1 hour for the full pipeline


def _load_sell_prompt() -> str:
    """Load the sell_presentation prompt template."""
    prompt_path = Path(__file__).parent.parent / "prompts" / "sell_presentation.txt"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    logger.warning("sell_presentation prompt file not found at %s", prompt_path)
    return (
        "Ты — стратегический маркетолог медицинского агентства AIM.\n"
        "Клиент: {clinic_name}, {city}, {specialization}.\n\n"
        "Напиши продающую презентацию на основе данных ниже.\n"
        "Структура: 1) Сколько пациентов недополучаешь, "
        "2) Сколько мы приведём (таблица), "
        "3) Что нужно сделать (3 действия), "
        "4) Сколько стоит и когда окупится.\n\n"
        "ИСХОДНЫЕ ДАННЫЕ:\n{all_data_from_session_archive}"
    )


async def handle_run_background_pipeline(
    session_hash=None, url=None, company_name=None, city=None, **kwargs
) -> str:
    """Run the complete background pipeline: scout → report → presentation.

    Phase 2: Full scout (all tools, 1-2 hours)
    Phase 3: Perplexity sell_presentation from assembled data

    Args:
        session_hash: Session archive key (required)
        url: Clinic website URL (required)
        company_name: Clinic name (derived from session data if omitted)
        city: City (derived from session data if omitted)

    Returns:
        JSON with session_hash, status, and presentation_text.
    """
    if isinstance(session_hash, dict):
        d = session_hash
        session_hash = d.get("session_hash", "")
        url = url or d.get("url", "")
        company_name = company_name or d.get("company_name", "")
        city = city or d.get("city", "")

    if not session_hash:
        return json.dumps({"error": "session_hash is required"})
    if not url:
        return json.dumps({"error": "url is required"})

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    logger.info("Starting background pipeline for session %s, url=%s", session_hash, url)

    from app.main import push_tool_progress
    from .session_archive import upsert_metadata, load_all_data, save_tool_output

    upsert_metadata(
        session_hash,
        client_url=url,
        pipeline="3-phase-perplexity",
        pipeline_started=datetime.now(timezone.utc).isoformat(),
    )

    # ── Phase 2: Full Scout ──────────────────────────────────────────────
    push_tool_progress(
        "background_pipeline",
        f"🔬 Фаза 2 — глубокий анализ: запускаю 12 инструментов разведки…",
    )

    scout_result = {}
    try:
        from .run_full_scout import handle_run_full_scout

        scout_json = await handle_run_full_scout(
            url=url,
            company_name=company_name or "Клиника",
            city=city or "",
            session_hash=session_hash,
            deep=True,
        )
        scout_result = json.loads(scout_json) if isinstance(scout_json, str) else scout_json
        logger.info("Full scout completed for %s: phases=%s", session_hash, scout_result.get("phases", []))

    except ImportError:
        logger.warning("run_full_scout not available — running individual tools")
        scout_result = await _run_tools_individually(session_hash, url, company_name, city, push_tool_progress)
    except Exception as e:
        logger.exception("Full scout failed for %s", session_hash)
        scout_result = {"error": str(e)}

    push_tool_progress(
        "background_pipeline",
        "✅ Фаза 2 завершена — все данные собраны в архив сессии",
    )

    # ── Phase 3: Sell Presentation ───────────────────────────────────────
    push_tool_progress(
        "background_pipeline",
        "📝 Фаза 3 — стратегический маркетолог готовит презентацию…",
    )

    presentation_text = await _generate_sell_presentation(
        session_hash, url, company_name, city
    )

    if presentation_text:
        save_tool_output(session_hash, "sell_presentation", {
            "text": presentation_text,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model": PERPLEXITY_MODEL,
        })

    # ── Final metadata ───────────────────────────────────────────────────
    upsert_metadata(
        session_hash,
        pipeline_completed=datetime.now(timezone.utc).isoformat(),
        phases_completed=list(scout_result.get("phases", [])),
    )

    push_tool_progress(
        "background_pipeline",
        "🎉 Пайплайн завершён! Отчёт и презентация готовы к отправке клиенту.",
    )

    return json.dumps({
        "session_hash": session_hash,
        "status": "completed",
        "url": url,
        "scout_status": "ok" if not scout_result.get("error") else "partial",
        "presentation_ready": bool(presentation_text),
    }, ensure_ascii=False, indent=2)


async def _run_tools_individually(
    session_hash: str, url: str, company_name: str, city: str, push_fn
) -> dict:
    """Fallback: run scout tools one by one instead of run_full_scout."""
    from .session_archive import save_tool_output

    tool_specs = [
        ("run_prescan", "handle_run_prescan", {"url": url}, "prescan-data"),
        ("find_competitors", "handle_find_competitors", {"url": url, "city": city, "company_name": company_name}, "competitors"),
        ("run_ci_analysis", "handle_run_ci_analysis", {"url": url, "city": city, "deep": True}, "ci-analysis"),
        ("run_seo_audit", "handle_run_seo_audit", {"url": url}, "seo_audit"),
        ("run_review_platforms", "handle_run_review_platforms", {"company_name": company_name, "city": city}, "review_platforms"),
        ("run_doctor_dossiers", "handle_run_doctor_dossiers", {"doctor_name": company_name}, "doctor_dossiers"),
        ("run_pagespeed", "handle_run_pagespeed", {"website": url}, "pagespeed"),
        ("run_ads_intelligence", "handle_run_ads_intelligence", {"company_name": company_name, "website": url}, "ads_intelligence"),
        ("find_company_financials", "handle_find_company_financials", {"company_name": company_name}, "financials"),
        ("run_content_analysis", "handle_run_content_analysis", {"url": url}, "content_analysis"),
    ]

    phases = []
    for tool_name, handler_name, params, file_key in tool_specs:
        try:
            module = __import__(f"tools.{tool_name}", fromlist=[handler_name])
            handler = getattr(module, handler_name, None)
            if handler:
                push_fn("background_pipeline", f"  🔧 {tool_name}…")
                result_json = await handler(**params)
                result = json.loads(result_json) if isinstance(result_json, str) else result_json
                save_tool_output(session_hash, file_key, result)
                phases.append((tool_name, True))
            else:
                phases.append((tool_name, False))
        except Exception as e:
            logger.warning("Tool %s failed: %s", tool_name, e)
            phases.append((tool_name, False))

    return {"phases": phases}


async def _generate_sell_presentation(
    session_hash: str, url: str, company_name: str, city: str
) -> str:
    """Call Perplexity API with sell_presentation prompt and all session data."""
    if not PERPLEXITY_API_KEY:
        logger.warning("PERPLEXITY_API_KEY not configured — skipping sell_presentation")
        return ""

    from .session_archive import load_all_data

    all_data = load_all_data(session_hash)

    # Extract context from loaded data
    prescan = all_data.get("prescan", {})
    clinic_name = company_name or prescan.get("legal_name", "") or "Клиника"
    clinic_city = city or prescan.get("city", "") or "город"
    specialization = prescan.get("specialization", "") or "медицина"

    # Stringify all data for the prompt
    all_data_str = json.dumps(all_data, ensure_ascii=False, indent=2)
    if len(all_data_str) > 80000:
        all_data_str = all_data_str[:80000] + "\n… [truncated]"

    prompt_template = _load_sell_prompt()
    user_prompt = (
        prompt_template
        .replace("{clinic_name}", clinic_name)
        .replace("{city}", clinic_city)
        .replace("{specialization}", specialization)
        .replace("{all_data_from_session_archive}", all_data_str)
    )

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=PERPLEXITY_API_KEY,
            base_url=PERPLEXITY_BASE_URL,
            timeout=120.0,
        )

        response = await client.chat.completions.create(
            model=PERPLEXITY_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты — стратегический маркетолог медицинского агентства AIM. "
                        "Твоя задача — написать продающую презентацию для владельца "
                        "медицинской клиники. Стиль: живой, уважительный, "
                        "«смотри, у тебя здесь так, а можно так». "
                        "Короткие абзацы. Без маркетинговых штампов. "
                        "Все цифры — только из предоставленных данных."
                    ),
                },
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=4000,
        )

        return response.choices[0].message.content or ""

    except Exception as e:
        logger.exception("Perplexity sell_presentation failed for %s", session_hash)
        return ""


# ── Registry ───────────────────────────────────────────────────────────────

registry.register(
    name="run_background_pipeline",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "run_background_pipeline",
            "description": (
                "BACKGROUND pipeline for Phase 2+3 of presale. "
                "Call this AFTER collect_contact — the client has left. "
                "Phase 2: Runs ALL 12+ scout tools sequentially (1-2 hours), "
                "saves results to session archive. "
                "Phase 3: Generates sell_presentation via Perplexity API "
                "answering 'how many patients you'll bring for what money'. "
                "No response needed from client during execution. "
                "Results are delivered via Telegram after completion."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "session_hash": {
                        "type": "string",
                        "description": "Session archive key (from presale flow)",
                    },
                    "url": {
                        "type": "string",
                        "description": "Client clinic website URL",
                    },
                    "company_name": {
                        "type": "string",
                        "description": "Clinic name (optional — derived from session data if omitted)",
                    },
                    "city": {
                        "type": "string",
                        "description": "City (optional — derived from session data if omitted)",
                    },
                },
                "required": ["session_hash", "url"],
            },
        },
    },
    handler=handle_run_background_pipeline,
    check_fn=lambda: True,
    is_async=True,
    description="Phase 2+3 background pipeline: all scout tools → Perplexity sell_presentation. 1-2h timeout.",
    emoji="🔬",
)
