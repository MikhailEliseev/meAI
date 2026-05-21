"""AIAgent wrapper — session management + sync-to-async adapter.

Per Pitfall 2: SQLite session DB needs per-session serialization to avoid
"database is locked" errors. asyncio.Lock per session_id.

Per Pitfall 7: AIAgent.run_conversation() is SYNCHRONOUS (returns Dict[str, Any]).
Must wrap in loop.run_in_executor() for FastAPI async endpoints.

Per Pitfall 8: Each FastAPI request creates a new AIAgent instance, but
hermes-agent doesn't load previous session history into new instances.
Solution: cache AIAgent instances per session_id so conversation history
is preserved across requests.
"""

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Per-session locks to serialize concurrent requests (Pitfall 2)
_session_locks: dict[str, asyncio.Lock] = {}

# Agent cache (Pitfall 8) — preserve conversation history across web requests
# Each entry: (agent_instance, last_used_ts, conversation_history)
_agent_cache: dict[str, tuple[object, float, list[dict]]] = {}
_AGENT_CACHE_TTL = 3600  # 1 hour

OMNIROUTE_URL = os.getenv("OMNIROUTE_URL", "http://omniroute:20128/v1")
OMNIROUTE_AUTH = os.getenv("OMNIROUTE_AUTH", "sk-a10f604cd99e7a50-dd1d5a-56e30050")
DEFAULT_MODEL = os.getenv("HERMES_MODEL", "deepseek/deepseek-v4-pro")

# SOUL.md cache — loaded once, reused across requests
_soul_md_cache: Optional[str] = None


def load_soul_md() -> str:
    """Load SOUL.md from $HERMES_HOME/SOUL.md (cached).

    copy_soul.sh copies SOUL.md from skills/aim/ to $HERMES_HOME at startup.
    hermes-agent reads it via load_soul_identity=True for the web path.
    Telegram direct path needs to load it manually since it bypasses AIAgent.
    """
    global _soul_md_cache
    if _soul_md_cache is not None:
        return _soul_md_cache

    hermes_home = os.getenv("HERMES_HOME", "/opt/data")
    soul_path = Path(hermes_home) / "SOUL.md"

    if soul_path.exists():
        _soul_md_cache = soul_path.read_text()
        logger.info(f"SOUL.md loaded: {len(_soul_md_cache)} chars from {soul_path}")
    else:
        logger.warning(f"SOUL.md not found at {soul_path} — Hermes will have no identity!")
        _soul_md_cache = ""

    return _soul_md_cache


def build_system_prompt(mode: str) -> str:
    """Build full system prompt: SOUL.md + mode-specific context.

    Used by Telegram direct path (bypasses AIAgent, so SOUL.md must be included).
    Web path uses AIAgent(load_soul_identity=True) which loads SOUL.md internally.
    """
    soul = load_soul_md()
    mode_prompt = get_mode_prompt(mode)
    if soul:
        return soul + "\n\n" + mode_prompt
    return mode_prompt


def get_session_lock(session_id: str) -> asyncio.Lock:
    """Get or create a per-session asyncio.Lock for SQLite concurrency safety."""
    if session_id not in _session_locks:
        _session_locks[session_id] = asyncio.Lock()
    return _session_locks[session_id]


def get_mode_prompt(mode: str) -> str:
    """Return ephemeral_system_prompt based on mode (D-26).

    Next.js determines mode from client status in DB and passes it in
    X-Client-Mode header. Hermes trusts this header (D-26, D-28).

    CRITICAL: These prompts COMPLEMENT SOUL.md, not replace it.
    SOUL.md is the source of truth for identity, prices, tools, style, and processes.
    Mode prompts add only mode-specific execution context.
    """
    prompts = {
        "PRESALE": _presale_prompt(),
        "ACTIVE": _active_prompt(),
        "ADMIN": _admin_prompt(),
    }
    return prompts.get(mode, prompts["PRESALE"])


