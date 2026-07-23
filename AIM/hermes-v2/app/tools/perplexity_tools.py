"""Perplexity-тулы: quick_overview + perplexity_search + run_smi_mentions + run_review_platforms.

Перенесены из бэкапа старого hermes, адаптированы под наш registry
и общий perplexity-клиент (app.lib.perplexity).
"""
import json
import logging
import re

from app.lib.perplexity import USE_PERPLEXITY, perplexity_chat
from app.tools.registry import register

logger = logging.getLogger(__name__)


# Regex для очистки сносок Perplexity: [1], [2], [3][5], etc.
_CITATION_RE = re.compile(r'\[\d+\](?:\[\d+\])*')
# Regex для очистки [SUGGESTIONS]...[/SUGGESTIONS] из текста
_SUGGESTIONS_BLOCK_RE = re.compile(
    r'\*{0,2}\[SUGGESTIONS\]\*{0,2}\s*.*?\*{0,2}\[/SUGGESTIONS\]\*{0,2}',
    re.DOTALL,
)
# Мусорные паттерны
_JUNK_PATTERNS = [
    re.compile(r'^\s*\[\d+\]\s*$', re.MULTILINE),  # строки только со сносками
    re.compile(r'\n{3,}'),  # 3+ пустых строк подряд
]


def _clean_perplexity_text(text: str) -> str:
    """Очистить текст от сносок Perplexity и мусора.

    Убирает:
    - [1], [2], [3][5] — citation markers
    - [SUGGESTIONS]...[/SUGGESTIONS] — маркеры кнопок
    - Лишние пустые строки
    """
    if not text:
        return text

    # 1. Убрать citation markers [1], [2], [3][5]
    text = _CITATION_RE.sub('', text)

    # 2. Убрать [SUGGESTIONS] блоки целиком
    text = _SUGGESTIONS_BLOCK_RE.sub('', text)

    # 3. Убрать строки состоящие только из сносок
    for pattern in _JUNK_PATTERNS:
        text = pattern.sub('\n\n' if pattern is _JUNK_PATTERNS[1] else '', text)

    # 4. Нормализовать пустые строки
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def _normalize_url(url) -> str:
    if isinstance(url, dict):
        url = url.get("url", "")
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


# --- quick_overview --------------------------------------------------------

QUICK_OVERVIEW_PROMPT = """Ты — AI-аналитик медицинского маркетинга. Изучи клинику по URL {url}.
Собери структурированно:
- БИЗНЕС: название, юрлицо, ИНН, выручка (если есть), город, специализация
- ВРАЧИ: 3-5 ключевых врачей (имя, специализация)
- КОНКУРЕНТЫ: 3-5 ближайших конкурентов в том же городе/сегменте
- СОЦСЕТИ: Instagram, VK, Telegram, YouTube, Яндекс.Карты — ссылки если есть
- САЙТ: платформа (Tilda/Bitrix/WordPress...), качество, кол-во страниц
- ЗАЦЕПКА: один неожиданный факт для владельца клиники

Каждый факт со ссылкой на источник. Ответ на русском, структурированно."""


async def handle_quick_overview(url=None, **kwargs) -> str:
    """Быстрый обзор клиники через Perplexity (~5-10 сек)."""
    url = _normalize_url(url)
    if not url:
        return json.dumps({"error": "url is required"})
    if not USE_PERPLEXITY:
        return json.dumps({"error": "PERPLEXITY_API_KEY not configured"})
    try:
        prompt = QUICK_OVERVIEW_PROMPT.format(url=url)
        text = await perplexity_chat([
            {"role": "system", "content": "Ты — AI-аналитик медицинского маркетинга. Отвечай на русском, структурированно, с источниками."},
            {"role": "user", "content": prompt},
        ])
        logger.info("quick_overview OK: %s (%d chars)", url, len(text))
        return _clean_perplexity_text(text)
    except Exception as e:
        logger.exception("quick_overview failed: %s", url)
        return json.dumps({"error": str(e)})


