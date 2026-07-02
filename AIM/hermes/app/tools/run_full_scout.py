"""run_full_scout — Hermes tool: Full 16-Phase Scout Pipeline.

Единая точка входа в 16-фазный пайплайн конкурентной разведки.
LLM вызывает ОДИН инструмент. Python (PipelineEngine) гарантирует
выполнение всех 16 фаз строго последовательно.

Поток:
  Сообщение пользователя с URL → agent_wrapper определяет ONBOARDING →
    system prompt говорит LLM: «вызови run_full_scout с этим URL» →
      LLM вызывает run_full_scout →
        run_full_scout handler → PipelineEngine.execute() (все 16 фаз) →
          HTML-отчёт → результат → LLM форматирует для клиента
"""

import json
import logging
import os

from tools.registry import registry

logger = logging.getLogger(__name__)


def _normalize_args(first_param, defaults):
    """Если hermes-agent передаёт весь arguments object как first_param, извлечь значения."""
    if isinstance(first_param, dict):
        return {k: first_param.get(k, defaults[k]) for k in defaults}
    return None


async def handle_run_full_scout(url=None, client_name="", **kwargs) -> str:
    """Запустить полный 16-фазный скаутинг конкурентной разведки для сайта клиники.

    Args:
        url: URL сайта клиники (обязательно).
        client_name: Название клиники (опционально, определяется из prescan).

    Returns:
        JSON строка с результатами всех фаз, ключевыми находками и URL отчёта.
    """
    unpacked = _normalize_args(url, {"url": "", "client_name": ""})
    if unpacked:
        url = unpacked["url"]
        client_name = unpacked.get("client_name", client_name)

    # Auto-prepend https:// if URL has no protocol
    if url and not url.startswith(("http://", "https://")):
        url = "https://" + url

    if not url:
        return json.dumps({
            "error": "URL is required",
            "detail": "run_full_scout requires a website URL to start the scout pipeline.",
        })

    # Извлекаем session_id из kwargs/контекста
    session_id = kwargs.get("session_id", "")
    if not session_id:
        # Пытаемся получить из переменной окружения или генерируем
        session_id = os.getenv("PIPELINE_SESSION_ID", "")
    if not session_id:
        import uuid
        session_id = str(uuid.uuid4())[:12]

    mode = kwargs.get("mode", os.getenv("PIPELINE_MODE", "ONBOARDING"))

    logger.info(
        "run_full_scout: starting 16-phase pipeline for %s (session=%s, mode=%s)",
        url, session_id, mode,
    )

    try:
        from app.pipeline.engine import PipelineEngine
        from app.pipeline.phases import PHASES
        from app.main import push_phase_progress
        import asyncio

        # ── Russian labels для phase-progress events (фронтенд их покажет) ──
        phase_labels = {
            "PERPLEXITY": "Исследование рынка",
            "COMPETITORS": "Конкуренты",
            "TECH AUDIT": "Технический аудит",
            "SOCIAL VERIFIER": "Отзывы и рейтинги",
            "CONTENT ANALYSIS": "Контент сайта",
            "KEY PERSONS": "Врачи и ключевые лица",
            "SMI MENTIONS": "Упоминания в СМИ",
            "FORUM PAINS": "Паттерны болей пациентов",
            "FINANCE": "Финансовые данные",
            "CONTENT PLAN": "Контент-план",
            "HTML BUILD": "Сборка HTML-отчёта",
            "QC CRITIQUE": "Проверка качества",
            "PRESENTATION": "Финальная презентация",
        }

        def _progress_cb(phase_id, phase_name, status, message="", duration_seconds=None, **_):
            """Bridge: PipelineEngine → SSE push_phase_progress.

            Engine вызывает с kwargs: phase_id, phase_name, status, message, duration_seconds.
            push_phase_progress отправляет в _tool_progress_queue → SSE → chat-bundle.js.
            """
            label = phase_labels.get(phase_name, phase_name)
            try:
                push_phase_progress(
                    phase_id=phase_id,
                    phase_name=phase_name,
                    phase_label=label,
                    status=status,
                    message=message or "",
                    duration_seconds=duration_seconds,
                    progress={"current": phase_id + 1, "total": len(PHASES)},
                )
            except Exception as cb_err:
                logger.warning("push_phase_progress failed: %s", cb_err)

        engine = PipelineEngine()
        state = await engine.execute(
            session_id=session_id,
            client_url=url,
            client_name=client_name,
            mode=mode,
            progress_callback=_progress_cb,
        )

        # ── Сохраняем metadata ───────────────────────────────────────
        try:
            from app.tools.session_archive import upsert_metadata

            completed = sum(
                1 for r in state.phases.values()
                if r.status.value in ("completed", "no_data")
            )
            failed = sum(
                1 for r in state.phases.values()
                if r.status.value in ("permanent_failure", "tool_failed", "timed_out")
            )

            upsert_metadata(
                session_id,
                url=url,
                client_name=client_name,
                completed_phases=completed,
                failed_phases=failed,
                total_phases=len(state.phases),
                started_at=state.started_at,
            )
        except Exception as meta_err:
            logger.warning("run_full_scout: metadata save failed: %s", meta_err)

        # ── Формируем результат ──────────────────────────────────────
        phase_results = []
        for phase_id, result in sorted(state.phases.items()):
            phase_results.append({
                "phase_id": phase_id,
                "name": result.data.get("phase_name", f"Phase {phase_id}") if result.data else f"Phase {phase_id}",
                "status": result.status.value,
                "duration_seconds": result.duration_seconds,
                "error": result.error_message,
                "interpretation": result.llm_interpretation[:300] if result.llm_interpretation else None,
            })

        completed = sum(1 for r in phase_results if r["status"] in ("completed", "no_data"))
        failed = sum(1 for r in phase_results if r["status"] in ("permanent_failure", "tool_failed", "timed_out"))

        # Проверяем URL HTML-отчёта
        report_url = state.accumulated_data.get("report_url", "")
        if not report_url:
            report_url = state.accumulated_data.get("DATA_ASSEMBLY_result", {}).get("url", "")
        if isinstance(report_url, dict):
            report_url = report_url.get("url", "")

        result = {
            "status": "completed" if failed == 0 else "partial",
            "session_id": session_id,
            "url": url,
            "client_name": client_name or state.client_name,
            "client_city": state.client_city,
            "client_specialization": state.client_specialization,
            "phases_total": len(state.phases),
            "phases_completed": completed,
            "phases_failed": failed,
            "phase_results": phase_results,
            "report_url": report_url,
            "started_at": state.started_at,
            "key_findings": _extract_key_findings(state),
        }

        logger.info(
            "run_full_scout: pipeline complete — %d/%d phases done",
            completed, len(state.phases),
        )

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.exception("run_full_scout: pipeline failed for %s", url)
        return json.dumps({
            "error": "Scout pipeline failed",
            "detail": str(e),
            "url": url,
        })


