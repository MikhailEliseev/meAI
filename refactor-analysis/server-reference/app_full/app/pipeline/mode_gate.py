"""Hermes v7 — Mode Gate.

Фильтрация инструментов в зависимости от режима.
ONBOARDING: только aim-operations, без hermes-debug и без админских инструментов.
ADMIN/ACTIVE/SALES_ADMIN: полный доступ (aim-operations + hermes-debug).
"""

import logging

logger = logging.getLogger(__name__)

# Инструменты, которые ВСЕГДА заблокированы в ONBOARDING/PRESALE режиме.
#
# Принцип: в PRESALE клиентский опыт ведётся через run_full_scout (13 фаз
# в Python-стейт-машине). Все индивидуальные scout/анализ/поиск инструменты
# скрыты — LLM не может их вызвать и обязан использовать run_full_scout.
# После завершения пайплайна доступны только CRM и отчётные инструменты.
_ONBOARDING_BLOCKED_TOOLS = frozenset({

    # ── Админские (были всегда) ──────────────────────────────────
    "orchestrate",           # Управление пайплайном
    "search_telegram_chats",  # Поиск по чатам
    "send_message_as_user",  # Отправка как пользователь
    "show_all_leads",        # Все лиды
    "get_lead_pipeline",     # Воронка лидов
    "file_write",            # Запись файлов (защищается file_guard)
    "shell_exec",            # Shell-команды
    "restart_myself",        # Перезапуск Hermes

    # ── Phase 0: Prelude (обходит run_full_scout) ────────────────
    "quick_overview",        # Быстрый обзор без пайплайна
    "perplexity_search",     # Поиск Perplexity (часть пайплайна)
    "perplexity_deep_analyze",# Глубокий анализ Perplexity (часть пайплайна)

    # ── Phase 1: Discovery (индивидуальные, дублируют пайплайн) ──
    "run_prescan",           # Старый прескан (заменён run_full_scout)
    "run_aim_scout",         # Старый скаут (заменён run_full_scout)
    "run_web_search",        # Веб-поиск (часть пайплайна)
    "find_company_financials",# Финансы компании (часть пайплайна)

    # ── Phase 2: Competitive Intelligence (всё внутри пайплайна) ─
    "find_competitors",      # Поиск конкурентов
    "run_ci_analysis",       # Анализ конкурентов
    "run_seo_audit",         # SEO-аудит
    "run_content_analysis",  # Контент-анализ
    "run_content_gaps",      # Контент-разрывы
    "run_ads_report",        # Отчёт по рекламе
    "run_ads_intelligence",  # Рекламная разведка
    "run_pagespeed",         # PageSpeed-аудит
    "run_review_platforms",  # Отзывы на площадках
    "run_smi_mentions",      # Упоминания в СМИ
    "crawlee_web",           # Crawlee-скрапинг
    "scrapy_crawl",          # Scrapy-скрапинг (зарегистрирован из scrapy_runner.py)
    "scrapy_runner",         # Scrapy-скрапинг (deprecated name)

    # ── Phase 3: People & Content (всё внутри пайплайна) ─────────
    "run_hh_analysis",       # Анализ вакансий HH.ru
    "run_doctor_dossiers",   # Досье на врачей
    "run_instagram_content", # Instagram-контент
    "run_geo_audit",         # Гео-аудит (зарегистрирован в geo_optimizer_tools.py)
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


# ── Registry patching (thread-safe per-agent tool filtering) ──────────

_original_get_definitions = None


def _patch_registry_for_presale() -> None:
    """Monkey-patch registry.get_definitions() to hide blocked tools.

    Thread-safe: patches the method on the singleton, restored after agent creation.
    AIAgent calls get_definitions() ONCE during init to build its tool list.
    """
    global _original_get_definitions
    from tools.registry import registry

    if _original_get_definitions is not None:
        return  # already patched

    _original_get_definitions = registry.get_definitions

    def _filtered_definitions(*args, **kwargs):
        result = _original_get_definitions(*args, **kwargs)
        # OpenAI tool format: {"type": "function", "function": {"name": "...", ...}}
        return [
            t for t in result
            if t.get("function", {}).get("name") not in _ONBOARDING_BLOCKED_TOOLS
        ]

    registry.get_definitions = _filtered_definitions
    logger.debug(
        "mode_gate: patched registry.get_definitions (blocking %d tools)",
        len(_ONBOARDING_BLOCKED_TOOLS),
    )


def _unpatch_registry() -> None:
    """Restore original registry.get_definitions()."""
    global _original_get_definitions
    if _original_get_definitions is None:
        return
    from tools.registry import registry

    registry.get_definitions = _original_get_definitions
    _original_get_definitions = None
    logger.debug("mode_gate: restored registry.get_definitions")


def apply_mode_filter(mode: str) -> None:
    """Apply per-tool filtering for the given mode (call before agent creation).

    Safe to call multiple times — patches only once, restores after unpatch.
    """
    mode_upper = mode.upper()
    if mode_upper in ("ONBOARDING", "PRESALE"):
        _patch_registry_for_presale()
    else:
        _unpatch_registry()


def remove_mode_filter() -> None:
    """Remove per-tool filtering (call after agent creation)."""
    _unpatch_registry()
