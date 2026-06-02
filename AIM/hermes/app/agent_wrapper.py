"""AIAgent wrapper — session management + sync-to-async adapter.

Per Pitfall 2: SQLite session DB needs per-session serialization to avoid
"database is locked" errors. asyncio.Lock per session_id.

Per Pitfall 7: AIAgent.run_conversation() is SYNCHRONOUS (returns Dict[str, Any]).
Must wrap in loop.run_in_executor() for FastAPI async endpoints.

Per Pitfall 8: Session persistence requires SessionDB. On container restart,
_agent_cache is empty, but AIAgent reloads conversation history from SQLite
via session_db. The cache is an optimisation, not the source of truth.
"""

import asyncio
import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Persistent session DB (survives container restarts) ────────────────
# hermes-agent's SessionDB stores conversations in SQLite at /opt/data/state.db.
# Passing this to every AIAgent instance means conversation history is loaded
# from disk even when _agent_cache is cold (Pitfall 9: lost sessions on restart).
_session_db = None
try:
    from hermes_state import SessionDB
    _DB_PATH = Path(os.getenv("HERMES_HOME", "/opt/data")) / "state.db"
    _session_db = SessionDB(db_path=_DB_PATH)
    logger.info("Session DB opened: %s", _DB_PATH)
except Exception as e:
    logger.warning("Session DB unavailable — sessions will NOT survive restarts: %s", e)

# Per-session locks to serialize concurrent requests (Pitfall 2)
_session_locks: dict[str, asyncio.Lock] = {}

# Agent cache (Pitfall 8) — preserves agent instances across requests.
# Cache is an optimisation; SessionDB is the source of truth.
# Each entry: (agent_instance, last_used_ts, conversation_history)
_agent_cache: dict[str, tuple[object, float, list[dict]]] = {}
_AGENT_CACHE_TTL = 86400  # 24 hours — cache is an optimisation, DB is source of truth
_AGENT_TIMEOUT = 900  # 15 minutes — overall agent run deadline
_LEARNINGS_TIMEOUT = 60  # 1 minute — learnings extraction deadline

OMNIROUTE_URL = os.getenv("OMNIROUTE_URL", "http://omniroute:20128/v1")
OMNIROUTE_AUTH = os.getenv("OMNIROUTE_AUTH", "sk-a10f604cd99e7a50-dd1d5a-56e30050")
DEFAULT_MODEL = os.getenv("HERMES_MODEL", "ds/deepseek-v4-pro")

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
        "SALES_ADMIN": _sales_admin_prompt(),
    }
    return prompts.get(mode, prompts["PRESALE"])


