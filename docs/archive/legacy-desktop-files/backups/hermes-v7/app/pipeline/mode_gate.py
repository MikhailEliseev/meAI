"""Hermes v7 — Mode Gate.

Фильтрация инструментов в зависимости от режима.
ONBOARDING: только aim-operations, без hermes-debug и без админских инструментов.
ADMIN/ACTIVE/SALES_ADMIN: полный доступ (aim-operations + hermes-debug).
"""

import logging

logger = logging.getLogger(__name__)

# Инструменты, которые ВСЕГДА заблокированы в ONBOARDING режиме
_ONBOARDING_BLOCKED_TOOLS = frozenset({
    "orchestrate",           # Управление пайплайном (админский)
    "search_chats",          # Поиск по чатам
    "send_message_as_user",  # Отправка как пользователь
    "show_all_leads",        # Все лиды
    "get_lead_pipeline",     # Воронка лидов
    "file_write",            # Запись файлов (защищается file_guard)
    "shell_exec",            # Shell-команды
    "restart_myself",        # Перезапуск Hermes
})


def get_toolsets_for_mode(mode: str) -> list[str]:
    """Возвращает список toolset'ов для заданного режима.

    ONBOARDING: только aim-operations (LLM не видит hermes-debug).
    Все остальные: aim-operations + hermes-debug (полный доступ).

    Args:
        mode: Режим работы ("ONBOARDING", "ADMIN", "ACTIVE", "SALES_ADMIN", "PRESALE").

    Returns:
        Список имён toolset'ов.
    """
    mode_upper = mode.upper()

    if mode_upper in ("ONBOARDING", "PRESALE"):
        return ["aim-operations"]

    # ADMIN, ACTIVE, SALES_ADMIN — полный доступ
    return ["aim-operations", "hermes-debug"]


def is_tool_allowed(tool_name: str, mode: str) -> bool:
    """Проверяет, разрешён ли конкретный инструмент в заданном режиме.

    Используется для дополнительной фильтрации на уровне вызова инструмента
    (помимо фильтрации toolset'ов в AIAgent).

    Args:
        tool_name: Имя инструмента (например "file_write", "orchestrate").
        mode: Режим работы.

    Returns:
        True если инструмент разрешён, False если заблокирован.
    """
    mode_upper = mode.upper()

    if mode_upper not in ("ONBOARDING", "PRESALE"):
        return True

    return tool_name not in _ONBOARDING_BLOCKED_TOOLS
