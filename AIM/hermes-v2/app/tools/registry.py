"""Минимальный registry тулов для tool-calling (без hermes-agent).

Хранит tool-definitions в формате OpenAI function-calling и связывает их
с handler'ами. Заменяет чужой tools.registry из hermes-agent==0.14.0.
"""
import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)

# name → {schema, handler, is_async, check_fn}
_TOOLS: dict[str, dict] = {}


def register(
    name: str,
    schema: dict,
    handler: Callable,
    is_async: bool = True,
    check_fn: Callable[[], bool] | None = None,
) -> None:
    """Регистрирует тул. schema — OpenAI function-calling формат."""
    if name in _TOOLS:
        logger.warning("tool %s already registered, overwriting", name)
    _TOOLS[name] = {
        "schema": schema,
        "handler": handler,
        "is_async": is_async,
        "check_fn": check_fn or (lambda: True),
    }
    logger.info("registered tool: %s", name)


def get_openai_tools() -> list[dict]:
    """Возвращает список schemas для параметра tools= в OpenAI API.

    Только тулы, чей check_fn() → True (доступные сейчас).
    Нормализует к полному формату {"type":"function","function":{...}}.
    """
    tools = []
    for name, t in _TOOLS.items():
        try:
            if not t["check_fn"]():
                continue
        except Exception:
            continue
        schema = t["schema"]
        # нормализация: если schema уже полная (есть "function") — берём как есть
        if "function" in schema:
            tools.append(schema)
        else:
            # старый формат без обёртки — оборачиваем
            tools.append({"type": "function", "function": schema})
    return tools


async def execute(name: str, arguments: dict[str, Any]) -> Any:
    """Выполняет handler тулза с аргументами. Возвращает результат."""
    if name not in _TOOLS:
        return {"error": f"unknown tool: {name}"}
    t = _TOOLS[name]
    try:
        if t["is_async"]:
            return await t["handler"](**arguments)
        return t["handler"](**arguments)
    except Exception as e:
        logger.exception("tool %s failed", name)
        return {"error": f"tool {name} failed: {e}"}


def list_tool_names() -> list[str]:
    return list(_TOOLS.keys())