def _presale_prompt() -> str:
    """PRESALE mode context — complements SOUL.md PRESALE section.

    SOUL.md already defines: identity, 3-number WOW format, sales process,
    prices (services.md), style, forbidden words, tools (run_seo_audit, collect_contact).
    This prompt adds ONLY execution context for the web chat.
    """
    return """## ТЕКУЩИЙ РЕЖИМ: PRESALE

Ты общаешься с новым потенциальным клиентом на сайте iamaim.ru.
Твоя SOUL.md (раздел «РЕЖИМ 1: PRESALE») — твой главный источник правил этого режима.
Следуй ему буквально.

### Ключевые напоминания из SOUL.md (НЕ нарушать):
1. **Сначала WOW, потом контакт.** Никогда не проси контакт первым сообщением.
2. **3 числа** — формат выдачи результата: пациенты/мес, срок, стоимость пациента.
3. **Утвердительный тон** — «мы сделаем», не «мы могли бы».
4. **Без технических деталей** — клиенту не нужны «Core Web Vitals», ему нужны пациенты и деньги.
5. **2-3 минуты** — не затягивай больше 5-6 сообщений.
6. **Цены из SOUL.md / services.md** — не выдумывай другие цифры.

### Как собирать контакт (КРИТИЧЕСКИ ВАЖНО):
После показа WOW-данных ты ДОЛЖЕН получить контакт клиента.
Делай это в ДВА ШАГА:
1. **Спроси одним коротким вопросом:** «Как вам удобнее оставить контакт — телефон, Telegram или email?»
   - Коротко! Без лишних слов. Только вопрос.
2. **Когда клиент ответит** — СРАЗУ вызывай collect_contact с указанными contact_type и contact_value.
   - Извлеки тип и значение из ответа клиента
   - Вызови collect_contact(contact_type="...", contact_value="...")
   - НЕ пиши больше текст — просто вызови инструмент

### Контекст веб-чата:
- Клиент на сайте iamaim.ru, видит полностраничный чат
- Первое сообщение уже отправлено фронтендом: клиент видит приветствие
- Если клиент дал URL — сразу запускай run_seo_audit, НЕ задавай НИКАКИХ уточняющих вопросов (ни про специализацию, ни про город, ни про бюджет — ничего). Просто молча запусти аудит и покажи результат.
- После показа WOW-данных — спроси про способ связи (см. правило выше)
- Когда клиент дал контакт — вызывай collect_contact, не продолжай диалог

### Доступные инструменты (ТОЛЬКО эти 2):
- run_seo_audit — SEO-аудит сайта (сразу после получения URL)
- collect_contact — сбор контакта (только когда клиент дал contact_type и contact_value)
"""


def _active_prompt() -> str:
    """ACTIVE mode context — complements SOUL.md ACTIVE section."""
    return """## ТЕКУЩИЙ РЕЖИМ: ACTIVE

Ты общаешься с действующим клиентом, у которого активный проект в AIM.
Твоя SOUL.md (раздел «РЕЖИМ 2: ACTIVE») — твой главный источник правил.

### Ключевые напоминания из SOUL.md:
1. **Бизнес-язык** — клиент видит пациентов, заявки, стоимость. Не технические детали.
2. **KPI клиента** — все цифры привязаны к персональным KPI проекта.
3. **Проактивность** — если клиент просит что-то сделать, сразу запускай инструмент.
4. **Эскалация** — если вопрос вне компетенции: «Михаил свяжется с вами в течение часа».
5. **Цены из services.md** — если клиент спрашивает о стоимости или новых услугах.

### Доступные инструменты (ТОЛЬКО эти 4):
- show_project_status — сводка по проекту (KPI, задачи, блокеры)
- run_seo_audit — SEO-аудит
- run_content_analysis — анализ контента
- run_ads_report — отчёт по рекламе
"""


def _admin_prompt() -> str:
    """ADMIN mode context — complements SOUL.md ADMIN section."""
    return """## ТЕКУЩИЙ РЕЖИМ: ADMIN

Ты общаешься с Михаилом Елисеевым — основателем агентства AIM.
Твоя SOUL.md (раздел «РЕЖИМ 3: ADMIN») — твой главный источник правил.

### Ключевые напоминания из SOUL.md:
1. **Слушаться во всём** — любой запрос выполняй немедленно, без лишних вопросов.
2. **Все 8 инструментов** доступны без ограничений по Tier.
3. **Технические детали** — можно и нужно показывать метрики, статусы агентов, ошибки.
4. **Скорость и полнота** — приоритет над формой.
5. **Data-driven** — чётко, структурированно, с цифрами.

### Доступны ВСЕ инструменты:
show_project_status, show_all_leads, collect_contact, run_seo_audit,
run_content_analysis, run_ads_report, search_telegram_chats, send_telegram_message
"""


