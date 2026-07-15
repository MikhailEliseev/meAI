"""Форматтер профиля клиники — нарративный стиль.

Не просто ИНН/город, а история бизнеса: возраст, масштаб, позиции.
Данные из ФНС (точные), не Perplexity-оценки.
"""

import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def _format_age(reg_date: str | None) -> str | None:
    """Возраст из registration_date → '88 лет' / '3 года'."""
    if not reg_date:
        return None
    try:
        dt = datetime.fromisoformat(str(reg_date)[:10])
        years = (datetime.now() - dt).days // 365
        if years >= 11:
            return f"{years} лет"
        elif years >= 2:
            return f"{years} года"
        elif years >= 1:
            return f"{years} год"
        else:
            return "новая клиника"
    except (ValueError, TypeError):
        return None


def _format_money(amount: int | float | None) -> str:
    """Форматирование денег: 4_300_000_000 → '4.3 млрд ₽'."""
    if not amount or amount <= 0:
        return ""
    if amount >= 1_000_000_000:
        return f"{amount / 1_000_000_000:.1f} млрд ₽"
    if amount >= 1_000_000:
        return f"{amount / 1_000_000:.0f} млн ₽"
    return f"{amount:,.0f} ₽"


def _okved_human(okved: str | None) -> str | None:
    """ОКВЭД на человеческом языке."""
    if not okved:
        return None
    okved_str = str(okved).strip()
    if okved_str.startswith("86.10"):
        return "больничная организация (полный цикл)"
    if okved_str.startswith("86.21"):
        return "амбулаторная медицинская помощь"
    if okved_str.startswith("86.22"):
        return "специализированная медицинская помощь"
    if okved_str.startswith("86.23"):
        return "стоматологическая практика"
    if okved_str.startswith("86"):
        return "здравоохранение"
    return okved_str


def format_profile(result: str, client_data: dict | None = None) -> tuple[str, dict]:
    """Формирует Markdown блок профиля клиники — нарративный стиль.

    Args:
        result: JSON строка от extract_clinic_profile.
        client_data: Доп. данные от pipeline (revenue, profit, reg_date, scl).

    Returns:
        Tuple of (markdown_text, parsed_dict).
    """
    try:
        data = json.loads(result) if isinstance(result, str) else result
    except (json.JSONDecodeError, TypeError):
        logger.warning("format_profile: invalid JSON input")
        return "", {}

    if not isinstance(data, dict):
        return "", {}

    # Merge client_data (from pipeline) если есть — они точнее
    if client_data:
        for key in ("revenue", "profit", "registration_date", "employee_count", "okved"):
            if client_data.get(key) and not data.get(key):
                data[key] = client_data[key]

    parts = []

    name = data.get("company_name") or data.get("brand_name") or ""
    legal = data.get("legal_name") or ""
    inn = data.get("inn") or ""
    city = data.get("city") or ""
    specialization = data.get("specialization") or ""
    address = data.get("address") or ""
    services = data.get("services") or []
    website_platform = data.get("website_platform") or ""

    # ── Заголовок-нарратив ──
    if name:
        parts.append(f"## 🏥 {name}\n")
    else:
        parts.append("## 🏥 Профиль клиники\n")

    # ── Строка масштаба (как в старом отчёте) ──
    scale_parts = []
    age = _format_age(data.get("registration_date"))
    if age:
        scale_parts.append(f"**{age} на рынке**")
    rev = data.get("revenue") or data.get("revenue_year")
    if rev:
        scale_parts.append(f"выручка {_format_money(rev)}")
    emp = data.get("employee_count")
    if emp:
        scale_parts.append(f"{emp} сотрудников")
    okved_h = _okved_human(data.get("okved") or data.get("okved_main"))
    if okved_h:
        scale_parts.append(okved_h)

    if scale_parts:
        parts.append(" | ".join(scale_parts) + "\n")

    # ── Детали ──
    if legal and legal != name:
        parts.append(f"**Юрлицо:** {legal}")
    if inn:
        parts.append(f"**ИНН:** {inn}")
    if city:
        parts.append(f"**Город:** {city}")
    if specialization:
        parts.append(f"**Специализация:** {specialization}")
    if address:
        parts.append(f"**Адрес:** {address}")
    if website_platform:
        parts.append(f"**Сайт:** {website_platform}")

    # ── Врачи (из Firecrawl скрапа, если есть) ──
    doctors_count = data.get("doctors_count")
    if doctors_count:
        parts.append(f"**Врачей:** {doctors_count}")

    # ── Соцсети (из Firecrawl скрапа, если есть) ──
    socials_found = data.get("socials_found")
    if socials_found and isinstance(socials_found, dict):
        social_parts = []
        for platform, url in socials_found.items():
            emoji = {"instagram": "📸", "vk": "🔵", "telegram": "✈️", "youtube": "▶️"}.get(platform, "🔗")
            social_parts.append(f"{emoji} [{platform}]({url})")
        if social_parts:
            parts.append(f"**Соцсети:** {' | '.join(social_parts)}")

    # ── Финансовая динамика ──
    profit = data.get("profit") or data.get("profit_year")
    trend = data.get("revenue_trend") or data.get("trend")
    trend_emoji = {"growing": "📈", "stable": "➡️", "declining": "📉"}.get(trend, "")

    fin_lines = []
    if profit:
        fin_lines.append(f"чистая прибыль {_format_money(profit)}")
    if trend and trend_emoji:
        fin_lines.append(f"тренд {trend_emoji}")

    if fin_lines:
        parts.append(f"\n**Финансы:** {', '.join(fin_lines)}")

    # ── Услуги ──
    if services:
        parts.append(f"\n**Услуги:** {', '.join(services[:8])}")

    return "\n".join(parts), data
