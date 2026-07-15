"""Форматтер профиля клиники из точных данных extract_clinic_profile.

Только факты: ИНН, юрлицо, город, специализация. Никакой аналитики.
"""

import json
import logging

logger = logging.getLogger(__name__)


def format_profile(result: str) -> tuple[str, dict]:
    """Формирует Markdown блок профиля клиники из JSON.

    Args:
        result: JSON строка от extract_clinic_profile.

    Returns:
        Tuple of (markdown_text, parsed_dict). markdown_text — для показа,
        parsed_dict — для использования в других форматтерах.
    """
    try:
        data = json.loads(result) if isinstance(result, str) else result
    except (json.JSONDecodeError, TypeError):
        logger.warning("format_profile: invalid JSON input")
        return "", {}

    if not isinstance(data, dict):
        return "", {}

    parts = ["## 🏥 Профиль клиники\n"]

    name = data.get("company_name") or data.get("brand_name") or ""
    legal = data.get("legal_name") or ""
    inn = data.get("inn") or ""
    city = data.get("city") or ""
    specialization = data.get("specialization") or ""
    address = data.get("address") or ""
    services = data.get("services") or []
    website_platform = data.get("website_platform") or ""

    if name:
        parts.append(f"**{name}**")
    if legal and legal != name:
        parts.append(f"Юрлицо: {legal}")
    if inn:
        parts.append(f"ИНН: {inn}")
    if city:
        parts.append(f"Город: {city}")
    if specialization:
        parts.append(f"Специализация: {specialization}")
    if address:
        parts.append(f"Адрес: {address}")
    if website_platform:
        parts.append(f"Платформа сайта: {website_platform}")

    if services:
        parts.append(f"\nУслуги: {', '.join(services[:10])}")

    return "\n".join(parts), data