def _extract_key_findings(state) -> list[str]:
    """Извлечь ключевые находки из accumulated_data."""
    findings = []

    # Приоритетные фазы для ключевых находок
    priority_phases = [
        "PRE-FLIGHT",
        "COMPETITOR MATRIX",
        "GAPS & ADVANTAGES",
        "FINANCIAL: FNS+",
        "RATINGS & REVIEWS",
    ]

    for phase_name in priority_phases:
        interp_key = f"{phase_name}_interpretation"
        if interp_key in state.accumulated_data:
            interp = str(state.accumulated_data[interp_key])
            if interp and len(interp) > 20:
                # Берём первые 200 символов как summary
                summary = interp[:200].strip()
                if len(interp) > 200:
                    summary += "..."
                findings.append(summary)

    return findings[:5]  # Максимум 5 ключевых находок


registry.register(
    name="run_full_scout",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "run_full_scout",
            "description": (
                "Запустить полный 16-фазный скаутинг конкурентной разведки для сайта клиники. "
                "Собирает всю информацию: рынок, Instagram, реклама, тех.аудит, SEO, "
                "соцсети, Telegram, врачи, СМИ, конкуренты, отзывы, финансы, контент. "
                "Генерирует HTML-отчёт. Вызывается когда клиент дал URL своего сайта."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL сайта клиники (например, 'https://clinic.ru')",
                    },
                    "client_name": {
                        "type": "string",
                        "description": "Название клиники (опционально, определяется автоматически)",
                    },
                },
                "required": ["url"],
            },
        },
    },
    handler=handle_run_full_scout,
    check_fn=lambda: True,
    is_async=True,
    description="Запустить полный 16-фазный скаутинг конкурентной разведки для сайта клиники",
    emoji="🔭",
)
