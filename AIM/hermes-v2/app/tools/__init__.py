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
                    "Найти топ-5 конкурентов для сайта клиники. Возвращает выручку, "
                    "ИНН, ОКВЭД, тренд, врачей, Instagram. "
                    "ВЫЗЫВАЙ ОДИН РАЗ на старте когда клиент прислал URL сайта."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL сайта клиники"},
                        "count": {"type": "integer", "description": "Сколько конкурентов (default 5, max 10)", "default": 5},
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
    from app.tools import run_review_platforms  # noqa: F401
    # aim-app proxy tools (financials, content analysis, SEO)
    from app.tools import aim_app_tools  # noqa: F401
    # Phase 13: Website scraper (врачи, соцсети — напрямую с сайта)
    from app.tools import website_scraper  # noqa: F401
    logger.info("register_all: %d tools — %s", len(list_tool_names()), list_tool_names())