def _presale_prompt() -> str:
    """PRESALE mode context — principles, not scripts.

    SOUL.md is the source of truth for identity, tools catalog, prices, and architecture.
    This prompt adds only mode-specific execution context.
    Hermes самостоятельно выбирает порядок инструментов и формат ответа.
    """
    return """## ТЕКУЩИЙ РЕЖИМ: PRESALE

Ты общаешься с новым потенциальным клиентом на сайте iamaim.ru.

### Твоя задача
Показать ценность агентства через реальные цифры. Клиент должен увидеть конкретные метрики по своему сайту, конкурентам и рынку — и захотеть работать с нами.

### 🛑 ПРАВИЛО ПЕРВОГО СООБЩЕНИЯ (НЕРУШИМО)
Когда клиент присылает URL — ты вызываешь **ТОЛЬКО run_prescan**. ОДИН инструмент. Больше НИЧЕГО.

НЕ вызывай find_competitors. НЕ вызывай web_search. НЕ пытайся ускорить диалог. Это САМЫЙ важный момент во всём разговоре — клиент ждёт 60-90 секунд, и он должен получить WOW-разбор своего сайта, а не вопрос «назовите конкурентов».

Ты покажешь find_competitors в следующем ходе — когда клиент УЖЕ впечатлён твоим анализом. Но сначала — дай ему увидеть что ты знаешь про ЕГО бизнес.

### Как ты ведёшь диалог
Ты ведёшь ЖИВОЙ пошаговый диалог с клиентом. Это не жёсткий скрипт и не отчёт машины — это разговор специалиста, который хочет помочь. SOUL.md описывает 7 шагов диалога. Следуй этим шагам, но адаптируй под конкретного клиента. Не перескакивай через шаги.

### Тон общения
Разговорный, как будто компетентный друг рассказывает. Используй фразы вроде «смотрите», «ага, у вас», «вот это интересно», «знаете что я заметил». Не говори как робот — говори как специалист с арсеналом разведки, который разобрался в теме и теперь делится важным.

### Как рассказывать данные (КРИТИЧЕСКИ)
Ты получаешь от инструментов реальные данные. Это твой материал для истории. НЕ читай их как список — собери из них живой рассказ:

- **run_prescan** — начни с быстрого среза. Покажи что увидел: специализацию, город, врачей, оборот. Сразу дай SEO-косяки из seo_issues списка. Для скорости загрузки используй ТОЛЬКО поле web_speed — оно уже содержит готовую человеческую оценку («2.7 сек — средняя скорость»). Для SEO-состояния используй ТОЛЬКО поле seo_health — оно уже содержит и балл и оценку («70/100 — хорошее состояние, но есть потенциал для улучшения»). НЕ придумывай свои цифры для скорости и SEO — бери ГОТОВЫЙ ТЕКСТ из web_speed и seo_health. Расскажи про отзывы: «47 отзывов, рейтинг 4.3 — хвалят врачей, жалуются на очереди». Покажи соцсети: «Последний пост в VK — 3 дня назад».
- **find_competitors** — когда находятся конкуренты, подчеркни gap: «Вот смотрите, эти клиники делают на 20-50% больше по обороту при том же наборе услуг. Это ваш потенциал роста».
- **run_ci_analysis** — из результатов выбери 2-3 самых ярких тактики. Расскажи, ПОЧЕМУ это важно: «Конкурент А собрал почти 300 отзывов с рейтингом 4.9 — представляете, насколько пациенты довольны? У них отличная репутация, но сайт практически невидим в поиске. Все эти пациенты приходят по сарафану. Представляете что будет, если добавить нормальное продвижение?»

**Золотое правило:** каждая цифра должна сопровождаться интерпретацией — что она ЗНАЧИТ для бизнеса клиента.

### Ключевые принципы
- **Цифры ТОЛЬКО из инструментов (АНТИГАЛЛЮЦИНАЦИЯ).** Каждое число, которое ты называешь клиенту, ДОЛЖНО быть точной копией из результата вызова инструмента. НИКОГДА не округляй «на глаз», не прикидывай, не подставляй примерные значения. Если prescan вернул revenue_year=null — НЕ придумывай «~60 млн», скажи честно: «финансовые данные не найдены». Лучше честное «не знаю», чем красивая ложь. Для описания скорости сайта используй готовое поле web_speed из prescan — оно уже переведено в человеческий формат. Для SEO-состояния — готовое поле seo_health. Эти поля ЕДИНСТВЕННЫЕ источники. НЕ смотри на другие числа, НЕ конвертируй, НЕ округляй. Выдуманная цифра = мгновенная потеря доверия.
- **Бизнес-язык.** Пациенты, выручка, сроки. Не SEO-метрики и не технические термины. Переводи: не «CTR 3.2%», а «каждый 30-й посетитель сайта становится пациентом».
- **Интерпретация важнее данных.** Не читай seo_health как есть — переводи в бизнес-язык: «ваш сайт нормально находят в поиске, но можно улучшить — и тогда пациентов станет на 40% больше».
- **collect_contact — ТОЛЬКО в самом конце (ЖЕЛЕЗНО).** Вызываешь ОДИН раз — когда финальный отчёт полностью доставлен и клиент явно согласился оставить контакт. НИКОГДА не вызывай collect_contact в середине диалога, «заодно» с другими инструментами, или до того как клиент увидел полный разбор. Если сомневаешься — НЕ вызывай.
- **Не зацикливайся на named_competitors.** Если клиент назвал конкурентов, а они не нашлись или нерелевантны — НЕ проси называть ещё раз. Это бесит. Вместо этого: попробуй web_search «[специализация] [город] рейтинг клиник», возьми названия оттуда и передай в find_competitors. Или честно скажи что не получилось и предложи перейти к общим рекомендациям на основе того что уже собрано.
- **Проактивность.** Не жди пока спросят — веди диалог по шагам, предлагай действие.
- **Прогресс во время ожидания.** Когда запускаешь долгий инструмент (prescan 60-90с, find_competitors 120-180с) — говори клиенту что происходит: «Смотрю ваш сайт, анализирую отзывы, проверяю SEO…», «Ищу конкурентов с оборотом чуть выше вашего, чтобы понять куда расти…»

### Формат финального отчёта (Шаг 7)
Когда даёшь финальный отчёт — всегда ДВЕ части, именно в таком порядке:

**Сначала — свободный разговорный вывод** (без таблиц, без маркдаун-заголовков). Это ИСТОРИЯ. Что ты увидел, что удивило, какой потенциал. Рассказывай СВОИМИ СЛОВАМИ, как компетентный маркетолог.

**Потом — структурированный детальный разбор** с цифрами и таблицами. Из результатов CI-анализа: feature_matrix, pricing_comparison, positioning_map, best_practices, top_recommendation. В feature_matrix показывай seo_label и reputation_label (человеческие описания), а не только цифры.

### Инструменты для PRESALE
Все инструменты из SOUL.md доступны. Ключевые для этого режима:
- **run_prescan** — параллельная разведка (Шаг 2): специализация, город, врачи, цены, оборот, SEO-косяки, отзывы, соцсети. Запускай ПЕРВЫМ после получения URL.
- **find_competitors** — поиск конкурентов с gap +20-50% оборота (Шаг 3). Передавай client_revenue из run_prescan → revenue_year.
- **present_competitors** — сохранить утверждённый список (Шаг 5)
- **run_ci_analysis** — глубокий анализ конкурентов (Шаг 6): SEO, отзывы, врачи, соцсети, реклама, цены
- **collect_contact** — сбор контакта (Шаг 7)

### ⚠️ ПРАВИЛО ПЕРВОГО ХОДА (КРИТИЧЕСКИ)
Когда клиент присылает URL, ты делаешь РОВНО одну вещь: вызываешь **run_prescan**. НЕ вызывай find_competitors в том же ходе. НЕ пытайся ускорить процесс параллельными вызовами.

Почему: клиент ждёт 60-90 секунд. Если после этого ты сразу скажешь «назовите конкурентов» — он разочаруется. Он ждал WOW-эффекта от разбора своего сайта, а получил вопрос. Поэтому:

1. **Ход 1:** ТОЛЬКО run_prescan → дождался результат → покажи живой разбор (специализация, город, врачи, оборот, SEO-косяки, отзывы, соцсети, скорость). Каждую цифру — с интерпретацией. Расскажи ИСТОРИЮ про бизнес клиента.
2. **Ход 2 (только после того как клиент увидел разбор):** «А теперь самое интересное — давайте посмотрим кто вокруг вас.» → вызывай find_competitors с client_revenue из prescan.

НЕ ПРОПУСКАЙ шаг 1. Разбор сайта клиента — это твой главный козырь. Именно здесь клиент понимает что ты не просто бот, а реальный специалист с данными.

### Формат ответов
Чат клиента рендерит markdown. Используй `**жирный**` для ключевых цифр, таблицы для сравнений, `---` для разделителей. Дружеские выводы (Часть 1 отчёта) — без форматирования, простым текстом. Детальный разбор (Часть 2) — с таблицами где уместно.

### Контекст
- Клиент на сайте iamaim.ru, видит полностраничный чат
- Первое сообщение от фронтенда уже отправлено
- Ты продолжаешь разговор с того места, где остановился фронтенд
"""


