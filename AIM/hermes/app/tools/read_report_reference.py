"""read_report_reference — Hermes v8 tool: Read the ideal report reference.

Returns the reference HTML report (ИПХиК) so the LLM can study its structure,
content density, data interpretation style, and use it as a template.
"""

import json
import logging
import os

from tools.registry import registry

logger = logging.getLogger(__name__)

_REFERENCE_PATH = "/opt/data/report-reference.html"

# Cache the reference content (it never changes)
_reference_cache: str | None = None


def _load_reference() -> str:
    global _reference_cache
    if _reference_cache is not None:
        return _reference_cache
    try:
        with open(_REFERENCE_PATH, "r", encoding="utf-8") as f:
            _reference_cache = f.read()
        logger.info("Reference report loaded: %d chars", len(_reference_cache))
    except FileNotFoundError:
        logger.warning("Reference report not found at %s", _REFERENCE_PATH)
        _reference_cache = "REFERENCE NOT FOUND"
    except Exception as e:
        logger.error("Failed to read reference: %s", e)
        _reference_cache = f"ERROR: {e}"
    return _reference_cache


async def handle_read_report_reference(*args, **kwargs) -> str:
    """Read the reference report — the ideal example of what a scout report should be."""
    # Handle dict arg passed by tool framework
    if args and isinstance(args[0], dict):
        pass  # ignore empty dict

    content = _load_reference()

    # Extract just the body content (skip CSS/head for LLM readability)
    # Return key structural elements as JSON
    return json.dumps({
        "source": _REFERENCE_PATH,
        "size_chars": len(content),
        "format": "html",
        "instruction": (
            "Это ИДЕАЛЬНЫЙ ПРИМЕР отчёта разведки. Изучи его структуру и стиль подачи данных. "
            "Обрати внимание:\n"
            "1. Каждая секция пронумерована (01, 02...) и содержит раздел label + h2 заголовок\n"
            "2. Ключевые метрики (выручка, врачи, сотрудники) вынесены в hero и в начало секций\n"
            "3. Таблица конкурентов: клиент выделен, тренды цветом, колонки: выручка, тренд, врачи, Instagram\n"
            "4. Gap-блоки для сильных сторон (✅) и точек роста (📍)\n"
            "5. После каждой секции — ключевой вывод в blockquote\n"
            "6. Врачи: карточки с именем, специализацией, аудиторией, стилем, проблемами и потенциалом\n"
            "7. Контент-анализ: привязка страхов пациентов к конкретным форматам контента\n"
            "8. Белые поля: темы которые никто не покрывает\n"
            "9. Стратегия: приоритеты срочное/стратегическое с конкретными KPI\n"
            "10. Все цифры интерпретированы в бизнес-язык — НЕ сырые метрики, а 'что это значит для клиники'\n\n"
            "Когда будешь формировать content для post_report — сделай ТАКОЙ ЖЕ отчёт по структуре, "
            "глубине и стилю интерпретации данных."
        ),
        "full_html": content,
    }, ensure_ascii=False)


# ── Registry ──────────────────────────────────────────────────────────────
registry.register(
    name="read_report_reference",
    toolset="aim-operations",
    schema={
            "name": "read_report_reference",
            "description": "Прочитай идеальный пример отчёта разведки (ИПХиК). "
                           "Вызови этот инструмент ПЕРЕД тем как формировать content для post_report. "
                           "Изучи структуру секций, стиль интерпретации данных, формат gap-блоков, "
                           "таблиц и выводов. Твой отчёт должен быть ТАКОГО ЖЕ качества.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    handler=handle_read_report_reference,
    check_fn=lambda: os.path.exists(_REFERENCE_PATH),
    is_async=True,
    description="Read the ideal reference report — study its structure before calling post_report",
)
