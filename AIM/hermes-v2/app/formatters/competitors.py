"""Форматтер таблицы конкурентов из точных данных pipeline.

Преобразует JSON find_competitors в готовую Markdown таблицу.
LLM не участвует — данные из ФНС/SearXNG, ноль галлюцинаций.
"""

import json
import logging

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


def _format_posts(posts: int | None) -> str:
    """Форматирование количества постов Instagram."""
    if not posts or posts <= 0:
        return "—"
    if posts >= 1000:
        return f"{posts // 1000}K"
    return str(posts)


def format_competitors(result: str, client_revenue: int | None = None) -> str:
    """Формирует Markdown таблицу конкурентов из JSON pipeline.

    Args:
        result: JSON строка от find_competitors (или dict).
        client_revenue: Выручка клиента для строки «Вы» (если есть).

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

    lines = ["## 📊 Конкуренты (данные ФНС)\n"]

    # Строка клиента (если есть выручка)
    if client_revenue:
        rev_str = _format_revenue(client_revenue)
        lines.append(f"**Ваша клиника:** выручка {rev_str}\n")

    lines.append("| Конкурент | Выручка | Прибыль | Тренд | Лет | Врачей | IG подп. | IG посты | Сайт | Стр. |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")

    for c in comps:
        brand = (c.get("brand_name") or c.get("legal_name") or "?").strip()
        # Укорачиваем длинные названия
        if len(brand) > 25:
            brand = brand[:22] + "…"

        rev = c.get("revenue_year")
        rev_str = _format_revenue(rev)

        profit_str = _format_profit(c.get("profit_year"))

        trend_raw = c.get("revenue_trend") or ""
        trend = _TREND_EMOJI.get(trend_raw, "—")

        age_str = _format_age(c.get("registration_date"))

        docs = c.get("surgeons_count")
        docs_str = str(docs) if docs else "—"

        ig = c.get("instagram_followers")
        ig_str = _format_followers(ig)

        ig_posts = c.get("instagram_posts")
        ig_posts_str = _format_posts(ig_posts)

        cms = c.get("website_cms") or "—"
        if len(cms) > 12:
            cms = cms[:10] + "…"

        pages = c.get("website_pages")
        pages_str = str(pages) if pages else "—"

        lines.append(f"| {brand} | {rev_str} | {profit_str} | {trend} | {age_str} | {docs_str} | {ig_str} | {ig_posts_str} | {cms} | {pages_str} |")

    return "\n".join(lines)