register(
    name="quick_overview",
    schema={
        "type": "function",
        "function": {
            "name": "quick_overview",
            "description": (
                "Быстрый обзор клиники через Perplexity (~5-10 сек). "
                "Возвращает: название, юрлицо, ИНН, выручка, город, специализация, "
                "3-5 врачей, 3-5 конкурентов, соцсети, платформу сайта, "
                "один неожиданный факт. ВЫЗЫВАЙ ОДИН РАЗ на старте, когда клиент прислал URL."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL сайта клиники (например 'https://clinic.ru')"},
                },
                "required": ["url"],
            },
        },
    },
    handler=handle_quick_overview,
    check_fn=lambda: USE_PERPLEXITY,
)


# --- perplexity_search -----------------------------------------------------

async def handle_perplexity_search(question=None, **kwargs) -> str:
    """Гибкий Perplexity-поиск по любому вопросу."""
    if isinstance(question, dict):
        question = question.get("question", "")
    if not question:
        return json.dumps({"error": "question is required"})
    if not USE_PERPLEXITY:
        return json.dumps({"error": "PERPLEXITY_API_KEY not configured"})
    try:
        text = await perplexity_chat([
            {"role": "system", "content": "Ты — AI-ассистент. Отвечай на русском, по делу, с источниками."},
            {"role": "user", "content": question},
        ])
        logger.info("perplexity_search OK: %s (%d chars)", question[:60], len(text))
        return _clean_perplexity_text(text)
    except Exception as e:
        logger.exception("perplexity_search failed")
        return json.dumps({"error": str(e)})


register(
    name="perplexity_search",
    schema={
        "type": "function",
        "function": {
            "name": "perplexity_search",
            "description": (
                "Гибкий поиск через Perplexity по любому вопросу (рынок, ниша, тренды). "
                "Используй когда нужен свежий поиск с источниками."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "Вопрос для поиска"},
                },
                "required": ["question"],
            },
        },
    },
    handler=handle_perplexity_search,
    check_fn=lambda: USE_PERPLEXITY,
)


# --- run_smi_mentions ------------------------------------------------------

async def handle_run_smi_mentions(url=None, query=None, **kwargs) -> str:
    """Поиск упоминаний клиники в СМИ через Perplexity."""
    url = _normalize_url(url)
    if not url and not query:
        return json.dumps({"error": "url или query требуется"})
    if not USE_PERPLEXITY:
        return json.dumps({"error": "PERPLEXITY_API_KEY not configured"})
    try:
        search_query = query or f"упоминания в СМИ клиники по адресу {url}"
        text = await perplexity_chat([
            {"role": "system", "content": "Ты — аналитик медиа. Найди упоминания компании в СМИ. Отвечай на русском, со ссылками."},
            {"role": "user", "content": f"Найди упоминания в СМИ, статьях, новостях: {search_query}. Перечисли найденные упоминания с источниками и датой."},
        ])
        logger.info("run_smi_mentions OK: %s (%d chars)", search_query[:60], len(text))
        return _clean_perplexity_text(text)
    except Exception as e:
        logger.exception("run_smi_mentions failed")
        return json.dumps({"error": str(e)})


register(
    name="run_smi_mentions",
    schema={
        "type": "function",
        "function": {
            "name": "run_smi_mentions",
            "description": (
                "Поиск упоминаний клиники в СМИ, статьях, новостях. "
                "Возвращает список упоминаний с источниками. "
                "ВЫЗЫВАЙ только когда клиент попросил 'проверить упоминания в СМИ'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL сайта клиники"},
                    "query": {"type": "string", "description": "Поисковый запрос (если не URL)"},
                },
            },
        },
    },
    handler=handle_run_smi_mentions,
    check_fn=lambda: USE_PERPLEXITY,
)


# --- run_review_platforms --------------------------------------------------

