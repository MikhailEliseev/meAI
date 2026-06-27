"""Hermes v7 — File Guard.

Защита файловой системы от записи LLM в ONBOARDING режиме.
ADMIN режим имеет whitelist путей.
"""

import logging
import os
import stat
from pathlib import Path

logger = logging.getLogger(__name__)

# Пути, РАЗРЕШЁННЫЕ для записи в ADMIN режиме
_ADMIN_WRITE_WHITELIST = [
    "/opt/hermes-data/skills/",
    "/opt/hermes-data/memory/",
    "/opt/data/memories/",
    "/opt/hermes/skills/",
    "/opt/hermes/memory/",
]

# Пути, ЗАБЛОКИРОВАННЫЕ для записи в ЛЮБОМ режиме
_ALWAYS_BLOCKED = [
    "/opt/hermes-data/app/",
    "/opt/hermes/app/",
    "/opt/hermes-data/config.yaml",
    "/opt/hermes/config.yaml",
    "/opt/hermes-data/.env",
    "/opt/hermes/.env",
]


def is_write_allowed(file_path: str, mode: str) -> bool:
    """Проверяет, разрешена ли запись в указанный файл.

    ONBOARDING: запись ВСЕГДА запрещена.
    ADMIN: запись разрешена только в whitelist-пути.
    Все режимы: заблокированные пути всегда недоступны.

    Args:
        file_path: Абсолютный путь к файлу.
        mode: Режим работы.

    Returns:
        True если запись разрешена.
    """
    # Всегда блокируем критические пути
    for blocked in _ALWAYS_BLOCKED:
        if file_path == blocked or file_path.startswith(blocked):
            logger.warning("file_guard: BLOCKED critical path — %s (mode=%s)", file_path, mode)
            return False

    mode_upper = mode.upper()

    # ONBOARDING / PRESALE — запись запрещена
    if mode_upper in ("ONBOARDING", "PRESALE"):
        logger.warning("file_guard: BLOCKED write in ONBOARDING mode — %s", file_path)
        return False

    # ADMIN / ACTIVE / SALES_ADMIN — whitelist
    for allowed in _ADMIN_WRITE_WHITELIST:
        if file_path.startswith(allowed):
            return True

    logger.warning("file_guard: BLOCKED path not in whitelist — %s (mode=%s)", file_path, mode)
    return False


def protect_config() -> None:
    """Защищает config.yaml от записи (chmod 444).

    Вызывается при старте FastAPI. Предотвращает случайную перезапись
    конфигурации LLM через file_write.
    """
    config_paths = [
        "/opt/hermes-data/config.yaml",
        "/opt/hermes/config.yaml",
    ]

    for path in config_paths:
        config_file = Path(path)
        if config_file.exists():
            try:
                config_file.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)  # 0444
                logger.info("file_guard: protected %s (chmod 0444)", config_file)
            except Exception as e:
                logger.warning("file_guard: cannot chmod %s: %s", config_file, e)
        else:
            logger.debug("file_guard: %s does not exist, skipping", config_file)


def set_key_rotator(rotator_fn) -> None:
    """Устанавливает функцию ротации ключей.

    Вызывается из main.py при старте. PipelineEngine использует эту функцию
    при обнаружении key exhaustion.

    Args:
        rotator_fn: Callable[[], bool] — возвращает True если ключи обновлены.
    """
    global _key_rotator
    _key_rotator = rotator_fn
    logger.info("file_guard: key rotator registered")


# ── Текущий режим (устанавливается agent_wrapper перед запуском) ──
_current_mode: str = "ONBOARDING"


def set_current_mode(mode: str) -> None:
    """Установить текущий режим для file_guard проверок."""
    global _current_mode
    _current_mode = mode


def get_current_mode() -> str:
    """Получить текущий режим."""
    return _current_mode


# ── Shell command validation ──────────────────────────────────────

# Паттерны, которые НЕЛЬЗЯ использовать в shell_exec
_FORBIDDEN_SHELL_PATTERNS = [
    # Запись в защищённые пути (> file, tee, dd, etc.)
    (r"(?:>|>>)\s*/opt/hermes(?:-data)?/app/", "write to /opt/hermes/app/"),
    (r"(?:>|>>)\s*/opt/hermes(?:-data)?/config\.yaml", "write to config.yaml"),
    (r"(?:>|>>)\s*/opt/hermes(?:-data)?/\.env", "write to .env"),
    # sed -i (inline edit) на защищённые пути
    (r"sed\s+.*-i.*/opt/hermes(?:-data)?/app/", "sed -i on /opt/hermes/app/"),
    (r"sed\s+.*-i.*/opt/hermes(?:-data)?/config\.yaml", "sed -i on config.yaml"),
    (r"sed\s+.*-i.*/opt/hermes(?:-data)?/\.env", "sed -i on .env"),
    # Python/Perl/Ruby запись в защищённые пути
    (r"(?:open|write)\s*\(['\"]/opt/hermes(?:-data)?/app/", "file write via script"),
    (r"(?:open|write)\s*\(['\"]/opt/hermes(?:-data)?/config\.yaml", "config write via script"),
    # chmod/chown на защищённые пути (снятие защиты)
    (r"chmod\s+.*/opt/hermes(?:-data)?/config\.yaml", "chmod on config.yaml"),
    (r"chmod\s+.*/opt/hermes(?:-data)?/app/", "chmod on /opt/hermes/app/"),
    # tee в защищённые пути
    (r"tee\s+/opt/hermes(?:-data)?/app/", "tee to /opt/hermes/app/"),
    # mv/cp в защищённые пути
    (r"(?:mv|cp)\s+.*/opt/hermes(?:-data)?/app/.*\.py", "mv/cp to /opt/hermes/app/"),
]


def validate_shell_command(command: str) -> tuple[bool, str]:
    """Проверяет shell-команду на попытки записи в защищённые пути.

    Вызывается из shell_exec перед выполнением команды.

    Args:
        command: Полный текст команды.

    Returns:
        (разрешена, причина_блокировки)
    """
    for pattern, description in _FORBIDDEN_SHELL_PATTERNS:
        import re as _re
        if _re.search(pattern, command):
            logger.warning(
                "file_guard: BLOCKED shell command — %s (pattern: %s)",
                description, pattern,
            )
            return False, description

    return True, ""


_key_rotator = None


def get_key_rotator():
    """Возвращает зарегистрированную функцию ротации ключей."""
    return _key_rotator