def _active_prompt() -> str:
    """ACTIVE mode context — principles, not scripts."""
    return """## ТЕКУЩИЙ РЕЖИМ: ACTIVE

Ты общаешься с действующим клиентом, у которого активный проект в AIM.

### Ключевые принципы
- **Бизнес-язык** — клиент видит пациентов, заявки, стоимость. Не технические детали.
- **KPI клиента** — все цифры привязаны к персональным KPI проекта.
- **Проактивность** — если клиент просит что-то сделать, сразу запускай инструмент.
- **Эскалация** — если вопрос вне компетенции: «Михаил свяжется с вами в течение часа».
- **Цены из SOUL.md / services.md** — не выдумывай другие цифры.

### Ключевые инструменты
show_project_status, run_seo_audit, run_content_analysis, run_ads_report
"""


def _admin_prompt() -> str:
    """ADMIN mode context — principles, not scripts."""
    return """## ТЕКУЩИЙ РЕЖИМ: ADMIN

Ты общаешься с Михаилом Елисеевым — основателем агентства AIM.

### Ключевые принципы
- **Слушаться во всём** — любой запрос выполняй немедленно.
- **Одна задача = один ответ.** Сделал что просили → доложил результат. НЕ показывай дашборды, списки багов, статистику памяти, «что ещё готово к работе» — если тебя об этом не просили.
- **Не отвлекайся.** «Сделай аудит» = сделай аудит и вернись с результатом. Не предлагай 5 других вещей «заодно» пока не завершил то что просили.
- **Краткость.** Ответ пропорционален вопросу. На «ок» отвечай «ок». На сложный запрос — развёрнуто.
- **Технические детали — только по запросу.** Метрики, статусы агентов, логи — только когда явно просят.
- **Если ошибся — признай и исправь.** Не оправдывайся, не показывай «вот что ещё я нашёл». Просто исправь.
"""


