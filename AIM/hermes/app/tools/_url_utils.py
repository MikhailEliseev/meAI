"""_url_utils — URL extraction & recovery helpers для tool handlers.

Решает проблему: GLM-5.2 (и подобные LLM) иногда не передаёт URL
в JSON arguments tool_call, только в пользовательском сообщении.

Использование в tool handler:

    from app.tools._url_utils import recover_url_from_context

    if not url:
        session_id_local = kwargs.get("session_id", "") or os.getenv("PIPELINE_SESSION_ID", "")
        recovered = recover_url_from_context(session_id_local, kwargs)
        if recovered:
            url = recovered
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            logger.info("<tool_name>: URL recovered via fallback: %s", url)

5-уровневый fallback:
  1. kwargs.get('url'/'client_url'/'user_url')
  2. kwargs.get('context') dict
  3. kwargs.get('_user_message'/'user_message'/'message')
  4. История сессии через SessionDB
  5. PIPELINE_CLIENT_URL env var (set by agent_wrapper)
"""

import logging
import os
import re

logger = logging.getLogger(__name__)


# ── URL extraction fallback для моделей типа glm-5.2 ────────────────────
# GLM-5.2 иногда не передаёт URL в arguments tool_call, только в сообщении.
# Эти regex и функция recover_url_from_context решают эту проблему.

_TLD_LIST = (
    "ru|com|net|org|рф|su|io|pro|dev|digital|agency|"
    "club|online|site|tech|med|health|clinic|center|care|"
    "msk|spb|rf|info|biz"
)
_FULL_URL_RE = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')
_BARE_DOMAIN_RE = re.compile(
    r'(?:^|\s)([a-zA-Z0-9](?:[a-zA-Z0-9\-]*[a-zA-Z0-9])?\.'
    r'(?:' + _TLD_LIST + r'))'
    r'(?:\s|$|[,.!?;:")]|$|/)'
)


def extract_url_anywhere(text: str) -> str | None:
    """Извлечь первый URL или bare domain из произвольного текста.

    Возвращает URL как есть ('https://clinic.ru/path') или bare domain
    ('clinic.ru'). Возвращает None, если ничего не найдено.
    """
    if not text:
        return None
    m = _FULL_URL_RE.search(text)
    if m:
        return m.group(0)
    m = _BARE_DOMAIN_RE.search(text)
    if m:
        return m.group(1)
    return None


def recover_url_from_context(session_id: str, kwargs: dict) -> str:
    """Fallback: восстановить URL из kwargs или истории сессии.

    Пробует по порядку 5 уровней (см. модуль docstring).
    Возвращает найденный URL (строка) или пустую строку "" если не найден.
    """
    # 1. Прямые kwargs
    for key in ("url", "client_url", "user_url"):
        val = kwargs.get(key)
        if val and isinstance(val, str) and val.strip():
            extracted = extract_url_anywhere(val)
            if extracted:
                return extracted

    # 2. context dict
    context = kwargs.get("context") or {}
    if isinstance(context, dict):
        for key in ("url", "client_url", "user_url", "message"):
            val = context.get(key)
            if val and isinstance(val, str):
                extracted = extract_url_anywhere(val)
                if extracted:
                    return extracted

    # 3. user_message в kwargs
    user_msg = (
        kwargs.get("_user_message")
        or kwargs.get("user_message")
        or kwargs.get("message")
    )
    if user_msg and isinstance(user_msg, str):
        extracted = extract_url_anywhere(user_msg)
        if extracted:
            logger.info("_url_utils: URL from kwargs.message: %s", extracted)
            return extracted

    # 4. История сессии через SessionDB
    if session_id:
        try:
            from hermes_state import SessionDB  # type: ignore[import-not-found]

            sdb = SessionDB()
            msgs = sdb.load_messages(session_id, role="user", limit=5) or []
            for msg in reversed(msgs):
                content = msg.get("content") if isinstance(msg, dict) else None
                if content and isinstance(content, str):
                    extracted = extract_url_anywhere(content)
                    if extracted:
                        logger.info(
                            "_url_utils: URL from session history: %s",
                            extracted,
                        )
                        return extracted
        except Exception as hist_err:
            logger.warning("_url_utils: session history lookup failed: %s", hist_err)

    # 5. PIPELINE_CLIENT_URL env var
    env_url = os.getenv("PIPELINE_CLIENT_URL", "")
    if env_url:
        extracted = extract_url_anywhere(env_url)
        if extracted:
            logger.info("_url_utils: URL from env PIPELINE_CLIENT_URL: %s", extracted)
            return extracted

    return ""