async def handle_run_review_platforms(url=None, query=None, **kwargs) -> str:
    """Анализ отзывов и рейтингов клиники по платформам."""
    url = _normalize_url(url)
    if not url and not query:
        return json.dumps({"error": "url или query требуется"})
    if not USE_PERPLEXITY:
        return json.dumps({"error": "PERPLEXITY_API_KEY not configured"})
    try:
        search_query = query or f"отзывы и рейтинги клиники {url}"
        text = await perplexity_chat([
            {"role": "system", "content": "Ты — аналитик репутации. Найди отзывы и рейтинги на платформах (Яндекс.Карты, 2ГИС, Google, ПроДокторов). Отвечай на русском."},
            {"role": "user", "content": f"Найди отзывы и рейтинги: {search_query}. Укажи платформу, рейтинг, кол-во отзывов, типичные плюсы/минусы."},
        ])
        logger.info("run_review_platforms OK: %s (%d chars)", search_query[:60], len(text))
        return _clean_perplexity_text(text)
    except Exception as e:
        logger.exception("run_review_platforms failed")
        return json.dumps({"error": str(e)})


# NOTE: run_review_platforms регистрация убрана — используется Apify-версия
# из app/tools/run_review_platforms.py (точные данные через Yandex Maps + 2GIS).
# Perplexity-версия (handle_run_review_platforms выше) — dead code, оставлена
# только для обратной совместимости, но НЕ регистрируется.


# --- extract_clinic_profile (structured) -----------------------------------

EXTRACT_PROFILE_PROMPT = """Изучи клинику по URL {url}. Верни ТОЛЬКО JSON (без markdown обёртки, без ```json):
{{
  "inn": "ИНН компании или null",
  "company_name": "Название юрлица",
  "brand_name": "Бренд/торговое название клиники",
  "specialization": "основная специализация (стоматология, косметология, etc.)",
  "city": "город",
  "address": "полный физический адрес клиники (улица, дом, корпус)",
  "services": ["услуга1", "услуга2"],
  "website_platform": "Tilda/Bitrix/WordPress/SiteEdit/другое или null"
}}
Если ИНН не найден на сайте — попробуй найти по названию юрлица в открытых источниках.
НЕ выдумывай данные — ставь null если не уверен.
Верни ТОЛЬКО JSON объект, без пояснений."""


async def handle_extract_clinic_profile(url=None, **kwargs) -> str:
    """Извлекает структурированный профиль клиники через Perplexity."""
    url = _normalize_url(url)
    if not url:
        return json.dumps({"error": "url is required"}, ensure_ascii=False)
    if not USE_PERPLEXITY:
        return json.dumps({"error": "PERPLEXITY_API_KEY not configured"}, ensure_ascii=False)
    try:
        prompt = EXTRACT_PROFILE_PROMPT.format(url=url)
        raw = await perplexity_chat([
            {"role": "system", "content": "Ты — AI-аналитик. Извлекаешь данные о компаниях. Отвечай ТОЛЬКО валидным JSON, без markdown. Русский язык."},
            {"role": "user", "content": prompt},
        ])
        # Strip markdown fences if present
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
            if text.endswith("```"):
                text = text[:-3].strip()
        # Validate JSON
        data = json.loads(text)
        # Ensure required keys exist
        for key in ("inn", "company_name", "brand_name", "specialization", "city", "address", "services", "website_platform"):
            if key not in data:
                data[key] = None
        logger.info("extract_clinic_profile OK: %s — inn=%s city=%s", url, data.get("inn"), data.get("city"))
        return json.dumps(data, ensure_ascii=False)
    except json.JSONDecodeError as e:
        logger.warning("extract_clinic_profile: invalid JSON from Perplexity: %s", str(e)[:200])
        return json.dumps({"error": "invalid JSON from Perplexity", "raw": raw.strip()[:500]}, ensure_ascii=False)
    except Exception as e:
        logger.exception("extract_clinic_profile failed: %s", url)
        return json.dumps({"error": str(e)}, ensure_ascii=False)


register(
    name="extract_clinic_profile",
    schema={
        "type": "function",
        "function": {
            "name": "extract_clinic_profile",
            "description": (
                "Извлекает структурированный профиль клиники через Perplexity: ИНН, юрлицо, "
                "бренд, специализация, город, точный адрес, услуги, платформа сайта. "
                "ВЫЗЫВАЙ ПЕРВЫМ когда клиент прислал URL — результат нужен для find_competitors."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL сайта клиники"},
                },
                "required": ["url"],
            },
        },
    },
    handler=handle_extract_clinic_profile,
    check_fn=lambda: USE_PERPLEXITY,
)