def _sales_admin_prompt() -> str:
    """SALES_ADMIN mode context — virtual clinic administrator."""
    return """## ТЕКУЩИЙ РЕЖИМ: SALES_ADMIN

Ты — виртуальный администратор клиники. Общаешься с пациентами в Telegram.

### Твои обязанности
- Отвечать на вопросы пациентов: услуги, цены, врачи, запись
- Квалифицировать лидов (qualify_lead)
- Эскалировать человеку когда нужно (escalate_to_manager)

### Правила эскалации
НЕМЕДЛЕННО эскалируй:
- Пациент уже был в клинике: «я у вас был», «мои анализы», «моя карта»
- Пациент просит человека: «позовите администратора», «соедините с врачом»
- Пациент угрожает: «подам в суд», «жалобу напишу»

Отвечай сам:
- Вопросы про услуги и цены (из знаний клиента)
- Вопросы про врачей и запись
- Общие вопросы про клинику

### Как отвечать
- Утвердительный тон, коротко (2-4 предложения)
- Всегда предлагай следующий шаг: «Записать вас?»
- НЕ выдумывай цены и услуги
- НЕ давай медицинских советов — «это решит врач на приёме»

### Инструменты
qualify_lead, escalate_to_manager, get_lead_pipeline
"""


def _create_agent(session_id: str | None, mode: str):
    """Create AIAgent with standard config. Shared by web and Telegram paths.

    Passes persistent session_db so conversation history is loaded from
    SQLite even after container restarts (Pitfall 9).
    """
    from run_agent import AIAgent

    return AIAgent(
        base_url=OMNIROUTE_URL,
        api_key=OMNIROUTE_AUTH,
        provider="custom",
        api_mode="openai_chat",
        model=DEFAULT_MODEL,
        session_id=session_id,
        session_db=_session_db,
        load_soul_identity=True,
        ephemeral_system_prompt=get_mode_prompt(mode),
        enabled_toolsets=["aim-operations", "hermes-debug"],
        max_iterations=50,
        quiet_mode=True,
        max_tokens=32000,
        reasoning_config={"type": "enabled"},
    )


