"""AIAgent wrapper — session management + sync-to-async adapter.

Per Pitfall 2: SQLite session DB needs per-session serialization to avoid
"database is locked" errors. asyncio.Lock per session_id.

Per Pitfall 7: AIAgent.run_conversation() is SYNCHRONOUS (returns Dict[str, Any]).
Must wrap in loop.run_in_executor() for FastAPI async endpoints.

Per Pitfall 8: Session persistence requires SessionDB. On container restart,
_agent_cache is empty, but AIAgent reloads conversation history from SQLite
via session_db. The cache is an optimisation, not the source of truth.

Hermes v8: PRESALE = LLM-оркестратор. Свободный выбор инструментов, параллельные вызовы.
Никакого жёсткого скрипта. Python-стейт-машина (PipelineEngine) — только для run_full_scout (batch).
"""

import asyncio
import json
import logging
import os
import re
import secrets
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from datetime import datetime
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
_AGENT_CACHE_TTL = 3600  # 24 hours — cache is an optimisation, DB is source of truth
_AGENT_TIMEOUT = 900  # 15 minutes — overall agent run deadline
_LEARNINGS_TIMEOUT = 60  # 1 minute — learnings extraction deadline

OMNIROUTE_URL = os.getenv("OMNIROUTE_URL", os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"))
OMNIROUTE_AUTH = os.getenv("OMNIROUTE_AUTH", os.getenv("DEEPSEEK_API_KEY", ""))
DEFAULT_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "custom")  # "custom" = DeepSeek/OpenAI-compat, "anthropic" = native Anthropic

# Phase 2 / Plan 02-02: OPT-IN env var for the 3-pass orchestrator.
# Default "0" = OFF — production behaviour is unchanged (existing PRESALE
# path with single AIAgent.run_conversation() call). Set ORCHESTRATOR_MODE=1
# to route PRESALE + URL through run_three_pass() (Collect → Gap-analyze →
# Fill+Assemble). On any orchestrator exception we fall back to the existing
# path (ORC-05: PipelineEngine stays as further fallback at the engine level).
ORCHESTRATOR_MODE = os.getenv("ORCHESTRATOR_MODE", "0") == "1"
logger.info("ORCHESTRATOR_MODE=%s (Phase 2 / Plan 02-02 opt-in gate)", ORCHESTRATOR_MODE)

# SOUL.md cache — loaded once, reused across requests
_soul_md_cache: Optional[str] = None

# 3PHASE_PIPELINE.md cache — loaded once, reused across requests
_pipeline_md_cache: Optional[str] = None


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


