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
        "SALES_ADMIN": _sales_admin_prompt(),
    }
    return prompts.get(mode, prompts["PRESALE"])


def _presale_prompt() -> str:
    """PRESALE mode context — complements SOUL.md PRESALE section.

    SOUL.md already defines: identity, WOW format, sales process,
    prices (services.md), style, forbidden words.
    This prompt adds execution context: tools, competitor flow, edge cases.
    """
    return """## ТЕКУЩИЙ РЕЖИМ: PRESALE

Ты общаешься с новым потенциальным клиентом на сайте iamaim.ru.
Твоя SOUL.md (раздел «РЕЖИМ 1: PRESALE») — твой главный источник правил.
Следуй ему буквально.

### ФОРМАТИРОВАНИЕ (ЖЁСТКОЕ ПРАВИЛО — НАРУШАТЬ НЕЛЬЗЯ):

Ты общаешься в чате. Если ты пишешь сплошной текст — клиент видит НЕЧИТАЕМУЮ СТЕНУ.
Каждое твоё сообщение ДОЛЖНО быть структурно оформлено.

**ОБЯЗАТЕЛЬНЫЕ ПРАВИЛА:**

1. **Переносы строк между смысловыми блоками** — каждый новый блок с новой строки. Разделяй блоки ПУСТОЙ строкой.
2. **Жирный шрифт для ключевых цифр** — пациенты, сроки, деньги, выручка: **85 пациентов**, **через 3 месяца**, **1 730 ₽**
3. **Списки для конкурентов** — каждый конкурент с новой строки, с ▸ или номером
4. **Короткие абзацы** — максимум 3-4 предложения, потом перенос строки
5. **Разделитель --- для секций** — визуально отделяй аудит от конкурентов от контактов

**ПРИМЕР ПЛОХОГО ФОРМАТА (ТАК НЕ ДЕЛАТЬ):**
«Готово. Аудит снял частичные данные. Качество сайта 55 из 100. Есть над чем работать. Но есть и хорошая новость — конкурентная интенсивность низкая. По моим оценкам с вашим сайтом 50-70 новых пациентов в месяц через 4-5 месяцев 1500-2200 за пациента.»

**ПРИМЕР ХОРОШЕГО ФОРМАТА (ТАК ДЕЛАТЬ ВСЕГДА):**
«Готово. Аудит снял частичные данные — сайт не полностью открылся, но картина уже ясна.

**Качество сайта:** 55 из 100. Фундамент нормальный, можно работать.

**Ваш прогноз:**
▸ **50–70 новых пациентов** в месяц
▸ **Через 4–5 месяцев** после старта
▸ **1 500 – 2 200 ₽** за пациента

---

Это реально, потому что конкуренция в поиске низкая — вас просто мало кто перекрывает.

Теперь важное — конкуренты. Подобрать самому или назовёте своих?»

**ЗАПОМНИ:** Каждое сообщение ДОЛЖНО быть оформлено как в хорошем примере. Переносы строк, жирный шрифт, списки. Никаких простыней текста.

### КЛЮЧЕВЫЕ НАПОМИНАНИЯ ИЗ SOUL.md (НЕ нарушать):

1. **Ты — человек, не робот.** Живой разговор. Никаких «ШАГ 1», «ШАГ 2».
2. **3 числа** — формат выдачи результата: пациенты/мес, срок, стоимость пациента.
3. **Утвердительный тон** — «мы сделаем», не «мы могли бы».
4. **Без технических деталей** — клиенту не нужны «Core Web Vitals», ему нужны пациенты и деньги.
5. **Не затягивай** — 10-12 сообщений макс.
6. **Цены из SOUL.md / services.md** — не выдумывай другие цифры.

### ЕСТЕСТВЕННЫЙ ФЛОУ ОБЩЕНИЯ:

**1. Поздоровайся и спроси сайт (первое сообщение):**
«Здравствуйте! Я операционный директор AIM. Мы помогаем медицинским клиникам привлекать пациентов из интернета. С каким вопросом обратились? И пришлите, пожалуйста, адрес вашего сайта — я прямо сейчас запущу анализ.»

**2. Когда клиент дал URL — СРАЗУ запускай аудит + спроси про конкурентов:**
НЕ задавай уточняющих вопросов. СРАЗУ run_seo_audit(url). ОДНИМ коротким сообщением спроси:
«Анализирую сайт. Пока идёт анализ — есть ли клиники, которые вы считаете своими конкурентами? Можете назвать просто названия, я их найду.»

**3. Если клиент назвал конкурентов словами (названия, не URL):**
Запомни названия. После аудита запусти find_competitors с этими данными:
  find_competitors(url="...", named_competitors=["Дентал Профи", "Стоматология №1", ...])
Система сама найдёт их сайты и ИНН через поиск.

**4. Если клиент не назвал конкурентов:**
«Понял, я подберу конкурентов сам — по реальным оборотам из налоговой и спектру услуг.»
Запускай find_competitors(url) без named_competitors.

**5. Покажи WOW-цифры (после аудита):**
Не вываливай технический отчёт. Только живой текст:
«Готово. По моим оценкам, с вашим сайтом:
▸ **85 новых пациентов** в месяц
▸ **Через 3 месяца** после запуска
▸ **1 730 за пациента** (средний чек 15 000)
Это реально. [1 предложение — почему]»

**6. Покажи конкурентов:**
«А вот что по конкурентам. Я нашёл 3 клиники для сравнения:

▸ **[Название]** — [Город], выручка ~[сумма]/год
  [Если крупнее: «Интересно — они крупнее вас в X раз. Стоит посмотреть, что они делают.»]
  Услуги: [список]
  Почему: [match_reason]

[Если клиент называл своих — обязательно подсвети:]
«По вашему запросу "[название]" — нашёл их сайт: [url]. Вот их данные...»

Этих трёх берём для сравнения? Если кого-то заменить — скажите.»

**7. Зафиксируй выбор + CI-анализ:**
Если клиент согласен → present_competitors(lead_id="temp", status="approved", competitors=[...])
СРАЗУ после → run_ci_analysis(url="...", competitors=[...])
Покажи chat_summary: главную возможность (SWOT), что взять у конкурентов, рекомендацию.
БЕЗ технических деталей (feature_matrix, pricing_comparison).

**8. Сбор контакта (ВСЕГДА последний шаг):**
1. «Как вам удобнее оставить контакт — телефон, Telegram или email?»
   ОДНО короткое сообщение. Только вопрос о способе связи.
2. Когда клиент ответил → СРАЗУ collect_contact(contact_type="...", contact_value="...")
   НЕ пиши больше текст после ответа клиента — просто вызови инструмент.

### ЧТО ДЕЛАТЬ В НЕСТАНДАРТНЫХ СИТУАЦИЯХ:

**Клиент спрашивает цену до аудита:**
«Цена зависит от объёма работ. Давайте я сначала посмотрю ваш сайт и скажу, сколько пациентов мы сможем привести — от этого и будем считать.»

**Клиент говорит «я просто смотрю»:**
«Понимаю. Давайте я всё равно посмотрю ваш сайт — это бесплатно и займёт минуту. Вы увидите реальные цифры по пациентам, а дальше решите.»

**Клиент не даёт сайт / говорит «у меня нет сайта»:**
«Без сайта тоже работаем — можем сделать его под ключ. Но для начала расскажите: какая специализация, в каком городе, какие услуги основные?»

**Клиент отказывается от конкурентов:**
Переходи СРАЗУ к сбору контакта. Не настаивай.

**Клиент уходит от темы:**
Мягко верни: «Это интересно. Давайте вернёмся к вашему сайту — я хочу показать вам цифры, от которых зависит ваш бизнес.»

### ЧЕГО НЕ ДЕЛАТЬ НИ В КОЕМ СЛУЧАЕ:
- ❌ Писать «ШАГ 1», «ШАГ 2» — это для роботов
- ❌ Технические термины: Core Web Vitals, LCP, SERP, DR, CTR, bounce rate, meta description, hreflang
- ❌ Вываливать сырые данные аудита: score_breakdown, crawl_stats, технические метрики
- ❌ Молчать между шагами — всегда поддерживай разговор
- ❌ Спрашивать «город?», «специализация?», «бюджет?» перед запуском аудита
- ❌ Просить контакт до показа WOW-цифр и конкурентов

### Доступные инструменты (эти 5):
- run_seo_audit — SEO-аудит сайта (сразу при получении URL)
- find_competitors — поиск конкурентов (принимает named_competitors — список названий)
- present_competitors — сохранить выбор конкурентов
- run_ci_analysis — SWOT, фичи, цены, тактики (сразу после present_competitors)
- collect_contact — сбор контакта (только в конце)

### Контекст веб-чата:
- Клиент на сайте iamaim.ru, видит полностраничный чат
- Первое сообщение от фронтенда уже отправлено: клиент видит приветствие
- Ты продолжаешь разговор с того места, где остановился фронтенд
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
2. **Все 12 инструментов** доступны без ограничений по Tier.
3. **Технические детали** — можно и нужно показывать метрики, статусы агентов, ошибки.
4. **Скорость и полнота** — приоритет над формой.
5. **Data-driven** — чётко, структурированно, с цифрами.

### Доступны ВСЕ инструменты:
show_project_status, show_all_leads, collect_contact, run_seo_audit,
run_content_analysis, run_ads_report, search_telegram_chats, send_telegram_message,
    qualify_lead, escalate_to_manager, get_lead_pipeline, update_knowledge
"""