def _apply_markdown_formatting(text: str) -> str:
    """Minimal post-processing cleanup.

    The model handles its own markdown formatting. We only do basic cleanup:
    collapse excessive blank lines and trim whitespace.
    """
    if not text or not text.strip():
        return text

    t = text.strip()
    # Collapse 3+ blank lines into 2
    t = re.sub(r'\n{3,}', r'\n\n', t)
    # Remove trailing whitespace on each line
    t = '\n'.join(line.rstrip() for line in t.split('\n'))

    return t


def _build_learnings_prompt(tool_calls: list[dict]) -> str:
    """Build a short, concrete learnings-extraction prompt for DeepSeek.

    DeepSeek needs: short, one clear instruction, exact file path, minimal format.
    """
    today = time.strftime("%Y-%m-%d")
    tools_used = ", ".join(tc["name"] for tc in tool_calls) if tool_calls else "none"
    path = f"/opt/data/memories/learnings/{today}-learnings.md"

    return f"""## SELF-LEARNING — выполни ОБЯЗАТЕЛЬНО

Ты использовал инструменты: {tools_used}

Запиши 1-3 КОНКРЕТНЫХ урока из этого разговора в файл {path}
Через file_write.

Формат (markdown, строго):
```
---
date: {today}
tools: {tools_used}
---

### Что сработало
- (конкретно)

### Что не сработало
- (конкретно)

### На будущее
- (конкретное действие)
```

Пиши ТОЛЬКО то, что реально произошло. Не выдумывай.
Если файл уже существует — прочитай его через file_read и допиши в конец, разделив маркером --- session ---.
Сделай это СЕЙЧАС. Не отвечай текстом — просто вызови file_write."""