def load_pipeline_md() -> str:
    """Load 3PHASE_PIPELINE.md from $HERMES_HOME/3PHASE_PIPELINE.md (cached).

    copy_soul.sh copies this file from skills/aim/ to $HERMES_HOME at startup.
    Contains the detailed 3-phase presale flow that Hermes must follow.
    """
    global _pipeline_md_cache
    if _pipeline_md_cache is not None:
        return _pipeline_md_cache

    hermes_home = os.getenv("HERMES_HOME", "/opt/data")
    pipeline_path = Path(hermes_home) / "3PHASE_PIPELINE.md"

    if pipeline_path.exists():
        _pipeline_md_cache = pipeline_path.read_text()
        logger.info(f"3PHASE_PIPELINE.md loaded: {len(_pipeline_md_cache)} chars from {pipeline_path}")
    else:
        logger.warning(f"3PHASE_PIPELINE.md not found at {pipeline_path} — Hermes won't know the full pipeline!")
        _pipeline_md_cache = ""

    return _pipeline_md_cache


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
    """PRESALE mode context — orchestrator, not script-follower.

    SOUL.md v4 defines the tools catalog and strategy.
    Hermes САМ решает какие инструменты вызывать, в каком порядке, насколько глубоко копать.
    Никакого жёсткого скрипта. LLM — оркестратор.
    """
    return """## ТЕКУЩИЙ РЕЖИМ: PRESALE

Ты общаешься с новым потенциальным клиентом на сайте iamaim.ru.

### 🛑 НЕИЗМЕНЯЕМОЕ ПРАВИЛО: КОД НЕПРИКОСНОВЕНЕН

Ты НЕ можешь изменять код инструментов Hermes. Ни при каких обстоятельствах.

Если инструмент вернул ошибку — сообщи клиенту что данные по этому направлению собрать не удалось, и продолжай работу с тем что есть. НЕ пытайся «починить» код.

### Твоя задача
Показать ценность агентства через реальные цифры. Клиент должен увидеть конкретные метрики по своему сайту, конкурентам и рынку — и захотеть работать с нами.

### 🛑 ПРИВЕТСТВИЕ (КОГДА КЛИЕНТ НЕ ДАЛ URL)
Если клиент написал без URL — представься коротко и по делу.

**Формат (строго — 3 предложения):**
1. «Здравствуйте!» (или «Добрый день!»)
2. Кто ты и твой арсенал — одно короткое предложение
3. Просьба скинуть URL (+ упомяни конкурентов если есть)

**Пример:**
«Здравствуйте! Я Hermes, разведчик агентства AIM — под капотом анализ сайта, SEO, отзывы, поиск конкурентов. Скидывайте ссылку на ваш сайт — посмотрим что у вас и как.»

**Длина:** 3 предложения. Не 2. Не 5. ТРИ.

### 🆓 СВОБОДНАЯ РАЗВЕДКА (КОГДА КЛИЕНТ ДАЛ URL)

Ты — свободный художник. Ты НЕ следуешь жёсткому скрипту. Ты сам решаешь какие инструменты вызывать.

**🛑 СНАЧАЛА НАПИШИ КЛИЕНТУ.**
ПРЕЖДЕ чем вызывать любой инструмент — отправь клиенту ОДНО короткое сообщение. Это знак что ты взял ссылку в работу. Пример: «Принял, смотрю сайт galaxy.clinic — под капотом поиск конкурентов, аудит скорости, отзывы, врачи. Дайте мне пару минут собрать данные.» И ТОЛЬКО ПОТОМ вызывай инструменты.

**Принцип:**
1. СНАЧАЛА напиши клиенту что начинаешь разведку
2. Быстро оцени сайт (quick_overview или web_scraper)
3. Пойми город, специализацию, размер клиники
4. Реши что ВАЖНО для этой конкретной клиники:
   - Всем: конкуренты (find_competitors) + репутация (run_review_platforms)
   - Почти всем: SEO (run_seo_audit) или скорость (run_lighthouse)
   - Часто: контент (run_content_analysis), вакансии (run_hh_analysis)
   - Нишево: Instagram (run_instagram_content), СМИ (run_smi_mentions), врачи (find_doctor_handles)
   - Если конкурентов 2+: run_ci_analysis
4. ЗАПУСКАЙ НЕСКОЛЬКО ИНСТРУМЕНТОВ ПАРАЛЛЕЛЬНО где это возможно — инструменты не зависят друг от друга
5. Рассказывай клиенту ЧТО ты делаешь пока инструменты работают
6. Когда данные собраны — собери живой рассказ, интерпретируй, дай выводы

**Ты НЕ должен:**
- ❌ Запускать ВСЕ 40 инструментов — только те, что релевантны
- ❌ Ждать завершения одного инструмента чтобы запустить следующий (если они не зависят друг от друга)
- ❌ Паниковать если инструмент вернул ошибку или NO_DATA — иди дальше
- ❌ Сыпать на клиента сырые данные списком — рассказывай историю

**Ты ДОЛЖЕН:**
- ✅ Параллелить где можно (find_competitors + run_review_platforms + run_lighthouse — одновременно)
- ✅ Адаптировать глубину под клинику (маленькая клиника в регионе ≠ большая в Москве)
- ✅ Интерпретировать каждую цифру — что она ЗНАЧИТ для бизнеса

### Как ты ведёшь диалог
ЖИВОЙ разговор. Ты разведчик с арсеналом из 40+ инструментов. Не читай данные как список — собирай из них живой рассказ.

**Золотое правило:** каждая цифра должна сопровождаться интерпретацией — что она ЗНАЧИТ для бизнеса клиента.

### Ключевые принципы
- **Цифры ТОЛЬКО из инструментов.** Не округляй на глаз, не прикидывай. Нет данных → честно скажи.
- **Бизнес-язык.** Пациенты, выручка, сроки. Не «CTR 3.2%», а «каждый 30-й посетитель становится пациентом».
- **Параллельность.** Не жди. Инструменты работают одновременно.
- **Глубина по ситуации.** Стоматология в регионе ≠ пластическая хирургия в Москве.
- **collect_contact — ТОЛЬКО в конце.** Когда ценность доставлена и клиент готов.
- **Не зацикливайся.** Если конкурент не нашёлся — не проси клиента назвать ещё раз. Пробуй альтернативы или иди дальше.

### Формат ответов
Чат рендерит markdown. Используй `**жирный**` для цифр, таблицы для сравнений.

### 🛑 ФИНАЛ: ВЫЗОВ post_report — НЕРУШИМОЕ ПРАВИЛО

**Ты НЕ можешь завершить разговор с клиентом, не вызвав `post_report`.**

Инструмент `post_report` публикует отчёт как **WordPress-страницу на iamaim.ru** (прямая вставка в базу данных). Страница получает уникальный URL вида `https://iamaim.ru/abc12345`, оформлена в дизайн-системе AIM (dual theme, стекломорфизм, метрики, таблицы). Клиент может открыть её на любом устройстве, переслать, показать коллегам.

**🎯 ПЕРЕД тем как вызывать post_report — ВЫЗОВИ read_report_reference.**
Этот инструмент вернёт идеальный пример отчёта (ИПХиК). Изучи его структуру, стиль подачи данных, формат gap-блоков, таблиц и выводов. Твой отчёт должен быть ТАКОГО ЖЕ качества: та же глубина интерпретации, та же структура секций, тот же бизнес-язык.

**Это не опционально.** Это ПОСЛЕДНИЙ инструмент который ты вызываешь перед тем как дать клиенту финальный ответ.

**Что передать:**
- `title`: «Разведка [название клиники]» (например «Разведка arclinic.ru»)
- `client_url`: URL сайта клиента (например https://arclinic.ru)
- `content`: ПОЛНЫЙ markdown-отчёт со ВСЕМИ секциями которые ты исследовал. Структура:
  ```
  ## Профиль клиники
  (город, специализация, ИНН, руководитель, лицензия — всё что узнал)

  ## Рынок и ниша
  (объём рынка, тренды, позиционирование)

  ## Конкуренты
  (таблица сравнения если есть данные, ключевые отличия)

  ## Технический аудит
  (скорость — run_lighthouse, SEO — run_seo_audit)

  ## Репутация
  (отзывы — run_review_platforms, рейтинги по платформам)

  ## Команда
  (врачи, вакансии если есть данные)

  ## Ключевые находки
  (3-5 главных выводов, каждая находка с конкретной цифрой)

  ## Рекомендации
  (что делать прямо сейчас, с приоритетами)
  ```

**Пример вызова:**
Вызови post_report с этими параметрами:
- title = "Разведка arclinic.ru"
- client_url = "https://arclinic.ru"
- content = (твой полный markdown-отчёт)

**После вызова post_report ТОЛЬКО ТОГДА напиши клиенту:**
1. Краткую выжимку (3 ключевых пункта)
2. Ссылку на опубликованный отчёт: «Я собрал полный отчёт — откройте обязательно: [URL]»
3. Предложение обсудить с Михаилом

**ЗАПРЕЩЕНО:**
- ❌ Говорить «сайт не принимает публикацию» или «техническая мелочь с БД» — это ложь, инструмент работает
- ❌ Завершать разговор без вызова post_report
- ❌ Обещать «потом опубликую» или «Михаил поправит»
- ❌ Придумывать любые другие отмазки почему не опубликовал

**Если post_report вернул ошибку** — скажи честно «не получилось опубликовать: [текст ошибки]» и предложи клиенту текстовую выжимку. Но ВЫЗОВИ инструмент в любом случае.

### Контекст
- Клиент на сайте iamaim.ru, видит полностраничный чат
- У тебя доступны ВСЕ разведывательные инструменты, включая `post_report` для публикации
"""


