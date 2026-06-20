"""Hermes v7 — Pipeline Engine.

Сердце v7. Жёсткий цикл по PHASES:
1. Вызвать инструменты фазы
2. При ошибке: проверить key_exhaustion → rotate_keys → retry
3. При allow_no_data: NO_DATA = легитимный исход, идём дальше
4. LLM-интерпретация: узкий промпт ТОЛЬКО с данными этой фазы
5. Персист данных в accumulated_data
6. Переход на следующую фазу — ТОЛЬКО Python

LLM — интерпретатор данных, НЕ оркестратор.
Python контролирует последовательность и обработку ошибок.
"""

import asyncio
import importlib
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Optional

from .states import PhaseStatus, PhaseContract, PhaseResult, PipelineState
from .phases import Phase, PHASES
from .file_guard import get_key_rotator

logger = logging.getLogger(__name__)

OMNIROUTE_URL = os.getenv("OMNIROUTE_URL", os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"))
OMNIROUTE_AUTH = os.getenv("OMNIROUTE_AUTH", os.getenv("DEEPSEEK_API_KEY", ""))
DEFAULT_MODEL = os.getenv("LLM_MODEL", "ds/deepseek-v4-pro")

# Короткий таймаут для tool-calling фаз (не интерпретация)
_TOOL_CALL_TIMEOUT = 300

# ── Tool Handler Map ───────────────────────────────────────────────
# Каждый инструмент → (module_path, handler_function_name).
# Хендлеры импортируются лениво при первом вызове.
_TOOL_HANDLERS: dict[str, tuple[str, str]] = {
    "web_search":              ("app.tools.run_web_search",         "handle_run_web_search"),
    "run_pagespeed":           ("app.tools.run_pagespeed",          "handle_run_pagespeed"),
    "run_seo_audit":           ("app.tools.run_seo_audit",          "handle_run_seo_audit"),
    "find_competitors":        ("app.tools.find_competitors",       "handle_find_competitors"),
    "run_review_platforms":    ("app.tools.run_review_platforms",   "handle_run_review_platforms"),
    "run_content_analysis":    ("app.tools.run_content_analysis",   "handle_run_content_analysis"),
    "run_hh_analysis":         ("app.tools.run_hh_analysis",        "handle_run_hh_analysis"),
    "run_doctor_dossiers":     ("app.tools.run_doctor_dossiers",    "handle_run_doctor_dossiers"),
    "run_ci_analysis":         ("app.tools.run_ci_analysis",        "handle_run_ci_analysis"),
    "run_smi_mentions":        ("app.tools.run_smi_mentions",       "handle_run_smi_mentions"),
    "run_content_gaps":        ("app.tools.run_content_gaps",       "handle_run_content_gaps"),
    "find_company_financials": ("app.tools.find_company_financials","handle_find_company_financials"),
    "generate_html_report":    ("app.tools.generate_html_report",   "handle_generate_html_report"),
    "publish_scout_report":    ("app.tools.publish_scout_report",   "handle_publish_scout_report"),
}

# Кеш импортированных хендлеров
_handler_cache: dict[str, callable] = {}


def _get_handler(tool_name: str):
    """Ленивый импорт хендлера инструмента."""
    if tool_name in _handler_cache:
        return _handler_cache[tool_name]

    entry = _TOOL_HANDLERS.get(tool_name)
    if not entry:
        raise ValueError(f"No handler mapping for tool: {tool_name}")

    module_path, fn_name = entry
    try:
        module = importlib.import_module(module_path)
        handler = getattr(module, fn_name)
        _handler_cache[tool_name] = handler
        return handler
    except (ImportError, AttributeError) as e:
        raise ImportError(
            f"Cannot import handler for {tool_name}: {module_path}.{fn_name} — {e}"
        ) from e


class PipelineEngine:
    """Python-стейт-машина для онбординга клиентов.

    Выполняет 15 фаз последовательно. Каждая фаза:
    - Вызывает свои инструменты (через LLM как tool-calling interface)
    - При ошибке: ретраит с ротацией ключей
    - NO_DATA = легитимный исход для фаз с allow_no_data
    - LLM-интерпретация данных фазы (узкий промпт)
    - Данные персистятся в accumulated_data

    LLM НЕ решает какие инструменты вызывать и в каком порядке.
    Python решает. LLM — только интерпретатор и tool-calling interface.
    """

    def __init__(self):
        self._key_rotator = get_key_rotator()

    async def execute(
        self,
        session_id: str,
        client_url: str,
        client_name: str = "",
        mode: str = "ONBOARDING",
    ) -> PipelineState:
        """Выполнить полный пайплайн онбординга.

        Args:
            session_id: ID сессии чата.
            client_url: URL сайта клиента.
            client_name: Название клиники (если известно заранее).
            mode: Режим работы.

        Returns:
            PipelineState с результатами всех фаз.
        """
        state = PipelineState(
            session_id=session_id,
            client_url=client_url,
            client_name=client_name,
            started_at=datetime.now(timezone.utc).isoformat(),
            mode=mode,
        )

        logger.info(
            "PipelineEngine: starting onboarding for %s (session=%s, mode=%s)",
            client_url, session_id, mode,
        )

        # ── Детекция города ПЕРЕД запуском фаз ──────────────────────
        city = await self._detect_city_from_contacts(client_url)
        if city:
            state.client_city = city
            logger.info(
                "PipelineEngine: detected city=%r for %s",
                city, client_url,
            )
        else:
            logger.warning(
                "PipelineEngine: could not detect city from contacts page for %s, "
                "will fall back to LLM inference",
                client_url,
            )

        # ── Детекция специализации ПЕРЕД запуском фаз ──────────────
        specialization = await self._detect_specialization(client_url)
        if specialization:
            state.client_specialization = specialization
            logger.info(
                "PipelineEngine: detected specialization=%r for %s",
                specialization, client_url,
            )
        else:
            logger.warning(
                "PipelineEngine: could not detect specialization for %s, "
                "will fall back to LLM inference",
                client_url,
            )

        # ── Детекция ИНН клиента (из /contacts) ─────────────────────
        client_inn = await self._detect_client_inn(client_url)
        if client_inn:
            state.client_inn = client_inn
            logger.info(
                "PipelineEngine: detected client INN=%s for %s",
                client_inn, client_url,
            )

        for i, phase in enumerate(PHASES):
            logger.info(
                "PipelineEngine: phase %d/%d — %s (id=%.2f)",
                i + 1, len(PHASES), phase.name, phase.id,
            )
            state.current_phase = phase.id

            result = await self._execute_phase(phase, state)
            state.phases[phase.id] = result

            # Аккумулируем данные
            if result.data:
                state.accumulated_data[phase.name] = result.data
            if result.llm_interpretation:
                state.accumulated_data[f"{phase.name}_interpretation"] = result.llm_interpretation
            if result.error_message:
                state.accumulated_data[f"{phase.name}_error"] = result.error_message

            # Сохраняем состояние для polling
            self._persist_state(state)

            # PERMANENT_FAILURE с on_permanent_failure="abort" → останов
            if result.status == PhaseStatus.PERMANENT_FAILURE:
                if phase.contract.on_permanent_failure == "abort":
                    logger.error(
                        "PipelineEngine: ABORTING — phase %s failed permanently: %s",
                        phase.name, result.error_message,
                    )
                    break
                else:
                    logger.warning(
                        "PipelineEngine: phase %s failed permanently, skipping (on_permanent_failure=skip)",
                        phase.name,
                    )
                    continue

            # SKIPPED → идём дальше
            if result.status == PhaseStatus.SKIPPED:
                logger.info("PipelineEngine: phase %s skipped", phase.name)
                continue

            logger.info(
                "PipelineEngine: phase %s → %s (%.1fs)",
                phase.name, result.status.value, result.duration_seconds,
            )

        completed = sum(
            1 for r in state.phases.values()
            if r.status in (PhaseStatus.COMPLETED, PhaseStatus.NO_DATA)
        )
        logger.info(
            "PipelineEngine: COMPLETE — %d/%d phases finished for %s",
            completed, len(PHASES), client_url,
        )

        return state

    async def _execute_phase(self, phase: Phase, state: PipelineState) -> PhaseResult:
        """Выполнить одну фазу пайплайна с ретраями.

        Args:
            phase: Определение фазы.
            state: Текущее состояние пайплайна.

        Returns:
            PhaseResult с результатом фазы.
        """
        t0 = time.time()
        retries_left = phase.contract.max_retries
        last_error = None
        tool_calls_made = []
        tool_results = {}

        while retries_left >= 0:
            try:
                # Шаг 1: Вызвать инструменты фазы
                if phase.tools:
                    tool_results, tool_names = await self._call_phase_tools(
                        phase, state, tool_calls_made,
                    )
                    tool_calls_made.extend(tool_names)

                # Шаг 2: Проверить на NO_DATA
                if self._is_no_data(tool_results, phase):
                    duration = time.time() - t0
                    return PhaseResult(
                        phase_id=phase.id,
                        status=PhaseStatus.NO_DATA,
                        data=tool_results,
                        duration_seconds=round(duration, 1),
                        tool_calls_made=tool_calls_made,
                    )

                # Шаг 3: LLM-интерпретация (если нужна)
                interpretation = None
                if phase.llm_interpret and phase.interpretation_prompt:
                    interpretation = await self._interpret_phase(
                        phase, tool_results, state,
                    )

                duration = time.time() - t0
                return PhaseResult(
                    phase_id=phase.id,
                    status=PhaseStatus.COMPLETED,
                    data=tool_results,
                    duration_seconds=round(duration, 1),
                    tool_calls_made=tool_calls_made,
                    llm_interpretation=interpretation,
                )

            except KeyExhaustionError:
                # Ротировать ключи и ретраить
                logger.warning(
                    "PipelineEngine: key exhaustion in phase %s, rotating keys (retries left: %d)",
                    phase.name, retries_left,
                )
                if phase.contract.retry_on_key_exhaustion:
                    self._rotate_keys()
                retries_left -= 1
                if retries_left < 0:
                    last_error = "Key exhaustion — все ключи исчерпаны"
                continue

            except PhaseTimeoutError:
                logger.error("PipelineEngine: phase %s timed out", phase.name)
                duration = time.time() - t0
                return PhaseResult(
                    phase_id=phase.id,
                    status=PhaseStatus.TIMED_OUT,
                    error_message=f"Таймаут {phase.contract.timeout}с",
                    duration_seconds=round(duration, 1),
                    tool_calls_made=tool_calls_made,
                )

            except Exception as e:
                last_error = str(e)
                logger.warning(
                    "PipelineEngine: phase %s error (retries left: %d): %s",
                    phase.name, retries_left, last_error,
                )
                retries_left -= 1

        # Все ретраи исчерпаны
        duration = time.time() - t0
        status = PhaseStatus.PERMANENT_FAILURE

        if phase.contract.allow_no_data and tool_results:
            status = PhaseStatus.NO_DATA
        elif phase.contract.on_permanent_failure == "abort":
            status = PhaseStatus.PERMANENT_FAILURE
        else:
            status = PhaseStatus.TOOL_FAILED

        return PhaseResult(
            phase_id=phase.id,
            status=status,
            data=tool_results if tool_results else None,
            error_message=last_error,
            duration_seconds=round(duration, 1),
            tool_calls_made=tool_calls_made,
        )

    async def _call_phase_tools(
        self,
        phase: Phase,
        state: PipelineState,
        already_called: list[str],
    ) -> tuple[dict, list[str]]:
        """Вызвать инструменты фазы НАПРЯМУЮ через Python-хендлеры.

        Больше не использует LLM для вызова инструментов.
        Каждый хендлер импортируется и вызывается с правильными параметрами,
        извлечёнными из состояния пайплайна.

        Args:
            phase: Фаза с определением инструментов.
            state: Состояние пайплайна.
            already_called: Уже вызванные инструменты (для ретраев).

        Returns:
            (tool_results_dict, tool_names_list)
        """
        if not phase.tools:
            return {}, []

        # Авто-определение имени клиента если не задано
        self._resolve_client_name(state)

        tool_results: dict[str, str] = {}
        tool_names: list[str] = []
        overall_timeout = min(phase.contract.timeout, _TOOL_CALL_TIMEOUT)

        async def _invoke_one(tool_name: str) -> None:
            """Вызвать один инструмент с таймаутом."""
            nonlocal tool_results, tool_names
            try:
                params = self._build_tool_params(tool_name, phase, state, tool_results)
                handler = _get_handler(tool_name)
                logger.info(
                    "PipelineEngine: calling %s(%s)",
                    tool_name,
                    ", ".join(f"{k}={str(v)[:60]}" for k, v in params.items() if v),
                )
                result = await asyncio.wait_for(
                    handler(**params),
                    timeout=overall_timeout,
                )
                tool_results[tool_name] = str(result) if result is not None else ""
                tool_names.append(tool_name)
                logger.info(
                    "PipelineEngine: %s → %d chars",
                    tool_name, len(tool_results[tool_name]),
                )
            except asyncio.TimeoutError:
                logger.error("PipelineEngine: %s timed out after %ds", tool_name, overall_timeout)
                tool_results[tool_name] = json.dumps({"error": f"timeout after {overall_timeout}s"})
                tool_names.append(tool_name)
            except Exception as e:
                logger.error("PipelineEngine: %s failed — %s", tool_name, e)
                tool_results[tool_name] = json.dumps({"error": str(e)})
                tool_names.append(tool_name)

        # Выполняем инструменты последовательно (сохраняем порядок фазы)
        for tool_name in phase.tools:
            if tool_name not in already_called:
                await _invoke_one(tool_name)

        return tool_results, tool_names

    def _resolve_client_name(self, state: PipelineState) -> None:
        """Авто-определить название клиники если не задано явно.

        Порядок:
        1. Если client_name уже задан — оставить как есть.
        2. Извлечь из домена (erasmile.ru → EraSmile).
        3. Попробовать из competitors данных (первый результат).
        """
        if state.client_name and state.client_name.strip():
            return

        # Извлекаем из домена
        url = state.client_url
        if url:
            from urllib.parse import urlparse
            parsed = urlparse(url if "://" in url else f"https://{url}")
            domain = parsed.netloc or parsed.path.split("/")[0]
            # Убираем www. и tld
            domain = domain.removeprefix("www.")
            domain = domain.rsplit(".", 1)[0]
            # Превращаем erasmile → EraSmile, sm-clinic → Sm-Clinic
            if "-" in domain:
                parts = [p.capitalize() for p in domain.split("-")]
                state.client_name = "-".join(parts)
            else:
                state.client_name = domain[0].upper() + domain[1:] if domain else ""
            logger.info("PipelineEngine: resolved client_name=%r from URL", state.client_name)

    def _build_tool_params(
        self,
        tool_name: str,
        phase: Phase,
        state: PipelineState,
        partial_results: dict[str, str] | None = None,
    ) -> dict:
        """Построить параметры для вызова инструмента.

        Извлекает нужные данные из состояния пайплайна:
        - client_url → url/website параметры
        - client_name → company_name/doctor_name параметры
        - accumulated_data → competitors, inn, и т.д.
        - partial_results → результаты уже выполненных инструментов ТЕКУЩЕЙ фазы
          (нужно для инструментов, которые зависят от предыдущих в той же фазе,
          например run_ci_analysis зависит от find_competitors)

        Args:
            tool_name: Имя инструмента (run_pagespeed, find_competitors, ...).
            phase: Текущая фаза.
            state: Состояние пайплайна.
            partial_results: Результаты уже выполненных инструментов в этой фазе.

        Returns:
            Словарь параметров для передачи в хендлер.
        """
        name = state.client_name or ""
        url = state.client_url or ""

        # ── URL-based tools ──────────────────────────────────────────
        if tool_name in ("run_pagespeed", "run_seo_audit"):
            return {"url" if tool_name == "run_seo_audit" else "website": url}

        if tool_name == "run_content_analysis":
            return {"url": url}

        if tool_name == "find_competitors":
            # Google Maps сам находит реальных географических соседей.
            # Perplexity-имена используем только для Deep Research раздела отчёта.
            params = {"url": url}
            return params

        # ── Company-based tools ──────────────────────────────────────
        if tool_name in ("run_hh_analysis", "run_smi_mentions", "run_review_platforms"):
            params: dict = {}
            if name:
                params["company_name"] = name
            # Для review_platforms передаём город (хендлер принимает city)
            if tool_name == "run_review_platforms":
                city = getattr(state, "client_city", "") or ""
                if city:
                    params["city"] = city
            return params

        if tool_name == "run_doctor_dossiers":
            # Ищем врачей клиники по company_name + специализации
            params = {}
            if name:
                params["company_name"] = name
            spec = getattr(state, "client_specialization", "") or ""
            if spec:
                params["specialization"] = spec
            return params

        # ── CI Analysis (нужны конкуренты) ──────────────────────────
        if tool_name == "run_ci_analysis":
            params: dict = {"url": url}
            competitors = self._extract_competitors_for_ci(state, partial_results or {})
            if competitors:
                params["competitors"] = competitors
                logger.info(
                    "PipelineEngine: CI analysis with %d competitors: %s",
                    len(competitors),
                    [c["name"] for c in competitors],
                )
            else:
                logger.warning(
                    "PipelineEngine: CI analysis — NO competitors extracted "
                    "(find_competitors may have failed or returned empty). "
                    "Skipping CI analysis."
                )
            # Pass specialization and city for better analysis
            spec = getattr(state, "client_specialization", "") or ""
            if spec:
                params["specialization"] = spec
            city = getattr(state, "client_city", "") or ""
            if city:
                params["city"] = city
            return params

        # ── Financials (нужен INN) ──────────────────────────────────
        if tool_name == "find_company_financials":
            inn = self._extract_inn_from_state(state)
            if inn:
                return {"inn": inn}
            return {}  # Без INN хендлер вернёт ошибку

        # ── Content Gaps (нужен конкурент) ─────────────────────────
        if tool_name == "run_content_gaps":
            params = {"client_site": url}
            comp_url = self._extract_first_competitor_url(state)
            if comp_url:
                params["competitor_site"] = comp_url
            return params

        # ── Web Search (Perplexity / Forum Pains) ───────────────────
        if tool_name == "web_search":
            query = self._build_search_query(phase, state)
            return {"query": query, "limit": 5}

        # ── HTML Report ────────────────────────────────────────────
        if tool_name == "generate_html_report":
            self._persist_session_to_disk(state)
            return {
                "session_hash": state.session_id,
                "title": f"{name} — Scout Report",
                "client_name": name,
                "client_url": url,
            }

        # ── Publish Report ─────────────────────────────────────────
        if tool_name == "publish_scout_report":
            # Если generate_html_report уже опубликовал отчёт — используем его URL
            html_data = state.accumulated_data.get("HTML BUILD", {})
            if isinstance(html_data, dict):
                gen_result = html_data.get("generate_html_report", "")
                if isinstance(gen_result, str):
                    try:
                        parsed = json.loads(gen_result)
                        if parsed.get("url"):
                            return {"url": parsed["url"], "already_published": True}
                    except (json.JSONDecodeError, TypeError):
                        pass
            return {"slug": state.session_id}

        # ── Fallback ────────────────────────────────────────────────
        logger.warning("PipelineEngine: no param mapping for %s, using empty dict", tool_name)
        return {}

    # ── Helpers for param extraction ────────────────────────────────────

    def _extract_competitors_for_ci(
        self,
        state: PipelineState,
        partial_results: dict[str, str] | None = None,
    ) -> list[dict] | None:
        """Извлечь список конкурентов для CI-анализа.

        Сначала проверяет accumulated_data (для крос-фазных зависимостей),
        затем partial_results (для same-phase зависимостей: run_ci_analysis
        идёт после find_competitors в фазе COMPETITORS).
        """
        import json as _json

        raw = ""
        source = ""

        # Пробуем accumulated_data (уже завершённые фазы)
        comp_data = state.accumulated_data.get("COMPETITORS", {})
        if isinstance(comp_data, dict):
            raw = comp_data.get("find_competitors", "")
            if raw and isinstance(raw, str):
                source = "accumulated_data"

        # Если accumulated_data пуст — смотрим partial_results этой же фазы
        if (not raw or not isinstance(raw, str)) and partial_results:
            raw = partial_results.get("find_competitors", "")
            if raw and isinstance(raw, str):
                source = "partial_results"

        if not raw or not isinstance(raw, str):
            logger.warning(
                "PipelineEngine: _extract_competitors_for_ci — "
                "no find_competitors result in accumulated_data or partial_results"
            )
            return None

        logger.debug(
            "PipelineEngine: _extract_competitors_for_ci from %s (%d chars)",
            source, len(raw),
        )

        try:
            parsed = _json.loads(raw)
        except (_json.JSONDecodeError, TypeError):
            logger.warning(
                "PipelineEngine: _extract_competitors_for_ci — "
                "failed to parse find_competitors result as JSON"
            )
            return None

        competitors = parsed.get("competitors", [])
        if not competitors:
            logger.warning(
                "PipelineEngine: _extract_competitors_for_ci — "
                "find_competitors returned empty competitors list. "
                "Raw keys: %s",
                list(parsed.keys())[:5] if isinstance(parsed, dict) else type(parsed).__name__,
            )
            return None

        result = []
        for c in competitors[:5]:
            name = c.get("brand_name") or c.get("legal_name", "")
            comp_url = c.get("website", "")
            if name and comp_url:
                result.append({"name": name, "url": comp_url})

        if not result:
            logger.warning(
                "PipelineEngine: _extract_competitors_for_ci — "
                "%d competitors parsed but none have both name and website",
                len(competitors),
            )
            return None

        logger.info(
            "PipelineEngine: extracted %d competitors for CI from %s",
            len(result), source,
        )
        return result

    def _extract_inn_from_state(self, state: PipelineState) -> str | None:
        """Извлечь ИНН клиента для FINANCE-фазы.

        Приоритет:
        1. ИНН клиента (из scraping /contacts — client_inn)
        2. Fallback: ИНН первого конкурента (если клиентский не найден)
        """
        # Приоритет 1: ИНН клиента (найден через scraping)
        client_inn = getattr(state, "client_inn", "") or ""
        if client_inn:
            return str(client_inn)

        # Fallback: ИНН первого конкурента
        comp_data = state.accumulated_data.get("COMPETITORS", {})
        if not isinstance(comp_data, dict):
            return None

        raw = comp_data.get("find_competitors", "")
        if not raw or not isinstance(raw, str):
            return None

        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None

        for c in parsed.get("competitors", []):
            inns = c.get("inns", [])
            if inns:
                return str(inns[0])
            inn = c.get("inn", "")
            if inn:
                return str(inn)
        return None

    def _extract_first_competitor_url(self, state: PipelineState) -> str | None:
        """Извлечь URL первого конкурента для content_gaps."""
        comp_data = state.accumulated_data.get("COMPETITORS", {})
        if not isinstance(comp_data, dict):
            return None

        raw = comp_data.get("find_competitors", "")
        if not raw or not isinstance(raw, str):
            return None

        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None

        for c in parsed.get("competitors", []):
            # Множество возможных полей с URL
            for url_field in ("website", "url", "site", "website_url", "link"):
                website = c.get(url_field, "")
                if website and website.startswith("http"):
                    return website
        return None

    def _extract_competitor_names_from_perplexity(
        self,
        state: PipelineState,
    ) -> list[str] | None:
        """Извлечь имена конкурентов из PERPLEXITY-интерпретации.

        Perplexity (deep research) должен обнаружить основных конкурентов
        в городе/нише клиента. LLM-интерпретация перечисляет их имена.

        Возвращает список имён (до 5) или None если не удалось извлечь.
        """
        interp = state.accumulated_data.get("PERPLEXITY_interpretation", "")
        if not interp or not isinstance(interp, str) or len(interp) < 30:
            return None

        # Пропускаем «технические» ответы (LLM пытается что-то «запустить»)
        if any(phrase in interp for phrase in (
            "запускаю", "попробую", "обойти ошибку", "ротацию ключей",
        )):
            logger.warning("PipelineEngine: PERPLEXITY_interpretation looks like agent-talk, skipping")
            return None

        import re

        names = set()

        # Пытаемся распарсить как JSON (если LLM вернула структурированно)
        try:
            parsed = json.loads(interp)
            if isinstance(parsed, dict):
                json_names = parsed.get("competitors") or parsed.get("ключевые_игроки") or []
                if isinstance(json_names, list) and json_names:
                    return [str(n) for n in json_names[:5] if isinstance(n, str) and len(n) > 1]
        except (json.JSONDecodeError, TypeError):
            pass

        # ── Метод 1: Нумерованный список с болдом «Название» ─────────
        # Формат: 1. **«Название»**, 2. **«Название»** — описание
        for m in re.finditer(r'\d+\.\s*\*\*[«"]([^»"]+?)[»"]\*\*', interp):
            candidate = m.group(1).strip()
            if len(candidate) >= 4 and not candidate.startswith(("http", "www.")):
                names.add(candidate)

        if names:
            logger.info(
                "PipelineEngine: extracted %d competitor names from numbered list",
                len(names),
            )
            return list(names)[:7]

        # ── Метод 2: Любые кавычки с фильтрацией specialization-фраз ─
        # Фильтруем фразы, которые выглядят как specialization, а не название клиники
        _spec_keywords = [
            "косметология", "трихология", "дерматология", "эстетическая медицина",
            "эстетика тела", "аппаратная коррекция", "лазерная",
            "стоматология", "хирургия", "гинекология", "урология",
            "офтальмология", "неврология", "кардиология", "терапия",
            "педиатрия", "рентгенология", "эндоскопия", "флебология",
            "отоларингология", "маммология", "диетология", "нутрициология",
            "реабилитация", "мануальная терапия", "остеопатия", "психотерапия",
        ]

        for m in re.finditer(r'[«"]([^»"]+?)[»"]', interp):
            candidate = m.group(1).strip()
            # Фильтруем служебные слова и короткие/URL-подобные строки
            if len(candidate) < 4:
                continue
            if len(candidate) > 60:  # Слишком длинное для названия клиники
                continue
            if candidate.startswith(("http", "www.", "клиник", "медицинск")):
                continue
            if candidate.lower() in (
                "санкт-петербург", "москва", "город", "находится", "ошибка",
                "инвестиций во внешность",
            ):
                continue
            # Фильтруем specialization-фразы: если текст выглядит как перечисление специализаций
            candidate_lower = candidate.lower()
            if " + " in candidate_lower or " и " in candidate_lower:
                # Проверяем, не является ли это specialization-перечислением
                spec_count = sum(
                    1 for kw in _spec_keywords if kw in candidate_lower
                )
                # Если 2+ specialization-ключей и есть " + " → это не название клиники
                if spec_count >= 2:
                    continue
            # Фильтруем чисто specialization-фразы без названия
            if candidate_lower in _spec_keywords or candidate_lower.rstrip(".,;") in _spec_keywords:
                continue
            names.add(candidate)

        if names:
            logger.info(
                "PipelineEngine: extracted %d competitor names from guillemets",
                len(names),
            )
            return list(names)[:7]

        # ── Метод 3: строки вида "1. Название", "— Название:", "**Название**" ─
        for m in re.finditer(
            r'(?:^|\n)\s*(?:\d+\.\s*|[-–—]\s*|\*\*)\s*([А-ЯA-Z][\w\s&.\-]{3,40}?)(?::|\.|,|\n| —|$)',
            interp,
        ):
            candidate = m.group(1).strip()
            if len(candidate) > 4 and candidate.lower() not in (
                "клиника", "центр", "медицинский", "стоматология", "вывод", "заключение",
                "город", "шаг", "конкуренты", "анализ", "результат",
            ):
                names.add(candidate)

        return list(names)[:7] if names else None

    def _build_search_query(self, phase: Phase, state: PipelineState) -> str:
        """Построить поисковый запрос для web_search в зависимости от фазы."""
        name = state.client_name or "клиника"
        url = state.client_url or ""

        if phase.name == "PERPLEXITY":
            city = getattr(state, "client_city", "") or ""
            specialization = getattr(state, "client_specialization", "") or ""
            if city:
                # Город уже определён через scraping /contacts — точный поиск
                query = (
                    f'частные клиники конкуренты "{name}" в городе {city} '
                )
                if specialization:
                    query += f'{specialization} в {city} '
                query += f'медицинские центры {city} отзывы рейтинг'
                return query
            # Fallback: поиск с URL (старое поведение)
            query = (
                f'"{name}" {url} адрес город контакты где находится клиника '
            )
            if specialization:
                query += f'{specialization} '
            query += f'конкуренты медицинские центры частные клиники отзывы рейтинг'
            return query
        elif phase.name == "FORUM PAINS":
            # Боли пациентов на форумах
            city = getattr(state, "client_city", "") or ""
            specialization = getattr(state, "client_specialization", "") or ""
            query = f'"{name}" отзывы пациентов форум отзовик '
            if specialization:
                query += f'{specialization} '
            if city:
                query += f'в городе {city} '
            query += f'проблемы жалобы мнения'
            return query

        # Default
        return f'"{name}" медицинский центр отзывы анализ'

    @staticmethod
    def _normalize_city_name(city: str) -> str:
        """Привести название города к именительному падежу.

        Regex'ы детекции захватывают город в предложном падеже
        («в Москве», «в Санкт-Петербурге») — нормализуем в именительный.
        """
        if not city or len(city) < 3:
            return city

        # Таблица известных пар (предложный → именительный)
        _prepositional_to_nominative = {
            "москве": "Москва",
            "санкт-петербурге": "Санкт-Петербург",
            "екатеринбурге": "Екатеринбург",
            "новосибирске": "Новосибирск",
            "казани": "Казань",
            "нижнем новгороде": "Нижний Новгород",
            "челябинске": "Челябинск",
            "омске": "Омск",
            "самаре": "Самара",
            "ростове-на-дону": "Ростов-на-Дону",
            "уфе": "Уфа",
            "красноярске": "Красноярск",
            "перми": "Пермь",
            "воронеже": "Воронеж",
            "волгограде": "Волгоград",
            "краснодаре": "Краснодар",
            "сочи": "Сочи",  # несклоняемое
            "тюмени": "Тюмень",
            "ижевске": "Ижевск",
            "барнауле": "Барнаул",
            "иркутске": "Иркутск",
            "хабаровске": "Хабаровск",
            "владивостоке": "Владивосток",
            "ярославле": "Ярославль",
            "томске": "Томск",
            "оренбурге": "Оренбург",
            "туле": "Тула",
            "рязани": "Рязань",
            "пензе": "Пенза",
            "липецке": "Липецк",
            "астрахани": "Астрахань",
            "калининграде": "Калининград",
            "сургуте": "Сургут",
            "твери": "Тверь",
            "белгороде": "Белгород",
            "кирове": "Киров",
            # Составные: «в Ростове-на-Дону» regex захватит «Ростове-на-Дону»
        }
        key = city.lower().strip()
        if key in _prepositional_to_nominative:
            return _prepositional_to_nominative[key]
        return city

    async def _detect_city_from_contacts(self, url: str) -> str | None:
        """Попытаться извлечь город из страницы /contacts клиники.

        Скрейпит страницы /contacts, /kontakty, /contact — парсит HTML,
        ищет физический адрес и извлекает название города.

        Это детерминированный метод, не зависит от API-ключей.
        Если адрес найден — город используется во всех фазах пайплайна.
        Если нет — fallback на LLM-инференс из домена.

        Args:
            url: URL сайта клиники.

        Returns:
            Название города или None.
        """
        import re
        from html import unescape
        from urllib.parse import urljoin
        from urllib.request import Request, urlopen

        if not url:
            return None

        if not url.startswith("http"):
            url = f"https://{url}"

        contacts_paths = ["/contacts", "/kontakty", "/contact", "/kontakt"]

        for path in contacts_paths:
            try:
                contacts_url = urljoin(url, path)
                logger.info(
                    "PipelineEngine: trying to fetch %s for city detection",
                    contacts_url,
                )

                loop = asyncio.get_running_loop()

                def _fetch():
                    req = Request(
                        contacts_url,
                        headers={
                            "User-Agent": (
                                "Mozilla/5.0 (compatible; HermesCityDetector/1.0)"
                            ),
                        },
                    )
                    with urlopen(req, timeout=15) as resp:
                        if resp.status != 200:
                            raise Exception(f"HTTP {resp.status}")
                        return resp.read().decode("utf-8", errors="ignore")

                html = await loop.run_in_executor(None, _fetch)

                # Очищаем HTML-теги
                text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
                text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
                text = re.sub(r'<[^>]+>', ' ', text)
                text = unescape(text)
                text = re.sub(r'\s+', ' ', text)

                if len(text) < 100:
                    logger.debug(
                        "PipelineEngine: %s returned too little content (%d chars)",
                        contacts_url, len(text),
                    )
                    continue

                # ── Извлечение города из контента ──────────────────────
                # Российские сайты используют «в Городе» (предложный падеж),
                # а не «г. Город» (именительный). Ищем все варианты.

                found_cities: list[tuple[str, str]] = []

                # Шаг 0: Извлекаем из <title> (самый надёжный источник)
                title_match = re.search(
                    r'<title>[^<]*?(?:в|города?)\s+([А-ЯЁ][а-яё]+(?:\s*[–—-]\s*[А-ЯЁ][а-яё]+)?)',
                    html, re.IGNORECASE,
                )
                if title_match:
                    city_raw = title_match.group(1).strip()
                    city_raw = re.sub(r'\s+', ' ', city_raw)
                    if len(city_raw) > 2 and city_raw.lower() not in ("россия", "рф", "область"):
                        found_cities.append((city_raw, "<title>"))

                # Шаг 1: meta description
                meta_match = re.search(
                    r'<meta[^>]+name="description"[^>]+content="[^"]*?(?:в|города?)\s+([А-ЯЁ][а-яё]+(?:\s*[–—-]\s*[А-ЯЁ][а-яё]+)?)',
                    html, re.IGNORECASE,
                )
                if meta_match:
                    city_raw = meta_match.group(1).strip()
                    if len(city_raw) > 2 and city_raw.lower() not in ("россия", "рф", "область"):
                        found_cities.append((city_raw, "<meta>"))

                # Шаг 2: паттерны в тексте
                text_patterns = [
                    # «клиника/центр в Городе» (самый частый)
                    r'(?:клиник[аиые]|центр[аые]?|филиал[аы]?|отделение|стационар)\s+(?:в|по\s+адресу\s+в)\s+(?:г\.\s*|городе?\s+)?([А-ЯЁ][а-яё]+(?:\s*[–—-]\s*[А-ЯЁ][а-яё]+)?)',
                    # г. Москва
                    r'г\.\s*([А-ЯЁ][а-яё]+(?:\s*[–—-]\s*[А-ЯЁ][а-яё]+)?)',
                    # город Москва
                    r'город\s+([А-ЯЁ][а-яё]+(?:\s*[–—-]\s*[А-ЯЁ][а-яё]+)?)',
                    # «находится/расположен в Городе»
                    r'(?:находит(?:ся|ься)|расположен[аы]?)\s+в\s+(?:г\.\s*|городе?\s+)?([А-ЯЁ][а-яё]+(?:\s*[–—-]\s*[А-ЯЁ][а-яё]+)?)',
                ]

                for pattern in text_patterns:
                    match = re.search(pattern, text)
                    if match:
                        city = match.group(1).strip()
                        city_lower = city.lower().rstrip("еиуюой")
                        # Фильтры
                        if city_lower in (
                            "россия", "рф", "российск", "федерац",
                            "московск", "ленинградск", "област",
                            "московская", "ленинградская",
                        ):
                            continue
                        if len(city) < 3:
                            continue
                        found_cities.append((city, pattern[:60]))

                # Шаг 3: Если ничего не нашли — ищем адресный паттерн с защитой от метро
                if not found_cities:
                    addr_match = re.search(
                        r'(?<!м\.\s)(?<!метро\s)([А-ЯЁ][а-яё]+(?:\s*[–—-]\s*[А-ЯЁ][а-яё]+)?),\s*(?:ул\.|улица|пр\.|проспект|пер\.|д\.|дом|ш\.|шоссе|наб\.|бульвар)',
                        text,
                    )
                    if addr_match:
                        city = addr_match.group(1).strip()
                        if len(city) > 3 and city.lower() not in (
                            "россия", "рф", "российская",
                        ):
                            found_cities.append((city, "address fallback"))

                if found_cities:
                    city = self._normalize_city_name(found_cities[0][0])
                    logger.info(
                        "PipelineEngine: detected city=%r from %s (source: %s)",
                        city, contacts_url, found_cities[0][1],
                    )
                    return city

                logger.debug(
                    "PipelineEngine: no city found in %s (%d chars of text)",
                    contacts_url, len(text),
                )

            except Exception as e:
                logger.debug(
                    "PipelineEngine: failed to fetch %s: %s", path, e,
                )
                continue

        return None

    async def _detect_specialization(self, url: str) -> str | None:
        """Определить медицинскую специализацию клиники по содержимому сайта.

        Фетчит главную страницу сайта через urllib (без API-ключей),
        извлекает текст, вызывает LLM для семантического анализа.

        Это предотвращает галлюцинации PERPLEXITY: без знания содержимого
        сайта LLM может неверно определить специализацию по названию домена
        (например, toriclinic.ru → офтальмология вместо косметологии).

        Args:
            url: URL сайта клиники.

        Returns:
            Строка со специализацией или None.
        """
        import re
        from html import unescape
        from urllib.request import Request, urlopen

        if not url:
            return None

        if not url.startswith("http"):
            url = f"https://{url}"

        try:
            logger.info(
                "PipelineEngine: fetching main page %s for specialization detection",
                url,
            )

            loop = asyncio.get_running_loop()

            def _fetch():
                req = Request(
                    url,
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (compatible; HermesSpecDetector/1.0)"
                        ),
                    },
                )
                with urlopen(req, timeout=15) as resp:
                    if resp.status != 200:
                        raise Exception(f"HTTP {resp.status}")
                    return resp.read().decode("utf-8", errors="ignore")

            html = await loop.run_in_executor(None, _fetch)

            # ── Извлечение текста ──────────────────────────────────
            # Удаляем скрипты и стили
            text = re.sub(
                r'<script[^>]*>.*?</script>', '', html,
                flags=re.DOTALL | re.IGNORECASE,
            )
            text = re.sub(
                r'<style[^>]*>.*?</style>', '', text,
                flags=re.DOTALL | re.IGNORECASE,
            )

            # Извлекаем ключевые элементы
            title_match = re.search(r'<title[^>]*>(.*?)</title>', text, re.IGNORECASE)
            title = unescape(title_match.group(1).strip()) if title_match else ""

            meta_match = re.search(
                r'<meta[^>]+name="description"[^>]+content="([^"]*)"',
                html, re.IGNORECASE,
            )
            meta_desc = unescape(meta_match.group(1).strip()) if meta_match else ""

            # H1-H2 заголовки
            h1_matches = re.findall(
                r'<h1[^>]*>(.*?)</h1>', text, re.IGNORECASE,
            )
            h2_matches = re.findall(
                r'<h2[^>]*>(.*?)</h2>', text, re.IGNORECASE,
            )

            # Очищаем от тегов
            def _clean(s: str) -> str:
                s = re.sub(r'<[^>]+>', ' ', s)
                s = unescape(s)
                s = re.sub(r'\s+', ' ', s)
                return s.strip()

            title = _clean(title)
            meta_desc = _clean(meta_desc)
            h1_text = " | ".join(_clean(h) for h in h1_matches[:5])
            h2_text = " | ".join(_clean(h) for h in h2_matches[:5])

            # Body — первые ~3000 символов
            body_text = _clean(text)
            body_text = body_text[:3000]

            if len(body_text) < 100:
                logger.warning(
                    "PipelineEngine: main page %s returned too little content (%d chars)",
                    url, len(body_text),
                )
                return None

            # ── LLM-анализ специализации ───────────────────────────
            specialization_prompt = (
                "Определи медицинскую специализацию клиники по содержимому сайта.\n\n"
                f"<title>{title}</title>\n"
                f"<meta>{meta_desc}</meta>\n"
                f"<h1>{h1_text}</h1>\n"
                f"<h2>{h2_text}</h2>\n"
                f"<body_sample>{body_text}</body_sample>\n\n"
                "Ответь одним предложением: «Специализация: ...». "
                "Не выдумывай, опирайся только на текст сайта. "
                "Если в тексте указано несколько направлений — перечисли их. "
                "Если специализацию определить невозможно — ответь «Специализация: не определена»."
            )

            try:
                from run_agent import AIAgent

                agent = AIAgent(
                    base_url=OMNIROUTE_URL,
                    api_key=OMNIROUTE_AUTH,
                    provider="custom",
                    api_mode="openai_chat",
                    model=DEFAULT_MODEL,
                    enabled_toolsets=[],
                    max_iterations=1,
                    quiet_mode=True,
                    max_tokens=500,
                )

                response = await loop.run_in_executor(
                    None,
                    lambda: agent.run_conversation(specialization_prompt),
                )

                reply = response.get(
                    "final_response",
                    response.get("response", ""),
                )
                reply = str(reply).strip()

                # ── Парсинг ответа ─────────────────────────────────
                spec_match = re.search(
                    r'специализация[:\s]*([^.\n]+)',
                    reply, re.IGNORECASE,
                )
                if spec_match:
                    spec = spec_match.group(1).strip().lower()
                    # Фильтруем явные «не определено»
                    if spec in ("не определена", "не определено", "не определена."):
                        logger.info(
                            "PipelineEngine: specialization not determined for %s",
                            url,
                        )
                        return None
                    logger.info(
                        "PipelineEngine: detected specialization=%r for %s",
                        spec, url,
                    )
                    return spec

                logger.info(
                    "PipelineEngine: could not parse specialization from LLM response: %r",
                    reply[:200],
                )
                return None

            except Exception as e:
                logger.warning(
                    "PipelineEngine: LLM specialization detection failed for %s: %s",
                    url, e,
                )
                return None

        except Exception as e:
            logger.warning(
                "PipelineEngine: specialization detection failed for %s: %s",
                url, e,
            )
            return None

    async def _detect_client_inn(self, url: str) -> str | None:
        """Извлечь ИНН/ОГРН клиники из страницы /contacts или /rekvizity.

        Российские медицинские сайты обязаны публиковать ИНН и ОГРН
        (закон о защите прав потребителей). Обычно в футере /contacts.

        Args:
            url: URL сайта клиники.

        Returns:
            Строка с ИНН (10-12 цифр) или None.
        """
        import re
        from urllib.parse import urljoin
        from urllib.request import Request, urlopen

        if not url:
            return None

        if not url.startswith("http"):
            url = f"https://{url}"

        # Страницы где может быть ИНН
        inn_paths = ["/contacts", "/kontakty", "/contact", "/rekvizity", "/about"]

        for path in inn_paths:
            try:
                page_url = urljoin(url, path)
                logger.debug(
                    "PipelineEngine: trying %s for INN detection",
                    page_url,
                )

                loop = asyncio.get_running_loop()

                def _fetch():
                    req = Request(
                        page_url,
                        headers={
                            "User-Agent": (
                                "Mozilla/5.0 (compatible; HermesINNDetector/1.0)"
                            ),
                        },
                    )
                    with urlopen(req, timeout=10) as resp:
                        if resp.status != 200:
                            raise Exception(f"HTTP {resp.status}")
                        return resp.read().decode("utf-8", errors="ignore")

                html = await loop.run_in_executor(None, _fetch)

                # Очищаем HTML
                text = re.sub(
                    r'<script[^>]*>.*?</script>', '', html,
                    flags=re.DOTALL | re.IGNORECASE,
                )
                text = re.sub(
                    r'<style[^>]*>.*?</style>', '', text,
                    flags=re.DOTALL | re.IGNORECASE,
                )
                text = re.sub(r'<[^>]+>', ' ', text)
                text = re.sub(r'\s+', ' ', text)

                # Ищем ИНН (10 или 12 цифр)
                inn_patterns = [
                    r'[иИ][нН][нН][:\s]*(\d{10,12})',
                    r'[iI][nN][nN][:\s]*(\d{10,12})',
                    r'ИНН\s*(?:организации|компании|клиники)?[:\s]*(\d{10,12})',
                ]
                for pat in inn_patterns:
                    m = re.search(pat, text)
                    if m:
                        inn = m.group(1)
                        logger.info(
                            "PipelineEngine: detected client INN=%s from %s",
                            inn, page_url,
                        )
                        return inn

                # ОГРН как fallback
                ogrn_match = re.search(
                    r'[оО][гГ][рР][нН][:\s]*(\d{13,15})', text,
                )
                if ogrn_match:
                    ogrn = ogrn_match.group(1)
                    logger.info(
                        "PipelineEngine: detected client OGRN=%s from %s",
                        ogrn, page_url,
                    )
                    return ogrn

            except Exception as e:
                logger.debug(
                    "PipelineEngine: INN detection failed for %s: %s",
                    page_url, e,
                )
                continue

        return None

    async def _interpret_phase(
        self,
        phase: Phase,
        tool_results: dict,
        state: PipelineState,
    ) -> str:
        """LLM-интерпретация данных фазы.

        Узкий промпт ТОЛЬКО с данными этой фазы.
        LLM НЕ видит другие фазы и НЕ принимает решений о пайплайне.

        Args:
            phase: Фаза с interpretation_prompt.
            tool_results: Результаты инструментов фазы.
            state: Состояние пайплайна.

        Returns:
            Текст интерпретации.
        """
        if not phase.interpretation_prompt:
            return ""

        # Формируем данные для интерпретации
        data_text = "\n\n".join(
            f"### {name}\n{result[:3000]}"
            for name, result in tool_results.items()
        ) if tool_results else "Нет данных"

        # ── QC CRITIQUE: добавляем URL HTML-отчёта ─────────────────
        if phase.name == "QC CRITIQUE":
            html_data = state.accumulated_data.get("HTML BUILD", {})
            if isinstance(html_data, dict):
                gen_result = html_data.get("generate_html_report", "")
                if isinstance(gen_result, str):
                    try:
                        parsed = json.loads(gen_result)
                        report_url = parsed.get("url", "")
                        if report_url:
                            data_text = (
                                f"HTML-отчёт опубликован по адресу: {report_url}\n\n"
                                f"Проверь отчёт по этому URL. Если не можешь открыть — "
                                f"проверь логически по данным, которые были собраны в предыдущих фазах."
                            )
                    except (json.JSONDecodeError, TypeError):
                        pass

        # Подготовка переменных для форматирования промпта
        format_vars = {
            "client_url": state.client_url,
            "client_city": getattr(state, "client_city", "") or "не определён",
            "client_specialization": getattr(state, "client_specialization", "") or "не определена",
        }

        prompt = (
            f"Данные фазы «{phase.name}» для клиента {state.client_name or state.client_url}:\n\n"
            f"{data_text}\n\n"
            f"---\n\n"
            f"{phase.interpretation_prompt.format(**format_vars)}"
        )

        try:
            from run_agent import AIAgent

            agent = AIAgent(
                base_url=OMNIROUTE_URL,
                api_key=OMNIROUTE_AUTH,
                provider="custom",
                api_mode="openai_chat",
                model=DEFAULT_MODEL,
                enabled_toolsets=[],  # Без инструментов — чистый LLM
                max_iterations=1,
                quiet_mode=True,
                max_tokens=4000,
            )

            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                lambda: agent.run_conversation(prompt),
            )

            reply = response.get("final_response", response.get("response", ""))
            return str(reply)[:4000]

        except Exception as e:
            logger.error("PipelineEngine: LLM interpretation failed for %s: %s", phase.name, e)
            return f"[Ошибка интерпретации: {e}]"

    def _is_no_data(self, tool_results: dict, phase: Phase) -> bool:
        """Проверить, является ли отсутствие данных легитимным исходом.

        Returns True если:
        - allow_no_data=True в контракте И
        - Все результаты инструментов — пустые или содержат только ошибки

        НЕ считает no_data если хотя бы один инструмент вернул реальные данные
        (> 500 chars или с явными признаками успеха).
        """
        if not phase.contract.allow_no_data:
            return False

        if not tool_results:
            return True

        # Признаки того, что данные реальные (не ошибка/пустышка)
        success_markers = [
            '"total_review_count"', '"competitors"', '"platforms"',
            '"reviews_count"', '"avg_rating"', '"results"',
            '"pagespeed_score"', '"seo_score"',
        ]

        for result in tool_results.values():
            result_str = str(result).strip()

            # Пустой результат → пропускаем
            if len(result_str) < 20:
                continue

            # Проверяем на явные признаки успешных данных
            result_lower = result_str.lower()
            for marker in success_markers:
                if marker.lower() in result_lower:
                    return False  # Есть реальные данные

            # Большой результат без error на верхнем уровне → данные
            try:
                parsed = json.loads(result_str)
                if isinstance(parsed, dict):
                    # Если есть ключи кроме error/detail → данные
                    non_error_keys = [k for k in parsed if k not in ("error", "detail", "status")]
                    if non_error_keys and len(result_str) > 500:
                        return False
                    # Если только error → это ошибка, не данные
                    if parsed.get("error") and len(parsed) <= 2:
                        continue
            except (json.JSONDecodeError, TypeError):
                pass

            # Строковый результат > 500 символов → вероятно данные
            if len(result_str) > 500:
                return False

        return True

    def _persist_state(self, state: PipelineState) -> None:
        """Сохранить состояние пайплайна в in-memory store для polling."""
        # Build phase_id → name lookup (float ids, can't index list)
        phase_names: dict[float, str] = {p.id: p.name for p in PHASES}
        phases_data = []
        for pid, pr in state.phases.items():
            phases_data.append({
                "id": pid,
                "name": phase_names.get(pid, f"phase_{pid}"),
                "status": pr.status.value,
                "duration_seconds": pr.duration_seconds,
                "tool_calls": pr.tool_calls_made,
                "has_interpretation": pr.llm_interpretation is not None,
                "error": pr.error_message,
            })

        store_pipeline_state(state.session_id, {
            "session_id": state.session_id,
            "client_url": state.client_url,
            "current_phase": state.current_phase,
            "total_phases": len(PHASES),
            "phases": phases_data,
            "started_at": state.started_at,
        })

    def _persist_session_to_disk(self, state: PipelineState) -> None:
        """Сохранить накопленные данные пайплайна в session_archive на диск.

        Необходимо перед вызовом generate_html_report, который читает данные с диска.
        """
        try:
            from app.tools.session_archive import save_tool_output, upsert_metadata

            for key, value in state.accumulated_data.items():
                if isinstance(value, (dict, list)):
                    save_tool_output(state.session_id, key, value)
                elif isinstance(value, str) and len(str(value).strip()) > 10:
                    save_tool_output(state.session_id, key, {"content": str(value)})

            # Сохраняем metadata
            completed = sum(
                1 for r in state.phases.values()
                if r.status.value in ("completed", "no_data")
            )
            failed = sum(
                1 for r in state.phases.values()
                if r.status.value in ("permanent_failure", "tool_failed", "timed_out")
            )
            upsert_metadata(
                state.session_id,
                url=state.client_url,
                completed_phases=completed,
                failed_phases=failed,
                total_phases=len(state.phases),
                started_at=state.started_at,
            )
            logger.info(
                "PipelineEngine: persisted %d keys to session_archive/%s",
                len(state.accumulated_data), state.session_id,
            )
        except Exception as e:
            logger.error("PipelineEngine: session persist failed: %s", e)

    def _rotate_keys(self) -> bool:
        """Ротировать API-ключи.

        Вызывает зарегистрированный key_rotator.
        Также пробует firecrawl_key_bank.get_next_key() для ротации Firecrawl-ключей.

        Returns:
            True если ключи обновлены.
        """
        rotated = False

        # Способ 1: зарегистрированный rotator (из main.py)
        if self._key_rotator:
            try:
                rotated = self._key_rotator()
                logger.info("PipelineEngine: key rotator called — success=%s", rotated)
            except Exception as e:
                logger.error("PipelineEngine: key rotator failed: %s", e)

        # Способ 2: firecrawl_key_bank — пометить текущий ключ и взять следующий
        try:
            from app.tools.firecrawl_key_bank import (
                get_key_with_fallback,
                mark_exhausted,
            )
            # Получаем следующий ключ (старый implicitly exhausted)
            new_key = get_key_with_fallback()
            if new_key:
                logger.info("PipelineEngine: rotated to next Firecrawl key (bank)")
                rotated = True
        except ImportError:
            logger.debug("PipelineEngine: firecrawl_key_bank not available")

        return rotated


# ── Pipeline State Store ───────────────────────────────────────────
# In-memory хранилище для polling через /api/pipeline/status/{session_id}
_pipeline_states: dict[str, dict] = {}


def store_pipeline_state(session_id: str, state_data: dict) -> None:
    """Сохранить состояние пайплайна для polling."""
    _pipeline_states[session_id] = state_data


def get_pipeline_state(session_id: str) -> dict | None:
    """Получить состояние пайплайна."""
    return _pipeline_states.get(session_id)


def cleanup_pipeline_state(session_id: str) -> None:
    """Удалить состояние пайплайна из памяти после завершения."""
    _pipeline_states.pop(session_id, None)
    logger.debug("PipelineEngine: cleaned up state for %s", session_id)


class KeyExhaustionError(Exception):
    """API-ключ исчерпал лимиты."""
    pass


class PhaseTimeoutError(Exception):
    """Фаза превысила таймаут."""
    pass