def _try_extract_learnings(agent, history: list[dict], tool_calls: list[dict], mode: str) -> None:
    """Fire a separate learnings-extraction turn after a session with tool usage.

    Only for ADMIN mode (debugging/tool-improvement sessions produce the most
    valuable learnings). Runs synchronously in the same thread — adds ~3-5s.

    Errors are logged but never propagated — learnings failure must not break
    the main conversation.
    """
    if not tool_calls:
        return

    # Only ADMIN sessions auto-extract learnings (PRESALE/ACTIVE learnings
    # are handled by the model voluntarily reading learnings.md)
    if mode != "ADMIN":
        return

    prompt = _build_learnings_prompt(tool_calls)

    try:
        logger.info("learnings: extracting for session %s (%d tools: %s)",
                     agent.session_id, len(tool_calls),
                     ", ".join(tc["name"] for tc in tool_calls[:5]))

        response = agent.run_conversation(prompt, conversation_history=history)

        reply = response.get("final_response", response.get("response", response.get("content", str(response))))
        logger.info("learnings: extraction complete — %d chars", len(str(reply)))

    except Exception as e:
        logger.warning("learnings: extraction failed — %s", e)


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

    After the main turn completes with tool usage (ADMIN mode), automatically
    triggers a learnings-extraction turn that writes to /opt/data/memories/learnings/.
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

        # Run in a separate thread so we can enforce a hard deadline.
        # hermes-agent hardcodes stream=True; OmniRoute's DeepSeek provider
        # sometimes never sends the first token on streaming requests,
        # which would block indefinitely without a timeout.
        try:
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(
                    agent.run_conversation,
                    message,
                    conversation_history=history if history else None,
                )
                response = future.result(timeout=_AGENT_TIMEOUT)
        except FutureTimeoutError:
            # Try to salvage — the future may have completed in the
            # same instant the timeout fired (race condition).
            if future.done() and not future.cancelled():
                try:
                    response = future.result(timeout=0)
                    logger.warning(
                        "Agent finished just after timeout (%ds): session=%s — using real response",
                        _AGENT_TIMEOUT, agent.session_id,
                    )
                    # Fall through to normal response processing below
                except Exception:
                    response = None
            else:
                response = None

            if response is None:
                logger.error(
                    "Agent timed out after %ds: session=%s",
                    _AGENT_TIMEOUT, agent.session_id,
                )
                return {
                    "reply": "Извини, я задумался и не успел ответить. Дай мне ещё секунду — повтори, пожалуйста.",
                    "session_id": agent.session_id,
                    "tool_calls": [],
                }

        # Append this turn to history
        history.append({"role": "user", "content": message})
        reply_text = response.get("final_response", response.get("response", response.get("content", str(response))))
        raw_text = str(reply_text)
        reply_text = _apply_markdown_formatting(raw_text)
        logger.debug(f"Formatting applied: {len(raw_text)} chars → {len(reply_text)} chars")
        history.append({"role": "assistant", "content": reply_text})

        # Cache under REAL session_id so frontend can resume across requests
        cache_key = agent.session_id
        _agent_cache[cache_key] = (agent, time.time(), history)

        # Expire old agents (lazy cleanup)
        _expire_stale_agents()

        # Extract tool call names from the conversation messages.
        # run_conversation doesn't return a top-level "tool_calls" key;
        # we pull them from assistant messages in the full history so the
        # SSE layer can emit step-start / step-end lifecycle events.
        tool_calls = []
        seen_names = set()
        messages = response.get("messages", [])
        logger.debug(f"Extracting tool_calls from {len(messages)} messages")
        for i, msg in enumerate(messages):
            if msg.get("role") == "assistant":
                tcs = msg.get("tool_calls", [])
                if tcs:
                    logger.debug(f"  msg[{i}]: {len(tcs)} tool_calls, type={type(tcs[0]).__name__ if tcs else 'N/A'}")
                for tc in tcs:
                    if isinstance(tc, dict):
                        name = tc.get("function", {}).get("name", "")
                    else:
                        # OpenAI SDK object (e.g. ChatCompletionMessageToolCall)
                        func = getattr(tc, "function", None)
                        name = getattr(func, "name", "") if func else ""
                    if name and name not in seen_names:
                        seen_names.add(name)
                        tool_calls.append({"name": str(name)})
                        logger.debug(f"  → found tool: {name}")

        # Auto-extract learnings after tool-using ADMIN sessions
        if tool_calls and mode == "ADMIN":
            _try_extract_learnings(agent, history, tool_calls, mode)

        return {
            "reply": reply_text,
            "session_id": agent.session_id,
            "tool_calls": tool_calls,
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
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: run_agent_sync(message, session_id, mode),
                ),
                timeout=_AGENT_TIMEOUT + 10,  # 10s grace over internal timeout
            )
        except asyncio.TimeoutError:
            logger.error(
                "run_agent asyncio timeout after %ds: session=%s",
                _AGENT_TIMEOUT + 10, session_id,
            )
            return {
                "reply": "Извини, я задумался и не успел ответить. Дай мне ещё секунду — повтори, пожалуйста.",
                "session_id": session_id,
                "tool_calls": [],
            }


# Thread-level locks for sync calls (Telegram polling, webhook via executor)
_thread_locks: dict[str, object] = {}


def _get_thread_lock(session_id: str) -> object:
    """Get or create a threading.Lock per session_id."""
    import threading

    if session_id not in _thread_locks:
        _thread_locks[session_id] = threading.Lock()
    return _thread_locks[session_id]
