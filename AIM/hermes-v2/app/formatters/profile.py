"""Форматтер профиля клиники — стиль эталонного отчёта.

Карточки-цифры, эмодзи-префиксы, пронумерованные секции.
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
    """Формирует Markdown блок профиля — стиль эталонного отчёта.

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
        for key in ("revenue", "profit", "revenue_trend", "registration_date", "employee_count", "okved"):
            if client_data.get(key) and not data.get(key):
                data[key] = client_data[key]

    lines = []

    name = data.get("company_name") or data.get("brand_name") or ""
    legal = data.get("legal_name") or ""
    inn = data.get("inn") or ""
    city = data.get("city") or ""
    specialization = data.get("specialization") or ""
    address = data.get("address") or ""
    services = data.get("services") or []
    website_platform = data.get("website_platform") or ""

    # ── 01 — Заголовок ──
    lines.append(":::section-num")
    lines.append("01 — О КЛИНИКЕ")
    lines.append(":::")
    lines.append("")

    if name:
        lines.append(f"### {name}")
    else:
        lines.append("### Профиль клиники")

    # ── Surface Block: ключевая информация ──
    quick = []
    if city and address:
        quick.append(f"📍 {city}, {address}")
    elif city:
        quick.append(f"📍 {city}")

    doctors_count = data.get("doctors_count")
    if doctors_count:
        quick.append(f"🔬 {doctors_count} врачей")

    age = _format_age(data.get("registration_date"))
    if age:
        quick.append(f"📅 С {data.get('registration_date', '')[:4]} · {age} на рынке")

    if quick:
        lines.append("")
        lines.append(":::surface-block")
        lines.append("  \n".join(quick))
        lines.append(":::")

    # ── Stat Cards: выручка, прибыль ──
    rev = data.get("revenue") or data.get("revenue_year")
    profit = data.get("profit") or data.get("profit_year")
    trend = data.get("revenue_trend") or data.get("trend")
    trend_emoji = {"growing": "📈", "stable": "➡️", "declining": "📉"}.get(trend, "")

    if rev or profit:
        lines.append("")
        if rev:
            lines.append(":::stat-card")
            lines.append(f"**{_format_money(rev)}**")
            lines.append("выручка")
            lines.append(":::")
        if profit:
            trend_part = f" {trend_emoji}" if trend_emoji else ""
            lines.append(":::stat-card")
            lines.append(f"**{_format_money(profit)}**")
            lines.append(f"прибыль{trend_part}")
            lines.append(":::")
        lines.append("")

    # ── Реквизиты (компактно) ──
    details = []
    if legal and legal != name:
        details.append(legal)
    if inn:
        details.append(f"ИНН: {inn}")
    okved_h = _okved_human(data.get("okved") or data.get("okved_main"))
    if okved_h:
        details.append(okved_h)
    if specialization:
        details.append(specialization)
    if website_platform:
        details.append(f"сайт на {website_platform}")

    if details:
        lines.append(" · ".join(details))
        lines.append("")

    # ── Соцсети (компактная строка) ──
    socials_found = data.get("socials_found")
    if socials_found and isinstance(socials_found, dict):
        social_parts = []
        emoji_map = {"instagram": "📸", "vk": "🔵", "telegram": "✈️", "youtube": "▶️"}
        for platform, url in socials_found.items():
            emoji = emoji_map.get(platform, "🔗")
            label = platform.upper() if platform in ("vk",) else platform.capitalize()
            social_parts.append(f"{emoji} [{label}]({url})")
        if social_parts:
            lines.append("**Соцсети:** " + " | ".join(social_parts))
            lines.append("")

    # ── Услуги ──
    if services:
        lines.append(f"**Услуги:** {', '.join(services[:8])}")
        lines.append("")

    # ── Врачи (из website_scraper — Phase 13) ──
    doctors = data.get("doctors")
    if doctors and isinstance(doctors, list) and len(doctors) > 0:
        lines.append("")
        lines.append("**Врачи на сайте:**")
        for doc in doctors[:8]:
            if isinstance(doc, dict):
                doc_name = doc.get("name", "")
                doc_spec = doc.get("specialization", "")
                if doc_name:
                    if doc_spec:
                        lines.append(f"- {doc_name} — {doc_spec[:60]}")
                    else:
                        lines.append(f"- {doc_name}")
            elif isinstance(doc, str) and len(doc) > 3:
                lines.append(f"- {doc}")
        lines.append("")

    # ── Соцсети (из website_scraper — Phase 13) ──
    socials = data.get("socials")
    if socials and isinstance(socials, dict) and socials:
        social_parts = []
        emoji_map = {"instagram": "📸", "vk": "🔵", "telegram": "✈️",
                     "youtube": "▶️", "rutube": "🎬", "whatsapp": "💬",
                     "dzen": "📰", "tenchat": "💼"}
        for platform, handle in socials.items():
            emoji = emoji_map.get(platform, "🔗")
            label = platform.upper() if platform in ("vk",) else platform.capitalize()
            # Формируем полную ссылку
            if platform == "instagram":
                url = f"https://instagram.com/{handle}"
            elif platform == "vk":
                url = f"https://vk.com/{handle}"
            elif platform == "telegram":
                url = f"https://t.me/{handle}"
            elif platform == "youtube":
                url = f"https://youtube.com/@{handle}"
            else:
                url = handle if handle.startswith("http") else f"https://{platform}.com/{handle}"
            social_parts.append(f"{emoji} [{label}]({url})")
        if social_parts:
            lines.append("**Соцсети (найдены на сайте):** " + " | ".join(social_parts))
            lines.append("")

    lines.append("---")

    return "\n".join(lines), data
