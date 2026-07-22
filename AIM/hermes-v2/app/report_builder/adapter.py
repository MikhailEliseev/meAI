"""Адаптер v2 collected_results → v1-shape data dict для build_report_html.

v2 pipeline хранит результаты тулов как ``collected_results: dict[str, str]`` где
значения — JSON-строки (или plain text для quick_overview). Этот модуль преобразует
их в структуру ``data``, которую ждёт ``build_report_html`` (перенесённая из v1).

Mapping (v2 tool → v1 phase_key → label)::

    extract_clinic_profile → PROFILE_interp      → "Профиль клиники"
    quick_overview         → OVERVIEW_interp     → "Обзор рынка"
    find_competitors       → COMPETITORS_interp  → "Конкуренты"
    run_review_platforms   → REVIEWS_interp      → "Отзывы пациентов"
"""

import json
import logging

logger = logging.getLogger(__name__)


# Mapping: v2 tool name → (v1 phase_key, label)
# phase_key используется как data[f"{phase_key}_interp"]["content"]
_TOOL_TO_SECTION = [
    ("extract_clinic_profile", "PROFILE",     "Профиль клиники"),
    ("quick_overview",         "OVERVIEW",    "Обзор рынка"),
    ("find_competitors",       "COMPETITORS", "Конкуренты"),
    ("run_review_platforms",   "REVIEWS",     "Отзывы пациентов"),
]


def _safe_load_json(raw: str) -> dict | None:
    """Безопасно распарсить JSON-строку. Вернуть None если не JSON."""
    if not raw or not isinstance(raw, str):
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


def _looks_like_markdown_or_text(s: str) -> bool:
    """Эвристика: строка содержит осмысленный markdown/plain-text контент
    (а не чистый JSON-объект без форматирования)."""
    if not s or not s.strip():
        return False
    stripped = s.strip()
    # Чистый JSON-объект с одной строкой без переносов — не подходит как контент
    if stripped.startswith("{") and "\n" not in stripped:
        return False
    return True


def _format_tool_result_as_markdown(tool_name: str, raw: str) -> str:
    """Преобразовать сырой результат тула в Markdown-контент для интерпретации.

    Используем v2 formatters для каждого тула — они уже дают готовый Markdown.
    Если formatter недоступен или упал — fallback на сырой текст.
    """
    if not raw or not raw.strip():
        return ""

    # Быстрая проверка: если это уже plain-text (quick_overview) — отдаём как есть
    if tool_name == "quick_overview":
        # quick_overview отдаёт свободный текст — используем напрямую
        return raw.strip()

    # Для остальных тулов используем v2 formatters
    try:
        if tool_name == "extract_clinic_profile":
            from app.formatters.profile import format_profile
            md, _ = format_profile(raw)
            return md
        if tool_name == "find_competitors":
            from app.formatters.competitors import format_competitors
            # client_revenue/profit передаются отдельно в revenue_block;
            # здесь таблица конкурентов без строки «ВЫ» (она дублирует блок).
            md = format_competitors(raw)
            return md
    except Exception as e:  # pragma: no cover — defensive
        logger.warning("adapter: formatter for %s failed: %s", tool_name, e)

    # Fallback: если это валидный JSON — показываем ключевые поля,
    # иначе отдаём как есть (plain text).
    parsed = _safe_load_json(raw)
    if parsed and isinstance(parsed, dict):
        return _dump_dict_as_markdown(parsed)
    return raw.strip()


def _dump_dict_as_markdown(d: dict, max_items: int = 12) -> str:
    """Превратить dict в простой Markdown-список (fallback).

    Глубина 1 уровень; вложенные dict/list — как JSON.
    """
    lines: list[str] = []
    for i, (k, v) in enumerate(d.items()):
        if i >= max_items:
            lines.append(f"- … (+{len(d) - max_items} ещё)")
            break
        if isinstance(v, (dict, list)):
            v_str = json.dumps(v, ensure_ascii=False)[:200]
            lines.append(f"- **{k}:** `{v_str}`")
        else:
            lines.append(f"- **{k}:** {v}")
    return "\n".join(lines)


