"""Форматтер таблицы конкурентов из точных данных pipeline.

Преобразует JSON find_competitors в готовую Markdown таблицу.
LLM не участвует — данные из ФНС/SearXNG, ноль галлюцинаций.
"""

import json
import logging
import re

logger = logging.getLogger(__name__)

_TREND_EMOJI = {
    "growing": "📈",
    "declining": "📉",
    "stable": "➡️",
}


def _format_revenue(rev: int | float | None) -> str:
    """Форматирование выручки в читаемый вид."""
    if not rev or rev <= 0:
        return "нет данных"
    if rev >= 1_000_000_000:
        return f"{rev / 1_000_000_000:.1f} млрд ₽"
    if rev >= 1_000_000:
        return f"{rev / 1_000_000:.0f} млн ₽"
    return f"{rev:,.0f} ₽"


def _format_followers(followers: int | None) -> str:
    """Форматирование подписчиков Instagram."""
    if not followers or followers <= 0:
        return "—"
    if followers >= 1_000_000:
        return f"{followers / 1_000_000:.1f}M"
    if followers >= 1_000:
        return f"{followers // 1_000}K"
    return str(followers)


def _format_profit(profit: int | float | None) -> str:
    """Форматирование прибыли."""
    if not profit or profit <= 0:
        return "—"
    return _format_revenue(profit)


def _format_age(reg_date: str | None) -> str:
    """Возраст клиники из registration_date."""
    if not reg_date:
        return "—"
    try:
        from datetime import datetime
        # ФНС: "2018-06-15" или ISO
        dt = datetime.fromisoformat(reg_date[:10])
        years = (datetime.now() - dt).days // 365
        if years > 0:
            return f"{years} лет"
    except (ValueError, TypeError):
        pass
    return "—"


def format_competitors(result: str, client_revenue: int | None = None,
                       client_profit: int | None = None,
                       client_reg_date: str | None = None,
                       client_scl: int | None = None) -> str:
    """Формирует Markdown таблицу конкурентов из JSON pipeline.

    Args:
        result: JSON строка от find_competitors (или dict).
        client_revenue: Выручка клиента для строки «Вы».
        client_profit: Прибыль клиента.
        client_reg_date: Дата регистрации клиента (для возраста).
        client_scl: СЧЛ клиента.

    Returns:
        Markdown строка с таблицей. Пустая строка если нет данных.
    """
    try:
        data = json.loads(result) if isinstance(result, str) else result
    except (json.JSONDecodeError, TypeError):
        logger.warning("format_competitors: invalid JSON input")
        return ""

    comps = data.get("competitors", []) if isinstance(data, dict) else []

    if not comps:
        return "📊 Конкуренты: данные не найдены."

    # Фильтр Perplexity-болтовни: иногда LLM отдаёт вступительную фразу как
    # имя конкурента («Вот несколько известных клиник косметологии в СПб:»).
    # ВАЖНО: одинаковые короткие имена с РАЗНЫМИ ИНН — это разные юрлица,
    # их НЕ сливаем (отчёт различает по ИНН-суффиксу).
    def _is_chatter(n: str) -> bool:
        if not n:
            return True
        s = n.strip()
        low = s.lower()
        if any(p in low for p in (
            "вот несколько", "известных клиник", "некоторых клиник", "список",
            "санкт-петербурге", "рекоменду", "обратите", "например",
        )):
            return True
        if s.endswith(":") or s.endswith(".") and len(s) > 40:
            return True
        if "?" in s or len(s) > 55:
            return True
        return False

    comps = [c for c in comps if not _is_chatter(c.get("brand_name") or c.get("legal_name"))]

    # Нумерация секций делается в builder.py через _PHASE_ORDER.
    # :::section-num убран — иначе печатался как текст (Fix Баг 4).
    lines = [""]

    lines.append("| Конкурент | Выручка | Прибыль | Тренд | Лет | Врачей | IG | Сайт |")
    lines.append("|---|---|---|---|---|---|---|---|")

    # Строка клиента (позиционирование в таблице)
    if client_revenue:
        client_profit_str = _format_profit(client_profit) if client_profit else "—"
        client_age = _format_age(client_reg_date)
        client_scl_str = str(client_scl) if client_scl else "—"
        lines.append(
            f"| **ВЫ** | **{_format_revenue(client_revenue)}** "
            f"| {client_profit_str} | — | {client_age} | {client_scl_str} | — | — |"
        )

    for c in comps:
        brand = (c.get("brand_name") or c.get("legal_name") or "?").strip()
        if len(brand) > 22:
            brand = brand[:19] + "…"

        rev = c.get("revenue_year")
        rev_str = _format_revenue(rev)

        profit_str = _format_profit(c.get("profit_year"))

        trend_raw = c.get("revenue_trend") or ""
        trend = _TREND_EMOJI.get(trend_raw, "—")

        age_str = _format_age(c.get("registration_date"))

        docs = c.get("surgeons_count") or c.get("employee_count")
        docs_str = str(docs) if docs else "—"

        ig = c.get("instagram_followers")
        ig_str = _format_followers(ig)

        cms = c.get("website_cms") or "—"
        if len(cms) > 12:
            cms = cms[:10] + "…"

        lines.append(f"| {brand} | {rev_str} | {profit_str} | {trend} | {age_str} | {docs_str} | {ig_str} | {cms} |")

    # ── Главный вывод в blockquote-плашке ──
    lines.append("")
    comp_revs = [(c.get("brand_name") or c.get("legal_name", "?")[:15],
                  c.get("revenue_year") or 0) for c in comps]
    if comp_revs and client_revenue:
        closest = min(comp_revs, key=lambda x: abs(x[1] - client_revenue))
        ratio = closest[1] / client_revenue if client_revenue else 0
        if 0.5 < ratio < 2:
            conclusion = f"Ближайший конкурент — {closest[0]}, выручка {ratio:.1f}× от вашей."
        elif closest[1] > client_revenue:
            conclusion = f"Все конкуренты крупнее. Ближайший — {closest[0]} ({_format_revenue(closest[1])})."
        else:
            conclusion = "Вы лидер по выручке среди найденных конкурентов."
        # :::surface-block не обрабатывается в markdown_engine → используем > blockquote
        lines.append(f"> **Главный вывод:** {conclusion}")

    lines.append("")
    lines.append("---")

    return "\n".join(lines)
