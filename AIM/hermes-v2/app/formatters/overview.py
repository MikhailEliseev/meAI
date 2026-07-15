"""Форматтер обзора клиники из Perplexity quick_overview.

Perplexity отдаёт свободный текст с аналитикой, оценочными цифрами
и «неожиданными фактами» — всё это источник галлюцинаций.

Форматтер извлекает ТОЛЬКО проверяемые факты:
- Врачи (имя, специализация)
- Соцсети (ссылки Instagram, VK, Telegram, YouTube)
- Платформа сайта (Tilda/Bitrix/WordPress/…)

Удаляет:
- Оценочные цифры («~19 000 визитов», «выручка 500 млн»)
- «Неожиданный факт» / «ЗАЦЕПКА»
- Выручку и ИНН (уже в profile + competitors из точных данных ФНС)
"""

import logging
import re

logger = logging.getLogger(__name__)

# Паттерны соцсетей — ищем URL в тексте
_SOCIAL_PATTERNS = [
    ("Instagram", re.compile(r"(?:https?://)?(?:www\.)?instagram\.com/[^\s,)\]]+", re.I)),
    ("VK", re.compile(r"(?:https?://)?(?:www\.)?vk\.com/[^\s,)\]]+", re.I)),
    ("Telegram", re.compile(r"(?:https?://)?t(?:elegram)?\.me/[^\s,)\]]+", re.I)),
    ("YouTube", re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/@?[^\s,)\]]+", re.I)),
    ("Я.Карты", re.compile(r"(?:https?://)?(?:www\.)?yandex\.(?:ru|com)/maps/[^ \s,)\]]+", re.I)),
]

# Платформы сайта (детект по упоминанию)
_SITE_PLATFORMS = [
    "Tilda", "Bitrix", "1C-Bitrix", "WordPress", "SiteEdit",
    "Joomla", "OpenCart", "Drupal", "Wix", "Shopify", "МойСайт",
]

# Секции Perplexity, которые могут содержать врачей
_DOCTOR_SECTION_HEADERS = [
    "ВРАЧИ", "Врачи", "КЛЮЧЕВЫЕ ВРАЧИ", "Команда", "КОМАНДА",
    "СПЕЦИАЛИСТЫ", "Специалисты",
]

# Что вырезаем полностью (источники галлюцинаций)
_STRIP_PATTERNS = [
    # «Неожиданный факт» / «ЗАЦЕПКА» секция
    re.compile(r"(?:ЗАЦЕПКА|Неожиданный факт|Интересный факт)[:\s].*?(?=\n##|\n\*\*|\Z)", re.DOTALL | re.I),
    # Оценочные числа: «~19 000», «≈ 500», «около 200»
    re.compile(r"[~≈]\s*[\d\s]+(?:визит|посет|пользов|человек|клиент)", re.I),
    # «выручка: 500 млн» — есть точные данные в competitors таблице
    re.compile(r"выручк[аи][^.\n]*?\d+\s*(?:млн|млрд|тыс)[^.\n]*", re.I),
]


def _extract_socials(text: str) -> list[tuple[str, str]]:
    """Извлекает ссылки на соцсети из текста. Возвращает [(platform, url), ...]."""
    found = []
    seen = set()
    for platform, pattern in _SOCIAL_PATTERNS:
        match = pattern.search(text)
        if match:
            url = match.group(0).rstrip(".,;)")
            # Нормализуем — добавляем https:// если нет
            if not url.startswith("http"):
                url = "https://" + url
            if url not in seen:
                seen.add(url)
                found.append((platform, url))
    return found


def _extract_platform(text: str) -> str | None:
    """Детектит платформу сайта по упоминанию в тексте."""
    text_lower = text.lower()
    for platform in _SITE_PLATFORMS:
        if platform.lower() in text_lower:
            return platform
    return None


def _extract_doctors(text: str) -> list[str]:
    """Извлекает врачей из секции 'ВРАЧИ' Perplexity-ответа.

    Perplexity обычно форматирует как:
    **ВРАЧИ:**
    - Иванов И.И. — пластический хирург
    - Петрова А.Б. — косметолог
    """
    doctors = []
    lines = text.split("\n")

    in_doctors_section = False
    for line in lines:
        stripped = line.strip()
        # Убираем markdown-обёртку (**заголовок**) и двоеточия
        header_raw = stripped.lstrip("*#").rstrip("*#:：").strip()

        # Вход в секцию врачей
        if header_raw in _DOCTOR_SECTION_HEADERS:
            in_doctors_section = True
            continue

        # Выход из секции (новый заголовок: CAPS, **жирный**, или ## )
        if in_doctors_section:
            is_header = (
                (header_raw.isupper() and len(header_raw) > 3)
                or stripped.startswith("**")
                or stripped.startswith("##")
            )
            if is_header and header_raw not in _DOCTOR_SECTION_HEADERS:
                in_doctors_section = False
                continue

            # Парсим строку врача: «- Имя — специализация» или «1. Имя: специализация»
            doc_match = re.match(
                r"^(?:[-•*]|\d+[.)])\s*(.+?)(?:\s*[—–\-:]\s*(.+))?$",
                stripped,
            )
            if doc_match:
                name = doc_match.group(1).strip()
                spec = (doc_match.group(2) or "").strip()
                # Фильтр: пропускаем мусор (слишком короткое, не имя)
                if name and len(name) > 3 and not name.startswith("http"):
                    entry = f"{name} — {spec}" if spec else name
                    doctors.append(entry)

    return doctors[:8]  # максимум 8 врачей


def format_overview(result: str) -> str:
    """Формирует Markdown блок обзора клиники из Perplexity quick_overview.

    Args:
        result: Свободный текст от quick_overview (plain text, не JSON).

    Returns:
        Markdown строка с фактами (врачи, соцсети, платформа).
        Пустая строка если нет полезных данных.
    """
    if not result or not result.strip():
        return ""

    # Если это JSON (ошибка или структурированный ответ) — не парсим
    result = result.strip()
    if result.startswith("{") and "error" in result[:50].lower():
        return ""

    # Вырезаем источники галлюцинаций
    cleaned = result
    for pattern in _STRIP_PATTERNS:
        cleaned = pattern.sub("", cleaned)

    parts = ["## 👩‍⚕️ Врачи и ресурсы\n"]

    # Врачи
    doctors = _extract_doctors(cleaned)
    if doctors:
        for doc in doctors:
            parts.append(f"- {doc}")
        parts.append("")  # пустая строка после списка

    # Соцсети
    socials = _extract_socials(result)  # из оригинального текста (URL не вырезаются)
    if socials:
        parts.append("**Соцсети:**")
        for platform, url in socials:
            parts.append(f"- {platform}: {url}")
        parts.append("")

    # Платформа сайта
    platform = _extract_platform(cleaned)
    if platform:
        parts.append(f"**Платформа сайта:** {platform}")

    # Если ничего не извлекли — не показываем пустой блок
    result_md = "\n".join(parts).strip()
    if result_md == "## 👩‍⚕️ Врачи и ресурсы":
        return ""

    return result_md + "\n"
