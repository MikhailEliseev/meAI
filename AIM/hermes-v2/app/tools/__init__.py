"""Регистрация всех тулов для tool-calling.

Импорт этого модуля регистрирует все тулы через registry.register().
Phase 3 Wave 1: 6 тулов (4 Perplexity + instagram + ads) + find_competitors.
"""
import logging

from app.tools.registry import register, list_tool_names
from app.tools.competitors import find_competitors

logger = logging.getLogger(__name__)


def _register_find_competitors():
    """Подключает find_competitors (из Phase 1) к tool-calling registry."""
    register(
        name="find_competitors",
        schema={
            "type": "function",
            "function": {
                "name": "find_competitors",
                "description": (
                    "Найти top-3 конкурента для сайта клиники. Возвращает имя, рейтинг, "
                    "кол-во отзывов, причину совпадения. "
                    "ВЫЗЫВАЙ ОДИН РАЗ на старте когда клиент прислал URL сайта. "
                    "⚠️ Занимает ~60-120 секунд (Google Maps через Apify)."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL сайта клиники"},
                        "count": {"type": "integer", "description": "Сколько конкурентов (по умолчанию 3)", "default": 3},
                    },
                    "required": ["url"],
                },
            },
        },
        handler=find_competitors,
    )


def register_all():
    """Регистрирует все тулы. Вызывается при startup."""
    _register_find_competitors()
    # Perplexity-тулы регистрируются при импорте модуля (на module level)
    from app.tools import perplexity_tools  # noqa: F401
    from app.tools import run_instagram_content  # noqa: F401
    from app.tools import run_ads_intelligence  # noqa: F401
    logger.info("register_all: %d tools — %s", len(list_tool_names()), list_tool_names())