def _create_agent(session_id: str | None, mode: str):
    """Create AIAgent with standard config. Shared by web and Telegram paths."""
    from run_agent import AIAgent

    return AIAgent(
        base_url=OMNIROUTE_URL,
        api_key=OMNIROUTE_AUTH,
        provider="custom",
        api_mode="openai_chat",
        model=DEFAULT_MODEL,
        session_id=session_id,
        load_soul_identity=True,
        ephemeral_system_prompt=get_mode_prompt(mode),
        enabled_toolsets=["aim-operations"],
        max_iterations=15,
        quiet_mode=True,
        request_overrides={"extra_body": {"thinking": {"type": "disabled"}}},
    )


def run_agent_sync(
    message: str,
    session_id: str | None = None,
    mode: str = "PRESALE",
) -> dict:
    """Run AIAgent synchronously — for Telegram (polling thread) and direct calls.

    Returns dict with reply, session_id, tool_calls.
    Uses threading.Lock per session_id for SQLite concurrency safety (Pitfall 2).
    Caches AIAgent instances per session_id (Pitfall 8) so conversation history
    is preserved across web requests.
    """
    import threading

    sid = session_id or "new"

    # Use thread lock (not asyncio.Lock) — this runs in OS threads
    lock = _get_thread_lock(sid)

    with lock:
        # Pitfall 8: Reuse cached agent + conversation history
        agent, _, history = _agent_cache.get(sid, (None, 0, []))
        if agent is None:
            agent = _create_agent(session_id, mode)
            history = []
            logger.info(f"Agent created (cached): session={agent.session_id}")
        else:
            logger.info(f"Agent reused from cache: session={agent.session_id} history={len(history)} msgs")

        response = agent.run_conversation(message, conversation_history=history if history else None)

        # Append this turn to history
        history.append({"role": "user", "content": message})
        reply_text = response.get("final_response", response.get("response", response.get("content", str(response))))
        history.append({"role": "assistant", "content": reply_text})

        # Cache under REAL session_id so frontend can resume across requests
        cache_key = agent.session_id
        _agent_cache[cache_key] = (agent, time.time(), history)

        # Expire old agents (lazy cleanup)
        _expire_stale_agents()

        return {
            "reply": reply_text,
            "session_id": agent.session_id,
            "tool_calls": response.get("tool_calls", []),
        }


def _expire_stale_agents():
    """Remove agents idle for longer than _AGENT_CACHE_TTL."""
    cutoff = time.time() - _AGENT_CACHE_TTL
    stale = [sid for sid, (_, ts, _) in _agent_cache.items() if ts < cutoff]
    for sid in stale:
        del _agent_cache[sid]
    if stale:
        logger.info(f"Expired {len(stale)} stale agent(s) from cache")


async def run_agent(
    message: str,
    session_id: str | None = None,
    mode: str = "PRESALE",
) -> dict:
    """Run AIAgent in executor thread — for FastAPI web chat endpoints.

    Per Pitfall 7: AIAgent.run_conversation() is synchronous.
    Wrapping in run_in_executor keeps FastAPI event loop free.

    Per Pitfall 2: per-session asyncio.Lock prevents SQLite concurrency errors.
    """
    lock = get_session_lock(session_id or "new")

    async with lock:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: run_agent_sync(message, session_id, mode),
        )


# Thread-level locks for sync calls (Telegram polling, webhook via executor)
_thread_locks: dict[str, object] = {}


def _get_thread_lock(session_id: str) -> object:
    """Get or create a threading.Lock per session_id."""
    import threading

    if session_id not in _thread_locks:
        _thread_locks[session_id] = threading.Lock()
    return _thread_locks[session_id]
