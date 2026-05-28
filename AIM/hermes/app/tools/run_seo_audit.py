"""
run_seo_audit — Hermes tool: SEO Audit

POST http://app:8000/api/seo/audit → starts async CI pipeline
GET  http://app:8000/api/seo/audit/{task_id} → polls until done

Runs a full SEO audit on a client website: technical analysis, keyword positions,
competitor comparison, backlink profile. Returns patient acquisition potential
(3 key numbers: patients/month, time-to-result, cost-per-patient).

Registered in Hermes internal registry under toolset "aim-operations".
"""

import asyncio
import json
import logging

import httpx

from tools.registry import registry

logger = logging.getLogger(__name__)


def _normalize_args(first_param, defaults):
    """If hermes-agent passes the whole arguments object as first_param, extract all values."""
    if isinstance(first_param, dict):
        return {k: first_param.get(k, defaults[k]) for k in defaults}
    return None


AIM_API_BASE = "http://app:8000"
REQUEST_TIMEOUT = 300.0  # full async pipeline: start + polling
POLL_INTERVAL = 2.0       # seconds between status checks


def _compact_audit_result(data: dict) -> dict:
    """Extract only LLM-essential metrics from the full CI result (18K → ~2K)."""
    findings = data.get("findings", {})

    # Helper: safely slice any iterable
    def _take(obj, n):
        if isinstance(obj, list):
            return obj[:n]
        if isinstance(obj, dict):
            return {k: obj[k] for k in list(obj.keys())[:n]}
        return obj

    # Phase 7 (ci-strategist) — 3 WOW numbers + insights
    phase7 = findings.get("phase_7", {})
    strat_result = phase7.get("result", {}) if isinstance(phase7, dict) else {}
    estimates = strat_result.get("estimates", {}) or {}
    insights = _take(strat_result.get("insights", []), 5)
    opportunities = _take(strat_result.get("opportunities", []), 3)
    landscape = strat_result.get("landscape", {}) or {}

    # Phase 1 (ci-scout) — competitors found
    phase1 = findings.get("phase_1", {})
    scout_result = phase1.get("result", {}) if isinstance(phase1, dict) else {}
    competitors = _take(scout_result.get("top_for_analysis", []), 5)

    # Phase 9 (ci-prioritizer) — action items
    phase9 = findings.get("phase_9", {})
    prio_result = phase9.get("result", {}) if isinstance(phase9, dict) else {}
    actions = _take(prio_result.get("action_items", []), 5)

    return {
        "wow": {
            "patients_per_month": estimates.get("patients_per_month"),
            "time_to_result_weeks": estimates.get("time_to_result"),
            "cost_per_patient_rub": estimates.get("cost_per_patient"),
        },
        "market": {
            "competitive_intensity": landscape.get("competitive_intensity", "unknown"),
            "digital_maturity": landscape.get("digital_maturity", "unknown"),
            "niche_size": landscape.get("market_size", "unknown"),
        },
        "competitors": [
            {"name": c.get("name", c.get("url", "")), "url": c.get("url", "")}
            for c in (competitors if isinstance(competitors, list) else [])
        ],
        "insights": insights if isinstance(insights, list) else [],
        "opportunities": opportunities if isinstance(opportunities, list) else [],
        "actions": actions if isinstance(actions, list) else [],
        "meta": {
            "tier": data.get("tier"),
            "phases": len(data.get("phases_executed", [])),
            "time_seconds": data.get("execution_time_seconds"),
            "quality_score": data.get("quality_score"),
        },
    }


async def handle_run_seo_audit(url=None, **kwargs) -> str:
    """Run a full SEO audit on a client website.

    Starts async CI pipeline, polls until complete, returns compact result.

    Args:
        url: Website URL to audit (e.g., "https://clinic.ru")

    Returns:
        JSON string with audit results including:
        - patients_per_month: estimated monthly patient acquisition
        - time_to_result: estimated weeks to first results
        - cost_per_patient: estimated acquisition cost
    """
    unpacked = _normalize_args(url, {"url": ""})
    if unpacked:
        url = unpacked["url"]
    # Auto-prepend https:// if URL has no protocol
    if url and not url.startswith(("http://", "https://")):
        url = "https://" + url
    logger.info("Running SEO audit for URL: %s", url)

    from app.main import push_tool_progress

    try:
        push_tool_progress("seo", f"🔍 Захожу на сайт {url}…")

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            # Step 1: Start async audit
            push_tool_progress("seo", "⚙️ Запускаю технический аудит…")
            start_response = await client.post(
                f"{AIM_API_BASE}/api/seo/audit",
                json={"url": url},
            )
            start_response.raise_for_status()
            start_data = start_response.json()
            task_id = start_data.get("task_id")
            if not task_id:
                return json.dumps({"error": "No task_id returned from SEO API"})

            logger.info("SEO audit task started: %s", task_id)

            # Step 2: Poll until done
            status_url = f"{AIM_API_BASE}/api/seo/audit/{task_id}"
            progress_messages = [
                "📊 Анализирую структуру сайта…",
                "🔗 Проверяю техническое SEO…",
                "🏗️ Изучаю архитектуру и контент…",
                "📊 Собираю WOW-цифры…",
            ]
            poll_count = 0

            while True:
                await asyncio.sleep(POLL_INTERVAL)
                poll_count += 1

                status_response = await client.get(status_url)
                status_response.raise_for_status()
                status_data = status_response.json()

                st = status_data.get("status", "unknown")
                progress_msg = status_data.get("progress", "")

                if st == "done":
                    push_tool_progress("seo", "✅ SEO-аудит готов!")
                    data = status_data.get("result", {})
                    compact = _compact_audit_result(data)
                    logger.info("SEO audit completed (task %s): %d polls, compacted %d chars",
                                task_id, poll_count, len(json.dumps(compact)))
                    return json.dumps(compact, ensure_ascii=False, indent=2)

                if st == "error":
                    err = status_data.get("error", "Unknown error")
                    logger.error("SEO audit failed (task %s): %s", task_id, err)
                    return json.dumps({
                        "error": "SEO audit failed",
                        "detail": err,
                    })

                # Rotate progress messages every few polls
                if progress_msg:
                    push_tool_progress("seo", progress_msg)
                else:
                    idx = (poll_count // 3) % len(progress_messages)
                    push_tool_progress("seo", progress_messages[idx])

    except httpx.HTTPStatusError as e:
        logger.error("AIM API returned error for SEO audit: %s", e)
        return json.dumps({
            "error": "AIM API returned an error",
            "status": e.response.status_code,
            "detail": str(e),
        })
    except httpx.RequestError as e:
        logger.error("Cannot reach AIM API for SEO audit: %s", e)
        return json.dumps({
            "error": "Cannot reach AIM API",
            "detail": str(e),
        })
    except Exception as e:
        logger.exception("Unexpected error in SEO audit handler")
        return json.dumps({
            "error": "Unexpected error in tool handler",
            "detail": str(e),
        })


registry.register(
    name="run_seo_audit",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "run_seo_audit",
            "description": (
                "Run a full SEO audit on a client website: technical analysis, "
                "keyword positions, competitor comparison, backlink profile. "
                "Returns patient acquisition potential (3 key numbers: "
                "patients/month, time-to-result, cost-per-patient)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Website URL to audit (e.g., 'https://clinic.ru')",
                    },
                },
                "required": ["url"],
            },
        },
    },
    handler=handle_run_seo_audit,
    check_fn=lambda: True,
    is_async=True,
    description="Run a full SEO audit on a client website and return patient acquisition potential",
    emoji="🔍",
)