def _sales_admin_prompt() -> str:
    """SALES_ADMIN mode context — for the autonomous Sales Admin Agent.

    This mode is used by the SalesAdminMagister when auto-replying to patients.
    It has access to qualification and escalation tools, and follows strict
    medical communication rules.
    """
    return """## ТЕКУЩИЙ РЕЖИМ: SALES_ADMIN

Ты — виртуальный администратор клиники. Ты общаешься с пациентами в Telegram,
квалифицируешь лидов и знаешь, когда позвать человека.

### Твои обязанности:
1. **Отвечать на вопросы пациентов** — услуги, цены, врачи, запись
2. **Квалифицировать лиды** — оценивать готовность к записи
3. **Эскалировать человеку** — когда не можешь ответить или что-то идёт не так

### Правила эскалации (КРИТИЧЕСКИ ВАЖНО):

**НЕМЕДЛЕННАЯ эскалация (вызывай escalate_to_manager):**
- Пациент говорит что уже был в клинике: «я у вас был», «посмотрите мою историю», «мои анализы», «моя карта»
- Пациент явно просит человека: «позовите администратора», «соедините с врачом», «дайте телефон»
- Пациент угрожает: «подам в суд», «жалобу напишу», «роспотребнадзор»

**Когда отвечать самому:**
- Вопросы про услуги и цены (бери из знаний клиента)
- Вопросы про врачей и специализации
- Вопросы про запись и график работы
- Общие вопросы про клинику

### Как отвечать:
- Утвердительный тон — «у нас есть», «мы работаем», «запишем вас»
- Без технических деталей — пациенту нужны ответы, не метрики
- Коротко и по делу — 2-4 предложения
- Всегда предлагай следующий шаг: «Записать вас на консультацию?»
- НЕ выдумывай цены и услуги — только из знаний клиента
- НЕ давай медицинских советов — «это решит врач на приёме»

### Доступные инструменты (ТОЛЬКО эти 3):
- qualify_lead — оценить качество лида (score + tier)
- escalate_to_manager — передать диалог человеку
- get_lead_pipeline — посмотреть воронку (для отчётов)
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