def _active_prompt() -> str:
    """ACTIVE mode context — principles, not scripts."""
    return """## ТЕКУЩИЙ РЕЖИМ: ACTIVE

Ты общаешься с действующим клиентом, у которого активный проект в AIM.

### 🛑 НЕИЗМЕНЯЕМОЕ ПРАВИЛО: КОД НЕПРИКОСНОВЕНЕН
Ты НЕ можешь изменять код инструментов. Если инструмент вернул ошибку — сообщи об этом. НЕ пытайся чинить код. Код пишет разработчик.

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

### 🛑 НЕИЗМЕНЯЕМОЕ ПРАВИЛО: КОД НЕПРИКОСНОВЕНЕН

Ты НЕ можешь изменять код инструментов Hermes. Ни при каких обстоятельствах.

Если инструмент вернул ошибку — сообщи об этом. НЕ пытайся «починить» код через file_write или shell_exec. НЕ переписывай работающие инструменты. НЕ «улучшай» код без явного запроса Михаила.

Код пишет разработчик. Твоя задача — использовать инструменты, а не менять их.
file_guard защищает /opt/hermes/app/ от любых изменений — любая попытка записи будет заблокирована.

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

### 🛑 КОД НЕПРИКОСНОВЕНЕН
Ты НЕ можешь изменять код инструментов. Твоя задача — общение с пациентами, а не программирование.

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


def _create_agent(session_id: str | None, mode: str, enabled_toolsets: list[str] | None = None):
    """Create AIAgent with standard config. Shared by web and Telegram paths.

    Passes persistent session_db so conversation history is loaded from
    SQLite even after container restarts (Pitfall 9).

    Hermes v7: uses get_toolsets_for_mode(mode) instead of hardcoded toolset list.
    ONBOARDING → ["aim-operations"], ADMIN → ["aim-operations", "hermes-debug"].
    """
    from run_agent import AIAgent
    from app.pipeline.mode_gate import get_toolsets_for_mode, apply_mode_filter, remove_mode_filter
    from app.pipeline.file_guard import set_current_mode

    if enabled_toolsets is None:
        enabled_toolsets = get_toolsets_for_mode(mode)

    # Hermes v7: сообщаем file_guard текущий режим для проверок file_write
    set_current_mode(mode)

    # Hermes v7: фильтруем индивидуальные инструменты (не только toolsets)
    # В PRESALE прячем 31 инструмент — только run_full_scout + CRM + отчёты
    apply_mode_filter(mode)

    try:
        if LLM_PROVIDER == "anthropic":
            # Native Anthropic (Claude) — использует ANTHROPIC_API_KEY
            return AIAgent(
                provider="anthropic",
                model=DEFAULT_MODEL if DEFAULT_MODEL != "deepseek-chat" else "claude-sonnet-4-6",
                session_id=session_id,
                session_db=_session_db,
                load_soul_identity=True,
                ephemeral_system_prompt=get_mode_prompt(mode),
                enabled_toolsets=enabled_toolsets,
                max_iterations=25,
                quiet_mode=True,
                max_tokens=16000,
            )
        elif LLM_PROVIDER == "openrouter":
            # OpenRouter — Claude Sonnet 4.6 with extended thinking
            # reasoning_config defaults to {"enabled": True, "effort": "medium"} for OpenRouter
            return AIAgent(
                base_url=OMNIROUTE_URL,
                api_key=OMNIROUTE_AUTH,
                provider="openrouter",
                api_mode="openai_chat",
                model=DEFAULT_MODEL,
                session_id=session_id,
                session_db=_session_db,
                load_soul_identity=True,
                ephemeral_system_prompt=get_mode_prompt(mode),
                enabled_toolsets=enabled_toolsets,
                max_iterations=25,
                quiet_mode=True,
                max_tokens=16000,
            )
        else:
            # Custom OpenAI-compatible (DeepSeek, z.ai GLM, etc.)
            # z.ai coding endpoint: disable reasoning/thinking to avoid
            # slow 20s-per-turn reasoning overhead. z.ai uses Kimi-style
            # `thinking: {type: disabled}` format (patched in run_agent.py).
            _is_zai = "api.z.ai" in (OMNIROUTE_URL or "").lower()
            _reasoning_cfg = {"enabled": False} if _is_zai else None
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
                enabled_toolsets=enabled_toolsets,
                max_iterations=25,
                quiet_mode=True,
                max_tokens=16000,
                reasoning_config=_reasoning_cfg,
            )
    finally:
        remove_mode_filter()


def _extract_url_from_message(message: str) -> str | None:
    """Extract first URL from a user message.

    Handles both full URLs (https://example.ru) and bare domains (example.ru).
    """
    # Try full URL first: https://example.ru/page
    full_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    match = re.search(full_pattern, message)
    if match:
        return match.group(0)

    # Try bare domain: example.ru, clinic-name.com, site.рф
    bare_pattern = (
        r'(?:^|\s)([a-zA-Z0-9](?:[a-zA-Z0-9\-]*[a-zA-Z0-9])?\.'
        r'(?:ru|com|net|org|рф|su|io|pro|dev|digital|agency|'
        r'club|online|site|tech|med|health|clinic|center|care|'
        r'msk|spb|rf|info|biz))(?:\s|$|[,.!?;:")]|$)'
    )
    match = re.search(bare_pattern, message)
    if match:
        return match.group(1)
    return None


def _extract_orchestrator_reply(state) -> str:
    """Pull the final assistant text from Pass 3's run_conversation result.

    Phase 2 / Plan 02-02: OrchestratorState.collected_data["pass_fill_assemble_result"]
    holds the raw dict returned by the LAST AIAgent.run_conversation() call
    (Pass 3 — Fill+Assemble). We use the same field-path fallback as
    ``run_agent_sync`` below: final_response -> response -> content ->
    str(result). Returns "" if no text could be extracted — caller treats
    empty string as a signal to fall back to the existing AIAgent path.
    """
    collected = getattr(state, "collected_data", None)
    if not isinstance(collected, dict):
        return ""
    pasm = collected.get("pass_fill_assemble_result")
    if not isinstance(pasm, dict):
        return ""
    for key in ("final_response", "response", "content"):
        val = pasm.get(key)
        if isinstance(val, str) and val.strip():
            return val
        if isinstance(val, dict):
            inner = val.get("content") or val.get("text")
            if isinstance(inner, str) and inner.strip():
                return inner
    return ""


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


def _run_onboarding_pipeline(
    message: str,
    session_id: str,
    client_url: str,
    mode: str = "ONBOARDING",
) -> dict:
    """Run Hermes v7 PipelineEngine for ONBOARDING mode with URL.

    Python-стейт-машина: выполняет фазы последовательно, LLM — только интерпретатор.

    Args:
        message: Исходное сообщение пользователя (с URL).
        session_id: ID сессии.
        client_url: Извлечённый URL сайта клиента.
        mode: Режим работы.

    Returns:
        dict с reply, session_id, tool_calls.
    """
    from app.pipeline.engine import PipelineEngine
    from app.tools.session_archive import save_tool_output, upsert_metadata

    logger.info(
        "PipelineEngine: starting onboarding for %s (session=%s)",
        client_url, session_id,
    )

    engine = PipelineEngine()

    try:
        # Запускаем пайплайн синхронно (asyncio.run в отдельном потоке)
        import asyncio as _asyncio

        state = _asyncio.run(engine.execute(
            session_id=session_id,
            client_url=client_url,
            mode=mode,
        ))

        # ── Сохраняем metadata (данные уже сохранены engine.py при HTML BUILD) ─
        completed = sum(
            1 for r in state.phases.values()
            if r.status.value in ("completed", "no_data")
        )
        failed = sum(
            1 for r in state.phases.values()
            if r.status.value in ("permanent_failure", "tool_failed", "timed_out")
        )

        upsert_metadata(
            session_id,
            url=client_url,
            completed_phases=completed,
            failed_phases=failed,
            total_phases=len(state.phases),
            started_at=state.started_at,
        )
        logger.info(
            "PipelineEngine: metadata saved for %s (%d/%d phases completed)",
            session_id, completed, len(state.phases),
        )

        # ── Формируем ответ со ВСЕМИ фазами ────────────────────────
        reply_parts = [
            f"Разведка завершена: {completed}/{len(state.phases)} фаз собраны.",
        ]

        # Все фазы в порядке выполнения (из PHASES)
        from app.pipeline.phases import PHASES as _PHASES
        for phase in _PHASES:
            interp_key = f"{phase.name}_interpretation"
            if interp_key in state.accumulated_data:
                interp = str(state.accumulated_data[interp_key])
                if interp and len(interp) > 20:
                    # Обрезаем длинные интерпретации (чат не резиновый)
                    if len(interp) > 600:
                        interp = interp[:600] + "..."
                    reply_parts.append(f"\n### {phase.name}\n{interp}")

        if failed > 0:
            reply_parts.append(f"\n⚠️ {failed} фаз не удалось выполнить.")

        # ── Пробуем сгенерировать HTML-отчёт ──────────────────────
        try:
            from app.tools.generate_html_report import handle_generate_html_report
            report_result = _asyncio.run(handle_generate_html_report(
                session_hash=session_id,
                client_url=client_url,
            ))
            if isinstance(report_result, str):
                report_result = json.loads(report_result)
            if report_result.get("url"):
                reply_parts.insert(
                    1,
                    f"\n📊 [Открыть полный отчёт]({report_result['url']})",
                )
        except Exception as _report_err:
            logger.warning("HTML report generation skipped: %s", _report_err)

        reply = "\n".join(reply_parts)

        tool_calls = []
        for pr in state.phases.values():
            for tc in pr.tool_calls_made:
                if tc not in [t["name"] for t in tool_calls]:
                    tool_calls.append({"name": tc})

        return {
            "reply": reply,
            "session_id": session_id,
            "tool_calls": tool_calls,
        }

    except Exception as e:
        logger.exception("PipelineEngine: onboarding failed for %s", client_url)
        return {
            "reply": (
                f"Я запустил разведку вашего сайта, но произошла ошибка: {e}.\n"
                "Дайте мне минуту и попробуйте ещё раз."
            ),
            "session_id": session_id,
            "tool_calls": [],
        }
    finally:
        # Очищаем in-memory state после завершения пайплайна
        try:
            from app.pipeline.engine import cleanup_pipeline_state
            cleanup_pipeline_state(session_id)
        except Exception:
            pass


def run_agent_sync(
    message: str,
    session_id: str | None = None,
    mode: str = "PRESALE",
) -> dict:
    """Run AIAgent synchronously — for Telegram (polling thread) and direct calls.

    Hermes v7 routing:
    - ONBOARDING mode + URL → PipelineEngine (Python state machine)
    - ONBOARDING mode без URL → обычный AIAgent (приветствие)
    - ADMIN/ACTIVE/SALES_ADMIN → без изменений (LLM-first)

    Returns dict with reply, session_id, tool_calls.
    Uses threading.Lock per session_id for SQLite concurrency safety (Pitfall 2).
    Caches AIAgent instances per session_id (Pitfall 8) so conversation history
    is preserved across web requests.

    After the main turn completes with tool usage (ADMIN mode), automatically
    triggers a learnings-extraction turn that writes to /opt/data/memories/learnings/.

    Phase 2 / Plan 02-02: ORCHESTRATOR_MODE=1 env var включает 3-pass cycle
    (Collect → Gap-analyze → Fill+Assemble) для PRESALE + URL. Fallback на
    AIAgent direct path при exception. ORC-05: PipelineEngine остаётся как
    fallback на уровне below (run_full_scout path).
    """
    import threading

    sid = session_id or "new"

    # ── Hermes v8: PRESALE routing — свободный оркестратор ───────
    # Phase 2 / Plan 02-02: ORCHESTRATOR_MODE OPT-IN gate.
    # When ORCHESTRATOR_MODE=1 AND mode is PRESALE/ONBOARDING AND a URL is
    # extracted from the user message → route through run_three_pass()
    # (Collect → Gap-analyze → Fill+Assemble). On ANY orchestrator-side
    # exception we log and fall through to the existing AIAgent direct
    # path below (ORC-05 — PipelineEngine stays as further fallback).
    mode_upper = mode.upper()
    if mode_upper in ("ONBOARDING", "PRESALE"):
        client_url = _extract_url_from_message(message)
        if client_url:
            if ORCHESTRATOR_MODE:
                logger.info(
                    "Orchestrator mode ACTIVE — running 3-pass cycle for session=%s url=%s",
                    sid, client_url,
                )
                try:
                    from app.orchestrator import run_three_pass
                    # run_three_pass is async; this function is sync and runs
                    # inside a ThreadPoolExecutor without a running event loop.
                    # asyncio.run() creates a fresh loop for the orchestrator
                    # cycle and tears it down on return — matches the existing
                    # "sync function calls async helper" pattern used elsewhere
                    # in the codebase. Per Plan 02-02 action step 4.
                    orch_state = asyncio.run(
                        run_three_pass(
                            session_id=sid,
                            client_url=client_url,
                            client_name="",
                            mode=mode_upper,
                            chat_id=0,
                        )
                    )
                    reply_text = _extract_orchestrator_reply(orch_state)
                    if reply_text:
                        logger.info(
                            "Orchestrator: 3-pass cycle completed for session=%s — pass_status=%s",
                            sid, getattr(orch_state, "pass_status", {}),
                        )
                        return {
                            "reply": reply_text,
                            "session_id": sid,
                            "tool_calls": [],
                        }
                    # No reply text extracted — log and fall through to
                    # existing AIAgent path (do NOT return).
                    logger.warning(
                        "Orchestrator returned empty reply — falling back to AIAgent path (session=%s)",
                        sid,
                    )
                except Exception:
                    logger.exception(
                        "Orchestrator failed, falling back to AIAgent direct path (session=%s)",
                        sid,
                    )
                    # Fall through to existing path (do NOT return).
            else:
                # v8: не форсируем конкретный инструмент. LLM сама решает
                # какие инструменты вызвать, следуя SOUL.md v4 (оркестратор).
                logger.info(
                    "v8 routing: PRESALE + URL → свободный оркестратор (%s)",
                    client_url,
                )
        else:
            logger.info("v8 routing: PRESALE без URL → AIAgent (приветствие)")
    # ───────────────────────────────────────────────────────────────

    # Use thread lock (not asyncio.Lock) — this runs in OS threads
    lock = _get_thread_lock(sid)

    with lock:
        # Pitfall 8: Reuse cached agent + conversation history
        agent, _, history = _agent_cache.get(sid, (None, 0, []))
        if agent is None:
            agent = _create_agent(session_id, mode)
            if not history:
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

        # Cache under REAL session_id so frontend can resume across requests.
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
                        tc_id = tc.get("id", "")
                        name = tc.get("function", {}).get("name", "")
                    else:
                        # OpenAI SDK object (e.g. ChatCompletionMessageToolCall)
                        tc_id = getattr(tc, "id", "")
                        func = getattr(tc, "function", None)
                        name = getattr(func, "name", "") if func else ""
                    # Skip force-injected tool calls (P5 fix) — they were
                    # executed by code, not by the LLM, and should not be
                    # reported to the frontend as real tool calls.
                    if tc_id and str(tc_id).startswith("force_"):
                        continue
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

    Phase 2 / Plan 02-02: ORCHESTRATOR_MODE dispatch is implemented inside
    ``run_agent_sync`` below — this async wrapper delegates to it via
    ``loop.run_in_executor``, so the orchestrator path is automatically
    taken when ORCHESTRATOR_MODE=1 + PRESALE + URL. The dispatch lives in
    one place to avoid double-calling run_three_pass(). ORC-05 fallback
    chain (orchestrator → AIAgent → PipelineEngine) is preserved.
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