def _extract_llm_section(llm_text: str, tool_name: str) -> str:
    """Попытаться извлечь из llm_text секцию, релевантную tool_name.

    llm_text — суммарный текст ответа LLM (может содержать анализ по нескольким
    фазам). Если в нём есть заголовок/маркер соответствующей секции — возвращаем
    кусок. Иначе возвращаем пустую строку (сигнал «используй formatted block»).

    Эвристика: ищем подстроки по label или имени тула.
    """
    if not llm_text or not llm_text.strip():
        return ""

    text = llm_text.strip()

    # Если llm_text короткий и без явной разбивки на секции — считаем его
    # общим анализом и используем целиком ТОЛЬКО для первой секции (PROFILE).
    # Для остальных — форматоры точнее.
    if tool_name != "extract_clinic_profile":
        return ""

    # Маркеры начала секции профиля
    markers = ["### Профиль", "## Профиль", "ПРОФИЛЬ КЛИНИКИ", "01 — О КЛИНИКЕ"]
    for marker in markers:
        idx = text.find(marker)
        if idx != -1:
            return text[idx:]

    # Если маркеров нет, но текст осмысленный (не JSON) — отдаём целиком
    if _looks_like_markdown_or_text(text) and not text.strip().startswith("{"):
        return text
    return ""


def build_data_dict(
    collected_results: dict[str, str],
    profile_cache: dict,
    llm_text: str = "",
) -> dict:
    """Преобразовать v2 collected_results в v1-shape data dict.

    Args:
        collected_results: dict tool_name → JSON-строка (или plain text).
            Ожидаемые ключи: ``extract_clinic_profile``, ``quick_overview``,
            ``find_competitors``, ``run_review_platforms``, ``company_financials``.
        profile_cache: dict с метаданными клиента (``company_name``, ``url``,
            ``inn``, ``city``…). Заполняется в pipeline.
        llm_text: Текст анализа от LLM (опционально). Если содержит осмысленный
            анализ по секции — используется как interpretation content вместо
            formatted block.

    Returns:
        dict в формате, ожидаемом ``build_report_html``::

            {
              "metadata": {"company_name": ..., "url": ...},
              "PROFILE_interp":     {"content": "...", "label": "Профиль клиники"},
              "OVERVIEW_interp":    {"content": "...", "label": "Обзор рынка"},
              "COMPETITORS_interp": {"content": "...", "label": "Конкуренты"},
              "REVIEWS_interp":     {"content": "...", "label": "Отзывы пациентов"},
              "FINANCE":      {"find_company_financials": "<json str>"},
              "COMPETITORS":  {"find_competitors": "<json str>"},
            }
    """
    profile_cache = profile_cache or {}
    collected_results = collected_results or {}

    # ── Metadata ──────────────────────────────────────────────────────────────
    company_name = (
        profile_cache.get("company_name")
        or profile_cache.get("brand_name")
        or "Клиника"
    )
    url = profile_cache.get("url") or profile_cache.get("website") or ""

    data: dict = {
        "metadata": {
            "company_name": company_name,
            "url": url,
            "inn": profile_cache.get("inn", ""),
        },
    }

    # ── Секции (интерпретации) ────────────────────────────────────────────────
    for tool_name, phase_key, label in _TOOL_TO_SECTION:
        raw_result = collected_results.get(tool_name, "")

        # 1. Пытаемся взять анализ из llm_text (если есть и релевантен)
        llm_section = _extract_llm_section(llm_text, tool_name)

        # 2. Иначе — formatted block из collected_results
        if _looks_like_markdown_or_text(llm_section):
            content = llm_section
        else:
            content = _format_tool_result_as_markdown(tool_name, raw_result)

        if content and content.strip():
            data[f"{phase_key}_interp"] = {
                "content": content,
                "label": label,
            }

    # ── Сырой JSON для revenue_block (читает эти ключи) ───────────────────────
    # v1: data["FINANCE"]["find_company_financials"] — вложенный JSON с
    # company.latest_revenue. В v2 company_financials уже плоский JSON
    # {"revenue": ..., "profit": ..., ...} — оборачиваем в {"company": ...}
    # для совместимости с v1 reader-логикой.
    fin_raw = collected_results.get("company_financials", "{}")
    fin_obj = _safe_load_json(fin_raw) if fin_raw else None
    if fin_obj:
        # company_financials в v2 плоский: revenue/profit/revenue_trend на верхнем
        # уровне. v1 reader искал fin.company.latest_revenue → нормализуем.
        normalized = {
            "company": {
                "latest_revenue": fin_obj.get("revenue") or fin_obj.get("latest_revenue"),
                "latest_profit": fin_obj.get("profit") or fin_obj.get("latest_profit"),
                "revenue_trend": fin_obj.get("revenue_trend", ""),
            }
        }
        data["FINANCE"] = {"find_company_financials": json.dumps(normalized, ensure_ascii=False)}
    else:
        data["FINANCE"] = {"find_company_financials": fin_raw or "{}"}

    # COMPETITORS — отдаём как есть, структура совпадает
    data["COMPETITORS"] = {
        "find_competitors": collected_results.get("find_competitors", "{}"),
    }

    return data
